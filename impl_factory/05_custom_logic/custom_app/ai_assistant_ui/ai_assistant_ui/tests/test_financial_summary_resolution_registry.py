import unittest

from ai_assistant_ui.qwen_chat.financial_summary_resolution_registry import (
	validate_financial_summary_resolution_registry,
)


class TestFinancialSummaryResolutionRegistry(unittest.TestCase):
	def test_current_metadata_validates(self):
		result = validate_financial_summary_resolution_registry()
		self.assertEqual(
			result.status,
			"pass",
			f"Current financial summary resolution registry must validate cleanly: {result.errors!r}",
		)
		self.assertGreaterEqual(result.stats.get("domain_rule_count", 0), 1)
		self.assertGreaterEqual(result.stats.get("clarification_rule_count", 0), 1)

	def test_validator_rejects_unknown_target_intent(self):
		result = validate_financial_summary_resolution_registry(
			{
				"contract_version": "1.0",
				"intent_class": "financial_summary",
				"summary_domains": ["inventory"],
				"summary_focuses": ["value_snapshot"],
				"summary_metric_families": ["balance_value"],
				"summary_grains": ["warehouse"],
				"domain_rules": [
					{
						"rule_id": "inventory_domain",
						"source": "candidate_capability_ids",
						"match_any": ["stock_read"],
						"emit_domain": "inventory",
					}
				],
				"metric_family_rules": [
					{
						"rule_id": "balance_value_metric",
						"canonical_metrics_any": ["balance_value"],
						"emit_metric_family": "balance_value",
					}
				],
				"focus_rules": [
					{
						"rule_id": "inventory_focus",
						"requires_metric_family": "balance_value",
						"emit_focus": "value_snapshot",
					}
				],
				"grain_rules": [
					{
						"rule_id": "warehouse_grain",
						"requested_dimensions_any": ["Warehouse"],
						"emit_grain": "warehouse",
					}
				],
				"normalization_rules": [
					{
						"rule_id": "bad_target",
						"required_domains_all": ["inventory"],
						"required_focus": "value_snapshot",
						"target_intent_class": "missing_intent",
					}
				],
				"clarification_policies": {
					"focus_required_domains": ["inventory"],
					"sales_domains": [],
				},
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("missing_intent" in message for message in result.errors),
			f"Expected unknown target-intent validation error, got: {result.errors!r}",
		)

	def test_validator_rejects_negative_domain_count_requirement(self):
		result = validate_financial_summary_resolution_registry(
			{
				"contract_version": "1.0",
				"intent_class": "financial_summary",
				"summary_domains": ["sales"],
				"summary_focuses": ["statement_view"],
				"summary_metric_families": ["sales_amount"],
				"summary_grains": ["customer"],
				"domain_rules": [
					{
						"rule_id": "sales_domain",
						"source": "candidate_capability_ids",
						"match_any": ["sales_read"],
						"emit_domain": "sales",
					}
				],
				"metric_family_rules": [
					{
						"rule_id": "sales_metric",
						"canonical_metrics_any": ["sales_amount"],
						"emit_metric_family": "sales_amount",
					}
				],
				"focus_rules": [
					{
						"rule_id": "statement_focus",
						"requires_metric_family": "sales_amount",
						"emit_focus": "statement_view",
					}
				],
				"grain_rules": [
					{
						"rule_id": "customer_grain",
						"requested_dimensions_any": ["Customer"],
						"emit_grain": "customer",
					}
				],
				"normalization_rules": [
					{
						"rule_id": "sales_norm",
						"required_domains_all": ["sales"],
						"required_focus": "statement_view",
						"target_intent_class": "trend_analysis",
						"decision_reason": "placeholder",
					}
				],
				"clarification_rules": [
					{
						"policy_id": "broken_no_domain",
						"requires_domain_count": -1,
						"clarification_reason_type": "financial_summary_domain_clarification",
						"ambiguity_flags": ["missing_summary_domain"],
						"ambiguity_reason": "broken",
						"decision_reason": "broken",
						"blocks_legacy_fallback": True
					}
				],
				"clarification_policies": {
					"focus_required_domains": [],
					"sales_domains": ["sales"]
				}
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("requires_domain_count" in message for message in result.errors),
			f"Expected invalid domain-count validation error, got: {result.errors!r}",
		)

	def test_validator_rejects_negative_domain_count_min_requirement(self):
		result = validate_financial_summary_resolution_registry(
			{
				"contract_version": "1.0",
				"intent_class": "financial_summary",
				"summary_domains": ["receivable", "payable"],
				"summary_focuses": ["outstanding_amount"],
				"summary_metric_families": ["outstanding_total"],
				"summary_grains": ["customer"],
				"domain_rules": [
					{
						"rule_id": "receivable_domain",
						"source": "candidate_capability_ids",
						"match_any": ["accounts_receivable_read"],
						"emit_domain": "receivable",
					}
				],
				"metric_family_rules": [
					{
						"rule_id": "outstanding_metric",
						"canonical_metrics_any": ["outstanding_amount"],
						"emit_metric_family": "outstanding_total",
					}
				],
				"focus_rules": [
					{
						"rule_id": "outstanding_focus",
						"requires_metric_family": "outstanding_total",
						"emit_focus": "outstanding_amount",
					}
				],
				"grain_rules": [
					{
						"rule_id": "customer_grain",
						"requested_dimensions_any": ["Customer"],
						"emit_grain": "customer",
					}
				],
				"normalization_rules": [
					{
						"rule_id": "receivable_norm",
						"required_domains_all": ["receivable"],
						"required_focus": "outstanding_amount",
						"target_intent_class": "aging_analysis",
						"decision_reason": "placeholder",
					}
				],
				"clarification_rules": [
					{
						"policy_id": "broken_multi_domain",
						"requires_domain_count_min": -2,
						"clarification_reason_type": "financial_summary_multi_domain_clarification",
						"ambiguity_flags": ["multiple_summary_domains"],
						"ambiguity_reason": "broken",
						"decision_reason": "broken",
						"blocks_legacy_fallback": True
					}
				],
				"clarification_policies": {
					"focus_required_domains": [],
					"sales_domains": []
				}
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("requires_domain_count_min" in message for message in result.errors),
			f"Expected invalid domain-count-min validation error, got: {result.errors!r}",
		)
