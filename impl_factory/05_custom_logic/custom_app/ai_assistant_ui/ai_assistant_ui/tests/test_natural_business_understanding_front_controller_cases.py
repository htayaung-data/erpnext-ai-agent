import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_front_controller_cases import (
	REQUIRED_BASELINE_CASE_KEYS,
	list_nbu_front_controller_baseline_cases,
	validate_nbu_front_controller_baseline_cases,
)


class NaturalBusinessUnderstandingFrontControllerCaseTests(unittest.TestCase):
	def test_baseline_case_registry_is_valid(self):
		result = validate_nbu_front_controller_baseline_cases()

		self.assertTrue(result["ok"], result["errors"])
		self.assertGreaterEqual(result["case_count"], 10)

	def test_baseline_cases_are_shared_failure_classes_not_phrase_patches(self):
		cases = list_nbu_front_controller_baseline_cases()

		for case in cases:
			self.assertTrue(REQUIRED_BASELINE_CASE_KEYS.issubset(case.keys()))
			self.assertGreaterEqual(len(case["failure_classes"]), 1)
			self.assertIsInstance(case["expected_target"], dict)
			self.assertNotIn("single_case_patch", case["failure_classes"])
			self.assertNotIn("keyword_patch", case["failure_classes"])

	def test_baseline_cases_cover_front_controller_risk_areas(self):
		cases = list_nbu_front_controller_baseline_cases()
		failure_classes = {
			str(value or "").strip()
			for case in cases
			for value in case.get("failure_classes", [])
			if str(value or "").strip()
		}
		expected = {
			"wrong_family_selection",
			"unsafe_recommendation",
			"unsafe_prediction",
			"stale_context_leakage",
			"row_reference_failure",
			"previous_artifact_resolution_failure",
			"missing_evidence_requery_gap",
			"correction_intent_failure",
			"multi_domain_understanding_gap",
			"ambiguous_reference_guess",
		}

		self.assertTrue(expected.issubset(failure_classes))

	def test_baseline_cases_cover_control_actions(self):
		actions = {
			str(case.get("expected_action") or "").strip()
			for case in list_nbu_front_controller_baseline_cases()
		}

		self.assertIn("execute_fresh_governed_query", actions)
		self.assertIn("execute_governed_requery", actions)
		self.assertIn("answer_from_current_artifact", actions)
		self.assertIn("ask_clarification", actions)
		self.assertIn("reject_with_boundary", actions)


if __name__ == "__main__":
	unittest.main()
