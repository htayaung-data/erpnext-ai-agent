from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import frappe

from ai_assistant_ui.ai_core.fac.client import fac_report_requirements
from ai_assistant_ui.ai_core.fac.normalize import NormalizedRequirements, normalize_requirements_output


def _parse_filters_from_report_script(script_text: str) -> List[Dict[str, Any]]:
    script = str(script_text or "")
    if not script:
        return []
    matches = list(re.finditer(r'fieldname\s*:\s*"([^"]+)"', script))
    if not matches:
        return []

    out: List[Dict[str, Any]] = []
    for idx, m in enumerate(matches):
        fieldname = str(m.group(1) or "").strip()
        if not fieldname:
            continue
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else min(len(script), start + 1200)
        block = script[start:end]

        def _pick(pattern: str) -> str:
            mm = re.search(pattern, block, flags=re.IGNORECASE | re.MULTILINE)
            return str(mm.group(1) or "").strip() if mm else ""

        label = _pick(r'label\s*:\s*__\(\s*"([^"]+)"\s*\)')
        if not label:
            label = _pick(r'label\s*:\s*"([^"]+)"')
        fieldtype = _pick(r'fieldtype\s*:\s*"([^"]+)"')
        options = _pick(r'options\s*:\s*"([^"]+)"')
        reqd = 1 if re.search(r"reqd\s*:\s*1", block, flags=re.IGNORECASE) else 0

        out.append(
            {
                "fieldname": fieldname,
                "label": label or fieldname.replace("_", " ").title(),
                "fieldtype": fieldtype,
                "options": options,
                "reqd": reqd,
            }
        )
    return out


def _fallback_requirements_from_frappe(report_name: str) -> NormalizedRequirements:
    """
    Fallback when FAC report_requirements() is not available.
    We infer filters from Frappe's report doc (metadata only).
    """
    filters: Any = []
    report_type = ""
    module = ""
    metadata_access_ok = False

    # Primary fallback: use Report doctype metadata through tools_read adapter.
    try:
        from ai_assistant_ui.ai_core.tools_read import report_requirements as _report_requirements

        req_data = _report_requirements(
            report_name=report_name,
            include_metadata=True,
            include_columns=False,
            include_filters=True,
        )
        if isinstance(req_data, dict):
            metadata_access_ok = True
            if isinstance(req_data.get("filters"), list):
                filters = req_data.get("filters") or []
            report_type = str(req_data.get("report_type") or "").strip()
            module = str(req_data.get("module") or "").strip()
    except Exception:
        pass

    # Secondary fallback: query report metadata.
    if not filters:
        try:
            from frappe.desk.query_report import get_report_doc  # type: ignore

            rep = get_report_doc(report_name)
            metadata_access_ok = True
            filters = rep.get("filters") or []
            report_type = report_type or str(rep.get("report_type") or "").strip()
            module = module or str(rep.get("module") or "").strip()
        except Exception:
            filters = []

    # Last fallback: Report doctype JSON metadata.
    if not filters:
        try:
            rep_doc = frappe.get_doc("Report", report_name)
            metadata_access_ok = True
            report_type = report_type or str(rep_doc.get("report_type") or "").strip()
            module = module or str(rep_doc.get("module") or "").strip()
            if isinstance(rep_doc.get("filters"), list):
                filters = rep_doc.get("filters") or []
            else:
                raw_json = rep_doc.get("json")
                if raw_json:
                    obj = json.loads(str(raw_json))
                    if isinstance(obj, dict) and isinstance(obj.get("filters"), list):
                        filters = obj.get("filters") or []
        except Exception:
            return NormalizedRequirements(required_filter_names=[], filters_definition=[], raw_type="fallback_empty")

    # Script-report fallback: parse JS filter config when report metadata is empty.
    if not filters:
        try:
            from frappe.desk.query_report import get_script  # type: ignore

            script_obj = get_script(report_name)
            script_text = ""
            if isinstance(script_obj, dict):
                metadata_access_ok = True
                script_text = str(script_obj.get("script") or "")
                report_type = report_type or str(script_obj.get("report_type") or "").strip()
            filters = _parse_filters_from_report_script(script_text)
        except Exception:
            filters = []

    filters_def: List[Dict[str, Any]] = []
    required: List[str] = []

    for f in filters:
        if not isinstance(f, dict):
            continue
        fd = dict(f)
        fn = fd.get("fieldname")
        if not fn:
            continue

        # normalize reqd flag (sometimes "reqd", "mandatory")
        reqd = fd.get("reqd")
        if reqd is None:
            reqd = fd.get("mandatory")
        if int(reqd or 0) == 1:
            required.append(fn)

        filters_def.append(fd)

    if filters_def:
        raw_type = "fallback_report_metadata"
        if report_type:
            raw_type = f"{raw_type}:{report_type}"
        if module:
            raw_type = f"{raw_type}:{module}"
        return NormalizedRequirements(required_filter_names=required, filters_definition=filters_def, raw_type=raw_type)

    if metadata_access_ok:
        raw_type = "fallback_report_metadata_no_filters"
        if report_type:
            raw_type = f"{raw_type}:{report_type}"
        if module:
            raw_type = f"{raw_type}:{module}"
        return NormalizedRequirements(required_filter_names=[], filters_definition=[], raw_type=raw_type)

    return NormalizedRequirements(required_filter_names=[], filters_definition=[], raw_type="fallback_empty")


def get_report_requirements(report_name: str, *, user: Optional[str] = None) -> NormalizedRequirements:
    """
    Preferred: FAC report_requirements()
    Fallback: infer from frappe.desk.query_report metadata
    """
    user = user or frappe.session.user

    try:
        raw = fac_report_requirements(report_name, user=user)
        return normalize_requirements_output(raw)
    except Exception:
        return _fallback_requirements_from_frappe(report_name)
