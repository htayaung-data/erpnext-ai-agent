# M0 Step 3 - Contract Alignment Refactor Log

Date: 2026-02-18  
Status: Completed (code refactor + runtime smoke checks)

## Objective
Align assistant runtime behavior with the new commercial contract:
1. reduce hardcoded/regex routing in active chat flow
2. move intent decisions toward planner + few-shot
3. enforce pending topic-switch behavior (ChatGPT-style)

## Files Updated
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/report_planner.py`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/service.py`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/router.py`

## Refactor Summary
1. Planner schema upgraded:
   - Added optional `export` flag in validated plan output.
   - Added planner guidance: export only when user explicitly requests file output.
   - Expanded few-shot examples with export scenario.

2. Pending-flow topic switching:
   - Added `choose_pending_mode()` in planner layer.
   - `service.py` now decides between `report_qa_continue` vs fresh `report_qa_start` while pending.
   - If pending is overridden by a new topic, service writes a pending-clear tool message before applying new state.

3. Removed regex/keyword routing from active chat orchestration:
   - Removed `_EXPORT_HINT` regex usage from `report_qa.py`.
   - Removed regex-based question-token scoring for candidate report selection.
   - Introduced diversified candidate selection without question keyword matching.
   - `chat/router.py` export helper now returns `False` (planner-driven export only).

4. Pending state now preserves export intent:
   - `export_requested` is stored in pending states and reused on continuation.

## Verification Evidence
1. Runtime import checks:
   - Backend imports of refactored modules succeeded via bench env python.

2. API smoke sequence:
   - create session -> `chat_send` -> `get_messages` -> delete session succeeded.
   - `chat_send` returned `{"ok": true}` in live runtime.

3. Topic-switch smoke sequence:
   - Session executed two different questions sequentially.
   - Tool trace showed fresh `report_qa_start` execution on second question, not a forced continue of prior context.

4. Service stability:
   - backend/websocket/queue-short/queue-long/scheduler remained up after refactor.

## Notes
1. This step did not delete `.bak` files yet (deferred until safe dependency sweep and explicit cleanup step).
2. Legacy modules outside the active chat path still contain regex helpers (e.g. date parsing utilities); this step focused on the active report-QA orchestration path.
