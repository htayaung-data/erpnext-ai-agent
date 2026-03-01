# Behavior Variation Matrix: Ranking + Projection + Transform

Date: 2026-03-01  
Owner: AI Runtime Engineering  
Scope: class-level hardening for `ranking_top_n`, `projection_followup`, `transform_last`, and correction/rebind variants  
Status: active stabilization artifact

## Purpose
This matrix exists to stop prompt-by-prompt fixing.

All scenarios below belong to the same behavior family:
- rank a business entity by a metric
- keep the active result stable across follow-ups
- allow projection/transform/correction on that active result
- never switch reports unless the user explicitly asks for a new read

The goal is to close the class with invariants, not chase each sentence separately.

## Class Invariants
1. Fresh explicit read must preserve requested primary grain.
2. Follow-up projection must stay on the latest active result.
3. Restrictive projection with `only` must keep only explicitly requested columns.
4. Transform-scale follow-up must preserve the active result grain and row set.
5. Correction follow-up must preserve the current ranking contract and change only the intended axis.
6. A parser-produced `transform_followup` on a valid active result must be promoted to `TRANSFORM_LAST`, even if planner intent remains `READ`.
7. New report selection is forbidden for projection/transform follow-ups unless the user explicitly starts a fresh read.

## Variation Matrix

| ID | Variant Type | Prompt / Flow | Expected Outcome | Current Status |
|---|---|---|---|---|
| RP-01 | Base ranking | `Top 10 products by sold quantity last month` | `Item-wise Sales Register`, columns `Item`, `Sold Quantity` | Passing |
| RP-02 | Add-column follow-up | `with Item Name` after RP-01 | Same report/result, columns `Item`, `Sold Quantity`, `Item Name` | Passing |
| RP-03 | Restrictive projection | `Give me Item Name and Sold Qty only` after RP-02 | Same report/result, columns only `Item Name`, `Sold Quantity` | Passing after latest fix |
| RP-04 | Single-column projection | `Give me Item Name only` after RP-02 | Same report/result, column only `Item Name` | Under verification after latest promotion/shaper fixes |
| RP-05 | Base customer ranking | `Top 7 customers by revenue last month` | Customer-grain ranking, not item-grain detail | Failing in latest browser evidence |
| RP-06 | Customer projection | `please give Customer Name and Revenue only` after RP-05 | Same customer ranking, columns `Customer`, `Revenue` only | Partially passing but depends on RP-05 correctness |
| RP-07 | Customer single-column projection | `please give Customer Name only` after RP-05 | Same customer ranking, column only `Customer` | Failing in latest browser evidence |
| RP-08 | Column-only alias variant | `Give me Customer Column only` after RP-05 | Same customer ranking, column only `Customer` | Failing in latest browser evidence |
| RP-09 | Supplier purchase ranking | `Top 10 suppliers by purchase amount last month` | `Supplier Ledger Summary`, columns `Supplier`, `Purchase Amount` | Passing |
| RP-10 | Supplier scale follow-up | `Show in Million` after RP-09 | Same report/result, same rows, scaled values | Passing |
| RP-11 | Warehouse ranking | `Top 3 warehouses by stock balance` | `Warehouse Wise Stock Balance`, 3 real warehouse rows | Passing |
| RP-12 | Warehouse scale follow-up | `Show in Million` after RP-11 | Same report/result, same 3 rows, scaled values | Passing |
| RP-13 | Warehouse combined prompt | `Top 3 Warehouse by Stock balance and show as Million` | Same warehouse ranking, scaled | Passing |
| RP-14 | Direction correction | `Lowest 3 warehouses by stock balance` then `I mean Top` | Preserve metric/grain/top_n; change only direction | Previously unstable, needs controlled recheck |

## Latest Findings

### Closed
- Product add-column follow-up now works on first follow-up.
- Restrictive projection with `only` now works for `Item Name + Sold Qty`.
- Supplier purchase ranking works on first attempt.
- Warehouse ranking and million-scale transforms are stable again.

### Open
- Single-column restrictive projection still needs browser confirmation (`Give me Item Name only`).
- Customer ranking by revenue still shows evidence of wrong-grain routing in natural browser variation.
- Customer restrictive projections remain unreliable because the base ranking itself is not yet stable enough.
- Correction/rebind around ranking direction still needs one focused recheck.

## Current Root-Cause Families
1. Primary-grain preservation for customer revenue ranking is still too weak.
2. Restrictive single-column projection must be verified across entity variants, not only item/product.
3. Correction/rebind on ranking direction/top_n still needs one more invariant pass.

## Next Implementation Order
1. Close `RP-04` browser verification:
   - `Top 10 products by sold quantity last month`
   - `with Item Name`
   - `Give me Item Name only`
2. Fix customer ranking primary-grain enforcement:
   - `RP-05`, `RP-06`, `RP-07`, `RP-08`
3. Recheck ranking correction:
   - `RP-14`
4. Only after the matrix is materially green, start controlled `read_engine.py` extraction.

## Exit Rule For This Matrix
This matrix is considered stable only when:
1. All `RP-01` to `RP-04` pass.
2. All `RP-05` to `RP-10` pass.
3. All `RP-11` to `RP-14` pass.
4. No scenario requires a second identical prompt to succeed.
5. No projection/transform follow-up switches to a different report family.
