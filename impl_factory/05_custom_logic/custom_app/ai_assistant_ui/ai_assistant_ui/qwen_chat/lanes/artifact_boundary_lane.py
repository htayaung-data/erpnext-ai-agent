from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import ExecutionPath
from ai_assistant_ui.qwen_chat.knowledge_boundary import render_knowledge_boundary_answer


class _ToolPayloadCollector:
	def __init__(self) -> None:
		self.messages = []

	def append(self, fieldname: str, value: Dict[str, Any]) -> None:
		if str(fieldname or "").strip() == "messages":
			self.messages.append(value)


def _payloads_from_collector(collector: _ToolPayloadCollector) -> list[Dict[str, Any]]:
	payloads: list[Dict[str, Any]] = []
	for row in list(getattr(collector, "messages", []) or []):
		if not isinstance(row, dict) or str(row.get("role") or "").strip() != "tool":
			continue
		content = row.get("content")
		payload = content if isinstance(content, dict) else {}
		if not payload:
			try:
				decoded = json.loads(str(content or ""))
			except Exception:
				decoded = {}
			payload = decoded if isinstance(decoded, dict) else {}
		if payload:
			payloads.append(payload)
	return payloads


def _collect_tool_payloads(builder: Callable[..., Dict[str, Any]], **kwargs) -> tuple[Dict[str, Any], list[Dict[str, Any]]]:
	collector = _ToolPayloadCollector()
	payload = builder(collector, **kwargs)
	payloads = _payloads_from_collector(collector)
	if isinstance(payload, dict) and payload and payload not in payloads:
		payloads.append(payload)
	return payload if isinstance(payload, dict) else {}, payloads


def _collect_observability_payloads(builder: Callable[..., None], **kwargs) -> list[Dict[str, Any]]:
	collector = _ToolPayloadCollector()
	builder(collector, **kwargs)
	return _payloads_from_collector(collector)


def handle_artifact_boundary_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	message: str,
	followup_resolution,
	interaction_contract,
	response_policy_contract,
	frontdoor_contract,
	scope_decision_contract,
	latest_family_artifact: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	enrichment_compatibility_contract,
	precomputed_evidence_response: Dict[str, Any] | None = None,
	precomputed_evidence_answer: str = "",
	grounded_artifact_direct_evidence_response: Callable[..., Dict[str, Any]],
	grounded_artifact_direct_evidence_answer: Callable[..., str],
	precomputed_evidence_boundary_answer: str = "",
	grounded_artifact_evidence_boundary_answer: Callable[..., str],
	artifact_enrichment_boundary_answer: Callable[..., str],
	append_grounded_evidence_recovery_contract: Callable[..., Dict[str, Any]],
	append_enrichment_recovery_contract: Callable[..., Dict[str, Any]],
	session_tool_payloads: Callable[..., list],
	latest_tool_payload_by_type: Callable[..., Dict[str, Any]],
	append_artifact_boundary_observability: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	append_tool_payload: Callable[..., None],
	append_message: Callable[..., None],
	assistant_text_payload: Callable[[str], str],
	store_pending_clarification_signal: Callable[..., None],
	save_session: Callable[..., None],
	clear_pending_clarification_signal: Callable[..., None] | None = None,
) -> Tuple[bool, Dict[str, Any] | None]:
	evidence_response = dict(precomputed_evidence_response or {}) if isinstance(precomputed_evidence_response, dict) else {}
	if not evidence_response:
		evidence_response = grounded_artifact_direct_evidence_response(
			request_id=request_id,
			session_id=session_id,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			raw_message=message,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
			fallback_answer_text=str(precomputed_evidence_answer or "").strip(),
		)
	evidence_answer = str(
		evidence_response.get("answer_text")
		or precomputed_evidence_answer
		or ""
	).strip()
	if not evidence_answer:
		evidence_answer = grounded_artifact_direct_evidence_answer(
			raw_message=message,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
		)
	if evidence_answer:
		execution_path = ExecutionPath(
			request_id=request_id,
			path="grounded_evidence_answer",
			reason="The current governed artifact contains direct ERP evidence for the requested operational status.",
			requires_runtime=False,
			grounded_required=True,
		)
		narrative_contract_payload = (
			evidence_response.get("narrative_contract_payload")
			if isinstance(evidence_response.get("narrative_contract_payload"), dict)
			else {}
		)
		evidence_request_contract_payload = (
			evidence_response.get("evidence_request_contract_payload")
			if isinstance(evidence_response.get("evidence_request_contract_payload"), dict)
			else {}
		)
		clarification_signal_payload = (
			evidence_response.get("clarification_signal_payload")
			if isinstance(evidence_response.get("clarification_signal_payload"), dict)
			else {}
		)
		selected_entity_activation_payload = (
			evidence_response.get("selected_entity_activation_payload")
			if isinstance(evidence_response.get("selected_entity_activation_payload"), dict)
			else {}
		)
		pre_assistant_tool_payloads = [execution_path.to_payload()]
		if evidence_request_contract_payload:
			pre_assistant_tool_payloads.append(evidence_request_contract_payload)
		if narrative_contract_payload:
			pre_assistant_tool_payloads.append(narrative_contract_payload)
		if selected_entity_activation_payload:
			pre_assistant_tool_payloads.append(selected_entity_activation_payload)
		if clarification_signal_payload:
			pre_assistant_tool_payloads.append(clarification_signal_payload)
		narrative_engine = str(
			narrative_contract_payload.get("narrative_engine")
			or "local_grounded_evidence"
		).strip()
		# EC-4R1 evidence authority checkpoint: staged evidence payloads are appended only by this helper.
		authorized_emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=evidence_answer,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={
				"agent_meta": {
					"engine": narrative_engine,
					"mode": "grounded_evidence_answer",
				}
			},
			grounded_turn_context=latest_grounded_turn,
			authority_context={"normalized_family_artifact": latest_family_artifact},
			pre_assistant_tool_payloads=pre_assistant_tool_payloads,
		)
		if not authorized_emission.emitted:
			save_session(session_doc, ignore_permissions=False)
			return False, {
				"ok": False,
				"request_id": request_id,
				"mode": "grounded_evidence_answer",
				"agent_meta": {
					"engine": narrative_engine,
					"authorized_emission": authorized_emission.to_payload(),
				},
			}
		if clarification_signal_payload:
			store_pending_clarification_signal(session_doc, clarification_signal_payload)
		elif callable(clear_pending_clarification_signal):
			clear_pending_clarification_signal(session_doc)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": True,
			"request_id": request_id,
			"mode": "grounded_evidence_answer",
			"agent_meta": {
				"engine": narrative_engine,
				"authorized_emission": authorized_emission.to_payload(),
			},
		}

	evidence_boundary_answer = str(precomputed_evidence_boundary_answer or "").strip()
	if not evidence_boundary_answer:
		evidence_boundary_answer = grounded_artifact_evidence_boundary_answer(
			raw_message=message,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
		)
	if evidence_boundary_answer:
		boundary_started_at = time.perf_counter()
		execution_path = ExecutionPath(
			request_id=request_id,
			path="grounded_evidence_boundary",
			reason="The current governed artifact does not contain direct ERP evidence for the requested operational status.",
			requires_runtime=False,
			grounded_required=True,
		)
		boundary_payload, boundary_payloads = _collect_tool_payloads(
			append_knowledge_boundary_contract,
			request_id=request_id,
			session_id=session_id,
			proposed_lane="artifact_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			governed_scope_contract=scope_decision_contract.to_payload(),
			grounded_turn=latest_grounded_turn,
		)
		recovery_payload, recovery_payloads = _collect_tool_payloads(
			append_grounded_evidence_recovery_contract,
			request_id=request_id,
			session_id=session_id,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
			followup_resolution=followup_resolution,
			reason=execution_path.reason,
		)
		answer_text = render_knowledge_boundary_answer(
			boundary_contract=boundary_payload,
			detail_answer=evidence_boundary_answer,
		)
		observability_payloads = _collect_observability_payloads(
			append_artifact_boundary_observability,
			request_id=request_id,
			session_id=session_id,
			boundary_name="grounded_evidence_boundary",
			latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
			recovery_payload=recovery_payload,
			grounded_turn_available=bool(latest_grounded_turn),
		)
		# EC-4R1 grounded-boundary authority checkpoint: recovery payloads stay staged until allowed.
		authorized_emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=answer_text,
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={
				"agent_meta": {
					"engine": "local_grounded_boundary",
					"mode": "grounded_evidence_boundary",
				}
			},
			grounded_turn_context={},
			authority_context={"knowledge_boundary": boundary_payload},
			pre_assistant_tool_payloads=[
				*boundary_payloads,
				*recovery_payloads,
				*observability_payloads,
				execution_path.to_payload(),
			],
		)
		if not authorized_emission.emitted:
			save_session(session_doc, ignore_permissions=False)
			return False, {
				"ok": False,
				"request_id": request_id,
				"mode": "grounded_evidence_boundary",
				"agent_meta": {
					"engine": "local_grounded_boundary",
					"authorized_emission": authorized_emission.to_payload(),
				},
			}
		if callable(clear_pending_clarification_signal):
			clear_pending_clarification_signal(session_doc)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": True,
			"request_id": request_id,
			"mode": "grounded_evidence_boundary",
			"agent_meta": {
				"engine": "local_grounded_boundary",
				"authorized_emission": authorized_emission.to_payload(),
			},
		}

	if enrichment_compatibility_contract is None or bool(getattr(enrichment_compatibility_contract, "compatible", False)):
		return False, None

	enrichment_boundary_answer = artifact_enrichment_boundary_answer(
		followup_resolution=followup_resolution,
		compatibility_contract=enrichment_compatibility_contract,
	)
	if not enrichment_boundary_answer:
		return False, None

	boundary_started_at = time.perf_counter()
	execution_path = ExecutionPath(
		request_id=request_id,
		path="artifact_enrichment_boundary",
		reason=str(getattr(enrichment_compatibility_contract, "reason", "") or "").strip()
		or "The current governed artifact cannot be enriched safely with the requested columns or metrics.",
		requires_runtime=False,
		grounded_required=True,
	)
	boundary_payload, boundary_payloads = _collect_tool_payloads(
		append_knowledge_boundary_contract,
		request_id=request_id,
		session_id=session_id,
		proposed_lane="artifact_lane",
		front_door_contract=frontdoor_contract.to_payload(),
		governed_scope_contract=scope_decision_contract.to_payload(),
		grounded_turn=latest_grounded_turn,
	)
	recovery_payload, recovery_payloads = _collect_tool_payloads(
		append_enrichment_recovery_contract,
		request_id=request_id,
		session_id=session_id,
		compatibility_contract=enrichment_compatibility_contract,
		grounded_turn=latest_grounded_turn,
		followup_resolution=followup_resolution,
	)
	answer_text = render_knowledge_boundary_answer(
		boundary_contract=boundary_payload,
		detail_answer=enrichment_boundary_answer,
	)
	observability_payloads = _collect_observability_payloads(
		append_artifact_boundary_observability,
		request_id=request_id,
		session_id=session_id,
		boundary_name="artifact_enrichment_boundary",
		latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
		recovery_payload=recovery_payload,
		grounded_turn_available=bool(latest_grounded_turn),
	)
	# EC-4R1 enrichment-boundary authority checkpoint: recovery payloads stay staged until allowed.
	authorized_emission = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		runtime_trace_payload={
			"agent_meta": {
				"engine": "local_grounded_boundary",
				"mode": "artifact_enrichment_boundary",
			}
		},
		grounded_turn_context={},
		authority_context={"knowledge_boundary": boundary_payload},
		pre_assistant_tool_payloads=[
			*boundary_payloads,
			*recovery_payloads,
			*observability_payloads,
			execution_path.to_payload(),
		],
	)
	if not authorized_emission.emitted:
		save_session(session_doc, ignore_permissions=False)
		return False, {
			"ok": False,
			"request_id": request_id,
			"mode": "artifact_enrichment_boundary",
			"agent_meta": {
				"engine": "local_grounded_boundary",
				"authorized_emission": authorized_emission.to_payload(),
			},
		}
	if callable(clear_pending_clarification_signal):
		clear_pending_clarification_signal(session_doc)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "artifact_enrichment_boundary",
		"agent_meta": {
			"engine": "local_grounded_boundary",
			"authorized_emission": authorized_emission.to_payload(),
		},
	}
