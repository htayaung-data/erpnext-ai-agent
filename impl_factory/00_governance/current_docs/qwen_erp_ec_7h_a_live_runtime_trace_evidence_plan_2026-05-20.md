# EC-7H-A Live Runtime Trace Evidence Plan

Decision: ec_7h_a_live_runtime_trace_evidence_plan_ready_for_counterpart_review

Date: 2026-05-20
Generated: 2026-05-20T13:09:42+00:00
Branch context: main post-merge verification worktree
Head: 1504158
Included package commit: d3ce165
Runtime effect: `none`
Strict enforcement enabled: `false`
Deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-A defines how to collect live runtime trace evidence after PR #4 without enabling strict enforcement or changing runtime behavior. EC-7D, EC-7E, EC-7F, and EC-7G proved backend metadata contracts, mocked runtime paths, helper provenance, deterministic/control coverage, and soft-gate reporting. They did not prove live Frappe/browser/ERP traces under a real runtime environment.

The goal of EC-7H is evidence collection only. It should answer whether real runtime payloads carry the same metadata and authority surfaces proven by backend tests before any future hard-enforcement discussion.

## Scope

EC-7H-A is report/plan only.

Allowed in future EC-7H evidence slices after approval:

- Run controlled live/staging runtime turns against the merged main build.
- Capture redacted session/tool/audit/metadata payloads already produced by runtime code.
- Compare live trace rows against EC-7G-B soft-gate expectations.
- Record release-readiness gaps as evidence, not runtime blocks.

Forbidden in EC-7H-A and not approved by this plan:

- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_deployment`
- `no_runtime_behavior_change`
- `no_route_or_model_selection_change`
- `no_answer_text_change`
- `no_report_selection_change`
- `no_new_instrumentation_without_approval`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Evidence Source Boundary

| Evidence type | Current status after PR #4 | EC-7H-A position |
|---|---|---|
| Backend contract tests | Closed through EC-7D/E/F/G | Sufficient for backend readiness, not live UAT. |
| Mocked runtime probes | Closed through EC-7F | Sufficient for call-path metadata proof, not hard enforcement. |
| Soft-gate dry run | Accepted through EC-7G-B/A | Observe/report only, no runtime effect. |
| Evidence-source classification | Accepted through EC-7G-C | Shows live trace evidence is still missing. |
| Live runtime trace evidence | Not yet collected | Required before EC-7H closure and any strict-enforcement decision. |

## Trace Capture Principles

- Capture only existing runtime outputs: session messages, tool payloads, audit envelopes, authorized-emission contracts, runtime metadata envelopes, model-role observability payloads, and final-answer authority surfaces.
- Redact user text, entity names, customer/vendor names, document IDs, monetary values, and freeform model text unless explicitly approved for test fixtures.
- Preserve structural fields: `lane_id`, `lane_class`, `model_role`, `model_name`, `fallback_used`, `fallback_reason`, `role_compliance`, `metadata_status`, `strict_readiness_status`, `strict_enforcement_ready`, `authority_source`, `final_answer_authority_status`, `preflight_status`, `answer_type`, payload order, and blocked/emitted flags.
- Do not treat trace collection failure as a user-facing runtime failure. Trace gaps should become soft-gate evidence warnings or release-readiness blockers only.
- Compare live trace evidence against EC-7F probe expectations and EC-7G-B soft-gate rows.

## Minimum Live Trace Evidence Set

| Group | Lanes | Required live scenarios | Required proof |
|---|---|---|---|
| Light semantic | `frontdoor_semantic_classification`, `fresh_query_interpretation`, `followup_interpretation`, `semantic_reasoning_activation`, `semantic_repair_intent` | accepted success; degraded/low-confidence/invalid; runtime-error or mocked failure in staging if available | Accepted complete metadata may be strict-ready; degraded/fallback/error is not strict-ready; fallback fields survive. |
| Heavy reasoning | `business_reasoning_answer`, reasoning execution metadata surface | success; missing metadata; fallback/runtime error; authority-separation case | Heavy reasoning provenance is present and does not bypass final-answer authority. |
| NBU shadow | `nbu_shadow_observation` | success observation; degraded observation; routing unchanged | Shadow metadata remains observe-only and cannot drive final answer authority. |
| Model-backed helpers | `frontdoor_render`, `clarification_system`, `artifact_narrative` | helper success; template/fallback; runtime failure/missing metadata | Helper metadata is provenance-only and cannot satisfy business final-answer authority. |
| Governed-tool helpers | `composite_reads`, `fresh_query_compiled_read_runtime` | deterministic success; model-backed fallback; governed-tool ok=false/runtime failure | Governed-tool runtime metadata is visible; fallback/error is not strict-ready; report authority remains separate. |
| Deterministic/report | `compiled_support_result_answer`, `legacy_runtime_business_or_boundary_answer`, `artifact_boundary`, `entity_followup`, `nbu_governed_requery_entity_detail` | governed/report success; missing authority; validation/boundary case where applicable | Deterministic metadata is covered, strict readiness is not-applicable, and blocked authority leaks no answer/evidence payloads. |
| Visible-context deterministic | `visible_context_followup`, `local_followup_transform` | success; blocked authority; fallback/degraded if reachable | Metadata is deterministic, authority is explicit, blocked authority has no assistant/answer/tool leak. |
| Policy/control/error | `runtime_gate`, `service_policy_control_responses`, `clarification_control`, `nbu_safe_response_activation`, `visible_context_trace_inspection`, error fallback paths | bounded policy response; control response; error fallback; blocked/missing authority | Policy/control/error metadata is explicit, not AI strict-ready, and final-answer authority remains correct. |
| Cross-cutting closure | authorized emission, append inventory, raw append scan | same build under review | Direct assistant inventory remains `0 / 1 / 27`; raw scan only reports `authorized_emission.py:271` and `authorized_emission.py:327`. |

## Per-Trace Required Fields

Each captured live trace record should include these fields or a documented `missing` reason:

- `trace_id`
- `session_id_hash`
- `request_id_hash`
- `scenario_id`
- `lane_id`
- `lane_class`
- `model_role`
- `model_name`
- `fallback_used`
- `fallback_reason`
- `role_compliance`
- `metadata_status`
- `strict_readiness_status`
- `strict_enforcement_ready`
- `runtime_probe_required`
- `metadata_source`
- `authority_source`
- `final_answer_authority_status`
- `final_answer_authority_source`
- `preflight_status`
- `answer_type`
- `authorized_emission.emitted`
- `authorized_emission.blocked`
- `authorized_emission.block_reason`
- `payload_order_summary`
- `assistant_message_count_delta`
- `tool_payload_count_delta`
- `leak_check_result`
- `redaction_status`

## Pass / Warn / Block Criteria

| Decision | Meaning | Runtime effect |
|---|---|---|
| `live_trace_pass` | Live trace matches EC-7 metadata, authority, and no-leak expectations. | none |
| `live_trace_warn` | Trace is structurally safe but incomplete, degraded, fallback, missing model metadata, or insufficient for hard enforcement. | none |
| `live_trace_block_release` | Trace shows missing final-answer authority, unexpected assistant append, helper metadata granting business authority, answer/evidence leak, or missing mandatory metadata in a release-critical lane. | none |
| `not_applicable_deterministic` | Deterministic/control lane is explicit and not AI strict-enforcement target. | none |
| `not_collected` | Scenario has no live trace yet. | none |

A live trace blocker must block release-readiness discussion, not user-facing runtime execution.

## Proposed EC-7H Sequence

| Slice | Purpose | Scope |
|---|---|---|
| EC-7H-A | Live runtime trace evidence plan | Report only, this slice. |
| EC-7H-B | Trace fixture and redaction protocol | Plan/test harness design only unless approved; define redaction, artifact schema, and safe capture workflow. |
| EC-7H-C | Light semantic live trace collection | Collect traces only; no enforcement or behavior changes. |
| EC-7H-D | Heavy reasoning and NBU shadow live trace collection | Collect traces only; prove observe-only and authority separation. |
| EC-7H-E | Helper/tool runtime live trace collection | Collect traces only; prove helper/tool provenance is not final-answer authority. |
| EC-7H-F | Deterministic/control live trace collection | Collect traces only; prove not-applicable strict readiness and no-leak behavior. |
| EC-7H-G | Live trace closure report | Decide whether EC-7H evidence is sufficient for future strict-readiness dry-run promotion discussion. |

Do not proceed to strict enforcement directly after EC-7H. A separate EC-7I or later enforcement-decision gate should be required.

## Required Verification For Future Live Trace Slices

Each future EC-7H trace-collection slice should rerun:

- `python3 scripts/check_qwen_enterprise_guardrails.py`
- Fake-Frappe service import for non-live test harness contexts
- Direct assistant inventory: expected `0 / 1 / 27`
- Formal raw assistant append scan: expected only `authorized_emission.py:271` and `authorized_emission.py:327`
- Relevant EC-7 metadata/probe/soft-gate tests
- Authorized-emission and final-answer dry-run contracts
- Excluded artifact scan for generated trace evidence before any packaging

## Risks And Open Questions

- Live trace capture may expose sensitive ERP/customer data; redaction must be mandatory before sharing with Counterpart/QA.
- Some negative scenarios may be hard to trigger naturally; future slices should prefer controlled staging fixtures or mocked runtime failures over production-like disruption.
- Trace storage policy is not yet defined; EC-7H-B should decide which trace artifacts belong in repo, archive, or external QA evidence storage.
- Strict enforcement remains unsafe until live trace evidence covers success, fallback, runtime-error, missing metadata, and authority-failure cases.

## Non-Goals

- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_live_deployment`
- `no_runtime_behavior_change`
- `no_route_model_answer_or_report_selection_change`
- `no_packaging_or_commit`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7h_a_live_runtime_trace_evidence_plan_ready_for_counterpart_review`

EC-7H-A is ready for Counterpart/QA review as a plan-only gate. The recommended next slice after acceptance is EC-7H-B trace fixture and redaction protocol, still without enforcement or runtime behavior change.
