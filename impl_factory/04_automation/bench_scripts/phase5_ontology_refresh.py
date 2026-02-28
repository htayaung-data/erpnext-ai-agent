#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


LOG_DIR = Path("impl_factory/04_automation/logs")
STATE_DIR = Path("impl_factory/04_automation/capability_v7")
DEFAULT_CAPABILITY = STATE_DIR / "latest_capability_platform.json"
DEFAULT_DB_CATALOG = STATE_DIR / "latest_db_semantic_catalog.json"
DEFAULT_OUT = STATE_DIR / "latest_ontology_generated.json"
BASE_ONTOLOGY = Path(
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json"
)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _normalize_token(v: Any) -> str:
    return " ".join(str(v or "").strip().lower().replace("_", " ").replace("-", " ").split())


def _alias_seed(term: str) -> List[str]:
    t = _normalize_token(term)
    if not t:
        return []
    aliases = [t]
    us = t.replace(" ", "_")
    if us != t:
        aliases.append(us)
    return list(dict.fromkeys(aliases))


def _extract_reports(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    index = payload.get("index") if isinstance(payload.get("index"), dict) else {}
    rows = index.get("reports") if isinstance(index.get("reports"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _build_metric_domain_map(metrics: Set[str], base_map: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for m in sorted(metrics):
        mm = str(m or "").strip().lower()
        if not mm:
            continue
        if mm in base_map:
            out[mm] = str(base_map.get(mm) or "").strip().lower()
            continue
        if "revenue" in mm or "sales" in mm or "sold" in mm:
            out[mm] = "sales"
        elif "purchase" in mm or "supplier" in mm or "received" in mm:
            out[mm] = "purchasing"
        elif "stock" in mm or "inventory" in mm:
            out[mm] = "inventory"
        elif "outstanding" in mm or "receivable" in mm or "payable" in mm:
            out[mm] = "finance"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 5 ontology generation from capability + DB semantic catalog.")
    ap.add_argument("--capability-json", default=str(DEFAULT_CAPABILITY))
    ap.add_argument("--db-semantic-json", default=str(DEFAULT_DB_CATALOG))
    ap.add_argument("--out-json", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    cap_path = Path(str(args.capability_json))
    db_path = Path(str(args.db_semantic_json))
    out_path = Path(str(args.out_json))

    capability = _load_json(cap_path)
    db_catalog = _load_json(db_path)
    base_ontology = _load_json(BASE_ONTOLOGY)
    reports = _extract_reports(capability)
    if not reports:
        print(f"Capability payload missing reports: {cap_path}")
        return 1
    catalog = db_catalog.get("catalog") if isinstance(db_catalog.get("catalog"), dict) else {}
    projection = catalog.get("capability_projection") if isinstance(catalog.get("capability_projection"), dict) else {}

    metrics: Set[str] = set()
    domains: Set[str] = set()
    dimensions: Set[str] = set()
    filter_kinds: Set[str] = set()

    for x in list(projection.get("metrics") or []):
        s = _normalize_token(x)
        if s:
            metrics.add(s)
    for x in list(projection.get("domains") or []):
        s = _normalize_token(x)
        if s:
            domains.add(s)
    for x in list(projection.get("dimensions") or []):
        s = _normalize_token(x)
        if s:
            dimensions.add(s)
    for x in list(projection.get("filter_kinds") or []):
        s = _normalize_token(x)
        if s:
            filter_kinds.add(s)

    # Fallback enrichment from report rows if projection is sparse.
    for r in reports:
        sem = r.get("semantics") if isinstance(r.get("semantics"), dict) else {}
        con = r.get("constraints") if isinstance(r.get("constraints"), dict) else {}
        for x in list(sem.get("metric_hints") or []):
            s = _normalize_token(x)
            if s:
                metrics.add(s)
        for x in list(sem.get("domain_hints") or []):
            s = _normalize_token(x)
            if s:
                domains.add(s)
        for x in list(sem.get("dimension_hints") or []):
            s = _normalize_token(x)
            if s:
                dimensions.add(s)
        for x in list(con.get("supported_filter_kinds") or []):
            s = _normalize_token(x)
            if s:
                filter_kinds.add(s)

    metric_aliases = {m.replace(" ", "_"): _alias_seed(m) for m in sorted(metrics)}
    domain_aliases = {d.replace(" ", "_"): _alias_seed(d) for d in sorted(domains)}
    dimension_aliases = {d.replace(" ", "_"): _alias_seed(d) for d in sorted(dimensions)}
    filter_kind_aliases = {k.replace(" ", "_"): _alias_seed(k) for k in sorted(filter_kinds)}
    primary_dimension_aliases = {
        d.replace(" ", "_"): list(dict.fromkeys(_alias_seed(d) + [f"{_normalize_token(d)} wise", f"{_normalize_token(d)}-wise"]))
        for d in sorted(dimensions)
    }

    base_metric_domain_map = (
        base_ontology.get("metric_domain_map")
        if isinstance(base_ontology.get("metric_domain_map"), dict)
        else {}
    )
    metric_domain_map = _build_metric_domain_map(
        {k for k in metric_aliases.keys()},
        {str(k).strip().lower(): str(v).strip().lower() for k, v in dict(base_metric_domain_map).items()},
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = {
        "schema_version": "ontology_generated_v1",
        "version": "generated_v1",
        "generated_at_utc": now,
        "source": {
            "phase": "phase5",
            "capability_path": str(cap_path),
            "db_semantic_path": str(db_path),
            "capability_report_count": len(reports),
            "projection_metric_count": len(metrics),
            "projection_domain_count": len(domains),
            "projection_dimension_count": len(dimensions),
            "projection_filter_kind_count": len(filter_kinds),
        },
        "metric_aliases": metric_aliases,
        "metric_domain_map": metric_domain_map,
        "domain_aliases": domain_aliases,
        "dimension_aliases": dimension_aliases,
        "primary_dimension_aliases": primary_dimension_aliases,
        "filter_kind_aliases": filter_kind_aliases,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = LOG_DIR / f"{ts}_phase5_ontology_generated.json"
    log_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "out_json": str(out_path),
        "log_json": str(log_path),
        "metric_alias_count": len(metric_aliases),
        "domain_alias_count": len(domain_aliases),
        "dimension_alias_count": len(dimension_aliases),
        "filter_kind_alias_count": len(filter_kind_aliases),
    }
    print(f"OUT_JSON={out_path}")
    print(f"OUT_LOG={log_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
