"""
Intent Rules Engine Module

This module provides metadata-driven intent bias rule evaluation.
All intent detection rules are loaded from intent_bias_rules_registry.json,
not hardcoded in Python.

Enterprise Principle:
- Business language understanding must be expressed in metadata registries
- Python code may only interpret metadata, not encode business rules
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Set

from ai_assistant_ui.qwen_chat.contracts import FreshQueryInterpretationContract

try:
    import frappe
except Exception:
    frappe = None


# Cache for registry (loaded once per process)
_registry_cache: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class IntentRule:
    """
    Intent bias rule from metadata registry.
    
    Attributes:
        rule_id: Unique identifier for the rule
        label: Human-readable description
        priority: Evaluation priority (higher = evaluated first)
        condition: Rule condition (tokens_all, tokens_any, etc.)
        action: Rule action (set_intent_class, set_capabilities, etc.)
    """
    rule_id: str
    label: str
    priority: int
    condition: Dict[str, Any]
    action: Dict[str, Any]
    
    def evaluate(self, tokens: Set[str], interpretation: FreshQueryInterpretationContract) -> bool:
        """
        Evaluate if rule condition matches the input.
        
        Args:
            tokens: Tokenized message tokens
            interpretation: Current interpretation contract
        
        Returns:
            True if rule condition matches
        """
        cond = self.condition
        
        # tokens_all: ALL tokens must be present
        if "tokens_all" in cond:
            required_tokens = set(cond["tokens_all"])
            if not required_tokens.issubset(tokens):
                return False
        
        # tokens_any: ANY of these tokens must be present
        if "tokens_any" in cond:
            any_tokens = set(cond["tokens_any"])
            if not any_tokens.intersection(tokens):
                return False
        
        # tokens_any_of: ANY of these tokens (OR within group)
        if "tokens_any_of" in cond:
            any_of_tokens = set(cond["tokens_any_of"])
            if not any_of_tokens.intersection(tokens):
                return False
        
        # tokens_none: NONE of these tokens should be present
        if "tokens_none" in cond:
            none_tokens = set(cond["tokens_none"])
            if none_tokens.intersection(tokens):
                return False
        
        # intent_class_is: Must match current intent class
        if "intent_class_is" in cond:
            if interpretation.intent_class != cond["intent_class_is"]:
                return False
        
        # capability_count_max: Maximum number of candidate capabilities
        if "capability_count_max" in cond:
            if len(interpretation.candidate_capability_ids) > cond["capability_count_max"]:
                return False
        
        return True
    
    def apply(self, interpretation: FreshQueryInterpretationContract) -> FreshQueryInterpretationContract:
        """
        Apply rule action to interpretation.
        
        Args:
            interpretation: Current interpretation contract
        
        Returns:
            Updated interpretation contract
        """
        action = self.action
        changes: Dict[str, Any] = {}
        
        if "set_intent_class" in action:
            changes["intent_class"] = action["set_intent_class"]
        
        if "set_capabilities" in action:
            changes["candidate_capability_ids"] = list(action["set_capabilities"])
        
        if "set_reports" in action:
            changes["candidate_reports"] = list(action["set_reports"])
        
        if "add_ambiguity_flag" in action:
            flags = list(interpretation.ambiguity_flags)
            if action["add_ambiguity_flag"] not in flags:
                flags.append(action["add_ambiguity_flag"])
            changes["ambiguity_flags"] = flags
        
        if "set_time_scope" in action:
            changes["requested_time_scope"] = action["set_time_scope"]
        
        # Apply changes if any
        if changes:
            return replace(interpretation, **changes)
        
        return interpretation


def _get_registry_path() -> str:
    """Get path to intent bias rules registry JSON file."""
    possible_paths = [
        # Docker container path (primary)
        "/home/frappe/frappe-bench/qwen_enterprise_metadata/intent_bias_rules_registry.json",
        # Relative to this file (development)
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "impl_factory", "03_config", "qwen_enterprise_metadata",
            "intent_bias_rules_registry.json"
        ),
        # Absolute path (deployment-specific)
        "/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Fallback: return first path (will fail gracefully)
    return possible_paths[0]


def _load_registry() -> Dict[str, Any]:
    """
    Load intent bias rules registry from metadata file.
    
    Uses caching to avoid repeated file I/O.
    Returns empty dict if file not found (graceful degradation).
    """
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    try:
        registry_path = _get_registry_path()
        with open(registry_path, 'r', encoding='utf-8') as f:
            _registry_cache = json.load(f)
        return _registry_cache
    except FileNotFoundError:
        # Graceful degradation: return empty registry
        return {"contract_version": "1.0", "rules": []}
    except json.JSONDecodeError as e:
        # Log error but don't crash
        if frappe:
            frappe.log_error(
                title="Intent Bias Rules Registry JSON Error",
                message=f"Failed to parse intent_bias_rules_registry.json: {str(e)}"
            )
        return {"contract_version": "1.0", "rules": []}
    except Exception as e:
        # Log unexpected errors
        if frappe:
            frappe.log_error(
                title="Intent Bias Rules Registry Load Error",
                message=f"Failed to load intent_bias_rules_registry.json: {str(e)}"
            )
        return {"contract_version": "1.0", "rules": []}


def load_intent_rules() -> List[IntentRule]:
    """
    Load intent rules from metadata registry.
    
    Returns:
        List of IntentRule objects sorted by priority (descending)
    """
    registry = _load_registry()
    rules = []
    
    for rule_data in registry.get("rules", []):
        if not isinstance(rule_data, dict):
            continue
        
        # Validate required fields
        if not rule_data.get("rule_id"):
            continue
        if "priority" not in rule_data:
            continue
        if "condition" not in rule_data:
            continue
        if "action" not in rule_data:
            continue
        
        rule = IntentRule(
            rule_id=rule_data["rule_id"],
            label=rule_data.get("label", rule_data["rule_id"]),
            priority=rule_data["priority"],
            condition=rule_data["condition"],
            action=rule_data["action"],
        )
        rules.append(rule)
    
    # Sort by priority (descending - higher priority evaluated first)
    return sorted(rules, key=lambda r: r.priority, reverse=True)


def _message_tokens(value: str) -> set[str]:
    """
    Tokenize message for rule evaluation.
    
    Args:
        value: Message text
    
    Returns:
        Set of lowercase tokens
    """
    import re
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return {token for token in text.split() if token}


def apply_intent_rules(
    message: str,
    interpretation: FreshQueryInterpretationContract
) -> FreshQueryInterpretationContract:
    """
    Apply intent bias rules to interpretation.
    
    Rules are evaluated by priority (highest first).
    First matching rule wins (to maintain backward compatibility with
    the original hardcoded behavior).
    
    Args:
        message: Original user message
        interpretation: Current interpretation contract
    
    Returns:
        Updated interpretation contract (or original if no rules matched)
    """
    tokens = _message_tokens(message)
    rules = load_intent_rules()
    
    # Evaluate rules by priority (highest first)
    for rule in rules:
        if rule.evaluate(tokens, interpretation):
            # First matching rule wins
            result = rule.apply(interpretation)
            
            # Log rule match for audit trail
            if frappe:
                frappe.log_error(
                    title="Intent Rule Matched",
                    message=f"Rule: {rule.rule_id} ({rule.label})\nMessage: {message[:100]}\nResult: intent_class={result.intent_class}"
                )
            
            return result
    
    # No rules matched - return original interpretation
    return interpretation


def apply_all_matching_rules(
    message: str,
    interpretation: FreshQueryInterpretationContract
) -> List[FreshQueryInterpretationContract]:
    """
    Apply ALL matching rules to interpretation.
    
    Unlike apply_intent_rules (first match wins), this returns
    results from all matching rules for analysis.
    
    Args:
        message: Original user message
        interpretation: Current interpretation contract
    
    Returns:
        List of interpretation contracts (one per matching rule)
    """
    tokens = _message_tokens(message)
    rules = load_intent_rules()
    results = []
    
    for rule in rules:
        if rule.evaluate(tokens, interpretation):
            result = rule.apply(interpretation)
            results.append(result)
    
    return results


def get_matching_rule_ids(
    message: str,
    interpretation: FreshQueryInterpretationContract
) -> List[str]:
    """
    Get IDs of all rules that match the input.
    
    Useful for debugging and audit trails.
    
    Args:
        message: Original user message
        interpretation: Current interpretation contract
    
    Returns:
        List of matching rule IDs
    """
    tokens = _message_tokens(message)
    rules = load_intent_rules()
    matching_ids = []
    
    for rule in rules:
        if rule.evaluate(tokens, interpretation):
            matching_ids.append(rule.rule_id)
    
    return matching_ids


def validate_rule(rule_data: Dict[str, Any]) -> List[str]:
    """
    Validate a single rule data structure.
    
    Args:
        rule_data: Rule data dictionary
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    if not rule_data.get("rule_id"):
        errors.append("Missing required field: rule_id")
    if "priority" not in rule_data:
        errors.append("Missing required field: priority")
    if not isinstance(rule_data.get("priority"), int):
        errors.append("Field 'priority' must be an integer")
    if "condition" not in rule_data:
        errors.append("Missing required field: condition")
    if "action" not in rule_data:
        errors.append("Missing required field: action")
    
    # Validate condition operators
    valid_condition_operators = {
        "tokens_all", "tokens_any", "tokens_any_of", "tokens_none",
        "intent_class_is", "capability_count_max"
    }
    condition = rule_data.get("condition", {})
    if isinstance(condition, dict):
        for op in condition.keys():
            if op not in valid_condition_operators:
                errors.append(f"Unknown condition operator: {op}")
    
    # Validate action operators
    valid_action_operators = {
        "set_intent_class", "set_capabilities", "set_reports",
        "add_ambiguity_flag", "set_time_scope"
    }
    action = rule_data.get("action", {})
    if isinstance(action, dict):
        for op in action.keys():
            if op not in valid_action_operators:
                errors.append(f"Unknown action operator: {op}")
    
    return errors


def validate_registry() -> List[str]:
    """
    Validate entire rules registry.
    
    Returns:
        List of error messages (empty if valid)
    """
    registry = _load_registry()
    errors = []
    
    for rule in registry.get("rules", []):
        rule_errors = validate_rule(rule)
        if rule_errors:
            rule_id = rule.get("rule_id", "UNKNOWN")
            for err in rule_errors:
                errors.append(f"Rule {rule_id}: {err}")
    
    return errors


def reload_registry() -> None:
    """
    Reload the registry from disk.
    
    Useful for testing or when the registry file is updated at runtime.
    """
    global _registry_cache
    _registry_cache = None
    _load_registry()


def get_rule_statistics() -> Dict[str, Any]:
    """
    Get statistics about loaded rules.
    
    Returns:
        Dictionary with rule statistics
    """
    rules = load_intent_rules()
    
    # Count by priority ranges
    high_priority = sum(1 for r in rules if r.priority >= 90)
    medium_priority = sum(1 for r in rules if 70 <= r.priority < 90)
    low_priority = sum(1 for r in rules if r.priority < 70)
    
    # Count by action type
    action_counts: Dict[str, int] = {}
    for rule in rules:
        for action_key in rule.action.keys():
            action_counts[action_key] = action_counts.get(action_key, 0) + 1
    
    return {
        "total_rules": len(rules),
        "priority_distribution": {
            "high (>=90)": high_priority,
            "medium (70-89)": medium_priority,
            "low (<70)": low_priority,
        },
        "action_distribution": action_counts,
        "rule_ids": [r.rule_id for r in rules],
    }
