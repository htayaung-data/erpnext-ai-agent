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
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import entity_detail as entity_detail_module
from ai_assistant_ui.qwen_chat import boundary_support as boundary_support_module
from ai_assistant_ui.qwen_chat import contracts as contracts_module
from ai_assistant_ui.qwen_chat import evidence_response_support as evidence_response_support_module
from ai_assistant_ui.qwen_chat import entity_dimension_support as entity_dimension_support_module
from ai_assistant_ui.qwen_chat import entity_detail_request_support as entity_detail_request_support_module
from ai_assistant_ui.qwen_chat import artifact_reference_support as artifact_reference_support_module
from ai_assistant_ui.qwen_chat.customer_lifecycle_basis import customer_lifecycle_supported_focus_grains
from ai_assistant_ui.qwen_chat.document_event_basis import (
	document_event_basis_specs,
	document_event_question_type_shape_map,
	document_event_supported_focus_grains,
)


class _FakeDoc:
	def __init__(self, **kwargs):
		self._payload = dict(kwargs)
		for key, value in kwargs.items():
			setattr(self, key, value)

	def get(self, key, default=None):
		return self._payload.get(key, default)


class TestEntityDetailContracts(unittest.TestCase):
	def test_resolve_entity_detail_executor_covers_supported_types(self):
		self.assertIsNotNone(entity_detail_module._resolve_entity_detail_executor("customer"))
		self.assertIsNotNone(entity_detail_module._resolve_entity_detail_executor("supplier"))
		self.assertIsNotNone(entity_detail_module._resolve_entity_detail_executor("item"))
		self.assertIsNotNone(entity_detail_module._resolve_entity_detail_executor("sales_invoice"))
		self.assertIsNotNone(entity_detail_module._resolve_entity_detail_executor("purchase_order"))
		self.assertIsNone(entity_detail_module._resolve_entity_detail_executor("unsupported_entity"))

	def test_entity_detail_response_builder_preserves_shared_contract_shape(self):
		outcome = entity_detail_module._entity_detail_response(
			detail_company="Enterprise Co",
			entity_type="item",
			entity_key="ITEM-001",
			entity_label="Demo Item",
			title="Demo Item Details",
			source_reports=["Item", "Bin", "Item"],
			blocks=[entity_detail_module._summary_block("Profile", [("Item Code", "ITEM-001")])],
			metrics={"total_amount": 1200},
			sections={"summary": [{"label": "Item Code", "value": "ITEM-001"}]},
			primary_metric_key="total_amount",
			primary_metric_label="Total Amount",
			source_grain="item_detail",
		)
		rendered = outcome.get("rendered") or {}
		artifact = outcome.get("artifact") or {}
		self.assertEqual(rendered.get("title"), "Demo Item Details")
		self.assertEqual(rendered.get("source_reports"), ["Item", "Bin"])
		self.assertEqual((artifact.get("dimensions") or {}).get("entity_type"), "item")
		self.assertEqual((artifact.get("dimensions") or {}).get("entity_key"), "ITEM-001")
		self.assertEqual((artifact.get("dimensions") or {}).get("source_grain"), "item_detail")
		self.assertEqual((artifact.get("filters") or {}).get("company"), "Enterprise Co")
		self.assertEqual((artifact.get("metrics") or {}).get("total_amount"), 1200)

	def test_document_detail_response_builder_preserves_document_sections(self):
		outcome = entity_detail_module._document_detail_response(
			detail_company="Enterprise Co",
			entity_type="sales_invoice",
			entity_key="SINV-001",
			entity_label="SINV-001",
			title="Sales Invoice SINV-001",
			source_report="Sales Invoice",
			summary_title="Invoice Summary",
			summary=[("Invoice", "SINV-001"), ("Customer", "Demo Customer")],
			bullets=["Current invoice status is Unpaid."],
			item_columns=["Item Code", "Qty"],
			item_rows=[["ITEM-001", "2"]],
			document_row={"document_name": "SINV-001", "status": "Unpaid"},
			item_section_rows=[{"item_code": "ITEM-001", "qty": 2}],
			metrics={"grand_total": 2500, "item_count": 1},
		)
		rendered = outcome.get("rendered") or {}
		artifact = outcome.get("artifact") or {}
		self.assertEqual(rendered.get("source_reports"), ["Sales Invoice"])
		self.assertEqual((artifact.get("sections") or {}).get("document_rows"), [{"document_name": "SINV-001", "status": "Unpaid"}])
		self.assertEqual((artifact.get("sections") or {}).get("item_rows"), [{"item_code": "ITEM-001", "qty": 2}])
		self.assertEqual((artifact.get("dimensions") or {}).get("entity_type"), "sales_invoice")
		self.assertEqual((artifact.get("metrics") or {}).get("grand_total"), 2500)

	def test_profile_entity_detail_response_builder_preserves_profile_sections(self):
		outcome = entity_detail_module._profile_entity_detail_response(
			detail_company="Enterprise Co",
			entity_type="item",
			entity_key="ITEM-001",
			entity_label="Demo Item",
			profile_title="Item Profile",
			summary=[("Item Code", "ITEM-001"), ("Brand", "Baseus")],
			bullets=["Current on-hand stock is 25 units."],
			source_reports=["Item", "Bin"],
			metrics={"total_amount": 1500, "warehouse_count": 2},
			primary_metric_key="total_amount",
			primary_metric_label="Total Sales Amount",
			source_grain="item_detail",
			extra_blocks=[entity_detail_module._data_block("Stock by Warehouse", ["Warehouse", "Qty"], [["Main", "20"]])],
			extra_sections={"stock_rows": [{"warehouse": "Main", "balance_qty": 20}]},
		)
		rendered = outcome.get("rendered") or {}
		artifact = outcome.get("artifact") or {}
		self.assertEqual(rendered.get("title"), "Demo Item Details")
		self.assertEqual((artifact.get("sections") or {}).get("summary"), [{"label": "Item Code", "value": "ITEM-001"}, {"label": "Brand", "value": "Baseus"}])
		self.assertEqual((artifact.get("sections") or {}).get("stock_rows"), [{"warehouse": "Main", "balance_qty": 20}])
		self.assertEqual((artifact.get("dimensions") or {}).get("source_grain"), "item_detail")
		self.assertEqual((artifact.get("metrics") or {}).get("warehouse_count"), 2)

	def test_prefix_entity_detail_answer_adds_entity_label_when_missing(self):
		answer = entity_detail_module._prefix_entity_detail_answer(
			"Demo Item",
			"Current on-hand stock is 25 units.",
		)
		self.assertIn("Here are the details for Demo Item.", answer)
		self.assertIn("Current on-hand stock is 25 units.", answer)

	def test_prefix_entity_detail_answer_repairs_unbalanced_markdown_emphasis(self):
		answer = entity_detail_module._prefix_entity_detail_answer(
			"Type-C Cable 2m Fast Charge",
			"Sold for a total of 170,000 MMK, with most recent sale on 2025-08-18**.",
		)
		self.assertNotIn("**", answer)
		self.assertIn("2025-08-18.", answer)

	def test_resolve_entity_detail_answer_falls_back_to_rendered_for_unsafe_narrative(self):
		with patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={"ok": True, "answer_text": "unsafe purchase receipt statement"},
		), patch.object(
			entity_detail_module,
			"build_artifact_narrative_contract",
			return_value=types.SimpleNamespace(
				to_payload=lambda: {
					"answer_text": "Planned vs. actual receipt date matched and physical receipt completed."
				}
			),
		):
			answer_text, narrative_payload, narrative_contract_payload = entity_detail_module._resolve_entity_detail_answer(
				request_id="purchase-order-answer",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="when was it received?",
				entity_type="purchase_order",
				preferred_answer_text="",
				artifact_payload={"sections": {}, "dimensions": {"entity_type": "purchase_order"}},
				rendered_payload={
					"title": "Purchase Order PUR-ORD-0001",
					"blocks": [
						entity_detail_module._summary_block("Order Summary", [("Purchase Order", "PUR-ORD-0001")])
					],
				},
				response_policy={},
			)
		self.assertIn("### Order Summary", answer_text)
		self.assertEqual(narrative_payload, {})
		self.assertEqual(narrative_contract_payload, {})

	def test_execute_entity_drilldown_rejects_unapproved_runtime_policy(self):
		with patch.object(entity_detail_module, "entity_detail_runtime_policy", return_value={}):
			with self.assertRaises(Exception):
				entity_detail_module.execute_entity_drilldown(
					request_id="unsupported-detail",
					session_id="session-1",
					user_id="user-1",
					site_name="site-1",
					message="tell me more",
					entity_reference={"entity_type": "customer", "entity_key": "CUST-0001"},
					response_policy={},
					grounded_turn={},
				)

	def test_entity_detail_request_support_clarifies_customer_tenure_basis_when_missing(self):
		payload = entity_detail_request_support_module.resolve_entity_detail_request_interpretation(
			entity_type="customer",
			requested_metrics=["tenure"],
			requested_dimensions=[],
			requested_concepts=[],
			artifact_payload={},
		)
		self.assertEqual(payload.get("entity_question_type"), "customer_tenure")
		self.assertTrue(payload.get("clarification_required"))
		self.assertEqual(payload.get("clarification_reason_type"), "customer_tenure_basis_missing")
		self.assertEqual(len(payload.get("clarification_options") or []), 3)

	def test_entity_detail_request_support_identifies_item_stock_position(self):
		payload = entity_detail_request_support_module.resolve_entity_detail_request_interpretation(
			entity_type="item",
			requested_metrics=["quantity"],
			requested_dimensions=["warehouse"],
			requested_concepts=["inventory"],
			artifact_payload={"sections": {"stock_rows": [{"warehouse": "Main", "balance_qty": 20}]}},
		)
		self.assertEqual(payload.get("entity_question_type"), "item_stock_position")
		self.assertEqual(payload.get("requested_metrics"), ["balance_qty"])
		self.assertEqual(payload.get("question_shape"), "dimension_lookup")

	def test_item_stock_direct_evidence_response_is_deterministic_and_skips_narrative_runtime(self):
		artifact_payload = {
			"request_id": "item-stock-direct-1",
			"family_id": "entity_detail",
			"source_reports": ["Item", "Bin"],
			"dimensions": {
				"entity_type": "item",
				"entity_key": "ACC-CBL-UGR-TC2M",
				"entity_label": "Type-C Cable 2m Fast Charge",
			},
			"metrics": {
				"balance_qty": 88,
				"balance_value": 704000,
				"warehouse_count": 2,
			},
			"sections": {
				"summary": [{"label": "UOM", "value": "Nos"}],
				"stock_rows": [
					{"warehouse": "Mandalay Warehouse - MMOB", "balance_qty": 53, "balance_value": 424000},
					{"warehouse": "Yangon Showroom Counter - MMOB", "balance_qty": 35, "balance_value": 280000},
				],
			},
		}
		with patch.object(
			evidence_response_support_module,
			"narrate_governed_artifact",
			side_effect=AssertionError("item stock direct evidence must not call narrative runtime"),
		):
			payload = evidence_response_support_module.grounded_artifact_direct_evidence_response(
				request_id="item-stock-direct-1",
				session_id="session-1",
				interaction_contract=types.SimpleNamespace(user_id="Administrator", site_name="erpai_prj1"),
				response_policy_contract=types.SimpleNamespace(to_runtime_payload=lambda: {}),
				raw_message="how many stocks do we have for that product, and in which warehouse?",
				artifact_payload=artifact_payload,
				grounded_turn={},
			)

		self.assertIn("88", payload.get("answer_text") or "")
		self.assertIn("warehouses", payload.get("answer_text") or "")
		rendered = payload.get("rendered_response_payload") or {}
		self.assertEqual(rendered.get("title"), "Stock Position for Type-C Cable 2m Fast Charge")
		self.assertEqual(rendered.get("answer_text"), payload.get("answer_text"))
		self.assertEqual((payload.get("narrative_payload") or {}), {})
		self.assertEqual((payload.get("narrative_contract_payload") or {}), {})
		blocks = rendered.get("blocks") or []
		self.assertTrue(any(str(block.get("title") or "").strip() == "Stock by Warehouse" for block in blocks))

	def test_entity_dimension_support_maps_master_data_dimensions(self):
		self.assertEqual(entity_dimension_support_module.entity_type_from_dimension("customer"), "customer")
		self.assertEqual(entity_dimension_support_module.entity_type_from_dimension("supplier"), "supplier")
		self.assertEqual(entity_dimension_support_module.entity_type_from_dimension("item name"), "item")

	def test_entity_dimension_support_optionally_maps_document_dimension(self):
		self.assertEqual(entity_dimension_support_module.entity_type_from_dimension("document name"), "")
		self.assertEqual(
			entity_dimension_support_module.entity_type_from_dimension("document name", include_documents=True),
			"sales_invoice",
		)

	def test_artifact_reference_support_extracts_master_data_and_transaction_party_fields(self):
		self.assertEqual(
			artifact_reference_support_module.transaction_party_label(
				{"party_name": "Ko Nay Lin Mobile Center"}
			),
			"Ko Nay Lin Mobile Center",
		)
		self.assertEqual(
			artifact_reference_support_module.ranked_entity_key_label(
				{"entity_name": "Type-C Cable 1m Fast Charge", "entity_code": "ACC-CBL-BAS-TC1M"}
			),
			("ACC-CBL-BAS-TC1M", "Type-C Cable 1m Fast Charge"),
		)
		self.assertEqual(
			artifact_reference_support_module.master_data_entity_key_label(
				{"customer_code": "CUST-001", "customer_name": "Chan Aye Mobile Trading Hub"}
			),
			("CUST-001", "Chan Aye Mobile Trading Hub"),
		)

	def test_customer_detail_enriches_credit_status_from_receivable_summary(self):
		master = {
			"name": "CUST-0001",
			"customer_name": "Zegyo Mobile Supply House",
			"customer_group": "Wholesale",
			"territory": "Yangon",
			"default_price_list": "Wholesale Selling - MMOB",
			"payment_terms": "15 Days - MMOB",
			"mobile_no": "",
			"email_id": "",
			"disabled": 0,
			"is_frozen": 0,
		}
		report_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"output_obj": {
						"result": {
							"data": [
								{
									"party": "Zegyo Mobile Supply House",
									"outstanding": 500000,
									"total_due": 450000,
									"future_amount": 0,
									"range1": 50000,
									"range2": 100000,
									"range3": 50000,
									"range4": 0,
									"range5": 250000,
									"currency": "MMK",
								}
							]
						}
					},
				}
			]
		}
		with patch.object(entity_detail_module.frappe.db, "get_value", return_value=master), patch.object(
			entity_detail_module.frappe,
			"get_all",
			return_value=[
				{
					"company": "Enterprise Co",
					"credit_limit": 10000000,
					"bypass_credit_limit_check": 0,
				}
			],
		), patch.object(
			entity_detail_module,
			"_aggregate_invoice_stats",
			return_value={"invoice_count": 0, "total_amount": 0, "outstanding_amount": 0, "latest_date": ""},
		), patch.object(entity_detail_module, "_recent_invoices", return_value=[]), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support.execute_governed_report",
			return_value=report_payload,
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_rows",
			return_value=report_payload["tool_trace"][0]["output_obj"]["result"]["data"],
		):
			detail = entity_detail_module._customer_or_supplier_detail(
				"customer",
				"Zegyo Mobile Supply House",
				company="Enterprise Co",
			)
		rendered = detail.get("rendered") or {}
		blocks = list(rendered.get("blocks") or [])
		credit_block = next(
			(block for block in blocks if str(block.get("title") or "").startswith("Credit Status")),
			{},
		)
		self.assertTrue(credit_block)
		self.assertTrue(any(row[0] == "Outstanding (MMK)" for row in credit_block.get("rows") or []))
		artifact = detail.get("artifact") or {}
		self.assertIn("Accounts Receivable Summary", artifact.get("source_reports") or [])
		self.assertIn("Customer Credit Limit", artifact.get("source_reports") or [])
		self.assertIn("outstanding_total", artifact.get("metrics") or {})
		self.assertEqual((artifact.get("metrics") or {}).get("credit_limit"), 10000000)
		buckets = (artifact.get("sections") or {}).get("credit_buckets") or []
		self.assertEqual(len(buckets), 6)
		policy_rows = (artifact.get("sections") or {}).get("credit_policy") or []
		self.assertTrue(any(row.get("label") == "Payment Terms" and row.get("value") == "15 Days - MMOB" for row in policy_rows))
		self.assertTrue(any(row.get("label") == "Credit Limit (MMK)" and row.get("value") == "10,000,000" for row in policy_rows))
		policy_block = next(
			(block for block in blocks if str(block.get("title") or "").strip() == "Commercial Policy"),
			{},
		)
		self.assertTrue(policy_block)
		highlight_block = next(
			(block for block in blocks if str(block.get("block_type") or "") == "bullet_list"),
			{},
		)
		self.assertFalse(bool(highlight_block))
	def test_detect_entity_drilldown_request_resolves_explicit_sales_invoice_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Sales Invoice" and name == "ACC-SINV-2026-00194",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about ACC-SINV-2026-00194",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "sales_invoice")
		self.assertEqual(outcome["entity_key"], "ACC-SINV-2026-00194")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_resolves_explicit_delivery_note_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Delivery Note" and name == "MAT-DN-2026-00016",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about MAT-DN-2026-00016",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "delivery_note")
		self.assertEqual(outcome["entity_key"], "MAT-DN-2026-00016")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_resolves_explicit_sales_order_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Sales Order" and name == "SAL-ORD-2026-00022",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about SAL-ORD-2026-00022",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "sales_order")
		self.assertEqual(outcome["entity_key"], "SAL-ORD-2026-00022")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_resolves_explicit_customer_name(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name=None: doctype == "Customer" and name == "Zegyo Mobile Supply House",
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value="Zegyo Mobile Supply House",
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Zegyo Mobile Supply House",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Zegyo Mobile Supply House")
		self.assertEqual(outcome["source"], "explicit_name")

	def test_detect_entity_drilldown_request_accepts_tell_me_details_phrase(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name=None: doctype == "Customer" and name == "Ko Nay Lin Mobile Center",
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value="Ko Nay Lin Mobile Center",
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me details about Ko Nay Lin Mobile Center",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "explicit_name")

	def test_detect_entity_drilldown_request_resolves_partial_customer_name_via_governed_scope(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			return_value=False,
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value=None,
		), patch.object(
			entity_detail_module,
			"resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_key": "Ko Nay Lin Mobile Center",
					"entity_label": "Ko Nay Lin Mobile Center",
					"resolution_source": "governed_fuzzy",
				},
				"reason": "The request matched one governed entity confidently through approved fuzzy resolution.",
			},
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me details about Ko Nay Lin Mobile",
				artifact_payload=None,
				grounded_turn=None,
		)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "governed_fuzzy")

	def test_detect_entity_drilldown_request_resolves_supplier_name_via_active_profile_policy(self):
		with patch.object(
			entity_detail_module,
				"list_active_entity_detail_scope_activations",
			return_value=[
				{
					"entity_grain": "customer",
					"doctype": "Customer",
					"identity_field": "name",
					"display_field": "customer_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
				{
					"entity_grain": "supplier",
					"doctype": "Supplier",
					"identity_field": "name",
					"display_field": "supplier_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
			],
		), patch.object(
			entity_detail_module.frappe.db,
			"exists",
			return_value=False,
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value=None,
		), patch.object(
			entity_detail_module,
			"resolve_entity_reference_from_message",
			side_effect=[
				{"resolution_status": "not_found", "resolved_entity": {}},
				{
					"resolution_status": "resolved",
					"resolved_entity": {
						"entity_key": "Myanmar Tech Import Services",
						"entity_label": "Myanmar Tech Import Services",
						"resolution_source": "governed_fuzzy",
					},
				},
			],
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Myanmar Tech Import",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "supplier")
		self.assertEqual(outcome["entity_key"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["source"], "governed_fuzzy")

	def test_detect_entity_drilldown_request_uses_shared_profile_target_slot_normalization(self):
		with patch.object(
			entity_detail_module,
				"list_active_entity_detail_scope_activations",
			return_value=[
				{
					"entity_grain": "customer",
					"doctype": "Customer",
					"identity_field": "name",
					"display_field": "customer_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
				{
					"entity_grain": "supplier",
					"doctype": "Supplier",
					"identity_field": "name",
					"display_field": "supplier_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
			],
		), patch.object(
			entity_detail_module,
			"normalize_master_data_lookup_slots",
			side_effect=lambda message, entity_grain, preferred_slots=None: (
				{"lookup_mode": "profile_target", "lookup_search_text": "Myanmar Tech Import"}
				if entity_grain == "supplier"
				else {}
			),
		), patch.object(
			entity_detail_module.frappe.db,
			"exists",
			return_value=False,
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value=None,
		), patch.object(
			entity_detail_module,
			"resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_key": "Myanmar Tech Import Services",
					"entity_label": "Myanmar Tech Import Services",
					"resolution_source": "governed_fuzzy",
				},
			},
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="anything at all",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "supplier")
		self.assertEqual(outcome["entity_key"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["source"], "governed_fuzzy")

	def test_detect_entity_drilldown_request_item_fallback_uses_shared_profile_target_slot_normalization(self):
		with patch.object(
			entity_detail_module,
				"list_active_entity_detail_scope_activations",
			return_value=[
				{
					"entity_grain": "customer",
					"doctype": "Customer",
					"identity_field": "name",
					"display_field": "customer_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
				{
					"entity_grain": "supplier",
					"doctype": "Supplier",
					"identity_field": "name",
					"display_field": "supplier_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
			],
		), patch.object(
			entity_detail_module,
			"normalize_master_data_lookup_slots",
			return_value={"lookup_mode": "profile_target", "lookup_search_text": "Demo Item"},
		), patch.object(
			entity_detail_module.frappe.db,
			"exists",
			return_value=False,
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value=None,
		), patch.object(
			entity_detail_module,
			"resolve_entity_reference_from_message",
			return_value={"resolution_status": "not_found", "resolved_entity": {}},
		), patch.object(
			entity_detail_module,
			"_resolve_item_name",
			return_value=("ITEM-001", "Demo Item"),
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="something unrelated",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "item")
		self.assertEqual(outcome["entity_key"], "ITEM-001")
		self.assertEqual(outcome["source"], "explicit_name")

	def test_detect_entity_drilldown_request_uses_policy_order_for_exact_profile_targets(self):
		with patch.object(
			entity_detail_module,
				"list_active_entity_detail_scope_activations",
			return_value=[
				{
					"entity_grain": "supplier",
					"doctype": "Supplier",
					"identity_field": "name",
					"display_field": "supplier_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
				{
					"entity_grain": "customer",
					"doctype": "Customer",
					"identity_field": "name",
					"display_field": "customer_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
			],
		), patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name=None: doctype == "Supplier" and name == "Myanmar Tech Import Services",
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			side_effect=lambda doctype, filters=None, fieldname=None, as_dict=False: "Myanmar Tech Import Services",
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Myanmar Tech Import Services",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "supplier")
		self.assertEqual(outcome["entity_key"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["source"], "explicit_name")

	def test_detect_entity_drilldown_request_keeps_item_as_bounded_explicit_fallback(self):
		with patch.object(
			entity_detail_module,
				"list_active_entity_detail_scope_activations",
			return_value=[
				{
					"entity_grain": "customer",
					"doctype": "Customer",
					"identity_field": "name",
					"display_field": "customer_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
				{
					"entity_grain": "supplier",
					"doctype": "Supplier",
					"identity_field": "name",
					"display_field": "supplier_name",
					"allowed_lookup_modes": ["profile_target"],
					"activation_state": "active",
				},
			],
		), patch.object(
			entity_detail_module.frappe.db,
			"exists",
			return_value=False,
		), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			return_value=None,
		), patch.object(
			entity_detail_module,
			"resolve_entity_reference_from_message",
			return_value={"resolution_status": "not_found", "resolved_entity": {}},
		), patch.object(
			entity_detail_module,
			"_resolve_item_name",
			return_value=("ITEM-001", "Demo Item"),
		):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Demo Item",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "item")
		self.assertEqual(outcome["entity_key"], "ITEM-001")
		self.assertEqual(outcome["source"], "explicit_name")

	def test_customer_detail_narrative_blocks_explanatory_credit_balance_language(self):
		self.assertFalse(
			entity_detail_module._entity_detail_narrative_is_safe(
				"customer",
				"Current outstanding balance is –249,000 MMK, reflecting net credit (i.e., overpayment).",
			)
		)
		self.assertFalse(
			entity_detail_module._entity_detail_narrative_is_safe(
				"customer",
				"Zegyo Mobile Supply House is a wholesale customer based in Mandalay.",
			)
		)

	def test_detect_entity_drilldown_request_resolves_explicit_purchase_order_identifier(self):
		with patch.object(
			entity_detail_module.frappe.db,
			"exists",
			side_effect=lambda doctype, name: doctype == "Purchase Order" and name == "PUR-ORD-2026-00008",
		), patch.object(entity_detail_module, "_resolve_item_name", return_value=("", "")):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about PUR-ORD-2026-00008",
				artifact_payload=None,
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "purchase_order")
		self.assertEqual(outcome["entity_key"], "PUR-ORD-2026-00008")
		self.assertEqual(outcome["source"], "explicit_identifier")

	def test_detect_entity_drilldown_request_uses_transaction_listing_delivery_note_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about MAT-DN-2026-00016",
				artifact_payload={
					"family_id": "transaction_listing",
					"dimensions": {"document_entity_type": "delivery_note"},
					"sections": {"transaction_rows": [{"document_name": "MAT-DN-2026-00016"}]},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "delivery_note")
		self.assertEqual(outcome["entity_key"], "MAT-DN-2026-00016")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_customer_master_artifact_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Ko Nay Lin Mobile Center",
				artifact_payload={
					"family_id": "customer_master_list",
					"sections": {
						"customer_rows": [
							{
								"customer_code": "Ko Nay Lin Mobile Center",
								"customer_name": "Ko Nay Lin Mobile Center",
							}
						]
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_master_data_directory_customer_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Ko Nay Lin Mobile Center",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "customer"},
					"sections": {
						"directory_rows": [
							{
								"entity_code": "Ko Nay Lin Mobile Center",
								"entity_name": "Ko Nay Lin Mobile Center",
							}
						]
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_deictic_customer_master_resolution(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that customer",
				artifact_payload={
					"family_id": "customer_master_list",
					"sections": {
						"entity_reference_resolution": {
							"resolution_status": "resolved",
							"resolved_entity": {
								"entity_key": "Ko Nay Lin Mobile Center",
								"entity_label": "Ko Nay Lin Mobile Center",
							},
						}
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_deictic_entity_detail_customer_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that customer",
				artifact_payload={
					"family_id": "entity_detail",
					"dimensions": {
						"entity_type": "customer",
						"entity_key": "Ko Nay Lin Mobile Center",
						"entity_label": "Ko Nay Lin Mobile Center",
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "customer")
		self.assertEqual(outcome["entity_key"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_deictic_supplier_master_resolution(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that supplier",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "supplier"},
					"sections": {
						"entity_reference_resolution": {
							"resolution_status": "resolved",
							"resolved_entity": {
								"entity_key": "Myanmar Tech Import Services",
								"entity_label": "Myanmar Tech Import Services",
							},
						}
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "supplier")
		self.assertEqual(outcome["entity_key"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["entity_label"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_master_data_directory_item_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about Demo Item",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "item"},
					"sections": {
						"directory_rows": [
							{
								"entity_code": "ITEM-001",
								"entity_name": "Demo Item",
							}
						]
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "item")
		self.assertEqual(outcome["entity_key"], "ITEM-001")
		self.assertEqual(outcome["entity_label"], "Demo Item")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_deictic_item_master_resolution(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that item",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "item"},
					"sections": {
						"entity_reference_resolution": {
							"resolution_status": "resolved",
							"resolved_entity": {
								"entity_key": "ITEM-001",
								"entity_label": "Demo Item",
							},
						}
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "item")
		self.assertEqual(outcome["entity_key"], "ITEM-001")
		self.assertEqual(outcome["entity_label"], "Demo Item")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_request_uses_deictic_product_alias_from_item_context(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that product",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "item"},
					"sections": {
						"entity_reference_resolution": {
							"resolution_status": "resolved",
							"resolved_entity": {
								"entity_key": "ITEM-001",
								"entity_label": "Demo Item",
							},
						}
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "item")
		self.assertEqual(outcome["entity_key"], "ITEM-001")
		self.assertEqual(outcome["entity_label"], "Demo Item")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_uses_generic_deictic_when_master_data_context_has_one_entity(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that one",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "supplier"},
					"sections": {
						"entity_reference_resolution": {
							"resolution_status": "resolved",
							"resolved_entity": {
								"entity_key": "Myanmar Tech Import Services",
								"entity_label": "Myanmar Tech Import Services",
							},
						}
					},
				},
				grounded_turn=None,
			)
		self.assertEqual(outcome["entity_type"], "supplier")
		self.assertEqual(outcome["entity_key"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["entity_label"], "Myanmar Tech Import Services")
		self.assertEqual(outcome["source"], "artifact_context")

	def test_detect_entity_drilldown_does_not_guess_from_generic_deictic_when_multiple_entities_exist(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that one",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "customer"},
					"sections": {
						"directory_rows": [
							{
								"entity_code": "Ko Nay Lin Mobile Center",
								"entity_name": "Ko Nay Lin Mobile Center",
							},
							{
								"entity_code": "Zegyo Mobile Supply House",
								"entity_name": "Zegyo Mobile Supply House",
							},
						]
					},
				},
				grounded_turn=None,
			)
		self.assertIsNone(outcome)

	def test_detect_entity_drilldown_does_not_guess_from_deictic_product_when_multiple_items_exist(self):
		with patch.object(entity_detail_module.frappe.db, "exists", return_value=False):
			outcome = entity_detail_module.detect_entity_drilldown_request(
				message="tell me more about that product",
				artifact_payload={
					"family_id": "master_data_directory",
					"dimensions": {"entity_type": "item"},
					"sections": {
						"directory_rows": [
							{
								"entity_code": "ITEM-001",
								"entity_name": "Demo Item",
							},
							{
								"entity_code": "ITEM-002",
								"entity_name": "Second Demo Item",
							},
						]
					},
				},
				grounded_turn=None,
			)
		self.assertIsNone(outcome)

	def test_execute_entity_drilldown_supports_delivery_note(self):
		fake_doc = _FakeDoc(
			name="MAT-DN-2026-00016",
			posting_date="2026-03-30",
			customer="Thaketa Mobile Exchange",
			status="Return",
			return_against="MAT-DN-2026-00014",
			total_qty=-2,
			grand_total=-36000,
			delivery_trip="",
			company="Mingalar Mobile Distribution Co., Ltd.",
			is_return=1,
			per_billed=0,
			items=[
				types.SimpleNamespace(
					item_code="ACC-CHR-XMI-33W",
					item_name="Xiaomi Fast Charger 33W",
					qty=-2,
					amount=-36000,
					net_amount=-36000,
					against_sales_order="SAL-ORD-2026-00025",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "MAT-DN-2026-00016 is a return delivery note.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="delivery-note-detail",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about MAT-DN-2026-00016",
				entity_reference={"entity_type": "delivery_note", "entity_key": "MAT-DN-2026-00016"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		self.assertIn("MAT-DN-2026-00016", outcome["answer_text"])
		artifact = outcome["artifact_payload"]
		self.assertEqual(artifact["dimensions"]["entity_type"], "delivery_note")
		self.assertEqual(artifact["sections"]["document_rows"][0]["return_against"], "MAT-DN-2026-00014")
		self.assertEqual(artifact["sections"]["item_rows"][0]["against_sales_order"], "SAL-ORD-2026-00025")
		self.assertEqual(outcome["rendered_response_payload"]["source_reports"], ["Delivery Note"])
		grounded = outcome["grounded_turn_payload"]
		self.assertEqual(grounded["known_entities"][0]["entity_type"], "delivery_note")
		self.assertIn("MAT-DN-2026-00016", grounded["known_documents"])

	def test_execute_entity_drilldown_supports_sales_order(self):
		fake_doc = _FakeDoc(
			name="SAL-ORD-2026-00022",
			transaction_date="2026-03-30",
			delivery_date="2026-04-02",
			customer="Zegyo Mobile Supply House",
			status="To Deliver and Bill",
			delivery_status="Partly Delivered",
			billing_status="Partly Billed",
			total_qty=2,
			grand_total=7600000,
			per_delivered=50,
			per_billed=10.460526,
			company="Mingalar Mobile Distribution Co., Ltd.",
			items=[
				types.SimpleNamespace(
					item_code="SPH-OPP-A58-6/128",
					item_name="OPPO A58 (6GB 128GB)",
					qty=2,
					delivered_qty=1,
					billed_amt=795000,
					amount=7600000,
					net_amount=7600000,
					delivery_date="2026-04-02",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "SAL-ORD-2026-00022 is a sales order for Zegyo Mobile Supply House.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="sales-order-detail",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about SAL-ORD-2026-00022",
				entity_reference={"entity_type": "sales_order", "entity_key": "SAL-ORD-2026-00022"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		self.assertIn("SAL-ORD-2026-00022", outcome["answer_text"])
		artifact = outcome["artifact_payload"]
		self.assertEqual(artifact["dimensions"]["entity_type"], "sales_order")
		self.assertEqual(artifact["sections"]["document_rows"][0]["delivery_date"], "2026-04-02")
		self.assertEqual(artifact["sections"]["document_rows"][0]["per_delivered"], 50.0)
		self.assertEqual(artifact["sections"]["item_rows"][0]["delivered_qty"], 1.0)
		self.assertEqual(artifact["sections"]["item_rows"][0]["billed_amount"], 795000.0)
		self.assertEqual(outcome["rendered_response_payload"]["source_reports"], ["Sales Order"])
		grounded = outcome["grounded_turn_payload"]
		self.assertEqual(grounded["known_entities"][0]["entity_type"], "sales_order")
		self.assertIn("SAL-ORD-2026-00022", grounded["known_documents"])

	def test_execute_entity_drilldown_supports_purchase_order(self):
		fake_doc = _FakeDoc(
			name="PUR-ORD-2026-00008",
			transaction_date="2026-01-30",
			schedule_date="2026-02-03",
			supplier="Sunflower Accessories Co.",
			status="To Bill",
			total_qty=1008,
			grand_total=28150000,
			per_received=100,
			per_billed=0,
			company="Mingalar Mobile Distribution Co., Ltd.",
			items=[
				types.SimpleNamespace(
					item_code="SPH-SAM-A15-6/128",
					item_name="Samsung Galaxy A15 (6GB 128GB)",
					qty=8,
					received_qty=8,
					billed_amt=0,
					amount=7000000,
					net_amount=7000000,
					schedule_date="2026-02-03",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "PUR-ORD-2026-00008 is a purchase order for Sunflower Accessories Co.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="purchase-order-detail",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about PUR-ORD-2026-00008",
				entity_reference={"entity_type": "purchase_order", "entity_key": "PUR-ORD-2026-00008"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		self.assertIn("PUR-ORD-2026-00008", outcome["answer_text"])
		artifact = outcome["artifact_payload"]
		self.assertEqual(artifact["dimensions"]["entity_type"], "purchase_order")
		self.assertEqual(artifact["sections"]["document_rows"][0]["schedule_date"], "2026-02-03")
		self.assertEqual(artifact["sections"]["document_rows"][0]["receipt_status"], "Fully Received")
		self.assertEqual(artifact["sections"]["document_rows"][0]["billing_status"], "Not Billed")
		self.assertEqual(artifact["sections"]["item_rows"][0]["received_qty"], 8.0)
		self.assertEqual(artifact["sections"]["item_rows"][0]["billed_amount"], 0.0)
		self.assertEqual(outcome["rendered_response_payload"]["source_reports"], ["Purchase Order"])
		self.assertEqual(outcome["narrative_payload"], {})
		self.assertEqual(outcome["narrative_contract_payload"], {})
		grounded = outcome["grounded_turn_payload"]
		self.assertEqual(grounded["known_entities"][0]["entity_type"], "purchase_order")
		self.assertIn("PUR-ORD-2026-00008", grounded["known_documents"])

	def test_execute_entity_drilldown_suppresses_unsafe_purchase_order_actual_receipt_narrative(self):
		fake_doc = _FakeDoc(
			name="PUR-ORD-2026-00003",
			transaction_date="2026-01-10",
			schedule_date="2026-01-15",
			supplier="Sunflower Accessories Co.",
			status="To Bill",
			total_qty=1008,
			grand_total=37000000,
			per_received=100,
			per_billed=0,
			company="Mingalar Mobile Distribution Co., Ltd.",
			items=[
				types.SimpleNamespace(
					item_code="ACC-PWB-BAS-20K",
					item_name="Power Bank 20000mAh",
					qty=200,
					received_qty=200,
					billed_amt=0,
					amount=16400000,
					net_amount=16400000,
					schedule_date="2026-01-15",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": (
					"PUR-ORD-2026-00003 is fully received. Planned vs. Actual Receipt Date: "
					"Aligned (2026-01-15), with completed physical receipt (100% received as of 2026-01-15). "
					"The supplier invoice is pending and accounts payable remains outstanding."
				),
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="purchase-order-unsafe-narrative",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="give me details about PUR-ORD-2026-00003",
				entity_reference={"entity_type": "purchase_order", "entity_key": "PUR-ORD-2026-00003"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		self.assertNotIn("planned vs. actual receipt", outcome["answer_text"].lower())
		self.assertNotIn("deadline met", outcome["answer_text"].lower())
		self.assertNotIn("physical receipt", outcome["answer_text"].lower())
		self.assertNotIn("supplier invoice", outcome["answer_text"].lower())
		self.assertNotIn("accounts payable", outcome["answer_text"].lower())
		self.assertIn("PUR-ORD-2026-00003 is a purchase order", outcome["answer_text"])
		self.assertIn("### Order Summary", outcome["answer_text"])
		self.assertEqual(outcome["narrative_payload"], {})
		self.assertEqual(outcome["narrative_contract_payload"], {})

	def test_execute_entity_drilldown_populates_sales_invoice_delivery_proof(self):
		fake_doc = _FakeDoc(
			name="ACC-SINV-2026-00194",
			posting_date="2026-03-30",
			customer="Zegyo Mobile Supply House",
			status="Partly Paid",
			due_date="2026-04-07",
			grand_total=795000,
			outstanding_amount=495000,
			company="Mingalar Mobile Distribution Co., Ltd.",
			is_return=0,
			update_stock=0,
			items=[
				types.SimpleNamespace(
					item_code="SPH-OPP-A58-6/128",
					item_name="OPPO A58 (6GB 128GB)",
					qty=1,
					amount=795000,
					net_amount=795000,
					delivery_note="MAT-DN-2026-00011",
					dn_detail="a9uhijifia",
					sales_order="SAL-ORD-2026-00022",
				)
			],
		)
		with patch.object(entity_detail_module.frappe, "get_doc", return_value=fake_doc), patch.object(
			entity_detail_module.frappe.db,
			"get_value",
			side_effect=lambda doctype, name, fields, as_dict=False: {
				"name": "MAT-DN-2026-00011",
				"docstatus": 1,
				"status": "Completed",
				"posting_date": "2026-03-30",
				"is_return": 0,
				"return_against": "",
			}
			if doctype == "Delivery Note" and name == "MAT-DN-2026-00011"
			else None,
		), patch.object(
			entity_detail_module,
			"narrate_governed_artifact",
			return_value={
				"ok": True,
				"answer_text": "ACC-SINV-2026-00194 has governed delivery proof.",
				"agent_meta": {"engine": "artifact_narrative"},
			},
		):
			outcome = entity_detail_module.execute_entity_drilldown(
				request_id="sales-invoice-proof",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="tell me more about ACC-SINV-2026-00194",
				entity_reference={"entity_type": "sales_invoice", "entity_key": "ACC-SINV-2026-00194"},
				response_policy={},
				grounded_turn={"company": "Mingalar Mobile Distribution Co., Ltd."},
			)
		self.assertTrue(outcome["ok"])
		artifact = outcome["artifact_payload"]
		delivery_proof = artifact["sections"]["delivery_proof"][0]
		self.assertEqual(delivery_proof["proof_state"], "direct_delivery_proven_via_linked_delivery_note")
		self.assertEqual(delivery_proof["submitted_delivery_notes"], ["MAT-DN-2026-00011"])
		self.assertEqual(delivery_proof["submitted_delivery_dates"], ["2026-03-30"])
		self.assertEqual(delivery_proof["sales_orders"], ["SAL-ORD-2026-00022"])
		self.assertEqual(artifact["sections"]["item_rows"][0]["delivery_note"], "MAT-DN-2026-00011")

	def test_grounded_artifact_direct_evidence_answer_confirms_supported_invoice_delivery_proof(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="items from this invoice are already delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertIn("has already been delivered", answer)
		self.assertIn("Zegyo Mobile Supply House", answer)
		self.assertIn("OPPO A58", answer)
		self.assertIn("MAT-DN-2026-00011", answer)
		self.assertNotIn("direct governed proof", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_returns_delivery_date_when_requested(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what it was delivered",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House", "posting_date": "2026-03-30"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
							"submitted_delivery_dates": ["2026-03-30"],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertIn("2026-03-30", answer)
		self.assertIn("MAT-DN-2026-00011", answer)

	def test_build_grounded_artifact_direct_evidence_rendered_payload_includes_relevant_delivery_context(self):
		rendered = boundary_support_module.build_grounded_artifact_direct_evidence_rendered_payload(
			raw_message="that item is already delivered to the customer?",
			artifact_payload={
				"family_id": "entity_detail",
				"request_id": "delivery-proof-render",
				"source_reports": ["Sales Invoice"],
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00194"},
				"sections": {
					"document_rows": [{"customer": "Zegyo Mobile Supply House"}],
					"item_rows": [{"item_name": "OPPO A58 (6GB 128GB)", "qty": 1}],
					"delivery_proof": [
						{
							"proof_state": "direct_delivery_proven_via_linked_delivery_note",
							"proof_method": "linked_delivery_note",
							"submitted_delivery_notes": ["MAT-DN-2026-00011"],
							"submitted_delivery_dates": ["2026-03-30"],
							"sales_orders": ["SAL-ORD-2026-00022"],
							"delivery_notes": [
								{
									"delivery_note": "MAT-DN-2026-00011",
									"docstatus": 1,
									"status": "Completed",
									"posting_date": "2026-03-30",
									"is_return": 0,
									"return_against": "",
								}
							],
						}
					],
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00194 Detail"},
		)
		self.assertEqual(rendered["renderer_id"], "grounded_artifact_direct_evidence")
		self.assertIn("Delivery Note", rendered["source_reports"])
		blocks = rendered["blocks"]
		self.assertTrue(any(block.get("title") == "Delivery Evidence" for block in blocks))
		self.assertTrue(any(block.get("title") == "Linked Delivery Notes" for block in blocks))
		summary_rows = next(block for block in blocks if block.get("title") == "Delivery Evidence")["rows"]
		self.assertIn(["Recorded Delivery Date", "2026-03-30"], summary_rows)
		self.assertIn(["Linked Delivery Notes", "MAT-DN-2026-00011"], summary_rows)
		self.assertIn(["Linked Sales Orders", "SAL-ORD-2026-00022"], summary_rows)

	def test_grounded_artifact_direct_evidence_answer_stays_empty_without_direct_proof(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="items from this invoice are already delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_invoice", "entity_label": "ACC-SINV-2026-00192"},
				"sections": {
					"delivery_proof": [
						{
							"proof_state": "insufficient_governed_delivery_evidence",
							"submitted_delivery_notes": [],
						}
					]
				},
			},
			grounded_turn={"source_name": "ACC-SINV-2026-00192 Detail"},
		)
		self.assertEqual(answer, "")

	def test_grounded_artifact_direct_evidence_answer_confirms_sales_order_delivery_progress(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="is it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
				"sections": {
					"document_rows": [
						{
							"customer": "Zegyo Mobile Supply House",
							"status": "To Deliver and Bill",
							"delivery_status": "Partly Delivered",
							"billing_status": "Partly Billed",
							"delivery_date": "2026-04-02",
							"quantity": 2,
							"per_delivered": 50,
							"per_billed": 10.460526,
						}
					],
					"item_rows": [
						{
							"item_name": "OPPO A58 (6GB 128GB)",
							"qty": 2,
							"delivered_qty": 1,
							"billed_amount": 795000,
						}
					],
				},
			},
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
		)
		self.assertIn("Partly.", answer)
		self.assertIn("50%", answer)
		self.assertIn("1 of 2 units", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_sales_order_billing_progress(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="how much is billed?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
				"sections": {
					"document_rows": [
						{
							"customer": "Zegyo Mobile Supply House",
							"status": "To Deliver and Bill",
							"delivery_status": "Partly Delivered",
							"billing_status": "Partly Billed",
							"delivery_date": "2026-04-02",
							"quantity": 2,
							"per_delivered": 50,
							"per_billed": 10.460526,
						}
					],
					"item_rows": [
						{
							"qty": 2,
							"delivered_qty": 1,
							"billed_amount": 795000,
						}
					],
				},
			},
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
		)
		self.assertIn("10.46%", answer)
		self.assertIn("795,000 MMK", answer)
		self.assertIn("Partly Billed", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_sales_order_planned_delivery_date(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="when is delivery due?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
				"sections": {
					"document_rows": [
						{
							"customer": "Zegyo Mobile Supply House",
							"status": "To Deliver and Bill",
							"delivery_status": "Partly Delivered",
							"billing_status": "Partly Billed",
							"delivery_date": "2026-04-02",
							"quantity": 2,
							"per_delivered": 50,
							"per_billed": 10.460526,
						}
					],
					"item_rows": [],
				},
			},
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
		)
		self.assertIn("2026-04-02", answer)
		self.assertIn("planned delivery date", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_uses_typed_sales_order_contract_without_raw_phrase(self):
		artifact_payload = {
			"family_id": "entity_detail",
			"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
			"sections": {
				"document_rows": [
					{
						"customer": "Zegyo Mobile Supply House",
						"status": "To Deliver and Bill",
						"delivery_status": "Partly Delivered",
						"billing_status": "Partly Billed",
						"delivery_date": "2026-04-02",
						"quantity": 2,
						"per_delivered": 50,
						"per_billed": 10.460526,
					}
				],
				"item_rows": [
					{
						"item_name": "OPPO A58 (6GB 128GB)",
						"qty": 2,
						"delivered_qty": 1,
						"billed_amount": 795000,
					}
				],
			},
		}
		evidence_request_contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="typed-sales-order-progress",
			raw_message="is it delivered?",
			artifact_payload=artifact_payload,
		).to_payload()
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="please continue with the same governed detail",
			artifact_payload=artifact_payload,
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
			evidence_request_contract=evidence_request_contract,
		)
		self.assertIn("Partly.", answer)
		self.assertIn("50%", answer)
		self.assertIn("1 of 2 units", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_overdue_status(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="is this customer overdue?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {"overdue_total": 450000, "outstanding_total": 600000},
				"sections": {"credit_buckets": [{"bucket": "31-60", "amount": 450000}]},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("Yes", answer)
		self.assertIn("450,000", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_credit_balance(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="does this customer have a credit balance?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Thaketa Mobile Exchange"},
				"metrics": {"outstanding_total": -249000},
				"sections": {"credit_buckets": [{"bucket": "0-30", "amount": -249000}]},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("Yes", answer)
		self.assertIn("249,000", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_highest_bucket(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="which aging bucket is highest?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {"outstanding_total": 600000},
				"sections": {
					"credit_buckets": [
						{"bucket": "0-30", "amount": 100000},
						{"bucket": "31-60", "amount": 200000},
						{"bucket": "61-90", "amount": 300000},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("61-90", answer)
		self.assertIn("300,000", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_overdue_ratio(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what is this customer's overdue ratio?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Bayint Naung Wholesale Mobile"},
				"metrics": {
					"outstanding_total": 12000000,
					"overdue_total": 10000000,
					"overdue_ratio": 0.8333333333333334,
				},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Enterprise Co"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("83.3%", answer)
		self.assertIn("10,000,000", answer)
		self.assertIn("12,000,000", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_credit_limit_status(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="has this customer exceeded credit limit?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {
					"outstanding_total": 495000,
					"credit_limit": 10000000,
					"credit_limit_available": 9505000,
					"credit_limit_excess": 0,
					"credit_limit_configured": True,
					"credit_limit_exceeded": False,
				},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Enterprise Co"},
						{"label": "Payment Terms", "value": "15 Days - MMOB"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("No.", answer)
		self.assertIn("10,000,000", answer)
		self.assertIn("9,505,000", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_customer_payment_terms(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what are this customer's payment terms?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Enterprise Co"},
						{"label": "Payment Terms", "value": "15 Days - MMOB"},
						{"label": "Default Price List", "value": "Wholesale Selling - MMOB"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("15 Days - MMOB", answer)
		self.assertIn("payment terms", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_returns_customer_default_price_list(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what is this customer's default price list?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Enterprise Co"},
						{"label": "Default Price List", "value": "Wholesale Selling - MMOB"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("Wholesale Selling - MMOB", answer)
		self.assertIn("default price list", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_returns_customer_created_tenure(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what is this customer's tenure by customer created date?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {"customer_created_tenure_days": 11},
				"sections": {
					"lifecycle": [
						{"label": "Customer Created Date", "value": "2026-03-30"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("11 days", answer.lower())
		self.assertIn("2026-03-30", answer)

	def test_grounded_artifact_direct_evidence_answer_clarifies_generic_customer_tenure_basis(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what is this customer's tenure?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {
					"customer_created_tenure_days": 11,
					"first_sales_order_tenure_days": 11,
					"first_sales_invoice_tenure_days": 11,
				},
				"sections": {
					"lifecycle": [
						{"label": "Customer Created Date", "value": "2026-03-30"},
						{"label": "First Sales Order Date", "value": "2026-03-30"},
						{"label": "First Sales Invoice Date", "value": "2026-03-30"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("three date bases", answer.lower())
		self.assertIn("customer created date", answer.lower())
		self.assertIn("first submitted sales order date", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_returns_first_sales_invoice_date(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="when was the first sales invoice for this customer?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Zegyo Mobile Supply House"},
				"metrics": {"first_sales_invoice_tenure_days": 11},
				"sections": {
					"lifecycle": [
						{"label": "First Sales Invoice Date", "value": "2026-03-30"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("2026-03-30", answer)
		self.assertIn("first observed submitted sales invoice", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_clarifies_customer_operational_document_missing(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "customer", "entity_label": "Ko Nay Lin Mobile Center"},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Enterprise Co"},
					]
				},
			},
			grounded_turn={"source_name": "Customer Detail"},
		)
		self.assertIn("exact sales document or date basis", answer.lower())
		self.assertIn("first sales order date", answer.lower())
		self.assertIn("specific sales order or sales invoice", answer.lower())

	def test_grounded_artifact_evidence_boundary_answer_blocks_actual_sales_order_delivery_event_date(self):
		answer = boundary_support_module.grounded_artifact_evidence_boundary_answer(
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
				"sections": {
					"document_rows": [
						{
							"customer": "Zegyo Mobile Supply House",
							"status": "To Deliver and Bill",
							"delivery_status": "Partly Delivered",
							"billing_status": "Partly Billed",
							"delivery_date": "2026-04-02",
							"quantity": 2,
							"per_delivered": 50,
							"per_billed": 10.460526,
						}
					],
					"item_rows": [],
				},
			},
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
		)
		self.assertIn("does not prove the actual shipment event date", answer)
		self.assertIn("delivery-note", answer.lower())

	def test_grounded_artifact_evidence_boundary_answer_uses_typed_sales_order_contract_without_raw_phrase(self):
		artifact_payload = {
			"family_id": "entity_detail",
			"dimensions": {"entity_type": "sales_order", "entity_label": "SAL-ORD-2026-00022"},
			"sections": {
				"document_rows": [
					{
						"customer": "Zegyo Mobile Supply House",
						"status": "To Deliver and Bill",
						"delivery_status": "Partly Delivered",
						"billing_status": "Partly Billed",
						"delivery_date": "2026-04-02",
						"quantity": 2,
						"per_delivered": 50,
						"per_billed": 10.460526,
					}
				],
				"item_rows": [],
			},
		}
		evidence_request_contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="typed-sales-order-boundary",
			raw_message="when was it delivered?",
			artifact_payload=artifact_payload,
		).to_payload()
		answer = boundary_support_module.grounded_artifact_evidence_boundary_answer(
			raw_message="keep the same order context",
			artifact_payload=artifact_payload,
			grounded_turn={"source_name": "SAL-ORD-2026-00022 Detail"},
			evidence_request_contract=evidence_request_contract,
		)
		self.assertIn("does not prove the actual shipment event date", answer)
		self.assertIn("delivery-note", answer.lower())

	def test_grounded_artifact_direct_evidence_answer_confirms_purchase_order_receipt_progress(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="is it received?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "purchase_order", "entity_label": "PUR-ORD-2026-00004"},
				"sections": {
					"document_rows": [
						{
							"supplier": "Shwe Taung Electronics Supply",
							"status": "To Receive and Bill",
							"receipt_status": "Partly Received",
							"billing_status": "Not Billed",
							"schedule_date": "2026-01-20",
							"quantity": 1008,
							"per_received": 79.96,
							"per_billed": 0,
						}
					],
					"item_rows": [
						{
							"item_name": "OPPO A58 (6GB 128GB)",
							"qty": 8,
							"received_qty": 6,
							"billed_amount": 0,
						},
						{
							"item_name": "Redmi TWS Earbuds",
							"qty": 200,
							"received_qty": 160,
							"billed_amount": 0,
						},
					],
				},
			},
			grounded_turn={"source_name": "PUR-ORD-2026-00004 Detail"},
		)
		self.assertIn("Partly.", answer)
		self.assertIn("79.96%", answer)
		self.assertIn("166 of 1,008 units", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_purchase_order_receipt_status(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="what is the receipt status?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "purchase_order", "entity_label": "PUR-ORD-2026-00004"},
				"sections": {
					"document_rows": [
						{
							"supplier": "Shwe Taung Electronics Supply",
							"status": "To Receive and Bill",
							"receipt_status": "Partly Received",
							"billing_status": "Not Billed",
							"schedule_date": "2026-01-20",
							"quantity": 1008,
							"per_received": 79.96,
							"per_billed": 0,
						}
					],
					"item_rows": [
						{
							"qty": 8,
							"received_qty": 6,
							"billed_amount": 0,
						}
					],
				},
			},
			grounded_turn={"source_name": "PUR-ORD-2026-00004 Detail"},
		)
		self.assertIn("Partly.", answer)
		self.assertIn("Partly Received", answer)
		self.assertIn("79.96%", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_purchase_order_billing_progress(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="how much is billed?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "purchase_order", "entity_label": "PUR-ORD-2026-00006"},
				"sections": {
					"document_rows": [
						{
							"supplier": "Golden Dragon Trading Co. Ltd.",
							"status": "To Bill",
							"receipt_status": "Fully Received",
							"billing_status": "Not Billed",
							"schedule_date": "2026-01-29",
							"quantity": 532,
							"per_received": 100,
							"per_billed": 0,
						}
					],
					"item_rows": [
						{
							"qty": 8,
							"received_qty": 8,
							"billed_amount": 0,
						}
					],
				},
			},
			grounded_turn={"source_name": "PUR-ORD-2026-00006 Detail"},
		)
		self.assertIn("not been billed yet", answer.lower())
		self.assertIn("0%", answer)
		self.assertIn("Not Billed", answer)

	def test_grounded_artifact_direct_evidence_answer_returns_purchase_order_planned_receipt_date(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="when is receipt due?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "purchase_order", "entity_label": "PUR-ORD-2026-00006"},
				"sections": {
					"document_rows": [
						{
							"supplier": "Golden Dragon Trading Co. Ltd.",
							"status": "To Bill",
							"receipt_status": "Fully Received",
							"billing_status": "Not Billed",
							"schedule_date": "2026-01-29",
							"quantity": 532,
							"per_received": 100,
							"per_billed": 0,
						}
					],
					"item_rows": [],
				},
			},
			grounded_turn={"source_name": "PUR-ORD-2026-00006 Detail"},
		)
		self.assertIn("2026-01-29", answer)
		self.assertIn("planned receipt date", answer.lower())

	def test_grounded_artifact_evidence_boundary_answer_blocks_actual_purchase_order_receipt_event_date(self):
		answer = boundary_support_module.grounded_artifact_evidence_boundary_answer(
			raw_message="when was it received?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {"entity_type": "purchase_order", "entity_label": "PUR-ORD-2026-00004"},
				"sections": {
					"document_rows": [
						{
							"supplier": "Shwe Taung Electronics Supply",
							"status": "To Receive and Bill",
							"receipt_status": "Partly Received",
							"billing_status": "Not Billed",
							"schedule_date": "2026-01-20",
							"quantity": 1008,
							"per_received": 79.96,
							"per_billed": 0,
						}
					],
					"item_rows": [],
				},
			},
			grounded_turn={"source_name": "PUR-ORD-2026-00004 Detail"},
		)
		self.assertIn("does not prove the actual receipt event date", answer)
		self.assertIn("purchase-receipt", answer.lower())

	def test_sales_order_contract_resolves_actual_delivery_event_date(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-sales-order-actual-event",
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "sales_order",
					"entity_label": "SAL-ORD-2026-00022",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "sales_order_actual_delivery_event_date")
		self.assertEqual(contract.question_shape, "date_lookup")
		self.assertEqual(contract.value_mode, "actual_value")

	def test_purchase_order_contract_resolves_actual_receipt_event_date(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-purchase-order-actual-event",
			raw_message="when was it received?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "purchase_order",
					"entity_label": "PUR-ORD-2026-00004",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "purchase_order_actual_receipt_event_date")
		self.assertEqual(contract.question_shape, "date_lookup")
		self.assertEqual(contract.value_mode, "actual_value")

	def test_purchase_order_contract_resolves_receipt_status_as_receipt_progress(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-purchase-order-receipt-status",
			raw_message="what is the receipt status?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "purchase_order",
					"entity_label": "PUR-ORD-2026-00004",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "purchase_order_receipt_progress")
		self.assertEqual(contract.question_shape, "boolean_status")
		self.assertEqual(contract.value_mode, "current_value")

	def test_sales_order_contract_resolves_delivery_status_as_delivery_progress(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-sales-order-delivery-status",
			raw_message="what is the delivery status?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "sales_order",
					"entity_label": "SAL-ORD-2026-00022",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "sales_order_delivery_progress")
		self.assertEqual(contract.question_shape, "boolean_status")
		self.assertEqual(contract.value_mode, "current_value")

	def test_purchase_order_contract_resolves_billing_status_as_billing_progress(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-purchase-order-billing-status",
			raw_message="what is the billing status?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "purchase_order",
					"entity_label": "PUR-ORD-2026-00004",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "purchase_order_billing_progress")
		self.assertEqual(contract.question_shape, "scalar_ratio")
		self.assertEqual(contract.value_mode, "current_value")

	def test_sales_invoice_contract_resolves_delivery_evidence_question_type(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-sales-invoice-delivery",
			raw_message="is this invoice delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "sales_invoice",
					"entity_label": "ACC-SINV-2026-00194",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "sales_invoice_delivery_evidence")
		self.assertEqual(contract.question_shape, "boolean_status")
		self.assertEqual(contract.value_mode, "current_value")

	def test_e4_3_document_event_date_support_is_shared_typed_basis(self):
		specs = document_event_basis_specs()
		question_types = {
			str(item.get("entity_question_type") or "").strip()
			for item in specs
		}
		self.assertEqual(
			question_types,
			{
				"sales_order_actual_delivery_event_date",
				"sales_order_planned_delivery_date",
				"sales_order_billing_progress",
				"sales_order_delivery_progress",
				"sales_order_document_status",
				"purchase_order_actual_receipt_event_date",
				"purchase_order_planned_receipt_date",
				"purchase_order_billing_progress",
				"purchase_order_receipt_progress",
				"purchase_order_document_status",
				"sales_invoice_delivery_event_date",
				"sales_invoice_delivery_evidence",
			},
		)
		self.assertEqual(
			document_event_question_type_shape_map(),
			{
				"sales_order_actual_delivery_event_date": ("date_lookup", "actual_value"),
				"sales_order_planned_delivery_date": ("date_lookup", "planned_value"),
				"sales_order_billing_progress": ("scalar_ratio", "current_value"),
				"sales_order_delivery_progress": ("boolean_status", "current_value"),
				"sales_order_document_status": ("dimension_lookup", "current_value"),
				"purchase_order_actual_receipt_event_date": ("date_lookup", "actual_value"),
				"purchase_order_planned_receipt_date": ("date_lookup", "planned_value"),
				"purchase_order_billing_progress": ("scalar_ratio", "current_value"),
				"purchase_order_receipt_progress": ("boolean_status", "current_value"),
				"purchase_order_document_status": ("dimension_lookup", "current_value"),
				"sales_invoice_delivery_event_date": ("date_lookup", "actual_value"),
				"sales_invoice_delivery_evidence": ("boolean_status", "current_value"),
			},
		)
		by_question_type = {
			str(item.get("entity_question_type") or "").strip(): item
			for item in specs
		}
		self.assertEqual(
			by_question_type["sales_invoice_delivery_event_date"].get("required_concepts_all"),
			["fulfillment"],
		)
		self.assertEqual(
			by_question_type["sales_invoice_delivery_evidence"].get("required_concepts_all"),
			["fulfillment"],
		)

	def test_customer_operational_document_contract_requires_clarification(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-customer-operational-doc-missing",
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
		)
		self.assertTrue(contract.clarification_required)
		self.assertEqual(contract.clarification_reason_type, "customer_operational_document_missing")
		self.assertIn("First Sales Order Date", contract.clarification_options)

	def test_customer_operational_document_clarification_signal_uses_artifact_boundary_continuations(self):
		signal = contracts_module.build_entity_detail_clarification_signal_contract(
			request_id="entity-detail-customer-operational-doc-signal",
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
		)
		self.assertIsNotNone(signal)
		signal_payload = signal.to_payload()
		self.assertEqual(signal_payload.get("reason_type"), "customer_operational_document_missing")
		self.assertEqual(signal_payload.get("stage"), "artifact_boundary")
		internal_details = signal_payload.get("internal_details") or {}
		self.assertEqual(internal_details.get("continuation_lane"), "artifact_boundary")
		self.assertEqual(
			(internal_details.get("resolved_message_by_option") or {}).get("First Sales Invoice Date"),
			"when was the first sales invoice for this customer?",
		)

	def test_customer_tenure_contract_requires_basis_clarification(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-clarify",
			raw_message="what is this customer's tenure?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
			},
		)
		self.assertEqual(contract.entity_type, "customer")
		self.assertEqual(contract.entity_question_type, "customer_tenure")
		self.assertTrue(contract.clarification_required)
		self.assertEqual(contract.clarification_reason_type, "customer_tenure_basis_missing")
		self.assertEqual(len(contract.clarification_options), 3)

	def test_customer_tenure_contract_resolves_first_sales_order_basis_from_dimension(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-tenure-basis",
			raw_message="what is this customer's tenure by first sales order date?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "customer_tenure")
		self.assertEqual(contract.basis, "first_sales_order_date")
		self.assertFalse(contract.clarification_required)

	def test_customer_lifecycle_contract_resolves_first_sales_invoice_basis(self):
		contract = contracts_module.build_entity_detail_evidence_request_contract(
			request_id="entity-detail-lifecycle",
			raw_message="when was the first sales invoice for this customer?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
			},
		)
		self.assertEqual(contract.entity_question_type, "customer_lifecycle_date")
		self.assertEqual(contract.basis, "first_sales_invoice_date")
		self.assertFalse(contract.clarification_required)

	def test_customer_tenure_clarification_signal_uses_artifact_boundary_continuations(self):
		signal = contracts_module.build_entity_detail_clarification_signal_contract(
			request_id="entity-detail-signal",
			raw_message="what is this customer's tenure?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
			},
		)
		self.assertIsNotNone(signal)
		signal_payload = signal.to_payload()
		self.assertEqual(signal_payload.get("stage"), "artifact_boundary")
		self.assertEqual(signal_payload.get("reason_type"), "customer_tenure_basis_missing")
		internal_details = signal_payload.get("internal_details") or {}
		self.assertEqual(internal_details.get("continuation_lane"), "artifact_boundary")
		self.assertEqual(
			(internal_details.get("resolved_message_by_option") or {}).get("Customer Tenure by First Sales Order"),
			"what is this customer's tenure by first sales order date?",
		)
		self.assertIn("I can calculate customer tenure for Zegyo Mobile Supply House", signal_payload.get("user_question") or "")
		self.assertIn("- Customer Tenure by First Sales Order", signal_payload.get("user_question") or "")

	def test_customer_operational_document_clarification_question_renders_shared_choice_list(self):
		signal = contracts_module.build_entity_detail_clarification_signal_contract(
			request_id="entity-detail-customer-operational-question",
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
		)
		self.assertIsNotNone(signal)
		user_question = (signal.to_payload() or {}).get("user_question") or ""
		self.assertIn("I can help with that for Ko Nay Lin Mobile Center", user_question)
		self.assertIn("Choose one:", user_question)
		self.assertIn("- First Sales Order Date", user_question)

	def test_phase_f_package4_lifecycle_event_ambiguity_is_artifact_boundary_and_typed(self):
		tenure_signal = contracts_module.build_entity_detail_clarification_signal_contract(
			request_id="phase-f-pkg4-tenure-clarification",
			raw_message="what is this customer's tenure?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
			},
		)
		operational_signal = contracts_module.build_entity_detail_clarification_signal_contract(
			request_id="phase-f-pkg4-operational-doc-clarification",
			raw_message="when was it delivered?",
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
		)
		self.assertIsNotNone(tenure_signal)
		self.assertIsNotNone(operational_signal)

		tenure_payload = tenure_signal.to_payload()
		tenure_internal = tenure_payload.get("internal_details") or {}
		self.assertEqual(tenure_payload.get("reason_type"), "customer_tenure_basis_missing")
		self.assertEqual(tenure_payload.get("stage"), "artifact_boundary")
		self.assertEqual(tenure_internal.get("continuation_lane"), "artifact_boundary")
		self.assertEqual(
			set(tenure_payload.get("suggested_options") or []),
			{
				"Customer Tenure by Customer Created Date",
				"Customer Tenure by First Sales Order",
				"Customer Tenure by First Sales Invoice",
			},
		)
		self.assertEqual(
			(tenure_internal.get("resolved_message_by_option") or {}).get("Customer Tenure by First Sales Invoice"),
			"what is this customer's tenure by first sales invoice date?",
		)
		self.assertIn(
			"first sales invoice",
			(tenure_internal.get("option_aliases_by_option") or {}).get("Customer Tenure by First Sales Invoice", []),
		)

		operational_payload = operational_signal.to_payload()
		operational_internal = operational_payload.get("internal_details") or {}
		self.assertEqual(operational_payload.get("reason_type"), "customer_operational_document_missing")
		self.assertEqual(operational_payload.get("stage"), "artifact_boundary")
		self.assertEqual(operational_internal.get("continuation_lane"), "artifact_boundary")
		self.assertEqual(
			set(operational_payload.get("suggested_options") or []),
			{
				"First Sales Order Date",
				"First Sales Invoice Date",
				"Specific Sales Document Detail",
			},
		)
		self.assertEqual(
			(operational_internal.get("resolved_message_by_option") or {}).get("First Sales Order Date"),
			"when was the first sales order for this customer?",
		)
		self.assertIn(
			"specific sales document",
			(operational_internal.get("option_aliases_by_option") or {}).get("Specific Sales Document Detail", []),
		)

		self.assertEqual(customer_lifecycle_supported_focus_grains(), ["customer"])
		self.assertEqual(
			document_event_supported_focus_grains(),
			["sales_order", "purchase_order", "sales_invoice"],
		)
