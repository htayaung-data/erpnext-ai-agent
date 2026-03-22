from __future__ import annotations

import json
import time
from concurrent.futures import Future, TimeoutError as FutureTimeoutError
from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from threading import Lock
from typing import Any, Dict, List

import requests

from app.schemas import (
	FreshQueryInterpretRequest,
	FreshQueryInterpretResponse,
	FreshQueryInterpretation,
)
from app.settings import Settings


class SemanticFreshQueryEngineError(RuntimeError):
	pass


RUNTIME_DEFAULT_MODEL_OVERRIDE = "__runtime_default__"


_CACHE_LOCK = Lock()
_FRESH_QUERY_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_INFLIGHT_LOCK = Lock()
_INFLIGHT_FRESH_QUERY: Dict[str, Future] = {}


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _extra_body(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {"enable_thinking": False}
	return {"chat_template_kwargs": {"enable_thinking": False}}


def _effective_model(settings: Settings, request: FreshQueryInterpretRequest) -> str:
	override = str(getattr(request, "model_override", "") or "").strip()
	if override == RUNTIME_DEFAULT_MODEL_OVERRIDE:
		return str(settings.qwen_model or "").strip()
	if override:
		return override
	return settings.effective_semantic_fresh_query_model()


def _system_prompt() -> str:
	return """You interpret first-turn ERP business requests into a governed proposal contract.
Return only a single JSON object with these keys:
- intent_class: string
- candidate_capability_ids: array of strings
- candidate_reports: array of strings
- requested_dimensions: array of strings
- requested_metrics: array of strings
- requested_time_scope: string
- requested_presentation: array of strings
- extracted_slots: object
- ambiguity_flags: array of strings
- ambiguity_reason: string
- confidence: number from 0 to 1

Rules:
- Use only intent_class values from interpretation_context.intent_classes.
- Use only capability ids from interpretation_context.capabilities.
- Use only report names, dimensions, and metrics that are present in the chosen governed capability definitions.
- candidate_reports are advisory only. Never assume they will be executed directly.
- Never ask for or output a company filter. Company is injected by the system.
- If a request is underspecified, use ambiguity_flags and ambiguity_reason instead of guessing.
- Use requested_presentation only for display requests such as table or million display.
- Keep extracted_slots compact. Allowed top-level slot keys are report_date, from_date, to_date, and filters.
- If you use extracted_slots.filters, never include company inside filters.
- Keep the JSON compact, valid, and schema-aligned."""


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _normalized_lookup(values: List[str]) -> Dict[str, str]:
	out: Dict[str, str] = {}
	for value in values:
		clean = str(value or "").strip()
		if clean:
			out[_normalize_key(clean)] = clean
	return out


def _capability_scope(
	intent_class: str,
	candidate_capability_ids: List[str],
	context: Dict[str, Any],
) -> List[Dict[str, Any]]:
	capabilities = [
		dict(item)
		for item in (context.get("capabilities") or [])
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	]
	if candidate_capability_ids:
		selected = {
			str(capability_id or "").strip()
			for capability_id in candidate_capability_ids
			if str(capability_id or "").strip()
		}
		return [item for item in capabilities if str(item.get("capability_id") or "").strip() in selected]
	if intent_class:
		return [
			item
			for item in capabilities
			if intent_class in _clean_list(item.get("intent_classes"))
		]
	return capabilities


def _canonicalize_interpretation_obj(
	obj: Dict[str, Any],
	request: FreshQueryInterpretRequest,
) -> Dict[str, Any] | None:
	context = request.interpretation_context if isinstance(request.interpretation_context, dict) else {}
	if not isinstance(obj, dict):
		return None

	intent_lookup = _normalized_lookup(
		[
			str(item.get("intent_class_id") or "").strip()
			for item in (context.get("intent_classes") or [])
			if isinstance(item, dict)
		]
	)
	raw_intent_class = str(obj.get("intent_class") or "").strip()
	intent_class = intent_lookup.get(_normalize_key(raw_intent_class), "")

	capabilities = [
		dict(item)
		for item in (context.get("capabilities") or [])
		if isinstance(item, dict)
	]
	capability_lookup = _normalized_lookup(
		[str(item.get("capability_id") or "").strip() for item in capabilities]
	)
	candidate_capability_ids: List[str] = []
	for value in _clean_list(obj.get("candidate_capability_ids")):
		canonical = capability_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		candidate_capability_ids.append(canonical)
	candidate_capability_ids = list(dict.fromkeys(candidate_capability_ids))

	for capability_id in candidate_capability_ids:
		spec = next(
			(
				item
				for item in capabilities
				if str(item.get("capability_id") or "").strip() == capability_id
			),
			{},
		)
		if intent_class and intent_class not in _clean_list(spec.get("intent_classes")):
			return None

	scoped_capabilities = _capability_scope(intent_class, candidate_capability_ids, context)
	report_lookup = _normalized_lookup(
		[
			report_name
			for capability in scoped_capabilities
			for report_name in _clean_list(capability.get("report_names"))
		]
	)
	if not report_lookup:
		report_lookup = _normalized_lookup(
			[
				report_name
				for capability in capabilities
				for report_name in _clean_list(capability.get("report_names"))
			]
		)
	candidate_reports: List[str] = []
	for value in _clean_list(obj.get("candidate_reports"))[:3]:
		canonical = report_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		candidate_reports.append(canonical)
	candidate_reports = list(dict.fromkeys(candidate_reports))

	dimension_lookup = _normalized_lookup(
		[
			dimension
			for capability in scoped_capabilities
			for dimension in _clean_list(capability.get("dimensions"))
		]
	)
	metric_lookup = _normalized_lookup(
		[
			metric
			for capability in scoped_capabilities
			for metric in _clean_list(capability.get("metrics"))
		]
	)
	requested_dimensions: List[str] = []
	for value in _clean_list(obj.get("requested_dimensions")):
		canonical = dimension_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_dimensions.append(canonical)
	requested_dimensions = list(dict.fromkeys(requested_dimensions))

	requested_metrics: List[str] = []
	for value in _clean_list(obj.get("requested_metrics")):
		canonical = metric_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_metrics.append(canonical)
	requested_metrics = list(dict.fromkeys(requested_metrics))

	presentation_lookup = _normalized_lookup(_clean_list(context.get("allowed_presentations")))
	requested_presentation: List[str] = []
	for value in _clean_list(obj.get("requested_presentation")):
		canonical = presentation_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_presentation.append(canonical)
	requested_presentation = list(dict.fromkeys(requested_presentation))

	ambiguity_lookup = _normalized_lookup(_clean_list(context.get("allowed_ambiguity_flags")))
	ambiguity_flags: List[str] = []
	for value in _clean_list(obj.get("ambiguity_flags")):
		canonical = ambiguity_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		ambiguity_flags.append(canonical)
	ambiguity_flags = list(dict.fromkeys(ambiguity_flags))

	extracted_slots = obj.get("extracted_slots")
	if not isinstance(extracted_slots, dict):
		extracted_slots = {}
	clean_slots: Dict[str, Any] = {}
	for key in ("report_date", "from_date", "to_date"):
		value = extracted_slots.get(key)
		if isinstance(value, str) and value.strip():
			clean_slots[key] = value.strip()
	slot_filters = extracted_slots.get("filters")
	if isinstance(slot_filters, dict):
		filters = {
			str(key or "").strip(): value
			for key, value in slot_filters.items()
			if str(key or "").strip() and str(key or "").strip().lower() != "company"
		}
		if filters:
			clean_slots["filters"] = filters

	try:
		confidence = float(obj.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	ambiguity_reason = str(obj.get("ambiguity_reason") or "").strip()
	requested_time_scope = str(obj.get("requested_time_scope") or "").strip()

	if not any(
		[
			intent_class,
			candidate_capability_ids,
			candidate_reports,
			requested_dimensions,
			requested_metrics,
			requested_time_scope,
			requested_presentation,
			ambiguity_flags,
			ambiguity_reason,
		]
	):
		return None

	return {
		"intent_class": intent_class,
		"candidate_capability_ids": candidate_capability_ids,
		"candidate_reports": candidate_reports,
		"requested_dimensions": requested_dimensions,
		"requested_metrics": requested_metrics,
		"requested_time_scope": requested_time_scope,
		"requested_presentation": requested_presentation,
		"extracted_slots": clean_slots,
		"ambiguity_flags": ambiguity_flags,
		"ambiguity_reason": ambiguity_reason,
		"confidence": confidence,
	}


def _user_prompt(request: FreshQueryInterpretRequest) -> str:
	payload = {
		"message": request.message,
		"interpretation_context": request.interpretation_context,
	}
	if request.recent_messages:
		payload["recent_messages"] = [
			{"role": m.role, "content": m.content}
			for m in request.recent_messages
		]
	return json.dumps(payload, ensure_ascii=False)


def _cache_enabled(settings: Settings) -> bool:
	return (
		int(max(0, settings.semantic_fresh_query_cache_ttl_seconds)) > 0
		and int(max(0, settings.semantic_fresh_query_cache_max_entries)) > 0
	)


def _cache_key(request: FreshQueryInterpretRequest, settings: Settings) -> str:
	payload = {
		"model": _effective_model(settings, request),
		"site_name": request.site_name,
		"message": request.message,
		"recent_messages": [
			{"role": m.role, "content": m.content}
			for m in request.recent_messages
		],
		"interpretation_context": request.interpretation_context,
		"system_prompt": _system_prompt(),
	}
	serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
	return sha256(serialized.encode("utf-8")).hexdigest()


def _prune_cache(now: float) -> None:
	expired_keys = [
		key
		for key, entry in _FRESH_QUERY_CACHE.items()
		if float(entry.get("expires_at") or 0.0) <= now
	]
	for key in expired_keys:
		_FRESH_QUERY_CACHE.pop(key, None)


def _cache_get(cache_key: str, settings: Settings) -> tuple[Dict[str, Any] | None, int]:
	if not _cache_enabled(settings):
		return None, 0
	now = time.monotonic()
	with _CACHE_LOCK:
		_prune_cache(now)
		entry = _FRESH_QUERY_CACHE.get(cache_key)
		if not isinstance(entry, dict):
			return None, 0
		_FRESH_QUERY_CACHE.move_to_end(cache_key)
		age_ms = int(max(0.0, (now - float(entry.get("created_at") or now)) * 1000.0))
		payload = entry.get("response")
		return (deepcopy(payload) if isinstance(payload, dict) else None), age_ms


def _cache_put(cache_key: str, response_payload: Dict[str, Any], settings: Settings) -> None:
	if not _cache_enabled(settings):
		return
	now = time.monotonic()
	with _CACHE_LOCK:
		_prune_cache(now)
		_FRESH_QUERY_CACHE[cache_key] = {
			"created_at": now,
			"expires_at": now + float(max(0, settings.semantic_fresh_query_cache_ttl_seconds)),
			"response": deepcopy(response_payload),
		}
		_FRESH_QUERY_CACHE.move_to_end(cache_key)
		while len(_FRESH_QUERY_CACHE) > int(max(0, settings.semantic_fresh_query_cache_max_entries)):
			_FRESH_QUERY_CACHE.popitem(last=False)


def _acquire_inflight_future(cache_key: str) -> tuple[Future, bool]:
	with _INFLIGHT_LOCK:
		existing = _INFLIGHT_FRESH_QUERY.get(cache_key)
		if existing is not None:
			return existing, False
		future: Future = Future()
		_INFLIGHT_FRESH_QUERY[cache_key] = future
		return future, True


def _resolve_inflight_future(
	cache_key: str,
	future: Future,
	*,
	response_payload: Dict[str, Any] | None = None,
	error: Exception | None = None,
) -> None:
	with _INFLIGHT_LOCK:
		current = _INFLIGHT_FRESH_QUERY.get(cache_key)
		if current is future:
			_INFLIGHT_FRESH_QUERY.pop(cache_key, None)
	if future.done():
		return
	if error is not None:
		future.set_exception(error)
		return
	future.set_result(deepcopy(response_payload) if isinstance(response_payload, dict) else {})


def _inflight_wait_timeout_seconds(settings: Settings) -> int:
	base = max(15, int(settings.semantic_fresh_query_timeout_seconds))
	attempts = max(1, int(settings.semantic_fresh_query_max_attempts))
	return base * attempts + 5


def _chat_completion_json(settings: Settings, messages: List[Dict[str, Any]]) -> tuple[Dict[str, Any], int, int]:
	return _chat_completion_json_for_model(settings, messages, settings.effective_semantic_fresh_query_model())


def _chat_completion_json_for_model(
	settings: Settings,
	messages: List[Dict[str, Any]],
	model_name: str,
) -> tuple[Dict[str, Any], int, int]:
	if not settings.qwen_base_url:
		raise SemanticFreshQueryEngineError("QWEN_BASE_URL is not configured.")
	url = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
	headers = {
		"Content-Type": "application/json",
		"Authorization": f"Bearer {settings.qwen_api_key or 'EMPTY'}",
	}
	payload = {
		"model": str(model_name or settings.effective_semantic_fresh_query_model() or "").strip(),
		"messages": messages,
		"temperature": 0,
		"max_tokens": max(64, int(settings.semantic_fresh_query_max_tokens or 160)),
		"response_format": {"type": "json_object"},
		"extra_body": _extra_body(settings),
	}
	start = time.perf_counter()
	try:
		resp = requests.post(
			url,
			headers=headers,
			data=json.dumps(payload),
			timeout=max(15, settings.semantic_fresh_query_timeout_seconds),
		)
	except requests.RequestException as exc:
		raise SemanticFreshQueryEngineError(f"Semantic fresh-query request failed: {exc}") from exc
	latency_ms = int((time.perf_counter() - start) * 1000)
	try:
		data = resp.json()
	except Exception as exc:
		raise SemanticFreshQueryEngineError(
			f"Semantic fresh-query returned non-JSON response ({resp.status_code})."
		) from exc
	if resp.status_code >= 400:
		raise SemanticFreshQueryEngineError(str(data)[:500])
	if not isinstance(data, dict):
		raise SemanticFreshQueryEngineError("Semantic fresh-query returned invalid payload.")
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
		raise SemanticFreshQueryEngineError("Semantic fresh-query response contained no choices.")
	message = choices[0].get("message") if isinstance(choices[0], dict) else {}
	content = str((message or {}).get("content") or "").strip()
	if not content:
		raise SemanticFreshQueryEngineError("Semantic fresh-query response was empty.")
	try:
		obj = json.loads(content)
	except Exception as exc:
		repaired_obj, used_repair = _repair_json_content(content)
		if repaired_obj is None:
			raise SemanticFreshQueryEngineError(
				f"Semantic fresh-query returned invalid JSON: {content[:300]}"
			) from exc
		return repaired_obj, used_repair
	if not isinstance(obj, dict):
		raise SemanticFreshQueryEngineError("Semantic fresh-query JSON was not an object.")
	return obj, False


def run_semantic_fresh_query_engine(
	request: FreshQueryInterpretRequest,
	settings: Settings,
) -> FreshQueryInterpretResponse:
	cache_key = _cache_key(request, settings)
	cached_payload, cache_age_ms = _cache_get(cache_key, settings)
	if isinstance(cached_payload, dict):
		agent_meta = cached_payload.get("agent_meta") if isinstance(cached_payload.get("agent_meta"), dict) else {}
		telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
		source_latency_ms = int(max(0, telemetry.get("source_latency_ms") or telemetry.get("latency_ms") or 0))
		cached_payload["agent_meta"] = {
			**agent_meta,
			"telemetry": {
				**telemetry,
				"attempt_count": 0,
				"latency_ms": 0,
				"cache_hit": True,
				"shared_inflight_hit": False,
				"inflight_wait_ms": 0,
				"cache_age_ms": cache_age_ms,
				"source_latency_ms": source_latency_ms,
			},
		}
		return FreshQueryInterpretResponse(**cached_payload)

	future, is_owner = _acquire_inflight_future(cache_key)
	if not is_owner:
		wait_started = time.perf_counter()
		try:
			shared_payload = future.result(timeout=_inflight_wait_timeout_seconds(settings))
		except FutureTimeoutError as exc:
			raise SemanticFreshQueryEngineError(
				"Semantic fresh-query wait on matching in-flight request timed out."
			) from exc
		except Exception as exc:
			raise SemanticFreshQueryEngineError(
				f"Semantic fresh-query shared in-flight request failed: {exc}"
			) from exc
		wait_ms = int((time.perf_counter() - wait_started) * 1000)
		agent_meta = shared_payload.get("agent_meta") if isinstance(shared_payload.get("agent_meta"), dict) else {}
		telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
		source_latency_ms = int(max(0, telemetry.get("source_latency_ms") or telemetry.get("latency_ms") or 0))
		shared_payload["agent_meta"] = {
			**agent_meta,
			"telemetry": {
				**telemetry,
				"attempt_count": 0,
				"latency_ms": wait_ms,
				"cache_hit": False,
				"shared_inflight_hit": True,
				"inflight_wait_ms": wait_ms,
				"cache_age_ms": 0,
				"source_latency_ms": source_latency_ms,
			},
		}
		return FreshQueryInterpretResponse(**shared_payload)

	try:
		model_name = _effective_model(settings, request)
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
				data, status_code, latency_ms = _chat_completion_json_for_model(settings, messages, model_name)
				last_status_code = status_code
				total_latency_ms += latency_ms
				obj, repaired = _extract_json_content(data)
				used_json_repair = used_json_repair or repaired
				break
			except SemanticFreshQueryEngineError as exc:
				last_error = str(exc)
				if attempt >= settings.semantic_fresh_query_max_attempts:
					raise
				time.sleep(min(2.0, (settings.semantic_fresh_query_backoff_ms * attempt) / 1000.0))
		if obj is None:
			raise SemanticFreshQueryEngineError(last_error or "Semantic fresh-query engine failed.")
		canonical_obj = _canonicalize_interpretation_obj(obj, request)
		if canonical_obj is None:
			raise SemanticFreshQueryEngineError(
				"Semantic fresh-query response did not pass governed runtime validation."
			)
		obj = canonical_obj

		extracted_slots = obj.get("extracted_slots")
		if not isinstance(extracted_slots, dict):
			extracted_slots = {}
		filters = extracted_slots.get("filters")
		if not isinstance(filters, dict):
			filters = {}
		else:
			filters = {
				str(key or "").strip(): value
				for key, value in filters.items()
				if str(key or "").strip() and str(key or "").strip().lower() != "company"
			}
		extracted_slots = {
			**{
				key: value
				for key, value in extracted_slots.items()
				if str(key or "").strip() in {"report_date", "from_date", "to_date"}
			},
		}
		if filters:
			extracted_slots["filters"] = filters

		interpretation = FreshQueryInterpretation(
			intent_class=str(obj.get("intent_class") or "").strip(),
			candidate_capability_ids=[
				str(x or "").strip()
				for x in (obj.get("candidate_capability_ids") or [])
				if str(x or "").strip()
			],
			candidate_reports=[
				str(x or "").strip()
				for x in (obj.get("candidate_reports") or [])
				if str(x or "").strip()
			],
			requested_dimensions=[
				str(x or "").strip()
				for x in (obj.get("requested_dimensions") or [])
				if str(x or "").strip()
			],
			requested_metrics=[
				str(x or "").strip()
				for x in (obj.get("requested_metrics") or [])
				if str(x or "").strip()
			],
			requested_time_scope=str(obj.get("requested_time_scope") or "").strip(),
			requested_presentation=[
				str(x or "").strip()
				for x in (obj.get("requested_presentation") or [])
				if str(x or "").strip()
			],
			extracted_slots=extracted_slots,
			ambiguity_flags=[
				str(x or "").strip()
				for x in (obj.get("ambiguity_flags") or [])
				if str(x or "").strip()
			],
			ambiguity_reason=str(obj.get("ambiguity_reason") or "").strip(),
			confidence=max(0.0, min(1.0, float(obj.get("confidence") or 0.0))),
		)
		response = FreshQueryInterpretResponse(
			ok=True,
			interpretation=interpretation,
			agent_meta={
				"engine": "semantic_fresh_query",
				"model": model_name,
				"telemetry": {
					"attempt_count": attempt,
					"latency_ms": total_latency_ms,
					"provider_status_code": last_status_code,
					"cache_hit": False,
					"shared_inflight_hit": False,
					"inflight_wait_ms": 0,
					"cache_age_ms": 0,
					"source_latency_ms": total_latency_ms,
					"used_json_repair": used_json_repair,
				},
			},
			error="",
		)
		response_payload = response.model_dump() if hasattr(response, "model_dump") else response.dict()
		_cache_put(cache_key, response_payload, settings)
		_resolve_inflight_future(cache_key, future, response_payload=response_payload)
		return response
	except Exception as exc:
		_resolve_inflight_future(cache_key, future, error=exc if isinstance(exc, Exception) else RuntimeError(str(exc)))
		raise
