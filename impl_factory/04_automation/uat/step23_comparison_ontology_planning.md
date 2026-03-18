# Comparison Ontology Planning

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: ontology design planning for `comparison`  
Status: design-preparation asset

## Purpose
Define ontology-side planning for comparison semantics before runtime changes begin.

This document ensures comparison language normalization is governed by ontology, not runtime prompt hacks.

## Class Objective
Interpret comparison asks such as:

1. `Compare Yangon and Mandalay sales last month`
2. `A vs B revenue last month`
3. `Which is higher between X and Y last month`
4. `Compare Yangon revenue in March 2026 vs February 2026`
5. `Show Yangon revenue month over month for March 2026`

## Canonical Intent Set

1. `comparison_request`
2. `entity_vs_entity`
3. `period_vs_period_monthly`
4. `month_over_month_request`

## Comparison Language Coverage

### Canonical `comparison_request`

1. compare
2. comparison
3. versus
4. vs

### Canonical `entity_vs_entity`

1. A vs B
2. X versus Y
3. between X and Y

### Canonical `period_vs_period_monthly`

1. March 2026 vs February 2026
2. compare this month to last month
3. compare current month with previous month

### Canonical `month_over_month_request`

1. month over month
2. MoM
3. compared to previous month

## Time Semantics For First Slice

### In Scope

1. single explicit period (for example `last month`)
2. two explicit monthly periods for period-vs-period comparison
3. MoM semantics anchored to an explicit or unambiguous monthly reference

### Out Of Scope

1. weekly compare / week-over-week
2. quarterly compare / quarter-over-quarter
3. year-over-year and non-month period comparisons
4. multi-point time-series semantics

## Metric Families In Scope

1. revenue
2. purchase amount

## Grain Semantics In Scope
Allowed by metadata and first-slice report support:

1. territory
2. customer
3. supplier
4. item

## Clarification Ambiguities
Clarify when:

1. metric is missing
2. compared entities are missing
3. comparison grain is missing

## Explicit Out-Of-Scope Language (First Slice)

1. growth rate
2. week over week
3. quarter over quarter
4. year over year
5. 12-month time series
6. forecast
7. recommendation/advisory interpretation

## Required Output Of This Planning Step

1. approved canonical comparison alias inventory
2. approved first-slice scope boundary
3. approved clarification/unsupported triggers
