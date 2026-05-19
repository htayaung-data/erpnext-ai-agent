from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from . import common, service


PROFILE_DOCTYPE = "Procurement Item Buying Profile"
LOG_DOCTYPE = "Procurement Item Buying Log"

NOT_REVIEWED = "Not reviewed"
READY_FOR_BUYING = "Ready for buying"
NEEDS_SOURCING_REVIEW = "Needs sourcing review"
HOLD_FOR_SOURCING = "Hold for sourcing"

STATUS_OPTIONS = [NOT_REVIEWED, READY_FOR_BUYING, NEEDS_SOURCING_REVIEW, HOLD_FOR_SOURCING]
MANAGER_ROLES = {"Purchase Manager", "Purchase Master Manager"}
ALLOWED_PAYLOAD_KEYS = {
	"buying_readiness_status",
	"preferred_existing_supplier",
	"supplier_part_no_context",
	"procurement_lead_time_days",
	"minimum_order_qty_context",
	"buying_note",
	"readiness_note",
}
FORBIDDEN_PAYLOAD_KEYS = {
	"item_name",
	"item_group",
	"brand",
	"stock_uom",
	"purchase_uom",
	"disabled",
	"is_stock_item",
	"is_purchase_item",
	"is_sales_item",
	"valuation_rate",
	"valuation_method",
	"item_defaults",
	"default_supplier",
	"default_warehouse",
	"default_price_list",
	"expense_account",
	"income_account",
	"supplier_items",
	"item_supplier",
	"supplier_part_no",
	"price_list_rate",
	"item_price",
	"price_list",
	"currency",
	"reorder_levels",
	"warehouse",
	"safety_stock",
	"has_serial_no",
	"has_batch_no",
	"has_variants",
	"variant_of",
	"taxes",
	"contact",
	"user",
	"portal",
	"communication",
	"email_queue",
	"send_email",
	"submit",
	"approve",
	"receive",
	"bill",
	"payment",
}
PROFILE_FIELDS = [
	"name",
	"item_code",
	"buying_readiness_status",
	"preferred_existing_supplier",
	"supplier_part_no_context",
	"procurement_lead_time_days",
	"minimum_order_qty_context",
	"buying_note",
	"readiness_note",
	"last_context_update_by",
	"last_context_update_at",
	"modified",
	"modified_by",
	"owner",
]
TEXT_LIMITS = {
	"supplier_part_no_context": 140,
	"buying_note": 1000,
	"readiness_note": 1000,
}


def _state(kind: str, title: str, detail: str = "") -> dict[str, str]:
	return {"kind": kind, "title": title, "detail": detail}


def _ready(title: str = "Item buying context ready") -> dict[str, str]:
	return _state("ready", title)


def _error(title: str, detail: str) -> dict[str, str]:
	return _state("error", title, detail)


def _restricted(detail: str | None = None) -> dict[str, str]:
	return _state(
		"restricted",
		"Item buying context restricted",
		detail or "You do not have permission to use item buying context controls.",
	)


def _roles() -> set[str]:
	return service.current_user_roles()


def _can_edit(context: dict[str, object] | None = None) -> bool:
	roles = set((context or {}).get("roles") or []) if context and "roles" in context else _roles()
	return bool(roles.intersection(MANAGER_ROLES))


def _safe_get_all(
	doctype: str,
	fields: list[str],
	filters: dict[str, object] | list | None = None,
	order_by: str | None = None,
	limit: int = 20,
) -> list[dict[str, Any]]:
	query: dict[str, Any] = {"fields": fields, "filters": filters or {}, "limit_page_length": limit}
	if order_by:
		query["order_by"] = order_by
	try:
		return list(frappe.get_all(doctype, ignore_permissions=True, **query))
	except TypeError:
		try:
			return list(frappe.get_all(doctype, **query))
		except Exception:
			return []
	except Exception:
		return []


def _item_exists(item_code: str) -> bool:
	item_name = cstr(item_code).strip()
	if not item_name or not common.can_read("Item"):
		return False
	rows = common.get_list("Item", fields=["name"], filters=[["Item", "name", "=", item_name]], limit=1)
	return bool(rows)


def _supplier_row(supplier: str) -> dict[str, Any] | None:
	supplier_name = cstr(supplier).strip()
	if not supplier_name or not common.can_read("Supplier"):
		return None
	fields = ["name", "supplier_name"]
	if common.has_field("Supplier", "disabled"):
		fields.append("disabled")
	rows = common.get_list("Supplier", fields=fields, filters=[["Supplier", "name", "=", supplier_name]], limit=1)
	return dict(rows[0]) if rows else None


def _profile_row(item_code: str) -> dict[str, Any] | None:
	item_name = cstr(item_code).strip()
	if not item_name:
		return None
	rows = _safe_get_all(PROFILE_DOCTYPE, PROFILE_FIELDS, filters={"item_code": item_name}, limit=1)
	return dict(rows[0]) if rows else None


def _profile_doc(item_code: str):
	row = _profile_row(item_code)
	if row and cstr(row.get("name")).strip():
		try:
			return frappe.get_doc(PROFILE_DOCTYPE, cstr(row.get("name")).strip())
		except Exception:
			return None
	return None


def _new_profile_doc(item_code: str):
	new_doc = getattr(frappe, "new_doc", None)
	if callable(new_doc):
		doc = new_doc(PROFILE_DOCTYPE)
		setattr(doc, "item_code", item_code)
		return doc
	return frappe.get_doc({"doctype": PROFILE_DOCTYPE, "item_code": item_code})


def _doc_value(doc: object, fieldname: str, default: Any = "") -> Any:
	if isinstance(doc, dict):
		return doc.get(fieldname, default)
	return getattr(doc, fieldname, default)


def _set_doc_value(doc: object, fieldname: str, value: Any) -> None:
	if isinstance(doc, dict):
		doc[fieldname] = value
	else:
		setattr(doc, fieldname, value)


def _insert_doc(doc: object) -> object:
	try:
		return doc.insert(ignore_permissions=True)
	except TypeError:
		try:
			setattr(doc, "ignore_permissions", True)
		except Exception:
			pass
		return doc.insert()


def _save_doc(doc: object) -> object:
	try:
		return doc.save(ignore_permissions=True)
	except TypeError:
		try:
			setattr(doc, "ignore_permissions", True)
		except Exception:
			pass
		return doc.save()


def _status_tone(status: str) -> str:
	if status == READY_FOR_BUYING:
		return "good"
	if status == NEEDS_SOURCING_REVIEW:
		return "warning"
	if status == HOLD_FOR_SOURCING:
		return "danger"
	return "neutral"


def _clean_text(value: object, fieldname: str) -> str:
	text = cstr(value).strip()
	limit = TEXT_LIMITS.get(fieldname)
	if limit and len(text) > limit:
		raise ValueError(f"{fieldname.replace('_', ' ').title()} is too long.")
	return text


def _optional_int(value: object, fieldname: str, minimum: int, maximum: int) -> int | None:
	if value in (None, ""):
		return None
	try:
		parsed = int(value)
	except Exception:
		raise ValueError(f"{fieldname.replace('_', ' ').title()} must be a whole number.")
	if parsed < minimum or parsed > maximum:
		raise ValueError(f"{fieldname.replace('_', ' ').title()} must be between {minimum} and {maximum}.")
	return parsed


def _optional_float(value: object, fieldname: str, minimum: float, maximum: float) -> float | None:
	if value in (None, ""):
		return None
	parsed = flt(value)
	if parsed <= minimum or parsed > maximum:
		raise ValueError(f"{fieldname.replace('_', ' ').title()} must be greater than {minimum:g} and no more than {maximum:g}.")
	return parsed


def _profile_values(row: dict[str, Any] | None) -> dict[str, Any]:
	status = cstr((row or {}).get("buying_readiness_status")).strip() or NOT_REVIEWED
	return {
		"name": cstr((row or {}).get("name")).strip(),
		"item_code": cstr((row or {}).get("item_code")).strip(),
		"exists": bool(row),
		"buying_readiness_status": status,
		"preferred_existing_supplier": cstr((row or {}).get("preferred_existing_supplier")).strip(),
		"supplier_part_no_context": cstr((row or {}).get("supplier_part_no_context")).strip(),
		"procurement_lead_time_days": (row or {}).get("procurement_lead_time_days") if (row or {}).get("procurement_lead_time_days") not in (None, "") else "",
		"minimum_order_qty_context": (row or {}).get("minimum_order_qty_context") if (row or {}).get("minimum_order_qty_context") not in (None, "") else "",
		"buying_note": cstr((row or {}).get("buying_note")).strip(),
		"readiness_note": cstr((row or {}).get("readiness_note")).strip(),
		"last_context_update_by": cstr((row or {}).get("last_context_update_by") or (row or {}).get("modified_by") or (row or {}).get("owner")).strip(),
		"last_context_update_at": cstr((row or {}).get("last_context_update_at") or (row or {}).get("modified")).strip(),
		"modified": cstr((row or {}).get("modified")).strip(),
		"modified_by": cstr((row or {}).get("modified_by") or (row or {}).get("owner")).strip(),
	}


def _supplier_options_for_item(item_code: str, selected_supplier: str = "") -> list[dict[str, str]]:
	suppliers: list[str] = []
	for row in _safe_get_all("Item Supplier", ["supplier"], filters={"parent": item_code}, order_by="idx asc", limit=50):
		supplier = cstr(row.get("supplier")).strip()
		if supplier and supplier not in suppliers:
			suppliers.append(supplier)
	if selected_supplier and selected_supplier not in suppliers:
		suppliers.insert(0, selected_supplier)
	options: list[dict[str, str]] = []
	for supplier in suppliers[:50]:
		row = _supplier_row(supplier) or {"name": supplier}
		options.append({"supplier": supplier, "label": cstr(row.get("supplier_name") or row.get("name") or supplier).strip(), "disabled": "1" if row.get("disabled") else ""})
	return options


def _context_from_row(item_code: str, row: dict[str, Any] | None, context: dict[str, object] | None = None) -> dict[str, Any]:
	profile = _profile_values(row)
	profile["item_code"] = item_code
	status = cstr(profile.get("buying_readiness_status")).strip() or NOT_REVIEWED
	preferred = cstr(profile.get("preferred_existing_supplier")).strip()
	supplier_row = _supplier_row(preferred) if preferred else None
	profile["preferred_supplier_name"] = cstr((supplier_row or {}).get("supplier_name") or preferred).strip()
	profile["preferred_supplier_disabled"] = bool((supplier_row or {}).get("disabled")) if supplier_row else False
	profile["readiness_label"] = status
	profile["readiness_tone"] = _status_tone(status)
	profile["status_options"] = [{"label": status_value, "value": status_value} for status_value in STATUS_OPTIONS]
	profile["supplier_options"] = _supplier_options_for_item(item_code, preferred)
	profile["can_edit"] = _can_edit(context)
	profile["read_only_reason"] = "" if profile["can_edit"] else "Purchase Manager permission is required to edit item buying context."
	profile["state"] = _ready()
	return profile


def item_readiness_chip(item_code: str) -> dict[str, str]:
	profile = _context_from_row(cstr(item_code).strip(), _profile_row(cstr(item_code).strip()))
	return {"value": cstr(profile.get("readiness_label") or NOT_REVIEWED), "tone": cstr(profile.get("readiness_tone") or "neutral")}


def readiness_chips_for_items(item_codes: list[str]) -> dict[str, dict[str, str]]:
	names = [cstr(name).strip() for name in item_codes if cstr(name).strip()]
	if not names:
		return {}
	rows = _safe_get_all(PROFILE_DOCTYPE, PROFILE_FIELDS, filters={"item_code": ["in", names]}, limit=len(names))
	by_item = {cstr(row.get("item_code")).strip(): dict(row) for row in rows}
	return {name: item_readiness_chip_from_row(name, by_item.get(name)) for name in names}


def item_readiness_chip_from_row(item_code: str, row: dict[str, Any] | None) -> dict[str, str]:
	profile = _profile_values(row)
	status = cstr(profile.get("buying_readiness_status")).strip() or NOT_REVIEWED
	return {"value": status, "tone": _status_tone(status)}


def get_item_profile_context(item_code: str, context: dict[str, object] | None = None) -> dict[str, Any]:
	item_name = cstr(item_code).strip()
	if not item_name:
		return _context_from_row("", None, context)
	return _context_from_row(item_name, _profile_row(item_name), context)


@frappe.whitelist()
def get_item_buying_profile_context(item_code: str) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	item_name = cstr(item_code).strip()
	if not service.has_procurement_access(context):
		return {"state": _restricted()}
	if not item_name:
		return {"state": _error("Item required", "Open a buying item before reviewing buying context.")}
	if not _item_exists(item_name):
		return {"state": _error("Item not found", "The requested item is not visible for this user.")}
	return {"state": _ready(), "profile": _context_from_row(item_name, _profile_row(item_name), context)}


def _parse_payload(payload: str | dict[str, Any] | None) -> dict[str, Any]:
	if isinstance(payload, str):
		try:
			value = json.loads(payload)
		except Exception:
			raise ValueError("Item buying context payload must be valid JSON.")
		if not isinstance(value, dict):
			raise ValueError("Item buying context payload must be an object.")
		return value
	if isinstance(payload, dict):
		return dict(payload)
	return {}


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
	keys = set(payload)
	forbidden = sorted(keys.intersection(FORBIDDEN_PAYLOAD_KEYS))
	if forbidden:
		raise ValueError(f"Forbidden item buying context fields are not accepted: {', '.join(forbidden)}.")
	unknown = sorted(keys.difference(ALLOWED_PAYLOAD_KEYS))
	if unknown:
		raise ValueError(f"Unknown item buying context fields are not accepted: {', '.join(unknown)}.")
	status = cstr(payload.get("buying_readiness_status")).strip() or NOT_REVIEWED
	if status not in STATUS_OPTIONS:
		raise ValueError("Buying readiness status is not valid.")
	preferred_supplier = cstr(payload.get("preferred_existing_supplier")).strip()
	if preferred_supplier:
		row = _supplier_row(preferred_supplier)
		if not row:
			raise ValueError("Preferred supplier must be an existing Supplier visible to Procurement.")
		if row.get("disabled"):
			raise ValueError("Preferred supplier is disabled and cannot be used for buying context.")
	return {
		"buying_readiness_status": status,
		"preferred_existing_supplier": preferred_supplier,
		"supplier_part_no_context": _clean_text(payload.get("supplier_part_no_context"), "supplier_part_no_context"),
		"procurement_lead_time_days": _optional_int(payload.get("procurement_lead_time_days"), "procurement_lead_time_days", 0, 365),
		"minimum_order_qty_context": _optional_float(payload.get("minimum_order_qty_context"), "minimum_order_qty_context", 0, 1000000),
		"buying_note": _clean_text(payload.get("buying_note"), "buying_note"),
		"readiness_note": _clean_text(payload.get("readiness_note"), "readiness_note"),
	}


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
	return [field for field in ALLOWED_PAYLOAD_KEYS if cstr(before.get(field)).strip() != cstr(after.get(field)).strip()]


def _append_log(item_code: str, before: dict[str, Any], after: dict[str, Any], changed: list[str]) -> None:
	if not changed:
		return
	before_values = {field: before.get(field, "") for field in changed}
	after_values = {field: after.get(field, "") for field in changed}
	log_values = {
		"doctype": LOG_DOCTYPE,
		"item_code": item_code,
		"changed_by": cstr(getattr(frappe.session, "user", "")).strip(),
		"changed_at": str(now_datetime()),
		"change_summary": ", ".join(changed),
		"before_json": json.dumps(before_values, sort_keys=True),
		"after_json": json.dumps(after_values, sort_keys=True),
	}
	_insert_doc(frappe.get_doc(log_values))


@frappe.whitelist()
def save_item_buying_profile(item_code: str, payload: str | dict[str, Any] | None = None) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	item_name = cstr(item_code).strip()
	try:
		if not service.has_procurement_access(context):
			return {"state": _restricted()}
		if not _can_edit(context):
			return {"state": _restricted("Purchase Manager permission is required to save item buying context.")}
		if not item_name:
			return {"state": _error("Item required", "Open a buying item before saving buying context.")}
		if not _item_exists(item_name):
			return {"state": _error("Item not found", "The requested item is not visible for this user.")}
		normalized = _validate_payload(_parse_payload(payload))
		before_row = _profile_row(item_name)
		before = _profile_values(before_row)
		doc = _profile_doc(item_name) or _new_profile_doc(item_name)
		_set_doc_value(doc, "item_code", item_name)
		for field, value in normalized.items():
			_set_doc_value(doc, field, value)
		_set_doc_value(doc, "last_context_update_by", cstr(getattr(frappe.session, "user", "")).strip())
		_set_doc_value(doc, "last_context_update_at", now_datetime())
		if before_row:
			_save_doc(doc)
		else:
			_insert_doc(doc)
		after_row = _profile_row(item_name) or {**normalized, "item_code": item_name, "name": _doc_value(doc, "name", item_name)}
		after = _profile_values(after_row)
		changed = _changed_fields(before, after)
		_append_log(item_name, before, after, changed)
		return {"state": _ready("Item buying context saved"), "profile": _context_from_row(item_name, _profile_row(item_name), context)}
	except Exception as exc:
		return {"state": _error("Item buying context not saved", cstr(exc))}
