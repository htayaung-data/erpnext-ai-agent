from __future__ import annotations

from app.mock_engine import run_mock_engine
from app.qwen_agent_engine import QwenAgentEngineError, run_qwen_agent_engine
from app.schemas import (
	ChatRequest,
	ChatResponse,
	FrontDoorInterpretRequest,
	FrontDoorInterpretResponse,
	FrontDoorRenderRequest,
	FrontDoorRenderResponse,
	FreshQueryInterpretRequest,
	FreshQueryInterpretResponse,
	FollowUpInterpretRequest,
	FollowUpInterpretResponse,
	ReasoningActivationInterpretRequest,
	ReasoningActivationInterpretResponse,
	RepairIntentInterpretRequest,
	RepairIntentInterpretResponse,
	ReasoningRenderRequest,
	ReasoningRenderResponse,
	ToolTraceItem,
)
from app.erp_business_reasoning_engine import (
	ERPBusinessReasoningEngineError,
	run_erp_business_reasoning_engine,
)
from app.semantic_frontdoor_engine import (
	SemanticFrontDoorEngineError,
	run_semantic_frontdoor_engine,
)
from app.frontdoor_response_engine import (
	FrontDoorResponseEngineError,
	run_frontdoor_response_engine,
)
from app.semantic_fresh_query_engine import (
	SemanticFreshQueryEngineError,
	run_semantic_fresh_query_engine,
)
from app.semantic_followup_engine import (
	SemanticFollowUpEngineError,
	run_semantic_followup_engine,
)
from app.semantic_reasoning_activation_engine import (
	SemanticReasoningActivationEngineError,
	run_semantic_reasoning_activation_engine,
)
from app.semantic_repair_intent_engine import (
	SemanticRepairIntentEngineError,
	run_semantic_repair_intent_engine,
)
from app.settings import Settings
from app.validation import summarize_artifact_narrative_validation, summarize_read_validation


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


def _validate_response(response: ChatResponse, settings: Settings, request: ChatRequest) -> ChatResponse:
	answer_text = str(response.answer_text or "").strip()
	if len(answer_text) > settings.response_char_limit:
		answer_text = answer_text[: settings.response_char_limit].rstrip()

	tool_trace = list(response.tool_trace or [])[: settings.max_tool_calls]
	mode = str(request.mode or "").strip().lower()
	if settings.engine_mode == "qwen_agent" and answer_text and not tool_trace and mode != "artifact_narrative":
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

	if mode == "artifact_narrative":
		validation_ok, validation_summary = summarize_artifact_narrative_validation(
			request.artifact_context if isinstance(request.artifact_context, dict) else {},
			answer_text,
		)
	else:
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
	if mode not in {"read_only", "compiled_read_query", "artifact_narrative"}:
		return _safe_response(error="Unsupported runtime mode.", engine=settings.engine_mode)

	if settings.engine_mode == "mock":
		return _validate_response(run_mock_engine(request), settings, request)

	if settings.engine_mode == "qwen_agent":
		try:
			return _validate_response(run_qwen_agent_engine(request, settings), settings, request)
		except QwenAgentEngineError as exc:
			return _safe_response(error=str(exc), engine=settings.engine_mode)
		except Exception as exc:  # pragma: no cover - defensive runtime hardening
			return _safe_response(error=f"Unexpected qwen runtime error: {exc}", engine=settings.engine_mode)

	return _safe_response(
		error=f"Unsupported engine mode: {settings.engine_mode}",
		engine=settings.engine_mode,
	)


def handle_frontdoor_interpretation(
	request: FrontDoorInterpretRequest,
	settings: Settings,
) -> FrontDoorInterpretResponse:
	try:
		return run_semantic_frontdoor_engine(request, settings)
	except SemanticFrontDoorEngineError as exc:
		return FrontDoorInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_frontdoor"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return FrontDoorInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_frontdoor"},
			error=f"Unexpected semantic front-door error: {exc}",
		)


def handle_frontdoor_render(
	request: FrontDoorRenderRequest,
	settings: Settings,
) -> FrontDoorRenderResponse:
	try:
		return run_frontdoor_response_engine(request, settings)
	except FrontDoorResponseEngineError as exc:
		return FrontDoorRenderResponse(
			ok=False,
			answer_text="",
			agent_meta={"engine": "frontdoor_response_renderer"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return FrontDoorRenderResponse(
			ok=False,
			answer_text="",
			agent_meta={"engine": "frontdoor_response_renderer"},
			error=f"Unexpected front-door render error: {exc}",
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


def handle_reasoning_activation_interpretation(
	request: ReasoningActivationInterpretRequest,
	settings: Settings,
) -> ReasoningActivationInterpretResponse:
	try:
		return run_semantic_reasoning_activation_engine(request, settings)
	except SemanticReasoningActivationEngineError as exc:
		return ReasoningActivationInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_reasoning_activation"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return ReasoningActivationInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_reasoning_activation"},
			error=f"Unexpected semantic reasoning activation error: {exc}",
		)


def handle_reasoning_render(
	request: ReasoningRenderRequest,
	settings: Settings,
) -> ReasoningRenderResponse:
	try:
		return run_erp_business_reasoning_engine(request, settings)
	except ERPBusinessReasoningEngineError as exc:
		return ReasoningRenderResponse(
			ok=False,
			payload=None,
			agent_meta={"engine": "erp_business_reasoning"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return ReasoningRenderResponse(
			ok=False,
			payload=None,
			agent_meta={"engine": "erp_business_reasoning"},
			error=f"Unexpected ERP business reasoning error: {exc}",
		)


def handle_repair_intent_interpretation(
	request: RepairIntentInterpretRequest,
	settings: Settings,
) -> RepairIntentInterpretResponse:
	try:
		return run_semantic_repair_intent_engine(request, settings)
	except SemanticRepairIntentEngineError as exc:
		return RepairIntentInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_repair_intent"},
			error=str(exc),
		)
	except Exception as exc:  # pragma: no cover - defensive runtime hardening
		return RepairIntentInterpretResponse(
			ok=False,
			interpretation=None,
			agent_meta={"engine": "semantic_repair_intent"},
			error=f"Unexpected semantic repair intent error: {exc}",
		)
