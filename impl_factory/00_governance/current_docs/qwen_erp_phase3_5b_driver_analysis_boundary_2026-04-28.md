# Qwen ERP Phase 3.5B Driver Analysis Boundary

Status: implemented, live verification in progress
Date: 2026-04-28
Scope: governed distinction between current-artifact metric-driver explanation and unsupported causal/trend/payment-behavior driver analysis.

## Purpose

Phase 3.5B extends the Phase 3.5A reasoning authority boundary.

The assistant should not treat all "why", "driver", or "factor" questions the same way:

1. evidence explanation is allowed when the current artifact has direct evidence
2. current-artifact metric-driver analysis is allowed when family metadata exposes driver metrics
3. causal, trend/change, and payment-behavior driver analysis must be blocked unless a governed artifact supports those claims

## Implemented Slice

Added driver-analysis policy support to the shared `business_reasoning_policy.py` helper.

For governed composite families, metadata can now define:

1. supported driver modes
2. supported driver aliases
3. driver metrics available in the current artifac
4. blocked driver modes
5. blocked driver aliases
6. business-natural labels for each mode

Customer Risk As-Of now supports:

1. `current_artifact_metric_driver`

Customer Risk As-Of blocks:

1. `causal_root_cause_driver`
2. `trend_change_driver`
3. `payment_behavior_driver`

## Runtime Behavior

Allowed example:

`what drives the first customer risk?`

The assistant may answer from current-artifact metrics only:

1. rank
2. overdue amoun
3. outstanding amoun
4. overdue ratio when presen
5. credit utilization when presen

Blocked examples:

1. `what caused the first customer's risk to increase?`
2. `what changed compared to last month?`
3. `is this payment behavior getting worse?`

The assistant should explain that the current artifact does not authorize causal, trend, or payment-behavior driver analysis and should ask for a governed trend, payment-behavior, or transaction-history analysis artifact.

## Precedence Refinemen

Manual browser UAT exposed one important routing bug: the deterministic driver helper could answer `what drives the first customer risk?`, but the generic front-door KPI-definition lane could still preempt it and return a broad explanation.

The fix is shared, not phrase-specific:

1. detect whether the current artifact already contains direct governed evidence before front-door handling
2. make front-door yield to the current-artifact evidence lane when that evidence exists
3. preserve entity drilldown precedence, because explicit entity drilldowns are a separate governed route
4. keep recommendation, prediction, causal, trend, and payment-behavior requests behind the Phase 3.5A/3.5B authority boundary

This closes the observed gap without adding a customer-name, rank, or single-question rescue.

## Enterprise Grade Notes

This slice is metadata-driven:

1. no customer-name-specific branching
2. no rank-specific branching
3. no service-level hardcoding
4. no one-off prompt rescue
5. no new reasoning lane

The same policy helper can be reused by future composite families by adding metadata, not by adding route-specific code.

## Verification Targe

Focused tests should prove:

1. current-artifact metric-driver questions receive deterministic evidence
2. unsupported causal driver questions receive a governed boundary
3. prediction and recommendation boundaries from Phase 3.5A remain intac
4. evidence explanations such as `why is the first customer risky?` still work
5. front-door handling yields when current-artifact direct evidence is available

## Next Step

After live UAT, Phase 3.5C should define recommendation policy artifacts:

1. what evidence is required before recommendations are allowed
2. how recommendations cite supported claims
3. how recommendations differ from evidence ranking
4. how unsupported recommendations fail closed with a useful business next step
