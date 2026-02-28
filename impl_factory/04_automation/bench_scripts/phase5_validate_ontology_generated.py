#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_PATH = Path("impl_factory/04_automation/capability_v7/latest_ontology_generated.json")


def _load(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("ontology payload must be JSON object")
    return obj


def _validate_alias_map(name: str, payload: Dict[str, Any], errs: List[str], *, required: bool = True) -> None:
    value = payload.get(name)
    if not isinstance(value, dict):
        errs.append(f"{name} must be object")
        return
    if required and not value:
        errs.append(f"{name} must be non-empty")
        return
    for k, aliases in value.items():
        kk = str(k or "").strip()
        if not kk:
            errs.append(f"{name} contains empty key")
            continue
        if not isinstance(aliases, list):
            errs.append(f"{name}.{kk} must be list")
            continue
        if not aliases:
            errs.append(f"{name}.{kk} must be non-empty list")
            continue
        for i, a in enumerate(aliases):
            if not str(a or "").strip():
                errs.append(f"{name}.{kk}[{i}] must be non-empty string")


def _validate(payload: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    schema_version = str(payload.get("schema_version") or "").strip()
    if schema_version != "ontology_generated_v1":
        errs.append("schema_version must be ontology_generated_v1")

    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    if int(source.get("capability_report_count") or 0) <= 0:
        errs.append("source.capability_report_count must be > 0")

    _validate_alias_map("metric_aliases", payload, errs)
    _validate_alias_map("domain_aliases", payload, errs)
    _validate_alias_map("dimension_aliases", payload, errs)
    _validate_alias_map("primary_dimension_aliases", payload, errs, required=False)
    _validate_alias_map("filter_kind_aliases", payload, errs)

    metric_domain_map = payload.get("metric_domain_map")
    if not isinstance(metric_domain_map, dict):
        errs.append("metric_domain_map must be object")
    elif not metric_domain_map:
        errs.append("metric_domain_map must be non-empty")
    else:
        for k, v in metric_domain_map.items():
            if not str(k or "").strip():
                errs.append("metric_domain_map contains empty key")
            if not str(v or "").strip():
                errs.append(f"metric_domain_map.{k} has empty value")

    metric_aliases = payload.get("metric_aliases") if isinstance(payload.get("metric_aliases"), dict) else {}
    if metric_aliases and isinstance(metric_domain_map, dict):
        for metric in metric_aliases.keys():
            if str(metric or "").strip() and (metric not in metric_domain_map):
                errs.append(f"metric_domain_map missing key for metric_aliases.{metric}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate phase5 generated ontology payload.")
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    args = ap.parse_args()

    path = Path(str(args.path))
    if not path.exists():
        print(f"FAIL: ontology file not found at {path}")
        return 1
    try:
        payload = _load(path)
    except Exception as ex:
        print(f"FAIL: unable to load ontology payload: {ex}")
        return 1

    errors = _validate(payload)
    if errors:
        print("Phase5 ontology validation: FAILED")
        for e in errors[:100]:
            print(f" - {e}")
        return 1

    summary = {
        "schema_version": payload.get("schema_version"),
        "metric_alias_count": len(list((payload.get("metric_aliases") or {}).keys())),
        "domain_alias_count": len(list((payload.get("domain_aliases") or {}).keys())),
        "dimension_alias_count": len(list((payload.get("dimension_aliases") or {}).keys())),
        "filter_kind_alias_count": len(list((payload.get("filter_kind_aliases") or {}).keys())),
    }
    print("Phase5 ontology validation: PASS")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
