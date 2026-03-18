# Comparison Replay Asset Design

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: replay design for `comparison`  
Status: design-preparation asset

## Purpose
Define replay coverage requirements for comparison class implementation acceptance.

## Suite Strategy
Recommended dedicated suite label:

- `comparison_class`

Until stable, keep this suite separate from broad packs for clearer failure attribution.

## First-Run Rule

1. first-run-only scoring
2. no retry credit
3. clarification/unsupported only when contract requires it

## Required Coverage Groups

### Group A: Territory Revenue Comparison

1. base compare ask
2. phrasing variants (`compare`, `vs`, `versus`)
3. projection/top-n/scale follow-ups

### Group B: Customer Revenue Comparison

1. same-period customer vs customer comparison
2. follow-up projection and correction cases

### Group C: Supplier Purchase Comparison

1. same-period supplier vs supplier comparison
2. follow-up projection and correction cases

### Group D: Item Sales Comparison

1. same-period item vs item comparison
2. follow-up projection cases

### Group E: Clarification

1. monthly comparison anchor missing
2. missing metric
3. missing comparison grain
4. missing compared entities

### Group F: Monthly Period Comparison

1. explicit month-vs-month comparison ask
2. phrasing variants for explicit monthly periods
3. projection/top-n/scale follow-ups on monthly comparison result

### Group G: Bounded MoM

1. explicit MoM ask with month anchor
2. phrasing variants (`month over month`, `MoM`, `vs previous month`)
3. correction and projection follow-ups on MoM result

### Group H: Unsupported

1. weekly comparison ask
2. quarterly comparison ask
3. YoY ask
4. unsupported grain ask

## Suggested Minimum Case Counts

1. territory group: 8
2. customer group: 6
3. supplier group: 6
4. item group: 4
5. monthly period comparison group: 4
6. bounded MoM group: 4
7. clarification group: 4
8. unsupported group: 4

Initial target total: `40`

## Mandatory Cases For Approval

1. one passing territory same-period comparison
2. one passing customer same-period comparison
3. one passing supplier same-period comparison
4. one passing monthly period-vs-period comparison
5. one passing bounded MoM case
6. one correction follow-up pass
7. one projection follow-up pass
8. one unsupported weekly or quarterly case pass
9. one clarification case pass

## Expected Failure Modes To Detect

1. wrong report family selection
2. wrong grain preservation
3. wrong metric basis
4. stale topic carryover during follow-up
5. correction follow-up rebind failure
6. wrong monthly period anchoring
7. weekly/quarterly/YoY ask silently accepted instead of unsupported
8. `trend_time_series` asks being incorrectly hijacked into comparison

## Impacted Existing-Suite Reruns

1. `core_read` (resolver/spec selection shared surface)
2. selected `trend_time_series` boundary probes from existing coverage
3. `multiturn_context` (if follow-up/rebind touched)
4. `transform_followup` (if active-result transform touched)
5. standing browser smoke pack

## Approval Note
This is a planning asset. Runtime work must stay within same-period comparison plus monthly period-vs-period plus bounded MoM boundary.
