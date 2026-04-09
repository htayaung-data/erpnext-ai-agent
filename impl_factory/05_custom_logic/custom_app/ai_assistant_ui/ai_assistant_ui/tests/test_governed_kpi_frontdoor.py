import unittest

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
		self.assertIn("configured customer credit limit", result.get("frontdoor_answer", ""))
		self.assertIn("Threshold semantics are active", result.get("frontdoor_answer", ""))

	def test_active_kpi_definition_with_business_purpose_suffix_stays_governed(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-active-kpi-purpose",
			message="what is customer credit utilization and why does it matter",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "active")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("configured customer credit limit", answer)
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
		self.assertIn("must be clarified first", answer)
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
		self.assertIn("must be clarified first", answer)
		self.assertIn("Average Order Value by Sales Order", answer)
		self.assertEqual(
			result.get("clarification_signal_payload", {}).get("internal_details", {}).get("resolved_message_by_option", {}).get("Average Order Value by Sales Invoice"),
			"what is average order value sales invoice",
		)

	def test_blocked_kpi_definition_stays_blocked_safe(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-blocked-kpi",
			message="what is collection ratio",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "blocked")
		answer = result.get("frontdoor_answer", "")
		self.assertIn("not runtime-active yet", answer)
		self.assertIn("collected-amount", answer)

	def test_explicit_unknown_definition_returns_undefined(self):
		result = maybe_build_governed_kpi_frontdoor_response(
			request_id="test-undefined-kpi",
			message="define gross margin",
			company_name=self.COMPANY,
		)
		self.assertTrue(result)
		self.assertEqual(result.get("definition_state", {}).get("resolution_state"), "undefined")
		self.assertIn("No governed KPI definition is currently registered", result.get("frontdoor_answer", ""))

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
