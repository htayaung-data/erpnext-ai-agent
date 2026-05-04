from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_reasoning_policy import (
	render_business_reasoning_policy_boundary_answer,
)
from ai_assistant_ui.qwen_chat.business_language_guards import (
	looks_like_predictive_guarantee_claim,
	looks_like_unsupported_operational_inference_claim,
)
from ai_assistant_ui.qwen_chat.contracts import (
	build_erp_business_reasoning_contract,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_reasoning_render,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


@dataclass(frozen=True)
class ERPBusinessReasoningExecutionResult:
	status: str
	answer_text: str = ""
	reasoning_contract: Dict[str, Any] = field(default_factory=dict)
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_erp_business_reasoning_execution",
			"contract_version": "1.0",
			"status": self.status,
			"answer_text": self.answer_text,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"reasoning_contract": dict(self.reasoning_contract or {}),
			"agent_meta": dict(self.agent_meta or {}),
		}


def _site_name() -> str:
	if frappe is None:
		return ""
	return str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()


def _build_reasoning_context(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
	prior_reasoning_contract: Dict[str, Any] | None = None,
	prior_answer_text: str = "",
) -> Dict[str, Any]:
	intent = dict(semantic_activation_result.get("intent") or {})
	grounding_summary = dict(activation_contract.get("grounding_summary") or {})
	grounded_turn = dict(latest_grounded_turn or {})
	family_artifact = dict(latest_family_artifact or {})
	assistant_payload = dict(latest_assistant_payload or {})
	grounded_findings: List[str] = []
	for row in list(grounded_turn.get("table_rows") or [])[:5]:
		if not isinstance(row, dict):
			continue
		pairs = [
			f"{str(key or '').strip()}: {str(value or '').strip()}"
			for key, value in row.items()
			if str(key or "").strip() and str(value or "").strip()
		]
		if pairs:
			grounded_findings.append("; ".join(pairs[:4]))
	report_name = str(activation_contract.get("grounded_source_name") or grounded_turn.get("source_name") or "").strip()
	if report_name:
		grounding_summary.setdefault("report_name", report_name)
	title = str(assistant_payload.get("title") or "").strip()
	if title:
		grounding_summary.setdefault("latest_assistant_title", title)
	context = {
		"reasoning_type": str(intent.get("reasoning_type") or "").strip(),
		"detail_level": str(intent.get("detail_level") or "default").strip() or "default",
		"presentation_style": str(intent.get("presentation_style") or "default").strip() or "default",
		"bounded_domain": "erp_business_reasoning",
		"recommendation_allowed": bool(activation_contract.get("recommendation_allowed")),
		"recommendation_policy_basis": [
			str(value or "").strip()
			for value in (activation_contract.get("recommendation_policy_basis") or [])
			if str(value or "").strip()
		],
		"grounding_summary": grounding_summary,
		"grounded_source": {
			"source_kind": str(activation_contract.get("grounded_source_kind") or "").strip(),
			"source_name": report_name,
			"family_id": str(activation_contract.get("grounded_family_id") or family_artifact.get("family_id") or "").strip(),
			"artifact_type": str(activation_contract.get("grounded_artifact_type") or family_artifact.get("artifact_type") or "").strip(),
			"source_reports": [
				str(value or "").strip()
				for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
				if str(value or "").strip()
			],
			"source_report_count": int(
				len(
					[
						str(value or "").strip()
						for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
						if str(value or "").strip()
					]
				)
			),
			"composite_grounding": bool(
				len(
					[
						str(value or "").strip()
						for value in (activation_contract.get("grounded_source_reports") or family_artifact.get("source_reports") or [])
						if str(value or "").strip()
					]
				)
				> 1
			),
			"capability_id": str(activation_contract.get("grounded_capability_id") or family_artifact.get("capability_id") or "").strip(),
		},
		"grounded_findings": grounded_findings,
		"table_schema": [str(value or "").strip() for value in (grounded_turn.get("returned_schema") or []) if str(value or "").strip()],
		"row_count": int(grounded_turn.get("row_count") or 0),
		"presentation_preferences": dict(presentation_preferences or {}),
	}
	prior_contract = dict(prior_reasoning_contract or {})
	if prior_contract:
		context["prior_reasoning"] = {
			"reasoning_type": str(prior_contract.get("reasoning_type") or "").strip(),
			"reason": str(prior_contract.get("reason") or "").strip(),
			"supported_claims": [dict(item) for item in (prior_contract.get("supported_claims") or []) if isinstance(item, dict)],
			"recommendations": [dict(item) for item in (prior_contract.get("recommendations") or []) if isinstance(item, dict)],
			"speculation_flags": [str(item or "").strip() for item in (prior_contract.get("speculation_flags") or []) if str(item or "").strip()],
			"answer_text": str(prior_answer_text or "").strip(),
		}
	return context


def build_reasoning_boundary_answer(
	*,
	execution_result: ERPBusinessReasoningExecutionResult,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
) -> str:
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	source_name = str(activation_contract.get("grounded_source_name") or "").strip()
	source_label = source_name or "the answer above"
	grounding_gaps = {
		str(item or "").strip()
		for item in ((execution_result.reasoning_contract or {}).get("grounding_gaps") or [])
		if str(item or "").strip()
	}
	if execution_result.status == "insufficient_grounding" and "predictive_guarantee_requires_governed_policy" in grounding_gaps:
		return (
			f"I can't answer it safely as a guarantee or prediction from {source_label}. "
			"The current ERP data can support facts and explanations, but it does not include an approved prediction policy, "
			"payment-commitment evidence, or collection/default model needed to say who will pay or default. "
			"Please ask for the current ERP facts, aging breakdown, or an approved prediction or collections policy first."
		)
	if execution_result.status == "insufficient_grounding" and "unsupported_operational_inference_requires_governed_evidence" in grounding_gaps:
		return (
			f"I can't answer that safely as a causal or subjective operational inference from {source_label}. "
			"The current ERP data can show recorded facts, but it does not include customer sentiment, complaint, dispute, "
			"or delay-reason evidence needed to infer dissatisfaction or intent. Please ask for the recorded fields, "
			"or use a complaint, dispute, or delay-reason view first."
		)
	grounding_summary = activation_contract.get("grounding_summary") if isinstance(activation_contract.get("grounding_summary"), dict) else {}
	policy_boundary_answer = render_business_reasoning_policy_boundary_answer(
		dict(grounding_summary.get("business_reasoning_authority_policy") or {})
	)
	if policy_boundary_answer:
		return policy_boundary_answer
	if execution_result.status == "insufficient_grounding":
		if (
			reasoning_type in {"recommendation", "continuation_detail"}
			and not bool(activation_contract.get("recommendation_allowed"))
		):
			return (
				f"I can explain {source_label}, but I can't safely give management recommendations from this result alone. "
				"This is a detailed operational view, so recommendations should come from an approved summary or analysis view first."
			)
		if "prior_reasoning_source_mismatch" in grounding_gaps or "prior_reasoning_report_mismatch" in grounding_gaps:
			return (
				"I can't safely continue that prior recommendation because the current ERP context no longer matches the original analysis. "
				"Please return to the original analysis or ask for a fresh summary before continuing."
			)
		return (
			f"I couldn't safely complete that ERP explanation from {source_label} without going beyond the available data. "
			"Please ask for a broader summary or reframe the question around the current result."
		)
	if execution_result.status in {"invalid_payload", "runtime_error"}:
		return (
			f"I stopped rather than guess because I couldn't safely generate a bounded reasoning answer from {source_label} just now. "
			"Please try the follow-up again or ask for a summary view."
		)
	return (
		f"I couldn't safely continue reasoning from {source_label}. "
		"Please ask for a summary view or a narrower explanation request."
	)


def _continuation_compatible(
	*,
	activation_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any],
) -> tuple[bool, List[str]]:
	gaps: List[str] = []
	prior_contract = dict(prior_reasoning_contract or {})
	if not prior_contract:
		gaps.append("missing_prior_reasoning_contract")
		return False, gaps
	if not bool(prior_contract.get("allowed_to_answer")):
		gaps.append("prior_reasoning_not_answerable")
	if not bool(prior_contract.get("grounding_sufficient")):
		gaps.append("prior_reasoning_insufficient_grounding")
	prior_source_request_id = str(prior_contract.get("grounding_source_request_id") or "").strip()
	current_source_request_id = str(
		activation_contract.get("grounded_source_request_id")
		or latest_grounded_turn.get("trace_request_id")
		or latest_grounded_turn.get("request_id")
		or ""
	).strip()
	if prior_source_request_id and current_source_request_id and prior_source_request_id != current_source_request_id:
		gaps.append("prior_reasoning_source_mismatch")
	prior_family_id = str(prior_contract.get("grounding_family_id") or "").strip()
	current_family_id = str(
		activation_contract.get("grounded_family_id")
		or latest_grounded_turn.get("artifact_family_id")
		or ""
	).strip()
	if prior_family_id and current_family_id and prior_family_id != current_family_id:
		gaps.append("prior_reasoning_family_mismatch")
	prior_reports = {
		str(value or "").strip()
		for value in (prior_contract.get("grounding_source_reports") or [])
		if str(value or "").strip()
	}
	current_reports = {
		str(value or "").strip()
		for value in (activation_contract.get("grounded_source_reports") or latest_grounded_turn.get("artifact_source_reports") or [])
		if str(value or "").strip()
	}
	if prior_reports and current_reports and prior_reports != current_reports:
		gaps.append("prior_reasoning_report_mismatch")
	return (not gaps, gaps)


def _answer_text_is_incomplete(answer_text: str) -> bool:
	text = str(answer_text or "").strip()
	if not text:
		return True
	# A dangling lead-in is not an acceptable fulfilled reasoning answer.
	if text.endswith(":"):
		return True
	return False


def _grounding_sufficient(
	*,
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any] | None = None,
) -> tuple[bool, List[str]]:
	gaps: List[str] = []
	if str(activation_contract.get("activation_state") or "").strip() != "eligible":
		gaps.append("reasoning_not_eligible")
	if str(semantic_activation_result.get("status") or "").strip() != "accepted":
		gaps.append("semantic_activation_not_accepted")
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	if not reasoning_type:
		gaps.append("missing_reasoning_type")
	allowed_types = {
		str(value or "").strip()
		for value in (activation_contract.get("allowed_reasoning_types") or [])
		if str(value or "").strip()
	}
	if reasoning_type and reasoning_type not in allowed_types:
		gaps.append("reasoning_type_not_allowed")
	if reasoning_type == "recommendation" and not bool(activation_contract.get("recommendation_allowed")):
		gaps.append("recommendation_policy_not_allowed")
	grounding_summary = activation_contract.get("grounding_summary") if isinstance(activation_contract.get("grounding_summary"), dict) else {}
	authority_policy = grounding_summary.get("business_reasoning_authority_policy")
	if isinstance(authority_policy, dict) and str(authority_policy.get("policy_state") or "").strip() == "blocked":
		gaps.append("business_reasoning_policy_blocked_variation")
	if not bool(latest_grounded_turn.get("grounded")):
		gaps.append("missing_grounded_turn")
	if reasoning_type == "continuation_detail":
		compatible, continuation_gaps = _continuation_compatible(
			activation_contract=activation_contract,
			latest_grounded_turn=latest_grounded_turn,
			prior_reasoning_contract=dict(prior_reasoning_contract or {}),
		)
		if not compatible:
			gaps.extend(continuation_gaps)
	return (not gaps, gaps)


def _insufficient_grounding_result(
	*,
	request_id: str,
	session_id: str,
	reasoning_type: str,
	activation_contract: Dict[str, Any],
	grounding_gaps: List[str],
	reason: str,
) -> ERPBusinessReasoningExecutionResult:
	contract = build_erp_business_reasoning_contract(
		request_id=request_id,
		session_id=session_id,
		reasoning_type=reasoning_type,
		grounding_source_request_id=str(activation_contract.get("grounded_source_request_id") or "").strip(),
		grounding_source_kind=str(activation_contract.get("grounded_source_kind") or "").strip(),
		grounding_family_id=str(activation_contract.get("grounded_family_id") or "").strip(),
		grounding_artifact_type=str(activation_contract.get("grounded_artifact_type") or "").strip(),
		grounding_source_reports=list(activation_contract.get("grounded_source_reports") or []),
		grounding_sufficient=False,
		grounding_gaps=grounding_gaps,
		bounded_domain="erp_business_reasoning",
		reasoning_scope="grounded_only",
		supported_claims=[],
		recommendations=[],
		speculation_flags=[],
		allowed_to_answer=False,
		reason=reason,
		confidence=0.0,
	)
	return ERPBusinessReasoningExecutionResult(
		status="insufficient_grounding",
		reasoning_contract=contract.to_payload(),
		validation_error=reason,
	)


def _validate_runtime_payload(
	*,
	payload: Dict[str, Any],
	reasoning_type: str,
	activation_contract: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
) -> tuple[bool, str]:
	if not isinstance(payload, dict):
		return False, "Runtime reasoning renderer returned invalid payload."
	answer_text = str(payload.get("answer_text") or "").strip()
	if _answer_text_is_incomplete(answer_text):
		return False, "Runtime reasoning renderer returned no answer text."
	supported_claims = payload.get("supported_claims") or []
	if not isinstance(supported_claims, list):
		return False, "Runtime reasoning renderer returned invalid supported_claims."
	recommendations = payload.get("recommendations") or []
	if not isinstance(recommendations, list):
		return False, "Runtime reasoning renderer returned invalid recommendations."
	speculation_flags = payload.get("speculation_flags") or []
	if not isinstance(speculation_flags, list):
		return False, "Runtime reasoning renderer returned invalid speculation_flags."
	supported_claim_count = len(supported_claims)
	recommendation_allowed = bool(activation_contract.get("recommendation_allowed"))
	if recommendations and not recommendation_allowed:
		return False, "Runtime reasoning renderer returned recommendations outside the governed recommendation policy."
	if str(reasoning_type or "").strip() in {"interpretation", "explanation"} and recommendations:
		return False, "Interpretation/explanation reasoning returned recommendations outside the allowed reasoning scope."
	if str(reasoning_type or "").strip() in {"recommendation", "continuation_detail"}:
		if str(reasoning_type or "").strip() == "recommendation" and not recommendations:
			return False, "Runtime reasoning renderer returned recommendation reasoning without governed recommendations."
		if str(reasoning_type or "").strip() == "continuation_detail" and not supported_claims and not recommendations:
			return False, "Runtime reasoning renderer returned continuation detail without substantive grounded content."
		for item in recommendations:
			if not isinstance(item, dict):
				return False, "Runtime reasoning renderer returned invalid recommendation item."
			action = str(item.get("action") or "").strip()
			rationale = str(item.get("rationale") or "").strip()
			basis_claim_refs = item.get("basis_claim_refs") or []
			if not action or not rationale:
				return False, "Runtime reasoning renderer returned recommendation without action/rationale."
			if not isinstance(basis_claim_refs, list) or not basis_claim_refs:
				return False, "Runtime reasoning renderer returned recommendation without basis_claim_refs."
			for ref in basis_claim_refs:
				if not isinstance(ref, int):
					return False, "Runtime reasoning renderer returned non-integer basis_claim_refs."
				if ref < 0 or ref >= supported_claim_count:
					return False, "Runtime reasoning renderer returned out-of-range basis_claim_refs."
	prefs = dict(presentation_preferences or {})
	if bool(prefs.get("bullet")) and not re.search(r"(^|\n)\s*[-•]\s+", answer_text):
		return False, "Runtime reasoning renderer did not honor requested bullet presentation."
	return True, ""


def _sanitize_runtime_payload(
	*,
	payload: Dict[str, Any],
	reasoning_type: str,
	presentation_preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	out = dict(payload or {})
	if str(reasoning_type or "").strip() in {"interpretation", "explanation"}:
		out["recommendations"] = []
	prefs = dict(presentation_preferences or {})
	answer_text = str(out.get("answer_text") or "").strip()
	if bool(prefs.get("bullet")) and not re.search(r"(^|\n)\s*[-•]\s+", answer_text):
		recommendations = [dict(item) for item in (out.get("recommendations") or []) if isinstance(item, dict)]
		supported_claims = [dict(item) for item in (out.get("supported_claims") or []) if isinstance(item, dict)]
		bullets: List[str] = []
		if str(reasoning_type or "").strip() in {"recommendation", "continuation_detail"} and recommendations:
			for item in recommendations:
				action = str(item.get("action") or "").strip()
				rationale = str(item.get("rationale") or "").strip()
				if action and rationale:
					bullets.append(f"- {action} {rationale}")
				elif action:
					bullets.append(f"- {action}")
		elif supported_claims:
			for item in supported_claims:
				claim = str(item.get("claim") or "").strip()
				support = str(item.get("support") or "").strip()
				if claim and support:
					bullets.append(f"- {claim} {support}")
				elif claim:
					bullets.append(f"- {claim}")
		if bullets:
			out["answer_text"] = "\n".join(bullets)
	return out


def execute_erp_business_reasoning(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	activation_contract: Dict[str, Any],
	semantic_activation_result: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	presentation_preferences: Dict[str, Any] | None = None,
	prior_reasoning_contract: Dict[str, Any] | None = None,
	prior_answer_text: str = "",
) -> ERPBusinessReasoningExecutionResult:
	grounding_sufficient, grounding_gaps = _grounding_sufficient(
		activation_contract=activation_contract,
		semantic_activation_result=semantic_activation_result,
		latest_grounded_turn=latest_grounded_turn,
		prior_reasoning_contract=prior_reasoning_contract,
	)
	intent = dict(semantic_activation_result.get("intent") or {})
	reasoning_type = str(intent.get("reasoning_type") or "").strip()
	if not grounding_sufficient:
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=grounding_gaps,
			reason="Grounding is insufficient for ERP business reasoning execution.",
		)
	if looks_like_predictive_guarantee_claim(message):
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=["predictive_guarantee_requires_governed_policy"],
			reason="Predictive guarantees require an approved governed prediction or collection policy.",
		)
	if looks_like_unsupported_operational_inference_claim(message):
		return _insufficient_grounding_result(
			request_id=request_id,
			session_id=session_id,
			reasoning_type=reasoning_type,
			activation_contract=activation_contract,
			grounding_gaps=["unsupported_operational_inference_requires_governed_evidence"],
			reason="Causal or subjective operational inference requires governed complaint, dispute, sentiment, or delay-reason evidence.",
		)

	context = _build_reasoning_context(
		activation_contract=activation_contract,
		semantic_activation_result=semantic_activation_result,
		latest_grounded_turn=latest_grounded_turn,
		latest_family_artifact=latest_family_artifact,
		latest_assistant_payload=latest_assistant_payload,
		presentation_preferences=presentation_preferences,
		prior_reasoning_contract=prior_reasoning_contract,
		prior_answer_text=prior_answer_text,
	)
	try:
		data = call_qwen_runtime_reasoning_render(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=_site_name(),
			message=message,
			recent_messages=recent_messages,
			reasoning_context=context,
		)
	except QwenRuntimeClientError as exc:
		return ERPBusinessReasoningExecutionResult(
			status="runtime_error",
			runtime_error=str(exc),
		)

	payload = dict(data.get("payload") or {})
	payload = _sanitize_runtime_payload(
		payload=payload,
		reasoning_type=reasoning_type,
		presentation_preferences=presentation_preferences,
	)
	ok, validation_error = _validate_runtime_payload(
		payload=payload,
		reasoning_type=reasoning_type,
		activation_contract=activation_contract,
		presentation_preferences=presentation_preferences,
	)
	if not ok:
		return ERPBusinessReasoningExecutionResult(
			status="invalid_payload",
			validation_error=validation_error,
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)

	contract = build_erp_business_reasoning_contract(
		request_id=request_id,
		session_id=session_id,
		reasoning_type=reasoning_type,
		grounding_source_request_id=str(activation_contract.get("grounded_source_request_id") or "").strip(),
		grounding_source_kind=str(activation_contract.get("grounded_source_kind") or "").strip(),
		grounding_family_id=str(activation_contract.get("grounded_family_id") or "").strip(),
		grounding_artifact_type=str(activation_contract.get("grounded_artifact_type") or "").strip(),
		grounding_source_reports=list(activation_contract.get("grounded_source_reports") or []),
		grounding_sufficient=True,
		grounding_gaps=[],
		bounded_domain="erp_business_reasoning",
		reasoning_scope="grounded_only",
		supported_claims=[dict(item) for item in (payload.get("supported_claims") or []) if isinstance(item, dict)],
		recommendations=[dict(item) for item in (payload.get("recommendations") or []) if isinstance(item, dict)],
		speculation_flags=[str(item or "").strip() for item in (payload.get("speculation_flags") or []) if str(item or "").strip()],
		allowed_to_answer=True,
		reason=str(payload.get("reason") or "").strip(),
		confidence=float(payload.get("confidence") or 0.0),
	)
	return ERPBusinessReasoningExecutionResult(
		status="answered",
		answer_text=str(payload.get("answer_text") or "").strip(),
		reasoning_contract=contract.to_payload(),
		agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
	)


def run_phase6c_reasoning_execution_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6c-reasoning",
		session_id="phase6c",
		user_id="Administrator",
		message="what does this mean",
		recent_messages=[
			{"role": "assistant", "content": "Accounts Receivable Summary for the company shows severe overdue concentration."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-1",
			"grounded_source_kind": "report",
			"grounded_source_name": "Accounts Receivable Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary"],
			"grounded_capability_id": "accounts_receivable_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "interpretation",
				"confidence": 0.95,
				"reason": "Grounded meaning question over prior AR summary.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-1",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
			"returned_schema": ["customer", "outstanding", "over_121_days"],
			"table_rows": [
				{"customer": "35th Street Mobile Wholesale", "outstanding": "44,324,000", "over_121_days": "33,447,000"},
				{"customer": "Bayint Naung Wholesale Mobile", "outstanding": "37,565,500", "over_121_days": "26,430,500"},
			],
			"row_count": 10,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
	)
	if result.status != "answered":
		raise RuntimeError(f"Phase 6C reasoning execution smoke failed with status `{result.status}`.")
	contract = dict(result.reasoning_contract or {})
	if not bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6C reasoning execution smoke failed: allowed_to_answer is false.")
	if str(contract.get("reasoning_type") or "").strip() != "interpretation":
		raise RuntimeError("Phase 6C reasoning execution smoke failed: reasoning_type mismatch.")
	if not str(result.answer_text or "").strip():
		raise RuntimeError("Phase 6C reasoning execution smoke failed: empty answer_text.")
	return {
		"ok": True,
		"result": result.to_payload(),
	}


def run_phase6d_reasoning_continuation_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6d-continuation",
		session_id="phase6d",
		user_id="Administrator",
		message="explain that recommendation more",
		recent_messages=[
			{"role": "assistant", "content": "Management should prioritize overdue receivables collection on the largest balances first and open supplier payment-plan discussions."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-2",
			"grounded_source_kind": "report",
			"grounded_source_name": "AR / AP Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"grounded_capability_id": "ar_ap_analysis_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "continuation_detail",
				"confidence": 0.93,
				"reason": "User is asking to expand the prior grounded recommendation.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-2",
			"source_kind": "report",
			"source_name": "AR / AP Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"returned_schema": ["metric", "value"],
			"table_rows": [
				{"metric": "Accounts Receivable Outstanding", "value": "288,345,000"},
				{"metric": "Accounts Payable Outstanding", "value": "701,339,600"},
				{"metric": "AR Overdue Ratio", "value": "92.9%"},
				{"metric": "AP Overdue Ratio", "value": "91.9%"},
			],
			"row_count": 4,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"capability_id": "ar_ap_analysis_read",
		},
		latest_assistant_payload={"title": "AR / AP working capital analysis"},
		prior_reasoning_contract={
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "artifact-trace-2",
			"grounding_source_kind": "report",
			"grounding_family_id": "aging",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"grounding_sufficient": True,
			"allowed_to_answer": True,
			"reasoning_type": "recommendation",
			"reason": "Recommendations are tied directly to the grounded AR/AP imbalance and overdue ratios.",
			"supported_claims": [
				{
					"claim": "Working-capital pressure is severe.",
					"support": "Payables exceed receivables by more than 400 MMK Million and both overdue ratios exceed 91%.",
				}
			],
			"recommendations": [
				{
					"action": "Prioritize overdue receivables collection on the largest balances first.",
					"rationale": "AR is heavily overdue, so cash recovery is the fastest grounded lever.",
				},
				{
					"action": "Open supplier payment-plan discussions with the most exposed vendors.",
					"rationale": "AP is also heavily overdue, so supplier stability needs immediate containment.",
				},
			],
			"speculation_flags": [],
		},
		prior_answer_text="Management should prioritize overdue receivables collection on the largest balances first and open supplier payment-plan discussions with major suppliers.",
	)
	if result.status != "answered":
		raise RuntimeError(f"Phase 6D reasoning continuation smoke failed with status `{result.status}`.")
	contract = dict(result.reasoning_contract or {})
	if str(contract.get("reasoning_type") or "").strip() != "continuation_detail":
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: reasoning_type mismatch.")
	if not bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: allowed_to_answer is false.")
	if not str(result.answer_text or "").strip():
		raise RuntimeError("Phase 6D reasoning continuation smoke failed: empty answer_text.")
	return {
		"ok": True,
		"result": result.to_payload(),
	}


def run_phase6d_reasoning_continuation_guardrail_smoke() -> Dict[str, Any]:
	result = execute_erp_business_reasoning(
		request_id="phase6d-continuation-guardrail",
		session_id="phase6d",
		user_id="Administrator",
		message="explain that recommendation more",
		recent_messages=[
			{"role": "assistant", "content": "Management should prioritize overdue receivables collection on the largest balances first."},
		],
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_request_id": "artifact-trace-current",
			"grounded_source_kind": "report",
			"grounded_source_name": "Accounts Receivable Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary"],
			"grounded_capability_id": "accounts_receivable_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"report_date": "2026-03-26",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
		semantic_activation_result={
			"status": "accepted",
			"intent": {
				"reasoning_type": "continuation_detail",
				"confidence": 0.91,
				"reason": "User is asking to expand the prior grounded recommendation.",
			},
		},
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-current",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
			"row_count": 10,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
		prior_reasoning_contract={
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "artifact-trace-prior",
			"grounding_source_kind": "report",
			"grounding_family_id": "aging",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Summary"],
			"grounding_sufficient": True,
			"allowed_to_answer": True,
			"reasoning_type": "recommendation",
			"reason": "Recommendations are tied to grounded AR facts.",
			"supported_claims": [],
			"recommendations": [],
			"speculation_flags": [],
		},
		prior_answer_text="Management should prioritize overdue receivables collection first.",
	)
	if result.status != "insufficient_grounding":
		raise RuntimeError(
			f"Phase 6D reasoning continuation guardrail smoke failed with status `{result.status}`."
		)
	contract = dict(result.reasoning_contract or {})
	if bool(contract.get("allowed_to_answer")):
		raise RuntimeError("Phase 6D reasoning continuation guardrail smoke failed: allowed_to_answer should be false.")
	grounding_gaps = {str(item or "").strip() for item in (contract.get("grounding_gaps") or []) if str(item or "").strip()}
	if "prior_reasoning_source_mismatch" not in grounding_gaps:
		raise RuntimeError(
			f"Phase 6D reasoning continuation guardrail smoke failed: expected source mismatch, got {sorted(grounding_gaps)!r}."
		)
	return {
		"ok": True,
		"result": result.to_payload(),
	}
