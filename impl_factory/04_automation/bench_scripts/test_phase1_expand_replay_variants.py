from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase1_expand_replay_variants as mod


class Phase1ExpandReplayVariantsTests(unittest.TestCase):
    def _write_jsonl(self, path: Path, rows):
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    def test_expand_manifest_generates_variants_and_preserves_behavior_labels(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            out = root / "out"
            src.mkdir(parents=True, exist_ok=True)

            rows = [
                {
                    "case_id": "A-01",
                    "suite": "core_read",
                    "role": "ai.reader",
                    "behavior_class": "ranking_top_n",
                    "turns": [{"role": "user", "text": "Show top customers last month"}],
                    "expected": {"intent": "READ"},
                    "tags": ["sales"],
                },
                {
                    "case_id": "A-02",
                    "suite": "core_read",
                    "role": "ai.reader",
                    "behavior_class": "trend_time_series",
                    "turns": [{"role": "user", "text": "Show monthly revenue for last 6 months"}],
                    "expected": {"intent": "READ"},
                    "tags": ["trend"],
                },
            ]
            self._write_jsonl(src / "core_read.jsonl", rows)
            manifest = {
                "version": "test",
                "behavior_class_schema": {
                    "field": "behavior_class",
                    "required": True,
                    "allowed": ["ranking_top_n", "trend_time_series"],
                    "target_mandatory_classes": ["ranking_top_n", "trend_time_series"],
                },
                "packs": [{"name": "core_read", "file": "core_read.jsonl", "case_count": 2, "description": ""}],
                "total_case_count": 2,
                "first_run_only": True,
            }
            (src / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            payload = mod.expand_manifest(
                manifest_path=(src / "manifest.json"),
                output_dir=out,
                target_total=10,
                seed=7,
                min_target_class_count=0,
                include_suites=[],
            )
            out_manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(int(out_manifest.get("total_case_count") or 0), 10)

            out_rows = mod._load_jsonl(out / "core_read.jsonl")
            self.assertEqual(len(out_rows), 10)
            variant_rows = [r for r in out_rows if str(r.get("variant_of") or "").strip()]
            self.assertGreaterEqual(len(variant_rows), 8)
            for r in variant_rows:
                self.assertTrue(str(r.get("case_id") or "").startswith(str(r.get("variant_of")) + "__v"))
                self.assertIn("generated_variant", list(r.get("tags") or []))
                self.assertTrue(str(r.get("behavior_class") or "").strip())

            behavior_counts = payload.get("behavior_counts") if isinstance(payload.get("behavior_counts"), dict) else {}
            self.assertIn("ranking_top_n", behavior_counts)
            self.assertIn("trend_time_series", behavior_counts)


if __name__ == "__main__":
    unittest.main()
