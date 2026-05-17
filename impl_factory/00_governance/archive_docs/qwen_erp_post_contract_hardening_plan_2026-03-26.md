# Qwen ERP Post-Contract Hardening Plan (2026-03-26)

## 1. Objective

Post-contract hardening is the immediate phase after Mini-phase 8 closure.

Its purpose is to make the now-closed stack operationally trustworthy before any new governed coverage expansion begins.

Current closed stack:

1. clarification authority
2. front door
3. ERP business reasoning
4. knowledge boundary
5. recovery / conversational repair

This phase is not for adding new business domains.
It is for making the existing stack safer, more testable, more observable, and more rollout-ready.

Related governance note:

1. `qwen_erp_post_contract_hardening_lessons_2026-03-26.md`
   - captures the practical hardening lessons and judgment heuristics learned during H1-H4 work

## 1.1 Current H1 Progress

Hardening A / H1 has started with two regression layers:

1. end-to-end site regression module
   - `ai_assistant_ui.tests.test_post_contract_regression`
   - covers live Phase 5.5, 6, 7, and 8 hardening suites under the real site runner
2. fast contract / guard probe module
   - `ai_assistant_ui.tests.test_post_contract_guard_probes`
   - covers deterministic guardrails that are stable enough for cheap CI validation:
     - Phase 6 continuation source mismatch guardrail
     - Phase 7A boundary contract integrity
     - Phase 7D boundary response behavior
     - Phase 8A recovery / repair contract integrity
     - semantic repair acceptance safety:
       - substantive enrichment follow-up must not be misread as explicit recovery acceptance
       - explicit confirmation remains allowed
     - stale recovery is invalidated after an accepted repair action
     - a newer recovery contract can still supersede an older consumed one
     - malformed tool payloads do not break recovery contract lookup
     - partial recovery metadata still renders a bounded recovery-guidance answer
     - partial boundary payload tolerance:
       - bounded user-facing response still renders safely from incomplete stored boundary metadata

Important implementation judgment:

1. only deterministic, repeatable guarantees should be promoted into CI gates
2. unstable browser-only edge paths should not be mislabeled as CI-safe regression truths

## 1.2 H1 Status Judgment

Current judgment:

1. H1 is materially complete and closure-ready
2. the regression layer is now credible enough to act as a real release gate foundation, not just a bundle of callable smokes
3. the remaining hardening priority should move to H2 observability and production metrics, not infinite H1 expansion

Evidence already in place:

1. end-to-end site regression module passes:
   - `ai_assistant_ui.tests.test_post_contract_regression`
2. fast contract / guard probe module passes:
   - `ai_assistant_ui.tests.test_post_contract_guard_probes`
3. the locked regression surface now covers:
   - closed-stack live suites for Phase 5.5, 6, 7, and 8
   - reasoning continuation guardrails
   - boundary contract / response integrity
   - recovery / repair contract integrity
   - semantic repair acceptance safety
   - stale recovery invalidation and recovery supersession
   - malformed payload and partial metadata tolerance

Next active step:

1. begin H2 observability and production metrics hardening

## 1.3 Current H2 Progress

Hardening B / H2 has now started with a dedicated fast observability validation layer:

1. `ai_assistant_ui.tests.test_post_contract_observability`
2. current locked checks include:
   - Phase 5.5 observability event payload shape
   - Phase 6 observability severity normalization
   - preservation of valid warning severity
   - performance metric numeric payload normalization
   - unsupported non-ERP knowledge-boundary warning event shape
3. live lane observability coverage now also exists:
   - `ai_assistant_ui.tests.test_post_contract_observability_live`
   - locked live checks include:
     - Phase 5.5 front-door + clarification observability emission
     - Phase 6 reasoning-lane observability emission
     - Phase 7 uncovered-boundary observability emission
     - Phase 8 recovery-guidance observability emission
     - Phase 8 grounded-evidence boundary observability emission
     - Phase 8 artifact-enrichment boundary observability emission
     - correlation consistency for `session_id` and non-empty `request_id`
     - latency metric presence for:
       - reasoning activation
       - reasoning execution
       - knowledge boundary
       - recovery guidance
       - grounded evidence boundary
       - artifact enrichment boundary

Current H2 judgment:

1. H2 is beyond foundation and now has real live-lane validation
2. H2 is materially strong for the currently intended observability surface
3. H2 now covers the most important stable closed-stack lanes, including boundary exits
4. H2 should be treated as pause-ready unless a concrete production observability gap is discovered
5. remaining work belongs more naturally to release-gate maturity than to indefinite H2 expansion:
   - manual/live sanity review of observability usefulness
   - broader metric consumption or dashboarding later if operationally needed

## 1.4 Current H3 Progress

Hardening C / H3 has now started with a dedicated fast state-integrity module:

1. `ai_assistant_ui.tests.test_post_contract_state_integrity`
2. persisted-session live state coverage now also exists:
   - `ai_assistant_ui.tests.test_post_contract_state_live`
3. current locked checks include:
   - repeated pending-clarification storage preserves the latest signal deterministically
   - repeated unresolved clarification attempts increment only the attempt counter while preserving the same pending signal
   - clearing pending clarification removes stored state cleanly
   - malformed clarification-state storage fails closed to an empty state
   - duplicate accepted recovery actions keep the prior recovery contract consumed
   - accepted non-recovery repair contracts do not consume an active recovery contract
   - unresolved repair interpretations do not consume an active recovery contract
   - later non-grounded tool payloads do not displace the latest grounded turn authority
   - later malformed or non-authoritative grounded-turn payloads do not displace the latest valid grounded authority
   - later malformed or non-authoritative grounded-turn payloads do not invalidate a still-valid latest recovery contract
   - reasoning compatibility keeps the latest grounded request id as the authoritative match key
   - reasoning compatibility rejects mismatched grounded family ids when request-id matching is absent
   - reasoning compatibility also rejects mismatched grounded source-report sets when request-id matching is absent
   - composite grounded authority prefers the matching composite artifact over later incompatible normalized artifacts
   - grounded entity-detail authority prefers the matching entity-detail artifact over later incompatible family artifacts
   - duplicate accepted recovery turns do not re-execute stale recovery in a live session, even if the second turn is handled as benign current-flow continuation
   - post-stop clarification repeats do not resurrect stale pending clarification in a live session
   - pending clarification preempts recovery guidance in a mixed-state session
   - explicit clarification resolution clears the mixed-state session cleanly, so later generic guidance does not resurrect stale recovery
   - explicit fresh-query override replaces stale grounded context before a later reasoning follow-up
   - explicit fresh grounded override invalidates prior recovery authority, so a later confirmation turn cannot resurrect stale recovery execution
   - pending clarification can be overridden by an explicit fresh grounded query, and the replacement grounded context becomes the new reasoning authority
   - back-to-back fresh grounded queries in the same session resolve in last-query-wins order before a later reasoning follow-up
   - when multiple recoveries are present in the same session state, only the newest valid recovery remains executable authority
   - an older consumed recovery cannot shadow or block a newer active recovery in the same persisted session
   - once a newer recovery has executed, a repeated acceptance turn does not create extra recovery consumption or re-execute stale recovery state
   - repeated identical fresh grounded queries still replace the prior grounded trace identity before a later reasoning follow-up
   - repeated identical composite grounded queries still replace the prior grounded trace identity before a later reasoning follow-up

Current H3 judgment:

1. H3 is materially strong and closure-ready for the currently intended contract surface
2. the current H3 surface covers the two most important closed-stack state machines:
   - pending clarification
   - recovery consumption
3. H3 now locks grounded-authority replacement, recovery-consumption order, malformed grounded-payload tolerance, and last-query-wins overlap cases across both fast and live layers
4. the remaining H3 risk area has moved outward into narrower timing-heavy and routing-heavy cases:
   - broader duplicate rapid submissions from the same session before persistence settles
   - same-session overlaps beyond the current clarified/recovery/fresh-query set where semantic routing, not just state order, becomes the dominant variable
5. those remaining cases should not be forced into the locked H3 surface unless they are first established as deterministic product contracts
6. current recommendation:
   - pause H3 after this review unless a concrete persisted-session risk is discovered
   - move the next hardening emphasis toward H4 release-gate / adversarial closure work

## 1.5 Current H4 Progress

Hardening D / H4 has now started with a dedicated live adversarial module:

1. `ai_assistant_ui.tests.test_post_contract_adversarial`
2. current locked checks include:
   - adversarial operational-evidence inference pressure remains bounded:
     - either `grounded_evidence_boundary`
     - or a grounded reasoning answer that explicitly refuses unsupported inference
   - mixed-metric requests over single-metric ranking artifacts stay bounded instead of silently collapsing into a misleading fresh query
   - long multi-sentence follow-ups that request incompatible metric mixing remain bounded and do not auto-accept governed recovery
   - creative non-ERP follow-ups after grounded reasoning are refused as unsupported instead of being answered through the reasoning lane
   - prediction / guarantee-style follow-ups after grounded reasoning degrade into a bounded reasoning guardrail response instead of producing unsupported forward-looking promises
3. the first H4 implementation also fixed a real product gap:
   - projection-like follow-ups such as `show together revenue and qty` and `add qty next to each row` are now interpreted as bounded column/enrichment pressure instead of drifting into self-contained fresh-query execution
4. the next H4 slice also fixed a second real product gap:
   - creative asks such as `write a short poem about this` no longer piggyback on grounded ERP reasoning merely because prior governed context exists
   - deterministic context isolation now blocks those turns as outside governed ERP assistant scope

Current H4 judgment:

1. H4 is meaningfully started
2. the current H4 surface now locks five high-value adversarial behaviors with live verification
   - including one deterministic reasoning-guardrail case around unsupported payment guarantees
3. a broader non-regression sweep is now also green across surrounding hardening layers:
   - fast guard probes
   - fast state integrity
   - fast observability
   - live observability
   - live state/session behavior
   - full post-contract regression suite
4. H4 is now materially strong enough for a closure review rather than blind further expansion
5. remaining candidates should focus on:
   - low-confidence semantic degradation staying bounded
   - malformed/partial runtime payload behavior not already covered by H1/H3 fast layers
   - unsupported or policy-disallowed asks after grounded reasoning that are less obviously creative than the current locked case

## 1.6 H4 Closure Review

Closure review judgment:

1. H4 is now closure-ready for the currently intended adversarial hardening surface
2. closure readiness is based on both direct H4 validation and surrounding non-regression evidence:
   - `ai_assistant_ui.tests.test_post_contract_adversarial`
   - `ai_assistant_ui.tests.test_post_contract_guard_probes`
   - `ai_assistant_ui.tests.test_post_contract_state_integrity`
   - `ai_assistant_ui.tests.test_post_contract_state_live`
   - `ai_assistant_ui.tests.test_post_contract_observability`
   - `ai_assistant_ui.tests.test_post_contract_observability_live`
   - `ai_assistant_ui.tests.test_post_contract_regression`
3. the current locked H4 surface now proves five enterprise-important safe-failure behaviors:
   - unsupported operational inference does not fabricate missing evidence
   - single-metric ranking artifacts do not silently absorb mixed-metric projection pressure
   - long incompatible follow-ups remain bounded and do not auto-accept recovery
   - creative non-ERP asks do not piggyback on grounded ERP context
   - recommendation / guarantee pressure degrades into a deterministic reasoning guardrail instead of unsupported promise generation
4. H4 also produced two real product corrections during hardening:
   - projection-like follow-ups are now classified as bounded enrichment pressure instead of fresh-query drift
   - explicit unsupported creative asks now override stale grounded context in deterministic scope isolation and boundary classification

What H4 closure does not mean:

1. it does not mean every imaginable adversarial prompt is now locked forever
2. it does not mean rollout / release gates are complete
3. it does not mean manual live sanity closure has been fully replaced by automated coverage

Recommended next step after H4 closure review:

1. move to `H5 rollout and release gates`
2. keep H4 closed unless a concrete new adversarial failure is discovered

## 1.7 Current H5 Progress

H5 has now started as the post-hardening release / closure-gate step.

It is intentionally small and executable, not just a checklist:

1. a dedicated H5 release-gate module now exists:
   - `ai_assistant_ui.tests.test_post_contract_release_gates`
2. the first H5 rollout probe locks rollout-visibility integrity for:
   - compiled first-turn rollout status
   - ERP business reasoning rollout status
3. the first H5 live sanity pack locks a compact release-gate surface across the closed stack:
   - Phase 5.5 front-door boundary
   - Phase 6 reasoning live rollout
   - Phase 7D boundary response behavior
   - Phase 8 recovery execution
   - H4 recommendation / guarantee safe-failure guardrail

Current H5 judgment:

1. H5 is meaningfully started and now has a verified executable spine
2. the dedicated H5 release-gate module is green:
   - `ai_assistant_ui.tests.test_post_contract_release_gates`
3. supporting fast non-regression verification remains green:
   - `ai_assistant_ui.tests.test_post_contract_guard_probes`
   - Qwen enterprise guardrail audit
4. H5 is correctly shaped as a release-gate layer, not as another vague hardening expansion
5. the next H5 step after this verification is closure judgment:
   - decide whether any additional manual live sanity remains required
   - record whether Wave 1 expansion can begin safely

## 1.8 H5 Closure Review

Closure review judgment:

1. H5 is now materially strong and closure-ready for the automated release-gate surface
2. that judgment is based on green executable evidence, not only on prose intent:
   - `ai_assistant_ui.tests.test_post_contract_release_gates`
   - `ai_assistant_ui.tests.test_post_contract_guard_probes`
   - Qwen enterprise guardrail audit
3. the current H5 executable spine now proves:
   - rollout-control visibility is structurally intact for compiled first-turn and ERP business reasoning
   - a compact live sanity pack still passes across front door, reasoning, boundary response, recovery execution, and an H4 bounded-failure guardrail
4. H5 is now strong enough that Wave 1 planning does not need to wait on more blind automation growth
5. what still remains outside this automated closure judgment is narrow and explicit:
   - optional final manual browser sanity / operator signoff if the team wants human-path confirmation before Wave 1

What H5 closure review does not mean:

1. it does not mean every future rollout or operational regression is impossible
2. it does not mean post-contract hardening should keep expanding indefinitely before any governed coverage growth
3. it does not mean manual signoff has no value, only that automation is now strong enough to carry the primary release-gate burden

Recommended next step after H5 closure review:

1. perform a brief manual live sanity pass if desired for release discipline
2. then treat post-contract hardening as complete enough to begin controlled Wave 1 governed expansion

## 1.9 Stage Model Clarification

For clarity, post-contract hardening has four actual hardening stages:

1. H1 regression / CI hardening
2. H2 observability / metrics hardening
3. H3 state / concurrency hardening
4. H4 adversarial / failure-mode hardening

`H5` is not a fifth hardening stage in the same sense.

It is the post-hardening closure step:

1. rollout / release gates
2. live sanity confirmation
3. readiness judgment before Wave 1 governed coverage expansion

## 2. Non-Negotiable Rules

Post-contract hardening must not:

1. reopen closed architectural chapters casually
2. sneak new product-surface expansion into a hardening phase
3. solve failures with keyword patches or special-case routing
4. replace contract authority with prompt-only optimism
5. defer known reliability risks just because the main flows already work

Post-contract hardening must:

1. strengthen confidence in the closed stack as it actually runs
2. turn callable smokes into stronger regression discipline
3. increase operational visibility into failures and drift
4. tighten state safety and concurrency assumptions
5. create release gates before Wave 1 expansion

## 3. Scope

In scope:

1. regression and CI hardening
2. observability and production metrics
3. state integrity and concurrency review
4. rollout / release-gate hardening
5. adversarial and failure-mode coverage

Out of scope:

1. new governed business domains
2. composite artifacts
3. business formula registry
4. complex request decomposition
5. OCR / CRUD / multilingual expansion

## 4. Hardening Workstreams

### 4.1 H1 Regression And CI Hardening

Goal:

1. promote the current callable smokes into a more formal, repeatable regression layer

Required outcomes:

1. preserve core closed-stack flows across:
   - clarification
   - front door
   - artifact lane
   - reasoning lane
   - knowledge boundary
   - recovery / repair
2. make previously-fixed bugs explicit locked regressions
3. create a minimum CI gate before Wave 1 expansion

Priority test themes:

1. clarification attempt boundaries
2. pending clarification override by valid fresh query
3. gratitude / closure after grounded ERP answers
4. reasoning activation only with valid grounding
5. reasoning continuation-detail source compatibility
6. unsupported operational evidence boundaries
7. recovery guidance vs accepted recovery execution
8. fresh-query override over stale recovery context

Recommended next step:

1. split today’s `run_phase*` smokes into pytest-grade suites while keeping the callable probes as lightweight runtime checks

### 4.2 H2 Observability And Production Metrics

Goal:

1. make failures, drift, and degraded behaviors visible in production without relying on transcript review

Required outcomes:

1. normalize severity levels consistently across active contracts:
   - `info`
   - `warning`
   - `error`
2. keep correlation across multi-turn flows
3. capture latency on the most important semantic/runtime boundaries

Minimum metrics to add or standardize:

1. clarification loop / fallback rates
2. reasoning activation acceptance / rejection
3. boundary uncovered / unsupported rates
4. recovery guidance rate
5. accepted recovery execution rate
6. fresh-query override rate
7. runtime latency by lane
8. compiler / runtime failure counts

Not required yet:

1. full dashboard program
2. external monitoring platform migration
3. pager/alert escalation

### 4.3 H3 State Integrity And Concurrency Hardening

Goal:

1. verify that session and state mutation remain safe under realistic concurrent or repeated user actions

Priority areas:

1. clarification state mutation
2. pending signal persistence / clearing
3. accepted recovery persistence
4. grounded-turn replacement and stale-context reads
5. duplicate rapid submissions from the same session

Required outcomes:

1. identify race-prone state transitions
2. document which transitions are assumed single-writer and which need stronger protection
3. add at least targeted regression coverage for duplicate / repeated-turn behaviors

### 4.4 H4 Adversarial And Failure-Mode Coverage

Goal:

1. prove that the closed stack fails safely under malformed, noisy, or unsupported inputs

Priority adversarial cases:

1. malformed or partial stored payloads
2. unsupported business asks after grounded ERP context
3. ambiguous follow-up that should remain bounded
4. mixed metric requests on single-metric ranking artifacts
5. long multi-sentence follow-ups that still must respect current boundaries
6. runtime degradation / semantic-interpreter low-confidence fallback cases

Required outcomes:

1. failure remains bounded
2. stale context does not leak
3. unsupported asks do not fabricate governed facts

### 4.5 H5 Rollout And Release Gates

Goal:

1. define what must be true before Wave 1 expansion begins

Required gates:

1. closed-stack regression suite passes
2. no known acceptance / persistence regressions remain open
3. observability is good enough to spot lane drift
4. executable release-gate sanity pack passes on live stack
5. no unresolved high-severity concurrency/state issue remains

Current implemented H5 gate surface:

1. rollout visibility probe:
   - compiled first-turn rollout status integrity
   - ERP business reasoning rollout status integrity
2. executable sanity pack:
   - Phase 5.5 front-door boundary smoke
   - Phase 6 reasoning live rollout smoke
   - Phase 7D boundary response smoke
   - Phase 8 recovery execution smoke
   - H4 recommendation / guarantee bounded-response smoke
3. manual browser sanity still remains useful, but it is now downstream of an executable H5 gate instead of being the only release check

## 5. Suggested Execution Order

Recommended order:

1. H1 regression and CI hardening
2. H2 observability and production metrics
3. H3 state integrity and concurrency hardening
4. H4 adversarial and failure-mode coverage
5. H5 rollout and release gates

Reason:

1. stronger regression coverage pays for every later hardening slice
2. observability is needed before rollout confidence means much
3. state and adversarial work should be informed by both tests and metrics

## 6. Closure Criteria

Post-contract hardening is complete when:

1. the closed stack has formal regression coverage beyond ad hoc smokes
2. key operational metrics exist for closed-stack lanes
3. race / persistence risks have been reviewed and the meaningful ones addressed or explicitly bounded
4. manual closure sanity flows pass on the live stack
5. the team can begin Wave 1 expansion without treating current reliability debt as “somebody later’s problem”

## 7. Honest Boundary

This phase should make the system more reliable, not more ambitious.

If a proposed change:

1. adds new business coverage
2. adds new composite data surfaces
3. adds new semantic business definitions
4. adds OCR / CRUD / multilingual scope

then it belongs after this hardening phase, not inside it.
