# Comparison Approval Review

Date: 2026-03-07  
Updated: 2026-03-17  
Owner: AI Runtime Engineering  
Scope: formal implementation-readiness review for `comparison`  
Status: reviewed under Phase 3 governance

## Candidate Summary

### Candidate Name
- `comparison`

### Candidate ID
- `BC-CMP-01`

### Date Of Review
- 2026-03-07

### Requested By
- AI Runtime Engineering

### Primary Owner
- AI Runtime Engineering

### Supporting Owner
- Business/Product reviewer pending final sign-off

### Proposed Risk Tier
- Tier 2 baseline
- Tier 1 rigor required for finance-adjacent customer/supplier comparisons

## Business Objective

1. support deterministic same-period and monthly business comparisons
2. reduce ambiguity for `A vs B` operational asks
3. expand class coverage to bounded MoM without introducing advisory behavior

## Scope Summary

1. domains:
   - sales
   - purchasing
2. grains:
   - territory
   - customer
   - supplier
   - item
3. metrics:
   - revenue
   - purchase amount
4. output mode:
   - deterministic comparison table
   - bounded MoM table
5. follow-up:
   - projection
   - top-n restriction
   - scale
   - correction rebind

## Explicit Non-Goals

1. weekly comparison
2. quarterly comparison
3. YoY and non-month period comparison
4. multi-point time-series output (owned by `trend_time_series`)
5. trend diagnosis
6. advisory recommendation

## Required Asset Review

### A. Class Definition
- [x] complete

Reference:
- [step23_first_approved_expansion_candidate_comparison.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_first_approved_expansion_candidate_comparison.md)

### B. Ontology Planning
- [x] complete

Reference:
- [step23_comparison_ontology_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_ontology_planning.md)

### C. Capability Metadata Planning
- [x] complete

Reference:
- [step23_comparison_capability_metadata_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_capability_metadata_planning.md)

### D. Variation Matrix
- [x] complete

Reference:
- [step23_comparison_variation_matrix.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_variation_matrix.md)

### E. Replay Asset Design
- [x] complete

Reference:
- [step23_comparison_replay_asset_design.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_replay_asset_design.md)

### F. Browser / Manual Golden Design
- [x] complete

Reference:
- [step23_comparison_manual_golden_pack.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_manual_golden_pack.md)

### G. Rerun Impact Plan
- [x] complete

Reference:
- [step23_comparison_replay_asset_design.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step23_comparison_replay_asset_design.md)
- [step14_phase3_rerun_decision_checklist.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_phase3_rerun_decision_checklist.md)

### H. Ownership / Risk Decision
- [x] complete

Reference:
- [step14_phase3_ownership_register_2026-03-03.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_phase3_ownership_register_2026-03-03.md)

## Contract Boundary Check

Decision:
- [x] boundary-safe
- [ ] boundary risk identified

Boundary notes:

1. design requires ontology/metadata-driven semantics
2. no prompt-to-report mapping required
3. no case-ID logic required
4. first slice allows only same-period, monthly period-vs-period, and bounded MoM behavior
5. weekly/quarterly/YoY/multi-point time-series asks remain outside the class boundary

## Shared Surface Impact Review
Likely impacted surfaces:

- [x] ontology normalization
- [x] capability metadata
- [x] semantic resolver
- [x] memory/state
- [x] transform-followup logic
- [x] response shaping
- [x] quality gate
- [ ] latest-record flow
- [ ] write safety
- [ ] release gate metrics

## Minimum Validation Plan

### New-Class Requirements
- [x] full class replay suite
- [x] variation-matrix coverage
- [x] browser/manual golden coverage
- [x] targeted unit/module regressions

### Existing-Class Regression Requirements

1. `comparison_class` full suite
2. `core_read`
3. selected `trend_time_series` boundary probes from existing coverage
4. `multiturn_context` if state/follow-up touched
5. `transform_followup` if transform surfaces touched
6. standing browser smoke pack

## Release Readiness Rule
`comparison` first slice may not be called releasable until:

1. replay evidence is green
2. manual golden evidence is green
3. impacted existing suites are green
4. first-slice boundary is preserved

## Open Risks

1. metadata gaps may force runtime guessing if not closed first
2. correction follow-up may drift without strict active-result binding checks
3. monthly period-anchor ambiguity may cause wrong-period selection if contract signals are weak
4. weekly/quarterly wording may be wrongly accepted if boundary policy is weak

## Decision

- [ ] approved for runtime implementation
- [x] approved with conditions
- [ ] not approved

## Conditions

1. runtime implementation stays within same-period, monthly period-vs-period, and bounded MoM scope
2. weekly/quarterly/YoY and multi-point time-series comparisons remain outside the first slice
3. metadata declarations for comparison-capable metrics and monthly period support are added before runtime guess paths

## Recommendation
Candidate is ready for controlled implementation planning under explicit first-slice boundaries.
