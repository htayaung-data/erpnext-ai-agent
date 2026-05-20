from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	get_business_definition_spec,
	get_business_threshold_spec,
	get_capability_spec,
	get_governed_formula_spec,
	load_business_rule_registry,
)


REQUIRED_ACTIVATION_STATES = {
	"active",
	"blocked_missing_policy",
	"blocked_missing_data",
	"draft_unapproved",
	"deprecated",
}


@dataclass(frozen=True)
class BusinessRuleRegistryValidationResult:
	status: str
	errors: List[str]
	warnings: List[str]
	stats: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_business_rule_registry_validation",
			"contract_version": "1.0",
			"status": self.status,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"stats": dict(self.stats),
		}


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	items: List[str] = []
	for item in value:
		text = str(item or "").strip()
		if text:
			items.append(text)
	return items


def _duplicate_values(values: List[str]) -> List[str]:
	seen: Set[str] = set()
	duplicates: List[str] = []
	for value in values:
		if value in seen and value not in duplicates:
			duplicates.append(value)
		seen.add(value)
	return duplicates


def _validate_activation_states(data: Dict[str, Any], errors: List[str]) -> Set[str]:
	allowed_states = _as_str_list(data.get("allowed_activation_states"))
	if not allowed_states:
		errors.append("allowed_activation_states must be a non-empty list.")
		return set()
	duplicates = _duplicate_values(allowed_states)
	if duplicates:
		errors.append(f"allowed_activation_states has duplicate values: {', '.join(duplicates)}.")
	allowed_state_set = set(allowed_states)
	missing = sorted(REQUIRED_ACTIVATION_STATES.difference(allowed_state_set))
	if missing:
		errors.append(
			f"allowed_activation_states is missing required values: {', '.join(missing)}."
		)
	return allowed_state_set


def _validate_blocked_reason(
	*,
	label: str,
	activation_state: str,
	blocked_reason: str,
	errors: List[str],
	warnings: List[str],
) -> None:
	if activation_state == "active":
		if blocked_reason:
			warnings.append(f"{label} is active but still provides blocked_reason.")
		return
	if not blocked_reason:
		errors.append(f"{label} must provide blocked_reason when activation_state is not 'active'.")


def validate_business_rule_registry(
	payload: Dict[str, Any] | None = None,
) -> BusinessRuleRegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_business_rule_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_rule_types = set(_as_str_list(data.get("allowed_rule_types")))
	allowed_scope_types = set(_as_str_list(data.get("allowed_scope_types")))

	if not allowed_rule_types:
		errors.append("allowed_rule_types must be a non-empty list.")
	if not allowed_scope_types:
		errors.append("allowed_scope_types must be a non-empty list.")

	rules = data.get("rules")
	if not isinstance(rules, list):
		errors.append("rules must be a list.")
		rules = []

	seen_rule_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(rules):
		if not isinstance(item, dict):
			errors.append(f"rules[{idx}] must be an object.")
			continue
		rule_id = str(item.get("rule_id") or "").strip()
		if not rule_id:
			errors.append(f"rules[{idx}].rule_id must be a non-empty string.")
			continue
		if rule_id in seen_rule_ids:
			errors.append(f"rules contains duplicate rule_id '{rule_id}'.")
		seen_rule_ids.add(rule_id)

		for field_name in ("label", "owner", "policy_statement"):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"rules[{idx}].{field_name} must be a non-empty string.")

		company_scope = _as_str_list(item.get("company_scope"))
		if not company_scope:
			errors.append(f"rules[{idx}].company_scope must be a non-empty list.")

		rule_type = str(item.get("rule_type") or "").strip()
		if rule_type not in allowed_rule_types:
			errors.append(f"rules[{idx}].rule_type must be one of {sorted(allowed_rule_types)}.")

		scope_type = str(item.get("scope_type") or "").strip()
		if scope_type not in allowed_scope_types:
			errors.append(f"rules[{idx}].scope_type must be one of {sorted(allowed_scope_types)}.")
		scope_reference = str(item.get("scope_reference") or "").strip()
		if scope_type in {"definition", "formula", "threshold", "capability"} and not scope_reference:
			errors.append(f"rules[{idx}].scope_reference must be a non-empty string for scope_type '{scope_type}'.")
		if scope_type in {"global", "company"} and scope_reference:
			errors.append(f"rules[{idx}].scope_reference must be empty for scope_type '{scope_type}'.")
		if scope_type == "definition" and scope_reference and not get_business_definition_spec(scope_reference):
			errors.append(f"rules[{idx}].scope_reference references unknown definition '{scope_reference}'.")
		if scope_type == "formula" and scope_reference and not get_governed_formula_spec(scope_reference):
			errors.append(f"rules[{idx}].scope_reference references unknown formula '{scope_reference}'.")
		if scope_type == "threshold" and scope_reference and not get_business_threshold_spec(scope_reference):
			errors.append(f"rules[{idx}].scope_reference references unknown threshold '{scope_reference}'.")
		if scope_type == "capability" and scope_reference and not get_capability_spec(scope_reference):
			errors.append(f"rules[{idx}].scope_reference references unknown capability '{scope_reference}'.")

		enforced_behavior = item.get("enforced_behavior")
		if not isinstance(enforced_behavior, dict) or not enforced_behavior:
			errors.append(f"rules[{idx}].enforced_behavior must be a non-empty object.")

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(f"rules[{idx}].activation_state must be one of {sorted(allowed_states)}.")
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"rules[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return BusinessRuleRegistryValidationResult(
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"rule_count": len([item for item in rules if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def run_business_rule_registry_probe() -> Dict[str, Any]:
	result = validate_business_rule_registry()
	return {
		"ok": result.status == "pass",
		"result": result.to_payload(),
	}
