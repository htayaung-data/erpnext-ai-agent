import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke,
	run_h3_clarification_preempts_recovery_smoke,
	run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke,
	run_h3_duplicate_recovery_acceptance_smoke,
	run_h3_fresh_query_replaces_grounded_context_smoke,
	run_h3_latest_fresh_grounded_query_wins_smoke,
	run_h3_latest_seeded_recovery_wins_smoke,
	run_h3_newer_recovery_survives_older_consumed_recovery_smoke,
	run_h3_pending_override_replaces_with_new_grounded_context_smoke,
	run_h3_post_stop_clarification_repeat_smoke,
	run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke,
	run_h3_repeated_identical_fresh_query_replaces_grounding_smoke,
	run_h3_stale_recovery_invalidated_by_fresh_override_smoke,
)


class TestPostContractStateLive(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_duplicate_recovery_acceptance_smoke(self):
		self._assert_ok_tree(
			run_h3_duplicate_recovery_acceptance_smoke(),
			"h3_duplicate_recovery_acceptance",
		)

	def test_duplicate_acceptance_after_newer_recovery_execution_smoke(self):
		self._assert_ok_tree(
			run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke(),
			"h3_duplicate_acceptance_after_newer_recovery_execution",
		)

	def test_post_stop_clarification_repeat_smoke(self):
		self._assert_ok_tree(
			run_h3_post_stop_clarification_repeat_smoke(),
			"h3_post_stop_clarification_repeat",
		)

	def test_clarification_preempts_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_clarification_preempts_recovery_smoke(),
			"h3_clarification_preempts_recovery",
		)

	def test_clarification_resolution_does_not_resurrect_stale_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke(),
			"h3_clarification_resolution_does_not_resurrect_stale_recovery",
		)

	def test_fresh_query_replaces_grounded_context_smoke(self):
		self._assert_ok_tree(
			run_h3_fresh_query_replaces_grounded_context_smoke(),
			"h3_fresh_query_replaces_grounded_context",
		)

	def test_pending_override_replaces_with_new_grounded_context_smoke(self):
		self._assert_ok_tree(
			run_h3_pending_override_replaces_with_new_grounded_context_smoke(),
			"h3_pending_override_replaces_with_new_grounded_context",
		)

	def test_latest_fresh_grounded_query_wins_smoke(self):
		self._assert_ok_tree(
			run_h3_latest_fresh_grounded_query_wins_smoke(),
			"h3_latest_fresh_grounded_query_wins",
		)

	def test_latest_seeded_recovery_wins_smoke(self):
		self._assert_ok_tree(
			run_h3_latest_seeded_recovery_wins_smoke(),
			"h3_latest_seeded_recovery_wins",
		)

	def test_newer_recovery_survives_older_consumed_recovery_smoke(self):
		self._assert_ok_tree(
			run_h3_newer_recovery_survives_older_consumed_recovery_smoke(),
			"h3_newer_recovery_survives_older_consumed_recovery",
		)

	def test_repeated_identical_fresh_query_replaces_grounding_smoke(self):
		self._assert_ok_tree(
			run_h3_repeated_identical_fresh_query_replaces_grounding_smoke(),
			"h3_repeated_identical_fresh_query_replaces_grounding",
		)

	def test_repeated_identical_composite_grounded_query_replaces_grounding_smoke(self):
		self._assert_ok_tree(
			run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke(),
			"h3_repeated_identical_composite_grounded_query_replaces_grounding",
		)

	def test_stale_recovery_invalidated_by_fresh_override_smoke(self):
		self._assert_ok_tree(
			run_h3_stale_recovery_invalidated_by_fresh_override_smoke(),
			"h3_stale_recovery_invalidated_by_fresh_override",
		)
