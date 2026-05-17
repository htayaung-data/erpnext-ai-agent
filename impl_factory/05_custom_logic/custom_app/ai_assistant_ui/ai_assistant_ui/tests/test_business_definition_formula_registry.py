import unittest

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import (
	validate_business_definition_registry,
	validate_business_threshold_registry,
	validate_governed_formula_registry,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_business_definition_spec,
	get_business_threshold_spec,
	get_governed_formula_spec,
	load_business_definition_registry,
	load_business_threshold_registry,
	load_governed_formula_registry,
)


def _activation_states():
	return [
		"active",
		"blocked_missing_policy",
		"blocked_missing_data",
		"draft_unapproved",
		"deprecated",
	]


class TestBusinessDefinitionFormulaRegistry(unittest.TestCase):
	def test_current_registry_payloads_validate(self):
		definition_result = validate_business_definition_registry()
		formula_result = validate_governed_formula_registry()
		threshold_result = validate_business_threshold_registry()

		self.assertEqual(
			definition_result.status,
			"pass",
			f"Business definition registry scaffold must validate cleanly: {definition_result.errors!r}",
		)
		self.assertEqual(
			formula_result.status,
			"pass",
			f"Governed formula registry scaffold must validate cleanly: {formula_result.errors!r}",
		)
		self.assertEqual(
			threshold_result.status,
			"pass",
			f"Business threshold registry must validate cleanly: {threshold_result.errors!r}",
		)
		self.assertEqual(definition_result.stats.get("definition_count"), 21)
		self.assertEqual(formula_result.stats.get("formula_count"), 21)
		self.assertEqual(threshold_result.stats.get("threshold_count"), 3)
		self.assertEqual(
			definition_result.stats.get("activation_counts", {}).get("active"),
			21,
		)
		self.assertEqual(
			formula_result.stats.get("activation_counts", {}).get("active"),
			21,
		)
		self.assertEqual(
			threshold_result.stats.get("activation_counts", {}).get("active"),
			1,
		)
		self.assertEqual(
			threshold_result.stats.get("activation_counts", {}).get("blocked_missing_policy"),
			2,
		)

	def test_metadata_loaders_remain_copy_safe_and_accessors_return_current_specs(self):
		definition_payload = load_business_definition_registry()
		formula_payload = load_governed_formula_registry()
		threshold_payload = load_business_threshold_registry()
		baseline_definition_count = len(definition_payload.get("definitions") or [])
		baseline_formula_count = len(formula_payload.get("formulas") or [])
		baseline_threshold_count = len(threshold_payload.get("threshold_sets") or [])

		definition_payload["definitions"].append({"definition_id": "mutated"})
		formula_payload["formulas"].append({"formula_id": "mutated"})
		threshold_payload["threshold_sets"].append({"threshold_id": "mutated"})

		self.assertEqual(
			len(load_business_definition_registry().get("definitions") or []),
			baseline_definition_count,
		)
		self.assertEqual(
			len(load_governed_formula_registry().get("formulas") or []),
			baseline_formula_count,
		)
		self.assertEqual(
			len(load_business_threshold_registry().get("threshold_sets") or []),
			baseline_threshold_count,
		)
		self.assertEqual(
			get_business_definition_spec("average_order_value_sales_order_period").get("activation_state"),
			"active",
		)
		self.assertEqual(
			get_governed_formula_spec("credit_utilization_customer_as_of_date_formula").get("activation_state"),
			"active",
		)
		self.assertEqual(get_business_definition_spec("missing_definition"), {})
		self.assertEqual(get_governed_formula_spec("missing_formula"), {})
		self.assertEqual(get_business_threshold_spec("missing_threshold"), {})

	def test_definition_validator_rejects_invalid_activation_state(self):
		result = validate_business_definition_registry(
			{
				"contract_version": "1.0",
				"status": "registry_scaffold_active",
				"description": "test",
				"allowed_activation_states": _activation_states(),
				"allowed_semantic_categories": ["customer_lifecycle"],
				"allowed_entity_grains": ["customer"],
				"allowed_time_bases": ["as_of_date"],
				"allowed_clarify_policies": ["clarify_basis"],
				"definitions": [
					{
						"definition_id": "customer_tenure",
						"label": "Customer Tenure",
						"description": "Customer tenure test definition.",
						"owner": "finance",
						"company_scope": ["global"],
						"entity_grain": "customer",
						"time_basis": "as_of_date",
						"semantic_category": "customer_lifecycle",
						"activation_state": "invalid_state",
						"source_of_truth": {"kind": "governed_definition"},
						"clarify_policy": "clarify_basis",
						"blocked_reason": ""
					}
				]
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("activation_state" in message for message in result.errors),
			f"Expected invalid activation-state error, got: {result.errors!r}",
		)

	def test_formula_validator_rejects_unknown_definition_reference(self):
		result = validate_governed_formula_registry(
			{
				"contract_version": "1.0",
				"status": "registry_scaffold_active",
				"description": "test",
				"allowed_activation_states": _activation_states(),
				"allowed_formula_types": ["ratio"],
				"allowed_aggregation_rules": ["ratio_of_sums"],
				"allowed_input_requirement_types": ["required"],
				"allowed_time_scope_requirements": ["period_required"],
				"formulas": [
					{
						"formula_id": "collection_ratio_period",
						"definition_id": "missing_definition",
						"label": "Collection Ratio",
						"formula_type": "ratio",
						"input_metrics": ["paid_amount", "invoiced_amount"],
						"input_requirements": [
							{"metric_key": "paid_amount", "requirement_type": "required"},
							{"metric_key": "invoiced_amount", "requirement_type": "required"}
						],
						"source_capabilities": ["accounts_receivable_read"],
						"source_reports": ["Accounts Receivable Summary"],
						"aggregation_rule": "ratio_of_sums",
						"grain_requirements": ["company"],
						"time_scope_requirements": ["period_required"],
						"activation_state": "draft_unapproved",
						"blocked_reason": "awaiting approved definition"
					}
				]
			},
			business_definition_payload={"definitions": []},
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("unknown definition" in message for message in result.errors),
			f"Expected unknown-definition validation error, got: {result.errors!r}",
		)

	def test_threshold_validator_requires_exactly_one_subject_reference(self):
		result = validate_business_threshold_registry(
			{
				"contract_version": "1.0",
				"status": "registry_scaffold_active",
				"description": "test",
				"allowed_activation_states": _activation_states(),
				"allowed_threshold_bases": ["overdue_amount"],
				"allowed_band_directions": ["higher_is_worse"],
				"threshold_sets": [
					{
						"threshold_id": "overdue_watch_bands",
						"label": "Overdue Watch Bands",
						"owner": "finance",
						"company_scope": ["global"],
						"threshold_basis": "overdue_amount",
						"band_direction": "higher_is_worse",
						"bands": [
							{"label": "watch"},
							{"label": "critical"}
						],
						"activation_state": "draft_unapproved",
						"blocked_reason": "definition or formula owner not chosen"
					}
				]
			},
			business_definition_payload={"definitions": []},
			governed_formula_payload={"formulas": []},
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("exactly one of definition_id or formula_id" in message for message in result.errors),
			f"Expected threshold subject-reference validation error, got: {result.errors!r}",
		)
