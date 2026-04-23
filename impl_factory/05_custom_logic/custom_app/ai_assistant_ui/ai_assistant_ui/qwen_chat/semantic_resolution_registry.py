from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	get_capability_spec,
	get_report_family_spec,
	get_report_spec,
	list_capability_specs,
	list_intent_class_specs,
	load_semantic_resolution_registry,
)


ALLOWED_RESOLUTION_MODES = {
	"required_or_clarify",
	"required_or_default",
	"optional",
}

ALLOWED_GOVERNED_DECISIONS = {
	"execute",
	"clarify",
	"reject",
}


@dataclass(frozen=True)
class SemanticResolutionRegistryValidationResult:
	status: str
	errors: List[str]
	warnings: List[str]
	stats: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_resolution_registry_validation",
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


def validate_semantic_resolution_registry(
	payload: Dict[str, Any] | None = None,
) -> SemanticResolutionRegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_semantic_resolution_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	known_intent_classes = {
		str(item.get("intent_class_id") or "").strip()
		for item in list_intent_class_specs()
		if isinstance(item, dict)
	}
	known_capabilities = {
		str(item.get("capability_id") or "").strip()
		for item in list_capability_specs()
		if isinstance(item, dict)
	}

	slot_definitions = data.get("slot_definitions")
	if not isinstance(slot_definitions, list) or not slot_definitions:
		errors.append("slot_definitions must be a non-empty list.")
		slot_definitions = []

	slot_names: Set[str] = set()
	slot_allowed_values: Dict[str, Set[str]] = {}
	for idx, slot_def in enumerate(slot_definitions):
		if not isinstance(slot_def, dict):
			errors.append(f"slot_definitions[{idx}] must be an object.")
			continue
		slot_name = str(slot_def.get("slot_name") or "").strip()
		if not slot_name:
			errors.append(f"slot_definitions[{idx}].slot_name must be a non-empty string.")
			continue
		if slot_name in slot_names:
			errors.append(f"slot_definitions contains duplicate slot_name '{slot_name}'.")
		slot_names.add(slot_name)

		allowed_values = _as_str_list(slot_def.get("allowed_values"))
		if not allowed_values:
			errors.append(f"slot_definitions[{idx}].allowed_values must be a non-empty list.")
		duplicates = _duplicate_values(allowed_values)
		if duplicates:
			errors.append(
				f"slot_definitions[{idx}].allowed_values has duplicate values: {', '.join(duplicates)}."
			)
		slot_allowed_values[slot_name] = set(allowed_values)

		resolution_mode = str(slot_def.get("resolution_mode") or "").strip()
		if resolution_mode not in ALLOWED_RESOLUTION_MODES:
			errors.append(
				f"slot_definitions[{idx}].resolution_mode must be one of {sorted(ALLOWED_RESOLUTION_MODES)}."
			)

		required_for = _as_str_list(slot_def.get("required_for_intent_classes"))
		for intent_class in required_for:
			if intent_class not in known_intent_classes:
				errors.append(
					f"slot_definitions[{idx}] references unknown intent_class '{intent_class}'."
				)

	alias_maps = data.get("alias_maps")
	if not isinstance(alias_maps, dict):
		errors.append("alias_maps must be an object.")
		alias_maps = {}
	for slot_name, alias_entries in alias_maps.items():
		if slot_name not in slot_names:
			errors.append(f"alias_maps references unknown slot '{slot_name}'.")
			continue
		if not isinstance(alias_entries, list):
			errors.append(f"alias_maps.{slot_name} must be a list.")
			continue
		seen_canonical_values: Set[str] = set()
		for idx, entry in enumerate(alias_entries):
			if not isinstance(entry, dict):
				errors.append(f"alias_maps.{slot_name}[{idx}] must be an object.")
				continue
			canonical_value = str(entry.get("canonical_value") or "").strip()
			if canonical_value not in slot_allowed_values.get(slot_name, set()):
				errors.append(
					f"alias_maps.{slot_name}[{idx}] uses unknown canonical_value '{canonical_value}'."
				)
			if canonical_value in seen_canonical_values:
				errors.append(
					f"alias_maps.{slot_name} contains duplicate canonical_value '{canonical_value}'."
				)
			seen_canonical_values.add(canonical_value)

			aliases = _as_str_list(entry.get("aliases"))
			if not aliases:
				errors.append(f"alias_maps.{slot_name}[{idx}].aliases must be a non-empty list.")
			duplicates = _duplicate_values(aliases)
			if duplicates:
				errors.append(
					f"alias_maps.{slot_name}[{idx}].aliases has duplicate values: {', '.join(duplicates)}."
				)

	family_resolution_rules = data.get("family_resolution_rules")
	if not isinstance(family_resolution_rules, list) or not family_resolution_rules:
		errors.append("family_resolution_rules must be a non-empty list.")
		family_resolution_rules = []
	seen_rule_ids: Set[str] = set()
	referenced_intent_classes: Set[str] = set()
	for idx, rule in enumerate(family_resolution_rules):
		if not isinstance(rule, dict):
			errors.append(f"family_resolution_rules[{idx}] must be an object.")
			continue
		rule_id = str(rule.get("rule_id") or "").strip()
		if not rule_id:
			errors.append(f"family_resolution_rules[{idx}].rule_id must be a non-empty string.")
		elif rule_id in seen_rule_ids:
			errors.append(f"family_resolution_rules contains duplicate rule_id '{rule_id}'.")
		seen_rule_ids.add(rule_id)

		intent_class = str(rule.get("intent_class") or "").strip()
		if intent_class not in known_intent_classes:
			errors.append(
				f"family_resolution_rules[{idx}] references unknown intent_class '{intent_class}'."
			)
		else:
			referenced_intent_classes.add(intent_class)

		required_slots = rule.get("required_slots")
		if not isinstance(required_slots, dict) or not required_slots:
			errors.append(f"family_resolution_rules[{idx}].required_slots must be a non-empty object.")
		else:
			for slot_name, slot_value in required_slots.items():
				if slot_name not in slot_names:
					errors.append(
						f"family_resolution_rules[{idx}] references unknown slot '{slot_name}'."
					)
					continue
				if str(slot_value or "").strip() not in slot_allowed_values.get(slot_name, set()):
					errors.append(
						f"family_resolution_rules[{idx}] uses invalid value '{slot_value}' for slot '{slot_name}'."
					)

		candidate_family_ids = _as_str_list(rule.get("candidate_family_ids"))
		candidate_capability_ids = _as_str_list(rule.get("candidate_capability_ids"))
		candidate_reports = _as_str_list(rule.get("candidate_reports"))
		governed_decision = str(rule.get("governed_decision") or "").strip()
		requires_execution_targets = governed_decision == "execute"
		if requires_execution_targets and not candidate_family_ids:
			errors.append(
				f"family_resolution_rules[{idx}].candidate_family_ids must be a non-empty list."
			)
		if requires_execution_targets and not candidate_capability_ids:
			errors.append(
				f"family_resolution_rules[{idx}].candidate_capability_ids must be a non-empty list."
			)
		if requires_execution_targets and not candidate_reports:
			errors.append(
				f"family_resolution_rules[{idx}].candidate_reports must be a non-empty list."
			)

		for family_id in candidate_family_ids:
			if not get_report_family_spec(family_id):
				errors.append(
					f"family_resolution_rules[{idx}] references unknown family_id '{family_id}'."
				)
		for capability_id in candidate_capability_ids:
			if capability_id not in known_capabilities:
				errors.append(
					f"family_resolution_rules[{idx}] references unknown capability_id '{capability_id}'."
				)
		for report_name in candidate_reports:
			report_spec = get_report_spec(report_name)
			if not report_spec:
				errors.append(
					f"family_resolution_rules[{idx}] references unknown report '{report_name}'."
				)
				continue
			if candidate_family_ids:
				if not any(
					report_name in _as_str_list(get_report_family_spec(family_id).get("report_names"))
					for family_id in candidate_family_ids
					if get_report_family_spec(family_id)
				):
					errors.append(
						f"family_resolution_rules[{idx}] report '{report_name}' is not declared by its candidate_family_ids."
					)
			if candidate_capability_ids:
				if not any(
					report_name in _as_str_list(get_capability_spec(capability_id).get("report_names"))
					for capability_id in candidate_capability_ids
					if get_capability_spec(capability_id)
				):
					errors.append(
						f"family_resolution_rules[{idx}] report '{report_name}' is not declared by its candidate_capability_ids."
					)

		if governed_decision not in ALLOWED_GOVERNED_DECISIONS:
			errors.append(
				f"family_resolution_rules[{idx}].governed_decision must be one of {sorted(ALLOWED_GOVERNED_DECISIONS)}."
			)

	ambiguity_policies = data.get("ambiguity_policies")
	if not isinstance(ambiguity_policies, list) or not ambiguity_policies:
		errors.append("ambiguity_policies must be a non-empty list.")
		ambiguity_policies = []
	seen_policy_ids: Set[str] = set()
	for idx, policy in enumerate(ambiguity_policies):
		if not isinstance(policy, dict):
			errors.append(f"ambiguity_policies[{idx}] must be an object.")
			continue
		policy_id = str(policy.get("policy_id") or "").strip()
		if not policy_id:
			errors.append(f"ambiguity_policies[{idx}].policy_id must be a non-empty string.")
		elif policy_id in seen_policy_ids:
			errors.append(f"ambiguity_policies contains duplicate policy_id '{policy_id}'.")
		seen_policy_ids.add(policy_id)

		intent_class = str(policy.get("intent_class") or "").strip()
		if intent_class not in known_intent_classes:
			errors.append(
				f"ambiguity_policies[{idx}] references unknown intent_class '{intent_class}'."
			)

		missing_slots = _as_str_list(policy.get("missing_slots"))
		if not missing_slots:
			errors.append(f"ambiguity_policies[{idx}].missing_slots must be a non-empty list.")
		for slot_name in missing_slots:
			if slot_name not in slot_names:
				errors.append(
					f"ambiguity_policies[{idx}] references unknown slot '{slot_name}'."
				)

		decision = str(policy.get("decision") or "").strip()
		if decision not in ALLOWED_GOVERNED_DECISIONS:
			errors.append(
				f"ambiguity_policies[{idx}].decision must be one of {sorted(ALLOWED_GOVERNED_DECISIONS)}."
			)

		default_slots = policy.get("default_slots")
		if default_slots is not None:
			if not isinstance(default_slots, dict):
				errors.append(f"ambiguity_policies[{idx}].default_slots must be an object when present.")
			else:
				for slot_name, slot_value in default_slots.items():
					if slot_name not in slot_names:
						errors.append(
							f"ambiguity_policies[{idx}] default_slots references unknown slot '{slot_name}'."
						)
						continue
					if str(slot_value or "").strip() not in slot_allowed_values.get(slot_name, set()):
						errors.append(
							f"ambiguity_policies[{idx}] default_slots uses invalid value '{slot_value}' for slot '{slot_name}'."
						)

	defaults = data.get("defaults")
	if not isinstance(defaults, dict):
		errors.append("defaults must be an object.")
		defaults = {}

	intent_defaults = defaults.get("intent_defaults")
	if intent_defaults is not None:
		if not isinstance(intent_defaults, dict):
			errors.append("defaults.intent_defaults must be an object when present.")
		else:
			for intent_class, slot_map in intent_defaults.items():
				if intent_class not in known_intent_classes:
					errors.append(
						f"defaults.intent_defaults references unknown intent_class '{intent_class}'."
					)
					continue
				if not isinstance(slot_map, dict):
					errors.append(
						f"defaults.intent_defaults.{intent_class} must be an object."
					)
					continue
				for slot_name, slot_value in slot_map.items():
					if slot_name not in slot_names:
						errors.append(
							f"defaults.intent_defaults.{intent_class} references unknown slot '{slot_name}'."
						)
						continue
					if str(slot_value or "").strip() not in slot_allowed_values.get(slot_name, set()):
						errors.append(
							f"defaults.intent_defaults.{intent_class} uses invalid value '{slot_value}' for slot '{slot_name}'."
						)

	for slot_name in slot_names:
		if slot_name not in alias_maps:
			warnings.append(f"slot '{slot_name}' has no alias map yet.")
		if not any(slot_name in (rule.get("required_slots") or {}) for rule in family_resolution_rules if isinstance(rule, dict)):
			warnings.append(f"slot '{slot_name}' is not used by any family_resolution_rule yet.")

	for intent_class in sorted(referenced_intent_classes):
		if not any(
			isinstance(policy, dict) and str(policy.get("intent_class") or "").strip() == intent_class
			for policy in ambiguity_policies
		):
			warnings.append(f"intent_class '{intent_class}' has no ambiguity policy.")

	stats = {
		"slot_definition_count": len(slot_definitions),
		"alias_map_count": len(alias_maps),
		"family_resolution_rule_count": len(family_resolution_rules),
		"ambiguity_policy_count": len(ambiguity_policies),
	}
	return SemanticResolutionRegistryValidationResult(
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats=stats,
	)


def semantic_resolution_intent_classes(
	payload: Dict[str, Any] | None = None,
) -> Set[str]:
	data = payload if isinstance(payload, dict) else load_semantic_resolution_registry()
	intent_classes: Set[str] = set()
	for rule in data.get("family_resolution_rules") or []:
		if not isinstance(rule, dict):
			continue
		intent_class = str(rule.get("intent_class") or "").strip()
		if intent_class:
			intent_classes.add(intent_class)
	return intent_classes


def semantic_resolution_governs_intent(
	intent_class: str,
	payload: Dict[str, Any] | None = None,
) -> bool:
	"""
	Enterprise boundary helper.

	If this returns True, the intent is owned by governed semantic resolution and
	must not be steered by legacy family-surface routing or deterministic lexical
	fallback paths.
	"""
	return str(intent_class or "").strip() in semantic_resolution_intent_classes(payload)


def run_semantic_resolution_registry_probe() -> Dict[str, Any]:
	result = validate_semantic_resolution_registry()
	payload = result.to_payload()
	payload["ok"] = result.status == "pass"
	return payload
