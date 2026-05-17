from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, TextIO

from .natural_business_understanding_contracts import CONTRACT_VERSION


FINAL_ANSWER_EMISSION_DRY_RUN_CONTRACT_TYPE = "qwen_final_answer_emission_dry_run_contract"
FINAL_ANSWER_EMISSION_DRY_RUN_SUITE_ID = "ec_3_final_answer_hard_gate_dry_run"

DEFAULT_EC3_OUT_DIR = "impl_factory/00_governance/current_docs/generated/ec_3_final_answer_hard_gate_dry_run"
DEFAULT_EC3_REPORT_JSON = "qwen_ec3_final_answer_emission_dry_run_report.json"
DEFAULT_EC3_REPORT_MARKDOWN = "qwen_ec3_final_answer_emission_dry_run_report.md"

RECOMMENDATION_READY = "enterprise_cleanup_ec_3_ready_for_counterpart_review"
RECOMMENDATION_BLOCKED = "enterprise_cleanup_ec_3_blocked_need_more_investigation"

STATUS_AFTER_APPEND = "audit_created_after_append"
STATUS_BEFORE_APPEND = "authority_context_available_before_append"
STATUS_CONDITIONAL_AFTER_APPEND = "conditional_audit_after_append"
STATUS_CONTROL_NO_FINAL = "control_path_no_final_authority"
STATUS_LOW_LEVEL = "not_applicable_low_level_append_wrapper"
STATUS_MISSING = "missing_or_unknown_final_authority"
STATUS_POST_APPEND_CALLER = "post_append_caller_audit"

RISK_HIGH = "high"
RISK_MEDIUM = "medium"
RISK_LOW = "low"

ANSWER_TYPE_BUSINESS_FACTUAL = "business_facing_factual_answer"
ANSWER_TYPE_VISIBLE_CONTEXT = "visible_context_answer"
ANSWER_TYPE_GOVERNED_REPORT = "governed_report_answer"
ANSWER_TYPE_POLICY_BOUNDARY = "policy_boundary_refusal"
ANSWER_TYPE_REASONING = "reasoning_business_consultant_answer"
ANSWER_TYPE_TRACE = "trace_debug_answer"
ANSWER_TYPE_ERROR = "error_fallback_answer"
ANSWER_TYPE_CONTROL = "control_meta_answer"
ANSWER_TYPE_LOW_LEVEL = "low_level_append_helper"

APPEND_DIRECT = "direct_append_message"
APPEND_SERVICE_WRAPPER = "service_append_wrapper"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Iterable[Any] | None) -> List[str]:
	return [_clean_text(value) for value in (values or []) if _clean_text(value)]


def _project_path(root_path: str | Path, relative_path: str) -> Path:
	root = Path(root_path or ".")
	path = Path(relative_path)
	return path if path.is_absolute() else root / path


def _entry(
	path_id: str,
	relative_file_path: str,
	function_name: str,
	line_reference: str,
	answer_type: str,
	append_mechanism: str,
	authority_availability_status: str,
	audit_timing: str,
	risk_level: str,
	risk_reason: str,
	ec4_action: str,
	*,
	direct_assistant_append: bool = True,
	requires_hard_gate: bool = True,
) -> Dict[str, Any]:
	return {
		"path_id": path_id,
		"relative_file_path": relative_file_path,
		"function_name": function_name,
		"line_reference": line_reference,
		"answer_type": answer_type,
		"append_mechanism": append_mechanism,
		"direct_assistant_append": bool(direct_assistant_append),
		"authority_availability_status": authority_availability_status,
		"audit_timing": audit_timing,
		"risk_level": risk_level,
		"risk_reason": risk_reason,
		"requires_hard_gate": bool(requires_hard_gate),
		"ec4_action": ec4_action,
	}


EMISSION_PATH_INVENTORY: List[Dict[str, Any]] = [
	_entry(
		"service_append_message_wrapper",
		"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"_append_message",
		"1034",
		ANSWER_TYPE_LOW_LEVEL,
		APPEND_SERVICE_WRAPPER,
		STATUS_LOW_LEVEL,
		"no_answer_context",
		RISK_HIGH,
		"The raw append wrapper can write any role and does not receive authority context.",
		"Monitor only; do not hard-gate the raw wrapper because authority context lives above this layer.",
		direct_assistant_append=False,
		requires_hard_gate=False,
	),
	]

EXCLUDED_APPEND_SITES: List[Dict[str, Any]] = [
	{
		"site_id": "phase8_quantity_recovery_smoke_seed",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase8_hardening_support.py",
		"function_name": "_seed_quantity_recovery_session",
		"line_reference": "68",
		"append_mechanism": APPEND_DIRECT,
		"direct_assistant_append": True,
		"source_classification": "excluded_non_runtime_append_site",
		"exclusion_reason": "Smoke/recovery seed helper, not active user-facing runtime emission.",
	}
]

AUTHORIZED_APPEND_SITES: List[Dict[str, Any]] = [
	{
		"site_id": "authorized_emission_control_meta_sink",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py",
		"function_name": "emit_authorized_assistant_answer",
		"line_reference": "271",
		"append_mechanism": APPEND_DIRECT,
		"direct_assistant_append": True,
		"source_classification": "authorized_runtime_append_sink",
		"authorization_reason": "Centralized helper append after explicit control/meta authority validation.",
	},
	{
		"site_id": "authorized_emission_business_sink",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py",
		"function_name": "emit_authorized_assistant_answer",
		"line_reference": "327",
		"append_mechanism": APPEND_DIRECT,
		"direct_assistant_append": True,
		"source_classification": "authorized_runtime_append_sink",
		"authorization_reason": "Centralized helper append after final-answer authority preflight validation.",
	},
]

MIGRATED_AUTHORIZED_PATHS: List[Dict[str, Any]] = [
	{
		"path_id": "visible_context_followup_filter_boundary",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py",
		"function_name": "try_activate_visible_context_followup",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4A",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Filter/readiness visible-context boundary now validates authority before appending the assistant answer.",
	},
	{
		"path_id": "visible_context_followup_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py",
		"function_name": "try_activate_visible_context_followup",
		"answer_type": ANSWER_TYPE_VISIBLE_CONTEXT,
		"migration_slice": "EC-4A",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Resolved, boundary, out-of-range, and clarification visible-context answers now emit through the authorized helper.",
	},
	{
		"path_id": "frontdoor_lane_package_governed_report_or_projection",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py",
		"function_name": "handle_frontdoor_turn",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4C",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Active package frontdoor governed/report, bounded-refusal, and control/meta answers now emit through the authorized helper.",
	},
	{
		"path_id": "frontdoor_lane_package_governed_kpi_definition",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py",
		"function_name": "handle_frontdoor_turn",
		"answer_type": ANSWER_TYPE_BUSINESS_FACTUAL,
		"migration_slice": "EC-4C",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Governed KPI definitions now emit as business-facing factual answers only with deterministic registry authority.",
	},
	{
		"path_id": "compiled_support_result_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py",
		"function_name": "handle_compiled_first_turn_result",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4E",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Compiled-support governed/report, bounded-refusal, control, and error fallback answers now emit through the authorized helper.",
	},
	{
		"path_id": "reasoning_lane_business_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
		"function_name": "handle_reasoning_turn",
		"answer_type": ANSWER_TYPE_REASONING,
		"migration_slice": "EC-4G",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Answered grounded ERP reasoning now emits through the authorized helper as reasoning_business_consultant_answer with passed authority required.",
	},
	{
		"path_id": "reasoning_lane_guardrail_boundary",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
		"function_name": "handle_reasoning_turn",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4G",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Reasoning guardrail/boundary output now emits through the authorized helper as policy_boundary_refusal with bounded authority required.",
	},
	{
		"path_id": "entity_followup_failure",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py",
		"function_name": "try_entity_detail_followup",
		"answer_type": ANSWER_TYPE_ERROR,
		"migration_slice": "EC-4M",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Entity follow-up failure now emits through the authorized helper with explicit error fallback authority.",
	},
	{
		"path_id": "entity_followup_success",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py",
		"function_name": "try_entity_detail_followup",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4M",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Entity follow-up success now appends artifact, grounded turn, trace, audit, and authorized emission before assistant answer.",
	},
	{
		"path_id": "nbu_governed_requery_entity_detail",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
		"function_name": "try_activate_nbu_governed_requery_response",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4K",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "NBU governed requery entity-detail answers now build authority before assistant emission and block missing authority without answer_text leakage.",
	},
	{
		"path_id": "legacy_runtime_client_error",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
		"function_name": "handle_legacy_runtime_turn",
		"answer_type": ANSWER_TYPE_ERROR,
		"migration_slice": "EC-4I",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Legacy runtime client errors now emit through the authorized helper with explicit error fallback authority.",
	},
	{
		"path_id": "legacy_runtime_business_or_boundary_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py",
		"function_name": "handle_legacy_runtime_turn",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4I",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_HIGH,
		"reason": "Legacy runtime governed output and grounded-validation boundaries now build authority before assistant emission.",
	},
	{
		"path_id": "artifact_boundary_evidence_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py",
		"function_name": "handle_artifact_boundary_turn",
		"answer_type": ANSWER_TYPE_GOVERNED_REPORT,
		"migration_slice": "EC-4R1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Artifact direct-evidence answers now validate governed artifact authority before assistant or evidence-payload emission.",
	},
	{
		"path_id": "artifact_boundary_grounded_evidence_refusal",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py",
		"function_name": "handle_artifact_boundary_turn",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4R1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Grounded-evidence artifact refusals now emit as bounded policy-boundary answers through the authorized helper.",
	},
	{
		"path_id": "artifact_boundary_enrichment_refusal",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py",
		"function_name": "handle_artifact_boundary_turn",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4R1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Artifact-enrichment refusals now emit as bounded policy-boundary answers through the authorized helper.",
	},
	{
		"path_id": "local_followup_transform",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py",
		"function_name": "try_local_followup_transform",
		"answer_type": ANSWER_TYPE_VISIBLE_CONTEXT,
		"migration_slice": "EC-4R2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Local follow-up transforms now validate visible/grounded authority before assistant or transform payload emission.",
	},
	{
		"path_id": "runtime_gate_out_of_scope_boundary",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py",
		"function_name": "try_handle_runtime_gate_lane",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4S1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Runtime-gate out-of-scope ERP-domain boundary now emits as a bounded policy refusal only after authority validation.",
	},
	{
		"path_id": "service_out_of_scope_domain_boundary",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"function_name": "chat",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4S2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Service out-of-scope-domain branch now emits as a bounded policy refusal through the authorized service boundary helper.",
	},
	{
		"path_id": "service_known_unsupported_erp_domain_boundary",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"function_name": "chat",
		"answer_type": ANSWER_TYPE_POLICY_BOUNDARY,
		"migration_slice": "EC-4S2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Service known-unsupported ERP-domain branch now emits as a bounded policy refusal through the authorized service boundary helper.",
	},
	{
		"path_id": "visible_context_trace_inspection",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py",
		"function_name": "try_activate_visible_context_trace_inspection_response",
		"answer_type": ANSWER_TYPE_TRACE,
		"migration_slice": "EC-4T1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_LOW,
		"reason": "Visible-context trace inspection now emits as trace_debug_answer with explicit trace-debug control authority.",
	},
	{
		"path_id": "nbu_presentation_safe_response",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py",
		"function_name": "try_activate_nbu_presentation_response",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "NBU safe presentation responses now emit as control_meta_answer with activation, execution, and optional audit payloads staged behind authority.",
	},
	{
		"path_id": "clarification_show_options",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py",
		"function_name": "handle_pending_clarification_turn",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_LOW,
		"reason": "Clarification option rendering now emits as control_meta_answer with pending-control payloads staged behind authority.",
	},
	{
		"path_id": "clarification_pending_reask_or_stop",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py",
		"function_name": "handle_pending_clarification_turn",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_LOW,
		"reason": "Pending clarification re-ask/stop responses now emit as control_meta_answer and update pending state only after authorized emission.",
	},
	{
		"path_id": "recovery_guidance_answer",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py",
		"function_name": "handle_recovery_guidance_response",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T1",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Recovery guidance now emits as control_meta_answer with recovery/audit/observability payloads staged behind authority.",
	},
	{
		"path_id": "service_prior_branch_clarification_restore",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"function_name": "_handle_prior_branch_restore_reopen_pending_clarification",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_LOW,
		"reason": "Prior-branch pending clarification restore now emits as control_meta_answer with restore evidence staged behind authority.",
	},
	{
		"path_id": "service_compound_continue_completed",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"function_name": "chat",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Compound completed-sequence continuation now emits as control_meta_answer with control/audit payloads staged behind authority.",
	},
	{
		"path_id": "service_compound_stop",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
		"function_name": "chat",
		"answer_type": ANSWER_TYPE_CONTROL,
		"migration_slice": "EC-4T2",
		"authorization_helper": "emit_authorized_assistant_answer",
		"migration_status": "migrated_to_authorized_helper",
		"previous_risk_level": RISK_MEDIUM,
		"reason": "Compound stop response now emits as control_meta_answer with cancellation/audit payloads staged behind authority.",
	},
]


EC4_ALLOWED_PREFLIGHT_STATUSES = ["passed", "bounded"]
EC4_BLOCKED_PREFLIGHT_STATUSES = ["missing_authority", "incomplete_authority"]

EC4_DESIGN = {
	"design_status": "proposed_for_ec4_not_implemented_in_ec3",
	"central_helper": "emit_authorized_assistant_answer",
	"helper_location_recommendation": "qwen_chat/authorized_emission.py or qwen_chat/context/authorized_emission.py",
	"why_not_lowest_append_only": (
		"The low-level append helper receives role/content only and cannot know report family, policy boundary, "
		"grounding, answer class, or audit timing."
	),
	"inputs": [
		"session_doc",
		"answer_text",
		"answer_type",
		"execution_path",
		"interaction_contract",
		"followup_resolution",
		"runtime_trace_payload",
		"grounded_turn_context",
		"authority_context",
		"control_meta_authority",
	],
	"allow_rules": [
		"Allow preflight_status=passed for complete factual/governed/report/visible-context answers.",
		"Allow preflight_status=bounded only when a valid policy_boundary is present.",
		"Allow explicit control/meta/error emissions only when they are classified as non-business and carry control authority.",
	],
	"block_or_downgrade_rules": [
		"Block or downgrade missing_authority.",
		"Block incomplete authority.",
		"Block unbounded business answers without visible, governed, grounded, or policy authority.",
		"Block silent fallback that presents as a business answer.",
	],
	"migration_strategy": [
		"Start with dry-run reporting.",
		"Wrap high-risk business paths first: frontdoor, compiled support, reasoning, legacy runtime, entity follow-up, NBU governed requery.",
		"Then wrap medium-risk boundary/control paths.",
		"Finally restrict direct assistant append usage to the authorized helper plus explicit test fixtures.",
	],
}

EC4_TEST_REQUIREMENTS = [
	"business_answer_missing_authority_is_blocked_or_downgraded",
	"visible_context_answer_with_complete_authority_is_allowed",
	"governed_report_answer_with_complete_authority_is_allowed",
	"policy_boundary_answer_with_bounded_preflight_is_allowed",
	"policy_boundary_answer_without_policy_boundary_is_blocked",
	"reasoning_answer_requires_complete_authority",
	"legacy_runtime_business_answer_requires_complete_authority_or_downgrades",
	"entity_followup_success_attaches_final_authority_before_append",
	"control_meta_answer_requires_explicit_control_authority",
	"direct_assistant_append_inventory_does_not_gain_new_business_paths",
	"trace_inspection_exposes_preflight_and_authority_status",
]

NON_GOALS = [
	"no_hard_runtime_blocking_in_ec3",
	"no_model_role_strict_enforcement",
	"no_service_py_refactor",
	"no_duplicate_lane_cleanup",
	"no_release_packaging_cleanup",
	"no_new_business_family_behavior",
	"no_filter_mi_or_ux_work",
]


def _risk_counts(inventory: Sequence[Dict[str, Any]]) -> Dict[str, int]:
	counts = {RISK_HIGH: 0, RISK_MEDIUM: 0, RISK_LOW: 0}
	for item in inventory:
		risk = _clean_text(item.get("risk_level"))
		if risk in counts:
			counts[risk] += 1
	return counts


def _status_counts(inventory: Sequence[Dict[str, Any]]) -> Dict[str, int]:
	counts: Dict[str, int] = {}
	for item in inventory:
		status = _clean_text(item.get("authority_availability_status")) or "unknown"
		counts[status] = counts.get(status, 0) + 1
	return dict(sorted(counts.items()))


def _answer_type_counts(inventory: Sequence[Dict[str, Any]]) -> Dict[str, int]:
	counts: Dict[str, int] = {}
	for item in inventory:
		answer_type = _clean_text(item.get("answer_type")) or "unknown"
		counts[answer_type] = counts.get(answer_type, 0) + 1
	return dict(sorted(counts.items()))


def _merged_counts(*count_sets: Dict[str, int]) -> Dict[str, int]:
	merged: Dict[str, int] = {}
	for counts in count_sets:
		for key, value in counts.items():
			merged[key] = merged.get(key, 0) + int(value or 0)
	return dict(sorted(merged.items()))


def _high_risk_paths(inventory: Sequence[Dict[str, Any]]) -> List[str]:
	return [
		_clean_text(item.get("path_id"))
		for item in inventory
		if _clean_text(item.get("risk_level")) == RISK_HIGH
	]


def _missing_required_fields(inventory: Sequence[Dict[str, Any]]) -> Dict[str, List[str]]:
	required = [
		"path_id",
		"relative_file_path",
		"function_name",
		"line_reference",
		"answer_type",
		"authority_availability_status",
		"audit_timing",
		"risk_level",
		"ec4_action",
	]
	missing_by_path: Dict[str, List[str]] = {}
	for item in inventory:
		path_id = _clean_text(item.get("path_id")) or "unknown_path"
		missing = [field for field in required if not _clean_text(item.get(field))]
		if missing:
			missing_by_path[path_id] = missing
	return missing_by_path


def build_final_answer_emission_dry_run_report(
	*,
	reviewer: str = "codex_ec3",
	status_count: int | None = None,
) -> Dict[str, Any]:
	inventory = [dict(item) for item in EMISSION_PATH_INVENTORY]
	excluded_append_sites = [dict(item) for item in EXCLUDED_APPEND_SITES]
	authorized_append_sites = [dict(item) for item in AUTHORIZED_APPEND_SITES]
	migrated_authorized_paths = [dict(item) for item in MIGRATED_AUTHORIZED_PATHS]
	missing_required_fields = _missing_required_fields(inventory)
	high_risk_paths = _high_risk_paths(inventory)
	active_answer_type_counts = _answer_type_counts(inventory)
	migrated_answer_type_counts = _answer_type_counts(migrated_authorized_paths)
	answer_type_counts = _merged_counts(active_answer_type_counts, migrated_answer_type_counts)
	active_runtime_direct_count = sum(1 for item in inventory if bool(item.get("direct_assistant_append")))
	excluded_non_runtime_count = sum(1 for item in excluded_append_sites if bool(item.get("direct_assistant_append")))
	authorized_runtime_sink_count = sum(1 for item in authorized_append_sites if bool(item.get("direct_assistant_append")))
	required_answer_types = [
		ANSWER_TYPE_BUSINESS_FACTUAL,
		ANSWER_TYPE_VISIBLE_CONTEXT,
		ANSWER_TYPE_GOVERNED_REPORT,
		ANSWER_TYPE_POLICY_BOUNDARY,
		ANSWER_TYPE_REASONING,
		ANSWER_TYPE_TRACE,
		ANSWER_TYPE_ERROR,
		ANSWER_TYPE_CONTROL,
	]
	missing_answer_types = [
		answer_type
		for answer_type in required_answer_types
		if answer_type_counts.get(answer_type, 0) <= 0
	]
	ready = not missing_required_fields and not missing_answer_types and bool(high_risk_paths)
	report = {
		"type": FINAL_ANSWER_EMISSION_DRY_RUN_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": FINAL_ANSWER_EMISSION_DRY_RUN_SUITE_ID,
		"generated_at": _utc_now(),
		"reviewer": _clean_text(reviewer) or "codex_ec3",
		"scope": "final_answer_hard_gate_design_dry_run_only",
		"hard_runtime_blocking_enabled": False,
		"runtime_behavior_changed": False,
		"inventory_count": len(inventory),
		"active_runtime_direct_assistant_append_count": active_runtime_direct_count,
		"authorized_runtime_append_sink_count": authorized_runtime_sink_count,
		"excluded_non_runtime_append_count": excluded_non_runtime_count,
		"total_source_assistant_append_sites_observed": active_runtime_direct_count + authorized_runtime_sink_count + excluded_non_runtime_count,
		"direct_assistant_append_count": active_runtime_direct_count,
		"direct_assistant_append_count_note": "Deprecated alias for active_runtime_direct_assistant_append_count.",
		"requires_hard_gate_count": sum(1 for item in inventory if bool(item.get("requires_hard_gate"))),
		"risk_counts": _risk_counts(inventory),
		"authority_availability_counts": _status_counts(inventory),
		"answer_type_counts": answer_type_counts,
		"active_unmanaged_answer_type_counts": active_answer_type_counts,
		"migrated_authorized_answer_type_counts": migrated_answer_type_counts,
		"high_risk_paths": high_risk_paths,
		"missing_required_fields": missing_required_fields,
		"missing_answer_types": missing_answer_types,
		"current_dirty_status_count": status_count,
		"emission_path_inventory": inventory,
		"authorized_append_sites": authorized_append_sites,
		"migrated_authorized_paths": migrated_authorized_paths,
		"excluded_append_sites": excluded_append_sites,
		"proposed_ec4_design": dict(EC4_DESIGN),
		"ec4_allowed_preflight_statuses": list(EC4_ALLOWED_PREFLIGHT_STATUSES),
		"ec4_blocked_preflight_statuses": list(EC4_BLOCKED_PREFLIGHT_STATUSES),
		"ec4_test_requirements": list(EC4_TEST_REQUIREMENTS),
		"non_goals": list(NON_GOALS),
		"final_recommendation": RECOMMENDATION_READY if ready else RECOMMENDATION_BLOCKED,
		"recommendation_reason": (
			"Dry-run inventory is complete enough for counterpart review; high-risk paths are intentionally exposed for EC-4."
			if ready
			else "Dry-run inventory is missing required fields or answer-type coverage."
		),
	}
	return report


def render_final_answer_emission_dry_run_markdown(report: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# EC-3 Final-Answer Hard Gate Design / Dry Run",
		"",
		"## Executive Verdict",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		f"- Scope: `{_clean_text(report.get('scope'))}`",
		f"- Hard runtime blocking enabled: `{bool(report.get('hard_runtime_blocking_enabled'))}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Inventory count: `{int(report.get('inventory_count') or 0)}`",
		f"- Active runtime direct assistant append count: `{int(report.get('active_runtime_direct_assistant_append_count') or 0)}`",
		f"- Authorized runtime append sink count: `{int(report.get('authorized_runtime_append_sink_count') or 0)}`",
		f"- Excluded non-runtime append count: `{int(report.get('excluded_non_runtime_append_count') or 0)}`",
		f"- Total source assistant append sites observed: `{int(report.get('total_source_assistant_append_sites_observed') or 0)}`",
		f"- Current dirty status count: `{report.get('current_dirty_status_count')}`",
		"",
		"EC-3 is a dry-run and design slice only. It intentionally does not block or change runtime emissions.",
		"",
		"## Risk Summary",
		"",
		"| Risk | Count |",
		"|---|---:|",
	]
	for risk, count in dict(report.get("risk_counts") or {}).items():
		lines.append(f"| {risk} | {count} |")
	lines.extend(["", "## Authority Availability", "", "| Status | Count |", "|---|---:|"])
	for status, count in dict(report.get("authority_availability_counts") or {}).items():
		lines.append(f"| {status} | {count} |")
	lines.extend(["", "## Emission Path Inventory", "", "| Path | Answer type | Authority status | Audit timing | Risk |", "|---|---|---|---|---|"])
	for item in list(report.get("emission_path_inventory") or []):
		lines.append(
			"| {path} | {answer_type} | {status} | {timing} | {risk} |".format(
				path=_clean_text(item.get("path_id")),
				answer_type=_clean_text(item.get("answer_type")),
				status=_clean_text(item.get("authority_availability_status")),
				timing=_clean_text(item.get("audit_timing")),
				risk=_clean_text(item.get("risk_level")),
			)
		)
	lines.extend(["", "## Authorized Append Sinks", "", "| Site | File | Line | Reason |", "|---|---|---:|---|"])
	for item in list(report.get("authorized_append_sites") or []):
		lines.append(
			"| {site} | {path} | {line} | {reason} |".format(
				site=_clean_text(item.get("site_id")),
				path=_clean_text(item.get("relative_file_path")),
				line=_clean_text(item.get("line_reference")),
				reason=_clean_text(item.get("authorization_reason")),
			)
		)
	lines.extend(["", "## Migrated Authorized Paths", "", "| Path | File | Slice | Reason |", "|---|---|---:|---|"])
	for item in list(report.get("migrated_authorized_paths") or []):
		lines.append(
			"| {path_id} | {path} | {slice} | {reason} |".format(
				path_id=_clean_text(item.get("path_id")),
				path=_clean_text(item.get("relative_file_path")),
				slice=_clean_text(item.get("migration_slice")),
				reason=_clean_text(item.get("reason")),
			)
		)
	lines.extend(["", "## Excluded Append Sites", "", "| Site | File | Line | Reason |", "|---|---|---:|---|"])
	for item in list(report.get("excluded_append_sites") or []):
		lines.append(
			"| {site} | {path} | {line} | {reason} |".format(
				site=_clean_text(item.get("site_id")),
				path=_clean_text(item.get("relative_file_path")),
				line=_clean_text(item.get("line_reference")),
				reason=_clean_text(item.get("exclusion_reason")),
			)
		)
	lines.extend(["", "## High-Risk Paths"])
	for path_id in _clean_list(report.get("high_risk_paths")):
		lines.append(f"- `{path_id}`")
	lines.extend(["", "## Proposed EC-4 Design"])
	design = dict(report.get("proposed_ec4_design") or {})
	lines.append(f"- Central helper: `{_clean_text(design.get('central_helper'))}`")
	lines.append(f"- Recommended location: `{_clean_text(design.get('helper_location_recommendation'))}`")
	lines.append(f"- Why not lowest append only: {_clean_text(design.get('why_not_lowest_append_only'))}")
	lines.extend(["", "Allowed rules:"])
	for rule in _clean_list(design.get("allow_rules")):
		lines.append(f"- {rule}")
	lines.extend(["", "Block or downgrade rules:"])
	for rule in _clean_list(design.get("block_or_downgrade_rules")):
		lines.append(f"- {rule}")
	lines.extend(["", "Migration strategy:"])
	for step in _clean_list(design.get("migration_strategy")):
		lines.append(f"- {step}")
	lines.extend(["", "## EC-4 Tests Required"])
	for test_id in _clean_list(report.get("ec4_test_requirements")):
		lines.append(f"- `{test_id}`")
	lines.extend(["", "## Non-Goals"])
	for non_goal in _clean_list(report.get("non_goals")):
		lines.append(f"- `{non_goal}`")
	lines.extend(["", "## Final Recommendation", "", f"`{_clean_text(report.get('final_recommendation'))}`", ""])
	return "\n".join(lines)


def write_final_answer_emission_dry_run_files(
	*,
	root_path: str | Path = ".",
	out_dir: str = DEFAULT_EC3_OUT_DIR,
	reviewer: str = "codex_ec3",
	status_count: int | None = None,
) -> Dict[str, Any]:
	report = build_final_answer_emission_dry_run_report(reviewer=reviewer, status_count=status_count)
	target_dir = _project_path(root_path, out_dir)
	target_dir.mkdir(parents=True, exist_ok=True)
	json_path = target_dir / DEFAULT_EC3_REPORT_JSON
	markdown_path = target_dir / DEFAULT_EC3_REPORT_MARKDOWN
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_final_answer_emission_dry_run_markdown(report), encoding="utf-8")
	report["report_json_artifact_path"] = str(json_path)
	report["report_markdown_artifact_path"] = str(markdown_path)
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	return report


def main(argv: Sequence[str] | None = None, stdout: TextIO | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-3 final-answer emission dry-run report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC3_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec3")
	parser.add_argument("--status-count", type=int, default=None)
	args = parser.parse_args(list(argv) if argv is not None else None)
	report = write_final_answer_emission_dry_run_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
		status_count=args.status_count,
	)
	stream = stdout
	if stream is not None:
		stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
	return 0 if report.get("final_recommendation") == RECOMMENDATION_READY else 1


if __name__ == "__main__":
	raise SystemExit(main())
