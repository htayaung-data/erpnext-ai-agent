import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.followup_entity_domain_support import (
	detected_message_entity_domains,
	entity_detail_context_domains,
	is_entity_detail_context_family,
	local_entity_detail_followup_family_ids,
	ranking_subject_alias_map,
	subject_alias_from_label,
)


class FollowupEntityDomainSupportTests(unittest.TestCase):
	def test_entity_detail_context_domains_includes_customer_and_item_inventory(self) -> None:
		domains = entity_detail_context_domains(
			{
				"known_entities": [
					{"entity_type": "customer"},
					{"entity_type": "item"},
				],
				"dimensions": ["customer"],
			}
		)
		self.assertIn("customer", domains)
		self.assertIn("product", domains)
		self.assertIn("inventory", domains)

	def test_subject_alias_resolution_uses_composite_registry(self) -> None:
		with patch(
			"ai_assistant_ui.qwen_chat.followup_entity_domain_support.list_composite_family_specs",
			return_value=[
				{"subject_alias_value": "customer", "entity_grain": "customer"},
				{"subject_alias_value": "product", "entity_grain": "item"},
			],
		):
			self.assertEqual(subject_alias_from_label("customers"), "customer")
			self.assertEqual(subject_alias_from_label("items"), "product")
			self.assertEqual(ranking_subject_alias_map().get("item"), "product")

	def test_local_entity_detail_followup_family_ids_come_from_composite_affordances(self) -> None:
		with patch(
			"ai_assistant_ui.qwen_chat.followup_entity_domain_support.list_composite_family_specs",
			return_value=[
				{
					"family_id": "customer_risk_as_of",
					"subject_alias_value": "customer",
					"entity_grain": "customer",
					"local_followup_family_id": "customer_entity_detail",
					"followup_affordances": ["customer_detail", "aging_breakdown"],
				},
				{
					"family_id": "product_margin_ranking",
					"subject_alias_value": "product",
					"entity_grain": "item",
					"local_followup_family_id": "ranking_analytics",
					"followup_affordances": ["rank_explanation"],
				},
			],
		):
			self.assertEqual(
				local_entity_detail_followup_family_ids(),
				{"customer_entity_detail"},
			)
			self.assertTrue(
				is_entity_detail_context_family(
					"customer_entity_detail",
					{"known_entities": [{"entity_type": "customer"}]},
				)
			)
			self.assertFalse(
				is_entity_detail_context_family(
					"customer_entity_detail",
					{"known_entities": []},
				)
			)

	def test_detected_message_entity_domains_filters_to_supported_entity_domains(self) -> None:
		with patch(
			"ai_assistant_ui.qwen_chat.followup_entity_domain_support.ontology_detect_concepts",
			return_value=["customer", "inventory", "warehouse", "sales"],
		):
			self.assertEqual(
				detected_message_entity_domains("show me customer inventory"),
				{"customer", "inventory"},
			)


if __name__ == "__main__":
	unittest.main()
