# Threshold Exception List Manual Golden Pack

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: curated browser/manual golden pack design for the first approved expansion candidate `threshold_exception_list`  
Status: design-preparation asset, implementation not yet approved

## Purpose
This document defines the manual/browser golden pack that must exist before the `threshold_exception_list` class is approved for runtime implementation and later Phase 3 operation.

The goal is to avoid shipping the class based only on replay coverage.

## Manual Pack Objective
Validate that threshold-based exception asks behave correctly in the real browser path for:

1. threshold parsing
2. comparator direction
3. grain preservation
4. follow-up projection
5. follow-up scaling
6. clarification behavior
7. safe refusal for unsupported asks

## Execution Rules
1. Use a fresh chat unless the case explicitly requires same-session follow-up.
2. Record:
   - prompt(s)
   - visible report title
   - visible columns
   - pass/fail
   - screenshot
   - short failure note if needed
3. A case fails if any of these happen:
   - wrong report
   - wrong grain
   - wrong threshold direction
   - wrong threshold value handling
   - stale topic carryover
   - unnecessary clarification
   - clarification loop
   - internal/debug leakage

## Pack A: Finance Customer Exceptions

### MG-TE-01
Prompt:

- `Show customers with outstanding amount above 10000000`

Expected:

1. customer-grain result
2. outstanding amount shown
3. only customers above threshold

### MG-TE-02
Prompt:

- `Show customers with outstanding amount over 10,000,000`

Expected:

1. same business result as MG-TE-01
2. no wrong comparator drift

### MG-TE-03
Same session as MG-TE-01:

- `Show only customer and outstanding amount`

Expected:

1. same active result
2. restrictive projection only

## Pack B: Finance Supplier Exceptions

### MG-TE-04
Prompt:

- `Show suppliers with outstanding amount above 20000000`

Expected:

1. supplier-grain result
2. no customer drift
3. no item-grain substitution

### MG-TE-05
Prompt:

- `Show suppliers with purchase amount above 50000000`

Expected:

1. supplier-grain result
2. purchase amount metric, not outstanding amount

### MG-TE-06
Same session as MG-TE-05:

- `Show in Million`

Expected:

1. same result
2. scaled metric values only

## Pack C: Invoice / Overdue Exceptions

### MG-TE-07
Prompt:

- `Show overdue sales invoices above 5000000`

Expected:

1. invoice-grain list
2. overdue or unpaid status retained
3. amount threshold retained

### MG-TE-08
Prompt:

- `Show overdue purchase invoices above 10000000`

Expected:

1. purchase invoice-grain list
2. supplier context retained

## Pack D: Inventory Item Exceptions

### MG-TE-09
Prompt:

- `Show items with stock below 20 in Main warehouse`

Expected:

1. item-grain result
2. Main warehouse filter retained
3. low-stock direction retained

### MG-TE-10
Prompt:

- `Show items under 20 stock in Main warehouse`

Expected:

1. same business result as MG-TE-09

### MG-TE-11
Same session as MG-TE-09:

- `Show only item and stock quantity`

Expected:

1. restrictive projection
2. same active result

## Pack E: Warehouse Exceptions

### MG-TE-12
Prompt:

- `Show warehouses with stock balance below 50000000`

Expected:

1. warehouse-grain result
2. aggregate row excluded unless explicitly required
3. below-threshold semantics retained

### MG-TE-13
Same session as MG-TE-12:

- `Show as Million`

Expected:

1. same result
2. scaled stock balance values only

## Pack F: Clarification And Unsupported

### MG-TE-14
Prompt:

- `Show customers above threshold`

Expected:

1. one necessary clarification
2. no silent assumption of value or metric

### MG-TE-15
Prompt:

- `Show items below 20`

Expected:

1. clarification for metric or warehouse where needed
2. no wrong report guess

### MG-TE-16
Prompt:

- `Why are these overdue invoices risky?`

Expected:

1. safe refusal or out-of-scope response
2. no fabricated consultant-style analysis under this class

## Initial Manual Golden Size
Recommended first pack size:

- `16` curated browser cases

This is enough to verify the class in browser without turning the manual pack into a full exploratory test program.

## Acceptance Rule Before Runtime Implementation Approval
The class is not ready for runtime implementation unless:

1. replay asset design is complete
2. this browser/manual golden pack is complete
3. design review confirms:
   - ontology plan
   - metadata plan
   - variation matrix
   - replay/manual design

## Acceptance Rule Before Phase 3 Operational Adoption
After implementation exists, the manual golden pack is acceptable only if:

1. all mandatory finance cases pass
2. all mandatory inventory cases pass
3. clarification/unsupported cases behave safely
4. no case requires retry to succeed

## Use Rule
This manual pack should later be used for:

1. implementation approval sign-off
2. milestone browser validation
3. post-change smoke checks when the class is modified
