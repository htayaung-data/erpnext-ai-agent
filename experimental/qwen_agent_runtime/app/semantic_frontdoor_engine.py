from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	FrontDoorInterpretRequest,
	FrontDoorInterpretResponse,
	FrontDoorInterpretation,
)
from app.settings import Settings


class SemanticFrontDoorEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You classify front-door conversational ERP assistant turns into a governed intent proposal.
Return only a single JSON object with these keys:
- intent_class: string
- confidence: number from 0 to 1
- reason: short string
- extracted_slots: object

Rules:
- Use only intent_class values from interpretation_context.intent_classes.
- Use front-door classes only for clearly conversational or session-management turns.
- If the message plausibly asks for ERP data, business analysis, reporting, metrics, or a governed follow-up, choose route_onward.
- Use capability_question only when the user is asking what the assistant can help with.
- Use session_flow only when the message is about continuing the current thread and depends on the existing grounded context.
- Use closure_signoff for polite turns that end, pause, or defer the conversation without asking for ERP data.
- Use extracted_slots only when the message is clearly a master-data navigation request that can be safely structured.
- Allowed extracted_slots keys are entity_grain, lookup_mode, lookup_projection, and lookup_search_text.
- Use only entity_grain values from interpretation_context.active_master_data_entity_grains.
- Use only lookup_mode values from interpretation_context.active_master_data_lookup_modes.
- Use only lookup_projection values from interpretation_context.active_master_data_lookup_projections.
- If the master-data grain or mode is not clear enough, leave extracted_slots empty or partially empty instead of guessing.
- For non-route_onward intents, extracted_slots should usually be empty.
- If uncertain, choose route_onward.
- Keep the JSON compact, valid, and schema-aligned."""


def _user_prompt(request: FrontDoorInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"grounded_context_available": bool(request.grounded_context_available),
		"interpretation_context": request.interpretation_context,
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticFrontDoorEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_frontdoor_model(),
		"messages": messages,
		"temperature": 0,
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
		raise SemanticFrontDoorEngineError(f"Semantic front-door request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticFrontDoorEngineError(
			f"Semantic front-door returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise SemanticFrontDoorEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticFrontDoorEngineError("Semantic front-door returned invalid payload.")
	return data, resp.status_code, latency_ms


def _extract_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise SemanticFrontDoorEngineError("Semantic front-door response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticFrontDoorEngineError("Semantic front-door response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		raise SemanticFrontDoorEngineError(
			f"Semantic front-door returned invalid JSON: {content[:300]}"
		) from exc
	if not isinstance(obj, dict):
		raise SemanticFrontDoorEngineError("Semantic front-door JSON was not an object.")
	return obj


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _canonicalize_interpretation_obj(
	raw_obj: Dict[str, Any],
	request: FrontDoorInterpretRequest,
) -> Dict[str, Any]:
	obj = dict(raw_obj or {})
	intent_class = _clean_text(obj.get("intent_class"))
	context = request.interpretation_context if isinstance(request.interpretation_context, dict) else {}
	allowed_entity_grains = set(_clean_list(context.get("active_master_data_entity_grains")))
	allowed_lookup_modes = set(_clean_list(context.get("active_master_data_lookup_modes")))
	allowed_lookup_projections = set(_clean_list(context.get("active_master_data_lookup_projections")))
	raw_slots = obj.get("extracted_slots") if isinstance(obj.get("extracted_slots"), dict) else {}
	canonical_slots: Dict[str, Any] = {}
	if intent_class == "route_onward":
		entity_grain = _clean_text(raw_slots.get("entity_grain"))
		lookup_mode = _clean_text(raw_slots.get("lookup_mode"))
		lookup_projection = _clean_text(raw_slots.get("lookup_projection"))
		lookup_search_text = _clean_text(raw_slots.get("lookup_search_text"))
		if entity_grain in allowed_entity_grains:
			canonical_slots["entity_grain"] = entity_grain
		if lookup_mode in allowed_lookup_modes:
			canonical_slots["lookup_mode"] = lookup_mode
		if lookup_projection in allowed_lookup_projections:
			canonical_slots["lookup_projection"] = lookup_projection
		if lookup_search_text:
			canonical_slots["lookup_search_text"] = lookup_search_text
	obj["extracted_slots"] = canonical_slots
	return obj


def run_semantic_frontdoor_engine(
	request: FrontDoorInterpretRequest,
	settings: Settings,
) -> FrontDoorInterpretResponse:
	messages = [
		{"role": "system", "content": _system_prompt()},
		{"role": "user", "content": _user_prompt(request)},
	]
	last_status_code = 0
	total_latency_ms = 0
	last_error = ""
	obj: Dict[str, Any] | None = None
	attempt = 0
	for attempt in range(1, settings.semantic_frontdoor_max_attempts + 1):
		try:
			data, status_code, latency_ms = _chat_completion_json(settings, messages)
			last_status_code = status_code
			total_latency_ms += latency_ms
			obj = _extract_json_content(data)
			break
		except SemanticFrontDoorEngineError as exc:
			last_error = str(exc)
			if attempt >= settings.semantic_frontdoor_max_attempts:
				raise
			time.sleep(min(2.0, (settings.semantic_frontdoor_backoff_ms * attempt) / 1000.0))
	if obj is None:
		raise SemanticFrontDoorEngineError(last_error or "Semantic front-door engine failed.")
	obj = _canonicalize_interpretation_obj(obj, request)

	return FrontDoorInterpretResponse(
		ok=True,
		interpretation=FrontDoorInterpretation(
			intent_class=str(obj.get("intent_class") or "").strip(),
			confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
			reason=str(obj.get("reason") or "").strip(),
			extracted_slots=obj.get("extracted_slots") if isinstance(obj.get("extracted_slots"), dict) else {},
		),
		agent_meta={
			"engine": "semantic_frontdoor",
			"model": settings.effective_semantic_frontdoor_model(),
			"telemetry": {
				"attempt_count": attempt,
				"latency_ms": total_latency_ms,
				"provider_status_code": last_status_code,
			},
		},
		error="",
	)
