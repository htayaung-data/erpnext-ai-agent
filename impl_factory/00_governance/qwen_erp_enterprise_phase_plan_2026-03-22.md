# Qwen ERP Enterprise Phase Plan (2026-03-22)

Scope: execution-phase plan for the governed Qwen ERP assistant  
Status: active implementation roadmap

This document updates the original phase plan with the enterprise hardening ideas identified during implementation review.

The blueprint remains the target architecture.  
This phase plan is the practical execution order.

## Guiding Rule

The system should not grow by adding phrase-specific fixes.

The steering rule after Qwen-Agent consultation is:

- `model proposes, compiler enforces`

Each phase must strengthen one of these enterprise properties:

1. semantic interpretation
2. deterministic execution
3. governed validation
4. auditable behavior
5. safe expansion

## Updated Phase Plan

### Phase 1: Contract Foundation

Deliver:

- `InteractionContract`
- `GroundedTurnContext`
- `FollowUpResolution`
- `ExecutionPath`

Status:

- `completed`

### Phase 2: Read Query Hardening

Deliver:

- capability registry
- report registry
- ontology and validation metadata
- tool gateway policy
- grounded validation
- audit envelope expansion

Status:

- `completed`

### Phase 3: Follow-Up Interpretation and Local Transform System

Deliver:

- semantic follow-up interpretation contract
- presentation transform path
- table presentation path
- sort/limit path
- dimension breakdown path
- column projection path
- filter refinement path
- regroup / metric-change path
- sibling-switch path
- confidence policy for semantic interpretation
- degraded-mode audit and no silent fallback
- clarify path when semantic interpretation is low-confidence
- bounded compatibility fallback for safe local transforms only

Status:

- `in progress`

Why this phase changed:

- follow-up handling must be semantic and typed
- local transforms must be deterministic
- enterprise behavior requires explicit degraded-mode control
- follow-up expansion must stay bounded until fresh-query compilation is governed

### Phase 4: Fresh Query Compiler and Intent-Result Validation

Deliver:

- `FreshQueryCompilerContract`
- fresh-query interpretation contract
- compiled query request contract
- model-proposed intent class and slot extraction
- business request to capability resolution
- compiler-selected report family / report id
- required filter completion
- single-company invariant injection
- default date / report-date completion
- clarify vs execute decision
- typed compiled runtime request
- semantic intent-to-result validation
- execution rejection when grounded result is semantically inconsistent with requested intent
- co-located compiler topology with no separate interpretation microservice

Status:

- `in progress`

Why this phase was added:

- first-turn business requests are still less reliable than follow-ups
- enterprise quality requires governed compilation before agent execution
- grounding alone is not sufficient; intent-to-result correctness must also be enforced
- latency should not worsen by splitting interpretation and compilation into separate network tiers

### Phase 4B: Semantic Family Layer and Broad Read Expansion

Deliver:

- `ReportFamilyContract`
- `NormalizedFamilyArtifactContract`
- `CompositeReadPlanContract`
- family registry
- family adapters
- financial statement adapter path
- aging adapter path
- ranking/trend adapter path
- inventory/product profitability adapter path
- family-level semantic validation
- compiler-approved composite read execution
- reduced high-level family tool surface for Qwen-Agent

Status:

- `in progress`

Why this phase is needed:

- Phase 4 solved first-turn governance, but broad ERP coverage still cannot scale cleanly by report id alone
- common business domains such as statements, aging, trends, and rankings need canonical family normalization
- composite questions such as company health require governed multi-family execution rather than raw model synthesis
- enterprise breadth now depends on semantic family abstraction, not just more report additions

### Phase 5: Artifact System

Deliver:

- table artifact
- chart artifact
- dashboard proposal
- PNG download path

Status:

- `not started`

### Phase 6: Multilingual Layer

Deliver:

- language detection
- Burmese normalization
- bilingual glossary
- same-language reply policy
- multilingual validation support

Status:

- `not started`

### Phase 7: Write Safety System

Deliver:

- `ActionProposalContract`
- preview card
- confirmation flow
- controlled create/update/delete execution
- destructive action policy

Status:

- `not started`

### Phase 8: Security Hardening

Deliver:

- dedicated service user
- least-privilege permissions
- read/write credential split
- secret rotation
- rate limiting
- audit strengthening

Status:

- `not started`

### Phase 9: Enterprise UX

Deliver:

- structured cards for tables/charts/actions
- better session/context UX
- artifact/history handling
- confirmation and download UX

Status:

- `not started`

### Phase 10: Evaluation and Release Governance

Deliver:

- smoke packs
- golden datasets
- multilingual tests
- write safety tests
- rollback and release gates

Status:

- `not started`

### Phase 11: Productionization

Deliver:

- observability
- scaling/runtime deployment
- self-hosted Qwen option
- operational playbooks

Status:

- `not started`

## Consultation-Informed Steering Corrections

The Qwen-Agent architecture review reinforced these decisions:

1. Qwen/Qwen-Agent should own:
   - natural-language understanding
   - intent classification
   - slot extraction
   - grounded summarization
2. deterministic compiler/policy layers should own:
   - report selection
   - company injection
   - required filter completion
   - clarify vs execute decision
   - semantic result validation
3. follow-up semantics should remain governed, but this layer should not keep growing while fresh-query compilation remains under-governed
4. separate semantic interpretation round-trips should be treated as a bounded reliability mechanism, not the permanent center of the architecture

## Current Position (2026-03-22)

We are here:

- Phase 1: complete
- Phase 2: complete
- Phase 3: active
- Phase 4: active as the next primary implementation track

Implemented inside Phase 3:

- semantic follow-up interpretation as the primary path
- local presentation transforms
- local sort/limit transforms
- local dimension breakdown transforms
- semantic sibling-switch routing
- semantic confidence policy
- explicit degraded-mode audit
- bounded compatibility fallback for safe local transforms only
- runtime follow-up interpretation hardening with retry/backoff and JSON repair
- response policy contract passed into runtime execution
- preserved response policy:
  - grounded facts first
  - table/breakdown next
  - concise interpretation only when relevant and grounded
  - fuller recommendations only on explicit request

Still open inside Phase 3:

1. generic column projection from grounded tables
2. generic filter refinement from grounded context
3. generic regroup / metric-change path
4. explicit reject/clarify policy when semantic interpretation is low-confidence and no safe compatibility fallback exists
5. stronger follow-up audit detail for requested vs applied transforms

## What Is Next

The next implementation order is now:

1. stabilize the open Phase 3 reliability boundary only:
   - explicit clarify path
   - stronger follow-up audit detail
2. continue Phase 4 as the primary enterprise reliability track:
   - Slice 1 contract and metadata foundation: completed
   - Slice 2 compiler core in ERP layer: completed
   - Slice 3 model proposal integration: completed
   - Slice 4 compiled execution path: completed
   - Slice 5 semantic intent-to-result validation: completed
   - Slice 6 audit and observability: completed
3. begin Phase 4B as the next scaling track after the Phase 4 foundation:
   - Slice 4B.1 family registry and contracts: completed
   - Slice 4B.2 financial statement adapter: completed
   - Slice 4B.3 aging adapter: completed
   - Slice 4B.4 ranking/trend adapters: completed
   - Slice 4B.5 inventory/product profitability adapters: completed
   - Slice 4B.6 composite read planning: completed
   - enterprise checkpoint after Slice 4B.6: completed
   - Slice 4B.7 family-level validation and rendering: completed
   - Slice 4B.8 family tool surface for Qwen-Agent: completed
   - Slice 4B.9 family-based evaluation and rollout: completed
   - current governed family baseline after post-4B.9 hardening: 7 of 7 core family cases passing
   - legacy family tool routing now uses governed family narrowing, with compiled execution still preferred for richer families
   - post-4B composite latency hardening: completed
   - latest governed evidence shows `working_capital_health` composite runtime reduced to about 15.6s with compiler-approved parallel child execution
   - post-family proposal resilience hardening: completed
   - deterministic family-level request defaults now protect ranking, trend, aging, inventory, and product families when proposal output is underspecified
   - deterministic family-surface fallback now preserves governed compilation when runtime semantic proposal is unavailable or invalid
   - latest full governed family evaluation suite now passes `11/11`
   - next work has moved from one remaining family gap into broader post-4B operational hardening and family-package expansion
4. return to the remaining Phase 3 convenience expansions after Phase 4B establishes the broad governed read path:
   - column projection
   - filter refinement
   - regroup / metric-change

## Recommended Steering Rule

Do not expand charts, writes, or multilingual behavior until:

1. Phase 3 follow-up behavior is semantically governed
2. Phase 4 fresh-query compilation is governed and reliable
3. semantic result validation can reject grounded-but-wrong answers

Those two phases are the core reliability gate for the enterprise read path.

## Phase Exit Intent

### Phase 3 exit intent

Phase 3 should close only when:

1. short follow-ups are interpreted semantically, not primarily by phrase matching
2. local transforms are deterministic and auditable
3. degraded mode is explicit, logged, and governable
4. low-confidence follow-ups can safely clarify rather than drift or silently fallback

### Phase 4 exit intent

Phase 4 should close only when:

1. vague first-turn business questions compile into governed requests reliably
2. required report filters are completed or clarified before execution
3. the system can distinguish:
   - execute now
   - ask clarification
   - reject unsupported request
4. company is injected centrally as an invariant and is never a user-visible failure burden
5. semantically inconsistent grounded results are rejected before answer display

Current Phase 4 note:

- Slice 3 contract and ERP-side validation/compilation handoff are implemented
- deterministic selftests passed
- runtime boundary was hardened with:
  - separate fresh-query runtime timeout
  - shared Docker network alias
  - ERP-side fresh-query timeout config
- advisory smoke pack now shows governed `execute` and `clarify` outcomes across representative first-turn requests
- Slice 4 compiled execution smoke now shows:
  - typed compiled request reaching the runtime
  - compiled mode restricted to the exact governed report and filters
  - single-tool grounded execution with successful validation
- Slice 5 semantic validation now shows:
  - deterministic post-runtime semantic checks in ERP
  - explicit `pass`, `clarify`, and `reject_semantically_inconsistent` outcomes
  - metadata-driven dimension/metric support checks
  - real compiled payable smoke passing semantic intent-to-result validation
- Slice 6 audit/observability now shows:
  - dedicated compiled first-turn audit payload
  - compiler, runtime, and semantic validation status in one governed record
  - per-stage latency breakdown for proposal, compilation, runtime execution, and semantic validation
  - real compiled observability smoke passing with grounded and semantic validation `pass`
  - rollout-gated live-service branch implemented with default-off posture
  - live-service smoke confirming compiled-path artifacts persist correctly when the flag is enabled
  - monitoring helper available to summarize compiled audit outcomes before any broader rollout
  - rollout-monitoring smoke now confirms the summary path observes real compiled audit traffic
  - rollout governance now supports:
    - master enable flag
    - deterministic canary percentage
    - allowlisted users
    - explicit audited fallback to the legacy read path when compiled proposal generation fails operationally
  - rollout governance helper and selftest now exist before any broader enablement
  - initial monitored sample shows proposal generation latency is the dominant first-turn bottleneck
  - runtime-side governed proposal cache now reduces repeated first-turn proposal latency from cold-path seconds to warmed-path milliseconds
  - compiled audit monitoring now exposes proposal cache hit state and cache hit rate
  - compiled audit monitoring now also exposes rollout status, proposal shared-inflight reuse rate, and rollout fallback rate
  - runtime now has dedicated fresh-query proposal tuning levers for cold-path latency without changing compiler governance
  - production posture remains single-model by default, with separate proposal-model routing kept only as an optional later optimization

Current Phase 4B note:

- Slice 4B.1 family registry and contracts are now implemented as the shared foundation
- Slice 4B.2 financial statement adapters are now implemented for:
  - Profit and Loss Statement
  - Balance Sheet
  - Cash Flow
- Slice 4B.3 aging adapters are now implemented for:
  - Accounts Receivable Summary
  - Accounts Receivable
  - Accounts Payable Summary
  - Accounts Payable
- Slice 4B.4 ranking/trend adapters are now implemented for:
  - `ranking_analytics`
  - `trend_analytics`
  - family-hinted routing when one governed report supports more than one business family
- Slice 4B.5 inventory/product profitability adapters are now implemented for:
  - `inventory_snapshot`
  - `product_profitability`
  - item-level stock snapshots and warehouse-tree stock snapshots
  - gross-profit and item-sales-history product normalization
- normalized aging artifacts now pass through family validation inside the compiled execution path
- normalized financial statement artifacts now pass through family validation inside the compiled execution path
- normalized ranking and trend artifacts now pass through family validation inside the compiled execution path
- normalized inventory and product profitability artifacts now pass through family validation inside the compiled execution path
- Slice 4B.6 composite read planning is now implemented with:
  - governed composite profile metadata
  - compiler-approved composite execution plans
  - persisted composite plan and composite audit artifacts
  - deterministic composite AR/AP working-capital health execution
  - sequential execution as the current safe runtime posture because Frappe runtime configuration is thread-local in worker child threads
- Slice 4B.7 family-level validation and rendering is now implemented with:
  - governed rendered family response contracts
  - governed composite validation contracts
  - renderer metadata per family
  - deterministic answer rendering from normalized family/composite artifacts
  - service-path preference for canonical rendered answers over runtime prose
- enterprise checkpoint after Slice 4B.6 confirms:
  - the architecture remains aligned with enterprise governance boundaries
  - the project is not drifting into phrase-specific hacks
  - the next needed work is canonical family/composite rendering and validation tightening, not redesign
- compiler-approved composite read planning is now implemented for the working-capital / AR-AP company-health class
- governed composite execution now persists:
  - composite read plans
  - step-level normalized family artifacts
  - composite validation payloads
  - composite execution audit payloads
- the next architecture gap is no longer first-turn governance foundation
- the next active implementation step is family-level validation and rendering
- common business families are now explicitly registered as first-class governed execution units:
  - financial statements
  - aging
  - trend/ranking analytics
  - inventory snapshot
  - product profitability
- composite business analysis should become compiler-approved multi-family execution, not free-form model synthesis
- multi-family routing is now explicitly tightened for shared governed reports such as `Sales Analytics` and AR/AP summaries
- stock and product metadata are now aligned so capability intent coverage matches governed family coverage
- runtime answer rendering is now materially tightened around normalized family/composite artifacts, but family-tool reduction and broader rollout governance are still open
- composite execution is intentionally serialized for correctness in the current Frappe worker/runtime model because configuration is thread-local in child threads
- post-family resilience hardening now closes the last evaluated family miss through family-level deterministic defaults rather than report-specific patches
- the Phase 4B implementation reference is:
  - `impl_factory/00_governance/qwen_erp_phase4b_semantic_family_layer_plan_2026-03-22.md`

## Summary

The plan is now:

- Phase 1 and Phase 2 are done
- Phase 3 is active but intentionally bounded
- Phase 4 foundation is implemented and remains the reliability gate
- Phase 4B is the next breadth and scaling gate for the governed read path
- the architecture direction is now explicitly:
  - Qwen proposes
  - compiler enforces
  - validator confirms

So the project is in the middle of the enterprise read-path build, not at the beginning and not yet at production hardening.
