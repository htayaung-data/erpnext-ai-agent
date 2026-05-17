import sys
import types
import unittest
from unittest.mock import patch

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
if not hasattr(sys.modules.get("frappe"), "get_all"):
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat.boundary_support import (
	grounded_artifact_direct_evidence_answer,
	grounded_artifact_evidence_boundary_answer,
)
from ai_assistant_ui.qwen_chat.business_reasoning_policy import (
	build_business_recommendation_execution_contract,
	build_business_reasoning_authority_policy_payload,
)
from ai_assistant_ui.qwen_chat.composite_evidence_support import (
	composite_ranked_row_evidence_boundary_answer,
	composite_ranked_row_direct_evidence_answer,
	composite_ranked_row_direct_evidence_rendered_payload,
)
from ai_assistant_ui.qwen_chat.contracts import build_followup_resolution_contract
from ai_assistant_ui.qwen_chat.evidence_response_support import (
	preserve_current_artifact_direct_evidence_followup_resolution,
)
from ai_assistant_ui.qwen_chat.reasoning_activation import build_reasoning_activation_contract
from ai_assistant_ui.qwen_chat.reasoning_execution import (
	build_reasoning_boundary_answer,
	execute_erp_business_reasoning,
)


def _risk_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": "risk-evidence-1",
		"family_id": "customer_entity_detail",
		"source_reports": ["Customer Risk As-Of"],
		"period": {"as_of_date": "2026-04-25"},
		"filters": {"composite_family_id": "customer_risk_as_of", "as_of_date": "2026-04-25"},
		"dimensions": {
			"entity_dimension": "Customer",
			"source_composite_family_id": "customer_risk_as_of",
			"source_composite_family_label": "Customer Risk As-Of",
			"source_composite_primary_metric_id": "overdue_amount",
			"source_composite_secondary_metric_ids": [
				"outstanding_amount",
				"overdue_ratio",
				"credit_utilization",
			],
		},
		"sections": {
			"ranked_rows": [
				{
					"rank": 1,
					"entity": "Ko Nay Lin Mobile Center",
					"customer": "Ko Nay Lin Mobile Center",
					"overdue_amount": 37335000.0,
					"outstanding_amount": 63125000.0,
					"overdue_ratio": 59.1,
					"credit_utilization": 0.842,
					"aging_buckets": [
						{"bucket": "<0", "amount": 0.0},
						{"bucket": "0-30", "amount": 23190000.0},
						{"bucket": "31-60", "amount": 17760000.0},
						{"bucket": "61-90", "amount": 4575000.0},
						{"bucket": "91-120", "amount": 0.0},
						{"bucket": "121-Above", "amount": 15000000.0},
					],
				},
				{
					"rank": 2,
					"entity": "Aung Aung Telecom",
					"customer": "Aung Aung Telecom",
					"overdue_amount": 21000000.0,
					"outstanding_amount": 42000000.0,
					"overdue_ratio": 50.0,
					"credit_utilization": 0.7,
				},
			]
		},
	}


def _sales_invoice_detail_payload():
	return {
		"ok": True,
		"tool_trace": [
			{
				"output_obj": {
					"result": {
						"data": [
							{
								"name": "SINV-2026-00042",
								"posting_date": "2026-05-01",
								"due_date": "2026-05-31",
								"customer": "Ko Nay Lin Mobile Center",
								"grand_total": "40,000,000",
								"outstanding_amount": "37,335,000",
								"status": "Overdue",
							}
						]
					}
				}
			}
		],
	}


class CompositeEvidenceSupportTests(unittest.TestCase):
	def test_composite_ranked_row_evidence_explains_selected_risk_row(self):
		answer = composite_ranked_row_direct_evidence_answer(
			raw_message="why is the first customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
		)

		self.assertIn("Ko Nay Lin Mobile Center", answer)
		self.assertIn("Customer Risk As-Of", answer)
		self.assertIn("Overdue Amount", answer)
		self.assertIn("37,335,000 MMK", answer)
		self.assertIn("84.2%", answer)
		self.assertIn("not a prediction", answer)

	def test_composite_ranked_row_uses_registered_invoice_detail_when_filters_are_proven(self):
		artifact = _risk_artifact()
		artifact["filters"]["company"] = "Mingalar Mobile Distribution Co., Ltd."
		with patch(
			"ai_assistant_ui.qwen_chat.source_detail_drilldown_execution.execute_governed_report",
			return_value=_sales_invoice_detail_payload(),
		) as execute:
			answer = composite_ranked_row_direct_evidence_answer(
				raw_message="why is the first customer risky?",
				artifact_payload=artifact,
				grounded_turn={
					"known_entities": [
						{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
						{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
					]
				},
			)

		self.assertIn("source-detail breakdown", answer)
		self.assertIn("Sales Invoice List", answer)
		self.assertIn("SINV-2026-00042", answer)
		self.assertIn("Due Date", answer)
		execute.assert_called_once()
		self.assertEqual(execute.call_args.kwargs["filters"]["customer"], "Ko Nay Lin Mobile Center")
		self.assertEqual(execute.call_args.kwargs["filters"]["to_date"], "2026-04-25")

	def test_composite_ranked_row_evidence_does_not_guess_ambiguous_multi_row_deictic(self):
		answer = composite_ranked_row_direct_evidence_answer(
			raw_message="why is this customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
		)

		self.assertEqual(answer, "")

	def test_composite_ranked_row_boundary_asks_for_row_on_ambiguous_multi_row_deictic(self):
		answer = composite_ranked_row_evidence_boundary_answer(
			raw_message="why is this customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
		)

		self.assertIn("Customer Risk As-Of", answer)
		self.assertIn("which customer or row", answer)
		self.assertIn("- Rank 1: Ko Nay Lin Mobile Center", answer)
		self.assertIn("- Rank 2: Aung Aung Telecom", answer)
		self.assertIn("explain rank 2", answer)

	def test_boundary_support_uses_composite_ranked_row_evidence(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="explain rank 2",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("Aung Aung Telecom", answer)
		self.assertIn("21,000,000 MMK", answer)

	def test_composite_ranked_row_evidence_explains_named_row(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="why is Aung Aung Telecom risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("Aung Aung Telecom", answer)
		self.assertIn("ranks #2", answer)
		self.assertIn("70%", answer)

	def test_composite_evidence_answers_selected_row_aging_breakdown_when_carried(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="show me the aging breakdown for the first customer",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("Ko Nay Lin Mobile Center aging breakdown", answer)
		self.assertIn("| Aging Bucket | Amount (MMK) |", answer)
		self.assertIn("| 31-60 | 17,760,000 |", answer)
		self.assertIn("Total due across displayed buckets: 60,525,000 MMK", answer)
		self.assertIn("Overdue beyond 30 days: 37,335,000 MMK", answer)
		self.assertIn("0-30 day bucket: 23,190,000 MMK", answer)
		self.assertIn("121+ day bucket: 15,000,000 MMK", answer)
		self.assertNotIn("No amounts are current", answer)
		self.assertIn("current result", answer)

	def test_composite_evidence_fails_closed_for_selected_row_aging_breakdown_without_buckets(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="show me the aging breakdown for rank 2",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
			evidence_request_contract={},
		)

		self.assertIn("Aung Aung Telecom", answer)
		self.assertIn("does not expose bucket-level aging amounts", answer)
		self.assertIn("won't fabricate", answer)

	def test_composite_evidence_does_not_capture_unrelated_context_switch(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="show me suppliers",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertEqual(answer, "")

	def test_composite_evidence_boundaries_blocked_collection_recommendation_with_evidence(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="who should we collect from first?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("does not authorize a collection recommendation", answer)
		self.assertIn("Rank 1: Ko Nay Lin Mobile Center", answer)
		self.assertIn("Overdue Amount: 37,335,000 MMK", answer)
		self.assertIn("Customer Collection Priority Policy", answer)
		self.assertIn("blocked_missing_policy", answer)
		self.assertIn("Recommendation execution gate", answer)
		self.assertIn("Production Execution Allowed: No", answer)
		self.assertIn("not a recommendation, prediction, score, or approval decision", answer)

	def test_collection_recommendation_boundary_carries_required_policy_artifact(self):
		payload = build_business_reasoning_authority_policy_payload(
			raw_message="who should we collect from first?",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(payload.get("policy_state"), "blocked")
		self.assertEqual(payload.get("requested_authority"), "recommendation")
		self.assertEqual(payload.get("blocked_variation"), "collection_recommendation")
		policy = payload.get("authority_policy") or {}
		self.assertEqual(policy.get("policy_artifact_id"), "customer_collection_priority_policy")
		self.assertEqual(policy.get("approval_state"), "blocked_missing_policy")
		self.assertIn("overdue_amount", list(policy.get("required_evidence_metrics") or []))
		self.assertIn("customer_payment_behavior_analysis", list(policy.get("required_governed_artifacts") or []))
		gate = payload.get("authority_policy_gate") or {}
		self.assertEqual(gate.get("gate_state"), "blocked_missing_policy")
		self.assertFalse(bool(gate.get("ready_to_recommend")))
		self.assertIn("customer_payment_behavior_analysis", list(gate.get("missing_governed_artifacts") or []))
		execution_contract = payload.get("recommendation_execution_contract") or {}
		self.assertEqual(execution_contract.get("type"), "qwen_business_recommendation_execution_contract")
		self.assertEqual(execution_contract.get("execution_state"), "blocked_missing_policy")
		self.assertFalse(bool(execution_contract.get("execution_allowed")))
		self.assertEqual(execution_contract.get("safe_response_mode"), "grounded_evidence_boundary")

	def test_collection_recommendation_gate_blocks_approved_policy_when_evidence_missing(self):
		family_spec = {
			"activation_state": "active",
			"label": "Customer Risk As-Of",
			"default_primary_metric": "overdue_amount",
			"default_secondary_metrics": ["outstanding_amount", "credit_utilization"],
			"blocked_variations": ["collection_recommendation"],
			"blocked_variation_aliases": {
				"collection_recommendation": ["who should we collect from first"]
			},
			"blocked_variation_labels": {
				"collection_recommendation": "collection recommendation"
			},
			"business_reasoning_authority_policies": {
				"collection_recommendation": {
					"policy_artifact_id": "customer_collection_priority_policy",
					"policy_artifact_label": "Customer Collection Priority Policy",
					"approval_state": "approved_active",
					"required_policy_state": "approved_active",
					"runtime_execution_state": "disabled_pending_policy_approval",
					"allowed_execution_modes": [],
					"recommendation_result_type": "ranked_collection_action",
					"required_evidence_metrics": ["overdue_amount", "payment_delay_days"],
					"required_governed_artifacts": ["customer_payment_behavior_analysis"],
				}
			},
		}
		with patch(
			"ai_assistant_ui.qwen_chat.business_reasoning_policy.get_composite_family_spec",
			return_value=family_spec,
		):
			payload = build_business_reasoning_authority_policy_payload(
				raw_message="who should we collect from first?",
				artifact_payload=_risk_artifact(),
				grounded_turn={},
			)

		gate = payload.get("authority_policy_gate") or {}
		self.assertEqual(gate.get("gate_state"), "blocked_missing_evidence")
		self.assertFalse(bool(gate.get("ready_to_recommend")))
		self.assertIn("payment_delay_days", list(gate.get("missing_evidence_metrics") or []))
		self.assertIn("customer_payment_behavior_analysis", list(gate.get("missing_governed_artifacts") or []))
		execution_contract = payload.get("recommendation_execution_contract") or {}
		self.assertEqual(execution_contract.get("execution_state"), "blocked_missing_evidence")
		self.assertFalse(bool(execution_contract.get("execution_allowed")))

	def test_collection_recommendation_gate_can_be_ready_without_enabling_runtime_recommendation(self):
		family_spec = {
			"activation_state": "active",
			"label": "Customer Risk As-Of",
			"default_primary_metric": "overdue_amount",
			"default_secondary_metrics": ["outstanding_amount", "credit_utilization"],
			"blocked_variations": ["collection_recommendation"],
			"blocked_variation_aliases": {
				"collection_recommendation": ["who should we collect from first"]
			},
			"blocked_variation_labels": {
				"collection_recommendation": "collection recommendation"
			},
			"business_reasoning_authority_policies": {
				"collection_recommendation": {
					"policy_artifact_id": "customer_collection_priority_policy",
					"policy_artifact_label": "Customer Collection Priority Policy",
					"approval_state": "approved_active",
					"required_policy_state": "approved_active",
					"runtime_execution_state": "disabled_pending_policy_approval",
					"allowed_execution_modes": [],
					"recommendation_result_type": "ranked_collection_action",
					"required_evidence_metrics": [
						"overdue_amount",
						"outstanding_amount",
						"credit_utilization",
						"aging_buckets",
					],
					"required_governed_artifacts": [
						"customer_risk_as_of",
						"accounts_receivable_aging",
						"customer_payment_behavior_analysis",
					],
				}
			},
		}
		artifact = _risk_artifact()
		artifact["supporting_governed_artifact_ids"] = [
			"accounts_receivable_aging",
			"customer_payment_behavior_analysis",
		]
		with patch(
			"ai_assistant_ui.qwen_chat.business_reasoning_policy.get_composite_family_spec",
			return_value=family_spec,
		):
			payload = build_business_reasoning_authority_policy_payload(
				raw_message="who should we collect from first?",
				artifact_payload=artifact,
				grounded_turn={},
			)

		self.assertEqual(payload.get("policy_state"), "blocked")
		gate = payload.get("authority_policy_gate") or {}
		self.assertEqual(gate.get("gate_state"), "ready")
		self.assertTrue(bool(gate.get("ready_to_recommend")))
		self.assertEqual(list(gate.get("missing_evidence_metrics") or []), [])
		self.assertEqual(list(gate.get("missing_governed_artifacts") or []), [])
		execution_contract = payload.get("recommendation_execution_contract") or {}
		self.assertEqual(execution_contract.get("execution_state"), "ready")
		self.assertTrue(bool(execution_contract.get("policy_gate_ready")))
		self.assertFalse(bool(execution_contract.get("runtime_execution_enabled")))
		self.assertFalse(bool(execution_contract.get("execution_allowed")))
		self.assertEqual(execution_contract.get("runtime_execution_state"), "disabled_pending_policy_approval")
		self.assertEqual(execution_contract.get("safe_response_mode"), "grounded_evidence_boundary")
		self.assertEqual(execution_contract.get("recommendation_result_type"), "ranked_collection_action")
		constraints = execution_contract.get("output_constraints") or {}
		self.assertTrue(bool(constraints.get("requires_ready_policy_gate")))
		self.assertTrue(bool(constraints.get("requires_runtime_execution_enabled")))
		self.assertIn("unsupported_causal_claim", list(constraints.get("must_not_include") or []))

	def test_collection_recommendation_contract_supports_explicit_dry_run_without_production_execution(self):
		family_spec = {
			"activation_state": "active",
			"label": "Customer Risk As-Of",
			"default_primary_metric": "overdue_amount",
			"default_secondary_metrics": ["outstanding_amount", "credit_utilization"],
			"blocked_variations": ["collection_recommendation"],
			"blocked_variation_aliases": {
				"collection_recommendation": ["who should we collect from first"]
			},
			"blocked_variation_labels": {
				"collection_recommendation": "collection recommendation"
			},
			"business_reasoning_authority_policies": {
				"collection_recommendation": {
					"policy_artifact_id": "customer_collection_priority_policy",
					"policy_artifact_label": "Customer Collection Priority Policy",
					"approval_state": "approved_active",
					"required_policy_state": "approved_active",
					"runtime_execution_state": "dry_run_only",
					"allowed_execution_modes": ["dry_run"],
					"recommendation_result_type": "ranked_collection_action",
					"required_evidence_metrics": [
						"overdue_amount",
						"outstanding_amount",
						"credit_utilization",
						"aging_buckets",
					],
					"required_governed_artifacts": [
						"customer_risk_as_of",
						"accounts_receivable_aging",
						"customer_payment_behavior_analysis",
					],
				}
			},
		}
		artifact = _risk_artifact()
		artifact["supporting_governed_artifact_ids"] = [
			"accounts_receivable_aging",
			"customer_payment_behavior_analysis",
		]
		with patch(
			"ai_assistant_ui.qwen_chat.business_reasoning_policy.get_composite_family_spec",
			return_value=family_spec,
		):
			payload = build_business_reasoning_authority_policy_payload(
				raw_message="who should we collect from first?",
				artifact_payload=artifact,
				grounded_turn={},
			)

		execution_contract = payload.get("recommendation_execution_contract") or {}
		self.assertEqual(execution_contract.get("execution_state"), "ready")
		self.assertTrue(bool(execution_contract.get("policy_gate_ready")))
		self.assertEqual(execution_contract.get("runtime_execution_state"), "dry_run_only")
		self.assertTrue(bool(execution_contract.get("dry_run_allowed")))
		self.assertFalse(bool(execution_contract.get("runtime_execution_enabled")))
		self.assertFalse(bool(execution_contract.get("execution_allowed")))

	def test_collection_recommendation_contract_allows_execution_only_when_runtime_enabled(self):
		family_spec = {
			"activation_state": "active",
			"label": "Customer Risk As-Of",
			"default_primary_metric": "overdue_amount",
			"default_secondary_metrics": ["outstanding_amount", "credit_utilization"],
			"blocked_variations": ["collection_recommendation"],
			"blocked_variation_aliases": {
				"collection_recommendation": ["who should we collect from first"]
			},
			"blocked_variation_labels": {
				"collection_recommendation": "collection recommendation"
			},
			"business_reasoning_authority_policies": {
				"collection_recommendation": {
					"policy_artifact_id": "customer_collection_priority_policy",
					"policy_artifact_label": "Customer Collection Priority Policy",
					"approval_state": "approved_active",
					"required_policy_state": "approved_active",
					"runtime_execution_state": "enabled_active",
					"allowed_execution_modes": ["production", "dry_run"],
					"recommendation_result_type": "ranked_collection_action",
					"required_evidence_metrics": [
						"overdue_amount",
						"outstanding_amount",
						"credit_utilization",
						"aging_buckets",
					],
					"required_governed_artifacts": [
						"customer_risk_as_of",
						"accounts_receivable_aging",
						"customer_payment_behavior_analysis",
					],
				}
			},
		}
		artifact = _risk_artifact()
		artifact["supporting_governed_artifact_ids"] = [
			"accounts_receivable_aging",
			"customer_payment_behavior_analysis",
		]
		with patch(
			"ai_assistant_ui.qwen_chat.business_reasoning_policy.get_composite_family_spec",
			return_value=family_spec,
		):
			payload = build_business_reasoning_authority_policy_payload(
				raw_message="who should we collect from first?",
				artifact_payload=artifact,
				grounded_turn={},
			)

		execution_contract = payload.get("recommendation_execution_contract") or {}
		self.assertEqual(execution_contract.get("execution_state"), "ready")
		self.assertTrue(bool(execution_contract.get("runtime_execution_enabled")))
		self.assertTrue(bool(execution_contract.get("execution_allowed")))
		self.assertEqual(execution_contract.get("safe_response_mode"), "recommendation_execution")

	def test_recommendation_execution_contract_helper_ignores_non_recommendation_requests(self):
		contract = build_business_recommendation_execution_contract(
			raw_message="what drives the first customer risk?",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(contract, {})

	def test_composite_evidence_boundaries_blocked_prediction_request(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="will the first customer default next month?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("does not authorize a predictive default probability", answer)
		self.assertIn("Rank 1: Ko Nay Lin Mobile Center", answer)
		self.assertIn("not a recommendation, prediction, score, or approval decision", answer)

	def test_composite_evidence_answers_current_artifact_driver_analysis(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="what drives the first customer risk?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("explainable drivers", answer)
		self.assertIn("Rank 1: Ko Nay Lin Mobile Center", answer)
		self.assertIn("Overdue Amount: 37,335,000 MMK", answer)
		self.assertIn("Outstanding Amount: 63,125,000 MMK", answer)
		self.assertIn("Credit Utilization: 84.2%", answer)
		self.assertIn("not causal, trend, payment-behavior", answer)

	def test_composite_evidence_boundaries_unsupported_causal_driver_analysis(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="what caused the first customer's risk to increase?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("does not authorize a causal root-cause driver analysis", answer)
		self.assertIn("Ask for a trend, payment-behavior, or transaction-history analysis view", answer)
		self.assertIn("Rank 1: Ko Nay Lin Mobile Center", answer)

	def test_boundary_support_uses_composite_multi_row_evidence_boundary(self):
		answer = grounded_artifact_evidence_boundary_answer(
			raw_message="why is this customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("which customer or row", answer)
		self.assertIn("Ko Nay Lin Mobile Center", answer)
		self.assertIn("Aung Aung Telecom", answer)
		self.assertIn("- Rank 1:", answer)

	def test_direct_evidence_wrapper_returns_composite_row_choice_prompt_without_recovery_boundary(self):
		answer = grounded_artifact_direct_evidence_answer(
			raw_message="why is this customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={
				"known_entities": [
					{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
					{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
				]
			},
			evidence_request_contract={},
		)

		self.assertIn("which customer or row", answer)
		self.assertIn("Ko Nay Lin Mobile Center", answer)
		self.assertIn("Aung Aung Telecom", answer)
		self.assertIn("- Rank 1:", answer)

	def test_boundary_support_does_not_block_selected_composite_row(self):
		answer = grounded_artifact_evidence_boundary_answer(
			raw_message="why is the first customer risky?",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
			evidence_request_contract={},
		)

		self.assertEqual(answer, "")

	def test_composite_ranked_row_rendered_payload_has_metric_table(self):
		payload = composite_ranked_row_direct_evidence_rendered_payload(
			raw_message="explain rank 1",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(payload.get("renderer_id"), "composite_ranked_row_direct_evidence")
		self.assertEqual(payload.get("rendering_policy"), "deterministic")
		self.assertEqual((payload.get("blocks") or [])[0].get("title"), "Current ERP Metrics")
		self.assertIn("not a prediction", payload.get("answer_text"))
		self.assertIn("37,335,000 MMK", payload.get("answer_text"))
		self.assertNotIn("37.34 MMK", payload.get("answer_text"))

	def test_composite_blocked_reasoning_boundary_payload_is_deterministic(self):
		payload = composite_ranked_row_direct_evidence_rendered_payload(
			raw_message="who should we collect from first?",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(payload.get("renderer_id"), "business_reasoning_authority_boundary")
		self.assertEqual(payload.get("rendering_policy"), "deterministic")
		self.assertIn("does not authorize a collection recommendation", payload.get("answer_text"))
		self.assertEqual((payload.get("blocks") or [])[0].get("title"), "Current ERP Facts")
		self.assertEqual((payload.get("blocks") or [])[1].get("title"), "Required Policy")
		self.assertEqual((payload.get("blocks") or [])[2].get("title"), "Recommendation Execution Gate")
		self.assertIn(["Production Execution Allowed", "No"], (payload.get("blocks") or [])[2].get("rows") or [])
		self.assertIn(["Runtime Execution State", "disabled_pending_policy_approval"], (payload.get("blocks") or [])[2].get("rows") or [])

	def test_composite_driver_analysis_payload_is_deterministic(self):
		payload = composite_ranked_row_direct_evidence_rendered_payload(
			raw_message="what are the key drivers for rank 1?",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(payload.get("renderer_id"), "business_reasoning_driver_analysis")
		self.assertEqual(payload.get("rendering_policy"), "deterministic")
		self.assertIn("current-result metric-driver analysis only", payload.get("answer_text"))
		self.assertEqual((payload.get("blocks") or [])[0].get("title"), "Driver Evidence")

	def test_phase_3_5_customer_risk_reasoning_boundary_matrix_is_locked(self):
		artifact = _risk_artifact()
		grounded_turn = {
			"known_entities": [
				{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 1},
				{"entity_type": "customer", "name": "Aung Aung Telecom", "rank": 2},
			]
		}
		matrix = [
			(
				"why is the first customer risky?",
				[
					"Ko Nay Lin Mobile Center",
					"ranks #1",
					"Overdue Amount: 37,335,000 MMK",
					"not a prediction",
				],
				["does not authorize"],
			),
			(
				"what drives the first customer risk?",
				[
					"explainable drivers",
					"Rank 1: Ko Nay Lin Mobile Center",
					"current-result metric-driver analysis only",
				],
				["does not authorize"],
			),
			(
				"what caused the first customer's risk to increase?",
				[
					"does not authorize a causal root-cause driver analysis",
					"Ask for a trend, payment-behavior, or transaction-history analysis view",
					"Rank 1: Ko Nay Lin Mobile Center",
				],
				[],
			),
			(
				"will the first customer default next month?",
				[
					"does not authorize a predictive default probability",
					"Rank 1: Ko Nay Lin Mobile Center",
					"not a recommendation, prediction, score, or approval decision",
				],
				[],
			),
			(
				"who should we collect from first?",
				[
					"does not authorize a collection recommendation",
					"Customer Collection Priority Policy",
					"Recommendation execution gate",
					"Production Execution Allowed: No",
				],
				[],
			),
		]
		for raw_message, expected_phrases, forbidden_phrases in matrix:
			with self.subTest(raw_message=raw_message):
				answer = grounded_artifact_direct_evidence_answer(
					raw_message=raw_message,
					artifact_payload=artifact,
					grounded_turn=grounded_turn,
					evidence_request_contract={},
				)
				for phrase in expected_phrases:
					self.assertIn(phrase, answer)
				for phrase in forbidden_phrases:
					self.assertNotIn(phrase, answer)

		recommendation_payload = composite_ranked_row_direct_evidence_rendered_payload(
			raw_message="who should we collect from first?",
			artifact_payload=artifact,
			grounded_turn=grounded_turn,
		)
		block_titles = [block.get("title") for block in recommendation_payload.get("blocks") or []]
		self.assertEqual(
			block_titles,
			[
				"Current ERP Facts",
				"Required Policy",
				"Recommendation Execution Gate",
				"Decision Limit",
			],
		)
		gate_rows = {
			row[0]: row[1]
			for row in ((recommendation_payload.get("blocks") or [])[2].get("rows") or [])
			if len(row) == 2
		}
		self.assertEqual(gate_rows.get("Execution State"), "blocked_missing_policy")
		self.assertEqual(gate_rows.get("Policy Gate Ready"), "No")
		self.assertEqual(gate_rows.get("Production Execution Allowed"), "No")
		self.assertEqual(gate_rows.get("Safe Response Mode"), "grounded_evidence_boundary")

	def test_composite_ranked_row_bucket_breakdown_uses_deterministic_rendering(self):
		payload = composite_ranked_row_direct_evidence_rendered_payload(
			raw_message="show me the aging breakdown for the first customer",
			artifact_payload=_risk_artifact(),
			grounded_turn={},
		)

		self.assertEqual(payload.get("renderer_id"), "composite_ranked_row_direct_evidence")
		self.assertEqual(payload.get("rendering_policy"), "deterministic")
		self.assertEqual((payload.get("blocks") or [])[0].get("title"), "Aging Breakdown")
		self.assertIn(["31-60", "17,760,000"], (payload.get("blocks") or [])[0].get("rows") or [])

	def test_composite_evidence_preserves_grounded_followup_without_entity_detail_contract(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="risk-preserve-1",
			mode="new_query",
			requested_modes=[],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="accounts_receivable_read",
			target_report="Accounts Receivable Aging",
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=True,
			reason="Semantic fallback would otherwise break out to a fresh AR aging query.",
		)

		preserved = preserve_current_artifact_direct_evidence_followup_resolution(
			request_id="risk-preserve-1",
			followup_resolution=followup_resolution,
			evidence_request_contract={},
			direct_evidence_answer="35th Street Mobile Wholesale is highlighted in the Customer Risk As-Of.",
			evidence_boundary_answer="",
			latest_grounded_turn_available=True,
		)

		self.assertEqual(preserved.mode, "grounded_follow_up")
		self.assertFalse(preserved.self_contained)
		self.assertEqual(preserved.target_capability_id, "")
		self.assertIn("direct_evidence_followup", list(preserved.requested_modes))

	def test_reasoning_activation_uses_composite_blocked_variation_policy(self):
		activation = build_reasoning_activation_contract(
			request_id="reasoning-policy-activation",
			session_id="reasoning-policy",
			message="who should we collect from first?",
			latest_grounded_turn={
				"grounded": True,
				"trace_request_id": "risk-evidence-1",
				"source_kind": "frontdoor_composite",
				"source_name": "Customer Risk As-Of",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"row_count": 2,
				"date_range": {"as_of_date": "2026-04-25"},
				"artifact_family_id": "customer_entity_detail",
				"artifact_type": "normalized_family_artifact",
				"artifact_source_reports": ["Customer Risk As-Of"],
			},
			latest_family_artifact=_risk_artifact(),
			latest_assistant_payload={"title": "Customer Risk As-Of"},
			response_policy_contract={"policy_mode": "grounded_analysis"},
		)

		self.assertFalse(activation.recommendation_allowed)
		policy = dict(activation.grounding_summary.get("business_reasoning_authority_policy") or {})
		self.assertEqual(policy.get("policy_state"), "blocked")
		self.assertEqual(policy.get("blocked_variation"), "collection_recommendation")

	def test_reasoning_execution_blocks_metadata_forbidden_business_variation_before_runtime(self):
		activation = build_reasoning_activation_contract(
			request_id="reasoning-policy-execution",
			session_id="reasoning-policy",
			message="who should we collect from first?",
			latest_grounded_turn={
				"grounded": True,
				"trace_request_id": "risk-evidence-1",
				"source_kind": "frontdoor_composite",
				"source_name": "Customer Risk As-Of",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"row_count": 2,
				"date_range": {"as_of_date": "2026-04-25"},
				"artifact_family_id": "customer_entity_detail",
				"artifact_type": "normalized_family_artifact",
				"artifact_source_reports": ["Customer Risk As-Of"],
				"returned_schema": ["Customer", "Overdue Amount", "Outstanding Amount"],
				"table_rows": [
					{"Customer": "Ko Nay Lin Mobile Center", "Overdue Amount": "37,335,000"},
				],
			},
			latest_family_artifact=_risk_artifact(),
			latest_assistant_payload={"title": "Customer Risk As-Of"},
			response_policy_contract={"policy_mode": "grounded_analysis"},
		)
		semantic_result = {
			"status": "accepted",
			"intent": {
				"reasoning_type": "recommendation",
				"detail_level": "default",
				"presentation_style": "default",
				"confidence": 0.95,
				"reason": "The user asks for a collection recommendation.",
			},
		}
		result = execute_erp_business_reasoning(
			request_id="reasoning-policy-execution",
			session_id="reasoning-policy",
			user_id="Administrator",
			message="who should we collect from first?",
			recent_messages=[],
			activation_contract=activation.to_payload(),
			semantic_activation_result=semantic_result,
			latest_grounded_turn={
				"grounded": True,
				"trace_request_id": "risk-evidence-1",
				"source_kind": "frontdoor_composite",
				"source_name": "Customer Risk As-Of",
				"artifact_family_id": "customer_entity_detail",
				"artifact_type": "normalized_family_artifact",
				"artifact_source_reports": ["Customer Risk As-Of"],
			},
			latest_family_artifact=_risk_artifact(),
			latest_assistant_payload={"title": "Customer Risk As-Of"},
		)

		self.assertEqual(result.status, "insufficient_grounding")
		self.assertIn("business_reasoning_policy_blocked_variation", result.reasoning_contract.get("grounding_gaps"))
		answer = build_reasoning_boundary_answer(
			execution_result=result,
			activation_contract=activation.to_payload(),
			semantic_activation_result=semantic_result,
		)
		self.assertIn("does not authorize a collection recommendation", answer)
		self.assertIn("Rank 1: Ko Nay Lin Mobile Center", answer)


if __name__ == "__main__":
	unittest.main()
