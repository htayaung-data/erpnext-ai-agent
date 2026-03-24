"""
Semantic Alias Resolution Module

This module provides metadata-driven semantic alias resolution for business terms.
All business term → canonical metric/dimension mappings are loaded from the
semantic_alias_registry.json metadata file, not hardcoded in Python.

Enterprise Principle:
- Business language understanding must be expressed in metadata registries
- Python code may only interpret metadata, not encode business rules
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Set

try:
    import frappe
except Exception:
    frappe = None


# Cache for registry (loaded once per process)
_registry_cache: Optional[Dict[str, Any]] = None


def _get_registry_path() -> str:
    """Get path to semantic alias registry JSON file."""
    # Try multiple paths for flexibility
    possible_paths = [
        # Docker container path (primary)
        "/home/frappe/frappe-bench/qwen_enterprise_metadata/semantic_alias_registry.json",
        # Relative to this file (development)
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "impl_factory", "03_config", "qwen_enterprise_metadata",
            "semantic_alias_registry.json"
        ),
        # Absolute path (deployment-specific)
        "/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_alias_registry.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Fallback: return first path (will fail gracefully)
    return possible_paths[0]


def _load_registry() -> Dict[str, Any]:
    """
    Load semantic alias registry from metadata file.
    
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
        # This allows code to work during development/testing
        return {"contract_version": "1.0", "alias_groups": []}
    except json.JSONDecodeError as e:
        # Log error but don't crash
        if frappe:
            frappe.log_error(
                title="Semantic Alias Registry JSON Error",
                message=f"Failed to parse semantic_alias_registry.json: {str(e)}"
            )
        return {"contract_version": "1.0", "alias_groups": []}
    except Exception as e:
        # Log unexpected errors
        if frappe:
            frappe.log_error(
                title="Semantic Alias Registry Load Error",
                message=f"Failed to load semantic_alias_registry.json: {str(e)}"
            )
        return {"contract_version": "1.0", "alias_groups": []}


def _normalize_key(value: str) -> str:
    """
    Normalize key for comparison.
    
    Handles:
    - Case normalization
    - Whitespace normalization
    - Special character handling
    """
    if not value:
        return ""
    
    text = str(value).strip().lower()
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Replace hyphens/underscores with spaces for matching
    text = text.replace('-', ' ').replace('_', ' ')
    return text.strip()


def _contains_alias(text: str, alias: str) -> bool:
    value = _normalize_key(text)
    target = _normalize_key(alias)
    if not value or not target:
        return False
    pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
    return bool(re.search(pattern, value))


def get_canonical_key(
    alias: str,
    capability_id: Optional[str] = None,
    dimension_or_metric: Optional[str] = None
) -> Optional[str]:
    """
    Resolve business term alias to canonical key.
    
    Args:
        alias: Business term (e.g., "revenue", "qty", "gross profit")
        capability_id: Optional capability scope for disambiguation
                      (e.g., "sales_read", "product_performance_read")
        dimension_or_metric: Optional filter for "dimension" or "metric"
    
    Returns:
        Canonical key (e.g., "sales_amount", "quantity") or None if not found
    
    Example:
        >>> get_canonical_key("revenue")
        'sales_amount'
        >>> get_canonical_key("qty")
        'quantity'
        >>> get_canonical_key("revenue", capability_id="sales_read")
        'sales_amount'
    """
    registry = _load_registry()
    normalized_alias = _normalize_key(alias)
    
    if not normalized_alias:
        return None
    
    for group in registry.get("alias_groups", []):
        # Check capability scope if provided
        if capability_id:
            scope = group.get("capability_scope", [])
            if scope and capability_id not in scope:
                continue
        
        # Check dimension_or_metric filter if provided
        if dimension_or_metric:
            group_dom = group.get("dimension_or_metric", "")
            if group_dom and group_dom != dimension_or_metric:
                continue
        
        # Check aliases
        for group_alias in group.get("aliases", []):
            if _normalize_key(group_alias) == normalized_alias:
                return group["canonical_key"]
    
    return None


def get_aliases(
    canonical_key: str,
    capability_id: Optional[str] = None
) -> List[str]:
    """
    Get all aliases for a canonical key.
    
    Args:
        canonical_key: Canonical key (e.g., "sales_amount", "quantity")
        capability_id: Optional capability scope for filtering
    
    Returns:
        List of aliases (e.g., ["revenue", "selling_amount", "value"])
    
    Example:
        >>> get_aliases("sales_amount")
        ['revenue', 'selling_amount', 'value', 'billed_amount']
    """
    registry = _load_registry()
    result = []
    
    for group in registry.get("alias_groups", []):
        if group["canonical_key"] == canonical_key:
            # Check capability scope if provided
            if capability_id:
                scope = group.get("capability_scope", [])
                if scope and capability_id not in scope:
                    continue
            
            result.extend(group.get("aliases", []))
    
    return result


def get_metric_label(canonical_key: str) -> str:
    """
    Get human-readable label for a canonical key.
    
    Args:
        canonical_key: Canonical key (e.g., "sales_amount")
    
    Returns:
        Human-readable label (e.g., "Sales Amount")
    
    Example:
        >>> get_metric_label("sales_amount")
        'Sales Amount'
    """
    registry = _load_registry()
    
    for group in registry.get("alias_groups", []):
        if group["canonical_key"] == canonical_key:
            return group.get("label", canonical_key.replace("_", " ").title())
    
    # Fallback: generate label from key
    return canonical_key.replace("_", " ").title()


def get_erp_field_mapping(
    canonical_key: str,
    report_name: str
) -> List[str]:
    """
    Get ERP field names for a canonical key in a specific report.
    
    Args:
        canonical_key: Canonical key (e.g., "sales_amount")
        report_name: ERP report name (e.g., "Sales Analytics")
    
    Returns:
        List of ERP field names (e.g., ["Value", "Sales Amount"])
    
    Example:
        >>> get_erp_field_mapping("sales_amount", "Sales Analytics")
        ['Value', 'Sales Amount']
    """
    registry = _load_registry()
    
    for group in registry.get("alias_groups", []):
        if group["canonical_key"] == canonical_key:
            field_mappings = group.get("erp_field_mappings", {})
            return field_mappings.get(report_name, [])
    
    return []


def get_dimension_or_metric(canonical_key: str) -> str:
    """
    Get whether a canonical key is a dimension or metric.
    
    Args:
        canonical_key: Canonical key
    
    Returns:
        "dimension", "metric", or "" if unknown
    """
    registry = _load_registry()
    
    for group in registry.get("alias_groups", []):
        if group["canonical_key"] == canonical_key:
            return group.get("dimension_or_metric", "")
    
    return ""


def get_all_canonical_keys(
    capability_id: Optional[str] = None,
    dimension_or_metric: Optional[str] = None
) -> List[str]:
    """
    Get all canonical keys, optionally filtered.
    
    Args:
        capability_id: Optional capability scope filter
        dimension_or_metric: Optional "dimension" or "metric" filter
    
    Returns:
        List of canonical keys
    """
    registry = _load_registry()
    result = []
    
    for group in registry.get("alias_groups", []):
        # Check capability scope if provided
        if capability_id:
            scope = group.get("capability_scope", [])
            if scope and capability_id not in scope:
                continue
        
        # Check dimension_or_metric filter if provided
        if dimension_or_metric:
            group_dom = group.get("dimension_or_metric", "")
            if group_dom and group_dom != dimension_or_metric:
                continue
        
        result.append(group["canonical_key"])
    
    return result


def detect_canonical_keys(
    text: str,
    capability_id: Optional[str] = None,
    dimension_or_metric: Optional[str] = None
) -> List[str]:
    """
    Detect canonical keys mentioned in free text using the alias registry.

    Detection is registry-driven:
    - no business keywords are encoded in Python
    - aliases come only from semantic_alias_registry.json
    - longer alias matches win before shorter ones
    """
    normalized_text = _normalize_key(text)
    if not normalized_text:
        return []

    matched: List[tuple[str, int]] = []
    for canonical_key in get_all_canonical_keys(
        capability_id=capability_id,
        dimension_or_metric=dimension_or_metric,
    ):
        aliases = get_aliases(canonical_key, capability_id=capability_id)
        best_len = 0
        for alias in aliases:
            if _contains_alias(normalized_text, alias):
                best_len = max(best_len, len(_normalize_key(alias)))
        if best_len > 0:
            matched.append((canonical_key, best_len))

    matched.sort(key=lambda item: item[1], reverse=True)
    out: List[str] = []
    for canonical_key, _score in matched:
        if canonical_key not in out:
            out.append(canonical_key)
    return out


def resolve_requested_metrics(
    requested_metrics: List[str],
    capability_id: Optional[str] = None
) -> List[str]:
    """
    Resolve user-requested metric aliases to canonical keys.
    
    Args:
        requested_metrics: List of user-requested metric terms
        capability_id: Optional capability scope
    
    Returns:
        List of canonical metric keys
    
    Example:
        >>> resolve_requested_metrics(["revenue", "qty"])
        ['sales_amount', 'quantity']
    """
    resolved = []
    
    for metric in requested_metrics:
        canonical = get_canonical_key(metric, capability_id=capability_id)
        if canonical:
            resolved.append(canonical)
        else:
            # Keep original if not found (may be already canonical)
            resolved.append(metric)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for item in resolved:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    return unique


def resolve_requested_dimensions(
    requested_dimensions: List[str],
    capability_id: Optional[str] = None
) -> List[str]:
    """
    Resolve user-requested dimension aliases to canonical keys.
    
    Args:
        requested_dimensions: List of user-requested dimension terms
        capability_id: Optional capability scope
    
    Returns:
        List of canonical dimension keys
    """
    resolved = []
    
    for dimension in requested_dimensions:
        canonical = get_canonical_key(dimension, capability_id=capability_id, dimension_or_metric="dimension")
        if canonical:
            resolved.append(canonical)
        else:
            # Keep original if not found (may be already canonical)
            resolved.append(dimension)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for item in resolved:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    
    return unique


def is_known_alias(alias: str) -> bool:
    """
    Check if a term is a known business alias.
    
    Args:
        alias: Term to check
    
    Returns:
        True if the term is a known alias
    """
    return get_canonical_key(alias) is not None


def reload_registry() -> None:
    """
    Reload the registry from disk.
    
    Useful for testing or when the registry file is updated at runtime.
    """
    global _registry_cache
    _registry_cache = None
    _load_registry()
