# Phase 2 Canary UAT Evidence (Matrix-Aligned)

Date: 2026-02-18
Executed at (UTC): 2026-02-18T17:59:08Z
Site: `erpai_prj1`
User: `Administrator`
Mode: Phase 2 canary with read orchestrator flag ON (in-run).

## Run Control
1. Orchestrator flag forced ON during run: `ai_assistant_orchestrator_v2_enabled=1`.
2. Write flag default OFF; toggled ON only for WR-02/03/04; restored after run.
3. Temporary sessions and ToDo records were cleaned up at run end.

## Preconditions
1. `report_list`: PASS (count=218)
2. `report_requirements`: PASS
3. `generate_report` probe: PASS

## Summary
1. Total scenarios: 23
2. Passed: 15
3. Failed: 8
4. Clarification rate on clear set: 0.75 (9/12)
5. Meta-clarification count on clear set: 3

## Release Gate (From Matrix Criteria)
1. Mandatory scenarios pass 100%: FAIL
2. Critical clear-query scenarios pass 100%: FAIL
3. Clarification rate <= 10% on clear set: FAIL
4. Zero meta-clarification on clear set: FAIL
5. Overall GO/NO-GO: NO-GO

## Scenario Matrix Evidence
| ID | Prompt Used | Expected | Actual | Pass/Fail | Evidence | Defect ID |
|---|---|---|---|---|---|---|
| FIN-01 | Show accounts receivable as of today | Returns FAC-backed result directly; no clarification for clear ask. | type=report_table, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (FIN-01) |  |
| FIN-03 | Total outstanding amount | Uses transform_last only and returns total in same turn. | type=report_table, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (FIN-03) |  |
| FIN-04 | Sort that by outstanding amount descending | Deterministic sort transform on last-result rows in same turn. | type=report_table, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (FIN-04) |  |
| FIN-02 | Show accounts receivable last month | Returns date-scoped FAC result directly when report supports it; otherwise one concrete constraint mismatch question. | type=text, pending=planner_clarify, downloads=0, text=Please specify one concrete metric or grouping so I can return the correct result. | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (FIN-02) |  |
| SAL-01 | Top 5 customers by revenue in last month | Returns top-5 customer ranking table (customer + revenue), sorted desc, no clarification loop. | type=text, pending=planner_clarify, downloads=0, text=Which metric column should I use from **Sales Analytics**? Options: Jan 2026, Total. | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (SAL-01) |  |
| SAL-02 | Show sales by item and download excel | Export only because explicitly requested. | type=text, pending=planner_clarify, downloads=0, text=Which metric column should I use from **Sales Analytics**? Options: Apr 2025, May 2025, Jun 2025, Jul 2025, Aug 2025,... | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (SAL-02) |  |
| STK-01 | Show stock balance in Returns and Damaged - MMOB | Warehouse constraint enforced; returns result directly when unambiguous. | type=text, pending=planner_clarify, downloads=0, text=Which specific warehouse should I use for the stock balance? | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (STK-01) |  |
| STK-02 | Show stock balance in the same warehouse | Reuses follow-up context and returns result without re-asking same filter. | type=text, pending=planner_clarify, downloads=0, text=I can group by **Warehouse** from **Warehouse Wise Stock Balance**. Should I proceed? | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (STK-02) |  |
| HR-01 | Which employee has attendance issues this month? | Returns report-based response directly for clear ask (or one concrete required-input clarification). | type=text, pending=planner_clarify, downloads=0, text=Please specify one concrete metric or grouping so I can return the correct result. | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (HR-01) |  |
| OPS-01 | What are the open material requests for production | Planner selects report path; response from FAC only. | type=text, pending=planner_clarify, downloads=0, text=Please specify one concrete metric or grouping so I can return the correct result. | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (OPS-01) |  |
| CFG-01 | Show the report | Asks exactly one clarification question. | type=text, pending=planner_clarify, downloads=0, text=Which specific report would you like to see? | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (CFG-01) |  |
| CFG-02 | Show open material requests for production | Pending flow is canceled and new topic starts. | type=report_table, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (CFG-02) |  |
| CFG-03 | Top 5 customers by revenue in last month | Must not ask abstract planner-preference questions. | type=text, pending=planner_clarify, downloads=0, text=Which metric column should I use from **Sales Analytics**? Options: Jan 2026, Total. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (CFG-03) |  |
| ENT-01 | Show stock balance in ZZZ-NO-MATCH-33NLDH | Asks refine question; does not guess names. | type=text, pending=planner_clarify, downloads=0, text=Which warehouse should I use for the stock balance? | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (ENT-01) |  |
| ENT-02 | Show stock balance in mmob | Presents options and asks to choose one. | type=text, pending=planner_clarify, downloads=0, text=Which warehouse should I use? | FAIL | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (ENT-02) | UAT-ENT-02-001 |
| WR-01 | Create a ToDo for follow-up | Returns write-disabled message; no write execution. | type=text, pending=None, downloads=0, text=Write-actions are disabled in this environment. Please ask an administrator to enable them. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (WR-01) |  |
| WR-02 | Delete ToDo ql9ucnn8l1 | Requires explicit confirmation before execution. | type=text, pending=write_confirmation, downloads=0, text=Are you sure you want to delete the ToDo with ID ql9ucnn8l1? Reply **confirm** to execute or **cancel** to stop. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (WR-02) |  |
| WR-03 | cancel | Cancels write and clears pending state. | type=text, pending=None, downloads=0, text=Write action canceled. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (WR-03) |  |
| WR-04 | Delete ToDo qma34eghq6 -> confirm | Executes exactly one draft action and returns safe result text. | type=text, pending=None, downloads=0, text=Confirmed. Deleted **ToDo** `qma34eghq6`. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (WR-04) |  |
| OBS-01 | get_messages(debug=0) | No tool/internal messages in normal user view. | type=observe, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (OBS-01) |  |
| OBS-02 | get_messages(debug=1) | Debug view includes audit_turn tool messages. | type=observe, pending=None, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (OBS-02) |  |
| ERR-01 | Show stock balance | User gets safe error text; no stacktrace/internal exception leakage. | type=error, pending=None, downloads=0, text=I couldn’t process that request right now. Please try again. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (ERR-01) |  |
| EXP-01 | Show sales by item for this month | No export artifacts unless explicit request. | type=text, pending=planner_clarify, downloads=0, text=Which metric column should I use from **Sales Analytics**? Options: Feb 2026, Total. | PASS | `impl_factory/04_automation/logs/20260218T174716Z_phase2_canary_uat_raw.json` (EXP-01) |  |

## Failures Requiring Fix/Rerun
1. `FIN-02` -> `UAT-FIN-02-001`: Please specify one concrete metric or grouping so I can return the correct result.
2. `SAL-01` -> `UAT-SAL-01-001`: Which metric column should I use from **Sales Analytics**? Options: Jan 2026, Total.
3. `SAL-02` -> `UAT-SAL-02-001`: Which metric column should I use from **Sales Analytics**? Options: Apr 2025, May 2025, Jun 2025, Jul 2025, Aug 2025, Sep 2025.
4. `STK-02` -> `UAT-STK-02-001`: I can group by **Warehouse** from **Warehouse Wise Stock Balance**. Should I proceed?
5. `HR-01` -> `UAT-HR-01-001`: Please specify one concrete metric or grouping so I can return the correct result.
6. `OPS-01` -> `UAT-OPS-01-001`: Please specify one concrete metric or grouping so I can return the correct result.
7. `ENT-01` -> `UAT-ENT-01-001`: Which warehouse should I use for the stock balance?
8. `ENT-02` -> `UAT-ENT-02-001`: Which warehouse should I use?

## Failed-8 Controlled Rerun (Post-Fix)
Date: 2026-02-18  
Artifact: `impl_factory/04_automation/logs/20260218T183205Z_phase2_failed8_rerun_v3_raw.json`

1. Scope: reran previously failed subset (`FIN-02`, `SAL-01`, `SAL-02`, `STK-02`, `HR-01`, `OPS-01`, `ENT-01`, `ENT-02`) with orchestrator flow active.
2. Result: `8/8 PASS`.
3. Notes:
- `ENT-01` now returns explicit no-match refine prompt.
- `ENT-02` now returns explicit ambiguity options prompt.
- `STK-02` passes when seeded with a concrete prior warehouse result in-session (documented in raw artifact note).

## Full Rerun v2 (2026-02-18)
Artifact: `impl_factory/04_automation/logs/20260218T185747Z_phase2_canary_uat_raw_v2.json`

1. Summary: `23 total`, `21 pass`, `2 fail`.
2. Release gate: `NO-GO` (mandatory 100% not met).
3. Passed gates in rerun:
- Critical clear-query scenarios: PASS
- Clarification rate on clear set <=10%: PASS (`0/12`)
- Zero meta-clarification on clear set: PASS
4. Full-run failing cases:
- `ENT-01` (`UAT-ENT-01-001`): no-match warehouse ask routed to unrelated item clarification.
- `ERR-01` (`UAT-ERR-01-001`): harness-level capture issue in full run.
5. Corrected ERR-01 retest artifact: `impl_factory/04_automation/logs/20260218T190359Z_phase2_err01_retest_raw.json` (PASS).
6. Effective remaining blocker after corrected retest: `ENT-01`.

## Full Rerun v3 Fresh (2026-02-18)
Artifact: `impl_factory/04_automation/logs/20260218T193146Z_phase2_canary_uat_raw_v3.json`

1. Summary: `23 total`, `23 pass`, `0 fail`.
2. Release gate: `GO`.
3. Gate detail:
- Mandatory scenarios pass 100%: PASS
- Critical clear-query scenarios pass 100%: PASS
- Clarification rate on clear set <=10%: PASS (`0/12`)
- Zero meta-clarification on clear set: PASS (`0`)
4. Scenario-level outcome: all matrix IDs from `FIN-01` through `EXP-01` passed in this fresh full run.
5. Note: run preconditions in artifact show `report_requirements_ok=false` for probe call while all executed scenarios still passed; keep this as a non-blocking harness observation for follow-up hardening.

## Phase 3 Validation Rerun (2026-02-19)
Artifacts:
1. Regression summary: `impl_factory/04_automation/logs/20260219T040812Z_step11_regression_summary.md`
2. Full canary raw: `impl_factory/04_automation/logs/20260219T041812Z_phase2_canary_uat_raw_v3.json`

1. Scope: post-implementation validation after iterative orchestrator terminal-action hardening (`respond/clarify/safe_error`) and additional loop tests.
2. Regression result: PASS (`56` tests).
3. Canary summary: `23 total`, `23 pass`, `0 fail`.
4. Release gate: `GO`.
5. Gate detail:
- Mandatory scenarios pass 100%: PASS
- Critical clear-query scenarios pass 100%: PASS
- Clarification rate on clear set <=10%: PASS (`0/12`)
- Zero meta-clarification on clear set: PASS (`0`)

## Phase 4 Validation Rerun (2026-02-19)
Artifacts:
1. Regression summary: `impl_factory/04_automation/logs/20260219T042528Z_step11_regression_summary.md`
2. Full canary raw: `impl_factory/04_automation/logs/20260219T043518Z_phase2_canary_uat_raw_v3.json`

1. Scope: post-implementation validation for clarification-policy hardening and deterministic semantic alias mapping.
2. Regression result: PASS (`60` tests).
3. Canary summary: `23 total`, `23 pass`, `0 fail`.
4. Release gate: `GO`.
5. Gate detail:
- Mandatory scenarios pass 100%: PASS
- Critical clear-query scenarios pass 100%: PASS
- Clarification rate on clear set <=10%: PASS (`0/12`)
- Zero meta-clarification on clear set: PASS (`0`)

## Phase 5 Validation Update (2026-02-19)
Artifacts:
1. Regression summary: `impl_factory/04_automation/logs/20260219T045608Z_step11_regression_summary.md`
2. Canary reference baseline: `impl_factory/04_automation/logs/20260219T043518Z_phase2_canary_uat_raw_v3.json`

1. Scope: post-hardening contract regression verification for repair-first and actionable-clarification behavior.
2. Regression result: PASS (`60` tests).
3. Canary status: latest valid full canary remains `23 total`, `23 pass`, `0 fail` from the referenced baseline artifact.
4. Release gate status (reference canary):
- Mandatory scenarios pass 100%: PASS
- Critical clear-query scenarios pass 100%: PASS
- Clarification rate on clear set <=10%: PASS (`0/12`)
- Zero meta-clarification on clear set: PASS (`0`)
