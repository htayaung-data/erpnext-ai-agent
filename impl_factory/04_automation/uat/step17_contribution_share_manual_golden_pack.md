# Contribution Share Manual Golden Pack

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: curated browser/manual golden pack design for `contribution_share`  
Status: design-preparation asset

## Purpose
This document defines the manual/browser golden pack that must exist before `contribution_share` is accepted as implemented.

The goal is to avoid shipping the class based only on replay coverage.

## Manual Pack Objective
Validate that contribution-share asks behave correctly in the real browser path for:

1. report selection
2. grain preservation
3. metric preservation
4. contribution-share calculation visibility
5. projection follow-up
6. top-n follow-up
7. scale follow-up
8. clarification behavior
9. safe refusal for unsupported asks

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
   - wrong metric
   - missing contribution-share column
   - stale topic carryover
   - unnecessary clarification
   - clarification loop
   - internal/debug leakage

## Pack A: Customer Revenue Contribution Share

### MG-CS-01
Prompt:

- `Top 10 customers contribution share of total revenue last month`

Expected:

1. customer-grain result
2. revenue shown
3. contribution share shown

### MG-CS-02
Prompt:

- `Show customers share of total revenue last month`

Expected:

1. customer-grain detail result
2. revenue shown
3. contribution share shown

### MG-CS-03
Same session as MG-CS-01:

- `Show only customer, revenue and contribution share`

Expected:

1. same active result
2. restrictive projection only

### MG-CS-04
Same session as MG-CS-01:

- `Show in Million`

Expected:

1. same ranked customer set
2. revenue scaled
3. contribution share unchanged semantically

## Pack B: Supplier Purchase Contribution Share

### MG-CS-05
Prompt:

- `Top 10 suppliers contribution share of total purchase amount last month`

Expected:

1. supplier-grain result
2. purchase amount shown
3. contribution share shown

### MG-CS-06
Prompt:

- `Show suppliers percent of total purchase amount last month`

Expected:

1. supplier-grain detail result
2. no customer drift

### MG-CS-07
Same session as MG-CS-05:

- `Top 5 only`

Expected:

1. same active result
2. restricted to top 5 suppliers only

## Pack C: Item Sales Contribution Share

### MG-CS-08
Prompt:

- `Top 10 items contribution share of total sales last month`

Expected:

1. item-grain result
2. sales metric shown
3. contribution share shown

### MG-CS-09
Same session as MG-CS-08:

- `Show only item and contribution share`

Expected:

1. restrictive projection
2. same active result

## Pack D: Clarification And Unsupported

### MG-CS-10
Prompt:

- `Show contribution share`

Expected:

1. one necessary clarification
2. no silent assumption of grain or metric

### MG-CS-11
Prompt:

- `Show contribution share of total revenue`

Expected:

1. one clarification for grouping grain
2. no wrong report guess

### MG-CS-12
Prompt:

- `Show revenue share by territory last month`

Expected:

1. safe unsupported or deferred-scope response
2. no silent widening into unapproved grouping support

## Initial Manual Golden Size
Recommended first pack size:

- `12` curated browser cases

## Acceptance Rule Before Runtime Implementation Approval
The class is not ready unless:

1. replay asset design is complete
2. this browser/manual golden pack is complete
3. design review confirms:
   - ontology plan
   - metadata plan
   - variation matrix
   - replay/manual design

## Acceptance Rule Before Phase 3 Operational Adoption
After implementation exists, the manual golden pack is acceptable only if:

1. all mandatory customer and supplier cases pass
2. no retry-to-succeed behavior remains
3. no deferred grouping variants are silently accepted
