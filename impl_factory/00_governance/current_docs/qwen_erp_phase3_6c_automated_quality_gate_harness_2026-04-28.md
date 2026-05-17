# Qwen ERP Phase 3.6C Automated Quality Gate Harness

Status: implemented as executable QA registry and coverage guard  
Date: 2026-04-28  
Scope: Phase 3.6 automated quality-control harness before manual browser UAT and Phase 4 Complex Business Question Decomposition.

## 1. Purpose

Phase 3.6C converts the Phase 3.6B business-question matrix into an executable quality gate.

This is intentionally not a pile of one-off prompt tests.

The goal is to make the gate auditable by business-user aspect:

1. master-data lookup and detail
2. transaction listing
3. financial statements
4. composite KPI evidence
5. follow-up and context switching
6. wise fallback and authority boundaries
7. presentation and live-data readiness

## 2. What Was Implemented

New executable registry:

`ai_assistant_ui/qwen_chat/evaluation/phase36_quality_gate.py`

New validation test:

`ai_assistant_ui/tests/test_phase36_quality_gate.py`

The registry defines every required Phase 3.6 `A` gate row from the minimum exit pack and maps each row to:

1. business-user group
2. gate level
3. execution mode
4. prompt sequence
5. expected behavior
6. fallback or boundary requirement
7. automation layer
8. existing coverage references
9. manual-browser requirement when applicable

## 3. Why This Is Enterprise Grade

This harness avoids the three risky patterns we have been actively eliminating:

1. single-case fixes
2. keyword-only tests
3. hidden coverage assumptions

Instead, each quality row points to an existing shared seam:

1. scope activation
2. entity reference resolution
3. transaction listing rendering
4. financial statement alias and period handling
5. composite evidence selected-row handling
6. unsupported authority boundary
7. context switching and clarification override
8. deterministic presentation rendering

If a manual browser test fails later, we can classify it against this map and fix the shared seam rather than patching only the failed sentence.

## 4. Automated Guard Rules

The new test verifies that:

1. every required Phase 3.6 `A` row is registered exactly once
2. every row has valid gate and execution metadata
3. every automated or mixed row has test references
4. every referenced test file and test function exists
5. all business-user aspect groups are represented
6. authority-boundary rows remain explicitly classified as boundaries

This means Phase 3.6C protects the QA matrix from becoming stale documentation.

## 5. What It Does Not Do

This harness does not replace manual browser testing.

It does not assert exact long-form prose, because exact prose is brittle and can punish harmless wording improvements.

It does not freeze live ERP values, because values naturally change as ERP data changes.

It checks the contract and seam coverage that should remain stable.

Manual browser UAT remains required for:

1. live answer freshness
2. visible formatting
3. no internal error
4. natural fallback tone
5. final end-to-end behavior across multiple turns

## 6. Current Status

Phase 3.6C is now implemented as the first automated quality-gate layer.

This gives us a stable bridge between:

1. the documented Phase 3.6B matrix
2. the existing backend contract tests
3. the upcoming Phase 3.6D manual browser checklist

## 6.1 Update: Composite Clarification Continuation Guard

Date: 2026-05-02

Additional executable guard added:

`ai_assistant_ui/qwen_chat/evaluation/composite_clarification_continuation_smoke.py`

Purpose:

1. prove that revenue/sales amount rankings use the approved Sales Invoice default basis before asking for any remaining clarification
2. cover both customer commercial ranking and product commercial ranking
3. prevent short period replies such as `Last Month` from being misread as standalone listing requests or stale visible-table row references

Covered flows:

1. `Top 7 Customers by Revenue` -> `Last Month`
2. `Top 10 Products by Revenue` -> `Last Month`

Implementation seam:

1. shared conversation-control helper: `pending_clarification_response_should_preempt_runtime`
2. service orchestration gate: pending clarification resolution preempts NBU governed requery, visible-context follow-up, and compiled first-turn runtime lanes unless the clarification layer classifies the turn as a new request
3. regression tests: `test_post_contract_state_integrity` and `test_clarification_resolution_contracts`

Verification completed on 2026-05-02:

1. container compile for changed modules
2. 453 backend unit tests across post-contract state integrity and clarification resolution
3. live bench smoke before restart for customer-ranking clarification continuation
4. backend restart
5. live bench smoke after restart
6. widened live bench smoke for customer and product revenue ranking default-basis continuation

## 7. Next Step

The next recommended step is Phase 3.6D:

1. generate a manual browser UAT checklist from the same business-question groups
2. execute the checklist in browser
3. record pass/fail and any approved exceptions
4. only then decide whether Phase 4 can begin safely
