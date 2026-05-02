from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .natural_business_understanding_context_graph import resolve_nbu_context_graph_reference
from .natural_business_understanding_context_resolution import (
	nbu_artifact_rows,
	nbu_row_identity_label,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_request_classification import (
	visible_context_reference_requested,
	visible_context_target_reference,
)
from .natural_business_understanding_visible_artifacts import session_visible_rendered_artifacts


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

	primary_tool_artifacts, secondary_tool_artifacts, fallback_tool_artifacts = _session_tool_artifact_groups(session_doc, limit=limit)
	for payload in primary_tool_artifacts:
		append(payload)
	for payload in session_visible_rendered_artifacts(session_doc, limit=limit):
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


def _resolve_visible_context(
	*,
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
) -> Dict[str, Any]:
	target = _target_reference(raw_message)
	if target == "selected_entity":
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


def _is_risk_explanation(message: str) -> bool:
	return bool(_tokens(message).intersection({"risk", "risky", "highlighted", "concern", "concerns"}))


def _visible_followup_authority_intent(message: str) -> str:
	tokens = _tokens(message)
	text = f" {_clean_text(message).lower()} "
	prediction_terms = {"predict", "prediction", "forecast", "probability", "chance", "likely", "default"}
	future_terms = {"will", "would", "next", "future", "soon", "month", "week", "quarter", "year"}
	recommendation_terms = {
		"should",
		"recommend",
		"recommendation",
		"priority",
		"prioritize",
		"collect",
		"collection",
		"chase",
		"call",
		"approve",
		"pay",
		"buy",
		"reorder",
		"restock",
		"action",
		"decision",
	}
	causal_terms = {"cause", "caused", "causing", "increase", "increased", "decrease", "decreased", "changed", "change", "worse", "improved"}
	if tokens.intersection(prediction_terms) and (tokens.intersection(future_terms) or "default" in tokens):
		return "prediction_boundary"
	if tokens.intersection(recommendation_terms) or {"what", "should"}.issubset(tokens):
		return "recommendation_boundary"
	if tokens.intersection(causal_terms):
		return "causal_boundary"
	return "safe_visible_fact"


def _resolved_answer_text(raw_message: str, resolution: Dict[str, Any]) -> str:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _entity_label(entity)
	rank = int(resolution.get("resolved_rank") or _row_rank(row, 0) or 0)
	rank_text = f"Rank {rank}" if rank > 0 else "The selected row"
	if _is_risk_explanation(raw_message):
		lines = [
			f"{label} is the {rank_text.lower()} entry in the current ERP result.",
			"",
			"Visible evidence from that row:",
		]
	else:
		lines = [f"{rank_text} is {label} in the current ERP result."]
	metric_lines = _row_metric_lines(row, identity_label=label)
	if metric_lines:
		if not _is_risk_explanation(raw_message):
			lines.append("")
			lines.append("Current row facts:")
		lines.extend(metric_lines)
	lines.append("")
	lines.append("This uses only the ERP result already shown in this conversation.")
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
			f"I can show the current ERP evidence for {rank_text}, but I can't safely predict whether {label} will default from this table alone.",
			"",
			f"Current visible evidence for {label}:",
		]
		next_step = "To answer that as a prediction, we would need an approved prediction model or policy plus payment-history and trend evidence."
	elif authority_intent == "recommendation_boundary":
		if _tokens(raw_message).intersection({"collect", "collection", "chase", "call"}):
			lines = [
				"I can show the current ERP evidence, but I can't choose who you should collect from first without an approved business rule for that decision.",
				"",
				f"Current visible evidence for {rank_text} ({label}):",
			]
			next_step = "If you approve a collection-priority policy, I can use it to turn this evidence into a recommendation."
		else:
			lines = [
				"I can show the current ERP evidence, but I can't make an action recommendation without an approved business rule for that decision.",
				"",
				f"Current visible evidence for {rank_text} ({label}):",
			]
			next_step = "If you approve the relevant decision policy, I can use it to turn this evidence into a recommendation."
	elif authority_intent == "causal_boundary":
		lines = [
			f"I can show the current ERP evidence for {rank_text}, but I can't prove what caused the change from this single displayed result.",
			"",
			f"Current visible evidence for {label}:",
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

	resolution = _resolve_visible_context(
		session_doc=session_doc,
		raw_message=raw_message,
		current_artifact=_clean_dict(current_artifact),
	)
	status = _clean_text(resolution.get("status")).lower()
	if status not in {"resolved", "ambiguous", "out_of_range"}:
		return False, None

	authority_intent = _visible_followup_authority_intent(raw_message)
	if status == "resolved" and authority_intent != "safe_visible_fact":
		answer_mode = "visible_context_boundary"
		answer_text = _boundary_answer_text(raw_message, resolution, authority_intent=authority_intent)
	else:
		answer_mode = "visible_context_answer" if status == "resolved" else "visible_context_clarification"
		answer_text = _resolved_answer_text(raw_message, resolution) if status == "resolved" else _clarification_text(resolution)
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
