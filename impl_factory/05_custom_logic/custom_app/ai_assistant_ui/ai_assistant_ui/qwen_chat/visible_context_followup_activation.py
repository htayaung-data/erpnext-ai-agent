from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .entity_detail_request_support import (
	entity_detail_capability_id,
	resolve_entity_detail_request_interpretation,
)
from .business_language_guards import (
	looks_like_causal_change_claim,
	looks_like_predictive_guarantee_claim,
	looks_like_recommendation_or_decision_claim,
)
from .metadata import ontology_detect_concepts
from .natural_business_understanding_context_graph import resolve_nbu_context_graph_reference
from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_ordinal_reference_index,
	nbu_row_identity_label,
	resolve_nbu_context_reference,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_request_classification import (
	artifact_level_visible_context_requested,
	visible_context_reference_requested,
	visible_context_target_reference,
)
from .visible_context_frame_stack import (
	build_visible_context_frame_stack,
	resolve_visible_context_frame_arbitration,
	visible_context_artifacts,
	visible_context_payload_identity,
)
from .visible_context_boundary_language import (
	render_causal_boundary,
	render_missing_field_boundary,
	render_out_of_range_rank,
	render_prediction_boundary,
	render_recommendation_boundary,
	render_row_clarification,
)
from .semantic_aliases import detect_canonical_keys
from .evidence_drilldown_registry import build_governed_drilldown_plan
from .filter_readiness_contract import (
	build_filter_readiness_contract,
	render_filter_readiness_boundary,
)
from .source_detail_drilldown_execution import (
	build_source_detail_drilldown_payload_from_artifact_line,
	source_detail_grounding_context_from_artifact,
)


AppendMessage = Callable[[Any, str, str], None]
AppendToolPayload = Callable[[Any, Dict[str, Any]], None]
AssistantTextPayload = Callable[[str], str]
SaveSession = Callable[..., None]
ClearPendingClarification = Callable[[Any], None]


VISIBLE_CONTEXT_TERMS = {
	"above",
	"current",
	"latest",
	"last",
	"rank",
	"row",
	"position",
	"table",
	"that",
	"this",
	"it",
	"same",
	"selected",
}

DEICTIC_ENTITY_TERMS = {"that", "this", "it", "same", "selected"}
ARTIFACT_SCOPE_TERMS = {
	"analysis",
	"aging",
	"ap",
	"ar",
	"balance",
	"cash",
	"capital",
	"context",
	"flow",
	"payable",
	"payables",
	"profit",
	"receivable",
	"receivables",
	"report",
	"statement",
	"summary",
	"table",
	"working",
}
ORDINAL_REFERENCE_TERMS = {
	"first",
	"second",
	"third",
	"fourth",
	"fifth",
	"sixth",
	"seventh",
	"eighth",
	"ninth",
	"tenth",
	"last",
}

MONEY_FIELD_HINTS = (
	"amount",
	"total",
	"balance",
	"outstanding",
	"overdue",
	"credit",
	"value",
	"payable",
	"receivable",
)

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


def _ordered_unique_texts(values: List[Any] | None) -> List[str]:
	ordered: List[str] = []
	for value in values or []:
		clean = _clean_text(value)
		if clean and clean not in ordered:
			ordered.append(clean)
	return ordered


def _tokens(value: Any) -> set[str]:
	text = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
	return {token for token in text.split() if token}


def _safe_json_loads(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	try:
		payload = json.loads(_clean_text(value))
	except Exception:
		return {}
	return dict(payload) if isinstance(payload, dict) else {}


def visible_context_followup_requested(message: str) -> bool:
	return visible_context_reference_requested(message)


def _target_reference(message: str) -> str:
	return visible_context_target_reference(message)


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


def _payload_identity(payload: Dict[str, Any]) -> str:
	return visible_context_payload_identity(_clean_dict(payload))


def _context_artifacts(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any],
	limit: int = 8,
) -> List[Dict[str, Any]]:
	return visible_context_artifacts(
		session_doc,
		current_artifact=_clean_dict(current_artifact),
		limit=limit,
	)


def _context_frame_stack(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any],
	selected_entity: Dict[str, Any] | None = None,
	limit: int = 8,
) -> Dict[str, Any]:
	return build_visible_context_frame_stack(
		session_doc,
		current_artifact=_clean_dict(current_artifact),
		selected_entity=_clean_dict(selected_entity),
		limit=limit,
	)


def _artifact_by_identity(artifacts: List[Dict[str, Any]], artifact_id: str) -> Dict[str, Any]:
	target = _clean_text(artifact_id)
	if not target:
		return {}
	for artifact in artifacts:
		clean_artifact = _clean_dict(artifact)
		if _payload_identity(clean_artifact) == target:
			return clean_artifact
	return {}


def _should_use_frame_arbitration(
	*,
	frame_arbitration: Dict[str, Any],
	selected_artifact_id: str,
	current_artifact_id: str,
) -> bool:
	if _clean_text(frame_arbitration.get("status")).lower() != "resolved":
		return False
	relation = _clean_text(frame_arbitration.get("relation")).lower()
	if relation in {"previous_table", "same_table", "parent_table", "detail_table"}:
		return True
	if _clean_text(frame_arbitration.get("selected_evidence_scope")).lower() == "visible_rendered_table":
		return True
	return bool(
		_clean_text(selected_artifact_id)
		and _clean_text(current_artifact_id)
		and _clean_text(selected_artifact_id) != _clean_text(current_artifact_id)
	)


def _latest_selected_entity(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		payload = _safe_json_loads(_message_content(message))
		if _clean_text(payload.get("type")).lower() not in {
			"qwen_nbu_current_artifact_answer_activation_contract",
			"qwen_visible_context_followup_activation_contract",
		}:
			continue
		entity = _clean_dict(payload.get("resolved_entity"))
		label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
		if label:
			try:
				rank = int(payload.get("resolved_rank") or entity.get("rank") or 0)
			except (TypeError, ValueError):
				rank = 0
			if rank > 0:
				entity["rank"] = rank
				row = _clean_dict(entity.get("row"))
				if row and not row.get("rank"):
					row["rank"] = rank
					entity["row"] = row
			resolved_artifact_id = _clean_text(payload.get("resolved_artifact_id"))
			if resolved_artifact_id and not _clean_text(entity.get("resolved_artifact_id")):
				entity["resolved_artifact_id"] = resolved_artifact_id
			return entity
	return {}


def _selected_focus(session_doc: Any) -> Dict[str, Any]:
	entity = _latest_selected_entity(session_doc)
	if not entity:
		return {}
	label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
	return {
		"focus_kind": "entity",
		"focus_grain": _clean_text(entity.get("entity_type")) or "entity",
		"focus_label": label,
		"focus_key": _clean_text(entity.get("entity_key")) or label,
		"resolved_entity": entity,
	}


def _selected_focus_allowed_for_message(raw_message: str) -> bool:
	tokens = _tokens(raw_message)
	return any(term in tokens for term in DEICTIC_ENTITY_TERMS)


def _artifact_scope_requested(raw_message: str) -> bool:
	tokens = _tokens(raw_message)
	return bool(tokens.intersection(ARTIFACT_SCOPE_TERMS))


def _selected_focus_has_continuation_authority(raw_message: str, target_reference: str) -> bool:
	if not _selected_focus_allowed_for_message(raw_message):
		return False
	target = _clean_text(target_reference).lower()
	if target == "selected_entity":
		return True
	if target == "current_artifact" and _artifact_scope_requested(raw_message):
		return False
	return target == "current_artifact"


def _selected_entity_rank(entity: Dict[str, Any]) -> int:
	source = _clean_dict(entity)
	row = _clean_dict(source.get("row"))
	for value in (
		source.get("rank"),
		source.get("resolved_rank"),
		row.get("rank"),
		row.get("row_rank"),
		row.get("position"),
	):
		try:
			rank = int(value or 0)
		except (TypeError, ValueError):
			rank = 0
		if rank > 0:
			return rank
	return 0


def _selected_entity_artifact_id(entity: Dict[str, Any]) -> str:
	source = _clean_dict(entity)
	return _clean_text(
		source.get("resolved_artifact_id")
		or source.get("artifact_id")
		or source.get("source_artifact_id")
		or source.get("source_request_id")
	)


def _normalize_field_key(value: Any) -> str:
	text = re.sub(r"\([^)]*\)", "", _clean_text(value).lower())
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return re.sub(r"_+", "_", text).strip("_")


def _artifact_requested_dimension_keys(raw_message: str) -> List[str]:
	requested: List[str] = []
	for key in detect_canonical_keys(text=raw_message, dimension_or_metric="dimension"):
		normalized = _normalize_field_key(key)
		if normalized and normalized not in requested:
			requested.append(normalized)
	return requested


def _visible_row_field_keys(rows: List[Dict[str, Any]]) -> List[str]:
	keys: List[str] = []
	for row in rows[:10]:
		for key in _clean_dict(row).keys():
			normalized = _normalize_field_key(key)
			if normalized and normalized not in keys:
				keys.append(normalized)
	return keys


def _field_label(key: str) -> str:
	return _humanize(key).title()


def _artifact_field_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
) -> str:
	return render_filter_readiness_boundary(
		build_filter_readiness_contract(
			raw_message=raw_message,
			artifact_payload=_clean_dict(artifact_payload),
		)
	)


def _resolve_against_artifact(
	*,
	raw_message: str,
	target: str,
	artifact: Dict[str, Any],
	frame_stack: Dict[str, Any],
	frame_arbitration: Dict[str, Any],
	session_doc: Any,
) -> Dict[str, Any]:
	resolution = resolve_nbu_context_reference(
		raw_message=raw_message,
		candidate_payload={
			"candidate_id": "visible-context-followup",
			"target_reference": target,
			"intent_scope": "visible_context_followup",
			"authority_class": "safe_read",
		},
		current_artifact=artifact,
		recent_focus=_selected_focus(session_doc),
	).to_payload()
	resolution_payload = _clean_dict(resolution)
	resolution_payload["context_frame_stack"] = frame_stack
	resolution_payload["frame_arbitration"] = frame_arbitration
	return resolution_payload


def _resolve_visible_context(
	*,
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
) -> Dict[str, Any]:
	target = _target_reference(raw_message)
	selected_entity = _latest_selected_entity(session_doc)
	frame_stack = _context_frame_stack(
		session_doc,
		current_artifact=current_artifact,
		selected_entity=selected_entity,
	)
	frame_arbitration = resolve_visible_context_frame_arbitration(
		raw_message=raw_message,
		frame_stack=frame_stack,
	)
	if _selected_focus_has_continuation_authority(raw_message, target):
		selected = selected_entity
		if _clean_dict(selected).get("row"):
			return {
				"status": "resolved",
				"target_reference": "selected_entity",
				"resolved_rank": _selected_entity_rank(selected),
				"resolved_entity": selected,
				"reason": "Resolved from the last selected visible row.",
				"context_frame_stack": frame_stack,
				"frame_arbitration": frame_arbitration,
			}

	artifacts = _context_artifacts(session_doc, current_artifact=current_artifact)
	if not artifacts:
		return {
			"status": "not_supported",
			"target_reference": target,
			"reason": "No visible ERP table with rows is available in this conversation.",
			"context_frame_stack": frame_stack,
			"frame_arbitration": frame_arbitration,
		}
	selected_artifact_id = _clean_text(frame_arbitration.get("selected_artifact_id"))
	current_artifact_id = _payload_identity(_clean_dict(artifacts[0])) if artifacts else ""
	if _clean_text(frame_arbitration.get("status")).lower() == "missing_requested_object":
		return {
			"status": "missing_requested_object",
			"target_reference": target,
			"requested_rank": nbu_ordinal_reference_index(raw_message) + 1,
			"reason": _clean_text(frame_arbitration.get("reason")),
			"context_frame_stack": frame_stack,
			"frame_arbitration": frame_arbitration,
		}
	if _clean_text(frame_arbitration.get("relation")).lower() == "same_table":
		same_table_artifact = _artifact_by_identity(
			artifacts,
			_selected_entity_artifact_id(selected_entity),
		)
		if same_table_artifact:
			resolution_payload = _resolve_against_artifact(
				raw_message=raw_message,
				target=target,
				artifact=same_table_artifact,
				frame_stack=frame_stack,
				frame_arbitration=frame_arbitration,
				session_doc=session_doc,
			)
			if _clean_text(resolution_payload.get("status")).lower() in {"resolved", "ambiguous", "out_of_range"}:
				return resolution_payload
	if _should_use_frame_arbitration(
		frame_arbitration=frame_arbitration,
		selected_artifact_id=selected_artifact_id,
		current_artifact_id=current_artifact_id,
	):
		selected_artifact = _artifact_by_identity(artifacts, selected_artifact_id)
		if selected_artifact:
			resolution_payload = _resolve_against_artifact(
				raw_message=raw_message,
				target=target,
				artifact=selected_artifact,
				frame_stack=frame_stack,
				frame_arbitration=frame_arbitration,
				session_doc=session_doc,
			)
			if _clean_text(resolution_payload.get("status")).lower() in {"resolved", "ambiguous", "out_of_range"}:
				return resolution_payload
	resolution = resolve_nbu_context_graph_reference(
		raw_message=raw_message,
		candidate_payload={
			"candidate_id": "visible-context-followup",
			"target_reference": target,
			"intent_scope": "visible_context_followup",
			"authority_class": "safe_read",
		},
		current_artifact=artifacts[0],
		previous_artifacts=artifacts[1:],
		recent_focus=_selected_focus(session_doc),
	).to_payload()
	resolution_payload = _clean_dict(resolution)
	resolution_payload["context_frame_stack"] = frame_stack
	resolution_payload["frame_arbitration"] = frame_arbitration
	return resolution_payload


def _artifact_identity_matches(payload: Dict[str, Any], artifact_id: str) -> bool:
	target = _clean_text(artifact_id)
	if not target:
		return False
	return _payload_identity(payload) == target


def _source_detail_artifact_for_visible_row(
	*,
	session_doc: Any,
	current_artifact: Dict[str, Any],
	resolution: Dict[str, Any],
	row: Dict[str, Any],
) -> Dict[str, Any]:
	artifacts: List[Dict[str, Any]] = []
	current_payload = _clean_dict(current_artifact)
	if current_payload:
		artifacts.append(current_payload)
	for artifact in _context_artifacts(session_doc, current_artifact=current_payload, limit=10):
		clean_artifact = _clean_dict(artifact)
		if clean_artifact and _payload_identity(clean_artifact) not in {_payload_identity(existing) for existing in artifacts}:
			artifacts.append(clean_artifact)
	if not artifacts:
		return {}
	resolved_artifact_id = _clean_text(resolution.get("resolved_artifact_id"))
	ordered_artifacts = sorted(
		artifacts,
		key=lambda artifact: 0 if _artifact_identity_matches(_clean_dict(artifact), resolved_artifact_id) else 1,
	)
	for artifact in ordered_artifacts:
		artifact_payload = _clean_dict(artifact)
		if not artifact_payload:
			continue
		context = source_detail_grounding_context_from_artifact(artifact_payload)
		plan = build_governed_drilldown_plan(
			grounding_context=context,
			focused_row=row,
		)
		if _clean_text(plan.get("status")) == "source_detail_available":
			return artifact_payload
	return {}


def _source_detail_answer_for_visible_row(
	*,
	session_doc: Any,
	current_artifact: Dict[str, Any],
	resolution: Dict[str, Any],
	row: Dict[str, Any],
	user_id: str,
) -> str:
	artifact = _source_detail_artifact_for_visible_row(
		session_doc=session_doc,
		current_artifact=current_artifact,
		resolution=resolution,
		row=row,
	)
	if not artifact:
		return ""
	try:
		payload = build_source_detail_drilldown_payload_from_artifact_line(
			artifact_payload=artifact,
			focused_row=row,
			user_id=user_id,
		)
	except Exception:
		return ""
	if not isinstance(payload, dict):
		return ""
	return _clean_text(payload.get("answer_text"))


def _current_entity_detail_evidence_followup_requested(raw_message: str, current_artifact: Dict[str, Any]) -> bool:
	artifact = _clean_dict(current_artifact)
	if _clean_text(artifact.get("family_id")).lower() != "entity_detail":
		return False
	if _visible_ordinal_or_rank_lookup_requested(raw_message):
		return False
	dimensions = _clean_dict(artifact.get("dimensions"))
	entity_type = _clean_text(dimensions.get("entity_type")).lower()
	if not entity_type:
		return False
	capability_id = entity_detail_capability_id(entity_type)
	requested_metrics = _ordered_unique_texts(
		detect_canonical_keys(
			text=raw_message,
			capability_id=capability_id or None,
			dimension_or_metric="metric",
		)
	)
	requested_dimensions = _ordered_unique_texts(
		detect_canonical_keys(
			text=raw_message,
			capability_id=capability_id or None,
			dimension_or_metric="dimension",
		)
	)
	requested_concepts = _ordered_unique_texts(
		[
			value
			for value in ontology_detect_concepts(raw_message)
			if _clean_text(value)
		]
	)
	interpretation = resolve_entity_detail_request_interpretation(
		entity_type=entity_type,
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		requested_concepts=requested_concepts,
		artifact_payload=artifact,
	)
	entity_question_type = _clean_text(interpretation.get("entity_question_type"))
	return bool(
		interpretation.get("clarification_required")
		or entity_question_type
		or requested_metrics
		or requested_dimensions
	)


def _visible_ordinal_or_rank_lookup_requested(raw_message: str) -> bool:
	tokens = _tokens(raw_message)
	if tokens.intersection(ORDINAL_REFERENCE_TERMS):
		return True
	text = " ".join(_clean_text(raw_message).lower().split())
	return bool(
		re.search(r"\b(?:rank|row|position|number|no|#)\s*\d{1,2}\b", text)
		or re.search(r"\b\d{1,2}(?:st|nd|rd|th)\b", text)
	)


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position", "idx", "index"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _humanize(value: Any) -> str:
	text = _clean_text(value).replace("_", " ").replace("-", " ")
	return " ".join(part for part in text.split() if part)


def _format_value(key: str, value: Any) -> str:
	if value in ("", None):
		return ""
	if isinstance(value, float):
		text = f"{value:,.2f}".rstrip("0").rstrip(".")
	elif isinstance(value, int):
		text = f"{value:,}"
	else:
		text = _clean_text(value)
	key_lower = _clean_text(key).lower()
	if isinstance(value, (int, float)) and any(hint in key_lower for hint in MONEY_FIELD_HINTS):
		return f"{text} MMK"
	if (
		not isinstance(value, (int, float))
		and any(hint in key_lower for hint in MONEY_FIELD_HINTS)
		and "mmk" not in text.lower()
		and "%" not in text
		and re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", text)
	):
		return f"{text} MMK"
	return text


def _number_value(value: Any) -> float | None:
	if isinstance(value, bool):
		return None
	if isinstance(value, (int, float)):
		return float(value)
	text = _clean_text(value)
	if not text:
		return None
	multiplier = 1.0
	if re.search(r"\b(?:million|mn|m)\b", text, flags=re.IGNORECASE):
		multiplier = 1_000_000.0
	text = re.sub(r"\bMMK\b", "", text, flags=re.IGNORECASE)
	text = re.sub(r"\b(?:million|mn|m)\b", "", text, flags=re.IGNORECASE)
	text = text.replace(",", "").replace("%", "").strip()
	try:
		return float(text) * multiplier
	except (TypeError, ValueError):
		return None


def _first_numeric(row: Dict[str, Any], keys: Tuple[str, ...]) -> float | None:
	for key in keys:
		if key in row:
			value = _number_value(row.get(key))
			if value is not None:
				return value
	return None


def _money_text(value: float) -> str:
	if abs(value) >= 1_000_000:
		million_text = f"{value / 1_000_000:,.1f}".rstrip("0").rstrip(".")
		return f"{million_text} MMK Million"
	return f"{value:,.0f} MMK"


def _percent_text(value: float) -> str:
	return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def _risk_signal_lines(row: Dict[str, Any]) -> List[str]:
	outstanding = _first_numeric(row, ("outstanding_amount", "outstanding", "outstanding_total"))
	total_due = _first_numeric(row, ("total_due", "total_amount_due", "due_amount"))
	overdue = _first_numeric(row, ("overdue_amount", "overdue_total", "overdue_31_plus", "overdue"))
	credit_utilization = _first_numeric(row, ("credit_utilization", "credit_used_pct", "credit_used_percent"))
	credit_limit = _first_numeric(row, ("credit_limit", "credit_limit_amount"))
	lines: List[str] = []

	if overdue is not None and overdue > 0:
		if outstanding is not None and outstanding > 0:
			lines.append(
				f"- {_money_text(overdue)} is overdue, which is {_percent_text(overdue / outstanding * 100)} of the outstanding balance."
			)
		elif total_due is not None and total_due > 0:
			lines.append(
				f"- {_money_text(overdue)} is overdue, which is {_percent_text(overdue / total_due * 100)} of the total due amount."
			)
		else:
			lines.append(f"- It has {_money_text(overdue)} overdue.")

	if total_due is not None and outstanding is not None and outstanding > 0:
		due_ratio = total_due / outstanding * 100
		if due_ratio >= 80:
			lines.append(
				f"- Total due is {_money_text(total_due)}, close to the outstanding balance ({_percent_text(due_ratio)})."
			)

	if credit_utilization is not None:
		lines.append(f"- Credit utilization is {_percent_text(credit_utilization)}, which adds credit-exposure context.")
	elif credit_limit is not None and outstanding is not None and credit_limit > 0:
		lines.append(
			f"- Outstanding balance uses {_percent_text(outstanding / credit_limit * 100)} of the configured credit limit."
		)

	return lines[:4]


def _row_metric_lines(row: Dict[str, Any], *, identity_label: str = "", limit: int = 8) -> List[str]:
	always_identity_keys = {
		"rank",
		"row_rank",
		"position",
		"idx",
		"index",
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
		"entity_key",
		"entity_code",
		"entity_label",
	}
	conditional_identity_keys = {
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
		"entity",
		"entity_name",
		"label",
		"name",
	}
	lines: List[str] = []
	normalized_identity = _clean_text(identity_label).lower()
	for key, value in row.items():
		clean_key = _clean_text(key)
		clean_key_lower = clean_key.lower()
		if not clean_key or clean_key_lower in always_identity_keys:
			continue
		if clean_key_lower in conditional_identity_keys and _clean_text(value).lower() == normalized_identity:
			continue
		display = _format_value(clean_key, value)
		if display:
			lines.append(f"- {_humanize(clean_key).title()}: {display}")
		if len(lines) >= limit:
			break
	return lines


def _entity_label(entity: Dict[str, Any]) -> str:
	row = _clean_dict(entity.get("row"))
	return _clean_text(
		entity.get("entity_label")
		or entity.get("entity_key")
		or nbu_row_identity_label(row)
	)


def _nbu_authority_class(nbu_trace_payload: Dict[str, Any] | None) -> str:
	payload = _clean_dict(nbu_trace_payload)
	authority_plan = _clean_dict(payload.get("authority_plan"))
	return _clean_text(authority_plan.get("authority_class")).lower()


def _nbu_selected_requested_action(nbu_trace_payload: Dict[str, Any] | None) -> str:
	payload = _clean_dict(nbu_trace_payload)
	selected_id = _clean_text(payload.get("selected_candidate_id"))
	candidates = _clean_list(payload.get("candidate_interpretations"))
	for candidate in candidates:
		candidate_payload = _clean_dict(candidate)
		if selected_id and _clean_text(candidate_payload.get("candidate_id")) != selected_id:
			continue
		return _clean_text(candidate_payload.get("requested_action")).lower()
	return ""


def _reasoning_type(reasoning_semantic_result: Any) -> str:
	if reasoning_semantic_result is None:
		return ""
	if _clean_text(getattr(reasoning_semantic_result, "status", "")).lower() != "accepted":
		return ""
	intent = getattr(reasoning_semantic_result, "intent", None)
	return _clean_text(getattr(intent, "reasoning_type", "")).lower()


def _latest_nbu_trace_payload(payloads: List[Dict[str, Any]] | None) -> Dict[str, Any]:
	for payload in reversed(payloads or []):
		clean_payload = _clean_dict(payload)
		if _clean_text(clean_payload.get("type")).lower() == "qwen_natural_business_understanding_trace_contract":
			return clean_payload
	return {}


def _nbu_selected_candidate_payload(nbu_trace_payload: Dict[str, Any] | None) -> Dict[str, Any]:
	payload = _clean_dict(nbu_trace_payload)
	selected_id = _clean_text(payload.get("selected_candidate_id"))
	candidates = _clean_list(payload.get("candidate_interpretations"))
	for candidate in candidates:
		candidate_payload = _clean_dict(candidate)
		if selected_id and _clean_text(candidate_payload.get("candidate_id")) != selected_id:
			continue
		return candidate_payload
	return {}


def _should_explain_row_signal(
	row: Dict[str, Any],
	*,
	nbu_trace_payload: Dict[str, Any] | None,
	reasoning_semantic_result: Any = None,
) -> bool:
	if not _risk_signal_lines(row):
		return False
	authority_class = _nbu_authority_class(nbu_trace_payload)
	requested_action = _nbu_selected_requested_action(nbu_trace_payload)
	reasoning_type = _reasoning_type(reasoning_semantic_result)
	selected_candidate = _nbu_selected_candidate_payload(nbu_trace_payload)
	if authority_class or requested_action:
		return (
			authority_class == "safe_explanation"
			or requested_action == "explain"
			or (
				requested_action == "detail"
				and reasoning_type in {"explanation", "interpretation"}
			)
			or (
				_clean_text(selected_candidate.get("target_reference")).lower() == "selected_entity"
				and bool(_clean_list(selected_candidate.get("candidate_composite_family_ids")))
			)
		)
	return (
		reasoning_type in {"explanation", "interpretation"}
	)


def _should_attempt_selected_row_drilldown(
	resolution: Dict[str, Any],
	*,
	nbu_trace_payload: Dict[str, Any] | None,
	reasoning_semantic_result: Any = None,
) -> bool:
	if _clean_text(_clean_dict(resolution).get("status")).lower() != "resolved":
		return False
	if _clean_text(_clean_dict(resolution).get("target_reference")).lower() != "selected_entity":
		return False
	if _nbu_selected_requested_action(nbu_trace_payload) == "detail":
		return True
	return _reasoning_type(reasoning_semantic_result) in {"continuation_detail"}


def _visible_identity_lookup_requested(raw_message: str) -> bool:
	text = " ".join(_clean_text(raw_message).lower().split())
	if not text:
		return False
	if re.search(
		r"\b(why|explain|interpret|insight|detail|details|breakdown|break\s+down|concerning|risky|risk|cause|caused|driver|recommend|should)\b",
		text,
	):
		return False
	return bool(
		re.search(
			r"\b(who|which|what)\s+(?:is|are|was|were)\b"
			r"|\b(rank|row|position)\s*\d+\b"
			r"|\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last)\b",
			text,
		)
	)


def _visible_followup_authority_intent(
	*,
	raw_message: str = "",
	nbu_trace_payload: Dict[str, Any] | None,
	reasoning_semantic_result: Any = None,
) -> str:
	if looks_like_predictive_guarantee_claim(raw_message):
		return "prediction_boundary"
	if looks_like_causal_change_claim(raw_message):
		return "causal_boundary"
	if looks_like_recommendation_or_decision_claim(raw_message):
		return "recommendation_boundary"
	authority_class = _nbu_authority_class(nbu_trace_payload)
	if authority_class == "prediction":
		return "prediction_boundary"
	if authority_class in {"recommendation", "approval_action", "policy_decision"}:
		return "recommendation_boundary"
	if authority_class == "causal_driver_analysis":
		return "causal_boundary"
	if _reasoning_type(reasoning_semantic_result) == "recommendation":
		return "recommendation_boundary"
	return "safe_visible_fact"


def _should_defer_visible_context_to_governed_detail(
	resolution: Dict[str, Any],
	*,
	nbu_trace_payload: Dict[str, Any] | None,
	reasoning_semantic_result: Any = None,
) -> bool:
	if _clean_text(_clean_dict(resolution).get("status")).lower() != "resolved":
		return False
	if _reasoning_type(reasoning_semantic_result) in {"explanation", "interpretation", "recommendation"}:
		return False
	selected_candidate = _nbu_selected_candidate_payload(nbu_trace_payload)
	if (
		_clean_text(selected_candidate.get("target_reference")).lower() == "selected_entity"
		and bool(_clean_list(selected_candidate.get("candidate_composite_family_ids")))
	):
		return False
	if _nbu_selected_requested_action(nbu_trace_payload) != "detail":
		return False
	entity = _clean_dict(_clean_dict(resolution).get("resolved_entity"))
	return bool(
		_clean_text(entity.get("entity_type"))
		and _clean_text(entity.get("entity_label") or entity.get("entity_key"))
	)


def _resolved_answer_text(
	raw_message: str,
	resolution: Dict[str, Any],
	*,
	session_doc: Any = None,
	current_artifact: Dict[str, Any] | None = None,
	user_id: str = "",
	nbu_trace_payload: Dict[str, Any] | None = None,
	reasoning_semantic_result: Any = None,
) -> str:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _entity_label(entity)
	try:
		rank = int(resolution.get("resolved_rank") or 0)
	except (TypeError, ValueError):
		rank = 0
	if rank <= 0 and _clean_text(resolution.get("target_reference")).lower() != "selected_entity":
		rank = _row_rank(row, 0)
	rank_text = f"Rank {rank}" if rank > 0 else "The selected row"
	entry_rank_text = f"rank {rank}" if rank > 0 else "selected row"
	identity_lookup_requested = _visible_identity_lookup_requested(raw_message)
	explain_row_signal = _should_explain_row_signal(
		row,
		nbu_trace_payload=nbu_trace_payload,
		reasoning_semantic_result=reasoning_semantic_result,
	)
	if identity_lookup_requested:
		explain_row_signal = False
	if (
		not identity_lookup_requested
		and not explain_row_signal
		and _clean_text(resolution.get("target_reference")).lower() == "selected_entity"
	):
		explain_row_signal = bool(_risk_signal_lines(row))
	drilldown_requested = False
	if not identity_lookup_requested:
		drilldown_requested = _should_attempt_selected_row_drilldown(
			resolution,
			nbu_trace_payload=nbu_trace_payload,
			reasoning_semantic_result=reasoning_semantic_result,
		)
	if explain_row_signal or drilldown_requested:
		source_detail_answer = _source_detail_answer_for_visible_row(
			session_doc=session_doc,
			current_artifact=_clean_dict(current_artifact),
			resolution=resolution,
			row=row,
			user_id=user_id or "Administrator",
		)
		if source_detail_answer:
			visible_lines = [
				f"{label} is the {entry_rank_text} entry in the table above.",
				"",
			]
			risk_lines = _risk_signal_lines(row)
			if risk_lines:
				visible_lines.extend(["Visible row signal:", *risk_lines, ""])
			visible_lines.extend([
				"Deeper approved ERP detail:",
				"",
				source_detail_answer,
			])
			return "\n".join(line for line in visible_lines if line is not None).strip()
	if explain_row_signal:
		lines = [
			f"{label} is the {entry_rank_text} entry in the table above.",
			"",
			"Why this stands out from the visible row:",
		]
		risk_lines = _risk_signal_lines(row)
		if risk_lines:
			lines.extend(risk_lines)
			lines.append("")
			lines.append(
				"Consultant takeaway: this row combines cash impact with timing or exposure intensity, so it deserves focused follow-up before lower-risk rows."
			)
			lines.append("")
			lines.append("Facts from that row:")
	else:
		lines = [f"{rank_text} is {label} in the table above."]
	metric_lines = _row_metric_lines(row, identity_label=label)
	if metric_lines:
		if not explain_row_signal:
			lines.append("")
			lines.append("Current row facts:")
		lines.extend(metric_lines)
	lines.append("")
	lines.append("This is based only on the table above.")
	return "\n".join(line for line in lines if line is not None).strip()


def _boundary_answer_text(raw_message: str, resolution: Dict[str, Any], *, authority_intent: str) -> str:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _entity_label(entity)
	try:
		rank = int(resolution.get("resolved_rank") or _row_rank(row, 0) or 0)
	except (TypeError, ValueError):
		rank = 0
	rank_text = f"Rank {rank}" if rank > 0 else "the selected row"
	metric_lines = _row_metric_lines(row, identity_label=label)
	if authority_intent == "prediction_boundary":
		return render_prediction_boundary(
			rank_text=rank_text,
			entity_label=label,
			metric_lines=metric_lines,
		)
	elif authority_intent == "recommendation_boundary":
		return render_recommendation_boundary(
			rank_text=rank_text,
			entity_label=label,
			metric_lines=metric_lines,
		)
	elif authority_intent == "causal_boundary":
		return render_causal_boundary(
			rank_text=rank_text,
			entity_label=label,
			metric_lines=metric_lines,
		)
	else:
		return _resolved_answer_text(raw_message, resolution)


def _ambiguity_options_from_resolution(resolution: Dict[str, Any]) -> List[str]:
	return [_clean_text(value) for value in _clean_list(resolution.get("ambiguity_options")) if _clean_text(value)]


def _clarification_text(resolution: Dict[str, Any]) -> str:
	options = _ambiguity_options_from_resolution(resolution)
	return render_row_clarification(options=options)


def _out_of_range_text(resolution: Dict[str, Any]) -> str:
	options = _ambiguity_options_from_resolution(resolution)
	requested_rank = _positive_int(resolution.get("requested_rank"))
	available_count = _positive_int(resolution.get("available_row_count")) or len(options)
	target_reference = _clean_text(resolution.get("target_reference")).lower()
	row_label = "option" if target_reference == "candidate_list" else "row"
	return render_out_of_range_rank(
		options=options,
		requested_rank=requested_rank,
		available_count=available_count,
		row_label=row_label,
	)


def _missing_requested_object_text(resolution: Dict[str, Any]) -> str:
	frame_arbitration = _clean_dict(resolution.get("frame_arbitration"))
	requested_label = _clean_text(frame_arbitration.get("requested_object_label"))
	requested_aliases = [
		_clean_text(value).replace("_", " ")
		for value in _clean_list(frame_arbitration.get("requested_object_aliases"))
		if _clean_text(value)
	]
	if not requested_label:
		requested_label = requested_aliases[0] if requested_aliases else "the requested row type"
	available_types = [
		_humanize(value).title()
		for value in _clean_list(frame_arbitration.get("available_business_object_types"))
		if _clean_text(value)
	]
	available_labels = [
		_clean_text(value)
		for value in _clean_list(frame_arbitration.get("available_table_labels"))
		if _clean_text(value)
	]
	lines = [
		f"I can't answer that from the visible context because there is no visible {requested_label} table in scope.",
		"I should not reuse an older table from another business family to answer this.",
	]
	if available_types:
		lines.extend(["", f"Visible table types available: {', '.join(available_types[:6])}."])
	if available_labels:
		lines.append(f"Visible tables checked: {', '.join(available_labels[:4])}.")
	lines.extend(
		[
			"",
			"Please ask for the relevant detail/breakdown first, or refer to a visible table that contains that row type.",
		]
	)
	return "\n".join(lines).strip()


def _activation_contract(
	*,
	request_id: str,
	resolution: Dict[str, Any],
	answer_mode: str,
) -> Dict[str, Any]:
	entity = _clean_dict(resolution.get("resolved_entity"))
	try:
		resolved_rank = int(resolution.get("resolved_rank") or entity.get("rank") or 0)
	except (TypeError, ValueError):
		resolved_rank = 0
	if resolved_rank > 0:
		entity["rank"] = resolved_rank
		row = _clean_dict(entity.get("row"))
		if row and not row.get("rank"):
			row["rank"] = resolved_rank
			entity["row"] = row
	return {
		"type": "qwen_nbu_current_artifact_answer_activation_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"activation_state": "activated",
		"activation_mode": answer_mode,
		"activation_level": "visible_context_followup",
		"live_execution_enabled": True,
		"runtime_execution_enabled": False,
		"resolved_artifact_id": _clean_text(resolution.get("resolved_artifact_id")),
		"resolved_row_index": resolution.get("resolved_row_index"),
		"resolved_rank": resolved_rank or resolution.get("resolved_rank"),
		"resolved_entity": entity,
		"reason": _clean_text(resolution.get("reason")) or "Resolved from the visible ERP result in the current conversation.",
	}


def _trace_payload(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	raw_message: str,
	resolution: Dict[str, Any],
) -> Dict[str, Any]:
	resolution_payload = _clean_dict(resolution)
	frame_stack = _clean_dict(resolution_payload.pop("context_frame_stack", {}))
	frame_arbitration = _clean_dict(resolution_payload.pop("frame_arbitration", {}))
	return {
		"type": "qwen_visible_context_followup_trace_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"session_id": _clean_text(session_id),
		"user_id": _clean_text(user_id),
		"site_name": _clean_text(site_name),
		"raw_message": _clean_text(raw_message),
		"resolution": resolution_payload,
		"context_frame_stack": frame_stack,
		"frame_arbitration": frame_arbitration,
		"created_at_unix": time.time(),
	}


def try_activate_visible_context_followup_response(
	*,
	session_doc: Any,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str = "",
	raw_message: str,
	current_artifact: Dict[str, Any] | None = None,
	latest_grounded_turn: Dict[str, Any] | None = None,
	interaction_contract: Any = None,
	reasoning_semantic_result: Any = None,
	user_message_already_appended: bool = False,
	append_message: AppendMessage,
	append_tool_payload: AppendToolPayload,
	assistant_text_payload: AssistantTextPayload,
	save_session: SaveSession,
	clear_pending_clarification_signal: ClearPendingClarification | None = None,
	additional_tool_payloads: List[Dict[str, Any]] | None = None,
) -> Tuple[bool, Dict[str, Any] | None]:
	if not visible_context_followup_requested(raw_message):
		return False, None
	if _current_entity_detail_evidence_followup_requested(raw_message, _clean_dict(current_artifact)):
		return False, None

	resolution = _resolve_visible_context(
		session_doc=session_doc,
		raw_message=raw_message,
		current_artifact=_clean_dict(current_artifact),
	)
	status = _clean_text(resolution.get("status")).lower()
	if status not in {"resolved", "ambiguous", "out_of_range", "missing_requested_object"}:
		return False, None
	if (
		status == "ambiguous"
		and _clean_text(resolution.get("target_reference")).lower() == "current_artifact"
		and artifact_level_visible_context_requested(raw_message)
	):
		artifacts = _context_artifacts(session_doc, current_artifact=_clean_dict(current_artifact), limit=8)
		frame_arbitration = _clean_dict(resolution.get("frame_arbitration"))
		selected_artifact_id = _clean_text(resolution.get("resolved_artifact_id")) or _clean_text(frame_arbitration.get("selected_artifact_id"))
		selected_artifact = _artifact_by_identity(artifacts, selected_artifact_id)
		filter_readiness_contract = build_filter_readiness_contract(
			raw_message=raw_message,
			artifact_payload=selected_artifact or (artifacts[0] if artifacts else _clean_dict(current_artifact)),
		)
		answer_text = render_filter_readiness_boundary(filter_readiness_contract)
		if not answer_text:
			return False, None
		answer_mode = "visible_context_boundary"
		authority_intent = "safe_visible_fact"
		if not user_message_already_appended:
			append_message(session_doc, "user", raw_message)
		for payload in additional_tool_payloads or []:
			if isinstance(payload, dict) and payload:
				append_tool_payload(session_doc, payload)
		append_tool_payload(session_doc, filter_readiness_contract)
		trace = _trace_payload(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			raw_message=raw_message,
			resolution={**resolution, "authority_intent": authority_intent},
		)
		append_tool_payload(session_doc, trace)
		activation_contract = _activation_contract(
			request_id=request_id,
			resolution=resolution,
			answer_mode=answer_mode,
		)
		append_tool_payload(session_doc, activation_contract)
		execution_path_payload = {
			"type": "qwen_execution_path",
			"contract_version": CONTRACT_VERSION,
			"request_id": _clean_text(request_id),
			"path": answer_mode,
			"reason": _clean_text(activation_contract.get("reason")),
			"requires_runtime": False,
			"grounded_required": False,
		}
		append_tool_payload(session_doc, execution_path_payload)
		append_message(session_doc, "assistant", assistant_text_payload(answer_text))
		if clear_pending_clarification_signal is not None:
			clear_pending_clarification_signal(session_doc)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": True,
			"request_id": request_id,
			"mode": answer_mode,
			"agent_meta": {"engine": "visible_context_followup", "status": status},
		}

	nbu_trace_payload = _latest_nbu_trace_payload(additional_tool_payloads)
	if _should_defer_visible_context_to_governed_detail(
		resolution,
		nbu_trace_payload=nbu_trace_payload,
		reasoning_semantic_result=reasoning_semantic_result,
	):
		return False, None
	authority_intent = _visible_followup_authority_intent(
		raw_message=raw_message,
		nbu_trace_payload=nbu_trace_payload,
		reasoning_semantic_result=reasoning_semantic_result,
	)
	if status == "resolved" and authority_intent != "safe_visible_fact":
		answer_mode = "visible_context_boundary"
		answer_text = _boundary_answer_text(raw_message, resolution, authority_intent=authority_intent)
	else:
		if status == "resolved":
			answer_mode = "visible_context_answer"
			answer_text = _resolved_answer_text(
				raw_message,
				resolution,
				session_doc=session_doc,
				current_artifact=_clean_dict(current_artifact),
				user_id=user_id,
				nbu_trace_payload=nbu_trace_payload,
				reasoning_semantic_result=reasoning_semantic_result,
			)
		elif status == "out_of_range":
			answer_mode = "visible_context_out_of_range"
			answer_text = _out_of_range_text(resolution)
		elif status == "missing_requested_object":
			answer_mode = "visible_context_boundary"
			answer_text = _missing_requested_object_text(resolution)
		else:
			answer_mode = "visible_context_clarification"
			answer_text = _clarification_text(resolution)
	if not answer_text:
		return False, None

	if not user_message_already_appended:
		append_message(session_doc, "user", raw_message)
	for payload in additional_tool_payloads or []:
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)
	trace = _trace_payload(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=raw_message,
		resolution={**resolution, "authority_intent": authority_intent},
	)
	append_tool_payload(session_doc, trace)
	activation_contract = _activation_contract(
		request_id=request_id,
		resolution=resolution,
		answer_mode=answer_mode,
	)
	append_tool_payload(session_doc, activation_contract)
	execution_path_payload = {
		"type": "qwen_execution_path",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"path": answer_mode,
		"reason": _clean_text(activation_contract.get("reason")),
		"requires_runtime": False,
		"grounded_required": False,
	}
	append_tool_payload(session_doc, execution_path_payload)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	if clear_pending_clarification_signal is not None:
		clear_pending_clarification_signal(session_doc)
	if interaction_contract is not None:
		from .contracts import ExecutionPath, build_audit_envelope, build_followup_resolution_contract

		execution_path = ExecutionPath(
			request_id=request_id,
			path=answer_mode,
			reason=_clean_text(activation_contract.get("reason")),
			requires_runtime=False,
			grounded_required=False,
		)
		resolution_contract = build_followup_resolution_contract(
			request_id=request_id,
			mode=answer_mode,
			requested_modes=[answer_mode],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=bool(_clean_dict(latest_grounded_turn).get("grounded")),
			reason="Visible ERP result follow-up was handled before route clarification.",
		)
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=resolution_contract,
				execution_path=execution_path,
				runtime_trace_payload={"agent_meta": {"engine": "visible_context_followup", "status": status}},
				grounded_turn_context=_clean_dict(latest_grounded_turn),
				answer_text=answer_text,
			).to_payload(),
		)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": answer_mode,
		"agent_meta": {"engine": "visible_context_followup", "status": status},
	}
