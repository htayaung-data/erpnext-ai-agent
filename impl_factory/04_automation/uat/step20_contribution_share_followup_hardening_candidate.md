## Contribution Share Follow-Up Hardening Candidate

Date: 2026-03-06  
Owner: AI Runtime Engineering  
Scope: proposed bounded hardening slice for follow-up variants after `contribution_share` core freeze

### Candidate Name
- `contribution_share_followup_hardening_tier3`

### Relationship To Existing Class
- hardening slice for the already completed core class:
  - `contribution_share`

Reference:

1. [step20_contribution_share_core_slice_status_2026-03-06.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step20_contribution_share_core_slice_status_2026-03-06.md)

### Why This Exists
Core class behavior is green and replay-valid.  
What remains is a narrow follow-up hardening area, not core class correctness failure.

### Deferred Tier-3 Hardening Items
This candidate contains exactly these three deferred items:

1. `show all` expansion should preserve active contribution context
   - expected: keep contribution-share semantics and avoid dropping share columns
2. additive projection follow-up should stay on the same active result
   - expected: add requested column(s) without report/result drift
3. conditional follow-up filtering on active contribution table
   - example: `show only above table if Purchase Amount is greater than zero`
   - expected: deterministic filter behavior or explicit safe clarification/unsupported response

### Why Tier-3
This is additive polish on top of a valid core slice:

1. no core deterministic-read correctness breach in approved first-slice asks
2. no safety breach in deferred-grouping handling
3. behavior gaps are follow-up-variant consistency issues

So these are tracked as:

1. deferred
2. non-blocker for current core-slice closure
3. candidate for a future bounded hardening sprint

### Out Of Scope For This Candidate
Still out of scope:

1. advisory interpretation
2. concentration-risk recommendations
3. time-comparison share analysis
4. broad natural-language follow-up generalization across all classes in this slice

### Activation Rule
This candidate should only move into implementation if:

1. business priority is explicitly confirmed
2. replay add-on cases are prepared first
3. manual/browser add-on cases are prepared first
4. an approval review is recorded before runtime changes

### Required Assets Before Runtime Work
Before implementation:

1. follow-up hardening variation matrix (3 items only)
2. replay add-on case set for those variants
3. manual/browser add-on case set for those variants
4. rerun impact note for:
   - `contribution_share`
   - `transform_followup`
   - `multiturn_context`

### Boundary Rules
Must not do:

1. prompt-to-report maps
2. case-ID logic
3. keyword routing hacks
4. informal widening to other classes during this slice

Must do:

1. class-level deterministic behavior
2. metadata/state-driven follow-up handling
3. replay + manual evidence before closure
