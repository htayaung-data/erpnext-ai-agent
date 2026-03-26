from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import FrontDoorRenderRequest, FrontDoorRenderResponse
from app.settings import Settings


class FrontDoorResponseEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You render warm, concise front-door replies for an ERP assistant after routing has already been validated.

You must follow these rules:
- Stay within the validated front-door intent and response payload facts.
- Never claim ERP data access, report execution, or business results in this reply.
- Never invent capabilities beyond response_payload.supported_areas or capability_labels when they are provided.
- Be warm, natural, and concise.
- Prefer 1 or 2 short paragraphs, maximum 3 sentences total.
- Do not mention internal contracts, classifiers, confidence, policies, or validation.
- If suggested prompts exist, you may naturally hint at one or two, but do not output a bullet list unless clearly useful.
- If response_mode is capability_summary, explain the supported governed ERP areas clearly and naturally.
- If response_mode is continue_current_flow, acknowledge the current context naturally without sounding robotic.
- If response_mode is direct_answer, respond like a helpful teammate.
- Return only a compact JSON object with:
  - answer_text: string
  - tone: string
"""


def _few_shot_messages() -> List[Dict[str, str]]:
	return [
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "you are really clever",
					"intent_class": "thanks",
					"response_mode": "direct_answer",
					"response_payload": {
						"text": "You're welcome. If you want, I can continue the current ERP analysis or start a new governed query."
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "Thank you. If you want, we can keep going with the current ERP analysis or start a new governed query.",
					"tone": "warm",
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "what can u do, tell me details",
					"intent_class": "capability_question",
					"response_mode": "capability_summary",
					"response_payload": {
						"supported_areas": [
							"financial statements",
							"AR / AP",
							"sales",
							"inventory",
							"product performance",
							"invoices",
						],
						"suggested_prompts": [
							"Show me sales trend",
							"Analyze AR / AP",
							"Give me the financial statement",
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
					"answer_text": "I can help with governed ERP reporting and follow-up analysis across financial statements, AR / AP, sales, inventory, product performance, and invoices. If you want, you can ask for something like sales trend, AR / AP analysis, or a financial statement.",
					"tone": "warm",
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "user",
			"content": json.dumps(
				{
					"message": "I am okay for now, I will come back later",
					"intent_class": "closure_signoff",
					"response_mode": "direct_answer",
					"response_payload": {
						"text": "Understood. Feel free to come back anytime, and we can pick up from a new ERP question or continue from there."
					},
				},
				ensure_ascii=False,
			),
		},
		{
			"role": "assistant",
			"content": json.dumps(
				{
					"answer_text": "Of course. Come back anytime and we can pick up from there whenever you're ready.",
					"tone": "warm",
				},
				ensure_ascii=False,
			),
		},
	]


def _user_prompt(request: FrontDoorRenderRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"grounded_context_available": bool(request.grounded_context_available),
		"intent_class": str(request.intent_class or "").strip(),
		"response_mode": str(request.response_mode or "").strip(),
		"response_payload": request.response_payload if isinstance(request.response_payload, dict) else {},
		"reason": str(request.reason or "").strip(),
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise FrontDoorResponseEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_frontdoor_model(),
		"messages": messages,
		"temperature": 0.35,
		"max_tokens": 220,
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
		raise FrontDoorResponseEngineError(f"Front-door renderer request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise FrontDoorResponseEngineError(
			f"Front-door renderer returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise FrontDoorResponseEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise FrontDoorResponseEngineError("Front-door renderer returned invalid payload.")
	return data, resp.status_code, latency_ms


def _extract_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise FrontDoorResponseEngineError("Front-door renderer response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise FrontDoorResponseEngineError("Front-door renderer response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		raise FrontDoorResponseEngineError(
			f"Front-door renderer returned invalid JSON: {content[:300]}"
		) from exc
	if not isinstance(obj, dict):
		raise FrontDoorResponseEngineError("Front-door renderer JSON was not an object.")
	return obj


def run_frontdoor_response_engine(
	request: FrontDoorRenderRequest,
	settings: Settings,
) -> FrontDoorRenderResponse:
	messages = [{"role": "system", "content": _system_prompt()}]
	messages.extend(_few_shot_messages())
	messages.append({"role": "user", "content": _user_prompt(request)})
	data, status_code, latency_ms = _chat_completion_json(settings, messages)
	obj = _extract_json_content(data)
	answer_text = str(obj.get("answer_text") or "").strip()
	if not answer_text:
		raise FrontDoorResponseEngineError("Front-door renderer returned no answer text.")
	return FrontDoorRenderResponse(
		ok=True,
		answer_text=answer_text,
		agent_meta={
			"engine": "frontdoor_response_renderer",
			"model": settings.effective_semantic_frontdoor_model(),
			"telemetry": {
				"latency_ms": latency_ms,
				"provider_status_code": status_code,
				"tone": str(obj.get("tone") or "").strip(),
			},
		},
		error="",
	)
