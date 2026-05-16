from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Dict, List


CONTRACT_VERSION = "1.0"

ALLOWED_INTENT_SCOPES = {
    "fresh_query",
    "followup",
    "context_reference",
    "policy_boundary",
    "capability_question",
    "out_of_scope",
    "unknown",
}

ALLOWED_REQUESTED_ACTIONS = {
    "show",
    "explain",
    "detail",
    "format",
    "compare",
    "requery",
    "recommend",
    "predict",
    "approve",
    "restore",
    "cancel",
    "clarify",
    "unknown",
}

ALLOWED_TARGET_REFERENCES = {
    "current_artifact",
    "previous_artifact",
    "rank_n",
    "named_entity",
    "selected_entity",
    "candidate_list",
    "unclear",
    "none",
}

ALLOWED_CANDIDATE_ROUTES = {
    "frontdoor_composite",
    "governed_kpi",
    "fresh_query",
    "local_followup",
    "entity_detail",
    "presentation_transform",
    "boundary",
    "clarification",
    "recovery",
    "out_of_scope",
    "unknown",
}

ALLOWED_EVIDENCE_NEEDS = {
    "current_artifact_ok",
    "needs_governed_requery",
    "presentation_only",
    "unsupported_policy",
    "needs_clarification",
    "out_of_scope",
    "unknown",
}

ALLOWED_AUTHORITY_CLASSES = {
    "safe_read",
    "safe_explanation",
    "governed_requery",
    "recommendation",
    "prediction",
    "approval_action",
    "policy_decision",
    "causal_driver_analysis",
    "hidden_score_classification",
    "unsupported_analysis",
    "unknown",
}

ALLOWED_ACTION_DECISIONS = {
    "answer_from_current_artifact",
    "reformat_previous_answer",
    "execute_fresh_governed_query",
    "execute_governed_requery",
    "ask_clarification",
    "show_supported_options",
    "restore_previous_context",
    "clear_pending_context",
    "reject_with_boundary",
    "answer_capability_question",
    "out_of_scope_response",
    "observe_only",
}

ALLOWED_RESPONSE_MODES = {
    "direct_answer",
    "presentation_transform",
    "governed_query",
    "clarification",
    "boundary",
    "supported_options",
    "capability_guidance",
    "out_of_scope",
    "shadow_trace_only",
}


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _clean_dict_list(values: Any) -> List[Dict[str, Any]]:
    if not isinstance(values, list):
        return []
    return [dict(value) for value in values if isinstance(value, dict)]


def _clamp_confidence(value: Any) -> float:
    try:
        numeric = float(value or 0.0)
    except Exception:
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


def _allowed_or_unknown(value: Any, allowed: set[str]) -> str:
    clean = _clean_text(value).lower()
    return clean if clean in allowed else "unknown"


def _candidate_evidence_need(*, requested_action: Any, candidate_route: Any, evidence_need: Any) -> str:
    requested = _clean_text(requested_action).lower()
    route = _clean_text(candidate_route).lower()
    evidence = _clean_text(evidence_need).lower()
    if requested == "format" or route == "presentation_transform" or evidence == "presentation_only":
        return "presentation_only"
    return _allowed_or_unknown(evidence, ALLOWED_EVIDENCE_NEEDS)


@dataclass(frozen=True)
class NBUCandidateInterpretationContract:
    candidate_id: str
    intent_scope: str = "unknown"
    business_domain: str = ""
    requested_action: str = "unknown"
    target_reference: str = "none"
    target_entity: Dict[str, Any] = field(default_factory=dict)
    candidate_route: str = "unknown"
    candidate_capability_ids: List[str] = field(default_factory=list)
    candidate_report_names: List[str] = field(default_factory=list)
    candidate_composite_family_ids: List[str] = field(default_factory=list)
    requested_metrics: List[str] = field(default_factory=list)
    requested_dimensions: List[str] = field(default_factory=list)
    requested_time_scope: str = ""
    evidence_need: str = "unknown"
    authority_class: str = "unknown"
    model_confidence: float = 0.0
    model_reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_candidate_interpretation_contract",
            "contract_version": CONTRACT_VERSION,
            "candidate_id": self.candidate_id,
            "intent_scope": _allowed_or_unknown(self.intent_scope, ALLOWED_INTENT_SCOPES),
            "business_domain": _clean_text(self.business_domain),
            "requested_action": _allowed_or_unknown(self.requested_action, ALLOWED_REQUESTED_ACTIONS),
            "target_reference": _allowed_or_unknown(self.target_reference, ALLOWED_TARGET_REFERENCES),
            "target_entity": _clean_dict(self.target_entity),
            "candidate_route": _allowed_or_unknown(self.candidate_route, ALLOWED_CANDIDATE_ROUTES),
            "candidate_capability_ids": _clean_list(self.candidate_capability_ids),
            "candidate_report_names": _clean_list(self.candidate_report_names),
            "candidate_composite_family_ids": _clean_list(self.candidate_composite_family_ids),
            "requested_metrics": _clean_list(self.requested_metrics),
            "requested_dimensions": _clean_list(self.requested_dimensions),
            "requested_time_scope": _clean_text(self.requested_time_scope),
            "evidence_need": _candidate_evidence_need(
                requested_action=self.requested_action,
                candidate_route=self.candidate_route,
                evidence_need=self.evidence_need,
            ),
            "authority_class": _allowed_or_unknown(self.authority_class, ALLOWED_AUTHORITY_CLASSES),
            "model_confidence": _clamp_confidence(self.model_confidence),
            "model_reason": _clean_text(self.model_reason),
        }


@dataclass(frozen=True)
class NBUValidationResultContract:
    status: str = "not_evaluated"
    registry_match_strength: float = 0.0
    context_reference_clarity: float = 0.0
    artifact_compatibility: float = 0.0
    evidence_availability: float = 0.0
    authority_policy_state: str = "unknown"
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_validation_result_contract",
            "contract_version": CONTRACT_VERSION,
            "status": _clean_text(self.status) or "not_evaluated",
            "registry_match_strength": _clamp_confidence(self.registry_match_strength),
            "context_reference_clarity": _clamp_confidence(self.context_reference_clarity),
            "artifact_compatibility": _clamp_confidence(self.artifact_compatibility),
            "evidence_availability": _clamp_confidence(self.evidence_availability),
            "authority_policy_state": _clean_text(self.authority_policy_state) or "unknown",
            "validation_errors": _clean_list(self.validation_errors),
            "validation_warnings": _clean_list(self.validation_warnings),
        }


@dataclass(frozen=True)
class NBUSystemConfidenceContract:
    model_confidence: float = 0.0
    registry_confidence: float = 0.0
    context_confidence: float = 0.0
    evidence_confidence: float = 0.0
    authority_confidence: float = 0.0
    context_conflict_score: float = 0.0
    final_confidence: float = 0.0
    confidence_basis: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_system_confidence_contract",
            "contract_version": CONTRACT_VERSION,
            "model_confidence": _clamp_confidence(self.model_confidence),
            "registry_confidence": _clamp_confidence(self.registry_confidence),
            "context_confidence": _clamp_confidence(self.context_confidence),
            "evidence_confidence": _clamp_confidence(self.evidence_confidence),
            "authority_confidence": _clamp_confidence(self.authority_confidence),
            "context_conflict_score": _clamp_confidence(self.context_conflict_score),
            "final_confidence": _clamp_confidence(self.final_confidence),
            "confidence_basis": _clean_list(self.confidence_basis),
        }


@dataclass(frozen=True)
class NBUConversationActionDecisionContract:
    action: str = "observe_only"
    response_mode: str = "shadow_trace_only"
    selected_candidate_id: str = ""
    requires_routing_change: bool = False
    safe_to_execute: bool = False
    reason: str = ""
    suggested_options: List[str] = field(default_factory=list)
    technical_details: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_conversation_action_decision_contract",
            "contract_version": CONTRACT_VERSION,
            "action": _allowed_or_unknown(self.action, ALLOWED_ACTION_DECISIONS),
            "response_mode": _allowed_or_unknown(self.response_mode, ALLOWED_RESPONSE_MODES),
            "selected_candidate_id": _clean_text(self.selected_candidate_id),
            "requires_routing_change": bool(self.requires_routing_change),
            "safe_to_execute": bool(self.safe_to_execute),
            "reason": _clean_text(self.reason),
            "suggested_options": _clean_list(self.suggested_options),
            "technical_details": _clean_dict(self.technical_details),
        }


@dataclass(frozen=True)
class NBUEvidencePlanContract:
    evidence_need: str = "unknown"
    current_artifact_supported: bool = False
    governed_requery_available: bool = False
    required_artifacts: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_evidence_plan_contract",
            "contract_version": CONTRACT_VERSION,
            "evidence_need": _allowed_or_unknown(self.evidence_need, ALLOWED_EVIDENCE_NEEDS),
            "current_artifact_supported": bool(self.current_artifact_supported),
            "governed_requery_available": bool(self.governed_requery_available),
            "required_artifacts": _clean_list(self.required_artifacts),
            "missing_fields": _clean_list(self.missing_fields),
            "reason": _clean_text(self.reason),
        }


@dataclass(frozen=True)
class NBUAuthorityPlanContract:
    authority_class: str = "unknown"
    authority_allowed: bool = False
    policy_artifact_required: str = ""
    approval_state: str = "unknown"
    boundary_reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_authority_plan_contract",
            "contract_version": CONTRACT_VERSION,
            "authority_class": _allowed_or_unknown(self.authority_class, ALLOWED_AUTHORITY_CLASSES),
            "authority_allowed": bool(self.authority_allowed),
            "policy_artifact_required": _clean_text(self.policy_artifact_required),
            "approval_state": _clean_text(self.approval_state) or "unknown",
            "boundary_reason": _clean_text(self.boundary_reason),
        }


@dataclass(frozen=True)
class NBUContextResolutionContract:
    status: str = "not_evaluated"
    target_reference: str = "none"
    resolved_artifact_id: str = ""
    selected_report_family: str = ""
    selected_entity_type: str = ""
    selected_artifact_role: str = ""
    selection_strategy: str = ""
    resolved_row_index: int = -1
    resolved_rank: int = 0
    requested_rank: int = 0
    available_row_count: int = 0
    resolved_entity: Dict[str, Any] = field(default_factory=dict)
    ambiguity_options: List[str] = field(default_factory=list)
    reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_context_resolution_contract",
            "contract_version": CONTRACT_VERSION,
            "status": _clean_text(self.status) or "not_evaluated",
            "target_reference": _allowed_or_unknown(self.target_reference, ALLOWED_TARGET_REFERENCES),
            "resolved_artifact_id": _clean_text(self.resolved_artifact_id),
            "selected_report_family": _clean_text(self.selected_report_family),
            "selected_entity_type": _clean_text(self.selected_entity_type),
            "selected_artifact_role": _clean_text(self.selected_artifact_role),
            "selection_strategy": _clean_text(self.selection_strategy),
            "resolved_row_index": int(self.resolved_row_index),
            "resolved_rank": int(max(0, self.resolved_rank or 0)),
            "requested_rank": int(max(0, self.requested_rank or 0)),
            "available_row_count": int(max(0, self.available_row_count or 0)),
            "resolved_entity": _clean_dict(self.resolved_entity),
            "ambiguity_options": _clean_list(self.ambiguity_options),
            "reason": _clean_text(self.reason),
        }


@dataclass(frozen=True)
class NBUGovernedRequeryPlanContract:
    status: str = "not_evaluated"
    planner_mode: str = "none"
    target_route: str = ""
    target_capability_ids: List[str] = field(default_factory=list)
    target_report_names: List[str] = field(default_factory=list)
    target_composite_family_ids: List[str] = field(default_factory=list)
    target_governed_kpi_ids: List[str] = field(default_factory=list)
    target_entity: Dict[str, Any] = field(default_factory=dict)
    requested_metrics: List[str] = field(default_factory=list)
    requested_dimensions: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    required_context: List[str] = field(default_factory=list)
    suggested_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    shadow_execution_ready: bool = False
    reason: str = ""
    warnings: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_nbu_governed_requery_plan_contract",
            "contract_version": CONTRACT_VERSION,
            "status": _clean_text(self.status) or "not_evaluated",
            "planner_mode": _clean_text(self.planner_mode) or "none",
            "target_route": _clean_text(self.target_route),
            "target_capability_ids": _clean_list(self.target_capability_ids),
            "target_report_names": _clean_list(self.target_report_names),
            "target_composite_family_ids": _clean_list(self.target_composite_family_ids),
            "target_governed_kpi_ids": _clean_list(self.target_governed_kpi_ids),
            "target_entity": _clean_dict(self.target_entity),
            "requested_metrics": _clean_list(self.requested_metrics),
            "requested_dimensions": _clean_list(self.requested_dimensions),
            "missing_fields": _clean_list(self.missing_fields),
            "required_context": _clean_list(self.required_context),
            "suggested_alternatives": _clean_dict_list(self.suggested_alternatives),
            "shadow_execution_ready": bool(self.shadow_execution_ready),
            "reason": _clean_text(self.reason),
            "warnings": _clean_list(self.warnings),
        }


@dataclass(frozen=True)
class NaturalBusinessUnderstandingTraceContract:
    request_id: str
    session_id: str
    raw_message: str
    detected_language: str = "en"
    candidate_interpretations: List[NBUCandidateInterpretationContract] = field(default_factory=list)
    selected_candidate_id: str = ""
    validation_result: NBUValidationResultContract = field(default_factory=NBUValidationResultContract)
    system_confidence: NBUSystemConfidenceContract = field(default_factory=NBUSystemConfidenceContract)
    conversation_action_decision: NBUConversationActionDecisionContract = field(
        default_factory=NBUConversationActionDecisionContract
    )
    evidence_plan: NBUEvidencePlanContract = field(default_factory=NBUEvidencePlanContract)
    authority_plan: NBUAuthorityPlanContract = field(default_factory=NBUAuthorityPlanContract)
    context_resolution: NBUContextResolutionContract = field(default_factory=NBUContextResolutionContract)
    governed_requery_plan: NBUGovernedRequeryPlanContract = field(default_factory=NBUGovernedRequeryPlanContract)
    clarification_question: str = ""
    boundary_reason: str = ""
    trace_summary: str = ""
    shadow_mode: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "qwen_natural_business_understanding_trace_contract",
            "contract_version": CONTRACT_VERSION,
            "request_id": _clean_text(self.request_id),
            "session_id": _clean_text(self.session_id),
            "raw_message": _clean_text(self.raw_message),
            "detected_language": _clean_text(self.detected_language) or "en",
            "candidate_interpretations": [
                candidate.to_payload()
                for candidate in self.candidate_interpretations
                if isinstance(candidate, NBUCandidateInterpretationContract)
            ],
            "selected_candidate_id": _clean_text(self.selected_candidate_id),
            "validation_result": self.validation_result.to_payload(),
            "system_confidence": self.system_confidence.to_payload(),
            "conversation_action_decision": self.conversation_action_decision.to_payload(),
            "evidence_plan": self.evidence_plan.to_payload(),
            "authority_plan": self.authority_plan.to_payload(),
            "context_resolution": self.context_resolution.to_payload(),
            "governed_requery_plan": self.governed_requery_plan.to_payload(),
            "clarification_question": _clean_text(self.clarification_question),
            "boundary_reason": _clean_text(self.boundary_reason),
            "trace_summary": _clean_text(self.trace_summary),
            "shadow_mode": bool(self.shadow_mode),
            "created_at": _utc_now(),
        }


def build_nbu_candidate_interpretation_contract(
    *,
    candidate_id: str,
    intent_scope: str = "unknown",
    business_domain: str = "",
    requested_action: str = "unknown",
    target_reference: str = "none",
    target_entity: Dict[str, Any] | None = None,
    candidate_route: str = "unknown",
    candidate_capability_ids: List[str] | None = None,
    candidate_report_names: List[str] | None = None,
    candidate_composite_family_ids: List[str] | None = None,
    requested_metrics: List[str] | None = None,
    requested_dimensions: List[str] | None = None,
    requested_time_scope: str = "",
    evidence_need: str = "unknown",
    authority_class: str = "unknown",
    model_confidence: float = 0.0,
    model_reason: str = "",
) -> NBUCandidateInterpretationContract:
    return NBUCandidateInterpretationContract(
        candidate_id=_clean_text(candidate_id),
        intent_scope=intent_scope,
        business_domain=business_domain,
        requested_action=requested_action,
        target_reference=target_reference,
        target_entity=_clean_dict(target_entity),
        candidate_route=candidate_route,
        candidate_capability_ids=_clean_list(candidate_capability_ids or []),
        candidate_report_names=_clean_list(candidate_report_names or []),
        candidate_composite_family_ids=_clean_list(candidate_composite_family_ids or []),
        requested_metrics=_clean_list(requested_metrics or []),
        requested_dimensions=_clean_list(requested_dimensions or []),
        requested_time_scope=requested_time_scope,
        evidence_need=evidence_need,
        authority_class=authority_class,
        model_confidence=model_confidence,
        model_reason=model_reason,
    )


def build_nbu_trace_contract(
    *,
    request_id: str,
    session_id: str,
    raw_message: str,
    detected_language: str = "en",
    candidate_interpretations: List[NBUCandidateInterpretationContract] | None = None,
    selected_candidate_id: str = "",
    validation_result: NBUValidationResultContract | None = None,
    system_confidence: NBUSystemConfidenceContract | None = None,
    conversation_action_decision: NBUConversationActionDecisionContract | None = None,
    evidence_plan: NBUEvidencePlanContract | None = None,
    authority_plan: NBUAuthorityPlanContract | None = None,
    context_resolution: NBUContextResolutionContract | None = None,
    governed_requery_plan: NBUGovernedRequeryPlanContract | None = None,
    clarification_question: str = "",
    boundary_reason: str = "",
    trace_summary: str = "",
    shadow_mode: bool = True,
) -> NaturalBusinessUnderstandingTraceContract:
    return NaturalBusinessUnderstandingTraceContract(
        request_id=_clean_text(request_id),
        session_id=_clean_text(session_id),
        raw_message=_clean_text(raw_message),
        detected_language=_clean_text(detected_language) or "en",
        candidate_interpretations=list(candidate_interpretations or []),
        selected_candidate_id=_clean_text(selected_candidate_id),
        validation_result=validation_result or NBUValidationResultContract(),
        system_confidence=system_confidence or NBUSystemConfidenceContract(),
        conversation_action_decision=conversation_action_decision or NBUConversationActionDecisionContract(),
        evidence_plan=evidence_plan or NBUEvidencePlanContract(),
        authority_plan=authority_plan or NBUAuthorityPlanContract(),
        context_resolution=context_resolution or NBUContextResolutionContract(),
        governed_requery_plan=governed_requery_plan or NBUGovernedRequeryPlanContract(),
        clarification_question=clarification_question,
        boundary_reason=boundary_reason,
        trace_summary=trace_summary,
        shadow_mode=shadow_mode,
    )
