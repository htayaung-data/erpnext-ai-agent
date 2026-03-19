# Phase 4 Runtime Signal Map

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: map Phase 4 KPIs to actual runtime, replay, and manual evidence sources  
Status: first operational signal baseline after KPI/SLO specification

## 1. Purpose

This document answers a simple operational question:

for each KPI, where does the evidence actually come from today?

This is the bridge between:

1. enterprise KPI definitions
2. current runtime telemetry
3. replay evidence
4. browser/manual evidence

The goal is to avoid guessing. If a field is missing, this document marks it as missing.

## 2. Signal Sources Available Today

The current system already exposes useful control surfaces.

### 2.1 Live Runtime Tool and Audit Surfaces

1. `audit_turn`
2. `v7_business_request_spec`
3. `v7_quality_gate`
4. `v7_clarification_policy`
5. `v7_read_engine`
6. `pending_state`
7. `last_result`
8. `error_envelope`

### 2.2 Replay and Automation Surfaces

1. Phase 6 manifest replay outputs
2. Phase 6 canary replay outputs
3. semantic assertion results
4. suite summaries and class-level first-run metrics
5. duration metrics already computed in replay tooling

### 2.3 Manual Evidence Surfaces

1. browser/manual golden packs
2. standing smoke flows
3. screenshots and closure notes
4. incident register entries

## 3. Field Inventory

### 3.1 `audit_turn`

Current observed fields:

1. `type`
2. `version`
3. `ts`
4. `turn_id`
5. `session_name`
6. `user`
7. `message_preview`
8. `intent`
9. `planner_output`
10. `tool_invocation_summary`
11. `result_meta.payload_type`
12. `result_meta.payload_hash_sha256`
13. `result_meta.duration_ms`
14. `user_visible_response`
15. `error_envelope`

Operational value:

1. turn-level runtime timing
2. planner output linkage
3. visible response snapshot
4. error envelope presence

Current limitation:

the legacy top-level `audit_turn` fields remain useful for backward compatibility, but the canonical operational fields now live under `audit_turn.turn_audit_envelope`. Downstream tooling still needs to consume that unified block consistently.

### 3.2 `v7_business_request_spec`

Current observed fields:

1. `schema_valid`
2. `schema_errors`
3. `outer_attempt_count`
4. `spec.intent`
5. `spec.task_type`
6. `spec.task_class`
7. `spec.metric`
8. `spec.domain`
9. `spec.group_by`
10. `spec.filters`
11. `spec.output_contract`

Operational value:

1. class-level KPI segmentation
2. supported-turn eligibility
3. output-shape expectation linkage
4. follow-up and comparison shape analysis

### 3.3 `v7_quality_gate`

Current observed fields:

1. `verdict`
2. `failed_check_ids`
3. `failed_failure_classes`
4. `repairable_failure_classes`
5. `hard_failure_classes`
6. `hard_fail_check_ids`
7. `repairable_check_ids`

Operational value:

1. output-shape correctness tracking
2. quality failure-family tracking
3. repair versus hard-fail trend tracking
4. unsupported and gating correctness support

### 3.4 `v7_clarification_policy`

Current observed fields:

1. `should_clarify`
2. `reason`

Operational value:

1. clarification rate tracking
2. blocker reason-code tracking

### 3.5 `pending_state`

Current observed fields:

1. `mode`
2. `base_question`
3. `clarification_question`
4. `clarification_options`
5. `options`
6. `clarification_round`
7. `clarification_reason`

Operational value:

1. planner clarify detection
2. clarification loop detection
3. write confirmation tracking
4. follow-up pending-state diagnostics

### 3.6 `v7_read_engine`

Current observed fields:

1. `selected_report`
2. `selected_score`
3. `max_steps`
4. `executed_steps`
5. `repair_attempts`
6. `quality_verdict`
7. `failed_check_ids`
8. `repeated_call_guard_triggered`
9. `step_trace`

Operational value:

1. fallback and repair rate analysis
2. repeated-call guard monitoring
3. selected report diagnostics
4. execution loop troubleshooting

### 3.7 Replay Runner Fields

Current observed fields in replay actuals and suite summaries:

1. `assistant_type`
2. `assistant_title`
3. `rows`
4. `columns`
5. `column_labels`
6. `pending_mode`
7. `clarification`
8. `meta_clarification`
9. `business_request_spec`
10. `result_quality_gate`
11. `quality_verdict`
12. `quality_failed_check_ids`
13. `duration_ms`
14. class-level pass/fail metrics
15. suite-level first-run pass metrics
16. latency p50/p95 in replay reports

Operational value:

1. formal gate measurement
2. weekly trend baselines
3. class-level regression tracking

## 4. KPI to Signal Mapping

## KPI-01 Wrong-Report Rate

Primary evidence today:

1. replay pass/fail and semantic assertions
2. browser/manual standing pack results
3. incident register entries for live escapes

Runtime fields that support diagnosis:

1. `v7_business_request_spec.spec.task_class`
2. `v7_read_engine.selected_report`
3. `audit_turn.user_visible_response`
4. `result_quality_gate.failed_check_ids`

Availability status:

`Partially available today`

Reason:

we can measure wrong-report rate reliably from replay and manual evidence now, but not yet from a fully automated live production event stream.

## KPI-02 First-Turn Success Rate

Primary evidence today:

1. replay first-run results
2. browser/manual standing pack

Runtime fields that support diagnosis:

1. `pending_state.mode`
2. `v7_quality_gate.verdict`
3. `v7_read_engine.repair_attempts`
4. `audit_turn.result_meta.payload_type`

Availability status:

`Available for offline control; partial for live runtime`

## KPI-03 Follow-Up Accuracy

Primary evidence today:

1. `multiturn_context` replay suite
2. manual/browser follow-up packs
3. incident register for contamination or carryover defects

Runtime fields that support diagnosis:

1. `pending_state`
2. session active-result metadata
3. `v7_business_request_spec`
4. `audit_turn.intent`

Availability status:

`Available for offline control; not yet fully automated for live trend reporting`

## KPI-04 Unnecessary Clarification Rate

Primary evidence today:

1. replay classification
2. browser/manual evidence

Runtime fields that support measurement:

1. `v7_clarification_policy.should_clarify`
2. `v7_clarification_policy.reason`
3. `pending_state.mode`
4. `pending_state.clarification_reason`

Availability status:

`Available with moderate confidence`

Note:

judging whether a clarification was unnecessary still requires governed review logic, not just raw field counting.

## KPI-05 Clarification Loop Rate

Primary evidence today:

1. multiturn replay
2. browser/manual follow-up pack

Runtime fields that support measurement:

1. `pending_state.mode`
2. `pending_state.clarification_round`
3. repeated clarification `audit_turn` sequence

Availability status:

`Partially available today`

Gap:

loop detection needs a canonical operational counting rule over conversation windows.

## KPI-06 Output-Shape Correctness

Primary evidence today:

1. replay semantic assertions
2. browser/manual goldens

Runtime fields that support diagnosis:

1. `v7_quality_gate.verdict`
2. `v7_quality_gate.failed_check_ids`
3. `audit_turn.user_visible_response`
4. replay `column_labels`

Availability status:

`Strongly available through replay/manual; partial in live runtime`

## KPI-07 Unsupported / No-Data / Permission Envelope Correctness

Primary evidence today:

1. replay packs
2. browser/manual evidence
3. incident records

Runtime fields that support measurement:

1. `error_envelope`
2. `pending_state.mode`
3. `v7_quality_gate.hard_failure_classes`
4. visible assistant text and envelope type

Availability status:

`Partially available today`

Gap:

permission and security-policy outcomes are not yet exposed as a dedicated canonical runtime field.

## KPI-08 Write-Safety Violations

Primary evidence today:

1. write-safety replay pack
2. browser/manual write pack
3. incident register

Runtime fields that support measurement:

1. `pending_state.mode == write_confirmation`
2. write response payloads
3. error or block envelopes on write attempts

Availability status:

`Available for governed review; not yet represented as a dedicated live counter`

## KPI-09 P95 Latency by Class

Primary evidence today:

1. replay runner durations
2. release gate latency summaries

Runtime fields that support measurement:

1. `audit_turn.result_meta.duration_ms`
2. `v7_business_request_spec.spec.task_class`

Availability status:

`Available`

Gap:

latency is available, but class-specific SLA thresholds still need final approval and possibly cleaner runtime aggregation.

## KPI-10 Fallback Rate

Primary evidence today:

1. `v7_read_engine.repair_attempts`
2. `v7_read_engine.repeated_call_guard_triggered`
3. `pending_state.mode == planner_clarify`
4. `v7_quality_gate.repairable_failure_classes`

Availability status:

`Available with moderate confidence`

Gap:

the system does not yet expose one canonical `fallback_used` boolean, so the first version will use composed logic from existing fields.

## KPI-11 Incident Reopen Rate

Primary evidence today:

1. incident register

Availability status:

`Available once Phase 4 incident operations begins`

Gap:

this depends on disciplined operational process, not runtime instrumentation.

## KPI-12 Incident Closure Discipline

Primary evidence today:

1. incident register
2. linked replay and browser evidence

Availability status:

`Available once Phase 4 incident operations begins`

## KPI-13 Audit Envelope Completeness

Primary evidence today:

1. `audit_turn`
2. debug replay traces
3. chat-service turn audit payloads

Runtime fields that support measurement:

1. `audit_turn` presence
2. `audit_turn.result_meta.duration_ms`
3. `audit_turn.planner_output`
4. `audit_turn.user_visible_response`
5. related tool messages that currently carry split audit information

Availability status:

`Partially available today`

Gap:

the current audit data is useful but still distributed across multiple structures rather than emitted as one canonical contract-complete envelope.

## KPI-14 Behavior-Class Mandatory Coverage

Primary evidence today:

1. replay manifest summaries
2. suite behavior metrics

Runtime fields that support measurement:

not a live runtime field; this is a control-plane metric derived from manifest and replay outputs

Availability status:

`Available`

## KPI-15 Behavior-Class First-Run Pass Rate

Primary evidence today:

1. replay class-level first-run summaries
2. release-gate reports

Runtime fields that support measurement:

not a live runtime field; this is a replay/control-plane metric

Availability status:

`Available`

## 5. Source-of-Truth Status Matrix

| KPI | Runtime Field Coverage | Replay Coverage | Manual Coverage | Current Operational Readiness |
|---|---|---|---|---|
| Wrong-report rate | Partial | Strong | Strong | Medium |
| First-turn success | Partial | Strong | Strong | Medium |
| Follow-up accuracy | Partial | Strong | Strong | Medium |
| Unnecessary clarification | Moderate | Strong | Strong | Medium |
| Clarification loop | Partial | Strong | Moderate | Medium |
| Output-shape correctness | Partial | Strong | Strong | High |
| Envelope correctness | Partial | Strong | Strong | Medium |
| Write safety | Partial | Strong | Strong | Medium |
| P95 latency | Moderate | Strong | Not needed | Medium |
| Fallback rate | Moderate | Moderate | Low | Medium |
| Incident reopen rate | Process-based | Not needed | Not needed | Low until ops starts |
| Incident closure discipline | Process-based | Not needed | Not needed | Low until ops starts |
| Audit envelope completeness | Partial | Moderate | Not needed | Medium |
| Mandatory class coverage | Not needed | Strong | Not needed | High |
| Mandatory class first-run pass rate | Not needed | Strong | Not needed | High |

## 6. Contract Gaps and Instrumentation Gaps

The following gaps are visible now and should be treated explicitly.

### Gap 1. Canonical Turn Audit Envelope

The enterprise contract expects a canonical audit envelope with:

1. `trace_id`
2. `engine_version`
3. `model_version`
4. `prompt_version`
5. `capability_version`
6. `selected_candidate`
7. `execution_plan`
8. `validation_result`
9. `latency_ms`
10. `final_response_hash`

Current status:

this gap is now materially reduced.

The runtime now emits `audit_turn.turn_audit_envelope` with the expected canonical fields:

1. `trace_id`
2. `engine_version`
3. `model_version`
4. `prompt_version`
5. `capability_version`
6. `selected_candidate`
7. `execution_plan`
8. `validation_result`
9. `latency_ms`
10. `final_response_hash`

Implementation note:

the envelope is assembled in the chat/service layer from existing governed v7 tool surfaces rather than from prompt-specific logic.

Action needed:

use this canonical emitted structure as the primary operational source for audit-envelope completeness, then extend downstream consumers and reporting to read it consistently.

### Gap 2. Security Policy Outcome Field

The contract requires security policy outcomes.

Current status:

no dedicated operational runtime field has been confirmed in the traced v7 surfaces.

Action needed:

define and emit a canonical security outcome field for operational reporting.

### Gap 3. Canonical Fallback Flag

Current status:

fallback must be inferred from `repair_attempts`, `planner_clarify`, and repairable failure classes.

Action needed:

consider a first-class `fallback_used` or equivalent operational signal.

### Gap 4. Live Wrong-Report Automation

Current status:

wrong-report is still measured most reliably through replay, browser, and incident review rather than fully automated live labels.

Action needed:

Phase 4 should define how live incidents and manual review feed the weekly wrong-report metric.

### Gap 5. Canonical Audit Completeness Rule

Current status:

we can tell that audit evidence exists, but the rule for when an actionable turn is considered contract-complete is not yet formalized in one weekly-review-ready check.

Action needed:

define a governed completeness checklist for actionable turns and apply it consistently in operational review.

## 7. Practical Recommendation

Use this signal map in the following way:

1. treat replay plus manual evidence as the current authoritative quality source
2. use runtime fields mainly for trend monitoring and diagnosis in the first Phase 4 version
3. do not pretend live production metrics are fully automated until the canonical audit and security gaps are resolved

## 8. Immediate Next Step

After approving this document, the next Phase 4 step should be:

create the incident operations contract so every alert, breach, or live defect has a defined owner, SLA, and closure path.
