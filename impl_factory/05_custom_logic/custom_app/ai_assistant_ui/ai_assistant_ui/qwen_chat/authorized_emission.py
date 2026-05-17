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
