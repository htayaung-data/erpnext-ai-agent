import unittest

from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import _followup_column_alias_map
from ai_assistant_ui.qwen_chat.semantic_interpreter import interpret_artifact_local_projection_deterministically


class UXS6LProductContextContracts(unittest.TestCase):
	def test_plural_quantity_followup_is_artifact_local_column_refinement(self):
		result = interpret_artifact_local_projection_deterministically(
			message="Include quantities alongside the results.",
			latest_grounded_turn={},
			latest_family_artifact={
				"family_id": "ranking_analytics",
				"dimensions": {
					"requested_metric_key": "revenue",
					"primary_metric_key": "revenue",
					"requested_column_alias_map": {
						"qty": "quantity",
						"quantity": "quantity",
						"quantities": "quantity",
					},
				},
				"sections": {
					"ranked_rows": [
						{"rank": 1, "entity": "A", "revenue": 100, "quantity": 2},
						{"rank": 2, "entity": "B", "revenue": 80, "quantity": 1},
					]
				},
			},
		)

		self.assertEqual(result.status, "accepted")
		self.assertIsNotNone(result.intent)
		self.assertEqual(result.intent.requested_modes, ["column_refinement"])
		self.assertEqual(result.intent.requested_columns, ["quantity"])

	def test_product_composite_artifact_exposes_plural_quantity_alias(self):
		alias_map = _followup_column_alias_map(
			family_spec={
				"entity_grain": "item",
				"subject_alias_value": "product",
				"metric_semantic_key_map": {
					"revenue": ["revenue"],
					"quantity": ["quantity"],
				},
			},
			metric_ids=["revenue", "quantity"],
		)

		self.assertEqual(alias_map.get("quantity"), "quantity")
		self.assertEqual(alias_map.get("quantities"), "quantity")


if __name__ == "__main__":
	unittest.main()
