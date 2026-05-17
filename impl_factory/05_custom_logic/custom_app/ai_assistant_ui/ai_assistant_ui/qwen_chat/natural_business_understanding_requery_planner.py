from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .natural_business_understanding_contracts import NBUGovernedRequeryPlanContract


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _normalize_key(value: Any) -> str:
	text = _clean_text(value).lower()
	return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _normalized_set(values: Any) -> set[str]:
	return {_normalize_key(value) for value in _clean_list(values)}


def _metadata_list(context: Dict[str, Any], *keys: str) -> List[Dict[str, Any]]:
	metadata = _clean_dict(context.get("metadata_context"))
	for key in keys:
		value = metadata.get(key)
		if isinstance(value, list):
			return [dict(item) for item in value if isinstance(item, dict)]
	return []


def _active_metadata_list(context: Dict[str, Any], *keys: str) -> List[Dict[str, Any]]:
	return [spec for spec in _metadata_list(context, *keys) if _active_spec(spec)]


def _any_active_metadata_specs(context: Dict[str, Any]) -> bool:
	return bool(
		_active_metadata_list(context, "reports", "report_specs")
		or _active_metadata_list(context, "composite_families", "composite_family_specs", "families")
		or _active_metadata_list(context, "governed_kpi_executions", "governed_kpi_execution_specs", "executions")
	)


def _ordered_unique(values: List[str]) -> List[str]:
	out: List[str] = []
	for value in values:
		clean = _clean_text(value)
		if clean and clean not in out:
			out.append(clean)
	return out


def _missing_fields(evidence_plan_payload: Dict[str, Any], validation_payload: Dict[str, Any]) -> List[str]:
	missing = _clean_list(_clean_dict(evidence_plan_payload).get("missing_fields"))
	for warning in _clean_list(_clean_dict(validation_payload).get("validation_warnings")):
		if ":" not in warning:
			continue
		key, value = warning.split(":", 1)
		if key in {
			"current_artifact_missing_requested_field",
			"report_missing_metric",
			"report_missing_dimension",
			"composite_family_missing_metric",
			"composite_family_missing_dimension",
			"governed_kpi_missing_metric",
			"governed_kpi_missing_dimension",
		}:
			missing.append(value)
	return _ordered_unique(missing)


def _target_entity(candidate_payload: Dict[str, Any], context_resolution_payload: Dict[str, Any]) -> Dict[str, Any]:
	resolved = _clean_dict(context_resolution_payload.get("resolved_entity"))
	if resolved:
		return resolved
	return _clean_dict(candidate_payload.get("target_entity"))


def _context_status(context_resolution_payload: Dict[str, Any]) -> str:
	return _clean_text(_clean_dict(context_resolution_payload).get("status")).lower()


def _context_blocks_requery(candidate_payload: Dict[str, Any], context_resolution_payload: Dict[str, Any]) -> bool:
	target_reference = _clean_text(candidate_payload.get("target_reference")).lower()
	if target_reference in {"none", "", "current_artifact"}:
		return False
	status = _context_status(context_resolution_payload)
	return status in {"ambiguous", "out_of_range", "not_supported"}


def _active_spec(spec: Dict[str, Any]) -> bool:
	state = _clean_text(spec.get("activation_state")).lower()
	return not state or state == "active"


def _requested_field_sets(candidate_payload: Dict[str, Any]) -> Tuple[set[str], set[str]]:
	return _normalized_set(candidate_payload.get("requested_metrics")), _normalized_set(candidate_payload.get("requested_dimensions"))


def _field_support_status(
	*,
	requested_metrics: set[str],
	requested_dimensions: set[str],
	supported_metrics: set[str],
	supported_dimensions: set[str],
) -> str:
	if requested_metrics and supported_metrics and not requested_metrics.issubset(supported_metrics):
		return "unsupported"
	if requested_dimensions and supported_dimensions and not requested_dimensions.issubset(supported_dimensions):
		return "unsupported"
	if (requested_metrics and supported_metrics) or (requested_dimensions and supported_dimensions):
		return "supported"
	if requested_metrics or requested_dimensions:
		return "unproven"
	return "not_requested"


def _field_status_is_ready(status: str) -> bool:
	return status in {"supported", "not_requested"}


def _report_field_support_status(spec: Dict[str, Any], candidate_payload: Dict[str, Any]) -> str:
	requested_metrics, requested_dimensions = _requested_field_sets(candidate_payload)
	return _field_support_status(
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		supported_metrics=_normalized_set(spec.get("supported_metrics")),
		supported_dimensions=_normalized_set(spec.get("supported_dimensions")),
	)


def _composite_field_support_status(spec: Dict[str, Any], candidate_payload: Dict[str, Any]) -> str:
	requested_metrics, requested_dimensions = _requested_field_sets(candidate_payload)
	metric_map = _clean_dict(spec.get("metric_semantic_key_map"))
	supported_metrics = _normalized_set(spec.get("allowed_primary_metrics"))
	supported_metrics.update(_normalized_set(spec.get("allowed_secondary_metrics")))
	supported_metrics.update(_normalized_set(list(metric_map.keys())))
	for values in metric_map.values():
		supported_metrics.update(_normalized_set(values))
	supported_dimensions = {
		_normalize_key(spec.get("entity_grain")),
		_normalize_key(spec.get("subject_alias_value")),
	}
	supported_dimensions = {value for value in supported_dimensions if value}
	return _field_support_status(
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		supported_metrics=supported_metrics,
		supported_dimensions=supported_dimensions,
	)


def _kpi_field_support_status(spec: Dict[str, Any], candidate_payload: Dict[str, Any]) -> str:
	requested_metrics, requested_dimensions = _requested_field_sets(candidate_payload)
	mapping = _clean_dict(spec.get("value_metric_mapping"))
	supported_metrics = {
		_normalize_key(mapping.get("value_metric")),
		_normalize_key(mapping.get("numerator_metric")),
		_normalize_key(mapping.get("denominator_metric")),
		_normalize_key(spec.get("definition_id")),
		_normalize_key(spec.get("execution_id")),
		_normalize_key(spec.get("label")),
	}
	supported_metrics = {value for value in supported_metrics if value}
	return _field_support_status(
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		supported_metrics=supported_metrics,
		supported_dimensions=_normalized_set(spec.get("required_dimensions")),
	)


def _report_spec_score(spec: Dict[str, Any], candidate_payload: Dict[str, Any]) -> int:
	score = 0
	report_names = set(_clean_list(candidate_payload.get("candidate_report_names")))
	capability_ids = set(_clean_list(candidate_payload.get("candidate_capability_ids")))
	requested_metrics = _normalized_set(candidate_payload.get("requested_metrics"))
	requested_dimensions = _normalized_set(candidate_payload.get("requested_dimensions"))
	if _clean_text(spec.get("report_name")) in report_names:
		score += 120
	spec_capabilities = set(_clean_list(spec.get("capability_ids")))
	score += len(spec_capabilities & capability_ids) * 90
	supported_metrics = _normalized_set(spec.get("supported_metrics"))
	supported_dimensions = _normalized_set(spec.get("supported_dimensions"))
	score += len(requested_metrics & supported_metrics) * 25
	score += len(requested_dimensions & supported_dimensions) * 15
	semantic_tags = _normalized_set(spec.get("semantic_tags"))
	if _normalize_key(candidate_payload.get("business_domain")) in semantic_tags:
		score += 20
	field_status = _report_field_support_status(spec, candidate_payload)
	if field_status == "supported":
		score += 60
	elif field_status == "unsupported":
		score -= 200
	elif field_status == "unproven":
		score -= 120
	return score


def _selected_report_targets(
	candidate_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
	specs = _active_metadata_list(interpretation_context, "reports", "report_specs")
	scored = [
		(_report_spec_score(spec, candidate_payload), spec)
		for spec in specs
	]
	scored = [(score, spec) for score, spec in scored if score > 0]
	scored.sort(key=lambda item: item[0], reverse=True)
	report_names: List[str] = []
	capability_ids: List[str] = []
	for _score, spec in scored[:3]:
		if not _field_status_is_ready(_report_field_support_status(spec, candidate_payload)):
			continue
		report_names.append(_clean_text(spec.get("report_name")))
		capability_ids.extend(_clean_list(spec.get("capability_ids")))
	return _ordered_unique(capability_ids), _ordered_unique(report_names)


def _selected_composite_targets(
	candidate_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> List[str]:
	candidate_family_ids = set(_clean_list(candidate_payload.get("candidate_composite_family_ids")))
	if not candidate_family_ids:
		return []
	return _ordered_unique(
		[
			_clean_text(spec.get("family_id"))
			for spec in _metadata_list(interpretation_context, "composite_families", "composite_family_specs", "families")
			if (
				_active_spec(spec)
				and _clean_text(spec.get("family_id")) in candidate_family_ids
				and _field_status_is_ready(_composite_field_support_status(spec, candidate_payload))
			)
		]
	)


def _selected_kpi_targets(
	candidate_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> List[str]:
	candidate_capabilities = set(_clean_list(candidate_payload.get("candidate_capability_ids")))
	candidate_reports = set(_clean_list(candidate_payload.get("candidate_report_names")))
	requested_metrics = _normalized_set(candidate_payload.get("requested_metrics"))
	targets: List[str] = []
	for spec in _active_metadata_list(interpretation_context, "governed_kpi_executions", "governed_kpi_execution_specs", "executions"):
		field_status = _kpi_field_support_status(spec, candidate_payload)
		if not _field_status_is_ready(field_status):
			continue
		mapping = _clean_dict(spec.get("value_metric_mapping"))
		metric_values = {
			_normalize_key(mapping.get("value_metric")),
			_normalize_key(spec.get("definition_id")),
			_normalize_key(spec.get("execution_id")),
			_normalize_key(spec.get("label")),
		}
		if (
			requested_metrics & metric_values
			or candidate_capabilities & set(_clean_list(spec.get("source_capabilities")))
			or candidate_reports & set(_clean_list(spec.get("source_reports")))
		):
			targets.append(_clean_text(spec.get("execution_id")))
	return _ordered_unique(targets)


def _planner_mode(
	*,
	candidate_payload: Dict[str, Any],
	target_entity: Dict[str, Any],
	capability_targets: List[str],
	report_targets: List[str],
	composite_targets: List[str],
	kpi_targets: List[str],
) -> str:
	route = _clean_text(candidate_payload.get("candidate_route")).lower()
	any_target = bool(capability_targets or report_targets or composite_targets or kpi_targets)
	if (route == "entity_detail" or target_entity) and any_target:
		return "entity_detail_requery"
	if kpi_targets:
		return "governed_kpi_requery"
	if composite_targets:
		return "composite_requery"
	if report_targets:
		return "capability_requery"
	return "unsupported"


def _compact_values(values: Any, limit: int = 8) -> List[str]:
	return _ordered_unique(_clean_list(values))[:limit]


def _report_alternative_payload(spec: Dict[str, Any], *, reason: str) -> Dict[str, Any]:
	return {
		"target_type": "report",
		"report_name": _clean_text(spec.get("report_name")),
		"capability_ids": _compact_values(spec.get("capability_ids"), limit=5),
		"supported_metrics": _compact_values(spec.get("supported_metrics"), limit=8),
		"supported_dimensions": _compact_values(spec.get("supported_dimensions"), limit=8),
		"reason": reason,
	}


def _composite_alternative_payload(spec: Dict[str, Any], *, reason: str) -> Dict[str, Any]:
	return {
		"target_type": "composite_family",
		"family_id": _clean_text(spec.get("family_id")),
		"label": _clean_text(spec.get("label")),
		"supported_metrics": _compact_values(
			_clean_list(spec.get("allowed_primary_metrics")) + _clean_list(spec.get("allowed_secondary_metrics")),
			limit=8,
		),
		"supported_dimensions": _compact_values([spec.get("entity_grain"), spec.get("subject_alias_value")], limit=8),
		"reason": reason,
	}


def _kpi_alternative_payload(spec: Dict[str, Any], *, reason: str) -> Dict[str, Any]:
	mapping = _clean_dict(spec.get("value_metric_mapping"))
	return {
		"target_type": "governed_kpi",
		"execution_id": _clean_text(spec.get("execution_id")),
		"label": _clean_text(spec.get("label")),
		"source_capabilities": _compact_values(spec.get("source_capabilities"), limit=5),
		"source_reports": _compact_values(spec.get("source_reports"), limit=5),
		"supported_metrics": _compact_values(
			[
				mapping.get("value_metric"),
				mapping.get("numerator_metric"),
				mapping.get("denominator_metric"),
				spec.get("definition_id"),
			],
			limit=8,
		),
		"required_dimensions": _compact_values(spec.get("required_dimensions"), limit=8),
		"reason": reason,
	}


def _suggested_alternatives(candidate_payload: Dict[str, Any], interpretation_context: Dict[str, Any]) -> List[Dict[str, Any]]:
	requested_metrics, requested_dimensions = _requested_field_sets(candidate_payload)
	candidate_capabilities = set(_clean_list(candidate_payload.get("candidate_capability_ids")))
	business_domain = _normalize_key(candidate_payload.get("business_domain"))
	scored: List[Tuple[int, Dict[str, Any]]] = []
	for spec in _metadata_list(interpretation_context, "reports", "report_specs"):
		if not _active_spec(spec):
			continue
		supported_metrics = _normalized_set(spec.get("supported_metrics"))
		supported_dimensions = _normalized_set(spec.get("supported_dimensions"))
		capability_overlap = len(set(_clean_list(spec.get("capability_ids"))) & candidate_capabilities)
		metric_overlap = len(requested_metrics & supported_metrics)
		dimension_overlap = len(requested_dimensions & supported_dimensions)
		semantic_match = int(bool(business_domain and business_domain in _normalized_set(spec.get("semantic_tags"))))
		score = capability_overlap * 50 + metric_overlap * 35 + dimension_overlap * 20 + semantic_match * 20
		field_status = _report_field_support_status(spec, candidate_payload)
		if field_status == "supported":
			score += 80
		elif field_status == "unsupported":
			score += 10 if (metric_overlap or dimension_overlap or capability_overlap or semantic_match) else 0
		if score > 0:
			reason = "Supports the requested metric/dimension." if field_status == "supported" else "Closest active governed report by capability, metric, or semantic overlap."
			scored.append((score, _report_alternative_payload(spec, reason=reason)))
	for spec in _metadata_list(interpretation_context, "composite_families", "composite_family_specs", "families"):
		if not _active_spec(spec):
			continue
		field_status = _composite_field_support_status(spec, candidate_payload)
		metric_values = _normalized_set(spec.get("allowed_primary_metrics")) | _normalized_set(spec.get("allowed_secondary_metrics"))
		dimension_values = {_normalize_key(spec.get("entity_grain")), _normalize_key(spec.get("subject_alias_value"))}
		score = len(requested_metrics & metric_values) * 35 + len(requested_dimensions & dimension_values) * 20
		if _clean_text(spec.get("family_id")) in _clean_list(candidate_payload.get("candidate_composite_family_ids")):
			score += 70
		if field_status == "supported":
			score += 80
		elif field_status == "unsupported" and score <= 0:
			continue
		if score > 0:
			reason = "Supports the requested composite metric/dimension." if field_status == "supported" else "Closest active governed composite family."
			scored.append((score, _composite_alternative_payload(spec, reason=reason)))
	for spec in _metadata_list(interpretation_context, "governed_kpi_executions", "governed_kpi_execution_specs", "executions"):
		if not _active_spec(spec):
			continue
		mapping = _clean_dict(spec.get("value_metric_mapping"))
		metric_values = {
			_normalize_key(mapping.get("value_metric")),
			_normalize_key(mapping.get("numerator_metric")),
			_normalize_key(mapping.get("denominator_metric")),
			_normalize_key(spec.get("definition_id")),
			_normalize_key(spec.get("execution_id")),
			_normalize_key(spec.get("label")),
		}
		score = len(requested_metrics & metric_values) * 45
		score += len(set(_clean_list(spec.get("source_capabilities"))) & candidate_capabilities) * 35
		if score > 0:
			scored.append((score, _kpi_alternative_payload(spec, reason="Closest active governed KPI execution.")))
	scored.sort(key=lambda item: item[0], reverse=True)
	alternatives: List[Dict[str, Any]] = []
	seen: set[Tuple[str, str]] = set()
	for _score, payload in scored:
		key = (
			_clean_text(payload.get("target_type")),
			_clean_text(payload.get("report_name") or payload.get("family_id") or payload.get("execution_id") or payload.get("label")),
		)
		if key in seen or not key[1]:
			continue
		seen.add(key)
		alternatives.append(payload)
		if len(alternatives) >= 5:
			break
	return alternatives


def _candidate_fallback_targets(
	candidate_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> Tuple[List[str], List[str], List[str], List[str], List[str]]:
	if _any_active_metadata_specs(interpretation_context):
		return [], [], [], [], []
	capability_targets = _clean_list(candidate_payload.get("candidate_capability_ids"))
	report_targets = _clean_list(candidate_payload.get("candidate_report_names"))
	composite_targets = _clean_list(candidate_payload.get("candidate_composite_family_ids"))
	kpi_targets: List[str] = []
	warnings: List[str] = []
	if capability_targets or report_targets or composite_targets:
		warnings.append("metadata_context_absent_candidate_targets_unverified")
	return capability_targets, report_targets, composite_targets, kpi_targets, warnings


def build_nbu_governed_requery_plan(
	*,
	candidate_payload: Dict[str, Any],
	validation_payload: Dict[str, Any],
	evidence_plan_payload: Dict[str, Any],
	context_resolution_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> NBUGovernedRequeryPlanContract:
	"""Build a shadow-only governed requery plan from NBU contracts.

	The planner does not execute. It proves whether the selected interpretation
	has a governed target that a later activation slice may pass to existing
	requery/execution lanes.
	"""

	candidate = _clean_dict(candidate_payload)
	evidence_plan = _clean_dict(evidence_plan_payload)
	validation = _clean_dict(validation_payload)
	context_resolution = _clean_dict(context_resolution_payload)
	evidence_need = _clean_text(candidate.get("evidence_need")).lower()
	action_route = _clean_text(candidate.get("candidate_route"))
	validation_status = _clean_text(validation.get("status")).lower()
	requested_metrics = _clean_list(candidate.get("requested_metrics"))
	requested_dimensions = _clean_list(candidate.get("requested_dimensions"))
	missing = _missing_fields(evidence_plan, validation)

	if evidence_need not in {"needs_governed_requery", "unknown"} and not missing:
		return NBUGovernedRequeryPlanContract(
			status="not_required",
			planner_mode="none",
			requested_metrics=requested_metrics,
			requested_dimensions=requested_dimensions,
			reason="The selected NBU candidate does not require a governed requery.",
		)

	if validation_status == "blocked_by_authority_policy":
		return NBUGovernedRequeryPlanContract(
			status="blocked_by_authority_policy",
			planner_mode="authority_boundary",
			target_route=action_route,
			requested_metrics=requested_metrics,
			requested_dimensions=requested_dimensions,
			missing_fields=missing,
			required_context=["approved_policy_or_authority_gate"],
			reason="Governed requery planning is blocked because the selected NBU candidate requires policy authority.",
		)

	if _context_blocks_requery(candidate, context_resolution):
		return NBUGovernedRequeryPlanContract(
			status="needs_clarification",
			planner_mode="context_resolution_required",
			target_route=action_route,
			requested_metrics=requested_metrics,
			requested_dimensions=requested_dimensions,
			missing_fields=missing,
			required_context=["unambiguous_context_reference"],
			reason="The request may need a governed requery, but the referenced row/entity/list item is not resolved safely.",
			warnings=_clean_list(context_resolution.get("ambiguity_options")),
		)

	target_entity = _target_entity(candidate, context_resolution)
	capability_targets, report_targets = _selected_report_targets(candidate, interpretation_context)
	composite_targets = _selected_composite_targets(candidate, interpretation_context)
	kpi_targets = _selected_kpi_targets(candidate, interpretation_context)
	alternatives = _suggested_alternatives(candidate, interpretation_context)
	fallback_warnings: List[str] = []
	if not (capability_targets or report_targets or composite_targets or kpi_targets):
		(
			capability_targets,
			report_targets,
			composite_targets,
			kpi_targets,
			fallback_warnings,
		) = _candidate_fallback_targets(candidate, interpretation_context)

	mode = _planner_mode(
		candidate_payload=candidate,
		target_entity=target_entity,
		capability_targets=capability_targets,
		report_targets=report_targets,
		composite_targets=composite_targets,
		kpi_targets=kpi_targets,
	)
	if mode == "unsupported":
		return NBUGovernedRequeryPlanContract(
			status="unsupported",
			planner_mode=mode,
			target_route=action_route,
			requested_metrics=requested_metrics,
			requested_dimensions=requested_dimensions,
			missing_fields=missing,
			required_context=["governed_report_or_capability_or_composite_or_kpi_target"],
			suggested_alternatives=alternatives,
			reason="No compatible governed requery target was proven from the selected NBU candidate and metadata context.",
			warnings=fallback_warnings,
		)

	required_context: List[str] = []
	if mode == "entity_detail_requery" and not target_entity:
		required_context.append("resolved_target_entity")
	status = "ready_shadow" if not required_context else "needs_clarification"
	return NBUGovernedRequeryPlanContract(
		status=status,
		planner_mode=mode,
		target_route=action_route,
		target_capability_ids=capability_targets,
		target_report_names=report_targets,
		target_composite_family_ids=composite_targets,
		target_governed_kpi_ids=kpi_targets,
		target_entity=target_entity,
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		missing_fields=missing,
		required_context=required_context,
		suggested_alternatives=[] if status == "ready_shadow" else alternatives,
		shadow_execution_ready=status == "ready_shadow",
		reason="A governed requery target was proven in NBU shadow mode; live execution remains disabled until activation.",
		warnings=fallback_warnings,
	)
