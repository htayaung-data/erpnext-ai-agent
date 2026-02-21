# Step 11 UAT Evidence - Phase 6 Controlled Canary (2026-02-19)

Date: 2026-02-19T08:52:31Z
Executed by: Codex automation run (service user: `Administrator`)
Environment: Docker Compose backend, bench runtime (`erpai_prj1`)
Mode: Phase 6 controlled canary, strict matrix, orchestrator flag ON in-run

## Canary Runner
1. Command:
   - `python3 -u impl_factory/04_automation/bench_scripts/run_phase6_canary_uat.py`
2. Raw artifact:
   - `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json`

## Preconditions
1. `report_list`: PASS (count=219)
2. `report_requirements`: PASS (validated against `Accounts Receivable Summary` after run)
3. `generate_report`: PASS
4. Note: raw canary payload precheck for `report_requirements` used `Accounts Receivable` and returned a false negative due report-name mismatch in this environment.

## Flags During Run
1. `ai_assistant_orchestrator_v2_enabled`: 1 (before=1)
2. `ai_assistant_write_enabled`: default=0, write-phase=1 (before=1)

## Regression Pack
1. Runner command:
   - `bash impl_factory/04_automation/bench_scripts/run_step11_regression.sh`
2. Summary artifact:
   - `impl_factory/04_automation/logs/20260219T085238Z_step11_regression_summary.md`
3. Result: PASS

## Release Gate
1. Mandatory scenarios pass 100%: `True`
2. Critical clear-query pass 100%: `True`
3. Clarification rate on clear set <= 10%: `True` (rate=0.0)
4. Zero meta-clarification on clear set: `True`
5. Overall GO: `True`

## Scenario Evidence

| ID | Prompt | Expected | Actual | Pass/Fail | Evidence |
|---|---|---|---|---|---|
| FIN-01 | Show accounts receivable as of today | Returns FAC-backed result directly; no clarification for clear ask. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (FIN-01) |
| FIN-03 | Total outstanding amount | Uses transform_last only and returns total in same turn. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (FIN-03) |
| FIN-04 | Sort that by outstanding amount descending | Deterministic sort transform on last-result rows in same turn. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (FIN-04) |
| FIN-02 | Show accounts receivable last month | Returns date-scoped FAC result directly when report supports it; otherwise one concrete constraint mismatch question. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (FIN-02) |
| SAL-01 | Top 5 customers by revenue in last month | Returns top-5 customer ranking table (customer + revenue), sorted desc, no clarification loop. | type=report_table, pending=None, rows=5, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (SAL-01) |
| SAL-02 | Show sales by item and download excel | Export only because explicitly requested. | type=report_table, pending=None, rows=16, downloads=2, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (SAL-02) |
| STK-01 | Show stock balance in Main warehouse | Warehouse constraint enforced; returns result directly when unambiguous. | type=report_table, pending=None, rows=10, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (STK-01) |
| STK-02 | Show stock balance in the same warehouse | Reuses follow-up context and returns result without re-asking same filter. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (STK-02) |
| HR-01 | Which employee has attendance issues this month? | Returns report-based response directly for clear ask (or one concrete required-input clarification). | type=report_table, pending=None, rows=0, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (HR-01) |
| OPS-01 | What are the open material requests for production | Planner selects report path; response from FAC only. | type=report_table, pending=None, rows=0, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (OPS-01) |
| CFG-01 | Show the report | Asks exactly one clarification question. | type=text, pending=planner_clarify, rows=0, downloads=0, text=Which specific report would you like to see? | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (CFG-01) |
| CFG-02 | Show open material requests for production | Pending flow is canceled and new topic starts. | type=report_table, pending=None, rows=0, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (CFG-02) |
| CFG-03 | Top 5 customers by revenue in last month | Must not ask abstract planner-preference questions (metric vs grouping vs period). | type=report_table, pending=None, rows=5, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (CFG-03) |
| ENT-01 | Show stock balance in warehouse ZZZ-NO-MATCH-999999 | Asks refine question; does not guess names. | type=text, pending=need_filters, rows=0, downloads=0, text=I couldn’t find any **Warehouse** matching "warehouse ZZZ-NO-MATCH-999999". Which exact value should I use? | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (ENT-01) |
| ENT-02 | Show stock balance in warehouse mmob | Presents options and asks to choose one. | type=text, pending=need_filters, rows=0, downloads=0, text=I found multiple matches for **Warehouse** matching "mmob": Returns and Damaged - MMOB, Transit Warehouse - MMOB, Man... | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (ENT-02) |
| WR-01 | Create a ToDo for follow-up | Returns write-disabled message; no write execution. | type=text, pending=None, rows=0, downloads=0, text=Write-actions are disabled in this environment. Please ask an administrator to enable them. | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (WR-01) |
| WR-02 | Delete ToDo 4h1f2th092 | Requires explicit confirmation before execution. | type=text, pending=write_confirmation, rows=0, downloads=0, text=Delete ToDo with ID 4h1f2th092? Reply **confirm** to execute or **cancel** to stop. | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (WR-02) |
| WR-03 | cancel | Cancels write and clears pending state. | type=text, pending=None, rows=0, downloads=0, text=Write action canceled. | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (WR-03) |
| WR-04 | Delete ToDo 4vsje5djgs -> confirm | Executes exactly one draft action and returns safe result text. | type=text, pending=None, rows=0, downloads=0, text=Confirmed. Deleted **ToDo** `4vsje5djgs`. | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (WR-04) |
| OBS-01 | get_messages(debug=0) | No tool/internal messages in normal user view. | type=observe, pending=None, rows=0, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (OBS-01) |
| OBS-02 | get_messages(debug=1) | Debug view includes audit_turn tool messages. | type=observe, pending=None, rows=0, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (OBS-02) |
| ERR-01 | Show stock balance | User gets safe error text; no stacktrace/internal exception leakage. | type=error, pending=None, rows=0, downloads=0, text=I couldn’t process that request right now. Please try again. | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (ERR-01) |
| EXP-01 | Show sales by item for this month | No export artifacts unless explicit request. | type=report_table, pending=None, rows=1, downloads=0, text= | PASS | `impl_factory/04_automation/logs/20260219T085231Z_phase6_canary_uat_raw_v1.json` (EXP-01) |

## Summary
1. Total: `23`, Pass: `23`, Fail: `0`
2. Clarification count on clear set: `0/12`
3. Meta clarification count on clear set: `0`

## Sign-Off
1. AI Operator sign-off: ____________________ (date/time)
2. Director sign-off: ____________________ (date/time)
3. Decision: GO / NO-GO
