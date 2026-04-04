import unittest

from ai_assistant_ui.qwen_chat.semantic_resolution_registry import (
	validate_semantic_resolution_registry,
)


class TestSemanticResolutionRegistry(unittest.TestCase):
	def test_current_metadata_validates(self):
		result = validate_semantic_resolution_registry()
		self.assertEqual(
			result.status,
			"pass",
			f"Current semantic resolution registry must validate cleanly: {result.errors!r}",
		)
		self.assertGreaterEqual(result.stats.get("slot_definition_count", 0), 2)

	def test_validator_rejects_unknown_family(self):
		result = validate_semantic_resolution_registry(
			{
				"contract_version": "1.0",
				"slot_definitions": [
					{
						"slot_name": "statement_variant",
						"allowed_values": ["profit_and_loss"],
						"required_for_intent_classes": ["financial_statement"],
						"resolution_mode": "required_or_clarify",
					}
				],
				"alias_maps": {
					"statement_variant": [
						{
							"canonical_value": "profit_and_loss",
							"aliases": ["profit and loss"],
						}
					]
				},
				"family_resolution_rules": [
					{
						"rule_id": "broken_rule",
						"intent_class": "financial_statement",
						"required_slots": {"statement_variant": "profit_and_loss"},
						"candidate_family_ids": ["missing_family"],
						"candidate_capability_ids": ["financial_statement_read"],
						"candidate_reports": ["Profit and Loss Statement"],
						"governed_decision": "execute",
						"ambiguity_policy": "none",
					}
				],
				"ambiguity_policies": [
					{
						"policy_id": "missing_variant",
						"intent_class": "financial_statement",
						"missing_slots": ["statement_variant"],
						"decision": "clarify",
						"reason": "statement_variant_required",
					}
				],
				"defaults": {},
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("missing_family" in message for message in result.errors),
			f"Expected unknown family validation error, got: {result.errors!r}",
		)
