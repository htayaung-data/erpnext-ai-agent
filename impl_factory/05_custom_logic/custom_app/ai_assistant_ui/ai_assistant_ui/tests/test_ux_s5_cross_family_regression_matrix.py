import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat import reasoning_execution as subject
from ai_assistant_ui.qwen_chat.evidence_drilldown_registry import build_governed_drilldown_plan
from ai_assistant_ui.tests import test_reasoning_execution_grounding as fixtures


def _assert_no_internal_terms(testcase, answer_text):
	answer = str(answer_text or "").lower()
	for internal_term in ("runtime", "contract", "artifact"):
		testcase.assertNotIn(internal_term, answer)


def _execute_reasoning(
	*,
	request_id,
	message,
	activation_contract,
	semantic_activation_result,
	latest_grounded_turn,
	latest_family_artifact,
	latest_assistant_payload,
	prior_reasoning_contract=None,
	prior_answer_text="",
):
	with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
		result = subject.execute_erp_business_reasoning(
			request_id=request_id,
			session_id="ux-s5e-matrix",
			user_id="Administrator",
			message=message,
			recent_messages=[],
			activation_contract=activation_contract,
			semantic_activation_result=semantic_activation_result,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
			presentation_preferences={"bullet": True},
			prior_reasoning_contract=prior_reasoning_contract,
			prior_answer_text=prior_answer_text,
		)
	runtime_call.assert_not_called()
	return result


def _entity_activation(entity_grain):
	return {
		"scope_id": f"{entity_grain}_scope",
		"entity_grain": entity_grain,
		"entity_label": entity_grain.replace("_", " ").title(),
		"entity_plural_label": f"{entity_grain.replace('_', ' ').title()}s",
		"identity_field": entity_grain,
		"display_field": f"{entity_grain}_name",
		"runtime_policy": {"can_execute": True},
	}


class UXS5CrossFamilyRegressionMatrixTests(unittest.TestCase):
	def test_financial_statement_consultant_matrix_uses_statement_specific_lenses(self):
		cases = [
			(
				"pnl",
				fixtures._activation_contract_profit_and_loss(),
				fixtures._latest_family_artifact_profit_and_loss(),
				fixtures._latest_assistant_payload_profit_and_loss_title_only(),
				["Expenses exceed income", "Expense burden", "Cost of Goods Sold", "profit-recovery target"],
				["Bucket Totals", "Indent", "I stopped rather than guess"],
			),
			(
				"cash_flow",
				fixtures._activation_contract_cash_flow(),
				fixtures._latest_family_artifact_cash_flow(),
				fixtures._latest_assistant_payload_cash_flow_title_only(),
				["Operations generated positive cash", "Financing cash flow", "Management priorities", "Net Change in Accounts Receivable"],
				["Bucket Totals", "I stopped rather than guess"],
			),
			(
				"balance_sheet",
				fixtures._activation_contract_profit_and_loss(),
				fixtures._latest_family_artifact_balance_sheet(),
				fixtures._latest_assistant_payload_balance_sheet_title_only(),
				["Liabilities are", "Equity funds", "liability-heavy", "Manage leverage before growth"],
				["Bucket Totals", "I stopped rather than guess"],
			),
		]

		for label, activation_contract, artifact, assistant_payload, expected_terms, forbidden_terms in cases:
			with self.subTest(statement=label):
				result = _execute_reasoning(
					request_id=f"ux-s5e-finance-{label}",
					message="Explain this as a business consultant",
					activation_contract=activation_contract,
					semantic_activation_result=fixtures._semantic_activation_result(),
					latest_grounded_turn=fixtures._latest_grounded_turn_profit_and_loss(),
					latest_family_artifact=artifact,
					latest_assistant_payload=assistant_payload,
				)

				self.assertEqual(result.status, "answered")
				self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
				self.assertIn("Executive diagnosis", result.answer_text)
				self.assertIn("Management priorities", result.answer_text)
				_assert_no_internal_terms(self, result.answer_text)
				for term in expected_terms:
					self.assertIn(term, result.answer_text)
				for term in forbidden_terms:
					self.assertNotIn(term, result.answer_text)

	def test_ar_ap_consultant_matrix_keeps_customer_supplier_and_working_capital_lenses(self):
		ar_result = _execute_reasoning(
			request_id="ux-s5e-ar-consultant",
			message="Give me key insights as Business Consultant",
			activation_contract=fixtures._activation_contract(),
			semantic_activation_result=fixtures._semantic_activation_result(),
			latest_grounded_turn=fixtures._latest_grounded_turn(),
			latest_family_artifact={},
			latest_assistant_payload=fixtures._latest_assistant_payload_visible_aging_table(),
		)
		self.assertEqual(ar_result.status, "answered")
		self.assertIn("Collection pressure is structural", ar_result.answer_text)
		self.assertIn("listed customers", ar_result.answer_text)
		self.assertNotIn("Supplier payment pressure is structural", ar_result.answer_text)
		self.assertEqual(
			(ar_result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("entity_scope"),
			"customers",
		)
		_assert_no_internal_terms(self, ar_result.answer_text)

		ap_result = _execute_reasoning(
			request_id="ux-s5e-ap-consultant",
			message="Give me key insights as Business Consultant",
			activation_contract=fixtures._activation_contract_accounts_payable(),
			semantic_activation_result=fixtures._semantic_activation_result(),
			latest_grounded_turn={"grounded": True, "source_name": "Accounts Payable Aging", "table_rows": []},
			latest_family_artifact={},
			latest_assistant_payload=fixtures._latest_assistant_payload_visible_ap_aging_table(),
		)
		self.assertEqual(ap_result.status, "answered")
		self.assertIn("Supplier payment pressure is structural", ap_result.answer_text)
		self.assertIn("listed suppliers", ap_result.answer_text)
		self.assertNotIn("Collection pressure is structural", ap_result.answer_text)
		self.assertEqual(
			(ap_result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("entity_scope"),
			"suppliers",
		)
		_assert_no_internal_terms(self, ap_result.answer_text)

		working_capital_result = _execute_reasoning(
			request_id="ux-s5e-working-capital-consultant",
			message="Give me more insight on above AR/AP evaluation",
			activation_contract=fixtures._activation_contract_ar_ap_working_capital(),
			semantic_activation_result=fixtures._semantic_activation_result_evidence_expansion_continuation(),
			latest_grounded_turn={"grounded": True, "source_name": "AR / AP Working Capital Health", "table_rows": []},
			latest_family_artifact=fixtures._latest_family_artifact_ar_ap_working_capital(),
			latest_assistant_payload=fixtures._latest_assistant_payload_ar_ap_working_capital_title_only(),
			prior_answer_text=(
				"AR/AP Working Capital Health shows Accounts Receivable Outstanding 803,681,000, "
				"Accounts Payable Outstanding 929,916,600, and both overdue ratios are material."
			),
		)
		self.assertEqual(working_capital_result.status, "answered")
		self.assertIn("working-capital squeeze", working_capital_result.answer_text)
		self.assertIn("two-sided working-capital stress", working_capital_result.answer_text)
		self.assertIn("customer collection pressure", working_capital_result.answer_text)
		self.assertNotIn("sales summary", working_capital_result.answer_text.lower())
		self.assertNotIn("supporting ERP detail view", working_capital_result.answer_text)
		self.assertEqual(
			(working_capital_result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("action_id"),
			"compare_ar_ap_pressure_side_by_side",
		)
		_assert_no_internal_terms(self, working_capital_result.answer_text)

	def test_yes_please_executes_prior_offered_action_without_family_drift(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "interpretation",
			"grounding_source_request_id": "grounded-risk-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "accounts_receivable",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Aging"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"offered_next_actions": [
				{
					"action_id": "compare_listed_parties_by_overdue_and_intensity",
					"execution_mode": "current_governed_artifact",
					"comparison_metrics": ["overdue_amount", "overdue_intensity"],
				}
			],
			"speculation_flags": [],
		}

		result = _execute_reasoning(
			request_id="ux-s5e-yes-please-party-comparison",
			message="yes please",
			activation_contract=fixtures._activation_contract(),
			semantic_activation_result=fixtures._semantic_activation_result_current_result_continuation(),
			latest_grounded_turn=fixtures._latest_grounded_turn(),
			latest_family_artifact=fixtures._latest_family_artifact_aging_sections(),
			latest_assistant_payload=fixtures._latest_assistant_payload_visible_aging_table(),
			prior_reasoning_contract=prior_contract,
			prior_answer_text="Would you like me to compare the listed customers by overdue amount and overdue intensity next?",
		)

		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("executed_prior_offered_next_action"))
		self.assertIn("Comparison table", result.answer_text)
		self.assertIn("35th Street Mobile Wholesale", result.answer_text)
		self.assertIn("overdue intensity", result.answer_text)
		self.assertNotIn("Profit and Loss Statement", result.answer_text)
		self.assertNotIn("Which financial view", result.answer_text)
		self.assertFalse(result.reasoning_contract.get("offered_next_actions"))
		_assert_no_internal_terms(self, result.answer_text)

	@patch("ai_assistant_ui.qwen_chat.evidence_drilldown_registry.list_active_entity_detail_scope_activations")
	def test_detail_drilldown_matrix_covers_customer_supplier_item_invoice_and_wrong_family_prevention(self, activations):
		activations.return_value = [
			_entity_activation("customer"),
			_entity_activation("supplier"),
			_entity_activation("item"),
			_entity_activation("sales_invoice"),
		]
		context = {
			"answer_goal": "expand_detail",
			"evidence_depth": "drilldown_preferred",
			"business_role": "business_consultant",
			"target_reference": "current_row",
			"risk_level": "bounded_consultation",
			"grounded_source": {"family_id": "cross_family_matrix", "capability_id": "matrix_read"},
		}
		cases = [
			({"Customer": "35th Street Mobile Wholesale", "Outstanding Amount": "84,837,000"}, "customer"),
			({"Supplier": "Sunflower Accessories Co.", "Outstanding Amount": "222,526,500"}, "supplier"),
			({"Item": "Xiaomi Redmi Note 13", "Revenue": "33,450,000"}, "item"),
			({"Sales Invoice": "ACC-SINV-2026-00205", "Grand Total": "4,375,000"}, "sales_invoice"),
		]

		for row, expected_entity_type in cases:
			with self.subTest(expected_entity_type=expected_entity_type):
				plan = build_governed_drilldown_plan(grounding_context=context, focused_row=row)

				self.assertEqual(plan["status"], "entity_detail_available")
				self.assertTrue(plan["can_execute"])
				self.assertEqual(plan["target_entity"]["entity_type"], expected_entity_type)

		summary_plan = build_governed_drilldown_plan(
			grounding_context=context,
			focused_row={"Account": "Cost of Goods Sold - MMOB", "2026": "65,245,820.70"},
		)
		self.assertEqual(summary_plan["status"], "source_detail_required")
		self.assertFalse(summary_plan["can_execute"])
		self.assertNotIn("target_entity", summary_plan)


if __name__ == "__main__":
	unittest.main()
