# Qwen ERP AI Assistant Enterprise Evaluation

Status: active evaluation note  
Date: 2026-04-12  
Scope: project-level evaluation of the AI Assistant implementation before further Phase `3.3` runtime changes

## 1. Purpose

This note records a careful re-evaluation of the Qwen ERP AI Assistant as it exists today.

It exists to prevent the next implementation slice from being driven only by the latest failing prompts.

The goal is to restate, in one place:

1. what has already been built
2. what is already enterprise-grade
3. where the real current gaps are
4. what types of fixes must be avoided
5. how the next slice should proceed without architecture drift

This note is design truth, not a closure note.

## 2. Executive Evaluation

The Qwen ERP AI Assistant is already a serious governed enterprise system.

It is not a prompt-led prototype anymore.

The current architecture already includes:

1. contract-governed interaction layers
2. metadata-owned business policy
3. fresh-query semantic interpretation plus compiler enforcement
4. grounded follow-up boundary handling
5. governed report-family execution
6. governed KPI definition and KPI value execution
7. governed composite artifact execution
8. explicit knowledge-boundary behavior
9. release-gated validation

The real issue is not that the project lacks enterprise foundations.

The real issue is that some edge seams are still less mature than the core seams.

In particular, the assistant is strongest when a user request already maps cleanly into:

1. an approved capability
2. an approved report family
3. an approved KPI execution
4. an approved composite family
5. an already-typed follow-up shape

The assistant becomes weaker when the request is:

1. valid ERP domain
2. still inside governed read scope
3. but not yet represented by a fully typed request seam

That is where recent drift occurred.

## 3. What The Project Already Has

The following enterprise assets are already materially present and should be treated as current architecture, not as optional ideas.

### 3.1 Governance And Architecture

Current governing docs already define the intended model:

1. `qwen_erp_enterprise_blueprint_2026-03-19.md`
2. `qwen_erp_enterprise_development_guidelines_2026-04-04.md`
3. `qwen_erp_phase_implementation_roadmap_2026-04-04.md`
4. `qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md`
5. `phase3_entity_lookup_scope/qwen_erp_phase3_3_ranking_projection_and_evidence_contract_design_2026-04-11.md`

Those docs already establish:

1. `model proposes, compiler enforces`
2. contracts before runtime widening
3. metadata owns business policy
4. fail closed when typed evidence is insufficient
5. no keyword routing
6. no hardcoded single-case fixes
7. no raw-message business branching after structured interpretation exists

### 3.2 Metadata Layer

The metadata layer is already substantial and active, not decorative.

Current active metadata homes include:

1. capability registry
2. report registry
3. report family registry
4. business ontology
5. frontdoor intent registry
6. semantic alias and semantic resolution registries
7. business definition, formula, threshold, and rule registries
8. governed KPI execution registry
9. composite family, artifact, compatibility, and assembly registries

This means future behavior should continue to enter through registries first wherever possible.

### 3.3 Contract Layer

The project already uses typed contracts as runtime currency.

Examples already active in the codebase include:

1. `InteractionContract`
2. `FreshQueryInterpretationContract`
3. `FreshQueryCompilerContract`
4. `FollowUpBoundaryContract`
5. `EntityDetailEvidenceRequestContract`
6. `GovernedKpi...` execution and artifact contracts
7. `CompositeFamilyResolutionContract`
8. `CompositeArtifactResolutionContract`
9. `CompositeAssemblyAdapterContract`

This is an important project strength.

The correct next moves should extend these seams, not bypass them.

### 3.4 Runtime Capabilities Already Proven

The assistant already has meaningful governed runtime behavior for:

1. operational listing/detail/follow-up coverage
   - Delivery Notes
   - Sales Orders
   - Purchase Orders
2. customer credit status and detail
3. governed KPI definition answers
4. governed KPI value execution
5. customer-scoped KPI execution
6. composite commercial ranking families
7. follow-up boundary and artifact continuity
8. knowledge-boundary blocking for unsupported asks

### 3.5 Verification Discipline

The project already has strong enterprise verification habits:

1. guardrail audit
2. semantic verification
3. post-contract verification
4. container-backed release-gate execution
5. targeted probes and smokes
6. broad test coverage across contracts and runtime seams

This is one of the clearest signs that the system is already beyond prototype level.

## 4. What The Project Does Well Today

The assistant is already strong in these areas:

### 4.1 Governed Business Questions

When a question fits an approved business capability, the system has a strong architecture for:

1. semantic proposal
2. compiler enforcement
3. metadata-governed source selection
4. grounded execution
5. fail-closed behavior when scope is insufficient

### 4.2 Follow-Up Governance

The project has already invested heavily in:

1. typed grounded context
2. follow-up boundary contracts
3. continuation protection
4. explicit lane selection
5. bounded fallback

This means the right answer to current problems is usually:

1. improve the typed follow-up seam
2. improve metadata-owned interpretation
3. avoid reintroducing raw-message recovery

### 4.3 KPI And Composite Maturity

The project has already crossed the threshold from:

1. simple report retrieval

to:

1. governed KPI execution
2. governed composite artifact execution
3. compatibility and basis control
4. family-based composite runtime behavior

That is real enterprise advancement and should be preserved carefully.

## 5. Where The Real Current Gaps Are

The current weaknesses are not broad architectural failure.

They are narrower seams where enterprise structure is not yet fully complete.

### 5.1 Entity-Oriented Discovery And Resolution

The most visible current gap is the seam between:

1. front-door semantic understanding
2. valid ERP lookup-style requests
3. master-data listing or lookup
4. candidate entity resolution
5. handoff into entity detail/profile behavior

Examples of this class of request include:

1. `give me some customer names`
2. `do you have a customer similar to Ko Nay Lin Mobile`
3. `tell me details about Ko Nay Lin Mobile Center`
4. `give me some supplier names`
5. `give me some item names`

These are not out-of-domain asks.

They are valid ERP asks.

But they are not yet represented through a clean enough typed seam across all supported grains.

### 5.2 Remaining Lexical Authority Drift

The current `3.3` design note already identified an authority problem:

1. some renderer or detail logic still recovers business meaning from raw message text
2. some runtime seams still use lexical rescue where typed state should own the decision

This remains the most important anti-pattern to remove in the next bounded slice.

### 5.3 Uneven Contract Activation Across Adjacent Surfaces

The project has strong contracts in some areas, but not all adjacent surfaces are equally activated.

For example:

1. KPI and composite family contracts are strongly established
2. detail evidence contracts exist
3. but some lookup/discovery/resolution asks still rely on partial runtime heuristics

So the assistant is currently more mature in metric/composite questions than in some master-data navigation questions.

### 5.4 High-Traffic Concentration Seams

The active debt register remains right to track these as near-blockers:

1. `service.py` orchestration concentration
2. `fresh_query_interpreter.py` scope concentration
3. external runtime governance

These do not justify a broad refactor-first chapter now.

But they should affect how narrowly the next change is designed.

## 6. What Must Be Avoided Next

The current project state makes the following especially dangerous:

### 6.1 Single-Case Runtime Rescue

Do not:

1. add one more customer-specific patch
2. add one more supplier-specific patch
3. add phrase-specific branches to make one UAT prompt pass

That would directly violate the active development guide.

### 6.2 Phrase-Led Detail Interpretation

Do not:

1. keep widening phrase scanners like `tell me details about`
2. keep extracting business meaning from English phrase lists after typed interpretation already exists
3. make runtime behavior depend on one wording family

### 6.3 Parallel Architecture Reinvention

Do not:

1. replace the current ecosystem with a brand-new lookup architecture
2. ignore existing contracts, metadata, and continuation state
3. build a second routing stack beside the current one

This project already has too much valid architecture to justify reinvention.

### 6.4 Hidden Fallback Expansion

Do not:

1. widen deterministic rescue without explicit governance
2. hide degraded behavior inside helper logic
3. let fallback silently change business meaning

If fallback exists, it must remain:

1. bounded
2. explicit
3. auditable
4. test-protected

## 7. Current Judgment On The Recent Customer-Focused Slice

The recent customer-master lookup work should be judged as partially useful but not final-architecture quality.

### 7.1 What Was Directionally Useful

Useful signals from that slice:

1. the user problem is real
2. these requests should not fall into irrelevant clarification
3. `master_data_lookup` is a real seam worth activating
4. a governed master-data path is better than ad hoc answer invention

### 7.2 What Was Not Enterprise-Grade Enough

The wrong parts were:

1. customer-specific rescue logic in shared runtime seams
2. phrase-led detail detection
3. customer-only fuzzy resolution imported broadly
4. output-driven green-path repair instead of seam-completion

This means the right action is:

1. keep the valid governed intent
2. remove the lexical and customer-specific rescue shape
3. re-implement through existing contracts and metadata

It does **not** mean:

1. discard the whole direction
2. deny the business need
3. start from zero

## 8. Phase Placement

This gap belongs inside the active Phase `3.3` authority-alignment work, not in a disconnected side track.

The official `3.3` design note already defines:

1. `3.3A` ranking projection harmonization
2. `3.3B` entity-detail evidence request contract cleanup
3. `3.3C` metadata and semantic completion for missing typed evidence distinctions

Current evaluation:

1. the remaining lexical business branching clearly belongs in `3.3B`
2. the missing typed distinctions for lookup/detail evidence belong in `3.3C`
3. the work should remain bounded and should not widen into a broad redesign chapter

## 9. Recommended Enterprise-Safe Direction

The next design and implementation slice should follow this posture:

### 9.1 Reuse The Existing Ecosystem

Prefer:

1. extending current contracts
2. extending metadata registries
3. extending governed semantic interpretation
4. extending approved continuation state

Avoid:

1. new parallel stacks
2. special prompt routers
3. per-domain rescue handlers

### 9.2 Complete The Missing Typed Seam

The system needs a cleaner typed seam for valid ERP lookup-style requests that can cover, at minimum:

1. directory-style entity listing
2. candidate entity resolution
3. typed handoff into entity detail/profile requests

This should be done through existing contract and metadata patterns, not through raw-message scanning.

### 9.3 Keep Unsupported Scope Honest

Where a request is:

1. valid ERP domain
2. but not yet supported by approved governed sources or typed contracts

the assistant should:

1. fail closed honestly
2. clarify if the missing distinction is small and typed
3. avoid pretending support through rescue logic

## 10. Practical Stop Rule For The Next Slice

The next bounded slice is good enough when:

1. valid ERP lookup-style requests stop depending on raw phrase rescue
2. entity-oriented lookup behavior is represented by typed state rather than customer-only logic
3. existing governed KPI, ranking, and detail behavior do not regress
4. unsupported asks still fail closed clearly
5. verification proves seam behavior, not only literal answer wording

The next slice is **not** trying to solve:

1. every unseen ERP question
2. a full multilingual redesign
3. a new global architecture chapter
4. broad `service.py` refactoring

## 11. Final Evaluation

The current assistant should be understood this way:

1. enterprise-grade in its foundations
2. materially strong in governed business, KPI, composite, and follow-up behavior
3. still incomplete in a few edge seams around entity-oriented lookup and evidence resolution
4. at risk only when those seams are repaired through phrase-led or single-case runtime logic

Therefore the right next move is not invention.

The right next move is disciplined seam completion.

That means:

1. preserve the architecture that is already working
2. remove the recent non-enterprise rescue shape
3. complete the missing typed seam through contracts and metadata
4. keep the work bounded inside the active roadmap
