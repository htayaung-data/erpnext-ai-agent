# Comparison Manual Golden Pack

Date: 2026-03-07  
Updated: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: curated browser/manual golden pack design for `comparison`  
Status: design-preparation asset

## Purpose
Define the manual/browser pack that must pass before comparison class closure.

## Execution Rules

1. Use fresh chat unless case requires follow-up context.
2. Record prompt, visible report, visible columns, pass/fail, screenshot.
3. Fail if wrong report, wrong grain, wrong metric, stale carryover, or unsupported policy violation.

## Pack A: Territory Comparison

### MG-CMP-01
Prompt:

- `Compare Yangon and Mandalay sales last month by territory`

Expected:

1. deterministic territory comparison table
2. same-period revenue metric
3. side-by-side comparison presentation with compared entities as columns
4. filtered-summary presentation is not accepted

### MG-CMP-02
Prompt:

- `Yangon vs Mandalay revenue last month`

Expected:

1. equivalent output semantics to MG-CMP-01
2. side-by-side comparison presentation with compared entities as columns

### MG-CMP-03
Same session as MG-CMP-01:

- `Show only territory and revenue`

Expected:

1. same active result, restrictive projection only

### MG-CMP-04
Same session as MG-CMP-01:

- `Show in Million`

Expected:

1. same compared entities
2. revenue scaled

## Pack B: Customer/Supplier/Item Comparison

### MG-CMP-05
Prompt:

- `Compare Shwe Li Road Mobile Wholesale and Latha Mobile Wholesale revenue last month`

Expected:

1. same-period customer revenue comparison
2. side-by-side comparison presentation with compared entities as columns

### MG-CMP-06
Prompt:

- `Compare Sunflower Accessories Co. and Golden Dragon Trading Co. Ltd. purchase amount last month`

Expected:

1. same-period supplier purchase comparison
2. side-by-side comparison presentation with compared entities as columns

### MG-CMP-07
Prompt:

- `Compare SPH-SAM-A15-6/128 and SPH-XMI-RN13-8/256 sales last month`

Expected:

1. same-period item sales comparison
2. side-by-side comparison presentation with compared entities as columns

## Pack C: Monthly / MoM

### MG-CMP-08
Prompt:

- `Compare Yangon revenue in March 2026 vs February 2026`

Expected:

1. deterministic monthly period-vs-period comparison
2. correct month anchoring

### MG-CMP-09
Prompt:

- `Show Yangon revenue month over month for March 2026`

Expected:

1. bounded MoM output
2. current month, previous month, and deterministic delta semantics

## Pack D: Correction / Clarification / Unsupported

### MG-CMP-10
Same session as MG-CMP-01:

- `Actually compare Yangon and Bago instead`

Expected:

1. correction rebind updates compared entities only
2. resulting table remains side-by-side comparison-grade

### MG-CMP-11
Prompt:

- `Compare Yangon and Mandalay`

Expected:

1. bounded clarification (metric and/or grain missing)

### MG-CMP-12
Prompt:

- `Compare Yangon revenue week over week`

Expected:

1. safe unsupported for weekly comparison

### MG-CMP-13
Prompt:

- `Compare Yangon revenue quarter over quarter`

Expected:

1. safe unsupported for quarterly comparison

## Initial Manual Golden Size

- `13` curated browser cases

## Acceptance Rule
Class is not considered ready until:

1. replay coverage is green
2. this manual pack is green
3. unsupported weekly/quarterly behavior is confirmed
