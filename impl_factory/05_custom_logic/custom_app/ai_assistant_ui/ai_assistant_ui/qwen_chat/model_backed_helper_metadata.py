from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .runtime_metadata_contract import (
	COMPLIANCE_COMPLIANT,
	COMPLIANCE_NOT_APPLICABLE,
	COMPLIANCE_UNKNOWN,
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	LANE_CLASS_MODEL_BACKED_HELPER,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_NOT_APPLICABLE,
	STRICT_STATUS_READY,
	build_runtime_metadata_envelope,
)


MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE = "qwen_model_role_observability_contract"
MODEL_ROLE_STRICT_READINESS_CONTRACT_TYPE = "qwen_model_role_strict_readiness_contract"


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


def _strict_readiness_contract(*, lane_id: str, envelope: Dict[str, Any]) -> Dict[str, Any]:
	strict_status = _clean_text(envelope.get("strict_readiness_status"))
	return {
		"type": MODEL_ROLE_STRICT_READINESS_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane": _clean_text(lane_id),
		"status": "ready_for_strict" if strict_status == STRICT_STATUS_READY else strict_status,
		"strict_readiness_status": strict_status,
		"strict_enforcement_ready": bool(envelope.get("strict_enforcement_ready")),
		"strict_enforcement_enabled": False,
		"blocking_reason": "none" if strict_status == STRICT_STATUS_READY else "helper_provenance_not_strict_ready",
		"created_at": _utc_now(),
	}


def build_model_backed_helper_runtime_metadata_bundle(
	*,
	lane_id: str,
	role_owner: str,
	agent_meta: Dict[str, Any] | None,
	runtime_source: str,
	answer_mode: str,
	evidence_scope: str,
	authority_source: str = "model_backed_helper_runtime",
	preflight_status: str = "passed",
	fallback_used: bool | None = None,
	fallback_reason: str = "",
) -> Dict[str, Dict[str, Any]]:
	clean_agent_meta = _clean_dict(agent_meta)
	resolved_fallback_used = _agent_fallback_used(clean_agent_meta) if fallback_used is None else bool(fallback_used)
	if resolved_fallback_used is None:
		resolved_fallback_used = False
	resolved_fallback_reason = _clean_text(fallback_reason) or _agent_fallback_reason(clean_agent_meta)
	model_name = _agent_model_name(clean_agent_meta) or "unknown"
	role_compliance = COMPLIANCE_COMPLIANT if model_name not in {"", "unknown", "none"} else COMPLIANCE_UNKNOWN
	envelope = build_runtime_metadata_envelope(
		lane_id=_clean_text(lane_id),
		lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
		model_role=ROLE_MODEL_BACKED_HELPER,
		model_name=model_name,
		fallback_used=resolved_fallback_used,
		fallback_reason=resolved_fallback_reason,
		role_compliance=role_compliance,
		authority_source=_clean_text(authority_source) or "model_backed_helper_runtime",
		evidence_scope=_clean_text(evidence_scope) or "model_backed_helper_output",
		answer_mode=_clean_text(answer_mode) or _clean_text(lane_id),
		preflight_status=_clean_text(preflight_status) or "passed",
		metadata_source=_clean_text(runtime_source) or "model_backed_helper_runtime_agent_meta",
	)
	observability = {
		"type": MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane": _clean_text(lane_id),
		"role_owner": _clean_text(role_owner),
		"model_role": ROLE_MODEL_BACKED_HELPER,
		"expected_model_role": ROLE_MODEL_BACKED_HELPER,
		"model_name": model_name,
		"fallback_used": bool(resolved_fallback_used),
		"fallback_reason": resolved_fallback_reason,
		"role_compliance": role_compliance,
		"strict_mode_enforced": False,
		"runtime_source": _clean_text(runtime_source) or "model_backed_helper_runtime_agent_meta",
		"created_at": _utc_now(),
	}
	return {
		"model_role_observability": observability,
		"model_role_strict_readiness": _strict_readiness_contract(lane_id=lane_id, envelope=envelope),
		"runtime_metadata_envelope": envelope,
	}



def build_governed_tool_runtime_metadata_bundle(
	*,
	lane_id: str,
	role_owner: str,
	agent_meta: Dict[str, Any] | None,
	runtime_source: str,
	answer_mode: str = "compiled_read_query",
	evidence_scope: str = "governed_tool_runtime",
	authority_source: str = "compiled_query_contract",
	preflight_status: str = "passed",
	fallback_used: bool | None = None,
	fallback_reason: str = "",
) -> Dict[str, Dict[str, Any]]:
	clean_agent_meta = _clean_dict(agent_meta)
	resolved_fallback_used = _agent_fallback_used(clean_agent_meta) if fallback_used is None else bool(fallback_used)
	if resolved_fallback_used is None:
		resolved_fallback_used = False
	resolved_fallback_reason = _clean_text(fallback_reason) or _agent_fallback_reason(clean_agent_meta)
	model_name = _agent_model_name(clean_agent_meta) or "unknown"
	role_compliance = COMPLIANCE_COMPLIANT if model_name not in {"", "unknown", "none"} else COMPLIANCE_UNKNOWN
	envelope = build_runtime_metadata_envelope(
		lane_id=_clean_text(lane_id),
		lane_class=LANE_CLASS_GOVERNED_TOOL_RUNTIME,
		model_role=ROLE_GOVERNED_TOOL_RUNTIME,
		model_name=model_name,
		fallback_used=resolved_fallback_used,
		fallback_reason=resolved_fallback_reason,
		role_compliance=role_compliance,
		authority_source=_clean_text(authority_source) or "compiled_query_contract",
		evidence_scope=_clean_text(evidence_scope) or "governed_tool_runtime",
		answer_mode=_clean_text(answer_mode) or "compiled_read_query",
		preflight_status=_clean_text(preflight_status) or "passed",
		metadata_source=_clean_text(runtime_source) or "governed_tool_runtime_agent_meta",
	)
	observability = {
		"type": MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane": _clean_text(lane_id),
		"role_owner": _clean_text(role_owner),
		"model_role": ROLE_GOVERNED_TOOL_RUNTIME,
		"expected_model_role": ROLE_GOVERNED_TOOL_RUNTIME,
		"model_name": model_name,
		"fallback_used": bool(resolved_fallback_used),
		"fallback_reason": resolved_fallback_reason,
		"role_compliance": role_compliance,
		"strict_mode_enforced": False,
		"runtime_source": _clean_text(runtime_source) or "governed_tool_runtime_agent_meta",
		"created_at": _utc_now(),
	}
	return {
		"model_role_observability": observability,
		"model_role_strict_readiness": _strict_readiness_contract(lane_id=lane_id, envelope=envelope),
		"runtime_metadata_envelope": envelope,
	}


def attach_governed_tool_runtime_metadata_to_payload(
	runtime_payload: Dict[str, Any] | None,
	*,
	lane_id: str,
	role_owner: str,
	runtime_source: str,
	answer_mode: str = "compiled_read_query",
	evidence_scope: str = "governed_tool_runtime",
	authority_source: str = "compiled_query_contract",
	fallback_used: bool | None = None,
	fallback_reason: str = "",
) -> Dict[str, Any]:
	payload = _clean_dict(runtime_payload)
	agent_meta = payload.get("agent_meta") if isinstance(payload.get("agent_meta"), dict) else {}
	metadata_bundle = build_governed_tool_runtime_metadata_bundle(
		lane_id=lane_id,
		role_owner=role_owner,
		agent_meta=agent_meta,
		runtime_source=runtime_source,
		answer_mode=answer_mode,
		evidence_scope=evidence_scope,
		authority_source=authority_source,
		preflight_status="passed",
		fallback_used=fallback_used,
		fallback_reason=fallback_reason,
	)
	payload["agent_meta"] = attach_helper_metadata_to_agent_meta(agent_meta, metadata_bundle)
	payload["model_role_observability"] = metadata_bundle["model_role_observability"]
	payload["model_role_strict_readiness"] = metadata_bundle["model_role_strict_readiness"]
	payload["runtime_metadata_envelope"] = metadata_bundle["runtime_metadata_envelope"]
	return payload


def build_not_applicable_helper_runtime_metadata_bundle(
	*,
	lane_id: str,
	role_owner: str,
	runtime_source: str,
	answer_mode: str,
	authority_source: str = "control_meta",
	fallback_reason: str = "",
) -> Dict[str, Dict[str, Any]]:
	envelope = build_runtime_metadata_envelope(
		lane_id=_clean_text(lane_id),
		lane_class=LANE_CLASS_CONTROL_META,
		model_role=ROLE_NOT_APPLICABLE,
		model_name="none",
		fallback_used=False,
		fallback_reason=_clean_text(fallback_reason),
		role_compliance=COMPLIANCE_NOT_APPLICABLE,
		authority_source=_clean_text(authority_source) or "control_meta",
		evidence_scope="control_meta",
		answer_mode=_clean_text(answer_mode) or _clean_text(lane_id),
		preflight_status="passed",
		metadata_source=_clean_text(runtime_source) or "not_applicable_helper_metadata",
	)
	observability = {
		"type": MODEL_ROLE_OBSERVABILITY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"lane": _clean_text(lane_id),
		"role_owner": _clean_text(role_owner),
		"model_role": ROLE_NOT_APPLICABLE,
		"expected_model_role": "not_applicable",
		"model_name": "none",
		"fallback_used": False,
		"fallback_reason": _clean_text(fallback_reason),
		"role_compliance": COMPLIANCE_NOT_APPLICABLE,
		"strict_mode_enforced": False,
		"runtime_source": _clean_text(runtime_source) or "not_applicable_helper_metadata",
		"created_at": _utc_now(),
	}
	return {
		"model_role_observability": observability,
		"model_role_strict_readiness": _strict_readiness_contract(lane_id=lane_id, envelope=envelope),
		"runtime_metadata_envelope": envelope,
	}


def attach_helper_metadata_to_agent_meta(
	agent_meta: Dict[str, Any] | None,
	metadata_bundle: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
	clean_agent_meta = _clean_dict(agent_meta)
	clean_agent_meta["model_role_observability"] = _clean_dict(metadata_bundle.get("model_role_observability"))
	clean_agent_meta["model_role_strict_readiness"] = _clean_dict(metadata_bundle.get("model_role_strict_readiness"))
	clean_agent_meta["runtime_metadata_envelope"] = _clean_dict(metadata_bundle.get("runtime_metadata_envelope"))
	return clean_agent_meta
