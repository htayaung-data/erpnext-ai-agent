from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .model_role_observability import (
	COMPLIANCE_COMPLIANT,
	COMPLIANCE_NON_COMPLIANT,
	COMPLIANCE_UNKNOWN,
	ROLE_DETERMINISTIC,
	ROLE_HEAVY_REASONING,
	ROLE_LIGHT_SEMANTIC,
	ROLE_SHADOW_OBSERVER,
	ROLE_UNKNOWN,
	TARGET_ROLE_BY_LANE,
	expected_model_role_for_lane,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MODEL_ROLE_STRICT_READINESS_CONTRACT_TYPE = "qwen_model_role_strict_readiness_contract"
MODEL_ROLE_STRICT_READINESS_SUMMARY_TYPE = "qwen_model_role_strict_readiness_summary_contract"

STATUS_READY_FOR_STRICT = "ready_for_strict"
STATUS_MISSING_METADATA = "missing_metadata"
STATUS_UNKNOWN_RUNTIME = "unknown_runtime"
STATUS_FALLBACK_UNTRACKED = "fallback_untracked"
STATUS_ROLE_MISMATCH = "role_mismatch"
STATUS_NOT_APPLICABLE_DETERMINISTIC = "not_applicable_deterministic"

AI_MODEL_ROLES = {ROLE_LIGHT_SEMANTIC, ROLE_HEAVY_REASONING, ROLE_SHADOW_OBSERVER}
STRICT_READY_STATUSES = {STATUS_READY_FOR_STRICT, STATUS_NOT_APPLICABLE_DETERMINISTIC}


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[Any]:
	return list(values) if isinstance(values, list) else []


def _fallback_used(value: Any) -> bool | None:
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


def _status_reason(status: str, *, lane: str, role: str, expected_role: str) -> str:
	if status == STATUS_READY_FOR_STRICT:
		return "AI runtime lane has expected role, known model metadata, and no fallback gap."
	if status == STATUS_NOT_APPLICABLE_DETERMINISTIC:
		return "Deterministic lane is audited but excluded from AI model-role strict enforcement."
	if status == STATUS_MISSING_METADATA:
		return "No model-role observability contract was available for this lane."
	if status == STATUS_FALLBACK_UNTRACKED:
		return "Fallback state blocks strict readiness until it is absent or fully governed."
	if status == STATUS_ROLE_MISMATCH:
		return f"Observed model role {role or ROLE_UNKNOWN} does not match expected role {expected_role or 'none'} for lane {lane or 'unknown'}."
	return "Runtime role metadata is incomplete or unknown, so strict enforcement is not ready."


def _missing_fields(
	*,
	observability: Dict[str, Any],
	lane: str,
	role: str,
	expected_role: str,
	model_name: str,
	fallback_value_available: bool,
) -> List[str]:
	missing: List[str] = []
	if not observability:
		return ["model_role_observability"]
	if not lane:
		missing.append("lane")
	if not role or role == ROLE_UNKNOWN:
		missing.append("model_role")
	if not expected_role or expected_role == "none":
		missing.append("expected_model_role")
	if expected_role in AI_MODEL_ROLES and (not model_name or model_name in {"unknown", "none"}):
		missing.append("model_name")
	if expected_role in AI_MODEL_ROLES and not fallback_value_available:
		missing.append("fallback_used")
	return missing


def classify_model_role_strict_readiness(model_role_observability: Dict[str, Any] | None, *, lane: str = "") -> str:
	observability = _clean_dict(model_role_observability)
	if not observability:
		return STATUS_MISSING_METADATA
	resolved_lane = _clean_text(lane) or _clean_text(observability.get("lane"))
	role = _clean_text(observability.get("model_role")) or ROLE_UNKNOWN
	expected_role = _clean_text(observability.get("expected_model_role"))
	if not expected_role or expected_role == "none":
		expected_role = expected_model_role_for_lane(resolved_lane) or "none"
	compliance = _clean_text(observability.get("role_compliance")) or COMPLIANCE_UNKNOWN
	model_name = _clean_text(observability.get("model_name")) or "unknown"
	fallback_value_available = "fallback_used" in observability
	fallback_used = _fallback_used(observability.get("fallback_used"))
	if not resolved_lane or expected_role == "none":
		return STATUS_UNKNOWN_RUNTIME
	if role == ROLE_UNKNOWN:
		return STATUS_UNKNOWN_RUNTIME
	if role != expected_role or compliance == COMPLIANCE_NON_COMPLIANT:
		return STATUS_ROLE_MISMATCH
	if expected_role == ROLE_DETERMINISTIC and role == ROLE_DETERMINISTIC:
		return STATUS_NOT_APPLICABLE_DETERMINISTIC
	if not fallback_value_available:
		return STATUS_FALLBACK_UNTRACKED
	if fallback_used:
		return STATUS_FALLBACK_UNTRACKED
	if expected_role in AI_MODEL_ROLES and model_name in {"unknown", "none"}:
		return STATUS_UNKNOWN_RUNTIME
	if compliance != COMPLIANCE_COMPLIANT:
		return STATUS_UNKNOWN_RUNTIME
	return STATUS_READY_FOR_STRICT


def build_model_role_strict_readiness_contract(
	*,
	model_role_observability: Dict[str, Any] | None,
	lane: str = "",
	readiness_owner: str = "model_role_strict_readiness_auditor",
	strict_enforcement_enabled: bool = False,
) -> Dict[str, Any]:
	observability = _clean_dict(model_role_observability)
	resolved_lane = _clean_text(lane) or _clean_text(observability.get("lane"))
	role = _clean_text(observability.get("model_role")) or ROLE_UNKNOWN
	expected_role = _clean_text(observability.get("expected_model_role"))
	if not expected_role or expected_role == "none":
		expected_role = expected_model_role_for_lane(resolved_lane) or "none"
	model_name = _clean_text(observability.get("model_name")) or "unknown"
	fallback_value_available = "fallback_used" in observability
	fallback_used = _fallback_used(observability.get("fallback_used"))
	if fallback_used is None:
		fallback_used = False
	compliance = _clean_text(observability.get("role_compliance")) or COMPLIANCE_UNKNOWN
	status = classify_model_role_strict_readiness(observability, lane=resolved_lane)
	missing_fields = _missing_fields(
		observability=observability,
		lane=resolved_lane,
		role=role,
		expected_role=expected_role,
		model_name=model_name,
		fallback_value_available=fallback_value_available,
	)
	return {
		"type": MODEL_ROLE_STRICT_READINESS_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"readiness_owner": _clean_text(readiness_owner),
		"lane": resolved_lane or "unknown",
		"model_role": role,
		"expected_model_role": expected_role,
		"model_name": model_name,
		"role_compliance": compliance,
		"fallback_used": bool(fallback_used),
		"fallback_observed": bool(fallback_used),
		"fallback_reason": _clean_text(observability.get("fallback_reason")),
		"readiness_status": status,
		"strict_enforcement_ready": status == STATUS_READY_FOR_STRICT,
		"runtime_safe_without_model_enforcement": status == STATUS_NOT_APPLICABLE_DETERMINISTIC,
		"strict_enforcement_enabled": bool(strict_enforcement_enabled),
		"blocking": status not in STRICT_READY_STATUSES,
		"missing_fields": missing_fields,
		"requires_ai_runtime": expected_role in AI_MODEL_ROLES,
		"deterministic_lane": expected_role == ROLE_DETERMINISTIC,
		"readiness_reason": _status_reason(status, lane=resolved_lane, role=role, expected_role=expected_role),
		"created_at": _utc_now(),
	}


def build_model_role_strict_readiness_summary(
	*,
	observed_contracts: Iterable[Dict[str, Any]] | None = None,
	required_lanes: Iterable[str] | None = None,
	strict_enforcement_enabled: bool = False,
) -> Dict[str, Any]:
	contracts_by_lane: Dict[str, Dict[str, Any]] = {}
	for contract in observed_contracts or []:
		clean_contract = _clean_dict(contract)
		lane = _clean_text(clean_contract.get("lane"))
		if lane and lane not in contracts_by_lane:
			contracts_by_lane[lane] = clean_contract
	lanes = [_clean_text(value) for value in (required_lanes or TARGET_ROLE_BY_LANE.keys()) if _clean_text(value)]
	readiness_items = [
		build_model_role_strict_readiness_contract(
			model_role_observability=contracts_by_lane.get(lane),
			lane=lane,
			strict_enforcement_enabled=strict_enforcement_enabled,
		)
		for lane in lanes
	]
	status_counts: Dict[str, int] = {}
	for item in readiness_items:
		status = _clean_text(item.get("readiness_status")) or STATUS_UNKNOWN_RUNTIME
		status_counts[status] = status_counts.get(status, 0) + 1
	blocking_lanes = [
		_clean_text(item.get("lane"))
		for item in readiness_items
		if bool(item.get("blocking"))
	]
	return {
		"type": MODEL_ROLE_STRICT_READINESS_SUMMARY_TYPE,
		"contract_version": CONTRACT_VERSION,
		"strict_enforcement_enabled": bool(strict_enforcement_enabled),
		"required_lane_count": len(lanes),
		"observed_lane_count": len(contracts_by_lane),
		"ready_for_strict_count": status_counts.get(STATUS_READY_FOR_STRICT, 0),
		"deterministic_exempt_count": status_counts.get(STATUS_NOT_APPLICABLE_DETERMINISTIC, 0),
		"blocking_lane_count": len(blocking_lanes),
		"blocking_lanes": blocking_lanes,
		"status_counts": status_counts,
		"readiness_items": readiness_items,
		"created_at": _utc_now(),
	}
