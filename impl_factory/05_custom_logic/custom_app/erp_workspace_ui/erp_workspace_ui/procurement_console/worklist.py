from __future__ import annotations

import frappe

from . import common, items, purchase_order_follow_up, purchase_orders, requests, service, sourcing, suppliers


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


@frappe.whitelist()
def get_procurement_console_worklist_context(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	normalized_key = _normalize_queue_key(queue_key)
	applied_filters = common.normalize_filters(filters)
	if not service.has_procurement_access(context):
		return _state_payload(normalized_key, service.restricted_state())
	builder = _queue_registry().get(normalized_key)
	if not builder:
		return _state_payload(normalized_key, service.unavailable_state())
	return builder(applied_filters)


def _queue_registry():
	return {
		"supplier_directory": suppliers.build_supplier_directory,
		"buying_item_directory": items.build_buying_item_directory,
		"purchase_request_directory": requests.build_purchase_request_directory,
		"requests_to_source": requests.build_requests_to_source,
		"purchase_order_directory": purchase_orders.build_purchase_order_directory,
		"purchase_orders_pending_approval": purchase_orders.build_purchase_orders_pending_approval,
		"purchase_orders_open": purchase_orders.build_purchase_orders_open,
		"purchase_orders_late_or_unreceived": purchase_order_follow_up.build_purchase_orders_late_or_unreceived,
		"purchase_orders_due_soon": purchase_order_follow_up.build_purchase_orders_due_soon,
		"purchase_orders_overdue": purchase_order_follow_up.build_purchase_orders_overdue,
		"purchase_orders_partially_received": purchase_order_follow_up.build_purchase_orders_partially_received,
		"purchase_orders_not_billed_visibility": purchase_order_follow_up.build_purchase_orders_not_billed_visibility,
		"purchase_orders_supplier_follow_up": purchase_order_follow_up.build_purchase_orders_supplier_follow_up,
		"rfq_directory": sourcing.build_rfq_directory,
		"rfqs_awaiting_supplier_response": sourcing.build_rfqs_awaiting_supplier_response,
		"rfqs_partially_quoted": sourcing.build_rfqs_partially_quoted,
		"supplier_quotation_directory": sourcing.build_supplier_quotation_directory,
		"supplier_quotations_to_compare": sourcing.build_supplier_quotations_to_compare,
		"supplier_quotations_expiring": sourcing.build_supplier_quotations_expiring,
	}
