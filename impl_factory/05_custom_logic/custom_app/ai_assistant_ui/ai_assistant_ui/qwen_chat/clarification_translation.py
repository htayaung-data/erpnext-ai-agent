from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	ClarificationReasonContract,
	ClarificationSignalContract,
	build_clarification_reason_contract_from_sources,
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

_DEFAULT_TIME_SCOPE_OPTIONS = ["today", "last month", "all time"]


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


def _human_join(values: List[str]) -> str:
	items = [value for value in values if _clean_text(value)]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} or {items[1]}"
	return f"{', '.join(items[:-1])}, or {items[-1]}"


def _group_business_options(capability_ids: List[str]) -> List[str]:
	options: List[str] = []
	capability_set = set(capability_ids)
	if capability_set & {"accounts_receivable_read", "accounts_payable_read"}:
		options.append("AR / AP")
	if "financial_statement_read" in capability_set:
		options.extend(["profitability", "cash flow"])
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


def _time_scope_options(details: Dict[str, Any]) -> List[str]:
	options = _clean_list(details.get("suggested_time_scope_options"))
	return options or list(_DEFAULT_TIME_SCOPE_OPTIONS)


def _translate_compiler_signal(
	*,
	request_id: str,
	compiler_reason: str,
	compiler_reason_type: str,
	compiler_details: Dict[str, Any],
) -> ClarificationSignalContract:
	reason_type = _clean_text(compiler_reason_type)
	details = dict(compiler_details or {})
	if reason_type == "capability_ambiguity":
		options = _group_business_options(_clean_list(details.get("capability_candidates")))
		question = "Which area would you like me to analyze?"
		if options:
			question = f"Which area would you like me to analyze: {_human_join(options)}?"
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question=question,
			suggested_options=options,
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	if reason_type == "report_ambiguity":
		options = _clean_list(details.get("report_candidates"))
		question = "Which report would you like me to use?"
		if {"Profit and Loss", "Balance Sheet", "Cash Flow"} & set(options):
			question = "Which financial view would you like to see: Profit & Loss, Balance Sheet, or Cash Flow?"
		elif options:
			question = f"Which report would you like me to use: {_human_join(list(dict.fromkeys(options))[:3])}?"
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question=question,
			suggested_options=list(dict.fromkeys(options))[:5],
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	if reason_type == "time_scope_missing":
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question="Which period would you like me to use for this?",
			suggested_options=_time_scope_options(details),
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	if reason_type == "filter_missing":
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question="I can help with that, but I need one more detail before I run it. Which specific scope would you like me to use?",
			suggested_options=[],
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	if reason_type == "capability_missing":
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question="Which business area would you like me to focus on: sales, AR / AP, financial statements, inventory, or product performance?",
			suggested_options=["sales", "AR / AP", "financial statements", "inventory", "product performance"],
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	if reason_type == "request_underspecified":
		return build_clarification_signal_contract(
			request_id=request_id,
			stage="compiler",
			reason_type=reason_type,
			user_question="I can help with that, but I need one more detail before I proceed. Could you clarify the metric, scope, or period you want?",
			suggested_options=[],
			internal_reason=_clean_text(compiler_reason),
			internal_details=details,
		)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="compiler",
		reason_type=reason_type or "generic_clarification",
		user_question="I can help with that, but I need one more detail before I proceed. Could you clarify the area or time period you want?",
		suggested_options=[],
		internal_reason=_clean_text(compiler_reason),
		internal_details=details,
	)


def _translate_validation_signal(
	*,
	request_id: str,
	stage: str,
	validation_payload: Dict[str, Any],
) -> ClarificationSignalContract:
	payload = dict(validation_payload or {})
	reason_type = "validation_clarification"
	user_question = "I need one more detail before I can answer this confidently."
	suggested_options: List[str] = []
	if payload.get("time_scope_match") is False:
		reason_type = "time_scope_clarification"
		user_question = "I couldn't confirm the right grounded period for that answer. Would you like me to try a different time scope?"
		suggested_options = list(_DEFAULT_TIME_SCOPE_OPTIONS)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage=stage,
		reason_type=reason_type,
		user_question=user_question,
		suggested_options=suggested_options,
		internal_reason=_clean_text(payload.get("decision")),
		internal_details=payload,
	)


def translate_clarification_reason_contract(
	*,
	reason_contract: ClarificationReasonContract,
) -> ClarificationSignalContract:
	stage = _clean_text(reason_contract.stage)
	reason_type = _clean_text(reason_contract.reason_type)
	details = dict(reason_contract.internal_details or {})
	internal_reason = _clean_text(reason_contract.internal_reason)
	if stage == "compiler" or reason_type in {"report_ambiguity", "capability_ambiguity", "time_scope_missing", "filter_missing", "capability_missing", "request_underspecified"}:
		return _translate_compiler_signal(
			request_id=reason_contract.request_id,
			compiler_reason=internal_reason,
			compiler_reason_type=reason_type,
			compiler_details=details,
		)
	return _translate_validation_signal(
		request_id=reason_contract.request_id,
		stage=stage or "validation",
		validation_payload=details,
	)


def translate_clarification_signal(
	*,
	request_id: str,
	raw_message: str = "",
	compiler_reason: str = "",
	compiler_reason_type: str = "",
	compiler_details: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
) -> ClarificationSignalContract:
	_ = _clean_text(raw_message)
	reason_contract = build_clarification_reason_contract_from_sources(
		request_id=request_id,
		compiler_reason=compiler_reason,
		compiler_reason_type=compiler_reason_type,
		compiler_details=dict(compiler_details or {}),
		family_validation=dict(family_validation or {}) if isinstance(family_validation, dict) else None,
		semantic_validation=dict(semantic_validation or {}) if isinstance(semantic_validation, dict) else None,
	)
	if reason_contract is not None:
		return translate_clarification_reason_contract(reason_contract=reason_contract)
	return build_clarification_signal_contract(
		request_id=request_id,
		stage="unknown",
		reason_type="generic_clarification",
		user_question="I need one more detail before I continue. Could you clarify the area or time period you want?",
		suggested_options=[],
		internal_reason="",
		internal_details={},
	)
