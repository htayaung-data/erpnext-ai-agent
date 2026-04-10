# Qwen Chat Service Refactor Checkpoint

Status: checkpoint reached after controlled Phase 2 extraction wave  
Date: 2026-03-30  
Audience: maintainers working on `qwen_chat`

## 1. Current Position

The refactor wave has reached the planned stopping zone.

Current state:

1. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py) is now below `5k` lines
2. major helper bodies have been extracted into domain support modules
3. runtime lanes, context access, and semantic-governed routing are already split from the old monolith
4. remaining large areas in `service.py` are no longer the original monolith pattern

This means further shrinking is no longer automatically high-value.

## 2. What Remains In `service.py`

The remaining content is mostly one of these categories:

1. top-level runtime orchestration and contract glue
2. stable public smoke/regression entrypoints that now delegate to support modules
3. debug-oriented helpers
4. scenario-heavy hardening suites like `H3`, `H4`, and `H5`

These are different from the earlier extraction candidates because they are:

1. more intertwined with verification workflows
2. less obviously reusable support logic
3. closer to operator/debug ergonomics than to business runtime behavior

## 3. Senior Evaluation

At this point, continued micro-refactoring should be treated as optional, not default.

The project has already captured the high-value wins:

1. reduced monolithic risk
2. clearer ownership boundaries
3. safer semantic/runtime evolution
4. cleaner separation between dispatcher, lanes, context, and support modules

The next best engineering move is usually not “extract one more helper.”

## 4. Recommendation

Pause active micro-slicing here unless one of these is true:

1. a remaining block is still clearly support-only and materially hurts readability
2. a new product/runtime change naturally touches that block
3. a live verification environment becomes available and we want to harden a remaining debug/scenario cluster with stronger confidence

Preferred focus after this checkpoint:

1. governed semantic/runtime work
2. live-site verification recovery
3. product behavior hardening
4. only then optional cleanup of remaining debug or scenario scaffolding

## 5. Practical Next-Step Rule

Before touching `service.py` again, ask:

1. does this change reduce architectural risk, or just line count?
2. can the slice be verified strongly enough for enterprise confidence?
3. is the target code real runtime behavior, or just debug/scenario scaffolding?

If the answer is mostly “line count” or “cosmetic cleanup,” do not proceed.

## 6. Out-Of-Scope Reminder

This checkpoint does not change the standing rule:

1. [sales_console.js](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js) is outside this task and must remain untouched
