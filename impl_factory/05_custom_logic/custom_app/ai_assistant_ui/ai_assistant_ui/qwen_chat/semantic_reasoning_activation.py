from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.runtime_client import (
	QwenRuntimeClientError,
	call_qwen_runtime_reasoning_activation_interpretation,
)

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


@dataclass(frozen=True)
class SemanticReasoningActivationIntent:
	reasoning_type: str
	detail_level: str = "default"
	presentation_style: str = "default"
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
		intent_payload: Dict[str, Any] = {}
		if self.intent is not None:
			intent_payload = {
				"reasoning_type": self.intent.reasoning_type,
				"detail_level": self.intent.detail_level,
				"presentation_style": self.intent.presentation_style,
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
			"intent": intent_payload,
			"agent_meta": self.agent_meta if isinstance(self.agent_meta, dict) else {},
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
		"activation_state": str(activation_contract.get("activation_state") or "").strip(),
		"route_target": str(activation_contract.get("route_target") or "").strip(),
	}


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
	try:
		confidence = float(payload.get("confidence") or 0.0)
	except Exception:
		confidence = 0.0
	confidence = max(0.0, min(1.0, confidence))
	return SemanticReasoningActivationIntent(
		reasoning_type=reasoning_type,
		detail_level=detail_level,
		presentation_style=presentation_style,
		confidence=confidence,
		reason=str(payload.get("reason") or "").strip(),
	)


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
	return {
		"ok": True,
		"not_applicable": not_applicable.to_payload(),
		"eligible": eligible.to_payload(),
	}
