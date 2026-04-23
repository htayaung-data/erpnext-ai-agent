import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.compiled_support import (
	compiled_decision_message,
	handle_compiled_first_turn_result,
)
from ai_assistant_ui.qwen_chat.compound_request_support import (
	compound_request_internal_details_with_multi_step_bridge,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_compound_request_assessment_contract,
	build_followup_resolution_contract,
	build_front_door_intent_gate_contract,
	build_interaction_contract,
)


class _DummyContract:
	def __init__(self, payload):
		self._payload = dict(payload)

	def to_payload(self):
		return dict(self._payload)


class TestCompiledSupportContracts(unittest.TestCase):
	def test_handle_compiled_first_turn_result_appends_next_step_note_and_advances_plan(self):
		messages = []
		tool_payloads = []
		session_doc = object()
		class _GroundedTurnContext:
			grounded = True

			def to_payload(self):
				return {
					"type": "qwen_grounded_turn_context",
					"request_id": "compound-seq",
					"trace_request_id": "compound-seq-trace",
					"grounded": True,
					"artifact_family_id": "master_data_directory",
					"source_name": "Customer Master List",
				}
		compound_assessment = build_compound_request_assessment_contract(
			request_id="compound-seq",
			status="ordered_execution_ready",
			segments=["give me some customer list", "give me some supplier list"],
			suggested_options=["Customer list", "Supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details=compound_request_internal_details_with_multi_step_bridge(
				request_id="compound-seq",
				status="ordered_execution_ready",
				segments=["give me some customer list", "give me some supplier list"],
				suggested_options=["Customer list", "Supplier list"],
				internal_details={
				"continuation_lane": "front_door",
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"primary_segment_label": "Customer list",
				"primary_segment_payload": {
					"segment_message": "give me some customer list",
					"segment_label": "Customer list",
					"interpretation_source": "deterministic_surface",
				},
				"remaining_segment_messages": ["give me some supplier list"],
				"remaining_segment_labels": ["Supplier list"],
				"remaining_segment_payloads": [
					{
						"segment_message": "give me some supplier list",
						"segment_label": "Supplier list",
						"interpretation_source": "deterministic_surface",
					}
				],
				"segment_execution_payloads": [
					{
						"segment_message": "give me some customer list",
						"segment_label": "Customer list",
						"interpretation_source": "deterministic_surface",
					},
					{
						"segment_message": "give me some supplier list",
						"segment_label": "Supplier list",
						"interpretation_source": "deterministic_surface",
					},
				],
				},
			),
		)
		frontdoor_contract = build_front_door_intent_gate_contract(
			request_id="compound-seq",
			intent_class="route_onward",
			confidence=1.0,
			grounded_context_available=False,
			reason="Ordered multi-step request.",
			response_payload_override={
				"compound_request_assessment": compound_assessment.to_payload(),
			},
		)
		interaction_contract = build_interaction_contract(
			request_id="compound-seq",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			raw_message="give me some customer list then give me some supplier list",
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="compound-seq",
			mode="capability_requery",
			requested_modes=[],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=False,
			reason="fresh query",
		)
		execution_path = ExecutionPath(
			request_id="compound-seq",
			path="runtime",
			reason="runtime",
			requires_runtime=True,
			grounded_required=False,
		)
		result = {
			"runtime_payload": {
				"ok": True,
				"answer_text": "Customer list result",
				"tool_trace": [],
				"agent_meta": {},
			},
			"family_validation": {"status": "pass"},
			"semantic_intent_validation": {"status": "pass"},
			"phase4_latency_breakdown": {},
			"compiled_execution_audit": {},
			"pipeline": {},
			"normalized_family_artifact": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "master_data_directory",
				"artifact_type": "normalized_family_artifact",
			},
		}

		ok, payload = handle_compiled_first_turn_result(
			session_doc=session_doc,
			request_id="compound-seq",
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			result=result,
			governed_scope_contract=None,
			front_door_contract=frontdoor_contract,
			clarification_response_contract=None,
			pre_result_tool_payloads=[],
			append_compiled_attempt_artifacts=lambda *_args, **_kwargs: None,
			compiled_decision_message=lambda **_kwargs: ("Customer list result", {}),
			compiled_clarification_reason_contract=lambda **_kwargs: None,
			append_message=lambda _doc, role, content: messages.append((role, content)),
			append_tool_payload=lambda _doc, payload: tool_payloads.append(dict(payload)),
			assistant_text_payload=lambda text: text,
			tool_trace_message=lambda **_kwargs: "",
			latest_qwen_trace_payload=lambda _doc: {},
			latest_assistant_payload=lambda _doc: {"text": messages[-1][1] if messages else ""},
			append_knowledge_boundary_contract=lambda *_args, **_kwargs: {},
			knowledge_boundary_event_level=lambda _payload: "info",
			append_knowledge_boundary_observability=lambda *_args, **_kwargs: None,
			build_grounded_turn_context=lambda **_kwargs: _GroundedTurnContext(),
			build_audit_envelope=lambda **_kwargs: _DummyContract({"type": "qwen_audit"}),
			save_session=lambda *_args, **_kwargs: None,
			store_pending_clarification_signal=lambda *_args, **_kwargs: None,
			clear_pending_clarification_signal=lambda *_args, **_kwargs: None,
		)

		self.assertTrue(ok)
		self.assertEqual(payload.get("mode"), "compiled_first_turn")
		assistant_messages = [content for role, content in messages if role == "assistant"]
		self.assertEqual(len(assistant_messages), 1)
		self.assertIn("Customer list result", assistant_messages[0])
		self.assertIn('If you\'d like, I can show Supplier list next. Just say "continue".', assistant_messages[0])
		advanced_payload = next(
			item for item in tool_payloads if item.get("type") == "qwen_compound_request_assessment_contract"
		)
		self.assertEqual(advanced_payload.get("status"), "ordered_execution_ready")
		self.assertEqual(
			(advanced_payload.get("internal_details") or {}).get("primary_segment_message"),
			"give me some supplier list",
		)
		multi_step_assessment = (advanced_payload.get("internal_details") or {}).get("multi_step_assessment") or {}
		self.assertEqual(multi_step_assessment.get("current_step_id"), "step_2")
		self.assertEqual(multi_step_assessment.get("remaining_step_ids"), [])
		self.assertEqual(multi_step_assessment.get("completed_step_ids"), ["step_1"])
		multi_step_execution_plan = (advanced_payload.get("internal_details") or {}).get("multi_step_execution_plan") or {}
		self.assertEqual(multi_step_execution_plan.get("type"), "qwen_multi_step_execution_plan_contract")
		self.assertEqual(multi_step_execution_plan.get("entry_step_id"), "step_1")
		self.assertEqual(
			((multi_step_execution_plan.get("steps") or [{}, {}])[1]).get("step_id"),
			"step_2",
		)
		multi_step_execution_state = (advanced_payload.get("internal_details") or {}).get("multi_step_execution_state") or {}
		self.assertEqual(multi_step_execution_state.get("type"), "qwen_multi_step_execution_state_contract")
		self.assertEqual(multi_step_execution_state.get("state"), "ready")
		self.assertEqual(multi_step_execution_state.get("current_step_id"), "step_2")
		self.assertEqual(multi_step_execution_state.get("last_completed_step_id"), "step_1")
		step_result_integration = next(
			item for item in tool_payloads if item.get("type") == "qwen_multi_step_step_result_integration_contract"
		)
		self.assertEqual(step_result_integration.get("source_step_id"), "step_1")
		self.assertTrue(bool(step_result_integration.get("update_recent_focus")))
		self.assertEqual(
			(step_result_integration.get("result_handle") or {}).get("artifact_family_id"),
			"master_data_directory",
		)

	def test_handle_compiled_first_turn_result_pauses_current_step_when_result_is_clarification(self):
		messages = []
		tool_payloads = []
		pending_signals = []
		cleared_pending = []
		session_doc = object()
		compound_assessment = build_compound_request_assessment_contract(
			request_id="compound-clarify",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			suggested_options=["Payment entries", "Supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details=compound_request_internal_details_with_multi_step_bridge(
				request_id="compound-clarify",
				status="ordered_execution_ready",
				segments=["show me payment entries", "give me some supplier list"],
				suggested_options=["Payment entries", "Supplier list"],
				internal_details={
					"continuation_lane": "front_door",
					"execution_strategy": "ordered_multi_step",
					"primary_segment_message": "show me payment entries",
					"primary_segment_label": "Payment entries",
					"primary_segment_payload": {
						"segment_message": "show me payment entries",
						"segment_label": "Payment entries",
						"interpretation_source": "deterministic_surface",
					},
					"remaining_segment_messages": ["give me some supplier list"],
					"remaining_segment_labels": ["Supplier list"],
					"remaining_segment_payloads": [
						{
							"segment_message": "give me some supplier list",
							"segment_label": "Supplier list",
							"interpretation_source": "deterministic_surface",
						}
					],
					"segment_execution_payloads": [
						{
							"segment_message": "show me payment entries",
							"segment_label": "Payment entries",
							"interpretation_source": "deterministic_surface",
						},
						{
							"segment_message": "give me some supplier list",
							"segment_label": "Supplier list",
							"interpretation_source": "deterministic_surface",
						},
					],
				},
			),
		)
		frontdoor_contract = build_front_door_intent_gate_contract(
			request_id="compound-clarify",
			intent_class="route_onward",
			confidence=1.0,
			grounded_context_available=False,
			reason="Ordered multi-step request.",
			response_payload_override={
				"compound_request_assessment": compound_assessment.to_payload(),
			},
		)
		interaction_contract = build_interaction_contract(
			request_id="compound-clarify",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			raw_message="show me payment entries then give me some supplier list",
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="compound-clarify",
			mode="capability_requery",
			requested_modes=[],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=False,
			reason="fresh query",
		)
		execution_path = ExecutionPath(
			request_id="compound-clarify",
			path="runtime",
			reason="runtime",
			requires_runtime=True,
			grounded_required=False,
		)
		result = {
			"runtime_payload": {
				"ok": True,
				"answer_text": "",
				"tool_trace": [],
				"agent_meta": {},
			},
			"family_validation": {"status": "pass"},
			"semantic_intent_validation": {"status": "pass"},
			"phase4_latency_breakdown": {},
			"compiled_execution_audit": {},
			"pipeline": {},
			"normalized_family_artifact": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "transaction_listing",
				"artifact_type": "normalized_family_artifact",
			},
		}

		ok, payload = handle_compiled_first_turn_result(
			session_doc=session_doc,
			request_id="compound-clarify",
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			result=result,
			governed_scope_contract=None,
			front_door_contract=frontdoor_contract,
			clarification_response_contract=None,
			pre_result_tool_payloads=[],
			append_compiled_attempt_artifacts=lambda *_args, **_kwargs: None,
			compiled_decision_message=lambda **_kwargs: (
				"Which one would you like?",
				{
					"type": "qwen_clarification_signal_contract",
					"request_id": "compound-clarify",
					"user_question": "Which one would you like?",
					"options": ["Payment entries"],
				},
			),
			compiled_clarification_reason_contract=lambda **_kwargs: _DummyContract(
				{"type": "qwen_clarification_reason_contract"}
			),
			append_message=lambda _doc, role, content: messages.append((role, content)),
			append_tool_payload=lambda _doc, payload: tool_payloads.append(dict(payload)),
			assistant_text_payload=lambda text: text,
			tool_trace_message=lambda **_kwargs: "",
			latest_qwen_trace_payload=lambda _doc: {},
			latest_assistant_payload=lambda _doc: {"text": messages[-1][1] if messages else ""},
			append_knowledge_boundary_contract=lambda *_args, **_kwargs: {},
			knowledge_boundary_event_level=lambda _payload: "info",
			append_knowledge_boundary_observability=lambda *_args, **_kwargs: None,
			build_grounded_turn_context=lambda **_kwargs: None,
			build_audit_envelope=lambda **_kwargs: _DummyContract({"type": "qwen_audit"}),
			save_session=lambda *_args, **_kwargs: None,
			store_pending_clarification_signal=lambda _doc, payload: pending_signals.append(dict(payload)),
			clear_pending_clarification_signal=lambda *_args, **_kwargs: cleared_pending.append(True),
		)

		self.assertTrue(ok)
		self.assertEqual(payload.get("mode"), "compiled_first_turn")
		assistant_messages = [content for role, content in messages if role == "assistant"]
		self.assertEqual(assistant_messages, ["Which one would you like?"])
		self.assertFalse(cleared_pending)
		self.assertEqual(len(pending_signals), 1)
		step_result_integration = next(
			item for item in tool_payloads if item.get("type") == "qwen_multi_step_step_result_integration_contract"
		)
		self.assertEqual(step_result_integration.get("result_kind"), "clarification_signal")
		self.assertFalse(bool(step_result_integration.get("update_recent_focus")))
		updated_payload = next(
			item for item in reversed(tool_payloads) if item.get("type") == "qwen_compound_request_assessment_contract"
		)
		self.assertEqual(updated_payload.get("status"), "ordered_execution_waiting_for_clarification")
		self.assertTrue(bool(updated_payload.get("clarification_required")))
		multi_step_assessment = (updated_payload.get("internal_details") or {}).get("multi_step_assessment") or {}
		self.assertEqual(multi_step_assessment.get("current_step_id"), "step_1")
		self.assertEqual(multi_step_assessment.get("remaining_step_ids"), ["step_2"])
		multi_step_execution_state = (updated_payload.get("internal_details") or {}).get("multi_step_execution_state") or {}
		self.assertEqual(multi_step_execution_state.get("state"), "waiting_for_clarification")
		self.assertEqual(multi_step_execution_state.get("waiting_step_id"), "step_1")

	def test_compiled_decision_message_prefers_rendered_answer_for_transaction_listing(self):
		answer_text, clarification_payload = compiled_decision_message(
			request_id="compiled-rendered-1",
			raw_message="show me payment entries",
			result={
				"pipeline": {"fresh_query_compiler": {"decision": "execute"}},
				"normalized_family_artifact": {"family_id": "transaction_listing"},
				"rendered_response": {
					"family_id": "transaction_listing",
					"answer_text": "Rendered listing answer",
				},
				"narrative_response": {
					"family_id": "transaction_listing",
					"answer_text": "Narrative rewritten listing answer",
				},
				"family_validation": {"status": "pass"},
				"semantic_intent_validation": {"status": "pass"},
				"runtime_payload": {"ok": True, "answer_text": "Runtime answer"},
			},
			build_known_unsupported_scope_decision_input=lambda **_kwargs: None,
			translate_clarification_signal=lambda **_kwargs: None,
			out_of_scope_answer=lambda *_args, **_kwargs: "out of scope",
			is_generic_compiled_failure_answer=lambda *_args, **_kwargs: False,
			safe_runtime_failure_message=lambda exc: str(exc),
		)
		self.assertEqual(answer_text, "Rendered listing answer")
		self.assertEqual(clarification_payload, {})

	def test_compiled_decision_message_keeps_narrative_for_non_listing_family(self):
		answer_text, clarification_payload = compiled_decision_message(
			request_id="compiled-rendered-2",
			raw_message="show top customers by revenue",
			result={
				"pipeline": {"fresh_query_compiler": {"decision": "execute"}},
				"normalized_family_artifact": {"family_id": "ranking_analytics"},
				"rendered_response": {
					"family_id": "ranking_analytics",
					"answer_text": "Rendered ranking answer",
				},
				"narrative_response": {
					"family_id": "ranking_analytics",
					"answer_text": "Narrative ranking answer",
				},
				"family_validation": {"status": "pass"},
				"semantic_intent_validation": {"status": "pass"},
				"runtime_payload": {"ok": True, "answer_text": "Runtime answer"},
			},
			build_known_unsupported_scope_decision_input=lambda **_kwargs: None,
			translate_clarification_signal=lambda **_kwargs: None,
			out_of_scope_answer=lambda *_args, **_kwargs: "out of scope",
			is_generic_compiled_failure_answer=lambda *_args, **_kwargs: False,
			safe_runtime_failure_message=lambda exc: str(exc),
		)
		self.assertEqual(answer_text, "Narrative ranking answer")
		self.assertEqual(clarification_payload, {})

	def test_compiled_decision_message_clarify_payload_preserves_canonical_capability_candidates(self):
		from ai_assistant_ui.qwen_chat.clarification_translation import _translate_compiler_signal

		answer_text, clarification_payload = compiled_decision_message(
			request_id="compiled-clarify-identity",
			raw_message="show me payment entries",
			result={
				"pipeline": {
					"fresh_query_compiler": {
						"decision": "clarify",
						"compiler_reason": "Need confirmation before running the listing.",
						"clarification_reason_type": "capability_ambiguity",
						"clarification_details": {
							"capability_candidates": ["collections_read"],
							"canonical_capability_candidates": ["payment_entry_read"],
							"report_candidates": ["Payment Entry List"],
							"scope_id": "payment_entry",
						},
					}
				},
				"family_validation": {"status": "pass"},
				"semantic_intent_validation": {"status": "pass"},
				"runtime_payload": {"ok": True, "answer_text": ""},
			},
			build_known_unsupported_scope_decision_input=lambda **_kwargs: None,
			translate_clarification_signal=lambda **kwargs: _translate_compiler_signal(
				request_id=kwargs["request_id"],
				compiler_reason=kwargs["compiler_reason"],
				compiler_reason_type=kwargs["compiler_reason_type"],
				compiler_details=kwargs["compiler_details"],
			),
			out_of_scope_answer=lambda *_args, **_kwargs: "out of scope",
			is_generic_compiled_failure_answer=lambda *_args, **_kwargs: False,
			safe_runtime_failure_message=lambda exc: str(exc),
		)
		self.assertTrue(answer_text)
		self.assertEqual(clarification_payload.get("candidate_capability_ids"), ["collections_read"])
		self.assertEqual(clarification_payload.get("canonical_candidate_capability_ids"), ["payment_entry_read"])


if __name__ == "__main__":
	unittest.main()
