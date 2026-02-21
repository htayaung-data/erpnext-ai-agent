#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_PATH = Path("impl_factory/04_automation/capability_v7/latest_capability_platform.json")


def _load(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("payload must be a JSON object")
    return obj


def _validate(payload: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    reports = [r for r in list(index.get("reports") or []) if isinstance(r, dict)]

    if str(index.get("schema_version") or "") != "v1":
        errs.append("index.schema_version must be v1")
    if not reports:
        errs.append("index.reports must be non-empty")

    for i, row in enumerate(reports):
        report_name = str(row.get("report_name") or "").strip()
        if not report_name:
            errs.append(f"reports[{i}].report_name missing")
            continue
        constraints = row.get("constraints") if isinstance(row.get("constraints"), dict) else {}
        semantics = row.get("semantics") if isinstance(row.get("semantics"), dict) else {}
        time_support = row.get("time_support") if isinstance(row.get("time_support"), dict) else {}
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        if not constraints:
            errs.append(f"{report_name}: constraints missing")
        if not semantics:
            errs.append(f"{report_name}: semantics missing")
        if not time_support:
            errs.append(f"{report_name}: time_support missing")
        if not meta:
            errs.append(f"{report_name}: metadata missing")
            continue
        try:
            conf = float(meta.get("confidence"))
        except Exception:
            conf = -1.0
        if conf < 0.0 or conf > 1.0:
            errs.append(f"{report_name}: metadata.confidence out of range")
        if not str(meta.get("fingerprint") or "").strip():
            errs.append(f"{report_name}: metadata.fingerprint missing")

    required_coverage_keys = (
        "active_report_family_count",
        "covered_report_family_count",
        "family_coverage_rate",
        "report_coverage_rate",
        "family_gate_pass_95",
    )
    for key in required_coverage_keys:
        if key not in coverage:
            errs.append(f"coverage.{key} missing")

    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 2 capability platform payload.")
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"FAIL: payload not found at {path}")
        return 1
    try:
        payload = _load(path)
    except Exception as ex:
        print(f"FAIL: unable to load payload: {ex}")
        return 1

    errors = _validate(payload)
    if errors:
        print("Phase2 capability payload validation: FAILED")
        for err in errors[:100]:
            print(f" - {err}")
        return 1

    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    coverage = payload.get("coverage") if isinstance(payload.get("coverage"), dict) else {}
    summary = {
        "report_count": index.get("report_count"),
        "active_report_family_count": coverage.get("active_report_family_count"),
        "family_coverage_rate": coverage.get("family_coverage_rate"),
        "family_gate_pass_95": coverage.get("family_gate_pass_95"),
    }
    print("Phase2 capability payload validation: PASS")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

