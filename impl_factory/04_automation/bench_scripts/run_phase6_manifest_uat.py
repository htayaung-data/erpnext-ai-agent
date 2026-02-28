from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from semantic_assertions import evaluate_case_assertions, is_meta_clarification

from run_phase6_canary_uat import (
    DEFAULT_MANIFEST,
    SITE,
    USER,
    _compute_behavior_metrics,
    _load_behavior_manifest,
    _parse_content,
    _safe_rate,
    _to_lc_set,
    bench_execute,
    create_session,
    create_todo,
    delete_session,
    delete_todo,
    get_first_doc_name,
    get_messages,
    pass_rule,
    preconditions,
    run_err_case_with_forced_failure,
    send_and_capture,
    set_config,
    show_config,
)


def _canonical_case_id(case_id: str, variant_of: str) -> str:
    base = str(variant_of or "").strip()
    if base:
        return base
    cid = str(case_id or "").strip()
    if "__" in cid:
        return cid.split("__", 1)[0].strip()
    return cid


def _load_manifest_rows(manifest_path: Path, suites: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest is not a JSON object")
    packs = [p for p in list(manifest.get("packs") or []) if isinstance(p, dict)]
    allowed = _to_lc_set(suites or set())

    rows: List[Dict[str, Any]] = []
    for p in packs:
        suite = str(p.get("name") or "").strip()
        if allowed and suite.lower() not in allowed:
            continue
        file_name = str(p.get("file") or "").strip()
        if not file_name:
            continue
        pack_path = (manifest_path.parent / file_name).resolve()
        if not pack_path.exists():
            continue
        for line in pack_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s:
                continue
            obj = json.loads(s)
            if isinstance(obj, dict):
                obj["_suite_name"] = suite
                rows.append(obj)
    return rows


def _observability_actual(session_name: str, debug_flag: int) -> Dict[str, Any]:
    msgs = get_messages(session_name, debug=int(debug_flag))
    if int(debug_flag) == 0:
        return {
            "assistant_type": "observe",
            "assistant_text": "",
            "assistant_title": None,
            "downloads": 0,
            "rows": 0,
            "columns": 0,
            "column_labels": [],
            "assistant_idx": None,
            "pending_mode": None,
            "pending_cleared": False,
            "options_count": 0,
            "audit_present": False,
            "error_env_present": False,
            "public_has_tool": any((str(x.get("role") or "").lower() == "tool") for x in msgs),
            "tool_types": [],
            "pending_state": {"mode": None, "base_question": None, "clarification_question": None, "clarification_options": [], "options": []},
            "clarification": False,
            "meta_clarification": False,
            "planner_plan": {},
            "business_request_spec": {},
            "result_quality_gate": {},
            "quality_verdict": "",
            "quality_failed_check_ids": [],
            "duration_ms": None,
            "applied_filters": {},
            "executed_as_user": USER,
            "send_ok": True,
            "send_error": None,
        }

    tool_types_dbg = set()
    for m in msgs:
        if str(m.get("role") or "").lower() != "tool":
            continue
        obj = _parse_content(m.get("content"))
        if isinstance(obj, dict):
            typ = str(obj.get("type") or "").strip()
            if typ:
                tool_types_dbg.add(typ)
    return {
        "assistant_type": "observe",
        "assistant_text": "",
        "assistant_title": None,
        "downloads": 0,
        "rows": 0,
        "columns": 0,
        "column_labels": [],
        "assistant_idx": None,
        "pending_mode": None,
        "pending_cleared": False,
        "options_count": 0,
        "audit_present": "audit_turn" in tool_types_dbg,
        "error_env_present": False,
        "public_has_tool": False,
        "tool_types": sorted(tool_types_dbg),
        "pending_state": {"mode": None, "base_question": None, "clarification_question": None, "clarification_options": [], "options": []},
        "clarification": False,
        "meta_clarification": False,
        "planner_plan": {},
        "business_request_spec": {},
        "result_quality_gate": {},
        "quality_verdict": "",
        "quality_failed_check_ids": [],
        "duration_ms": None,
        "applied_filters": {},
        "executed_as_user": USER,
        "send_ok": True,
        "send_error": None,
    }


def _row_role(row: Dict[str, Any], canonical_case_id: str) -> str:
    role = str(row.get("role") or "").strip()
    if role:
        return role
    if canonical_case_id in {"HR-01", "OPS-01", "DOC-01", "LST-01", "WR-01", "WR-02", "WR-03", "WR-04"}:
        return "ai.operator"
    return "ai.reader"


def _replace_placeholders(
    *,
    text: str,
    sample_doc: Optional[str],
    sample_todo: Optional[str],
) -> str:
    out = str(text or "")
    if "<sample_doc>" in out:
        out = out.replace("<sample_doc>", str(sample_doc or "SINV-0001"))
    if "<sample_todo>" in out:
        out = out.replace("<sample_todo>", str(sample_todo or "TODO-MISSING"))
    return out


def _case_error_actual(error_text: str) -> Dict[str, Any]:
    msg = str(error_text or "").strip()
    return {
        "assistant_type": "error",
        "assistant_text": msg,
        "assistant_title": None,
        "downloads": 0,
        "rows": 0,
        "columns": 0,
        "column_labels": [],
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
        "planner_plan": {},
        "business_request_spec": {},
        "result_quality_gate": {},
        "quality_verdict": "",
        "quality_failed_check_ids": [],
        "duration_ms": None,
        "applied_filters": {},
        "executed_as_user": USER,
        "send_ok": False,
        "send_error": msg,
    }


def _execute_case(
    *,
    row: Dict[str, Any],
    canonical_case_id: str,
    sample_doc: Optional[str],
    todos_for_cleanup: List[str],
) -> Tuple[Dict[str, Any], str]:
    turns = row.get("turns") if isinstance(row.get("turns"), list) else []
    if not turns:
        return _case_error_actual("case_has_no_turns"), ""

    if canonical_case_id == "ERR-01":
        return run_err_case_with_forced_failure(), ""

    # Case-local setup for context-dependent behaviors.
    sample_todo: Optional[str] = None
    if canonical_case_id in {"WR-02", "WR-03", "WR-04"}:
        sample_todo = create_todo(f"phase6 manifest {row.get('case_id')}")
        if sample_todo:
            todos_for_cleanup.append(sample_todo)

    session_name, create_out = create_session(f"Phase6 MANIFEST {row.get('case_id')}")
    if not session_name:
        err = create_out.get("stderr") or create_out.get("stdout") or "session_create_failed"
        return _case_error_actual(str(err)), ""

    note = ""
    try:
        if canonical_case_id == "STK-02":
            _ = send_and_capture(session_name, "Show stock balance in Main warehouse")
        elif canonical_case_id in {"WR-03", "WR-04"} and sample_todo:
            _ = send_and_capture(session_name, f"Delete ToDo {sample_todo}")
        elif canonical_case_id in {"OBS-01", "OBS-02"}:
            _ = send_and_capture(session_name, "Show accounts receivable as of today")

        actual: Optional[Dict[str, Any]] = None
        for t in turns:
            role = str(t.get("role") or "").strip().lower()
            text = str(t.get("text") or "").strip()
            if role == "user":
                prompt = _replace_placeholders(text=text, sample_doc=sample_doc, sample_todo=sample_todo)
                actual = send_and_capture(session_name, prompt)
            elif role == "system":
                sys_cmd = str(text or "").strip().lower()
                if "get_messages(debug=0)" in sys_cmd:
                    actual = _observability_actual(session_name, debug_flag=0)
                elif "get_messages(debug=1)" in sys_cmd:
                    actual = _observability_actual(session_name, debug_flag=1)
                else:
                    actual = _case_error_actual(f"unsupported_system_turn:{text}")
            else:
                actual = _case_error_actual(f"unsupported_turn_role:{role}")

        if actual is None:
            return _case_error_actual("case_produced_no_actual"), note

        if canonical_case_id == "DOC-01":
            expected_doc = str(sample_doc or "SINV-0001")
            actual["expected_doc"] = expected_doc
            if not sample_doc:
                note = "sales_invoice_sample_missing_fallback=SINV-0001"

        actual["meta_clarification"] = bool(actual.get("meta_clarification")) or is_meta_clarification(str(actual.get("assistant_text") or ""))
        return actual, note
    finally:
        delete_session(session_name)


def _render_prompt(turns: List[Dict[str, Any]]) -> str:
    items = []
    for t in turns:
        if str(t.get("role") or "").strip().lower() != "user":
            continue
        txt = str(t.get("text") or "").strip()
        if txt:
            items.append(txt)
    return " -> ".join(items) if items else "(no-user-turn)"


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 6 manifest-driven replay UAT runner.")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Replay manifest path.")
    ap.add_argument("--suite", action="append", dest="suites", default=[], help="Optional suite filter (repeatable).")
    ap.add_argument("--case-id", action="append", dest="case_ids", default=[], help="Optional case-id filter (repeatable).")
    ap.add_argument("--max-cases", type=int, default=0, help="Optional max cases (0 means all).")
    args = ap.parse_args()

    manifest_path = Path(str(args.manifest)).resolve()
    suite_filter = set(str(x).strip().lower() for x in list(args.suites or []) if str(x).strip())
    case_filter = set(str(x).strip() for x in list(args.case_ids or []) if str(x).strip())
    rows = _load_manifest_rows(manifest_path=manifest_path, suites=suite_filter if suite_filter else None)
    if case_filter:
        rows = [r for r in rows if str(r.get("case_id") or "").strip() in case_filter]
    if int(args.max_cases or 0) > 0:
        rows = rows[: int(args.max_cases)]

    behavior_manifest = _load_behavior_manifest(manifest_path)
    before_cfg = show_config()
    orch_before = before_cfg.get("ai_assistant_orchestrator_v2_enabled")
    write_before = before_cfg.get("ai_assistant_write_enabled")

    set_config("ai_assistant_orchestrator_v2_enabled", 1)
    set_config("ai_assistant_write_enabled", 0)

    results: List[Dict[str, Any]] = []
    todos_for_cleanup: List[str] = []

    sample_doc = get_first_doc_name("Sales Invoice", {"docstatus": 1}) or get_first_doc_name("Sales Invoice")

    try:
        pre = preconditions()
        for idx, row in enumerate(rows, start=1):
            case_id = str(row.get("case_id") or "").strip()
            variant_of = str(row.get("variant_of") or "").strip()
            canonical = _canonical_case_id(case_id=case_id, variant_of=variant_of)
            role = _row_role(row=row, canonical_case_id=canonical)
            behavior_class = str(row.get("behavior_class") or "").strip().lower()
            turns = row.get("turns") if isinstance(row.get("turns"), list) else []

            # Write path only where required by contract behavior class.
            write_enabled = 1 if canonical in {"WR-02", "WR-03", "WR-04"} else 0
            set_config("ai_assistant_write_enabled", write_enabled)

            try:
                actual, note = _execute_case(
                    row=row,
                    canonical_case_id=canonical,
                    sample_doc=sample_doc,
                    todos_for_cleanup=todos_for_cleanup,
                )
            except Exception as ex:
                actual, note = _case_error_actual(f"runner_exception:{ex}"), "runner_exception"

            semantic = evaluate_case_assertions(canonical, actual)
            ok, extra_note = pass_rule(canonical, actual, semantic)
            note_out = note
            if extra_note:
                note_out = f"{note_out}; {extra_note}" if note_out else extra_note

            results.append(
                {
                    "id": case_id,
                    "base_case_id": canonical,
                    "variant_of": variant_of,
                    "suite": str(row.get("_suite_name") or row.get("suite") or "").strip(),
                    "behavior_class": behavior_class,
                    "role": role,
                    "prompt": _render_prompt(turns),
                    "expected": row.get("expected"),
                    "actual": actual,
                    "semantic": semantic,
                    "pass": bool(ok),
                    "defect_id": "" if ok else f"UAT-{canonical}-001",
                    "note": note_out,
                    "tags": list(row.get("tags") or []),
                    "turn_count": len(turns),
                    "order_index": idx,
                }
            )

            t = str(actual.get("assistant_type") or "")
            txt = str(actual.get("assistant_text") or "").strip().replace("\n", " ")
            print(
                f"[{idx}/{len(rows)}] [{case_id}] {'PASS' if ok else 'FAIL'} | base={canonical} | class={behavior_class} | type={t} | sem=({semantic.get('summary')}) | text={txt[:140]}",
                flush=True,
            )
    finally:
        set_config("ai_assistant_write_enabled", 0)
        if orch_before is not None:
            set_config("ai_assistant_orchestrator_v2_enabled", orch_before)
        if write_before is not None:
            set_config("ai_assistant_write_enabled", write_before)
        for td in todos_for_cleanup:
            delete_todo(td)

    total = len(results)
    passed = sum(1 for r in results if bool(r.get("pass")))
    failed = int(total - passed)
    behavior_metrics = _compute_behavior_metrics(
        results=results,
        case_to_class=behavior_manifest.get("case_to_class") if isinstance(behavior_manifest.get("case_to_class"), dict) else {},
        target_classes=set(behavior_manifest.get("target_classes") or set()),
    )

    payload = {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": SITE,
        "user": USER,
        "mode": "phase6_manifest_replay",
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
        },
        "preconditions": pre if "pre" in locals() else {},
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "first_run_pass_rate": round(_safe_rate(passed, total), 4),
            "manifest_path": str(manifest_path),
            "suite_filter": sorted(list(suite_filter)),
            "case_filter_count": len(case_filter),
            "role_counts": {
                "ai.reader": sum(1 for r in results if str(r.get("role") or "") == "ai.reader"),
                "ai.operator": sum(1 for r in results if str(r.get("role") or "") == "ai.operator"),
            },
        },
        "behavior_class": behavior_metrics,
        "behavior_manifest": {
            "manifest_path": str(behavior_manifest.get("manifest_path") or ""),
            "manifest_exists": bool(behavior_manifest.get("manifest_exists")),
            "manifest_load_error": str(behavior_manifest.get("manifest_load_error") or ""),
            "field": str(behavior_manifest.get("behavior_field") or "behavior_class"),
            "target_classes": sorted(list(behavior_manifest.get("target_classes") or set())),
        },
        "results": results,
    }

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = Path("impl_factory/04_automation/logs") / f"{ts}_phase6_manifest_uat_raw_v3.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OUT={out_path}")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(json.dumps(payload["behavior_class"], ensure_ascii=False))


if __name__ == "__main__":
    main()
