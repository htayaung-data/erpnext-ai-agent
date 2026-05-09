from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_ordinal_reference_index,
	nbu_row_entity_payload,
	nbu_row_identity_alias_values,
	resolve_nbu_context_reference,
)
from .natural_business_understanding_contracts import NBUContextResolutionContract


NBU_CONTEXT_GRAPH_VERSION = "1.0"

NBU_CONTEXT_GRAPH_NODE_TYPES: List[Dict[str, str]] = [
	{"node_type": "artifact", "meaning": "A current or prior governed result that can hold rows or summary facts."},
	{"node_type": "row", "meaning": "A visible row inside an artifact, optionally with rank or position."},
	{"node_type": "entity", "meaning": "A business entity resolved from a visible row or focus payload."},
	{"node_type": "focus", "meaning": "A recent selected entity, statement, document, or detail focus."},
	{"node_type": "candidate_option", "meaning": "A disambiguation option from an NBU candidate list."},
]

DISCOURSE_PREVIOUS_TERMS = {"above", "previous", "prior", "earlier", "back"}
DISCOURSE_EXPLICIT_PREVIOUS_TERMS = {"previous", "prior", "earlier", "back"}
DISCOURSE_CURRENT_TERMS = {"current", "latest", "last", "this", "shown", "above"}
DEICTIC_ENTITY_TERMS = {"that", "this", "it", "selected", "same"}
GENERIC_CONTEXT_ALIAS_TERMS = (
	DISCOURSE_PREVIOUS_TERMS
	| DISCOURSE_CURRENT_TERMS
	| DEICTIC_ENTITY_TERMS
	| {
		"a",
		"an",
		"and",
		"answer",
		"are",
		"as",
		"at",
		"based",
		"by",
		"entry",
		"for",
		"from",
		"give",
		"here",
		"in",
		"is",
		"me",
		"of",
		"on",
		"or",
		"please",
		"position",
		"rank",
		"row",
		"rows",
		"table",
		"tell",
		"the",
		"to",
		"visible",
		"what",
		"which",
		"who",
		"with",
	}
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([_clean_text(value) for value in values if _clean_text(value)]))


def _normalize(value: Any) -> str:
	text = _clean_text(value).lower().replace("_", " ")
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def _tokens(value: Any) -> List[str]:
	return [token for token in _normalize(value).split() if token]


def _window_acronyms(tokens: List[str]) -> List[str]:
	acronyms: List[str] = []
	for size in range(2, min(4, len(tokens)) + 1):
		for index in range(0, len(tokens) - size + 1):
			acronym = "".join(token[0] for token in tokens[index : index + size] if token)
			if len(acronym) >= 2:
				acronyms.append(acronym)
	return acronyms


def _aliases(*values: Any) -> List[str]:
	aliases: List[str] = []
	for value in values:
		normalized = _normalize(value)
		if not normalized:
			continue
		aliases.append(normalized)
		value_tokens = _tokens(normalized)
		aliases.extend(token for token in value_tokens if len(token) >= 2)
		aliases.extend(_window_acronyms(value_tokens))
	return _dedupe(aliases)


def _message_alias_set(raw_message: str) -> set[str]:
	message = _normalize(raw_message)
	parts = set(_tokens(message))
	message_tokens = _tokens(message)
	for size in range(2, min(5, len(message_tokens)) + 1):
		for index in range(0, len(message_tokens) - size + 1):
			parts.add(" ".join(message_tokens[index : index + size]))
	parts.update(_window_acronyms(message_tokens))
	return parts


def _contains_term(raw_message: str, terms: set[str]) -> bool:
	return bool(set(_tokens(raw_message)).intersection(terms))


def _is_generic_context_alias(value: Any) -> bool:
	normalized = _normalize(value)
	return not normalized or normalized.isdigit() or normalized in GENERIC_CONTEXT_ALIAS_TERMS


def _artifact_id(artifact_payload: Dict[str, Any], fallback: str) -> str:
	artifact = _clean_dict(artifact_payload)
	for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
		value = _clean_text(artifact.get(key))
		if value:
			return value
	return fallback


def _artifact_label(artifact_payload: Dict[str, Any]) -> str:
	artifact = _clean_dict(artifact_payload)
	for key in ("title", "report_title", "report_name", "label", "family_label", "family_id", "family"):
		value = _clean_text(artifact.get(key))
		if value:
			return value
	dimensions = _clean_dict(artifact.get("dimensions"))
	for key in ("source_report", "source_composite_family_id", "entity_dimension"):
		value = _clean_text(dimensions.get(key))
		if value:
			return value
	return ""


def _artifact_family(artifact_payload: Dict[str, Any]) -> str:
	artifact = _clean_dict(artifact_payload)
	dimensions = _clean_dict(artifact.get("dimensions"))
	for key in ("family_id", "family", "composite_family_id", "report_name"):
		value = _clean_text(artifact.get(key))
		if value:
			return value
	for key in ("source_composite_family_id", "source_report", "entity_dimension"):
		value = _clean_text(dimensions.get(key))
		if value:
			return value
	return ""


def _artifact_aliases(artifact_payload: Dict[str, Any]) -> List[str]:
	artifact = _clean_dict(artifact_payload)
	dimensions = _clean_dict(artifact.get("dimensions"))
	return _aliases(
		artifact.get("artifact_id"),
		artifact.get("title"),
		artifact.get("report_title"),
		artifact.get("report_name"),
		artifact.get("family_id"),
		artifact.get("family"),
		artifact.get("composite_family_id"),
		dimensions.get("source_composite_family_id"),
		dimensions.get("source_report"),
		dimensions.get("entity_dimension"),
		_artifact_label(artifact),
	)


def _focus_entity_payload(focus_payload: Dict[str, Any]) -> Dict[str, Any]:
	focus = _clean_dict(focus_payload)
	focus_label = _clean_text(focus.get("focus_label"))
	focus_key = _clean_text(focus.get("focus_key")) or focus_label
	focus_grain = _clean_text(focus.get("focus_grain"))
	if not focus_label and not focus_key:
		return {}
	return {
		key: value
		for key, value in {
			"entity_type": focus_grain,
			"entity_key": focus_key,
			"entity_label": focus_label or focus_key,
			"focus_kind": _clean_text(focus.get("focus_kind")),
			"focus_grain": focus_grain,
		}.items()
		if value not in ("", {}, [])
	}


def _candidate_options(candidate_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	candidate = _clean_dict(candidate_payload)
	target_entity = _clean_dict(candidate.get("target_entity"))
	for source in (candidate, target_entity):
		for key in ("candidate_options", "possible_matches", "matching_options", "clarification_options", "options", "choices"):
			value = source.get(key)
			if isinstance(value, list):
				return [dict(row) if isinstance(row, dict) else {"entity": _clean_text(row)} for row in value if row]
	return []


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position", "idx", "index"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _artifact_node(artifact_payload: Dict[str, Any], *, role: str, recency_index: int) -> Dict[str, Any]:
	artifact = _clean_dict(artifact_payload)
	node_id = _artifact_id(artifact, f"{role}-artifact-{recency_index}")
	return {
		"node_id": node_id,
		"node_type": "artifact",
		"role": role,
		"recency_index": recency_index,
		"artifact_id": node_id,
		"family_id": _artifact_family(artifact),
		"label": _artifact_label(artifact),
		"aliases": _artifact_aliases(artifact),
		"payload": artifact,
	}


def _append_artifact_nodes(
	*,
	graph: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	role: str,
	recency_index: int,
) -> None:
	artifact = _clean_dict(artifact_payload)
	if not artifact:
		return
	artifact_node = _artifact_node(artifact, role=role, recency_index=recency_index)
	graph["artifact_nodes"].append(artifact_node)
	graph["nodes"].append({key: value for key, value in artifact_node.items() if key != "payload"})
	rows, source_key = nbu_artifact_rows(artifact)
	for index, row in enumerate(rows):
		row_payload = dict(row)
		row_rank = _row_rank(row_payload, index)
		row_id = f"{artifact_node['artifact_id']}:row:{row_rank}"
		entity = nbu_row_entity_payload(row_payload, artifact, {})
		row_node = {
			"node_id": row_id,
			"node_type": "row",
			"artifact_id": artifact_node["artifact_id"],
			"role": role,
			"recency_index": recency_index,
			"row_index": index,
			"rank": row_rank,
			"source_key": source_key,
			"entity": entity,
			"aliases": _aliases(
				entity.get("entity_label"),
				entity.get("entity_key"),
				entity.get("entity_type"),
				*nbu_row_identity_alias_values(row_payload),
			),
			"row": row_payload,
		}
		graph["row_nodes"].append(row_node)
		graph["nodes"].append({key: value for key, value in row_node.items() if key != "row"})
		if entity:
			entity_node = {
				"node_id": f"{artifact_node['artifact_id']}:entity:{row_rank}",
				"node_type": "entity",
				"artifact_id": artifact_node["artifact_id"],
				"role": role,
				"recency_index": recency_index,
				"row_index": index,
				"rank": row_rank,
				"entity": entity,
				"aliases": row_node["aliases"],
			}
			graph["entity_nodes"].append(entity_node)
			graph["nodes"].append(entity_node)


def build_nbu_context_graph(
	*,
	current_artifact: Dict[str, Any] | None = None,
	previous_artifacts: List[Dict[str, Any]] | None = None,
	recent_focus: Dict[str, Any] | None = None,
	candidate_payloads: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	graph: Dict[str, Any] = {
		"type": "qwen_nbu_context_graph",
		"schema_version": NBU_CONTEXT_GRAPH_VERSION,
		"nodes": [],
		"artifact_nodes": [],
		"row_nodes": [],
		"entity_nodes": [],
		"focus_nodes": [],
		"candidate_option_nodes": [],
	}
	_append_artifact_nodes(
		graph=graph,
		artifact_payload=_clean_dict(current_artifact),
		role="current",
		recency_index=0,
	)
	for index, artifact in enumerate(previous_artifacts or [], start=1):
		_append_artifact_nodes(
			graph=graph,
			artifact_payload=_clean_dict(artifact),
			role="previous",
			recency_index=index,
		)
	focus = _clean_dict(recent_focus)
	focus_entity = _focus_entity_payload(focus)
	if focus_entity:
		focus_id = _artifact_id(focus, "recent-focus")
		focus_node = {
			"node_id": focus_id,
			"node_type": "focus",
			"role": "recent_focus",
			"artifact_id": focus_id,
			"family_id": _clean_text(focus.get("family_id")),
			"entity": focus_entity,
			"aliases": _aliases(focus_entity.get("entity_label"), focus_entity.get("entity_key"), focus_entity.get("entity_type")),
			"payload": focus,
		}
		graph["focus_nodes"].append(focus_node)
		graph["nodes"].append({key: value for key, value in focus_node.items() if key != "payload"})
	for candidate_index, candidate in enumerate(candidate_payloads or []):
		for option_index, option in enumerate(_candidate_options(_clean_dict(candidate))):
			entity = nbu_row_entity_payload(option, {}, _clean_dict(candidate))
			option_node = {
				"node_id": f"candidate:{candidate_index}:option:{option_index + 1}",
				"node_type": "candidate_option",
				"role": "candidate_option",
				"row_index": option_index,
				"rank": option_index + 1,
				"entity": entity,
				"aliases": _aliases(entity.get("entity_label"), entity.get("entity_key"), entity.get("entity_type")),
				"row": option,
			}
			graph["candidate_option_nodes"].append(option_node)
			graph["nodes"].append({key: value for key, value in option_node.items() if key != "row"})
	graph["node_count"] = len(graph["nodes"])
	graph["artifact_count"] = len(graph["artifact_nodes"])
	graph["row_count"] = len(graph["row_nodes"])
	graph["entity_count"] = len(graph["entity_nodes"]) + len(graph["focus_nodes"])
	return graph


def list_nbu_context_graph_node_types() -> List[Dict[str, str]]:
	return [dict(row) for row in NBU_CONTEXT_GRAPH_NODE_TYPES]


def validate_nbu_context_graph_contract() -> Dict[str, Any]:
	required = {"artifact", "row", "entity", "focus", "candidate_option"}
	node_types = [_clean_text(row.get("node_type")) for row in NBU_CONTEXT_GRAPH_NODE_TYPES]
	errors: List[str] = []
	for node_type in sorted(required.difference(node_types)):
		errors.append(f"missing_context_graph_node_type:{node_type}")
	for node_type in node_types:
		if node_types.count(node_type) > 1:
			errors.append(f"duplicate_context_graph_node_type:{node_type}")
	for row in NBU_CONTEXT_GRAPH_NODE_TYPES:
		if not _clean_text(row.get("meaning")):
			errors.append(f"{_clean_text(row.get('node_type'))}:missing_meaning")
	return {
		"ok": not errors,
		"schema_version": NBU_CONTEXT_GRAPH_VERSION,
		"node_type_count": len(NBU_CONTEXT_GRAPH_NODE_TYPES),
		"errors": _dedupe(errors),
	}


def _artifact_match_score(raw_message: str, artifact_node: Dict[str, Any]) -> int:
	message = _normalize(raw_message)
	message_parts = _message_alias_set(raw_message)
	score = 0
	for alias in _clean_list(artifact_node.get("aliases")):
		normalized_alias = _normalize(alias)
		if len(normalized_alias) <= 2 or _is_generic_context_alias(normalized_alias):
			continue
		if normalized_alias in message_parts:
			score += 5 if len(normalized_alias) <= 3 else 7
		elif len(normalized_alias) > 3 and f" {normalized_alias} " in f" {message} ":
			score += 4
	return score


def _plural_alias(value: str) -> str:
	clean = _normalize(value)
	if not clean:
		return ""
	if clean.endswith("y"):
		return f"{clean[:-1]}ies"
	if clean.endswith("s"):
		return clean
	return f"{clean}s"


def _artifact_row_context_score(
	*,
	raw_message: str,
	artifact_node: Dict[str, Any],
	context_graph: Dict[str, Any],
) -> int:
	artifact_id = _clean_text(artifact_node.get("artifact_id"))
	if not artifact_id:
		return 0
	message_parts = _message_alias_set(raw_message)
	score = 0
	for row_node in _clean_dict(context_graph).get("row_nodes", []):
		row = _clean_dict(row_node)
		if _clean_text(row.get("artifact_id")) != artifact_id:
			continue
		entity = _clean_dict(row.get("entity"))
		entity_type = _normalize(entity.get("entity_type"))
		source_key = _normalize(row.get("source_key"))
		for value in (entity_type, _plural_alias(entity_type), source_key, _plural_alias(source_key)):
			if value and value in message_parts:
				score += 8
		for alias in _clean_list(row.get("aliases")):
			normalized_alias = _normalize(alias)
			if len(normalized_alias) >= 3 and normalized_alias in message_parts:
				score += 3
	return score


def select_nbu_context_graph_artifact(
	*,
	raw_message: str,
	context_graph: Dict[str, Any],
	prefer_previous: bool = False,
) -> Dict[str, Any]:
	artifacts = [_clean_dict(node) for node in _clean_dict(context_graph).get("artifact_nodes", []) if isinstance(node, dict)]
	if not artifacts:
		return {}
	scored: List[Tuple[int, int, Dict[str, Any]]] = []
	for artifact in artifacts:
		score = _artifact_match_score(raw_message, artifact)
		score += _artifact_row_context_score(
			raw_message=raw_message,
			artifact_node=artifact,
			context_graph=context_graph,
		)
		if prefer_previous and artifact.get("role") == "previous":
			score += 3
		if not prefer_previous and artifact.get("role") == "current":
			score += 2
		recency_penalty = int(artifact.get("recency_index") or 0)
		scored.append((score, -recency_penalty, artifact))
	scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
	if scored and scored[0][0] > 0:
		return scored[0][2]
	for artifact in artifacts:
		if artifact.get("role") == ("previous" if prefer_previous else "current"):
			return artifact
	return artifacts[0]


def _artifact_payload_from_node(artifact_node: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(artifact_node).get("payload"))


def _candidate_with_target(candidate_payload: Dict[str, Any], target_reference: str) -> Dict[str, Any]:
	candidate = _clean_dict(candidate_payload)
	if target_reference:
		candidate["target_reference"] = target_reference
	return candidate


def _resolution_from_focus(
	*,
	raw_message: str,
	target_reference: str,
	context_graph: Dict[str, Any],
) -> NBUContextResolutionContract | None:
	if not _contains_term(raw_message, DEICTIC_ENTITY_TERMS) and "back" not in set(_tokens(raw_message)):
		return None
	focus_nodes = [_clean_dict(node) for node in _clean_dict(context_graph).get("focus_nodes", []) if isinstance(node, dict)]
	if not focus_nodes:
		return None
	message_aliases = _message_alias_set(raw_message)
	scored: List[Tuple[int, Dict[str, Any]]] = []
	for focus in focus_nodes:
		score = 1
		for alias in _clean_list(focus.get("aliases")):
			if _normalize(alias) in message_aliases:
				score += 5
		scored.append((score, focus))
	scored.sort(key=lambda row: row[0], reverse=True)
	focus = scored[0][1]
	return NBUContextResolutionContract(
		status="resolved",
		target_reference=target_reference or "selected_entity",
		resolved_artifact_id=_clean_text(focus.get("artifact_id")),
		resolved_entity=_clean_dict(focus.get("entity")),
		reason="Resolved from the shared context graph recent-focus node.",
	)


def resolve_nbu_context_graph_reference(
	*,
	raw_message: str,
	candidate_payload: Dict[str, Any] | None = None,
	context_graph: Dict[str, Any] | None = None,
	current_artifact: Dict[str, Any] | None = None,
	previous_artifacts: List[Dict[str, Any]] | None = None,
	recent_focus: Dict[str, Any] | None = None,
) -> NBUContextResolutionContract:
	graph = _clean_dict(context_graph) or build_nbu_context_graph(
		current_artifact=current_artifact,
		previous_artifacts=previous_artifacts,
		recent_focus=recent_focus,
		candidate_payloads=[_clean_dict(candidate_payload)] if candidate_payload else [],
	)
	candidate = _clean_dict(candidate_payload)
	target_reference = _clean_text(candidate.get("target_reference")).lower() or "none"
	if target_reference == "none" and nbu_ordinal_reference_index(raw_message) >= 0:
		target_reference = "rank_n"
	if target_reference == "none" and _contains_term(raw_message, DEICTIC_ENTITY_TERMS):
		target_reference = "selected_entity"

	focus_resolution = _resolution_from_focus(
		raw_message=raw_message,
		target_reference=target_reference,
		context_graph=graph,
	)
	if focus_resolution is not None and target_reference in {"selected_entity", "named_entity", "previous_artifact", "none"}:
		return focus_resolution

	prefer_previous = target_reference == "previous_artifact" or _contains_term(raw_message, DISCOURSE_EXPLICIT_PREVIOUS_TERMS)
	selected_artifact = select_nbu_context_graph_artifact(
		raw_message=raw_message,
		context_graph=graph,
		prefer_previous=prefer_previous,
	)
	selected_payload = _artifact_payload_from_node(selected_artifact)

	if target_reference == "unclear":
		rows, _source_key = nbu_artifact_rows(selected_payload)
		if rows:
			return resolve_nbu_context_reference(
				raw_message=raw_message,
				candidate_payload={"target_reference": "current_artifact"},
				current_artifact=selected_payload,
				recent_focus=recent_focus,
			)
	if target_reference == "previous_artifact":
		target_reference = "current_artifact" if selected_payload else "previous_artifact"
	if target_reference in {"rank_n", "current_artifact", "selected_entity", "named_entity"}:
		return resolve_nbu_context_reference(
			raw_message=raw_message,
			candidate_payload=_candidate_with_target(candidate, target_reference),
			current_artifact=selected_payload,
			recent_focus=recent_focus,
		)
	if target_reference == "candidate_list":
		return resolve_nbu_context_reference(
			raw_message=raw_message,
			candidate_payload=candidate,
			current_artifact=selected_payload,
			recent_focus=recent_focus,
		)
	return NBUContextResolutionContract(
		status="not_evaluated",
		target_reference=target_reference,
		reason="No shared context graph resolution was required for this candidate.",
	)
