# Qwen ERP Phase 3.5D Recommendation Policy Activation Gate

Status: implemented as readiness gate
Date: 2026-04-28
Scope: metadata-driven activation gate for governed business recommendations.

## Purpose

Phase 3.5C introduced the recommendation policy artifact scaffold. Phase 3.5D adds the activation gate that decides whether a recommendation request is ready for a future recommendation execution lane.

This slice does not enable recommendations by itself.

It answers a safer internal question:

`Is this recommendation request backed by an approved policy and complete governed evidence?`

## Implemented Slice

The shared `business_reasoning_policy.py` helper now emits an `authority_policy_gate` payload for blocked authority variations with policy metadata.

The gate evaluates:

1. policy artifact id and label
2. current approval state
3. required approval state
4. required evidence metrics
5. available evidence metrics in the selected row
6. missing evidence metrics
7. required governed artifacts
8. available governed artifacts
9. missing governed artifacts
10. whether the request is ready for a future recommendation lane

## Gate States

`not_configured`

No policy artifact is configured for this authority variation.

`blocked_missing_policy`

The required policy artifact exists in metadata but is not approved or active.

`blocked_missing_evidence`

The policy is approved, but the current artifact package does not carry all required metrics or governed supporting artifacts.

`ready`

The policy is approved and all required governed evidence is present.

Important: `ready` means recommendation execution may be considered by a future lane. It does not mean the current boundary helper should produce the recommendation.

## Current Customer Risk Behavior

`who should we collect from first?` remains blocked as a collection recommendation because `customer_collection_priority_policy` is currently `blocked_missing_policy`.

The response can still show ranked evidence, but it must not convert that evidence into a collection recommendation.

## Enterprise Grade Notes

This is a reusable control, not a phrase fix.

The gate is driven by metadata and selected-row evidence. Future recommendation families should add policy metadata instead of adding service-level keyword branches.

## Verification

Focused tests cover:

1. current production metadata: blocked because policy is missing
2. synthetic approved policy with missing evidence: blocked because evidence is incomplete
3. synthetic approved policy with complete evidence: gate state becomes ready while runtime recommendation remains blocked
4. existing driver and causal-boundary behavior remains stable

## Next Step

Phase 3.5E should define the future recommendation execution contract:

1. consume only `authority_policy_gate.ready_to_recommend == true`
2. emit a constrained recommendation result type
3. cite the approved policy artifac
4. cite every governed evidence input used
5. fail closed if runtime tries to produce unsupported recommendation tex
