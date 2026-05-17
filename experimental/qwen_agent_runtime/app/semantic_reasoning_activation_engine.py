from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	ReasoningActivationInterpretRequest,
	ReasoningActivationInterpretResponse,
	ReasoningActivationInterpretation,
)
from app.settings import Settings


class SemanticReasoningActivationEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You classify whether a user turn is requesting ERP business reasoning over an already grounded ERP result.
Return only a single JSON object with these keys:
- reasoning_type: string
- detail_level: string
- presentation_style: string
- response_mode: string
- evidence_policy: string
- answer_obligation: string
- answer_goal: string
- evidence_depth: string
- business_role: string
- target_reference: string
- risk_level: string
- confidence: number from 0 to 1
- reason: short string

Rules:
- Use only reasoning_type values from activation_context.allowed_reasoning_types.
- If the user is asking for business meaning of grounded ERP facts, choose interpretation.
- If the user is asking why a grounded conclusion was reached, choose explanation.
- If the user is asking what management should do next or for bounded actions tied to grounded ERP facts, choose recommendation.
- If the user is asking to expand or continue a prior grounded recommendation or explanation, choose continuation_detail.
- If activation_context.prior_reasoning_available is true and the user is clearly continuing that prior grounded answer, prefer continuation_detail over falling back to fresh-query behavior.
- If activation_context.prior_reasoning_available is true and the user asks to make the prior grounded answer clearer, easier to read, reformatted, summarized, or expanded, choose continuation_detail; this is a continuation of the reasoning answer, not a master-data or fresh-report request.
- If activation_context.prior_offered_next_action_count is greater than zero and the user accepts or continues the offered next action, choose continuation_detail; the offered action is part of the prior grounded reasoning contract.
- If activation_context.composite_grounding is true, preserve that multi-source analytical context when classifying the turn; do not collapse it into a single-source reading.
- Use detail_level values only from:
  - default
  - expanded
  - comprehensive
- Use presentation_style values only from:
  - default
  - bullet
  - table
- Use response_mode values only from:
  - factual_grounded_answer
  - consultant_interpretation
  - consultant_detail
  - consultant_recommendation
  - boundary_guidance
- Use evidence_policy values only from:
  - current_result_only
  - evidence_expansion_preferred
  - evidence_expansion_required
  - policy_required
- Use answer_obligation values only from:
  - explain_grounded_meaning
  - explain_grounded_basis
  - expand_grounded_detail
  - advise_with_approved_policy
  - state_boundary_and_next_step
- Use answer_goal values only from:
  - explain
  - expand_detail
  - compare
  - recommend
  - diagnose
  - define
  - calculate
  - clarify_boundary
- Use evidence_depth values only from:
  - current_result_only
  - drilldown_preferred
  - drilldown_required
  - policy_required
- Use business_role values only from:
  - business_consultant
  - controller
  - collector
  - buyer
  - sales_manager
  - inventory_manager
  - analyst
- Use target_reference values only from:
  - current_result
  - current_metric
  - current_row
  - entity
  - document
  - line_item
  - offered_next_action
  - family_summary
  - unknown
- Use risk_level values only from:
  - factual_only
  - bounded_consultation
  - policy_required
  - unsupported
- Populate the detail-intent slots from the business intent and activation_context, not from brittle phrase matching.
- When the user asks for business interpretation, implications, or management-level meaning of a grounded result, use consultant_interpretation and explain_grounded_meaning.
- When the user asks for deeper detail beyond a summary, use consultant_detail and prefer evidence expansion instead of repeating the same rows.
- When the user asks for management action or advice, use consultant_recommendation only if activation_context.recommendation_allowed is true; otherwise use boundary_guidance with policy_required.
- If the user asks for a clearer or more detailed grounded continuation, raise detail_level to expanded or comprehensive as appropriate.
- If the user asks for bullet-style or table-style grounded output, set presentation_style accordingly.
- If the message is really asking for fresh data retrieval, a report switch, a new governed query, repair, or front-door conversation, return an empty reasoning_type with low confidence.
- Do not invent reasoning types.
- Keep the JSON compact and valid."""


def _user_prompt(request: ReasoningActivationInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"latest_grounded_turn": request.latest_grounded_turn,
		"latest_family_artifact": request.latest_family_artifact,
		"latest_assistant_payload": request.latest_assistant_payload,
		"activation_context": request.activation_context,
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticReasoningActivationEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_reasoning_model(),
		"messages": messages,
		"temperature": 0,
		"max_tokens": 320,
		"response_format": {"type": "json_object"},
		"extra_body": _extra_body(settings),
	}
	start = time.perf_counter()
	try:
		resp = requests.post(
			url,
			headers=headers,
			data=json.dumps(payload),
			timeout=max(5, settings.chat_timeout_seconds),
		)
	except requests.RequestException as exc:
		raise SemanticReasoningActivationEngineError(f"Semantic reasoning activation request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticReasoningActivationEngineError(
			f"Semantic reasoning activation returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise SemanticReasoningActivationEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticReasoningActivationEngineError("Semantic reasoning activation returned invalid payload.")
	return data, resp.status_code, latency_ms


def _extract_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise SemanticReasoningActivationEngineError("Semantic reasoning activation response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticReasoningActivationEngineError("Semantic reasoning activation response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		raise SemanticReasoningActivationEngineError(
			f"Semantic reasoning activation returned invalid JSON: {content[:300]}"
		) from exc
	if not isinstance(obj, dict):
		raise SemanticReasoningActivationEngineError("Semantic reasoning activation JSON was not an object.")
	return obj


def run_semantic_reasoning_activation_engine(
	request: ReasoningActivationInterpretRequest,
	settings: Settings,
) -> ReasoningActivationInterpretResponse:
	messages = [
		{"role": "system", "content": _system_prompt()},
		{"role": "user", "content": _user_prompt(request)},
	]
	last_status_code = 0
	total_latency_ms = 0
	last_error = ""
	obj: Dict[str, Any] | None = None
	attempt = 0
	for attempt in range(1, settings.semantic_reasoning_max_attempts + 1):
		try:
			data, status_code, latency_ms = _chat_completion_json(settings, messages)
			last_status_code = status_code
			total_latency_ms += latency_ms
			obj = _extract_json_content(data)
			break
		except SemanticReasoningActivationEngineError as exc:
			last_error = str(exc)
			if attempt >= settings.semantic_reasoning_max_attempts:
				raise
			time.sleep(min(2.0, (settings.semantic_reasoning_backoff_ms * attempt) / 1000.0))
	if obj is None:
		raise SemanticReasoningActivationEngineError(last_error or "Semantic reasoning activation engine failed.")

	return ReasoningActivationInterpretResponse(
		ok=True,
		interpretation=ReasoningActivationInterpretation(
			reasoning_type=str(obj.get("reasoning_type") or "").strip(),
			detail_level=str(obj.get("detail_level") or "").strip(),
			presentation_style=str(obj.get("presentation_style") or "").strip(),
			response_mode=str(obj.get("response_mode") or "").strip(),
			evidence_policy=str(obj.get("evidence_policy") or "").strip(),
			answer_obligation=str(obj.get("answer_obligation") or "").strip(),
			answer_goal=str(obj.get("answer_goal") or "").strip(),
			evidence_depth=str(obj.get("evidence_depth") or "").strip(),
			business_role=str(obj.get("business_role") or "").strip(),
			target_reference=str(obj.get("target_reference") or "").strip(),
			risk_level=str(obj.get("risk_level") or "").strip(),
			confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
			reason=str(obj.get("reason") or "").strip(),
		),
		agent_meta={
			"engine": "semantic_reasoning_activation",
			"model": settings.effective_semantic_reasoning_model(),
			"telemetry": {
				"attempt_count": attempt,
				"latency_ms": total_latency_ms,
				"provider_status_code": last_status_code,
			},
		},
		error="",
	)
