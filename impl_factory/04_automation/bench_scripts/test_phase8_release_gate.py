from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from pathlib import Path

from phase8_release_gate import (
    MANDATORY_IDS,
    Artifact,
    build_release_evaluation,
    select_first_run_results,
)


def _mk_result(case_id: str, *, passed: bool, role: str = "ai.reader", clarification: bool = False) -> dict:
    return {
        "id": case_id,
        "role": role,
        "pass": bool(passed),
        "actual": {
            "assistant_type": "text" if clarification else "report_table",
            "pending_mode": None if not clarification else "need_filters",
            "clarification": bool(clarification),
            "meta_clarification": False,
            "duration_ms": 1000,
        },
        "semantic": {
            "blocker_clarification": bool(clarification),
            "meta_clarification": False,
            "assertions": {
                "report_alignment_pass": bool(passed),
                "dimension_alignment_pass": True,
                "metric_alignment_pass": True,
                "time_scope_alignment_pass": True,
                "filter_alignment_pass": True,
                "output_shape_pass": True,
                "clarification_policy_pass": True,
                "loop_policy_pass": True,
            },
        },
    }


def _mk_artifact(*, ts: datetime, results: list[dict], with_preconditions: bool = True) -> Artifact:
    data = {
        "executed_at_utc": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "results": results,
    }
    if with_preconditions:
        data["preconditions"] = {
            "report_list_ok": True,
            "report_requirements_ok": True,
            "generate_report_ok": True,
        }
    return Artifact(path=Path(f"/tmp/{ts.timestamp()}.json"), executed_at_utc=data["executed_at_utc"], ts=ts, data=data)


class Phase8ReleaseGateTests(unittest.TestCase):
    def _write_payload(self, name: str, *, executed_at_utc: str, results: list[dict], with_preconditions: bool = True) -> Path:
        p = Path(f"/tmp/{name}.json")
        payload = {
            "executed_at_utc": executed_at_utc,
            "results": results,
        }
        if with_preconditions:
            payload["preconditions"] = {
                "report_list_ok": True,
                "report_requirements_ok": True,
                "generate_report_ok": True,
            }
        p.write_text(__import__("json").dumps(payload, ensure_ascii=False), encoding="utf-8")
        return p

    def test_first_run_policy_keeps_earliest_case_result(self):
        now = datetime.utcnow()
        art1 = _mk_artifact(ts=now, results=[_mk_result("FIN-01", passed=False)])
        art2 = _mk_artifact(ts=now + timedelta(minutes=1), results=[_mk_result("FIN-01", passed=True)])
        selected, stats = select_first_run_results([art2, art1])
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["pass"], False)
        self.assertEqual(stats.get("diagnostic_ignored_count"), 1)

    def test_gate_fails_when_role_parity_missing(self):
        now = datetime.utcnow()
        results = []
        for cid in sorted(MANDATORY_IDS):
            # Intentionally keep only reader role to trigger role parity fail.
            results.append(_mk_result(cid, passed=True, role="ai.reader", clarification=False))
        p = self._write_payload("test_phase8_role_parity_fail", executed_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"), results=results)
        out = build_release_evaluation(raw_paths=[p], stage_percent=10)
        gate = out.get("release_gate") or {}
        self.assertEqual(gate.get("role_parity_reader_vs_operator"), False)
        self.assertEqual(gate.get("overall_go"), False)

    def test_gate_passes_for_balanced_roles_and_full_pass_set(self):
        now = datetime.utcnow()
        results = []
        for cid in sorted(MANDATORY_IDS):
            role = "ai.operator" if cid in {"HR-01", "OPS-01", "DOC-01", "WR-01", "WR-02", "WR-03", "WR-04"} else "ai.reader"
            clar = cid in {"ENT-01", "ENT-02", "CFG-01"}
            results.append(_mk_result(cid, passed=True, role=role, clarification=clar))
        p = self._write_payload("test_phase8_release_gate_payload", executed_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"), results=results)
        out = build_release_evaluation(raw_paths=[p], stage_percent=10, latency_p95_sla_ms=5000)
        gate = out.get("release_gate") or {}
        self.assertEqual(gate.get("mandatory_pass_rate_100"), True)
        self.assertEqual(gate.get("critical_clear_query_pass_100"), True)
        self.assertEqual(gate.get("role_parity_reader_vs_operator"), True)
        self.assertEqual(gate.get("overall_go"), True)


if __name__ == "__main__":
    unittest.main()
