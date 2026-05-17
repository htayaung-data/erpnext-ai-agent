import unittest

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	SemanticFreshQueryResult,
	_deterministic_family_surface_interpretation,
	_semantic_result_should_defer_to_deterministic_surface,
)
from ai_assistant_ui.qwen_chat.master_data_frontdoor_support import assess_master_data_frontdoor_request


class UXS6NCustomerRiskContracts(unittest.TestCase):
	def _deterministic(self, message: str):
		return _deterministic_family_surface_interpretation(
			request_id="ux-s6n-customer-risk",
			session_id="ux-s6n",
			message=message,
			confidence_threshold=0.8,
		)

	def test_customer_risk_language_routes_to_receivable_aging_not_customer_master(self):
		for message in [
			"Display customer risk levels.",
			"Show customer risk profile.",
			"Show customer credit risk.",
			"Display risk levels for customers.",
		]:
			with self.subTest(message=message):
				interpretation = self._deterministic(message)
				self.assertIsNotNone(interpretation)
				self.assertEqual(interpretation.intent_class, "aging_analysis")
				self.assertEqual(list(interpretation.candidate_capability_ids), ["accounts_receivable_read"])
				self.assertEqual(list(interpretation.candidate_reports), ["Accounts Receivable Summary"])
				self.assertEqual(dict(interpretation.extracted_slots), {"aging_view": "receivable"})

				outcome = compile_fresh_query(
					request_id="ux-s6n-customer-risk-compile",
					session_id="ux-s6n",
					interpretation=interpretation,
					response_policy={},
				)
				self.assertEqual(outcome.compiler_contract.capability_id, "accounts_receivable_read")
				self.assertEqual(outcome.compiler_contract.selected_report, "Accounts Receivable Summary")

	def test_plain_customer_directory_language_still_routes_to_customer_master(self):
		interpretation = self._deterministic("Show me customers.")

		self.assertIsNotNone(interpretation)
		self.assertEqual(interpretation.intent_class, "master_data_lookup")
		self.assertEqual(list(interpretation.candidate_capability_ids), ["customer_master_read"])
		self.assertEqual(list(interpretation.candidate_reports), ["Customer Master List"])

	def test_supplier_risk_language_routes_to_payable_aging_not_customer_risk(self):
		interpretation = self._deterministic("Display supplier risk levels.")

		self.assertIsNotNone(interpretation)
		self.assertEqual(interpretation.intent_class, "aging_analysis")
		self.assertEqual(list(interpretation.candidate_capability_ids), ["accounts_payable_read"])
		self.assertEqual(list(interpretation.candidate_reports), ["Accounts Payable Summary"])
		self.assertEqual(dict(interpretation.extracted_slots), {"aging_view": "payable"})

	def test_governed_risk_surface_overrides_master_data_listing_guess(self):
		deterministic = self._deterministic("Display supplier risk levels.")
		master_data_guess = build_fresh_query_interpretation_contract(
			request_id="ux-s6n-supplier-master-guess",
			session_id="ux-s6n",
			intent_class="master_data_lookup",
			candidate_capability_ids=["supplier_master_read"],
			candidate_reports=["Supplier Master List"],
			requested_dimensions=["Supplier"],
			requested_metrics=[],
			requested_time_scope="",
			target_limit=0,
			requested_presentation=[],
			extracted_slots={"entity_grain": "supplier", "lookup_mode": "directory_list"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.9,
		)

		self.assertTrue(
			_semantic_result_should_defer_to_deterministic_surface(
				semantic_result=SemanticFreshQueryResult(
					status="accepted",
					interpretation=master_data_guess,
				),
				deterministic_interpretation=deterministic,
			)
		)

	def test_master_data_frontdoor_does_not_claim_customer_risk_as_directory(self):
		payload = assess_master_data_frontdoor_request(
			request_id="ux-s6n-master-data-risk-block",
			message="Display customer risk levels.",
			frontdoor_extracted_slots={
				"lookup_mode": "directory_list",
				"entity_grain": "customer",
			},
		)
		assessment = payload.get("assessment_contract")

		self.assertIsNotNone(assessment)
		self.assertEqual(assessment.status, "not_applicable")
		self.assertIn(
			"risk",
			(assessment.internal_details or {}).get("blocked_by_business_concepts", []),
		)


if __name__ == "__main__":
	unittest.main()
