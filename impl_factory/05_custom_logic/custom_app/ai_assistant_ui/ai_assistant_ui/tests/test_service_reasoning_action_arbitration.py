import types
import unittest

from ai_assistant_ui.qwen_chat.service import (
	build_scope_decision_input,
	_context_isolation_should_yield_to_prior_reasoning_action,
	_fresh_query_should_skip_pre_frontdoor_reasoning,
	_message_should_override_stale_context_as_fresh_query,
)


class ServiceReasoningActionArbitrationTests(unittest.TestCase):
	def test_self_contained_ranking_query_skips_prior_artifact_reasoning(self):
		self.assertTrue(
			_message_should_override_stale_context_as_fresh_query(
				message="Top 7 Customers by Revenue Last Year",
				language="en",
			)
		)
		self.assertTrue(
			_fresh_query_should_skip_pre_frontdoor_reasoning(
				fresh_governed_query_override_requested=True,
				prior_offered_next_action_available=False,
			)
		)

	def test_prior_executable_next_action_can_keep_context(self):
		self.assertFalse(
			_fresh_query_should_skip_pre_frontdoor_reasoning(
				fresh_governed_query_override_requested=True,
				prior_offered_next_action_available=True,
			)
		)

	def test_prior_executable_reasoning_action_beats_contradictory_fresh_query_guess(self):
		context_isolation = build_scope_decision_input(
			force_new_query=True,
			out_of_scope=False,
			reason="A presentation-only semantic payload carried conflicting query slots.",
		)
		reasoning_semantic_result = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="continuation_detail"),
		)
		latest_reasoning_contract = {
			"offered_next_actions": [
				{
					"action_id": "compare_listed_parties_by_overdue_and_intensity",
					"execution_mode": "current_governed_artifact",
				}
			]
		}

		self.assertTrue(
			_context_isolation_should_yield_to_prior_reasoning_action(
				context_isolation=context_isolation,
				reasoning_semantic_result=reasoning_semantic_result,
				latest_reasoning_contract=latest_reasoning_contract,
			)
		)

	def test_prior_reasoning_action_does_not_override_out_of_scope_boundary(self):
		context_isolation = build_scope_decision_input(
			force_new_query=True,
			out_of_scope=True,
			reason="The request is outside governed ERP support.",
		)
		reasoning_semantic_result = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="continuation_detail"),
		)
		latest_reasoning_contract = {
			"offered_next_actions": [
				{
					"action_id": "compare_listed_parties_by_overdue_and_intensity",
					"execution_mode": "current_governed_artifact",
				}
			]
		}

		self.assertFalse(
			_context_isolation_should_yield_to_prior_reasoning_action(
				context_isolation=context_isolation,
				reasoning_semantic_result=reasoning_semantic_result,
				latest_reasoning_contract=latest_reasoning_contract,
			)
		)


if __name__ == "__main__":
	unittest.main()
