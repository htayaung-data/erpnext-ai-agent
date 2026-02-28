#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


LOG_DIR = Path("impl_factory/04_automation/logs")
STATE_DIR = Path("impl_factory/04_automation/capability_v7")
DEFAULT_INPUT = STATE_DIR / "latest_capability_platform.json"
DEFAULT_OUT = STATE_DIR / "latest_contract_overrides.json"
BASE_CLARIFICATION_CONTRACT = Path(
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/clarification_contract_v1.json"
)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _extract_reports(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    rows = index.get("reports") if isinstance(index.get("reports"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _humanize(text: str) -> str:
    t = re.sub(r"[_\-\s]+", " ", str(text or "").strip().lower()).strip()
    return re.sub(r"\s+", " ", t)


def _candidate_question_for_kind(kind: str, filters_definition: List[Dict[str, Any]]) -> str:
    k = str(kind or "").strip().lower()
    if not k:
        return ""
    labels: List[str] = []
    for row in filters_definition:
        if not isinstance(row, dict):
            continue
        fieldname = str(row.get("fieldname") or "").strip().lower()
        label = str(row.get("label") or "").strip()
        if fieldname == k and label:
            labels.append(label)
    if labels:
        # Prefer shortest clear label ("Company" over long variants).
        labels.sort(key=lambda s: (len(str(s)), str(s).lower()))
        clean = _humanize(labels[0])
        if clean:
            return f"Which {clean} should I use?"
    return f"Which value should I use for {_humanize(k)}?"


def _derive_overrides(
    reports: List[Dict[str, Any]],
    *,
    existing_kind_questions: Dict[str, str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    domain_set = {"unknown", "cross_functional"}
    dim_set = set()
    dim_domain_votes: Dict[str, Dict[str, int]] = {}
    filter_kinds = set()
    question_votes: Dict[str, Dict[str, int]] = {}

    for row in reports:
        semantics = row.get("semantics") if isinstance(row.get("semantics"), dict) else {}
        constraints = row.get("constraints") if isinstance(row.get("constraints"), dict) else {}
        domains = [str(x).strip().lower() for x in list(semantics.get("domain_hints") or []) if str(x).strip()]
        dims = [str(x).strip().lower() for x in list(semantics.get("dimension_hints") or []) if str(x).strip()]
        kinds = [str(x).strip().lower() for x in list(constraints.get("supported_filter_kinds") or []) if str(x).strip()]
        defs = [d for d in list(constraints.get("filters_definition") or []) if isinstance(d, dict)]

        for d in domains:
            domain_set.add(d)
        for d in dims:
            dim_set.add(d)
            if d not in dim_domain_votes:
                dim_domain_votes[d] = {}
            for dom in domains:
                dim_domain_votes[d][dom] = int(dim_domain_votes[d].get(dom) or 0) + 1
        for k in kinds:
            filter_kinds.add(k)
            if k in existing_kind_questions:
                continue
            q = _candidate_question_for_kind(k, defs)
            if not q:
                continue
            if k not in question_votes:
                question_votes[k] = {}
            question_votes[k][q] = int(question_votes[k].get(q) or 0) + 1

    dimension_domain_map: Dict[str, str] = {}
    for dim in sorted(dim_set):
        votes = dim_domain_votes.get(dim) if isinstance(dim_domain_votes.get(dim), dict) else {}
        if not votes:
            continue
        top = sorted(votes.items(), key=lambda it: (int(it[1]), str(it[0])), reverse=True)[0][0]
        if str(top).strip():
            dimension_domain_map[dim] = str(top).strip()

    questions_by_kind: Dict[str, str] = {}
    for kind in sorted(filter_kinds):
        if kind in existing_kind_questions:
            continue
        votes = question_votes.get(kind) if isinstance(question_votes.get(kind), dict) else {}
        if votes:
            q = sorted(votes.items(), key=lambda it: (int(it[1]), str(it[0])), reverse=True)[0][0]
        else:
            q = f"Which value should I use for {_humanize(kind)}?"
        questions_by_kind[kind] = q

    spec_override = {
        "version": "generated_v1_from_capability_platform",
        "allowed": {
            "domains": sorted(domain_set),
        },
        "canonical_dimensions": sorted(dim_set),
        "dimension_domain_map": dimension_domain_map,
    }

    clar_override = {
        "version": "generated_v1_from_capability_platform",
        "questions_by_filter_kind": questions_by_kind,
    }
    return spec_override, clar_override


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 3 generated contract overrides from capability platform snapshot.")
    ap.add_argument("--input-json", default=str(DEFAULT_INPUT), help="Capability platform payload path.")
    ap.add_argument("--out-json", default=str(DEFAULT_OUT), help="Output contract overrides json path.")
    args = ap.parse_args()

    inp = Path(str(args.input_json or DEFAULT_INPUT))
    out = Path(str(args.out_json or DEFAULT_OUT))
    payload = _load_json(inp)
    if not payload:
        print(f"Input payload missing/invalid: {inp}")
        return 1

    reports = _extract_reports(payload)
    if not reports:
        print("No capability rows found in payload.")
        return 1

    base_clar = _load_json(BASE_CLARIFICATION_CONTRACT)
    existing_kind_questions = (
        base_clar.get("questions_by_filter_kind")
        if isinstance(base_clar.get("questions_by_filter_kind"), dict)
        else {}
    )
    existing_kind_questions = {
        str(k).strip().lower(): str(v).strip()
        for k, v in dict(existing_kind_questions).items()
        if str(k).strip() and str(v).strip()
    }

    spec_override, clar_override = _derive_overrides(
        reports,
        existing_kind_questions=existing_kind_questions,
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = {
        "version": "phase3_generated_contract_overrides_v1",
        "generated_at_utc": now,
        "source": {
            "phase": "phase3",
            "input_payload": str(inp),
            "report_count": len(reports),
        },
        "spec_contract": spec_override,
        "clarification_contract": clar_override,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"{ts}_phase3_contract_overrides.json"
    log_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "out_json": str(out),
        "log_json": str(log_path),
        "report_count": len(reports),
        "domain_count": len(list((spec_override.get("allowed") or {}).get("domains") or [])),
        "dimension_count": len(list(spec_override.get("canonical_dimensions") or [])),
        "filter_kind_question_count": len(list(clar_override.get("questions_by_filter_kind") or {})),
    }
    print(f"OUT_JSON={out}")
    print(f"OUT_LOG={log_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
