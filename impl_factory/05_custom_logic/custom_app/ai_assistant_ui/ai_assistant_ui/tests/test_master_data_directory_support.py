import unittest

from ai_assistant_ui.qwen_chat.master_data_directory_support import (
	master_directory_context,
	master_directory_requested_column_alias_map,
	requested_master_directory_columns,
)


class MasterDataDirectorySupportTests(unittest.TestCase):
	def test_master_directory_context_maps_supplier_and_customer_reports(self) -> None:
		supplier_context = master_directory_context("Supplier Master List")
		customer_context = master_directory_context("Customer Master List")
		self.assertEqual(supplier_context["entity_type"], "supplier")
		self.assertEqual(supplier_context["source_grain"], "supplier_master_list")
		self.assertEqual(customer_context["entity_type"], "customer")
		self.assertEqual(customer_context["source_grain"], "customer_master_list")

	def test_requested_master_directory_columns_remain_neutral(self) -> None:
		self.assertEqual(
			requested_master_directory_columns(
				requested_dimensions={"customer", "territory", "status"},
				lookup_projection="",
				entity_type="customer",
			),
			["entity", "region", "status"],
		)
		self.assertEqual(
			requested_master_directory_columns(
				requested_dimensions={"supplier", "country", "supplier_group", "payment_terms"},
				lookup_projection="",
				entity_type="supplier",
			),
			["entity", "region", "group", "payment_terms"],
		)

	def test_master_directory_alias_map_adds_entity_specific_deictic_aliases(self) -> None:
		item_aliases = master_directory_requested_column_alias_map("item")
		customer_aliases = master_directory_requested_column_alias_map("customer")
		self.assertEqual(item_aliases["that_product"], "entity")
		self.assertEqual(item_aliases["that_item"], "entity")
		self.assertEqual(customer_aliases["that_customer"], "entity")


if __name__ == "__main__":
	unittest.main()
