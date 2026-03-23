from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

import frappe

LEGACY_CHAT_SESSION_DOCTYPE = "AI Chat Session"
LEGACY_CHAT_MESSAGE_DOCTYPE = "AI Chat Message"
LEGACY_CHAT_PAGE = "ai-chat"

_LEGACY_DOCTYPES = (
	LEGACY_CHAT_SESSION_DOCTYPE,
	LEGACY_CHAT_MESSAGE_DOCTYPE,
)

_DOCTYPE_METADATA_TABLES = (
	"tabDocField",
	"tabDocPerm",
	"tabDocType Action",
	"tabDocType Link",
	"tabDocType State",
	"tabCustom Field",
	"tabCustom DocPerm",
	"tabProperty Setter",
	"tabNotification Settings",
)

_PAGE_METADATA_TABLES = (
	"tabHas Role",
)


def _scalar(sql: str, values: Iterable[Any] | None = None) -> Any:
	rows = frappe.db.sql(sql, tuple(values or ()))
	if not rows:
		return 0
	return rows[0][0]


def _table_exists(table_name: str) -> bool:
	return bool(frappe.db.sql("show tables like %s", (table_name,)))


def _table_columns(table_name: str) -> List[str]:
	if not _table_exists(table_name):
		return []
	return [row[0] for row in frappe.db.sql(f"show columns from `{table_name}`")]


def _count_where(table_name: str, where_sql: str = "", values: Iterable[Any] | None = None) -> int:
	if not _table_exists(table_name):
		return 0
	sql = f"select count(*) from `{table_name}`"
	if where_sql:
		sql = f"{sql} where {where_sql}"
	return int(_scalar(sql, values))


def _doctype_metadata_filter(table_name: str) -> tuple[str, tuple[Any, ...]] | None:
	columns = set(_table_columns(table_name))
	if "parent" in columns:
		return "parent in (%s, %s)", _LEGACY_DOCTYPES
	if "dt" in columns:
		return "dt in (%s, %s)", _LEGACY_DOCTYPES
	if "doc_type" in columns:
		return "doc_type in (%s, %s)", _LEGACY_DOCTYPES
	if "document_type" in columns:
		return "document_type in (%s, %s)", _LEGACY_DOCTYPES
	return None


def _page_metadata_filter(table_name: str) -> tuple[str, tuple[Any, ...]] | None:
	columns = set(_table_columns(table_name))
	if {"parent", "parenttype"}.issubset(columns):
		return "parent=%s and parenttype=%s", (LEGACY_CHAT_PAGE, "Page")
	if "page" in columns:
		return "page=%s", (LEGACY_CHAT_PAGE,)
	return None


def inventory_legacy_ai_chat_artifacts() -> Dict[str, Any]:
	legacy_tables = {
		LEGACY_CHAT_SESSION_DOCTYPE: f"tab{LEGACY_CHAT_SESSION_DOCTYPE}",
		LEGACY_CHAT_MESSAGE_DOCTYPE: f"tab{LEGACY_CHAT_MESSAGE_DOCTYPE}",
	}
	result: Dict[str, Any] = {
		"legacy_tables": {},
		"attachments": {
			"rows": _count_where("tabFile", "attached_to_doctype=%s", (LEGACY_CHAT_SESSION_DOCTYPE,)),
		},
		"doctypes": {},
		"doctype_metadata": {},
		"page": {
			"rows": _count_where("tabPage", "name=%s", (LEGACY_CHAT_PAGE,)),
		},
		"page_metadata": {},
	}

	for doctype_name, table_name in legacy_tables.items():
		table_exists = _table_exists(table_name)
		row_count = _count_where(table_name) if table_exists else 0
		result["legacy_tables"][doctype_name] = {
			"table_name": table_name,
			"table_exists": table_exists,
			"rows": row_count,
		}
		result["doctypes"][doctype_name] = {
			"definition_rows": _count_where("tabDocType", "name=%s", (doctype_name,)),
		}

	for table_name in _DOCTYPE_METADATA_TABLES:
		metadata_filter = _doctype_metadata_filter(table_name)
		if not metadata_filter:
			continue
		where_sql, values = metadata_filter
		count = _count_where(table_name, where_sql, values)
		if count:
			result["doctype_metadata"][table_name] = count

	for table_name in _PAGE_METADATA_TABLES:
		metadata_filter = _page_metadata_filter(table_name)
		if not metadata_filter:
			continue
		where_sql, values = metadata_filter
		count = _count_where(table_name, where_sql, values)
		if count:
			result["page_metadata"][table_name] = count

	return result


def cleanup_legacy_ai_chat_artifacts(dry_run: int = 1) -> Dict[str, Any]:
	dry_run_flag = bool(int(dry_run))
	before = inventory_legacy_ai_chat_artifacts()
	actions: List[Dict[str, Any]] = []

	def record(action: str, count: int = 0, *, kind: str = "sql") -> None:
		actions.append({"action": action, "count": int(count), "kind": kind})

	if dry_run_flag:
		return {
			"dry_run": True,
			"before": before,
			"actions": actions,
		}

	file_names = []
	if _table_exists("tabFile"):
		file_names = [
			row["name"]
			for row in frappe.db.sql(
				"select name from `tabFile` where attached_to_doctype=%s",
				(LEGACY_CHAT_SESSION_DOCTYPE,),
				as_dict=True,
			)
		]
	for file_name in file_names:
		frappe.delete_doc("File", file_name, ignore_permissions=True, force=True)
	record("delete_legacy_file_rows", len(file_names), kind="doctype")

	for doctype_name in (LEGACY_CHAT_MESSAGE_DOCTYPE, LEGACY_CHAT_SESSION_DOCTYPE):
		table_name = f"tab{doctype_name}"
		row_count = _count_where(table_name)
		if row_count:
			frappe.db.sql(f"delete from `{table_name}`")
		record(f"delete_rows:{table_name}", row_count)

	for table_name in _PAGE_METADATA_TABLES:
		metadata_filter = _page_metadata_filter(table_name)
		if not metadata_filter:
			continue
		where_sql, values = metadata_filter
		row_count = _count_where(table_name, where_sql, values)
		if row_count:
			frappe.db.sql(f"delete from `{table_name}` where {where_sql}", values)
		record(f"delete_page_metadata:{table_name}", row_count)

	page_rows = _count_where("tabPage", "name=%s", (LEGACY_CHAT_PAGE,))
	if page_rows:
		frappe.db.sql("delete from `tabPage` where name=%s", (LEGACY_CHAT_PAGE,))
	record("delete_page:tabPage", page_rows)

	for table_name in _DOCTYPE_METADATA_TABLES:
		metadata_filter = _doctype_metadata_filter(table_name)
		if not metadata_filter:
			continue
		where_sql, values = metadata_filter
		row_count = _count_where(table_name, where_sql, values)
		if row_count:
			frappe.db.sql(f"delete from `{table_name}` where {where_sql}", values)
		record(f"delete_doctype_metadata:{table_name}", row_count)

	doctype_rows = _count_where("tabDocType", "name in (%s, %s)", _LEGACY_DOCTYPES)
	if doctype_rows:
		frappe.db.sql(
			"delete from `tabDocType` where name in (%s, %s)",
			_LEGACY_DOCTYPES,
		)
	record("delete_doctype_rows:tabDocType", doctype_rows)

	for doctype_name in (LEGACY_CHAT_MESSAGE_DOCTYPE, LEGACY_CHAT_SESSION_DOCTYPE):
		table_name = f"tab{doctype_name}"
		table_exists = _table_exists(table_name)
		if table_exists:
			frappe.db.sql_ddl(f"drop table `{table_name}`")
		record(f"drop_table:{table_name}", 1 if table_exists else 0)

	frappe.db.commit()
	frappe.clear_cache()

	after = inventory_legacy_ai_chat_artifacts()
	return {
		"dry_run": False,
		"before": before,
		"actions": actions,
		"after": after,
	}


def print_legacy_ai_chat_inventory() -> None:
	print(json.dumps(inventory_legacy_ai_chat_artifacts(), indent=2, sort_keys=True))


def run_legacy_ai_chat_cleanup(dry_run: int = 1) -> None:
	print(json.dumps(cleanup_legacy_ai_chat_artifacts(dry_run=dry_run), indent=2, sort_keys=True))
