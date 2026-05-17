import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import _apply_clarification_resolution_to_interpretation
from ai_assistant_ui.qwen_chat.master_data_frontdoor_support import assess_master_data_frontdoor_request
from ai_assistant_ui.qwen_chat.clarification_resolution import resolve_pending_clarification_response


class TestMasterDataClarificationCarryoverContracts(unittest.TestCase):
	def test_master_data_entity_grain_clarification_declares_typed_slot_carryover(self):
		assessment = assess_master_data_frontdoor_request(
			request_id="master-data-frontdoor-clarify",
			message="give me some names",
			frontdoor_extracted_slots={"lookup_mode": "directory_list"},
		)
		signal = assessment.get("clarification_signal")
		self.assertIsNotNone(signal)
		internal_details = dict(signal.internal_details or {})
		self.assertEqual(internal_details.get("semantic_slot_name"), "entity_grain")
		self.assertEqual(
			internal_details.get("semantic_slot_value_by_option", {}).get("Customers"),
			"customer",
		)
		self.assertEqual(
			internal_details.get("semantic_slot_value_by_option", {}).get("Suppliers"),
			"supplier",
		)
		self.assertEqual(
			internal_details.get("semantic_slot_value_by_option", {}).get("Items"),
			"item",
		)
		self.assertEqual(
			internal_details.get("carryover_slot_values", {}).get("lookup_mode"),
			"directory_list",
		)

	def test_master_data_entity_grain_resolution_carries_typed_slots(self):
		signal_payload = {
			"stage": "front_door",
			"reason_type": "master_data_entity_grain_missing",
			"user_question": "I can help with customers or suppliers or items. Which one would you like?",
			"suggested_options": ["Customers", "Suppliers", "Items"],
			"internal_details": {
				"continuation_lane": "front_door",
				"resolved_message_by_option": {
					"Customers": "give me some customer list",
					"Suppliers": "give me some supplier list",
					"Items": "give me some item list",
				},
				"option_aliases_by_option": {
					"Customers": ["customer", "customers"],
					"Suppliers": ["supplier", "suppliers"],
					"Items": ["item", "items", "product", "products"],
				},
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
		contract = resolve_pending_clarification_response(
			request_id="clarify-master-data-carryover",
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
		self.assertEqual(contract.resolved_slot.get("entity_grain"), "supplier")
		self.assertEqual(contract.resolved_slot.get("lookup_mode"), "directory_list")
		self.assertEqual(contract.resolved_slot.get("lookup_projection"), "names_only")

	def test_clarification_resolution_updates_master_data_interpretation_slots(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="master-data-interpretation",
			session_id="session-a",
			intent_class="master_data_lookup",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=["ambiguous_capability"],
			ambiguity_reason="Need clarification.",
			confidence=0.8,
		)
		updated = _apply_clarification_resolution_to_interpretation(
			interpretation=interpretation,
			clarification_resolution={
				"decision": "resolved_option",
				"resolved_slot": {
					"entity_grain": "supplier",
					"lookup_mode": "directory_list",
					"lookup_projection": "names_only",
					"lookup_search_text": "Myanmar Tech Import",
				},
			},
		)
		self.assertEqual(updated.extracted_slots.get("entity_grain"), "supplier")
		self.assertEqual(updated.extracted_slots.get("lookup_mode"), "directory_list")
		self.assertEqual(updated.extracted_slots.get("lookup_projection"), "names_only")
		self.assertEqual(updated.extracted_slots.get("lookup_search_text"), "Myanmar Tech Import")
		self.assertEqual(list(updated.requested_dimensions), ["Supplier"])


if __name__ == "__main__":
	unittest.main()
