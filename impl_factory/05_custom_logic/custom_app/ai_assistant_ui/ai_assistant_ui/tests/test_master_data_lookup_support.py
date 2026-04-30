import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.master_data_lookup_support import (
	extract_lookup_search_text,
	infer_lookup_mode_from_message,
	infer_master_data_lookup_slots,
	normalize_master_data_lookup_slots,
)


class MasterDataLookupSupportTests(unittest.TestCase):
	def test_infer_lookup_mode_detects_directory_list_for_plural_show_me(self) -> None:
		with patch(
			"ai_assistant_ui.qwen_chat.master_data_lookup_support.slot_alias_matches",
			side_effect=lambda slot_name, message: ["customer"] if slot_name == "entity_grain" else [],
		), patch(
			"ai_assistant_ui.qwen_chat.master_data_lookup_support.canonical_scope_aliases_for_entity_grain",
			return_value=["customer master list", "customer directory"],
		):
			self.assertEqual(infer_lookup_mode_from_message("show me customers"), "directory_list")

	def test_extract_lookup_search_text_prefers_quoted_value(self) -> None:
		self.assertEqual(
			extract_lookup_search_text('do u have customer name similar to "Nay Lin Mobile"?', "candidate_resolution"),
			"Nay Lin Mobile",
		)

	def test_normalize_master_data_lookup_slots_prefers_preferred_slots(self) -> None:
		with patch(
			"ai_assistant_ui.qwen_chat.master_data_lookup_support.get_entity_reference_policy_spec",
			return_value={"default_projection": "names_only", "default_limit": 10},
		), patch(
			"ai_assistant_ui.qwen_chat.master_data_lookup_support.infer_lookup_mode_from_message",
			return_value="candidate_resolution",
		), patch(
			"ai_assistant_ui.qwen_chat.master_data_lookup_support.extract_lookup_search_text",
			return_value="Ko Nay Lin Mobile",
		):
			slots = normalize_master_data_lookup_slots(
				message="tell me more about that customer",
				entity_grain="customer",
				preferred_slots={"lookup_mode": "profile_target", "lookup_search_text": "Ko Nay Lin Mobile Center"},
			)
		self.assertEqual(slots["lookup_mode"], "profile_target")
		self.assertEqual(slots["lookup_search_text"], "Ko Nay Lin Mobile Center")
		self.assertEqual(slots["lookup_limit"], 10)


if __name__ == "__main__":
	unittest.main()
