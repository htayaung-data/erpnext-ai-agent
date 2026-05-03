from __future__ import annotations

import json

import frappe

from . import service


def _normalize_report_key(report_key: str | None) -> str:
	return str(report_key or "").strip().lower().replace("-", "_")


def _state_payload(report_key: str, state: dict[str, str]) -> dict[str, object]:
	return {
		"page": {"title": "Procurement Console Report", "key": report_key},
		"summary": {
			"kicker": "Procurement Console report",
			"title": state["title"],
			"subtitle": state["detail"],
		},
		"controls": {
			"actions": [
				{"key": "refresh", "label": "Refresh"},
				{"key": "back_to_console", "label": "Back to Procurement Console"},
			],
			"fields": [],
		},
		"metrics": [],
		"results": {
			"title": "Report state",
			"columns": [],
			"rows": [],
			"state": state,
		},
		"action_targets": {},
	}


def _coerce_filter_overrides(filter_overrides: str | dict[str, object] | None) -> dict[str, object]:
	if isinstance(filter_overrides, dict):
		return filter_overrides
	if isinstance(filter_overrides, str) and filter_overrides.strip():
		try:
			parsed = json.loads(filter_overrides)
		except Exception:
			return {}
		return parsed if isinstance(parsed, dict) else {}
	return {}


@frappe.whitelist()
def get_procurement_console_report_context(
	report_key: str | None = None,
	filter_overrides: str | dict[str, object] | None = None,
) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	normalized_key = _normalize_report_key(report_key)
	_coerce_filter_overrides(filter_overrides)
	if not service.has_procurement_access(context):
		return _state_payload(normalized_key, service.restricted_state())
	return _state_payload(normalized_key, service.unavailable_state())
