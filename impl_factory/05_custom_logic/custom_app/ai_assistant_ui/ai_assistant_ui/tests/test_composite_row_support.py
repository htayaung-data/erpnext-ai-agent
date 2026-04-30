import unittest

from ai_assistant_ui.qwen_chat.composite_row_support import (
	composite_join_key_label,
	composite_row_entity_code,
	composite_row_identity_value,
	composite_row_join_key_payload,
	composite_row_join_key_tuple,
	composite_row_join_key_value,
)


class TestCompositeRowSupport(unittest.TestCase):
	def test_composite_row_join_key_value_supports_customer_and_item_code(self):
		row = {
			"customer": "Zegyo Mobile Supply House",
			"item_code": "ITEM-001",
			"entity_code": "ENTITY-001",
			"entity_key": "ENTITY-KEY-001",
		}
		self.assertEqual(composite_row_join_key_value(row, "customer"), "Zegyo Mobile Supply House")
		self.assertEqual(composite_row_join_key_value(row, "item_code"), "ITEM-001")

	def test_composite_row_join_key_payload_and_tuple_follow_schema(self):
		row = {"customer": "Ko Nay Lin Mobile Center", "posting_month": "2026-04"}
		self.assertEqual(
			composite_row_join_key_tuple(row, ["customer", "posting_month"]),
			("Ko Nay Lin Mobile Center", "2026-04"),
		)
		self.assertEqual(
			composite_row_join_key_payload(row, ["customer", "posting_month"]),
			{"customer": "Ko Nay Lin Mobile Center", "posting_month": "2026-04"},
		)

	def test_composite_row_identity_and_code_support_customer_and_item_policies(self):
		customer_row = {"customer": "Chan Aye Mobile Trading Hub", "customer_name": "Chan Aye Mobile Trading Hub"}
		item_row = {"item_code": "ITEM-002", "item_name": "Type-C Cable 1m Fast Charge", "entity_code": "ITEM-002"}
		self.assertEqual(composite_row_identity_value(customer_row, ""), "Chan Aye Mobile Trading Hub")
		self.assertEqual(composite_row_identity_value(item_row, "item_code"), "ITEM-002")
		self.assertEqual(composite_row_entity_code(customer_row), "Chan Aye Mobile Trading Hub")
		self.assertEqual(composite_row_entity_code(item_row), "ITEM-002")
		self.assertEqual(composite_join_key_label("customer"), "customer")
		self.assertEqual(composite_join_key_label("item"), "item_code")


if __name__ == "__main__":
	unittest.main()
