from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_repair_intent_interpretation,
)
from ai_assistant_ui.qwen_chat.contracts import build_conversational_repair_intent_contract

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


@dataclass(frozen=True)
class SemanticRepairIntent:
	repair_intent_type: str
	accepted_recovery_action: str = ""
	guidance_topic: str = ""
	preserve_scope: bool = False
	preserve_entity_dimension: bool = False
	preserve_time_context: bool = False
	confidence: float = 0.0
	reason: str = ""


@dataclass(frozen=True)
class SemanticRepairIntentResult:
	status: str
	intent: SemanticRepairIntent | None = None
	confidence_threshold: float = 0.72
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		intent_payload: Dict[str, Any] = {}
		if self.intent is not None:
			intent_payload = {
				"repair_intent_type": self.intent.repair_intent_type,
				"accepted_recovery_action": self.intent.accepted_recovery_action,
				"guidance_topic": self.intent.guidance_topic,
				"preserve_scope": bool(self.intent.preserve_scope),
				"preserve_entity_dimension": bool(self.intent.preserve_entity_dimension),
				"preserve_time_context": bool(self.intent.preserve_time_context),
				"confidence": float(self.intent.confidence),
				"reason": self.intent.reason,
			}
		return {
			"type": "qwen_semantic_repair_intent",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"intent": intent_payload,
			"agent_meta": self.agent_meta if isinstance(self.agent_meta, dict) else {},
		}


def _confidence_threshold() -> float:
	default = 0.72
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_semantic_repair_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _build_repair_context(
	*,
	recovery_contract: Dict[str, Any],
) -> Dict[str, Any]:
	available_actions = [
		str(value or "").strip()
		for value in (recovery_contract.get("available_recovery_actions") or [])
		if str(value or "").strip()
	]
	preservable_scope = dict(recovery_contract.get("preservable_scope") or {}) if isinstance(recovery_contract.get("preservable_scope"), dict) else {}
	preservable_dimensions = [
		str(value or "").strip()
		for value in (recovery_contract.get("preservable_dimensions") or [])
		if str(value or "").strip()
	]
	preservable_time_context = dict(recovery_contract.get("preservable_time_context") or {}) if isinstance(recovery_contract.get("preservable_time_context"), dict) else {}
	return {
		"recovery_state": str(recovery_contract.get("recovery_state") or "").strip(),
		"available_recovery_actions": available_actions,
		"recommended_recovery_action": str(recovery_contract.get("recommended_recovery_action") or "").strip(),
		"alternative_capability_id": str(recovery_contract.get("alternative_capability_id") or "").strip(),
		"alternative_report": str(recovery_contract.get("alternative_report") or "").strip(),
		"source_family_id": str(recovery_contract.get("source_family_id") or "").strip(),
		"source_report": str(recovery_contract.get("source_report") or "").strip(),
		"failure_type": str(recovery_contract.get("failure_type") or "").strip(),
		"preservable_scope_available": bool(preservable_scope),
		"preservable_dimension_available": bool(preservable_dimensions),
		"preservable_time_available": bool(preservable_time_context),
	}


def _validate_semantic_payload(
	*,
	payload: Dict[str, Any],
	context: Dict[str, Any],
	message: str,
	latest_grounded_turn: Dict[str, Any],
) -> SemanticRepairIntent | None:
	if not isinstance(payload, dict):
		return None
	repair_intent_type = str(payload.get("repair_intent_type") or "").strip()
	if repair_intent_type not in {"accept_recovery_action", "guidance_request", "not_applicable"}:
		return None
	accepted_recovery_action = str(payload.get("accepted_recovery_action") or "").strip()
	available_actions = {
		str(value or "").strip()
		for value in (context.get("available_recovery_actions") or [])
		if str(value or "").strip()
	}
	if repair_intent_type == "accept_recovery_action" and accepted_recovery_action not in available_actions:
		return None
	if repair_intent_type != "accept_recovery_action":
		accepted_recovery_action = ""
	guidance_topic = str(payload.get("guidance_topic") or "").strip()
	if repair_intent_type != "guidance_request":
		guidance_topic = ""
	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	return SemanticRepairIntent(
		repair_intent_type=repair_intent_type,
		accepted_recovery_action=accepted_recovery_action,
		guidance_topic=guidance_topic,
		preserve_scope=bool(payload.get("preserve_scope")) and bool(context.get("preservable_scope_available")),
		preserve_entity_dimension=bool(payload.get("preserve_entity_dimension")) and bool(context.get("preservable_dimension_available")),
		preserve_time_context=bool(payload.get("preserve_time_context")) and bool(context.get("preservable_time_available")),
		confidence=confidence,
		reason=str(payload.get("reason") or "").strip(),
	)


def interpret_repair_intent_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_recovery_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
) -> SemanticRepairIntentResult:
	threshold = _confidence_threshold()
	if not isinstance(latest_recovery_contract, dict) or not latest_recovery_contract:
		return SemanticRepairIntentResult(
			status="not_applicable",
			confidence_threshold=threshold,
		)
	context = _build_repair_context(recovery_contract=latest_recovery_contract)
	try:
		data = call_qwen_runtime_repair_intent_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			latest_recovery_contract=latest_recovery_contract,
			latest_grounded_turn=latest_grounded_turn,
			latest_assistant_payload=latest_assistant_payload,
			interpretation_context=context,
		)
	except QwenRuntimeClientError as exc:
		return SemanticRepairIntentResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticRepairIntentResult(
			status="invalid_payload",
			confidence_threshold=threshold,
			validation_error="Runtime repair interpreter returned no valid interpretation object.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	intent = _validate_semantic_payload(
		payload=interpretation,
		context=context,
		message=message,
		latest_grounded_turn=latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {},
	)
	if intent is None:
		return SemanticRepairIntentResult(
			status="rejected",
			confidence_threshold=threshold,
			validation_error="Runtime repair interpretation did not pass governed validation.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	if str(intent.repair_intent_type or "").strip() == "not_applicable":
		return SemanticRepairIntentResult(
			status="not_applicable",
			intent=intent,
			confidence_threshold=threshold,
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	if float(intent.confidence or 0.0) < threshold:
		return SemanticRepairIntentResult(
			status="low_confidence",
			intent=intent,
			confidence_threshold=threshold,
			validation_error="Runtime repair interpretation confidence is below threshold.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	return SemanticRepairIntentResult(
		status="accepted",
		intent=intent,
		confidence_threshold=threshold,
		agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
	)


def build_repair_intent_contract_from_semantic_result(
	*,
	request_id: str,
	session_id: str,
	semantic_result: SemanticRepairIntentResult,
) -> Dict[str, Any]:
	intent = semantic_result.intent
	if semantic_result.status == "accepted" and intent is not None:
		repair_state = "accepted" if intent.repair_intent_type == "accept_recovery_action" else "guidance_only"
		allowed_next_lane = "artifact_lane" if intent.repair_intent_type == "accept_recovery_action" else "recovery_guidance"
		return build_conversational_repair_intent_contract(
			request_id=request_id,
			session_id=session_id,
			repair_intent_type=intent.repair_intent_type,
			repair_state=repair_state,
			targets_prior_recovery=True,
			accepted_recovery_action=intent.accepted_recovery_action,
			guidance_topic=intent.guidance_topic,
			fresh_query_override=False,
			preserve_scope=bool(intent.preserve_scope),
			preserve_entity_dimension=bool(intent.preserve_entity_dimension),
			preserve_time_context=bool(intent.preserve_time_context),
			reason=str(intent.reason or "").strip(),
			allowed_next_lane=allowed_next_lane,
			confidence=float(intent.confidence or 0.0),
		).to_payload()
	return build_conversational_repair_intent_contract(
		request_id=request_id,
		session_id=session_id,
		repair_intent_type="not_applicable",
		repair_state="unresolved",
		targets_prior_recovery=bool(intent is not None),
		accepted_recovery_action="",
		guidance_topic="",
		fresh_query_override=False,
		preserve_scope=False,
		preserve_entity_dimension=False,
		preserve_time_context=False,
		reason=str(semantic_result.validation_error or semantic_result.runtime_error or "").strip(),
		allowed_next_lane="",
		confidence=float(getattr(intent, "confidence", 0.0) or 0.0),
	).to_payload()
