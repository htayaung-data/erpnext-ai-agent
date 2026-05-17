import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_context_graph import (
	build_nbu_context_graph,
	list_nbu_context_graph_node_types,
	resolve_nbu_context_graph_reference,
	select_nbu_context_graph_artifact,
	validate_nbu_context_graph_contract,
)


def _ar_artifact():
	return {
		"artifact_id": "ar-aging-1",
		"title": "Accounts Receivable Aging",
		"family_id": "accounts_receivable_aging",
		"dimensions": {
			"entity_dimension": "customer",
			"source_composite_family_id": "accounts_receivable_aging",
		},
		"sections": {
			"top_customers": [
				{
					"rank": 1,
					"customer": "Capital Telecom (NPT)",
					"outstanding": 97309500,
					"overdue_amount": 35274500,
				},
				{
					"rank": 2,
					"customer": "35th Street Mobile Wholesale",
					"outstanding": 84837000,
					"overdue_amount": 58212000,
				},
			]
		},
	}


def _supplier_artifact():
	return {
		"artifact_id": "supplier-list-1",
		"title": "Supplier Master List",
		"family_id": "supplier_master",
		"rows": [
			{"rank": 1, "supplier": "Shan Yoma Electronics"},
			{"rank": 2, "supplier": "Shwe Taung Electronics Supply"},
		],
	}


def _product_detail_focus():
	return {
		"focus_kind": "entity",
		"focus_grain": "item",
		"focus_label": "Type-C Cable 2m Fast Charge",
		"focus_key": "ACC-CBL-UGR-TC2M",
		"source_request_id": "item-detail-1",
	}


class NaturalBusinessUnderstandingContextGraphTests(unittest.TestCase):
	def test_context_graph_contract_has_generic_node_types(self):
		validation = validate_nbu_context_graph_contract()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(validation["node_type_count"], 5)
		node_types = {row["node_type"] for row in list_nbu_context_graph_node_types()}
		self.assertIn("artifact", node_types)
		self.assertIn("entity", node_types)

	def test_builds_graph_from_current_and_previous_artifacts(self):
		graph = build_nbu_context_graph(
			current_artifact=_supplier_artifact(),
			previous_artifacts=[_ar_artifact()],
		)

		self.assertEqual(graph["artifact_count"], 2)
		self.assertEqual(graph["row_count"], 4)
		artifact_ids = {node["artifact_id"] for node in graph["artifact_nodes"]}
		self.assertEqual(artifact_ids, {"supplier-list-1", "ar-aging-1"})

	def test_selects_previous_ar_artifact_from_metadata_alias_not_phrase_patch(self):
		graph = build_nbu_context_graph(
			current_artifact=_supplier_artifact(),
			previous_artifacts=[_ar_artifact()],
		)
		artifact = select_nbu_context_graph_artifact(
			raw_message="who is in second position in the above AR table?",
			context_graph=graph,
			prefer_previous=True,
		)

		self.assertEqual(artifact["artifact_id"], "ar-aging-1")
		self.assertIn("ar", artifact["aliases"])

	def test_resolves_rank_reference_against_named_previous_artifact(self):
		payload = resolve_nbu_context_graph_reference(
			raw_message="who is in second position in the above AR table?",
			candidate_payload={"target_reference": "rank_n"},
			context_graph=build_nbu_context_graph(
				current_artifact=_supplier_artifact(),
				previous_artifacts=[_ar_artifact()],
			),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "ar-aging-1")
		self.assertEqual(payload["resolved_rank"], 2)
		self.assertEqual(payload["resolved_entity"]["entity_label"], "35th Street Mobile Wholesale")

	def test_above_table_without_named_artifact_stays_on_current_visible_table(self):
		payload = resolve_nbu_context_graph_reference(
			raw_message="who is in second position in the above table?",
			candidate_payload={"target_reference": "rank_n"},
			context_graph=build_nbu_context_graph(
				current_artifact=_ar_artifact(),
				previous_artifacts=[_supplier_artifact()],
			),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "ar-aging-1")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "35th Street Mobile Wholesale")

	def test_resolves_unqualified_rank_against_current_artifact(self):
		payload = resolve_nbu_context_graph_reference(
			raw_message="who is in second position?",
			candidate_payload={"target_reference": "rank_n"},
			context_graph=build_nbu_context_graph(
				current_artifact=_supplier_artifact(),
				previous_artifacts=[_ar_artifact()],
			),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "supplier-list-1")
		self.assertEqual(payload["resolved_entity"]["entity_label"], "Shwe Taung Electronics Supply")

	def test_resolves_deictic_product_from_recent_focus(self):
		payload = resolve_nbu_context_graph_reference(
			raw_message="how many stocks do we have for that product?",
			candidate_payload={"target_reference": "selected_entity"},
			context_graph=build_nbu_context_graph(
				current_artifact={},
				recent_focus=_product_detail_focus(),
			),
		).to_payload()

		self.assertEqual(payload["status"], "resolved")
		self.assertEqual(payload["resolved_artifact_id"], "item-detail-1")
		self.assertEqual(payload["resolved_entity"]["entity_key"], "ACC-CBL-UGR-TC2M")
		self.assertEqual(payload["resolved_entity"]["entity_type"], "item")

	def test_unclear_visible_customer_reference_returns_options_not_report_repeat(self):
		payload = resolve_nbu_context_graph_reference(
			raw_message="why is this customer risky?",
			candidate_payload={"target_reference": "unclear"},
			context_graph=build_nbu_context_graph(current_artifact=_ar_artifact()),
		).to_payload()

		self.assertEqual(payload["status"], "ambiguous")
		self.assertEqual(
			payload["ambiguity_options"],
			["Capital Telecom (NPT)", "35th Street Mobile Wholesale"],
		)

	def test_candidate_options_are_graph_nodes_for_future_disambiguation(self):
		graph = build_nbu_context_graph(
			candidate_payloads=[
				{
					"target_reference": "candidate_list",
					"target_entity": {
						"possible_matches": [
							{"item_name": "Type-C Cable 2m Fast Charge", "item_code": "ACC-CBL-UGR-TC2M"},
							{"item_name": "Type-C Cable 1m Fast Charge", "item_code": "ACC-CBL-BAS-TC1M"},
						]
					},
				}
			]
		)

		self.assertEqual(len(graph["candidate_option_nodes"]), 2)
		self.assertEqual(
			graph["candidate_option_nodes"][1]["entity"]["entity_label"],
			"Type-C Cable 1m Fast Charge",
		)


if __name__ == "__main__":
	unittest.main()
