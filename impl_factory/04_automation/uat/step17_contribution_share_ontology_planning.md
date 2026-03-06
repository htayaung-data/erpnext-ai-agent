# Contribution Share Ontology Planning

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: ontology design planning for the `contribution_share` behavioral class  
Status: design-preparation asset

## Purpose
This document defines the ontology-side planning for:

- `contribution_share`

The goal is to make sure share/contribution language is governed before runtime implementation starts.

This is not runtime code. It is the planning document that defines what ontology support must exist first.

## Class Objective
Interpret business requests that ask for each entity's percent share of a total, such as:

1. customers share of total revenue
2. suppliers share of total purchase amount
3. items contribution share of total sales

The ontology must normalize user wording into canonical contribution intent semantics that runtime can consume generically.

## Canonical Contribution Intent Set
The first approved intent set should be:

1. `share_of_total`
2. `contribution_share`

For the first implementation slice, these may be treated as one runtime execution family as long as ontology aliases remain explicit and governed.

## Contribution Language Coverage
The ontology should normalize the following surface forms.

### Canonical `share_of_total`
Examples:

1. share of total
2. percent of total
3. percentage of total
4. percentage contribution

### Canonical `contribution_share`
Examples:

1. contribution share
2. contribution to total
3. contributes to total
4. contribution %

## Metric Families In Scope
The ontology planning for this class should support the following canonical metric families first:

1. `revenue`
2. `purchase_amount`

Possible later additions:

1. sold quantity share
2. outstanding amount share
3. margin share

These later additions should not be assumed in the first implementation slice.

## Grain / Dimension Semantics In Scope
The ontology planning for this class should support the following entity grains first:

1. `customer`
2. `supplier`
3. `item`

Possible later additions:

1. territory
2. item group
3. customer group
4. supplier group

These are explicitly deferred from the first slice.

## Domain-Specific Contribution Semantics

### Sales
Supported semantic patterns:

1. customer share of total revenue
2. item share of total sales

### Purchasing
Supported semantic patterns:

1. supplier share of total purchase amount

These remain deterministic read behaviors, not advisory behaviors.

## Clarification-Trigger Ambiguities
The ontology planning must explicitly acknowledge the cases where clarification should still be needed.

Clarification should likely be required when:

1. metric is missing
   - `show customer contribution share`
2. grouping grain is missing
   - `show contribution share of total revenue`
3. the request asks for a deferred grouping
   - `show revenue share by territory`

## Known Ambiguity Examples To Design Around

1. `show contribution share`
   - ambiguous: share of what, by what
2. `show percent of total revenue`
   - ambiguous: by customer, supplier, or item
3. `show customer share`
   - ambiguous: revenue, outstanding amount, or some other measure

## Out-Of-Scope Language For First Slice
The ontology should explicitly mark these as not first-slice commitments:

1. concentration-risk wording
   - dominant
   - overexposed
   - too dependent
2. advisory language
   - which ones should I focus on
   - is this healthy
3. cumulative distribution language
   - cumulative share
   - running share
   - Pareto
4. comparison language
   - compare share vs last month

## Relationship To Existing Ontology
This class should reuse existing ontology where possible:

1. canonical metric normalization
2. canonical dimension normalization
3. domain inference
4. transform ambiguity semantics

New ontology additions must remain additive and controlled, not a hidden routing table.

## Required Output Of This Planning Step
Before runtime implementation begins, the following should exist in governed form:

1. approved contribution/share alias inventory
2. approved in-scope metrics and grains
3. approved ambiguity / clarification cases
4. approved out-of-scope list

## Current Recommendation
Implementation should not widen beyond the first slice until:

1. territory/group-share semantics are separately planned
2. cumulative or diagnostic share semantics are separately approved
