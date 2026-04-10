from __future__ import annotations

import datetime as dt
import json
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Tuple

import frappe

from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.audit_support import (
	audit_latency_summary as _audit_latency_summary_helper,
	case_latency_budget_assessment as _case_latency_budget_assessment_helper,
	family_latency_budget_payload as _family_latency_budget_payload_helper,
	family_latency_budget_summary as _family_latency_budget_summary_helper,
	family_metrics_summary as _family_metrics_summary_helper,
)
from ai_assistant_ui.qwen_chat.boundary_support import (
	append_artifact_boundary_observability as _append_artifact_boundary_observability_helper,
	append_knowledge_boundary_observability as _append_knowledge_boundary_observability_helper,
	artifact_evidence_concepts as _artifact_evidence_concepts_helper,
	artifact_enrichment_boundary_answer as _artifact_enrichment_boundary_answer_helper,
	build_grounded_artifact_direct_evidence_rendered_payload as _build_grounded_artifact_direct_evidence_rendered_payload_helper,
	grounded_artifact_direct_evidence_answer as _grounded_artifact_direct_evidence_answer_helper,
	grounded_artifact_evidence_boundary_answer as _grounded_artifact_evidence_boundary_answer_helper,
	knowledge_boundary_event_level as _knowledge_boundary_event_level_helper,
)
from ai_assistant_ui.qwen_chat.boundary_contract_support import (
	append_enrichment_recovery_contract as _append_enrichment_recovery_contract_helper,
	append_grounded_evidence_recovery_contract as _append_grounded_evidence_recovery_contract_helper,
	append_knowledge_boundary_contract as _append_knowledge_boundary_contract_helper,
)
from ai_assistant_ui.qwen_chat.assistant_formatting import (
	ensure_table_from_grounded_context as _ensure_table_from_grounded_context,
	extract_markdown_tables as _extract_markdown_tables,
	is_markdown_table_separator as _is_markdown_table_separator,
	normalize_markdown_units as _normalize_markdown_units,
	split_markdown_table_cells as _split_markdown_table_cells,
	transform_markdown_to_million as _transform_markdown_to_million,
	assistant_text_payload as _assistant_text_payload_helper,
)
from ai_assistant_ui.qwen_chat.capability_adapters import render_local_followup
from ai_assistant_ui.qwen_chat.clarification_state import get_clarification_state
from ai_assistant_ui.qwen_chat.clarification_translation import (
	translate_clarification_signal,
)
from ai_assistant_ui.qwen_chat.clarification_resolution import (
	clarification_continuation_lane,
	clarification_resolved_continuation_message,
	clarification_state_after_unresolved_attempt,
	clear_pending_clarification_signal,
	governed_fallback_option,
	latest_assistant_turn_was_clarification_fallback_stop,
	latest_pending_clarification_signal,
	looks_like_short_acknowledgement,
	pending_clarification_empty_ack_answer,
	pending_clarification_fallback_stop_answer,
	pending_clarification_meta_answer,
	pending_clarification_repeat_answer,
	resolve_pending_clarification_response,
	store_pending_clarification_signal,
)
from ai_assistant_ui.qwen_chat.compiled_support import (
	append_compiled_attempt_artifacts as _append_compiled_attempt_artifacts_helper,
	handle_compiled_first_turn_result as _handle_compiled_first_turn_result_helper,
	compiled_decision_message as _compiled_decision_message_helper,
	compiled_clarification_reason_contract as _compiled_clarification_reason_contract,
	compiled_rollout_fallback_eligible as _compiled_rollout_fallback_eligible,
	compiled_rollout_fallback_payload as _compiled_rollout_fallback_payload,
	compiled_rollout_fallback_reason as _compiled_rollout_fallback_reason,
)
from ai_assistant_ui.qwen_chat.continuation_support import (
	artifact_rank_row_count as _artifact_rank_row_count_helper,
	authoritative_continuation_resolution as _authoritative_continuation_resolution_helper,
	requery_resolution_for_unsupported_local_columns as _requery_resolution_for_unsupported_local_columns_helper,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_artifact_enrichment_recovery_contract,
	build_conversational_repair_intent_contract,
	build_known_unsupported_scope_decision_input,
	coerce_followup_resolution_from_scope_decision,
	build_artifact_continuation_contract,
	build_audit_envelope,
	build_execution_path,
	build_followup_resolution_contract,
	build_followup_resolution,
	build_governed_scope_decision_contract,
	build_grounded_turn_context,
	build_interaction_contract,
	build_response_policy_contract,
	build_scope_decision_input,
	governed_scope_decision_is_out_of_scope,
	governed_scope_decision_public_decision,
	governed_scope_decision_requires_fresh_query,
	normalize_scope_decision_input,
)
from ai_assistant_ui.qwen_chat.context.session_context import (
	append_message as _session_append_message,
	append_tool_payload as _session_append_tool_payload,
	safe_json_dumps as _session_safe_json_dumps,
	save_session as _session_save,
)
from ai_assistant_ui.qwen_chat.context.message_history import (
	parse_payload as _history_parse_payload,
	positions_to_skip_for_runtime_context as _history_positions_to_skip_for_runtime_context,
	recent_messages as _history_recent_messages,
	recent_messages_for_grounded_source as _history_recent_messages_for_grounded_source,
	latest_assistant_payload as _history_latest_assistant_payload,
	latest_display_preferences as _history_latest_display_preferences,
	tool_payloads as _history_tool_payloads,
	visible_message_text as _history_visible_message_text,
)
from ai_assistant_ui.qwen_chat.context.grounded_context import (
	artifact_compatible_with_grounded_turn as _grounded_artifact_compatible_with_grounded_turn,
	grounded_turn_source_request_id as _grounded_turn_source_request_id_helper,
	latest_grounded_assistant_context as _grounded_latest_grounded_assistant_context,
	latest_grounded_turn_contract as _grounded_latest_grounded_turn_contract,
	latest_normalized_family_artifact as _grounded_latest_normalized_family_artifact,
	latest_qwen_trace_payload as _grounded_latest_qwen_trace_payload,
	latest_reasoning_contract as _grounded_latest_reasoning_contract,
	latest_recovery_contract as _grounded_latest_recovery_contract,
	source_compatible_reasoning_contract as _grounded_source_compatible_reasoning_contract,
)
from ai_assistant_ui.qwen_chat.entity_detail import (
	detect_entity_drilldown_request,
	execute_entity_drilldown,
)
from ai_assistant_ui.qwen_chat.entity_followup_support import (
	try_entity_detail_followup as _try_entity_detail_followup_helper,
)
from ai_assistant_ui.qwen_chat.family_followup import (
	render_local_family_followup,
	supports_local_family_followup,
)
from ai_assistant_ui.qwen_chat.family_tool_surface import build_family_tool_surface_for_message
from ai_assistant_ui.qwen_chat.followup_interpreter import (
	assess_context_isolation,
)
from ai_assistant_ui.qwen_chat.knowledge_boundary import (
	render_knowledge_boundary_answer,
)
from ai_assistant_ui.qwen_chat.lanes.clarification_lane import (
	build_pending_clarification_frontdoor_skip,
	handle_pending_clarification_turn,
)
from ai_assistant_ui.qwen_chat.lanes.artifact_boundary_lane import handle_artifact_boundary_turn
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import (
	evaluate_frontdoor_lane,
	handle_frontdoor_turn,
)
from ai_assistant_ui.qwen_chat.lanes.compiled_query_lane import handle_compiled_query_turn
from ai_assistant_ui.qwen_chat.lanes.entity_drilldown_lane import handle_entity_drilldown_turn
from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import handle_legacy_runtime_turn
from ai_assistant_ui.qwen_chat.lanes.reasoning_lane import handle_reasoning_turn
from ai_assistant_ui.qwen_chat.lanes.repair_lane import handle_repair_turn
from ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane import handle_runtime_gate_turn
from ai_assistant_ui.qwen_chat.local_followup_support import (
	apply_local_followup_transforms as _apply_local_followup_transforms_helper,
	maybe_apply_local_followup_narrative as _maybe_apply_local_followup_narrative_helper,
	try_local_followup_transform as _try_local_followup_transform_helper,
)
from ai_assistant_ui.qwen_chat.observability import (
	record_phase55_observability_event,
	record_phase6_observability_event,
	record_phase6_performance_metric,
)
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message
from ai_assistant_ui.qwen_chat.reasoning_activation import (
	build_reasoning_activation_contract,
	run_phase6a_recommendation_policy_probe,
)
from ai_assistant_ui.qwen_chat.reasoning_execution import (
	build_reasoning_boundary_answer,
	execute_erp_business_reasoning,
	run_phase6d_reasoning_continuation_guardrail_smoke,
)
from ai_assistant_ui.qwen_chat.recovery_support import (
	build_recovery_governed_query_message as _build_recovery_governed_query_message_helper,
	build_recovery_guidance_answer as _build_recovery_guidance_answer_helper,
	dimension_query_subject as _dimension_query_subject_helper,
	metric_query_phrase as _metric_query_phrase_helper,
	recovery_time_phrase as _recovery_time_phrase_helper,
	structured_governed_query_message as _structured_governed_query_message_helper,
)
from ai_assistant_ui.qwen_chat.recovery_guidance_support import (
	handle_recovery_guidance_response as _handle_recovery_guidance_response_helper,
)
from ai_assistant_ui.qwen_chat.requery_message_support import (
	compile_capability_requery_message as _compile_capability_requery_message_helper,
)
from ai_assistant_ui.qwen_chat.rollout import (
	_compiled_first_turn_rollout_decision,
	_erp_business_reasoning_rollout_decision,
	get_compiled_first_turn_rollout_status,
	get_erp_business_reasoning_rollout_status,
)
from ai_assistant_ui.qwen_chat.scope_support import (
	context_isolation_payload as _context_isolation_payload_helper,
	out_of_scope_answer as _out_of_scope_answer_helper,
	reasoning_preempted_by_followup_refinement as _reasoning_preempted_by_followup_refinement,
	reasoning_scope_suppression_allowed as _reasoning_scope_suppression_allowed,
	reasoning_supersedes_contradictory_presentation_followup as _reasoning_supersedes_contradictory_presentation_followup,
)
from ai_assistant_ui.qwen_chat.smoke_fixtures import (
	require_smoke_fixture,
	smoke_fixture_action_message,
	smoke_fixture_reasoning_message,
	smoke_fixture_replacement_message,
)
from ai_assistant_ui.qwen_chat.family_evaluation_support import (
	build_family_latency_budget_report as _build_family_latency_budget_report_helper,
	run_clarification_policy_smoke as _run_clarification_policy_smoke_helper,
	run_clarification_translation_probe as _run_clarification_translation_probe_helper,
	run_context_isolation_smoke as _run_context_isolation_smoke_helper,
	run_entity_drilldown_probe as _run_entity_drilldown_probe_helper,
	run_entity_drilldown_smoke as _run_entity_drilldown_smoke_helper,
	run_family_evaluation_case as _run_family_evaluation_case_helper,
	run_family_evaluation_smoke as _run_family_evaluation_smoke_helper,
	run_family_latency_budget_smoke as _run_family_latency_budget_smoke_helper,
	run_followup_fidelity_smoke as _run_followup_fidelity_smoke_helper,
	run_full_family_evaluation_suite as _run_full_family_evaluation_suite_helper,
	run_full_family_evaluation_smoke as _run_full_family_evaluation_smoke_helper,
	run_family_evaluation_suite as _run_family_evaluation_suite_helper,
	run_followup_report_ambiguity_smoke as _run_followup_report_ambiguity_smoke_helper,
	run_family_tool_surface_probe as _run_family_tool_surface_probe_helper,
	run_family_tool_surface_smoke as _run_family_tool_surface_smoke_helper,
	run_natural_narrative_smoke as _run_natural_narrative_smoke_helper,
	run_response_policy_probe as _run_response_policy_probe_helper,
	run_delivery_note_date_scope_probe as _run_delivery_note_date_scope_probe_helper,
	run_delivery_note_detail_smoke as _run_delivery_note_detail_smoke_helper,
	run_delivery_note_listing_limit_probe as _run_delivery_note_listing_limit_probe_helper,
	run_delivery_note_listing_smoke as _run_delivery_note_listing_smoke_helper,
	run_delivery_note_session_reset_smoke as _run_delivery_note_session_reset_smoke_helper,
	run_delivery_note_status_probe as _run_delivery_note_status_probe_helper,
	run_delivery_note_trend_probe as _run_delivery_note_trend_probe_helper,
	run_fresh_chat_invoice_delivery_proof_smoke as _run_fresh_chat_invoice_delivery_proof_smoke_helper,
	run_invoice_delivery_proof_smoke as _run_invoice_delivery_proof_smoke_helper,
	run_customer_credit_exposure_smoke as _run_customer_credit_exposure_smoke_helper,
	run_customer_credit_overdue_smoke as _run_customer_credit_overdue_smoke_helper,
	run_customer_credit_balance_smoke as _run_customer_credit_balance_smoke_helper,
	run_customer_credit_detail_followup_smoke as _run_customer_credit_detail_followup_smoke_helper,
	run_customer_credit_policy_followup_smoke as _run_customer_credit_policy_followup_smoke_helper,
	run_governed_kpi_frontdoor_smoke as _run_governed_kpi_frontdoor_smoke_helper,
	run_governed_kpi_customer_execution_smoke as _run_governed_kpi_customer_execution_smoke_helper,
	run_governed_kpi_period_execution_smoke as _run_governed_kpi_period_execution_smoke_helper,
	run_customer_credit_overdue_probe as _run_customer_credit_overdue_probe_helper,
	run_customer_credit_balance_probe as _run_customer_credit_balance_probe_helper,
	run_customer_credit_scope_reset_probe as _run_customer_credit_scope_reset_probe_helper,
	run_customer_credit_scope_reset_smoke as _run_customer_credit_scope_reset_smoke_helper,
	run_purchase_order_detail_smoke as _run_purchase_order_detail_smoke_helper,
	run_purchase_order_listing_smoke as _run_purchase_order_listing_smoke_helper,
	run_purchase_order_status_followup_smoke as _run_purchase_order_status_followup_smoke_helper,
	run_purchase_order_status_scope_reset_smoke as _run_purchase_order_status_scope_reset_smoke_helper,
	run_sales_order_detail_smoke as _run_sales_order_detail_smoke_helper,
	run_sales_order_status_followup_smoke as _run_sales_order_status_followup_smoke_helper,
	run_structured_presentation_smoke as _run_structured_presentation_smoke_helper,
	run_transaction_listing_smoke as _run_transaction_listing_smoke_helper,
)
from ai_assistant_ui.qwen_chat.phase55_hardening_support import (
	run_ap_ar_default_policy_smoke as _run_phase55_ap_ar_default_policy_smoke_helper,
	run_clarification_attempt_smoke as _run_phase55_clarification_attempt_smoke_helper,
	run_clarification_meta_question_smoke as _run_phase55_clarification_meta_question_smoke_helper,
	run_frontdoor_boundary_smoke as _run_phase55_frontdoor_boundary_smoke_helper,
	run_hardening_suite as _run_phase55_hardening_suite_helper,
	run_observability_smoke as _run_phase55_observability_smoke_helper,
	run_pending_override_smoke as _run_phase55_pending_override_smoke_helper,
)
from ai_assistant_ui.qwen_chat.phase6_hardening_support import (
	run_artifact_refinement_precedence_smoke as _run_phase6_artifact_refinement_precedence_smoke_helper,
	run_continuation_fulfillment_smoke as _run_phase6_continuation_fulfillment_smoke_helper,
	run_grounded_source_reset_smoke as _run_phase6_grounded_source_reset_smoke_helper,
	run_hardening_suite as _run_phase6_hardening_suite_helper,
	run_nonadvisory_recommendation_boundary_smoke as _run_phase6_nonadvisory_recommendation_boundary_smoke_helper,
	run_observability_smoke as _run_phase6_observability_smoke_helper,
	run_reasoning_frontdoor_boundary_smoke as _run_phase6_reasoning_frontdoor_boundary_smoke_helper,
	run_reasoning_live_rollout_smoke as _run_phase6_reasoning_live_rollout_smoke_helper,
	run_reasoning_without_grounding_smoke as _run_phase6_reasoning_without_grounding_smoke_helper,
)
from ai_assistant_ui.qwen_chat.phase7_hardening_support import (
	run_boundary_response_live_smoke as _run_phase7_boundary_response_live_smoke_helper,
	run_hardening_suite as _run_phase7_hardening_suite_helper,
	run_live_boundary_orchestration_smoke as _run_phase7_live_boundary_orchestration_smoke_helper,
	run_observability_smoke as _run_phase7_observability_smoke_helper,
)
from ai_assistant_ui.qwen_chat.phase8_hardening_support import (
	run_evidence_boundary_observability_smoke as _run_phase8_evidence_boundary_observability_smoke_helper,
	run_enrichment_boundary_observability_smoke as _run_phase8_enrichment_boundary_observability_smoke_helper,
	run_fresh_query_override_smoke as _run_phase8_fresh_query_override_smoke_helper,
	run_hardening_suite as _run_phase8_hardening_suite_helper,
	run_recovery_authority_smoke as _run_phase8_recovery_authority_smoke_helper,
	run_recovery_execution_smoke as _run_phase8_recovery_execution_smoke_helper,
	run_recovery_guidance_observability_smoke as _run_phase8_recovery_guidance_observability_smoke_helper,
	run_repair_handling_smoke as _run_phase8_repair_handling_smoke_helper,
)
from ai_assistant_ui.qwen_chat.smoke_session_support import (
	run_phase55_smoke_session as _run_phase55_smoke_session_helper,
	run_phase6_smoke_session as _run_phase6_smoke_session_helper,
)
from ai_assistant_ui.qwen_chat.probes.service_diagnostics import (
	run_first_turn_regression_suite as _run_first_turn_regression_suite_helper,
	run_phase1_1_delivery_note_invoice_switch_debug as _run_phase1_1_delivery_note_invoice_switch_debug_helper,
	run_phase1_1_invoice_detail_delivery_trend_debug as _run_phase1_1_invoice_detail_delivery_trend_debug_helper,
	run_phase4_compiled_rollout_governance_selftests as _run_phase4_compiled_rollout_governance_selftests_helper,
	run_phase4_compiled_rollout_monitoring_smoke as _run_phase4_compiled_rollout_monitoring_smoke_helper,
	run_phase4_compiled_rollout_smoke as _run_phase4_compiled_rollout_smoke_helper,
	run_same_session_fresh_query_regression_smoke as _run_same_session_fresh_query_regression_smoke_helper,
	summarize_compiled_first_turn_audits as _summarize_compiled_first_turn_audits_helper,
)
from ai_assistant_ui.qwen_chat.metadata import (
	capability_default_report_name,
	capability_report_names,
	capability_semantic_tags,
	get_family_evaluation_case_set,
	governed_self_contained_business_terms,
	list_family_evaluation_case_sets,
	ontology_detect_concepts,
	ontology_concept_aliases,
	ontology_self_contained_prefixes,
	report_business_family_ids,
	report_defaultable_filters,
	report_family_capability_ids,
	report_semantic_tags,
	report_supported_metrics,
)
from ai_assistant_ui.qwen_chat.metric_union_support import (
	artifact_metric_columns_available as _artifact_metric_columns_available_helper,
	canonical_metric_keys_for_values as _canonical_metric_keys_for_values_helper,
	metric_union_target_score as _metric_union_target_score_helper,
	normalized_key_fallback as _normalized_key_fallback_helper,
	report_can_project_metric_union as _report_can_project_metric_union_helper,
	resolve_metric_union_requery_target as _resolve_metric_union_requery_target_helper,
)
from ai_assistant_ui.qwen_chat.governed_kpi_support import (
	run_governed_kpi_frontdoor_probe as _run_governed_kpi_frontdoor_probe_helper,
)
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	run_governed_kpi_customer_execution_probe as _run_governed_kpi_customer_execution_probe_helper,
	run_governed_kpi_period_execution_probe as _run_governed_kpi_period_execution_probe_helper,
)
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat
from ai_assistant_ui.qwen_chat.runtime_support import (
	is_generic_compiled_failure_answer as _is_generic_compiled_failure_answer,
	local_transform_trace_message as _local_transform_trace_message_helper,
	phase6_activation_event_level as _phase6_activation_event_level,
	phase6_execution_event_level as _phase6_execution_event_level,
	safe_runtime_failure_message as _safe_runtime_failure_message,
	tool_trace_message as _tool_trace_message_helper,
	tool_trace_payload as _tool_trace_payload,
)
from ai_assistant_ui.qwen_chat.semantic_interpreter import interpret_followup_semantically
from ai_assistant_ui.qwen_chat.semantic_reasoning_activation import interpret_reasoning_activation_semantically
from ai_assistant_ui.qwen_chat.semantic_aliases import detect_canonical_keys as _detect_semantic_alias_keys
QWEN_SESSION_DOCTYPE = "Qwen Chat Session"
VISIBLE_ROLES = {"user", "assistant"}


def _message_looks_like_self_contained_governed_business_query(
	*,
	message: str,
	language: str = "en",
) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	prefixes = [
		str(value or "").strip().lower()
		for value in ontology_self_contained_prefixes(language)
		if str(value or "").strip()
	]
	if prefixes and not any(text.startswith(prefix) for prefix in prefixes):
		return False
	if ontology_detect_concepts(text, language=language, include_extended=False):
		return True
	for term in governed_self_contained_business_terms(language):
		clean = str(term or "").strip().lower()
		if clean and re.search(rf"(?<!\\w){re.escape(clean)}(?!\\w)", text):
			return True
	return False


def _message_has_grounded_context_anchor(message: str) -> bool:
	text = " ".join(str(message or "").strip().lower().split())
	if not text:
		return False
	return bool(
		re.search(
			r"\b(this|that|these|those|it|its|they|their|them)\b",
			text,
		)
	)


def _compiled_decision_message(*, request_id: str, raw_message: str, result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
	return _compiled_decision_message_helper(
		request_id=request_id,
		raw_message=raw_message,
		result=result,
		build_known_unsupported_scope_decision_input=build_known_unsupported_scope_decision_input,
		translate_clarification_signal=translate_clarification_signal,
		out_of_scope_answer=_out_of_scope_answer,
		is_generic_compiled_failure_answer=_is_generic_compiled_failure_answer,
		safe_runtime_failure_message=_safe_runtime_failure_message,
	)


def _handle_compiled_first_turn_result(
	*,
	session_doc,
	request_id: str,
	interaction_contract,
	followup_resolution,
	execution_path,
	governed_scope_contract=None,
	front_door_contract=None,
	clarification_response_contract=None,
	pre_result_tool_payloads: List[Dict[str, Any]] | None = None,
	result: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
	return _handle_compiled_first_turn_result_helper(
		session_doc=session_doc,
		request_id=request_id,
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		result=result,
		governed_scope_contract=governed_scope_contract,
		front_door_contract=front_door_contract,
		clarification_response_contract=clarification_response_contract,
		pre_result_tool_payloads=pre_result_tool_payloads,
		append_compiled_attempt_artifacts=_append_compiled_attempt_artifacts,
		compiled_decision_message=_compiled_decision_message,
		compiled_clarification_reason_contract=_compiled_clarification_reason_contract,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		tool_trace_message=_tool_trace_message,
		latest_qwen_trace_payload=_latest_qwen_trace_payload,
		latest_assistant_payload=_latest_assistant_payload,
		append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
		knowledge_boundary_event_level=_knowledge_boundary_event_level,
		append_knowledge_boundary_observability=_append_knowledge_boundary_observability,
		build_grounded_turn_context=build_grounded_turn_context,
		build_audit_envelope=build_audit_envelope,
		save_session=_save_session,
		store_pending_clarification_signal=store_pending_clarification_signal,
		clear_pending_clarification_signal=clear_pending_clarification_signal,
	)


def _append_compiled_attempt_artifacts(session_doc, result: Dict[str, Any]) -> None:
	_append_compiled_attempt_artifacts_helper(
		session_doc,
		result,
		append_tool_payload=_append_tool_payload,
	)


def _append_message(session_doc, role: str, content: str) -> None:
	_session_append_message(session_doc, role, content)


def _append_tool_payload(session_doc, payload: Dict[str, Any]) -> None:
	_session_append_tool_payload(session_doc, payload)


def _safe_json_dumps(obj: Any) -> str:
	return _session_safe_json_dumps(obj)


def _save_session(session_doc, *, ignore_permissions: bool = False) -> None:
	_session_save(session_doc, ignore_permissions=ignore_permissions)


def _assistant_text_payload(text: str) -> str:
	return _assistant_text_payload_helper(str(text or ""), safe_json_dumps=_safe_json_dumps)


def _visible_message_text(role: str, content: str) -> str:
	return _history_visible_message_text(role, content)


def _parse_payload(content: str) -> Dict[str, Any]:
	return _history_parse_payload(content)


def _positions_to_skip_for_runtime_context(session_doc) -> set[int]:
	return _history_positions_to_skip_for_runtime_context(session_doc, visible_roles=VISIBLE_ROLES)


def _recent_messages(session_doc, limit: int = 10) -> List[Dict[str, str]]:
	return _history_recent_messages(session_doc, visible_roles=VISIBLE_ROLES, limit=limit)


def _latest_assistant_payload(session_doc) -> Dict[str, Any]:
	return _history_latest_assistant_payload(session_doc)


def _session_tool_payloads(session_doc) -> List[Dict[str, Any]]:
	return _history_tool_payloads(session_doc)


def _latest_display_preferences(session_doc, requested_modes: List[str] | None = None) -> Dict[str, bool]:
	return _history_latest_display_preferences(session_doc, requested_modes=requested_modes)


def _compile_capability_requery_message(
	session_doc,
	*,
	raw_message: str,
	followup_resolution,
	grounded_turn: Dict[str, Any],
	continuation_contract=None,
) -> str:
	return _compile_capability_requery_message_helper(
		session_doc,
		raw_message=raw_message,
		followup_resolution=followup_resolution,
		grounded_turn=grounded_turn,
		continuation_contract=continuation_contract,
	)


def _recovery_time_phrase(recovery_contract: Dict[str, Any]) -> str:
	return _recovery_time_phrase_helper(recovery_contract)


def _dimension_query_subject(value: str) -> str:
	return _dimension_query_subject_helper(value)


def _metric_query_phrase(value: str, capability_id: str = "") -> str:
	return _metric_query_phrase_helper(value, capability_id=capability_id)


def _structured_governed_query_message(
	*,
	requested_top_n: int,
	dimension: str,
	metric: str,
	time_phrase: str = "",
	report_name: str = "",
	capability_id: str = "",
) -> str:
	return _structured_governed_query_message_helper(
		requested_top_n=requested_top_n,
		dimension=dimension,
		metric=metric,
		time_phrase=time_phrase,
		report_name=report_name,
		capability_id=capability_id,
	)


def _build_recovery_governed_query_message(recovery_contract: Dict[str, Any]) -> str:
	return _build_recovery_governed_query_message_helper(recovery_contract)


def _build_recovery_guidance_answer(recovery_contract: Dict[str, Any]) -> str:
	return _build_recovery_guidance_answer_helper(recovery_contract)


def _artifact_metric_columns_available(
	artifact_payload: Dict[str, Any],
	requested_columns: List[str],
) -> bool:
	return _artifact_metric_columns_available_helper(artifact_payload, requested_columns)


def _normalized_key_fallback(value: str) -> str:
	return _normalized_key_fallback_helper(value)


def _canonical_metric_keys_for_values(values: List[str], capability_id: str = "") -> List[str]:
	return _canonical_metric_keys_for_values_helper(values, capability_id=capability_id)


def _report_can_project_metric_union(report_name: str, required_metric_keys: List[str], capability_id: str) -> bool:
	return _report_can_project_metric_union_helper(report_name, required_metric_keys, capability_id)


def _metric_union_target_score(
	*,
	report_name: str,
	capability_id: str,
	source_report: str,
	current_capability_id: str,
	required_metric_keys: List[str],
) -> int:
	return _metric_union_target_score_helper(
		report_name=report_name,
		capability_id=capability_id,
		source_report=source_report,
		current_capability_id=current_capability_id,
		required_metric_keys=required_metric_keys,
	)


def _resolve_metric_union_requery_target(
	*,
	artifact_payload: Dict[str, Any],
	source_report: str,
	current_capability_id: str,
	required_metric_keys: List[str],
) -> tuple[str, str]:
	return _resolve_metric_union_requery_target_helper(
		artifact_payload=artifact_payload,
		source_report=source_report,
		current_capability_id=current_capability_id,
		required_metric_keys=required_metric_keys,
	)


def _artifact_evidence_concepts(artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> set[str]:
	return _artifact_evidence_concepts_helper(artifact_payload, grounded_turn)


def _grounded_artifact_evidence_boundary_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	return _grounded_artifact_evidence_boundary_answer_helper(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)


def _grounded_artifact_direct_evidence_answer(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	return _grounded_artifact_direct_evidence_answer_helper(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)


def _build_grounded_artifact_direct_evidence_rendered_payload(
	*,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> Dict[str, Any]:
	return _build_grounded_artifact_direct_evidence_rendered_payload_helper(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)


def _grounded_artifact_direct_evidence_response(
	*,
	request_id: str,
	session_id: str,
	interaction_contract,
	response_policy_contract,
	raw_message: str,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	fallback_answer_text: str = "",
) -> Dict[str, Any]:
	fallback_text = str(fallback_answer_text or "").strip()
	if not fallback_text:
		fallback_text = _grounded_artifact_direct_evidence_answer(
			raw_message=raw_message,
			artifact_payload=artifact_payload,
			grounded_turn=grounded_turn,
		)
	if not fallback_text:
		return {}
	requested_dimensions = {
		str(value or "").strip()
		for value in _detect_semantic_alias_keys(raw_message, dimension_or_metric="dimension")
		if str(value or "").strip()
	}
	entity_type = str((artifact_payload.get("dimensions") or {}).get("entity_type") or "").strip().lower()
	rendered_response_payload = _build_grounded_artifact_direct_evidence_rendered_payload(
		raw_message=raw_message,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)
	if not rendered_response_payload:
		return {
			"answer_text": fallback_text,
			"rendered_response_payload": {},
			"narrative_payload": {},
			"narrative_contract_payload": {},
		}
	if entity_type == "purchase_order" or "posting_date" in requested_dimensions or (
		entity_type == "sales_order" and "planned_delivery_date" in requested_dimensions
	):
		rendered_response_payload["answer_text"] = fallback_text
		return {
			"answer_text": fallback_text,
			"rendered_response_payload": rendered_response_payload,
			"narrative_payload": {},
			"narrative_contract_payload": {},
		}
	rendered_response_payload["answer_text"] = fallback_text
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=artifact_payload,
		rendered_response_payload=rendered_response_payload,
		response_policy=response_policy_contract.to_runtime_payload(),
		validation_payload={},
	)
	narrative_payload = narrate_governed_artifact(
		session_id=session_id,
		user_id=str(interaction_contract.user_id or "").strip(),
		site_name=str(interaction_contract.site_name or "").strip(),
		message=raw_message,
		request_id=request_id,
		artifact_context=artifact_context,
		response_policy=response_policy_contract.to_runtime_payload(),
	)
	narrative_contract = build_artifact_narrative_contract(
		request_id=request_id,
		artifact_context=artifact_context,
		runtime_payload=narrative_payload,
	)
	narrative_contract_payload = narrative_contract.to_payload() if narrative_contract is not None else {}
	answer_text = str(narrative_contract_payload.get("answer_text") or "").strip() or fallback_text
	return {
		"answer_text": answer_text,
		"rendered_response_payload": rendered_response_payload,
		"narrative_payload": narrative_payload if isinstance(narrative_payload, dict) else {},
		"narrative_contract_payload": narrative_contract_payload,
	}


def _artifact_enrichment_boundary_answer(
	*,
	followup_resolution,
	compatibility_contract,
) -> str:
	return _artifact_enrichment_boundary_answer_helper(
		followup_resolution=followup_resolution,
		compatibility_contract=compatibility_contract,
	)


def _artifact_rank_row_count(artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> int:
	return _artifact_rank_row_count_helper(artifact_payload, grounded_turn)


def _authoritative_continuation_resolution(
	*,
	request_id: str,
	followup_resolution,
	continuation_contract,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
):
	return _authoritative_continuation_resolution_helper(
		request_id=request_id,
		followup_resolution=followup_resolution,
		continuation_contract=continuation_contract,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)


def _requery_resolution_for_unsupported_local_columns(
	*,
	request_id: str,
	followup_resolution,
	artifact_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
	continuation_contract=None,
) -> tuple[Any | None, Any | None]:
	return _requery_resolution_for_unsupported_local_columns_helper(
		request_id=request_id,
		followup_resolution=followup_resolution,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
		continuation_contract=continuation_contract,
	)


def _latest_qwen_trace_payload(session_doc) -> Dict[str, Any]:
	return _grounded_latest_qwen_trace_payload(session_doc)


def _latest_grounded_assistant_context(session_doc) -> Tuple[Dict[str, Any], Dict[str, Any]]:
	return _grounded_latest_grounded_assistant_context(session_doc)


def _grounded_turn_source_request_id(payload: Dict[str, Any] | None) -> str:
	return _grounded_turn_source_request_id_helper(payload)


def _latest_grounded_turn_contract(session_doc) -> Dict[str, Any]:
	return _grounded_latest_grounded_turn_contract(session_doc)


def _artifact_compatible_with_grounded_turn(*, artifact_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> bool:
	return _grounded_artifact_compatible_with_grounded_turn(
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
	)


def _latest_normalized_family_artifact(session_doc, *, grounded_turn: Dict[str, Any] | None = None) -> Dict[str, Any]:
	return _grounded_latest_normalized_family_artifact(session_doc, grounded_turn=grounded_turn)


def _latest_reasoning_contract(session_doc) -> Dict[str, Any]:
	return _grounded_latest_reasoning_contract(session_doc)


def _latest_recovery_contract(session_doc) -> Dict[str, Any]:
	return _grounded_latest_recovery_contract(session_doc)


def _source_compatible_reasoning_contract(
	*,
	grounded_turn: Dict[str, Any],
	reasoning_contract: Dict[str, Any],
) -> Dict[str, Any]:
	return _grounded_source_compatible_reasoning_contract(
		grounded_turn=grounded_turn,
		reasoning_contract=reasoning_contract,
	)


def _recent_messages_for_grounded_source(
	session_doc,
	*,
	grounded_turn: Dict[str, Any],
	limit: int = 10,
) -> List[Dict[str, str]]:
	return _history_recent_messages_for_grounded_source(
		session_doc,
		grounded_turn=grounded_turn,
		visible_roles=VISIBLE_ROLES,
		limit=limit,
	)


def _append_knowledge_boundary_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	proposed_lane: str,
	clarification_resolution: Dict[str, Any] | None = None,
	clarification_reason: Dict[str, Any] | None = None,
	front_door_contract: Dict[str, Any] | None = None,
	governed_scope_contract: Dict[str, Any] | None = None,
	compiled_execution_audit: Dict[str, Any] | None = None,
	family_validation: Dict[str, Any] | None = None,
	semantic_validation: Dict[str, Any] | None = None,
	reasoning_activation_contract: Dict[str, Any] | None = None,
	reasoning_contract: Dict[str, Any] | None = None,
	grounded_turn: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	return _append_knowledge_boundary_contract_helper(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		proposed_lane=proposed_lane,
		clarification_resolution=clarification_resolution,
		clarification_reason=clarification_reason,
		front_door_contract=front_door_contract,
		governed_scope_contract=governed_scope_contract,
		compiled_execution_audit=compiled_execution_audit,
		family_validation=family_validation,
		semantic_validation=semantic_validation,
		reasoning_activation_contract=reasoning_activation_contract,
		reasoning_contract=reasoning_contract,
		grounded_turn=grounded_turn,
		append_tool_payload=_append_tool_payload,
	)


def _append_grounded_evidence_recovery_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	artifact_payload: Dict[str, Any] | None,
	grounded_turn: Dict[str, Any] | None,
	followup_resolution,
	reason: str,
) -> Dict[str, Any]:
	return _append_grounded_evidence_recovery_contract_helper(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		artifact_payload=artifact_payload,
		grounded_turn=grounded_turn,
		followup_resolution=followup_resolution,
		reason=reason,
		append_tool_payload=_append_tool_payload,
	)


def _append_enrichment_recovery_contract(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	compatibility_contract,
	grounded_turn: Dict[str, Any] | None,
	followup_resolution,
) -> Dict[str, Any]:
	return _append_enrichment_recovery_contract_helper(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		compatibility_contract=compatibility_contract,
		grounded_turn=grounded_turn,
		followup_resolution=followup_resolution,
		append_tool_payload=_append_tool_payload,
	)


def _handle_recovery_guidance_response(
	*,
	session_doc,
	request_id: str,
	raw_message: str,
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	clarification_response_contract,
	response_policy_contract,
	semantic_repair_payload: Dict[str, Any],
	repair_contract_payload: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	answer_text: str,
) -> Tuple[bool, Dict[str, Any]]:
	return _handle_recovery_guidance_response_helper(
		session_doc,
		request_id=request_id,
		raw_message=raw_message,
		interaction_contract=interaction_contract,
		frontdoor_semantic_result=frontdoor_semantic_result,
		frontdoor_contract=frontdoor_contract,
		clarification_response_contract=clarification_response_contract,
		response_policy_contract=response_policy_contract,
		semantic_repair_payload=semantic_repair_payload,
		repair_contract_payload=repair_contract_payload,
		latest_grounded_turn=latest_grounded_turn,
		answer_text=answer_text,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
	)


def _knowledge_boundary_event_level(boundary_payload: Dict[str, Any]) -> str:
	return _knowledge_boundary_event_level_helper(boundary_payload)


def _append_knowledge_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_payload: Dict[str, Any],
	latency_ms: int,
) -> None:
	_append_knowledge_boundary_observability_helper(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		boundary_payload=boundary_payload,
		latency_ms=latency_ms,
		append_tool_payload=_append_tool_payload,
	)


def _append_artifact_boundary_observability(
	session_doc,
	*,
	request_id: str,
	session_id: str,
	boundary_name: str,
	latency_ms: int,
	recovery_payload: Dict[str, Any] | None = None,
	grounded_turn_available: bool = False,
) -> None:
	_append_artifact_boundary_observability_helper(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		boundary_name=boundary_name,
		latency_ms=latency_ms,
		recovery_payload=recovery_payload,
		grounded_turn_available=grounded_turn_available,
		append_tool_payload=_append_tool_payload,
	)


def _local_transform_trace_message(request_id: str, source_request_id: str, transforms: List[str]) -> str:
	return _local_transform_trace_message_helper(
		request_id=request_id,
		source_request_id=source_request_id,
		transforms=transforms,
		safe_json_dumps=_safe_json_dumps,
	)


def _try_local_followup_transform(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	followup_resolution,
	interaction_contract,
	response_policy_contract,
	continuation_contract=None,
) -> Tuple[bool, Dict[str, Any]] | None:
	return _try_local_followup_transform_helper(
		session_doc,
		request_id=request_id,
		raw_message=raw_message,
		followup_resolution=followup_resolution,
		interaction_contract=interaction_contract,
		response_policy_contract=response_policy_contract,
		continuation_contract=continuation_contract,
		latest_grounded_assistant_context=_latest_grounded_assistant_context,
		latest_grounded_turn_contract=_latest_grounded_turn_contract,
		latest_normalized_family_artifact=_latest_normalized_family_artifact,
		latest_display_preferences=_latest_display_preferences,
		session_tool_payloads=_session_tool_payloads,
		apply_local_followup_transforms=_apply_local_followup_transforms_helper,
		maybe_apply_local_followup_narrative=lambda **kwargs: _maybe_apply_local_followup_narrative_helper(
			**kwargs,
			build_artifact_narrative_context=build_artifact_narrative_context,
			narrate_governed_artifact=narrate_governed_artifact,
			build_artifact_narrative_contract=build_artifact_narrative_contract,
		),
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		local_transform_trace_message=_local_transform_trace_message,
		save_session=_save_session,
		supports_local_family_followup=supports_local_family_followup,
		render_local_family_followup=render_local_family_followup,
		render_local_followup=render_local_followup,
		ensure_table_from_grounded_context=_ensure_table_from_grounded_context,
		transform_markdown_to_million=_transform_markdown_to_million,
	)


def _tool_trace_message(
	*,
	request_id: str,
	ok: bool,
	tool_trace: List[Dict[str, Any]],
	agent_meta: Dict[str, Any],
	error: str,
	runtime_latency_ms: int,
) -> str:
	return _tool_trace_message_helper(
		request_id=request_id,
		ok=ok,
		tool_trace=tool_trace,
		agent_meta=agent_meta,
		error=error,
		runtime_latency_ms=runtime_latency_ms,
		safe_json_dumps=_safe_json_dumps,
	)


def _context_isolation_payload(*, request_id: str, decision: Dict[str, Any]) -> Dict[str, Any]:
	return _context_isolation_payload_helper(request_id=request_id, decision=decision)


def _out_of_scope_answer(message: str, decision: Dict[str, Any] | Any) -> str:
	return _out_of_scope_answer_helper(message, decision)


def _try_entity_detail_followup(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	entity_reference: Dict[str, Any],
	interaction_contract,
	response_policy_contract,
	latest_grounded_turn: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]] | None:
	return _try_entity_detail_followup_helper(
		session_doc,
		request_id=request_id,
		raw_message=raw_message,
		entity_reference=entity_reference,
		interaction_contract=interaction_contract,
		response_policy_contract=response_policy_contract,
		latest_grounded_turn=latest_grounded_turn,
		execute_entity_drilldown=execute_entity_drilldown,
		log_error=lambda title: frappe.log_error(frappe.get_traceback(), title),
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		tool_trace_message=_tool_trace_message,
		save_session=_save_session,
	)


def handle_qwen_user_message(*, session_name: str, message: str, user: str) -> Tuple[bool, Dict[str, Any]]:
	session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
	site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	request_id = uuid.uuid4().hex
	msg = str(message or "").strip()
	raw_msg = msg
	recent_frontdoor_messages = _recent_messages(session_doc, limit=6)
	latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
	latest_family_artifact = _latest_normalized_family_artifact(session_doc, grounded_turn=latest_grounded_turn)
	latest_assistant_payload = _latest_assistant_payload(session_doc)
	latest_reasoning_contract = _source_compatible_reasoning_contract(
		grounded_turn=latest_grounded_turn,
		reasoning_contract=_latest_reasoning_contract(session_doc),
	)
	latest_recovery_contract = _latest_recovery_contract(session_doc)
	clarification_state = get_clarification_state(session_doc)
	pending_clarification_signal = (
		dict(clarification_state.pending_signal)
		if clarification_state.has_pending
		else latest_pending_clarification_signal(session_doc)
	)
	latest_grounded_turn_available = bool(latest_grounded_turn.get("grounded")) or bool(
		_latest_grounded_assistant_context(session_doc)[0]
	)
	interaction_contract = build_interaction_contract(
		request_id=request_id,
		session_id=session_name,
		user_id=user,
		site_name=site_name,
		raw_message=msg,
	)
	reasoning_rollout = _erp_business_reasoning_rollout_decision(
		session_name=session_name,
		user=user,
		site_name=site_name,
	)
	provisional_response_policy_contract = build_response_policy_contract(
		interaction_contract=interaction_contract,
	)
	pre_frontdoor_reasoning_activation_contract = None
	pre_frontdoor_reasoning_semantic_result = None
	pre_frontdoor_reasoning_activation_latency_ms = 0
	reasoning_recent_messages = _recent_messages_for_grounded_source(
		session_doc,
		grounded_turn=latest_grounded_turn,
		limit=10,
	)
	if bool(reasoning_rollout.get("enabled")) and latest_grounded_turn_available and not pending_clarification_signal:
		pre_frontdoor_reasoning_activation_contract = build_reasoning_activation_contract(
			request_id=request_id,
			session_id=session_name,
			message=msg,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
			response_policy_contract=provisional_response_policy_contract.to_payload(),
		)
		activation_started_at = time.perf_counter()
		pre_frontdoor_reasoning_semantic_result = interpret_reasoning_activation_semantically(
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			recent_messages=reasoning_recent_messages,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
			activation_contract=pre_frontdoor_reasoning_activation_contract.to_payload(),
			prior_reasoning_contract=latest_reasoning_contract,
		)
		pre_frontdoor_reasoning_activation_latency_ms = int(max(0, round((time.perf_counter() - activation_started_at) * 1000)))
		_append_tool_payload(
			session_doc,
			record_phase6_observability_event(
				request_id=request_id,
				session_id=session_name,
				event_family="reasoning_activation",
				event_name=str(pre_frontdoor_reasoning_semantic_result.status or "").strip() or "unknown",
				event_level=_phase6_activation_event_level(pre_frontdoor_reasoning_semantic_result.status),
				details={
					"reasoning_type": str(getattr(getattr(pre_frontdoor_reasoning_semantic_result, "intent", None), "reasoning_type", "") or "").strip(),
					"confidence": float(getattr(getattr(pre_frontdoor_reasoning_semantic_result, "intent", None), "confidence", 0.0) or 0.0),
					"confidence_threshold": float(getattr(pre_frontdoor_reasoning_semantic_result, "confidence_threshold", 0.0) or 0.0),
					"grounded_source_name": str(pre_frontdoor_reasoning_activation_contract.grounded_source_name or "").strip(),
					"grounded_family_id": str(pre_frontdoor_reasoning_activation_contract.grounded_family_id or "").strip(),
					"activation_state": str(pre_frontdoor_reasoning_activation_contract.activation_state or "").strip(),
					"rollout_source": str(reasoning_rollout.get("source") or "").strip(),
					"latency_ms": pre_frontdoor_reasoning_activation_latency_ms,
					"validation_error": str(getattr(pre_frontdoor_reasoning_semantic_result, "validation_error", "") or "").strip(),
					"runtime_error": str(getattr(pre_frontdoor_reasoning_semantic_result, "runtime_error", "") or "").strip(),
					"stage": "pre_frontdoor",
				},
			),
		)
		_append_tool_payload(
			session_doc,
			record_phase6_performance_metric(
				request_id=request_id,
				session_id=session_name,
				metric_name="reasoning_activation_latency",
				metric_value=float(pre_frontdoor_reasoning_activation_latency_ms),
				metric_unit="ms",
				details={
					"stage": "pre_frontdoor",
					"status": str(pre_frontdoor_reasoning_semantic_result.status or "").strip(),
				},
			),
		)
	clarification_response_contract = None
	frontdoor_render_result = None
	frontdoor_answer = ""
	if pending_clarification_signal:
		clarification_response_contract, frontdoor_semantic_result, frontdoor_contract = build_pending_clarification_frontdoor_skip(
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=raw_msg,
			pending_clarification_signal=pending_clarification_signal,
			clarification_state=clarification_state,
			latest_grounded_turn_available=latest_grounded_turn_available,
			latest_grounded_turn=latest_grounded_turn,
		)
	else:
		post_clarification_stop_acknowledgement = bool(
			latest_assistant_turn_was_clarification_fallback_stop(session_doc)
			and looks_like_short_acknowledgement(msg)
		)
		frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer = evaluate_frontdoor_lane(
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			recent_messages=recent_frontdoor_messages,
			grounded_context_available=latest_grounded_turn_available,
			latest_grounded_turn=latest_grounded_turn,
			latest_recovery_contract_available=bool(latest_recovery_contract),
			pre_frontdoor_reasoning_semantic_result=pre_frontdoor_reasoning_semantic_result,
			post_clarification_stop_acknowledgement=post_clarification_stop_acknowledgement,
		)
	entity_drilldown = detect_entity_drilldown_request(
		message=msg,
		artifact_payload=latest_family_artifact if isinstance(latest_family_artifact, dict) else {},
		grounded_turn=latest_grounded_turn if isinstance(latest_grounded_turn, dict) else {},
	)
	semantic_intent = None
	allow_heuristic_fallback = True
	degraded_reason = ""
	semantic_payload = None
	recovery_allows_semantic_followup = bool(
		latest_recovery_contract
		and _message_looks_like_self_contained_governed_business_query(
			message=msg,
			language=interaction_contract.detected_language,
		)
	)
	if (
		latest_grounded_turn_available
		and latest_grounded_turn
		and entity_drilldown is None
		and (not latest_recovery_contract or recovery_allows_semantic_followup)
	):
		semantic_result = interpret_followup_semantically(
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			recent_messages=_recent_messages(session_doc, limit=6),
			latest_grounded_turn=latest_grounded_turn,
			latest_assistant_payload=latest_assistant_payload,
		)
		if semantic_result.status == "accepted" and semantic_result.intent is not None:
			semantic_intent = semantic_result.intent
			allow_heuristic_fallback = False
		else:
			allow_heuristic_fallback = False
			degraded_reason = "Semantic follow-up interpretation did not meet governed confidence or runtime reliability requirements."
		semantic_payload = semantic_result.to_payload(
			fallback_used=False,
			fallback_reason="No heuristic fallback permitted; degraded follow-up handling remains explicit and auditable.",
		)
	recommendation_reasoning_preferred = (
		str(getattr(pre_frontdoor_reasoning_semantic_result, "status", "") or "").strip() == "accepted"
		and str(getattr(getattr(pre_frontdoor_reasoning_semantic_result, "intent", None), "reasoning_type", "") or "").strip()
		in {"recommendation", "continuation_detail"}
	)
	if _reasoning_supersedes_contradictory_presentation_followup(
		semantic_intent=semantic_intent,
		reasoning_semantic_result=pre_frontdoor_reasoning_semantic_result,
	):
		semantic_intent = None
	semantic_intent_has_explicit_query_shape = bool(
		semantic_intent is not None
		and (
			str(getattr(semantic_intent, "target_capability_id", "") or "").strip()
			or int(getattr(semantic_intent, "target_limit", 0) or 0)
			or str(getattr(semantic_intent, "sort_direction", "") or "").strip()
			or str(getattr(semantic_intent, "target_metric", "") or "").strip()
			or list(getattr(semantic_intent, "requested_columns", []) or [])
			or [
				str(mode or "").strip()
				for mode in (getattr(semantic_intent, "requested_modes", []) or [])
				if str(mode or "").strip() and str(mode or "").strip() not in {"presentation_transform", "table_presentation", "bullet_presentation"}
			]
		)
	)
	if recommendation_reasoning_preferred and semantic_intent is not None and not semantic_intent_has_explicit_query_shape:
		semantic_intent = None
	context_isolation = build_scope_decision_input()
	if latest_grounded_turn_available and not bool(getattr(frontdoor_contract, "handle_in_front_door", False)):
		context_isolation = normalize_scope_decision_input(
			assess_context_isolation(
				msg,
				language=interaction_contract.detected_language,
				grounded_turn=latest_grounded_turn,
				semantic_intent=semantic_intent,
				reasoning_semantic_result=pre_frontdoor_reasoning_semantic_result,
			)
		)
	if (
		bool(getattr(context_isolation, "force_new_query", False))
		and not bool(getattr(context_isolation, "out_of_scope", False))
		and semantic_intent is None
		and str(getattr(pre_frontdoor_reasoning_semantic_result, "status", "") or "").strip() == "accepted"
		and str(getattr(getattr(pre_frontdoor_reasoning_semantic_result, "intent", None), "reasoning_type", "") or "").strip()
		in {"recommendation", "continuation_detail"}
		and _reasoning_scope_suppression_allowed(context_isolation)
	):
		context_isolation = build_scope_decision_input()
	repair_recent_messages = _recent_messages(session_doc, limit=8)
	if latest_recovery_contract and not pending_clarification_signal and not bool(context_isolation.force_new_query):
		repair_handled, repair_payload = handle_repair_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			raw_message=raw_msg,
			recent_messages=repair_recent_messages,
			latest_recovery_contract=latest_recovery_contract,
			latest_grounded_turn=latest_grounded_turn,
			latest_assistant_payload=latest_assistant_payload,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			clarification_response_contract=clarification_response_contract,
			response_policy_contract=provisional_response_policy_contract,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			build_recovery_guidance_answer=_build_recovery_guidance_answer,
			handle_recovery_guidance_response=_handle_recovery_guidance_response,
			build_recovery_governed_query_message=_build_recovery_governed_query_message,
			handle_compiled_first_turn_result=_handle_compiled_first_turn_result,
		)
		if repair_handled and repair_payload is not None:
			return True, repair_payload
	if entity_drilldown is None:
		frontdoor_handled, frontdoor_payload = handle_frontdoor_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			message=msg,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			frontdoor_render_result=frontdoor_render_result,
			frontdoor_answer=frontdoor_answer,
			context_force_new_query=bool(context_isolation.force_new_query),
			latest_grounded_turn_available=latest_grounded_turn_available,
			latest_grounded_turn=latest_grounded_turn,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			assistant_text_payload=_assistant_text_payload,
			store_pending_clarification_signal=store_pending_clarification_signal,
			save_session=_save_session,
			raw_message=raw_msg,
		)
		if frontdoor_handled and frontdoor_payload is not None:
			return True, frontdoor_payload
	if pending_clarification_signal:
		clarification_handled, clarification_response_contract, msg, clarification_payload = handle_pending_clarification_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			raw_message=raw_msg,
			pending_clarification_signal=pending_clarification_signal,
			clarification_state=clarification_state,
			clarification_response_contract=clarification_response_contract,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			latest_grounded_turn_available=latest_grounded_turn_available,
			latest_grounded_turn=latest_grounded_turn,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
		)
		if clarification_handled and clarification_payload is not None:
			return True, clarification_payload
		clarified_frontdoor_message = ""
		clarification_decision = (
			str(clarification_response_contract.decision or "").strip()
			if clarification_response_contract is not None
			else ""
		)
		if (
			clarification_response_contract is not None
			and clarification_decision == "resolved_option"
			and clarification_continuation_lane(pending_clarification_signal) == "front_door"
		):
			clarified_frontdoor_message = clarification_resolved_continuation_message(
				signal_payload=pending_clarification_signal,
				resolved_option=str(clarification_response_contract.resolved_option or "").strip(),
			)
		elif clarification_decision == "new_request":
			clarified_frontdoor_message = raw_msg
		if clarified_frontdoor_message and entity_drilldown is None:
			(
				clarified_frontdoor_semantic_result,
				clarified_frontdoor_contract,
				clarified_frontdoor_render_result,
				clarified_frontdoor_answer,
			) = evaluate_frontdoor_lane(
				request_id=request_id,
				session_id=session_name,
				user_id=user,
				site_name=site_name,
				message=clarified_frontdoor_message,
				recent_messages=repair_recent_messages,
				grounded_context_available=latest_grounded_turn_available,
				latest_grounded_turn=latest_grounded_turn,
				latest_recovery_contract_available=bool(latest_recovery_contract),
				pre_frontdoor_reasoning_semantic_result=None,
			)
			frontdoor_handled, frontdoor_payload = handle_frontdoor_turn(
				session_doc=session_doc,
				request_id=request_id,
				session_id=session_name,
				message=clarified_frontdoor_message,
				interaction_contract=interaction_contract,
				frontdoor_semantic_result=clarified_frontdoor_semantic_result,
				frontdoor_contract=clarified_frontdoor_contract,
				frontdoor_render_result=clarified_frontdoor_render_result,
				frontdoor_answer=clarified_frontdoor_answer,
				context_force_new_query=False,
				latest_grounded_turn_available=latest_grounded_turn_available,
				latest_grounded_turn=latest_grounded_turn,
				append_message=_append_message,
				append_tool_payload=_append_tool_payload,
				append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
				assistant_text_payload=_assistant_text_payload,
				store_pending_clarification_signal=store_pending_clarification_signal,
				save_session=_save_session,
				raw_message=raw_msg,
				clarification_response_contract=clarification_response_contract,
			)
			if frontdoor_handled and frontdoor_payload is not None:
				return True, frontdoor_payload
	compiled_rollout = _compiled_first_turn_rollout_decision(
		session_name=session_name,
		user=user,
		site_name=site_name,
	)
	if bool(compiled_rollout.get("enabled")) and not latest_grounded_turn_available and entity_drilldown is None:
		return handle_compiled_query_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			raw_message=raw_msg,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			clarification_response_contract=clarification_response_contract,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			handle_compiled_first_turn_result=_handle_compiled_first_turn_result,
		)
	followup_context_available = bool(latest_grounded_turn_available and not bool(context_isolation.force_new_query) and entity_drilldown is None)
	pre_reasoning_followup_resolution = None
	reasoning_preempted_by_artifact_refinement = False
	precomputed_evidence_answer = ""
	precomputed_evidence_response: Dict[str, Any] = {}
	precomputed_evidence_boundary_answer = ""
	if followup_context_available:
		pre_reasoning_followup_resolution = build_followup_resolution(
			request_id=request_id,
			message=msg,
			latest_grounded_turn_available=True,
			latest_grounded_turn=latest_grounded_turn,
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=False,
			degraded_reason=str(context_isolation.reason or degraded_reason or "").strip(),
		)
		reasoning_preempted_by_artifact_refinement = _reasoning_preempted_by_followup_refinement(
			pre_reasoning_followup_resolution
		)
		precomputed_evidence_answer = _grounded_artifact_direct_evidence_answer(
			raw_message=msg,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
		)
		if not precomputed_evidence_answer:
			precomputed_evidence_boundary_answer = _grounded_artifact_evidence_boundary_answer(
				raw_message=msg,
				artifact_payload=latest_family_artifact,
				grounded_turn=latest_grounded_turn,
			)
	reasoning_display_preferences = _latest_display_preferences(
		session_doc,
		[
			str(mode or "").strip()
			for mode in (getattr(pre_reasoning_followup_resolution, "requested_modes", []) or [])
			if str(mode or "").strip()
		],
	)
	if (
		bool(reasoning_rollout.get("enabled"))
		and latest_grounded_turn_available
		and not bool(context_isolation.force_new_query)
		and entity_drilldown is None
		and not reasoning_preempted_by_artifact_refinement
		and not precomputed_evidence_answer
		and not precomputed_evidence_boundary_answer
	):
		reasoning_activation_contract = (
			pre_frontdoor_reasoning_activation_contract
			if pre_frontdoor_reasoning_activation_contract is not None
			else build_reasoning_activation_contract(
				request_id=request_id,
				session_id=session_name,
				message=msg,
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				response_policy_contract=provisional_response_policy_contract.to_payload(),
			)
		)
		reasoning_semantic_result = (
			pre_frontdoor_reasoning_semantic_result
			if pre_frontdoor_reasoning_semantic_result is not None
			else interpret_reasoning_activation_semantically(
				request_id=request_id,
				session_id=session_name,
				user_id=user,
				site_name=site_name,
				message=msg,
				recent_messages=reasoning_recent_messages,
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				activation_contract=reasoning_activation_contract.to_payload(),
				prior_reasoning_contract=latest_reasoning_contract,
			)
		)
		reasoning_handled, reasoning_payload = handle_reasoning_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			message=msg,
			raw_message=raw_msg,
			reasoning_recent_messages=reasoning_recent_messages,
			reasoning_display_preferences=reasoning_display_preferences,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			clarification_response_contract=clarification_response_contract,
			provisional_response_policy_contract=provisional_response_policy_contract,
			reasoning_activation_contract=reasoning_activation_contract,
			reasoning_semantic_result=reasoning_semantic_result,
			latest_grounded_turn=latest_grounded_turn,
			latest_family_artifact=latest_family_artifact,
			latest_assistant_payload=latest_assistant_payload,
			latest_reasoning_contract=latest_reasoning_contract,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
			phase6_execution_event_level=_phase6_execution_event_level,
		)
		if reasoning_handled and reasoning_payload is not None:
			return True, reasoning_payload
	if entity_drilldown is not None:
		entity_drilldown_requires_grounded_turn = bool(
			latest_grounded_turn_available and str((entity_drilldown or {}).get("source") or "").strip() != "explicit_identifier"
		)
		followup_resolution = build_followup_resolution_contract(
			request_id=request_id,
			mode="entity_drilldown",
			requested_modes=["entity_drilldown"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=entity_drilldown_requires_grounded_turn,
			self_contained=not entity_drilldown_requires_grounded_turn,
			latest_grounded_turn_available=latest_grounded_turn_available,
			reason=(
				"The request drills into an explicitly referenced governed entity."
				if not entity_drilldown_requires_grounded_turn
				else "The request drills into a governed entity from the latest grounded artifact."
			),
		)
	else:
		followup_resolution = build_followup_resolution(
			request_id=request_id,
			message=msg,
			latest_grounded_turn_available=followup_context_available,
			latest_grounded_turn=latest_grounded_turn if followup_context_available else {},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=allow_heuristic_fallback if followup_context_available else True,
			degraded_reason=str(context_isolation.reason or degraded_reason or "").strip(),
		)
	family_artifact_for_requery = _latest_normalized_family_artifact(session_doc) if followup_context_available else {}
	provisional_continuation_contract = None
	if followup_context_available:
		provisional_continuation_contract = build_artifact_continuation_contract(
			request_id=request_id,
			followup_resolution=followup_resolution,
			grounded_turn=latest_grounded_turn,
			artifact_payload=family_artifact_for_requery,
		)
		followup_resolution = _authoritative_continuation_resolution(
			request_id=request_id,
			followup_resolution=followup_resolution,
			continuation_contract=provisional_continuation_contract,
			artifact_payload=family_artifact_for_requery,
			grounded_turn=latest_grounded_turn,
		)
	requery_upgrade, enrichment_compatibility_contract = _requery_resolution_for_unsupported_local_columns(
		request_id=request_id,
		followup_resolution=followup_resolution,
		artifact_payload=family_artifact_for_requery,
		grounded_turn=latest_grounded_turn if followup_context_available else {},
		continuation_contract=provisional_continuation_contract,
	)
	if requery_upgrade is not None:
		followup_resolution = requery_upgrade
	provisional_scope_decision_contract = build_governed_scope_decision_contract(
		request_id=request_id,
		stage="followup_orchestration",
		followup_resolution=followup_resolution,
		context_isolation=context_isolation,
		latest_grounded_turn_available=latest_grounded_turn_available,
		entity_drilldown=entity_drilldown,
		continuation_contract=provisional_continuation_contract,
		clarification_required=False,
	)
	if entity_drilldown is None:
		followup_resolution = coerce_followup_resolution_from_scope_decision(
			request_id=request_id,
			followup_resolution=followup_resolution,
			scope_decision_contract=provisional_scope_decision_contract,
		)
	continuation_contract = None
	if followup_context_available:
		continuation_contract = build_artifact_continuation_contract(
			request_id=request_id,
			followup_resolution=followup_resolution,
			grounded_turn=latest_grounded_turn,
			artifact_payload=family_artifact_for_requery,
		)
	scope_decision_contract = build_governed_scope_decision_contract(
		request_id=request_id,
		stage="followup_orchestration",
		followup_resolution=followup_resolution,
		context_isolation=context_isolation,
		latest_grounded_turn_available=latest_grounded_turn_available,
		entity_drilldown=entity_drilldown,
		continuation_contract=continuation_contract,
		clarification_required=False,
	)
	response_policy_contract = build_response_policy_contract(
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
	)
	if precomputed_evidence_answer:
		precomputed_evidence_response = _grounded_artifact_direct_evidence_response(
			request_id=request_id,
			session_id=session_name,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			raw_message=msg,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
			fallback_answer_text=precomputed_evidence_answer,
		)
	recent_messages = (
		[]
		if governed_scope_decision_requires_fresh_query(scope_decision_contract)
		else _recent_messages(session_doc, limit=10)
	)
	runtime_message = msg
	if followup_resolution.mode == "capability_requery":
		runtime_message = _compile_capability_requery_message(
			session_doc,
			raw_message=raw_msg,
			followup_resolution=followup_resolution,
			grounded_turn=latest_grounded_turn,
			continuation_contract=continuation_contract,
		)
		recent_messages = []

	if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
		session_doc.title = (raw_msg[:60] + "…") if len(raw_msg) > 60 else raw_msg

	_append_message(session_doc, "user", raw_msg)
	_append_tool_payload(session_doc, interaction_contract.to_payload())
	_append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
	_append_tool_payload(session_doc, frontdoor_contract.to_payload())
	if clarification_response_contract is not None:
		_append_tool_payload(session_doc, clarification_response_contract.to_payload())
	_append_tool_payload(session_doc, response_policy_contract.to_payload())
	if isinstance(semantic_payload, dict):
		_append_tool_payload(session_doc, semantic_payload)
	if governed_scope_decision_requires_fresh_query(scope_decision_contract):
		_append_tool_payload(
			session_doc,
			_context_isolation_payload(
				request_id=request_id,
				decision=governed_scope_decision_public_decision(scope_decision_contract),
			),
		)
	_append_tool_payload(session_doc, followup_resolution.to_payload())
	if continuation_contract is not None:
		_append_tool_payload(session_doc, continuation_contract.to_payload())
	if enrichment_compatibility_contract is not None:
		_append_tool_payload(session_doc, enrichment_compatibility_contract.to_payload())
	_append_tool_payload(session_doc, scope_decision_contract.to_payload())

	if governed_scope_decision_is_out_of_scope(scope_decision_contract) and entity_drilldown is None:
		boundary_started_at = time.perf_counter()
		legacy_out_of_scope_answer = _out_of_scope_answer(msg, governed_scope_decision_public_decision(scope_decision_contract))
		execution_path = ExecutionPath(
			request_id=request_id,
			path="unsupported_domain",
			reason=str(getattr(scope_decision_contract, "reason", "") or "").strip() or "The request is outside the current governed ERP scope.",
			requires_runtime=False,
			grounded_required=False,
		)
		boundary_payload = _append_knowledge_boundary_contract(
			session_doc,
			request_id=request_id,
			session_id=session_name,
			proposed_lane="artifact_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			governed_scope_contract=scope_decision_contract.to_payload(),
			grounded_turn=latest_grounded_turn,
		)
		answer_text = render_knowledge_boundary_answer(
			boundary_contract=boundary_payload,
			detail_answer=legacy_out_of_scope_answer,
		)
		_append_knowledge_boundary_observability(
			session_doc,
			request_id=request_id,
			session_id=session_name,
			boundary_payload=boundary_payload,
			latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
		)
		_append_tool_payload(session_doc, execution_path.to_payload())
		_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))
		_append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={},
				grounded_turn_context={},
				answer_text=answer_text,
			).to_payload(),
		)
		_save_session(session_doc, ignore_permissions=False)
		return True, {"ok": True, "request_id": request_id, "mode": "out_of_scope_domain", "agent_meta": {"engine": "local_governed_scope_guard"}}

	local_transform = None
	if followup_resolution.mode == "local_grounded_transform" and not precomputed_evidence_answer and not precomputed_evidence_boundary_answer:
		local_transform = _try_local_followup_transform(
			session_doc,
			request_id=request_id,
			raw_message=msg,
			followup_resolution=followup_resolution,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			continuation_contract=continuation_contract,
		)
	if local_transform:
		_append_knowledge_boundary_contract(
			session_doc,
			request_id=request_id,
			session_id=session_name,
			proposed_lane="artifact_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			governed_scope_contract=scope_decision_contract.to_payload(),
			grounded_turn=latest_grounded_turn,
		)
		execution_path = build_execution_path(
			request_id=request_id,
			followup_resolution=followup_resolution,
			local_transform_applied=True,
		)
		_append_tool_payload(
			session_doc,
			execution_path.to_payload(),
		)
		_append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload=_latest_qwen_trace_payload(session_doc),
				grounded_turn_context=latest_grounded_turn,
				answer_text=str(_latest_assistant_payload(session_doc).get("text") or ""),
			).to_payload(),
		)
		_save_session(session_doc, ignore_permissions=False)
		return local_transform

	skip_artifact_boundary_for_self_contained_breakout = bool(
		governed_scope_decision_requires_fresh_query(scope_decision_contract)
		and _message_looks_like_self_contained_governed_business_query(
			message=msg,
			language=interaction_contract.detected_language,
		)
		and not _message_has_grounded_context_anchor(msg)
	)
	if entity_drilldown is None and not skip_artifact_boundary_for_self_contained_breakout:
		artifact_boundary_handled, artifact_boundary_payload = handle_artifact_boundary_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			message=msg,
			followup_resolution=followup_resolution,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			frontdoor_contract=frontdoor_contract,
			scope_decision_contract=scope_decision_contract,
			latest_family_artifact=latest_family_artifact,
			latest_grounded_turn=latest_grounded_turn,
			enrichment_compatibility_contract=enrichment_compatibility_contract,
			grounded_artifact_direct_evidence_response=_grounded_artifact_direct_evidence_response,
			grounded_artifact_direct_evidence_answer=_grounded_artifact_direct_evidence_answer,
			grounded_artifact_evidence_boundary_answer=_grounded_artifact_evidence_boundary_answer,
			artifact_enrichment_boundary_answer=_artifact_enrichment_boundary_answer,
			append_grounded_evidence_recovery_contract=_append_grounded_evidence_recovery_contract,
			append_enrichment_recovery_contract=_append_enrichment_recovery_contract,
			session_tool_payloads=_session_tool_payloads,
			latest_tool_payload_by_type=_latest_tool_payload_by_type,
			append_artifact_boundary_observability=_append_artifact_boundary_observability,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			append_tool_payload=_append_tool_payload,
			append_message=_append_message,
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
			precomputed_evidence_response=precomputed_evidence_response,
			precomputed_evidence_answer=precomputed_evidence_answer,
			precomputed_evidence_boundary_answer=precomputed_evidence_boundary_answer,
		)
		if artifact_boundary_handled and artifact_boundary_payload is not None:
			return True, artifact_boundary_payload

	if followup_resolution.mode == "entity_drilldown" and entity_drilldown is not None:
		entity_handled, entity_payload = handle_entity_drilldown_turn(
			session_doc=session_doc,
			request_id=request_id,
			session_id=session_name,
			message=msg,
			entity_reference=entity_drilldown,
			followup_resolution=followup_resolution,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			frontdoor_contract=frontdoor_contract,
			scope_decision_contract=scope_decision_contract,
			latest_grounded_turn=latest_grounded_turn,
			try_entity_detail_followup=_try_entity_detail_followup,
			append_tool_payload=_append_tool_payload,
			append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
			build_latest_grounded_turn_contract=_latest_grounded_turn_contract,
			build_latest_qwen_trace_payload=_latest_qwen_trace_payload,
			build_latest_assistant_payload=_latest_assistant_payload,
			save_session=_save_session,
		)
		if entity_handled and entity_payload is not None:
			return True, entity_payload

	execution_path = build_execution_path(
		request_id=request_id,
		followup_resolution=followup_resolution,
		local_transform_applied=False,
	)
	_append_tool_payload(
		session_doc,
		execution_path.to_payload(),
	)
	runtime_gate_handled, runtime_gate_payload, compiled_rollout_fallback = handle_runtime_gate_turn(
		session_doc=session_doc,
		request_id=request_id,
		session_id=session_name,
		user_id=user,
		site_name=site_name,
		message=runtime_message,
		raw_message=msg,
		latest_grounded_turn_available=latest_grounded_turn_available,
		latest_grounded_turn=latest_grounded_turn,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		interaction_contract=interaction_contract,
		frontdoor_contract=frontdoor_contract,
		clarification_response_contract=clarification_response_contract,
		scope_decision_contract=scope_decision_contract,
		compiled_rollout=compiled_rollout,
		append_tool_payload=_append_tool_payload,
		append_message=_append_message,
		append_knowledge_boundary_contract=_append_knowledge_boundary_contract,
		append_knowledge_boundary_observability=_append_knowledge_boundary_observability,
		append_compiled_attempt_artifacts=_append_compiled_attempt_artifacts,
		compiled_rollout_fallback_eligible=_compiled_rollout_fallback_eligible,
		compiled_rollout_fallback_reason=_compiled_rollout_fallback_reason,
		compiled_rollout_fallback_payload=_compiled_rollout_fallback_payload,
		handle_compiled_first_turn_result=_handle_compiled_first_turn_result,
		out_of_scope_answer=_out_of_scope_answer,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
	)
	if runtime_gate_handled and runtime_gate_payload is not None:
		return True, runtime_gate_payload
	return handle_legacy_runtime_turn(
		session_doc=session_doc,
		request_id=request_id,
		session_id=session_name,
		user_id=user,
		site_name=site_name,
		message=runtime_message,
		recent_messages=recent_messages,
		response_policy_contract=response_policy_contract,
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=execution_path,
		compiled_rollout_fallback=compiled_rollout_fallback,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
		tool_trace_payload=_tool_trace_payload,
		tool_trace_message=_tool_trace_message,
		safe_runtime_failure_message=_safe_runtime_failure_message,
		latest_qwen_trace_payload=_latest_qwen_trace_payload,
		latest_assistant_payload=_latest_assistant_payload,
		latest_normalized_family_artifact=_latest_normalized_family_artifact,
	)


def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_smoke_helper()


def run_phase4_compiled_rollout_governance_selftests() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_governance_selftests_helper()


def summarize_compiled_first_turn_audits(
	limit_sessions: int = 50,
	limit_audits: int = 200,
	session_names: List[str] | None = None,
) -> Dict[str, Any]:
	return _summarize_compiled_first_turn_audits_helper(
		limit_sessions=limit_sessions,
		limit_audits=limit_audits,
		session_names=session_names,
	)


def run_phase4_compiled_rollout_monitoring_smoke() -> Dict[str, Any]:
	return _run_phase4_compiled_rollout_monitoring_smoke_helper()


def run_first_turn_regression_suite(messages: List[str] | None = None) -> Dict[str, Any]:
	return _run_first_turn_regression_suite_helper(messages=messages)


def run_same_session_fresh_query_regression_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	return _run_same_session_fresh_query_regression_smoke_helper(messages=messages)


def run_phase4b_followup_fidelity_smoke() -> Dict[str, Any]:
	return _run_followup_fidelity_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase4b_transaction_listing_smoke() -> Dict[str, Any]:
	return _run_transaction_listing_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_listing_smoke() -> Dict[str, Any]:
	return _run_delivery_note_listing_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_listing_limit_probe() -> Dict[str, Any]:
	return _run_delivery_note_listing_limit_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_detail_smoke() -> Dict[str, Any]:
	return _run_delivery_note_detail_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_2_sales_order_detail_smoke() -> Dict[str, Any]:
	return _run_sales_order_detail_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_2_sales_order_status_followup_smoke() -> Dict[str, Any]:
	return _run_sales_order_status_followup_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_3_purchase_order_listing_smoke() -> Dict[str, Any]:
	return _run_purchase_order_listing_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_3_purchase_order_status_scope_reset_smoke() -> Dict[str, Any]:
	return _run_purchase_order_status_scope_reset_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_3_purchase_order_detail_smoke() -> Dict[str, Any]:
	return _run_purchase_order_detail_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_3_purchase_order_status_followup_smoke() -> Dict[str, Any]:
	return _run_purchase_order_status_followup_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_exposure_smoke() -> Dict[str, Any]:
	return _run_customer_credit_exposure_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_overdue_smoke() -> Dict[str, Any]:
	return _run_customer_credit_overdue_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_overdue_probe() -> Dict[str, Any]:
	return _run_customer_credit_overdue_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_balance_smoke() -> Dict[str, Any]:
	return _run_customer_credit_balance_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_detail_followup_smoke() -> Dict[str, Any]:
	return _run_customer_credit_detail_followup_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_policy_followup_smoke() -> Dict[str, Any]:
	return _run_customer_credit_policy_followup_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_balance_probe() -> Dict[str, Any]:
	return _run_customer_credit_balance_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_scope_reset_smoke() -> Dict[str, Any]:
	return _run_customer_credit_scope_reset_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_4_customer_credit_scope_reset_probe() -> Dict[str, Any]:
	return _run_customer_credit_scope_reset_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
		latest_qwen_trace_payload=_latest_qwen_trace_payload,
		latest_grounded_turn_contract=_latest_grounded_turn_contract,
	)


def run_phase2_4_governed_kpi_frontdoor_smoke() -> Dict[str, Any]:
	return _run_governed_kpi_frontdoor_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase2_4_governed_kpi_frontdoor_probe() -> Dict[str, Any]:
	return _run_governed_kpi_frontdoor_probe_helper()


def run_phase2_5_governed_kpi_period_execution_smoke() -> Dict[str, Any]:
	return _run_governed_kpi_period_execution_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase2_5_governed_kpi_period_execution_probe() -> Dict[str, Any]:
	return _run_governed_kpi_period_execution_probe_helper()


def run_phase2_5_governed_kpi_customer_execution_smoke() -> Dict[str, Any]:
	return _run_governed_kpi_customer_execution_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase2_5_governed_kpi_customer_execution_probe() -> Dict[str, Any]:
	return _run_governed_kpi_customer_execution_probe_helper()


def run_phase1_1_delivery_note_date_scope_probe() -> Dict[str, Any]:
	return _run_delivery_note_date_scope_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_date_scope_smoke() -> Dict[str, Any]:
	return _run_delivery_note_date_scope_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_status_probe() -> Dict[str, Any]:
	return _run_delivery_note_status_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_status_smoke() -> Dict[str, Any]:
	return _run_delivery_note_status_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_session_reset_smoke() -> Dict[str, Any]:
	return _run_delivery_note_session_reset_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_delivery_note_invoice_switch_debug() -> Dict[str, Any]:
	return _run_phase1_1_delivery_note_invoice_switch_debug_helper()


def run_phase1_1_invoice_detail_delivery_trend_debug() -> Dict[str, Any]:
	return _run_phase1_1_invoice_detail_delivery_trend_debug_helper()


def run_phase1_1_invoice_detail_delivery_trend_smoke() -> Dict[str, Any]:
	return run_phase1_1_invoice_detail_delivery_trend_debug()


def run_phase1_1_delivery_note_trend_probe() -> Dict[str, Any]:
	return _run_delivery_note_trend_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_1_delivery_note_trend_smoke() -> Dict[str, Any]:
	return _run_delivery_note_trend_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
		expected_series_column="Delivered Quantity",
	)


def run_phase1_1_delivery_note_last_year_trend_smoke() -> Dict[str, Any]:
	return _run_delivery_note_trend_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
		message="show monthly delivery note trend by customer last year",
		expected_title_fragment="Trend",
		expected_series_column="Delivered Quantity",
		expected_summary_metric="Total Delivered Quantity",
		minimum_summary_value=1,
	)


def _latest_tool_payload_by_type(tool_payloads: List[Dict[str, Any]], payload_type: str) -> Dict[str, Any]:
	for item in reversed(tool_payloads):
		if str(item.get("type") or "").strip() == str(payload_type or "").strip():
			return item
	return {}


def _run_family_evaluation_case(*, case: Dict[str, Any], user: str = "Administrator") -> Dict[str, Any]:
	return _run_family_evaluation_case_helper(
		case=case,
		user=user,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		parse_payload=_parse_payload,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		case_latency_budget_assessment=_case_latency_budget_assessment,
	)


def run_phase4b_family_evaluation_suite(set_id: str = "core_governed_families") -> Dict[str, Any]:
	return _run_family_evaluation_suite_helper(
		set_id=set_id,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		list_family_evaluation_case_sets=list_family_evaluation_case_sets,
		get_family_evaluation_case_set=get_family_evaluation_case_set,
		run_family_evaluation_case=lambda **kwargs: _run_family_evaluation_case(**kwargs),
		summarize_compiled_first_turn_audits=summarize_compiled_first_turn_audits,
		family_latency_budget_summary=_family_latency_budget_summary,
		get_compiled_first_turn_rollout_status=get_compiled_first_turn_rollout_status,
	)


def run_phase4b_family_evaluation_smoke(set_id: str = "core_governed_families") -> Dict[str, Any]:
	return _run_family_evaluation_smoke_helper(
		set_id=set_id,
		run_family_evaluation_suite=run_phase4b_family_evaluation_suite,
	)


def run_phase4b_full_family_evaluation_suite() -> Dict[str, Any]:
	return _run_full_family_evaluation_suite_helper(
		list_family_evaluation_case_sets=list_family_evaluation_case_sets,
		run_family_evaluation_suite=run_phase4b_family_evaluation_suite,
		family_latency_budget_summary=_family_latency_budget_summary,
	)


def run_phase4b_full_family_evaluation_smoke() -> Dict[str, Any]:
	return _run_full_family_evaluation_smoke_helper(
		run_full_family_evaluation_suite=run_phase4b_full_family_evaluation_suite,
	)


def run_phase4b_family_latency_budget_report(set_id: str = "") -> Dict[str, Any]:
	return _build_family_latency_budget_report_helper(
		set_id=set_id,
		run_family_evaluation_suite=run_phase4b_family_evaluation_suite,
		run_full_family_evaluation_suite=run_phase4b_full_family_evaluation_suite,
	)


def run_phase4b_family_latency_budget_smoke() -> Dict[str, Any]:
	return _run_family_latency_budget_smoke_helper(
		run_family_latency_budget_report=run_phase4b_family_latency_budget_report,
	)


def run_phase4b_family_tool_surface_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	return _run_family_tool_surface_smoke_helper(
		messages=messages,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		build_family_tool_surface_for_message=build_family_tool_surface_for_message,
		handle_qwen_user_message=handle_qwen_user_message,
		parse_payload=_parse_payload,
	)


def run_phase4b_family_tool_surface_probe() -> Dict[str, Any]:
	return _run_family_tool_surface_probe_helper(
		build_family_tool_surface_for_message=build_family_tool_surface_for_message,
	)


def run_phase4b_clarification_translation_probe() -> Dict[str, Any]:
	return _run_clarification_translation_probe_helper(
		translate_clarification_signal=translate_clarification_signal,
	)


def run_phase4b_response_policy_probe() -> Dict[str, Any]:
	return _run_response_policy_probe_helper(
		build_interaction_contract=build_interaction_contract,
		build_response_policy_contract=build_response_policy_contract,
	)


def run_phase4b_clarification_policy_smoke() -> Dict[str, Any]:
	return _run_clarification_policy_smoke_helper(
		translate_clarification_signal=translate_clarification_signal,
		build_interaction_contract=build_interaction_contract,
		build_response_policy_contract=build_response_policy_contract,
	)


def run_phase4b_natural_narrative_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	return _run_natural_narrative_smoke_helper(
		messages=messages,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		parse_payload=_parse_payload,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
		assistant_text_payload=_assistant_text_payload,
	)


def run_phase4b_structured_presentation_smoke() -> Dict[str, Any]:
	return _run_structured_presentation_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase4b_context_isolation_smoke() -> Dict[str, Any]:
	return _run_context_isolation_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase4b_entity_drilldown_smoke() -> Dict[str, Any]:
	return _run_entity_drilldown_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase1_1_invoice_delivery_proof_smoke() -> Dict[str, Any]:
	return _run_invoice_delivery_proof_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase1_1_fresh_chat_invoice_delivery_proof_smoke() -> Dict[str, Any]:
	return _run_fresh_chat_invoice_delivery_proof_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase4b_followup_report_ambiguity_smoke() -> Dict[str, Any]:
	return _run_followup_report_ambiguity_smoke_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase4b_entity_drilldown_probe() -> Dict[str, Any]:
	return _run_entity_drilldown_probe_helper(
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		parse_payload=_parse_payload,
		latest_qwen_trace_payload=_latest_qwen_trace_payload,
		latest_grounded_turn_contract=_latest_grounded_turn_contract,
		latest_normalized_family_artifact=_latest_normalized_family_artifact,
	)


def _run_phase55_smoke_session(title: str, runner: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
	return _run_phase55_smoke_session_helper(
		title,
		runner,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
	)


def _run_phase6_smoke_session(title: str, runner: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
	return _run_phase6_smoke_session_helper(
		title,
		runner,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
	)


def run_phase55_clarification_attempt_smoke() -> Dict[str, Any]:
	return _run_phase55_clarification_attempt_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		get_clarification_state=get_clarification_state,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase55_clarification_meta_question_smoke() -> Dict[str, Any]:
	return _run_phase55_clarification_meta_question_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		get_clarification_state=get_clarification_state,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase55_pending_override_smoke() -> Dict[str, Any]:
	return _run_phase55_pending_override_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		get_clarification_state=get_clarification_state,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase55_frontdoor_boundary_smoke() -> Dict[str, Any]:
	return _run_phase55_frontdoor_boundary_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		get_clarification_state=get_clarification_state,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase55_ap_ar_default_policy_smoke() -> Dict[str, Any]:
	return _run_phase55_ap_ar_default_policy_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		get_clarification_state=get_clarification_state,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase55_hardening_suite() -> Dict[str, Any]:
	return _run_phase55_hardening_suite_helper(
		clarification_attempt_smoke=run_phase55_clarification_attempt_smoke,
		clarification_meta_question_smoke=run_phase55_clarification_meta_question_smoke,
		pending_override_smoke=run_phase55_pending_override_smoke,
		frontdoor_boundary_smoke=run_phase55_frontdoor_boundary_smoke,
		ap_ar_default_policy_smoke=run_phase55_ap_ar_default_policy_smoke,
		observability_smoke=run_phase55_observability_smoke,
	)


def run_phase55_observability_smoke() -> Dict[str, Any]:
	return _run_phase55_observability_smoke_helper(
		run_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase6_reasoning_live_rollout_smoke() -> Dict[str, Any]:
	return run_phase6_reasoning_live_debug()


def run_phase6_reasoning_without_grounding_smoke() -> Dict[str, Any]:
	return _run_phase6_reasoning_without_grounding_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase6_reasoning_frontdoor_boundary_smoke() -> Dict[str, Any]:
	return _run_phase6_reasoning_frontdoor_boundary_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase6_nonadvisory_recommendation_boundary_smoke() -> Dict[str, Any]:
	return _run_phase6_nonadvisory_recommendation_boundary_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		latest_assistant_payload=_latest_assistant_payload,
	)


def run_phase6_artifact_refinement_precedence_smoke() -> Dict[str, Any]:
	return _run_phase6_artifact_refinement_precedence_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase6_continuation_fulfillment_smoke() -> Dict[str, Any]:
	return _run_phase6_continuation_fulfillment_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
	)


def run_phase6_grounded_source_reset_smoke() -> Dict[str, Any]:
	return _run_phase6_grounded_source_reset_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase6_observability_smoke() -> Dict[str, Any]:
	return _run_phase6_observability_smoke_helper(
		run_phase6_smoke_session=_run_phase6_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase6_hardening_suite() -> Dict[str, Any]:
	return _run_phase6_hardening_suite_helper(
		recommendation_policy_probe=run_phase6a_recommendation_policy_probe,
		reasoning_live_rollout_smoke=run_phase6_reasoning_live_rollout_smoke,
		reasoning_without_grounding_smoke=run_phase6_reasoning_without_grounding_smoke,
		reasoning_frontdoor_boundary_smoke=run_phase6_reasoning_frontdoor_boundary_smoke,
		nonadvisory_recommendation_boundary_smoke=run_phase6_nonadvisory_recommendation_boundary_smoke,
		artifact_refinement_precedence_smoke=run_phase6_artifact_refinement_precedence_smoke,
		continuation_fulfillment_smoke=run_phase6_continuation_fulfillment_smoke,
		grounded_source_reset_smoke=run_phase6_grounded_source_reset_smoke,
		continuation_guardrail_smoke=run_phase6d_reasoning_continuation_guardrail_smoke,
		observability_smoke=run_phase6_observability_smoke,
	)


def run_phase7_hardening_suite() -> Dict[str, Any]:
	return _run_phase7_hardening_suite_helper(
		live_boundary_orchestration_smoke=run_phase7c_live_boundary_orchestration_smoke,
		boundary_response_live_smoke=run_phase7d_boundary_response_live_smoke,
	)


def run_phase6_reasoning_live_debug() -> Dict[str, Any]:
	flag_key = "qwen_enable_erp_business_reasoning"
	percent_key = "qwen_erp_business_reasoning_rollout_percentage"
	users_key = "qwen_erp_business_reasoning_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]

		def _runner(doc) -> Dict[str, Any]:
			ok, first_payload = handle_qwen_user_message(
				session_name=doc.name,
				message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Phase 6 live reasoning debug failed: first turn did not complete.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
			latest_family_artifact = _latest_normalized_family_artifact(session_doc, grounded_turn=latest_grounded_turn)
			latest_assistant_payload = _latest_assistant_payload(session_doc)
			request_id = "phase6-debug"
			interaction_contract = build_interaction_contract(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				raw_message="what does this mean",
			)
			response_policy_contract = build_response_policy_contract(
				interaction_contract=interaction_contract,
			)
			activation = build_reasoning_activation_contract(
				request_id=request_id,
				session_id=doc.name,
				message="what does this mean",
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				response_policy_contract=response_policy_contract.to_payload(),
			)
			semantic = interpret_reasoning_activation_semantically(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				message="what does this mean",
				recent_messages=_recent_messages(session_doc, limit=8),
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				activation_contract=activation.to_payload(),
			)
			direct_execution = execute_erp_business_reasoning(
				request_id=request_id,
				session_id=doc.name,
				user_id="Administrator",
				message="what does this mean",
				recent_messages=_recent_messages(session_doc, limit=10),
				activation_contract=activation.to_payload(),
				semantic_activation_result=semantic.to_payload(),
				latest_grounded_turn=latest_grounded_turn,
				latest_family_artifact=latest_family_artifact,
				latest_assistant_payload=latest_assistant_payload,
				prior_reasoning_contract=_latest_reasoning_contract(session_doc),
				prior_answer_text=str(latest_assistant_payload.get("text") or "").strip(),
			)
			ok2, second_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="what does this mean",
				user="Administrator",
			)
			second_payload_summary = {
				"request_id": str((second_payload or {}).get("request_id") or "").strip(),
				"mode": str((second_payload or {}).get("mode") or "").strip(),
				"family_validation_status": str((second_payload or {}).get("family_validation_status") or "").strip(),
				"semantic_validation_status": str((second_payload or {}).get("semantic_validation_status") or "").strip(),
				"agent_meta": dict(((second_payload or {}).get("agent_meta") or {})),
			}
			return {
				"ok": True,
				"rollout": _erp_business_reasoning_rollout_decision(
					session_name=doc.name,
					user="Administrator",
					site_name=str(getattr(getattr(frappe, "local", None), "site", "") or "").strip(),
				),
				"first_payload": first_payload,
				"activation": activation.to_payload(),
				"semantic": semantic.to_payload(),
				"direct_execution": direct_execution.to_payload(),
				"second_ok": ok2,
				"second_payload": second_payload_summary,
				"latest_assistant_payload": _latest_assistant_payload(frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)),
			}

		return _run_phase55_smoke_session("Phase 6 Live Reasoning Debug", _runner)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase7c_live_boundary_orchestration_smoke() -> Dict[str, Any]:
	return _run_phase7_live_boundary_orchestration_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase7d_boundary_response_live_smoke() -> Dict[str, Any]:
	return _run_phase7_boundary_response_live_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		latest_grounded_turn_contract=_latest_grounded_turn_contract,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase7_observability_smoke() -> Dict[str, Any]:
	return _run_phase7_observability_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		latest_grounded_turn_contract=_latest_grounded_turn_contract,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase8b_recovery_authority_smoke() -> Dict[str, Any]:
	return _run_phase8_recovery_authority_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		build_followup_resolution_contract=build_followup_resolution_contract,
		append_grounded_evidence_recovery_contract=_append_grounded_evidence_recovery_contract,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
	)


def run_phase8_recovery_guidance_observability_smoke() -> Dict[str, Any]:
	return _run_phase8_recovery_guidance_observability_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase8_evidence_boundary_observability_smoke() -> Dict[str, Any]:
	return _run_phase8_evidence_boundary_observability_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase8_enrichment_boundary_observability_smoke() -> Dict[str, Any]:
	return _run_phase8_enrichment_boundary_observability_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		session_tool_payloads=_session_tool_payloads,
	)


def run_phase8c_repair_handling_smoke() -> Dict[str, Any]:
	return _run_phase8_repair_handling_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase8c_repair_handling_debug() -> Dict[str, Any]:
	def _seed_recovery_session(doc) -> None:
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="phase8c-debug-recovery",
			session_id=doc.name,
			source_request_id="phase8c-debug-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "phase8c-debug-grounded-request",
			"trace_request_id": "phase8c-debug-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"I can't safely add quantity to the current ranking, but I can run the governed Top Customers by Quantity report for last month."
			),
		)
		_append_tool_payload(doc, grounded_turn_payload)
		_append_tool_payload(doc, recovery_payload)
		_save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		_seed_recovery_session(doc)
		fixture_id = "product_recovery_flow"
		ok, guidance_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "guidance"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8C repair debug failed on guidance turn.")
		ok, accepted_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8C repair debug failed on accepted recovery turn.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = _session_tool_payloads(session_doc)
		return {
			"ok": True,
			"guidance_mode": str((guidance_payload or {}).get("mode") or "").strip(),
			"accepted_mode": str((accepted_payload or {}).get("mode") or "").strip(),
			"assistant_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
			"repair_contract": _latest_tool_payload_by_type(tool_payloads, "qwen_conversational_repair_intent_contract"),
			"followup_resolution": _latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution_contract"),
			"compiled_audit": _latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract"),
			"rendered_family_response": _latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract"),
		}

	return _run_phase55_smoke_session("Phase 8C Repair Handling Debug", _runner)


def run_phase8d_fresh_query_override_smoke() -> Dict[str, Any]:
	return _run_phase8_fresh_query_override_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		build_artifact_enrichment_recovery_contract=build_artifact_enrichment_recovery_contract,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		save_session=_save_session,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase8_recovery_execution_smoke() -> Dict[str, Any]:
	return _run_phase8_recovery_execution_smoke_helper(
		run_phase55_smoke_session=_run_phase55_smoke_session_helper,
		frappe_module=frappe,
		session_doctype=QWEN_SESSION_DOCTYPE,
		handle_qwen_user_message=handle_qwen_user_message,
		latest_assistant_payload=_latest_assistant_payload,
		session_tool_payloads=_session_tool_payloads,
		latest_tool_payload_by_type=_latest_tool_payload_by_type,
	)


def run_phase8_recovery_execution_debug() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		fixture_id = "product_recovery_flow"
		fixture = require_smoke_fixture(fixture_id)
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery debug failed on initial products ranking request.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "qty_enrichment"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Phase 8 recovery debug failed on quantity enrichment request.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = _session_tool_payloads(session_doc)
		return {
			"ok": True,
			"first_mode": str((first_payload or {}).get("mode") or "").strip(),
			"first_assistant_text": first_assistant_text,
			"mode": str((second_payload or {}).get("mode") or "").strip(),
			"assistant_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
			"recent_tool_types": [str(item.get("type") or "").strip() for item in tool_payloads[-20:]],
			"followup_resolution": _latest_tool_payload_by_type(tool_payloads, "qwen_followup_resolution_contract"),
			"continuation_contract": _latest_tool_payload_by_type(tool_payloads, "qwen_artifact_continuation_contract"),
			"enrichment_compatibility_contract": _latest_tool_payload_by_type(tool_payloads, "qwen_artifact_enrichment_compatibility_contract"),
			"recovery_contract": _latest_tool_payload_by_type(tool_payloads, "qwen_artifact_enrichment_recovery_contract"),
			"scope_decision_contract": _latest_tool_payload_by_type(tool_payloads, "qwen_governed_scope_decision_contract"),
			"grounded_turn_context": _latest_tool_payload_by_type(tool_payloads, "qwen_grounded_turn_context"),
			"compiled_audit": _latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract"),
			"rendered_family_response": _latest_tool_payload_by_type(tool_payloads, "qwen_rendered_family_response_contract"),
		}

	return _run_phase55_smoke_session("Phase 8 Recovery Execution Debug", _runner)


def _stabilize_smoke_grounded_turn_visibility(
	*,
	session_name: str,
	expected_request_id: str,
	attempts: int = 3,
	delay_seconds: float = 0.05,
	disallow_assistant_text: str = "",
) -> Dict[str, Any]:
	expected = str(expected_request_id or "").strip()
	disallowed_text = str(disallow_assistant_text or "").strip()
	last_grounded_turn: Dict[str, Any] = {}
	for attempt in range(max(1, int(attempts))):
		frappe.db.commit()
		frappe.clear_cache()
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
		last_grounded_turn = _latest_grounded_turn_contract(session_doc)
		request_id = str(
			last_grounded_turn.get("trace_request_id") or last_grounded_turn.get("request_id") or ""
		).strip()
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		assistant_ready = bool(assistant_text) and (not disallowed_text or assistant_text != disallowed_text)
		if expected and request_id == expected and assistant_ready:
			return last_grounded_turn
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))
	return last_grounded_turn


def _run_smoke_reasoning_followup_with_retry(
	*,
	session_name: str,
	message: str,
	user: str,
	attempts: int = 2,
	delay_seconds: float = 0.1,
) -> tuple[bool, Dict[str, Any]]:
	last_payload: Dict[str, Any] = {}
	for attempt in range(max(1, int(attempts))):
		frappe.db.commit()
		frappe.clear_cache()
		ok, payload = handle_qwen_user_message(
			session_name=session_name,
			message=message,
			user=user,
		)
		last_payload = payload if isinstance(payload, dict) else {"error": payload}
		mode = str((last_payload or {}).get("mode") or "").strip()
		if ok and mode == "erp_business_reasoning":
			return True, last_payload
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))
	return False, last_payload


def _run_smoke_fresh_query_turn_with_retry(
	*,
	session_name: str,
	message: str,
	user: str,
	allowed_modes: set[str],
	attempts: int = 2,
	delay_seconds: float = 0.15,
) -> tuple[bool, Dict[str, Any]]:
	last_payload: Dict[str, Any] = {}
	for attempt in range(max(1, int(attempts))):
		frappe.db.commit()
		frappe.clear_cache()
		ok, payload = handle_qwen_user_message(
			session_name=session_name,
			message=message,
			user=user,
		)
		last_payload = payload if isinstance(payload, dict) else {"error": payload}
		mode = str((last_payload or {}).get("mode") or "").strip()
		payload_ok = bool(last_payload.get("ok")) if "ok" in last_payload else bool(ok)
		if ok and mode in allowed_modes and payload_ok:
			return True, last_payload
		if attempt + 1 < max(1, int(attempts)):
			time.sleep(max(0.0, float(delay_seconds)))
	return False, last_payload


def run_h3_duplicate_recovery_acceptance_smoke() -> Dict[str, Any]:
	def _seed_recovery_session(doc) -> None:
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-seed-recovery",
			session_id=doc.name,
			source_request_id="h3-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-grounded-request",
			"trace_request_id": "h3-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"I can't safely add quantity to the current ranking, but I can run the governed Top Customers by Quantity report for last month."
			),
		)
		_append_tool_payload(doc, grounded_turn_payload)
		_append_tool_payload(doc, recovery_payload)
		_save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		_seed_recovery_session(doc)
		fixture_id = "product_recovery_flow"
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError("H3 duplicate recovery smoke failed: first acceptance did not execute as a fresh governed query.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		first_tool_payloads = _session_tool_payloads(session_doc)
		first_accepted_repairs = [
			item
			for item in first_tool_payloads
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("repair_state") or "").strip() == "accepted"
			and str(item.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query"
		]
		if len(first_accepted_repairs) != 1:
			raise RuntimeError("H3 duplicate recovery smoke failed: first acceptance did not persist exactly one accepted repair contract.")
		if "quantity" not in first_text.lower() and "qty" not in first_text.lower() and "unit" not in first_text.lower():
			raise RuntimeError("H3 duplicate recovery smoke failed: first acceptance did not appear to execute the quantity query.")

		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 duplicate recovery smoke failed: second duplicate acceptance turn did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		second_tool_payloads = _session_tool_payloads(session_doc)
		second_accepted_repairs = [
			item
			for item in second_tool_payloads
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("repair_state") or "").strip() == "accepted"
			and str(item.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query"
		]
		if len(second_accepted_repairs) != 1:
			raise RuntimeError("H3 duplicate recovery smoke failed: duplicate acceptance created an extra accepted repair contract.")
		if _latest_recovery_contract(session_doc):
			raise RuntimeError("H3 duplicate recovery smoke failed: stale recovery contract remained active after duplicate acceptance.")
		if str((second_payload or {}).get("mode") or "").strip() == "compiled_first_turn":
			raise RuntimeError("H3 duplicate recovery smoke failed: duplicate acceptance re-executed a stale governed recovery query.")
		lower_second_text = second_text.lower()
		if (
			("i can run" in lower_second_text or "we can run" in lower_second_text or "run the governed" in lower_second_text)
			and "top customers by quantity" in lower_second_text
		):
			raise RuntimeError("H3 duplicate recovery smoke failed: duplicate acceptance leaked stale recovery guidance.")
		return {
			"ok": True,
			"first_mode": str((first_payload or {}).get("mode") or "").strip(),
			"second_mode": str((second_payload or {}).get("mode") or "").strip(),
			"second_text": second_text,
		}

	return _run_phase55_smoke_session("H3 Duplicate Recovery Acceptance Smoke", _runner)


def run_h3_stale_recovery_invalidated_by_fresh_override_smoke() -> Dict[str, Any]:
	def _seed_recovery_session(doc) -> None:
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-stale-recovery-seed",
			session_id=doc.name,
			source_request_id="h3-stale-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-stale-grounded-request",
			"trace_request_id": "h3-stale-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"I can't safely add quantity to the current ranking, but I can run the governed Top Customers by Quantity report for last month."
			),
		)
		_append_tool_payload(doc, grounded_turn_payload)
		_append_tool_payload(doc, recovery_payload)
		_save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		fixture_id = "product_recovery_flow"
		_seed_recovery_session(doc)

		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("recovery_interaction_defaults", "guidance"),
			user="Administrator",
		)
		first_mode = str((first_payload or {}).get("mode") or "").strip()
		first_engine = str((((first_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
		if not ok or first_mode != "recovery_guidance":
			raise RuntimeError("H3 stale recovery invalidation smoke failed: seeded recovery did not answer through recovery guidance.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		recovery_after_first = _latest_recovery_contract(session_doc)
		if not recovery_after_first:
			raise RuntimeError("H3 stale recovery invalidation smoke failed: active recovery contract was lost before fresh override.")

		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "fresh_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError("H3 stale recovery invalidation smoke failed: fresh-query override did not execute as a fresh governed query.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		override_grounded_turn = _latest_grounded_turn_contract(session_doc)
		override_trace_request_id = str(
			override_grounded_turn.get("trace_request_id") or override_grounded_turn.get("request_id") or ""
		).strip()
		override_reports = {
			str(value or "").strip()
			for value in (override_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not override_trace_request_id:
			raise RuntimeError("H3 stale recovery invalidation smoke failed: fresh-query override did not create grounded trace identity.")
		if override_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 stale recovery invalidation smoke failed: override reports were unexpected: {sorted(override_reports)!r}."
			)
		if _latest_recovery_contract(session_doc):
			raise RuntimeError("H3 stale recovery invalidation smoke failed: stale recovery contract remained active after fresh grounded override.")

		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message(fixture_id, "short_acceptance"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 stale recovery invalidation smoke failed: post-override confirmation turn did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		final_grounded_turn = _latest_grounded_turn_contract(session_doc)
		final_trace_request_id = str(
			final_grounded_turn.get("trace_request_id") or final_grounded_turn.get("request_id") or ""
		).strip()
		final_reports = {
			str(value or "").strip()
			for value in (final_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if final_trace_request_id != override_trace_request_id:
			raise RuntimeError(
				"H3 stale recovery invalidation smoke failed: stale recovery acceptance changed the grounded trace after fresh override."
			)
		if final_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 stale recovery invalidation smoke failed: stale recovery acceptance changed grounded reports to {sorted(final_reports)!r}."
			)
		final_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip().lower()
		if "top products by quantity" in final_text or "quantity sold" in final_text:
			raise RuntimeError("H3 stale recovery invalidation smoke failed: stale recovery alternative leaked back after fresh override.")
		return {
			"ok": True,
			"guidance_mode": first_mode,
			"guidance_engine": first_engine,
			"override_mode": str((second_payload or {}).get("mode") or "").strip(),
			"post_override_mode": str((third_payload or {}).get("mode") or "").strip(),
			"override_trace_request_id": override_trace_request_id,
			"final_trace_request_id": final_trace_request_id,
			"final_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return _run_phase6_smoke_session("H3 Stale Recovery Invalidated By Fresh Override Smoke", _runner)


def run_h3_post_stop_clarification_repeat_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, initial_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 clarification repeat smoke failed: initial ambiguous request did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		initial_state = get_clarification_state(session_doc)
		if not initial_state.has_pending:
			raise RuntimeError("H3 clarification repeat smoke failed: initial ambiguous request did not create pending clarification state.")

		for expected_attempt in (1, 2):
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="yes",
				user="Administrator",
			)
			if not ok or str((payload or {}).get("mode") or "").strip() != "clarification":
				raise RuntimeError("H3 clarification repeat smoke failed: unresolved reply did not remain in clarification.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			state = get_clarification_state(session_doc)
			if int(state.attempt_count) != expected_attempt:
				raise RuntimeError("H3 clarification repeat smoke failed: attempt count drifted during unresolved clarification.")

		ok, stop_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok or str((stop_payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("H3 clarification repeat smoke failed: bounded stop turn did not complete.")
		if str(((stop_payload or {}).get("agent_meta") or {}).get("mode") or "").strip() != "fallback_stop":
			raise RuntimeError("H3 clarification repeat smoke failed: bounded stop did not exit through fallback_stop.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("H3 clarification repeat smoke failed: pending clarification was not cleared after fallback_stop.")

		ok, repeated_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="yes",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 clarification repeat smoke failed: repeated post-stop turn did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		repeated_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("H3 clarification repeat smoke failed: repeated post-stop reply resurrected stale clarification state.")
		if str((repeated_payload or {}).get("mode") or "").strip() == "clarification":
			raise RuntimeError("H3 clarification repeat smoke failed: repeated post-stop reply was trapped back into stale clarification.")
		return {
			"ok": True,
			"post_stop_mode": str((repeated_payload or {}).get("mode") or "").strip(),
			"post_stop_text": repeated_text,
		}

	return _run_phase55_smoke_session("H3 Post-Stop Clarification Repeat Smoke", _runner)


def run_h3_clarification_preempts_recovery_smoke() -> Dict[str, Any]:
	def _seed_mixed_state(doc) -> None:
		pending_signal = {
			"type": "qwen_clarification_signal_contract",
			"contract_version": "1.0",
			"request_id": "h3-mixed-clarify",
			"stage": "fresh_query_compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which report would you like me to use: Sales Analytics or Stock Balance?",
			"suggested_options": ["Sales Analytics", "Stock Balance"],
			"governed_default_option": "Sales Analytics",
		}
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-mixed-recovery",
			session_id=doc.name,
			source_request_id="h3-mixed-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-mixed-grounded-request",
			"trace_request_id": "h3-mixed-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		_append_message(doc, "assistant", _assistant_text_payload(str(pending_signal.get("user_question") or "").strip()))
		_append_tool_payload(doc, grounded_turn_payload)
		_append_tool_payload(doc, recovery_payload)
		_append_tool_payload(doc, pending_signal)
		store_pending_clarification_signal(doc, pending_signal)
		_save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		_seed_mixed_state(doc)
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("recovery_interaction_defaults", "guidance"),
			user="Administrator",
		)
		if not ok or str((payload or {}).get("mode") or "").strip() != "clarification":
			raise RuntimeError("H3 clarification/recovery smoke failed: pending clarification did not preempt recovery guidance.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		state = get_clarification_state(session_doc)
		if not state.has_pending:
			raise RuntimeError("H3 clarification/recovery smoke failed: pending clarification was lost during preemption.")
		tool_payloads = _session_tool_payloads(session_doc)
		request_id = str((payload or {}).get("request_id") or "").strip()
		current_turn_repairs = [
			item
			for item in tool_payloads
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("request_id") or "").strip() == request_id
		]
		if current_turn_repairs:
			raise RuntimeError("H3 clarification/recovery smoke failed: recovery repair contract leaked into a clarification-owned turn.")
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"attempt_count": int(state.attempt_count),
		}

	return _run_phase55_smoke_session("H3 Clarification Preempts Recovery Smoke", _runner)


def run_h3_clarification_resolution_does_not_resurrect_stale_recovery_smoke() -> Dict[str, Any]:
	def _seed_mixed_state(doc) -> None:
		pending_signal = {
			"type": "qwen_clarification_signal_contract",
			"contract_version": "1.0",
			"request_id": "h3-mixed-clarify-resolve",
			"stage": "fresh_query_compiler",
			"reason_type": "report_ambiguity",
			"user_question": "Which aging report would you like me to use: Accounts Receivable Summary or Accounts Payable Summary?",
			"suggested_options": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"governed_default_option": "Accounts Receivable Summary",
		}
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-mixed-recovery-resume",
			session_id=doc.name,
			source_request_id="h3-mixed-grounded-trace-resume",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-mixed-grounded-request-resume",
			"trace_request_id": "h3-mixed-grounded-trace-resume",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		_append_message(doc, "assistant", _assistant_text_payload(str(pending_signal.get("user_question") or "").strip()))
		_append_tool_payload(doc, grounded_turn_payload)
		_append_tool_payload(doc, recovery_payload)
		_append_tool_payload(doc, pending_signal)
		store_pending_clarification_signal(doc, pending_signal)
		_save_session(doc, ignore_permissions=False)

	def _runner(doc) -> Dict[str, Any]:
		_seed_mixed_state(doc)
		ok, resolution_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Accounts Receivable Summary",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 clarification/recovery resume smoke failed: clarification resolution turn did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("H3 clarification/recovery resolution smoke failed: clarification state did not clear after explicit resolution.")
		resolution_grounded_turn = _latest_grounded_turn_contract(session_doc)
		resolution_trace_request_id = str(
			resolution_grounded_turn.get("trace_request_id") or resolution_grounded_turn.get("request_id") or ""
		).strip()
		resolution_reports = {
			str(value or "").strip()
			for value in (resolution_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}

		ok, followup_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("recovery_interaction_defaults", "guidance"),
			user="Administrator",
		)
		followup_mode = str((followup_payload or {}).get("mode") or "").strip()
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		latest_recovery = _latest_recovery_contract(session_doc)
		if latest_recovery:
			latest_source_request_id = str(latest_recovery.get("source_request_id") or "").strip()
			latest_source_report = str(latest_recovery.get("source_report") or "").strip()
			if latest_source_request_id != resolution_trace_request_id:
				raise RuntimeError(
					"H3 clarification/recovery resolution smoke failed: stale recovery contract remained active after explicit clarification resolution."
				)
			if latest_source_report and resolution_reports and latest_source_report not in resolution_reports:
				raise RuntimeError(
					"H3 clarification/recovery resolution smoke failed: recovery follow-up did not stay anchored to the resolved grounded source."
				)
		followup_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		lower_text = followup_text.lower()
		if "top customers by quantity" in lower_text or "governed alternative" in lower_text:
			raise RuntimeError(
				"H3 clarification/recovery resolution smoke failed: stale recovery guidance leaked back after explicit clarification resolution."
			)
		return {
			"ok": True,
			"resolution_mode": str((resolution_payload or {}).get("mode") or "").strip(),
			"followup_ok": bool(ok),
			"followup_mode": followup_mode,
			"resolution_trace_request_id": resolution_trace_request_id,
			"followup_text": followup_text,
		}

	return _run_phase55_smoke_session(
		"H3 Clarification Resolution Does Not Resurrect Stale Recovery Smoke",
		_runner,
	)


def run_h3_fresh_query_replaces_grounded_context_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		fixture = require_smoke_fixture("fresh_query_override_to_ar")
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H3 grounded-context replacement smoke failed: initial governed artifact query did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_grounded_turn = _latest_grounded_turn_contract(session_doc)
		first_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
		if first_source_name != str(fixture.get("expected_initial_source_name") or "").strip():
			raise RuntimeError("H3 grounded-context replacement smoke failed: initial grounded artifact context was missing.")

		frappe.clear_cache()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("replacement_message") or "").strip(),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
			"erp_business_reasoning",
		}:
			raise RuntimeError("H3 grounded-context replacement smoke failed: explicit fresh query override did not execute as a fresh governed query.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_grounded_turn = _latest_grounded_turn_contract(session_doc)
		second_source_name = str(second_grounded_turn.get("source_name") or "").strip()
		expected_replacement_source_names = {
			str(value or "").strip()
			for value in (fixture.get("expected_replacement_source_names") or [])
			if str(value or "").strip()
		}
		if (
			not second_source_name
			or second_source_name == first_source_name
			or (expected_replacement_source_names and second_source_name not in expected_replacement_source_names)
		):
			raise RuntimeError("H3 grounded-context replacement smoke failed: fresh query did not replace the stale grounded source.")

		stable_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id=str(
				second_grounded_turn.get("trace_request_id") or second_grounded_turn.get("request_id") or ""
			).strip(),
			disallow_assistant_text=first_assistant_text,
		)
		stable_source_name = str(stable_grounded_turn.get("source_name") or "").strip()
		if stable_source_name != second_source_name:
			raise RuntimeError("H3 grounded-context replacement smoke failed: replacement grounded source was not durably visible before reasoning follow-up.")
		second_grounded_turn = stable_grounded_turn
		ok, third_payload = _run_smoke_reasoning_followup_with_retry(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((third_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("H3 grounded-context replacement smoke failed: follow-up interpretation did not enter the reasoning lane for the replacement context.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		tool_payloads = _session_tool_payloads(session_doc)
		reasoning_contract = _latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract")
		compatible_contract = _source_compatible_reasoning_contract(
			grounded_turn=second_grounded_turn,
			reasoning_contract=reasoning_contract,
		)
		if not compatible_contract:
			raise RuntimeError("H3 grounded-context replacement smoke failed: reasoning contract did not bind to the replacement grounded source.")
		lower_text = assistant_text.lower()
		if "receivable" not in lower_text and "overdue" not in lower_text and "ar" not in lower_text:
			raise RuntimeError("H3 grounded-context replacement smoke failed: reasoning answer did not stay anchored to AR context.")
		return {
			"ok": True,
			"first_source_name": first_source_name,
			"second_source_name": second_source_name,
			"grounding_family_id": str(reasoning_contract.get("grounding_family_id") or "").strip(),
			"grounding_source_reports": [
				str(value or "").strip()
				for value in (reasoning_contract.get("grounding_source_reports") or [])
				if str(value or "").strip()
			],
			"reasoning_mode": str((third_payload or {}).get("mode") or "").strip(),
			"answer_text": assistant_text,
		}

	return _run_phase6_smoke_session("H3 Fresh Query Replaces Grounded Context Smoke", _runner)


def run_h3_pending_override_replaces_with_new_grounded_context_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me financial statement",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("H3 pending override replacement smoke failed: initial ambiguous request did not complete.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		if not get_clarification_state(session_doc).has_pending:
			raise RuntimeError("H3 pending override replacement smoke failed: initial ambiguous request did not create pending clarification state.")

		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("recovery_interaction_defaults", "fresh_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError("H3 pending override replacement smoke failed: explicit fresh query did not override pending clarification as a new governed query.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("H3 pending override replacement smoke failed: pending clarification survived the explicit fresh query override.")
		replacement_grounded_turn = _latest_grounded_turn_contract(session_doc)
		replacement_source_name = str(replacement_grounded_turn.get("source_name") or "").strip()
		if not replacement_source_name:
			raise RuntimeError("H3 pending override replacement smoke failed: replacement fresh query did not create grounded context.")

		replacement_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id=str(
				replacement_grounded_turn.get("trace_request_id") or replacement_grounded_turn.get("request_id") or ""
			).strip(),
			disallow_assistant_text=first_assistant_text,
		)
		replacement_source_name = str(replacement_grounded_turn.get("source_name") or "").strip()
		if not replacement_source_name:
			raise RuntimeError("H3 pending override replacement smoke failed: replacement grounded context was not durably visible before reasoning follow-up.")
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			user="Administrator",
		)
		third_mode = str((third_payload or {}).get("mode") or "").strip()
		if not ok or third_mode not in {
			"erp_business_reasoning",
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			tool_types = [
				str(item.get("type") or "").strip()
				for item in _session_tool_payloads(session_doc)
				if str(item.get("type") or "").strip()
			]
			raise RuntimeError(
				f"H3 pending override replacement smoke failed: follow-up did not stay in an approved bounded lane on the new grounded context. third_payload={third_payload!r} tool_types={tool_types!r}"
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		tool_payloads = _session_tool_payloads(session_doc)
		final_grounded_turn = _latest_grounded_turn_contract(session_doc)
		final_reports = {
			str(value or "").strip()
			for value in (final_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if final_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 pending override replacement smoke failed: final grounded source drifted to unexpected reports {sorted(final_reports)!r}."
			)
		reasoning_reports = set(final_reports)
		if third_mode == "erp_business_reasoning":
			reasoning_contract = _latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract")
			compatible_contract = _source_compatible_reasoning_contract(
				grounded_turn=replacement_grounded_turn,
				reasoning_contract=reasoning_contract,
			)
			if not compatible_contract:
				raise RuntimeError("H3 pending override replacement smoke failed: reasoning contract did not bind to the replacement grounded source.")
			reasoning_reports = {
				str(value or "").strip()
				for value in (reasoning_contract.get("grounding_source_reports") or [])
				if str(value or "").strip()
			}
		lower_text = assistant_text.lower()
		if "receivable" not in lower_text and "overdue" not in lower_text and "ar" not in lower_text:
			raise RuntimeError("H3 pending override replacement smoke failed: follow-up answer did not stay anchored to AR context after clarification override.")
		if "profit & loss" in lower_text or "balance sheet" in lower_text or "cash flow" in lower_text:
			raise RuntimeError("H3 pending override replacement smoke failed: stale financial-view clarification leaked back after override.")
		return {
			"ok": True,
			"replacement_source_name": replacement_source_name,
			"grounding_family_id": str((final_grounded_turn or {}).get("artifact_family_id") or "").strip(),
			"grounding_source_reports": sorted(reasoning_reports),
			"reasoning_mode": third_mode,
			"answer_text": assistant_text,
		}

	return _run_phase6_smoke_session("H3 Pending Override Replaces With New Grounded Context Smoke", _runner)


def run_h3_latest_fresh_grounded_query_wins_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		ok, first_payload = _run_smoke_fresh_query_turn_with_retry(
			session_name=doc.name,
			message="give me AR / AP insight",
			user="Administrator",
			allowed_modes={
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			},
		)
		if not ok:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: initial AR/AP query did not execute as a fresh governed query.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_grounded_turn = _latest_grounded_turn_contract(session_doc)
		first_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
		first_family_id = str(first_grounded_turn.get("artifact_family_id") or "").strip()
		if not first_source_name or not first_family_id:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: initial AR/AP grounded context was missing.")

		frappe.clear_cache()
		ok, second_payload = _run_smoke_fresh_query_turn_with_retry(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
			allowed_modes={
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			},
		)
		if not ok:
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = _session_tool_payloads(session_doc)
			fresh_query_payload = _latest_tool_payload_by_type(tool_payloads, "qwen_semantic_fresh_query_interpretation")
			raise RuntimeError(
				"H3 latest fresh grounded query smoke failed: second AR query did not execute as a fresh governed query. "
				f"second_payload={second_payload!r} fresh_query_payload={fresh_query_payload!r}"
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_grounded_turn = _latest_grounded_turn_contract(session_doc)
		second_source_name = str(second_grounded_turn.get("source_name") or "").strip()
		second_family_id = str(second_grounded_turn.get("artifact_family_id") or "").strip()
		second_reports = {
			str(value or "").strip()
			for value in (second_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not second_source_name or not second_family_id:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: second AR grounded context was missing.")
		if first_source_name == second_source_name and first_family_id == second_family_id:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: second fresh grounded query did not replace the first grounded context.")
		if second_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 latest fresh grounded query smoke failed: replacement AR reports were unexpected: {sorted(second_reports)!r}."
			)

		second_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id=str(
				second_grounded_turn.get("trace_request_id") or second_grounded_turn.get("request_id") or ""
			).strip(),
			disallow_assistant_text=first_assistant_text,
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		second_source_name = str(second_grounded_turn.get("source_name") or "").strip()
		second_reports = {
			str(value or "").strip()
			for value in (second_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not second_source_name or second_reports != {"Accounts Receivable Summary"} or not second_assistant_text or second_assistant_text == first_assistant_text:
			raise RuntimeError(
				f"H3 latest fresh grounded query smoke failed: replacement grounded context was not durably visible before reasoning follow-up: source={second_source_name!r} reports={sorted(second_reports)!r}."
			)
		frappe.db.commit()
		frappe.clear_cache()
		time.sleep(0.15)
		frappe.db.commit()
		frappe.clear_cache()
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			user="Administrator",
		)
		third_mode = str((third_payload or {}).get("mode") or "").strip()
		if not ok or third_mode not in {
			"erp_business_reasoning",
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			tool_types = [
				str(item.get("type") or "").strip()
				for item in _session_tool_payloads(session_doc)
				if str(item.get("type") or "").strip()
			]
			raise RuntimeError(
				f"H3 latest fresh grounded query smoke failed: latest-context follow-up did not stay in an approved bounded lane. third_payload={third_payload!r} tool_types={tool_types!r}"
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		tool_payloads = _session_tool_payloads(session_doc)
		final_grounded_turn = _latest_grounded_turn_contract(session_doc)
		final_reports = {
			str(value or "").strip()
			for value in (final_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if final_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 latest fresh grounded query smoke failed: final grounded source drifted to unexpected reports {sorted(final_reports)!r}."
			)
		reasoning_reports = set(final_reports)
		if third_mode == "erp_business_reasoning":
			reasoning_contract = _latest_tool_payload_by_type(tool_payloads, "qwen_erp_business_reasoning_contract")
			compatible_contract = _source_compatible_reasoning_contract(
				grounded_turn=second_grounded_turn,
				reasoning_contract=reasoning_contract,
			)
			if not compatible_contract:
				raise RuntimeError("H3 latest fresh grounded query smoke failed: reasoning contract did not bind to the latest grounded query.")
			reasoning_reports = {
				str(value or "").strip()
				for value in (reasoning_contract.get("grounding_source_reports") or [])
				if str(value or "").strip()
			}
			if reasoning_reports != {"Accounts Receivable Summary"}:
				raise RuntimeError(
					f"H3 latest fresh grounded query smoke failed: reasoning stayed on unexpected reports {sorted(reasoning_reports)!r}."
				)
		lower_text = assistant_text.lower()
		if "receivable" not in lower_text and "overdue" not in lower_text and "ar" not in lower_text:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: follow-up answer did not stay anchored to the latest AR context.")
		if "accounts payable" in lower_text or "supplier" in lower_text:
			raise RuntimeError("H3 latest fresh grounded query smoke failed: stale AP context leaked into the latest AR follow-up answer.")
		return {
			"ok": True,
			"first_source_name": first_source_name,
			"second_source_name": second_source_name,
			"reasoning_mode": third_mode,
			"grounding_source_reports": sorted(reasoning_reports),
			"answer_text": assistant_text,
		}

	return _run_phase6_smoke_session("H3 Latest Fresh Grounded Query Wins Smoke", _runner)


def run_h3_repeated_identical_fresh_query_replaces_grounding_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = _run_smoke_fresh_query_turn_with_retry(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
			allowed_modes={
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			},
		)
		if not ok:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: first AR query did not execute as a fresh governed query.")
		first_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id="",
			attempts=8,
			delay_seconds=0.1,
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_trace_request_id = str(first_grounded_turn.get("trace_request_id") or first_grounded_turn.get("request_id") or "").strip()
		first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
		first_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		if not first_trace_request_id or not first_source_name:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: first grounded context was missing.")

		ok, second_payload = _run_smoke_fresh_query_turn_with_retry(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
			allowed_modes={
				"compiled_first_turn",
				"legacy_runtime",
				"legacy_runtime_rollout_fallback",
			},
		)
		if not ok:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: second AR query did not execute as a fresh governed query.")
		second_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id="",
			disallow_assistant_text=first_assistant_text,
			attempts=8,
			delay_seconds=0.1,
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_trace_request_id = str(second_grounded_turn.get("trace_request_id") or second_grounded_turn.get("request_id") or "").strip()
		second_source_name = str(second_grounded_turn.get("source_name") or "").strip()
		second_reports = {
			str(value or "").strip()
			for value in (second_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not second_trace_request_id or not second_source_name:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: second grounded context was missing.")
		if second_trace_request_id == first_trace_request_id:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: repeated fresh query did not replace the prior grounded trace identity.")
		if second_source_name != first_source_name:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: repeated identical query changed the grounded source unexpectedly.")
		if second_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 repeated identical fresh query smoke failed: repeated AR reports were unexpected: {sorted(second_reports)!r}."
			)

		second_grounded_turn = _stabilize_smoke_grounded_turn_visibility(
			session_name=doc.name,
			expected_request_id=second_trace_request_id,
			disallow_assistant_text=first_assistant_text,
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		if not second_assistant_text or second_assistant_text == first_assistant_text:
			raise RuntimeError(
				"H3 repeated identical fresh query smoke failed: repeated AR grounded context was not durably visible before reasoning follow-up."
			)

		frappe.db.commit()
		frappe.clear_cache()
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			user="Administrator",
		)
		third_mode = str((third_payload or {}).get("mode") or "").strip()
		if not ok or third_mode not in {
			"erp_business_reasoning",
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError(
				f"H3 repeated identical fresh query smoke failed: follow-up did not stay in an approved bounded lane. third_payload={third_payload!r}"
			)

		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		final_grounded_turn = _latest_grounded_turn_contract(session_doc)
		final_reports = {
			str(value or "").strip()
			for value in (final_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if final_reports != {"Accounts Receivable Summary"}:
			raise RuntimeError(
				f"H3 repeated identical fresh query smoke failed: final grounded source drifted to unexpected reports {sorted(final_reports)!r}."
			)
		if third_mode == "erp_business_reasoning":
			reasoning_contract = _latest_tool_payload_by_type(
				_session_tool_payloads(session_doc),
				"qwen_erp_business_reasoning_contract",
			)
			compatible_contract = _source_compatible_reasoning_contract(
				grounded_turn=second_grounded_turn,
				reasoning_contract=reasoning_contract,
			)
			if not compatible_contract:
				raise RuntimeError("H3 repeated identical fresh query smoke failed: reasoning contract did not bind to the latest repeated grounded query.")
			if str(reasoning_contract.get("grounding_source_request_id") or "").strip() != second_trace_request_id:
				raise RuntimeError("H3 repeated identical fresh query smoke failed: reasoning contract did not carry the latest repeated grounded trace request id.")
		lower_text = assistant_text.lower()
		if "receivable" not in lower_text and "overdue" not in lower_text and "ar" not in lower_text:
			raise RuntimeError("H3 repeated identical fresh query smoke failed: follow-up answer did not stay anchored to AR context.")
		return {
			"ok": True,
			"first_trace_request_id": first_trace_request_id,
			"second_trace_request_id": second_trace_request_id,
			"source_name": second_source_name,
			"reasoning_mode": third_mode,
			"answer_text": assistant_text,
		}

	return _run_phase6_smoke_session("H3 Repeated Identical Fresh Query Replaces Grounding Smoke", _runner)


def run_h3_repeated_identical_composite_grounded_query_replaces_grounding_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="give me AR / AP insight",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: first AR/AP query did not execute as a fresh governed query."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_grounded_turn = _latest_grounded_turn_contract(session_doc)
		first_trace_request_id = str(first_grounded_turn.get("trace_request_id") or first_grounded_turn.get("request_id") or "").strip()
		first_source_name = str(first_grounded_turn.get("source_name") or "").strip()
		first_reports = {
			str(value or "").strip()
			for value in (first_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not first_trace_request_id or not first_source_name:
			raise RuntimeError("H3 repeated identical composite grounded query smoke failed: first composite grounded context was missing.")
		if first_reports != {"Accounts Receivable Summary", "Accounts Payable Summary"}:
			raise RuntimeError(
				f"H3 repeated identical composite grounded query smoke failed: first AR/AP reports were unexpected: {sorted(first_reports)!r}."
			)

		frappe.clear_cache()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="give me AR / AP insight",
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: second AR/AP query did not execute as a fresh governed query."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_grounded_turn = _latest_grounded_turn_contract(session_doc)
		second_trace_request_id = str(second_grounded_turn.get("trace_request_id") or second_grounded_turn.get("request_id") or "").strip()
		second_source_name = str(second_grounded_turn.get("source_name") or "").strip()
		second_reports = {
			str(value or "").strip()
			for value in (second_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if not second_trace_request_id or not second_source_name:
			raise RuntimeError("H3 repeated identical composite grounded query smoke failed: second composite grounded context was missing.")
		if second_trace_request_id == first_trace_request_id:
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: repeated composite fresh query did not replace the prior grounded trace identity."
			)
		if second_source_name != first_source_name:
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: repeated identical composite query changed the grounded source unexpectedly."
			)
		if second_reports != {"Accounts Receivable Summary", "Accounts Payable Summary"}:
			raise RuntimeError(
				f"H3 repeated identical composite grounded query smoke failed: repeated AR/AP reports were unexpected: {sorted(second_reports)!r}."
			)

		frappe.clear_cache()
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what should management do next",
			user="Administrator",
		)
		if not ok or str((third_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: reasoning follow-up did not enter the reasoning lane."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		reasoning_contract = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_erp_business_reasoning_contract",
		)
		compatible_contract = _source_compatible_reasoning_contract(
			grounded_turn=second_grounded_turn,
			reasoning_contract=reasoning_contract,
		)
		if not compatible_contract:
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: reasoning contract did not bind to the latest repeated composite grounded query."
			)
		if str(reasoning_contract.get("grounding_source_request_id") or "").strip() != second_trace_request_id:
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: reasoning contract did not carry the latest repeated composite grounded trace request id."
			)
		reasoning_reports = {
			str(value or "").strip()
			for value in (reasoning_contract.get("grounding_source_reports") or [])
			if str(value or "").strip()
		}
		if reasoning_reports != {"Accounts Receivable Summary", "Accounts Payable Summary"}:
			raise RuntimeError(
				f"H3 repeated identical composite grounded query smoke failed: reasoning stayed on unexpected reports {sorted(reasoning_reports)!r}."
			)
		if not assistant_text:
			raise RuntimeError("H3 repeated identical composite grounded query smoke failed: reasoning answer text was empty.")
		lower_text = assistant_text.lower()
		if "accounts payable" not in lower_text and "supplier" not in lower_text and "liquidity" not in lower_text:
			raise RuntimeError(
				"H3 repeated identical composite grounded query smoke failed: reasoning answer did not stay anchored to the repeated AR/AP composite context."
			)
		return {
			"ok": True,
			"first_trace_request_id": first_trace_request_id,
			"second_trace_request_id": second_trace_request_id,
			"source_name": second_source_name,
			"grounding_source_reports": sorted(reasoning_reports),
			"reasoning_mode": str((third_payload or {}).get("mode") or "").strip(),
			"answer_text": assistant_text,
		}

	return _run_phase6_smoke_session("H3 Repeated Identical Composite Grounded Query Replaces Grounding Smoke", _runner)


def run_h3_latest_seeded_recovery_wins_smoke() -> Dict[str, Any]:
	def _seed_multiple_recoveries(doc) -> Dict[str, str]:
		older_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-older-grounded-request",
			"trace_request_id": "h3-older-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		older_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-older-recovery",
			session_id=doc.name,
			source_request_id="h3-older-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling customer query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		newer_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-newer-grounded-request",
			"trace_request_id": "h3-newer-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Products by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["item_code"],
			"metrics": ["revenue"],
			"returned_schema": ["Item", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "product_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Products by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		newer_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-newer-recovery",
			session_id=doc.name,
			source_request_id="h3-newer-grounded-trace",
			source_family_id="product_rankings",
			source_capability_id="top_products_by_revenue",
			source_report="Top Products by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["item_code"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_products_by_quantity",
			alternative_report="Top Products by Quantity",
			reason="Quantity requires a governed sibling product query.",
			allowed_to_recover=True,
			confidence=0.92,
		).to_payload()
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"I can run a governed quantity alternative for the current ranking if you want."
			),
		)
		_append_tool_payload(doc, older_grounded_turn_payload)
		_append_tool_payload(doc, older_recovery_payload)
		_append_tool_payload(doc, newer_grounded_turn_payload)
		_append_tool_payload(doc, newer_recovery_payload)
		_save_session(doc, ignore_permissions=False)
		return {
			"older_trace_request_id": "h3-older-grounded-trace",
			"newer_trace_request_id": "h3-newer-grounded-trace",
		}

	def _runner(doc) -> Dict[str, Any]:
		ids = _seed_multiple_recoveries(doc)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		active_recovery = _latest_recovery_contract(session_doc)
		if str(active_recovery.get("source_request_id") or "").strip() != ids["newer_trace_request_id"]:
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: newest seeded recovery was not selected as the active recovery authority."
			)
		if str(active_recovery.get("alternative_capability_id") or "").strip() != "top_products_by_quantity":
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: active recovery authority did not point to the product quantity alternative."
			)

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok or str((payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: explicit acceptance did not execute as a fresh governed query."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip().lower()
		latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
		latest_grounded_request_id = str(
			latest_grounded_turn.get("trace_request_id") or latest_grounded_turn.get("request_id") or ""
		).strip()
		latest_reports = {
			str(value or "").strip()
			for value in (latest_grounded_turn.get("artifact_source_reports") or [])
			if str(value or "").strip()
		}
		if "top customers by quantity" in assistant_text:
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: stale customer recovery leaked into the accepted alternative execution."
			)
		if "top products by quantity" not in assistant_text and "quantity sold" not in assistant_text:
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: accepted alternative did not appear to execute the product quantity query."
			)
		if latest_grounded_request_id in {ids["older_trace_request_id"], ids["newer_trace_request_id"]}:
			raise RuntimeError(
				"H3 latest seeded recovery smoke failed: accepted recovery did not create a fresh grounded trace."
			)
		if "Top Products by Quantity" not in latest_reports and "Sales Analytics" not in latest_reports:
			raise RuntimeError(
				f"H3 latest seeded recovery smoke failed: accepted recovery produced unexpected grounded reports {sorted(latest_reports)!r}."
			)
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"older_trace_request_id": ids["older_trace_request_id"],
			"newer_trace_request_id": ids["newer_trace_request_id"],
			"latest_grounded_request_id": latest_grounded_request_id,
			"latest_reports": sorted(latest_reports),
			"assistant_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return _run_phase55_smoke_session("H3 Latest Seeded Recovery Wins Smoke", _runner)


def run_h3_newer_recovery_survives_older_consumed_recovery_smoke() -> Dict[str, Any]:
	def _seed_consumed_old_and_active_new_recovery(doc) -> Dict[str, str]:
		old_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-consumed-old-grounded-request",
			"trace_request_id": "h3-consumed-old-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		old_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-consumed-old-recovery",
			session_id=doc.name,
			source_request_id="h3-consumed-old-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling customer query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		old_accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="h3-consumed-old-repair",
			session_id=doc.name,
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="Older recovery was already accepted and consumed.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		new_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-active-new-grounded-request",
			"trace_request_id": "h3-active-new-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Products by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["item_code"],
			"metrics": ["revenue"],
			"returned_schema": ["Item", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "product_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Products by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		new_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-active-new-recovery",
			session_id=doc.name,
			source_request_id="h3-active-new-grounded-trace",
			source_family_id="product_rankings",
			source_capability_id="top_products_by_revenue",
			source_report="Top Products by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["item_code"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_products_by_quantity",
			alternative_report="Top Products by Quantity",
			reason="Quantity requires a governed sibling product query.",
			allowed_to_recover=True,
			confidence=0.92,
		).to_payload()
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"The current ranking needs a governed quantity sibling query if you want to continue."
			),
		)
		_append_tool_payload(doc, old_grounded_turn_payload)
		_append_tool_payload(doc, old_recovery_payload)
		_append_tool_payload(doc, old_accepted_repair_payload)
		_append_tool_payload(doc, new_grounded_turn_payload)
		_append_tool_payload(doc, new_recovery_payload)
		_save_session(doc, ignore_permissions=False)
		return {
			"old_trace_request_id": "h3-consumed-old-grounded-trace",
			"new_trace_request_id": "h3-active-new-grounded-trace",
		}

	def _runner(doc) -> Dict[str, Any]:
		ids = _seed_consumed_old_and_active_new_recovery(doc)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		active_recovery = _latest_recovery_contract(session_doc)
		if str(active_recovery.get("request_id") or "").strip() != "h3-active-new-recovery":
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: newer active recovery was not selected."
			)
		if str(active_recovery.get("source_request_id") or "").strip() != ids["new_trace_request_id"]:
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: active recovery did not bind to the newer grounded trace."
			)

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok or str((payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: explicit acceptance did not execute as a fresh governed query."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip().lower()
		latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
		latest_grounded_request_id = str(
			latest_grounded_turn.get("trace_request_id") or latest_grounded_turn.get("request_id") or ""
		).strip()
		accepted_repairs = [
			item
			for item in _session_tool_payloads(session_doc)
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("repair_state") or "").strip() == "accepted"
			and str(item.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query"
		]
		if len(accepted_repairs) != 2:
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: expected exactly two accepted repair contracts after newer execution."
			)
		if latest_grounded_request_id in {ids["old_trace_request_id"], ids["new_trace_request_id"]}:
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: accepted newer recovery did not create a fresh grounded trace."
			)
		if "top customers by quantity" in assistant_text:
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: stale older customer recovery leaked into newer recovery execution."
			)
		if "top products by quantity" not in assistant_text and "quantity sold" not in assistant_text:
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: accepted newer recovery did not appear to execute the product quantity query."
			)
		if _latest_recovery_contract(session_doc):
			raise RuntimeError(
				"H3 newer recovery survives older consumed recovery smoke failed: recovery remained active after accepted newer execution."
			)
		return {
			"ok": True,
			"mode": str((payload or {}).get("mode") or "").strip(),
			"old_trace_request_id": ids["old_trace_request_id"],
			"new_trace_request_id": ids["new_trace_request_id"],
			"latest_grounded_request_id": latest_grounded_request_id,
			"accepted_repair_count": len(accepted_repairs),
			"assistant_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return _run_phase55_smoke_session("H3 Newer Recovery Survives Older Consumed Recovery Smoke", _runner)


def run_h3_duplicate_acceptance_after_newer_recovery_execution_smoke() -> Dict[str, Any]:
	def _seed_consumed_old_and_active_new_recovery(doc) -> Dict[str, str]:
		old_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-dup-old-grounded-request",
			"trace_request_id": "h3-dup-old-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Customers by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["customer"],
			"metrics": ["revenue"],
			"returned_schema": ["Customer", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "customer_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Customers by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		old_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-dup-old-recovery",
			session_id=doc.name,
			source_request_id="h3-dup-old-grounded-trace",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["customer"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_customers_by_quantity",
			alternative_report="Top Customers by Quantity",
			reason="Quantity requires a governed sibling customer query.",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		old_accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="h3-dup-old-repair",
			session_id=doc.name,
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="Older recovery was already accepted and consumed.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		new_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "h3-dup-new-grounded-request",
			"trace_request_id": "h3-dup-new-grounded-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Products by Revenue",
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"date_range": {"from_date": "2026-02-01", "to_date": "2026-02-29"},
			"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
			"dimensions": ["item_code"],
			"metrics": ["revenue"],
			"returned_schema": ["Item", "Sales Amount"],
			"table_rows": [],
			"row_count": 7,
			"base_language": "en",
			"transform_chain": [],
			"artifact_family_id": "product_rankings",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Top Products by Revenue"],
			"known_entities": [],
			"known_documents": [],
		}
		new_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="h3-dup-new-recovery",
			session_id=doc.name,
			source_request_id="h3-dup-new-grounded-trace",
			source_family_id="product_rankings",
			source_capability_id="top_products_by_revenue",
			source_report="Top Products by Revenue",
			failure_type="artifact_enrichment_incompatible",
			recovery_state="recoverable",
			available_recovery_actions=["keep_current_artifact", "run_alternative_governed_query", "clarify_target_output"],
			recommended_recovery_action="run_alternative_governed_query",
			preservable_scope={"company": "Mingalar Mobile Distribution Co., Ltd.", "requested_top_n": 7},
			preservable_dimensions=["item_code"],
			preservable_metrics=["quantity", "revenue"],
			preservable_time_context={"from_date": "2026-02-01", "to_date": "2026-02-29"},
			alternative_capability_id="top_products_by_quantity",
			alternative_report="Top Products by Quantity",
			reason="Quantity requires a governed sibling product query.",
			allowed_to_recover=True,
			confidence=0.92,
		).to_payload()
		_append_message(
			doc,
			"assistant",
			_assistant_text_payload(
				"The current ranking needs a governed quantity sibling query if you want to continue."
			),
		)
		_append_tool_payload(doc, old_grounded_turn_payload)
		_append_tool_payload(doc, old_recovery_payload)
		_append_tool_payload(doc, old_accepted_repair_payload)
		_append_tool_payload(doc, new_grounded_turn_payload)
		_append_tool_payload(doc, new_recovery_payload)
		_save_session(doc, ignore_permissions=False)
		return {
			"old_trace_request_id": "h3-dup-old-grounded-trace",
			"new_trace_request_id": "h3-dup-new-grounded-trace",
		}

	def _runner(doc) -> Dict[str, Any]:
		ids = _seed_consumed_old_and_active_new_recovery(doc)
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: first newer acceptance did not execute as a fresh governed query."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		first_grounded_turn = _latest_grounded_turn_contract(session_doc)
		first_latest_grounded_request_id = str(
			first_grounded_turn.get("trace_request_id") or first_grounded_turn.get("request_id") or ""
		).strip()
		first_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip().lower()
		first_accepted_repairs = [
			item
			for item in _session_tool_payloads(session_doc)
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("repair_state") or "").strip() == "accepted"
			and str(item.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query"
		]
		if len(first_accepted_repairs) != 2:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: expected exactly two accepted repairs after first newer execution."
			)
		if first_latest_grounded_request_id in {ids["old_trace_request_id"], ids["new_trace_request_id"]}:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: first newer execution did not create a fresh grounded trace."
			)
		if "top products by quantity" not in first_text and "quantity sold" not in first_text:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: first newer execution did not appear to return the product quantity result."
			)

		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_action_message("product_recovery_flow", "accept_governed_alternative"),
			user="Administrator",
		)
		if not ok:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: duplicate acceptance turn did not complete."
			)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip().lower()
		second_grounded_turn = _latest_grounded_turn_contract(session_doc)
		second_latest_grounded_request_id = str(
			second_grounded_turn.get("trace_request_id") or second_grounded_turn.get("request_id") or ""
		).strip()
		second_accepted_repairs = [
			item
			for item in _session_tool_payloads(session_doc)
			if str(item.get("type") or "").strip() == "qwen_conversational_repair_intent_contract"
			and str(item.get("repair_state") or "").strip() == "accepted"
			and str(item.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query"
		]
		if len(second_accepted_repairs) != 2:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: duplicate acceptance created an extra accepted repair."
			)
		if _latest_recovery_contract(session_doc):
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: recovery remained active after duplicate acceptance."
			)
		if str((second_payload or {}).get("mode") or "").strip() == "compiled_first_turn":
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: duplicate acceptance re-executed a stale recovery query."
			)
		if second_latest_grounded_request_id != first_latest_grounded_request_id:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: duplicate acceptance changed the grounded trace unexpectedly."
			)
		if "top customers by quantity" in second_text:
			raise RuntimeError(
				"H3 duplicate acceptance after newer recovery smoke failed: stale older customer recovery leaked back on duplicate acceptance."
			)
		return {
			"ok": True,
			"first_mode": str((first_payload or {}).get("mode") or "").strip(),
			"second_mode": str((second_payload or {}).get("mode") or "").strip(),
			"latest_grounded_request_id": second_latest_grounded_request_id,
			"accepted_repair_count": len(second_accepted_repairs),
			"second_text": str(_latest_assistant_payload(session_doc).get("text") or "").strip(),
		}

	return _run_phase55_smoke_session("H3 Duplicate Acceptance After Newer Recovery Execution Smoke", _runner)


def run_phase8_hardening_suite() -> Dict[str, Any]:
	return _run_phase8_hardening_suite_helper(
		recovery_authority_smoke=run_phase8b_recovery_authority_smoke,
		repair_handling_smoke=run_phase8c_repair_handling_smoke,
		fresh_query_override_smoke=run_phase8d_fresh_query_override_smoke,
		recovery_execution_smoke=run_phase8_recovery_execution_smoke,
	)


def run_h4_inferred_operational_evidence_stays_bounded_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sales invoice list",
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H4 inferred evidence smoke failed: setup artifact turn did not complete.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Based on this invoice list, can you infer which ones are delivered or undelivered? Even an estimate is okay.",
			user="Administrator",
		)
		second_mode = str((second_payload or {}).get("mode") or "").strip()
		if not ok or second_mode not in {"grounded_evidence_boundary", "erp_business_reasoning", "out_of_scope_domain"}:
			raise RuntimeError("H4 inferred evidence smoke failed: adversarial follow-up did not stay in a bounded safe lane.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		lower_text = assistant_text.lower()
		if second_mode != "out_of_scope_domain" and "delivery" not in lower_text:
			raise RuntimeError("H4 inferred evidence smoke failed: user-facing answer did not stay on delivery-status scope.")
		if second_mode == "grounded_evidence_boundary":
			recovery_payload = _latest_tool_payload_by_type(
				_session_tool_payloads(session_doc),
				"qwen_artifact_enrichment_recovery_contract",
			)
			if str(recovery_payload.get("failure_type") or "").strip() != "grounded_evidence_missing":
				raise RuntimeError("H4 inferred evidence smoke failed: recovery failure_type was not grounded_evidence_missing.")
			if str(recovery_payload.get("recommended_recovery_action") or "").strip() != "clarify_target_output":
				raise RuntimeError("H4 inferred evidence smoke failed: adversarial follow-up did not recommend bounded clarification recovery.")
		if second_mode == "out_of_scope_domain" and not any(
			phrase in lower_text
			for phrase in (
				"outside the current governed",
				"can't answer it confidently",
				"can't answer it safely",
				"falls outside",
			)
		):
			raise RuntimeError("H4 inferred evidence smoke failed: out-of-scope refusal did not explain the bounded safe refusal.")
		if not any(
			phrase in lower_text
			for phrase in (
				"can't answer",
				"can't confirm",
				"cannot answer",
				"cannot confirm",
				"cannot safely",
				"cannot be inferred",
				"unsupported speculation",
				"are absent from the provided data",
				"current governed artifact does not include",
			)
		):
			raise RuntimeError("H4 inferred evidence smoke failed: adversarial follow-up did not answer with bounded uncertainty.")
		return {
			"ok": True,
			"mode": second_mode,
			"assistant_text": assistant_text,
		}

	return _run_phase55_smoke_session("H4 Inferred Operational Evidence Stays Bounded Smoke", _runner)


def run_h4_mixed_metric_request_stays_bounded_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		fixture = require_smoke_fixture("fresh_query_override_to_ar")
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H4 mixed metric smoke failed: setup artifact turn did not complete.")
		frappe.clear_cache()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show together revenue and qty",
			user="Administrator",
		)
		second_mode = str((second_payload or {}).get("mode") or "").strip()
		second_engine = str((((second_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
		second_validation_status = str(
			((((second_payload or {}).get("agent_meta") or {}).get("validation") or {}).get("status") or "")
		).strip()
		if not ok or (
			second_mode
			not in {
				"artifact_enrichment_boundary",
				"recovery_guidance",
				"compiled_first_turn",
				"erp_business_reasoning",
				"out_of_scope_domain",
			}
			and second_engine not in {"local_transform", "qwen_agent", "erp_business_reasoning_guardrail", "local_governed_scope_guard"}
		):
			raise RuntimeError("H4 mixed metric smoke failed: mixed-metric request did not stay bounded.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		recovery_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_artifact_enrichment_recovery_contract",
		)
		repair_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_conversational_repair_intent_contract",
		)
		if second_engine not in {"local_transform", "qwen_agent", "erp_business_reasoning", "erp_business_reasoning_guardrail", "local_governed_scope_guard"} and str(
			recovery_payload.get("failure_type") or ""
		).strip() != "artifact_enrichment_incompatible":
			raise RuntimeError("H4 mixed metric smoke failed: mixed-metric request did not emit artifact_enrichment_incompatible recovery.")
		if str(repair_payload.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query":
			raise RuntimeError("H4 mixed metric smoke failed: mixed-metric request auto-accepted a governed alternative.")
		lower_text = assistant_text.lower()
		if second_mode == "compiled_first_turn":
			if "sales amount" not in lower_text and "revenue" not in lower_text:
				raise RuntimeError("H4 mixed metric smoke failed: compiled bounded answer lost the original ranking basis.")
		elif second_engine == "local_transform":
			if "sales amount" not in lower_text and "revenue" not in lower_text:
				raise RuntimeError("H4 mixed metric smoke failed: local mixed-metric answer lost the original ranking basis.")
		elif second_engine == "qwen_agent":
			if second_validation_status != "pass":
				raise RuntimeError("H4 mixed metric smoke failed: qwen_agent path did not stay within validated bounded execution.")
			if "sales amount" not in lower_text and "revenue" not in lower_text:
				raise RuntimeError("H4 mixed metric smoke failed: validated bounded answer lost the original ranking basis.")
		elif second_mode == "out_of_scope_domain":
			if not any(
				phrase in lower_text
				for phrase in (
					"outside the current governed",
					"can't answer it confidently",
					"can't answer it safely",
					"falls outside",
				)
			):
				raise RuntimeError("H4 mixed metric smoke failed: out-of-scope refusal did not explain the bounded safe refusal.")
		elif second_engine == "erp_business_reasoning":
			if (
				"no grounded finding supports" not in lower_text
				and "represent revenue" not in lower_text
				and "can't answer it safely" not in lower_text
			):
				raise RuntimeError("H4 mixed metric smoke failed: bounded reasoning answer did not explain the grounded mixed-metric limitation.")
		elif second_engine == "erp_business_reasoning_guardrail":
			if "couldn't safely complete grounded erp reasoning" not in lower_text and "can't answer it safely" not in lower_text:
				raise RuntimeError("H4 mixed metric smoke failed: reasoning-guardrail answer did not explain the bounded limitation.")
		elif "current governed source cannot safely provide" not in lower_text and "can't answer it safely" not in lower_text:
			raise RuntimeError("H4 mixed metric smoke failed: user-facing answer did not explain the bounded limitation.")
		return {
			"ok": True,
			"mode": second_mode,
			"engine": second_engine,
			"assistant_text": assistant_text,
			"recovery_payload": recovery_payload,
		}

	return _run_phase55_smoke_session("H4 Mixed Metric Request Stays Bounded Smoke", _runner)


def run_h4_long_multisentence_followup_stays_bounded_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		fixture = require_smoke_fixture("fresh_query_override_to_ar")
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=str(fixture.get("initial_message") or "").strip(),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H4 long follow-up smoke failed: setup artifact turn did not complete.")
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Please keep the exact same top 7 customer ranking by quantity, add serial number next to each row, do not change the ranking basis, and if you cannot do that safely then explain the governed option instead of guessing.",
			user="Administrator",
		)
		second_mode = str((second_payload or {}).get("mode") or "").strip()
		second_engine = str((((second_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
		second_validation_status = str(
			((((second_payload or {}).get("agent_meta") or {}).get("validation") or {}).get("status") or "")
		).strip()
		second_error = str((second_payload or {}).get("error") or "").strip().lower()
		if not ok or (
			second_mode not in {"artifact_enrichment_boundary", "recovery_guidance", "compiled_first_turn", "erp_business_reasoning"}
			and second_engine not in {"local_transform", "qwen_agent", "erp_business_reasoning_guardrail"}
		):
			raise RuntimeError("H4 long follow-up smoke failed: long adversarial follow-up did not remain bounded.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		recovery_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_artifact_enrichment_recovery_contract",
		)
		repair_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_conversational_repair_intent_contract",
		)
		if second_mode in {"artifact_enrichment_boundary", "recovery_guidance"} and str(recovery_payload.get("recommended_recovery_action") or "").strip() != "run_alternative_governed_query":
			raise RuntimeError("H4 long follow-up smoke failed: long bounded follow-up did not preserve the governed alternative path.")
		if str(repair_payload.get("accepted_recovery_action") or "").strip() == "run_alternative_governed_query":
			raise RuntimeError("H4 long follow-up smoke failed: long bounded follow-up auto-accepted the governed alternative.")
		lower_text = assistant_text.lower()
		if second_mode == "compiled_first_turn":
			if "sales amount" not in lower_text and "revenue" not in lower_text:
				raise RuntimeError("H4 long follow-up smoke failed: compiled bounded answer lost the original ranking basis.")
		elif second_engine == "local_transform":
			if "sales amount" not in lower_text and "revenue" not in lower_text:
				raise RuntimeError("H4 long follow-up smoke failed: local bounded answer lost the original ranking basis.")
		elif second_engine == "qwen_agent":
			if second_validation_status == "fail":
				if "ungrounded answer without tool usage" not in second_error:
					raise RuntimeError("H4 long follow-up smoke failed: qwen_agent validation failure was not the approved fail-closed rejection.")
			elif second_validation_status == "pass":
				if "sales amount" not in lower_text and "revenue" not in lower_text:
					raise RuntimeError("H4 long follow-up smoke failed: validated bounded answer lost the original ranking basis.")
			else:
				raise RuntimeError("H4 long follow-up smoke failed: qwen_agent path returned without a bounded validation outcome.")
		elif second_engine == "erp_business_reasoning_guardrail":
			if "couldn't safely complete grounded erp reasoning" not in lower_text:
				raise RuntimeError("H4 long follow-up smoke failed: reasoning guardrail did not return the approved bounded refusal.")
		elif (
			"governed alternative" not in lower_text
			and "top 7 products by quantity" not in lower_text
			and "separate governed query" not in lower_text
			and "can't answer it safely" not in lower_text
		):
			raise RuntimeError("H4 long follow-up smoke failed: bounded answer did not explain the governed safe path.")
		return {
			"ok": True,
			"mode": second_mode,
			"engine": second_engine,
			"assistant_text": assistant_text,
			"recovery_payload": recovery_payload,
		}

	return _run_phase55_smoke_session("H4 Long Multisentence Follow-Up Stays Bounded Smoke", _runner)


def run_h4_creative_followup_after_reasoning_is_refused_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		frappe.clear_cache()
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H4 creative follow-up smoke failed: setup artifact turn did not complete.")
		ok, second_payload = _run_smoke_reasoning_followup_with_retry(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("H4 creative follow-up smoke failed: setup reasoning turn did not complete.")
		frappe.clear_cache()
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="write a short poem about this",
			user="Administrator",
		)
		third_mode = str((third_payload or {}).get("mode") or "").strip()
		third_engine = str((((third_payload or {}).get("agent_meta") or {}).get("engine") or "")).strip()
		third_intent_class = str((((third_payload or {}).get("agent_meta") or {}).get("intent_class") or "")).strip()
		if not ok or (
			third_mode != "out_of_scope_domain"
			and not (third_mode == "front_door" and third_engine == "frontdoor_response_renderer" and third_intent_class == "low_signal_non_business")
		):
			raise RuntimeError("H4 creative follow-up smoke failed: creative ask did not resolve to a bounded safe refusal.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		lower_text = assistant_text.lower()
		if "poem" in lower_text:
			raise RuntimeError("H4 creative follow-up smoke failed: user-facing answer still complied with creative generation.")
		if third_mode == "front_door":
			if not any(
				phrase in lower_text
				for phrase in (
					"erp questions and analysis",
					"erp insights",
					"business assistant",
					"erp/business",
					"non-business",
					"outside",
					"governed area",
					"return to the accounts receivable summary",
				)
			):
				raise RuntimeError("H4 creative follow-up smoke failed: front-door refusal did not explain the non-business boundary.")
		elif not any(
			phrase in lower_text
			for phrase in (
				"outside the current governed erp assistant coverage",
				"outside the current governed qwen erp coverage",
				"can't answer it confidently",
				"can't answer it confidently here",
			)
		):
			raise RuntimeError("H4 creative follow-up smoke failed: refusal did not explain governed coverage boundary.")
		boundary_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(session_doc),
			"qwen_knowledge_boundary_contract",
		)
		if third_mode != "front_door" and str(boundary_payload.get("knowledge_coverage_state") or "").strip() != "unsupported_non_erp":
			raise RuntimeError("H4 creative follow-up smoke failed: knowledge boundary did not classify the creative ask as unsupported_non_erp.")
		return {
			"ok": True,
			"mode": third_mode,
			"engine": third_engine,
			"assistant_text": assistant_text,
			"boundary_payload": boundary_payload,
		}

	return _run_phase55_smoke_session("H4 Creative Follow-Up After Reasoning Is Refused Smoke", _runner)


def run_h4_recommendation_guarantee_stays_bounded_smoke() -> Dict[str, Any]:
	def _runner(doc) -> Dict[str, Any]:
		ok, first_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_replacement_message("fresh_query_override_to_ar"),
			user="Administrator",
		)
		if not ok or str((first_payload or {}).get("mode") or "").strip() not in {
			"compiled_first_turn",
			"legacy_runtime",
			"legacy_runtime_rollout_fallback",
		}:
			raise RuntimeError("H4 recommendation guarantee smoke failed: setup artifact turn did not complete.")
		frappe.db.commit()
		frappe.clear_cache()
		ok, second_payload = handle_qwen_user_message(
			session_name=doc.name,
			message=smoke_fixture_reasoning_message("fresh_query_override_to_ar_explicit_reasoning"),
			user="Administrator",
		)
		if not ok or str((second_payload or {}).get("mode") or "").strip() != "erp_business_reasoning":
			raise RuntimeError("H4 recommendation guarantee smoke failed: setup reasoning turn did not complete.")
		ok, third_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="guarantee which customer will pay this week",
			user="Administrator",
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		tool_payloads = _session_tool_payloads(session_doc)
		latest_semantic_followup = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_semantic_followup_interpretation",
		)
		latest_reasoning_activation = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_semantic_reasoning_activation",
		)
		latest_scope_decision = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_governed_scope_decision_contract",
		)
		third_mode = str((third_payload or {}).get("mode") or "").strip()
		third_engine = str(((third_payload or {}).get("agent_meta") or {}).get("engine") or "").strip()
		third_status = str(((third_payload or {}).get("agent_meta") or {}).get("status") or "").strip()
		if not ok or third_mode != "erp_business_reasoning" or third_engine != "erp_business_reasoning_guardrail":
			raise RuntimeError(
				"H4 recommendation guarantee smoke failed: bounded reasoning guardrail did not own the turn; "
				f"payload={third_payload!r}; semantic_followup={latest_semantic_followup!r}; "
				f"reasoning_activation={latest_reasoning_activation!r}; scope_decision={latest_scope_decision!r}."
			)
		if third_status != "invalid_payload":
			raise RuntimeError("H4 recommendation guarantee smoke failed: recommendation guarantee path did not expose the expected deterministic guardrail status.")
		assistant_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
		lower_text = assistant_text.lower()
		if "guarantee" in lower_text and "stopped rather than guess" not in lower_text:
			raise RuntimeError("H4 recommendation guarantee smoke failed: user-facing answer sounded like a guarantee instead of a bounded guardrail response.")
		if not any(
			phrase in lower_text
			for phrase in (
				"stopped rather than guess",
				"can't answer it safely",
				"couldn't safely generate",
				"current governed support",
			)
		):
			raise RuntimeError("H4 recommendation guarantee smoke failed: user-facing answer did not explain the bounded safe stop.")
		boundary_payload = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_knowledge_boundary_contract",
		)
		if str(boundary_payload.get("knowledge_coverage_state") or "").strip() != "valid_erp_domain_uncovered":
			raise RuntimeError("H4 recommendation guarantee smoke failed: knowledge boundary did not reclassify the blocked recommendation as valid_erp_domain_uncovered.")
		execution_path = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_execution_path",
		)
		if str(execution_path.get("path") or "").strip() != "reasoning_lane_guardrail":
			raise RuntimeError("H4 recommendation guarantee smoke failed: execution path did not record reasoning_lane_guardrail.")
		reasoning_execution = _latest_tool_payload_by_type(
			tool_payloads,
			"qwen_erp_business_reasoning_execution",
		)
		if str(reasoning_execution.get("status") or "").strip() != "invalid_payload":
			raise RuntimeError("H4 recommendation guarantee smoke failed: reasoning execution did not preserve the invalid_payload guardrail status.")
		return {
			"ok": True,
			"mode": third_mode,
			"assistant_text": assistant_text,
			"boundary_payload": boundary_payload,
			"execution_path": execution_path,
		}

	flag_key = "qwen_enable_erp_business_reasoning"
	percent_key = "qwen_erp_business_reasoning_rollout_percentage"
	users_key = "qwen_erp_business_reasoning_rollout_users"
	compiled_flag_key = "qwen_enable_compiled_first_turn"
	compiled_percent_key = "qwen_compiled_first_turn_rollout_percentage"
	compiled_users_key = "qwen_compiled_first_turn_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	keys = [
		flag_key,
		percent_key,
		users_key,
		compiled_flag_key,
		compiled_percent_key,
		compiled_users_key,
	]
	originals = {key: conf.get(key) for key in keys}
	presence = {key: key in conf for key in keys}
	try:
		conf[compiled_flag_key] = True
		conf[compiled_percent_key] = 0
		conf[compiled_users_key] = ["Administrator"]
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "H4 Recommendation Guarantee Stays Bounded Smoke"
		doc.insert(ignore_permissions=False)
		frappe.db.commit()
		try:
			return _runner(doc)
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_h4_adversarial_suite() -> Dict[str, Any]:
	return {
		"ok": True,
		"inferred_operational_evidence": run_h4_inferred_operational_evidence_stays_bounded_smoke(),
		"mixed_metric_request": run_h4_mixed_metric_request_stays_bounded_smoke(),
		"long_multisentence_followup": run_h4_long_multisentence_followup_stays_bounded_smoke(),
		"creative_followup_after_reasoning": run_h4_creative_followup_after_reasoning_is_refused_smoke(),
		"recommendation_guarantee": run_h4_recommendation_guarantee_stays_bounded_smoke(),
	}


def run_h5_release_gate_rollout_probe() -> Dict[str, Any]:
	def _validate_status(label: str, payload: Dict[str, Any]) -> Dict[str, Any]:
		if not isinstance(payload, dict):
			raise RuntimeError(f"H5 rollout probe failed: {label} status payload was not a dict.")
		for key in ("master_enabled", "rollout_percentage", "allow_users", "sample_decision"):
			if key not in payload:
				raise RuntimeError(f"H5 rollout probe failed: {label} status missing `{key}`.")
		try:
			percentage = float(payload.get("rollout_percentage"))
		except Exception as exc:
			raise RuntimeError(f"H5 rollout probe failed: {label} rollout_percentage was not numeric.") from exc
		if percentage < 0.0 or percentage > 100.0:
			raise RuntimeError(f"H5 rollout probe failed: {label} rollout_percentage was out of range.")
		decision = payload.get("sample_decision")
		if not isinstance(decision, dict):
			raise RuntimeError(f"H5 rollout probe failed: {label} sample_decision was not a dict.")
		for key in ("enabled", "reason", "rollout_percentage", "rollout_bucket", "allow_users"):
			if key not in decision:
				raise RuntimeError(f"H5 rollout probe failed: {label} sample_decision missing `{key}`.")
		if float(decision.get("rollout_percentage") or 0.0) < 0.0 or float(decision.get("rollout_percentage") or 0.0) > 100.0:
			raise RuntimeError(f"H5 rollout probe failed: {label} sample_decision rollout_percentage was out of range.")
		if float(decision.get("rollout_bucket") or 0.0) < 0.0 or float(decision.get("rollout_bucket") or 0.0) > 100.0:
			raise RuntimeError(f"H5 rollout probe failed: {label} sample_decision rollout_bucket was out of range.")
		return {
			"master_enabled": bool(payload.get("master_enabled")),
			"rollout_percentage": percentage,
			"sample_reason": str(decision.get("reason") or "").strip(),
			"sample_enabled": bool(decision.get("enabled")),
		}

	compiled = get_compiled_first_turn_rollout_status()
	reasoning = get_erp_business_reasoning_rollout_status()
	return {
		"ok": True,
		"compiled_first_turn": _validate_status("compiled_first_turn", compiled),
		"erp_business_reasoning": _validate_status("erp_business_reasoning", reasoning),
	}


def run_h5_release_gate_sanity_pack() -> Dict[str, Any]:
	def _isolate_release_gate_step() -> None:
		frappe.db.commit()
		frappe.clear_cache()

	_isolate_release_gate_step()
	frontdoor_boundary = run_phase55_frontdoor_boundary_smoke()
	_isolate_release_gate_step()
	reasoning_live_rollout = run_phase6_reasoning_live_debug()
	_isolate_release_gate_step()
	boundary_responses = run_phase7d_boundary_response_live_smoke()
	_isolate_release_gate_step()
	recovery_execution = run_phase8_recovery_execution_smoke()
	_isolate_release_gate_step()
	adversarial_recommendation_guardrail = run_h4_recommendation_guarantee_stays_bounded_smoke()
	return {
		"ok": True,
		"frontdoor_boundary": frontdoor_boundary,
		"reasoning_live_rollout": reasoning_live_rollout,
		"boundary_responses": boundary_responses,
		"recovery_execution": recovery_execution,
		"adversarial_recommendation_guardrail": adversarial_recommendation_guardrail,
	}


def run_h5_release_gate_suite() -> Dict[str, Any]:
	return {
		"ok": True,
		"rollout_probe": run_h5_release_gate_rollout_probe(),
		"sanity_pack": run_h5_release_gate_sanity_pack(),
	}


def run_post_contract_regression_suite() -> Dict[str, Any]:
	return {
		"ok": True,
		"phase55": run_phase55_hardening_suite(),
		"phase6": run_phase6_hardening_suite(),
		"phase7": run_phase7_hardening_suite(),
		"phase8": run_phase8_hardening_suite(),
	}
