# Qwen ERP Phase 3.5C Recommendation Policy Artifact Scaffold

Status: implemented as conservative scaffold
Date: 2026-04-28
Scope: governed recommendation authority for business questions such as collection prioritization.

## Purpose

Phase 3.5A blocked unsupported recommendations and predictions. Phase 3.5B separated allowed current-artifact metric-driver analysis from blocked causal, trend, and payment-behavior claims.

Phase 3.5C adds the next enterprise control: a recommendation request should not be blocked only by generic wording. It should point to the exact policy artifact and evidence package required before that recommendation can be allowed.

## Implemented Slice

Customer Risk As-Of now declares a `business_reasoning_authority_policies` entry for `collection_recommendation`.

The scaffold defines:

1. required policy artifact: `customer_collection_priority_policy`
2. policy label: `Customer Collection Priority Policy`
3. current approval state: `blocked_missing_policy`
4. required policy state: `approved_active`
5. recommendation result type: `ranked_collection_action`
6. required evidence metrics: overdue amount, outstanding amount, overdue ratio, credit utilization, and aging buckets
7. required governed artifacts: Customer Risk As-Of, Accounts Receivable Aging, and Customer Payment Behavior Analysis

## Runtime Behavior

Today, `who should we collect from first?` remains blocked as a recommendation.

The answer should now be more precise:

1. it may show ranked evidence from the current artifac
2. it must say this is not a recommendation
3. it must identify the missing policy artifac
4. it must identify the evidence requirements needed before recommendations can be enabled

## Enterprise Grade Notes

This is not a single-case answer fix.

The control lives in metadata and the shared `business_reasoning_policy.py` helper. Future recommendation families can add their own authority policy entries without adding phrase-specific service routing.

## Verification Targe

Focused tests should prove:

1. blocked collection recommendations still fail closed
2. the boundary payload carries the required policy artifac
3. rendered responses include a Required Policy block
4. driver analysis and prediction boundaries remain unchanged

## Next Step

Phase 3.5D should define the future activation gate for policy-approved recommendations:

1. verify policy approval state
2. verify required evidence artifacts are presen
3. verify recommendation output is constrained to the approved result type
4. prevent runtime generation from creating recommendations outside the policy contrac
