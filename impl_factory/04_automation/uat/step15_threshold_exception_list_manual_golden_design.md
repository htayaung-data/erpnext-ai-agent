# Threshold Exception List Manual Golden Design

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: curated browser/manual golden design for the `threshold_exception_list` behavioral class  
Status: design-preparation asset

## Purpose
This document defines the manual/browser golden pack that must exist before the first implementation of `threshold_exception_list` is considered safe.

This is not for exploratory testing. It is the curated human-facing proof pack for the new class.

## Why Manual Golden Is Required
Replay is necessary but not enough.

This class introduces:

1. threshold semantics
2. exception-oriented business language
3. finance and inventory business importance
4. follow-up interactions on exception lists

So browser/manual confirmation is required before implementation can be accepted.

## Execution Rules
1. Use browser UI.
2. Use a fresh chat unless the case explicitly says to continue the same session.
3. Record:
   - prompt(s)
   - visible report title
   - pass/fail
   - screenshot if failed
4. Fail if any of these happen:
   - wrong report
   - wrong grain
   - wrong comparator behavior
   - threshold not applied
   - stale topic carryover
   - retry required to succeed
   - internal/debug leakage

## Manual Golden Pack

### Pack A: Customer Receivable Exceptions
Risk tier: Tier 1

1. `Show customers with outstanding amount above 10000000`
   Expect:
   - customer-grain exception list
   - outstanding amount threshold applied

2. Continue same session:
   `Show only customer and outstanding amount`
   Expect:
   - same active result
   - restrictive projection only

### Pack B: Supplier Payable/Outstanding Exceptions
Risk tier: Tier 1

1. `Show suppliers with outstanding amount above 20000000`
   Expect:
   - supplier-grain exception list
   - threshold applied

2. Continue same session:
   `Show as Million`
   Expect:
   - same supplier set
   - values scaled

### Pack C: Overdue Invoice Exceptions
Risk tier: Tier 1

1. `Show overdue sales invoices above 5000000`
   Expect:
   - invoice-grain list
   - overdue semantics applied
   - amount threshold applied

### Pack D: Inventory Item Threshold Exceptions
Risk tier: Tier 2

1. `Show items with stock below 20 in Main warehouse`
   Expect:
   - item-grain list
   - warehouse filter applied
   - threshold applied

2. Continue same session:
   `Show only item and stock quantity`
   Expect:
   - same active result
   - restrictive projection

### Pack E: Warehouse Threshold Exceptions
Risk tier: Tier 2

1. `Show warehouses with stock balance below 50000000`
   Expect:
   - warehouse-grain exception list
   - threshold applied

2. Continue same session:
   `Show as Million`
   Expect:
   - same warehouse set
   - values scaled

## Clarification Golden Cases
At least two clarification-required cases should be in the manual pack.

Examples:

1. `Show items above 20`
   Expect:
   - clarification because metric is unclear

2. `Show overdue above 5000000`
   Expect:
   - clarification because grain is unclear

## Follow-Up Golden Cases
At least these follow-up types must be represented:

1. projection follow-up
2. restrictive `only` follow-up
3. scale follow-up
4. top-n follow-up if supported in the implementation slice

## Manual Pass Rule
The class should not be considered ready until:

1. every Tier 1 manual case passes
2. all clarification cases behave safely
3. no case needs prompt repetition to succeed
4. no cross-topic contamination occurs

## Required Output Of This Design Step
Before implementation begins, this step should provide:

1. named browser/manual golden cases
2. explicit pass expectations
3. risk-tier marking per case pack
4. clarification cases
5. follow-up cases

## Current Recommendation
Do not approve runtime implementation until:

1. this manual golden design is reviewed
2. the replay asset design is reviewed
3. the ontology and capability planning assets are reviewed together
