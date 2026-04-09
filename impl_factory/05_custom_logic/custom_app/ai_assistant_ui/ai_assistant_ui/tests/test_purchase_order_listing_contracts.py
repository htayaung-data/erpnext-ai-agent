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
from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_adapters import _requested_transaction_columns
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.family_validator import validate_normalized_family_artifact
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	SemanticFreshQueryResult,
	compile_from_fresh_query_message,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report
from ai_assistant_ui.qwen_chat.metadata import (
	capability_fresh_query_defaults,
	get_report_spec,
	get_report_surface_evidence_spec,
	load_semantic_resolution_registry,
)
from ai_assistant_ui.qwen_chat.semantic_resolution import resolve_transaction_listing_interpretation


class TestPurchaseOrderListingContracts(unittest.TestCase):
	def test_purchase_order_list_metadata_registers_transaction_listing_baseline(self):
		report_spec = get_report_spec("Purchase Order List")
		self.assertEqual(report_spec.get("grounding_mode"), "direct_query")
		self.assertEqual(
			((report_spec.get("direct_query") or {}).get("doctype")),
			"Purchase Order",
		)
		self.assertEqual(
			((report_spec.get("direct_query") or {}).get("date_field")),
			"transaction_date",
		)
		self.assertEqual(
			((report_spec.get("direct_query") or {}).get("fixed_filters") or {}).get("docstatus"),
			1,
		)
		self.assertIn("company", list(report_spec.get("required_filters") or []))
		self.assertIn("status", list(((report_spec.get("direct_query") or {}).get("filterable_fields")) or []))
		filter_value_aliases = ((report_spec.get("direct_query") or {}).get("filter_value_aliases") or {})
		status_aliases = list(filter_value_aliases.get("status") or [])
		self.assertTrue(status_aliases)
		to_bill_spec = next(
			(
				item
				for item in status_aliases
				if isinstance(item, dict) and str(item.get("value") or "").strip() == "To Bill"
			),
			{},
		)
		self.assertIn("to bill", list(to_bill_spec.get("aliases") or []))
		self.assertIn("transaction_listing", list(report_spec.get("supported_intent_classes") or []))
		defaults = capability_fresh_query_defaults("purchase_order_read", intent_class="transaction_listing")
		self.assertEqual(defaults.get("default_report_name"), "Purchase Order List")
		self.assertEqual(defaults.get("default_metrics"), ["Grand Total", "Quantity"])
		resolution_registry = load_semantic_resolution_registry()
		slot_definitions = list(resolution_registry.get("slot_definitions") or [])
		listing_view = next(
			(
				item
				for item in slot_definitions
				if isinstance(item, dict) and str(item.get("slot_name") or "").strip() == "listing_view"
			),
			{},
		)
		self.assertIn("purchase_order", list(listing_view.get("allowed_values") or []))
		alias_maps = resolution_registry.get("alias_maps") if isinstance(resolution_registry.get("alias_maps"), dict) else {}
		listing_aliases = alias_maps.get("listing_view") if isinstance(alias_maps.get("listing_view"), list) else []
		purchase_order_aliases = next(
			(
				item
				for item in listing_aliases
				if isinstance(item, dict) and str(item.get("canonical_value") or "").strip() == "purchase_order"
			),
			{},
		)
		self.assertIn("purchase orders", list(purchase_order_aliases.get("aliases") or []))
		evidence_spec = get_report_surface_evidence_spec("Purchase Order List")
		self.assertEqual(evidence_spec.get("evidence_class"), "governed_direct_query")

	def test_purchase_order_transaction_listing_resolution_uses_governed_purchase_order_view(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="purchase-order-resolution",
			session_id="purchase-order-resolution-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["purchase_order_read"],
			candidate_reports=["Purchase Order List"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={"listing_view": "purchase_order"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.91,
		)
		outcome = resolve_transaction_listing_interpretation(interpretation)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.contract.resolved_slots.get("listing_view"), "purchase_order")
		self.assertEqual(outcome.interpretation.candidate_capability_ids, ["purchase_order_read"])
		self.assertEqual(outcome.interpretation.candidate_reports, ["Purchase Order List"])
		self.assertEqual(
			outcome.interpretation.requested_dimensions,
			["Purchase Order", "Supplier", "Status"],
		)
		self.assertEqual(
			outcome.interpretation.requested_metrics,
			["Grand Total", "Quantity"],
		)

	def test_compile_purchase_order_last_month_uses_transaction_date_scope(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="purchase-order-last-month",
			session_id="purchase-order-last-month-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["purchase_order_read"],
			candidate_reports=["Purchase Order List"],
			requested_dimensions=["Purchase Order", "Supplier", "Transaction Date"],
			requested_metrics=["Grand Total", "Quantity"],
			requested_time_scope="last_month",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		with patch(
			"ai_assistant_ui.qwen_chat.compiler.defaults_single_company_name",
			return_value="Enterprise Co",
		):
			outcome = compile_fresh_query(
				request_id="purchase-order-last-month",
				session_id="purchase-order-last-month-session",
				interpretation=interpretation,
				response_policy={},
			)
		self.assertEqual(outcome.compiler_contract.capability_id, "purchase_order_read")
		self.assertEqual(outcome.compiler_contract.selected_report, "Purchase Order List")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("from_date"), "2026-03-01")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("to_date"), "2026-03-31")
		self.assertEqual(outcome.compiler_contract.completed_filters.get("company"), "Enterprise Co")

	def test_compile_purchase_order_status_filter_preserves_scalar_status(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="purchase-order-status-filter",
			session_id="purchase-order-status-filter-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["purchase_order_read"],
			candidate_reports=["Purchase Order List"],
			requested_dimensions=["Purchase Order", "Supplier", "Status"],
			requested_metrics=["Grand Total"],
			requested_time_scope="",
			requested_presentation=[],
			extracted_slots={"filters": {"status": "To Bill"}},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)
		outcome = compile_fresh_query(
			request_id="purchase-order-status-filter",
			session_id="purchase-order-status-filter-session",
			interpretation=interpretation,
			response_policy={},
		)
		self.assertEqual(outcome.compiler_contract.completed_filters.get("status"), "To Bill")
		self.assertEqual(
			(outcome.compiled_request_contract.filters if outcome.compiled_request_contract else {}).get("status"),
			"To Bill",
		)

	def test_compile_from_fresh_query_message_clears_as_of_today_for_latest_purchase_orders(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="purchase-order-latest-structural-limit",
			session_id="purchase-order-latest-structural-limit-session",
			intent_class="transaction_listing",
			candidate_capability_ids=["purchase_order_read"],
			candidate_reports=["Purchase Order List"],
			requested_dimensions=["Purchase Order", "Supplier", "Transaction Date"],
			requested_metrics=["Grand Total", "Quantity"],
			requested_time_scope="as_of_today",
			requested_presentation=[],
			extracted_slots={
				"report_date": "2026-04-08",
				"from_date": "2026-04-08",
				"to_date": "2026-04-08",
				"filters": {
					"report_date": "2026-04-08",
					"from_date": "2026-04-08",
					"to_date": "2026-04-08",
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
				session_id="purchase-order-latest-structural-limit-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me latest 5 purchase orders",
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

	def test_compile_from_fresh_query_message_grounds_purchase_order_status_alias(self):
		pipeline = compile_from_fresh_query_message(
			session_id="purchase-order-status-alias-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show me purchase orders to bill",
			recent_messages=[],
		)
		self.assertEqual(
			str(
				(
					((pipeline.get("fresh_query_interpretation") or {}).get("interpretation") or {}).get("extracted_slots")
					or {}
				).get("filters", {}).get("status")
				or ""
			),
			"To Bill",
		)
		self.assertEqual(
			str(((pipeline.get("compiled_query_request") or {}).get("filters") or {}).get("status") or ""),
			"To Bill",
		)
		self.assertEqual(
			_requested_transaction_columns(pipeline.get("fresh_query_compiler") or {}),
			["party_name", "grand_total", "quantity", "status"],
		)

	def test_transaction_listing_adapter_accepts_purchase_orders_with_supplier(self):
		compiler_contract = {
			"request_id": "purchase-order-adapter",
			"capability_id": "purchase_order_read",
			"selected_report": "Purchase Order List",
			"requested_dimensions": ["Purchase Order", "Supplier", "Transaction Date", "Status"],
			"requested_metrics": ["Grand Total", "Quantity"],
			"requested_time_scope": "",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Purchase Order List",
						"filters": {
							"company": "Enterprise Co",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"name": "PUR-ORD-2026-00008",
									"transaction_date": "2026-01-30",
									"supplier": "Sunflower Accessories Co.",
									"grand_total": 28150000,
									"total_qty": 1008,
									"status": "To Bill",
									"docstatus": 1,
								}
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="purchase-order-adapter",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="transaction_listing",
			preferred_family_id="transaction_listing",
		)
		self.assertEqual(outcome.status, "adapted")
		artifact = outcome.artifact_contract
		self.assertIsNotNone(artifact)
		transaction_rows = ((artifact.sections or {}).get("transaction_rows") or [])
		self.assertEqual(transaction_rows[0].get("posting_date"), "2026-01-30")
		self.assertEqual(transaction_rows[0].get("party_name"), "Sunflower Accessories Co.")
		self.assertEqual(artifact.metrics.get("quantity"), 1008.0)
		validation = validate_normalized_family_artifact(
			request_id="purchase-order-adapter",
			compiler_contract=compiler_contract,
			artifact_contract=artifact,
			family_id="transaction_listing",
			adapter_errors=outcome.errors,
			adapter_warnings=outcome.warnings,
		)
		self.assertIsNotNone(validation)
		self.assertEqual(validation.status, "pass")
		rendered = render_normalized_family_response(
			request_id="purchase-order-adapter",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		document_block = next(
			(
				block
				for block in blocks
				if isinstance(block, dict) and str(block.get("title") or "").strip() == "Documents"
			),
			{},
		)
		columns = list(document_block.get("columns") or [])
		self.assertIn("Transaction Date", columns)
		self.assertIn("Supplier", columns)
		self.assertIn("Status", columns)

	def test_direct_query_execution_labels_purchase_order_columns_and_filters(self):
		report_spec = {
			"grounding_mode": "direct_query",
			"direct_query": {
				"doctype": "Purchase Order",
				"fields": ["name", "transaction_date", "supplier", "grand_total", "total_qty", "status", "company"],
				"fixed_filters": {"docstatus": 1},
				"date_field": "transaction_date",
				"default_limit": 5,
			},
			"required_filters": ["company"],
			"defaultable_filters": [{"fieldname": "company", "strategy": "single_company_invariant"}],
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.get_report_spec",
			return_value=report_spec,
		), patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.frappe.get_all",
			return_value=[
				{
					"name": "PUR-ORD-2026-00008",
					"transaction_date": "2026-01-30",
					"supplier": "Sunflower Accessories Co.",
					"grand_total": 28150000,
					"total_qty": 1008,
					"status": "To Bill",
					"company": "Enterprise Co",
				}
			],
		) as mocked_get_all:
			payload = execute_governed_report(
				report_name="Purchase Order List",
				filters={
					"company": "Enterprise Co",
					"from_date": "2026-01-01",
					"to_date": "2026-01-31",
					"status": "To Bill",
				},
				user="Administrator",
			)
		self.assertTrue(payload.get("ok"))
		detail = ((payload.get("tool_trace") or [{}])[0].get("output_obj") or {}).get("result") or {}
		columns = detail.get("columns") or []
		self.assertEqual(columns[0].get("label"), "Purchase Order")
		self.assertEqual(columns[1].get("label"), "Transaction Date")
		self.assertEqual(columns[2].get("label"), "Supplier")
		self.assertEqual(columns[4].get("label"), "Quantity")
		self.assertEqual(
			mocked_get_all.call_args.kwargs.get("filters"),
			{
				"docstatus": 1,
				"company": "Enterprise Co",
				"transaction_date": ["between", ["2026-01-01", "2026-01-31"]],
				"status": "To Bill",
			},
		)


if __name__ == "__main__":
	unittest.main()
