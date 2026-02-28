from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/contract_registry.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_contract_registry_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load contract_registry module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ContractRegistryTests(unittest.TestCase):
    def test_spec_contract_exposes_allowed_sets(self):
        mod = _load_module()
        contract = mod.get_spec_contract()
        self.assertTrue(bool(str(contract.get("version") or "").strip()))
        self.assertIn("read", set(mod.allowed_spec_values("intents")))
        self.assertIn("kpi", set(mod.allowed_spec_values("task_types")))
        self.assertIn("list_latest_records", set(mod.allowed_spec_values("task_classes")))
        self.assertIn("finance", set(mod.allowed_spec_values("domains")))

    def test_dimension_to_domain_mapping(self):
        mod = _load_module()
        self.assertEqual(mod.domain_from_dimension("customer"), "sales")
        self.assertEqual(mod.domain_from_dimension("supplier"), "purchasing")
        self.assertEqual(mod.domain_from_dimension("unknown_dim"), "")

    def test_clarification_contract_defaults(self):
        mod = _load_module()
        reasons = mod.allowed_blocker_reasons()
        self.assertIn("missing_required_filter_value", reasons)
        q = mod.default_clarification_question("entity_ambiguous")
        self.assertTrue("multiple matches" in q.lower())
        kind_q = mod.clarification_question_for_filter_kind("warehouse")
        self.assertEqual(kind_q, "Which warehouse should I use?")
        fallback = mod.default_clarification_question("non_existing_reason")
        self.assertTrue(bool(str(fallback or "").strip()))
        unknown_kind_q = mod.clarification_question_for_filter_kind("cost_center")
        self.assertIn("cost center", str(unknown_kind_q).lower())

    def test_contract_override_file_is_applied(self):
        mod = _load_module()
        override = {
            "spec_contract": {
                "allowed": {"domains": ["unknown", "sales", "custom_domain"]},
                "dimension_domain_map": {"territory": "sales_override"},
            },
            "clarification_contract": {
                "questions_by_filter_kind": {"cost_center": "Which cost center should I use?"}
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
            f.write(json.dumps(override, ensure_ascii=False))
            override_path = f.name
        prev = os.environ.get("AI_ASSISTANT_V7_CONTRACT_OVERRIDE")
        try:
            os.environ["AI_ASSISTANT_V7_CONTRACT_OVERRIDE"] = override_path
            mod.clear_contract_cache()
            self.assertIn("custom_domain", set(mod.allowed_spec_values("domains")))
            self.assertEqual(mod.domain_from_dimension("territory"), "sales_override")
            self.assertEqual(mod.clarification_question_for_filter_kind("cost_center"), "Which cost center should I use?")
        finally:
            if prev is None:
                os.environ.pop("AI_ASSISTANT_V7_CONTRACT_OVERRIDE", None)
            else:
                os.environ["AI_ASSISTANT_V7_CONTRACT_OVERRIDE"] = prev
            mod.clear_contract_cache()
            try:
                Path(override_path).unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
