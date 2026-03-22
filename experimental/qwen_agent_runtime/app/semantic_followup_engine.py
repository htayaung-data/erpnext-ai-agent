from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	FollowUpInterpretRequest,
	FollowUpInterpretResponse,
	FollowUpInterpretation,
)
from app.settings import Settings


class SemanticFollowUpEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You interpret ERP chat follow-up requests relative to the latest grounded ERP answer.
Return only a single JSON object with these keys:
- requested_modes: array of strings
- target_dimension: string
- target_limit: integer
- sort_direction: \"asc\" | \"desc\" | \"\"
- target_capability_id: string
- self_contained: boolean
- confidence: number from 0 to 1
- reason: short string

Rules:
- Use only follow-up modes from interpretation_context.approved_follow_up_modes.
- Use only dimensions from interpretation_context.available_dimensions.
- Use only sibling capability ids from interpretation_context.available_sibling_capabilities.
- If the user asks to switch business area (for example payable to receivable), include \"sibling_switch\" and set target_capability_id.
- If the user asks for a local display change like by supplier, by customer, top N, as table, or in million, prefer follow-up modes instead of self_contained.
- If the request is a fresh standalone ERP question that should not depend on the previous grounded result, set self_contained true.
- Do not invent dimensions, modes, or capability ids that are not present in the provided context.
- Keep the JSON compact and valid."""


def _user_prompt(request: FollowUpInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [
			{"role": m.role, "content": m.content}
			for m in request.recent_messages
		],
		"latest_grounded_turn": request.latest_grounded_turn,
		"latest_assistant_payload": request.latest_assistant_payload,
		"interpretation_context": request.interpretation_context,
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticFollowUpEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_followup_model(),
		"messages": messages,
		"temperature": 0,
		"max_tokens": 300,
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
		raise SemanticFollowUpEngineError(f"Semantic follow-up request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticFollowUpEngineError(f"Semantic follow-up returned non-JSON response ({resp.status_code}).") from exc
	if resp.status_code >= 400:
		raise SemanticFollowUpEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticFollowUpEngineError("Semantic follow-up returned invalid payload.")
	return data, resp.status_code, latency_ms


def _repair_json_content(content: str) -> tuple[Dict[str, Any] | None, bool]:
	text = str(content or "").strip()
	if not text:
		return None, False
	candidates = [text]
	if text.startswith("```"):
		lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
		candidates.append("\n".join(lines).strip())
	first_brace = text.find("{")
	last_brace = text.rfind("}")
	if first_brace >= 0 and last_brace > first_brace:
		candidates.append(text[first_brace : last_brace + 1].strip())
	for candidate in list(candidates):
		trimmed = candidate.strip()
		without_trailing_commas = trimmed.replace(",}", "}").replace(",]", "]")
		if without_trailing_commas not in candidates:
			candidates.append(without_trailing_commas)
	for candidate in candidates:
		try:
			obj = json.loads(candidate)
		except Exception:
			continue
		if isinstance(obj, dict):
			return obj, candidate != text
	return None, False


def _extract_json_content(data: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
	choices = data.get("choices")
	if not isinstance(choices, list) or not choices:
		raise SemanticFollowUpEngineError("Semantic follow-up response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticFollowUpEngineError("Semantic follow-up response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		repaired_obj, used_repair = _repair_json_content(content)
		if repaired_obj is None:
			raise SemanticFollowUpEngineError(f"Semantic follow-up returned invalid JSON: {content[:300]}") from exc
		return repaired_obj, used_repair
	if not isinstance(obj, dict):
		raise SemanticFollowUpEngineError("Semantic follow-up JSON was not an object.")
	return obj, False


def run_semantic_followup_engine(request: FollowUpInterpretRequest, settings: Settings) -> FollowUpInterpretResponse:
	messages = [
		{"role": "system", "content": _system_prompt()},
		{"role": "user", "content": _user_prompt(request)},
	]
	last_error = ""
	total_latency_ms = 0
	last_status_code = 0
	used_json_repair = False
	obj: Dict[str, Any] | None = None
	attempt = 0
	for attempt in range(1, settings.semantic_followup_max_attempts + 1):
		try:
			data, status_code, latency_ms = _chat_completion_json(settings, messages)
			last_status_code = status_code
			total_latency_ms += latency_ms
			obj, repaired = _extract_json_content(data)
			used_json_repair = used_json_repair or repaired
			break
		except SemanticFollowUpEngineError as exc:
			last_error = str(exc)
			if attempt >= settings.semantic_followup_max_attempts:
				raise
			time.sleep(min(2.0, (settings.semantic_followup_backoff_ms * attempt) / 1000.0))
	if obj is None:
		raise SemanticFollowUpEngineError(last_error or "Semantic follow-up engine failed.")

	interpretation = FollowUpInterpretation(
		requested_modes=[str(x or "").strip() for x in (obj.get("requested_modes") or []) if str(x or "").strip()],
		target_dimension=str(obj.get("target_dimension") or "").strip(),
		target_limit=int(max(0, obj.get("target_limit") or 0)),
		sort_direction=str(obj.get("sort_direction") or "").strip().lower(),
		target_capability_id=str(obj.get("target_capability_id") or "").strip(),
		self_contained=bool(obj.get("self_contained")),
		confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
		reason=str(obj.get("reason") or "").strip(),
	)
	return FollowUpInterpretResponse(
		ok=True,
		interpretation=interpretation,
		agent_meta={
			"engine": "semantic_followup",
			"model": settings.effective_semantic_followup_model(),
			"telemetry": {
				"attempt_count": attempt,
				"latency_ms": total_latency_ms,
				"provider_status_code": last_status_code,
				"used_json_repair": used_json_repair,
			},
		},
		error="",
	)
