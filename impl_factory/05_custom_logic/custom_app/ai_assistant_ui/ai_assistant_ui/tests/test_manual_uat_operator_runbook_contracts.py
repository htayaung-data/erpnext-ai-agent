import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_operator_runbook import (
	MANUAL_UAT_OPERATOR_RUNBOOK_CONTRACT_TYPE,
	MANUAL_UAT_OPERATOR_RUNBOOK_SUITE_ID,
	REQUIRED_BLOCKER_KEYS,
	REQUIRED_CONTRACT_REFERENCES,
	REQUIRED_RUNBOOK_SECTIONS,
	build_operator_evidence_runbook_contract,
	render_operator_evidence_runbook_markdown,
	write_operator_evidence_runbook_files,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)


class ManualUATOperatorRunbookContractTests(unittest.TestCase):
	def test_runbook_contract_contains_all_required_sections(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")

		self.assertEqual(contract["type"], MANUAL_UAT_OPERATOR_RUNBOOK_CONTRACT_TYPE)
		self.assertTrue(contract["runbook_complete"])
		self.assertEqual(contract["missing_sections"], [])
		self.assertEqual(contract["missing_blocker_keys"], [])
		self.assertEqual(contract["required_sections"], REQUIRED_RUNBOOK_SECTIONS)
		self.assertEqual({section["id"] for section in contract["sections"]}, set(REQUIRED_RUNBOOK_SECTIONS))

	def test_runbook_references_required_contract_authorities(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")

		for reference in REQUIRED_CONTRACT_REFERENCES:
			with self.subTest(reference=reference):
				self.assertIn(reference, contract["contract_references"])
		self.assertIn("qwen_manual_uat_operator_evidence_cli_contract", contract["contract_references"])
		self.assertIn("qwen_manual_uat_real_evidence_intake_contract", contract["contract_references"])

	def test_runbook_artifacts_include_capture_cli_intake_bundle_and_promotion_outputs(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")
		paths = contract["artifact_paths"]

		for key in [
			"operator_capture_template_markdown",
			"operator_capture_skeleton_json",
			"manual_browser_uat_pack_markdown",
			"operator_cli_report_markdown",
			"real_evidence_intake_json",
			"promotion_ready_bundle_markdown",
			"real_evidence_promotion_markdown",
		]:
			with self.subTest(path=key):
				self.assertIn(key, paths)
				self.assertTrue(paths[key])

	def test_command_examples_use_governed_cli_strict_and_overwrite_flags(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")
		commands = "\n".join(example["command"] for example in contract["command_examples"])

		self.assertIn("scripts/qwen_manual_uat_operator_evidence_import.py", commands)
		self.assertIn("--captures", commands)
		self.assertIn("--reviewer", commands)
		self.assertIn("--strict", commands)
		self.assertIn("--overwrite", commands)
		self.assertIn("--expected-scenarios-file", commands)

	def test_blocker_catalog_covers_required_operator_blockers(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")
		catalog = {entry["key"]: entry for entry in contract["blocker_catalog"]}

		for blocker in REQUIRED_BLOCKER_KEYS:
			with self.subTest(blocker=blocker):
				self.assertIn(blocker, catalog)
				self.assertTrue(catalog[blocker]["meaning"])
				self.assertTrue(catalog[blocker]["operator_action"])
		self.assertIn("sample_evidence_not_allowed", catalog)
		self.assertIn("promotion_not_release_ready", catalog)

	def test_forbidden_actions_prevent_unsafe_manual_shortcuts(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")
		text = "\n".join(contract["forbidden_actions"])

		self.assertIn("Do not edit generated CLI", text)
		self.assertIn("Do not use sample_fixture", text)
		self.assertIn("Do not remove blocker keys", text)
		self.assertIn("Do not bypass S7-6P", text)
		self.assertIn("operator_attestation", text)

	def test_markdown_renders_required_sections_commands_blockers_and_paths(self):
		contract = build_operator_evidence_runbook_contract(generated_at="2026-05-13T23:59:00+06:30")
		markdown = render_operator_evidence_runbook_markdown(contract)

		self.assertIn("# S7 Operator Evidence Bundle UAT Execution Runbook", markdown)
		self.assertIn("## Contract Authority", markdown)
		self.assertIn("## Command Examples", markdown)
		self.assertIn("## Blocker Catalog", markdown)
		self.assertIn("operator_attestation_missing", markdown)
		self.assertIn("qwen_s7_manual_uat_operator_capture_skeleton.json", markdown)
		self.assertIn("qwen_s7_operator_evidence_import_cli_report.md", markdown)
		self.assertIn("release_ready=True", markdown)

	def test_writer_is_deterministic(self):
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "runbook.json"
			markdown_path = Path(tmp) / "runbook.md"

			first = write_operator_evidence_runbook_files(
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-13T23:59:00+06:30",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_operator_evidence_runbook_files(
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-13T23:59:00+06:30",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertTrue(loaded["runbook_complete"])
			self.assertIn("Blocker Catalog", first_markdown)

	def test_s7_6q_operator_runbook_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_OPERATOR_RUNBOOK_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_OPERATOR_RUNBOOK_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_OPERATOR_RUNBOOK_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
