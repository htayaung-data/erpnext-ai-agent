import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_arbitration import (
	build_nbu_arbitration_decision,
	list_nbu_arbitration_activation_levels,
	list_nbu_arbitration_decisions,
	nbu_action_lane_for_action,
	nbu_activation_level_supports_action,
	summarize_nbu_arbitration_decisions,
	validate_nbu_arbitration_contract,
)


def _scorecard(
	*,
	outcome,
	nbu_passed=False,
	current_passed=False,
	nbu_action="answer_from_current_artifact",
	nbu_failure_buckets=None,
	current_failure_buckets=None,
	nbu_diagnostic_buckets=None,
	current_diagnostic_buckets=None,
):
	return {
		"type": "qwen_nbu_vs_current_router_scorecard",
		"case_id": "case-1",
		"scorecard_outcome": outcome,
		"nbu_passed": nbu_passed,
		"current_router_passed": current_passed,
		"nbu_actual_action": nbu_action,
		"current_router_actual_action": "execute_fresh_governed_query",
		"nbu_failure_buckets": nbu_failure_buckets or [],
		"current_router_failure_buckets": current_failure_buckets or [],
		"nbu_diagnostic_buckets": nbu_diagnostic_buckets or [],
		"current_router_diagnostic_buckets": current_diagnostic_buckets or [],
	}


class NaturalBusinessUnderstandingArbitrationTests(unittest.TestCase):
	def test_arbitration_contract_has_enterprise_decisions_and_activation_levels(self):
		validation = validate_nbu_arbitration_contract()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(validation["decision_count"], 5)
		self.assertEqual(validation["activation_level_count"], 6)
		decisions = {row["decision"] for row in list_nbu_arbitration_decisions()}
		levels = {row["activation_level"] for row in list_nbu_arbitration_activation_levels()}
		self.assertIn("trust_current_router", decisions)
		self.assertIn("trust_nbu", decisions)
		self.assertIn("fresh_query", levels)

	def test_both_correct_keeps_current_router_without_behavior_change(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="both_correct",
				nbu_passed=True,
				current_passed=True,
				nbu_action="execute_fresh_governed_query",
			)
		)

		self.assertEqual(arbitration["decision"], "trust_current_router")
		self.assertEqual(arbitration["selected_route_owner"], "current_router")
		self.assertFalse(arbitration["live_behavior_change_authorized"])
		self.assertFalse(arbitration["live_behavior_changed_by_fc2"])

	def test_action_lane_support_is_shared_for_activation_slices(self):
		self.assertEqual(nbu_action_lane_for_action("ask_clarification"), "presentation")
		self.assertEqual(nbu_action_lane_for_action("answer_from_current_artifact"), "current_artifact")

		presentation = nbu_activation_level_supports_action(
			action="ask_clarification",
			activation_level="presentation_only",
		)
		fresh_query = nbu_activation_level_supports_action(
			action="execute_fresh_governed_query",
			activation_level="presentation_only",
		)

		self.assertTrue(presentation["supported"])
		self.assertFalse(fresh_query["supported"])
		self.assertEqual(fresh_query["required_action_lane"], "fresh_query")

	def test_current_correct_nbu_wrong_keeps_current_router(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="current_correct_nbu_wrong",
				nbu_passed=False,
				current_passed=True,
			)
		)

		self.assertEqual(arbitration["decision"], "trust_current_router")
		self.assertIn("nbu_did_not_match_oracle", arbitration["blockers"])

	def test_nbu_correct_current_wrong_stays_shadow_until_lane_enabled(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_correct_current_wrong",
				nbu_passed=True,
				current_passed=False,
				nbu_action="execute_fresh_governed_query",
			),
			activation_level="shadow_only",
		)

		self.assertEqual(arbitration["decision"], "shadow_only")
		self.assertEqual(arbitration["selected_route_owner"], "current_router")
		self.assertIn("nbu_lane_not_enabled_for_activation_level", arbitration["blockers"])
		self.assertIn("nbu_would_win_if_lane_enabled", arbitration["warnings"])

	def test_nbu_correct_current_wrong_can_trust_presentation_when_level_allows(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_correct_current_wrong",
				nbu_passed=True,
				current_passed=False,
				nbu_action="ask_clarification",
			),
			activation_level="presentation_only",
		)

		self.assertEqual(arbitration["decision"], "trust_nbu")
		self.assertEqual(arbitration["selected_route_owner"], "nbu")
		self.assertEqual(arbitration["required_action_lane"], "presentation")
		self.assertTrue(arbitration["live_behavior_change_authorized"])
		self.assertFalse(arbitration["live_behavior_changed_by_fc2"])

	def test_governed_requery_lane_requires_governed_requery_activation(self):
		shadow = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_correct_current_wrong",
				nbu_passed=True,
				current_passed=False,
				nbu_action="execute_governed_requery",
			),
			activation_level="current_artifact_answer",
		)
		activated = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_correct_current_wrong",
				nbu_passed=True,
				current_passed=False,
				nbu_action="execute_governed_requery",
			),
			activation_level="governed_requery",
		)

		self.assertEqual(shadow["decision"], "shadow_only")
		self.assertEqual(shadow["required_action_lane"], "governed_requery")
		self.assertEqual(activated["decision"], "trust_nbu")
		self.assertTrue(activated["live_behavior_change_authorized"])

	def test_unsafe_nbu_fails_safely_when_current_not_correct(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_unsafe",
				nbu_passed=False,
				current_passed=False,
				nbu_failure_buckets=["renderer_quality_failure"],
			)
		)

		self.assertEqual(arbitration["decision"], "safe_boundary")
		self.assertEqual(arbitration["selected_route_owner"], "safe_boundary")
		self.assertIn("nbu_failed_safety_gate", arbitration["blockers"])

	def test_low_confidence_nbu_asks_clarification_when_no_route_is_proven(self):
		arbitration = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="nbu_low_confidence",
				nbu_passed=False,
				current_passed=False,
			)
		)

		self.assertEqual(arbitration["decision"], "ask_clarification")
		self.assertEqual(arbitration["selected_route_owner"], "clarification")
		self.assertIn("nbu_below_confidence_threshold", arbitration["blockers"])

	def test_both_wrong_asks_clarification_unless_policy_gap_requires_boundary(self):
		clarify = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(outcome="both_wrong")
		)
		boundary = build_nbu_arbitration_decision(
			scorecard_payload=_scorecard(
				outcome="both_wrong",
				nbu_diagnostic_buckets=["policy_evidence_gap"],
			)
		)

		self.assertEqual(clarify["decision"], "ask_clarification")
		self.assertEqual(boundary["decision"], "safe_boundary")

	def test_arbitration_summary_counts_decisions_and_authorized_changes(self):
		decisions = [
			build_nbu_arbitration_decision(
				scorecard_payload=_scorecard(outcome="both_correct", nbu_passed=True, current_passed=True)
			),
			build_nbu_arbitration_decision(
				scorecard_payload=_scorecard(
					outcome="nbu_correct_current_wrong",
					nbu_passed=True,
					current_passed=False,
					nbu_action="ask_clarification",
				),
				activation_level="presentation_only",
			),
		]

		summary = summarize_nbu_arbitration_decisions(decisions)

		self.assertEqual(summary["case_count"], 2)
		self.assertEqual(summary["decision_counts"]["trust_current_router"], 1)
		self.assertEqual(summary["decision_counts"]["trust_nbu"], 1)
		self.assertEqual(summary["selected_route_owner_counts"]["nbu"], 1)
		self.assertEqual(summary["authorized_behavior_change_count"], 1)
		self.assertEqual(summary["actual_behavior_change_count"], 0)


if __name__ == "__main__":
	unittest.main()
