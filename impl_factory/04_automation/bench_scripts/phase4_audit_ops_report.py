#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SITE = "erpai_prj1"
CMD_TIMEOUT_SEC = 120
LOG_DIR = Path("impl_factory/04_automation/logs")
DEFAULT_OUT = LOG_DIR / "latest_phase4_audit_ops_report.json"
ACTIONABLE_INTENTS = {"READ", "EXPORT", "TRANSFORM", "WRITE_DRAFT", "WRITE_CONFIRM"}
PLANNER_BACKED_INTENTS = {"READ", "EXPORT", "TRANSFORM", "WRITE_DRAFT"}


def _run(cmd: List[str], timeout_sec: int = CMD_TIMEOUT_SEC) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=int(timeout_sec))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", errors="ignore") if exc.stdout else "")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else "")
        stderr = (stderr + f"\nTIMEOUT after {int(timeout_sec)}s").strip()
        return subprocess.CompletedProcess(exc.cmd, 124, stdout=stdout, stderr=stderr)


def _parse_last_json(stdout: str) -> Any:
    lines = [ln.strip() for ln in str(stdout or "").splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("{") or ln.startswith("["):
            try:
                return json.loads(ln)
            except Exception:
                continue
    return None


def _fetch_recent_audit_sessions(*, site: str, session_limit: int, owner: str = "") -> List[Dict[str, Any]]:
    py = f"""
import os, json
os.chdir('/home/frappe/frappe-bench/sites')
import frappe
frappe.init(site={site!r}, sites_path='.')
frappe.connect()
try:
    rows = frappe.get_all(
        'AI Chat Session',
        fields=['name', 'title', 'modified', 'owner'],
        order_by='modified desc',
        limit_page_length={int(session_limit)},
    )
    owner_filter = {owner!r}.strip()
    out = []
    for row in rows:
        if owner_filter and str(row.get('owner') or '').strip() != owner_filter:
            continue
        doc = frappe.get_doc('AI Chat Session', row['name'])
        audits = []
        for m in doc.get('messages') or []:
            if str(getattr(m, 'role', '') or '').lower() != 'tool':
                continue
            raw = str(getattr(m, 'content', '') or '').strip()
            if not raw.startswith('{{'):
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if not isinstance(obj, dict) or str(obj.get('type') or '') != 'audit_turn':
                continue
            audits.append({{'idx': getattr(m, 'idx', None), 'audit': obj}})
        out.append({{
            'name': row.get('name'),
            'title': row.get('title'),
            'modified': str(row.get('modified') or ''),
            'owner': row.get('owner'),
            'audit_turns': audits,
        }})
    print(json.dumps(out, ensure_ascii=False, default=str))
finally:
    frappe.destroy()
"""
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "backend",
        "bash",
        "-lc",
        "cd /home/frappe/frappe-bench && ./env/bin/python - <<'PY'\n" + py + "\nPY",
    ]
    res = _run(cmd)
    data = _parse_last_json(res.stdout)
    if res.returncode != 0:
        raise RuntimeError((res.stderr or res.stdout or "phase4_audit_ops_report fetch failed").strip())
    return data if isinstance(data, list) else []


def _parse_ts(raw: Any) -> Optional[datetime]:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _payload_type(audit: Dict[str, Any]) -> str:
    meta = audit.get("result_meta") if isinstance(audit.get("result_meta"), dict) else {}
    return str(meta.get("payload_type") or "").strip().lower()


def _is_actionable_turn(audit: Dict[str, Any]) -> bool:
    intent = str(audit.get("intent") or "").strip().upper()
    return intent in ACTIONABLE_INTENTS


def _audit_completeness_missing(audit: Dict[str, Any]) -> List[str]:
    env = audit.get("turn_audit_envelope") if isinstance(audit.get("turn_audit_envelope"), dict) else {}
    missing: List[str] = []

    def need(path: str, value: Any) -> None:
        if value is None:
            missing.append(path)
            return
        if isinstance(value, str) and (not value.strip()):
            missing.append(path)

    def need_bool(path: str, obj: Any, key: str) -> None:
        if not isinstance(obj, dict) or key not in obj or not isinstance(obj.get(key), bool):
            missing.append(path)

    need("schema_version", env.get("schema_version"))
    need("trace_id", env.get("trace_id"))
    need("engine_version", env.get("engine_version"))
    need("engine_mode", env.get("engine_mode"))
    need("capability_version", env.get("capability_version"))
    need("final_response_hash", env.get("final_response_hash"))
    if not isinstance(env.get("latency_ms"), int):
        missing.append("latency_ms")

    sec = env.get("security_outcome") if isinstance(env.get("security_outcome"), dict) else {}
    need("security_outcome.status", sec.get("status"))

    fallback = env.get("fallback_used") if isinstance(env.get("fallback_used"), dict) else {}
    need_bool("fallback_used.plan", fallback, "plan")
    need_bool("fallback_used.spec", fallback, "spec")
    need_bool("fallback_used.any", fallback, "any")

    vr = env.get("validation_result") if isinstance(env.get("validation_result"), dict) else {}
    if not str(vr.get("quality_verdict") or "").strip() and not str(vr.get("error_code") or "").strip():
        missing.append("validation_result.quality_verdict_or_error_code")

    intent = str(audit.get("intent") or "").strip().upper()
    model = env.get("model_version") if isinstance(env.get("model_version"), dict) else {}
    prompt = env.get("prompt_version") if isinstance(env.get("prompt_version"), dict) else {}
    if intent in PLANNER_BACKED_INTENTS:
        need("model_version.spec", model.get("spec"))
        need("prompt_version.spec", prompt.get("spec"))

    selected = env.get("selected_candidate") if isinstance(env.get("selected_candidate"), dict) else {}
    if _payload_type(audit) == "table":
        need("selected_candidate.report_name", selected.get("report_name"))

    return missing


def build_phase4_audit_ops_report(
    *,
    session_rows: List[Dict[str, Any]],
    since_hours: int,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max(0, int(since_hours)))
    missing_counter: Counter[str] = Counter()
    security_counter: Counter[str] = Counter()

    scanned_sessions = 0
    sessions_with_audit = 0
    audit_turns = 0
    actionable_turns = 0
    complete_actionable_turns = 0
    fallback_any_true = 0
    fallback_plan_true = 0
    fallback_spec_true = 0
    recent_incomplete: List[Dict[str, Any]] = []

    for session in list(session_rows or []):
        scanned_sessions += 1
        audits = [a for a in list(session.get("audit_turns") or []) if isinstance(a, dict)]
        if audits:
            sessions_with_audit += 1
        for entry in audits:
            audit = entry.get("audit") if isinstance(entry.get("audit"), dict) else {}
            ts = _parse_ts(audit.get("ts"))
            if ts is None or ts < cutoff:
                continue
            audit_turns += 1
            env = audit.get("turn_audit_envelope") if isinstance(audit.get("turn_audit_envelope"), dict) else {}
            fallback = env.get("fallback_used") if isinstance(env.get("fallback_used"), dict) else {}
            security = env.get("security_outcome") if isinstance(env.get("security_outcome"), dict) else {}
            status = str(security.get("status") or "missing").strip() or "missing"
            security_counter[status] += 1
            if bool(fallback.get("any")):
                fallback_any_true += 1
            if bool(fallback.get("plan")):
                fallback_plan_true += 1
            if bool(fallback.get("spec")):
                fallback_spec_true += 1

            if not _is_actionable_turn(audit):
                continue

            actionable_turns += 1
            missing = _audit_completeness_missing(audit)
            if not missing:
                complete_actionable_turns += 1
                continue
            for item in missing:
                missing_counter[item] += 1
            if len(recent_incomplete) < 20:
                recent_incomplete.append(
                    {
                        "session_name": str(session.get("name") or "").strip(),
                        "turn_id": str(audit.get("turn_id") or "").strip(),
                        "ts": str(audit.get("ts") or "").strip(),
                        "intent": str(audit.get("intent") or "").strip(),
                        "payload_type": _payload_type(audit),
                        "missing_fields": missing,
                        "trace_id": str(env.get("trace_id") or "").strip(),
                    }
                )

    incomplete_actionable_turns = max(0, actionable_turns - complete_actionable_turns)
    completeness_rate = round((complete_actionable_turns / actionable_turns), 4) if actionable_turns else 1.0

    return {
        "schema_version": "phase4_audit_ops_report_v1",
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {
            "since_hours": int(since_hours),
            "cutoff_utc": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "summary": {
            "sessions_scanned": scanned_sessions,
            "sessions_with_audit_turns": sessions_with_audit,
            "audit_turns_in_window": audit_turns,
            "actionable_turns_in_window": actionable_turns,
            "actionable_turns_complete": complete_actionable_turns,
            "actionable_turns_incomplete": incomplete_actionable_turns,
            "audit_completeness_rate": completeness_rate,
            "audit_completeness_ok": incomplete_actionable_turns == 0,
        },
        "fallback_summary": {
            "fallback_any_true": fallback_any_true,
            "fallback_plan_true": fallback_plan_true,
            "fallback_spec_true": fallback_spec_true,
        },
        "security_outcome_counts": dict(sorted(security_counter.items())),
        "missing_required_field_counts": dict(sorted(missing_counter.items())),
        "recent_incomplete_actionable_turns": recent_incomplete,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 4 operational report from canonical turn audit envelopes.")
    ap.add_argument("--site", default=SITE)
    ap.add_argument("--session-limit", type=int, default=50)
    ap.add_argument("--since-hours", type=int, default=24)
    ap.add_argument("--owner", default="")
    ap.add_argument("--out-json", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    sessions = _fetch_recent_audit_sessions(
        site=str(args.site),
        session_limit=max(1, int(args.session_limit)),
        owner=str(args.owner or "").strip(),
    )
    report = build_phase4_audit_ops_report(
        session_rows=sessions,
        since_hours=max(0, int(args.since_hours)),
    )

    out_path = Path(str(args.out_json))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"{ts}_phase4_audit_ops_report.json"
    log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OUT_JSON={out_path}")
    print(f"OUT_LOG={log_path}")
    print(json.dumps(report.get("summary") or {}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
