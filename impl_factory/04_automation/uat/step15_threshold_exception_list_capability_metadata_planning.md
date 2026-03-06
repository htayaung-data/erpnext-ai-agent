# Threshold Exception List Capability Metadata Planning

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: capability/report metadata planning for the `threshold_exception_list` behavioral class  
Status: design-preparation asset

## Purpose
This document identifies the metadata work that must be prepared before runtime implementation of `threshold_exception_list`.

The key rule is:

- runtime should not guess threshold-ready report behavior if capability metadata can declare it explicitly

## Class Objective
Support deterministic exception-style reads like:

1. customers with outstanding amount above threshold
2. suppliers with outstanding amount above threshold
3. overdue invoices above threshold
4. items below stock threshold
5. warehouses below stock-balance threshold

## Required Metadata Questions Per Report
For every candidate report, metadata planning must answer:

1. what is the primary grain
2. what metric columns are threshold-filterable
3. what comparator directions are safe
4. is the report summary or detail
5. what status columns are available
6. what filters can be safely pinned
7. are aggregate rows present
8. does the report support browser-visible exception-style output cleanly

## Priority Report Families

### 1. Customer Ledger Summary
Likely use cases:

1. customers with outstanding amount above threshold
2. receivable exceptions

Metadata planning needed:

1. confirm primary grain = customer
2. confirm threshold-ready metric = outstanding amount / closing balance
3. confirm whether comparator filtering can be applied at source or must be post-filtered safely
4. confirm acceptable output columns for first slice

### 2. Supplier Ledger Summary
Likely use cases:

1. suppliers with outstanding amount above threshold
2. suppliers with purchase amount above threshold if supported

Metadata planning needed:

1. confirm primary grain = supplier
2. confirm threshold-ready metrics = outstanding amount, purchase amount
3. confirm safe columns and aggregate policy

### 3. Latest Sales / Purchase Invoice Or Invoice Detail Paths
Likely use cases:

1. overdue invoices above threshold
2. invoices above grand total threshold

Metadata planning needed:

1. confirm invoice grain
2. confirm threshold-ready columns: grand total, outstanding, due date / status
3. confirm overdue semantics source:
   - status
   - due date
   - derived field

### 4. Warehouse Wise Stock Balance
Likely use cases:

1. warehouses with stock balance below threshold
2. warehouses with stock balance above threshold

Metadata planning needed:

1. confirm primary grain = warehouse
2. confirm threshold-ready metric = stock balance
3. confirm aggregate-row exclusion policy

### 5. Stock-Per-Item / Item Stock Balance Paths
Likely use cases:

1. items below stock quantity threshold
2. items below threshold in a selected warehouse

Metadata planning needed:

1. confirm primary grain = item
2. confirm threshold-ready metric = stock quantity / balance quantity
3. confirm warehouse-filter support
4. confirm which report should be the governed path for this use case

## Proposed Metadata Fields To Declare
The following governed semantics should be available for relevant reports/capabilities:

1. `primary_dimension`
2. `result_grain`
3. `supported_metrics`
4. `threshold_metrics`
5. `supported_comparators`
6. `status_dimensions`
7. `aggregate_row_policy`
8. `exception_safe_columns`

If these do not exist yet, they should be introduced in a controlled metadata extension instead of buried in runtime logic.

## Finance Planning Notes
Finance exception flows are higher risk than generic analytics.

Planning must explicitly decide:

1. when a finance exception query is `Tier 1`
2. whether post-filtering is acceptable or source filtering is required
3. what “overdue” means operationally:
   - status field
   - due date comparison
   - both

## Inventory Planning Notes
Inventory exception flows need explicit decisions for:

1. stock quantity vs stock balance
2. per-item vs per-warehouse grain
3. whether warehouse scope is required
4. whether zero/aggregate rows should be suppressed

## Known Metadata Gaps To Expect
Before implementation, expect that at least some of these may be missing:

1. explicit threshold-filterable metric declaration
2. explicit comparator support declaration
3. explicit overdue/status semantics
4. explicit aggregate-row policy on stock reports

These gaps should be closed in metadata first, not worked around in runtime with prompt-specific logic.

## Required Output Of This Planning Step
Before runtime implementation begins, this planning step should produce:

1. a list of approved report paths for the first slice
2. the missing metadata fields that must be added
3. any blocked use cases that must be deferred
4. the first-slice supported metrics by domain and grain

## Current Recommendation
Do not implement until the candidate report paths and missing metadata items are frozen in a reviewed planning note or metadata change set.
