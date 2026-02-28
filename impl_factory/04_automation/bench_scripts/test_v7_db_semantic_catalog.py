from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/db_semantic_catalog.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_db_semantic_catalog_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load db semantic catalog module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7DbSemanticCatalogTests(unittest.TestCase):
    def test_retrieve_context_returns_ranked_tables(self):
        mod = _load_module()
        payload = {
            "schema_version": "db_semantic_catalog_v1",
            "catalog": {
                "tables": [
                    {
                        "doctype": "Customer",
                        "tokens": ["customer", "revenue", "territory"],
                        "field_names": ["customer_name", "territory", "company"],
                        "link_targets": ["Territory"],
                    },
                    {
                        "doctype": "Supplier",
                        "tokens": ["supplier", "payable"],
                        "field_names": ["supplier_name", "company"],
                        "link_targets": [],
                    },
                ],
                "joins": [
                    {"from_doctype": "Customer", "fieldname": "territory", "to_doctype": "Territory", "join_type": "link"}
                ],
                "capability_projection": {
                    "domains": ["sales", "finance"],
                    "dimensions": ["customer", "supplier"],
                    "metrics": ["revenue", "outstanding_amount"],
                    "filter_kinds": ["company", "customer"],
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
            f.write(json.dumps(payload, ensure_ascii=False))
            p = f.name
        prev = os.environ.get("AI_ASSISTANT_V7_DB_SEMANTIC_CATALOG")
        try:
            os.environ["AI_ASSISTANT_V7_DB_SEMANTIC_CATALOG"] = p
            mod.clear_db_semantic_catalog_cache()
            spec = {"subject": "Top customers by revenue", "metric": "revenue"}
            cs = {
                "domain": "sales",
                "metric": "revenue",
                "requested_dimensions": ["customer"],
                "hard_filter_kinds": ["company"],
            }
            out = mod.retrieve_db_semantic_context(
                business_spec=spec,
                constraint_set=cs,
                top_k=2,
            )
            self.assertTrue(bool(out.get("catalog_available")))
            tables = list(out.get("selected_tables") or [])
            self.assertTrue(bool(tables))
            self.assertEqual(str(tables[0].get("doctype") or ""), "Customer")
            self.assertIn("sales", list(out.get("preferred_domains") or []))
        finally:
            if prev is None:
                os.environ.pop("AI_ASSISTANT_V7_DB_SEMANTIC_CATALOG", None)
            else:
                os.environ["AI_ASSISTANT_V7_DB_SEMANTIC_CATALOG"] = prev
            mod.clear_db_semantic_catalog_cache()
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()

