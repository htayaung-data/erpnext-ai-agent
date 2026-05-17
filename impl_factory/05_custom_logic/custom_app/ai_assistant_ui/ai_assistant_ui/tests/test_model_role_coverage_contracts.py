import unittest

from ai_assistant_ui.qwen_chat.model_role_coverage import (
	ACTIVE_MODEL_ROLE_COVERAGE_LANES,
	build_deterministic_model_role_contract_bundle,
	build_model_role_contract_bundle,
	build_model_role_coverage_contract,
)
from ai_assistant_ui.qwen_chat.model_role_observability import (
	ROLE_DETERMINISTIC,
	ROLE_LIGHT_SEMANTIC,
	ROLE_UNKNOWN,
)
from ai_assistant_ui.qwen_chat.model_role_strict_readiness import (
	STATUS_MISSING_METADATA,
	STATUS_NOT_APPLICABLE_DETERMINISTIC,
	STATUS_READY_FOR_STRICT,
	STATUS_UNKNOWN_RUNTIME,
)


class ModelRoleCoverageContractTests(unittest.TestCase):
	def test_contract_bundle_builds_observability_and_readiness_together(self):
		bundle = build_model_role_contract_bundle(
			lane="frontdoor_semantic_classification",
			role_owner="frontdoor_intent_gate",
			model_role=ROLE_LIGHT_SEMANTIC,
			agent_meta={"model_name": "qwen-light-semantic", "fallback_used": False},
			runtime_source="frontdoor_runtime_agent_meta",
		)

		observability = bundle["model_role_observability"]
		readiness = bundle["model_role_strict_readiness"]
		self.assertEqual(observability["lane"], "frontdoor_semantic_classification")
		self.assertEqual(observability["model_role"], ROLE_LIGHT_SEMANTIC)
		self.assertEqual(observability["expected_model_role"], ROLE_LIGHT_SEMANTIC)
		self.assertEqual(observability["model_name"], "qwen-light-semantic")
		self.assertEqual(readiness["readiness_status"], STATUS_READY_FOR_STRICT)
		self.assertFalse(readiness["strict_enforcement_enabled"])

	def test_deterministic_bundle_is_audited_but_not_ai_strict_ready(self):
		bundle = build_deterministic_model_role_contract_bundle(
			lane="erp_report_execution",
			role_owner="governed_report_executor",
			runtime_source="deterministic_governed_report_executor",
		)

		observability = bundle["model_role_observability"]
		readiness = bundle["model_role_strict_readiness"]
		self.assertEqual(observability["model_role"], ROLE_DETERMINISTIC)
		self.assertEqual(observability["expected_model_role"], ROLE_DETERMINISTIC)
		self.assertEqual(readiness["readiness_status"], STATUS_NOT_APPLICABLE_DETERMINISTIC)
		self.assertTrue(readiness["runtime_safe_without_model_enforcement"])
		self.assertFalse(readiness["strict_enforcement_ready"])

	def test_coverage_lists_uncovered_lanes_as_blockers_not_compliance(self):
		visible_bundle = build_deterministic_model_role_contract_bundle(
			lane="visible_context_followup",
			role_owner="visible_context_followup_activation",
			runtime_source="deterministic_visible_context_contract",
		)

		coverage = build_model_role_coverage_contract(
			observed_contracts=[visible_bundle["model_role_observability"]],
			required_lanes=[
				"visible_context_followup",
				"fresh_query_interpretation",
				"business_reasoning_answer",
			],
		)

		self.assertEqual(coverage["type"], "qwen_model_role_coverage_contract")
		self.assertEqual(coverage["coverage_status"], "partial_blocked")
		self.assertFalse(coverage["coverage_complete"])
		self.assertFalse(coverage["global_strict_enforcement_safe"])
		self.assertEqual(coverage["observed_lanes"], ["visible_context_followup"])
		self.assertEqual(
			coverage["uncovered_lanes"],
			["fresh_query_interpretation", "business_reasoning_answer"],
		)
		self.assertEqual(coverage["blocking_lanes"], coverage["uncovered_lanes"])
		self.assertEqual(coverage["status_counts"][STATUS_MISSING_METADATA], 2)

	def test_unknown_ai_runtime_metadata_remains_blocking_even_when_lane_is_observed(self):
		unknown_bundle = build_model_role_contract_bundle(
			lane="fresh_query_interpretation",
			role_owner="fresh_query_interpreter",
			model_role=ROLE_UNKNOWN,
			runtime_source="fresh_query_runtime_missing_agent_meta",
		)

		coverage = build_model_role_coverage_contract(
			observed_contracts=[unknown_bundle["model_role_observability"]],
			required_lanes=["fresh_query_interpretation"],
		)

		self.assertEqual(coverage["coverage_status"], "partial_blocked")
		self.assertTrue(coverage["coverage_complete"])
		self.assertFalse(coverage["global_strict_enforcement_safe"])
		self.assertEqual(coverage["uncovered_lanes"], [])
		self.assertEqual(coverage["blocking_lanes"], ["fresh_query_interpretation"])
		self.assertEqual(coverage["status_counts"][STATUS_UNKNOWN_RUNTIME], 1)

	def test_default_active_lane_registry_includes_enterprise_semantic_surfaces(self):
		self.assertIn("frontdoor_semantic_classification", ACTIVE_MODEL_ROLE_COVERAGE_LANES)
		self.assertIn("fresh_query_interpretation", ACTIVE_MODEL_ROLE_COVERAGE_LANES)
		self.assertIn("followup_interpretation", ACTIVE_MODEL_ROLE_COVERAGE_LANES)
		self.assertIn("erp_report_execution", ACTIVE_MODEL_ROLE_COVERAGE_LANES)
		self.assertIn("business_reasoning_answer", ACTIVE_MODEL_ROLE_COVERAGE_LANES)
		self.assertIn("policy_boundary_rendering", ACTIVE_MODEL_ROLE_COVERAGE_LANES)


if __name__ == "__main__":
	unittest.main()
