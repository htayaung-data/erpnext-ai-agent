import unittest

from ai_assistant_ui.qwen_chat.entity_detail_capability_registry import (
	capability_id_for_entity_detail,
	entity_detail_capability_binding_registry,
)
from ai_assistant_ui.qwen_chat.entity_detail_request_support import entity_detail_capability_id


class EntityDetailCapabilityRegistryTests(unittest.TestCase):
	def test_registry_resolves_customer_supplier_item_and_document_capabilities(self):
		cases = {
			"customer": "accounts_receivable_read",
			"supplier": "accounts_payable_read",
			"item": "stock_read",
			"product": "stock_read",
			"purchase_order": "purchase_order_read",
			"sales_order": "sales_order_read",
			"sales_invoice": "sales_read",
		}

		for entity_type, expected_capability in cases.items():
			with self.subTest(entity_type=entity_type):
				self.assertEqual(capability_id_for_entity_detail(entity_type), expected_capability)
				self.assertEqual(entity_detail_capability_id(entity_type), expected_capability)

	def test_registry_fails_closed_for_unregistered_entity_type(self):
		self.assertEqual(capability_id_for_entity_detail("unknown_entity"), "")
		self.assertEqual(entity_detail_capability_id("unknown_entity"), "")

	def test_registry_file_is_metadata_owned(self):
		registry = entity_detail_capability_binding_registry()

		self.assertEqual(registry["type"], "qwen_entity_detail_capability_binding_registry")
		self.assertIn("entity_capability_bindings", registry)


if __name__ == "__main__":
	unittest.main()
