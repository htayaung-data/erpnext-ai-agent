from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .artifact_reference_support import (
	master_data_entity_key_label,
	ranked_entity_key_label,
	transaction_party_label,
)
from .composite_row_support import composite_row_entity_code, composite_row_identity_value
from .natural_business_understanding_contracts import NBUContextResolutionContract


ROW_LIST_KEYS = (
	"ranked_rows",
	"top_rows",
	"top_customers",
	"top_suppliers",
	"top_items",
	"documents",
	"document_rows",
	"transaction_rows",
	"item_rows",
	"customer_rows",
	"supplier_rows",
	"stock_rows",
	"rows",
	"records",
	"data",
)

OPTION_LIST_KEYS = (
	"candidate_options",
	"possible_matches",
	"matching_options",
	"clarification_options",
	"options",
	"choices",
)

ENTITY_TYPE_FIELDS = (
	"entity_type",
	"party_type",
	"doctype",
	"document_type",
)

ROW_ENTITY_KIND_HINTS = (
	("customer", "customer"),
	("customer_name", "customer"),
	("supplier", "supplier"),
	("supplier_name", "supplier"),
	("item", "item"),
	("item_name", "item"),
	("item_code", "item"),
	("warehouse", "warehouse"),
	("warehouse_name", "warehouse"),
	("account", "account"),
	("account_name", "account"),
	("line", "statement_line"),
	("metric", "metric"),
	("sales_invoice", "sales_invoice"),
	("purchase_invoice", "purchase_invoice"),
	("purchase_receipt", "purchase_receipt"),
	("payment_entry", "payment_entry"),
	("delivery_note", "delivery_note"),
	("stock_entry", "stock_entry"),
	("document", "document"),
	("document_name", "document"),
	("invoice", "invoice"),
	("voucher_no", "voucher"),
)

ROW_IDENTITY_LABEL_KEYS = (
	"entity_label",
	"entity",
	"customer",
	"customer_name",
	"supplier",
	"supplier_name",
	"item",
	"item_name",
	"item_code",
	"warehouse",
	"warehouse_name",
	"account",
	"account_name",
	"line",
	"metric",
	"sales_invoice",
	"purchase_invoice",
	"purchase_receipt",
	"payment_entry",
	"delivery_note",
	"stock_entry",
	"document",
	"document_name",
	"invoice",
	"voucher_no",
	"name",
	"label",
	"title",
	"value",
)

ROW_IDENTITY_KEY_FIELDS = (
	"entity_key",
	"entity_code",
	"code",
	"customer",
	"customer_name",
	"supplier",
	"supplier_name",
	"item_code",
	"item_name",
	"item",
	"warehouse",
	"warehouse_name",
	"account",
	"account_name",
	"sales_invoice",
	"purchase_invoice",
	"purchase_receipt",
	"payment_entry",
	"delivery_note",
	"stock_entry",
	"document",
	"document_name",
	"invoice",
	"voucher_no",
	"name",
	"label",
	"value",
)

DOCUMENT_IDENTITY_KEYS = (
	"sales_invoice",
	"purchase_invoice",
	"purchase_receipt",
	"payment_entry",
	"delivery_note",
	"stock_entry",
	"document",
	"document_name",
	"invoice",
	"voucher_no",
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _normalize_text(value: Any) -> str:
	return re.sub(r"\s+", " ", _clean_text(value).lower()).strip()


def _as_row_dict(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	text = _clean_text(value)
	if text:
		return {"entity": text, "label": text, "value": text}
	return {}


def _row_identity_label(row: Dict[str, Any]) -> str:
	for key in ROW_IDENTITY_LABEL_KEYS:
		value = _clean_text(row.get(key))
		if value:
			return value
	return ""


def _row_identity_key(row: Dict[str, Any], fallback_label: str = "") -> str:
	for key in ROW_IDENTITY_KEY_FIELDS:
		value = _clean_text(row.get(key))
		if value:
			return value
	return _clean_text(fallback_label)


def _document_identity(row: Dict[str, Any]) -> Tuple[str, str]:
	for key in DOCUMENT_IDENTITY_KEYS:
		value = _clean_text(row.get(key))
		if value:
			return value, value
	return "", ""


def nbu_row_identity_label(row: Dict[str, Any]) -> str:
	"""Return the best business-facing label for a visible artifact row."""

	return _row_identity_label(_clean_dict(row))


def nbu_row_identity_alias_values(row: Dict[str, Any]) -> List[str]:
	"""Return stable identity values used for cross-family visible-row matching."""

	source = _clean_dict(row)
	return list(dict.fromkeys(_clean_text(source.get(key)) for key in ROW_IDENTITY_LABEL_KEYS + ROW_IDENTITY_KEY_FIELDS if _clean_text(source.get(key))))


def _ordinal_reference_index(message: str) -> int:
	normalized = _normalize_text(message)
	if not normalized:
		return -1
	ordinal_words = {
		"first": 1,
		"second": 2,
		"third": 3,
		"fourth": 4,
		"fifth": 5,
		"sixth": 6,
		"seventh": 7,
		"eighth": 8,
		"ninth": 9,
		"tenth": 10,
		"last": -1,
	}
	for word, value in ordinal_words.items():
		if re.search(rf"\b{re.escape(word)}\b", normalized):
			return value - 1 if value > 0 else -2
	for pattern in (
		r"\b(?:rank|row|number|no|no\.|#)\s*(\d{1,2})\b",
		r"\b(\d{1,2})(?:st|nd|rd|th)\b",
	):
		match = re.search(pattern, normalized)
		if not match:
			continue
		try:
			value = int(match.group(1))
		except (TypeError, ValueError):
			continue
		if value > 0:
			return value - 1
	return -1


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position", "idx", "index"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _rows_from_list(value: Any) -> List[Dict[str, Any]]:
	if not isinstance(value, list):
		return []
	return [row for row in (_as_row_dict(item) for item in value) if row]


def _first_rows_from_mapping(mapping: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
	for key in ROW_LIST_KEYS:
		rows = _rows_from_list(mapping.get(key))
		if rows:
			return rows, key
	return [], ""


def _artifact_rows(artifact_payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
	artifact = _clean_dict(artifact_payload)
	if not artifact:
		return [], ""
	sections = _clean_dict(artifact.get("sections"))
	rows, source_key = _first_rows_from_mapping(sections)
	if rows:
		return rows, f"sections.{source_key}"
	blocks = artifact.get("blocks")
	if isinstance(blocks, list):
		for index, block in enumerate(blocks):
			block_rows, source_key = _first_rows_from_mapping(_clean_dict(block))
			if block_rows:
				return block_rows, f"blocks[{index}].{source_key}"
	rows, source_key = _first_rows_from_mapping(artifact)
	if rows:
		return rows, source_key
	return [], ""


def nbu_artifact_rows(artifact_payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
	"""Return the first visible row collection from a governed artifact payload."""

	return _artifact_rows(artifact_payload)


def nbu_ordinal_reference_index(message: str) -> int:
	"""Return a zero-based index for natural ordinal/rank references, or -1."""

	return _ordinal_reference_index(message)


def _options_from_payload(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
	source = _clean_dict(payload)
	for key in OPTION_LIST_KEYS:
		options = _rows_from_list(source.get(key))
		if options:
			return options, key
	target_entity = _clean_dict(source.get("target_entity"))
	for key in OPTION_LIST_KEYS:
		options = _rows_from_list(target_entity.get(key))
		if options:
			return options, f"target_entity.{key}"
	return [], ""


def _candidate_options(
	*,
	candidate_payload: Dict[str, Any],
	current_artifact: Dict[str, Any],
	recent_focus: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], str]:
	for label, payload in (
		("candidate", candidate_payload),
		("current_artifact", current_artifact),
		("recent_focus", recent_focus),
	):
		options, source = _options_from_payload(payload)
		if options:
			return options, f"{label}.{source}"
	return [], ""


def _artifact_id(artifact_payload: Dict[str, Any], recent_focus: Dict[str, Any]) -> str:
	for payload in (artifact_payload, recent_focus):
		source = _clean_dict(payload)
		for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
			value = _clean_text(source.get(key))
			if value:
				return value
	return ""


def _focus_entity_payload(focus_payload: Dict[str, Any]) -> Dict[str, Any]:
	focus = _clean_dict(focus_payload)
	focus_kind = _clean_text(focus.get("focus_kind"))
	focus_grain = _clean_text(focus.get("focus_grain"))
	focus_label = _clean_text(focus.get("focus_label"))
	focus_key = _clean_text(focus.get("focus_key")) or focus_label
	if not focus_label and not focus_key:
		return {}
	return {
		key: value
		for key, value in {
			"entity_type": focus_grain,
			"entity_key": focus_key,
			"entity_label": focus_label or focus_key,
			"focus_kind": focus_kind,
			"focus_grain": focus_grain,
		}.items()
		if value
	}


def _resolve_from_recent_focus(
	*,
	target_reference: str,
	recent_focus: Dict[str, Any],
) -> NBUContextResolutionContract:
	entity = _focus_entity_payload(recent_focus)
	if not entity:
		return NBUContextResolutionContract(
			status="not_supported",
			target_reference=target_reference,
			reason="No recent-focus entity, list, document, or statement target was available for restoration.",
		)
	return NBUContextResolutionContract(
		status="resolved",
		target_reference=target_reference,
		resolved_artifact_id=_artifact_id({}, recent_focus),
		resolved_entity=entity,
		reason="Resolved from the current recent-focus contract.",
	)


def _entity_type_from_payloads(row: Dict[str, Any], artifact_payload: Dict[str, Any], candidate_payload: Dict[str, Any]) -> str:
	for source in (row, _clean_dict(candidate_payload.get("target_entity")), artifact_payload):
		for key in ENTITY_TYPE_FIELDS:
			value = _clean_text(_clean_dict(source).get(key))
			if value:
				return value.lower()
	dimensions = _clean_dict(artifact_payload.get("dimensions"))
	value = _clean_text(dimensions.get("entity_dimension") or dimensions.get("entity_type"))
	if value:
		return value.lower()
	for key, entity_type in ROW_ENTITY_KIND_HINTS:
		if _clean_text(row.get(key)):
			return entity_type
	return ""


def _row_entity_payload(row: Dict[str, Any], artifact_payload: Dict[str, Any], candidate_payload: Dict[str, Any]) -> Dict[str, Any]:
	key, label = _document_identity(row)
	if not key and not label:
		key, label = ranked_entity_key_label(row)
	if not key and not label:
		key, label = master_data_entity_key_label(row)
	if not label:
		label = transaction_party_label(row)
	if not key:
		key = composite_row_entity_code(row)
	if not label:
		policy = _clean_text(_clean_dict(artifact_payload.get("dimensions")).get("row_identity_policy"))
		label = composite_row_identity_value(row, policy) if policy else ""
	if not label:
		label = _row_identity_label(row)
	if not key:
		key = _row_identity_key(row, label)
	entity_type = _entity_type_from_payloads(row, artifact_payload, candidate_payload)
	payload = {
		"entity_type": entity_type,
		"entity_key": key,
		"entity_label": label,
	}
	if row:
		payload["row"] = dict(row)
	return {key: value for key, value in payload.items() if value not in ("", {}, [])}


def nbu_row_entity_payload(
	row: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	candidate_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	"""Build the generic entity payload used by NBU row/context resolvers."""

	return _row_entity_payload(row, artifact_payload, _clean_dict(candidate_payload))


def _named_row_matches(raw_message: str, rows: List[Dict[str, Any]], artifact_payload: Dict[str, Any], candidate_payload: Dict[str, Any]) -> List[Tuple[int, Dict[str, Any]]]:
	normalized_message = f" {_normalize_text(raw_message)} "
	matches: List[Tuple[int, Dict[str, Any]]] = []
	if not normalized_message.strip():
		return matches
	for index, row in enumerate(rows):
		entity = _row_entity_payload(row, artifact_payload, candidate_payload)
		names = [
			entity.get("entity_label"),
			entity.get("entity_key"),
			*nbu_row_identity_alias_values(row),
		]
		for name in names:
			normalized_name = _normalize_text(name)
			if normalized_name and f" {normalized_name} " in normalized_message:
				matches.append((index, row))
				break
	return matches


def _resolved_contract(
	*,
	target_reference: str,
	artifact_payload: Dict[str, Any],
	recent_focus: Dict[str, Any],
	candidate_payload: Dict[str, Any],
	rows: List[Dict[str, Any]],
	row_index: int,
	reason: str,
) -> NBUContextResolutionContract:
	row = rows[row_index]
	rank = _row_rank(row, row_index)
	return NBUContextResolutionContract(
		status="resolved",
		target_reference=target_reference,
		resolved_artifact_id=_artifact_id(artifact_payload, recent_focus),
		resolved_row_index=row_index,
		resolved_rank=rank,
		resolved_entity=_row_entity_payload(row, artifact_payload, candidate_payload),
		reason=reason,
	)


def _resolve_from_rows(
	*,
	raw_message: str,
	target_reference: str,
	candidate_payload: Dict[str, Any],
	current_artifact: Dict[str, Any],
	recent_focus: Dict[str, Any],
) -> NBUContextResolutionContract:
	rows, source_key = _artifact_rows(current_artifact)
	if not rows:
		rows, source_key = _artifact_rows(recent_focus)
	if not rows:
		return NBUContextResolutionContract(
			status="not_supported",
			target_reference=target_reference,
			reason="No current artifact row list was available for context reference resolution.",
		)

	ordinal_index = _ordinal_reference_index(raw_message)
	if ordinal_index == -2:
		return _resolved_contract(
			target_reference=target_reference,
			artifact_payload=current_artifact,
			recent_focus=recent_focus,
			candidate_payload=candidate_payload,
			rows=rows,
			row_index=len(rows) - 1,
			reason=f"Resolved last visible row from {source_key}.",
		)
	if ordinal_index >= 0:
		for index, row in enumerate(rows):
			if _row_rank(row, index) == ordinal_index + 1:
				return _resolved_contract(
					target_reference=target_reference,
					artifact_payload=current_artifact,
					recent_focus=recent_focus,
					candidate_payload=candidate_payload,
					rows=rows,
					row_index=index,
					reason=f"Resolved rank {ordinal_index + 1} from {source_key}.",
				)
		if ordinal_index < len(rows):
			return _resolved_contract(
				target_reference=target_reference,
				artifact_payload=current_artifact,
				recent_focus=recent_focus,
				candidate_payload=candidate_payload,
				rows=rows,
				row_index=ordinal_index,
				reason=f"Resolved row position {ordinal_index + 1} from {source_key}.",
			)
		return NBUContextResolutionContract(
			status="out_of_range",
			target_reference=target_reference,
			ambiguity_options=[_clean_text(_row_entity_payload(row, current_artifact, candidate_payload).get("entity_label")) for row in rows[:10]],
			reason=f"Requested row/rank {ordinal_index + 1}, but only {len(rows)} row(s) are available.",
		)

	named_matches = _named_row_matches(raw_message, rows, current_artifact, candidate_payload)
	if len(named_matches) == 1:
		index, _row = named_matches[0]
		return _resolved_contract(
			target_reference=target_reference,
			artifact_payload=current_artifact,
			recent_focus=recent_focus,
			candidate_payload=candidate_payload,
			rows=rows,
			row_index=index,
			reason=f"Resolved named row from {source_key}.",
		)
	if len(named_matches) > 1:
		return NBUContextResolutionContract(
			status="ambiguous",
			target_reference=target_reference,
			ambiguity_options=[_clean_text(_row_entity_payload(row, current_artifact, candidate_payload).get("entity_label")) for _, row in named_matches[:10]],
			reason="More than one visible row matched the requested entity reference.",
		)
	if len(rows) == 1 and target_reference in {"current_artifact", "selected_entity"}:
		return _resolved_contract(
			target_reference=target_reference,
			artifact_payload=current_artifact,
			recent_focus=recent_focus,
			candidate_payload=candidate_payload,
			rows=rows,
			row_index=0,
			reason=f"Resolved the only visible row from {source_key}.",
		)
	return NBUContextResolutionContract(
		status="ambiguous",
		target_reference=target_reference,
		ambiguity_options=[_clean_text(_row_entity_payload(row, current_artifact, candidate_payload).get("entity_label")) for row in rows[:10]],
		reason="The message references the current artifact, but no unique row could be selected.",
	)


def _resolve_from_candidate_options(
	*,
	raw_message: str,
	candidate_payload: Dict[str, Any],
	current_artifact: Dict[str, Any],
	recent_focus: Dict[str, Any],
) -> NBUContextResolutionContract:
	options, source_key = _candidate_options(
		candidate_payload=candidate_payload,
		current_artifact=current_artifact,
		recent_focus=recent_focus,
	)
	if not options:
		return NBUContextResolutionContract(
			status="not_supported",
			target_reference="candidate_list",
			reason="No candidate option list was available for context reference resolution.",
		)
	ordinal_index = _ordinal_reference_index(raw_message)
	if ordinal_index == -2:
		row_index = len(options) - 1
	elif ordinal_index >= 0 and ordinal_index < len(options):
		row_index = ordinal_index
	elif ordinal_index >= len(options):
		return NBUContextResolutionContract(
			status="out_of_range",
			target_reference="candidate_list",
			ambiguity_options=[_clean_text(_row_entity_payload(row, current_artifact, candidate_payload).get("entity_label")) for row in options[:10]],
			reason=f"Requested option {ordinal_index + 1}, but only {len(options)} option(s) are available.",
		)
	else:
		return NBUContextResolutionContract(
			status="ambiguous",
			target_reference="candidate_list",
			ambiguity_options=[_clean_text(_row_entity_payload(row, current_artifact, candidate_payload).get("entity_label")) for row in options[:10]],
			reason="The candidate list exists, but no unique option was selected.",
		)
	return _resolved_contract(
		target_reference="candidate_list",
		artifact_payload=current_artifact,
		recent_focus=recent_focus,
		candidate_payload=candidate_payload,
		rows=options,
		row_index=row_index,
		reason=f"Resolved option {row_index + 1} from {source_key}.",
	)


def resolve_nbu_context_reference(
	*,
	raw_message: str,
	candidate_payload: Dict[str, Any] | None = None,
	current_artifact: Dict[str, Any] | None = None,
	recent_focus: Dict[str, Any] | None = None,
) -> NBUContextResolutionContract:
	"""Resolve natural follow-up references against governed context.

	This resolver is intentionally generic. It does not choose a business family
	or execute a route; it only proves whether a natural reference such as
	"rank 2", "the first customer", "that item", or "the second option" can be
	grounded to a visible artifact row or candidate option.
	"""

	candidate = _clean_dict(candidate_payload)
	artifact = _clean_dict(current_artifact)
	focus = _clean_dict(recent_focus)
	target_reference = _clean_text(candidate.get("target_reference")).lower() or "none"
	if target_reference not in {
		"current_artifact",
		"previous_artifact",
		"rank_n",
		"named_entity",
		"selected_entity",
		"candidate_list",
		"unclear",
	}:
		target_reference = "none"

	if target_reference == "candidate_list":
		return _resolve_from_candidate_options(
			raw_message=raw_message,
			candidate_payload=candidate,
			current_artifact=artifact,
			recent_focus=focus,
		)

	target_entity = _clean_dict(candidate.get("target_entity"))
	if target_reference in {"named_entity", "selected_entity"} and target_entity:
		return NBUContextResolutionContract(
			status="resolved",
			target_reference=target_reference,
			resolved_artifact_id=_artifact_id(artifact, focus),
			resolved_entity={key: value for key, value in target_entity.items() if value not in ("", {}, [])},
			reason="Resolved directly from the selected NBU target entity.",
		)

	if target_reference == "previous_artifact":
		focus_resolution = _resolve_from_recent_focus(
			target_reference=target_reference,
			recent_focus=focus,
		)
		if focus_resolution.status == "resolved":
			return focus_resolution

	if target_reference in {"current_artifact", "previous_artifact", "rank_n", "named_entity", "selected_entity"}:
		return _resolve_from_rows(
			raw_message=raw_message,
			target_reference=target_reference,
			candidate_payload=candidate,
			current_artifact=artifact,
			recent_focus=focus,
		)

	if target_reference == "unclear":
		return NBUContextResolutionContract(
			status="ambiguous",
			target_reference="unclear",
			reason="The selected NBU candidate marked the target reference as unclear.",
		)

	return NBUContextResolutionContract(
		status="not_evaluated",
		target_reference=target_reference,
		reason="No context reference resolution was required for this candidate.",
	)
