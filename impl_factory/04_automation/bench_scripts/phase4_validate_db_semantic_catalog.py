#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set


DEFAULT_PATH = Path("impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json")


def _load(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("catalog payload must be JSON object")
    return obj


def _validate(payload: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if str(payload.get("schema_version") or "").strip() != "db_semantic_catalog_v1":
        errs.append("schema_version must be db_semantic_catalog_v1")

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    catalog = payload.get("catalog") if isinstance(payload.get("catalog"), dict) else {}
    tables = [t for t in list(catalog.get("tables") or []) if isinstance(t, dict)]
    joins = [j for j in list(catalog.get("joins") or []) if isinstance(j, dict)]
    proj = catalog.get("capability_projection") if isinstance(catalog.get("capability_projection"), dict) else {}
    if not tables:
        errs.append("catalog.tables must be non-empty")
        return errs
    if int(source.get("doctype_count") or 0) != len(tables):
        errs.append("source.doctype_count mismatch")

    names: Set[str] = set()
    for i, t in enumerate(tables):
        dt = str(t.get("doctype") or "").strip()
        if not dt:
            errs.append(f"tables[{i}].doctype missing")
            continue
        if dt in names:
            errs.append(f"duplicate doctype in catalog.tables: {dt}")
        names.add(dt)
        for key in ("field_names", "mandatory_fields", "tokens", "links"):
            if key not in t:
                errs.append(f"{dt}: {key} missing")
        for lk in list(t.get("links") or []):
            if not isinstance(lk, dict):
                errs.append(f"{dt}: link row must be object")
                continue
            if not str(lk.get("fieldname") or "").strip():
                errs.append(f"{dt}: link.fieldname missing")
            if not str(lk.get("target_doctype") or "").strip():
                errs.append(f"{dt}: link.target_doctype missing")

    for i, j in enumerate(joins):
        src = str(j.get("from_doctype") or "").strip()
        dst = str(j.get("to_doctype") or "").strip()
        fld = str(j.get("fieldname") or "").strip()
        if not src or not dst or not fld:
            errs.append(f"joins[{i}] missing fields")
            continue
        if src not in names:
            errs.append(f"joins[{i}] from_doctype not in tables: {src}")
        if dst not in names:
            errs.append(f"joins[{i}] to_doctype not in tables: {dst}")

    for key in ("domains", "dimensions", "metrics", "filter_kinds"):
        if key not in proj:
            errs.append(f"catalog.capability_projection.{key} missing")

    if int(source.get("capability_report_count") or 0) <= 0:
        errs.append("source.capability_report_count must be > 0")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate phase4 DB semantic catalog payload.")
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    args = ap.parse_args()
    path = Path(str(args.path))
    if not path.exists():
        print(f"FAIL: catalog not found at {path}")
        return 1
    try:
        payload = _load(path)
    except Exception as ex:
        print(f"FAIL: unable to load catalog: {ex}")
        return 1

    errors = _validate(payload)
    if errors:
        print("Phase4 DB semantic catalog validation: FAILED")
        for e in errors[:100]:
            print(f" - {e}")
        return 1

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    catalog = payload.get("catalog") if isinstance(payload.get("catalog"), dict) else {}
    summary = {
        "doctype_count": source.get("doctype_count"),
        "capability_report_count": source.get("capability_report_count"),
        "join_count": len(list(catalog.get("joins") or [])),
    }
    print("Phase4 DB semantic catalog validation: PASS")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

