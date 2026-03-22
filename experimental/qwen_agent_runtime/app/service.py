from __future__ import annotations

from app.mock_engine import run_mock_engine
from app.qwen_agent_engine import QwenAgentEngineError, run_qwen_agent_engine
from app.schemas import (
	ChatRequest,
	ChatResponse,
	FreshQueryInterpretRequest,
	FreshQueryInterpretResponse,
	FollowUpInterpretRequest,
	FollowUpInterpretResponse,
	ToolTraceItem,
)
from app.semantic_fresh_query_engine import (
	SemanticFreshQueryEngineError,
	run_semantic_fresh_query_engine,
)
from app.semantic_followup_engine import (
	SemanticFollowUpEngineError,
	run_semantic_followup_engine,
)
from app.settings import Settings
from app.validation import summarize_read_validation


def _safe_response(
	*,
	error: str,
	engine: str,
	validation: dict | None = None,
	agent_meta: dict | None = None,
	tool_trace: list | None = None,
) -> ChatResponse:
	meta = dict(agent_meta or {}) if isinstance(agent_meta, dict) else {}
	meta.update(
		{
			"engine": str(meta.get("engine") or engine or "").strip() or engine,
			"grounded": False,
			"validation": validation or {"status": "fail", "errors": [str(error or "").strip()]},
		}
	)
	return ChatResponse(
		ok=False,
		answer_text="I could not complete a grounded ERP lookup.",
		tool_trace=[
			item if isinstance(item, ToolTraceItem) else ToolTraceItem(**item)
			for item in list(tool_trace or [])
			if isinstance(item, (dict, ToolTraceItem))
		],
		agent_meta=meta,
		error=str(error or "").strip(),
	)


def _validate_response(response: ChatResponse, settings: Settings) -> ChatResponse:
	answer_text = str(response.answer_text or "").strip()
	if len(answer_text) > settings.response_char_limit:
		answer_text = answer_text[: settings.response_char_limit].rstrip()

	tool_trace = list(response.tool_trace or [])[: settings.max_tool_calls]
	if settings.engine_mode == "qwen_agent" and answer_text and not tool_trace:
		return _safe_response(
			error="Qwen-Agent returned an ungrounded answer without tool usage.",
			engine=settings.engine_mode,
			agent_meta=response.agent_meta,
			tool_trace=response.tool_trace,
		)

	if any(str(x.tool or "").strip().lower().startswith(("create", "update", "delete", "write")) for x in tool_trace):
		return _safe_response(
			error="Write-oriented tool usage is not allowed in read-only mode.",
			engine=settings.engine_mode,
			agent_meta=response.agent_meta,
			tool_trace=response.tool_trace,
		)

	validation_ok, validation_summary = summarize_read_validation(tool_trace, answer_text)
	if settings.engine_mode == "qwen_agent" and not validation_ok:
		return _safe_response(
			error="Grounded read validation failed.",
			engine=settings.engine_mode,
			validation=validation_summary,
			agent_meta=response.agent_meta,
			tool_trace=response.tool_trace,
		)

	return ChatResponse(
		ok=bool(response.ok and answer_text),
		answer_text=answer_text,
		tool_trace=[
			item if isinstance(item, ToolTraceItem) else ToolTraceItem(**item)
			for item in tool_trace
		],
		agent_meta={
			**(response.agent_meta or {}),
			"validation": validation_summary,
		},
		error=str(response.error or "").strip(),
	)


def handle_chat(request: ChatRequest, settings: Settings) -> ChatResponse:
	mode = str(request.mode or "").strip().lower()
	if mode not in {"read_only", "compiled_read_query"}:
		return _safe_response(error="Unsupported runtime mode.", engine=settings.engine_mode)

	if settings.engine_mode == "mock":
		return _validate_response(run_mock_engine(request), settings)

	if settings.engine_mode == "qwen_agent":
		try:
			return _validate_response(run_qwen_agent_engine(request, settings), settings)
		except QwenAgentEngineError as exc:
			return _safe_response(error=str(exc), engine=settings.engine_mode)
		except Exception as exc:  # pragma: no cover - defensive runtime hardening
			return _safe_response(error=f"Unexpected qwen runtime error: {exc}", engine=settings.engine_mode)

	return _safe_response(
		error=f"Unsupported engine mode: {settings.engine_mode}",
		engine=settings.engine_mode,
	)


def handle_followup_interpretation(request: FollowUpInterpretRequest, settings: Settings) -> FollowUpInterpretResponse:
	try:
		return run_semantic_followup_engine(request, settings)
	except SemanticFollowUpEngineError as exc:
		return FollowUpInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_followup"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return FollowUpInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_followup"},
			error=f"Unexpected semantic follow-up error: {exc}",
		)


def handle_fresh_query_interpretation(
	request: FreshQueryInterpretRequest,
	settings: Settings,
) -> FreshQueryInterpretResponse:
	try:
		return run_semantic_fresh_query_engine(request, settings)
	except SemanticFreshQueryEngineError as exc:
		return FreshQueryInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_fresh_query"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return FreshQueryInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_fresh_query"},
			error=f"Unexpected semantic fresh-query error: {exc}",
		)
