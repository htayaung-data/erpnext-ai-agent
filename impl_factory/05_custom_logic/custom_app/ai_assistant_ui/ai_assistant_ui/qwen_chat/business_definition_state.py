from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	load_business_definition_registry,
	load_governed_formula_registry,
)


ALLOWED_LOOKUP_MODES = {
	"auto",
	"definition_id",
	"formula_id",
	"label",
	"lookup_term",
}

ALLOWED_RESOLUTION_STATES = {
	"active",
	"blocked",
	"undefined",
	"ambiguous",
}

ALLOWED_REGISTRY_ACTIVATION_STATES = {
	"active",
	"blocked_missing_policy",
	"blocked_missing_data",
	"draft_unapproved",
	"deprecated",
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


def _normalize_lookup_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	if not text:
		return ""
	text = re.sub(r"[_-]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def normalize_business_definition_lookup_mode(value: Any) -> str:
	mode = str(value or "auto").strip().lower() or "auto"
	return mode if mode in ALLOWED_LOOKUP_MODES else "auto"


def normalize_registry_activation_state(value: Any) -> str:
	state = str(value or "").strip()
	return state if state in ALLOWED_REGISTRY_ACTIVATION_STATES else ""


def normalize_blocked_vs_active_resolution_state(
	activation_state: Any,
	*,
	in_scope: bool = True,
) -> str:
	if not in_scope:
		return "blocked"
	return "active" if normalize_registry_activation_state(activation_state) == "active" else "blocked"


def _entry_lookup_terms(entry: Dict[str, Any]) -> List[str]:
	terms: List[str] = []
	for key in ("definition_id", "label", "formula_id"):
		text = str(entry.get(key) or "").strip()
		if text:
			terms.append(text)
	for key in ("lookup_terms", "aliases", "query_terms"):
		terms.extend(_as_str_list(entry.get(key)))
	seen: set[str] = set()
	normalized_terms: List[str] = []
	for item in terms:
		normalized = _normalize_lookup_key(item)
		if normalized and normalized not in seen:
			seen.add(normalized)
			normalized_terms.append(normalized)
	return normalized_terms


def _company_scope_matches(entry: Dict[str, Any], company_name: str, *, empty_scope_means_global: bool) -> bool:
	if not str(company_name or "").strip():
		return True
	scope_values = _as_str_list(entry.get("company_scope"))
	if not scope_values:
		return bool(empty_scope_means_global)
	normalized_company = _normalize_lookup_key(company_name)
	normalized_scope = {_normalize_lookup_key(value) for value in scope_values if _normalize_lookup_key(value)}
	return "global" in normalized_scope or normalized_company in normalized_scope


def _matches_lookup(entry: Dict[str, Any], *, lookup_value: str, lookup_mode: str) -> bool:
	target = _normalize_lookup_key(lookup_value)
	if not target:
		return False
	mode = normalize_business_definition_lookup_mode(lookup_mode)
	if mode == "definition_id":
		return target == _normalize_lookup_key(entry.get("definition_id"))
	if mode == "formula_id":
		return target == _normalize_lookup_key(entry.get("formula_id"))
	if mode == "label":
		return target == _normalize_lookup_key(entry.get("label"))
	if mode == "lookup_term":
		terms = []
		for key in ("lookup_terms", "aliases", "query_terms"):
			terms.extend(_as_str_list(entry.get(key)))
		if not terms:
			terms = [str(entry.get("label") or "").strip()]
		return target in {_normalize_lookup_key(item) for item in terms if _normalize_lookup_key(item)}
	return target in _entry_lookup_terms(entry)


def _definition_candidate_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"definition_id": str(entry.get("definition_id") or "").strip(),
		"label": str(entry.get("label") or "").strip(),
		"activation_state": normalize_registry_activation_state(entry.get("activation_state")),
		"company_scope": _as_str_list(entry.get("company_scope")),
		"clarify_policy": str(entry.get("clarify_policy") or "").strip(),
		"blocked_reason": str(entry.get("blocked_reason") or "").strip(),
	}


def _formula_candidate_summary(entry: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"formula_id": str(entry.get("formula_id") or "").strip(),
		"definition_id": str(entry.get("definition_id") or "").strip(),
		"label": str(entry.get("label") or "").strip(),
		"activation_state": normalize_registry_activation_state(entry.get("activation_state")),
		"blocked_reason": str(entry.get("blocked_reason") or "").strip(),
	}


@dataclass(frozen=True)
class BusinessDefinitionStateContract:
	lookup_value: str
	lookup_mode: str
	requested_company_name: str
	resolution_state: str
	match_count: int
	matched_definition_ids: List[str] = field(default_factory=list)
	definition_id: str = ""
	label: str = ""
	owner: str = ""
	company_scope: List[str] = field(default_factory=list)
	entity_grain: str = ""
	time_basis: str = ""
	semantic_category: str = ""
	activation_state: str = ""
	source_of_truth: Dict[str, Any] = field(default_factory=dict)
	clarify_policy: str = ""
	blocked_reason: str = ""
	reason: str = ""
	candidate_definitions: List[Dict[str, Any]] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_business_definition_state_contract",
			"contract_version": "1.0",
			"lookup_value": self.lookup_value,
			"lookup_mode": self.lookup_mode,
			"requested_company_name": self.requested_company_name,
			"resolution_state": self.resolution_state,
			"match_count": int(max(0, self.match_count)),
			"matched_definition_ids": list(self.matched_definition_ids),
			"definition_id": self.definition_id,
			"label": self.label,
			"owner": self.owner,
			"company_scope": list(self.company_scope),
			"entity_grain": self.entity_grain,
			"time_basis": self.time_basis,
			"semantic_category": self.semantic_category,
			"activation_state": self.activation_state,
			"source_of_truth": dict(self.source_of_truth),
			"clarify_policy": self.clarify_policy,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
			"candidate_definitions": [dict(item) for item in self.candidate_definitions if isinstance(item, dict)],
		}


@dataclass(frozen=True)
class GovernedFormulaStateContract:
	requested_definition_id: str
	lookup_value: str
	lookup_mode: str
	requested_company_name: str
	resolution_state: str
	match_count: int
	matched_formula_ids: List[str] = field(default_factory=list)
	formula_id: str = ""
	definition_id: str = ""
	label: str = ""
	formula_type: str = ""
	input_metrics: List[str] = field(default_factory=list)
	input_requirements: List[Dict[str, Any]] = field(default_factory=list)
	source_capabilities: List[str] = field(default_factory=list)
	source_reports: List[str] = field(default_factory=list)
	aggregation_rule: str = ""
	grain_requirements: List[str] = field(default_factory=list)
	time_scope_requirements: List[str] = field(default_factory=list)
	activation_state: str = ""
	blocked_reason: str = ""
	reason: str = ""
	candidate_formulas: List[Dict[str, Any]] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_governed_formula_state_contract",
			"contract_version": "1.0",
			"requested_definition_id": self.requested_definition_id,
			"lookup_value": self.lookup_value,
			"lookup_mode": self.lookup_mode,
			"requested_company_name": self.requested_company_name,
			"resolution_state": self.resolution_state,
			"match_count": int(max(0, self.match_count)),
			"matched_formula_ids": list(self.matched_formula_ids),
			"formula_id": self.formula_id,
			"definition_id": self.definition_id,
			"label": self.label,
			"formula_type": self.formula_type,
			"input_metrics": list(self.input_metrics),
			"input_requirements": [dict(item) for item in self.input_requirements if isinstance(item, dict)],
			"source_capabilities": list(self.source_capabilities),
			"source_reports": list(self.source_reports),
			"aggregation_rule": self.aggregation_rule,
			"grain_requirements": list(self.grain_requirements),
			"time_scope_requirements": list(self.time_scope_requirements),
			"activation_state": self.activation_state,
			"blocked_reason": self.blocked_reason,
			"reason": self.reason,
			"candidate_formulas": [dict(item) for item in self.candidate_formulas if isinstance(item, dict)],
		}


def build_business_definition_state_contract(
	*,
	lookup_value: str,
	lookup_mode: str = "auto",
	requested_company_name: str = "",
	resolution_state: str = "undefined",
	match_count: int = 0,
	matched_definition_ids: List[str] | None = None,
	definition_id: str = "",
	label: str = "",
	owner: str = "",
	company_scope: List[str] | None = None,
	entity_grain: str = "",
	time_basis: str = "",
	semantic_category: str = "",
	activation_state: str = "",
	source_of_truth: Dict[str, Any] | None = None,
	clarify_policy: str = "",
	blocked_reason: str = "",
	reason: str = "",
	candidate_definitions: List[Dict[str, Any]] | None = None,
) -> BusinessDefinitionStateContract:
	state = str(resolution_state or "undefined").strip().lower() or "undefined"
	if state not in ALLOWED_RESOLUTION_STATES:
		state = "undefined"
	return BusinessDefinitionStateContract(
		lookup_value=str(lookup_value or "").strip(),
		lookup_mode=normalize_business_definition_lookup_mode(lookup_mode),
		requested_company_name=str(requested_company_name or "").strip(),
		resolution_state=state,
		match_count=int(max(0, match_count)),
		matched_definition_ids=[
			str(value or "").strip()
			for value in (matched_definition_ids or [])
			if str(value or "").strip()
		],
		definition_id=str(definition_id or "").strip(),
		label=str(label or "").strip(),
		owner=str(owner or "").strip(),
		company_scope=_as_str_list(company_scope or []),
		entity_grain=str(entity_grain or "").strip(),
		time_basis=str(time_basis or "").strip(),
		semantic_category=str(semantic_category or "").strip(),
		activation_state=normalize_registry_activation_state(activation_state),
		source_of_truth=dict(source_of_truth or {}),
		clarify_policy=str(clarify_policy or "").strip(),
		blocked_reason=str(blocked_reason or "").strip(),
		reason=str(reason or "").strip(),
		candidate_definitions=[dict(item) for item in (candidate_definitions or []) if isinstance(item, dict)],
	)


def build_governed_formula_state_contract(
	*,
	requested_definition_id: str = "",
	lookup_value: str = "",
	lookup_mode: str = "auto",
	requested_company_name: str = "",
	resolution_state: str = "undefined",
	match_count: int = 0,
	matched_formula_ids: List[str] | None = None,
	formula_id: str = "",
	definition_id: str = "",
	label: str = "",
	formula_type: str = "",
	input_metrics: List[str] | None = None,
	input_requirements: List[Dict[str, Any]] | None = None,
	source_capabilities: List[str] | None = None,
	source_reports: List[str] | None = None,
	aggregation_rule: str = "",
	grain_requirements: List[str] | None = None,
	time_scope_requirements: List[str] | None = None,
	activation_state: str = "",
	blocked_reason: str = "",
	reason: str = "",
	candidate_formulas: List[Dict[str, Any]] | None = None,
) -> GovernedFormulaStateContract:
	state = str(resolution_state or "undefined").strip().lower() or "undefined"
	if state not in ALLOWED_RESOLUTION_STATES:
		state = "undefined"
	return GovernedFormulaStateContract(
		requested_definition_id=str(requested_definition_id or "").strip(),
		lookup_value=str(lookup_value or "").strip(),
		lookup_mode=normalize_business_definition_lookup_mode(lookup_mode),
		requested_company_name=str(requested_company_name or "").strip(),
		resolution_state=state,
		match_count=int(max(0, match_count)),
		matched_formula_ids=[
			str(value or "").strip()
			for value in (matched_formula_ids or [])
			if str(value or "").strip()
		],
		formula_id=str(formula_id or "").strip(),
		definition_id=str(definition_id or "").strip(),
		label=str(label or "").strip(),
		formula_type=str(formula_type or "").strip(),
		input_metrics=_as_str_list(input_metrics or []),
		input_requirements=_as_dict_list(input_requirements or []),
		source_capabilities=_as_str_list(source_capabilities or []),
		source_reports=_as_str_list(source_reports or []),
		aggregation_rule=str(aggregation_rule or "").strip(),
		grain_requirements=_as_str_list(grain_requirements or []),
		time_scope_requirements=_as_str_list(time_scope_requirements or []),
		activation_state=normalize_registry_activation_state(activation_state),
		blocked_reason=str(blocked_reason or "").strip(),
		reason=str(reason or "").strip(),
		candidate_formulas=[dict(item) for item in (candidate_formulas or []) if isinstance(item, dict)],
	)


def resolve_business_definition_state(
	lookup_value: Any,
	*,
	lookup_mode: str = "auto",
	company_name: str = "",
	registry_payload: Dict[str, Any] | None = None,
) -> BusinessDefinitionStateContract:
	requested_lookup = str(lookup_value or "").strip()
	mode = normalize_business_definition_lookup_mode(lookup_mode)
	if not requested_lookup:
		return build_business_definition_state_contract(
			lookup_value="",
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="undefined",
			reason="No governed business-definition lookup value was provided.",
		)

	data = registry_payload if isinstance(registry_payload, dict) else load_business_definition_registry()
	definitions = data.get("definitions")
	if not isinstance(definitions, list):
		definitions = []

	raw_matches = [
		dict(item)
		for item in definitions
		if isinstance(item, dict) and _matches_lookup(item, lookup_value=requested_lookup, lookup_mode=mode)
	]
	if not raw_matches:
		return build_business_definition_state_contract(
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="undefined",
			reason=f"No governed business definition matched '{requested_lookup}'.",
		)

	scoped_matches = [
		item
		for item in raw_matches
		if _company_scope_matches(item, str(company_name or "").strip(), empty_scope_means_global=False)
	]
	if str(company_name or "").strip() and not scoped_matches:
		return build_business_definition_state_contract(
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="blocked",
			match_count=len(raw_matches),
			matched_definition_ids=[
				str(item.get("definition_id") or "").strip()
				for item in raw_matches
				if str(item.get("definition_id") or "").strip()
			],
			blocked_reason="definition_out_of_company_scope",
			reason=(
				f"Governed business definitions matched '{requested_lookup}', but none are configured for "
				f"company scope '{str(company_name or '').strip()}'."
			),
			candidate_definitions=[_definition_candidate_summary(item) for item in raw_matches],
		)

	candidates = scoped_matches or raw_matches
	if len(candidates) > 1:
		return build_business_definition_state_contract(
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="ambiguous",
			match_count=len(candidates),
			matched_definition_ids=[
				str(item.get("definition_id") or "").strip()
				for item in candidates
				if str(item.get("definition_id") or "").strip()
			],
			reason=f"Multiple governed business definitions match '{requested_lookup}'.",
			candidate_definitions=[_definition_candidate_summary(item) for item in candidates],
		)

	match = dict(candidates[0])
	activation_state = normalize_registry_activation_state(match.get("activation_state"))
	resolution_state = normalize_blocked_vs_active_resolution_state(activation_state, in_scope=True)
	blocked_reason = str(match.get("blocked_reason") or "").strip()
	reason = (
		f"Governed business definition '{str(match.get('definition_id') or '').strip()}' is active and ready for runtime use."
		if resolution_state == "active"
		else (
			f"Governed business definition '{str(match.get('definition_id') or '').strip()}' is not runtime-active "
			f"because activation_state is '{activation_state or 'unknown'}'."
		)
	)
	return build_business_definition_state_contract(
		lookup_value=requested_lookup,
		lookup_mode=mode,
		requested_company_name=company_name,
		resolution_state=resolution_state,
		match_count=1,
		matched_definition_ids=[str(match.get("definition_id") or "").strip()],
		definition_id=str(match.get("definition_id") or "").strip(),
		label=str(match.get("label") or "").strip(),
		owner=str(match.get("owner") or "").strip(),
		company_scope=_as_str_list(match.get("company_scope")),
		entity_grain=str(match.get("entity_grain") or "").strip(),
		time_basis=str(match.get("time_basis") or "").strip(),
		semantic_category=str(match.get("semantic_category") or "").strip(),
		activation_state=activation_state,
		source_of_truth=dict(match.get("source_of_truth") or {}) if isinstance(match.get("source_of_truth"), dict) else {},
		clarify_policy=str(match.get("clarify_policy") or "").strip(),
		blocked_reason=blocked_reason,
		reason=reason,
		candidate_definitions=[_definition_candidate_summary(match)],
	)


def resolve_governed_formula_state(
	*,
	definition_id: Any = "",
	formula_lookup_value: Any = "",
	lookup_mode: str = "auto",
	company_name: str = "",
	definition_state: BusinessDefinitionStateContract | None = None,
	formula_registry_payload: Dict[str, Any] | None = None,
	business_definition_payload: Dict[str, Any] | None = None,
) -> GovernedFormulaStateContract:
	requested_definition_id = str(definition_id or "").strip()
	requested_lookup = str(formula_lookup_value or "").strip()
	mode = normalize_business_definition_lookup_mode(lookup_mode)

	parent_definition_state = definition_state
	if parent_definition_state is None and requested_definition_id:
		parent_definition_state = resolve_business_definition_state(
			requested_definition_id,
			lookup_mode="definition_id",
			company_name=company_name,
			registry_payload=business_definition_payload,
		)
	if parent_definition_state is not None and parent_definition_state.definition_id and not requested_definition_id:
		requested_definition_id = parent_definition_state.definition_id
	if parent_definition_state is not None and parent_definition_state.resolution_state != "active":
		return build_governed_formula_state_contract(
			requested_definition_id=requested_definition_id,
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="blocked",
			reason=(
				f"Governed formula resolution is blocked because parent definition state is "
				f"'{parent_definition_state.resolution_state}'."
			),
			blocked_reason=parent_definition_state.blocked_reason or "parent_definition_not_active",
		)

	if not requested_definition_id and not requested_lookup:
		return build_governed_formula_state_contract(
			requested_definition_id="",
			lookup_value="",
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="undefined",
			reason="No governed formula lookup or definition reference was provided.",
		)

	data = formula_registry_payload if isinstance(formula_registry_payload, dict) else load_governed_formula_registry()
	formulas = data.get("formulas")
	if not isinstance(formulas, list):
		formulas = []

	raw_matches: List[Dict[str, Any]] = []
	for item in formulas:
		if not isinstance(item, dict):
			continue
		if requested_definition_id and str(item.get("definition_id") or "").strip() != requested_definition_id:
			continue
		if requested_lookup and not _matches_lookup(item, lookup_value=requested_lookup, lookup_mode=mode):
			continue
		raw_matches.append(dict(item))

	if not raw_matches:
		target = requested_lookup or requested_definition_id
		return build_governed_formula_state_contract(
			requested_definition_id=requested_definition_id,
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="undefined",
			reason=f"No governed formula matched '{target}'.",
		)

	scoped_matches = [
		item
		for item in raw_matches
		if _company_scope_matches(item, str(company_name or "").strip(), empty_scope_means_global=True)
	]
	if str(company_name or "").strip() and not scoped_matches:
		return build_governed_formula_state_contract(
			requested_definition_id=requested_definition_id,
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="blocked",
			match_count=len(raw_matches),
			matched_formula_ids=[
				str(item.get("formula_id") or "").strip()
				for item in raw_matches
				if str(item.get("formula_id") or "").strip()
			],
			blocked_reason="formula_out_of_company_scope",
			reason=(
				f"Governed formulas matched the requested lookup, but none are configured for "
				f"company scope '{str(company_name or '').strip()}'."
			),
			candidate_formulas=[_formula_candidate_summary(item) for item in raw_matches],
		)

	candidates = scoped_matches or raw_matches
	if len(candidates) > 1:
		return build_governed_formula_state_contract(
			requested_definition_id=requested_definition_id,
			lookup_value=requested_lookup,
			lookup_mode=mode,
			requested_company_name=company_name,
			resolution_state="ambiguous",
			match_count=len(candidates),
			matched_formula_ids=[
				str(item.get("formula_id") or "").strip()
				for item in candidates
				if str(item.get("formula_id") or "").strip()
			],
			reason="Multiple governed formulas satisfy the requested definition state.",
			candidate_formulas=[_formula_candidate_summary(item) for item in candidates],
		)

	match = dict(candidates[0])
	activation_state = normalize_registry_activation_state(match.get("activation_state"))
	resolution_state = normalize_blocked_vs_active_resolution_state(activation_state, in_scope=True)
	blocked_reason = str(match.get("blocked_reason") or "").strip()
	reason = (
		f"Governed formula '{str(match.get('formula_id') or '').strip()}' is active and ready for runtime use."
		if resolution_state == "active"
		else (
			f"Governed formula '{str(match.get('formula_id') or '').strip()}' is not runtime-active because "
			f"activation_state is '{activation_state or 'unknown'}'."
		)
	)
	return build_governed_formula_state_contract(
		requested_definition_id=requested_definition_id,
		lookup_value=requested_lookup,
		lookup_mode=mode,
		requested_company_name=company_name,
		resolution_state=resolution_state,
		match_count=1,
		matched_formula_ids=[str(match.get("formula_id") or "").strip()],
		formula_id=str(match.get("formula_id") or "").strip(),
		definition_id=str(match.get("definition_id") or "").strip(),
		label=str(match.get("label") or "").strip(),
		formula_type=str(match.get("formula_type") or "").strip(),
		input_metrics=_as_str_list(match.get("input_metrics")),
		input_requirements=_as_dict_list(match.get("input_requirements")),
		source_capabilities=_as_str_list(match.get("source_capabilities")),
		source_reports=_as_str_list(match.get("source_reports")),
		aggregation_rule=str(match.get("aggregation_rule") or "").strip(),
		grain_requirements=_as_str_list(match.get("grain_requirements")),
		time_scope_requirements=_as_str_list(match.get("time_scope_requirements")),
		activation_state=activation_state,
		blocked_reason=blocked_reason,
		reason=reason,
		candidate_formulas=[_formula_candidate_summary(match)],
	)


def run_business_definition_state_probe() -> Dict[str, Any]:
	definition_payload = {
		"definitions": [
			{
				"definition_id": "customer_tenure_first_invoice",
				"label": "Customer Tenure By First Invoice",
				"owner": "finance",
				"company_scope": ["global"],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "customer_lifecycle",
				"activation_state": "active",
				"source_of_truth": {"kind": "sales_invoice"},
				"clarify_policy": "clarify_basis",
				"lookup_terms": ["customer tenure by invoice"],
			},
			{
				"definition_id": "customer_tenure_customer_created",
				"label": "Customer Tenure By Customer Creation",
				"owner": "finance",
				"company_scope": ["global"],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "customer_lifecycle",
				"activation_state": "draft_unapproved",
				"source_of_truth": {"kind": "customer"},
				"clarify_policy": "clarify_basis",
				"blocked_reason": "awaiting approved generic tenure basis",
				"lookup_terms": ["customer tenure", "tenure"],
			},
			{
				"definition_id": "customer_tenure_first_invoice_generic",
				"label": "Customer Tenure By First Invoice Generic",
				"owner": "finance",
				"company_scope": ["global"],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "customer_lifecycle",
				"activation_state": "active",
				"source_of_truth": {"kind": "sales_invoice"},
				"clarify_policy": "clarify_basis",
				"lookup_terms": ["customer tenure", "tenure"],
			},
			{
				"definition_id": "credit_utilization",
				"label": "Customer Credit Utilization",
				"owner": "finance",
				"company_scope": ["Mingalar Mobile Distribution Co., Ltd."],
				"entity_grain": "customer",
				"time_basis": "as_of_date",
				"semantic_category": "credit_risk",
				"activation_state": "blocked_missing_policy",
				"source_of_truth": {"kind": "accounts_receivable_aging"},
				"clarify_policy": "clarify_basis",
				"blocked_reason": "threshold semantics not yet approved",
				"lookup_terms": ["credit utilization"],
			},
		]
	}
	formula_payload = {
		"formulas": [
			{
				"formula_id": "customer_tenure_days_first_invoice",
				"definition_id": "customer_tenure_first_invoice",
				"label": "Customer Tenure Days By First Invoice",
				"formula_type": "date_diff_days",
				"input_metrics": ["first_invoice_date", "as_of_date"],
				"input_requirements": [
					{"metric_key": "first_invoice_date", "requirement_type": "required"},
					{"metric_key": "as_of_date", "requirement_type": "required"},
				],
				"source_capabilities": ["customer_invoice_detail"],
				"source_reports": ["Sales Register"],
				"aggregation_rule": "direct_entity_value",
				"grain_requirements": ["customer"],
				"time_scope_requirements": ["as_of_date_required"],
				"activation_state": "active",
			},
			{
				"formula_id": "credit_utilization_outstanding_vs_limit",
				"definition_id": "credit_utilization",
				"label": "Credit Utilization Outstanding Vs Limit",
				"formula_type": "ratio",
				"input_metrics": ["outstanding_amount", "credit_limit"],
				"input_requirements": [
					{"metric_key": "outstanding_amount", "requirement_type": "required"},
					{"metric_key": "credit_limit", "requirement_type": "required"},
				],
				"source_capabilities": ["customer_credit_status"],
				"source_reports": ["Accounts Receivable Aging"],
				"aggregation_rule": "ratio_of_sums",
				"grain_requirements": ["customer"],
				"time_scope_requirements": ["as_of_date_required"],
				"activation_state": "active",
			},
		]
	}

	active_definition = resolve_business_definition_state(
		"customer_tenure_first_invoice",
		lookup_mode="definition_id",
		registry_payload=definition_payload,
	)
	ambiguous_definition = resolve_business_definition_state(
		"tenure",
		lookup_mode="lookup_term",
		registry_payload=definition_payload,
	)
	blocked_definition = resolve_business_definition_state(
		"credit utilization",
		lookup_mode="lookup_term",
		company_name="Mingalar Mobile Distribution Co., Ltd.",
		registry_payload=definition_payload,
	)
	formula_blocked_by_parent = resolve_governed_formula_state(
		definition_state=blocked_definition,
		formula_registry_payload=formula_payload,
		business_definition_payload=definition_payload,
		company_name="Mingalar Mobile Distribution Co., Ltd.",
	)

	ok = (
		active_definition.resolution_state == "active"
		and ambiguous_definition.resolution_state == "ambiguous"
		and blocked_definition.resolution_state == "blocked"
		and formula_blocked_by_parent.resolution_state == "blocked"
	)
	return {
		"ok": ok,
		"active_definition": active_definition.to_payload(),
		"ambiguous_definition": ambiguous_definition.to_payload(),
		"blocked_definition": blocked_definition.to_payload(),
		"formula_blocked_by_parent": formula_blocked_by_parent.to_payload(),
	}


def run_governed_kpi_registry_probe() -> Dict[str, Any]:
	company_name = "Mingalar Mobile Distribution Co., Ltd."

	average_order_value = resolve_business_definition_state(
		"average order value",
		lookup_mode="lookup_term",
		company_name=company_name,
	)
	tenure = resolve_business_definition_state(
		"tenure",
		lookup_mode="lookup_term",
		company_name=company_name,
	)
	collection_ratio = resolve_business_definition_state(
		"collection ratio",
		lookup_mode="lookup_term",
		company_name=company_name,
	)
	credit_utilization = resolve_business_definition_state(
		"credit utilization",
		lookup_mode="lookup_term",
		company_name=company_name,
	)
	credit_utilization_formula = resolve_governed_formula_state(
		definition_state=credit_utilization,
		company_name=company_name,
	)

	ok = (
		average_order_value.resolution_state == "ambiguous"
		and tenure.resolution_state == "ambiguous"
		and collection_ratio.resolution_state == "active"
		and credit_utilization.resolution_state == "active"
		and credit_utilization_formula.resolution_state == "active"
	)
	return {
		"ok": ok,
		"average_order_value": average_order_value.to_payload(),
		"tenure": tenure.to_payload(),
		"collection_ratio": collection_ratio.to_payload(),
		"credit_utilization": credit_utilization.to_payload(),
		"credit_utilization_formula": credit_utilization_formula.to_payload(),
	}
