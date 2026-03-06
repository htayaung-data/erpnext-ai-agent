# Threshold Exception List Replay Asset Design

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: replay design for the first approved expansion candidate `threshold_exception_list`  
Status: design-preparation asset, implementation not yet approved

## Purpose
This document defines how replay coverage must be built for the `threshold_exception_list` behavioral class before runtime implementation is approved.

The goal is to make sure this class is introduced with the same discipline used for the stabilized core classes:

1. class-level replay coverage
2. first-run evaluation
3. explicit risk-tier handling
4. targeted rerun obligations

## Proposed Suite Name
Recommended manifest suite label:

- `threshold_exception_list`

This suite should remain separate from `core_read` until the class is stable enough to be promoted into the standing core regression mix.

## Class Intent
The replay suite should validate deterministic exception-style list generation where the user asks for records above, below, over, under, overdue, or otherwise outside an expected threshold.

This first slice is limited to factual list outputs only.

Not in scope for this replay suite:

1. advisory explanations
2. causal diagnosis
3. recommendations
4. automatic write/action proposals

## First-Run Rule
All replay scoring must continue to use first-run-only expectations.

For this class:

1. no hidden retry credit
2. no multi-attempt success counted as pass
3. clarification is allowed only where the class definition explicitly requires it

## Required Replay Coverage Structure

### Group A: Finance Customer Exceptions
Minimum families:

1. customers with outstanding amount above threshold
2. customers with outstanding amount below threshold
3. customers with overdue balance above threshold

Minimum examples:

1. `Show customers with outstanding amount above 10000000`
2. `Show customers with outstanding amount over 10,000,000`
3. `Show customers with outstanding amount below 1000000`

Expected output:

1. customer-grain list
2. threshold comparator preserved
3. correct metric column

### Group B: Finance Supplier Exceptions
Minimum families:

1. suppliers with outstanding amount above threshold
2. suppliers with purchase amount above threshold
3. suppliers with overdue payable amount above threshold

Expected output:

1. supplier-grain list
2. no customer drift
3. no item-grain substitution

### Group C: Invoice / Transaction Exceptions
Minimum families:

1. overdue sales invoices above amount threshold
2. overdue purchase invoices above amount threshold
3. invoices below amount threshold where supported by report metadata

Expected output:

1. invoice-grain detail list
2. overdue/status filter preserved
3. threshold amount preserved

### Group D: Inventory Item Exceptions
Minimum families:

1. items with stock below threshold in a warehouse
2. items with stock under threshold using equivalent phrasing
3. items above threshold where supported

Expected output:

1. item-grain list
2. warehouse filter preserved
3. stock quantity or stock balance metric preserved

### Group E: Warehouse Exceptions
Minimum families:

1. warehouses with stock balance below threshold
2. warehouses under stock balance threshold with comma-formatted numbers
3. warehouses above threshold where meaningful

Expected output:

1. warehouse-grain list
2. aggregate-row policy enforced
3. threshold semantics preserved

## Variation Categories That Must Appear In Replay
Every class slice should include these categories where meaningful:

1. base ask
2. equivalent comparator phrasing
3. threshold formatting variation
4. unit/number formatting variation
5. projection follow-up
6. restrictive `only` follow-up
7. top-n follow-up where meaningful
8. scale follow-up where meaningful

## Clarification Cases That Must Be Included
This suite must contain deliberate clarification cases, not just happy paths.

Minimum clarification families:

1. threshold value missing
2. metric missing
3. grain missing
4. warehouse/entity required but omitted

Examples:

1. `Show customers above threshold`
2. `Show items below 20`
3. `Show overdue above 5000000`

Expected outcome:

1. one necessary clarification
2. no wrong silent assumption
3. no clarification loop

## Negative / Unsupported Cases
The suite must include explicit unsupported cases where the class should refuse gracefully.

Examples:

1. mixed advisory asks like `Why are these overdue invoices risky?`
2. unsupported compound asks like `Show customers above 10M but below 20M and grouped by region and salesperson`
3. vague business-risk asks with no threshold basis

Expected outcome:

1. safe refusal or required clarification
2. no fabricated exception logic

## Suggested Minimum Replay Case Counts
Initial design target:

1. finance customer: 8
2. finance supplier: 8
3. invoice/transaction: 8
4. inventory item: 8
5. warehouse: 6
6. clarification / unsupported: 6

Initial target total:

- `44` cases minimum

This is enough for a first disciplined implementation slice without making the first class introduction too thin.

## Risk Tier Split
Recommended replay case tiering:

### Tier 1

1. customer outstanding amount threshold
2. supplier outstanding amount threshold
3. overdue sales invoice threshold
4. overdue purchase invoice threshold

### Tier 2

1. purchase amount threshold
2. item stock threshold
3. warehouse stock balance threshold

### Tier 3

1. equivalent phrasing variants
2. projection follow-ups
3. scale/top-n follow-ups

## Mandatory Cases For Initial Approval
These should be treated as mandatory green before implementation is considered acceptable:

1. customer outstanding amount above threshold
2. supplier outstanding amount above threshold
3. overdue sales invoice above threshold
4. item stock below threshold in warehouse
5. warehouse stock balance below threshold
6. one threshold clarification case
7. one unsupported compound case

## Expected Failure Modes To Track
Replay design should explicitly track and detect:

1. wrong report family
2. wrong grain
3. wrong comparator direction
4. wrong threshold value parsing
5. stale topic carryover from previous result
6. projection follow-up drift
7. scale/top-n follow-up drift

## Rerun Impact Rule Once Implementation Starts
Once runtime implementation begins, the minimum reruns should be:

1. full `threshold_exception_list` suite
2. `core_read`
3. `multiturn_context` if follow-up logic changes
4. standing browser smoke pack
5. release gate for milestone close

## Approval Note
This replay design is a planning asset only.

Runtime implementation should not begin until:

1. this replay design
2. the browser/manual golden design
3. ontology planning
4. capability metadata planning
5. variation matrix

are all complete and reviewed together.
