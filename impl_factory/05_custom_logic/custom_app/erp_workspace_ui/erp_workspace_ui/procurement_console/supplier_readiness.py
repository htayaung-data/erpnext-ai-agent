from __future__ import annotations

import json
import re
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from . import common, readiness_evidence, service


PROFILE_DOCTYPE = "Procurement Supplier Readiness Profile"
LOG_DOCTYPE = "Procurement Supplier Readiness Log"

READY = "Ready"
NEEDS_EMAIL = "Needs email"
NEEDS_CONTACT_REVIEW = "Needs contact review"
HOLD_FOR_SOURCING = "Hold for sourcing"
NO_PROFILE = "No profile"

STATUS_OPTIONS = [READY, NEEDS_EMAIL, NEEDS_CONTACT_REVIEW, HOLD_FOR_SOURCING]
NON_READY_STATUSES = {NEEDS_EMAIL, NEEDS_CONTACT_REVIEW, HOLD_FOR_SOURCING}
MANAGER_ROLES = {"Purchase Manager", "Purchase Master Manager"}
ALLOWED_PAYLOAD_KEYS = {
	"buying_readiness_status",
	"preferred_rfq_contact",
	"rfq_recipient_email_override",
	"buying_note",
	"readiness_note",
}
FORBIDDEN_PAYLOAD_KEYS = {
	"disabled",
	"supplier_group",
	"supplier_type",
	"tax_id",
	"tax_category",
	"tax_withholding_category",
	"default_bank_account",
	"default_currency",
	"default_price_list",
	"payment_terms",
	"supplier_primary_contact",
	"email_id",
	"contact_email",
	"send_email",
	"email_sent",
	"communication",
	"email_queue",
	"item_price",
	"default_supplier",
	"submit",
	"approve",
	"receive",
	"bill",
	"payment",
}

PROFILE_FIELDS = [
	"name",
	"supplier",
	"buying_readiness_status",
	"preferred_rfq_contact",
	"rfq_recipient_email_override",
	"buying_note",
	"readiness_note",
	"modified",
	"modified_by",
	"owner",
]


def _state(kind: str, title: str, detail: str = "") -> dict[str, str]:
	return {"kind": kind, "title": title, "detail": detail}


def _ready(title: str = "Ready") -> dict[str, str]:
	return _state("ready", title)


def _error(title: str, detail: str) -> dict[str, str]:
	return _state("error", title, detail)


def _restricted(detail: str | None = None) -> dict[str, str]:
	return _state(
		"restricted",
		"Supplier readiness restricted",
		detail or "You do not have permission to use supplier readiness controls.",
	)


def _roles() -> set[str]:
	return service.current_user_roles()


def _can_edit(context: dict[str, object] | None = None) -> bool:
	roles = set((context or {}).get("roles") or []) if context and "roles" in context else _roles()
	return bool(roles.intersection(MANAGER_ROLES))


def _supplier_exists(supplier: str) -> bool:
	if not supplier or not common.can_read("Supplier"):
		return False
	rows = common.get_list("Supplier", fields=["name"], filters=[["Supplier", "name", "=", supplier]], limit=1)
	return bool(rows)


def _safe_get_all(
	doctype: str,
	fields: list[str],
	filters: dict[str, object] | list | None = None,
	order_by: str | None = None,
	limit: int = 20,
) -> list[dict[str, Any]]:
	query: dict[str, Any] = {
		"fields": fields,
		"filters": filters or {},
		"limit_page_length": limit,
	}
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


def _profile_row(supplier: str) -> dict[str, Any] | None:
	supplier_name = cstr(supplier).strip()
	if not supplier_name:
		return None
	rows = _safe_get_all(PROFILE_DOCTYPE, PROFILE_FIELDS, filters={"supplier": supplier_name}, limit=1)
	return dict(rows[0]) if rows else None


def _profile_doc(supplier: str):
	row = _profile_row(supplier)
	if row and cstr(row.get("name")).strip():
		try:
			return frappe.get_doc(PROFILE_DOCTYPE, cstr(row.get("name")).strip())
		except Exception:
			return None
	return None


def _new_profile_doc(supplier: str):
	values = {"doctype": PROFILE_DOCTYPE, "supplier": supplier}
	new_doc = getattr(frappe, "new_doc", None)
	if callable(new_doc):
		doc = new_doc(PROFILE_DOCTYPE)
		setattr(doc, "supplier", supplier)
		return doc
	return frappe.get_doc(values)


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


def _linked_contact_names(supplier: str) -> list[str]:
	rows = _safe_get_all(
		"Dynamic Link",
		fields=["parent"],
		filters={"link_doctype": "Supplier", "link_name": supplier, "parenttype": "Contact"},
		order_by="idx asc",
		limit=50,
	)
	return [cstr(row.get("parent")).strip() for row in rows if cstr(row.get("parent")).strip()]


def _contact_name(row: dict[str, Any]) -> str:
	first = cstr(row.get("first_name")).strip()
	last = cstr(row.get("last_name")).strip()
	return " ".join(part for part in (first, last) if part).strip() or cstr(row.get("name")).strip()


def _contact_info(contact: str) -> dict[str, str]:
	contact_name = cstr(contact).strip()
	if not contact_name:
		return {"contact": "", "contact_name": "", "email": "", "phone": ""}
	row = {}
	try:
		value = frappe.db.get_value("Contact", contact_name, ["name", "first_name", "last_name", "email_id", "phone", "mobile_no"], as_dict=True)
		row = dict(value or {}) if isinstance(value, dict) else {}
	except Exception:
		row = {}
	email = cstr(row.get("email_id")).strip()
	if not email:
		email_rows = common.get_list(
			"Contact Email",
			fields=["email_id", "is_primary"],
			filters=[["Contact Email", "parent", "=", contact_name]],
			order_by="is_primary desc, idx asc",
			limit=5,
		)
		for email_row in email_rows:
			email = cstr(email_row.get("email_id")).strip()
			if email:
				break
	return {
		"contact": cstr(row.get("name") or contact_name).strip(),
		"contact_name": _contact_name({**row, "name": contact_name}),
		"email": email,
		"phone": cstr(row.get("mobile_no") or row.get("phone")).strip(),
	}


def contact_options_for_supplier(supplier: str) -> list[dict[str, str]]:
	options: list[dict[str, str]] = []
	for contact in _linked_contact_names(supplier):
		info = _contact_info(contact)
		if info.get("contact"):
			options.append(info)
	return options


def _is_valid_email(value: str) -> bool:
	email = cstr(value).strip()
	if not email:
		return True
	return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def display_readiness_label(status: str) -> str:
	value = cstr(status).strip()
	if value == READY:
		return readiness_evidence.REVIEWED_FOR_BUYING_LABEL
	if value in {NEEDS_EMAIL, NEEDS_CONTACT_REVIEW}:
		return readiness_evidence.NEEDS_SUPPLIER_REVIEW_LABEL
	return value or NO_PROFILE


def _status_tone(status: str) -> str:
	if status == READY:
		return "good"
	if status == HOLD_FOR_SOURCING:
		return "danger"
	if status in {NEEDS_EMAIL, NEEDS_CONTACT_REVIEW}:
		return "warning"
	return "neutral"


def _profile_values(row: dict[str, Any] | None) -> dict[str, Any]:
	return {
		"name": cstr((row or {}).get("name")).strip(),
		"supplier": cstr((row or {}).get("supplier")).strip(),
		"exists": bool(row),
		"buying_readiness_status": cstr((row or {}).get("buying_readiness_status")).strip() or NO_PROFILE,
		"preferred_rfq_contact": cstr((row or {}).get("preferred_rfq_contact")).strip(),
		"rfq_recipient_email_override": cstr((row or {}).get("rfq_recipient_email_override")).strip(),
		"buying_note": cstr((row or {}).get("buying_note")).strip(),
		"readiness_note": cstr((row or {}).get("readiness_note")).strip(),
		"modified": cstr((row or {}).get("modified")).strip(),
		"modified_by": cstr((row or {}).get("modified_by") or (row or {}).get("owner")).strip(),
	}


def _derive_recipient(profile: dict[str, Any]) -> dict[str, str]:
	override = cstr(profile.get("rfq_recipient_email_override")).strip()
	preferred_contact = cstr(profile.get("preferred_rfq_contact")).strip()
	if override:
		return {
			"email": override,
			"contact": preferred_contact,
			"contact_name": cstr(profile.get("preferred_contact_name")).strip(),
			"source": "readiness_override",
			"source_label": "Readiness email override",
		}
	if preferred_contact:
		info = _contact_info(preferred_contact)
		if info.get("email"):
			return {
				"email": info.get("email") or "",
				"contact": info.get("contact") or preferred_contact,
				"contact_name": info.get("contact_name") or preferred_contact,
				"source": "preferred_contact",
				"source_label": "Preferred RFQ contact",
			}
	return {"email": "", "contact": preferred_contact, "contact_name": "", "source": "", "source_label": ""}


def _context_from_row(supplier: str, row: dict[str, Any] | None, context: dict[str, object] | None = None) -> dict[str, Any]:
	profile = _profile_values(row)
	profile["supplier"] = supplier
	preferred = cstr(profile.get("preferred_rfq_contact")).strip()
	if preferred:
		info = _contact_info(preferred)
		profile["preferred_contact_name"] = info.get("contact_name") or preferred
		profile["preferred_contact_email"] = info.get("email") or ""
		profile["preferred_contact_phone"] = info.get("phone") or ""
	else:
		profile["preferred_contact_name"] = ""
		profile["preferred_contact_email"] = ""
		profile["preferred_contact_phone"] = ""
	recipient = _derive_recipient(profile)
	status = cstr(profile.get("buying_readiness_status")).strip() or NO_PROFILE
	evidence = readiness_evidence.supplier_evidence(supplier) if not profile.get("exists") else {}
	profile["evidence"] = evidence
	if not profile.get("exists") and evidence:
		profile["readiness_label"] = cstr(evidence.get("inferred_label")).strip() or readiness_evidence.SUPPLIER_NEW_REVIEW_LABEL
		profile["readiness_tone"] = cstr(evidence.get("inferred_tone")).strip() or "warning"
	else:
		profile["readiness_label"] = display_readiness_label(status)
		profile["readiness_tone"] = _status_tone(status)
	profile["recipient"] = recipient
	profile["contact_options"] = contact_options_for_supplier(supplier)
	profile["can_edit"] = _can_edit(context)
	profile["read_only_reason"] = "" if profile["can_edit"] else "Purchase Manager permission is required to edit readiness."
	profile["status_options"] = [{"label": status_value, "value": status_value} for status_value in STATUS_OPTIONS]
	profile["state"] = _ready("Supplier readiness ready")
	return profile


def get_supplier_profile_for_readiness(supplier: str) -> dict[str, Any]:
	supplier_name = cstr(supplier).strip()
	if not supplier_name:
		return _context_from_row("", None)
	return _context_from_row(supplier_name, _profile_row(supplier_name))


def get_supplier_profile_context(supplier: str, context: dict[str, object] | None = None) -> dict[str, Any]:
	supplier_name = cstr(supplier).strip()
	if not supplier_name:
		return _context_from_row("", None, context)
	return _context_from_row(supplier_name, _profile_row(supplier_name), context)


def supplier_readiness_chip(supplier: str) -> dict[str, str]:
	profile = get_supplier_profile_for_readiness(supplier)
	return {"value": cstr(profile.get("readiness_label") or NO_PROFILE), "tone": cstr(profile.get("readiness_tone") or "neutral")}


def supplier_readiness_chips_for_suppliers(suppliers: list[str]) -> dict[str, dict[str, str]]:
	names = [cstr(name).strip() for name in suppliers if cstr(name).strip()]
	if not names:
		return {}
	rows = _safe_get_all(PROFILE_DOCTYPE, PROFILE_FIELDS, filters={"supplier": ["in", names]}, limit=len(names))
	profiles = {cstr(row.get("supplier")).strip(): dict(row) for row in rows}
	evidence = readiness_evidence.supplier_evidence_for_suppliers([name for name in names if name not in profiles])
	chips: dict[str, dict[str, str]] = {}
	for name in names:
		row = profiles.get(name)
		if row:
			status = cstr(row.get("buying_readiness_status")).strip() or NO_PROFILE
			chips[name] = {"value": display_readiness_label(status), "tone": _status_tone(status)}
		else:
			entry = evidence.get(name) or {}
			chips[name] = {"value": cstr(entry.get("inferred_label") or readiness_evidence.SUPPLIER_NEW_REVIEW_LABEL), "tone": cstr(entry.get("inferred_tone") or "warning")}
	return chips


@frappe.whitelist()
def get_supplier_readiness_profile(supplier: str) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	supplier_name = cstr(supplier).strip()
	if not service.has_procurement_access(context):
		return {"state": _restricted()}
	if not supplier_name:
		return {"state": _error("Supplier required", "Open a supplier before reviewing readiness.")}
	if not _supplier_exists(supplier_name):
		return {"state": _error("Supplier not found", "The requested supplier is not visible for this user.")}
	return {"state": _ready("Supplier readiness ready"), "profile": _context_from_row(supplier_name, _profile_row(supplier_name), context)}


def _parse_payload(payload: str | dict[str, Any] | None) -> dict[str, Any]:
	if isinstance(payload, str):
		try:
			value = json.loads(payload)
		except Exception:
			raise ValueError("Readiness payload must be valid JSON.")
		if not isinstance(value, dict):
			raise ValueError("Readiness payload must be an object.")
		return value
	if isinstance(payload, dict):
		return dict(payload)
	return {}


def _validate_payload(supplier: str, payload: dict[str, Any]) -> dict[str, str]:
	keys = set(payload)
	forbidden = sorted(keys.intersection(FORBIDDEN_PAYLOAD_KEYS))
	if forbidden:
		raise ValueError("This form can only update approved fields. Remove unsupported fields and try again.")
	unknown = sorted(keys.difference(ALLOWED_PAYLOAD_KEYS))
	if unknown:
		raise ValueError(f"Unknown readiness fields are not accepted: {', '.join(unknown)}.")

	status = cstr(payload.get("buying_readiness_status")).strip() or READY
	if status not in STATUS_OPTIONS:
		raise ValueError("Buying readiness status is not valid.")
	contact = cstr(payload.get("preferred_rfq_contact")).strip()
	if contact and contact not in set(_linked_contact_names(supplier)):
		raise ValueError("Preferred RFQ contact must be linked to this supplier.")
	email_override = cstr(payload.get("rfq_recipient_email_override")).strip()
	if email_override and not _is_valid_email(email_override):
		raise ValueError("RFQ recipient email override must be a valid email address.")
	readiness_note = cstr(payload.get("readiness_note")).strip()
	if status in NON_READY_STATUSES and not readiness_note:
		raise ValueError("Readiness note is required for non-ready supplier readiness.")
	return {
		"buying_readiness_status": status,
		"preferred_rfq_contact": contact,
		"rfq_recipient_email_override": email_override,
		"buying_note": cstr(payload.get("buying_note")).strip(),
		"readiness_note": readiness_note,
	}


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
	return [field for field in ALLOWED_PAYLOAD_KEYS if cstr(before.get(field)).strip() != cstr(after.get(field)).strip()]


def _append_log(supplier: str, before: dict[str, Any], after: dict[str, Any], changed: list[str]) -> None:
	if not changed:
		return
	log_values = {
		"doctype": LOG_DOCTYPE,
		"supplier": supplier,
		"profile": after.get("name") or supplier,
		"changed_by": cstr(getattr(frappe.session, "user", "")).strip(),
		"changed_at": str(now_datetime()),
		"changed_fields": ", ".join(changed),
		"before_values": json.dumps({field: before.get(field, "") for field in changed}, sort_keys=True),
		"after_values": json.dumps({field: after.get(field, "") for field in changed}, sort_keys=True),
		"readiness_note": after.get("readiness_note") or "",
	}
	doc = frappe.get_doc(log_values)
	_insert_doc(doc)


@frappe.whitelist()
def save_supplier_readiness_profile(supplier: str, payload: str | dict[str, Any] | None = None) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	supplier_name = cstr(supplier).strip()
	try:
		if not service.has_procurement_access(context):
			return {"state": _restricted()}
		if not _can_edit(context):
			return {"state": _restricted("Purchase Manager permission is required to save supplier readiness.")}
		if not supplier_name:
			return {"state": _error("Supplier required", "Open a supplier before saving readiness.")}
		if not _supplier_exists(supplier_name):
			return {"state": _error("Supplier not found", "The requested supplier is not visible for this user.")}
		normalized = _validate_payload(supplier_name, _parse_payload(payload))
		before_row = _profile_row(supplier_name)
		before = _profile_values(before_row)
		doc = _profile_doc(supplier_name) or _new_profile_doc(supplier_name)
		_set_doc_value(doc, "supplier", supplier_name)
		for field, value in normalized.items():
			_set_doc_value(doc, field, value)
		if before_row:
			_save_doc(doc)
		else:
			_insert_doc(doc)
		after_row = _profile_row(supplier_name) or {**normalized, "supplier": supplier_name, "name": _doc_value(doc, "name", supplier_name)}
		after = _profile_values(after_row)
		changed = _changed_fields(before, after)
		_append_log(supplier_name, before, after, changed)
		return {"state": _ready("Supplier readiness saved"), "profile": _context_from_row(supplier_name, _profile_row(supplier_name), context)}
	except Exception as exc:
		return {"state": _error("Supplier readiness not saved", cstr(exc))}
