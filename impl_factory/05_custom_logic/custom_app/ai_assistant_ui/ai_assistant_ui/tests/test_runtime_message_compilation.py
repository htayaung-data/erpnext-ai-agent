import sys
import types
import unittest

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
if not hasattr(sys.modules.get("frappe"), "get_all"):
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat.runtime_message_compilation import (
	grounded_entity_reference,
	recent_focus_contextual_reference,
)


class RuntimeMessageCompilationTests(unittest.TestCase):
	def test_grounded_entity_reference_uses_ordinal_rank_for_ranked_artifact(self):
		reference = grounded_entity_reference(
			raw_message="tell me more about the second customer",
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Alpha Mobile", "rank": 1},
					{"entity_type": "customer", "name": "Beta Mobile", "rank": 2},
				]
			},
			artifact_payload={},
		)

		self.assertEqual(reference["entity_type"], "customer")
		self.assertEqual(reference["entity_key"], "Beta Mobile")
		self.assertEqual(reference["entity_label"], "Beta Mobile")

	def test_grounded_entity_reference_stays_empty_for_ambiguous_multi_entity_without_ordinal(self):
		reference = grounded_entity_reference(
			raw_message="tell me more about that customer",
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Alpha Mobile", "rank": 1},
					{"entity_type": "customer", "name": "Beta Mobile", "rank": 2},
				]
			},
			artifact_payload={},
		)

		self.assertEqual(reference, {})

	def test_recent_focus_contextual_reference_uses_ranked_grounded_turn_when_focus_is_report(self):
		reference = recent_focus_contextual_reference(
			raw_message="show details for rank 1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "customer",
			},
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Alpha Mobile", "rank": 1},
					{"entity_type": "customer", "name": "Beta Mobile", "rank": 2},
				]
			},
			artifact_payload={},
		)

		self.assertEqual(reference["entity_key"], "Alpha Mobile")


if __name__ == "__main__":
	unittest.main()
