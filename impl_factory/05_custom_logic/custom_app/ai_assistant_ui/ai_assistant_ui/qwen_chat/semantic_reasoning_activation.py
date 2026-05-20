from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.consultant_role_registry import consultant_business_role_for_context
from ai_assistant_ui.qwen_chat.light_semantic_metadata import (
	attach_light_semantic_metadata_to_agent_meta,
	build_light_semantic_runtime_metadata_bundle,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_followup_class_spec,
	ontology_detect_followup_modes,
)
from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_reasoning_activation_interpretation,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


_ALLOWED_CONSULTANT_RESPONSE_MODES = {
	"factual_grounded_answer",
	"consultant_interpretation",
	"consultant_detail",
	"consultant_recommendation",
	"boundary_guidance",
}

_ALLOWED_EVIDENCE_POLICIES = {
	"current_result_only",
	"evidence_expansion_preferred",
	"evidence_expansion_required",
	"policy_required",
}

_ALLOWED_ANSWER_OBLIGATIONS = {
	"explain_grounded_meaning",
	"explain_grounded_basis",
	"expand_grounded_detail",
	"advise_with_approved_policy",
	"state_boundary_and_next_step",
}

_ALLOWED_ANSWER_GOALS = {
	"explain",
	"expand_detail",
	"compare",
	"recommend",
	"diagnose",
	"define",
	"calculate",
	"clarify_boundary",
}

_ALLOWED_EVIDENCE_DEPTHS = {
	"current_result_only",
	"drilldown_preferred",
	"drilldown_required",
	"policy_required",
}

_ALLOWED_BUSINESS_ROLES = {
	"business_consultant",
	"controller",
	"collector",
	"buyer",
	"sales_manager",
	"inventory_manager",
	"analyst",
}

_ALLOWED_TARGET_REFERENCES = {
	"current_result",
	"current_metric",
	"current_row",
	"entity",
	"document",
	"line_item",
	"offered_next_action",
	"family_summary",
	"unknown",
}

_ALLOWED_RISK_LEVELS = {
	"factual_only",
	"bounded_consultation",
	"policy_required",
	"unsupported",
}


@dataclass(frozen=True)
class SemanticReasoningActivationIntent:
	reasoning_type: str
	detail_level: str = "default"
	presentation_style: str = "default"
	response_mode: str = "factual_grounded_answer"
	evidence_policy: str = "current_result_only"
	answer_obligation: str = "explain_grounded_meaning"
	answer_goal: str = "explain"
	evidence_depth: str = "current_result_only"
	business_role: str = "business_consultant"
	target_reference: str = "current_result"
	risk_level: str = "factual_only"
	confidence: float = 0.0
	reason: str = ""


@dataclass(frozen=True)
class SemanticReasoningActivationResult:
	status: str
	intent: SemanticReasoningActivationIntent | None = None
	confidence_threshold: float = 0.72
	runtime_error: str = ""
	validation_error: str = ""
	agent_meta: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		agent_meta = self.agent_meta if isinstance(self.agent_meta, dict) else {}
		metadata_bundle = build_light_semantic_runtime_metadata_bundle(
			lane_id="semantic_reasoning_activation",
			role_owner="semantic_reasoning_activation",
			agent_meta=agent_meta,
			runtime_source="reasoning_activation_runtime_agent_meta" if agent_meta else f"reasoning_activation_{self.status or 'unknown'}_without_runtime_agent_meta",
			answer_mode=f"reasoning_activation_{self.status or 'unknown'}",
			semantic_status=self.status,
		)
		agent_meta = attach_light_semantic_metadata_to_agent_meta(agent_meta, metadata_bundle)
		runtime_metadata = metadata_bundle["runtime_metadata_envelope"]
		intent_payload: Dict[str, Any] = {}
		if self.intent is not None:
			intent_payload = {
				"reasoning_type": self.intent.reasoning_type,
				"detail_level": self.intent.detail_level,
				"presentation_style": self.intent.presentation_style,
				"response_mode": self.intent.response_mode,
				"evidence_policy": self.intent.evidence_policy,
				"answer_obligation": self.intent.answer_obligation,
				"answer_goal": self.intent.answer_goal,
				"evidence_depth": self.intent.evidence_depth,
				"business_role": self.intent.business_role,
				"target_reference": self.intent.target_reference,
				"risk_level": self.intent.risk_level,
				"confidence": self.intent.confidence,
				"reason": self.intent.reason,
			}
		return {
			"type": "qwen_semantic_reasoning_activation",
			"contract_version": "1.0",
			"status": self.status,
			"confidence_threshold": self.confidence_threshold,
			"runtime_error": self.runtime_error,
			"validation_error": self.validation_error,
			"fallback_used": bool(runtime_metadata.get("fallback_used")),
			"fallback_reason": str(runtime_metadata.get("fallback_reason") or "").strip(),
			"intent": intent_payload,
			"agent_meta": agent_meta,
			"model_role_observability": metadata_bundle["model_role_observability"],
			"model_role_strict_readiness": metadata_bundle["model_role_strict_readiness"],
			"runtime_metadata_envelope": metadata_bundle["runtime_metadata_envelope"],
		}


def _confidence_threshold() -> float:
	default = 0.72
	if frappe is None:
		return default
	try:
		raw = (getattr(frappe, "conf", None) or {}).get("qwen_semantic_reasoning_min_confidence", default)
		return max(0.0, min(1.0, float(raw)))
	except Exception:
		return default


def _build_activation_context(
	*,
	activation_contract: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	prior_contract = dict(prior_reasoning_contract or {})
	prior_offered_next_actions = [
		dict(item)
		for item in (prior_contract.get("offered_next_actions") or [])
		if isinstance(item, dict)
	]
	source_reports = [
		str(value or "").strip()
		for value in (activation_contract.get("grounded_source_reports") or [])
		if str(value or "").strip()
	]
	return {
		"grounded_context_available": bool(activation_contract.get("grounded_context_available")),
		"grounded_source_kind": str(activation_contract.get("grounded_source_kind") or "").strip(),
		"grounded_source_name": str(activation_contract.get("grounded_source_name") or "").strip(),
		"grounded_family_id": str(activation_contract.get("grounded_family_id") or "").strip(),
		"grounded_artifact_type": str(activation_contract.get("grounded_artifact_type") or "").strip(),
		"grounded_source_reports": source_reports,
		"grounded_source_report_count": int(len(source_reports)),
		"composite_grounding": bool(len(source_reports) > 1),
		"grounded_capability_id": str(activation_contract.get("grounded_capability_id") or "").strip(),
		"grounded_semantic_tags": [
			str(value or "").strip()
			for value in (activation_contract.get("grounded_semantic_tags") or [])
			if str(value or "").strip()
		],
		"grounding_summary": dict(activation_contract.get("grounding_summary") or {})
		if isinstance(activation_contract.get("grounding_summary"), dict)
		else {},
		"recommendation_allowed": bool(activation_contract.get("recommendation_allowed")),
		"recommendation_policy_basis": [
			str(value or "").strip()
			for value in (activation_contract.get("recommendation_policy_basis") or [])
			if str(value or "").strip()
		],
		"allowed_reasoning_types": [
			str(value or "").strip()
			for value in (activation_contract.get("allowed_reasoning_types") or [])
			if str(value or "").strip()
		],
		"prior_reasoning_available": bool(prior_contract),
		"prior_reasoning_type": str(prior_contract.get("reasoning_type") or "").strip(),
		"prior_offered_next_action_count": int(len(prior_offered_next_actions)),
		"prior_offered_next_actions": prior_offered_next_actions,
		"activation_state": str(activation_contract.get("activation_state") or "").strip(),
		"route_target": str(activation_contract.get("route_target") or "").strip(),
	}


def _normalize_presentation_style(
	*,
	reasoning_type: str,
	detail_level: str,
	presentation_style: str,
) -> str:
	style = str(presentation_style or "default").strip().lower() or "default"
	if style in {"bullet", "table"}:
		return style
	if str(detail_level or "").strip().lower() in {"expanded", "comprehensive"} and str(reasoning_type or "").strip() in {
		"recommendation",
		"continuation_detail",
	}:
		return "bullet"
	return "default"


def _default_business_role(context: Dict[str, Any]) -> str:
	return consultant_business_role_for_context(
		family_id=str(context.get("grounded_family_id") or "").strip(),
		capability_id=str(context.get("grounded_capability_id") or "").strip(),
		semantic_tags=[
			str(value or "").strip()
			for value in (context.get("grounded_semantic_tags") or [])
			if str(value or "").strip()
		],
	)


def _evidence_depth_from_policy(evidence_policy: str) -> str:
	policy = str(evidence_policy or "").strip()
	if policy == "evidence_expansion_required":
		return "drilldown_required"
	if policy == "evidence_expansion_preferred":
		return "drilldown_preferred"
	if policy == "policy_required":
		return "policy_required"
	return "current_result_only"


def _default_semantic_detail_intent_fields(
	*,
	reasoning_type: str,
	detail_level: str,
	response_mode: str,
	evidence_policy: str,
	answer_obligation: str,
	context: Dict[str, Any],
) -> Dict[str, str]:
	reasoning = str(reasoning_type or "").strip()
	obligation = str(answer_obligation or "").strip()
	mode = str(response_mode or "").strip()
	if obligation == "state_boundary_and_next_step":
		answer_goal = "clarify_boundary"
	elif reasoning == "recommendation" or obligation == "advise_with_approved_policy":
		answer_goal = "recommend"
	elif reasoning == "continuation_detail" or obligation == "expand_grounded_detail":
		answer_goal = "expand_detail"
	elif reasoning == "explanation" or obligation == "explain_grounded_basis":
		answer_goal = "explain"
	else:
		answer_goal = "explain"
	if mode == "boundary_guidance" or evidence_policy == "policy_required":
		risk_level = "policy_required"
	elif mode in {"consultant_interpretation", "consultant_detail", "consultant_recommendation"}:
		risk_level = "bounded_consultation"
	else:
		risk_level = "factual_only"
	target_reference = "offered_next_action" if int(context.get("prior_offered_next_action_count") or 0) > 0 else "current_result"
	return {
		"answer_goal": answer_goal,
		"evidence_depth": _evidence_depth_from_policy(evidence_policy),
		"business_role": _default_business_role(context),
		"target_reference": target_reference,
		"risk_level": risk_level,
	}


def _default_consultant_contract_fields(
	*,
	reasoning_type: str,
	detail_level: str,
	context: Dict[str, Any],
) -> Dict[str, str]:
	reasoning = str(reasoning_type or "").strip()
	level = str(detail_level or "default").strip().lower() or "default"
	if reasoning == "recommendation":
		if not bool(context.get("recommendation_allowed")):
			return {
				"response_mode": "boundary_guidance",
				"evidence_policy": "policy_required",
				"answer_obligation": "state_boundary_and_next_step",
			}
		return {
			"response_mode": "consultant_recommendation",
			"evidence_policy": "evidence_expansion_preferred",
			"answer_obligation": "advise_with_approved_policy",
		}
	if reasoning == "continuation_detail":
		return {
			"response_mode": "consultant_detail",
			"evidence_policy": "evidence_expansion_required" if level == "comprehensive" else "evidence_expansion_preferred",
			"answer_obligation": "expand_grounded_detail",
		}
	if reasoning == "explanation":
		return {
			"response_mode": "consultant_interpretation",
			"evidence_policy": "current_result_only",
			"answer_obligation": "explain_grounded_basis",
		}
	return {
		"response_mode": "consultant_interpretation",
		"evidence_policy": "current_result_only",
		"answer_obligation": "explain_grounded_meaning",
	}


def _normalize_consultant_contract_field(
	*,
	payload: Dict[str, Any],
	context: Dict[str, Any],
	reasoning_type: str,
	detail_level: str,
	field_name: str,
	allowed_values: set[str],
) -> str:
	defaults = _default_consultant_contract_fields(
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		context=context,
	)
	value = str(payload.get(field_name) or "").strip()
	if value in allowed_values:
		return value
	return defaults[field_name]


def _normalize_semantic_detail_intent_field(
	*,
	payload: Dict[str, Any],
	defaults: Dict[str, str],
	field_name: str,
	allowed_values: set[str],
) -> str:
	value = str(payload.get(field_name) or "").strip()
	if value in allowed_values:
		return value
	return str(defaults.get(field_name) or "").strip()


def _validate_semantic_payload(
	*,
	payload: Dict[str, Any],
	context: Dict[str, Any],
) -> SemanticReasoningActivationIntent | None:
	if not isinstance(payload, dict):
		return None
	allowed_types = {
		str(value or "").strip()
		for value in (context.get("allowed_reasoning_types") or [])
		if str(value or "").strip()
	}
	reasoning_type = str(payload.get("reasoning_type") or "").strip()
	if reasoning_type not in allowed_types:
		return None
	detail_level = str(payload.get("detail_level") or "default").strip().lower() or "default"
	if detail_level not in {"default", "expanded", "comprehensive"}:
		return None
	presentation_style = str(payload.get("presentation_style") or "default").strip().lower() or "default"
	if presentation_style not in {"default", "bullet", "table"}:
		return None
	presentation_style = _normalize_presentation_style(
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		presentation_style=presentation_style,
	)
	response_mode = _normalize_consultant_contract_field(
		payload=payload,
		context=context,
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		field_name="response_mode",
		allowed_values=_ALLOWED_CONSULTANT_RESPONSE_MODES,
	)
	evidence_policy = _normalize_consultant_contract_field(
		payload=payload,
		context=context,
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		field_name="evidence_policy",
		allowed_values=_ALLOWED_EVIDENCE_POLICIES,
	)
	answer_obligation = _normalize_consultant_contract_field(
		payload=payload,
		context=context,
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		field_name="answer_obligation",
		allowed_values=_ALLOWED_ANSWER_OBLIGATIONS,
	)
	detail_intent_defaults = _default_semantic_detail_intent_fields(
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		response_mode=response_mode,
		evidence_policy=evidence_policy,
		answer_obligation=answer_obligation,
		context=context,
	)
	answer_goal = _normalize_semantic_detail_intent_field(
		payload=payload,
		defaults=detail_intent_defaults,
		field_name="answer_goal",
		allowed_values=_ALLOWED_ANSWER_GOALS,
	)
	evidence_depth = _normalize_semantic_detail_intent_field(
		payload=payload,
		defaults=detail_intent_defaults,
		field_name="evidence_depth",
		allowed_values=_ALLOWED_EVIDENCE_DEPTHS,
	)
	business_role = _normalize_semantic_detail_intent_field(
		payload=payload,
		defaults=detail_intent_defaults,
		field_name="business_role",
		allowed_values=_ALLOWED_BUSINESS_ROLES,
	)
	target_reference = _normalize_semantic_detail_intent_field(
		payload=payload,
		defaults=detail_intent_defaults,
		field_name="target_reference",
		allowed_values=_ALLOWED_TARGET_REFERENCES,
	)
	risk_level = _normalize_semantic_detail_intent_field(
		payload=payload,
		defaults=detail_intent_defaults,
		field_name="risk_level",
		allowed_values=_ALLOWED_RISK_LEVELS,
	)
	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	return SemanticReasoningActivationIntent(
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		presentation_style=presentation_style,
		response_mode=response_mode,
		evidence_policy=evidence_policy,
		answer_obligation=answer_obligation,
		answer_goal=answer_goal,
		evidence_depth=evidence_depth,
		business_role=business_role,
		target_reference=target_reference,
		risk_level=risk_level,
		confidence=confidence,
		reason=str(payload.get("reason") or "").strip(),
	)


def _metadata_reasoning_activation_result(
	*,
	message: str,
	context: Dict[str, Any],
	threshold: float,
) -> SemanticReasoningActivationResult | None:
	if not bool(context.get("grounded_context_available")):
		return None
	try:
		modes = [
			str(mode or "").strip()
			for mode in ontology_detect_followup_modes(message)
			if str(mode or "").strip()
		]
	except Exception:
		modes = []
	if not modes:
		return None
	family_id = str(context.get("grounded_family_id") or "").strip()
	for mode in modes:
		spec = get_followup_class_spec(mode)
		if not isinstance(spec, dict):
			continue
		supported_families = [
			str(value or "").strip()
			for value in (spec.get("supported_families") or [])
			if str(value or "").strip()
		]
		if supported_families and family_id and family_id not in supported_families:
			continue
		activation = spec.get("reasoning_activation")
		if not isinstance(activation, dict):
			continue
		intent = _validate_semantic_payload(
			payload=dict(activation),
			context=context,
		)
		if intent is None:
			continue
		if float(intent.confidence or 0.0) < threshold:
			continue
		return SemanticReasoningActivationResult(
			status="accepted",
			intent=intent,
			confidence_threshold=threshold,
			agent_meta={
				"activation_source": "governed_followup_metadata",
				"followup_mode": mode,
				"detected_followup_modes": list(dict.fromkeys(modes)),
			},
		)
	return None


def interpret_reasoning_activation_semantically(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages: List[Dict[str, str]],
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	activation_contract: Dict[str, Any],
	prior_reasoning_contract: Dict[str, Any] | None = None,
) -> SemanticReasoningActivationResult:
	threshold = _confidence_threshold()
	if str(activation_contract.get("activation_state") or "").strip() != "eligible":
		return SemanticReasoningActivationResult(
			status="not_applicable",
			confidence_threshold=threshold,
		)
	context = _build_activation_context(
		activation_contract=activation_contract,
		prior_reasoning_contract=prior_reasoning_contract,
	)
	metadata_activation = _metadata_reasoning_activation_result(
		message=message,
		context=context,
		threshold=threshold,
	)
	if metadata_activation is not None:
		return metadata_activation
	try:
		data = call_qwen_runtime_reasoning_activation_interpretation(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
			activation_context=context,
		)
	except QwenRuntimeClientError as exc:
		return SemanticReasoningActivationResult(
			status="runtime_error",
			confidence_threshold=threshold,
			runtime_error=str(exc),
		)

	interpretation = data.get("interpretation")
	if not isinstance(interpretation, dict):
		return SemanticReasoningActivationResult(
			status="invalid_payload",
			confidence_threshold=threshold,
			validation_error="Runtime reasoning activation interpreter returned no valid interpretation object.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	intent = _validate_semantic_payload(payload=interpretation, context=context)
	if intent is None:
		return SemanticReasoningActivationResult(
			status="rejected",
			confidence_threshold=threshold,
			validation_error="Runtime reasoning activation interpretation did not pass governed validation.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	if float(intent.confidence or 0.0) < threshold:
		return SemanticReasoningActivationResult(
			status="low_confidence",
			intent=intent,
			confidence_threshold=threshold,
			validation_error="Runtime reasoning activation interpretation confidence is below threshold.",
			agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
		)
	return SemanticReasoningActivationResult(
		status="accepted",
		intent=intent,
		confidence_threshold=threshold,
		agent_meta=data.get("agent_meta") if isinstance(data.get("agent_meta"), dict) else {},
	)


def run_phase6b_reasoning_activation_smoke() -> Dict[str, Any]:
	not_applicable = interpret_reasoning_activation_semantically(
		request_id="phase6b-empty",
		session_id="phase6b",
		user_id="Administrator",
		site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "") if frappe is not None else "",
		message="what does this mean",
		recent_messages=[],
		latest_grounded_turn={},
		latest_family_artifact={},
		latest_assistant_payload={},
		activation_contract={"activation_state": "not_eligible", "allowed_reasoning_types": []},
	)
	if not_applicable.status != "not_applicable":
		raise RuntimeError("Phase 6B reasoning activation smoke failed: empty activation did not stay not_applicable.")

	eligible = interpret_reasoning_activation_semantically(
		request_id="phase6b-grounded",
		session_id="phase6b",
		user_id="Administrator",
		site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "") if frappe is not None else "",
		message="what does this mean",
		recent_messages=[
			{"role": "assistant", "content": "Accounts Receivable Summary for the company shows severe overdue concentration."},
		],
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-1",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
			"row_count": 10,
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
		activation_contract={
			"activation_state": "eligible",
			"grounded_context_available": True,
			"grounded_source_kind": "report",
			"grounded_source_name": "Accounts Receivable Summary",
			"grounded_family_id": "aging",
			"grounded_artifact_type": "normalized_family_artifact",
			"grounded_source_reports": ["Accounts Receivable Summary"],
			"grounded_capability_id": "accounts_receivable_read",
			"grounding_summary": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"row_count": 10,
				"date_range": {"report_date": "2026-03-26"},
				"latest_assistant_title": "Accounts Receivable Summary",
				"response_policy_mode": "grounded_analysis",
			},
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
			"route_target": "reasoning_lane",
		},
	)
	if eligible.status not in {"accepted", "low_confidence"}:
		raise RuntimeError(
			f"Phase 6B reasoning activation smoke failed: eligible activation returned unexpected status `{eligible.status}`."
		)
	if eligible.intent is None or str(eligible.intent.reasoning_type or "").strip() not in {
		"interpretation",
		"explanation",
		"recommendation",
		"continuation_detail",
	}:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned no valid reasoning type.")
	if str(eligible.intent.detail_level or "").strip() not in {"default", "expanded", "comprehensive"}:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid detail level.")
	if str(eligible.intent.presentation_style or "").strip() not in {"default", "bullet", "table"}:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid presentation style.")
	if str(eligible.intent.response_mode or "").strip() not in _ALLOWED_CONSULTANT_RESPONSE_MODES:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid consultant response mode.")
	if str(eligible.intent.evidence_policy or "").strip() not in _ALLOWED_EVIDENCE_POLICIES:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid evidence policy.")
	if str(eligible.intent.answer_obligation or "").strip() not in _ALLOWED_ANSWER_OBLIGATIONS:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid answer obligation.")
	if str(eligible.intent.answer_goal or "").strip() not in _ALLOWED_ANSWER_GOALS:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid answer goal.")
	if str(eligible.intent.evidence_depth or "").strip() not in _ALLOWED_EVIDENCE_DEPTHS:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid evidence depth.")
	if str(eligible.intent.business_role or "").strip() not in _ALLOWED_BUSINESS_ROLES:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid business role.")
	if str(eligible.intent.target_reference or "").strip() not in _ALLOWED_TARGET_REFERENCES:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid target reference.")
	if str(eligible.intent.risk_level or "").strip() not in _ALLOWED_RISK_LEVELS:
		raise RuntimeError("Phase 6B reasoning activation smoke failed: eligible activation returned invalid risk level.")
	return {
		"ok": True,
		"not_applicable": not_applicable.to_payload(),
		"eligible": eligible.to_payload(),
	}


def run_phase6_detail_presentation_policy_probe() -> Dict[str, Any]:
	normalized = _validate_semantic_payload(
		payload={
			"reasoning_type": "continuation_detail",
			"detail_level": "comprehensive",
			"presentation_style": "default",
			"confidence": 0.93,
			"reason": "Expanded grounded continuation requested.",
		},
		context={
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		},
	)
	if normalized is None:
		raise RuntimeError("Phase 6 detail presentation policy probe failed: normalized intent was rejected.")
	if str(normalized.presentation_style or "").strip() != "bullet":
		raise RuntimeError("Phase 6 detail presentation policy probe failed: expanded continuation did not default to bullet presentation.")

	explicit_default = _validate_semantic_payload(
		payload={
			"reasoning_type": "recommendation",
			"detail_level": "default",
			"presentation_style": "default",
			"confidence": 0.9,
			"reason": "Initial recommendation request.",
		},
		context={
			"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		},
	)
	if explicit_default is None:
		raise RuntimeError("Phase 6 detail presentation policy probe failed: default recommendation intent was rejected.")
	if str(explicit_default.presentation_style or "").strip() != "default":
		raise RuntimeError("Phase 6 detail presentation policy probe failed: first-turn recommendation should stay default presentation.")

	return {
		"ok": True,
		"normalized": {
			"reasoning_type": normalized.reasoning_type,
			"detail_level": normalized.detail_level,
			"presentation_style": normalized.presentation_style,
			"response_mode": normalized.response_mode,
			"evidence_policy": normalized.evidence_policy,
			"answer_obligation": normalized.answer_obligation,
			"answer_goal": normalized.answer_goal,
			"evidence_depth": normalized.evidence_depth,
			"business_role": normalized.business_role,
			"target_reference": normalized.target_reference,
			"risk_level": normalized.risk_level,
		},
		"default_recommendation": {
			"reasoning_type": explicit_default.reasoning_type,
			"detail_level": explicit_default.detail_level,
			"presentation_style": explicit_default.presentation_style,
			"response_mode": explicit_default.response_mode,
			"evidence_policy": explicit_default.evidence_policy,
			"answer_obligation": explicit_default.answer_obligation,
			"answer_goal": explicit_default.answer_goal,
			"evidence_depth": explicit_default.evidence_depth,
			"business_role": explicit_default.business_role,
			"target_reference": explicit_default.target_reference,
			"risk_level": explicit_default.risk_level,
		},
	}
