# Comparison Capability Metadata Planning

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: capability/report metadata planning for `comparison`  
Status: design-preparation asset

## Purpose
Identify metadata declarations required before runtime implementation of `comparison`.

Rule: runtime must not guess comparison behavior if metadata can declare it.

## Class Objective
Support deterministic comparisons for:

1. sales revenue
2. purchase amount
3. monthly period-vs-period comparisons
4. bounded MoM comparisons

## Required Metadata Questions Per Report

1. what is the primary comparison grain
2. which metrics are valid for comparison
3. which filters map to compared entities
4. which time-comparison grain is supported (`month` only in first slice)
5. whether aggregate rows exist and must be excluded
6. which columns are safe for default comparison output
7. which delta columns are safe for bounded MoM output

## First-Slice Report Families (Planned)

1. territory-capable sales comparison report family
2. customer revenue comparison-capable summary report family
3. supplier purchase comparison-capable summary report family
4. item sales comparison-capable report family
5. report families that can safely support monthly period-vs-period comparisons

## Proposed Metadata Declarations

1. `result_grain`
2. `supported_metrics`
3. `comparison_capable` flag
4. `comparison_entity_fields`
5. `aggregate_row_policy`
6. `safe_default_columns`
7. `transform_safe_columns`
8. `supported_period_comparison_grains`
9. `mom_capable`
10. `safe_delta_columns`

## Known Gaps To Prevent Runtime Guessing

1. missing explicit comparison-capable metric declarations
2. inconsistent aggregate-row handling across summaries
3. incomplete entity-field mapping for `A vs B` comparisons
4. missing monthly period-comparison declarations
5. missing safe delta-column declarations for MoM output

## Deferred Metadata Scope

1. weekly comparison declarations
2. quarterly comparison declarations
3. YoY semantics
4. multi-point trend-delta metadata

## Required Output Of This Planning Step

1. approved first-slice report family list
2. missing metadata fields to add before runtime implementation
3. explicit deferred metadata list
