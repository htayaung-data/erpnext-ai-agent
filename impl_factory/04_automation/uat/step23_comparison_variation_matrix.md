# Comparison Variation Matrix

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: initial variation matrix for `comparison`  
Status: design-preparation asset

## Purpose
Define first controlled prompt families for comparison behavior.

The unit of closure is class-level variation coverage, not one successful prompt.

## Matrix

| ID | Domain | Grain | Base Ask | Variation Type | Expected Contract Outcome |
|---|---|---|---|---|---|
| CMP-01 | sales | territory | `Compare Yangon and Mandalay sales last month by territory` | base ask | deterministic side-by-side territory comparison |
| CMP-02 | sales | territory | `Yangon vs Mandalay revenue last month` | equivalent phrasing | same as CMP-01 |
| CMP-03 | sales | territory | `Compare Mandalay and Yangon sales last month` | entity-order variation | same result semantics, deterministic ordering policy |
| CMP-04 | sales | territory | `Show only territory and revenue` | projection follow-up | same active result, restrictive projection |
| CMP-05 | sales | territory | `Top 2 only` | follow-up bound | same active result, bounded row restriction |
| CMP-06 | sales | territory | `Show in Million` | scale follow-up | same comparison result with scaled amount |
| CMP-07 | sales | customer | `Compare Shwe Li Road Mobile Wholesale and Latha Mobile Wholesale revenue last month` | base ask | same-period customer revenue comparison |
| CMP-08 | purchasing | supplier | `Compare Sunflower Accessories Co. and Golden Dragon Trading Co. Ltd. purchase amount last month` | base ask | same-period supplier purchase comparison |
| CMP-09 | sales | item | `Compare SPH-SAM-A15-6/128 and SPH-XMI-RN13-8/256 sales last month` | base ask | same-period item sales comparison |
| CMP-10 | sales | territory | `Actually compare Yangon and Bago instead` | correction follow-up | correction/rebind updates only compared entities |
| CMP-11 | sales | territory | `Compare Yangon revenue in March 2026 vs February 2026` | monthly period comparison | deterministic month-vs-month comparison |
| CMP-12 | sales | territory | `Show Yangon revenue month over month for March 2026` | MoM ask | bounded monthly comparison with deterministic delta semantics |
| CMP-13 | sales | territory | `Compare Yangon revenue week over week` | out-of-scope ask | safe unsupported for weekly comparison |
| CMP-14 | sales | territory | `Compare Yangon revenue quarter over quarter` | out-of-scope ask | safe unsupported for quarterly comparison |
| CMP-15 | sales | territory | `Compare Yangon and Mandalay` | missing metric/grain | bounded clarification, no silent guess |

## Required Variation Categories

1. base ask
2. equivalent phrasing
3. monthly period-vs-period
4. bounded MoM
5. projection follow-up
6. restrictive follow-up
7. scale follow-up
8. correction follow-up
9. unsupported period-structure ask
10. clarification case

## First-Slice Non-Goals

1. weekly comparison
2. quarterly comparison
3. YoY comparison
4. multi-point time-series output
5. advisory interpretation of why one entity is higher
