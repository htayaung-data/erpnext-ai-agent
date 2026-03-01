from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


_DEFAULT_ONTOLOGY: Dict[str, Any] = {
    "version": "fallback_v1",
    "metric_aliases": {
        "revenue": ["revenue"],
        "purchase_amount": ["purchase_amount", "purchase amount", "procurement amount", "vendor spend"],
        "sold_quantity": ["sold_quantity", "sold quantity"],
        "received_quantity": ["received_quantity", "received quantity"],
        "stock_balance": ["stock_balance", "stock balance"],
        "projected_quantity": ["projected_quantity", "projected quantity", "projected qty"],
        "outstanding_amount": ["outstanding_amount", "outstanding amount"],
        "open_requests": ["open_requests", "open requests"],
    },
    "metric_column_aliases": {
        "revenue": [
            "revenue",
            "sales amount",
            "sales value",
            "invoiced amount",
            "billed amount",
            "amount",
            "total",
            "value",
            "sales",
            "income",
        ],
        "purchase_amount": ["purchase amount", "procurement amount", "vendor spend", "invoiced amount", "billed amount", "purchase value"],
        "sold_quantity": ["sold quantity", "sold qty", "sales qty", "sales quantity", "qty sold", "quantity", "qty"],
        "received_quantity": ["received quantity", "received qty", "purchase qty", "qty received", "quantity", "qty"],
        "stock_balance": ["stock balance", "item balance", "balance qty", "warehouse balance", "inventory balance", "balance", "quantity", "qty"],
        "projected_quantity": ["projected quantity", "projected qty", "quantity", "qty"],
        "outstanding_amount": [
            "outstanding amount",
            "amount due",
            "receivable amount",
            "payable amount",
            "outstanding balance",
            "receivable balance",
            "payable balance",
            "balance due",
            "closing balance",
        ],
        "open_requests": ["open requests", "pending requests", "request count", "count"],
    },
        "metric_domain_map": {
        "revenue": "sales",
        "purchase_amount": "purchasing",
        "sold_quantity": "sales",
        "received_quantity": "purchasing",
        "stock_balance": "inventory",
        "projected_quantity": "inventory",
        "outstanding_amount": "finance",
        "open_requests": "operations",
    },
    "domain_aliases": {
        "sales": ["sales"],
        "purchasing": ["purchasing"],
        "inventory": ["inventory"],
        "finance": ["finance"],
        "operations": ["operations"],
        "hr": ["hr"],
    },
    "dimension_aliases": {
        "customer": ["customer"],
        "supplier": ["supplier"],
        "item": ["item"],
        "warehouse": ["warehouse"],
        "territory": ["territory"],
        "company": ["company"],
    },
    "primary_dimension_aliases": {
        "customer": ["customer"],
        "supplier": ["supplier"],
        "item": ["item"],
        "warehouse": ["warehouse"],
        "territory": ["territory"],
        "sales_person": ["sales_person"],
        "sales_partner": ["sales_partner"],
    },
    "filter_kind_aliases": {
        "warehouse": ["warehouse"],
        "company": ["company"],
        "customer": ["customer"],
        "supplier": ["supplier"],
        "item": ["item"],
        "date": ["date"],
        "from_date": ["from_date", "from date"],
        "to_date": ["to_date", "to date"],
        "report_date": ["report_date", "report date"],
        "start_year": ["start_year", "start year"],
        "end_year": ["end_year", "end year"],
        "fiscal_year": ["fiscal_year", "fiscal year"],
        "year": ["year"],
    },
    "write_operation_aliases": {
        "create": ["create"],
        "update": ["update"],
        "delete": ["delete"],
        "confirm": ["confirm"],
        "cancel": ["cancel"],
    },
    "write_doctype_aliases": {
        "ToDo": ["todo"],
    },
    "export_aliases": {
        "include_download": ["download"],
    },
    "reference_value_aliases": {
        "same": [
            "same",
            "the same",
            "same as before",
            "same one",
            "that one",
            "this one",
            "previous one",
            "same value",
        ],
    },
    "transform_ambiguity_aliases": {
        "transform_scale:million": ["as million", "in million", "million", "mn"],
        "transform_sort:desc": ["descending", "desc", "high to low", "highest", "largest", "greatest", "top"],
        "transform_sort:asc": ["ascending", "asc", "low to high", "lowest", "bottom", "least", "smallest"],
        "transform_projection:only": ["only", "only these", "only this", "just these", "just this"],
        "transform_aggregate:sum": ["total", "sum"],
    },
    "record_query_stop_tokens": [
        "show",
        "me",
        "the",
        "latest",
        "recent",
        "newest",
        "last",
        "from",
        "this",
        "that",
        "these",
        "those",
        "month",
        "week",
        "year",
        "records",
        "record",
        "list",
        "give",
        "all",
        "for",
        "in",
        "of",
    ],
    "generic_record_entity_tokens": [
        "invoice",
        "order",
        "entry",
        "receipt",
        "request",
        "payment",
    ],
    "generic_metric_terms": ["amount", "value", "total"],
}


def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    for p in [cur] + list(cur.parents):
        if (p / "impl_factory").is_dir():
            return p
    return cur.parent


def _contracts_dir() -> Path:
    return Path(__file__).resolve().parent / "v7" / "contracts_data"


def _default_generated_path() -> Path:
    return _repo_root() / "impl_factory/04_automation/capability_v7/latest_ontology_generated.json"


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _as_alias_map(obj: Any) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    if not isinstance(obj, dict):
        return out
    for k, vals in obj.items():
        kk = str(k or "").strip()
        if not kk:
            continue
        seen: Set[str] = set()
        arr: List[str] = []
        for v in list(vals or []):
            s = str(v or "").strip()
            if not s:
                continue
            sl = s.lower()
            if sl in seen:
                continue
            seen.add(sl)
            arr.append(s)
        out[kk] = arr
    return out


def _as_str_map(obj: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(obj, dict):
        return out
    for k, v in obj.items():
        kk = str(k or "").strip()
        vv = str(v or "").strip()
        if kk and vv:
            out[kk] = vv
    return out


def _merge_alias_maps(base: Dict[str, List[str]], extra: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {str(k): list(v) for k, v in (base or {}).items()}
    for k, vals in (extra or {}).items():
        kk = str(k)
        cur = list(out.get(kk) or [])
        seen = {str(x).strip().lower() for x in cur if str(x).strip()}
        for v in list(vals or []):
            s = str(v or "").strip()
            if not s:
                continue
            sl = s.lower()
            if sl in seen:
                continue
            seen.add(sl)
            cur.append(s)
        out[kk] = cur
    return out


def _merge_catalog(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base or {})

    for key in (
        "metric_aliases",
        "metric_column_aliases",
        "domain_aliases",
        "dimension_aliases",
        "primary_dimension_aliases",
        "filter_kind_aliases",
        "write_operation_aliases",
        "write_doctype_aliases",
        "export_aliases",
        "reference_value_aliases",
        "transform_ambiguity_aliases",
    ):
        out[key] = _merge_alias_maps(_as_alias_map(out.get(key)), _as_alias_map(extra.get(key)))

    metric_domain_map = _as_str_map(out.get("metric_domain_map"))
    metric_domain_map.update(_as_str_map(extra.get("metric_domain_map")))
    out["metric_domain_map"] = metric_domain_map

    terms: List[str] = []
    seen: Set[str] = set()
    for src in (list(out.get("generic_metric_terms") or []), list(extra.get("generic_metric_terms") or [])):
        for t in src:
            s = str(t or "").strip().lower()
            if (not s) or (s in seen):
                continue
            seen.add(s)
            terms.append(s)
    out["generic_metric_terms"] = terms

    def _merge_str_set(key: str) -> None:
        merged: List[str] = []
        seen: Set[str] = set()
        for src in (list(out.get(key) or []), list(extra.get(key) or [])):
            for v in src:
                s = str(v or "").strip().lower()
                if (not s) or (s in seen):
                    continue
                seen.add(s)
                merged.append(s)
        out[key] = merged

    _merge_str_set("record_query_stop_tokens")
    _merge_str_set("generic_record_entity_tokens")
    return out


@lru_cache(maxsize=1)
def get_ontology_catalog() -> Dict[str, Any]:
    catalog = dict(_DEFAULT_ONTOLOGY)

    base_path = _contracts_dir() / "ontology_base_v1.json"
    if base_path.exists():
        catalog = _merge_catalog(catalog, _read_json(base_path))

    generated_env = str(os.environ.get("AI_ASSISTANT_V7_ONTOLOGY_GENERATED") or "").strip()
    generated_path = Path(generated_env) if generated_env else _default_generated_path()
    if generated_path.exists():
        catalog = _merge_catalog(catalog, _read_json(generated_path))

    overrides_path = _contracts_dir() / "ontology_overrides_v1.json"
    if overrides_path.exists():
        catalog = _merge_catalog(catalog, _read_json(overrides_path))

    return catalog


def clear_ontology_cache() -> None:
    get_ontology_catalog.cache_clear()


def _metric_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("metric_aliases"))


def _metric_domain_map() -> Dict[str, str]:
    return _as_str_map(get_ontology_catalog().get("metric_domain_map"))


def _metric_column_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("metric_column_aliases"))


def _domain_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("domain_aliases"))


def _dimension_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("dimension_aliases"))


def _primary_dimension_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("primary_dimension_aliases"))


def _filter_kind_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("filter_kind_aliases"))


def _write_operation_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("write_operation_aliases"))


def _write_doctype_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("write_doctype_aliases"))


def _export_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("export_aliases"))


def _reference_value_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("reference_value_aliases"))


def _transform_ambiguity_alias_map() -> Dict[str, List[str]]:
    return _as_alias_map(get_ontology_catalog().get("transform_ambiguity_aliases"))


def _generic_metric_terms() -> Set[str]:
    return {str(x).strip().lower() for x in list(get_ontology_catalog().get("generic_metric_terms") or []) if str(x).strip()}


def _record_query_stop_tokens() -> Set[str]:
    return {str(x).strip().lower() for x in list(get_ontology_catalog().get("record_query_stop_tokens") or []) if str(x).strip()}


def _generic_record_entity_tokens() -> Set[str]:
    return {str(x).strip().lower() for x in list(get_ontology_catalog().get("generic_record_entity_tokens") or []) if str(x).strip()}


def _contains_any(text: str, aliases: Iterable[str]) -> bool:
    t = _norm(text)
    if not t:
        return False
    semantic_tokens = set(_tokenize_semantic_text(t))
    for a in aliases:
        a_n = _norm(a)
        if not a_n:
            continue
        if " " not in a_n:
            alias_tokens = [tok for tok in _tokenize_semantic_text(a_n) if tok]
            if alias_tokens:
                if len(alias_tokens) == 1 and alias_tokens[0] in semantic_tokens:
                    return True
                if len(alias_tokens) > 1 and all(tok in semantic_tokens for tok in alias_tokens):
                    return True
        pattern = r"(?<![a-z0-9_])" + re.escape(a_n) + r"(?![a-z0-9_])"
        if re.search(pattern, t):
            return True
    return False


def canonical_metric(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for canonical, aliases in _metric_alias_map().items():
        if _contains_any(txt, aliases):
            return canonical
    return txt.replace(" ", "_")


def canonical_domain(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for canonical, aliases in _domain_alias_map().items():
        if _contains_any(txt, aliases):
            return canonical
    return txt.replace(" ", "_")


def canonical_dimension(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for canonical, aliases in _dimension_alias_map().items():
        if txt == canonical or txt.replace(" ", "_") == canonical:
            return canonical
        if _contains_any(txt, aliases):
            return canonical
    return txt.replace(" ", "_")


def known_metric(value: Any) -> str:
    canonical = canonical_metric(value)
    return canonical if canonical in _metric_alias_map() else ""


def known_dimension(value: Any) -> str:
    canonical = canonical_dimension(value)
    return canonical if canonical in _dimension_alias_map() else ""


def semantic_aliases(value: Any, *, exclude_generic_metric_terms: bool = False) -> List[str]:
    txt = _norm(value)
    if not txt:
        return []

    aliases: Set[str] = {txt.replace("_", " ")}

    metric = known_metric(txt)
    if metric:
        aliases.add(metric.replace("_", " "))
        for a in _metric_alias_map().get(metric, []):
            a_n = _norm(a).replace("_", " ")
            if a_n:
                aliases.add(a_n)

    dim = known_dimension(txt)
    if dim:
        aliases.add(dim.replace("_", " "))
        for a in _dimension_alias_map().get(dim, []):
            a_n = _norm(a).replace("_", " ")
            if a_n:
                aliases.add(a_n)

    if exclude_generic_metric_terms:
        blocked = _generic_metric_terms()
        aliases = {a for a in aliases if a not in blocked}

    return sorted(a for a in aliases if a)


def metric_domain(metric: Any) -> str:
    canonical = canonical_metric(metric)
    return _metric_domain_map().get(canonical, "")


def metric_column_aliases(metric: Any) -> List[str]:
    canonical = canonical_metric(metric)
    aliases: List[str] = []
    seen: Set[str] = set()
    for source in (_metric_column_alias_map().get(canonical) or [], _metric_alias_map().get(canonical) or []):
        for value in source:
            normalized = _norm(value).replace("_", " ")
            if (not normalized) or (normalized in seen):
                continue
            seen.add(normalized)
            aliases.append(normalized)
    return aliases


def infer_filter_kinds(text: Any) -> List[str]:
    source = _norm(text)
    if not source:
        return []
    out: Set[str] = set()
    for kind, aliases in _filter_kind_alias_map().items():
        if _contains_any(source, aliases):
            out.add(kind)
    if "year" in out and any(k in out for k in ("start_year", "end_year", "fiscal_year")):
        out.discard("year")
    return sorted(out)


def infer_metric_hints(
    *,
    report_name: str,
    report_family: str,
    supported_filter_names: Iterable[str],
    supported_filter_kinds: Iterable[str],
) -> List[str]:
    text = " ".join(
        [
            _norm(report_name),
            _norm(report_family),
            " ".join(_norm(x) for x in list(supported_filter_names or []) if _norm(x)),
            " ".join(_norm(x) for x in list(supported_filter_kinds or []) if _norm(x)),
        ]
    ).strip()
    if not text:
        return []

    out: Set[str] = set()
    metric_alias_map = _metric_alias_map()
    for canonical, aliases in metric_alias_map.items():
        if _contains_any(text, aliases):
            out.add(canonical)

    family = _norm(report_family)
    report = _norm(report_name)
    if ("selling" in family or "sales" in family) and ("item" in text or "customer" in text):
        out.add("revenue")
        out.add("sold_quantity")
    if ("sales register" in report) or ("item-wise sales register" in report):
        out.add("revenue")
        out.add("sold_quantity")
    if ("buying" in family or "purchase" in family) and ("item" in text or "supplier" in text):
        out.add("received_quantity")
    if ("projected qty" in text) or ("projected quantity" in text) or ("projected_qty" in text):
        out.add("projected_quantity")
    if ("stock" in family or "inventory" in family) and ("balance" in text):
        out.add("stock_balance")
    if ("accounts" in family or "finance" in family) and ("outstanding" in text or "ledger" in text):
        out.add("outstanding_amount")
    if ("material request" in text) or ("production" in text):
        out.add("open_requests")

    return sorted(out)


def infer_primary_dimension(report_name: Any) -> str:
    txt = _norm(report_name)
    if not txt:
        return ""
    for dim, aliases in _primary_dimension_alias_map().items():
        if _contains_any(txt, aliases):
            return dim
    return ""


def infer_domain_hints_from_report(report_name: Any, report_family: Any, filter_kinds: Iterable[str]) -> List[str]:
    txt = _norm(report_name)
    family = _norm(report_family)
    kinds = {str(x or "").strip().lower() for x in filter_kinds}
    out: Set[str] = set()
    source = f"{txt} {family}".strip()

    # Domain inference is driven by ontology aliases (generated + override + base),
    # not inline phrase rules in runtime modules.
    for domain, aliases in _domain_alias_map().items():
        if _contains_any(source, aliases):
            out.add(domain)

    if not out:
        # Deterministic fallback by canonical filter kind only.
        if "warehouse" in kinds:
            out.add("inventory")
        if "supplier" in kinds:
            out.add("purchasing")
        if "customer" in kinds:
            out.add("sales")
        if "company" in kinds and not out:
            out.add("finance")
    if not out:
        out.add("cross_functional")
    return sorted(out)


def infer_write_request(message: Any) -> Dict[str, Any]:
    txt = _norm(message)
    if not txt:
        return {"intent": "", "operation": "", "doctype": "", "document_id": "", "confidence": 0.0}

    def _has_alias(alias: str) -> bool:
        a = _norm(alias)
        if not a:
            return False
        if re.fullmatch(r"[a-z0-9_ ]+", a):
            return bool(re.search(rf"(?<!\\w){re.escape(a)}(?!\\w)", txt))
        return a in txt

    op = ""
    op_score = 0.0
    for operation, aliases in _write_operation_alias_map().items():
        for alias in aliases:
            if _has_alias(alias):
                op = operation
                op_score = 0.8
                break
        if op:
            break

    doctype = ""
    for dt, aliases in _write_doctype_alias_map().items():
        if _contains_any(txt, aliases):
            doctype = dt
            break

    doc_id = ""
    msg_raw = str(message or "")
    if op in {"delete", "update"}:
        for rx in (
            r"\b[A-Za-z]{2,}-[A-Za-z0-9-]{3,}\b",
            r"\b[a-z0-9]{8,20}\b",
            r"\b[A-Za-z0-9]{6,}\b",
        ):
            m = re.search(rx, msg_raw)
            if m:
                cand = str(m.group(0) or "").strip()
                if cand and cand.lower() not in {"delete", "update", "remove", "todo"}:
                    doc_id = cand
                    break

    word_count = len([w for w in re.findall(r"[A-Za-z0-9_]+", txt) if w])
    if op in {"confirm", "cancel"} and (word_count <= 3):
        return {
            "intent": "WRITE_CONFIRM",
            "operation": op,
            "doctype": doctype,
            "document_id": doc_id,
            "confidence": 0.9,
        }

    if op in {"create", "update", "delete"} and doctype:
        return {
            "intent": "WRITE_DRAFT",
            "operation": op,
            "doctype": doctype,
            "document_id": doc_id,
            "confidence": op_score,
        }

    return {"intent": "", "operation": "", "doctype": "", "document_id": "", "confidence": 0.0}


def infer_output_flags(message: Any) -> Dict[str, Any]:
    txt = _norm(message)
    if not txt:
        return {"include_download": False}
    include_download = _contains_any(txt, _export_alias_map().get("include_download") or [])
    return {"include_download": bool(include_download)}


def infer_reference_value(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for code, aliases in _reference_value_alias_map().items():
        if _contains_any(txt, aliases):
            return str(code).strip()
    return ""


def infer_transform_ambiguities(message: Any) -> List[str]:
    txt = _norm(message)
    if not txt:
        return []
    out: Set[str] = set()
    for code, aliases in _transform_ambiguity_alias_map().items():
        if _contains_any(txt, aliases):
            out.add(str(code).strip())
    return sorted([x for x in out if x])


def _tokenize_semantic_text(value: Any) -> List[str]:
    txt = _norm(value)
    if not txt:
        return []
    raw = [t for t in re.findall(r"[a-z0-9]+", txt) if t]
    out: List[str] = []
    seen: Set[str] = set()
    for token in raw:
        variants = [token]
        if len(token) >= 4 and token.endswith("ies"):
            variants.append(token[:-3] + "y")
        if len(token) >= 4 and token.endswith("es"):
            variants.append(token[:-2])
        if len(token) >= 4 and token.endswith("s"):
            variants.append(token[:-1])
        for v in variants:
            s = str(v or "").strip().lower()
            if (not s) or (s in seen):
                continue
            seen.add(s)
            out.append(s)
    return out


def infer_record_doctype_candidates(
    *,
    query_parts: Iterable[str],
    candidate_doctypes: Iterable[str],
    domain: Any = "",
) -> List[str]:
    """
    Ontology-bound candidate scoring for record listing tasks.
    Keeps lexical logic out of runtime core modules.
    """
    doctypes = [str(d or "").strip() for d in list(candidate_doctypes or []) if str(d or "").strip()]
    if not doctypes:
        return []
    query_text = " ".join([str(x or "").strip().lower() for x in list(query_parts or []) if str(x or "").strip()]).strip()
    if not query_text:
        return []

    exact: List[str] = []
    for dt in doctypes:
        dt_norm = str(dt or "").strip().lower()
        if dt_norm and (dt_norm in query_text):
            exact.append(dt)
    if exact:
        return sorted(list(dict.fromkeys(exact)))

    q_tokens = [t for t in _tokenize_semantic_text(query_text) if t not in _record_query_stop_tokens() and not t.isdigit()]
    if not q_tokens:
        return []

    generic_tokens = _generic_record_entity_tokens()
    single_generic_entity = len(set(q_tokens)) == 1 and (q_tokens[0] in generic_tokens)
    domain_l = str(canonical_domain(domain) or _norm(domain) or "").strip().lower()

    scored: List[Dict[str, Any]] = []
    for dt in doctypes:
        dt_name = str(dt or "").strip()
        dt_tokens = set(_tokenize_semantic_text(dt_name))
        if not dt_tokens:
            continue
        overlap = [t for t in q_tokens if t in dt_tokens]
        if not overlap:
            continue
        score = float(len(set(overlap))) * 3.0
        if (not single_generic_entity) and domain_l and domain_l not in {"", "unknown", "cross_functional"}:
            if domain_l == "sales" and (("sale" in dt_tokens) or ("sales" in dt_tokens)):
                score += 2.0
            if domain_l == "purchasing" and (("purchase" in dt_tokens) or ("supplier" in dt_tokens)):
                score += 2.0
            if domain_l == "inventory" and (("stock" in dt_tokens) or ("inventory" in dt_tokens)):
                score += 2.0
        scored.append({"doctype": dt_name, "score": score})

    scored.sort(key=lambda x: (float(x.get("score") or 0.0), str(x.get("doctype") or "")), reverse=True)
    if not scored:
        return []
    top_score = float(scored[0].get("score") or 0.0)
    threshold = max(1.0, top_score - (0.5 if not single_generic_entity else 3.0))
    winners = [str(x.get("doctype") or "").strip() for x in scored if float(x.get("score") or 0.0) >= threshold]
    return sorted(list(dict.fromkeys([w for w in winners if w])))
