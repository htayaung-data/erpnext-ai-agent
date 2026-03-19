# Phase 4 Operational Audit Report Plan

Date: 2026-03-19  
Owner: AI Runtime Engineering  
Scope: first operational consumer of the canonical turn audit envelope  
Status: implemented for controlled review use

## 1. Purpose

This note records the first Phase 4 operational reporting consumer.

The purpose is practical:

1. read the canonical `audit_turn.turn_audit_envelope` from real chat-session data
2. score actionable-turn audit completeness with one governed rule
3. summarize security outcome and fallback usage for a review window

## 2. Implemented Consumer

Script:

1. [phase4_audit_ops_report.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/phase4_audit_ops_report.py)

Regression coverage:

1. [test_phase4_audit_ops_report.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_phase4_audit_ops_report.py)

## 3. What The Script Produces

The report summarizes:

1. sessions scanned
2. audit turns in window
3. actionable turns in window
4. actionable turns complete / incomplete
5. audit completeness rate
6. security outcome counts
7. fallback summary
8. missing required field counts
9. recent incomplete actionable-turn examples

## 4. Governed Audit Completeness Rule

For actionable turns, the first governed completeness rule checks:

1. `schema_version`
2. `trace_id`
3. `engine_version`
4. `engine_mode`
5. `capability_version`
6. `latency_ms`
7. `final_response_hash`
8. `security_outcome.status`
9. `fallback_used.plan`
10. `fallback_used.spec`
11. `fallback_used.any`
12. `validation_result.quality_verdict_or_error_code`

Additional requirements:

1. planner-backed turns must include model/prompt versions for `spec`
2. table payloads must include `selected_candidate.report_name`

Note:

plan-level model/prompt provenance is currently treated as best-effort rather than closure-blocking in this first operational rule, because the current v7 runtime does not yet persist planner-plan LLM metadata into the final `audit_turn` path consistently.

Spec-level model provenance is expected to be present through the effective deployed model, including fallback to the default configured `openai_model` when slot-specific model keys are unset.

## 5. Operational Meaning

This is the first real Phase 4 operational consumer.

That means:

1. Phase 4 is no longer only emitting telemetry
2. Phase 4 can now score audit completeness from real runtime data
3. weekly review can move from qualitative statements toward measured audit evidence

## 6. Remaining Work Before Phase 4 Closure

This consumer is a strong step, but not the end of Phase 4.

Still needed:

1. run the script on a real review window and record the first live output
2. decide whether the current completeness rule needs one refinement pass after the first live run
3. attach that first live report to the weekly operational baseline
