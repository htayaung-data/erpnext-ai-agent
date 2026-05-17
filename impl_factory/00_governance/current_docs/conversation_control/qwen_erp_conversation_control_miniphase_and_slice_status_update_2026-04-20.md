# Qwen ERP Conversation Control Mini-Phase And Slice Status Update

Status: active technical update
Date: 2026-04-20
Scope: current implementation truth snapshot for conversation-control work inside main Phase C, covering mini-phase status, slice status, completed work, current position, and next required work

## 1. Purpose

This note is a practical status snapshot.

It exists to answer these questions clearly:

1. what we have already finished
2. where we are now
3. what is still open
4. what we should do next in the correct order

This note is not a replacement for the roadmap.

The roadmap remains the long-lived structure. This note is the execution snapshot after the recent `IC4` and `IC5` implementation slices and live H3 verification work.

## 2. Position In The Overall Program

We are inside main Phase C work, not starting a new roadmap.

The active implementation context is:

1. `CC0` to `CC6` design stack: complete
2. implementation stack is now tracked with `IC` labels
3. current practical focus is still the conversation-control implementation spine
4. we are not yet done with the `IC` series
5. the most active implementation area right now is the overlap between:
   - `IC3` shared control-language owner-activation closure
   - `IC5` prior-branch restore seam cleanup and stabilization

In simple terms:

1. the design work is already done
2. the implementation work is partly done
3. we are currently hardening the shared runtime behavior so business-natural follow-up and restore behavior works safely across families

## 3. Current Executive Summary

What is already strong now:

1. recent focus is no longer only an entity-detail idea; it now covers master-data listings, transaction listings, statements, and generic grounded report views
2. recent-focus continuation is now routed through a shared affordance contract instead of scattered family-local assumptions
3. prior-branch restore behavior is much broader and more honest than before
4. live H3 proof now exists for many natural business turns that previously drifted, stalled, or leaked stale contex
5. softer discard language and pronoun discard language are now proven through the shared continuation/restore seam instead of narrow phrase-local fixes
6. targeted prior-branch restore matching logic is no longer owned only by the `service.py` facade; the shared `restore_support.py` seam now owns the matching behavior, with focused pure-unit coverage
7. clarification-lane ownership is now cleaner as well: the older top-level `qwen_chat/clarification_lane.py` module is reduced to a compatibility facade over `qwen_chat/lanes/clarification_lane.py`, preventing a second clarification-lane behavior copy from drifting separately

What is still not fully closed:

1. `IC4` is now complete for the current delivery chapter: recent-focus inventory and affordance policy are broadly shared, matrix-covered, and no genuinely uncovered standard focus seam was found in the closure audi
2. `IC5-C` is now complete for the current delivery chapter; the remaining restore-related surface is mostly facade orchestration and should defer to the later dedicated `service.py` refactor chapter unless a genuinely new shared policy gap appears
3. `IC6` is now complete for the current delivery chapter: bounded entry slices delivered the governed multi-step assessment, plan, execution-state, and step-result integration layer with clarification-pause stability and focused server-side proof
4. the next useful work is no longer more conversation-control widening; it is to return to the broader Phase B1 + C1 backbone roadmap while keeping this control spine as shared infrastructure

Most important current open gap:

1. the original collection-vs-detail targeted restore seam is now closed for the current safe families, including shared collection-alias wording such as `supplier directory` and `supplier directories`
2. the current conversation-control checkpoint is now strong enough that we should stop widening `IC6` by default and hand control back to the broader enterprise roadmap
3. remaining payment-entry detail-lane limitations still belong to governed family/scope rollout work, not to more local conversation-control patching

## 4. Mini-Phase Status Snapsho

## 4.1 Completed Design Mini-Phases

These are complete and should remain treated as design foundation:

1. `CC0`: complete
2. `CC1`: complete
3. `CC2`: complete
4. `CC3`: complete
5. `CC4`: complete
6. `CC5`: complete
7. `CC6`: complete

Meaning:

1. we are not designing the model from zero anymore
2. we are implementing and hardening the model

## 4.2 Implementation Mini-Phase Status

### `IC1` Shared Normalization Adapter

Status: complete

What is done:

1. shared conversation-state snapshot exists
2. snapshot includes:
   - pending clarification
   - latest grounded turn
   - latest normalized artifac
   - latest recovery contrac
   - latest repair inten
   - active sequence
   - recent focus
   - resumable prior reques
3. integrity tests already exis

### `IC2` Shared Precedence Evaluator

Status: complete for the current delivery chapter

What is done:

1. typed conversation-control decision contract exists
2. clarification, sequence, recent-focus, and prior-branch decisions are no longer purely local
3. latest-owner arbitration is stronger than before

What is still open:

1. broader future-family expansion belongs to later mini phases rather than to the current shared precedence spine
2. remaining facade-stage cleanup belongs to the later dedicated `service.py` refactor chapter, not to `IC2` policy work

### `IC3` Shared Control-Language Evidence Layer

Status: complete for the current delivery chapter

What is done:

1. shared classifier exists
2. typed evidence contract exists
3. shared evidence now covers:
   - discard prefix
   - fresh redirec
   - option-list reques
   - sequence continuation
   - targeted restore
   - question restore
4. shared control-language evidence now also recognizes polite and natural variants for the same governed control classes, including:
   - `answer the last question please`
   - `repeat the last request please`
   - `go back to that question`
   - `go ahead with the next one`
   - `continue with that`
   - `stop this sequence`
5. integrity coverage now proves those broader variants flow through the same shared classifier and the same sequence-control helper seams without introducing family-local logic

What is still open:

1. broader future-language breadth belongs to later `IC7` and `IC8` expansion rather than to the current `IC3` control-language spine
2. remaining facade-stage adapter cleanup belongs to the later dedicated `service.py` refactor chapter, not to `IC3` policy work

Closure basis:

1. shared control-language evidence is now active across clarification, redirect, option-list, question-restore, targeted-restore, sequence continuation, and sequence stop paths for the current delivery chapter
2. the bounded `IC3` closure audit confirmed that the remaining `service.py` seams are adapter-or-orchestration bridges, not missing shared control-language policy
3. live integrity coverage is green after the latest `IC3` extraction pass, so the chapter can move forward without reopening phrase-local cleanup

### `IC4` Recent-Focus Affordance Builder

Status: complete

#### `IC4-A` Focus Type Inventory

Status: complete

Done:

1. recent focus now derives explicit focus kinds for:
   - entity detail
   - statements
   - master-data listings
   - transaction listings
   - generic grounded report views
2. single-row transaction listings can promote into normalized document focus
3. single-row master-data results can promote into normalized entity focus
4. integrity coverage now characterizes single-row transaction-listing promotion for:
   - payment entry
   - purchase order
   - sales order
   - delivery note
   - purchase receip
   - purchase invoice
5. integrity coverage now also characterizes broader recent-focus listing inventory across representative governed list families:
   - `Item Master List`
   - `Sales Order List`
   - `Purchase Invoice List`
6. integrity coverage now also characterizes the remaining active governed listing/master families for the current matrix:
   - `Customer Master List`
   - `Sales Invoice List`
   - `Delivery Note List`
   - `Purchase Order List`

Closure basis:

1. the governed matrix now explicitly covers the supported statement, listing, document-detail, entity-detail, and generic-report focus classes
2. the remaining inline recent-focus code in `service.py` is limited to orchestration, single-row promotion, targeted-restore matching, and historical carryover glue rather than a second hidden inventory-policy surface
3. no genuinely uncovered standard document/report inventory edge was found during the close-out audi

#### `IC4-B` RecentFocusAffordanceContract Builder

Status: complete

Done:

1. shared `qwen_recent_focus_affordance_contract` exists
2. local follow-up modes and requery follow-up modes are separated
3. continuation decisions now carry the affordance payload
4. the affordance surface is broader than before and no longer limited to entity detail or statements
5. recent-focus affordance now has a conservative shared fallback for listing, statement, and report focus when the display report name is generated or not explicitly registry-backed
6. approved report follow-up modes are now normalized into the runtime continuation vocabulary, so registry labels such as `column_projection` and `metric_change` do not drift away from runtime-local modes like `column_refinement` and `metric_refinement`
7. integrity coverage now proves recent-focus snapshot and affordance behavior for:
   - master-data listing
   - transaction listing
   - document detail
   - statement view
   - report view
8. integrity coverage now also proves canonical mode normalization for:
   - listing affordance from `Supplier Master List`
   - report affordance from `Gross Profit`
   - follow-up resolution alias normalization from semantic follow-up input into runtime follow-up modes
9. governed listing affordance policy now composes two governed sources instead of treating one as the whole truth:
   - scope-family compatibility policy for cross-family-safe follow-up boundary behavior
   - report-approved follow-up modes for listing-local refinement behavior
10. listing affordance scope resolution now prefers governed report-backed scope identity before falling back to grain heuristics, which prevents master-data listings from being misread as entity-only scope when the real governed source is a listing repor
11. live backend verification now proves that:
   - transaction listings such as `Payment Entry List` expose the governed requery-safe and local-safe follow-up surface together
   - master-data listings such as `Supplier Master List` expose bounded local column/sort refinement without losing the shared follow-up boundary contrac
12. the live full `test_post_contract_state_integrity` suite is green at `201` tests after this slice
13. listing-scope resolution is now slightly more future-proof because `scope_id_for_listing_view` can fall back to an active approved governed scope with the same id when the explicit listing-view map has not yet been expanded, and live coverage now proves representative governed affordance composition for:
   - `Item Master List`
   - `Sales Order List`
   - `Purchase Invoice List`
14. live affordance coverage now also proves the remaining active governed listing/master families for the current matrix:
   - `Customer Master List`
   - `Sales Invoice List`
   - `Delivery Note List`
   - `Purchase Order List`
15. broader governed report-family coverage now also proves representative shared report-focus behavior for:
   - aging summaries via `Accounts Receivable Summary`
   - inventory snapshots via `Stock Balance`
   - trend analytics via `Delivery Note Trends`
16. broader governed report-family coverage now also proves:
   - aging sibling coverage via `Accounts Payable Summary`
   - financial/trend analytics coverage via `Sales Analytics`
17. broader governed report-family coverage now also proves:
   - non-summary aging coverage via `Accounts Payable`
   - warehouse-oriented inventory snapshot coverage via `Warehouse Wise Stock Balance`
   - product history coverage via `Item-wise Sales History`
18. broader governed report-family coverage now also proves:
   - non-summary receivable aging coverage via `Accounts Receivable`
   - direct-query item-line report fallback behavior via `Sales Order Item List`
   - direct-query item-line report fallback behavior via `Sales Invoice Item List`

Closure basis:

1. the standard recent-focus affordance surface for supported focus classes now composes through the shared support layer and the broad state-integrity matrix already proves that surface across statements, listings, detail views, and generic reports
2. the remaining recent-focus code inside `service.py` is orchestration glue rather than a second affordance-policy implementation and belongs to the later dedicated `service.py` refactor chapter, not to another `IC4-B` policy slice

#### `IC4-C` Shared Follow-Up Routing

Status: complete

Done:

1. shared affordance routing runs before family-local rescue logic
2. entity-detail local transform remains preserved
3. listing and report follow-up can use the shared recent-focus continuation path
4. single-row master-data results can continue through bounded entity-detail follow-up
5. grounded document follow-up can stay on the shared recent-focus spine
6. natural document status follow-up is now normalized into shared document-detail continuation

#### `IC4-D` Cross-Family Follow-Up Tests

Status: complete

Done:

1. entity-detail follow-up coverage exists
2. item stock and warehouse follow-up coverage exists
3. financial statement switch coverage exists
4. master-data list-to-detail coverage exists
5. transaction listing to document detail coverage exists
6. document status follow-up coverage exists for sibling document families

### `IC5` Prior-Branch Restore Evaluator

Status: in progress

#### `IC5-A` Prior Branch Snapsho

Status: complete

Done:

1. resumable prior branch snapshot exists
2. restore eligibility state exists
3. branch kind typing exists

#### `IC5-B` PriorBranchRestoreContrac

Status: complete

Done:

1. shared restore contract exists
2. restore modes exist for:
   - reopen clarification
   - restore recent focus
   - resume sequence
   - accept recovery action
   - replay as fresh query

#### `IC5-C` Routing To Existing Owners

Status: complete

Done:

1. targeted recent-focus restore is routed through the shared control spine
2. restore contracts preserve focus details and reference-policy fields
3. targeted recent-focus restore clears superseded pending clarification
4. restore and recent-focus continuation now share the same bounded affordance surface
5. newer business-owner turns can retire older active sequences cleanly
6. accepted prior recovery replay is now proven through shared targeted restore paths
7. targeted restore evidence now carries explicit requested focus kind metadata, not only target grain
8. targeted restore arbitration now checks requested focus kind as well as target grain, so collection restore can prefer a historical listing branch over a newer detail branch when the user explicitly asks for the collection
9. targeted restore over resumable prior branches is now less brittle for accepted recovery origins because non-semantic branch kinds such as `accepted_recovery_origin` no longer block a valid targeted restore when the preserved branch still matches by governed family or grain
10. branch-owned recency for recent focus is now normalized from the latest relevant contributor, not only the first grounded-turn position:
   - grounded turn
   - compatible artifac
   - matching recovery contrac
11. question and branch restore arbitration can now keep a grounded branch ahead of an older pending clarification when the branch's later compatible artifact or recovery payload is the true latest contributor
12. accepted-recovery resumable prior branches now also normalize their source index from the latest branch-owned contributor, not only the repair-acceptance event:
   - prior recovery contrac
   - accepted repair inten
   - newer grounded turn proving the branch became resumable
13. snapshot arbitration between accepted-recovery-origin branches and historical prior-focus branches is now less brittle because the accepted-recovery branch can carry the truthful later contributor index instead of appearing artificially older than it really is
14. non-clarification restore ownership is now less brittle when pending clarification survives only through message fallback with no usable source index:
   - active sequence can now precede a non-authoritative fallback clarification when the sequence still has a known current source index
   - recent focus can now precede a non-authoritative fallback clarification when the grounded branch still has a known current source index
   - resumable prior branch can now precede a non-authoritative fallback clarification when the preserved branch still has a known current source index
15. completed/cancelled active-sequence completion handling now uses the same non-authoritative clarification rule, so a message-fallback pending clarification with no usable source index no longer suppresses sequence-completion acknowledgement by itself
16. direct restore fallback no longer reopens a non-authoritative message-fallback clarification when no stronger owner exists, so shared restore does not revive a weak clarification stub as if it were authoritative
17. recent-focus versus resumable-prior owner arbitration now also prefers a known indexed owner over an otherwise-available but unindexed owner, instead of silently defaulting to recent focus whenever raw recency is not comparable
18. latest-repair-intent snapshot state now also carries normalized `source_tool_index`, so repair evidence is as explicit and auditable as the other owner-relevant snapshot states
19. peer-owner arbitration now also records when recent focus wins only by explicit default because precedence is indeterminate, instead of mislabeling that outcome as if a stronger known-versus-unindexed rule had fired
20. resumable-prior snapshot selection is now routed through an explicit shared selector that records why accepted repair or historical prior focus won, instead of silently relying on inline branch-choice defaults
21. non-clarification restore owner selection is now also routed through an explicit shared selector, so winner and basis come from one seam instead of split helper/default logic
22. compound-completion reentry eligibility now also uses an explicit shared selector across completion-answer presence, continuation-control evidence, and supported completion status, so sequence-completion reentry no longer hides that route gating inline
23. compound-completion reentry response selection now also uses one shared selector across status-to-answer mapping, decision-action mapping, and eligibility gating, so completion-answer wording and completion-decision routing no longer drift across separate inline seams
24. prior-branch restore snapshot routing now also uses an explicit shared selector across targeted restore, latest non-clarification ownership, authoritative pending clarification, and direct fallback, so restore-route precedence no longer lives as a mostly inline builder sequence
25. prior-branch restore projection now also uses one shared selector across runtime override messaging, recent-focus target enrichment, and recent-focus affordance attachment, so restore-mode-specific decision shaping no longer lives separately in both runtime-message and decision-mapping seams
26. prior-branch direct handler routing now also uses an explicit shared selector and dispatcher across reopen-pending-clarification and replay-as-fresh-query modes, so top-level restore execution no longer depends on ordered inline trial logic in the conversation-control spine
27. prior-branch restore decision classification now also uses one shared selector across reopen-pending-clarification, resume-active-sequence, and non-clarification override states, so multiple control selectors no longer re-implement that restore-action branching inline

Closure note:

1. broader collection/detail restore matrix coverage is no longer the main open gap for the current safe families
2. some restore routing still meets older runtime seams, but the remaining surface now looks much more like facade orchestration than reusable shared policy
3. the final thin restore-helper reconstruction seams are now directly characterized in the live state-integrity suite, so the remaining work is better classified as later facade refactor work than current shared-policy incompleteness
4. the practical focus should now shift back to unfinished `IC4-A` / `IC4-B` closure work and later dedicated `service.py` refactor work for the remaining orchestration gravity

#### `IC5-D` Branch Restore Tests

Status: complete

Done:

1. restore tests exist for:
   - `go back`
   - `answer the last question`
   - discard-prefixed restore
   - targeted restore
   - active sequence resume
   - accepted prior recovery replay
2. live H3 proof now covers multiple cross-family restore scenarios
3. dedicated H3 collection-over-detail targeted-restore smokes are now implemented, registered, and proven in the governed bench runtime for supplier and customer collection restores
4. dedicated H3 collection-over-detail targeted-restore smokes are now implemented, registered, and proven in the governed bench runtime for item collection restore over newer item detail in both plain and discard-prefixed forms
5. dedicated H3 transaction-listing targeted-restore smokes are now implemented, registered, and proven in the governed bench runtime for:
   - sales invoice listing restore over newer sales invoice detail
   - purchase order listing restore over newer purchase order detail
6. restore coverage also includes:
   - cross-listing targeted restore
   - discard-prefixed cross-listing targeted restore
   - pronoun discard targeted restore over active sequence
   - targeted restore replay of resumable prior recovery
   - targeted restore replay of resumable prior recovery over active sequence

Closure basis:

1. the shared restore matrix is now broad enough to treat `IC5-D` as complete for the current safe families and restore classes we actively suppor
2. remaining work belongs to `IC5-C` routing cleanup and future-family expansion, not to missing branch-restore test coverage for the current supported seam

### `IC6` Multi-Step Execution Generalization

Status: complete for the current delivery chapter

Done:

1. current compound request support is now widened through a backward-compatible multi-step assessment bridge
2. typed plan, execution-state, and step-result integration contracts are now attached through the shared compound-request support layer
3. clarification pause versus grounded-result advancement is now shared behavior, not an implicit compiled-path branch
4. focused server-side characterization is green at `397` tests across compound support, front-door preservation, compiled execution, and post-contract state integrity

Still open:

1. broader future multi-step breadth still belongs to a later governed execution chapter if and when new approved execution patterns require i
2. the dedicated `service.py` refactor remains separate work and should not be smuggled back into `IC6`

## 5. Slice Status Snapsho

This section records the practical slice sequence we recently completed or attempted.

## 5.1 Slices Finished And Kep

### Slice: Shared Recent-Focus Expansion

Status: complete

What we did:

1. expanded recent-focus derivation beyond entity detail and statements
2. included master-data listings, transaction listings, and generic grounded report views
3. attached normalized affordance metadata to recent-focus continuation decisions

Why it matters:

1. follow-up behavior now has one shared normalized surface
2. this reduces family-local guessing

### Slice: Recent-Focus Affordance Fallback Hardening

Status: complete

What we did:

1. added a conservative fallback policy for recent-focus affordance when the current focus is:
   - listing
   - statemen
   - repor
   and the display report name is not explicitly registry-backed
2. the fallback allows only shared requery continuation (`new_query`), not broad local transform permissions
3. corrected the report-focus characterization coverage so it aligns with real governed ranking/report family metadata instead of an invented report/capability pair
4. added integrity coverage for:
   - report-focus shared-affordance passthrough
   - report snapshot affordance
   - statement snapshot affordance
   - transaction-listing snapshot affordance

Why it matters:

1. recent-focus policy now degrades safely for generated or family-backed report labels instead of collapsing to no follow-up surface
2. this is a shared affordance-policy fix, not a report-specific or wording-specific patch
3. it moves `IC4-B` forward with real policy hardening rather than only more restore-matrix work

### Slice: Recent-Focus Affordance Helper Extraction

Status: complete

What we did:

1. extracted recent-focus affordance policy helpers out of `service.py` into a dedicated shared helper module
2. kept the `service.py` affordance entrypoint stable so the orchestration facade still exposes the same runtime seam
3. preserved the existing affordance contract shape and recent-focus behavior
4. re-verified the full `test_post_contract_state_integrity` suite in the live backend container after the extraction

Why it matters:

1. this reduces `service.py` role mixing without interrupting the current `IC` delivery wave
2. it follows the controlled refactor guidance instead of adding more recent-focus policy gravity to the facade
3. it proves we can keep shipping `IC4` / `IC5` work while also leaving behind real extraction seams

### Slice: Transaction-Document Recent-Focus Inventory Characterization

Status: complete

What we did:

1. added integrity coverage for the remaining supported single-row transaction-listing document promotions
2. the inventory characterization now explicitly proves recent-focus document promotion for:
   - sales order
   - delivery note
   - purchase receip
   - purchase invoice
3. together with the earlier coverage, the shared transaction-document focus inventory is now much less implicit in code

Why it matters:

1. `IC4-A` is about explicit focus-type inventory, not only behavior that happens to work
2. this reduces the gap between the documented supported document-focus surface and the tested one
3. it narrows the remaining `IC4-A` work toward broader report/listing inventory closure rather than untested transaction-document promotion paths

### Slice: Shared Follow-Up Routing Before Family Rescue

Status: complete

What we did:

1. routed follow-up through the shared affordance layer before family-local rescue logic
2. preserved strong entity-detail local transform behavior
3. widened bounded follow-up continuity for document and listing flows

Why it matters:

1. this is a true shared routing seam
2. it reduces single-case family branching

### Slice: Live Financial Statement Continuity

Status: complete

What we proved live:

1. clarification to Profit and Loss
2. Profit and Loss to Balance Shee
3. Balance Sheet to Cash Flow

Why it matters:

1. statement continuity now has real shared live proof
2. this is not only source-level confidence

### Slice: Master Data Single-Row To Detail Continuity

Status: complete

What we proved live:

1. supplier match result to `tell me more about that supplier`
2. customer and item continuity paths remain healthy

Why it matters:

1. single-row master-data listing can promote into stable detail ownership

### Slice: Ambiguous Item To Option List To Detail To Stock Follow-Up

Status: complete

What we proved live:

1. ambiguous item reques
2. option list response
3. named item detail
4. stock by warehouse follow-up

Why it matters:

1. this proved a broader natural option-list path, not only exact-match shortcut paths

### Slice: Softer Discard Language Live Proof

Status: complete

What we proved live:

1. `ignore that show me suppliers`
2. `forget it answer the last question`
3. `ignore this and go back to the customer`

Why it matters:

1. these are more natural business utterances
2. they are now covered by the shared control-language seam, not phrase-local fixes

### Slice: Richer Option-List Language Live Proof

Status: complete

What we proved live:

1. `show me the list that you found`
2. same candidate preservation
3. downstream detail and stock-by-warehouse continuity remained healthy

Why it matters:

1. this widened the natural business-language surface without changing architecture

### Slice: Shared Metadata-Driven Front-Door Breakout From Stale Clarification

Status: complete

What we did:

1. hardened shared entity-grain inference so plural business-natural requests such as `show me suppliers` and `show me customers` can resolve as governed master-data directory requests even when alias coverage is incomplete
2. hardened shared lookup-mode inference so explicit listing-style phrasing can normalize into `directory_list` without depending on a narrow exact-phrase alias
3. added a shared metadata-driven front-door breakout seam so stale pending clarification can also yield to explicit transaction-listing requests such as `show me sales invoices`
4. added the same shared metadata-driven breakout behavior for generic financial-statement entry requests such as `show me financial statement`
5. preserved the clarification path for true option-list follow-up requests such as `show me the list`
6. proved that pending item clarification no longer traps a clearly new business owner across multiple front-door families when generic semantic/front-door cross-checks miss

Why it matters:

1. this is a shared front-door and clarification-breakout fix, not a supplier-only, sales-invoice-only, or financial-statement-only rescue
2. it closes a real restore-owner gap where stale clarification state could block a new natural business request even when the user had clearly switched families
3. it moves `IC5-C` forward by reducing one more older runtime seam in favor of shared metadata-driven inference and shared breakout policy

### Slice: Targeted Restore Matching For Accepted Recovery Origins

Status: complete

What we did:

1. hardened shared targeted-restore matching for resumable prior branches so accepted recovery origins are not rejected only because their branch kind is operational rather than semantic
2. preserved focus-kind matching when the resumable prior branch actually carries a semantic focus kind
3. proved the shared path with targeted restore tests for:
   - resumable prior request replay by target grain
   - target-scope focus-grain matching
   - discard-prefixed targeted restore over historical prior branch

Why it matters:

1. this is a shared restore-arbitration improvement, not a customer-ranking-only workaround
2. it reduces one more `IC5-C` failure mode where a valid historical governed branch existed but could not be restored because the matcher treated operational branch metadata as if it were business focus metadata
3. it keeps targeted restore aligned with preserved governed family and scope information instead of over-trusting local branch-kind labels

### Slice: Discard-Prefixed Targeted Restore On Transaction Listing

Status: complete

What we proved live:

1. `show me sales invoices`
2. sales invoice detail follow-up
3. `ignore that, go back to the sales invoices`
4. `show me purchase orders`
5. purchase order detail follow-up
6. `ignore that, go back to the purchase orders`

Why it matters:

1. this proves discard-prefixed targeted restore is not only a master-data behavior
2. the same shared control seam now holds for transaction listing owners too
3. discard-prefixed restore is now proven across two different transaction listing families

### Slice: Targeted Restore After Cross-Listing Override

Status: complete

What we proved live:

1. `show me sales invoices`
2. `show me purchase orders`
3. `go back to the sales invoices`

Why it matters:

1. this proves historical targeted restore can recover an older transaction listing even after a newer listing takes ownership
2. the shared restore seam is now proven on listing-over-listing owner switches, not only listing-over-detail detours

### Slice: Discard-Prefixed Targeted Restore After Cross-Listing Override

Status: complete

What we proved live:

1. `show me sales invoices`
2. `show me purchase orders`
3. `ignore that, go back to the sales invoices`
4. discard-prefixed recovery still restored `Sales Invoice List` after the newer purchase-order listing had taken ownership

Why it matters:

1. this proves the same cross-listing recovery still holds when natural discard language is layered on top
2. the shared control-language seam and the shared restore seam are now proven together for listing-over-listing owner switches
3. the cross-listing owner-switch seam is now proven in both plain targeted restore and discard-prefixed targeted restore forms

### Slice: Shared Compound-Completion Response Selector

Status: complete

What we did:

1. introduced one shared selector for compound-completion reentry response handling
2. unified completion status to acknowledgement action mapping
3. unified completion status to user-facing acknowledgement answer mapping
4. unified continuation-control eligibility gating
5. switched both completion-answer generation and completion-decision building onto that same shared selector
6. re-verified focused completion tests and the live full state-integrity suite after the change

Why it matters:

1. this removes duplicated completion-reentry reasoning across parallel helpers
2. completion wording and completion routing now come from one governed seam instead of two partially-overlapping ones
3. this is still `IC5-C` routing cleanup, not a transcript-local fix

### Slice: Shared Prior-Branch Restore Route Selector

Status: complete

What we did:

1. introduced one shared selector for prior-branch restore route choice
2. made route choice explicit across:
   - targeted recent focus restore
   - targeted resumable-prior restore
   - unmatched targeted branch-restore block
   - latest non-clarification restore
   - authoritative pending-clarification reopen
   - direct fallback restore
3. switched `_build_prior_branch_restore_contract_from_snapshot` to dispatch from that selector instead of deciding route order inline
4. added direct tests for route selection itself, not only for the final built contrac
5. re-verified the focused restore matrix and the live full state-integrity suite after the change

Why it matters:

1. restore-route precedence is now more explicit and auditable
2. the shared restore builder now owns less hidden decision logic
3. this is another real `IC5-C` routing cleanup slice, not a family-specific restore patch

### Slice: Shared Prior-Branch Restore Projection Selector

Status: complete

What we did:

1. introduced one shared selector for prior-branch restore projection
2. unified runtime override message selection
3. unified recent-focus decision target enrichmen
4. unified recent-focus affordance attachmen
5. switched both `_prior_branch_restore_runtime_override_message` and `_conversation_control_decision_from_prior_branch_restore_contract` onto that selector
6. added focused tests for sequence-label projection
7. added focused tests for recent-focus projection
8. added focused tests for existing prior-branch restore decision behavior after the change
9. re-verified the live full state-integrity suite after the selector landed

Why it matters:

1. restore-mode-specific shaping is now shared instead of duplicated across runtime override and decision mapping
2. prior-branch restore behavior is more explicit without changing the business contrac
3. this is still `IC5-C` routing cleanup, not a one-off restore tweak

## 5.2 Slices That Started As Risk Items But Are Now Closed

### Slice: Plural Collection Restore From Singular Detail

Status: complete

Scenario:

1. supplier match
2. supplier detail
3. `go back to the suppliers`

What we did:

1. extended the shared targeted-restore evidence contract so it records requested focus kind, not only target grain
2. hardened shared restore arbitration so collection requests such as `go back to the suppliers` do not match a newer singular detail branch only because the grain is the same
3. added a dedicated H3 smoke for supplier-directory restore over newer supplier detail
4. proved the slice in the governed bench runtime for:
   - supplier list -> supplier detail -> `go back to the suppliers`
   - customer list -> customer detail -> `go back to the customers`
   - item list -> item detail -> `go back to the items`
   - item list -> item detail -> `ignore that, go back to the items`
   - sales invoice list -> sales invoice detail -> `go back to the sales invoices`
   - purchase order list -> purchase order detail -> `go back to the purchase orders`

Current classification:

1. `IC5-C` shared seam is now complete for this restore class
2. `IC5-D` now has live proof for this restore class across supplier, customer, item, sales-invoice listing, and purchase-order listing families, while broader restore-matrix expansion remains open

Additional note:

1. payment-entry listing is active and healthy as a listing family
2. payment-entry detail is not yet a safe governed detail lane, so we intentionally did not mark payment-entry listing-over-detail restore as a completed proof slice
3. payment-entry remains a valid future matrix candidate only after its governed detail lane becomes reliable enough for honest restore-over-detail proof

## 6. Where We Are Now

We are still inside the conversation-control implementation series.

More specifically:

1. `IC4-C` is complete
2. `IC4-D` is complete
3. `IC4-A` and `IC4-B` are complete
4. `IC5-C` is complete for the current delivery chapter
5. `IC5-D` is complete
6. current real blocker is not general wording anymore
7. current real blocker is now the decision of when to enter `IC6` versus when to start the later dedicated `service.py` refactor chapter, not the original missing collection/detail arbitration seam itself

In simple English:

1. we have already built a strong shared control spine
2. we have already proved many natural business cases live
3. but we are still in the middle of the `IC` hardening work
4. the latest closed seams are:
   - shared metadata-driven front-door breakout from stale pending clarification ownership across master-data, transaction-listing, and financial-statement entry requests
   - targeted restore matching hardening for accepted recovery-origin resumable prior branches
   - shared collection-alias targeted restore widening for directory-style collection wording over newer detail focus
5. we should not pretend we are ready to leave this area ye

## 7. What We Still Need To Do Nex

Recommended next order:

### Next 1: Close `IC6` And Hand Back To The Main Roadmap

Priority: highes

Reason:

1. `IC6-S5` is complete and the closure checkpoint now says `IC6` is complete for the current delivery chapter
2. conversation control is no longer the right active build center for the project; it should become shared infrastructure again
3. the immediate program move should be to resume the broader Phase B1 + C1 backbone plan with this stabilized control spine underneath i

### Next 2: Keep `IC5-C` Closed And Do Not Reopen It Lightly

Reason:

1. `IC5-D` is complete
2. the remaining `IC5-C` surface now appears to be mostly facade orchestration rather than broad reusable policy
3. we should only extract another seam if a genuinely new shared routing contract appears, not because the facade still has orchestration gravity
4. we should not reopen restore-matrix expansion unless a real shared routing gap appears

### Next 3: Keep The Dedicated `service.py` Refactor Separate From `IC6`

Reason:

1. governed multi-step execution is now the right next product-facing chapter
2. but the remaining facade gravity should still be handled as a dedicated refactor chapter, not smuggled into `IC6` delivery slices
3. we should let `IC6` add governed execution contracts and tests, then schedule the broader facade refactor deliberately as its own workstream

## 8. What We Should Not Do

To stay enterprise grade, we should not:

1. solve `go back to the suppliers` as a supplier-only branch
2. add hardcoded restore exceptions per entity type
3. bypass shared restore precedence just to pass one transcrip
4. mark a slice complete because one wording variant happened to work
5. keep pretending the original collection/detail restore gap or restore-matrix coverage is still the main blocker after `IC5-D` is already complete for the current safe families

## 9. Honest Status Conclusion

The direction is correct.

This is enterprise-grade progress, not random patching, because:

1. we are building on shared state, shared evidence, shared affordance, and shared restore contracts
2. we are verifying with live H3 proof, not only unit assumptions
3. when a scenario is not truly solved, we are recording it as open instead of masking i

But we are not finished.

The current truthful position is:

1. conversation-control implementation is significantly stronger than before
2. natural business follow-up behavior is broader and more stable than before
3. the original collection-vs-detail restore gap is now closed for the shared targeted-restore seam
4. item collection restore is now also live-proven in both plain and discard-prefixed forms
5. recent-focus affordance no longer collapses for generated or family-backed listing/report/statement labels that are not individually registry-backed
6. `IC5-D` is now complete
7. `IC4-A` transaction-document focus inventory is now materially more explicit and tested than before
8. shared metadata-driven stale-clarification breakout is now also proven and recorded across master-data listings, transaction listings, and financial-statement entry requests
9. targeted restore matching for accepted recovery-origin resumable prior branches is now also proven and recorded
10. recent-focus affordance policy has now also been extracted out of `service.py` into a dedicated helper seam without changing runtime behavior
11. the full live `test_post_contract_state_integrity` suite is green again after that extraction
12. recent-focus listing affordance now composes governed scope-family policy with governed report policy instead of relying on a single registry seam or focus-grain fallback alone
13. live verification now proves this composition for both transaction listing and master-data listing affordance cases
14. restore arbitration now also uses normalized branch-owned source indexes for recent focus, so newer compatible artifact/recovery contributors can keep the grounded branch ahead of an older pending clarification when that is the truthful latest owner
15. accepted-recovery resumable prior branches now also use normalized branch-owned source indexes, so they no longer appear artificially older than a later historical prior-focus candidate just because the repair acceptance happened earlier
16. restore arbitration can now also let known active-sequence, recent-focus, and resumable-prior owners outrank a non-authoritative message-fallback pending clarification when that clarification has no usable source index
17. sequence-completion suppression now also uses an explicit superseding-state selector with recorded owner/basis output, and still ignores a non-authoritative message-fallback pending clarification when that clarification has no usable source index and no truly newer owner has taken precedence
18. direct restore fallback now also ignores a non-authoritative message-fallback pending clarification when no stronger owner exists, instead of reopening that fallback clarification as if it were authoritative
19. recent-focus versus resumable-prior arbitration now also prefers the owner with a known source index over an otherwise-available but unindexed peer before falling back to the older hard defaul
20. latest-repair-intent snapshot state now also exposes normalized source-index evidence, and live characterization proves the accepted-repair snapshot keeps that recency metadata visible alongside resumable-prior derivation
21. peer-owner arbitration now explicitly labels the indeterminate-default path, so shared restore no longer overstates why recent focus won when both peer branches lack comparable precedence evidence
22. resumable-prior snapshot arbitration now explicitly records whether accepted repair or historical prior focus won by:
   - newer index
   - known over unindexed
   - explicit indeterminate defaul
   - sole availability
23. non-clarification restore owner arbitration now also uses an explicit selector that returns both winner and basis, and live coverage proves the selector directly for known-over-unindexed and indeterminate-default cases
24. sequence-completion suppression now explicitly records whether a newer authoritative pending clarification, recent focus, or resumable-prior owner superseded the completed sequence instead of hiding that decision behind an inline boolean check
25. non-clarification restore winner selection now also uses an explicit shared selector across active sequence, recent focus, resumable-prior request, and pending-clarification precedence, so `_build_latest_non_clarification_restore_contract` no longer owns winner selection inline
26. authoritative pending-clarification reopen now also uses a shared builder with explicit arbitration-basis recording for both `question_restore` and `branch_restore`, instead of keeping those restore-owner branches duplicated inline in `_build_prior_branch_restore_contract_from_snapshot`
27. targeted branch-restore owner selection now also uses an explicit selector across recent focus and resumable-prior request matching, so `_build_prior_branch_restore_contract_from_snapshot` no longer decides targeted restore ownership through duplicated inline match branches
28. direct restore fallback now also uses a shared helper across `sequence_restore` and final resumable-prior fallback paths, with explicit arbitration-basis output instead of leaving those last restore-owner branches inline in `_build_prior_branch_restore_contract_from_snapshot`
29. active-sequence supersede routing now also uses an explicit selector with coupled owner/basis output across control override, current control-decision owner, prior-branch restore owner, and substantive front-door override, so `_active_sequence_supersede_reason` no longer hides that runtime-owner arbitration inline
30. pending-clarification yield arbitration now also uses explicit owner selectors for both initial-control override and current-control override cases, so those clarification-yield seams no longer hide strong-owner precedence behind boolean-only inline checks
31. active-sequence completion gating now also uses an explicit owner selector across current control resume and prior-branch resume, so sequence-completion eligibility no longer hides its runtime-owner check inline
32. active-sequence completion source selection now also uses an explicit owner selector across current-active and latest-active payload candidates, so completion-source fallback no longer hides that source arbitration inline
33. compound-execution runtime-message resolution now also uses an explicit source selector across current front-door compound payload and latest active-sequence continuation payload, so runtime-message source choice no longer hides that arbitration inline
34. compound-cancellation decision building now also uses an explicit source selector across cancelled-sequence payload and active-sequence fallback payload, so cancellation target selection no longer hides that source choice inline
35. compound-completion reentry now also uses an explicit selector for completion-versus-cancelled acknowledgement action, so sequence-completion reentry semantics no longer hide that action mapping inline
36. recent-focus continuation routing now also uses an explicit eligibility selector across passthrough allowance, strong control-owner suppression, recent-focus availability, and grounded follow-up requirements, so recent-focus continuation no longer hides that route gating inline
37. compound-continuation routing now also uses an explicit eligibility selector across runtime-message presence, continuation-control evidence, and active-sequence availability, so sequence continuation no longer hides that route gating inline
38. compound-completion reentry now also uses an explicit eligibility selector across completion-answer presence, continuation-control evidence, and supported completion status, so completion reentry no longer hides that route gating inline
39. compound-completion reentry response handling now also uses one shared selector across acknowledgement-answer mapping, decision-action mapping, and eligibility gating, so completion response wording and decision routing no longer diverge across separate helper seams
40. prior-branch restore snapshot routing now also uses an explicit shared selector across targeted restore, latest non-clarification restore, authoritative pending clarification, and direct fallback, so restore-route precedence no longer hides inside the snapshot builder
41. prior-branch restore projection now also uses one shared selector across runtime override messaging, recent-focus target enrichment, and recent-focus affordance attachment, so restore-mode shaping no longer diverges across separate helper seams
42. the shared collection-alias targeted-restore seam is now also proven in the live and state-integrity matrix for directory-style wording such as `supplier directory` and `supplier directories` over newer supplier detail
43. the full live `test_post_contract_state_integrity` suite is green at `376` tests after the latest shared restore and affordance slices
44. next work should stay focused on unfinished `IC4-A` / `IC4-B` closure work while keeping `IC5-C` closed unless a genuinely new shared routing gap appears

## 10. Recommended Short Status Line

If we want one short summary for daily tracking:

1. `IC4-C` complete
2. `IC4-D` complete
3. `IC5-C` complete
4. `IC5-D` complete
5. latest completed slices: richer option-list live proof and plural collection restore from singular detail across supplier, customer, item, sales-invoice listing, and purchase-order listing families
6. latest completed `IC4-B` slice: conservative recent-focus affordance fallback hardening for generated/family-backed listing, statement, and report focus
7. latest completed `IC4-B` slice: recent-focus affordance helper extraction out of `service.py` with the live full state-integrity suite green afterward
8. latest completed `IC4-B` slice: governed listing-affordance composition across scope-family compatibility policy and report-approved follow-up policy, with live proof for `Payment Entry List` and `Supplier Master List`
9. latest completed `IC4-A` / `IC4-B` slice: single-row listing promotion now respects governed detail-capable scope policy through shared metadata-backed document-focus helpers, so unsupported listing scopes such as `Payment Entry List` no longer auto-promote into document focus just because one row is presen
10. latest completed `IC4-A` / `IC4-B` slice: master-data single-row entity promotion now also uses shared metadata-backed row label/key helpers derived from active approved report metadata, so `Customer Master List`, `Supplier Master List`, and `Item Master List` no longer depend on service-local column maps
11. latest completed `IC5-C` slice: shared metadata-driven front-door breakout from stale pending clarification ownership across master-data listings, transaction listings, and financial-statement entry requests
12. latest completed `IC5-C` slice: targeted restore matching hardening for accepted recovery-origin resumable prior branches
13. latest completed `IC5-C` slice: branch-owned recent-focus source-index normalization across grounded turn, compatible artifact, and matching recovery contributors, with live proof that question-restore can prefer the newer grounded branch over an older pending clarification
14. latest completed `IC5-C` slice: accepted-recovery resumable-prior-branch source-index normalization across prior recovery, accepted repair, and newer grounded contributors, with live proof that the accepted-recovery branch can outrank a historical prior-focus candidate when it is truly newer
15. latest completed `IC5-C` slice: non-authoritative pending-clarification fallback yielding to known active-sequence, recent-focus, and resumable-prior owners when the clarification has no usable source index
16. latest completed `IC5-C` slice: sequence-completion suppression now uses an explicit superseding-state selector with coupled owner/basis output while preserving the same non-authoritative pending-clarification rule, so fallback clarification stubs do not suppress completed-sequence acknowledgement by themselves
17. latest completed `IC5-C` slice: direct restore fallback aligned with the same non-authoritative pending-clarification rule, so generic question-restore and branch-restore do not reopen weak fallback clarification stubs by themselves
18. latest completed `IC5-C` slice: recent-focus versus resumable-prior arbitration aligned with known-versus-unindexed owner precedence, so owner selection no longer silently depends on the old recent-focus default when raw recency is not comparable
19. latest completed `IC5-C` slice: latest-repair-intent snapshot evidence now includes normalized source-index metadata, keeping repair evidence aligned with the broader owner-audit model
20. latest completed `IC5-C` slice: peer-owner arbitration now explicitly labels the indeterminate recent-focus default path instead of implying a stronger precedence reason than the evidence supports
21. latest completed `IC5-C` slice: resumable-prior snapshot selection now uses an explicit selector with recorded arbitration basis across accepted-repair, historical-prior-focus, known-over-unindexed, and indeterminate-default cases
22. latest completed `IC5-C` slice: non-clarification restore owner selection now uses an explicit selector with coupled winner/basis output across sole-availability, newer-index, known-over-unindexed, and indeterminate-default cases
23. latest completed `IC5-C` slice: full non-clarification restore winner selection now also uses a shared selector across active-sequence precedence, pending-clarification precedence, recent-focus vs resumable-prior arbitration, and final winner/basis outpu
24. latest completed `IC5-C` slice: authoritative pending-clarification reopen now also uses a shared builder with explicit arbitration-basis output across both question-restore and generic branch-restore paths
25. latest completed `IC5-C` slice: targeted branch-restore owner selection now also uses an explicit selector across recent-focus and resumable-prior matching instead of two separate inline owner branches
26. latest completed `IC5-C` slice: direct restore fallback now also uses a shared helper across sequence-restore and resumable-prior fallback paths, with explicit arbitration-basis output for those last fallback owners
27. latest completed `IC5-C` slice: active-sequence supersede routing now also uses an explicit selector with coupled owner/basis output across control override, current control-decision owner, prior-branch restore owner, and substantive front-door override
28. latest completed `IC5-C` slice: pending-clarification yield arbitration now also uses explicit owner selectors for both initial-control override and current-control override cases, so clarification-yield precedence is no longer hidden behind boolean-only inline checks
29. latest completed `IC5-C` slice: active-sequence completion gating now also uses an explicit owner selector across current control resume and prior-branch resume, so sequence-completion eligibility no longer hides its runtime-owner check inline
30. latest completed `IC5-C` slice: active-sequence completion source selection now also uses an explicit owner selector across current-active and latest-active payload candidates, so completion-source fallback no longer hides that source arbitration inline
31. latest completed `IC5-C` slice: compound-execution runtime-message resolution now also uses an explicit source selector across current front-door compound payload and latest active-sequence continuation payload, so runtime-message source choice no longer hides that arbitration inline
32. latest completed `IC5-C` slice: compound-cancellation decision building now also uses an explicit source selector across cancelled-sequence payload and active-sequence fallback payload, so cancellation target selection no longer hides that source choice inline
31. latest completed `IC5-C` slice: compound-completion reentry now also uses an explicit selector for completion-versus-cancelled acknowledgement action, so sequence-completion reentry semantics no longer hide that action mapping inline
32. latest completed `IC5-C` slice: recent-focus continuation routing now also uses an explicit eligibility selector across passthrough allowance, strong control-owner suppression, recent-focus availability, and grounded follow-up requirements, so recent-focus continuation no longer hides that route gating inline
33. latest completed `IC5-C` slice: compound-continuation routing now also uses an explicit eligibility selector across runtime-message presence, continuation-control evidence, and active-sequence availability, so sequence continuation no longer hides that route gating inline
34. latest completed `IC5-C` slice: compound-completion reentry now also uses an explicit eligibility selector across completion-answer presence, continuation-control evidence, and supported completion status, so completion reentry no longer hides that route gating inline
35. latest completed `IC5-C` slice: compound-completion response handling now also uses one shared selector across acknowledgement-answer mapping, decision-action mapping, and eligibility gating, so completion wording and decision routing no longer drift across separate helper seams
36. latest completed `IC5-C` slice: prior-branch restore snapshot routing now also uses an explicit shared selector across targeted restore, latest non-clarification restore, authoritative pending clarification, and direct fallback, so restore-route precedence no longer hides inside the snapshot builder
37. latest completed `IC5-C` slice: prior-branch restore projection now also uses one shared selector across runtime override messaging, recent-focus target enrichment, and recent-focus affordance attachment, so restore-mode shaping no longer diverges across separate helper seams
38. the live full `test_post_contract_state_integrity` suite is now green at `376` tests
39. latest completed `IC5-C` slice: prior-branch direct handler routing now also uses an explicit shared selector and dispatcher across reopen-pending-clarification and replay-as-fresh-query modes, so top-level restore execution no longer depends on ordered inline trial logic
40. latest completed `IC5-C` slice: prior-branch restore decision classification now also uses one shared selector across reopen-pending-clarification, resume-active-sequence, and non-clarification override states, so the conversation-control spine no longer repeats that restore-action branching across multiple selectors
41. latest completed `IC4-A` slice: transaction-document recent-focus inventory characterization for sales order, delivery note, purchase receipt, and purchase invoice
42. latest completed `IC4-B` slice: listing-scope resolution now falls back to active approved governed scope identity when view id and scope id match, with representative affordance proof for `Item Master List`, `Sales Order List`, and `Purchase Invoice List`
43. latest completed `IC4-A` slice: representative recent-focus listing inventory characterization now also covers `Item Master List`, `Sales Order List`, and `Purchase Invoice List`
44. latest completed `IC4-A` / `IC4-B` slice: the current active governed master/listing surface is now explicitly characterized across `Customer Master List`, `Supplier Master List`, `Item Master List`, `Payment Entry List`, `Sales Invoice List`, `Purchase Invoice List`, `Delivery Note List`, `Sales Order List`, and `Purchase Order List`
45. latest completed `IC4-A` / `IC4-B` slice: broader governed report-focus coverage now explicitly characterizes aging, inventory snapshot, and trend report families through `Accounts Receivable Summary`, `Stock Balance`, and `Delivery Note Trends`
46. latest completed `IC4-A` / `IC4-B` slice: broader governed report-focus coverage now also explicitly characterizes the aging sibling and sales analytics edges through `Accounts Payable Summary` and `Sales Analytics`
47. latest completed `IC4-A` / `IC4-B` slice: broader governed report-focus coverage now also explicitly characterizes non-summary aging, warehouse-oriented inventory snapshot, and item sales history edges through `Accounts Payable`, `Warehouse Wise Stock Balance`, and `Item-wise Sales History`
48. latest completed `IC4-A` / `IC4-B` slice: broader governed report-focus coverage now also explicitly characterizes non-summary receivable aging and the current direct-query item-line report fallback edges through `Accounts Receivable`, `Sales Order Item List`, and `Sales Invoice Item List`
49. latest completed `IC5-C` slice: restore-owner arbitration for initial-control override, pending-clarification yield, active-sequence completion, and active-sequence supersede now composes through a shared `conversation_control_support` helper instead of repeating those rule ladders inline in `service.py`
50. latest completed `IC5-C` slice: continuation and sequence-source arbitration for compound-completion reentry, compound continuation, compound cancellation, recent-focus continuation, active-sequence completion-source fallback, and compound runtime-message source selection now also composes through the shared `conversation_control_support` helper instead of staying as additional inline selector ladders in `service.py`
51. latest completed `IC5-C` slice: targeted-restore owner arbitration, non-clarification restore owner arbitration, and direct prior-branch restore handler route selection now also compose through the shared `conversation_control_support` helper instead of staying as additional inline selector ladders in `service.py`
52. latest completed `IC5-C` slice: latest non-clarification restore arbitration and top-level prior-branch restore route selection now also compose through the shared `conversation_control_support` helper, so the central pending-vs-sequence-vs-recent-focus-vs-resumable precedence mapping no longer sits inline in `service.py`
53. latest completed `IC5-C` slice: restore projection shaping and restore runtime-message policy for recent-focus and active-sequence restore modes now also compose through the shared `conversation_control_support` helper, so `service.py` no longer owns that projection policy inline
54. latest completed `IC5-C` slice: prior-branch restore mode parsing, restore-derived recent-focus reconstruction, and restore runtime-message reconstruction now also compose through the shared `conversation_control_support` helper instead of remaining as duplicated reconstruction policy in `service.py`
55. latest completed `IC5-C` slice: authoritative pending-clarification restore spec selection and direct restore fallback spec selection now also compose through the shared `conversation_control_support` helper, while `service.py` keeps only the final restore-contract assembly calls
56. latest completed `IC5-C` slice: prior-branch restore decision-payload shaping now also composes through the shared `conversation_control_support` helper, so `service.py` keeps only the final `build_conversation_control_decision_contract(...)` call for that restore-decision path
57. latest completed `IC5-C` slice: targeted recent-focus restore spec selection and targeted resumable-prior restore spec selection now also compose through the shared `conversation_control_support` helper, so the snapshot builder keeps only the final restore-contract assembly calls for those targeted routes
58. latest completed `IC5-C` slice: prior-branch restore request interpretation now also composes through the shared `conversation_control_support` helper, so phrase-type precedence and targeted-restore hint precedence no longer stay inline in the snapshot builder
59. latest completed `IC5-C` slice: close-out review now shows the remaining prior-branch restore surface is mostly facade orchestration, so further extractions from this seam should defer to the later dedicated `service.py` refactor chapter unless a truly shared policy gap is discovered
60. latest completed `IC5-C` slice: restore-derived recent-focus reconstruction and restore-derived recent-focus affordance reconstruction are now directly characterized in the live state-integrity suite, so the last thin shared reconstruction seams are explicitly covered before deferring the remaining restore surface to later facade refactor work
61. latest completed `IC4-A` / `IC4-B` slice: financial-statement recent-focus classification now uses a shared metadata-backed statement descriptor instead of literal statement-name matching inline in `service.py`, so the snapshot spine stays aligned with governed report metadata rather than a hardcoded three-name se
62. latest completed `IC4-A` / `IC4-B` slice: registry-driven report-affordance matrix coverage now proves the active approved report surface normalizes into recent-focus affordance modes without leaking raw policy aliases such as `column_projection` or `metric_change`, including statement-backed reports through the shared metadata descriptor path
63. latest completed `IC4-A` / `IC4-B` slice: registry-driven listing-scope matrix coverage now proves the active approved list-style governed scope surface resolves through the correct recent-focus selection class and normalized listing follow-up modes across:
   - master-data scopes
   - document-listing scopes
   - financial-operation listing scopes
64. the live full `test_post_contract_state_integrity` suite is green at `317` tests after that broader matrix coverage, and the dedicated listing-scope matrix test is also live-proven directly by name
65. latest completed `IC4-A` / `IC4-B` slice: registry-driven snapshot matrix coverage now proves the active approved listing-scope surface derives the correct list-shaped recent-focus state from grounded payload shape itself, while respecting governed scope identity instead of looser business-grain hints
66. latest completed `IC4-A` / `IC4-B` slice: registry-driven snapshot matrix coverage now also proves the active approved financial-statement surface derives statement recent focus through the shared metadata-backed descriptor, and that active approved non-scope report surfaces derive generic report focus through the same snapshot spine
67. latest completed `IC4-A` / `IC4-B` slice: registry-driven single-row snapshot matrix coverage now proves the active approved listing-scope surface promotes from list focus into governed entity focus or governed document focus through the shared snapshot spine, instead of relying only on hand-picked point tests
68. latest completed `IC4-A` / `IC4-B` slice: registry-driven detail-capable scope matrix coverage now proves the active approved `entity_detail` surface derives governed entity focus and governed document focus through the shared snapshot spine and produces the expected detail-follow-up affordance class without relying only on named examples like `Customer Detail` or `Sales Invoice Detail`
69. latest completed `IC4-A` / `IC4-B` slice: registry-driven runtime-routing matrix coverage now proves the active approved detail-capable scope surface routes through `local_transform`, while the active approved listing, statement, and non-scope report surfaces route through `shared_affordance`, all from snapshot-derived recent-focus state rather than handcrafted recent-focus fixtures
70. the live full `test_post_contract_state_integrity` suite is green at `326` tests after this broader snapshot-plus-runtime matrix coverage
71. latest completed `IC5-C` slice: direct characterization now covers restore-derived recent-focus reconstruction and restore-derived recent-focus affordance reconstruction, so the last thin shared reconstruction seams are no longer only implicitly exercised through larger restore flows
72. the live full `test_post_contract_state_integrity` suite is green at `328` tests after this final `IC5-C` close-out characterization pass
73. latest completed `IC4-A` / `IC4-B` slice: single-row listing promotion now respects governed detail-capable scope policy through shared metadata-backed document-focus helpers, so unsupported listing scopes such as `Payment Entry List` and non-governed legacy surfaces such as `Purchase Receipt List` stay on listing focus instead of auto-promoting into document focus from hardcoded grain maps
74. the live full `test_post_contract_state_integrity` suite is green at `329` tests after this governed single-row promotion alignment pass
75. latest completed `IC4-A` / `IC4-B` slice: master-data single-row entity promotion now also uses shared metadata-backed row label/key helpers derived from active approved report metadata, so `Customer Master List`, `Supplier Master List`, and `Item Master List` no longer depend on service-local column maps
76. the live full `test_post_contract_state_integrity` suite is green at `331` tests after this governed master-data single-row promotion alignment pass
77. latest completed `IC4-A` / `IC4-B` slice: grounded recent-focus source-surface classification now composes through one shared metadata-backed descriptor in `recent_focus_support.py`, so `service.py` no longer mixes statement, master-data, transaction-listing, and detail-source classification inline through family-name heuristics alone
78. the live full `test_post_contract_state_integrity` suite is green at `334` tests after this shared recent-focus source-surface classification alignment pass
79. latest completed `IC4-A` / `IC4-B` slice: generic report recent-focus classification now also composes through that same shared descriptor seam, so `service.py` no longer keeps a separate inline fallback for report-shaped grounded focus while detail, statement, master-data listing, and transaction listing already use shared governed classification
80. the live full `test_post_contract_state_integrity` suite is green at `335` tests after this shared generic-report recent-focus classification alignment pass
81. latest completed `IC4-A` / `IC4-B` slice: default grounded recent-focus state shaping for statement, master-data listing, transaction listing, and generic report surfaces now also composes through one shared builder in `recent_focus_support.py`, so `service.py` keeps only the entity-detail special case and the governed single-row promotion overrides instead of duplicating standard list/report state payload assembly inline
82. the live full `test_post_contract_state_integrity` suite is green at `337` tests after this shared grounded recent-focus state-builder alignment pass
83. latest completed `IC4-A` / `IC4-B` slice: entity-detail recent-focus state shaping now also composes through that same shared grounded state builder, so `service.py` resolves only the entity key/label inputs while the standard entity-versus-document focus payload assembly no longer lives inline
84. the live full `test_post_contract_state_integrity` suite is green at `339` tests after this shared entity-detail recent-focus state-builder alignment pass
85. latest completed `IC4-A` / `IC4-B` slice: the conservative empty recent-focus snapshot payload now also composes through the shared recent-focus support layer, so even the no-focus fallback shape no longer has to be assembled inline in `service.py`
86. the live full `test_post_contract_state_integrity` suite is green at `340` tests after this shared empty recent-focus fallback alignment pass
87. latest completed `IC4-A` / `IC4-B` slice: the conservative empty resumable-prior-request snapshot payload now also composes through a dedicated shared `snapshot_defaults.py` helper instead of being assembled inline in `service.py`, so another snapshot-default seam is now explicit and directly characterized
88. the live full `test_post_contract_state_integrity` suite is green at `341` tests after this shared empty resumable-prior-request fallback alignment pass
89. latest completed `IC4-A` / `IC4-B` slice: snapshot `state_quality` shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, so the facade keeps one fewer snapshot-summary payload contract locally
90. the live full `test_post_contract_state_integrity` suite is green at `342` tests after this shared snapshot-state-quality alignment pass
91. latest completed `IC4-A` / `IC4-B` slice: snapshot `internal_details` source-summary and fallback-marker shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, so the facade keeps one fewer snapshot-observability payload contract locally
92. the live full `test_post_contract_state_integrity` suite is green at `343` tests after this shared snapshot-internal-details alignment pass
93. latest completed `IC4-A` / `IC4-B` slice: pending-clarification snapshot-state shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, while the facade still owns only the actual pending-signal lookup and source-index detection
94. the live full `test_post_contract_state_integrity` suite is green at `344` tests after this shared pending-clarification snapshot-state alignment pass
95. latest completed `IC4-A` / `IC4-B` slice: latest recovery-contract and latest repair-intent snapshot-state shaping now also compose through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, while the facade still owns only the authoritative payload lookup and source-index detection
96. the live full `test_post_contract_state_integrity` suite is green at `346` tests after this shared recovery-and-repair snapshot-state alignment pass
97. latest completed `IC4-A` / `IC4-B` slice: latest grounded-turn snapshot-state shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, while the facade still owns only the authoritative grounded-turn lookup and source-index detection
98. the live full `test_post_contract_state_integrity` suite is green at `347` tests after this shared grounded-turn snapshot-state alignment pass
99. latest completed `IC4-A` / `IC4-B` slice: latest artifact snapshot-state shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, while the facade still owns only the authoritative artifact lookup, grounded-compatibility decision, and source-index detection
100. the live full `test_post_contract_state_integrity` suite is green at `348` tests after this shared artifact snapshot-state alignment pass
101. latest completed `IC4-A` / `IC4-B` slice: active-sequence snapshot-state shaping now also composes through the shared `snapshot_defaults.py` layer instead of being assembled inline in `service.py`, while the facade still owns only the authoritative sequence payload lookup, sequence-active interpretation, and source-index detection
102. the live full `test_post_contract_state_integrity` suite is green at `349` tests after this shared active-sequence snapshot-state alignment pass
103. latest completed `IC4-A` / `IC4-B` slice: historical grounded-branch reconstruction for resumable-prior discovery now also composes through shared `snapshot_defaults.py` snapshot builders instead of maintaining a second inline copy of grounded-turn, artifact, and recovery snapshot payload shaping inside `service.py`, so historical focus carryover now reuses the same normalized snapshot currency as the main conversation-state snapsho
104. latest completed `IC4-A` / `IC4-B` slice: latest artifact snapshot shaping now also normalizes `artifact_type` from either `artifact_type` or payload `type`, so historical and primary artifact-state reconstruction no longer diverge on that field
105. the live full `test_post_contract_state_integrity` suite is green at `351` tests after this shared historical-snapshot reconstruction alignment pass
106. latest completed `IC4-A` / `IC4-B` slice: single-row recent-focus payload shaping for governed transaction-document promotion and governed master-data entity promotion now also composes through shared builders in `recent_focus_support.py` instead of being assembled inline in `service.py`, while the facade still owns only row inspection, governed detail-capable eligibility, and row label/key extraction
107. the live full `test_post_contract_state_integrity` suite is green at `353` tests after this shared single-row recent-focus payload alignment pass
108. latest open gap: any genuinely uncovered `IC4-A` / `IC4-B` edges outside the now-broad affordance-plus-snapshot-plus-runtime matrix, plus later dedicated `service.py` refactor work for remaining facade orchestration gravity
109. latest completed `IC4-A` / `IC4-B` slice: recent-focus runtime routing permission decisions now also compose through a shared helper in `recent_focus_support.py` instead of being decided inline inside `_compile_recent_focus_runtime_message`, so the facade no longer locally owns the follow-up mode intersection rules, the entity/document local-transform fallback, or the cross-family requery fallback policy
110. the live full `test_post_contract_state_integrity` suite is green at `355` tests after this shared recent-focus runtime-routing permission alignment pass
111. current `IC4-A` / `IC4-B` posture: the main remaining work is to identify any truly uncovered continuation-affordance seams that still live inline in `service.py` before we call this mini-phase closure block sufficiently stable and move cleanly into the next planned `IC` slice
112. latest completed `IC4-A` / `IC4-B` slice: recent-focus runtime route-selection eligibility now also composes through a shared helper in `recent_focus_support.py` instead of being split across inline follow-up mode normalization and inline grounded-follow-up gating inside `_compile_recent_focus_runtime_message`, so the facade no longer locally owns whether the shared recent-focus affordance surface is even eligible to route the turn before contextual local-transform versus requery selection
113. the live full `test_post_contract_state_integrity` suite is green at `357` tests after this shared recent-focus runtime-route-selection alignment pass
114. current `IC4-A` / `IC4-B` posture: the remaining work is now narrower still and appears concentrated in any residual inline continuation-decision payload shaping or restore-affordance glue that still lives in `service.py`, rather than in the recent-focus snapshot, affordance, or runtime-routing matrix itself
115. latest completed `IC4-A` / `IC4-B` slice: recent-focus continuation decision payload shaping now also composes through shared helpers in `recent_focus_support.py`, including focus-target extraction, continuation-reason wording, and internal-details payload assembly, so `service.py` no longer hand-builds the core recent-focus continuation decision payload even though it still owns the orchestration point that decides to emit that decision
116. the live full `test_post_contract_state_integrity` suite is green at `359` tests after this shared recent-focus continuation-decision payload alignment pass
117. current `IC4-A` / `IC4-B` posture: the remaining inline gravity now looks increasingly concentrated in restore-path glue and a smaller set of continuation-arbitration seams, rather than in the standard recent-focus continuation surface itself
118. latest completed `IC4-A` / `IC4-B` slice: recent-focus continuation eligibility evaluation now also composes through a shared helper in `recent_focus_support.py`, so `service.py` no longer owns the normalized runtime-vs-raw comparison, passthrough gating, recent-focus availability check, and grounded-follow-up eligibility composition for that standard continuation surface; it now contributes only the stronger control-owner signal from orchestration state
119. the live full `test_post_contract_state_integrity` suite is green at `361` tests after this shared recent-focus continuation-eligibility alignment pass
120. current `IC4-A` / `IC4-B` posture: the standard recent-focus continuation surface is now largely shared end-to-end, and the remaining inline gravity appears more clearly concentrated in restore-path arbitration and projection glue rather than in ordinary recent-focus continuation policy
121. latest completed `IC4-A` / `IC4-B` slice: recent-focus restore projection assembly now also composes through a shared helper in `recent_focus_support.py`, so `service.py` no longer hand-builds the restore-recent-focus runtime override message, resolved focus target, and recent-focus affordance payload before delegating to the shared prior-branch projection selector; it now passes through one shared projection bundle instead
122. the live full `test_post_contract_state_integrity` suite is green at `362` tests after this shared recent-focus restore-projection alignment pass
123. current `IC4-A` / `IC4-B` posture: the remaining inline gravity is now even more tightly concentrated in restore-path arbitration wording and owner-specific contract assembly, rather than in recent-focus continuation or recent-focus restore projection payload construction
124. latest completed `IC4-A` / `IC4-B` slice: owner-specific latest-non-clarification restore reason and detail-spec assembly now composes through a dedicated shared `restore_support.py` helper instead of being inlined inside `_build_latest_non_clarification_restore_contract`, so `service.py` no longer locally owns the restore-path wording matrix or the owner-specific internal-details payload shape for active-sequence, recent-focus, and resumable-prior restores
125. the live full `test_post_contract_state_integrity` suite is green at `364` tests after this shared latest-non-clarification restore-owner-spec alignment pass
126. current `IC4-A` / `IC4-B` posture: the restore path is now materially cleaner, and the remaining inline gravity appears increasingly limited to higher-level restore arbitration flow and final contract wiring rather than to owner-specific policy text or payload construction
127. latest completed `IC4-A` / `IC4-B` slice: direct-restore fallback owner-spec assembly now also composes through the shared `restore_support.py` layer instead of branching inline inside `_build_direct_restore_fallback_contract`, so `service.py` no longer locally owns the owner-specific fallback payload wiring for active-sequence versus resumable-prior direct restore fallback paths
128. the live full `test_post_contract_state_integrity` suite is green at `366` tests after this shared direct-restore fallback owner-spec alignment pass
129. current `IC4-A` / `IC4-B` posture: the remaining restore-path inline gravity now looks increasingly concentrated in the higher-level arbitration flow itself rather than in the owner-specific fallback or latest-restore payload construction branches
130. latest completed `IC4-A` / `IC4-B` slice: prior-branch restore route-selector input assembly now also composes through the shared `restore_support.py` layer instead of being normalized inline inside `_select_prior_branch_restore_route`, so `service.py` no longer locally owns the final targeted-vs-latest restore selector input packaging after candidate discovery
131. the live full `test_post_contract_state_integrity` suite is green at `367` tests after this shared prior-branch restore route-input alignment pass
132. current `IC4-A` / `IC4-B` posture: the remaining inline restore gravity is now increasingly centered on candidate discovery and top-level orchestration ordering rather than on payload shaping, wording matrices, or selector-input normalization
133. latest completed `IC4-A` / `IC4-B` slice: targeted restore owner-spec assembly now also composes through the shared `restore_support.py` layer instead of branching inline inside `_build_prior_branch_restore_contract_from_snapshot`, so `service.py` no longer locally owns the targeted recent-focus versus targeted resumable-prior spec-construction payload wiring after route selection
134. the live full `test_post_contract_state_integrity` suite is green at `369` tests after this shared targeted-restore owner-spec alignment pass
135. current `IC4-A` / `IC4-B` posture: the remaining inline restore gravity is now more clearly narrowed to candidate discovery and final top-level restore orchestration order, with most owner-specific restore payload construction already moved into shared helpers
136. latest completed `IC4-A` / `IC4-B` slice: targeted restore helper-spec assembly itself now also composes through the shared `restore_support.py` layer via one owner-agnostic targeted-owner-spec helper, so the top-level prior-branch restore orchestrator no longer locally owns the selector-backed targeted recent-focus versus targeted resumable-prior helper-spec wiring after route resolution
137. the live full `test_post_contract_state_integrity` suite is green at `369` tests after this shared targeted-restore helper-spec alignment pass
138. current `IC4-A` / `IC4-B` posture: the remaining inline restore gravity is now very tightly concentrated in candidate discovery and the final orchestration branch ordering itself, with most restore-specific payload shaping and helper-spec construction already shared
139. latest completed `IC4-A` / `IC4-B` slice: prior-branch restore snapshot-context normalization now also composes through the shared `restore_support.py` layer, so `_build_prior_branch_restore_contract_from_snapshot` no longer locally owns the cleaned interpretation fields plus normalized snapshot-state bucket extraction before route arbitration
140. the live full `test_post_contract_state_integrity` suite is green at `370` tests after this shared prior-branch restore snapshot-context alignment pass
141. current `IC4-A` / `IC4-B` posture: the remaining restore-path inline gravity is now even more narrowly reduced to candidate discovery and final contract-orchestration ordering, which is close to the point where additional extractions should likely stop and be deferred to the later dedicated `service.py` facade refactor chapter
142. latest completed `IC4-A` / `IC4-B` slice: prior-branch restore candidate-discovery composition now also composes through the shared `restore_support.py` layer, including latest-non-clarification ownership selection, targeted-restore candidate packaging, and selector-input context assembly, so `_select_prior_branch_restore_route` no longer locally owns that restore-candidate discovery cluster before final route arbitration
143. the live full `test_post_contract_state_integrity` suite is green at `372` tests after this shared prior-branch restore candidate-discovery alignment pass
144. current `IC4-A` / `IC4-B` posture: the remaining restore-path inline gravity now appears very close to pure facade orchestration order rather than shared policy ownership, which strongly suggests this cleanup block is approaching its intended closure point and that any larger extraction beyond this should be deferred to the later dedicated `service.py` refactor chapter

145. latest completed `IC3` slice: control-evidence restore interpretation now also composes through the shared `conversation_control_language.py` layer, so `service.py` no longer locally owns restore-target extraction, control-action-to-phrase-type mapping, or control-evidence internal-detail tagging for the prior-branch restore snapshot builder
146. the live server-side verification is green at `382` tests after this shared control-language restore-interpretation alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
147. current posture: `IC5-C` remains closed for the current delivery chapter, while `IC3` continues to narrow the remaining owner-activation and shared control-language seams before we return to the broader `IC2` close-out and later `IC6` hand-off decision

148. latest completed `IC3` slice: clarification-yield override gating now also composes through the shared `conversation_control_support.py` layer, so `service.py` no longer locally owns whether a clarification decision may yield to a shared initial-control owner or a shared current-control owner
149. the live server-side verification is green at `385` tests after this shared clarification-yield alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
150. current posture: `IC3` is continuing to narrow the remaining owner-activation seams around shared control and clarification interaction, while `IC5-C` remains closed for the current delivery chapter and `IC2` still waits for close-out review after `IC3`

151. latest completed `IC3` slice: clarification-response decision classification now also composes through the shared `conversation_control_support.py` layer, so `service.py` no longer locally owns the decision-to-action matrix for clarification resolution, option-list replay, fresh-request override, branch discard, meta question, acknowledgement, and reask mapping
152. the live server-side verification is green at `386` tests after this shared clarification-decision-spec alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
153. current posture: `IC3` is now increasingly narrowed to the remaining control-language / clarification interaction seams that still materially affect shared owner activation, while `IC5-C` remains closed and `IC2` still stays queued behind `IC3` closure work

154. latest completed `IC3` slice: front-door clarification reentry and reset predicates now also compose through the shared `conversation_control_support.py` layer, so `service.py` no longer locally owns resolved-slot extraction, front-door reentry message selection, artifact-boundary runtime-reset gating, or front-door fresh-query-reset gating for clarified turns
155. the live server-side verification is green at `387` tests after this shared clarification-reentry alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
156. current posture: `IC3` is now focused on the remaining small set of shared control-language and clarification interaction seams that still materially influence owner activation, while final clarified-turn state application remains intentionally in the facade and `IC2` still follows after `IC3` closure work

157. latest completed `IC3` slice: clarified runtime-message resolution now also composes through the shared `conversation_control_support.py` layer, so `service.py` no longer locally owns how clarification outcomes become either a fresh business request or a resolved continuation message for clarified follow-up turns
158. the live server-side verification is green at `388` tests after this shared clarified-runtime-message alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
159. current posture: `IC3` is now down to a very small set of remaining clarification/control interaction seams, while clarified-turn state application still stays intentionally in the facade and `IC2` remains queued behind final `IC3` closure work

160. latest completed `IC3` slice: pending-clarification fallback precedence now also composes through the shared `restore_support.py` layer, so `service.py` no longer keeps a second local copy of the non-authoritative pending-clarification and candidate-precedence rule used by restore arbitration
161. the live server-side verification is green at `389` tests after this shared pending-clarification precedence alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
162. current posture: `IC3` is now very close to closure, with only a tiny remaining set of clarification/control seams to evaluate before we decide whether further extraction would become facade churn and hand back to `IC2`

163. latest completed `IC3` slice: completed-sequence supersession precedence now also composes through the shared `conversation_control_support.py` layer, so `service.py` no longer locally owns when a finished or cancelled active sequence must yield to a newer authoritative pending clarification, recent focus, or resumable prior branch
164. the live server-side verification is green at `390` tests after this shared completed-sequence supersession alignment pass, including `test_post_contract_state_integrity`, `test_clarification_lane_compatibility`, and `test_restore_support_contracts`
165. current posture: `IC3` is now reduced further to the tiny remaining clarification/control ownership seams that still look like reusable policy, while sequence-completion snapshot precedence has joined the shared control-support layer and `IC2` remains queued behind final `IC3` closure review

166. bounded `IC3` closure audit completed: the remaining `service.py` clarification/control seams are now adapter-or-orchestration bridges such as contract-to-state normalization, decision-contract envelope assembly, and clarified-turn state application, rather than uncovered shared policy
167. decision: stop further `IC3` extraction here for the current chapter, because additional movement would mainly create facade churn instead of reducing mixed authority
168. next planned step: treat `IC3` as ready for closure review and return to the queued `IC2` close-out work, while leaving the broader `service.py` stage refactor for the later dedicated refactor chapter

169. `IC2` close-out review completed: the shared precedence evaluator now covers clarification breakout, fresh-request override, strong-owner suppression, sequence completion gating, recent-focus suppression, and question-restore / branch-restore latest-owner arbitration across the current supported chapter surface
170. decision: treat `IC2` as complete for the current delivery chapter, because the remaining open work is future-family expansion and facade refactor cleanup rather than missing shared precedence policy
171. next planned step: keep `IC3` as ready for closure review, then move to the deliberate hand-off decision between `IC6` entry work and the later dedicated `service.py` refactor chapter

172. `IC3` closure review completed: the shared control-language layer now covers the current chapter surface for clarification interaction, redirect/discard, option-list request, question restore, targeted restore, sequence continuation, and sequence stop without relying on new family-local phrase branches
173. decision: treat `IC3` as complete for the current delivery chapter, because the remaining open work is future language breadth and facade-stage cleanup rather than missing shared control-language policy
174. next planned step: begin `IC6` entry with a bounded multi-step assessment generalization slice, while continuing to defer the broader `service.py` refactor to its own chapter
175. completed `IC6-S1`: the current ordered compound-request assessment now carries a backward-compatible normalized `multi_step_assessment` bridge, and that bridge stays coherent through assessment creation, compiled-step advancement, and service-level completion / cancellation rebuilds
176. focused server-side characterization is green at `393` tests after the `IC6-S1` bridge pass, covering assessment, front-door preservation, active-sequence advancement, and completion / cancellation state transitions
177. completed `IC6-S2`: the current ordered compound-request bridge now also carries a typed `qwen_multi_step_execution_plan_contract` with governed step ids, dependency edges, carryover classes, interruption policy, and clarification policy
178. focused server-side characterization remains green at `393` tests after the `IC6-S2` pass, proving the typed plan contract survives assessment creation, front-door preservation, active-sequence advancement, and completion / cancellation transitions
179. completed `IC6-S3`: the current ordered compound-request bridge now also carries a typed `qwen_multi_step_execution_state_contract` with governed lifecycle state, current-step focus, remaining steps, completed steps, and last-completed-step tracking
180. focused server-side characterization remains green at `393` tests after the `IC6-S3` pass, proving the shared execution-state contract survives assessment creation, front-door preservation, active-sequence advancement, and completion / cancellation transitions
181. completed `IC6-S4`: the current ordered compound-step flow now emits a typed `qwen_multi_step_step_result_integration_contract` that makes recent-focus promotion, carryover classes, and interruption-owner policy explicit for grounded results and clarification outcomes
182. focused server-side characterization is green at `394` tests after the `IC6-S4` pass, proving the new result-integration contract through both the shared builder path and the live compiled-step execution path
183. completed `IC6-S5`: the shared compound-request layer now owns post-result advancement versus clarification pause, and the assessment bridge preserves the active step while waiting for clarification instead of dropping the current-step pointer
184. focused server-side characterization is green at `397` tests after the `IC6-S5` pass, proving the full assessment / plan / execution-state / result-integration stack through grounded-result execution, clarification pause, front-door preservation, and post-contract state integrity
185. completed the `IC6` closure checkpoint: `IC6` is now complete for the current delivery chapter, and further widening is intentionally deferred unless a genuinely new governed execution requirement appears
186. immediate next program step: return to the broader Phase B1 + C1 backbone work while keeping this conversation-control spine stable and shared
