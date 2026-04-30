# Qwen ERP Mini-phase 6 ERPBusinessReasoningContract Design (2026-03-26)

## 1. Objective

Mini-phase 6 adds a separate ERP business reasoning lane.

Its job is not to fetch new governed ERP data.

Its job is to:

1. interpret grounded ERP results
2. explain business meaning
3. provide bounded ERP-domain recommendations
4. continue recommendation/explanation detail safely

Mini-phase 6 exists because these turns are neither:

1. front-door conversational turns
2. fresh governed artifact requests
3. clarification-only turns

They are grounded reasoning turns and need their own contract authority.

## 2. Non-Negotiable Rules

Mini-phase 6 must not:

1. become a hidden general chatbot lane
2. become a fallback for unsupported requests
3. fetch arbitrary new data silently
4. use keyword bags or phrase-surface routing authority
5. let AI invent ungrounded recommendations

Mini-phase 6 must:

1. require governed grounding
2. separate activation from reasoning execution
3. separate recommendation from speculation
4. make deterministic sufficiency checks explicit

## 3. Position In The Lane Stack

Recommended precedence:

1. Clarification Resolution Authority
2. FrontDoorIntentGate
3. Governed ERP Artifact Lane
4. ERP Business Reasoning Lane
5. Knowledge Boundary Layer
6. Recovery / Conversational Repair Layer

Meaning:

1. clarification still owns pending state
2. front door remains thin
3. fresh data questions still go through governed artifact execution first
4. reasoning is only eligible after governed grounding exists

## 4. Scope

### 4.1 In Scope

Mini-phase 6 should handle:

1. grounded interpretation
2. grounded explanation
3. grounded ERP-domain recommendation framing
4. grounded recommendation-detail continuation

Representative examples:

1. `evaluate company health based on AR / AP`
2. `what does this balance sheet mean`
3. `why is this high risk`
4. `give me suggestions in details`
5. `explain that recommendation more`
6. `what should management do next`

### 4.2 Out Of Scope

Mini-phase 6 should not handle:

1. fresh data retrieval asks
2. unsupported world knowledge
3. legal or tax advice beyond grounded ERP interpretation
4. dissatisfaction / repair orchestration
5. enrichment recovery after failed artifact continuation
6. knowledge-boundary final arbitration

Those belong to later phases.

## 5. Contract Model

Mini-phase 6 should use two contracts.

### 5.1 ERPBusinessReasoningActivationContract

This is the phase 6A contract.

Its purpose is to answer:

1. is grounded reasoning even eligible here?
2. what source artifact is allowed to ground the reasoning?
3. what reasoning types are permitted for this grounded context?

Suggested fields:

1. `request_id`
2. `session_id`
3. `grounded_context_available`
4. `grounded_source_request_id`
5. `grounded_source_kind`
6. `grounded_source_name`
7. `grounded_family_id`
8. `grounded_artifact_type`
9. `grounded_source_reports`
10. `grounded_capability_id`
11. `grounded_semantic_tags`
12. `grounding_summary`
13. `recommendation_allowed`
14. `recommendation_policy_basis`
15. `allowed_reasoning_types`
16. `activation_state`
17. `route_target`
18. `reason`

Allowed reasoning types should be restricted to:

1. `interpretation`
2. `explanation`
3. `recommendation`
4. `continuation_detail`

This contract is deterministic and safe.

It does not yet decide whether the current user message is definitely one of those reasoning asks.

That semantic activation comes later after the foundation exists.

### 5.2 ERPBusinessReasoningContract

This is the final phase contract for execution/result authority.

Its purpose is to answer:

1. what kind of reasoning was performed?
2. was grounding sufficient?
3. what claims are allowed?
4. what recommendations are permitted?

Suggested fields:

1. `request_id`
2. `session_id`
3. `reasoning_type`
4. `grounding_source_request_id`
5. `grounding_source_kind`
6. `grounding_family_id`
7. `grounding_artifact_type`
8. `grounding_source_reports`
9. `grounding_sufficient`
10. `grounding_gaps`
11. `bounded_domain`
12. `reasoning_scope`
13. `supported_claims`
14. `recommendations`
15. `speculation_flags`
16. `allowed_to_answer`
17. `reason`
18. `confidence`

Mini-phase 6 must not render a recommendation answer if:

1. grounding is insufficient
2. the output depends on external unsupported knowledge
3. the recommendation cannot be tied back to grounded ERP facts or explicit derived calculations

Recommendation objects should be tied back deterministically to supported claims.

A safe contract shape is:

1. `action`
2. `rationale`
3. `basis_claim_refs`

Where `basis_claim_refs` are integer indexes into `supported_claims`.

## 6. Grounding Rules

Grounding sources may include:

1. `qwen_grounded_turn_context`
2. normalized family artifact
3. composite grounded artifact
4. prior governed analytical answer when its source artifacts are still available

Grounding sufficiency should be deterministic and explicit.

A reasoning answer is eligible only when:

1. a grounded source exists
2. the source still matches the active business context
3. the reasoning ask can be answered from the grounded source without hidden new retrieval

Grounding is insufficient when:

1. the user is really asking for new data
2. the user asks for recommendation detail that depends on missing dimensions
3. the prior answer had unsupported or weakly grounded recommendation content

## 7. Reasoning Types

### 7.1 Interpretation

Allowed:

1. summarize business meaning of grounded facts
2. explain what the figures imply operationally

Not allowed:

1. invent new external causes
2. claim certainty beyond the grounded data

### 7.2 Explanation

Allowed:

1. explain why a grounded conclusion was reached
2. unpack the logic behind a prior grounded answer

Not allowed:

1. introduce new unsupported metrics or causes

### 7.3 Recommendation

Allowed:

1. bounded ERP-domain actions tied to grounded facts
2. prioritization suggestions based on grounded risk or concentration

Not allowed:

1. legal advice
2. tax advice
3. credit-policy claims with no grounded support
4. invented management strategy unrelated to grounded ERP evidence

### 7.4 Continuation Detail

Allowed:

1. continue a prior grounded recommendation or explanation answer
2. expand the detail of already grounded guidance

Not allowed:

1. silently pivot into new data retrieval
2. silently replace the source artifact

## 8. Deterministic vs AI Authority

### 8.1 Deterministic Authority

Deterministic logic should be absolute for:

1. whether grounded context exists
2. what grounded source may be used
3. whether reasoning is allowed at all
4. what reasoning types are permitted
5. whether grounding is sufficient
6. whether the answer must route back to governed artifact execution instead

### 8.2 AI Proposal / Rendering

AI may be used for:

1. reasoning activation proposal after deterministic eligibility is established
2. generating the narrative explanation
3. turning bounded recommendations into natural language

AI must not be the authority for:

1. grounding sufficiency
2. lane precedence
3. clarification ownership
4. unsupported recommendation allowance

## 9. Mini-phase 6 Slice Plan

### 9.1 Phase 6A

Reasoning activation foundation.

Deliver:

1. `ERPBusinessReasoningActivationContract`
2. deterministic activation context builder
3. explicit allowed reasoning types from grounded context
4. no production routing takeover yet

This slice should not yet execute reasoning answers.

Its purpose is to make the lane explicit and inspectable.

### 9.2 Phase 6B

Semantic reasoning activation.

Deliver:

1. semantic proposal about whether the current turn is:
   - interpretation
   - explanation
   - recommendation
   - continuation_detail
2. deterministic validation against activation contract

### 9.3 Phase 6C

ERPBusinessReasoningContract execution.

Deliver:

1. final reasoning contract
2. grounded narrative rendering
3. recommendation/speculation boundary enforcement

### 9.4 Phase 6D

Recommendation-detail continuation.

Deliver:

1. stable continuation over previously grounded recommendation or explanation
2. refusal to drift into unsupported fresh claims

### 9.5 Phase 6.1 Carry-Forward

Mini-phase 6.1 should add:

1. CI-grade regression promotion from the callable 5.5 suite
2. observability severity levels
3. explicit regression lock-in for:
   - pending clarification fresh-query override
   - stale-context gratitude/closure leakage

### 9.6 Phase 6.2 Carry-Forward

Mini-phase 6.2 should evaluate:

1. clarification-state concurrency/race risk
2. adversarial clarification-state tests

## 10. Anti-Patterns

Mini-phase 6 must avoid:

1. front door absorbing reasoning turns
2. reasoning lane silently doing fresh data retrieval
3. recommendation text without deterministic grounding sufficiency
4. keyword detection of `analysis`, `explain`, `why`, `suggest`
5. mixing recovery/dissatisfaction into reasoning lane

## 11. Exit Criteria

Mini-phase 6 is complete when:

1. a dedicated reasoning activation contract exists
2. reasoning is only available when grounded context is sufficient
3. interpretation / explanation / recommendation are separated explicitly
4. unsupported speculation is blocked structurally
5. recommendation-detail continuation works without degrading artifact routing
6. the lane has regression coverage and observability

## 12. Current Status

Mini-phase 6A through 6D are implemented, and Phase 6 hardening is now materially in place.

Implemented:

1. `ERPBusinessReasoningActivationContract`
2. `ERPBusinessReasoningContract` contract surface
3. deterministic reasoning activation context builder in `reasoning_activation.py`
4. semantic reasoning activation proposal + governed validation in `semantic_reasoning_activation.py`
5. runtime semantic reasoning activation endpoint
6. reasoning execution foundation in `reasoning_execution.py`
7. runtime ERP business reasoning render endpoint
8. continuation-detail compatibility checks tied to prior grounded reasoning contract
9. backend probes covering:
   - no-grounding -> `not_eligible`
   - grounded artifact context -> `eligible`
   - eligible reasoning activation -> `accepted`
   - grounded reasoning execution -> `answered`
   - grounded reasoning continuation -> `answered`
10. rollout-gated live routing in `service.py`
11. live rollout smoke covering:
   - grounded artifact first turn
   - second-turn reasoning follow-up
   - persisted reasoning audit payloads
12. hardening change:
   - reasoning activation is now skipped when a clarification is pending, preserving clarification precedence structurally
13. Phase 6 observability expansion:
   - structured `qwen_phase6_observability_event`
   - severity levels:
     - `info`
     - `warning`
     - `error`
   - event families:
     - `reasoning_activation`
     - `reasoning_execution`
14. Phase 6 performance metrics:
   - `qwen_phase6_performance_metric`
   - `reasoning_activation_latency`
   - `reasoning_execution_latency`
15. Phase 6 hardening suite now covers:
   - live rollout reasoning path
   - no reasoning without grounding
   - gratitude/front-door boundary after grounded ERP context
   - continuation-detail source mismatch guardrail
   - reasoning observability emission
   - governed recommendation policy boundary for non-advisory grounded sources
16. end-to-end verification now includes:
   - `run_phase6_hardening_suite()`
   - post-restart live rollout smoke on the running backend container
17. final recommendation-boundary hardening now includes:
   - recommendation recognition is separated from recommendation answerability
   - recommendation allowance comes from governed grounded semantics, not merely “any grounded family”
   - non-advisory transactional sources may still recognize recommendation-shaped asks, but deterministic policy stops them from being answered as recommendations
   - interpretation / explanation payloads are deterministically sanitized to remove recommendations
   - recommendation / continuation recommendation objects must carry `basis_claim_refs`
   - non-advisory recommendation asks now stay inside the reasoning lane and exit through a bounded guardrail answer instead of falling back into report behavior
18. final precedence and fulfillment hardening now includes:
   - structural artifact refinements such as top-N / metric / column follow-ups preempt reasoning lane activation and stay in the governed artifact lane
   - accepted continuation-detail answers must deliver substantive grounded content directly rather than returning a teaser or dangling lead-in
   - presentation preferences such as bullet style and MMK Million labeling are now passed into the reasoning renderer as bounded output preferences
19. final source-authority hardening now includes:
   - grounded-turn identity is now treated as the authoritative source for reasoning activation, instead of letting the latest appended artifact payload override the fresh grounded source implicitly
   - composite grounded artifacts now preserve explicit source identity, including request id, source name, source reports, and composite capability identity
   - source-compatible artifact lookup is now structural rather than “last artifact wins”
   - fresh AR/AP reasoning no longer reuses stale ranking context once a newer composite grounded source exists

Not implemented yet:

1. promotion of the callable hardening suite into a CI-grade pytest layer
2. deeper adversarial reasoning-state and runtime failure tests
3. broader reasoning coverage beyond the current grounded interpretation / continuation path
4. concurrency review for multi-request mutation risk in adjacent stateful paths

Current closure judgment:

1. Phase 6 is now ready to close
2. the last identified backend source-contamination defect was fixed structurally
3. targeted backend smokes now pass again for:
   - grounded source reset over AR/AP composite reasoning
   - continuation-detail fulfillment
   - non-advisory recommendation refusal
4. manual browser confirmation now also passed for:
   - AR/AP insight -> management follow-up
   - deeper recommendation-detail continuation
   - safe refusal on transactional operational views
5. remaining carry-forward is operational, not architectural:
   - CI-grade regression promotion
   - deeper adversarial/runtime-failure coverage
