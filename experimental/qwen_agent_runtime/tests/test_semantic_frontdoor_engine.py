from __future__ import annotations

import unittest

from app.schemas import FrontDoorInterpretRequest
from app.semantic_frontdoor_engine import _canonicalize_interpretation_obj, _system_prompt


class TestSemanticFrontDoorEngine(unittest.TestCase):
	def _request(self, message: str) -> FrontDoorInterpretRequest:
		return FrontDoorInterpretRequest(
			request_id="frontdoor-engine-test",
			session_id="sess-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			message=message,
			interpretation_context={
				"intent_classes": [
					{"intent_class_id": "route_onward"},
					{"intent_class_id": "greeting"},
				],
				"active_master_data_entity_grains": ["customer", "supplier"],
				"active_master_data_lookup_modes": ["directory_list", "candidate_resolution", "profile_target"],
				"active_master_data_lookup_projections": ["names_only"],
			},
		)

	def test_system_prompt_requires_master_data_slot_contract(self):
		prompt = _system_prompt()
		self.assertIn("extracted_slots", prompt)
		self.assertIn("entity_grain", prompt)
		self.assertIn("lookup_mode", prompt)
		self.assertIn("lookup_projection", prompt)
		self.assertIn("lookup_search_text", prompt)

	def test_canonicalize_preserves_valid_master_data_slots(self):
		request = self._request("give me some supplier list")
		raw_obj = {
			"intent_class": "route_onward",
			"confidence": 0.91,
			"reason": "ERP lookup request.",
			"extracted_slots": {
				"entity_grain": "supplier",
				"lookup_mode": "directory_list",
				"lookup_projection": "names_only",
			},
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertEqual(
			canonical.get("extracted_slots"),
			{
				"entity_grain": "supplier",
				"lookup_mode": "directory_list",
				"lookup_projection": "names_only",
			},
		)

	def test_canonicalize_drops_invalid_master_data_slots(self):
		request = self._request("give me some names")
		raw_obj = {
			"intent_class": "route_onward",
			"confidence": 0.88,
			"reason": "ERP lookup request.",
			"extracted_slots": {
				"entity_grain": "item",
				"lookup_mode": "directory_list",
				"lookup_projection": "all_columns",
				"lookup_search_text": "Nay Lin Mobile",
			},
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertEqual(
			canonical.get("extracted_slots"),
			{
				"lookup_mode": "directory_list",
				"lookup_search_text": "Nay Lin Mobile",
			},
		)

	def test_canonicalize_clears_slots_for_non_route_onward(self):
		request = self._request("hello")
		raw_obj = {
			"intent_class": "greeting",
			"confidence": 0.99,
			"reason": "Greeting.",
			"extracted_slots": {
				"entity_grain": "supplier",
				"lookup_mode": "directory_list",
			},
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertEqual(canonical.get("extracted_slots"), {})


if __name__ == "__main__":
	unittest.main()
