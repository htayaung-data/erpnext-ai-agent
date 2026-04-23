# Qwen ERP Phase 3.3 Ranking Projection And Evidence Contract Design

Status: active design note, `3.3A` next  
Date: 2026-04-11  
Scope: bounded Phase `3.3` plan for ranking projection harmonization and entity-detail evidence contract cleanup inside the existing enterprise runtime

## 1. Executive Decision

Phase `3.3` should not become a loose collection of ranking prompt fixes.

It should also not defer known authority drift into an undefined later cleanup chapter.

The correct enterprise move is:

1. finish ranking projection behavior as a shared governed runtime capability
2. preserve the recent shared follow-up and subject-switch work
3. remove remaining raw-message business branching from entity-detail evidence rendering through an explicit typed seam
4. complete the missing metadata and semantic slots needed to keep that renderer fail closed without lexical rescue

This means the active bounded order inside `3.3` is:

1. `3.3A` ranking projection contract harmonization
2. `3.3B` entity-detail evidence request contract cleanup
3. `3.3C` metadata and semantic completion for the missing typed evidence distinctions

## 2. Current Starting Point

The current ecosystem is already strong enough to support this work without a redesign.

What already exists:

1. `3.1` composite contracts and metadata are active
2. `3.2` customer commercial ranking composites are active
3. governed continuation state already preserves ranking scope, metric, limit, sort direction, requested columns, and time scope
4. recent shared work already corrected:
   - customer or product ranking defaulting toward minimal columns
   - governed subject-switch behavior such as customer to product
   - targeted diagnostics around ranking subject-switch regression

Important current reality:

1. explicit composite ranking behavior is cleaner than some generic compiled ranking behavior
2. projection behavior is not yet uniformly governed across all ranking paths
3. entity-detail evidence rendering in `boundary_support.py` still contains raw-message business branching that violates the current enterprise authority model

So the next slice is not a fresh architecture chapter.

It is a bounded authority-alignment chapter inside the current ecosystem.

## 3. Why This Should Not Be Deferred

The earlier recommendation to remove lexical business branching from `boundary_support.py` should not be deferred outside the active roadmap.

Why:

1. the current development guide explicitly forbids letting raw message text steer runtime decisions after structured interpretation exists
2. the same authority concern is showing up in the current ranking-harmonization work
3. leaving the renderer lexical while the ranking runtime becomes more contract-driven would preserve two inconsistent authority standards inside the same enterprise assistant
4. this problem is bounded enough to solve safely after `3.3A` without opening a broad refactor chapter

This does not mean `3.3B` should preempt `3.3A`.

It means:

1. do `3.3A` first because it is the active user-facing ranking gap
2. then do `3.3B` immediately as the next approved bounded slice

## 4. Enterprise Rules For This Slice

This note inherits the active development guide and Phase `3` design note.

The specific rules for `3.3` are:

1. do not add a parallel ranking pipeline
2. do not add keyword routing, prompt tricks, or single-case rescue logic
3. do not discard the recent shared subject-switch and projection work if the seam is directionally correct
4. do not let renderer code decide business meaning from English phrases
5. keep business meaning in contracts, metadata, semantic resolution, or governed continuation state
6. keep runtime behavior auditable and fail closed when typed evidence is insufficient

## 5. `3.3A` Ranking Projection Contract Harmonization

Goal:

1. make ranking projection behavior consistent across governed composite ranking and generic compiled ranking paths

Required business behavior:

1. default ranking display is entity plus primary metric only
2. supporting metrics such as quantity, AOV, ASP, or other approved fields appear only when explicitly requested
3. projection follow-ups such as `show customer and revenue only`, `add qty`, or `replace qty with AOV` stay inside the same governed scope when the current artifact already exposes the needed columns
4. time correction follow-ups such as `I mean last year, not last month` re-enter governed requery while preserving the same ranking family, basis, and projection intent
5. subject changes such as customer to product must not reuse stale ranked artifacts

Implementation direction:

1. reuse the current continuation and family-follow-up seams
2. reuse the current render override seam for requested columns, metric key, top N, and sort direction
3. normalize generic ranking outputs so they consume the same projection contract shape already used by cleaner composite ranking paths
4. preserve current bounded requery rules when a follow-up changes governed scope rather than only display shape

Primary files expected to matter:

1. `governed_composite_runtime_execution.py`
2. `family_followup.py`
3. `continuation_support.py`
4. `family_rendering.py`
5. `followup_interpreter.py`
6. `contracts.py`

What must not happen:

1. special-case `product`
2. special-case `customer`
3. hardcode `last year`
4. hardcode `qty` or `aov` behavior outside the shared projection vocabulary

## 6. `3.3B` Entity-Detail Evidence Request Contract Cleanup

Goal:

1. remove raw-message business branching from governed entity-detail evidence rendering

Problem statement:

1. `grounded_artifact_direct_evidence_answer(...)` in `boundary_support.py` still resolves business meaning from phrase checks over `raw_message`
2. this violates the active enterprise rule that structured interpretation should outrank raw text
3. this makes renderer behavior harder to generalize, harder to audit, and weaker for multilingual growth

Implementation direction:

1. keep `raw_message` only for audit or trace purposes
2. pass typed evidence-request state into the governed entity-detail evidence renderer
3. make the renderer answer only from:
   - canonical requested metrics
   - canonical requested dimensions
   - typed question shape
   - typed basis or scope slots
   - grounded artifact fields

Preferred contract posture:

1. adapt the current contract ecosystem rather than inventing a separate mini-stack
2. either:
   - extend the current artifact-boundary or evidence contract with typed evidence-request fields
   - or introduce one small dedicated `EntityDetailEvidenceRequestContract` consumed by the existing boundary seam

Minimum typed fields expected:

1. `requested_metrics`
2. `requested_dimensions`
3. `question_shape`
4. `basis`
5. `value_mode`
6. `entity_question_type` if needed for stable renderer branching

What must remain true:

1. unsupported asks fail closed
2. missing typed distinctions clarify upstream
3. renderer does not recover business meaning by phrase scanning

## 7. `3.3C` Metadata And Semantic Completion

Goal:

1. complete the missing typed distinctions needed so the entity-detail evidence renderer can stop depending on lexical rescue

Expected governed additions:

1. tenure basis:
   - customer created date
   - first sales order
   - first sales invoice
2. date-of-first-activity evidence distinctions
3. overdue question shape:
   - boolean status
   - amount
   - ratio
4. credit-balance question shape:
   - boolean status
   - amount
5. dominant aging bucket or top aging bucket as an approved dimension or evidence slot
6. explicit distinction between `outstanding` and `total due`

Implementation direction:

1. extend metadata and semantic registries first
2. let upstream interpretation produce canonical values
3. let the renderer consume those canonical values
4. do not solve these by adding more phrase checks

## 8. How To Treat The Recent Implementation

The recent ranking work should be treated as a valid bounded step, not as final closure truth.

Current judgment:

1. the recent work is directionally correct because it used shared runtime seams instead of a prompt-only patch
2. the recent work is not yet closure-ready because authority is still partially split between typed contracts and runtime text-derived interpretation
3. the correct response is targeted rework and harmonization, not discard-and-rebuild

So for this phase:

1. keep the shared ranking subject-switch and projection work that is already in the right seam
2. reimplement only the parts that still derive business meaning from raw message parsing where a typed contract should own it

## 9. Verification Order

The approved verification order for this slice is:

1. deterministic contract and runtime tests for the exact changed seam
2. narrow diagnostics or probes for:
   - minimal default ranking display
   - projection follow-up continuity
   - time correction continuity
   - subject-switch continuity
3. compile checks for touched Python modules
4. enterprise guardrail pass where relevant
5. browser or manual UAT only after code-level verification is green

Recommended manual prompts after implementation:

1. `show top 5 customers by revenue for sales orders last month`
2. `give me Customer, Revenue and AOV columns only`
3. `I mean last year, not last month`
4. `show top 5 products by revenue last month`
5. `show top 5 products by revenue for sales orders last month`
6. `add Qty column`
7. `tell me more about Zegyo Mobile Supply House`
8. `what is this customer's tenure by customer created date?`

## 10. Active Stop Rule

`3.3` is successful when:

1. ranking responses default to minimal governed columns consistently
2. explicit additional metrics or columns are respected without stale summary leakage
3. time corrections preserve governed ranking scope through requery
4. subject switches do not inherit stale ranked artifacts
5. entity-detail evidence rendering no longer depends on lexical business branching
6. the fix lives in shared contracts, metadata, continuation logic, and bounded runtime seams

`3.3` is not trying to solve:

1. a general lexical cleanup chapter across the whole assistant
2. dashboard generation
3. management recommendations
4. uncontrolled renderer redesign
