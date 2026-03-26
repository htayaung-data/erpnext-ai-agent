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

## Mini-phase 5.5

Foundation hardening after Mini-phase 5 closure and before Mini-phase 6.

Goal:

1. make the newly closed Mini-phase 5 operationally trustworthy before adding new reasoning/recovery layers

This is not a new user-facing lane.

It is a bounded hardening phase for:

1. clarification attempt enforcement
2. regression test coverage
3. explicit clarification state discipline
4. basic observability for clarification/front-door decisions

Rule:

1. do not reopen Mini-phase 5 architecture
2. do not add new conversational features here
3. do not start Mini-phase 6 until Mini-phase 5.5 is good enough

Why this phase exists:

1. the architecture is now materially healthier
2. but enterprise trust requires verification, not only better structure
3. Mini-phase 6/7/8 would be riskier if built on unverified clarification and routing behavior

Phase 5.5 scope:

1. clarification max-attempt handling with safe fallback policy
2. automated regression tests for clarification continuity and thin front-door behavior
3. explicit clarification-state transitions
4. observability for:
   - clarification decisions
   - attempt counts
   - fallback usage
   - front-door vs ERP routing outcomes

Phase 5.5 constraints:

1. no keyword-bag repair logic
2. no single-case fixes
3. no new broad front-door intent expansion
4. fallback must be governed-safe:
   - use a true governed default when one exists
   - otherwise stop safely rather than silently choosing an arbitrary option

Recommended implementation order:

1. 5.5A clarification-state foundation
2. 5.5B max-attempt enforcement
3. 5.5C automated regression suite
4. 5.5D observability and metrics
5. 5.5E close-out review before Mini-phase 6

Current progress:

1. 5.5A clarification-state foundation: implemented
2. explicit wrapper now stores:
   - `state`
   - `attempt_count`
   - `max_attempts`
   - `pending_signal`
3. backward compatibility with older raw clarification-signal storage is preserved
4. 5.5B max-attempt enforcement: implemented
5. current bounded policy:
   - unresolved clarification attempts increment explicit state
   - true governed default may be used only when one is explicitly carried by the clarification payload
   - otherwise the assistant stops safely and refuses to guess
6. 5.5C callable regression suite: implemented
7. the suite now verifies:
   - bounded clarification attempts
   - meta-question handling
   - fresh ERP override while clarification is pending
   - gratitude/closure front-door boundaries after grounded ERP answers
   - AP/AR direct-intent default-report behavior
8. 5.5D observability: implemented
9. clarification/front-door decisions now emit structured `qwen_phase55_observability_event` payloads into session trace and dedicated logger output
10. live verification confirmed:
   - attempt count persisted across repeated unresolved replies
   - pending clarification state cleared after the bounded stop path
   - financial-statement ambiguity did not auto-pick an arbitrary option
   - the callable hardening suite passed end to end
   - observability smoke confirmed both front-door and clarification events were emitted

Closure review:

1. 5.5A through 5.5D are now complete
2. the hardening suite caught and drove a structural fix in pending fresh-query override detection
3. Mini-phase 5.5 is ready to close
4. Mini-phase 6 can now begin on a materially safer foundation

Qwen-reviewed carry-forward notes:

1. Mini-phase 5.5 is closure-ready, but Mini-phase 6 should explicitly inherit a small hardening backlog rather than pretending the foundation is perfect
2. Mini-phase 6.1 should add:
   - severity levels for front-door and clarification observability events
   - a more formal CI-grade regression layer built from the current callable hardening suite
   - explicit regression lock-in for:
     - pending fresh-query override while clarification is pending
     - gratitude/closure staying in front door after grounded ERP answers
3. Mini-phase 6.2 should evaluate:
   - concurrent session mutation / clarification-state race conditions
   - broader adversarial clarification-state tests
4. these are carry-forward hardening tasks, not blockers to starting Mini-phase 6
5. what should not happen next:
   - no front-door intent expansion
   - no keyword or phrase-bag clarification logic
   - no uncontrolled AI authority for clarification resolution
   - no hidden dissatisfaction/repair lane slipped into Mini-phase 6.0

Exit criteria:

1. clarification loops are bounded
2. slot binding and clarification override behavior have automated regression coverage
3. front-door gratitude/closure/capability paths have automated regression coverage
4. basic production-visible metrics exist for clarification/front-door behavior
5. Mini-phase 6 can start without depending on manual confidence alone

## Mini-phase 6

Active next feature phase after Mini-phase 5.5 hardening.

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

Carry-forward obligations from Mini-phase 5.5:

1. Mini-phase 6.1:
   - promote callable hardening smokes into a more formal CI-grade regression layer
   - add explicit regression protection for previously fixed:
     - pending clarification fresh-query override
     - stale-context gratitude/closure leakage
2. Mini-phase 6.2:
   - evaluate clarification-state mutation under concurrent session writes
   - expand adversarial clarification-state tests
3. these hardening tasks should be treated as explicit Mini-phase 6 carry-forward work, not forgotten residual notes

This phase should also absorb:

1. continuation over recommendation/explanation detail after a valid analytical answer
2. examples like:
   - `give me suggestions in details`
   - `explain that recommendation more`
3. these are not front-door failures and should not be solved by Mini-phase 5 routing logic

Detailed design:

1. Mini-phase 6 is a separate ERP business reasoning lane, not a report family and not a front-door extension
2. it exists for:
   - grounded interpretation
   - grounded explanation
   - bounded ERP-domain recommendation framing
   - recommendation / explanation continuation detail
3. it must never become:
   - a hidden general chatbot lane
   - a fallback for unsupported requests
   - a silent fresh-data retrieval path
4. it requires grounded ERP sources such as:
   - `qwen_grounded_turn_context`
   - normalized family artifact
   - composite grounded artifact
5. it should use two contracts:
   - `ERPBusinessReasoningActivationContract`
   - `ERPBusinessReasoningContract`
6. deterministic authority must remain absolute for:
   - grounded-context existence
   - source-artifact ownership
   - grounding sufficiency
   - lane precedence
   - blocked speculation
7. AI may be used later for:
   - reasoning activation proposal after deterministic eligibility exists
   - natural-language explanation rendering
   - natural-language recommendation rendering within bounded grounded scope
8. Mini-phase 6 should be implemented in slices:
   - 6A activation foundation
   - 6B semantic reasoning activation
   - 6C reasoning execution contract
   - 6D recommendation-detail continuation
9. Mini-phase 6 anti-patterns:
   - no front-door expansion
   - no keyword detection of analysis/explain/recommend
   - no silent fresh-data retrieval from reasoning lane
   - no recommendation text without deterministic grounding sufficiency

Current progress:

1. 6A through 6D are now implemented, and Phase 6 hardening is materially in place
2. a dedicated design document now exists at:
   - `qwen_erp_miniphase6_erp_business_reasoning_design_2026-03-26.md`
3. code foundation now exists for:
   - `ERPBusinessReasoningActivationContract`
   - `ERPBusinessReasoningContract`
   - deterministic reasoning activation context building
   - semantic reasoning activation proposal + governed validation
   - reasoning execution contract + grounded rendering foundation
   - recommendation-detail continuation compatibility + continuation foundation
4. the current 6A/6B/6C foundation is implemented in:
   - `contracts.py`
   - `reasoning_activation.py`
   - `semantic_reasoning_activation.py`
   - `reasoning_execution.py`
   - runtime semantic reasoning activation endpoint
   - runtime ERP business reasoning render endpoint
5. backend probes now pass for:
   - no-grounding -> `not_eligible`
   - grounded artifact context -> `eligible`
   - eligible reasoning activation -> `accepted`
   - grounded reasoning execution -> `answered`
   - grounded reasoning continuation -> `answered`
6. rollout-gated live service routing is now implemented for grounded reasoning turns
7. live rollout smoke now passes:
   - grounded artifact first turn
   - follow-up `what does this mean`
   - second turn routes to `erp_business_reasoning`
8. rollout control currently uses:
   - `qwen_enable_erp_business_reasoning`
   - `qwen_erp_business_reasoning_rollout_percentage`
   - `qwen_erp_business_reasoning_rollout_users`
9. hardening now implemented for Phase 6:
   - reasoning activation is skipped when clarification is pending
   - structured Phase 6 observability events now exist with severity levels:
     - `info`
     - `warning`
     - `error`
   - Phase 6 performance metrics now exist for:
     - `reasoning_activation_latency`
     - `reasoning_execution_latency`
   - callable hardening suite now covers:
     - live rollout path
     - no-grounding refusal boundary
     - front-door gratitude boundary after grounded ERP context
     - continuation-detail source mismatch guardrail
     - observability emission
     - governed recommendation-policy boundary for non-advisory grounded sources
   - recommendation hardening now includes:
     - recommendation recognition is separate from recommendation answerability
     - recommendation allowance comes from governed grounded semantics
     - transactional/document-style grounded sources may still recognize recommendation-shaped asks, but deterministic policy blocks unsafe recommendation answers
     - interpretation/explanation outputs are deterministically stripped of recommendations
     - recommendation objects must cite supported claims via `basis_claim_refs`
     - blocked non-advisory recommendation asks now remain in the reasoning lane and return a bounded guardrail answer instead of falling through to report behavior
     - structural artifact refinements now preempt reasoning lane activation, preventing ranking/column/metric corrections from being hijacked by reasoning continuation
     - continuation-detail answers are now validated for substantive fulfillment so accepted reasoning turns cannot stop at a teaser or dangling lead-in
     - grounded-turn authority now anchors reasoning activation more strongly than “latest appended artifact,” so fresh grounded sources can reset stale reasoning context structurally
     - composite grounded artifacts now preserve explicit source identity for reasoning, including request id, source name, and source report set
     - source-compatible artifact lookup now replaces “latest artifact wins” behavior for reasoning activation
   - post-restart live rollout smoke on the running backend now passes
10. Phase 6 is now closed:
   - the earlier closure-review findings were addressed structurally
   - live backend smokes pass after the final source-authority hardening
   - manual browser confirmation passed on the previously failing AR/AP reasoning flow and the transactional safe-refusal boundary
11. Remaining carry-forward is operational rather than architectural:
   - CI-grade regression promotion is still pending
   - broader adversarial/runtime-failure coverage is still pending
   - broader reasoning coverage beyond the current grounded path still needs hardening

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

1. start Mini-phase 6 on top of the now-closed Mini-phase 5.5 hardening foundation
2. carry 5.5 follow-through explicitly into:
   - Mini-phase 6.1 regression formalization
   - Mini-phase 6.1 observability severity improvements
   - Mini-phase 6.2 clarification-state concurrency review
3. keep clarification resolution as the only owner of pending clarification state

What is explicitly not next:

1. not more front-door expansion right now
2. not more phrase-level patching
3. not hidden dissatisfaction handling inside front door or clarification
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
