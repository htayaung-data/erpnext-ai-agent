from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	NormalizedFamilyArtifactContract,
	build_family_validation_contract,
)


def _today_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return text.strip("_")


def _has_source_reports(artifact_contract: NormalizedFamilyArtifactContract | None) -> bool:
	return bool(
		artifact_contract is not None
		and isinstance(artifact_contract.source_reports, list)
		and any(str(item or "").strip() for item in artifact_contract.source_reports)
	)


def _statement_type_required_metrics(statement_type: str) -> List[str]:
	if statement_type == "profit_and_loss":
		return ["total_income", "total_expense", "net_profit"]
	if statement_type == "balance_sheet":
		return ["total_asset", "total_liability", "total_equity"]
	if statement_type == "cash_flow":
		return [
			"net_cash_from_operations",
			"net_cash_from_investing",
			"net_cash_from_financing",
			"net_change_in_cash",
		]
	return []


def _canonical_metric(requested_metric: str) -> str:
	key = _normalize_key(requested_metric)
	mapping = {
		"total_income": "total_income",
		"income": "total_income",
		"total_expense": "total_expense",
		"expense": "total_expense",
		"net_profit": "net_profit",
		"profit": "net_profit",
		"loss": "net_profit",
		"profit_for_the_year": "net_profit",
		"total_asset": "total_asset",
		"total_assets": "total_asset",
		"asset": "total_asset",
		"total_liability": "total_liability",
		"total_liabilities": "total_liability",
		"liability": "total_liability",
		"total_equity": "total_equity",
		"equity": "total_equity",
		"provisional_profit_loss": "provisional_profit_or_loss",
		"provisional_profit_or_loss": "provisional_profit_or_loss",
		"net_cash_from_operations": "net_cash_from_operations",
		"net_cash_from_investing": "net_cash_from_investing",
		"net_cash_from_financing": "net_cash_from_financing",
		"net_change_in_cash": "net_change_in_cash",
		"outstanding": "outstanding_total",
		"outstanding_amount": "outstanding_total",
		"outstanding_total": "outstanding_total",
		"total_due": "total_due",
		"total_amount_due": "total_due",
		"invoiced": "invoiced_total",
		"invoiced_amount": "invoiced_total",
		"paid": "paid_total",
		"paid_amount": "paid_total",
		"credit_note": "credit_note_total",
		"future_amount": "future_bucket_total",
		"future_bucket_total": "future_bucket_total",
		"current_bucket_total": "current_bucket_total",
		"current_amount": "current_bucket_total",
		"bucket_0_30": "current_bucket_total",
		"0_30": "current_bucket_total",
		"31_60": "bucket_31_60_total",
		"bucket_31_60": "bucket_31_60_total",
		"61_90": "bucket_61_90_total",
		"bucket_61_90": "bucket_61_90_total",
		"91_120": "bucket_91_120_total",
		"bucket_91_120": "bucket_91_120_total",
		"121_above": "bucket_121_above_total",
		"bucket_121_above": "bucket_121_above_total",
		"overdue": "overdue_total",
		"overdue_total": "overdue_total",
		"overdue_ratio": "overdue_ratio",
		"sales_amount": "sales_amount",
		"selling_amount": "sales_amount",
		"billed_amount": "sales_amount",
		"revenue": "sales_amount",
		"value": "sales_amount",
		"quantity": "quantity",
		"qty": "quantity",
		"delivered_quantity": "quantity",
		"period_value": "sales_amount",
		"period_quantity": "quantity",
		"gross_profit": "gross_profit",
		"gross_profit_percent": "gross_profit_percent",
		"gross_profit_percentage": "gross_profit_percent",
		"balance_qty": "balance_qty",
		"balance_value": "balance_value",
		"balance_value_mmk": "balance_value",
		"grand_total": "total_amount",
		"invoice_amount": "total_amount",
		"total_amount": "total_amount",
		"outstanding_amount": "outstanding_amount",
		"document_count": "document_count",
	}
	return mapping.get(key, "")


def _inventory_time_scope_matches(requested_time_scope: str, period: Dict[str, Any]) -> bool:
	scope = str(requested_time_scope or "").strip()
	if scope in {"as_of_today", "current_date_utc"}:
		to_date = str(period.get("to_date") or "").strip()
		return not to_date or to_date == _today_iso()
	return _time_scope_matches(scope, period)


def _time_scope_matches(requested_time_scope: str, period: Dict[str, Any]) -> bool:
	scope = str(requested_time_scope or "").strip()
	if not scope:
		return True
	from_date = str(period.get("from_date") or "").strip()
	to_date = str(period.get("to_date") or "").strip()
	today = _today_iso()
	if scope in {"as_of_today", "current_date_utc"}:
		return to_date == today
	if scope == "current_fiscal_year_to_date":
		return bool(from_date and to_date == today)
	if scope == "last_month":
		if not from_date or not to_date:
			return False
		end_date = dt.date.fromisoformat(to_date)
		first_day_current_month = _today_date().replace(day=1)
		last_day_previous_month = first_day_current_month - dt.timedelta(days=1)
		first_day_previous_month = last_day_previous_month.replace(day=1)
		return (
			from_date == first_day_previous_month.isoformat()
			and end_date.isoformat() == last_day_previous_month.isoformat()
		)
	return True


def _today_date() -> dt.date:
	return dt.datetime.now(dt.timezone.utc).date()


@dataclass(frozen=True)
class FamilyValidationOutcome:
	status: str
	contract: Any
	family_id: str
	errors: List[str] = field(default_factory=list)
	warnings: List[str] = field(default_factory=list)
	observed_metrics: List[str] = field(default_factory=list)
	time_scope_match: bool = False
	family_schema_match: bool = False

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_family_validation_outcome",
			"contract_version": "1.0",
			"status": self.status,
			"family_id": self.family_id,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"observed_metrics": list(self.observed_metrics),
			"time_scope_match": self.time_scope_match,
			"family_schema_match": self.family_schema_match,
			"contract": self.contract.to_payload() if self.contract else {},
		}


def _validate_financial_statement_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="financial_statement",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Financial statement adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="financial_statement",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	statement_type = str(dimensions.get("statement_type") or "").strip()
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and key != "statement_type" and value not in (None, "")
	]
	required_metrics = requested_metrics or _statement_type_required_metrics(statement_type)
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if statement_type == "profit_and_loss":
		missing_metrics = [metric for metric in missing_metrics if metric != "provisional_profit_or_loss"]
	if missing_metrics:
		errors.append(f"Missing normalized financial metrics: {', '.join(missing_metrics)}")

	required_sections = {
		"profit_and_loss": {"income", "expense", "summary"},
		"balance_sheet": {"assets", "liabilities", "equity", "summary"},
		"cash_flow": {"operations", "investing", "financing", "summary"},
	}.get(statement_type, set())
	missing_sections = [section for section in required_sections if section not in sections]
	if missing_sections:
		errors.append(f"Missing normalized statement sections: {', '.join(sorted(missing_sections))}")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized financial statement artifact did not preserve governed source reports.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized financial statement period did not match the requested time scope cleanly.")

	family_schema_match = bool(statement_type and not missing_sections)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="financial_statement",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="financial_statement",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_aging_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="aging",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Aging adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="aging",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	aging_type = str(dimensions.get("aging_type") or "").strip()
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and key != "aging_type" and value not in (None, "")
	]
	required_metrics = requested_metrics or [
		"outstanding_total",
		"total_due",
		"current_bucket_total",
		"overdue_total",
		"overdue_ratio",
	]
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized aging metrics: {', '.join(missing_metrics)}")

	required_sections = {"parties", "bucket_totals", "summary"}
	missing_sections = [section for section in required_sections if section not in sections]
	if missing_sections:
		errors.append(f"Missing normalized aging sections: {', '.join(sorted(missing_sections))}")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized aging artifact did not preserve governed source reports.")

	parties = sections.get("parties")
	if not isinstance(parties, list) or not parties:
		errors.append("Normalized aging artifact contains no party rows.")

	bucket_totals = sections.get("bucket_totals")
	if isinstance(bucket_totals, list):
		if len(bucket_totals) < 6:
			errors.append("Normalized aging artifact did not expose the full governed bucket set.")
	else:
		errors.append("Normalized aging artifact missing bucket total rows.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized aging period did not match the requested time scope cleanly.")

	family_schema_match = bool(aging_type and not missing_sections)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="aging",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="aging",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_ranking_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="ranking_analytics",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Ranking adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="ranking_analytics",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	primary_metric_key = str(dimensions.get("primary_metric_key") or "").strip()
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and value not in (None, "")
	]
	required_metrics = [primary_metric_key] if primary_metric_key else (requested_metrics[:1] if requested_metrics else [])
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized ranking metrics: {', '.join(missing_metrics)}")

	ranked_rows = sections.get("ranked_rows")
	if not isinstance(ranked_rows, list) or not ranked_rows:
		errors.append("Normalized ranking artifact contains no ranked rows.")
	else:
		first_row = ranked_rows[0] if isinstance(ranked_rows[0], dict) else {}
		if not str(first_row.get("entity") or "").strip():
			errors.append("Normalized ranking artifact top row is missing the ranked entity label.")
		if primary_metric_key and primary_metric_key not in first_row:
			errors.append("Normalized ranking artifact top row is missing the primary metric value.")
	if not isinstance(sections.get("summary"), list) or not sections.get("summary"):
		errors.append("Normalized ranking artifact is missing its governed summary section.")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized ranking artifact did not preserve governed source reports.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized ranking period did not match the requested time scope cleanly.")

	family_schema_match = bool(primary_metric_key and isinstance(ranked_rows, list) and ranked_rows)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="ranking_analytics",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_trend_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="trend_analytics",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Trend adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="trend_analytics",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	primary_metric_key = str(dimensions.get("primary_metric_key") or "").strip()
	time_grain = str(dimensions.get("time_grain") or "").strip()
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and value not in (None, "")
	]
	required_metrics = [primary_metric_key] if primary_metric_key else (requested_metrics[:1] if requested_metrics else [])
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized trend metrics: {', '.join(missing_metrics)}")

	period_series = sections.get("period_series")
	if not isinstance(period_series, list) or not period_series:
		errors.append("Normalized trend artifact contains no period series.")
	else:
		first_period = period_series[0] if isinstance(period_series[0], dict) else {}
		if not str(first_period.get("period_key") or "").strip():
			errors.append("Normalized trend artifact is missing period keys.")
		if "value" not in first_period:
			errors.append("Normalized trend artifact is missing period values.")

	if not time_grain:
		errors.append("Normalized trend artifact is missing governed time grain metadata.")
	if not isinstance(sections.get("summary"), list) or not sections.get("summary"):
		errors.append("Normalized trend artifact is missing its governed summary section.")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized trend artifact did not preserve governed source reports.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized trend period did not match the requested time scope cleanly.")

	family_schema_match = bool(primary_metric_key and time_grain and isinstance(period_series, list) and period_series)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="trend_analytics",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="trend_analytics",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_inventory_snapshot_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="inventory_snapshot",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Inventory snapshot adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="inventory_snapshot",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and value not in (None, "")
	]
	required_metrics = requested_metrics or ["balance_qty", "balance_value"]
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized inventory metrics: {', '.join(missing_metrics)}")

	snapshot_rows = sections.get("snapshot_rows")
	if not isinstance(snapshot_rows, list) or not snapshot_rows:
		errors.append("Normalized inventory artifact contains no snapshot rows.")

	required_sections = {"snapshot_rows", "summary"}
	missing_sections = [section for section in required_sections if section not in sections]
	if missing_sections:
		errors.append(f"Missing normalized inventory sections: {', '.join(sorted(missing_sections))}")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized inventory artifact did not preserve governed source reports.")

	if not str(dimensions.get("snapshot_dimension") or "").strip():
		errors.append("Normalized inventory artifact is missing the governed snapshot dimension.")

	time_scope_match = _inventory_time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized inventory snapshot period did not match the requested time scope cleanly.")

	family_schema_match = bool(str(dimensions.get("snapshot_dimension") or "").strip() and isinstance(snapshot_rows, list) and snapshot_rows)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="inventory_snapshot",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="inventory_snapshot",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_product_profitability_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="product_profitability",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Product profitability adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="product_profitability",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and value not in (None, "")
	]
	default_metrics = [metric for metric in ("gross_profit", "sales_amount", "quantity") if metric in observed_metrics]
	required_metrics = requested_metrics or default_metrics or observed_metrics[:1]
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized product profitability metrics: {', '.join(missing_metrics)}")

	product_rows = sections.get("product_rows")
	if not isinstance(product_rows, list) or not product_rows:
		errors.append("Normalized product profitability artifact contains no product rows.")
	else:
		first_row = product_rows[0] if isinstance(product_rows[0], dict) else {}
		if not str(first_row.get("item_name") or first_row.get("item") or first_row.get("item_code") or "").strip():
			errors.append("Normalized product profitability artifact top row is missing the product label.")

	required_sections = {"product_rows", "summary"}
	missing_sections = [section for section in required_sections if section not in sections]
	if missing_sections:
		errors.append(f"Missing normalized product profitability sections: {', '.join(sorted(missing_sections))}")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized product profitability artifact did not preserve governed source reports.")

	if not str(dimensions.get("product_dimension") or "").strip():
		errors.append("Normalized product profitability artifact is missing the governed product dimension.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match:
		warnings.append("Normalized product profitability period did not match the requested time scope cleanly.")

	family_schema_match = bool(str(dimensions.get("product_dimension") or "").strip() and isinstance(product_rows, list) and product_rows)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif not time_scope_match:
		decision = "clarify"

	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="product_profitability",
		requested_metrics=required_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="product_profitability",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def _validate_transaction_listing_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	adapter_errors: List[str],
	adapter_warnings: List[str],
) -> FamilyValidationOutcome:
	requested_metrics = [_canonical_metric(value) for value in _clean_list(compiler_contract.get("requested_metrics"))]
	requested_metrics = [value for value in requested_metrics if value]
	errors: List[str] = list(adapter_errors or [])
	warnings: List[str] = list(adapter_warnings or [])

	if artifact_contract is None:
		contract = build_family_validation_contract(
			request_id=request_id,
			family_id="transaction_listing",
			requested_metrics=requested_metrics,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
			decision="reject_family_inconsistent",
			validation_errors=errors or ["Transaction listing adapter did not produce a normalized artifact."],
			validation_warnings=warnings,
		)
		return FamilyValidationOutcome(
			status="reject_family_inconsistent",
			contract=contract,
			family_id="transaction_listing",
			errors=list(contract.validation_errors),
			warnings=warnings,
			observed_metrics=[],
			time_scope_match=False,
			family_schema_match=False,
		)

	dimensions = artifact_contract.dimensions if isinstance(artifact_contract.dimensions, dict) else {}
	metrics = artifact_contract.metrics if isinstance(artifact_contract.metrics, dict) else {}
	sections = artifact_contract.sections if isinstance(artifact_contract.sections, dict) else {}
	period = artifact_contract.period if isinstance(artifact_contract.period, dict) else {}
	rows = _clean_list([])
	transaction_rows = sections.get("transaction_rows") if isinstance(sections.get("transaction_rows"), list) else []
	observed_metrics = [
		str(key or "").strip()
		for key, value in metrics.items()
		if str(key or "").strip() and value not in (None, "")
	]
	required_metrics = requested_metrics or ["document_count", "total_amount", "outstanding_amount"]
	missing_metrics = [metric for metric in required_metrics if metric not in observed_metrics]
	if missing_metrics:
		errors.append(f"Missing normalized transaction metrics: {', '.join(missing_metrics)}")
	if not _has_source_reports(artifact_contract):
		errors.append("Normalized transaction listing artifact did not preserve governed source reports.")
	if not transaction_rows:
		errors.append("Normalized transaction listing artifact contains no document rows.")
	else:
		first_row = transaction_rows[0] if isinstance(transaction_rows[0], dict) else {}
		if not str(first_row.get("document_name") or "").strip():
			errors.append("Normalized transaction listing artifact did not preserve a document identifier.")
		if not str(first_row.get("posting_date") or "").strip():
			warnings.append("Normalized transaction listing artifact did not preserve posting dates.")

	time_scope_match = _time_scope_matches(
		str(compiler_contract.get("requested_time_scope") or "").strip(),
		period,
	)
	if not time_scope_match and str(compiler_contract.get("requested_time_scope") or "").strip():
		warnings.append("Normalized transaction listing period did not match the requested time scope cleanly.")

	family_schema_match = bool(str(dimensions.get("transaction_type") or "").strip() and transaction_rows)
	decision = "pass"
	if errors:
		decision = "reject_family_inconsistent"
	elif warnings:
		decision = "pass"
	contract = build_family_validation_contract(
		request_id=request_id,
		family_id="transaction_listing",
		requested_metrics=requested_metrics,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
		decision=decision,
		validation_errors=errors,
		validation_warnings=warnings,
	)
	return FamilyValidationOutcome(
		status=decision,
		contract=contract,
		family_id="transaction_listing",
		errors=errors,
		warnings=warnings,
		observed_metrics=observed_metrics,
		time_scope_match=time_scope_match,
		family_schema_match=family_schema_match,
	)


def validate_normalized_family_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	artifact_contract: NormalizedFamilyArtifactContract | None,
	family_id: str,
	adapter_errors: List[str] | None = None,
	adapter_warnings: List[str] | None = None,
) -> FamilyValidationOutcome | None:
	target = str(family_id or "").strip()
	if target != "financial_statement":
		if target == "aging":
			return _validate_aging_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		if target == "ranking_analytics":
			return _validate_ranking_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		if target == "trend_analytics":
			return _validate_trend_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		if target == "inventory_snapshot":
			return _validate_inventory_snapshot_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		if target == "product_profitability":
			return _validate_product_profitability_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		if target == "transaction_listing":
			return _validate_transaction_listing_artifact(
				request_id=request_id,
				compiler_contract=compiler_contract,
				artifact_contract=artifact_contract,
				adapter_errors=_clean_list(adapter_errors),
				adapter_warnings=_clean_list(adapter_warnings),
			)
		return None
	return _validate_financial_statement_artifact(
		request_id=request_id,
		compiler_contract=compiler_contract,
		artifact_contract=artifact_contract,
		adapter_errors=_clean_list(adapter_errors),
		adapter_warnings=_clean_list(adapter_warnings),
	)
