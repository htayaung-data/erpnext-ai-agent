from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .intent_boundary_contract import (
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_GOVERNED_ERP,
	AUTHORITY_DECISION_ALLOW_REPORT,
	AUTHORITY_DECISION_BLOCK,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
	validate_intent_boundary_contract,
)
from .intent_boundary_proposal_classifier import build_intent_boundary_proposal


USER_INTENT_BOUNDARY_CONTRACT_TYPE = "qwen_user_intent_boundary_contract"
V1_IB_RUNTIME_CONTRACT_METADATA_TYPE = "qwen_v1_ib_runtime_contract_metadata"

CATEGORY_CLARIFICATION_REQUIRED = "clarification_required"
CATEGORY_FACTUAL_ERP_QUERY = "factual_erp_query"
CATEGORY_TRUE_VISIBLE_CONTEXT_FOLLOWUP = "true_visible_context_followup"
CATEGORY_UNSUPPORTED_BUSINESS_DECISION = "recommendation_or_business_advice"

_SAFE_CONTRACT_METADATA_FIELDS = (
	"contract_version",
	"raw_message_hash",
	"normalized_message_hash",
	"clause_count",
	"factual_lookup_intent",
	"safe_followup_intent",
	"decision_intent",
	"advice_intent",
	"business_action_intent",
	"policy_boundary_intent",
	"mixed_intent_detected",
	"business_action_domain",
	"policy_domain",
	"ambiguity_status",
	"report_routing_allowed",
	"context_reuse_allowed",
	"model_reasoning_allowed",
	"final_emission_allowed",
	"required_answer_mode",
	"boundary_reason",
	"validator_status",
	"trace_redaction_status",
	"proposal_authority_source",
	"semantic_backstop_status",
	"semantic_backstop_effect",
	"authority_source",
	"authority_decision",
	"authority_blocking_reason",
	"deterministic_validator_status",
	"deterministic_validator_errors",
	"residual_text_status",
	"connector_coverage_status",
	"pronoun_reference_status",
	"validator_owned_safe_route_authority_status",
	"validator_owned_safety_proof_status",
	"validator_owned_safety_proof_blocking_reason",
	"validator_owned_raw_message_analysis_status",
	"validator_owned_raw_message_analysis_evidence_match_status",
	"analysis_execution_status",
	"analysis_execution_replay_status",
	"replayed_raw_message_safety_status",
	"replayed_raw_message_safety_final_decision",
	"replayed_raw_message_safety_evidence_match_status",
	"replayed_raw_message_safety_blocking_reason",
	"role_verification_authority_effect",
	"semantic_backstop_authority_effect",
	"lexical_evidence_authority_effect",
)

_LEGACY_METADATA_FIELDS = (
	"contract_version",
	"category",
	"required_answer_mode",
	"context_reuse_allowed",
	"report_routing_allowed",
	"boundary_reason",
)


def _safe_bool(value: Any) -> bool:
	return bool(value) is True


def _mapping(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _contract_payload(contract: Any) -> Dict[str, Any]:
	if hasattr(contract, "to_payload") and callable(contract.to_payload):
		payload = contract.to_payload()
		return _mapping(payload)
	return _mapping(contract)


def _redacted_contract_metadata(payload: Dict[str, Any]) -> Dict[str, Any]:
	return {field: payload.get(field) for field in _SAFE_CONTRACT_METADATA_FIELDS if field in payload}


def _redacted_legacy_metadata(payload: Dict[str, Any] | None) -> Dict[str, Any]:
	legacy = _mapping(payload)
	return {field: legacy.get(field) for field in _LEGACY_METADATA_FIELDS if field in legacy}


def _category_for_contract(payload: Dict[str, Any], *, report_allowed: bool, context_allowed: bool) -> str:
	if report_allowed:
		return CATEGORY_FACTUAL_ERP_QUERY
	if context_allowed:
		return CATEGORY_TRUE_VISIBLE_CONTEXT_FOLLOWUP
	if str(payload.get("required_answer_mode") or "") in {"policy_boundary", "control_boundary"}:
		return CATEGORY_UNSUPPORTED_BUSINESS_DECISION
	return CATEGORY_CLARIFICATION_REQUIRED


def _runtime_contract_hash(payload: Dict[str, Any]) -> str:
	return hash_text(
		"|".join(
			str(payload.get(field) or "")
			for field in (
				"raw_message_hash",
				"normalized_message_hash",
				"validator_status",
				"authority_decision",
				"replayed_raw_message_safety_final_decision",
				"trace_redaction_status",
			)
		)
	)


def _fail_closed_boundary(raw_message: Any, reason: str, *, error: str = "") -> Dict[str, Any]:
	normalized = normalize_message(raw_message)
	payload = {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "v1-ib-c-2-runtime",
		"raw_message_hash": hash_text(raw_message),
		"normalized_message_hash": hash_text(normalized),
		"clause_count": 0,
		"category": CATEGORY_CLARIFICATION_REQUIRED,
		"required_answer_mode": ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": False,
		"model_reasoning_allowed": False,
		"final_emission_allowed": False,
		"authority_decision": AUTHORITY_DECISION_BLOCK,
		"boundary_reason": reason,
		"validator_status": "invalid",
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"v1_ib_runtime_status": "fail_closed",
		"v1_ib_runtime_blocking_reason": reason,
		"deterministic_validator_errors": [reason],
		"runtime_exception_type": error,
	}
	payload["v1_ib_runtime_contract_hash"] = _runtime_contract_hash(payload)
	payload["v1_ib_contract_metadata"] = _redacted_contract_metadata(payload)
	return payload


def _normalize_validated_boundary(contract_payload: Dict[str, Any]) -> Dict[str, Any]:
	valid = str(contract_payload.get("validator_status") or "") == "valid"
	trace_safe = str(contract_payload.get("trace_redaction_status") or "") == TRACE_REDACTION_SAFE
	required_mode = str(contract_payload.get("required_answer_mode") or "")
	authority_decision = str(contract_payload.get("authority_decision") or "")
	replay_safe = str(contract_payload.get("replayed_raw_message_safety_final_decision") or "") == "safe"
	unsafe_or_ambiguous = any(
		_safe_bool(contract_payload.get(field))
		for field in (
			"decision_intent",
			"advice_intent",
			"business_action_intent",
			"policy_boundary_intent",
			"mixed_intent_detected",
		)
	) or str(contract_payload.get("ambiguity_status") or "none") != "none"

	report_allowed = bool(
		valid
		and trace_safe
		and replay_safe
		and required_mode == ANSWER_MODE_GOVERNED_ERP
		and authority_decision == AUTHORITY_DECISION_ALLOW_REPORT
		and _safe_bool(contract_payload.get("report_routing_allowed"))
		and not unsafe_or_ambiguous
	)
	context_allowed = bool(
		valid
		and trace_safe
		and _safe_bool(contract_payload.get("context_reuse_allowed"))
		and _safe_bool(contract_payload.get("safe_followup_intent"))
		and not unsafe_or_ambiguous
	)
	model_reasoning_allowed = bool(report_allowed and _safe_bool(contract_payload.get("model_reasoning_allowed")))
	final_emission_allowed = bool((report_allowed or context_allowed) and _safe_bool(contract_payload.get("final_emission_allowed")))

	payload = _redacted_contract_metadata(contract_payload)
	payload.update(
		{
			"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
			"category": _category_for_contract(
				contract_payload,
				report_allowed=report_allowed,
				context_allowed=context_allowed,
			),
			"required_answer_mode": required_mode or ANSWER_MODE_CLARIFICATION,
			"context_reuse_allowed": context_allowed,
			"report_routing_allowed": report_allowed,
			"model_reasoning_allowed": model_reasoning_allowed,
			"final_emission_allowed": final_emission_allowed,
			"authority_decision": authority_decision if report_allowed else AUTHORITY_DECISION_BLOCK,
			"boundary_reason": str(contract_payload.get("boundary_reason") or "v1_ib_contract_blocked_runtime_authority"),
			"v1_ib_runtime_status": "validated" if valid else "fail_closed",
			"v1_ib_runtime_blocking_reason": "" if (report_allowed or context_allowed) else str(
				contract_payload.get("authority_blocking_reason")
				or contract_payload.get("boundary_reason")
				or "v1_ib_contract_did_not_authorize_runtime_route"
			),
		}
	)
	payload["v1_ib_runtime_contract_hash"] = _runtime_contract_hash(payload)
	payload["v1_ib_contract_metadata"] = _redacted_contract_metadata(payload)
	return payload


def build_v1_ib_runtime_boundary(
	raw_message: str,
	*,
	proposal_builder: Optional[Callable[[str], Dict[str, Any]]] = build_intent_boundary_proposal,
	contract_validator: Optional[Callable[..., Any]] = validate_intent_boundary_contract,
	semantic_backstop: Optional[Dict[str, Any]] = None,
	verifier_envelope: Optional[Dict[str, Any]] = None,
	trusted_verifier_registry: Optional[Dict[str, Dict[str, Any]]] = None,
	validator_owned_safety_proof_registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
	"""Build redaction-safe V1-IB runtime authority metadata.

	This glue never interprets user intent. It only invokes the accepted
	classifier/validator path and normalizes validator-owned route flags.
	"""

	if not callable(proposal_builder):
		return _fail_closed_boundary(raw_message, "v1_ib_classifier_missing")
	if not callable(contract_validator):
		return _fail_closed_boundary(raw_message, "v1_ib_validator_missing")
	try:
		proposal = proposal_builder(raw_message)
	except Exception as exc:  # pragma: no cover - exact exception type is intentionally not authority.
		return _fail_closed_boundary(raw_message, "v1_ib_classifier_exception", error=exc.__class__.__name__)
	try:
		contract = contract_validator(
			raw_message,
			proposal,
			semantic_backstop=semantic_backstop,
			verifier_envelope=verifier_envelope,
			trusted_verifier_registry=trusted_verifier_registry,
			validator_owned_safety_proof_registry=validator_owned_safety_proof_registry,
		)
	except Exception as exc:  # pragma: no cover - exact exception type is intentionally not authority.
		return _fail_closed_boundary(raw_message, "v1_ib_validator_exception", error=exc.__class__.__name__)
	return _normalize_validated_boundary(_contract_payload(contract))


def merge_v1_ib_with_legacy_boundary(
	v1_ib_boundary: Dict[str, Any] | None,
	legacy_boundary: Dict[str, Any] | None,
) -> Dict[str, Any]:
	v1_payload = _mapping(v1_ib_boundary)
	if not v1_payload:
		v1_payload = _fail_closed_boundary("", "v1_ib_contract_missing")
	legacy_metadata = _redacted_legacy_metadata(legacy_boundary)
	merged = dict(v1_payload)
	merged["legacy_user_intent_boundary_metadata"] = legacy_metadata
	merged["runtime_authority_source"] = "v1_ib_contract_validator"

	if not legacy_metadata:
		return merged

	if merged.get("report_routing_allowed") and not bool(legacy_metadata.get("report_routing_allowed")):
		merged.update(
			{
				"category": CATEGORY_CLARIFICATION_REQUIRED,
				"required_answer_mode": ANSWER_MODE_CLARIFICATION,
				"context_reuse_allowed": False,
				"report_routing_allowed": False,
				"model_reasoning_allowed": False,
				"final_emission_allowed": False,
				"authority_decision": AUTHORITY_DECISION_BLOCK,
				"boundary_reason": "legacy_boundary_restricted_after_v1_ib_allow",
				"v1_ib_runtime_blocking_reason": "legacy_boundary_restricted_after_v1_ib_allow",
			}
		)
	if merged.get("context_reuse_allowed") and not bool(legacy_metadata.get("context_reuse_allowed")):
		merged.update(
			{
				"context_reuse_allowed": False,
				"model_reasoning_allowed": False,
				"final_emission_allowed": False,
				"authority_decision": AUTHORITY_DECISION_BLOCK,
				"boundary_reason": "legacy_context_boundary_restricted_after_v1_ib_allow",
				"v1_ib_runtime_blocking_reason": "legacy_context_boundary_restricted_after_v1_ib_allow",
			}
		)
	merged["v1_ib_runtime_contract_hash"] = _runtime_contract_hash(merged)
	merged["v1_ib_contract_metadata"] = _redacted_contract_metadata(merged)
	return merged


def v1_ib_runtime_contract_metadata(user_intent_boundary: Dict[str, Any] | None) -> Dict[str, Any]:
	payload = _mapping(user_intent_boundary)
	metadata = _redacted_contract_metadata(payload)
	metadata.update(
		{
			"type": V1_IB_RUNTIME_CONTRACT_METADATA_TYPE,
			"v1_ib_runtime_status": str(payload.get("v1_ib_runtime_status") or ""),
			"v1_ib_runtime_blocking_reason": str(payload.get("v1_ib_runtime_blocking_reason") or ""),
			"v1_ib_runtime_contract_hash": str(payload.get("v1_ib_runtime_contract_hash") or ""),
			"runtime_authority_source": str(payload.get("runtime_authority_source") or "v1_ib_contract_validator"),
		}
	)
	return metadata
