# Threshold Exception List Approval Review

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: formal implementation-readiness review for the first approved behavioral-class expansion candidate  
Status: reviewed under Phase 3 governance

## Candidate Summary

### Candidate Name
- `threshold_exception_list`

### Candidate ID
- `BC-TE-01`

### Date Of Review
- 2026-03-03

### Requested By
- AI Runtime Engineering

### Primary Owner
- AI Runtime Engineering

### Supporting Owner
- Business / Product reviewer to be assigned for final business sign-off

### Proposed Risk Tier
- Tier 2 baseline
- Tier 1 rigor required for finance-critical subflows

## Business Objective
This class solves a practical business problem:

1. help users ask for records that cross an important threshold
2. help users quickly find items needing attention
3. extend the assistant from “show me data” to “show me what needs review”

This is valuable now because it stays close to the stabilized deterministic ERP read layer while adding visible business value.

## Scope Summary
Planned initial scope:

1. domains:
   - finance
   - inventory
2. entity grains:
   - customer
   - supplier
   - invoice
   - item
   - warehouse
3. metrics:
   - outstanding amount
   - purchase amount
   - grand total / invoice amount
   - stock balance
   - stock quantity
4. logic patterns:
   - above / over / greater than
   - below / under / less than
   - overdue
5. output modes:
   - deterministic exception list
   - projection follow-up
   - restrictive `only` follow-up
   - scale/top-n follow-up where meaningful
6. follow-up behavior:
   - same active-result contract rules as current stabilized read classes

## Explicit Non-Goals
This first slice must not include:

1. causal “why” analysis
2. recommendations
3. decision advice
4. consultant-style narrative
5. write/action automation
6. compound multi-threshold logic beyond the reviewed first slice

## Required Asset Review

### A. Class Definition
- [x] complete

Reference:
- [step15_first_approved_expansion_candidate_threshold_exception_list.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_first_approved_expansion_candidate_threshold_exception_list.md)

### B. Ontology Planning
- [x] complete

Reference:
- [step15_threshold_exception_list_ontology_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_ontology_planning.md)

### C. Capability Metadata Planning
- [x] complete

Reference:
- [step15_threshold_exception_list_capability_metadata_planning.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_capability_metadata_planning.md)

### D. Variation Matrix
- [x] complete

Reference:
- [step15_threshold_exception_list_variation_matrix.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_variation_matrix.md)

### E. Replay Asset Design
- [x] complete

Reference:
- [step15_threshold_exception_list_replay_asset_design.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_replay_asset_design.md)

### F. Browser / Manual Golden Design
- [x] complete

Reference:
- [step15_threshold_exception_list_manual_golden_pack.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_manual_golden_pack.md)

### G. Rerun Impact Plan
- [x] complete

Reference:
- [step15_threshold_exception_list_replay_asset_design.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_threshold_exception_list_replay_asset_design.md)
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

1. class is designed to expand through ontology and metadata, not prompt-specific runtime routing
2. no prompt-to-report map is required by the current design assets
3. no case-ID or tenant-specific routing is required by the current design assets
4. the candidate stays inside deterministic read behavior and does not jump into advisory behavior

## Shared Surface Impact Review
Likely impacted shared surfaces:

- [x] ontology normalization
- [x] capability metadata
- [x] semantic resolver
- [x] memory/state
- [x] transform-followup logic
- [x] response shaping
- [x] quality gate
- [ ] latest-record flow
- [ ] write safety
- [x] release gate metrics

Impact notes:

1. resolver and metadata will be the primary risk surfaces
2. memory/state and shaping are impacted because projection and follow-up behavior are part of class scope
3. latest-record and write safety are not expected to be primary impact areas for the first slice

## Minimum Validation Plan

### New-Class Requirements
- [x] full class replay suite
- [x] variation-matrix coverage
- [x] browser/manual golden coverage
- [x] targeted unit/module regressions

### Existing-Class Regression Requirements
Minimum impacted suites and smoke packs:

1. `threshold_exception_list` full suite
2. `core_read`
3. `multiturn_context` if follow-up behavior is touched
4. standing browser smoke pack

## Release Readiness Rule
This class may not be considered releasable until:

1. replay evidence is green
2. manual golden evidence is green
3. impacted existing suites are green
4. Tier 1 finance obligations are satisfied for finance-critical flows
5. no retry-to-succeed behavior remains

## Open Risks
Current known risks before runtime work begins:

1. capability metadata for threshold-filterable metrics may still need extension before code work
2. finance subflows may require stricter Tier 1 treatment than the broader class baseline
3. comparator and threshold parsing must not drift into hidden runtime lexical logic

## Decision

- [ ] approved for runtime implementation
- [x] approved with conditions
- [ ] not approved

## Conditions
Runtime implementation may begin only under these conditions:

1. implementation stays limited to the approved initial scope in the candidate definition
2. capability metadata additions for the first-slice report paths are committed before or together with runtime logic
3. no advisory, causal, or recommendation behavior is introduced under this class
4. finance-critical flows are treated with Tier 1 validation rigor even if the class baseline remains Tier 2

## Review Sign-Off

### Engineering Reviewer
- Name: Codex / AI Runtime Engineering
- Date: 2026-03-03
- Decision: approved with conditions

### Product / Business Reviewer
- Name: pending
- Date: pending
- Decision: pending business sign-off

### Final Owner Confirmation
- Name: pending
- Date: pending
- Decision: pending operational sign-off

## Recommendation
This candidate is ready to move from pure design-preparation into controlled runtime implementation planning, but only under the conditions above.

In simple terms:

1. the candidate is mature enough to start building
2. it is not approved for release
3. it must stay inside the reviewed scope and governance rules
