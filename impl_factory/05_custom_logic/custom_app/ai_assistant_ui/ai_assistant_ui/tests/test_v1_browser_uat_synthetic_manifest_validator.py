import importlib.util
import json
from contextlib import redirect_stdout
import io
from pathlib import Path
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


validator = _load_script_module(
	"validate_v1_browser_uat_synthetic_manifest",
	"scripts/validate_v1_browser_uat_synthetic_manifest.py",
)


def _scenario_mapping(records=None):
	return {
		"required_records": list(records or []),
		"expected_dataset_status": "mapped",
	}


def _valid_manifest() -> dict:
	mappings = {
		scenario_id: _scenario_mapping()
		for scenario_id in sorted(validator.SMOKE_10_SCENARIOS)
	}
	mappings["V1RA-001"] = _scenario_mapping(["EC7H-CUST-A", "EC7H-CUST-B"])
	mappings["V1RA-009"] = _scenario_mapping(["EC7H-SUP-A", "EC7H-SUP-B"])
	mappings["V1RA-017"] = _scenario_mapping(["EC7H Synthetic Company"])
	mappings["V1RA-025"] = _scenario_mapping(["EC7H-CUST-A", "EC7H-ITEM-A"])
	mappings["V1RA-033"] = _scenario_mapping(["EC7H-SINV-0001", "EC7H-CUST-A"])
	mappings["V1RA-041"] = _scenario_mapping(["EC7H-CUST-A"])
	mappings["V1RA-049"] = _scenario_mapping(["EC7H-CUST-A", "EC7H-SUP-A", "EC7H-ITEM-A"])
	mappings["V1RA-055"] = _scenario_mapping(["EC7H-CUST-A", "EC7H-CUST-B"])
	return {
		"manifest_name": validator.EXPECTED_MANIFEST_NAME,
		"site": {
			"site_label": "TBD_NON_PRODUCTION_SITE_LABEL",
			"environment_type": "non_production",
		},
		"context": {
			"company": "EC7H Synthetic Company",
			"date_context": "synthetic_current_month",
		},
		"customers": [
			{"customer_id": "EC7H-CUST-A", "display_name": "EC7H Synthetic Customer A"},
			{"customer_id": "EC7H-CUST-B", "display_name": "EC7H Synthetic Customer B"},
		],
		"suppliers": [
			{"supplier_id": "EC7H-SUP-A", "display_name": "EC7H Synthetic Supplier A"},
			{"supplier_id": "EC7H-SUP-B", "display_name": "EC7H Synthetic Supplier B"},
		],
		"items": [
			{"item_id": "EC7H-ITEM-A", "display_name": "EC7H Synthetic Item A"},
		],
		"sales_invoices": [
			{
				"invoice_id": "EC7H-SINV-0001",
				"display_name": "EC7H Synthetic Sales Invoice 0001",
				"customer_id": "EC7H-CUST-A",
			},
		],
		"summaries": {
			"ar": {"record_ids": ["EC7H-CUST-A", "EC7H-CUST-B"]},
			"ap": {"record_ids": ["EC7H-SUP-A", "EC7H-SUP-B"]},
			"pnl": {"company": "EC7H Synthetic Company"},
			"sales": {"record_ids": ["EC7H-CUST-A", "EC7H-ITEM-A"]},
			"boundary": {"policy": "synthetic_boundary_only"},
		},
		"scenario_mappings": mappings,
	}


class V1BrowserUATSyntheticManifestValidatorTests(unittest.TestCase):
	def test_valid_minimal_smoke_10_manifest_passes(self):
		report = validator.validate_manifest(_valid_manifest())

		self.assertTrue(report["valid"])
		self.assertEqual(report["runtime_effect"], "none")
		self.assertEqual(report["manifest_name"], validator.EXPECTED_MANIFEST_NAME)
		self.assertEqual(report["violations"], [])

	def test_missing_and_wrong_manifest_name_fail(self):
		missing = _valid_manifest()
		missing.pop("manifest_name")
		wrong = _valid_manifest()
		wrong["manifest_name"] = "WRONG"

		missing_report = validator.validate_manifest(missing)
		wrong_report = validator.validate_manifest(wrong)

		self.assertFalse(missing_report["valid"])
		self.assertIn("manifest_name_mismatch:None", missing_report["violations"])
		self.assertFalse(wrong_report["valid"])
		self.assertIn("manifest_name_mismatch:'WRONG'", wrong_report["violations"])

	def test_missing_top_level_section_fails(self):
		manifest = _valid_manifest()
		manifest.pop("customers")

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("missing_top_level_section:customers", report["violations"])

	def test_missing_smoke_10_mapping_fails(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"].pop("V1RA-033")

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("missing_smoke_10_mapping:V1RA-033", report["violations"])

	def test_unknown_scenario_id_fails(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-999"] = _scenario_mapping()

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("unknown_scenario_id:V1RA-999", report["violations"])

	def test_approved_synthetic_ids_pass_in_correct_fields(self):
		report = validator.validate_manifest(_valid_manifest())

		self.assertTrue(report["valid"], report["violations"])

	def test_undeclared_synthetic_references_fail(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-001"]["required_records"] = ["EC7H-CUST-Z"]
		manifest["scenario_mappings"]["V1RA-009"]["required_records"] = ["EC7H-SUP-Z"]
		manifest["scenario_mappings"]["V1RA-025"]["required_records"] = ["EC7H-ITEM-Z"]
		manifest["scenario_mappings"]["V1RA-033"]["required_records"] = ["EC7H-SINV-9999"]

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn(
			"scenario_mappings.V1RA-001.required_records.0:undeclared_synthetic_reference:EC7H-CUST-Z",
			report["violations"],
		)
		self.assertIn(
			"scenario_mappings.V1RA-009.required_records.0:undeclared_synthetic_reference:EC7H-SUP-Z",
			report["violations"],
		)
		self.assertIn(
			"scenario_mappings.V1RA-025.required_records.0:undeclared_synthetic_reference:EC7H-ITEM-Z",
			report["violations"],
		)
		self.assertIn(
			"scenario_mappings.V1RA-033.required_records.0:undeclared_synthetic_reference:EC7H-SINV-9999",
			report["violations"],
		)

	def test_wrong_record_family_in_smoke_10_scenarios_fails(self):
		cases = (
			("V1RA-009", "EC7H-CUST-A", "customer"),
			("V1RA-001", "EC7H-SUP-A", "supplier"),
			("V1RA-025", "EC7H-SUP-A", "supplier"),
		)
		for scenario_id, record_id, family in cases:
			with self.subTest(scenario_id=scenario_id):
				manifest = _valid_manifest()
				manifest["scenario_mappings"][scenario_id]["required_records"] = [record_id]

				report = validator.validate_manifest(manifest)

				self.assertFalse(report["valid"])
				self.assertIn(
					f"scenario_mappings.{scenario_id}.required_records.0:wrong_record_family:{family}",
					report["violations"],
				)

	def test_correct_record_families_still_pass(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-009"]["required_records"] = ["EC7H-SUP-A"]
		manifest["scenario_mappings"]["V1RA-001"]["required_records"] = ["EC7H-CUST-A"]
		manifest["scenario_mappings"]["V1RA-025"]["required_records"] = ["EC7H-CUST-A", "EC7H-ITEM-A"]

		report = validator.validate_manifest(manifest)

		self.assertTrue(report["valid"], report["violations"])

	def test_malformed_summaries_fail(self):
		for summaries in ("not an object", [], None):
			with self.subTest(summaries=summaries):
				manifest = _valid_manifest()
				manifest["summaries"] = summaries

				report = validator.validate_manifest(manifest)

				self.assertFalse(report["valid"])
				self.assertIn("summaries:must_be_object", report["violations"])

	def test_missing_required_summary_key_fails(self):
		manifest = _valid_manifest()
		manifest["summaries"].pop("ar")

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("summaries:missing_required_summary_key:ar", report["violations"])

	def test_expected_dataset_status_allowlist(self):
		for status in ("mapped", "boundary_only", "clarification_expected"):
			with self.subTest(status=status):
				manifest = _valid_manifest()
				manifest["scenario_mappings"]["V1RA-061"]["expected_dataset_status"] = status

				report = validator.validate_manifest(manifest)

				self.assertTrue(report["valid"], report["violations"])

	def test_execute_real_data_status_fails(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-001"]["expected_dataset_status"] = "execute_real_data"

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn(
			"scenario_mappings.V1RA-001:invalid_expected_dataset_status:'execute_real_data'",
			report["violations"],
		)

	def test_approved_invoice_id_fails_in_wrong_field(self):
		manifest = _valid_manifest()
		manifest["customers"][0]["customer_id"] = "EC7H-SINV-0001"

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("customers.0.customer_id:synthetic_id_wrong_field:EC7H-SINV-0001", report["violations"])

	def test_bare_production_ids_fail(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-033"]["required_records"] = [
			"SINV-0001",
			"SO-0001",
			"PO-0001",
		]

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertTrue(any("bare_production_document_id" in item for item in report["violations"]))

	def test_marker_laundered_ids_fail(self):
		manifest = _valid_manifest()
		manifest["scenario_mappings"]["V1RA-033"]["required_records"] = ["EC7H_SYNTH_SINV-0001"]

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertTrue(any("marker_laundered_document_id" in item for item in report["violations"]))

	def test_real_like_names_fail(self):
		for value in ("Yoma Bank", "Global Trading Ltd", "John Smith"):
			manifest = _valid_manifest()
			manifest["customers"][0]["display_name"] = value

			report = validator.validate_manifest(manifest)

			self.assertFalse(report["valid"], value)
			self.assertTrue(any("real_like_name" in item for item in report["violations"]), value)

	def test_secret_trace_log_screenshot_and_forbidden_path_fields_fail(self):
		manifest = _valid_manifest()
		manifest["password"] = "never-store"
		manifest["session_id"] = "session"
		manifest["trace_payload"] = {"safe": False}
		manifest["browser_log"] = "raw log"
		manifest["screenshot_path"] = "screenshots/raw.png"
		manifest["artifact_path"] = "impl_factory/02_seed_data/raw_trace/site_config.json"

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertTrue(any("forbidden_secret_field" in item for item in report["violations"]))
		self.assertTrue(any("forbidden_artifact_field" in item for item in report["violations"]))
		self.assertTrue(any("forbidden_path_value" in item for item in report["violations"]))

	def test_site_environment_type_must_be_non_production(self):
		production = _valid_manifest()
		production["site"]["environment_type"] = "production"
		missing = _valid_manifest()
		missing["site"].pop("environment_type")
		unknown = _valid_manifest()
		unknown["site"]["environment_type"] = "unknown"

		production_report = validator.validate_manifest(production)
		missing_report = validator.validate_manifest(missing)
		unknown_report = validator.validate_manifest(unknown)

		self.assertFalse(production_report["valid"])
		self.assertIn("site.environment_type_must_be_non_production:'production'", production_report["violations"])
		self.assertFalse(missing_report["valid"])
		self.assertIn("site.environment_type_must_be_non_production:None", missing_report["violations"])
		self.assertFalse(unknown_report["valid"])
		self.assertIn("site.environment_type_must_be_non_production:'unknown'", unknown_report["violations"])

	def test_production_looking_site_label_fails(self):
		manifest = _valid_manifest()
		manifest["site"]["site_label"] = "erp-production-main"

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertIn("site.site_label_production_like:'erp-production-main'", report["violations"])

	def test_unknown_artifact_path_container_fails(self):
		manifest = _valid_manifest()
		manifest["artifact"] = {"output_path": "/var/qa/artifacts"}

		report = validator.validate_manifest(manifest)

		self.assertFalse(report["valid"])
		self.assertTrue(any("forbidden_artifact_field" in item for item in report["violations"]))

	def test_cli_outputs_pass_fail_without_db_or_browser(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "manifest.json"
			path.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
			stdout = io.StringIO()
			with redirect_stdout(stdout):
				exit_code = validator.main([str(path)])

		self.assertEqual(exit_code, 0)
		self.assertIn('"valid": true', stdout.getvalue())


if __name__ == "__main__":
	unittest.main()
