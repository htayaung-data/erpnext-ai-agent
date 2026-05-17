# Qwen ERP Phase 4B Post-Family Latency Hardening Note (2026-03-23)

Status: completed

Scope:

- post-Phase 4B operational hardening for governed family execution
- first target: composite read latency for `working_capital_health`

## Summary

After Phase 4B reached a fully green `7/7` core governed family baseline, the clearest remaining operational weakness was composite latency.

The `working_capital_health` composite plan was still executing its governed child steps sequentially, which kept composite runtime latency materially higher than the single-family path.

This hardening pass kept the existing compiler / adapter / validator contracts intact and improved the runtime behavior instead of redesigning the architecture.

## What Changed

1. runtime chat request configuration is now snapshotted deterministically on the current worker thread in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
2. governed composite child execution now uses that immutable runtime request config in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py`
3. composite execution now uses parallel child step execution when the governed composite profile explicitly allows it
4. if parallel execution fails for any reason, the composite path falls back safely to sequential execution and records the failure reason in the composite execution audit

## Why This Is Enterprise-Safe

This change remains in line with the enterprise rule:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

because:

1. no execution authority moved back to the model
2. the governed composite plan still decides whether parallel execution is allowed
3. each child step still runs through the same compiled request boundary
4. normalization, family validation, semantic validation, and audit contracts remain unchanged

## Verification

Verification completed with:

1. `python3 -m py_compile ...`
2. `bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.fresh_query_interpreter.run_phase4b_composite_read_smoke`
3. `bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_first_turn_regression_suite --kwargs '{"messages":["Top 5 customers by revenue"]}'`
4. `bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase4b_family_evaluation_smoke`

## Measured Result

Latest governed evidence:

1. `working_capital_health` composite execution now reports:
   - `parallel_execution_allowed = true`
   - `parallel_execution_used = true`
2. composite runtime execution dropped from the earlier sequential baseline of roughly `32.8s` to about `15.6s` on the latest governed family smoke
3. the core governed family baseline remained `7/7` passing after verification

One operational note:

1. one intermediate family smoke produced a transient `proposal_runtime_error` fallback on `ranking_analytics`
2. an immediate targeted ranking rerun and the subsequent full family smoke both passed
3. so the final verified state after this hardening pass is still `7/7` passing

## Recommended Next Step

Continue post-4B operational hardening with the same acceptance gate:

1. keep the family evaluation suite as the regression gate
2. continue broadening governed family datasets beyond the current core set
3. keep reducing latency on heavier families without weakening compiler or validator governance
