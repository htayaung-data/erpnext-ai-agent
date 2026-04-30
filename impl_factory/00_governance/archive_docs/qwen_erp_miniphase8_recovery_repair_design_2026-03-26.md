# Qwen ERP Mini-phase 8 Recovery and Conversational Repair Design (2026-03-26)

## 1. Objective

Mini-phase 8 adds a dedicated recovery and conversational repair layer.

Its purpose is not to replace:

1. clarification authority
2. front-door intent handling
3. governed artifact execution
4. ERP business reasoning execution
5. knowledge-boundary validation

Its purpose is to:

1. recover safely when artifact enrichment or continuation cannot proceed
2. convert accepted alternatives into clean fresh governed queries
3. distinguish instruction / guidance questions from data requests
4. prevent stale context from trapping valid fresh asks
5. support bounded repair when the user is trying to continue a valid business thread but the current lane cannot satisfy it directly

Mini-phase 8 exists because even with strong routing, reasoning, and boundary contracts, the system still needs one explicit authority for:

1. structured recovery options
2. safe conversational repair
3. alternative acceptance handling
4. stronger fresh-query override in ambiguous continuation contexts

## 2. Non-Negotiable Rules

Mini-phase 8 must not:

1. become a generic fallback chatbot
2. become a keyword patch layer for frustrating transcripts
3. silently rewrite user intent without explicit structural evidence
4. bypass governed query compilation when a fresh governed query is required
5. swallow valid clarification, artifact, reasoning, or boundary ownership

Mini-phase 8 must:

1. operate after the earlier authorities have had a fair chance to answer
2. emit explicit recovery / repair contracts
3. preserve safe scope, entity, and time context only when structurally justified
4. convert accepted alternatives into fresh governed queries rather than fuzzy continuation loops
5. keep deterministic authority over final repair actions and recovery safety

## 3. Position In The Lane Stack

Recommended precedence:

1. Clarification Resolution Authority
2. FrontDoorIntentGate
3. Governed ERP Artifact Lane
4. ERP Business Reasoning Lane
5. Knowledge Boundary Layer
6. Recovery / Conversational Repair Layer

Meaning:

1. Mini-phase 8 does not get first pick
2. it is activated only after the existing lanes and boundary layer determine that normal handling is insufficient or mismatched
3. it repairs failure surfaces and instruction-style follow-ups without reopening earlier phase ownership

## 4. Scope

### 4.1 In Scope

Mini-phase 8 should handle:

1. artifact enrichment recovery
2. alternative acceptance turning into fresh governed query execution
3. instruction / guidance questions such as:
   - `how can I instruct you`
   - `what should I ask for`
   - `how do I get qty`
4. explicit fresh-query override over stale grounded context
5. bounded recovery when analytical follow-up drift or failed enrichment leaves the user trying to continue a valid business task

Representative examples:

1. `yes please run separate governed query on qty`
2. `how should I ask you to get quantity by product`
3. `just give me top 7 product revenue qty`
4. `no, I mean use a different governed report`
5. `show it another way if this source cannot provide that field`

### 4.2 Out Of Scope

Mini-phase 8 should not handle:

1. broad dissatisfaction coaching
2. free-form escalation therapy
3. OCR or document ingestion
4. CRUD / write actions
5. broad world-knowledge instruction outside the ERP assistant surface

Those belong to later product chapters.

## 5. Core Responsibility

The exact responsibility of Mini-phase 8 is:

1. detect when a normal governed answer path has hit a structured dead-end
2. decide whether there is a safe recovery option
3. expose that option as a contract rather than as ad hoc prose
4. if the user accepts a safe alternative, convert it into a fresh governed query with preserved justified context
5. distinguish guidance questions about how to use the assistant from actual data requests

It should answer:

1. is this a failed enrichment / failed continuation case?
2. is the user accepting a prior recovery option?
3. is this a guidance / instruction request instead of a data request?
4. is this an explicit fresh ask that should override stale context?

## 6. Contract Model

Mini-phase 8 should introduce two main contracts.

### 6.1 ArtifactEnrichmentRecoveryContract

This contract is for recovery after artifact-boundary / enrichment-boundary failures.

Suggested fields:

1. `request_id`
2. `session_id`
3. `source_request_id`
4. `source_family_id`
5. `source_capability_id`
6. `source_report`
7. `failure_type`
8. `recovery_state`
9. `available_recovery_actions`
10. `recommended_recovery_action`
11. `preservable_scope`
12. `preservable_dimensions`
13. `preservable_metrics`
14. `preservable_time_context`
15. `alternative_capability_id`
16. `alternative_report`
17. `reason`
18. `allowed_to_recover`
19. `confidence`

Recommended normalized values:

#### 6.1.1 `failure_type`

1. `artifact_enrichment_incompatible`
2. `grounded_evidence_missing`
3. `reasoning_source_mismatch`
4. `unsupported_continuation_target`

#### 6.1.2 `recovery_state`

1. `recoverable`
2. `clarify_recovery_target`
3. `unavailable`

#### 6.1.3 `available_recovery_actions`

1. `keep_current_artifact`
2. `run_alternative_governed_query`
3. `clarify_target_output`
4. `unavailable`

### 6.2 ConversationalRepairIntentContract

This contract is for instruction / repair / explicit override interpretation.

Suggested fields:

1. `request_id`
2. `session_id`
3. `repair_intent_type`
4. `repair_state`
5. `targets_prior_recovery`
6. `accepted_recovery_action`
7. `guidance_topic`
8. `fresh_query_override`
9. `preserve_scope`
10. `preserve_entity_dimension`
11. `preserve_time_context`
12. `reason`
13. `allowed_next_lane`
14. `confidence`

Recommended normalized values:

#### 6.2.1 `repair_intent_type`

1. `accept_recovery_action`
2. `guidance_request`
3. `fresh_query_override`
4. `repair_reframe`
5. `not_applicable`

#### 6.2.2 `repair_state`

1. `accepted`
2. `guidance_only`
3. `route_fresh_query`
4. `unresolved`

## 7. Decision Logic

Mini-phase 8 should evaluate in this order:

1. is there an active recovery contract from the immediately prior failed enrichment / boundary?
2. if yes, is the current user turn accepting one of the available recovery actions?
3. if not, is the current user turn actually asking for guidance on how to ask the assistant?
4. if not, is the user issuing an explicit fresh governed ask that should override stale context?
5. if not, keep earlier lane ownership or return unresolved repair safely

This keeps Mini-phase 8 from becoming a vague “anything confusing goes here” layer.

## 8. Recovery Rules

### 8.1 Accepted Alternative Must Become Fresh Governed Query

If a recovery option such as `run_alternative_governed_query` is accepted, Mini-phase 8 must:

1. build a fresh governed query input
2. preserve only structurally safe context:
   - same company
   - same time scope when justified
   - same entity or grouping dimension when justified
   - requested target metric / report change
3. send the result back through governed compilation

It must not:

1. answer from the old artifact as if nothing changed
2. stay in a continuation loop
3. silently broaden or narrow the scope without contract evidence

### 8.2 Guidance / Instruction Requests

When the user asks how to obtain a result, Mini-phase 8 should route to a guidance output, not to data retrieval.

Examples:

1. `how do I get qty`
2. `how should I ask for top 10 products with revenue and qty`
3. `what should I type to see overdue customers`

The response should be:

1. bounded to supported governed surfaces
2. concrete enough to help the user
3. not a fake data answer

### 8.3 Fresh-Query Override

Mini-phase 8 should strengthen explicit fresh asks such as:

1. `just give me top 7 product revenue qty`
2. `no, show me sales by item instead`
3. `forget that, show me receivable aging`

If a turn is structurally a fresh governed ask, Mini-phase 8 should prefer:

1. fresh governed compilation

over:

1. stale continuation
2. stale recovery loop
3. prior reasoning continuation

## 9. Deterministic vs AI Authority

Deterministic authority should own:

1. recovery contract schema
2. available recovery actions
3. acceptance safety
4. context-preservation rules
5. fresh-query override safety
6. final decision to run a fresh governed query

AI may help with:

1. proposing nuanced guidance phrasing
2. interpreting whether a turn sounds like an instruction request
3. rendering repair responses more naturally

AI must not be:

1. the final authority for context preservation
2. the final authority for whether recovery is available
3. the final authority for whether an alternative becomes a fresh governed query

## 10. Implementation Slices

Mini-phase 8 should be implemented in bounded slices:

### 8A. Recovery Contract Foundation

Build:

1. `ArtifactEnrichmentRecoveryContract`
2. `ConversationalRepairIntentContract`
3. normalization helpers and probes

Exit:

1. recovery / repair contracts exist and are testable in isolation

### 8B. Enrichment Recovery Authority

Build:

1. recovery contract emission from artifact enrichment / evidence boundary cases
2. structured available recovery actions
3. safe preservation metadata

Exit:

1. failed enrichment no longer ends only with prose; it also emits explicit recovery authority

### 8C. Alternative Acceptance and Guidance Handling

Build:

1. repair / guidance interpretation
2. accepted recovery action -> fresh governed query conversion
3. instruction / guidance response path

Exit:

1. `yes please run separate governed query on qty` becomes a fresh governed query
2. `how do I ask for qty` becomes bounded guidance rather than data retrieval

### 8D. Strong Fresh-Query Override

Build:

1. override checks against stale grounded or repair context
2. stronger precedence for explicit fresh asks
3. regression locks for stale-context failures

Exit:

1. explicit fresh asks win cleanly over stale continuation / repair state

## 11. Observability

Mini-phase 8 should emit structured recovery / repair events:

1. `recovery_contract_emitted`
2. `recovery_action_accepted`
3. `guidance_request_handled`
4. `fresh_query_override_applied`
5. `recovery_unavailable`

Minimum details:

1. `failure_type`
2. `recovery_state`
3. `accepted_recovery_action`
4. `preserved_scope`
5. `next_lane`

## 12. Completion Criteria

Mini-phase 8 is complete when:

1. failed enrichment emits structured recovery contracts
2. safe alternative acceptance becomes fresh governed query execution
3. instruction / guidance asks are no longer misrouted as data requests
4. explicit fresh-query override is stronger and regression-tested
5. no keyword-bag repair rules were introduced
6. browser regression pack confirms recovery and guidance behavior in live flow

## 13. Honest Boundary

Mini-phase 8 should improve recovery and repair materially, but it still should not become:

1. a general emotional support layer
2. a free-form copilot for anything ambiguous
3. a write-action authority

Its job is disciplined recovery, not infinite conversational improvisation.

## 14. Current Status

Mini-phase 8A, 8B, 8C, and 8D are now implemented.

Implemented:

1. `ArtifactEnrichmentRecoveryContract` in `contracts.py`
2. `ConversationalRepairIntentContract` in `contracts.py`
3. builder helpers:
   - `build_artifact_enrichment_recovery_contract(...)`
   - `build_conversational_repair_intent_contract(...)`
4. recovery-authority builders:
   - `build_recovery_contract_from_enrichment_compatibility(...)`
   - `build_recovery_contract_from_evidence_boundary(...)`
5. service-layer recovery emission helpers:
   - `_append_grounded_evidence_recovery_contract(...)`
   - `_append_enrichment_recovery_contract(...)`
6. runtime boundary emission is now wired into:
   - `grounded_evidence_boundary`
   - `artifact_enrichment_boundary`
7. Phase 8 probes:
   - `run_phase8a_recovery_contract_probe()`
   - `run_phase8b_recovery_authority_probe()`
   - `run_phase8b_recovery_authority_smoke()`
8. semantic repair / guidance interpretation is now implemented in:
   - `semantic_repair_intent.py`
   - runtime `/interpret-repair-intent` endpoint
9. accepted governed recovery alternatives now convert into fresh governed queries
10. bounded guidance replies now render from the active recovery contract
11. Phase 8C smoke:
   - `run_phase8c_repair_handling_smoke()`
12. strong fresh-query override is now implemented in live orchestration:
   - recovery handling is skipped when `context_isolation.force_new_query` is true
   - front-door early return is skipped when `context_isolation.force_new_query` is true
   - explicit fresh governed asks no longer get trapped by stale recovery context
13. Phase 8D smoke:
   - `run_phase8d_fresh_query_override_smoke()`

Verified:

1. `py_compile`
2. enterprise guardrail audit
3. live backend probe for:
   - recoverable enrichment recovery contract
   - accepted recovery-intent contract
   - governed enrichment recovery authority
   - evidence-boundary recovery authority
4. service smoke confirms session-level recovery payload emission for grounded evidence recovery
5. service smoke confirms:
   - `how do I ask for qty` -> `recovery_guidance`
   - `yes please run the governed alternative` -> fresh governed query execution
6. service smoke confirms:
   - stale recovery session + explicit fresh governed ask -> `compiled_first_turn`
   - no stale recovery guidance leak into the new answer
7. recovery-execution hardening now also confirms:
   - ranking metric-basis enrichment stops at `artifact_enrichment_boundary`
   - accepted alternative execution compiles into a fresh governed quantity query
   - mixed metric follow-up stays in `recovery_guidance` instead of fabricating a combined artifact

Honest judgment:

1. Mini-phase 8 is now materially real, not just planned
2. prior recovery now has two live outcomes:
   - bounded guidance
   - fresh governed alternative execution
3. strong fresh-query override is now structurally enforced through context isolation, not phrase patches
4. recovery execution is now materially hardened for ranking metric-basis repair, not just seeded acceptance paths
5. manual browser closure review passed for:
   - AR reasoning continuity remaining intact after Phase 8 work
   - `Top 7 products by revenue` -> `include qty column` stopping safely in recovery guidance
   - explicit acceptance `yes run that` executing the governed quantity alternative on the next turn
   - fresh-query override such as `forget that, just analyze AR` dropping stale recovery context cleanly
6. recovery acceptance persistence is now structurally fixed:
   - the explicit acceptance user turn is persisted before fresh governed execution
   - substantive refinement turns no longer auto-trigger acceptance
7. Mini-phase 8 is now closed for its intended scope
8. separate governed multi-metric ranking artifacts such as `Revenue + Qty together` remain future product expansion, not a Phase 8 blocker
