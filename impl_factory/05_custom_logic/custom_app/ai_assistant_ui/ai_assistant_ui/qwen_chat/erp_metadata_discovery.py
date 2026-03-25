from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set

import frappe

from ai_assistant_ui.qwen_chat.metadata import (
	load_capability_registry,
	load_report_registry,
	get_report_surface_evidence_spec,
	list_report_surface_evidence_specs,
)


def _utc_now_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _jsonable_default(value: Any) -> Any:
	if isinstance(value, (dt.date, dt.datetime)):
		return value.isoformat()
	return str(value)


def _field_payload(field) -> Dict[str, Any]:
	return {
		"fieldname": _clean_text(getattr(field, "fieldname", "")),
		"label": _clean_text(getattr(field, "label", "")),
		"fieldtype": _clean_text(getattr(field, "fieldtype", "")),
		"options": _clean_text(getattr(field, "options", "")),
		"reqd": bool(getattr(field, "reqd", 0)),
		"in_list_view": bool(getattr(field, "in_list_view", 0)),
		"in_standard_filter": bool(getattr(field, "in_standard_filter", 0)),
	}


def _report_filter_payload(row) -> Dict[str, Any]:
	return {
		"fieldname": _clean_text(getattr(row, "fieldname", "")),
		"label": _clean_text(getattr(row, "label", "")),
		"fieldtype": _clean_text(getattr(row, "fieldtype", "")),
		"reqd": bool(getattr(row, "reqd", 0)),
		"default": _clean_text(getattr(row, "default", "")),
	}


def _report_column_payload(row) -> Dict[str, Any]:
	return {
		"fieldname": _clean_text(getattr(row, "fieldname", "")),
		"label": _clean_text(getattr(row, "label", "")),
		"fieldtype": _clean_text(getattr(row, "fieldtype", "")),
		"options": _clean_text(getattr(row, "options", "")),
		"width": _clean_text(getattr(row, "width", "")),
	}


def _governed_report_specs_by_name() -> Dict[str, Dict[str, Any]]:
	values = load_report_registry().get("reports")
	if not isinstance(values, list):
		return {}
	return {
		_clean_text(item.get("report_name")): dict(item)
		for item in values
		if isinstance(item, dict) and _clean_text(item.get("report_name"))
	}


def _governed_report_names_by_surface_mode() -> Dict[str, Set[str]]:
	names: Dict[str, Set[str]] = {
		"report_backed": set(),
		"direct_query": set(),
		"other": set(),
	}
	for spec in _governed_report_specs_by_name().values():
		grounding_mode = _clean_text(spec.get("grounding_mode"))
		report_name = _clean_text(spec.get("report_name"))
		if not report_name:
			continue
		if grounding_mode == "direct_query":
			names["direct_query"].add(report_name)
		elif grounding_mode == "report":
			names["report_backed"].add(report_name)
		else:
			names["other"].add(report_name)
	return names


def _governed_report_surface_hints(report_name: str) -> Dict[str, Any]:
	spec = _governed_report_specs_by_name().get(_clean_text(report_name), {})
	if not spec:
		return {}
	direct_query = spec.get("direct_query") if isinstance(spec.get("direct_query"), dict) else {}
	return {
		"report_name": _clean_text(spec.get("report_name")),
		"family": _clean_text(spec.get("family")),
		"capability_ids": _clean_list(spec.get("capability_ids")),
		"grounding_mode": _clean_text(spec.get("grounding_mode")),
		"validation_profile": _clean_text(spec.get("validation_profile")),
		"required_filters": _clean_list(spec.get("required_filters")),
		"defaultable_filters": list(spec.get("defaultable_filters") or []) if isinstance(spec.get("defaultable_filters"), list) else [],
		"supported_intent_classes": _clean_list(spec.get("supported_intent_classes")),
		"semantic_tags": _clean_list(spec.get("semantic_tags")),
		"supported_dimensions": _clean_list(spec.get("supported_dimensions")),
		"supported_metrics": _clean_list(spec.get("supported_metrics")),
		"approved_follow_up_modes": _clean_list(spec.get("approved_follow_up_modes")),
		"chartable_fields": _clean_list(spec.get("chartable_fields")),
		"direct_query": {
			"doctype": _clean_text(direct_query.get("doctype")),
			"fields": _clean_list(direct_query.get("fields")),
			"order_by": _clean_text(direct_query.get("order_by")),
			"date_field": _clean_text(direct_query.get("date_field")),
			"default_limit": direct_query.get("default_limit"),
		} if direct_query else {},
	}


def _governed_report_evidence_policy(report_name: str) -> Dict[str, Any]:
	spec = get_report_surface_evidence_spec(report_name)
	if not spec:
		return {}
	return {
		"report_name": _clean_text(spec.get("report_name")),
		"evidence_class": _clean_text(spec.get("evidence_class")),
		"discovery_proves": _clean_list(spec.get("discovery_proves")),
		"discovery_does_not_prove": _clean_list(spec.get("discovery_does_not_prove")),
		"runtime_semantic_assumptions": _clean_list(spec.get("runtime_semantic_assumptions")),
		"recommended_runtime_posture": _clean_text(spec.get("recommended_runtime_posture")),
	}


def _doctype_surface(doctype_name: str) -> Dict[str, Any]:
	meta = frappe.get_meta(doctype_name)
	search_fields = []
	raw_search = _clean_text(getattr(meta, "search_fields", ""))
	if raw_search:
		search_fields = [part for part in [_clean_text(item) for item in raw_search.split(",")] if part]
	return {
		"doctype": doctype_name,
		"module": _clean_text(getattr(meta, "module", "")),
		"istable": bool(getattr(meta, "istable", 0)),
		"custom": bool(getattr(meta, "custom", 0)),
		"title_field": _clean_text(getattr(meta, "title_field", "")),
		"search_fields": search_fields,
		"field_count": len(getattr(meta, "fields", []) or []),
		"fields": [
			_field_payload(field)
			for field in (getattr(meta, "fields", []) or [])
			if _clean_text(getattr(field, "fieldname", "")) or _clean_text(getattr(field, "label", ""))
		],
	}


def _report_surface(report_row: Dict[str, Any]) -> Dict[str, Any]:
	report_name = _clean_text(report_row.get("name"))
	report_doc = frappe.get_doc("Report", report_name)
	declared_filters = [
		_report_filter_payload(row)
		for row in (getattr(report_doc, "filters", []) or [])
		if _clean_text(getattr(row, "fieldname", "")) or _clean_text(getattr(row, "label", ""))
	]
	declared_columns = [
		_report_column_payload(row)
		for row in (getattr(report_doc, "columns", []) or [])
		if _clean_text(getattr(row, "fieldname", "")) or _clean_text(getattr(row, "label", ""))
	]
	governed_hints = _governed_report_surface_hints(report_name)
	governed_evidence_policy = _governed_report_evidence_policy(report_name)
	surface_sources: List[str] = []
	if declared_filters or declared_columns:
		surface_sources.append("erp_report_doc")
	if governed_hints:
		surface_sources.append("governed_registry")
	if governed_evidence_policy:
		surface_sources.append("governed_evidence_policy")
	return {
		"report_name": report_name,
		"module": _clean_text(getattr(report_doc, "module", "") or report_row.get("module")),
		"ref_doctype": _clean_text(getattr(report_doc, "ref_doctype", "") or report_row.get("ref_doctype")),
		"report_type": _clean_text(getattr(report_doc, "report_type", "") or report_row.get("report_type")),
		"is_standard": _clean_text(getattr(report_doc, "is_standard", "") or report_row.get("is_standard")),
		"prepared_report": bool(getattr(report_doc, "prepared_report", 0)),
		"disabled": bool(getattr(report_doc, "disabled", 0)),
		"roles": [_clean_text(getattr(row, "role", "")) for row in (getattr(report_doc, "roles", []) or []) if _clean_text(getattr(row, "role", ""))],
		"filters": declared_filters,
		"columns": declared_columns,
		"governed_surface_hints": governed_hints,
		"governed_evidence_policy": governed_evidence_policy,
		"surface_sources": surface_sources,
		"surface_assessment": {
			"erp_declared_surface": bool(declared_filters or declared_columns),
			"governed_hint_surface": bool(governed_hints),
			"governed_evidence_policy": bool(governed_evidence_policy),
		},
	}


def get_report_surface_summary(report_name: str) -> Dict[str, Any]:
	report = _clean_text(report_name)
	if not report:
		return {}
	report_row = {}
	if frappe.db.exists("Report", report):
		report_row = frappe.db.get_value(
			"Report",
			report,
			["name", "ref_doctype", "report_type", "module", "is_standard"],
			as_dict=True,
		) or {}
	if report_row:
		return _report_surface(report_row)
	governed_hints = _governed_report_surface_hints(report)
	governed_evidence_policy = _governed_report_evidence_policy(report)
	if not governed_hints:
		return {}
	return {
		"report_name": report,
		"module": _clean_text(governed_hints.get("module")),
		"ref_doctype": _clean_text((governed_hints.get("direct_query") or {}).get("doctype")),
		"report_type": "",
		"is_standard": "",
		"prepared_report": False,
		"disabled": False,
		"roles": [],
		"filters": [],
		"columns": [],
		"governed_surface_hints": governed_hints,
		"governed_evidence_policy": governed_evidence_policy,
		"surface_sources": [value for value in ["governed_registry", "governed_evidence_policy" if governed_evidence_policy else ""] if value],
		"surface_assessment": {
			"erp_declared_surface": False,
			"governed_hint_surface": True,
			"governed_evidence_policy": bool(governed_evidence_policy),
		},
	}


def _governed_alignment_payload(discovered_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
	governed_capability_specs = load_capability_registry().get("capabilities")
	governed_report_names_by_surface = _governed_report_names_by_surface_mode()
	governed_report_names = set().union(
		governed_report_names_by_surface["report_backed"],
		governed_report_names_by_surface["direct_query"],
		governed_report_names_by_surface["other"],
	)
	governed_capability_ids = {
		_clean_text(item.get("capability_id"))
		for item in (governed_capability_specs or [])
		if isinstance(item, dict) and _clean_text(item.get("capability_id"))
	}
	discovered_report_names = {
		_clean_text(item.get("report_name"))
		for item in discovered_reports
		if isinstance(item, dict) and _clean_text(item.get("report_name"))
	}
	return {
		"governed_report_count": len(governed_report_names),
		"discovered_report_count": len(discovered_report_names),
		"governed_reports_present_in_erp": sorted(governed_report_names.intersection(discovered_report_names)),
		"governed_reports_missing_from_erp": sorted(
			governed_report_names_by_surface["report_backed"].difference(discovered_report_names)
		),
		"governed_report_backed_count": len(governed_report_names_by_surface["report_backed"]),
		"governed_report_backed_present_in_erp": sorted(
			governed_report_names_by_surface["report_backed"].intersection(discovered_report_names)
		),
		"governed_direct_query_count": len(governed_report_names_by_surface["direct_query"]),
		"governed_direct_query_reports": sorted(governed_report_names_by_surface["direct_query"]),
		"governed_other_surface_count": len(governed_report_names_by_surface["other"]),
		"governed_other_surface_reports": sorted(governed_report_names_by_surface["other"]),
		"governed_capability_count": len(governed_capability_ids),
	}


def _latest_modified(doctype_name: str) -> str:
	rows = frappe.get_all(doctype_name, fields=["modified"], order_by="modified desc", limit=1)
	if not rows:
		return ""
	value = rows[0].get("modified")
	if isinstance(value, (dt.date, dt.datetime)):
		return value.isoformat()
	return _clean_text(value)


def build_discovered_erp_source_signature() -> Dict[str, Any]:
	return {
		"report_count": int(frappe.db.count("Report") or 0),
		"doctype_count": int(frappe.db.count("DocType") or 0),
		"custom_field_count": int(frappe.db.count("Custom Field") or 0),
		"property_setter_count": int(frappe.db.count("Property Setter") or 0),
		"latest_modified": {
			"Report": _latest_modified("Report"),
			"DocType": _latest_modified("DocType"),
			"Custom Field": _latest_modified("Custom Field"),
			"Property Setter": _latest_modified("Property Setter"),
		},
	}


def _default_snapshot_dir() -> Path:
	env_dir = _clean_text(os.environ.get("QWEN_DISCOVERY_OUTPUT_DIR"))
	if env_dir:
		return Path(env_dir)
	module_path = Path(__file__).resolve()
	repo_candidate = module_path
	for parent in module_path.parents:
		if parent.name == "erpai_project1" and (parent / "impl_factory").exists():
			return parent / "impl_factory" / "01_discovery" / "qwen_enterprise_metadata_snapshots"
	site_name = _clean_text(getattr(getattr(frappe, "local", None), "site", ""))
	if site_name:
		return Path("/home/frappe/frappe-bench/sites") / site_name / "private" / "files" / "qwen_discovery"
	return repo_candidate.parent / "qwen_discovery"


def build_discovered_erp_surface_snapshot() -> Dict[str, Any]:
	report_rows = frappe.get_all(
		"Report",
		fields=["name", "ref_doctype", "report_type", "module", "is_standard"],
		order_by="name asc",
	)
	discovered_reports = [_report_surface(row) for row in report_rows]
	referenced_doctypes: Set[str] = {
		_clean_text(item.get("ref_doctype"))
		for item in discovered_reports
		if _clean_text(item.get("ref_doctype"))
	}
	doctype_rows = frappe.get_all(
		"DocType",
		fields=["name", "module", "istable", "custom"],
		order_by="name asc",
	)
	all_doctypes_summary = [
		{
			"doctype": _clean_text(row.get("name")),
			"module": _clean_text(row.get("module")),
			"istable": bool(row.get("istable")),
			"custom": bool(row.get("custom")),
		}
		for row in doctype_rows
		if _clean_text(row.get("name"))
	]
	referenced_doctype_surfaces = [
		_doctype_surface(doctype_name)
		for doctype_name in sorted(referenced_doctypes)
		if frappe.db.exists("DocType", doctype_name)
	]
	return {
		"type": "qwen_discovered_erp_surface_snapshot",
		"contract_version": "1.0",
		"generated_at_utc": _utc_now_iso(),
		"site_name": _clean_text(getattr(getattr(frappe, "local", None), "site", "")),
		"source_signature": build_discovered_erp_source_signature(),
		"report_summary": {
			"report_count": len(discovered_reports),
			"referenced_doctype_count": len(referenced_doctypes),
		},
		"doctype_summary": {
			"doctype_count": len(all_doctypes_summary),
		},
		"governed_alignment": _governed_alignment_payload(discovered_reports),
		"reports": discovered_reports,
		"referenced_doctypes": referenced_doctype_surfaces,
		"all_doctypes_summary": all_doctypes_summary,
	}


def _load_snapshot(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def _report_type_breakdown(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	counts: Dict[str, int] = {}
	for item in reports or []:
		report_type = _clean_text(item.get("report_type")) or "Unknown"
		counts[report_type] = int(counts.get(report_type, 0) or 0) + 1
	return [
		{"report_type": report_type, "count": count}
		for report_type, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
	]


def build_discovery_evaluation_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
	reports = [item for item in (snapshot.get("reports") or []) if isinstance(item, dict)]
	governed_alignment = snapshot.get("governed_alignment") if isinstance(snapshot.get("governed_alignment"), dict) else {}
	script_reports_without_surface = [
		{
			"report_name": _clean_text(item.get("report_name")),
			"module": _clean_text(item.get("module")),
			"ref_doctype": _clean_text(item.get("ref_doctype")),
		}
		for item in reports
		if _clean_text(item.get("report_type")) == "Script Report"
		and not (item.get("filters") or [])
		and not (item.get("columns") or [])
	]
	script_reports_with_governed_hints = [
		{
			"report_name": _clean_text(item.get("report_name")),
			"module": _clean_text(item.get("module")),
			"ref_doctype": _clean_text(item.get("ref_doctype")),
			"family": _clean_text(((item.get("governed_surface_hints") or {}) if isinstance(item.get("governed_surface_hints"), dict) else {}).get("family")),
		}
		for item in reports
		if _clean_text(item.get("report_type")) == "Script Report"
		and not (item.get("filters") or [])
		and not (item.get("columns") or [])
		and bool(item.get("governed_surface_hints"))
	]
	governed_reports_with_evidence_policy = [
		{
			"report_name": _clean_text(item.get("report_name")),
			"evidence_class": _clean_text(((item.get("governed_evidence_policy") or {}) if isinstance(item.get("governed_evidence_policy"), dict) else {}).get("evidence_class")),
		}
		for item in reports
		if bool(item.get("governed_evidence_policy"))
	]
	report_surface_evidence_specs = list_report_surface_evidence_specs()
	all_report_surface_evidence_entries = [
		{
			"report_name": _clean_text(item.get("report_name")),
			"evidence_class": _clean_text(item.get("evidence_class")),
		}
		for item in report_surface_evidence_specs
		if _clean_text(item.get("report_name"))
	]
	referenced_doctypes = [item for item in (snapshot.get("referenced_doctypes") or []) if isinstance(item, dict)]
	custom_referenced_doctypes = [
		_clean_text(item.get("doctype"))
		for item in referenced_doctypes
		if bool(item.get("custom")) and _clean_text(item.get("doctype"))
	]
	return {
		"generated_at_utc": _clean_text(snapshot.get("generated_at_utc")),
		"site_name": _clean_text(snapshot.get("site_name")),
		"report_count": int((snapshot.get("report_summary") or {}).get("report_count") or 0),
		"doctype_count": int((snapshot.get("doctype_summary") or {}).get("doctype_count") or 0),
		"referenced_doctype_count": int((snapshot.get("report_summary") or {}).get("referenced_doctype_count") or 0),
		"governed_report_count": int(governed_alignment.get("governed_report_count") or 0),
		"governed_report_backed_count": int(governed_alignment.get("governed_report_backed_count") or 0),
		"governed_present_count": len(governed_alignment.get("governed_reports_present_in_erp") or []),
		"governed_missing_reports": list(governed_alignment.get("governed_reports_missing_from_erp") or []),
		"governed_direct_query_count": int(governed_alignment.get("governed_direct_query_count") or 0),
		"governed_direct_query_reports": list(governed_alignment.get("governed_direct_query_reports") or []),
		"report_type_breakdown": _report_type_breakdown(reports),
		"script_reports_without_declared_surface_count": len(script_reports_without_surface),
		"script_reports_without_declared_surface_sample": script_reports_without_surface[:25],
		"script_reports_with_governed_hints_count": len(script_reports_with_governed_hints),
		"script_reports_with_governed_hints_sample": script_reports_with_governed_hints[:25],
		"report_surface_evidence_registry_count": len(all_report_surface_evidence_entries),
		"report_surface_evidence_registry_sample": all_report_surface_evidence_entries[:25],
		"governed_reports_with_evidence_policy_count": len(governed_reports_with_evidence_policy),
		"governed_reports_with_evidence_policy_sample": governed_reports_with_evidence_policy[:25],
		"custom_referenced_doctype_count": len(custom_referenced_doctypes),
		"custom_referenced_doctype_sample": custom_referenced_doctypes[:25],
		"source_signature": snapshot.get("source_signature") if isinstance(snapshot.get("source_signature"), dict) else {},
	}


def _summary_markdown(summary: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# Qwen ERP Discovery Evaluation Summary",
		"",
		f"Generated at: {summary.get('generated_at_utc') or ''}",
		f"Site: {summary.get('site_name') or ''}",
		"",
		"## Counts",
		"",
		f"- Reports: {summary.get('report_count') or 0}",
		f"- Doctypes: {summary.get('doctype_count') or 0}",
		f"- Referenced doctypes: {summary.get('referenced_doctype_count') or 0}",
		f"- Governed reports: {summary.get('governed_report_count') or 0}",
		f"- Governed report-backed entries: {summary.get('governed_report_backed_count') or 0}",
		f"- Governed direct-query entries: {summary.get('governed_direct_query_count') or 0}",
		f"- Governed reports present in ERP: {summary.get('governed_present_count') or 0}",
		"",
		"## Governed Missing Reports",
		"",
	]
	missing_reports = [str(value or "").strip() for value in (summary.get("governed_missing_reports") or []) if str(value or "").strip()]
	if missing_reports:
		lines.extend(f"- {value}" for value in missing_reports)
	else:
		lines.append("- None")
	lines.extend(["", "## Governed Direct-query Entries", ""])
	direct_query_reports = [str(value or "").strip() for value in (summary.get("governed_direct_query_reports") or []) if str(value or "").strip()]
	if direct_query_reports:
		lines.extend(f"- {value}" for value in direct_query_reports)
	else:
		lines.append("- None")
	lines.extend(["", "## Report Type Breakdown", ""])
	for item in summary.get("report_type_breakdown") or []:
		if not isinstance(item, dict):
			continue
		lines.append(f"- {item.get('report_type')}: {item.get('count')}")
	lines.extend(
		[
			"",
			"## Surface Gaps",
			"",
			f"- Script reports without declared filters/columns: {summary.get('script_reports_without_declared_surface_count') or 0}",
			f"- Script reports without declared surface but with governed hints: {summary.get('script_reports_with_governed_hints_count') or 0}",
			f"- Report-surface evidence policy entries: {summary.get('report_surface_evidence_registry_count') or 0}",
			f"- Governed reports with explicit evidence policy: {summary.get('governed_reports_with_evidence_policy_count') or 0}",
		]
	)
	for item in summary.get("script_reports_without_declared_surface_sample") or []:
		if not isinstance(item, dict):
			continue
		lines.append(
			f"- {item.get('report_name')} | module={item.get('module') or ''} | ref_doctype={item.get('ref_doctype') or ''}"
		)
	lines.extend(["", "## Script Reports With Governed Hints", ""])
	for item in summary.get("script_reports_with_governed_hints_sample") or []:
		if not isinstance(item, dict):
			continue
		lines.append(
			f"- {item.get('report_name')} | family={item.get('family') or ''} | module={item.get('module') or ''} | ref_doctype={item.get('ref_doctype') or ''}"
		)
	lines.extend(["", "## Governed Reports With Evidence Policy", ""])
	for item in summary.get("governed_reports_with_evidence_policy_sample") or []:
		if not isinstance(item, dict):
			continue
		lines.append(
			f"- {item.get('report_name')} | evidence_class={item.get('evidence_class') or ''}"
		)
	lines.extend(["", "## Report-surface Evidence Registry", ""])
	for item in summary.get("report_surface_evidence_registry_sample") or []:
		if not isinstance(item, dict):
			continue
		lines.append(
			f"- {item.get('report_name')} | evidence_class={item.get('evidence_class') or ''}"
		)
	lines.extend(
		[
			"",
			"## Custom Referenced Doctypes",
			"",
			f"- Count: {summary.get('custom_referenced_doctype_count') or 0}",
		]
	)
	for value in summary.get("custom_referenced_doctype_sample") or []:
		if str(value or "").strip():
			lines.append(f"- {value}")
	return "\n".join(lines).strip() + "\n"


def _diff_discovered_erp_surface_snapshots(
	previous: Dict[str, Any],
	current: Dict[str, Any],
	*,
	previous_path: str = "",
	current_path: str = "",
) -> Dict[str, Any]:
	if not previous or not current:
		return {
			"ok": False,
			"reason": "One or both snapshot files could not be loaded.",
			"previous_path": previous_path,
			"current_path": current_path,
		}
	previous_reports = {
		_clean_text(item.get("report_name")): item
		for item in (previous.get("reports") or [])
		if isinstance(item, dict) and _clean_text(item.get("report_name"))
	}
	current_reports = {
		_clean_text(item.get("report_name")): item
		for item in (current.get("reports") or [])
		if isinstance(item, dict) and _clean_text(item.get("report_name"))
	}
	previous_doctypes = {
		_clean_text(item.get("doctype")): item
		for item in (previous.get("all_doctypes_summary") or [])
		if isinstance(item, dict) and _clean_text(item.get("doctype"))
	}
	current_doctypes = {
		_clean_text(item.get("doctype")): item
		for item in (current.get("all_doctypes_summary") or [])
		if isinstance(item, dict) and _clean_text(item.get("doctype"))
	}
	report_changes: List[Dict[str, Any]] = []
	for report_name in sorted(set(previous_reports).intersection(current_reports)):
		before = previous_reports[report_name]
		after = current_reports[report_name]
		change: Dict[str, Any] = {"report_name": report_name}
		for key in ("module", "ref_doctype", "report_type", "is_standard", "disabled"):
			if before.get(key) != after.get(key):
				change[key] = {"before": before.get(key), "after": after.get(key)}
		if change.keys() != {"report_name"}:
			report_changes.append(change)
	doctype_changes: List[Dict[str, Any]] = []
	for doctype_name in sorted(set(previous_doctypes).intersection(current_doctypes)):
		before = previous_doctypes[doctype_name]
		after = current_doctypes[doctype_name]
		change: Dict[str, Any] = {"doctype": doctype_name}
		for key in ("module", "istable", "custom"):
			if before.get(key) != after.get(key):
				change[key] = {"before": before.get(key), "after": after.get(key)}
		if change.keys() != {"doctype"}:
			doctype_changes.append(change)
	return {
		"ok": True,
		"previous_path": previous_path,
		"current_path": current_path,
		"source_signature_changed": previous.get("source_signature") != current.get("source_signature"),
		"added_reports": sorted(set(current_reports).difference(previous_reports)),
		"removed_reports": sorted(set(previous_reports).difference(current_reports)),
		"changed_reports": report_changes,
		"added_doctypes": sorted(set(current_doctypes).difference(previous_doctypes)),
		"removed_doctypes": sorted(set(previous_doctypes).difference(current_doctypes)),
		"changed_doctypes": doctype_changes,
	}


def diff_discovered_erp_surface_snapshots(previous_path: str, current_path: str) -> Dict[str, Any]:
	previous = _load_snapshot(Path(previous_path))
	current = _load_snapshot(Path(current_path))
	return _diff_discovered_erp_surface_snapshots(
		previous,
		current,
		previous_path=previous_path,
		current_path=current_path,
	)


def export_discovered_erp_surface_snapshot(output_dir: str = "") -> Dict[str, Any]:
	snapshot = build_discovered_erp_surface_snapshot()
	target_dir = Path(output_dir) if _clean_text(output_dir) else _default_snapshot_dir()
	target_dir.mkdir(parents=True, exist_ok=True)
	timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
	snapshot_path = target_dir / f"discovered_erp_surface_{timestamp}.json"
	latest_path = target_dir / "latest_discovered_erp_surface.json"
	with snapshot_path.open("w", encoding="utf-8") as handle:
		json.dump(snapshot, handle, ensure_ascii=False, indent=2, default=_jsonable_default)
	with latest_path.open("w", encoding="utf-8") as handle:
		json.dump(snapshot, handle, ensure_ascii=False, indent=2, default=_jsonable_default)
	return {
		"ok": True,
		"output_dir": str(target_dir),
		"snapshot_path": str(snapshot_path),
		"latest_path": str(latest_path),
		"report_count": int((snapshot.get("report_summary") or {}).get("report_count") or 0),
		"doctype_count": int((snapshot.get("doctype_summary") or {}).get("doctype_count") or 0),
		"referenced_doctype_count": int((snapshot.get("report_summary") or {}).get("referenced_doctype_count") or 0),
	}


def refresh_discovered_erp_surface_snapshot_if_changed(output_dir: str = "") -> Dict[str, Any]:
	target_dir = Path(output_dir) if _clean_text(output_dir) else _default_snapshot_dir()
	target_dir.mkdir(parents=True, exist_ok=True)
	latest_path = target_dir / "latest_discovered_erp_surface.json"
	current_signature = build_discovered_erp_source_signature()
	previous_snapshot = _load_snapshot(latest_path)
	previous_signature = previous_snapshot.get("source_signature") if isinstance(previous_snapshot, dict) else {}
	if previous_signature == current_signature:
		return {
			"ok": True,
			"changed": False,
			"output_dir": str(target_dir),
			"latest_path": str(latest_path),
			"source_signature": current_signature,
		}
	export_result = export_discovered_erp_surface_snapshot(output_dir=str(target_dir))
	diff_payload = {}
	if previous_snapshot:
		current_snapshot = _load_snapshot(Path(str(export_result.get("latest_path") or latest_path)))
		diff_payload = _diff_discovered_erp_surface_snapshots(
			previous_snapshot,
			current_snapshot,
			previous_path=str(latest_path),
			current_path=str(export_result.get("latest_path") or latest_path),
		)
	return {
		"ok": True,
		"changed": True,
		"output_dir": str(target_dir),
		"latest_path": str(export_result.get("latest_path") or latest_path),
		"source_signature": current_signature,
		"diff": diff_payload,
	}


def export_discovery_evaluation_summary(output_dir: str = "") -> Dict[str, Any]:
	target_dir = Path(output_dir) if _clean_text(output_dir) else _default_snapshot_dir()
	target_dir.mkdir(parents=True, exist_ok=True)
	latest_path = target_dir / "latest_discovered_erp_surface.json"
	snapshot = _load_snapshot(latest_path)
	if not snapshot:
		return {
			"ok": False,
			"reason": "No discovery snapshot is available to summarize.",
			"latest_path": str(latest_path),
		}
	summary = build_discovery_evaluation_summary(snapshot)
	summary_json_path = target_dir / "latest_discovery_evaluation_summary.json"
	summary_md_path = target_dir / "latest_discovery_evaluation_summary.md"
	with summary_json_path.open("w", encoding="utf-8") as handle:
		json.dump(summary, handle, ensure_ascii=False, indent=2, default=_jsonable_default)
	with summary_md_path.open("w", encoding="utf-8") as handle:
		handle.write(_summary_markdown(summary))
	return {
		"ok": True,
		"latest_path": str(latest_path),
		"summary_json_path": str(summary_json_path),
		"summary_md_path": str(summary_md_path),
		"report_count": int(summary.get("report_count") or 0),
		"governed_missing_reports": list(summary.get("governed_missing_reports") or []),
		"script_reports_without_declared_surface_count": int(summary.get("script_reports_without_declared_surface_count") or 0),
	}
