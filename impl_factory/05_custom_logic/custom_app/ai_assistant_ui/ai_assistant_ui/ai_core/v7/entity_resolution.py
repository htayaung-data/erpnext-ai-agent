from __future__ import annotations

import re
from typing import Any, Dict, List

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover
    frappe = None

_DOC_ID_RE = re.compile(r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b")

_ENTITY_CONFIG: Dict[str, Dict[str, Any]] = {
    "warehouse": {
        "label": "warehouse",
        "doctype": "Warehouse",
        "search_fields": ("name", "warehouse_name"),
    },
    "customer": {
        "label": "customer",
        "doctype": "Customer",
        "search_fields": ("name", "customer_name"),
    },
    "supplier": {
        "label": "supplier",
        "doctype": "Supplier",
        "search_fields": ("name", "supplier_name"),
    },
    "item": {
        "label": "item",
        "doctype": "Item",
        "search_fields": ("name", "item_name"),
    },
    "company": {
        "label": "company",
        "doctype": "Company",
        "search_fields": ("name",),
    },
    "territory": {
        "label": "territory",
        "doctype": "Territory",
        "search_fields": ("name", "territory_name"),
    },
}


def _safe_str(v: Any) -> str:
    return str(v or "").strip()


def _infer_filter_kind(filter_key: str) -> str:
    k = _safe_str(filter_key).lower()
    if not k:
        return ""
    tokens = set(re.findall(r"[a-z0-9_]+", k))
    for kind in _ENTITY_CONFIG.keys():
        if kind in tokens or kind in k:
            return kind
    return ""


def _is_doc_id_value(v: str) -> bool:
    s = _safe_str(v)
    return bool(s and _DOC_ID_RE.search(s))


def _dedupe_keep_order(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for v in values:
        s = _safe_str(v)
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def _list_candidates(kind: str) -> List[Dict[str, Any]]:
    cfg = _ENTITY_CONFIG.get(kind) if isinstance(_ENTITY_CONFIG, dict) else None
    if not isinstance(cfg, dict):
        return []
    if frappe is None:
        return []
    doctype = _safe_str(cfg.get("doctype"))
    fields = [f for f in list(cfg.get("search_fields") or ()) if _safe_str(f)]
    if (not doctype) or (not fields):
        return []
    try:
        rows = frappe.get_all(doctype, fields=list(dict.fromkeys(fields)), limit_page_length=2000)
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        name = _safe_str(row.get("name"))
        if not name:
            continue
        aliases = [name]
        for f in fields:
            s = _safe_str(row.get(f))
            if s:
                aliases.append(s)
        out.append({"name": name, "aliases": _dedupe_keep_order(aliases)})
    return out


def _match_entity_value(kind: str, raw_value: str) -> Dict[str, Any]:
    raw = _safe_str(raw_value)
    if (not kind) or (not raw) or _is_doc_id_value(raw):
        return {"status": "skip", "value": raw, "options": []}

    candidates = _list_candidates(kind)
    if not candidates:
        # No deterministic master list available; keep original filter.
        return {"status": "unverified", "value": raw, "options": []}

    raw_lc = raw.lower()
    exact = []
    partial = []
    for cand in candidates:
        aliases = [str(x).strip() for x in list(cand.get("aliases") or []) if str(x or "").strip()]
        aliases_lc = [a.lower() for a in aliases]
        if raw_lc in aliases_lc:
            exact.append(cand)
            continue
        if any((raw_lc in a) for a in aliases_lc):
            partial.append(cand)

    if len(exact) == 1:
        return {"status": "matched", "value": _safe_str(exact[0].get("name")), "options": []}
    if len(exact) > 1:
        options = _dedupe_keep_order([_safe_str(x.get("name")) for x in exact])[:8]
        return {"status": "ambiguous", "value": raw, "options": options}
    if len(partial) == 1:
        return {"status": "matched", "value": _safe_str(partial[0].get("name")), "options": []}
    if len(partial) > 1:
        options = _dedupe_keep_order([_safe_str(x.get("name")) for x in partial])[:8]
        return {"status": "ambiguous", "value": raw, "options": options}
    return {"status": "no_match", "value": raw, "options": []}


def _build_entity_clarification(
    *,
    reason: str,
    label: str,
    filter_key: str,
    raw_value: str,
    options: List[str],
) -> Dict[str, Any]:
    if reason == "entity_ambiguous":
        options_text = ", ".join([str(x) for x in list(options or []) if _safe_str(x)])
        question = f'I found multiple matches for {label} matching "{raw_value}": {options_text}. Which one should I use?'
    else:
        question = f'I couldn\'t find a matching {label} for "{raw_value}". Which exact value should I use?'
    return {
        "reason": reason,
        "question": question,
        "options": list(options or []),
        "filter_key": str(filter_key or "").strip(),
        "raw_value": str(raw_value or "").strip(),
    }


def resolve_entity_filters(*, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically validates entity-like filters against ERP master doctypes.
    Returns normalized filters plus optional clarification blocker envelope.
    """
    src = filters if isinstance(filters, dict) else {}
    out_filters: Dict[str, Any] = {}

    for key, value in src.items():
        kind = _infer_filter_kind(str(key or ""))
        if not kind:
            out_filters[key] = value
            continue

        cfg = _ENTITY_CONFIG.get(kind) if isinstance(_ENTITY_CONFIG, dict) else {}
        label = _safe_str(cfg.get("label") or kind)

        if isinstance(value, list):
            vals = []
            for raw_item in value:
                raw = _safe_str(raw_item)
                if not raw:
                    continue
                match = _match_entity_value(kind, raw)
                status = str(match.get("status") or "").strip().lower()
                if status == "matched":
                    vals.append(_safe_str(match.get("value")))
                    continue
                if status == "ambiguous":
                    return {
                        "filters": out_filters,
                        "clarification": _build_entity_clarification(
                            reason="entity_ambiguous",
                            label=label,
                            filter_key=str(key or ""),
                            raw_value=raw,
                            options=[str(x) for x in list(match.get("options") or [])][:8],
                        ),
                    }
                if status == "no_match":
                    return {
                        "filters": out_filters,
                        "clarification": _build_entity_clarification(
                            reason="entity_no_match",
                            label=label,
                            filter_key=str(key or ""),
                            raw_value=raw,
                            options=[],
                        ),
                    }
                vals.append(raw)
            out_filters[key] = vals
            continue

        raw = _safe_str(value)
        if not raw:
            out_filters[key] = value
            continue
        match = _match_entity_value(kind, raw)
        status = str(match.get("status") or "").strip().lower()
        if status == "matched":
            out_filters[key] = _safe_str(match.get("value"))
            continue
        if status == "ambiguous":
            return {
                "filters": out_filters,
                "clarification": _build_entity_clarification(
                    reason="entity_ambiguous",
                    label=label,
                    filter_key=str(key or ""),
                    raw_value=raw,
                    options=[str(x) for x in list(match.get("options") or [])][:8],
                ),
            }
        if status == "no_match":
            return {
                "filters": out_filters,
                "clarification": _build_entity_clarification(
                    reason="entity_no_match",
                    label=label,
                    filter_key=str(key or ""),
                    raw_value=raw,
                    options=[],
                ),
            }
        out_filters[key] = value

    return {"filters": out_filters, "clarification": None}
