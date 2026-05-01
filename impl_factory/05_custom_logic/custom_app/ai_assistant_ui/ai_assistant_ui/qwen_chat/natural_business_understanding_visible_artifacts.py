from __future__ import annotations

import json
import re
from typing import Any, Dict, List


VISIBLE_ARTIFACT_VERSION = "1.0"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_key(value: Any) -> str:
	text = _clean_text(value).lower()
	text = re.sub(r"\([^)]*\)", "", text)
	text = re.sub(r"[^a-z0-9]+", "_", text)
	text = re.sub(r"_+", "_", text).strip("_")
	if text == "customer":
		return "customer"
	if text == "supplier":
		return "supplier"
	if text in {"product", "item"}:
		return "item"
	if "overdue" in text:
		return "overdue_amount"
	if "outstanding" in text:
		return "outstanding_amount"
	if text in {"total_due", "due"} or "total_due" in text:
		return "total_due"
	if "credit_utilization" in text or "credit_used" in text:
		return "credit_utilization"
	return text


def _section_key(value: Any) -> str:
	text = _normalize_key(value)
	if text in {"top_customer", "top_customers"}:
		return "top_customers"
	if text in {"customer_name", "customer_names"}:
		return "customer_rows"
	if text in {"top_supplier", "top_suppliers"}:
		return "top_suppliers"
	if text in {"supplier_name", "supplier_names"}:
		return "supplier_rows"
	if text in {"top_item", "top_items", "top_product", "top_products"}:
		return "top_items"
	if text in {"item_name", "item_names", "product_name", "product_names"}:
		return "item_rows"
	if text in {"document", "documents"}:
		return "documents"
	return text or "rows"


def _list_row_key(section_key: str) -> str:
	if section_key in {"customer_rows", "top_customers"}:
		return "customer"
	if section_key in {"supplier_rows", "top_suppliers"}:
		return "supplier"
	if section_key in {"item_rows", "top_items"}:
		return "item_name"
	if section_key in {"documents", "document_rows"}:
		return "document"
	return "label"


def _is_supported_list_heading(line: str) -> bool:
	section_key = _section_key(line)
	return section_key in {"customer_rows", "supplier_rows", "item_rows", "documents", "document_rows"}


def _line_looks_like_data_item(line: str) -> bool:
	text = _clean_text(line)
	if not text or _is_table_line(text):
		return False
	if text.startswith(("#", "-", "*")):
		return False
	if ":" in text and len(text.split(":")[0].split()) <= 4:
		return False
	if len(text.split()) > 12:
		return False
	return True


def _assistant_text_from_content(content: Any) -> str:
	text = _clean_text(content)
	if not text:
		return ""
	try:
		payload = json.loads(text)
	except Exception:
		return text
	if isinstance(payload, dict):
		return _clean_text(payload.get("text") or payload.get("message") or payload.get("content"))
	return text


def _is_table_line(line: str) -> bool:
	text = _clean_text(line)
	return text.startswith("|") and text.endswith("|") and text.count("|") >= 2


def _is_separator_line(line: str) -> bool:
	text = _clean_text(line).strip("|").strip()
	if not text:
		return False
	parts = [part.strip() for part in text.split("|")]
	return bool(parts) and all(re.fullmatch(r":?-{3,}:?", part or "") for part in parts)


def _split_table_row(line: str) -> List[str]:
	return [_clean_text(part) for part in _clean_text(line).strip("|").split("|")]


def _heading_before(lines: List[str], table_index: int) -> str:
	for index in range(table_index - 1, -1, -1):
		line = _clean_text(lines[index])
		if not line or _is_table_line(line):
			continue
		return line.lstrip("#").strip()
	return ""


def visible_artifacts_from_assistant_text(text: str, *, artifact_id: str = "") -> List[Dict[str, Any]]:
	lines = str(text or "").splitlines()
	sections: Dict[str, List[Dict[str, Any]]] = {}
	title = ""
	index = 0
	while index < len(lines):
		if not _is_table_line(lines[index]):
			if not title and _clean_text(lines[index]):
				title = _clean_text(lines[index]).lstrip("#").strip()
			index += 1
			continue
		if index + 1 >= len(lines) or not _is_separator_line(lines[index + 1]):
			index += 1
			continue
		heading = _heading_before(lines, index)
		headers = [_normalize_key(value) for value in _split_table_row(lines[index])]
		rows: List[Dict[str, Any]] = []
		index += 2
		while index < len(lines) and _is_table_line(lines[index]):
			values = _split_table_row(lines[index])
			row = {
				headers[col_index]: values[col_index]
				for col_index in range(min(len(headers), len(values)))
				if headers[col_index]
			}
			if row:
				rows.append(row)
			index += 1
		if rows:
			sections[_section_key(heading)] = rows
		continue
	index = 0
	while index < len(lines):
		heading = _clean_text(lines[index]).lstrip("#").strip()
		if not _is_supported_list_heading(heading):
			index += 1
			continue
		section_key = _section_key(heading)
		row_key = _list_row_key(section_key)
		rows: List[Dict[str, Any]] = []
		index += 1
		while index < len(lines) and not _clean_text(lines[index]):
			index += 1
		while index < len(lines):
			line = _clean_text(lines[index]).strip("-* ").strip()
			if not line:
				break
			if _is_table_line(line) or _is_supported_list_heading(line):
				break
			if _line_looks_like_data_item(line):
				rows.append({row_key: line, "label": line})
			index += 1
		if rows and section_key not in sections:
			sections[section_key] = rows
		continue
	if not sections:
		return []
	artifact = {
		"type": "qwen_visible_rendered_artifact",
		"schema_version": VISIBLE_ARTIFACT_VERSION,
		"artifact_id": artifact_id or f"visible-rendered-artifact-{abs(hash(text))}",
		"title": title,
		"report_title": title,
		"family_id": _section_key(title),
		"sections": sections,
		"source": "assistant_visible_markdown",
	}
	if "top_customers" in sections:
		artifact["dimensions"] = {"entity_dimension": "customer"}
	elif "top_suppliers" in sections:
		artifact["dimensions"] = {"entity_dimension": "supplier"}
	elif "top_items" in sections:
		artifact["dimensions"] = {"entity_dimension": "item"}
	return [artifact]


def session_visible_rendered_artifacts(session_doc: Any, *, limit: int = 4) -> List[Dict[str, Any]]:
	if isinstance(session_doc, dict):
		messages = list(session_doc.get("messages") or [])
	else:
		messages = list(getattr(session_doc, "messages", []) or [])
	artifacts: List[Dict[str, Any]] = []
	for offset, message in enumerate(reversed(messages)):
		role = _clean_text(getattr(message, "role", "") or (message.get("role") if isinstance(message, dict) else "")).lower()
		if role != "assistant":
			continue
		content = getattr(message, "content", None)
		if content is None and isinstance(message, dict):
			content = message.get("content")
		text = _assistant_text_from_content(content)
		artifacts.extend(
			visible_artifacts_from_assistant_text(
				text,
				artifact_id=f"visible-assistant-{offset + 1}",
			)
		)
		if len(artifacts) >= limit:
			break
	return artifacts[:limit]
