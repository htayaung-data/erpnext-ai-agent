from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ERPBusinessReasoningActivationContract,
	build_erp_business_reasoning_activation_contract,
)
from ai_assistant_ui.qwen_chat.metadata import (
	capability_semantic_tags,
	report_family_semantic_tags,
	report_semantic_tags,
)


_RECOMMENDATION_SEMANTIC_TAG_ALLOWLIST = {
	"financial",
	"statement",
	"profitability",
	"aging",
	"overdue",
	"outstanding",
	"liquidity",
	"cash",
	"inventory",
	"stock",
	"balance",
	"asset",
	"liability",
	"equity",
	"performance",
}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _grounded_semantic_tags(
	*,
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
) -> List[str]:
	artifact = dict(latest_family_artifact or {})
	grounded_turn = dict(latest_grounded_turn or {})
	family_id = str(grounded_turn.get("artifact_family_id") or artifact.get("family_id") or "").strip()
	capability_id = str(artifact.get("capability_id") or "").strip()
	reports = list(
		dict.fromkeys(
			_clean_list(grounded_turn.get("artifact_source_reports"))
			+ _clean_list(artifact.get("source_reports"))
		)
	)
	values: List[str] = []
	if family_id:
		values.extend(report_family_semantic_tags(family_id))
	for report_name in reports:
		values.extend(report_semantic_tags(report_name))
	if not values and capability_id:
		values.extend(capability_semantic_tags(capability_id))
	return list(dict.fromkeys(str(value or "").strip() for value in values if str(value or "").strip()))


def _recommendation_policy(
	*,
	grounded_context_available: bool,
	grounded_semantic_tags: List[str],
) -> tuple[bool, List[str]]:
	if not grounded_context_available:
		return False, []
	observed = {
		str(value or "").strip()
		for value in (grounded_semantic_tags or [])
		if str(value or "").strip()
	}
	policy_basis = sorted(observed.intersection(_RECOMMENDATION_SEMANTIC_TAG_ALLOWLIST))
	return bool(policy_basis), policy_basis


def _reasoning_types_for_grounding(
	*,
	grounded_context_available: bool,
) -> List[str]:
	if not grounded_context_available:
		return []
	reasoning_types = ["interpretation", "explanation"]
	# Recognition and answerability are separate authorities. A grounded turn may
	# still ask for a recommendation-shaped continuation even when deterministic
	# policy later refuses to answer it from this source.
	reasoning_types.append("recommendation")
	reasoning_types.append("continuation_detail")
	return list(dict.fromkeys(reasoning_types))


def build_reasoning_activation_contract(
	*,
	request_id: str,
	session_id: str,
	message: str,
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	response_policy_contract: Dict[str, Any] | None = None,
) -> ERPBusinessReasoningActivationContract:
	grounded_turn = dict(latest_grounded_turn or {})
	artifact = dict(latest_family_artifact or {})
	assistant_payload = dict(latest_assistant_payload or {})
	response_policy = dict(response_policy_contract or {})
	grounded_context_available = bool(grounded_turn.get("grounded"))
	grounded_semantic_tags = _grounded_semantic_tags(
		latest_grounded_turn=grounded_turn,
		latest_family_artifact=artifact,
	)
	grounded_source_reports = list(
		dict.fromkeys(
			_clean_list(grounded_turn.get("artifact_source_reports"))
			+ _clean_list(artifact.get("source_reports"))
		)
	)
	recommendation_allowed, recommendation_policy_basis = _recommendation_policy(
		grounded_context_available=grounded_context_available,
		grounded_semantic_tags=grounded_semantic_tags,
	)
	allowed_reasoning_types = _reasoning_types_for_grounding(
		grounded_context_available=grounded_context_available,
	)
	activation_state = "eligible" if allowed_reasoning_types else "not_eligible"
	route_target = "reasoning_lane" if allowed_reasoning_types else "artifact_lane"
	reason = (
		"Grounded ERP context is available, so a later reasoning lane may activate if the current turn requests interpretation, explanation, bounded recommendation, or continuation detail."
		if allowed_reasoning_types
		else "No grounded ERP context is available yet, so ERP business reasoning is not eligible."
	)
	grounding_summary = {
		"company": str(grounded_turn.get("company") or "").strip(),
		"row_count": int(max(0, grounded_turn.get("row_count") or 0)),
		"date_range": dict(grounded_turn.get("date_range") or {}) if isinstance(grounded_turn.get("date_range"), dict) else {},
		"latest_assistant_title": str(assistant_payload.get("title") or "").strip(),
		"response_policy_mode": str(response_policy.get("policy_mode") or "").strip(),
		"raw_message_present": bool(str(message or "").strip()),
	}
	return build_erp_business_reasoning_activation_contract(
		request_id=request_id,
		session_id=session_id,
		grounded_context_available=grounded_context_available,
		grounded_source_request_id=str(grounded_turn.get("trace_request_id") or grounded_turn.get("request_id") or "").strip(),
		grounded_source_kind=str(grounded_turn.get("source_kind") or "").strip(),
		grounded_source_name=str(grounded_turn.get("source_name") or "").strip(),
		grounded_family_id=str(grounded_turn.get("artifact_family_id") or artifact.get("family_id") or "").strip(),
		grounded_artifact_type=str(grounded_turn.get("artifact_type") or artifact.get("artifact_type") or "").strip(),
		grounded_source_reports=grounded_source_reports,
		grounded_capability_id=str(artifact.get("capability_id") or "").strip(),
		grounded_semantic_tags=grounded_semantic_tags,
		grounding_summary=grounding_summary,
		recommendation_allowed=recommendation_allowed,
		recommendation_policy_basis=recommendation_policy_basis,
		allowed_reasoning_types=allowed_reasoning_types,
		activation_state=activation_state,
		route_target=route_target,
		reason=reason,
	)


def run_phase6a_reasoning_activation_probe() -> Dict[str, Any]:
	empty = build_reasoning_activation_contract(
		request_id="phase6a-empty",
		session_id="phase6a",
		message="what does this mean",
		latest_grounded_turn={},
		latest_family_artifact={},
		latest_assistant_payload={},
		response_policy_contract={},
	)
	if empty.activation_state != "not_eligible":
		raise RuntimeError("Phase 6A probe failed: empty grounding should not activate reasoning.")

	grounded = build_reasoning_activation_contract(
		request_id="phase6a-grounded",
		session_id="phase6a",
		message="what does this mean",
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-1",
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"row_count": 10,
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		},
		latest_family_artifact={
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"capability_id": "accounts_receivable_read",
		},
		latest_assistant_payload={"title": "Accounts Receivable Summary"},
		response_policy_contract={"policy_mode": "grounded_analysis"},
	)
	if grounded.activation_state != "eligible":
		raise RuntimeError("Phase 6A probe failed: grounded context should mark reasoning as eligible.")
	if "recommendation" not in list(grounded.allowed_reasoning_types):
		raise RuntimeError("Phase 6A probe failed: grounded context did not expose recommendation reasoning type.")
	if not bool(grounded.recommendation_allowed):
		raise RuntimeError("Phase 6A probe failed: grounded context did not expose governed recommendation policy.")
	return {
		"ok": True,
		"empty": empty.to_payload(),
		"grounded": grounded.to_payload(),
	}


def run_phase6a_recommendation_policy_probe() -> Dict[str, Any]:
	non_advisory = build_reasoning_activation_contract(
		request_id="phase6a-no-recommendation",
		session_id="phase6a",
		message="what does this mean",
		latest_grounded_turn={
			"grounded": True,
			"trace_request_id": "artifact-trace-2",
			"source_kind": "report",
			"source_name": "Sales Invoice List",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"row_count": 10,
			"date_range": {"report_date": "2026-03-26"},
			"artifact_family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Sales Invoice List"],
		},
		latest_family_artifact={
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Invoice List"],
			"capability_id": "sales_read",
		},
		latest_assistant_payload={"title": "Sales Invoice List"},
		response_policy_contract={"policy_mode": "grounded_analysis"},
	)
	if bool(non_advisory.recommendation_allowed):
		raise RuntimeError("Phase 6A recommendation-policy probe failed: transaction listing should not expose recommendation allowance.")
	return {
		"ok": True,
		"non_advisory": non_advisory.to_payload(),
	}
