from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.metadata import (
	get_business_rule_spec,
	list_capability_specs,
	load_business_definition_registry,
	load_business_threshold_registry,
	load_governed_formula_registry,
	get_report_spec,
)


REQUIRED_ACTIVATION_STATES = {
	"active",
	"blocked_missing_policy",
	"blocked_missing_data",
	"draft_unapproved",
	"deprecated",
}


@dataclass(frozen=True)
class RegistryValidationResult:
	registry_name: str
	status: str
	errors: List[str]
	warnings: List[str]
	stats: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_registry_validation",
			"contract_version": "1.0",
			"registry_name": self.registry_name,
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


def _coerce_number(value: Any) -> float | None:
	if value is None or value == "":
		return None
	try:
		return float(value)
	except Exception:
		return None


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


def validate_business_definition_registry(
	payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_business_definition_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_categories = set(_as_str_list(data.get("allowed_semantic_categories")))
	allowed_grains = set(_as_str_list(data.get("allowed_entity_grains")))
	allowed_time_bases = set(_as_str_list(data.get("allowed_time_bases")))
	allowed_clarify_policies = set(_as_str_list(data.get("allowed_clarify_policies")))

	if not allowed_categories:
		errors.append("allowed_semantic_categories must be a non-empty list.")
	if not allowed_grains:
		errors.append("allowed_entity_grains must be a non-empty list.")
	if not allowed_time_bases:
		errors.append("allowed_time_bases must be a non-empty list.")
	if not allowed_clarify_policies:
		errors.append("allowed_clarify_policies must be a non-empty list.")

	definitions = data.get("definitions")
	if not isinstance(definitions, list):
		errors.append("definitions must be a list.")
		definitions = []

	seen_definition_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(definitions):
		if not isinstance(item, dict):
			errors.append(f"definitions[{idx}] must be an object.")
			continue
		definition_id = str(item.get("definition_id") or "").strip()
		if not definition_id:
			errors.append(f"definitions[{idx}].definition_id must be a non-empty string.")
			continue
		if definition_id in seen_definition_ids:
			errors.append(f"definitions contains duplicate definition_id '{definition_id}'.")
		seen_definition_ids.add(definition_id)

		for field_name in ("label", "description", "owner"):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"definitions[{idx}].{field_name} must be a non-empty string.")

		company_scope = _as_str_list(item.get("company_scope"))
		if not company_scope:
			errors.append(f"definitions[{idx}].company_scope must be a non-empty list.")

		entity_grain = str(item.get("entity_grain") or "").strip()
		if entity_grain not in allowed_grains:
			errors.append(
				f"definitions[{idx}].entity_grain must be one of {sorted(allowed_grains)}."
			)

		time_basis = str(item.get("time_basis") or "").strip()
		if time_basis not in allowed_time_bases:
			errors.append(
				f"definitions[{idx}].time_basis must be one of {sorted(allowed_time_bases)}."
			)

		semantic_category = str(item.get("semantic_category") or "").strip()
		if semantic_category not in allowed_categories:
			errors.append(
				f"definitions[{idx}].semantic_category must be one of {sorted(allowed_categories)}."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"definitions[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		source_of_truth = item.get("source_of_truth")
		if not isinstance(source_of_truth, dict) or not source_of_truth:
			errors.append(f"definitions[{idx}].source_of_truth must be a non-empty object.")

		clarify_policy = str(item.get("clarify_policy") or "").strip()
		if clarify_policy not in allowed_clarify_policies:
			errors.append(
				f"definitions[{idx}].clarify_policy must be one of {sorted(allowed_clarify_policies)}."
			)

		_validate_blocked_reason(
			label=f"definitions[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="business_definition_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"definition_count": len([item for item in definitions if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def validate_governed_formula_registry(
	payload: Dict[str, Any] | None = None,
	*,
	business_definition_payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_governed_formula_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_formula_types = set(_as_str_list(data.get("allowed_formula_types")))
	allowed_aggregation_rules = set(_as_str_list(data.get("allowed_aggregation_rules")))
	allowed_input_requirement_types = set(_as_str_list(data.get("allowed_input_requirement_types")))
	allowed_time_scope_requirements = set(_as_str_list(data.get("allowed_time_scope_requirements")))

	if not allowed_formula_types:
		errors.append("allowed_formula_types must be a non-empty list.")
	if not allowed_aggregation_rules:
		errors.append("allowed_aggregation_rules must be a non-empty list.")
	if not allowed_input_requirement_types:
		errors.append("allowed_input_requirement_types must be a non-empty list.")
	if not allowed_time_scope_requirements:
		errors.append("allowed_time_scope_requirements must be a non-empty list.")

	definition_source = (
		business_definition_payload
		if isinstance(business_definition_payload, dict)
		else load_business_definition_registry()
	)
	known_definition_ids = {
		str(item.get("definition_id") or "").strip()
		for item in (definition_source.get("definitions") or [])
		if isinstance(item, dict) and str(item.get("definition_id") or "").strip()
	}
	known_capabilities = {
		str(item.get("capability_id") or "").strip()
		for item in list_capability_specs()
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	}

	formulas = data.get("formulas")
	if not isinstance(formulas, list):
		errors.append("formulas must be a list.")
		formulas = []

	seen_formula_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(formulas):
		if not isinstance(item, dict):
			errors.append(f"formulas[{idx}] must be an object.")
			continue
		formula_id = str(item.get("formula_id") or "").strip()
		if not formula_id:
			errors.append(f"formulas[{idx}].formula_id must be a non-empty string.")
			continue
		if formula_id in seen_formula_ids:
			errors.append(f"formulas contains duplicate formula_id '{formula_id}'.")
		seen_formula_ids.add(formula_id)

		definition_id = str(item.get("definition_id") or "").strip()
		if definition_id not in known_definition_ids:
			errors.append(
				f"formulas[{idx}].definition_id references unknown definition '{definition_id}'."
			)

		if not str(item.get("label") or "").strip():
			errors.append(f"formulas[{idx}].label must be a non-empty string.")

		formula_type = str(item.get("formula_type") or "").strip()
		if formula_type not in allowed_formula_types:
			errors.append(
				f"formulas[{idx}].formula_type must be one of {sorted(allowed_formula_types)}."
			)

		input_metrics = _as_str_list(item.get("input_metrics"))
		if not input_metrics:
			errors.append(f"formulas[{idx}].input_metrics must be a non-empty list.")

		input_requirements = item.get("input_requirements")
		if not isinstance(input_requirements, list) or not input_requirements:
			errors.append(f"formulas[{idx}].input_requirements must be a non-empty list.")
		else:
			for req_idx, requirement in enumerate(input_requirements):
				if not isinstance(requirement, dict):
					errors.append(f"formulas[{idx}].input_requirements[{req_idx}] must be an object.")
					continue
				metric_key = str(requirement.get("metric_key") or "").strip()
				if not metric_key:
					errors.append(
						f"formulas[{idx}].input_requirements[{req_idx}].metric_key must be a non-empty string."
					)
				requirement_type = str(requirement.get("requirement_type") or "").strip()
				if requirement_type not in allowed_input_requirement_types:
					errors.append(
						f"formulas[{idx}].input_requirements[{req_idx}].requirement_type must be one of {sorted(allowed_input_requirement_types)}."
					)

		source_capabilities = _as_str_list(item.get("source_capabilities"))
		if not source_capabilities:
			errors.append(f"formulas[{idx}].source_capabilities must be a non-empty list.")
		else:
			for capability_id in source_capabilities:
				if capability_id not in known_capabilities:
					errors.append(
						f"formulas[{idx}].source_capabilities references unknown capability '{capability_id}'."
					)

		source_reports = _as_str_list(item.get("source_reports"))
		if not source_reports:
			errors.append(f"formulas[{idx}].source_reports must be a non-empty list.")
		else:
			for report_name in source_reports:
				if not get_report_spec(report_name):
					errors.append(
						f"formulas[{idx}].source_reports references unknown report '{report_name}'."
					)

		aggregation_rule = str(item.get("aggregation_rule") or "").strip()
		if aggregation_rule not in allowed_aggregation_rules:
			errors.append(
				f"formulas[{idx}].aggregation_rule must be one of {sorted(allowed_aggregation_rules)}."
			)

		grain_requirements = _as_str_list(item.get("grain_requirements"))
		if not grain_requirements:
			errors.append(f"formulas[{idx}].grain_requirements must be a non-empty list.")

		time_scope_requirements = _as_str_list(item.get("time_scope_requirements"))
		if not time_scope_requirements:
			errors.append(f"formulas[{idx}].time_scope_requirements must be a non-empty list.")
		for requirement in time_scope_requirements:
			if requirement not in allowed_time_scope_requirements:
				errors.append(
					f"formulas[{idx}].time_scope_requirements contains unsupported value '{requirement}'."
				)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"formulas[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"formulas[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="governed_formula_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"formula_count": len([item for item in formulas if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def validate_business_threshold_registry(
	payload: Dict[str, Any] | None = None,
	*,
	business_definition_payload: Dict[str, Any] | None = None,
	governed_formula_payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_business_threshold_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_threshold_bases = set(_as_str_list(data.get("allowed_threshold_bases")))
	allowed_band_directions = set(_as_str_list(data.get("allowed_band_directions")))

	if not allowed_threshold_bases:
		errors.append("allowed_threshold_bases must be a non-empty list.")
	if not allowed_band_directions:
		errors.append("allowed_band_directions must be a non-empty list.")

	definition_source = (
		business_definition_payload
		if isinstance(business_definition_payload, dict)
		else load_business_definition_registry()
	)
	formula_source = (
		governed_formula_payload
		if isinstance(governed_formula_payload, dict)
		else load_governed_formula_registry()
	)
	known_definition_ids = {
		str(item.get("definition_id") or "").strip()
		for item in (definition_source.get("definitions") or [])
		if isinstance(item, dict) and str(item.get("definition_id") or "").strip()
	}
	known_formula_ids = {
		str(item.get("formula_id") or "").strip()
		for item in (formula_source.get("formulas") or [])
		if isinstance(item, dict) and str(item.get("formula_id") or "").strip()
	}

	threshold_sets = data.get("threshold_sets")
	if not isinstance(threshold_sets, list):
		errors.append("threshold_sets must be a list.")
		threshold_sets = []

	seen_threshold_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(threshold_sets):
		if not isinstance(item, dict):
			errors.append(f"threshold_sets[{idx}] must be an object.")
			continue
		threshold_id = str(item.get("threshold_id") or "").strip()
		if not threshold_id:
			errors.append(f"threshold_sets[{idx}].threshold_id must be a non-empty string.")
			continue
		if threshold_id in seen_threshold_ids:
			errors.append(f"threshold_sets contains duplicate threshold_id '{threshold_id}'.")
		seen_threshold_ids.add(threshold_id)

		for field_name in ("label", "owner"):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"threshold_sets[{idx}].{field_name} must be a non-empty string.")

		company_scope = _as_str_list(item.get("company_scope"))
		if not company_scope:
			errors.append(f"threshold_sets[{idx}].company_scope must be a non-empty list.")

		definition_id = str(item.get("definition_id") or "").strip()
		formula_id = str(item.get("formula_id") or "").strip()
		if bool(definition_id) == bool(formula_id):
			errors.append(
				f"threshold_sets[{idx}] must reference exactly one of definition_id or formula_id."
			)
		if definition_id and definition_id not in known_definition_ids:
			errors.append(
				f"threshold_sets[{idx}].definition_id references unknown definition '{definition_id}'."
			)
		if formula_id and formula_id not in known_formula_ids:
			errors.append(
				f"threshold_sets[{idx}].formula_id references unknown formula '{formula_id}'."
			)
		business_rule_id = str(item.get("business_rule_id") or "").strip()
		if business_rule_id and not get_business_rule_spec(business_rule_id):
			errors.append(
				f"threshold_sets[{idx}].business_rule_id references unknown rule '{business_rule_id}'."
			)

		threshold_basis = str(item.get("threshold_basis") or "").strip()
		if threshold_basis not in allowed_threshold_bases:
			errors.append(
				f"threshold_sets[{idx}].threshold_basis must be one of {sorted(allowed_threshold_bases)}."
			)

		band_direction = str(item.get("band_direction") or "").strip()
		if band_direction not in allowed_band_directions:
			errors.append(
				f"threshold_sets[{idx}].band_direction must be one of {sorted(allowed_band_directions)}."
			)

		bands = item.get("bands")
		if not isinstance(bands, list) or not bands:
			errors.append(f"threshold_sets[{idx}].bands must be a non-empty list.")
		else:
			for band_idx, band in enumerate(bands):
				if not isinstance(band, dict):
					errors.append(f"threshold_sets[{idx}].bands[{band_idx}] must be an object.")
					continue
				if not str(band.get("label") or "").strip():
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}].label must be a non-empty string."
					)
				lower_inclusive = _coerce_number(band.get("lower_bound_inclusive"))
				lower_exclusive = _coerce_number(band.get("lower_bound_exclusive"))
				upper_inclusive = _coerce_number(band.get("upper_bound_inclusive"))
				upper_exclusive = _coerce_number(band.get("upper_bound_exclusive"))
				if band.get("lower_bound_inclusive") not in (None, "") and lower_inclusive is None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}].lower_bound_inclusive must be numeric when provided."
					)
				if band.get("lower_bound_exclusive") not in (None, "") and lower_exclusive is None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}].lower_bound_exclusive must be numeric when provided."
					)
				if band.get("upper_bound_inclusive") not in (None, "") and upper_inclusive is None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}].upper_bound_inclusive must be numeric when provided."
					)
				if band.get("upper_bound_exclusive") not in (None, "") and upper_exclusive is None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}].upper_bound_exclusive must be numeric when provided."
					)
				if lower_inclusive is not None and lower_exclusive is not None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}] cannot define both lower_bound_inclusive and lower_bound_exclusive."
					)
				if upper_inclusive is not None and upper_exclusive is not None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}] cannot define both upper_bound_inclusive and upper_bound_exclusive."
					)
				effective_lower = lower_inclusive if lower_inclusive is not None else lower_exclusive
				effective_upper = upper_inclusive if upper_inclusive is not None else upper_exclusive
				if effective_lower is None and effective_upper is None:
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}] must define at least one numeric bound."
					)
				if (
					effective_lower is not None
					and effective_upper is not None
					and effective_lower > effective_upper
				):
					errors.append(
						f"threshold_sets[{idx}].bands[{band_idx}] has lower bound greater than upper bound."
					)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"threshold_sets[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"threshold_sets[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="business_threshold_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"threshold_count": len([item for item in threshold_sets if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def run_business_definition_formula_registry_probe() -> Dict[str, Any]:
	definition_result = validate_business_definition_registry()
	formula_result = validate_governed_formula_registry()
	threshold_result = validate_business_threshold_registry()
	return {
		"ok": all(
			result.status == "pass"
			for result in (definition_result, formula_result, threshold_result)
		),
		"business_definitions": definition_result.to_payload(),
		"governed_formulas": formula_result.to_payload(),
		"business_thresholds": threshold_result.to_payload(),
	}
