## Threshold Exception List Follow-Up Projection Hardening Checklist

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: preparation checklist for the deferred hardening slice `threshold_exception_list_followup_projection_hardening`

### Purpose
This checklist exists so richer threshold follow-up projection/display behavior is expanded in a controlled way.

It is not a release approval document.  
It is the gate before any runtime implementation starts for this deferred slice.

### Current Status
- Core threshold slice: complete
- Core threshold replay: green
- Advanced threshold projection/display variants: deferred

Reference:
- [step16_threshold_exception_list_core_slice_status_2026-03-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_core_slice_status_2026-03-04.md)
- [step16_threshold_exception_list_followup_projection_hardening_candidate.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_followup_projection_hardening_candidate.md)

## Checklist

### A. Scope Freeze
- [ ] exact supported follow-up variants listed
- [ ] explicit out-of-scope variants listed
- [ ] no hidden expansion beyond threshold projection/display behavior

### B. Variation Matrix
- [ ] stock-threshold projection variants listed
- [ ] invoice-threshold projection variants listed
- [ ] same-session follow-up ordering variants listed
- [ ] scale + projection interaction variants listed where meaningful

Minimum examples to include:

1. `Show items with stock below 10 in Main warehouse -> I mean 20 -> Give me Item Code, Item Name and Stock Qty`
2. `Show overdue sales invoices above 5000000 -> Show as Million -> Give me Invoice, Customer Name and Invoice Amount`
3. `Show suppliers with purchase amount above 20000000 -> Show in Million -> Show only supplier and purchase amount`

### C. Replay Asset Preparation
- [ ] add replay cases for stock-threshold projection variants
- [ ] add replay cases for invoice-threshold projection variants
- [ ] add replay cases for same-session scale/projection combinations
- [ ] expected output columns and labels defined explicitly

### D. Browser / Manual Golden Preparation
- [ ] manual browser pack updated for deferred variants
- [ ] pass/fail rule written for:
  - label correctness
  - column correctness
  - value preservation
  - no stale topic carryover
- [ ] screenshots required for new browser variants

### E. Metadata / Ontology Review
- [ ] confirm report metadata contains all required dimension/metric aliases
- [ ] confirm explicit business labels are governed where needed:
  - `Item Code`
  - `Item Name`
  - `Invoice`
  - `Customer Name`
  - `Invoice Amount`
- [ ] confirm no prompt-specific routing is needed

### F. Shared-Surface Impact Review
- [ ] impact reviewed for:
  - `response_shaper.py`
  - `memory.py`
  - `read_engine.py`
  - `shaping_policy.py`
  - capability metadata
- [ ] standing browser smoke pack rerun obligations identified
- [ ] impacted replay suites identified

### G. Boundary Check
- [ ] no prompt-to-report map
- [ ] no case-ID logic
- [ ] no runtime keyword hack
- [ ] all intended fixes can be explained by metadata, ontology, persisted state, or generic shaping rules

### H. Approval Readiness
- [ ] candidate ready for formal approval review
- [ ] owner agrees this slice is worth the added complexity now
- [ ] business priority is confirmed

## Recommended Rerun Set If Approved Later

1. full `threshold_exception_list`
2. targeted `transform_followup`
3. standing browser smoke pack
4. focused threshold browser manual pack for the new variants

## Recommendation
Do not start runtime implementation for this deferred slice until this checklist is completed and a formal approval review is recorded.

