from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "impl_factory").is_dir():
            return p
    return cur.parent


def _default_catalog_path() -> Path:
    return _repo_root() / "impl_factory/04_automation/capability_v7/latest_db_semantic_catalog.json"


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _norm(v: Any) -> str:
    s = re.sub(r"[_\-\s]+", " ", str(v or "").strip().lower())
    return re.sub(r"\s+", " ", s).strip()


def _tokenize(v: Any) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for t in re.findall(r"[a-z0-9_]+", _norm(v)):
        if len(t) < 2:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _query_tokens(*, business_spec: Dict[str, Any], constraint_set: Dict[str, Any]) -> List[str]:
    spec = business_spec if isinstance(business_spec, dict) else {}
    cs = constraint_set if isinstance(constraint_set, dict) else {}
    tokens: List[str] = []
    seen: Set[str] = set()
    bits = [
        str(spec.get("subject") or ""),
        str(spec.get("metric") or ""),
        str(cs.get("metric") or ""),
        str(cs.get("domain") or ""),
        " ".join([str(x) for x in list(cs.get("requested_dimensions") or [])]),
        " ".join([str(x) for x in list(cs.get("hard_filter_kinds") or [])]),
    ]
    for b in bits:
        for t in _tokenize(b):
            if t in seen:
                continue
            seen.add(t)
            tokens.append(t)
    return tokens


@lru_cache(maxsize=1)
def load_db_semantic_catalog() -> Dict[str, Any]:
    env_path = str(os.environ.get("AI_ASSISTANT_V7_DB_SEMANTIC_CATALOG") or "").strip()
    path = Path(env_path) if env_path else _default_catalog_path()
    if not path.exists():
        return {}
    payload = _load_json(path)
    if str(payload.get("schema_version") or "").strip() != "db_semantic_catalog_v1":
        return {}
    return payload


def clear_db_semantic_catalog_cache() -> None:
    load_db_semantic_catalog.cache_clear()


def retrieve_db_semantic_context(
    *,
    business_spec: Dict[str, Any],
    constraint_set: Dict[str, Any],
    top_k: int = 6,
) -> Dict[str, Any]:
    payload = load_db_semantic_catalog()
    catalog = payload.get("catalog") if isinstance(payload.get("catalog"), dict) else {}
    tables = [t for t in list(catalog.get("tables") or []) if isinstance(t, dict)]
    joins = [j for j in list(catalog.get("joins") or []) if isinstance(j, dict)]
    proj = catalog.get("capability_projection") if isinstance(catalog.get("capability_projection"), dict) else {}
    if not tables:
        return {
            "catalog_available": False,
            "selected_tables": [],
            "join_paths": [],
            "preferred_domains": [],
            "preferred_dimensions": [],
            "preferred_filter_kinds": [],
            "retrieval_score": 0.0,
            "query_tokens": [],
        }

    cs = constraint_set if isinstance(constraint_set, dict) else {}
    query_tokens = _query_tokens(business_spec=business_spec, constraint_set=cs)
    qset = set(query_tokens)
    requested_dimensions = {str(x).strip().lower() for x in list(cs.get("requested_dimensions") or []) if str(x).strip()}
    hard_filter_kinds = {str(x).strip().lower() for x in list(cs.get("hard_filter_kinds") or []) if str(x).strip()}
    domain = str(cs.get("domain") or "").strip().lower()

    scored: List[Dict[str, Any]] = []
    for t in tables:
        dt = str(t.get("doctype") or "").strip()
        tokens = {str(x).strip().lower() for x in list(t.get("tokens") or []) if str(x).strip()}
        fields = {str(x).strip().lower() for x in list(t.get("field_names") or []) if str(x).strip()}
        if not dt:
            continue
        overlap = sorted(list(qset & tokens))
        score = float(len(overlap)) * 5.0

        if requested_dimensions:
            dim_hits = requested_dimensions & fields
            score += float(len(dim_hits)) * 4.0
        if hard_filter_kinds:
            fk_hits = hard_filter_kinds & fields
            score += float(len(fk_hits)) * 3.0
        if domain and domain not in {"unknown", "cross functional"}:
            if domain in dt.lower():
                score += 2.0
        if score <= 0.0:
            continue
        scored.append(
            {
                "doctype": dt,
                "score": round(score, 4),
                "overlap_tokens": overlap[:12],
                "field_names": list(t.get("field_names") or [])[:160],
                "link_targets": list(t.get("link_targets") or [])[:80],
            }
        )

    scored.sort(key=lambda x: (float(x.get("score") or 0.0), str(x.get("doctype") or "")), reverse=True)
    selected = scored[: max(1, int(top_k))]
    selected_doctypes = {str(x.get("doctype") or "").strip() for x in selected if str(x.get("doctype") or "").strip()}

    join_paths: List[Dict[str, Any]] = []
    for j in joins:
        src = str(j.get("from_doctype") or "").strip()
        dst = str(j.get("to_doctype") or "").strip()
        if src in selected_doctypes and dst in selected_doctypes:
            join_paths.append(
                {
                    "from_doctype": src,
                    "fieldname": str(j.get("fieldname") or "").strip(),
                    "to_doctype": dst,
                    "join_type": str(j.get("join_type") or "link").strip(),
                }
            )

    preferred_domains = [str(x).strip().lower() for x in list(proj.get("domains") or []) if str(x).strip()]
    preferred_dimensions = [str(x).strip().lower() for x in list(proj.get("dimensions") or []) if str(x).strip()]
    preferred_filter_kinds = [str(x).strip().lower() for x in list(proj.get("filter_kinds") or []) if str(x).strip()]
    retrieval_score = round(sum(float(x.get("score") or 0.0) for x in selected), 4)
    return {
        "catalog_available": True,
        "selected_tables": selected,
        "join_paths": join_paths[:120],
        "preferred_domains": preferred_domains,
        "preferred_dimensions": preferred_dimensions,
        "preferred_filter_kinds": preferred_filter_kinds,
        "retrieval_score": retrieval_score,
        "query_tokens": query_tokens,
    }

