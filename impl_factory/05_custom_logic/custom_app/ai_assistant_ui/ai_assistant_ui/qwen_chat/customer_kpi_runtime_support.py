from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	class _FallbackDB:
		def exists(self, *args, **kwargs):
			return False

	class _FallbackFrappe:
		db = _FallbackDB()

		def get_all(self, *args, **kwargs):
			return []

	frappe = _FallbackFrappe()  # type: ignore

from ai_assistant_ui.qwen_chat.business_threshold_state import evaluate_business_threshold
from ai_assistant_ui.qwen_chat.customer_lifecycle_support import get_customer_lifecycle_snapshot
from ai_assistant_ui.qwen_chat.defaults_repository import single_company_name
from ai_assistant_ui.qwen_chat.family_adapters import (
	_report_result,
	_report_rows,
	_report_tool,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _coerce_date(value: Any) -> dt.date | None:
	if isinstance(value, dt.datetime):
		return value.date()
	if isinstance(value, dt.date):
		return value
	text = _clean_text(value)
	if not text:
		return None
	text = text[:10]
	try:
		return dt.date.fromisoformat(text)
	except Exception:
		return None


def _iso_date(value: Any) -> str:
	date_value = _coerce_date(value)
	return date_value.isoformat() if date_value else ""


def current_date_iso() -> str:
	return dt.datetime.now(dt.timezone.utc).date().isoformat()


def resolve_company_name(company: str) -> str:
	company_name = _clean_text(company) or _clean_text(single_company_name())
	if company_name:
		return company_name
	try:
		candidates = frappe.get_all("Company", pluck="name")
		if isinstance(candidates, list) and candidates:
			return _clean_text(candidates[0])
	except Exception:
		return ""
	return ""


def match_party_row(row: Dict[str, Any], entity_name: str, entity_label: str) -> bool:
	targets = {_normalize_text(entity_name), _normalize_text(entity_label)}
	for field in ("party", "customer", "party_name", "customer_name"):
		value = _normalize_text(row.get(field))
		if value and value in targets:
			return True
	return False


def _contains_phrase(text: str, phrase: str) -> bool:
	value = _normalize_text(text)
	target = _normalize_text(phrase)
	if not value or not target:
		return False
	pattern = r"(^|[^a-z0-9])" + re.escape(target) + r"([^a-z0-9]|$)"
	return bool(re.search(pattern, value))


def _text_tokens(value: Any) -> List[str]:
	text = re.sub(r"[^a-z0-9]+", " ", _normalize_text(value))
	return [token for token in text.split() if token]


def _customer_alias_match(
	*,
	message: str,
	alias: str,
) -> Dict[str, Any]:
	if _contains_phrase(message, alias):
		return {
			"match_mode": "exact_phrase",
			"confidence": 1.0,
			"overlap_count": len(_text_tokens(alias)),
		}
	message_tokens = set(_text_tokens(message))
	alias_tokens = _text_tokens(alias)
	if len(alias_tokens) < 2:
		return {}
	overlap_count = len(message_tokens.intersection(alias_tokens))
	overlap_ratio = float(overlap_count) / float(len(alias_tokens) or 1)
	min_overlap = 2 if len(alias_tokens) <= 3 else max(3, len(alias_tokens) - 1)
	if overlap_count < min_overlap or overlap_ratio < 0.8:
		return {}
	return {
		"match_mode": "token_overlap",
		"confidence": overlap_ratio,
		"overlap_count": overlap_count,
	}


def _customer_master_rows() -> List[Dict[str, Any]]:
	rows = frappe.get_all(
		"Customer",
		fields=[
			"name",
			"customer_name",
			"creation",
			"default_price_list",
			"payment_terms",
			"customer_group",
			"territory",
			"disabled",
			"is_frozen",
		],
		limit_page_length=5000,
		order_by="creation asc, modified asc",
	)
	return [dict(row or {}) for row in (rows or []) if isinstance(row, dict)]


def _customer_aliases(row: Dict[str, Any]) -> List[str]:
	values = [
		_clean_text(row.get("name")),
		_clean_text(row.get("customer_name")),
	]
	seen: set[str] = set()
	aliases: List[str] = []
	for value in values:
		normalized = _normalize_text(value)
		if not normalized or normalized in seen:
			continue
		seen.add(normalized)
		aliases.append(value)
	return aliases


def _best_customer_match_from_message(message: str) -> Dict[str, Any]:
	best_exact_row: Dict[str, Any] = {}
	best_exact_alias = ""
	best_exact_score = -1
	best_fuzzy_row: Dict[str, Any] = {}
	best_fuzzy_alias = ""
	best_fuzzy_confidence = 0.0
	second_fuzzy_confidence = 0.0
	best_fuzzy_overlap = 0
	best_fuzzy_alias_length = 0
	for row in _customer_master_rows():
		for alias in _customer_aliases(row):
			match = _customer_alias_match(message=message, alias=alias)
			match_mode = _clean_text(match.get("match_mode"))
			if not match_mode:
				continue
			alias_token_count = len(_text_tokens(alias))
			if match_mode == "exact_phrase":
				score = len(_normalize_text(alias))
				if score > best_exact_score:
					best_exact_row = dict(row or {})
					best_exact_alias = alias
					best_exact_score = score
				continue
			confidence = float(match.get("confidence") or 0.0)
			overlap_count = int(match.get("overlap_count") or 0)
			is_better = (
				confidence > best_fuzzy_confidence
				or (
					confidence == best_fuzzy_confidence
					and overlap_count > best_fuzzy_overlap
				)
				or (
					confidence == best_fuzzy_confidence
					and overlap_count == best_fuzzy_overlap
					and alias_token_count > best_fuzzy_alias_length
				)
			)
			if is_better:
				second_fuzzy_confidence = best_fuzzy_confidence
				best_fuzzy_row = dict(row or {})
				best_fuzzy_alias = alias
				best_fuzzy_confidence = confidence
				best_fuzzy_overlap = overlap_count
				best_fuzzy_alias_length = alias_token_count
			elif confidence > second_fuzzy_confidence:
				second_fuzzy_confidence = confidence
	if best_exact_row:
		return {
			"row": best_exact_row,
			"matched_alias": best_exact_alias,
			"match_mode": "exact_phrase",
			"confidence": 1.0,
		}
	if best_fuzzy_row and best_fuzzy_confidence >= 0.8 and (best_fuzzy_confidence - second_fuzzy_confidence) >= 0.05:
		return {
			"row": best_fuzzy_row,
			"matched_alias": best_fuzzy_alias,
			"match_mode": "token_overlap",
			"confidence": best_fuzzy_confidence,
		}
	return {
		"row": {},
		"matched_alias": "",
		"match_mode": "",
		"confidence": 0.0,
	}


def resolve_customer_scope_from_message(message: str) -> Dict[str, Any]:
	match = _best_customer_match_from_message(message)
	row = dict(match.get("row") or {}) if isinstance(match.get("row"), dict) else {}
	customer_key = _clean_text(row.get("name"))
	if not customer_key:
		return {}
	customer_label = _clean_text(row.get("customer_name")) or customer_key
	return {
		"customer": customer_key,
		"customer_name": customer_label,
		"entity_name": customer_key,
		"entity_label": customer_label,
		"matched_alias": _clean_text(match.get("matched_alias")),
		"matched_by": _clean_text(match.get("match_mode")),
		"match_confidence": float(match.get("confidence") or 0.0),
		"has_customer_scope": True,
	}


def get_customer_receivable_snapshot(
	customer_name: str,
	*,
	customer_label: str = "",
	company: str = "",
	as_of_date: str = "",
) -> Dict[str, Any]:
	customer_key = _clean_text(customer_name)
	entity_label = _clean_text(customer_label) or customer_key
	company_name = resolve_company_name(company)
	report_date = _clean_text(as_of_date) or current_date_iso()
	if not customer_key or not company_name or not report_date:
		return {}
	runtime_payload = execute_governed_report(
		report_name="Accounts Receivable Summary",
		filters={"company": company_name, "report_date": report_date},
		user="Administrator",
		mode="entity_detail",
		target_limit=0,
	)
	report_tool = _report_tool(runtime_payload if isinstance(runtime_payload, dict) else {})
	result = _report_result(report_tool)
	rows = _report_rows(result)
	target_row = next(
		(row for row in rows if isinstance(row, dict) and match_party_row(row, customer_key, entity_label)),
		{},
	)
	if not target_row:
		return {}
	outstanding = _numeric(target_row.get("outstanding"))
	total_due = _numeric(target_row.get("total_due"))
	future_amount = _numeric(target_row.get("future_amount"))
	range1 = _numeric(target_row.get("range1"))
	range2 = _numeric(target_row.get("range2"))
	range3 = _numeric(target_row.get("range3"))
	range4 = _numeric(target_row.get("range4"))
	range5 = _numeric(target_row.get("range5"))
	overdue_total = range2 + range3 + range4 + range5
	overdue_ratio = (overdue_total / outstanding) if outstanding > 0 else 0.0
	return {
		"report_date": report_date,
		"company": company_name,
		"currency": _clean_text(target_row.get("currency")),
		"summary": [
			("Outstanding (MMK)", f"{outstanding:,.2f}".rstrip("0").rstrip(".")),
			("Total Due (MMK)", f"{total_due:,.2f}".rstrip("0").rstrip(".")),
			("Overdue Total (MMK)", f"{overdue_total:,.2f}".rstrip("0").rstrip(".")),
			("Overdue Ratio", f"{overdue_ratio * 100:.1f}%"),
		],
		"bucket_rows": [
			("<0", future_amount),
			("0-30", range1),
			("31-60", range2),
			("61-90", range3),
			("91-120", range4),
			("121-Above", range5),
		],
		"metrics": {
			"outstanding_total": outstanding,
			"total_due": total_due,
			"future_bucket_total": future_amount,
			"current_bucket_total": range1,
			"bucket_31_60_total": range2,
			"bucket_61_90_total": range3,
			"bucket_91_120_total": range4,
			"bucket_121_above_total": range5,
			"overdue_total": overdue_total,
			"overdue_ratio": overdue_ratio,
		},
	}


def get_customer_credit_policy_snapshot(
	customer_name: str,
	*,
	company: str = "",
	outstanding_total: float = 0.0,
) -> Dict[str, Any]:
	customer_key = _clean_text(customer_name)
	company_name = resolve_company_name(company)
	filters: Dict[str, Any] = {"parent": customer_key}
	if company_name:
		filters["company"] = company_name
	rows = frappe.get_all(
		"Customer Credit Limit",
		fields=["company", "credit_limit", "bypass_credit_limit_check"],
		filters=filters,
		limit_page_length=20,
	)
	if not rows and company_name:
		rows = frappe.get_all(
			"Customer Credit Limit",
			fields=["company", "credit_limit", "bypass_credit_limit_check"],
			filters={"parent": customer_key},
			limit_page_length=20,
		)
	target_row = next(
		(
			row
			for row in (rows or [])
			if isinstance(row, dict) and _clean_text(row.get("company")) == company_name
		),
		(rows[0] if isinstance(rows, list) and rows else {}),
	)
	if not isinstance(target_row, dict):
		target_row = {}
	credit_limit = _numeric(target_row.get("credit_limit"))
	configured = credit_limit > 0
	outstanding_for_limit = max(_numeric(outstanding_total), 0.0)
	available_credit = max(credit_limit - outstanding_for_limit, 0.0) if configured else 0.0
	exceeded_amount = max(outstanding_for_limit - credit_limit, 0.0) if configured else 0.0
	utilization_ratio = (outstanding_for_limit / credit_limit) if configured else 0.0
	return {
		"company": _clean_text(target_row.get("company")) or company_name,
		"has_row": bool(target_row),
		"configured": configured,
		"credit_limit": credit_limit,
		"available_credit": available_credit,
		"exceeded_amount": exceeded_amount,
		"utilization_ratio": utilization_ratio,
		"exceeded": bool(configured and exceeded_amount > 0),
		"bypass_credit_limit_check": bool(int(target_row.get("bypass_credit_limit_check") or 0)),
	}


def get_customer_kpi_scalar_snapshot(
	customer_name: str,
	*,
	customer_label: str = "",
	company: str = "",
	as_of_date: str = "",
) -> Dict[str, Any]:
	customer_key = _clean_text(customer_name)
	entity_label = _clean_text(customer_label) or customer_key
	report_date = _clean_text(as_of_date) or current_date_iso()
	receivable_snapshot = get_customer_receivable_snapshot(
		customer_key,
		customer_label=entity_label,
		company=company,
		as_of_date=report_date,
	)
	receivable_metrics = (
		dict(receivable_snapshot.get("metrics") or {})
		if isinstance(receivable_snapshot.get("metrics"), dict)
		else {}
	)
	policy_snapshot = get_customer_credit_policy_snapshot(
		customer_key,
		company=company,
		outstanding_total=_numeric(receivable_metrics.get("outstanding_total")),
	)
	lifecycle_snapshot = get_customer_lifecycle_snapshot(
		customer_key,
		company=resolve_company_name(company),
		as_of_date=report_date,
	)
	credit_threshold = {}
	if bool(policy_snapshot.get("configured")):
		credit_threshold = evaluate_business_threshold(
			"customer_credit_utilization_policy_bands",
			observed_value=policy_snapshot.get("utilization_ratio"),
			company_name=resolve_company_name(company),
		).to_payload()
	return {
		"customer": customer_key,
		"customer_label": entity_label,
		"company": resolve_company_name(company),
		"as_of_date": report_date,
		"receivable_snapshot": receivable_snapshot,
		"policy_snapshot": policy_snapshot,
		"lifecycle_snapshot": lifecycle_snapshot,
		"credit_threshold_state": credit_threshold,
	}


def list_customer_kpi_rows(
	*,
	company: str = "",
	as_of_date: str = "",
) -> List[Dict[str, Any]]:
	company_name = resolve_company_name(company)
	report_date = _clean_text(as_of_date) or current_date_iso()
	if not company_name:
		return []
	runtime_payload = execute_governed_report(
		report_name="Accounts Receivable Summary",
		filters={"company": company_name, "report_date": report_date},
		user="Administrator",
		mode="entity_detail",
		target_limit=0,
	)
	report_tool = _report_tool(runtime_payload if isinstance(runtime_payload, dict) else {})
	result = _report_result(report_tool)
	rows = _report_rows(result)
	customer_rows = _customer_master_rows()
	alias_index: Dict[str, Dict[str, Any]] = {}
	for row in customer_rows:
		for alias in _customer_aliases(row):
			alias_index[_normalize_text(alias)] = dict(row or {})
	credit_limit_rows = frappe.get_all(
		"Customer Credit Limit",
		fields=["parent", "company", "credit_limit", "bypass_credit_limit_check"],
		filters={"company": company_name},
		limit_page_length=5000,
	)
	credit_limit_by_customer = {
		_clean_text(row.get("parent")): dict(row or {})
		for row in (credit_limit_rows or [])
		if isinstance(row, dict) and _clean_text(row.get("parent"))
	}
	kpi_rows: List[Dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		customer_ref = _clean_text(row.get("party") or row.get("customer") or row.get("party_name") or row.get("customer_name"))
		if not customer_ref:
			continue
		master_row = alias_index.get(_normalize_text(customer_ref), {})
		customer_key = _clean_text(master_row.get("name")) or (customer_ref if frappe.db.exists("Customer", customer_ref) else "")
		customer_label = _clean_text(master_row.get("customer_name")) or customer_ref
		if not customer_key:
			continue
		outstanding = _numeric(row.get("outstanding"))
		total_due = _numeric(row.get("total_due"))
		future_amount = _numeric(row.get("future_amount"))
		range1 = _numeric(row.get("range1"))
		range2 = _numeric(row.get("range2"))
		range3 = _numeric(row.get("range3"))
		range4 = _numeric(row.get("range4"))
		range5 = _numeric(row.get("range5"))
		overdue_total = range2 + range3 + range4 + range5
		overdue_ratio = (overdue_total / outstanding) if outstanding > 0 else 0.0
		policy_row = dict(credit_limit_by_customer.get(customer_key) or {})
		credit_limit = _numeric(policy_row.get("credit_limit"))
		credit_limit_configured = credit_limit > 0
		outstanding_for_limit = max(outstanding, 0.0)
		credit_limit_available = max(credit_limit - outstanding_for_limit, 0.0) if credit_limit_configured else 0.0
		credit_limit_excess = max(outstanding_for_limit - credit_limit, 0.0) if credit_limit_configured else 0.0
		credit_limit_utilization_ratio = (outstanding_for_limit / credit_limit) if credit_limit_configured else 0.0
		credit_threshold = {}
		if credit_limit_configured:
			credit_threshold = evaluate_business_threshold(
				"customer_credit_utilization_policy_bands",
				observed_value=credit_limit_utilization_ratio,
				company_name=company_name,
			).to_payload()
		kpi_rows.append(
			{
				"customer": customer_key,
				"customer_label": customer_label,
				"company": company_name,
				"as_of_date": report_date,
				"outstanding_total": outstanding,
				"total_due": total_due,
				"future_bucket_total": future_amount,
				"current_bucket_total": range1,
				"bucket_31_60_total": range2,
				"bucket_61_90_total": range3,
				"bucket_91_120_total": range4,
				"bucket_121_above_total": range5,
				"overdue_total": overdue_total,
				"overdue_ratio": overdue_ratio,
				"credit_limit": credit_limit,
				"credit_limit_configured": credit_limit_configured,
				"credit_limit_available": credit_limit_available,
				"credit_limit_excess": credit_limit_excess,
				"credit_limit_utilization_ratio": credit_limit_utilization_ratio,
				"credit_limit_exceeded": bool(credit_limit_configured and credit_limit_excess > 0),
				"credit_limit_bypass_sales_order": bool(int(policy_row.get("bypass_credit_limit_check") or 0)),
				"credit_threshold_state": credit_threshold,
			}
		)
	return kpi_rows
