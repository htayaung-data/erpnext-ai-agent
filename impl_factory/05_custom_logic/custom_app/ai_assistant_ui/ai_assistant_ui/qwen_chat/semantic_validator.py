from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.capability_adapters import extract_grounded_table
from ai_assistant_ui.qwen_chat.contracts import build_semantic_intent_validation_contract
from ai_assistant_ui.qwen_chat.metadata import (
	capability_semantic_tags,
	get_intent_class_spec,
	get_report_spec,
	report_semantic_tags,
	report_supported_dimensions,
	report_supported_intent_classes,
	report_supported_metrics,
	semantic_validation_policy,
)


def _today_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([str(value or "").strip() for value in values if str(value or "").strip()]))


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return text.strip("_")


def _tokenize(value: Any) -> set[str]:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return {token for token in text.split() if token and token not in {"mmk"}}


def _matches_requested_value(requested: str, observed: str) -> bool:
	left = _normalize_key(requested)
	right = _normalize_key(observed)
	if not left or not right:
		return False
	if left == right or left.startswith(right) or right.startswith(left):
		return True
	left_tokens = _tokenize(requested)
	right_tokens = _tokenize(observed)
	if not left_tokens or not right_tokens:
		return False
	return left_tokens.issubset(right_tokens) or right_tokens.issubset(left_tokens)


def _safe_json_loads(value: Any) -> Any:
	if isinstance(value, (dict, list)):
		return value
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def _tool_trace_items(runtime_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	values = runtime_payload.get("tool_trace")
	if not isinstance(values, list):
		return []
	return [item for item in values if isinstance(item, dict)]


def _report_tool(runtime_payload: Dict[str, Any]) -> Dict[str, Any]:
	for item in reversed(_tool_trace_items(runtime_payload)):
		if str(item.get("tool") or "").strip() == "erp_fac-generate_report":
			return item
	return {}


def _tool_args(item: Dict[str, Any]) -> Dict[str, Any]:
	value = item.get("detail_obj")
	if isinstance(value, dict):
		return value
	parsed = _safe_json_loads(item.get("detail"))
	return parsed if isinstance(parsed, dict) else {}


def _tool_filters(item: Dict[str, Any]) -> Dict[str, Any]:
	filters = _tool_args(item).get("filters")
	return dict(filters) if isinstance(filters, dict) else {}


def _headers_and_rows(item: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	headers, rows = extract_grounded_table(item, {})
	clean_headers = [str(value or "").strip() for value in headers if str(value or "").strip()]
	clean_rows = [row for row in rows if isinstance(row, dict)]
	return clean_headers, clean_rows


def _row_text_values(rows: List[Dict[str, Any]]) -> List[str]:
	values: List[str] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		for value in row.values():
			text = str(value or "").strip()
			if text:
				values.append(text)
	return values


def _metric_alias_candidates(requested: str, report_name: str) -> List[str]:
	candidates = [str(requested or "").strip()]
	normalized_report = _normalize_key(report_name)
	normalized_requested = _normalize_key(requested)
	if normalized_report == "profit_and_loss_statement":
		aliases = {
			"total_income": ["Total Income (Credit)"],
			"total_expense": ["Total Expense (Debit)"],
			"net_profit": ["Profit for the year", "Net Profit"],
			"profit": ["Profit for the year", "Net Profit"],
			"loss": ["Loss for the year", "Profit for the year"],
		}
		candidates.extend(aliases.get(normalized_requested, []))
	return _dedupe(candidates)


def _requested_metric_present(
	requested_metrics: List[str],
	*,
	report_name: str,
	headers: List[str],
	rows: List[Dict[str, Any]],
	actual_filters: Dict[str, Any],
) -> Tuple[bool, List[str]]:
	if not requested_metrics:
		return True, []
	allowed = report_supported_metrics(report_name)
	value_quantity = str(actual_filters.get("value_quantity") or "").strip()
	effective_requested_metrics = list(requested_metrics)
	if value_quantity:
		matching_selected_metric = [
			requested
			for requested in requested_metrics
			if _matches_requested_value(requested, value_quantity)
		]
		if matching_selected_metric:
			effective_requested_metrics = matching_selected_metric
	row_values = _row_text_values(rows)
	errors: List[str] = []
	for requested in effective_requested_metrics:
		if allowed and not any(_matches_requested_value(requested, candidate) for candidate in allowed):
			errors.append(f"Requested metric `{requested}` is not governed for report `{report_name}`.")
			continue
		candidates = _metric_alias_candidates(requested, report_name)
		if any(
			_matches_requested_value(candidate, header)
			for candidate in candidates
			for header in headers
		):
			continue
		if value_quantity and any(_matches_requested_value(candidate, value_quantity) for candidate in candidates):
			continue
		if any(
			_matches_requested_value(candidate, observed)
			for candidate in candidates
			for observed in row_values
		):
			continue
		errors.append(f"Requested metric `{requested}` was not found in the grounded result schema.")
	return not errors, errors


def _requested_dimension_present(
	requested_dimensions: List[str],
	*,
	report_name: str,
	headers: List[str],
	actual_filters: Dict[str, Any],
) -> Tuple[bool, List[str]]:
	if not requested_dimensions:
		return True, []
	allowed = report_supported_dimensions(report_name)
	tree_type = str(actual_filters.get("tree_type") or "").strip()
	errors: List[str] = []
	for requested in requested_dimensions:
		if allowed and not any(_matches_requested_value(requested, candidate) for candidate in allowed):
			errors.append(f"Requested dimension `{requested}` is not governed for report `{report_name}`.")
			continue
		if any(_matches_requested_value(requested, header) for header in headers):
			continue
		if tree_type and _matches_requested_value(requested, tree_type):
			continue
		errors.append(f"Requested dimension `{requested}` was not found in the grounded result schema.")
	return not errors, errors


def _expected_semantic_tags(capability_id: str, intent_class: str) -> List[str]:
	intent_tags = _clean_list(get_intent_class_spec(intent_class).get("semantic_tags"))
	if str(intent_class or "").strip() == "transaction_listing":
		return _dedupe(intent_tags)
	return _dedupe(capability_semantic_tags(capability_id) + intent_tags)


@dataclass(frozen=True)
class SemanticValidationOutcome:
	status: str
	contract: Any
	schema_ok: bool
	field_presence_ok: bool
	semantic_tag_ok: bool
	time_scope_match: bool
	dimension_match: bool
	errors: List[str] = field(default_factory=list)
	warnings: List[str] = field(default_factory=list)
	returned_filters: Dict[str, Any] = field(default_factory=dict)
	observed_headers: List[str] = field(default_factory=list)
	row_count: int = 0

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_semantic_validation_outcome",
			"contract_version": "1.0",
			"status": self.status,
			"schema_ok": self.schema_ok,
			"field_presence_ok": self.field_presence_ok,
			"semantic_tag_ok": self.semantic_tag_ok,
			"time_scope_match": self.time_scope_match,
			"dimension_match": self.dimension_match,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"returned_filters": dict(self.returned_filters),
			"observed_headers": list(self.observed_headers),
			"row_count": int(max(0, self.row_count)),
			"contract": self.contract.to_payload(),
		}


def validate_compiled_semantic_result(
	*,
	interaction_contract: Dict[str, Any],
	interpretation_contract: Dict[str, Any],
	compiler_contract: Dict[str, Any],
	runtime_payload: Dict[str, Any],
	normalized_family_artifact: Dict[str, Any] | None = None,
	family_validation_payload: Dict[str, Any] | None = None,
) -> SemanticValidationOutcome:
	request_id = str(interaction_contract.get("request_id") or compiler_contract.get("request_id") or "").strip()
	capability_id = str(compiler_contract.get("capability_id") or "").strip()
	selected_report = str(compiler_contract.get("selected_report") or "").strip()
	intent_class = str(interpretation_contract.get("intent_class") or "").strip()
	requested_metrics = _clean_list(compiler_contract.get("requested_metrics"))
	requested_dimensions = _clean_list(compiler_contract.get("requested_dimensions"))
	requested_time_scope = str(compiler_contract.get("requested_time_scope") or "").strip()
	completed_filters = (
		dict(compiler_contract.get("completed_filters"))
		if isinstance(compiler_contract.get("completed_filters"), dict)
		else {}
	)
	artifact_payload = (
		dict(normalized_family_artifact)
		if isinstance(normalized_family_artifact, dict)
		else {}
	)
	artifact_family_id = str(
		artifact_payload.get("family_id") or compiler_contract.get("selected_report_family") or ""
	).strip()
	artifact_filters = dict(artifact_payload.get("filters")) if isinstance(artifact_payload.get("filters"), dict) else {}
	family_validation = (
		dict(family_validation_payload)
		if isinstance(family_validation_payload, dict)
		else {}
	)
	family_validation_status = str(family_validation.get("status") or "").strip()
	family_validation_contract = (
		dict(family_validation.get("contract"))
		if isinstance(family_validation.get("contract"), dict)
		else {}
	)
	family_time_scope_match = bool(
		family_validation.get("time_scope_match")
		if "time_scope_match" in family_validation
		else family_validation_contract.get("time_scope_match")
	)
	family_artifact_governed = bool(artifact_family_id and family_validation_status == "pass")

	errors: List[str] = []
	warnings: List[str] = []

	if not bool(runtime_payload.get("ok")):
		errors.append("Runtime payload did not indicate a successful grounded execution.")
	validation_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	runtime_validation = validation_meta.get("validation") if isinstance(validation_meta.get("validation"), dict) else {}
	if str(runtime_validation.get("status") or "").strip().lower() not in {"", "pass"}:
		errors.extend(_clean_list(runtime_validation.get("errors")))

	report_tool = _report_tool(runtime_payload)
	report_name = str(_tool_args(report_tool).get("report_name") or "").strip()
	actual_filters = _tool_filters(report_tool)
	headers, rows = _headers_and_rows(report_tool)
	row_count = len(rows)

	schema_errors: List[str] = []
	if not report_tool:
		schema_errors.append("No successful report tool trace was available for semantic validation.")
	if not report_name:
		schema_errors.append("The runtime did not return a report name for semantic validation.")
	if report_name and not get_report_spec(report_name):
		schema_errors.append(f"Returned report `{report_name}` is not governed in the registry.")
	if selected_report and report_name and selected_report != report_name:
		schema_errors.append(
			f"Returned report `{report_name}` does not match the compiler-selected report `{selected_report}`."
		)
	if not headers and row_count == 0:
		schema_errors.append("Grounded result returned no governed schema and no table rows.")

	field_errors: List[str] = []
	metric_ok, metric_errors = _requested_metric_present(
		requested_metrics,
		report_name=report_name,
		headers=headers,
		rows=rows,
		actual_filters=actual_filters,
	)
	field_errors.extend(metric_errors)

	dimension_ok, dimension_errors = _requested_dimension_present(
		requested_dimensions,
		report_name=report_name,
		headers=headers,
		actual_filters=actual_filters,
	)

	expected_tags = _expected_semantic_tags(capability_id, intent_class)
	observed_tags = report_semantic_tags(report_name)
	semantic_errors: List[str] = []
	if report_name:
		report_spec = get_report_spec(report_name)
		report_capability_ids = _clean_list(report_spec.get("capability_ids"))
		if capability_id and report_capability_ids and capability_id not in report_capability_ids:
			semantic_errors.append(
				f"Returned report `{report_name}` is not governed for capability `{capability_id}`."
			)
		supported_intent_classes = report_supported_intent_classes(report_name)
		if intent_class and supported_intent_classes and intent_class not in supported_intent_classes:
			semantic_errors.append(
				f"Returned report `{report_name}` does not support intent class `{intent_class}`."
			)
		if intent_class != "transaction_listing":
			missing_capability_tags = [
				tag for tag in capability_semantic_tags(capability_id) if tag not in observed_tags
			]
			if missing_capability_tags:
				semantic_errors.append(
					f"Returned report `{report_name}` is missing capability semantic tags: {', '.join(missing_capability_tags)}."
				)

	time_scope_errors: List[str] = []
	for fieldname, expected_value in completed_filters.items():
		actual_value = actual_filters.get(fieldname)
		if str(actual_value or "").strip() != str(expected_value or "").strip():
			time_scope_errors.append(
				f"Runtime filter `{fieldname}` did not match the compiler-completed filter value."
			)
	if requested_time_scope == "as_of_today":
		report_date = str(actual_filters.get("report_date") or "").strip()
		if report_date != _today_iso():
			time_scope_errors.append(
				f"`as_of_today` requested, but grounded report_date was `{report_date or 'missing'}`."
			)

	if family_artifact_governed:
		# Once a normalized family artifact has passed deterministic family validation,
		# semantic validation should not reject on raw report-schema mismatches alone.
		if metric_errors:
			metric_errors = []
			metric_ok = True
		if time_scope_errors and (
			family_time_scope_match
			or str(artifact_filters.get("report_date") or "").strip() == _today_iso()
		):
			time_scope_errors = []
	field_errors = list(metric_errors)

	policy = semantic_validation_policy()
	zero_result_intents = set(_clean_list(policy.get("zero_result_clarify_intent_classes")))
	if row_count == 0 and intent_class in zero_result_intents:
		warnings.append(
			f"Grounded result returned zero rows for intent class `{intent_class}`, so clarification is safer than silent display."
		)

	schema_ok = not schema_errors
	field_presence_ok = not field_errors
	semantic_tag_ok = not semantic_errors
	time_scope_match = not time_scope_errors
	dimension_match = not dimension_errors

	errors.extend(schema_errors)
	errors.extend(field_errors)
	errors.extend(semantic_errors)
	errors.extend(time_scope_errors)

	decision = "pass"
	if errors:
		decision = "reject_semantically_inconsistent"
	elif warnings:
		decision = "clarify"

	contract = build_semantic_intent_validation_contract(
		request_id=request_id,
		requested_capability_id=capability_id,
		returned_report=report_name,
		expected_semantic_tags=expected_tags,
		observed_semantic_tags=observed_tags,
		time_scope_match=time_scope_match,
		dimension_match=dimension_match,
		decision=decision,
	)
	return SemanticValidationOutcome(
		status=decision,
		contract=contract,
		schema_ok=schema_ok,
		field_presence_ok=field_presence_ok and metric_ok,
		semantic_tag_ok=semantic_tag_ok,
		time_scope_match=time_scope_match,
		dimension_match=dimension_match and dimension_ok,
		errors=errors,
		warnings=warnings,
		returned_filters=actual_filters,
		observed_headers=headers,
		row_count=row_count,
	)


def run_phase4_semantic_validation_selftests() -> Dict[str, Any]:
	today = _today_iso()
	base_interaction = {"request_id": "semantic-selftest"}
	pass_interpretation = {"intent_class": "financial_summary"}
	pass_compiler = {
		"request_id": "semantic-selftest",
		"capability_id": "accounts_payable_read",
		"selected_report": "Accounts Payable Summary",
		"completed_filters": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"report_date": today,
		},
		"requested_dimensions": [],
		"requested_metrics": ["Outstanding"],
		"requested_time_scope": "as_of_today",
	}
	pass_runtime = {
		"ok": True,
		"tool_trace": [
			{
				"tool": "erp_fac-generate_report",
				"status": "ok",
				"detail_obj": {
					"report_name": "Accounts Payable Summary",
					"filters": {
						"company": "Mingalar Mobile Distribution Co., Ltd.",
						"report_date": today,
					},
				},
				"output_obj": {
					"result": {
						"columns": [
							{"fieldname": "party", "label": "Party"},
							{"fieldname": "outstanding", "label": "Outstanding Amount"},
							{"fieldname": "total_due", "label": "Total Amount Due"},
						],
						"data": [
							{
								"party": "Supplier A",
								"outstanding": 1000,
								"total_due": 1000,
							}
						],
					}
				},
			}
		],
		"agent_meta": {"validation": {"status": "pass", "errors": []}},
	}
	pass_outcome = validate_compiled_semantic_result(
		interaction_contract=base_interaction,
		interpretation_contract=pass_interpretation,
		compiler_contract=pass_compiler,
		runtime_payload=pass_runtime,
	)
	if pass_outcome.status != "pass":
		raise RuntimeError(f"Semantic validation selftest failed: expected pass, got {pass_outcome.status}.")

	reject_runtime = {
		**pass_runtime,
		"tool_trace": [
			{
				"tool": "erp_fac-generate_report",
				"status": "ok",
				"detail_obj": {
					"report_name": "Accounts Receivable Summary",
					"filters": {
						"company": "Mingalar Mobile Distribution Co., Ltd.",
						"report_date": today,
					},
				},
				"output_obj": {
					"result": {
						"columns": [
							{"fieldname": "party", "label": "Party"},
							{"fieldname": "outstanding", "label": "Outstanding Amount"},
						],
						"data": [
							{
								"party": "Customer A",
								"outstanding": 1000,
							}
						],
					}
				},
			}
		],
	}
	reject_outcome = validate_compiled_semantic_result(
		interaction_contract=base_interaction,
		interpretation_contract=pass_interpretation,
		compiler_contract=pass_compiler,
		runtime_payload=reject_runtime,
	)
	if reject_outcome.status != "reject_semantically_inconsistent":
		raise RuntimeError(
			"Semantic validation selftest failed: report-family mismatch did not reject deterministically."
		)

	clarify_interpretation = {"intent_class": "ranked_entities"}
	clarify_compiler = {
		"request_id": "semantic-selftest-clarify",
		"capability_id": "sales_read",
		"selected_report": "Sales Analytics",
		"completed_filters": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"from_date": "2026-03-01",
			"to_date": today,
			"tree_type": "Customer",
			"value_quantity": "Value",
			"doc_type": "Sales Invoice",
		},
		"requested_dimensions": ["Customer"],
		"requested_metrics": ["Value"],
		"requested_time_scope": "current_period",
	}
	clarify_runtime = {
		"ok": True,
		"tool_trace": [
			{
				"tool": "erp_fac-generate_report",
				"status": "ok",
				"detail_obj": {
					"report_name": "Sales Analytics",
					"filters": {
						"company": "Mingalar Mobile Distribution Co., Ltd.",
						"from_date": "2026-03-01",
						"to_date": today,
						"tree_type": "Customer",
						"value_quantity": "Value",
						"doc_type": "Sales Invoice",
					},
				},
				"output_obj": {
					"result": {
						"columns": [
							{"fieldname": "customer", "label": "Customer"},
							{"fieldname": "value", "label": "Value"},
						],
						"data": [],
					}
				},
			}
		],
		"agent_meta": {"validation": {"status": "pass", "errors": []}},
	}
	clarify_outcome = validate_compiled_semantic_result(
		interaction_contract=base_interaction,
		interpretation_contract=clarify_interpretation,
		compiler_contract=clarify_compiler,
		runtime_payload=clarify_runtime,
	)
	if clarify_outcome.status != "clarify":
		raise RuntimeError(
			"Semantic validation selftest failed: zero-row ranked entity result did not clarify deterministically."
		)

	return {
		"pass_case": pass_outcome.to_payload(),
		"reject_case": reject_outcome.to_payload(),
		"clarify_case": clarify_outcome.to_payload(),
	}
