# M0 Step 5 - Deterministic Constraints + Entity Disambiguation

Date: 2026-02-18  
Status: Completed

## Objective
Implement Step 5 as a quality-first vertical slice:
1. deterministic hard-constraint validation for warehouse/date/company
2. entity disambiguation enforcement (Link/MultiSelect)
3. regression tests covering these behaviors

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added deterministic constraint detection + validation helpers:
     - detects user-required `warehouse`, `company`, `date`, and `date_range`
     - blocks report execution when selected report cannot support required constraints
     - asks one next-step question and stores pending state (`planner_clarify`)
   - Added enforcement for missing hard-constraint values even when fields are optional:
     - asks one filter question (`need_filters`) for warehouse/company/date when required by user request but not yet provided.
   - Integrated constraint validation into `report_qa_start` before report execution.
   - Strengthened entity resolution:
     - `_resolve_link_value()` now returns explicit status: `exact | ambiguous | no_match`
     - ambiguous values force one-choice clarification
     - no-match values force user refinement (no guessing/fallback pass-through)
   - Added MultiSelect Link disambiguation path (split/resolve/serialize).
   - Added pending-option enforcement in `report_qa_continue`:
     - user must choose from provided options (name, number, or unique contains)
     - invalid choice keeps pending and asks again with indexed options.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 5 regression tests:
     - unsupported warehouse constraint is blocked
     - unsupported date-range constraint is blocked
     - ambiguous link value prompts disambiguation
     - no-match link value prompts refine
     - pending option selection is enforced before execution

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Regression tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 9 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. No deletion of `.bak` or other candidate dead files in this step.
3. This step intentionally focuses on deterministic safety enforcement and test evidence; broader conversation-quality iteration continues in the next step after confirmation.
