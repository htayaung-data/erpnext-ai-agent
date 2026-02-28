#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set


DEFAULT_CAPABILITY_PATH = Path("impl_factory/04_automation/capability_v7/latest_capability_platform.json")
DEFAULT_OVERRIDE_PATH = Path("impl_factory/04_automation/capability_v7/latest_contract_overrides.json")
BASE_CLARIFICATION_CONTRACT = Path(
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json"
)


def _load(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: payload must be JSON object")
    return obj


def _extract_reports(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    rows = index.get("reports") if isinstance(index.get("reports"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _domains_from_capability(reports: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for r in reports:
        sem = r.get("semantics") if isinstance(r.get("semantics"), dict) else {}
        for d in list(sem.get("domain_hints") or []):
            s = str(d or "").strip().lower()
            if s:
                out.add(s)
    return out


def _dimensions_from_capability(reports: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for r in reports:
        sem = r.get("semantics") if isinstance(r.get("semantics"), dict) else {}
        for d in list(sem.get("dimension_hints") or []):
            s = str(d or "").strip().lower()
            if s:
                out.add(s)
    return out


def _filter_kinds_from_capability(reports: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for r in reports:
        con = r.get("constraints") if isinstance(r.get("constraints"), dict) else {}
        for k in list(con.get("supported_filter_kinds") or []):
            s = str(k or "").strip().lower()
            if s:
                out.add(s)
    return out


def _validate(capability_payload: Dict[str, Any], overrides_payload: Dict[str, Any], base_clarification: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    reports = _extract_reports(capability_payload)
    if not reports:
        errs.append("capability payload has no reports")
        return errs

    source = overrides_payload.get("source") if isinstance(overrides_payload.get("source"), dict) else {}
    spec = overrides_payload.get("spec_contract") if isinstance(overrides_payload.get("spec_contract"), dict) else {}
    clar = overrides_payload.get("clarification_contract") if isinstance(overrides_payload.get("clarification_contract"), dict) else {}
    allowed = spec.get("allowed") if isinstance(spec.get("allowed"), dict) else {}
    domains = {str(x).strip().lower() for x in list(allowed.get("domains") or []) if str(x).strip()}
    dims = {str(x).strip().lower() for x in list(spec.get("canonical_dimensions") or []) if str(x).strip()}
    dim_map = spec.get("dimension_domain_map") if isinstance(spec.get("dimension_domain_map"), dict) else {}
    kind_questions = clar.get("questions_by_filter_kind") if isinstance(clar.get("questions_by_filter_kind"), dict) else {}
    base_kind_questions = (
        base_clarification.get("questions_by_filter_kind")
        if isinstance(base_clarification.get("questions_by_filter_kind"), dict)
        else {}
    )

    if str(overrides_payload.get("version") or "").strip() != "phase3_generated_contract_overrides_v1":
        errs.append("overrides.version must be phase3_generated_contract_overrides_v1")
    if int(source.get("report_count") or 0) != len(reports):
        errs.append("source.report_count mismatch with capability report count")

    capability_domains = _domains_from_capability(reports)
    capability_dims = _dimensions_from_capability(reports)
    capability_filter_kinds = _filter_kinds_from_capability(reports)

    if "unknown" not in domains:
        errs.append("spec_contract.allowed.domains must include 'unknown'")
    if not capability_domains.issubset(domains):
        miss = sorted(list(capability_domains - domains))[:20]
        errs.append(f"spec_contract.allowed.domains missing capability domains: {miss}")

    if not capability_dims.issubset(dims):
        miss = sorted(list(capability_dims - dims))[:20]
        errs.append(f"spec_contract.canonical_dimensions missing capability dimensions: {miss}")

    for k, v in dim_map.items():
        kk = str(k or "").strip().lower()
        vv = str(v or "").strip().lower()
        if not kk:
            errs.append("dimension_domain_map contains empty key")
            continue
        if kk not in dims:
            errs.append(f"dimension_domain_map key not in canonical_dimensions: {kk}")
        if vv and vv not in domains:
            errs.append(f"dimension_domain_map value not in allowed.domains: {kk}->{vv}")

    for k, q in kind_questions.items():
        kk = str(k or "").strip().lower()
        qq = str(q or "").strip()
        if not kk or not qq:
            errs.append("clarification_contract.questions_by_filter_kind contains empty key/value")
            continue
        if kk not in capability_filter_kinds:
            errs.append(f"clarification question kind not found in capability filter kinds: {kk}")
        if kk in base_kind_questions:
            errs.append(f"clarification override should not redefine base kind question: {kk}")

    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate generated phase3 contract overrides payload.")
    ap.add_argument("--capability-json", default=str(DEFAULT_CAPABILITY_PATH))
    ap.add_argument("--overrides-json", default=str(DEFAULT_OVERRIDE_PATH))
    ap.add_argument("--base-clarification-json", default=str(BASE_CLARIFICATION_CONTRACT))
    args = ap.parse_args()

    capability_path = Path(str(args.capability_json))
    overrides_path = Path(str(args.overrides_json))
    base_clar_path = Path(str(args.base_clarification_json))
    if not capability_path.exists():
        print(f"FAIL: capability payload not found: {capability_path}")
        return 1
    if not overrides_path.exists():
        print(f"FAIL: overrides payload not found: {overrides_path}")
        return 1
    if not base_clar_path.exists():
        print(f"FAIL: base clarification contract not found: {base_clar_path}")
        return 1

    capability_payload = _load(capability_path)
    overrides_payload = _load(overrides_path)
    base_clarification = _load(base_clar_path)

    errors = _validate(capability_payload, overrides_payload, base_clarification)
    if errors:
        print("Phase3 contract overrides validation: FAILED")
        for err in errors[:100]:
            print(f" - {err}")
        return 1

    reports = _extract_reports(capability_payload)
    spec = overrides_payload.get("spec_contract") if isinstance(overrides_payload.get("spec_contract"), dict) else {}
    allowed = spec.get("allowed") if isinstance(spec.get("allowed"), dict) else {}
    clar = overrides_payload.get("clarification_contract") if isinstance(overrides_payload.get("clarification_contract"), dict) else {}
    summary = {
        "report_count": len(reports),
        "domain_count": len(list(allowed.get("domains") or [])),
        "dimension_count": len(list(spec.get("canonical_dimensions") or [])),
        "filter_kind_question_count": len(list((clar.get("questions_by_filter_kind") or {}).keys())),
    }
    print("Phase3 contract overrides validation: PASS")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

