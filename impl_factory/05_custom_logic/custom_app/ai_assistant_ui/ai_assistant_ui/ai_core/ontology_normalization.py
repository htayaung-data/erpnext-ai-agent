from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Set


METRIC_ALIAS_MAP: Dict[str, List[str]] = {
    "revenue": [
        "revenue",
        "sales",
        "sales amount",
        "sales value",
        "invoiced amount",
        "income",
        "total sales",
        "amount",
    ],
    "sold_quantity": [
        "sold quantity",
        "sold qty",
        "sales qty",
        "sales quantity",
        "qty sold",
        "stock qty",
        "quantity sold",
    ],
    "received_quantity": [
        "received quantity",
        "received qty",
        "purchase qty",
        "qty received",
    ],
    "stock_balance": [
        "stock balance",
        "item balance",
        "balance qty",
        "warehouse balance",
        "inventory balance",
    ],
    "outstanding_amount": [
        "outstanding amount",
        "total amount due",
        "amount due",
        "receivable amount",
        "payable amount",
    ],
    "open_requests": [
        "open requests",
        "open material requests",
        "pending requests",
        "material request",
    ],
}

METRIC_DOMAIN_MAP: Dict[str, str] = {
    "revenue": "sales",
    "sold_quantity": "sales",
    "received_quantity": "purchasing",
    "stock_balance": "inventory",
    "outstanding_amount": "finance",
    "open_requests": "operations",
}

DOMAIN_ALIAS_MAP: Dict[str, List[str]] = {
    "sales": ["sales", "selling", "customer", "invoice"],
    "purchasing": ["purchase", "buying", "supplier", "vendor"],
    "inventory": ["stock", "inventory", "warehouse", "item balance"],
    "finance": ["receivable", "payable", "ledger", "outstanding", "account"],
    "operations": ["material request", "production", "manufacturing", "work order"],
    "hr": ["employee", "attendance", "leave", "payroll", "hr"],
}

DIMENSION_ALIAS_MAP: Dict[str, List[str]] = {
    "customer": ["customer", "party"],
    "supplier": ["supplier", "vendor"],
    "item": ["item", "product", "sku"],
    "warehouse": ["warehouse", "store"],
    "territory": ["territory", "region", "city"],
    "company": ["company", "business unit"],
}

PRIMARY_DIMENSION_ALIAS_MAP: Dict[str, List[str]] = {
    "customer": ["customer-wise", "customer wise", "customer"],
    "supplier": ["supplier-wise", "supplier wise", "supplier", "vendor"],
    "item": ["item-wise", "item wise", "product-wise", "product wise", "item", "product", "sku"],
    "warehouse": ["warehouse-wise", "warehouse wise", "warehouse"],
    "territory": ["territory-wise", "territory wise", "territory", "region"],
    "sales_person": ["sales person-wise", "sales person wise", "sales person"],
    "sales_partner": ["sales partner-wise", "sales partner wise", "sales partner"],
}

FILTER_KIND_ALIAS_MAP: Dict[str, List[str]] = {
    "warehouse": ["warehouse"],
    "company": ["company"],
    "customer": ["customer"],
    "supplier": ["supplier", "vendor"],
    "item": ["item", "product", "sku"],
    "date": ["date", "posting", "as on", "as_of"],
    "from_date": ["from_date", "from date"],
    "to_date": ["to_date", "to date"],
    "report_date": ["report_date", "report date", "as on", "as_of"],
    "start_year": ["start_year", "start year", "from_year", "from year"],
    "end_year": ["end_year", "end year", "to_year", "to year"],
    "fiscal_year": ["fiscal_year", "fiscal year"],
    "year": ["year"],
}

WRITE_OPERATION_ALIAS_MAP: Dict[str, List[str]] = {
    "create": ["create", "add", "new", "make"],
    "update": ["update", "edit", "change", "modify", "set"],
    "delete": ["delete", "remove"],
    "confirm": ["confirm", "yes", "proceed", "approve", "execute", "do it", "ok", "okay"],
    "cancel": ["cancel", "stop", "abort", "no"],
}

WRITE_DOCTYPE_ALIAS_MAP: Dict[str, List[str]] = {
    "ToDo": ["todo", "to do", "task"],
}

EXPORT_ALIAS_MAP: Dict[str, List[str]] = {
    "include_download": ["download", "export", "excel", "xlsx", "csv", "pdf"],
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains_any(text: str, aliases: Iterable[str]) -> bool:
    t = _norm(text)
    if not t:
        return False
    for a in aliases:
        a_n = _norm(a)
        if a_n and a_n in t:
            return True
    return False


def canonical_metric(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for canonical, aliases in METRIC_ALIAS_MAP.items():
        if _contains_any(txt, aliases):
            return canonical
    return txt.replace(" ", "_")


def canonical_domain(value: Any) -> str:
    txt = _norm(value)
    if not txt:
        return ""
    for canonical, aliases in DOMAIN_ALIAS_MAP.items():
        if _contains_any(txt, aliases):
            return canonical
    return txt.replace(" ", "_")


def canonical_dimension(value: Any) -> str:
    txt = _norm(value).replace(" ", "_")
    if not txt:
        return ""
    for canonical, aliases in DIMENSION_ALIAS_MAP.items():
        if txt == canonical:
            return canonical
        if _contains_any(txt, aliases):
            return canonical
    return txt


def metric_domain(metric: Any) -> str:
    canonical = canonical_metric(metric)
    return METRIC_DOMAIN_MAP.get(canonical, "")


def infer_filter_kinds(text: Any) -> List[str]:
    source = _norm(text)
    if not source:
        return []
    out: Set[str] = set()
    for kind, aliases in FILTER_KIND_ALIAS_MAP.items():
        if _contains_any(source, aliases):
            out.add(kind)
    # year is a fallback only when start/end/fiscal are absent.
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
    for canonical, aliases in METRIC_ALIAS_MAP.items():
        if _contains_any(text, aliases):
            out.add(canonical)

    # Lightweight structural priors by report family/name.
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
    if ("stock" in family or "inventory" in family) and ("balance" in text or "warehouse" in text):
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
    for dim, aliases in PRIMARY_DIMENSION_ALIAS_MAP.items():
        if _contains_any(txt, aliases):
            return dim
    return ""


def infer_domain_hints_from_report(report_name: Any, report_family: Any, filter_kinds: Iterable[str]) -> List[str]:
    txt = _norm(report_name)
    family = _norm(report_family)
    kinds = {str(x or "").strip().lower() for x in filter_kinds}
    out: Set[str] = set()

    if any(x in txt for x in ("sales", "customer", "invoice", "receivable")):
        out.add("sales")
    if any(x in txt for x in ("purchase", "supplier", "payable")):
        out.add("purchasing")
    if any(x in txt for x in ("stock", "inventory", "warehouse")):
        out.add("inventory")
    if any(x in txt for x in ("material request", "production", "manufacturing")):
        out.add("operations")

    if "accounts" in family or "assets" in family:
        out.add("finance")
    if "selling" in family or "crm" in family:
        out.add("sales")
    if "buying" in family:
        out.add("purchasing")
    if "stock" in family or "inventory" in family:
        out.add("inventory")
    if "manufacturing" in family or "production" in family or "project" in family:
        out.add("operations")
    if "human resources" in family or "hr" in family or "payroll" in family:
        out.add("hr")

    if not out:
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
            # strict token/phrase boundary for operation aliases
            return bool(re.search(rf"(?<!\\w){re.escape(a)}(?!\\w)", txt))
        return a in txt

    op = ""
    op_score = 0.0
    for operation, aliases in WRITE_OPERATION_ALIAS_MAP.items():
        for alias in aliases:
            if _has_alias(alias):
                op = operation
                op_score = 0.8
                break
        if op:
            break

    doctype = ""
    for dt, aliases in WRITE_DOCTYPE_ALIAS_MAP.items():
        if _contains_any(txt, aliases):
            doctype = dt
            break

    doc_id = ""
    msg_raw = str(message or "")
    if op in {"delete", "update"}:
        for rx in (
            r"\b[A-Za-z]{2,}-[A-Za-z0-9-]{3,}\b",   # ACC-SINV-2026-00013
            r"\b[a-z0-9]{8,20}\b",                   # todo ids
            r"\b[A-Za-z0-9]{6,}\b",                  # generic fallback
        ):
            m = re.search(rx, msg_raw)
            if m:
                cand = str(m.group(0) or "").strip()
                if cand and cand.lower() not in {"delete", "update", "remove", "todo"}:
                    doc_id = cand
                    break

    # confirm/cancel without an explicit write target should only be treated as
    # write-intent for short direct replies.
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
    include_download = _contains_any(txt, EXPORT_ALIAS_MAP.get("include_download") or [])
    return {"include_download": bool(include_download)}
