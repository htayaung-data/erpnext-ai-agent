import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_h5_release_gate_rollout_probe,
	run_h5_release_gate_sanity_pack,
)


class TestPostContractReleaseGates(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_h5_release_gate_rollout_probe(self):
		self._assert_ok_tree(
			run_h5_release_gate_rollout_probe(),
			"h5_release_gate_rollout_probe",
		)

	def test_h5_release_gate_sanity_pack(self):
		self._assert_ok_tree(
			run_h5_release_gate_sanity_pack(),
			"h5_release_gate_sanity_pack",
		)
