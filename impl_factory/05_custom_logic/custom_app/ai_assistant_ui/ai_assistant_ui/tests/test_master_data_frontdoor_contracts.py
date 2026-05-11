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

from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	SemanticFreshQueryResult,
	_apply_master_data_frontdoor_assessment_to_interpretation,
	_augment_master_data_lookup_interpretation_from_message,
	compile_from_fresh_query_message,
)
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
	_build_interpretation_context,
)
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import evaluate_frontdoor_lane
from ai_assistant_ui.qwen_chat.master_data_frontdoor_support import (
	assess_master_data_frontdoor_request,
)


class TestMasterDataFrontDoorContracts(unittest.TestCase):
	def test_frontdoor_context_uses_governed_master_data_scope_activations(self):
		context = _build_interpretation_context()

		self.assertEqual(
			set(context.get("active_master_data_entity_grains") or []),
			{"customer", "supplier", "item"},
		)
		self.assertIn("directory_list", list(context.get("active_master_data_lookup_modes") or []))
		self.assertIn("candidate_resolution", list(context.get("active_master_data_lookup_modes") or []))
		self.assertIn("names_only", list(context.get("active_master_data_lookup_projections") or []))

	def test_master_data_frontdoor_assessment_resolves_supplier_directory(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-supplier-directory",
			message="give me some supplier list",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "supplier_master")
		self.assertEqual(assessment.entity_grain, "supplier")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.lookup_projection, "names_only")
		self.assertEqual(assessment.capability_id, "supplier_master_read")
		self.assertEqual(assessment.report_name, "Supplier Master List")
		self.assertIn("directory_list", list(assessment.allowed_lookup_modes))
		self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_resolves_supplier_directory_from_business_natural_show_phrase(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-supplier-directory-show",
			message="show me suppliers",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.entity_grain, "supplier")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.report_name, "Supplier Master List")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_resolves_metadata_backed_directory_aliases(self):
		examples = [
			("frontdoor-customer-directory-alias", "customer directory", "customer", "Customer Master List"),
			("frontdoor-supplier-master-alias", "supplier master", "supplier", "Supplier Master List"),
			("frontdoor-product-master-alias", "product master", "item", "Item Master List"),
		]
		for request_id, message, expected_grain, expected_report in examples:
			with self.subTest(message=message):
				payload = assess_master_data_frontdoor_request(
					request_id=request_id,
					message=message,
				)
				assessment = payload.get("assessment_contract")
				self.assertIsNotNone(assessment)
				self.assertEqual(assessment.status, "resolved")
				self.assertEqual(assessment.entity_grain, expected_grain)
				self.assertEqual(assessment.request_mode, "directory_list")
				self.assertEqual(assessment.report_name, expected_report)
				self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_resolves_customer_directory_from_business_natural_show_phrase(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-customer-directory-show",
			message="show me customers",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.entity_grain, "customer")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.report_name, "Customer Master List")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_customer_risk_levels_are_not_claimed_as_customer_master_list(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-customer-risk-levels",
			message="Display customer risk levels.",
			frontdoor_extracted_slots={
				"lookup_mode": "directory_list",
				"entity_grain": "customer",
			},
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "not_applicable")
		self.assertIsNone(payload.get("clarification_signal"))
		self.assertIn(
			"risk",
			(assessment.internal_details or {}).get("blocked_by_business_concepts", []),
		)

	def test_master_data_frontdoor_assessment_resolves_standard_directory_projection(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-customer-full-list",
			message="give me full customer list",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.entity_grain, "customer")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.lookup_projection, "standard_directory")

	def test_master_data_frontdoor_assessment_requires_grain_clarification_for_names(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-ambiguous-directory",
			message="give me some names",
		)
		assessment = payload.get("assessment_contract")
		signal = payload.get("clarification_signal")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "clarification_required")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(list(assessment.supported_entity_grains), ["customer", "supplier", "item"])
		self.assertIsNotNone(signal)
		self.assertEqual(signal.reason_type, "master_data_entity_grain_missing")
		self.assertIn("Which one would you like", signal.user_question)

	def test_master_data_frontdoor_assessment_prefers_typed_slots_before_alias_fallback(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-supplier-directory",
			message="give me some names",
			frontdoor_extracted_slots={
				"entity_grain": "supplier",
				"lookup_mode": "directory_list",
				"lookup_projection": "names_only",
			},
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "supplier_master")
		self.assertEqual(assessment.entity_grain, "supplier")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.lookup_projection, "names_only")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_typed_entity_grain_wins_over_conflicting_message_alias(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-grain-over-message-alias",
			message="give me some customer list",
			frontdoor_extracted_slots={
				"entity_grain": "supplier",
				"lookup_mode": "directory_list",
				"lookup_projection": "names_only",
			},
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "supplier_master")
		self.assertEqual(assessment.entity_grain, "supplier")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.lookup_projection, "names_only")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_typed_unsupported_grain_still_clarifies_honestly(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-unsupported-over-message-alias",
			message="give me some supplier list",
			frontdoor_extracted_slots={
				"entity_grain": "warehouse",
				"lookup_mode": "directory_list",
			},
		)
		assessment = payload.get("assessment_contract")
		signal = payload.get("clarification_signal")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "clarification_required")
		self.assertEqual(assessment.entity_grain, "warehouse")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.ambiguity_reason_type, "master_data_scope_unsupported")
		self.assertIsNotNone(signal)
		self.assertEqual(signal.reason_type, "master_data_scope_unsupported")
		self.assertIn("customers", signal.user_question.lower())
		self.assertIn("suppliers", signal.user_question.lower())
		self.assertIn("items", signal.user_question.lower())

	def test_master_data_frontdoor_assessment_uses_typed_mode_to_request_grain_clarification(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-clarification",
			message="names please",
			frontdoor_extracted_slots={
				"lookup_mode": "directory_list",
			},
		)
		assessment = payload.get("assessment_contract")
		signal = payload.get("clarification_signal")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "clarification_required")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertIsNotNone(signal)
		self.assertEqual(signal.reason_type, "master_data_entity_grain_missing")

	def test_master_data_grain_clarification_preserves_typed_lookup_search_text(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-search-carryover",
			message='do u have name similar to "Nay Lin Mobile"?',
			frontdoor_extracted_slots={
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Myanmar Tech Import",
			},
		)
		assessment = payload.get("assessment_contract")
		signal = payload.get("clarification_signal")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "clarification_required")
		self.assertEqual(assessment.request_mode, "candidate_resolution")
		self.assertEqual(assessment.lookup_search_text, "Myanmar Tech Import")
		self.assertIsNotNone(signal)
		self.assertEqual(
			(signal.internal_details or {}).get("carryover_slot_values", {}).get("lookup_search_text"),
			"Myanmar Tech Import",
		)
		self.assertEqual(
			(signal.internal_details or {}).get("resolved_message_by_option", {}).get("Suppliers"),
			'do u have supplier name similar to "Myanmar Tech Import"',
		)

	def test_master_data_frontdoor_assessment_resolves_item_directory(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-item-directory",
			message="give me some item list",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "item_master")
		self.assertEqual(assessment.entity_grain, "item")
		self.assertEqual(assessment.request_mode, "directory_list")
		self.assertEqual(assessment.lookup_projection, "names_only")
		self.assertEqual(assessment.capability_id, "item_master_read")
		self.assertEqual(assessment.report_name, "Item Master List")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_master_data_frontdoor_assessment_resolves_product_directory_alias_to_item_scope(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-product-directory",
			message="give me some product list",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "item_master")
		self.assertEqual(assessment.entity_grain, "item")
		self.assertEqual(assessment.report_name, "Item Master List")

	def test_master_data_frontdoor_assessment_normalizes_typed_product_alias_to_item_scope(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-typed-product-directory",
			message="give me some product list",
			frontdoor_extracted_slots={
				"entity_grain": "product",
				"lookup_mode": "directory_list",
			},
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "resolved")
		self.assertEqual(assessment.scope_id, "item_master")
		self.assertEqual(assessment.entity_grain, "item")
		self.assertEqual(assessment.report_name, "Item Master List")

	def test_evaluate_frontdoor_lane_attaches_resolved_master_data_assessment(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=0.99,
					reason="The request should continue through the main lanes.",
				),
				confidence_threshold=0.8,
			),
		):
			_, frontdoor_contract, _, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-route-supplier",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="give me some supplier list",
				recent_messages=[],
				grounded_context_available=False,
				latest_grounded_turn=None,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=None,
			)
		self.assertEqual(frontdoor_contract.intent_class, "route_onward")
		self.assertEqual(frontdoor_answer, "")
		assessment = frontdoor_contract.response_payload.get("master_data_frontdoor_assessment", {})
		self.assertEqual(assessment.get("status"), "resolved")
		self.assertEqual(assessment.get("entity_grain"), "supplier")

	def test_evaluate_frontdoor_lane_consumes_typed_frontdoor_slots_first(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=0.99,
					reason="The request should continue through the main lanes.",
					extracted_slots={
						"entity_grain": "supplier",
						"lookup_mode": "directory_list",
						"lookup_projection": "names_only",
					},
				),
				confidence_threshold=0.8,
			),
		):
			_, frontdoor_contract, _, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-typed-route-supplier",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="give me some names",
				recent_messages=[],
				grounded_context_available=False,
				latest_grounded_turn=None,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=None,
			)
		self.assertEqual(frontdoor_contract.intent_class, "route_onward")
		self.assertEqual(frontdoor_answer, "")
		assessment = frontdoor_contract.response_payload.get("master_data_frontdoor_assessment", {})
		self.assertEqual(assessment.get("status"), "resolved")
		self.assertEqual(assessment.get("entity_grain"), "supplier")
		self.assertEqual(assessment.get("request_mode"), "directory_list")

	def test_evaluate_frontdoor_lane_handles_master_data_grain_clarification(self):
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.interpret_front_door_semantically",
			return_value=SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=0.99,
					reason="The request should continue through the main lanes.",
				),
				confidence_threshold=0.8,
			),
		):
			_, frontdoor_contract, _, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="frontdoor-ambiguous-master-data",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="give me some names",
				recent_messages=[],
				grounded_context_available=False,
				latest_grounded_turn=None,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=None,
			)
		self.assertEqual(frontdoor_contract.intent_class, "master_data_grain_clarification")
		self.assertEqual(frontdoor_contract.response_mode, "clarification_signal")
		self.assertIn("Which one would you like", frontdoor_answer)
		self.assertTrue(frontdoor_contract.response_payload.get("clarification_signal_payload"))

	def test_compile_flow_seeds_master_data_interpretation_before_surface_fallback(self):
		captured = {}

		def fake_requires_deterministic_surface_rescue(result):
			captured["intent_class"] = str(getattr(getattr(result, "interpretation", None), "intent_class", "") or "").strip()
			captured["entity_grain"] = str(
				getattr(getattr(result, "interpretation", None), "extracted_slots", {}).get("entity_grain") or ""
			).strip()
			captured["scope_id"] = str(
				getattr(getattr(result, "interpretation", None), "extracted_slots", {}).get("scope_id") or ""
			).strip()
			captured["candidate_capability_ids"] = list(
				getattr(getattr(result, "interpretation", None), "candidate_capability_ids", [])
			)
			captured["candidate_reports"] = list(
				getattr(getattr(result, "interpretation", None), "candidate_reports", [])
			)
			return False

		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			return_value=SemanticFreshQueryResult(
				status="accepted",
				interpretation=None,
				confidence_threshold=0.8,
				runtime_error="",
				validation_error="",
				agent_meta={},
			),
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter._semantic_result_requires_deterministic_surface_rescue",
			side_effect=fake_requires_deterministic_surface_rescue,
		), patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter._compile_pipeline_from_semantic_result",
			return_value={},
		):
			compile_from_fresh_query_message(
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="give me some supplier list",
				recent_messages=[],
				front_door_contract={
					"response_payload": {
						"master_data_frontdoor_assessment": {
							"status": "resolved",
							"scope_id": "supplier_master",
							"entity_grain": "supplier",
							"request_mode": "directory_list",
							"lookup_projection": "names_only",
							"lookup_search_text": "",
							"capability_id": "supplier_master_read",
							"report_name": "Supplier Master List",
							"allowed_lookup_modes": ["directory_list", "candidate_resolution"],
							"internal_details": {"lookup_limit": 10},
						}
					}
				},
			)
		self.assertEqual(captured.get("intent_class"), "master_data_lookup")
		self.assertEqual(captured.get("scope_id"), "supplier_master")
		self.assertEqual(captured.get("entity_grain"), "supplier")
		self.assertEqual(captured.get("candidate_capability_ids"), ["supplier_master_read"])
		self.assertEqual(captured.get("candidate_reports"), ["Supplier Master List"])

	def test_frontdoor_candidate_resolution_still_attaches_entity_reference_resolution(self):
		interpretation = _apply_master_data_frontdoor_assessment_to_interpretation(
			request_id="frontdoor-customer-resolution",
			session_id="session-a",
			interpretation=None,
			assessment_payload={
				"status": "resolved",
				"scope_id": "customer_master",
				"entity_grain": "customer",
				"request_mode": "candidate_resolution",
				"lookup_projection": "names_only",
				"lookup_search_text": "Nay Lin Mobile",
				"capability_id": "customer_master_read",
				"report_name": "Customer Master List",
				"allowed_lookup_modes": ["directory_list", "candidate_resolution"],
				"internal_details": {"lookup_limit": 10},
			},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_type": "customer",
					"entity_key": "Ko Nay Lin Mobile Center",
					"entity_label": "Ko Nay Lin Mobile Center",
					"resolution_source": "governed_fuzzy",
				},
			},
		):
			augmented = _augment_master_data_lookup_interpretation_from_message(
				message='do u have customer name similar to "Nay Lin Mobile"?',
				interpretation=interpretation,
			)
		self.assertEqual(augmented.intent_class, "master_data_lookup")
		self.assertEqual(augmented.extracted_slots.get("lookup_mode"), "candidate_resolution")
		self.assertEqual(
			augmented.extracted_slots.get("entity_reference_resolution", {}).get("resolution_status"),
			"resolved",
		)
		self.assertEqual(
			augmented.extracted_slots.get("filters", {}).get("name"),
			"Ko Nay Lin Mobile Center",
		)

	def test_master_data_lookup_augmentation_prefers_typed_lookup_slots_before_message_alias_fallback(self):
		interpretation = _apply_master_data_frontdoor_assessment_to_interpretation(
			request_id="frontdoor-supplier-resolution",
			session_id="session-a",
			interpretation=None,
			assessment_payload={
				"status": "resolved",
				"scope_id": "supplier_master",
				"entity_grain": "supplier",
				"request_mode": "candidate_resolution",
				"lookup_projection": "names_only",
				"lookup_search_text": "Myanmar Tech Import",
				"capability_id": "supplier_master_read",
				"report_name": "Supplier Master List",
				"allowed_lookup_modes": ["directory_list", "candidate_resolution"],
				"internal_details": {"lookup_limit": 10},
			},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_type": "supplier",
					"entity_key": "Myanmar Tech Import Services",
					"entity_label": "Myanmar Tech Import Services",
					"resolution_source": "governed_fuzzy",
				},
			},
		) as resolution_mock:
			augmented = _augment_master_data_lookup_interpretation_from_message(
				message='do u have customer name similar to "Nay Lin Mobile"?',
				interpretation=interpretation,
			)
		self.assertEqual(augmented.intent_class, "master_data_lookup")
		self.assertEqual(augmented.extracted_slots.get("entity_grain"), "supplier")
		self.assertEqual(augmented.extracted_slots.get("lookup_mode"), "candidate_resolution")
		self.assertEqual(augmented.extracted_slots.get("lookup_search_text"), "Myanmar Tech Import")
		self.assertEqual(
			augmented.extracted_slots.get("filters", {}).get("name"),
			"Myanmar Tech Import Services",
		)
		self.assertEqual(resolution_mock.call_args.kwargs.get("entity_grain"), "supplier")
		self.assertEqual(
			resolution_mock.call_args.kwargs.get("search_text"),
			"Myanmar Tech Import",
		)

	def test_frontdoor_profile_target_for_customer_is_not_claimed_by_lookup_family(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-profile-target-customer",
			message="tell me more about customer Ko Nay Lin Mobile Center",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "not_applicable")
		self.assertEqual(assessment.entity_grain, "customer")
		self.assertEqual(assessment.request_mode, "profile_target")
		self.assertIsNone(payload.get("clarification_signal"))

	def test_frontdoor_profile_target_for_item_is_not_claimed_by_lookup_family(self):
		payload = assess_master_data_frontdoor_request(
			request_id="frontdoor-profile-target-item",
			message="tell me more about Demo Item",
		)
		assessment = payload.get("assessment_contract")
		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "not_applicable")
		self.assertEqual(assessment.entity_grain, "item")
		self.assertEqual(assessment.request_mode, "profile_target")
		self.assertIsNone(payload.get("clarification_signal"))


if __name__ == "__main__":
	unittest.main()
