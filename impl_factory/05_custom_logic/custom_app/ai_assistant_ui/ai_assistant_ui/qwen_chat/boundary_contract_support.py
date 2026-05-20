from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.contracts import (
	build_recovery_contract_from_enrichment_compatibility,
	build_recovery_contract_from_evidence_boundary,
)
from ai_assistant_ui.qwen_chat.knowledge_boundary import evaluate_knowledge_boundary


def append_knowledge_boundary_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	proposed_lane: str,
	clarification_resolution: Dict[str, Any] | None = None,
	clarification_reason: Dict[str, Any] | None = None,
	front_door_contract: Dict[str, Any] | None = None,
	governed_scope_contract: Dict[str, Any] | None = None,
	compiled_execution_audit: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
	reasoning_activation_contract: Dict[str, Any] | None = None,
	reasoning_contract: Dict[str, Any] | None = None,
	grounded_turn: Dict[str, Any] | None = None,
	append_tool_payload=None,
) -> Dict[str, Any]:
	boundary_payload = evaluate_knowledge_boundary(
		request_id=request_id,
		session_id=session_id,
		proposed_lane=proposed_lane,
		clarification_resolution=clarification_resolution,
		clarification_reason=clarification_reason,
		front_door_contract=front_door_contract,
		governed_scope_contract=governed_scope_contract,
		compiled_execution_audit=compiled_execution_audit,
		family_validation=family_validation,
		semantic_validation=semantic_validation,
		reasoning_activation_contract=reasoning_activation_contract,
		reasoning_contract=reasoning_contract,
		grounded_turn=grounded_turn,
	)
	append_tool_payload(session_doc, boundary_payload)
	return boundary_payload


def append_grounded_evidence_recovery_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	artifact_payload: Dict[str, Any] | None,
	grounded_turn: Dict[str, Any] | None,
	followup_resolution,
	reason: str,
	append_tool_payload=None,
) -> Dict[str, Any]:
	recovery_payload = build_recovery_contract_from_evidence_boundary(
		request_id=request_id,
		session_id=session_id,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
		followup_resolution=followup_resolution,
		reason=reason,
	).to_payload()
	append_tool_payload(session_doc, recovery_payload)
	return recovery_payload


def append_enrichment_recovery_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	compatibility_contract,
	grounded_turn: Dict[str, Any] | None,
	followup_resolution,
	append_tool_payload=None,
) -> Dict[str, Any]:
	recovery_payload = build_recovery_contract_from_enrichment_compatibility(
		request_id=request_id,
		session_id=session_id,
		compatibility_contract=compatibility_contract,
		grounded_turn=grounded_turn,
		followup_resolution=followup_resolution,
	).to_payload()
	append_tool_payload(session_doc, recovery_payload)
	return recovery_payload
