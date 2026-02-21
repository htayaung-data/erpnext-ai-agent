import json
import shlex
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from semantic_assertions import evaluate_case_assertions, is_meta_clarification

SITE = "erpai_prj1"
USER = "Administrator"
CMD_TIMEOUT_SEC = 120


def _run(cmd: List[str], timeout_sec: int = CMD_TIMEOUT_SEC) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=int(timeout_sec))
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", errors="ignore") if e.stdout else "")
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", errors="ignore") if e.stderr else "")
        stderr = (stderr + f"\nTIMEOUT after {int(timeout_sec)}s").strip()
        return subprocess.CompletedProcess(e.cmd, 124, stdout=stdout, stderr=stderr)


def _parse_last_json(stdout: str):
    lines = [ln.strip() for ln in (stdout or "").splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("{") or ln.startswith("["):
            try:
                return json.loads(ln)
            except Exception:
                continue
    return None


def bench_execute(method: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    # bench execute parses --kwargs with Python eval(), so use Python-literal repr.
    kwargs_py = repr(kwargs)
    inner = (
        "cd /home/frappe/frappe-bench && "
        f"bench --site {SITE} execute {method} --kwargs {shlex.quote(kwargs_py)}"
    )
    cmd = ["docker", "compose", "exec", "-T", "backend", "bash", "-lc", inner]
    res = _run(cmd)
    return {
        "ok": res.returncode == 0,
        "returncode": res.returncode,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "data": _parse_last_json(res.stdout),
    }


def bench_shell(command: str) -> Dict[str, Any]:
    inner = f"cd /home/frappe/frappe-bench && {command}"
    cmd = ["docker", "compose", "exec", "-T", "backend", "bash", "-lc", inner]
    res = _run(cmd)
    return {"ok": res.returncode == 0, "returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr}


def show_config() -> Dict[str, Optional[str]]:
    out = bench_shell(f"bench --site {SITE} show-config")
    vals: Dict[str, Optional[str]] = {}
    txt = out.get("stdout") or ""
    for line in txt.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        key = parts[1]
        val = parts[2]
        if not key or key in ("Config", "+-----------------------------------------------+"):
            continue
        vals[key] = val
    return vals


def set_config(key: str, value: Any) -> bool:
    val = str(value)
    out = bench_shell(f"bench --site {SITE} set-config {shlex.quote(key)} {shlex.quote(val)}")
    return bool(out.get("ok"))


def create_session(title: str) -> Tuple[str, Dict[str, Any]]:
    out = bench_execute("ai_assistant_ui.api.create_session", {"title": title})
    name = ""
    if isinstance(out.get("data"), dict):
        name = str(out["data"].get("name") or "").strip()
    return name, out


def delete_session(name: str) -> None:
    if not name:
        return
    bench_execute("ai_assistant_ui.api.delete_session", {"session_name": name})


def chat_send(session_name: str, message: str) -> Dict[str, Any]:
    return bench_execute("ai_assistant_ui.api.chat_send", {"session_name": session_name, "message": message})


def get_messages(session_name: str, debug: int) -> List[Dict[str, Any]]:
    out = bench_execute("ai_assistant_ui.api.get_messages", {"session_name": session_name, "debug": int(debug)})
    data = out.get("data")
    if isinstance(data, list):
        return data
    return []


def create_todo(description: str) -> Optional[str]:
    out = bench_execute(
        "frappe.client.insert",
        {"doc": {"doctype": "ToDo", "description": description, "status": "Open"}},
    )
    if not out.get("ok"):
        return None
    data = out.get("data")
    if isinstance(data, dict):
        nm = str(data.get("name") or "").strip()
        return nm or None
    return None


def delete_todo(name: str) -> None:
    if not name:
        return
    bench_execute("frappe.client.delete", {"doctype": "ToDo", "name": name})


def get_first_doc_name(doctype: str, filters: Optional[Any] = None) -> Optional[str]:
    kwargs: Dict[str, Any] = {
        "doctype": doctype,
        "fields": ["name"],
        "limit_page_length": 1,
        "order_by": "modified desc",
    }
    if filters is not None:
        kwargs["filters"] = filters
    out = bench_execute("frappe.client.get_list", kwargs)
    if not out.get("ok"):
        return None
    data = out.get("data")
    if not isinstance(data, list) or not data:
        return None
    first = data[0] if isinstance(data[0], dict) else {}
    nm = str(first.get("name") or "").strip()
    return nm or None


def _parse_content(raw: Any) -> Optional[Dict[str, Any]]:
    s = str(raw or "").strip()
    if not s.startswith("{") or not s.endswith("}"):
        return None
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _max_idx(msgs: List[Dict[str, Any]]) -> int:
    m = 0
    for x in msgs or []:
        try:
            i = int(x.get("idx") or 0)
            if i > m:
                m = i
        except Exception:
            continue
    return m


def _new_msgs(msgs: List[Dict[str, Any]], after_idx: int) -> List[Dict[str, Any]]:
    out = []
    for x in msgs or []:
        try:
            i = int(x.get("idx") or 0)
        except Exception:
            i = 0
        if i > after_idx:
            out.append(x)
    return out


def _extract_turn_actual(new_debug_msgs: List[Dict[str, Any]], all_public_msgs: List[Dict[str, Any]]) -> Dict[str, Any]:
    tool_types = set()
    pending_mode = None
    pending_cleared = False
    pending_state: Dict[str, Any] = {
        "mode": None,
        "base_question": None,
        "clarification_question": None,
        "clarification_options": [],
        "options": [],
        "clarification_round": 0,
    }

    assistant_obj: Dict[str, Any] = {"type": "text", "text": ""}
    assistant_idx = None
    audit_turn: Dict[str, Any] = {}
    last_result_tool: Dict[str, Any] = {}

    for m in new_debug_msgs:
        role = str(m.get("role") or "").lower()
        obj = _parse_content(m.get("content"))
        if role == "assistant":
            assistant_idx = m.get("idx")
            if isinstance(obj, dict):
                assistant_obj = obj
            else:
                assistant_obj = {"type": "text", "text": str(m.get("content") or "")}
        if role == "tool" and isinstance(obj, dict):
            typ = str(obj.get("type") or "").strip()
            if typ:
                tool_types.add(typ)
            if typ == "pending_state":
                if obj.get("cleared"):
                    pending_cleared = True
                    pending_mode = None
                    pending_state = {
                        "mode": None,
                        "base_question": None,
                        "clarification_question": None,
                        "clarification_options": [],
                        "options": [],
                        "clarification_round": 0,
                    }
                st = obj.get("state") if isinstance(obj.get("state"), dict) else None
                if st:
                    clar_round = 0
                    try:
                        clar_round = int(st.get("clarification_round") or 0)
                    except Exception:
                        clar_round = 0
                    pending_mode = st.get("mode")
                    pending_state = {
                        "mode": st.get("mode"),
                        "base_question": st.get("base_question"),
                        "clarification_question": st.get("clarification_question"),
                        "clarification_options": st.get("clarification_options") if isinstance(st.get("clarification_options"), list) else [],
                        "options": st.get("options") if isinstance(st.get("options"), list) else [],
                        "clarification_round": clar_round,
                    }
            elif typ == "audit_turn":
                audit_turn = obj
            elif typ == "last_result":
                last_result_tool = obj

    table = assistant_obj.get("table") if isinstance(assistant_obj.get("table"), dict) else {}
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []

    downloads = assistant_obj.get("downloads")
    if isinstance(downloads, list):
        dl_count = len(downloads)
    elif isinstance(downloads, int):
        dl_count = downloads
    else:
        dl_count = 0

    assistant_text = str(assistant_obj.get("text") or "")
    clarification = bool(pending_mode in ("planner_clarify", "need_filters", "transform_pending", "write_confirmation"))
    planner_output = audit_turn.get("planner_output") if isinstance(audit_turn.get("planner_output"), dict) else {}
    plan = planner_output.get("plan") if isinstance(planner_output.get("plan"), dict) else {}
    spec_wrap = planner_output.get("business_request_spec") if isinstance(planner_output.get("business_request_spec"), dict) else {}
    business_spec = spec_wrap.get("spec") if isinstance(spec_wrap.get("spec"), dict) else {}
    gate_wrap = planner_output.get("result_quality_gate") if isinstance(planner_output.get("result_quality_gate"), dict) else {}
    gate = gate_wrap.get("gate") if isinstance(gate_wrap.get("gate"), dict) else {}
    result_meta = audit_turn.get("result_meta") if isinstance(audit_turn.get("result_meta"), dict) else {}
    duration_ms = None
    try:
        if result_meta.get("duration_ms") is not None:
            duration_ms = int(result_meta.get("duration_ms"))
    except Exception:
        duration_ms = None
    failed = gate.get("failed_checks") if isinstance(gate.get("failed_checks"), list) else []
    failed_ids: List[str] = []
    for fc in failed:
        if not isinstance(fc, dict):
            continue
        cid = str(fc.get("id") or "").strip()
        if cid:
            failed_ids.append(cid)

    return {
        "assistant_type": str(assistant_obj.get("type") or "text"),
        "assistant_text": assistant_text,
        "assistant_title": assistant_obj.get("title") or assistant_obj.get("report_name"),
        "downloads": dl_count,
        "rows": len(rows),
        "columns": len(cols),
        "column_labels": [
            str((c.get("label") or c.get("fieldname") or "")).strip()
            for c in cols[:12]
            if isinstance(c, dict)
        ],
        "assistant_idx": assistant_idx,
        "pending_mode": pending_mode,
        "pending_cleared": pending_cleared,
        "options_count": len(pending_state.get("options") or []) + len(pending_state.get("clarification_options") or []),
        "audit_present": "audit_turn" in tool_types,
        "error_env_present": "error_envelope" in tool_types,
        "public_has_tool": any((str(x.get("role") or "").lower() == "tool") for x in (all_public_msgs or [])),
        "tool_types": sorted(tool_types),
        "pending_state": pending_state,
        "clarification": clarification,
        "meta_clarification": is_meta_clarification(assistant_text),
        "planner_plan": plan,
        "business_request_spec": business_spec,
        "result_quality_gate": gate,
        "quality_verdict": str(gate.get("verdict") or ""),
        "quality_failed_check_ids": sorted(list(set(failed_ids))),
        "duration_ms": duration_ms,
        "applied_filters": last_result_tool.get("filters") if isinstance(last_result_tool.get("filters"), dict) else {},
        "executed_as_user": USER,
    }


def send_and_capture(session_name: str, prompt: str) -> Dict[str, Any]:
    before_debug = get_messages(session_name, debug=1)
    before_idx = _max_idx(before_debug)

    send_out = chat_send(session_name, prompt)

    after_debug: List[Dict[str, Any]] = []
    after_public: List[Dict[str, Any]] = []
    new_msgs: List[Dict[str, Any]] = []
    deadline = time.time() + 20.0
    while True:
        after_debug = get_messages(session_name, debug=1)
        after_public = get_messages(session_name, debug=0)
        new_msgs = _new_msgs(after_debug, before_idx)

        has_new_assistant = any(str(x.get("role") or "").lower() == "assistant" for x in new_msgs)
        if has_new_assistant:
            break
        if time.time() >= deadline:
            break
        time.sleep(0.4)

    actual = _extract_turn_actual(new_msgs, after_public)
    actual["send_ok"] = bool(send_out.get("ok"))
    actual["send_error"] = None if send_out.get("ok") else (send_out.get("stderr") or send_out.get("stdout"))
    return actual


def pass_rule(
    case_id: str,
    actual: Dict[str, Any],
    semantic: Dict[str, Any],
) -> Tuple[bool, str]:
    t = str(actual.get("assistant_type") or "")
    txt = str(actual.get("assistant_text") or "").strip().lower()
    pending = actual.get("pending_mode")
    rows = int(actual.get("rows") or 0)
    cols = int(actual.get("columns") or 0)
    dl = int(actual.get("downloads") or 0)
    pstate = actual.get("pending_state") if isinstance(actual.get("pending_state"), dict) else {}
    opts = pstate.get("options") if isinstance(pstate.get("options"), list) else []
    labels = [str(x or "").strip().lower() for x in (actual.get("column_labels") or []) if str(x or "").strip()]
    expected_doc = str(actual.get("expected_doc") or "").strip().lower()
    blocker_clar = bool(semantic.get("blocker_clarification"))
    semantic_required_pass = bool(semantic.get("required_pass"))

    ok = False

    if case_id == "FIN-01":
        ok = (t == "report_table" and pending is None and rows >= 1)
    elif case_id == "FIN-02":
        if t == "report_table" and pending is None:
            ok = True
        else:
            ok = (t == "text" and pending in ("planner_clarify", "need_filters") and blocker_clar)
    elif case_id == "FIN-03":
        ok = (t == "report_table" and rows >= 1 and pending is None)
    elif case_id == "FIN-04":
        ok = (t == "report_table" and rows >= 1 and pending is None)
    elif case_id == "SAL-01":
        ok = (t == "report_table" and rows == 5 and pending is None)
    elif case_id == "SAL-02":
        ok = (t == "report_table" and dl >= 1 and pending is None)
    elif case_id == "STK-01":
        ok = (t == "report_table" and rows >= 1 and pending is None)
    elif case_id == "STK-02":
        ok = (t == "report_table" and rows >= 1 and pending is None)
    elif case_id == "HR-01":
        if t == "report_table" and pending is None:
            ok = True
        else:
            ok = (t == "text" and pending in ("planner_clarify", "need_filters") and blocker_clar)
    elif case_id == "OPS-01":
        ok = (t == "report_table" and pending is None)
    elif case_id == "COR-01":
        ok = (t == "report_table" and pending is None and rows >= 1)
    elif case_id == "DET-01":
        has_customer_col = any(("customer" in lb) for lb in labels)
        has_revenue_col = any(("revenue" in lb or "total" in lb or "value" in lb) for lb in labels)
        ok = (t == "report_table" and pending is None and cols <= 4 and has_customer_col and has_revenue_col)
    elif case_id == "DOC-01":
        # Detail retrieval must not collapse to generic clarification for clear doc-id ask.
        if t == "report_table" and pending is None and rows >= 1:
            ok = True
        elif t == "text" and pending is None and bool(expected_doc) and expected_doc in txt:
            ok = True
        else:
            ok = False
    elif case_id == "CFG-01":
        ok = (t == "text" and pending == "planner_clarify" and not is_meta_clarification(txt))
    elif case_id == "CFG-02":
        ok = (t == "report_table" and pending is None)
    elif case_id == "CFG-03":
        ok = (not is_meta_clarification(txt))
    elif case_id == "ENT-01":
        ok = (t == "text" and "couldn" in txt and "which exact value should i use" in txt and pending == "need_filters")
    elif case_id == "ENT-02":
        ok = (t == "text" and "multiple matches" in txt and "which one should i use" in txt and pending == "need_filters" and len(opts) >= 2)
    elif case_id == "WR-01":
        ok = (t == "text" and "write-actions are disabled" in txt and pending is None)
    elif case_id == "WR-02":
        ok = (t == "text" and "reply **confirm**" in txt and pending == "write_confirmation")
    elif case_id == "WR-03":
        ok = (t == "text" and "write action canceled" in txt and pending is None)
    elif case_id == "WR-04":
        ok = (t == "text" and "confirmed. deleted" in txt and pending is None)
    elif case_id == "OBS-01":
        ok = (not bool(actual.get("public_has_tool")))
    elif case_id == "OBS-02":
        ok = bool(actual.get("audit_present"))
    elif case_id == "ERR-01":
        safe_txt = "i couldn’t process that request right now" in txt or "i couldn't process that request right now" in txt
        no_stack = ("traceback" not in txt and "exception" not in txt)
        ok = (t == "error" and safe_txt and no_stack and bool(actual.get("error_env_present")))
    elif case_id == "EXP-01":
        ok = (t == "report_table" and dl == 0 and pending is None)
    else:
        return False, "unknown_case"

    if not semantic_required_pass:
        return False, "semantic_assertions_failed"
    return ok, ""


def add_result(
    results: List[Dict[str, Any]],
    case_id: str,
    prompt: str,
    expected: str,
    actual: Dict[str, Any],
    defect_id: str = "",
    note: str = "",
    role: str = "ai.reader",
) -> None:
    semantic = evaluate_case_assertions(case_id, actual)
    ok, extra_note = pass_rule(case_id, actual, semantic)
    note_out = note
    if extra_note:
        note_out = f"{note_out}; {extra_note}" if note_out else extra_note
    results.append(
        {
            "id": case_id,
            "role": role,
            "prompt": prompt,
            "expected": expected,
            "actual": actual,
            "semantic": semantic,
            "pass": bool(ok),
            "defect_id": defect_id if not ok else "",
            "note": note_out,
        }
    )
    at = str(actual.get("assistant_type") or "")
    tx = str(actual.get("assistant_text") or "").strip().replace("\n", " ")
    print(
        f"[{case_id}] {'PASS' if ok else 'FAIL'} | type={at} | sem=({semantic.get('summary')}) | text={tx[:140]}",
        flush=True,
    )


def preconditions() -> Dict[str, Any]:
    out = {
        "report_list_ok": False,
        "report_requirements_ok": False,
        "generate_report_ok": False,
        "report_list_count": 0,
        "report_requirements_error": "",
        "generate_report_error": "",
    }

    r1 = bench_execute("ai_assistant_ui.ai_core.tools_read.report_list", {})
    if r1.get("ok") and isinstance(r1.get("data"), dict):
        reports = r1["data"].get("reports")
        if isinstance(reports, list):
            out["report_list_ok"] = True
            out["report_list_count"] = len(reports)

    r2 = bench_execute(
        "ai_assistant_ui.ai_core.tools_read.report_requirements",
        {"report_name": "Accounts Receivable"},
    )
    if r2.get("ok") and isinstance(r2.get("data"), dict):
        out["report_requirements_ok"] = True
    else:
        out["report_requirements_error"] = (r2.get("stderr") or r2.get("stdout") or "")[:240]

    r3 = bench_execute(
        "ai_assistant_ui.ai_core.tools_read.generate_report",
        {"report_name": "Accounts Receivable", "filters": {}, "format": "json"},
    )
    if r3.get("ok") and isinstance(r3.get("data"), dict):
        out["generate_report_ok"] = True
    else:
        out["generate_report_error"] = (r3.get("stderr") or r3.get("stdout") or "")[:240]

    return out


def run_err_case_with_forced_failure() -> Dict[str, Any]:
    sess_name, create_out = create_session("Phase2 ERR-01")
    if not sess_name:
        return {
            "assistant_type": "error",
            "assistant_text": "session_create_failed",
            "assistant_title": None,
            "downloads": 0,
            "rows": 0,
            "assistant_idx": None,
            "pending_mode": None,
            "pending_cleared": False,
            "options_count": 0,
            "audit_present": False,
            "error_env_present": False,
            "public_has_tool": False,
            "tool_types": [],
            "pending_state": {"mode": None, "base_question": None, "clarification_question": None, "clarification_options": [], "options": []},
            "clarification": False,
            "meta_clarification": False,
            "send_ok": False,
            "send_error": create_out.get("stderr") or create_out.get("stdout"),
        }

    py = f"""
import os, json
os.chdir('/home/frappe/frappe-bench/sites')
import frappe
from ai_assistant_ui.ai_core.chat import service
frappe.init(site='{SITE}', sites_path='.')
frappe.connect()
frappe.set_user('{USER}')
orig = service.run_tool
try:
    def _boom(*args, **kwargs):
        raise RuntimeError('forced_phase2_canary_failure')
    service.run_tool = _boom
    ok, msg = service.handle_user_message(session_name='{sess_name}', message='Show stock balance', user='{USER}')
    frappe.db.commit()
    print(json.dumps({{'ok': ok, 'msg': msg}}, ensure_ascii=False))
finally:
    service.run_tool = orig
    frappe.destroy()
"""
    cmd = [
        "docker", "compose", "exec", "-T", "backend", "bash", "-lc",
        "cd /home/frappe/frappe-bench && ./env/bin/python - <<'PY'\n" + py + "\nPY",
    ]
    res = _run(cmd)

    dbg = get_messages(sess_name, debug=1)
    pub = get_messages(sess_name, debug=0)
    actual = _extract_turn_actual(dbg, pub)
    actual["send_ok"] = (res.returncode == 0)
    actual["send_error"] = None if res.returncode == 0 else (res.stderr or res.stdout)

    delete_session(sess_name)
    return actual


def main():
    before_cfg = show_config()
    orch_before = before_cfg.get("ai_assistant_orchestrator_v2_enabled")
    write_before = before_cfg.get("ai_assistant_write_enabled")

    set_config("ai_assistant_orchestrator_v2_enabled", 1)
    set_config("ai_assistant_write_enabled", 0)

    results: List[Dict[str, Any]] = []
    todos_for_cleanup: List[str] = []

    try:
        pre = preconditions()

        s_fin, _ = create_session("Phase2 FIN")
        if s_fin:
            add_result(results, "FIN-01", "Show accounts receivable as of today", "Returns FAC-backed result directly; no clarification for clear ask.", send_and_capture(s_fin, "Show accounts receivable as of today"))
            add_result(results, "FIN-03", "Total outstanding amount", "Uses transform_last only and returns total in same turn.", send_and_capture(s_fin, "Total outstanding amount"))
            add_result(results, "FIN-04", "Sort that by outstanding amount descending", "Deterministic sort transform on last-result rows in same turn.", send_and_capture(s_fin, "Sort that by outstanding amount descending"))
            delete_session(s_fin)

        s, _ = create_session("Phase2 FIN-02")
        if s:
            add_result(results, "FIN-02", "Show accounts receivable last month", "Returns date-scoped FAC result directly when report supports it; otherwise one concrete constraint mismatch question.", send_and_capture(s, "Show accounts receivable last month"))
            delete_session(s)

        s, _ = create_session("Phase2 SAL-01")
        if s:
            add_result(results, "SAL-01", "Top 5 customers by revenue in last month", "Returns top-5 customer ranking table (customer + revenue), sorted desc, no clarification loop.", send_and_capture(s, "Top 5 customers by revenue in last month"))
            delete_session(s)

        s, _ = create_session("Phase2 SAL-02")
        if s:
            add_result(results, "SAL-02", "Show sales by item and download excel", "Export only because explicitly requested.", send_and_capture(s, "Show sales by item and download excel"))
            delete_session(s)

        s_stk, _ = create_session("Phase2 STK")
        if s_stk:
            add_result(results, "STK-01", "Show stock balance in Main warehouse", "Warehouse constraint enforced; returns result directly when unambiguous.", send_and_capture(s_stk, "Show stock balance in Main warehouse"))
            add_result(results, "STK-02", "Show stock balance in the same warehouse", "Reuses follow-up context and returns result without re-asking same filter.", send_and_capture(s_stk, "Show stock balance in the same warehouse"))
            delete_session(s_stk)

        s, _ = create_session("Phase2 HR")
        if s:
            add_result(
                results,
                "HR-01",
                "Which employee has attendance issues this month?",
                "Returns report-based response directly for clear ask (or one concrete required-input clarification).",
                send_and_capture(s, "Which employee has attendance issues this month?"),
                role="ai.operator",
            )
            delete_session(s)

        s, _ = create_session("Phase2 OPS")
        if s:
            add_result(
                results,
                "OPS-01",
                "What are the open material requests for production",
                "Planner selects report path; response from FAC only.",
                send_and_capture(s, "What are the open material requests for production"),
                role="ai.operator",
            )
            delete_session(s)

        s_cor, _ = create_session("Phase2 COR-01")
        if s_cor:
            _ = send_and_capture(s_cor, "Top 5 products by received qty in last month")
            add_result(
                results,
                "COR-01",
                "I mean sold qty, not received qty",
                "Reroutes metric semantics to sold qty without topic contamination.",
                send_and_capture(s_cor, "I mean sold qty, not received qty"),
            )
            delete_session(s_cor)

        s_det, _ = create_session("Phase2 DET-01")
        if s_det:
            _ = send_and_capture(s_det, "Top 5 customers by revenue in last month")
            add_result(
                results,
                "DET-01",
                "Show only customer and revenue columns",
                "Returns requested minimal business columns only.",
                send_and_capture(s_det, "Show only customer and revenue columns"),
            )
            delete_session(s_det)

        s_doc, _ = create_session("Phase2 DOC-01")
        if s_doc:
            sales_invoice = get_first_doc_name("Sales Invoice", {"docstatus": 1}) or get_first_doc_name("Sales Invoice")
            target_doc = sales_invoice or "SINV-0001"
            doc_prompt = f"Show details for Sales Invoice {target_doc}"
            doc_actual = send_and_capture(s_doc, doc_prompt)
            doc_actual["expected_doc"] = target_doc
            doc_note = "" if sales_invoice else "sales_invoice_sample_missing_fallback=SINV-0001"
            add_result(
                results,
                "DOC-01",
                doc_prompt,
                "Returns targeted document details, not generic aggregate summary.",
                doc_actual,
                note=doc_note,
                role="ai.operator",
            )
            delete_session(s_doc)

        s_cfg, _ = create_session("Phase2 CFG")
        if s_cfg:
            add_result(results, "CFG-01", "Show the report", "Asks exactly one clarification question.", send_and_capture(s_cfg, "Show the report"))
            add_result(results, "CFG-02", "Show open material requests for production", "Pending flow is canceled and new topic starts.", send_and_capture(s_cfg, "Show open material requests for production"))
            delete_session(s_cfg)

        s, _ = create_session("Phase2 CFG-03")
        if s:
            add_result(results, "CFG-03", "Top 5 customers by revenue in last month", "Must not ask abstract planner-preference questions (metric vs grouping vs period).", send_and_capture(s, "Top 5 customers by revenue in last month"))
            delete_session(s)

        s, _ = create_session("Phase2 ENT-01")
        if s:
            add_result(results, "ENT-01", "Show stock balance in warehouse ZZZ-NO-MATCH-999999", "Asks refine question; does not guess names.", send_and_capture(s, "Show stock balance in warehouse ZZZ-NO-MATCH-999999"))
            delete_session(s)

        s, _ = create_session("Phase2 ENT-02")
        if s:
            add_result(results, "ENT-02", "Show stock balance in warehouse mmob", "Presents options and asks to choose one.", send_and_capture(s, "Show stock balance in warehouse mmob"), defect_id="UAT-ENT-02-001")
            delete_session(s)

        set_config("ai_assistant_write_enabled", 0)
        s, _ = create_session("Phase2 WR-01")
        if s:
            add_result(
                results,
                "WR-01",
                "Create a ToDo for follow-up",
                "Returns write-disabled message; no write execution.",
                send_and_capture(s, "Create a ToDo for follow-up"),
                role="ai.operator",
            )
            delete_session(s)

        set_config("ai_assistant_write_enabled", 1)
        todo_a = create_todo("phase2 canary WR-02")
        if todo_a:
            todos_for_cleanup.append(todo_a)
        s_wr, _ = create_session("Phase2 WR-02-03")
        if s_wr and todo_a:
            add_result(
                results,
                "WR-02",
                f"Delete ToDo {todo_a}",
                "Requires explicit confirmation before execution.",
                send_and_capture(s_wr, f"Delete ToDo {todo_a}"),
                role="ai.operator",
            )
            add_result(
                results,
                "WR-03",
                "cancel",
                "Cancels write and clears pending state.",
                send_and_capture(s_wr, "cancel"),
                role="ai.operator",
            )
            delete_session(s_wr)

        todo_b = create_todo("phase2 canary WR-04")
        if todo_b:
            todos_for_cleanup.append(todo_b)
        s_wr4, _ = create_session("Phase2 WR-04")
        if s_wr4 and todo_b:
            _ = send_and_capture(s_wr4, f"Delete ToDo {todo_b}")
            add_result(
                results,
                "WR-04",
                f"Delete ToDo {todo_b} -> confirm",
                "Executes exactly one draft action and returns safe result text.",
                send_and_capture(s_wr4, "confirm"),
                role="ai.operator",
            )
            delete_session(s_wr4)

        s_obs, _ = create_session("Phase2 OBS")
        if s_obs:
            _ = send_and_capture(s_obs, "Show accounts receivable as of today")
            msgs0 = get_messages(s_obs, debug=0)
            msgs1 = get_messages(s_obs, debug=1)

            obs1_actual = {
                "assistant_type": "observe",
                "assistant_text": "",
                "assistant_title": None,
                "downloads": 0,
                "rows": 0,
                "assistant_idx": None,
                "pending_mode": None,
                "pending_cleared": False,
                "options_count": 0,
                "audit_present": False,
                "error_env_present": False,
                "public_has_tool": any((str(x.get("role") or "").lower() == "tool") for x in msgs0),
                "tool_types": [],
                "pending_state": {"mode": None, "base_question": None, "clarification_question": None, "clarification_options": [], "options": []},
                "clarification": False,
                "meta_clarification": False,
                "send_ok": True,
                "send_error": None,
            }
            add_result(
                results,
                "OBS-01",
                "get_messages(debug=0)",
                "No tool/internal messages in normal user view.",
                obs1_actual,
            )

            tool_types_dbg = set()
            for m in msgs1:
                if str(m.get("role") or "").lower() != "tool":
                    continue
                obj = _parse_content(m.get("content"))
                if isinstance(obj, dict):
                    t = str(obj.get("type") or "").strip()
                    if t:
                        tool_types_dbg.add(t)
            obs2_actual = {
                **obs1_actual,
                "assistant_type": "observe",
                "audit_present": "audit_turn" in tool_types_dbg,
                "tool_types": sorted(tool_types_dbg),
            }
            add_result(
                results,
                "OBS-02",
                "get_messages(debug=1)",
                "Debug view includes audit_turn tool messages.",
                obs2_actual,
            )
            delete_session(s_obs)

        err_actual = run_err_case_with_forced_failure()
        add_result(results, "ERR-01", "Show stock balance", "User gets safe error text; no stacktrace/internal exception leakage.", err_actual)

        s, _ = create_session("Phase2 EXP")
        if s:
            add_result(results, "EXP-01", "Show sales by item for this month", "No export artifacts unless explicit request.", send_and_capture(s, "Show sales by item for this month"))
            delete_session(s)

    finally:
        set_config("ai_assistant_write_enabled", 0)
        if orch_before is not None:
            set_config("ai_assistant_orchestrator_v2_enabled", orch_before)
        if write_before is not None:
            set_config("ai_assistant_write_enabled", write_before)
        for td in todos_for_cleanup:
            delete_todo(td)

    role_defaults = {
        "HR-01": "ai.operator",
        "OPS-01": "ai.operator",
        "DOC-01": "ai.operator",
        "WR-01": "ai.operator",
        "WR-02": "ai.operator",
        "WR-03": "ai.operator",
        "WR-04": "ai.operator",
    }
    for r in results:
        rid = str(r.get("id") or "").strip()
        role = str(r.get("role") or "").strip()
        if not role or role == "Administrator":
            r["role"] = role_defaults.get(rid, "ai.reader")

    mandatory_ids = {
        "FIN-01", "FIN-02", "FIN-03", "FIN-04",
        "SAL-01", "SAL-02",
        "STK-01", "STK-02",
        "HR-01", "OPS-01",
        "COR-01", "DET-01", "DOC-01",
        "CFG-01", "CFG-02", "CFG-03",
        "ENT-01", "ENT-02",
        "WR-01", "WR-02", "WR-03", "WR-04",
        "OBS-01", "OBS-02",
        "ERR-01", "EXP-01",
    }
    critical_ids = {"FIN-01", "FIN-03", "FIN-04", "SAL-01", "CFG-03", "COR-01"}
    clear_read_ids = {
        "FIN-01", "FIN-02", "FIN-03", "FIN-04",
        "SAL-01", "SAL-02",
        "STK-01", "STK-02",
        "HR-01", "OPS-01",
        "COR-01", "DET-01", "DOC-01",
        "CFG-03", "EXP-01",
    }
    loop_scope_ids = clear_read_ids | {"CFG-01", "CFG-02", "ENT-01", "ENT-02"}

    executed_ids = {str(r.get("id") or "").strip() for r in results}
    missing_mandatory_ids = sorted(list(mandatory_ids - executed_ids))
    missing_critical_ids = sorted(list(critical_ids - executed_ids))

    for r in results:
        if r.get("pass"):
            continue
        if r.get("defect_id"):
            continue
        r["defect_id"] = f"UAT-{r.get('id')}-001"

    total = len(results)
    passed = sum(1 for r in results if r.get("pass"))
    failed = total - passed

    def _rate(num: int, den: int) -> float:
        return (float(num) / float(den)) if den else 0.0

    def _percentile(values: List[int], pct: float) -> Optional[int]:
        if not values:
            return None
        if len(values) == 1:
            return int(values[0])
        vs = sorted(values)
        pos = (float(pct) / 100.0) * float(len(vs) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(vs) - 1)
        frac = pos - float(lo)
        out = (float(vs[lo]) * (1.0 - frac)) + (float(vs[hi]) * frac)
        return int(round(out))

    clear_rows = [r for r in results if r.get("id") in clear_read_ids]
    clear_total = len(clear_rows)

    direct_answer_count = 0
    unnecessary_clar_count = 0
    wrong_report_count = 0
    meta_clar_count = 0
    clear_durations: List[int] = []
    for r in clear_rows:
        a = r.get("actual") if isinstance(r.get("actual"), dict) else {}
        sem = r.get("semantic") if isinstance(r.get("semantic"), dict) else {}
        assertions = sem.get("assertions") if isinstance(sem.get("assertions"), dict) else {}
        is_clar = bool(a.get("clarification"))
        a_type = str(a.get("assistant_type") or "").strip().lower()
        if (not is_clar) and a_type in ("report_table", "text") and a.get("pending_mode") is None:
            direct_answer_count += 1
        if is_clar and (not bool(sem.get("blocker_clarification"))):
            unnecessary_clar_count += 1
        if assertions.get("report_alignment_pass") is False:
            wrong_report_count += 1
        if bool(a.get("meta_clarification")) or bool(sem.get("meta_clarification")):
            meta_clar_count += 1
        try:
            d = int(a.get("duration_ms")) if a.get("duration_ms") is not None else None
        except Exception:
            d = None
        if isinstance(d, int) and d >= 0:
            clear_durations.append(d)

    loop_rows = [r for r in results if r.get("id") in loop_scope_ids]
    loop_total = len(loop_rows)
    loop_fail_count = 0
    for r in loop_rows:
        sem = r.get("semantic") if isinstance(r.get("semantic"), dict) else {}
        assertions = sem.get("assertions") if isinstance(sem.get("assertions"), dict) else {}
        if assertions.get("loop_policy_pass") is False:
            loop_fail_count += 1

    correction_rows = [r for r in results if r.get("id") == "COR-01"]
    correction_total = len(correction_rows)
    correction_fail_count = sum(1 for r in correction_rows if not r.get("pass"))

    reader_rows = [r for r in results if r.get("role") == "ai.reader"]
    operator_rows = [r for r in results if r.get("role") == "ai.operator"]
    reader_pass_rate = _rate(sum(1 for r in reader_rows if r.get("pass")), len(reader_rows))
    operator_pass_rate = _rate(sum(1 for r in operator_rows if r.get("pass")), len(operator_rows))
    role_parity = bool(reader_rows and operator_rows and abs(reader_pass_rate - operator_pass_rate) <= 0.05)

    direct_answer_rate = _rate(direct_answer_count, clear_total)
    unnecessary_clar_rate = _rate(unnecessary_clar_count, clear_total)
    wrong_report_rate = _rate(wrong_report_count, clear_total)
    loop_rate = _rate(loop_fail_count, loop_total)
    user_correction_rate = _rate(correction_fail_count, correction_total)
    latency_p50_ms = _percentile(clear_durations, 50.0)
    latency_p95_ms = _percentile(clear_durations, 95.0)

    mandatory_pass_100 = (failed == 0 and len(missing_mandatory_ids) == 0)
    critical_rows = [r for r in results if r.get("id") in critical_ids]
    critical_pass_100 = (len(missing_critical_ids) == 0 and all(r.get("pass") for r in critical_rows))
    direct_ge_90 = direct_answer_rate >= 0.90
    unnecessary_clar_le_5 = unnecessary_clar_rate <= 0.05
    wrong_report_le_3 = wrong_report_rate <= 0.03
    loop_lt_1 = loop_rate < 0.01
    zero_meta = (meta_clar_count == 0)
    fac_preconditions_ok = bool(pre.get("report_list_ok") and pre.get("report_requirements_ok") and pre.get("generate_report_ok"))

    payload = {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": SITE,
        "user": USER,
        "mode": "phase6_canary",
        "run_policy": {
            "gate_source": "first_run_only",
            "rerun_policy": "diagnostic_only_non_gating",
        },
        "flags": {
            "orchestrator_flag_key": "ai_assistant_orchestrator_v2_enabled",
            "orchestrator_flag_before": orch_before,
            "orchestrator_flag_during": 1,
            "write_flag_key": "ai_assistant_write_enabled",
            "write_flag_before": write_before,
            "write_flag_during_default": 0,
            "write_flag_wr_phase": 1,
        },
        "preconditions": pre,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "missing_mandatory_ids": missing_mandatory_ids,
            "clear_read_total": clear_total,
            "direct_answer_count_clear_read": direct_answer_count,
            "direct_answer_rate_clear_read": round(direct_answer_rate, 4),
            "unnecessary_clarification_count_clear_read": unnecessary_clar_count,
            "unnecessary_clarification_rate_clear_read": round(unnecessary_clar_rate, 4),
            "wrong_report_count_clear_read": wrong_report_count,
            "wrong_report_rate_clear_read": round(wrong_report_rate, 4),
            "loop_fail_count": loop_fail_count,
            "loop_scope_total": loop_total,
            "clarification_loop_rate": round(loop_rate, 4),
            "meta_clarification_count_clear_read": meta_clar_count,
            "user_correction_total": correction_total,
            "user_correction_fail_count": correction_fail_count,
            "user_correction_rate": round(user_correction_rate, 4),
            "latency_p50_ms_clear_read": latency_p50_ms,
            "latency_p95_ms_clear_read": latency_p95_ms,
            "reader_total": len(reader_rows),
            "reader_pass_rate": round(reader_pass_rate, 4),
            "operator_total": len(operator_rows),
            "operator_pass_rate": round(operator_pass_rate, 4),
        },
        "release_gate": {
            "mandatory_pass_rate_100": mandatory_pass_100,
            "critical_clear_query_pass_100": critical_pass_100,
            "fac_preconditions_ok": fac_preconditions_ok,
            "direct_answer_rate_clear_read_ge_90pct": direct_ge_90,
            "unnecessary_clarification_rate_clear_read_le_5pct": unnecessary_clar_le_5,
            "wrong_report_rate_clear_read_le_3pct": wrong_report_le_3,
            "clarification_loop_rate_lt_1pct": loop_lt_1,
            "zero_meta_clarification_on_clear_asks": zero_meta,
            "role_parity_reader_vs_operator": role_parity,
            "overall_go": bool(
                mandatory_pass_100
                and critical_pass_100
                and fac_preconditions_ok
                and direct_ge_90
                and unnecessary_clar_le_5
                and wrong_report_le_3
                and loop_lt_1
                and zero_meta
                and role_parity
            ),
        },
        "results": results,
    }

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = Path("impl_factory/04_automation/logs") / f"{ts}_phase6_canary_uat_raw_v3.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OUT={out_path}")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(json.dumps(payload["release_gate"], ensure_ascii=False))
    for r in results:
        if not r.get("pass"):
            a = r.get("actual") or {}
            print(f"FAIL {r.get('id')}: {a.get('assistant_type')} :: {a.get('assistant_text')}")


if __name__ == "__main__":
    main()
