from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from .conversation_control_language import classify_conversation_control_evidence
from .natural_business_understanding_activation import build_nbu_activation_assessment
from .natural_business_understanding_contracts import (
	ALLOWED_AUTHORITY_CLASSES,
	ALLOWED_CANDIDATE_ROUTES,
	ALLOWED_EVIDENCE_NEEDS,
	ALLOWED_INTENT_SCOPES,
	ALLOWED_REQUESTED_ACTIONS,
	ALLOWED_TARGET_REFERENCES,
	NBUEvidencePlanContract,
	NBUGovernedRequeryPlanContract,
	NBUSystemConfidenceContract,
	NBUAuthorityPlanContract,
	NBUConversationActionDecisionContract,
	NBUContextResolutionContract,
	NBUValidationResultContract,
	build_nbu_candidate_interpretation_contract,
	build_nbu_trace_contract,
)
from .natural_business_understanding_context_resolution import resolve_nbu_context_reference
from .natural_business_understanding_decision import build_nbu_conversation_action_decision
from .natural_business_understanding_requery_planner import build_nbu_governed_requery_plan
from .natural_business_understanding_response_renderer import render_nbu_professional_response
from .natural_business_understanding_schema_hardening import validate_nbu_trace_schema_hardening
from .natural_business_understanding_validation import evaluate_nbu_candidate_against_context


NBU_RUNTIME_ENDPOINT_PATH = "/interpret-business-understanding"
NBU_SHADOW_ENGINE_NAME = "semantic_business_understanding"


RuntimeCall = Callable[..., Dict[str, Any]]


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clamp_confidence(value: Any) -> float:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	return max(0.0, min(1.0, numeric))


def _allowed_values_payload() -> Dict[str, List[str]]:
	return {
		"intent_scopes": sorted(ALLOWED_INTENT_SCOPES),
		"requested_actions": sorted(ALLOWED_REQUESTED_ACTIONS),
		"target_references": sorted(ALLOWED_TARGET_REFERENCES),
		"candidate_routes": sorted(ALLOWED_CANDIDATE_ROUTES),
		"evidence_needs": sorted(ALLOWED_EVIDENCE_NEEDS),
		"authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
	}


def _compact_conversation_control_evidence(message: str) -> Dict[str, Any]:
	try:
		evidence = classify_conversation_control_evidence(message)
	except Exception:
		return {}
	if not isinstance(evidence, dict):
		return {}
	action_id = _clean_text(evidence.get("action_id"))
	if not action_id:
		return {}
	internal_details = _clean_dict(evidence.get("internal_details"))
	allowed_internal_keys = {
		"target_hint",
		"target_grain",
		"target_focus_kind",
		"targeted_restore",
		"discard_prefix_applied",
		"discarded_branch_before_action",
		"chained_remainder_message",
	}
	return {
		"evidence_class": _clean_text(evidence.get("evidence_class")),
		"action_id": action_id,
		"evidence_strength": _clean_text(evidence.get("evidence_strength")),
		"matched_surface_form": _clean_text(evidence.get("matched_surface_form")),
		"embedded_business_message": _clean_text(evidence.get("embedded_business_message")),
		"internal_details": {
			key: internal_details.get(key)
			for key in allowed_internal_keys
			if key in internal_details and internal_details.get(key) not in ("", None)
		},
	}


def _compact_artifact_context(value: Any) -> Dict[str, Any]:
	artifact = _clean_dict(value)
	if not artifact:
		return {}
	allowed_keys = {
		"artifact_id",
		"artifact_type",
		"family_id",
		"family",
		"report_name",
		"title",
		"as_of_date",
		"period_start",
		"period_end",
		"row_count",
		"primary_entity_type",
		"primary_metric",
		"sort_metric",
		"columns",
		"available_fields",
		"affordances",
	}
	return {key: artifact.get(key) for key in allowed_keys if key in artifact and artifact.get(key) is not None}


def _compact_metadata_specs(values: Any, allowed_keys: set[str]) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	out: List[Dict[str, Any]] = []
	for item in values[:50]:
		spec = _clean_dict(item)
		if not spec:
			continue
		out.append({key: spec.get(key) for key in allowed_keys if key in spec and spec.get(key) is not None})
	return out


def build_nbu_shadow_interpretation_context(
	*,
	raw_message: str = "",
	current_artifact: Dict[str, Any] | None = None,
	recent_focus: Dict[str, Any] | None = None,
	metadata_context: Dict[str, Any] | None = None,
	conversation_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	"""Build a compact, registry-shaped context for the lightweight NBU model.

	The returned payload is intentionally descriptive, not executable. It gives the
	model allowed vocabulary and current context hints, while downstream contract
	validation remains the authority.
	"""

	metadata = _clean_dict(metadata_context)
	report_specs = _compact_metadata_specs(
		metadata.get("reports") or metadata.get("report_specs"),
		{
			"report_name",
			"family",
			"capability_ids",
			"supported_intent_classes",
			"supported_dimensions",
			"supported_metrics",
			"semantic_tags",
			"grounding_mode",
			"activation_state",
		},
	)
	composite_family_specs = _compact_metadata_specs(
		metadata.get("composite_families") or metadata.get("composite_family_specs") or metadata.get("families"),
		{
			"family_id",
			"label",
			"entity_grain",
			"subject_alias_value",
			"allowed_primary_metrics",
			"allowed_secondary_metrics",
			"metric_semantic_key_map",
			"supported_variation_values",
			"activation_state",
			"blocked_reason",
		},
	)
	kpi_execution_specs = _compact_metadata_specs(
		metadata.get("governed_kpi_executions") or metadata.get("governed_kpi_execution_specs") or metadata.get("executions"),
		{
			"execution_id",
			"definition_id",
			"label",
			"source_capabilities",
			"source_reports",
			"required_dimensions",
			"value_metric_mapping",
			"activation_state",
			"blocked_reason",
		},
	)
	return {
		"contract_version": "1.0",
		"shadow_mode": True,
		"allowed_values": _allowed_values_payload(),
		"current_artifact": _compact_artifact_context(current_artifact),
		"recent_focus": _compact_artifact_context(recent_focus),
		"conversation_state": _compact_artifact_context(conversation_state),
		"conversation_control_evidence": _compact_conversation_control_evidence(raw_message),
		"metadata_context": {
			"capability_ids": _clean_list(metadata.get("capability_ids")),
			"report_names": _clean_list(metadata.get("report_names")),
			"composite_family_ids": _clean_list(metadata.get("composite_family_ids")),
			"governed_kpi_ids": _clean_list(metadata.get("governed_kpi_ids")),
			"business_domains": _clean_list(metadata.get("business_domains")),
			"business_terms": _clean_list(metadata.get("business_terms")),
			"reports": report_specs,
			"composite_families": composite_family_specs,
			"governed_kpi_executions": kpi_execution_specs,
		},
		"instructions": [
			"Return ranked candidate interpretations only.",
			"Use allowed values where they apply.",
			"Preserve future business domains if not present in metadata.",
			"Do not decide execution, approval, or recommendations.",
		],
	}


def _extract_interpretation_payload(runtime_response: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(runtime_response, dict):
		return {}
	interpretation = runtime_response.get("interpretation")
	if isinstance(interpretation, dict):
		return interpretation
	return runtime_response


def _candidate_from_payload(index: int, raw_candidate: Any) -> Tuple[Any | None, List[str]]:
	warnings: List[str] = []
	if not isinstance(raw_candidate, dict):
		return None, [f"candidate_{index}_invalid_shape"]

	candidate_id = _clean_text(raw_candidate.get("candidate_id")) or f"candidate-{index + 1}"
	candidate = build_nbu_candidate_interpretation_contract(
		candidate_id=candidate_id,
		intent_scope=raw_candidate.get("intent_scope", "unknown"),
		business_domain=raw_candidate.get("business_domain", ""),
		requested_action=raw_candidate.get("requested_action", "unknown"),
		target_reference=raw_candidate.get("target_reference", "none"),
		target_entity=_clean_dict(raw_candidate.get("target_entity")),
		candidate_route=raw_candidate.get("candidate_route", "unknown"),
		candidate_capability_ids=_clean_list(raw_candidate.get("candidate_capability_ids")),
		candidate_report_names=_clean_list(raw_candidate.get("candidate_report_names")),
		candidate_composite_family_ids=_clean_list(raw_candidate.get("candidate_composite_family_ids")),
		requested_metrics=_clean_list(raw_candidate.get("requested_metrics")),
		requested_dimensions=_clean_list(raw_candidate.get("requested_dimensions")),
		requested_time_scope=raw_candidate.get("requested_time_scope", ""),
		evidence_need=raw_candidate.get("evidence_need", "unknown"),
		authority_class=raw_candidate.get("authority_class", "unknown"),
		model_confidence=_clamp_confidence(raw_candidate.get("model_confidence")),
		model_reason=raw_candidate.get("model_reason", ""),
	)
	return candidate, warnings


def _runtime_failure_trace(
	*,
	request_id: str,
	session_id: str,
	message: str,
	error: str,
) -> Dict[str, Any]:
	trace = build_nbu_trace_contract(
		request_id=request_id,
		session_id=session_id,
		raw_message=message,
		validation_result=NBUValidationResultContract(
			status="runtime_unavailable",
			validation_errors=[_clean_text(error) or "NBU runtime interpretation failed."],
		),
		conversation_action_decision=NBUConversationActionDecisionContract(
			action="observe_only",
			response_mode="shadow_trace_only",
			requires_routing_change=False,
			safe_to_execute=False,
			reason="NBU shadow interpretation failed without changing runtime behavior.",
		),
		trace_summary="NBU shadow runtime unavailable; no routing behavior changed.",
		shadow_mode=True,
	)
	payload = trace.to_payload()
	response = render_nbu_professional_response(payload)
	payload["professional_response"] = response
	payload["schema_hardening_assessment"] = validate_nbu_trace_schema_hardening(payload, response_payload=response)
	payload["activation_assessment"] = build_nbu_activation_assessment(payload)
	return payload


def _resolve_runtime_call(runtime_call: RuntimeCall | None) -> RuntimeCall:
	if runtime_call is not None:
		return runtime_call
	try:
		from .runtime_client import call_qwen_runtime_business_understanding_interpretation
	except Exception as exc:  # pragma: no cover - only hit when runtime client is absent in stripped workspaces
		raise RuntimeError(f"NBU runtime client is not available: {exc}") from exc
	return call_qwen_runtime_business_understanding_interpretation


def _shadow_decision_contract(
	decision: NBUConversationActionDecisionContract,
	*,
	control_evidence: Dict[str, Any] | None = None,
) -> NBUConversationActionDecisionContract:
	payload = decision.to_payload()
	technical_details = _clean_dict(payload.get("technical_details"))
	clean_control_evidence = _clean_dict(control_evidence)
	if clean_control_evidence:
		technical_details["conversation_control_evidence"] = clean_control_evidence
	technical_details.update(
		{
			"shadow_mode": True,
			"runtime_execution_enabled": False,
			"execution_not_performed": True,
			"proposed_action": _clean_text(payload.get("action")),
			"proposed_response_mode": _clean_text(payload.get("response_mode")),
		}
	)
	return NBUConversationActionDecisionContract(
		action=_clean_text(payload.get("action")) or "observe_only",
		response_mode=_clean_text(payload.get("response_mode")) or "shadow_trace_only",
		selected_candidate_id=_clean_text(payload.get("selected_candidate_id")),
		requires_routing_change=bool(payload.get("requires_routing_change")),
		safe_to_execute=bool(payload.get("safe_to_execute")),
		reason=_clean_text(payload.get("reason")),
		suggested_options=_clean_list(payload.get("suggested_options")),
		technical_details=technical_details,
	)


def interpret_natural_business_understanding_shadow(
	*,
	request_id: str,
	session_id: str,
	user_id: str = "",
	site_name: str = "",
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
	latest_grounded_turn: Dict[str, Any] | None = None,
	latest_assistant_payload: Dict[str, Any] | None = None,
	current_artifact: Dict[str, Any] | None = None,
	recent_focus: Dict[str, Any] | None = None,
	metadata_context: Dict[str, Any] | None = None,
	conversation_state: Dict[str, Any] | None = None,
	runtime_call: RuntimeCall | None = None,
) -> Dict[str, Any]:
	"""Call the lightweight NBU model in shadow mode and validate the result.

	This function is deliberately observe-only. It never returns a routing command
	that should be executed by the caller. Later NBU activation slices can consume
	the same trace contract after stronger registry and evidence gates are in
	place.
	"""

	context = build_nbu_shadow_interpretation_context(
		raw_message=message,
		current_artifact=current_artifact,
		recent_focus=recent_focus,
		metadata_context=metadata_context,
		conversation_state=conversation_state,
	)
	control_evidence = _clean_dict(context.get("conversation_control_evidence"))
	try:
		call = _resolve_runtime_call(runtime_call)
		runtime_response = call(
			request_id=_clean_text(request_id),
			session_id=_clean_text(session_id),
			user_id=_clean_text(user_id),
			site_name=_clean_text(site_name),
			message=_clean_text(message),
			recent_messages=list(recent_messages or []),
			latest_grounded_turn=_clean_dict(latest_grounded_turn),
			latest_assistant_payload=_clean_dict(latest_assistant_payload),
			interpretation_context=context,
		)
	except Exception as exc:
		return _runtime_failure_trace(
			request_id=request_id,
			session_id=session_id,
			message=message,
			error=str(exc),
		)

	if not isinstance(runtime_response, dict) or not bool(runtime_response.get("ok", True)):
		return _runtime_failure_trace(
			request_id=request_id,
			session_id=session_id,
			message=message,
			error=str((runtime_response or {}).get("error") or "NBU runtime returned an unsuccessful response."),
		)

	interpretation = _extract_interpretation_payload(runtime_response)
	raw_candidates = interpretation.get("candidate_interpretations")
	if not isinstance(raw_candidates, list):
		raw_candidates = []

	candidates = []
	warnings: List[str] = []
	for index, raw_candidate in enumerate(raw_candidates[:5]):
		candidate, candidate_warnings = _candidate_from_payload(index, raw_candidate)
		warnings.extend(candidate_warnings)
		if candidate is not None:
			candidates.append(candidate)

	selected_candidate_id = _clean_text(interpretation.get("selected_candidate_id"))
	if not selected_candidate_id and candidates:
		selected_candidate_id = candidates[0].candidate_id
	selected_candidate = next((candidate for candidate in candidates if candidate.candidate_id == selected_candidate_id), None)
	if selected_candidate is None and candidates:
		selected_candidate = candidates[0]
		selected_candidate_id = selected_candidate.candidate_id

	if not candidates:
		warnings.append("no_candidate_interpretations")

	if selected_candidate is not None:
		context_resolution = resolve_nbu_context_reference(
			raw_message=message,
			candidate_payload=selected_candidate.to_payload(),
			current_artifact=current_artifact,
			recent_focus=recent_focus,
		)
		validation_result, system_confidence = evaluate_nbu_candidate_against_context(
			candidate_payload=selected_candidate.to_payload(),
			interpretation_context=context,
		)
		if warnings:
			validation_result = NBUValidationResultContract(
				status=validation_result.status,
				registry_match_strength=validation_result.registry_match_strength,
				context_reference_clarity=validation_result.context_reference_clarity,
				artifact_compatibility=validation_result.artifact_compatibility,
				evidence_availability=validation_result.evidence_availability,
				authority_policy_state=validation_result.authority_policy_state,
				validation_errors=validation_result.validation_errors,
				validation_warnings=list(validation_result.validation_warnings or []) + warnings,
			)
		action_decision, evidence_plan, authority_plan = build_nbu_conversation_action_decision(
			candidate_payload=selected_candidate.to_payload(),
			validation_payload=validation_result.to_payload(),
			system_confidence_payload=system_confidence.to_payload(),
		)
		governed_requery_plan = build_nbu_governed_requery_plan(
			candidate_payload=selected_candidate.to_payload(),
			validation_payload=validation_result.to_payload(),
			evidence_plan_payload=evidence_plan.to_payload(),
			context_resolution_payload=context_resolution.to_payload(),
			interpretation_context=context,
		)
		action_decision = _shadow_decision_contract(action_decision, control_evidence=control_evidence)
	else:
		validation_result = NBUValidationResultContract(
			status="shadow_no_candidates",
			authority_policy_state="not_evaluated",
			validation_warnings=warnings,
		)
		system_confidence = NBUSystemConfidenceContract()
		action_decision = NBUConversationActionDecisionContract(
			action="observe_only",
			response_mode="shadow_trace_only",
			requires_routing_change=False,
			safe_to_execute=False,
			reason="No NBU candidate was available; no behavior changed.",
			technical_details={
				"shadow_mode": True,
				"runtime_execution_enabled": False,
				"execution_not_performed": True,
			},
		)
		evidence_plan = NBUEvidencePlanContract(
			evidence_need="unknown",
			reason="No candidate evidence plan was available in NBU shadow mode.",
		)
		authority_plan = NBUAuthorityPlanContract(
			authority_class="unknown",
			authority_allowed=False,
			approval_state="not_evaluated",
			boundary_reason="No candidate authority plan was available in NBU shadow mode.",
		)
		context_resolution = NBUContextResolutionContract(
			status="not_evaluated",
			target_reference="none",
		)
		governed_requery_plan = NBUGovernedRequeryPlanContract(
			status="not_evaluated",
			planner_mode="none",
			reason="No candidate was available for governed requery planning.",
		)

	trace = build_nbu_trace_contract(
		request_id=request_id,
		session_id=session_id,
		raw_message=message,
		detected_language=_clean_text(interpretation.get("detected_language")) or "en",
		candidate_interpretations=candidates,
		selected_candidate_id=selected_candidate_id,
		validation_result=validation_result,
		system_confidence=system_confidence,
		conversation_action_decision=action_decision,
		evidence_plan=evidence_plan,
		authority_plan=authority_plan,
		context_resolution=context_resolution,
		governed_requery_plan=governed_requery_plan,
		trace_summary="NBU shadow interpretation and proposed action captured without routing behavior change.",
		shadow_mode=True,
	)
	payload = trace.to_payload()
	response = render_nbu_professional_response(payload)
	payload["professional_response"] = response
	payload["schema_hardening_assessment"] = validate_nbu_trace_schema_hardening(payload, response_payload=response)
	payload["activation_assessment"] = build_nbu_activation_assessment(payload)
	return payload
