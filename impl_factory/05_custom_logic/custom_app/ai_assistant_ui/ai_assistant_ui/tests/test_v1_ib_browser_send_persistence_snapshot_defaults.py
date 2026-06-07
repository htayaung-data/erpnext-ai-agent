from __future__ import annotations

import importlib
import sys
import types
import unittest
from unittest.mock import patch

if "frappe" not in sys.modules:
    fake_frappe = types.ModuleType("frappe")
    fake_frappe.local = types.SimpleNamespace(site="unit.test")
    fake_frappe.get_doc = lambda *_args, **_kwargs: None
    fake_frappe.get_traceback = lambda: ""
    fake_frappe.log_error = lambda *_args, **_kwargs: None
    sys.modules["frappe"] = fake_frappe


EXPECTED_SNAPSHOT_DEFAULT_EXPORTS = (
    "build_active_sequence_snapshot_state",
    "build_historical_recent_focus_snapshot_inputs",
    "build_latest_artifact_snapshot_state",
    "build_latest_grounded_turn_snapshot_state",
    "build_latest_recovery_contract_snapshot_state",
    "build_latest_repair_intent_snapshot_state",
    "build_pending_clarification_snapshot_state",
    "build_snapshot_internal_details",
    "build_snapshot_state_quality",
    "empty_resumable_prior_request_state",
)


class V1IBBrowserSendPersistenceSnapshotDefaultsTests(unittest.TestCase):
    def test_snapshot_defaults_module_exports_service_lazy_helpers(self):
        module = importlib.import_module("ai_assistant_ui.qwen_chat.snapshot_defaults")

        for helper_name in EXPECTED_SNAPSHOT_DEFAULT_EXPORTS:
            with self.subTest(helper_name=helper_name):
                self.assertTrue(callable(getattr(module, helper_name, None)))

    def test_service_lazy_snapshot_default_helpers_resolve_for_send_snapshot_path(self):
        from ai_assistant_ui.qwen_chat import service

        resumable_prior_request = service._empty_resumable_prior_request_state_helper()
        pending_clarification = service._build_pending_clarification_snapshot_state_helper(
            signal={},
            source_kind="none",
            attempt_count=0,
            max_attempts=0,
            continuation_lane="",
            status="none",
            source_tool_index=-1,
        )
        quality = service._build_snapshot_state_quality_helper(
            pending_clarification=pending_clarification,
            latest_grounded_turn={},
            latest_artifact={},
            latest_recovery_contract={},
            latest_repair_intent={},
            active_sequence={},
            recent_focus={},
            recent_focus_affordance={},
            resumable_prior_request=resumable_prior_request,
        )

        self.assertFalse(resumable_prior_request["available"])
        self.assertEqual(resumable_prior_request["derivation_basis"], "conservative_none")
        self.assertFalse(pending_clarification["available"])
        self.assertFalse(quality["has_resumable_prior_request"])
        self.assertFalse(quality["has_authoritative_pending_clarification"])

    def test_compiled_query_helper_accepts_frontdoor_contract_metadata(self):
        from ai_assistant_ui.qwen_chat import fresh_query_interpreter as fqi

        frontdoor_payload = {
            "type": "qwen_front_door_contract",
            "authority_effect": "evidence_only",
            "route_target": "compiled_query",
        }
        semantic_result = fqi.SemanticFreshQueryResult(
            status="no_match",
            interpretation=None,
            confidence_threshold=0.72,
            agent_meta={"engine": "unit_test"},
        )

        with patch.object(fqi, "interpret_fresh_query_semantically", return_value=semantic_result), patch.object(
            fqi,
            "_deterministic_family_surface_interpretation",
            return_value=None,
        ):
            result = fqi.compile_from_fresh_query_message(
                session_id="unit-session",
                user_id="unit-user",
                site_name="unit.test",
                message="unit no-match request",
                recent_messages=[],
                clarification_resolution=None,
                front_door_contract=frontdoor_payload,
            )

        self.assertEqual(result.get("front_door_contract"), frontdoor_payload)
        self.assertEqual(result.get("fresh_query_interpretation", {}).get("status"), "no_match")
        self.assertNotIn("report_routing_allowed", result.get("front_door_contract", {}))

    def test_governed_report_executor_accepts_request_message_without_trace_leak(self):
        from ai_assistant_ui.qwen_chat import governed_report_executor as executor

        def fake_execute_once(**_kwargs):
            return {
                "output_obj": {"result": {"columns": [], "result": []}},
                "success": True,
                "error": "",
                "duration_ms": 0,
                "row_count": 0,
            }

        with patch.object(executor, "get_report_spec", return_value={"grounding_mode": "report"}), patch.object(
            executor,
            "_execute_once",
            side_effect=fake_execute_once,
        ):
            payload = executor.execute_governed_report(
                report_name="Synthetic Item Sales",
                filters={"item_code": "EC7H-ITEM-A"},
                user="Administrator",
                mode="compiled_read_query",
                request_message="Show EC7H-ITEM-A item sales",
            )

        self.assertTrue(payload.get("ok"))
        self.assertEqual(
            payload.get("agent_meta", {}).get("engine"),
            "deterministic_governed_report_executor",
        )
        trace_blob = repr(payload.get("tool_trace"))
        self.assertNotIn("Show EC7H-ITEM-A item sales", trace_blob)
        self.assertNotIn("request_message", trace_blob)


if __name__ == "__main__":
    unittest.main()
