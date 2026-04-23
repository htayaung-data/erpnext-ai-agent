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
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import NormalizedFamilyArtifactContract
from ai_assistant_ui.qwen_chat.family_adapters import (
	_requested_metric_key_from_contract,
	build_normalized_family_artifact,
)
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response


class TestProfitabilityRankingContracts(unittest.TestCase):
	def test_margin_metric_alias_maps_to_gross_profit_percent(self):
		metric_key = _requested_metric_key_from_contract(
			{
				"capability_id": "product_performance_read",
				"requested_metrics": ["margin"],
			},
			["gross_profit", "gross_profit_percent", "sales_amount"],
			"gross_profit",
		)
		self.assertEqual(metric_key, "gross_profit_percent")

	def test_gross_profit_ranking_artifact_uses_percent_metric_for_margin_requests(self):
		outcome = build_normalized_family_artifact(
			request_id="ranking-margin-percent",
			compiler_contract={
				"request_id": "ranking-margin-percent",
				"capability_id": "product_performance_read",
				"selected_report": "Gross Profit",
				"requested_dimensions": ["Item Code"],
				"requested_metrics": ["margin"],
				"requested_time_scope": "",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Gross Profit",
							"filters": {
								"company": "Enterprise Co",
								"group_by": "Item Code",
							},
						},
						"output_obj": {
							"result": {
								"data": [
									{
										"item_code": "SPH-XMI-RN13-8/256",
										"item_name": "Xiaomi Redmi Note 13 (8GB 256GB)",
										"gross_profit": 1600000,
										"gross_profit_%": 19.7,
										"selling_amount": 8120000,
										"buying_amount": 6520000,
										"qty": 10,
									},
									{
										"item_code": "ACC-CHR-XMI-33W",
										"item_name": "Xiaomi Fast Charger 33W",
										"gross_profit": 585000,
										"gross_profit_%": 54.8,
										"selling_amount": 1067000,
										"buying_amount": 482000,
										"qty": 39,
									},
								]
							}
						},
					}
				]
			},
			intent_class="ranked_entities",
			preferred_family_id="ranking_analytics",
		)
		self.assertEqual(outcome.status, "adapted")
		self.assertEqual(outcome.artifact_contract.family_id, "ranking_analytics")
		self.assertEqual(outcome.artifact_contract.dimensions.get("primary_metric_key"), "gross_profit_percent")
		self.assertEqual(
			outcome.artifact_contract.dimensions.get("requested_columns"),
			["entity", "gross_profit_percent"],
		)

		rendered = render_normalized_family_response(
			request_id="ranking-margin-percent-render",
			artifact_contract=outcome.artifact_contract,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("Top 2 Items by Gross Profit %", answer_text)
		self.assertIn("| Rank | Item | Gross Profit % |", answer_text)
		self.assertNotIn("| Rank | Item | Gross Profit % | Gross Profit % |", answer_text)
		self.assertIn("| 1 | Xiaomi Fast Charger 33W | 54.8% |", answer_text)

	def test_ranking_renderer_dedupes_metric_projection_after_amount_normalization(self):
		artifact = NormalizedFamilyArtifactContract(
			request_id="ranking-duplicate-percent-columns",
			family_id="ranking_analytics",
			artifact_type="normalized_family_artifact",
			source_reports=["Gross Profit"],
			period={"from_date": "2026-04-01", "to_date": "2026-04-16"},
			filters={"company": "Enterprise Co"},
			dimensions={
				"entity_dimension": "Product",
				"primary_metric_key": "gross_profit_percent",
				"primary_metric_label": "Gross Profit Percent",
				"requested_columns": ["entity", "amount", "gross_profit_percent"],
			},
			metrics={},
			sections={
				"ranked_rows": [
					{
						"rank": 1,
						"entity_name": "Xiaomi Redmi Note 13 (8GB 256GB)",
						"gross_profit": 1600000,
						"gross_profit_percent": 19.7,
					}
				]
			},
			warnings=[],
		)
		rendered = render_normalized_family_response(
			request_id="ranking-duplicate-percent-columns-render",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Rank | Product | Gross Profit Percent |", answer_text)
		self.assertNotIn("| Rank | Product | Gross Profit Percent | Gross Profit Percent |", answer_text)


if __name__ == "__main__":
	unittest.main()
