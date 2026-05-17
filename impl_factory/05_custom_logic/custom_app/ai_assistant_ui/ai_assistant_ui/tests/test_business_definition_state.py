import unittest

from ai_assistant_ui.qwen_chat.business_definition_state import (
	normalize_blocked_vs_active_resolution_state,
	resolve_business_definition_state,
	resolve_governed_formula_state,
)


def _definition_payload():
	return {
		"definitions": [
			{
				"definition_id": "aov_sales_order",
				"label": "Average Order Value Sales Order",
				"owner": "sales_ops",
				"company_scope": ["global"],
				"entity_grain": "company",
				"time_basis": "period_range",
				"semantic_category": "sales_efficiency",
				"activation_state": "active",
				"source_of_truth": {"kind": "sales_order"},
				"clarify_policy": "clarify_document_basis",
				"lookup_terms": ["sales order aov"],
			},
			{
				"definition_id": "credit_utilization",
				"label": "Customer Credit Utilization",
				"owner": "finance",
				"company_scope": ["Mingalar Mobile Distribution Co., Ltd."],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "credit_risk",
				"activation_state": "blocked_missing_policy",
				"source_of_truth": {"kind": "accounts_receivable_aging"},
				"clarify_policy": "clarify_basis",
				"blocked_reason": "credit utilization formula basis not yet approved",
				"lookup_terms": ["credit utilization"],
			},
			{
				"definition_id": "customer_tenure_created",
				"label": "Customer Tenure By Customer Creation",
				"owner": "finance",
				"company_scope": ["global"],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "customer_lifecycle",
				"activation_state": "draft_unapproved",
				"source_of_truth": {"kind": "customer"},
				"clarify_policy": "clarify_basis",
				"blocked_reason": "generic tenure basis is not approved",
				"lookup_terms": ["tenure", "customer tenure"],
			},
			{
				"definition_id": "customer_tenure_first_invoice",
				"label": "Customer Tenure By First Invoice",
				"owner": "finance",
				"company_scope": ["global"],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "customer_lifecycle",
				"activation_state": "active",
				"source_of_truth": {"kind": "sales_invoice"},
				"clarify_policy": "clarify_basis",
				"lookup_terms": ["tenure", "customer tenure"],
			},
		]
	}


def _formula_payload():
	return {
		"formulas": [
			{
				"formula_id": "aov_sales_order_sum_div_count",
				"definition_id": "aov_sales_order",
				"label": "AOV Sales Order Formula",
				"formula_type": "ratio",
				"input_metrics": ["grand_total", "document_count"],
				"input_requirements": [
					{"metric_key": "grand_total", "requirement_type": "required"},
					{"metric_key": "document_count", "requirement_type": "required"},
				],
				"source_capabilities": ["sales_order_listing"],
				"source_reports": ["Sales Order List"],
				"aggregation_rule": "ratio_of_sums",
				"grain_requirements": ["company"],
				"time_scope_requirements": ["period_required"],
				"activation_state": "active",
			},
			{
				"formula_id": "aov_sales_order_alt_variant",
				"definition_id": "aov_sales_order",
				"label": "AOV Sales Order Alternate Formula",
				"formula_type": "ratio",
				"input_metrics": ["net_total", "document_count"],
				"input_requirements": [
					{"metric_key": "net_total", "requirement_type": "required"},
					{"metric_key": "document_count", "requirement_type": "required"},
				],
				"source_capabilities": ["sales_order_listing"],
				"source_reports": ["Sales Order List"],
				"aggregation_rule": "ratio_of_sums",
				"grain_requirements": ["company"],
				"time_scope_requirements": ["period_required"],
				"activation_state": "draft_unapproved",
				"blocked_reason": "awaiting formula selection approval",
			},
			{
				"formula_id": "credit_utilization_outstanding_vs_limit",
				"definition_id": "credit_utilization",
				"label": "Credit Utilization Outstanding Vs Limit",
				"formula_type": "ratio",
				"input_metrics": ["outstanding_amount", "credit_limit"],
				"input_requirements": [
					{"metric_key": "outstanding_amount", "requirement_type": "required"},
					{"metric_key": "credit_limit", "requirement_type": "required"},
				],
				"source_capabilities": ["customer_credit_status"],
				"source_reports": ["Accounts Receivable Aging"],
				"aggregation_rule": "ratio_of_sums",
				"grain_requirements": ["customer"],
				"time_scope_requirements": ["as_of_date_required"],
				"activation_state": "active",
			},
		]
	}


class TestBusinessDefinitionState(unittest.TestCase):
	def test_normalize_blocked_vs_active_resolution_state(self):
		self.assertEqual(normalize_blocked_vs_active_resolution_state("active"), "active")
		self.assertEqual(
			normalize_blocked_vs_active_resolution_state("blocked_missing_policy"),
			"blocked",
		)
		self.assertEqual(
			normalize_blocked_vs_active_resolution_state("active", in_scope=False),
			"blocked",
		)

	def test_resolve_business_definition_state_returns_active_match(self):
		result = resolve_business_definition_state(
			"aov_sales_order",
			lookup_mode="definition_id",
			registry_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "active")
		self.assertEqual(result.definition_id, "aov_sales_order")
		self.assertEqual(result.activation_state, "active")

	def test_resolve_business_definition_state_returns_blocked_for_inactive_definition(self):
		result = resolve_business_definition_state(
			"credit utilization",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
			registry_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "blocked")
		self.assertEqual(result.definition_id, "credit_utilization")
		self.assertEqual(result.blocked_reason, "credit utilization formula basis not yet approved")

	def test_resolve_business_definition_state_returns_undefined_for_missing_lookup(self):
		result = resolve_business_definition_state(
			"gross margin",
			lookup_mode="lookup_term",
			registry_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "undefined")
		self.assertEqual(result.match_count, 0)

	def test_resolve_business_definition_state_returns_ambiguous_for_shared_lookup_term(self):
		result = resolve_business_definition_state(
			"tenure",
			lookup_mode="lookup_term",
			registry_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "ambiguous")
		self.assertEqual(set(result.matched_definition_ids), {"customer_tenure_created", "customer_tenure_first_invoice"})

	def test_resolve_governed_formula_state_returns_active_for_single_formula(self):
		definition_state = resolve_business_definition_state(
			"aov_sales_order",
			lookup_mode="definition_id",
			registry_payload=_definition_payload(),
		)
		result = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_lookup_value="aov_sales_order_sum_div_count",
			lookup_mode="formula_id",
			formula_registry_payload=_formula_payload(),
			business_definition_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "active")
		self.assertEqual(result.formula_id, "aov_sales_order_sum_div_count")

	def test_resolve_governed_formula_state_blocks_when_parent_definition_is_not_active(self):
		definition_state = resolve_business_definition_state(
			"credit utilization",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
			registry_payload=_definition_payload(),
		)
		result = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_registry_payload=_formula_payload(),
			business_definition_payload=_definition_payload(),
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(result.resolution_state, "blocked")
		self.assertEqual(result.blocked_reason, "credit utilization formula basis not yet approved")

	def test_resolve_governed_formula_state_returns_ambiguous_when_definition_has_multiple_formulas(self):
		definition_state = resolve_business_definition_state(
			"aov_sales_order",
			lookup_mode="definition_id",
			registry_payload=_definition_payload(),
		)
		result = resolve_governed_formula_state(
			definition_state=definition_state,
			formula_registry_payload=_formula_payload(),
			business_definition_payload=_definition_payload(),
		)
		self.assertEqual(result.resolution_state, "ambiguous")
		self.assertEqual(
			set(result.matched_formula_ids),
			{"aov_sales_order_sum_div_count", "aov_sales_order_alt_variant"},
		)

	def test_current_registry_average_order_value_is_ambiguous_without_document_basis(self):
		result = resolve_business_definition_state(
			"average order value",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(result.resolution_state, "ambiguous")
		self.assertEqual(
			set(result.matched_definition_ids),
			{
				"average_order_value_sales_order_period",
				"average_order_value_sales_invoice_period",
			},
		)

	def test_current_registry_collection_ratio_is_active(self):
		result = resolve_business_definition_state(
			"collection ratio",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(result.resolution_state, "active")
		self.assertEqual(result.definition_id, "collection_ratio_sales_invoice_period")
		self.assertEqual(result.activation_state, "active")

	def test_current_registry_customer_created_tenure_is_active(self):
		result = resolve_business_definition_state(
			"customer tenure by customer created date",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(result.resolution_state, "active")
		self.assertEqual(result.definition_id, "customer_tenure_customer_created_at")

	def test_current_registry_credit_utilization_definition_and_formula_are_active(self):
		definition_state = resolve_business_definition_state(
			"credit utilization",
			lookup_mode="lookup_term",
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(definition_state.resolution_state, "active")
		self.assertEqual(definition_state.definition_id, "credit_utilization_customer_as_of_date")
		formula_state = resolve_governed_formula_state(
			definition_state=definition_state,
			company_name="Mingalar Mobile Distribution Co., Ltd.",
		)
		self.assertEqual(formula_state.resolution_state, "active")
		self.assertEqual(formula_state.formula_id, "credit_utilization_customer_as_of_date_formula")
