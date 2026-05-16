import unittest

from ai_assistant_ui.qwen_chat.regression_scenario_packs import (
	EXECUTION_DETERMINISTIC_CONTRACT,
	EXECUTION_MANUAL_BROWSER_UAT,
	PACK_FINANCIAL_STATEMENT_DRILLDOWN,
	PACK_MANUAL_BROWSER_UAT,
	PACK_POLICY_BOUNDARIES,
	PACK_PROJECTION_AND_CARDINALITY,
	PACK_TRACE_AND_MODEL_ROLE,
	PACK_VISIBLE_CONTEXT_SWITCHING,
	REGRESSION_SCENARIO_PACK_CONTRACT_TYPE,
	REGRESSION_SCENARIO_PACK_SUITE_ID,
	REQUIRED_SCENARIO_FIELDS,
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
	build_regression_scenario_pack_contract,
	deterministic_regression_scenarios,
	manual_uat_regression_scenarios,
	regression_scenario_missing_fields,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)
from ai_assistant_ui.qwen_chat.visible_context_trace_inspection import INSPECTION_PAYLOAD_TYPE
from ai_assistant_ui.tests.test_visible_context_conversation_regression import (
	VisibleConversationHarness,
	_ap_top_5_text,
	_cogs_source_detail_text,
	_product_revenue_text,
	_product_revenue_top_10_with_qty_text,
)
from ai_assistant_ui.tests.test_visible_context_trace_inspection import (
	TraceInspectionHarness,
	_audit_envelope_with_final_authority,
)


def _ar_top_5_text() -> str:
	return """Accounts Receivable Aging as of 2026-05-12

Top 5 Customers

Customer	Outstanding (MMK)	Total Due (MMK)	Overdue (31+) (MMK)
Capital Telecom (NPT)	97,309,500	63,654,500	36,054,500
Bayint Naung Wholesale Mobile	95,513,000	69,287,000	33,559,000
35th Street Mobile Wholesale	84,837,000	84,237,000	58,212,000
Ko Nay Lin Mobile Center	63,125,000	63,125,000	37,335,000
Latha Mobile Wholesale	49,352,000	49,352,000	33,372,000
"""


def _ar_top_7_text() -> str:
	return """Accounts Receivable Aging as of 2026-05-12

Top 7 Customers

Customer	Outstanding (MMK)	Total Due (MMK)	Overdue (31+) (MMK)
Capital Telecom (NPT)	97,309,500	63,654,500	36,054,500
Bayint Naung Wholesale Mobile	95,513,000	69,287,000	33,559,000
35th Street Mobile Wholesale	84,837,000	84,237,000	58,212,000
Ko Nay Lin Mobile Center	63,125,000	63,125,000	37,335,000
Latha Mobile Wholesale	49,352,000	49,352,000	33,372,000
Mandalay Accessories Wholesale	38,320,000	33,090,000	29,430,000
Mandalay Mobile Hub	38,100,000	38,100,000	28,280,000
"""


def _product_revenue_million_top_7_text() -> str:
	return """Top 7 Products by Revenue (2026-04-01 to 2026-04-30)

Top Ranked Rows

Rank	Product	Revenue (MMK Million)
1	Xiaomi Redmi Note 13 (8GB 256GB)	33.45
2	Samsung Galaxy A15 (6GB 128GB)	19.77
3	Power Bank 20000mAh	11.94
4	Xiaomi Fast Charger 33W	6.61
5	Apple iPhone 14 128GB	5
6	Type-C Cable 1m Fast Charge	1.55
7	Wi-Fi Router Archer C54	0.34
"""


def _ledger(result):
	return result.trace.get("semantic_ownership_ledger") or {}


def _assert_visible_contract(
	testcase: unittest.TestCase,
	result,
	*,
	answer_mode: str,
	entity_type: str,
	row_reference: str,
	authority_source: str = "visible_rendered_table",
	policy_boundary: str = "none",
) -> None:
	testcase.assertTrue(result.handled)
	testcase.assertEqual(result.payload.get("mode"), answer_mode)
	ledger = _ledger(result)
	resolved_context = ledger.get("resolved_context") or {}
	authority = ledger.get("authority") or {}
	testcase.assertEqual(resolved_context.get("entity_type"), entity_type)
	testcase.assertEqual(resolved_context.get("row_reference"), row_reference)
	testcase.assertEqual(authority.get("authority_source"), authority_source)
	testcase.assertEqual(authority.get("policy_boundary"), policy_boundary)
	testcase.assertEqual(authority.get("answer_mode"), answer_mode)
	testcase.assertEqual(authority.get("evidence_scope"), "visible_rendered_table")
	observability = result.trace.get("model_role_observability") or {}
	testcase.assertEqual(observability.get("lane"), "visible_context_followup")
	testcase.assertEqual(observability.get("model_role"), "deterministic")
	testcase.assertEqual(observability.get("expected_model_role"), "deterministic")
	testcase.assertEqual(observability.get("role_compliance"), "compliant")
	coverage = result.trace.get("model_role_coverage") or {}
	testcase.assertIn("visible_context_followup", coverage.get("required_lanes") or [])
	testcase.assertIn("policy_boundary_rendering", coverage.get("observed_lanes") or [])


class RegressionScenarioPacksTests(unittest.TestCase):
	def test_scenario_pack_registry_is_structured_and_linked_to_s7_6a_boundary(self):
		contract = build_regression_scenario_pack_contract()

		self.assertEqual(contract["type"], REGRESSION_SCENARIO_PACK_CONTRACT_TYPE)
		self.assertTrue(contract["contract_complete"])
		self.assertEqual(contract["linked_regression_suite_id"], REGRESSION_SCENARIO_PACK_SUITE_ID)
		self.assertEqual(contract["missing_pack_ids"], [])
		self.assertEqual(contract["duplicate_scenario_ids"], [])
		self.assertEqual(contract["incomplete_scenarios"], [])
		self.assertGreaterEqual(contract["deterministic_scenario_count"], 10)
		self.assertGreaterEqual(contract["manual_uat_scenario_count"], 1)
		self.assertEqual(
			set(contract["pack_ids"]),
			{
				PACK_VISIBLE_CONTEXT_SWITCHING,
				PACK_PROJECTION_AND_CARDINALITY,
				PACK_FINANCIAL_STATEMENT_DRILLDOWN,
				PACK_POLICY_BOUNDARIES,
				PACK_TRACE_AND_MODEL_ROLE,
				PACK_MANUAL_BROWSER_UAT,
			},
		)

		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}
		self.assertIn(REGRESSION_SCENARIO_PACK_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(REGRESSION_SCENARIO_PACK_SUITE_ID, entries)
		entry = entries[REGRESSION_SCENARIO_PACK_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])

	def test_every_scenario_declares_required_enterprise_contract_fields(self):
		for entry in S7_REGRESSION_SCENARIO_REGISTRY:
			with self.subTest(scenario=entry.get("scenario_id")):
				self.assertEqual(regression_scenario_missing_fields(entry), [])
				contract = build_regression_scenario_contract(entry)
				self.assertTrue(contract["scenario_complete"])
				for field in REQUIRED_SCENARIO_FIELDS:
					self.assertIn(field, contract)

	def test_manual_uat_scenarios_are_explicitly_separated_from_deterministic_gates(self):
		deterministic = deterministic_regression_scenarios()
		manual = manual_uat_regression_scenarios()

		self.assertTrue(deterministic)
		self.assertTrue(manual)
		self.assertTrue(all(entry["execution_mode"] == EXECUTION_DETERMINISTIC_CONTRACT for entry in deterministic))
		self.assertTrue(all(entry["execution_mode"] == EXECUTION_MANUAL_BROWSER_UAT for entry in manual))
		self.assertTrue(all(not entry["manual_uat"] for entry in deterministic))
		self.assertTrue(all(entry["manual_uat"] for entry in manual))

	def test_visible_context_switching_scenarios_resolve_ar_and_ap_authority(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ar_top_7_text())
		chat.assistant(_ap_top_5_text())

		ar_lookup = chat.ask("Who is second in the above AR table?")
		self.assertIn("Bayint Naung Wholesale Mobile", ar_lookup.answer)
		_assert_visible_contract(
			self,
			ar_lookup,
			answer_mode="visible_context_answer",
			entity_type="customer",
			row_reference="rank_2",
		)
		arbitration = ar_lookup.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration.get("selected_visible_row_count"), 7)
		self.assertEqual(arbitration.get("selected_requested_limit"), 7)
		self.assertEqual(arbitration.get("selection_strategy"), "current_table:contract_context_match")

		ap_lookup = chat.ask("Who is second in the above table?")
		self.assertIn("Sunflower Accessories Co.", ap_lookup.answer)
		_assert_visible_contract(
			self,
			ap_lookup,
			answer_mode="visible_context_answer",
			entity_type="supplier",
			row_reference="rank_2",
		)

	def test_product_projection_and_out_of_range_scenarios_preserve_authority(self):
		chat = VisibleConversationHarness()
		chat.assistant(_product_revenue_million_top_7_text())

		rank_two = chat.ask("Who is second in the above table?")
		self.assertIn("Samsung Galaxy A15", rank_two.answer)
		self.assertIn("19.77", rank_two.answer)
		_assert_visible_contract(
			self,
			rank_two,
			answer_mode="visible_context_answer",
			entity_type="item",
			row_reference="rank_2",
		)

		chat_with_qty = VisibleConversationHarness()
		chat_with_qty.assistant(_product_revenue_top_10_with_qty_text())
		qty_rank_two = chat_with_qty.ask("Who is second in the above table?")
		self.assertIn("Xiaomi Redmi Note 13", qty_rank_two.answer)
		self.assertIn("281,770,000", qty_rank_two.answer)
		self.assertIn("286", qty_rank_two.answer)
		_assert_visible_contract(
			self,
			qty_rank_two,
			answer_mode="visible_context_answer",
			entity_type="item",
			row_reference="rank_2",
		)

		out_of_range_chat = VisibleConversationHarness()
		out_of_range_chat.assistant(_product_revenue_text())
		out_of_range = out_of_range_chat.ask("Tell me more about rank 8 product.")
		self.assertIn("only 7 visible rows", out_of_range.answer)
		self.assertIn("Rank 7: Xiaomi Fast Charger 33W", out_of_range.answer)
		_assert_visible_contract(
			self,
			out_of_range,
			answer_mode="visible_context_out_of_range",
			entity_type="item",
			row_reference="none",
			policy_boundary="visible_context_out_of_range",
		)
		resolution = out_of_range.trace.get("resolution") or {}
		self.assertEqual(resolution.get("status"), "out_of_range")
		self.assertEqual(resolution.get("available_row_count"), 7)

	def test_financial_statement_cogs_drilldown_scenario_resolves_source_document_rank(self):
		chat = VisibleConversationHarness()
		chat.assistant(_cogs_source_detail_text())

		lookup = chat.ask("Who is second in the above table?")

		self.assertIn("Delivery Note MAT-DN-2026-00336", lookup.answer)
		_assert_visible_contract(
			self,
			lookup,
			answer_mode="visible_context_answer",
			entity_type="document",
			row_reference="rank_2",
		)
		self.assertIn("Net Line Impact", lookup.answer)
		self.assertIn("Share Of Line", lookup.answer)

	def test_policy_boundary_scenarios_are_bounded_with_current_visible_facts(self):
		prediction_chat = VisibleConversationHarness()
		prediction_chat.assistant(_ar_top_5_text())
		selected = prediction_chat.ask("Who is Rank 2 in the above table?")
		self.assertIn("Bayint Naung Wholesale Mobile", selected.answer)
		prediction = prediction_chat.ask("Will this customer default next month?")
		self.assertIn("can't forecast", prediction.answer)
		self.assertIn("Bayint Naung Wholesale Mobile", prediction.answer)
		_assert_visible_contract(
			self,
			prediction,
			answer_mode="visible_context_boundary",
			entity_type="customer",
			row_reference="rank_2",
			policy_boundary="prediction_boundary",
		)

		cause_chat = VisibleConversationHarness()
		cause_chat.assistant(_ar_top_5_text())
		cause = cause_chat.ask("From above table, what caused the first customer risk to increase?")
		self.assertIn("can't attribute cause", cause.answer)
		_assert_visible_contract(
			self,
			cause,
			answer_mode="visible_context_boundary",
			entity_type="customer",
			row_reference="rank_1",
			policy_boundary="causal_boundary",
		)

		recommendation_chat = VisibleConversationHarness()
		recommendation_chat.assistant(_ar_top_5_text())
		recommendation = recommendation_chat.ask("Which customer should we collect from first?")
		self.assertIn("can't recommend a business action", recommendation.answer)
		_assert_visible_contract(
			self,
			recommendation,
			answer_mode="visible_context_boundary",
			entity_type="customer",
			row_reference="rank_1",
			policy_boundary="recommendation_boundary",
		)

	def test_requested_cardinality_is_visible_in_trace_for_top5_and_top7_artifacts(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ar_top_5_text())
		top_five = chat.ask("Who is rank 5 in the above table?")
		self.assertIn("Latha Mobile Wholesale", top_five.answer)
		arbitration_five = top_five.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration_five.get("selected_visible_row_count"), 5)
		self.assertEqual(arbitration_five.get("selected_requested_limit"), 5)
		_assert_visible_contract(
			self,
			top_five,
			answer_mode="visible_context_answer",
			entity_type="customer",
			row_reference="rank_5",
		)

		chat.assistant(_ar_top_7_text())
		top_seven = chat.ask("Who is rank 7 in the above table?")
		self.assertIn("Mandalay Mobile Hub", top_seven.answer)
		arbitration_seven = top_seven.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration_seven.get("selected_visible_row_count"), 7)
		self.assertEqual(arbitration_seven.get("selected_requested_limit"), 7)
		_assert_visible_contract(
			self,
			top_seven,
			answer_mode="visible_context_answer",
			entity_type="customer",
			row_reference="rank_7",
		)

	def test_trace_inspection_scenario_renders_model_role_and_final_authority_sections(self):
		chat = TraceInspectionHarness()
		chat.assistant(_cogs_source_detail_text())
		lookup = chat.ask("Who is second in the above table?")
		self.assertTrue(lookup.handled)
		ledger = _ledger(lookup)
		resolved_context = ledger.get("resolved_context") or {}
		chat.tool(
			_audit_envelope_with_final_authority(
				selected_artifact_id=resolved_context.get("artifact_id") or "visible-assistant-1",
				selected_report_family=resolved_context.get("report_family") or "source_detail_breakdown",
				selected_row_reference=resolved_context.get("row_reference") or "rank_2",
			)
		)

		inspection = chat.inspect("Show latest context authority trace")

		self.assertTrue(inspection.handled)
		self.assertEqual(inspection.payload.get("mode"), "visible_context_trace_inspection")
		self.assertIn("**Semantic Ownership Ledger**", inspection.answer)
		self.assertIn("**Final Answer Authority**", inspection.answer)
		self.assertIn("**Policy Boundary Uniformity**", inspection.answer)
		self.assertIn("**Model Role Observability**", inspection.answer)
		self.assertIn("**Model Role Strict Readiness**", inspection.answer)
		self.assertIn("**Model Role Coverage**", inspection.answer)
		inspection_contract = inspection.latest_payload(INSPECTION_PAYLOAD_TYPE)
		self.assertTrue(inspection_contract.get("final_answer_authority_available"))
		self.assertTrue(inspection_contract.get("model_role_observability_available"))
		self.assertTrue(inspection_contract.get("model_role_strict_readiness_available"))
		self.assertTrue(inspection_contract.get("model_role_coverage_available"))
		self.assertEqual(inspection_contract.get("model_role_lane"), "visible_context_followup")
		self.assertEqual(inspection_contract.get("model_role"), "deterministic")
		self.assertEqual(inspection_contract.get("model_role_compliance"), "compliant")


if __name__ == "__main__":
	unittest.main()
