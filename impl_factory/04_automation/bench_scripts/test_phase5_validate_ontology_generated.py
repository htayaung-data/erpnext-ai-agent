from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase5_validate_ontology_generated.py"


class Phase5ValidateOntologyGeneratedTests(unittest.TestCase):
    def test_validator_passes_for_valid_payload(self):
        payload = {
            "schema_version": "ontology_generated_v1",
            "source": {"capability_report_count": 1},
            "metric_aliases": {"revenue": ["revenue", "sales"]},
            "metric_domain_map": {"revenue": "sales"},
            "domain_aliases": {"sales": ["sales"]},
            "dimension_aliases": {"customer": ["customer"]},
            "primary_dimension_aliases": {"customer": ["customer", "customer-wise"]},
            "filter_kind_aliases": {"company": ["company"], "from_date": ["from_date"], "to_date": ["to_date"]},
        }
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            p = td_path / "ontology.json"
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            cp = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--path", str(p)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
            self.assertIn("PASS", cp.stdout)

    def test_validator_fails_for_missing_metric_domain_map(self):
        payload = {
            "schema_version": "ontology_generated_v1",
            "source": {"capability_report_count": 1},
            "metric_aliases": {"revenue": ["revenue", "sales"]},
            "metric_domain_map": {},
            "domain_aliases": {"sales": ["sales"]},
            "dimension_aliases": {"customer": ["customer"]},
            "primary_dimension_aliases": {"customer": ["customer"]},
            "filter_kind_aliases": {"company": ["company"]},
        }
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            p = td_path / "ontology_bad.json"
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            cp = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--path", str(p)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(cp.returncode, 0)
            self.assertIn("FAILED", cp.stdout)


if __name__ == "__main__":
    unittest.main()
