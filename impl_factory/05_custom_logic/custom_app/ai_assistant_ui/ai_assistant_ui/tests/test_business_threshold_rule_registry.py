import unittest

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import (
	validate_business_threshold_registry,
)
from ai_assistant_ui.qwen_chat.business_rule_registry import (
	validate_business_rule_registry,
)
from ai_assistant_ui.qwen_chat.business_threshold_state import (
	evaluate_business_threshold,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_business_rule_spec,
	load_business_rule_registry,
)


class TestBusinessThresholdRuleRegistry(unittest.TestCase):
	def test_current_business_rule_registry_validates(self):
		result = validate_business_rule_registry()
		self.assertEqual(result.status, "pass", f"Business rule registry should validate cleanly: {result.errors!r}")
		self.assertEqual(result.stats.get("rule_count"), 6)
		self.assertEqual(result.stats.get("activation_counts", {}).get("active"), 6)

	def test_business_rule_registry_loader_is_copy_safe_and_accessor_returns_current_rule(self):
		payload = load_business_rule_registry()
		baseline_count = len(payload.get("rules") or [])
		payload["rules"].append({"rule_id": "mutated"})
		self.assertEqual(len(load_business_rule_registry().get("rules") or []), baseline_count)
		self.assertEqual(
			get_business_rule_spec("credit_utilization_primary_basis_outstanding_vs_limit").get("activation_state"),
			"active",
		)
		self.assertEqual(get_business_rule_spec("missing_rule"), {})

	def test_threshold_evaluation_returns_active_band_for_credit_utilization(self):
		within_limit = evaluate_business_threshold(
			"customer_credit_utilization_policy_bands",
			observed_value=0.25,
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		limit_exceeded = evaluate_business_threshold(
			"customer_credit_utilization_policy_bands",
			observed_value=1.25,
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(within_limit.resolution_state, "active")
		self.assertEqual(within_limit.matched_band_label, "within_limit")
		self.assertEqual(limit_exceeded.resolution_state, "active")
		self.assertEqual(limit_exceeded.matched_band_label, "limit_exceeded")

	def test_threshold_evaluation_respects_blocked_threshold_activation(self):
		result = evaluate_business_threshold(
			"customer_overdue_ratio_severity_bands",
			observed_value=0.42,
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(result.resolution_state, "blocked")
		self.assertEqual(
			result.blocked_reason,
			"customer overdue severity labels are not yet approved for user-facing runtime use.",
		)

	def test_threshold_validator_rejects_conflicting_band_bounds(self):
		result = validate_business_threshold_registry(
			{
				"contract_version": "1.0",
				"status": "test",
				"allowed_activation_states": [
					"active",
					"blocked_missing_policy",
					"blocked_missing_data",
					"draft_unapproved",
					"deprecated",
				],
				"allowed_threshold_bases": ["credit_utilization_ratio"],
				"allowed_band_directions": ["higher_is_worse"],
				"threshold_sets": [
					{
						"threshold_id": "bad_threshold",
						"label": "Bad Threshold",
						"formula_id": "credit_utilization_customer_as_of_date_formula",
						"owner": "finance",
						"company_scope": ["Mingalar Mobile Distribution Co., Ltd."],
						"threshold_basis": "credit_utilization_ratio",
						"band_direction": "higher_is_worse",
						"activation_state": "active",
						"blocked_reason": "",
						"bands": [
							{
								"label": "bad",
								"lower_bound_inclusive": 0.5,
								"lower_bound_exclusive": 0.4
							}
						]
					}
				]
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("cannot define both lower_bound_inclusive and lower_bound_exclusive" in message for message in result.errors),
			f"Expected conflicting lower-bound validation error, got: {result.errors!r}",
		)

	def test_business_rule_validator_rejects_unknown_scope_reference(self):
		result = validate_business_rule_registry(
			{
				"contract_version": "1.0",
				"status": "test",
				"allowed_activation_states": [
					"active",
					"blocked_missing_policy",
					"blocked_missing_data",
					"draft_unapproved",
					"deprecated",
				],
				"allowed_rule_types": ["credit_policy_basis"],
				"allowed_scope_types": ["formula"],
				"rules": [
					{
						"rule_id": "bad_rule",
						"label": "Bad Rule",
						"owner": "finance",
						"company_scope": ["Mingalar Mobile Distribution Co., Ltd."],
						"rule_type": "credit_policy_basis",
						"scope_type": "formula",
						"scope_reference": "missing_formula",
						"policy_statement": "test",
						"activation_state": "active",
						"blocked_reason": "",
						"enforced_behavior": {"comparison_basis": "x"}
					}
				]
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("unknown formula" in message for message in result.errors),
			f"Expected unknown-formula validation error, got: {result.errors!r}",
		)
