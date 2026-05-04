import time
import unittest

from ai_assistant_ui.qwen_chat.evaluation.bounded_release_gate import (
	BoundedSmokeCase,
	build_bounded_release_gate_cases,
	bounded_release_gate_inventory,
	run_bounded_release_gate,
	run_bounded_smoke_cases,
	_signal_timeout_supported,
)


class TestBoundedReleaseGate(unittest.TestCase):
	def test_run_bounded_smoke_cases_reports_passed_cases(self):
		cases = [
			BoundedSmokeCase(
				case_id="a",
				label="A",
				group="unit",
				runner=lambda: {"ok": True, "answer": "passed"},
				timeout_seconds=2,
			),
			BoundedSmokeCase(
				case_id="b",
				label="B",
				group="unit",
				runner=lambda: {"ok": True, "answer": "passed"},
				timeout_seconds=2,
			),
		]

		result = run_bounded_smoke_cases(
			cases=cases,
			profile="unit",
			fail_fast=True,
		)

		self.assertEqual(result["ok"], True)
		self.assertEqual(result["total_planned"], 2)
		self.assertEqual(result["total_run"], 2)
		self.assertEqual(result["passed"], 2)
		self.assertEqual(result["first_failure"], {})

	def test_fail_fast_stops_after_first_failure(self):
		run_order = []

		def _fail():
			run_order.append("fail")
			raise RuntimeError("shared seam failed")

		def _later():
			run_order.append("later")
			return {"ok": True}

		result = run_bounded_smoke_cases(
			cases=[
				BoundedSmokeCase(
					case_id="fail",
					label="Fail",
					group="unit",
					runner=_fail,
					timeout_seconds=2,
				),
				BoundedSmokeCase(
					case_id="later",
					label="Later",
					group="unit",
					runner=_later,
					timeout_seconds=2,
				),
			],
			profile="unit",
			fail_fast=True,
		)

		self.assertEqual(result["ok"], False)
		self.assertEqual(result["total_planned"], 2)
		self.assertEqual(result["total_run"], 1)
		self.assertEqual(result["failed"], 1)
		self.assertEqual(result["first_failure"]["case_id"], "fail")
		self.assertEqual(run_order, ["fail"])

	def test_fail_fast_false_continues_after_failure(self):
		result = run_bounded_smoke_cases(
			cases=[
				BoundedSmokeCase(
					case_id="bad",
					label="Bad",
					group="unit",
					runner=lambda: {"ok": False, "error": "not green"},
					timeout_seconds=2,
				),
				BoundedSmokeCase(
					case_id="good",
					label="Good",
					group="unit",
					runner=lambda: {"ok": True},
					timeout_seconds=2,
				),
			],
			profile="unit",
			fail_fast=False,
		)

		self.assertEqual(result["ok"], False)
		self.assertEqual(result["total_run"], 2)
		self.assertEqual(result["failed"], 1)
		self.assertEqual(result["passed"], 1)

	def test_profile_builder_requires_registered_smokes(self):
		with self.assertRaisesRegex(ValueError, "missing smoke"):
			build_bounded_release_gate_cases(
				registry={},
				profile="stabilization_fast",
			)

	def test_run_bounded_release_gate_uses_named_profile(self):
		registry = {
			"phase1_1_invoice_delivery_proof": lambda: {"ok": True},
			"phase1_1_fresh_chat_invoice_delivery_proof": lambda: {"ok": True},
			"phase1_2_sales_order_status_followup": lambda: {"ok": True},
			"phase1_3_purchase_order_status_followup": lambda: {"ok": True},
			"nbu_governed_requery": lambda: {"ok": True},
		}

		result = run_bounded_release_gate(
			registry=registry,
			profile="stabilization_fast",
			fail_fast=True,
			timeout_seconds=2,
		)

		self.assertEqual(result["ok"], True)
		self.assertEqual(result["total_planned"], 5)
		self.assertEqual(result["passed"], 5)

	def test_inventory_exposes_profiles_without_running_smokes(self):
		inventory = bounded_release_gate_inventory()

		self.assertEqual(inventory["ok"], True)
		self.assertIn("stabilization_fast", inventory["profiles"])
		self.assertIn("phase1_document_detail", inventory["profiles"])
		self.assertIn("phase1_order_followup", inventory["profiles"])
		self.assertIn("phase1_customer_credit", inventory["profiles"])
		self.assertIn("release_sanity", inventory["profiles"])
		self.assertIn("post_contract_phase55", inventory["profiles"])
		self.assertIn("post_contract_phase6", inventory["profiles"])
		self.assertIn("post_contract_phase6_aggregate", inventory["profiles"])
		self.assertIn("post_contract_phase6_grounded_source_reset", inventory["profiles"])
		self.assertIn("post_contract_phase7", inventory["profiles"])
		self.assertIn("post_contract_phase7_aggregate", inventory["profiles"])
		self.assertIn("post_contract_phase7_live_boundary_orchestration", inventory["profiles"])
		self.assertIn("post_contract_phase8", inventory["profiles"])
		self.assertIn("post_contract_phase8_aggregate", inventory["profiles"])
		self.assertIn("post_contract_phase8_recovery_execution", inventory["profiles"])
		self.assertIn("nbu_s7_regression_matrix", inventory["profiles"])
		self.assertIn("nbu_s7_context_matrix", inventory["profiles"])
		self.assertIn("nbu_s7_projection_matrix", inventory["profiles"])
		self.assertIn("nbu_s7_boundary_recovery_matrix", inventory["profiles"])
		self.assertGreater(inventory["profile_timeout_budget_seconds"]["phase1_core"], 0)
		self.assertGreater(inventory["profile_timeout_budget_seconds"]["post_contract_suites"], 0)

	def test_phase1_segmented_profiles_cover_phase1_core(self):
		inventory = bounded_release_gate_inventory()
		profiles = inventory["profiles"]

		core_case_ids = [
			item["case_id"]
			for item in profiles["phase1_core"]
		]
		segmented_case_ids = [
			item["case_id"]
			for profile_name in [
				"phase1_document_detail",
				"phase1_order_followup",
				"phase1_customer_credit",
			]
			for item in profiles[profile_name]
		]

		self.assertEqual(segmented_case_ids, core_case_ids)

	def test_post_contract_phase6_profile_uses_atomic_cases(self):
		inventory = bounded_release_gate_inventory()
		profiles = inventory["profiles"]

		phase6_atomic_case_ids = [
			item["case_id"]
			for item in profiles["post_contract_phase6"]
		]
		expected_case_ids = [
			"phase6_recommendation_policy_probe",
			"phase6_reasoning_live_rollout",
			"phase6_reasoning_without_grounding",
			"phase6_reasoning_frontdoor_boundary",
			"phase6_nonadvisory_recommendation_boundary",
			"phase6_artifact_refinement_precedence",
			"phase6_continuation_fulfillment",
			"phase6_grounded_source_reset",
			"phase6_continuation_guardrail",
			"phase6_observability",
		]

		self.assertEqual(phase6_atomic_case_ids, expected_case_ids)
		self.assertNotIn("phase6_hardening_suite", phase6_atomic_case_ids)
		self.assertEqual(
			[item["case_id"] for item in profiles["post_contract_phase6_aggregate"]],
			["phase6_hardening_suite"],
		)

	def test_post_contract_phase7_profile_uses_atomic_cases(self):
		inventory = bounded_release_gate_inventory()
		profiles = inventory["profiles"]

		phase7_atomic_case_ids = [
			item["case_id"]
			for item in profiles["post_contract_phase7"]
		]

		self.assertEqual(
			phase7_atomic_case_ids,
			[
				"phase7_live_boundary_orchestration",
				"phase7_boundary_response_live",
			],
		)
		self.assertNotIn("phase7_hardening_suite", phase7_atomic_case_ids)
		self.assertEqual(
			[item["case_id"] for item in profiles["post_contract_phase7_aggregate"]],
			["phase7_hardening_suite"],
		)

	def test_post_contract_phase8_profile_uses_atomic_cases(self):
		inventory = bounded_release_gate_inventory()
		profiles = inventory["profiles"]

		phase8_atomic_case_ids = [
			item["case_id"]
			for item in profiles["post_contract_phase8"]
		]

		self.assertEqual(
			phase8_atomic_case_ids,
			[
				"phase8_recovery_authority",
				"phase8_repair_handling",
				"phase8_fresh_query_override",
				"phase8_recovery_execution",
			],
		)
		self.assertNotIn("phase8_hardening_suite", phase8_atomic_case_ids)
		self.assertEqual(
			[item["case_id"] for item in profiles["post_contract_phase8_aggregate"]],
			["phase8_hardening_suite"],
		)

	def test_nbu_s7_regression_matrix_profiles_are_segmented(self):
		inventory = bounded_release_gate_inventory()
		profiles = inventory["profiles"]

		self.assertEqual(
			[item["case_id"] for item in profiles["nbu_s7_context_matrix"]],
			[
				"nbu_s7_same_session_fresh_query",
				"nbu_s7_visible_context_latest_artifact",
				"nbu_governed_requery",
			],
		)
		self.assertEqual(
			[item["case_id"] for item in profiles["nbu_s7_projection_matrix"]],
			[
				"nbu_s7_subject_switch",
				"nbu_s7_ranking_projection_continuation",
				"nbu_s7_product_quantity_projection",
			],
		)
		self.assertEqual(
			[item["case_id"] for item in profiles["nbu_s7_boundary_recovery_matrix"]],
			[
				"nbu_s7_safe_boundary_language",
				"phase8_fresh_query_override",
				"phase8_recovery_execution",
				"h4_recommendation_guarantee",
			],
		)

		segmented_case_ids = [
			item["case_id"]
			for profile_name in [
				"nbu_s7_context_matrix",
				"nbu_s7_projection_matrix",
				"nbu_s7_boundary_recovery_matrix",
			]
			for item in profiles[profile_name]
		]
		self.assertEqual(
			[item["case_id"] for item in profiles["nbu_s7_regression_matrix"]],
			segmented_case_ids,
		)

	@unittest.skipUnless(_signal_timeout_supported(), "signal timeout is only enforced on Unix main thread")
	def test_signal_timeout_marks_case_as_timed_out(self):
		result = run_bounded_smoke_cases(
			cases=[
				BoundedSmokeCase(
					case_id="slow",
					label="Slow",
					group="unit",
					runner=lambda: time.sleep(0.2) or {"ok": True},
					timeout_seconds=0.01,
				)
			],
			profile="unit",
			fail_fast=True,
		)

		self.assertEqual(result["ok"], False)
		self.assertEqual(result["timed_out"], 1)
		self.assertEqual(result["first_failure"]["status"], "timeout")


if __name__ == "__main__":
	unittest.main()
