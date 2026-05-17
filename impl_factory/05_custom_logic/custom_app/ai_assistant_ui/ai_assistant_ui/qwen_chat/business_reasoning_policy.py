from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	get_composite_family_spec,
	get_report_family_spec,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import get_metric_label


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().replace("_", " ").split())


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _format_number(value: Any) -> str:
	number = _numeric(value)
	return f"{number:,.2f}".rstrip("0").rstrip(".")


def _format_metric_value(metric_key: str, value: Any, display_value: str = "") -> str:
	if _clean_text(display_value):
		return _clean_text(display_value)
	key = _clean_text(metric_key)
	if key.endswith("_ratio") or "utilization" in key or key.endswith("_percent"):
		number = _numeric(value)
		if -1.0 <= number <= 1.0:
			number *= 100
		return f"{_format_number(number)}%"
	if "amount" in key or "revenue" in key or "profit" in key or "value" in key:
		return f"{_format_number(value)} MMK"
	return _format_number(value)


def _source_composite_family_id(artifact_payload: Dict[str, Any]) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	filters = artifact.get("filters") if isinstance(artifact.get("filters"), dict) else {}
	return _clean_text(dimensions.get("source_composite_family_id") or filters.get("composite_family_id"))


def _source_composite_family_label(family_spec: Dict[str, Any], artifact_payload: Dict[str, Any]) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	return _clean_text(
		dimensions.get("source_composite_family_label")
		or family_spec.get("label")
		or family_spec.get("family_label")
		or "ERP result"
	)


def _family_spec_active(family_spec: Dict[str, Any]) -> bool:
	if not family_spec:
		return False
	state = _clean_text(family_spec.get("activation_state") or family_spec.get("coverage_status"))
	return not state or state == "active"


def _family_spec_has_reasoning_authority(family_spec: Dict[str, Any]) -> bool:
	return bool(
		family_spec.get("blocked_variations")
		or family_spec.get("driver_analysis_policy")
		or family_spec.get("business_reasoning_authority_policies")
	)


def _authority_family_spec_for_artifact(artifact_payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	composite_family_id = _source_composite_family_id(artifact)
	if composite_family_id:
		composite_spec = get_composite_family_spec(composite_family_id)
		if _family_spec_active(composite_spec) and _family_spec_has_reasoning_authority(composite_spec):
			return composite_family_id, composite_spec
	report_family_id = _clean_text(artifact.get("family_id"))
	if report_family_id:
		report_family_spec = get_report_family_spec(report_family_id)
		if _family_spec_active(report_family_spec) and _family_spec_has_reasoning_authority(report_family_spec):
			return report_family_id, report_family_spec
	return "", {}


def _subject_alias(family_spec: Dict[str, Any]) -> str:
	alias = _clean_text(
		family_spec.get("subject_alias_value")
		or family_spec.get("subject_alias")
		or family_spec.get("entity_dimension")
	)
	return alias.lower() if alias else "row"


def _ranked_rows(artifact_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	for section_key in ("ranked_rows", "parties", "customers", "suppliers", "items"):
		rows = sections.get(section_key)
		if isinstance(rows, list) and rows:
			return [dict(row) for row in rows if isinstance(row, dict)]
	return []


def _entity_label(row: Dict[str, Any]) -> str:
	return _clean_text(
		row.get("entity_name")
		or row.get("entity")
		or row.get("party")
		or row.get("customer")
		or row.get("supplier")
		or row.get("item_name")
		or row.get("item_code")
	)


def _row_rank(row: Dict[str, Any], fallback_index: int) -> int:
	for key in ("rank", "row_rank", "position"):
		try:
			value = int(row.get(key) or 0)
		except (TypeError, ValueError):
			value = 0
		if value > 0:
			return value
	return fallback_index + 1


def _ordinal_reference_index(message: str) -> int:
	normalized = _normalize_text(message)
	if not normalized:
		return -1
	ordinal_words = {
		"first": 1,
		"second": 2,
		"third": 3,
		"fourth": 4,
		"fifth": 5,
		"sixth": 6,
		"seventh": 7,
		"eighth": 8,
		"ninth": 9,
		"tenth": 10,
	}
	for word, value in ordinal_words.items():
		if re.search(rf"\b{re.escape(word)}\b", normalized):
			return value - 1
	for pattern in (
		r"\b(?:rank|row|number|no|no\.|#)\s*(\d{1,2})\b",
		r"\b(\d{1,2})(?:st|nd|rd|th)\b",
	):
		match = re.search(pattern, normalized)
		if not match:
			continue
		try:
			value = int(match.group(1))
		except (TypeError, ValueError):
			continue
		if value > 0:
			return value - 1
	return -1


def _alias_matches(normalized_message: str, alias: Any) -> bool:
	alias_text = _normalize_text(alias)
	if not normalized_message or not alias_text:
		return False
	return bool(re.search(rf"(^|[^a-z0-9]){re.escape(alias_text)}([^a-z0-9]|$)", normalized_message))


def _matched_blocked_variation(
	*,
	raw_message: str,
	family_spec: Dict[str, Any],
) -> str:
	normalized = _normalize_text(raw_message)
	if not normalized:
		return ""
	blocked_variations = {
		_clean_text(value)
		for value in (family_spec.get("blocked_variations") or [])
		if _clean_text(value)
	}
	aliases = family_spec.get("blocked_variation_aliases")
	if not isinstance(aliases, dict):
		return ""
	for variation, variation_aliases in aliases.items():
		variation_id = _clean_text(variation)
		if variation_id not in blocked_variations:
			continue
		for alias in variation_aliases or []:
			if _alias_matches(normalized, alias):
				return variation_id
	return ""


def _driver_policy(family_spec: Dict[str, Any]) -> Dict[str, Any]:
	policy = family_spec.get("driver_analysis_policy")
	return dict(policy) if isinstance(policy, dict) else {}


def _matched_driver_mode(
	*,
	raw_message: str,
	family_spec: Dict[str, Any],
) -> tuple[str, str]:
	normalized = _normalize_text(raw_message)
	if not normalized:
		return "", ""
	policy = _driver_policy(family_spec)
	if not policy:
		return "", ""
	blocked_aliases = policy.get("blocked_mode_aliases")
	if isinstance(blocked_aliases, dict):
		for mode_id, aliases in blocked_aliases.items():
			for alias in aliases or []:
				if _alias_matches(normalized, alias):
					return "blocked", _clean_text(mode_id)
	supported_aliases = policy.get("supported_mode_aliases")
	if isinstance(supported_aliases, dict):
		for mode_id, aliases in supported_aliases.items():
			for alias in aliases or []:
				if _alias_matches(normalized, alias):
					return "supported", _clean_text(mode_id)
	return "", ""


def _driver_mode_label(family_spec: Dict[str, Any], mode_id: str) -> str:
	labels = _driver_policy(family_spec).get("mode_labels")
	if isinstance(labels, dict):
		label = _clean_text(labels.get(mode_id))
		if label:
			return label
	return _clean_text(mode_id).replace("_", " ")


def _supported_driver_metric_keys(family_spec: Dict[str, Any], mode_id: str) -> List[str]:
	policy = _driver_policy(family_spec)
	mode_metrics = policy.get("supported_mode_metrics")
	if isinstance(mode_metrics, dict):
		values = mode_metrics.get(mode_id)
		if isinstance(values, list):
			return [_clean_text(value) for value in values if _clean_text(value)]
	values = policy.get("supported_driver_metrics")
	if isinstance(values, list):
		return [_clean_text(value) for value in values if _clean_text(value)]
	return []


def _authority_class_for_variation(variation_id: str) -> str:
	value = _clean_text(variation_id)
	if "driver" in value or "root_cause" in value or "cause" in value:
		return "driver_analysis"
	if "predict" in value or "probability" in value or "forecast" in value:
		return "prediction"
	if "recommendation" in value or "approval_decision" in value:
		return "recommendation"
	if "score" in value:
		return "score"
	if "severity" in value or "label" in value:
		return "classification"
	return "governed_analysis"


def _variation_label(family_spec: Dict[str, Any], variation_id: str) -> str:
	labels = family_spec.get("blocked_variation_labels")
	if isinstance(labels, dict):
		label = _clean_text(labels.get(variation_id))
		if label:
			return label
	return _clean_text(variation_id).replace("_", " ")


def _authority_policy_for_variation(family_spec: Dict[str, Any], variation_id: str) -> Dict[str, Any]:
	policies = family_spec.get("business_reasoning_authority_policies")
	if not isinstance(policies, dict):
		return {}
	policy = policies.get(_clean_text(variation_id))
	return dict(policy) if isinstance(policy, dict) else {}


def _policy_list_values(policy: Dict[str, Any], key: str) -> List[str]:
	values = policy.get(key)
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _policy_safe_next_action(
	*,
	policy: Dict[str, Any],
	default_next_action: str,
) -> str:
	return _clean_text(policy.get("safe_next_action")) or default_next_action


def _available_metric_keys_for_row(row: Dict[str, Any]) -> List[str]:
	if not row:
		return []
	keys: List[str] = []
	metric_values = row.get("metric_values") if isinstance(row.get("metric_values"), dict) else {}
	for key in metric_values.keys():
		clean = _clean_text(key)
		if clean:
			keys.append(clean)
	for key, value in row.items():
		clean = _clean_text(key)
		if not clean:
			continue
		if clean in {"rank", "entity", "entity_name", "entity_code", "customer", "customer_name", "supplier", "supplier_name", "item", "item_name", "item_code"}:
			continue
		if value in (None, ""):
			continue
		keys.append(clean)
	return list(dict.fromkeys(keys))


def _available_governed_artifact_ids(
	*,
	artifact_payload: Dict[str, Any],
) -> List[str]:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	dimensions = artifact.get("dimensions") if isinstance(artifact.get("dimensions"), dict) else {}
	filters = artifact.get("filters") if isinstance(artifact.get("filters"), dict) else {}
	artifact_family_id = _clean_text(artifact.get("family_id"))
	aging_type = _clean_text(dimensions.get("aging_type"))
	candidates: List[Any] = [
		artifact_family_id,
		artifact.get("source_composite_family_id"),
		filters.get("composite_family_id"),
		dimensions.get("source_composite_family_id"),
	]
	if artifact_family_id == "aging" and aging_type == "accounts_receivable":
		candidates.append("accounts_receivable_aging")
	if artifact_family_id == "aging" and aging_type == "accounts_payable":
		candidates.append("accounts_payable_aging")
	source_reports = artifact.get("source_reports") if isinstance(artifact.get("source_reports"), list) else []
	for report_name in source_reports:
		normalized_report_name = _normalize_text(report_name)
		if "accounts receivable" in normalized_report_name:
			candidates.append("accounts_receivable_aging")
		if "accounts payable" in normalized_report_name:
			candidates.append("accounts_payable_aging")
	for key in (
		"evidence_artifact_ids",
		"supporting_governed_artifact_ids",
		"supporting_governed_artifacts",
	):
		values = artifact.get(key)
		if isinstance(values, list):
			candidates.extend(values)
	values = dimensions.get("supporting_governed_artifacts")
	if isinstance(values, list):
		candidates.extend(values)
	out = [_clean_text(value) for value in candidates if _clean_text(value)]
	return list(dict.fromkeys(out))


def _authority_policy_gate_payload(
	*,
	variation_id: str,
	authority_policy: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	selected_row: Dict[str, Any],
	family_spec: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if not authority_policy:
		return {
			"gate_state": "not_configured",
			"variation_id": _clean_text(variation_id),
			"approval_state": "",
			"required_policy_state": "",
			"missing_evidence_metrics": [],
			"missing_governed_artifacts": [],
			"ready_to_recommend": False,
		}
	approval_state = _clean_text(authority_policy.get("approval_state"))
	required_policy_state = _clean_text(authority_policy.get("required_policy_state")) or "approved_active"
	required_metrics = _policy_list_values(authority_policy, "required_evidence_metrics")
	required_artifacts = _policy_list_values(authority_policy, "required_governed_artifacts")
	available_metrics = _available_policy_metric_keys_for_row(
		selected_row,
		required_metrics=required_metrics,
		family_spec=family_spec or {},
	)
	available_artifacts = _available_governed_artifact_ids(artifact_payload=artifact_payload)
	missing_metrics = [value for value in required_metrics if value not in set(available_metrics)]
	missing_artifacts = [value for value in required_artifacts if value not in set(available_artifacts)]
	if approval_state != required_policy_state:
		gate_state = approval_state or "blocked_missing_policy"
	elif missing_metrics or missing_artifacts:
		gate_state = "blocked_missing_evidence"
	else:
		gate_state = "ready"
	return {
		"gate_state": gate_state,
		"variation_id": _clean_text(variation_id),
		"policy_artifact_id": _clean_text(authority_policy.get("policy_artifact_id")),
		"policy_artifact_label": _clean_text(authority_policy.get("policy_artifact_label")),
		"approval_state": approval_state,
		"required_policy_state": required_policy_state,
		"recommendation_result_type": _clean_text(authority_policy.get("recommendation_result_type")),
		"required_evidence_metrics": required_metrics,
		"available_evidence_metrics": available_metrics,
		"missing_evidence_metrics": missing_metrics,
		"required_governed_artifacts": required_artifacts,
		"available_governed_artifacts": available_artifacts,
		"missing_governed_artifacts": missing_artifacts,
		"ready_to_recommend": gate_state == "ready",
	}


def _recommendation_output_constraints(authority_policy: Dict[str, Any]) -> Dict[str, Any]:
	result_type = _clean_text(authority_policy.get("recommendation_result_type"))
	return {
		"requires_ready_policy_gate": True,
		"requires_runtime_execution_enabled": True,
		"allowed_result_type": result_type,
		"must_cite_policy_artifact": True,
		"must_cite_governed_evidence": True,
		"must_not_include": [
			"predictive_default_probability",
			"hidden_weighted_risk_score",
			"credit_approval_decision",
			"unsupported_causal_claim",
			"unsupported_trend_claim",
		],
		"fallback_mode": "grounded_evidence_boundary",
	}


def _recommendation_runtime_execution_state(authority_policy: Dict[str, Any]) -> str:
	state = _clean_text(authority_policy.get("runtime_execution_state"))
	return state or "disabled_pending_policy_approval"


def _recommendation_allowed_execution_modes(authority_policy: Dict[str, Any]) -> List[str]:
	return _policy_list_values(authority_policy, "allowed_execution_modes")


def _recommendation_runtime_execution_enabled(authority_policy: Dict[str, Any]) -> bool:
	return _recommendation_runtime_execution_state(authority_policy) == "enabled_active"


def _recommendation_dry_run_allowed(authority_policy: Dict[str, Any]) -> bool:
	state = _recommendation_runtime_execution_state(authority_policy)
	modes = set(_recommendation_allowed_execution_modes(authority_policy))
	return state in {"dry_run_only", "enabled_active"} and "dry_run" in modes


def _yes_no(value: Any) -> str:
	return "Yes" if bool(value) else "No"


def _recommendation_execution_observability_rows(execution_contract: Dict[str, Any]) -> List[List[str]]:
	contract = execution_contract if isinstance(execution_contract, dict) else {}
	if not contract:
		return []
	rows = [
		["Execution State", _clean_text(contract.get("execution_state"))],
		["Policy Gate Ready", _yes_no(contract.get("policy_gate_ready"))],
		["Runtime Execution State", _clean_text(contract.get("runtime_execution_state"))],
		["Runtime Execution Enabled", _yes_no(contract.get("runtime_execution_enabled"))],
		["Dry Run Allowed", _yes_no(contract.get("dry_run_allowed"))],
		["Production Execution Allowed", _yes_no(contract.get("execution_allowed"))],
		["Safe Response Mode", _clean_text(contract.get("safe_response_mode"))],
		["Boundary Reason", _clean_text(contract.get("boundary_reason"))],
	]
	return [row for row in rows if row[1]]


def _recommendation_execution_state_from_gate(gate_payload: Dict[str, Any]) -> str:
	gate_state = _clean_text(gate_payload.get("gate_state"))
	if bool(gate_payload.get("ready_to_recommend")):
		return "ready"
	return gate_state or "blocked"


def _recommendation_execution_contract_from_policy_payload(policy_payload: Dict[str, Any]) -> Dict[str, Any]:
	payload = policy_payload if isinstance(policy_payload, dict) else {}
	if _clean_text(payload.get("requested_authority")) != "recommendation":
		return {}
	authority_policy = payload.get("authority_policy") if isinstance(payload.get("authority_policy"), dict) else {}
	gate = payload.get("authority_policy_gate") if isinstance(payload.get("authority_policy_gate"), dict) else {}
	if not authority_policy:
		return {}
	execution_state = _recommendation_execution_state_from_gate(gate)
	policy_gate_ready = execution_state == "ready" and bool(gate.get("ready_to_recommend"))
	runtime_execution_state = _recommendation_runtime_execution_state(authority_policy)
	allowed_execution_modes = _recommendation_allowed_execution_modes(authority_policy)
	runtime_execution_enabled = _recommendation_runtime_execution_enabled(authority_policy)
	dry_run_allowed = _recommendation_dry_run_allowed(authority_policy)
	execution_allowed = policy_gate_ready and runtime_execution_enabled
	return {
		"type": "qwen_business_recommendation_execution_contract",
		"contract_version": "1.0",
		"execution_state": execution_state,
		"policy_gate_ready": bool(policy_gate_ready),
		"runtime_execution_state": runtime_execution_state,
		"runtime_execution_enabled": bool(runtime_execution_enabled),
		"dry_run_allowed": bool(dry_run_allowed),
		"allowed_execution_modes": allowed_execution_modes,
		"execution_allowed": bool(execution_allowed),
		"source_family_id": _clean_text(payload.get("source_family_id")),
		"source_family_label": _clean_text(payload.get("source_family_label")),
		"recommendation_variation": _clean_text(payload.get("blocked_variation")),
		"recommendation_label": _clean_text(payload.get("blocked_variation_label")),
		"policy_artifact_id": _clean_text(authority_policy.get("policy_artifact_id")),
		"policy_artifact_label": _clean_text(authority_policy.get("policy_artifact_label")),
		"approval_state": _clean_text(authority_policy.get("approval_state")),
		"required_policy_state": _clean_text(authority_policy.get("required_policy_state")),
		"recommendation_result_type": _clean_text(authority_policy.get("recommendation_result_type")),
		"selected_row": dict(payload.get("selected_row") or {}),
		"metric_rows": [dict(item) for item in (payload.get("metric_rows") or []) if isinstance(item, dict)],
		"authority_policy_gate": dict(gate),
		"output_constraints": _recommendation_output_constraints(authority_policy),
		"safe_response_mode": "recommendation_execution" if execution_allowed else "grounded_evidence_boundary",
		"boundary_reason": (
			"The recommendation policy gate is ready for constrained execution."
			if execution_allowed
			else (
				"Recommendation execution is blocked because runtime recommendation execution is not enabled."
				if policy_gate_ready
				else "Recommendation execution is blocked until the policy approval and required ERP inputs are complete."
			)
		),
	}


def _selected_ranked_row(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	prefer_first_ranked_row: bool = False,
) -> Dict[str, Any]:
	rows = _ranked_rows(artifact_payload)
	if not rows:
		return {}
	ordinal_index = _ordinal_reference_index(raw_message)
	if ordinal_index >= 0:
		for index, row in enumerate(rows):
			if _row_rank(row, index) == ordinal_index + 1:
				return row
		if ordinal_index < len(rows):
			return rows[ordinal_index]
		return {}
	message_text = f" {_normalize_text(raw_message)} "
	named_matches = [
		row
		for row in rows
		if _entity_label(row) and f" {_normalize_text(_entity_label(row))} " in message_text
	]
	if len(named_matches) == 1:
		return named_matches[0]
	if prefer_first_ranked_row:
		return rows[0]
	if len(rows) == 1:
		return rows[0]
	return {}


def _metric_value(row: Dict[str, Any], metric_key: str, family_spec: Dict[str, Any] | None = None) -> tuple[Any, str]:
	metric_values = row.get("metric_values") if isinstance(row.get("metric_values"), dict) else {}
	value_payload = metric_values.get(metric_key) if isinstance(metric_values.get(metric_key), dict) else {}
	if value_payload:
		return value_payload.get("value"), _clean_text(value_payload.get("display_value"))
	if metric_key in row:
		return row.get(metric_key), ""
	family = family_spec if isinstance(family_spec, dict) else {}
	metric_map = family.get("metric_semantic_key_map") if isinstance(family.get("metric_semantic_key_map"), dict) else {}
	common_aliases = {
		"outstanding_amount": ["outstanding", "outstanding_total", "outstanding_amount"],
		"overdue_amount": ["overdue", "overdue_total", "overdue_amount", "past_due_amount"],
		"total_due": ["total_due", "due_amount"],
		"credit_utilization": ["credit_utilization", "credit_utilization_ratio", "credit_usage"],
	}
	alias_keys = list(metric_map.get(metric_key) or []) + common_aliases.get(metric_key, [])
	for alias_key in alias_keys:
		clean_key = _clean_text(alias_key)
		if clean_key and clean_key in row:
			return row.get(clean_key), ""
	if metric_key == "overdue_amount":
		bucket_total = sum(
			_numeric(row.get(key))
			for key in ("bucket_31_60", "bucket_61_90", "bucket_91_120", "bucket_121_above")
		)
		if bucket_total:
			return bucket_total, ""
	if metric_key == "overdue_ratio":
		overdue_value, _display = _metric_value(row, "overdue_amount", family_spec=family)
		outstanding_value, _display = _metric_value(row, "outstanding_amount", family_spec=family)
		outstanding = _numeric(outstanding_value)
		if outstanding > 0:
			return _numeric(overdue_value) / outstanding, ""
	return "", ""


def _row_has_aging_bucket_evidence(row: Dict[str, Any]) -> bool:
	return any(
		key in row and row.get(key) not in (None, "")
		for key in ("bucket_31_60", "bucket_61_90", "bucket_91_120", "bucket_121_above")
	)


def _available_policy_metric_keys_for_row(
	row: Dict[str, Any],
	*,
	required_metrics: List[str],
	family_spec: Dict[str, Any],
) -> List[str]:
	available = _available_metric_keys_for_row(row)
	available_set = set(available)
	for metric_key in required_metrics:
		clean_metric = _clean_text(metric_key)
		if not clean_metric or clean_metric in available_set:
			continue
		if clean_metric == "aging_buckets" and _row_has_aging_bucket_evidence(row):
			available.append(clean_metric)
			available_set.add(clean_metric)
			continue
		value, display_value = _metric_value(row, clean_metric, family_spec=family_spec)
		if value not in (None, "") or bool(display_value):
			available.append(clean_metric)
			available_set.add(clean_metric)
	return list(dict.fromkeys(available))


def _metric_rows(
	*,
	row: Dict[str, Any],
	family_spec: Dict[str, Any],
	artifact_payload: Dict[str, Any],
) -> List[Dict[str, str]]:
	if not row:
		return []
	dimensions = artifact_payload.get("dimensions") if isinstance(artifact_payload.get("dimensions"), dict) else {}
	primary_metric = _clean_text(
		dimensions.get("source_composite_primary_metric_id")
		or family_spec.get("default_primary_metric")
	)
	secondary_metrics = [
		_clean_text(value)
		for value in (
			dimensions.get("source_composite_secondary_metric_ids")
			or family_spec.get("default_secondary_metrics")
			or family_spec.get("allowed_secondary_metrics")
			or []
		)
		if _clean_text(value)
	]
	metric_keys = list(dict.fromkeys([primary_metric] + secondary_metrics))
	out: List[Dict[str, str]] = []
	for metric_key in metric_keys:
		if not metric_key:
			continue
		value, display_value = _metric_value(row, metric_key, family_spec=family_spec)
		if value in (None, "") and not display_value:
			continue
		out.append(
			{
				"metric_key": metric_key,
				"label": get_metric_label(metric_key) or metric_key.replace("_", " ").title(),
				"value": _format_metric_value(metric_key, value, display_value),
			}
		)
	return out


@dataclass(frozen=True)
class BusinessReasoningAuthorityDecision:
	policy_state: str
	source_family_id: str = ""
	source_family_label: str = ""
	requested_authority: str = ""
	blocked_variation: str = ""
	blocked_variation_label: str = ""
	allowed_to_answer: bool = True
	boundary_reason: str = ""
	safe_response_mode: str = "grounded_evidence_only"
	safe_next_action: str = ""
	selected_row: Dict[str, Any] = field(default_factory=dict)
	metric_rows: List[Dict[str, str]] = field(default_factory=list)
	authority_policy: Dict[str, Any] = field(default_factory=dict)
	authority_policy_gate: Dict[str, Any] = field(default_factory=dict)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_business_reasoning_authority_policy",
			"contract_version": "1.0",
			"policy_state": self.policy_state,
			"source_family_id": self.source_family_id,
			"source_family_label": self.source_family_label,
			"requested_authority": self.requested_authority,
			"blocked_variation": self.blocked_variation,
			"blocked_variation_label": self.blocked_variation_label,
			"allowed_to_answer": bool(self.allowed_to_answer),
			"boundary_reason": self.boundary_reason,
			"safe_response_mode": self.safe_response_mode,
			"safe_next_action": self.safe_next_action,
			"selected_row": dict(self.selected_row or {}),
			"metric_rows": [dict(item) for item in (self.metric_rows or []) if isinstance(item, dict)],
			"authority_policy": dict(self.authority_policy or {}),
			"authority_policy_gate": dict(self.authority_policy_gate or {}),
		}


def assess_business_reasoning_authority(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> BusinessReasoningAuthorityDecision:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id, family_spec = _authority_family_spec_for_artifact(artifact)
	if not family_id:
		return BusinessReasoningAuthorityDecision(policy_state="not_applicable")
	if not _family_spec_active(family_spec):
		return BusinessReasoningAuthorityDecision(policy_state="not_applicable", source_family_id=family_id)
	blocked_variation = _matched_blocked_variation(raw_message=raw_message, family_spec=family_spec)
	family_label = _source_composite_family_label(family_spec, artifact)
	if not blocked_variation:
		driver_state, driver_mode = _matched_driver_mode(raw_message=raw_message, family_spec=family_spec)
		if driver_state == "blocked":
			selected_row = _selected_ranked_row(
				raw_message=raw_message,
				artifact_payload=artifact,
				prefer_first_ranked_row=False,
			)
			return BusinessReasoningAuthorityDecision(
				policy_state="blocked",
				source_family_id=family_id,
				source_family_label=family_label,
				requested_authority="driver_analysis",
				blocked_variation=driver_mode,
				blocked_variation_label=_driver_mode_label(family_spec, driver_mode),
				allowed_to_answer=False,
				boundary_reason=f"The {family_label} metadata blocks {driver_mode}.",
				safe_response_mode="grounded_evidence_only",
				safe_next_action=(
					"Ask for a trend, payment-behavior, or transaction-history analysis view "
					"before requesting causal or change-driver analysis."
				),
				selected_row=selected_row,
				metric_rows=_metric_rows(row=selected_row, family_spec=family_spec, artifact_payload=artifact),
			)
		return BusinessReasoningAuthorityDecision(
			policy_state="allowed",
			source_family_id=family_id,
			source_family_label=family_label,
			allowed_to_answer=True,
		)
	authority_policy = _authority_policy_for_variation(family_spec, blocked_variation)
	prefer_first_ranked_row = _authority_class_for_variation(blocked_variation) in {"prediction", "recommendation"}
	selected_row = _selected_ranked_row(
		raw_message=raw_message,
		artifact_payload=artifact,
		prefer_first_ranked_row=prefer_first_ranked_row,
	)
	authority_policy_gate = _authority_policy_gate_payload(
		variation_id=blocked_variation,
		authority_policy=authority_policy,
		artifact_payload=artifact,
		selected_row=selected_row,
		family_spec=family_spec,
	)
	default_next_action = "Use the current ranking as supporting evidence, or define an approved company policy before asking for a decision or recommendation."
	return BusinessReasoningAuthorityDecision(
		policy_state="blocked",
		source_family_id=family_id,
		source_family_label=family_label,
		requested_authority=_authority_class_for_variation(blocked_variation),
		blocked_variation=blocked_variation,
		blocked_variation_label=_variation_label(family_spec, blocked_variation),
		allowed_to_answer=False,
		boundary_reason=f"The {family_label} metadata blocks {blocked_variation}.",
		safe_response_mode="grounded_evidence_only",
		safe_next_action=_policy_safe_next_action(
			policy=authority_policy,
			default_next_action=default_next_action,
		),
		selected_row=selected_row,
		metric_rows=_metric_rows(row=selected_row, family_spec=family_spec, artifact_payload=artifact),
		authority_policy=authority_policy,
		authority_policy_gate=authority_policy_gate,
	)


def build_business_reasoning_authority_policy_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	decision = assess_business_reasoning_authority(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn or {},
	)
	payload = decision.to_payload()
	if payload.get("policy_state") == "not_applicable":
		return {}
	recommendation_execution_contract = _recommendation_execution_contract_from_policy_payload(payload)
	if recommendation_execution_contract:
		payload["recommendation_execution_contract"] = recommendation_execution_contract
	return payload


def build_business_recommendation_execution_contract(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	payload = build_business_reasoning_authority_policy_payload(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn or {},
	)
	return dict(payload.get("recommendation_execution_contract") or {})


def render_business_reasoning_policy_boundary_answer(policy_payload: Dict[str, Any]) -> str:
	policy = policy_payload if isinstance(policy_payload, dict) else {}
	if _clean_text(policy.get("policy_state")) != "blocked":
		return ""
	family_label = _clean_text(policy.get("source_family_label")) or "the answer above"
	variation_label = _clean_text(policy.get("blocked_variation_label")) or "that decision"
	selected_row = policy.get("selected_row") if isinstance(policy.get("selected_row"), dict) else {}
	metric_rows = [dict(item) for item in (policy.get("metric_rows") or []) if isinstance(item, dict)]
	authority_policy = policy.get("authority_policy") if isinstance(policy.get("authority_policy"), dict) else {}
	authority_policy_gate = policy.get("authority_policy_gate") if isinstance(policy.get("authority_policy_gate"), dict) else {}
	recommendation_execution_contract = (
		policy.get("recommendation_execution_contract")
		if isinstance(policy.get("recommendation_execution_contract"), dict)
		else {}
	)
	lines = [
		f"The current {family_label} result can support ranked facts, but it does not authorize a {variation_label}.",
	]
	entity_label = _entity_label(selected_row)
	if selected_row and entity_label:
		rank = _row_rank(selected_row, 0)
		lines.extend(
			[
				"",
				f"Current ERP facts from the current ranking:",
				f"- Rank {rank}: {entity_label}",
			]
		)
		for item in metric_rows[:5]:
			label = _clean_text(item.get("label"))
			value = _clean_text(item.get("value"))
			if label and value:
				lines.append(f"- {label}: {value}")
	policy_label = _clean_text(authority_policy.get("policy_artifact_label"))
	gate_state = _clean_text(authority_policy_gate.get("gate_state")) or _clean_text(authority_policy.get("approval_state")) or "not_configured"
	policy_state = _clean_text(authority_policy.get("approval_state")) or "not_configured"
	if policy_label:
		lines.extend(
			[
				"",
				"Required policy before this can become a governed decision:",
				f"- Policy: {policy_label}",
				f"- Approval state: {policy_state}",
				f"- Gate state: {gate_state}",
			]
		)
		required_metrics = _policy_list_values(authority_policy, "required_evidence_metrics")
		required_artifacts = _policy_list_values(authority_policy, "required_governed_artifacts")
		missing_metrics = _policy_list_values(authority_policy_gate, "missing_evidence_metrics")
		missing_artifacts = _policy_list_values(authority_policy_gate, "missing_governed_artifacts")
		if required_metrics:
			lines.append(f"- Required evidence metrics: {', '.join(required_metrics)}")
		if required_artifacts:
			lines.append(f"- Required supporting views: {', '.join(required_artifacts)}")
		if missing_metrics:
			lines.append(f"- Missing evidence metrics: {', '.join(missing_metrics)}")
		if missing_artifacts:
			lines.append(f"- Missing supporting views: {', '.join(missing_artifacts)}")
	execution_rows = _recommendation_execution_observability_rows(recommendation_execution_contract)
	if execution_rows:
		lines.extend(
			[
				"",
				"Recommendation execution gate:",
			]
		)
		for label, value in execution_rows:
			lines.append(f"- {label}: {value}")
	lines.extend(
		[
			"",
			"This is a data-safety limit, not a recommendation, prediction, score, or approval decision.",
			_clean_text(policy.get("safe_next_action")) or "Ask for a summary view or approved company policy before requesting a decision.",
		]
	)
	return "\n".join(lines).strip()


def composite_blocked_reasoning_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> str:
	payload = build_business_reasoning_authority_policy_payload(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn or {},
	)
	return render_business_reasoning_policy_boundary_answer(payload)


def _metric_rows_for_keys(
	*,
	row: Dict[str, Any],
	family_spec: Dict[str, Any],
	artifact_payload: Dict[str, Any],
	metric_keys: List[str],
) -> List[Dict[str, str]]:
	if not metric_keys:
		return _metric_rows(row=row, family_spec=family_spec, artifact_payload=artifact_payload)
	all_rows = _metric_rows(row=row, family_spec=family_spec, artifact_payload=artifact_payload)
	allowed = {_clean_text(value) for value in metric_keys if _clean_text(value)}
	return [dict(item) for item in all_rows if _clean_text(item.get("metric_key")) in allowed]


def composite_driver_analysis_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> str:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _source_composite_family_id(artifact)
	if not family_id:
		return ""
	family_spec = get_composite_family_spec(family_id)
	if _clean_text(family_spec.get("activation_state")) != "active":
		return ""
	driver_state, driver_mode = _matched_driver_mode(raw_message=raw_message, family_spec=family_spec)
	if driver_state != "supported":
		return ""
	row = _selected_ranked_row(raw_message=raw_message, artifact_payload=artifact)
	if not row:
		return ""
	family_label = _source_composite_family_label(family_spec, artifact)
	entity_label = _entity_label(row) or "the selected row"
	rank = _row_rank(row, 0)
	as_of_date = _clean_text((artifact.get("period") or {}).get("as_of_date") or (artifact.get("filters") or {}).get("as_of_date"))
	date_phrase = f" as of {as_of_date}" if as_of_date else ""
	metric_rows = _metric_rows_for_keys(
		row=row,
		family_spec=family_spec,
		artifact_payload=artifact,
		metric_keys=_supported_driver_metric_keys(family_spec, driver_mode),
	)
	if not metric_rows:
		return (
			f"I can identify {entity_label} in the current {family_label} result, but this result does not carry "
			"the metric components needed for driver analysis. Please ask for a broader analysis view."
		)
	lines = [
		f"Within the current {family_label} result{date_phrase}, the explainable drivers for {entity_label} are the ranking and supporting metrics already carried by this result.",
		"",
		f"Current ERP driver facts:",
		f"- Rank {rank}: {entity_label}",
	]
	for item in metric_rows[:6]:
		label = _clean_text(item.get("label"))
		value = _clean_text(item.get("value"))
		if label and value:
			lines.append(f"- {label}: {value}")
	lines.extend(
		[
			"",
			"This is current-result metric-driver analysis only. It is not causal, trend, payment-behavior, prediction, or collection-recommendation analysis.",
		]
	)
	return "\n".join(lines).strip()


def composite_blocked_reasoning_boundary_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	policy = build_business_reasoning_authority_policy_payload(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn or {},
	)
	answer_text = render_business_reasoning_policy_boundary_answer(policy)
	if not answer_text:
		return {}
	metric_rows = [dict(item) for item in (policy.get("metric_rows") or []) if isinstance(item, dict)]
	authority_policy = policy.get("authority_policy") if isinstance(policy.get("authority_policy"), dict) else {}
	authority_policy_gate = policy.get("authority_policy_gate") if isinstance(policy.get("authority_policy_gate"), dict) else {}
	recommendation_execution_contract = (
		policy.get("recommendation_execution_contract")
		if isinstance(policy.get("recommendation_execution_contract"), dict)
		else {}
	)
	blocks: List[Dict[str, Any]] = []
	if metric_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Current ERP Facts",
				"columns": ["Metric", "Value"],
				"rows": [
					[_clean_text(item.get("label")), _clean_text(item.get("value"))]
					for item in metric_rows
					if _clean_text(item.get("label")) and _clean_text(item.get("value"))
				],
			}
		)
	if authority_policy:
		policy_rows = [
			["Policy", _clean_text(authority_policy.get("policy_artifact_label")) or _clean_text(authority_policy.get("policy_artifact_id"))],
			["Approval State", _clean_text(authority_policy.get("approval_state")) or "not_configured"],
			["Required Policy State", _clean_text(authority_policy.get("required_policy_state"))],
			["Gate State", _clean_text(authority_policy_gate.get("gate_state"))],
			["Recommendation Result Type", _clean_text(authority_policy.get("recommendation_result_type"))],
			["Required Evidence Metrics", ", ".join(_policy_list_values(authority_policy, "required_evidence_metrics"))],
			["Required Supporting Views", ", ".join(_policy_list_values(authority_policy, "required_governed_artifacts"))],
			["Missing Evidence Metrics", ", ".join(_policy_list_values(authority_policy_gate, "missing_evidence_metrics"))],
			["Missing Supporting Views", ", ".join(_policy_list_values(authority_policy_gate, "missing_governed_artifacts"))],
		]
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Required Policy",
				"columns": ["Policy Field", "Value"],
				"rows": [row for row in policy_rows if row[1]],
			}
		)
	execution_rows = _recommendation_execution_observability_rows(recommendation_execution_contract)
	if execution_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Recommendation Execution Gate",
				"columns": ["Gate Field", "Value"],
				"rows": execution_rows,
			}
		)
	blocks.append(
			{
				"block_type": "bullet_list",
				"title": "Decision Limit",
				"items": [
					f"Blocked variation: {_clean_text(policy.get('blocked_variation_label')) or _clean_text(policy.get('blocked_variation'))}",
					"Uses only the facts shown above.",
					"Does not create recommendation, prediction, score, or approval decisions.",
				],
		}
	)
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	return {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"request_id": _clean_text(artifact.get("request_id")),
		"family_id": _clean_text(artifact.get("family_id")),
		"renderer_id": "business_reasoning_authority_boundary",
		"rendering_policy": "deterministic",
		"title": "Decision Limit",
		"answer_text": answer_text,
		"source_reports": [
			_clean_text(value)
			for value in (artifact.get("source_reports") or [])
			if _clean_text(value)
		],
		"blocks": blocks,
		"warnings": [
			_clean_text(value)
			for value in (artifact.get("warnings") or [])
			if _clean_text(value)
		],
	}


def composite_driver_analysis_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	answer_text = composite_driver_analysis_answer(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn or {},
	)
	if not answer_text:
		return {}
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	family_id = _source_composite_family_id(artifact)
	family_spec = get_composite_family_spec(family_id)
	driver_state, driver_mode = _matched_driver_mode(raw_message=raw_message, family_spec=family_spec)
	row = _selected_ranked_row(raw_message=raw_message, artifact_payload=artifact)
	metric_rows = _metric_rows_for_keys(
		row=row,
		family_spec=family_spec,
		artifact_payload=artifact,
		metric_keys=_supported_driver_metric_keys(family_spec, driver_mode) if driver_state == "supported" else [],
	)
	blocks: List[Dict[str, Any]] = []
	if metric_rows:
		blocks.append(
			{
				"block_type": "data_table",
				"title": "Driver Evidence",
				"columns": ["Metric", "Value"],
				"rows": [
					[_clean_text(item.get("label")), _clean_text(item.get("value"))]
					for item in metric_rows
					if _clean_text(item.get("label")) and _clean_text(item.get("value"))
				],
			}
		)
	blocks.append(
		{
			"block_type": "bullet_list",
			"title": "Decision Limit",
			"items": [
				"Current-result metric-driver analysis only.",
				"Does not infer causal, trend, payment-behavior, prediction, or recommendation drivers.",
			],
		}
	)
	return {
		"type": "qwen_rendered_family_response_contract",
		"contract_version": "1.0",
		"request_id": _clean_text(artifact.get("request_id")),
		"family_id": _clean_text(artifact.get("family_id")),
		"renderer_id": "business_reasoning_driver_analysis",
		"rendering_policy": "deterministic",
		"title": "Driver Evidence",
		"answer_text": answer_text,
		"source_reports": [
			_clean_text(value)
			for value in (artifact.get("source_reports") or [])
			if _clean_text(value)
		],
		"blocks": blocks,
		"warnings": [
			_clean_text(value)
			for value in (artifact.get("warnings") or [])
			if _clean_text(value)
		],
	}
