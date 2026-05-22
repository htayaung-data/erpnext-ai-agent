import importlib.util
import json
import os
from pathlib import Path
from contextlib import redirect_stdout
import io
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[6]


def _load_script_module(name: str, relative_path: str):
	path = REPO_ROOT / relative_path
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	assert spec.loader is not None
	spec.loader.exec_module(module)
	return module


dataset_validator = _load_script_module(
	"validate_ec7h_synthetic_dataset",
	"scripts/validate_ec7h_synthetic_dataset.py",
)
archive_checker = _load_script_module(
	"check_ec7h_archive_readiness",
	"scripts/check_ec7h_archive_readiness.py",
)
environment_checker = _load_script_module(
	"check_ec7h_environment_readiness",
	"scripts/check_ec7h_environment_readiness.py",
)


def _valid_scenario(lane_id: str, index: int) -> dict:
	return {
		"scenario_id": f"ec7h_{lane_id}_{index:03d}",
		"lane_id": lane_id,
		"scenario_type": "accepted_success",
		"synthetic_prompt": f"Classify EC7H Synthetic request {index} for {lane_id}.",
		"synthetic_record_reference": f"EC7H_SYNTH_RECORD_{index:03d}",
		"expected_metadata_status": "covered",
		"expected_strict_readiness_status": "strict_ready",
		"expected_fallback_used": False,
		"expected_fallback_reason": "",
		"expected_authority_status": "not_applicable",
		"redaction_expectation": "no_raw_sensitive_values",
	}


def _valid_manifest() -> dict:
	return {
		"dataset_id": dataset_validator.EXPECTED_DATASET_ID,
		"data_classification": "synthetic_only",
		"schema_version": "1",
		"qa_owner": "qa_owner",
		"scenarios": [
			_valid_scenario(lane_id, index)
			for index, lane_id in enumerate(sorted(dataset_validator.REQUIRED_LANES), start=1)
		],
	}


class EC7ISetupSupportHarnessTests(unittest.TestCase):
	def test_valid_synthetic_dataset_manifest_passes(self):
		report = dataset_validator.validate_manifest(_valid_manifest())

		self.assertTrue(report["valid"])
		self.assertEqual(report["runtime_effect"], "none")
		self.assertEqual(report["dataset_id"], dataset_validator.EXPECTED_DATASET_ID)
		self.assertEqual(set(report["lane_coverage"]), dataset_validator.REQUIRED_LANES)
		self.assertEqual(report["violations"], [])

	def test_dataset_manifest_rejects_wrong_name_and_missing_lane(self):
		manifest = _valid_manifest()
		manifest["dataset_id"] = "WRONG_DATASET"
		manifest["scenarios"] = manifest["scenarios"][:-1]

		report = dataset_validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("dataset_id_mismatch:'WRONG_DATASET'", report["violations"])
		self.assertTrue(any(item.startswith("missing_lane_coverage:") for item in report["violations"]))

	def test_dataset_manifest_rejects_raw_business_identifiers(self):
		manifest = _valid_manifest()
		manifest["scenarios"][0]["synthetic_prompt"] = "Show Yoma Bank invoice SINV-0001"
		manifest["scenarios"][0]["synthetic_record_reference"] = "SINV-0001"

		report = dataset_validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("scenarios[0]:synthetic_prompt_raw_business_identifier", report["violations"])
		self.assertIn("scenarios[0]:synthetic_record_reference_raw_business_identifier", report["violations"])

	def test_dataset_manifest_rejects_raw_identifiers_even_with_synthetic_marker(self):
		manifest = _valid_manifest()
		manifest["scenarios"][0][
			"synthetic_prompt"
		] = "EC7H Synthetic request for Yoma Bank invoice SINV-0001"
		manifest["scenarios"][0]["synthetic_record_reference"] = "EC7H Synthetic Myanmar Apex Co Ltd"
		manifest["scenarios"][0]["metadata_note"] = "Vendor value Myanmar Apex Co Ltd"

		report = dataset_validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("scenarios[0]:synthetic_prompt_raw_business_identifier", report["violations"])
		self.assertIn("scenarios[0]:synthetic_record_reference_raw_business_identifier", report["violations"])
		self.assertIn("scenarios[0]:metadata_note_raw_business_identifier", report["violations"])

	def test_dataset_manifest_rejects_document_ids_hidden_after_synthetic_prefix(self):
		manifest = _valid_manifest()
		manifest["scenarios"][0]["synthetic_record_reference"] = "EC7H_SYNTH_SINV-0001"
		manifest["scenarios"][1]["synthetic_record_reference"] = "EC7H_SYNTH_SO-0001"

		report = dataset_validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("scenarios[0]:synthetic_record_reference_raw_business_identifier", report["violations"])
		self.assertIn("scenarios[1]:synthetic_record_reference_raw_business_identifier", report["violations"])

	def test_dataset_cli_outputs_pass_fail_without_db(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "dataset.json"
			path.write_text(json.dumps(_valid_manifest()), encoding="utf-8")

			stdout = io.StringIO()
			with redirect_stdout(stdout):
				exit_code = dataset_validator.main([str(path)])

		self.assertEqual(exit_code, 0)
		self.assertIn('"valid": true', stdout.getvalue())

	def test_archive_readiness_passes_for_external_restricted_directory(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as archive_root:
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			(archive / "RETENTION.md").write_text("synthetic retention marker", encoding="utf-8")
			os.chmod(archive, 0o750)
			stat_result = archive.stat()
			owner = archive_checker._name_for_uid(stat_result.st_uid)
			group = archive_checker._name_for_gid(stat_result.st_gid)

			report = archive_checker.check_archive_readiness(
				path=archive,
				expected_owner=owner,
				expected_group=group,
				max_mode="750",
				retention_marker="RETENTION.md",
				repo_root=repo_root,
			)

		self.assertTrue(report["valid"])
		self.assertEqual(report["runtime_effect"], "none")
		self.assertTrue(report["outside_repo"])
		self.assertTrue(report["permissions_ok"])
		self.assertTrue(report["retention_marker_ok"])

	def test_archive_readiness_rejects_missing_path_and_inside_repo(self):
		with tempfile.TemporaryDirectory() as repo_root:
			missing = Path(repo_root) / "missing_archive"

			report = archive_checker.check_archive_readiness(path=missing, repo_root=repo_root)

		self.assertFalse(report["valid"])
		self.assertIn("archive_path_missing", report["violations"])
		self.assertIn("archive_path_inside_repo", report["violations"])

	def test_archive_readiness_rejects_broad_permissions_and_missing_marker(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as archive_root:
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			os.chmod(archive, 0o755)

			report = archive_checker.check_archive_readiness(
				path=archive,
				max_mode="750",
				retention_marker="RETENTION.md",
				repo_root=repo_root,
			)

		self.assertFalse(report["valid"])
		self.assertIn("permissions_too_broad:0o755", report["violations"])
		self.assertTrue(any(item.startswith("retention_marker_missing:") for item in report["violations"]))

	def test_archive_readiness_rejects_repo_local_symlink_to_external_archive(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as archive_root:
			external_archive = Path(archive_root) / "ec7h_live_trace_raw"
			external_archive.mkdir()
			os.chmod(external_archive, 0o750)
			repo_symlink = Path(repo_root) / "archive_link"
			repo_symlink.symlink_to(external_archive, target_is_directory=True)

			report = archive_checker.check_archive_readiness(path=repo_symlink, repo_root=repo_root)

		self.assertFalse(report["valid"])
		self.assertIn("archive_path_is_symlink", report["violations"])
		self.assertIn("archive_path_lexically_inside_repo", report["violations"])

	def test_environment_readiness_passes_when_all_passive_inputs_exist(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
			repo = Path(repo_root)
			(repo / ".git").mkdir()
			bench = Path(bench_root) / "ec7h_controlled_bench"
			bench.mkdir()
			(bench / "sites").mkdir()
			(bench / "apps").mkdir()
			(bench / "sites" / "ec7h-test.local").mkdir()
			(bench / "sites" / "ec7h-test.local" / "site_config.json").write_text(
				json.dumps({"db_name": "ec7h_synthetic_site"}),
				encoding="utf-8",
			)
			(bench / "Procfile").write_text("web: bench serve", encoding="utf-8")
			dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
			dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			(archive / "RETENTION.md").write_text("retain for QA", encoding="utf-8")
			os.chmod(archive, 0o750)

			report = environment_checker.check_environment_readiness(
				bench_path=bench,
				site_name="ec7h-test.local",
				qa_user="qa_ec7h_trace_user@example.invalid",
				dataset_manifest_path=dataset,
				archive_path=archive,
				raw_trace_custodian="qa_owner",
				redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
				repo_root=repo,
				archive_retention_marker="RETENTION.md",
			)

		self.assertTrue(report["ready"])
		self.assertEqual(report["runtime_effect"], "none")
		self.assertEqual(report["decision"], "environment_ready_for_collection_request")
		self.assertTrue(report["site_name_valid"])
		self.assertTrue(report["bench_evidence"]["site_config_exists"])
		self.assertTrue(report["bench_evidence"]["site_config_valid"])
		self.assertEqual(report["bench_evidence"]["site_config_expected_keys_present"], ["db_name"])
		self.assertEqual(report["blockers"], [])

	def test_environment_readiness_rejects_source_checkout_as_bench_path(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as archive_root:
			repo = Path(repo_root)
			(repo / ".git").mkdir()
			(repo / "impl_factory").mkdir()
			(repo / "scripts").mkdir()
			(repo / "scripts" / "check_qwen_enterprise_guardrails.py").write_text("# guardrail", encoding="utf-8")
			dataset = Path(archive_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
			dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			os.chmod(archive, 0o750)

			report = environment_checker.check_environment_readiness(
				bench_path=repo,
				site_name="ec7h-test.local",
				qa_user="qa_ec7h_trace_user@example.invalid",
				dataset_manifest_path=dataset,
				archive_path=archive,
				raw_trace_custodian="qa_owner",
				redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
				repo_root=repo,
			)

		self.assertFalse(report["ready"])
		self.assertIn("bench_path_inside_repo", report["blockers"])
		self.assertIn("bench_path_is_source_checkout", report["blockers"])

	def test_environment_readiness_rejects_arbitrary_temp_directory_as_bench_path(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
			repo = Path(repo_root)
			(repo / ".git").mkdir()
			bench = Path(bench_root) / "not_a_bench"
			bench.mkdir()
			dataset = Path(archive_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
			dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			os.chmod(archive, 0o750)

			report = environment_checker.check_environment_readiness(
				bench_path=bench,
				site_name="ec7h-test.local",
				qa_user="qa_ec7h_trace_user@example.invalid",
				dataset_manifest_path=dataset,
				archive_path=archive,
				raw_trace_custodian="qa_owner",
				redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
				repo_root=repo,
			)

		self.assertFalse(report["ready"])
		self.assertIn("bench_path_is_temp", report["blockers"])
		self.assertIn("bench_path_lacks_controlled_bench_evidence", report["blockers"])

	def test_environment_readiness_rejects_empty_or_single_bench_markers(self):
		marker_sets = (
			("sites_only", ("sites",)),
			("apps_only", ("apps",)),
			("procfile_only", ("Procfile",)),
			("empty_sites_and_apps", ("sites", "apps")),
		)
		for label, markers in marker_sets:
			with self.subTest(label=label):
				with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
					repo = Path(repo_root)
					(repo / ".git").mkdir()
					bench = Path(bench_root) / "ec7h_controlled_bench"
					bench.mkdir()
					for marker in markers:
						marker_path = bench / marker
						if marker == "Procfile":
							marker_path.write_text("web: bench serve", encoding="utf-8")
						else:
							marker_path.mkdir()
					dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
					dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
					archive = Path(archive_root) / "ec7h_live_trace_raw"
					archive.mkdir()
					os.chmod(archive, 0o750)

					report = environment_checker.check_environment_readiness(
						bench_path=bench,
						site_name="ec7h-test.local",
						qa_user="qa_ec7h_trace_user@example.invalid",
						dataset_manifest_path=dataset,
						archive_path=archive,
						raw_trace_custodian="qa_owner",
						redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
						repo_root=repo,
					)

				self.assertFalse(report["ready"])
				self.assertIn("bench_path_lacks_controlled_bench_evidence", report["blockers"])

	def test_environment_readiness_rejects_unsafe_site_names(self):
		for unsafe_site_name in (".", "..", "../apps", "foo/bar", "foo\\bar", ""):
			with self.subTest(site_name=unsafe_site_name):
				with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
					repo = Path(repo_root)
					(repo / ".git").mkdir()
					bench = Path(bench_root) / "ec7h_controlled_bench"
					bench.mkdir()
					(bench / "sites").mkdir()
					(bench / "apps").mkdir()
					dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
					dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
					archive = Path(archive_root) / "ec7h_live_trace_raw"
					archive.mkdir()
					os.chmod(archive, 0o750)

					report = environment_checker.check_environment_readiness(
						bench_path=bench,
						site_name=unsafe_site_name,
						qa_user="qa_ec7h_trace_user@example.invalid",
						dataset_manifest_path=dataset,
						archive_path=archive,
						raw_trace_custodian="qa_owner",
						redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
						repo_root=repo,
					)

				self.assertFalse(report["ready"])
				if unsafe_site_name:
					self.assertIn("site_name_invalid", report["blockers"])
				else:
					self.assertIn("site_name_missing", report["blockers"])

	def test_environment_readiness_rejects_empty_site_directory_without_site_config(self):
		with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
			repo = Path(repo_root)
			(repo / ".git").mkdir()
			bench = Path(bench_root) / "ec7h_controlled_bench"
			bench.mkdir()
			(bench / "sites").mkdir()
			(bench / "apps").mkdir()
			(bench / "sites" / "ec7h-test.local").mkdir()
			dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
			dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
			archive = Path(archive_root) / "ec7h_live_trace_raw"
			archive.mkdir()
			os.chmod(archive, 0o750)

			report = environment_checker.check_environment_readiness(
				bench_path=bench,
				site_name="ec7h-test.local",
				qa_user="qa_ec7h_trace_user@example.invalid",
				dataset_manifest_path=dataset,
				archive_path=archive,
				raw_trace_custodian="qa_owner",
				redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
				repo_root=repo,
			)

		self.assertFalse(report["ready"])
		self.assertFalse(report["bench_evidence"]["site_config_exists"])
		self.assertFalse(report["bench_evidence"]["site_config_valid"])
		self.assertIn("site_config_invalid", report["blockers"])
		self.assertIn("bench_path_lacks_controlled_bench_evidence", report["blockers"])

	def test_environment_readiness_rejects_malformed_or_symlinked_site_config(self):
		def write_empty(path: Path, bench_root: Path):
			path.write_text("", encoding="utf-8")

		def write_invalid_json(path: Path, bench_root: Path):
			path.write_text("not json", encoding="utf-8")

		def write_json_list(path: Path, bench_root: Path):
			path.write_text("[]", encoding="utf-8")

		def write_object_without_frappe_key(path: Path, bench_root: Path):
			path.write_text(json.dumps({"synthetic": True}), encoding="utf-8")

		def write_symlink(path: Path, bench_root: Path):
			target = bench_root / "external_site_config.json"
			target.write_text(json.dumps({"db_name": "ec7h_synthetic_site"}), encoding="utf-8")
			path.symlink_to(target)

		cases = (
			("empty", write_empty, "site_config_empty"),
			("invalid_json", write_invalid_json, "site_config_invalid_json"),
			("json_list", write_json_list, "site_config_not_object"),
			(
				"object_without_frappe_key",
				write_object_without_frappe_key,
				"site_config_missing_expected_frappe_key",
			),
			("symlink", write_symlink, "site_config_is_symlink"),
		)
		for label, writer, expected_violation in cases:
			with self.subTest(label=label):
				with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
					repo = Path(repo_root)
					(repo / ".git").mkdir()
					bench = Path(bench_root) / "ec7h_controlled_bench"
					bench.mkdir()
					(bench / "sites").mkdir()
					(bench / "apps").mkdir()
					site_dir = bench / "sites" / "ec7h-test.local"
					site_dir.mkdir()
					writer(site_dir / "site_config.json", Path(bench_root))
					dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
					dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
					archive = Path(archive_root) / "ec7h_live_trace_raw"
					archive.mkdir()
					os.chmod(archive, 0o750)

					report = environment_checker.check_environment_readiness(
						bench_path=bench,
						site_name="ec7h-test.local",
						qa_user="qa_ec7h_trace_user@example.invalid",
						dataset_manifest_path=dataset,
						archive_path=archive,
						raw_trace_custodian="qa_owner",
						redacted_output_candidate_path="impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries",
						repo_root=repo,
					)

				self.assertFalse(report["ready"])
				self.assertIn("site_config_invalid", report["blockers"])
				self.assertIn(expected_violation, report["bench_evidence"]["site_config_violations"])

	def test_environment_readiness_rejects_forbidden_redacted_output_streams(self):
		for forbidden_output in (
			"erp_workspace_ui/redacted",
			"erp_ui/redacted",
			"02_seed_data/redacted",
			"seed/data/redacted",
			"tmp/redacted",
			"temp/redacted",
			"probe/redacted",
			"cache/redacted",
			"primeaxis/redacted",
			"generated/qwen_s7_browser_batch/redacted",
		):
			with self.subTest(forbidden_output=forbidden_output):
				with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as bench_root, tempfile.TemporaryDirectory() as archive_root:
					repo = Path(repo_root)
					(repo / ".git").mkdir()
					bench = Path(bench_root) / "ec7h_controlled_bench"
					bench.mkdir()
					(bench / "sites").mkdir()
					(bench / "apps").mkdir()
					dataset = Path(bench_root) / "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json"
					dataset.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
					archive = Path(archive_root) / "ec7h_live_trace_raw"
					archive.mkdir()
					os.chmod(archive, 0o750)

					report = environment_checker.check_environment_readiness(
						bench_path=bench,
						site_name="ec7h-test.local",
						qa_user="qa_ec7h_trace_user@example.invalid",
						dataset_manifest_path=dataset,
						archive_path=archive,
						raw_trace_custodian="qa_owner",
						redacted_output_candidate_path=forbidden_output,
						repo_root=repo,
					)

				self.assertFalse(report["ready"])
				self.assertIn("redacted_output_candidate_forbidden_stream", report["blockers"])

	def test_environment_readiness_reports_blockers_without_fixing_inputs(self):
		with tempfile.TemporaryDirectory() as repo_root:
			repo = Path(repo_root)
			(repo / ".git").mkdir()
			forbidden = repo / "erp_workspace_ui"
			forbidden.mkdir()

			report = environment_checker.check_environment_readiness(
				bench_path=repo / "missing_bench",
				site_name="",
				qa_user="not_preferred@example.invalid",
				dataset_manifest_path=repo / "missing_dataset.json",
				archive_path=repo / "missing_archive",
				raw_trace_custodian="",
				redacted_output_candidate_path="erp_workspace_ui/redacted",
				repo_root=repo,
			)

		self.assertFalse(report["ready"])
		self.assertIn("bench_path_missing", report["blockers"])
		self.assertIn("site_name_missing", report["blockers"])
		self.assertIn("dataset_manifest_missing", report["blockers"])
		self.assertIn("archive_readiness_invalid", report["blockers"])
		self.assertIn("raw_trace_custodian_missing", report["blockers"])
		self.assertIn("redacted_output_candidate_forbidden_stream", report["blockers"])
		self.assertIn("qa_user_not_preferred_name", report["warnings"])


if __name__ == "__main__":
	unittest.main()
