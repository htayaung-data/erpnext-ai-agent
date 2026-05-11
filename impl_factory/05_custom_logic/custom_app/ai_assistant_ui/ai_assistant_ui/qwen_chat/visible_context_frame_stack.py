from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_row_entity_payload,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_visible_artifacts import visible_artifacts_from_assistant_text
from .metadata import ontology_detect_concepts


VISIBLE_CONTEXT_FRAME_STACK_VERSION = "1.0"

ARTIFACT_PAYLOAD_TYPES = {
	"qwen_normalized_family_artifact_contract",
	"qwen_composite_family_artifact",
	"qwen_entity_detail_artifact",
	"qwen_visible_rendered_artifact",
}
LOW_PRIORITY_ROW_SOURCES = {"sections.parties", "sections.party_rows"}
FRAME_RELATION_PREVIOUS_TERMS = {"previous", "prior", "earlier", "back"}
FRAME_RELATION_SAME_TERMS = {"same"}
FRAME_RELATION_PARENT_TERMS = {"parent", "origin"}
FRAME_RELATION_DETAIL_TERMS = {"detail", "details", "breakdown", "invoice", "document", "source"}
DOCUMENT_OBJECT_TYPES = {
	"document",
	"invoice",
	"sales_invoice",
	"purchase_invoice",
	"delivery_note",
	"voucher",
	"stock_entry",
	"payment_entry",
}
REQUEST_OBJECT_ALIAS_GROUPS: List[Tuple[str, set[str]]] = [
	("purchase_invoice", {"purchase invoice", "purchase invoices", "pinv", "purchase bill", "purchase bills"}),
	("sales_invoice", {"sales invoice", "sales invoices", "sinv"}),
	("invoice", {"invoice", "invoices", "bill", "bills"}),
	("delivery_note", {"delivery note", "delivery notes", "dn"}),
	("stock_entry", {"stock entry", "stock entries"}),
	("payment_entry", {"payment entry", "payment entries", "payment", "payments"}),
	("document", {"document", "documents", "source document", "source documents", "voucher", "vouchers"}),
	("supplier", {"supplier", "suppliers", "vendor", "vendors"}),
	("customer", {"customer", "customers", "party", "parties"}),
	("item", {"item", "items", "product", "products"}),
	("account", {"account", "accounts", "line", "lines"}),
]


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


def _normalize(value: Any) -> str:
	text = _clean_text(value).lower().replace("_", " ")
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def _tokens(value: Any) -> set[str]:
	return {token for token in _normalize(value).split() if token}


def _terms(value: Any) -> set[str]:
	normalized = _normalize(value)
	if not normalized:
		return set()
	token_list = [token for token in normalized.split() if token]
	terms = set(token_list)
	for size in range(2, min(4, len(token_list)) + 1):
		for index in range(0, len(token_list) - size + 1):
			terms.add(" ".join(token_list[index : index + size]))
	terms.add(normalized)
	return terms


def _plural(value: str) -> str:
	clean = _normalize(value)
	if not clean:
		return ""
	if clean.endswith("y"):
		return f"{clean[:-1]}ies"
	if clean.endswith("s"):
		return clean
	return f"{clean}s"


def _positive_int(value: Any) -> int:
	try:
		return max(0, int(value or 0))
	except (TypeError, ValueError):
		return 0


def _safe_json_loads(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	try:
		payload = json.loads(_clean_text(value))
	except Exception:
		return {}
	return dict(payload) if isinstance(payload, dict) else {}


def _session_messages(session_doc: Any) -> List[Any]:
	if isinstance(session_doc, dict):
		values = session_doc.get("messages", [])
	else:
		values = getattr(session_doc, "messages", [])
	try:
		return list(values or [])
	except Exception:
		return []


def _message_role(message: Any) -> str:
	return _clean_text(getattr(message, "role", "") or (message.get("role") if isinstance(message, dict) else "")).lower()


def _message_content(message: Any) -> Any:
	content = getattr(message, "content", None)
	if content is None and isinstance(message, dict):
		content = message.get("content")
	return content


def _assistant_text_from_content(content: Any) -> str:
	text = _clean_text(content)
	if not text:
		return ""
	payload = _safe_json_loads(text)
	if payload:
		return _clean_text(payload.get("text") or payload.get("message") or payload.get("content"))
	return text


def visible_context_payload_identity(payload: Dict[str, Any]) -> str:
	payload = _clean_dict(payload)
	for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
		value = _clean_text(payload.get(key))
		if value:
			return value
	return _clean_text(payload.get("title") or payload.get("report_name") or payload.get("family_id"))


def _section_key_for_business_object_type(value: Any) -> str:
	object_type = _normalize(value)
	if object_type in {"customer", "customers", "party", "parties"}:
		return "top_customers"
	if object_type in {"supplier", "suppliers", "vendor", "vendors"}:
		return "top_suppliers"
	if object_type in {"item", "items", "product", "products"}:
		return "top_items"
	if object_type in DOCUMENT_OBJECT_TYPES:
		return "documents"
	return "rows"


def _artifact_from_trace_frame(frame: Dict[str, Any], trace_payload: Dict[str, Any], *, fallback_index: int) -> Dict[str, Any]:
	clean_frame = _clean_dict(frame)
	frame_rows = _clean_list(clean_frame.get("rows"))
	rows = [
		_clean_dict(_clean_dict(row).get("values"))
		for row in frame_rows
		if _clean_dict(_clean_dict(row).get("values"))
	]
	if not rows:
		return {}
	object_type = _clean_text(clean_frame.get("business_object_type"))
	artifact_id = _clean_text(clean_frame.get("artifact_id") or clean_frame.get("frame_id"))
	if not artifact_id:
		artifact_id = f"visible-trace-{_clean_text(trace_payload.get('request_id')) or fallback_index}"
	return {
		"type": "qwen_visible_rendered_artifact",
		"schema_version": VISIBLE_CONTEXT_FRAME_STACK_VERSION,
		"artifact_id": artifact_id,
		"title": _clean_text(clean_frame.get("artifact_title") or clean_frame.get("family_id") or artifact_id),
		"report_title": _clean_text(clean_frame.get("artifact_title") or clean_frame.get("family_id") or artifact_id),
		"family_id": _clean_text(clean_frame.get("family_id")),
		"dimensions": {
			key: value
			for key, value in {
				"entity_dimension": object_type,
				"business_object_type": object_type,
				"source": "visible_context_trace_frame",
			}.items()
			if value
		},
		"sections": {_section_key_for_business_object_type(object_type): rows},
		"source": "visible_context_trace_frame",
	}


def _trace_frame_artifacts(payload: Dict[str, Any], *, fallback_index: int) -> List[Dict[str, Any]]:
	trace = _clean_dict(payload)
	if _clean_text(trace.get("type")).lower() != "qwen_visible_context_followup_trace_contract":
		return []
	frame_stack = _clean_dict(trace.get("context_frame_stack"))
	frames = [
		_clean_dict(frame)
		for frame in _clean_list(frame_stack.get("frames"))
		if _clean_text(_clean_dict(frame).get("frame_kind")).lower() == "table"
	]
	if not frames:
		return []
	arbitration = _clean_dict(trace.get("frame_arbitration"))
	selected_frame_id = _clean_text(arbitration.get("selected_frame_id"))
	if selected_frame_id:
		frames = sorted(frames, key=lambda frame: 0 if _clean_text(frame.get("frame_id")) == selected_frame_id else 1)
	artifacts = [_artifact_from_trace_frame(frames[0], trace, fallback_index=fallback_index)]
	return [artifact for artifact in artifacts if artifact]


def _session_visible_artifacts_with_trace(session_doc: Any, *, limit: int = 8) -> List[Dict[str, Any]]:
	candidates: List[Tuple[str, Dict[str, Any]]] = []
	for offset, message in enumerate(reversed(_session_messages(session_doc)), start=1):
		role = _message_role(message)
		if role == "assistant":
			for artifact in visible_artifacts_from_assistant_text(
					_assistant_text_from_content(_message_content(message)),
					artifact_id=f"visible-assistant-{offset}",
			):
				candidates.append(("assistant", artifact))
		elif role == "tool":
			for artifact in _trace_frame_artifacts(_safe_json_loads(_message_content(message)), fallback_index=offset):
				candidates.append(("trace", artifact))
		if len(candidates) >= limit * 2:
			break
	assistant_artifacts = [artifact for source, artifact in candidates if source == "assistant"]
	artifacts: List[Dict[str, Any]] = []
	for source, artifact in candidates:
		if source == "trace" and _equivalent_artifact_available(artifact, assistant_artifacts):
			continue
		artifacts.append(artifact)
		if len(artifacts) >= limit:
			break
	return artifacts


def _has_rows(payload: Dict[str, Any]) -> bool:
	rows, _source = nbu_artifact_rows(_clean_dict(payload))
	return bool(rows)


def _artifact_row_signature(payload: Dict[str, Any]) -> Tuple[str, ...]:
	rows, _source = nbu_artifact_rows(_clean_dict(payload))
	signature: List[str] = []
	for row in rows[:8]:
		entity = nbu_row_entity_payload(_clean_dict(row), _clean_dict(payload), {})
		label = _normalize(entity.get("entity_label") or entity.get("entity_key"))
		if label:
			signature.append(label)
	return tuple(signature)


def _equivalent_artifact_available(candidate: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> bool:
	candidate_signature = _artifact_row_signature(candidate)
	if not candidate_signature:
		return False
	for artifact in artifacts:
		if _artifact_row_signature(_clean_dict(artifact)) == candidate_signature:
			return True
	return False


def _row_source(payload: Dict[str, Any]) -> str:
	_rows, source = nbu_artifact_rows(_clean_dict(payload))
	return _clean_text(source)


def _session_tool_artifact_groups(session_doc: Any, *, limit: int = 8) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
	primary_typed_artifacts: List[Dict[str, Any]] = []
	secondary_typed_artifacts: List[Dict[str, Any]] = []
	fallback_artifacts: List[Dict[str, Any]] = []
	scanned = 0
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		scanned += 1
		payload = _safe_json_loads(_message_content(message))
		payload_type = _clean_text(payload.get("type")).lower()
		if not _has_rows(payload):
			continue
		if payload_type in ARTIFACT_PAYLOAD_TYPES:
			if _row_source(payload) in LOW_PRIORITY_ROW_SOURCES:
				secondary_typed_artifacts.append(payload)
			else:
				primary_typed_artifacts.append(payload)
		else:
			fallback_artifacts.append(payload)
		if len(primary_typed_artifacts) >= limit:
			break
		if scanned >= limit * 4 and (primary_typed_artifacts or secondary_typed_artifacts):
			break
	return (
		primary_typed_artifacts[:limit],
		secondary_typed_artifacts[:limit],
		fallback_artifacts[:limit],
	)


def visible_context_artifacts(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any] | None = None,
	limit: int = 8,
) -> List[Dict[str, Any]]:
	artifacts: List[Dict[str, Any]] = []
	seen: set[str] = set()

	def append(payload: Dict[str, Any]) -> None:
		if len(artifacts) >= limit:
			return
		clean_payload = _clean_dict(payload)
		if not clean_payload or not _has_rows(clean_payload):
			return
		identity = visible_context_payload_identity(clean_payload)
		if identity and identity in seen:
			return
		if identity:
			seen.add(identity)
		artifacts.append(clean_payload)

	for payload in _session_visible_artifacts_with_trace(session_doc, limit=limit):
		append(payload)
	primary_tool_artifacts, secondary_tool_artifacts, fallback_tool_artifacts = _session_tool_artifact_groups(session_doc, limit=limit)
	for payload in primary_tool_artifacts:
		append(payload)
	for payload in secondary_tool_artifacts:
		append(payload)
	for payload in fallback_tool_artifacts:
		append(payload)
	append(_clean_dict(current_artifact))
	return artifacts


def _artifact_title(artifact: Dict[str, Any]) -> str:
	for key in ("title", "report_title", "report_name", "label", "family_label"):
		value = _clean_text(artifact.get(key))
		if value:
			return value
	return _clean_text(artifact.get("family_id") or artifact.get("family") or artifact.get("type"))


def _business_object_type(artifact: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
	dimensions = _clean_dict(artifact.get("dimensions"))
	for key in ("entity_dimension", "entity_type", "business_object_type", "row_type"):
		value = _clean_text(dimensions.get(key) or artifact.get(key))
		if value:
			return value.lower()
	for row in rows[:5]:
		entity = nbu_row_entity_payload(_clean_dict(row), artifact, {})
		value = _clean_text(entity.get("entity_type"))
		if value:
			return value.lower()
	for row in rows[:5]:
		clean_row = _clean_dict(row)
		for key in ("customer", "supplier", "party", "item", "product", "warehouse", "invoice"):
			if _clean_text(clean_row.get(key)):
				return key
	return ""


def _requested_limit(artifact: Dict[str, Any], rows: List[Dict[str, Any]]) -> int:
	for source in (artifact, _clean_dict(artifact.get("metadata")), _clean_dict(artifact.get("dimensions"))):
		for key in ("requested_limit", "limit", "top_n", "row_limit", "visible_limit"):
			value = _positive_int(source.get(key))
			if value:
				return value
	return len(rows)


def _evidence_scope(artifact: Dict[str, Any]) -> str:
	if _clean_text(artifact.get("source")).lower() in {"assistant_visible_markdown", "visible_context_trace_frame"}:
		return "visible_rendered_table"
	if artifact.get("source_detail_drilldown"):
		return "approved_source_detail"
	if _clean_text(artifact.get("family_id")).lower() == "entity_detail":
		return "approved_detail"
	return "governed_artifact"


def _columns(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
	ordered: List[str] = []
	for row in rows[:10]:
		for key in _clean_dict(row).keys():
			if key and key not in ordered:
				ordered.append(str(key))
	return [{"key": key, "label": key.replace("_", " ").title()} for key in ordered[:20]]


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position", "idx", "index"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _frame_rows(rows: List[Dict[str, Any]], artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
	frame_rows: List[Dict[str, Any]] = []
	for index, row in enumerate(rows):
		clean_row = _clean_dict(row)
		entity = nbu_row_entity_payload(clean_row, artifact, {})
		object_type = _clean_text(entity.get("entity_type")).lower()
		if not object_type:
			for key in ("customer", "supplier", "party", "item", "product", "warehouse", "invoice"):
				if _clean_text(clean_row.get(key)):
					object_type = key
					break
		frame_rows.append(
			{
				"row_index": index,
				"rank": _row_rank(clean_row, index),
				"label": _clean_text(entity.get("entity_label") or entity.get("entity_key")),
				"business_object_type": object_type,
				"values": clean_row,
			}
		)
	return frame_rows


def _row_business_object_types(frame_rows: List[Dict[str, Any]]) -> List[str]:
	values: List[str] = []
	for row in frame_rows:
		value = _clean_text(_clean_dict(row).get("business_object_type")).lower()
		if value and value not in values:
			values.append(value)
	return values


def _artifact_frame(
	*,
	artifact: Dict[str, Any],
	authority_rank: int,
	role: str,
) -> Dict[str, Any]:
	rows, row_source = nbu_artifact_rows(artifact)
	identity = visible_context_payload_identity(artifact)
	frame_rows = _frame_rows(rows, artifact)
	object_type = _business_object_type(artifact, rows)
	row_object_types = _row_business_object_types(frame_rows)
	return {
		"frame_id": f"{identity or 'artifact'}:table:{authority_rank}",
		"frame_kind": "table" if rows else "artifact",
		"authority_rank": authority_rank,
		"role": role,
		"artifact_id": identity,
		"family_id": _clean_text(artifact.get("family_id") or artifact.get("family") or artifact.get("composite_family_id")),
		"capability_id": _clean_text(artifact.get("capability_id") or artifact.get("source_capability_id")),
		"artifact_title": _artifact_title(artifact),
		"business_object_type": object_type,
		"row_business_object_types": row_object_types,
		"row_source": _clean_text(row_source),
		"visible_row_count": len(rows),
		"requested_limit": _requested_limit(artifact, rows),
		"columns": _columns(rows),
		"rows": frame_rows,
		"parent_artifact_id": _clean_text(artifact.get("parent_artifact_id") or artifact.get("source_artifact_id")),
		"evidence_scope": _evidence_scope(artifact),
	}


def _selection_frame(selected_entity: Dict[str, Any] | None) -> Dict[str, Any]:
	entity = _clean_dict(selected_entity)
	row = _clean_dict(entity.get("row"))
	label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
	if not label:
		return {}
	try:
		rank = int(entity.get("rank") or row.get("rank") or 0)
	except (TypeError, ValueError):
		rank = 0
	return {
		"frame_id": f"selected:{label}",
		"frame_kind": "selection",
		"authority_rank": -1,
		"role": "recent_selection",
		"artifact_id": _clean_text(entity.get("artifact_id") or entity.get("resolved_artifact_id")),
		"business_object_type": _clean_text(entity.get("entity_type")).lower(),
		"row_business_object_types": [_clean_text(entity.get("entity_type")).lower()] if _clean_text(entity.get("entity_type")) else [],
		"visible_row_count": 1,
		"requested_limit": 1,
		"rows": [
			{
				"row_index": 0,
				"rank": rank,
				"label": label,
				"business_object_type": _clean_text(entity.get("entity_type")).lower(),
				"values": row,
			}
		],
		"evidence_scope": "selected_visible_row",
	}


def _table_frames(frame_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
	return [
		_clean_dict(frame)
		for frame in _clean_list(_clean_dict(frame_stack).get("frames"))
		if _clean_text(_clean_dict(frame).get("frame_kind")) == "table"
	]


def _frame_object_aliases(frame: Dict[str, Any]) -> set[str]:
	values = {
		_clean_text(frame.get("business_object_type")).lower(),
		*[
			_clean_text(value).lower()
			for value in _clean_list(frame.get("row_business_object_types"))
			if _clean_text(value)
		],
	}
	aliases: set[str] = set()
	for value in values:
		normalized = _normalize(value)
		if not normalized:
			continue
		aliases.add(normalized)
		aliases.add(_plural(normalized))
		aliases.update(token for token in normalized.split() if token)
	aliases.update(_frame_contextual_object_aliases(frame, aliases))
	return {alias for alias in aliases if alias}


def _frame_contract_terms(frame: Dict[str, Any]) -> set[str]:
	terms: set[str] = set()
	for key in ("family_id", "capability_id", "artifact_title", "row_source"):
		terms.update(_terms(frame.get(key)))
	return terms


def _frame_contextual_object_aliases(frame: Dict[str, Any], base_aliases: set[str]) -> set[str]:
	"""Infer object labels from governed frame context, not from user wording.

	Some rendered consultant tables intentionally show a neutral Party column.
	The table frame still carries family/capability/title context, so the
	resolver can expose customer/supplier aliases without hardcoding a single
	report path.
	"""

	contract_terms = _frame_contract_terms(frame)
	if not {"party", "parties"}.intersection(base_aliases):
		return set()
	if {"receivable", "accounts receivable"}.intersection(contract_terms):
		return {"customer", "customers"}
	if {"payable", "accounts payable"}.intersection(contract_terms):
		return {"supplier", "suppliers"}
	return set()


def _message_parts(raw_message: str) -> set[str]:
	parts = set(_tokens(raw_message))
	token_list = [token for token in _normalize(raw_message).split() if token]
	for size in range(2, min(4, len(token_list)) + 1):
		for index in range(0, len(token_list) - size + 1):
			parts.add(" ".join(token_list[index : index + size]))
	return parts


def _frame_matches_message_object(raw_message: str, frame: Dict[str, Any]) -> bool:
	return bool(_message_parts(raw_message).intersection(_frame_object_aliases(frame)))


def _requested_object_aliases(raw_message: str) -> set[str]:
	parts = _message_parts(raw_message)
	for canonical, aliases in REQUEST_OBJECT_ALIAS_GROUPS:
		normalized_aliases = {_normalize(alias) for alias in aliases if _normalize(alias)}
		if parts.intersection(normalized_aliases):
			return {
				_normalize(canonical),
				_plural(_normalize(canonical)),
				*normalized_aliases,
			}
	return set()


def _requested_object_label(raw_message: str) -> str:
	parts = _message_parts(raw_message)
	for canonical, aliases in REQUEST_OBJECT_ALIAS_GROUPS:
		normalized_aliases = {_normalize(alias) for alias in aliases if _normalize(alias)}
		if parts.intersection(normalized_aliases):
			return _normalize(canonical).replace("_", " ")
	return ""


def _frame_matches_requested_object(frame: Dict[str, Any], requested_aliases: set[str]) -> bool:
	if not requested_aliases:
		return False
	return bool(requested_aliases.intersection(_frame_object_aliases(frame)))


def _missing_requested_object_result(
	*,
	relation: str,
	requested_aliases: set[str],
	requested_label: str,
	frames: List[Dict[str, Any]],
) -> Dict[str, Any]:
	available_types: List[str] = []
	available_labels: List[str] = []
	for frame in frames:
		object_type = _clean_text(frame.get("business_object_type"))
		if object_type and object_type not in available_types:
			available_types.append(object_type)
		label = _clean_text(frame.get("artifact_title") or frame.get("family_id") or frame.get("artifact_id"))
		if label and label not in available_labels:
			available_labels.append(label)
	return {
		"status": "missing_requested_object",
		"relation": relation,
		"requested_object_label": _clean_text(requested_label),
		"requested_object_aliases": sorted(requested_aliases),
		"available_business_object_types": available_types[:8],
		"available_table_labels": available_labels[:8],
		"reason": "The requested object type is not present in the authoritative visible table frames.",
	}


def _semantic_concept_terms(raw_message: str) -> set[str]:
	terms: set[str] = set()
	for concept in ontology_detect_concepts(raw_message):
		terms.update(_terms(concept))
	return terms


def _frame_matches_semantic_concepts(raw_message: str, frame: Dict[str, Any]) -> bool:
	concept_terms = _semantic_concept_terms(raw_message)
	if not concept_terms:
		return False
	return bool(concept_terms.intersection(_frame_contract_terms(frame)))


def _is_detail_frame(frame: Dict[str, Any]) -> bool:
	evidence_scope = _clean_text(frame.get("evidence_scope")).lower()
	object_types = {
		_clean_text(frame.get("business_object_type")).lower(),
		*[
			_clean_text(value).lower()
			for value in _clean_list(frame.get("row_business_object_types"))
			if _clean_text(value)
		],
	}
	return (
		evidence_scope in {"approved_source_detail", "approved_detail"}
		or bool(object_types.intersection(DOCUMENT_OBJECT_TYPES))
	)


def resolve_visible_context_frame_arbitration(
	*,
	raw_message: str,
	frame_stack: Dict[str, Any],
) -> Dict[str, Any]:
	"""Select the authoritative table frame for a contextual follow-up.

	This is intentionally family-neutral: it uses the frame relation requested
	by the user plus object types emitted by governed artifacts.
	"""

	frames = _table_frames(frame_stack)
	if not frames:
		return {"status": "not_evaluated", "reason": "No table frames are available."}
	tokens = _tokens(raw_message)
	requested_object_aliases = _requested_object_aliases(raw_message)
	requested_object_label = _requested_object_label(raw_message)
	matching_object_frames = (
		[frame for frame in frames if _frame_matches_requested_object(frame, requested_object_aliases)]
		if requested_object_aliases
		else [frame for frame in frames if _frame_matches_message_object(raw_message, frame)]
	)
	semantic_context_frames = [
		frame
		for frame in frames
		if not _is_detail_frame(frame)
		and _frame_matches_semantic_concepts(raw_message, frame)
		and frame not in matching_object_frames
	]
	matching_business_frames = matching_object_frames or semantic_context_frames
	relation = "current_table"
	if tokens.intersection(FRAME_RELATION_PARENT_TERMS):
		relation = "parent_table"
	elif tokens.intersection(FRAME_RELATION_PREVIOUS_TERMS):
		relation = "previous_table"
	elif tokens.intersection(FRAME_RELATION_SAME_TERMS):
		relation = "same_table"
	elif tokens.intersection(FRAME_RELATION_DETAIL_TERMS):
		relation = "detail_table"

	selected_frame: Dict[str, Any] = {}
	if relation == "parent_table":
		candidates = matching_business_frames or [frame for frame in frames[1:] if not _is_detail_frame(frame)]
		if not candidates:
			candidates = frames[1:]
		selected_frame = candidates[0] if candidates else {}
	elif relation == "previous_table":
		previous_frames = frames[1:]
		candidates = [frame for frame in previous_frames if _frame_matches_message_object(raw_message, frame)]
		selected_frame = (candidates or previous_frames or frames)[0]
	elif relation == "same_table":
		selected_frame = frames[0]
	elif relation == "detail_table":
		detail_frames = [frame for frame in frames if _is_detail_frame(frame)]
		candidates = (
			[frame for frame in detail_frames if _frame_matches_requested_object(frame, requested_object_aliases)]
			if requested_object_aliases
			else [frame for frame in detail_frames if _frame_matches_message_object(raw_message, frame)]
		)
		if requested_object_aliases and not candidates:
			return _missing_requested_object_result(
				relation=relation,
				requested_aliases=requested_object_aliases,
				requested_label=requested_object_label,
				frames=detail_frames or frames,
			)
		selected_frame = (candidates or detail_frames or matching_business_frames or frames)[0]
	else:
		current_frame = frames[0]
		if requested_object_aliases and not _frame_matches_requested_object(current_frame, requested_object_aliases):
			if matching_business_frames:
				selected_frame = matching_business_frames[0]
			else:
				return _missing_requested_object_result(
					relation=relation,
					requested_aliases=requested_object_aliases,
					requested_label=requested_object_label,
					frames=frames,
				)
		elif _is_detail_frame(current_frame) and matching_business_frames:
			selected_frame = matching_business_frames[0]
		else:
			selected_frame = current_frame

	if not selected_frame:
		return {
			"status": "not_evaluated",
			"relation": relation,
			"reason": "No compatible context frame was selected.",
		}
	return {
		"status": "resolved",
		"relation": relation,
		"selected_frame_id": _clean_text(selected_frame.get("frame_id")),
		"selected_artifact_id": _clean_text(selected_frame.get("artifact_id")),
		"selected_business_object_type": _clean_text(selected_frame.get("business_object_type")),
		"selected_evidence_scope": _clean_text(selected_frame.get("evidence_scope")),
		"selected_visible_row_count": _positive_int(selected_frame.get("visible_row_count")),
		"reason": "Resolved the authoritative visible table frame from the shared frame stack.",
	}


def build_visible_context_frame_stack(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any] | None = None,
	selected_entity: Dict[str, Any] | None = None,
	limit: int = 8,
) -> Dict[str, Any]:
	artifacts = visible_context_artifacts(
		session_doc,
		current_artifact=_clean_dict(current_artifact),
		limit=limit,
	)
	frames: List[Dict[str, Any]] = []
	selection = _selection_frame(selected_entity)
	if selection:
		frames.append(selection)
	for index, artifact in enumerate(artifacts):
		frames.append(
			_artifact_frame(
				artifact=_clean_dict(artifact),
				authority_rank=index,
				role="current" if index == 0 else "previous",
			)
		)
	return {
		"type": "qwen_visible_context_frame_stack_contract",
		"contract_version": CONTRACT_VERSION,
		"schema_version": VISIBLE_CONTEXT_FRAME_STACK_VERSION,
		"artifact_count": len(artifacts),
		"frame_count": len(frames),
		"frames": frames,
	}
