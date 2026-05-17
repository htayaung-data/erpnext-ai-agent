from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests

from app.schemas import (
	BusinessUnderstandingCandidate,
	BusinessUnderstandingInterpretRequest,
	BusinessUnderstandingInterpretResponse,
	BusinessUnderstandingInterpretation,
)
from app.settings import Settings


class SemanticBusinessUnderstandingEngineError(RuntimeError):
	pass


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _system_prompt() -> str:
	return """You are the Natural Business Understanding interpreter for an ERP assistant.
Return only a single compact JSON object with these keys:
- detected_language: string
- selected_candidate_id: string
- candidate_interpretations: array of objects
- reason: short string

Each candidate_interpretations object must use these keys:
- candidate_id: string
- intent_scope: string
- business_domain: string
- requested_action: string
- target_reference: string
- target_entity: object
- candidate_route: string
- candidate_capability_ids: array of strings
- candidate_report_names: array of strings
- candidate_composite_family_ids: array of strings
- requested_metrics: array of strings
- requested_dimensions: array of strings
- requested_time_scope: string
- evidence_need: string
- authority_class: string
- model_confidence: number from 0 to 1
- model_reason: short string

Rules:
- Return ranked candidate interpretations only. Do not answer the user.
- Use interpretation_context.allowed_values whenever a controlled value applies.
- Use only capability ids, report names, and composite family ids present in interpretation_context.metadata_context when possible.
- Preserve a future business_domain if the user clearly asks for a domain not yet present in metadata.
- If the user asks "that", "first", "rank 2", "above table", or similar, mark the target_reference rather than guessing the entity.
- If the user asks for recommendation, prediction, approval, scoring, or causal driver analysis, reflect that in requested_action and authority_class instead of pretending it is a safe read.
- If the question is unclear, return a clarification candidate with evidence_need needs_clarification.
- Do not invent data values, account balances, dates, policies, or final recommendations.
- Keep the JSON valid and schema-aligned."""


def _user_prompt(request: BusinessUnderstandingInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"recent_messages": [{"role": m.role, "content": m.content} for m in request.recent_messages],
		"latest_grounded_turn": request.latest_grounded_turn,
		"latest_assistant_payload": request.latest_assistant_payload,
		"interpretation_context": request.interpretation_context,
	}
	return json.dumps(payload, ensure_ascii=False)


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticBusinessUnderstandingEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": settings.effective_semantic_fresh_query_model(),
		"messages": messages,
		"temperature": 0,
		"max_tokens": max(700, int(settings.semantic_fresh_query_max_tokens or 0)),
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
		raise SemanticBusinessUnderstandingEngineError(f"Semantic business-understanding request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticBusinessUnderstandingEngineError(
			f"Semantic business-understanding returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise SemanticBusinessUnderstandingEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticBusinessUnderstandingEngineError("Semantic business-understanding returned invalid payload.")
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
		raise SemanticBusinessUnderstandingEngineError("Semantic business-understanding response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticBusinessUnderstandingEngineError("Semantic business-understanding response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		repaired_obj, used_repair = _repair_json_content(content)
		if repaired_obj is None:
			raise SemanticBusinessUnderstandingEngineError(
				f"Semantic business-understanding returned invalid JSON: {content[:300]}"
			) from exc
		return repaired_obj, used_repair
	if not isinstance(obj, dict):
		raise SemanticBusinessUnderstandingEngineError("Semantic business-understanding JSON was not an object.")
	return obj, False


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clamp_confidence(value: Any) -> float:
	try:
		numeric = float(value or 0.0)
	except Exception:
		numeric = 0.0
	return max(0.0, min(1.0, numeric))


def _candidate_from_obj(index: int, obj: Any) -> BusinessUnderstandingCandidate | None:
	if not isinstance(obj, dict):
		return None
	return BusinessUnderstandingCandidate(
		candidate_id=_clean_text(obj.get("candidate_id")) or f"candidate-{index + 1}",
		intent_scope=_clean_text(obj.get("intent_scope")) or "unknown",
		business_domain=_clean_text(obj.get("business_domain")),
		requested_action=_clean_text(obj.get("requested_action")) or "unknown",
		target_reference=_clean_text(obj.get("target_reference")) or "none",
		target_entity=_clean_dict(obj.get("target_entity")),
		candidate_route=_clean_text(obj.get("candidate_route")) or "unknown",
		candidate_capability_ids=_clean_list(obj.get("candidate_capability_ids")),
		candidate_report_names=_clean_list(obj.get("candidate_report_names")),
		candidate_composite_family_ids=_clean_list(obj.get("candidate_composite_family_ids")),
		requested_metrics=_clean_list(obj.get("requested_metrics")),
		requested_dimensions=_clean_list(obj.get("requested_dimensions")),
		requested_time_scope=_clean_text(obj.get("requested_time_scope")),
		evidence_need=_clean_text(obj.get("evidence_need")) or "unknown",
		authority_class=_clean_text(obj.get("authority_class")) or "unknown",
		model_confidence=_clamp_confidence(obj.get("model_confidence")),
		model_reason=_clean_text(obj.get("model_reason")),
	)


def run_semantic_business_understanding_engine(
	request: BusinessUnderstandingInterpretRequest,
	settings: Settings,
) -> BusinessUnderstandingInterpretResponse:
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
	for attempt in range(1, settings.semantic_fresh_query_max_attempts + 1):
		try:
			data, status_code, latency_ms = _chat_completion_json(settings, messages)
			last_status_code = status_code
			total_latency_ms += latency_ms
			obj, repaired = _extract_json_content(data)
			used_json_repair = used_json_repair or repaired
			break
		except SemanticBusinessUnderstandingEngineError as exc:
			last_error = str(exc)
			if attempt >= settings.semantic_fresh_query_max_attempts:
				raise
			time.sleep(min(2.0, (settings.semantic_fresh_query_backoff_ms * attempt) / 1000.0))
	if obj is None:
		raise SemanticBusinessUnderstandingEngineError(last_error or "Semantic business-understanding engine failed.")

	raw_candidates = obj.get("candidate_interpretations")
	if not isinstance(raw_candidates, list):
		raw_candidates = []
	candidates = [
		candidate
		for index, raw_candidate in enumerate(raw_candidates[:5])
		for candidate in [_candidate_from_obj(index, raw_candidate)]
		if candidate is not None
	]
	selected_candidate_id = _clean_text(obj.get("selected_candidate_id"))
	if not selected_candidate_id and candidates:
		selected_candidate_id = candidates[0].candidate_id

	return BusinessUnderstandingInterpretResponse(
		ok=True,
		interpretation=BusinessUnderstandingInterpretation(
			detected_language=_clean_text(obj.get("detected_language")) or "en",
			candidate_interpretations=candidates,
			selected_candidate_id=selected_candidate_id,
			reason=_clean_text(obj.get("reason")),
		),
		agent_meta={
			"engine": "semantic_business_understanding",
			"model": settings.effective_semantic_fresh_query_model(),
			"shadow_mode": True,
			"telemetry": {
				"attempt_count": attempt,
				"latency_ms": total_latency_ms,
				"provider_status_code": last_status_code,
				"used_json_repair": used_json_repair,
				"candidate_count": len(candidates),
			},
		},
		error="",
	)
