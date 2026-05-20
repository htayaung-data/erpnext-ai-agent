import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	COMPLIANCE_COMPLIANT,
	COMPLIANCE_NOT_APPLICABLE,
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_POLICY_BOUNDARY,
	METADATA_STATUS_COVERED,
	METADATA_STATUS_MISSING,
	ROLE_CONTROL_META,
	ROLE_DETERMINISTIC,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_LIGHT_SEMANTIC,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	STRICT_STATUS_NOT_APPLICABLE,
	STRICT_STATUS_NOT_READY_MISSING_METADATA,
	STRICT_STATUS_READY,
	STRICT_STATUS_SOFT_BLOCK,
)
from ai_assistant_ui.qwen_chat.strict_readiness_soft_gate import (
	NOT_APPLICABLE_CONTROL,
	NOT_APPLICABLE_DETERMINISTIC,
	RUNTIME_EFFECT_NONE,
	SOFT_GATE_BLOCK_RELEASE,
	SOFT_GATE_PASS,
	SOFT_GATE_WARN,
	ASSISTANT_APPEND_NEEDLE,
	build_strict_readiness_soft_gate_dry_run_report,
	classify_soft_gate_lane,
	default_lane_evidence_rows,
	raw_assistant_append_scan,
)


def _ai_row(**overrides):
	row = {
		"lane_id": "frontdoor_semantic_classification",
		"lane_class": LANE_CLASS_AI_SEMANTIC,
		"model_role": ROLE_LIGHT_SEMANTIC,
		"metadata_status": METADATA_STATUS_COVERED,
		"strict_readiness_status": STRICT_STATUS_READY,
		"strict_enforcement_ready": True,
		"fallback_used": False,
		"fallback_reason": "",
		"role_compliance": COMPLIANCE_COMPLIANT,
		"authority_source": "semantic_runtime_metadata",
		"final_answer_authority_status": "not_applicable",
		"final_answer_authority_source": "not_applicable",
		"preflight_status": "passed",
		"probe_evidence_slice": "EC-7F-B",
	}
	row.update(overrides)
	return row


class StrictReadinessSoftGateTests(unittest.TestCase):
	def test_complete_ai_provenance_can_pass_without_runtime_effect(self):
		row = classify_soft_gate_lane(_ai_row())

		self.assertEqual(row["soft_gate_decision"], SOFT_GATE_PASS)
		self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertEqual(row["release_readiness_impact"], "pass")

	def test_degraded_or_missing_ai_metadata_warns_without_runtime_block(self):
		fallback = classify_soft_gate_lane(
			_ai_row(
				strict_readiness_status=STRICT_STATUS_SOFT_BLOCK,
				strict_enforcement_ready=False,
				fallback_used=True,
				fallback_reason="semantic_status_low_confidence",
			)
		)
		missing = classify_soft_gate_lane(
			_ai_row(
				metadata_status=METADATA_STATUS_MISSING,
				strict_readiness_status=STRICT_STATUS_NOT_READY_MISSING_METADATA,
				strict_enforcement_ready=False,
			)
		)

		self.assertEqual(fallback["soft_gate_decision"], SOFT_GATE_WARN)
		self.assertEqual(missing["soft_gate_decision"], SOFT_GATE_WARN)
		self.assertEqual(fallback["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertEqual(missing["runtime_effect"], RUNTIME_EFFECT_NONE)

	def test_ai_claiming_strict_ready_with_fallback_blocks_release_only(self):
		row = classify_soft_gate_lane(_ai_row(fallback_used=True, fallback_reason="runtime_timeout"))

		self.assertEqual(row["soft_gate_decision"], SOFT_GATE_BLOCK_RELEASE)
		self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertEqual(row["release_readiness_impact"], "release_blocking")

	def test_deterministic_lane_classifies_not_applicable_deterministic(self):
		row = classify_soft_gate_lane(
			{
				"lane_id": "compiled_support_result_answer",
				"lane_class": LANE_CLASS_DETERMINISTIC_REPORT,
				"model_role": ROLE_DETERMINISTIC,
				"metadata_status": METADATA_STATUS_COVERED,
				"strict_readiness_status": STRICT_STATUS_NOT_APPLICABLE,
				"strict_enforcement_ready": False,
				"fallback_used": False,
				"role_compliance": COMPLIANCE_NOT_APPLICABLE,
				"authority_source": "governed_erp_report",
				"final_answer_authority_status": "passed",
				"final_answer_authority_source": "governed_erp_report",
				"preflight_status": "passed",
				"probe_evidence_slice": "EC-7F-E",
			}
		)

		self.assertEqual(row["soft_gate_decision"], NOT_APPLICABLE_DETERMINISTIC)
		self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)

	def test_policy_control_and_error_lanes_classify_not_applicable_control(self):
		policy = classify_soft_gate_lane(
			{
				"lane_id": "runtime_gate",
				"lane_class": LANE_CLASS_POLICY_BOUNDARY,
				"model_role": ROLE_POLICY_BOUNDARY,
				"metadata_status": METADATA_STATUS_COVERED,
				"strict_readiness_status": STRICT_STATUS_NOT_APPLICABLE,
				"strict_enforcement_ready": False,
				"fallback_used": False,
				"role_compliance": COMPLIANCE_NOT_APPLICABLE,
				"authority_source": "policy_boundary",
				"final_answer_authority_status": "bounded",
				"final_answer_authority_source": "policy_boundary",
				"preflight_status": "bounded",
			}
		)
		control = classify_soft_gate_lane(
			{
				"lane_id": "clarification_control",
				"lane_class": LANE_CLASS_CONTROL_META,
				"model_role": ROLE_CONTROL_META,
				"metadata_status": METADATA_STATUS_COVERED,
				"strict_readiness_status": STRICT_STATUS_NOT_APPLICABLE,
				"strict_enforcement_ready": False,
				"fallback_used": False,
				"role_compliance": COMPLIANCE_NOT_APPLICABLE,
				"authority_source": "control_meta",
				"final_answer_authority_status": "passed",
				"final_answer_authority_source": "control_meta",
				"preflight_status": "passed",
			}
		)
		error = classify_soft_gate_lane(
			{
				"lane_id": "legacy_runtime_error",
				"lane_class": LANE_CLASS_ERROR_FALLBACK,
				"model_role": ROLE_NOT_APPLICABLE,
				"metadata_status": METADATA_STATUS_COVERED,
				"strict_readiness_status": STRICT_STATUS_NOT_APPLICABLE,
				"strict_enforcement_ready": False,
				"fallback_used": False,
				"role_compliance": COMPLIANCE_NOT_APPLICABLE,
				"authority_source": "error_fallback",
				"final_answer_authority_status": "passed",
				"final_answer_authority_source": "error_fallback",
				"preflight_status": "passed",
			}
		)

		self.assertEqual(policy["soft_gate_decision"], NOT_APPLICABLE_CONTROL)
		self.assertEqual(control["soft_gate_decision"], NOT_APPLICABLE_CONTROL)
		self.assertEqual(error["soft_gate_decision"], NOT_APPLICABLE_CONTROL)

	def test_helper_and_tool_provenance_cannot_satisfy_final_answer_business_authority(self):
		for lane_class, role in (
			(LANE_CLASS_MODEL_BACKED_HELPER, ROLE_MODEL_BACKED_HELPER),
			(LANE_CLASS_GOVERNED_TOOL_RUNTIME, ROLE_GOVERNED_TOOL_RUNTIME),
		):
			row = classify_soft_gate_lane(
				{
					"lane_id": "helper_authority_probe",
					"lane_class": lane_class,
					"model_role": role,
					"metadata_status": METADATA_STATUS_COVERED,
					"strict_readiness_status": STRICT_STATUS_READY,
					"strict_enforcement_ready": True,
					"fallback_used": False,
					"role_compliance": COMPLIANCE_COMPLIANT,
					"authority_source": "governed_erp_report",
					"final_answer_authority_status": "satisfied_by_helper_metadata",
					"final_answer_authority_source": "governed_erp_report",
					"preflight_status": "passed",
				}
			)
			self.assertEqual(row["soft_gate_decision"], SOFT_GATE_BLOCK_RELEASE)
			self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)

	def test_final_answer_authority_failure_blocks_release(self):
		row = classify_soft_gate_lane(
			_ai_row(
				final_answer_authority_status="missing_authority",
				final_answer_authority_source="none",
			)
		)

		self.assertEqual(row["soft_gate_decision"], SOFT_GATE_BLOCK_RELEASE)
		self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)

	def test_direct_assistant_append_regression_becomes_release_blocker(self):
		report = build_strict_readiness_soft_gate_dry_run_report(
			branch="test",
			head="head",
			lane_rows=[],
			inventory_report={
				"active_runtime_direct_assistant_append_count": 1,
				"inventory_count": 2,
				"migrated_authorized_paths": [],
				"authorized_runtime_append_sink_count": 2,
				"excluded_non_runtime_append_count": 1,
			},
			raw_scan_rows=[],
		)

		self.assertEqual(report["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertFalse(report["strict_enforcement_enabled"])
		self.assertEqual(report["summary_counts"][SOFT_GATE_BLOCK_RELEASE], 1)
		self.assertEqual(report["release_blockers"][0]["lane_id"], "direct_assistant_append_inventory_regression")

	def test_raw_append_outside_authorized_emission_blocks_release_readiness(self):
		report = build_strict_readiness_soft_gate_dry_run_report(
			branch="test",
			head="head",
			lane_rows=[],
			inventory_report={
				"active_runtime_direct_assistant_append_count": 0,
				"inventory_count": 1,
				"migrated_authorized_paths": [{}] * 27,
				"authorized_runtime_append_sink_count": 2,
				"excluded_non_runtime_append_count": 1,
			},
			raw_scan_rows=[
				{
					"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/surprise_lane.py",
					"line": 99,
					"source": 'append_message(session_doc, "assistant", payload)',
				}
			],
		)

		self.assertFalse(report["strict_enforcement_enabled"])
		self.assertEqual(report["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertEqual(report["summary_counts"][SOFT_GATE_BLOCK_RELEASE], 1)
		self.assertEqual(report["release_blockers"][0]["lane_id"], "raw_assistant_append_scan_regression")

	def test_formal_raw_append_scan_finds_only_authorized_emission_sinks(self):
		self.assertEqual(ASSISTANT_APPEND_NEEDLE, 'append_message(session_doc, "assistant"')
		repo_root = next(parent for parent in Path(__file__).resolve().parents if (parent / "impl_factory").exists())

		rows = raw_assistant_append_scan(root_path=repo_root)
		observed = [
			(row["relative_file_path"].replace("\\", "/"), row["line"])
			for row in rows
		]

		self.assertEqual(
			observed,
			[
				(
					"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py",
					271,
				),
				(
					"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py",
					327,
				),
			],
		)

	def test_report_shape_has_required_fields_and_no_runtime_effect(self):
		report = build_strict_readiness_soft_gate_dry_run_report(
			branch="test",
			head="head",
			lane_rows=default_lane_evidence_rows(),
			inventory_report={
				"active_runtime_direct_assistant_append_count": 0,
				"inventory_count": 1,
				"migrated_authorized_paths": [{}] * 27,
				"authorized_runtime_append_sink_count": 2,
				"excluded_non_runtime_append_count": 1,
			},
			raw_scan_rows=[
				{
					"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py",
					"line": 271,
					"source": 'append_message(session_doc, "assistant", assistant_text_payload(answer_text))',
				}
			],
		)
		self.assertFalse(report["strict_enforcement_enabled"])
		self.assertEqual(report["runtime_effect"], RUNTIME_EFFECT_NONE)
		self.assertIn("direct_assistant_append_inventory", report)
		self.assertIn("raw_assistant_append_scan", report)
		self.assertIn("ec7f_probe_closure_evidence", report)
		self.assertEqual(report["direct_assistant_append_inventory"]["migrated_authorized_paths_length"], 27)
		for row in report["lane_results"]:
			self.assertEqual(row["runtime_effect"], RUNTIME_EFFECT_NONE)
			for field in (
				"lane_id",
				"lane_class",
				"model_role",
				"expected_lane_class",
				"expected_model_role",
				"metadata_status",
				"strict_readiness_status",
				"strict_enforcement_ready",
				"fallback_used",
				"fallback_reason",
				"role_compliance",
				"authority_source",
				"final_answer_authority_status",
				"final_answer_authority_source",
				"preflight_status",
				"probe_evidence_slice",
				"soft_gate_decision",
				"reason",
				"release_readiness_impact",
				"observed_metadata",
				"expected_metadata",
				"runtime_effect",
			):
				self.assertIn(field, row)
			self.assertIsInstance(row["observed_metadata"], dict)
			self.assertIsInstance(row["expected_metadata"], dict)
			self.assertIn("metadata_status", row["observed_metadata"])
			self.assertIn("metadata_status", row["expected_metadata"])


if __name__ == "__main__":
	unittest.main()
