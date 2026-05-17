import unittest
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.service import (
	run_phase55_hardening_suite,
	run_phase6_hardening_suite,
	run_phase7_hardening_suite,
	run_phase8_hardening_suite,
)


class TestPostContractRegression(unittest.TestCase):
	def _assert_ok_tree(self, payload: Dict[str, Any], path: str) -> None:
		self.assertIsInstance(payload, dict, f"{path} must return a dict payload.")
		self.assertTrue(bool(payload.get("ok")), f"{path} did not report ok=True: {payload!r}")
		for key, value in payload.items():
			if key == "ok":
				continue
			if isinstance(value, dict) and "ok" in value:
				self._assert_ok_tree(value, f"{path}.{key}")

	def test_phase55_hardening_suite(self):
		self._assert_ok_tree(run_phase55_hardening_suite(), "phase55")

	def test_phase6_hardening_suite(self):
		self._assert_ok_tree(run_phase6_hardening_suite(), "phase6")

	def test_phase7_hardening_suite(self):
		self._assert_ok_tree(run_phase7_hardening_suite(), "phase7")

	def test_phase8_hardening_suite(self):
		self._assert_ok_tree(run_phase8_hardening_suite(), "phase8")
