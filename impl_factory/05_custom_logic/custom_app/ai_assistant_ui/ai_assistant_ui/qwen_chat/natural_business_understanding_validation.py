from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .natural_business_understanding_contracts import (
	NBUSystemConfidenceContract,
	NBUValidationResultContract,
)


POLICY_GATED_AUTHORITY_CLASSES = {
	"recommendation",
	"prediction",
	"approval_action",
	"policy_decision",
	"causal_driver_analysis",
	"hidden_score_classification",
	"unsupported_analysis",
}

SAFE_AUTHORITY_CLASSES = {
	"safe_read",
	"safe_explanation",
	"governed_requery",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


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


def _artifact_field_catalog(context: Dict[str, Any]) -> set[str]:
	fields: set[str] = set()
	for context_key in ("current_artifact", "recent_focus", "conversation_state"):
		artifact = _clean_dict(context.get(context_key))
		if not artifact:
			continue
		for field_key in (
			"columns",
			"available_fields",
			"metrics",
			"dimensions",
			"requested_metrics",
			"requested_dimensions",
			"supported_metrics",
			"supported_dimensions",
		):
			fields.update(_normalized_set(artifact.get(field_key)))
		for scalar_key in ("primary_metric", "sort_metric", "primary_entity_type", "entity_grain"):
			if _clean_text(artifact.get(scalar_key)):
				fields.add(_normalize_key(artifact.get(scalar_key)))
		if isinstance(artifact.get("field_catalog"), dict):
			field_catalog = _clean_dict(artifact.get("field_catalog"))
			for values in field_catalog.values():
				fields.update(_normalized_set(values))
	return fields


def _score_subset(values: List[str], known_values: set[str]) -> Tuple[float, List[str]]:
	clean_values = _clean_list(values)
	if not clean_values:
		return 0.0, []
	missing = [value for value in clean_values if value not in known_values]
	return (len(clean_values) - len(missing)) / max(1, len(clean_values)), missing


def _metadata_sets(context: Dict[str, Any]) -> Dict[str, set[str]]:
	metadata = _clean_dict(context.get("metadata_context"))
	report_specs = _metadata_list(context, "reports", "report_specs")
	composite_specs = _metadata_list(context, "composite_families", "composite_family_specs", "families")
	kpi_specs = _metadata_list(context, "governed_kpi_executions", "governed_kpi_execution_specs", "executions")
	return {
		"capability_ids": set(_clean_list(metadata.get("capability_ids"))),
		"report_names": set(_clean_list(metadata.get("report_names"))),
		"composite_family_ids": set(_clean_list(metadata.get("composite_family_ids"))),
		"governed_kpi_ids": set(_clean_list(metadata.get("governed_kpi_ids"))),
		"business_domains": set(_clean_list(metadata.get("business_domains"))),
		"report_names_from_specs": {
			_clean_text(item.get("report_name"))
			for item in report_specs
			if _clean_text(item.get("report_name"))
		},
		"composite_family_ids_from_specs": {
			_clean_text(item.get("family_id"))
			for item in composite_specs
			if _clean_text(item.get("family_id"))
		},
		"governed_kpi_ids_from_specs": {
			_clean_text(item.get("execution_id"))
			for item in kpi_specs
			if _clean_text(item.get("execution_id"))
		},
	}


def _has_artifact_context(context: Dict[str, Any]) -> bool:
	return bool(_clean_dict(context.get("current_artifact")) or _clean_dict(context.get("recent_focus")))


def _artifact_surface_keys(context: Dict[str, Any]) -> set[str]:
	keys: set[str] = set()
	for context_key in ("current_artifact", "recent_focus"):
		artifact = _clean_dict(context.get(context_key))
		if not artifact:
			continue
		for scalar_key in ("family_id", "family", "report_name", "artifact_type", "title"):
			if _clean_text(artifact.get(scalar_key)):
				keys.add(_normalize_key(artifact.get(scalar_key)))
	return keys


def _candidate_surface_keys(candidate_payload: Dict[str, Any]) -> set[str]:
	keys = _normalized_set(candidate_payload.get("candidate_composite_family_ids"))
	keys.update(_normalized_set(candidate_payload.get("candidate_report_names")))
	if _clean_text(candidate_payload.get("business_domain")):
		keys.add(_normalize_key(candidate_payload.get("business_domain")))
	return keys


def _context_surface_conflict(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
	target_reference = _clean_text(candidate_payload.get("target_reference")).lower()
	evidence_need = _clean_text(candidate_payload.get("evidence_need")).lower()
	if target_reference not in {"rank_n", "selected_entity", "current_artifact", "previous_artifact"}:
		return False, ""
	if evidence_need != "current_artifact_ok":
		return False, ""
	artifact_keys = _artifact_surface_keys(context)
	candidate_keys = _candidate_surface_keys(candidate_payload)
	if not artifact_keys or not candidate_keys:
		return False, ""
	if artifact_keys & candidate_keys:
		return False, ""
	return True, (
		"context_artifact_family_conflict:"
		f"candidate={','.join(sorted(candidate_keys))};artifact={','.join(sorted(artifact_keys))}"
	)


def _selected_report_specs(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
	report_names = set(_clean_list(candidate_payload.get("candidate_report_names")))
	capability_ids = set(_clean_list(candidate_payload.get("candidate_capability_ids")))
	specs = _metadata_list(context, "reports", "report_specs")
	if report_names:
		return [
			spec
			for spec in specs
			if _clean_text(spec.get("report_name")) in report_names
		]
	if capability_ids:
		return [
			spec
			for spec in specs
			if capability_ids & set(_clean_list(spec.get("capability_ids")))
		]
	return []


def _selected_composite_specs(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
	family_ids = set(_clean_list(candidate_payload.get("candidate_composite_family_ids")))
	if not family_ids:
		return []
	return [
		spec
		for spec in _metadata_list(context, "composite_families", "composite_family_specs", "families")
		if _clean_text(spec.get("family_id")) in family_ids
	]


def _selected_kpi_specs(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
	requested_metric_keys = _normalized_set(candidate_payload.get("requested_metrics"))
	capability_ids = set(_clean_list(candidate_payload.get("candidate_capability_ids")))
	report_names = set(_clean_list(candidate_payload.get("candidate_report_names")))
	specs = _metadata_list(context, "governed_kpi_executions", "governed_kpi_execution_specs", "executions")
	selected: List[Dict[str, Any]] = []
	for spec in specs:
		value_mapping = _clean_dict(spec.get("value_metric_mapping"))
		metric_values = {
			value_mapping.get("value_metric"),
			spec.get("definition_id"),
			spec.get("execution_id"),
			spec.get("label"),
		}
		metric_match = bool(requested_metric_keys & {_normalize_key(value) for value in metric_values if _clean_text(value)})
		capability_match = bool(capability_ids & set(_clean_list(spec.get("source_capabilities"))))
		report_match = bool(report_names & set(_clean_list(spec.get("source_reports"))))
		if metric_match or capability_match or report_match:
			selected.append(spec)
	return selected


def _active_state_score(specs: List[Dict[str, Any]], label: str) -> Tuple[float, List[str]]:
	if not specs:
		return 0.0, []
	blocked = [
		_clean_text(spec.get("family_id") or spec.get("execution_id") or spec.get("report_name") or label)
		for spec in specs
		if _clean_text(spec.get("activation_state")).lower()
		and _clean_text(spec.get("activation_state")).lower() != "active"
	]
	if blocked:
		return 0.0, [f"inactive_{label}:{value}" for value in blocked]
	return 1.0, []


def _requested_metric_dimension_compatibility(
	*,
	candidate_payload: Dict[str, Any],
	supported_metrics: set[str],
	supported_dimensions: set[str],
	label: str,
) -> Tuple[float, List[str]]:
	requested_metrics = _normalized_set(candidate_payload.get("requested_metrics"))
	requested_dimensions = _normalized_set(candidate_payload.get("requested_dimensions"))
	warnings: List[str] = []
	scores: List[float] = []
	if requested_metrics and supported_metrics:
		missing_metrics = sorted(requested_metrics - supported_metrics)
		scores.append((len(requested_metrics) - len(missing_metrics)) / max(1, len(requested_metrics)))
		warnings.extend([f"{label}_missing_metric:{value}" for value in missing_metrics])
	if requested_dimensions and supported_dimensions:
		missing_dimensions = sorted(requested_dimensions - supported_dimensions)
		scores.append((len(requested_dimensions) - len(missing_dimensions)) / max(1, len(requested_dimensions)))
		warnings.extend([f"{label}_missing_dimension:{value}" for value in missing_dimensions])
	if not scores:
		return 1.0, []
	return sum(scores) / len(scores), warnings


def _report_registry_compatibility(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	specs = _selected_report_specs(candidate_payload, context)
	if not specs:
		return 1.0, []
	supported_metrics: set[str] = set()
	supported_dimensions: set[str] = set()
	for spec in specs:
		supported_metrics.update(_normalized_set(spec.get("supported_metrics")))
		supported_dimensions.update(_normalized_set(spec.get("supported_dimensions")))
	active_score, active_warnings = _active_state_score(specs, "report")
	field_score, field_warnings = _requested_metric_dimension_compatibility(
		candidate_payload=candidate_payload,
		supported_metrics=supported_metrics,
		supported_dimensions=supported_dimensions,
		label="report",
	)
	return min(active_score or 0.0, field_score), active_warnings + field_warnings


def _composite_registry_compatibility(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	specs = _selected_composite_specs(candidate_payload, context)
	if not specs:
		return 1.0, []
	supported_metrics: set[str] = set()
	supported_dimensions: set[str] = set()
	for spec in specs:
		supported_metrics.update(_normalized_set(spec.get("allowed_primary_metrics")))
		supported_metrics.update(_normalized_set(spec.get("allowed_secondary_metrics")))
		supported_dimensions.add(_normalize_key(spec.get("entity_grain")))
		supported_dimensions.add(_normalize_key(spec.get("subject_alias_value")))
		metric_map = _clean_dict(spec.get("metric_semantic_key_map"))
		supported_metrics.update(_normalized_set(list(metric_map.keys())))
		for values in metric_map.values():
			supported_metrics.update(_normalized_set(values))
	active_score, active_warnings = _active_state_score(specs, "composite_family")
	field_score, field_warnings = _requested_metric_dimension_compatibility(
		candidate_payload=candidate_payload,
		supported_metrics=supported_metrics,
		supported_dimensions=supported_dimensions,
		label="composite_family",
	)
	return min(active_score or 0.0, field_score), active_warnings + field_warnings


def _kpi_registry_compatibility(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	specs = _selected_kpi_specs(candidate_payload, context)
	if not specs:
		return 1.0, []
	supported_metrics: set[str] = set()
	supported_dimensions: set[str] = set()
	for spec in specs:
		value_mapping = _clean_dict(spec.get("value_metric_mapping"))
		supported_metrics.update(
			_normalized_set(
				[
					value_mapping.get("value_metric"),
					value_mapping.get("numerator_metric"),
					value_mapping.get("denominator_metric"),
					spec.get("definition_id"),
					spec.get("execution_id"),
				]
			)
		)
		supported_dimensions.update(_normalized_set(spec.get("required_dimensions")))
	active_score, active_warnings = _active_state_score(specs, "governed_kpi_execution")
	field_score, field_warnings = _requested_metric_dimension_compatibility(
		candidate_payload=candidate_payload,
		supported_metrics=supported_metrics,
		supported_dimensions=supported_dimensions,
		label="governed_kpi",
	)
	return min(active_score or 0.0, field_score), active_warnings + field_warnings


def _governed_surface_compatibility(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	scores: List[float] = []
	warnings: List[str] = []
	for evaluator in (
		_report_registry_compatibility,
		_composite_registry_compatibility,
		_kpi_registry_compatibility,
	):
		score, evaluator_warnings = evaluator(candidate_payload, context)
		scores.append(score)
		warnings.extend(evaluator_warnings)
	if not scores:
		return 1.0, warnings
	return min(scores), warnings


def _registry_match_strength(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	known = _metadata_sets(context)
	scores: List[float] = []
	warnings: List[str] = []
	for field_name, known_key in (
		("candidate_capability_ids", "capability_ids"),
		("candidate_report_names", "report_names"),
		("candidate_composite_family_ids", "composite_family_ids"),
	):
		score, missing = _score_subset(_clean_list(candidate_payload.get(field_name)), known.get(known_key, set()))
		if _clean_list(candidate_payload.get(field_name)):
			scores.append(score)
		warnings.extend([f"unknown_{field_name}:{value}" for value in missing])
	if _clean_list(candidate_payload.get("candidate_report_names")) and known["report_names_from_specs"]:
		score, missing = _score_subset(_clean_list(candidate_payload.get("candidate_report_names")), known["report_names_from_specs"])
		scores.append(score)
		warnings.extend([f"unknown_report_spec:{value}" for value in missing])
	if _clean_list(candidate_payload.get("candidate_composite_family_ids")) and known["composite_family_ids_from_specs"]:
		score, missing = _score_subset(
			_clean_list(candidate_payload.get("candidate_composite_family_ids")),
			known["composite_family_ids_from_specs"],
		)
		scores.append(score)
		warnings.extend([f"unknown_composite_family_spec:{value}" for value in missing])

	business_domain = _clean_text(candidate_payload.get("business_domain"))
	if business_domain and known["business_domains"]:
		scores.append(1.0 if business_domain in known["business_domains"] else 0.35)
		if business_domain not in known["business_domains"]:
			warnings.append(f"future_or_unknown_business_domain:{business_domain}")
	elif business_domain:
		scores.append(0.5)

	if not scores:
		return 0.0, ["no_registry_anchor"]
	surface_score, surface_warnings = _governed_surface_compatibility(candidate_payload, context)
	warnings.extend(surface_warnings)
	return min(sum(scores) / len(scores), surface_score), warnings


def _context_reference_clarity(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	target_reference = _clean_text(candidate_payload.get("target_reference")).lower()
	target_entity = _clean_dict(candidate_payload.get("target_entity"))
	if target_reference in {"none", ""}:
		return 1.0, []
	if target_reference == "named_entity":
		return (1.0, []) if target_entity else (0.45, ["named_entity_missing_target_payload"])
	if target_reference in {"rank_n", "selected_entity", "current_artifact", "previous_artifact"}:
		if not _has_artifact_context(context):
			return 0.2, [f"{target_reference}_without_artifact_context"]
		has_conflict, conflict_reason = _context_surface_conflict(candidate_payload, context)
		if has_conflict:
			return 0.05, [conflict_reason]
		return 0.9, []
	if target_reference == "candidate_list":
		return 0.75, []
	if target_reference == "unclear":
		return 0.1, ["unclear_target_reference"]
	return 0.3, [f"unknown_target_reference:{target_reference}"]


def _artifact_compatibility(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	evidence_need = _clean_text(candidate_payload.get("evidence_need")).lower()
	has_artifact = _has_artifact_context(context)
	has_registry_anchor = bool(
		_clean_list(candidate_payload.get("candidate_capability_ids"))
		or _clean_list(candidate_payload.get("candidate_report_names"))
		or _clean_list(candidate_payload.get("candidate_composite_family_ids"))
	)
	if evidence_need == "current_artifact_ok":
		if not has_artifact:
			return 0.25, ["current_artifact_requested_but_missing"]
		field_catalog = _artifact_field_catalog(context)
		requested_fields = _normalized_set(candidate_payload.get("requested_metrics")) | _normalized_set(
			candidate_payload.get("requested_dimensions")
		)
		if requested_fields and field_catalog:
			missing = sorted(requested_fields - field_catalog)
			if missing:
				score = (len(requested_fields) - len(missing)) / max(1, len(requested_fields))
				return score, [f"current_artifact_missing_requested_field:{value}" for value in missing]
		return 1.0, []
	if evidence_need == "needs_governed_requery":
		if not has_registry_anchor:
			return 0.35, ["governed_requery_without_registry_anchor"]
		surface_score, surface_warnings = _governed_surface_compatibility(candidate_payload, context)
		return min(0.8, max(0.0, surface_score)), surface_warnings
	if evidence_need == "needs_clarification":
		return 0.4, ["clarification_needed"]
	if evidence_need in {"unsupported_policy", "out_of_scope"}:
		return 0.0, [f"artifact_not_compatible:{evidence_need}"]
	return 0.2, ["unknown_evidence_need"]


def _evidence_availability(candidate_payload: Dict[str, Any], context: Dict[str, Any]) -> Tuple[float, List[str]]:
	evidence_need = _clean_text(candidate_payload.get("evidence_need")).lower()
	has_artifact = _has_artifact_context(context)
	has_registry_anchor = bool(
		_clean_list(candidate_payload.get("candidate_capability_ids"))
		or _clean_list(candidate_payload.get("candidate_report_names"))
		or _clean_list(candidate_payload.get("candidate_composite_family_ids"))
	)
	if evidence_need == "current_artifact_ok" and has_artifact:
		return 1.0, []
	if evidence_need == "needs_governed_requery" and has_registry_anchor:
		return 0.75, []
	if evidence_need == "needs_clarification":
		return 0.35, ["evidence_waiting_for_clarification"]
	if evidence_need == "unsupported_policy":
		return 0.2, ["policy_artifact_required_before_evidence_can_execute"]
	return 0.0, ["evidence_not_available"]


def _authority_policy_state(candidate_payload: Dict[str, Any]) -> Tuple[float, str, List[str]]:
	authority_class = _clean_text(candidate_payload.get("authority_class")).lower()
	if authority_class in SAFE_AUTHORITY_CLASSES:
		return 1.0, "safe_read_authority", []
	if authority_class in POLICY_GATED_AUTHORITY_CLASSES:
		return 0.0, "blocked_policy_required", [f"policy_gated_authority:{authority_class}"]
	if authority_class == "unknown":
		return 0.2, "unknown_authority", ["unknown_authority_class"]
	return 0.0, "unsupported_authority", [f"unsupported_authority_class:{authority_class}"]


def evaluate_nbu_candidate_against_context(
	*,
	candidate_payload: Dict[str, Any],
	interpretation_context: Dict[str, Any],
) -> Tuple[NBUValidationResultContract, NBUSystemConfidenceContract]:
	candidate = _clean_dict(candidate_payload)
	context = _clean_dict(interpretation_context)

	registry_score, registry_warnings = _registry_match_strength(candidate, context)
	context_score, context_warnings = _context_reference_clarity(candidate, context)
	artifact_score, artifact_warnings = _artifact_compatibility(candidate, context)
	evidence_score, evidence_warnings = _evidence_availability(candidate, context)
	authority_score, authority_state, authority_warnings = _authority_policy_state(candidate)
	warnings = registry_warnings + context_warnings + artifact_warnings + evidence_warnings + authority_warnings

	model_confidence = 0.0
	try:
		model_confidence = max(0.0, min(1.0, float(candidate.get("model_confidence") or 0.0)))
	except Exception:
		model_confidence = 0.0
	final_confidence = min(
		model_confidence,
		max(0.0, registry_score),
		max(0.0, context_score),
		max(0.0, artifact_score),
		max(0.0, evidence_score),
		max(0.0, authority_score),
	)
	if authority_state.startswith("blocked"):
		status = "blocked_by_authority_policy"
	elif final_confidence >= 0.65:
		status = "accepted"
	elif final_confidence >= 0.35:
		status = "needs_validation"
	else:
		status = "insufficient_confidence"

	validation_result = NBUValidationResultContract(
		status=status,
		registry_match_strength=registry_score,
		context_reference_clarity=context_score,
		artifact_compatibility=artifact_score,
		evidence_availability=evidence_score,
		authority_policy_state=authority_state,
		validation_warnings=warnings,
	)
	system_confidence = NBUSystemConfidenceContract(
		model_confidence=model_confidence,
		registry_confidence=registry_score,
		context_confidence=context_score,
		evidence_confidence=evidence_score,
		authority_confidence=authority_score,
		context_conflict_score=1.0 - context_score,
		final_confidence=final_confidence,
		confidence_basis=["model", "registry", "context", "artifact", "evidence", "authority"],
	)
	return validation_result, system_confidence
