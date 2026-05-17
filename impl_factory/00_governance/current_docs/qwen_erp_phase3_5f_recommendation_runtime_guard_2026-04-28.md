# Qwen ERP Phase 3.5F Recommendation Runtime Guard

Status: implemented as production safety guard
Date: 2026-04-28
Scope: explicit runtime enablement control for governed recommendation execution.

## Purpose

Phase 3.5E introduced the recommendation execution contract. Phase 3.5F tightens that contract by separating:

1. policy/evidence gate readiness
2. dry-run availability
3. production recommendation execution permission

This prevents a future implementation from treating `ready_to_recommend` as automatic permission to advise.

## Implemented Slice

Recommendation policy metadata now supports:

1. `runtime_execution_state`
2. `allowed_execution_modes`

The execution contract now emits:

1. `policy_gate_ready`
2. `runtime_execution_state`
3. `runtime_execution_enabled`
4. `dry_run_allowed`
5. `allowed_execution_modes`
6. `execution_allowed`

## Runtime States

`disabled_pending_policy_approval`

Default production-safe state. Recommendation execution is blocked even if a synthetic gate is ready.

`dry_run_only`

Allows future admin/test dry-run rendering, but still blocks production recommendation execution.

`enabled_active`

Allows production recommendation execution only when the policy/evidence gate is also ready.

## Current Customer Risk Behavior

`customer_collection_priority_policy` remains:

1. approval state: `blocked_missing_policy`
2. runtime execution state: `disabled_pending_policy_approval`
3. allowed execution modes: none

Therefore `who should we collect from first?` continues to return a governed evidence boundary, not a collection recommendation.

## Enterprise Grade Notes

This is a guardrail slice, not a feature expansion.

The assistant now requires both:

1. approved policy and complete evidence
2. explicit runtime enablemen

before any future recommendation lane can produce action advice.

## Verification

Focused tests cover:

1. missing policy blocks execution
2. approved policy with missing evidence blocks execution
3. ready policy/evidence gate still blocks production execution when runtime is disabled
4. dry-run mode can be identified without enabling production execution
5. production execution is allowed only when runtime state is `enabled_active`

## Next Step

Phase 3.5G should add an observability/audit surface for recommendation boundary and execution-contract payloads so UAT can confirm why each recommendation request was blocked, dry-run eligible, or execution eligible.
