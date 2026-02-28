from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase4_db_semantic_catalog_refresh.py"


class Phase4DbSemanticCatalogRefreshTests(unittest.TestCase):
    def test_refresh_builds_catalog_from_meta_and_capability(self):
        doctype_meta = {
            "Customer": {
                "autoname": "field:customer_name",
                "title_field": "customer_name",
                "mandatory_fields": [{"fieldname": "customer_name", "label": "Customer Name"}],
                "link_fields": [{"fieldname": "territory", "label": "Territory", "fieldtype": "Link", "options": "Territory"}],
                "fields": [
                    {"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data"},
                    {"fieldname": "territory", "label": "Territory", "fieldtype": "Link", "options": "Territory"},
                ],
            },
            "Territory": {
                "autoname": "field:territory_name",
                "title_field": "territory_name",
                "mandatory_fields": [{"fieldname": "territory_name", "label": "Territory Name"}],
                "link_fields": [],
                "fields": [{"fieldname": "territory_name", "label": "Territory Name", "fieldtype": "Data"}],
            },
        }
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

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            meta_path = td_path / "doctype_meta.json"
            cap_path = td_path / "capability.json"
            out_path = td_path / "db_catalog.json"
            meta_path.write_text(json.dumps(doctype_meta, ensure_ascii=False), encoding="utf-8")
            cap_path.write_text(json.dumps(capability_payload, ensure_ascii=False), encoding="utf-8")

            cp = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--doctype-meta-json",
                    str(meta_path),
                    "--capability-json",
                    str(cap_path),
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
            self.assertEqual(str(out.get("schema_version") or ""), "db_semantic_catalog_v1")
            catalog = out.get("catalog") if isinstance(out.get("catalog"), dict) else {}
            tables = [t for t in list(catalog.get("tables") or []) if isinstance(t, dict)]
            joins = [j for j in list(catalog.get("joins") or []) if isinstance(j, dict)]
            self.assertEqual(len(tables), 2)
            self.assertEqual(len(joins), 1)
            self.assertEqual(str(joins[0].get("from_doctype") or ""), "Customer")
            self.assertEqual(str(joins[0].get("to_doctype") or ""), "Territory")


if __name__ == "__main__":
    unittest.main()

