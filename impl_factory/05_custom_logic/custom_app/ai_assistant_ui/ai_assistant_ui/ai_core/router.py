import json
import frappe

from .openai_client import OpenAIClient
from .report_export import export_report_csv, export_report_xlsx
from .state import load_state_from_messages
from .tools_read import TOOL_REGISTRY_READ
from .tools_write import TOOL_REGISTRY_WRITE
from .util_dates import detect_language, parse_relative_range

MAX_CONTEXT_MESSAGES = 24
MAX_TOOL_LOOPS = 4
MAX_PREVIEW_ROWS = 50
MAX_EXPORT_ROWS = 5000


def _safe_json_loads(s):
    try:
        return json.loads(s) if s else None
    except Exception:
        return None


def _truncate(text: str, max_len=3000) -> str:
    if not text:
        return ""
    return text if len(text) <= max_len else text[:max_len] + "…"


def _make_tool_card(tool, status, title, payload, ui=None):
    return json.dumps(
        {"tool": tool, "status": status, "title": title, "payload": payload or {}, "ui": ui or {}},
        ensure_ascii=False,
    )


def _is_write_tool(name: str) -> bool:
    return name in TOOL_REGISTRY_WRITE


def _normalize_report_result(raw):
    """
    Normalize report results to a dict so router code can safely use .get().
    Handles common shapes:
      - dict: {"columns": [...], "result": [...]}
      - list/tuple: [columns, rows] or [columns, rows, message]
    """
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, (list, tuple)):
        if len(raw) >= 2:
            cols = raw[0]
            rows = raw[1]
            out = {"columns": cols, "result": rows}
            if len(raw) >= 3:
                out["message"] = raw[2]
            return out
        # single-item list fallback
        return {"result": list(raw)}

    # unknown shape
    return {"raw": raw}


def _tool_schemas():
    return [
        {"type": "function", "function": {"name": "report_list", "description": "List available ERP reports.", "parameters": {"type": "object", "properties": {"module": {"type": "string"}, "report_type": {"type": "string"}}}}},
        {"type": "function", "function": {"name": "report_requirements", "description": "Get required filters/options/columns for a report.", "parameters": {"type": "object", "properties": {"report_name": {"type": "string"}}, "required": ["report_name"]}}},
        {"type": "function", "function": {"name": "generate_report", "description": "Run a report (FAC prepared report supported). Read-only.", "parameters": {"type": "object", "properties": {"report_name": {"type": "string"}, "filters": {"type": "object"}, "format": {"type": "string", "enum": ["json", "csv", "excel"]}}, "required": ["report_name"]}}},
        {"type": "function", "function": {"name": "list_documents", "description": "List documents from a DocType. Read-only.", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "filters": {"type": "object"}, "fields": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer"}, "order_by": {"type": "string"}}, "required": ["doctype"]}}},
        {"type": "function", "function": {"name": "get_document", "description": "Fetch a single document. Read-only.", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}}, "required": ["doctype", "name"]}}},
        {"type": "function", "function": {"name": "search_link", "description": "Search link options. Read-only.", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "query": {"type": "string"}, "filters": {"type": "object"}}, "required": ["doctype", "query"]}}},
        {"type": "function", "function": {"name": "search_doctype", "description": "Search doctype by name-like query. Read-only.", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["doctype", "query"]}}},
        # Write tools: propose only; never execute without confirm_action.
        {"type": "function", "function": {"name": "create_document", "description": "Create doc (requires confirmation).", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "data": {"type": "object"}, "submit": {"type": "boolean"}}, "required": ["doctype", "data"]}}},
        {"type": "function", "function": {"name": "update_document", "description": "Update doc (requires confirmation).", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}, "data": {"type": "object"}}, "required": ["doctype", "name", "data"]}}},
        {"type": "function", "function": {"name": "delete_document", "description": "Delete doc (requires confirmation).", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}, "force": {"type": "boolean"}}, "required": ["doctype", "name"]}}},
        {"type": "function", "function": {"name": "submit_document", "description": "Submit doc (requires confirmation).", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}}, "required": ["doctype", "name"]}}},
        {"type": "function", "function": {"name": "run_workflow", "description": "Run workflow (requires confirmation).", "parameters": {"type": "object", "properties": {"doctype": {"type": "string"}, "name": {"type": "string"}, "action": {"type": "string"}}, "required": ["doctype", "name", "action"]}}},
    ]


def _system_prompt(language: str) -> str:
    if language == "my":
        return (
            "သင်သည် ERPNext အတွင်းရှိ AI Assistant ဖြစ်သည်။\n"
            "စည်းကမ်းများ:\n"
            "1) Read-only tools များကို ချက်ချင်း run လုပ်ပါ (အတည်ပြုချက် မလို)။\n"
            "2) Write tools များကို ချက်ချင်း မလုပ်ပါ—UI Confirm/Cancel အတည်ပြုချက်လိုအပ်သည်။\n"
            "3) Tool output မရှိဘဲ မခန့်မှန်းပါနှင့်—လိုအပ်ပါက tool ကိုခေါ်ပါ။\n"
            "4) User က မြန်မာလိုရေးထားလျှင် မြန်မာလိုပဲ ဖြေပါ။\n"
        )
    return (
        "You are an ERPNext embedded AI Assistant.\n"
        "Rules:\n"
        "1) Read-only tools run immediately (no confirmation).\n"
        "2) Write tools must NEVER execute without explicit UI confirmation.\n"
        "3) Don’t guess ERP facts without tool output—use tools.\n"
        "4) If user writes in English, respond in English.\n"
    )


def _messages_for_llm(session_doc, state: dict):
    out = [{"role": "system", "content": _system_prompt(state.get("language") or "en")}]
    out.append(
        {
            "role": "system",
            "content": (
                "Session state:\n"
                f"- company: {state.get('company')}\n"
                f"- last_report: {state.get('last_report')}\n"
                f"- last_filters: {state.get('last_filters')}\n"
                f"- last_date_range: {state.get('last_date_range')}\n"
                f"- pending_actions_count: {len(state.get('pending_actions') or [])}\n"
            ),
        }
    )

    msgs = session_doc.get("messages") or []
    for m in msgs[-MAX_CONTEXT_MESSAGES:]:
        if m.role == "tool":
            j = _safe_json_loads(m.content)
            if isinstance(j, dict) and j.get("ui_hidden") is True and j.get("tool") == "__state__":
                continue
        out.append({"role": m.role, "content": _truncate(m.content or "", 6000)})
    return out


class ChatRouter:
    def __init__(self):
        self.client = OpenAIClient()

    def handle(self, session_doc, user_text: str) -> dict:
        state = load_state_from_messages([{"role": m.role, "content": m.content} for m in (session_doc.get("messages") or [])])

        state["language"] = detect_language(user_text) or (state.get("language") or "en")

        dr = parse_relative_range(user_text)
        if dr:
            state["last_date_range"] = dr

        llm_messages = _messages_for_llm(session_doc, state)
        tools = _tool_schemas()

        final_text = ""
        for _ in range(MAX_TOOL_LOOPS):
            resp = self.client.chat_completions(llm_messages, tools=tools, tool_choice="auto", timeout=90)
            choice = (resp.get("choices") or [{}])[0]
            msg = choice.get("message") or {}

            tool_calls = msg.get("tool_calls") or []
            content = (msg.get("content") or "").strip()

            if not tool_calls:
                final_text = content or final_text
                break

            for tc in tool_calls:
                fn = (tc.get("function") or {}).get("name")
                arg_s = (tc.get("function") or {}).get("arguments") or "{}"
                args = _safe_json_loads(arg_s) or {}

                if not fn:
                    continue

                if _is_write_tool(fn):
                    action_id = frappe.generate_hash(length=12)
                    pending = state.get("pending_actions") or []
                    pending.append({"id": action_id, "tool": fn, "args": args, "status": "pending"})
                    state["pending_actions"] = pending

                    session_doc.append(
                        "messages",
                        {
                            "role": "tool",
                            "content": _make_tool_card(
                                tool=fn,
                                status="needs_confirmation",
                                title="Proposed change (requires confirmation)",
                                payload={"action_id": action_id, "tool": fn, "args": args},
                                ui={"type": "confirm", "action_id": action_id},
                            ),
                        },
                    )
                    llm_messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": "Proposed write action; waiting for confirmation."})
                    continue

                result = self._run_read_tool(fn, args)
                session_doc.append("messages", {"role": "tool", "content": self._tool_result_to_card(fn, args, result)})
                llm_messages.append({"role": "tool", "tool_call_id": tc.get("id"), "content": _truncate(json.dumps(result, ensure_ascii=False, default=str), 8000)})

            llm_messages.append({"role": "assistant", "content": content or ""})

        if not final_text:
            final_text = "OK."

        session_doc.append("messages", {"role": "assistant", "content": final_text})
        return {"state": state, "assistant": final_text}

    def execute_single_read_tool(self, session_doc, tool_name: str, tool_args: dict) -> dict:
        state = load_state_from_messages([{"role": m.role, "content": m.content} for m in (session_doc.get("messages") or [])])
        result = self._run_read_tool(tool_name, tool_args)
        session_doc.append("messages", {"role": "tool", "content": self._tool_result_to_card(tool_name, tool_args, result)})
        return {"state": state, "tool_result": result}

    def confirm_pending_action(self, session_doc, action_id: str, decision: str) -> dict:
        state = load_state_from_messages([{"role": m.role, "content": m.content} for m in (session_doc.get("messages") or [])])
        pending = state.get("pending_actions") or []

        idx = next((i for i, a in enumerate(pending) if a.get("id") == action_id), None)
        if idx is None:
            raise frappe.ValidationError("Action not found or already handled.")

        action = pending[idx]
        tool = action.get("tool")
        args = action.get("args") or {}

        if decision == "cancel":
            action["status"] = "cancelled"
            session_doc.append("messages", {"role": "tool", "content": _make_tool_card(tool, "cancelled", "Action cancelled", {"action_id": action_id}, {"type": "info"})})
            return {"state": state}

        fn = TOOL_REGISTRY_WRITE.get(tool)
        if not fn:
            raise frappe.ValidationError("Write tool not available.")

        res = fn(**args)
        action["status"] = "executed"
        session_doc.append("messages", {"role": "tool", "content": _make_tool_card(tool, "success", "Action executed", {"action_id": action_id, "result": res}, {"type": "result"})})
        session_doc.append("messages", {"role": "assistant", "content": "Done." if (state.get("language") or "en") == "en" else "ပြီးပါပြီ။"})
        return {"state": state}

    def _run_read_tool(self, tool_name: str, tool_args: dict):
        fn = TOOL_REGISTRY_READ.get(tool_name)
        if not fn:
            return {"status": "error", "error": f"Tool not allowed: {tool_name}"}
        try:
            return fn(**(tool_args or {}))
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _tool_result_to_card(self, tool_name: str, tool_args: dict, result):
        if tool_name == "generate_report":
            return self._report_result_card(tool_args, result)

        # normalize any non-dict tool result
        if not isinstance(result, dict):
            result = {"raw": result}

        status = "error" if result.get("status") == "error" else "success"
        return _make_tool_card(tool_name, status, f"{tool_name} result", {"args": tool_args, "result": result}, {"type": "generic"})

    def _report_result_card(self, tool_args: dict, result):
        report_name = tool_args.get("report_name") or "Report"
        filters = tool_args.get("filters") or {}

        result = _normalize_report_result(result)

        columns = result.get("columns") or result.get("columns_list") or result.get("report_columns") or []
        rows = result.get("result") or result.get("rows") or result.get("data") or []

        if not isinstance(rows, list):
            return _make_tool_card(
                "generate_report",
                "pending",
                f"{report_name} (pending)",
                {"report_name": report_name, "filters": filters, "raw": result},
                {"type": "report", "retry": {"tool_name": "generate_report", "tool_args": tool_args}},
            )

        preview = rows[:MAX_PREVIEW_ROWS]
        export_rows = rows[:MAX_EXPORT_ROWS]

        exports = {}
        try:
            if export_rows:
                exports["csv"] = export_report_csv(report_name, columns, export_rows)
                exports["xlsx"] = export_report_xlsx(report_name, columns, export_rows)
        except Exception:
            exports["error"] = "Export failed."

        ui = {
            "type": "report",
            "row_count": len(rows),
            "preview_row_count": len(preview),
            "truncated": len(rows) > MAX_PREVIEW_ROWS,
            "exports": exports,
            "retry": {"tool_name": "generate_report", "tool_args": tool_args},
        }
        payload = {"report_name": report_name, "filters": filters, "columns": columns, "rows": preview}
        return _make_tool_card("generate_report", "success", report_name, payload, ui)
