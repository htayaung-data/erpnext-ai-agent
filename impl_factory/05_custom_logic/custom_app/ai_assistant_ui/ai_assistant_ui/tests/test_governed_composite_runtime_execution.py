import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault("frappe", types.ModuleType("frappe"))

from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	maybe_build_governed_composite_frontdoor_response,
)


class TestGovernedCompositeRuntimeExecution(unittest.TestCase):
	def test_customer_commercial_family_clarifies_missing_basis(self):
		response = maybe_build_governed_composite_frontdoor_response(
			request_id="phase3-2-clarify-basis",
			message="show top 5 customers by revenue last month",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(
			((response.get("family_resolution") or {}).get("status")),
			"clarify_family_variation",
		)
		self.assertEqual(
			((response.get("clarification_signal_payload") or {}).get("reason_type")),
			"composite_family_variation",
		)
		self.assertIn("Sales Order", response.get("frontdoor_answer") or "")
		self.assertIn("Sales Invoice", response.get("frontdoor_answer") or "")
		internal_details = ((response.get("clarification_signal_payload") or {}).get("internal_details") or {})
		self.assertEqual(internal_details.get("semantic_slot_name"), "requested_basis")
		self.assertEqual(
			(internal_details.get("semantic_slot_value_by_option") or {}).get("Sales Order"),
			"sales_order",
		)
		self.assertEqual(
			(internal_details.get("carryover_slot_values") or {}).get("requested_primary_metric"),
			"revenue",
		)
		self.assertEqual(
			(internal_details.get("carryover_slot_values") or {}).get("selected_time_scope"),
			"last_month",
		)

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
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_customer_period_commercial_rows",
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
		self.assertIn("| Rank | Customer | Revenue | Quantity | Average Order Value |", response.get("frontdoor_answer") or "")

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
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_customer_period_commercial_rows",
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
		self.assertIn("| Rank | Customer | Quantity | Revenue | Average Invoice Value |", response.get("frontdoor_answer") or "")

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
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_customer_period_commercial_rows",
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
