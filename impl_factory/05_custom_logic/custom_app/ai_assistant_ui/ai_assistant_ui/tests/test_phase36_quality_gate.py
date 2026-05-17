from __future__ import annotations

from pathlib import Path
import unittest

from ai_assistant_ui.qwen_chat.evaluation.phase36_quality_gate import (
	PHASE36_EXIT_GATE_IDS,
	VALID_GATES,
	VALID_MODES,
	phase36_quality_gate_scenario_by_id,
	phase36_quality_gate_scenarios,
	phase36_quality_gate_summary,
	phase36_required_exit_gate_scenarios,
)


class TestPhase36QualityGate(unittest.TestCase):
	def test_all_phase36_exit_gate_rows_are_registered_once(self) -> None:
		scenario_ids = [scenario.scenario_id for scenario in phase36_required_exit_gate_scenarios()]
		self.assertEqual(set(scenario_ids), set(PHASE36_EXIT_GATE_IDS))
		self.assertEqual(len(scenario_ids), len(set(scenario_ids)))

	def test_phase36_scenarios_have_valid_gate_metadata(self) -> None:
		for scenario in phase36_quality_gate_scenarios():
			with self.subTest(scenario_id=scenario.scenario_id):
				self.assertIn(scenario.gate, VALID_GATES)
				self.assertIn(scenario.mode, VALID_MODES)
				self.assertTrue(scenario.group)
				self.assertTrue(scenario.prompt_sequence)
				self.assertTrue(scenario.expected_behavior)
				self.assertTrue(scenario.fallback_boundary)
				self.assertTrue(scenario.automation_layer)

	def test_phase36_a_gate_rows_have_contract_or_manual_guards(self) -> None:
		for scenario in phase36_required_exit_gate_scenarios():
			with self.subTest(scenario_id=scenario.scenario_id):
				if scenario.automated_guard_required:
					self.assertTrue(
						scenario.coverage_refs,
						f"{scenario.scenario_id} needs automated coverage refs.",
					)
				if scenario.manual_browser_required:
					self.assertTrue(scenario.manual_browser_required)
				self.assertNotEqual(scenario.coverage_state, "unmapped")

	def test_phase36_coverage_refs_point_to_existing_tests(self) -> None:
		tests_dir = Path(__file__).resolve().parent
		for scenario in phase36_required_exit_gate_scenarios():
			for coverage_ref in scenario.coverage_refs:
				with self.subTest(scenario_id=scenario.scenario_id, coverage_ref=coverage_ref):
					file_name, test_name = coverage_ref.split("::", 1)
					test_path = tests_dir / file_name
					self.assertTrue(test_path.exists(), f"Missing coverage file: {coverage_ref}")
					source = test_path.read_text(encoding="utf-8")
					self.assertIn(f"def {test_name}", source)

	def test_phase36_quality_gate_covers_all_business_user_aspects(self) -> None:
		expected_groups = {
			"master_data",
			"transaction_listing",
			"financial_statement",
			"composite_kpi_evidence",
			"followup_context",
			"wise_fallback",
			"presentation_live_data",
		}
		summary = phase36_quality_gate_summary()
		self.assertEqual(set((summary.get("groups") or {}).keys()), expected_groups)
		self.assertEqual(summary.get("required_exit_gate_count"), len(PHASE36_EXIT_GATE_IDS))
		self.assertGreater(summary.get("manual_browser_required_count"), 0)

	def test_phase36_authority_boundary_rows_stay_explicit(self) -> None:
		for scenario_id in ("CK-06", "CK-07", "CK-08", "WF-04", "WF-05"):
			scenario = phase36_quality_gate_scenario_by_id(scenario_id)
			self.assertIn("boundary", scenario.automation_layer)
			self.assertTrue(scenario.fallback_boundary)


if __name__ == "__main__":
	unittest.main()
