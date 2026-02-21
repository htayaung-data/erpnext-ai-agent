# Step 11 UAT Scenario Matrix (v3.0 Alignment)

Date: 2026-02-19  
Owner: Director + AI Operator + QA Lead  
System Under Test: `ai_assistant_ui` on site `erpai_prj1`  
Contract Baseline: `AI Assistant Contract Specification (Commercial v3.0)`

## Preconditions
1. FAC connectivity is healthy (`report_list`, `report_requirements`, `generate_report`).
2. `ai_assistant_ui` is installed and migrated on target site.
3. Engine mode under test is explicit (`assistant_engine=v2|v3_shadow|v3_active`).
4. Test users exist and are used in-run:
   - read-only (`ai.reader`)
   - operator (`ai.operator`)
   - admin (`Administrator`) for controlled write/error injection only
5. Write capability flag state is known before write scenarios.
6. Debug mode is OFF for user validation (`get_messages(debug=0)`), ON only for audit checks.
7. Dataset snapshot/version is recorded before run (so semantic expectations are reproducible).

## Evaluation Policy (v3 Hard Rules)
1. Release gate scoring uses first-run results only.
2. Diagnostic reruns are allowed for debugging evidence only; they do not convert a failed gate case to pass.
3. A scenario is `PASS` only if all required semantic assertions pass.
4. Any clarification on clear business asks is `FAIL` unless a true blocker exists:
   - missing required FAC filter not safely inferable
   - entity ambiguity/no-match requiring user choice
   - unsupported FAC capability with explicit mismatch message
5. Meta-clarifications are always `FAIL` on clear asks.
6. Clarification loop/repetition for same blocker is always `FAIL`.
7. "Table returned" alone is never sufficient for `PASS`.

## Mandatory Scenarios

| ID | Domain | User Prompt | Expected Behavior | Required Semantic Assertions |
|---|---|---|---|---|
| FIN-01 | Finance | `Show accounts receivable as of today` | Direct FAC-backed result in same turn. | correct report family; date scope applied; receivable metric alignment; no unnecessary clarification |
| FIN-02 | Finance | `Show accounts receivable last month` | Direct date-range result when supported, else one concrete capability mismatch question. | date-range semantics correct; mismatch explanation concrete if blocked |
| FIN-03 | Finance | `Total outstanding amount` (after FIN-01) | Deterministic transform on last result. | transform_last provenance; metric column correctness; no report re-run unless required |
| FIN-04 | Finance | `Sort that by outstanding amount descending` | Deterministic sort transform in same turn. | sort column correctness; descending order correctness |
| SAL-01 | Sales | `Top 5 customers by revenue in last month` | Returns top-5 customer ranking, sorted desc, no loop. | dimension=customer; metric=revenue/value; top_n=5; date scope=last month |
| SAL-02 | Sales | `Show sales by item and download excel` | Export only because explicitly requested. | dimension=item alignment; export artifacts present; no implicit clarification |
| STK-01 | Stock | `Show stock balance in Main warehouse` | Warehouse-constrained stock response in same turn when unambiguous. | warehouse filter applied; stock metric context correct |
| STK-02 | Stock | `Show stock balance in the same warehouse` (after STK-01) | Reuses prior warehouse without re-asking same filter. | follow-up context reuse; no redundant clarification |
| HR-01 | HR | `Which employee has attendance issues this month?` | Direct response or one concrete blocker only. | domain/subject alignment=employee attendance; month scope honored |
| OPS-01 | Operations | `What are the open material requests for production` | Planner chooses compatible report path; FAC-backed response. | subject=open material requests; operational status semantics |
| COR-01 | Correction turn | `I mean sold qty, not received qty` (after received-qty output) | Reroutes semantics correctly without topic contamination. | metric polarity corrected; same topic preserved |
| DET-01 | Detail ask | `Show only customer and revenue columns` | Returns requested minimal columns only. | output columns exactly match requested business columns |
| DOC-01 | Detail retrieval | `Show details for Sales Invoice SINV-0001` | Returns document/detail response, not generic summary. | specific document targeting; no unrelated aggregation |
| CFG-01 | Clarify discipline | `Show the report` | Exactly one clarification question. | single question only; no loop |
| CFG-02 | Topic switch | While pending clarify, send unrelated request | Pending flow canceled; new topic executed. | pending canceled; no stale filter carryover |
| CFG-03 | No meta-clarify | `Top 5 customers by revenue in last month` | Must not ask abstract planner-preference question. | no meta-clarification markers |
| ENT-01 | Entity no match | Use non-existing warehouse/company | Asks refine question; no guessing. | no guessed entity; blocker-specific prompt |
| ENT-02 | Entity ambiguous | Use ambiguous link value | Presents options and asks to choose one. | options >= 2; pending mode correct |
| WR-01 | Write disabled | `Create a ToDo for follow-up` (write flag OFF) | Returns write-disabled message; no execution. | write never executed |
| WR-02 | Write confirmation | `Delete ToDo TODO-0001` (write flag ON) | Requires explicit confirmation before execution. | pending mode=write_confirmation |
| WR-03 | Write cancel | After WR-02 pending, reply `cancel` | Cancels write and clears pending state. | no write side effect |
| WR-04 | Write confirm | After WR-02 pending, reply `confirm` | Executes exactly one draft action and returns safe result text. | single execution; idempotent behavior |
| OBS-01 | Hidden internals | Regular chat fetch (`debug=0`) | No internal tool/audit payload visible. | no tool-role leakage in public view |
| OBS-02 | Debug trace | Chat fetch with `debug=1` | Internal tool messages include audit envelope. | audit turn present |
| ERR-01 | Safe failures | Force tool/runtime failure | User gets safe error text only. | no traceback/internal exception leakage |
| EXP-01 | No implicit export | Ask report without download words | No export artifact unless explicitly requested. | downloads count = 0 |

## Required Semantic Assertion Fields per Scenario
For each scenario, evaluator must record:
1. `report_alignment_pass`
2. `dimension_alignment_pass`
3. `metric_alignment_pass`
4. `time_scope_alignment_pass`
5. `filter_alignment_pass`
6. `output_shape_pass`
7. `clarification_policy_pass`
8. `loop_policy_pass`

A scenario fails if any required field is false.

## Release Pass Criteria (v3)
1. Mandatory scenario pass rate (first-run): 100%.
2. Critical clear-query scenarios (`FIN-01`, `FIN-03`, `FIN-04`, `SAL-01`, `CFG-03`, `COR-01`) pass rate: 100%.
3. Direct-answer rate on clear read benchmark: >= 90%.
4. Unnecessary clarification rate on clear read benchmark: <= 5%.
5. Clarification loop rate: < 1%.
6. Wrong-report rate on benchmark/replay: <= 3%.
7. Zero meta-clarification prompts on clear business asks.
8. Role-based run parity: no critical regression between `ai.reader` and `ai.operator`.
9. Any failed scenario must include defect ID and root-cause classification.
10. Regression script and semantic contract tests both must pass.
