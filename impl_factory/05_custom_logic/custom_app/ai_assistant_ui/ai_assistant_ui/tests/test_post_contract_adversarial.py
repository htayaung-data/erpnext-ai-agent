import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_h4_creative_followup_after_reasoning_is_refused_smoke,
	run_h4_inferred_operational_evidence_stays_bounded_smoke,
	run_h4_long_multisentence_followup_stays_bounded_smoke,
	run_h4_mixed_metric_request_stays_bounded_smoke,
	run_h4_recommendation_guarantee_stays_bounded_smoke,
)


class TestPostContractAdversarial(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_h4_inferred_operational_evidence_stays_bounded(self):
		self._assert_ok_tree(
			run_h4_inferred_operational_evidence_stays_bounded_smoke(),
			"h4_inferred_operational_evidence",
		)

	def test_h4_mixed_metric_request_stays_bounded(self):
		self._assert_ok_tree(
			run_h4_mixed_metric_request_stays_bounded_smoke(),
			"h4_mixed_metric_request",
		)

	def test_h4_long_multisentence_followup_stays_bounded(self):
		self._assert_ok_tree(
			run_h4_long_multisentence_followup_stays_bounded_smoke(),
			"h4_long_multisentence_followup",
		)

	def test_h4_creative_followup_after_reasoning_is_refused(self):
		self._assert_ok_tree(
			run_h4_creative_followup_after_reasoning_is_refused_smoke(),
			"h4_creative_followup_after_reasoning",
		)

	def test_h4_recommendation_guarantee_stays_bounded(self):
		self._assert_ok_tree(
			run_h4_recommendation_guarantee_stays_bounded_smoke(),
			"h4_recommendation_guarantee",
		)
