# Contribution Share Replay Asset Design

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: replay design for `contribution_share`  
Status: design-preparation asset

## Purpose
This document defines how replay coverage must be built for the `contribution_share` behavioral class before runtime implementation is accepted.

The goal is to make sure this class is introduced with the same discipline used for stabilized core classes and the first threshold expansion:

1. class-level replay coverage
2. first-run evaluation
3. explicit risk-tier handling
4. targeted rerun obligations

## Proposed Suite Name
Recommended manifest suite label:

- `contribution_share`

This suite should remain separate from `core_read` until the class is stable enough to be promoted into the standing regression mix.

## Class Intent
The replay suite should validate deterministic contribution-share output where the user asks for the share or percent of total by customer, supplier, or item.

This first slice is limited to factual list outputs only.

Not in scope for this replay suite:

1. concentration-risk interpretation
2. recommendations
3. cumulative share analysis
4. time-comparison share analysis

## First-Run Rule
All replay scoring must continue to use first-run-only expectations.

For this class:

1. no hidden retry credit
2. no multi-attempt success counted as pass
3. clarification is allowed only where the class definition explicitly requires it

## Required Replay Coverage Structure

### Group A: Customer Revenue Contribution Share
Minimum families:

1. top-n customer contribution share
2. detail customer contribution share
3. equivalent share phrasing
4. projection/top-n/scale follow-ups

### Group B: Supplier Purchase Contribution Share
Minimum families:

1. top-n supplier contribution share
2. detail supplier contribution share
3. equivalent share phrasing
4. projection/top-n/scale follow-ups

### Group C: Item Sales Contribution Share
Minimum families:

1. top-n item contribution share
2. detail item contribution share
3. equivalent share phrasing
4. projection/top-n follow-ups

### Group D: Clarification Cases
Minimum families:

1. missing metric
2. missing grain
3. missing metric and grain

### Group E: Unsupported Cases
Minimum families:

1. deferred grouping asks
2. cumulative/Pareto asks
3. advisory/risk asks

## Variation Categories That Must Appear In Replay
Every class slice should include these categories where meaningful:

1. base ask
2. equivalent phrasing
3. detail vs top-n
4. projection follow-up
5. restrictive `only` follow-up
6. scale follow-up where meaningful
7. clarification cases
8. unsupported cases

## Suggested Minimum Replay Case Counts
Initial design target:

1. customer revenue share: 10
2. supplier purchase share: 10
3. item sales share: 8
4. clarification: 4
5. unsupported: 4

Initial target total:

- `36` cases minimum

## Risk Tier Split
Recommended replay case tiering:

### Tier 1 rigor

1. customer revenue contribution share
2. supplier purchase contribution share

### Tier 2

1. item sales contribution share
2. top-n and scale follow-ups

### Tier 3

1. equivalent phrasing variants
2. restrictive projection variants

## Mandatory Cases For Initial Approval
These should be treated as mandatory green before implementation is considered acceptable:

1. top customers contribution share of total revenue
2. suppliers contribution share of total purchase amount
3. items contribution share of total sales
4. one projection follow-up
5. one scale follow-up
6. one clarification case
7. one unsupported deferred-grouping case

## Expected Failure Modes To Track
Replay design should explicitly track and detect:

1. wrong report family
2. wrong grain
3. wrong metric basis
4. contribution share column missing
5. contribution share inconsistent with returned metric
6. stale topic carryover from previous result
7. projection follow-up drift
8. scale follow-up incorrectly scaling contribution share itself

## Rerun Impact Rule Once Implementation Starts
Once runtime implementation begins, the minimum reruns should be:

1. full `contribution_share` suite
2. `core_read`
3. `multiturn_context` if follow-up logic changes
4. `transform_followup` if last-result transform behavior changes
5. standing browser smoke pack

## Approval Note
This replay design is a planning asset only.

Runtime implementation should stay inside the reviewed first slice and should not silently expand to deferred grouping variants.
