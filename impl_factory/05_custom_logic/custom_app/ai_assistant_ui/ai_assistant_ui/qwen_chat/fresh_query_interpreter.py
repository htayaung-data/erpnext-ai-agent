from __future__ import annotations

import datetime as dt
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List

import requests

from ai_assistant_ui.qwen_chat.compiler import CompilerOutcome, compile_fresh_query
from ai_assistant_ui.qwen_chat.contracts import (
	FreshQueryInterpretationContract,
	build_compiled_execution_audit_contract,
	build_fresh_query_interpretation_contract,
	build_interaction_contract,
	build_response_policy_contract,
)
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_validator import validate_normalized_family_artifact
from ai_assistant_ui.qwen_chat.metadata import list_capability_specs, list_intent_class_specs
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_chat,
	call_qwen_runtime_fresh_query_interpretation,
)
from ai_assistant_ui.qwen_chat.semantic_validator import (
	run_phase4_semantic_validation_selftests,
	validate_compiled_semantic_result,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


_ALLOWED_PRESENTATION_MODES = {"presentation_transform", "table_presentation"}
_ALLOWED_AMBIGUITY_FLAGS = {
	"missing_time_scope",
	"missing_metric",
	"missing_dimension",
	"ambiguous_business_object",
	"ambiguous_capability",
	"ambiguous_report",
	"underspecified_request",
	"unsupported_request",
}
_RUNTIME_DEFAULT_MODEL_OVERRIDE = "__runtime_default__"


@dataclass(frozen=True)
class SemanticFreshQueryResult:
	status: str
	interpretation: FreshQueryInterpretationContract | None = None
	confidence_threshold: float = 0.72
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_fresh_query_interpretation",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"interpretation": self.interpretation.to_payload() if self.interpretation else {},
			"agent_meta": self.agent_meta if isinstance(self.agent_meta, dict) else {},
		}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(x or "").strip() for x in values if str(x or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return text.strip("_")


def _normalized_lookup(values: List[str]) -> Dict[str, str]:
	out: Dict[str, str] = {}
	for value in values:
		clean = str(value or "").strip()
		if not clean:
			continue
		out[_normalize_key(clean)] = clean
	return out


def _normalize_time_scope(value: Any) -> str:
	key = _normalize_key(value)
	if not key:
		return ""
	if key in {"as_of_today", "as_of_now", "today", "now", "current_date", "current_date_utc"}:
		return "as_of_today"
	if key in {"current_period", "this_period", "this_month", "current_month"}:
		return "current_period"
	if key in {"last_month", "previous_month", "prior_month"}:
		return "last_month"
	if key in {"current_fiscal_year_to_date", "fiscal_year_to_date", "year_to_date", "this_fiscal_year"}:
		return "current_fiscal_year_to_date"
	if key in {"all_period", "all_time", "overall"}:
		return "all_period"
	return key


def _confidence_threshold() -> float:
	default = 0.72
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_fresh_query_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _current_date_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _build_interpretation_context() -> Dict[str, Any]:
	intent_classes = [
		{
			"intent_class_id": str(item.get("intent_class_id") or "").strip(),
			"semantic_tags": _clean_list(item.get("semantic_tags")),
		}
		for item in list_intent_class_specs()
		if isinstance(item, dict) and str(item.get("intent_class_id") or "").strip()
	]
	capabilities = [
		{
			"capability_id": str(item.get("capability_id") or "").strip(),
			"intent_classes": _clean_list(item.get("intent_classes")),
			"report_names": _clean_list(item.get("report_names")),
			"dimensions": _clean_list(item.get("dimensions")),
			"metrics": _clean_list(item.get("metrics")),
			"ontology_concepts": _clean_list(item.get("ontology_concepts")),
		}
		for item in list_capability_specs()
		if isinstance(item, dict) and str(item.get("capability_id") or "").strip()
	]
	return {
		"current_date_utc": _current_date_iso(),
		"single_company_mode": True,
		"company_handling": "compiler_injected_invariant",
		"intent_classes": intent_classes,
		"capabilities": capabilities,
		"allowed_presentations": sorted(_ALLOWED_PRESENTATION_MODES),
		"allowed_ambiguity_flags": sorted(_ALLOWED_AMBIGUITY_FLAGS),
	}


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


def _validate_semantic_payload(
	*,
	request_id: str,
	session_id: str,
	payload: Dict[str, Any],
	context: Dict[str, Any],
) -> FreshQueryInterpretationContract | None:
	if not isinstance(payload, dict):
		return None

	intent_lookup = _normalized_lookup(
		[
			str(item.get("intent_class_id") or "").strip()
			for item in (context.get("intent_classes") or [])
			if isinstance(item, dict)
		]
	)
	raw_intent_class = str(payload.get("intent_class") or "").strip()
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
	for value in _clean_list(payload.get("candidate_capability_ids")):
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
	for value in _clean_list(payload.get("candidate_reports"))[:3]:
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
	for value in _clean_list(payload.get("requested_dimensions")):
		canonical = dimension_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_dimensions.append(canonical)
	requested_dimensions = list(dict.fromkeys(requested_dimensions))

	requested_metrics: List[str] = []
	for value in _clean_list(payload.get("requested_metrics")):
		canonical = metric_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_metrics.append(canonical)
	requested_metrics = list(dict.fromkeys(requested_metrics))

	presentation_lookup = _normalized_lookup(sorted(_ALLOWED_PRESENTATION_MODES))
	requested_presentation: List[str] = []
	for value in _clean_list(payload.get("requested_presentation")):
		canonical = presentation_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		requested_presentation.append(canonical)
	requested_presentation = list(dict.fromkeys(requested_presentation))

	ambiguity_lookup = _normalized_lookup(sorted(_ALLOWED_AMBIGUITY_FLAGS))
	ambiguity_flags: List[str] = []
	for value in _clean_list(payload.get("ambiguity_flags")):
		canonical = ambiguity_lookup.get(_normalize_key(value), "")
		if not canonical:
			return None
		ambiguity_flags.append(canonical)
	ambiguity_flags = list(dict.fromkeys(ambiguity_flags))

	extracted_slots = payload.get("extracted_slots")
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
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	requested_time_scope = _normalize_time_scope(payload.get("requested_time_scope"))
	ambiguity_reason = str(payload.get("ambiguity_reason") or "").strip()

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

	return build_fresh_query_interpretation_contract(
		request_id=request_id,
		session_id=session_id,
		intent_class=intent_class,
		candidate_capability_ids=candidate_capability_ids,
		candidate_reports=candidate_reports,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=requested_time_scope,
		requested_presentation=requested_presentation,
		extracted_slots=clean_slots,
		ambiguity_flags=ambiguity_flags,
		ambiguity_reason=ambiguity_reason,
		confidence=confidence,
	)


def interpret_fresh_query_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	model_override: str = "",
) -> SemanticFreshQueryResult:
	threshold = _confidence_threshold()
	context = _build_interpretation_context()
	try:
		data = call_qwen_runtime_fresh_query_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			interpretation_context=context,
			model_override=model_override,
		)
	except QwenRuntimeClientError as exc:
		return SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	agent_meta = data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {}
	if data.get("ok") is False:
		return SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(data.get("error") or "Runtime fresh-query interpreter returned an error.").strip(),
			agent_meta=agent_meta,
		)
	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticFreshQueryResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime fresh-query interpreter returned no valid interpretation object.",
			agent_meta=agent_meta,
		)

	contract = _validate_semantic_payload(
		request_id=request_id,
		session_id=session_id,
		payload=interpretation,
		context=context,
	)
	if contract is None:
		return SemanticFreshQueryResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime fresh-query interpretation did not pass governed validation.",
			agent_meta=agent_meta,
		)

	if contract.confidence < threshold:
		return SemanticFreshQueryResult(
			status="low_confidence",
			interpretation=contract,
			confidence_threshold=threshold,
			validation_error="Semantic fresh-query interpretation fell below the governed confidence threshold.",
			agent_meta=agent_meta,
		)

	return SemanticFreshQueryResult(
		status="accepted",
		interpretation=contract,
		confidence_threshold=threshold,
		agent_meta=agent_meta,
	)


def _merge_fallback_agent_meta(
	primary: Dict[str, Any],
	fallback: Dict[str, Any],
	primary_status: str,
) -> Dict[str, Any]:
	merged = dict(fallback or {})
	telemetry = merged.get("telemetry") if isinstance(merged.get("telemetry"), dict) else {}
	merged["telemetry"] = {
		**telemetry,
		"fallback_attempted": True,
		"fallback_used": True,
		"primary_status": str(primary_status or "").strip(),
		"primary_model": str((primary or {}).get("model") or "").strip(),
		"primary_latency_ms": int(
			max(
				0,
				(
					((primary or {}).get("telemetry") or {}).get("latency_ms")
					if isinstance((primary or {}).get("telemetry"), dict)
					else 0
				)
				or 0,
			)
		),
	}
	return merged


def _should_retry_with_runtime_default(result: SemanticFreshQueryResult, model_override: str) -> bool:
	if str(model_override or "").strip() == _RUNTIME_DEFAULT_MODEL_OVERRIDE:
		return False
	return str(result.status or "").strip() in {"runtime_error", "invalid_response", "low_confidence"}


def compile_from_fresh_query_message(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
	request_id = uuid.uuid4().hex
	interaction_contract = build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=message,
	)
	response_policy = build_response_policy_contract(
		interaction_contract=interaction_contract,
	)
	proposal_started = time.perf_counter()
	semantic_result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=list(recent_messages or []),
	)
	if _should_retry_with_runtime_default(semantic_result, ""):
		fallback_result = interpret_fresh_query_semantically(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			model_override=_RUNTIME_DEFAULT_MODEL_OVERRIDE,
		)
		if fallback_result.interpretation is not None:
			fallback_result = SemanticFreshQueryResult(
				status=fallback_result.status,
				interpretation=fallback_result.interpretation,
				confidence_threshold=fallback_result.confidence_threshold,
				runtime_error=fallback_result.runtime_error,
				validation_error=fallback_result.validation_error,
				agent_meta=_merge_fallback_agent_meta(
					semantic_result.agent_meta,
					fallback_result.agent_meta,
					semantic_result.status,
				),
			)
			semantic_result = fallback_result
	proposal_generation_latency_ms = int((time.perf_counter() - proposal_started) * 1000)
	compilation_latency_ms = 0
	out: Dict[str, Any] = {
		"request_id": request_id,
		"interaction_contract": interaction_contract.to_payload(),
		"response_policy_contract": response_policy.to_payload(),
		"fresh_query_interpretation": semantic_result.to_payload(),
	}
	if semantic_result.interpretation is None:
		out["phase4_latency_breakdown"] = {
			"proposal_generation_latency_ms": proposal_generation_latency_ms,
			"compilation_latency_ms": 0,
		}
		return out
	compilation_started = time.perf_counter()
	compiler_outcome: CompilerOutcome = compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=semantic_result.interpretation,
		response_policy=response_policy.to_runtime_payload(),
	)
	compilation_latency_ms = int((time.perf_counter() - compilation_started) * 1000)
	out["fresh_query_compiler"] = compiler_outcome.compiler_contract.to_payload()
	if compiler_outcome.compiled_request_contract is not None:
		out["compiled_query_request"] = compiler_outcome.compiled_request_contract.to_payload()
	out["phase4_latency_breakdown"] = {
		"proposal_generation_latency_ms": proposal_generation_latency_ms,
		"compilation_latency_ms": compilation_latency_ms,
	}
	return out


def _proposal_cache_hit_from_pipeline(pipeline: Dict[str, Any]) -> bool:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	agent_meta = (
		fresh_query_payload.get("agent_meta")
		if isinstance(fresh_query_payload.get("agent_meta"), dict)
		else {}
	)
	telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
	return bool(telemetry.get("cache_hit"))


def _proposal_shared_inflight_hit_from_pipeline(pipeline: Dict[str, Any]) -> bool:
	fresh_query_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	agent_meta = (
		fresh_query_payload.get("agent_meta")
		if isinstance(fresh_query_payload.get("agent_meta"), dict)
		else {}
	)
	telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
	return bool(telemetry.get("shared_inflight_hit"))


def run_phase4_fresh_query_pipeline_smokes() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	results: List[Dict[str, Any]] = []
	for message in [
		"How much payable amount do we have as of now",
		"Analyze payable amount",
		"Top 5 customers by revenue",
		"Show monthly sales trend in all regions",
	]:
		results.append(
			compile_from_fresh_query_message(
				session_id="phase4-smoke",
				user_id="Administrator",
				site_name=site_name,
				message=message,
				recent_messages=[],
			)
		)
	return {"smokes": results}


def run_phase4_fresh_query_cache_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	message = "How much payable amount do we have as of now"
	first = compile_from_fresh_query_message(
		session_id="phase4-cache-smoke-1",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	second = compile_from_fresh_query_message(
		session_id="phase4-cache-smoke-2",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	first_telemetry = (
		((first.get("fresh_query_interpretation") or {}).get("agent_meta") or {}).get("telemetry")
		if isinstance(first.get("fresh_query_interpretation"), dict)
		else {}
	)
	second_telemetry = (
		((second.get("fresh_query_interpretation") or {}).get("agent_meta") or {}).get("telemetry")
		if isinstance(second.get("fresh_query_interpretation"), dict)
		else {}
	)
	if not isinstance(first_telemetry, dict):
		first_telemetry = {}
	if not isinstance(second_telemetry, dict):
		second_telemetry = {}
	if bool(first_telemetry.get("cache_hit")):
		raise RuntimeError("Fresh-query cache smoke failed: first proposal unexpectedly reported a cache hit.")
	if not bool(second_telemetry.get("cache_hit")):
		raise RuntimeError("Fresh-query cache smoke failed: second proposal did not report a cache hit.")
	return {
		"first": {
			"status": (first.get("fresh_query_interpretation") or {}).get("status")
			if isinstance(first.get("fresh_query_interpretation"), dict)
			else "",
			"telemetry": first_telemetry,
			"phase4_latency_breakdown": first.get("phase4_latency_breakdown"),
		},
		"second": {
			"status": (second.get("fresh_query_interpretation") or {}).get("status")
			if isinstance(second.get("fresh_query_interpretation"), dict)
			else "",
			"telemetry": second_telemetry,
			"phase4_latency_breakdown": second.get("phase4_latency_breakdown"),
		},
	}


def run_phase4_fresh_query_inflight_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	message = "Please show the current total payable amount as of today"
	barrier = threading.Barrier(2)
	context = _build_interpretation_context()
	conf = getattr(frappe, "conf", None) or {}
	base_url = str(conf.get("qwen_agent_runtime_base_url") or "").strip().rstrip("/")
	if not base_url:
		raise RuntimeError("Fresh-query inflight smoke failed: qwen runtime base URL is not configured.")
	headers = {"Content-Type": "application/json"}
	token = str(conf.get("qwen_agent_runtime_api_token") or "").strip()
	if token:
		headers["Authorization"] = f"Bearer {token}"

	def _run(index: int) -> Dict[str, Any]:
		barrier.wait()
		payload = {
			"request_id": f"phase4-inflight-{index}-{uuid.uuid4().hex}",
			"session_id": f"phase4-inflight-smoke-{index}",
			"user_id": "Administrator",
			"site_name": site_name,
			"message": message,
			"recent_messages": [],
			"interpretation_context": context,
		}
		response = requests.post(
			f"{base_url}/interpret-fresh-query",
			headers=headers,
			data=json.dumps(payload),
			timeout=150,
		)
		response.raise_for_status()
		return response.json()

	with ThreadPoolExecutor(max_workers=2) as executor:
		first_future = executor.submit(_run, 1)
		second_future = executor.submit(_run, 2)
		first = first_future.result()
		second = second_future.result()

	def _telemetry(result: Dict[str, Any]) -> Dict[str, Any]:
		agent_meta = result.get("agent_meta") if isinstance(result.get("agent_meta"), dict) else {}
		telemetry = agent_meta.get("telemetry") if isinstance(agent_meta.get("telemetry"), dict) else {}
		return telemetry

	first_telemetry = _telemetry(first)
	second_telemetry = _telemetry(second)
	shared_inflight = bool(first_telemetry.get("shared_inflight_hit")) or bool(second_telemetry.get("shared_inflight_hit"))
	warm_cache = bool(first_telemetry.get("cache_hit")) and bool(second_telemetry.get("cache_hit"))
	if not (shared_inflight or warm_cache):
		raise RuntimeError(
			f"Fresh-query inflight smoke failed: no request reported a shared inflight hit. "
			f"first={first_telemetry!r} second={second_telemetry!r}"
		)
	return {
		"mode": "shared_inflight" if shared_inflight else "warm_cache",
		"first": {
			"telemetry": first_telemetry,
			"phase4_latency_breakdown": first.get("phase4_latency_breakdown"),
		},
		"second": {
			"telemetry": second_telemetry,
			"phase4_latency_breakdown": second.get("phase4_latency_breakdown"),
		},
	}


def run_phase4_fresh_query_interpreter_selftests() -> Dict[str, Any]:
	context = _build_interpretation_context()
	request_id = "selftest-fresh-query"
	session_id = "selftest-session"
	valid_payload = {
		"intent_class": "financial_summary",
		"candidate_capability_ids": ["accounts_payable_read"],
		"candidate_reports": ["Accounts Payable Summary"],
		"requested_dimensions": [],
		"requested_metrics": ["Outstanding"],
		"requested_time_scope": "as_of_today",
		"requested_presentation": [],
		"extracted_slots": {
			"report_date": _current_date_iso(),
			"filters": {
				"company": "Should Be Ignored",
			},
		},
		"ambiguity_flags": [],
		"ambiguity_reason": "",
		"confidence": 0.94,
	}
	contract = _validate_semantic_payload(
		request_id=request_id,
		session_id=session_id,
		payload=valid_payload,
		context=context,
	)
	if contract is None:
		raise RuntimeError("Fresh-query validation selftest failed: valid payload did not validate.")
	if "company" in ((contract.extracted_slots or {}).get("filters") or {}):
		raise RuntimeError("Fresh-query validation selftest failed: company leaked into extracted slot filters.")
	compiler_outcome = compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=contract,
		response_policy={"analysis_level": "none"},
	)
	if compiler_outcome.compiler_contract.decision != "execute":
		raise RuntimeError(
			f"Fresh-query compiler selftest failed: expected execute, got {compiler_outcome.compiler_contract.decision}."
		)

	invalid_payload = {
		"intent_class": "financial_summary",
		"candidate_capability_ids": ["accounts_payable_read"],
		"candidate_reports": ["Accounts Payable Summary"],
		"requested_dimensions": ["Warehouse"],
		"requested_metrics": ["Outstanding"],
		"requested_time_scope": "as_of_today",
		"requested_presentation": [],
		"extracted_slots": {},
		"ambiguity_flags": [],
		"ambiguity_reason": "",
		"confidence": 0.9,
	}
	invalid_contract = _validate_semantic_payload(
		request_id="selftest-invalid",
		session_id=session_id,
		payload=invalid_payload,
		context=context,
	)
	if invalid_contract is not None:
		raise RuntimeError("Fresh-query validation selftest failed: invalid dimension payload was accepted.")

	return {
		"valid_interpretation": contract.to_payload(),
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"invalid_payload_rejected": True,
	}


def run_phase4_compiled_execution_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	message = "How much payable amount do we have as of now"
	result = execute_compiled_fresh_query_message(
		session_id="phase4-compiled-smoke",
		user_id="Administrator",
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	semantic_validation = result.get("semantic_intent_validation")
	if not isinstance(semantic_validation, dict) or str(semantic_validation.get("status") or "").strip() != "pass":
		raise RuntimeError("Compiled execution smoke failed: semantic validation did not pass.")
	return result


def _phase4b_financial_statement_case_result(
	*,
	request_id: str,
	session_id: str,
	site_name: str,
	message: str,
	candidate_report: str,
	requested_metrics: List[str],
) -> Dict[str, Any]:
	response_policy = {"analysis_level": "none"}
	interaction_contract = build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id="Administrator",
		site_name=site_name,
		raw_message=message,
	)
	interpretation = build_fresh_query_interpretation_contract(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		intent_class="financial_statement",
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=[candidate_report],
		requested_dimensions=[],
		requested_metrics=requested_metrics,
		requested_time_scope="current_fiscal_year_to_date",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.95,
	)
	compiler_outcome = compile_fresh_query(
		request_id=interaction_contract.request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy=response_policy,
	)
	runtime_payload: Dict[str, Any] = {}
	if compiler_outcome.compiled_request_contract is not None:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_id,
			user_id="Administrator",
			site_name=site_name,
			message=message,
			recent_messages=[],
			response_policy=response_policy,
			mode="compiled_read_query",
			compiled_query=compiler_outcome.compiled_request_contract.to_payload(),
			request_id=interaction_contract.request_id,
		)
	adapter_outcome = build_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		runtime_payload=runtime_payload,
	)
	family_validation = validate_normalized_family_artifact(
		request_id=interaction_contract.request_id,
		compiler_contract=compiler_outcome.compiler_contract.to_payload(),
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	return {
		"request_id": interaction_contract.request_id,
		"message": message,
		"compiler_contract": compiler_outcome.compiler_contract.to_payload(),
		"compiled_query_request": (
			compiler_outcome.compiled_request_contract.to_payload()
			if compiler_outcome.compiled_request_contract is not None
			else {}
		),
		"runtime_ok": bool(runtime_payload.get("ok")),
		"runtime_answer": str(runtime_payload.get("answer_text") or "").strip(),
		"normalized_family_artifact": (
			adapter_outcome.artifact_contract.to_payload()
			if adapter_outcome.artifact_contract is not None
			else {}
		),
		"family_adapter_status": adapter_outcome.status,
		"family_adapter_errors": list(adapter_outcome.errors),
		"family_validation": family_validation.to_payload() if family_validation else {},
	}


def run_phase4b_financial_statement_family_probe() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	return {
		"pnl": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-pnl",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show me P & L statement, and analyze it",
			candidate_report="Profit and Loss Statement",
			requested_metrics=["Total Income", "Total Expense", "Net Profit"],
		),
		"balance_sheet": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-balance-sheet",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show balance sheet",
			candidate_report="Balance Sheet",
			requested_metrics=["Total Asset", "Total Liability", "Total Equity"],
		),
		"cash_flow": _phase4b_financial_statement_case_result(
			request_id="phase4b-probe-cash-flow",
			session_id="phase4b-financial-family-probe",
			site_name=site_name,
			message="Show cash flow statement",
			candidate_report="Cash Flow",
			requested_metrics=["Net Cash from Operations", "Net Change in Cash"],
		),
	}


def run_phase4b_financial_statement_family_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	cases = [
		{
			"request_id": "phase4b-pnl",
			"message": "Show me P & L statement, and analyze it",
			"intent_class": "financial_statement",
			"candidate_reports": ["Profit and Loss Statement"],
			"requested_metrics": ["Total Income", "Total Expense", "Net Profit"],
		},
		{
			"request_id": "phase4b-balance-sheet",
			"message": "Show balance sheet",
			"intent_class": "financial_statement",
			"candidate_reports": ["Balance Sheet"],
			"requested_metrics": ["Total Asset", "Total Liability", "Total Equity"],
		},
		{
			"request_id": "phase4b-cash-flow",
			"message": "Show cash flow statement",
			"intent_class": "financial_statement",
			"candidate_reports": ["Cash Flow"],
			"requested_metrics": ["Net Cash from Operations", "Net Change in Cash"],
		},
	]
	results: List[Dict[str, Any]] = []
	for item in cases:
		case_result = _phase4b_financial_statement_case_result(
			request_id=str(item.get("request_id") or uuid.uuid4().hex),
			session_id="phase4b-financial-family-smoke",
			site_name=site_name,
			message=str(item.get("message") or "").strip(),
			candidate_report=str((item.get("candidate_reports") or [""])[0] or "").strip(),
			requested_metrics=list(item.get("requested_metrics") or []),
		)
		family_validation = case_result.get("family_validation") if isinstance(case_result.get("family_validation"), dict) else {}
		if str(family_validation.get("status") or "").strip() != "pass":
			raise RuntimeError(
				f"Phase 4B financial family smoke failed: family validation did not pass for `{item.get('message')}`."
			)
		results.append(case_result)
	return {"ok": True, "results": results}


def execute_compiled_fresh_query_message(
	*,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
	total_started = time.perf_counter()
	pipeline = compile_from_fresh_query_message(
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=list(recent_messages or []),
	)
	latency_breakdown = (
		dict(pipeline.get("phase4_latency_breakdown"))
		if isinstance(pipeline.get("phase4_latency_breakdown"), dict)
		else {}
	)
	proposal_generation_latency_ms = int(max(0, latency_breakdown.get("proposal_generation_latency_ms") or 0))
	compilation_latency_ms = int(max(0, latency_breakdown.get("compilation_latency_ms") or 0))
	runtime_execution_latency_ms = 0
	semantic_validation_latency_ms = 0
	normalized_family_artifact_payload: Dict[str, Any] = {}
	family_validation_payload: Dict[str, Any] = {}
	compiled_query = pipeline.get("compiled_query_request")
	compiler_contract = (
		pipeline.get("fresh_query_compiler")
		if isinstance(pipeline.get("fresh_query_compiler"), dict)
		else {}
	)
	if not isinstance(compiled_query, dict) or not compiled_query:
		total_pipeline_latency_ms = int((time.perf_counter() - total_started) * 1000)
		audit_contract = build_compiled_execution_audit_contract(
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
			session_id=session_id,
			compiler_decision=str(compiler_contract.get("decision") or "").strip(),
			compiler_reason=str(compiler_contract.get("compiler_reason") or "").strip(),
			capability_id=str(compiler_contract.get("capability_id") or "").strip(),
			selected_report=str(compiler_contract.get("selected_report") or "").strip(),
			proposal_cache_hit=_proposal_cache_hit_from_pipeline(pipeline),
			proposal_shared_inflight_hit=_proposal_shared_inflight_hit_from_pipeline(pipeline),
			compiled_query_available=False,
			runtime_invoked=False,
			runtime_ok=False,
			grounded_validation_status="not_run",
			semantic_validation_status="not_run",
			proposal_generation_latency_ms=proposal_generation_latency_ms,
			compilation_latency_ms=compilation_latency_ms,
			runtime_execution_latency_ms=0,
			semantic_validation_latency_ms=0,
			total_pipeline_latency_ms=total_pipeline_latency_ms,
			tool_count=0,
			tool_names=[],
		)
		return {
			"pipeline": pipeline,
			"runtime_payload": {},
			"normalized_family_artifact": {},
			"family_validation": {},
			"semantic_intent_validation": {},
			"compiled_execution_audit": audit_contract.to_payload(),
			"phase4_latency_breakdown": {
				"proposal_generation_latency_ms": proposal_generation_latency_ms,
				"compilation_latency_ms": compilation_latency_ms,
				"runtime_execution_latency_ms": 0,
				"semantic_validation_latency_ms": 0,
				"total_pipeline_latency_ms": total_pipeline_latency_ms,
			},
		}
	response_policy = (
		compiled_query.get("response_policy")
		if isinstance(compiled_query.get("response_policy"), dict)
		else {}
	)
	runtime_started = time.perf_counter()
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			response_policy=response_policy,
			mode="compiled_read_query",
			compiled_query=compiled_query,
			request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		)
	except QwenRuntimeClientError as exc:
		runtime_payload = {
			"ok": False,
			"tool_trace": [],
			"agent_meta": {"engine": "unavailable", "mode": "compiled_read_query"},
			"error": str(exc),
		}
	runtime_execution_latency_ms = int((time.perf_counter() - runtime_started) * 1000)
	adapter_outcome = build_normalized_family_artifact(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		compiler_contract=compiler_contract,
		runtime_payload=runtime_payload if isinstance(runtime_payload, dict) else {},
	)
	if adapter_outcome.artifact_contract is not None:
		normalized_family_artifact_payload = adapter_outcome.artifact_contract.to_payload()
	family_validation = validate_normalized_family_artifact(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		compiler_contract=compiler_contract,
		artifact_contract=adapter_outcome.artifact_contract,
		family_id=adapter_outcome.family_id,
		adapter_errors=adapter_outcome.errors,
		adapter_warnings=adapter_outcome.warnings,
	)
	if family_validation is not None:
		family_validation_payload = family_validation.to_payload()
	semantic_validation_payload: Dict[str, Any] = {}
	if isinstance(runtime_payload, dict) and isinstance(runtime_payload.get("tool_trace"), list) and runtime_payload.get("tool_trace"):
		semantic_started = time.perf_counter()
		semantic_validation = validate_compiled_semantic_result(
			interaction_contract=(
				pipeline.get("interaction_contract")
				if isinstance(pipeline.get("interaction_contract"), dict)
				else {}
			),
			interpretation_contract=(
				(pipeline.get("fresh_query_interpretation") or {}).get("interpretation")
				if isinstance(pipeline.get("fresh_query_interpretation"), dict)
				and isinstance((pipeline.get("fresh_query_interpretation") or {}).get("interpretation"), dict)
				else {}
			),
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload if isinstance(runtime_payload, dict) else {},
		)
		semantic_validation_latency_ms = int((time.perf_counter() - semantic_started) * 1000)
		semantic_validation_payload = semantic_validation.to_payload()
	total_pipeline_latency_ms = int((time.perf_counter() - total_started) * 1000)
	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	tool_names = [
		str(item.get("tool") or "").strip()
		for item in tool_trace
		if isinstance(item, dict) and str(item.get("tool") or "").strip()
	]
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	runtime_validation = agent_meta.get("validation") if isinstance(agent_meta.get("validation"), dict) else {}
	audit_contract = build_compiled_execution_audit_contract(
		request_id=str(pipeline.get("request_id") or uuid.uuid4().hex),
		session_id=session_id,
		compiler_decision=str(compiler_contract.get("decision") or "").strip(),
		compiler_reason=str(compiler_contract.get("compiler_reason") or "").strip(),
		capability_id=str(compiler_contract.get("capability_id") or "").strip(),
		selected_report=str(compiler_contract.get("selected_report") or "").strip(),
		proposal_cache_hit=_proposal_cache_hit_from_pipeline(pipeline),
		proposal_shared_inflight_hit=_proposal_shared_inflight_hit_from_pipeline(pipeline),
		compiled_query_available=True,
		runtime_invoked=True,
		runtime_ok=bool(runtime_payload.get("ok")),
		runtime_engine=str(agent_meta.get("engine") or "").strip(),
		runtime_model=str(agent_meta.get("model") or "").strip(),
		grounded_validation_status=str(runtime_validation.get("status") or "unknown").strip(),
		semantic_validation_status=str(semantic_validation_payload.get("status") or "not_run").strip(),
		semantic_validation_errors=(
			semantic_validation_payload.get("errors")
			if isinstance(semantic_validation_payload.get("errors"), list)
			else []
		),
		semantic_validation_warnings=(
			semantic_validation_payload.get("warnings")
			if isinstance(semantic_validation_payload.get("warnings"), list)
			else []
		),
		proposal_generation_latency_ms=proposal_generation_latency_ms,
		compilation_latency_ms=compilation_latency_ms,
		runtime_execution_latency_ms=runtime_execution_latency_ms,
		semantic_validation_latency_ms=semantic_validation_latency_ms,
		total_pipeline_latency_ms=total_pipeline_latency_ms,
		tool_count=len(tool_names),
		tool_names=tool_names,
	)
	return {
		"pipeline": pipeline,
		"runtime_payload": runtime_payload,
		"normalized_family_artifact": normalized_family_artifact_payload,
		"family_validation": family_validation_payload,
		"semantic_intent_validation": semantic_validation_payload,
		"compiled_execution_audit": audit_contract.to_payload(),
		"phase4_latency_breakdown": {
			"proposal_generation_latency_ms": proposal_generation_latency_ms,
			"compilation_latency_ms": compilation_latency_ms,
			"runtime_execution_latency_ms": runtime_execution_latency_ms,
			"semantic_validation_latency_ms": semantic_validation_latency_ms,
			"total_pipeline_latency_ms": total_pipeline_latency_ms,
		},
	}


def run_phase4_semantic_validation_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	return execute_compiled_fresh_query_message(
		session_id="phase4-semantic-smoke",
		user_id="Administrator",
		site_name=site_name,
		message="How much payable amount do we have as of now",
		recent_messages=[],
	)


def run_phase4_slice5_selftests() -> Dict[str, Any]:
	return {
		"fresh_query_interpreter": run_phase4_fresh_query_interpreter_selftests(),
		"semantic_validation": run_phase4_semantic_validation_selftests(),
	}


def run_phase4_slice6_selftests() -> Dict[str, Any]:
	audit = build_compiled_execution_audit_contract(
		request_id="slice6-selftest",
		session_id="slice6-session",
		compiler_decision="execute",
		compiler_reason="governed compiler path",
		capability_id="accounts_payable_read",
		selected_report="Accounts Payable Summary",
		proposal_cache_hit=False,
		proposal_shared_inflight_hit=False,
		compiled_query_available=True,
		runtime_invoked=True,
		runtime_ok=True,
		runtime_engine="qwen_agent",
		runtime_model="qwen3.5-plus",
		grounded_validation_status="pass",
		semantic_validation_status="pass",
		proposal_generation_latency_ms=120,
		compilation_latency_ms=5,
		runtime_execution_latency_ms=950,
		semantic_validation_latency_ms=3,
		total_pipeline_latency_ms=1078,
		tool_count=1,
		tool_names=["erp_fac-generate_report"],
	)
	payload = audit.to_payload()
	if str(payload.get("type") or "").strip() != "qwen_compiled_execution_audit_contract":
		raise RuntimeError("Slice 6 selftest failed: compiled execution audit contract type mismatch.")
	if int(payload.get("total_pipeline_latency_ms") or 0) < int(payload.get("runtime_execution_latency_ms") or 0):
		raise RuntimeError("Slice 6 selftest failed: total latency is inconsistent.")
	if int(payload.get("tool_count") or 0) != 1:
		raise RuntimeError("Slice 6 selftest failed: tool count mismatch.")
	if bool(payload.get("proposal_cache_hit")):
		raise RuntimeError("Slice 6 selftest failed: proposal cache flag mismatch.")
	if bool(payload.get("proposal_shared_inflight_hit")):
		raise RuntimeError("Slice 6 selftest failed: proposal inflight flag mismatch.")
	return payload


def run_phase4_audit_observability_smoke() -> Dict[str, Any]:
	site_name = ""
	if frappe is not None:
		site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	result = execute_compiled_fresh_query_message(
		session_id="phase4-audit-smoke",
		user_id="Administrator",
		site_name=site_name,
		message="How much payable amount do we have as of now",
		recent_messages=[],
	)
	audit = result.get("compiled_execution_audit")
	if not isinstance(audit, dict):
		raise RuntimeError("Slice 6 audit smoke failed: missing compiled execution audit payload.")
	if str(audit.get("semantic_validation_status") or "").strip() != "pass":
		raise RuntimeError("Slice 6 audit smoke failed: semantic validation did not pass.")
	if int(audit.get("tool_count") or 0) < 1:
		raise RuntimeError("Slice 6 audit smoke failed: expected at least one grounded tool call.")
	return result
