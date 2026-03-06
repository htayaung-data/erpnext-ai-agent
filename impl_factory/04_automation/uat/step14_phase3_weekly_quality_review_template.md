# Phase 3 Weekly Quality Review Template

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: weekly review template for runtime quality, incidents, and regression discipline  
Status: active Phase 3 operational template

## Purpose
Use this template once per week to review current quality health.

The goal is simple:

1. check whether quality is stable
2. check whether important failures reopened
3. check whether evidence is current
4. decide what must be fixed, rerun, or deferred next

This is not a runtime artifact. It is an operating review document.

## Review Header

- Review Date:
- Review Owner:
- Participants:
- Review Window Covered:
- Current Phase: `Phase 3`

## 1. Current Baseline Status

- Phase 2 baseline still valid: `Yes / No`
- Latest release gate green: `Yes / No`
- Latest targeted replay confidence green: `Yes / No`
- Standing browser smoke pack green: `Yes / No`

Notes:

- 

## 2. Incident Summary

- New Tier 1 incidents this week:
- New Tier 2 incidents this week:
- Reopened incidents:
- Closed incidents:

Links:

- incident register entries:

## 3. Replay Health

Record the latest status of the important replay assets:

| Asset | Tier | Latest Status | Latest Evidence Path | Notes |
|---|---|---|---|---|
| `core_read` | Tier 1 |  |  |  |
| `multiturn_context` | Tier 1 |  |  |  |
| `write_safety` | Tier 1 |  |  |  |
| `no_data_unsupported` | Tier 1 |  |  |  |
| `transform_followup` | Tier 2 |  |  |  |

## 4. Browser / Manual Health

Record the latest status of the standing browser smoke pack:

| Browser Pack | Tier | Latest Status | Evidence Path / Notes |
|---|---|---|---|
| Customer ranking + scale | Tier 1 |  |  |
| Supplier ranking + scale | Tier 1 |  |  |
| Product ranking + projection | Tier 2 |  |  |
| Warehouse correction + scale | Tier 1 |  |  |
| Latest-record clarification | Tier 1 |  |  |
| Finance parity | Tier 1 |  |  |
| Write confirm/cancel smoke | Tier 1 |  |  |

## 5. Shared-Surface Risk Review

List the risky shared surfaces touched this week:

- `ontology`
- `capability metadata`
- `semantic resolver`
- `spec pipeline`
- `memory/state`
- `resume/latest-record`
- `transform_last`
- `response_shaper`
- `quality_gate`
- `write path`
- `read_engine orchestration`
- `execution runner / loop`

Notes:

- 

## 6. Rerun Discipline Review

Questions:

1. Were all required reruns performed for shared-runtime changes?
2. Was the rerun decision checklist followed?
3. Were any reruns skipped? If yes, why?
4. Did browser smoke run where required?

Findings:

- 

## 7. Deferred Risks

List known deferred risks:

1. 
2. 
3. 

For each deferred risk, record:

- why it is deferred
- current mitigation
- when it must be revisited

## 8. Expansion Readiness Check

Questions:

1. Are Phase 3 controls being followed consistently?
2. Is any new behavioral-class expansion currently approved?
3. If yes, does it have the required contract, risk tier, replay assets, and browser assets?

Decision:

- `No new expansion`
- `Expansion allowed for approved class only`

## 9. Actions For Next Week

List only the most important actions:

1. 
2. 
3. 

## 10. Review Outcome

- Quality status this week: `Stable / Watch / At Risk`
- Main reason:
- Approved by:

