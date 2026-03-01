from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/read_execution_runner.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_read_execution_runner_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load read_execution_runner module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _base_kwargs():
    quality_calls = []

    def _legacy_path_unavailable_payload():
        return {"type": "text", "text": "legacy unavailable"}

    def _capture_source_columns(payload):
        return dict(payload)

    def _as_payload(value):
        return dict(value) if isinstance(value, dict) else {"type": "text", "text": str(value)}

    def _apply_transform_last(payload, business_spec):
        return dict(payload)

    def _looks_like_system_error_text(payload):
        return False

    def _make_transform_tool_message(**kwargs):
        return "transform"

    def _shape_response(payload, business_spec):
        return dict(payload)

    def _sanitize_user_payload(**kwargs):
        return dict(kwargs.get("payload") or {})

    def _apply_requested_entity_row_filters(**kwargs):
        return dict(kwargs.get("payload") or {})

    def _make_response_shaper_tool_message(**kwargs):
        return "shaper"

    def _evaluate_quality_gate(**kwargs):
        quality_calls.append(dict(kwargs))
        return {
            "verdict": "PASS",
            "failed_check_ids": [],
            "hard_fail_check_ids": [],
            "repairable_check_ids": [],
            "checks": [],
        }

    def _should_switch_candidate_on_repairable(**kwargs):
        return False

    def _resolve_business_request(**kwargs):
        return {"resolved": {"selected_report": "Report A", "selected_score": 1.0}}

    def _quality_has_repairable_failure_class(quality, classes):
        return False

    def _unsupported_message_from_spec(spec):
        return "unsupported"

    def _planner_option_actions(**kwargs):
        return {"switch to compatible report": "switch_report", "keep current scope": "keep_current"}

    def _default_clarification_question(reason):
        return "clarify"

    return {
        "message": "test message",
        "mode": "start",
        "source": "report_qa_start",
        "plan_seed": {"action": "run_report"},
        "max_steps": 2,
        "spec_obj": {"intent": "READ", "task_class": "analytical_read", "filters": {}, "output_contract": {}},
        "spec_envelope": {"spec": {"intent": "READ", "task_class": "analytical_read"}},
        "resolved": {"selected_report": "Report A", "selected_score": 1.0},
        "selected_report": "Report A",
        "selected_score": 1.0,
        "candidate_reports": ["Report A", "Report B"],
        "candidate_scores": {"Report A": 1.0, "Report B": 0.9},
        "candidate_cursor": 0,
        "initial_step_trace": [{"step": 0, "action": "resolver_selected", "selected_report": "Report A"}],
        "previous_topic_state": {},
        "session_name": "browser-session",
        "user": "test@example.com",
        "export_requested": False,
        "direct_doc_payload": None,
        "direct_latest_payload": None,
        "clarify_decision": {"should_clarify": False, "reason": "", "question": ""},
        "internal_retry_key": "__retry__",
        "verdict_pass": "PASS",
        "verdict_hard_fail": "HARD_FAIL",
        "verdict_repairable_fail": "REPAIRABLE_FAIL",
        "execute_selected_report_direct_fn": lambda **kwargs: {"type": "report_table", "report_name": "Report A", "table": {"columns": [{"label": "X"}], "rows": [{"x": 1}]}},
        "legacy_path_unavailable_payload_fn": _legacy_path_unavailable_payload,
        "load_last_result_payload_fn": lambda **kwargs: None,
        "extract_auto_switch_pending_fn": lambda payload: None,
        "capture_source_columns_fn": _capture_source_columns,
        "as_payload_fn": _as_payload,
        "apply_transform_last_fn": _apply_transform_last,
        "looks_like_system_error_text_fn": _looks_like_system_error_text,
        "make_transform_tool_message_fn": _make_transform_tool_message,
        "shape_response_fn": _shape_response,
        "sanitize_user_payload_fn": _sanitize_user_payload,
        "apply_requested_entity_row_filters_fn": _apply_requested_entity_row_filters,
        "make_response_shaper_tool_message_fn": _make_response_shaper_tool_message,
        "evaluate_quality_gate_fn": _evaluate_quality_gate,
        "should_switch_candidate_on_repairable_fn": _should_switch_candidate_on_repairable,
        "resolve_business_request_fn": _resolve_business_request,
        "quality_has_repairable_failure_class_fn": _quality_has_repairable_failure_class,
        "unsupported_message_from_spec_fn": _unsupported_message_from_spec,
        "planner_option_actions_fn": _planner_option_actions,
        "default_clarification_question_fn": _default_clarification_question,
        "_quality_calls": quality_calls,
    }


class V7ReadExecutionRunnerTests(unittest.TestCase):
    def test_guard_stop_on_repeated_execution_signature(self):
        mod = _load_module()
        kwargs = _base_kwargs()
        kwargs["execute_selected_report_direct_fn"] = (
            lambda **kw: {
                "type": "report_table",
                "report_name": "Report A",
                "table": {"columns": [{"label": "X"}], "rows": [{"x": 1}]},
                "__retry__": True,
            }
        )
        quality_calls = kwargs.pop("_quality_calls")

        out = mod.execute_read_loop(**kwargs)

        self.assertTrue(bool(out.get("repeated_guard")))
        payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
        self.assertIn("repeated execution path", str(payload.get("text") or "").lower())
        self.assertEqual(len(quality_calls), 2)
        self.assertTrue(bool(quality_calls[-1].get("repeated_call_guard_triggered")))

    def test_auto_switches_to_next_candidate_from_quality_pending(self):
        mod = _load_module()
        kwargs = _base_kwargs()
        calls = {"count": 0}

        def _execute(**kw):
            calls["count"] += 1
            if calls["count"] == 1:
                return {
                    "type": "text",
                    "text": "switch",
                    "_pending_state": {
                        "mode": "planner_clarify",
                        "report_name": "Report A",
                        "quality_clarification": {"intent": "switch_report", "switch_attempt": 0},
                    },
                }
            return {
                "type": "report_table",
                "report_name": kw.get("selected_report") or "Report B",
                "table": {"columns": [{"label": "X"}], "rows": [{"x": 1}]},
            }

        def _extract_auto(payload):
            pending = payload.get("_pending_state") if isinstance(payload, dict) else None
            return pending if isinstance(pending, dict) else None

        kwargs["execute_selected_report_direct_fn"] = _execute
        kwargs["extract_auto_switch_pending_fn"] = _extract_auto
        kwargs.pop("_quality_calls")

        out = mod.execute_read_loop(**kwargs)

        self.assertEqual(str(out.get("selected_report") or ""), "Report B")
        trace = [x for x in list(out.get("step_trace") or []) if isinstance(x, dict)]
        self.assertTrue(any(str(x.get("action") or "") == "auto_switch_next_candidate_from_quality_pending" for x in trace))

    def test_final_repairable_fallback_returns_planner_clarify_payload(self):
        mod = _load_module()
        kwargs = _base_kwargs()

        def _evaluate_quality_gate(**kw):
            return {
                "verdict": "REPAIRABLE_FAIL",
                "failed_check_ids": ["QG11_minimal_columns_present"],
                "hard_fail_check_ids": [],
                "repairable_check_ids": ["QG11_minimal_columns_present"],
                "checks": [],
            }

        kwargs["max_steps"] = 2
        kwargs["evaluate_quality_gate_fn"] = _evaluate_quality_gate
        kwargs["should_switch_candidate_on_repairable_fn"] = lambda **kw: False
        kwargs["resolve_business_request_fn"] = lambda **kw: {"resolved": {"selected_report": "Report A", "selected_score": 1.0}}
        kwargs["quality_has_repairable_failure_class_fn"] = lambda quality, classes: True
        kwargs["unsupported_message_from_spec_fn"] = lambda spec: "unsupported"
        kwargs.pop("_quality_calls")

        out = mod.execute_read_loop(**kwargs)

        payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
        pending = payload.get("_pending_state") if isinstance(payload.get("_pending_state"), dict) else {}
        self.assertEqual(str(payload.get("type") or ""), "text")
        self.assertIn("unsupported", str(payload.get("text") or ""))
        self.assertEqual(str(pending.get("mode") or ""), "planner_clarify")
        clarify = out.get("clarify_decision") if isinstance(out.get("clarify_decision"), dict) else {}
        self.assertEqual(str(clarify.get("reason") or ""), "hard_constraint_not_supported")


if __name__ == "__main__":
    unittest.main()
