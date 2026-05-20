from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from .natural_business_understanding_contracts import CONTRACT_VERSION


MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE = "qwen_model_role_observability_contract"

ROLE_LIGHT_SEMANTIC = "light_semantic"
ROLE_HEAVY_REASONING = "heavy_reasoning"
ROLE_DETERMINISTIC = "deterministic"
ROLE_SHADOW_OBSERVER = "shadow_observer"
ROLE_UNKNOWN = "unknown"

COMPLIANCE_COMPLIANT = "compliant"
COMPLIANCE_NON_COMPLIANT = "non_compliant"
COMPLIANCE_UNKNOWN = "unknown"
COMPLIANCE_NOT_APPLICABLE = "not_applicable"


TARGET_ROLE_BY_LANE = {
	"frontdoor_semantic_classification": ROLE_LIGHT_SEMANTIC,
	"fresh_query_interpretation": ROLE_LIGHT_SEMANTIC,
	"followup_interpretation": ROLE_LIGHT_SEMANTIC,
	"semantic_reasoning_activation": ROLE_LIGHT_SEMANTIC,
	"semantic_repair_intent": ROLE_LIGHT_SEMANTIC,
	"visible_context_followup": ROLE_DETERMINISTIC,
	"visible_context_frame_resolution": ROLE_DETERMINISTIC,
	"visible_context_boundary": ROLE_DETERMINISTIC,
	"visible_context_answer": ROLE_DETERMINISTIC,
	"visible_context_trace_inspection": ROLE_DETERMINISTIC,
	"erp_report_execution": ROLE_DETERMINISTIC,
	"policy_boundary_rendering": ROLE_DETERMINISTIC,
	"business_reasoning_answer": ROLE_HEAVY_REASONING,
	"nbu_shadow_observation": ROLE_SHADOW_OBSERVER,
}


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _bool_or_none(value: Any) -> bool | None:
	if isinstance(value, bool):
		return value
	if value in (None, ""):
		return None
	text = _clean_text(value).lower()
	if text in {"true", "1"}:
		return True
	if text in {"false", "0"}:
		return False
	return None


def _agent_model_name(agent_meta: Dict[str, Any]) -> str:
	meta = _clean_dict(agent_meta)
	telemetry = _clean_dict(meta.get("telemetry"))
	for source in (meta, telemetry):
		for key in ("model_name", "model", "runtime_model", "selected_model"):
			value = _clean_text(source.get(key))
			if value:
				return value
	return ""


def _agent_fallback_used(agent_meta: Dict[str, Any]) -> bool | None:
	meta = _clean_dict(agent_meta)
	telemetry = _clean_dict(meta.get("telemetry"))
	for source in (meta, telemetry):
		for key in ("fallback_used", "degraded_message_fallback_used", "fallback"):
			value = _bool_or_none(source.get(key))
			if value is not None:
				return value
	return None


def _agent_fallback_reason(agent_meta: Dict[str, Any]) -> str:
	meta = _clean_dict(agent_meta)
	telemetry = _clean_dict(meta.get("telemetry"))
	for source in (meta, telemetry):
		for key in ("fallback_reason", "fallback_source", "fallback_mode", "degraded_reason"):
			value = _clean_text(source.get(key))
			if value:
				return value
	return ""


def expected_model_role_for_lane(lane: str) -> str:
	return TARGET_ROLE_BY_LANE.get(_clean_text(lane), "")


def _role_compliance(model_role: str, expected_role: str, *, fallback_used: bool) -> str:
	role = _clean_text(model_role) or ROLE_UNKNOWN
	expected = _clean_text(expected_role)
	if not expected:
		return COMPLIANCE_NOT_APPLICABLE
	if role == ROLE_UNKNOWN or fallback_used:
		return COMPLIANCE_UNKNOWN if fallback_used else COMPLIANCE_UNKNOWN
	if role == expected:
		return COMPLIANCE_COMPLIANT
	return COMPLIANCE_NON_COMPLIANT


def build_model_role_observability_contract(
	*,
	lane: str,
	role_owner: str,
	model_role: str = "",
	model_name: str = "",
	agent_meta: Dict[str, Any] | None = None,
	fallback_used: bool | None = None,
	fallback_reason: str = "",
	strict_mode_enforced: bool = False,
	runtime_source: str = "",
) -> Dict[str, Any]:
	meta = _clean_dict(agent_meta)
	resolved_role = _clean_text(model_role) or ROLE_UNKNOWN
	resolved_model_name = _clean_text(model_name) or _agent_model_name(meta) or "unknown"
	resolved_fallback_used = _agent_fallback_used(meta) if fallback_used is None else bool(fallback_used)
	if resolved_fallback_used is None:
		resolved_fallback_used = False
	resolved_fallback_reason = _clean_text(fallback_reason) or _agent_fallback_reason(meta)
	expected_role = expected_model_role_for_lane(lane)
	return {
		"type": MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane": _clean_text(lane),
		"role_owner": _clean_text(role_owner),
		"model_role": resolved_role,
		"expected_model_role": expected_role or "none",
		"model_name": resolved_model_name,
		"fallback_used": bool(resolved_fallback_used),
		"fallback_reason": resolved_fallback_reason,
		"role_compliance": _role_compliance(
			resolved_role,
			expected_role,
			fallback_used=bool(resolved_fallback_used),
		),
		"strict_mode_enforced": bool(strict_mode_enforced),
		"runtime_source": _clean_text(runtime_source) or "unknown",
		"created_at": _utc_now(),
	}
