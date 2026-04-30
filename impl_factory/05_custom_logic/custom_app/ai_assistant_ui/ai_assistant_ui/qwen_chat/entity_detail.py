from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Optional, Tuple

import frappe

from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.customer_kpi_runtime_support import (
	get_customer_credit_policy_snapshot,
	get_customer_receivable_snapshot,
	resolve_company_name,
)
from ai_assistant_ui.qwen_chat.customer_lifecycle_support import get_customer_lifecycle_snapshot
from ai_assistant_ui.qwen_chat.supplier_kpi_runtime_support import get_supplier_payable_snapshot
from ai_assistant_ui.qwen_chat.entity_reference_resolution import (
	normalize_master_data_lookup_slots,
	resolve_entity_reference_from_message,
)
from ai_assistant_ui.qwen_chat.family_adapters import (
	_report_result,
	_report_rows,
	_report_tool,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report
from ai_assistant_ui.qwen_chat.governed_scope_registry import (
	entity_detail_runtime_policy,
	list_active_entity_detail_scope_activations,
)
from ai_assistant_ui.qwen_chat.master_data_family_support import is_master_data_listing_family
from ai_assistant_ui.qwen_chat.entity_dimension_support import entity_type_from_dimension
from ai_assistant_ui.qwen_chat.artifact_reference_support import (
	master_data_entity_key_label,
	ranked_entity_key_label,
	transaction_party_label,
)
from ai_assistant_ui.qwen_chat.semantic_resolution_registry import semantic_slot_alias_phrases_for_value


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _repair_unbalanced_markdown_emphasis(value: Any) -> str:
	text = _clean_text(value)
	if text.count("**") % 2 == 0:
		return text
	return text.replace("**", "")


def _raise_validation_error(message: str) -> None:
	error_type = getattr(frappe, "ValidationError", Exception)
	raise error_type(message)


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _clean_text_list(values: Any) -> List[str]:
	out: List[str] = []
	seen: set[str] = set()
	for value in values or []:
		clean = _clean_text(value)
		if not clean or clean in seen:
			continue
		out.append(clean)
		seen.add(clean)
	return out


def _iso_date(value: Any) -> str:
	if isinstance(value, (dt.date, dt.datetime)):
		return value.isoformat()[:10]
	return _clean_text(value)


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _days_text(value: Any) -> str:
	days = int(max(_numeric(value), 0))
	return f"{days} day" if days == 1 else f"{days} days"


def _markdown_table(columns: List[str], rows: List[List[str]]) -> str:
	if not columns or not rows:
		return ""
	lines = [
		"| " + " | ".join(columns) + " |",
		"| " + " | ".join("---" for _ in columns) + " |",
	]
	for row in rows:
		lines.append("| " + " | ".join(str(cell or "").strip() for cell in row) + " |")
	return "\n".join(lines).strip()


def _render_blocks_markdown(rendered_payload: Dict[str, Any], *, include_title: bool = True) -> str:
	blocks = rendered_payload.get("blocks") if isinstance(rendered_payload.get("blocks"), list) else []
	lines: List[str] = []
	title = _clean_text(rendered_payload.get("title"))
	if include_title and title:
		lines.append(f"## {title}")
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_title = _clean_text(block.get("title"))
		block_type = _clean_text(block.get("block_type"))
		if block_title:
			lines.append(f"### {block_title}")
		if block_type in {"summary_table", "data_table"}:
			columns = [_clean_text(col) for col in (block.get("columns") or []) if _clean_text(col)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "bullet_list":
			for item in (block.get("items") or []):
				value = _clean_text(item)
				if value:
					lines.append(f"- {value}")
	return "\n\n".join(part for part in lines if part).strip()


def _entity_detail_narrative_validation_payload(entity_type: str) -> Dict[str, Any]:
	clean_type = _clean_text(entity_type).lower()
	if clean_type == "customer":
		return {
			"authority_boundary": "customer_receivable_summary_only",
			"forbidden_claims": [
				"credit limit exceeded",
				"credit approval decision",
				"collections recommendation",
				"payment prediction",
				"chronic delinquency analysis",
			],
		}
	if clean_type == "purchase_order":
		return {
			"authority_boundary": "purchase_order_authority_only",
			"forbidden_claims": [
				"actual receipt event date",
				"planned versus actual receipt alignment",
				"purchase receipt proof",
				"downstream receipt-document inference",
			],
		}
	return {}


def _entity_detail_narrative_is_safe(entity_type: str, answer_text: str) -> bool:
	clean_type = _clean_text(entity_type).lower()
	if clean_type == "customer":
		return False
	if clean_type != "purchase_order":
		return True
	text = _normalize_text(answer_text)
	forbidden_phrases = (
		"planned vs. actual receipt",
		"planned vs actual receipt",
		"actual receipt date",
		"deadline met",
		"against the planned receipt date",
		"met the planned receipt date",
		"purchase receipt",
		"physical receipt",
		"supplier invoice",
		"accounts payable",
		"invoice is pending",
	)
	if any(phrase in text for phrase in forbidden_phrases):
		return False
	if re.search(r"received\s+as\s+of\s+\d{4}-\d{2}-\d{2}", text):
		return False
	return True


def _identifier_candidates(message: str) -> List[str]:
	return list(dict.fromkeys(re.findall(r"\b[A-Z0-9]{2,}(?:-[A-Z0-9]+){2,}\b", str(message or ""))))


def _explicit_detail_request(message: str) -> bool:
	if _identifier_candidates(message):
		return True
	return bool(_profile_target_request_candidates(message))


def _active_profile_target_entity_policies() -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for item in list_active_entity_detail_scope_activations(request_mode="profile_target"):
		if not isinstance(item, dict):
			continue
		allowed_lookup_modes = {
			_clean_text(value)
			for value in (item.get("allowed_lookup_modes") or [])
			if _clean_text(value)
		}
		if "profile_target" not in allowed_lookup_modes:
			continue
		entity_grain = _clean_text(item.get("entity_grain"))
		doctype = _clean_text(item.get("doctype"))
		identity_field = _clean_text(item.get("identity_field"))
		if not entity_grain or not doctype or not identity_field:
			continue
		out.append(dict(item))
	return out


def _profile_target_request_candidates(message: str) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	seen: set[tuple[str, str]] = set()
	for policy in _active_profile_target_entity_policies():
		entity_grain = _clean_text(policy.get("entity_grain"))
		if not entity_grain:
			continue
		normalized_slots = normalize_master_data_lookup_slots(
			message=message,
			entity_grain=entity_grain,
		)
		if _clean_text(normalized_slots.get("lookup_mode")) != "profile_target":
			continue
		target_clean = _clean_text(normalized_slots.get("lookup_search_text"))
		if not target_clean:
			continue
		candidate_key = (entity_grain, target_clean)
		if candidate_key in seen:
			continue
		seen.add(candidate_key)
		out.append(
			{
				"entity_grain": entity_grain,
				"target_clean": target_clean,
				"policy": dict(policy),
			}
		)
	return out


def _resolve_named_entity_from_policy_exact(
	*,
	target_clean: str,
	policy: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
	entity_grain = _clean_text(policy.get("entity_grain"))
	doctype = _clean_text(policy.get("doctype"))
	identity_field = _clean_text(policy.get("identity_field"))
	display_field = _clean_text(policy.get("display_field"))
	if not entity_grain or not doctype or not identity_field:
		return None
	if frappe.db.exists(doctype, target_clean):
		label = _clean_text(frappe.db.get_value(doctype, target_clean, display_field)) if display_field else ""
		return {
			"entity_type": entity_grain,
			"entity_key": target_clean,
			"entity_label": label or target_clean,
			"source": "explicit_name",
		}
	if display_field:
		row = frappe.db.get_value(doctype, {display_field: target_clean}, [identity_field, display_field], as_dict=True)
		if isinstance(row, dict) and _clean_text(row.get(identity_field)):
			entity_key = _clean_text(row.get(identity_field))
			entity_label = _clean_text(row.get(display_field)) or entity_key
			return {
				"entity_type": entity_grain,
				"entity_key": entity_key,
				"entity_label": entity_label,
				"source": "explicit_name",
			}
	return None


def _resolve_named_entity_from_policy_reference(
	*,
	target_clean: str,
	policy: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
	entity_grain = _clean_text(policy.get("entity_grain"))
	if not entity_grain:
		return None
	resolution = resolve_entity_reference_from_message(
		request_id="entity-detail-explicit-target",
		entity_grain=entity_grain,
		message=target_clean,
		lookup_mode="profile_target",
		search_text=target_clean,
	)
	resolved_entity = (
		resolution.get("resolved_entity")
		if isinstance(resolution.get("resolved_entity"), dict)
		else {}
	)
	entity_key = _clean_text(resolved_entity.get("entity_key"))
	if _clean_text(resolution.get("resolution_status")) != "resolved" or not entity_key:
		return None
	entity_label = _clean_text(resolved_entity.get("entity_label")) or entity_key
	return {
		"entity_type": entity_grain,
		"entity_key": entity_key,
		"entity_label": entity_label,
		"source": _clean_text(resolved_entity.get("resolution_source")) or "governed_resolution",
	}


def _resolve_named_entity_from_detail_request(message: str) -> Optional[Dict[str, Any]]:
	candidates = _profile_target_request_candidates(message)
	if not candidates:
		return None
	for candidate in candidates:
		target_clean = _clean_text(candidate.get("target_clean"))
		policy = candidate.get("policy") if isinstance(candidate.get("policy"), dict) else {}
		exact_match = _resolve_named_entity_from_policy_exact(target_clean=target_clean, policy=policy)
		if exact_match:
			return exact_match
	for candidate in candidates:
		target_clean = _clean_text(candidate.get("target_clean"))
		policy = candidate.get("policy") if isinstance(candidate.get("policy"), dict) else {}
		resolved_match = _resolve_named_entity_from_policy_reference(target_clean=target_clean, policy=policy)
		if resolved_match:
			return resolved_match
	target_clean = _clean_text(candidates[0].get("target_clean"))
	item_code, item_name = _resolve_item_name(target_clean)
	if item_code:
		return {"entity_type": "item", "entity_key": item_code, "entity_label": item_name or item_code, "source": "explicit_name"}
	return None


def _resolve_item_name(name_or_code: str) -> Tuple[str, str]:
	value = _clean_text(name_or_code)
	if not value:
		return "", ""
	if frappe.db.exists("Item", value):
		item_name = _clean_text(frappe.db.get_value("Item", value, "item_name"))
		return value, item_name or value
	row = frappe.db.get_value("Item", {"item_name": value}, ["name", "item_name"], as_dict=True)
	if isinstance(row, dict):
		return _clean_text(row.get("name")), _clean_text(row.get("item_name")) or value
	return "", ""


def _resolve_explicit_identifier(message: str) -> Optional[Dict[str, Any]]:
	for candidate in _identifier_candidates(message):
		if frappe.db.exists("Sales Invoice", candidate):
			return {"entity_type": "sales_invoice", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Purchase Invoice", candidate):
			return {"entity_type": "purchase_invoice", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Sales Order", candidate):
			return {"entity_type": "sales_order", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Purchase Order", candidate):
			return {"entity_type": "purchase_order", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		if frappe.db.exists("Delivery Note", candidate):
			return {"entity_type": "delivery_note", "entity_key": candidate, "entity_label": candidate, "source": "explicit_identifier"}
		item_code, item_name = _resolve_item_name(candidate)
		if item_code:
			return {"entity_type": "item", "entity_key": item_code, "entity_label": item_name or item_code, "source": "explicit_identifier"}
	return None


def _message_has_deictic_entity_reference(message: str) -> bool:
	text = _normalize_text(message)
	if not text:
		return False
	return bool(
		re.search(
			r"\b(this|that)\s+(customer|supplier|item|product|invoice|order|delivery|one|record|entry)\b",
			text,
		)
	)


def _artifact_entity_candidates(artifact_payload: Dict[str, Any] | None) -> List[Dict[str, Any]]:
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	sections = dict(artifact.get("sections") or {}) if isinstance(artifact.get("sections"), dict) else {}
	dimensions = dict(artifact.get("dimensions") or {}) if isinstance(artifact.get("dimensions"), dict) else {}
	family_id = _clean_text(artifact.get("family_id"))
	out: List[Dict[str, Any]] = []

	def _entity_deictic_aliases(entity_type: str) -> List[str]:
		clean_entity_type = _clean_text(entity_type)
		if not clean_entity_type:
			return []
		entity_aliases: List[str] = []
		for alias in semantic_slot_alias_phrases_for_value("entity_grain", clean_entity_type):
			clean_alias = _normalize_text(alias)
			if not clean_alias or clean_alias.endswith(" name") or clean_alias.endswith(" names"):
				continue
			entity_aliases.append(clean_alias)
		out_aliases: List[str] = []
		for alias in _clean_text_list(entity_aliases):
			out_aliases.extend([f"that {alias}", f"this {alias}"])
		return _clean_text_list(out_aliases)

	def _append(
		entity_type: str,
		entity_key: Any,
		entity_label: Any = "",
		*,
		alias: Any = "",
		aliases: List[str] | None = None,
	) -> None:
		key = _clean_text(entity_key)
		label = _clean_text(entity_label) or key
		if not key and not label:
			return
		alias_values = _clean_text_list(list(aliases or []) + [_clean_text(alias)])
		payload = {
			"entity_type": _clean_text(entity_type),
			"entity_key": key or label,
			"entity_label": label or key,
			"alias": alias_values[0] if alias_values else "",
			"aliases": alias_values,
			"source": "artifact_context",
		}
		if payload not in out:
			out.append(payload)

	if family_id == "transaction_listing":
		document_entity_type = _clean_text(dimensions.get("document_entity_type") or dimensions.get("transaction_type")) or "sales_invoice"
		for row in sections.get("transaction_rows") or []:
			if not isinstance(row, dict):
				continue
			_append(document_entity_type, row.get("document_name"))
			_append("customer", transaction_party_label(row))
	elif family_id == "aging":
		entity_type = "supplier" if _clean_text(dimensions.get("aging_type")) == "accounts_payable" else "customer"
		for row in sections.get("parties") or []:
			if not isinstance(row, dict):
				continue
			_append(entity_type, row.get("party"))
			_append("purchase_invoice" if entity_type == "supplier" else "sales_invoice", row.get("voucher_no"))
	elif family_id == "ranking_analytics":
		entity_type = entity_type_from_dimension(_clean_text(dimensions.get("entity_dimension")))
		for row in sections.get("ranked_rows") or []:
			if not isinstance(row, dict):
				continue
			key, label = ranked_entity_key_label(row)
			_append(entity_type, key, label)
	elif family_id == "product_profitability":
		for row in sections.get("product_rows") or []:
			if not isinstance(row, dict):
				continue
			_append("item", row.get("item_code") or row.get("item_name"), row.get("item_name") or row.get("item_code"))
	elif is_master_data_listing_family(family_id):
		entity_type = _clean_text(dimensions.get("entity_type")) or "customer"
		entity_aliases = _entity_deictic_aliases(entity_type)
		for row in sections.get("directory_rows") or sections.get("customer_rows") or []:
			if not isinstance(row, dict):
				continue
			entity_key, entity_label = master_data_entity_key_label(row)
			_append(
				entity_type,
				entity_key,
				entity_label,
				aliases=entity_aliases,
			)
		resolution_payload = (
			dict(sections.get("entity_reference_resolution"))
			if isinstance(sections.get("entity_reference_resolution"), dict)
			else {}
		)
		resolved_entity = (
			dict(resolution_payload.get("resolved_entity"))
			if isinstance(resolution_payload.get("resolved_entity"), dict)
			else {}
		)
		if _clean_text(resolved_entity.get("entity_key")) or _clean_text(resolved_entity.get("entity_label")):
			_append(
				entity_type,
				resolved_entity.get("entity_key") or resolved_entity.get("entity_label"),
				resolved_entity.get("entity_label") or resolved_entity.get("entity_key"),
				aliases=entity_aliases,
			)
	elif family_id == "entity_detail":
		entity_type = _clean_text(dimensions.get("entity_type"))
		entity_key = _clean_text(dimensions.get("entity_key"))
		entity_label = _clean_text(dimensions.get("entity_label"))
		if entity_type and (entity_key or entity_label):
			_append(
				entity_type,
				entity_key or entity_label,
				entity_label or entity_key,
				aliases=_entity_deictic_aliases(entity_type),
			)
	return out[:50]


def detect_entity_drilldown_request(
	*,
	message: str,
	artifact_payload: Dict[str, Any] | None,
	grounded_turn: Dict[str, Any] | None = None,
) -> Optional[Dict[str, Any]]:
	def _candidate_identity(candidate: Dict[str, Any]) -> tuple[str, str]:
		entity_type = _clean_text(candidate.get("entity_type"))
		entity_key = _clean_text(candidate.get("entity_key") or candidate.get("entity_label"))
		return entity_type, entity_key

	if not _explicit_detail_request(message):
		return None
	explicit = _resolve_explicit_identifier(message)
	if explicit:
		return explicit

	text = _normalize_text(message)
	artifact_candidates = _artifact_entity_candidates(artifact_payload)
	if _message_has_deictic_entity_reference(message):
		matching_candidates: List[Dict[str, Any]] = []
		seen_matching: set[tuple[str, str]] = set()
		for candidate in artifact_candidates:
			alias_values = _clean_text_list(candidate.get("aliases") or [])
			legacy_alias = _clean_text(candidate.get("alias"))
			if legacy_alias:
				alias_values.append(legacy_alias)
			normalized_aliases = [_normalize_text(value) for value in _clean_text_list(alias_values)]
			if not any(alias and alias in text for alias in normalized_aliases):
				continue
			candidate_identity = _candidate_identity(candidate)
			if candidate_identity in seen_matching:
				continue
			seen_matching.add(candidate_identity)
			matching_candidates.append(candidate)
		if len(matching_candidates) == 1:
			return matching_candidates[0]
		unique_candidates: List[Dict[str, Any]] = []
		seen_candidates: set[tuple[str, str]] = set()
		for candidate in artifact_candidates:
			candidate_identity = _candidate_identity(candidate)
			if candidate_identity in seen_candidates:
				continue
			seen_candidates.add(candidate_identity)
			unique_candidates.append(candidate)
		if len(unique_candidates) == 1:
			return unique_candidates[0]

	for candidate in sorted(
		artifact_candidates,
		key=lambda item: len(_clean_text(item.get("entity_label") or item.get("entity_key"))),
		reverse=True,
	):
		key = _normalize_text(candidate.get("entity_key"))
		label = _normalize_text(candidate.get("entity_label"))
		if key and key in text:
			return candidate
		if label and label in text:
			return candidate

	explicit_name = _resolve_named_entity_from_detail_request(message)
	if explicit_name:
		return explicit_name

	known_entities = grounded_turn.get("known_entities") if isinstance(grounded_turn, dict) else []
	if isinstance(known_entities, list):
		for item in sorted(
			[item for item in known_entities if isinstance(item, dict)],
			key=lambda value: len(_clean_text(value.get("name"))),
			reverse=True,
		):
			name = _normalize_text(item.get("name"))
			if name and name in text:
				return {
					"entity_type": _clean_text(item.get("entity_type")),
					"entity_key": _clean_text(item.get("code") or item.get("name")),
					"entity_label": _clean_text(item.get("name")),
					"source": "grounded_turn",
				}
	return None


def _summary_block(title: str, rows: List[Tuple[str, Any]]) -> Dict[str, Any]:
	return {
		"block_type": "summary_table",
		"title": title,
		"columns": ["Field", "Value"],
		"rows": [[_clean_text(label), _clean_text(value)] for label, value in rows if _clean_text(label) and _clean_text(value)],
	}


def _data_block(title: str, columns: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
	return {
		"block_type": "data_table",
		"title": title,
		"columns": [_clean_text(col) for col in columns if _clean_text(col)],
		"rows": [[_clean_text(cell) for cell in row] for row in rows if isinstance(row, list)],
	}


def _bullet_block(title: str, items: List[str]) -> Dict[str, Any]:
	return {
		"block_type": "bullet_list",
		"title": title,
		"items": [_clean_text(item) for item in items if _clean_text(item)],
	}


def _entity_detail_response(
	*,
	detail_company: str,
	entity_type: str,
	entity_key: str,
	entity_label: str,
	title: str,
	source_reports: List[str],
	blocks: List[Dict[str, Any]],
	metrics: Dict[str, Any],
	sections: Dict[str, Any],
	primary_metric_key: str,
	primary_metric_label: str,
	source_grain: str,
	filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	clean_source_reports = [item for item in _clean_text_list(source_reports) if item]
	rendered = {
		"type": "qwen_entity_detail_rendered_response",
		"request_id": "",
		"family_id": "entity_detail",
		"title": _clean_text(title),
		"source_reports": clean_source_reports,
		"blocks": [block for block in blocks if isinstance(block, dict)],
	}
	artifact = {
		"type": "qwen_entity_detail_artifact",
		"artifact_type": "entity_detail_artifact",
		"family_id": "entity_detail",
		"source_reports": clean_source_reports,
		"filters": dict(filters or {"company": detail_company, "entity_key": entity_key}),
		"dimensions": {
			"entity_type": _clean_text(entity_type),
			"entity_key": _clean_text(entity_key),
			"entity_label": _clean_text(entity_label),
			"primary_metric_key": _clean_text(primary_metric_key),
			"primary_metric_label": _clean_text(primary_metric_label),
			"source_grain": _clean_text(source_grain),
		},
		"metrics": dict(metrics or {}),
		"sections": dict(sections or {}),
	}
	return {
		"artifact": artifact,
		"rendered": rendered,
		"company": _clean_text(detail_company),
		"entity_label": _clean_text(entity_label),
	}


def _document_detail_response(
	*,
	detail_company: str,
	entity_type: str,
	entity_key: str,
	entity_label: str,
	title: str,
	source_report: str,
	summary_title: str,
	summary: List[Tuple[str, Any]],
	bullets: List[str],
	item_columns: List[str],
	item_rows: List[List[Any]],
	document_row: Dict[str, Any],
	item_section_rows: List[Dict[str, Any]],
	metrics: Dict[str, Any],
	primary_metric_key: str = "grand_total",
	primary_metric_label: str = "Grand Total",
	extra_sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	sections = {
		"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
		"document_rows": [dict(document_row or {})] if isinstance(document_row, dict) else [],
		"item_rows": [dict(row) for row in (item_section_rows or []) if isinstance(row, dict)],
	}
	if isinstance(extra_sections, dict):
		for key, value in extra_sections.items():
			sections[_clean_text(key)] = value
	blocks = [
		_summary_block(summary_title, summary),
		_bullet_block("Key Facts", bullets),
		_data_block("Items", item_columns, item_rows),
	]
	return _entity_detail_response(
		detail_company=detail_company,
		entity_type=entity_type,
		entity_key=entity_key,
		entity_label=entity_label,
		title=title,
		source_reports=[source_report],
		blocks=blocks,
		metrics=metrics,
		sections=sections,
		primary_metric_key=primary_metric_key,
		primary_metric_label=primary_metric_label,
		source_grain="document_detail",
	)


def _profile_entity_detail_response(
	*,
	detail_company: str,
	entity_type: str,
	entity_key: str,
	entity_label: str,
	profile_title: str,
	summary: List[Tuple[str, Any]],
	bullets: List[str],
	source_reports: List[str],
	metrics: Dict[str, Any],
	primary_metric_key: str,
	primary_metric_label: str,
	source_grain: str,
	extra_blocks: Optional[List[Dict[str, Any]]] = None,
	extra_sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	blocks = [_summary_block(profile_title, summary)]
	if extra_blocks:
		blocks.extend([block for block in extra_blocks if isinstance(block, dict)])
	if bullets:
		blocks.append(_bullet_block("Highlights", bullets))
	sections = {
		"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
	}
	if isinstance(extra_sections, dict):
		for key, value in extra_sections.items():
			sections[_clean_text(key)] = value
	return _entity_detail_response(
		detail_company=detail_company,
		entity_type=entity_type,
		entity_key=entity_key,
		entity_label=entity_label,
		title=f"{entity_label} Details",
		source_reports=source_reports,
		blocks=blocks,
		metrics=metrics,
		sections=sections,
		primary_metric_key=primary_metric_key,
		primary_metric_label=primary_metric_label,
		source_grain=source_grain,
	)


def _current_date_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _resolve_company_name(company: str) -> str:
	return resolve_company_name(company)


def _match_party_row(row: Dict[str, Any], entity_name: str, entity_label: str) -> bool:
	targets = {_normalize_text(entity_name), _normalize_text(entity_label)}
	for field in ("party", "customer", "party_name", "customer_name"):
		value = _normalize_text(row.get(field))
		if value and value in targets:
			return True
	return False


def _customer_receivable_snapshot(entity_name: str, entity_label: str, company: str) -> Dict[str, Any]:
	return get_customer_receivable_snapshot(
		entity_name,
		customer_label=entity_label,
		company=company,
		as_of_date=_current_date_iso(),
	)


def _customer_credit_policy_snapshot(entity_name: str, company: str, outstanding_total: float) -> Dict[str, Any]:
	return get_customer_credit_policy_snapshot(
		entity_name,
		company=company,
		outstanding_total=outstanding_total,
	)


def _sales_invoice_delivery_proof(doc) -> Dict[str, Any]:
	items = list(doc.get("items") or [])
	is_return = int(getattr(doc, "is_return", 0) or 0)
	update_stock = int(getattr(doc, "update_stock", 0) or 0)
	item_count = len(items)
	linked_sales_orders = sorted(
		{
			_clean_text(getattr(row, "sales_order", ""))
			for row in items
			if _clean_text(getattr(row, "sales_order", ""))
		}
	)
	linked_delivery_note_names = sorted(
		{
			_clean_text(getattr(row, "delivery_note", ""))
			for row in items
			if _clean_text(getattr(row, "delivery_note", "")) and _clean_text(getattr(row, "dn_detail", ""))
		}
	)
	delivery_note_rows: List[Dict[str, Any]] = []
	submitted_delivery_note_names: List[str] = []
	for delivery_note_name in linked_delivery_note_names:
		row = frappe.db.get_value(
			"Delivery Note",
			delivery_note_name,
			["name", "docstatus", "status", "posting_date", "is_return", "return_against"],
			as_dict=True,
		)
		row_payload = dict(row or {}) if isinstance(row, dict) else {}
		row_docstatus = int(row_payload.get("docstatus") or 0)
		delivery_note_rows.append(
			{
				"delivery_note": delivery_note_name,
				"docstatus": row_docstatus,
				"status": _clean_text(row_payload.get("status")),
				"posting_date": _iso_date(row_payload.get("posting_date")),
				"is_return": int(row_payload.get("is_return") or 0),
				"return_against": _clean_text(row_payload.get("return_against")),
			}
		)
		if row_docstatus == 1:
			submitted_delivery_note_names.append(delivery_note_name)
	submitted_delivery_note_names = sorted(dict.fromkeys(submitted_delivery_note_names))
	submitted_linked_item_count = 0
	for row in items:
		delivery_note_name = _clean_text(getattr(row, "delivery_note", ""))
		dn_detail = _clean_text(getattr(row, "dn_detail", ""))
		if delivery_note_name and dn_detail and delivery_note_name in submitted_delivery_note_names:
			submitted_linked_item_count += 1
	proof_state = "insufficient_governed_delivery_evidence"
	proof_method = ""
	if update_stock:
		proof_state = (
			"direct_return_proven_via_invoice_stock"
			if is_return
			else "direct_delivery_proven_via_invoice_stock"
		)
		proof_method = "invoice_stock"
	elif item_count > 0 and submitted_linked_item_count == item_count:
		proof_state = (
			"direct_return_proven_via_linked_delivery_note"
			if is_return
			else "direct_delivery_proven_via_linked_delivery_note"
		)
		proof_method = "linked_delivery_note"
	return {
		"proof_state": proof_state,
		"proof_method": proof_method,
		"is_return": is_return,
		"update_stock": update_stock,
		"item_count": item_count,
		"submitted_linked_item_count": submitted_linked_item_count,
		"linked_delivery_note_count": len(submitted_delivery_note_names),
		"delivery_notes": delivery_note_rows,
		"submitted_delivery_notes": submitted_delivery_note_names,
		"submitted_delivery_dates": sorted(
			{
				str(row.get("posting_date") or "").strip()
				for row in delivery_note_rows
				if int(row.get("docstatus") or 0) == 1 and str(row.get("posting_date") or "").strip()
			}
		),
		"sales_orders": linked_sales_orders,
	}


def _sales_invoice_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Sales Invoice", entity_key)
	delivery_proof = _sales_invoice_delivery_proof(doc)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Invoice", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Customer", _clean_text(doc.customer)),
		("Status", _clean_text(doc.status)),
		("Due Date", _iso_date(doc.due_date)),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Outstanding (MMK)", _money(doc.outstanding_amount)),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _numeric(doc.outstanding_amount) > 0:
		bullets.append(f"Outstanding balance remains {_money(doc.outstanding_amount)} MMK.")
	if _clean_text(doc.status):
		bullets.append(f"Current invoice status is {_clean_text(doc.status)}.")
	if delivery_proof.get("proof_state") == "direct_delivery_proven_via_invoice_stock":
		bullets.append("This submitted invoice posted stock movement directly, which provides governed delivery proof.")
	elif delivery_proof.get("proof_state") == "direct_delivery_proven_via_linked_delivery_note":
		submitted_delivery_notes = list(delivery_proof.get("submitted_delivery_notes") or [])
		if submitted_delivery_notes:
			bullets.append(
				"All invoice items are linked to submitted delivery note(s): "
				+ ", ".join(submitted_delivery_notes[:3])
				+ ("." if len(submitted_delivery_notes) <= 3 else ", ...")
			)
	elif delivery_proof.get("proof_state") == "direct_return_proven_via_invoice_stock":
		bullets.append("This is a return invoice with direct stock reversal posted on the submitted invoice.")
	elif delivery_proof.get("proof_state") == "direct_return_proven_via_linked_delivery_note":
		submitted_delivery_notes = list(delivery_proof.get("submitted_delivery_notes") or [])
		if submitted_delivery_notes:
			bullets.append(
				"This return invoice is linked to submitted delivery note reversal evidence: "
				+ ", ".join(submitted_delivery_notes[:3])
				+ ("." if len(submitted_delivery_notes) <= 3 else ", ...")
			)
	return _document_detail_response(
		detail_company=_clean_text(doc.company),
		entity_type="sales_invoice",
		entity_key=doc.name,
		entity_label=doc.name,
		title=f"Sales Invoice {doc.name}",
		source_report="Sales Invoice",
		summary_title="Invoice Summary",
		summary=summary,
		bullets=bullets,
		item_columns=["Item Code", "Item Name", "Qty", "Amount (MMK)"],
		item_rows=item_rows,
		document_row={
			"document_name": doc.name,
			"posting_date": _iso_date(doc.posting_date),
			"customer": _clean_text(doc.customer),
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"status": _clean_text(doc.status),
			"is_return": int(getattr(doc, "is_return", 0) or 0),
			"update_stock": int(getattr(doc, "update_stock", 0) or 0),
		},
		item_section_rows=[
			{
				"item_code": _clean_text(row.item_code),
				"item_name": _clean_text(row.item_name),
				"qty": _numeric(row.qty),
				"amount": _numeric(row.net_amount or row.amount or 0),
				"delivery_note": _clean_text(getattr(row, "delivery_note", "")),
				"dn_detail": _clean_text(getattr(row, "dn_detail", "")),
				"sales_order": _clean_text(getattr(row, "sales_order", "")),
			}
			for row in (doc.get("items") or [])[:25]
		],
		metrics={
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"item_count": len(item_rows),
			"linked_delivery_note_count": int(delivery_proof.get("linked_delivery_note_count") or 0),
		},
		extra_sections={"delivery_proof": [delivery_proof]},
	)


def _purchase_invoice_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Purchase Invoice", entity_key)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.amount or row.base_amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Invoice", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Supplier", _clean_text(doc.supplier)),
		("Status", _clean_text(doc.status)),
		("Due Date", _iso_date(doc.due_date)),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Outstanding (MMK)", _money(doc.outstanding_amount)),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _numeric(doc.outstanding_amount) > 0:
		bullets.append(f"Outstanding supplier balance remains {_money(doc.outstanding_amount)} MMK.")
	if _clean_text(doc.status):
		bullets.append(f"Current purchase invoice status is {_clean_text(doc.status)}.")
	return _document_detail_response(
		detail_company=_clean_text(doc.company),
		entity_type="purchase_invoice",
		entity_key=doc.name,
		entity_label=doc.name,
		title=f"Purchase Invoice {doc.name}",
		source_report="Purchase Invoice",
		summary_title="Invoice Summary",
		summary=summary,
		bullets=bullets,
		item_columns=["Item Code", "Item Name", "Qty", "Amount (MMK)"],
		item_rows=item_rows,
		document_row={
			"document_name": doc.name,
			"posting_date": _iso_date(doc.posting_date),
			"supplier": _clean_text(doc.supplier),
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"status": _clean_text(doc.status),
		},
		item_section_rows=[
			{
				"item_code": _clean_text(row.item_code),
				"item_name": _clean_text(row.item_name),
				"qty": _numeric(row.qty),
				"amount": _numeric(row.amount or row.base_amount or 0),
			}
			for row in (doc.get("items") or [])[:25]
		],
		metrics={
			"grand_total": _numeric(doc.grand_total),
			"outstanding_amount": _numeric(doc.outstanding_amount),
			"item_count": len(item_rows),
		},
	)


def _delivery_note_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Delivery Note", entity_key)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	linked_sales_orders = sorted(
		{
			_clean_text(row.against_sales_order)
			for row in (doc.get("items") or [])
			if _clean_text(row.against_sales_order)
		}
	)
	summary = [
		("Delivery Note", doc.name),
		("Posting Date", _iso_date(doc.posting_date)),
		("Customer", _clean_text(doc.customer)),
		("Status", _clean_text(doc.status)),
		("Return Against", _clean_text(getattr(doc, "return_against", ""))),
		("Total Quantity", _clean_text(getattr(doc, "total_qty", ""))),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Delivery Trip", _clean_text(getattr(doc, "delivery_trip", ""))),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if int(getattr(doc, "is_return", 0) or 0):
		return_against = _clean_text(getattr(doc, "return_against", ""))
		if return_against:
			bullets.append(f"This delivery note is a return against {return_against}.")
		else:
			bullets.append("This delivery note is recorded as a return.")
	if _clean_text(doc.status):
		bullets.append(f"Current delivery note status is {_clean_text(doc.status)}.")
	if _numeric(getattr(doc, "per_billed", 0)) > 0:
		bullets.append(f"Billing completion is {_money(getattr(doc, 'per_billed', 0))}%.")
	if linked_sales_orders:
		bullets.append(f"Linked sales order reference starts from {linked_sales_orders[0]}.")
	return _document_detail_response(
		detail_company=_clean_text(doc.company),
		entity_type="delivery_note",
		entity_key=doc.name,
		entity_label=doc.name,
		title=f"Delivery Note {doc.name}",
		source_report="Delivery Note",
		summary_title="Delivery Summary",
		summary=summary,
		bullets=bullets,
		item_columns=["Item Code", "Item Name", "Qty", "Amount (MMK)"],
		item_rows=item_rows,
		document_row={
			"document_name": doc.name,
			"posting_date": _iso_date(doc.posting_date),
			"customer": _clean_text(doc.customer),
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"status": _clean_text(doc.status),
			"is_return": int(getattr(doc, "is_return", 0) or 0),
			"return_against": _clean_text(getattr(doc, "return_against", "")),
		},
		item_section_rows=[
			{
				"item_code": _clean_text(row.item_code),
				"item_name": _clean_text(row.item_name),
				"qty": _numeric(row.qty),
				"amount": _numeric(row.net_amount or row.amount or 0),
				"against_sales_order": _clean_text(row.against_sales_order),
			}
			for row in (doc.get("items") or [])[:25]
		],
		metrics={
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"item_count": len(item_rows),
		},
	)


def _sales_order_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Sales Order", entity_key)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_clean_text(getattr(row, "delivered_qty", "")),
			_money(getattr(row, "billed_amt", 0)),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Sales Order", doc.name),
		("Transaction Date", _iso_date(getattr(doc, "transaction_date", ""))),
		("Customer", _clean_text(doc.customer)),
		("Status", _clean_text(doc.status)),
		("Delivery Status", _clean_text(getattr(doc, "delivery_status", ""))),
		("Billing Status", _clean_text(getattr(doc, "billing_status", ""))),
		("Planned Delivery Date", _iso_date(getattr(doc, "delivery_date", ""))),
		("Total Quantity", _clean_text(getattr(doc, "total_qty", ""))),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Delivered (%)", _money(getattr(doc, "per_delivered", 0))),
		("Billed (%)", _money(getattr(doc, "per_billed", 0))),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _clean_text(doc.status):
		bullets.append(f"Current sales order status is {_clean_text(doc.status)}.")
	if _clean_text(getattr(doc, "delivery_status", "")):
		bullets.append(f"Delivery progress is {_money(getattr(doc, 'per_delivered', 0))}% ({_clean_text(getattr(doc, 'delivery_status', ''))}).")
	if _clean_text(getattr(doc, "billing_status", "")):
		bullets.append(f"Billing progress is {_money(getattr(doc, 'per_billed', 0))}% ({_clean_text(getattr(doc, 'billing_status', ''))}).")
	if _clean_text(getattr(doc, "delivery_date", "")):
		bullets.append(f"Planned delivery date is {_iso_date(getattr(doc, 'delivery_date', ''))}.")
	return _document_detail_response(
		detail_company=_clean_text(doc.company),
		entity_type="sales_order",
		entity_key=doc.name,
		entity_label=doc.name,
		title=f"Sales Order {doc.name}",
		source_report="Sales Order",
		summary_title="Order Summary",
		summary=summary,
		bullets=bullets,
		item_columns=["Item Code", "Item Name", "Qty", "Delivered Qty", "Billed Amount (MMK)", "Amount (MMK)"],
		item_rows=item_rows,
		document_row={
			"document_name": doc.name,
			"transaction_date": _iso_date(getattr(doc, "transaction_date", "")),
			"customer": _clean_text(doc.customer),
			"status": _clean_text(doc.status),
			"delivery_status": _clean_text(getattr(doc, "delivery_status", "")),
			"billing_status": _clean_text(getattr(doc, "billing_status", "")),
			"delivery_date": _iso_date(getattr(doc, "delivery_date", "")),
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"per_delivered": _numeric(getattr(doc, "per_delivered", 0)),
			"per_billed": _numeric(getattr(doc, "per_billed", 0)),
		},
		item_section_rows=[
			{
				"item_code": _clean_text(row.item_code),
				"item_name": _clean_text(row.item_name),
				"qty": _numeric(row.qty),
				"delivered_qty": _numeric(getattr(row, "delivered_qty", 0)),
				"billed_amount": _numeric(getattr(row, "billed_amt", 0)),
				"amount": _numeric(row.net_amount or row.amount or 0),
				"delivery_date": _iso_date(getattr(row, "delivery_date", "")),
			}
			for row in (doc.get("items") or [])[:25]
		],
		metrics={
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"per_delivered": _numeric(getattr(doc, "per_delivered", 0)),
			"per_billed": _numeric(getattr(doc, "per_billed", 0)),
			"item_count": len(item_rows),
		},
	)


def _purchase_order_receipt_status(percent_received: Any) -> str:
	received = _numeric(percent_received)
	if received >= 99.995:
		return "Fully Received"
	if received > 0:
		return "Partly Received"
	return "Not Received"


def _purchase_order_billing_status(percent_billed: Any) -> str:
	billed = _numeric(percent_billed)
	if billed >= 99.995:
		return "Fully Billed"
	if billed > 0:
		return "Partly Billed"
	return "Not Billed"


def _purchase_order_detail(entity_key: str) -> Dict[str, Any]:
	doc = frappe.get_doc("Purchase Order", entity_key)
	per_received = _numeric(getattr(doc, "per_received", 0))
	per_billed = _numeric(getattr(doc, "per_billed", 0))
	receipt_status = _purchase_order_receipt_status(per_received)
	billing_status = _purchase_order_billing_status(per_billed)
	item_rows = [
		[
			_clean_text(row.item_code),
			_clean_text(row.item_name),
			_clean_text(row.qty),
			_clean_text(getattr(row, "received_qty", "")),
			_money(getattr(row, "billed_amt", 0)),
			_money(row.net_amount or row.amount or 0),
		]
		for row in (doc.get("items") or [])[:10]
	]
	summary = [
		("Purchase Order", doc.name),
		("Transaction Date", _iso_date(getattr(doc, "transaction_date", ""))),
		("Supplier", _clean_text(doc.supplier)),
		("Status", _clean_text(doc.status)),
		("Receipt Status", receipt_status),
		("Billing Status", billing_status),
		("Planned Receipt Date", _iso_date(getattr(doc, "schedule_date", ""))),
		("Total Quantity", _clean_text(getattr(doc, "total_qty", ""))),
		("Grand Total (MMK)", _money(doc.grand_total)),
		("Received (%)", _money(per_received)),
		("Billed (%)", _money(per_billed)),
		("Company", _clean_text(doc.company)),
	]
	bullets = []
	if _clean_text(doc.status):
		bullets.append(f"Current purchase order status is {_clean_text(doc.status)}.")
	bullets.append(f"Receipt progress is {_money(per_received)}% ({receipt_status}).")
	bullets.append(f"Billing progress is {_money(per_billed)}% ({billing_status}).")
	if _clean_text(getattr(doc, "schedule_date", "")):
		bullets.append(f"Planned receipt date is {_iso_date(getattr(doc, 'schedule_date', ''))}.")
	artifact_sections = {
		"summary": [{"label": label, "value": value} for label, value in summary if _clean_text(value)],
		"document_rows": [
			{
				"document_name": doc.name,
				"transaction_date": _iso_date(getattr(doc, "transaction_date", "")),
				"supplier": _clean_text(doc.supplier),
				"status": _clean_text(doc.status),
				"receipt_status": receipt_status,
				"billing_status": billing_status,
				"schedule_date": _iso_date(getattr(doc, "schedule_date", "")),
				"grand_total": _numeric(doc.grand_total),
				"quantity": _numeric(getattr(doc, "total_qty", 0)),
				"per_received": per_received,
				"per_billed": per_billed,
			}
		],
		"item_rows": [
			{
				"item_code": _clean_text(row.item_code),
				"item_name": _clean_text(row.item_name),
				"qty": _numeric(row.qty),
				"received_qty": _numeric(getattr(row, "received_qty", 0)),
				"billed_amount": _numeric(getattr(row, "billed_amt", 0)),
				"amount": _numeric(row.net_amount or row.amount or 0),
				"schedule_date": _iso_date(getattr(row, "schedule_date", "")),
			}
			for row in (doc.get("items") or [])[:25]
		],
	}
	intro = (
		f"{doc.name} is a purchase order from {_clean_text(doc.supplier)} dated "
		f"{_iso_date(getattr(doc, 'transaction_date', ''))}, with a grand total of "
		f"{_money(doc.grand_total)} MMK across {_money(getattr(doc, 'total_qty', 0))} units."
	)
	status_sentence = (
		f"It is currently {_clean_text(doc.status)}, with receipt progress at {_money(per_received)}% "
		f"({receipt_status}) and billing progress at {_money(per_billed)}% ({billing_status})."
	)
	if _clean_text(getattr(doc, "schedule_date", "")):
		status_sentence += f" The planned receipt date on the order is {_iso_date(getattr(doc, 'schedule_date', ''))}."
	preferred_answer_text = (
		intro
		+ "\n\n"
		+ status_sentence
		+ "\n\n"
	).strip()
	response = _document_detail_response(
		detail_company=_clean_text(doc.company),
		entity_type="purchase_order",
		entity_key=doc.name,
		entity_label=doc.name,
		title=f"Purchase Order {doc.name}",
		source_report="Purchase Order",
		summary_title="Order Summary",
		summary=summary,
		bullets=bullets,
		item_columns=["Item Code", "Item Name", "Qty", "Received Qty", "Billed Amount (MMK)", "Amount (MMK)"],
		item_rows=item_rows,
		document_row=(artifact_sections.get("document_rows") or [{}])[0],
		item_section_rows=artifact_sections.get("item_rows") or [],
		metrics={
			"grand_total": _numeric(doc.grand_total),
			"quantity": _numeric(getattr(doc, "total_qty", 0)),
			"per_received": per_received,
			"per_billed": per_billed,
			"item_count": len(item_rows),
		},
	)
	preferred_answer_text = (
		preferred_answer_text
		+ "\n\n"
		+ _render_blocks_markdown(dict(response.get("rendered") or {}), include_title=False)
	).strip()
	response["preferred_answer_text"] = preferred_answer_text
	return response


def _aggregate_invoice_stats(doctype: str, party_field: str, party_value: str, company: str) -> Dict[str, Any]:
	conditions = [f"{party_field}=%s", "docstatus=1"]
	values: List[Any] = [party_value]
	if company:
		conditions.append("company=%s")
		values.append(company)
	row = frappe.db.sql(
		f"""
		select count(*) as invoice_count,
		       coalesce(sum(grand_total), 0) as total_amount,
		       coalesce(sum(outstanding_amount), 0) as outstanding_amount,
		       max(posting_date) as latest_date,
		       min(posting_date) as first_date
		from `tab{doctype}`
		where {' and '.join(conditions)}
		""",
		tuple(values),
		as_dict=True,
	)
	return dict(row[0] or {}) if row else {}


def _recent_invoices(doctype: str, party_field: str, party_value: str, company: str) -> List[Dict[str, Any]]:
	filters = {party_field: party_value, "docstatus": 1}
	if company:
		filters["company"] = company
	return frappe.get_all(
		doctype,
		fields=["name", "posting_date", "grand_total", "outstanding_amount", "status"],
		filters=filters,
		order_by="posting_date desc",
		limit_page_length=7,
	)


def _customer_or_supplier_detail(entity_type: str, entity_key: str, company: str = "") -> Dict[str, Any]:
	doctype = "Customer" if entity_type == "customer" else "Supplier"
	invoice_doctype = "Sales Invoice" if entity_type == "customer" else "Purchase Invoice"
	party_field = "customer" if entity_type == "customer" else "supplier"
	name_field = "customer_name" if entity_type == "customer" else "supplier_name"
	group_field = "customer_group" if entity_type == "customer" else "supplier_group"
	territory_field = "territory" if entity_type == "customer" else "country"
	detail_company = _resolve_company_name(company) if entity_type == "customer" else _clean_text(company)
	master = frappe.db.get_value(
		doctype,
		entity_key,
		[
			"name",
			name_field,
			group_field,
			territory_field,
			"mobile_no",
			"email_id",
			"default_price_list",
			"payment_terms",
			"disabled",
			"is_frozen",
		],
		as_dict=True,
	)
	if not isinstance(master, dict):
		master = frappe.db.get_value(
			doctype,
			{name_field: entity_key},
			[
				"name",
				name_field,
				group_field,
				territory_field,
				"mobile_no",
				"email_id",
				"default_price_list",
				"payment_terms",
				"disabled",
				"is_frozen",
			],
			as_dict=True,
		) or {}
	entity_name = _clean_text(master.get("name")) or entity_key
	entity_label = _clean_text(master.get(name_field)) or entity_name
	stats = _aggregate_invoice_stats(invoice_doctype, party_field, entity_name, detail_company)
	recent = _recent_invoices(invoice_doctype, party_field, entity_name, detail_company)
	credit_snapshot = {}
	policy_snapshot = {}
	lifecycle_snapshot = {}
	payable_snapshot = {}
	if entity_type == "customer":
		credit_snapshot = _customer_receivable_snapshot(entity_name, entity_label, detail_company)
		outstanding_for_policy = _numeric(
			(credit_snapshot.get("metrics") or {}).get("outstanding_total")
			if isinstance(credit_snapshot.get("metrics"), dict)
			else stats.get("outstanding_amount")
		)
		policy_snapshot = _customer_credit_policy_snapshot(entity_name, detail_company, outstanding_for_policy)
		lifecycle_snapshot = get_customer_lifecycle_snapshot(entity_name, company=detail_company)
	else:
		payable_snapshot = get_supplier_payable_snapshot(
			entity_name,
			supplier_label=entity_label,
			company=detail_company,
		)
	summary = [
		("Name", entity_label),
		("Code", entity_name),
		("Group", _clean_text(master.get(group_field))),
		("Territory / Region", _clean_text(master.get(territory_field))),
		("Mobile", _clean_text(master.get("mobile_no"))),
		("Email", _clean_text(master.get("email_id"))),
		("Disabled", "Yes" if master.get("disabled") else "No"),
		("Frozen", "Yes" if master.get("is_frozen") else "No"),
		("Invoice Count", int(stats.get("invoice_count") or 0)),
		("Total Amount (MMK)", _money(stats.get("total_amount"))),
		("Outstanding (MMK)", _money(stats.get("outstanding_amount"))),
		("Latest Invoice Date", _iso_date(stats.get("latest_date"))),
	]
	bullets = []
	if entity_type != "customer":
		if int(stats.get("invoice_count") or 0) > 0:
			bullets.append(f"{entity_label} has {int(stats.get('invoice_count') or 0)} posted {invoice_doctype.lower()} records in the governed history.")
		if _numeric(stats.get("outstanding_amount")) > 0:
			bullets.append(f"Current outstanding balance is {_money(stats.get('outstanding_amount'))} MMK.")
		if _clean_text(stats.get("latest_date")):
			bullets.append(f"Most recent governed transaction was on {_iso_date(stats.get('latest_date'))}.")
		if _numeric((payable_snapshot.get("metrics") or {}).get("overdue_total")) > 0:
			bullets.append(
				f"Current overdue payable balance is {_money((payable_snapshot.get('metrics') or {}).get('overdue_total'))} MMK."
			)
	recent_rows = [
		[
			_clean_text(row.get("name")),
			_iso_date(row.get("posting_date")),
			_money(row.get("grand_total")),
			_money(row.get("outstanding_amount")),
			_clean_text(row.get("status")),
		]
		for row in recent
	]
	status_blocks: List[Dict[str, Any]] = []
	if credit_snapshot:
		credit_title = "Credit Status"
		report_date = _clean_text(credit_snapshot.get("report_date"))
		if report_date:
			credit_title = f"{credit_title} (As of {report_date})"
		status_blocks = [
			_summary_block(credit_title, credit_snapshot.get("summary") or []),
			_data_block(
				"Aging Buckets",
				["Bucket", "Amount (MMK)"],
				[
					[_clean_text(bucket), _money(amount)]
					for bucket, amount in (credit_snapshot.get("bucket_rows") or [])
					if _clean_text(bucket)
				],
			),
		]
	elif payable_snapshot:
		payable_title = "Payable Status"
		report_date = _clean_text(payable_snapshot.get("report_date"))
		if report_date:
			payable_title = f"{payable_title} (As of {report_date})"
		status_blocks = [
			_summary_block(payable_title, payable_snapshot.get("summary") or []),
			_data_block(
				"Aging Buckets",
				["Bucket", "Amount (MMK)"],
				[
					[_clean_text(bucket), _money(amount)]
					for bucket, amount in (payable_snapshot.get("bucket_rows") or [])
					if _clean_text(bucket)
				],
			),
		]
	lifecycle_rows: List[Tuple[str, str]] = []
	if entity_type == "customer":
		customer_created_date = _clean_text(lifecycle_snapshot.get("customer_created_date"))
		first_sales_order_date = _clean_text(lifecycle_snapshot.get("first_sales_order_date"))
		first_sales_invoice_date = _clean_text(lifecycle_snapshot.get("first_sales_invoice_date"))
		as_of_date = _clean_text(lifecycle_snapshot.get("as_of_date"))
		if customer_created_date:
			lifecycle_rows.append(("Customer Created Date", customer_created_date))
			lifecycle_rows.append(
				(
					f"Tenure from Customer Created ({as_of_date or 'As Of'})",
					_days_text(lifecycle_snapshot.get("customer_created_tenure_days")),
				)
			)
		if first_sales_order_date:
			lifecycle_rows.append(("First Sales Order Date", first_sales_order_date))
			lifecycle_rows.append(
				(
					f"Tenure from First Sales Order ({as_of_date or 'As Of'})",
					_days_text(lifecycle_snapshot.get("first_sales_order_tenure_days")),
				)
			)
		if first_sales_invoice_date:
			lifecycle_rows.append(("First Sales Invoice Date", first_sales_invoice_date))
			lifecycle_rows.append(
				(
					f"Tenure from First Sales Invoice ({as_of_date or 'As Of'})",
					_days_text(lifecycle_snapshot.get("first_sales_invoice_tenure_days")),
				)
			)
	policy_rows: List[Tuple[str, str]] = []
	if entity_type == "customer":
		policy_company = _clean_text(policy_snapshot.get("company")) or detail_company
		if policy_company:
			policy_rows.append(("Company", policy_company))
		if _clean_text(master.get("default_price_list")):
			policy_rows.append(("Default Price List", _clean_text(master.get("default_price_list"))))
		if _clean_text(master.get("payment_terms")):
			policy_rows.append(("Payment Terms", _clean_text(master.get("payment_terms"))))
		if bool(policy_snapshot.get("configured")):
			policy_rows.append(("Credit Limit (MMK)", _money(policy_snapshot.get("credit_limit"))))
			policy_rows.append(
				(
					"Credit Limit Status",
					"Exceeded" if bool(policy_snapshot.get("exceeded")) else "Within Limit",
				)
			)
			if bool(policy_snapshot.get("exceeded")):
				policy_rows.append(("Exceeded By (MMK)", _money(policy_snapshot.get("exceeded_amount"))))
			else:
				policy_rows.append(("Available Credit (MMK)", _money(policy_snapshot.get("available_credit"))))
			policy_rows.append(("Credit Used (%)", f"{_numeric(policy_snapshot.get('utilization_ratio')) * 100:.1f}%"))
			if bool(policy_snapshot.get("bypass_credit_limit_check")):
				policy_rows.append(("Sales Order Credit Check", "Bypassed"))
		elif bool(policy_snapshot.get("has_row")) or detail_company:
			policy_rows.append(("Credit Limit", "Not Configured"))
	else:
		if detail_company:
			policy_rows.append(("Company", detail_company))
		if _clean_text(master.get("payment_terms")):
			policy_rows.append(("Payment Terms", _clean_text(master.get("payment_terms"))))
	source_reports = [doctype, invoice_doctype]
	source_reports += ["Sales Order"] if entity_type == "customer" and _clean_text(lifecycle_snapshot.get("first_sales_order_date")) else []
	source_reports += ["Accounts Receivable Summary"] if credit_snapshot else []
	source_reports += ["Accounts Payable Summary"] if payable_snapshot else []
	source_reports += ["Customer Credit Limit"] if entity_type == "customer" and bool(policy_snapshot.get("has_row")) else []
	artifact_metrics = {
		"invoice_count": int(stats.get("invoice_count") or 0),
		"total_amount": _numeric(stats.get("total_amount")),
		"outstanding_amount": _numeric(stats.get("outstanding_amount")),
		"latest_invoice_date": _iso_date(stats.get("latest_date")),
	}
	if credit_snapshot:
		artifact_metrics.update(credit_snapshot.get("metrics") or {})
	if payable_snapshot:
		artifact_metrics.update(payable_snapshot.get("metrics") or {})
	if policy_snapshot:
		artifact_metrics.update(
			{
				"credit_limit": _numeric(policy_snapshot.get("credit_limit")),
				"credit_limit_available": _numeric(policy_snapshot.get("available_credit")),
				"credit_limit_excess": _numeric(policy_snapshot.get("exceeded_amount")),
				"credit_limit_utilization_ratio": _numeric(policy_snapshot.get("utilization_ratio")),
				"credit_limit_configured": bool(policy_snapshot.get("configured")),
				"credit_limit_exceeded": bool(policy_snapshot.get("exceeded")),
				"credit_limit_bypass_sales_order": bool(policy_snapshot.get("bypass_credit_limit_check")),
			}
		)
	if lifecycle_snapshot:
		artifact_metrics.update(
			{
				"customer_created_tenure_days": int(_numeric(lifecycle_snapshot.get("customer_created_tenure_days"))),
				"first_sales_order_tenure_days": int(_numeric(lifecycle_snapshot.get("first_sales_order_tenure_days"))),
				"first_sales_invoice_tenure_days": int(_numeric(lifecycle_snapshot.get("first_sales_invoice_tenure_days"))),
			}
		)
	return _profile_entity_detail_response(
		detail_company=detail_company,
		entity_type=entity_type,
		entity_key=entity_name,
		entity_label=entity_label,
		profile_title="Profile",
		summary=summary,
		bullets=bullets,
		source_reports=source_reports,
		metrics=artifact_metrics,
		primary_metric_key="total_amount",
		primary_metric_label="Total Amount",
		source_grain="party_detail",
		extra_blocks=[
			*([_summary_block("Lifecycle", lifecycle_rows)] if lifecycle_rows else []),
			*status_blocks,
			*([_summary_block("Commercial Policy", policy_rows)] if policy_rows else []),
			_data_block(
				f"Recent {invoice_doctype}s",
				["Invoice", "Posting Date", "Amount (MMK)", "Outstanding (MMK)", "Status"],
				recent_rows,
			),
		],
		extra_sections={
			"credit_status": [
				{"label": _clean_text(label), "value": _clean_text(value)}
				for label, value in (credit_snapshot.get("summary") or [])
				if _clean_text(label) and _clean_text(value)
			],
			"credit_buckets": [
				{"bucket": _clean_text(bucket), "amount": _numeric(amount)}
				for bucket, amount in (credit_snapshot.get("bucket_rows") or [])
				if _clean_text(bucket)
			],
			"payable_status": [
				{"label": _clean_text(label), "value": _clean_text(value)}
				for label, value in (payable_snapshot.get("summary") or [])
				if _clean_text(label) and _clean_text(value)
			],
			"aging_buckets": [
				{"bucket": _clean_text(bucket), "amount": _numeric(amount)}
				for bucket, amount in (payable_snapshot.get("bucket_rows") or [])
				if _clean_text(bucket)
			],
			"credit_policy": [
				{"label": _clean_text(label), "value": _clean_text(value)}
				for label, value in policy_rows
				if _clean_text(label) and _clean_text(value)
			],
			"lifecycle": [
				{"label": _clean_text(label), "value": _clean_text(value)}
				for label, value in lifecycle_rows
				if _clean_text(label) and _clean_text(value)
			],
			"recent_transactions": [
				{
					"document_name": _clean_text(row.get("name")),
					"posting_date": _iso_date(row.get("posting_date")),
					"amount": _numeric(row.get("grand_total")),
					"outstanding_amount": _numeric(row.get("outstanding_amount")),
					"status": _clean_text(row.get("status")),
				}
				for row in recent
			],
		},
	)


def _item_detail(entity_key: str, company: str = "") -> Dict[str, Any]:
	def _item_stock_snapshot(item_code: str, company_name: str = "") -> Dict[str, Any]:
		conditions = ["b.item_code=%s", "coalesce(b.actual_qty, 0) <> 0"]
		values: List[Any] = [item_code]
		if company_name:
			conditions.append("coalesce(w.company, '')=%s")
			values.append(company_name)
		rows = frappe.db.sql(
			f"""
			select b.warehouse as warehouse,
			       coalesce(b.actual_qty, 0) as balance_qty,
			       coalesce(b.stock_value, 0) as balance_value
			from `tabBin` b
			left join `tabWarehouse` w on w.name = b.warehouse
			where {' and '.join(conditions)}
			order by b.actual_qty desc, b.stock_value desc, b.warehouse asc
			limit 10
			""",
			tuple(values),
			as_dict=True,
		)
		stock_rows = [
			{
				"warehouse": _clean_text(row.get("warehouse")),
				"balance_qty": _numeric(row.get("balance_qty")),
				"balance_value": _numeric(row.get("balance_value")),
			}
			for row in (rows or [])
			if isinstance(row, dict) and _clean_text(row.get("warehouse"))
		]
		return {
			"rows": stock_rows,
			"warehouse_count": len(stock_rows),
			"balance_qty": sum(_numeric(row.get("balance_qty")) for row in stock_rows),
			"balance_value": sum(_numeric(row.get("balance_value")) for row in stock_rows),
		}

	item_code, item_name = _resolve_item_name(entity_key)
	if not item_code:
		raise frappe.DoesNotExistError(f"Item `{entity_key}` not found.")
	master = frappe.db.get_value(
		"Item",
		item_code,
		["name", "item_name", "item_group", "brand", "stock_uom", "disabled"],
		as_dict=True,
	) or {}
	conditions = ["sii.item_code=%s", "si.docstatus=1"]
	values: List[Any] = [item_code]
	if company:
		conditions.append("si.company=%s")
		values.append(company)
	stats_row = frappe.db.sql(
		f"""
		select count(distinct si.name) as invoice_count,
		       coalesce(sum(sii.qty), 0) as total_qty,
		       coalesce(sum(sii.net_amount), 0) as total_amount,
		       max(si.posting_date) as latest_date
		from `tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on si.name = sii.parent
		where {' and '.join(conditions)}
		""",
		tuple(values),
		as_dict=True,
	)
	stats = dict(stats_row[0] or {}) if stats_row else {}
	recent = frappe.db.sql(
		f"""
		select si.name as invoice,
		       si.posting_date as posting_date,
		       sii.qty as qty,
		       sii.net_amount as amount
		from `tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on si.name = sii.parent
		where {' and '.join(conditions)}
		order by si.posting_date desc
		limit 7
		""",
		tuple(values),
		as_dict=True,
	)
	stock_snapshot = _item_stock_snapshot(item_code, company)
	entity_label = _clean_text(master.get("item_name")) or item_name or item_code
	summary = [
		("Item Name", entity_label),
		("Item Code", item_code),
		("Item Group", _clean_text(master.get("item_group"))),
		("Brand", _clean_text(master.get("brand"))),
		("UOM", _clean_text(master.get("stock_uom"))),
		("Disabled", "Yes" if master.get("disabled") else "No"),
		("Invoice Count", int(stats.get("invoice_count") or 0)),
		("Total Sold Qty", _clean_text(stats.get("total_qty"))),
		("Total Sales Amount (MMK)", _money(stats.get("total_amount"))),
		("Latest Sale Date", _iso_date(stats.get("latest_date"))),
		("Total On Hand Qty", _clean_text(stock_snapshot.get("balance_qty"))),
		("Total Stock Value (MMK)", _money(stock_snapshot.get("balance_value"))),
		("Warehouse Count", _clean_text(stock_snapshot.get("warehouse_count"))),
	]
	bullets = []
	if int(stats.get("invoice_count") or 0) > 0:
		bullets.append(f"{entity_label} appears on {int(stats.get('invoice_count') or 0)} posted sales invoices in the governed history.")
	if _clean_text(stats.get("latest_date")):
		bullets.append(f"Most recent sale was on {_iso_date(stats.get('latest_date'))}.")
	if int(stock_snapshot.get("warehouse_count") or 0) > 0:
		bullets.append(
			f"Current on-hand stock is {_clean_text(stock_snapshot.get('balance_qty'))} "
			f"{_clean_text(master.get('stock_uom')) or 'units'} across {int(stock_snapshot.get('warehouse_count') or 0)} warehouses."
		)
	else:
		bullets.append("No on-hand stock is currently recorded for this item.")
	recent_rows = [
		[
			_clean_text(row.get("invoice")),
			_iso_date(row.get("posting_date")),
			_clean_text(row.get("qty")),
			_money(row.get("amount")),
		]
		for row in recent
	]
	stock_rows = [
		[
			_clean_text(row.get("warehouse")),
			_clean_text(row.get("balance_qty")),
			_money(row.get("balance_value")),
		]
		for row in (stock_snapshot.get("rows") or [])
	]
	extra_blocks: List[Dict[str, Any]] = []
	if stock_rows:
		extra_blocks.append(
			_data_block(
				"Stock by Warehouse",
				["Warehouse", "Qty", "Stock Value (MMK)"],
				stock_rows,
			)
		)
	if recent_rows:
		extra_blocks.append(
			_data_block("Recent Sales", ["Invoice", "Posting Date", "Qty", "Amount (MMK)"], recent_rows)
		)
	return _profile_entity_detail_response(
		detail_company=company,
		entity_type="item",
		entity_key=item_code,
		entity_label=entity_label,
		profile_title="Item Profile",
		summary=summary,
		bullets=bullets,
		source_reports=["Item", "Bin", "Sales Invoice Item"],
		metrics={
			"invoice_count": int(stats.get("invoice_count") or 0),
			"total_qty": _numeric(stats.get("total_qty")),
			"total_amount": _numeric(stats.get("total_amount")),
			"balance_qty": _numeric(stock_snapshot.get("balance_qty")),
			"balance_value": _numeric(stock_snapshot.get("balance_value")),
			"warehouse_count": int(stock_snapshot.get("warehouse_count") or 0),
		},
		primary_metric_key="total_amount",
		primary_metric_label="Total Sales Amount",
		source_grain="item_detail",
		extra_blocks=extra_blocks,
		extra_sections={
			"stock_rows": [
				{
					"warehouse": _clean_text(row.get("warehouse")),
					"balance_qty": _numeric(row.get("balance_qty")),
					"balance_value": _numeric(row.get("balance_value")),
				}
				for row in (stock_snapshot.get("rows") or [])
			],
			"recent_transactions": [
				{
					"document_name": _clean_text(row.get("invoice")),
					"posting_date": _iso_date(row.get("posting_date")),
					"quantity": _numeric(row.get("qty")),
					"amount": _numeric(row.get("amount")),
				}
				for row in recent
			],
		},
	)


def _entity_grounded_turn_payload(
	*,
	request_id: str,
	entity_type: str,
	entity_key: str,
	entity_label: str,
	company: str,
	artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	sections = dict(artifact_payload.get("sections") or {}) if isinstance(artifact_payload.get("sections"), dict) else {}
	recent_rows = sections.get("recent_transactions") if isinstance(sections.get("recent_transactions"), list) else []
	document_rows = sections.get("document_rows") if isinstance(sections.get("document_rows"), list) else []
	table_rows = recent_rows or document_rows
	if table_rows and isinstance(table_rows[0], dict):
		headers = [str(key or "").strip().replace("_", " ").title() for key in table_rows[0].keys()]
	else:
		headers = []
	return {
		"type": "qwen_grounded_turn_context",
		"contract_version": "1.0",
		"request_id": request_id,
		"trace_request_id": request_id,
		"grounded": True,
		"source_kind": "entity_detail",
		"source_name": f"{entity_label} Detail",
		"company": company,
		"date_range": {},
		"filters": {"company": company, "entity_type": entity_type, "entity_key": entity_key},
		"dimensions": [entity_type],
		"metrics": [str(key or "").strip() for key in (artifact_payload.get("metrics") or {}).keys()],
		"returned_schema": headers,
		"table_rows": list(table_rows or [])[:100],
		"row_count": len(table_rows or []),
		"base_language": "en",
		"transform_chain": [],
		"artifact_family_id": "entity_detail",
		"artifact_type": "entity_detail_artifact",
		"artifact_source_reports": [str(item or "").strip() for item in (artifact_payload.get("source_reports") or []) if _clean_text(item)],
		"known_entities": [{"entity_type": entity_type, "name": entity_label, "code": entity_key}],
		"known_documents": [
			str(row.get("document_name") or "").strip()
			for row in list(table_rows or [])
			if isinstance(row, dict) and str(row.get("document_name") or "").strip()
		],
	}


def _sales_invoice_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _sales_invoice_detail(entity_key)


def _purchase_invoice_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _purchase_invoice_detail(entity_key)


def _sales_order_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _sales_order_detail(entity_key)


def _purchase_order_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _purchase_order_detail(entity_key)


def _delivery_note_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _delivery_note_detail(entity_key)


def _customer_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _customer_or_supplier_detail("customer", entity_key, company=company)


def _supplier_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _customer_or_supplier_detail("supplier", entity_key, company=company)


def _item_detail_executor(entity_key: str, *, company: str = "") -> Dict[str, Any]:
	return _item_detail(entity_key, company=company)


_ENTITY_DETAIL_EXECUTOR_BY_TYPE = {
	"sales_invoice": _sales_invoice_detail_executor,
	"purchase_invoice": _purchase_invoice_detail_executor,
	"sales_order": _sales_order_detail_executor,
	"purchase_order": _purchase_order_detail_executor,
	"delivery_note": _delivery_note_detail_executor,
	"customer": _customer_detail_executor,
	"supplier": _supplier_detail_executor,
	"item": _item_detail_executor,
}


def _resolve_entity_detail_executor(entity_type: str):
	return _ENTITY_DETAIL_EXECUTOR_BY_TYPE.get(_clean_text(entity_type))


def _prefix_entity_detail_answer(entity_label: str, answer_text: str) -> str:
	clean_label = _clean_text(entity_label)
	clean_answer = _repair_unbalanced_markdown_emphasis(answer_text)
	if not clean_label:
		return clean_answer
	if clean_answer and _normalize_text(clean_label) in _normalize_text(clean_answer):
		return clean_answer
	prefix = f"Here are the details for {clean_label}."
	return f"{prefix}\n\n{clean_answer}".strip() if clean_answer else prefix


def _resolve_entity_detail_answer(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	entity_type: str,
	preferred_answer_text: str,
	artifact_payload: Dict[str, Any],
	rendered_payload: Dict[str, Any],
	response_policy: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
	preferred_text = _clean_text(preferred_answer_text)
	if preferred_text:
		return preferred_text, {}, {}
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=artifact_payload,
		rendered_response_payload=rendered_payload,
		response_policy=response_policy,
		validation_payload=_entity_detail_narrative_validation_payload(entity_type),
	)
	narrative_payload = narrate_governed_artifact(
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		request_id=request_id,
		artifact_context=artifact_context,
		response_policy=response_policy,
	)
	narrative_contract = build_artifact_narrative_contract(
		request_id=request_id,
		artifact_context=artifact_context,
		runtime_payload=narrative_payload,
	)
	narrative_contract_payload = narrative_contract.to_payload() if narrative_contract is not None else {}
	answer_text = _clean_text(narrative_contract_payload.get("answer_text"))
	if answer_text and not _entity_detail_narrative_is_safe(entity_type, answer_text):
		answer_text = ""
		narrative_payload = {}
		narrative_contract_payload = {}
	if not answer_text:
		answer_text = _render_blocks_markdown(rendered_payload)
	return answer_text, narrative_payload, narrative_contract_payload


def _entity_detail_result_payload(
	*,
	ok: bool,
	answer_text: str,
	artifact_payload: Dict[str, Any],
	rendered_payload: Dict[str, Any],
	narrative_payload: Dict[str, Any],
	narrative_contract_payload: Dict[str, Any],
	entity_type: str,
	entity_key: str,
	entity_label: str,
	request_id: str,
	company: str,
) -> Dict[str, Any]:
	return {
		"ok": ok,
		"answer_text": answer_text,
		"artifact_payload": artifact_payload,
		"rendered_response_payload": rendered_payload,
		"narrative_payload": narrative_payload,
		"narrative_contract_payload": narrative_contract_payload,
		"entity_reference": {
			"entity_type": entity_type,
			"entity_key": entity_key,
			"entity_label": entity_label,
		},
		"grounded_turn_payload": _entity_grounded_turn_payload(
			request_id=request_id,
			entity_type=entity_type,
			entity_key=entity_key,
			entity_label=entity_label,
			company=company,
			artifact_payload=artifact_payload,
		),
	}


def execute_entity_drilldown(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	entity_reference: Dict[str, Any],
	response_policy: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	entity_type = _clean_text(entity_reference.get("entity_type"))
	entity_key = _clean_text(entity_reference.get("entity_key") or entity_reference.get("entity_label"))
	company = _clean_text((grounded_turn or {}).get("company")) if isinstance(grounded_turn, dict) else ""
	runtime_policy = entity_detail_runtime_policy(entity_type)
	if not runtime_policy or not runtime_policy.get("can_execute"):
		_raise_validation_error(f"Unsupported governed entity detail type `{entity_type}`.")
	executor = _resolve_entity_detail_executor(entity_type)
	if executor is None:
		_raise_validation_error(f"Unsupported governed entity detail type `{entity_type}`.")
	detail = executor(entity_key, company=company)

	artifact_payload = dict(detail.get("artifact") or {})
	rendered_payload = dict(detail.get("rendered") or {})
	artifact_payload["request_id"] = request_id
	rendered_payload["request_id"] = request_id
	entity_label = _clean_text(detail.get("entity_label")) or entity_key
	company = _clean_text(detail.get("company")) or company
	answer_text, narrative_payload, narrative_contract_payload = _resolve_entity_detail_answer(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		entity_type=entity_type,
		preferred_answer_text=_clean_text(detail.get("preferred_answer_text")),
		artifact_payload=artifact_payload,
		rendered_payload=rendered_payload,
		response_policy=response_policy,
	)
	answer_text = _prefix_entity_detail_answer(entity_label, answer_text)
	return _entity_detail_result_payload(
		ok=bool(answer_text),
		answer_text=answer_text,
		artifact_payload=artifact_payload,
		rendered_payload=rendered_payload,
		narrative_payload=narrative_payload,
		narrative_contract_payload=narrative_contract_payload,
		entity_type=entity_type,
		entity_key=entity_key,
		entity_label=entity_label,
		request_id=request_id,
		company=company,
	)
