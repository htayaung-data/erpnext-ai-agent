from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .natural_business_understanding_activation import EXECUTION_REQUIRED_ACTIONS, PRESENTATION_ONLY_ACTIONS
from .natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)
from .natural_business_understanding_quality_standard import (
	validate_nbu_user_facing_response_text,
)
from .natural_business_understanding_schema_hardening import (
	validate_nbu_trace_schema_hardening,
)
from .natural_business_understanding_validation import POLICY_GATED_AUTHORITY_CLASSES


NBU_EVALUATION_HARNESS_VERSION = "1.0"
DEFAULT_LATENCY_BUDGET_MS = 2500
GENERIC_EXPECTED_TARGET_PLACEHOLDERS = {
	"current_ranked_or_list_artifact",
	"current_customer_risk_or_ar_table",
}


NBU_EVALUATION_FAILURE_TAXONOMY: List[Dict[str, Any]] = [
	{
		"bucket_id": "model_misunderstanding",
		"label": "Model Misunderstanding",
		"meaning": "The semantic interpretation selected the wrong action, business domain, entity family, metric, or authority class.",
	},
	{
		"bucket_id": "missing_registry_metadata",
		"label": "Missing Registry Metadata",
		"meaning": "The request may be understandable, but the registry does not expose enough active metadata for a safe route.",
	},
	{
		"bucket_id": "context_graph_failure",
		"label": "Context Graph Failure",
		"meaning": "The request depends on current, previous, row, rank, or selected-entity context that was not resolved correctly.",
	},
	{
		"bucket_id": "validation_gate_failure",
		"label": "Validation Or Gate Failure",
		"meaning": "The candidate did not satisfy schema, confidence, authority, evidence, or hardening gates.",
	},
	{
		"bucket_id": "route_execution_failure",
		"label": "Route Execution Failure",
		"meaning": "The interpretation points to a governed route, but no ready execution or requery path is proven.",
	},
	{
		"bucket_id": "renderer_quality_failure",
		"label": "Renderer Quality Failure",
		"meaning": "The user-facing response leaks internal language, repeats the wrong shape, or is not safe to show.",
	},
	{
		"bucket_id": "policy_evidence_gap",
		"label": "Policy Or Evidence Gap",
		"meaning": "The request needs evidence, policy, prediction, recommendation, approval, or causal authority that is not approved yet.",
	},
	{
		"bucket_id": "latency_runtime_unavailable",
		"label": "Latency Or Runtime Unavailable",
		"meaning": "The NBU runtime is unavailable, returns no candidates, or exceeds the configured latency budget.",
	},
]


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_float(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _normalize(value: Any) -> str:
	text = _clean_text(value).lower()
	return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([value for value in values if value]))


def _selected_candidate(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	selected_id = _clean_text(trace.get("selected_candidate_id"))
	candidates = trace.get("candidate_interpretations")
	if not isinstance(candidates, list):
		return {}
	for candidate in candidates:
		candidate_payload = _clean_dict(candidate)
		if selected_id and _clean_text(candidate_payload.get("candidate_id")) == selected_id:
			return candidate_payload
	if candidates:
		return _clean_dict(candidates[0])
	return {}


def _decision(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("conversation_action_decision"))


def _validation(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("validation_result"))


def _authority(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("authority_plan"))


def _evidence(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("evidence_plan"))


def _context(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("context_resolution"))


def _requery(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("governed_requery_plan"))


def _activation(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("activation_assessment"))


def _response(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("professional_response"))


def _schema_assessment(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	assessment = _clean_dict(_clean_dict(trace_payload).get("schema_hardening_assessment"))
	if assessment:
		return assessment
	try:
		return validate_nbu_trace_schema_hardening(trace_payload, response_payload=_response(trace_payload))
	except Exception as exc:
		return {
			"ok": False,
			"errors": [f"schema_hardening_assessment_failed:{exc}"],
			"warnings": [],
		}


def _candidate_values(candidate: Dict[str, Any], trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	requery = _requery(trace_payload)
	context = _context(trace_payload)
	authority = _authority(trace_payload)
	return {
		"business_domain": _clean_text(candidate.get("business_domain")),
		"authority_class": _clean_text(candidate.get("authority_class") or authority.get("authority_class")),
		"target_reference": _clean_text(candidate.get("target_reference") or context.get("target_reference")),
		"rank": int(context.get("resolved_rank") or _clean_dict(candidate.get("target_entity")).get("rank") or 0),
		"capability_ids": _clean_list(candidate.get("candidate_capability_ids")) + _clean_list(requery.get("target_capability_ids")),
		"report_names": _clean_list(candidate.get("candidate_report_names")) + _clean_list(requery.get("target_report_names")),
		"family_ids": (
			_clean_list(candidate.get("candidate_composite_family_ids"))
			+ _clean_list(requery.get("target_composite_family_ids"))
			+ [_clean_text(_clean_dict(trace_payload.get("current_artifact")).get("family_id"))]
			+ [_clean_text(_clean_dict(trace_payload.get("recent_focus")).get("family_id"))]
		),
		"requested_metrics": _clean_list(candidate.get("requested_metrics")) + _clean_list(requery.get("requested_metrics")),
		"requested_dimensions": _clean_list(candidate.get("requested_dimensions")) + _clean_list(requery.get("requested_dimensions")),
	}


def _expected_alternatives(value: Any) -> List[str]:
	if isinstance(value, list):
		return _clean_list(value)
	text = _clean_text(value)
	if not text:
		return []
	if "_or_" in text:
		return [part for part in text.split("_or_") if part]
	if " or " in text.lower():
		return [part for part in text.lower().split(" or ") if part]
	return [text]


def _matches_any(actual_values: List[str], expected_values: List[str]) -> bool:
	actual_norms = [_normalize(value) for value in actual_values if _normalize(value)]
	expected_norms = [_normalize(value) for value in expected_values if _normalize(value)]
	if not expected_norms:
		return True
	if not actual_norms:
		return False
	for expected in expected_norms:
		for actual in actual_norms:
			if expected == actual or expected in actual or actual in expected:
				return True
	return False


def _target_checks(case_payload: Dict[str, Any], trace_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	case = _clean_dict(case_payload)
	expected = _clean_dict(case.get("expected_target"))
	candidate = _selected_candidate(trace_payload)
	actual = _candidate_values(candidate, trace_payload)
	checks: List[Dict[str, Any]] = []

	def add_check(field: str, expected_value: Any, actual_values: List[str], bucket: str) -> None:
		expected_values = _expected_alternatives(expected_value)
		passed = _matches_any(actual_values, expected_values)
		checks.append(
			{
				"field": field,
				"expected": expected_value,
				"actual": _dedupe(actual_values),
				"passed": passed,
				"failure_bucket": "" if passed else bucket,
			}
		)

	if "business_domain" in expected:
		add_check("business_domain", expected.get("business_domain"), [actual["business_domain"]], "model_misunderstanding")
	if "authority_class" in expected:
		add_check("authority_class", expected.get("authority_class"), [actual["authority_class"]], "model_misunderstanding")
	if "target_reference" in expected:
		add_check("target_reference", expected.get("target_reference"), [actual["target_reference"]], "context_graph_failure")
	if "rank" in expected:
		expected_rank = int(expected.get("rank") or 0)
		actual_rank = int(actual.get("rank") or 0)
		checks.append(
			{
				"field": "rank",
				"expected": expected_rank,
				"actual": actual_rank,
				"passed": expected_rank == actual_rank,
				"failure_bucket": "" if expected_rank == actual_rank else "context_graph_failure",
			}
		)
	if "capability_id" in expected:
		add_check("capability_id", expected.get("capability_id"), actual["capability_ids"], "model_misunderstanding")
	if "preferred_family_id" in expected:
		family_expected = [expected.get("preferred_family_id")]
		if expected.get("fallback_family_id"):
			family_expected.append(expected.get("fallback_family_id"))
		add_check("preferred_family_id", family_expected, actual["family_ids"], "model_misunderstanding")
	if "artifact_family" in expected:
		if _normalize(expected.get("artifact_family")) in GENERIC_EXPECTED_TARGET_PLACEHOLDERS:
			actual_artifact_values = actual["family_ids"] + actual["report_names"] + [_clean_text(_context(trace_payload).get("resolved_artifact_id"))]
			passed = bool([value for value in actual_artifact_values if _clean_text(value)])
			checks.append(
				{
					"field": "artifact_family",
					"expected": expected.get("artifact_family"),
					"actual": _dedupe(actual_artifact_values),
					"passed": passed,
					"failure_bucket": "" if passed else "context_graph_failure",
				}
			)
		else:
			add_check("artifact_family", expected.get("artifact_family"), actual["family_ids"] + actual["report_names"], "context_graph_failure")
	if "requested_metrics" in expected:
		for metric in _clean_list(expected.get("requested_metrics")):
			add_check("requested_metric", metric, actual["requested_metrics"], "model_misunderstanding")
	if "required_concepts" in expected:
		concept_values = (
			[actual["business_domain"]]
			+ actual["requested_metrics"]
			+ actual["requested_dimensions"]
			+ actual["capability_ids"]
			+ actual["report_names"]
			+ actual["family_ids"]
		)
		for concept in _clean_list(expected.get("required_concepts")):
			add_check("required_concept", concept, concept_values, "model_misunderstanding")

	return checks


def _taxonomy_ids() -> set[str]:
	return {_clean_text(bucket.get("bucket_id")) for bucket in NBU_EVALUATION_FAILURE_TAXONOMY}


def list_nbu_evaluation_failure_taxonomy() -> List[Dict[str, Any]]:
	return [dict(bucket) for bucket in NBU_EVALUATION_FAILURE_TAXONOMY]


def validate_nbu_evaluation_failure_taxonomy() -> Dict[str, Any]:
	required = {
		"model_misunderstanding",
		"missing_registry_metadata",
		"context_graph_failure",
		"validation_gate_failure",
		"route_execution_failure",
		"renderer_quality_failure",
		"policy_evidence_gap",
		"latency_runtime_unavailable",
	}
	errors: List[str] = []
	seen: set[str] = set()
	for index, bucket in enumerate(NBU_EVALUATION_FAILURE_TAXONOMY):
		bucket_id = _clean_text(bucket.get("bucket_id"))
		if not bucket_id:
			errors.append(f"bucket_{index}:missing_bucket_id")
		elif bucket_id in seen:
			errors.append(f"{bucket_id}:duplicate_bucket_id")
		seen.add(bucket_id)
		for key in ("label", "meaning"):
			if not _clean_text(bucket.get(key)):
				errors.append(f"{bucket_id or 'bucket_' + str(index)}:missing_{key}")
	for bucket_id in sorted(required.difference(seen)):
		errors.append(f"missing_required_bucket:{bucket_id}")
	return {
		"ok": not errors,
		"schema_version": NBU_EVALUATION_HARNESS_VERSION,
		"bucket_count": len(NBU_EVALUATION_FAILURE_TAXONOMY),
		"errors": errors,
	}


def evaluate_nbu_trace_against_front_controller_case(
	*,
	case_payload: Dict[str, Any],
	trace_payload: Dict[str, Any],
	latency_ms: int | float | None = None,
	latency_budget_ms: int = DEFAULT_LATENCY_BUDGET_MS,
) -> Dict[str, Any]:
	case = _clean_dict(case_payload)
	trace = _clean_dict(trace_payload)
	decision = _decision(trace)
	validation = _validation(trace)
	authority = _authority(trace)
	evidence = _evidence(trace)
	requery = _requery(trace)
	activation = _activation(trace)
	response = _response(trace)
	schema = _schema_assessment(trace)

	expected_action = _clean_text(case.get("expected_action"))
	actual_action = _clean_text(decision.get("action")) or "observe_only"
	response_mode = _clean_text(decision.get("response_mode")) or "shadow_trace_only"
	action_match = expected_action == actual_action
	target_checks = _target_checks(case, trace)
	target_match = all(bool(check.get("passed")) for check in target_checks)

	diagnostic_buckets: List[str] = []
	failure_buckets: List[str] = []
	evaluation_notes: List[str] = []

	if not action_match:
		failure_buckets.append("model_misunderstanding")
		evaluation_notes.append(f"expected_action={expected_action};actual_action={actual_action}")

	for check in target_checks:
		if not bool(check.get("passed")):
			failure_buckets.append(_clean_text(check.get("failure_bucket")) or "model_misunderstanding")
			evaluation_notes.append(f"target_check_failed:{check.get('field')}")

	validation_status = _clean_text(validation.get("status")).lower()
	if validation_status in {"runtime_unavailable", "shadow_no_candidates"} or not trace.get("candidate_interpretations"):
		failure_buckets.append("latency_runtime_unavailable")
	if latency_ms is not None and _clean_float(latency_ms) > float(latency_budget_ms):
		failure_buckets.append("latency_runtime_unavailable")
		evaluation_notes.append(f"latency_budget_exceeded:{latency_ms}>{latency_budget_ms}")

	validation_warnings = _clean_list(validation.get("validation_warnings"))
	validation_errors = _clean_list(validation.get("validation_errors"))
	if any("inactive_" in warning or "missing_" in warning or "not_registered" in warning for warning in validation_warnings + validation_errors):
		diagnostic_buckets.append("missing_registry_metadata")
	if validation_errors or validation_status in {"insufficient_confidence", "blocked_by_authority_policy"}:
		diagnostic_buckets.append("validation_gate_failure")

	if not bool(schema.get("ok", True)):
		failure_buckets.append("validation_gate_failure")
		evaluation_notes.extend([f"schema:{error}" for error in _clean_list(schema.get("errors"))[:5]])

	if actual_action in EXECUTION_REQUIRED_ACTIONS and response_mode == "governed_query":
		requery_status = _clean_text(requery.get("status")).lower()
		if requery_status in {"unsupported", "not_evaluated", ""} and not bool(requery.get("shadow_execution_ready")):
			failure_buckets.append("route_execution_failure")

	quality = validate_nbu_user_facing_response_text(response) if response else {"ok": True, "violations": []}
	if _clean_list(response.get("quality_warnings")) or not bool(quality.get("ok")):
		failure_buckets.append("renderer_quality_failure")
		evaluation_notes.extend([f"user_text_violation:{term}" for term in _clean_list(quality.get("violations"))])
	if actual_action in PRESENTATION_ONLY_ACTIONS and response and not bool(response.get("safe_to_show")):
		failure_buckets.append("renderer_quality_failure")
		evaluation_notes.append("presentation_response_not_safe_to_show")

	authority_class = _clean_text(authority.get("authority_class") or _selected_candidate(trace).get("authority_class")).lower()
	if (
		authority_class in POLICY_GATED_AUTHORITY_CLASSES
		or _clean_list(evidence.get("missing_fields"))
		or _clean_text(requery.get("status")).lower() in {"unsupported", "blocked_by_authority_policy"}
	):
		diagnostic_buckets.append("policy_evidence_gap")

	if _clean_list(activation.get("blockers")):
		diagnostic_buckets.extend(
			"route_execution_failure"
			if blocker == "requires_execution_lane_activation"
			else "renderer_quality_failure"
			if blocker.startswith("professional_response")
			else "validation_gate_failure"
			if blocker in {"missing_candidate_interpretation", "runtime_interpretation_not_ready"}
			else ""
			for blocker in _clean_list(activation.get("blockers"))
		)

	failure_buckets = _dedupe([bucket for bucket in failure_buckets if bucket in _taxonomy_ids()])
	diagnostic_buckets = _dedupe([bucket for bucket in diagnostic_buckets if bucket in _taxonomy_ids()])
	passed = action_match and target_match and not failure_buckets
	return {
		"type": "qwen_nbu_front_controller_case_evaluation_report",
		"schema_version": NBU_EVALUATION_HARNESS_VERSION,
		"case_id": _clean_text(case.get("case_id")),
		"expected_action": expected_action,
		"actual_action": actual_action,
		"response_mode": response_mode,
		"action_match": action_match,
		"target_match": target_match,
		"passed": passed,
		"failure_buckets": failure_buckets,
		"diagnostic_buckets": diagnostic_buckets,
		"target_checks": target_checks,
		"latency_ms": latency_ms,
		"latency_budget_ms": latency_budget_ms,
		"evaluation_notes": _dedupe(evaluation_notes),
	}


def summarize_nbu_front_controller_evaluations(evaluation_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
	reports = [_clean_dict(report) for report in evaluation_reports if isinstance(report, dict)]
	failure_bucket_counts: Dict[str, int] = {bucket_id: 0 for bucket_id in sorted(_taxonomy_ids())}
	diagnostic_bucket_counts: Dict[str, int] = {bucket_id: 0 for bucket_id in sorted(_taxonomy_ids())}
	for report in reports:
		for bucket in _clean_list(report.get("failure_buckets")):
			if bucket in failure_bucket_counts:
				failure_bucket_counts[bucket] += 1
		for bucket in _clean_list(report.get("diagnostic_buckets")):
			if bucket in diagnostic_bucket_counts:
				diagnostic_bucket_counts[bucket] += 1
	pass_count = sum(1 for report in reports if bool(report.get("passed")))
	return {
		"type": "qwen_nbu_front_controller_evaluation_summary",
		"schema_version": NBU_EVALUATION_HARNESS_VERSION,
		"case_count": len(reports),
		"pass_count": pass_count,
		"fail_count": len(reports) - pass_count,
		"pass_rate": round(pass_count / max(1, len(reports)), 4),
		"failure_bucket_counts": failure_bucket_counts,
		"diagnostic_bucket_counts": diagnostic_bucket_counts,
	}


def validate_nbu_front_controller_evaluation_harness() -> Dict[str, Any]:
	errors: List[str] = []
	taxonomy = validate_nbu_evaluation_failure_taxonomy()
	errors.extend(_clean_list(taxonomy.get("errors")))
	for case in list_nbu_front_controller_baseline_cases():
		if not _clean_text(case.get("expected_action")):
			errors.append(f"{_clean_text(case.get('case_id'))}:missing_expected_action")
		for failure_class in _clean_list(case.get("failure_classes")):
			if not failure_class:
				errors.append(f"{_clean_text(case.get('case_id'))}:empty_failure_class")
	return {
		"ok": not errors,
		"schema_version": NBU_EVALUATION_HARNESS_VERSION,
		"taxonomy_bucket_count": len(NBU_EVALUATION_FAILURE_TAXONOMY),
		"baseline_case_count": len(list_nbu_front_controller_baseline_cases()),
		"errors": errors,
	}
