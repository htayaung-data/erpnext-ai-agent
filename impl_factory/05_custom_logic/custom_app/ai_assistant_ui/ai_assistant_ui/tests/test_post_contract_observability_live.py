import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_phase55_observability_smoke,
	run_phase6_observability_smoke,
	run_phase7_observability_smoke,
	run_phase8_enrichment_boundary_observability_smoke,
	run_phase8_evidence_boundary_observability_smoke,
	run_phase8_recovery_guidance_observability_smoke,
)


class TestPostContractObservabilityLive(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_phase55_live_observability_smoke(self):
		self._assert_ok_tree(run_phase55_observability_smoke(), "phase55_live_observability")

	def test_phase6_live_observability_smoke(self):
		self._assert_ok_tree(run_phase6_observability_smoke(), "phase6_live_observability")

	def test_phase7_live_observability_smoke(self):
		self._assert_ok_tree(run_phase7_observability_smoke(), "phase7_live_observability")

	def test_phase8_live_recovery_guidance_observability_smoke(self):
		self._assert_ok_tree(
			run_phase8_recovery_guidance_observability_smoke(),
			"phase8_live_recovery_guidance_observability",
		)

	def test_phase8_live_evidence_boundary_observability_smoke(self):
		self._assert_ok_tree(
			run_phase8_evidence_boundary_observability_smoke(),
			"phase8_live_evidence_boundary_observability",
		)

	def test_phase8_live_enrichment_boundary_observability_smoke(self):
		self._assert_ok_tree(
			run_phase8_enrichment_boundary_observability_smoke(),
			"phase8_live_enrichment_boundary_observability",
		)
