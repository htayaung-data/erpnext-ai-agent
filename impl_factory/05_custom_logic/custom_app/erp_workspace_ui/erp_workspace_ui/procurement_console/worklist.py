from __future__ import annotations

import json

import frappe

from . import service


def _normalize_queue_key(queue_key: str | None) -> str:
	return str(queue_key or "").strip().lower().replace("-", "_")


def _state_payload(queue_key: str, state: dict[str, str]) -> dict[str, object]:
	return {
		"page": {"title": "Procurement Console Worklist", "key": queue_key},
		"summary": {
			"kicker": "Procurement Console worklist",
			"title": state["title"],
			"subtitle": state["detail"],
			"facts": [],
		},
		"controls": {
			"actions": [{"key": "refresh", "label": "Refresh"}],
			"fields": [],
		},
		"results": {
			"title": "Queue state",
			"columns": [],
			"rows": [],
			"state": state,
		},
		"action_targets": {},
	}


def _coerce_filters(filters: str | dict[str, object] | None) -> dict[str, object]:
	if isinstance(filters, dict):
		return filters
	if isinstance(filters, str) and filters.strip():
		try:
			parsed = json.loads(filters)
		except Exception:
			return {}
		return parsed if isinstance(parsed, dict) else {}
	return {}


@frappe.whitelist()
def get_procurement_console_worklist_context(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	normalized_key = _normalize_queue_key(queue_key)
	_coerce_filters(filters)
	if not service.has_procurement_access(context):
		return _state_payload(normalized_key, service.restricted_state())
	return _state_payload(normalized_key, service.unavailable_state())
