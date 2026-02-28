from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase4_validate_db_semantic_catalog.py"


class Phase4ValidateDbSemanticCatalogTests(unittest.TestCase):
    def test_validator_passes_for_consistent_catalog(self):
        payload = {
            "schema_version": "db_semantic_catalog_v1",
            "source": {
                "phase": "phase4",
                "doctype_count": 2,
                "capability_report_count": 5,
            },
            "catalog": {
                "tables": [
                    {
                        "doctype": "Customer",
                        "field_names": ["customer_name", "territory"],
                        "mandatory_fields": ["customer_name"],
                        "tokens": ["customer", "territory"],
                        "links": [{"fieldname": "territory", "target_doctype": "Territory"}],
                    },
                    {
                        "doctype": "Territory",
                        "field_names": ["territory_name"],
                        "mandatory_fields": ["territory_name"],
                        "tokens": ["territory"],
                        "links": [],
                    },
                ],
                "joins": [
                    {"from_doctype": "Customer", "fieldname": "territory", "to_doctype": "Territory", "join_type": "link"}
                ],
                "capability_projection": {
                    "domains": ["sales"],
                    "dimensions": ["customer"],
                    "metrics": ["revenue"],
                    "filter_kinds": ["company"],
                },
            },
        }
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "catalog.json"
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            cp = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--path", str(p)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
            self.assertIn("PASS", cp.stdout)


if __name__ == "__main__":
    unittest.main()

