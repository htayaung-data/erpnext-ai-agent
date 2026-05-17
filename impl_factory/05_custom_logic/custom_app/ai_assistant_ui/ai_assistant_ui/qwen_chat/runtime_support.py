from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List


def tool_trace_payload(
	*,
	request_id: str,
	ok: bool,
	tool_trace: List[Dict[str, Any]],
	agent_meta: Dict[str, Any],
	error: str,
	runtime_latency_ms: int,
) -> Dict[str, Any]:
	return {
		"type": "qwen_runtime_trace",
		"request_id": str(request_id or "").strip(),
		"ok": bool(ok),
		"tool_trace": list(tool_trace or []),
		"agent_meta": agent_meta if isinstance(agent_meta, dict) else {},
		"error": str(error or "").strip(),
		"runtime_latency_ms": int(max(0, runtime_latency_ms)),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def tool_trace_message(
	*,
	request_id: str,
	ok: bool,
	tool_trace: List[Dict[str, Any]],
	agent_meta: Dict[str, Any],
	error: str,
	runtime_latency_ms: int,
	safe_json_dumps,
) -> str:
	return safe_json_dumps(
		tool_trace_payload(
			request_id=request_id,
			ok=ok,
			tool_trace=tool_trace,
			agent_meta=agent_meta,
			error=error,
			runtime_latency_ms=runtime_latency_ms,
		)
	)


def local_transform_trace_message(*, request_id: str, source_request_id: str, transforms: List[str], safe_json_dumps) -> str:
	return tool_trace_message(
		request_id=request_id,
		ok=True,
		tool_trace=[
			{
				"tool": "local_transform",
				"status": "ok",
				"detail": ",".join(str(x or "").strip() for x in transforms if str(x or "").strip()),
				"detail_obj": {"transforms": transforms, "source_request_id": source_request_id},
			}
		],
		agent_meta={"engine": "local_transform", "transforms": transforms, "source_request_id": source_request_id},
		error="",
		runtime_latency_ms=0,
		safe_json_dumps=safe_json_dumps,
	)


def safe_runtime_failure_message(exc: Exception) -> str:
	return "Qwen runtime is unavailable right now. Please try again."


def phase6_activation_event_level(status: str) -> str:
	value = str(status or "").strip().lower()
	if value in {"runtime_error", "invalid_payload"}:
		return "error"
	if value in {"low_confidence"}:
		return "warning"
	return "info"


def phase6_execution_event_level(status: str) -> str:
	value = str(status or "").strip().lower()
	if value in {"runtime_error", "invalid_payload"}:
		return "error"
	if value in {"insufficient_grounding"}:
		return "warning"
	return "info"


def is_generic_compiled_failure_answer(answer_text: str) -> bool:
	clean = str(answer_text or "").strip().lower()
	if not clean:
		return False
	return clean in {
		"i could not complete a grounded erp lookup.",
		"i could not complete a governed erp lookup.",
		"i can't complete that safely within the approved erp read path yet.",
	}
