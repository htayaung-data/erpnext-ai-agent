from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.context.message_history import parse_payload


def latest_qwen_trace_payload(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		if str(payload.get("type") or "").strip().lower() == "qwen_runtime_trace":
			return payload
	return {}


def latest_grounded_assistant_context(session_doc: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
	messages = list(session_doc.get("messages") or [])
	for idx in range(len(messages) - 1, -1, -1):
		message = messages[idx]
		if str(message.role or "").strip().lower() != "tool":
			continue
		trace = parse_payload(str(message.content or ""))
		if str(trace.get("type") or "").strip().lower() != "qwen_runtime_trace":
			continue
		if not bool(trace.get("ok")):
			continue
		for prev_idx in range(idx - 1, -1, -1):
			prev = messages[prev_idx]
			role = str(prev.role or "").strip().lower()
			if role == "assistant":
				payload = parse_payload(str(prev.content or ""))
				if payload:
					return payload, trace
				text = str(prev.content or "").strip()
				if text:
					return {"type": "text", "text": text}, trace
				break
			if role == "user":
				break
	return {}, {}


def grounded_turn_source_request_id(payload: Dict[str, Any] | None) -> str:
	grounded_payload = dict(payload or {})
	if not bool(grounded_payload.get("grounded")):
		return ""
	return str(grounded_payload.get("trace_request_id") or grounded_payload.get("request_id") or "").strip()


def latest_grounded_turn_contract(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		if (
			str(payload.get("type") or "").strip().lower() == "qwen_grounded_turn_context"
			and grounded_turn_source_request_id(payload)
		):
			return payload
	return {}


def artifact_compatible_with_grounded_turn(*, artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> bool:
	artifact = dict(artifact_payload or {})
	grounded = dict(grounded_turn or {})
	if not artifact or not grounded:
		return False
	grounded_artifact_type = str(grounded.get("artifact_type") or "").strip()
	artifact_contract_type = str(artifact.get("type") or "").strip().lower()
	artifact_type = str(artifact.get("artifact_type") or artifact.get("type") or "").strip()
	if grounded_artifact_type == "normalized_composite_family_artifact":
		if artifact_contract_type != "qwen_composite_family_artifact" and artifact_type != "normalized_composite_family_artifact":
			return False
	grounded_request_id = str(grounded.get("trace_request_id") or grounded.get("request_id") or "").strip()
	artifact_request_id = str(artifact.get("request_id") or "").strip()
	if grounded_request_id and artifact_request_id:
		return grounded_request_id == artifact_request_id
	grounded_family_id = str(grounded.get("artifact_family_id") or "").strip()
	artifact_family_id = str(artifact.get("family_id") or "").strip()
	if grounded_family_id and artifact_family_id and grounded_family_id != artifact_family_id:
		return False
	grounded_reports = {
		str(value or "").strip()
		for value in (grounded.get("artifact_source_reports") or [])
		if str(value or "").strip()
	}
	artifact_reports = {
		str(value or "").strip()
		for value in (artifact.get("source_reports") or [])
		if str(value or "").strip()
	}
	if grounded_reports and artifact_reports:
		return grounded_reports == artifact_reports
	return bool(grounded_family_id and artifact_family_id and grounded_family_id == artifact_family_id)


def latest_normalized_family_artifact(
	session_doc: Any,
	*,
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	candidates: List[Dict[str, Any]] = []
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		payload_type = str(payload.get("type") or "").strip().lower()
		if payload_type in {
			"qwen_normalized_family_artifact_contract",
			"qwen_composite_family_artifact",
			"qwen_entity_detail_artifact",
		}:
			candidates.append(payload)
	if not candidates:
		return {}
	grounded = dict(grounded_turn or {})
	if grounded:
		for payload in candidates:
			if artifact_compatible_with_grounded_turn(artifact_payload=payload, grounded_turn=grounded):
				return payload
	return candidates[0]


def latest_reasoning_contract(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		if str(payload.get("type") or "").strip().lower() == "qwen_erp_business_reasoning_contract":
			return payload
	return {}


def latest_recovery_contract(session_doc: Any) -> Dict[str, Any]:
	newest_grounded_request_id = ""
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		payload_type = str(payload.get("type") or "").strip().lower()
		if payload_type == "qwen_grounded_turn_context":
			if not newest_grounded_request_id:
				newest_grounded_request_id = grounded_turn_source_request_id(payload)
			continue
		if payload_type == "qwen_conversational_repair_intent_contract":
			repair_state = str(payload.get("repair_state") or "").strip().lower()
			accepted_action = str(payload.get("accepted_recovery_action") or "").strip()
			if bool(payload.get("targets_prior_recovery")) and repair_state == "accepted" and accepted_action:
				return {}
		if payload_type == "qwen_artifact_enrichment_recovery_contract":
			recovery_source_request_id = str(payload.get("source_request_id") or "").strip()
			if newest_grounded_request_id and recovery_source_request_id and newest_grounded_request_id != recovery_source_request_id:
				return {}
			return payload
	return {}


def source_compatible_reasoning_contract(
	*,
	grounded_turn: Dict[str, Any],
	reasoning_contract: Dict[str, Any],
) -> Dict[str, Any]:
	grounded = dict(grounded_turn or {})
	contract = dict(reasoning_contract or {})
	if not grounded or not contract:
		return {}
	grounded_source_request_id = str(grounded.get("trace_request_id") or grounded.get("request_id") or "").strip()
	contract_source_request_id = str(contract.get("grounding_source_request_id") or "").strip()
	if grounded_source_request_id and contract_source_request_id and grounded_source_request_id != contract_source_request_id:
		return {}
	grounded_family_id = str(grounded.get("artifact_family_id") or "").strip()
	contract_family_id = str(contract.get("grounding_family_id") or "").strip()
	if grounded_family_id and contract_family_id and grounded_family_id != contract_family_id:
		return {}
	grounded_reports = {
		str(value or "").strip()
		for value in (grounded.get("artifact_source_reports") or [])
		if str(value or "").strip()
	}
	contract_reports = {
		str(value or "").strip()
		for value in (contract.get("grounding_source_reports") or [])
		if str(value or "").strip()
	}
	if grounded_reports and contract_reports and grounded_reports != contract_reports:
		return {}
	return contract
