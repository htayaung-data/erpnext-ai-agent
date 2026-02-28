from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Set


def _load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except Exception as ex:
            raise ValueError(f"{path}:{i}: invalid JSON: {ex}") from ex
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{i}: row is not object")
        rows.append(obj)
    return rows


def _to_lc_set(values: object) -> Set[str]:
    out: Set[str] = set()
    for v in list(values or []):
        s = str(v or "").strip().lower()
        if s:
            out.add(s)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate Phase 1 replay packs.")
    default_manifest = Path("impl_factory/04_automation/replay_v7_expanded/manifest.json").resolve()
    if not default_manifest.exists():
        default_manifest = Path("impl_factory/04_automation/replay_v7/manifest.json").resolve()
    ap.add_argument("--manifest", default=str(default_manifest))
    ap.add_argument("--min-target-coverage", type=float, default=0.0, help="Optional minimum coverage ratio for target_mandatory_classes [0.0-1.0].")
    args = ap.parse_args()

    manifest_path = Path(str(args.manifest)).resolve()
    if not manifest_path.exists():
        raise SystemExit(f"manifest not found: {manifest_path}")

    manifest = _load_json(manifest_path)
    packs = [p for p in list(manifest.get("packs") or []) if isinstance(p, dict)]
    behavior_schema = manifest.get("behavior_class_schema") if isinstance(manifest.get("behavior_class_schema"), dict) else {}
    behavior_field = str(behavior_schema.get("field") or "behavior_class").strip() or "behavior_class"
    behavior_required = bool(behavior_schema.get("required"))
    allowed_behavior_classes = _to_lc_set(behavior_schema.get("allowed"))
    target_mandatory_classes = _to_lc_set(behavior_schema.get("target_mandatory_classes"))

    total_declared = int(manifest.get("total_case_count") or 0)
    total_actual = 0
    case_ids: Dict[str, str] = {}
    behavior_counts: Dict[str, int] = {}
    failures: List[str] = []

    for p in packs:
        name = str(p.get("name") or "").strip()
        file_name = str(p.get("file") or "").strip()
        count_declared = int(p.get("case_count") or 0)
        if not name or not file_name:
            failures.append(f"manifest pack missing name/file: {p}")
            continue

        pack_path = (manifest_path.parent / file_name).resolve()
        if not pack_path.exists():
            failures.append(f"missing pack file: {pack_path}")
            continue

        rows = _load_jsonl(pack_path)
        total_actual += len(rows)
        if len(rows) != count_declared:
            failures.append(f"case_count mismatch for {name}: declared={count_declared} actual={len(rows)}")

        for i, row in enumerate(rows, start=1):
            cid = str(row.get("case_id") or "").strip()
            suite = str(row.get("suite") or "").strip()
            turns = row.get("turns") if isinstance(row.get("turns"), list) else []
            expected = row.get("expected") if isinstance(row.get("expected"), dict) else None
            behavior_class = str(row.get(behavior_field) or "").strip().lower()
            if not cid:
                failures.append(f"{pack_path}:{i}: missing case_id")
                continue
            if cid in case_ids:
                failures.append(f"duplicate case_id {cid}: {case_ids[cid]} and {pack_path}")
            else:
                case_ids[cid] = str(pack_path)
            if suite != name:
                failures.append(f"{pack_path}:{i}: suite mismatch, expected '{name}' got '{suite}'")
            if not turns:
                failures.append(f"{pack_path}:{i}: empty turns")
            if expected is None:
                failures.append(f"{pack_path}:{i}: missing expected object")
            if behavior_required and not behavior_class:
                failures.append(f"{pack_path}:{i}: missing {behavior_field}")
            if behavior_class and allowed_behavior_classes and behavior_class not in allowed_behavior_classes:
                failures.append(f"{pack_path}:{i}: unknown {behavior_field}='{behavior_class}'")
            if behavior_class:
                behavior_counts[behavior_class] = int(behavior_counts.get(behavior_class) or 0) + 1

    if total_declared != total_actual:
        failures.append(f"manifest total_case_count mismatch: declared={total_declared} actual={total_actual}")

    covered_targets = set(behavior_counts.keys()) & target_mandatory_classes if target_mandatory_classes else set()
    missing_targets = sorted(list(target_mandatory_classes - covered_targets)) if target_mandatory_classes else []
    target_coverage = (float(len(covered_targets)) / float(len(target_mandatory_classes))) if target_mandatory_classes else 1.0
    if target_mandatory_classes and float(args.min_target_coverage) > 0.0 and target_coverage < float(args.min_target_coverage):
        failures.append(
            "target behavior class coverage below threshold: "
            f"coverage={target_coverage:.4f} threshold={float(args.min_target_coverage):.4f}"
        )

    if failures:
        print("Phase1 replay pack validation: FAILED")
        for f in failures:
            print(f" - {f}")
        raise SystemExit(1)

    print("Phase1 replay pack validation: PASS")
    print(f"pack_count={len(packs)}")
    print(f"total_case_count={total_actual}")
    print(f"behavior_class_field={behavior_field}")
    print(f"behavior_class_count={len(behavior_counts)}")
    print(f"target_behavior_class_count={len(target_mandatory_classes)}")
    print(f"target_behavior_class_coverage={target_coverage:.4f}")
    if missing_targets:
        print(f"missing_target_behavior_classes={','.join(missing_targets)}")


if __name__ == "__main__":
    main()
