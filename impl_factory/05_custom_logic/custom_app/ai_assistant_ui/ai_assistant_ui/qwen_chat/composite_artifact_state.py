from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	list_composite_artifact_specs,
	list_composite_artifact_specs_for_family,
	list_composite_assembly_specs_for_family,
	list_composite_compatibility_specs,
	list_composite_family_specs,
)


ALLOWED_FAMILY_RESOLUTION_STATES = {
	"resolved_family",
	"clarify_family_variation",
	"blocked_no_governed_family",
	"blocked_unsupported_family_variation",
}

ALLOWED_COMPOSITE_RESOLUTION_STATES = {
	"active_composite",
	"clarify_scope",
	"clarify_metric_basis",
	"blocked_incompatible_grain",
	"blocked_incompatible_time_scope",
	"blocked_missing_component",
	"unsupported_composite_shape",
	"blocked_no_governed_family",
	"blocked_unsupported_family_variation",
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


def _as_dict_list(value: Any) -> List[Dict[str, Any]]:
	if not isinstance(value, list):
		return []
	return [dict(item) for item in value if isinstance(item, dict)]


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _company_scope_matches(values: Any, company_name: str) -> bool:
	scope_values = [_clean_text(item).lower() for item in (values or []) if _clean_text(item)]
	if not scope_values:
		return True
	normalized_company = _clean_text(company_name).lower()
	return not normalized_company or "global" in scope_values or normalized_company in scope_values


def _requested_time_scope_type(variation_inputs: Dict[str, Any]) -> str:
	as_of_date = _clean_text(variation_inputs.get("requested_as_of_date"))
	period_start = _clean_text(variation_inputs.get("requested_period_start"))
	period_end = _clean_text(variation_inputs.get("requested_period_end"))
	if as_of_date:
		return "as_of_date_required"
	if period_start and period_end:
		return "period_required"
	return ""


def _variation_value_supported(family_spec: Dict[str, Any], axis: str, requested_value: str) -> bool:
	variation_values = family_spec.get("supported_variation_values")
	if not isinstance(variation_values, dict):
		return False
	allowed_values = _as_str_list(variation_values.get(axis))
	if not allowed_values:
		return False
	return requested_value in allowed_values


def _supported_variation_axes(family_spec: Dict[str, Any]) -> List[str]:
	return _as_str_list(family_spec.get("supported_variation_axes"))


def _primary_metric_matches_family(family_spec: Dict[str, Any], requested_primary_metric: str) -> bool:
	primary_metric = _clean_text(requested_primary_metric)
	if not primary_metric:
		return True
	allowed_values = set(_as_str_list(family_spec.get("allowed_primary_metrics")))
	return not allowed_values or primary_metric in allowed_values


def _secondary_metrics_match_family(family_spec: Dict[str, Any], requested_secondary_metrics: List[str]) -> bool:
	metrics = [_clean_text(value) for value in requested_secondary_metrics if _clean_text(value)]
	if not metrics:
		return True
	allowed_values = set(_as_str_list(family_spec.get("allowed_secondary_metrics")))
	return not allowed_values or set(metrics).issubset(allowed_values)


def _basis_matches_family(family_spec: Dict[str, Any], requested_basis: str) -> bool:
	basis = _clean_text(requested_basis)
	if not basis:
		return "basis" not in set(_supported_variation_axes(family_spec))
	return _variation_value_supported(family_spec, "basis", basis)


def _scope_matches_family(family_spec: Dict[str, Any], variation_inputs: Dict[str, Any]) -> bool:
	time_scope_type = _clean_text(family_spec.get("time_scope_type"))
	requested_scope_type = _requested_time_scope_type(variation_inputs)
	if not requested_scope_type:
		return not time_scope_type
	return time_scope_type == requested_scope_type


def _missing_family_clarifications(
	family_spec: Dict[str, Any],
	variation_inputs: Dict[str, Any],
	requested_primary_metric: str = "",
) -> List[str]:
	missing: List[str] = []
	supported_axes = set(_supported_variation_axes(family_spec))
	if "primary_sort_metric" in supported_axes and not _clean_text(requested_primary_metric):
		missing.append("primary_sort_metric")
	requested_basis = _clean_text(variation_inputs.get("requested_basis"))
	if "basis" in supported_axes and not requested_basis:
		missing.append("basis")

	time_scope_type = _clean_text(family_spec.get("time_scope_type"))
	requested_period_start = _clean_text(variation_inputs.get("requested_period_start"))
	requested_period_end = _clean_text(variation_inputs.get("requested_period_end"))
	requested_as_of_date = _clean_text(variation_inputs.get("requested_as_of_date"))
	if time_scope_type == "period_required" and not (requested_period_start and requested_period_end):
		missing.append("scope")
	if time_scope_type == "as_of_date_required" and not requested_as_of_date:
		missing.append("scope")
	return missing


def _artifact_variation_matches(
	artifact_spec: Dict[str, Any],
	variation_inputs: Dict[str, Any],
	requested_secondary_metrics: List[str] | None = None,
) -> bool:
	requirements = artifact_spec.get("variation_requirements")
	if not isinstance(requirements, dict):
		requirements = {}
	requested_basis = _clean_text(variation_inputs.get("requested_basis"))
	required_basis = _clean_text(requirements.get("basis"))
	if required_basis and requested_basis and requested_basis != required_basis:
		return False
	requested_secondary_metric_values = {_clean_text(value) for value in (requested_secondary_metrics or []) if _clean_text(value)}
	artifact_secondary_metric_values = {
		_clean_text(value)
		for value in (artifact_spec.get("secondary_metric_ids") or [])
		if _clean_text(value)
	}
	if requested_secondary_metric_values and not requested_secondary_metric_values.issubset(artifact_secondary_metric_values):
		return False
	return True


@dataclass(frozen=True)
class CompositeFamilyResolutionContract:
	resolution_type: str
	requested_company_name: str
	requested_family_id: str
	family_id: str
	family_label: str
	requested_primary_metric: str
	requested_secondary_metrics: List[str] = field(default_factory=list)
	requested_basis: str = ""
	requested_period_start: str = ""
	requested_period_end: str = ""
	requested_as_of_date: str = ""
	requested_limit: int = 0
	requested_sort_direction: str = ""
	variation_inputs: Dict[str, Any] = field(default_factory=dict)
	missing_clarifications: List[str] = field(default_factory=list)
	status: str = "blocked_no_governed_family"
	blocked_reason: str = ""
	reason: str = ""
	candidate_families: List[Dict[str, Any]] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_composite_family_resolution_contract",
			"contract_version": "1.0",
			"resolution_type": self.resolution_type,
			"requested_company_name": self.requested_company_name,
			"requested_family_id": self.requested_family_id,
			"family_id": self.family_id,
			"family_label": self.family_label,
			"requested_primary_metric": self.requested_primary_metric,
			"requested_secondary_metrics": list(self.requested_secondary_metrics),
			"requested_basis": self.requested_basis,
			"requested_period_start": self.requested_period_start,
			"requested_period_end": self.requested_period_end,
			"requested_as_of_date": self.requested_as_of_date,
			"requested_limit": int(max(0, self.requested_limit)),
			"requested_sort_direction": self.requested_sort_direction,
			"variation_inputs": dict(self.variation_inputs),
			"missing_clarifications": list(self.missing_clarifications),
			"status": self.status,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
			"candidate_families": [dict(item) for item in self.candidate_families if isinstance(item, dict)],
		}


@dataclass(frozen=True)
class CompositeArtifactResolutionContract:
	requested_company_name: str
	family_resolution_status: str
	family_id: str
	family_label: str
	composite_id: str
	label: str
	composite_kind: str
	entity_grain: str
	time_scope_type: str
	assembly_id: str
	compatibility_rule_ids: List[str] = field(default_factory=list)
	required_execution_ids: List[str] = field(default_factory=list)
	status: str = "blocked_no_governed_family"
	activation_state: str = ""
	blocked_reason: str = ""
	reason: str = ""
	candidate_composites: List[Dict[str, Any]] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_composite_artifact_resolution_contract",
			"contract_version": "1.0",
			"requested_company_name": self.requested_company_name,
			"family_resolution_status": self.family_resolution_status,
			"family_id": self.family_id,
			"family_label": self.family_label,
			"composite_id": self.composite_id,
			"label": self.label,
			"composite_kind": self.composite_kind,
			"entity_grain": self.entity_grain,
			"time_scope_type": self.time_scope_type,
			"assembly_id": self.assembly_id,
			"compatibility_rule_ids": list(self.compatibility_rule_ids),
			"required_execution_ids": list(self.required_execution_ids),
			"status": self.status,
			"activation_state": self.activation_state,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
			"candidate_composites": [dict(item) for item in self.candidate_composites if isinstance(item, dict)],
		}


@dataclass(frozen=True)
class CompositeAssemblyAdapterContract:
	assembly_id: str
	family_id: str
	component_metric_ids: List[str] = field(default_factory=list)
	component_execution_ids: List[str] = field(default_factory=list)
	join_key_schema: List[str] = field(default_factory=list)
	row_identity_policy: str = ""
	row_merge_policy: str = ""
	row_missing_component_policy: str = ""
	row_provenance_policy: str = ""
	status: str = "blocked_missing_component"
	blocked_reason: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_composite_assembly_adapter_contract",
			"contract_version": "1.0",
			"assembly_id": self.assembly_id,
			"family_id": self.family_id,
			"component_metric_ids": list(self.component_metric_ids),
			"component_execution_ids": list(self.component_execution_ids),
			"join_key_schema": list(self.join_key_schema),
			"row_identity_policy": self.row_identity_policy,
			"row_merge_policy": self.row_merge_policy,
			"row_missing_component_policy": self.row_missing_component_policy,
			"row_provenance_policy": self.row_provenance_policy,
			"status": self.status,
			"blocked_reason": self.blocked_reason,
		}


@dataclass(frozen=True)
class CompositeGovernedArtifactContract:
	artifact_type: str
	composite_id: str
	label: str
	composite_kind: str
	primary_metric_id: str
	secondary_metric_ids: List[str] = field(default_factory=list)
	entity_grain: str = ""
	time_scope_type: str = ""
	scope: Dict[str, Any] = field(default_factory=dict)
	period_start: str = ""
	period_end: str = ""
	as_of_date: str = ""
	row_count: int = 0
	source_document_count: int = 0
	rows: List[Dict[str, Any]] = field(default_factory=list)
	source_artifact_refs: List[Dict[str, Any]] = field(default_factory=list)
	compatibility_status: str = ""
	blocked_reason: str = ""
	render_policy: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": self.artifact_type,
			"contract_version": "1.0",
			"composite_id": self.composite_id,
			"label": self.label,
			"composite_kind": self.composite_kind,
			"primary_metric_id": self.primary_metric_id,
			"secondary_metric_ids": list(self.secondary_metric_ids),
			"entity_grain": self.entity_grain,
			"time_scope_type": self.time_scope_type,
			"scope": dict(self.scope),
			"period_start": self.period_start,
			"period_end": self.period_end,
			"as_of_date": self.as_of_date,
			"row_count": int(max(0, self.row_count)),
			"source_document_count": int(max(0, self.source_document_count)),
			"rows": [dict(item) for item in self.rows if isinstance(item, dict)],
			"source_artifact_refs": [dict(item) for item in self.source_artifact_refs if isinstance(item, dict)],
			"compatibility_status": self.compatibility_status,
			"blocked_reason": self.blocked_reason,
			"render_policy": dict(self.render_policy),
		}


def build_composite_family_resolution_contract(
	*,
	resolution_type: str = "governed_family_resolution",
	requested_company_name: str = "",
	requested_family_id: str = "",
	family_id: str = "",
	family_label: str = "",
	requested_primary_metric: str = "",
	requested_secondary_metrics: List[str] | None = None,
	requested_basis: str = "",
	requested_period_start: str = "",
	requested_period_end: str = "",
	requested_as_of_date: str = "",
	requested_limit: int = 0,
	requested_sort_direction: str = "",
	variation_inputs: Dict[str, Any] | None = None,
	missing_clarifications: List[str] | None = None,
	status: str = "blocked_no_governed_family",
	blocked_reason: str = "",
	reason: str = "",
	candidate_families: List[Dict[str, Any]] | None = None,
) -> CompositeFamilyResolutionContract:
	normalized_status = _clean_text(status).lower() or "blocked_no_governed_family"
	if normalized_status not in ALLOWED_FAMILY_RESOLUTION_STATES:
		normalized_status = "blocked_no_governed_family"
	return CompositeFamilyResolutionContract(
		resolution_type=_clean_text(resolution_type) or "governed_family_resolution",
		requested_company_name=_clean_text(requested_company_name),
		requested_family_id=_clean_text(requested_family_id),
		family_id=_clean_text(family_id),
		family_label=_clean_text(family_label),
		requested_primary_metric=_clean_text(requested_primary_metric),
		requested_secondary_metrics=_as_str_list(requested_secondary_metrics or []),
		requested_basis=_clean_text(requested_basis),
		requested_period_start=_clean_text(requested_period_start),
		requested_period_end=_clean_text(requested_period_end),
		requested_as_of_date=_clean_text(requested_as_of_date),
		requested_limit=int(max(0, int(requested_limit or 0))),
		requested_sort_direction=_clean_text(requested_sort_direction),
		variation_inputs=dict(variation_inputs or {}),
		missing_clarifications=_as_str_list(missing_clarifications or []),
		status=normalized_status,
		blocked_reason=_clean_text(blocked_reason),
		reason=_clean_text(reason),
		candidate_families=_as_dict_list(candidate_families or []),
	)


def build_composite_artifact_resolution_contract(
	*,
	requested_company_name: str = "",
	family_resolution_status: str = "",
	family_id: str = "",
	family_label: str = "",
	composite_id: str = "",
	label: str = "",
	composite_kind: str = "",
	entity_grain: str = "",
	time_scope_type: str = "",
	assembly_id: str = "",
	compatibility_rule_ids: List[str] | None = None,
	required_execution_ids: List[str] | None = None,
	status: str = "blocked_no_governed_family",
	activation_state: str = "",
	blocked_reason: str = "",
	reason: str = "",
	candidate_composites: List[Dict[str, Any]] | None = None,
) -> CompositeArtifactResolutionContract:
	normalized_status = _clean_text(status).lower() or "blocked_no_governed_family"
	if normalized_status not in ALLOWED_COMPOSITE_RESOLUTION_STATES:
		normalized_status = "blocked_no_governed_family"
	return CompositeArtifactResolutionContract(
		requested_company_name=_clean_text(requested_company_name),
		family_resolution_status=_clean_text(family_resolution_status),
		family_id=_clean_text(family_id),
		family_label=_clean_text(family_label),
		composite_id=_clean_text(composite_id),
		label=_clean_text(label),
		composite_kind=_clean_text(composite_kind),
		entity_grain=_clean_text(entity_grain),
		time_scope_type=_clean_text(time_scope_type),
		assembly_id=_clean_text(assembly_id),
		compatibility_rule_ids=_as_str_list(compatibility_rule_ids or []),
		required_execution_ids=_as_str_list(required_execution_ids or []),
		status=normalized_status,
		activation_state=_clean_text(activation_state),
		blocked_reason=_clean_text(blocked_reason),
		reason=_clean_text(reason),
		candidate_composites=_as_dict_list(candidate_composites or []),
	)


def build_composite_assembly_adapter_contract(
	*,
	assembly_id: str = "",
	family_id: str = "",
	component_metric_ids: List[str] | None = None,
	component_execution_ids: List[str] | None = None,
	join_key_schema: List[str] | None = None,
	row_identity_policy: str = "",
	row_merge_policy: str = "",
	row_missing_component_policy: str = "",
	row_provenance_policy: str = "",
	status: str = "blocked_missing_component",
	blocked_reason: str = "",
) -> CompositeAssemblyAdapterContract:
	normalized_status = _clean_text(status).lower() or "blocked_missing_component"
	if normalized_status not in ALLOWED_COMPOSITE_RESOLUTION_STATES:
		normalized_status = "blocked_missing_component"
	return CompositeAssemblyAdapterContract(
		assembly_id=_clean_text(assembly_id),
		family_id=_clean_text(family_id),
		component_metric_ids=_as_str_list(component_metric_ids or []),
		component_execution_ids=_as_str_list(component_execution_ids or []),
		join_key_schema=_as_str_list(join_key_schema or []),
		row_identity_policy=_clean_text(row_identity_policy),
		row_merge_policy=_clean_text(row_merge_policy),
		row_missing_component_policy=_clean_text(row_missing_component_policy),
		row_provenance_policy=_clean_text(row_provenance_policy),
		status=normalized_status,
		blocked_reason=_clean_text(blocked_reason),
	)


def build_composite_governed_artifact_contract(
	*,
	composite_id: str,
	label: str,
	composite_kind: str,
	primary_metric_id: str,
	secondary_metric_ids: List[str] | None = None,
	entity_grain: str = "",
	time_scope_type: str = "",
	scope: Dict[str, Any] | None = None,
	period_start: str = "",
	period_end: str = "",
	as_of_date: str = "",
	row_count: int = 0,
	source_document_count: int = 0,
	rows: List[Dict[str, Any]] | None = None,
	source_artifact_refs: List[Dict[str, Any]] | None = None,
	compatibility_status: str = "",
	blocked_reason: str = "",
	render_policy: Dict[str, Any] | None = None,
) -> CompositeGovernedArtifactContract:
	return CompositeGovernedArtifactContract(
		artifact_type="qwen_composite_governed_artifact_contract",
		composite_id=_clean_text(composite_id),
		label=_clean_text(label),
		composite_kind=_clean_text(composite_kind),
		primary_metric_id=_clean_text(primary_metric_id),
		secondary_metric_ids=_as_str_list(secondary_metric_ids or []),
		entity_grain=_clean_text(entity_grain),
		time_scope_type=_clean_text(time_scope_type),
		scope=dict(scope or {}),
		period_start=_clean_text(period_start),
		period_end=_clean_text(period_end),
		as_of_date=_clean_text(as_of_date),
		row_count=int(max(0, row_count)),
		source_document_count=int(max(0, source_document_count)),
		rows=_as_dict_list(rows or []),
		source_artifact_refs=_as_dict_list(source_artifact_refs or []),
		compatibility_status=_clean_text(compatibility_status),
		blocked_reason=_clean_text(blocked_reason),
		render_policy=dict(render_policy or {}),
	)


def resolve_composite_family_resolution(
	*,
	requested_company_name: str = "",
	requested_family_id: str = "",
	requested_primary_metric: str = "",
	requested_secondary_metrics: List[str] | None = None,
	requested_basis: str = "",
	requested_period_start: str = "",
	requested_period_end: str = "",
	requested_as_of_date: str = "",
	requested_limit: int = 0,
	requested_sort_direction: str = "",
	registry_payload: Dict[str, Any] | None = None,
) -> CompositeFamilyResolutionContract:
	variation_inputs = {
		"requested_basis": _clean_text(requested_basis),
		"requested_period_start": _clean_text(requested_period_start),
		"requested_period_end": _clean_text(requested_period_end),
		"requested_as_of_date": _clean_text(requested_as_of_date),
		"requested_limit": int(max(0, int(requested_limit or 0))),
		"requested_sort_direction": _clean_text(requested_sort_direction),
	}
	requested_secondary_metric_values = _as_str_list(requested_secondary_metrics or [])
	data = registry_payload if isinstance(registry_payload, dict) else {"families": list_composite_family_specs()}
	families = data.get("families")
	if not isinstance(families, list):
		families = []

	base_candidates = [
		dict(item)
		for item in families
		if isinstance(item, dict)
		and _company_scope_matches(item.get("company_scope"), requested_company_name)
		and (
			not _clean_text(requested_family_id)
			or _clean_text(item.get("family_id")) == _clean_text(requested_family_id)
		)
	]
	if not base_candidates:
		return build_composite_family_resolution_contract(
			requested_company_name=requested_company_name,
			requested_family_id=requested_family_id,
			requested_primary_metric=requested_primary_metric,
			requested_secondary_metrics=requested_secondary_metric_values,
			requested_basis=requested_basis,
			requested_period_start=requested_period_start,
			requested_period_end=requested_period_end,
			requested_as_of_date=requested_as_of_date,
			requested_limit=requested_limit,
			requested_sort_direction=requested_sort_direction,
			variation_inputs=variation_inputs,
			status="blocked_no_governed_family",
			blocked_reason="no_governed_composite_family",
			reason="No governed composite family matched the requested business surface.",
		)

	metric_candidates = [
		item
		for item in base_candidates
		if _primary_metric_matches_family(item, requested_primary_metric)
		and _secondary_metrics_match_family(item, requested_secondary_metric_values)
	]
	if not metric_candidates:
		return build_composite_family_resolution_contract(
			requested_company_name=requested_company_name,
			requested_family_id=requested_family_id,
			requested_primary_metric=requested_primary_metric,
			requested_secondary_metrics=requested_secondary_metric_values,
			requested_basis=requested_basis,
			requested_period_start=requested_period_start,
			requested_period_end=requested_period_end,
			requested_as_of_date=requested_as_of_date,
			requested_limit=requested_limit,
			requested_sort_direction=requested_sort_direction,
			variation_inputs=variation_inputs,
			status="blocked_no_governed_family",
			blocked_reason="no_governed_metric_family",
			reason="No governed composite family matched the requested metric mix.",
			candidate_families=base_candidates,
		)

	variation_candidates = [
		item
		for item in metric_candidates
		if _basis_matches_family(item, requested_basis)
		and _scope_matches_family(item, variation_inputs)
	]
	if not variation_candidates:
		missing_clarifications: List[str] = []
		for item in metric_candidates:
			for clarification in _missing_family_clarifications(
				item,
				variation_inputs,
				requested_primary_metric=requested_primary_metric,
			):
				if clarification not in missing_clarifications:
					missing_clarifications.append(clarification)
		if missing_clarifications:
			return build_composite_family_resolution_contract(
				requested_company_name=requested_company_name,
				requested_family_id=requested_family_id,
				requested_primary_metric=requested_primary_metric,
				requested_secondary_metrics=requested_secondary_metric_values,
				requested_basis=requested_basis,
				requested_period_start=requested_period_start,
				requested_period_end=requested_period_end,
				requested_as_of_date=requested_as_of_date,
				requested_limit=requested_limit,
				requested_sort_direction=requested_sort_direction,
				variation_inputs=variation_inputs,
				missing_clarifications=missing_clarifications,
				status="clarify_family_variation",
				reason="Composite family variation must be clarified before governed composite execution can proceed.",
				candidate_families=metric_candidates,
			)
		missing_clarifications: List[str] = []
		if not _clean_text(requested_basis):
			if any("basis" in _supported_variation_axes(item) for item in metric_candidates):
				missing_clarifications.append("basis")
		if not _requested_time_scope_type(variation_inputs):
			missing_clarifications.append("scope")
		return build_composite_family_resolution_contract(
			requested_company_name=requested_company_name,
			requested_family_id=requested_family_id,
			requested_primary_metric=requested_primary_metric,
			requested_secondary_metrics=requested_secondary_metric_values,
			requested_basis=requested_basis,
			requested_period_start=requested_period_start,
			requested_period_end=requested_period_end,
			requested_as_of_date=requested_as_of_date,
			requested_limit=requested_limit,
			requested_sort_direction=requested_sort_direction,
			variation_inputs=variation_inputs,
			missing_clarifications=missing_clarifications,
			status="clarify_family_variation" if missing_clarifications else "blocked_unsupported_family_variation",
			blocked_reason="" if missing_clarifications else "unsupported_family_variation",
			reason=(
				"Composite family variation must be clarified before governed composite execution can proceed."
				if missing_clarifications
				else "The requested composite variation is not approved inside the matched composite family."
			),
			candidate_families=metric_candidates,
		)

	if len(variation_candidates) > 1:
		return build_composite_family_resolution_contract(
			requested_company_name=requested_company_name,
			requested_family_id=requested_family_id,
			requested_primary_metric=requested_primary_metric,
			requested_secondary_metrics=requested_secondary_metric_values,
			requested_basis=requested_basis,
			requested_period_start=requested_period_start,
			requested_period_end=requested_period_end,
			requested_as_of_date=requested_as_of_date,
			requested_limit=requested_limit,
			requested_sort_direction=requested_sort_direction,
			variation_inputs=variation_inputs,
			missing_clarifications=["family_variation"],
			status="clarify_family_variation",
			reason="Multiple governed composite families remain possible after the current variation inputs.",
			candidate_families=variation_candidates,
		)

	match = variation_candidates[0]
	final_missing_clarifications = _missing_family_clarifications(
		match,
		variation_inputs,
		requested_primary_metric=requested_primary_metric,
	)
	if final_missing_clarifications:
		return build_composite_family_resolution_contract(
			requested_company_name=requested_company_name,
			requested_family_id=requested_family_id,
			requested_primary_metric=requested_primary_metric,
			requested_secondary_metrics=requested_secondary_metric_values,
			requested_basis=requested_basis,
			requested_period_start=requested_period_start,
			requested_period_end=requested_period_end,
			requested_as_of_date=requested_as_of_date,
			requested_limit=requested_limit,
			requested_sort_direction=requested_sort_direction,
			variation_inputs=variation_inputs,
			missing_clarifications=final_missing_clarifications,
			status="clarify_family_variation",
			reason="Composite family variation must be clarified before governed composite execution can proceed.",
			candidate_families=variation_candidates,
		)
	return build_composite_family_resolution_contract(
		requested_company_name=requested_company_name,
		requested_family_id=requested_family_id,
		family_id=_clean_text(match.get("family_id")),
		family_label=_clean_text(match.get("label")),
		requested_primary_metric=requested_primary_metric,
		requested_secondary_metrics=requested_secondary_metric_values,
		requested_basis=requested_basis,
		requested_period_start=requested_period_start,
		requested_period_end=requested_period_end,
		requested_as_of_date=requested_as_of_date,
		requested_limit=requested_limit,
		requested_sort_direction=requested_sort_direction,
		variation_inputs=variation_inputs,
		status="resolved_family",
		blocked_reason=_clean_text(match.get("blocked_reason")),
		reason="A governed composite family matched the requested variation inputs.",
		candidate_families=variation_candidates,
	)


def resolve_composite_artifact_resolution(
	*,
	family_resolution: CompositeFamilyResolutionContract,
	registry_payload: Dict[str, Any] | None = None,
	assembly_payload: Dict[str, Any] | None = None,
) -> CompositeArtifactResolutionContract:
	if family_resolution.status != "resolved_family":
		status = family_resolution.status
		if status == "clarify_family_variation":
			status = "clarify_metric_basis"
		return build_composite_artifact_resolution_contract(
			requested_company_name=family_resolution.requested_company_name,
			family_resolution_status=family_resolution.status,
			family_id=family_resolution.family_id,
			family_label=family_resolution.family_label,
			status=status,
			blocked_reason=family_resolution.blocked_reason,
			reason=family_resolution.reason,
		)

	data = registry_payload if isinstance(registry_payload, dict) else {"artifacts": list_composite_artifact_specs_for_family(family_resolution.family_id)}
	artifacts = data.get("artifacts")
	if not isinstance(artifacts, list):
		artifacts = []
	candidate_artifacts = [
		dict(item)
		for item in artifacts
		if isinstance(item, dict) and _clean_text(item.get("family_id")) == family_resolution.family_id
	]
	matching_artifacts = [
		item
		for item in candidate_artifacts
		if _artifact_variation_matches(
			item,
			family_resolution.variation_inputs,
			requested_secondary_metrics=family_resolution.requested_secondary_metrics,
		)
	]
	if not matching_artifacts:
		return build_composite_artifact_resolution_contract(
			requested_company_name=family_resolution.requested_company_name,
			family_resolution_status=family_resolution.status,
			family_id=family_resolution.family_id,
			family_label=family_resolution.family_label,
			status="unsupported_composite_shape",
			blocked_reason="no_governed_composite_artifact",
			reason="No governed composite artifact matched the resolved family variation.",
			candidate_composites=candidate_artifacts,
		)

	if len(matching_artifacts) > 1:
		return build_composite_artifact_resolution_contract(
			requested_company_name=family_resolution.requested_company_name,
			family_resolution_status=family_resolution.status,
			family_id=family_resolution.family_id,
			family_label=family_resolution.family_label,
			status="clarify_metric_basis",
			reason="Multiple governed composite artifacts remain possible inside the resolved family.",
			candidate_composites=matching_artifacts,
		)

	match = matching_artifacts[0]
	activation_state = _clean_text(match.get("activation_state"))
	normalized_status = "active_composite" if activation_state == "active" else "blocked_missing_component"
	assembly_source = (
		assembly_payload
		if isinstance(assembly_payload, dict)
		else {"assemblies": list_composite_assembly_specs_for_family(family_resolution.family_id)}
	)
	assemblies = assembly_source.get("assemblies")
	if not isinstance(assemblies, list):
		assemblies = []
	known_assembly_ids = {
		_clean_text(item.get("assembly_id"))
		for item in assemblies
		if isinstance(item, dict) and _clean_text(item.get("assembly_id"))
	}
	assembly_id = _clean_text(match.get("assembly_id"))
	if assembly_id and assembly_id not in known_assembly_ids:
		normalized_status = "blocked_missing_component"
		reason = f"Composite artifact '{_clean_text(match.get('composite_id'))}' references missing assembly '{assembly_id}'."
	else:
		reason = (
			"Composite artifact is active and ready for governed assembly."
			if normalized_status == "active_composite"
			else "Composite artifact is declared but not active yet."
		)
	return build_composite_artifact_resolution_contract(
		requested_company_name=family_resolution.requested_company_name,
		family_resolution_status=family_resolution.status,
		family_id=family_resolution.family_id,
		family_label=family_resolution.family_label,
		composite_id=_clean_text(match.get("composite_id")),
		label=_clean_text(match.get("label")),
		composite_kind=_clean_text(match.get("composite_kind")),
		entity_grain=_clean_text(match.get("entity_grain")),
		time_scope_type=_clean_text(match.get("time_scope_type")),
		assembly_id=assembly_id,
		compatibility_rule_ids=_as_str_list(match.get("compatibility_rule_ids")),
		required_execution_ids=_as_str_list(match.get("required_execution_ids")),
		status=normalized_status,
		activation_state=activation_state,
		blocked_reason=_clean_text(match.get("blocked_reason")),
		reason=reason,
		candidate_composites=matching_artifacts,
	)


def build_composite_assembly_contract_from_spec(spec: Dict[str, Any]) -> CompositeAssemblyAdapterContract:
	activation_state = _clean_text(spec.get("activation_state"))
	status = "active_composite" if activation_state == "active" else "blocked_missing_component"
	return build_composite_assembly_adapter_contract(
		assembly_id=_clean_text(spec.get("assembly_id")),
		family_id=_clean_text(spec.get("family_id")),
		component_metric_ids=_as_str_list(spec.get("component_metric_ids")),
		component_execution_ids=_as_str_list(spec.get("component_execution_ids")),
		join_key_schema=_as_str_list(spec.get("join_key_schema")),
		row_identity_policy=_clean_text(spec.get("row_identity_policy")),
		row_merge_policy=_clean_text(spec.get("row_merge_policy")),
		row_missing_component_policy=_clean_text(spec.get("row_missing_component_policy")),
		row_provenance_policy=_clean_text(spec.get("row_provenance_policy")),
		status=status,
		blocked_reason=_clean_text(spec.get("blocked_reason")),
	)


def run_composite_artifact_contract_probe() -> Dict[str, Any]:
	resolved = resolve_composite_family_resolution(
		requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
		requested_primary_metric="revenue",
		requested_secondary_metrics=["quantity", "average_order_value"],
		requested_basis="sales_order",
		requested_period_start="2026-03-01",
		requested_period_end="2026-03-31",
	)
	clarify = resolve_composite_family_resolution(
		requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
		requested_primary_metric="revenue",
		requested_secondary_metrics=["quantity", "average_order_value"],
		requested_period_start="2026-03-01",
		requested_period_end="2026-03-31",
	)
	artifact = resolve_composite_artifact_resolution(family_resolution=resolved)
	assembly_specs = list_composite_assembly_specs_for_family("customer_commercial_ranking")
	assembly = build_composite_assembly_contract_from_spec(assembly_specs[0]) if assembly_specs else build_composite_assembly_adapter_contract()
	ok = (
		resolved.status == "resolved_family"
		and clarify.status == "clarify_family_variation"
		and artifact.status == "active_composite"
		and bool(assembly.assembly_id)
	)
	return {
		"ok": ok,
		"resolved_family": resolved.to_payload(),
		"clarify_family": clarify.to_payload(),
		"artifact_resolution": artifact.to_payload(),
		"assembly_contract": assembly.to_payload(),
	}
