# Threshold Exception List Ontology Planning

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: ontology design planning for the `threshold_exception_list` behavioral class  
Status: design-preparation asset

## Purpose
This document defines the ontology-side planning for the first approved expansion candidate:

- `threshold_exception_list`

The goal is to make sure threshold, comparator, and exception language are governed before runtime implementation starts.

This is not runtime code. It is the planning document that defines what ontology support must exist first.

## Class Objective
Interpret business requests that ask for records crossing a threshold, such as:

1. above a value
2. below a value
3. overdue above a value
4. under-stock below a value
5. exceptions needing attention

The ontology must normalize user wording into canonical comparison semantics that runtime can consume generically.

## Canonical Comparator Set
The first approved comparator set should be:

1. `gt`
   - greater than
2. `gte`
   - greater than or equal to
3. `lt`
   - less than
4. `lte`
   - less than or equal to
5. `eq`
   - equal to

For initial implementation, the required minimum set is:

1. `gt`
2. `lt`
3. `gte`
4. `lte`

`eq` may remain optional if not needed in the first release slice.

## Comparator Language Coverage
The ontology should normalize the following surface forms.

### Canonical `gt`
Examples:

1. above
2. over
3. greater than
4. more than
5. higher than
6. exceeds

### Canonical `gte`
Examples:

1. at least
2. greater than or equal to
3. no less than
4. minimum of

### Canonical `lt`
Examples:

1. below
2. under
3. less than
4. lower than
5. fewer than

### Canonical `lte`
Examples:

1. at most
2. less than or equal to
3. no more than
4. maximum of

## Exception-Oriented Language Coverage
Some asks are not purely numeric-comparator style. They carry exception language that should be normalized into compatible threshold/filter semantics.

Initial approved exception-oriented terms:

1. overdue
2. due
3. below minimum stock
4. low stock
5. understock
6. outstanding above
7. payable above
8. receivable above

## Metric Families In Scope
The ontology planning for this class should support the following canonical metric families first:

1. `outstanding amount`
2. `purchase amount`
3. `grand total`
4. `stock balance`
5. `stock quantity`

Possible later additions:

1. margin
2. sold quantity
3. delayed days
4. aging buckets

These later additions should not be assumed in the first implementation slice.

## Threshold Value Semantics
The ontology itself should not compute values, but planning must define acceptable threshold expression forms.

Approved value forms for the first slice:

1. plain integers
   - `20`
   - `5000000`
2. comma-formatted numbers
   - `5,000,000`
3. decimal values
   - `10.5`
4. common unit words if already governed elsewhere
   - `10 million`

If unit words are not already governed clearly, they must be added before implementation.

## Domain-Specific Exception Semantics

### Finance
Supported semantic patterns:

1. receivables above threshold
2. payables above threshold
3. overdue invoices above threshold

### Inventory
Supported semantic patterns:

1. stock below threshold
2. stock balance below threshold
3. low-stock exception listing

These are still deterministic read behaviors, not advisory behaviors.

## Clarification-Trigger Ambiguities
The ontology planning must explicitly acknowledge the cases where clarification should still be needed.

Clarification should likely be required when:

1. metric is missing
   - `show items above 20`
2. threshold exists but comparator is not safely inferable
3. entity grain is unclear
   - `show above 5 million`
4. exception word is too broad without a governed meaning
   - `show bad records`

## Known Ambiguity Examples To Design Around

1. `show items above 20`
   - ambiguous: amount? quantity? stock?
2. `show overdue above 5 million`
   - ambiguous: invoice? customer? supplier?
3. `show stock under 20`
   - ambiguous if warehouse/location scope matters
4. `show top customers above 10 million`
   - combines ranking and threshold; must be clearly supported or deferred

## Out-Of-Scope Language For First Slice
The ontology should explicitly mark these as not first-slice commitments:

1. fuzzy business adjectives
   - risky
   - weak
   - poor performing
2. advisory language
   - which ones should I focus on
   - what should I do first
3. causal language
   - why are these overdue
4. multi-threshold compound logic
   - above X and below Y and not in region Z

## Relationship To Existing Ontology
This class should reuse existing ontology where possible:

1. canonical metric normalization
2. canonical dimension normalization
3. domain inference
4. transform ambiguity semantics

New ontology additions must remain additive and controlled, not a hidden routing table.

## Required Output Of This Planning Step
Before runtime implementation begins, the following should exist in governed form:

1. approved comparator alias inventory
2. approved exception-term inventory
3. approved threshold value forms
4. approved ambiguity / clarification cases
5. approved out-of-scope list

## Current Recommendation
Implementation should not begin until:

1. comparator semantics are explicitly added to governed ontology data
2. threshold value expression handling is agreed
3. ambiguity and non-goals are frozen
