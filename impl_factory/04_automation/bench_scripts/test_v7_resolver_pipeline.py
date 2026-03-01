from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/resolver_pipeline.py"


def _load_module():
    orig_frappe = sys.modules.get("frappe")
    sys.modules["frappe"] = SimpleNamespace()
    spec = importlib.util.spec_from_file_location("v7_resolver_pipeline_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v7 resolver pipeline module")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    finally:
        if orig_frappe is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = orig_frappe
    return mod


class V7ResolverPipelineTests(unittest.TestCase):
    def test_llm_rerank_does_not_override_feasible_deterministic_selection(self):
        mod = _load_module()
        resolved = {
            "selected_report": "Item-wise Sales Register",
            "candidate_reports": [
                {
                    "report_name": "Item-wise Sales Register",
                    "score": 164,
                    "hard_blockers": [],
                    "missing_required_filter_values": [],
                },
                {
                    "report_name": "Item-wise Sales History",
                    "score": 164,
                    "hard_blockers": [],
                    "missing_required_filter_values": [],
                },
            ],
            "business_spec": {
                "task_type": "ranking",
                "output_contract": {"mode": "top_n"},
            },
        }
        index = {
            "reports_by_name": {
                "Item-wise Sales Register": {
                    "report_name": "Item-wise Sales Register",
                    "constraints": {},
                    "semantics": {"primary_dimension": "item"},
                },
                "Item-wise Sales History": {
                    "report_name": "Item-wise Sales History",
                    "constraints": {},
                    "semantics": {"primary_dimension": "item"},
                },
            }
        }

        orig_choose_candidate_report = mod.choose_candidate_report
        try:
            mod.choose_candidate_report = lambda **kwargs: {"selected_report": "Item-wise Sales History"}
            out = mod._llm_rerank_selected_report(
                message="Top 10 products by revenue last month",
                resolved=resolved,
                index=index,
            )
        finally:
            mod.choose_candidate_report = orig_choose_candidate_report

        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
