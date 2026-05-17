import unittest

from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_BACKLOG,
	BLOCKING_RELEASE,
	GATE_LEGACY_STABILIZATION_BACKLOG,
	GATE_RELEASE_BLOCKING_CONTRACT,
	GATE_RUNTIME_REQUIRED_SMOKE,
	REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_FRAPPE_SESSION,
	RUNTIME_NONE,
	STATUS_KNOWN_RED_CLASSIFIED,
	S7_REGRESSION_SUITE_REGISTRY,
	build_regression_suite_boundary_contract,
	build_regression_suite_entry_contract,
	regression_suite_missing_fields,
	release_blocking_regression_commands,
)


class RegressionSuiteGovernanceContractTests(unittest.TestCase):
	def test_every_registry_entry_has_required_boundary_fields(self):
		for entry in S7_REGRESSION_SUITE_REGISTRY:
			with self.subTest(entry=entry.get("suite_id")):
				self.assertEqual(regression_suite_missing_fields(entry), [])

	def test_boundary_contract_classifies_release_blocking_and_runtime_suites(self):
		contract = build_regression_suite_boundary_contract()

		self.assertEqual(contract["type"], REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE)
		self.assertTrue(contract["contract_complete"])
		self.assertGreaterEqual(contract["release_blocking_suite_count"], len(RELEASE_BLOCKING_SUITE_IDS))
		self.assertGreaterEqual(contract["runtime_required_suite_count"], 1)
		self.assertEqual(contract["missing_release_blocking_suites"], [])
		self.assertEqual(contract["duplicate_suite_ids"], [])
		self.assertEqual(contract["incomplete_entries"], [])
		self.assertIn("frappe_live_smoke_suites", contract["runtime_required_suites"])
		self.assertIn("s7_manual_browser_uat", contract["manual_uat_suites"])
		self.assertIn("semantic_financial_legacy_full_discovery", contract["known_red_classified_suites"])

	def test_release_blocking_suites_are_deterministic_and_blocking(self):
		contract = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in contract["entries"]}

		for suite_id in RELEASE_BLOCKING_SUITE_IDS:
			with self.subTest(suite_id=suite_id):
				entry = entries[suite_id]
				self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
				self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
				self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
				self.assertTrue(entry["release_blocking"])
				self.assertFalse(entry["runtime_required"])
				self.assertFalse(entry["allowed_skip_reason"])

	def test_operator_and_browser_evidence_suites_are_release_blocking_contracts(self):
		contract = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in contract["entries"]}

		for suite_id in (
			"s7_operator_evidence_import_cli_contracts",
			"s7_browser_batch_resilience_runner_contracts",
			"s7_browser_batch_cli_adapter_contracts",
		):
			with self.subTest(suite_id=suite_id):
				entry = entries[suite_id]
				self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
				self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
				self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
				self.assertTrue(entry["release_blocking"])
				self.assertIn("test_manual_uat_", entry["expected_command"])

		self.assertEqual(entries["s7_manual_browser_uat"]["runtime_dependency"], "browser_manual")
		self.assertFalse(entries["s7_manual_browser_uat"]["release_blocking"])

	def test_runtime_required_suites_are_not_misclassified_as_plain_unit_tests(self):
		contract = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in contract["entries"]}
		runtime_entry = entries["frappe_live_smoke_suites"]

		self.assertEqual(runtime_entry["gate_class"], GATE_RUNTIME_REQUIRED_SMOKE)
		self.assertEqual(runtime_entry["runtime_dependency"], RUNTIME_FRAPPE_SESSION)
		self.assertTrue(runtime_entry["runtime_required"])
		self.assertFalse(runtime_entry["release_blocking"])
		self.assertIn("frappe.new_doc", runtime_entry["allowed_skip_reason"])

	def test_legacy_red_full_discovery_suite_is_classified_not_ignored(self):
		contract = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in contract["entries"]}
		legacy_entry = entries["semantic_financial_legacy_full_discovery"]

		self.assertEqual(legacy_entry["gate_class"], GATE_LEGACY_STABILIZATION_BACKLOG)
		self.assertEqual(legacy_entry["blocking_level"], BLOCKING_BACKLOG)
		self.assertEqual(legacy_entry["last_verified_status"], STATUS_KNOWN_RED_CLASSIFIED)
		self.assertIn("Known broad legacy suite", legacy_entry["allowed_skip_reason"])
		self.assertFalse(legacy_entry["release_blocking"])

	def test_boundary_detects_missing_required_release_gate(self):
		registry = [
			entry
			for entry in S7_REGRESSION_SUITE_REGISTRY
			if entry.get("suite_id") != "s7_visible_context_contracts"
		]

		contract = build_regression_suite_boundary_contract(registry=registry)

		self.assertFalse(contract["contract_complete"])
		self.assertIn("s7_visible_context_contracts", contract["missing_release_blocking_suites"])

	def test_boundary_detects_duplicate_suite_ids(self):
		registry = list(S7_REGRESSION_SUITE_REGISTRY)
		registry.append(dict(S7_REGRESSION_SUITE_REGISTRY[0]))

		contract = build_regression_suite_boundary_contract(registry=registry)

		self.assertFalse(contract["contract_complete"])
		self.assertIn(S7_REGRESSION_SUITE_REGISTRY[0]["suite_id"], contract["duplicate_suite_ids"])

	def test_entry_contract_marks_incomplete_entries(self):
		entry = build_regression_suite_entry_contract(
			{
				"suite_id": "bad_entry",
				"test_paths": [],
				"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
			}
		)

		self.assertFalse(entry["entry_complete"])
		self.assertIn("expected_command", entry["missing_fields"])
		self.assertIn("runtime_dependency", entry["missing_fields"])

	def test_release_blocking_command_list_excludes_runtime_and_backlog_suites(self):
		commands = release_blocking_regression_commands()
		joined = "\n".join(commands)

		self.assertGreaterEqual(len(commands), len(RELEASE_BLOCKING_SUITE_IDS))
		self.assertIn("check_qwen_enterprise_guardrails.py", joined)
		self.assertIn("test_visible_context_followup_activation.py", joined)
		self.assertNotIn("test_post_contract_observability_live.py", joined)
		self.assertNotIn("test_semantic_financial_resolution.py", joined)


if __name__ == "__main__":
	unittest.main()
