from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .entity_detail_request_support import (
	entity_detail_capability_id,
	resolve_entity_detail_request_interpretation,
)
from .business_language_guards import looks_like_predictive_guarantee_claim
from .metadata import ontology_detect_concepts
from .natural_business_understanding_context_graph import resolve_nbu_context_graph_reference
from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_row_identity_label,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_request_classification import (
	artifact_level_visible_context_requested,
	visible_context_reference_requested,
	visible_context_target_reference,
)
from .natural_business_understanding_visible_artifacts import session_visible_rendered_artifacts
from .semantic_aliases import detect_canonical_keys


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


def _context_artifacts(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any],
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
		identity = _payload_identity(clean_payload)
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
	requested_keys = _artifact_requested_dimension_keys(raw_message)
	if not requested_keys:
		return ""
	rows, _source = nbu_artifact_rows(_clean_dict(artifact_payload))
	if not rows:
		return ""
	visible_keys = _visible_row_field_keys(rows)
	if not visible_keys:
		return ""
	missing_keys = [key for key in requested_keys if key not in visible_keys]
	if not missing_keys:
		return ""
	lines = [
		"I can't verify that from the table above.",
		"",
		f"The visible rows show: {', '.join(_field_label(key) for key in visible_keys[:8])}.",
		f"The table does not show: {', '.join(_field_label(key) for key in missing_keys[:6])}.",
		"",
		"To answer this safely, we need a governed result that includes those fields or a filtered view that proves the condition.",
	]
	return "\n".join(lines).strip()


def _resolve_visible_context(
	*,
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
) -> Dict[str, Any]:
	target = _target_reference(raw_message)
	if target == "selected_entity" and _selected_focus_allowed_for_message(raw_message):
		selected = _latest_selected_entity(session_doc)
		if _clean_dict(selected).get("row"):
			return {
				"status": "resolved",
				"target_reference": target,
				"resolved_rank": _row_rank(_clean_dict(selected.get("row")), 0),
				"resolved_entity": selected,
				"reason": "Resolved from the last selected visible row.",
			}

	artifacts = _context_artifacts(session_doc, current_artifact=current_artifact)
	if not artifacts:
		return {
			"status": "not_supported",
			"target_reference": target,
			"reason": "No visible ERP table with rows is available in this conversation.",
		}
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
	return _clean_dict(resolution)


def _current_entity_detail_evidence_followup_requested(raw_message: str, current_artifact: Dict[str, Any]) -> bool:
	artifact = _clean_dict(current_artifact)
	if _clean_text(artifact.get("family_id")).lower() != "entity_detail":
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


def _visible_followup_authority_intent(
	*,
	raw_message: str = "",
	nbu_trace_payload: Dict[str, Any] | None,
	reasoning_semantic_result: Any = None,
) -> str:
	if looks_like_predictive_guarantee_claim(raw_message):
		return "prediction_boundary"
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
	nbu_trace_payload: Dict[str, Any] | None = None,
	reasoning_semantic_result: Any = None,
) -> str:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _entity_label(entity)
	rank = int(resolution.get("resolved_rank") or _row_rank(row, 0) or 0)
	rank_text = f"Rank {rank}" if rank > 0 else "The selected row"
	explain_row_signal = _should_explain_row_signal(
		row,
		nbu_trace_payload=nbu_trace_payload,
		reasoning_semantic_result=reasoning_semantic_result,
	)
	if not explain_row_signal and _clean_text(resolution.get("target_reference")).lower() == "selected_entity":
		explain_row_signal = bool(_risk_signal_lines(row))
	if explain_row_signal:
		lines = [
			f"{label} is the {rank_text.lower()} entry in the table above.",
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
	if authority_intent == "prediction_boundary":
		lines = [
			f"I can show the facts for {rank_text}, but I can't safely predict whether {label} will default from this table alone.",
			"",
			f"Facts from the table above for {label}:",
		]
		next_step = "To answer that as a prediction, we would need an approved prediction model or policy plus payment-history and trend evidence."
	elif authority_intent == "recommendation_boundary":
		if _tokens(raw_message).intersection({"collect", "collection", "chase", "call"}):
			lines = [
				"I can show the facts from the table above, but I can't choose who you should collect from first without an approved business rule for that decision.",
				"",
				f"Facts from the table above for {rank_text} ({label}):",
			]
			next_step = "If you approve a collection-priority policy, I can use it to turn this evidence into a recommendation."
		else:
			lines = [
				"I can show the facts from the table above, but I can't make an action recommendation without an approved business rule for that decision.",
				"",
				f"Facts from the table above for {rank_text} ({label}):",
			]
			next_step = "If you approve the relevant decision policy, I can use it to turn this evidence into a recommendation."
	elif authority_intent == "causal_boundary":
		lines = [
			f"I can show the facts for {rank_text}, but I can't prove what caused the change from this single displayed result.",
			"",
			f"Facts from the table above for {label}:",
		]
		next_step = "To explain cause or change, we would need a trend, payment-behavior, or transaction-history view."
	else:
		return _resolved_answer_text(raw_message, resolution)
	metric_lines = _row_metric_lines(row, identity_label=label)
	if metric_lines:
		lines.extend(metric_lines)
	lines.append("")
	lines.append(next_step)
	return "\n".join(line for line in lines if line is not None).strip()


def _ambiguity_options_from_resolution(resolution: Dict[str, Any]) -> List[str]:
	return [_clean_text(value) for value in _clean_list(resolution.get("ambiguity_options")) if _clean_text(value)]


def _clarification_text(resolution: Dict[str, Any]) -> str:
	options = _ambiguity_options_from_resolution(resolution)
	lines = ["I can help, but I need which row you mean from the current result."]
	if options:
		lines.append("")
		lines.append("Current options:")
		for index, option in enumerate(options[:10], start=1):
			lines.append(f"- Rank {index}: {option}")
	lines.append("")
	lines.append('For example, ask "explain rank 2" or name the customer/item/supplier.')
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
	return {
		"type": "qwen_visible_context_followup_trace_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"session_id": _clean_text(session_id),
		"user_id": _clean_text(user_id),
		"site_name": _clean_text(site_name),
		"raw_message": _clean_text(raw_message),
		"resolution": resolution,
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
	if status not in {"resolved", "ambiguous", "out_of_range"}:
		return False, None
	if (
		status == "ambiguous"
		and _clean_text(resolution.get("target_reference")).lower() == "current_artifact"
		and artifact_level_visible_context_requested(raw_message)
	):
		artifacts = _context_artifacts(session_doc, current_artifact=_clean_dict(current_artifact), limit=1)
		answer_text = _artifact_field_boundary_answer(
			raw_message=raw_message,
			artifact_payload=artifacts[0] if artifacts else _clean_dict(current_artifact),
		)
		if not answer_text:
			return False, None
		answer_mode = "visible_context_boundary"
		authority_intent = "safe_visible_fact"
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
		answer_mode = "visible_context_answer" if status == "resolved" else "visible_context_clarification"
		answer_text = (
			_resolved_answer_text(
				raw_message,
				resolution,
				nbu_trace_payload=nbu_trace_payload,
				reasoning_semantic_result=reasoning_semantic_result,
			)
			if status == "resolved"
			else _clarification_text(resolution)
		)
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
