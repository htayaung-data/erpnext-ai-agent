import sys
import types
import unittest
from unittest.mock import Mock, patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2025",
				"year_start_date": "2024-04-01",
				"year_end_date": "2025-03-31",
			},
			{
				"name": "FY-2026",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			},
			{
				"name": "FY-2027",
				"year_start_date": "2026-04-01",
				"year_end_date": "2027-03-31",
			}
		]
	if doctype == "Period Closing Voucher":
		return [
			{
				"name": "PCV-2025-0001",
				"company": "Enterprise Co",
				"fiscal_year": "FY-2025",
				"period_start_date": "2024-04-01",
				"period_end_date": "2025-03-31",
				"transaction_date": "2025-03-31",
				"gle_processing_status": "Completed",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: False)
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.clarification_translation import _translate_compiler_signal
from ai_assistant_ui.qwen_chat.contracts import (
	build_artifact_enrichment_compatibility_contract,
	build_artifact_continuation_contract,
	build_clarification_reason_contract_from_sources,
	build_compiled_query_request_contract,
	build_composite_read_plan_contract,
	build_followup_boundary_contract,
	build_followup_resolution_contract,
	build_fresh_query_compiler_contract,
	build_fresh_query_interpretation_contract,
	build_followup_resolution,
	build_grounded_turn_context,
	build_normalized_family_artifact_contract,
	build_scope_decision_input,
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
	interpret_front_door_semantically,
)
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_followup import (
	refine_local_family_artifact,
	render_local_family_followup,
	supports_local_family_followup,
)
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.family_validator import validate_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_tool_surface import build_family_tool_surface_for_message
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_allow_deterministic_family_surface_fallback,
	_apply_governed_interpretation_biases,
	_build_interpretation_context,
	_augment_master_data_lookup_interpretation_from_message,
	SemanticFreshQueryResult,
	compile_from_fresh_query_message,
	execute_compiled_fresh_query_message,
	_deterministic_family_surface_interpretation,
	_reconcile_financial_statement_default_time_scope_from_message,
	_recover_pipeline_with_deterministic_surface_fallback,
	_normalize_trend_requested_metrics_from_message,
	_validate_semantic_payload,
)
from ai_assistant_ui.qwen_chat.metadata import (
	capability_fresh_query_defaults,
	entity_grain_display_label,
	get_report_spec,
	get_report_family_spec,
	load_business_ontology,
	load_semantic_resolution_registry,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import listing_view_display_label
from ai_assistant_ui.qwen_chat.semantic_interpreter import (
	_build_interpretation_context as _build_semantic_followup_context,
	interpret_artifact_local_projection_deterministically,
	_validate_semantic_payload as _validate_semantic_followup_payload,
)
from ai_assistant_ui.qwen_chat import followup_interpreter as followup_interpreter_module
from ai_assistant_ui.qwen_chat.followup_interpreter import assess_context_isolation
from ai_assistant_ui.qwen_chat.continuation_support import authoritative_continuation_resolution
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report
from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	_resolve_composite_candidate,
)
from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import (
	_legacy_runtime_family_tool_surface_allowed,
	handle_legacy_runtime_turn,
)
from ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane import handle_runtime_gate_turn
from ai_assistant_ui.qwen_chat.requery_message_support import (
	compile_capability_requery_message,
)
from ai_assistant_ui.qwen_chat.metric_union_support import artifact_metric_columns_available
from ai_assistant_ui.qwen_chat.phase8_hardening_support import (
	_seed_quantity_recovery_session,
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
	resolve_master_data_lookup_interpretation,
	resolve_product_performance_interpretation,
	resolve_ranked_entities_interpretation,
	resolve_trend_analysis_interpretation,
	resolve_transaction_listing_interpretation,
)
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import evaluate_frontdoor_lane
from ai_assistant_ui.qwen_chat.scope_support import (
	reasoning_preempted_by_followup_refinement,
	reasoning_scope_suppression_allowed,
	reasoning_supersedes_contradictory_presentation_followup,
)
from ai_assistant_ui.qwen_chat.service import (
	_frontdoor_context_isolation_retry_needed,
	_frontdoor_recent_messages_for_message,
	_message_looks_like_self_contained_governed_business_query,
	_should_skip_artifact_boundary,
)


class TestSemanticFinancialResolution(unittest.TestCase):
	def test_reasoning_supersedes_contradictory_presentation_only_followup(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["presentation_transform"],
			target_dimension="Customer",
			target_limit=10,
			sort_direction="desc",
			target_metric="outstanding",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
		)
		reasoning_result = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="explanation"),
		)
		self.assertTrue(
			reasoning_supersedes_contradictory_presentation_followup(
				semantic_intent=semantic_intent,
				reasoning_semantic_result=reasoning_result,
			)
		)

	def test_reasoning_does_not_supersede_legitimate_structured_followup(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["dimension_breakdown"],
			target_dimension="Customer",
			target_limit=10,
			sort_direction="desc",
			target_metric="outstanding",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
		)
		reasoning_result = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="explanation"),
		)
		self.assertFalse(
			reasoning_supersedes_contradictory_presentation_followup(
				semantic_intent=semantic_intent,
				reasoning_semantic_result=reasoning_result,
			)
		)

	def test_recovery_semantic_bypass_detects_self_contained_governed_business_query(self):
		self.assertTrue(
			_message_looks_like_self_contained_governed_business_query(
				message="give me last year delivery trend",
			)
		)


	def test_recovery_semantic_bypass_detects_payment_entry_self_contained_query(self):
		self.assertTrue(
			_message_looks_like_self_contained_governed_business_query(
				message="show me payment entries",
			)
		)

	def test_recovery_semantic_bypass_does_not_trigger_on_short_acknowledgement(self):
		self.assertFalse(
			_message_looks_like_self_contained_governed_business_query(
				message="yes",
			)
		)

	def test_frontdoor_recent_messages_preserve_grounded_anchor_followup(self):
		recent_messages = [
			{"role": "user", "content": "show me payment entries"},
			{"role": "assistant", "content": "Here are the payment entries."},
		]
		self.assertEqual(
			_frontdoor_recent_messages_for_message(
				message="show me those payment entries today",
				recent_messages=recent_messages,
				grounded_context_available=True,
			),
			recent_messages,
		)

	def test_frontdoor_context_isolation_retry_needed_for_unanchored_clarification(self):
		contract = types.SimpleNamespace(
			handle_in_front_door=True,
			intent_class="master_data_grain_clarification",
		)
		self.assertTrue(
			_frontdoor_context_isolation_retry_needed(
				message="show me payment entries today",
				grounded_context_available=True,
				frontdoor_contract=contract,
			)
		)

	def test_frontdoor_context_isolation_retry_skips_anchored_followup(self):
		contract = types.SimpleNamespace(
			handle_in_front_door=True,
			intent_class="master_data_grain_clarification",
		)
		self.assertFalse(
			_frontdoor_context_isolation_retry_needed(
				message="show me those payment entries today",
				grounded_context_available=True,
				frontdoor_contract=contract,
			)
		)

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
				latest_grounded_turn={},
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
				latest_grounded_turn={},
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

	def test_deferred_artifact_refinement_prevents_master_data_frontdoor_capture(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=0.91,
					reason="The current grounded artifact should get first chance to answer.",
				),
				confidence_threshold=0.8,
			),
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.assess_master_data_frontdoor_request",
			return_value={"assessment_contract": object()},
		) as master_data_frontdoor:
			frontdoor_semantic_result, frontdoor_contract, _render_result, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-deferred-artifact-evidence",
				session_id="session-deferred-artifact-evidence",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me the aging breakdown for the first customer",
				recent_messages=[],
				grounded_context_available=True,
				latest_grounded_turn={"artifact_family_id": "customer_entity_detail"},
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=None,
				defer_runtime_value_frontdoor=True,
			)

		master_data_frontdoor.assert_not_called()
		self.assertEqual(frontdoor_semantic_result.status, "accepted")
		self.assertEqual(frontdoor_contract.intent_class, "route_onward")
		self.assertFalse(frontdoor_contract.handle_in_front_door)
		self.assertEqual(frontdoor_answer, "")

	def test_frontdoor_semantic_keeps_thanks_in_front_door_despite_fresh_query_acceptance(self):
		with patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.call_qwen_runtime_frontdoor_interpretation",
			return_value={
				"interpretation": {
					"intent_class": "thanks",
					"confidence": 0.97,
					"reason": "The message is clearly appreciative and requests no ERP data.",
				},
				"agent_meta": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.interpret_fresh_query_semantically",
			return_value=types.SimpleNamespace(
				status="accepted",
				confidence_threshold=0.72,
				interpretation=types.SimpleNamespace(
					candidate_capability_ids=["receivable_summary"],
					candidate_reports=["Accounts Receivable Summary"],
					confidence=0.93,
				),
			),
		):
			result = interpret_front_door_semantically(
				request_id="frontdoor-thanks",
				session_id="session-thanks",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="Really Great, thank you",
				recent_messages=[],
				grounded_context_available=True,
			)
		self.assertEqual(result.status, "accepted")
		self.assertEqual(result.intent.intent_class, "thanks")

	def test_frontdoor_semantic_can_still_override_session_flow_with_fresh_query_acceptance(self):
		with patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.call_qwen_runtime_frontdoor_interpretation",
			return_value={
				"interpretation": {
					"intent_class": "session_flow",
					"confidence": 0.95,
					"reason": "The message looks like a continuation turn.",
				},
				"agent_meta": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.interpret_fresh_query_semantically",
			return_value=types.SimpleNamespace(
				status="accepted",
				confidence_threshold=0.72,
				interpretation=types.SimpleNamespace(
					candidate_capability_ids=["receivable_summary"],
					candidate_reports=["Accounts Receivable Summary"],
					confidence=0.93,
				),
			),
		):
			result = interpret_front_door_semantically(
				request_id="frontdoor-session-flow",
				session_id="session-flow",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="what does this mean",
				recent_messages=[],
				grounded_context_available=True,
			)
		self.assertEqual(result.status, "guardrailed_to_route_onward")
		self.assertEqual(result.intent.intent_class, "route_onward")

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

	def test_semantic_followup_context_uses_report_context_for_report_family_artifact(self):
		context = _build_semantic_followup_context(
			latest_grounded_turn={
				"source_name": "ranking_analytics",
				"artifact_family_id": "ranking_analytics",
				"artifact_source_reports": ["Sales Order List"],
				"returned_schema": ["Customer", "Revenue", "Quantity", "Average Order Value"],
				"row_count": 4,
			},
			latest_assistant_payload={"title": "Top Customers"},
		)
		self.assertEqual(context.get("source_surface_name"), "ranking_analytics")
		self.assertEqual(context.get("source_report_name"), "Sales Order List")
		self.assertTrue(context.get("grounded_followup_supported"))
		self.assertIn("column_projection", context.get("approved_follow_up_modes") or [])
		self.assertIn("Customer", context.get("available_dimensions") or [])

	def test_artifact_metric_columns_available_resolves_family_aliases(self):
		artifact_payload = {
			"dimensions": {
				"available_metric_keys": ["revenue", "quantity", "average_order_value", "sales_amount"],
				"requested_column_alias_map": {
					"customer": "entity",
					"customer_name": "entity",
					"aov": "average_order_value",
					"rev": "revenue",
					"qty": "quantity",
				},
			},
			"sections": {
				"ranked_rows": [
					{
						"entity": "Zegyo Mobile Supply House",
						"customer_name": "Zegyo Mobile Supply House",
						"revenue": 9340000.0,
						"quantity": 30.0,
						"average_order_value": 3113333.33,
					}
				]
			},
		}
		self.assertTrue(
			artifact_metric_columns_available(
				artifact_payload,
				["customer name", "aov"],
			)
		)

	def test_artifact_local_projection_fallback_accepts_family_alias_projection(self):
		result = interpret_artifact_local_projection_deterministically(
			message="Give me customer name and AOV column only",
			latest_grounded_turn={
				"source_name": "ranking_analytics",
				"artifact_family_id": "ranking_analytics",
			},
			latest_family_artifact={
				"family_id": "ranking_analytics",
				"dimensions": {
					"requested_column_alias_map": {
						"customer": "entity",
						"customer name": "entity",
						"aov": "average_order_value",
						"average order value": "average_order_value",
					},
				},
			},
		)
		self.assertEqual(result.status, "accepted")
		self.assertEqual(list(result.intent.requested_modes), ["column_projection"])
		self.assertEqual(list(result.intent.requested_columns), ["entity", "average_order_value"])
		self.assertEqual(result.intent.target_metric, "average_order_value")

	def test_artifact_local_projection_fallback_rejects_time_scope_breakout(self):
		result = interpret_artifact_local_projection_deterministically(
			message="Give me customer name and AOV column only for last year",
			latest_grounded_turn={
				"source_name": "ranking_analytics",
				"artifact_family_id": "ranking_analytics",
			},
			latest_family_artifact={
				"family_id": "ranking_analytics",
				"dimensions": {
					"requested_column_alias_map": {
						"customer": "entity",
						"customer name": "entity",
						"aov": "average_order_value",
					},
				},
			},
		)
		self.assertEqual(result.status, "not_applicable")

	def test_build_followup_resolution_infers_last_year_temporal_correction_and_clears_inherited_limit_noise(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["sort_or_limit"],
			target_dimension="Transaction Date",
			target_limit=5,
			sort_direction="",
			target_metric="revenue",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="The user is restating the governed period for the current ranking.",
		)
		resolution = build_followup_resolution(
			request_id="grounded-last-year-restatement",
			message="I mean last year, not last month",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"source_name": "Sales Order List",
				"artifact_family_id": "ranking_analytics",
				"returned_schema": ["Customer", "Revenue", "Average Order Value"],
				"dimensions": ["Customer"],
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
			degraded_reason="",
		)
		self.assertEqual(resolution.mode, "capability_requery")
		self.assertEqual(resolution.requested_time_scope, "last_year")
		self.assertEqual(resolution.target_limit, 0)
		self.assertEqual(resolution.target_dimension, "")
		self.assertIn("time_scope_restatement", resolution.requested_modes)
		self.assertNotIn("sort_or_limit", resolution.requested_modes)

	def test_build_followup_resolution_keeps_grounded_column_refinement_despite_inherited_date_context(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["column_refinement"],
			target_dimension="Customer",
			target_limit=5,
			sort_direction="",
			target_metric="revenue",
			requested_columns=["customer", "average order value"],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User requested specific columns from the previous result.",
		)
		resolution = build_followup_resolution(
			request_id="grounded-column-refinement",
			message="give me customer name and AOV column only",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"source_name": "ranking_analytics",
				"artifact_family_id": "ranking_analytics",
				"returned_schema": ["Customer", "Revenue", "Quantity", "Average Order Value"],
				"dimensions": ["Customer"],
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
			degraded_reason="",
		)
		self.assertEqual(resolution.mode, "local_grounded_transform")
		self.assertFalse(resolution.self_contained)

	def test_render_local_family_followup_normalizes_alias_projection_columns(self):
		payload = render_local_family_followup(
			request_id="family-followup-aov-only",
			artifact_payload={
				"request_id": "family-followup-aov-only",
				"family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"source_reports": ["Sales Order List"],
				"period": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"dimensions": {
					"entity_dimension": "Customer",
					"primary_metric_key": "revenue",
					"requested_metric_key": "revenue",
					"requested_columns": ["entity", "revenue", "quantity", "average_order_value"],
					"requested_column_alias_map": {
						"customer": "entity",
						"customer name": "entity",
						"aov": "average_order_value",
						"average order value": "average_order_value",
					},
					"requested_top_n": 5,
					"requested_sort_direction": "desc",
				},
				"sections": {
					"ranked_rows": [
						{
							"rank": 1,
							"entity": "Zegyo Mobile Supply House",
							"entity_name": "Zegyo Mobile Supply House",
							"revenue": 9340000.0,
							"quantity": 30.0,
							"average_order_value": 3113333.33,
						}
					],
				},
			},
			requested_columns=["customer name", "average order value"],
			requested_modes=["column_refinement"],
		)
		answer_text = str(payload.get("answer_text") or "").strip()
		self.assertIn("| Rank | Customer | Average Order Value |", answer_text)
		self.assertNotIn("| Rank | Customer | Revenue | Quantity | Average Order Value |", answer_text)
		self.assertNotIn("Summary", answer_text)

	def test_refine_local_family_artifact_updates_composite_projection_metadata(self):
		payload = refine_local_family_artifact(
			request_id="family-followup-refined-composite-projection",
			artifact_payload={
				"request_id": "family-followup-refined-composite-projection",
				"family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"source_reports": ["Sales Order List"],
				"period": {"time_scope": "last_month", "from_date": "2026-03-01", "to_date": "2026-03-31"},
				"dimensions": {
					"entity_dimension": "Customer",
					"source_composite_family_id": "customer_revenue_ranking",
					"source_composite_primary_metric_id": "revenue",
					"source_composite_secondary_metric_ids": ["quantity", "average_order_value"],
					"primary_metric_key": "revenue",
					"requested_metric_key": "revenue",
					"requested_columns": ["entity", "revenue", "quantity", "average_order_value"],
					"requested_column_alias_map": {
						"customer": "entity",
						"revenue": "revenue",
						"aov": "average_order_value",
					},
				},
				"sections": {
					"ranked_rows": [
						{
							"rank": 1,
							"entity": "Zegyo Mobile Supply House",
							"revenue": 9340000.0,
							"quantity": 30.0,
							"average_order_value": 3113333.33,
						}
					]
				},
			},
			requested_columns=["customer", "revenue", "aov"],
			requested_modes=["column_refinement"],
		)
		dimensions = payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else {}
		self.assertEqual(dimensions.get("requested_columns"), ["entity", "revenue", "average_order_value"])
		self.assertEqual(dimensions.get("source_composite_primary_metric_id"), "revenue")
		self.assertEqual(dimensions.get("source_composite_secondary_metric_ids"), ["average_order_value"])
		self.assertEqual(dimensions.get("requested_projection_mode"), "explicit_selection")

	def test_supports_local_family_followup_allows_preserved_time_scope_for_projection(self):
		self.assertTrue(
			supports_local_family_followup(
				{
					"family_id": "ranking_analytics",
					"period": {
						"time_scope": "last_month",
						"from_date": "2026-03-01",
						"to_date": "2026-03-31",
					},
					"dimensions": {
						"requested_metric_key": "revenue",
						"requested_columns": ["entity", "revenue", "quantity", "average_order_value"],
					},
					"sections": {
						"ranked_rows": [
							{
								"rank": 1,
								"entity": "Zegyo Mobile Supply House",
								"revenue": 9340000.0,
								"quantity": 30.0,
								"average_order_value": 3113333.33,
							}
						],
					},
				},
				target_limit=5,
				target_metric="revenue",
				requested_columns=["entity", "revenue", "average_order_value"],
				requested_time_scope="last_month",
				requested_modes=["column_refinement"],
			)
		)

	def test_supports_local_family_followup_rejects_explicit_time_scope_restatement(self):
		self.assertFalse(
			supports_local_family_followup(
				{
					"family_id": "ranking_analytics",
					"period": {
						"time_scope": "last_month",
						"from_date": "2026-03-01",
						"to_date": "2026-03-31",
					},
					"dimensions": {
						"requested_metric_key": "revenue",
						"requested_columns": ["entity", "revenue", "quantity", "average_order_value"],
					},
					"sections": {
						"ranked_rows": [
							{
								"rank": 1,
								"entity": "Zegyo Mobile Supply House",
								"revenue": 9340000.0,
								"quantity": 30.0,
								"average_order_value": 3113333.33,
							}
						],
					},
				},
				target_limit=5,
				target_metric="revenue",
				requested_columns=["entity", "revenue", "average_order_value"],
				requested_time_scope="last_year",
				requested_modes=["column_refinement", "time_scope_restatement"],
			)
		)

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

	def test_build_followup_resolution_upgrades_filter_refinement_to_capability_requery(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["filter_refinement"],
			target_dimension="Status",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User asked to filter the current grounded listing by status.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-filter-requery",
			message="show only completed delivery notes",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Delivery Note List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Invoice", "Posting Date", "Customer", "Status"],
				"returned_schema": ["Invoice", "Posting Date", "Customer", "Status"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "capability_requery")
		self.assertEqual(outcome.target_report, "Delivery Note List")
		self.assertEqual(outcome.target_dimension, "Status")

	def test_build_followup_resolution_infers_time_scope_for_grounded_temporal_refinement(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["presentation_transform"],
			target_dimension="Posting Date",
			target_limit=1,
			sort_direction="desc",
			target_metric="grand total",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User asked for delivery notes from last month, which aligns with the existing grounded data.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-time-scope-inference",
			message="show me delivery notes from last month",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Delivery Note List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Invoice", "Posting Date", "Customer", "Status"],
				"returned_schema": ["Invoice", "Posting Date", "Customer", "Status"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "capability_requery")
		self.assertEqual(outcome.target_report, "Delivery Note List")
		self.assertEqual(outcome.requested_time_scope, "last_month")
		self.assertEqual(outcome.target_limit, 0)


	def test_build_followup_resolution_treats_bare_payment_entry_reask_as_new_query_when_prior_scope_exists(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=[],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User is restating the base payment entry listing.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-payment-entry-bare-reask",
			message="show me payment entries",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Payment Entry List",
				"artifact_family_id": "transaction_listing",
				"date_range": {
					"from_date": "2026-03-01",
					"to_date": "2026-03-31",
				},
				"dimensions": ["Payment Entry", "Posting Date", "Party"],
				"returned_schema": ["Payment Entry", "Posting Date", "Party", "Received Amount"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "new_query")
		self.assertTrue(outcome.self_contained)
		self.assertFalse(outcome.depends_on_grounded_turn)
		self.assertEqual(outcome.requested_time_scope, "")


	def test_build_followup_resolution_clears_projection_noise_for_base_payment_entry_reask(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["column_refinement"],
			target_dimension="Customer",
			target_limit=0,
			sort_direction="",
			target_metric="received amount",
			requested_columns=["payment entry", "posting date", "customer", "received amount"],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User requested payment entries, and the follow-up mode 'column_projection' is appropriate to refine the display.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-payment-entry-projection-noise",
			message="show me payment entries",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Payment Entry List",
				"artifact_family_id": "transaction_listing",
				"date_range": {
					"from_date": "2026-03-01",
					"to_date": "2026-03-31",
				},
				"dimensions": ["Payment Entry"],
				"returned_schema": ["Payment Entry", "Posting Date", "Party", "Received Amount"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "new_query")
		self.assertTrue(outcome.self_contained)
		self.assertFalse(outcome.depends_on_grounded_turn)
		self.assertEqual(list(outcome.requested_modes), [])
		self.assertEqual(outcome.target_dimension, "")
		self.assertEqual(outcome.target_metric, "")
		self.assertEqual(list(outcome.requested_columns), [])


	def test_build_followup_resolution_uses_source_report_when_transaction_listing_family_id_is_blank(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["column_refinement"],
			target_dimension="Customer",
			target_limit=10,
			sort_direction="",
			target_metric="received amount",
			requested_columns=["payment entry", "posting date", "customer", "received amount"],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User asked to show payment entries, and the follow-up is a refinement of the existing result by projecting columns related to customers.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-payment-entry-blank-family-id",
			message="show me payment entries",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Payment Entry List",
				"artifact_family_id": "",
				"date_range": {
					"from_date": "2026-03-01",
					"to_date": "2026-03-31",
				},
				"dimensions": ["Payment Entry"],
				"returned_schema": ["Payment Entry", "Posting Date", "Party", "Received Amount"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "new_query")
		self.assertTrue(outcome.self_contained)
		self.assertEqual(list(outcome.requested_modes), [])

	def test_build_followup_resolution_treats_self_contained_transaction_listing_reask_as_new_query(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=["filter_refinement"],
			target_dimension="Status",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="User restated a full purchase-order query with an explicit status filter.",
		)
		outcome = build_followup_resolution(
			request_id="semantic-followup-purchase-order-self-contained-reask",
			message="show me purchase orders with status To Bill",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Purchase Order List",
				"artifact_family_id": "transaction_listing",
				"date_range": {
					"from_date": "2026-03-01",
					"to_date": "2026-03-31",
				},
				"dimensions": ["Purchase Order", "Transaction Date", "Supplier", "Status"],
				"returned_schema": ["Purchase Order", "Transaction Date", "Supplier", "Grand Total", "Quantity", "Status"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
		)
		self.assertEqual(outcome.mode, "new_query")
		self.assertTrue(outcome.self_contained)
		self.assertFalse(outcome.depends_on_grounded_turn)
		self.assertEqual(outcome.requested_time_scope, "")

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
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

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
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

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
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

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
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

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
		self.assertEqual(payload["resolution_source"]["requested_domains"], "semantic_runtime")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")

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
		self.assertEqual(payload["requested_domains"], [])
		self.assertEqual(payload["resolution_source"]["requested_domains"], "message_fallback_denied")
		self.assertFalse(payload["degraded_message_fallback_allowed"])
		self.assertFalse(payload["degraded_message_fallback_used"])
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

	def test_build_followup_boundary_contract_forces_fresh_query_on_transaction_listing_view_switch(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"show me last 7 sale invoices",
			request_id="followup-boundary-from-context-6e",
			session_id="session-ctx-6e",
			grounded_turn={
				"grounded": True,
				"source_name": "Delivery Note List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date"],
				"metrics": ["Grand Total", "Quantity"],
				"returned_schema": ["Delivery Note", "Posting Date", "Customer", "Grand Total", "Quantity", "Status"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["filter_refinement"],
				target_dimension="Posting Date",
				target_limit=7,
				sort_direction="desc",
				target_metric="grand total",
				requested_columns=["grand_total", "status"],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User is asking for last 7 sale invoices, which is a refinement of the previous delivery notes query.",
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")
		self.assertIn("different governed document-listing target", payload["decision_reason"])

	def test_build_followup_boundary_contract_forces_fresh_query_on_payment_entry_to_supplier_directory_switch(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"give me some supplier list",
			request_id="followup-boundary-from-context-6e-payment-supplier",
			session_id="session-ctx-6e-payment-supplier",
			grounded_turn={
				"grounded": True,
				"source_name": "Payment Entry List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date", "Customer"],
				"metrics": ["Received Amount"],
				"returned_schema": ["Payment Entry", "Posting Date", "Party"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")
		self.assertIn("entity-navigation", payload["decision_reason"])

	def test_build_followup_boundary_contract_forces_fresh_query_on_customer_master_to_payment_entries_switch(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"show me payment entries",
			request_id="followup-boundary-from-context-6e-customer-payment",
			session_id="session-ctx-6e-customer-payment",
			grounded_turn={
				"grounded": True,
				"source_name": "Customer Master List",
				"artifact_family_id": "master_data_lookup",
				"dimensions": ["Customer", "Territory"],
				"metrics": [],
				"returned_schema": ["Customer", "Territory", "Customer Group", "Creation"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")
		self.assertIn("document list", payload["decision_reason"])

	def test_build_followup_boundary_contract_forces_fresh_query_on_customer_master_to_supplier_list_switch(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"give me some supplier list",
			request_id="followup-boundary-from-context-6e-customer-supplier",
			session_id="session-ctx-6e-customer-supplier",
			grounded_turn={
				"grounded": True,
				"source_name": "Customer Master List",
				"artifact_family_id": "master_data_lookup",
				"dimensions": ["Customer", "Territory"],
				"metrics": [],
				"returned_schema": ["Customer", "Territory", "Customer Group", "Creation"],
			},
		)
		payload = contract.to_payload()
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")
		self.assertIn("different entity list", payload["decision_reason"])

	def test_build_followup_boundary_contract_infers_transaction_listing_family_from_report_when_missing(self):
		contract = followup_interpreter_module.build_followup_boundary_contract_from_context(
			"show me last 7 sale invoices",
			request_id="followup-boundary-from-context-6f",
			session_id="session-ctx-6f",
			grounded_turn={
				"grounded": True,
				"source_name": "Delivery Note List",
				"artifact_family_id": "",
				"dimensions": ["Posting Date"],
				"metrics": ["Grand Total", "Quantity"],
				"returned_schema": ["Delivery Note", "Posting Date", "Customer", "Grand Total", "Quantity", "Status"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["filter_refinement"],
				target_dimension="Posting Date",
				target_limit=7,
				sort_direction="desc",
				target_metric="grand total",
				requested_columns=["grand_total", "status"],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User is asking for last 7 sale invoices, which changes the governed listing target.",
			),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["source_family_id"], "transaction_listing")
		self.assertEqual(payload["recommended_boundary_decision"], "force_fresh_query")
		self.assertIn("different governed document-listing target", payload["decision_reason"])

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

	def test_assess_context_isolation_breaks_out_from_payment_entry_to_customer_directory(self):
		result = assess_context_isolation(
			"give me some customer list",
			grounded_turn={
				"grounded": True,
				"source_name": "Payment Entry List",
				"artifact_family_id": "transaction_listing",
				"dimensions": ["Posting Date", "Customer"],
				"metrics": ["Received Amount"],
				"returned_schema": ["Payment Entry", "Posting Date", "Party"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("entity-navigation", result.reason)

	def test_assess_context_isolation_breaks_out_from_customer_master_to_payment_entries(self):
		result = assess_context_isolation(
			"show me payment entries",
			grounded_turn={
				"grounded": True,
				"source_name": "Customer Master List",
				"artifact_family_id": "master_data_lookup",
				"dimensions": ["Customer", "Territory"],
				"metrics": [],
				"returned_schema": ["Customer", "Territory", "Customer Group", "Creation"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("document list", result.reason)

	def test_assess_context_isolation_breaks_out_from_customer_master_to_supplier_list(self):
		result = assess_context_isolation(
			"give me some supplier list",
			grounded_turn={
				"grounded": True,
				"source_name": "Customer Master List",
				"artifact_family_id": "master_data_lookup",
				"dimensions": ["Customer", "Territory"],
				"metrics": [],
				"returned_schema": ["Customer", "Territory", "Customer Group", "Creation"],
			},
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("different entity list", result.reason)

	def test_master_data_lookup_augmentation_infers_entity_grain_from_message(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="master-data-augment-supplier",
			session_id="semantic-master-data",
			intent_class="master_data_lookup",
			candidate_capability_ids=["customer_master_read"],
			candidate_reports=["Customer Master List"],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="as_of_today",
			requested_presentation=["table_presentation"],
			extracted_slots={},
			ambiguity_flags=["ambiguous_business_object"],
			ambiguity_reason="Supplier vs customer scope is unresolved.",
			confidence=0.6,
		)
		augmented = _augment_master_data_lookup_interpretation_from_message(
			message="give me some supplier list",
			interpretation=interpretation,
		)
		self.assertEqual((augmented.extracted_slots or {}).get("entity_grain"), "supplier")
		self.assertIn("ambiguous_business_object", list(augmented.ambiguity_flags))

	def test_master_data_lookup_resolution_executes_supported_inferred_supplier_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="master-data-unsupported-supplier",
			session_id="semantic-master-data",
			intent_class="master_data_lookup",
			candidate_capability_ids=["customer_master_read"],
			candidate_reports=["Customer Master List"],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="as_of_today",
			requested_presentation=["table_presentation"],
			extracted_slots={"entity_grain": "supplier"},
			ambiguity_flags=["ambiguous_business_object"],
			ambiguity_reason="Supplier scope was requested but customer scope was suggested.",
			confidence=0.6,
		)
		outcome = resolve_master_data_lookup_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.clarification_reason_type, "")
		self.assertEqual(outcome.contract.scope_id, "supplier_master")
		self.assertIn("supplier_master_read", list(outcome.interpretation.candidate_capability_ids))
		self.assertNotIn("unsupported_request", list(outcome.interpretation.ambiguity_flags))

	def test_compile_from_fresh_query_message_executes_supported_supplier_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="master-data-pipeline-supplier",
			session_id="semantic-master-data",
			intent_class="master_data_lookup",
			candidate_capability_ids=["customer_master_read"],
			candidate_reports=["Customer Master List"],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="as_of_today",
			requested_presentation=["table_presentation"],
			extracted_slots={},
			ambiguity_flags=["ambiguous_business_object"],
			ambiguity_reason="Supplier was requested but only customer directory was proposed.",
			confidence=0.6,
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=SemanticFreshQueryResult(
				status="low_confidence",
				interpretation=interpretation,
				confidence_threshold=0.72,
				validation_error="Semantic fresh-query interpretation fell below the governed confidence threshold.",
				agent_meta={},
			),
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-master-data",
				user_id="Administrator",
				site_name="test-site",
				message="give me some supplier list",
				recent_messages=[],
			)
		semantic_resolution_contract = (
			pipeline.get("semantic_resolution_contract")
			if isinstance(pipeline.get("semantic_resolution_contract"), dict)
			else {}
		)
		compiler_payload = (
			pipeline.get("fresh_query_compiler")
			if isinstance(pipeline.get("fresh_query_compiler"), dict)
			else {}
		)
		semantic_payload = (
			pipeline.get("fresh_query_interpretation")
			if isinstance(pipeline.get("fresh_query_interpretation"), dict)
			else {}
		)
		semantic_interpretation = (
			semantic_payload.get("interpretation")
			if isinstance(semantic_payload.get("interpretation"), dict)
			else {}
		)
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("entity_grain"), "supplier")
		self.assertEqual(semantic_resolution_contract.get("governed_decision"), "execute")
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("scope_id"), "supplier_master")
		self.assertEqual(semantic_resolution_contract.get("scope_id"), "supplier_master")
		self.assertEqual(semantic_resolution_contract.get("resolved_slots", {}).get("entity_grain"), "supplier")
		self.assertEqual(compiler_payload.get("decision"), "execute")
		self.assertEqual(compiler_payload.get("selected_report"), "Supplier Master List")

	def test_should_skip_artifact_boundary_when_boundary_requires_fresh_query(self):
		self.assertTrue(
			_should_skip_artifact_boundary(
				scope_decision_contract=types.SimpleNamespace(
					governed_scope_status="fresh_query_breakout",
				)
			)
		)

	def test_should_not_skip_artifact_boundary_when_boundary_stays_grounded(self):
		self.assertFalse(
			_should_skip_artifact_boundary(
				scope_decision_contract=types.SimpleNamespace(
					governed_scope_status="grounded_followup",
				)
			)
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

	def test_reasoning_scope_suppression_allowed_for_same_domain_breakout(self):
		decision = build_scope_decision_input(
			force_new_query=True,
			requested_domains=["sales"],
			context_domains=["sales", "customer"],
			primary_domain="sales",
			reason="The request stays within the current governed sales area.",
		)
		self.assertTrue(reasoning_scope_suppression_allowed(decision))

	def test_reasoning_scope_suppression_denied_for_cross_domain_reset(self):
		decision = assess_context_isolation(
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
		self.assertTrue(decision.force_new_query)
		self.assertFalse(reasoning_scope_suppression_allowed(decision))

	def test_reasoning_scope_suppression_denied_for_self_contained_reason_without_domains(self):
		decision = build_scope_decision_input(
			force_new_query=True,
			requested_domains=[],
			context_domains=["sales"],
			primary_domain="sales",
			reason="The request is self-contained and should be treated as a fresh governed ERP question.",
		)
		self.assertFalse(reasoning_scope_suppression_allowed(decision))

	def test_reasoning_preempted_by_followup_refinement_includes_filter_refinement(self):
		self.assertTrue(
			reasoning_preempted_by_followup_refinement(
				types.SimpleNamespace(
					mode="capability_requery",
					requested_modes=["filter_refinement", "table_presentation"],
				)
			)
		)
		self.assertFalse(
			reasoning_preempted_by_followup_refinement(
				types.SimpleNamespace(
					mode="capability_requery",
					requested_modes=["table_presentation"],
				)
			)
		)

	def test_reasoning_preempted_by_followup_refinement_for_self_contained_new_query(self):
		self.assertTrue(
			reasoning_preempted_by_followup_refinement(
				types.SimpleNamespace(
					mode="new_query",
					self_contained=True,
					requested_modes=[],
				)
			)
		)
		self.assertFalse(
			reasoning_preempted_by_followup_refinement(
				types.SimpleNamespace(
					mode="new_query",
					self_contained=False,
					requested_modes=[],
				)
			)
		)

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
		self.assertTrue(result.force_new_query)
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
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("fresh governed ERP question", result.reason)

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
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("fresh governed ERP question", result.reason)

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
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("fresh governed ERP question", result.reason)

	def test_assess_context_isolation_prefers_explicit_ranking_subject_over_stale_semantic_dimension(self):
		result = assess_context_isolation(
			"show top 5 products by revenue last month",
			grounded_turn={
				"grounded": True,
				"source_name": "ranking_analytics",
				"artifact_family_id": "ranking_analytics",
				"dimensions": ["Customer"],
				"known_entities": [
					{"entity_type": "customer", "name": "Zegyo Mobile Supply House", "code": "Zegyo Mobile Supply House"}
				],
				"returned_schema": ["Customer", "Revenue", "Average Order Value"],
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["sort_or_limit", "time_scope_restatement"],
				target_dimension="Customer",
				target_limit=5,
				sort_direction="",
				target_metric="revenue",
				requested_columns=["entity", "revenue", "average_order_value"],
				requested_time_scope="last_month",
				target_capability_id="",
				self_contained=False,
			),
		)
		self.assertTrue(result.force_new_query)
		self.assertFalse(result.out_of_scope)
		self.assertIn("switches the governed ranking subject from customer to product", result.reason)

	def test_build_artifact_continuation_contract_preserves_projection_shape_for_time_scope_restatement(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="ranking-time-scope-projection-preserve",
			mode="capability_requery",
			requested_modes=["time_scope_restatement"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="last_year",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Preserve the governed ranking shape while changing the period.",
		)
		continuation = build_artifact_continuation_contract(
			request_id="ranking-time-scope-projection-preserve",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"dimensions": ["Customer"],
				"metrics": ["Revenue"],
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
			},
			artifact_payload={
				"family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"period": {"time_scope": "last_month", "from_date": "2026-03-01", "to_date": "2026-03-31"},
				"dimensions": {
					"entity_dimension": "Customer",
					"requested_metric_key": "revenue",
					"primary_metric_key": "revenue",
					"requested_columns": ["entity", "revenue", "average_order_value"],
					"requested_top_n": 5,
					"requested_sort_direction": "desc",
				},
				"sections": {
					"ranked_rows": [
						{"rank": 1, "entity": "Zegyo Mobile Supply House", "revenue": 9340000.0, "average_order_value": 3113333.33}
					]
				},
			},
		)
		self.assertTrue(continuation.preserve_projection_shape)
		self.assertFalse(continuation.preserve_rank_membership)
		self.assertEqual(continuation.preserved_requested_columns, ["entity", "revenue", "average_order_value"])

	def test_build_artifact_continuation_contract_derives_composite_context_from_generic_sales_analytics_ranking(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="generic-ranking-composite-derivation",
			mode="capability_requery",
			requested_modes=["column_refinement"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="qty",
			requested_columns=["qty"],
			requested_time_scope="",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Add quantity to the preserved ranking.",
		)
		continuation = build_artifact_continuation_contract(
			request_id="generic-ranking-composite-derivation",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Sales Analytics",
				"artifact_family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"filters": {
					"company": "Enterprise Co",
					"doc_type": "Sales Invoice",
					"tree_type": "Item",
				},
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"dimensions": ["Item"],
				"metrics": ["Sales Amount"],
			},
			artifact_payload={
				"family_id": "ranking_analytics",
				"artifact_type": "normalized_family_artifact",
				"period": {"time_scope": "last_month", "from_date": "2026-03-01", "to_date": "2026-03-31"},
				"filters": {
					"company": "Enterprise Co",
					"doc_type": "Sales Invoice",
					"tree_type": "Item",
				},
				"dimensions": {
					"entity_dimension": "Item",
					"requested_metric_key": "sales_amount",
					"primary_metric_key": "sales_amount",
					"requested_columns": ["entity", "sales_amount"],
					"requested_top_n": 5,
					"requested_sort_direction": "desc",
				},
				"sections": {
					"ranked_rows": [
						{"rank": 1, "entity": "OPPO A58 (6GB 128GB)", "sales_amount": 4780000.0}
					]
				},
			},
		)
		self.assertEqual(continuation.source_composite_family_id, "product_commercial_ranking")
		self.assertEqual(continuation.source_composite_basis, "sales_invoice")
		self.assertEqual(continuation.source_composite_primary_metric_id, "revenue")
		self.assertEqual(continuation.source_composite_subject_alias, "product")

	def test_build_artifact_enrichment_compatibility_contract_allows_composite_requery_for_generic_ranking_metric_union(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="generic-ranking-composite-compatibility",
			mode="capability_requery",
			requested_modes=["column_refinement"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="qty",
			requested_columns=["qty"],
			requested_time_scope="",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Add quantity to the preserved ranking.",
		)
		compatibility = build_artifact_enrichment_compatibility_contract(
			request_id="generic-ranking-composite-compatibility",
			followup_resolution=followup_resolution,
			continuation_contract=types.SimpleNamespace(
				source_family_id="ranking_analytics",
				source_capability_id="sales_read",
				source_report="Sales Analytics",
				preserved_dimension="Item",
				source_dimension="Item",
				source_composite_family_id="product_commercial_ranking",
				source_composite_primary_metric_id="revenue",
			),
			required_metric_keys=["sales_amount", "quantity"],
		)
		self.assertTrue(compatibility.compatible)
		self.assertEqual(compatibility.compatibility_status, "governed_composite_requery_compatible")
		self.assertIn("composite requery", compatibility.reason.lower())

	def test_compile_capability_requery_message_promotes_generic_ranking_followup_to_composite_family(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="generic-ranking-composite-message",
			mode="capability_requery",
			requested_modes=["column_refinement"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="qty",
			requested_columns=["qty"],
			requested_time_scope="",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Add quantity to the preserved ranking.",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="include Qty column in the above table",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Sales Analytics",
				"filters": {"company": "Enterprise Co", "doc_type": "Sales Invoice"},
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"artifact_family_id": "ranking_analytics",
			},
			continuation_contract=types.SimpleNamespace(
				preserved_dimension="Item",
				preserved_metric_key="sales_amount",
				preserved_requested_columns=["entity", "sales_amount"],
				preserved_limit=5,
				preserve_rank_membership=True,
				preserve_rank_order=True,
				preserve_projection_shape=True,
				preserve_date_context=True,
				source_family_id="ranking_analytics",
				source_composite_family_id="product_commercial_ranking",
				source_composite_subject_alias="product",
				source_composite_basis="sales_invoice",
				source_composite_primary_metric_id="revenue",
				source_composite_secondary_metric_ids=[],
				source_composite_time_scope="last_month",
				source_metric_key="sales_amount",
				source_capability_id="sales_read",
				source_report="Sales Analytics",
			),
		)
		self.assertIn("show top 5 products by revenue", message.lower())
		self.assertIn("sales invoices", message.lower())
		self.assertIn("with quantity", message.lower())

	def test_render_normalized_family_response_suppresses_ranking_summary_for_table_first_policy(self):
		artifact = build_normalized_family_artifact_contract(
			request_id="ranking-summary-suppressed",
			family_id="ranking_analytics",
			source_reports=["Sales Analytics"],
			period={"from_date": "2026-03-01", "to_date": "2026-03-31"},
			filters={"doc_type": "Sales Invoice", "tree_type": "Item"},
			dimensions={
				"entity_dimension": "Product",
				"primary_metric_key": "sales_amount",
				"primary_metric_label": "Sales Amount",
				"requested_metric_key": "sales_amount",
				"requested_columns": ["entity", "sales_amount"],
				"suppress_summary_by_default": True,
			},
			metrics={"sales_amount": 4780000.0, "entity_count": 1, "top_value": 4780000.0},
			sections={
				"ranked_rows": [{"rank": 1, "entity": "OPPO A58 (6GB 128GB)", "sales_amount": 4780000.0}],
				"summary": [{"label": "Total Sales Amount", "metric_key": "sales_amount", "amount": 4780000.0}],
			},
		)
		render_outcome = render_normalized_family_response(
			request_id="ranking-summary-suppressed",
			artifact_contract=artifact,
		)
		self.assertIsNotNone(render_outcome.contract)
		blocks = render_outcome.contract.blocks if render_outcome.contract is not None else []
		block_titles = [str(block.get("title") or "") for block in blocks if isinstance(block, dict)]
		self.assertNotIn("Summary", block_titles)
		data_table = next(
			(block for block in blocks if isinstance(block, dict) and str(block.get("block_type") or "").strip() == "data_table"),
			{},
		)
		self.assertEqual(data_table.get("columns"), ["Rank", "Product", "Sales Amount"])

	def test_resolve_composite_candidate_defaults_basis_for_generic_product_metric_expansion(self):
		family_spec, family_resolution = _resolve_composite_candidate(
			message="show top 5 products by revenue last month, show together with Qty column",
			company_name="Enterprise Co",
		)
		self.assertEqual(str(family_spec.get("family_id") or ""), "product_commercial_ranking")
		self.assertIsNotNone(family_resolution)
		self.assertEqual(family_resolution.status, "resolved_family")
		self.assertEqual(family_resolution.requested_basis, "sales_invoice")
		self.assertEqual(family_resolution.requested_primary_metric, "revenue")
		self.assertEqual(family_resolution.requested_secondary_metrics, ["quantity"])

	def test_resolve_composite_candidate_clarifies_generic_single_metric_product_ranking_basis(self):
		family_spec, family_resolution = _resolve_composite_candidate(
			message="show top 5 products by revenue last month",
			company_name="Enterprise Co",
		)
		self.assertEqual(str(family_spec.get("family_id") or ""), "product_commercial_ranking")
		self.assertIsNotNone(family_resolution)
		self.assertEqual(family_resolution.status, "clarify_family_variation")
		self.assertEqual(family_resolution.requested_basis, "")
		self.assertEqual(family_resolution.requested_primary_metric, "revenue")
		self.assertEqual(family_resolution.requested_secondary_metrics, [])

	def test_compile_capability_requery_message_prefers_explicit_last_year_for_composite_ranking_and_does_not_add_unrequested_secondary_metrics(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="composite-last-year-requery",
			mode="capability_requery",
			requested_modes=["time_scope_restatement"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="last_year",
			target_capability_id="sales_read",
			target_report="Sales Analytics",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Restate the governed ranking period without changing the selected columns.",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="I mean last year, not last month",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Sales Analytics",
				"filters": {"company": "Enterprise Co", "basis": "sales_order"},
				"date_range": {"from_date": "2026-03-01", "to_date": "2026-03-31"},
				"artifact_family_id": "ranking_analytics",
			},
			continuation_contract=types.SimpleNamespace(
				preserved_dimension="Customer",
				preserved_metric_key="revenue",
				preserved_requested_columns=["customer", "revenue", "average_order_value"],
				source_requested_columns=["customer", "revenue", "average_order_value"],
				preserved_limit=5,
				preserve_rank_membership=False,
				preserve_rank_order=False,
				preserve_projection_shape=True,
				preserve_date_context=False,
				source_family_id="ranking_analytics",
				source_composite_family_id="customer_revenue_ranking",
				source_composite_subject_alias="customer",
				source_composite_basis="sales_order",
				source_composite_primary_metric_id="revenue",
				source_composite_secondary_metric_ids=["average_order_value"],
				source_composite_time_scope="last_month",
				source_metric_key="revenue",
				source_capability_id="sales_read",
				source_report="Sales Analytics",
			),
		)
		self.assertIn("last year", message.lower())
		self.assertNotIn("last month", message.lower())
		self.assertIn("average order value", message.lower())
		self.assertNotIn("quantity", message.lower())

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

	def test_compile_capability_requery_message_describes_filter_refinement_as_filter(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="filter-requery-message",
			mode="capability_requery",
			requested_modes=["filter_refinement"],
			target_dimension="Status",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="Delivery Note List",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Apply a governed status filter to the current listing.",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="show me delivery notes with status Completed",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Delivery Note List",
				"filters": {"company": "Enterprise Co"},
				"date_range": {},
				"artifact_family_id": "transaction_listing",
			},
			continuation_contract=types.SimpleNamespace(
				preserve_projection_shape=True,
				preserved_requested_columns=["document_name", "posting_date", "customer", "status"],
				source_requested_columns=["document_name", "posting_date", "customer", "status"],
				preserve_date_context=False,
				source_family_id="transaction_listing",
			),
		)
		self.assertIn("apply a governed filter refinement on `status`", message.lower())
		self.assertNotIn("grouped or broken down by `status`", message.lower())
		self.assertNotIn("requested follow-up transforms", message.lower())

	def test_compile_capability_requery_message_uses_minimal_listing_shape_for_temporal_limit_followup(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="listing-requery-message",
			mode="capability_requery",
			requested_modes=["sort_or_limit"],
			target_dimension="Posting Date",
			target_limit=5,
			sort_direction="desc",
			target_metric="Posting Date",
			requested_columns=[],
			requested_time_scope="last_month",
			target_capability_id="fulfillment_read",
			target_report="Delivery Note List",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Requery the current delivery note listing for last month with the requested row limit.",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="show me the last 5 delivery notes from last month",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Delivery Note List",
				"filters": {"company": "Enterprise Co"},
				"date_range": {},
				"artifact_family_id": "transaction_listing",
			},
			continuation_contract=types.SimpleNamespace(
				preserve_projection_shape=True,
				preserved_requested_columns=["document_name", "posting_date", "customer", "status"],
				source_requested_columns=["document_name", "posting_date", "customer", "status"],
				preserved_limit=5,
				preserve_rank_membership=True,
				preserve_rank_order=True,
				preserved_entities=["DN-0001", "DN-0002"],
				preserve_date_context=False,
				source_family_id="transaction_listing",
			),
		)
		lower_message = message.lower()
		self.assertIn("use the report `delivery note list`.", lower_message)
		self.assertIn("use the last month date range.", lower_message)
		self.assertIn("use a row limit of 5 rows.", lower_message)
		self.assertIn("user request: show me the last 5 delivery notes from last month", lower_message)
		self.assertNotIn("grouped or broken down", lower_message)
		self.assertNotIn("ranking scope", lower_message)
		self.assertNotIn("prioritize the metric", lower_message)
		self.assertNotIn("preserve the exact current ranked entities", lower_message)
		self.assertNotIn("requested follow-up transforms", lower_message)

	def test_compile_capability_requery_message_prefers_preserved_date_range_over_report_date_for_transaction_listing(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="listing-requery-message-date-range",
			mode="capability_requery",
			requested_modes=["filter_refinement"],
			target_dimension="Status",
			target_limit=5,
			sort_direction="",
			target_metric="grand total",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="Delivery Note List",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="Apply a governed status filter on the current delivery note listing.",
		)
		session_doc = types.SimpleNamespace(get=lambda key, default=None: [])
		message = compile_capability_requery_message(
			session_doc,
			raw_message="show me delivery notes with status Completed",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Delivery Note List",
				"filters": {"company": "Enterprise Co", "report_date": "2026-03-06"},
				"date_range": {"report_date": "2026-03-06", "from_date": "2026-03-01", "to_date": "2026-03-31"},
				"artifact_family_id": "transaction_listing",
			},
			continuation_contract=types.SimpleNamespace(
				preserve_projection_shape=True,
				preserved_requested_columns=["document_name", "posting_date", "customer", "grand_total", "status"],
				source_requested_columns=["document_name", "posting_date", "customer", "grand_total", "status"],
				preserve_date_context=True,
				source_family_id="transaction_listing",
			),
		)
		lower_message = message.lower()
		self.assertIn("use the date range from 2026-03-01 to 2026-03-31.", lower_message)
		self.assertNotIn("use report_date 2026-03-06.", lower_message)

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

	def test_compile_from_fresh_query_message_seeds_transaction_listing_limit_from_structural_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-limit-seed",
			session_id="delivery-note-limit-seed-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
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
				session_id="delivery-note-limit-seed-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me the last 5 delivery notes",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			5,
		)
		self.assertEqual(
			int(((pipeline.get("compiled_query_request") or {}).get("target_limit") or 0)),
			5,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"",
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("selected_report") or "")),
			"Delivery Note List",
		)

	def test_compile_from_fresh_query_message_clears_synthetic_last_n_days_when_limit_is_structural(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-limit-time-conflict",
			session_id="delivery-note-limit-time-conflict-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="last_5_days",
			requested_presentation=[],
			extracted_slots={
				"from_date": "2026-04-02",
				"to_date": "2026-04-06",
				"filters": {
					"from_date": "2026-04-02",
					"to_date": "2026-04-06",
				},
			},
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
				session_id="delivery-note-limit-time-conflict-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me the last 5 delivery notes",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			5,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"",
		)
		self.assertNotIn("from_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("to_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))

	def test_compile_from_fresh_query_message_clears_latest_time_scope_when_limit_is_document_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="sales-invoice-latest-limit-time-conflict",
			session_id="sales-invoice-latest-limit-time-conflict-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Invoice List"],
			requested_dimensions=["Invoice", "Customer", "Posting Date"],
			requested_metrics=["Grand Total", "Outstanding Amount"],
			requested_time_scope="latest",
			requested_presentation=[],
			extracted_slots={
				"report_date": "2026-04-07",
				"from_date": "2026-04-07",
				"to_date": "2026-04-07",
				"filters": {
					"report_date": "2026-04-07",
					"from_date": "2026-04-07",
					"to_date": "2026-04-07",
				},
			},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
			target_limit=7,
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
				session_id="sales-invoice-latest-limit-time-conflict-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me latest 7 sale invoices",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			7,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"",
		)
		self.assertNotIn("report_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("from_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("to_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))

	def test_compile_from_fresh_query_message_clears_latest_n_time_scope_when_limit_matches_document_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="sales-invoice-latest-n-limit-time-conflict",
			session_id="sales-invoice-latest-n-limit-time-conflict-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Invoice List"],
			requested_dimensions=["Invoice", "Customer", "Posting Date"],
			requested_metrics=["Grand Total", "Outstanding Amount"],
			requested_time_scope="latest_7",
			requested_presentation=[],
			extracted_slots={
				"report_date": "2026-04-07",
				"from_date": "2026-03-31",
				"to_date": "2026-04-07",
				"filters": {
					"report_date": "2026-04-07",
					"from_date": "2026-03-31",
					"to_date": "2026-04-07",
				},
			},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
			target_limit=7,
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
				session_id="sales-invoice-latest-n-limit-time-conflict-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me latest 7 sale invoices",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			7,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"",
		)
		self.assertNotIn("report_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("from_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("to_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))

	def test_compile_from_fresh_query_message_clears_as_of_today_when_latest_n_is_structural_document_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-latest-structural-limit",
			session_id="delivery-note-latest-structural-limit-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note", "Posting Date", "Customer"],
			requested_metrics=["Grand Total", "Quantity"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={
				"report_date": "2026-04-07",
				"from_date": "2026-04-07",
				"to_date": "2026-04-07",
				"filters": {
					"report_date": "2026-04-07",
					"from_date": "2026-04-07",
					"to_date": "2026-04-07",
				},
			},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
			target_limit=5,
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
				session_id="delivery-note-latest-structural-limit-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="give me latest 5 delivery note",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			5,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"",
		)
		self.assertNotIn("report_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("from_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))
		self.assertNotIn("to_date", ((pipeline.get("compiled_query_request") or {}).get("filters") or {}))

	def test_compile_from_fresh_query_message_preserves_explicit_last_n_days_without_limit_seed(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-explicit-time-scope",
			session_id="delivery-note-explicit-time-scope-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="last_5_days",
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
				session_id="delivery-note-explicit-time-scope-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me delivery notes from last 5 days",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			0,
		)
		self.assertEqual(
			str(((pipeline.get("fresh_query_compiler") or {}).get("requested_time_scope") or "")),
			"last_5_days",
		)

	def test_compile_from_fresh_query_message_keeps_explicit_transaction_listing_limit(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-limit-explicit",
			session_id="delivery-note-limit-explicit-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
			target_limit=7,
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
				session_id="delivery-note-limit-explicit-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me the last 5 delivery notes",
				recent_messages=[],
			)
		self.assertEqual(
			int(((pipeline.get("fresh_query_compiler") or {}).get("target_limit") or 0)),
			7,
		)
		self.assertEqual(
			int(((pipeline.get("compiled_query_request") or {}).get("target_limit") or 0)),
			7,
		)

	def test_compile_from_fresh_query_message_grounds_delivery_note_status_filter_from_message(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-status-grounding",
			session_id="delivery-note-status-grounding-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
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
		mocked_frappe = Mock()
		mocked_frappe.get_all.return_value = [
			{"status": "Completed"},
			{"status": "Partially Billed"},
		]
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=semantic_result,
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.frappe",
			mocked_frappe,
		):
			pipeline = compile_from_fresh_query_message(
				session_id="delivery-note-status-grounding-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me delivery notes with status Completed",
				recent_messages=[],
			)
		self.assertEqual(
			((pipeline.get("fresh_query_interpretation") or {}).get("interpretation") or {}).get("extracted_slots", {}).get("filters", {}).get("status"),
			"Completed",
		)
		self.assertEqual(
			((pipeline.get("compiled_query_request") or {}).get("filters") or {}).get("status"),
			"Completed",
		)

	def test_compile_from_fresh_query_message_does_not_ground_unfilterable_customer_value(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="delivery-note-customer-boundary",
			session_id="delivery-note-customer-boundary-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
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
		mocked_frappe = Mock()
		mocked_frappe.get_all.return_value = [
			{"customer": "Acme Trading"},
			{"customer": "Beta Stores"},
		]
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=semantic_result,
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.frappe",
			mocked_frappe,
		):
			pipeline = compile_from_fresh_query_message(
				session_id="delivery-note-customer-boundary-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me delivery notes for customer Acme Trading",
				recent_messages=[],
			)
		self.assertNotIn(
			"customer",
			((pipeline.get("compiled_query_request") or {}).get("filters") or {}),
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

	def test_composite_plan_normalizes_period_parent_scope_for_as_of_aging_steps(self):
		base_interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-fin-summary-composite-period-parent",
			session_id="semantic-fin-summary",
			intent_class="financial_summary",
			candidate_capability_ids=["accounts_receivable_read", "accounts_payable_read"],
			candidate_reports=["Accounts Receivable Summary", "Accounts Payable Summary"],
			requested_dimensions=[],
			requested_metrics=["Outstanding"],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={"composite_profile_context": ["working_capital_health"]},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		resolution_outcome = resolve_financial_summary_interpretation(base_interpretation)
		self.assertIsNotNone(resolution_outcome)
		outcome = plan_composite_read(
			request_id="semantic-fin-summary-composite-period-parent",
			session_id="semantic-fin-summary",
			message="Analyze AR / AP amount and evaluate the company health",
			interpretation=resolution_outcome.interpretation,
			response_policy={},
		)

		self.assertEqual(outcome.status, "execute")
		self.assertEqual(
			[
				str(step.requested_time_scope or "").strip()
				for step in outcome.step_compiler_contracts
			],
			["as_of_today", "as_of_today"],
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
			return_value={"status": "pass", "validation_errors": [], "validation_warnings": [], "completed_steps": 1},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads._composite_semantic_payload",
			return_value={"status": "pass", "errors": [], "warnings": []},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads.render_composite_family_response",
			return_value=fake_render,
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads.build_qwen_runtime_chat_request_config",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.composite_reads.narrate_governed_artifact"
		) as narrative_runtime:
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
		narrative_runtime.assert_not_called()
		self.assertEqual(
			result.get("runtime_payload", {}).get("answer_text"),
			"Working capital looks stable.",
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

	def test_transaction_listing_surface_unsupported_translation_stays_business_natural(self):
		signal = _translate_compiler_signal(
			request_id="transaction-listing-surface-unsupported-signal",
			compiler_reason="Purchase invoice list is not active.",
			compiler_reason_type="transaction_listing_surface_unsupported",
			compiler_details={
				"requested_listing_view": "purchase_invoice",
				"supported_listing_views": [
					"sales_invoice",
					"delivery_note",
					"sales_order",
					"purchase_order",
					"purchase_receipt",
					"payment_entry",
				],
			},
		)
		self.assertEqual(
			signal.user_question,
			"I can't show purchase invoices as a list right now. I can show sales invoices, delivery notes, sales orders, purchase orders, purchase receipts, or payment entries instead. Which one would you like?",
		)
		self.assertEqual(
			signal.suggested_options,
			[
				"sales invoices",
				"delivery notes",
				"sales orders",
				"purchase orders",
				"purchase receipts",
			],
		)

	def test_clarification_reason_preserves_canonical_capability_candidates(self):
		reason = build_clarification_reason_contract_from_sources(
			request_id="clarification-payment-entry-identity",
			compiler_reason="Need confirmation before running the listing.",
			compiler_reason_type="capability_ambiguity",
			compiler_details={
				"capability_candidates": ["collections_read"],
				"canonical_capability_candidates": ["payment_entry_read"],
				"report_candidates": ["Payment Entry List"],
				"scope_id": "payment_entry",
			},
		)
		self.assertIsNotNone(reason)
		payload = reason.to_payload()
		self.assertEqual(payload.get("candidate_capability_ids"), ["collections_read"])
		self.assertEqual(payload.get("canonical_candidate_capability_ids"), ["payment_entry_read"])

	def test_translate_capability_ambiguity_signal_preserves_canonical_capability_candidates(self):
		signal = _translate_compiler_signal(
			request_id="clarification-signal-payment-entry-identity",
			compiler_reason="Need confirmation before running the listing.",
			compiler_reason_type="capability_ambiguity",
			compiler_details={
				"capability_candidates": ["collections_read"],
				"canonical_capability_candidates": ["payment_entry_read"],
				"report_candidates": ["Payment Entry List"],
				"scope_id": "payment_entry",
			},
		)
		payload = signal.to_payload()
		self.assertEqual(payload.get("candidate_capability_ids"), ["collections_read"])
		self.assertEqual(payload.get("canonical_candidate_capability_ids"), ["payment_entry_read"])

	def test_master_data_scope_unsupported_translation_stays_plain_and_does_not_overpromise_detail_path(self):
		signal = _translate_compiler_signal(
			request_id="master-data-scope-unsupported-signal",
			compiler_reason="Supplier directory is not active.",
			compiler_reason_type="master_data_scope_unsupported",
			compiler_details={
				"requested_entity_grain": "supplier",
				"supported_entity_grains": ["customer"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"I can list customers right now. I can't open suppliers as a list yet.",
		)
		self.assertEqual(signal.suggested_options, ["customers"])

	def test_entity_grain_display_label_uses_governed_registry(self):
		self.assertEqual(entity_grain_display_label("customer"), "customer")
		self.assertEqual(entity_grain_display_label("customer", plural=True), "customers")
		self.assertEqual(entity_grain_display_label("supplier", plural=True), "suppliers")

	def test_listing_view_display_label_uses_governed_scope_registry(self):
		self.assertEqual(listing_view_display_label("payment_entry"), "payment entries")
		self.assertEqual(listing_view_display_label("purchase_order"), "purchase orders")
		self.assertEqual(listing_view_display_label("sales_invoice", lowercase=False), "Sales Invoices")

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

	def test_deterministic_family_surface_does_not_collapse_purchase_invoices_into_sales_invoices(self):
		contract = _deterministic_family_surface_interpretation(
			request_id="semantic-listing-purchase-fallback",
			session_id="semantic-listing",
			message="show me purchase invoices",
			confidence_threshold=0.72,
		)
		self.assertIsNotNone(contract)
		self.assertEqual(contract.intent_class, "transaction_listing")
		self.assertEqual(contract.extracted_slots.get("listing_view"), "purchase_invoice")
		self.assertEqual(list(contract.candidate_capability_ids), ["purchase_invoice_read"])
		self.assertEqual(list(contract.candidate_reports), ["Purchase Invoice List"])
		self.assertIn("Purchase Invoice", contract.requested_dimensions)
		self.assertIn("Supplier", contract.requested_dimensions)

	def test_deterministic_family_surface_executes_purchase_receipts_from_metadata(self):
		contract = _deterministic_family_surface_interpretation(
			request_id="semantic-listing-purchase-receipt-fallback",
			session_id="semantic-listing",
			message="show me purchase receipts",
			confidence_threshold=0.72,
		)
		self.assertIsNotNone(contract)
		self.assertEqual(contract.intent_class, "transaction_listing")
		self.assertEqual(contract.extracted_slots.get("listing_view"), "purchase_receipt")
		self.assertEqual(list(contract.candidate_capability_ids), ["purchase_receipt_read"])
		self.assertEqual(list(contract.candidate_reports), ["Purchase Receipt List"])
		self.assertIn("Purchase Receipt", contract.requested_dimensions)
		self.assertIn("Supplier", contract.requested_dimensions)

	def test_transaction_listing_resolution_executes_supported_purchase_invoice_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-purchase-supported",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Invoice List"],
			requested_dimensions=["Invoice"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={"listing_view": "purchase_invoice"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.scope_id, "purchase_invoice")
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "purchase_invoice")
		self.assertEqual(list(outcome.interpretation.candidate_reports), ["Purchase Invoice List"])
		self.assertEqual(list(outcome.interpretation.candidate_capability_ids), ["purchase_invoice_read"])
		self.assertEqual(list(outcome.interpretation.canonical_candidate_capability_ids), ["purchase_invoice_read"])
		self.assertEqual(list(outcome.interpretation.requested_dimensions), ["Invoice"])
		self.assertEqual(list(outcome.interpretation.requested_metrics), ["Grand Total"])

	def test_transaction_listing_resolution_executes_payment_entry_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-payment-entry",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={"listing_view": "payment_entry"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "payment_entry")
		self.assertEqual(outcome.contract.scope_id, "payment_entry")
		self.assertEqual(outcome.interpretation.extracted_slots.get("scope_id"), "payment_entry")
		self.assertEqual(list(outcome.interpretation.candidate_capability_ids), ["collections_read"])
		self.assertEqual(list(outcome.interpretation.canonical_candidate_capability_ids), ["payment_entry_read"])
		self.assertEqual(list(outcome.contract.canonical_candidate_capability_ids), ["payment_entry_read"])
		self.assertEqual(list(outcome.interpretation.candidate_reports), ["Payment Entry List"])
		self.assertEqual(list(outcome.interpretation.requested_dimensions), ["Payment Entry", "Customer"])
		self.assertEqual(list(outcome.interpretation.requested_metrics), ["Received Amount"])

	def test_transaction_listing_resolution_executes_purchase_receipt_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-purchase-receipt",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={"listing_view": "purchase_receipt"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "purchase_receipt")
		self.assertEqual(outcome.contract.scope_id, "purchase_receipt")
		self.assertEqual(outcome.interpretation.extracted_slots.get("scope_id"), "purchase_receipt")
		self.assertEqual(list(outcome.interpretation.candidate_capability_ids), ["purchase_receipt_read"])
		self.assertEqual(list(outcome.interpretation.canonical_candidate_capability_ids), ["purchase_receipt_read"])
		self.assertEqual(list(outcome.contract.canonical_candidate_capability_ids), ["purchase_receipt_read"])
		self.assertEqual(list(outcome.interpretation.candidate_reports), ["Purchase Receipt List"])
		self.assertEqual(list(outcome.interpretation.requested_dimensions), ["Purchase Receipt", "Supplier", "Status"])
		self.assertEqual(list(outcome.interpretation.requested_metrics), ["Grand Total", "Quantity"])

	def test_compile_from_fresh_query_message_reconciles_explicit_purchase_invoice_view(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "transaction_listing",
					"candidate_capability_ids": ["sales_read"],
					"candidate_reports": ["Sales Invoice List"],
					"requested_dimensions": ["Invoice"],
					"requested_metrics": ["Grand Total"],
					"requested_time_scope": "as_of_today",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 1.0,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-listing-purchase-runtime",
				user_id="Administrator",
				site_name="test-site",
				message="show me purchase invoices",
				recent_messages=[],
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		semantic_interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
		semantic_resolution_contract = pipeline.get("semantic_resolution_contract") if isinstance(pipeline.get("semantic_resolution_contract"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("listing_view"), "purchase_invoice")
		self.assertEqual(semantic_resolution_contract.get("governed_decision"), "execute")
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("scope_id"), "purchase_invoice")
		self.assertEqual(list(semantic_interpretation.get("candidate_capability_ids") or []), ["purchase_invoice_read"])
		self.assertEqual(list(semantic_interpretation.get("candidate_reports") or []), ["Purchase Invoice List"])
		self.assertEqual(semantic_resolution_contract.get("scope_id"), "purchase_invoice")
		self.assertEqual(semantic_resolution_contract.get("resolved_slots", {}).get("listing_view"), "purchase_invoice")
		self.assertEqual(compiler_payload.get("decision"), "execute")

	def test_compile_from_fresh_query_message_preserves_explicit_today_for_payment_entry_listing(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "transaction_listing",
					"candidate_capability_ids": [],
					"candidate_reports": [],
					"requested_dimensions": [],
					"requested_metrics": [],
					"requested_time_scope": "as_of_today",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {
						"report_date": "2026-04-14"
					},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 1.0,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-listing-payment-entry-explicit-today",
				user_id="Administrator",
				site_name="test-site",
				message="show me payment entries today",
				recent_messages=[],
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		semantic_interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("listing_view"), "payment_entry")
		self.assertEqual(semantic_interpretation.get("requested_time_scope"), "as_of_today")

	def test_compile_from_fresh_query_message_resolves_payment_entry_listing(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "transaction_listing",
					"candidate_capability_ids": [],
					"candidate_reports": [],
					"requested_dimensions": [],
					"requested_metrics": [],
					"requested_time_scope": "as_of_today",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 1.0,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-listing-payment-entry-runtime",
				user_id="Administrator",
				site_name="test-site",
				message="show me payment entries",
				recent_messages=[],
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		semantic_interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
		semantic_resolution_contract = pipeline.get("semantic_resolution_contract") if isinstance(pipeline.get("semantic_resolution_contract"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		compiled_request_payload = pipeline.get("compiled_query_request") if isinstance(pipeline.get("compiled_query_request"), dict) else {}
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("listing_view"), "payment_entry")
		self.assertEqual(semantic_interpretation.get("requested_time_scope"), "")
		self.assertEqual(semantic_resolution_contract.get("governed_decision"), "execute")
		self.assertEqual(semantic_interpretation.get("extracted_slots", {}).get("scope_id"), "payment_entry")
		self.assertEqual(semantic_resolution_contract.get("scope_id"), "payment_entry")
		self.assertEqual(semantic_resolution_contract.get("resolved_slots", {}).get("listing_view"), "payment_entry")
		self.assertEqual(semantic_interpretation.get("canonical_candidate_capability_ids"), ["payment_entry_read"])
		self.assertEqual(semantic_resolution_contract.get("canonical_candidate_capability_ids"), ["payment_entry_read"])
		self.assertEqual(compiler_payload.get("selected_report"), "Payment Entry List")
		self.assertEqual(compiler_payload.get("capability_id"), "collections_read")
		self.assertEqual(compiler_payload.get("canonical_capability_id"), "payment_entry_read")
		self.assertEqual(compiled_request_payload.get("canonical_capability_id"), "payment_entry_read")

	def test_compile_from_fresh_query_message_normalizes_payment_entry_default_metric_bundle(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "transaction_listing",
					"candidate_capability_ids": ["collections_read"],
					"candidate_reports": ["Payment Entry List"],
					"requested_dimensions": ["Payment Entry", "Posting Date", "Customer"],
					"requested_metrics": ["Total Allocated Amount", "Received Amount"],
					"requested_time_scope": "",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {"listing_view": "payment_entry"},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 1.0,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-listing-payment-entry-default-metric-bundle",
				user_id="Administrator",
				site_name="test-site",
				message="show me payment entries",
				recent_messages=[],
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		semantic_interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		self.assertEqual(semantic_interpretation.get("requested_metrics"), ["Received Amount"])
		self.assertEqual(compiler_payload.get("requested_metrics"), ["Received Amount"])
		self.assertEqual(compiler_payload.get("selected_report"), "Payment Entry List")

	def test_compile_from_fresh_query_message_preserves_explicit_payment_entry_metric(self):
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
			return_value={
				"ok": True,
				"interpretation": {
					"intent_class": "transaction_listing",
					"candidate_capability_ids": ["collections_read"],
					"candidate_reports": ["Payment Entry List"],
					"requested_dimensions": ["Payment Entry", "Posting Date", "Customer"],
					"requested_metrics": ["Total Allocated Amount", "Received Amount"],
					"requested_time_scope": "",
					"requested_presentation": ["table_presentation"],
					"extracted_slots": {"listing_view": "payment_entry"},
					"ambiguity_flags": [],
					"ambiguity_reason": "",
					"confidence": 1.0,
				},
				"agent_meta": {},
			},
		):
			pipeline = compile_from_fresh_query_message(
				session_id="semantic-listing-payment-entry-explicit-metric",
				user_id="Administrator",
				site_name="test-site",
				message="show me payment entries by total allocated amount",
				recent_messages=[],
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		semantic_interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		self.assertEqual(semantic_interpretation.get("requested_metrics"), ["Total Allocated Amount"])
		self.assertEqual(compiler_payload.get("requested_metrics"), ["Total Allocated Amount"])
		self.assertEqual(compiler_payload.get("selected_report"), "Payment Entry List")

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

	def test_transaction_listing_resolution_uses_structured_fulfillment_capability(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-2b",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.89,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "delivery_note")
		self.assertEqual(outcome.contract.resolution_source.get("listing_view"), "semantic_runtime")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["fulfillment_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Delivery Note List"])
		self.assertEqual(outcome.interpretation.requested_dimensions, ["Delivery Note"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Grand Total", "Quantity"])

	def test_fulfillment_transaction_listing_defaults_do_not_use_concept_report_override(self):
		defaults = capability_fresh_query_defaults("fulfillment_read", intent_class="transaction_listing")
		self.assertEqual(defaults.get("default_report_name"), "Delivery Note List")
		self.assertFalse(
			isinstance(defaults.get("report_overrides_by_concept"), dict)
			and defaults.get("report_overrides_by_concept"),
			"Fulfillment transaction-listing defaults must not steer report selection from broad message concepts.",
		)

	def test_fulfillment_trend_defaults_admit_delivery_note_trends_narrowly(self):
		defaults = capability_fresh_query_defaults("fulfillment_read", intent_class="trend_analysis")
		self.assertEqual(defaults.get("default_report_name"), "Delivery Note Trends")
		self.assertEqual(defaults.get("default_dimensions"), ["Customer"])
		self.assertEqual(defaults.get("default_metrics"), ["Delivered Amount", "Delivered Quantity"])
		self.assertEqual(defaults.get("default_time_scope"), "current_fiscal_year_to_date")
		self.assertEqual(
			defaults.get("metric_overrides_by_canonical_key", {}).get("sales_amount"),
			["Delivered Amount"],
		)
		self.assertEqual(
			defaults.get("metric_overrides_by_canonical_key", {}).get("quantity"),
			["Delivered Quantity"],
		)

	def test_semantic_resolution_registry_time_scope_admits_last_year(self):
		registry = load_semantic_resolution_registry()
		slot_definitions = registry.get("slot_definitions") if isinstance(registry.get("slot_definitions"), list) else []
		time_scope_values = []
		for item in slot_definitions:
			if not isinstance(item, dict):
				continue
			if str(item.get("slot_name") or "").strip() == "time_scope":
				time_scope_values = [
					str(value or "").strip()
					for value in (item.get("allowed_values") or [])
					if str(value or "").strip()
				]
				break
		self.assertIn("last_year", time_scope_values)

	def test_semantic_resolution_registry_time_scope_admits_open_fiscal_year_to_date(self):
		registry = load_semantic_resolution_registry()
		slot_definitions = registry.get("slot_definitions") if isinstance(registry.get("slot_definitions"), list) else []
		time_scope_values = []
		for item in slot_definitions:
			if not isinstance(item, dict):
				continue
			if str(item.get("slot_name") or "").strip() == "time_scope":
				time_scope_values = [
					str(value or "").strip()
					for value in (item.get("allowed_values") or [])
					if str(value or "").strip()
				]
				break
		self.assertIn("open_fiscal_year_to_date", time_scope_values)

	def test_financial_statement_defaults_use_open_fiscal_year_to_date(self):
		statement_defaults = capability_fresh_query_defaults(
			"financial_statement_read",
			intent_class="financial_statement",
		)
		summary_defaults = capability_fresh_query_defaults(
			"financial_statement_read",
			intent_class="financial_summary",
		)
		self.assertEqual(statement_defaults.get("default_time_scope"), "open_fiscal_year_to_date")
		self.assertEqual(summary_defaults.get("default_time_scope"), "open_fiscal_year_to_date")

	def test_financial_statement_default_reconciler_uses_open_period_when_no_time_is_requested(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-default-period",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_period",
			requested_presentation=[],
			extracted_slots={"statement_variant": "profit_and_loss"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = _reconcile_financial_statement_default_time_scope_from_message(
			message="P & L",
			interpretation=interpretation,
		)
		self.assertEqual(outcome.requested_time_scope, "open_fiscal_year_to_date")

	def test_financial_statement_default_reconciler_preserves_explicit_time_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-explicit-period",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_period",
			requested_presentation=[],
			extracted_slots={"statement_variant": "profit_and_loss"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = _reconcile_financial_statement_default_time_scope_from_message(
			message="show P&L this month",
			interpretation=interpretation,
		)
		self.assertEqual(outcome.requested_time_scope, "current_period")

	def test_trend_analytics_family_admits_delivery_note_trends_and_fulfillment_capability(self):
		spec = get_report_family_spec("trend_analytics")
		self.assertIn("fulfillment_read", spec.get("capability_ids") or [])
		self.assertIn("Delivery Note Trends", spec.get("report_names") or [])
		self.assertIn("delivery_note_trends", spec.get("source_report_families") or [])

	def test_delivery_note_trends_report_contract_is_explicit(self):
		spec = get_report_spec("Delivery Note Trends")
		self.assertEqual(
			spec.get("required_filters"),
			["company", "fiscal_year", "period", "based_on"],
		)
		defaultable = {
			str(item.get("fieldname") or "").strip(): str(item.get("strategy") or "").strip()
			for item in (spec.get("defaultable_filters") or [])
			if isinstance(item, dict)
		}
		self.assertEqual(defaultable.get("company"), "single_company_invariant")
		self.assertEqual(defaultable.get("fiscal_year"), "current_fiscal_year_name")
		self.assertEqual(defaultable.get("period"), "compiler_default")
		self.assertEqual(defaultable.get("based_on"), "compiler_default")
		self.assertEqual(spec.get("supported_intent_classes"), ["trend_analysis"])
		self.assertEqual(spec.get("supported_dimensions"), ["Customer", "Period"])
		self.assertEqual(spec.get("supported_metrics"), ["Delivered Amount", "Delivered Quantity"])
		self.assertIn("fulfillment", spec.get("semantic_tags") or [])
		self.assertIn("delivery", spec.get("semantic_tags") or [])
		self.assertIn("shipment", spec.get("semantic_tags") or [])
		self.assertIn("trend", spec.get("semantic_tags") or [])

	def test_transaction_listing_delivery_note_slot_aliases_stay_explicit(self):
		registry = load_semantic_resolution_registry()
		alias_maps = registry.get("alias_maps") if isinstance(registry.get("alias_maps"), dict) else {}
		listing_aliases = alias_maps.get("listing_view") if isinstance(alias_maps.get("listing_view"), list) else []
		delivery_aliases = []
		for entry in listing_aliases:
			if not isinstance(entry, dict):
				continue
			if str(entry.get("canonical_value") or "").strip() == "delivery_note":
				delivery_aliases = [str(value or "").strip() for value in (entry.get("aliases") or []) if str(value or "").strip()]
				break
		self.assertEqual(delivery_aliases, ["delivery note", "delivery notes"])

	def test_transaction_listing_family_markers_do_not_add_delivery_phrase_routing(self):
		spec = get_report_family_spec("transaction_listing")
		routing_hints = spec.get("routing_hints") if isinstance(spec.get("routing_hints"), dict) else {}
		markers = {
			str(value or "").strip()
			for value in (routing_hints.get("intent_markers") or [])
			if str(value or "").strip()
		}
		self.assertFalse(
			{"delivery list", "recent deliveries", "latest deliveries", "delivery notes"} & markers
		)

	def test_phase8_quantity_recovery_seed_uses_retry_safe_session_save(self):
		doc = types.SimpleNamespace(name="phase8-doc")
		calls = {"save_session": 0}

		def _build_recovery_contract(**kwargs):
			return types.SimpleNamespace(to_payload=lambda: {"type": "qwen_artifact_enrichment_recovery_contract", **kwargs})

		def _append_message(_doc, _role, _content):
			return None

		def _append_tool_payload(_doc, _payload):
			return None

		def _assistant_text_payload(text):
			return text

		def _save_session(target_doc, *, ignore_permissions=False):
			self.assertIs(target_doc, doc)
			self.assertFalse(ignore_permissions)
			calls["save_session"] += 1

		doc.save = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("raw doc.save must not be called"))

		_seed_quantity_recovery_session(
			doc,
			request_prefix="phase8-seed-test",
			top_n=5,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			build_artifact_enrichment_recovery_contract=_build_recovery_contract,
			save_session=_save_session,
		)
		self.assertEqual(calls["save_session"], 1)

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

	def test_compiler_executes_transaction_listing_delivery_note(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-3b",
			session_id="semantic-listing",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.86,
		)
		outcome = compile_fresh_query(
			request_id="semantic-listing-3b",
			session_id="semantic-listing",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Delivery Note List")
		self.assertEqual(outcome.compiler_contract.capability_id, "fulfillment_read")
		self.assertEqual(
			outcome.compiler_contract.governed_resolution_details.get(
				"semantic_resolution_contract", {}
			).get("resolved_slots", {}).get("listing_view"),
			"delivery_note",
		)

	def test_compiler_applies_last_month_time_scope_to_direct_query_delivery_note_listing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-date-1",
			session_id="semantic-listing-date",
			intent_class="transaction_listing",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note List"],
			requested_dimensions=["Delivery Note"],
			requested_metrics=["Grand Total"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = compile_fresh_query(
			request_id="semantic-listing-date-1",
			session_id="semantic-listing-date",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Delivery Note List")
		self.assertEqual(
			outcome.compiler_contract.completed_filters.get("from_date"),
			"2026-03-01",
		)
		self.assertEqual(
			outcome.compiler_contract.completed_filters.get("to_date"),
			"2026-03-31",
		)
		self.assertEqual(
			(outcome.compiled_request_contract.to_payload() if outcome.compiled_request_contract else {}).get("filters", {}).get("from_date"),
			"2026-03-01",
		)
		self.assertEqual(
			(outcome.compiled_request_contract.to_payload() if outcome.compiled_request_contract else {}).get("filters", {}).get("to_date"),
			"2026-03-31",
		)

	def test_compiler_applies_explicit_slot_dates_to_direct_query_sales_invoice_listing(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-listing-date-2",
			session_id="semantic-listing-date",
			intent_class="transaction_listing",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Invoice List"],
			requested_dimensions=["Invoice"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={
				"from_date": "2026-03-01",
				"to_date": "2026-03-15",
			},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = compile_fresh_query(
			request_id="semantic-listing-date-2",
			session_id="semantic-listing-date",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Sales Invoice List")
		self.assertEqual(
			outcome.compiler_contract.completed_filters.get("from_date"),
			"2026-03-01",
		)
		self.assertEqual(
			outcome.compiler_contract.completed_filters.get("to_date"),
			"2026-03-15",
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

	@patch("ai_assistant_ui.qwen_chat.compiler._today_date", return_value=__import__("datetime").date(2026, 4, 16))
	@patch("ai_assistant_ui.qwen_chat.compiler._today_iso", return_value="2026-04-16")
	def test_compiler_uses_last_closed_period_for_profit_and_loss_defaults(self, _mock_today_iso, _mock_today_date):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-open-period-pnl",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = compile_fresh_query(
			request_id="semantic-financial-open-period-pnl",
			session_id="semantic-financial",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("period_start_date"), "2025-04-01")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("period_end_date"), "2026-04-16")

	@patch("ai_assistant_ui.qwen_chat.compiler._today_date", return_value=__import__("datetime").date(2026, 4, 16))
	@patch("ai_assistant_ui.qwen_chat.compiler._today_iso", return_value="2026-04-16")
	def test_compiler_uses_cross_fiscal_year_bounds_for_cash_flow_open_period(self, _mock_today_iso, _mock_today_date):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-financial-open-period-cash-flow",
			session_id="semantic-financial",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Cash Flow"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		outcome = compile_fresh_query(
			request_id="semantic-financial-open-period-cash-flow",
			session_id="semantic-financial",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("from_fiscal_year"), "FY-2026")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("to_fiscal_year"), "FY-2027")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("period_start_date"), "2025-04-01")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("period_end_date"), "2026-04-16")

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

	def test_trend_resolution_prefers_fulfillment_capability_defaults_genericly(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-fulfillment-1",
			session_id="semantic-trend-fulfillment",
			intent_class="trend_analysis",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.8,
		)
		outcome = resolve_trend_analysis_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "sales_amount")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["fulfillment_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Delivery Note Trends"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Delivered Amount"])

	def test_trend_resolution_maps_quantity_to_fulfillment_trend_metric(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-fulfillment-2",
			session_id="semantic-trend-fulfillment",
			intent_class="trend_analysis",
			candidate_capability_ids=["fulfillment_read"],
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
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "quantity")
		self.assertEqual(outcome.interpretation.candidate_reports, ["Delivery Note Trends"])
		self.assertEqual(outcome.interpretation.requested_metrics, ["Delivered Quantity"])

	def test_delivery_note_trends_family_adapter_uses_existing_trend_family_contract(self):
		compiler_contract = {
			"request_id": "adapter-trend-fulfillment-1",
			"capability_id": "fulfillment_read",
			"selected_report": "Delivery Note Trends",
			"requested_dimensions": ["Customer"],
			"requested_metrics": ["Delivered Amount"],
			"requested_time_scope": "current_fiscal_year_to_date",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Delivery Note Trends",
						"filters": {
							"company": "Enterprise Co",
							"fiscal_year": "FY-2026",
							"period": "Monthly",
							"based_on": "Customer",
						},
					},
					"output_obj": {
						"result": {
							"columns": [
								{"fieldname": "customer", "label": "Customer"},
								{"fieldname": "currency", "label": "Currency"},
								{"fieldname": "jan_(qty)", "label": "Jan (Qty)"},
								{"fieldname": "jan_(amt)", "label": "Jan (Amt)"},
								{"fieldname": "feb_(qty)", "label": "Feb (Qty)"},
								{"fieldname": "feb_(amt)", "label": "Feb (Amt)"},
								{"fieldname": "total(qty)", "label": "Total(Qty)"},
								{"fieldname": "total(amt)", "label": "Total(Amt)"},
							],
							"data": [
								{
									"customer": "Alpha",
									"currency": "MMK",
									"jan_(qty)": 5,
									"jan_(amt)": 500,
									"feb_(qty)": 3,
									"feb_(amt)": 300,
									"total(qty)": 8,
									"total(amt)": 800,
								},
								{
									"customer": "'Total'",
									"currency": None,
									"jan_(qty)": 5,
									"jan_(amt)": 500,
									"feb_(qty)": 3,
									"feb_(amt)": 300,
									"total(qty)": 8,
									"total(amt)": 800,
								},
							],
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-trend-fulfillment-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="trend_analysis",
			preferred_family_id="trend_analytics",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		metrics = dict(outcome.artifact_contract.metrics)
		sections = dict(outcome.artifact_contract.sections)
		period = dict(outcome.artifact_contract.period)
		self.assertEqual(dimensions.get("primary_metric_key"), "sales_amount")
		self.assertEqual(dimensions.get("primary_metric_label"), "Delivered Amount")
		self.assertEqual(dimensions.get("time_grain"), "monthly")
		self.assertEqual(metrics.get("sales_amount"), 800.0)
		self.assertEqual(period.get("fiscal_year"), "FY-2026")
		self.assertEqual(period.get("from_fiscal_year"), "FY-2026")
		self.assertEqual(period.get("to_fiscal_year"), "FY-2026")
		self.assertEqual(len(sections.get("period_series") or []), 2)

	def test_delivery_note_trends_family_adapter_uses_matching_quantity_label_when_quantity_selected(self):
		compiler_contract = {
			"request_id": "adapter-trend-fulfillment-1b",
			"capability_id": "fulfillment_read",
			"selected_report": "Delivery Note Trends",
			"requested_dimensions": ["Customer", "Period"],
			"requested_metrics": ["Delivered Amount", "Delivered Quantity"],
			"requested_time_scope": "last_year",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Delivery Note Trends",
						"filters": {
							"company": "Enterprise Co",
							"fiscal_year": "FY-2025",
							"period": "Monthly",
							"based_on": "Customer",
						},
					},
					"output_obj": {
						"result": {
							"columns": [
								{"fieldname": "customer", "label": "Customer"},
								{"fieldname": "mar_(qty)", "label": "Mar (Qty)"},
								{"fieldname": "mar_(amt)", "label": "Mar (Amt)"},
								{"fieldname": "total(qty)", "label": "Total(Qty)"},
								{"fieldname": "total(amt)", "label": "Total(Amt)"},
							],
							"data": [
								{
									"customer": "Alpha",
									"mar_(qty)": 41,
									"mar_(amt)": 2446000,
									"total(qty)": 41,
									"total(amt)": 2446000,
								},
								{
									"customer": "'Total'",
									"mar_(qty)": 41,
									"mar_(amt)": 2446000,
									"total(qty)": 41,
									"total(amt)": 2446000,
								},
							],
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-trend-fulfillment-1b",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="trend_analysis",
			preferred_family_id="trend_analytics",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		metrics = dict(outcome.artifact_contract.metrics)
		sections = dict(outcome.artifact_contract.sections)
		self.assertEqual(dimensions.get("primary_metric_key"), "quantity")
		self.assertEqual(dimensions.get("primary_metric_label"), "Delivered Quantity")
		self.assertEqual(metrics.get("quantity"), 41.0)
		self.assertEqual((sections.get("summary") or [])[0].get("label"), "Total Delivered Quantity")

	def test_trend_family_validation_accepts_current_fiscal_year_name_without_date_range(self):
		artifact = build_normalized_family_artifact(
			request_id="adapter-trend-fulfillment-validate",
			compiler_contract={
				"request_id": "adapter-trend-fulfillment-validate",
				"capability_id": "fulfillment_read",
				"selected_report": "Delivery Note Trends",
				"requested_dimensions": ["Customer"],
				"requested_metrics": ["Delivered Amount"],
				"requested_time_scope": "current_fiscal_year_to_date",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Delivery Note Trends",
							"filters": {
								"company": "Enterprise Co",
								"fiscal_year": "FY-2026",
								"period": "Monthly",
								"based_on": "Customer",
							},
						},
						"output_obj": {
						"result": {
							"columns": [
								{"fieldname": "customer", "label": "Customer"},
								{"fieldname": "jan_(amt)", "label": "Jan (Amt)"},
								{"fieldname": "total(amt)", "label": "Total(Amt)"},
							],
							"data": [
								{"customer": "Alpha", "jan_(amt)": 500, "total(amt)": 500},
								{"customer": "'Total'", "jan_(amt)": 500, "total(amt)": 500},
							],
						}
						},
					}
				]
			},
			intent_class="trend_analysis",
			preferred_family_id="trend_analytics",
		).artifact_contract
		with patch("ai_assistant_ui.qwen_chat.family_validator._current_fiscal_year_name", return_value="FY-2026"):
			validation = validate_normalized_family_artifact(
				request_id="adapter-trend-fulfillment-validate",
				compiler_contract={
					"request_id": "adapter-trend-fulfillment-validate",
					"capability_id": "fulfillment_read",
					"selected_report": "Delivery Note Trends",
					"requested_dimensions": ["Customer"],
					"requested_metrics": ["Delivered Amount"],
					"requested_time_scope": "current_fiscal_year_to_date",
				},
				artifact_contract=artifact,
				family_id="trend_analytics",
				adapter_errors=[],
				adapter_warnings=[],
			)
		self.assertEqual(validation.status, "pass")

	def test_trend_family_validation_accepts_previous_fiscal_year_name_for_last_year(self):
		with patch("ai_assistant_ui.qwen_chat.family_validator._previous_fiscal_year_name", return_value="FY-2025"):
			artifact = build_normalized_family_artifact(
				request_id="adapter-trend-fulfillment-validate-last-year",
				compiler_contract={
					"request_id": "adapter-trend-fulfillment-validate-last-year",
					"capability_id": "fulfillment_read",
					"selected_report": "Delivery Note Trends",
					"requested_dimensions": ["Customer"],
					"requested_metrics": ["Delivered Amount"],
					"requested_time_scope": "last_year",
				},
				runtime_payload={
					"tool_trace": [
						{
							"tool": "erp_fac-generate_report",
							"detail_obj": {
								"report_name": "Delivery Note Trends",
								"filters": {
									"company": "Enterprise Co",
									"fiscal_year": "FY-2025",
									"period": "Monthly",
									"based_on": "Customer",
								},
							},
							"output_obj": {
								"result": {
									"columns": [
										{"fieldname": "customer", "label": "Customer"},
										{"fieldname": "jan_(amt)", "label": "Jan (Amt)"},
										{"fieldname": "total(amt)", "label": "Total(Amt)"},
									],
									"data": [
										{"customer": "Alpha", "jan_(amt)": 500, "total(amt)": 500},
										{"customer": "'Total'", "jan_(amt)": 500, "total(amt)": 500},
									],
								}
							},
						}
					]
				},
				intent_class="trend_analysis",
				preferred_family_id="trend_analytics",
			).artifact_contract
			validation = validate_normalized_family_artifact(
				request_id="adapter-trend-fulfillment-validate-last-year",
				compiler_contract={
					"request_id": "adapter-trend-fulfillment-validate-last-year",
					"capability_id": "fulfillment_read",
					"selected_report": "Delivery Note Trends",
					"requested_dimensions": ["Customer"],
					"requested_metrics": ["Delivered Amount"],
					"requested_time_scope": "last_year",
				},
				artifact_contract=artifact,
				family_id="trend_analytics",
				adapter_errors=[],
				adapter_warnings=[],
			)
		self.assertEqual(validation.status, "pass")

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

	def test_trend_metric_reconciliation_prefers_explicit_sales_amount_from_message(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-sales-message",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Analytics"],
			requested_dimensions=[],
			requested_metrics=["Quantity"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.84,
		)
		reconciled = _normalize_trend_requested_metrics_from_message(
			message="Show monthly sales trend",
			interpretation=interpretation,
		)
		self.assertEqual(reconciled.requested_metrics, ["Sales Amount"])
		outcome = resolve_trend_analysis_interpretation(reconciled)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "sales_amount")
		self.assertEqual(outcome.interpretation.requested_metrics, ["Sales Amount"])

	def test_trend_metric_reconciliation_preserves_explicit_quantity_from_message(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-quantity-message",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=["sales_read"],
			candidate_reports=["Sales Analytics"],
			requested_dimensions=[],
			requested_metrics=["Sales Amount"],
			requested_time_scope="current_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.84,
		)
		reconciled = _normalize_trend_requested_metrics_from_message(
			message="Show monthly sales quantity trend",
			interpretation=interpretation,
		)
		self.assertEqual(reconciled.requested_metrics, ["Quantity"])
		outcome = resolve_trend_analysis_interpretation(reconciled)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.resolved_slots.get("trend_metric"), "quantity")
		self.assertEqual(outcome.interpretation.requested_metrics, ["Quantity"])

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

	def test_compiler_uses_previous_fiscal_year_for_last_year_delivery_trend(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="semantic-trend-last-year",
			session_id="semantic-trend",
			intent_class="trend_analysis",
			candidate_capability_ids=["fulfillment_read"],
			candidate_reports=["Delivery Note Trends"],
			requested_dimensions=["Customer"],
			requested_metrics=["Delivered Amount"],
			requested_time_scope="last_year",
			requested_presentation=[],
			extracted_slots={
				"from_date": "2025-04-01",
				"to_date": "2026-03-31",
			},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.92,
		)
		with patch(
			"ai_assistant_ui.qwen_chat.compiler._previous_fiscal_year_row",
			return_value={
				"name": "FY-2025",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			},
		):
			outcome = compile_fresh_query(
				request_id="semantic-trend-last-year",
				session_id="semantic-trend",
				interpretation=interpretation,
				response_policy={},
			)
		self.assertEqual(outcome.compiler_contract.decision, "execute")
		self.assertEqual(outcome.compiler_contract.selected_report, "Delivery Note Trends")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("fiscal_year"), "FY-2025")

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

	def test_runtime_ranking_payload_uses_deterministic_surface_fallback_for_noisy_receivable_bundle(self):
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
		self.assertIn("fresh_query_compiler", pipeline)
		compiler_payload = pipeline.get("fresh_query_compiler", {})
		self.assertEqual(compiler_payload.get("decision"), "execute")
		self.assertEqual(compiler_payload.get("capability_id"), "sales_read")
		self.assertEqual(compiler_payload.get("selected_report"), "Sales Analytics")

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
		self.assertEqual(contract.requested_time_scope, "open_fiscal_year_to_date")

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

	def test_ranking_metric_alias_refinement_stays_local_when_artifact_already_has_metric(self):
		resolution = build_followup_resolution_contract(
			request_id="continuation-ranking-aov",
			mode="local_grounded_transform",
			requested_modes=["column_refinement"],
			target_dimension="Customer",
			target_limit=5,
			target_metric="aov",
			requested_columns=["customer name"],
			requested_time_scope="",
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="Show customer name and aov only.",
		)
		continuation_contract = types.SimpleNamespace(
			preserve_grounded_context=True,
			source_family_id="ranking_analytics",
			source_capability_id="sales_order_read",
			source_report="Sales Order List",
			preserved_dimension="Customer",
			source_dimension="Customer",
			preserved_metric_key="revenue",
			source_metric_key="revenue",
			preserve_projection_shape=False,
			preserved_requested_columns=["entity", "revenue", "quantity", "average_order_value"],
			source_requested_columns=["entity", "revenue", "quantity", "average_order_value"],
			preserve_rank_membership=True,
			preserved_limit=5,
			source_limit=5,
			preserve_rank_order=True,
			preserved_sort_direction="desc",
			source_sort_direction="desc",
			preserved_time_scope="last_month",
			source_time_scope="last_month",
		)
		artifact_payload = {
			"dimensions": {
				"requested_metric_key": "revenue",
				"available_metric_keys": ["revenue", "quantity", "average_order_value", "sales_amount"],
				"requested_column_alias_map": {
					"customer": "entity",
					"customer_name": "entity",
					"aov": "average_order_value",
				},
			},
			"sections": {
				"ranked_rows": [
					{
						"entity": "Zegyo Mobile Supply House",
						"customer_name": "Zegyo Mobile Supply House",
						"revenue": 9340000,
						"quantity": 30,
						"average_order_value": 3113333.33,
					}
				]
			},
		}
		outcome = authoritative_continuation_resolution(
			request_id="continuation-ranking-aov",
			followup_resolution=resolution,
			continuation_contract=continuation_contract,
			artifact_payload=artifact_payload,
			grounded_turn={},
		)
		self.assertEqual(outcome.mode, "local_grounded_transform")
		self.assertEqual(outcome.target_metric, "aov")
		self.assertEqual(list(outcome.requested_columns), ["customer name"])

	def test_transaction_listing_time_scope_restatement_upgrades_to_capability_requery(self):
		resolution = build_followup_resolution_contract(
			request_id="continuation-transaction-time-scope",
			mode="grounded_follow_up",
			requested_modes=["filter_refinement", "time_scope_restatement"],
			target_dimension="Posting Date",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="last_month",
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="User asked for the same governed listing for last month.",
		)
		continuation_contract = types.SimpleNamespace(
			preserve_grounded_context=True,
			source_family_id="transaction_listing",
			source_capability_id="fulfillment_read",
			source_report="Delivery Note List",
			preserved_dimension="Posting Date",
			source_dimension="Posting Date",
			preserved_metric_key="grand_total",
			source_metric_key="grand_total",
			preserve_projection_shape=True,
			preserved_requested_columns=["document_name", "posting_date", "customer", "grand_total", "quantity", "status"],
			source_requested_columns=["document_name", "posting_date", "customer", "grand_total", "quantity", "status"],
			preserve_rank_membership=False,
			preserved_limit=5,
			source_limit=5,
			preserve_rank_order=False,
			preserved_sort_direction="",
			source_sort_direction="",
			preserved_time_scope="",
			source_time_scope="",
		)
		outcome = authoritative_continuation_resolution(
			request_id="continuation-transaction-time-scope",
			followup_resolution=resolution,
			continuation_contract=continuation_contract,
			artifact_payload={"sections": {"transaction_rows": [{"document_name": "MAT-DN-2026-00015"}]}},
			grounded_turn={},
		)
		self.assertEqual(outcome.mode, "capability_requery")
		self.assertEqual(outcome.target_capability_id, "fulfillment_read")
		self.assertEqual(outcome.target_report, "Delivery Note List")
		self.assertEqual(outcome.requested_time_scope, "last_month")

	def test_build_artifact_continuation_contract_does_not_mark_transaction_listing_as_rank_membership(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="listing-contract-no-rank-membership",
			mode="grounded_follow_up",
			requested_modes=[],
			target_dimension="Posting Date",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="Keep the current listing context.",
		)
		contract = build_artifact_continuation_contract(
			request_id="listing-contract-no-rank-membership",
			followup_resolution=followup_resolution,
			grounded_turn={
				"source_name": "Delivery Note List",
				"artifact_family_id": "transaction_listing",
			},
			artifact_payload={
				"family_id": "transaction_listing",
				"dimensions": {"requested_top_n": 5},
				"sections": {"transaction_rows": [{"document_name": "MAT-DN-2026-00015"}]},
			},
		)
		self.assertFalse(contract.preserve_rank_membership)
		self.assertFalse(contract.preserve_rank_order)
		self.assertEqual(contract.preserved_limit, 0)

	def test_transaction_listing_time_scope_restatement_drops_legacy_preserved_limit(self):
		resolution = build_followup_resolution_contract(
			request_id="continuation-transaction-time-scope-legacy-limit",
			mode="grounded_follow_up",
			requested_modes=["filter_refinement", "time_scope_restatement"],
			target_dimension="Posting Date",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="last_month",
			depends_on_grounded_turn=True,
			self_contained=False,
			reason="User asked for the same governed listing for last month.",
		)
		continuation_contract = types.SimpleNamespace(
			preserve_grounded_context=True,
			source_family_id="transaction_listing",
			source_capability_id="fulfillment_read",
			source_report="Delivery Note List",
			preserved_dimension="Posting Date",
			source_dimension="Posting Date",
			preserved_metric_key="grand_total",
			source_metric_key="grand_total",
			preserve_projection_shape=True,
			preserved_requested_columns=["document_name", "posting_date", "customer", "grand_total", "quantity", "status"],
			source_requested_columns=["document_name", "posting_date", "customer", "grand_total", "quantity", "status"],
			preserve_rank_membership=True,
			preserved_limit=5,
			source_limit=5,
			preserve_rank_order=True,
			preserved_sort_direction="desc",
			source_sort_direction="desc",
			preserved_time_scope="",
			source_time_scope="",
		)
		outcome = authoritative_continuation_resolution(
			request_id="continuation-transaction-time-scope-legacy-limit",
			followup_resolution=resolution,
			continuation_contract=continuation_contract,
			artifact_payload={"sections": {"transaction_rows": [{"document_name": "MAT-DN-2026-00015"}]}},
			grounded_turn={},
		)
		self.assertEqual(outcome.mode, "capability_requery")
		self.assertEqual(outcome.target_capability_id, "fulfillment_read")
		self.assertEqual(outcome.target_report, "Delivery Note List")
		self.assertEqual(outcome.requested_time_scope, "last_month")
		self.assertEqual(outcome.target_limit, 0)

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
		self.assertTrue(_allow_deterministic_family_surface_fallback("transaction_listing"))
		self.assertTrue(_allow_deterministic_family_surface_fallback("financial_statement"))
		self.assertTrue(_allow_deterministic_family_surface_fallback("inventory_summary"))
		self.assertTrue(_allow_deterministic_family_surface_fallback("aging_analysis"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("trend_analysis"))
		self.assertFalse(_allow_deterministic_family_surface_fallback("financial_summary"))
		self.assertTrue(_allow_deterministic_family_surface_fallback("ranked_entities"))
		self.assertTrue(_allow_deterministic_family_surface_fallback("product_performance"))

	def test_deterministic_family_surface_interpretation_builds_aging_route_from_governed_registry(self):
		outcome = _deterministic_family_surface_interpretation(
			request_id="semantic-det-1",
			session_id="semantic-det",
			message="show accounts receivable summary as of today",
			confidence_threshold=0.8,
		)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.intent_class, "aging_analysis")
		self.assertEqual(list(outcome.candidate_capability_ids), ["accounts_receivable_read"])
		self.assertEqual(list(outcome.candidate_reports), ["Accounts Receivable Summary"])
		self.assertEqual(outcome.requested_time_scope, "as_of_today")
		self.assertEqual(dict(outcome.extracted_slots), {"aging_view": "receivable"})

	def test_deterministic_family_surface_interpretation_stays_disabled_for_ambiguous_trend_rules(self):
		outcome = _deterministic_family_surface_interpretation(
			request_id="semantic-det-2",
			session_id="semantic-det",
			message="show monthly sales trend this fiscal year",
			confidence_threshold=0.8,
		)
		self.assertIsNone(outcome)

	def test_semantic_resolution_registry_loader_returns_defensive_copy(self):
		first = load_semantic_resolution_registry()
		second = load_semantic_resolution_registry()
		self.assertIsNot(first, second)
		first_rules = first.get("family_resolution_rules") if isinstance(first.get("family_resolution_rules"), list) else []
		second_rules = second.get("family_resolution_rules") if isinstance(second.get("family_resolution_rules"), list) else []
		self.assertTrue(first_rules)
		self.assertTrue(second_rules)
		self.assertIsNot(first_rules, second_rules)
		first_rules.pop()
		self.assertGreater(len(second_rules), len(first_rules))

	def test_business_ontology_loader_returns_defensive_copy(self):
		first = load_business_ontology()
		second = load_business_ontology()
		self.assertIsNot(first, second)
		first_concepts = first.get("concepts") if isinstance(first.get("concepts"), list) else []
		second_concepts = second.get("concepts") if isinstance(second.get("concepts"), list) else []
		self.assertTrue(first_concepts)
		self.assertTrue(second_concepts)
		self.assertIsNot(first_concepts, second_concepts)
		first_aliases = first_concepts[0].get("aliases") if isinstance(first_concepts[0], dict) else {}
		second_aliases = second_concepts[0].get("aliases") if isinstance(second_concepts[0], dict) else {}
		self.assertIsInstance(first_aliases, dict)
		self.assertIsInstance(second_aliases, dict)
		self.assertIsNot(first_aliases, second_aliases)
		first_en_aliases = first_aliases.get("en") if isinstance(first_aliases.get("en"), list) else []
		second_en_aliases = second_aliases.get("en") if isinstance(second_aliases.get("en"), list) else []
		self.assertTrue(first_en_aliases)
		self.assertTrue(second_en_aliases)
		first_en_aliases.pop()
		self.assertGreater(len(second_en_aliases), len(first_en_aliases))

	def test_compile_from_fresh_query_message_uses_deterministic_surface_fallback_after_runtime_error(self):
		runtime_error = SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=0.72,
			runtime_error="provider timeout",
			agent_meta={},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			side_effect=[runtime_error, runtime_error],
		):
			pipeline = compile_from_fresh_query_message(
				session_id="deterministic-fallback-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show accounts receivable summary as of today",
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		compiled_request = pipeline.get("compiled_query_request") if isinstance(pipeline.get("compiled_query_request"), dict) else {}
		self.assertEqual(semantic_payload.get("status"), "semantic_resolution_applied")
		self.assertTrue(bool((semantic_payload.get("agent_meta") or {}).get("deterministic_surface_fallback")))
		self.assertEqual(compiler_payload.get("decision"), "execute")
		self.assertEqual(compiled_request.get("selected_report"), "Accounts Receivable Summary")

	def test_pipeline_recover_with_deterministic_surface_fallback_rebuilds_compiled_request(self):
		pipeline = {
			"request_id": "deterministic-pipeline-rescue",
			"fresh_query_interpretation": {
				"type": "qwen_semantic_fresh_query_interpretation",
				"contract_version": "1.0",
				"status": "runtime_error",
				"confidence_threshold": 0.72,
				"runtime_error": "Semantic fresh-query response did not pass governed runtime validation.",
				"validation_error": "",
				"interpretation": {},
				"agent_meta": {"engine": "semantic_fresh_query"},
			},
			"phase4_latency_breakdown": {
				"proposal_generation_latency_ms": 17,
				"compilation_latency_ms": 0,
			},
		}

		recovered = _recover_pipeline_with_deterministic_surface_fallback(
			pipeline=pipeline,
			session_id="deterministic-pipeline-rescue-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show accounts receivable summary as of today",
			clarification_resolution=None,
		)
		semantic_payload = (
			recovered.get("fresh_query_interpretation")
			if isinstance(recovered.get("fresh_query_interpretation"), dict)
			else {}
		)
		compiler_payload = (
			recovered.get("fresh_query_compiler")
			if isinstance(recovered.get("fresh_query_compiler"), dict)
			else {}
		)
		compiled_request = (
			recovered.get("compiled_query_request")
			if isinstance(recovered.get("compiled_query_request"), dict)
			else {}
		)
		self.assertEqual(semantic_payload.get("status"), "semantic_resolution_applied")
		self.assertTrue(bool((semantic_payload.get("agent_meta") or {}).get("deterministic_surface_fallback")))
		self.assertTrue(bool((semantic_payload.get("agent_meta") or {}).get("deterministic_surface_pipeline_rescue")))
		self.assertEqual(compiler_payload.get("decision"), "execute")
		self.assertEqual(compiled_request.get("selected_report"), "Accounts Receivable Summary")

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

	def test_build_grounded_turn_context_ignores_stale_artifact_metadata_from_prior_request(self):
		grounded = build_grounded_turn_context(
			request_id="current-request",
			interaction_contract=types.SimpleNamespace(detected_language="en"),
			assistant_payload={
				"tables": [
					{
						"headers": ["Customer", "Outstanding Amount"],
						"rows": [["Customer A", "100,000"]],
					}
				]
			},
			runtime_payload={
				"ok": True,
				"request_id": "current-request",
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Accounts Receivable Summary",
							"filters": {
								"company": "Enterprise Co",
								"report_date": "2026-04-06",
							},
						},
					}
				],
			},
			artifact_payload={
				"request_id": "prior-request",
				"family_id": "aging",
				"artifact_type": "normalized_family_artifact",
				"source_name": "Accounts Payable",
				"source_reports": ["Accounts Payable Summary"],
			},
		)
		self.assertIsNotNone(grounded)
		self.assertEqual(grounded.source_name, "Accounts Receivable Summary")
		self.assertEqual(list(grounded.artifact_source_reports or []), [])
		self.assertEqual(str(grounded.artifact_family_id or ""), "")

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

	def test_transaction_listing_family_adapter_uses_payment_entry_primary_metric(self):
		compiler_contract = {
			"request_id": "adapter-payment-entry-1",
			"capability_id": "collections_read",
			"selected_report": "Payment Entry List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Received Amount"],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Payment Entry List",
						"filters": {"company": "Enterprise Co"},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "ACC-PAY-0001",
									"posting_date": "2026-04-15",
									"party": "Sunflower Accessories Co.",
									"party_type": "Supplier",
									"received_amount": 1500000,
									"total_allocated_amount": 1500000,
									"paid_amount": 1500000,
									"docstatus": 1,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-payment-entry-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		metrics = dict(outcome.artifact_contract.metrics)
		summary = list((outcome.artifact_contract.sections or {}).get("summary") or [])
		self.assertEqual(dimensions.get("primary_metric_key"), "received_amount")
		self.assertEqual(dimensions.get("primary_metric_label"), "Received Amount")
		self.assertEqual(dimensions.get("requested_columns"), ["posting_date", "customer", "received_amount"])
		self.assertEqual(metrics.get("total_amount"), 1500000.0)
		self.assertTrue(any(str(item.get("label") or "").strip() == "Total Received Amount" for item in summary))

	def test_transaction_listing_family_adapter_uses_metadata_default_metric_for_payment_entries(self):
		compiler_contract = {
			"request_id": "adapter-payment-entry-default-1",
			"selected_report": "Payment Entry List",
			"requested_dimensions": [],
			"requested_metrics": [],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Payment Entry List",
						"filters": {"company": "Enterprise Co"},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "ACC-PAY-0001",
									"posting_date": "2026-04-15",
									"party": "Sunflower Accessories Co.",
									"party_type": "Supplier",
									"received_amount": 2000000,
									"total_allocated_amount": 3500000,
									"paid_amount": 3500000,
									"docstatus": 1,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-payment-entry-default-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		metrics = dict(outcome.artifact_contract.metrics)
		summary = list((outcome.artifact_contract.sections or {}).get("summary") or [])
		self.assertEqual(dimensions.get("primary_metric_key"), "received_amount")
		self.assertEqual(dimensions.get("primary_metric_label"), "Received Amount")
		self.assertEqual(dimensions.get("requested_columns"), ["received_amount"])
		self.assertEqual(metrics.get("total_amount"), 2000000.0)
		self.assertTrue(any(str(item.get("label") or "").strip() == "Total Received Amount" for item in summary))


	def test_transaction_listing_renderer_uses_payment_entry_primary_metric_label(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-payment-entry-2",
			compiler_contract={
				"request_id": "adapter-payment-entry-2",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Received Amount"],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-15",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"received_amount": 1500000,
										"total_allocated_amount": 1500000,
										"paid_amount": 1500000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-payment-entry-2",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		summary_block = next((block for block in blocks if isinstance(block, dict) and str(block.get("title") or "").strip() == "Summary"), {})
		documents_block = next((block for block in blocks if isinstance(block, dict) and str(block.get("title") or "").strip() == "Documents"), {})
		self.assertIn(["Total Received Amount", "1,500,000"], list(summary_block.get("rows") or []))
		self.assertIn("Received Amount", list(documents_block.get("columns") or []))

	def test_transaction_listing_renderer_avoids_duplicate_total_metric_label(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-payment-entry-2b",
			compiler_contract={
				"request_id": "adapter-payment-entry-2b",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Total Allocated Amount"],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-15",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"received_amount": 1500000,
										"total_allocated_amount": 1500000,
										"paid_amount": 1500000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-payment-entry-2b",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		summary_block = next((block for block in blocks if isinstance(block, dict) and str(block.get("title") or "").strip() == "Summary"), {})
		self.assertIn(["Total Allocated Amount", "1,500,000"], list(summary_block.get("rows") or []))
		self.assertNotIn(["Total Total Allocated Amount", "1,500,000"], list(summary_block.get("rows") or []))

	def test_transaction_listing_renderer_pluralizes_document_title(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-payment-entry-title-1",
			compiler_contract={
				"request_id": "adapter-payment-entry-title-1",
				"capability_id": "collections_read",
				"selected_report": "Payment Entry List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Total Allocated Amount"],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Payment Entry List",
							"filters": {"company": "Enterprise Co"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-PAY-0001",
										"posting_date": "2026-04-15",
										"party": "Sunflower Accessories Co.",
										"party_type": "Supplier",
										"total_allocated_amount": 1500000,
										"docstatus": 1,
									},
									{
										"name": "ACC-PAY-0002",
										"posting_date": "2026-04-16",
										"party": "Golden Dragon Trading Co. Ltd.",
										"party_type": "Supplier",
										"total_allocated_amount": 500000,
										"docstatus": 1,
									}
								]
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-payment-entry-title-1",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertEqual(str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("title") or ""), "Last 2 Payment Entries")

	def test_transaction_listing_renderer_keeps_singular_document_title(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-sales-invoice-title-1",
			compiler_contract={
				"request_id": "adapter-sales-invoice-title-1",
				"capability_id": "sales_invoice_read",
				"selected_report": "Sales Invoice List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total"],
				"requested_time_scope": "today",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Sales Invoice List",
							"filters": {"company": "Enterprise Co", "from_date": "2026-04-15", "to_date": "2026-04-15"},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"name": "ACC-SINV-0001",
										"posting_date": "2026-04-15",
										"customer": "35th Street Mobile Wholesale",
										"grand_total": 300000,
										"outstanding_amount": 0,
										"docstatus": 1,
									}
								],
							}
						},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-sales-invoice-title-1",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertEqual(str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("title") or ""), "Last 1 Sales Invoice (2026-04-15 to 2026-04-15)")

	def test_transaction_listing_family_adapter_generalizes_delivery_note_list(self):
		compiler_contract = {
			"request_id": "adapter-structured-2b",
			"capability_id": "fulfillment_read",
			"selected_report": "Delivery Note List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Quantity"],
			"requested_time_scope": "last_month",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Delivery Note List",
						"filters": {
							"from_date": "2026-03-01",
							"to_date": "2026-03-31",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "MAT-DN-2026-00015",
									"posting_date": "2026-03-30",
									"customer": "Thaketa Mobile Exchange",
									"status": "Partially Billed",
									"company": "Enterprise Co",
									"grand_total": 200000,
									"total_qty": 5,
									"docstatus": 1,
									"is_return": 0,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-structured-2b",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		dimensions = dict(outcome.artifact_contract.dimensions)
		metrics = dict(outcome.artifact_contract.metrics)
		summary = list((outcome.artifact_contract.sections or {}).get("summary") or [])
		self.assertEqual(dimensions.get("transaction_type"), "delivery_note")
		self.assertEqual(dimensions.get("document_label"), "Delivery Note")
		self.assertEqual(
			dimensions.get("requested_columns"),
			["posting_date", "customer", "quantity"],
		)
		self.assertEqual(metrics.get("document_count"), 1)
		self.assertEqual(metrics.get("total_amount"), 200000.0)
		self.assertEqual(metrics.get("quantity"), 5.0)
		self.assertNotIn("outstanding_amount", metrics)
		self.assertTrue(any(str(item.get("metric_key") or "").strip() == "quantity" for item in summary))

	def test_transaction_listing_family_validation_does_not_require_outstanding_for_delivery_note_shape(self):
		compiler_contract = {
			"request_id": "adapter-structured-2c",
			"capability_id": "fulfillment_read",
			"selected_report": "Delivery Note List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Quantity"],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Delivery Note List",
						"filters": {"company": "Enterprise Co"},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "MAT-DN-2026-00015",
									"posting_date": "2026-03-30",
									"customer": "Thaketa Mobile Exchange",
									"status": "Partially Billed",
									"company": "Enterprise Co",
									"grand_total": 200000,
									"total_qty": 5,
									"docstatus": 1,
									"is_return": 0,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-structured-2c",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		validation = validate_normalized_family_artifact(
			request_id="adapter-structured-2c",
			compiler_contract=compiler_contract,
			artifact_contract=outcome.artifact_contract,
			family_id=outcome.family_id,
			adapter_errors=outcome.errors,
			adapter_warnings=outcome.warnings,
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		self.assertNotIn(
			"Missing normalized transaction metrics: outstanding_amount",
			list(validation.errors),
		)

	def test_transaction_listing_family_validation_does_not_require_quantity_for_invoice_shape(self):
		compiler_contract = {
			"request_id": "adapter-structured-2d",
			"capability_id": "sales_read",
			"selected_report": "Sales Invoice List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Grand Total"],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Sales Invoice List",
						"filters": {"company": "Enterprise Co"},
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
			request_id="adapter-structured-2d",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		validation = validate_normalized_family_artifact(
			request_id="adapter-structured-2d",
			compiler_contract=compiler_contract,
			artifact_contract=outcome.artifact_contract,
			family_id=outcome.family_id,
			adapter_errors=outcome.errors,
			adapter_warnings=outcome.warnings,
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		self.assertNotIn(
			"Missing normalized transaction metrics: quantity",
			list(validation.errors),
		)

	def test_transaction_listing_family_validation_accepts_outstanding_total_canonical_request(self):
		compiler_contract = {
			"request_id": "adapter-structured-2e",
			"capability_id": "sales_read",
			"selected_report": "Sales Invoice List",
			"requested_dimensions": ["Posting Date", "Customer"],
			"requested_metrics": ["Outstanding Amount"],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Sales Invoice List",
						"filters": {"company": "Enterprise Co"},
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
			request_id="adapter-structured-2e",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		validation = validate_normalized_family_artifact(
			request_id="adapter-structured-2e",
			compiler_contract=compiler_contract,
			artifact_contract=outcome.artifact_contract,
			family_id=outcome.family_id,
			adapter_errors=outcome.errors,
			adapter_warnings=outcome.warnings,
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		self.assertNotIn(
			"Missing normalized transaction metrics: outstanding_total",
			list(validation.errors),
		)

	def test_transaction_listing_family_adapter_preserves_empty_governed_result(self):
		compiler_contract = {
			"request_id": "adapter-structured-empty-1",
			"capability_id": "fulfillment_read",
			"selected_report": "Delivery Note List",
			"requested_dimensions": ["Posting Date", "Customer", "Document Status"],
			"requested_metrics": ["Grand Total"],
			"requested_time_scope": "last_month",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Delivery Note List",
						"filters": {
							"company": "Enterprise Co",
							"from_date": "2026-03-01",
							"to_date": "2026-03-31",
							"status": "Completed",
						},
					},
					"output_obj": {"result": {"data": []}},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="adapter-structured-empty-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertIsNotNone(outcome.artifact_contract)
		self.assertEqual(outcome.artifact_contract.metrics.get("document_count"), 0)
		self.assertEqual((outcome.artifact_contract.sections or {}).get("transaction_rows"), [])
		self.assertIn(
			"No documents matched these filters.",
			list(outcome.artifact_contract.warnings),
		)

	def test_transaction_listing_family_validation_accepts_empty_governed_result(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-structured-empty-2",
			compiler_contract={
				"request_id": "adapter-structured-empty-2",
				"capability_id": "fulfillment_read",
				"selected_report": "Delivery Note List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total"],
				"requested_time_scope": "last_month",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Delivery Note List",
							"filters": {
								"company": "Enterprise Co",
								"from_date": "2026-03-01",
								"to_date": "2026-03-31",
								"status": "Completed",
							},
						},
						"output_obj": {"result": {"data": []}},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		validation = validate_normalized_family_artifact(
			request_id="adapter-structured-empty-2",
			compiler_contract={
				"request_id": "adapter-structured-empty-2",
				"capability_id": "fulfillment_read",
				"selected_report": "Delivery Note List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total"],
				"requested_time_scope": "last_month",
			},
			artifact_contract=artifact_contract,
			family_id="transaction_listing",
			adapter_errors=[],
			adapter_warnings=list(artifact_contract.warnings),
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		self.assertEqual(list(validation.errors), [])
		self.assertIn(
			"Normalized transaction listing artifact contains no matching document rows for the current governed filters.",
			list(validation.warnings),
		)

	def test_transaction_listing_family_validation_accepts_empty_invoice_result_with_outstanding_metric(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-structured-empty-3",
			compiler_contract={
				"request_id": "adapter-structured-empty-3",
				"capability_id": "sales_read",
				"selected_report": "Sales Invoice List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total", "Outstanding Amount"],
				"requested_time_scope": "latest",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Sales Invoice List",
							"filters": {
								"company": "Enterprise Co",
								"from_date": "2026-04-07",
								"to_date": "2026-04-07",
							},
						},
						"output_obj": {"result": {"data": []}},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		validation = validate_normalized_family_artifact(
			request_id="adapter-structured-empty-3",
			compiler_contract={
				"request_id": "adapter-structured-empty-3",
				"capability_id": "sales_read",
				"selected_report": "Sales Invoice List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total", "Outstanding Amount"],
				"requested_time_scope": "latest",
			},
			artifact_contract=artifact_contract,
			family_id="transaction_listing",
			adapter_errors=[],
			adapter_warnings=list(artifact_contract.warnings),
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		self.assertNotIn(
			"Missing normalized transaction metrics: outstanding_amount",
			list(validation.errors),
		)
		self.assertIn(
			"Normalized transaction listing artifact contains no matching document rows for the current governed filters.",
			list(validation.warnings),
		)

	def test_transaction_listing_renderer_explains_empty_governed_result(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-structured-empty-3",
			compiler_contract={
				"request_id": "adapter-structured-empty-3",
				"capability_id": "fulfillment_read",
				"selected_report": "Delivery Note List",
				"requested_dimensions": ["Posting Date", "Customer"],
				"requested_metrics": ["Grand Total"],
				"requested_time_scope": "last_month",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Delivery Note List",
							"filters": {
								"company": "Enterprise Co",
								"from_date": "2026-03-01",
								"to_date": "2026-03-31",
								"status": "Completed",
							},
						},
						"output_obj": {"result": {"data": []}},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-structured-empty-3",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("No documents matched these filters.", answer_text)

	def test_transaction_listing_renderer_preserves_zero_summary_values(self):
		artifact_contract = build_normalized_family_artifact(
			request_id="adapter-structured-empty-4",
			compiler_contract={
				"request_id": "adapter-structured-empty-4",
				"capability_id": "purchasing_read",
				"selected_report": "Purchase Order List",
				"requested_dimensions": ["Transaction Date", "Supplier"],
				"requested_metrics": ["Grand Total", "Quantity"],
				"requested_time_scope": "last_month",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Purchase Order List",
							"filters": {
								"company": "Enterprise Co",
								"from_date": "2026-03-01",
								"to_date": "2026-03-31",
							},
						},
						"output_obj": {"result": {"data": []}},
					}
				]
			},
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		).artifact_contract
		rendered = render_normalized_family_response(
			request_id="adapter-structured-empty-4",
			artifact_contract=artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		summary_block = next(
			(
				block
				for block in blocks
				if isinstance(block, dict) and str(block.get("title") or "").strip() == "Summary"
			),
			{},
		)
		self.assertIn(["Document Count", "0"], list(summary_block.get("rows") or []))

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

	def test_direct_query_execution_applies_governed_scalar_status_filter(self):
		report_spec = {
			"grounding_mode": "direct_query",
			"direct_query": {
				"doctype": "Delivery Note",
				"fields": ["name", "posting_date", "customer", "status", "company"],
				"fixed_filters": {"docstatus": 1},
				"date_field": "posting_date",
				"default_limit": 8,
			},
			"required_filters": ["company"],
			"defaultable_filters": [{"fieldname": "company", "strategy": "single_company_invariant"}],
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.get_report_spec",
			return_value=report_spec,
		), patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.frappe.get_all",
			return_value=[{"name": "DN-0001", "status": "Completed"}],
		) as mocked_get_all:
			payload = execute_governed_report(
				report_name="Delivery Note List",
				filters={
					"company": "Enterprise Co",
					"from_date": "2026-03-01",
					"to_date": "2026-03-31",
					"status": "Completed",
					"unexpected_filter": "ignore-me",
				},
				user="Administrator",
			)
		self.assertTrue(payload.get("ok"))
		self.assertEqual(
			mocked_get_all.call_args.kwargs.get("filters"),
			{
				"docstatus": 1,
				"company": "Enterprise Co",
				"posting_date": ["between", ["2026-03-01", "2026-03-31"]],
				"status": "Completed",
			},
		)

	def test_direct_query_execution_ignores_nonscalar_dynamic_filter_values(self):
		report_spec = {
			"grounding_mode": "direct_query",
			"direct_query": {
				"doctype": "Delivery Note",
				"fields": ["name", "status", "company"],
				"fixed_filters": {"docstatus": 1},
			},
			"required_filters": ["company"],
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.get_report_spec",
			return_value=report_spec,
		), patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.frappe.get_all",
			return_value=[{"name": "DN-0001"}],
		) as mocked_get_all:
			payload = execute_governed_report(
				report_name="Delivery Note List",
				filters={
					"company": "Enterprise Co",
					"status": ["in", ["Completed", "To Bill"]],
				},
				user="Administrator",
			)
		self.assertTrue(payload.get("ok"))
		self.assertEqual(
			mocked_get_all.call_args.kwargs.get("filters"),
			{
				"docstatus": 1,
				"company": "Enterprise Co",
			},
		)
