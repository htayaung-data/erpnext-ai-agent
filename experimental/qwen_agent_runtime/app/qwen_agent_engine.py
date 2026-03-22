from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List

from app.fac_mcp import build_fac_mcp_descriptor
from app.report_registry import approved_report_names
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


def _build_system_contract(
	settings: Settings,
	response_policy: Dict[str, Any] | None = None,
	family_tool_context: Dict[str, Any] | None = None,
	*,
	mode: str = "read_only",
	compiled_query: Dict[str, Any] | None = None,
) -> str:
	today = datetime.now(timezone.utc).date().isoformat()
	tools = ", ".join(sorted(settings.fac_allowed_tools_set)) if settings.fac_allowed_tools_set else "approved MCP tools"
	default_company_line = ""
	if settings.erp_default_company:
		default_company_line = (
			f'If a report requires company and the user did not specify one, use this exact company value: "{settings.erp_default_company}".\n'
		)
	policy = response_policy if isinstance(response_policy, dict) else {}
	if bool(policy.get("analysis_requested")):
		response_policy_line = (
			"Response policy: the user explicitly requested analysis, so deeper business interpretation is allowed, "
			"but any insight or recommendation must be clearly grounded in ERP facts or explicit derived calculations.\n"
		)
	else:
		response_policy_line = (
			"Response policy: for default factual answers, present grounded facts first and include a supporting table "
			"or numeric breakdown when relevant. Brief business interpretation is allowed only when clearly useful and grounded. "
			"Do not include recommendations unless the user explicitly asks for analysis, interpretation, comparison, or recommendation.\n"
		)
	if mode == "compiled_read_query":
		compiled = compiled_query if isinstance(compiled_query, dict) else {}
		selected_report = str(compiled.get("selected_report") or "").strip()
		filters = compiled.get("filters") if isinstance(compiled.get("filters"), dict) else {}
		requested_dimensions = compiled.get("requested_dimensions") if isinstance(compiled.get("requested_dimensions"), list) else []
		requested_metrics = compiled.get("requested_metrics") if isinstance(compiled.get("requested_metrics"), list) else []
		return f"""You are an ERP assistant operating in compiled read-only mode.
Today's date is {today} UTC.
Use only the tool erp_fac-generate_report.
Never call report_list or report_requirements in this mode.
Never fabricate ERP facts, totals, IDs, dates, or statuses.
You have already been given the exact governed report and filters.
You must call erp_fac-generate_report exactly once using this exact report name and exact filters:
report_name = {selected_report}
filters = {json.dumps(filters, ensure_ascii=False, sort_keys=True)}
Requested dimensions = {json.dumps(requested_dimensions, ensure_ascii=False)}
Requested metrics = {json.dumps(requested_metrics, ensure_ascii=False)}
Do not add, remove, or modify filters.
After the tool returns, answer only from tool results.
If you cannot ground the answer in tool results, say you could not complete a grounded ERP lookup.
Keep answers concise and business-focused.
{response_policy_line}"""
	family_context = family_tool_context if isinstance(family_tool_context, dict) else {}
	family_entries = family_context.get("family_entries") if isinstance(family_context.get("family_entries"), list) else []
	allowed_report_names = family_context.get("allowed_report_names") if isinstance(family_context.get("allowed_report_names"), list) else []
	report_discovery_allowed = bool(family_context.get("report_discovery_allowed", True))
	family_policy_block = ""
	preferred_order_block = (
		"Prefer this order when answering report questions:\n"
		"1. use report_list to identify the relevant report,\n"
		"2. use report_requirements only if required,\n"
		"3. use generate_report to fetch the answer.\n"
	)
	if family_entries:
		lines: List[str] = []
		for item in family_entries[:3]:
			if not isinstance(item, dict):
				continue
			family_id = str(item.get("family_id") or "").strip()
			tool_id = str(item.get("tool_id") or "").strip()
			report_names = [
				str(name or "").strip()
				for name in list(item.get("report_names") or [])
				if str(name or "").strip()
			]
			prompt_hint = str(item.get("prompt_hint") or "").strip()
			label = tool_id or family_id or "governed_family_route"
			detail = f"- {label}: approved reports = {', '.join(report_names[:6])}."
			if prompt_hint:
				detail = f"{detail} {prompt_hint}"
			lines.append(detail)
		allowed_line = ""
		if allowed_report_names:
			allowed_line = f"In this request, restrict report calls to these approved family reports: {', '.join(str(name or '').strip() for name in allowed_report_names if str(name or '').strip())}.\n"
		discovery_line = (
			"Do not call erp_fac-report_list when a governed family route is provided. "
			"Prefer direct family routing: use erp_fac-report_requirements only if a required filter is missing; otherwise call erp_fac-generate_report directly.\n"
			if not report_discovery_allowed
			else "Prefer governed family routes first; use erp_fac-report_list only if the family route truly cannot answer the request.\n"
		)
		family_policy_block = (
			"A governed family tool surface is active for this request.\n"
			"Prefer these family routes over raw report discovery:\n"
			f"{chr(10).join(lines)}\n"
			f"{allowed_line}"
			f"{discovery_line}"
		)
		if not report_discovery_allowed:
			preferred_order_block = (
				"Prefer this order when answering the request:\n"
				"1. select one governed family route from the provided family entries,\n"
				"2. use report_requirements only if a required filter is missing,\n"
				"3. use generate_report to fetch the grounded result.\n"
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
{response_policy_line}{default_company_line}{family_policy_block}For follow-up filters like territory, customer, warehouse, or date refinement, prefer continuing to a final grounded report instead of stopping after discovery steps.
{preferred_order_block}Do not retry the same tool with the same inputs repeatedly.
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


def _serialize_result_like_original(original: Any, payload: Dict[str, Any]) -> Any:
	if isinstance(original, str):
		return json.dumps(payload, ensure_ascii=False)
	return payload


def _filter_report_list_result(result: Any) -> Any:
	approved = {str(name or "").strip().lower() for name in approved_report_names() if str(name or "").strip()}
	if not approved:
		return result
	parsed = _parse_json_like(result)
	if not isinstance(parsed, dict):
		return result

	def _item_name(item: Any) -> str:
		if not isinstance(item, dict):
			return ""
		return str(item.get("report_name") or item.get("name") or "").strip().lower()

	def _filter_items(items: Any) -> List[Dict[str, Any]]:
		if not isinstance(items, list):
			return []
		return [
			dict(item)
			for item in items
			if isinstance(item, dict) and _item_name(item) in approved
		]

	updated = json.loads(json.dumps(parsed))
	changed = False
	if isinstance(updated.get("reports"), list):
		updated["reports"] = _filter_items(updated.get("reports"))
		changed = True
	result_obj = updated.get("result")
	if isinstance(result_obj, dict) and isinstance(result_obj.get("reports"), list):
		result_obj["reports"] = _filter_items(result_obj.get("reports"))
		updated["result"] = result_obj
		changed = True
	elif isinstance(result_obj, list):
		updated["result"] = _filter_items(result_obj)
		changed = True
	return _serialize_result_like_original(result, updated) if changed else result


def _normalize_conversation_messages(request: ChatRequest) -> List[Dict[str, Any]]:
	raw_messages: List[Dict[str, Any]] = []
	for item in request.recent_messages:
		role = str(item.role or "").strip()
		content = str(item.content or "").strip()
		if role not in {"user", "assistant"} or not content:
			continue
		raw_messages.append({"role": role, "content": content})
	current_message = str(request.message or "").strip()
	if current_message:
		raw_messages.append({"role": "user", "content": current_message})

	normalized: List[Dict[str, Any]] = []
	for item in raw_messages:
		role = str(item.get("role") or "").strip()
		content = str(item.get("content") or "").strip()
		if role not in {"user", "assistant"} or not content:
			continue
		if not normalized:
			if role != "user":
				continue
			normalized.append({"role": role, "content": content})
			continue
		if str(normalized[-1].get("role") or "").strip() == role:
			normalized[-1]["content"] = f"{normalized[-1]['content']}\n\n{content}".strip()
			continue
		normalized.append({"role": role, "content": content})

	if not normalized and current_message:
		return [{"role": "user", "content": current_message}]
	return normalized


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


def _wrap_fac_tool_calls(
	bot: Assistant,
	settings: Settings,
	*,
	compiled_query: Dict[str, Any] | None = None,
	family_tool_context: Dict[str, Any] | None = None,
) -> None:
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
				params = enforce_tool_gateway_policy(
					current_tool_name,
					params,
					settings,
					compiled_query=compiled_query,
					family_tool_context=family_tool_context,
				)
				result = fn(params, **kwargs)
				if str(current_tool_name or "").strip() == "erp_fac-report_list":
					result = _filter_report_list_result(result)
				if str(current_tool_name or "").strip() == "erp_fac-generate_report" and not compiled_query:
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
	compiled_query = request.compiled_query if isinstance(request.compiled_query, dict) else {}
	family_tool_context = request.family_tool_context if isinstance(request.family_tool_context, dict) else {}
	bot = Assistant(
		llm=llm_cfg,
		system_message=_build_system_contract(
			settings,
			request.response_policy,
			family_tool_context,
			mode=str(request.mode or "read_only").strip().lower(),
			compiled_query=compiled_query,
		),
		function_list=[mcp_descriptor],
	)
	_wrap_fac_tool_calls(
		bot,
		settings,
		compiled_query=compiled_query,
		family_tool_context=family_tool_context,
	)

	messages = _normalize_conversation_messages(request)

	final_response: List[Dict[str, Any]] = []
	try:
		for chunk in bot.run(messages=messages):
			final_response = _flatten_responses([chunk])
	except ToolGatewayPolicyError as exc:
		raise QwenAgentEngineError(str(exc)) from exc
	except Exception as exc:
		raise QwenAgentEngineError(f"Qwen-Agent execution failed: {exc}") from exc

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
			"family_tool_surface_active": bool(family_tool_context),
			"family_tool_report_discovery_allowed": bool(family_tool_context.get("report_discovery_allowed", True))
			if isinstance(family_tool_context, dict)
			else True,
			"family_tool_candidate_count": len(family_tool_context.get("candidate_family_ids") or [])
			if isinstance(family_tool_context, dict)
			else 0,
		},
		error=error if answer_text else "No grounded answer returned.",
	)
