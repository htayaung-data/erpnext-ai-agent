from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import frappe

from ai_assistant_ui.qwen_chat.contracts import (
	CompiledQueryRequestContract,
	FreshQueryCompilerContract,
	FreshQueryInterpretationContract,
	build_compiled_query_request_contract,
	build_fresh_query_compiler_contract,
)
from ai_assistant_ui.qwen_chat.metadata import (
	ambiguity_rules,
	capability_default_report_name,
	capability_detail_report_name,
	capability_intent_classes,
	capability_report_names,
	capability_summary_report_name,
	get_capability_spec,
	get_report_spec,
	list_intent_class_specs,
	list_capability_specs,
	report_defaultable_filters,
	report_supported_dimensions,
	report_supported_intent_classes,
	report_supported_metrics,
)
from ai_assistant_ui.qwen_chat.semantic_aliases import (
	get_canonical_key,
	get_aliases,
)


@dataclass(frozen=True)
class CompilerOutcome:
	compiler_contract: FreshQueryCompilerContract
	compiled_request_contract: CompiledQueryRequestContract | None


def _today_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _today_date() -> dt.date:
	return dt.datetime.now(dt.timezone.utc).date()


def _clean_list(values: List[Any] | None) -> List[str]:
	return [str(x or "").strip() for x in (values or []) if str(x or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def _semantic_alias_keys(value: Any) -> set[str]:
	"""
	Get semantic aliases from metadata registry.
	
	This function loads aliases from semantic_alias_registry.json metadata file,
	not hardcoded in Python. This is enterprise-grade architecture.
	
	Args:
		value: Business term (e.g., "revenue", "qty", "gross profit")
	
	Returns:
		Set of semantically equivalent canonical keys
	
	Example:
		>>> _semantic_alias_keys("revenue")
		{'revenue', 'sales_amount', 'selling_amount', 'value', ...}
	"""
	key = _normalize_key(value)
	if not key:
		return set()
	
	# Try to resolve to canonical key using metadata registry
	canonical = get_canonical_key(key)
	
	if canonical:
		# Get all aliases for this canonical key from metadata
		all_aliases = get_aliases(canonical)
		# Include the canonical key itself and all aliases
		result = {canonical}
		result.update(alias.lower() for alias in all_aliases)
		return result
	
	# Fallback: return the key itself if not found in registry
	return {key}


def _tokenize(value: Any) -> set[str]:
	text = str(value or "").strip().lower()
	clean = "".join(ch if ch.isalnum() else " " for ch in text)
	return {token for token in clean.split() if token and token not in {"mmk"}}


def _requested_value_matches_supported(requested: str, supported: str) -> bool:
	left = _normalize_key(requested)
	right = _normalize_key(supported)
	if not left or not right:
		return False
	left_aliases = _semantic_alias_keys(requested)
	right_aliases = _semantic_alias_keys(supported)
	if left_aliases & right_aliases:
		return True
	if left == right or left.startswith(right) or right.startswith(left):
		return True
	left_tokens = _tokenize(requested)
	right_tokens = _tokenize(supported)
	if not left_tokens or not right_tokens:
		return False
	return left_tokens.issubset(right_tokens) or right_tokens.issubset(left_tokens)


def _prune_requested_values(requested_values: List[str], supported_values: List[str]) -> List[str]:
	requested = _clean_list(requested_values)
	supported = _clean_list(supported_values)
	if not requested or not supported:
		return requested
	pruned = [
		value
		for value in requested
		if any(_requested_value_matches_supported(value, candidate) for candidate in supported)
	]
	return list(dict.fromkeys(pruned)) or requested


def _first_supported_value_match(requested_values: List[str], supported_values: List[str]) -> str:
	for requested in _clean_list(requested_values):
		for candidate in _clean_list(supported_values):
			if _requested_value_matches_supported(requested, candidate):
				return candidate
	return ""


def _single_company_name() -> str:
	companies = frappe.get_all("Company", pluck="name", limit=2)
	if isinstance(companies, list) and len(companies) == 1:
		return str(companies[0] or "").strip()
	return ""


def _current_fiscal_year_bounds() -> Tuple[str, str]:
	today = _today_date()
	rows = frappe.get_all(
		"Fiscal Year",
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date desc",
		limit=10,
	)
	fallback_start = ""
	fallback_end = ""
	for row in rows or []:
		start_value = row.get("year_start_date")
		end_value = row.get("year_end_date")
		start = dt.date.fromisoformat(str(start_value)) if start_value else None
		end = dt.date.fromisoformat(str(end_value)) if end_value else None
		if not start or not end:
			continue
		if not fallback_start:
			fallback_start = start.isoformat()
			fallback_end = end.isoformat()
		if start <= today <= end:
			return start.isoformat(), end.isoformat()
	return fallback_start, fallback_end


def _current_fiscal_year_name() -> str:
	today = _today_date()
	rows = frappe.get_all(
		"Fiscal Year",
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date desc",
		limit=10,
	)
	fallback_name = ""
	for row in rows or []:
		name = str(row.get("name") or "").strip()
		start_value = row.get("year_start_date")
		end_value = row.get("year_end_date")
		start = dt.date.fromisoformat(str(start_value)) if start_value else None
		end = dt.date.fromisoformat(str(end_value)) if end_value else None
		if not name or not start or not end:
			continue
		if not fallback_name:
			fallback_name = name
		if start <= today <= end:
			return name
	return fallback_name


def _valid_intent_classes() -> set[str]:
	return {
		str(item.get("intent_class_id") or "").strip()
		for item in list_intent_class_specs()
		if isinstance(item, dict) and str(item.get("intent_class_id") or "").strip()
	}


def _capability_candidates_for_intent(intent_class: str) -> List[str]:
	target = str(intent_class or "").strip()
	if not target:
		return []
	out: List[str] = []
	for item in list_capability_specs():
		capability_id = str(item.get("capability_id") or "").strip()
		if not capability_id:
			continue
		if target in capability_intent_classes(capability_id):
			out.append(capability_id)
	return out


def _capability_match_score(
	capability_id: str,
	interpretation: FreshQueryInterpretationContract,
) -> int:
	spec = get_capability_spec(capability_id)
	if not spec:
		return -1
	requested_dimensions = _clean_list(interpretation.requested_dimensions)
	requested_metrics = _clean_list(interpretation.requested_metrics)
	capability_dimensions = {str(value or "").strip().lower() for value in _clean_list(spec.get("dimensions"))}
	capability_metrics = {str(value or "").strip().lower() for value in _clean_list(spec.get("metrics"))}
	score = 0
	for requested in requested_dimensions:
		if str(requested or "").strip().lower() in capability_dimensions:
			score += 3
	for requested in requested_metrics:
		if str(requested or "").strip().lower() in capability_metrics:
			score += 2
	return score


def _date_range_from_time_scope(requested_time_scope: str) -> Tuple[str, str]:
	scope = str(requested_time_scope or "").strip()
	today = _today_date()
	if scope in {"current_period", "current_month"}:
		start = today.replace(day=1)
		return start.isoformat(), today.isoformat()
	if scope == "last_month":
		first_day_current_month = today.replace(day=1)
		last_day_previous_month = first_day_current_month - dt.timedelta(days=1)
		first_day_previous_month = last_day_previous_month.replace(day=1)
		return first_day_previous_month.isoformat(), last_day_previous_month.isoformat()
	if scope == "current_fiscal_year_to_date":
		start, _ = _current_fiscal_year_bounds()
		if start:
			return start, today.isoformat()
	return "", ""


def _resolve_capability(interpretation: FreshQueryInterpretationContract) -> Tuple[str, str]:
	intent_class = str(interpretation.intent_class or "").strip()
	if intent_class and intent_class not in _valid_intent_classes():
		return "", f"Unsupported intent class: {intent_class}"

	candidates = [
		capability_id
		for capability_id in _clean_list(interpretation.candidate_capability_ids)
		if get_capability_spec(capability_id)
	]
	if intent_class:
		candidates = [capability_id for capability_id in candidates if intent_class in capability_intent_classes(capability_id)]
		if not candidates:
			candidates = _capability_candidates_for_intent(intent_class)

	candidates = list(dict.fromkeys(candidates))
	if len(candidates) == 1:
		return candidates[0], "Capability resolved unambiguously from the governed intent class and candidate set."
	if len(candidates) > 1:
		scores = {
			capability_id: _capability_match_score(capability_id, interpretation)
			for capability_id in candidates
		}
		best_score = max(scores.values())
		best_candidates = [
			capability_id
			for capability_id, score in scores.items()
			if score == best_score and score > 0
		]
		if len(best_candidates) == 1:
			return best_candidates[0], "Capability resolved from governed dimension/metric match scoring."
		return "", f"Ambiguous capability candidates: {', '.join(candidates)}"
	return "", "No governed capability could be resolved from the fresh-query interpretation."


def _report_supports_intent(report_name: str, intent_class: str) -> bool:
	supported = set(report_supported_intent_classes(report_name))
	if not supported:
		return True
	return not intent_class or intent_class in supported


def _structural_default_report_for_capability(
	capability_id: str,
	interpretation: FreshQueryInterpretationContract,
	supported_reports: List[str],
) -> str:
	default_report = capability_default_report_name(capability_id)
	summary_report = capability_summary_report_name(capability_id)
	detail_report = capability_detail_report_name(capability_id)
	structural_reports = {
		report_name
		for report_name in (default_report, summary_report, detail_report)
		if str(report_name or "").strip()
	}
	if len(structural_reports) < 2:
		return ""
	supported_set = {report_name for report_name in supported_reports if str(report_name or "").strip()}
	if not default_report or default_report not in supported_set:
		return ""
	if not supported_set.issubset(structural_reports):
		return ""
	advisory_candidates = set(_clean_list(interpretation.candidate_reports))
	if advisory_candidates and not advisory_candidates.issubset(structural_reports):
		return ""
	return default_report


def _select_report(capability_id: str, interpretation: FreshQueryInterpretationContract) -> Tuple[str, str]:
	intent_class = str(interpretation.intent_class or "").strip()
	allowed_reports = capability_report_names(capability_id)
	if not allowed_reports:
		return "", f"No governed reports are registered for capability `{capability_id}`."

	advisory_candidates = [
		report_name
		for report_name in _clean_list(interpretation.candidate_reports)
		if report_name in allowed_reports and _report_supports_intent(report_name, intent_class)
	]
	if len(advisory_candidates) == 1:
		return advisory_candidates[0], "Compiler accepted a single governed advisory report candidate."
	if len(advisory_candidates) > 1:
		structural_default = _structural_default_report_for_capability(capability_id, interpretation, advisory_candidates)
		if structural_default:
			return structural_default, "Compiler selected the governed default report for a structural summary/detail advisory pair."
		return "", f"Ambiguous governed report candidates: {', '.join(advisory_candidates)}"

	supported_reports = [
		report_name for report_name in allowed_reports if _report_supports_intent(report_name, intent_class)
	]
	if len(supported_reports) == 1:
		return supported_reports[0], "Compiler selected the only governed report matching the requested intent class."
	if len(supported_reports) > 1:
		structural_default = _structural_default_report_for_capability(capability_id, interpretation, supported_reports)
		if structural_default:
			return structural_default, "Compiler selected the governed default report for a structural summary/detail report pair."
		return "", f"Ambiguous governed report candidates: {', '.join(supported_reports)}"
	default_report = capability_default_report_name(capability_id)
	if default_report and default_report in allowed_reports and _report_supports_intent(default_report, intent_class):
		return default_report, "Compiler selected the capability default report."
	return "", f"No governed report supports intent class `{intent_class}` for capability `{capability_id}`."


def _extract_candidate_filters(
	interpretation: FreshQueryInterpretationContract,
	report_name: str,
) -> Dict[str, Any]:
	filters: Dict[str, Any] = {}
	slots = interpretation.extracted_slots if isinstance(interpretation.extracted_slots, dict) else {}
	ambiguity_flags = {str(value or "").strip() for value in _clean_list(interpretation.ambiguity_flags)}
	requested_time_scope = str(interpretation.requested_time_scope or "").strip()
	allow_slot_dates = "missing_time_scope" not in ambiguity_flags or requested_time_scope == "as_of_today"
	date_slot_fields = {"report_date", "from_date", "to_date", "period_start_date", "period_end_date"}
	slot_filters = slots.get("filters")
	if isinstance(slot_filters, dict):
		for raw_key, value in slot_filters.items():
			key = str(raw_key or "").strip()
			if not key:
				continue
			if not allow_slot_dates and key in date_slot_fields:
				continue
			filters[key] = value

	report_spec = get_report_spec(report_name)
	required_filters = set(_clean_list(report_spec.get("required_filters")))
	if allow_slot_dates and "report_date" in required_filters and not filters.get("report_date"):
		slot_value = slots.get("report_date")
		if isinstance(slot_value, str) and slot_value.strip():
			filters["report_date"] = slot_value.strip()
	if allow_slot_dates and "from_date" in required_filters and not filters.get("from_date"):
		slot_value = slots.get("from_date")
		if isinstance(slot_value, str) and slot_value.strip():
			filters["from_date"] = slot_value.strip()
	if allow_slot_dates and "to_date" in required_filters and not filters.get("to_date"):
		slot_value = slots.get("to_date")
		if isinstance(slot_value, str) and slot_value.strip():
			filters["to_date"] = slot_value.strip()
	if allow_slot_dates and "period_start_date" in required_filters and not filters.get("period_start_date"):
		slot_value = slots.get("from_date")
		if isinstance(slot_value, str) and slot_value.strip():
			filters["period_start_date"] = slot_value.strip()
	if allow_slot_dates and "period_end_date" in required_filters and not filters.get("period_end_date"):
		slot_value = slots.get("to_date")
		if isinstance(slot_value, str) and slot_value.strip():
			filters["period_end_date"] = slot_value.strip()

	date_from, date_to = _date_range_from_time_scope(interpretation.requested_time_scope)
	if "from_date" in required_filters and not filters.get("from_date") and date_from:
		filters["from_date"] = date_from
	if "to_date" in required_filters and not filters.get("to_date") and date_to:
		filters["to_date"] = date_to
	if "period_start_date" in required_filters and not filters.get("period_start_date") and date_from:
		filters["period_start_date"] = date_from
	if "period_end_date" in required_filters and not filters.get("period_end_date") and date_to:
		filters["period_end_date"] = date_to
	if "report_date" in required_filters and not filters.get("report_date"):
		if date_to:
			filters["report_date"] = date_to
		elif interpretation.requested_time_scope == "as_of_today":
			filters["report_date"] = _today_iso()
	if "tree_type" in required_filters and not filters.get("tree_type"):
		dimensions = _clean_list(interpretation.requested_dimensions)
		match = _first_supported_value_match(dimensions, report_supported_dimensions(report_name))
		if match:
			filters["tree_type"] = match
	if "value_quantity" in required_filters and not filters.get("value_quantity"):
		metrics = _clean_list(interpretation.requested_metrics)
		match = _first_supported_value_match(metrics, report_supported_metrics(report_name))
		if match:
			filters["value_quantity"] = match
	if "group_by" in required_filters and not filters.get("group_by"):
		dimensions = _clean_list(interpretation.requested_dimensions)
		match = _first_supported_value_match(dimensions, report_supported_dimensions(report_name))
		if match:
			filters["group_by"] = match
	return filters


def _apply_defaultable_filters(report_name: str, filters: Dict[str, Any]) -> Dict[str, Any]:
	updated = dict(filters or {})
	for item in report_defaultable_filters(report_name):
		fieldname = str(item.get("fieldname") or "").strip()
		strategy = str(item.get("strategy") or "").strip()
		if not fieldname or updated.get(fieldname):
			continue
		if strategy == "single_company_invariant":
			company = _single_company_name()
			if company:
				updated[fieldname] = company
		elif strategy == "current_date":
			updated[fieldname] = _today_iso()
		elif strategy == "fiscal_year_start_date":
			start, _ = _current_fiscal_year_bounds()
			if start:
				updated[fieldname] = start
		elif strategy == "current_fiscal_year_name":
			fiscal_year_name = _current_fiscal_year_name()
			if fiscal_year_name:
				updated[fieldname] = fiscal_year_name
		elif strategy == "compiler_default":
			value = item.get("value")
			if value not in (None, ""):
				updated[fieldname] = value
	return updated


def _missing_required_filters(report_name: str, filters: Dict[str, Any]) -> List[str]:
	spec = get_report_spec(report_name)
	required = _clean_list(spec.get("required_filters"))
	missing: List[str] = []
	for fieldname in required:
		value = filters.get(fieldname)
		if value is None or (isinstance(value, str) and not value.strip()):
			missing.append(fieldname)
	return missing


def _ambiguity_rule_decision(interpretation: FreshQueryInterpretationContract) -> str:
	intent_class = str(interpretation.intent_class or "").strip()
	if not intent_class:
		return ""
	requested_dimensions = _clean_list(interpretation.requested_dimensions)
	requested_metrics = _clean_list(interpretation.requested_metrics)
	requested_time_scope = str(interpretation.requested_time_scope or "").strip()
	for rule in ambiguity_rules():
		if str(rule.get("intent_class") or "").strip() != intent_class:
			continue
		required_fields = _clean_list(rule.get("requires"))
		required_any = _clean_list(rule.get("requires_any"))
		missing_required = []
		for fieldname in required_fields:
			if fieldname == "requested_time_scope" and not requested_time_scope:
				missing_required.append(fieldname)
			elif fieldname == "requested_dimensions" and not requested_dimensions:
				missing_required.append(fieldname)
			elif fieldname == "requested_metrics" and not requested_metrics:
				missing_required.append(fieldname)
		if missing_required:
			return str(rule.get("decision") or "").strip() or "clarify"
		if required_any:
			satisfied = False
			for fieldname in required_any:
				if fieldname == "requested_time_scope" and requested_time_scope:
					satisfied = True
				if fieldname == "requested_dimensions" and requested_dimensions:
					satisfied = True
				if fieldname == "requested_metrics" and requested_metrics:
					satisfied = True
			if not satisfied:
				return str(rule.get("decision") or "").strip() or "clarify"
	return ""


def compile_fresh_query(
	*,
	request_id: str,
	session_id: str,
	interpretation: FreshQueryInterpretationContract,
	response_policy: Dict[str, Any] | None = None,
) -> CompilerOutcome:
	capability_id, capability_reason = _resolve_capability(interpretation)
	if not capability_id:
		decision = "clarify" if interpretation.ambiguity_flags else "reject"
		reason_type = "capability_ambiguity" if interpretation.ambiguity_flags else "capability_missing"
		reason_details = {
			"capability_candidates": list(interpretation.candidate_capability_ids),
			"ambiguity_flags": list(interpretation.ambiguity_flags),
		}
		compiler_contract = build_fresh_query_compiler_contract(
			request_id=request_id,
			session_id=session_id,
			requested_dimensions=interpretation.requested_dimensions,
			requested_metrics=interpretation.requested_metrics,
			requested_time_scope=interpretation.requested_time_scope,
			decision=decision,
			clarification_required=decision == "clarify",
			compiler_reason=capability_reason or interpretation.ambiguity_reason or "Capability resolution failed.",
			clarification_reason_type=reason_type if decision == "clarify" else "",
			clarification_details=reason_details if decision == "clarify" else {},
		)
		return CompilerOutcome(compiler_contract=compiler_contract, compiled_request_contract=None)

	report_name, report_reason = _select_report(capability_id, interpretation)
	if not report_name:
		compiler_contract = build_fresh_query_compiler_contract(
			request_id=request_id,
			session_id=session_id,
			capability_id=capability_id,
			requested_dimensions=interpretation.requested_dimensions,
			requested_metrics=interpretation.requested_metrics,
			requested_time_scope=interpretation.requested_time_scope,
			decision="clarify",
			clarification_required=True,
			compiler_reason=report_reason or "Report selection remained ambiguous.",
			clarification_reason_type="report_ambiguity",
			clarification_details={"report_candidates": list(interpretation.candidate_reports)},
		)
		return CompilerOutcome(compiler_contract=compiler_contract, compiled_request_contract=None)

	filters = _extract_candidate_filters(interpretation, report_name)
	filters = _apply_defaultable_filters(report_name, filters)
	missing_filters = _missing_required_filters(report_name, filters)
	ambiguity_decision = _ambiguity_rule_decision(interpretation)
	report_spec = get_report_spec(report_name)
	report_family = str(report_spec.get("family") or "").strip()
	requested_dimensions = _prune_requested_values(
		interpretation.requested_dimensions,
		report_supported_dimensions(report_name),
	)
	requested_metrics = _prune_requested_values(
		interpretation.requested_metrics,
		report_supported_metrics(report_name),
	)

	decision = "execute"
	clarification_required = False
	clarification_reason_type = ""
	clarification_details: Dict[str, Any] = {}
	reasons: List[str] = [capability_reason, report_reason]
	if requested_dimensions != _clean_list(interpretation.requested_dimensions):
		reasons.append("Compiler pruned unsupported requested dimensions to the report-governed subset.")
	if requested_metrics != _clean_list(interpretation.requested_metrics):
		reasons.append("Compiler pruned unsupported requested metrics to the report-governed subset.")
	if ambiguity_decision == "clarify":
		decision = "clarify"
		clarification_required = True
		clarification_reason_type = "request_underspecified"
		clarification_details = {"ambiguity_flags": list(interpretation.ambiguity_flags)}
		reasons.append(interpretation.ambiguity_reason or "The request is valid but underspecified for safe execution.")
	if missing_filters:
		decision = "clarify"
		clarification_required = True
		clarification_reason_type = (
			"time_scope_missing"
			if set(missing_filters) & {"from_date", "to_date", "report_date"}
			else "filter_missing"
		)
		clarification_details = {"missing_fields": list(missing_filters)}
		reasons.append(f"Missing or unresolved required filters: {', '.join(missing_filters)}")

	compiler_contract = build_fresh_query_compiler_contract(
		request_id=request_id,
		session_id=session_id,
		capability_id=capability_id,
		selected_report=report_name,
		selected_report_family=report_family,
		completed_filters=filters,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		requested_time_scope=interpretation.requested_time_scope,
		decision=decision,
		clarification_required=clarification_required,
		compiler_reason=" ".join(part for part in reasons if part).strip(),
		clarification_reason_type=clarification_reason_type,
		clarification_details=clarification_details,
	)
	if decision != "execute":
		return CompilerOutcome(compiler_contract=compiler_contract, compiled_request_contract=None)

	compiled_request = build_compiled_query_request_contract(
		request_id=request_id,
		capability_id=capability_id,
		selected_report=report_name,
		filters=filters,
		requested_dimensions=requested_dimensions,
		requested_metrics=requested_metrics,
		response_policy=response_policy if isinstance(response_policy, dict) else {},
	)
	return CompilerOutcome(compiler_contract=compiler_contract, compiled_request_contract=compiled_request)


def run_phase4_compiler_selftests() -> Dict[str, Any]:
	today = _today_iso()
	last_month_start, last_month_end = _date_range_from_time_scope("last_month")
	fiscal_year_start, _ = _current_fiscal_year_bounds()
	payable_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-payable",
		session_id="selftest",
		intent_class="financial_summary",
		candidate_capability_ids=["accounts_payable_read"],
		candidate_reports=["Accounts Payable Summary"],
		requested_dimensions=[],
		requested_metrics=["outstanding_amount"],
		requested_time_scope="as_of_today",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.9,
	)
	trend_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-trend",
		session_id="selftest",
		intent_class="trend_analysis",
		candidate_capability_ids=["sales_read"],
		candidate_reports=["Sales Analytics"],
		requested_dimensions=["Customer"],
		requested_metrics=["Value"],
		requested_time_scope="",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=["missing_time_scope"],
		ambiguity_reason="Trend analysis requires an explicit time scope.",
		confidence=0.82,
	)
	pnl_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-pnl",
		session_id="selftest",
		intent_class="financial_statement",
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=["Profit and Loss Statement"],
		requested_dimensions=[],
		requested_metrics=[],
		requested_time_scope="current_fiscal_year_to_date",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.88,
	)
	balance_sheet_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-balance-sheet",
		session_id="selftest",
		intent_class="financial_statement",
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=["Balance Sheet"],
		requested_dimensions=[],
		requested_metrics=["Total Asset", "Total Liability", "Total Equity"],
		requested_time_scope="current_fiscal_year_to_date",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.88,
	)
	cash_flow_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-cash-flow",
		session_id="selftest",
		intent_class="financial_statement",
		candidate_capability_ids=["financial_statement_read"],
		candidate_reports=["Cash Flow"],
		requested_dimensions=[],
		requested_metrics=["Net Cash from Operations", "Net Change in Cash"],
		requested_time_scope="current_fiscal_year_to_date",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.88,
	)
	product_interpretation = FreshQueryInterpretationContract(
		request_id="selftest-product-performance",
		session_id="selftest",
		intent_class="product_performance",
		candidate_capability_ids=["product_performance_read"],
		candidate_reports=["Gross Profit"],
		requested_dimensions=[],
		requested_metrics=[],
		requested_time_scope="last_month",
		requested_presentation=[],
		extracted_slots={},
		ambiguity_flags=[],
		ambiguity_reason="",
		confidence=0.85,
	)
	results = []
	for interpretation in [
		payable_interpretation,
		trend_interpretation,
		pnl_interpretation,
		balance_sheet_interpretation,
		cash_flow_interpretation,
		product_interpretation,
	]:
		outcome = compile_fresh_query(
			request_id=interpretation.request_id,
			session_id=interpretation.session_id,
			interpretation=interpretation,
			response_policy={"analysis_level": "none"},
		)
		results.append(
			{
				"request_id": interpretation.request_id,
				"compiler_contract": outcome.compiler_contract.to_payload(),
				"compiled_request": outcome.compiled_request_contract.to_payload() if outcome.compiled_request_contract else None,
			}
		)
		if interpretation.request_id == "selftest-payable":
			if outcome.compiler_contract.decision != "execute":
				raise RuntimeError("Payable compiler selftest failed: payable summary did not execute.")
			if outcome.compiler_contract.completed_filters.get("company") != _single_company_name():
				raise RuntimeError("Payable compiler selftest failed: company invariant was not injected.")
			if outcome.compiler_contract.completed_filters.get("report_date") != today:
				raise RuntimeError("Payable compiler selftest failed: report_date default was not applied.")
		if interpretation.request_id == "selftest-trend":
			if outcome.compiler_contract.decision != "clarify":
				raise RuntimeError("Trend compiler selftest failed: underspecified trend query did not clarify.")
		if interpretation.request_id == "selftest-pnl":
			if outcome.compiler_contract.decision != "execute":
				raise RuntimeError("P&L compiler selftest failed: financial statement query did not execute.")
			if outcome.compiler_contract.selected_report != "Profit and Loss Statement":
				raise RuntimeError("P&L compiler selftest failed: wrong report selected.")
			if outcome.compiler_contract.completed_filters.get("period_start_date") != fiscal_year_start:
				raise RuntimeError("P&L compiler selftest failed: fiscal-year start default was not applied.")
			if outcome.compiler_contract.completed_filters.get("period_end_date") != today:
				raise RuntimeError("P&L compiler selftest failed: period_end_date did not resolve to today.")
		if interpretation.request_id == "selftest-product-performance":
			if outcome.compiler_contract.decision != "execute":
				raise RuntimeError("Product-performance compiler selftest failed: last-month product query did not execute.")
			if outcome.compiler_contract.selected_report != "Gross Profit":
				raise RuntimeError("Product-performance compiler selftest failed: wrong report selected.")
			if outcome.compiler_contract.completed_filters.get("group_by") != "Item Code":
				raise RuntimeError("Product-performance compiler selftest failed: default item grouping was not applied.")
			if outcome.compiler_contract.completed_filters.get("from_date") != last_month_start:
				raise RuntimeError("Product-performance compiler selftest failed: last-month from_date was not derived.")
			if outcome.compiler_contract.completed_filters.get("to_date") != last_month_end:
				raise RuntimeError("Product-performance compiler selftest failed: last-month to_date was not derived.")
		if interpretation.request_id == "selftest-balance-sheet":
			if outcome.compiler_contract.decision != "execute":
				raise RuntimeError("Balance Sheet compiler selftest failed: financial statement query did not execute.")
			if outcome.compiler_contract.selected_report != "Balance Sheet":
				raise RuntimeError("Balance Sheet compiler selftest failed: wrong report selected.")
			if outcome.compiler_contract.completed_filters.get("period_start_date") != fiscal_year_start:
				raise RuntimeError("Balance Sheet compiler selftest failed: fiscal-year start default was not applied.")
			if outcome.compiler_contract.completed_filters.get("period_end_date") != today:
				raise RuntimeError("Balance Sheet compiler selftest failed: period_end_date did not resolve to today.")
		if interpretation.request_id == "selftest-cash-flow":
			if outcome.compiler_contract.decision != "execute":
				raise RuntimeError("Cash Flow compiler selftest failed: financial statement query did not execute.")
			if outcome.compiler_contract.selected_report != "Cash Flow":
				raise RuntimeError("Cash Flow compiler selftest failed: wrong report selected.")
			if outcome.compiler_contract.completed_filters.get("from_fiscal_year") != _current_fiscal_year_name():
				raise RuntimeError("Cash Flow compiler selftest failed: from_fiscal_year was not resolved.")
			if outcome.compiler_contract.completed_filters.get("to_fiscal_year") != outcome.compiler_contract.completed_filters.get("from_fiscal_year"):
				raise RuntimeError("Cash Flow compiler selftest failed: to_fiscal_year did not mirror from_fiscal_year.")
			if outcome.compiler_contract.completed_filters.get("period_start_date") != fiscal_year_start:
				raise RuntimeError("Cash Flow compiler selftest failed: fiscal-year start default was not applied.")
			if outcome.compiler_contract.completed_filters.get("period_end_date") != today:
				raise RuntimeError("Cash Flow compiler selftest failed: period_end_date did not resolve to today.")
	return {
		"ok": True,
		"results": results,
	}
