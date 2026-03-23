# Qwen ERP Phase 4B Slice 9 Evaluation and Rollout Note (2026-03-22)

Status: completed

## Purpose

Slice 4B.9 adds governed family-level evaluation and rollout measurement so Phase 4B can be judged by family evidence, not only one-off smokes.

## What Was Implemented

1. governed family evaluation dataset in:
   - `impl_factory/03_config/qwen_enterprise_metadata/family_evaluation_registry.json`

2. ERP metadata accessors for the evaluation registry in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`

3. family-aware compiled audit fields in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py`

4. governed family evaluation runners in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

5. family-aware audit summaries in:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

6. semantic/family hardening discovered during evaluation:
   - normalized family artifacts now bridge semantic validation where raw report-schema checks were over-rejecting valid governed answers
   - profit-and-loss family validation now treats `provisional_profit_or_loss` as optional instead of mandatory

## New Runtime/ERP Evaluation Helpers

1. `run_phase4b_family_evaluation_suite`
2. `run_phase4b_family_evaluation_smoke`
3. `summarize_compiled_first_turn_audits`

## Verified

1. `python3 -m py_compile ...`
2. JSON validation for `family_evaluation_registry.json`
3. `bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.semantic_validator.run_phase4_semantic_validation_selftests`
4. `bench --site erpai_prj1 execute ai_assistant_ui.qwen_chat.service.run_phase4b_family_evaluation_smoke`

## Current Governed Baseline

Core family evaluation set result after the latest post-slice hardening:

1. `case_count = 7`
2. `passed_case_count = 7`
3. `failed_case_count = 0`
4. `smoke_ok = true`
5. `baseline_ok = true`

Passing families:

1. `financial_statement`
2. `aging`
3. `ranking_analytics`
4. `trend_analytics`
5. `inventory_snapshot`
6. `product_profitability`
7. `working_capital_health` composite

Trend-family hardening outcome:

1. live compiled `trend_analytics` now routes generic sales-trend requests through `sales_read`
2. the governed selected report is now `Sales Analytics`, not `Item-wise Sales History`
3. family validation passes on the normalized trend artifact
4. semantic validation also passes on the compiled trend result

## Enterprise Interpretation

This slice is complete because:

1. family-based governed evaluation now exists
2. rollout/fallback metrics can now be summarized by family
3. compiled family baselines are measurable and repeatable
4. the evaluation layer exposed a real hardening target instead of hiding it
5. the measured trend-family gap was closed under the governed compiled path

This slice does not mean Phase 4B is "finished forever".

The new state after Slice 4B.9 is:

1. the core governed family baseline is fully green on the current acceptance set
2. the family evaluation suite is now the required regression gate for future family changes
3. the next enterprise work should move to post-4B operational hardening rather than one remaining family gap

## Recommended Next Step

Move to post-4B operational hardening with the family evaluation suite as the acceptance gate:

1. keep compiled family execution as the preferred enterprise path for richer families
2. reduce composite and other heavy-family latency without relaxing compiler or validator governance
3. expand the governed family evaluation sets beyond the current core seven cases
4. continue widening business-family coverage by family packages, not by isolated example questions
