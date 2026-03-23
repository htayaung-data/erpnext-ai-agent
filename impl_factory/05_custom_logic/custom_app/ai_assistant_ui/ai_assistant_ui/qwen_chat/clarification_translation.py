from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ClarificationSignalContract,
	build_clarification_signal_contract,
)
from ai_assistant_ui.qwen_chat.metadata import get_capability_spec


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(item or "").strip() for item in values if str(item or "").strip()]


_CAPABILITY_LABEL_OVERRIDES = {
	"accounts_receivable_read": "receivables (AR)",
	"accounts_payable_read": "payables (AP)",
	"financial_statement_read": "profitability or financial statements",
	"sales_read": "sales",
	"stock_read": "inventory",
	"product_performance_read": "product performance",
}


def _capability_business_label(capability_id: str) -> str:
	clean_id = _clean_text(capability_id)
	if not clean_id:
		return ""
	if clean_id in _CAPABILITY_LABEL_OVERRIDES:
		return _CAPABILITY_LABEL_OVERRIDES[clean_id]
	spec = get_capability_spec(clean_id)
	for key in ("capability_label", "label", "name"):
		value = _clean_text(spec.get(key))
		if value:
			return value
	return clean_id.replace("_", " ")


def _extract_suffix_list(reason: str, prefix: str) -> List[str]:
	text = _clean_text(reason)
	if not text.lower().startswith(prefix.lower()):
		return []
	suffix = text[len(prefix):].strip()
	return [part.strip() for part in suffix.split(",") if part.strip()]


def _human_join(values: List[str]) -> str:
	items = [value for value in values if _clean_text(value)]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} or {items[1]}"
	return f"{', '.join(items[:-1])}, or {items[-1]}"


def _group_business_options(capability_ids: List[str], raw_message: str) -> List[str]:
	options: List[str] = []
	capability_set = set(capability_ids)
	if capability_set & {"accounts_receivable_read", "accounts_payable_read"}:
		options.append("AR / AP")
	if "financial_statement_read" in capability_set:
		if "cash flow" in _clean_text(raw_message).lower():
			options.append("cash flow")
		options.append("profitability")
	if "sales_read" in capability_set:
		options.append("sales")
	if "stock_read" in capability_set:
		options.append("inventory")
	if "product_performance_read" in capability_set:
		options.append("product performance")
	for capability_id in capability_ids:
		label = _capability_business_label(capability_id)
		if label and label not in options:
			options.append(label)
	return list(dict.fromkeys(options))[:5]


def _time_scope_options(raw_message: str) -> List[str]:
	text = _clean_text(raw_message).lower()
	if "trend" in text or "monthly" in text or "weekly" in text:
		return ["last month", "this quarter", "all time"]
	return ["today", "last month", "all time"]


def _translate_compiler_reason(
	*,
	request_id: str,
	raw_message: str,
	compiler_reason: str,
) -> ClarificationSignalContract:
	reason = _clean_text(compiler_reason)
	capability_candidates = _extract_suffix_list(reason, "Ambiguous capability candidates:")
	if capability_candidates:
		options = _group_business_options(capability_candidates, raw_message)
		question = "Which area would you like me to analyze?"
		if options:
			question = f"Which area would you like me to analyze: {_human_join(options)}?"
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type="capability_ambiguity",
			user_question=question,
			suggested_options=options,
			internal_reason=reason,
			internal_details={"capability_candidates": capability_candidates},
		)

	report_candidates = _extract_suffix_list(reason, "Ambiguous governed report candidates:")
	if report_candidates:
		options = [value.replace("Statement", "").strip() if value.endswith("Statement") else value for value in report_candidates]
		question = "Which report would you like me to use?"
		if {"Profit and Loss", "Balance Sheet", "Cash Flow"} & set(options):
			question = "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?"
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type="report_ambiguity",
			user_question=question,
			suggested_options=list(dict.fromkeys(options))[:5],
			internal_reason=reason,
			internal_details={"report_candidates": report_candidates},
		)

	if "Missing or unresolved required filters:" in reason:
		missing_fields = _extract_suffix_list(reason, "Missing or unresolved required filters:")
		if set(missing_fields) & {"from_date", "to_date", "report_date"}:
			return build_clarification_signal_contract(
				request_id=request_id,
				stage="compiler",
				reason_type="time_scope_missing",
				user_question="Which period would you like me to use for this?",
				suggested_options=_time_scope_options(raw_message),
				internal_reason=reason,
				internal_details={"missing_fields": missing_fields},
			)
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type="filter_missing",
			user_question="I can help with that, but I need one more detail before I run it. Which specific scope would you like me to use?",
			suggested_options=[],
			internal_reason=reason,
			internal_details={"missing_fields": missing_fields},
		)

	if reason.startswith("No governed capability could be resolved"):
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type="capability_missing",
			user_question="Which business area would you like me to focus on: sales, AR/AP, financial statements, inventory, or product performance?",
			suggested_options=["sales", "AR / AP", "financial statements", "inventory", "product performance"],
			internal_reason=reason,
			internal_details={},
		)

	return build_clarification_signal_contract(
		request_id=request_id,
		stage="compiler",
		reason_type="generic_clarification",
		user_question="I can help with that, but I need one more detail before I proceed. Could you clarify the area or time period you want?",
		suggested_options=[],
		internal_reason=reason,
		internal_details={},
	)


def _translate_validation_reason(
	*,
	request_id: str,
	stage: str,
	message: str,
	detail: str,
) -> ClarificationSignalContract:
	text = _clean_text(detail)
	options = _time_scope_options(message) if "zero rows" in text.lower() or "time scope" in text.lower() else []
	question = "I need one more detail before I can answer this confidently."
	if options:
		question = "I couldn't find a confident grounded result for that scope. Would you like to try a different period?"
	return build_clarification_signal_contract(
		request_id=request_id,
		stage=stage,
		reason_type="validation_clarification",
		user_question=question,
		suggested_options=options,
		internal_reason=text,
		internal_details={},
	)


def translate_clarification_signal(
	*,
	request_id: str,
	raw_message: str,
	compiler_reason: str = "",
	family_detail: str = "",
	semantic_detail: str = "",
) -> ClarificationSignalContract:
	if _clean_text(compiler_reason):
		return _translate_compiler_reason(
			request_id=request_id,
			raw_message=raw_message,
			compiler_reason=compiler_reason,
		)
	if _clean_text(family_detail):
		return _translate_validation_reason(
			request_id=request_id,
			stage="family_validation",
			message=raw_message,
			detail=family_detail,
		)
	if _clean_text(semantic_detail):
		return _translate_validation_reason(
			request_id=request_id,
			stage="semantic_validation",
			message=raw_message,
			detail=semantic_detail,
		)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="unknown",
		reason_type="generic_clarification",
		user_question="I need one more detail before I continue. Could you clarify the area or time period you want?",
		suggested_options=[],
		internal_reason="",
		internal_details={},
	)
