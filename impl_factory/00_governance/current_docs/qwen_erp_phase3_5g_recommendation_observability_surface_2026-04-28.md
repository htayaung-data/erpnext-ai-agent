# Qwen ERP Phase 3.5G Recommendation Observability Surface

Status: implemented
Date: 2026-04-28
Scope: auditable rendering surface for recommendation boundary and execution-gate state.

## Purpose

Phase 3.5F added runtime recommendation guards. Phase 3.5G makes those guards visible in deterministic boundary responses and rendered payloads.

This matters because recommendation safety should not be hidden inside code. During UAT and review, the team should be able to see exactly why a recommendation request is blocked, dry-run eligible, or production eligible.

## Implemented Slice

The shared `business_reasoning_policy.py` helper now renders recommendation execution observability for recommendation-authority boundaries.

The answer text can show:

1. execution state
2. policy gate readiness
3. runtime execution state
4. runtime execution enabled flag
5. dry-run allowed flag
6. production execution allowed flag
7. safe response mode
8. boundary reason

The rendered payload now includes a deterministic table block:

`Recommendation Execution Gate`

## Current Customer Risk Behavior

For `who should we collect from first?`, the assistant still returns a governed boundary.

The boundary now makes clear:

1. policy gate is not ready
2. runtime execution is not enabled
3. dry-run is not allowed
4. production execution is not allowed
5. the safe response mode remains `grounded_evidence_boundary`

## Enterprise Grade Notes

This is an auditability improvement, not a recommendation feature.

It avoids hidden governance state and makes future review easier:

1. business users see why the answer is blocked
2. developers can inspect the rendered payload
3. future recommendation lanes can consume the same execution contrac
4. production advice remains impossible unless policy and runtime gates both pass

## Verification

Focused tests confirm:

1. blocked collection recommendation answers include execution-gate tex
2. rendered payloads include the `Recommendation Execution Gate` block
3. production execution is shown as disabled when runtime execution is not enabled
4. prior policy and driver-analysis boundaries remain intac

## Next Step

Phase 3.5H should be a closure/evaluation slice for Phase 3.5:

1. run a compact browser UAT matrix
2. verify all recommendation/prediction/driver boundaries
3. document remaining work before moving beyond Phase 3.5
