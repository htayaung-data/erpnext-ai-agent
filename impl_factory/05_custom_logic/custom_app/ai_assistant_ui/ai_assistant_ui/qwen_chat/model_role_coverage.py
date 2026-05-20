from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .model_role_observability import (
	ROLE_DETERMINISTIC,
	TARGET_ROLE_BY_LANE,
	build_model_role_observability_contract,
)
from .model_role_strict_readiness import (
	STATUS_MISSING_METADATA,
	build_model_role_strict_readiness_contract,
	build_model_role_strict_readiness_summary,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MODEL_ROLE_COVERAGE_CONTRACT_TYPE = "qwen_model_role_coverage_contract"

ACTIVE_MODEL_ROLE_COVERAGE_LANES = [
	"frontdoor_semantic_classification",
	"fresh_query_interpretation",
	"followup_interpretation",
	"semantic_reasoning_activation",
	"semantic_repair_intent",
	"visible_context_followup",
	"visible_context_trace_inspection",
	"erp_report_execution",
	"policy_boundary_rendering",
	"business_reasoning_answer",
	"nbu_shadow_observation",
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _required_lanes(values: Iterable[str] | None = None) -> List[str]:
	seen: set[str] = set()
	out: List[str] = []
	for raw_value in values or ACTIVE_MODEL_ROLE_COVERAGE_LANES:
		lane = _clean_text(raw_value)
		if not lane or lane in seen:
			continue
		seen.add(lane)
		out.append(lane)
	return out


def build_model_role_contract_bundle(
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
	strict_enforcement_enabled: bool = False,
) -> Dict[str, Dict[str, Any]]:
	observability = build_model_role_observability_contract(
		lane=lane,
		role_owner=role_owner,
		model_role=model_role,
		model_name=model_name,
		agent_meta=agent_meta,
		fallback_used=fallback_used,
		fallback_reason=fallback_reason,
		strict_mode_enforced=strict_mode_enforced,
		runtime_source=runtime_source,
	)
	readiness = build_model_role_strict_readiness_contract(
		model_role_observability=observability,
		lane=lane,
		strict_enforcement_enabled=strict_enforcement_enabled,
	)
	return {
		"model_role_observability": observability,
		"model_role_strict_readiness": readiness,
	}


def build_deterministic_model_role_contract_bundle(
	*,
	lane: str,
	role_owner: str,
	runtime_source: str,
	strict_enforcement_enabled: bool = False,
) -> Dict[str, Dict[str, Any]]:
	return build_model_role_contract_bundle(
		lane=lane,
		role_owner=role_owner,
		model_role=ROLE_DETERMINISTIC,
		model_name="none",
		fallback_used=False,
		strict_mode_enforced=False,
		runtime_source=runtime_source,
		strict_enforcement_enabled=strict_enforcement_enabled,
	)


def build_model_role_coverage_contract(
	*,
	observed_contracts: Iterable[Dict[str, Any]] | None = None,
	required_lanes: Iterable[str] | None = None,
	coverage_owner: str = "model_role_coverage_expansion_auditor",
	strict_enforcement_enabled: bool = False,
) -> Dict[str, Any]:
	required = _required_lanes(required_lanes)
	contracts_by_lane: Dict[str, Dict[str, Any]] = {}
	for contract in observed_contracts or []:
		clean_contract = _clean_dict(contract)
		lane = _clean_text(clean_contract.get("lane"))
		if not lane or lane in contracts_by_lane:
			continue
		contracts_by_lane[lane] = clean_contract
	observed_lanes = [lane for lane in required if lane in contracts_by_lane]
	uncovered_lanes = [lane for lane in required if lane not in contracts_by_lane]
	summary = build_model_role_strict_readiness_summary(
		observed_contracts=[contracts_by_lane[lane] for lane in observed_lanes],
		required_lanes=required,
		strict_enforcement_enabled=strict_enforcement_enabled,
	)
	blocking_lanes = _clean_list(summary.get("blocking_lanes"))
	status_counts = _clean_dict(summary.get("status_counts"))
	coverage_complete = not uncovered_lanes
	blocking = bool(blocking_lanes)
	if not observed_lanes:
		coverage_status = "no_observability"
	elif blocking:
		coverage_status = "partial_blocked"
	else:
		coverage_status = "coverage_ready"
	return {
		"type": MODEL_ROLE_COVERAGE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"coverage_owner": _clean_text(coverage_owner),
		"coverage_status": coverage_status,
		"coverage_complete": bool(coverage_complete),
		"global_strict_enforcement_safe": bool(coverage_complete and not blocking),
		"strict_enforcement_enabled": bool(strict_enforcement_enabled),
		"required_lane_count": len(required),
		"observed_lane_count": len(observed_lanes),
		"uncovered_lane_count": len(uncovered_lanes),
		"blocking_lane_count": len(blocking_lanes),
		"required_lanes": required,
		"observed_lanes": observed_lanes,
		"uncovered_lanes": uncovered_lanes,
		"blocking_lanes": blocking_lanes,
		"status_counts": status_counts,
		"missing_metadata_count": int(status_counts.get(STATUS_MISSING_METADATA) or 0),
		"expected_roles_by_lane": {
			lane: _clean_text(TARGET_ROLE_BY_LANE.get(lane)) or "none"
			for lane in required
		},
		"strict_readiness_summary": summary,
		"created_at": _utc_now(),
	}
