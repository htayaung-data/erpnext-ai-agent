from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List


CONTRACT_VERSION = "1.0"
POLICY_BOUNDARY_UNIFORMITY_CONTRACT_TYPE = "qwen_policy_boundary_uniformity_contract"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


def _clean_text_list(value: Any) -> List[str]:
	return [_clean_text(item) for item in _clean_list(value) if _clean_text(item)]


def _first_text(*values: Any) -> str:
	for value in values:
		text = _clean_text(value)
		if text:
			return text
	return ""


def _intent_from_authority_class(value: Any) -> str:
	authority_class = _clean_text(value).lower()
	if authority_class == "prediction":
		return "prediction"
	if authority_class in {"recommendation", "policy_decision"}:
		return "recommendation_action"
	if authority_class == "approval_action":
		return "approval_decision"
	if authority_class in {"causal_driver_analysis", "driver_analysis"}:
		return "cause_attribution"
	if authority_class in {"hidden_score_classification", "score", "classification"}:
		return "risk_scoring"
	if authority_class == "unsupported_analysis":
		return "unsupported_scope"
	return "none"


def _intent_from_visible_boundary(value: Any) -> str:
	boundary = _clean_text(value).lower()
	if boundary == "prediction_boundary":
		return "prediction"
	if boundary == "recommendation_boundary":
		return "recommendation_action"
	if boundary == "causal_boundary":
		return "cause_attribution"
	return "none"


def _intent_from_business_policy(policy_payload: Dict[str, Any]) -> str:
	policy = _clean_dict(policy_payload)
	if _clean_text(policy.get("policy_state")).lower() != "blocked":
		return "none"
	requested_authority = _clean_text(policy.get("requested_authority")).lower()
	if requested_authority == "prediction":
		return "prediction"
	if requested_authority == "recommendation":
		return "recommendation_action"
	if requested_authority in {"driver_analysis", "causal_driver_analysis"}:
		return "cause_attribution"
	if requested_authority in {"score", "classification"}:
		return "risk_scoring"
	if requested_authority in {"approval_action", "policy_decision"}:
		return "approval_decision"
	return _intent_from_authority_class(requested_authority)


def _blocked_claim_types(intent_class: str) -> List[str]:
	if intent_class == "prediction":
		return ["unsupported_prediction", "default_probability", "future_payment_outcome"]
	if intent_class == "recommendation_action":
		return ["unsupported_recommendation", "collection_action", "payment_priority_decision"]
	if intent_class == "cause_attribution":
		return ["unsupported_causal_claim", "unsupported_change_driver", "unsupported_trend_claim"]
	if intent_class == "risk_scoring":
		return ["unsupported_score", "hidden_weighted_risk_score", "unsupported_classification"]
	if intent_class == "approval_decision":
		return ["approval_decision", "credit_release_decision", "supplier_block_decision"]
	if intent_class == "territory_verification":
		return ["unsupported_attribute_verification"]
	if intent_class == "unsupported_scope":
		return ["unsupported_scope_claim"]
	return []


def _required_flags(intent_class: str) -> Dict[str, bool]:
	return {
		"approved_model_required": intent_class in {"prediction", "risk_scoring"},
		"approved_policy_required": intent_class in {
			"prediction",
			"recommendation_action",
			"risk_scoring",
			"approval_decision",
		},
		"approved_trend_required": intent_class == "cause_attribution",
	}


def _metric_fact_lines(metric_rows: Iterable[Dict[str, Any]]) -> List[str]:
	lines: List[str] = []
	for row in metric_rows or []:
		item = _clean_dict(row)
		label = _clean_text(item.get("label") or item.get("metric_key"))
		value = _clean_text(item.get("value"))
		if label and value:
			lines.append(f"{label}: {value}")
	return lines[:8]


def _safe_alternatives(intent_class: str, safe_next_action: str = "") -> List[str]:
	values: List[str] = []
	if safe_next_action:
		values.append(safe_next_action)
	if intent_class == "prediction":
		values.extend([
			"Show current ERP facts and aging evidence.",
			"Use an approved prediction model or payment-behavior trend view before forecasting.",
		])
	elif intent_class == "recommendation_action":
		values.extend([
			"Compare visible rows by the metrics shown.",
			"Apply an approved company decision policy before recommending action.",
		])
	elif intent_class == "cause_attribution":
		values.extend([
			"Show trend, event, payment-behavior, or transaction-history evidence.",
			"Limit the answer to current visible facts until cause evidence is available.",
		])
	elif intent_class == "risk_scoring":
		values.extend([
			"Show current risk indicators from approved ERP evidence.",
			"Use an approved scoring model before assigning a score.",
		])
	elif intent_class == "approval_decision":
		values.extend([
			"Show the supporting ERP facts.",
			"Apply an approved approval policy before making the decision.",
		])
	elif intent_class == "territory_verification":
		values.append("Use a governed result that includes the required attribute field.")
	return list(dict.fromkeys(value for value in values if value))[:5]


def _business_policy_dimensions(policy_payload: Dict[str, Any]) -> Dict[str, Any]:
	policy = _clean_dict(policy_payload)
	authority_policy = _clean_dict(policy.get("authority_policy"))
	authority_gate = _clean_dict(policy.get("authority_policy_gate"))
	return {
		"required_evidence_scope": {
			"required_metrics": _clean_text_list(authority_policy.get("required_evidence_metrics")),
			"required_artifacts": _clean_text_list(authority_policy.get("required_governed_artifacts")),
		},
		"available_evidence_scope": {
			"available_metrics": _clean_text_list(authority_gate.get("available_evidence_metrics")),
			"available_artifacts": _clean_text_list(authority_gate.get("available_governed_artifacts")),
			"missing_metrics": _clean_text_list(authority_gate.get("missing_evidence_metrics")),
			"missing_artifacts": _clean_text_list(authority_gate.get("missing_governed_artifacts")),
		},
		"allowed_visible_facts": _metric_fact_lines(policy.get("metric_rows") or []),
	}


def build_policy_boundary_uniformity_contract(
	*,
	raw_message: str = "",
	route: str,
	visible_authority_intent: str = "",
	business_policy_payload: Dict[str, Any] | None = None,
	nbu_authority_plan: Dict[str, Any] | None = None,
	final_answer_authority: Dict[str, Any] | None = None,
	selected_report_family: str = "",
	entity_type: str = "",
	evidence_scope: str = "",
	visible_metric_lines: Iterable[str] | None = None,
	safe_next_action: str = "",
) -> Dict[str, Any]:
	business_policy = _clean_dict(business_policy_payload)
	nbu_authority = _clean_dict(nbu_authority_plan)
	final_authority = _clean_dict(final_answer_authority)
	source = "none"
	intent_class = _intent_from_business_policy(business_policy)
	if intent_class != "none":
		source = "business_reasoning_authority_policy"
	policy_boundary = _clean_text(business_policy.get("blocked_variation"))
	if intent_class == "none":
		intent_class = _intent_from_authority_class(nbu_authority.get("authority_class"))
		approval_state = _clean_text(nbu_authority.get("approval_state")).lower()
		if intent_class != "none" and approval_state not in {"safe_read_authority", "allowed", ""}:
			source = "nbu_authority_plan"
			policy_boundary = _first_text(nbu_authority.get("approval_state"), nbu_authority.get("policy_artifact_required"))
		else:
			intent_class = "none"
	if intent_class == "none":
		intent_class = _intent_from_visible_boundary(visible_authority_intent)
		if intent_class != "none":
			source = "visible_context_authority_intent"
			policy_boundary = _clean_text(visible_authority_intent)
	if intent_class == "none":
		final_boundary = _clean_text(final_authority.get("policy_boundary"))
		if final_boundary and final_boundary != "none":
			source = "final_answer_authority"
			policy_boundary = final_boundary
			intent_class = _intent_from_visible_boundary(final_boundary)
			if intent_class == "none":
				intent_class = _intent_from_authority_class(final_boundary)
			if intent_class == "none":
				intent_class = "unsupported_scope"
	boundary_applies = intent_class != "none"
	policy_boundary = policy_boundary or ("none" if not boundary_applies else intent_class)
	business_dimensions = _business_policy_dimensions(business_policy)
	required_flags = _required_flags(intent_class)
	return {
		"type": POLICY_BOUNDARY_UNIFORMITY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"raw_message_present": bool(_clean_text(raw_message)),
		"route": _clean_text(route),
		"policy_owner": "policy_boundary_uniformity_contract",
		"source": source,
		"policy_intent_class": intent_class,
		"policy_boundary": policy_boundary,
		"boundary_applies": boundary_applies,
		"allowed_answer_mode": "bounded_current_evidence" if boundary_applies else "allowed",
		"selected_report_family": _clean_text(selected_report_family),
		"entity_type": _clean_text(entity_type),
		"required_evidence_scope": business_dimensions["required_evidence_scope"],
		"available_evidence_scope": {
			**business_dimensions["available_evidence_scope"],
			"evidence_scope": _clean_text(evidence_scope),
		},
		"approved_model_required": required_flags["approved_model_required"],
		"approved_policy_required": required_flags["approved_policy_required"],
		"approved_trend_required": required_flags["approved_trend_required"],
		"allowed_visible_facts": business_dimensions["allowed_visible_facts"]
		or [_clean_text(line) for line in (visible_metric_lines or []) if _clean_text(line)][:8],
		"blocked_claim_types": _blocked_claim_types(intent_class),
		"safe_alternative_actions": _safe_alternatives(
			intent_class,
			safe_next_action=_first_text(safe_next_action, business_policy.get("safe_next_action")),
		),
		"renderer_instruction": "render_bounded_natural_answer" if boundary_applies else "render_allowed_answer",
		"created_at": _utc_now(),
	}
