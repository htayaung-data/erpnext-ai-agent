from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.contracts import normalize_scope_decision_input


def reasoning_supersedes_contradictory_presentation_followup(
	*,
	semantic_intent: Any,
	reasoning_semantic_result: Any,
) -> bool:
	if semantic_intent is None:
		return False
	if str(getattr(reasoning_semantic_result, "status", "") or "").strip() != "accepted":
		return False
	reasoning_type = str(getattr(getattr(reasoning_semantic_result, "intent", None), "reasoning_type", "") or "").strip()
	if reasoning_type not in {"interpretation", "explanation", "recommendation", "continuation_detail"}:
		return False
	requested_modes = {
		str(mode or "").strip()
		for mode in (getattr(semantic_intent, "requested_modes", []) or [])
		if str(mode or "").strip()
	}
	if not requested_modes:
		return False
	if any(mode not in {"presentation_transform", "table_presentation", "bullet_presentation"} for mode in requested_modes):
		return False
	return bool(
		str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
		or str(getattr(semantic_intent, "requested_time_scope", "") or "").strip()
		or str(getattr(semantic_intent, "target_metric", "") or "").strip()
		or list(getattr(semantic_intent, "requested_columns", []) or [])
		or str(getattr(semantic_intent, "target_dimension", "") or "").strip()
		or int(getattr(semantic_intent, "target_limit", 0) or 0)
		or str(getattr(semantic_intent, "sort_direction", "") or "").strip()
	)


def reasoning_scope_suppression_allowed(decision: Dict[str, Any] | Any) -> bool:
	normalized_decision = normalize_scope_decision_input(decision)
	if not bool(normalized_decision.force_new_query) or bool(normalized_decision.out_of_scope):
		return False
	reason_text = str(normalized_decision.reason or "").strip().lower()
	if (
		"self-contained" in reason_text
		or "different governed business area" in reason_text
		or "fresh governed erp question" in reason_text
	):
		return False
	requested_domains = {
		str(value or "").strip()
		for value in (normalized_decision.requested_domains or [])
		if str(value or "").strip()
	}
	context_domains = {
		str(value or "").strip()
		for value in (normalized_decision.context_domains or [])
		if str(value or "").strip()
	}
	if not requested_domains:
		return True
	if not context_domains:
		return False
	return requested_domains.issubset(context_domains)


def reasoning_preempted_by_followup_refinement(followup_resolution: Dict[str, Any] | Any) -> bool:
	mode = str(getattr(followup_resolution, "mode", "") or "").strip()
	if mode == "new_query":
		return bool(getattr(followup_resolution, "self_contained", False))
	if mode not in {"local_grounded_transform", "capability_requery"}:
		return False
	requested_modes = {
		str(mode_value or "").strip()
		for mode_value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(mode_value or "").strip()
	}
	if not requested_modes:
		return False
	return bool(
		{
			"sort_or_limit",
			"metric_refinement",
			"column_refinement",
			"time_scope_restatement",
			"dimension_breakdown",
			"grouping_change",
			"filter_refinement",
		}.intersection(requested_modes)
	)


def context_isolation_payload(*, request_id: str, decision: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"type": "qwen_context_isolation_decision",
		"request_id": str(request_id or "").strip(),
		"force_new_query": bool(decision.get("force_new_query")),
		"out_of_scope": bool(decision.get("out_of_scope")),
		"reason": str(decision.get("reason") or "").strip(),
		"requested_domains": list(decision.get("requested_domains") or []),
		"context_domains": list(decision.get("context_domains") or []),
		"primary_domain": str(decision.get("primary_domain") or "").strip(),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def out_of_scope_answer(message: str, decision: Dict[str, Any] | Any) -> str:
	normalized_decision = normalize_scope_decision_input(decision)
	primary_domain = str(normalized_decision.primary_domain or "").strip()
	if primary_domain == "finance":
		return (
			"I can help with governed financial statements, AR / AP, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
			"This is a valid finance question, but this exact finance area is not yet covered as a governed Qwen ERP answer path."
		)
	if primary_domain == "hr":
		return (
			"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
			"I don't have governed HR or headcount coverage yet, so I can't answer staff-count questions confidently from ERP data in this assistant."
		)
	return (
		"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
		"This question falls outside the current governed Qwen ERP coverage, so I can't answer it confidently from ERP data yet."
	)
