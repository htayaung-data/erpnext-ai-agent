import sys
import types
import unittest
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2026",
				"year_start_date": "2026-01-01",
				"year_end_date": "2026-12-31",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	SemanticFreshQueryResult,
	_deterministic_family_surface_interpretation,
	_family_narrative_prefers_rendered_response,
	compile_from_fresh_query_message,
)
from ai_assistant_ui.qwen_chat.artifact_narrative import build_artifact_narrative_context
from ai_assistant_ui.qwen_chat.contracts import build_followup_resolution
from ai_assistant_ui.qwen_chat.metadata import (
	load_business_ontology,
	load_semantic_resolution_registry,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key


class TestCustomerCreditStatusContracts(unittest.TestCase):
	def test_customer_credit_status_metadata_binds_to_receivable_authority(self):
		registry = load_semantic_resolution_registry()
		alias_maps = registry.get("alias_maps") if isinstance(registry.get("alias_maps"), dict) else {}
		aging_aliases = alias_maps.get("aging_view") if isinstance(alias_maps.get("aging_view"), list) else []
		receivable_aliases = next(
			(
				item
				for item in aging_aliases
				if isinstance(item, dict) and str(item.get("canonical_value") or "").strip() == "receivable"
			),
			{},
		)
		self.assertIn("customer credit status", list(receivable_aliases.get("aliases") or []))
		self.assertIn("customer credit exposure", list(receivable_aliases.get("aliases") or []))

		ontology = load_business_ontology()
		concepts = ontology.get("concepts") if isinstance(ontology.get("concepts"), list) else []
		receivable_concept = next(
			(
				item
				for item in concepts
				if isinstance(item, dict) and str(item.get("concept_id") or "").strip() == "receivable"
			),
			{},
		)
		receivable_english = (
			(receivable_concept.get("aliases") or {}).get("en")
			if isinstance(receivable_concept.get("aliases"), dict)
			else []
		)
		self.assertIn("customer credit status", list(receivable_english or []))
		self.assertIn("credit exposure", list(receivable_english or []))

	def test_customer_credit_status_metric_aliases_include_overdue_and_credit_balance(self):
		self.assertEqual(
			get_canonical_key("overdue customers", capability_id="accounts_receivable_read", dimension_or_metric="metric"),
			"overdue_only",
		)
		self.assertEqual(
			get_canonical_key("credit balance", capability_id="accounts_receivable_read", dimension_or_metric="metric"),
			"credit_balance_only",
		)

	def test_customer_credit_policy_aliases_include_limit_and_terms(self):
		self.assertEqual(
			get_canonical_key("credit limit", capability_id="accounts_receivable_read", dimension_or_metric="metric"),
			"credit_limit_amount",
		)
		self.assertEqual(
			get_canonical_key("remaining credit", capability_id="accounts_receivable_read", dimension_or_metric="metric"),
			"credit_limit_available",
		)
		self.assertEqual(
			get_canonical_key("exceeded credit limit", capability_id="accounts_receivable_read", dimension_or_metric="metric"),
			"credit_limit_status",
		)
		self.assertEqual(
			get_canonical_key("payment terms", capability_id="accounts_receivable_read", dimension_or_metric="dimension"),
			"payment_terms_template",
		)
		self.assertEqual(
			get_canonical_key("default price list", capability_id="accounts_receivable_read", dimension_or_metric="dimension"),
			"default_price_list",
		)

	def test_deterministic_family_surface_interpretation_builds_customer_credit_route(self):
		outcome = _deterministic_family_surface_interpretation(
			request_id="customer-credit-det-1",
			session_id="customer-credit-det",
			message="show customer credit status as of today",
			confidence_threshold=0.8,
		)
		self.assertIsNotNone(outcome)
		self.assertEqual(outcome.intent_class, "aging_analysis")
		self.assertEqual(list(outcome.candidate_capability_ids), ["accounts_receivable_read"])
		self.assertEqual(list(outcome.candidate_reports), ["Accounts Receivable Summary"])
		self.assertEqual(outcome.requested_time_scope, "as_of_today")
		self.assertEqual(dict(outcome.extracted_slots), {"aging_view": "receivable"})

	def test_compile_from_fresh_query_message_recovers_customer_credit_status_via_deterministic_fallback(self):
		runtime_error = SemanticFreshQueryResult(
			status="runtime_error",
			confidence_threshold=0.72,
			runtime_error="provider timeout",
			agent_meta={},
		)
		with patch(
			"ai_assistant_ui.qwen_chat.fresh_query_interpreter.interpret_fresh_query_semantically",
			side_effect=[runtime_error, runtime_error],
		):
			pipeline = compile_from_fresh_query_message(
				session_id="customer-credit-fallback-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show customer credit status as of today",
			)
		semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
		compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
		compiled_request = pipeline.get("compiled_query_request") if isinstance(pipeline.get("compiled_query_request"), dict) else {}
		self.assertEqual(semantic_payload.get("status"), "semantic_resolution_applied")
		self.assertTrue(bool((semantic_payload.get("agent_meta") or {}).get("deterministic_surface_fallback")))
		self.assertEqual(compiler_payload.get("decision"), "execute")
		self.assertEqual(compiled_request.get("selected_report"), "Accounts Receivable Summary")

	def test_aging_rendering_surfaces_credit_useful_customer_exposure_columns(self):
		compiler_contract = {
			"request_id": "customer-credit-render-1",
			"capability_id": "accounts_receivable_read",
			"selected_report": "Accounts Receivable Summary",
			"requested_dimensions": ["Party", "Territory", "Customer Group"],
			"requested_metrics": ["Outstanding Amount", "Total Amount Due"],
			"requested_time_scope": "as_of_today",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Accounts Receivable Summary",
						"filters": {
							"company": "Enterprise Co",
							"report_date": "2026-04-09",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"party": "Pazundaung Mobile Distribution",
									"outstanding": 945000,
									"total_due": 945000,
									"future_amount": 0,
									"range1": 0,
									"range2": 945000,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"territory": "Yangon",
									"customer_group": "Wholesale",
									"currency": "MMK",
								},
								{
									"party": "Thaketa Mobile Exchange",
									"outstanding": -249000,
									"total_due": -249000,
									"future_amount": 0,
									"range1": 0,
									"range2": 0,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"territory": "Yangon",
									"customer_group": "Wholesale",
									"currency": "MMK",
								},
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="customer-credit-render-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="aging_analysis",
			preferred_family_id="aging",
		)
		self.assertEqual(outcome.status, "adapted")
		artifact = outcome.artifact_contract
		self.assertIsNotNone(artifact)
		rendered = render_normalized_family_response(
			request_id="customer-credit-render-1",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		top_customers_block = next(
			(
				block
				for block in blocks
				if isinstance(block, dict) and str(block.get("title") or "").strip() == "Top Customers"
			),
			{},
		)
		columns = list(top_customers_block.get("columns") or [])
		self.assertEqual(columns, ["Customer", "Outstanding", "Total Due", "Overdue (31+)"])
		rows = list(top_customers_block.get("rows") or [])
		self.assertTrue(any(isinstance(row, list) and row and row[0] == "Pazundaung Mobile Distribution" for row in rows))
		thaketa_row = next(
			(
				row
				for row in rows
				if isinstance(row, list) and row and row[0] == "Thaketa Mobile Exchange"
			),
			[],
		)
		self.assertTrue(thaketa_row)
		self.assertTrue(any("-" in str(cell or "") for cell in thaketa_row[1:]))

	def test_overdue_only_filters_to_overdue_customers(self):
		compiler_contract = {
			"request_id": "customer-credit-overdue-1",
			"capability_id": "accounts_receivable_read",
			"selected_report": "Accounts Receivable Summary",
			"requested_dimensions": ["Party"],
			"requested_metrics": ["overdue_only"],
			"requested_time_scope": "as_of_today",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Accounts Receivable Summary",
						"filters": {
							"company": "Enterprise Co",
							"report_date": "2026-04-09",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"party": "Overdue Customer",
									"outstanding": 500000,
									"total_due": 500000,
									"future_amount": 0,
									"range1": 0,
									"range2": 500000,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"currency": "MMK",
								},
								{
									"party": "Current Only Customer",
									"outstanding": 200000,
									"total_due": 200000,
									"future_amount": 0,
									"range1": 200000,
									"range2": 0,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"currency": "MMK",
								},
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="customer-credit-overdue-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="aging_analysis",
			preferred_family_id="aging",
		)
		self.assertEqual(outcome.status, "adapted")
		rendered = render_normalized_family_response(
			request_id="customer-credit-overdue-1",
			artifact_contract=outcome.artifact_contract,
		)
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		top_customers_block = next(
			(
				block
				for block in blocks
				if isinstance(block, dict) and str(block.get("title") or "").strip() == "Top Customers"
			),
			{},
		)
		rows = list(top_customers_block.get("rows") or [])
		self.assertTrue(any(isinstance(row, list) and row and row[0] == "Overdue Customer" for row in rows))
		self.assertFalse(any(isinstance(row, list) and row and row[0] == "Current Only Customer" for row in rows))

	def test_credit_balance_only_filters_to_negative_outstanding(self):
		compiler_contract = {
			"request_id": "customer-credit-negative-1",
			"capability_id": "accounts_receivable_read",
			"selected_report": "Accounts Receivable Summary",
			"requested_dimensions": ["Party"],
			"requested_metrics": ["credit_balance_only"],
			"requested_time_scope": "as_of_today",
		}
		runtime_payload = {
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {
						"report_name": "Accounts Receivable Summary",
						"filters": {
							"company": "Enterprise Co",
							"report_date": "2026-04-09",
						},
					},
					"output_obj": {
						"result": {
							"data": [
								{
									"party": "Negative Balance Customer",
									"outstanding": -120000,
									"total_due": -120000,
									"future_amount": 0,
									"range1": 0,
									"range2": 0,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"currency": "MMK",
								},
								{
									"party": "Positive Balance Customer",
									"outstanding": 220000,
									"total_due": 220000,
									"future_amount": 0,
									"range1": 220000,
									"range2": 0,
									"range3": 0,
									"range4": 0,
									"range5": 0,
									"currency": "MMK",
								},
							]
						}
					},
				}
			]
		}
		outcome = build_normalized_family_artifact(
			request_id="customer-credit-negative-1",
			compiler_contract=compiler_contract,
			runtime_payload=runtime_payload,
			intent_class="aging_analysis",
			preferred_family_id="aging",
		)
		self.assertEqual(outcome.status, "adapted")
		rendered = render_normalized_family_response(
			request_id="customer-credit-negative-1",
			artifact_contract=outcome.artifact_contract,
		)
		blocks = list((rendered.contract.to_payload() if rendered.contract is not None else {}).get("blocks") or [])
		top_customers_block = next(
			(
				block
				for block in blocks
				if isinstance(block, dict) and str(block.get("title") or "").strip() == "Top Customers"
			),
			{},
		)
		rows = list(top_customers_block.get("rows") or [])
		self.assertTrue(any(isinstance(row, list) and row and row[0] == "Negative Balance Customer" for row in rows))
		self.assertFalse(any(isinstance(row, list) and row and row[0] == "Positive Balance Customer" for row in rows))

	def test_artifact_narrative_context_tightens_customer_credit_exposure_to_facts_only(self):
		context = build_artifact_narrative_context(
			request_id="customer-credit-narrative-1",
			artifact_payload={
				"family_id": "aging",
				"source_reports": ["Accounts Receivable Summary"],
			},
			rendered_response_payload={
				"family_id": "aging",
				"title": "Accounts Receivable Aging as of 2026-04-09",
				"source_reports": ["Accounts Receivable Summary"],
				"blocks": [],
			},
			response_policy={
				"answer_style": "simple_factual",
				"direct_answer_first": True,
				"implication_allowed": False,
				"recommendation_allowed": False,
			},
			validation_payload={},
		)
		system_prompt = str(context.get("system_prompt") or "").strip().lower()
		self.assertIn("governed artifact", system_prompt)
		self.assertIn("do not infer causes", system_prompt)
		self.assertIn("chronic issues", system_prompt)
		self.assertIn("short-term delays", system_prompt)
		self.assertIn("credit limits", system_prompt)

	def test_aging_family_prefers_rendered_response_for_non_analysis_credit_reads(self):
		self.assertTrue(
			_family_narrative_prefers_rendered_response(
				family_id="aging",
				response_policy={
					"analysis_requested": False,
					"implication_allowed": False,
					"recommendation_allowed": False,
				},
			)
		)
		self.assertFalse(
			_family_narrative_prefers_rendered_response(
				family_id="aging",
				response_policy={
					"analysis_requested": True,
					"implication_allowed": True,
					"recommendation_allowed": False,
				},
			)
		)

	def test_customer_credit_exposure_reask_breaks_out_of_prior_as_of_today_context(self):
		semantic_intent = types.SimpleNamespace(
			requested_modes=[],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="semantic follow-up accepted governed customer credit re-ask",
		)
		resolution = build_followup_resolution(
			request_id="customer-credit-reask-1",
			message="show me customer credit exposure",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"source_name": "Accounts Receivable Summary",
				"date_range": {"report_date": "2026-04-09"},
				"filters": {"company": "Enterprise Co", "report_date": "2026-04-09"},
				"dimensions": ["customer"],
				"returned_schema": ["party", "outstanding", "total_due"],
			},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
			degraded_reason="",
		)
		self.assertEqual(resolution.mode, "new_query")
		self.assertTrue(resolution.self_contained)
		self.assertFalse(resolution.depends_on_grounded_turn)
		noisy_presentation_intent = types.SimpleNamespace(
			requested_modes=["bullet_presentation"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			self_contained=False,
			reason="semantic follow-up misclassified the re-ask as presentation-oriented",
		)
		noisy_resolution = build_followup_resolution(
			request_id="customer-credit-reask-2",
			message="show me customer credit exposure",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"source_name": "Accounts Receivable Summary",
				"date_range": {"report_date": "2026-04-09"},
				"filters": {"company": "Enterprise Co", "report_date": "2026-04-09"},
				"dimensions": ["customer"],
				"returned_schema": ["party", "outstanding", "total_due"],
			},
			semantic_intent=noisy_presentation_intent,
			allow_heuristic_fallback=False,
			degraded_reason="",
		)
		self.assertEqual(noisy_resolution.mode, "new_query")
		self.assertTrue(noisy_resolution.self_contained)
