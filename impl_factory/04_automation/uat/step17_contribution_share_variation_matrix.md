# Contribution Share Variation Matrix

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: initial variation matrix for the `contribution_share` behavioral class  
Status: design-preparation asset

## Purpose
This matrix defines the first controlled prompt families for the new class.

The point is not to approve these exact prompts only. The point is to define the variation structure that implementation must satisfy at class level.

## Class Objective
Return deterministic contribution-share lists that show entity, base amount, and percent share of total.

## Matrix Columns

| ID | Domain | Grain | Base Ask | Variation Type | Expected Contract Outcome |
|---|---|---|---|---|---|
| CS-01 | sales | customer | `Top 10 customers contribution share of total revenue last month` | base ask | customer ranking with revenue and contribution share |
| CS-02 | sales | customer | `Top 10 customers share of total revenue last month` | equivalent phrasing | same as CS-01 |
| CS-03 | sales | customer | `Show customers contribution to total revenue last month` | non-top-n base ask | detail output with customer, revenue, contribution share |
| CS-04 | sales | customer | `Show only customer, revenue and contribution share` | projection follow-up | same active result, restrictive projection |
| CS-05 | sales | customer | `Top 5 only` | top-n follow-up | same active result narrowed to top 5 |
| CS-06 | sales | customer | `Show in Million` | scale follow-up | base metric scaled, contribution share unchanged |
| CS-07 | purchasing | supplier | `Top 10 suppliers contribution share of total purchase amount last month` | base ask | supplier ranking with purchase amount and contribution share |
| CS-08 | purchasing | supplier | `Show suppliers percent of total purchase amount last month` | equivalent phrasing | detail output with supplier, purchase amount, contribution share |
| CS-09 | purchasing | supplier | `Show only supplier and contribution share` | restrictive projection follow-up | same active result, restrictive projection |
| CS-10 | sales | item | `Top 10 items contribution share of total sales last month` | base ask | item ranking with revenue and contribution share |
| CS-11 | sales | item | `Show items share of total revenue last month` | equivalent phrasing | detail output with item, revenue, contribution share |
| CS-12 | sales | item | `Show only item and contribution share` | restrictive projection follow-up | same active result, restrictive projection |

## Required Variation Categories
Implementation is not ready unless the class design covers all of these:

1. base ask
2. equivalent share phrasing
3. detail and top-n variants
4. projection follow-up
5. restrictive `only` follow-up
6. scale follow-up
7. domain/grain variation

## Clarification Cases To Include
The matrix must also include cases that should clarify rather than guess.

Examples to add during replay design:

1. `Show contribution share`
   - missing metric and grain
2. `Show contribution share of total revenue`
   - missing grain
3. `Show customer contribution share`
   - missing metric

## Explicit Non-Goals For First Slice
These should not be treated as required passes in the first implementation slice:

1. `Show revenue share by territory`
2. `Show cumulative customer share of total revenue`
3. `Which customers are too concentrated?`
4. `Compare customer share this month vs last month`

## Use Rule
This variation matrix should later be used to build:

1. replay cases
2. browser/manual golden cases
3. impacted-suite rerun obligations
