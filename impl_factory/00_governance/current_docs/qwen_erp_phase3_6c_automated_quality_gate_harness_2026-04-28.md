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
6. fallback or boundary requiremen
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
3. the upcoming Phase 3.6D manual browser checklis

## 7. Next Step

The next recommended step is Phase 3.6D:

1. generate a manual browser UAT checklist from the same business-question groups
2. execute the checklist in browser
3. record pass/fail and any approved exceptions
4. only then decide whether Phase 4 can begin safely
