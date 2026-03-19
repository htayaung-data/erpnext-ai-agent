from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase4_audit_ops_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("phase4_audit_ops_report_module", str(SCRIPT_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load phase4_audit_ops_report module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Phase4AuditOpsReportTests(unittest.TestCase):
    def test_complete_read_turn_scores_as_complete(self):
        mod = _load_module()
        audit = {
            "type": "audit_turn",
            "ts": "2026-03-19T12:00:00Z",
            "turn_id": "t1",
            "intent": "READ",
            "result_meta": {"payload_type": "table"},
            "turn_audit_envelope": {
                "schema_version": "turn_audit_envelope_v1",
                "trace_id": "t1",
                "engine_version": "v7",
                "engine_mode": "v7_active",
                "capability_version": "cap_v1",
                "model_version": {"plan": "", "spec": "gpt-5.4-mini"},
                "prompt_version": {"plan": "", "spec": "spec_v1"},
                "fallback_used": {"plan": False, "spec": False, "any": False},
                "security_outcome": {"status": "not_applicable"},
                "selected_candidate": {"report_name": "Customer Ledger Summary"},
                "validation_result": {"quality_verdict": "PASS"},
                "latency_ms": 120,
                "final_response_hash": "abc",
            },
        }
        report = mod.build_phase4_audit_ops_report(
            session_rows=[{"name": "S-1", "audit_turns": [{"audit": audit}]}],
            since_hours=24,
        )
        summary = report.get("summary") or {}
        self.assertEqual(int(summary.get("actionable_turns_in_window") or 0), 1)
        self.assertEqual(int(summary.get("actionable_turns_complete") or 0), 1)
        self.assertEqual(bool(summary.get("audit_completeness_ok")), True)

    def test_missing_engine_mode_and_report_name_are_counted(self):
        mod = _load_module()
        audit = {
            "type": "audit_turn",
            "ts": "2026-03-19T12:00:00Z",
            "turn_id": "t2",
            "intent": "READ",
            "result_meta": {"payload_type": "table"},
            "turn_audit_envelope": {
                "schema_version": "turn_audit_envelope_v1",
                "trace_id": "t2",
                "engine_version": "v7",
                "engine_mode": "",
                "capability_version": "cap_v1",
                "model_version": {"plan": "", "spec": "gpt-5.4-mini"},
                "prompt_version": {"plan": "", "spec": "spec_v1"},
                "fallback_used": {"plan": False, "spec": False, "any": False},
                "security_outcome": {"status": "not_applicable"},
                "selected_candidate": {"report_name": ""},
                "validation_result": {"quality_verdict": "PASS"},
                "latency_ms": 120,
                "final_response_hash": "abc",
            },
        }
        report = mod.build_phase4_audit_ops_report(
            session_rows=[{"name": "S-2", "audit_turns": [{"audit": audit}]}],
            since_hours=24,
        )
        missing = report.get("missing_required_field_counts") or {}
        self.assertEqual(int(missing.get("engine_mode") or 0), 1)
        self.assertEqual(int(missing.get("selected_candidate.report_name") or 0), 1)

    def test_write_confirmation_security_outcome_and_fallback_counts(self):
        mod = _load_module()
        audit = {
            "type": "audit_turn",
            "ts": "2026-03-19T12:00:00Z",
            "turn_id": "t3",
            "intent": "WRITE_CONFIRM",
            "result_meta": {"payload_type": "text"},
            "turn_audit_envelope": {
                "schema_version": "turn_audit_envelope_v1",
                "trace_id": "t3",
                "engine_version": "v7",
                "engine_mode": "v7_active",
                "capability_version": "cap_v1",
                "model_version": {"plan": "", "spec": ""},
                "prompt_version": {"plan": "", "spec": ""},
                "fallback_used": {"plan": True, "spec": False, "any": True},
                "security_outcome": {"status": "confirmation_required"},
                "selected_candidate": {"report_name": ""},
                "validation_result": {"quality_verdict": "PASS"},
                "latency_ms": 40,
                "final_response_hash": "xyz",
            },
        }
        report = mod.build_phase4_audit_ops_report(
            session_rows=[{"name": "S-3", "audit_turns": [{"audit": audit}]}],
            since_hours=24,
        )
        sec = report.get("security_outcome_counts") or {}
        fallback = report.get("fallback_summary") or {}
        self.assertEqual(int(sec.get("confirmation_required") or 0), 1)
        self.assertEqual(int(fallback.get("fallback_any_true") or 0), 1)
        self.assertEqual(int(fallback.get("fallback_plan_true") or 0), 1)

    def test_low_volume_window_is_marked_watch(self):
        mod = _load_module()
        current_audit = {
            "type": "audit_turn",
            "ts": "2026-03-19T12:30:00Z",
            "turn_id": "t4",
            "intent": "READ",
            "result_meta": {"payload_type": "table"},
            "turn_audit_envelope": {
                "schema_version": "turn_audit_envelope_v1",
                "trace_id": "t4",
                "engine_version": "v7",
                "engine_mode": "v7_active",
                "capability_version": "cap_v1",
                "model_version": {"plan": "", "spec": "gpt-5.4-mini"},
                "prompt_version": {"plan": "", "spec": "spec_v1"},
                "fallback_used": {"plan": False, "spec": False, "any": False},
                "security_outcome": {"status": "not_applicable"},
                "selected_candidate": {"report_name": "Sales Analytics"},
                "validation_result": {"quality_verdict": "PASS"},
                "latency_ms": 55,
                "final_response_hash": "hash4",
            },
        }
        older_audit = {
            **current_audit,
            "turn_id": "old1",
            "ts": "2026-03-19T09:00:00Z",
        }
        report = mod.build_phase4_audit_ops_report(
            session_rows=[{"name": "S-4", "audit_turns": [{"audit": current_audit}, {"audit": older_audit}]}],
            since_hours=1,
            now_utc=datetime(2026, 3, 19, 13, 0, 0, tzinfo=timezone.utc),
            min_actionable_turns_for_stable=20,
        )
        summary = report.get("summary") or {}
        self.assertEqual(int(summary.get("actionable_turns_in_window") or 0), 1)
        self.assertEqual(bool(summary.get("low_volume")), True)
        self.assertEqual(str(summary.get("review_status_hint") or ""), "Watch")


if __name__ == "__main__":
    unittest.main()
