# Phase 2 Working Contract

Date: 2026-03-01  
Owner: AI Runtime Engineering  
Scope: Phase 2 quality architecture hardening, post-refactor stabilization, and transition into Phase 3 regression discipline  
Status: active working contract

## Purpose
This contract governs how the remaining runtime fixes must be made.

It exists to stop three failure modes:
1. prompt-by-prompt patching
2. runtime keyword fallback growth
3. endless browser-debug loops without class closure

This is not a runtime JSON contract. It is an engineering working contract for the current stage.

## Non-Negotiable Boundaries
1. No ad-hoc keyword-driven runtime routing.
2. No case-ID hacks.
3. No prompt-to-report mapping in runtime modules.
4. No hidden fallback behavior that cannot be explained by contract, ontology, metadata, or persisted state.
5. No broad reruns before targeted invariant-level verification.
6. No behavior change in the name of refactor unless verified by targeted replay or direct unit coverage.

## Allowed Fix Types
1. Capability metadata enrichment in governed data files.
2. Ontology normalization enrichment in governed data files.
3. Generic state-policy fixes in memory/resume/transform/shaping modules.
4. Deterministic resolver scoring or gating improvements.
5. Quality-gate fixes that strengthen data-vs-presentation correctness.
6. Structural refactor that reduces orchestration fragility without changing business semantics.

## Disallowed Fix Types
1. `if prompt contains X, choose Y`
2. `if case_id == ...`
3. hardcoded business phrase fallback maps in:
   - `read_engine.py`
   - `semantic_resolver.py`
   - `response_shaper.py`
   - `quality_gate.py`
   - `spec_pipeline.py`
   - `memory.py`
4. forcing a reply shape just to satisfy one manifest case
5. broad manual exploration used as the main debugging method

## Class-First Rule
Every failure must be categorized first as one of:
1. wrong behavior class
2. wrong report selection
3. wrong state carryover
4. wrong transform/projection semantics
5. wrong capability metadata
6. wrong presentation/shaping

No code change should be made until the failure is framed as one of those classes.

## Required Fix Workflow
For every new regression family:
1. Identify the invariant being violated.
2. Fix the invariant at the correct layer.
3. Add one focused regression example for that invariant.
4. Run targeted unit verification.
5. Run targeted replay only for the affected family.
6. Use browser/manual only as confirmation, not as the primary debugging engine.

## Current Invariant Focus
The current runtime must preserve these invariants:
1. Fresh explicit read must reset stale output-shape carryover.
2. Follow-up transform must bind only to the latest eligible active result.
3. Restrictive projection with `only` must keep only explicitly requested columns.
4. Ranking correction must preserve grain, metric, time scope, and `top_n`, changing only the requested axis.
5. Refinement that changes underlying grain or doctype must trigger a fresh anchored read, not `TRANSFORM_LAST`.
6. Report metadata must outrank weak lexical inference whenever the selected report is already feasible.

## Verification Rules
1. Targeted replay comes before broad replay.
2. Browser/manual confirmation comes after invariant-level fix, not before.
3. A suite is not considered stable if the same prompt must be repeated to succeed.
4. A behavior class is not considered stable until its variation matrix is materially green.

## Current Stage Assessment
1. Phase 1 functional stabilization is largely achieved but not yet fully re-proven after the latest refactor.
2. Phase 2 monolith-risk reduction is actively underway and materially improved.
3. Phase 3 has started only in the form of focused regressions and variation matrices; it is not yet formalized.

## Next-Step Rule
From this point forward:
1. do not add new behavior classes
2. do not broaden ontology casually
3. do not continue refactoring for its own sake
4. close post-refactor regression families first
5. then formalize regression discipline and ownership

## Exit Criteria For This Working Contract
This working contract can be retired only when:
1. post-refactor targeted replay suites are green again
2. the active variation matrix is materially closed
3. no known browser/manual failure still requires a retry to succeed
4. remaining work shifts from stabilization to formal regression discipline and operational governance
