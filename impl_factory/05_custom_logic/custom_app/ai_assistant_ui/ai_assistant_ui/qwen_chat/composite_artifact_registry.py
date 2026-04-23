from __future__ import annotations

from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import RegistryValidationResult
from ai_assistant_ui.qwen_chat.metadata import (
	load_composite_artifact_registry,
	load_composite_assembly_registry,
	load_composite_compatibility_registry,
	load_composite_family_registry,
	list_governed_kpi_execution_specs,
)


REQUIRED_ACTIVATION_STATES = {
	"active",
	"blocked_missing_policy",
	"blocked_missing_data",
	"draft_unapproved",
	"deprecated",
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


def validate_composite_family_registry(
	payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_composite_family_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_entity_grains = set(_as_str_list(data.get("allowed_entity_grains")))
	allowed_time_scope_types = set(_as_str_list(data.get("allowed_time_scope_types")))
	allowed_variation_axes = set(_as_str_list(data.get("allowed_variation_axes")))
	allowed_limit_policies = set(_as_str_list(data.get("allowed_limit_policies")))
	allowed_sort_directions = set(_as_str_list(data.get("allowed_sort_directions")))
	allowed_clarification_policies = set(_as_str_list(data.get("allowed_clarification_policies")))

	if not allowed_entity_grains:
		errors.append("allowed_entity_grains must be a non-empty list.")
	if not allowed_time_scope_types:
		errors.append("allowed_time_scope_types must be a non-empty list.")
	if not allowed_variation_axes:
		errors.append("allowed_variation_axes must be a non-empty list.")
	if not allowed_limit_policies:
		errors.append("allowed_limit_policies must be a non-empty list.")
	if not allowed_sort_directions:
		errors.append("allowed_sort_directions must be a non-empty list.")
	if not allowed_clarification_policies:
		errors.append("allowed_clarification_policies must be a non-empty list.")

	families = data.get("families")
	if not isinstance(families, list):
		errors.append("families must be a list.")
		families = []

	seen_family_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(families):
		if not isinstance(item, dict):
			errors.append(f"families[{idx}] must be an object.")
			continue
		family_id = str(item.get("family_id") or "").strip()
		if not family_id:
			errors.append(f"families[{idx}].family_id must be a non-empty string.")
			continue
		if family_id in seen_family_ids:
			errors.append(f"families contains duplicate family_id '{family_id}'.")
		seen_family_ids.add(family_id)

		for field_name in ("label", "owner"):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"families[{idx}].{field_name} must be a non-empty string.")

		company_scope = _as_str_list(item.get("company_scope"))
		if not company_scope:
			errors.append(f"families[{idx}].company_scope must be a non-empty list.")

		subject_alias_value = str(item.get("subject_alias_value") or "").strip()
		if not subject_alias_value:
			warnings.append(f"families[{idx}] does not declare subject_alias_value.")

		metric_semantic_key_map = item.get("metric_semantic_key_map")
		if metric_semantic_key_map is not None and not isinstance(metric_semantic_key_map, dict):
			errors.append(f"families[{idx}].metric_semantic_key_map must be an object when provided.")

		entity_grain = str(item.get("entity_grain") or "").strip()
		if entity_grain not in allowed_entity_grains:
			errors.append(
				f"families[{idx}].entity_grain must be one of {sorted(allowed_entity_grains)}."
			)

		time_scope_type = str(item.get("time_scope_type") or "").strip()
		if time_scope_type not in allowed_time_scope_types:
			errors.append(
				f"families[{idx}].time_scope_type must be one of {sorted(allowed_time_scope_types)}."
			)

		supported_variation_axes = _as_str_list(item.get("supported_variation_axes"))
		if not supported_variation_axes:
			errors.append(f"families[{idx}].supported_variation_axes must be a non-empty list.")
		else:
			for axis in supported_variation_axes:
				if axis not in allowed_variation_axes:
					errors.append(
						f"families[{idx}].supported_variation_axes references unsupported axis '{axis}'."
					)

		supported_variation_values = item.get("supported_variation_values")
		if not isinstance(supported_variation_values, dict):
			errors.append(f"families[{idx}].supported_variation_values must be an object.")

		allowed_primary_metrics = _as_str_list(item.get("allowed_primary_metrics"))
		if not allowed_primary_metrics:
			errors.append(f"families[{idx}].allowed_primary_metrics must be a non-empty list.")

		allowed_secondary_metrics = _as_str_list(item.get("allowed_secondary_metrics"))
		if not allowed_secondary_metrics:
			errors.append(f"families[{idx}].allowed_secondary_metrics must be a non-empty list.")
		elif isinstance(metric_semantic_key_map, dict):
			for metric_id in allowed_primary_metrics + allowed_secondary_metrics:
				if metric_id not in metric_semantic_key_map:
					warnings.append(
						f"families[{idx}].metric_semantic_key_map does not declare semantic aliases for '{metric_id}'."
					)
				elif not _as_str_list(metric_semantic_key_map.get(metric_id)):
					errors.append(
						f"families[{idx}].metric_semantic_key_map['{metric_id}'] must be a non-empty list."
					)

		default_sort_direction = str(item.get("default_sort_direction") or "").strip()
		if default_sort_direction not in allowed_sort_directions:
			errors.append(
				f"families[{idx}].default_sort_direction must be one of {sorted(allowed_sort_directions)}."
			)

		default_limit_policy = str(item.get("default_limit_policy") or "").strip()
		if default_limit_policy not in allowed_limit_policies:
			errors.append(
				f"families[{idx}].default_limit_policy must be one of {sorted(allowed_limit_policies)}."
			)

		clarification_policy = str(item.get("clarification_policy") or "").strip()
		if clarification_policy not in allowed_clarification_policies:
			errors.append(
				f"families[{idx}].clarification_policy must be one of {sorted(allowed_clarification_policies)}."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"families[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"families[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="composite_family_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"family_count": len([item for item in families if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def validate_composite_compatibility_registry(
	payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_composite_compatibility_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_entity_grains = set(_as_str_list(data.get("allowed_entity_grains")))
	allowed_time_scope_types = set(_as_str_list(data.get("allowed_time_scope_types")))
	allowed_join_key_policies = set(_as_str_list(data.get("allowed_join_key_policies")))
	allowed_freshness_policies = set(_as_str_list(data.get("allowed_freshness_policies")))

	if not allowed_entity_grains:
		errors.append("allowed_entity_grains must be a non-empty list.")
	if not allowed_time_scope_types:
		errors.append("allowed_time_scope_types must be a non-empty list.")
	if not allowed_join_key_policies:
		errors.append("allowed_join_key_policies must be a non-empty list.")
	if not allowed_freshness_policies:
		errors.append("allowed_freshness_policies must be a non-empty list.")

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
		rule_id = str(item.get("compatibility_rule_id") or "").strip()
		if not rule_id:
			errors.append(f"rules[{idx}].compatibility_rule_id must be a non-empty string.")
			continue
		if rule_id in seen_rule_ids:
			errors.append(f"rules contains duplicate compatibility_rule_id '{rule_id}'.")
		seen_rule_ids.add(rule_id)

		if not str(item.get("label") or "").strip():
			errors.append(f"rules[{idx}].label must be a non-empty string.")

		entity_grain = str(item.get("allowed_entity_grain") or "").strip()
		if entity_grain not in allowed_entity_grains:
			errors.append(
				f"rules[{idx}].allowed_entity_grain must be one of {sorted(allowed_entity_grains)}."
			)

		time_scope_type = str(item.get("allowed_time_scope_type") or "").strip()
		if time_scope_type not in allowed_time_scope_types:
			errors.append(
				f"rules[{idx}].allowed_time_scope_type must be one of {sorted(allowed_time_scope_types)}."
			)

		for field_name in ("required_period_alignment", "required_as_of_alignment", "required_scope_alignment", "block_on_missing_metric"):
			if not isinstance(item.get(field_name), bool):
				errors.append(f"rules[{idx}].{field_name} must be a boolean.")

		join_key_policy = str(item.get("join_key_policy") or "").strip()
		if join_key_policy not in allowed_join_key_policies:
			errors.append(
				f"rules[{idx}].join_key_policy must be one of {sorted(allowed_join_key_policies)}."
			)

		freshness_policy = str(item.get("freshness_policy") or "").strip()
		if freshness_policy not in allowed_freshness_policies:
			errors.append(
				f"rules[{idx}].freshness_policy must be one of {sorted(allowed_freshness_policies)}."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"rules[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		_validate_blocked_reason(
			label=f"rules[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="composite_compatibility_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"compatibility_rule_count": len([item for item in rules if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def validate_composite_assembly_registry(
	payload: Dict[str, Any] | None = None,
	*,
	composite_family_payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_composite_assembly_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_join_key_fields = set(_as_str_list(data.get("allowed_join_key_fields")))
	allowed_row_identity_policies = set(_as_str_list(data.get("allowed_row_identity_policies")))
	allowed_row_merge_policies = set(_as_str_list(data.get("allowed_row_merge_policies")))
	allowed_row_missing_component_policies = set(_as_str_list(data.get("allowed_row_missing_component_policies")))
	allowed_row_provenance_policies = set(_as_str_list(data.get("allowed_row_provenance_policies")))

	if not allowed_join_key_fields:
		errors.append("allowed_join_key_fields must be a non-empty list.")
	if not allowed_row_identity_policies:
		errors.append("allowed_row_identity_policies must be a non-empty list.")
	if not allowed_row_merge_policies:
		errors.append("allowed_row_merge_policies must be a non-empty list.")
	if not allowed_row_missing_component_policies:
		errors.append("allowed_row_missing_component_policies must be a non-empty list.")
	if not allowed_row_provenance_policies:
		errors.append("allowed_row_provenance_policies must be a non-empty list.")

	family_source = (
		composite_family_payload
		if isinstance(composite_family_payload, dict)
		else load_composite_family_registry()
	)
	known_family_ids = {
		str(item.get("family_id") or "").strip()
		for item in (family_source.get("families") or [])
		if isinstance(item, dict) and str(item.get("family_id") or "").strip()
	}
	known_execution_ids = {
		str(item.get("execution_id") or "").strip()
		for item in list_governed_kpi_execution_specs()
		if isinstance(item, dict) and str(item.get("execution_id") or "").strip()
	}

	assemblies = data.get("assemblies")
	if not isinstance(assemblies, list):
		errors.append("assemblies must be a list.")
		assemblies = []

	seen_assembly_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(assemblies):
		if not isinstance(item, dict):
			errors.append(f"assemblies[{idx}] must be an object.")
			continue
		assembly_id = str(item.get("assembly_id") or "").strip()
		if not assembly_id:
			errors.append(f"assemblies[{idx}].assembly_id must be a non-empty string.")
			continue
		if assembly_id in seen_assembly_ids:
			errors.append(f"assemblies contains duplicate assembly_id '{assembly_id}'.")
		seen_assembly_ids.add(assembly_id)

		family_id = str(item.get("family_id") or "").strip()
		if family_id not in known_family_ids:
			errors.append(f"assemblies[{idx}].family_id references unknown family '{family_id}'.")

		component_metric_ids = _as_str_list(item.get("component_metric_ids"))
		if not component_metric_ids:
			errors.append(f"assemblies[{idx}].component_metric_ids must be a non-empty list.")

		component_execution_ids = _as_str_list(item.get("component_execution_ids"))
		if not component_execution_ids:
			errors.append(f"assemblies[{idx}].component_execution_ids must be a non-empty list.")

		join_key_schema = _as_str_list(item.get("join_key_schema"))
		if not join_key_schema:
			errors.append(f"assemblies[{idx}].join_key_schema must be a non-empty list.")
		else:
			for key_name in join_key_schema:
				if key_name not in allowed_join_key_fields:
					errors.append(
						f"assemblies[{idx}].join_key_schema references unsupported join field '{key_name}'."
					)

		row_identity_policy = str(item.get("row_identity_policy") or "").strip()
		if row_identity_policy not in allowed_row_identity_policies:
			errors.append(
				f"assemblies[{idx}].row_identity_policy must be one of {sorted(allowed_row_identity_policies)}."
			)

		row_merge_policy = str(item.get("row_merge_policy") or "").strip()
		if row_merge_policy not in allowed_row_merge_policies:
			errors.append(
				f"assemblies[{idx}].row_merge_policy must be one of {sorted(allowed_row_merge_policies)}."
			)

		row_missing_component_policy = str(item.get("row_missing_component_policy") or "").strip()
		if row_missing_component_policy not in allowed_row_missing_component_policies:
			errors.append(
				f"assemblies[{idx}].row_missing_component_policy must be one of {sorted(allowed_row_missing_component_policies)}."
			)

		row_provenance_policy = str(item.get("row_provenance_policy") or "").strip()
		if row_provenance_policy not in allowed_row_provenance_policies:
			errors.append(
				f"assemblies[{idx}].row_provenance_policy must be one of {sorted(allowed_row_provenance_policies)}."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"assemblies[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		for execution_id in component_execution_ids:
			if execution_id not in known_execution_ids:
				message = (
					f"assemblies[{idx}].component_execution_ids references unknown execution '{execution_id}'."
				)
				if activation_state == "active":
					errors.append(message)
				else:
					warnings.append(message)

		_validate_blocked_reason(
			label=f"assemblies[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="composite_assembly_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"assembly_count": len([item for item in assemblies if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def validate_composite_artifact_registry(
	payload: Dict[str, Any] | None = None,
	*,
	composite_family_payload: Dict[str, Any] | None = None,
	composite_compatibility_payload: Dict[str, Any] | None = None,
	composite_assembly_payload: Dict[str, Any] | None = None,
) -> RegistryValidationResult:
	data = payload if isinstance(payload, dict) else load_composite_artifact_registry()
	errors: List[str] = []
	warnings: List[str] = []

	if str(data.get("contract_version") or "").strip() != "1.0":
		errors.append("contract_version must be '1.0'.")

	allowed_states = _validate_activation_states(data, errors)
	allowed_composite_kinds = set(_as_str_list(data.get("allowed_composite_kinds")))
	allowed_render_styles = set(_as_str_list(data.get("allowed_render_styles")))
	if not allowed_composite_kinds:
		errors.append("allowed_composite_kinds must be a non-empty list.")
	if not allowed_render_styles:
		errors.append("allowed_render_styles must be a non-empty list.")

	family_source = (
		composite_family_payload
		if isinstance(composite_family_payload, dict)
		else load_composite_family_registry()
	)
	compatibility_source = (
		composite_compatibility_payload
		if isinstance(composite_compatibility_payload, dict)
		else load_composite_compatibility_registry()
	)
	assembly_source = (
		composite_assembly_payload
		if isinstance(composite_assembly_payload, dict)
		else load_composite_assembly_registry()
	)
	known_families = {
		str(item.get("family_id") or "").strip(): dict(item)
		for item in (family_source.get("families") or [])
		if isinstance(item, dict) and str(item.get("family_id") or "").strip()
	}
	known_compatibility_ids = {
		str(item.get("compatibility_rule_id") or "").strip()
		for item in (compatibility_source.get("rules") or [])
		if isinstance(item, dict) and str(item.get("compatibility_rule_id") or "").strip()
	}
	known_assembly_ids = {
		str(item.get("assembly_id") or "").strip()
		for item in (assembly_source.get("assemblies") or [])
		if isinstance(item, dict) and str(item.get("assembly_id") or "").strip()
	}
	known_execution_ids = {
		str(item.get("execution_id") or "").strip()
		for item in list_governed_kpi_execution_specs()
		if isinstance(item, dict) and str(item.get("execution_id") or "").strip()
	}

	artifacts = data.get("artifacts")
	if not isinstance(artifacts, list):
		errors.append("artifacts must be a list.")
		artifacts = []

	seen_composite_ids: Set[str] = set()
	activation_counts: Dict[str, int] = {}
	for idx, item in enumerate(artifacts):
		if not isinstance(item, dict):
			errors.append(f"artifacts[{idx}] must be an object.")
			continue
		composite_id = str(item.get("composite_id") or "").strip()
		if not composite_id:
			errors.append(f"artifacts[{idx}].composite_id must be a non-empty string.")
			continue
		if composite_id in seen_composite_ids:
			errors.append(f"artifacts contains duplicate composite_id '{composite_id}'.")
		seen_composite_ids.add(composite_id)

		for field_name in ("label", "primary_metric_id", "assembly_id"):
			if not str(item.get(field_name) or "").strip():
				errors.append(f"artifacts[{idx}].{field_name} must be a non-empty string.")

		family_id = str(item.get("family_id") or "").strip()
		family_spec = known_families.get(family_id)
		if not family_spec:
			errors.append(f"artifacts[{idx}].family_id references unknown family '{family_id}'.")

		composite_kind = str(item.get("composite_kind") or "").strip()
		if composite_kind not in allowed_composite_kinds:
			errors.append(
				f"artifacts[{idx}].composite_kind must be one of {sorted(allowed_composite_kinds)}."
			)

		if family_spec:
			if str(item.get("entity_grain") or "").strip() != str(family_spec.get("entity_grain") or "").strip():
				errors.append(
					f"artifacts[{idx}].entity_grain must match family '{family_id}'."
				)
			if str(item.get("time_scope_type") or "").strip() != str(family_spec.get("time_scope_type") or "").strip():
				errors.append(
					f"artifacts[{idx}].time_scope_type must match family '{family_id}'."
				)
			allowed_primary = set(_as_str_list(family_spec.get("allowed_primary_metrics")))
			allowed_secondary = set(_as_str_list(family_spec.get("allowed_secondary_metrics")))
			primary_metric_id = str(item.get("primary_metric_id") or "").strip()
			if primary_metric_id and allowed_primary and primary_metric_id not in allowed_primary:
				errors.append(
					f"artifacts[{idx}].primary_metric_id '{primary_metric_id}' is not allowed by family '{family_id}'."
				)
			for metric_id in _as_str_list(item.get("secondary_metric_ids")):
				if allowed_secondary and metric_id not in allowed_secondary:
					errors.append(
						f"artifacts[{idx}].secondary_metric_ids contains metric '{metric_id}' not allowed by family '{family_id}'."
					)

		required_execution_ids = _as_str_list(item.get("required_execution_ids"))
		if not required_execution_ids:
			errors.append(f"artifacts[{idx}].required_execution_ids must be a non-empty list.")

		assembly_id = str(item.get("assembly_id") or "").strip()
		if assembly_id and assembly_id not in known_assembly_ids:
			errors.append(f"artifacts[{idx}].assembly_id references unknown assembly '{assembly_id}'.")

		compatibility_rule_ids = _as_str_list(item.get("compatibility_rule_ids"))
		if not compatibility_rule_ids:
			errors.append(f"artifacts[{idx}].compatibility_rule_ids must be a non-empty list.")
		else:
			for rule_id in compatibility_rule_ids:
				if rule_id not in known_compatibility_ids:
					errors.append(
						f"artifacts[{idx}].compatibility_rule_ids references unknown rule '{rule_id}'."
					)

		render_style = str(item.get("render_style") or "").strip()
		if render_style not in allowed_render_styles:
			errors.append(
				f"artifacts[{idx}].render_style must be one of {sorted(allowed_render_styles)}."
			)

		activation_state = str(item.get("activation_state") or "").strip()
		if activation_state not in allowed_states:
			errors.append(
				f"artifacts[{idx}].activation_state must be one of {sorted(allowed_states)}."
			)
		else:
			activation_counts[activation_state] = activation_counts.get(activation_state, 0) + 1

		for execution_id in required_execution_ids:
			if execution_id not in known_execution_ids:
				message = (
					f"artifacts[{idx}].required_execution_ids references unknown execution '{execution_id}'."
				)
				if activation_state == "active":
					errors.append(message)
				else:
					warnings.append(message)

		_validate_blocked_reason(
			label=f"artifacts[{idx}]",
			activation_state=activation_state,
			blocked_reason=str(item.get("blocked_reason") or "").strip(),
			errors=errors,
			warnings=warnings,
		)

	return RegistryValidationResult(
		registry_name="composite_artifact_registry",
		status="pass" if not errors else "fail",
		errors=errors,
		warnings=warnings,
		stats={
			"artifact_count": len([item for item in artifacts if isinstance(item, dict)]),
			"allowed_activation_state_count": len(allowed_states),
			"activation_counts": activation_counts,
		},
	)


def run_composite_artifact_registry_probe() -> Dict[str, Any]:
	family_result = validate_composite_family_registry()
	compatibility_result = validate_composite_compatibility_registry()
	assembly_result = validate_composite_assembly_registry()
	artifact_result = validate_composite_artifact_registry()
	ok = all(
		result.status == "pass"
		for result in (family_result, compatibility_result, assembly_result, artifact_result)
	)
	return {
		"ok": ok,
		"family_registry": family_result.to_payload(),
		"compatibility_registry": compatibility_result.to_payload(),
		"assembly_registry": assembly_result.to_payload(),
		"artifact_registry": artifact_result.to_payload(),
	}
