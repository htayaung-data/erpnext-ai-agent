import sys
import types
import unittest

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

from ai_assistant_ui.qwen_chat.governed_kpi_support import (
	maybe_build_governed_kpi_frontdoor_response,
	run_governed_kpi_frontdoor_probe,
)


class TestGovernedKpiFrontdoor(unittest.TestCase):
	COMPANY = "Mingalar Mobile Distribution Co., Ltd."

	def test_active_kpi_definition_uses_governed_formula_basis(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-active-kpi",
			message="what is credit utilization",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		self.assertEqual(result.get("formula_state", {}).get("resolution_state"), "active")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("Customer Credit Utilization", answer)
		self.assertIn("approved credit", answer)
		self.assertNotIn("The approved basis is", answer)
		self.assertNotIn("Entity grain:", answer)
		self.assertNotIn("Source:", answer)

	def test_active_kpi_definition_with_business_purpose_suffix_stays_governed(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-active-kpi-purpose",
			message="what is customer credit utilization and why does it matter",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("approved credit", answer)
		self.assertIn("It matters because", answer)
		self.assertIn("working-capital control", answer)

	def test_ambiguous_kpi_definition_requests_clarification(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-ambiguous-kpi",
			message="what is average order value",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "ambiguous")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("choose the approved basis first", answer.lower())
		self.assertIn("Average Order Value by Sales Order", answer)
		self.assertIn("Average Order Value by Sales Invoice", answer)
		signal = result.get("clarification_signal_payload", {})
		self.assertEqual(signal.get("reason_type"), "governed_kpi_definition_ambiguity")
		self.assertEqual(signal.get("internal_details", {}).get("continuation_lane"), "front_door")
		self.assertEqual(
			signal.get("internal_details", {}).get("resolved_message_by_option", {}).get("Average Order Value by Sales Order"),
			"what is average order value sales order",
		)

	def test_meaning_query_with_erp_context_suffix_stays_governed(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-meaning-context-kpi",
			message="what does average order value mean in this ERP",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "ambiguous")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("choose the approved basis first", answer.lower())
		self.assertIn("Average Order Value by Sales Order", answer)
		self.assertEqual(
			result.get("clarification_signal_payload", {}).get("internal_details", {}).get("resolved_message_by_option", {}).get("Average Order Value by Sales Invoice"),
			"what is average order value sales invoice",
		)

	def test_collection_ratio_definition_is_now_active(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-collection-ratio",
			message="what is collection ratio",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("collected cash against submitted sales invoices", answer.lower())
		self.assertIn("health labels are not yet approved", answer.lower())
		self.assertNotIn("Governed basis:", answer)

	def test_customer_created_tenure_definition_is_active(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-created-tenure",
			message="what is customer tenure by customer created date",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("customer created date", answer.lower())
		self.assertNotIn("Source:", answer)

	def test_explicit_unknown_definition_returns_undefined(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-undefined-kpi",
			message="define gross margin",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "undefined")
		self.assertIn("I don't have a governed KPI definition for gross margin yet", result.get("frontdoor_answer", ""))

	def test_formula_query_exposes_governed_basis_on_demand(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-active-kpi-formula",
			message="what is the formula for customer credit utilization",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		answer = result.get("frontdoor_answer", "")
		self.assertIn("approved formula", answer.lower())
		self.assertIn("Outstanding Amount / Configured Credit Limit", answer)
		self.assertIn("Governed basis:", answer)

	def test_deictic_followup_does_not_get_hijacked_by_kpi_frontdoor(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-deictic-followup",
			message="what is this customer's credit limit?",
			company_name=self.COMPANY,
		)
		self.assertEqual(result, {})

	def test_probe_reports_all_expected_states(self):
		result = run_governed_kpi_frontdoor_probe()
		self.assertTrue(result.get("ok"), result)
