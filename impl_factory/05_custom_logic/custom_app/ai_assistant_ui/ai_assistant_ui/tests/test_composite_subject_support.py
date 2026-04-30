import unittest

from ai_assistant_ui.qwen_chat.composite_subject_support import (
	composite_entity_dimension_label,
	composite_family_from_entity_dimension,
)


class TestCompositeSubjectSupport(unittest.TestCase):
	def test_composite_family_from_entity_dimension_maps_customer(self):
		self.assertEqual(
			composite_family_from_entity_dimension("customer"),
			("customer_commercial_ranking", "customer"),
		)

	def test_composite_family_from_entity_dimension_maps_product_aliases(self):
		self.assertEqual(
			composite_family_from_entity_dimension("product"),
			("product_commercial_ranking", "product"),
		)
		self.assertEqual(
			composite_family_from_entity_dimension("item"),
			("product_commercial_ranking", "product"),
		)

	def test_composite_entity_dimension_label_uses_governed_labels(self):
		self.assertEqual(composite_entity_dimension_label("customer"), "Customer")
		self.assertEqual(composite_entity_dimension_label("item"), "Product")
		self.assertEqual(composite_entity_dimension_label("supplier"), "Supplier")


if __name__ == "__main__":
	unittest.main()
