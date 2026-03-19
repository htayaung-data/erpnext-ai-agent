# Phase 4 Security and Fallback Telemetry Status

Date: 2026-03-19  
Owner: AI Runtime Engineering  
Scope: second canonical telemetry slice after the turn-audit envelope  
Status: implemented and validated with focused unit coverage

## 1. Purpose

This note records the second Phase 4 telemetry improvement.

The goal of this slice was narrow:

1. emit a first-class `security_outcome` field in the canonical turn audit envelope
2. surface the already-governed planner/spec `fallback_used` signal in the same envelope
3. keep runtime business behavior unchanged

## 2. What Was Implemented

The runtime canonical envelope at `audit_turn.turn_audit_envelope` now includes:

1. `security_outcome`
2. `fallback_used`

These are emitted from governed runtime evidence that already exists in:

1. planner/spec intent metadata
2. write-confirmation pending state
3. write result payloads
4. hidden write-engine tool messages
5. user-visible safe-block / confirmation payloads

## 3. Security Outcome Shape

Current emitted shape:

1. `status`
2. `category`
3. `requires_confirmation`
4. `doctype`
5. `operation`

Current statuses covered:

1. `not_applicable`
2. `confirmation_required`
3. `blocked_disabled`
4. `blocked_idempotency`
5. `execution_error`
6. `executed`
7. `canceled`
8. `observed_unclassified`

## 4. Fallback Signal Shape

Current emitted shape:

1. `plan`
2. `spec`
3. `any`

This is sourced from the existing `llm_meta.fallback_used` fields, so the telemetry slice did not invent a new planner rule.

## 5. Implementation Surfaces

Changed files:

1. [turn_audit.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/turn_audit.py)
2. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/service.py)
3. [test_chat_turn_audit.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_chat_turn_audit.py)

Updated Phase 4 control docs:

1. [step35_phase4_runtime_signal_map_2026-03-18.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step35_phase4_runtime_signal_map_2026-03-18.md)
2. [step37_phase4_weekly_operations_review_baseline_2026-03-18.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step37_phase4_weekly_operations_review_baseline_2026-03-18.md)

## 6. Validation Performed

Focused validations completed:

1. `python3 -m unittest impl_factory.04_automation.bench_scripts.test_chat_turn_audit`
2. `python3 -m py_compile` on changed runtime files

Result:

targeted tests passed.

## 7. Contract Alignment

This slice stays inside the contract boundary because:

1. it does not change routing or business behavior
2. it does not introduce keyword-based parser behavior
3. it derives telemetry from already-governed write and planner/spec surfaces
4. it improves operational observability without widening user-facing capability

## 8. Remaining Phase 4 Gaps

This still does not complete all telemetry work.

Remaining gaps now are:

1. downstream operational reporting does not yet score envelope completeness directly from the canonical block
2. live wrong-report automation still depends on replay/manual/incident review
3. security outcome is available, but weekly reporting consumers still need to adopt it
