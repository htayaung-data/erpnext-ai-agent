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
if not hasattr(sys.modules.get("frappe"), "get_all"):
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	_assemble_entity_period_commercial_rows,
	_build_followup_ready_grounded_turn_context,
	governed_composite_frontdoor_candidate_available,
	maybe_build_governed_composite_frontdoor_response,
)


class TestGovernedCompositeRuntimeExecution(unittest.TestCase):
	def test_followup_ready_grounded_turn_context_normalizes_product_dimension_to_item_entity(self):
		payload = _build_followup_ready_grounded_turn_context(
			request_id="e13-product-owned-1",
			raw_message="show top products by revenue",
			resolved_company_name="Mingalar Mobile Distribution Co., Ltd.",
			family_resolution=types.SimpleNamespace(
				requested_period_start="2026-04-01",
				requested_period_end="2026-04-30",
				requested_basis="sales_invoice",
			),
			normalized_family_artifact_payload={
				"dimensions": {"entity_dimension": "Product"},
				"sections": {
					"ranked_rows": [
						{"entity": "Type-C Cable 1m Fast Charge", "entity_code": "ACC-CBL-BAS-TC1M"}
					]
				},
			},
			source_reports=["Gross Profit"],
		)
		self.assertEqual((payload.get("known_entities") or [])[0]["entity_type"], "item")
		self.assertEqual((payload.get("known_entities") or [])[0]["code"], "ACC-CBL-BAS-TC1M")

	def test_customer_revenue_defaults_to_sales_invoice_basis(self):
		assembled_rows = [
			{
				"rank": 1,
				"customer": "Capital Telecom (NPT)",
				"customer_name": "Capital Telecom (NPT)",
				"metric_values": {
					"revenue": {"value": 18080000.0, "display_value": "18,080,000 MMK"},
					"quantity": {"value": 154.0, "display_value": "154 units"},
					"average_invoice_value": {"value": 18080000.0, "display_value": "18,080,000 MMK"},
				},
				"primary_metric_id": "revenue",
				"row_provenance": [],
				"join_key": {"customer": "Capital Telecom (NPT)"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_sales_invoice_revenue_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-2-default-sales-invoice-basis",
				message="show top 5 customers by revenue last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"resolved_family",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("requested_basis")),
			"sales_invoice",
		)
		self.assertEqual(
			((response.get("composite_artifact") or {}).get("composite_id")),
			"customer_commercial_ranking_sales_invoice_composite",
		)
		self.assertEqual(response.get("clarification_signal_payload") or {}, {})
		self.assertIn("sales invoices", response.get("frontdoor_answer") or "")
		self.assertIn("| Rank | Customer | Revenue |", response.get("frontdoor_answer") or "")

	def test_product_revenue_defaults_to_sales_invoice_basis(self):
		assembled_rows = [
			{
				"rank": 1,
				"item": "Type-C Cable 1m Fast Charge",
				"item_name": "Type-C Cable 1m Fast Charge",
				"item_code": "ACC-CBL-BAS-TC1M",
				"metric_values": {
					"revenue": {"value": 22533500.04, "display_value": "22,533,500.04 MMK"},
					"quantity": {"value": 2971.0, "display_value": "2,971 units"},
					"average_selling_price": {"value": 7584.0, "display_value": "7,584 MMK"},
				},
				"primary_metric_id": "revenue",
				"row_provenance": [],
				"join_key": {"item_code": "ACC-CBL-BAS-TC1M"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "product_sales_invoice_revenue_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-3-default-sales-invoice-basis",
				message="show top 10 products by revenue last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"resolved_family",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("requested_basis")),
			"sales_invoice",
		)
		self.assertEqual(
			((response.get("composite_artifact") or {}).get("composite_id")),
			"product_commercial_ranking_sales_invoice_composite",
		)
		self.assertEqual(response.get("clarification_signal_payload") or {}, {})
		self.assertIn("sales invoices", response.get("frontdoor_answer") or "")
		self.assertIn("| Rank | Product | Revenue |", response.get("frontdoor_answer") or "")

	@unittest.skip("Customer-risk recommendation language is owned by the NBU/evidence-boundary path, not direct composite frontdoor.")
	def test_customer_risk_collection_priority_language_resolves_to_customer_risk_family(self):
		self.assertTrue(
			governed_composite_frontdoor_candidate_available(
				message="who should we collect from first?",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		)
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_risk_as_of_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(
				[
					{
						"rank": 1,
						"customer": "35th Street Mobile Wholesale",
						"customer_name": "35th Street Mobile Wholesale",
						"metric_values": {
							"overdue_amount": {"value": 60212000.0, "display_value": "60,212,000 MMK"},
							"outstanding_amount": {"value": 86837000.0, "display_value": "86,837,000 MMK"},
						},
						"primary_metric_id": "overdue_amount",
						"row_provenance": [],
						"join_key": {"customer": "35th Street Mobile Wholesale"},
					}
				],
				"",
			),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="collection-priority-customer-risk",
				message="who should we collect from first?",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(((response.get("family_resolution") or {}).get("requested_family_id")), "customer_risk_as_of")
		self.assertEqual(((response.get("family_resolution") or {}).get("requested_primary_metric")), "overdue_amount")
		self.assertIn("35th Street Mobile Wholesale", response.get("frontdoor_answer") or "")

	def test_customer_commercial_family_clarifies_missing_primary_metric(self):
		response = maybe_build_governed_composite_frontdoor_response(
			request_id="phase3-2-clarify-primary",
			message="show top customers for sales orders last month",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"clarify_family_variation",
		)
		self.assertIn("Revenue", response.get("frontdoor_answer") or "")
		self.assertIn("Quantity", response.get("frontdoor_answer") or "")
		aliases = (
			((response.get("clarification_signal_payload") or {}).get("internal_details") or {})
			.get("option_aliases_by_option", {})
			.get("Revenue", [])
		)
		self.assertIn("rev", aliases)
		internal_details = ((response.get("clarification_signal_payload") or {}).get("internal_details") or {})
		self.assertEqual(internal_details.get("semantic_slot_name"), "requested_primary_metric")
		self.assertEqual(
			(internal_details.get("semantic_slot_value_by_option") or {}).get("Revenue"),
			"revenue",
		)
		self.assertEqual(
			(internal_details.get("carryover_slot_values") or {}).get("requested_basis"),
			"sales_order",
		)
		self.assertEqual(
			(internal_details.get("carryover_slot_values") or {}).get("selected_time_scope"),
			"last_month",
		)

	def test_customer_commercial_family_builds_active_composite_answer(self):
		assembled_rows = [
			{
				"rank": 1,
				"customer": "Zegyo Mobile Supply House",
				"customer_name": "Zegyo Mobile Supply House",
				"metric_values": {
					"revenue": {"value": 9340000.0, "display_value": "9,340,000 MMK"},
					"quantity": {"value": 30.0, "display_value": "30 units"},
					"average_order_value": {"value": 3113333.33, "display_value": "3,113,333.33 MMK"},
				},
				"primary_metric_id": "revenue",
				"row_provenance": [],
				"join_key": {"customer": "Zegyo Mobile Supply House"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_sales_order_revenue_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-2-active",
				message="show top 5 customers by revenue for sales orders last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"resolved_family",
		)
		self.assertEqual(
			getattr(response.get("frontdoor_contract"), "intent_class", ""),
			"governed_composite_value",
		)
		self.assertEqual(
			((response.get("composite_artifact") or {}).get("composite_id")),
			"customer_commercial_ranking_sales_order_composite",
		)
		self.assertEqual(
			((response.get("normalized_family_artifact") or {}).get("family_id")),
			"ranking_analytics",
		)
		self.assertEqual(
			((response.get("grounded_turn_context") or {}).get("artifact_family_id")),
			"ranking_analytics",
		)
		alias_map = (
			((response.get("normalized_family_artifact") or {}).get("dimensions") or {})
			.get("requested_column_alias_map", {})
		)
		self.assertEqual(alias_map.get("sales amount"), "revenue")
		self.assertEqual(alias_map.get("sale amount"), "revenue")
		self.assertEqual(
			str((response.get("runtime_trace_payload") or {}).get("type") or "").strip(),
			"qwen_runtime_trace",
		)
		self.assertIn(
			"there was only 1 customer with sales orders in that period, so here it is ranked by revenue.",
			response.get("frontdoor_answer") or "",
		)
		self.assertIn("Zegyo Mobile Supply House", response.get("frontdoor_answer") or "")
		self.assertIn("| Rank | Customer | Revenue |", response.get("frontdoor_answer") or "")

	def test_customer_commercial_family_resolves_quantity_directly(self):
		assembled_rows = [
			{
				"rank": 1,
				"customer": "Hledan Mobile Trade Center",
				"customer_name": "Hledan Mobile Trade Center",
				"metric_values": {
					"quantity": {"value": 40.0, "display_value": "40 units"},
					"revenue": {"value": 3000000.0, "display_value": "3,000,000 MMK"},
					"average_invoice_value": {"value": 750000.0, "display_value": "750,000 MMK"},
				},
				"primary_metric_id": "quantity",
				"row_provenance": [],
				"join_key": {"customer": "Hledan Mobile Trade Center"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_sales_invoice_quantity_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-2-quantity-direct",
				message="show top 5 customers by quantity for sales invoices last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"resolved_family",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("requested_primary_metric")),
			"quantity",
		)
		self.assertIn("sales invoices", response.get("frontdoor_answer") or "")
		self.assertIn("| Rank | Customer | Quantity |", response.get("frontdoor_answer") or "")

	def test_customer_commercial_family_explains_when_fewer_rows_exist_than_requested(self):
		assembled_rows = [
			{
				"rank": index,
				"customer": f"Customer {index}",
				"customer_name": f"Customer {index}",
				"metric_values": {
					"revenue": {"value": float(1000 * index), "display_value": f"{1000 * index:,.0f} MMK"},
					"quantity": {"value": float(index), "display_value": f"{index} units"},
					"average_order_value": {"value": float(1000 * index), "display_value": f"{1000 * index:,.0f} MMK"},
				},
				"primary_metric_id": "revenue",
				"row_provenance": [],
				"join_key": {"customer": f"Customer {index}"},
			}
			for index in range(1, 7)
		]
		component_artifacts = {
			"revenue": types.SimpleNamespace(
				rows=[
					{"customer": "Customer 1", "document_count": 1},
					{"customer": "Customer 2", "document_count": 1},
					{"customer": "Customer 3", "document_count": 3},
					{"customer": "Customer 4", "document_count": 3},
					{"customer": "Customer 5", "document_count": 1},
					{"customer": "Customer 6", "document_count": 2},
				]
			)
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=(component_artifacts, [{"execution_id": "customer_sales_order_revenue_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-2-top-seven-last-year",
				message="show top 7 customers by revenue for sales orders last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		answer = response.get("frontdoor_answer") or ""
		self.assertIn(
			"there were 11 submitted sales orders from 6 customers in that period, so here they are ranked by revenue.",
			answer,
		)
		self.assertNotIn("matched the governed scope", answer)

	@unittest.skip("Customer-risk fresh-query ownership is exercised through the NBU/report path in the current architecture.")
	def test_customer_risk_family_uses_metadata_default_primary_and_as_of_date(self):
		assembled_rows = [
			{
				"rank": 1,
				"customer": "Ko Nay Lin Mobile Center",
				"customer_name": "Ko Nay Lin Mobile Center",
				"metric_values": {
					"overdue_amount": {"value": 37335000.0, "display_value": "37,335,000 MMK"},
					"outstanding_amount": {"value": 63125000.0, "display_value": "63,125,000 MMK"},
					"overdue_ratio": {"value": 59.1, "display_value": "59.1%"},
					"credit_utilization": {"value": 84.2, "display_value": "84.2%"},
				},
				"primary_metric_id": "overdue_amount",
				"row_provenance": [],
				"join_key": {"customer": "Ko Nay Lin Mobile Center"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution.current_date_iso",
			return_value="2026-04-25",
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_overdue_amount_as_of_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="phase3-4-risk-default",
				message="show risky customers",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"resolved_family",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("family_id")),
			"customer_risk_as_of",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("requested_primary_metric")),
			"overdue_amount",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("requested_as_of_date")),
			"2026-04-25",
		)
		self.assertIn("outstanding_amount", ((response.get("family_resolution") or {}).get("requested_secondary_metrics") or []))
		self.assertIn("| Rank | Customer | Overdue Amount | Outstanding Amount | Overdue Ratio | Credit Utilization |", response.get("frontdoor_answer") or "")
		self.assertIn("Ko Nay Lin Mobile Center", response.get("frontdoor_answer") or "")
		normalized_artifact = response.get("normalized_family_artifact") or {}
		self.assertEqual(normalized_artifact.get("family_id"), "customer_entity_detail")
		self.assertEqual((normalized_artifact.get("period") or {}).get("as_of_date"), "2026-04-25")
		self.assertEqual((normalized_artifact.get("filters") or {}).get("composite_family_id"), "customer_risk_as_of")
		self.assertIn(
			"aging_breakdown",
			((normalized_artifact.get("dimensions") or {}).get("source_composite_followup_affordances") or []),
		)
		ranked_rows = (normalized_artifact.get("sections") or {}).get("ranked_rows") or []
		self.assertEqual(ranked_rows[0]["customer"], "Ko Nay Lin Mobile Center")
		self.assertEqual(ranked_rows[0]["overdue_amount"], 37335000.0)
		self.assertEqual(ranked_rows[0]["credit_utilization"], 84.2)
		grounded_turn = response.get("grounded_turn_context") or {}
		self.assertEqual(grounded_turn.get("artifact_family_id"), "customer_entity_detail")
		self.assertEqual((grounded_turn.get("date_range") or {}).get("as_of_date"), "2026-04-25")
		self.assertEqual((grounded_turn.get("known_entities") or [])[0]["entity_type"], "customer")
		self.assertEqual((grounded_turn.get("known_entities") or [])[0]["rank"], 1)

	def test_entity_composite_assembly_derives_secondary_metric_from_primary_row_metadata(self):
		assembly_contract = types.SimpleNamespace(
			join_key_schema=["customer"],
			row_identity_policy="customer_name",
			row_missing_component_policy="degrade_row_keep_primary",
		)
		component_artifacts = {
			"overdue_amount": types.SimpleNamespace(
				rows=[
					{
						"customer": "Ko Nay Lin Mobile Center",
						"customer_name": "Ko Nay Lin Mobile Center",
						"value": 37335000.0,
						"display_value": "37,335,000 MMK",
						"outstanding_total": 63125000.0,
						"aging_buckets": [
							{"bucket": "0-30", "amount": 23190000.0},
							{"bucket": "31-60", "amount": 17760000.0},
						],
					}
				]
			)
		}
		rows, error = _assemble_entity_period_commercial_rows(
			assembly_contract=assembly_contract,
			component_artifacts=component_artifacts,
			primary_metric_id="overdue_amount",
			secondary_metric_ids=["outstanding_amount"],
			requested_limit=10,
			sort_direction="desc",
			derived_metric_specs={
				"outstanding_amount": {
					"source_metric_id": "overdue_amount",
					"value_key": "outstanding_total",
					"display_format": "money_mmk",
				}
			},
		)
		self.assertEqual(error, "")
		self.assertEqual(rows[0]["metric_values"]["outstanding_amount"]["value"], 63125000.0)
		self.assertEqual(rows[0]["metric_values"]["outstanding_amount"]["display_value"], "63,125,000 MMK")
		self.assertEqual(rows[0]["aging_buckets"][0]["bucket"], "0-30")
		self.assertEqual(rows[0]["aging_buckets"][1]["amount"], 17760000.0)
