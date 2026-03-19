# Phase 4 Incident Record

Date: 2026-03-19  
Owner: AI Runtime Engineering  
Scope: standing browser smoke failure on product ranking projection pack  
Status: closed

## Incident Header

- Incident ID: `INC-P4-001`
- Date Opened: `2026-03-19`
- Severity: `P2`
- Risk Tier: `Tier 2`
- Owner: `AI Runtime Engineering`
- Status: `Closed`

## User-Visible Symptom

- User prompt or flow:
  - `Top 10 products by sold quantity last month`
  - `with Item Name`
  - `Give me Item Name and Sold Qty only`
  - `Give me Item Name Only`
- Browser/replay environment:
  - browser/manual standing smoke refresh, Phase 4
- What the user saw:
  - projection follow-up changed row authority by merging duplicate item names and aggregating sold quantity
  - example: `Type-C Cable 1m Fast Charge` became `614.00` instead of preserving the active ranked rows from the prior result
- Expected behavior:
  - projection follow-up should restrict visible columns only
  - it should not regroup or aggregate the active ranked result

## Classification

- Behavioral class: `detail_projection`
- Primary incident family:
  - `projection/shaping failure`

## Root Cause

- Root-cause summary:
  - confirmed in `response_shaper._apply_top_n()`
  - projection-only top-N follow-ups were still passing through dimension-level aggregation
  - when the visible projected dimension contained duplicate values such as `Item Name`, rows were incorrectly regrouped and metric values were summed
- Violated class invariant:
  - restrictive projection must preserve active-result row authority
- Shared surfaces impacted:
  - `response_shaper`
  - `browser/runtime parity`

## Fix Record

- Fix summary:
  - top-N shaping now skips regrouping when the request is a projection-only follow-up
  - this preserves the ranked active rows and only narrows visible columns
- Files changed:
  - [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
  - [test_v7_response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_response_shaper.py)
- Why the fix stays inside contract boundary:
  - remediation preserves active-result row authority
  - no prompt-specific hack or keyword override was introduced
  - fix is scoped to shaper behavior for projection-only top-N follow-ups

## Regression Assets Added

- Unit/module regression:
  - `test_projection_only_top_n_preserves_row_authority_without_regrouping_duplicates`
- Replay evidence:
  - standing replay remains green; this incident was primarily browser/manual parity driven
  - browser drift was prevented from closing silently because the Phase 4 standing pack caught it
- Browser/manual evidence:
  - [step39_phase4_standing_browser_smoke_refresh_results_2026-03-19.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step39_phase4_standing_browser_smoke_refresh_results_2026-03-19.md)
- Variation-matrix row updated:
  - not yet

## Reruns Performed

- Targeted reruns:
  - `python3 -m unittest impl_factory.04_automation.bench_scripts.test_v7_response_shaper`
  - `python3 -m unittest impl_factory.04_automation.bench_scripts.test_v7_transform_last`
- Shared-surface reruns:
  - focused browser rerun of Pack B
- Browser/manual reruns:
  - fresh rerun of:
    - `Top 10 products by sold quantity last month`
    - `with Item Name`
    - `Give me Item Name and Sold Qty only`
    - `Give me Item Name Only`
- Release gate rerun required: `No`

## Evidence Links

- Raw replay log(s):
  - not required for closure because the defect was browser-visible and fixed under the standing smoke control path
- Browser/manual screenshots or notes:
  - captured in [step39_phase4_standing_browser_smoke_refresh_results_2026-03-19.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step39_phase4_standing_browser_smoke_refresh_results_2026-03-19.md)
- Release gate output, if applicable:
  - not applicable

## Closure Decision

- Closure date:
  - `2026-03-19`
- Closed by:
  - `AI Runtime Engineering`
- Why this incident is considered closed:
  - root cause confirmed
  - bounded fix applied inside contract boundary
  - focused regressions passed
  - fresh browser rerun confirmed row authority is preserved
- Residual risk, if any:
  - no active blocker remains for this incident
  - broader projection/replay hardening can still be improved later, but this specific user-visible defect is resolved

## Notes

- Follow-up governance action:
  - keep this incident as the first completed live Phase 4 incident-handling example
- Future class/metadata/ontology update needed:
  - not required for incident closure
