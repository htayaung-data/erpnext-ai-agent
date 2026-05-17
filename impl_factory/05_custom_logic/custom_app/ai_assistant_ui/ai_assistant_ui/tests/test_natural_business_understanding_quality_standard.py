import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_contracts import (
	ALLOWED_ACTION_DECISIONS,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_quality_standard import (
	list_nbu_business_conversation_quality_rules,
	nbu_action_quality_expectations,
	validate_nbu_business_conversation_quality_standard,
	validate_nbu_user_facing_response_text,
)


class NaturalBusinessUnderstandingQualityStandardTests(unittest.TestCase):
	def test_quality_standard_is_valid_and_covers_baseline_failures(self):
		result = validate_nbu_business_conversation_quality_standard()

		self.assertTrue(result["ok"], result["errors"])
		self.assertGreaterEqual(result["rule_count"], 10)

	def test_every_allowed_action_has_quality_expectations(self):
		for action in sorted(ALLOWED_ACTION_DECISIONS):
			with self.subTest(action=action):
				self.assertGreaterEqual(len(nbu_action_quality_expectations(action)), 1)

	def test_baseline_failure_classes_are_covered_by_quality_rules(self):
		baseline_failure_classes = {
			str(value or "").strip()
			for case in list_nbu_front_controller_baseline_cases()
			for value in case.get("failure_classes", [])
			if str(value or "").strip()
		}
		covered_failure_classes = {
			str(value or "").strip()
			for rule in list_nbu_business_conversation_quality_rules()
			for value in rule.get("covered_failure_classes", [])
			if str(value or "").strip()
		}

		self.assertTrue(baseline_failure_classes.issubset(covered_failure_classes))

	def test_user_facing_response_validator_allows_business_language(self):
		result = validate_nbu_user_facing_response_text(
			{
				"title": "Decision Not Available Yet",
				"answer_text": "I can show the ERP facts we have, but I cannot safely predict default next month.",
				"next_steps": ["ask for overdue balance, aging, payment history, or credit usage"],
			}
		)

		self.assertTrue(result["ok"], result["violations"])

	def test_user_facing_response_validator_blocks_internal_language(self):
		result = validate_nbu_user_facing_response_text(
			{
				"title": "Governed Boundary",
				"answer_text": "The runtime contract cannot use this artifact because blocked_missing_policy is active.",
				"next_steps": ["inspect the policy artifact"],
			}
		)

		self.assertFalse(result["ok"])
		self.assertIn("contract", result["violations"])
		self.assertIn("runtime", result["violations"])
		self.assertIn("artifact", result["violations"])
		self.assertIn("governed boundary", result["violations"])

	def test_quality_rules_are_action_backed_not_only_documentation(self):
		for rule in list_nbu_business_conversation_quality_rules():
			with self.subTest(rule=rule["rule_id"]):
				self.assertTrue(rule["applies_to_actions"])
				for action in rule["applies_to_actions"]:
					self.assertIn(action, ALLOWED_ACTION_DECISIONS)


if __name__ == "__main__":
	unittest.main()
