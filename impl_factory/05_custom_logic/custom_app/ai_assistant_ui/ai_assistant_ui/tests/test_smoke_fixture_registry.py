import unittest

from ai_assistant_ui.qwen_chat.smoke_fixtures import (
	smoke_fixture_action_message,
	smoke_fixture_reasoning_message,
	smoke_fixture_replacement_message,
)
from ai_assistant_ui.qwen_chat.smoke_fixture_registry import (
	validate_smoke_fixture_registry,
)


class TestSmokeFixtureRegistry(unittest.TestCase):
	def test_registry_passes_validation(self):
		result = validate_smoke_fixture_registry()
		self.assertEqual(result.status, "pass", result.errors)
		self.assertEqual(result.errors, [])
		self.assertGreaterEqual(result.stats.get("fixture_count", 0), 2)

	def test_registry_rejects_duplicate_fixture_ids(self):
		result = validate_smoke_fixture_registry(
			{
				"contract_version": "1.0",
				"fixtures": [
					{
						"fixture_id": "duplicate",
						"fixture_family": "post_contract_live_smoke",
						"initial_message": "first",
						"followup_messages": ["next"],
						"expected_initial_source_name": "Sales Analytics",
						"expected_family_id": "ranking_analytics",
					},
					{
						"fixture_id": "duplicate",
						"fixture_family": "post_contract_live_smoke",
						"initial_message": "second",
						"replacement_message": "replacement",
						"expected_initial_source_name": "Sales Analytics",
						"expected_replacement_source_names": ["Accounts Receivable Summary"],
					},
				],
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(any("duplicate fixture_id" in error for error in result.errors), result.errors)

	def test_registry_requires_replacement_sources_for_replacement_message(self):
		result = validate_smoke_fixture_registry(
			{
				"contract_version": "1.0",
				"fixtures": [
					{
						"fixture_id": "fresh_query",
						"fixture_family": "post_contract_live_smoke",
						"initial_message": "first",
						"replacement_message": "replacement",
						"expected_initial_source_name": "Sales Analytics",
					}
				],
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("expected_replacement_source_names" in error for error in result.errors),
			result.errors,
		)

	def test_registry_accepts_action_messages_fixture(self):
		result = validate_smoke_fixture_registry(
			{
				"contract_version": "1.0",
				"fixtures": [
					{
						"fixture_id": "product_recovery_flow",
						"fixture_family": "post_contract_live_smoke",
						"fixture_kind": "recovery_flow",
						"initial_message": "Top 7 products by revenue last month",
						"expected_initial_source_name": "Gross Profit",
						"expected_family_id": "ranking_analytics",
						"action_messages": {
							"guidance": "how do I ask for qty",
							"accept_governed_alternative": "yes please run the governed alternative",
						},
					}
				],
			}
		)
		self.assertEqual(result.status, "pass", result.errors)

	def test_registry_requires_expected_family_for_action_messages(self):
		result = validate_smoke_fixture_registry(
			{
				"contract_version": "1.0",
				"fixtures": [
					{
						"fixture_id": "product_recovery_flow",
						"fixture_family": "post_contract_live_smoke",
						"initial_message": "Top 7 products by revenue last month",
						"expected_initial_source_name": "Gross Profit",
						"action_messages": {
							"guidance": "how do I ask for qty",
						},
					}
				],
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(any("expected_family_id" in error for error in result.errors), result.errors)

	def test_registry_accepts_interaction_actions_fixture_without_initial_message(self):
		result = validate_smoke_fixture_registry(
			{
				"contract_version": "1.0",
				"fixtures": [
					{
						"fixture_id": "recovery_interaction_defaults",
						"fixture_family": "post_contract_live_smoke",
						"fixture_kind": "interaction_actions",
						"action_messages": {
							"guidance": "how do I ask for qty",
							"fresh_override_to_ar": "forget that, give me AR insight",
						},
					}
				],
			}
		)
		self.assertEqual(result.status, "pass", result.errors)

	def test_fixture_helpers_read_governed_messages(self):
		self.assertEqual(
			smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			"show accounts receivable summary as of today",
		)
		self.assertEqual(
			smoke_fixture_reasoning_message("fresh_query_override_to_ar"),
			"what does this mean",
		)
		self.assertEqual(
			smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			"explain this accounts receivable summary",
		)
		self.assertEqual(
			smoke_fixture_action_message("recovery_interaction_defaults", "guidance"),
			"how do I ask for qty",
		)
