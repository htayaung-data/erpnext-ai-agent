# Qwen ERP Conversation Control Post-Design Implementation Roadmap

Status: active roadmap  
Date: 2026-04-18  
Scope: implementation roadmap that converts the completed `CC0` to `CC6` design stack into practical enterprise-grade build slices

Naming note:

1. `CC0` to `CC6` remain the completed design-stack labels
2. `IC1` onward are the implementation-phase labels
3. active progress tracking should now use `IC` labels only

## 1. Purpose

This roadmap converts the completed conversation-control design work into a practical implementation order.

The goal is not to build everything at once.

The goal is to:

1. protect the architecture we just designed
2. deliver value in a safe sequence
3. avoid falling back into single-case fixes
4. keep implementation aligned with the existing ERP assistant ecosystem

## 2. Current Status

### 2.1 Completed Design Slices

1. `CC0`  
   Status: `complete`  
   Contract family foundation

2. `CC1`  
   Status: `complete`  
   Shared conversation-state model

3. `CC2`  
   Status: `complete`  
   Normalization adapter and precedence path

4. `CC3`  
   Status: `complete`  
   Shared control-language taxonomy

5. `CC4`  
   Status: `complete`  
   Recent-focus follow-up activation model

6. `CC5`  
   Status: `complete`  
   Resumable prior-branch restore model

7. `CC6`  
   Status: `complete`  
   Governed multi-step execution model

### 2.2 Implementation Status

1. shared conversation-control runtime integration  
   Status: `in progress`

2. shared metadata activation for control wording  
   Status: `next`

3. cross-family rollout  
   Status: `next`

4. test matrix expansion  
   Status: `next`

### 2.3 Corrected Implementation Status After Code Audit

This section supersedes any stale `next` markers below when the codebase already contains the implementation.

1. `IC1` shared normalization adapter  
   Status: `complete`  
   Notes:
   - normalized conversation snapshot exists in runtime
   - snapshot currently includes pending clarification, latest grounded turn, latest artifact, latest recovery contract, latest repair intent, active sequence, recent focus, and resumable prior request
   - integrity tests already exist

2. `IC2` shared precedence evaluator  
   Status: `close-out review`  
   Notes:
   - typed decision contract exists
   - clarification, sequence, recent-focus, and prior-branch decisions are partially integrated
   - shared arbitration is still incomplete

3. `IC3` shared control-language evidence layer  
   Status: `in progress`  
   Notes:
   - shared evidence classifier exists
   - typed evidence contract exists
   - discard-only, redirect, option-list, sequence, and targeted branch-restore evidence are now shared
   - targeted prior-branch restore matching now also lives in the shared `restore_support.py` seam instead of remaining as a full inline decision block in `service.py`
   - the older top-level clarification-lane module is now only a compatibility facade over the live lane module, reducing duplicate owner behavior risk
   - evidence activation is still uneven across runtime seams

4. `IC4` recent-focus affordance builder  
   Status: `complete`  
   Notes:
   - recent-focus state and continuation decisions exist
   - formal affordance contract and broader cross-family rollout are not complete yet

5. `IC5` prior-branch restore evaluator  
   Status: `in progress`  
   Notes:
   - prior-branch restore contract exists
   - restore modes exist
   - targeted recent-focus restore is now activated through the shared control spine
   - routing is partially integrated and still needs stabilization across runtime owners
   - `IC5-C` now includes active-sequence owner retirement when a newer business-owner turn supersedes a remaining ordered sequence

6. `IC6` multi-step execution generalization  
   Status: `complete for the current delivery chapter`  
   Notes:
   - backward-compatible multi-step assessment bridge exists
   - typed plan, execution-state, and step-result integration contracts now exist
   - clarification pause versus grounded-step advancement now composes through the shared compound-request support layer
   - broader execution generalization should not widen further unless a genuinely new governed multi-step requirement appears

## 3. Enterprise Implementation Principles

All implementation slices below must preserve these principles:

1. one shared control/state model, not family-by-family local memory
2. one shared precedence path, not repeated raw-text ordering in many files
3. wording in metadata where practical, behavior in code
4. explicit state ownership, not hidden state duplication
5. safe replay or requery instead of stale-context guessing

## 4. Implementation Sequence Overview

Recommended implementation order:

1. `IC1` shared normalization adapter
2. `IC2` shared precedence evaluator
3. `IC3` shared control-language evidence layer
4. `IC4` recent-focus affordance builder
5. `IC5` prior-branch restore evaluator
6. `IC6` multi-step execution generalization
7. `IC7` metadata migration and wording unification
8. `IC8` cross-family rollout and coverage matrix

This order is deliberate.

Current execution note:

1. `IC2` is now complete for the current delivery chapter
2. `IC3` is complete for the current delivery chapter after the bounded closure audit
3. `IC4` is complete for the current delivery chapter and should not be reopened without a newly discovered shared gap
4. `IC5-C` and `IC5-D` are complete for the current delivery chapter, so remaining `IC5` work should be limited to truly shared restore-policy seams rather than broad facade churn
5. `IC6-S1` is now complete: the active-sequence compound assessment carries a backward-compatible normalized multi-step bridge through assessment creation, step advancement, completion, and cancellation
6. the next deliberate step is `IC6-S2` typed plan-contract work, while the broader `service.py` refactor remains deferred to its dedicated chapter


We should first build the shared runtime spine, then connect higher-level behaviors to that spine, then complete the metadata and rollout work.

## 5. Detailed Implementation Slices

## 5.1 IC1 Shared Normalization Adapter

Status: `complete`

Purpose:

1. build one normalized conversation-state snapshot from existing owners
2. expose shared state to all later control/follow-up logic

Depends on:

1. `CC1`
2. current clarification state owner
3. current grounded-turn/artifact/recovery helpers

Mini phases:

### IC1-A State Source Inventory

Status: `complete`

Deliverables:

1. exact source map for:
   - pending clarification
   - latest grounded turn
   - latest normalized family artifact
   - latest recovery contract
   - latest compound request assessment

2. adapter field mapping table

### IC1-B ConversationStateSnapshot Builder

Status: `complete`

Deliverables:

1. shared builder/helper for normalized snapshot
2. normalized classes for:
   - pending clarification
   - recent focus
   - active sequence
   - resumable prior request

### IC1-C Snapshot Integrity Tests

Status: `complete`

Deliverables:

1. tests for snapshot creation
2. tests for empty/missing-state behavior
3. tests for owner-boundary preservation

## 5.2 IC2 Shared Precedence Evaluator

Status: `complete for the current delivery chapter`

Purpose:

1. decide control versus business interpretation in one place
2. eliminate scattered precedence drift

Depends on:

1. `IC1`
2. `CC2`

Mini phases:

### IC2-A Decision Contract Introduction

Status: `complete`

Deliverables:

1. shared `ConversationControlDecisionContract`
2. typed decision classes and actions

### IC2-B Clarification/Fresh-Request Alignment

Status: `complete for the current delivery chapter`

Deliverables:

1. move existing clarification precedence into the shared evaluator path
2. preserve current strong behavior:
   - option resolution
   - option list request
   - fresh request override
   - meta-question handling
3. allow explicit master-data breakout from an older pending clarification when the new request clearly changes entity grain, lookup mode, or lookup search text

### IC2-C Sequence/Focus/Branch Precedence Integration

Status: `complete for the current delivery chapter`

Deliverables:

1. active-sequence control integration
2. recent-focus follow-up precedence integration
3. prior-branch restore precedence integration
4. recency-aware arbitration when an older pending clarification competes with a newer grounded business focus
5. generic branch-restore fallback can now restore recent focus, not only pending clarification or repair-origin replay
6. generic branch-restore fallback is now recency-aware for resumable prior branches as well
7. repeated strong-owner control actions are now centralized so recent-focus and sequence seams share the same precedence vocabulary
8. sequence continuation and stop fallback now route through the shared control-language classifier instead of a separate raw-text list
9. completed-sequence acknowledgement is now snapshot-aware and yields when a newer clarification, newer grounded focus, or newer resumable prior branch has become the true latest owner
10. question-restore and branch-restore now share a latest non-clarification owner rule, comparing recent focus and resumable prior branch by snapshot recency instead of hard-wiring one owner first

### IC2-D Shared Precedence Tests

Status: `complete for the current delivery chapter`

Deliverables:

1. tests for stale clarification breakout
2. tests for cross-family new request override
3. tests for continue/stop only when valid
4. tests proving recent-focus continuation yields to stronger shared control owners such as option-list, fresh-request override, sequence resume, and prior-branch restore
5. tests proving completed-sequence acknowledgement does not override newer snapshot owners
6. tests proving question-restore and branch-restore choose the latest eligible non-clarification owner across recent focus and resumable prior branch

## 5.3 IC3 Shared Control-Language Evidence Layer

Status: `complete for the current delivery chapter`

Purpose:

1. normalize business-natural control language into typed evidence classes
2. stop repeating bounded phrase logic in isolated files

Depends on:

1. `IC2`
2. `CC3`

Mini phases:

### IC3-A Shared Evidence Class Registry

Status: `complete for the current delivery chapter`

Deliverables:

1. shared control language classes:
   - option list request
   - clarification resolution
   - override/discard
   - resume prior branch
   - sequence continuation
   - sequence stop
   - recent-focus follow-up
   - meta-question

### IC3-B Existing Helper Migration

Status: `complete for the current delivery chapter`

Deliverables:

1. map current helper functions into shared evidence classification
2. retain bounded evidence logic, but route it through shared contracts

Current implemented notes:

1. discard-prefixed fresh redirects already route through shared evidence
2. discard-prefixed control continuations such as `forget the first question, answer the last question` now also route through shared evidence
3. targeted restore hints such as `go back to the customer` now enter the system through the shared classifier instead of runtime-only phrase branches
4. pending-clarification frontdoor skip now accepts shared control evidence, removing a contract drift where the service already passed that payload but the clarification lane had not yet been aligned
5. clarification-resolution contracts now carry `internal_details`, so shared override payloads such as embedded business messages can survive from clarification resolution into the main control decision layer

### IC3-C Shared Control-Language Tests

Status: `complete for the current delivery chapter`

Deliverables:

1. tests for natural language families
2. tests for strong versus weak evidence
3. tests proving evidence is not final authority without valid state
4. broaden shared-language coverage for business-natural variants such as `answer the last one` and `show the list you found`
5. cover chained natural control turns such as `forget that, answer the last one` and `forget that, go back to the customer`

Current implemented notes:

1. classifier coverage now includes chained discard-to-control turns
2. classifier coverage now includes targeted branch-restore hints
3. regression coverage now includes pending-clarification frontdoor skip honoring shared redirect evidence instead of trapping the user in the old clarification loop
4. live transcript verification now covers discard-prefixed targeted restore, proving the shared control-evidence classifier reaches the same bounded restore path as the plain-language variant
5. live transcript verification now covers discard-prefixed question restore, proving the shared control-evidence classifier reaches the same newer-owner restore path as `answer the last question` without the discard preamble

## 5.4 IC4 Recent-Focus Affordance Builder

Status: `in progress`

Purpose:

1. define what the current focus safely supports next
2. make cross-family follow-up behavior consistent

Depends on:

1. `IC1`
2. `IC2`
3. `CC4`

Mini phases:

### IC4-A Focus Type Inventory

Status: `in progress`

Deliverables:

1. focus-grain mapping for:
   - entity
   - document
   - listing
   - statement
   - report/ranking

Current implemented notes:

1. recent-focus snapshot now derives explicit focus kinds for entity detail, statement, master-data listing, transaction listing, and generic grounded report views
2. listing/report focus is now represented inside the shared snapshot spine instead of staying implicit inside family-local follow-up behavior
3. single-row transaction listings for canonical ERP documents now promote into normalized document focus instead of staying trapped as generic listing focus
4. singular entity/document recent focus can now reuse the shared contextual rewrite seam even when the originating family was master-data or transaction listing rather than only entity-detail
5. document-focused recent-focus inventory is broader now, but this slice remains open until wider live coverage and remaining document-family audit are completed

### IC4-B RecentFocusAffordanceContract Builder

Status: `in progress`

Deliverables:

1. shared affordance builder
2. allowed action classes by focus type
3. local versus requery action separation

Current implemented notes:

1. shared `qwen_recent_focus_affordance_contract` now exists for recent focus
2. affordance builder now separates allowed local follow-up modes from requery follow-up modes
3. recent-focus continuation decisions now attach the shared affordance payload so downstream routing can consume one normalized follow-up surface
4. the shared affordance surface is no longer limited to entity detail and statements; it now derives normalized recent focus for master-data listings, transaction listings, and generic grounded report views as well

### IC4-C Shared Follow-Up Routing

Status: `complete`

Deliverables:

1. route follow-up through shared affordances before family-local rescue logic
2. preserve current strong local grounded transform path

Current implemented notes:

1. shared recent-focus routing now consults the normalized affordance contract before attempting family-local breakout behavior
2. entity-detail local transform remains preserved as the strong local grounded path when the shared affordance allows it
3. listing and report follow-up can now enter the shared recent-focus continuation path even when no family-local runtime rewrite is needed
4. single-row master-data results now promote into entity recent focus, so restored master-data branches can continue through the same bounded entity-detail follow-up path instead of dropping back into a generic listing seam
5. artifact-boundary ownership now accepts the same pending-clarification clear seam as the main runtime path, preventing live lane-signature drift and letting bounded artifact answers clear stale ambiguity state cleanly
6. shared recent-focus runtime rewriting now applies to grounded-follow-up document turns as well, not only new-query turns, so deictic transaction document follow-ups can stay on the bounded recent-focus spine instead of falling back to a fresh listing query
7. recent-focus snapshot precedence now evaluates transaction-listing document promotion before generic entity-grain fallback, preventing purchase-order-style single-row listings from collapsing into supplier/entity focus
8. document-focused recent-context detail requests now normalize into one canonical explicit detail query shape, so natural turns such as tell me more about that purchase order can enter the shared document-detail path instead of re-running a broad listing
9. document-detail evidence follow-up now also honors business-natural status wording through the shared metadata/evidence seam, so turns such as what is the receipt status stay on the grounded purchase-order detail instead of drifting into a fresh report query

### IC4-D Cross-Family Follow-Up Tests

Status: `complete`

Deliverables:

1. entity detail follow-up tests
2. item stock/warehouse follow-up tests
3. statement-switch follow-up tests
4. list-to-detail follow-up tests

Current implemented notes:

1. entity-detail recent-focus follow-up remains covered, including item stock and warehouse phrasing
2. shared-affordance routing tests now cover master-data listing follow-up without local rewrite
3. shared-affordance routing tests now cover transaction-listing to detail-navigation follow-up
4. entity-detail evidence contract coverage now includes business-natural document status wording across sibling document families, including purchase-order receipt status, purchase-order billing status, and sales-order delivery status
5. live financial-statement switch proof now exists on the shared continuation spine, verifying clarification -> Profit and Loss -> Balance Sheet -> Cash Flow without falling back into repeated clarification or losing the governed statement family
6. live master-data list-to-detail proof now exists on the same shared continuation spine, verifying single-row supplier match -> tell me more about that supplier without dropping back into generic listing or artifact-boundary fallback
5. live financial-statement switch proof now exists on the shared continuation spine, verifying clarification -> Profit and Loss -> Balance Sheet -> Cash Flow without falling back into repeated clarification or losing the governed statement family
4. shared-affordance routing tests now cover statement-switch follow-up
5. shared-affordance routing tests now cover report-to-detail navigation follow-up
6. live transcript verification now covers targeted customer restore followed by deictic customer-detail follow-up, proving entity-detail continuity survives a newer ambiguity branch without stale leakage
7. live transcript verification now covers exact item match -> tell me more about that product -> stock-by-warehouse follow-up, proving the master-data singular-focus path can promote into entity detail and then continue through grounded evidence without internal error fallback
8. seeded H3 verification now covers single-row purchase-order listing -> deictic detail follow-up -> receipt-status follow-up, proving transaction singular document focus can promote from listing into document detail and continue through the same bounded follow-up spine

## 5.5 IC5 Prior-Branch Restore Evaluator

Status: `in progress`

Purpose:

1. safely restore a prior branch of work across families
2. align repair, focus restore, clarification restore, and sequence restore

Depends on:

1. `IC1`
2. `IC2`
3. `CC5`

Mini phases:

### IC5-A Prior Branch Snapshot

Status: `complete`

Deliverables:

1. derived snapshot for:
   - current branch
   - resumable prior branch
   - branch kind
   - restore eligibility

### IC5-B PriorBranchRestoreContract

Status: `complete`

Deliverables:

1. shared restore contract
2. restore modes:
   - reopen clarification
   - restore recent focus
   - resume sequence
   - accept recovery action
   - replay as fresh query

### IC5-C Routing To Existing Owners

Status: `in progress`

Deliverables:

1. branch restore routing into:
   - repair lane
   - recent focus path
   - active sequence path
   - clarification path

Current implemented notes:

1. recent-focus targeted restore is now routed through `restore_recent_focus`
2. targeted restore fails closed when no matching recent focus or resumable prior branch exists
3. prior-branch restore decisions now expose normalized focus details for recent-focus restores
4. prior-branch restore routing now passes through shared helper seams for restore-mode detection, runtime override messaging, and direct pending-clarification reopen handling, reducing scattered mode-specific logic inside `handle_qwen_user_message`
5. `restore_recent_focus` now reconstructs a normalized recent-focus snapshot from the restore contract instead of carrying a partial restore-only shape
6. recent-focus restore decisions now attach the shared recent-focus affordance payload, keeping restore and live follow-up on the same bounded continuation surface
7. recent-focus restore contracts now preserve reference-policy fields such as `source_capability`, `deictic_allowed`, and `explicit_named_allowed`
8. weak pending-clarification responses now yield to stronger shared restore owners instead of immediately claiming the turn when a valid non-clarification restore path already exists
9. the pending-clarification lane now accepts the same shared control-evidence contract shape as the main runtime path, removing a live signature drift at the lane boundary
10. targeted recent-focus restore now clears superseded pending clarification state before the restored focus is re-owned by entity-detail routing
11. transaction-listing single-row document focus now preserves document shape through recent-focus restore contracts and runtime restore messaging rather than collapsing back into generic listing phrasing

### IC5-D Branch Restore Tests

Status: `in progress`

Deliverables:

1. tests for `go back`
2. tests for `answer the last question`
3. tests for branch discard and later restore

Current implemented notes:

1. tests now cover targeted restore to recent focus
2. tests now cover targeted restore to resumable prior branch
3. tests now cover discard-prefixed targeted restore evidence
4. tests now cover latest-owner arbitration in both directions between recent focus and resumable prior branch
5. tests now cover recent-focus restore decision normalization for capability/reference-policy fields and shared affordance attachment
6. tests now cover targeted master-data restore preservation of recent-focus reference-policy fields
7. tests now cover weak clarification state yielding to recent-focus restore and sequence-resume control owners
8. live transcript verification now covers ambiguous item -> explicit customer override -> customer detail follow-up without stale ambiguity leakage
9. live transcript verification now also covers ambiguous item -> show me the list -> explicit customer override -> customer detail follow-up without stale ambiguity leakage
10. live transcript verification now covers ambiguous item -> go back to the customer -> tell me more about that customer, proving named restore and restored entity follow-up stay on the same normalized branch
11. discard-prefixed fresh business redirects are now being formalized in live H3 smoke coverage so pending ambiguity cannot silently survive into the new grounded branch
12. live transcript verification now covers `forget that, go back to the customer`, proving discard-prefixed targeted restore shares the same normalized restore path and follow-up continuity as the plain restore form
13. live transcript verification now covers `forget the first question, answer the last question`, proving discard-prefixed question restore shares the same newer-owner selection path as the plain restore form
14. integrity tests now cover transaction-listing document restores explicitly, proving single-row document focus promotion stays aligned with restore payload preservation and restore runtime messaging
15. integrity tests now cover `answer the last question` resolving to the active ordered sequence when that sequence is the latest unresolved business owner, instead of falling back to older recent focus or prior-branch snapshots
16. live transcript verification now covers compound payment-entry listing -> `answer the last question` -> supplier-list resume through the shared prior-branch restore seam
17. live transcript verification now covers discard-prefixed `forget the first question, answer the last question` resuming the same active sequence leg through the shared restore path rather than a separate phrase-local branch
18. replay-as-fresh prior-branch restore now applies the same shared active-sequence cleanup payloads before rerunning the restored branch, instead of leaving sequence retirement behind on the normal front-door path only
19. active-sequence completion now derives from the latest authoritative active owner when a resume restore is in progress, so sequence retirement does not depend on one narrow runtime-message seam
20. live H3 smoke now proves both plain and discard-prefixed `answer the last question` paths retire the active ordered sequence after the final resumed leg completes
21. existing cross-family continuation smokes for financial-statement view switching and single-row master-data list-to-detail follow-up are now promoted into the shared live test suite, so they are enforced matrix coverage instead of helper-only checks
22. ambiguous item match -> `show me the list` -> named item detail -> stock-by-warehouse follow-up is now an explicit live matrix case, covering the more natural option-list path rather than only the exact-item shortcut path
23. discard-prefixed pending-clarification redirect now has explicit cross-family live proof into financial statements, showing the same shared owner seam can leave an item ambiguity branch and land cleanly in Balance Sheet, then continue to Cash Flow without re-entering the earlier ambiguity

## 5.6 IC6 Multi-Step Execution Generalization

Status: `complete for the current delivery chapter`

Purpose:

1. turn current compound request handling into a typed governed multi-step execution system

Depends on:

1. `IC1`
2. `IC2`
3. `IC4`
4. `IC5`
5. `CC6`

Mini phases:

### IC6-A Multi-Step Assessment Generalization

Status: `complete for the current delivery chapter`

Deliverables:

1. extend compound request assessment into multi-step assessment
2. retain current ordered multi-step behavior

### IC6-B Typed Plan Contract

Status: `complete for the current delivery chapter`

Deliverables:

1. typed step plan
2. explicit dependencies
3. explicit carryover classes

### IC6-C Shared Execution State Contract

Status: `complete for the current delivery chapter`

Deliverables:

1. current step
2. remaining steps
3. completed steps
4. waiting/active/cancelled/completed state transitions

### IC6-D Step Result Integration

Status: `complete for the current delivery chapter`

Deliverables:

1. step result contract
2. recent-focus update from step outputs
3. prior-branch preservation when interrupted

### IC6-E Multi-Step Execution Tests

Status: `complete for the current delivery chapter`

Deliverables:

1. ordered two-step tests
2. dependent two-step tests
3. interruption and restore tests
4. clarification-inside-plan tests

### IC6 Entry Slice Plan

Recommended bounded slice order:

#### IC6-S1 Assessment Widening Bridge

Status: `complete`

Goal:

1. widen the current compound-request assessment into a backward-compatible multi-step assessment without changing the user-facing ordered two-step behavior yet

Deliverables:

1. introduce a normalized multi-step assessment payload that can still represent current ordered two-step turns
2. preserve the current compound-request contract as a compatibility surface during the bridge
3. explicitly classify step relationship type such as `independent_ordered`, `dependent_followup`, or `clarification_blocked`
4. fail closed to the current single-step or ordered-two-step behavior when the assessment is not confident

Completed outcome:

1. added a backward-compatible `multi_step_assessment` bridge under the existing compound assessment internal details
2. preserved the current ordered execution contract as the active compatibility surface
3. widened the bridge coherently across initial assessment creation, compiled-step advancement, and service-level completion / cancellation rebuilds
4. added characterization coverage so the bridge is proven through assessment, front-door preservation, advancement, and completion / cancellation state transitions

Anti-drift rules:

1. do not add transcript-local step parsing branches
2. do not bypass current shared control precedence to force a plan
3. do not break current ordered two-step user turns just to introduce the new contract

#### IC6-S2 Typed Step Plan Contract

Status: `complete`

Goal:

1. define one governed plan currency for multi-step execution before broadening execution logic

Deliverables:

1. typed step identifiers
2. explicit step dependency references
3. typed carryover classes such as `entity_reference`, `time_scope`, `projection`, `metric`, and `result_handle`
4. explicit plan-level interruption policy and clarification policy fields

Completed outcome:

1. introduced a first-class typed `qwen_multi_step_execution_plan_contract` in `contracts.py`
2. attached that contract through the shared compound-request assessment builder instead of creating a second entry seam
3. preserved backward compatibility by keeping the typed plan contract static and letting the newer assessment bridge continue to carry execution-progress fields
4. added characterization coverage so the typed plan contract is proven through assessment creation, front-door preservation, advancement carry-forward, and completion / cancellation carry-forward

#### IC6-S3 Shared Execution State Bridge

Status: `complete`

Goal:

1. let the runtime store multi-step progress through one governed execution-state surface instead of expanding ad hoc sequence payloads

Deliverables:

1. current step, remaining steps, completed steps, and waiting state
2. normalized execution transitions: `ready`, `waiting_for_clarification`, `running_step`, `interrupted`, `cancelled`, `completed`
3. compatibility mapping from the current active-sequence payload into the new shared execution-state shape
4. preservation of recent-focus and resumable-prior ownership when execution is interrupted

Completed outcome:

1. introduced a first-class typed `qwen_multi_step_execution_state_contract` in `contracts.py`
2. attached that state contract through the same shared compound-request builder path as the assessment bridge and typed plan contract
3. kept the state contract focused on live progress only, with lifecycle state, current step, remaining steps, completed steps, and last-completed step separated from the static plan definition
4. added characterization coverage so the state contract is proven through assessment creation, front-door preservation, compiled-step advancement, and completion / cancellation transitions

#### IC6-S4 Step Result Integration Bridge

Status: `complete`

Goal:

1. connect step outputs back into the shared conversation-control spine without inventing family-local follow-up logic

Deliverables:

1. typed step-result contract
2. explicit rules for when a step output updates recent focus
3. explicit rules for when a step output becomes carryover for a dependent later step
4. explicit rules for when an interrupted plan preserves the prior branch versus the current step owner

Completed outcome:

1. introduced a typed `qwen_multi_step_step_result_integration_contract` in `contracts.py`
2. attached that result-integration contract from the compiled-turn path after a step yields a grounded result or clarification, instead of relying on implicit legacy sequence behavior
3. made recent-focus promotion, carryover classes, and interruption-owner policy explicit in the integration contract payload
4. added characterization coverage so result integration is proven through the live compound-step execution path and through a pure shared-builder path

#### IC6-S5 Execution Test Matrix

Status: `complete`

Goal:

1. prove the new multi-step bridge works through the existing shared control spine before any broader rollout

Deliverables:

1. ordered two-step compatibility proof
2. dependent-step carryover proof
3. interruption and restore proof
4. clarification-inside-plan proof
5. proof that stronger shared owners such as fresh-request override and restore still supersede a running plan when appropriate

Completed outcome:

1. added a tighter execution-matrix layer proving the multi-step bridge across both grounded-result and clarification-result outcomes
2. moved post-result compound-step transition ownership into shared `compound_request_support.py`, so advancement versus pause-on-clarification is no longer an implicit compiled-path choice
3. hardened the shared assessment bridge so clarification-waiting state preserves the active step instead of blanking the current-step pointer
4. verified the broader focused server-side characterization is green at `397` tests, including compound support, front-door preservation, compiled execution, and post-contract state integrity
5. closure checkpoint outcome: `IC6` is now sufficiently stable to hand control back to the broader mini-phase roadmap instead of widening conversation control further without a new governed execution requirement

## 5.7 IC7 Metadata Migration And Wording Unification

Status: `next`

Purpose:

1. move reusable control wording into metadata-backed templates
2. reduce wording drift and future bilingual pain

Depends on:

1. `IC2`
2. `IC3`
3. partial `IC4`
4. partial `IC5`

Mini phases:

### IC7-A Shared Control Response Template Model

Status: `next`

Deliverables:

1. metadata spec for control prompts and responses

### IC7-B Clarification/Control Wording Alignment

Status: `next`

Deliverables:

1. unify clarification, option-list, stop, resume, and missing-target wording patterns

### IC7-C Wording Migration

Status: `next`

Deliverables:

1. move Python-assembled control wording into metadata where appropriate

## 5.8 IC8 Cross-Family Rollout And Coverage Matrix

Status: `next`

Purpose:

1. roll the shared architecture out across supported families
2. verify no family remains on a private control seam where it should use the shared one

Depends on:

1. `IC1` to `IC7`

Mini phases:

### IC8-A Coverage Matrix

Status: `next`

Deliverables:

1. family-by-family control/follow-up coverage matrix

### IC8-B Family Retrofit Pass

Status: `next`

Deliverables:

1. align customer, supplier, item, document, statement, and listing flows

### IC8-C UAT And Regression Pack

Status: `next`

Deliverables:

1. real chat scenario pack
2. regression set for:
   - ambiguity
   - branch switching
   - follow-up
   - multi-step execution

## 6. Recommended Build Priority

If we want the safest enterprise rollout, the recommended immediate build order is:

1. `IC1`
2. `IC2`
3. `IC4`
4. `IC5`
5. `IC3`
6. `IC6`
7. `IC7`
8. `IC8`

Why this order:

1. state and precedence must come first
2. recent-focus and branch-restore need that spine
3. language taxonomy is most useful once the evaluator exists
4. multi-step generalization should sit on the completed conversation-control spine

## 7. Recommended Current Sprint

The current implementation sprint should stay focused on finishing the shared runtime spine already in progress.

Recommended current sprint scope:

1. `IC2-B`
2. `IC2-C`
3. `IC2-D`
4. `IC3-B`
5. `IC3-C`
6. `IC5-C`
7. `IC5-D`

This is the highest-leverage move now because the codebase already contains the `IC1` foundation and the first `IC2` and `IC3` layers.

If we stabilize this spine before moving on, later `IC4`, `IC6`, `IC7`, and `IC8` work becomes much cleaner.

## 8. Anti-Drift Rules During Implementation

While implementing this roadmap, do not:

1. add new family-local pending state unless explicitly justified
2. add new raw-text control branches without mapping them into shared evidence classes
3. let one family define a private precedence order
4. silently replay stale context when fresh governed replay is safer

## 9. Success Criteria For The Roadmap

This roadmap is successful when the implementation can honestly say:

1. conversation control is no longer scattered across isolated seams
2. cross-family follow-up and branch restore use shared state and precedence
3. multi-step business execution uses typed contracts rather than raw sequencing tricks
4. wording is consistent and ready for future bilingual expansion

## 10. Immediate Next Step

Immediate next step:

1. continue the current shared runtime spine stabilization inside `IC2`, `IC3`, and `IC5`  
   Status: `in progress`

That means:

1. finish shared state arbitration when pending clarification, recent focus, active sequence, and prior-branch restore all compete
2. activate shared control evidence more uniformly across remaining runtime seams
3. expand transcript-level tests for natural business turns such as:
   - ignore that
   - forget the first question
   - answer the last question
   - show me the list
   - go back to the customer
4. only after that, move forward to `IC4` formal affordance rollout and later `IC6`

## 11. Latest Progress Note

Date: `2026-04-19`

Recent enterprise-grade progress:

1. restored the missing shared `conversation_control_language` source module into the live repo
2. realigned `clarification_resolution`, `clarification_lane`, and `service` onto the same shared conversation-control seam
3. widened pending-clarification breakout so explicit master-data requests can safely become new business turns even when heavier cross-checks miss
4. moved targeted verification from pure compile-only checking to real focused unittest coverage for the restored shared module seam
5. hardened shared clarification-yield arbitration so strong restore and sequence owners can safely supersede a weak pending clarification even when no intermediate clarification-response contract is present yet
6. extended recent-focus normalization so document-detail turns such as sales invoices and purchase orders now produce a shared `document` focus kind with its own bounded affordance surface
7. extended shared recent-focus routing so document-detail follow-up now uses the same shared local-transform seam as entity detail, instead of depending on family-local fallback behavior
8. broadened document-follow-up regression coverage so the shared recent-focus seam is now explicitly verified for sales invoice, purchase order, and delivery note detail turns
9. widened shared targeted branch-restore language so document targets such as sales invoice, purchase order, and delivery note now flow through the same restore classifier seam as master-data targets
10. widened shared prior-branch restore runtime shaping so document and listing focus now reroute through natural restore messages such as purchase-order detail, supplier list, and payment-entry list without family-local phrasing
11. realigned the pending-clarification lane with the shared control-evidence seam so live clarification handling no longer drifts from the main service signature during explicit override turns
12. added a live transcript smoke proving that an ambiguous item branch can be replaced by an explicit customer query and then followed by customer detail without stale item ambiguity leaking back
13. added a live transcript smoke proving that the same focus switch still holds after an explicit option-list step, so `show me the list` no longer traps later customer override flow inside the earlier item ambiguity branch
14. widened `resumable_prior_request` from repair-only memory into a shared historical grounded-branch seam, so older grounded business branches can remain restorable even after a newer listing or ordered sequence becomes current focus
15. widened targeted branch restore matching so typed target scope metadata such as `focus_grain=customer` can resolve the right prior branch without depending on branch-label wording alone
16. added integrity proof and live backend smoke showing that a grounded customer detail branch can be recovered through `go back to the customer` after a newer payment-entry ordered sequence has taken focus
17. added discard-prefixed matrix proof for the same owner-transfer seam, showing that `forget that, go back to the customer` now restores the preserved historical customer branch even when a newer ordered sequence is active
18. closed the replay-restore cleanup gap inside `IC5-D`, so `answer the last question` and discard-prefixed resume paths now retire the active ordered sequence through the same shared cleanup contract instead of only through the normal front-door append path
19. added integrity proof that active-sequence completion can fall back to the latest authoritative active owner when the current runtime seam does not carry the active payload directly
20. live backend H3 smoke now passes for both plain and discard-prefixed question-restore resume flows, confirming that shared restore, requery, and sequence-retirement ownership stay aligned end to end
21. promoted the already-implemented financial-statement switch and master-data single-row detail smokes into the shared live unittest surface, tightening the official cross-family continuation matrix without adding new family-local logic
22. added a new live H3 matrix case for ambiguous item option-list continuation into named item detail and warehouse stock follow-up, closing a user-important continuity path without introducing phrase-local runtime logic
23. added a new cross-family live H3 matrix case proving that `ignore that` can discard a pending item ambiguity and redirect cleanly into Balance Sheet, then continue to Cash Flow on the shared financial-statement continuation seam
24. normalized the `reopen_pending_clarification` restore lane onto the same shared front-door artifact seam as the other restore paths, and added live H3 proof that `answer the last question` reopens a pending clarification without dropping semantic-frontdoor or front-door gate audit artifacts
25. added matching live H3 proof for the generic `go back` branch-restore lane, confirming that branch-restore reopen of a pending clarification now uses the same shared front-door artifact seam rather than a phrase-local runtime path
26. added live H3 proof that generic `go back` and discard-prefixed `forget that, go back` both prefer a newer grounded business focus over an older financial-statement clarification, so generic branch-restore precedence now matches the shared owner-arbitration policy already used by question-restore
27. added live H3 proof that generic `go back` and discard-prefixed `forget that, go back` both prefer the newer recent payment-entry focus over an older historical customer branch preserved inside the snapshot, so generic branch-restore now has honest live coverage for recent-focus-vs-historical-prior-focus arbitration as well
28. kept the live-suite registration guard green after widening the H3 matrix, so the new restore-owner proofs are now part of the official live smoke surface instead of ad-hoc local verification
29. added live H3 proof that targeted restore language can replay a resumable accepted prior recovery branch, and that the replay stays on the semantic customer-ranking branch even when the current governed route materializes through `Sales Analytics` instead of the literal legacy report name
30. added matching discard-prefixed live H3 proof for that same accepted-recovery restore seam, so softer natural discard wording now shares the same targeted resumable-branch path instead of relying on a separate phrase-local branch
31. added live H3 proof that targeted restore can replay an accepted prior recovery branch even while a newer active sequence owns the current turn, and that the same restore retires the active sequence cleanly instead of leaving two owners alive
32. added matching discard-prefixed live H3 proof for that active-sequence collision, so both direct and discard-prefixed targeted restore now share the same accepted-recovery replay plus sequence-retirement seam
33. added live H3 proof that softer chained discard redirect wording like `ignore that show me suppliers` clears pending ambiguity and switches cleanly into a fresh supplier owner through the same shared redirect seam
34. added live H3 proof that pronoun-discard question-restore wording like `forget it answer the last question` resumes the still-valid active sequence through the same shared question-restore seam
35. added live H3 proof that pronoun-discard targeted-restore wording like `ignore this and go back to the customer` restores the preserved customer branch over a newer active sequence through the same shared targeted-restore seam
36. added live H3 proof that richer option-list wording like `show me the list that you found` stays on the same ambiguous-item candidate set and still supports downstream detail plus stock follow-up
Current meaning for roadmap status:

1. `IC5-C` is complete for the current delivery chapter, and the shared owner-precedence seam is stronger and more honest at source level
2. `IC4-C` is complete: shared recent-focus routing covers single-row document detail continuation and live seeded proof now passes through both detail follow-up and natural receipt-status follow-up
3. `IC4-D` is complete: cross-family proof now covers item stock follow-up, transaction document continuation, financial-statement switch continuation, and master-data list-to-detail continuation on the shared follow-up spine
4. the reopen-pending-clarification restore lane is now aligned to the shared front-door artifact seam instead of remaining a thinner special-case restore branch
5. both `question_restore` and generic `branch_restore` now have live H3 proof for pending-clarification reopen on that same shared seam
6. generic branch-restore and discard-prefixed generic branch-restore now also have live H3 proof that newer business focus beats older pending clarification on the shared owner-arbitration seam
7. generic branch-restore and discard-prefixed generic branch-restore now also have live H3 proof that newer recent focus beats an older historical prior branch preserved in the snapshot
8. targeted restore and discard-prefixed targeted restore now also have live H3 proof for replaying resumable accepted prior recovery branches through the shared targeted-resumable restore seam
9. targeted restore and discard-prefixed targeted restore now also have live H3 proof that the same accepted-recovery replay still works cleanly when a newer active sequence is present, and that the older active sequence is retired in that same restore turn
10. the collection-vs-detail targeted-restore gap is now closed for the current safe families, including plural directory-style wording such as supplier directories over newer supplier detail
11. `IC4-A` / `IC4-B` are now complete for the current delivery chapter after the closure audit confirmed no genuinely uncovered standard recent-focus inventory or affordance seam remained
12. the next practical step is to finish `IC3`, then finish `IC2`, while keeping `IC5-C` closed unless a truly new shared routing gap appears, and only then choose the deliberate hand-off into `IC6` versus the later dedicated `service.py` refactor chapter

37. extracted shared restore-interpretation helpers into `conversation_control_language.py`, covering control-evidence internal-detail tagging, targeted restore hint extraction from evidence or message, and control-action-to-restore-phrase mapping
38. rewired `service.py` to consume those shared helpers instead of keeping that restore-interpretation logic inline inside the prior-branch restore snapshot builder
39. added characterization coverage for that seam inside the shared control-language matrix, and the live server-side suite is green at `382` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
40. this keeps the project in the intended enterprise direction: `IC5-C` stays closed except for genuinely shared restore-policy gaps, while `IC3` continues to absorb the remaining shared control-language ownership that should not live in the facade

41. extracted shared clarification-yield override gating into `conversation_control_support.py`, covering the clarification-decision allow-list plus the shared initial-control and current-control yield gates that sit above the already-shared owner selectors
42. rewired `service.py` to consume those shared clarification-yield helpers instead of keeping that override policy inline around the pending-clarification and clarification-response control seam
43. added direct characterization for that seam in the shared state-integrity matrix, and the live server-side suite is green at `385` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
44. this keeps the project on the intended enterprise path: we are still finishing `IC3` shared owner-activation cleanup rather than reopening `IC5-C`, and the remaining work is now a smaller set of control/clarification interaction seams rather than family-local phrase logic

45. extracted the clarification-response decision-spec matrix into `conversation_control_support.py`, covering the shared mapping from clarification outcome into normalized conversation-control decision class, action, resolved business message, clear-pending flag, and internal-detail patching
46. rewired `service.py` to consume that shared clarification-response decision spec while keeping only the common contract envelope assembly around the clarification-resolution contract itself
47. added direct characterization for that decision-spec seam in the shared state-integrity matrix, and the live server-side suite is green at `386` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
48. this keeps the project on the intended enterprise path: we are still shrinking shared owner-activation policy out of the facade under `IC3`, rather than reopening `IC5-C` or drifting into transcript-local clarification behavior

49. extracted clarified-turn reentry and reset predicates into `conversation_control_support.py`, covering resolved-slot payload normalization, front-door clarification reentry message selection, artifact-boundary runtime-reset gating, and front-door fresh-query-reset gating
50. rewired `service.py` to consume those shared clarified-turn policy helpers while intentionally keeping the final clarified-turn state application and entity-drilldown recomputation inside the facade as orchestration work
51. added direct characterization for that reentry/reset seam in the shared state-integrity matrix, and the live server-side suite is green at `387` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
52. this keeps the project on the intended enterprise path: we are still shrinking shared owner-activation and clarification policy out of the facade under `IC3`, while deliberately leaving pure state-application wiring in `service.py` until the later dedicated facade refactor chapter

53. extracted clarified runtime-message resolution into `conversation_control_support.py`, covering the shared mapping from clarification outcome into either a direct fresh business message or a resolved continuation message for clarified follow-up turns
54. rewired `service.py` to consume that shared clarified runtime-message helper while keeping only the surrounding clarification-decision contract assembly and clarified-turn orchestration in the facade
55. added direct characterization for that runtime-message seam in the shared state-integrity matrix, and the live server-side suite is green at `388` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
56. this keeps the project on the intended enterprise path: we are still extracting reusable clarification/control policy under `IC3`, while keeping the facade responsible only for orchestration and avoiding another reopen of `IC5-C`

57. extracted pending-clarification fallback precedence into `restore_support.py`, exposing the shared non-authoritative-fallback, restore-authoritative, and candidate-precedes-pending helpers instead of keeping a second local copy in `service.py`
58. rewired `service.py` to consume those shared precedence helpers while leaving the broader snapshot assembly and state-loading orchestration in the facade
59. added direct characterization for that precedence seam in `test_restore_support_contracts.py`, and the live server-side suite is green at `389` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
60. this keeps the project on the intended enterprise path: we are still removing real duplicated shared policy under `IC3`, rather than inventing a new one-off extraction just to reduce line count in `service.py`

61. extracted completed-sequence supersession precedence into `conversation_control_support.py`, covering the shared policy that decides when a finished or cancelled active sequence must yield to a newer authoritative pending clarification, recent focus, or resumable prior branch preserved in snapshot state
62. rewired `service.py` to consume that shared completion-supersession selector while intentionally keeping the surrounding snapshot readout and completion-answer orchestration inside the facade
63. added direct characterization for that shared selector in the state-integrity suite, and the live server-side suite is green at `390` tests including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
64. this keeps the project on the intended enterprise path: we are still extracting real shared precedence policy under `IC3`, while leaving snapshot plumbing and answer orchestration in `service.py` until the later dedicated facade refactor chapter

65. completed a bounded `IC3` closure audit after the shared completion-supersession extraction and confirmed the remaining `service.py` clarification/control seams are fa?ade adapters or state-application orchestration, not missing shared policy
66. explicit decision: stop `IC3` extraction at this point for the current chapter so we do not trade enterprise alignment for low-value facade churn
67. next move: take `IC3` as ready for closure review, resume the queued `IC2` close-out work, and defer any broader service-stage cleanup to the later dedicated `service.py` refactor chapter

68. completed the `IC2` close-out review and confirmed that the current chapter now has shared precedence coverage for clarification breakout, fresh-request override, strong-owner suppression, sequence completion gating, recent-focus suppression, and question-restore / branch-restore latest-owner arbitration
69. explicit decision: treat `IC2` as complete for the current delivery chapter because the remaining open work is future-family expansion and facade-stage cleanup, not missing shared precedence policy
70. next move: keep `IC3` ready for closure review and make the deliberate hand-off choice between `IC6` entry work and the later dedicated `service.py` refactor chapter

71. completed the `IC3` closure review and confirmed that the current chapter now has shared control-language coverage across clarification interaction, redirect/discard, option-list request, question restore, targeted restore, sequence continuation, and sequence stop for the current supported surface
72. explicit decision: treat `IC3` as complete for the current delivery chapter because the remaining open work is future language breadth and facade-stage cleanup, not missing shared control-language policy
73. designed the bounded `IC6` entry slice plan so the next chapter can begin with assessment widening and typed plan/state contracts instead of drifting into unbounded multi-step execution changes
74. completed `IC6-S1` by introducing a backward-compatible normalized `multi_step_assessment` bridge for compound ordered execution, while intentionally keeping the legacy compound-request assessment contract as the live compatibility surface
75. widened that bridge across assessment creation, compiled-step advancement, and service-level completion / cancellation rebuilds, then verified the server-side characterization suite is green at `393` targeted tests
76. completed `IC6-S2` by introducing a typed `qwen_multi_step_execution_plan_contract` with governed step ids, dependency edges, carryover classes, interruption policy, and clarification policy while keeping execution progress out of the plan contract itself
77. attached that typed plan through the shared compound-request builder so the plan survives front-door preservation, compiled-step advancement, and service-level completion / cancellation without adding a parallel service-local seam
78. completed `IC6-S3` by introducing a typed `qwen_multi_step_execution_state_contract` with governed lifecycle state, current-step focus, remaining steps, completed steps, and last-completed-step tracking while keeping plan definition separate in the static typed plan contract
79. attached that execution-state contract through the shared compound-request builder so state survives assessment creation, front-door preservation, compiled-step advancement, and service-level completion / cancellation without adding a parallel orchestration-only state seam
80. completed `IC6-S4` by introducing a typed `qwen_multi_step_step_result_integration_contract` that makes recent-focus promotion, carryover classes, and interruption-owner policy explicit when a compound step yields a grounded result or clarification
81. attached that integration contract through the compiled-turn execution path and the shared multi-step support layer, then verified the focused server-side suite is green at `394` tests
82. completed `IC6-S5` by tightening the multi-step execution matrix across grounded-result and clarification-result paths, and by moving post-result advancement-versus-pause behavior into the shared compound-request support layer instead of leaving it implicit in the compiled path
83. focused server-side characterization is green at `397` tests after the `IC6-S5` pass, proving the assessment, plan, execution-state, and result-integration contracts stay coherent through front-door preservation, compiled-step execution, clarification pause, and post-contract state integrity
84. completed the `IC6` closure checkpoint and confirmed the conversation-control delivery chapter can return cleanly to the broader mini-phase roadmap without more `IC6` widening
85. immediate next program step: resume the main Phase B1 + C1 backbone work, using the now-stabilized conversation-control spine as shared infrastructure instead of keeping it as the active build center
