# Qwen ERP Revised Architecture Mini-phase Roadmap (2026-03-25)

Status: active roadmap reset  
Scope: replace the older narrow contract-only sequence with the updated enterprise architecture plan:

1. finish current 3 contracts cleanly
2. add `FrontDoorIntentGate`
3. add `ERPBusinessReasoningContract`
4. add `KnowledgeBoundaryContract`
5. then integrate front-door + artifact lane + reasoning lane

Decision: keep report-family contracts focused on governed ERP data and artifact continuity; do not solve general ERP business reasoning inside report-family follow-up logic.

## 1. Executive Architecture

The target runtime should have three main lanes plus a boundary layer.

### 1.1 Front-door lane

Purpose:

1. catch greetings, thanks, low-signal chat, capability questions, and session-flow turns
2. keep non-ERP conversational turns out of the governed artifact pipeline
3. route valid ERP-business questions onward

Target authority:

1. `FrontDoorIntentGate`

### 1.2 Governed artifact lane

Purpose:

1. resolve fresh ERP queries into governed reports or composite reads
2. preserve artifact continuation over grounded ERP results
3. choose local transform vs governed requery vs fresh breakout

Target authorities:

1. `ArtifactContinuationContract`
2. `GovernedScopeDecisionContract`
3. `ClarificationReasonContract`

### 1.3 ERP business reasoning lane

Purpose:

1. answer accounting, finance, management, operations, HR-business, and ERP-domain interpretation questions
2. stay bounded to ERP business scope
3. answer from grounded artifacts when possible
4. otherwise answer from bounded ERP business knowledge, not random general knowledge

Target authority:

1. `ERPBusinessReasoningContract`

### 1.4 Boundary layer

Purpose:

1. decide whether a question should be treated as:
   - grounded ERP artifact question
   - ERP business reasoning question
   - clarification case
   - valid ERP domain but not yet covered
   - unsupported request
2. keep the system from bouncing between report runtime and generic fallback behavior

Target authority:

1. `KnowledgeBoundaryContract`

## 2. What We Have Already Done

### 2.1 Contract architecture progress already completed

These are real improvements and should be kept.

1. `ArtifactContinuationContract` exists and is already threaded into runtime
2. `GovernedScopeDecisionContract` exists and is already emitted and partly consumed
3. service now preserves more continuation state through contracts instead of re-guessing everything ad hoc
4. fresh-query breakout behavior improved through contract-driven orchestration
5. unknown-handling improved for some finance asks through metadata-driven support-surface fixes

### 2.2 Metadata and support-surface improvements worth keeping

These are not narrow term-pair patches and should stay.

1. broader governed finance concept support such as:
   - `cash_flow`
   - `balance_sheet`
   - `tax`
2. capability/family support-surface improvements
3. ontology and registry improvements that describe true governed coverage

### 2.3 Governance and planning artifacts already created

These should stay and continue to guide work.

1. `qwen_erp_contracts_miniphase1_inventory_2026-03-25.md`
2. `qwen_erp_post_contract_expansion_backlog_2026-03-25.md`

## 3. What We Intentionally Stepped Back From

The branch already proved one important lesson:

Trying to solve semantic comparison or definition questions by adding more local term-matching behavior in follow-up logic is not the final enterprise path.

So we intentionally stepped back from:

1. grounded term-specific semantic follow-up patches
2. metadata additions whose main purpose was to make one specific definition/comparison answer work
3. blending general ERP business reasoning into the current report-family follow-up path

Those experiments were useful because they showed where the real boundary problem is, but they should not become the permanent architecture.

## 4. Current Position

We are here now:

### 4.1 Stable direction

1. the branch is already in the contract-migration stream
2. Contract 1 and Contract 2 are partially real
3. broad finance support-surface classification is better than before
4. report-family architecture is still the right foundation for governed ERP data

### 4.2 Not finished yet

1. Contract 1 is not yet the sole authority for continuation
2. Contract 2 is not yet the sole authority for local vs requery vs clarify vs fresh vs out-of-scope
3. Contract 3 does not yet exist as the true upstream clarification-reason authority
4. front-door lane does not yet exist
5. ERP business reasoning lane does not yet exist
6. knowledge boundary between governed artifact and ERP reasoning is not yet explicit

## 5. Revised Mini-phase Sequence

This is the updated enterprise roadmap from now on.

Important correction:

1. Mini-phase 3 contract cleanup was necessary and valuable, but it is no longer the active core track
2. the active core track now moves to metadata/discovery because that is the foundation for later contract families, enrichment compatibility, reasoning boundaries, and front-door quality
3. runtime UX/recovery issues discovered during testing are real, but they should not pull this chapter away from metadata/discovery completion

## Mini-phase 1

Completed.

Goal:

1. inventory what already exists for the 3 contracts
2. classify keep vs transitional vs retire-later

Primary artifact:

1. `qwen_erp_contracts_miniphase1_inventory_2026-03-25.md`

## Mini-phase 2

In progress.

Goal:

1. finish `ArtifactContinuationContract` as the authoritative continuation data model
2. retire competing continuation re-guessing gradually

Done so far:

1. source artifact scope is captured more explicitly
2. preserved metric/dimension/limit/date/projection state is captured more explicitly
3. service already reads continuation contract in several places

Still to do:

1. remove more competing continuation branches
2. make continuation contract the first authority across local follow-up and governed requery paths

## Mini-phase 3

Completed enough to move forward, with final review retained as needed.

Goal:

1. complete contract authority cleanup for:
   - `ArtifactContinuationContract`
   - `GovernedScopeDecisionContract`
   - `ClarificationReasonContract`
2. reduce Python-owned fallback policy and phrase-surface overreach
3. make current artifact-lane behavior production-acceptable before new chapters

Status judgment:

1. good enough to stop as the active focus
2. may still receive targeted cleanup later if another chapter proves real residual debt
3. should not be expanded further right now

## Mini-phase 4

Closed.

Goal:

1. build and harden discovered ERP metadata as a separate foundation layer
2. keep discovered ERP surface separate from governed semantic contracts
3. use discovery to understand real ERP/report surface before adding more runtime behavior

Sub-sequence:

1. Discovery Foundation
   - extract reports, doctypes, filters, columns, and governed/live alignment
2. Change Detection
   - add source signature, diff awareness, and refresh-if-changed behavior
3. Discovery Evaluation
   - evaluate whether the extracted ERP surface is useful enough and where it is weak
4. Discovery Strengthening
   - enrich script-report surface using governed hints where live ERP declaration is weak
5. Discovery-to-Runtime Bridge
   - use discovery outputs to inform runtime and contract decisions carefully, without turning discovery into the runtime authority
6. Discovery Evidence Policy
   - define what discovery proves vs what still depends on governed semantic assumptions for priority reports

Current status:

1. Discovery Foundation: done
2. Change Detection: done
3. Discovery Evaluation: done
4. Discovery Strengthening: done for the current boundary
5. Discovery-to-Runtime Bridge: started carefully
6. metadata gap audit completed:
   - `qwen_erp_metadata_gap_audit_2026-03-25.md`
7. discovery evidence policy added:
   - `report_surface_evidence_registry.json`
   - `qwen_erp_discovery_evidence_policy_note_2026-03-25.md`

Current judgment:

1. discovery is already useful enough to keep
2. report-backed governed alignment is now honest after separating `direct_query` entries
3. the main remaining gap is not report discovery itself
4. it is the thin ERP-declared surface of script reports
5. the current metadata chapter now has an explicit evidence boundary for priority reports
6. so the next metadata move should be governance/use of discovery, not blind generic extractor expansion

Closure artifact:

1. `qwen_erp_miniphase4_closure_note_2026-03-25.md`

Rules:

1. discovery tells us what exists
2. discovery does not decide business meaning by itself
3. discovery supports later contracts; it does not replace them

## Mini-phase 5

Closed after redesign and closure review.

After metadata/discovery is judged stable enough.

Goal:

1. add `FrontDoorIntentGate`

It should handle:

1. greetings
2. thanks
3. acknowledgements
4. capability questions
5. low-signal conversational turns
6. simple session-repair turns such as `okay`, `continue`, `go on`

Rule:

1. this gate should route ERP-business questions onward
2. it should not become a catch-all answer engine
3. conversational intent proposal should come from AI classification plus deterministic guardrails, not keyword bags in code or JSON

Design artifact:

1. `qwen_erp_miniphase5_frontdoor_intent_gate_design_2026-03-25.md`

Current status:

1. Slice 5.1 contract and policy layer: implemented
2. Slice 5.2 AI proposal plus deterministic guardrails: implemented
3. Slice 5.3 service integration and warm response rendering: implemented
4. live browser testing improved greetings/thanks/capability questions
5. live browser testing also exposed regressions in ERP clarification continuity
6. redesign implementation corrected the clarification/front-door boundary
7. closure review passed for Mini-phase 5 scope

Current lesson:

1. front-door should stay thin
2. pending ERP clarification should not be treated as ordinary front-door/session-flow state
3. clarification option selection must bind to the pending ERP clarification, not behave like a fresh standalone query
4. we should not keep expanding front-door features while this boundary remains unstable
5. recommendation-detail follow-ups after a valid ERP analysis are not Mini-phase 5 work; they belong to later reasoning/recovery chapters

Redesign decision after architecture review:

1. add a new highest-precedence `ClarificationResolutionAuthority` before front door
2. front door must be skipped entirely when clarification is pending
3. front door remains a thin conversational lane only
4. ERP lane must consume resolved clarification slots structurally
5. clear business asks such as payable/receivable should not trigger user-facing internal report ambiguity unless a genuinely user-visible distinction is required

Redesign progress now completed:

1. `ClarificationResolutionContract`: implemented
2. `ClarificationResolutionAuthority` before front door: implemented
3. ERP lane consumption of resolved clarification slots: implemented
4. explicit persisted pending clarification state on `Qwen Chat Session`: implemented
5. internal default report selection for structural summary/detail ambiguity such as AP/AR: implemented
6. minimal clarification repair handling for `empty_ack` and `meta_question`: implemented
7. `closure_signoff` intent class added for polite session-ending turns
8. alias-based front-door and clarification business-signal authority removed
9. front door now uses semantic fresh-query cross-check instead of lexical business-signal veto
10. clarification `new_request` detection now uses semantic fresh-query cross-check instead of ontology-alias matching
11. semantic fresh-query cross-check is now current-turn-only for front door / clarification, preventing gratitude or closure turns from inheriting stale ERP context

Closure decision:

1. Mini-phase 5 is closed for its intended scope
2. clarification resolution remains the only authority for pending clarification state
3. later recommendation-detail reasoning and recovery work moves to later phases, not back into front door

## Mini-phase 6

Active next phase after Mini-phase 5 closure.

Goal:

1. add `ERPBusinessReasoningContract`

This is not a report family.

It is a separate reasoning lane for:

1. accounting meaning
2. finance interpretation
3. management explanation
4. ERP-domain recommendation framing
5. HR/business interpretation where it stays within ERP-business scope

Rule:

1. bounded ERP business knowledge only
2. not random general knowledge

This phase should also absorb:

1. continuation over recommendation/explanation detail after a valid analytical answer
2. examples like:
   - `give me suggestions in details`
   - `explain that recommendation more`
3. these are not front-door failures and should not be solved by Mini-phase 5 routing logic

## Mini-phase 7

After the ERP reasoning lane exists.

Goal:

1. add `KnowledgeBoundaryContract`

It must decide between:

1. front-door answer
2. governed artifact lane
3. ERP business reasoning lane
4. clarification
5. valid ERP domain but not yet covered
6. unsupported request

This phase is what prevents semantic questions from being pushed into the wrong report path.

## Mini-phase 8

Deferred structural chapter: artifact enrichment recovery and conversational repair.

Reason for deferral:

1. this chapter was surfaced by runtime testing
2. it is important, but it should not interrupt metadata/discovery as the current core track
3. it should be implemented after discovery and boundary foundations are stronger

Target authorities to add here:

1. `ArtifactEnrichmentRecoveryContract`
2. `ConversationalRepairIntent`

Required outcomes:

1. when enrichment fails, return structured recovery options:
   - `keep_current_artifact`
   - `run_alternative_governed_query`
   - `clarify_target_output`
   - `unavailable`
2. if the user accepts an alternative, convert that into a fresh governed query with preserved safe context
3. repair/instruction questions such as:
   - `how can I instruct you`
   - `what should I ask for`
   - `how do I get`
   should go to guidance/clarification instead of being treated as data requests
4. explicit fresh asks such as:
   - `just give me top 7 product, revenue, qty`
   must override stale continuation context more strongly
5. recovery after analytical-follow-up drift, when the user is trying to continue advice or explanation rather than request a new artifact view

Rule:

1. this chapter is not template polishing
2. this chapter is recovery orchestration and conversational repair

## Mini-phase 9

Integration phase.

Goal:

1. integrate front-door + artifact lane + reasoning lane + boundary layer
2. integrate enrichment recovery after its chapter is complete
3. retire legacy split-authority branches
4. prove behavior with browser regression packs

## 6. Design Rules For All Remaining Mini-phases

These rules are now fixed.

1. do not patch single questions or single answer phrasings
2. do not move keyword bags into code and call it architecture
3. do not move keyword bags into JSON and call it architecture
4. use metadata for canonical business surface, not for endless phrase enumeration
5. keep report families for ERP data and artifacts
6. keep ERP business reasoning outside report-family follow-up logic
7. use contracts as authorities and service as orchestration

## 7. What Is Next Right Now

The immediate next step is:

1. rerun targeted regression on clarification continuity
2. keep clarification resolution as the only owner of pending clarification state
3. keep Mini-phase 5 scoped to routing and clarification correctness

What is explicitly not next:

1. not more front-door expansion right now
2. not more phrase-level patching
3. not ERP business reasoning implementation yet
4. not knowledge-boundary implementation yet
5. not enrichment-recovery implementation yet

## 8. Practical Summary

What we have done:

1. started the 3-contract migration
2. improved continuation and scope architecture materially
3. improved several governed finance support surfaces
4. built discovery foundation, change detection, evaluation, and strengthening slices
5. documented contract inventory and post-contract expansion backlog

Where we are now:

1. Mini-phase 3 is good enough to stop as the active center
2. Mini-phase 4 is complete enough to close
3. Mini-phase 5 has been implemented in early slices but is now paused for architecture review
4. runtime testing surfaced both a later recovery chapter and a nearer clarification/front-door boundary problem
5. architecture review now confirms that clarification resolution must become its own authority before Mini-phase 5 can succeed
6. Mini-phase 5 should continue only through that redesign path, not by further front-door expansion

What is next:

1. build front door
2. then build ERP business reasoning
3. then build knowledge boundary
4. then implement enrichment recovery in its proper chapter
5. then integrate all lanes cleanly
