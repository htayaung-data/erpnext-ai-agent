import unittest

from ai_assistant_ui.qwen_chat.business_definition_state import (
	build_business_definition_state_contract,
	build_governed_formula_state_contract,
	resolve_business_definition_state,
	resolve_governed_formula_state,
)
from ai_assistant_ui.qwen_chat.governed_kpi_execution_registry import (
	validate_governed_kpi_execution_registry,
)
from ai_assistant_ui.qwen_chat.governed_kpi_execution_state import (
	build_governed_kpi_value_artifact_contract,
	resolve_governed_kpi_execution_state,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_governed_kpi_execution_spec,
	list_governed_kpi_execution_specs_for_formula,
	load_governed_kpi_execution_registry,
)


class TestGovernedKpiExecutionState(unittest.TestCase):
	def test_current_execution_registry_validates_and_loader_accessors_are_copy_safe(self):
		result = validate_governed_kpi_execution_registry()
		self.assertEqual(result.status, "pass", f"Execution registry must validate cleanly: {result.errors!r}")
		self.assertEqual(result.stats.get("execution_count"), 24)
		self.assertEqual(result.stats.get("activation_counts", {}).get("active"), 24)

		payload = load_governed_kpi_execution_registry()
		baseline_count = len(payload.get("executions") or [])
		payload["executions"].append({"execution_id": "mutated"})
		self.assertEqual(len(load_governed_kpi_execution_registry().get("executions") or []), baseline_count)
		self.assertEqual(
			get_governed_kpi_execution_spec(
				"average_order_value_sales_order_period_company_scalar_execution"
			).get("activation_state"),
			"active",
		)
		self.assertEqual(
			len(
				list_governed_kpi_execution_specs_for_formula(
					"credit_utilization_customer_as_of_date_formula"
				)
			),
			2,
		)

	def test_execution_validator_rejects_shape_scope_mismatch(self):
		result = validate_governed_kpi_execution_registry(
			{
				"contract_version": "1.0",
				"status": "test",
				"description": "test",
				"allowed_activation_states": [
					"active",
					"blocked_missing_policy",
					"blocked_missing_data",
					"draft_unapproved",
					"deprecated",
				],
				"allowed_execution_shapes": ["company_period_scalar"],
				"allowed_scope_types": ["company", "customer"],
				"allowed_time_scope_types": ["period_required"],
				"allowed_source_modes": ["single_report"],
				"allowed_value_unit_types": ["currency"],
				"executions": [
					{
						"execution_id": "bad_execution",
						"definition_id": "average_order_value_sales_order_period",
						"formula_id": "average_order_value_sales_order_period_formula",
						"label": "Bad Execution",
						"execution_shape": "company_period_scalar",
						"scope_type": "customer",
						"time_scope_type": "period_required",
						"source_mode": "single_report",
						"source_capabilities": ["sales_order_read"],
						"source_reports": ["Sales Order List"],
						"supported_filters": ["company", "from_date", "to_date"],
						"required_dimensions": ["customer"],
						"value_unit_type": "currency",
						"value_metric_mapping": {"value_metric": "average_order_value"},
						"activation_state": "active",
						"blocked_reason": ""
					}
				]
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(
			any("scope_type must be 'company'" in message for message in result.errors),
			f"Expected execution-shape scope validation error, got: {result.errors!r}",
		)

	def test_current_registry_company_period_execution_resolves_active_value(self):
		company_name = "Mingalar Mobile Distribution Co., Ltd."
		definition_state = resolve_business_definition_state(
			"average order value sales order",
			lookup_mode="lookup_term",
			company_name=company_name,
		)
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value="average_order_value_sales_order_period_formula",
			lookup_mode="formula_id",
			company_name=company_name,
		)
		result = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape="company_period_scalar",
			company_name=company_name,
			requested_scope={"period_start": "2026-03-01", "period_end": "2026-03-31"},
		)
		self.assertEqual(result.resolution_state, "active_value")
		self.assertEqual(
			result.execution_id,
			"average_order_value_sales_order_period_company_scalar_execution",
		)
		self.assertEqual(result.value_unit_type, "currency")

	def test_current_registry_company_period_execution_clarifies_missing_period_scope(self):
		company_name = "Mingalar Mobile Distribution Co., Ltd."
		definition_state = resolve_business_definition_state(
			"average order value sales invoice",
			lookup_mode="lookup_term",
			company_name=company_name,
		)
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value="average_order_value_sales_invoice_period_formula",
			lookup_mode="formula_id",
			company_name=company_name,
		)
		result = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape="company_period_scalar",
			company_name=company_name,
			requested_scope={},
		)
		self.assertEqual(result.resolution_state, "clarify_scope")
		self.assertIn("explicit business period", result.reason)

	def test_current_registry_customer_ranking_execution_resolves_active_value(self):
		company_name = "Mingalar Mobile Distribution Co., Ltd."
		definition_state = resolve_business_definition_state(
			"credit utilization",
			lookup_mode="lookup_term",
			company_name=company_name,
		)
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value="credit_utilization_customer_as_of_date_formula",
			lookup_mode="formula_id",
			company_name=company_name,
		)
		result = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape="customer_as_of_ranking",
			company_name=company_name,
			requested_scope={"as_of_date": "2026-04-10"},
		)
		self.assertEqual(result.resolution_state, "active_value")
		self.assertEqual(result.scope_type, "customer_set")
		self.assertEqual(result.value_unit_type, "ratio")

	def test_execution_state_clarifies_basis_when_definition_is_not_active(self):
		definition_state = build_business_definition_state_contract(
			lookup_value="average order value",
			lookup_mode="lookup_term",
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			resolution_state="ambiguous",
			match_count=2,
			matched_definition_ids=[
				"average_order_value_sales_order_period",
				"average_order_value_sales_invoice_period",
			],
			reason="Multiple governed business definitions match the KPI.",
		)
		formula_state = build_governed_formula_state_contract(
			requested_definition_id="",
			lookup_value="",
			lookup_mode="definition_id",
			requested_company_name="Mingalar Mobile Distribution Co., Ltd.",
			resolution_state="undefined",
			reason="No formula was chosen because definition basis is ambiguous.",
		)
		result = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape="company_period_scalar",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
			requested_scope={"period_start": "2026-03-01", "period_end": "2026-03-31"},
		)
		self.assertEqual(result.resolution_state, "clarify_basis")

	def test_value_artifact_contract_normalizes_numeric_fields(self):
		company_name = "Mingalar Mobile Distribution Co., Ltd."
		definition_state = resolve_business_definition_state(
			"collection ratio",
			lookup_mode="lookup_term",
			company_name=company_name,
		)
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value="collection_ratio_sales_invoice_period_formula",
			lookup_mode="formula_id",
			company_name=company_name,
		)
		execution_state = resolve_governed_kpi_execution_state(
			definition_state=definition_state,
			formula_state=formula_state,
			execution_shape="company_period_scalar",
			company_name=company_name,
			requested_scope={"period_start": "2026-03-01", "period_end": "2026-03-31"},
		)
		artifact = build_governed_kpi_value_artifact_contract(
			execution_state=execution_state,
			entity_grain="company",
			scope={"company": company_name},
			period_start="2026-03-01",
			period_end="2026-03-31",
			value="0.82",
			numerator_label="Allocated Customer Receipt Amount",
			numerator_value="820000",
			denominator_label="Sales Invoice Grand Total",
			denominator_value="1000000",
			source_evidence=[{"report_name": "Sales Invoice List"}, {"report_name": "Payment Entry List"}],
		)
		self.assertEqual(artifact.status, "active_value")
		self.assertEqual(artifact.value, 0.82)
		self.assertEqual(artifact.numerator_value, 820000.0)
		self.assertEqual(artifact.denominator_value, 1000000.0)
		self.assertEqual(artifact.unit_type, "ratio")
