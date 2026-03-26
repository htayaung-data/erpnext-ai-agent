# Qwen ERP Mini-phase 5 FrontDoorIntentGate Design (2026-03-25)

Status: closed after redesign and closure review  
Scope: enterprise approach for Mini-phase 5, plus current status after live testing and redesign execution

## 1. Why Mini-phase 5 Exists

The current runtime still sends too many clearly non-artifact turns into the governed artifact pipeline.

That creates avoidable noise for:

1. acknowledgements
2. thanks
3. low-signal session-flow turns
4. capability questions
5. simple repair turns that are not actual ERP data requests

Mini-phase 5 adds a front-door lane so the system can:

1. answer obvious conversational turns directly
2. route valid ERP-business requests onward
3. avoid forcing the artifact lane to handle everything

## 1.1 Current status after implementation

Implemented so far:

1. `FrontDoorIntentGateContract`
2. AI proposal for front-door classes with deterministic guardrails
3. service integration ahead of the ERP lanes
4. warm AI-rendered replies for validated front-door turns
5. pending-clarification guardrails so short continuation-like turns do not stay in front door

Current judgment:

1. Mini-phase 5 improved greetings, thanks, and simple capability questions
2. live testing exposed real regressions in core ERP clarification flows and gratitude/signoff continuity
3. redesign execution corrected those boundary failures structurally
4. Mini-phase 5 now reaches closure quality for its intended scope

## 2. Enterprise Boundary

`FrontDoorIntentGate` should be:

1. narrow
2. contract-led
3. low-risk
4. conservative

It should **not** become:

1. a hidden chatbot lane
2. a general reasoning engine
3. a substitute for `KnowledgeBoundaryContract`
4. a place to answer broad ERP business questions

Rule:

1. if clearly front-door, answer or handle there
2. otherwise route onward

## 3. Initial Intent Classes

Mini-phase 5 should start with only high-confidence front-door classes:

1. `greeting`
2. `thanks`
3. `acknowledgement`
4. `capability_question`
5. `session_flow`
6. `low_signal_non_business`
7. `route_onward`

### 3.1 What these mean

These are semantic classes, not keyword buckets.

Examples are illustrative only and must not become exhaustive phrase lists.

`low_signal_non_business`

1. very short, non-specific turns that do not ask for ERP data or reasoning

`route_onward`

1. default when the message is a plausible ERP/business request

## 4. Contract Shape

Add:

1. `FrontDoorIntentGateContract`

Recommended fields:

1. `request_id`
2. `intent_class`
3. `confidence`
4. `handle_in_front_door`
5. `response_mode`
6. `response_payload`
7. `route_target`
8. `reason`

Recommended `response_mode` values:

1. `direct_answer`
2. `capability_summary`
3. `continue_current_flow`
4. `route_onward`

Recommended `route_target` values:

1. `front_door`
2. `artifact_lane`
3. `boundary_layer_later`

For Mini-phase 5, `route_target` should normally be:

1. `front_door`
2. `artifact_lane`

The full boundary-layer split can come later.

## 5. Decision Strategy

Mini-phase 5 should use a strict precedence order.

Recommended order:

1. AI proposal selects a front-door intent class from the governed schema
2. deterministic validators protect the ERP/business lanes
3. if the turn is a plausible ERP/business request, do **not** trap it in front door
4. if proposed `session_flow` but grounded context does not exist, route onward
5. if classifier confidence is weak, route onward
6. otherwise honor the validated front-door class

This keeps false positives low.

## 6. What To Reuse

Mini-phase 5 should reuse existing governed assets where appropriate:

1. follow-up ontology classes for simple continuation-like phrases
2. supported capability metadata for capability-summary responses
3. session context signals such as whether a grounded artifact exists

But it should **not**:

1. rely on large phrase bags
2. reuse report-family markers as front-door authority
3. classify broad ERP business questions as front-door just because they are short

## 7. Implementation Slices

### Slice 5.1 Contract and translator

Deliver:

1. `FrontDoorIntentGateContract`
2. deterministic translator for direct-answer payloads
3. no service integration yet

### Slice 5.2 Conservative classifier

Deliver:

1. semantic front-door proposal endpoint in runtime
2. AI classifier proposal constrained to governed front-door classes
3. deterministic validators that can still force `route_onward`
4. default to `route_onward` when uncertain or below confidence threshold

### Slice 5.3 Service integration

Deliver:

1. service entry check before the governed artifact lane
2. front-door audit payload
3. simple direct responses for greetings/thanks/capability questions/session flow

### Slice 5.4 Smoke coverage

Add browser/manual and scripted cases for:

1. `hi`
2. `thank you`
3. `okay continue`
4. `what can you do`
5. `show me sales trend`
6. `analyze company health`

Expected:

1. first four handled in front door
2. last two routed onward

## 8. Non-goals For Mini-phase 5

Mini-phase 5 should **not** implement:

1. ERP business reasoning answers
2. enrichment recovery
3. conversational repair after failed enrichment
4. broad ambiguity handling for ERP-domain questions
5. full unsupported-domain boundary decisions

Those belong to later chapters.

## 8.1 Lessons From Live Testing

Live testing showed that the front-door lane is not the only issue.

What worked:

1. greetings and thanks became warmer and less robotic
2. basic capability questions behaved better
3. obvious non-ERP turns could stay out of the artifact lane

What regressed:

1. ERP clarification turns and front-door behavior became too entangled
2. pending clarification replies such as report selections were not reliably binding back to the original ERP intent
3. some dissatisfaction or repair turns were still leaking into the wrong lane
4. some ERP requests that previously behaved better became less reliable once front-door and clarification state started interacting

Most important lesson:

1. front-door should stay thin
2. clarification resolution must be treated as its own structural authority
3. selecting a pending option must bind to the pending ERP clarification, not behave like a fresh standalone message

## 9. Success Criteria

Mini-phase 5 is successful if:

1. clearly conversational turns no longer go through the artifact lane
2. capability questions get clean direct answers
3. simple session-flow turns behave more naturally
4. plausible ERP/business requests still route onward safely
5. no new keyword-bag architecture is introduced
6. conversational intent classification does not depend on enumerating common phrases

Current status against these criteria:

1. partially met for simple conversational turns
2. not yet met for ERP clarification continuity
3. not yet met for overall production-readiness

## 10. Recommended Next Implementation Order

1. add `FrontDoorIntentGateContract`
2. implement semantic proposal plus deterministic validators
3. wire it into service before artifact-lane routing
4. add smoke cases and manual browser pack
5. only after that consider expanding the front-door coverage

## 11. Current Decision

Do not continue expanding Mini-phase 5 right now.

Instead:

1. pause Mini-phase 5 expansion
2. review whether front-door should be bypassed whenever:
   - a governed clarification is pending
   - or a turn is plausibly ERP/business-like
3. redesign clarification response resolution as a proper slot-binding mechanism
4. keep front-door focused on thin conversational handling only
5. seek architecture review before resuming Mini-phase 5 implementation

## 12. Redesign Direction After Architecture Review

The external architecture review confirmed the core problem:

1. the missing authority is not more front-door logic
2. the missing authority is a dedicated clarification resolution layer
3. front-door should not participate in pending clarification handling

Additional business rule confirmed during review:

1. if business intent is already clear, the assistant should not expose internal report-selection ambiguity to the user
2. for example, `payable` and `receivable` are normally clear business intents
3. the system should choose the governed default AP/AR report internally unless a genuinely user-visible distinction must be clarified

## 13. Practical Mini-phase 5 Redesign Plan

This is the implementation plan we should now follow.

### 13.1 Phase 5A: Clarification Resolution Authority

Add a new highest-precedence layer before front door.

Responsibilities:

1. detect whether a clarification is pending
2. bind user replies to pending clarification options deterministically
3. distinguish:
   - valid option selection
   - clear new ERP request
   - unresolved meta/dissatisfaction/empty acknowledgement
4. emit a dedicated `ClarificationResolutionContract`
5. route the resolved slot into the ERP lane

Required outcome:

1. a reply like `Accounts Receivable` must bind to the pending report-selection slot
2. it must not be treated as a fresh unrelated turn

Current redesign status:

1. `ClarificationResolutionContract` is implemented
2. dedicated clarification resolution now runs before front door
3. resolved clarification slots are already consumed by the ERP fresh-query path
4. pending clarification state is now stored explicitly on `Qwen Chat Session.pending_clarification_state_json`
5. live probe confirmed:
   - clarification state is written when a clarification is emitted
   - the stored state is cleared after the user selects an option and the ERP lane executes successfully
6. front door no longer owns pending clarification through a guardrail parameter or branch
7. clarification precedence is now enforced only in service orchestration

### 13.2 Phase 5B: Front-Door Scope Reduction

Keep front door, but make it thinner.

Rules:

1. if clarification is pending, front door is skipped entirely
2. front door handles only clearly non-ERP conversational turns
3. front door may still use:
   - AI proposal
   - deterministic guardrails
   - warm AI rendering
4. front door must not own ERP clarification continuity

### 13.3 Phase 5C: ERP Lane Slot Consumption

The ERP lane must consume resolved clarification slots explicitly.

Responsibilities:

1. compiler/interpreter accepts resolved slot data from clarification resolution
2. resolved report/capability/time-scope choices are applied structurally
3. resolved clarification must clear pending state once consumed

Required outcome:

1. pending clarification selection becomes binding
2. clarification loops stop

### 13.4 Phase 5D: Internal Default Report Selection

Do not clarify low-level internal report ambiguity when user intent is already clear.

Rule:

1. clarify only when user intent is ambiguous
2. do not clarify when only internal report choice is ambiguous but the business ask is already clear

Examples:

1. `show me payable amount` should route to governed AP using the default governed report internally
2. `show me receivable amount` should route to governed AR using the default governed report internally
3. clarification is justified only if the missing choice materially changes user-visible meaning

### 13.5 Phase 5E: Deferred Improvements

These should not block the redesign start:

1. clarification attempt counting
2. richer dissatisfaction handling
3. explicit repair lane
4. broader conversational guidance

Those can come after the core clarification authority is stable.

### 13.6 Phase 5D.1: Minimal Repair Handling

Implemented as a bounded clarification-resolution improvement.

What it now handles:

1. `empty_ack`
   - very short non-business acknowledgements while clarification is pending
   - example outcome: re-ask with the concrete options instead of treating the turn as ERP data
2. `meta_question`
   - clarification-about-the-clarification turns
   - example outcome: explain that the system is still waiting for a choice and restate the available options
3. `new_request`
   - substantive ERP/business turns still clear pending clarification and route through the ERP lane

What it intentionally does not try to solve yet:

1. rich dissatisfaction handling
2. multi-turn clarification coaching
3. attempt escalation / fallback policy

Live redesign check:

1. pending `report_ambiguity` + `yes` -> `empty_ack`
2. pending `report_ambiguity` + `what do you mean?` -> `meta_question`
3. pending `report_ambiguity` + `show me sales trend` -> `new_request` and fresh ERP execution

Known residual niche gap:

1. some conversational closing/sign-off turns can still misroute if they contain temporal follow-up wording such as `as of now`
2. this is not a clarification-binding defect
3. it is a broader intent-boundary issue between:
   - real time-scope follow-up
   - and non-business conversational closure containing time language
4. this should be deferred unless we choose to do one more Mini-phase 5 intent-boundary slice

## 16. Explicit Boundary Note: Recommendation-Detail Follow-ups

Observed example:

1. user asks for `AR / AP insight`
2. assistant returns a grounded working-capital analysis with recommendations
3. user asks `give me suggestions in details`
4. system drops into a raw AP aging artifact instead of continuing the recommendation thread

Judgment:

1. this is **not** a core Mini-phase 5 front-door problem
2. this is **not** a pending clarification binding problem
3. this is mainly a missing reasoning-continuation / recovery capability

Why it is deferred:

1. Mini-phase 5 is responsible for:
   - front-door routing
   - clarification authority
   - preventing conversational turns from degrading ERP routing
2. this failure happens after a valid ERP analysis has already been produced
3. the missing behavior is the ability to continue recommendation/explanation detail coherently from an analytical answer

So this should be handled later by:

1. `ERPBusinessReasoningContract`
2. and, if needed, the later conversational recovery chapter

Rule for Mini-phase 5:

1. do not stretch front-door or clarification logic to solve recommendation-detail follow-up continuity
2. keep Mini-phase 5 focused on routing and clarification correctness

## 14. Immediate Next Implementation Order

1. keep clarification precedence as the only authority when pending state exists
2. reduce user-facing AP/AR report clarification where business intent is already clear
3. rerun browser regression on:
   - AR/AP selection
   - pending clarification replies
   - front-door greetings / thanks / capability questions

Completed in the redesign already:

1. `ClarificationResolutionContract`
2. clarification-resolution module before front door
3. resolved-slot ERP lane consumption
4. explicit persisted pending clarification state
5. front-door cleanup removing pending clarification ownership
6. `closure_signoff` is added as an explicit front-door intent class for polite session-ending turns
7. alias-based business-signal authority is removed from front door and clarification resolution
8. front door now uses AI proposal plus governed validation, with semantic fresh-query cross-check instead of lexical business-signal veto
9. clarification `new_request` detection now uses semantic fresh-query cross-check instead of ontology alias matching
10. semantic fresh-query cross-check for front door and clarification is evaluated on the current turn only, to avoid gratitude/signoff turns inheriting prior grounded ERP context

## 15. Updated Success Criteria

Mini-phase 5 should only be considered successful after all of the following are true:

1. front door remains thin and does not degrade ERP behavior
2. pending clarification replies bind correctly to the intended ERP slot
3. AP/AR-style clear business asks do not trigger unnecessary internal report clarification
4. greetings / thanks / capability questions still feel warm and natural
5. polite closure turns like `I am okay for now, I will come back later` stay in front door instead of leaking into ERP lanes
6. no keyword-bag, phrase-surface routing authority, ontology-alias routing authority, or single-case architecture is introduced

## 16. Closure Decision

Mini-phase 5 is closed.

Reason:

1. front door is now thin and stable for its intended scope
2. clarification continuity no longer depends on front-door/session-flow handling
3. AP/AR clear intent no longer exposes unnecessary internal report ambiguity
4. gratitude and polite closure turns no longer inherit stale ERP context
5. remaining deeper reasoning/recovery gaps belong to later phases, not Mini-phase 5
