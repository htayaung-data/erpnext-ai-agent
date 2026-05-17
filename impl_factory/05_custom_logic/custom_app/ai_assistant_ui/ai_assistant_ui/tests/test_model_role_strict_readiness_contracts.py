import unittest

from ai_assistant_ui.qwen_chat.model_role_observability import (
	ROLE_DETERMINISTIC,
	ROLE_HEAVY_REASONING,
	ROLE_SHADOW_OBSERVER,
	build_model_role_observability_contract,
)
from ai_assistant_ui.qwen_chat.model_role_strict_readiness import (
	STATUS_FALLBACK_UNTRACKED,
	STATUS_MISSING_METADATA,
	STATUS_NOT_APPLICABLE_DETERMINISTIC,
	STATUS_READY_FOR_STRICT,
	STATUS_ROLE_MISMATCH,
	STATUS_UNKNOWN_RUNTIME,
	build_model_role_strict_readiness_contract,
	build_model_role_strict_readiness_summary,
)


class ModelRoleStrictReadinessContractTests(unittest.TestCase):
	def test_deterministic_lane_is_audited_but_exempt_from_ai_model_enforcement(self):
		observability = build_model_role_observability_contract(
			lane="visible_context_followup",
			role_owner="visible_context_followup_activation",
			model_role=ROLE_DETERMINISTIC,
			model_name="none",
			fallback_used=False,
			runtime_source="deterministic_visible_context_contract",
		)

		readiness = build_model_role_strict_readiness_contract(
			model_role_observability=observability,
			lane="visible_context_followup",
		)

		self.assertEqual(readiness["type"], "qwen_model_role_strict_readiness_contract")
		self.assertEqual(readiness["readiness_status"], STATUS_NOT_APPLICABLE_DETERMINISTIC)
		self.assertFalse(readiness["strict_enforcement_ready"])
		self.assertTrue(readiness["runtime_safe_without_model_enforcement"])
		self.assertFalse(readiness["strict_enforcement_enabled"])
		self.assertFalse(readiness["blocking"])
		self.assertTrue(readiness["deterministic_lane"])
		self.assertFalse(readiness["requires_ai_runtime"])

	def test_ai_runtime_lane_with_known_model_and_no_fallback_is_ready_for_future_strict_mode(self):
		observability = build_model_role_observability_contract(
			lane="nbu_shadow_observation",
			role_owner="natural_business_understanding_shadow_runtime",
			model_role=ROLE_SHADOW_OBSERVER,
			agent_meta={"model_name": "qwen-light-semantic", "fallback_used": False},
			runtime_source="nbu_runtime_response_agent_meta",
		)

		readiness = build_model_role_strict_readiness_contract(
			model_role_observability=observability,
			lane="nbu_shadow_observation",
		)

		self.assertEqual(readiness["readiness_status"], STATUS_READY_FOR_STRICT)
		self.assertTrue(readiness["strict_enforcement_ready"])
		self.assertFalse(readiness["runtime_safe_without_model_enforcement"])
		self.assertFalse(readiness["strict_enforcement_enabled"])
		self.assertFalse(readiness["blocking"])
		self.assertTrue(readiness["requires_ai_runtime"])

	def test_missing_model_role_observability_is_not_marked_compliant(self):
		readiness = build_model_role_strict_readiness_contract(
			model_role_observability={},
			lane="fresh_query_interpretation",
		)

		self.assertEqual(readiness["readiness_status"], STATUS_MISSING_METADATA)
		self.assertFalse(readiness["strict_enforcement_ready"])
		self.assertTrue(readiness["blocking"])
		self.assertIn("model_role_observability", readiness["missing_fields"])

	def test_unknown_ai_runtime_metadata_blocks_strict_readiness(self):
		observability = build_model_role_observability_contract(
			lane="business_reasoning_answer",
			role_owner="business_reasoning_renderer",
			model_role=ROLE_HEAVY_REASONING,
			model_name="unknown",
			fallback_used=False,
			runtime_source="heavy_reasoning_runtime",
		)

		readiness = build_model_role_strict_readiness_contract(
			model_role_observability=observability,
			lane="business_reasoning_answer",
		)

		self.assertEqual(readiness["readiness_status"], STATUS_UNKNOWN_RUNTIME)
		self.assertTrue(readiness["blocking"])
		self.assertIn("model_name", readiness["missing_fields"])

	def test_fallback_state_blocks_strict_readiness_even_when_role_matches(self):
		observability = build_model_role_observability_contract(
			lane="nbu_shadow_observation",
			role_owner="natural_business_understanding_shadow_runtime",
			model_role=ROLE_SHADOW_OBSERVER,
			agent_meta={
				"model_name": "qwen-light-semantic",
				"fallback_used": True,
				"fallback_reason": "runtime_timeout",
			},
			runtime_source="nbu_runtime_response_agent_meta",
		)

		readiness = build_model_role_strict_readiness_contract(
			model_role_observability=observability,
			lane="nbu_shadow_observation",
		)

		self.assertEqual(readiness["readiness_status"], STATUS_FALLBACK_UNTRACKED)
		self.assertTrue(readiness["fallback_observed"])
		self.assertTrue(readiness["blocking"])

	def test_role_mismatch_blocks_strict_readiness(self):
		observability = build_model_role_observability_contract(
			lane="business_reasoning_answer",
			role_owner="business_reasoning_renderer",
			model_role="light_semantic",
			model_name="qwen-light-semantic",
			fallback_used=False,
			runtime_source="business_reasoning_runtime",
		)

		readiness = build_model_role_strict_readiness_contract(
			model_role_observability=observability,
			lane="business_reasoning_answer",
		)

		self.assertEqual(readiness["readiness_status"], STATUS_ROLE_MISMATCH)
		self.assertTrue(readiness["blocking"])
		self.assertFalse(readiness["strict_enforcement_ready"])

	def test_summary_reports_missing_lanes_before_global_strict_enforcement(self):
		observed = [
			build_model_role_observability_contract(
				lane="visible_context_followup",
				role_owner="visible_context_followup_activation",
				model_role=ROLE_DETERMINISTIC,
				model_name="none",
				fallback_used=False,
				runtime_source="deterministic_visible_context_contract",
			),
			build_model_role_observability_contract(
				lane="nbu_shadow_observation",
				role_owner="natural_business_understanding_shadow_runtime",
				model_role=ROLE_SHADOW_OBSERVER,
				agent_meta={"model_name": "qwen-light-semantic", "fallback_used": False},
				runtime_source="nbu_runtime_response_agent_meta",
			),
		]

		summary = build_model_role_strict_readiness_summary(
			observed_contracts=observed,
			required_lanes=[
				"visible_context_followup",
				"nbu_shadow_observation",
				"business_reasoning_answer",
			],
		)

		self.assertEqual(summary["type"], "qwen_model_role_strict_readiness_summary_contract")
		self.assertEqual(summary["ready_for_strict_count"], 1)
		self.assertEqual(summary["deterministic_exempt_count"], 1)
		self.assertEqual(summary["blocking_lane_count"], 1)
		self.assertEqual(summary["blocking_lanes"], ["business_reasoning_answer"])
		self.assertEqual(summary["status_counts"][STATUS_MISSING_METADATA], 1)


if __name__ == "__main__":
	unittest.main()
