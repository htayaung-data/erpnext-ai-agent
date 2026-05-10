from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_row_entity_payload,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_visible_artifacts import session_visible_rendered_artifacts


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


def visible_context_payload_identity(payload: Dict[str, Any]) -> str:
	payload = _clean_dict(payload)
	for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
		value = _clean_text(payload.get(key))
		if value:
			return value
	return _clean_text(payload.get("title") or payload.get("report_name") or payload.get("family_id"))


def _has_rows(payload: Dict[str, Any]) -> bool:
	rows, _source = nbu_artifact_rows(_clean_dict(payload))
	return bool(rows)


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

	for payload in session_visible_rendered_artifacts(session_doc, limit=limit):
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
	return ""


def _requested_limit(artifact: Dict[str, Any], rows: List[Dict[str, Any]]) -> int:
	for source in (artifact, _clean_dict(artifact.get("metadata")), _clean_dict(artifact.get("dimensions"))):
		for key in ("requested_limit", "limit", "top_n", "row_limit", "visible_limit"):
			value = _positive_int(source.get(key))
			if value:
				return value
	return len(rows)


def _evidence_scope(artifact: Dict[str, Any]) -> str:
	if _clean_text(artifact.get("source")).lower() == "assistant_visible_markdown":
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
		frame_rows.append(
			{
				"row_index": index,
				"rank": _row_rank(clean_row, index),
				"label": _clean_text(entity.get("entity_label") or entity.get("entity_key")),
				"business_object_type": _clean_text(entity.get("entity_type")).lower(),
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
	return {alias for alias in aliases if alias}


def _frame_matches_message_object(raw_message: str, frame: Dict[str, Any]) -> bool:
	tokens = _tokens(raw_message)
	parts = set(tokens)
	token_list = [token for token in _normalize(raw_message).split() if token]
	for size in range(2, min(4, len(token_list)) + 1):
		for index in range(0, len(token_list) - size + 1):
			parts.add(" ".join(token_list[index : index + size]))
	return bool(parts.intersection(_frame_object_aliases(frame)))


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
	matching_object_frames = [frame for frame in frames if _frame_matches_message_object(raw_message, frame)]
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
		candidates = matching_object_frames or [frame for frame in frames[1:] if not _is_detail_frame(frame)]
		if not candidates:
			candidates = frames[1:]
		selected_frame = candidates[0] if candidates else {}
	elif relation == "previous_table":
		previous_frames = frames[1:]
		candidates = [frame for frame in previous_frames if _frame_matches_message_object(raw_message, frame)]
		selected_frame = (candidates or previous_frames or frames)[0]
	elif relation == "same_table":
		if matching_object_frames and matching_object_frames[0].get("artifact_id") != frames[0].get("artifact_id"):
			selected_frame = matching_object_frames[0]
		else:
			selected_frame = frames[0]
	elif relation == "detail_table":
		detail_frames = [frame for frame in frames if _is_detail_frame(frame)]
		candidates = [frame for frame in detail_frames if _frame_matches_message_object(raw_message, frame)]
		selected_frame = (candidates or detail_frames or matching_object_frames or frames)[0]
	else:
		current_frame = frames[0]
		if _is_detail_frame(current_frame) and matching_object_frames:
			selected_frame = matching_object_frames[0]
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
