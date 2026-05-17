# EC-3 Final-Answer Hard Gate Design / Dry Run

## Executive Verdict
- Final recommendation: `enterprise_cleanup_ec_3_ready_for_counterpart_review`
- Scope: `final_answer_hard_gate_design_dry_run_only`
- Hard runtime blocking enabled: `False`
- Runtime behavior changed: `False`
- Inventory count: `1`
- Active runtime direct assistant append count: `0`
- Authorized runtime append sink count: `2`
- Excluded non-runtime append count: `1`
- Total source assistant append sites observed: `3`
- Current dirty status count: `307`

EC-3 is a dry-run and design slice only. It intentionally does not block or change runtime emissions.

## Risk Summary

| Risk | Count |
|---|---:|
| high | 1 |
| medium | 0 |
| low | 0 |

## Authority Availability

| Status | Count |
|---|---:|
| not_applicable_low_level_append_wrapper | 1 |

## Emission Path Inventory

| Path | Answer type | Authority status | Audit timing | Risk |
|---|---|---|---|---|
| service_append_message_wrapper | low_level_append_helper | not_applicable_low_level_append_wrapper | no_answer_context | high |

## Authorized Append Sinks

| Site | File | Line | Reason |
|---|---|---:|---|
| authorized_emission_control_meta_sink | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py | 271 | Centralized helper append after explicit control/meta authority validation. |
| authorized_emission_business_sink | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py | 327 | Centralized helper append after final-answer authority preflight validation. |

## Migrated Authorized Paths

| Path | File | Slice | Reason |
|---|---|---:|---|
| visible_context_followup_filter_boundary | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py | EC-4A | Filter/readiness visible-context boundary now validates authority before appending the assistant answer. |
| visible_context_followup_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_followup_activation.py | EC-4A | Resolved, boundary, out-of-range, and clarification visible-context answers now emit through the authorized helper. |
| frontdoor_lane_package_governed_report_or_projection | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py | EC-4C | Active package frontdoor governed/report, bounded-refusal, and control/meta answers now emit through the authorized helper. |
| frontdoor_lane_package_governed_kpi_definition | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py | EC-4C | Governed KPI definitions now emit as business-facing factual answers only with deterministic registry authority. |
| compiled_support_result_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support.py | EC-4E | Compiled-support governed/report, bounded-refusal, control, and error fallback answers now emit through the authorized helper. |
| reasoning_lane_business_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py | EC-4G | Answered grounded ERP reasoning now emits through the authorized helper as reasoning_business_consultant_answer with passed authority required. |
| reasoning_lane_guardrail_boundary | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py | EC-4G | Reasoning guardrail/boundary output now emits through the authorized helper as policy_boundary_refusal with bounded authority required. |
| entity_followup_failure | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py | EC-4M | Entity follow-up failure now emits through the authorized helper with explicit error fallback authority. |
| entity_followup_success | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py | EC-4M | Entity follow-up success now appends artifact, grounded turn, trace, audit, and authorized emission before assistant answer. |
| nbu_governed_requery_entity_detail | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py | EC-4K | NBU governed requery entity-detail answers now build authority before assistant emission and block missing authority without answer_text leakage. |
| legacy_runtime_client_error | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py | EC-4I | Legacy runtime client errors now emit through the authorized helper with explicit error fallback authority. |
| legacy_runtime_business_or_boundary_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py | EC-4I | Legacy runtime governed output and grounded-validation boundaries now build authority before assistant emission. |
| artifact_boundary_evidence_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py | EC-4R1 | Artifact direct-evidence answers now validate governed artifact authority before assistant or evidence-payload emission. |
| artifact_boundary_grounded_evidence_refusal | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py | EC-4R1 | Grounded-evidence artifact refusals now emit as bounded policy-boundary answers through the authorized helper. |
| artifact_boundary_enrichment_refusal | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/artifact_boundary_lane.py | EC-4R1 | Artifact-enrichment refusals now emit as bounded policy-boundary answers through the authorized helper. |
| local_followup_transform | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/local_followup_support.py | EC-4R2 | Local follow-up transforms now validate visible/grounded authority before assistant or transform payload emission. |
| runtime_gate_out_of_scope_boundary | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/runtime_gate_lane.py | EC-4S1 | Runtime-gate out-of-scope ERP-domain boundary now emits as a bounded policy refusal only after authority validation. |
| service_out_of_scope_domain_boundary | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | EC-4S2 | Service out-of-scope-domain branch now emits as a bounded policy refusal through the authorized service boundary helper. |
| service_known_unsupported_erp_domain_boundary | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | EC-4S2 | Service known-unsupported ERP-domain branch now emits as a bounded policy refusal through the authorized service boundary helper. |
| visible_context_trace_inspection | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/visible_context_trace_inspection.py | EC-4T1 | Visible-context trace inspection now emits as trace_debug_answer with explicit trace-debug control authority. |
| nbu_presentation_safe_response | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_service_activation.py | EC-4T1 | NBU safe presentation responses now emit as control_meta_answer with activation, execution, and optional audit payloads staged behind authority. |
| clarification_show_options | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py | EC-4T1 | Clarification option rendering now emits as control_meta_answer with pending-control payloads staged behind authority. |
| clarification_pending_reask_or_stop | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py | EC-4T1 | Pending clarification re-ask/stop responses now emit as control_meta_answer and update pending state only after authorized emission. |
| recovery_guidance_answer | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/recovery_guidance_support.py | EC-4T1 | Recovery guidance now emits as control_meta_answer with recovery/audit/observability payloads staged behind authority. |
| service_prior_branch_clarification_restore | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | EC-4T2 | Prior-branch pending clarification restore now emits as control_meta_answer with restore evidence staged behind authority. |
| service_compound_continue_completed | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | EC-4T2 | Compound completed-sequence continuation now emits as control_meta_answer with control/audit payloads staged behind authority. |
| service_compound_stop | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py | EC-4T2 | Compound stop response now emits as control_meta_answer with cancellation/audit payloads staged behind authority. |

## Excluded Append Sites

| Site | File | Line | Reason |
|---|---|---:|---|
| phase8_quantity_recovery_smoke_seed | impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase8_hardening_support.py | 68 | Smoke/recovery seed helper, not active user-facing runtime emission. |

## High-Risk Paths
- `service_append_message_wrapper`

## Proposed EC-4 Design
- Central helper: `emit_authorized_assistant_answer`
- Recommended location: `qwen_chat/authorized_emission.py or qwen_chat/context/authorized_emission.py`
- Why not lowest append only: The low-level append helper receives role/content only and cannot know report family, policy boundary, grounding, answer class, or audit timing.

Allowed rules:
- Allow preflight_status=passed for complete factual/governed/report/visible-context answers.
- Allow preflight_status=bounded only when a valid policy_boundary is present.
- Allow explicit control/meta/error emissions only when they are classified as non-business and carry control authority.

Block or downgrade rules:
- Block or downgrade missing_authority.
- Block incomplete authority.
- Block unbounded business answers without visible, governed, grounded, or policy authority.
- Block silent fallback that presents as a business answer.

Migration strategy:
- Start with dry-run reporting.
- Wrap high-risk business paths first: frontdoor, compiled support, reasoning, legacy runtime, entity follow-up, NBU governed requery.
- Then wrap medium-risk boundary/control paths.
- Finally restrict direct assistant append usage to the authorized helper plus explicit test fixtures.

## EC-4 Tests Required
- `business_answer_missing_authority_is_blocked_or_downgraded`
- `visible_context_answer_with_complete_authority_is_allowed`
- `governed_report_answer_with_complete_authority_is_allowed`
- `policy_boundary_answer_with_bounded_preflight_is_allowed`
- `policy_boundary_answer_without_policy_boundary_is_blocked`
- `reasoning_answer_requires_complete_authority`
- `legacy_runtime_business_answer_requires_complete_authority_or_downgrades`
- `entity_followup_success_attaches_final_authority_before_append`
- `control_meta_answer_requires_explicit_control_authority`
- `direct_assistant_append_inventory_does_not_gain_new_business_paths`
- `trace_inspection_exposes_preflight_and_authority_status`

## Non-Goals
- `no_hard_runtime_blocking_in_ec3`
- `no_model_role_strict_enforcement`
- `no_service_py_refactor`
- `no_duplicate_lane_cleanup`
- `no_release_packaging_cleanup`
- `no_new_business_family_behavior`
- `no_filter_mi_or_ux_work`

## Final Recommendation

`enterprise_cleanup_ec_3_ready_for_counterpart_review`
