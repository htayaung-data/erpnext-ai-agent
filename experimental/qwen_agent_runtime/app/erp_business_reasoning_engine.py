from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	ReasoningRenderPayload,
	ReasoningRenderRequest,
	ReasoningRenderResponse,
)
from app.settings import Settings


class ERPBusinessReasoningEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You render grounded ERP business reasoning from structured governed context.

Return only one compact JSON object with these keys:
- answer_text: string
- supported_claims: array of objects
- recommendations: array of objects
- speculation_flags: array of strings
- confidence: number from 0 to 1
- reason: short string

Rules:
- Use only the supplied reasoning_context and recent grounded conversation.
- Never fetch new data, invent metrics, or assume facts not present in reasoning_context.
- Once a reasoning turn is accepted, answer it directly. Do not ask the user to choose another option, do not say "happy to help" without delivering the content, and do not stop at a lead-in sentence ending with a colon.
- If reasoning_type is interpretation or explanation, recommendations must be empty.
- If reasoning_type is recommendation or continuation_detail, recommendations must stay tied to grounded ERP facts already present in reasoning_context.
- If reasoning_type is continuation_detail and prior_reasoning is provided, expand that prior grounded reasoning instead of starting a new line of analysis.
- If grounded_source.composite_grounding is true or grounded_source.source_report_count > 1, preserve the multi-source analytical picture in the answer. Do not collapse a composite AR/AP-style analysis into only one side unless the grounding is explicitly one-sided.
- Honor reasoning_context.presentation_preferences when present:
  - if bullet is true, answer_text must contain the actual bullet content directly
  - if table is true, answer_text may introduce a compact table but still must deliver the content directly
  - if million is true, any scaled monetary values must be labeled explicitly as "MMK Million"
- Honor reasoning_context.detail_level when present:
  - default: concise but useful
  - expanded: more grounded detail, clearer breakdown, more operational specificity
  - comprehensive: the most complete grounded continuation you can provide without inventing facts
- If you cannot support a claim from the provided grounding, omit it and add a short speculation flag.
- Keep supported_claims concise. Each claim object should use:
  - claim: string
  - support: string
- Keep recommendation objects concise. Each recommendation object should use:
  - action: string
  - rationale: string
  - basis_claim_refs: array of integer indices into supported_claims
- Keep answer_text concise and useful. Prefer 1-3 short paragraphs.
- Do not mention contracts, policies, validators, or routing.
"""


def _few_shot_messages() -> List[Dict[str, str]]:
	return [
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "what does this mean",
					"reasoning_context": {
						"reasoning_type": "interpretation",
						"bounded_domain": "erp_business_reasoning",
						"grounding_summary": {
							"company": "Example Co.",
							"report_name": "Accounts Receivable Summary",
							"report_date": "2026-03-26",
						},
						"grounded_findings": [
							"Outstanding receivables total 288.3 MMK Million.",
							"92.9% of receivables are overdue.",
							"121+ day balances dominate the aging profile.",
						],
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "This receivables position indicates serious collection stress. Most of the balance is already overdue, and the concentration in the oldest bucket suggests the problem is not short-term timing but persistent non-collection.",
					"supported_claims": [
						{
							"claim": "Receivables quality is weak.",
							"support": "92.9% of the outstanding balance is overdue.",
						},
						{
							"claim": "Collection problems are long-standing rather than recent.",
							"support": "The 121+ day bucket dominates the aging profile.",
						},
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.92,
					"reason": "Interpretation grounded entirely in the aging summary facts.",
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "what should management do next",
					"reasoning_context": {
						"reasoning_type": "recommendation",
						"bounded_domain": "erp_business_reasoning",
						"grounding_summary": {
							"company": "Example Co.",
							"report_name": "AR / AP analysis",
							"report_date": "2026-03-26",
						},
						"grounded_findings": [
							"Payables exceed receivables by 413.0 MMK Million.",
							"AR overdue ratio is 92.9%.",
							"AP overdue ratio is 91.9%.",
						],
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "Management should treat this as a working-capital emergency. The immediate priority is to improve cash conversion from receivables while stabilizing supplier commitments that are already badly overdue.",
					"supported_claims": [
						{
							"claim": "Working-capital pressure is severe.",
							"support": "Payables exceed receivables by 413.0 MMK Million and both overdue ratios exceed 91%.",
						},
					],
					"recommendations": [
						{
							"action": "Prioritize overdue receivables collection on the largest balances first.",
							"rationale": "AR is heavily overdue, so cash recovery is the fastest grounded lever.",
							"basis_claim_refs": [0],
						},
						{
							"action": "Open supplier payment-plan discussions with the most exposed vendors.",
							"rationale": "AP is also heavily overdue, so supplier stability needs immediate containment.",
							"basis_claim_refs": [0],
						},
					],
					"speculation_flags": [],
					"confidence": 0.9,
					"reason": "Recommendations are tied directly to the grounded AR/AP imbalance and overdue ratios.",
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "explain that recommendation more",
					"reasoning_context": {
						"reasoning_type": "continuation_detail",
						"bounded_domain": "erp_business_reasoning",
						"grounding_summary": {
							"company": "Example Co.",
							"report_name": "AR / AP analysis",
							"report_date": "2026-03-26",
						},
						"grounded_findings": [
							"Payables exceed receivables by 413.0 MMK Million.",
							"AR overdue ratio is 92.9%.",
							"AP overdue ratio is 91.9%.",
						],
						"prior_reasoning": {
							"reasoning_type": "recommendation",
							"supported_claims": [
								{
									"claim": "Working-capital pressure is severe.",
									"support": "Payables exceed receivables by 413.0 MMK Million and both overdue ratios exceed 91%.",
								}
							],
							"recommendations": [
								{
									"action": "Prioritize overdue receivables collection on the largest balances first.",
									"rationale": "AR is heavily overdue, so cash recovery is the fastest grounded lever.",
								}
							],
							"answer_text": "Management should prioritize overdue receivables collection on the largest balances first.",
						},
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "That recommendation matters because receivables are the fastest grounded cash lever in this situation. Since AR is already heavily overdue, improving collection on the largest balances can relieve pressure sooner than waiting for a broad operating recovery.",
					"supported_claims": [
						{
							"claim": "Receivables recovery is the most immediate cash action available from the grounded facts.",
							"support": "AR is heavily overdue, so cash is already tied up in late customer balances.",
						}
					],
					"recommendations": [
						{
							"action": "Start with the largest overdue customers first.",
							"rationale": "That sequence maximizes near-term cash impact within the same grounded AR problem.",
							"basis_claim_refs": [0],
						}
					],
					"speculation_flags": [],
					"confidence": 0.9,
					"reason": "Continuation detail expands the prior grounded recommendation without changing the source analysis.",
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "give me with bullet style recommendation so that I can understand more easily",
					"reasoning_context": {
						"reasoning_type": "continuation_detail",
						"bounded_domain": "erp_business_reasoning",
						"presentation_preferences": {"bullet": True, "table": False, "million": True},
						"grounding_summary": {
							"company": "Example Co.",
							"report_name": "AR / AP analysis",
							"report_date": "2026-03-26",
						},
						"grounded_findings": [
							"Payables exceed receivables by 413.0 MMK Million.",
							"AR overdue ratio is 92.9%.",
							"AP overdue ratio is 91.9%.",
						],
						"prior_reasoning": {
							"reasoning_type": "recommendation",
							"supported_claims": [
								{
									"claim": "Working-capital pressure is severe.",
									"support": "Payables exceed receivables by 413.0 MMK Million and both overdue ratios exceed 91%.",
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
						},
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "- Start with the largest overdue receivables so the business can unlock cash faster.\n- Open payment-plan discussions with the most exposed suppliers to reduce near-term outflow pressure.\n- Track both actions together because the AR/AP gap of 413.0 MMK Million shows one side will not stabilize without the other.",
					"supported_claims": [
						{
							"claim": "The working-capital gap is material.",
							"support": "Payables exceed receivables by 413.0 MMK Million.",
						},
						{
							"claim": "Both cash inflow and outflow sides are stressed.",
							"support": "AR overdue ratio is 92.9% and AP overdue ratio is 91.9%.",
						},
					],
					"recommendations": [
						{
							"action": "Prioritize overdue receivables collection on the largest balances first.",
							"rationale": "That is the fastest grounded lever for improving cash inflow.",
							"basis_claim_refs": [0, 1],
						},
						{
							"action": "Open payment-plan discussions with the most exposed suppliers.",
							"rationale": "That reduces near-term outflow pressure while AR recovery is underway.",
							"basis_claim_refs": [0, 1],
						},
					],
					"speculation_flags": [],
					"confidence": 0.9,
					"reason": "Continuation detail directly fulfills the requested bullet-style recommendation using the prior grounded analysis.",
				},
				ensure_ascii=False,
			),
		},
	]


def _user_prompt(request: ReasoningRenderRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"reasoning_context": request.reasoning_context if isinstance(request.reasoning_context, dict) else {},
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise ERPBusinessReasoningEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_reasoning_model(),
		"messages": messages,
		"temperature": 0.2,
		"max_tokens": 700,
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
		raise ERPBusinessReasoningEngineError(f"ERP business reasoning request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise ERPBusinessReasoningEngineError(
			f"ERP business reasoning returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise ERPBusinessReasoningEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise ERPBusinessReasoningEngineError("ERP business reasoning returned invalid payload.")
	return data, resp.status_code, latency_ms


def _extract_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise ERPBusinessReasoningEngineError("ERP business reasoning response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise ERPBusinessReasoningEngineError("ERP business reasoning response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		raise ERPBusinessReasoningEngineError(
			f"ERP business reasoning returned invalid JSON: {content[:300]}"
		) from exc
	if not isinstance(obj, dict):
		raise ERPBusinessReasoningEngineError("ERP business reasoning JSON was not an object.")
	return obj


def run_erp_business_reasoning_engine(
	request: ReasoningRenderRequest,
	settings: Settings,
) -> ReasoningRenderResponse:
	messages = [{"role": "system", "content": _system_prompt()}]
	messages.extend(_few_shot_messages())
	messages.append({"role": "user", "content": _user_prompt(request)})
	data, status_code, latency_ms = _chat_completion_json(settings, messages)
	obj = _extract_json_content(data)
	answer_text = str(obj.get("answer_text") or "").strip()
	if not answer_text:
		raise ERPBusinessReasoningEngineError("ERP business reasoning renderer returned no answer text.")
	return ReasoningRenderResponse(
		ok=True,
		payload=ReasoningRenderPayload(
			answer_text=answer_text,
			supported_claims=[dict(item) for item in (obj.get("supported_claims") or []) if isinstance(item, dict)],
			recommendations=[dict(item) for item in (obj.get("recommendations") or []) if isinstance(item, dict)],
			speculation_flags=[str(item or "").strip() for item in (obj.get("speculation_flags") or []) if str(item or "").strip()],
			confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
			reason=str(obj.get("reason") or "").strip(),
		),
		agent_meta={
			"engine": "erp_business_reasoning",
			"model": settings.effective_semantic_reasoning_model(),
			"telemetry": {
				"latency_ms": latency_ms,
				"provider_status_code": status_code,
			},
		},
		error="",
	)
