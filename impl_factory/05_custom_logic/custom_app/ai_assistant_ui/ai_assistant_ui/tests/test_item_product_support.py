import unittest

from ai_assistant_ui.qwen_chat.composite_subject_support import (
	composite_entity_dimension_label,
	composite_family_from_entity_dimension,
)
from ai_assistant_ui.qwen_chat.followup_entity_domain_support import (
	detected_message_entity_domains,
)
from ai_assistant_ui.qwen_chat.item_product_support import (
	is_item_product_grain,
	item_product_context_domains,
	item_product_subject_label,
	normalize_item_product_grain,
)


class TestItemProductSupport(unittest.TestCase):
	def test_item_product_helper_normalizes_product_to_item(self) -> None:
		self.assertEqual(normalize_item_product_grain("product"), "item")
		self.assertEqual(normalize_item_product_grain("item"), "item")
		self.assertTrue(is_item_product_grain("product"))
		self.assertEqual(item_product_context_domains("product"), {"product", "inventory"})
		self.assertEqual(item_product_subject_label("item", analytical=True), "Product")

	def test_composite_subject_support_uses_shared_item_product_ownership(self) -> None:
		self.assertEqual(
			composite_family_from_entity_dimension("product"),
			("product_commercial_ranking", "product"),
		)
		self.assertEqual(
			composite_family_from_entity_dimension("item"),
			("product_commercial_ranking", "product"),
		)
		self.assertEqual(composite_entity_dimension_label("product"), "Product")

	def test_detected_message_entity_domains_keeps_product_on_item_owned_path(self) -> None:
		from unittest.mock import patch

		with patch(
			"ai_assistant_ui.qwen_chat.followup_entity_domain_support.ontology_detect_concepts",
			return_value=["product", "inventory", "warehouse"],
		):
			self.assertEqual(
				detected_message_entity_domains("show me product inventory"),
				{"item", "inventory"},
			)

if __name__ == "__main__":
	unittest.main()
