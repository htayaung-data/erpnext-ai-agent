from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List

from .contracts import (
	ExecutionPath,
	FollowUpResolution,
	InteractionContract,
	build_audit_envelope,
)


AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE = "qwen_authorized_assistant_emission_contract"

ANSWER_TYPE_BUSINESS_FACTUAL = "business_facing_factual_answer"
ANSWER_TYPE_VISIBLE_CONTEXT = "visible_context_answer"
ANSWER_TYPE_GOVERNED_REPORT = "governed_report_answer"
ANSWER_TYPE_POLICY_BOUNDARY = "policy_boundary_refusal"
ANSWER_TYPE_REASONING = "reasoning_business_consultant_answer"
ANSWER_TYPE_TRACE = "trace_debug_answer"
ANSWER_TYPE_ERROR = "error_fallback_answer"
ANSWER_TYPE_CONTROL = "control_meta_answer"

BUSINESS_ANSWER_TYPES = {
	ANSWER_TYPE_BUSINESS_FACTUAL,
	ANSWER_TYPE_VISIBLE_CONTEXT,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_REASONING,
}
POLICY_BOUNDARY_ANSWER_TYPES = {ANSWER_TYPE_POLICY_BOUNDARY}
NON_BUSINESS_ANSWER_TYPES = {ANSWER_TYPE_CONTROL, ANSWER_TYPE_ERROR, ANSWER_TYPE_TRACE}
VALID_ANSWER_TYPES = BUSINESS_ANSWER_TYPES | POLICY_BOUNDARY_ANSWER_TYPES | NON_BUSINESS_ANSWER_TYPES

PREFLIGHT_PASSED = "passed"
PREFLIGHT_BOUNDED = "bounded"
PREFLIGHT_MISSING_AUTHORITY = "missing_authority"

EMISSION_STATUS_EMITTED = "emitted"
EMISSION_STATUS_BLOCKED = "blocked"

CONTROL_AUTHORITY_SOURCES = {"control_meta", "trace_debug", "error_fallback", "non_business_control"}
REQUIRED_CONTROL_AUTHORITY_FIELDS = ("authority_source", "answer_mode", "reason")


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Iterable[Any] | None) -> List[str]:
	return [_clean_text(value) for value in (values or []) if _clean_text(value)]


def _none_like(value: Any) -> bool:
	text = _clean_text(value).lower()
	return not text or text in {"none", "[]", "null", "-"}


def _payload(value: Any) -> Dict[str, Any]:
	if hasattr(value, "to_payload"):
		try:
			return _clean_dict(value.to_payload())
		except Exception:
			return {}
	return _clean_dict(value)


def _append_pre_assistant_tool_payloads(
	*,
	session_doc: Any,
	append_tool_payload: Callable[[Any, Dict[str, Any]], None],
	pre_assistant_tool_payloads: Iterable[Dict[str, Any]] | None,
) -> None:
	for payload in pre_assistant_tool_payloads or []:
		clean_payload = _clean_dict(payload)
		if clean_payload:
			append_tool_payload(session_doc, clean_payload)


def _emission_contract(
	*,
	answer_type: str,
	emission_status: str,
	block_reason: str,
	final_answer_authority: Dict[str, Any] | None = None,
	control_meta_authority: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	final_authority = _clean_dict(final_answer_authority)
	control_authority = _clean_dict(control_meta_authority)
	preflight_status = _clean_text(final_authority.get("preflight_status"))
	if not preflight_status and control_authority:
		preflight_status = _clean_text(control_authority.get("preflight_status")) or PREFLIGHT_PASSED
	return {
		"type": AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
		"contract_version": "1.0",
		"answer_type": _clean_text(answer_type),
		"emission_status": _clean_text(emission_status),
		"emitted": emission_status == EMISSION_STATUS_EMITTED,
		"blocked": emission_status == EMISSION_STATUS_BLOCKED,
		"block_reason": _clean_text(block_reason) or "none",
		"preflight_status": preflight_status or PREFLIGHT_MISSING_AUTHORITY,
		"final_answer_authority": final_authority,
		"control_meta_authority": control_authority,
	}


def _validate_control_meta_authority(control_meta_authority: Dict[str, Any]) -> tuple[bool, str]:
	authority = _clean_dict(control_meta_authority)
	missing = [field for field in REQUIRED_CONTROL_AUTHORITY_FIELDS if not _clean_text(authority.get(field))]
	if missing:
		return False, "missing_control_authority_fields:" + ",".join(missing)
	if _clean_text(authority.get("authority_source")) not in CONTROL_AUTHORITY_SOURCES:
		return False, "unsupported_control_authority_source"
	return True, ""


def _validate_final_authority_for_answer_type(
	*,
	answer_type: str,
	final_answer_authority: Dict[str, Any],
) -> tuple[bool, str]:
	authority = _clean_dict(final_answer_authority)
	if not bool(authority.get("authority_complete")):
		return False, "final_answer_authority_incomplete"
	preflight_status = _clean_text(authority.get("preflight_status"))
	policy_boundary = _clean_text(authority.get("policy_boundary"))
	authority_source = _clean_text(authority.get("authority_source"))
	if answer_type in BUSINESS_ANSWER_TYPES:
		if preflight_status == PREFLIGHT_PASSED:
			return True, ""
		if preflight_status == PREFLIGHT_BOUNDED:
			return False, "business_answer_bounded_preflight_requires_policy_boundary_answer_type"
		return False, "business_answer_preflight_not_allowed"
	if answer_type in POLICY_BOUNDARY_ANSWER_TYPES:
		if preflight_status != PREFLIGHT_BOUNDED:
			return False, "policy_boundary_preflight_not_bounded"
		if _none_like(policy_boundary):
			return False, "policy_boundary_missing"
		if authority_source not in {
			"policy_boundary",
			"visible_rendered_table",
			"governed_artifact",
			"visible_context_resolution",
		}:
			return False, "policy_boundary_authority_source_not_allowed"
		return True, ""
	return False, "unsupported_business_authority_answer_type"


@dataclass(frozen=True)
class AuthorizedEmissionResult:
	emitted: bool
	blocked: bool
	answer_type: str
	preflight_status: str
	block_reason: str
	final_answer_authority: Dict[str, Any]
	control_meta_authority: Dict[str, Any]
	emission_contract: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return {
			"emitted": bool(self.emitted),
			"blocked": bool(self.blocked),
			"answer_type": self.answer_type,
			"preflight_status": self.preflight_status,
			"block_reason": self.block_reason,
			"final_answer_authority": dict(self.final_answer_authority),
			"control_meta_authority": dict(self.control_meta_authority),
			"emission_contract": dict(self.emission_contract),
		}


def _blocked_result(
	*,
	answer_type: str,
	block_reason: str,
	append_tool_payload: Callable[[Any, Dict[str, Any]], None] | None,
	session_doc: Any,
	final_answer_authority: Dict[str, Any] | None = None,
	control_meta_authority: Dict[str, Any] | None = None,
) -> AuthorizedEmissionResult:
	final_authority = _clean_dict(final_answer_authority)
	control_authority = _clean_dict(control_meta_authority)
	contract = _emission_contract(
		answer_type=answer_type,
		emission_status=EMISSION_STATUS_BLOCKED,
		block_reason=block_reason,
		final_answer_authority=final_authority,
		control_meta_authority=control_authority,
	)
	if callable(append_tool_payload):
		append_tool_payload(session_doc, contract)
	return AuthorizedEmissionResult(
		emitted=False,
		blocked=True,
		answer_type=answer_type,
		preflight_status=_clean_text(contract.get("preflight_status")) or PREFLIGHT_MISSING_AUTHORITY,
		block_reason=_clean_text(block_reason),
		final_answer_authority=final_authority,
		control_meta_authority=control_authority,
		emission_contract=contract,
	)


def emit_authorized_assistant_answer(
	*,
	session_doc: Any,
	answer_text: str,
	answer_type: str,
	append_message: Callable[[Any, str, str], None],
	append_tool_payload: Callable[[Any, Dict[str, Any]], None],
	assistant_text_payload: Callable[[str], Any],
	interaction_contract: InteractionContract | Dict[str, Any] | None = None,
	followup_resolution: FollowUpResolution | Dict[str, Any] | None = None,
	execution_path: ExecutionPath | Dict[str, Any] | None = None,
	runtime_trace_payload: Dict[str, Any] | None = None,
	grounded_turn_context: Dict[str, Any] | None = None,
	authority_context: Dict[str, Any] | None = None,
	control_meta_authority: Dict[str, Any] | None = None,
	pre_assistant_tool_payloads: Iterable[Dict[str, Any]] | None = None,
) -> AuthorizedEmissionResult:
	"""Validate final-answer authority before appending an assistant answer.

	This helper is intentionally above the low-level append layer because it
	needs answer classification and authority context before any user-visible
	assistant message is written.
	"""
	normalized_answer_type = _clean_text(answer_type)
	if normalized_answer_type not in VALID_ANSWER_TYPES:
		return _blocked_result(
			answer_type=normalized_answer_type or "unknown",
			block_reason="unsupported_answer_type",
			append_tool_payload=append_tool_payload,
			session_doc=session_doc,
		)
	if not _clean_text(answer_text):
		return _blocked_result(
			answer_type=normalized_answer_type,
			block_reason="answer_text_missing",
			append_tool_payload=append_tool_payload,
			session_doc=session_doc,
		)
	if normalized_answer_type in NON_BUSINESS_ANSWER_TYPES:
		control_authority = _clean_dict(control_meta_authority)
		ok, reason = _validate_control_meta_authority(control_authority)
		if not ok:
			return _blocked_result(
				answer_type=normalized_answer_type,
				block_reason=reason,
				append_tool_payload=append_tool_payload,
				session_doc=session_doc,
				control_meta_authority=control_authority,
			)
		contract = _emission_contract(
			answer_type=normalized_answer_type,
			emission_status=EMISSION_STATUS_EMITTED,
			block_reason="none",
			control_meta_authority=control_authority,
		)
		_append_pre_assistant_tool_payloads(
			session_doc=session_doc,
			append_tool_payload=append_tool_payload,
			pre_assistant_tool_payloads=pre_assistant_tool_payloads,
		)
		append_tool_payload(session_doc, contract)
		append_message(session_doc, "assistant", assistant_text_payload(answer_text))
		return AuthorizedEmissionResult(
			emitted=True,
			blocked=False,
			answer_type=normalized_answer_type,
			preflight_status=_clean_text(contract.get("preflight_status")) or PREFLIGHT_PASSED,
			block_reason="none",
			final_answer_authority={},
			control_meta_authority=control_authority,
			emission_contract=contract,
		)

	if interaction_contract is None or followup_resolution is None or execution_path is None:
		return _blocked_result(
			answer_type=normalized_answer_type,
			block_reason="missing_authority_contract_inputs",
			append_tool_payload=append_tool_payload,
			session_doc=session_doc,
		)

	audit_payload = build_audit_envelope(
		interaction_contract=interaction_contract,  # type: ignore[arg-type]
		followup_resolution=followup_resolution,  # type: ignore[arg-type]
		execution_path=execution_path,  # type: ignore[arg-type]
		runtime_trace_payload=_clean_dict(runtime_trace_payload),
		grounded_turn_context=_clean_dict(grounded_turn_context),
		answer_text=answer_text,
		authority_context=_clean_dict(authority_context),
	).to_payload()
	_sanitize_user_intent_veto_audit_payload(audit_payload, runtime_trace_payload)
	final_authority = _clean_dict(audit_payload.get("final_answer_authority"))
	ok, reason = _validate_final_authority_for_answer_type(
		answer_type=normalized_answer_type,
		final_answer_authority=final_authority,
	)
	if not ok:
		return _blocked_result(
			answer_type=normalized_answer_type,
			block_reason=reason,
			append_tool_payload=append_tool_payload,
			session_doc=session_doc,
			final_answer_authority=final_authority,
		)
	contract = _emission_contract(
		answer_type=normalized_answer_type,
		emission_status=EMISSION_STATUS_EMITTED,
		block_reason="none",
		final_answer_authority=final_authority,
	)
	_append_pre_assistant_tool_payloads(
		session_doc=session_doc,
		append_tool_payload=append_tool_payload,
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	append_tool_payload(session_doc, audit_payload)
	append_tool_payload(session_doc, contract)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	return AuthorizedEmissionResult(
		emitted=True,
		blocked=False,
		answer_type=normalized_answer_type,
		preflight_status=_clean_text(final_authority.get("preflight_status")),
		block_reason="none",
		final_answer_authority=final_authority,
		control_meta_authority={},
		emission_contract=contract,
	)


def _sanitize_user_intent_veto_audit_payload(audit_payload: Dict[str, Any], runtime_trace_payload: Dict[str, Any]) -> None:
	if not _clean_dict(runtime_trace_payload).get("user_intent_final_emission_veto"):
		return
	for selected_answer_key in (
		"answer_text",
		"rows",
		"artifact",
		"rendered",
		"narrative",
		"grounded_evidence",
	):
		audit_payload.pop(selected_answer_key, None)


USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE = "qwen_user_intent_final_emission_veto_contract"
USER_INTENT_BOUNDARY_CONTRACT_TYPE = "qwen_user_intent_boundary_contract"


def _interaction_raw_message_for_user_intent_veto(interaction_contract: InteractionContract | Dict[str, Any] | None) -> str:
	if isinstance(interaction_contract, dict):
		return _clean_text(interaction_contract.get("raw_message"))
	return _clean_text(getattr(interaction_contract, "raw_message", ""))


def _user_intent_boundary_matches_current_message(
	user_intent_boundary: Dict[str, Any],
	raw_message: str,
) -> bool:
	if not raw_message:
		return False
	if _clean_text(user_intent_boundary.get("trace_redaction_status")) != "safe":
		return False
	from .intent_boundary_contract import hash_text, normalize_message

	normalized_message = normalize_message(raw_message)
	return (
		_clean_text(user_intent_boundary.get("raw_message_hash")) == hash_text(raw_message)
		and _clean_text(user_intent_boundary.get("normalized_message_hash")) == hash_text(normalized_message)
	)


def _user_intent_boundary_for_final_emission_veto(
	*,
	interaction_contract: InteractionContract | Dict[str, Any] | None,
	runtime_trace_payload: Dict[str, Any] | None,
	authority_context: Dict[str, Any] | None,
	pre_assistant_tool_payloads: Iterable[Dict[str, Any]] | None,
) -> Dict[str, Any]:
	raw_message = _interaction_raw_message_for_user_intent_veto(interaction_contract)
	for payload in [
		_clean_dict(authority_context),
		_clean_dict(runtime_trace_payload),
		*[_clean_dict(item) for item in (pre_assistant_tool_payloads or [])],
	]:
		if not payload:
			continue
		for candidate in (
			payload.get("user_intent_boundary"),
			payload.get("user_intent_boundary_contract"),
			payload,
		):
			clean_candidate = _clean_dict(candidate)
			if clean_candidate.get("type") == USER_INTENT_BOUNDARY_CONTRACT_TYPE:
				if _user_intent_boundary_matches_current_message(clean_candidate, raw_message):
					return clean_candidate
	from .intent_boundary_runtime_integration import build_v1_ib_runtime_boundary, merge_v1_ib_with_legacy_boundary
	from .user_intent_boundary import build_user_intent_boundary_contract

	legacy_boundary = build_user_intent_boundary_contract(raw_message) if raw_message else {}
	return merge_v1_ib_with_legacy_boundary(
		build_v1_ib_runtime_boundary(raw_message),
		legacy_boundary,
	)


def _user_intent_final_emission_veto_required(*, answer_type: str, user_intent_boundary: Dict[str, Any]) -> bool:
	if answer_type not in BUSINESS_ANSWER_TYPES or not user_intent_boundary:
		return False
	required_mode = _clean_text(user_intent_boundary.get("required_answer_mode"))
	if required_mode == "governed_erp_answer":
		if answer_type == ANSWER_TYPE_VISIBLE_CONTEXT:
			return not bool(user_intent_boundary.get("context_reuse_allowed"))
		return not bool(user_intent_boundary.get("report_routing_allowed"))
	if answer_type == ANSWER_TYPE_VISIBLE_CONTEXT and not bool(user_intent_boundary.get("context_reuse_allowed")):
		return True
	return not bool(user_intent_boundary.get("report_routing_allowed"))


def _user_intent_final_emission_veto_answer_text(user_intent_boundary: Dict[str, Any]) -> str:
	required_mode = _clean_text(user_intent_boundary.get("required_answer_mode"))
	if required_mode == "control_boundary":
		return (
			"I can't create, change, hide, approve, submit, or remove ERP records from chat. "
			"I can help you inspect the relevant ERP facts instead."
		)
	if required_mode == "policy_boundary":
		return (
			"I can help with factual ERP information, but I can't provide advice, predictions, "
			"legal guidance, or decisions from this prompt. Please ask for the specific ERP facts "
			"you want to review."
		)
	return (
		"I need a bit more detail before I can answer safely. Please ask for a specific ERP fact, "
		"report, customer, supplier, invoice, product, period, or metric."
	)


def _user_intent_final_emission_veto_payload(
	*,
	selected_answer_type: str,
	emitted_answer_type: str,
	user_intent_boundary: Dict[str, Any],
) -> Dict[str, Any]:
	return {
		"type": USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE,
		"contract_version": "1.0",
		"veto_applied": True,
		"selected_answer_type": _clean_text(selected_answer_type),
		"emitted_answer_type": _clean_text(emitted_answer_type),
		"category": _clean_text(user_intent_boundary.get("category")),
		"required_answer_mode": _clean_text(user_intent_boundary.get("required_answer_mode")),
		"context_reuse_allowed": bool(user_intent_boundary.get("context_reuse_allowed")),
		"report_routing_allowed": bool(user_intent_boundary.get("report_routing_allowed")),
		"boundary_reason": _clean_text(user_intent_boundary.get("boundary_reason")),
		"user_intent_boundary": dict(user_intent_boundary),
	}


def _user_intent_policy_boundary_payload(
	*,
	user_intent_boundary: Dict[str, Any],
	interaction_contract: InteractionContract | Dict[str, Any] | None,
) -> Dict[str, Any]:
	payload = dict(user_intent_boundary)
	payload.update(
		{
			"request_id": _clean_text(
				interaction_contract.get("request_id") if isinstance(interaction_contract, dict) else getattr(interaction_contract, "request_id", "")
			),
			"session_id": _clean_text(
				interaction_contract.get("session_id") if isinstance(interaction_contract, dict) else getattr(interaction_contract, "session_id", "")
			),
			"final_lane": "user_intent_boundary_final_emission_veto",
			"knowledge_coverage_state": _clean_text(user_intent_boundary.get("category")) or "user_intent_boundary",
			"user_response_mode": "policy_boundary",
			"safe_next_action": "respond_with_final_emission_veto_boundary",
			"boundary_status": _clean_text(user_intent_boundary.get("boundary_reason")) or "user_intent_boundary_final_emission_veto",
		}
	)
	return payload


_emit_authorized_assistant_answer_without_user_intent_veto = emit_authorized_assistant_answer


def emit_authorized_assistant_answer(
	*,
	session_doc: Any,
	answer_text: str,
	answer_type: str,
	append_message: Callable[[Any, str, str], None],
	append_tool_payload: Callable[[Any, Dict[str, Any]], None],
	assistant_text_payload: Callable[[str], Any],
	interaction_contract: InteractionContract | Dict[str, Any] | None = None,
	followup_resolution: FollowUpResolution | Dict[str, Any] | None = None,
	execution_path: ExecutionPath | Dict[str, Any] | None = None,
	runtime_trace_payload: Dict[str, Any] | None = None,
	grounded_turn_context: Dict[str, Any] | None = None,
	authority_context: Dict[str, Any] | None = None,
	control_meta_authority: Dict[str, Any] | None = None,
	pre_assistant_tool_payloads: Iterable[Dict[str, Any]] | None = None,
) -> AuthorizedEmissionResult:
	pre_assistant_payload_list = list(pre_assistant_tool_payloads or [])
	normalized_answer_type = _clean_text(answer_type)
	user_intent_boundary = _user_intent_boundary_for_final_emission_veto(
		interaction_contract=interaction_contract,
		runtime_trace_payload=runtime_trace_payload,
		authority_context=authority_context,
		pre_assistant_tool_payloads=pre_assistant_payload_list,
	)
	if not _user_intent_final_emission_veto_required(
		answer_type=normalized_answer_type,
		user_intent_boundary=user_intent_boundary,
	):
		return _emit_authorized_assistant_answer_without_user_intent_veto(
			session_doc=session_doc,
			answer_text=answer_text,
			answer_type=answer_type,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=runtime_trace_payload,
			grounded_turn_context=grounded_turn_context,
			authority_context=authority_context,
			control_meta_authority=control_meta_authority,
			pre_assistant_tool_payloads=pre_assistant_payload_list,
		)

	required_mode = _clean_text(user_intent_boundary.get("required_answer_mode"))
	safe_answer_text = _user_intent_final_emission_veto_answer_text(user_intent_boundary)
	emitted_answer_type = ANSWER_TYPE_POLICY_BOUNDARY if required_mode == "policy_boundary" else ANSWER_TYPE_CONTROL
	veto_payload = _user_intent_final_emission_veto_payload(
		selected_answer_type=normalized_answer_type,
		emitted_answer_type=emitted_answer_type,
		user_intent_boundary=user_intent_boundary,
	)
	veto_pre_payloads = [
		dict(user_intent_boundary),
		veto_payload,
	]
	if emitted_answer_type == ANSWER_TYPE_POLICY_BOUNDARY:
		return _emit_authorized_assistant_answer_without_user_intent_veto(
			session_doc=session_doc,
			answer_text=safe_answer_text,
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={
				"user_intent_final_emission_veto": veto_payload,
				"selected_answer_payloads_redacted": True,
			},
			grounded_turn_context={},
			authority_context={
				"knowledge_boundary": _user_intent_policy_boundary_payload(
					user_intent_boundary=user_intent_boundary,
					interaction_contract=interaction_contract,
				),
				"user_intent_boundary": dict(user_intent_boundary),
				"user_intent_final_emission_veto": veto_payload,
			},
			pre_assistant_tool_payloads=veto_pre_payloads,
		)
	control_answer_mode = (
		"user_intent_final_emission_control_boundary"
		if required_mode == "control_boundary"
		else "user_intent_final_emission_clarification"
	)
	return _emit_authorized_assistant_answer_without_user_intent_veto(
		session_doc=session_doc,
		answer_text=safe_answer_text,
		answer_type=ANSWER_TYPE_CONTROL,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		control_meta_authority={
			"authority_source": "control_meta",
			"answer_mode": control_answer_mode,
			"reason": _clean_text(user_intent_boundary.get("boundary_reason")) or "User intent boundary vetoed final business emission.",
			"preflight_status": PREFLIGHT_PASSED,
		},
		pre_assistant_tool_payloads=veto_pre_payloads,
	)
