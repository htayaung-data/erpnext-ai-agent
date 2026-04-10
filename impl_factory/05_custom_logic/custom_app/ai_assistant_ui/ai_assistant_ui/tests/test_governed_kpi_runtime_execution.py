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

from ai_assistant_ui.qwen_chat.governed_kpi_execution_state import (
	build_governed_kpi_ranking_artifact_contract,
	build_governed_kpi_value_artifact_contract,
)
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	maybe_build_governed_kpi_value_frontdoor_response,
)


class TestGovernedKpiRuntimeExecution(unittest.TestCase):
	COMPANY = "Mingalar Mobile Distribution Co., Ltd."

	def test_sales_order_aov_last_month_executes_governed_value(self):
		def _fake_artifact(*, definition_state, formula_state, execution_state, requested_scope):
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope={"company": definition_state.requested_company_name},
				period_start=requested_scope.get("period_start"),
				period_end=requested_scope.get("period_end"),
				value=1473000,
				display_value="1,473,000 MMK",
				numerator_label="Grand Total",
				numerator_value=13257000,
				denominator_label="Submitted Document Count",
				denominator_value=9,
				source_evidence=[{"report_name": "Sales Order List"}],
				status="active_value",
			)

		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution._execute_company_period_value_artifact",
			side_effect=_fake_artifact,
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-aov-last-month",
				message="what is average order value for sales orders last month",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		self.assertEqual(result.get("semantic_result").intent.intent_class, "governed_kpi_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("1,473,000 MMK", answer)
		self.assertIn("2026-03-01 to 2026-03-31", answer)
		self.assertIn("13,257,000 MMK", answer)
		self.assertNotIn("Source:", answer)

	def test_ambiguous_period_kpi_requests_basis_clarification_and_preserves_period(self):
		result = maybe_build_governed_kpi_value_frontdoor_response(
			request_id="test-aov-ambiguous-period",
			message="show average order value last month",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "ambiguous")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("need the approved basis first", answer)
		self.assertIn("Average Order Value by Sales Order", answer)
		signal = result.get("clarification_signal_payload", {})
		self.assertEqual(signal.get("reason_type"), "governed_kpi_definition_ambiguity")
		self.assertEqual(signal.get("internal_details", {}).get("continuation_lane"), "front_door")
		self.assertEqual(
			signal.get("internal_details", {}).get("resolved_message_by_option", {}).get("Average Order Value by Sales Order"),
			"show average order value sales order last month",
		)
		self.assertIn(
			"sales order",
			signal.get("internal_details", {}).get("option_aliases_by_option", {}).get("Average Order Value by Sales Order", []),
		)

	def test_specific_period_kpi_without_period_requests_time_scope(self):
		result = maybe_build_governed_kpi_value_frontdoor_response(
			request_id="test-aov-period-missing",
			message="what is average order value for sales orders",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "clarify_scope")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("need the business period", answer)
		signal = result.get("clarification_signal_payload", {})
		self.assertEqual(signal.get("reason_type"), "time_scope_missing")
		self.assertEqual(signal.get("suggested_options"), ["Last Month", "Current Fiscal Year to Date", "Last Year"])
		self.assertEqual(
			signal.get("internal_details", {}).get("resolved_message_by_option", {}).get("Last Month"),
			"show average order value sales order last month",
		)

	def test_sales_invoice_aov_last_month_executes_without_basis_clarification(self):
		def _fake_artifact(*, definition_state, formula_state, execution_state, requested_scope):
			return build_governed_kpi_value_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope={"company": definition_state.requested_company_name},
				period_start=requested_scope.get("period_start"),
				period_end=requested_scope.get("period_end"),
				value=1124347.83,
				display_value="1,124,347.83 MMK",
				numerator_label="Grand Total",
				numerator_value=25860000,
				denominator_label="Submitted Document Count",
				denominator_value=23,
				source_evidence=[{"report_name": "Sales Invoice List"}],
				status="active_value",
			)

		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution._execute_company_period_value_artifact",
			side_effect=_fake_artifact,
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-aov-sales-invoice-last-month",
				message="what is average order value for sales invoices last month",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		self.assertEqual(result.get("definition_state", {}).get("definition_id"), "average_order_value_sales_invoice_period")
		self.assertIn("1,124,347.83 MMK", result.get("frontdoor_answer", ""))

	def test_definition_owned_query_is_not_hijacked_by_runtime_execution(self):
		result = maybe_build_governed_kpi_value_frontdoor_response(
			request_id="test-definition-owned-query",
			message="what is average order value",
			company_name=self.COMPANY,
		)
		self.assertEqual(result, {})

	def test_collection_ratio_last_month_executes_governed_value(self):
		with patch(
			"ai_assistant_ui.qwen_chat.collections_support.compute_collection_ratio_by_sales_invoice_period",
			return_value={
				"company": self.COMPANY,
				"from_date": "2026-03-01",
				"to_date": "2026-03-31",
				"invoice_count": 21,
				"sales_invoice_grand_total": 26109000.0,
				"allocated_customer_receipt_amount": 17889000.0,
				"collection_ratio": 0.6851660347006779,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-collection-ratio-last-month",
				message="show collection ratio last month",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("68.52%", answer)
		self.assertIn("26,109,000 MMK", answer)
		self.assertIn("17,889,000 MMK", answer)
		self.assertNotIn("Formula basis:", answer)

	def test_customer_overdue_ratio_as_of_today_executes_governed_scalar_value(self):
		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.get_customer_kpi_scalar_snapshot",
			return_value={
				"receivable_snapshot": {
					"metrics": {
						"outstanding_total": 12000000,
						"overdue_total": 10000000,
						"overdue_ratio": 0.8333333333333334,
					}
				},
				"policy_snapshot": {},
				"lifecycle_snapshot": {},
				"credit_threshold_state": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.resolve_customer_scope_from_message",
			return_value={
				"customer": "Bayint Naung Wholesale Mobile",
				"customer_name": "Bayint Naung Wholesale Mobile",
				"entity_name": "Bayint Naung Wholesale Mobile",
				"entity_label": "Bayint Naung Wholesale Mobile",
				"has_customer_scope": True,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-overdue-ratio-customer",
				message="what is overdue ratio for Bayint Naung Wholesale Mobile as of today",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("83.33%", answer)
		self.assertIn("10,000,000 MMK", answer)
		self.assertIn("12,000,000 MMK", answer)
		self.assertNotIn("Source:", answer)

	def test_credit_limit_status_question_uses_governed_scalar_threshold_answer(self):
		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.get_customer_kpi_scalar_snapshot",
			return_value={
				"receivable_snapshot": {
					"metrics": {
						"outstanding_total": 12000000,
						"overdue_total": 10000000,
						"overdue_ratio": 0.8333333333333334,
					}
				},
				"policy_snapshot": {
					"configured": True,
					"credit_limit": 10000000,
					"utilization_ratio": 1.2,
				},
				"lifecycle_snapshot": {},
				"credit_threshold_state": {"matched_band_label": "limit_exceeded"},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.resolve_customer_scope_from_message",
			return_value={
				"customer": "Bayint Naung Wholesale Mobile",
				"customer_name": "Bayint Naung Wholesale Mobile",
				"entity_name": "Bayint Naung Wholesale Mobile",
				"entity_label": "Bayint Naung Wholesale Mobile",
				"has_customer_scope": True,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-credit-limit-status-customer",
				message="has Bayint Naung Wholesale Mobile exceeded credit limit?",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("Yes.", answer)
		self.assertIn("exceeded the approved credit limit", answer)

	def test_customer_tenure_value_without_customer_scope_requests_customer(self):
		result = maybe_build_governed_kpi_value_frontdoor_response(
			request_id="test-tenure-customer-scope-missing",
			message="show customer tenure by first sales order as of today",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "clarify_scope")
		self.assertEqual(
			result.get("clarification_signal_payload", {}).get("reason_type"),
			"customer_scope_missing",
		)
		self.assertIn("still need the customer", result.get("frontdoor_answer", ""))

	def test_customer_tenure_by_created_date_executes_governed_scalar_value(self):
		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.get_customer_kpi_scalar_snapshot",
			return_value={
				"receivable_snapshot": {"metrics": {}},
				"policy_snapshot": {},
				"lifecycle_snapshot": {
					"customer_created_date": "2026-03-29",
					"customer_created_tenure_days": 12,
				},
				"credit_threshold_state": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.resolve_customer_scope_from_message",
			return_value={
				"customer": "Bayint Naung Wholesale Mobile",
				"customer_name": "Bayint Naung Wholesale Mobile",
				"entity_name": "Bayint Naung Wholesale Mobile",
				"entity_label": "Bayint Naung Wholesale Mobile",
				"has_customer_scope": True,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-customer-created-tenure",
				message="what is customer tenure by customer created date for Bayint Naung Wholesale Mobile as of today",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("12 days", answer)
		self.assertIn("2026-03-29", answer)
		self.assertNotIn("Source:", answer)

	def test_top_customers_by_credit_utilization_executes_governed_ranking(self):
		fake_execution_state = None

		def _fake_ranking_artifact(*, definition_state, formula_state, execution_state, requested_scope, message):
			nonlocal fake_execution_state
			fake_execution_state = execution_state
			return build_governed_kpi_ranking_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope={"company": definition_state.requested_company_name},
				as_of_date=requested_scope.get("as_of_date"),
				ranking_mode="top_n_desc",
				sort_direction="desc",
				applied_limit=5,
				rows=[
					{
						"customer": "Bayint Naung Wholesale Mobile",
						"customer_name": "Bayint Naung Wholesale Mobile",
						"value": 1.2,
						"display_value": "120%",
						"outstanding_total": 12000000,
						"credit_limit": 10000000,
					}
				],
				source_evidence=[{"report_name": "Accounts Receivable Summary"}, {"report_name": "Customer Credit Limit"}],
				status="active_value",
			)

		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution._execute_customer_ranking_artifact",
			side_effect=_fake_ranking_artifact,
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-credit-utilization-ranking",
				message="show top 5 customers by credit utilization",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(fake_execution_state.execution_shape, "customer_as_of_ranking")
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		self.assertIn("top 5 customers", result.get("frontdoor_answer", "").lower())
		self.assertIn("120%", result.get("frontdoor_answer", ""))

	def test_customers_above_credit_limit_executes_threshold_match_ranking(self):
		fake_execution_state = None

		def _fake_ranking_artifact(*, definition_state, formula_state, execution_state, requested_scope, message):
			nonlocal fake_execution_state
			fake_execution_state = execution_state
			return build_governed_kpi_ranking_artifact_contract(
				execution_state=execution_state,
				entity_grain=definition_state.entity_grain,
				scope={"company": definition_state.requested_company_name},
				as_of_date=requested_scope.get("as_of_date"),
				ranking_mode="threshold_match",
				sort_direction="desc",
				applied_limit=1,
				threshold_state={
					"threshold_id": "customer_credit_utilization_policy_bands",
					"matched_band_label": "limit_exceeded",
				},
				rows=[
					{
						"customer": "Bayint Naung Wholesale Mobile",
						"customer_name": "Bayint Naung Wholesale Mobile",
						"value": 1.2,
						"display_value": "120%",
						"outstanding_total": 12000000,
						"credit_limit": 10000000,
						"credit_limit_excess": 2000000,
						"threshold_state": {"matched_band_label": "limit_exceeded"},
					}
				],
				source_evidence=[{"report_name": "Accounts Receivable Summary"}, {"report_name": "Customer Credit Limit"}],
				status="active_value",
			)

		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution._execute_customer_ranking_artifact",
			side_effect=_fake_ranking_artifact,
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-customers-above-credit-limit",
				message="show customers above credit limit",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		self.assertEqual(fake_execution_state.execution_shape, "customer_as_of_ranking")
		self.assertEqual(result.get("definition_state", {}).get("definition_id"), "credit_utilization_customer_as_of_date")
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("above the approved credit limit", answer)
		self.assertIn("2,000,000 MMK above limit", answer)

	def test_deictic_customer_tenure_uses_grounded_customer_context(self):
		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.get_customer_kpi_scalar_snapshot",
			return_value={
				"receivable_snapshot": {"metrics": {}},
				"policy_snapshot": {},
				"lifecycle_snapshot": {
					"customer_created_date": "2026-03-30",
					"customer_created_tenure_days": 11,
				},
				"credit_threshold_state": {},
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-deictic-customer-tenure",
				message="what is this customer's tenure by customer created date?",
				company_name=self.COMPANY,
				grounded_turn={
					"artifact_family_id": "entity_detail",
					"known_entities": [
						{
							"entity_type": "customer",
							"name": "Zegyo Mobile Supply House",
							"code": "Zegyo Mobile Supply House",
						}
					],
					"filters": {"entity_type": "customer", "entity_key": "Zegyo Mobile Supply House"},
				},
			)
		self.assertTrue(result)
		self.assertEqual(result.get("execution_state", {}).get("resolution_state"), "active_value")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("Zegyo Mobile Supply House", answer)
		self.assertIn("11 days", answer)

	def test_collection_ratio_calculation_request_exposes_detail_on_demand(self):
		with patch(
			"ai_assistant_ui.qwen_chat.collections_support.compute_collection_ratio_by_sales_invoice_period",
			return_value={
				"company": self.COMPANY,
				"from_date": "2026-03-01",
				"to_date": "2026-03-31",
				"invoice_count": 21,
				"sales_invoice_grand_total": 26109000.0,
				"allocated_customer_receipt_amount": 17889000.0,
				"collection_ratio": 0.6851660347006779,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-collection-ratio-calculation",
				message="how was collection ratio calculated for last month",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		answer = result.get("frontdoor_answer", "")
		self.assertIn("How it was calculated", answer)
		self.assertIn("Formula basis:", answer)
		self.assertIn("Source:", answer)

	def test_customer_overdue_ratio_calculation_request_exposes_detail_on_demand(self):
		with patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.get_customer_kpi_scalar_snapshot",
			return_value={
				"receivable_snapshot": {
					"metrics": {
						"outstanding_total": 12000000,
						"overdue_total": 10000000,
						"overdue_ratio": 0.8333333333333334,
					}
				},
				"policy_snapshot": {},
				"lifecycle_snapshot": {},
				"credit_threshold_state": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution.resolve_customer_scope_from_message",
			return_value={
				"customer": "Bayint Naung Wholesale Mobile",
				"customer_name": "Bayint Naung Wholesale Mobile",
				"entity_name": "Bayint Naung Wholesale Mobile",
				"entity_label": "Bayint Naung Wholesale Mobile",
				"has_customer_scope": True,
			},
		):
			result = maybe_build_governed_kpi_value_frontdoor_response(
				request_id="test-overdue-ratio-customer-calculation",
				message="how is overdue ratio for Bayint Naung Wholesale Mobile calculated as of today",
				company_name=self.COMPANY,
			)
		self.assertTrue(result)
		answer = result.get("frontdoor_answer", "")
		self.assertIn("How it was calculated", answer)
		self.assertIn("Formula basis:", answer)
		self.assertIn("Source:", answer)
