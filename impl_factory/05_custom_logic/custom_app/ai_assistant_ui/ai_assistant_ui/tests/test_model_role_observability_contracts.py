import unittest

from ai_assistant_ui.qwen_chat.model_role_observability import (
	ROLE_DETERMINISTIC,
	ROLE_SHADOW_OBSERVER,
	build_model_role_observability_contract,
)


class ModelRoleObservabilityContractTests(unittest.TestCase):
	def test_deterministic_visible_context_contract_is_compliant_without_runtime_model(self):
		contract = build_model_role_observability_contract(
			lane="visible_context_followup",
			role_owner="visible_context_followup_activation",
			model_role=ROLE_DETERMINISTIC,
			model_name="none",
			fallback_used=False,
			runtime_source="deterministic_visible_context_contract",
		)

		self.assertEqual(contract["type"], "qwen_model_role_observability_contract")
		self.assertEqual(contract["lane"], "visible_context_followup")
		self.assertEqual(contract["model_role"], "deterministic")
		self.assertEqual(contract["expected_model_role"], "deterministic")
		self.assertEqual(contract["model_name"], "none")
		self.assertFalse(contract["fallback_used"])
		self.assertEqual(contract["role_compliance"], "compliant")
		self.assertFalse(contract["strict_mode_enforced"])

	def test_shadow_observer_reads_runtime_agent_metadata_without_claiming_enforcement(self):
		contract = build_model_role_observability_contract(
			lane="nbu_shadow_observation",
			role_owner="natural_business_understanding_shadow_runtime",
			model_role=ROLE_SHADOW_OBSERVER,
			agent_meta={
				"model": "qwen-light-semantic",
				"fallback_used": False,
			},
			runtime_source="nbu_runtime_response_agent_meta",
		)

		self.assertEqual(contract["model_role"], "shadow_observer")
		self.assertEqual(contract["expected_model_role"], "shadow_observer")
		self.assertEqual(contract["model_name"], "qwen-light-semantic")
		self.assertFalse(contract["fallback_used"])
		self.assertEqual(contract["role_compliance"], "compliant")
		self.assertFalse(contract["strict_mode_enforced"])

	def test_fallback_is_visible_and_role_compliance_is_not_overstated(self):
		contract = build_model_role_observability_contract(
			lane="fresh_query_interpretation",
			role_owner="fresh_query_router",
			model_role="light_semantic",
			agent_meta={
				"telemetry": {
					"model_name": "qwen-light-semantic",
					"fallback_used": True,
					"fallback_reason": "semantic_runtime_timeout",
				}
			},
			runtime_source="semantic_runtime",
		)

		self.assertEqual(contract["expected_model_role"], "light_semantic")
		self.assertEqual(contract["model_name"], "qwen-light-semantic")
		self.assertTrue(contract["fallback_used"])
		self.assertEqual(contract["fallback_reason"], "semantic_runtime_timeout")
		self.assertEqual(contract["role_compliance"], "unknown")

	def test_missing_model_metadata_is_explicit_unknown_not_invented(self):
		contract = build_model_role_observability_contract(
			lane="business_reasoning_answer",
			role_owner="business_reasoning_renderer",
			model_role="",
			runtime_source="heavy_reasoning_runtime",
		)

		self.assertEqual(contract["model_role"], "unknown")
		self.assertEqual(contract["expected_model_role"], "heavy_reasoning")
		self.assertEqual(contract["model_name"], "unknown")
		self.assertEqual(contract["role_compliance"], "unknown")


if __name__ == "__main__":
	unittest.main()
