from __future__ import annotations

from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import (
	RegistryValidationResult,
)
from ai_assistant_ui.qwen_chat.metadata import (
	list_capability_specs,
	load_business_definition_registry,
	load_governed_formula_registry,
	load_governed_kpi_execution_registry,
	get_report_spec,
)


REQUIRED_ACTIVATION_STATES = {
	"active",
	"blocked_missing_policy",
	"blocked_missing_data",
	"draft_unapproved",
	"deprecated",
}

_EXECUTION_SHAPE_SCOPE_MAP = {
	"company_period_scalar": "company",
	"customer_as_of_scalar": "customer",
	"customer_as_of_ranking": "customer_set",
}

_EXECUTION_SHAPE_TIME_SCOPE_MAP = {
	"company_period_scalar": "period_required",
	"customer_as_of_scalar": "as_of_date_required",
	"customer_as_of_ranking": "as_of_date_required",
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


def validate_governed_kpi_execution_registry(
	payload: Dict[str, Any] | None = None,
	*,
	business_definition_payload: Dict[str, Any] | None = None,
	governed_formula_payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_governed_kpi_execution_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_execution_shapes = set(_as_str_list(data.get("allowed_execution_shapes")))
	allowed_scope_types = set(_as_str_list(data.get("allowed_scope_types")))
	allowed_time_scope_types = set(_as_str_list(data.get("allowed_time_scope_types")))
	allowed_source_modes = set(_as_str_list(data.get("allowed_source_modes")))
	allowed_value_unit_types = set(_as_str_list(data.get("allowed_value_unit_types")))

	if not allowed_execution_shapes:
		errors.append("allowed_execution_shapes must be a non-empty list.")
	if not allowed_scope_types:
		errors.append("allowed_scope_types must be a non-empty list.")
	if not allowed_time_scope_types:
		errors.append("allowed_time_scope_types must be a non-empty list.")
	if not allowed_source_modes:
		errors.append("allowed_source_modes must be a non-empty list.")
	if not allowed_value_unit_types:
		errors.append("allowed_value_unit_types must be a non-empty list.")

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
	known_formula_specs = {
		str(item.get("formula_id") or "").strip(): dict(item)
		for item in (formula_source.get("formulas") or [])
		if isinstance(item, dict) and str(item.get("formula_id") or "").strip()
	}
	known_capabilities = {
		str(item.get("capability_id") or "").strip()
		for item in list_capability_specs()
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	}

	executions = data.get("executions")
	if not isinstance(executions, list):
		errors.append("executions must be a list.")
		executions = []

	seen_execution_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	shape_counts: Dict[str, int] = {}
	for idx, item in enumerate(executions):
		if not isinstance(item, dict):
			errors.append(f"executions[{idx}] must be an object.")
			continue
		execution_id = str(item.get("execution_id") or "").strip()
		if not execution_id:
			errors.append(f"executions[{idx}].execution_id must be a non-empty string.")
			continue
		if execution_id in seen_execution_ids:
			errors.append(f"executions contains duplicate execution_id '{execution_id}'.")
		seen_execution_ids.add(execution_id)

		for field_name in ("label",):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"executions[{idx}].{field_name} must be a non-empty string.")

		definition_id = str(item.get("definition_id") or "").strip()
		if definition_id not in known_definition_ids:
			errors.append(
				f"executions[{idx}].definition_id references unknown definition '{definition_id}'."
			)

		formula_id = str(item.get("formula_id") or "").strip()
		formula_spec = known_formula_specs.get(formula_id)
		if not formula_spec:
			errors.append(
				f"executions[{idx}].formula_id references unknown formula '{formula_id}'."
			)
		elif str(formula_spec.get("definition_id") or "").strip() != definition_id:
			errors.append(
				f"executions[{idx}].formula_id '{formula_id}' does not belong to definition '{definition_id}'."
			)

		execution_shape = str(item.get("execution_shape") or "").strip()
		if execution_shape not in allowed_execution_shapes:
			errors.append(
				f"executions[{idx}].execution_shape must be one of {sorted(allowed_execution_shapes)}."
			)
		else:
			shape_counts[execution_shape] = shape_counts.get(execution_shape, 0) + 1

		scope_type = str(item.get("scope_type") or "").strip()
		if scope_type not in allowed_scope_types:
			errors.append(
				f"executions[{idx}].scope_type must be one of {sorted(allowed_scope_types)}."
			)
		elif execution_shape and _EXECUTION_SHAPE_SCOPE_MAP.get(execution_shape) != scope_type:
			errors.append(
				f"executions[{idx}].scope_type must be '{_EXECUTION_SHAPE_SCOPE_MAP.get(execution_shape)}' for execution_shape '{execution_shape}'."
			)

		time_scope_type = str(item.get("time_scope_type") or "").strip()
		if time_scope_type not in allowed_time_scope_types:
			errors.append(
				f"executions[{idx}].time_scope_type must be one of {sorted(allowed_time_scope_types)}."
			)
		elif execution_shape and _EXECUTION_SHAPE_TIME_SCOPE_MAP.get(execution_shape) != time_scope_type:
			errors.append(
				f"executions[{idx}].time_scope_type must be '{_EXECUTION_SHAPE_TIME_SCOPE_MAP.get(execution_shape)}' for execution_shape '{execution_shape}'."
			)

		source_mode = str(item.get("source_mode") or "").strip()
		if source_mode not in allowed_source_modes:
			errors.append(
				f"executions[{idx}].source_mode must be one of {sorted(allowed_source_modes)}."
			)

		source_capabilities = _as_str_list(item.get("source_capabilities"))
		if not source_capabilities:
			errors.append(f"executions[{idx}].source_capabilities must be a non-empty list.")
		else:
			for capability_id in source_capabilities:
				if capability_id not in known_capabilities:
					errors.append(
						f"executions[{idx}].source_capabilities references unknown capability '{capability_id}'."
					)

		source_reports = _as_str_list(item.get("source_reports"))
		if not source_reports:
			errors.append(f"executions[{idx}].source_reports must be a non-empty list.")
		else:
			for report_name in source_reports:
				if not get_report_spec(report_name):
					errors.append(
						f"executions[{idx}].source_reports references unknown report '{report_name}'."
					)

		supported_filters = item.get("supported_filters")
		if not isinstance(supported_filters, list) or not _as_str_list(supported_filters):
			errors.append(f"executions[{idx}].supported_filters must be a non-empty list.")

		required_dimensions = item.get("required_dimensions")
		if not isinstance(required_dimensions, list):
			errors.append(f"executions[{idx}].required_dimensions must be a list.")
		elif scope_type in {"customer", "customer_set"} and "customer" not in _as_str_list(required_dimensions):
			errors.append(
				f"executions[{idx}].required_dimensions must include 'customer' for scope_type '{scope_type}'."
			)

		value_unit_type = str(item.get("value_unit_type") or "").strip()
		if value_unit_type not in allowed_value_unit_types:
			errors.append(
				f"executions[{idx}].value_unit_type must be one of {sorted(allowed_value_unit_types)}."
			)

		value_metric_mapping = item.get("value_metric_mapping")
		if not isinstance(value_metric_mapping, dict) or not value_metric_mapping:
			errors.append(f"executions[{idx}].value_metric_mapping must be a non-empty object.")
		elif not str(value_metric_mapping.get("value_metric") or "").strip():
			errors.append(
				f"executions[{idx}].value_metric_mapping.value_metric must be a non-empty string."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"executions[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"executions[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

		if formula_spec:
			formula_time_scope_requirements = {
				str(value or "").strip()
				for value in (formula_spec.get("time_scope_requirements") or [])
				if str(value or "").strip()
			}
			if time_scope_type not in formula_time_scope_requirements:
				errors.append(
					f"executions[{idx}].time_scope_type '{time_scope_type}' is not supported by formula '{formula_id}'."
				)
			formula_grains = {
				str(value or "").strip()
				for value in (formula_spec.get("grain_requirements") or [])
				if str(value or "").strip()
			}
			expected_grain = "customer" if scope_type in {"customer", "customer_set"} else scope_type
			if expected_grain not in formula_grains:
				errors.append(
					f"executions[{idx}] scope_type '{scope_type}' is incompatible with formula grain requirements {sorted(formula_grains)}."
				)

	return RegistryValidationResult(
		registry_name="governed_kpi_execution_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"execution_count": len([item for item in executions if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
			"execution_shape_counts": shape_counts,
		},
	)


def run_governed_kpi_execution_registry_probe() -> Dict[str, Any]:
	validation = validate_governed_kpi_execution_registry()
	ok = (
		validation.status == "pass"
		and validation.stats.get("execution_count") == 10
		and validation.stats.get("activation_counts", {}).get("active") == 10
		and validation.stats.get("execution_shape_counts", {}).get("company_period_scalar") == 3
		and validation.stats.get("execution_shape_counts", {}).get("customer_as_of_scalar") == 5
		and validation.stats.get("execution_shape_counts", {}).get("customer_as_of_ranking") == 2
	)
	return {
		"ok": ok,
		"validation": validation.to_payload(),
	}
