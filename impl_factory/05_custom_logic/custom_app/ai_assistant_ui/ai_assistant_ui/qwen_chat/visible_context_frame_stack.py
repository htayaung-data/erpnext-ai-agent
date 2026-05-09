from __future__ import annotations

import json
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


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


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


def _artifact_frame(
	*,
	artifact: Dict[str, Any],
	authority_rank: int,
	role: str,
) -> Dict[str, Any]:
	rows, row_source = nbu_artifact_rows(artifact)
	identity = visible_context_payload_identity(artifact)
	return {
		"frame_id": f"{identity or 'artifact'}:table:{authority_rank}",
		"frame_kind": "table" if rows else "artifact",
		"authority_rank": authority_rank,
		"role": role,
		"artifact_id": identity,
		"family_id": _clean_text(artifact.get("family_id") or artifact.get("family") or artifact.get("composite_family_id")),
		"capability_id": _clean_text(artifact.get("capability_id") or artifact.get("source_capability_id")),
		"artifact_title": _artifact_title(artifact),
		"business_object_type": _business_object_type(artifact, rows),
		"row_source": _clean_text(row_source),
		"visible_row_count": len(rows),
		"requested_limit": _requested_limit(artifact, rows),
		"columns": _columns(rows),
		"rows": _frame_rows(rows, artifact),
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
