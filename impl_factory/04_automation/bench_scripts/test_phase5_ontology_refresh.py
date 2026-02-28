from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase5_ontology_refresh.py"


class Phase5OntologyRefreshTests(unittest.TestCase):
    def test_refresh_builds_generated_ontology(self):
        capability_payload = {
            "index": {
                "reports": [
                    {
                        "report_name": "Customer Revenue",
                        "semantics": {
                            "domain_hints": ["sales"],
                            "dimension_hints": ["customer", "territory"],
                            "metric_hints": ["revenue"],
                        },
                        "constraints": {
                            "supported_filter_kinds": ["company", "customer", "from_date", "to_date"],
                        },
                    }
                ]
            }
        }
        db_catalog_payload = {
            "schema_version": "db_semantic_catalog_v1",
            "catalog": {
                "capability_projection": {
                    "domains": ["sales", "finance"],
                    "dimensions": ["customer", "territory"],
                    "metrics": ["revenue", "outstanding_amount"],
                    "filter_kinds": ["company", "customer", "from_date", "to_date"],
                }
            },
        }

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            cap_path = td_path / "capability.json"
            db_path = td_path / "db_catalog.json"
            out_path = td_path / "ontology_generated.json"
            cap_path.write_text(json.dumps(capability_payload, ensure_ascii=False), encoding="utf-8")
            db_path.write_text(json.dumps(db_catalog_payload, ensure_ascii=False), encoding="utf-8")

            cp = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--capability-json",
                    str(cap_path),
                    "--db-semantic-json",
                    str(db_path),
                    "--out-json",
                    str(out_path),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
            self.assertTrue(out_path.exists())
            out = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(str(out.get("schema_version") or ""), "ontology_generated_v1")
            self.assertIn("metric_aliases", out)
            self.assertIn("dimension_aliases", out)
            self.assertIn("filter_kind_aliases", out)
            self.assertGreater(len(list((out.get("metric_aliases") or {}).keys())), 0)


if __name__ == "__main__":
    unittest.main()
