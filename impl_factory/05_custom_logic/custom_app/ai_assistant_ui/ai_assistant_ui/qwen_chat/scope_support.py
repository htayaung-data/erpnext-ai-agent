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
	requested_modes = {
		str(mode_value or "").strip()
		for mode_value in (getattr(followup_resolution, "requested_modes", []) or [])
		if str(mode_value or "").strip()
	}
	if mode == "grounded_follow_up":
		return "detail_followup" in requested_modes
	if mode not in {"local_grounded_transform", "capability_requery"}:
		return False
	if not requested_modes:
		return False
	if mode == "local_grounded_transform" and requested_modes.issubset(
		{"presentation_transform", "table_presentation", "bullet_presentation"}
	):
		return True
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


def reasoning_activation_supersedes_followup_refinement(
	*,
	reasoning_semantic_result: Any,
	followup_resolution: Dict[str, Any] | Any,
	artifact_level_context_requested: bool = False,
) -> bool:
	if reasoning_semantic_result is None:
		return False
	if str(getattr(reasoning_semantic_result, "status", "") or "").strip() != "accepted":
		return False
	intent = getattr(reasoning_semantic_result, "intent", None)
	reasoning_type = str(getattr(intent, "reasoning_type", "") or "").strip()
	if reasoning_type not in {"interpretation", "explanation", "recommendation"}:
		return False
	if isinstance(followup_resolution, dict):
		mode = str(followup_resolution.get("mode") or "").strip()
		requested_modes_source = followup_resolution.get("requested_modes") or []
	else:
		mode = str(getattr(followup_resolution, "mode", "") or "").strip()
		requested_modes_source = getattr(followup_resolution, "requested_modes", []) or []
	requested_modes = {
		str(mode_value or "").strip()
		for mode_value in requested_modes_source
		if str(mode_value or "").strip()
	}
	if mode == "capability_requery":
		if "detail_followup" in requested_modes:
			return False
		return True
	if mode == "grounded_follow_up":
		return bool(artifact_level_context_requested and "detail_followup" in requested_modes)
	if mode == "new_query":
		return bool(artifact_level_context_requested)
	if mode != "capability_requery":
		return False
	return False


def local_presentation_refinement_should_preserve_semantic_intent(
	*,
	artifact_local_projection_followup_requested: bool,
	semantic_intent: Any,
) -> bool:
	if not bool(artifact_local_projection_followup_requested) or semantic_intent is None:
		return False
	requested_modes = {
		str(mode_value or "").strip()
		for mode_value in (getattr(semantic_intent, "requested_modes", []) or [])
		if str(mode_value or "").strip()
	}
	return bool(requested_modes) and requested_modes.issubset(
		{"presentation_transform", "table_presentation", "bullet_presentation"}
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
			"I can help with financial statements, AR / AP, sales, inventory, product performance, invoices, and ERP drilldowns.\n\n"
			"This is a valid finance question, but this exact finance area is not yet covered by the assistant."
		)
	if primary_domain == "hr":
		return (
			"I can help with finance, sales, inventory, product performance, invoices, and ERP drilldowns.\n\n"
			"I don't have HR or headcount coverage yet, so I can't answer staff-count questions confidently from ERP data in this assistant."
		)
	return (
		"I can help with finance, sales, inventory, product performance, invoices, and ERP drilldowns.\n\n"
		"This question falls outside the assistant's current ERP coverage, so I can't answer it confidently from ERP data yet."
	)
