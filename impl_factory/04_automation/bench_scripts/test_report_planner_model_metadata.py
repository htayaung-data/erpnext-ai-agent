from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/llm/report_planner.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("report_planner_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load report_planner module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ReportPlannerModelMetadataTests(unittest.TestCase):
    def test_preferred_model_falls_back_to_default_openai_model(self):
        mod = _load_module()
        original_frappe = getattr(mod, "frappe", None)
        try:
            mod.frappe = types.SimpleNamespace(conf={"openai_model": "gpt-5.4-mini"})
            self.assertEqual(mod._preferred_model("spec"), "gpt-5.4-mini")
            self.assertEqual(mod._preferred_model("plan"), "gpt-5.4-mini")
        finally:
            mod.frappe = original_frappe


if __name__ == "__main__":
    unittest.main()
