from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from phase8_release_gate import _load_artifact, compute_gate, select_first_run_results


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _resolve_wrong_report_rate(path: Path) -> Optional[float]:
    raw = _load_json(path)
    summary = raw.get("summary") if isinstance(raw.get("summary"), dict) else {}
    rate = _safe_float(summary.get("wrong_report_rate_clear_read"))
    if rate is not None:
        return rate
    try:
        artifact = _load_artifact(path)
        selected, _ = select_first_run_results([artifact])
        gate = compute_gate(selected_results=selected, artifacts=[artifact])
        gsum = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
        return _safe_float(gsum.get("wrong_report_rate_clear_read"))
    except Exception:
        return None


def _evaluate_confusion_suite() -> Dict[str, Any]:
    import sys

    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))

    from ai_assistant_ui.ai_core.v7.constraint_engine import build_constraint_set
    from ai_assistant_ui.ai_core.v7.semantic_resolver import resolve_semantics

    capability_index = {
        "reports": [
            {
                "report_name": "Accounts Payable Summary",
                "constraints": {
                    "supported_filter_kinds": ["company", "date"],
                    "required_filter_kinds": [],
                    "requirements_unknown": False,
                },
                "semantics": {
                    "domain_hints": ["finance", "payable"],
                    "dimension_hints": ["supplier"],
                    "metric_hints": ["outstanding_amount"],
                    "primary_dimension": "supplier",
                },
                "metadata": {"confidence": 0.97, "fresh": True},
                "time_support": {"as_of": True, "range": True, "any": True},
            },
            {
                "report_name": "Accounts Receivable Summary",
                "constraints": {
                    "supported_filter_kinds": ["company", "date"],
                    "required_filter_kinds": [],
                    "requirements_unknown": False,
                },
                "semantics": {
                    "domain_hints": ["finance", "receivable"],
                    "dimension_hints": ["customer"],
                    "metric_hints": ["outstanding_amount"],
                    "primary_dimension": "customer",
                },
                "metadata": {"confidence": 0.97, "fresh": True},
                "time_support": {"as_of": True, "range": True, "any": True},
            },
            {
                "report_name": "Item-wise Sales Register",
                "constraints": {
                    "supported_filter_kinds": ["company", "date", "item"],
                    "required_filter_kinds": [],
                    "requirements_unknown": False,
                },
                "semantics": {
                    "domain_hints": ["sales"],
                    "dimension_hints": ["item"],
                    "metric_hints": ["sold_quantity", "revenue"],
                    "primary_dimension": "item",
                },
                "metadata": {"confidence": 0.96, "fresh": True},
                "time_support": {"as_of": True, "range": True, "any": True},
            },
            {
                "report_name": "Item-wise Purchase Register",
                "constraints": {
                    "supported_filter_kinds": ["company", "date", "item"],
                    "required_filter_kinds": [],
                    "requirements_unknown": False,
                },
                "semantics": {
                    "domain_hints": ["purchasing"],
                    "dimension_hints": ["item"],
                    "metric_hints": ["received_quantity"],
                    "primary_dimension": "item",
                },
                "metadata": {"confidence": 0.96, "fresh": True},
                "time_support": {"as_of": True, "range": True, "any": True},
            },
        ]
    }

    cases: List[Dict[str, Any]] = [
        {
            "id": "CP-01-payable-vs-receivable",
            "spec": {
                "intent": "READ",
                "domain": "payable",
                "subject": "suppliers to pay",
                "metric": "outstanding_amount",
                "task_type": "detail",
                "filters": {"company": "MMOB"},
                "dimensions": ["supplier"],
                "group_by": ["supplier"],
                "time_scope": {"mode": "as_of"},
                "output_contract": {"mode": "detail", "minimal_columns": ["supplier", "outstanding_amount"]},
            },
            "expected_report": "Accounts Payable Summary",
        },
        {
            "id": "CP-02-receivable-vs-payable",
            "spec": {
                "intent": "READ",
                "domain": "receivable",
                "subject": "customers receivable",
                "metric": "outstanding_amount",
                "task_type": "detail",
                "filters": {"company": "MMOB"},
                "dimensions": ["customer"],
                "group_by": ["customer"],
                "time_scope": {"mode": "as_of"},
                "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding_amount"]},
            },
            "expected_report": "Accounts Receivable Summary",
        },
        {
            "id": "CP-03-sold-vs-received",
            "spec": {
                "intent": "READ",
                "domain": "sales",
                "subject": "items sold quantity",
                "metric": "sold_quantity",
                "task_type": "ranking",
                "filters": {"company": "MMOB"},
                "dimensions": ["item"],
                "group_by": ["item"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold_quantity"]},
            },
            "expected_report": "Item-wise Sales Register",
        },
        {
            "id": "CP-04-received-vs-sold",
            "spec": {
                "intent": "READ",
                "domain": "purchasing",
                "subject": "items received quantity",
                "metric": "received_quantity",
                "task_type": "ranking",
                "filters": {"company": "MMOB"},
                "dimensions": ["item"],
                "group_by": ["item"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "received_quantity"]},
            },
            "expected_report": "Item-wise Purchase Register",
        },
        {
            "id": "CP-05-customer-vs-supplier",
            "spec": {
                "intent": "READ",
                "domain": "finance",
                "subject": "top customers by outstanding receivable",
                "metric": "outstanding_amount",
                "task_type": "ranking",
                "filters": {"company": "MMOB"},
                "dimensions": ["customer"],
                "group_by": ["customer"],
                "time_scope": {"mode": "as_of"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "outstanding_amount"]},
            },
            "expected_report": "Accounts Receivable Summary",
        },
        {
            "id": "CP-06-supplier-vs-customer",
            "spec": {
                "intent": "READ",
                "domain": "finance",
                "subject": "top suppliers by payable outstanding",
                "metric": "outstanding_amount",
                "task_type": "ranking",
                "filters": {"company": "MMOB"},
                "dimensions": ["supplier"],
                "group_by": ["supplier"],
                "time_scope": {"mode": "as_of"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "outstanding_amount"]},
            },
            "expected_report": "Accounts Payable Summary",
        },
    ]

    case_results: List[Dict[str, Any]] = []
    passed = 0
    for case in cases:
        spec = dict(case["spec"])
        constraint_set = build_constraint_set(business_spec=spec, topic_state={})
        out = resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
            semantic_context={
                "catalog_available": True,
                "preferred_domains": [str(spec.get("domain") or "")],
                "preferred_dimensions": list(spec.get("dimensions") or []),
                "preferred_filter_kinds": ["company", "date"],
            },
        )
        selected = str(out.get("selected_report") or "")
        selected_candidate: Dict[str, Any] = {}
        for cand in list(out.get("candidate_reports") or []):
            if isinstance(cand, dict) and str(cand.get("report_name") or "") == selected:
                selected_candidate = cand
                break
        hard_blockers = list(selected_candidate.get("hard_blockers") or [])
        needs_clar = bool(out.get("needs_clarification"))
        ok = (selected == str(case["expected_report"])) and (not needs_clar) and (len(hard_blockers) == 0)
        if ok:
            passed += 1
        case_results.append(
            {
                "id": case["id"],
                "expected_report": case["expected_report"],
                "selected_report": selected,
                "needs_clarification": needs_clar,
                "hard_blockers": hard_blockers,
                "score": selected_candidate.get("score"),
                "confidence": selected_candidate.get("confidence"),
                "pass": bool(ok),
            }
        )

    total = len(case_results)
    pass_rate = (float(passed) / float(total)) if total else 0.0
    return {
        "suite_name": "phase6_confusion_pairs_v1",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(pass_rate, 4),
        "threshold": 0.95,
        "threshold_pass": bool(pass_rate >= 0.95),
        "cases": case_results,
    }


def _markdown(payload: Dict[str, Any]) -> str:
    wr = payload.get("wrong_report_delta") if isinstance(payload.get("wrong_report_delta"), dict) else {}
    cp = payload.get("confusion_pair_suite") if isinstance(payload.get("confusion_pair_suite"), dict) else {}
    gate = payload.get("phase6_gate") if isinstance(payload.get("phase6_gate"), dict) else {}

    lines = [
        "# Phase 6 Confusion-Pair Scorecard",
        "",
        f"- Executed: {payload.get('executed_at_utc')}",
        f"- Baseline artifact: `{payload.get('baseline_artifact')}`",
        f"- Current artifact: `{payload.get('current_artifact')}`",
        "",
        "## Wrong-Report Delta",
        f"- Baseline wrong-report rate: {wr.get('baseline_wrong_report_rate')}",
        f"- Current wrong-report rate: {wr.get('current_wrong_report_rate')}",
        f"- Relative improvement: {wr.get('relative_improvement')}",
        f"- Rule mode: {wr.get('rule_mode')}",
        f"- Gate pass: {wr.get('gate_pass')}",
        "",
        "## Confusion-Pair Suite",
        f"- Suite: {cp.get('suite_name')}",
        f"- Total: {cp.get('total')}",
        f"- Passed: {cp.get('passed')}",
        f"- Failed: {cp.get('failed')}",
        f"- Pass rate: {cp.get('pass_rate')}",
        f"- Threshold: {cp.get('threshold')}",
        f"- Gate pass: {cp.get('threshold_pass')}",
        "",
        "## P6 Exit Gate",
        f"- Wrong-report gate pass: {gate.get('wrong_report_delta_gate_pass')}",
        f"- Confusion-pair gate pass: {gate.get('confusion_pair_gate_pass')}",
        f"- Overall pass: {gate.get('overall_pass')}",
        "",
        "## Case Results",
    ]
    for row in list(cp.get("cases") or []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- {row.get('id')}: pass={row.get('pass')} | expected={row.get('expected_report')} | selected={row.get('selected_report')} | blockers={row.get('hard_blockers')}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 6 confusion-pair and wrong-report scorecard.")
    ap.add_argument("--baseline", required=True, help="Baseline artifact JSON (phase1 baseline or compatible).")
    ap.add_argument("--current", required=True, help="Current phase6 raw artifact JSON.")
    ap.add_argument("--output-dir", default="impl_factory/04_automation/logs", help="Output folder.")
    args = ap.parse_args()

    baseline_path = Path(str(args.baseline)).resolve()
    current_path = Path(str(args.current)).resolve()

    baseline_wrong = _resolve_wrong_report_rate(baseline_path)
    current_wrong = _resolve_wrong_report_rate(current_path)

    rule_mode = "standard_40pct_improvement"
    relative_improvement: Optional[float] = None
    wrong_report_gate_pass = False
    note = ""
    if baseline_wrong is None or current_wrong is None:
        rule_mode = "insufficient_data"
        wrong_report_gate_pass = False
        note = "unable_to_resolve_wrong_report_rate"
    elif baseline_wrong > 0.0:
        relative_improvement = round((baseline_wrong - current_wrong) / baseline_wrong, 4)
        wrong_report_gate_pass = bool(relative_improvement >= 0.40)
    else:
        # Baseline already at zero. Enforce non-regression.
        rule_mode = "baseline_zero_non_regression"
        relative_improvement = 0.0 if current_wrong <= baseline_wrong else -1.0
        wrong_report_gate_pass = bool(current_wrong <= baseline_wrong)

    confusion = _evaluate_confusion_suite()

    payload: Dict[str, Any] = {
        "executed_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "mode": "phase6_confusion_pair_scorecard",
        "baseline_artifact": str(baseline_path),
        "current_artifact": str(current_path),
        "wrong_report_delta": {
            "baseline_wrong_report_rate": baseline_wrong,
            "current_wrong_report_rate": current_wrong,
            "relative_improvement": relative_improvement,
            "rule_mode": rule_mode,
            "gate_pass": bool(wrong_report_gate_pass),
            "note": note,
        },
        "confusion_pair_suite": confusion,
        "phase6_gate": {
            "wrong_report_delta_gate_pass": bool(wrong_report_gate_pass),
            "confusion_pair_gate_pass": bool(confusion.get("threshold_pass")),
            "overall_pass": bool(wrong_report_gate_pass and bool(confusion.get("threshold_pass"))),
        },
    }

    out_dir = Path(str(args.output_dir or "impl_factory/04_automation/logs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_json = out_dir / f"{ts}_phase6_confusion_pair_scorecard.json"
    out_md = out_dir / f"{ts}_phase6_confusion_pair_scorecard.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(_markdown(payload), encoding="utf-8")

    print(f"OUT_JSON={out_json}")
    print(f"OUT_MD={out_md}")
    print(json.dumps(payload.get("phase6_gate") or {}, ensure_ascii=False))


if __name__ == "__main__":
    main()
