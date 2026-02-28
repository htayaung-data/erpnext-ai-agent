from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "impl_factory/04_automation/bench_scripts/phase3_validate_contract_overrides.py"


class Phase3ValidateContractOverridesTests(unittest.TestCase):
    def test_validator_passes_for_minimal_consistent_payload(self):
        capability = {
            "index": {
                "reports": [
                    {
                        "report_name": "Receivable Summary",
                        "semantics": {
                            "domain_hints": ["finance"],
                            "dimension_hints": ["customer"],
                            "metric_hints": ["outstanding_amount"],
                            "primary_dimension": "customer",
                        },
                        "constraints": {
                            "supported_filter_kinds": ["company", "from_date", "to_date"],
                            "required_filter_kinds": ["company"],
                            "filters_definition": [],
                        },
                    }
                ]
            }
        }
        overrides = {
            "version": "phase3_generated_contract_overrides_v1",
            "source": {"report_count": 1},
            "spec_contract": {
                "allowed": {"domains": ["unknown", "finance"]},
                "canonical_dimensions": ["customer"],
                "dimension_domain_map": {"customer": "finance"},
            },
            "clarification_contract": {"questions_by_filter_kind": {"from_date": "Which value should I use for from date?"}},
        }
        base_clar = {"questions_by_filter_kind": {"company": "Which company should I use?"}}

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            cap_path = td_path / "cap.json"
            ov_path = td_path / "ov.json"
            base_path = td_path / "base.json"
            cap_path.write_text(json.dumps(capability, ensure_ascii=False), encoding="utf-8")
            ov_path.write_text(json.dumps(overrides, ensure_ascii=False), encoding="utf-8")
            base_path.write_text(json.dumps(base_clar, ensure_ascii=False), encoding="utf-8")

            cp = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--capability-json",
                    str(cap_path),
                    "--overrides-json",
                    str(ov_path),
                    "--base-clarification-json",
                    str(base_path),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(cp.returncode, 0, msg=f"stdout={cp.stdout}\nstderr={cp.stderr}")
            self.assertIn("PASS", cp.stdout)


if __name__ == "__main__":
    unittest.main()

