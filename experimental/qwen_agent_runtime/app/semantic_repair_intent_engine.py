from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	RepairIntentInterpretRequest,
	RepairIntentInterpretResponse,
	RepairIntentInterpretation,
)
from app.settings import Settings


class SemanticRepairIntentEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You classify whether a user turn is accepting a prior governed recovery action or asking for bounded guidance about that recovery.
Return only a single JSON object with these keys:
- repair_intent_type: string
- accepted_recovery_action: string
- guidance_topic: string
- preserve_scope: boolean
- preserve_entity_dimension: boolean
- preserve_time_context: boolean
- confidence: number from 0 to 1
- reason: short string

Rules:
- Use only repair_intent_type values from:
  - accept_recovery_action
  - guidance_request
  - not_applicable
- Use accepted_recovery_action only when the user is clearly accepting one of interpretation_context.available_recovery_actions.
- Do not treat a substantive output refinement as acceptance. If the user is still asking for a missing metric, column, field, or output shape, do not choose accept_recovery_action.
- If the user is asking how to request the missing governed output or asking what to type, choose guidance_request.
- If the user is asking for fresh data unrelated to the prior recovery, return not_applicable.
- If the user is just continuing normal analysis or front-door talk, return not_applicable.
- Only set preserve_scope, preserve_entity_dimension, or preserve_time_context when the user is continuing the prior recovery and those context elements should carry forward.
- Keep guidance_topic compact, such as qty, delivery_status, overdue_customers, or alternative_report.
- Do not invent recovery actions that are not available.
- Examples:
  - If the prior recovery offered a governed alternative and the user says "yes, run that" or "please run the separate governed query", choose `accept_recovery_action`.
  - If the user says "include qty column", "show revenue and quantity together", or keeps requesting the missing output itself, do not choose `accept_recovery_action`; prefer `guidance_request` or `not_applicable` based on the turn.
  - If the user asks "how should I ask for qty" or "what should I type to get that result", choose `guidance_request`.
  - If the user changes topic to a new ERP ask, choose `not_applicable`.
- Keep the JSON compact and valid."""


def _user_prompt(request: RepairIntentInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"latest_recovery_contract": request.latest_recovery_contract,
		"latest_grounded_turn": request.latest_grounded_turn,
		"latest_assistant_payload": request.latest_assistant_payload,
		"interpretation_context": request.interpretation_context,
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticRepairIntentEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_reasoning_model(),
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
		raise SemanticRepairIntentEngineError(f"Semantic repair interpretation request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticRepairIntentEngineError(
			f"Semantic repair interpretation returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise SemanticRepairIntentEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticRepairIntentEngineError("Semantic repair interpretation returned invalid payload.")
	return data, resp.status_code, latency_ms


def _extract_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise SemanticRepairIntentEngineError("Semantic repair interpretation response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticRepairIntentEngineError("Semantic repair interpretation response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		raise SemanticRepairIntentEngineError(
			f"Semantic repair interpretation returned invalid JSON: {content[:300]}"
		) from exc
	if not isinstance(obj, dict):
		raise SemanticRepairIntentEngineError("Semantic repair interpretation JSON was not an object.")
	return obj


def run_semantic_repair_intent_engine(
	request: RepairIntentInterpretRequest,
	settings: Settings,
) -> RepairIntentInterpretResponse:
	messages = [
		{"role": "system", "content": _system_prompt()},
		{"role": "user", "content": _user_prompt(request)},
	]
	data, status_code, latency_ms = _chat_completion_json(settings, messages)
	obj = _extract_json_content(data)
	return RepairIntentInterpretResponse(
		ok=True,
		interpretation=RepairIntentInterpretation(
			repair_intent_type=str(obj.get("repair_intent_type") or "").strip(),
			accepted_recovery_action=str(obj.get("accepted_recovery_action") or "").strip(),
			guidance_topic=str(obj.get("guidance_topic") or "").strip(),
			preserve_scope=bool(obj.get("preserve_scope")),
			preserve_entity_dimension=bool(obj.get("preserve_entity_dimension")),
			preserve_time_context=bool(obj.get("preserve_time_context")),
			confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
			reason=str(obj.get("reason") or "").strip(),
		),
		agent_meta={
			"engine": "semantic_repair_intent",
			"model": settings.effective_semantic_reasoning_model(),
			"telemetry": {
				"attempt_count": 1,
				"latency_ms": latency_ms,
				"provider_status_code": status_code,
			},
		},
		error="",
	)
