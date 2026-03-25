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

This is the new enterprise roadmap from now on.

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

Current next priority.

Goal:

1. finish `GovernedScopeDecisionContract`
2. make it the real authority for:
   - local continuation
   - governed requery
   - clarify
   - fresh query
   - governed out-of-scope

Important rule:

1. do not solve semantic or unknown cases by adding more local term patches
2. solve them by improving scope decision quality

Still to add here:

1. stronger treatment of:
   - ambiguous ERP-business semantic questions
   - valid ERP-domain but not-yet-covered questions
   - safe escalation from governed artifact lane into later ERP reasoning lane

## Mini-phase 4

After Contract 2 is clean enough.

Goal:

1. build `ClarificationReasonContract`
2. unify clarification cause across fresh-query, follow-up, and boundary decisions

It must own:

1. why clarification is required
2. what is missing or ambiguous
3. whether the clarification is blocking
4. what user-safe options may be suggested

## Mini-phase 5

After the first 3 contracts are clean enough.

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

## Mini-phase 6

After front-door gate exists.

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

Integration phase.

Goal:

1. integrate front-door + artifact lane + reasoning lane + boundary layer
2. retire legacy split-authority branches
3. prove behavior with browser regression packs

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

1. continue Mini-phase 3
2. finish `GovernedScopeDecisionContract` cleanly
3. make it better at handling:
   - ambiguous ERP-business questions
   - valid-but-not-covered ERP business questions
   - safe transition points for the future ERP reasoning lane

What is explicitly not next:

1. not report-family expansion
2. not more term-pair fixes
3. not front-door implementation yet
4. not ERP business reasoning implementation yet

## 8. Practical Summary

What we have done:

1. started the 3-contract migration
2. improved continuation and scope architecture materially
3. improved several governed finance support surfaces
4. documented contract inventory and post-contract expansion backlog

Where we are now:

1. Contract 1 and Contract 2 are partially real
2. architecture direction is clearer
3. semantic-question policy is still missing

What is next:

1. finish Contract 2 cleanly
2. then build Contract 3
3. then build front door
4. then build ERP business reasoning
5. then build knowledge boundary
6. then integrate all lanes cleanly
