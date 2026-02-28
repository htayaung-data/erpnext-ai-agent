from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from phase8_release_gate import _load_artifact, compute_gate, select_first_run_results


def _default_manifest_path() -> str:
    expanded = Path("impl_factory/04_automation/replay_v7_expanded/manifest.json").resolve()
    if expanded.exists():
        return str(expanded)
    return str(Path("impl_factory/04_automation/replay_v7/manifest.json").resolve())


def _markdown(payload: Dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    kpi = payload.get("kpi") if isinstance(payload.get("kpi"), dict) else {}
    first_run = payload.get("first_run_policy") if isinstance(payload.get("first_run_policy"), dict) else {}
    behavior = payload.get("behavior_class") if isinstance(payload.get("behavior_class"), dict) else {}
    class_rates = behavior.get("first_run_pass_rate_by_class") if isinstance(behavior.get("first_run_pass_rate_by_class"), dict) else {}

    lines = [
        "# Phase 1 First-Run Baseline Score",
        "",
        f"- Executed: {payload.get('executed_at_utc')}",
        f"- Label: {payload.get('label') or '-'}",
        f"- Input artifacts: {len(list(payload.get('input_artifacts') or []))}",
        "",
        "## First-Run Policy",
        f"- Enforced: {first_run.get('enforced')}",
        f"- Source: {first_run.get('source')}",
        f"- Selected cases: {first_run.get('selected_case_count')}",
        f"- Ignored duplicate results: {first_run.get('diagnostic_ignored_count')}",
        "",
        "## KPI Summary",
        f"- Total cases scored: {summary.get('total')}",
        f"- Pass count: {summary.get('passed')}",
        f"- Fail count: {summary.get('failed')}",
        f"- First-run pass rate: {kpi.get('first_run_pass_rate')}",
        f"- Direct-answer rate (clear): {summary.get('direct_answer_rate_clear_read')}",
        f"- Clarification rate (clear): {summary.get('clarification_rate_clear_read')}",
        f"- Unnecessary clarification rate (clear): {summary.get('unnecessary_clarification_rate_clear_read')}",
        f"- Wrong-report rate (clear): {summary.get('wrong_report_rate_clear_read')}",
        f"- Clarification loop rate: {summary.get('clarification_loop_rate')}",
        f"- Output-shape pass rate (clear): {summary.get('output_shape_pass_rate_clear_read')}",
        f"- User correction rate: {summary.get('user_correction_rate')}",
        f"- Write safety incidents: {summary.get('write_safety_incidents')}",
        f"- Latency p95 ms (clear): {summary.get('latency_p95_ms_clear_read')}",
        "",
        "## Behavior Class Coverage",
        f"- Cases with behavior class labels: {behavior.get('labeled_case_count')}",
        f"- Distinct behavior classes observed: {behavior.get('observed_class_count')}",
        f"- Target mandatory classes: {behavior.get('target_mandatory_count')}",
        f"- Target class coverage: {behavior.get('target_coverage_rate')}",
        f"- Missing target classes: {', '.join(list(behavior.get('missing_target_classes') or [])) or '-'}",
        "",
        "## Manifest",
        f"- Path: {payload.get('replay_manifest_path') or '-'}",
        f"- Total expected cases: {payload.get('replay_manifest_total_cases')}",
        "",
        "## First-Run Pass Rate by Behavior Class",
    ]
    for cls in sorted(class_rates.keys()):
        lines.append(f"- {cls}: {class_rates.get(cls)}")
    lines.extend([
        "",
        "## Input Artifacts",
    ])
    for p in list(payload.get("input_artifacts") or []):
        lines.append(f"- `{p}`")
    lines.append("")
    return "\n".join(lines)


def _safe_rate(num: int, den: int) -> float:
    return (float(num) / float(den)) if den else 0.0


def _to_lc_set(values: object) -> Set[str]:
    out: Set[str] = set()
    for v in list(values or []):
        s = str(v or "").strip().lower()
        if s:
            out.add(s)
    return out


def _load_manifest_case_ids(manifest_path: Path) -> Dict[str, Any]:
    if not manifest_path.exists():
        return {
            "version": "",
            "total_case_count": 0,
            "case_ids": set(),
            "packs": [],
            "case_meta": {},
            "behavior_class_schema": {},
            "target_behavior_classes": set(),
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "version": "",
            "total_case_count": 0,
            "case_ids": set(),
            "packs": [],
            "case_meta": {},
            "behavior_class_schema": {},
            "target_behavior_classes": set(),
        }

    packs = [p for p in list(manifest.get("packs") or []) if isinstance(p, dict)]
    case_ids: Set[str] = set()
    case_meta: Dict[str, Dict[str, str]] = {}
    behavior_schema = manifest.get("behavior_class_schema") if isinstance(manifest.get("behavior_class_schema"), dict) else {}
    behavior_field = str(behavior_schema.get("field") or "behavior_class").strip() or "behavior_class"
    target_behavior_classes = _to_lc_set(behavior_schema.get("target_mandatory_classes"))
    for p in packs:
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
            try:
                row = json.loads(s)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue
            cid = str(row.get("case_id") or "").strip()
            if cid:
                case_ids.add(cid)
                case_meta[cid] = {
                    "suite": str(row.get("suite") or "").strip(),
                    "behavior_class": str(row.get(behavior_field) or "").strip().lower(),
                }

    return {
        "version": str(manifest.get("version") or ""),
        "total_case_count": int(manifest.get("total_case_count") or 0),
        "case_ids": case_ids,
        "packs": packs,
        "case_meta": case_meta,
        "behavior_class_schema": behavior_schema,
        "target_behavior_classes": target_behavior_classes,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 1 first-run baseline scorer.")
    ap.add_argument("--raw", dest="raw_paths", action="append", required=True, help="Raw replay artifact JSON path (repeatable).")
    ap.add_argument("--manifest", dest="manifest_path", default=_default_manifest_path(), help="Replay pack manifest path.")
    ap.add_argument("--label", dest="label", default="", help="Optional label.")
    ap.add_argument("--output-dir", dest="output_dir", default="impl_factory/04_automation/logs", help="Output folder.")
    args = ap.parse_args()

    raw_paths = [Path(p) for p in list(args.raw_paths or [])]
    artifacts = [_load_artifact(p) for p in raw_paths]
    selected_results, first_run_stats = select_first_run_results(artifacts)

    manifest_path = Path(str(args.manifest_path or "")).resolve()
    manifest_info = _load_manifest_case_ids(manifest_path)
    expected_ids = set(manifest_info.get("case_ids") or set())
    case_meta = manifest_info.get("case_meta") if isinstance(manifest_info.get("case_meta"), dict) else {}
    target_behavior_classes = set(manifest_info.get("target_behavior_classes") or set())

    selected_by_id: Dict[str, Dict[str, Any]] = {}
    for r in selected_results:
        rid = str(r.get("id") or "").strip()
        if rid:
            selected_by_id[rid] = r

    observed_ids = set(selected_by_id.keys())
    if expected_ids:
        scoring_ids = sorted(list(expected_ids))
        filtered_results = [selected_by_id[cid] for cid in scoring_ids if cid in selected_by_id]
    else:
        scoring_ids = sorted(list(observed_ids))
        filtered_results = list(selected_results)

    gate = compute_gate(
        selected_results=filtered_results,
        artifacts=artifacts,
        baseline_correction_rate=None,
        latency_p95_sla_ms=None,
    )
    summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}

    total_expected = len(scoring_ids)
    pass_expected = 0
    fail_expected = 0
    missing_ids = sorted(list(set(scoring_ids) - observed_ids))
    unexpected_ids = sorted(list(observed_ids - set(scoring_ids))) if scoring_ids else []
    failed_ids = []
    for cid in scoring_ids:
        row = selected_by_id.get(cid)
        if row is None:
            fail_expected += 1
            failed_ids.append(cid)
            continue
        if bool(row.get("pass")):
            pass_expected += 1
        else:
            fail_expected += 1
            failed_ids.append(cid)

    # Behavior-class baseline metrics are computed against manifest-scoped case IDs.
    class_totals: Dict[str, int] = {}
    class_passed: Dict[str, int] = {}
    unlabeled_case_ids: List[str] = []
    for cid in scoring_ids:
        meta = case_meta.get(cid) if isinstance(case_meta.get(cid), dict) else {}
        behavior_class = str(meta.get("behavior_class") or "").strip().lower()
        if not behavior_class:
            unlabeled_case_ids.append(cid)
            continue
        class_totals[behavior_class] = int(class_totals.get(behavior_class) or 0) + 1
        row = selected_by_id.get(cid)
        if row is not None and bool(row.get("pass")):
            class_passed[behavior_class] = int(class_passed.get(behavior_class) or 0) + 1

    class_pass_rate: Dict[str, float] = {}
    class_failed: Dict[str, int] = {}
    for cls, total in class_totals.items():
        passed = int(class_passed.get(cls) or 0)
        failed = int(total - passed)
        class_failed[cls] = failed
        class_pass_rate[cls] = round(_safe_rate(passed, total), 4)

    observed_classes = set(class_totals.keys())
    covered_target_classes = observed_classes & target_behavior_classes
    missing_target_classes = sorted(list(target_behavior_classes - covered_target_classes))
    target_coverage_rate = round(_safe_rate(len(covered_target_classes), len(target_behavior_classes)), 4) if target_behavior_classes else 1.0

    payload: Dict[str, Any] = {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "phase1_first_run_baseline",
        "label": str(args.label or "").strip(),
        "input_artifacts": [str(p) for p in raw_paths],
        "first_run_policy": {
            "enforced": True,
            "source": "earliest_result_per_case_id",
            **first_run_stats,
        },
        "summary": {
            **summary,
            "manifest_expected_total": total_expected,
            "manifest_expected_passed": pass_expected,
            "manifest_expected_failed": fail_expected,
            "manifest_missing_case_ids": missing_ids,
            "manifest_unexpected_case_ids": unexpected_ids,
            "manifest_failed_case_ids": failed_ids,
            "manifest_coverage_rate": round(_safe_rate(total_expected - len(missing_ids), total_expected), 4),
        },
        "kpi": {
            "first_run_pass_rate": round(_safe_rate(pass_expected, total_expected), 4),
            "total_cases": total_expected,
            "passed_cases": pass_expected,
            "failed_cases": fail_expected,
        },
        "behavior_class": {
            "field": str((manifest_info.get("behavior_class_schema") or {}).get("field") or "behavior_class"),
            "labeled_case_count": int(sum(class_totals.values())),
            "unlabeled_case_ids": unlabeled_case_ids,
            "observed_class_count": len(observed_classes),
            "target_mandatory_count": len(target_behavior_classes),
            "target_coverage_rate": target_coverage_rate,
            "missing_target_classes": missing_target_classes,
            "first_run_pass_rate_by_class": class_pass_rate,
            "class_totals": class_totals,
            "class_passed": class_passed,
            "class_failed": class_failed,
        },
        "replay_manifest_path": str(manifest_path) if manifest_path.exists() else "",
        "replay_manifest_version": str(manifest_info.get("version") or ""),
        "replay_manifest_total_cases": int(manifest_info.get("total_case_count") or 0),
    }

    out_dir = Path(str(args.output_dir or "impl_factory/04_automation/logs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"{ts}_phase1_first_run_baseline.json"
    md_path = out_dir / f"{ts}_phase1_first_run_baseline.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown(payload), encoding="utf-8")

    print(f"OUT_JSON={json_path}")
    print(f"OUT_MD={md_path}")
    print(json.dumps(payload.get("kpi") or {}, ensure_ascii=False))


if __name__ == "__main__":
    main()
