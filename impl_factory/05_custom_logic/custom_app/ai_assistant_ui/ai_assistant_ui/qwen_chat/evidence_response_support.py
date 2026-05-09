from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.boundary_support import (
	build_grounded_artifact_direct_evidence_rendered_payload,
	grounded_artifact_direct_evidence_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	build_entity_detail_clarification_signal_contract,
	build_entity_detail_evidence_request_contract,
	build_followup_resolution_contract,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_contracts import CONTRACT_VERSION
from ai_assistant_ui.qwen_chat.natural_business_understanding_context_resolution import (
	nbu_row_entity_payload,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys
from ai_assistant_ui.qwen_chat.source_detail_drilldown_execution import (
	build_source_detail_drilldown_payload_from_artifact_line,
	source_detail_artifact_line_from_message,
)


def entity_detail_evidence_request_payload(
	*,
	request_id: str,
	raw_message: str,
	artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	if str(artifact.get("family_id") or "").strip() != "entity_detail":
		return {}
	return build_entity_detail_evidence_request_contract(
		request_id=request_id,
		raw_message=raw_message,
		artifact_payload=artifact,
	).to_payload()


def entity_detail_clarification_signal_payload(
	*,
	request_id: str,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any],
) -> Dict[str, Any]:
	clarification_signal = build_entity_detail_clarification_signal_contract(
		request_id=request_id,
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		evidence_request_contract=evidence_request_contract,
	)
	return clarification_signal.to_payload() if clarification_signal is not None else {}


def _direct_evidence_response_payload(
	*,
	answer_text: str,
	rendered_response_payload: Dict[str, Any] | None = None,
	narrative_payload: Dict[str, Any] | None = None,
	narrative_contract_payload: Dict[str, Any] | None = None,
	clarification_signal_payload: Dict[str, Any] | None = None,
	evidence_request_contract_payload: Dict[str, Any] | None = None,
	selected_entity_activation_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	return {
		"answer_text": str(answer_text or "").strip(),
		"rendered_response_payload": dict(rendered_response_payload or {}),
		"narrative_payload": dict(narrative_payload or {}),
		"narrative_contract_payload": dict(narrative_contract_payload or {}),
		"clarification_signal_payload": dict(clarification_signal_payload or {}),
		"evidence_request_contract_payload": dict(evidence_request_contract_payload or {}),
		"selected_entity_activation_payload": dict(selected_entity_activation_payload or {}),
	}


def _selected_row_activation_payload(
	*,
	request_id: str,
	artifact_payload: Dict[str, Any],
	focused_row: Dict[str, Any],
	activation_mode: str,
	reason: str,
) -> Dict[str, Any]:
	row = dict(focused_row or {}) if isinstance(focused_row, dict) else {}
	if not row:
		return {}
	artifact = dict(artifact_payload or {}) if isinstance(artifact_payload, dict) else {}
	entity = nbu_row_entity_payload(row, artifact, {"target_reference": "selected_entity"})
	if not entity:
		return {}
	try:
		resolved_rank = int(row.get("rank") or row.get("row_rank") or row.get("position") or 0)
	except (TypeError, ValueError):
		resolved_rank = 0
	return {
		"type": "qwen_nbu_current_artifact_answer_activation_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": str(request_id or "").strip(),
		"activation_state": "activated",
		"activation_mode": str(activation_mode or "direct_evidence_selected_row").strip(),
		"activation_level": "grounded_direct_evidence",
		"live_execution_enabled": True,
		"runtime_execution_enabled": False,
		"resolved_artifact_id": str(
			artifact.get("artifact_id")
			or artifact.get("request_id")
			or artifact.get("title")
			or artifact.get("family_id")
			or ""
		).strip(),
		"resolved_rank": resolved_rank,
		"resolved_entity": entity,
		"reason": str(reason or "The direct evidence answer selected a focused row from the current governed artifact.").strip(),
	}


def preserve_artifact_boundary_clarification_followup_resolution(
	*,
	request_id: str,
	followup_resolution,
	clarification_continuation_active: bool,
	latest_grounded_turn_available: bool,
):
	if not clarification_continuation_active or followup_resolution is None:
		return followup_resolution
	if str(getattr(followup_resolution, "mode", "") or "").strip() != "capability_requery":
		return followup_resolution
	requested_modes = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	]
	if "entity_detail_evidence" not in requested_modes:
		requested_modes.append("entity_detail_evidence")
	return build_followup_resolution_contract(
		request_id=request_id,
		mode="grounded_follow_up",
		requested_modes=requested_modes,
		target_dimension=str(getattr(followup_resolution, "target_dimension", "") or "").strip(),
		target_limit=int(max(0, getattr(followup_resolution, "target_limit", 0) or 0)),
		sort_direction=str(getattr(followup_resolution, "sort_direction", "") or "").strip(),
		target_metric=str(getattr(followup_resolution, "target_metric", "") or "").strip(),
		requested_columns=list(getattr(followup_resolution, "requested_columns", []) or []),
		requested_time_scope=str(getattr(followup_resolution, "requested_time_scope", "") or "").strip(),
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=bool(latest_grounded_turn_available),
		reason=(
			"A resolved artifact-boundary clarification must continue on the current governed artifact "
			"before any governed requery breakout."
		),
	)


def preserve_current_artifact_direct_evidence_followup_resolution(
	*,
	request_id: str,
	followup_resolution,
	evidence_request_contract: Dict[str, Any] | None,
	direct_evidence_answer: str,
	evidence_boundary_answer: str,
	latest_grounded_turn_available: bool,
):
	if followup_resolution is None or not bool(latest_grounded_turn_available):
		return followup_resolution
	evidence_contract = (
		dict(evidence_request_contract)
		if isinstance(evidence_request_contract, dict)
		else {}
	)
	clarification_required = bool(evidence_contract.get("clarification_required"))
	if not clarification_required and not str(direct_evidence_answer or evidence_boundary_answer or "").strip():
		return followup_resolution
	requested_modes = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(value or "").strip()
	]
	preserved_mode = "entity_detail_evidence" if clarification_required else "direct_evidence_followup"
	if preserved_mode not in requested_modes:
		requested_modes.append(preserved_mode)
	return build_followup_resolution_contract(
		request_id=request_id,
		mode="grounded_follow_up",
		requested_modes=requested_modes,
		target_dimension=str(getattr(followup_resolution, "target_dimension", "") or "").strip(),
		target_limit=int(max(0, getattr(followup_resolution, "target_limit", 0) or 0)),
		sort_direction=str(getattr(followup_resolution, "sort_direction", "") or "").strip(),
		target_metric=str(getattr(followup_resolution, "target_metric", "") or "").strip(),
		requested_columns=list(getattr(followup_resolution, "requested_columns", []) or []),
		requested_time_scope=str(getattr(followup_resolution, "requested_time_scope", "") or "").strip(),
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=True,
		reason=(
			"The current grounded artifact already contains the direct evidence needed for this "
			"follow-up, so the turn should stay on the current artifact instead of breaking out "
			"to a fresh governed query."
		),
	)


def _direct_evidence_response_should_use_deterministic_rendering(
	*,
	artifact_payload: Dict[str, Any],
	evidence_request_contract: Dict[str, Any],
	requested_dimensions: set[str],
) -> bool:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	entity_type = str(dimensions.get("entity_type") or "").strip().lower()
	entity_question_type = str(
		evidence_request_contract.get("entity_question_type")
		or evidence_request_contract.get("question_type")
		or ""
	).strip()
	if entity_type == "item" and entity_question_type == "item_stock_position":
		return True
	if entity_type == "purchase_order":
		return True
	if "posting_date" in requested_dimensions:
		return True
	if entity_type == "sales_order" and "planned_delivery_date" in requested_dimensions:
		return True
	return False


def _source_detail_direct_evidence_response(
	*,
	request_id: str,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	interaction_contract,
	clarification_signal_payload: Dict[str, Any] | None = None,
	evidence_request_contract_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	_section_key, focused_row = source_detail_artifact_line_from_message(raw_message, artifact_payload)
	if not focused_row:
		return {}
	source_detail_payload = build_source_detail_drilldown_payload_from_artifact_line(
		artifact_payload=artifact_payload,
		focused_row=focused_row,
		user_id=str(getattr(interaction_contract, "user_id", "") or "").strip(),
	)
	answer_text = str(source_detail_payload.get("answer_text") or "").strip()
	if not answer_text:
		return {}
	rendered_response_payload = {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"renderer_id": "governed_source_detail_drilldown",
		"rendering_policy": "deterministic",
		"answer_text": answer_text,
		"source_detail_drilldown": True,
	}
	return _direct_evidence_response_payload(
		answer_text=answer_text,
		rendered_response_payload=rendered_response_payload,
		narrative_payload=source_detail_payload,
		narrative_contract_payload={
			"narrative_engine": "governed_source_detail_drilldown",
			"reason": str(source_detail_payload.get("reason") or "").strip(),
		},
		clarification_signal_payload=clarification_signal_payload,
		evidence_request_contract_payload=evidence_request_contract_payload,
		selected_entity_activation_payload=_selected_row_activation_payload(
			request_id=request_id,
			artifact_payload=artifact_payload,
			focused_row=focused_row,
			activation_mode="source_detail_selected_row",
			reason="The source-detail response selected a focused row from the current governed artifact.",
		),
	)


def grounded_artifact_direct_evidence_response(
	*,
	request_id: str,
	session_id: str,
	interaction_contract,
	response_policy_contract,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	fallback_answer_text: str = "",
) -> Dict[str, Any]:
	evidence_request_contract = entity_detail_evidence_request_payload(
		request_id=request_id,
		raw_message=raw_message,
		artifact_payload=artifact_payload,
	)
	fallback_text = str(fallback_answer_text or "").strip()
	if not fallback_text:
		fallback_text = grounded_artifact_direct_evidence_answer(
			raw_message=raw_message,
			artifact_payload=artifact_payload,
			grounded_turn=grounded_turn,
			evidence_request_contract=evidence_request_contract,
		)
	if not fallback_text:
		return {}
	clarification_signal_payload = entity_detail_clarification_signal_payload(
		request_id=request_id,
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		evidence_request_contract=evidence_request_contract,
	)
	if not clarification_signal_payload:
		source_detail_response = _source_detail_direct_evidence_response(
			request_id=request_id,
			raw_message=raw_message,
			artifact_payload=artifact_payload,
			interaction_contract=interaction_contract,
			clarification_signal_payload=clarification_signal_payload,
			evidence_request_contract_payload=evidence_request_contract,
		)
		if source_detail_response:
			return source_detail_response
	requested_dimensions = {
		str(value or "").strip()
		for value in detect_canonical_keys(raw_message, dimension_or_metric="dimension")
		if str(value or "").strip()
	}
	_section_key, focused_row = source_detail_artifact_line_from_message(raw_message, artifact_payload)
	selected_entity_activation_payload = _selected_row_activation_payload(
		request_id=request_id,
		artifact_payload=artifact_payload,
		focused_row=focused_row,
		activation_mode="direct_evidence_selected_row",
		reason="The direct evidence answer selected a focused row from the current governed artifact.",
	)
	entity_type = str((artifact_payload.get("dimensions") or {}).get("entity_type") or "").strip().lower()
	rendered_response_payload = build_grounded_artifact_direct_evidence_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
		evidence_request_contract=evidence_request_contract,
	)
	if clarification_signal_payload:
		return _direct_evidence_response_payload(
			answer_text=fallback_text,
			clarification_signal_payload=clarification_signal_payload,
			evidence_request_contract_payload=evidence_request_contract,
			selected_entity_activation_payload=selected_entity_activation_payload,
		)
	if not rendered_response_payload:
		return _direct_evidence_response_payload(
			answer_text=fallback_text,
			clarification_signal_payload=clarification_signal_payload,
			evidence_request_contract_payload=evidence_request_contract,
			selected_entity_activation_payload=selected_entity_activation_payload,
		)
	if str(rendered_response_payload.get("rendering_policy") or "").strip() == "deterministic":
		rendered_response_payload["answer_text"] = fallback_text
		return _direct_evidence_response_payload(
			answer_text=fallback_text,
			rendered_response_payload=rendered_response_payload,
			clarification_signal_payload=clarification_signal_payload,
			evidence_request_contract_payload=evidence_request_contract,
			selected_entity_activation_payload=selected_entity_activation_payload,
		)
	if _direct_evidence_response_should_use_deterministic_rendering(
		artifact_payload=artifact_payload,
		evidence_request_contract=evidence_request_contract,
		requested_dimensions=requested_dimensions,
	):
		rendered_response_payload["answer_text"] = fallback_text
		return _direct_evidence_response_payload(
			answer_text=fallback_text,
			rendered_response_payload=rendered_response_payload,
			clarification_signal_payload=clarification_signal_payload,
			evidence_request_contract_payload=evidence_request_contract,
			selected_entity_activation_payload=selected_entity_activation_payload,
		)
	rendered_response_payload["answer_text"] = fallback_text
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=artifact_payload,
		rendered_response_payload=rendered_response_payload,
		response_policy=response_policy_contract.to_runtime_payload(),
		validation_payload={},
	)
	narrative_payload = narrate_governed_artifact(
		session_id=session_id,
		user_id=str(interaction_contract.user_id or "").strip(),
		site_name=str(interaction_contract.site_name or "").strip(),
		message=raw_message,
		request_id=request_id,
		artifact_context=artifact_context,
		response_policy=response_policy_contract.to_runtime_payload(),
	)
	narrative_contract = build_artifact_narrative_contract(
		request_id=request_id,
		artifact_context=artifact_context,
		runtime_payload=narrative_payload,
	)
	narrative_contract_payload = narrative_contract.to_payload() if narrative_contract is not None else {}
	answer_text = str(narrative_contract_payload.get("answer_text") or "").strip() or fallback_text
	return _direct_evidence_response_payload(
		answer_text=answer_text,
		rendered_response_payload=rendered_response_payload,
		narrative_payload=narrative_payload if isinstance(narrative_payload, dict) else {},
		narrative_contract_payload=narrative_contract_payload,
		clarification_signal_payload=clarification_signal_payload,
		evidence_request_contract_payload=evidence_request_contract,
		selected_entity_activation_payload=selected_entity_activation_payload,
	)
