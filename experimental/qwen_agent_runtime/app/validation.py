from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from app.report_registry import (
	get_validation_profile,
	is_report_approved,
	report_validation_profile,
	validate_report_filters,
)
from app.schemas import ToolTraceItem


def _parse_detail_obj(item: ToolTraceItem) -> Dict[str, Any]:
	obj = item.detail_obj
	if isinstance(obj, dict):
		return obj
	text = str(item.detail or "").strip()
	if not text:
		return {}
	try:
		parsed = json.loads(text)
	except Exception:
		return {}
	return parsed if isinstance(parsed, dict) else {}


def summarize_read_validation(tool_trace: List[ToolTraceItem], answer_text: str) -> Tuple[bool, Dict[str, Any]]:
	errors: List[str] = []
	grounding_tools: List[str] = []
	approved_reports: List[str] = []
	allowed_grounding_tools: set[str] = set()

	for item in tool_trace:
		tool_name = str(item.tool or "").strip()

		if tool_name not in {"erp_fac-report_requirements", "erp_fac-generate_report"}:
			detail_obj = _parse_detail_obj(item)
			report_name = str(detail_obj.get("report_name") or "").strip()
			if report_name:
				profile = get_validation_profile(report_validation_profile(report_name))
				allowed_grounding_tools.update(profile.get("allowed_grounding_tools") or [])
			if tool_name in allowed_grounding_tools and str(item.status or "").strip().lower() == "ok":
				grounding_tools.append(tool_name)
			continue

		detail_obj = _parse_detail_obj(item)
		report_name = str(detail_obj.get("report_name") or "").strip()
		if not report_name:
			errors.append(f"Missing report_name in tool trace for {tool_name}.")
			continue
		if not is_report_approved(report_name):
			errors.append(f"Unapproved report used: {report_name}")
			continue
		approved_reports.append(report_name)
		profile = get_validation_profile(report_validation_profile(report_name))
		allowed_grounding_tools.update(profile.get("allowed_grounding_tools") or [])
		if tool_name == "erp_fac-generate_report":
			filter_errors = validate_report_filters(report_name, detail_obj.get("filters"))
			errors.extend(filter_errors)
		if tool_name in allowed_grounding_tools and str(item.status or "").strip().lower() == "ok":
			grounding_tools.append(tool_name)

	if str(answer_text or "").strip() and not grounding_tools:
		errors.append("A grounded read answer requires at least one successful grounding tool call.")

	return (
		not errors,
		{
			"status": "pass" if not errors else "fail",
			"errors": errors,
			"grounding_tools": grounding_tools,
			"approved_reports": sorted({x for x in approved_reports if x}),
		},
	)
