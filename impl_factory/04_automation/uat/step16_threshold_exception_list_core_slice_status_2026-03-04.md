## Threshold Exception List Core Slice Status

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: status of the first approved implementation slice for `threshold_exception_list`

### Decision
- Core slice complete
- Replay validated
- Advanced projection/display variants deferred to a later bounded hardening slice

### What Is Complete
The approved first slice is complete for:

1. deterministic threshold exception reads for:
   - customers by outstanding amount
   - suppliers by outstanding amount
   - suppliers by purchase amount
   - overdue sales invoices
   - overdue purchase invoices
   - items below stock threshold in a warehouse
   - warehouses above/below stock balance threshold
2. approved blocker clarification behavior
3. approved unsupported/error-envelope behavior
4. approved threshold follow-up behaviors in the first slice:
   - threshold value correction like `I mean 20`
   - supported `Top N only`
   - supported scale follow-up where meaningful

### Replay Evidence
Authoritative current suite result:

- [20260304T075158Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260304T075158Z_phase6_manifest_uat_raw_v3.json)

Summary:

1. total: `44`
2. passed: `44`
3. failed: `0`
4. first-run pass rate: `1.0`

### What Is Not Included In Core Completion
The following are not considered blocker failures for closing the first approved slice, because they were not part of the approved minimum scope and are not yet fully generalized:

1. richer projection variants on threshold results such as:
   - `Give me Item Code, Item Name and Stock Qty`
   - `Give me Invoice, Customer Name and Invoice Amount`
2. invoice-threshold display normalization variants where multiple metric-like columns may need tighter business-label normalization
3. broader natural-language re-evaluation prompts outside the approved first follow-up slice

### Why They Are Deferred
These remaining behaviors are not core threshold-read correctness failures.
They are follow-up projection/display hardening work on top of an already valid deterministic class.

Enterprise rule:

1. do not keep widening scope informally in the same cycle
2. treat broader variations as a new bounded hardening slice
3. prepare and approve that slice before implementation

### Current Product Meaning
In simple terms:

1. the first threshold class is successfully implemented
2. the approved core business questions for that class are working
3. the class is not yet fully broadened for all extra projection/display variations

### Recommended Next Step
Use a new bounded hardening slice for:

1. threshold projection variants
2. invoice-threshold display normalization
3. richer same-session projection behavior on threshold outputs

Reference:

- [step16_threshold_exception_list_followup_projection_hardening_candidate.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_followup_projection_hardening_candidate.md)

