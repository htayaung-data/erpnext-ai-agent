from __future__ import annotations

import unittest

from app.schemas import FreshQueryInterpretRequest
from app.semantic_fresh_query_engine import _canonicalize_interpretation_obj


class TestSemanticFreshQueryEngine(unittest.TestCase):
	def _request(self, message: str) -> FreshQueryInterpretRequest:
		return FreshQueryInterpretRequest(
			request_id="fresh-query-engine-test",
			session_id="sess-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			message=message,
			interpretation_context={
				"intent_classes": [
					{"intent_class_id": "trend_analysis", "semantic_tags": ["trend"]},
				],
				"capabilities": [
					{
						"capability_id": "sales_read",
						"intent_classes": ["trend_analysis"],
						"report_names": ["Sales Analytics"],
						"dimensions": ["Customer", "Territory", "Item"],
						"metrics": ["Value", "Sales Amount", "Quantity"],
					},
					{
						"capability_id": "fulfillment_read",
						"intent_classes": ["trend_analysis"],
						"report_names": ["Delivery Note Trends"],
						"dimensions": ["Customer", "Period"],
						"metrics": ["Delivered Amount", "Delivered Quantity"],
					},
				],
				"reports": [
					{
						"report_name": "Sales Analytics",
						"capability_ids": ["sales_read"],
						"supported_intent_classes": ["trend_analysis"],
						"supported_dimensions": ["Customer", "Territory", "Item"],
						"supported_metrics": ["Sales Amount", "Quantity"],
						"semantic_tags": ["sales", "trend"],
					},
					{
						"report_name": "Delivery Note Trends",
						"capability_ids": ["fulfillment_read"],
						"supported_intent_classes": ["trend_analysis"],
						"supported_dimensions": ["Customer", "Period"],
						"supported_metrics": ["Delivered Amount", "Delivered Quantity"],
						"semantic_tags": ["delivery", "fulfillment", "trend"],
					},
				],
				"slot_definitions": [
					{
						"slot_name": "time_scope",
						"allowed_values": [
							"current_period",
							"last_month",
							"last_year",
							"current_fiscal_year_to_date",
							"all_period",
							"as_of_today",
						],
					}
				],
				"alias_maps": {
					"time_scope": [
						{
							"canonical_value": "current_fiscal_year_to_date",
							"aliases": ["this fiscal year", "current fiscal year", "this year", "year to date"],
						},
						{
							"canonical_value": "last_year",
							"aliases": ["last year", "previous year", "prior year", "last fiscal year"],
						},
					]
				},
				"allowed_presentations": ["table_presentation"],
				"allowed_ambiguity_flags": ["missing_dimension", "missing_metric"],
			},
		)

	def test_canonicalize_reconciles_trend_scope_against_report_contract(self):
		request = self._request("show monthly delivery note trend by customer this fiscal year")
		raw_obj = {
			"intent_class": "trend_analysis",
			"candidate_capability_ids": ["sales_read"],
			"candidate_reports": ["Sales Analytics"],
			"requested_dimensions": ["Customer", "Monthly"],
			"requested_metrics": ["Delivered Quantity", "Delivered Amount"],
			"requested_time_scope": "this fiscal year",
			"requested_presentation": ["table_presentation"],
			"extracted_slots": {},
			"ambiguity_flags": ["missing_dimension", "missing_metric"],
			"ambiguity_reason": "Underspecified trend request.",
			"confidence": 0.7,
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertIsNotNone(canonical)
		self.assertEqual(canonical.get("candidate_capability_ids"), ["fulfillment_read"])
		self.assertEqual(canonical.get("candidate_reports"), ["Delivery Note Trends"])
		self.assertEqual(canonical.get("requested_dimensions"), ["Customer"])
		self.assertEqual(
			canonical.get("requested_metrics"),
			["Delivered Quantity", "Delivered Amount"],
		)
		self.assertEqual(canonical.get("requested_time_scope"), "current_fiscal_year_to_date")
		self.assertEqual(canonical.get("ambiguity_flags"), [])
		self.assertEqual(canonical.get("ambiguity_reason"), "")
		self.assertGreaterEqual(float(canonical.get("confidence") or 0.0), 0.82)

	def test_canonicalize_trend_defaults_use_selected_report_contract(self):
		request = self._request("show delivery note trend this fiscal year")
		raw_obj = {
			"intent_class": "trend_analysis",
			"candidate_capability_ids": ["fulfillment_read"],
			"candidate_reports": ["Delivery Note Trends"],
			"requested_dimensions": [],
			"requested_metrics": [],
			"requested_time_scope": "",
			"requested_presentation": ["table_presentation"],
			"extracted_slots": {},
			"ambiguity_flags": [],
			"ambiguity_reason": "",
			"confidence": 0.78,
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertIsNotNone(canonical)
		self.assertEqual(canonical.get("candidate_reports"), ["Delivery Note Trends"])
		self.assertEqual(canonical.get("requested_dimensions"), ["Customer"])
		self.assertEqual(canonical.get("requested_metrics"), ["Delivered Amount"])
		self.assertEqual(canonical.get("requested_time_scope"), "current_fiscal_year_to_date")
		self.assertEqual(canonical.get("ambiguity_flags"), [])
		self.assertEqual(canonical.get("ambiguity_reason"), "")
		self.assertGreaterEqual(float(canonical.get("confidence") or 0.0), 0.82)

	def test_canonicalize_prefers_report_semantic_affinity_over_stale_sales_metric_guess(self):
		request = self._request("show monthly delivery note trend by customer this fiscal year")
		raw_obj = {
			"intent_class": "trend_analysis",
			"candidate_capability_ids": ["sales_read"],
			"candidate_reports": ["Sales Analytics"],
			"requested_dimensions": ["Customer", "Monthly"],
			"requested_metrics": ["Sales Amount"],
			"requested_time_scope": "this fiscal year",
			"requested_presentation": ["table_presentation"],
			"extracted_slots": {},
			"ambiguity_flags": [],
			"ambiguity_reason": "",
			"confidence": 0.78,
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertIsNotNone(canonical)
		self.assertEqual(canonical.get("candidate_capability_ids"), ["fulfillment_read"])
		self.assertEqual(canonical.get("candidate_reports"), ["Delivery Note Trends"])
		self.assertEqual(canonical.get("requested_dimensions"), ["Customer"])
		self.assertEqual(canonical.get("requested_time_scope"), "current_fiscal_year_to_date")

	def test_canonicalize_preserves_last_year_scope_from_metadata_alias(self):
		request = self._request("show delivery note trend last year")
		raw_obj = {
			"intent_class": "trend_analysis",
			"candidate_capability_ids": ["fulfillment_read"],
			"candidate_reports": ["Delivery Note Trends"],
			"requested_dimensions": [],
			"requested_metrics": [],
			"requested_time_scope": "last year",
			"requested_presentation": ["table_presentation"],
			"extracted_slots": {},
			"ambiguity_flags": [],
			"ambiguity_reason": "",
			"confidence": 0.8,
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertIsNotNone(canonical)
		self.assertEqual(canonical.get("requested_time_scope"), "last_year")

	def test_canonicalize_infers_last_year_scope_from_message_alias(self):
		request = self._request("show delivery note trend last fiscal year")
		raw_obj = {
			"intent_class": "trend_analysis",
			"candidate_capability_ids": ["fulfillment_read"],
			"candidate_reports": ["Delivery Note Trends"],
			"requested_dimensions": [],
			"requested_metrics": [],
			"requested_time_scope": "",
			"requested_presentation": ["table_presentation"],
			"extracted_slots": {},
			"ambiguity_flags": [],
			"ambiguity_reason": "",
			"confidence": 0.8,
		}

		canonical = _canonicalize_interpretation_obj(raw_obj, request)

		self.assertIsNotNone(canonical)
		self.assertEqual(canonical.get("requested_time_scope"), "last_year")


if __name__ == "__main__":
	unittest.main()
