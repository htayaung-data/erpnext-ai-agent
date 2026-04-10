from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_definition_formula_registry import (
	validate_business_threshold_registry,
)
from ai_assistant_ui.qwen_chat.business_rule_registry import validate_business_rule_registry
from ai_assistant_ui.qwen_chat.metadata import get_business_threshold_spec


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	items: List[str] = []
	for item in value:
		text = str(item or "").strip()
		if text:
			items.append(text)
	return items


def _coerce_number(value: Any) -> float | None:
	if value is None or value == "":
		return None
	try:
		return float(value)
	except Exception:
		return None


def _company_scope_matches(spec: Dict[str, Any], company_name: str) -> bool:
	if not str(company_name or "").strip():
		return True
	company_scope = _as_str_list(spec.get("company_scope"))
	if not company_scope:
		return False
	normalized_scope = {str(value or "").strip().lower() for value in company_scope if str(value or "").strip()}
	return "global" in normalized_scope or str(company_name or "").strip().lower() in normalized_scope


def _band_matches(band: Dict[str, Any], observed_value: float) -> bool:
	lower_inclusive = _coerce_number(band.get("lower_bound_inclusive"))
	lower_exclusive = _coerce_number(band.get("lower_bound_exclusive"))
	upper_inclusive = _coerce_number(band.get("upper_bound_inclusive"))
	upper_exclusive = _coerce_number(band.get("upper_bound_exclusive"))
	if lower_inclusive is not None and observed_value < lower_inclusive:
		return False
	if lower_exclusive is not None and observed_value <= lower_exclusive:
		return False
	if upper_inclusive is not None and observed_value > upper_inclusive:
		return False
	if upper_exclusive is not None and observed_value >= upper_exclusive:
		return False
	return True


@dataclass(frozen=True)
class BusinessThresholdEvaluationContract:
	threshold_id: str
	requested_company_name: str
	resolution_state: str
	activation_state: str = ""
	label: str = ""
	threshold_basis: str = ""
	band_direction: str = ""
	observed_value: float = 0.0
	matched_band_label: str = ""
	matched_band: Dict[str, Any] = field(default_factory=dict)
	business_rule_id: str = ""
	blocked_reason: str = ""
	reason: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_business_threshold_evaluation_contract",
			"contract_version": "1.0",
			"threshold_id": self.threshold_id,
			"requested_company_name": self.requested_company_name,
			"resolution_state": self.resolution_state,
			"activation_state": self.activation_state,
			"label": self.label,
			"threshold_basis": self.threshold_basis,
			"band_direction": self.band_direction,
			"observed_value": self.observed_value,
			"matched_band_label": self.matched_band_label,
			"matched_band": dict(self.matched_band),
			"business_rule_id": self.business_rule_id,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
		}


def evaluate_business_threshold(
	threshold_id: Any,
	*,
	observed_value: Any,
	company_name: str = "",
) -> BusinessThresholdEvaluationContract:
	target = str(threshold_id or "").strip()
	if not target:
		return BusinessThresholdEvaluationContract(
			threshold_id="",
			requested_company_name=str(company_name or "").strip(),
			resolution_state="undefined",
			reason="No threshold_id was provided.",
		)
	spec = get_business_threshold_spec(target)
	if not spec:
		return BusinessThresholdEvaluationContract(
			threshold_id=target,
			requested_company_name=str(company_name or "").strip(),
			resolution_state="undefined",
			reason=f"No governed threshold set matched '{target}'.",
		)
	if not _company_scope_matches(spec, company_name):
		return BusinessThresholdEvaluationContract(
			threshold_id=target,
			requested_company_name=str(company_name or "").strip(),
			resolution_state="blocked",
			label=str(spec.get("label") or "").strip(),
			threshold_basis=str(spec.get("threshold_basis") or "").strip(),
			band_direction=str(spec.get("band_direction") or "").strip(),
			business_rule_id=str(spec.get("business_rule_id") or "").strip(),
			blocked_reason="threshold_out_of_company_scope",
			reason=(
				f"Threshold set '{target}' is not configured for company scope "
				f"'{str(company_name or '').strip()}'."
			),
		)
	activation_state = str(spec.get("activation_state") or "").strip()
	if activation_state != "active":
		return BusinessThresholdEvaluationContract(
			threshold_id=target,
			requested_company_name=str(company_name or "").strip(),
			resolution_state="blocked",
			activation_state=activation_state,
			label=str(spec.get("label") or "").strip(),
			threshold_basis=str(spec.get("threshold_basis") or "").strip(),
			band_direction=str(spec.get("band_direction") or "").strip(),
			business_rule_id=str(spec.get("business_rule_id") or "").strip(),
			blocked_reason=str(spec.get("blocked_reason") or "").strip(),
			reason=(
				f"Threshold set '{target}' is not runtime-active because activation_state is "
				f"'{activation_state or 'unknown'}'."
			),
		)

	numeric_value = _coerce_number(observed_value)
	if numeric_value is None:
		return BusinessThresholdEvaluationContract(
			threshold_id=target,
			requested_company_name=str(company_name or "").strip(),
			resolution_state="undefined",
			activation_state=activation_state,
			label=str(spec.get("label") or "").strip(),
			threshold_basis=str(spec.get("threshold_basis") or "").strip(),
			band_direction=str(spec.get("band_direction") or "").strip(),
			business_rule_id=str(spec.get("business_rule_id") or "").strip(),
			reason="Observed threshold value must be numeric.",
		)

	for band in spec.get("bands") or []:
		if not isinstance(band, dict):
			continue
		if _band_matches(band, numeric_value):
			return BusinessThresholdEvaluationContract(
				threshold_id=target,
				requested_company_name=str(company_name or "").strip(),
				resolution_state="active",
				activation_state=activation_state,
				label=str(spec.get("label") or "").strip(),
				threshold_basis=str(spec.get("threshold_basis") or "").strip(),
				band_direction=str(spec.get("band_direction") or "").strip(),
				observed_value=float(numeric_value),
				matched_band_label=str(band.get("label") or "").strip(),
				matched_band=dict(band),
				business_rule_id=str(spec.get("business_rule_id") or "").strip(),
				reason=(
					f"Observed value {float(numeric_value):.4f} matched band "
					f"'{str(band.get('label') or '').strip()}' for threshold '{target}'."
				),
			)

	return BusinessThresholdEvaluationContract(
		threshold_id=target,
		requested_company_name=str(company_name or "").strip(),
		resolution_state="undefined",
		activation_state=activation_state,
		label=str(spec.get("label") or "").strip(),
		threshold_basis=str(spec.get("threshold_basis") or "").strip(),
		band_direction=str(spec.get("band_direction") or "").strip(),
		observed_value=float(numeric_value),
		business_rule_id=str(spec.get("business_rule_id") or "").strip(),
		reason=f"Observed value {float(numeric_value):.4f} did not match any configured threshold band.",
	)


def run_business_threshold_semantics_probe() -> Dict[str, Any]:
	threshold_validation = validate_business_threshold_registry()
	rule_validation = validate_business_rule_registry()
	company_name = "Mingalar Mobile Distribution Co., Ltd."
	within_limit = evaluate_business_threshold(
		"customer_credit_utilization_policy_bands",
		observed_value=0.0495,
		company_name=company_name,
	)
	limit_exceeded = evaluate_business_threshold(
		"customer_credit_utilization_policy_bands",
		observed_value=1.125,
		company_name=company_name,
	)
	overdue_blocked = evaluate_business_threshold(
		"customer_overdue_ratio_severity_bands",
		observed_value=0.42,
		company_name=company_name,
	)
	ok = (
		threshold_validation.status == "pass"
		and rule_validation.status == "pass"
		and within_limit.resolution_state == "active"
		and within_limit.matched_band_label == "within_limit"
		and limit_exceeded.resolution_state == "active"
		and limit_exceeded.matched_band_label == "limit_exceeded"
		and overdue_blocked.resolution_state == "blocked"
	)
	return {
		"ok": ok,
		"threshold_validation": threshold_validation.to_payload(),
		"business_rule_validation": rule_validation.to_payload(),
		"within_limit": within_limit.to_payload(),
		"limit_exceeded": limit_exceeded.to_payload(),
		"overdue_blocked": overdue_blocked.to_payload(),
	}
