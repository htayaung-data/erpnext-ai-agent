# Qwen ERP Phase 3.5E Recommendation Execution Contrac

Status: implemented as contract layer
Date: 2026-04-28
Scope: constrained execution contract for future governed business recommendations.

## Purpose

Phase 3.5D added the recommendation policy activation gate. Phase 3.5E adds the execution contract that a future recommendation lane must consume before it is allowed to produce a recommendation.

This slice still does not enable collection recommendations in production.

## Implemented Slice

The shared `business_reasoning_policy.py` helper now emits `qwen_business_recommendation_execution_contract` for recommendation-authority requests.

The contract carries:

1. execution state
2. execution allowed flag
3. source composite family
4. recommendation variation
5. policy artifact id and label
6. approval state and required approval state
7. constrained recommendation result type
8. selected row evidence
9. policy gate payload
10. output constraints
11. safe response mode

## Output Constraints

Future recommendation execution must:

1. require a ready policy gate
2. emit only the approved recommendation result type
3. cite the policy artifac
4. cite governed evidence
5. avoid prediction probabilities
6. avoid hidden weighted risk scores
7. avoid credit approval decisions
8. avoid unsupported causal or trend claims
9. fall back to a grounded evidence boundary when constraints are not satisfied

## Current Runtime Behavior

For current production metadata:

`who should we collect from first?`

still returns a governed boundary because `customer_collection_priority_policy` is `blocked_missing_policy`.

The new execution contract is attached behind that boundary for audit and future routing, but no recommendation text is generated.

## Enterprise Grade Notes

This prevents the next implementation phase from accidentally creating a prompt-only recommendation lane.

Any future recommendation execution must prove:

1. policy approval
2. evidence completeness
3. allowed output type
4. explicit constraints

before producing action advice.

## Verification

Focused tests cover:

1. missing policy blocks execution
2. approved policy with missing evidence blocks execution
3. synthetic ready gate produces an execution-ready contrac
4. ready contract still does not change the current boundary helper into runtime recommendation outpu
5. non-recommendation driver questions do not produce a recommendation execution contrac

## Next Step

Phase 3.5F should decide whether to:

1. keep recommendations disabled until a real approved policy document exists, or
2. implement a dry-run recommendation renderer that shows what would be recommended only in explicit admin/test mode.

Production recommendation execution should not be enabled until the business approves the policy artifact.
