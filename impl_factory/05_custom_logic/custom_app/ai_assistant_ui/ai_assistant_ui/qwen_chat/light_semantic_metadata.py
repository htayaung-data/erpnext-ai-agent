from __future__ import annotations

from typing import Any, Dict

from .model_role_coverage import build_model_role_contract_bundle
from .model_role_observability import ROLE_LIGHT_SEMANTIC
from .runtime_metadata_contract import LANE_CLASS_AI_SEMANTIC, build_runtime_metadata_envelope


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _semantic_status_fallback_reason(value: Any) -> str:
	status = _clean_text(value).lower() or "unknown"
	clean_status = "".join(ch if ch.isalnum() else "_" for ch in status).strip("_")
	return f"semantic_status_{clean_status or 'unknown'}"


def build_light_semantic_runtime_metadata_bundle(
	*,
	lane_id: str,
	role_owner: str,
	agent_meta: Dict[str, Any] | None,
	runtime_source: str,
	answer_mode: str = "semantic_interpretation",
	evidence_scope: str = "semantic_interpretation",
	authority_source: str = "runtime_agent_meta",
	preflight_status: str = "not_applicable",
	fallback_used: bool | None = None,
	fallback_reason: str = "",
	semantic_status: str,
) -> Dict[str, Dict[str, Any]]:
	clean_agent_meta = _clean_dict(agent_meta)
	clean_semantic_status = _clean_text(semantic_status) or "unknown"
	semantic_degraded = clean_semantic_status != "accepted"
	resolved_fallback_used = True if semantic_degraded else fallback_used
	resolved_fallback_reason = _clean_text(fallback_reason) or (_semantic_status_fallback_reason(clean_semantic_status) if semantic_degraded else "")
	model_role_bundle = build_model_role_contract_bundle(
		lane=_clean_text(lane_id),
		role_owner=_clean_text(role_owner),
		model_role=ROLE_LIGHT_SEMANTIC,
		agent_meta=clean_agent_meta,
		fallback_used=resolved_fallback_used,
		fallback_reason=resolved_fallback_reason,
		runtime_source=_clean_text(runtime_source) or "light_semantic_runtime_agent_meta",
		strict_enforcement_enabled=False,
	)
	observability = model_role_bundle["model_role_observability"]
	runtime_metadata_envelope = build_runtime_metadata_envelope(
		lane_id=_clean_text(lane_id),
		lane_class=LANE_CLASS_AI_SEMANTIC,
		model_role=_clean_text(observability.get("model_role")),
		model_name=_clean_text(observability.get("model_name")),
		fallback_used=observability.get("fallback_used") if "fallback_used" in observability else None,
		fallback_reason=_clean_text(observability.get("fallback_reason")),
		role_compliance=_clean_text(observability.get("role_compliance")),
		authority_source=_clean_text(authority_source) or "runtime_agent_meta",
		evidence_scope=_clean_text(evidence_scope) or "semantic_interpretation",
		answer_mode=_clean_text(answer_mode) or "semantic_interpretation",
		preflight_status=_clean_text(preflight_status) or "not_applicable",
		metadata_source=_clean_text(runtime_source) or "light_semantic_runtime_agent_meta",
	)
	return {
		"model_role_observability": observability,
		"model_role_strict_readiness": model_role_bundle["model_role_strict_readiness"],
		"runtime_metadata_envelope": runtime_metadata_envelope,
	}


def attach_light_semantic_metadata_to_agent_meta(
	agent_meta: Dict[str, Any] | None,
	metadata_bundle: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
	clean_agent_meta = _clean_dict(agent_meta)
	clean_agent_meta["model_role_observability"] = _clean_dict(metadata_bundle.get("model_role_observability"))
	clean_agent_meta["model_role_strict_readiness"] = _clean_dict(metadata_bundle.get("model_role_strict_readiness"))
	clean_agent_meta["runtime_metadata_envelope"] = _clean_dict(metadata_bundle.get("runtime_metadata_envelope"))
	return clean_agent_meta
