from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import ExecutionPath, build_audit_envelope
from ai_assistant_ui.qwen_chat.knowledge_boundary import render_knowledge_boundary_answer


def handle_artifact_boundary_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	message: str,
	followup_resolution,
	interaction_contract,
	frontdoor_contract,
	scope_decision_contract,
	latest_family_artifact: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	enrichment_compatibility_contract,
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
	save_session: Callable[..., None],
) -> Tuple[bool, Dict[str, Any] | None]:
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
		boundary_payload = append_knowledge_boundary_contract(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			proposed_lane="artifact_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			governed_scope_contract=scope_decision_contract.to_payload(),
			grounded_turn=latest_grounded_turn,
		)
		append_grounded_evidence_recovery_contract(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
			followup_resolution=followup_resolution,
			reason=execution_path.reason,
		)
		recovery_payload = latest_tool_payload_by_type(
			session_tool_payloads(session_doc),
			"qwen_artifact_enrichment_recovery_contract",
		)
		answer_text = render_knowledge_boundary_answer(
			boundary_contract=boundary_payload,
			detail_answer=evidence_boundary_answer,
		)
		append_artifact_boundary_observability(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			boundary_name="grounded_evidence_boundary",
			latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
			recovery_payload=recovery_payload,
			grounded_turn_available=bool(latest_grounded_turn),
		)
		append_tool_payload(session_doc, execution_path.to_payload())
		append_message(session_doc, "assistant", assistant_text_payload(answer_text))
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={},
				grounded_turn_context=latest_grounded_turn,
				answer_text=answer_text,
			).to_payload(),
		)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": True,
			"request_id": request_id,
			"mode": "grounded_evidence_boundary",
			"agent_meta": {"engine": "local_grounded_boundary"},
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
	boundary_payload = append_knowledge_boundary_contract(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		proposed_lane="artifact_lane",
		front_door_contract=frontdoor_contract.to_payload(),
		governed_scope_contract=scope_decision_contract.to_payload(),
		grounded_turn=latest_grounded_turn,
	)
	append_enrichment_recovery_contract(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		compatibility_contract=enrichment_compatibility_contract,
		grounded_turn=latest_grounded_turn,
		followup_resolution=followup_resolution,
	)
	recovery_payload = latest_tool_payload_by_type(
		session_tool_payloads(session_doc),
		"qwen_artifact_enrichment_recovery_contract",
	)
	answer_text = render_knowledge_boundary_answer(
		boundary_contract=boundary_payload,
		detail_answer=enrichment_boundary_answer,
	)
	append_artifact_boundary_observability(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		boundary_name="artifact_enrichment_boundary",
		latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
		recovery_payload=recovery_payload,
		grounded_turn_available=bool(latest_grounded_turn),
	)
	append_tool_payload(session_doc, execution_path.to_payload())
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={},
			grounded_turn_context=latest_grounded_turn,
			answer_text=answer_text,
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "artifact_enrichment_boundary",
		"agent_meta": {"engine": "local_grounded_boundary"},
	}
