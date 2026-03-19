from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/chat/turn_audit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("chat_turn_audit_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load chat turn_audit module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ChatTurnAuditTests(unittest.TestCase):
    def test_build_turn_audit_envelope_unifies_runtime_surfaces(self):
        mod = _load_module()
        planner_output = {
            "plan": {
                "action": "run_report",
                "report_name": "Item-wise Sales Register",
                "llm_meta": {
                    "prompt_version": "planner_prompt_v2026_02_19_now1",
                    "model_version": "gpt-5.4-mini",
                    "fallback_used": False,
                },
            },
            "business_request_spec": {
                "spec": {
                    "intent": "READ",
                    "task_type": "ranking",
                    "task_class": "analytical_read",
                    "metric": "sold quantity",
                    "group_by": ["item"],
                    "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity"]},
                    "llm_meta": {
                        "prompt_version": "spec_prompt_v2026_02_19_now1",
                        "model_version": "gpt-5.4-mini",
                        "fallback_used": False,
                    },
                }
            },
        }
        tool_messages = [
            json.dumps({"type": "engine_route", "executed_engine": "v7", "effective_mode": "v7_active"}),
            json.dumps(
                {
                    "type": "v7_business_request_spec",
                    "schema_valid": True,
                    "schema_errors": [],
                    "spec": planner_output["business_request_spec"]["spec"],
                }
            ),
            json.dumps(
                {
                    "type": "v7_quality_gate",
                    "verdict": "PASS",
                    "failed_check_ids": [],
                    "failed_failure_classes": [],
                    "repairable_failure_classes": [],
                    "hard_failure_classes": [],
                    "hard_fail_check_ids": [],
                    "repairable_check_ids": [],
                }
            ),
            json.dumps(
                {
                    "type": "v7_read_engine",
                    "selected_report": "Item-wise Sales Register",
                    "selected_score": 0.97,
                }
            ),
        ]

        out = mod.build_turn_audit_envelope(
            turn_id="abc123",
            planner_output=planner_output,
            tool_messages=tool_messages,
            error_envelope=None,
            latency_ms=184,
            final_response_hash="hash123",
            user_payload={"type": "table", "table": {"columns": [], "rows": []}},
        )

        self.assertEqual(str(out.get("schema_version") or ""), "turn_audit_envelope_v1")
        self.assertEqual(str(out.get("trace_id") or ""), "abc123")
        self.assertEqual(str(out.get("engine_version") or ""), "v7")
        self.assertEqual(str(out.get("engine_mode") or ""), "v7_active")
        self.assertEqual(str(((out.get("model_version") or {}).get("plan") or "")), "gpt-5.4-mini")
        self.assertEqual(str(((out.get("prompt_version") or {}).get("spec") or "")), "spec_prompt_v2026_02_19_now1")
        self.assertEqual(str(((out.get("selected_candidate") or {}).get("report_name") or "")), "Item-wise Sales Register")
        self.assertEqual(str(((out.get("validation_result") or {}).get("quality_verdict") or "")), "PASS")
        self.assertEqual(bool(((out.get("fallback_used") or {}).get("any"))), False)
        self.assertEqual(str(((out.get("security_outcome") or {}).get("status") or "")), "not_applicable")
        self.assertEqual(int(out.get("latency_ms") or 0), 184)
        self.assertEqual(str(out.get("final_response_hash") or ""), "hash123")

    def test_error_trace_id_takes_precedence_when_present(self):
        mod = _load_module()
        out = mod.build_turn_audit_envelope(
            turn_id="abc123",
            planner_output={},
            tool_messages=[],
            error_envelope={"code": "TOOL_EXECUTION_FAILED", "trace_id": "err999"},
            latency_ms=42,
            final_response_hash="hash999",
            user_payload={"type": "error", "text": "I couldn’t process that request right now. Please try again."},
        )
        self.assertEqual(str(out.get("trace_id") or ""), "err999")
        self.assertEqual(str(((out.get("validation_result") or {}).get("error_code") or "")), "TOOL_EXECUTION_FAILED")

    def test_write_confirmation_sets_security_outcome(self):
        mod = _load_module()
        planner_output = {
            "business_request_spec": {
                "spec": {
                    "intent": "WRITE_DRAFT",
                    "subject": "ToDo",
                    "llm_meta": {
                        "prompt_version": "spec_prompt_v2026_02_19_now1",
                        "model_version": "gpt-5.4-mini",
                        "fallback_used": False,
                    },
                }
            }
        }
        pending = {
            "mode": "write_confirmation",
            "write_draft": {
                "doctype": "ToDo",
                "operation": "delete",
            },
        }
        out = mod.build_turn_audit_envelope(
            turn_id="w1",
            planner_output=planner_output,
            tool_messages=[],
            error_envelope=None,
            latency_ms=25,
            final_response_hash="hashw1",
            user_payload={
                "type": "text",
                "text": "Delete ToDo with ID TEST-123? Reply **confirm** to execute or **cancel** to stop.",
            },
            pending_state_to_set=pending,
            clear_pending=False,
        )
        sec = out.get("security_outcome") or {}
        self.assertEqual(str(sec.get("status") or ""), "confirmation_required")
        self.assertEqual(str(sec.get("doctype") or ""), "ToDo")
        self.assertEqual(str(sec.get("operation") or ""), "delete")
        self.assertEqual(bool(sec.get("requires_confirmation")), True)

    def test_write_blocked_disabled_and_fallback_are_emitted(self):
        mod = _load_module()
        planner_output = {
            "plan": {
                "action": "write_draft",
                "llm_meta": {
                    "prompt_version": "planner_prompt_v2026_02_19_now1",
                    "model_version": "gpt-5.4-mini",
                    "fallback_used": True,
                },
            },
            "business_request_spec": {
                "spec": {
                    "intent": "WRITE_DRAFT",
                    "subject": "ToDo",
                    "llm_meta": {
                        "prompt_version": "spec_prompt_v2026_02_19_now1",
                        "model_version": "gpt-5.4-mini",
                        "fallback_used": True,
                    },
                }
            },
        }
        out = mod.build_turn_audit_envelope(
            turn_id="w2",
            planner_output=planner_output,
            tool_messages=[],
            error_envelope=None,
            latency_ms=19,
            final_response_hash="hashw2",
            user_payload={
                "type": "text",
                "text": "Write-actions are disabled in this environment. Please ask an administrator to enable them.",
            },
        )
        sec = out.get("security_outcome") or {}
        fallback = out.get("fallback_used") or {}
        self.assertEqual(str(sec.get("status") or ""), "blocked_disabled")
        self.assertEqual(bool(fallback.get("plan")), True)
        self.assertEqual(bool(fallback.get("spec")), True)
        self.assertEqual(bool(fallback.get("any")), True)


if __name__ == "__main__":
    unittest.main()
