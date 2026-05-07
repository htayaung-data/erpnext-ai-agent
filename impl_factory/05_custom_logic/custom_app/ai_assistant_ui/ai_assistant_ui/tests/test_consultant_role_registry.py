import unittest

from ai_assistant_ui.qwen_chat.consultant_role_registry import (
	consultant_business_role_for_context,
	consultant_role_registry,
)


class ConsultantRoleRegistryTests(unittest.TestCase):
	def test_registry_resolves_role_from_capability_metadata_first(self):
		role = consultant_business_role_for_context(
			family_id="unknown_family",
			capability_id="accounts_receivable_read",
			semantic_tags=[],
		)

		self.assertEqual(role, "collector")

	def test_registry_resolves_role_from_family_metadata(self):
		role = consultant_business_role_for_context(
			family_id="financial_statement",
			capability_id="",
			semantic_tags=[],
		)

		self.assertEqual(role, "controller")

	def test_registry_resolves_role_from_semantic_tags(self):
		role = consultant_business_role_for_context(
			family_id="unknown_family",
			capability_id="",
			semantic_tags=["inventory"],
		)

		self.assertEqual(role, "inventory_manager")

	def test_registry_fails_closed_to_business_consultant(self):
		role = consultant_business_role_for_context(
			family_id="unknown_family",
			capability_id="unknown_read",
			semantic_tags=["unknown_tag"],
		)

		self.assertEqual(role, "business_consultant")

	def test_registry_file_is_metadata_owned(self):
		registry = consultant_role_registry()

		self.assertEqual(registry["type"], "qwen_consultant_role_registry")
		self.assertIn("capability_roles", registry)
		self.assertIn("family_roles", registry)


if __name__ == "__main__":
	unittest.main()
