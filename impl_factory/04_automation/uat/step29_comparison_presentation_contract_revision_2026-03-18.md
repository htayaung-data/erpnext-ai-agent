# Comparison Presentation Contract Revision

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: approved presentation revision for `comparison` first-slice closure  
Status: planning only, no runtime edits in this step

## Purpose

This note records an approved correction to the `comparison` class closure contract:

1. same-period comparison output must be **comparison-grade**
2. a plain filtered summary table is **not** sufficient
3. replay and manual acceptance must be updated to enforce this

This revision is based on fresh browser evidence after container restart.

## Approved Presentation Rule

For same-period entity-vs-entity comparison, the expected presentation is:

1. compared entities appear as **side-by-side columns**
2. the business metric appears as the comparison row label
3. the output reads as a comparison table, not as a filtered report extract

Accepted example:

```text
Territory   Yangon        Mandalay
Revenue     6,306,500.00  8,680,000.00
```

Also acceptable if the top-left label is `Metric` instead of `Territory`, as long as:

1. the compared entities are side-by-side columns
2. the metric is explicit
3. the values are aligned in one comparison-grade matrix

## Explicitly Not Accepted

The following is **not** closure-grade for same-period comparison:

```text
Territory   Revenue
Yangon      6,306,500.00
Mandalay    8,680,000.00
```

Reason:

1. this is only a filtered summary table
2. it does not express direct side-by-side comparison
3. it is not the approved enterprise presentation for `comparison`

## Scope Of This Revision

### In Scope

1. same-period territory comparison
2. same-period customer comparison
3. same-period supplier comparison
4. same-period item comparison

### Not Changed In This Revision

1. monthly period-vs-period comparison stays period-column based
2. month-over-month comparison stays period-column based
3. clarification behavior
4. unsupported weekly/quarterly behavior

## Replay / Manual Consequences

Before `comparison` can be frozen:

1. same-period replay acceptance must require side-by-side comparison shape
2. manual golden expectations must require side-by-side comparison shape
3. same-period outputs that are only filtered-summary-grade must fail closure

## Next Implementation Boundary

The next runtime change is allowed only for:

1. same-period comparison presentation shaping
2. only after using current resolved comparison entities and metric
3. without adding prompt-to-report maps
4. without adding new keyword-routing logic
5. without widening comparison scope

## Current Status

As of this revision:

1. replay for `comparison_class` is green
2. browser evidence shows same-period comparison presentation is still partial
3. therefore `comparison` is **not ready to freeze yet**
4. Phase 3 is **not ready to close yet**
