## Threshold Exception List Follow-Up Projection Hardening Approval Review

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: formal review record for the deferred hardening slice `threshold_exception_list_followup_projection_hardening`  
Status: reviewed under Phase 3 governance

### Candidate Summary

#### Candidate Name
- `threshold_exception_list_followup_projection_hardening`

#### Candidate ID
- `BC-TE-01-H1`

#### Relationship To Existing Class
- hardening slice for the already implemented core class:
  - `threshold_exception_list`

Reference:
- [step16_threshold_exception_list_core_slice_status_2026-03-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_core_slice_status_2026-03-04.md)
- [step16_threshold_exception_list_followup_projection_hardening_candidate.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_followup_projection_hardening_candidate.md)
- [step16_threshold_exception_list_followup_projection_hardening_checklist.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_followup_projection_hardening_checklist.md)

### Why This Review Exists
The first approved threshold slice is complete in its core scope.

What remains is not a core threshold-read failure.
What remains is a bounded follow-up/display hardening area:

1. richer threshold projection variants
2. invoice-threshold label normalization
3. same-session projection consistency after threshold follow-ups

This review exists so those broader variations are not implemented informally.

### Business Value
This hardening slice improves user experience for same-session threshold analysis by making follow-up requests more natural and consistent.

Examples:

1. `Give me Item Code, Item Name and Stock Qty`
2. `Give me Invoice, Customer Name and Invoice Amount`
3. projection after `Show as Million`

### Current Recommendation
Do not treat this slice as mandatory for closing the current threshold class.

Treat it as:

1. valuable
2. bounded
3. optional until explicitly prioritized

### Scope Summary
Potential scope if later approved:

1. threshold stock-result projection hardening
2. threshold invoice-result projection hardening
3. label normalization for threshold result follow-ups
4. same-session scale + projection consistency on threshold results

### Explicit Non-Goals
Still out of scope:

1. causal explanations
2. recommendations
3. advisory reasoning
4. complaint-style re-evaluation behavior
5. compound threshold logic beyond the existing unsupported envelope

### Risk Tier
- Tier 2 hardening slice
- Tier 1 rigor required if finance-critical invoice displays are touched

### Asset Readiness Review

#### A. Candidate Scope
- [x] bounded
- [x] not open-ended

#### B. Checklist Prepared
- [x] yes

Reference:
- [step16_threshold_exception_list_followup_projection_hardening_checklist.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step16_threshold_exception_list_followup_projection_hardening_checklist.md)

#### C. Replay Assets
- [ ] not yet prepared

#### D. Browser / Manual Assets
- [ ] not yet prepared

#### E. Rerun Impact Plan
- [x] identified at high level
- [ ] not yet fully formalized for execution

### Boundary Review

Decision:
- [x] boundary-safe if implemented through metadata/state/shaping rules
- [ ] boundary risk already identified

Boundary notes:

1. no prompt-to-report routing is required
2. no case-ID logic is required
3. the work should stay inside:
   - shaping
   - projection binding
   - metadata-driven labels
   - follow-up state normalization

### Shared Surface Impact
Likely impacted:

1. [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
2. [shaping_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/shaping_policy.py)
3. [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py)
4. capability metadata

### Approval Decision

- [ ] approved for runtime implementation now
- [x] deferred pending future prioritization
- [ ] rejected

### Why It Is Deferred

1. the core threshold slice is already complete and replay-green
2. this hardening work is additive, not required for current core class validity
3. Phase 3 discipline says broader variation support should only be expanded when explicitly prioritized

### Future Activation Rule
This slice should only move into runtime implementation if:

1. business priority is confirmed
2. the checklist is completed
3. replay/manual assets are prepared first
4. a new implementation approval decision is recorded

### Review Sign-Off

#### Engineering Reviewer
- Name: Codex / AI Runtime Engineering
- Date: 2026-03-04
- Decision: deferred pending future prioritization

#### Product / Business Reviewer
- Name: pending
- Date: pending
- Decision: pending

### Summary In Simple Terms

1. the core threshold class is already good enough
2. richer threshold follow-up display behavior is valuable but optional
3. we should not expand it casually
4. if we want it later, it already has a controlled path

