from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import build_front_door_intent_gate_contract
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_deterministic_family_surface_interpretation,
	interpret_fresh_query_semantically,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import list_active_master_data_scope_activations
from ai_assistant_ui.qwen_chat.metadata import (
	get_frontdoor_intent_spec,
	list_frontdoor_intent_specs,
)
from ai_assistant_ui.qwen_chat.model_backed_helper_metadata import (
	attach_helper_metadata_to_agent_meta,
	build_model_backed_helper_runtime_metadata_bundle,
)
from ai_assistant_ui.qwen_chat.light_semantic_metadata import (
	attach_light_semantic_metadata_to_agent_meta,
	build_light_semantic_runtime_metadata_bundle,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_frontdoor_interpretation,
	call_qwen_runtime_frontdoor_render,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


@dataclass(frozen=True)
class SemanticFrontDoorIntent:
	intent_class: str
	confidence: float
	reason: str
	extracted_slots: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticFrontDoorResult:
	status: str
	intent: SemanticFrontDoorIntent | None = None
	confidence_threshold: float = 0.8
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] | None = None

	def to_payload(self) -> Dict[str, Any]:
		agent_meta = dict(self.agent_meta or {})
		metadata_bundle = build_light_semantic_runtime_metadata_bundle(
			lane_id="frontdoor_semantic_classification",
			role_owner="frontdoor_intent_gate",
			agent_meta=agent_meta,
			runtime_source=(
				"frontdoor_runtime_agent_meta"
				if agent_meta
				else f"frontdoor_{self.status or 'unknown'}_without_runtime_agent_meta"
			),
			answer_mode=f"frontdoor_{self.status or 'unknown'}",
			semantic_status=self.status,
		)
		agent_meta = attach_light_semantic_metadata_to_agent_meta(agent_meta, metadata_bundle)
		runtime_metadata = metadata_bundle["runtime_metadata_envelope"]
		return {
			"type": "qwen_semantic_frontdoor_interpretation",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"fallback_used": bool(runtime_metadata.get("fallback_used")),
			"fallback_reason": str(runtime_metadata.get("fallback_reason") or "").strip(),
			"intent": {
				"intent_class": self.intent.intent_class,
				"confidence": self.intent.confidence,
				"reason": self.intent.reason,
				"extracted_slots": dict(self.intent.extracted_slots or {}),
			}
			if self.intent
			else {},
			"agent_meta": agent_meta,
			"model_role_observability": metadata_bundle["model_role_observability"],
			"model_role_strict_readiness": metadata_bundle["model_role_strict_readiness"],
			"runtime_metadata_envelope": metadata_bundle["runtime_metadata_envelope"],
		}


@dataclass(frozen=True)
class FrontDoorRenderResult:
	ok: bool
	answer_text: str
	runtime_error: str = ""
	agent_meta: Dict[str, Any] | None = None

	def to_payload(self) -> Dict[str, Any]:
		agent_meta = dict(self.agent_meta or {})
		runtime_error = str(self.runtime_error or "").strip()
		metadata_bundle = build_model_backed_helper_runtime_metadata_bundle(
			lane_id="frontdoor_render",
			role_owner="frontdoor_intent_gate",
			agent_meta=agent_meta,
			runtime_source="frontdoor_render_runtime_agent_meta" if agent_meta else "frontdoor_render_without_runtime_agent_meta",
			answer_mode="frontdoor_render",
			evidence_scope="frontdoor_response_payload",
			authority_source="frontdoor_contract",
			preflight_status="passed",
			fallback_used=not bool(self.ok),
			fallback_reason=runtime_error if not bool(self.ok) else "",
		)
		agent_meta = attach_helper_metadata_to_agent_meta(agent_meta, metadata_bundle)
		return {
			"type": "qwen_frontdoor_render_result",
			"contract_version": "1.0",
			"ok": bool(self.ok),
			"answer_text": str(self.answer_text or "").strip(),
			"runtime_error": runtime_error,
			"agent_meta": agent_meta,
			"model_role_observability": metadata_bundle["model_role_observability"],
			"model_role_strict_readiness": metadata_bundle["model_role_strict_readiness"],
			"runtime_metadata_envelope": metadata_bundle["runtime_metadata_envelope"],
		}


def _confidence_threshold() -> float:
	default = 0.8
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_frontdoor_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _build_interpretation_context() -> Dict[str, Any]:
	intent_classes: List[Dict[str, str]] = []
	for item in list_frontdoor_intent_specs():
		intent_class_id = str(item.get("intent_class_id") or "").strip()
		if not intent_class_id:
			continue
		intent_classes.append(
			{
				"intent_class_id": intent_class_id,
				"label": str(item.get("label") or intent_class_id).strip(),
				"description": str(item.get("description") or "").strip(),
			}
		)
	active_master_data_entity_grains: List[str] = []
	active_master_data_lookup_modes: List[str] = []
	active_master_data_lookup_projections: List[str] = []
	for activation in list_active_master_data_scope_activations():
		entity_grain = str(activation.get("entity_grain") or "").strip()
		if entity_grain:
			active_master_data_entity_grains.append(entity_grain)
		for lookup_mode in (activation.get("allowed_lookup_modes") or []):
			clean_mode = str(lookup_mode or "").strip()
			if clean_mode:
				active_master_data_lookup_modes.append(clean_mode)
		projection = str(activation.get("default_projection") or "").strip()
		if projection:
			active_master_data_lookup_projections.append(projection)
	return {
		"intent_classes": intent_classes,
		"active_master_data_entity_grains": list(dict.fromkeys(active_master_data_entity_grains)),
		"active_master_data_lookup_modes": list(dict.fromkeys(active_master_data_lookup_modes)),
		"active_master_data_lookup_projections": list(dict.fromkeys(active_master_data_lookup_projections)),
	}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _validated_frontdoor_slots(intent_class: str, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
	if intent_class != "route_onward":
		return {}
	raw_slots = payload.get("extracted_slots") if isinstance(payload.get("extracted_slots"), dict) else {}
	if not raw_slots:
		return {}
	allowed_entity_grains = set(_clean_list(context.get("active_master_data_entity_grains")))
	allowed_lookup_modes = set(_clean_list(context.get("active_master_data_lookup_modes")))
	allowed_lookup_projections = set(_clean_list(context.get("active_master_data_lookup_projections")))
	out: Dict[str, Any] = {}
	entity_grain = _clean_text(raw_slots.get("entity_grain"))
	if entity_grain in allowed_entity_grains:
		out["entity_grain"] = entity_grain
	lookup_mode = _clean_text(raw_slots.get("lookup_mode"))
	if lookup_mode in allowed_lookup_modes:
		out["lookup_mode"] = lookup_mode
	lookup_projection = _clean_text(raw_slots.get("lookup_projection"))
	if lookup_projection in allowed_lookup_projections:
		out["lookup_projection"] = lookup_projection
	lookup_search_text = _clean_text(raw_slots.get("lookup_search_text"))
	if lookup_search_text:
		out["lookup_search_text"] = lookup_search_text
	return out


def _validate_semantic_payload(payload: Dict[str, Any], context: Dict[str, Any]) -> SemanticFrontDoorIntent | None:
	if not isinstance(payload, dict):
		return None
	allowed_intents = {
		str(item.get("intent_class_id") or "").strip()
		for item in (context.get("intent_classes") or [])
		if isinstance(item, dict) and str(item.get("intent_class_id") or "").strip()
	}
	intent_class = str(payload.get("intent_class") or "").strip()
	if intent_class not in allowed_intents:
		return None
	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	return SemanticFrontDoorIntent(
		intent_class=intent_class,
		confidence=max(0.0, min(1.0, confidence)),
		reason=_clean_text(payload.get("reason")),
		extracted_slots=_validated_frontdoor_slots(intent_class, payload, context),
	)


def _frontdoor_intent_keeps_conversational_ownership(intent: SemanticFrontDoorIntent | None) -> bool:
	if intent is None:
		return False
	spec = get_frontdoor_intent_spec(str(intent.intent_class or "").strip())
	if not spec:
		return False
	return bool(
		bool(spec.get("handle_in_front_door", False))
		and str(spec.get("route_target") or "").strip() == "front_door"
		and not bool(spec.get("requires_grounded_context", False))
	)


def _fresh_query_semantic_override(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
) -> SemanticFrontDoorIntent | None:
	result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	interpretation = getattr(result, "interpretation", None)
	if str(getattr(result, "status", "") or "").strip() != "accepted" or interpretation is None:
		interpretation = _deterministic_family_surface_interpretation(
			request_id=request_id,
			session_id=session_id,
			message=message,
			confidence_threshold=float(getattr(result, "confidence_threshold", 0.72) or 0.72),
		)
		if interpretation is None:
			return None
	if not list(getattr(interpretation, "candidate_capability_ids", []) or []) and not list(
		getattr(interpretation, "candidate_reports", []) or []
	):
		return None
	return SemanticFrontDoorIntent(
		intent_class="route_onward",
		confidence=max(
			float(getattr(result, "confidence_threshold", 0.72) or 0.72),
			float(getattr(interpretation, "confidence", 0.0) or 0.0),
		),
		reason="A semantic fresh-query cross-check indicates the turn is a plausible ERP request and should continue through the main lanes.",
		extracted_slots={},
	)


def interpret_front_door_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
	grounded_context_available: bool,
) -> SemanticFrontDoorResult:
	threshold = _confidence_threshold()
	context = _build_interpretation_context()
	try:
		data = call_qwen_runtime_frontdoor_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			grounded_context_available=grounded_context_available,
			interpretation_context=context,
		)
	except QwenRuntimeClientError as exc:
		return SemanticFrontDoorResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	agent_meta = data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {}
	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticFrontDoorResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime front-door interpreter returned no valid interpretation object.",
			agent_meta=agent_meta,
		)
	intent = _validate_semantic_payload(interpretation, context)
	if intent is None:
		return SemanticFrontDoorResult(
			status="invalid_response",
			confidence_threshold=threshold,
			validation_error="Runtime front-door interpretation did not pass governed validation.",
			agent_meta=agent_meta,
		)
	if intent.confidence < threshold:
		return SemanticFrontDoorResult(
			status="below_threshold",
			intent=intent,
			confidence_threshold=threshold,
			validation_error="Runtime front-door interpretation confidence is below threshold.",
			agent_meta=agent_meta,
		)
	if intent.intent_class == "session_flow" and grounded_context_available:
		fresh_query_override = _fresh_query_semantic_override(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
		)
		if fresh_query_override is not None:
			return SemanticFrontDoorResult(
				status="guardrailed_to_route_onward",
				intent=fresh_query_override,
				confidence_threshold=threshold,
				agent_meta=agent_meta,
			)
	if intent.intent_class != "route_onward" and not _frontdoor_intent_keeps_conversational_ownership(intent):
		fresh_query_override = _fresh_query_semantic_override(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
		)
		if fresh_query_override is not None:
			return SemanticFrontDoorResult(
				status="guardrailed_to_route_onward",
				intent=fresh_query_override,
				confidence_threshold=threshold,
				agent_meta=agent_meta,
			)
	if intent.intent_class == "session_flow" and not grounded_context_available:
		return SemanticFrontDoorResult(
			status="guardrailed_to_route_onward",
			intent=SemanticFrontDoorIntent(
				intent_class="route_onward",
				confidence=max(intent.confidence, threshold),
				reason="The turn looks like session flow, but there is no grounded context yet.",
				extracted_slots={},
			),
			confidence_threshold=threshold,
			agent_meta=agent_meta,
		)
	return SemanticFrontDoorResult(
		status="accepted",
		intent=intent,
		confidence_threshold=threshold,
		agent_meta=agent_meta,
	)


def build_front_door_intent_gate_contract_from_semantic_result(
	*,
	request_id: str,
	semantic_result: SemanticFrontDoorResult,
	grounded_context_available: bool,
	response_payload_override: Dict[str, Any] | None = None,
):
	intent = semantic_result.intent
	intent_class = str(getattr(intent, "intent_class", "") or "route_onward").strip() or "route_onward"
	confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
	reason = str(getattr(intent, "reason", "") or "").strip()
	if semantic_result.status in {"runtime_error", "invalid_response", "below_threshold"}:
		intent_class = "route_onward"
		confidence = 0.0
		if semantic_result.status == "runtime_error":
			reason = "Front-door proposal was unavailable, so the turn should route onward."
		elif semantic_result.status == "below_threshold":
			reason = "Front-door proposal confidence was too low, so the turn should route onward."
		else:
			reason = "Front-door proposal did not pass governed validation, so the turn should route onward."
	return build_front_door_intent_gate_contract(
		request_id=request_id,
		intent_class=intent_class,
		confidence=confidence,
		grounded_context_available=grounded_context_available,
		reason=reason,
		response_payload_override=response_payload_override,
	)


def build_front_door_intent_gate_contract_from_message(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None = None,
	grounded_context_available: bool,
):
	result = interpret_front_door_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=recent_messages,
		grounded_context_available=grounded_context_available,
	)
	return build_front_door_intent_gate_contract_from_semantic_result(
		request_id=request_id,
		semantic_result=result,
		grounded_context_available=grounded_context_available,
	)


def render_front_door_answer(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]] | None,
	grounded_context_available: bool,
	frontdoor_contract: Any,
) -> FrontDoorRenderResult:
	response_payload = getattr(frontdoor_contract, "response_payload", {})
	fallback_text = str(response_payload.get("text") or "").strip() if isinstance(response_payload, dict) else ""
	try:
		data = call_qwen_runtime_frontdoor_render(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=list(recent_messages or []),
			grounded_context_available=grounded_context_available,
			intent_class=str(getattr(frontdoor_contract, "intent_class", "") or "").strip(),
			response_mode=str(getattr(frontdoor_contract, "response_mode", "") or "").strip(),
			response_payload=response_payload if isinstance(response_payload, dict) else {},
			reason=str(getattr(frontdoor_contract, "reason", "") or "").strip(),
		)
	except QwenRuntimeClientError as exc:
		return FrontDoorRenderResult(
			ok=False,
			answer_text=fallback_text,
			runtime_error=str(exc),
		)
	answer_text = str(data.get("answer_text") or "").strip()
	if not answer_text:
		return FrontDoorRenderResult(
			ok=False,
			answer_text=fallback_text,
			runtime_error="Front-door renderer returned no answer text.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	return FrontDoorRenderResult(
		ok=bool(data.get("ok")),
		answer_text=answer_text,
		runtime_error=str(data.get("error") or "").strip(),
		agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
	)


def front_door_intent_probe_cases() -> List[Dict[str, object]]:
	return [
		{"message": "hi", "grounded_context_available": False},
		{"message": "thank you", "grounded_context_available": False},
		{"message": "what can you do", "grounded_context_available": False},
		{"message": "continue", "grounded_context_available": True},
		{"message": "I am okay for now, I will come back later", "grounded_context_available": True},
		{"message": "show me sales trend", "grounded_context_available": False},
	]
