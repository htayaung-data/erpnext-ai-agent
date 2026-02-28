#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


LOG_DIR = Path("impl_factory/04_automation/logs")
STATE_DIR = Path("impl_factory/04_automation/capability_v7")
DEFAULT_DTYPE_META = Path("impl_factory/04_automation/logs/doctype_meta.json")
DEFAULT_CAPABILITY = STATE_DIR / "latest_capability_platform.json"
DEFAULT_OUT = STATE_DIR / "latest_db_semantic_catalog.json"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _normalize_token(v: Any) -> str:
    s = re.sub(r"[_\-\s]+", " ", str(v or "").strip().lower())
    return re.sub(r"\s+", " ", s).strip()


def _tokenize(text: Any) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for t in re.findall(r"[a-z0-9_]+", _normalize_token(text)):
        if len(t) < 2:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _extract_reports(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    rows = index.get("reports") if isinstance(index.get("reports"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _doctype_entry(doctype: str, row: Dict[str, Any]) -> Dict[str, Any]:
    fields = [f for f in list(row.get("fields") or []) if isinstance(f, dict)]
    field_names = [str(f.get("fieldname") or "").strip() for f in fields if str(f.get("fieldname") or "").strip()]
    field_labels = [str(f.get("label") or "").strip() for f in fields if str(f.get("label") or "").strip()]
    link_fields = [f for f in list(row.get("link_fields") or []) if isinstance(f, dict)]

    link_targets: List[str] = []
    links: List[Dict[str, Any]] = []
    for lf in link_fields:
        src = str(lf.get("fieldname") or "").strip()
        target = str(lf.get("options") or "").strip()
        if not src or not target:
            continue
        links.append({"fieldname": src, "target_doctype": target})
        link_targets.append(target)

    mandatory = [f for f in list(row.get("mandatory_fields") or []) if isinstance(f, dict)]
    mandatory_names = [str(f.get("fieldname") or "").strip() for f in mandatory if str(f.get("fieldname") or "").strip()]

    token_pool = set(_tokenize(doctype))
    for x in field_names + field_labels + mandatory_names + link_targets:
        token_pool.update(_tokenize(x))

    return {
        "doctype": str(doctype or "").strip(),
        "title_field": str(row.get("title_field") or "").strip(),
        "autoname": str(row.get("autoname") or "").strip(),
        "field_count": len(fields),
        "field_names": sorted(list(dict.fromkeys(field_names))),
        "field_labels": sorted(list(dict.fromkeys(field_labels))),
        "mandatory_fields": sorted(list(dict.fromkeys(mandatory_names))),
        "links": links,
        "link_targets": sorted(list(dict.fromkeys(link_targets))),
        "tokens": sorted(token_pool),
    }


def _join_edges(table_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    known_tables = {str(t.get("doctype") or "").strip() for t in list(table_entries or []) if str(t.get("doctype") or "").strip()}
    edges: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for t in list(table_entries or []):
        src_dt = str(t.get("doctype") or "").strip()
        for lk in list(t.get("links") or []):
            if not isinstance(lk, dict):
                continue
            target_dt = str(lk.get("target_doctype") or "").strip()
            fieldname = str(lk.get("fieldname") or "").strip()
            if not src_dt or not target_dt or not fieldname:
                continue
            if target_dt not in known_tables:
                continue
            key = f"{src_dt}|{fieldname}|{target_dt}"
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "from_doctype": src_dt,
                    "fieldname": fieldname,
                    "to_doctype": target_dt,
                    "join_type": "link",
                }
            )
    edges.sort(key=lambda x: (str(x.get("from_doctype") or ""), str(x.get("fieldname") or ""), str(x.get("to_doctype") or "")))
    return edges


def _capability_projection(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    domain_set: Set[str] = set()
    dim_set: Set[str] = set()
    metric_set: Set[str] = set()
    filter_set: Set[str] = set()
    for r in reports:
        sem = r.get("semantics") if isinstance(r.get("semantics"), dict) else {}
        con = r.get("constraints") if isinstance(r.get("constraints"), dict) else {}
        for x in list(sem.get("domain_hints") or []):
            s = _normalize_token(x)
            if s:
                domain_set.add(s)
        for x in list(sem.get("dimension_hints") or []):
            s = _normalize_token(x)
            if s:
                dim_set.add(s)
        for x in list(sem.get("metric_hints") or []):
            s = _normalize_token(x)
            if s:
                metric_set.add(s)
        for x in list(con.get("supported_filter_kinds") or []):
            s = _normalize_token(x)
            if s:
                filter_set.add(s)
    return {
        "domains": sorted(domain_set),
        "dimensions": sorted(dim_set),
        "metrics": sorted(metric_set),
        "filter_kinds": sorted(filter_set),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 4 DB semantic catalog refresh from doctype metadata + capability metadata.")
    ap.add_argument("--doctype-meta-json", default=str(DEFAULT_DTYPE_META))
    ap.add_argument("--capability-json", default=str(DEFAULT_CAPABILITY))
    ap.add_argument("--out-json", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    dtype_path = Path(str(args.doctype_meta_json))
    cap_path = Path(str(args.capability_json))
    out_path = Path(str(args.out_json))

    dtype_meta = _load_json(dtype_path)
    capability_payload = _load_json(cap_path)
    if not dtype_meta:
        print(f"Doctype metadata missing/invalid: {dtype_path}")
        return 1
    reports = _extract_reports(capability_payload)
    if not reports:
        print(f"Capability payload missing reports: {cap_path}")
        return 1

    table_entries: List[Dict[str, Any]] = []
    for doctype, row in dtype_meta.items():
        if not isinstance(row, dict):
            continue
        table_entries.append(_doctype_entry(str(doctype), row))
    table_entries.sort(key=lambda x: str(x.get("doctype") or "").lower())
    joins = _join_edges(table_entries)
    capability_projection = _capability_projection(reports)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = {
        "schema_version": "db_semantic_catalog_v1",
        "generated_at_utc": now,
        "source": {
            "phase": "phase4",
            "doctype_meta_path": str(dtype_path),
            "capability_path": str(cap_path),
            "doctype_count": len(table_entries),
            "capability_report_count": len(reports),
        },
        "catalog": {
            "tables": table_entries,
            "joins": joins,
            "capability_projection": capability_projection,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"{ts}_phase4_db_semantic_catalog.json"
    log_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "out_json": str(out_path),
        "log_json": str(log_path),
        "doctype_count": len(table_entries),
        "join_count": len(joins),
        "projection_metric_count": len(list(capability_projection.get("metrics") or [])),
    }
    print(f"OUT_JSON={out_path}")
    print(f"OUT_LOG={log_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

