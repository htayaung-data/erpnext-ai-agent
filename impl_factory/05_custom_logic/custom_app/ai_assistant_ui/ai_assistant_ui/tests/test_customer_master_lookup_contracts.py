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

from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
from ai_assistant_ui.qwen_chat.entity_reference_resolution import (
	infer_entity_grains_from_message,
	infer_lookup_mode_from_message,
	infer_master_data_lookup_slots,
	resolve_entity_reference_from_message,
)
from ai_assistant_ui.qwen_chat.family_adapters import _master_directory_context, build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_augment_master_data_lookup_interpretation_from_message,
	_deterministic_family_surface_interpretation,
)
from ai_assistant_ui.qwen_chat.semantic_resolution import (
	resolve_master_data_lookup_interpretation,
)


class TestCustomerMasterLookupContracts(unittest.TestCase):
	def test_deterministic_customer_names_surface_uses_governed_customer_master(self):
		contract = _deterministic_family_surface_interpretation(
			request_id="customer-master-surface",
			session_id="session-a",
			message="give me some customer names",
			confidence_threshold=0.72,
		)
		self.assertIsNotNone(contract)
		self.assertEqual(contract.intent_class, "master_data_lookup")
		self.assertEqual(list(contract.candidate_capability_ids), ["customer_master_read"])
		self.assertEqual(list(contract.candidate_reports), ["Customer Master List"])
		self.assertEqual(list(contract.requested_dimensions), ["Customer"])
		self.assertEqual(contract.extracted_slots.get("entity_grain"), "customer")
		self.assertEqual(contract.extracted_slots.get("lookup_mode"), "directory_list")
		self.assertEqual(contract.extracted_slots.get("lookup_projection"), "names_only")

	def test_deterministic_supplier_names_surface_uses_governed_scope_rule_before_fallback(self):
		contract = _deterministic_family_surface_interpretation(
			request_id="supplier-master-surface",
			session_id="session-a",
			message="give me some supplier names",
			confidence_threshold=0.72,
		)
		self.assertIsNotNone(contract)
		self.assertEqual(contract.intent_class, "master_data_lookup")
		self.assertEqual(list(contract.candidate_capability_ids), ["supplier_master_read"])
		self.assertEqual(list(contract.candidate_reports), ["Supplier Master List"])
		self.assertEqual(list(contract.requested_dimensions), ["Supplier"])
		self.assertEqual(contract.extracted_slots.get("entity_grain"), "supplier")

	def test_master_data_lookup_slot_inference_uses_governed_alias_policy(self):
		slots = infer_master_data_lookup_slots(
			message="tell me more about Ko Nay Lin Mobile Center",
			entity_grain="customer",
		)
		self.assertEqual(slots.get("lookup_mode"), "profile_target")
		self.assertEqual(slots.get("lookup_projection"), "names_only")
		self.assertEqual(slots.get("lookup_search_text"), "Ko Nay Lin Mobile Center")
		self.assertEqual(slots.get("lookup_limit"), 10)

	def test_entity_grain_and_lookup_mode_inference_support_business_natural_show_plural_requests(self):
		self.assertEqual(list(infer_entity_grains_from_message("show me suppliers")), ["supplier"])
		self.assertEqual(infer_lookup_mode_from_message("show me suppliers"), "directory_list")
		self.assertEqual(list(infer_entity_grains_from_message("show me customers")), ["customer"])
		self.assertEqual(infer_lookup_mode_from_message("show me customers"), "directory_list")

	def test_master_data_lookup_augmentation_uses_governed_entity_resolution(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="customer-master-filter",
			session_id="session-a",
			intent_class="master_data_lookup",
			candidate_capability_ids=["customer_master_read"],
			candidate_reports=["Customer Master List"],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="",
			target_limit=0,
			requested_presentation=[],
			extracted_slots={"entity_grain": "customer"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.93,
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
				message="do u have customer name similar to Ko Nay Lin Mobile",
				interpretation=interpretation,
			)
		self.assertEqual(augmented.extracted_slots.get("filters", {}).get("name"), "Ko Nay Lin Mobile Center")
		self.assertEqual(augmented.extracted_slots.get("lookup_mode"), "candidate_resolution")
		self.assertEqual(
			augmented.extracted_slots.get("entity_reference_resolution", {}).get("resolution_status"),
			"resolved",
		)

	def test_governed_customer_resolution_matches_partial_name(self):
		with patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.exists",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.get_value",
			return_value=None,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.get_all",
			return_value=[
				{"name": "Ko Nay Lin Mobile Center", "customer_name": "Ko Nay Lin Mobile Center"},
				{"name": "Zegyo Mobile Supply House", "customer_name": "Zegyo Mobile Supply House"},
			],
		):
			resolution = resolve_entity_reference_from_message(
				request_id="customer-master-fuzzy",
				entity_grain="customer",
				message='do u have customer name similar to "Nay Lin Mobile"?',
				lookup_mode="candidate_resolution",
				search_text="Nay Lin Mobile",
			)
		self.assertEqual(resolution.get("resolution_status"), "resolved")
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("entity_key"),
			"Ko Nay Lin Mobile Center",
		)
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("resolution_source"),
			"governed_fuzzy",
		)

	def test_governed_supplier_resolution_matches_partial_name(self):
		with patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.exists",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.get_value",
			return_value=None,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.get_all",
			return_value=[
				{"name": "Myanmar Tech Import Services", "supplier_name": "Myanmar Tech Import Services"},
				{"name": "Sunflower Accessories Co.", "supplier_name": "Sunflower Accessories Co."},
			],
		):
			resolution = resolve_entity_reference_from_message(
				request_id="supplier-master-fuzzy",
				entity_grain="supplier",
				message='do u have supplier name similar to "Myanmar Tech Import"?',
				lookup_mode="candidate_resolution",
				search_text="Myanmar Tech Import",
			)
		self.assertEqual(resolution.get("resolution_status"), "resolved")
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("entity_key"),
			"Myanmar Tech Import Services",
		)
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("resolution_source"),
			"governed_fuzzy",
		)

	def test_entity_reference_resolution_prefers_typed_search_text_over_message_alias_fallback(self):
		with patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.exists",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.get_value",
			return_value=None,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.get_all",
			return_value=[
				{"name": "Myanmar Tech Import Services", "supplier_name": "Myanmar Tech Import Services"},
				{"name": "Sunflower Accessories Co.", "supplier_name": "Sunflower Accessories Co."},
			],
		):
			resolution = resolve_entity_reference_from_message(
				request_id="supplier-master-typed-search-text",
				entity_grain="supplier",
				message='do u have customer name similar to "Nay Lin Mobile"?',
				lookup_mode="candidate_resolution",
				search_text="Myanmar Tech Import",
			)
		self.assertEqual(resolution.get("resolution_status"), "resolved")
		self.assertEqual(resolution.get("lookup_mode"), "candidate_resolution")
		self.assertEqual(resolution.get("search_text"), "Myanmar Tech Import")
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("entity_key"),
			"Myanmar Tech Import Services",
		)

	def test_entity_reference_resolution_accepts_active_item_profile_target_mode(self):
		with patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.exists",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.entity_reference_resolution.frappe.db.get_value",
			side_effect=lambda doctype, filters=None, fieldname=None, as_dict=False: (
				{"name": "ITEM-001", "item_name": "Demo Item"}
				if doctype == "Item"
				and isinstance(filters, dict)
				and filters.get("item_name") == "Demo Item"
				and as_dict
				else None
			),
		):
			resolution = resolve_entity_reference_from_message(
				request_id="item-master-profile-target",
				entity_grain="item",
				message="tell me more about Demo Item",
				lookup_mode="profile_target",
				search_text="Demo Item",
			)
		self.assertEqual(resolution.get("resolution_status"), "resolved")
		self.assertEqual(resolution.get("lookup_mode"), "profile_target")
		self.assertEqual(resolution.get("search_text"), "Demo Item")
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("entity_key"),
			"ITEM-001",
		)
		self.assertEqual(
			resolution.get("resolved_entity", {}).get("entity_label"),
			"Demo Item",
		)

	def test_customer_master_family_renders_customer_names_cleanly(self):
		compiler_contract = {
			"selected_report": "Customer Master List",
			"capability_id": "customer_master_read",
			"requested_dimensions": ["Customer"],
			"requested_metrics": [],
			"target_limit": 5,
		}
		with patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_rows",
			return_value=[
				{"name": "Ko Nay Lin Mobile Center", "customer_name": "Ko Nay Lin Mobile Center"},
				{"name": "Zegyo Mobile Supply House", "customer_name": "Zegyo Mobile Supply House"},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_filters",
			return_value={},
		):
			outcome = build_normalized_family_artifact(
				request_id="customer-master-render",
				compiler_contract=compiler_contract,
				runtime_payload={},
				intent_class="master_data_lookup",
			)
		self.assertEqual(outcome.status, "adapted")
		rendered = render_normalized_family_response(
			request_id="customer-master-render",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertIn("Ko Nay Lin Mobile Center", rendered.contract.answer_text)
		self.assertIn("Zegyo Mobile Supply House", rendered.contract.answer_text)

	def test_customer_master_family_preserves_standard_directory_projection_from_slots(self):
		compiler_contract = {
			"selected_report": "Customer Master List",
			"capability_id": "customer_master_read",
			"requested_dimensions": ["Customer"],
			"requested_metrics": [],
			"target_limit": 5,
			"extracted_slots": {
				"entity_grain": "customer",
				"scope_id": "customer_master",
				"lookup_mode": "directory_list",
				"lookup_projection": "standard_directory",
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_rows",
			return_value=[
				{
					"name": "Ko Nay Lin Mobile Center",
					"customer_name": "Ko Nay Lin Mobile Center",
					"territory": "Mandalay",
					"customer_group": "Wholesale",
					"creation": "2026-02-12 08:00:00",
					"disabled": 0,
					"is_frozen": 0,
				},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_filters",
			return_value={},
		):
			outcome = build_normalized_family_artifact(
				request_id="customer-master-standard-directory",
				compiler_contract=compiler_contract,
				runtime_payload={},
				intent_class="master_data_lookup",
			)
		self.assertEqual(outcome.status, "adapted")
		self.assertEqual(outcome.artifact_contract.dimensions.get("lookup_projection"), "standard_directory")
		self.assertEqual(outcome.artifact_contract.dimensions.get("scope_id"), "customer_master")
		self.assertEqual(outcome.artifact_contract.dimensions.get("requested_columns"), [])
		rendered = render_normalized_family_response(
			request_id="customer-master-standard-directory",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertIn("| Customer | Created Date | Territory | Customer Group | Status |", rendered.contract.answer_text)
		self.assertIn("| Ko Nay Lin Mobile Center | 2026-02-12 | Mandalay | Wholesale | Active |", rendered.contract.answer_text)

	def test_master_directory_context_uses_governed_entity_labels(self):
		def _label(grain, plural=False):
			if grain == "supplier":
				return "vendors" if plural else "vendor"
			if grain == "customer":
				return "clients" if plural else "client"
			return ""

		with patch("ai_assistant_ui.qwen_chat.master_data_directory_support.entity_grain_display_label", side_effect=_label):
			supplier_context = _master_directory_context("Supplier Master List")
			customer_context = _master_directory_context("Customer Master List")

		self.assertEqual(supplier_context.get("entity_label"), "Vendor")
		self.assertEqual(supplier_context.get("entity_plural_label"), "Vendors")
		self.assertEqual(customer_context.get("entity_label"), "Client")
		self.assertEqual(customer_context.get("entity_plural_label"), "Clients")

	def test_supplier_master_family_renders_supplier_names_cleanly(self):
		compiler_contract = {
			"selected_report": "Supplier Master List",
			"capability_id": "supplier_master_read",
			"requested_dimensions": ["Supplier"],
			"requested_metrics": [],
			"target_limit": 5,
		}
		with patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_rows",
			return_value=[
				{"name": "Myanmar Tech Import Services", "supplier_name": "Myanmar Tech Import Services"},
				{"name": "Sunflower Accessories Co.", "supplier_name": "Sunflower Accessories Co."},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_filters",
			return_value={},
		):
			outcome = build_normalized_family_artifact(
				request_id="supplier-master-render",
				compiler_contract=compiler_contract,
				runtime_payload={},
				intent_class="master_data_lookup",
			)
		self.assertEqual(outcome.status, "adapted")
		rendered = render_normalized_family_response(
			request_id="supplier-master-render",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertIn("Myanmar Tech Import Services", rendered.contract.answer_text)
		self.assertIn("Sunflower Accessories Co.", rendered.contract.answer_text)

	def test_customer_master_family_renders_typed_candidate_resolution(self):
		compiler_contract = {
			"selected_report": "Customer Master List",
			"capability_id": "customer_master_read",
			"requested_dimensions": ["Customer"],
			"requested_metrics": [],
			"target_limit": 5,
			"extracted_slots": {
				"entity_grain": "customer",
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Nay Lin Mobile",
				"entity_reference_resolution": {
					"resolution_status": "resolved",
					"resolved_entity": {
						"entity_type": "customer",
						"entity_key": "Ko Nay Lin Mobile Center",
						"entity_label": "Ko Nay Lin Mobile Center",
						"resolution_source": "governed_fuzzy",
					},
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_rows",
			return_value=[
				{"name": "Ko Nay Lin Mobile Center", "customer_name": "Ko Nay Lin Mobile Center"},
				{"name": "Zegyo Mobile Supply House", "customer_name": "Zegyo Mobile Supply House"},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_filters",
			return_value={},
		):
			outcome = build_normalized_family_artifact(
				request_id="customer-master-resolution-render",
				compiler_contract=compiler_contract,
				runtime_payload={},
				intent_class="master_data_lookup",
			)
		rendered = render_normalized_family_response(
			request_id="customer-master-resolution-render",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertIn("closest customer match", rendered.contract.answer_text.lower())
		self.assertIn("Ko Nay Lin Mobile Center", rendered.contract.answer_text)
		self.assertNotIn("Zegyo Mobile Supply House", rendered.contract.answer_text)

	def test_supplier_master_family_renders_typed_candidate_resolution(self):
		compiler_contract = {
			"selected_report": "Supplier Master List",
			"capability_id": "supplier_master_read",
			"requested_dimensions": ["Supplier"],
			"requested_metrics": [],
			"target_limit": 5,
			"extracted_slots": {
				"entity_grain": "supplier",
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Myanmar Tech Import",
				"entity_reference_resolution": {
					"resolution_status": "resolved",
					"resolved_entity": {
						"entity_type": "supplier",
						"entity_key": "Myanmar Tech Import Services",
						"entity_label": "Myanmar Tech Import Services",
						"resolution_source": "governed_fuzzy",
					},
				},
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_rows",
			return_value=[
				{"name": "Myanmar Tech Import Services", "supplier_name": "Myanmar Tech Import Services"},
				{"name": "Sunflower Accessories Co.", "supplier_name": "Sunflower Accessories Co."},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.family_adapters._report_filters",
			return_value={},
		):
			outcome = build_normalized_family_artifact(
				request_id="supplier-master-resolution-render",
				compiler_contract=compiler_contract,
				runtime_payload={},
				intent_class="master_data_lookup",
			)
		rendered = render_normalized_family_response(
			request_id="supplier-master-resolution-render",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		self.assertIn("closest supplier match", rendered.contract.answer_text.lower())
		self.assertIn("Myanmar Tech Import Services", rendered.contract.answer_text)
		self.assertNotIn("Sunflower Accessories Co.", rendered.contract.answer_text)

	def test_master_data_resolution_executes_customer_directory_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="customer-master-semantic",
			session_id="session-a",
			intent_class="master_data_lookup",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			target_limit=0,
			requested_presentation=[],
			extracted_slots={"entity_grain": "customer"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_master_data_lookup_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("entity_grain"), "customer")
		self.assertEqual(outcome.contract.scope_id, "customer_master")
		self.assertEqual(outcome.interpretation.extracted_slots.get("scope_id"), "customer_master")
		self.assertEqual(list(outcome.interpretation.candidate_capability_ids), ["customer_master_read"])
		self.assertEqual(list(outcome.interpretation.candidate_reports), ["Customer Master List"])

	def test_master_data_resolution_executes_supplier_directory_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="supplier-master-semantic",
			session_id="session-a",
			intent_class="master_data_lookup",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			target_limit=0,
			requested_presentation=[],
			extracted_slots={"entity_grain": "supplier"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_master_data_lookup_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "execute")
		self.assertEqual(outcome.contract.resolved_slots.get("entity_grain"), "supplier")
		self.assertEqual(outcome.contract.scope_id, "supplier_master")
		self.assertEqual(outcome.interpretation.extracted_slots.get("scope_id"), "supplier_master")
		self.assertEqual(list(outcome.interpretation.candidate_capability_ids), ["supplier_master_read"])
		self.assertEqual(list(outcome.interpretation.candidate_reports), ["Supplier Master List"])

	def test_master_data_resolution_rejects_profile_target_mode_for_lookup_family(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="customer-master-profile-target",
			session_id="session-a",
			intent_class="master_data_lookup",
			candidate_capability_ids=[],
			candidate_reports=[],
			requested_dimensions=["Customer"],
			requested_metrics=[],
			requested_time_scope="",
			target_limit=0,
			requested_presentation=[],
			extracted_slots={"entity_grain": "customer", "lookup_mode": "profile_target"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_master_data_lookup_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.governed_decision, "clarify")
		self.assertEqual(outcome.clarification_reason_type, "master_data_mode_unsupported")
		self.assertEqual(outcome.contract.resolved_slots.get("lookup_mode"), "profile_target")
