# Qwen ERP Post-Contract Hardening Lessons (2026-03-26)

## 1. Purpose

This note captures the practical hardening lessons learned while stabilizing the post-contract Qwen ERP stack after Mini-phases 6, 7, and 8.

It is not a roadmap.
It is a reusable operating guide for:

1. later hardening work
2. refactor-safe validation
3. Wave 1 and later expansion hardening
4. future teams working on the same stack

The goal is to preserve the engineering judgment we earned during this phase, not just the tests we wrote.

## 2. The Most Important Lesson

Hardening is not just “add more tests.”

Real hardening means:

1. deciding what behavior is truly guaranteed
2. refusing to promote unstable behavior into CI just because it looks desirable
3. distinguishing product bugs from bad smoke assertions
4. locking only deterministic truths
5. keeping docs honest when a path is exploratory, not yet guaranteed

This discipline mattered more than any single test.

## 3. What Worked Best

### 3.1 Two-Layer Regression Was The Right Shape

The strongest pattern was:

1. fast deterministic guard tests
2. real persisted-session / live site tests

Why this worked:

1. fast tests locked contract integrity cheaply
2. live tests caught real orchestration, persistence, and runtime behavior
3. each layer covered a different failure mode

Rule:

1. do not rely only on fast tests for stateful session behavior
2. do not rely only on live tests for cheap regression confidence

Both are needed.

### 3.2 Sequential Verification Was More Trustworthy Than Parallel Bench Smokes

We hit MySQL deadlocks and ambiguous failures when some bench-style smokes overlapped.

Lesson:

1. parallelization is good for code reading and some shell inspection
2. but stateful live verification should often run sequentially
3. especially when the same site/session/persistence surface is involved

Rule:

1. for persisted-session hardening, prefer sequential validation over optimistic concurrency

### 3.3 Contract-Based Assertions Beat Surface-Text Assertions

A repeated lesson was that some failures were caused by the test checking the wrong field, not by runtime misbehavior.

Example pattern:

1. runtime answered correctly
2. smoke failed because it checked a stale or non-canonical field

What worked better:

1. validate against the authoritative contract fields
2. use compatibility helpers already trusted elsewhere
3. use answer text only as a secondary anchor, not the main source of truth

Rule:

1. when contract authority exists, test against that authority first

### 3.4 Phase-By-Phase Lessons Matter

One useful hindsight lesson is that the four hardening stages did not all teach the same thing.

They produced different kinds of reusable judgment:

1. H1 taught regression discipline
2. H2 taught observability discipline
3. H3 taught state-authority discipline
4. H4 taught adversarial safe-failure discipline

So later teams should not treat “hardening” as one undifferentiated activity.
The phase matters.

## 4. What We Should Not Do

### 4.1 Do Not Promote Aspirational Behavior Into CI

A recurring risk was writing a test for behavior we wanted, but had not actually established as a deterministic contract.

That caused two kinds of bad outcomes:

1. false failures
2. pressure to patch behavior prematurely just to make the test green

Rule:

1. CI should lock guaranteed behavior
2. exploratory desired behavior should stay out of the locked suite until the product contract is real

### 4.2 Do Not Hide Architecture Gaps With Keyword Patches

We intentionally avoided:

1. keyword hacks
2. hardcoded single-turn fixes
3. local phrase bags pretending to be architecture

This mattered during hardening too, not just feature work.

Why:

1. hardening should strengthen the real authority model
2. not produce green tests by shrinking the problem into narrow string matching

### 4.3 Do Not Mix Big Refactors Into Hardening

We discussed oversized files like `service.py`.

Lesson:

1. refactor is good
2. but hardening and refactor should not be heavily mixed

Why:

1. when behavior changes and code movement happen together, failures become harder to interpret
2. hardening needs clear signal about whether the system is wrong or the code was merely rearranged

Rule:

1. finish stabilization first
2. refactor in controlled slices later
3. rerun hardening after each refactor slice

## 5. Reliable Hardening Heuristics

### 5.1 Lock The Stable Path, Not The Clever Path

If a behavior is:

1. high-value
2. deterministic
3. already explained by current contracts

then lock it.

If a behavior is:

1. desirable but not fully defined
2. dependent on semantic interpretation drift
3. not yet clearly guaranteed by authority contracts

then do not lock it yet.

### 5.2 When A New Test Fails, First Ask “Test Bug Or Product Bug?”

This question saved time repeatedly.

The right order is:

1. inspect whether the assertion uses the true contract authority
2. inspect whether the runtime behavior is actually wrong
3. only then decide whether to patch product code

Do not assume every red test means runtime regression.

### 5.3 Backing Out An Exploratory Slice Is A Valid Quality Decision

We learned that backing out an exploratory regression is sometimes the correct move.

That is not failure.

It means:

1. the behavior is not yet stable enough to lock
2. the suite should remain trustworthy
3. engineering discipline is more important than pretending progress

Rule:

1. if a new test pushes beyond the current guaranteed surface, back it out cleanly instead of distorting the architecture

### 5.4 “Latest Authority Wins” Needs Explicit Tests

Many of the most valuable H3 tests were not about simple correctness.
They were about authority order:

1. latest grounded context replacing stale grounded context
2. accepted recovery consuming stale recovery
3. clarification clearing before later state can proceed
4. last fresh grounded query becoming the reasoning authority

Lesson:

1. state-machine order is a first-class risk area
2. these priority rules deserve explicit tests

## 6. What We Learned About State And Session Safety

### 6.1 Pending Clarification And Recovery Are The Two Core State Machines

Most meaningful H3 value came from focusing on:

1. pending clarification
2. recovery consumption

Why:

1. both are multi-turn
2. both can be resurrected accidentally
3. both can interfere with fresh queries and reasoning

This was a better starting point than trying to simulate broad concurrency all at once.

### 6.2 Mixed-State Interactions Matter More Than Isolated Happy Paths

The most useful state tests were mixed-state cases such as:

1. clarification preempting recovery
2. recovery resuming after clarification resolution
3. fresh-query replacing stale grounded context
4. latest grounded query winning before reasoning follow-up

Lesson:

1. interactions between state machines are often riskier than any one state machine alone

### 6.3 Duplicate User Actions Need Explicit Guarding

Repeated acceptance turns, repeated clarification turns, and repeated follow-up confirmations are not edge fluff.
They are normal user behavior.

We learned to lock:

1. duplicate recovery acceptance must not re-execute stale recovery
2. repeated clarification after stop must not resurrect stale state

That kind of behavior should be treated as standard reliability scope.

## 7. What We Learned About Observability

### 7.1 Observability Needs Both Shape Validation And Live Emission Validation

Builder-level tests were not enough.

We needed to verify:

1. payload shape
2. severity normalization
3. numeric metric normalization
4. live session emission
5. correlation fields like `session_id` and `request_id`

Lesson:

1. observability is only useful if both contract shape and runtime emission are trusted

### 7.2 Not Every Observability Path Is CI-Stable Yet

We tried to lock unsupported non-ERP live probes and found that some front-door/runtime behavior was not deterministic enough for honest CI gating.

Lesson:

1. do not force unstable live observability paths into CI
2. keep deterministic coverage where possible
3. wait until the live path is truly stable before promoting it

### 7.3 H2 Reached “Materially Strong” Before It Reached “Complete In Theory”

Another important lesson from H2 was that there is a practical stopping point.

We do not need infinite observability expansion before moving on.

What mattered was reaching a credible trusted core:

1. stable payload shape
2. live emission on the important lanes
3. correlation integrity
4. latency presence on the important paths

Rule:

1. once observability is materially strong for the intended release surface, move on
2. do not delay the whole program waiting for every possible metric dream

## 8. What We Learned About Adversarial Hardening

### 8.1 Unsupported Asks Can Piggyback On Real ERP Context If Isolation Is Weak

One major H4 lesson was that prior grounded ERP context can accidentally make unrelated asks look legitimate.

Examples:

1. creative asks after grounded reasoning
2. unsupported future-looking pressure after grounded ERP explanation

Lesson:

1. stale legitimate context is not harmless
2. unsupported asks can hide inside a legitimate conversation unless isolation is explicit

Rule:

1. unsupported current-turn intent must be allowed to override prior grounding authority when the ask itself is outside governed scope

### 8.2 Boundary Precedence Matters As Much As Boundary Rendering

We found a real bug where the assistant refused the turn correctly, but the boundary contract still labeled it as a valid ERP uncovered case because prior grounded context leaked into classification.

Lesson:

1. it is not enough for the prose answer to be safe
2. the contract and the prose must agree

Rule:

1. if scope says `unsupported_request`, stale grounding should not silently re-upgrade the turn into `valid_erp_domain_uncovered`

### 8.3 Some Dangerous Asks Belong In Reasoning Guardrails, Not Out-Of-Scope Refusal

Not every risky prompt should be forced into the same bucket.

We learned to distinguish:

1. clearly unsupported asks:
   - creative non-ERP requests
2. valid ERP-domain asks that still require safe refusal:
   - unsupported guarantees
   - unsupported forward-looking promises

That second group is often better handled as:

1. reasoning activation may occur
2. deterministic execution guardrail blocks unsafe answer
3. user gets bounded safe-stop language

Rule:

1. do not overuse out-of-scope classification when the real issue is unsupported reasoning guarantee or unsupported predictive certainty

### 8.4 H4 Should Be Judged By Non-Regression Sweep, Not Only By Its Own New Tests

A big H4 lesson was that adversarial coverage should not be declared “strong” just because the new adversarial module passes.

We only became confident after rerunning the surrounding hardening surface:

1. fast guard probes
2. fast state integrity
3. fast observability
4. live observability
5. live state/session
6. full post-contract regression

Rule:

1. adversarial hardening should be closure-reviewed against the wider stack, not only its local test file

## 9. What We Learned About Documentation

### 9.1 Governance Notes Should Track Honest Status, Not Aspirational Status

The docs were most useful when they said:

1. what is truly locked
2. what is exploratory
3. what was backed out
4. what remains outside the guaranteed surface

This made later decisions faster and safer.

### 9.2 Lessons Should Be Written During Hardening, Not Only After

A lot of the valuable judgment came from:

1. failed experiments
2. reverted tests
3. decisions not to overreach

Those are easy to forget later.

Rule:

1. capture hardening lessons while the tradeoffs are fresh
2. refine later if needed

### 9.3 Status Needs To Be Written Per Phase, Not Just “Hardening Is Ongoing”

Another documentation lesson is that a generic statement like “hardening is ongoing” becomes too vague once the work matures.

We needed the docs to say:

1. H1 materially complete
2. H2 materially strong
3. H3 closure-ready for intended state surface
4. H4 closure-ready for intended adversarial surface
5. release gates still remain

Rule:

1. document hardening status phase by phase
2. keep the remaining step explicit so the team does not confuse “strong” with “done”

### 9.4 Release Gates Should Be Executable, Not Merely Discussed

One more lesson became clear as we moved into H5:

1. release readiness should not live only in prose
2. at least part of the release gate must be runnable as code

What worked better:

1. a compact rollout probe for the live rollout-control surfaces
2. a compact executable sanity pack spanning the most important closed-stack lanes
3. keeping the release-gate pack small enough that it is credible to rerun before expansion decisions

Rule:

1. do not let the final closure step become a manual checklist with no executable spine
2. make the release gate small, real, and tied to already trusted hardening surfaces
3. after the executable spine is green, resist the urge to invent more gates unless a concrete risk is still uncovered

## 10. Guidance For Later Refactor Hardening

These lessons should directly guide refactor work later.

When refactoring:

1. move code in small slices
2. rerun the locked hardening surface after each slice
3. do not expand product behavior during refactor unless explicitly intended
4. prefer extracting around existing contract boundaries
5. keep regression assertions tied to authority contracts, not incidental implementation details

Practical meaning:

1. hardening knowledge is reusable
2. refactor should use this hardening discipline, not reset it

## 11. Guidance For Later Wave Expansion

When Wave 1 and later coverage expansion begins, reuse this pattern:

1. build the smallest trustworthy contract surface first
2. add deterministic fast tests
3. add a small number of high-value live tests
4. lock authority order and state interactions early
5. do not promote unstable “nice to have” behavior into CI

This should reduce future hardening cost significantly.

## 12. Practical Rules To Reuse Later

If we need a quick hardening checklist later, use this:

1. test the contract, not just the prose
2. separate fast deterministic tests from live stateful tests
3. run stateful verification sequentially when persistence is involved
4. treat duplicate user actions as normal, not rare
5. test authority order explicitly
6. do not lock unstable behavior into CI
7. back out exploratory tests if the contract is not yet real
8. keep docs honest about what is actually guaranteed
9. refactor only after stabilization, then rerun hardening
10. expansion should inherit the hardening discipline, not bypass it

## 13. Current Summary

The main hardening insight from this project so far is simple:

The winning strategy is not “test everything.”

It is:

1. identify the real authority surface
2. lock only deterministic guarantees
3. use live tests where state matters
4. refuse fake certainty
5. preserve engineering judgment in docs, not only in code

Current status snapshot to remember:

1. H1 is materially complete
2. H2 is materially strong for the intended observability surface
3. H3 is closure-ready for the intended state surface
4. H4 is closure-ready for the intended adversarial surface
5. H5 is closure-ready for the automated release-gate surface
6. only a brief optional manual live sanity / operator signoff remains before Wave 1 expansion

That is the part we should carry forward into refactor, Wave 1 expansion, and every later enterprise chapter.
