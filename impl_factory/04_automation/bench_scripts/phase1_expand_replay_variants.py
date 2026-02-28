from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple


DEFAULT_MANIFEST = Path("impl_factory/04_automation/replay_v7/manifest.json")
DEFAULT_OUTPUT_DIR = Path("impl_factory/04_automation/replay_v7_expanded")


_PHRASE_VARIANTS: List[Tuple[str, str]] = [
    ("show", "display"),
    ("display", "show"),
    ("top", "highest"),
    ("highest", "top"),
    ("latest", "most recent"),
    ("most recent", "latest"),
    ("last month", "previous month"),
    ("previous month", "last month"),
    ("this month", "current month"),
    ("current month", "this month"),
    ("how many", "count"),
    ("count", "how many"),
    ("give me", "show"),
    ("i mean", "please correct to"),
    ("show as million", "convert to million"),
    ("stock balance", "inventory balance"),
    ("inventory balance", "stock balance"),
    ("outstanding amount", "amount due"),
    ("amount due", "outstanding amount"),
    ("sales", "revenue"),
    ("revenue", "sales"),
]


def _load_json(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        obj = json.loads(s)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{i} row is not object")
        rows.append(obj)
    return rows


def _dump_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _dump_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    path.write_text(out + ("\n" if out else ""), encoding="utf-8")


def _replace_once(text: str, source: str, target: str) -> str:
    low = text.lower()
    idx = low.find(source)
    if idx < 0:
        return text
    return text[:idx] + target + text[idx + len(source) :]


def _rewrite_user_text(text: str, *, variant_index: int, rng: random.Random) -> str:
    s = str(text or "").strip()
    if not s:
        return s

    # Deterministic phrase replacement by rotating variant index across phrase map.
    phrase = _PHRASE_VARIANTS[variant_index % len(_PHRASE_VARIANTS)]
    rewritten = _replace_once(s, phrase[0], phrase[1])
    if rewritten != s:
        return rewritten

    # Fallback: swap one token with deterministic light perturbation.
    tokens = s.split()
    if len(tokens) <= 2:
        return s
    i = rng.randrange(1, len(tokens))
    t = tokens[i]
    if t.isalpha() and len(t) > 3:
        tokens[i] = t[0].upper() + t[1:] if t[0].islower() else t.lower()
    return " ".join(tokens)


def _variant_case_id(base_case_id: str, variant_no: int) -> str:
    return f"{base_case_id}__v{variant_no:03d}"


def _iter_rows(
    *,
    manifest_path: Path,
    manifest: Dict[str, Any],
    include_suites: Iterable[str] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    packs = [x for x in list(manifest.get("packs") or []) if isinstance(x, dict)]
    allowed_suites = {str(x).strip() for x in (include_suites or []) if str(x).strip()}
    if not allowed_suites:
        allowed_suites = {str(p.get("name") or "").strip() for p in packs if str(p.get("name") or "").strip()}

    all_rows: List[Dict[str, Any]] = []
    by_suite: Dict[str, List[Dict[str, Any]]] = {}
    for p in packs:
        suite = str(p.get("name") or "").strip()
        file_name = str(p.get("file") or "").strip()
        if not suite or not file_name or suite not in allowed_suites:
            continue
        rows = _load_jsonl((manifest_path.parent / file_name).resolve())
        by_suite[suite] = rows
        all_rows.extend(rows)
    return all_rows, by_suite


def _behavior_counts(rows: Sequence[Dict[str, Any]], behavior_field: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for r in rows:
        cls = str(r.get(behavior_field) or "").strip().lower()
        if cls:
            counts[cls] += 1
    return dict(sorted(counts.items()))


def _to_lc_set(values: Any) -> Set[str]:
    out: Set[str] = set()
    for v in list(values or []):
        s = str(v or "").strip().lower()
        if s:
            out.add(s)
    return out


def expand_manifest(
    *,
    manifest_path: Path,
    output_dir: Path,
    target_total: int,
    seed: int,
    min_target_class_count: int,
    include_suites: Iterable[str] | None = None,
) -> Dict[str, Any]:
    manifest = _load_json(manifest_path)
    behavior_schema = manifest.get("behavior_class_schema") if isinstance(manifest.get("behavior_class_schema"), dict) else {}
    behavior_field = str(behavior_schema.get("field") or "behavior_class").strip() or "behavior_class"
    all_rows, by_suite = _iter_rows(manifest_path=manifest_path, manifest=manifest, include_suites=include_suites)
    if not all_rows:
        raise ValueError("no rows loaded from source manifest")

    rng = random.Random(int(seed))
    base_total = len(all_rows)
    rows_out_by_suite: Dict[str, List[Dict[str, Any]]] = {}
    generated = 0
    target = max(base_total, int(target_total))
    min_target = max(0, int(min_target_class_count))

    # Start with base rows unchanged.
    for suite, rows in by_suite.items():
        rows_out_by_suite[suite] = [dict(r) for r in rows]

    # Generate deterministic variants round-robin by suite, then by row.
    suite_names = sorted(rows_out_by_suite.keys())
    per_case_variant_counter: Dict[str, int] = defaultdict(int)
    base_rows_by_class: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for suite, rows in by_suite.items():
        for row in rows:
            cls = str(row.get(behavior_field) or "").strip().lower()
            if cls:
                base_rows_by_class[cls].append((suite, row))

    def _append_variant(*, suite: str, row: Dict[str, Any], variant_no: int) -> None:
        nonlocal generated
        base_case_id = str(row.get("case_id") or "").strip()
        variant_row = dict(row)
        variant_row["variant_of"] = base_case_id
        variant_row["case_id"] = _variant_case_id(base_case_id, variant_no)
        turns = variant_row.get("turns") if isinstance(variant_row.get("turns"), list) else []
        new_turns: List[Dict[str, Any]] = []
        for t_idx, t in enumerate(turns):
            tt = dict(t) if isinstance(t, dict) else {}
            if str(tt.get("role") or "").strip().lower() == "user":
                tt["text"] = _rewrite_user_text(str(tt.get("text") or ""), variant_index=(variant_no + t_idx), rng=rng)
            new_turns.append(tt)
        variant_row["turns"] = new_turns
        tags = [str(x).strip() for x in list(variant_row.get("tags") or []) if str(x).strip()]
        if "generated_variant" not in tags:
            tags.append("generated_variant")
        variant_row["tags"] = tags
        rows_out_by_suite[suite].append(variant_row)
        generated += 1

    suite_cursor = 0
    while (base_total + generated) < target:
        suite = suite_names[suite_cursor % len(suite_names)]
        suite_cursor += 1
        base_rows = by_suite.get(suite) or []
        if not base_rows:
            continue
        row = base_rows[(generated + suite_cursor) % len(base_rows)]
        base_case_id = str(row.get("case_id") or "").strip()
        if not base_case_id:
            continue
        per_case_variant_counter[base_case_id] += 1
        variant_no = per_case_variant_counter[base_case_id]
        _append_variant(suite=suite, row=row, variant_no=variant_no)

    # If requested, enforce minimum target-class representation.
    target_classes = _to_lc_set(behavior_schema.get("target_mandatory_classes"))
    if min_target > 0 and target_classes:
        expanded_rows_snapshot: List[Dict[str, Any]] = []
        for suite in suite_names:
            expanded_rows_snapshot.extend(rows_out_by_suite.get(suite) or [])
        class_counts = _behavior_counts(expanded_rows_snapshot, behavior_field)
        for cls in sorted(target_classes):
            deficit = max(0, min_target - int(class_counts.get(cls) or 0))
            candidates = base_rows_by_class.get(cls) or []
            if deficit <= 0 or not candidates:
                continue
            for i in range(deficit):
                suite, row = candidates[i % len(candidates)]
                base_case_id = str(row.get("case_id") or "").strip()
                if not base_case_id:
                    continue
                per_case_variant_counter[base_case_id] += 1
                variant_no = per_case_variant_counter[base_case_id]
                _append_variant(suite=suite, row=row, variant_no=variant_no)

    packs_out: List[Dict[str, Any]] = []
    expanded_rows: List[Dict[str, Any]] = []
    for p in [x for x in list(manifest.get("packs") or []) if isinstance(x, dict)]:
        suite = str(p.get("name") or "").strip()
        if suite not in rows_out_by_suite:
            continue
        file_name = str(p.get("file") or "").strip()
        rows = rows_out_by_suite[suite]
        expanded_rows.extend(rows)
        packs_out.append(
            {
                "name": suite,
                "file": file_name,
                "case_count": len(rows),
                "description": str(p.get("description") or ""),
            }
        )
        _dump_jsonl((output_dir / file_name).resolve(), rows)

    base_version = str(manifest.get("version") or "v7_phase1_baseline")
    out_manifest: Dict[str, Any] = {
        "version": f"{base_version}_expanded_{len(expanded_rows)}",
        "source_manifest": str(manifest_path.resolve()),
        "generation": {
            "seed": int(seed),
            "target_total_cases": int(target),
            "min_target_class_count": int(min_target),
            "generated_variants": int(generated),
            "base_total_cases": int(base_total),
        },
        "behavior_class_schema": behavior_schema,
        "packs": packs_out,
        "total_case_count": len(expanded_rows),
        "first_run_only": bool(manifest.get("first_run_only", True)),
    }
    _dump_json((output_dir / "manifest.json").resolve(), out_manifest)

    return {
        "manifest": out_manifest,
        "output_dir": str(output_dir.resolve()),
        "behavior_field": behavior_field,
        "behavior_counts": _behavior_counts(expanded_rows, behavior_field),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Expand replay_v7 manifest with deterministic paraphrase variants.")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Source manifest path.")
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for expanded replay set.")
    ap.add_argument("--target-total", type=int, default=320, help="Target total case count after expansion.")
    ap.add_argument("--min-target-class-count", type=int, default=0, help="Optional minimum cases per target mandatory behavior class.")
    ap.add_argument("--seed", type=int, default=23, help="Deterministic seed.")
    ap.add_argument(
        "--include-suite",
        dest="include_suites",
        action="append",
        default=[],
        help="Optional suite include filter (repeatable).",
    )
    args = ap.parse_args()

    manifest_path = Path(str(args.manifest)).resolve()
    output_dir = Path(str(args.output_dir)).resolve()
    payload = expand_manifest(
        manifest_path=manifest_path,
        output_dir=output_dir,
        target_total=int(args.target_total),
        seed=int(args.seed),
        min_target_class_count=int(args.min_target_class_count),
        include_suites=list(args.include_suites or []),
    )
    print(f"OUT_DIR={payload.get('output_dir')}")
    print(json.dumps(payload.get("manifest") or {}, ensure_ascii=False))
    print(json.dumps({"behavior_counts": payload.get("behavior_counts") or {}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
