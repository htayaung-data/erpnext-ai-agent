import sys
import types
import unittest
from unittest.mock import patch


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

from ai_assistant_ui.qwen_chat.clarification_resolution import (
	clarification_resolved_continuation_message,
	pending_clarification_message_matches_option,
	pending_clarification_empty_ack_answer,
	pending_clarification_fallback_stop_answer,
	pending_clarification_meta_answer,
	pending_clarification_repeat_answer,
	resolve_pending_clarification_response,
)
from ai_assistant_ui.qwen_chat.clarification_translation import translate_clarification_signal
from ai_assistant_ui.qwen_chat.clarification_translation import translate_clarification_reason_contract
from ai_assistant_ui.qwen_chat.governed_kpi_support import maybe_build_governed_kpi_frontdoor_response
from ai_assistant_ui.qwen_chat.service import (
	_apply_frontdoor_clarification_reentry_state,
	_compound_request_completion_answer,
	_cancel_compound_request_assessment_payload,
	_compound_request_stop_control,
	_frontdoor_clarification_reentry_message,
	_frontdoor_clarification_requires_fresh_query_reset,
	_message_should_override_stale_context_as_fresh_query,
)
from ai_assistant_ui.qwen_chat.contracts import build_compound_request_assessment_contract


class TestClarificationResolutionContracts(unittest.TestCase):
	def test_compound_request_stop_control_matches_business_stop_words(self):
		self.assertTrue(_compound_request_stop_control("stop"))
		self.assertTrue(_compound_request_stop_control("no thanks"))
		self.assertTrue(_compound_request_stop_control("not now"))
		self.assertFalse(_compound_request_stop_control("continue"))

	def test_cancel_compound_request_assessment_clears_remaining_steps(self):
		payload = build_compound_request_assessment_contract(
			request_id="compound-stop",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			suggested_options=["Payment entries", "Customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"continuation_lane": "front_door",
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"primary_segment_label": "Customer list",
				"remaining_segment_messages": [],
				"remaining_segment_labels": [],
			},
		).to_payload()
		cancelled = _cancel_compound_request_assessment_payload(payload)
		self.assertEqual(cancelled.get("status"), "ordered_execution_cancelled")
		self.assertEqual(
			(cancelled.get("internal_details") or {}).get("primary_segment_message"),
			"",
		)
		self.assertEqual(
			(cancelled.get("internal_details") or {}).get("remaining_segment_messages"),
			[],
		)
		self.assertTrue((cancelled.get("internal_details") or {}).get("cancelled"))

	def test_compound_request_completion_answer_handles_exhausted_continue(self):
		payload = build_compound_request_assessment_contract(
			request_id="compound-done",
			status="ordered_execution_complete",
			segments=["show me payment entries", "give me some customer list"],
			suggested_options=["Payment entries", "Customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"continuation_lane": "front_door",
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"primary_segment_label": "",
				"remaining_segment_messages": [],
				"remaining_segment_labels": [],
			},
		).to_payload()
		self.assertEqual(
			_compound_request_completion_answer(payload, "continue"),
			"That sequence is already finished. You can start a new request anytime.",
		)
		self.assertEqual(_compound_request_completion_answer(payload, "show me customers"), "")

	def test_frontdoor_clarification_resolution_breaks_prior_artifact_inheritance(self):
		contract = types.SimpleNamespace(decision="resolved_option")
		self.assertTrue(
			_frontdoor_clarification_requires_fresh_query_reset(
				clarification_lane="front_door",
				clarification_response_contract=contract,
				clarified_runtime_message="give me some supplier list",
			)
		)
		self.assertFalse(
			_frontdoor_clarification_requires_fresh_query_reset(
				clarification_lane="artifact_boundary",
				clarification_response_contract=contract,
				clarified_runtime_message="give me some supplier list",
			)
		)

	def test_frontdoor_clarification_resolution_breaks_prior_artifact_inheritance_with_structured_slot_only(self):
		contract = types.SimpleNamespace(
			decision="resolved_option",
			resolved_slot={"statement_variant": "balance_sheet"},
		)
		self.assertTrue(
			_frontdoor_clarification_requires_fresh_query_reset(
				clarification_lane="front_door",
				clarification_response_contract=contract,
				clarified_runtime_message="",
			)
		)

	def test_frontdoor_clarification_reentry_message_falls_back_to_raw_reply_for_structured_resolution(self):
		contract = types.SimpleNamespace(
			decision="resolved_option",
			resolved_slot={"entity_grain": "supplier"},
		)
		self.assertEqual(
			_frontdoor_clarification_reentry_message(
				raw_message="suppliers",
				clarification_lane="front_door",
				clarification_response_contract=contract,
				clarified_runtime_message="",
			),
			"suppliers",
		)
		self.assertEqual(
			_frontdoor_clarification_reentry_message(
				raw_message="suppliers",
				clarification_lane="artifact_boundary",
				clarification_response_contract=contract,
				clarified_runtime_message="",
			),
			"",
		)

	def test_frontdoor_clarification_reentry_adopts_clarified_contract_and_message(self):
		with patch(
			"ai_assistant_ui.qwen_chat.service.detect_entity_drilldown_request",
			return_value={"source": "explicit_identifier"},
		) as drilldown_mock:
			updated_semantic, updated_contract, updated_entity_drilldown = _apply_frontdoor_clarification_reentry_state(
				frontdoor_semantic_result="old-semantic",
				frontdoor_contract={"response_payload": {}},
				entity_drilldown=None,
				clarified_frontdoor_semantic_result="new-semantic",
				clarified_frontdoor_contract={
					"response_payload": {
						"master_data_frontdoor_assessment": {
							"status": "resolved",
							"entity_grain": "supplier",
						}
					}
				},
				clarified_runtime_message="give me some supplier list",
				latest_family_artifact={},
				latest_grounded_turn={},
			)
		self.assertEqual(updated_semantic, "new-semantic")
		self.assertEqual(
			updated_contract.get("response_payload", {}).get("master_data_frontdoor_assessment", {}).get("entity_grain"),
			"supplier",
		)
		self.assertEqual(updated_entity_drilldown, {"source": "explicit_identifier"})
		drilldown_mock.assert_called_once()
		self.assertEqual(drilldown_mock.call_args.kwargs.get("message"), "give me some supplier list")

	def test_artifact_boundary_option_resolution_beats_new_request_detection(self):
		signal_payload = {
			"stage": "artifact_boundary",
			"reason_type": "customer_tenure_basis_missing",
			"user_question": "Choose the customer tenure basis.",
			"suggested_options": [
				"Customer Tenure by Customer Created Date",
				"Customer Tenure by First Sales Order",
				"Customer Tenure by First Sales Invoice",
			],
			"internal_details": {
				"continuation_lane": "artifact_boundary",
				"resolved_message_by_option": {
					"Customer Tenure by Customer Created Date": "what is this customer's tenure by customer created date?",
					"Customer Tenure by First Sales Order": "what is this customer's tenure by first sales order date?",
					"Customer Tenure by First Sales Invoice": "what is this customer's tenure by first sales invoice date?",
				},
				"option_aliases_by_option": {
					"Customer Tenure by First Sales Order": [
						"first sales order",
						"first sales order date",
						"sales order",
						"order date",
						"by first sales order",
					]
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=True,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-1",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="first submitted sales order date",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={"grounded": True},
		)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Customer Tenure by First Sales Order")
		self.assertIn(contract.matched_by, {"exact_token_alias", "substring", "concept_overlap", "semantic", "fuzzy_alias"})

	def test_frontdoor_master_data_grain_clarification_resolves_supplier_option(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "master_data_entity_grain_missing",
			"user_question": "I can help with customers or suppliers or items. Which one would you like?",
			"suggested_options": [
				"Customers",
				"Suppliers",
				"Items",
			],
			"internal_details": {
				"continuation_lane": "front_door",
				"resolved_message_by_option": {
					"Customers": "give me some customer list",
					"Suppliers": "give me some supplier list",
					"Items": "give me some item list",
				},
				"option_aliases_by_option": {
					"Customers": ["customer", "customers", "customer list"],
					"Suppliers": ["supplier", "suppliers", "supplier list"],
					"Items": ["item", "items", "item list", "product", "products", "product list"],
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-master-data",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="suppliers",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Suppliers")
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal_payload,
				resolved_option=contract.resolved_option,
			),
			"give me some supplier list",
		)

	def test_frontdoor_structured_clarification_match_beats_new_request_detection(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "master_data_entity_grain_missing",
			"user_question": "I can help with customers or suppliers or items. Which one would you like?",
			"suggested_options": [
				"Customers",
				"Suppliers",
				"Items",
			],
			"internal_details": {
				"continuation_lane": "front_door",
				"semantic_slot_name": "entity_grain",
				"semantic_slot_value_by_option": {
					"Customers": "customer",
					"Suppliers": "supplier",
					"Items": "item",
				},
				"carryover_slot_values": {
					"lookup_mode": "directory_list",
					"lookup_projection": "names_only",
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._match_pending_clarification_option",
			return_value=("Suppliers", "semantic", 0.72),
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=True,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=True,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-frontdoor-structured-authority",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="supplier directory",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Suppliers")
		self.assertEqual(contract.resolved_slot.get("entity_grain"), "supplier")
		self.assertEqual(contract.resolved_slot.get("lookup_mode"), "directory_list")
		self.assertEqual(contract.resolved_slot.get("lookup_projection"), "names_only")

	def test_composite_structured_clarification_match_beats_new_request_detection(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "composite_family_variation",
			"user_question": "I can rank customers by revenue, but I still need the approved basis.",
			"suggested_options": [
				"Sales Order",
				"Sales Invoice",
			],
			"internal_details": {
				"continuation_lane": "front_door",
				"clarification_axis": "basis",
				"semantic_slot_name": "requested_basis",
				"semantic_slot_value_by_option": {
					"Sales Order": "sales_order",
					"Sales Invoice": "sales_invoice",
				},
				"carryover_slot_values": {
					"family_id": "customer_period_commercial",
					"requested_primary_metric": "revenue",
					"selected_time_scope": "last_month",
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._match_pending_clarification_option",
			return_value=("Sales Order", "semantic", 0.72),
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=True,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=True,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-composite-structured-authority",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="sales order",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Sales Order")
		self.assertEqual(contract.resolved_slot.get("requested_basis"), "sales_order")
		self.assertEqual(contract.resolved_slot.get("requested_primary_metric"), "revenue")
		self.assertEqual(contract.resolved_slot.get("selected_time_scope"), "last_month")

	def test_pending_clarification_option_guard_protects_short_composite_answers(self):
		basis_signal = {
			"stage": "front_door",
			"reason_type": "composite_family_variation",
			"user_question": "I can rank customers by revenue, but I still need the approved basis.",
			"suggested_options": ["Sales Order", "Sales Invoice"],
			"internal_details": {
				"continuation_lane": "front_door",
				"clarification_axis": "basis",
				"semantic_slot_name": "requested_basis",
				"semantic_slot_value_by_option": {
					"Sales Order": "sales_order",
					"Sales Invoice": "sales_invoice",
				},
				"resolved_message_by_option": {
					"Sales Invoice": "show top 7 customers by revenue for sales invoices",
				},
			},
		}
		period_signal = {
			"stage": "front_door",
			"reason_type": "composite_family_variation",
			"user_question": "I can rank customers by revenue for sales invoices, but I still need the business period.",
			"suggested_options": ["Last Month", "Current Fiscal Year to Date", "Last Year", "All time"],
			"internal_details": {
				"continuation_lane": "front_door",
				"clarification_axis": "scope",
				"semantic_slot_name": "selected_time_scope",
				"semantic_slot_value_by_option": {
					"Last Month": "last_month",
					"Current Fiscal Year to Date": "current_fiscal_year_to_date",
					"Last Year": "last_year",
					"All time": "all_time",
				},
				"resolved_message_by_option": {
					"Last Month": "show top 7 customers by revenue for sales invoices last month",
				},
			},
		}
		self.assertTrue(pending_clarification_message_matches_option("Sales Invoice", basis_signal))
		self.assertTrue(pending_clarification_message_matches_option("Last Month", period_signal))
		self.assertFalse(pending_clarification_message_matches_option("show me suppliers", basis_signal))
		self.assertFalse(
			_message_should_override_stale_context_as_fresh_query(
				message="Last Month",
				language="en",
			)
			and not pending_clarification_message_matches_option("Last Month", period_signal)
		)
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=True,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=True,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-composite-period",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="Last Month",
				signal_payload=period_signal,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Last Month")
		self.assertEqual(contract.resolved_slot.get("selected_time_scope"), "last_month")

	def test_clarification_continuation_message_supports_declared_placeholder(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "customer_scope_missing",
			"user_question": "Which customer do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"entity_grain": "customer",
				"resolved_message_placeholder": "customer",
				"resolved_message_template": "show customer tenure by customer created date for {customer} as of 2026-04-10",
			},
		}
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal_payload,
				resolved_option="Zegyo Mobile Supply House",
			),
			"show customer tenure by customer created date for Zegyo Mobile Supply House as of 2026-04-10",
		)

	def test_clarification_continuation_message_supports_generic_single_template_placeholder(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "entity_scope_missing",
			"user_question": "Which supplier do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"entity_grain": "supplier",
				"resolved_message_template": "show supplier profile for {entity}",
			},
		}
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal_payload,
				resolved_option="Myanmar Tech Import Services",
			),
			"show supplier profile for Myanmar Tech Import Services",
		)

	def test_clarification_continuation_message_does_not_guess_when_template_has_multiple_placeholders(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "entity_scope_missing",
			"user_question": "Which entity do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"resolved_message_template": "show {entity} in {period}",
			},
		}
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal_payload,
				resolved_option="Ko Nay Lin Mobile Center",
			),
			"",
		)

	def test_entity_scope_clarification_uses_declared_slot_key_not_reason_specific_branch(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "entity_scope_missing",
			"user_question": "Which customer do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"entity_grain": "customer",
				"resolved_slot_key": "selected_customer",
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_label": "Zegyo Mobile Supply House",
					"resolution_source": "exact_name",
				},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-entity-scope",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="Zegyo Mobile Supply House",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Zegyo Mobile Supply House")
		self.assertEqual(contract.resolved_slot.get("selected_customer"), "Zegyo Mobile Supply House")

	def test_entity_scope_clarification_prefers_shared_normalized_search_text(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "entity_scope_missing",
			"user_question": "Which supplier do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"entity_grain": "supplier",
				"lookup_mode": "candidate_resolution",
				"resolved_slot_key": "selected_supplier",
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.normalize_master_data_lookup_slots",
			return_value={
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Myanmar Tech Import",
			},
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_label": "Myanmar Tech Import Services",
					"resolution_source": "governed_fuzzy",
				},
			},
		) as resolve_mock, patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-entity-scope-normalized",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message='the supplier "Myanmar Tech Import"',
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Myanmar Tech Import Services")
		self.assertEqual(contract.resolved_slot.get("selected_supplier"), "Myanmar Tech Import Services")
		self.assertEqual(
			resolve_mock.call_args.kwargs.get("lookup_mode"),
			"candidate_resolution",
		)
		self.assertEqual(
			resolve_mock.call_args.kwargs.get("search_text"),
			"Myanmar Tech Import",
		)

	def test_entity_scope_clarification_falls_back_to_raw_reply_when_normalizer_has_no_search_text(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "entity_scope_missing",
			"user_question": "Which supplier do you want?",
			"suggested_options": [],
			"internal_details": {
				"continuation_lane": "front_door",
				"entity_grain": "supplier",
				"lookup_mode": "candidate_resolution",
				"resolved_slot_key": "selected_supplier",
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.normalize_master_data_lookup_slots",
			return_value={
				"lookup_mode": "candidate_resolution",
			},
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_label": "Myanmar Tech Import Services",
					"resolution_source": "exact_name",
				},
			},
		) as resolve_mock, patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-entity-scope-fallback",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="Myanmar Tech Import Services",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Myanmar Tech Import Services")
		self.assertEqual(
			resolve_mock.call_args.kwargs.get("search_text"),
			"Myanmar Tech Import Services",
		)

	def test_master_data_scope_unsupported_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-master-data-unsupported",
			compiler_reason="unsupported master-data scope",
			compiler_reason_type="master_data_scope_unsupported",
			compiler_details={
				"requested_entity_grain": "item",
				"supported_entity_grains": ["customer", "supplier"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"I can list customers or suppliers right now. I can't open items as a list yet.",
		)
		self.assertEqual(signal.suggested_options, ["customers", "suppliers"])
		self.assertEqual(
			(signal.internal_details or {}).get("clarification_template_group"),
			"unsupported_scope_clarification",
		)
		self.assertEqual(
			(signal.internal_details or {}).get("requested_label"),
			"items",
		)

	def test_master_data_scope_unsupported_pending_repeat_uses_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-master-data-unsupported-repeat",
			compiler_reason="unsupported master-data scope",
			compiler_reason_type="master_data_scope_unsupported",
			compiler_details={
				"requested_entity_grain": "item",
				"supported_entity_grains": ["customer", "supplier"],
			},
		)
		self.assertEqual(
			pending_clarification_repeat_answer(signal.to_payload()),
			"I still can't open items as a list. Please choose one of these instead: customers or suppliers.",
		)

	def test_generic_clarification_pending_meta_uses_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-generic-meta",
		)
		self.assertEqual(
			pending_clarification_meta_answer(signal.to_payload()),
			"I'm waiting for one more detail before I continue. Could you clarify the area or time period you want?",
		)

	def test_capability_ambiguity_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-capability-ambiguity",
			compiler_reason="capability ambiguity",
			compiler_reason_type="capability_ambiguity",
			compiler_details={
				"capability_candidates": ["sales_read", "stock_read"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"Which area would you like me to analyze: sales or inventory?",
		)
		self.assertEqual(signal.suggested_options, ["sales", "inventory"])

	def test_capability_missing_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-capability-missing",
			compiler_reason="capability missing",
			compiler_reason_type="capability_missing",
			compiler_details={},
		)
		self.assertEqual(
			signal.user_question,
			"Which business area would you like me to focus on: sales, AR / AP, financial statements, inventory, or product performance?",
		)
		self.assertEqual(
			signal.suggested_options,
			["sales", "AR / AP", "financial statements", "inventory", "product performance"],
		)

	def test_capability_missing_options_follow_metadata_business_area_order(self):
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_translation.list_capability_specs",
			return_value=[
				{
					"capability_id": "cap-b",
					"clarification_business_area_label": "inventory",
					"clarification_business_area_order": 40,
				},
				{
					"capability_id": "cap-a",
					"clarification_business_area_label": "sales",
					"clarification_business_area_order": 10,
				},
				{
					"capability_id": "cap-c",
					"clarification_business_area_label": "sales",
					"clarification_business_area_order": 20,
				},
			],
		):
			signal = translate_clarification_signal(
				request_id="clarify-capability-missing-metadata-order",
				compiler_reason="capability missing",
				compiler_reason_type="capability_missing",
				compiler_details={},
			)
		self.assertEqual(signal.suggested_options, ["sales", "inventory"])

	def test_request_underspecified_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-request-underspecified",
			compiler_reason="request underspecified",
			compiler_reason_type="request_underspecified",
			compiler_details={},
		)
		self.assertEqual(
			signal.user_question,
			"I can help with that, but I need one more detail before I proceed. Could you clarify the metric, scope, or period you want?",
		)
		self.assertEqual(signal.suggested_options, [])
		self.assertEqual(
			(signal.internal_details or {}).get("clarification_template_group"),
			"shared_clarification",
		)

	def test_report_ambiguity_financial_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-ambiguity",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
		)
		self.assertEqual(
			signal.suggested_options,
			["Profit and Loss", "Balance Sheet", "Cash Flow"],
		)

	def test_report_ambiguity_financial_wording_uses_metadata_display_labels_for_report_names(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-ambiguity-report-names",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
		)
		self.assertEqual(
			signal.suggested_options,
			["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
		)

	def test_validation_time_scope_wording_comes_from_metadata_templates(self):
		reason_contract = types.SimpleNamespace(
			request_id="clarify-time-validation",
			stage="validation",
			reason_type="validation_clarification",
			internal_reason="clarify",
			internal_details={
				"decision": "clarify",
				"time_scope_match": False,
			},
		)
		signal = translate_clarification_reason_contract(
			reason_contract=reason_contract,
		)
		self.assertEqual(
			signal.user_question,
			"I couldn't confirm the right period for that answer. Would you like me to try a different time scope?",
		)
		self.assertEqual(signal.suggested_options, ["today", "last month", "all time"])

	def test_report_ambiguity_resolution_accepts_financial_alias_variant(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-ambiguity-followup",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-report-followup",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="P & L",
				signal_payload=signal.to_payload(),
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertIn(
			"p&l",
			[
				str(value or "").strip().lower()
				for value in (
					(signal.internal_details or {}).get("option_aliases_by_option", {}).get("Profit and Loss Statement") or []
				)
			],
		)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss Statement")

	def test_report_ambiguity_resolution_accepts_financial_alias_variant_without_payload_aliases(self):
		signal_payload = {
			"stage": "compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
			"suggested_options": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			"internal_details": {},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-report-followup-no-payload-aliases",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="P & L",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss Statement")


	def test_report_ambiguity_resolution_accepts_financial_abbreviation_statement_variant(self):
		signal_payload = {
			"stage": "compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
			"suggested_options": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			"internal_details": {},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-report-followup-abbreviation",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="PL Statement",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss Statement")
		self.assertEqual(contract.resolved_slot.get("selected_report"), "Profit and Loss Statement")
		self.assertEqual(contract.resolved_slot.get("statement_variant"), "profit_and_loss")

	def test_report_ambiguity_resolution_accepts_compact_financial_abbreviation(self):
		signal_payload = {
			"stage": "compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
			"suggested_options": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			"internal_details": {},
		}
		contract = resolve_pending_clarification_response(
			request_id="clarify-report-followup-compact-abbreviation",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			message="PL",
			signal_payload=signal_payload,
			clarification_attempt_count=0,
			max_attempts=3,
			grounded_turn={},
		)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss Statement")
		self.assertEqual(contract.resolved_slot.get("statement_variant"), "profit_and_loss")

	def test_report_ambiguity_resolution_accepts_financial_spaced_alias_with_live_detectors(self):
		signal_payload = {
			"stage": "compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
			"suggested_options": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			"internal_details": {},
		}
		contract = resolve_pending_clarification_response(
			request_id="clarify-report-followup-spaced-alias",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			message="P & L",
			signal_payload=signal_payload,
			clarification_attempt_count=0,
			max_attempts=3,
			grounded_turn={},
		)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss Statement")
		self.assertIn(contract.matched_by, {"exact_token", "exact_token_alias"})
		self.assertEqual(contract.resolved_slot.get("selected_report"), "Profit and Loss Statement")
		self.assertEqual(contract.resolved_slot.get("statement_variant"), "profit_and_loss")

	def test_report_ambiguity_resolution_maps_display_option_to_canonical_report(self):
		signal_payload = {
			"stage": "compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?",
			"suggested_options": ["Profit and Loss", "Balance Sheet", "Cash Flow"],
			"internal_details": {},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-report-followup-display-option",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="Profit and Loss",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Profit and Loss")
		self.assertEqual(contract.resolved_slot.get("selected_report"), "Profit and Loss Statement")
		self.assertEqual(contract.resolved_slot.get("statement_variant"), "profit_and_loss")


	def test_report_ambiguity_translation_exposes_resolved_runtime_message(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-runtime-message",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			(signal.internal_details or {}).get("resolved_message_by_option", {}).get("Balance Sheet"),
			"show me Balance Sheet",
		)
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal.to_payload(),
				resolved_option="Balance Sheet",
			),
			"show me Balance Sheet",
		)

	def test_financial_summary_cross_domain_option_resolves_to_executable_message(self):
		signal = translate_clarification_signal(
			request_id="clarify-financial-summary-cross-domain",
			compiler_reason="Multiple areas are possible.",
			compiler_reason_type="financial_summary_multi_domain_clarification",
			compiler_details={},
		)
		contract = resolve_pending_clarification_response(
			request_id="clarify-financial-summary-cross-domain-response",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			message="combined cross-domain health summary",
			signal_payload=signal.to_payload(),
			clarification_attempt_count=0,
			max_attempts=3,
			grounded_turn={},
		)

		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "cross-domain health")
		self.assertEqual(contract.resolved_slot.get("intent_class"), "financial_summary")
		self.assertEqual(
			contract.resolved_slot.get("candidate_capability_ids"),
			["accounts_receivable_read", "accounts_payable_read"],
		)
		self.assertEqual(
			(contract.resolved_slot.get("extracted_slots") or {}).get("composite_profile_context"),
			["working_capital_health"],
		)
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal.to_payload(),
				resolved_option=contract.resolved_option,
			),
			"show me working capital health",
		)

	def test_financial_summary_single_area_option_resolves_to_next_safe_clarification(self):
		signal = translate_clarification_signal(
			request_id="clarify-financial-summary-single-area",
			compiler_reason="Multiple areas are possible.",
			compiler_reason_type="financial_summary_multi_domain_clarification",
			compiler_details={},
		)
		contract = resolve_pending_clarification_response(
			request_id="clarify-financial-summary-single-area-response",
			session_id="session-a",
			user_id="Administrator",
			site_name="erp.test",
			message="one specific area",
			signal_payload=signal.to_payload(),
			clarification_attempt_count=0,
			max_attempts=3,
			grounded_turn={},
		)

		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "one specific area")
		self.assertEqual(contract.resolved_slot.get("intent_class"), "financial_summary")
		self.assertEqual(contract.resolved_slot.get("requested_time_scope"), "as_of_today")
		self.assertEqual(contract.resolved_slot.get("ambiguity_flags"), ["ambiguous_capability"])

	def test_report_ambiguity_translation_carries_report_resolution_payload_fields(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-resolution-payload",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		details = signal.internal_details or {}
		self.assertEqual(details.get("clarification_template_group"), "shared_clarification")
		self.assertEqual(details.get("semantic_slot_name"), "statement_variant")
		self.assertEqual(
			(details.get("semantic_slot_value_by_option") or {}).get("Profit and Loss Statement"),
			"profit_and_loss",
		)
		self.assertEqual(
			(details.get("selected_report_by_option") or {}).get("Profit and Loss Statement"),
			"Profit and Loss Statement",
		)

	def test_report_ambiguity_pending_repeat_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-repeat",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			pending_clarification_repeat_answer(signal.to_payload()),
			"I still need you to choose the report before I continue: Profit and Loss Statement, Balance Sheet, or Cash Flow.",
		)

	def test_report_ambiguity_pending_empty_ack_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-empty-ack",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			pending_clarification_empty_ack_answer(signal.to_payload()),
			"I still need one of these choices before I continue: Profit and Loss Statement, Balance Sheet, or Cash Flow.",
		)

	def test_report_ambiguity_pending_fallback_stop_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-report-fallback-stop",
			compiler_reason="report ambiguity",
			compiler_reason_type="report_ambiguity",
			compiler_details={
				"report_candidates": ["Profit and Loss Statement", "Balance Sheet", "Cash Flow"],
			},
		)
		self.assertEqual(
			pending_clarification_fallback_stop_answer(signal.to_payload()),
			"I'll pause here rather than guess the report. When you come back, please choose one of these directly: Profit and Loss Statement, Balance Sheet, or Cash Flow.",
		)

	def test_governed_kpi_definition_pending_repeat_wording_comes_from_metadata_templates(self):
		payload = maybe_build_governed_kpi_frontdoor_response(
			request_id="clarify-kpi-definition-repeat",
			message="what is average order value",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		signal_payload = payload.get("clarification_signal_payload") or {}
		options = signal_payload.get("suggested_options") or []
		supported_options = " or ".join(options) if len(options) == 2 else ", ".join(options)
		self.assertEqual(
			(signal_payload.get("internal_details") or {}).get("clarification_template_group"),
			"shared_clarification",
		)
		self.assertEqual(
			pending_clarification_repeat_answer(signal_payload),
			f"I still need you to choose the approved basis before I continue: {supported_options}.",
		)

	def test_governed_kpi_definition_pending_fallback_wording_comes_from_metadata_templates(self):
		signal_payload = {
			"stage": "frontdoor",
			"reason_type": "governed_kpi_definition_ambiguity",
			"user_question": "I can calculate average order value, but I need the approved basis first.",
			"suggested_options": ["Average Order Value by Sales Order", "Average Order Value by Sales Invoice"],
			"internal_details": {
				"continuation_lane": "front_door",
				"continuation_intent_class": "governed_kpi_value",
				"clarification_template_group": "shared_clarification",
			},
		}
		self.assertEqual(
			(signal_payload.get("internal_details") or {}).get("clarification_template_group"),
			"shared_clarification",
		)
		self.assertEqual(
			pending_clarification_fallback_stop_answer(signal_payload),
			"I'll pause here rather than guess the approved basis. When you come back, please choose one of these directly: Average Order Value by Sales Order or Average Order Value by Sales Invoice.",
		)

	def test_composite_family_variation_pending_meta_wording_comes_from_metadata_templates(self):
		signal_payload = {
			"stage": "frontdoor",
			"reason_type": "composite_family_variation",
			"user_question": "I can rank products by margin, but I still need the primary metric.",
			"suggested_options": ["Gross Profit Amount", "Gross Profit Percent"],
			"internal_details": {
				"continuation_lane": "front_door",
				"continuation_intent_class": "governed_composite_value",
				"clarification_template_group": "shared_clarification",
			},
		}
		self.assertEqual(
			(signal_payload.get("internal_details") or {}).get("clarification_template_group"),
			"shared_clarification",
		)
		self.assertEqual(
			pending_clarification_meta_answer(signal_payload),
			"I'm waiting for one of these choices before I continue: Gross Profit Amount or Gross Profit Percent.",
		)

	def test_time_scope_pending_meta_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-time-meta",
			compiler_reason="time scope missing",
			compiler_reason_type="time_scope_missing",
			compiler_details={},
		)
		self.assertEqual(
			pending_clarification_meta_answer(signal.to_payload()),
			"I'm waiting for the time period before I continue: today, last month, or all time.",
		)

	def test_generic_clarification_fallback_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-generic-fallback",
		)
		self.assertEqual(
			signal.user_question,
			"I need one more detail before I continue. Could you clarify the area or time period you want?",
		)
		self.assertEqual(signal.suggested_options, [])

	def test_transaction_listing_surface_unsupported_wording_comes_from_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-listing-unsupported",
			compiler_reason="unsupported transaction listing surface",
			compiler_reason_type="transaction_listing_surface_unsupported",
			compiler_details={
				"requested_listing_view": "journal_entry",
				"supported_listing_views": ["sales_invoice", "purchase_invoice", "purchase_order"],
			},
		)
		self.assertEqual(
			signal.user_question,
			"I can't show journal entries as a list right now. I can show sales invoices, purchase invoices, or purchase orders instead. Which one would you like?",
		)
		self.assertEqual(
			signal.suggested_options,
			["sales invoices", "purchase invoices", "purchase orders"],
		)

	def test_transaction_listing_surface_unsupported_requested_only_uses_metadata_templates(self):
		signal = translate_clarification_signal(
			request_id="clarify-listing-unsupported-requested-only",
			compiler_reason="unsupported transaction listing surface",
			compiler_reason_type="transaction_listing_surface_unsupported",
			compiler_details={
				"requested_listing_view": "journal_entry",
				"supported_listing_views": [],
			},
		)
		self.assertEqual(
			signal.user_question,
			"I can't show journal entries as a list right now.",
		)
		self.assertEqual(signal.suggested_options, [])
		self.assertEqual(
			(signal.internal_details or {}).get("requested_label"),
			"journal entries",
		)

	def test_frontdoor_compound_request_option_resolution_returns_selected_subrequest(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "compound_request_clarification",
			"user_question": "I can help with both of those, but let's do one at a time. Which one would you like first?",
			"suggested_options": [
				"Payment entries",
				"Supplier list",
			],
			"internal_details": {
				"continuation_lane": "front_door",
				"resolved_message_by_option": {
					"Payment entries": "show me payment entries",
					"Supplier list": "give me some supplier list",
				},
				"option_aliases_by_option": {
					"Supplier list": [
						"give me some supplier list",
						"supplier list",
						"suppliers",
					]
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-compound",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="supplier list",
				signal_payload=signal_payload,
				clarification_attempt_count=0,
				max_attempts=3,
				grounded_turn={},
			)
		self.assertEqual(contract.decision, "resolved_option")
		self.assertEqual(contract.resolved_option, "Supplier list")
		self.assertEqual(contract.resolved_slot.get("selected_option"), "Supplier list")
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal_payload,
				resolved_option=contract.resolved_option,
			),
			"give me some supplier list",
		)
