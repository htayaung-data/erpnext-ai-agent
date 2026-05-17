# Qwen ERP Mini-phase 7 KnowledgeBoundaryContract Design (2026-03-26)

## 1. Objective

Mini-phase 7 adds a dedicated knowledge-boundary layer.

Its purpose is not to replace:

1. clarification authority
2. front-door intent handling
3. governed artifact execution
4. ERP business reasoning execution

Its purpose is to:

1. validate whether the chosen lane is actually appropriate
2. prevent lane-bouncing between artifact, reasoning, and front door
3. distinguish supported grounded ERP questions from valid-but-not-yet-covered ERP/business questions
4. enforce safe exits when the system would otherwise overreach

Mini-phase 7 exists because even with good front-door and reasoning layers, the system still needs one explicit authority for:

1. lane suitability
2. knowledge coverage
3. unsupported-boundary handling

## 2. Non-Negotiable Rules

Mini-phase 7 must not:

1. become a hidden front-door replacement
2. become a keyword router
3. override clarification precedence
4. silently invent a new lane outcome without contract evidence
5. become a generic fallback chatbot layer

Mini-phase 7 must:

1. read the outputs of prior authorities rather than replacing them
2. validate lane fitness structurally
3. distinguish unsupported from uncovered-but-valid ERP/business asks
4. emit one explicit boundary contract
5. provide stable, auditable reason codes

## 3. Position In The Lane Stack

Recommended precedence:

1. Clarification Resolution Authority
2. FrontDoorIntentGate
3. Governed ERP Artifact Lane
4. ERP Business Reasoning Lane
5. Knowledge Boundary Layer
6. Recovery / Conversational Repair Layer

Meaning:

1. clarification still has highest precedence when pending
2. front door still owns safe conversational turns
3. artifact lane still owns fresh governed retrieval and artifact continuation
4. reasoning lane still owns grounded interpretation/recommendation
5. boundary layer validates the chosen result before final commitment

So Mini-phase 7 is primarily a late-stage validator and arbitration layer, not an early first-pass classifier.

## 4. Scope

### 4.1 In Scope

Mini-phase 7 should decide whether a turn/result belongs to:

1. `front_door`
2. `artifact_lane`
3. `reasoning_lane`
4. `clarification`
5. `valid_erp_domain_uncovered`
6. `unsupported_request`

Representative examples:

1. a broad business question with no governed grounding
2. a reasoning-shaped request over a transactional listing
3. a fresh ERP question that looks analytical but is really governed retrieval
4. a valid ERP/business education ask not yet supported by grounded artifact or bounded reasoning
5. a request that belongs nowhere in ERP scope

### 4.2 Out Of Scope

Mini-phase 7 should not:

1. recover from failed enrichment continuations
2. own dissatisfaction handling
3. do multi-turn repair coaching
4. generate fresh governed queries
5. expand front-door class taxonomy

Those belong to Mini-phase 8 or later integration work.

## 5. Core Responsibility

The exact responsibility of the Knowledge Boundary Layer is:

1. inspect what lane the system is about to use or has just used
2. inspect whether the available evidence actually supports that lane
3. reject, reclassify, or confirm the lane
4. emit a contract that explains why

It should answer:

1. was the chosen lane appropriate?
2. if not, what lane or outcome is safer?
3. is this a supported ERP/business request, an uncovered ERP/business request, or a truly unsupported request?

## 6. Contract Model

Mini-phase 7 should introduce `KnowledgeBoundaryContract`.

Suggested fields:

1. `request_id`
2. `session_id`
3. `proposed_lane`
4. `final_lane`
5. `boundary_status`
6. `lane_appropriate`
7. `valid_erp_domain`
8. `grounding_required`
9. `grounding_available`
10. `knowledge_coverage_state`
11. `reclassification_reason`
12. `boundary_flags`
13. `allowed_to_answer`
14. `safe_next_action`
15. `user_response_mode`
16. `confidence`

Recommended normalized values:

### 6.1 `boundary_status`

1. `confirmed`
2. `reclassified`
3. `blocked`

### 6.2 `knowledge_coverage_state`

1. `covered`
2. `covered_but_wrong_lane`
3. `valid_erp_domain_uncovered`
4. `unsupported_non_erp`

### 6.3 `safe_next_action`

1. `allow_current_lane`
2. `route_to_front_door`
3. `route_to_artifact_lane`
4. `route_to_reasoning_lane`
5. `route_to_clarification`
6. `respond_uncovered_erp_domain`
7. `respond_unsupported`

### 6.4 `user_response_mode`

1. `normal_answer`
2. `boundary_explanation`
3. `safe_refusal`
4. `coverage_gap_explanation`

## 7. Inputs The Boundary Layer Should Read

The boundary layer should not work from raw text alone.

It should read structured outputs from earlier phases:

1. `InteractionContract`
2. `ClarificationResolutionContract`
3. `FrontDoorIntentGate` decision payload
4. `ArtifactContinuationContract` when present
5. `GovernedScopeDecisionContract` when present
6. compiled execution audit / family validation / semantic validation
7. `ERPBusinessReasoningActivationContract`
8. `ERPBusinessReasoningContract`
9. `qwen_grounded_turn_context`
10. discovery evidence / supported surface metadata where relevant

This keeps boundary decisions structural and auditable.

## 8. Decision Logic

Boundary evaluation should happen in this order:

1. confirm whether clarification already owns the turn
2. if front door claimed the turn, verify no stronger ERP/business evidence exists
3. if artifact lane claimed the turn, verify it is really a governed retrieval/continuation ask
4. if reasoning lane claimed the turn, verify grounding and knowledge scope really support it
5. if neither artifact nor reasoning can safely answer, classify:
   - valid ERP domain but not yet covered
   - unsupported non-ERP

This means the boundary layer validates claims from other layers instead of trying to outsmart them from raw text.

## 9. Boundary Rules By Lane

### 9.1 Front Door

Confirm front door only when:

1. the front-door contract is valid
2. no stronger grounded artifact or reasoning evidence exists
3. the turn is truly conversational/session-flow/capability oriented

Reclassify away from front door when:

1. grounded artifact continuation exists
2. grounded reasoning follow-up exists
3. fresh governed ERP retrieval is actually available

### 9.2 Artifact Lane

Confirm artifact lane when:

1. fresh governed retrieval is supported
2. artifact continuation is valid
3. clarification is satisfied

Block or reclassify artifact lane when:

1. the ask is actually interpretive/recommendation oriented over an existing grounded source
2. retrieval succeeded but cannot safely answer the actual user ask

### 9.3 Reasoning Lane

Confirm reasoning lane when:

1. grounded source exists
2. reasoning activation is eligible
3. reasoning scope is supported
4. recommendation/speculation boundaries are respected

Block or reclassify reasoning lane when:

1. the user is actually asking for fresh governed retrieval
2. the source is non-advisory and the ask exceeds grounded meaning
3. the ask is valid ERP/business domain but not yet supported by grounded or bounded reasoning

## 10. Valid ERP Domain vs Unsupported

This is the most important Mini-phase 7 distinction.

### 10.1 `valid_erp_domain_uncovered`

Use this when:

1. the request is clearly about business / finance / operations / ERP
2. the question is legitimate
3. current grounded artifact or bounded reasoning support is insufficient
4. the system should not pretend it is unsupported nonsense

Examples:

1. broad ratio education asks
2. business concepts not yet implemented in governed or reasoning form
3. analytical asks needing a not-yet-built lane

The response should be honest:

1. acknowledge the business-valid domain
2. say current support is not yet available
3. optionally steer toward supported governed summaries

### 10.2 `unsupported_non_erp`

Use this when:

1. the request is outside ERP/business scope
2. it is not a reasonable future ERP support candidate

The response should be a clear safe refusal or polite redirect.

## 11. Anti-Patterns To Avoid

Mini-phase 7 must not become:

1. a top-level keyword router
2. a prompt-only “AI decides everything” layer
3. a duplicate of front door
4. a duplicate of reasoning activation
5. a silent fallback that hides coverage gaps

Specific anti-patterns:

1. no regex bags for “business words”
2. no giant phrase libraries for `supported` vs `unsupported`
3. no hidden front-door expansion through boundary responses
4. no implicit artifact reruns when the issue is really unsupported coverage

## 12. Implementation Slices

Mini-phase 7 should be implemented in bounded slices:

### 7A. Boundary Contract Foundation

Build:

1. `KnowledgeBoundaryContract`
2. normalized enums / reason codes
3. deterministic contract builders

Exit:

1. boundary contract can be emitted from fixtures and smokes

### 7B. Lane-Validation Foundation

Build:

1. boundary evaluator over existing contract outputs
2. late-stage validation for:
   - front door
   - artifact lane
   - reasoning lane

Exit:

1. boundary can confirm or reclassify lanes without raw keyword routing

### 7C. Coverage-State Classification

Build:

1. `covered`
2. `covered_but_wrong_lane`
3. `valid_erp_domain_uncovered`
4. `unsupported_non_erp`

Exit:

1. uncovered ERP/business questions no longer fall into generic unsupported behavior

### 7D. User-Facing Boundary Responses

Build:

1. bounded boundary response renderer
2. consistent response modes for:
   - coverage gap
   - unsupported
   - safe redirect

Exit:

1. user gets honest, stable explanations instead of lane confusion

## 13. Deterministic vs AI Authority

Deterministic authority should own:

1. boundary contract schema
2. lane suitability rules
3. coverage-state classification
4. safe next action
5. final answerability decision

AI may help with:

1. proposing nuanced ERP-domain-likeness later if needed
2. rendering uncovered-domain explanations in natural language
3. rendering supported boundary explanations more naturally

But AI must not be:

1. the final authority for `supported` vs `unsupported`
2. the final authority for lane reclassification
3. the final authority for knowledge-boundary safety

## 14. Observability

Mini-phase 7 should emit structured boundary events:

1. `boundary_confirmed`
2. `boundary_reclassified`
3. `boundary_blocked`
4. `coverage_gap_detected`
5. `unsupported_request_detected`

Minimum details:

1. `proposed_lane`
2. `final_lane`
3. `knowledge_coverage_state`
4. `safe_next_action`
5. `reclassification_reason`
6. `event_level`

## 15. Exit Criteria

Mini-phase 7 is complete when:

1. a dedicated `KnowledgeBoundaryContract` exists
2. boundary decisions are late-stage and contract-driven
3. valid ERP-domain-uncovered asks are separated from unsupported asks
4. lane-bouncing is reduced materially
5. artifact / reasoning / front-door boundaries are auditable
6. regression coverage exists for major reclassification cases

## 16. Recommended Immediate Next Step

The first implementation slice should be:

1. `7A Boundary Contract Foundation`

Then:

1. `7B Lane-Validation Foundation`
2. `7C Coverage-State Classification`
3. `7D User-Facing Boundary Responses`

That order keeps Mini-phase 7 contract-led and prevents it from becoming another heuristic router.

## 17. Current Status

Mini-phase 7 is now closed for its intended scope.

Implemented:

1. `KnowledgeBoundaryContract` in `contracts.py`
2. `build_knowledge_boundary_contract(...)`
3. normalized contract fields for:
   - proposed lane
   - final lane
   - boundary status
   - knowledge coverage state
   - safe next action
   - user response mode
4. Phase 7A probe:
   - `run_phase7a_knowledge_boundary_contract_probe()`

Verified:

1. `py_compile`
2. enterprise guardrail audit
3. live backend probe for:
   - confirmed covered lane
   - reclassified valid-ERP-domain-uncovered case

7B lane-validation foundation is now also implemented.

Implemented in 7B:

1. deterministic boundary evaluator in `knowledge_boundary.py`
2. lane-validation over prior contract evidence for:
   - clarification
   - front door
   - artifact lane
   - reasoning lane
3. explicit structural classification for:
   - `covered`
   - `covered_but_wrong_lane`
   - `valid_erp_domain_uncovered`
   - `unsupported_non_erp`
4. Phase 7B probe:
   - `run_phase7b_lane_validation_probe()`

Verified:

1. `py_compile`
2. enterprise guardrail audit
3. live backend probe for:
   - front door reclassified to artifact lane when governed artifact evidence is already stronger
   - confirmed reasoning lane
   - valid-ERP-domain-uncovered reasoning case

7C coverage-state classification is now also integrated into live orchestration.

Implemented in 7C:

1. `qwen_knowledge_boundary_contract` is now emitted in live chat flow for:
   - confirmed front-door handling
   - compiled first-turn governed artifact execution
   - grounded reasoning lane execution
   - clarification-owned branches
   - out-of-scope / unsupported-domain exits
   - artifact-boundary branches such as evidence and enrichment stops
2. compiled first-turn orchestration now passes governed-scope, clarification, and front-door evidence into boundary evaluation
3. follow-up orchestration now emits boundary contracts without changing user-facing response behavior
4. Phase 7C live orchestration smoke:
   - `run_phase7c_live_boundary_orchestration_smoke()`

Verified:

1. `py_compile`
2. enterprise guardrail audit
3. live backend smoke for:
   - confirmed `front_door`
   - confirmed `artifact_lane`
   - confirmed `reasoning_lane`

7D user-facing boundary responses are now also implemented.

Implemented in 7D:

1. bounded boundary response renderer in `knowledge_boundary.py`
2. contract-driven response modes for:
   - `coverage_gap_explanation`
   - `safe_refusal`
   - `boundary_explanation`
3. live service integration for uncovered and unsupported exits, including:
   - governed out-of-scope follow-up exits
   - known unsupported ERP-domain exits
   - grounded evidence boundary exits
   - artifact enrichment boundary exits
   - reasoning guardrail exits
4. stronger legacy detail is preserved as supplemental explanation instead of being discarded
5. Phase 7D probes:
   - `run_phase7d_boundary_response_probe()`
   - `run_phase7d_boundary_response_live_smoke()`

Verified:

1. `py_compile`
2. enterprise guardrail audit
3. renderer probe for:
   - uncovered ERP-domain explanation
   - unsupported request refusal
   - safer-lane redirect explanation
4. live backend smoke for:
   - follow-up uncovered ERP-domain response with `valid_erp_domain_uncovered`
   - `coverage_gap_explanation` user-facing answer
5. manual browser closure pass for:
   - normal front-door handling
   - normal governed artifact answers
   - uncovered ERP-domain answer staying honest and non-random
   - safe blocked recommendation refusal on transactional listing
   - grounded reasoning continuity without boundary confusion

Not implemented yet:

1. no dedicated Mini-phase 7 observability chapter yet
2. no external metrics/dashboard layer for boundary outcomes yet

Honest judgment:

1. 7A through 7D are now in place
2. boundary decisions are now structural both internally and in the uncovered/unsupported user-facing exits
3. Mini-phase 7 now has real runtime value, not just latent contracts
4. Mini-phase 7 is closure-ready and now closed
5. the next correct phase is Mini-phase 8
