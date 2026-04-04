import sys
import types
import unittest
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2026",
				"year_start_date": "2026-01-01",
				"year_end_date": "2026-12-31",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.clarification_translation import _translate_compiler_signal
from ai_assistant_ui.qwen_chat.contracts import (
	build_compiled_query_request_contract,
	build_composite_read_plan_contract,
	build_followup_boundary_contract,
	build_followup_resolution_contract,
	build_fresh_query_compiler_contract,
	build_fresh_query_interpretation_contract,
	build_followup_resolution,
)
from ai_assistant_ui.qwen_chat.composite_reads import (
	CompositePlanOutcome,
	execute_composite_read_plan,
	plan_composite_read,
)
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	FrontDoorRenderResult,
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
)
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_tool_surface import build_family_tool_surface_for_message
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_allow_deterministic_family_surface_fallback,
	_apply_governed_interpretation_biases,
	_build_interpretation_context,
	SemanticFreshQueryResult,
	compile_from_fresh_query_message,
	execute_compiled_fresh_query_message,
	_deterministic_family_surface_interpretation,
	_validate_semantic_payload,
)
from ai_assistant_ui.qwen_chat.semantic_interpreter import (
	_build_interpretation_context as _build_semantic_followup_context,
	_validate_semantic_payload as _validate_semantic_followup_payload,
)
from ai_assistant_ui.qwen_chat import followup_interpreter as followup_interpreter_module
from ai_assistant_ui.qwen_chat.followup_interpreter import assess_context_isolation
from ai_assistant_ui.qwen_chat.continuation_support import authoritative_continuation_resolution
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report
from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import (
	_legacy_runtime_family_tool_surface_allowed,
	handle_legacy_runtime_turn,
)
from ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane import handle_runtime_gate_turn
from ai_assistant_ui.qwen_chat.requery_message_support import (
	compile_capability_requery_message,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import (
	semantic_resolution_governs_intent,
	semantic_resolution_intent_classes,
)
from ai_assistant_ui.qwen_chat.semantic_resolution import (
	resolve_aging_analysis_interpretation,
	resolve_financial_summary_interpretation,
	resolve_financial_statement_interpretation,
	resolve_inventory_summary_interpretation,
	resolve_product_performance_interpretation,
	resolve_ranked_entities_interpretation,
	resolve_trend_analysis_interpretation,
	resolve_transaction_listing_interpretation,
)
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import evaluate_frontdoor_lane


class TestSemanticFinancialResolution(unittest.TestCase):
	def test_evaluate_frontdoor_lane_preserves_non_business_frontdoor_intent_despite_reasoning_acceptance(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="low_signal_non_business",
					confidence=0.98,
					reason="The turn asks for creative writing rather than an ERP question.",
				),
				confidence_threshold=0.8,
			),
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.render_front_door_answer",
			return_value=FrontDoorRenderResult(
				ok=True,
				answer_text="I’m ready when you want to continue with an ERP question or follow-up.",
			),
		):
			frontdoor_semantic_result, frontdoor_contract, _render_result, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-reasoning-creative",
				session_id="session-creative",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="write a short poem about this",
				recent_messages=[],
				grounded_context_available=True,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=types.SimpleNamespace(
					status="accepted",
					intent=types.SimpleNamespace(reasoning_type="continuation_detail", confidence=0.96),
				),
			)
		self.assertEqual(frontdoor_semantic_result.status, "accepted")
		self.assertEqual(frontdoor_contract.intent_class, "low_signal_non_business")
		self.assertTrue(frontdoor_contract.handle_in_front_door)
		self.assertIn("ERP question", frontdoor_answer)

	def test_evaluate_frontdoor_lane_keeps_reasoning_route_onward_when_frontdoor_would_route_onward(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=0.91,
					reason="This is a governed ERP follow-up and should continue through the main lanes.",
				),
				confidence_threshold=0.8,
			),
		):
			frontdoor_semantic_result, frontdoor_contract, _render_result, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-reasoning-route-onward",
				session_id="session-route",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="what does this mean",
				recent_messages=[],
				grounded_context_available=True,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=types.SimpleNamespace(
					status="accepted",
					intent=types.SimpleNamespace(reasoning_type="continuation_detail", confidence=0.96),
				),
			)
		self.assertEqual(frontdoor_semantic_result.status, "guardrailed_to_route_onward")
		self.assertEqual(frontdoor_contract.intent_class, "route_onward")
		self.assertFalse(frontdoor_contract.handle_in_front_door)
		self.assertEqual(frontdoor_answer, "")

	def test_runtime_gate_honors_governed_uncovered_scope_without_new_query_mode(self):
		appended_messages = []
		appended_tools = []
		boundary_contracts = []

		def _append_message(_session_doc, role, content):
			appended_messages.append((role, content))

		def _append_tool_payload(_session_doc, payload):
			appended_tools.append(payload)

		def _append_knowledge_boundary_contract(_session_doc, **kwargs):
			boundary_contracts.append(kwargs)
			return {
				"type": "qwen_knowledge_boundary_contract",
				"final_lane": "valid_erp_domain_uncovered",
				"knowledge_coverage_state": "valid_erp_domain_uncovered",
				"user_response_mode": "coverage_gap_explanation",
				"grounding_required": True,
				"grounding_available": False,
			}

		ok, payload, compiled_fallback = handle_runtime_gate_turn(
			session_doc=object(),
			request_id="runtime-gate-1",
			session_id="session-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show employee headcount by department",
			raw_message="show employee headcount by department",
			latest_grounded_turn_available=True,
			latest_grounded_turn={"grounded": True, "source_name": "Sales Analytics"},
			followup_resolution=types.SimpleNamespace(mode="grounded_follow_up", target_limit=0),
			execution_path=types.SimpleNamespace(path="artifact_lane"),
			interaction_contract=types.SimpleNamespace(
				request_id="runtime-gate-1",
				session_id="session-1",
			),
			frontdoor_contract=types.SimpleNamespace(to_payload=lambda: {}),
			clarification_response_contract=None,
			scope_decision_contract=types.SimpleNamespace(
				governed_scope_status="out_of_scope_but_valid_erp_domain",
				requested_domains=["employee"],
				context_domains=["sales"],
				primary_domain="hr",
				reason="HR is a valid ERP domain but not covered.",
				out_of_scope=True,
			),
			compiled_rollout={"enabled": False},
			append_tool_payload=_append_tool_payload,
			append_message=_append_message,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			append_knowledge_boundary_observability=lambda *_args, **_kwargs: None,
			append_compiled_attempt_artifacts=lambda *_args, **_kwargs: None,
			compiled_rollout_fallback_eligible=lambda *_args, **_kwargs: False,
			compiled_rollout_fallback_reason=lambda *_args, **_kwargs: "",
			compiled_rollout_fallback_payload=lambda **_kwargs: {},
			handle_compiled_first_turn_result=lambda **_kwargs: (True, {}),
			out_of_scope_answer=lambda _message, _decision: "I don't have governed HR or headcount coverage yet.",
			assistant_text_payload=lambda text: text,
			save_session=lambda *_args, **_kwargs: None,
		)

		self.assertTrue(ok)
		self.assertEqual(payload["mode"], "known_unsupported_erp_domain")
		self.assertIsNone(compiled_fallback)
		self.assertEqual(boundary_contracts[-1]["governed_scope_contract"]["governed_scope_status"], "out_of_scope_but_valid_erp_domain")
		self.assertEqual(boundary_contracts[-1]["governed_scope_contract"]["primary_domain"], "hr")
		self.assertIn("headcount coverage", appended_messages[-1][1])

	def test_artifact_context_signal_uses_governed_metadata_domains(self):
		signal = followup_interpreter_module._artifact_context_signal(
			{
				"grounded": True,
				"source_name": "Accounts Receivable Summary",
				"artifact_family_id": "aging_analysis",
				"dimensions": ["Customer"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Customer", "Outstanding Amount"],
			}
		)
		self.assertIn("receivable", signal.context_concepts)

	def test_semantic_followup_context_exposes_grounded_scope_hints(self):
		context = _build_semantic_followup_context(
			latest_grounded_turn={
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"row_count": 5,
			},
			latest_assistant_payload={"title": "Working Capital Health"},
		)
		self.assertEqual(context.get("source_report_name"), "AR / AP Working Capital Health")
		self.assertEqual(context.get("source_family_id"), "composite_working_capital_health")
		self.assertEqual(
			context.get("latest_grounded_source_reports"),
			["Accounts Receivable Summary", "Accounts Payable Summary"],
		)
		self.assertFalse(context.get("grounded_followup_supported"))
		self.assertIsInstance(context.get("source_semantic_tags"), list)

	def test_semantic_followup_column_projection_reason_restores_missing_qty_metric(self):
		intent = _validate_semantic_followup_payload(
			payload={
				"requested_modes": ["column_projection"],
				"target_dimension": "Item",
				"target_limit": 7,
				"sort_direction": "desc",
				"target_metric": "",
				"requested_columns": [],
				"confidence": 0.95,
				"reason": "User requested to include the 'qty' column.",
			},
			context={
				"approved_follow_up_modes": ["column_projection", "column_refinement", "sort_or_limit"],
				"available_dimensions": ["Item"],
				"available_metrics": ["Sales Amount", "Quantity"],
				"available_sibling_capabilities": [],
			},
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.target_metric, "quantity")
		self.assertEqual(intent.requested_columns, ["quantity"])

	def test_semantic_followup_sort_limit_drops_unowned_structured_fields(self):
		intent = _validate_semantic_followup_payload(
			payload={
				"requested_modes": ["sort_or_limit"],
				"target_dimension": "Customer",
				"target_limit": 3,
				"sort_direction": "desc",
				"target_metric": "quantity",
				"requested_columns": ["customer", "quantity"],
				"requested_time_scope": "March 2026",
				"confidence": 0.95,
				"reason": "User requested to limit the result to top 3.",
			},
			context={
				"approved_follow_up_modes": ["sort_or_limit", "column_projection", "column_refinement", "time_scope_restatement"],
				"available_dimensions": ["Customer"],
				"available_metrics": ["Quantity"],
				"available_sibling_capabilities": [],
			},
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.target_limit, 3)
		self.assertEqual(intent.sort_direction, "desc")
		self.assertEqual(intent.target_metric, "quantity")
		self.assertEqual(intent.requested_columns, [])
		self.assertEqual(intent.requested_time_scope, "")

	def test_semantic_followup_rejects_predictive_guarantee_prompt_even_if_runtime_suggests_breakdown(self):
		intent = _validate_semantic_followup_payload(
			payload={
				"requested_modes": ["dimension_breakdown"],
				"target_dimension": "Customer",
				"target_limit": 5,
				"sort_direction": "desc",
				"target_metric": "outstanding amount",
				"requested_columns": [],
				"requested_time_scope": "",
				"confidence": 0.9,
				"reason": "User is asking for customers who will pay this week, which requires a breakdown of customers by their outstanding amounts.",
			},
			context={
				"approved_follow_up_modes": ["dimension_breakdown", "sort_or_limit"],
				"available_dimensions": ["Customer"],
				"available_metrics": ["Outstanding Amount"],
				"available_sibling_capabilities": [],
			},
			message="guarantee which customer will pay this week",
		)
		self.assertIsNone(intent)

	def test_build_followup_resolution_does_not_backfill_from_message_after_semantic_acceptance(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["sort_or_limit"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="Accepted governed semantic follow-up intent.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-no-lexical-backfill",
			message="show only top 5",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "grounded_follow_up")
		self.assertEqual(outcome.target_limit, 0)
		self.assertEqual(outcome.sort_direction, "")

	def test_build_followup_resolution_no_longer_uses_lexical_parser_when_heuristic_flag_is_true(self):
		outcome = build_followup_resolution(
			request_id="no-lexical-followup-fallback",
			message="show top 5 only",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=None,
			allow_heuristic_fallback=True,
		)
		self.assertEqual(outcome.mode, "grounded_follow_up")
		self.assertEqual(outcome.target_limit, 0)
		self.assertEqual(outcome.requested_modes, [])

	def test_build_followup_boundary_contract_normalizes_and_serializes(self):
		contract = build_followup_boundary_contract(
			request_id="followup-boundary-1",
			session_id="session-1",
			source_family_id=" ranking_analytics ",
			source_report_name=" Sales Analytics ",
			grounded_context_domains=["sales", "sales", "customer", ""],
			requested_domains=["receivable", "receivable", ""],
			structured_followup_modes=["sort_or_limit", "sort_or_limit", ""],
			structured_business_signals_present=True,
			grounded_followup_supported=True,
			self_contained_signal=False,
			contradictory_payload=False,
			out_of_scope_signal=False,
			primary_domain=" finance ",
			domain_affinity="partial_overlap",
			recommended_boundary_decision="stay_grounded",
			decision_reason="Structured semantic follow-up stays within the governed scope.",
			resolution_source={"requested_domains": "semantic_runtime", "": "ignored"},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["type"], "qwen_followup_boundary_contract")
		self.assertEqual(payload["source_family_id"], "ranking_analytics")
		self.assertEqual(payload["source_report_name"], "Sales Analytics")
		self.assertEqual(payload["grounded_context_domains"], ["sales", "customer"])
		self.assertEqual(payload["requested_domains"], ["receivable"])
		self.assertEqual(payload["structured_followup_modes"], ["sort_or_limit"])
		self.assertFalse(payload["out_of_scope_signal"])
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["primary_domain"], "finance")
		self.assertEqual(payload["domain_affinity"], "partial_overlap")
		self.assertEqual(payload["recommended_boundary_decision"], "stay_grounded")
		self.assertEqual(payload["resolution_source"], {"requested_domains": "semantic_runtime"})

	def test_build_followup_boundary_contract_fails_closed_on_invalid_values(self):
		contract = build_followup_boundary_contract(
			request_id="followup-boundary-2",
			session_id="session-2",
			domain_affinity="totally_new_bucket",
			recommended_boundary_decision="maybe_route",
		)
		payload = contract.to_payload()
		self.assertEqual(payload["domain_affinity"], "unknown")
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")
		self.assertEqual(payload["grounded_context_domains"], [])
		self.assertEqual(payload["requested_domains"], [])
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])

	def test_build_followup_boundary_contract_from_context_uses_structured_semantic_domains(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"anything",
			request_id="followup-boundary-from-context-1",
			session_id="session-ctx-1",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["sibling_switch"],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="accounts_receivable_read",
				self_contained=False,
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], ["customer", "receivable"])
		self.assertEqual(payload["grounded_context_domains"], ["sales"])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "semantic_runtime")
		self.assertEqual(payload["domain_affinity"], "disjoint")
		self.assertEqual(payload["recommended_boundary_decision"], "stay_grounded")

	def test_build_followup_boundary_contract_from_context_fails_closed_without_business_signal(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"what should management do next",
			request_id="followup-boundary-from-context-2",
			session_id="session-ctx-2",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Invoice List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date"],
				"metrics": [],
				"returned_schema": ["Name", "Posting Date", "Customer", "Grand Total"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")
		self.assertEqual(payload["resolution_source"]["requested_domains"], "none")

	def test_build_followup_boundary_contract_from_context_blank_semantic_payload_fails_closed_for_supported_grounded_followup(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			return_value=followup_interpreter_module.MessageSignal(
				text="show ar summary for last month",
				concepts={"receivable"},
			),
		):
			contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
				"show AR summary for last month",
				request_id="followup-boundary-from-context-3",
				session_id="session-ctx-3",
				grounded_turn={
					"grounded": True,
					"source_name": "Sales Analytics",
					"artifact_family_id": "ranking_analytics",
					"dimensions": ["Customer"],
					"metrics": ["Quantity"],
					"returned_schema": ["Customer", "Quantity"],
				},
				semantic_intent=types.SimpleNamespace(self_contained=False),
			)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "semantic_runtime")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")

	def test_build_followup_boundary_contract_from_context_denies_same_domain_message_fallback_for_supported_grounded_followup(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			return_value=followup_interpreter_module.MessageSignal(
				text="show sales summary",
				concepts={"sales"},
			),
		):
			contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
				"show sales summary",
				request_id="followup-boundary-from-context-4",
				session_id="session-ctx-4",
				grounded_turn={
					"grounded": True,
					"source_name": "Sales Analytics",
					"artifact_family_id": "ranking_analytics",
					"dimensions": ["Customer"],
					"metrics": ["Quantity"],
					"returned_schema": ["Customer", "Quantity"],
				},
			)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "message_fallback_denied")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")

	def test_build_followup_boundary_contract_from_context_ignores_non_primary_message_concepts(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			return_value=followup_interpreter_module.MessageSignal(
				text="show customer summary",
				concepts={"customer"},
			),
		):
			contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
				"show customer summary",
				request_id="followup-boundary-from-context-4b",
				session_id="session-ctx-4b",
				grounded_turn={
					"grounded": True,
					"source_name": "Sales Analytics",
					"artifact_family_id": "ranking_analytics",
					"dimensions": ["Customer"],
					"metrics": ["Quantity"],
					"returned_schema": ["Customer", "Quantity"],
				},
			)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "none")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")

	def test_build_followup_boundary_contract_from_context_does_not_use_message_fallback_when_semantic_modes_are_present(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			return_value=followup_interpreter_module.MessageSignal(
				text="show ar summary",
				concepts={"receivable"},
			),
		):
			contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
				"show AR summary",
				request_id="followup-boundary-from-context-4c",
				session_id="session-ctx-4c",
				grounded_turn={
					"grounded": True,
					"source_name": "Sales Analytics",
					"artifact_family_id": "ranking_analytics",
					"dimensions": ["Customer"],
					"metrics": ["Quantity"],
					"returned_schema": ["Customer", "Quantity"],
				},
				semantic_intent=types.SimpleNamespace(
					requested_modes=["presentation_transform"],
					target_dimension="",
					target_limit=0,
					sort_direction="",
					target_metric="",
					requested_columns=[],
					requested_time_scope="",
					target_capability_id="",
					self_contained=False,
				),
			)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "semantic_runtime")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")

	def test_build_followup_boundary_contract_from_context_uses_known_uncovered_scope_for_hr(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"employee headcount",
			request_id="followup-boundary-from-context-5",
			session_id="session-ctx-5",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], ["employee"])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "known_uncovered_scope")
		self.assertTrue(payload["out_of_scope_signal"])
		self.assertEqual(payload["primary_domain"], "hr")
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

	def test_build_followup_boundary_contract_from_context_uses_known_uncovered_scope_even_when_semantic_payload_is_present_but_blank(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"employee headcount",
			request_id="followup-boundary-from-context-6",
			session_id="session-ctx-6",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], ["employee"])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "known_uncovered_scope")
		self.assertTrue(payload["out_of_scope_signal"])
		self.assertEqual(payload["primary_domain"], "hr")

	def test_build_followup_boundary_contract_from_context_blank_semantic_payload_denies_single_disjoint_domain_fallback_on_unsupported_artifact(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"give me sales insight",
			request_id="followup-boundary-from-context-6b",
			session_id="session-ctx-6b",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "message_fallback_denied")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "fail_closed_to_reasoning")

	def test_build_followup_boundary_contract_from_context_allows_multi_domain_message_fallback_on_unsupported_artifact_without_semantic_payload(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"give me AR / AP insight",
			request_id="followup-boundary-from-context-6c",
			session_id="session-ctx-6c",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], ["payable", "receivable"])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "message_fallback")
		self.assertTrue(payload["degraded_message_fallback_allowed"])
		self.assertTrue(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

	def test_build_followup_boundary_contract_from_context_allows_contradictory_presentation_payload_to_use_bounded_message_fallback(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"give me AR insight",
			request_id="followup-boundary-from-context-6d",
			session_id="session-ctx-6d",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=7,
				sort_direction="desc",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["requested_domains"], ["receivable"])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "degraded_semantic_message_fallback")
		self.assertTrue(payload["degraded_message_fallback_allowed"])
		self.assertTrue(payload["degraded_message_fallback_used"])
		self.assertTrue(payload["contradictory_payload"])
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

	def test_evaluate_followup_boundary_contract_forces_new_query(self):
		decision = followup_interpreter_module.evaluate_followup_boundary_contract(
			build_followup_boundary_contract(
				request_id="followup-boundary-eval-1",
				session_id="session-eval-1",
				grounded_context_domains=["sales"],
				requested_domains=["receivable"],
				recommended_boundary_decision="force_fresh_query",
				decision_reason="The request is self-contained and should be treated as a fresh governed ERP question.",
			)
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertEqual(decision.requested_domains, ["receivable"])
		self.assertEqual(decision.context_domains, ["sales"])

	def test_evaluate_followup_boundary_contract_fails_closed_to_non_breakout(self):
		decision = followup_interpreter_module.evaluate_followup_boundary_contract(
			build_followup_boundary_contract(
				request_id="followup-boundary-eval-2",
				session_id="session-eval-2",
				recommended_boundary_decision="fail_closed_to_reasoning",
				decision_reason="Should not be used for breakout.",
			)
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertEqual(decision.reason, "")

	def test_evaluate_followup_boundary_contract_preserves_known_uncovered_scope(self):
		decision = followup_interpreter_module.evaluate_followup_boundary_contract(
			build_followup_boundary_contract(
				request_id="followup-boundary-eval-3",
				session_id="session-eval-3",
				requested_domains=["employee"],
				out_of_scope_signal=True,
				primary_domain="hr",
				recommended_boundary_decision="force_fresh_query",
				decision_reason="The request targets a valid ERP business area that is not yet covered by the current governed assistant.",
			)
		)
		self.assertTrue(decision.force_new_query)
		self.assertTrue(decision.out_of_scope)
		self.assertEqual(decision.primary_domain, "hr")
		self.assertEqual(decision.requested_domains, ["employee"])

	def test_context_isolation_no_longer_uses_lexical_dimension_breakdown_exception(self):
		decision = assess_context_isolation(
			"break this down by warehouse",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("different governed business area", decision.reason)

	def test_assess_context_isolation_marks_self_contained_request_as_new_query(self):
		result = assess_context_isolation(
			"show AR summary for last month",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertTrue(
			"different governed business area" in result.reason
			or "self-contained" in result.reason
		)

	def test_assess_context_isolation_treats_repeated_self_contained_business_request_as_new_query(self):
		result = assess_context_isolation(
			"give me AR / AP insight",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("self-contained", result.reason)

	def test_assess_context_isolation_breaks_out_without_prefix_registry_when_grounded_followups_are_unsupported(self):
		result = assess_context_isolation(
			"give me AR / AP insight",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertIn("self-contained", result.reason)

	def test_assess_context_isolation_normalizes_slash_separated_ar_ap_domain_signal(self):
		result = assess_context_isolation(
			"give me AR / AP insight",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Invoice List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Invoice"],
				"metrics": ["Grand Total"],
				"returned_schema": ["Invoice", "Grand Total"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertTrue(
			"different governed business area" in result.reason
			or "self-contained" in result.reason
		)

	def test_assess_context_isolation_does_not_use_prefix_only_to_break_grounded_reasoning(self):
		result = assess_context_isolation(
			"what should management do next",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Invoice List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date"],
				"metrics": [],
				"returned_schema": ["Name", "Posting Date", "Customer", "Grand Total"],
			},
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_ignores_unstructured_semantic_self_contained_flag(self):
		result = assess_context_isolation(
			"what should management do next",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Invoice List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date"],
				"metrics": [],
				"returned_schema": ["Name", "Posting Date", "Customer", "Grand Total"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=True,
			),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_presentation_only_semantic_payload_does_not_block_domain_shift_breakout(self):
		result = assess_context_isolation(
			"give me AR insight",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=7,
				sort_direction="desc",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertTrue(
			"different governed business area" in result.reason
			or "self-contained" in result.reason
		)

	def test_assess_context_isolation_uses_semantic_reason_domains_before_artifact_fallback(self):
		result = assess_context_isolation(
			"give me AR insight",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=7,
				sort_direction="desc",
				target_metric="quantity",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User asked for AR insight, which implies a shift to accounts receivable data.",
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("different governed business area", result.reason)

	def test_assess_context_isolation_contradictory_presentation_payload_breaks_out_as_fresh_query(self):
		result = assess_context_isolation(
			"give me AR insight",
			grounded_turn={
				"grounded": True,
				"source_name": "Accounts Receivable Summary",
				"artifact_family_id": "aging_analysis",
				"dimensions": ["Customer"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Customer", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=10,
				sort_direction="desc",
				target_metric="outstanding",
				requested_columns=["customer", "outstanding amount"],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("conflicting query fields", result.reason)

	def test_assess_context_isolation_same_domain_contradictory_presentation_payload_stays_grounded(self):
		result = assess_context_isolation(
			"Please keep the exact same top 7 customer ranking by quantity, add serial number next to each row.",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=7,
				sort_direction="desc",
				target_metric="quantity",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User requested a top 7 customer ranking with serial numbers, which aligns with the existing grounded result.",
			),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_marks_semantic_creative_presentation_request_out_of_scope(self):
		result = assess_context_isolation(
			"write a short poem about this",
			grounded_turn={
				"grounded": True,
				"source_name": "Accounts Receivable Summary",
				"artifact_family_id": "aging_analysis",
				"dimensions": ["Customer"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Customer", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["presentation_transform"],
				target_dimension="Customer",
				target_limit=5,
				sort_direction="desc",
				target_metric="outstanding",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User requested a short poem about the AR insight, which is a creative follow-up.",
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertTrue(result.out_of_scope)
		self.assertIn("creative content generation", result.reason)

	def test_assess_context_isolation_marks_creative_reasoning_reframing_out_of_scope(self):
		result = assess_context_isolation(
			"write a short poem about this",
			grounded_turn={
				"grounded": True,
				"source_name": "Accounts Receivable Summary",
				"artifact_family_id": "aging_analysis",
				"dimensions": ["Customer"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Customer", "Outstanding Amount"],
			},
			reasoning_semantic_result=types.SimpleNamespace(
				status="accepted",
				intent=types.SimpleNamespace(
					reasoning_type="interpretation",
					reason="User asks for a creative reframing of the same grounded ERP facts rather than a governed business follow-up.",
				),
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertTrue(result.out_of_scope)
		self.assertIn("creative content generation", result.reason)

	def test_assess_context_isolation_uses_structured_domains_without_message_concepts(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			return_value=followup_interpreter_module.MessageSignal(text="give me AR insight", concepts=set()),
		):
			result = assess_context_isolation(
				"give me AR insight",
				grounded_turn={
					"grounded": True,
					"source_name": "AR / AP Working Capital Health",
					"artifact_family_id": "composite_working_capital_health",
					"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
					"dimensions": [],
					"metrics": ["Outstanding Amount"],
					"returned_schema": ["Party", "Outstanding Amount"],
				},
				semantic_intent=types.SimpleNamespace(
					requested_modes=["presentation_transform"],
					target_dimension="",
					target_limit=0,
					sort_direction="",
					target_metric="outstanding",
					requested_columns=["outstanding"],
					requested_time_scope="",
					target_capability_id="",
					self_contained=False,
				),
			)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("conflicting query fields", result.reason)

	def test_assess_context_isolation_skips_message_signal_when_capability_domains_are_structured(self):
		with patch.object(
			followup_interpreter_module,
			"_message_signal",
			side_effect=AssertionError("message signal should not be consulted when semantic domains are structured"),
		):
			result = assess_context_isolation(
				"anything",
				grounded_turn={
					"grounded": True,
					"source_name": "Sales Analytics",
					"artifact_family_id": "ranking_analytics",
					"dimensions": ["Customer"],
					"metrics": ["Quantity"],
					"returned_schema": ["Customer", "Quantity"],
				},
				semantic_intent=types.SimpleNamespace(
					requested_modes=["sibling_switch"],
					target_dimension="",
					target_limit=0,
					sort_direction="",
					target_metric="",
					requested_columns=[],
					requested_time_scope="",
					target_capability_id="accounts_receivable_read",
					self_contained=False,
				),
			)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_no_longer_uses_followup_mode_detection(self):
		self.assertFalse(hasattr(followup_interpreter_module, "ontology_detect_followup_modes"))
		result = assess_context_isolation(
			"show AR summary for last month",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertTrue(result.force_new_query)

	def test_assess_context_isolation_no_longer_uses_time_scope_alias_detection(self):
		self.assertFalse(hasattr(followup_interpreter_module, "ontology_followup_slot_aliases"))
		result = assess_context_isolation(
			"show AR summary for last month",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertTrue(result.force_new_query)

	def test_assess_context_isolation_no_longer_classifies_creative_request(self):
		result = assess_context_isolation(
			"write a poem about sales",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)

	def test_assess_context_isolation_marks_known_uncovered_hr_domain_from_governed_scope_registry(self):
		result = assess_context_isolation(
			"show employee salary summary",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertTrue(result.out_of_scope)
		self.assertEqual(result.primary_domain, "hr")
		self.assertIn("valid ERP business area", result.reason)

	def test_message_signal_ignores_extended_ontology_aliases(self):
		signal = followup_interpreter_module._message_signal("show business health")
		self.assertNotIn("working_capital", signal.concepts)

	def test_assess_context_isolation_blank_semantic_intent_fails_closed_on_supported_grounded_followup(self):
		result = assess_context_isolation(
			"show AR summary for last month",
			grounded_turn={
				"grounded": True,
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"metrics": ["Quantity"],
				"returned_schema": ["Customer", "Quantity"],
			},
			semantic_intent=types.SimpleNamespace(self_contained=False),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_blank_semantic_intent_breaks_out_on_unsupported_grounded_artifact(self):
		result = assess_context_isolation(
			"give me AR / AP insight",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("self-contained", result.reason)

	def test_assess_context_isolation_blank_semantic_intent_does_not_use_single_same_domain_fallback_on_unsupported_artifact(self):
		result = assess_context_isolation(
			"give me AR insight",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_blank_semantic_intent_does_not_promote_customer_guarantee_to_fresh_query(self):
		result = assess_context_isolation(
			"guarantee which customer will pay this week",
			grounded_turn={
				"grounded": True,
				"source_name": "Accounts Receivable Summary",
				"artifact_family_id": "aging_analysis",
				"artifact_source_reports": ["Accounts Receivable Summary"],
				"dimensions": ["Customer"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Customer", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_assess_context_isolation_blank_semantic_intent_does_not_break_out_on_single_disjoint_domain_unsupported_artifact(self):
		result = assess_context_isolation(
			"give me sales insight",
			grounded_turn={
				"grounded": True,
				"source_name": "AR / AP Working Capital Health",
				"artifact_family_id": "composite_working_capital_health",
				"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"dimensions": ["Party Type"],
				"metrics": ["Outstanding Amount"],
				"returned_schema": ["Party Type", "Outstanding Amount"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertFalse(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertEqual(result.reason, "")

	def test_compile_capability_requery_message_preserves_structured_ranking_limit(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="ranking-requery-limit",
			mode="capability_requery",
			requested_modes=["sort_or_limit"],
			target_dimension="",
			target_limit=3,
			sort_direction="desc",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Preserve the governed ranking scope and reduce the row count.",
		)
		continuation_contract = types.SimpleNamespace(
			preserved_dimension="Customer",
			preserved_metric_key="quantity",
			preserved_requested_columns=["entity", "quantity"],
			preserved_limit=3,
			preserved_entities=["Ko Nay Lin Mobile Center", "Capital Telecom (NPT)", "Bayint Naung Wholesale Mobile"],
			preserve_rank_membership=True,
			preserve_rank_order=False,
			preserve_date_context=True,
			source_family_id="ranking_analytics",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="limit this to top 3",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Sales Analytics",
				"filters": {"company": "Enterprise Co"},
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"artifact_family_id": "ranking_analytics",
			},
			continuation_contract=continuation_contract,
		)
		self.assertIn("top 3 customers", message.lower())
		self.assertIn("by quantity", message.lower())

	def test_compile_from_fresh_query_message_preserves_governed_target_limit_seed(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="seeded-target-limit",
			session_id="seeded-target-limit-session",
			intent_class="ranked_entities",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Analytics"],
			requested_dimensions=["Customer"],
			requested_metrics=["Quantity"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
			target_limit=0,
		)
		semantic_result = SemanticFreshQueryResult(
			status="accepted",
			interpretation=interpretation,
			confidence_threshold=0.72,
			agent_meta={"engine": "semantic_runtime"},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=semantic_result,
		):
			pipeline = compile_from_fresh_query_message(
				session_id="seeded-target-limit-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me top customers by quantity",
				recent_messages=[],
				governed_target_limit=3,
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			3,
		)
		self.assertEqual(
			int(((pipeline.get("compiled_query_request") or {}).get("target_limit") or 0)),
			3,
		)

	def test_financial_summary_normalizes_payable_into_aging(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-1",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_payable_read"],
			candidate_reports=["Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "normalize_intent")
		self.assertEqual(outcome.contract.target_intent_class, "aging_analysis")
		self.assertEqual(outcome.interpretation.intent_class, "aging_analysis")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["payable"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "outstanding_amount")

	def test_financial_summary_normalizes_receivable_into_aging(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-receivable",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read"],
			candidate_reports=["Accounts Receivable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "normalize_intent")
		self.assertEqual(outcome.contract.target_intent_class, "aging_analysis")
		self.assertEqual(outcome.interpretation.intent_class, "aging_analysis")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["receivable"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "outstanding_amount")

	def test_financial_summary_normalizes_statement_into_financial_statement(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-statement",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "normalize_intent")
		self.assertEqual(outcome.contract.target_intent_class, "financial_statement")
		self.assertEqual(outcome.interpretation.intent_class, "financial_statement")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["statement"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "statement_view")

	def test_financial_summary_normalizes_inventory_value_snapshot(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-inventory",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=["Stock Balance"],
			requested_dimensions=["Warehouse"],
			requested_metrics=["Balance Value"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.87,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "normalize_intent")
		self.assertEqual(outcome.contract.target_intent_class, "inventory_summary")
		self.assertEqual(outcome.interpretation.intent_class, "inventory_summary")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["inventory"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "value_snapshot")
		self.assertEqual(outcome.contract.resolved_summary_grain, "warehouse")

	def test_financial_summary_normalizes_product_profitability_snapshot(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-product-profitability",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["product_performance_read"],
			candidate_reports=["Gross Profit"],
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.88,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "normalize_intent")
		self.assertEqual(outcome.contract.target_intent_class, "product_performance")
		self.assertEqual(outcome.interpretation.intent_class, "product_performance")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["product_profitability"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "profitability_snapshot")
		self.assertEqual(outcome.contract.resolved_summary_grain, "item")

	def test_financial_summary_executes_working_capital_health_from_structured_profile(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-working-capital",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read", "accounts_payable_read"],
			candidate_reports=["Accounts Receivable Summary", "Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={"composite_profile_context": ["working_capital_health"]},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = resolve_financial_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.decision, "execute_composite")
		self.assertEqual(outcome.contract.target_composite_plan_id, "working_capital_health")
		self.assertEqual(outcome.contract.resolved_summary_domains, ["receivable", "payable"])
		self.assertEqual(outcome.contract.resolved_summary_focus, "cross_domain_health")

	def test_runtime_payload_validation_preserves_governed_composite_profile_context(self):
		context = _build_interpretation_context()
		contract = _validate_semantic_payload(
			request_id="semantic-fin-summary-runtime-slot",
			session_id="semantic-fin-summary",
			payload={
				"intent_class": "financial_summary",
				"candidate_capability_ids": ["accounts_receivable_read", "accounts_payable_read"],
				"candidate_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
				"requested_dimensions": [],
				"requested_metrics": ["Outstanding"],
				"requested_time_scope": "as_of_today",
				"requested_presentation": [],
				"extracted_slots": {
					"composite_profile_context": ["working_capital_health", "unknown_profile"],
				},
				"ambiguity_flags": [],
				"ambiguity_reason": "",
				"confidence": 0.92,
			},
			context=context,
			message="Show me our financial summary",
		)
		self.assertIsNotNone(contract)
		self.assertEqual(
			(contract.extracted_slots or {}).get("composite_profile_context"),
			["working_capital_health"],
		)

	def test_composite_plan_prefers_structured_profile_context_for_financial_summary(self):
		base_interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-composite-plan",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read", "accounts_payable_read"],
			candidate_reports=["Accounts Receivable Summary", "Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={"composite_profile_context": ["working_capital_health"]},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		resolution_outcome = resolve_financial_summary_interpretation(base_interpretation)
		self.assertIsNotNone(resolution_outcome)
		interpretation = resolution_outcome.interpretation
		outcome = plan_composite_read(
			request_id="semantic-fin-summary-composite-plan",
			session_id="semantic-fin-summary",
			message="Show me our financial summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.status, "execute")
		self.assertIsNotNone(outcome.plan_contract)
		self.assertEqual(outcome.plan_contract.plan_id, "working_capital_health")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("decision"),
			"execute_composite",
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("target_composite_plan_id"),
			"working_capital_health",
		)

	def test_compiler_executes_financial_summary_payable_via_normalization(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-2",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_payable_read"],
			candidate_reports=["Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-2",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Accounts Payable Summary")
		self.assertEqual(outcome.compiler_contract.capability_id, "accounts_payable_read")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertIn(
			"semantic_resolution_contract",
			outcome.compiler_contract.governed_resolution_details,
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details["semantic_resolution_contract"].get("decision"),
			"normalize_intent",
		)

	def test_compiler_executes_financial_summary_receivable_via_normalization(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-receivable-compile",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read"],
			candidate_reports=["Accounts Receivable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-receivable-compile",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Accounts Receivable Summary")
		self.assertEqual(outcome.compiler_contract.capability_id, "accounts_receivable_read")

	def test_compiler_executes_financial_summary_statement_via_normalization(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-statement-compile",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-statement-compile",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Profit and Loss Statement")
		self.assertEqual(outcome.compiler_contract.capability_id, "financial_statement_read")

	def test_compiler_executes_financial_summary_inventory_via_normalization(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-inventory-compile",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=["Stock Balance"],
			requested_dimensions=["Warehouse"],
			requested_metrics=["Balance Value"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.87,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-inventory-compile",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Stock Balance")
		self.assertEqual(outcome.compiler_contract.capability_id, "stock_read")

	def test_compiler_executes_financial_summary_product_profitability_via_normalization(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-product-profitability-compile",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["product_performance_read"],
			candidate_reports=["Gross Profit"],
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.88,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-product-profitability-compile",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Gross Profit")
		self.assertEqual(outcome.compiler_contract.capability_id, "product_performance_read")

	def test_financial_summary_clarifies_inventory_focus_when_metric_missing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-3",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=["Stock Balance"],
			requested_dimensions=["Warehouse"],
			requested_metrics=[],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.82,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-3",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "financial_summary_focus_clarification")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertIn(
			"semantic_resolution_contract",
			outcome.compiler_contract.governed_resolution_details,
		)
		self.assertIn("financial_summary_resolution_contract", outcome.compiler_contract.clarification_details)
		self.assertTrue(outcome.compiler_contract.clarification_details.get("blocks_legacy_fallback"))

	def test_compiler_payload_includes_governed_resolution_details_for_execute(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-payload",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-payload",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		payload = outcome.compiler_contract.to_payload()
		self.assertEqual(payload.get("contract_version"), "1.1")
		self.assertEqual(
			payload.get("governed_resolution_details", {}).get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			payload.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("decision"),
			"normalize_intent",
		)

	def test_pipeline_payload_preserves_governed_resolution_details_for_execute(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-pipeline",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=SemanticFreshQueryResult(
				status="ok",
				interpretation=interpretation,
				confidence_threshold=0.72,
				runtime_error="",
				validation_error="",
				agent_meta={},
			),
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-fin-summary",
				user_id="Administrator",
				site_name="test-site",
				message="Show me our financial summary",
				recent_messages=[],
			)
		compiler_payload = pipeline.get("fresh_query_compiler")
		self.assertIsInstance(compiler_payload, dict)
		self.assertEqual(
			compiler_payload.get("governed_resolution_details", {}).get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			compiler_payload.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("governed_decision"),
			"execute",
		)
		self.assertEqual(
			pipeline.get("semantic_resolution_contract", {}).get("decision"),
			"normalize_intent",
		)

	def test_execute_pipeline_routes_structured_financial_summary_into_composite_plan(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-composite-pipeline",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read", "accounts_payable_read"],
			candidate_reports=["Accounts Receivable Summary", "Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={"composite_profile_context": ["working_capital_health"]},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		captured = {}

		def _fake_execute_composite_read_plan(**kwargs):
			captured["pipeline"] = kwargs.get("pipeline")
			captured["plan_outcome"] = kwargs.get("plan_outcome")
			return {
				"pipeline": kwargs.get("pipeline"),
				"compiled_execution_audit": {},
				"rendered_response": {"answer_text": "Working capital looks stable."},
			}

		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=SemanticFreshQueryResult(
				status="ok",
				interpretation=interpretation,
				confidence_threshold=0.72,
				runtime_error="",
				validation_error="",
				agent_meta={},
			),
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.execute_composite_read_plan",
			side_effect=_fake_execute_composite_read_plan,
		) as composite_exec:
			result = execute_compiled_fresh_query_message(
				session_id="semantic-fin-summary",
				user_id="Administrator",
				site_name="test-site",
				message="Show me our financial summary",
				recent_messages=[],
			)

		self.assertTrue(composite_exec.called)
		self.assertIn("pipeline", captured)
		self.assertIn("plan_outcome", captured)
		self.assertEqual(
			captured["pipeline"].get("semantic_resolution_contract", {}).get("decision"),
			"execute_composite",
		)
		self.assertEqual(
			captured["pipeline"].get("semantic_resolution_contract", {}).get("target_composite_plan_id"),
			"working_capital_health",
		)
		self.assertEqual(
			captured["pipeline"].get("fresh_query_compiler", {})
			.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("decision"),
			"execute_composite",
		)
		self.assertEqual(
			captured["plan_outcome"].plan_contract.plan_id,
			"working_capital_health",
		)
		self.assertEqual(
			captured["plan_outcome"].compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("target_composite_plan_id"),
			"working_capital_health",
		)
		self.assertEqual(
			result.get("pipeline", {}).get("fresh_query_compiler", {})
			.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("decision"),
			"execute_composite",
		)

	def test_execute_pipeline_accepts_runtime_produced_composite_profile_context(self):
		captured = {}

		def _fake_execute_composite_read_plan(**kwargs):
			captured["pipeline"] = kwargs.get("pipeline")
			captured["plan_outcome"] = kwargs.get("plan_outcome")
			return {
				"pipeline": kwargs.get("pipeline"),
				"compiled_execution_audit": {},
				"rendered_response": {"answer_text": "Working capital looks stable."},
			}

		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "financial_summary",
					"candidate_capability_ids": ["accounts_receivable_read", "accounts_payable_read"],
					"candidate_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
					"requested_dimensions": [],
					"requested_metrics": ["Outstanding"],
					"requested_time_scope": "as_of_today",
					"requested_presentation": [],
					"extracted_slots": {
						"composite_profile_context": ["working_capital_health"],
					},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 0.92,
				},
				"agent_meta": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.execute_composite_read_plan",
			side_effect=_fake_execute_composite_read_plan,
		) as composite_exec:
			result = execute_compiled_fresh_query_message(
				session_id="semantic-fin-summary",
				user_id="Administrator",
				site_name="test-site",
				message="Show me our financial summary",
				recent_messages=[],
			)

		self.assertTrue(composite_exec.called)
		self.assertEqual(
			captured["pipeline"].get("semantic_resolution_contract", {}).get("decision"),
			"execute_composite",
		)
		self.assertEqual(
			captured["pipeline"].get("semantic_resolution_contract", {}).get("target_composite_plan_id"),
			"working_capital_health",
		)
		self.assertEqual(
			captured["pipeline"].get("fresh_query_interpretation", {})
			.get("interpretation", {})
			.get("extracted_slots", {})
			.get("composite_profile_context"),
			["working_capital_health"],
		)
		self.assertEqual(
			captured["plan_outcome"].plan_contract.plan_id,
			"working_capital_health",
		)
		self.assertEqual(
			result.get("pipeline", {}).get("semantic_resolution_contract", {}).get("decision"),
			"execute_composite",
		)

	def test_execution_audit_preserves_governed_resolution_details_without_runtime(self):
		pipeline = {
			"request_id": "semantic-audit-no-runtime",
			"phase4_latency_breakdown": {
				"proposal_generation_latency_ms": 4,
				"compilation_latency_ms": 2,
			},
			"fresh_query_interpretation": {
				"interpretation": {
					"intent_class": "financial_summary",
				}
			},
			"fresh_query_compiler": {
				"decision": "clarify",
				"compiler_reason": "Governed semantic clarification.",
				"capability_id": "financial_statement_read",
				"selected_report": "Profit and Loss Statement",
				"selected_report_family": "financial_statement",
				"governed_resolution_details": {
					"resolution_mode": "semantic_resolution",
					"semantic_resolution_contract": {
						"type": "qwen_financial_summary_resolution_contract",
						"decision": "normalize_intent",
					},
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.compile_from_fresh_query_message",
			return_value=pipeline,
		):
			execution_result = execute_compiled_fresh_query_message(
				session_id="semantic-audit-session",
				user_id="Administrator",
				site_name="test-site",
				message="Show me our financial summary",
				recent_messages=[],
			)
		audit = execution_result.get("compiled_execution_audit")
		self.assertIsInstance(audit, dict)
		self.assertEqual(audit.get("contract_version"), "1.1")
		self.assertEqual(
			audit.get("governed_resolution_details", {}).get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			audit.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("decision"),
			"normalize_intent",
		)

	def test_composite_execution_audit_preserves_governed_resolution_details(self):
		plan_contract = build_composite_read_plan_contract(
			plan_id="working_capital_health",
			request_id="semantic-composite-audit",
			decision="execute",
			steps=[
				{
					"step_id": "receivable",
					"family_id": "aging",
					"capability_id": "accounts_receivable_read",
					"selected_report": "Accounts Receivable Summary",
				},
				{
					"step_id": "payable",
					"family_id": "aging",
					"capability_id": "accounts_payable_read",
					"selected_report": "Accounts Payable Summary",
				},
			],
			compiler_reason="Composite plan approved.",
		)
		plan_compiler_contract = build_fresh_query_compiler_contract(
			request_id="semantic-composite-audit",
			session_id="semantic-composite",
			capability_id="composite::working_capital_health",
			selected_report="Composite Read",
			selected_report_family="composite_read",
			completed_filters={},
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			decision="execute",
			clarification_required=False,
			compiler_reason="Composite plan approved.",
			governed_resolution_details={
				"resolution_mode": "semantic_resolution",
				"semantic_resolution_contract": {
					"type": "qwen_financial_summary_resolution_contract",
					"decision": "execute_composite",
				},
			},
		)
		step_compiler_contract = build_fresh_query_compiler_contract(
			request_id="semantic-composite-audit:receivable",
			session_id="semantic-composite",
			capability_id="accounts_receivable_read",
			selected_report="Accounts Receivable Summary",
			selected_report_family="aging",
			completed_filters={"company": "Enterprise Co", "report_date": "2026-03-31"},
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			decision="execute",
			clarification_required=False,
			compiler_reason="Receivable step approved.",
		)
		step_request = build_compiled_query_request_contract(
			request_id="semantic-composite-audit:receivable",
			capability_id="accounts_receivable_read",
			selected_report="Accounts Receivable Summary",
			filters={"company": "Enterprise Co", "report_date": "2026-03-31"},
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			response_policy={},
		)
		plan_outcome = CompositePlanOutcome(
			status="execute",
			plan_contract=plan_contract,
			compiler_contract=plan_compiler_contract,
			step_compiler_contracts=[step_compiler_contract],
			step_compiled_requests=[step_request],
			errors=[],
		)

		fake_step = types.SimpleNamespace(
			step_id="receivable",
			family_id="aging",
			compiler_contract={"selected_report": "Accounts Receivable Summary"},
			compiled_request={"selected_report": "Accounts Receivable Summary"},
			runtime_payload={
				"ok": True,
				"tool_trace": [{"tool": "erp_fac-generate_report"}],
				"agent_meta": {"model": "governed", "validation": {"status": "pass"}},
			},
			artifact_payload={"artifact_type": "aging_summary"},
			family_validation_payload={"status": "pass"},
			runtime_latency_ms=12,
		)
		fake_render = types.SimpleNamespace(
			contract=types.SimpleNamespace(
				to_payload=lambda: {"answer_text": "Working capital looks stable."}
			)
		)
		with patch(
			"ai_assistant_ui.qwen_chat.composite_reads._execute_composite_step",
			return_value=fake_step,
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads._working_capital_health_summary",
			return_value={"answer_text": "Working capital looks stable."},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads._composite_validation_payload",
			return_value={"status": "fail", "validation_errors": [], "validation_warnings": [], "completed_steps": 1},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads._composite_semantic_payload",
			return_value={"status": "not_run", "errors": [], "warnings": []},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads.render_composite_family_response",
			return_value=fake_render,
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads.build_qwen_runtime_chat_request_config",
			return_value={},
		):
			result = execute_composite_read_plan(
				session_id="semantic-composite",
				user_id="Administrator",
				site_name="test-site",
				message="Show me our working capital health",
				recent_messages=[],
				pipeline={"request_id": "semantic-composite-audit"},
				plan_outcome=plan_outcome,
				proposal_generation_latency_ms=4,
				compilation_latency_ms=2,
				total_started=None,
			)
		audit = result.get("compiled_execution_audit")
		self.assertIsInstance(audit, dict)
		self.assertEqual(audit.get("contract_version"), "1.1")
		self.assertEqual(
			audit.get("governed_resolution_details", {}).get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			audit.get("governed_resolution_details", {})
			.get("semantic_resolution_contract", {})
			.get("decision"),
			"execute_composite",
		)

	def test_financial_summary_clarifies_sales_scope_without_guessing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-4",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Analytics"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.8,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-4",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "financial_summary_sales_scope_clarification")
		self.assertTrue(outcome.compiler_contract.clarification_details.get("blocks_legacy_fallback"))

	def test_financial_summary_clarification_translation_uses_governed_registry(self):
		signal = _translate_compiler_signal(
			request_id="semantic-fin-summary-signal",
			compiler_reason="Sales is valid but still unresolved.",
			compiler_reason_type="financial_summary_sales_scope_clarification",
			compiler_details={},
		)
		self.assertEqual(signal.user_question, "What kind of sales summary do you want: monthly trend, top customers, top products, or a sales statement-style summary?")
		self.assertEqual(
			signal.suggested_options,
			["monthly trend", "top customers", "top products", "sales statement-style summary"],
		)

	def test_financial_summary_clarification_translation_allows_governed_detail_override(self):
		signal = _translate_compiler_signal(
			request_id="semantic-fin-summary-signal-override",
			compiler_reason="Inventory focus is still unclear.",
			compiler_reason_type="financial_summary_focus_clarification",
			compiler_details={
				"user_question": "Which inventory summary focus do you want?",
				"suggested_options": ["value snapshot", "current position"],
			},
		)
		self.assertEqual(signal.user_question, "Which inventory summary focus do you want?")
		self.assertEqual(signal.suggested_options, ["value snapshot", "current position"])

	def test_financial_summary_clarifies_when_no_domain_is_resolved(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-no-domain",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.61,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-no-domain",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "financial_summary_domain_clarification")
		self.assertTrue(outcome.compiler_contract.clarification_details.get("blocks_legacy_fallback"))
		self.assertIn("financial_summary_resolution_contract", outcome.compiler_contract.clarification_details)

	def test_financial_summary_multi_domain_stays_outside_first_slice(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-5",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read", "accounts_payable_read"],
			candidate_reports=["Accounts Receivable Summary", "Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = compile_fresh_query(
			request_id="semantic-fin-summary-5",
			session_id="semantic-fin-summary",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "financial_summary_multi_domain_clarification")
		self.assertTrue(outcome.compiler_contract.clarification_details.get("blocks_legacy_fallback"))
		self.assertIn("financial_summary_resolution_contract", outcome.compiler_contract.clarification_details)

	def test_financial_statement_resolution_executes_single_statement(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-1",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=[],
			candidate_reports=["Balance Sheet"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.94,
		)
		outcome = resolve_financial_statement_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("statement_variant"), "balance_sheet")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["financial_statement_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Balance Sheet"])

	def test_transaction_listing_resolution_defaults_sales_invoice_listing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-1",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.66,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "sales_invoice")
		self.assertEqual(outcome.contract.resolution_source.get("listing_view"), "metadata_default")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["sales_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Sales Invoice List"])
		self.assertEqual(outcome.interpretation.requested_dimensions, ["Invoice"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Grand Total"])

	def test_transaction_listing_resolution_preserves_explicit_sales_invoice_report(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-2",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Invoice List"],
			requested_dimensions=["Invoice"],
			requested_metrics=["Outstanding Amount"],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolution_source.get("listing_view"), "semantic_runtime")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Sales Invoice List"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Outstanding Amount"])

	def test_compiler_executes_transaction_listing_default(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-3",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.7,
		)
		outcome = compile_fresh_query(
			request_id="semantic-listing-3",
			session_id="semantic-listing",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Sales Invoice List")
		self.assertEqual(outcome.compiler_contract.capability_id, "sales_read")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("governed_decision"),
			"execute",
		)

	def test_financial_statement_resolution_clarifies_missing_variant(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-2",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.81,
		)
		outcome = resolve_financial_statement_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "clarify")
		self.assertIn("Profit and Loss Statement", outcome.contract.candidate_reports)
		self.assertIn("Balance Sheet", outcome.contract.candidate_reports)
		self.assertIn("Cash Flow", outcome.contract.candidate_reports)

	def test_compiler_clarifies_missing_financial_statement_variant(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-3",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.88,
		)
		outcome = compile_fresh_query(
			request_id="semantic-financial-3",
			session_id="semantic-financial",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "report_ambiguity")
		self.assertIn(
			"semantic_resolution_contract",
			outcome.compiler_contract.clarification_details,
		)

	def test_compiler_executes_resolved_balance_sheet(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-4",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=[],
			candidate_reports=["Balance Sheet"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = compile_fresh_query(
			request_id="semantic-financial-4",
			session_id="semantic-financial",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Balance Sheet")
		self.assertEqual(outcome.compiler_contract.capability_id, "financial_statement_read")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("governed_decision"),
			"execute",
		)

	def test_inventory_summary_resolution_executes_warehouse_report(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-inventory-1",
			session_id="semantic-inventory",
			intent_class="inventory_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=[],
			requested_dimensions=["Warehouse"],
			requested_metrics=["Balance Value (MMK)"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_inventory_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("inventory_axis"), "warehouse")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Warehouse Wise Stock Balance"])

	def test_inventory_summary_resolution_defaults_to_item_report(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-inventory-2",
			session_id="semantic-inventory",
			intent_class="inventory_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=["Balance Qty"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.74,
		)
		outcome = resolve_inventory_summary_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("inventory_axis"), "item")
		self.assertEqual(
			outcome.contract.resolution_source.get("inventory_axis"),
			"metadata_default",
		)
		self.assertEqual(outcome.interpretation.candidate_reports, ["Stock Balance"])

	def test_compiler_executes_inventory_default_item_report(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-inventory-3",
			session_id="semantic-inventory",
			intent_class="inventory_summary",
			candidate_capability_ids=["stock_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=["Balance Qty"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.82,
		)
		outcome = compile_fresh_query(
			request_id="semantic-inventory-3",
			session_id="semantic-inventory",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Stock Balance")
		self.assertEqual(outcome.compiler_contract.capability_id, "stock_read")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get("resolution_mode"),
			"semantic_resolution",
		)
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("governed_decision"),
			"execute",
		)

	def test_ranking_resolution_executes_customer_revenue(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-1",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Customer"],
			requested_metrics=["Revenue"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
		)
		outcome = resolve_ranked_entities_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("ranking_subject"), "customer")
		self.assertEqual(outcome.contract.resolved_slots.get("ranking_metric"), "sales_amount")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Sales Analytics"])

	def test_aging_resolution_executes_receivable_from_report(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-aging-1",
			session_id="semantic-aging",
			intent_class="aging_analysis",
			candidate_capability_ids=[],
			candidate_reports=["Accounts Receivable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding Amount"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = resolve_aging_analysis_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("aging_view"), "receivable")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["accounts_receivable_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Accounts Receivable Summary"])

	def test_aging_resolution_executes_payable_from_capability(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-aging-2",
			session_id="semantic-aging",
			intent_class="aging_analysis",
			candidate_capability_ids=["accounts_payable_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=["Outstanding Amount"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.88,
		)
		outcome = resolve_aging_analysis_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("aging_view"), "payable")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Accounts Payable Summary"])

	def test_compiler_clarifies_missing_aging_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-aging-3",
			session_id="semantic-aging",
			intent_class="aging_analysis",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=["Outstanding Amount"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.75,
		)
		outcome = compile_fresh_query(
			request_id="semantic-aging-3",
			session_id="semantic-aging",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "clarify")
		self.assertEqual(outcome.compiler_contract.clarification_reason_type, "report_ambiguity")
		self.assertIn(
			"semantic_resolution_contract",
			outcome.compiler_contract.clarification_details,
		)

	def test_trend_resolution_executes_quantity_metric(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-1",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=["Quantity"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.86,
		)
		outcome = resolve_trend_analysis_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "quantity")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Sales Analytics"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Quantity"])

	def test_trend_resolution_defaults_sales_amount_when_metric_missing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-2",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=["sales_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.7,
		)
		outcome = resolve_trend_analysis_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "sales_amount")
		self.assertEqual(outcome.contract.resolution_source.get("trend_metric"), "metadata_default")
		self.assertEqual(outcome.interpretation.requested_metrics, ["Sales Amount"])

	def test_compiler_executes_default_trend_metric(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-3",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.73,
		)
		outcome = compile_fresh_query(
			request_id="semantic-trend-3",
			session_id="semantic-trend",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Sales Analytics")
		self.assertEqual(outcome.compiler_contract.capability_id, "sales_read")

	def test_ranking_resolution_executes_product_gross_profit(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-2",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.94,
		)
		outcome = resolve_ranked_entities_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("ranking_subject"), "product")
		self.assertEqual(outcome.contract.resolved_slots.get("ranking_metric"), "gross_profit")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Gross Profit"])

	def test_ranking_resolution_clarifies_missing_metric(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-3",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.77,
		)
		outcome = resolve_ranked_entities_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "clarify")
		self.assertIn("missing_ranking_metric", outcome.contract.ambiguity_flags)

	def test_compiler_executes_ranking_customer_revenue(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-4",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Customer"],
			requested_metrics=["Revenue"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = compile_fresh_query(
			request_id="semantic-ranking-4",
			session_id="semantic-ranking",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Sales Analytics")
		self.assertEqual(outcome.compiler_contract.capability_id, "sales_read")

	def test_compiler_executes_ranking_customer_quantity(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-quantity",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Customer"],
			requested_metrics=["Quantity"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = compile_fresh_query(
			request_id="semantic-ranking-quantity",
			session_id="semantic-ranking",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Sales Analytics")
		self.assertEqual(outcome.compiler_contract.capability_id, "sales_read")

	def test_ranked_entities_resolution_clarifies_mixed_metric_payload(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-ranking-mixed-metrics",
			session_id="semantic-ranking",
			intent_class="ranked_entities",
			candidate_capability_ids=["accounts_receivable_read"],
			candidate_reports=["Accounts Receivable Summary"],
			requested_dimensions=["Customer"],
			requested_metrics=["Value", "Outstanding Amount"],
			requested_time_scope="",
			requested_presentation=["table_presentation"],
			extracted_slots={},
			ambiguity_flags=["missing_metric"],
			ambiguity_reason="",
			confidence=0.75,
		)
		outcome = resolve_ranked_entities_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "clarify")
		self.assertIn("missing_ranking_metric", outcome.contract.ambiguity_flags)
		self.assertEqual(outcome.interpretation.candidate_reports, [])

	def test_runtime_ranking_payload_does_not_repair_noisy_receivable_bundle_from_message(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "ranked_entities",
					"candidate_capability_ids": ["accounts_receivable_read"],
					"candidate_reports": ["Accounts Receivable Summary"],
					"requested_dimensions": ["Customer"],
					"requested_metrics": [
						"Value",
						"Grand Total",
						"Outstanding",
						"Total Due",
						"Selling Amount",
						"Billed Amount",
					],
					"requested_time_scope": "",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {},
					"ambiguity_flags": ["missing_metric", "missing_time_scope"],
					"ambiguity_reason": "",
					"confidence": 0.75,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-ranking-runtime",
				user_id="Administrator",
				site_name="test-site",
				message="Top 5 customers by revenue",
				recent_messages=[],
			)

		self.assertEqual(
			pipeline.get("fresh_query_interpretation", {}).get("validation_error"),
			"Runtime fresh-query interpretation did not pass governed validation.",
		)
		self.assertNotIn("fresh_query_compiler", pipeline)

	def test_runtime_payload_validation_does_not_derive_time_scope_from_message(self):
		context = _build_interpretation_context()
		contract = _validate_semantic_payload(
			request_id="semantic-ranking-no-time-repair",
			session_id="semantic-ranking-runtime",
			payload={
				"intent_class": "ranked_entities",
				"candidate_capability_ids": ["sales_read"],
				"candidate_reports": ["Sales Analytics"],
				"requested_dimensions": ["Customer"],
				"requested_metrics": ["Value"],
				"requested_time_scope": "",
				"requested_presentation": ["table_presentation"],
				"extracted_slots": {},
				"ambiguity_flags": ["missing_time_scope"],
				"ambiguity_reason": "",
				"confidence": 0.8,
			},
			context=context,
			message="Top 5 customers by revenue last month",
		)
		self.assertIsNotNone(contract)
		self.assertEqual(contract.requested_time_scope, "current_fiscal_year_to_date")

	def test_ranking_column_refinement_stays_local_when_quantity_exists(self):
		resolution = build_followup_resolution_contract(
			request_id="continuation-ranking-qty",
			mode="grounded_follow_up",
			requested_modes=["column_refinement"],
			target_dimension="Item",
			target_limit=7,
			target_metric="sales_amount",
			requested_columns=["quantity"],
			requested_time_scope="",
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="Include quantity column.",
		)
		continuation_contract = types.SimpleNamespace(
			preserve_grounded_context=True,
			source_family_id="ranking_analytics",
			source_capability_id="product_performance_read",
			source_report="Gross Profit",
			preserved_dimension="Item",
			source_dimension="Item",
			preserved_metric_key="sales_amount",
			source_metric_key="sales_amount",
			preserve_projection_shape=False,
			preserved_requested_columns=["quantity"],
			source_requested_columns=["entity", "sales_amount"],
			preserve_rank_membership=True,
			preserved_limit=7,
			source_limit=7,
			preserve_rank_order=True,
			preserved_sort_direction="",
			source_sort_direction="",
			preserved_time_scope="",
			source_time_scope="",
		)
		artifact_payload = {
			"dimensions": {
				"requested_metric_key": "sales_amount",
				"available_metric_keys": ["sales_amount", "quantity"],
			},
			"sections": {
				"ranked_rows": [
					{"entity": "A", "sales_amount": 100, "quantity": 2},
					{"entity": "B", "sales_amount": 80, "quantity": 1},
				]
			},
		}
		outcome = authoritative_continuation_resolution(
			request_id="continuation-ranking-qty",
			followup_resolution=resolution,
			continuation_contract=continuation_contract,
			artifact_payload=artifact_payload,
			grounded_turn={},
		)
		self.assertEqual(outcome.mode, "grounded_follow_up")
		self.assertEqual(list(outcome.requested_columns), ["quantity"])
		self.assertEqual(outcome.target_metric, "sales_amount")

	def test_product_performance_resolution_executes_profitability_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-product-1",
			session_id="semantic-product",
			intent_class="product_performance",
			candidate_capability_ids=[],
			candidate_reports=["Gross Profit"],
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit", "Gross Profit Percent"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.94,
		)
		outcome = resolve_product_performance_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("performance_view"), "profitability")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Gross Profit"])

	def test_product_performance_resolution_executes_sales_history_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-product-2",
			session_id="semantic-product",
			intent_class="product_performance",
			candidate_capability_ids=[],
			candidate_reports=["Item-wise Sales History"],
			requested_dimensions=["Item"],
			requested_metrics=["Billed Amount", "Delivered Quantity"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = resolve_product_performance_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("performance_view"), "sales_history")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Item-wise Sales History"])

	def test_product_performance_resolution_clarifies_unresolved_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-product-3",
			session_id="semantic-product",
			intent_class="product_performance",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Item"],
			requested_metrics=["Quantity"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.8,
		)
		outcome = resolve_product_performance_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "clarify")
		self.assertIn("missing_performance_view", outcome.contract.ambiguity_flags)

	def test_compiler_executes_product_profitability_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-product-4",
			session_id="semantic-product",
			intent_class="product_performance",
			candidate_capability_ids=[],
			candidate_reports=["Gross Profit"],
			requested_dimensions=["Item Code"],
			requested_metrics=["Gross Profit", "Gross Profit Percent"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = compile_fresh_query(
			request_id="semantic-product-4",
			session_id="semantic-product",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Gross Profit")
		self.assertEqual(outcome.compiler_contract.capability_id, "product_performance_read")

	def test_semantic_registry_intent_classes_cover_resolved_domains(self):
		intent_classes = semantic_resolution_intent_classes()
		self.assertIn("transaction_listing", intent_classes)
		self.assertIn("financial_statement", intent_classes)
		self.assertIn("inventory_summary", intent_classes)
		self.assertIn("aging_analysis", intent_classes)
		self.assertIn("trend_analysis", intent_classes)
		self.assertIn("ranked_entities", intent_classes)
		self.assertIn("product_performance", intent_classes)

	def test_semantic_registry_governs_intent_helper(self):
		self.assertTrue(semantic_resolution_governs_intent("transaction_listing"))
		self.assertTrue(semantic_resolution_governs_intent("financial_statement"))
		self.assertTrue(semantic_resolution_governs_intent("trend_analysis"))
		self.assertFalse(semantic_resolution_governs_intent("financial_summary"))

	def test_governed_interpretation_biases_do_not_lexically_steer_semantic_intent(self):
		capability_ids, candidate_reports = _apply_governed_interpretation_biases(
			intent_class="financial_statement",
			message="show me balance sheet",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
		)
		self.assertEqual(capability_ids, [])
		self.assertEqual(candidate_reports, [])

	def test_deterministic_family_surface_fallback_is_disabled_for_semantic_intent(self):
		self.assertFalse(_allow_deterministic_family_surface_fallback("transaction_listing"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("financial_statement"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("inventory_summary"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("aging_analysis"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("trend_analysis"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("financial_summary"))

	def test_deterministic_family_surface_interpretation_is_retired(self):
		outcome = _deterministic_family_surface_interpretation(
			request_id="semantic-det-1",
			session_id="semantic-det",
			message="show me p and l",
			confidence_threshold=0.8,
		)
		self.assertIsNone(outcome)

	def test_legacy_runtime_family_surface_disabled_for_semantic_rollout_fallback(self):
		self.assertFalse(_legacy_runtime_family_tool_surface_allowed(None))
		self.assertFalse(
			_legacy_runtime_family_tool_surface_allowed(
				{"interpretation_intent_class": "transaction_listing"}
			)
		)
		self.assertFalse(
			_legacy_runtime_family_tool_surface_allowed(
				{"interpretation_intent_class": "financial_statement"}
			)
		)
		self.assertFalse(
			_legacy_runtime_family_tool_surface_allowed(
				{"interpretation_intent_class": "trend_analysis"}
			)
		)
		self.assertFalse(
			_legacy_runtime_family_tool_surface_allowed(
				{"interpretation_intent_class": "financial_summary"}
			)
		)
		self.assertFalse(_legacy_runtime_family_tool_surface_allowed({}))

	def test_legacy_runtime_success_payload_includes_mode(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.call_qwen_runtime_chat",
			return_value={
				"ok": True,
				"answer_text": "AR summary",
				"tool_trace": [],
				"agent_meta": {"engine": "qwen_agent", "mode": "read_only"},
				"error": "",
			},
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_grounded_turn_context",
			return_value=types.SimpleNamespace(grounded=False),
		):
			handled, payload = handle_legacy_runtime_turn(
				session_doc=types.SimpleNamespace(),
				request_id="legacy-runtime-mode",
				session_id="legacy-runtime-mode",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me ar summary",
				recent_messages=[],
				response_policy_contract=types.SimpleNamespace(to_runtime_payload=lambda: {}),
				interaction_contract=types.SimpleNamespace(),
				followup_resolution=types.SimpleNamespace(),
				execution_path=types.SimpleNamespace(),
				compiled_rollout_fallback=None,
				append_message=lambda *args, **kwargs: None,
				append_tool_payload=lambda *args, **kwargs: None,
				assistant_text_payload=lambda text: text,
				save_session=lambda *args, **kwargs: None,
				tool_trace_payload=lambda **kwargs: {},
				tool_trace_message=lambda **kwargs: "",
				safe_runtime_failure_message=lambda exc: str(exc),
				latest_qwen_trace_payload=lambda *args, **kwargs: {},
				latest_assistant_payload=lambda *args, **kwargs: {},
				latest_normalized_family_artifact=lambda *args, **kwargs: {},
			)
		self.assertTrue(handled)
		self.assertEqual(payload.get("mode"), "legacy_runtime")

	def test_legacy_runtime_without_compiled_fallback_does_not_build_family_surface(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.call_qwen_runtime_chat",
			return_value={
				"ok": True,
				"answer_text": "AR summary",
				"tool_trace": [],
				"agent_meta": {"engine": "qwen_agent", "mode": "read_only"},
				"error": "",
			},
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_grounded_turn_context",
			return_value=types.SimpleNamespace(grounded=False),
		):
			handled, payload = handle_legacy_runtime_turn(
				session_doc=types.SimpleNamespace(),
				request_id="legacy-runtime-no-surface",
				session_id="legacy-runtime-no-surface",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="top customers by revenue",
				recent_messages=[],
				response_policy_contract=types.SimpleNamespace(to_runtime_payload=lambda: {}),
				interaction_contract=types.SimpleNamespace(),
				followup_resolution=types.SimpleNamespace(),
				execution_path=types.SimpleNamespace(),
				compiled_rollout_fallback=None,
				append_message=lambda *args, **kwargs: None,
				append_tool_payload=lambda *args, **kwargs: None,
				assistant_text_payload=lambda text: text,
				save_session=lambda *args, **kwargs: None,
				tool_trace_payload=lambda **kwargs: {},
				tool_trace_message=lambda **kwargs: "",
				safe_runtime_failure_message=lambda exc: str(exc),
				latest_qwen_trace_payload=lambda *args, **kwargs: {},
				latest_assistant_payload=lambda *args, **kwargs: {},
				latest_normalized_family_artifact=lambda *args, **kwargs: {},
			)
		self.assertTrue(handled)
		self.assertEqual(payload.get("mode"), "legacy_runtime")

	def test_legacy_runtime_with_structured_rollout_fallback_does_not_build_family_surface(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.call_qwen_runtime_chat",
			return_value={
				"ok": True,
				"answer_text": "financial summary",
				"tool_trace": [],
				"agent_meta": {"engine": "qwen_agent", "mode": "read_only"},
				"error": "",
			},
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.build_grounded_turn_context",
			return_value=types.SimpleNamespace(grounded=False),
		):
			handled, payload = handle_legacy_runtime_turn(
				session_doc=types.SimpleNamespace(),
				request_id="legacy-runtime-no-surface-rollout",
				session_id="legacy-runtime-no-surface-rollout",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="top customers by revenue",
				recent_messages=[],
				response_policy_contract=types.SimpleNamespace(to_runtime_payload=lambda: {}),
				interaction_contract=types.SimpleNamespace(),
				followup_resolution=types.SimpleNamespace(),
				execution_path=types.SimpleNamespace(),
				compiled_rollout_fallback={"interpretation_intent_class": "financial_summary", "reason": "legacy-path"},
				append_message=lambda *args, **kwargs: None,
				append_tool_payload=lambda *args, **kwargs: None,
				assistant_text_payload=lambda text: text,
				save_session=lambda *args, **kwargs: None,
				tool_trace_payload=lambda **kwargs: {},
				tool_trace_message=lambda **kwargs: "",
				safe_runtime_failure_message=lambda exc: str(exc),
				latest_qwen_trace_payload=lambda *args, **kwargs: {},
				latest_assistant_payload=lambda *args, **kwargs: {},
				latest_normalized_family_artifact=lambda *args, **kwargs: {},
			)
		self.assertTrue(handled)
		self.assertEqual(payload.get("mode"), "legacy_runtime_rollout_fallback")

	def test_family_tool_surface_no_longer_matches_marker_only_phrase(self):
		surface = build_family_tool_surface_for_message(
			request_id="family-surface-no-marker",
			session_id="family-surface-no-marker",
			message="give me management report",
		)
		self.assertIsNone(surface)

	def test_ranking_family_adapter_uses_structured_compiler_metrics(self):
		compiler_contract = {
			"request_id": "adapter-structured-1",
			"capability_id": "sales_read",
			"selected_report": "Sales Analytics",
			"requested_dimensions": ["Customer"],
			"requested_metrics": ["qty"],
			"requested_time_scope": "last_month",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Sales Analytics",
						"filters": {
							"tree_type": "Customer",
							"value_quantity": "quantity",
							"period_start_date": "2026-03-01",
							"period_end_date": "2026-03-31",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{"entity": "CUST-001", "entity_name": "Alpha", "total": 1000},
								{"entity": "CUST-002", "entity_name": "Beta", "total": 500},
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-structured-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="ranked_entities",
			preferred_family_id="ranking_analytics",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		self.assertEqual(dimensions.get("requested_metric_key"), "quantity")
		self.assertEqual(dimensions.get("requested_columns"), ["entity", "quantity"])

	def test_transaction_listing_family_adapter_uses_structured_columns(self):
		compiler_contract = {
			"request_id": "adapter-structured-2",
			"capability_id": "sales_read",
			"selected_report": "Sales Invoice List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Outstanding Amount"],
			"requested_time_scope": "last_month",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Sales Invoice List",
						"filters": {
							"from_date": "2026-03-01",
							"to_date": "2026-03-31",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "SINV-0001",
									"posting_date": "2026-03-05",
									"customer": "Alpha",
									"grand_total": 1200,
									"outstanding_amount": 400,
									"status": "Overdue",
									"docstatus": 1,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-structured-2",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		self.assertEqual(
			dimensions.get("requested_columns"),
			["posting_date", "customer", "outstanding_amount"],
		)

	def test_direct_query_execution_uses_governed_default_limit(self):
		report_spec = {
			"grounding_mode": "direct_query",
			"direct_query": {
				"doctype": "Sales Invoice",
				"fields": ["name"],
				"default_limit": 7,
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.get_report_spec",
			return_value=report_spec,
		), patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.frappe.get_all",
			return_value=[{"name": "SINV-0001"}],
		) as mocked_get_all:
			payload = execute_governed_report(
				report_name="Sales Invoice List",
				filters={},
				user="Administrator",
			)
		self.assertTrue(payload.get("ok"))
		self.assertEqual(mocked_get_all.call_args.kwargs.get("limit_page_length"), 7)
