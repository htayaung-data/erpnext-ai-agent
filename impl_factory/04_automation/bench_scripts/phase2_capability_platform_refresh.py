#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SITE = "erpai_prj1"
DEFAULT_USER = "Administrator"
LOG_DIR = Path("impl_factory/04_automation/logs")
STATE_DIR = Path("impl_factory/04_automation/capability_v7")


def _run(cmd: List[str], timeout_sec: int = 180) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode("utf-8", errors="ignore") if e.stdout else "")
        stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode("utf-8", errors="ignore") if e.stderr else "")
        stderr = (stderr + f"\nTIMEOUT after {int(timeout_sec)}s").strip()
        return subprocess.CompletedProcess(e.cmd, 124, stdout=stdout, stderr=stderr)


def _parse_last_json(stdout: str) -> Dict[str, Any]:
    lines = [ln.strip() for ln in (stdout or "").splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("{") and ln.endswith("}"):
            try:
                obj = json.loads(ln)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
    return {}


def bench_execute(site: str, method: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    kwargs_py = repr(kwargs)
    inner = (
        "cd /home/frappe/frappe-bench && "
        f"bench --site {site} execute {method} --kwargs {shlex.quote(kwargs_py)}"
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


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _extract_index(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("index"), dict):
        return dict(payload.get("index") or {})
    if isinstance(payload.get("reports"), list):
        return dict(payload)
    return {}


def _simple_drift(prev_payload: Dict[str, Any], curr_payload: Dict[str, Any]) -> Dict[str, Any]:
    prev = _extract_index(prev_payload)
    curr = _extract_index(curr_payload)
    prev_rows = [r for r in list(prev.get("reports") or []) if isinstance(r, dict)]
    curr_rows = [r for r in list(curr.get("reports") or []) if isinstance(r, dict)]

    def _name(row: Dict[str, Any]) -> str:
        return str(row.get("report_name") or row.get("name") or "").strip()

    def _fp(row: Dict[str, Any]) -> str:
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        return str(meta.get("fingerprint") or "").strip()

    prev_by = {_name(r): r for r in prev_rows if _name(r)}
    curr_by = {_name(r): r for r in curr_rows if _name(r)}
    prev_names = set(prev_by.keys())
    curr_names = set(curr_by.keys())

    added = sorted(list(curr_names - prev_names))
    removed = sorted(list(prev_names - curr_names))
    changed: List[str] = []
    for name in sorted(prev_names & curr_names):
        if _fp(prev_by[name]) != _fp(curr_by[name]):
            changed.append(name)

    return {
        "previous_report_count": len(prev_rows),
        "current_report_count": len(curr_rows),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "added_sample": added[:80],
        "removed_sample": removed[:80],
        "changed_sample": changed[:80],
    }


def _write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    drift = payload.get("drift") if isinstance(payload.get("drift"), dict) else {}
    alerts = [a for a in list(payload.get("alerts") or []) if isinstance(a, dict)]
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    lines = [
        "# Phase 2 Capability Platform Report",
        "",
        f"- Executed: {payload.get('executed_at_utc')}",
        f"- Schema version: {index.get('schema_version')}",
        f"- Capability index version: {index.get('capability_index_version')}",
        f"- Report count: {index.get('report_count')}",
        f"- Known requirements count: {index.get('known_requirements_count')}",
        f"- High confidence count: {index.get('high_confidence_count')}",
        "",
        "## Coverage",
        f"- Active report families: {coverage.get('active_report_family_count')}",
        f"- Covered report families: {coverage.get('covered_report_family_count')}",
        f"- Family coverage rate: {coverage.get('family_coverage_rate')}",
        f"- Family gate pass (>=0.95): {coverage.get('family_gate_pass_95')}",
        f"- Report coverage rate: {coverage.get('report_coverage_rate')}",
        "",
        "## Drift",
        f"- Added count: {drift.get('added_count')}",
        f"- Removed count: {drift.get('removed_count')}",
        f"- Changed count: {drift.get('changed_count')}",
        "",
        "## Alerts",
    ]
    if not alerts:
        lines.append("- none")
    else:
        for a in alerts:
            lines.append(f"- [{a.get('severity')}] {a.get('code')}: {a.get('message')}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2 capability platform refresh and report.")
    parser.add_argument("--site", default=SITE)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--max-reports", type=int, default=260)
    parser.add_argument("--freshness-hours", type=int, default=24)
    parser.add_argument("--min-confidence", type=float, default=0.60)
    parser.add_argument("--previous", default="", help="optional previous capability payload json")
    args = parser.parse_args()

    site = str(args.site or SITE)

    previous_payload = _load_json(Path(args.previous)) if str(args.previous or "").strip() else _load_json(STATE_DIR / "latest_capability_platform.json")
    previous_snapshot = previous_payload if isinstance(previous_payload, dict) else {}

    result = bench_execute(
        site,
        "ai_assistant_ui.ai_core.v7.capability_platform.run_capability_ingestion_job",
        {
            "user": str(args.user or DEFAULT_USER),
            "include_disabled": False,
            "max_reports": int(max(1, args.max_reports)),
            "freshness_hours": int(max(1, args.freshness_hours)),
            "min_confidence": float(max(0.0, min(args.min_confidence, 1.0))),
            "include_rows": True,
        },
    )
    if not result.get("ok"):
        print(result.get("stderr") or result.get("stdout") or "capability ingestion failed")
        return 1

    payload = result.get("data") if isinstance(result.get("data"), dict) else {}
    if not payload:
        print("capability ingestion returned empty payload")
        return 1

    if previous_snapshot:
        payload["drift"] = _simple_drift(previous_snapshot, payload)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    out_json = LOG_DIR / f"{ts}_phase2_capability_platform.json"
    out_md = LOG_DIR / f"{ts}_phase2_capability_platform.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    _write_markdown(out_md, payload)

    latest_json = STATE_DIR / "latest_capability_platform.json"
    latest_md = STATE_DIR / "latest_capability_platform.md"
    latest_json.write_text(out_json.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(out_md.read_text(encoding="utf-8"), encoding="utf-8")

    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    summary = {
        "out_json": str(out_json),
        "out_md": str(out_md),
        "report_count": (payload.get("index") or {}).get("report_count"),
        "family_coverage_rate": coverage.get("family_coverage_rate"),
        "family_gate_pass_95": coverage.get("family_gate_pass_95"),
    }
    print(f"OUT_JSON={out_json}")
    print(f"OUT_MD={out_md}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
