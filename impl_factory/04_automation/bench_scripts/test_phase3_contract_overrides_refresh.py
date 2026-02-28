from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase3_contract_overrides_refresh.py"


class Phase3ContractOverridesRefreshTests(unittest.TestCase):
    def test_generates_contract_overrides_from_capability_payload(self):
        payload = {
            "index": {
                "reports": [
                    {
                        "report_name": "Custom Sales Report",
                        "semantics": {
                            "domain_hints": ["sales"],
                            "dimension_hints": ["customer"],
                            "metric_hints": ["revenue"],
                            "primary_dimension": "customer",
                        },
                        "constraints": {
                            "supported_filter_kinds": ["company", "cost_center"],
                            "required_filter_kinds": ["company"],
                            "filters_definition": [
                                {"fieldname": "company", "label": "Company", "fieldtype": "Link"},
                                {"fieldname": "cost_center", "label": "Cost Center", "fieldtype": "Link"},
                            ],
                        },
                    }
                ]
            }
        }

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            inp = td_path / "capability.json"
            out = td_path / "overrides.json"
            inp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            cp = subprocess.run(
                ["python3", str(SCRIPT_PATH), "--input-json", str(inp), "--out-json", str(out)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
            self.assertTrue(out.exists())

            generated = json.loads(out.read_text(encoding="utf-8"))
            spec = generated.get("spec_contract") if isinstance(generated.get("spec_contract"), dict) else {}
            clar = generated.get("clarification_contract") if isinstance(generated.get("clarification_contract"), dict) else {}
            allowed = spec.get("allowed") if isinstance(spec.get("allowed"), dict) else {}
            questions = clar.get("questions_by_filter_kind") if isinstance(clar.get("questions_by_filter_kind"), dict) else {}

            self.assertIn("sales", list(allowed.get("domains") or []))
            self.assertIn("customer", list(spec.get("canonical_dimensions") or []))
            self.assertEqual(str((spec.get("dimension_domain_map") or {}).get("customer") or ""), "sales")
            self.assertIn("cost_center", questions)
            self.assertIn("cost center", str(questions.get("cost_center") or "").lower())
            # "company" is already defined in base clarification contract and should not be overwritten here.
            self.assertNotIn("company", questions)


if __name__ == "__main__":
    unittest.main()

