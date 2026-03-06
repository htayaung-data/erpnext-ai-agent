# Threshold Exception List Variation Matrix

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: initial variation matrix for the `threshold_exception_list` behavioral class  
Status: design-preparation asset

## Purpose
This matrix defines the first controlled prompt families for the new class.

The point is not to approve these exact prompts only. The point is to define the variation structure that implementation must satisfy at class level.

## Class Objective
Return deterministic exception-style lists based on metric threshold and comparator semantics.

## Matrix Columns

| ID | Domain | Grain | Base Ask | Variation Type | Expected Contract Outcome |
|---|---|---|---|---|---|
| TE-01 | finance | customer | `Show customers with outstanding amount above 10000000` | base ask | customer exception list, threshold `gt`, metric `outstanding amount` |
| TE-02 | finance | customer | `Show customers with outstanding amount over 10,000,000` | equivalent comparator phrasing | same as TE-01 |
| TE-03 | finance | customer | `Show only customer and outstanding amount` | projection follow-up | same active result, restrictive projection |
| TE-04 | finance | customer | `Top 5 only` | top-n follow-up | same active result narrowed to top 5 |
| TE-05 | finance | supplier | `Show suppliers with outstanding amount above 20000000` | base ask | supplier exception list, threshold `gt`, metric `outstanding amount` |
| TE-06 | finance | invoice | `Show overdue sales invoices above 5000000` | status + threshold | invoice exception list, overdue + amount threshold |
| TE-07 | inventory | item | `Show items with stock below 20 in Main warehouse` | base ask | item exception list, threshold `lt`, warehouse filter |
| TE-08 | inventory | item | `Show items under 20 stock in Main warehouse` | equivalent phrasing | same as TE-07 |
| TE-09 | inventory | item | `Show only item and stock quantity` | projection follow-up | same active result, restrictive projection |
| TE-10 | inventory | warehouse | `Show warehouses with stock balance below 50000000` | base ask | warehouse exception list, threshold `lt`, metric `stock balance` |
| TE-11 | inventory | warehouse | `Show warehouses under 50,000,000 stock balance` | equivalent phrasing | same as TE-10 |
| TE-12 | inventory | warehouse | `Show as Million` | transform follow-up | same warehouse exception result, scaled values |

## Required Variation Categories
Implementation is not ready unless the class design covers all of these:

1. base ask
2. equivalent comparator phrasing
3. threshold value formatting variation
4. projection follow-up
5. restrictive `only` follow-up
6. top-n follow-up where meaningful
7. domain/grain variation

## Clarification Cases To Include
The matrix must also include cases that should clarify rather than guess.

Examples to add during replay design:

1. `Show items above 20`
   - unclear metric
2. `Show overdue above 5 million`
   - unclear grain
3. `Show customers above threshold`
   - missing threshold value

## Explicit Non-Goals For First Slice
These should not be treated as required passes in the first implementation slice:

1. `Why are these invoices overdue?`
2. `What should I do first?`
3. `Which customers are risky?`
4. compound logic with multiple thresholds and exclusions

## Use Rule
This variation matrix should be used later to build:

1. replay cases
2. browser/manual golden cases
3. impact-based regression obligations
