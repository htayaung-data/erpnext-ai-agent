from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_IDS = {
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
CRITICAL_IDS = {"FIN-01", "FIN-03", "FIN-04", "SAL-01", "CFG-03", "COR-01"}
CLEAR_READ_IDS = {
    "FIN-01", "FIN-02", "FIN-03", "FIN-04",
    "SAL-01", "SAL-02",
    "STK-01", "STK-02",
    "HR-01", "OPS-01",
    "COR-01", "DET-01", "DOC-01",
    "CFG-03", "EXP-01",
}
LOOP_SCOPE_IDS = CLEAR_READ_IDS | {"CFG-01", "CFG-02", "ENT-01", "ENT-02"}
WRITE_IDS = {"WR-01", "WR-02", "WR-03", "WR-04"}
ROLE_DEFAULTS = {
    "HR-01": "ai.operator",
    "OPS-01": "ai.operator",
    "DOC-01": "ai.operator",
    "WR-01": "ai.operator",
    "WR-02": "ai.operator",
    "WR-03": "ai.operator",
    "WR-04": "ai.operator",
}


@dataclass
class Artifact:
    path: Path
    executed_at_utc: str
    ts: datetime
    data: Dict[str, Any]


def _parse_ts(ts_raw: Any) -> datetime:
    s = str(ts_raw or "").strip()
    if not s:
        return datetime.min
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.min


def _safe_rate(num: int, den: int) -> float:
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


def _load_artifact(path: Path) -> Artifact:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Artifact(
        path=path,
        executed_at_utc=str(raw.get("executed_at_utc") or ""),
        ts=_parse_ts(raw.get("executed_at_utc")),
        data=raw if isinstance(raw, dict) else {},
    )


def _result_role(result: Dict[str, Any]) -> str:
    role = str(result.get("role") or "").strip()
    if role and role != "Administrator":
        return role
    rid = str(result.get("id") or "").strip()
    return ROLE_DEFAULTS.get(rid, "ai.reader")


def select_first_run_results(artifacts: List[Artifact]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Contract policy: first-run-only scoring.
    If multiple artifacts contain the same scenario ID, keep earliest one only.
    """
    ordered = sorted(artifacts, key=lambda a: (a.ts, str(a.path)))
    selected_by_id: Dict[str, Dict[str, Any]] = {}
    ignored = 0
    for art in ordered:
        for result in list(art.data.get("results") or []):
            if not isinstance(result, dict):
                continue
            rid = str(result.get("id") or "").strip()
            if not rid:
                continue
            if rid in selected_by_id:
                ignored += 1
                continue
            row = dict(result)
            row["_artifact_path"] = str(art.path)
            row["_artifact_executed_at_utc"] = art.executed_at_utc
            row["role"] = _result_role(row)
            selected_by_id[rid] = row
    selected = [selected_by_id[k] for k in sorted(selected_by_id.keys())]
    return selected, {"diagnostic_ignored_count": ignored, "selected_case_count": len(selected)}


def _fac_preconditions_ok(artifacts: List[Artifact]) -> bool:
    if not artifacts:
        return False
    ok = True
    for art in artifacts:
        pre = art.data.get("preconditions") if isinstance(art.data.get("preconditions"), dict) else {}
        # Handle older artifact variants gracefully.
        if pre:
            fac_ok = bool(pre.get("report_list_ok")) and bool(pre.get("report_requirements_ok")) and bool(pre.get("generate_report_ok"))
            ok = ok and fac_ok
    return ok


def _first_run_policy_declared(artifacts: List[Artifact]) -> bool:
    if not artifacts:
        return False
    ok = True
    for art in artifacts:
        rp = art.data.get("run_policy") if isinstance(art.data.get("run_policy"), dict) else {}
        gate_source = str(rp.get("gate_source") or "").strip().lower()
        # Legacy artifacts may omit run_policy; do not fail declaration check for those.
        if gate_source and gate_source != "first_run_only":
            ok = False
    return ok


def _assertion(row: Dict[str, Any], key: str) -> Optional[bool]:
    sem = row.get("semantic") if isinstance(row.get("semantic"), dict) else {}
    assertions = sem.get("assertions") if isinstance(sem.get("assertions"), dict) else {}
    val = assertions.get(key)
    if isinstance(val, bool):
        return val
    return None


def _actual(row: Dict[str, Any], key: str, default: Any = None) -> Any:
    act = row.get("actual") if isinstance(row.get("actual"), dict) else {}
    return act.get(key, default)


def compute_gate(
    *,
    selected_results: List[Dict[str, Any]],
    artifacts: List[Artifact],
    baseline_correction_rate: Optional[float] = None,
    latency_p95_sla_ms: Optional[int] = None,
) -> Dict[str, Any]:
    ids = {str(r.get("id") or "").strip() for r in selected_results}
    missing_mandatory = sorted(list(MANDATORY_IDS - ids))
    missing_critical = sorted(list(CRITICAL_IDS - ids))

    mandatory_pass = (len(missing_mandatory) == 0) and all(bool(r.get("pass")) for r in selected_results if str(r.get("id") or "") in MANDATORY_IDS)
    critical_rows = [r for r in selected_results if str(r.get("id") or "") in CRITICAL_IDS]
    critical_pass = (len(missing_critical) == 0) and all(bool(r.get("pass")) for r in critical_rows)

    clear_rows = [r for r in selected_results if str(r.get("id") or "") in CLEAR_READ_IDS]
    clear_total = len(clear_rows)
    loop_rows = [r for r in selected_results if str(r.get("id") or "") in LOOP_SCOPE_IDS]
    loop_total = len(loop_rows)
    write_rows = [r for r in selected_results if str(r.get("id") or "") in WRITE_IDS]

    direct_answer_count = 0
    clarification_count = 0
    unnecessary_clarification_count = 0
    wrong_report_count = 0
    meta_clarification_count = 0
    output_shape_pass_count = 0
    durations: List[int] = []

    for r in clear_rows:
        assistant_type = str(_actual(r, "assistant_type", "") or "").strip().lower()
        pending_mode = _actual(r, "pending_mode")
        clarification = bool(_actual(r, "clarification", False))
        sem = r.get("semantic") if isinstance(r.get("semantic"), dict) else {}
        blocker = bool(sem.get("blocker_clarification"))
        if (not clarification) and assistant_type in ("report_table", "text") and pending_mode is None:
            direct_answer_count += 1
        if clarification:
            clarification_count += 1
        if clarification and (not blocker):
            unnecessary_clarification_count += 1
        if _assertion(r, "report_alignment_pass") is False:
            wrong_report_count += 1
        if bool(_actual(r, "meta_clarification", False)) or bool(sem.get("meta_clarification")):
            meta_clarification_count += 1
        if _assertion(r, "output_shape_pass") is True:
            output_shape_pass_count += 1
        d = _actual(r, "duration_ms")
        try:
            if d is not None:
                durations.append(int(d))
        except Exception:
            pass

    loop_fail_count = 0
    for r in loop_rows:
        if _assertion(r, "loop_policy_pass") is False:
            loop_fail_count += 1

    correction_rows = [r for r in selected_results if str(r.get("id") or "") == "COR-01"]
    correction_total = len(correction_rows)
    correction_fail_count = sum(1 for r in correction_rows if not bool(r.get("pass")))

    write_safety_incidents = sum(1 for r in write_rows if not bool(r.get("pass")))

    reader_rows = [r for r in selected_results if str(r.get("role") or "") == "ai.reader"]
    operator_rows = [r for r in selected_results if str(r.get("role") or "") == "ai.operator"]
    reader_pass_rate = _safe_rate(sum(1 for r in reader_rows if bool(r.get("pass"))), len(reader_rows))
    operator_pass_rate = _safe_rate(sum(1 for r in operator_rows if bool(r.get("pass"))), len(operator_rows))
    role_parity = bool(reader_rows and operator_rows and abs(reader_pass_rate - operator_pass_rate) <= 0.05)

    direct_answer_rate = _safe_rate(direct_answer_count, clear_total)
    clarification_rate = _safe_rate(clarification_count, clear_total)
    unnecessary_clarification_rate = _safe_rate(unnecessary_clarification_count, clear_total)
    wrong_report_rate = _safe_rate(wrong_report_count, clear_total)
    loop_rate = _safe_rate(loop_fail_count, loop_total)
    user_correction_rate = _safe_rate(correction_fail_count, correction_total)
    output_shape_pass_rate = _safe_rate(output_shape_pass_count, clear_total)
    latency_p95 = _percentile(durations, 95.0)
    fac_ok = _fac_preconditions_ok(artifacts)
    first_run_declared = _first_run_policy_declared(artifacts)

    correction_trend_ok: Optional[bool] = None
    if baseline_correction_rate is not None:
        correction_trend_ok = user_correction_rate <= (float(baseline_correction_rate) * 0.8)

    latency_sla_ok: Optional[bool] = None
    if latency_p95_sla_ms is not None:
        latency_sla_ok = (latency_p95 is not None) and (int(latency_p95) <= int(latency_p95_sla_ms))

    gate_checks: Dict[str, bool] = {
        "mandatory_pass_rate_100": mandatory_pass,
        "critical_clear_query_pass_100": critical_pass,
        "first_run_policy_declared": first_run_declared,
        "fac_preconditions_ok": fac_ok,
        "direct_answer_rate_clear_read_ge_90pct": direct_answer_rate >= 0.90,
        "clarification_rate_clear_read_le_10pct": clarification_rate <= 0.10,
        "unnecessary_clarification_rate_clear_read_le_5pct": unnecessary_clarification_rate <= 0.05,
        "wrong_report_rate_clear_read_le_3pct": wrong_report_rate <= 0.03,
        "clarification_loop_rate_lt_1pct": loop_rate < 0.01,
        "zero_meta_clarification_on_clear_asks": meta_clarification_count == 0,
        "role_parity_reader_vs_operator": role_parity,
        "write_safety_incidents_eq_0": write_safety_incidents == 0,
        "output_shape_pass_rate_eq_100pct": output_shape_pass_rate >= 1.0,
    }

    # Optional gates become required only when configured.
    if correction_trend_ok is not None:
        gate_checks["user_correction_rate_trending_down_20pct"] = bool(correction_trend_ok)
    if latency_sla_ok is not None:
        gate_checks["latency_p95_within_sla"] = bool(latency_sla_ok)

    overall_go = all(gate_checks.values())
    failed_checks = sorted([k for k, v in gate_checks.items() if not bool(v)])

    return {
        "summary": {
            "total": len(selected_results),
            "passed": sum(1 for r in selected_results if bool(r.get("pass"))),
            "failed": sum(1 for r in selected_results if not bool(r.get("pass"))),
            "missing_mandatory_ids": missing_mandatory,
            "missing_critical_ids": missing_critical,
            "clear_read_total": clear_total,
            "direct_answer_count_clear_read": direct_answer_count,
            "direct_answer_rate_clear_read": round(direct_answer_rate, 4),
            "clarification_count_clear_read": clarification_count,
            "clarification_rate_clear_read": round(clarification_rate, 4),
            "unnecessary_clarification_count_clear_read": unnecessary_clarification_count,
            "unnecessary_clarification_rate_clear_read": round(unnecessary_clarification_rate, 4),
            "wrong_report_count_clear_read": wrong_report_count,
            "wrong_report_rate_clear_read": round(wrong_report_rate, 4),
            "loop_fail_count": loop_fail_count,
            "loop_scope_total": loop_total,
            "clarification_loop_rate": round(loop_rate, 4),
            "meta_clarification_count_clear_read": meta_clarification_count,
            "output_shape_pass_rate_clear_read": round(output_shape_pass_rate, 4),
            "write_safety_incidents": write_safety_incidents,
            "user_correction_total": correction_total,
            "user_correction_fail_count": correction_fail_count,
            "user_correction_rate": round(user_correction_rate, 4),
            "latency_p95_ms_clear_read": latency_p95,
            "reader_total": len(reader_rows),
            "reader_pass_rate": round(reader_pass_rate, 4),
            "operator_total": len(operator_rows),
            "operator_pass_rate": round(operator_pass_rate, 4),
        },
        "release_gate": {
            **gate_checks,
            "overall_go": bool(overall_go),
            "failed_gate_checks": failed_checks,
        },
        "baseline": {
            "baseline_correction_rate": baseline_correction_rate,
            "correction_trend_gate_applied": baseline_correction_rate is not None,
        },
        "sla": {
            "latency_p95_sla_ms": latency_p95_sla_ms,
            "latency_gate_applied": latency_p95_sla_ms is not None,
        },
    }


def stage_decision(*, stage_percent: int, gate: Dict[str, Any]) -> Dict[str, Any]:
    go = bool((gate.get("release_gate") or {}).get("overall_go"))
    failed = list((gate.get("release_gate") or {}).get("failed_gate_checks") or [])
    next_stage_map = {10: 25, 25: 50, 50: 100, 100: 100}
    stage = int(stage_percent)
    if go:
        nxt = next_stage_map.get(stage, stage)
        if stage >= 100:
            action = "hold_100pct_monitor"
            note = "100% stage passed. Keep monitoring with rollback readiness."
        else:
            action = f"promote_to_{nxt}pct"
            note = f"Current stage passed. Promote canary from {stage}% to {nxt}%."
        return {
            "stage_percent": stage,
            "go": True,
            "action": action,
            "next_stage_percent": nxt,
            "rollback_triggered": False,
            "rollback_target": "",
            "reason": note,
        }
    return {
        "stage_percent": stage,
        "go": False,
        "action": "rollback_to_v2",
        "next_stage_percent": stage,
        "rollback_triggered": True,
        "rollback_target": "assistant_engine=v2",
        "reason": "Gate failed at current stage.",
        "failed_gate_checks": failed,
    }


def build_release_evaluation(
    *,
    raw_paths: List[Path],
    stage_percent: int,
    baseline_correction_rate: Optional[float] = None,
    latency_p95_sla_ms: Optional[int] = None,
    label: str = "",
) -> Dict[str, Any]:
    artifacts = [_load_artifact(p) for p in raw_paths]
    selected, first_run_stats = select_first_run_results(artifacts)
    gate = compute_gate(
        selected_results=selected,
        artifacts=artifacts,
        baseline_correction_rate=baseline_correction_rate,
        latency_p95_sla_ms=latency_p95_sla_ms,
    )
    decision = stage_decision(stage_percent=stage_percent, gate=gate)
    return {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "phase8_release_gate",
        "label": str(label or "").strip(),
        "input_artifacts": [str(p) for p in raw_paths],
        "first_run_policy": {
            "enforced": True,
            "source": "earliest_result_per_case_id",
            **first_run_stats,
        },
        "stage": decision,
        **gate,
    }


def _markdown_report(payload: Dict[str, Any]) -> str:
    stage = payload.get("stage") if isinstance(payload.get("stage"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    gate = payload.get("release_gate") if isinstance(payload.get("release_gate"), dict) else {}
    lines = [
        "# Phase 8 Release Gate Decision",
        "",
        f"- Executed: {payload.get('executed_at_utc')}",
        f"- Label: {payload.get('label') or '-'}",
        f"- Stage: {stage.get('stage_percent')}%",
        f"- GO: {stage.get('go')}",
        f"- Action: {stage.get('action')}",
        f"- Rollback Triggered: {stage.get('rollback_triggered')}",
        "",
        "## Summary",
        f"- Total: {summary.get('total')}",
        f"- Passed: {summary.get('passed')}",
        f"- Failed: {summary.get('failed')}",
        f"- Direct-answer rate (clear): {summary.get('direct_answer_rate_clear_read')}",
        f"- Clarification rate (clear): {summary.get('clarification_rate_clear_read')}",
        f"- Unnecessary clarification rate (clear): {summary.get('unnecessary_clarification_rate_clear_read')}",
        f"- Wrong-report rate (clear): {summary.get('wrong_report_rate_clear_read')}",
        f"- Loop rate: {summary.get('clarification_loop_rate')}",
        f"- Output-shape pass rate (clear): {summary.get('output_shape_pass_rate_clear_read')}",
        f"- Write safety incidents: {summary.get('write_safety_incidents')}",
        f"- Role parity reader/operator: {gate.get('role_parity_reader_vs_operator')}",
        "",
        "## Gate Checks",
    ]
    for key in sorted([k for k in gate.keys() if k not in ("overall_go", "failed_gate_checks")]):
        lines.append(f"- {key}: {gate.get(key)}")
    lines.extend(
        [
            f"- overall_go: {gate.get('overall_go')}",
            f"- failed_gate_checks: {gate.get('failed_gate_checks') or []}",
            "",
            "## Inputs",
        ]
    )
    for p in list(payload.get("input_artifacts") or []):
        lines.append(f"- `{p}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 8 staged release gate evaluator (first-run-only).")
    ap.add_argument("--raw", dest="raw_paths", action="append", required=True, help="Raw canary artifact JSON path (repeatable).")
    ap.add_argument("--stage", dest="stage_percent", type=int, required=True, choices=[10, 25, 50, 100], help="Current canary stage percentage.")
    ap.add_argument("--baseline-correction-rate", dest="baseline_correction_rate", type=float, default=None, help="Baseline user correction rate for trend gate.")
    ap.add_argument("--latency-p95-sla-ms", dest="latency_p95_sla_ms", type=int, default=None, help="Latency p95 SLA in ms.")
    ap.add_argument("--label", dest="label", default="", help="Optional release label.")
    ap.add_argument("--output-dir", dest="output_dir", default="impl_factory/04_automation/logs", help="Output folder.")
    args = ap.parse_args()

    raw_paths = [Path(p) for p in (args.raw_paths or [])]
    payload = build_release_evaluation(
        raw_paths=raw_paths,
        stage_percent=int(args.stage_percent),
        baseline_correction_rate=args.baseline_correction_rate,
        latency_p95_sla_ms=args.latency_p95_sla_ms,
        label=str(args.label or ""),
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    tag = f"stage{int(args.stage_percent)}"
    json_path = out_dir / f"{ts}_phase8_release_gate_{tag}.json"
    md_path = out_dir / f"{ts}_phase8_release_gate_{tag}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown_report(payload), encoding="utf-8")

    print(f"OUT_JSON={json_path}")
    print(f"OUT_MD={md_path}")
    print(json.dumps(payload.get("stage") or {}, ensure_ascii=False))
    print(json.dumps(payload.get("release_gate") or {}, ensure_ascii=False))


if __name__ == "__main__":
    main()
