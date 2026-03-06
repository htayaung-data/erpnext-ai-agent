# Contribution Share Capability Metadata Planning

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: capability/report metadata planning for the `contribution_share` behavioral class  
Status: design-preparation asset

## Purpose
This document identifies the metadata work that must be prepared before runtime implementation of `contribution_share`.

The key rule is:

- runtime should not guess contribution-capable report behavior if capability metadata can declare it explicitly

## Class Objective
Support deterministic contribution-share reads such as:

1. customer share of total revenue
2. supplier share of total purchase amount
3. item share of total sales

## Required Metadata Questions Per Report
For every candidate report, metadata planning must answer:

1. what is the primary grain
2. what metric columns are safe for contribution-share calculation
3. whether aggregate rows exist and must be excluded
4. whether the report returns enough rows for correct total calculation
5. what default visible columns are safe
6. whether ranking support exists

## Approved First-Slice Report Families

### 1. Customer Ledger Summary
Likely use cases:

1. customers share of total revenue
2. top customers contribution share of total revenue

Metadata planning needed:

1. confirm primary grain = customer
2. confirm contribution-capable metric = revenue
3. confirm aggregate-row exclusion policy
4. confirm safe columns for first-turn output

### 2. Supplier Ledger Summary
Likely use cases:

1. suppliers share of total purchase amount
2. top suppliers contribution share of total purchase amount

Metadata planning needed:

1. confirm primary grain = supplier
2. confirm contribution-capable metric = purchase amount
3. confirm aggregate-row exclusion policy
4. confirm safe columns for first-turn output

### 3. Item-wise Sales Register
Likely use cases:

1. items share of total sales
2. top products contribution share of total sales

Metadata planning needed:

1. confirm primary grain = item
2. confirm contribution-capable metric = revenue
3. confirm safe item identifier columns
4. confirm contribution output can be shaped cleanly

## Proposed Metadata Fields To Declare
The following governed semantics should be available for relevant reports/capabilities:

1. `primary_dimension`
2. `result_grain`
3. `supported_metrics`
4. `contribution_metrics`
5. `aggregate_row_policy` or aggregate-row exclusion values
6. `column_roles`
7. `transform_safe_columns`

If these do not exist yet, they should be introduced in a controlled metadata extension instead of buried in runtime logic.

## Known Metadata Gaps To Expect
Before implementation, expect that at least some of these may be missing:

1. explicit `contribution_metrics` declaration
2. safe default first-turn contribution columns
3. consistent aggregate-row handling across summary reports

These gaps should be closed in metadata first, not worked around in runtime with prompt-specific logic.

## Deferred Metadata Scope
Do not assume first-slice support for:

1. territory contribution paths
2. item-group contribution paths
3. customer-group contribution paths
4. supplier-group contribution paths

If these paths are later needed, they must be reviewed as a separate bounded slice.

## Required Output Of This Planning Step
Before runtime implementation begins, this planning step should produce:

1. a list of approved first-slice report paths
2. the missing metadata fields that must be added
3. any blocked use cases that must be deferred
4. the first-slice supported metrics by domain and grain

## Current Recommendation
Do not implement beyond the approved first slice until the report metadata explicitly declares contribution-capable metrics and safe shaping columns.
