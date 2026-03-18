# First Approved Expansion Candidate

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: next approved behavioral-class expansion candidate after contribution-share stabilization  
Status: approved for design and controlled implementation review

## Candidate Name
`comparison`

## Simple Description
This class answers business questions of the form:

1. compare one entity against another entity in the same period
2. compare one monthly period against another monthly period for the same approved grain
3. support bounded MoM read-only comparison without advisory interpretation

In business language, this is the class for:

- `A vs B in last month`
- `which one is higher in the same period`
- `March 2026 vs February 2026`
- `month over month for Yangon revenue`

## Why This Is The Right Next Candidate
This candidate is the safest next step because:

1. comparison semantics already exist in ontology and replay assets (`CMP-*`)
2. it is a Tier-2 analytical class with high business usefulness
3. the ERP now contains approximately 15 months of data, which enables bounded monthly comparison and MoM without inventing synthetic periods

## Business Value
This class supports frequent operational asks such as:

1. `Compare Yangon and Mandalay sales last month by territory`
2. `Compare Customer A and Customer B revenue last month`
3. `Compare Supplier X and Supplier Y purchase amount last month`
4. `Compare Yangon revenue in March 2026 vs February 2026`
5. `Show Yangon revenue month over month for March 2026`

## First-Slice Scope

### In Scope

1. same-period entity-vs-entity comparison
2. monthly period-vs-period comparison for one approved metric/grain
3. bounded MoM comparison for approved metric/grain with explicit or unambiguous month anchor
4. deterministic read table output

### Out Of Scope

1. weekly comparison
2. quarterly comparison
3. year-over-year and non-month period-over-period analytics
4. multi-point time-series output, which remains owned by the existing `trend_time_series` class
5. causal or recommendation narratives
6. advisory risk statements

## Initial Domain/Metric Scope

1. sales revenue comparisons
2. purchasing amount comparisons
3. approved monthly period comparisons for governed metadata grains
4. approved comparison grains from governed metadata (for example territory, customer, supplier, item)

## Example User Questions

1. `Compare Yangon and Mandalay sales last month by territory`
2. `Yangon vs Mandalay revenue last month`
3. `Compare Sunflower Accessories Co. and Golden Dragon purchase amount last month`
4. `Compare Yangon revenue in March 2026 vs February 2026`
5. `Show customer revenue month over month for March 2026`

These are examples only. Implementation must generalize by class contract, not by prompt memorization.

## Proposed Class Contract

### Input Shape

1. metric (for example revenue, purchase amount)
2. comparison axis/grain (for example territory, customer, supplier, item)
3. either:
   - at least two entities to compare inside one period
   - or one approved entity/grain with two monthly periods to compare
4. one explicit time scope or explicit monthly period pair

### Output Mode

1. deterministic tabular comparison result
2. bounded MoM comparison table when MoM is explicitly requested
3. follow-up projection and top-n compatible with active-result rules

### Clarification Rules

Clarify when:

1. entities to compare are missing
2. metric is missing
3. comparison grain is missing
4. monthly comparison anchor is missing for a period-vs-period or MoM ask

### Unsupported Rules

Return safe unsupported for:

1. weekly, quarterly, or YoY comparison asks
2. multi-point time-series asks that belong to `trend_time_series`
3. unsupported grains not approved in first slice

## Risk Tier
Baseline: `Tier 2`  
Tier 1 rigor required for finance-adjacent customer/supplier comparisons.

## Required Validation Before Runtime Implementation

1. class definition complete
2. ontology plan complete
3. capability metadata plan complete
4. variation matrix complete
5. replay design complete
6. manual golden pack complete
7. approval review complete

## Required Existing-Suite Reruns Once Runtime Work Starts

1. new comparison suite in full
2. `core_read`
3. selected time-boundary probes from existing `trend_time_series` coverage
4. `multiturn_context` if follow-up/state surfaces are touched
5. `transform_followup` if active-result transform surfaces are touched
6. standing browser smoke pack

## Approval Decision
Approved for:

1. design-preparation completion
2. controlled implementation-readiness review
3. bounded first-slice runtime implementation after explicit checkpoint approval
