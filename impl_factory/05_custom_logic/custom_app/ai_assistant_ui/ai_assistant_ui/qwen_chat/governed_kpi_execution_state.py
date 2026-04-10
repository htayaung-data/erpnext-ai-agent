from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.business_definition_state import (
	BusinessDefinitionStateContract,
	GovernedFormulaStateContract,
)
from ai_assistant_ui.qwen_chat.governed_kpi_execution_registry import (
	validate_governed_kpi_execution_registry,
)
from ai_assistant_ui.qwen_chat.metadata import (
	list_governed_kpi_execution_specs,
)


ALLOWED_EXECUTION_RESOLUTION_STATES = {
	"active_value",
	"blocked_missing_policy",
	"blocked_missing_data",
	"clarify_scope",
	"clarify_basis",
	"unsupported_execution_shape",
}


def _as_str_list(value: Any) -> List[str]:
	if not isinstance(value, list):
		return []
	items: List[str] = []
	for item in value:
		text = str(item or "").strip()
		if text:
			items.append(text)
	return items


def _as_dict_list(value: Any) -> List[Dict[str, Any]]:
	if not isinstance(value, list):
		return []
	return [dict(item) for item in value if isinstance(item, dict)]


def _company_scope_matches(values: Any, company_name: str) -> bool:
	scope_values = [str(item or "").strip().lower() for item in (values or []) if str(item or "").strip()]
	if not scope_values:
		return True
	normalized_company = str(company_name or "").strip().lower()
	return not normalized_company or "global" in scope_values or normalized_company in scope_values


def _coerce_number(value: Any) -> float | None:
	if value is None or value == "":
		return None
	try:
		return float(value)
	except Exception:
		return None


def _blocked_execution_state(activation_state: str) -> str:
	state = str(activation_state or "").strip()
	if state == "blocked_missing_policy":
		return "blocked_missing_policy"
	if state == "blocked_missing_data":
		return "blocked_missing_data"
	return "clarify_basis"


def _has_period_scope(requested_scope: Dict[str, Any]) -> bool:
	if requested_scope.get("has_period_scope") is True:
		return True
	period_start = str(requested_scope.get("period_start") or "").strip()
	period_end = str(requested_scope.get("period_end") or "").strip()
	return bool(period_start and period_end)


def _has_as_of_scope(requested_scope: Dict[str, Any]) -> bool:
	if requested_scope.get("has_as_of_date") is True:
		return True
	return bool(str(requested_scope.get("as_of_date") or "").strip())


def _has_customer_scope(requested_scope: Dict[str, Any]) -> bool:
	if requested_scope.get("has_customer_scope") is True:
		return True
	for key in ("customer", "customer_name", "entity_name"):
		if str(requested_scope.get(key) or "").strip():
			return True
	return False


def _execution_candidate_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"execution_id": str(entry.get("execution_id") or "").strip(),
		"definition_id": str(entry.get("definition_id") or "").strip(),
		"formula_id": str(entry.get("formula_id") or "").strip(),
		"label": str(entry.get("label") or "").strip(),
		"execution_shape": str(entry.get("execution_shape") or "").strip(),
		"scope_type": str(entry.get("scope_type") or "").strip(),
		"time_scope_type": str(entry.get("time_scope_type") or "").strip(),
		"activation_state": str(entry.get("activation_state") or "").strip(),
		"blocked_reason": str(entry.get("blocked_reason") or "").strip(),
	}


@dataclass(frozen=True)
class GovernedKpiExecutionStateContract:
	requested_definition_id: str
	requested_formula_id: str
	requested_execution_shape: str
	requested_company_name: str
	requested_scope: Dict[str, Any]
	resolution_state: str
	match_count: int
	matched_execution_ids: List[str] = field(default_factory=list)
	execution_id: str = ""
	label: str = ""
	execution_shape: str = ""
	scope_type: str = ""
	time_scope_type: str = ""
	source_mode: str = ""
	source_capabilities: List[str] = field(default_factory=list)
	source_reports: List[str] = field(default_factory=list)
	supported_filters: List[str] = field(default_factory=list)
	required_dimensions: List[str] = field(default_factory=list)
	value_unit_type: str = ""
	value_metric_mapping: Dict[str, Any] = field(default_factory=dict)
	activation_state: str = ""
	blocked_reason: str = ""
	reason: str = ""
	candidate_executions: List[Dict[str, Any]] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_governed_kpi_execution_state_contract",
			"contract_version": "1.0",
			"requested_definition_id": self.requested_definition_id,
			"requested_formula_id": self.requested_formula_id,
			"requested_execution_shape": self.requested_execution_shape,
			"requested_company_name": self.requested_company_name,
			"requested_scope": dict(self.requested_scope),
			"resolution_state": self.resolution_state,
			"match_count": int(max(0, self.match_count)),
			"matched_execution_ids": list(self.matched_execution_ids),
			"execution_id": self.execution_id,
			"label": self.label,
			"execution_shape": self.execution_shape,
			"scope_type": self.scope_type,
			"time_scope_type": self.time_scope_type,
			"source_mode": self.source_mode,
			"source_capabilities": list(self.source_capabilities),
			"source_reports": list(self.source_reports),
			"supported_filters": list(self.supported_filters),
			"required_dimensions": list(self.required_dimensions),
			"value_unit_type": self.value_unit_type,
			"value_metric_mapping": dict(self.value_metric_mapping),
			"activation_state": self.activation_state,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
			"candidate_executions": [dict(item) for item in self.candidate_executions if isinstance(item, dict)],
		}


@dataclass(frozen=True)
class GovernedKpiValueArtifactContract:
	artifact_type: str
	definition_id: str
	formula_id: str
	execution_id: str
	label: str
	execution_shape: str
	entity_grain: str
	scope: Dict[str, Any]
	as_of_date: str = ""
	period_start: str = ""
	period_end: str = ""
	value: float | None = None
	display_value: str = ""
	unit_type: str = ""
	numerator_label: str = ""
	numerator_value: float | None = None
	denominator_label: str = ""
	denominator_value: float | None = None
	source_evidence: List[Dict[str, Any]] = field(default_factory=list)
	threshold_state: Dict[str, Any] = field(default_factory=dict)
	status: str = "active_value"
	blocked_reason: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": self.artifact_type,
			"contract_version": "1.0",
			"definition_id": self.definition_id,
			"formula_id": self.formula_id,
			"execution_id": self.execution_id,
			"label": self.label,
			"execution_shape": self.execution_shape,
			"entity_grain": self.entity_grain,
			"scope": dict(self.scope),
			"as_of_date": self.as_of_date,
			"period_start": self.period_start,
			"period_end": self.period_end,
			"value": self.value,
			"display_value": self.display_value,
			"unit_type": self.unit_type,
			"numerator_label": self.numerator_label,
			"numerator_value": self.numerator_value,
			"denominator_label": self.denominator_label,
			"denominator_value": self.denominator_value,
			"source_evidence": [dict(item) for item in self.source_evidence if isinstance(item, dict)],
			"threshold_state": dict(self.threshold_state),
			"status": self.status,
			"blocked_reason": self.blocked_reason,
		}


@dataclass(frozen=True)
class GovernedKpiRankingArtifactContract:
	artifact_type: str
	definition_id: str
	formula_id: str
	execution_id: str
	label: str
	execution_shape: str
	entity_grain: str
	scope: Dict[str, Any]
	as_of_date: str = ""
	unit_type: str = ""
	ranking_mode: str = ""
	sort_direction: str = ""
	applied_limit: int = 0
	threshold_state: Dict[str, Any] = field(default_factory=dict)
	rows: List[Dict[str, Any]] = field(default_factory=list)
	source_evidence: List[Dict[str, Any]] = field(default_factory=list)
	status: str = "active_value"
	blocked_reason: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": self.artifact_type,
			"contract_version": "1.0",
			"definition_id": self.definition_id,
			"formula_id": self.formula_id,
			"execution_id": self.execution_id,
			"label": self.label,
			"execution_shape": self.execution_shape,
			"entity_grain": self.entity_grain,
			"scope": dict(self.scope),
			"as_of_date": self.as_of_date,
			"unit_type": self.unit_type,
			"ranking_mode": self.ranking_mode,
			"sort_direction": self.sort_direction,
			"applied_limit": int(max(0, self.applied_limit)),
			"threshold_state": dict(self.threshold_state),
			"rows": [dict(item) for item in self.rows if isinstance(item, dict)],
			"source_evidence": [dict(item) for item in self.source_evidence if isinstance(item, dict)],
			"status": self.status,
			"blocked_reason": self.blocked_reason,
		}


def build_governed_kpi_execution_state_contract(
	*,
	requested_definition_id: str = "",
	requested_formula_id: str = "",
	requested_execution_shape: str = "",
	requested_company_name: str = "",
	requested_scope: Dict[str, Any] | None = None,
	resolution_state: str = "unsupported_execution_shape",
	match_count: int = 0,
	matched_execution_ids: List[str] | None = None,
	execution_id: str = "",
	label: str = "",
	execution_shape: str = "",
	scope_type: str = "",
	time_scope_type: str = "",
	source_mode: str = "",
	source_capabilities: List[str] | None = None,
	source_reports: List[str] | None = None,
	supported_filters: List[str] | None = None,
	required_dimensions: List[str] | None = None,
	value_unit_type: str = "",
	value_metric_mapping: Dict[str, Any] | None = None,
	activation_state: str = "",
	blocked_reason: str = "",
	reason: str = "",
	candidate_executions: List[Dict[str, Any]] | None = None,
) -> GovernedKpiExecutionStateContract:
	state = str(resolution_state or "unsupported_execution_shape").strip().lower() or "unsupported_execution_shape"
	if state not in ALLOWED_EXECUTION_RESOLUTION_STATES:
		state = "unsupported_execution_shape"
	return GovernedKpiExecutionStateContract(
		requested_definition_id=str(requested_definition_id or "").strip(),
		requested_formula_id=str(requested_formula_id or "").strip(),
		requested_execution_shape=str(requested_execution_shape or "").strip(),
		requested_company_name=str(requested_company_name or "").strip(),
		requested_scope=dict(requested_scope or {}),
		resolution_state=state,
		match_count=int(max(0, match_count)),
		matched_execution_ids=[
			str(value or "").strip()
			for value in (matched_execution_ids or [])
			if str(value or "").strip()
		],
		execution_id=str(execution_id or "").strip(),
		label=str(label or "").strip(),
		execution_shape=str(execution_shape or "").strip(),
		scope_type=str(scope_type or "").strip(),
		time_scope_type=str(time_scope_type or "").strip(),
		source_mode=str(source_mode or "").strip(),
		source_capabilities=_as_str_list(source_capabilities or []),
		source_reports=_as_str_list(source_reports or []),
		supported_filters=_as_str_list(supported_filters or []),
		required_dimensions=_as_str_list(required_dimensions or []),
		value_unit_type=str(value_unit_type or "").strip(),
		value_metric_mapping=dict(value_metric_mapping or {}),
		activation_state=str(activation_state or "").strip(),
		blocked_reason=str(blocked_reason or "").strip(),
		reason=str(reason or "").strip(),
		candidate_executions=[dict(item) for item in (candidate_executions or []) if isinstance(item, dict)],
	)


def build_governed_kpi_value_artifact_contract(
	*,
	execution_state: GovernedKpiExecutionStateContract,
	entity_grain: str,
	scope: Dict[str, Any] | None = None,
	as_of_date: str = "",
	period_start: str = "",
	period_end: str = "",
	value: Any = None,
	display_value: str = "",
	unit_type: str = "",
	numerator_label: str = "",
	numerator_value: Any = None,
	denominator_label: str = "",
	denominator_value: Any = None,
	source_evidence: List[Dict[str, Any]] | None = None,
	threshold_state: Dict[str, Any] | None = None,
	status: str = "",
	blocked_reason: str = "",
) -> GovernedKpiValueArtifactContract:
	resolution_state = str(execution_state.resolution_state or "").strip()
	normalized_status = str(status or resolution_state or "unsupported_execution_shape").strip()
	if normalized_status not in ALLOWED_EXECUTION_RESOLUTION_STATES:
		normalized_status = "unsupported_execution_shape"
	numeric_value = _coerce_number(value)
	numeric_numerator = _coerce_number(numerator_value)
	numeric_denominator = _coerce_number(denominator_value)
	display = str(display_value or "").strip()
	if not display and numeric_value is not None:
		display = str(numeric_value)
	return GovernedKpiValueArtifactContract(
		artifact_type="qwen_governed_kpi_value_artifact_contract",
		definition_id=str(execution_state.requested_definition_id or "").strip(),
		formula_id=str(execution_state.requested_formula_id or "").strip(),
		execution_id=str(execution_state.execution_id or "").strip(),
		label=str(execution_state.label or "").strip(),
		execution_shape=str(execution_state.execution_shape or execution_state.requested_execution_shape or "").strip(),
		entity_grain=str(entity_grain or "").strip(),
		scope=dict(scope or {}),
		as_of_date=str(as_of_date or "").strip(),
		period_start=str(period_start or "").strip(),
		period_end=str(period_end or "").strip(),
		value=numeric_value,
		display_value=display,
		unit_type=str(unit_type or execution_state.value_unit_type or "").strip(),
		numerator_label=str(numerator_label or "").strip(),
		numerator_value=numeric_numerator,
		denominator_label=str(denominator_label or "").strip(),
		denominator_value=numeric_denominator,
		source_evidence=_as_dict_list(source_evidence or []),
		threshold_state=dict(threshold_state or {}),
		status=normalized_status,
		blocked_reason=str(blocked_reason or execution_state.blocked_reason or "").strip(),
	)


def build_governed_kpi_ranking_artifact_contract(
	*,
	execution_state: GovernedKpiExecutionStateContract,
	entity_grain: str,
	scope: Dict[str, Any] | None = None,
	as_of_date: str = "",
	unit_type: str = "",
	ranking_mode: str = "",
	sort_direction: str = "",
	applied_limit: int = 0,
	threshold_state: Dict[str, Any] | None = None,
	rows: List[Dict[str, Any]] | None = None,
	source_evidence: List[Dict[str, Any]] | None = None,
	status: str = "",
	blocked_reason: str = "",
) -> GovernedKpiRankingArtifactContract:
	resolution_state = str(execution_state.resolution_state or "").strip()
	normalized_status = str(status or resolution_state or "unsupported_execution_shape").strip()
	if normalized_status not in ALLOWED_EXECUTION_RESOLUTION_STATES:
		normalized_status = "unsupported_execution_shape"
	return GovernedKpiRankingArtifactContract(
		artifact_type="qwen_governed_kpi_ranking_artifact_contract",
		definition_id=str(execution_state.requested_definition_id or "").strip(),
		formula_id=str(execution_state.requested_formula_id or "").strip(),
		execution_id=str(execution_state.execution_id or "").strip(),
		label=str(execution_state.label or "").strip(),
		execution_shape=str(execution_state.execution_shape or execution_state.requested_execution_shape or "").strip(),
		entity_grain=str(entity_grain or "").strip(),
		scope=dict(scope or {}),
		as_of_date=str(as_of_date or "").strip(),
		unit_type=str(unit_type or execution_state.value_unit_type or "").strip(),
		ranking_mode=str(ranking_mode or "").strip(),
		sort_direction=str(sort_direction or "").strip(),
		applied_limit=int(max(0, applied_limit or 0)),
		threshold_state=dict(threshold_state or {}),
		rows=_as_dict_list(rows or []),
		source_evidence=_as_dict_list(source_evidence or []),
		status=normalized_status,
		blocked_reason=str(blocked_reason or execution_state.blocked_reason or "").strip(),
	)


def resolve_governed_kpi_execution_state(
	*,
	definition_state: BusinessDefinitionStateContract,
	formula_state: GovernedFormulaStateContract,
	execution_shape: Any,
	company_name: str = "",
	requested_scope: Dict[str, Any] | None = None,
	registry_payload: Dict[str, Any] | None = None,
) -> GovernedKpiExecutionStateContract:
	requested_execution_shape = str(execution_shape or "").strip()
	requested_company_name = str(company_name or "").strip()
	requested_scope_dict = dict(requested_scope or {})

	if definition_state.resolution_state != "active":
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			resolution_state=_blocked_execution_state(definition_state.activation_state),
			blocked_reason=definition_state.blocked_reason or "definition_not_active",
			reason=(
				f"KPI execution cannot proceed because definition state is "
				f"'{definition_state.resolution_state}'."
			),
		)

	if formula_state.resolution_state != "active":
		resolution_state = "clarify_basis" if formula_state.resolution_state == "ambiguous" else _blocked_execution_state(formula_state.activation_state)
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			resolution_state=resolution_state,
			blocked_reason=formula_state.blocked_reason or "formula_not_active",
			reason=(
				f"KPI execution cannot proceed because formula state is "
				f"'{formula_state.resolution_state}'."
			),
		)

	if not requested_execution_shape:
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape="",
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			resolution_state="clarify_scope",
			reason="Execution shape must be explicit before governed KPI execution can proceed.",
		)

	data = registry_payload if isinstance(registry_payload, dict) else {"executions": list_governed_kpi_execution_specs()}
	executions = data.get("executions")
	if not isinstance(executions, list):
		executions = []

	raw_matches = [
		dict(item)
		for item in executions
		if isinstance(item, dict)
		and str(item.get("definition_id") or "").strip() == str(definition_state.definition_id or "").strip()
		and str(item.get("formula_id") or "").strip() == str(formula_state.formula_id or "").strip()
		and str(item.get("execution_shape") or "").strip() == requested_execution_shape
	]
	matches = [
		item
		for item in raw_matches
		if _company_scope_matches(item.get("company_scope"), requested_company_name)
	]
	if not matches:
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			resolution_state="unsupported_execution_shape",
			reason=(
				f"No governed KPI execution matched definition '{definition_state.definition_id}', "
				f"formula '{formula_state.formula_id}', and execution shape '{requested_execution_shape}'."
			),
			candidate_executions=[_execution_candidate_summary(item) for item in raw_matches],
		)

	if len(matches) > 1:
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			resolution_state="clarify_scope",
			match_count=len(matches),
			matched_execution_ids=[
				str(item.get("execution_id") or "").strip()
				for item in matches
				if str(item.get("execution_id") or "").strip()
			],
			reason=(
				f"Multiple governed KPI executions matched execution shape '{requested_execution_shape}'."
			),
			candidate_executions=[_execution_candidate_summary(item) for item in matches],
		)

	match = dict(matches[0])
	scope_type = str(match.get("scope_type") or "").strip()
	time_scope_type = str(match.get("time_scope_type") or "").strip()
	if time_scope_type == "period_required" and not _has_period_scope(requested_scope_dict):
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			match_count=1,
			matched_execution_ids=[str(match.get("execution_id") or "").strip()],
			execution_id=str(match.get("execution_id") or "").strip(),
			label=str(match.get("label") or "").strip(),
			execution_shape=str(match.get("execution_shape") or "").strip(),
			scope_type=scope_type,
			time_scope_type=time_scope_type,
			resolution_state="clarify_scope",
			reason="This KPI execution requires an explicit business period.",
			candidate_executions=[_execution_candidate_summary(match)],
		)
	if time_scope_type == "as_of_date_required" and not _has_as_of_scope(requested_scope_dict):
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			match_count=1,
			matched_execution_ids=[str(match.get("execution_id") or "").strip()],
			execution_id=str(match.get("execution_id") or "").strip(),
			label=str(match.get("label") or "").strip(),
			execution_shape=str(match.get("execution_shape") or "").strip(),
			scope_type=scope_type,
			time_scope_type=time_scope_type,
			resolution_state="clarify_scope",
			reason="This KPI execution requires an explicit as-of date.",
			candidate_executions=[_execution_candidate_summary(match)],
		)
	if scope_type == "customer" and not _has_customer_scope(requested_scope_dict):
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			match_count=1,
			matched_execution_ids=[str(match.get("execution_id") or "").strip()],
			execution_id=str(match.get("execution_id") or "").strip(),
			label=str(match.get("label") or "").strip(),
			execution_shape=str(match.get("execution_shape") or "").strip(),
			scope_type=scope_type,
			time_scope_type=time_scope_type,
			resolution_state="clarify_scope",
			reason="This KPI execution requires an explicit customer scope.",
			candidate_executions=[_execution_candidate_summary(match)],
		)

	activation_state = str(match.get("activation_state") or "").strip()
	if activation_state != "active":
		return build_governed_kpi_execution_state_contract(
			requested_definition_id=definition_state.definition_id,
			requested_formula_id=formula_state.formula_id,
			requested_execution_shape=requested_execution_shape,
			requested_company_name=requested_company_name,
			requested_scope=requested_scope_dict,
			match_count=1,
			matched_execution_ids=[str(match.get("execution_id") or "").strip()],
			execution_id=str(match.get("execution_id") or "").strip(),
			label=str(match.get("label") or "").strip(),
			execution_shape=str(match.get("execution_shape") or "").strip(),
			scope_type=scope_type,
			time_scope_type=time_scope_type,
			source_mode=str(match.get("source_mode") or "").strip(),
			source_capabilities=_as_str_list(match.get("source_capabilities")),
			source_reports=_as_str_list(match.get("source_reports")),
			supported_filters=_as_str_list(match.get("supported_filters")),
			required_dimensions=_as_str_list(match.get("required_dimensions")),
			value_unit_type=str(match.get("value_unit_type") or "").strip(),
			value_metric_mapping=dict(match.get("value_metric_mapping") or {}),
			activation_state=activation_state,
			blocked_reason=str(match.get("blocked_reason") or "").strip(),
			resolution_state=_blocked_execution_state(activation_state),
			reason=(
				f"Governed KPI execution '{str(match.get('execution_id') or '').strip()}' is not runtime-active."
			),
			candidate_executions=[_execution_candidate_summary(match)],
		)

	return build_governed_kpi_execution_state_contract(
		requested_definition_id=definition_state.definition_id,
		requested_formula_id=formula_state.formula_id,
		requested_execution_shape=requested_execution_shape,
		requested_company_name=requested_company_name,
		requested_scope=requested_scope_dict,
		match_count=1,
		matched_execution_ids=[str(match.get("execution_id") or "").strip()],
		execution_id=str(match.get("execution_id") or "").strip(),
		label=str(match.get("label") or "").strip(),
		execution_shape=str(match.get("execution_shape") or "").strip(),
		scope_type=scope_type,
		time_scope_type=time_scope_type,
		source_mode=str(match.get("source_mode") or "").strip(),
		source_capabilities=_as_str_list(match.get("source_capabilities")),
		source_reports=_as_str_list(match.get("source_reports")),
		supported_filters=_as_str_list(match.get("supported_filters")),
		required_dimensions=_as_str_list(match.get("required_dimensions")),
		value_unit_type=str(match.get("value_unit_type") or "").strip(),
		value_metric_mapping=dict(match.get("value_metric_mapping") or {}),
		activation_state=activation_state,
		resolution_state="active_value",
		reason=(
			f"Governed KPI execution '{str(match.get('execution_id') or '').strip()}' is active for execution shape "
			f"'{requested_execution_shape}'."
		),
		candidate_executions=[_execution_candidate_summary(match)],
	)


def run_governed_kpi_execution_contract_probe() -> Dict[str, Any]:
	validation = validate_governed_kpi_execution_registry()
	from ai_assistant_ui.qwen_chat.business_definition_state import (
		resolve_business_definition_state,
		resolve_governed_formula_state,
	)

	company_name = "Mingalar Mobile Distribution Co., Ltd."
	definition_state = resolve_business_definition_state(
		"average order value sales order",
		lookup_mode="lookup_term",
		company_name=company_name,
	)
	formula_state = resolve_governed_formula_state(
		definition_state=definition_state,
		formula_lookup_value="average_order_value_sales_order_period_formula",
		lookup_mode="formula_id",
		company_name=company_name,
	)
	execution_state = resolve_governed_kpi_execution_state(
		definition_state=definition_state,
		formula_state=formula_state,
		execution_shape="company_period_scalar",
		company_name=company_name,
		requested_scope={"period_start": "2026-03-01", "period_end": "2026-03-31"},
	)
	value_artifact = build_governed_kpi_value_artifact_contract(
		execution_state=execution_state,
		entity_grain="company",
		scope={"company": company_name},
		period_start="2026-03-01",
		period_end="2026-03-31",
		value=1250.0,
		display_value="1,250.0",
		numerator_label="Grand Total",
		numerator_value=12500.0,
		denominator_label="submitted_sales_order_count",
		denominator_value=10.0,
		source_evidence=[{"report_name": "Sales Order List"}],
	)
	ok = (
		validation.status == "pass"
		and execution_state.resolution_state == "active_value"
		and value_artifact.status == "active_value"
		and value_artifact.execution_id == execution_state.execution_id
	)
	return {
		"ok": ok,
		"validation": validation.to_payload(),
		"execution_state": execution_state.to_payload(),
		"value_artifact": value_artifact.to_payload(),
	}
