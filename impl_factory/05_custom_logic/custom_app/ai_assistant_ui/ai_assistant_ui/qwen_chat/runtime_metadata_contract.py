from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from .natural_business_understanding_contracts import CONTRACT_VERSION


RUNTIME_METADATA_ENVELOPE_CONTRACT_TYPE = "qwen_runtime_metadata_envelope_contract"

ROLE_LIGHT_SEMANTIC = "light_semantic"
ROLE_HEAVY_REASONING = "heavy_reasoning"
ROLE_DETERMINISTIC = "deterministic"
ROLE_SHADOW_OBSERVER = "shadow_observer"
ROLE_CONTROL_META = "control_meta"
ROLE_POLICY_BOUNDARY = "policy_boundary"
ROLE_NOT_APPLICABLE = "not_applicable"
ROLE_MODEL_BACKED_HELPER = "model_backed_helper"
ROLE_GOVERNED_TOOL_RUNTIME = "governed_tool_runtime"
ROLE_UNKNOWN = "unknown"

ALLOWED_MODEL_ROLES = {
	ROLE_LIGHT_SEMANTIC,
	ROLE_HEAVY_REASONING,
	ROLE_DETERMINISTIC,
	ROLE_SHADOW_OBSERVER,
	ROLE_CONTROL_META,
	ROLE_POLICY_BOUNDARY,
	ROLE_NOT_APPLICABLE,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_UNKNOWN,
}

LANE_CLASS_AI_SEMANTIC = "ai_semantic"
LANE_CLASS_AI_REASONING = "ai_reasoning"
LANE_CLASS_DETERMINISTIC_REPORT = "deterministic_report"
LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT = "deterministic_visible_context"
LANE_CLASS_POLICY_BOUNDARY = "policy_boundary"
LANE_CLASS_CONTROL_META = "control_meta"
LANE_CLASS_SHADOW_OBSERVER = "shadow_observer"
LANE_CLASS_ERROR_FALLBACK = "error_fallback"
LANE_CLASS_MODEL_BACKED_HELPER = "model_backed_helper"
LANE_CLASS_GOVERNED_TOOL_RUNTIME = "governed_tool_runtime"
LANE_CLASS_UNKNOWN = "unknown"

ALLOWED_LANE_CLASSES = {
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
	LANE_CLASS_POLICY_BOUNDARY,
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_SHADOW_OBSERVER,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	LANE_CLASS_UNKNOWN,
}

METADATA_STATUS_COVERED = "covered"
METADATA_STATUS_PARTIAL = "partial"
METADATA_STATUS_MISSING = "missing"
METADATA_STATUS_NOT_APPLICABLE = "not_applicable"
METADATA_STATUS_BLOCKED = "blocked"
METADATA_STATUS_NEEDS_RUNTIME_PROBE = "needs_runtime_probe"

ALLOWED_METADATA_STATUSES = {
	METADATA_STATUS_COVERED,
	METADATA_STATUS_PARTIAL,
	METADATA_STATUS_MISSING,
	METADATA_STATUS_NOT_APPLICABLE,
	METADATA_STATUS_BLOCKED,
	METADATA_STATUS_NEEDS_RUNTIME_PROBE,
}

STRICT_STATUS_READY = "strict_ready"
STRICT_STATUS_SOFT_BLOCK = "soft_block"
STRICT_STATUS_NOT_APPLICABLE = "not_applicable"
STRICT_STATUS_NOT_READY_MISSING_METADATA = "not_ready_missing_metadata"
STRICT_STATUS_NOT_READY_RUNTIME_PROBE_REQUIRED = "not_ready_runtime_probe_required"

ALLOWED_STRICT_READINESS_STATUSES = {
	STRICT_STATUS_READY,
	STRICT_STATUS_SOFT_BLOCK,
	STRICT_STATUS_NOT_APPLICABLE,
	STRICT_STATUS_NOT_READY_MISSING_METADATA,
	STRICT_STATUS_NOT_READY_RUNTIME_PROBE_REQUIRED,
}

COMPLIANCE_COMPLIANT = "compliant"
COMPLIANCE_NON_COMPLIANT = "non_compliant"
COMPLIANCE_UNKNOWN = "unknown"
COMPLIANCE_NOT_APPLICABLE = "not_applicable"

AI_LANE_CLASSES = {
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_SHADOW_OBSERVER,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
}
DETERMINISTIC_LANE_CLASSES = {LANE_CLASS_DETERMINISTIC_REPORT, LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT}
CONTROL_LANE_CLASSES = {LANE_CLASS_CONTROL_META, LANE_CLASS_ERROR_FALLBACK}

EXPECTED_ROLE_BY_LANE_CLASS = {
	LANE_CLASS_AI_SEMANTIC: ROLE_LIGHT_SEMANTIC,
	LANE_CLASS_AI_REASONING: ROLE_HEAVY_REASONING,
	LANE_CLASS_DETERMINISTIC_REPORT: ROLE_DETERMINISTIC,
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT: ROLE_DETERMINISTIC,
	LANE_CLASS_POLICY_BOUNDARY: ROLE_POLICY_BOUNDARY,
	LANE_CLASS_CONTROL_META: ROLE_CONTROL_META,
	LANE_CLASS_SHADOW_OBSERVER: ROLE_SHADOW_OBSERVER,
	LANE_CLASS_ERROR_FALLBACK: ROLE_NOT_APPLICABLE,
	LANE_CLASS_MODEL_BACKED_HELPER: ROLE_MODEL_BACKED_HELPER,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME: ROLE_GOVERNED_TOOL_RUNTIME,
}

COMPATIBLE_ROLES_BY_LANE_CLASS = {
	LANE_CLASS_AI_SEMANTIC: {ROLE_LIGHT_SEMANTIC},
	LANE_CLASS_AI_REASONING: {ROLE_HEAVY_REASONING},
	LANE_CLASS_DETERMINISTIC_REPORT: {ROLE_DETERMINISTIC},
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT: {ROLE_DETERMINISTIC},
	LANE_CLASS_POLICY_BOUNDARY: {ROLE_POLICY_BOUNDARY},
	LANE_CLASS_CONTROL_META: {ROLE_CONTROL_META, ROLE_NOT_APPLICABLE},
	LANE_CLASS_SHADOW_OBSERVER: {ROLE_SHADOW_OBSERVER},
	LANE_CLASS_ERROR_FALLBACK: {ROLE_NOT_APPLICABLE},
	LANE_CLASS_MODEL_BACKED_HELPER: {ROLE_MODEL_BACKED_HELPER},
	LANE_CLASS_GOVERNED_TOOL_RUNTIME: {ROLE_GOVERNED_TOOL_RUNTIME},
	LANE_CLASS_UNKNOWN: {ROLE_UNKNOWN},
}

CANONICAL_METADATA_FIELDS = (
	"model_role",
	"model_name",
	"fallback_used",
	"fallback_reason",
	"role_compliance",
	"authority_source",
	"evidence_scope",
	"answer_mode",
	"preflight_status",
	"metadata_status",
	"strict_readiness_status",
	"lane_id",
	"lane_class",
	"metadata_source",
	"runtime_probe_required",
)


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_role(value: Any) -> str:
	role = _clean_text(value)
	return role if role in ALLOWED_MODEL_ROLES else ROLE_UNKNOWN


def _clean_lane_class(value: Any) -> str:
	lane_class = _clean_text(value)
	return lane_class if lane_class in ALLOWED_LANE_CLASSES else LANE_CLASS_UNKNOWN


def _clean_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	return [_clean_text(item) for item in value if _clean_text(item)]


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


def expected_role_for_lane_class(lane_class: str) -> str:
	return EXPECTED_ROLE_BY_LANE_CLASS.get(_clean_lane_class(lane_class), ROLE_UNKNOWN)


def compatible_roles_for_lane_class(lane_class: str) -> List[str]:
	return sorted(COMPATIBLE_ROLES_BY_LANE_CLASS.get(_clean_lane_class(lane_class), {ROLE_UNKNOWN}))


def is_role_compatible_with_lane_class(*, lane_class: str, model_role: str) -> bool:
	resolved_lane_class = _clean_lane_class(lane_class)
	resolved_model_role = _clean_role(model_role)
	return resolved_model_role in COMPATIBLE_ROLES_BY_LANE_CLASS.get(resolved_lane_class, {ROLE_UNKNOWN})


def allowed_runtime_metadata_values() -> Dict[str, List[str]]:
	return {
		"model_roles": sorted(ALLOWED_MODEL_ROLES),
		"lane_classes": sorted(ALLOWED_LANE_CLASSES),
		"metadata_statuses": sorted(ALLOWED_METADATA_STATUSES),
		"strict_readiness_statuses": sorted(ALLOWED_STRICT_READINESS_STATUSES),
	}


def _required_missing_fields(
	*,
	lane_id: str,
	lane_class: str,
	model_role: str,
	model_name: str,
	fallback_used_value: bool | None,
	role_compliance: str,
	authority_source: str,
	preflight_status: str,
) -> List[str]:
	missing: List[str] = []
	if not lane_id:
		missing.append("lane_id")
	if lane_class == LANE_CLASS_UNKNOWN:
		missing.append("lane_class")
	if model_role == ROLE_UNKNOWN:
		missing.append("model_role")
	if model_role != ROLE_UNKNOWN and not is_role_compatible_with_lane_class(
		lane_class=lane_class,
		model_role=model_role,
	):
		missing.append("role_lane_mismatch")
	if lane_class in AI_LANE_CLASSES:
		if model_name in {"", "unknown", "none"}:
			missing.append("model_name")
		if fallback_used_value is None:
			missing.append("fallback_used")
		if not role_compliance or role_compliance == COMPLIANCE_UNKNOWN:
			missing.append("role_compliance")
	if lane_class in DETERMINISTIC_LANE_CLASSES | {LANE_CLASS_POLICY_BOUNDARY} and not authority_source:
		missing.append("authority_source")
	if lane_class == LANE_CLASS_POLICY_BOUNDARY and preflight_status != "bounded":
		missing.append("preflight_status")
	if lane_class == LANE_CLASS_CONTROL_META and model_role == ROLE_CONTROL_META and not authority_source:
		missing.append("authority_source")
	return missing


def classify_runtime_metadata_status(
	*,
	lane_class: str,
	model_role: str,
	missing_fields: List[str],
	runtime_probe_required: bool,
	blocked: bool,
) -> str:
	if blocked:
		return METADATA_STATUS_BLOCKED
	if missing_fields:
		return METADATA_STATUS_MISSING
	if runtime_probe_required:
		return METADATA_STATUS_NEEDS_RUNTIME_PROBE
	if lane_class in CONTROL_LANE_CLASSES and model_role == ROLE_NOT_APPLICABLE:
		return METADATA_STATUS_NOT_APPLICABLE
	return METADATA_STATUS_COVERED


def classify_strict_readiness_status(
	*,
	lane_class: str,
	model_role: str,
	role_compliance: str,
	fallback_used: bool | None,
	metadata_status: str,
	runtime_probe_required: bool,
) -> str:
	if metadata_status == METADATA_STATUS_MISSING:
		return STRICT_STATUS_NOT_READY_MISSING_METADATA
	if not is_role_compatible_with_lane_class(lane_class=lane_class, model_role=model_role):
		return STRICT_STATUS_SOFT_BLOCK
	if runtime_probe_required or metadata_status == METADATA_STATUS_NEEDS_RUNTIME_PROBE:
		return STRICT_STATUS_NOT_READY_RUNTIME_PROBE_REQUIRED
	if lane_class in DETERMINISTIC_LANE_CLASSES | CONTROL_LANE_CLASSES | {LANE_CLASS_POLICY_BOUNDARY}:
		return STRICT_STATUS_NOT_APPLICABLE
	if lane_class in AI_LANE_CLASSES:
		if model_role == ROLE_UNKNOWN or role_compliance != COMPLIANCE_COMPLIANT or fallback_used:
			return STRICT_STATUS_SOFT_BLOCK
		return STRICT_STATUS_READY
	return STRICT_STATUS_SOFT_BLOCK


def _recompute_metadata_semantics(payload: Dict[str, Any]) -> Dict[str, Any]:
	lane_id = _clean_text(payload.get("lane_id"))
	lane_class = _clean_lane_class(payload.get("lane_class"))
	model_role = _clean_role(payload.get("model_role"))
	model_name = _clean_text(payload.get("model_name")) or "unknown"
	fallback_used = _bool_or_none(payload.get("fallback_used"))
	role_compliance = _clean_text(payload.get("role_compliance")) or COMPLIANCE_UNKNOWN
	authority_source = _clean_text(payload.get("authority_source"))
	preflight_status = _clean_text(payload.get("preflight_status"))
	runtime_probe_required = bool(payload.get("runtime_probe_required"))
	blocked = bool(payload.get("metadata_status") == METADATA_STATUS_BLOCKED)
	missing_fields = _required_missing_fields(
		lane_id=lane_id,
		lane_class=lane_class,
		model_role=model_role,
		model_name=model_name,
		fallback_used_value=fallback_used,
		role_compliance=role_compliance,
		authority_source=authority_source,
		preflight_status=preflight_status,
	)
	metadata_status = classify_runtime_metadata_status(
		lane_class=lane_class,
		model_role=model_role,
		missing_fields=missing_fields,
		runtime_probe_required=runtime_probe_required,
		blocked=blocked,
	)
	strict_readiness_status = classify_strict_readiness_status(
		lane_class=lane_class,
		model_role=model_role,
		role_compliance=role_compliance,
		fallback_used=fallback_used,
		metadata_status=metadata_status,
		runtime_probe_required=runtime_probe_required,
	)
	return {
		"lane_id": lane_id,
		"lane_class": lane_class,
		"model_role": model_role,
		"role_lane_compatible": is_role_compatible_with_lane_class(lane_class=lane_class, model_role=model_role),
		"missing_fields": missing_fields,
		"metadata_status": metadata_status,
		"strict_readiness_status": strict_readiness_status,
		"strict_enforcement_ready": strict_readiness_status == STRICT_STATUS_READY,
	}


def build_runtime_metadata_envelope(
	*,
	lane_id: str,
	lane_class: str,
	model_role: str = "",
	model_name: str = "",
	fallback_used: bool | None = None,
	fallback_reason: str = "",
	role_compliance: str = "",
	authority_source: str = "",
	evidence_scope: str = "",
	answer_mode: str = "",
	preflight_status: str = "",
	metadata_source: str = "",
	runtime_probe_required: bool = False,
	blocked: bool = False,
) -> Dict[str, Any]:
	payload = {
		"lane_id": _clean_text(lane_id),
		"lane_class": _clean_lane_class(lane_class),
		"model_role": _clean_role(model_role),
		"model_name": _clean_text(model_name) or "unknown",
		"fallback_used": bool(_bool_or_none(fallback_used)) if _bool_or_none(fallback_used) is not None else None,
		"fallback_reason": _clean_text(fallback_reason),
		"role_compliance": _clean_text(role_compliance) or COMPLIANCE_UNKNOWN,
		"authority_source": _clean_text(authority_source),
		"evidence_scope": _clean_text(evidence_scope),
		"answer_mode": _clean_text(answer_mode),
		"preflight_status": _clean_text(preflight_status),
		"metadata_source": _clean_text(metadata_source) or "unknown",
		"runtime_probe_required": bool(runtime_probe_required),
		"metadata_status": METADATA_STATUS_BLOCKED if blocked else "",
	}
	computed = _recompute_metadata_semantics(payload)
	return {
		"type": RUNTIME_METADATA_ENVELOPE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane_id": payload["lane_id"],
		"lane_class": payload["lane_class"],
		"expected_model_role": expected_role_for_lane_class(payload["lane_class"]),
		"compatible_model_roles": compatible_roles_for_lane_class(payload["lane_class"]),
		"model_role": payload["model_role"],
		"role_lane_compatible": computed["role_lane_compatible"],
		"model_name": payload["model_name"],
		"fallback_used": payload["fallback_used"],
		"fallback_reason": payload["fallback_reason"],
		"role_compliance": payload["role_compliance"],
		"authority_source": payload["authority_source"],
		"evidence_scope": payload["evidence_scope"],
		"answer_mode": payload["answer_mode"],
		"preflight_status": payload["preflight_status"],
		"metadata_status": computed["metadata_status"],
		"strict_readiness_status": computed["strict_readiness_status"],
		"metadata_source": payload["metadata_source"],
		"runtime_probe_required": payload["runtime_probe_required"],
		"missing_fields": computed["missing_fields"],
		"strict_enforcement_ready": computed["strict_enforcement_ready"],
		"created_at": _utc_now(),
	}


def validate_runtime_metadata_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
	payload = dict(envelope or {})
	missing_canonical_fields = [field for field in CANONICAL_METADATA_FIELDS if field not in payload]
	invalid_values: List[str] = []
	if payload.get("model_role") not in ALLOWED_MODEL_ROLES:
		invalid_values.append("model_role")
	if payload.get("lane_class") not in ALLOWED_LANE_CLASSES:
		invalid_values.append("lane_class")
	if payload.get("metadata_status") not in ALLOWED_METADATA_STATUSES:
		invalid_values.append("metadata_status")
	if payload.get("strict_readiness_status") not in ALLOWED_STRICT_READINESS_STATUSES:
		invalid_values.append("strict_readiness_status")
	computed = _recompute_metadata_semantics(payload)
	supplied_missing_fields = _clean_list(payload.get("missing_fields"))
	recomputed_missing_fields = list(computed["missing_fields"])
	missing_fields_omitted = [field for field in recomputed_missing_fields if field not in supplied_missing_fields]
	metadata_status_mismatch = _clean_text(payload.get("metadata_status")) != computed["metadata_status"]
	strict_readiness_status_mismatch = _clean_text(payload.get("strict_readiness_status")) != computed["strict_readiness_status"]
	strict_enforcement_ready_mismatch = bool(payload.get("strict_enforcement_ready")) != bool(
		computed["strict_enforcement_ready"]
	)
	role_lane_mismatch = not bool(computed["role_lane_compatible"])
	strict_ready = payload.get("strict_readiness_status") == STRICT_STATUS_READY
	unknown_role_ready = payload.get("model_role") == ROLE_UNKNOWN and strict_ready
	missing_metadata_ready = bool(recomputed_missing_fields) and strict_ready
	role_lane_mismatch_ready = role_lane_mismatch and strict_ready
	valid = not (
		missing_canonical_fields
		or invalid_values
		or role_lane_mismatch
		or unknown_role_ready
		or missing_metadata_ready
		or role_lane_mismatch_ready
		or missing_fields_omitted
		or metadata_status_mismatch
		or strict_readiness_status_mismatch
		or strict_enforcement_ready_mismatch
	)
	return {
		"valid": valid,
		"missing_canonical_fields": missing_canonical_fields,
		"invalid_values": invalid_values,
		"role_lane_mismatch": role_lane_mismatch,
		"unknown_role_ready": unknown_role_ready,
		"missing_metadata_ready": missing_metadata_ready,
		"role_lane_mismatch_ready": role_lane_mismatch_ready,
		"recomputed_missing_fields": recomputed_missing_fields,
		"missing_fields_omitted": missing_fields_omitted,
		"recomputed_metadata_status": computed["metadata_status"],
		"metadata_status_mismatch": metadata_status_mismatch,
		"recomputed_strict_readiness_status": computed["strict_readiness_status"],
		"strict_readiness_status_mismatch": strict_readiness_status_mismatch,
		"recomputed_strict_enforcement_ready": computed["strict_enforcement_ready"],
		"strict_enforcement_ready_mismatch": strict_enforcement_ready_mismatch,
	}
