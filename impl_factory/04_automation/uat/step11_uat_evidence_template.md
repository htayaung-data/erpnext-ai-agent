# Step 11 UAT Evidence Template (v3.0)

Date: YYYY-MM-DDTHH:MM:SSZ  
Executed by: <name/automation user>  
Environment: <runtime details>  
Site: `<site_name>`  
Build/Commit: `<git_sha>`  
Engine Mode: `assistant_engine=<v2|v3_shadow|v3_active>`  
Write Capability Flag: `<state transitions>`  
Dataset Snapshot ID: `<snapshot/version>`

## Run Policy Declaration
1. Gate scoring is based on first-run results only.
2. Any reruns are diagnostic and must be documented separately.
3. No rerun may overwrite original pass/fail for release gates.

## Regression Pack Attachment
1. Runner command:
   - `<command>`
2. Compile/Test artifacts:
   - `<compile_log_path>`
   - `<contract_test_log_path>`
   - `<semantic_test_log_path>`
3. Result:
   - `PASS/FAIL` with test counts

## UAT Runner Attachment
1. Runner command:
   - `<command>`
2. Raw first-run artifact:
   - `<raw_json_path>`
3. Optional diagnostic rerun artifact(s):
   - `<rerun_json_path_or_none>`

## Preconditions Check
1. FAC connectivity:
   - `report_list`: PASS/FAIL (+ count)
   - `report_requirements`: PASS/FAIL
   - `generate_report`: PASS/FAIL
2. Role profiles available:
   - `ai.reader`: PASS/FAIL
   - `ai.operator`: PASS/FAIL
3. Debug visibility behavior sanity:
   - `debug=0` hidden internals: PASS/FAIL
   - `debug=1` audit visibility: PASS/FAIL

## Scenario Evidence (First-Run Only)

| ID | User/Role | Prompt Used | Expected | Actual (Type/Text/Rows/Downloads/Pending) | Semantic Assertions (R/D/M/T/F/O/C/L) | Pass/Fail | Defect ID (if fail) | Evidence Ref |
|---|---|---|---|---|---|---|---|---|
| FIN-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| FIN-02 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| FIN-03 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| FIN-04 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| SAL-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| SAL-02 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| STK-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| STK-02 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| HR-01 | ai.operator |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| OPS-01 | ai.operator |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| COR-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| DET-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| DOC-01 | ai.operator |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| CFG-01 | ai.reader |  |  |  | `R=?, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| CFG-02 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| CFG-03 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |
| ENT-01 | ai.reader |  |  |  | `R=?, D=NA, M=NA, T=NA, F=?, O=?, C=?, L=?` |  |  |  |
| ENT-02 | ai.reader |  |  |  | `R=?, D=NA, M=NA, T=NA, F=?, O=?, C=?, L=?` |  |  |  |
| WR-01 | ai.operator |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| WR-02 | ai.operator |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| WR-03 | ai.operator |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| WR-04 | ai.operator |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| OBS-01 | ai.reader |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| OBS-02 | ai.reader |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| ERR-01 | ai.reader |  |  |  | `R=NA, D=NA, M=NA, T=NA, F=NA, O=?, C=?, L=?` |  |  |  |
| EXP-01 | ai.reader |  |  |  | `R=?, D=?, M=?, T=?, F=?, O=?, C=?, L=?` |  |  |  |

Legend:
- `R`=report alignment
- `D`=dimension alignment
- `M`=metric alignment
- `T`=time scope alignment
- `F`=filter alignment
- `O`=output shape alignment
- `C`=clarification policy compliance
- `L`=loop policy compliance

## Aggregate KPI Summary (First-Run)
1. Total scenarios: `<n>`
2. Passed: `<n>`
3. Failed: `<n>`
4. Direct-answer rate on clear benchmark: `<value>`
5. Unnecessary clarification rate on clear benchmark: `<value>`
6. Wrong-report rate: `<value>`
7. Clarification loop rate: `<value>`
8. Meta-clarification count (clear asks): `<value>`
9. User correction rate (if replay included): `<value>`
10. p50/p95 latency: `<value>/<value>`

## Release Gate Decision
1. Mandatory scenarios pass 100%: PASS/FAIL
2. Critical clear-query scenarios pass 100%: PASS/FAIL
3. Direct-answer rate >= 90%: PASS/FAIL
4. Clarification rate <= 10%: PASS/FAIL
5. Unnecessary clarification rate <= 5%: PASS/FAIL
6. Wrong-report rate <= 3%: PASS/FAIL
7. Clarification loop rate < 1%: PASS/FAIL
8. Zero meta-clarification on clear asks: PASS/FAIL
9. Role parity check (`ai.reader` vs `ai.operator`): PASS/FAIL
10. Output-shape pass rate = 100% on clear benchmark: PASS/FAIL
11. Write safety incidents = 0: PASS/FAIL
12. Overall GO: `True/False`

## Phase 8 Canary Promotion Decision
1. Current stage: `<10|25|50|100>%`
2. Gate artifact:
   - `<*_phase8_release_gate_stage*.json>`
3. Decision:
   - `promote_to_next_stage / hold_100pct_monitor / rollback_to_v2`
4. Failed gate check IDs (if any):
   - `<list>`
5. Rollback rehearsal evidence:
   - `<command + log path>`
6. Shadow diff artifact:
   - `<*_phase8_shadow_diff.json>`

## Diagnostic Rerun Log (Non-Gating)
Use this section only for debugging after first-run scoring is frozen.

| Scenario ID | Why rerun was needed | Rerun outcome | Root cause found | Fix candidate |
|---|---|---|---|---|
|  |  |  |  |  |

## Defect Summary
| Defect ID | Scenario ID | Severity | Category (intent/report/metric/dimension/time/filter/clarification/loop/write/security/observability) | Description | Owner | ETA |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Sign-Off
1. QA Lead sign-off: ____________________ (date/time)
2. AI Operator sign-off: ____________________ (date/time)
3. Engineering Lead sign-off: ____________________ (date/time)
4. Director sign-off: ____________________ (date/time)
5. Decision: GO / NO-GO
