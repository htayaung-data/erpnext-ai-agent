import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_context_resolution import (
	resolve_nbu_context_reference,
)


def _risk_artifact():
	return {
		"artifact_id": "risk-artifact-1",
		"family_id": "customer_risk_as_of",
		"dimensions": {
			"entity_dimension": "customer",
			"source_composite_family_id": "customer_risk_as_of",
		},
		"sections": {
			"ranked_rows": [
				{
					"rank": 1,
					"entity": "35th Street Mobile Wholesale",
					"customer": "35th Street Mobile Wholesale",
					"overdue_amount": 60212000,
				},
				{
					"rank": 2,
					"entity": "Ko Nay Lin Mobile Center",
					"customer": "Ko Nay Lin Mobile Center",
					"overdue_amount": 37335000,
				},
			]
		},
	}


class NaturalBusinessUnderstandingContextResolutionTests(unittest.TestCase):
	def test_resolves_ranked_row_reference_from_current_artifact(self):
		payload = resolve_nbu_context_reference(
			raw_message="Explain rank 2 customer",
			candidate_payload={
				"target_reference": "rank_n",
				"target_entity": {"entity_type": "customer"},
			},
			current_artifact=_risk_artifact(),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "risk-artifact-1")
		self.assertEqual(payload["resolved_row_index"], 1)
		self.assertEqual(payload["resolved_rank"], 2)
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertEqual(payload["resolved_entity"]["entity_type"], "customer")

	def test_resolves_ordinal_visible_row_without_family_specific_logic(self):
		payload = resolve_nbu_context_reference(
			raw_message="who is in the second position?",
			candidate_payload={"target_reference": "current_artifact"},
			current_artifact={
				"artifact_id": "generic-table-1",
				"rows": [
					{"rank": 1, "supplier": "Sunflower Accessories Co."},
					{"rank": 2, "supplier": "Myanmar Tech Import Services"},
				],
			},
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Myanmar Tech Import Services")
		self.assertEqual(payload["resolved_entity"]["entity_type"], "supplier")

	def test_aging_party_rows_are_preferred_over_summary_rows_for_rank_reference(self):
		payload = resolve_nbu_context_reference(
			raw_message="who is in second position in the above table?",
			candidate_payload={"target_reference": "rank_n"},
			current_artifact={
				"artifact_id": "ar-aging-1",
				"family_id": "aging",
				"sections": {
					"summary": [
						{"label": "Outstanding Total", "amount": 790855000},
						{"label": "Total Amount Due", "amount": 724170000},
					],
					"parties": [
						{
							"party": "Capital Telecom (NPT)",
							"party_type": "Customer",
							"outstanding": 97309500,
						},
						{
							"party": "35th Street Mobile Wholesale",
							"party_type": "Customer",
							"outstanding": 84837000,
						},
					],
				},
			},
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_row_index"], 1)
		self.assertEqual(payload["resolved_entity"]["entity_label"], "35th Street Mobile Wholesale")
		self.assertEqual(payload["resolved_entity"]["entity_type"], "customer")

	def test_candidate_list_reference_requires_selection_when_ambiguous(self):
		payload = resolve_nbu_context_reference(
			raw_message="show me the list",
			candidate_payload={
				"target_reference": "candidate_list",
				"target_entity": {
					"possible_matches": [
						{"item_name": "Type-C Cable 2m Fast Charge", "item_code": "ACC-CBL-UGR-TC2M"},
						{"item_name": "Type-C Cable 1m Fast Charge", "item_code": "ACC-CBL-BAS-TC1M"},
					]
				},
			},
		).to_payload()

		self.assertEqual(payload["status"], "ambiguous")
		self.assertEqual(
			payload["ambiguity_options"],
			["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"],
		)

	def test_candidate_list_reference_resolves_selected_option(self):
		payload = resolve_nbu_context_reference(
			raw_message="choose the second one",
			candidate_payload={
				"target_reference": "candidate_list",
				"target_entity": {
					"possible_matches": [
						{"item_name": "Type-C Cable 2m Fast Charge", "item_code": "ACC-CBL-UGR-TC2M"},
						{"item_name": "Type-C Cable 1m Fast Charge", "item_code": "ACC-CBL-BAS-TC1M"},
					]
				},
			},
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_row_index"], 1)
		self.assertEqual(payload["resolved_entity"]["entity_key"], "ACC-CBL-BAS-TC1M")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Type-C Cable 1m Fast Charge")

	def test_out_of_range_reference_returns_professional_resolution_failure(self):
		payload = resolve_nbu_context_reference(
			raw_message="explain rank 9",
			candidate_payload={"target_reference": "rank_n"},
			current_artifact=_risk_artifact(),
		).to_payload()

		self.assertEqual(payload["status"], "out_of_range")
		self.assertIn("only 2 row", payload["reason"])
		self.assertEqual(
			payload["ambiguity_options"],
			["35th Street Mobile Wholesale", "Ko Nay Lin Mobile Center"],
		)

	def test_direct_target_entity_is_preserved_for_named_entity(self):
		payload = resolve_nbu_context_reference(
			raw_message="tell me more about Ko Nay Lin Mobile Center",
			candidate_payload={
				"target_reference": "named_entity",
				"target_entity": {
					"entity_type": "customer",
					"entity_key": "Ko Nay Lin Mobile Center",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
			current_artifact=_risk_artifact(),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertEqual(payload["resolved_row_index"], -1)

	def test_previous_artifact_reference_resolves_recent_focus_contract(self):
		payload = resolve_nbu_context_reference(
			raw_message="go back to the customer",
			candidate_payload={"target_reference": "previous_artifact"},
			recent_focus={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "customer-detail-1",
			},
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "customer-detail-1")
		self.assertEqual(payload["resolved_entity"]["entity_type"], "customer")
		self.assertEqual(payload["resolved_entity"]["focus_kind"], "entity")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Ko Nay Lin Mobile Center")


if __name__ == "__main__":
	unittest.main()
