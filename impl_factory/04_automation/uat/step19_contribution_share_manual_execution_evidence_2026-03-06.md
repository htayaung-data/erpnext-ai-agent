# Contribution Share Manual Execution Evidence

Date: 2026-03-06  
Owner: AI Runtime Engineering  
Scope: controlled browser/manual evidence capture for `contribution_share`  
Status: in execution (partial pass evidence captured, Phase 3 governance)

## Governing References

1. `step13_behavioral_class_development_contract.md`
2. `step14_phase3_regression_discipline_contract.md`
3. `step16_phase3_baseline_freeze_2026-03-04.md`
4. `step17_contribution_share_manual_golden_pack.md`
5. `step17_contribution_share_approval_review_2026-03-04.md`
6. `step18_contribution_share_implementation_plan_2026-03-04.md`

## Scope Boundary

This evidence run is limited to the approved first slice:

1. customer revenue contribution share
2. supplier purchase-amount contribution share
3. item sales contribution share
4. required clarification and unsupported handling inside approved boundaries

Explicitly out of scope:

1. territory/group contribution support
2. advisory/concentration interpretation
3. time-comparison share analysis

## Replay Baseline Snapshot (Already Green)

1. `contribution_share`:
   - `OUT=impl_factory/04_automation/logs/20260305T100328Z_phase6_manifest_uat_raw_v3.json`
   - result: `36/36`, first-run pass rate `1.0`
2. `multiturn_context`:
   - `OUT=impl_factory/04_automation/logs/20260305T194722Z_phase6_manifest_uat_raw_v3.json`
   - result: `81/81`, first-run pass rate `1.0`
3. `transform_followup`:
   - `OUT=impl_factory/04_automation/logs/20260305T205542Z_phase6_manifest_uat_raw_v3.json`
   - result: `61/61`, first-run pass rate `1.0`
4. `core_read`:
   - `OUT=impl_factory/04_automation/logs/20260305T140903Z_phase6_manifest_uat_raw_v3.json`
   - result: `114/114`, first-run pass rate `1.0`

## Manual Run Protocol (Mandatory)

1. Use a fresh chat for every base case unless the case is explicitly marked as same-session follow-up.
2. Keep role/mode fixed to reader path for this pack.
3. For each case, record:
   - prompt
   - report title
   - visible columns
   - pass/fail
   - screenshot path
   - note
4. Do not mark a case pass if:
   - wrong report is selected
   - contribution-share column is missing
   - unsupported ask is silently accepted
   - clarification-required ask is answered without clarification

## Current Manual Observation Triage (From Prior Uncontrolled Run)

The previously captured browser outputs are informative but not closure-grade evidence because fresh-chat boundaries were not enforced per pack rules. They are treated as triage-only observations.

Triage observations:

1. contribution-share prompts sometimes returned tables without an explicit contribution-share column.
2. `Show contribution share of total revenue` returned a data table in one run, where manual pack expects clarification.
3. `Show revenue share by territory last month` returned a table in one run, where manual pack expects safe unsupported/deferred response.

Decision:

1. do not close manual evidence from uncontrolled runs
2. execute controlled MG-CS run below

Post-triage note:

1. after runtime refresh (`backend` + `websocket` restart), browser/manual behavior aligned with replay/API-path behavior for the targeted recovery cases.

## Controlled MG-CS Execution Ledger

### Pack A: Customer Revenue

1. `MG-CS-01`
   - prompt: `Top 10 customers contribution share of total revenue last month`
   - expected: customer grain, revenue, contribution share
   - observed: `Customer Ledger Summary` with columns `Customer`, `Revenue`, `Party`, `Invoiced Amount`, `Amount`, `Contribution Share`
   - status: pass (2026-03-06)
2. `MG-CS-02`
   - prompt: `Show customers share of total revenue last month`
   - expected: customer detail, revenue, contribution share
   - status: pending
3. `MG-CS-03` (same session as MG-CS-01)
   - prompt: `Show only customer, revenue and contribution share`
   - expected: restrictive projection on same active result
   - status: pending
4. `MG-CS-04` (same session as MG-CS-01)
   - prompt: `Show in Million`
   - expected: same ranked set, metric scaled, share semantics preserved
   - status: pending

Supplemental observed follow-up (not a mandatory MG case id):

1. prompt: `Show Customer name and contribution share only`
2. observed: `Customer Ledger Summary` with `Customer`, `Contribution Share`
3. status: pass (2026-03-06)

### Pack B: Supplier Purchase

1. `MG-CS-05`
   - prompt: `Top 10 suppliers contribution share of total purchase amount last month`
   - expected: supplier grain, purchase amount, contribution share
   - status: pending
2. `MG-CS-06`
   - prompt: `Show suppliers percent of total purchase amount last month`
   - expected: supplier detail, no customer drift
   - status: pending
3. `MG-CS-07` (same session as MG-CS-05)
   - prompt: `Top 5 only`
   - expected: same active result narrowed to top 5
   - status: pending

### Pack C: Item Sales

1. `MG-CS-08`
   - prompt: `Top 10 items contribution share of total sales last month`
   - expected: item grain, sales metric, contribution share
   - status: pending
2. `MG-CS-09` (same session as MG-CS-08)
   - prompt: `Show only item and contribution share`
   - expected: restrictive projection on same active result
   - status: pending

### Pack D: Clarification and Unsupported

1. `MG-CS-10`
   - prompt: `Show contribution share`
   - expected: one required clarification
   - observed: clarification question asking for business measure
   - status: pass (2026-03-06, fresh chat)
2. `MG-CS-11`
   - prompt: `Show contribution share of total revenue`
   - expected: one clarification for grouping grain
   - observed: clarification question asking for grouping (`customer`, `supplier`, `item`)
   - status: pass (2026-03-06, fresh chat)
3. `MG-CS-12`
   - prompt: `Show revenue share by territory last month`
   - expected: safe unsupported/deferred response
   - observed: safe unsupported message (`grouping not in approved first slice`)
   - status: pass (2026-03-06)

## Current Completion Snapshot

1. mandatory cases passed: `4 / 12` (`MG-CS-01`, `MG-CS-10`, `MG-CS-11`, `MG-CS-12`)
2. remaining mandatory cases pending: `8 / 12` (`MG-CS-02` to `MG-CS-09`)
3. contract status: still open until all 12 mandatory cases are executed and recorded

## Closure Rule

Manual evidence can be marked green only when:

1. all 12 MG-CS cases are executed under the protocol above
2. all 12 meet expected outcomes
3. screenshots and notes are attached for every case
4. no contract-boundary drift is observed
