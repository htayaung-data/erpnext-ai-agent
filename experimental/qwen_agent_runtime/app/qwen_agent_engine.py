from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List

from app.fac_mcp import build_fac_mcp_descriptor
from app.schemas import ChatRequest, ChatResponse, ToolTraceItem
from app.settings import Settings
from app.tool_gateway_policy import ToolGatewayPolicyError, enforce_tool_gateway_policy

try:  # pragma: no cover - optional dependency
	from qwen_agent.agents import Assistant  # type: ignore
	from qwen_agent.agents import fncall_agent  # type: ignore
except Exception:  # pragma: no cover
	Assistant = None
	fncall_agent = None


class QwenAgentEngineError(RuntimeError):
	pass


def _build_system_contract(settings: Settings) -> str:
	today = datetime.now(timezone.utc).date().isoformat()
	tools = ", ".join(sorted(settings.fac_allowed_tools_set)) if settings.fac_allowed_tools_set else "approved MCP tools"
	default_company_line = ""
	if settings.erp_default_company:
		default_company_line = (
			f'If a report requires company and the user did not specify one, use this exact company value: "{settings.erp_default_company}".\n'
		)
	return f"""You are an ERP assistant operating in read-only mode.
Today's date is {today} UTC.
Use only these approved tools: {tools}.
Never fabricate ERP facts, totals, IDs, dates, or statuses.
Resolve relative dates like "last month" against today's date.
Only answer from tool results.
If you cannot ground the answer in tool results, say you could not complete a grounded ERP lookup.
Do not narrate your plan or say "let me" before the work is complete.
Keep answers concise and business-focused.
{default_company_line}For follow-up filters like territory, customer, warehouse, or date refinement, prefer continuing to a final grounded report instead of stopping after discovery steps.
Prefer this order when answering report questions:
1. use report_list to identify the relevant report,
2. use report_requirements only if required,
3. use generate_report to fetch the answer.
Do not retry the same tool with the same inputs repeatedly.
Use at most {max(1, settings.max_tool_calls)} tool/LLM turns and stop once you have enough grounded data to answer."""


def _is_dashscope_compatible(base_url: str) -> bool:
	value = str(base_url or "").strip().lower()
	return "dashscope" in value and "compatible-mode" in value


def _generate_cfg(settings: Settings) -> Dict[str, Any]:
	if _is_dashscope_compatible(settings.qwen_base_url):
		return {
			"max_input_tokens": 8192,
			"extra_body": {
				"enable_thinking": False,
			},
		}

	return {
		"max_input_tokens": 8192,
		"extra_body": {
			"chat_template_kwargs": {"enable_thinking": False},
		},
	}


def _flatten_responses(chunks: List[Any]) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for chunk in chunks:
		if isinstance(chunk, dict):
			out.append(chunk)
		elif isinstance(chunk, list):
			for item in chunk:
				if isinstance(item, dict):
					out.append(item)
	return out


def _extract_tool_trace(messages: List[Dict[str, Any]]) -> List[ToolTraceItem]:
	tool_trace: List[ToolTraceItem] = []
	pending_index: int | None = None
	for item in messages:
		if not isinstance(item, dict):
			continue
		role = str(item.get("role") or "").strip()
		function_call = item.get("function_call")
		if isinstance(function_call, dict):
			name = str(function_call.get("name") or "").strip()
			args = str(function_call.get("arguments") or "").strip()
			repaired_args = _repair_json_argument_string(args)
			parsed_args = _parse_json_like(repaired_args)
			if name:
				tool_trace.append(
					ToolTraceItem(
						tool=name,
						status="called",
						detail=repaired_args[:2000],
						detail_obj=parsed_args if isinstance(parsed_args, (dict, list)) else None,
					)
				)
				pending_index = len(tool_trace) - 1
				continue
		if role == "function" and pending_index is not None and 0 <= pending_index < len(tool_trace):
			content = str(item.get("content") or "").strip()
			preview = content[:500]
			status = _tool_output_status(content)
			output_obj = _parse_json_like(content)
			tool_trace[pending_index].status = status
			tool_trace[pending_index].output_preview = preview
			tool_trace[pending_index].output_obj = output_obj if isinstance(output_obj, (dict, list)) else None
			pending_index = None
	return tool_trace


def _extract_answer_text(messages: List[Dict[str, Any]]) -> str:
	last_toolish_index = -1
	for idx, item in enumerate(messages):
		if not isinstance(item, dict):
			continue
		role = str(item.get("role") or "").strip()
		if role == "function" or item.get("function_call"):
			last_toolish_index = idx

	for idx in range(len(messages) - 1, last_toolish_index, -1):
		item = messages[idx]
		if not isinstance(item, dict):
			continue
		if str(item.get("role") or "").strip() != "assistant":
			continue
		if item.get("function_call"):
			continue
		content = item.get("content")
		if isinstance(content, str) and content.strip():
			return content.strip()
	return ""


def _repair_json_argument_string(value: str) -> str:
	text = str(value or "").strip()
	if not text:
		return text
	candidates = [text]
	if text.startswith("```"):
		lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
		candidates.append("\n".join(lines).strip())

	for candidate in list(candidates):
		balanced = candidate
		for open_char, close_char in (("{", "}"), ("[", "]")):
			diff = balanced.count(open_char) - balanced.count(close_char)
			if diff > 0:
				balanced += close_char * diff
		if balanced not in candidates:
			candidates.append(balanced)

	for candidate in candidates:
		try:
			json.loads(candidate)
			return candidate
		except Exception:
			continue
	return text


def _parse_json_like(value: Any) -> Any:
	if isinstance(value, (dict, list)):
		return value
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def _tool_output_status(content: str) -> str:
	text = str(content or "").strip()
	if "An error occurred when calling tool" in text:
		return "error"
	obj = _parse_json_like(text)
	if not isinstance(obj, dict):
		return "ok"
	if obj.get("success") is False:
		return "error"
	result = obj.get("result")
	if isinstance(result, dict) and result.get("success") is False:
		return "error"
	return "ok"


def _extract_company_suggestion(tool_result: Any) -> str:
	obj = _parse_json_like(tool_result)
	if not isinstance(obj, dict):
		return ""
	result = obj.get("result")
	if not isinstance(result, dict):
		return ""
	if result.get("success") is not False:
		return ""
	validation_errors = result.get("validation_errors")
	if not isinstance(validation_errors, list):
		return ""
	if not any("invalid company" in str(item or "").strip().lower() for item in validation_errors):
		return ""
	suggestions = result.get("suggestions")
	if not isinstance(suggestions, list):
		return ""
	for suggestion in suggestions:
		match = re.search(r"valid company names include:\s*(.+)$", str(suggestion or "").strip(), re.IGNORECASE)
		if not match:
			continue
		return match.group(1).strip().rstrip(".")
	return ""


def _normalize_tool_params(params: Any) -> tuple[Any, Dict[str, Any] | None]:
	if isinstance(params, dict):
		return params, json.loads(json.dumps(params))
	if isinstance(params, str):
		repaired = _repair_json_argument_string(params)
		parsed = _parse_json_like(repaired)
		return repaired, parsed if isinstance(parsed, dict) else None
	return params, None


def _apply_company_retry(params_obj: Dict[str, Any], company_name: str) -> Dict[str, Any] | None:
	updated = json.loads(json.dumps(params_obj))
	filters = updated.get("filters")
	if not isinstance(filters, dict):
		return None
	current = str(filters.get("company") or "").strip()
	next_value = str(company_name or "").strip()
	if not next_value or next_value == current:
		return None
	filters["company"] = next_value
	if isinstance(updated.get("company"), str):
		updated["company"] = next_value
	return updated


def _maybe_retry_generate_report(fn: Any, original_params: Any, initial_result: Any, **kwargs: Any) -> Any:
	suggested_company = _extract_company_suggestion(initial_result)
	if not suggested_company:
		return initial_result
	serialized_params, params_obj = _normalize_tool_params(original_params)
	if not isinstance(params_obj, dict):
		return initial_result
	retry_params = _apply_company_retry(params_obj, suggested_company)
	if not retry_params:
		return initial_result
	if isinstance(serialized_params, str):
		retry_input = json.dumps(retry_params, ensure_ascii=False)
	else:
		retry_input = retry_params
	retry_result = fn(retry_input, **kwargs)
	return retry_result if retry_result is not None else initial_result


def _wrap_fac_tool_calls(bot: Assistant, settings: Settings) -> None:
	for tool_name, tool in getattr(bot, "function_map", {}).items():
		if not str(tool_name or "").startswith("erp_fac-"):
			continue
		original_call = getattr(tool, "call", None)
		if original_call is None or getattr(tool, "_qwen_runtime_wrapped", False):
			continue

		def _make_wrapped_call(fn: Any, current_tool_name: str):
			def wrapped_call(params: Any, **kwargs: Any) -> Any:
				if isinstance(params, str):
					params = _repair_json_argument_string(params)
				params = enforce_tool_gateway_policy(current_tool_name, params, settings)
				result = fn(params, **kwargs)
				if str(current_tool_name or "").strip() == "erp_fac-generate_report":
					result = _maybe_retry_generate_report(fn, params, result, **kwargs)
				return result

			return wrapped_call

		tool.call = _make_wrapped_call(original_call, str(tool_name or "").strip())
		tool._qwen_runtime_wrapped = True


def run_qwen_agent_engine(request: ChatRequest, settings: Settings) -> ChatResponse:
	if Assistant is None:
		raise QwenAgentEngineError(
			"qwen-agent is not installed in this runtime environment. Install it before using ENGINE_MODE=qwen_agent."
		)
	if not settings.qwen_base_url:
		raise QwenAgentEngineError("QWEN_BASE_URL is not configured.")
	if fncall_agent is not None:
		fncall_agent.MAX_LLM_CALL_PER_RUN = max(2, settings.max_tool_calls + 1)

	mcp_descriptor = build_fac_mcp_descriptor(settings)
	if not mcp_descriptor:
		raise QwenAgentEngineError("FAC MCP is not configured.")

	llm_cfg = {
		"model": settings.qwen_model,
		"model_server": settings.qwen_base_url,
		"api_key": settings.qwen_api_key or "EMPTY",
		"generate_cfg": _generate_cfg(settings),
	}
	bot = Assistant(
		llm=llm_cfg,
		system_message=_build_system_contract(settings),
		function_list=[mcp_descriptor],
	)
	_wrap_fac_tool_calls(bot, settings)

	messages: List[Dict[str, Any]] = [
		{"role": m.role, "content": m.content}
		for m in request.recent_messages
		if str(m.role or "").strip() in {"user", "assistant"}
	]
	messages.append({"role": "user", "content": request.message})

	final_response: List[Dict[str, Any]] = []
	try:
		for chunk in bot.run(messages=messages):
			final_response = _flatten_responses([chunk])
	except ToolGatewayPolicyError as exc:
		raise QwenAgentEngineError(str(exc)) from exc

	tool_trace = _extract_tool_trace(final_response)
	answer_text = _extract_answer_text(final_response)

	allowed = settings.fac_allowed_tools_set
	if allowed and tool_trace:
		disallowed = [x.tool for x in tool_trace if x.tool not in allowed]
		if disallowed:
			raise QwenAgentEngineError(f"Disallowed tool call detected: {', '.join(disallowed)}")

	ok = bool(answer_text)
	error = ""
	if not answer_text and tool_trace:
		answer_text = "I completed ERP tool calls but could not produce a grounded final answer."
		ok = False
		error = "No grounded final answer returned."

	return ChatResponse(
		ok=ok,
		answer_text=answer_text,
		tool_trace=tool_trace,
		agent_meta={
			"engine": "qwen_agent",
			"model": settings.qwen_model,
			"tool_call_count": len(tool_trace),
		},
		error=error if answer_text else "No grounded answer returned.",
	)
