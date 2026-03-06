# Phase 3 Rerun Decision Checklist

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: operational checklist for deciding what must be rerun after a change  
Status: active Phase 3 operational checklist

## Purpose
This checklist turns the rerun policy into a practical workflow.

Use it before calling a change complete.

## Step 1: Identify The Impact Surface
Mark every surface touched by the change:

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

## Step 2: Apply The Required Reruns

### If ontology changed
Rerun:

1. affected class suite in full
2. impacted read suites
3. standing browser smoke pack if the change affects user language interpretation materially

### If capability metadata changed
Rerun:

1. affected class suite in full
2. `core_read` if resolver-visible semantics changed
3. targeted browser pack for the affected behavior

### If semantic resolver changed
Rerun:

1. `core_read`
2. affected class suite
3. standing browser smoke pack if core read behavior may shift

### If spec pipeline changed
Rerun:

1. affected class suite
2. `core_read` if read intent/class generation can change
3. `multiturn_context` if follow-up/latest-record planning can change

### If memory/state changed
Rerun:

1. `multiturn_context`
2. `transform_followup`
3. affected class suite
4. standing browser smoke pack

### If resume/latest-record logic changed
Rerun:

1. `multiturn_context`
2. targeted latest-record cases if available
3. standing browser smoke pack sections:
   - latest-record clarification
   - any affected finance parity flow

### If transform_last changed
Rerun:

1. `transform_followup`
2. affected class suite
3. browser smoke sections touching scale/projection follow-up

### If response_shaper changed
Rerun:

1. affected class suite
2. `core_read` if shared shaping semantics are affected
3. browser smoke sections touching projection or display shape

### If quality_gate changed
Rerun:

1. affected class suite
2. `core_read`
3. `no_data_unsupported` if no-data or unsupported behavior changed

### If write path changed
Rerun:

1. `write_safety`
2. targeted browser/manual write safety pack

### If read_engine orchestration or execution runner changed
Rerun:

1. `core_read`
2. `multiturn_context`
3. `transform_followup`
4. standing browser smoke pack
5. release gate if preparing closure/release evidence

## Step 3: Decide Whether Release Gate Must Be Rerun
Rerun the release gate when:

1. phase-close evidence is being prepared
2. release-candidate evidence is being prepared
3. a structural refactor touched shared-runtime behavior
4. a Tier 1 incident was fixed and the affected replay assets changed

## Step 4: Attach Evidence
Before closing the change, attach:

1. rerun command(s)
2. raw log paths
3. browser/manual notes if applicable
4. incident link if this change closes an incident

## Minimum Rule
Do not mark a shared-runtime change complete if:

1. impacted reruns were skipped
2. browser parity was required but not checked
3. evidence paths are missing

## Notes
This checklist is intentionally conservative.

If impact is unclear:

1. choose the broader rerun set
2. document the assumption
