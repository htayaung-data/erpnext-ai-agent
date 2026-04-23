import unittest

from ai_assistant_ui.qwen_chat.composite_artifact_state import (
	build_composite_governed_artifact_contract,
	resolve_composite_artifact_resolution,
	resolve_composite_family_resolution,
	run_composite_artifact_contract_probe,
)


class TestCompositeArtifactState(unittest.TestCase):
	def test_current_registry_resolves_customer_commercial_family(self):
		result = resolve_composite_family_resolution(
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			requested_primary_metric="revenue",
			requested_secondary_metrics=["quantity", "average_order_value"],
			requested_basis="sales_order",
			requested_period_start="2026-03-01",
			requested_period_end="2026-03-31",
		)
		self.assertEqual(result.status, "resolved_family")
		self.assertEqual(result.family_id, "customer_commercial_ranking")

	def test_current_registry_clarifies_missing_basis_inside_customer_family(self):
		result = resolve_composite_family_resolution(
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			requested_primary_metric="revenue",
			requested_secondary_metrics=["quantity", "average_order_value"],
			requested_period_start="2026-03-01",
			requested_period_end="2026-03-31",
		)
		self.assertEqual(result.status, "clarify_family_variation")
		self.assertIn("basis", result.missing_clarifications)

	def test_current_registry_blocks_unknown_metric_mix(self):
		result = resolve_composite_family_resolution(
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			requested_primary_metric="gross_margin",
			requested_secondary_metrics=["quantity"],
			requested_period_start="2026-03-01",
			requested_period_end="2026-03-31",
		)
		self.assertEqual(result.status, "blocked_no_governed_family")

	def test_current_registry_artifact_resolution_is_active_for_customer_commercial_rollout(self):
		family_resolution = resolve_composite_family_resolution(
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			requested_primary_metric="revenue",
			requested_secondary_metrics=["quantity", "average_order_value"],
			requested_basis="sales_order",
			requested_period_start="2026-03-01",
			requested_period_end="2026-03-31",
		)
		artifact_resolution = resolve_composite_artifact_resolution(
			family_resolution=family_resolution
		)
		self.assertEqual(artifact_resolution.status, "active_composite")
		self.assertEqual(
			artifact_resolution.composite_id,
			"customer_commercial_ranking_sales_order_composite",
		)

	def test_composite_artifact_contract_preserves_row_provenance_fields(self):
		artifact = build_composite_governed_artifact_contract(
			composite_id="customer_credit_overdue_composite",
			label="Customer Credit And Overdue Composite",
			composite_kind="risk_table",
			primary_metric_id="overdue_amount",
			secondary_metric_ids=["overdue_ratio", "credit_utilization"],
			entity_grain="customer",
			time_scope_type="as_of_date_required",
			scope={"company": "Mingalar Mobile Distribution Co., Ltd."},
			as_of_date="2026-04-10",
			row_count=1,
			rows=[
				{
					"customer": "Zegyo Mobile Supply House",
					"join_key": {"customer": "Zegyo Mobile Supply House"},
					"row_provenance": {
						"source_artifact_refs": [
							{"definition_id": "customer_overdue_ratio_as_of_date"},
							{"definition_id": "credit_utilization_customer_as_of_date"}
						]
					},
				}
			],
			source_artifact_refs=[
				{"definition_id": "customer_overdue_ratio_as_of_date"},
				{"definition_id": "credit_utilization_customer_as_of_date"}
			],
			compatibility_status="compatible",
			render_policy={"style": "business_table"},
		)
		payload = artifact.to_payload()
		self.assertEqual(payload.get("row_count"), 1)
		self.assertEqual(payload.get("source_document_count"), 0)
		self.assertEqual(payload.get("rows")[0].get("join_key", {}).get("customer"), "Zegyo Mobile Supply House")

	def test_contract_probe_reports_ok(self):
		probe = run_composite_artifact_contract_probe()
		self.assertTrue(probe.get("ok"), probe)
