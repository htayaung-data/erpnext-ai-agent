# Qwen ERP `service.py` Refactor And Delivery Guidance

Status: active technical implementation note  
Date: 2026-04-20  
Scope: delivery guidance for the current AI assistant implementation phase, plus the controlled refactor plan for `ai_assistant_ui/qwen_chat/service.py`

## 1. Purpose

This note gives the AI Assistant development team one clear answer to two questions:

1. should current governed assistant feature work continue even though `service.py` is already too large
2. how should the team implement current and future tasks so that the later `service.py` refactor is safer, faster, and more systematic

This note is not a rewrite proposal.

It is a practical engineering control note for the current in-between state:

1. feature completion is still in progress
2. `service.py` is already too large and will likely grow further before the current chapter closes
3. a systematic refactor is still required, but should happen as a governed chapter rather than as ad hoc cleanup during every feature

## 2. Current Decision

The current decision is:

1. do not stop the remaining governed AI assistant implementation solely because `service.py` is already large
2. continue the current implementation wave
3. during that wave, implement in a refactor-compatible way
4. after the current feature chapter stabilizes, execute a dedicated `service.py` refactor program

This means the team should not treat current feature work and future refactor work as competing priorities.

The correct model is:

1. finish the currently approved governed feature surface
2. prevent unnecessary new gravity from being added to `service.py`
3. then run a dedicated extraction chapter with explicit seams and verification

## 3. Current Reality

The current `service.py` file at:

`impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

is not just one service function.

It is currently acting as all of the following:

1. public assistant runtime entrypoint
2. orchestration layer for governed turn handling
3. compatibility facade over already-extracted helper modules
4. conversation-state and control logic host
5. evidence and boundary helper host
6. smoke, probe, regression, and debug runner host

That is why it grows continuously.

The issue is not only file length.

The deeper issue is role mixing.

## 4. Non-Negotiable Engineering Rule

From this point onward, the team must treat `service.py` as a temporary orchestration shell, not as the preferred home for new business logic.

This means:

1. `service.py` may still grow during the current implementation chapter
2. but new behavior should enter through extracted helpers or modules whenever practical
3. `service.py` should mainly gain wiring, ordering, and explicit stage calls
4. `service.py` should not keep absorbing entire new domains of logic

## 5. What The Team Should Do Right Now

During the current implementation chapter, the team should continue feature work under the following rules.

### 5.1 Allowed

The following are allowed:

1. adding new orchestration call-sites in `handle_qwen_user_message`
2. adding minimal bridging code needed to connect a new governed lane, contract, or helper
3. extending existing contracts and helper modules outside `service.py`
4. adding temporary in-file code only when extraction would slow the active delivery slice too much

### 5.2 Not Allowed

The following should be treated as disallowed unless there is a very strong reason:

1. adding whole new feature domains directly inside `service.py`
2. placing new smoke, debug, or probe utilities in `service.py`
3. copying an existing orchestration block and slightly modifying it for a new case
4. introducing more wrapper noise that only forwards to another helper without adding value
5. mixing behavior change and cleanup change in one uncontrolled patch

### 5.3 Immediate Bounded Extraction Being Executed Now

The first bounded extraction during the current implementation chapter should be:

1. move the first slice of Phase E scope-package smoke runners out of `service.py` into a dedicated evaluation module
2. keep only thin compatibility wrappers in `service.py` where callers still expect those entrypoints
3. add no new Phase E smoke or debug bodies directly into `service.py`
4. continue the current governed delivery wave only after that seam is in place

This is intentionally a small live extraction, not the full refactor chapter.
It reduces file gravity now without turning the active delivery wave into a broad orchestration rewrite.

### 5.4 Current `IC5-C` Close-Out Rule

The current `IC5-C` review has now reached an important boundary:

1. most of the reusable restore-policy and restore-arbitration logic has already been moved behind shared helper seams
2. the remaining prior-branch restore surface in `service.py` is now mostly:
   - append/save ordering
   - execution-path wiring
   - direct dispatch between already-normalized restore modes
   - replay-through-runtime orchestration
3. that remaining surface should currently be treated as facade orchestration unless a new extraction candidate proves it is truly shared policy
4. the team should not force another extraction there just to make `service.py` shorter if that extraction would only create wrapper noise or split one ordered flow across multiple files without adding a clearer contract
5. this means `IC5-C` can move into close-out review while the later dedicated `service.py` refactor chapter remains the correct place for deeper orchestration slimming

## 6. Current Implementation Rules

Every team member working on assistant features should follow these implementation rules immediately.

### 6.1 New domain logic goes to a module first

If the change introduces any of the following:

1. new decision logic
2. new rendering logic
3. new clarification logic
4. new evidence logic
5. new continuation logic
6. new interpretation or normalization logic

then the default location is a dedicated helper or module, not `service.py`.

`service.py` should only call it.

### 6.2 `handle_qwen_user_message` should gain stage calls, not story-sized blocks

If a proposed change adds more than a small orchestration bridge, the developer should first ask:

1. can this be a function with a narrow return value
2. can this be a lane helper
3. can this be a state helper
4. can this be a boundary helper
5. can this be a delivery-specific module outside the facade

If yes, do that first.

### 6.3 Use extraction-friendly naming now

Even when code must temporarily remain in `service.py`, it should be written as though it will be moved soon.

That means:

1. use focused helper names
2. avoid giant anonymous local blocks
3. keep input and output shapes explicit
4. avoid hidden mutation where possible
5. keep domain vocabulary aligned with existing contracts and lanes

### 6.4 Preserve architecture vocabulary

Do not casually rename:

1. lane concepts
2. contract concepts
3. execution-path concepts
4. audit payload concepts
5. governed scope concepts

Refactor location, not meaning.

### 6.5 Prefer pure helpers where possible

When extracting new logic, prefer helpers that:

1. accept explicit inputs
2. return explicit outputs
3. do not append session messages directly unless that is their job
4. do not save the session unless that is their job

The more side effects are isolated, the easier the later facade refactor becomes.

### 6.6 New evaluation utilities must not be added to `service.py`

All new:

1. smokes
2. probes
3. regression utilities
4. diagnostics
5. evaluation suites

should be placed in dedicated evaluation modules.

The current file already contains too many of these and should not receive more.

## 7. Required Mental Model For Current Work

During the current implementation chapter, the team should work under this model:

1. `service.py` is the turn facade
2. extracted modules own the detailed behavior
3. lane modules own lane behavior
4. contracts remain the runtime currency
5. metadata and registries remain the source of policy truth

This is important because the project must not drift into:

1. prompt-shaped business branching
2. one-off service-level rescue logic
3. specialized behavior hidden only in orchestration code
4. duplicated continuation or clarification logic

## 8. Refactor Target State

After the current feature chapter is complete, the target role of `service.py` should become:

1. load session and request context
2. normalize current-turn control overrides
3. call named orchestration stages
4. persist output artifacts through a controlled recorder/journal seam
5. return the final payload

The target file should not remain the home of:

1. most conversation snapshot logic
2. most conversation-control logic
3. most evidence and boundary logic
4. most runtime message compilation logic
5. smoke and debug runner libraries

## 9. Recommended Extraction Seams

The later refactor should be done by seam, not by arbitrary line count.

### 9.1 Evaluation seam

Move out:

1. smokes
2. probes
3. debug runners
4. family evaluation suites

Reason:

1. low production risk
2. large immediate line reduction
3. clear ownership boundary

### 9.2 Conversation snapshot seam

Move out:

1. `_snapshot_*`
2. `_historical_*`
3. `_build_conversation_state_snapshot`
4. related state compatibility helpers

Reason:

1. this is a coherent domain
2. it is not the orchestration facade itself
3. it reduces the turn-start cognitive load in `handle_qwen_user_message`

### 9.3 Conversation control seam

Move out:

1. control evidence logic
2. prior-branch restore logic
3. recent-focus logic
4. compound-request continuation / completion / cancellation logic
5. restore-affordance logic

Reason:

1. this is one of the biggest clusters in the file
2. it is conceptually one subsystem
3. it has its own decision model and should not be flattened into the facade

### 9.4 Evidence and boundary seam

Move out:

1. direct evidence payload and answer helpers
2. evidence boundary helpers
3. enrichment boundary helpers
4. recovery appenders
5. knowledge-boundary helper orchestration that does not need to stay in the facade

Reason:

1. boundary handling is already a first-class governed concept
2. it deserves its own stable implementation home

### 9.5 Runtime message compilation seam

Move out:

1. requery compilation helpers
2. contextual breakout helpers
3. recent-focus runtime message generation
4. helper logic that rewrites the runtime-facing message before lane selection

Reason:

1. this is orchestration support logic, not the facade itself
2. it grows whenever continuation sophistication grows

## 10. Recommended Future Module Map

The exact file names may vary, but the following target shape is recommended:

1. `qwen_chat/service.py`
   role: public turn facade only
2. `qwen_chat/orchestration/turn_context.py`
   role: turn-level typed context or shared orchestration state
3. `qwen_chat/orchestration/conversation_snapshot.py`
   role: current and historical conversation state assembly
4. `qwen_chat/orchestration/conversation_control.py`
   role: control evidence, restore, recent focus, compound flow
5. `qwen_chat/orchestration/runtime_message_compilation.py`
   role: runtime message rewriting and requery compilation
6. `qwen_chat/orchestration/turn_journal.py`
   role: session append ordering, audit finalization, save control
7. `qwen_chat/evaluation/smokes.py`
   role: smoke runners
8. `qwen_chat/evaluation/probes.py`
   role: probes and debug runners
9. `qwen_chat/evaluation/family_suite.py`
   role: family evaluation suite orchestration

This is a target map, not an immediate requirement.

## 11. Recommended Refactor Sequence

When the dedicated refactor chapter begins, use this order:

1. extract evaluation utilities out of `service.py`
2. remove wrapper-only noise where safe
3. extract conversation snapshot logic
4. extract conversation control logic
5. introduce a turn-context object if needed
6. introduce a recorder or journal seam for persistence
7. split `handle_qwen_user_message` into explicit stage functions
8. then do secondary cleanup only after behavior is stable

This order is recommended because it gives:

1. quick size reduction early
2. low-risk wins first
3. better understanding before touching the orchestration core

### 11.1 Immediate execution inside the current delivery chapter

Before the full refactor chapter begins, the team should execute one small live extraction now:

1. create a dedicated evaluation module for the first scope-package smoke slice
2. remove the moved bodies from `service.py`
3. keep temporary thin wrappers only for compatibility
4. verify no runtime lane precedence changed
5. then return to the active governed implementation slice

## 12. Stage-Based Shape For `handle_qwen_user_message`

The future top-level function should read like a pipeline.

Recommended high-level stages:

1. load session and turn context
2. build conversation snapshot
3. apply control override normalization
4. resolve restore and pending clarification state
5. evaluate front door
6. evaluate pre-runtime reasoning activation
7. build follow-up resolution and scope decision
8. try non-runtime handled lanes
9. choose runtime path
10. finalize artifacts, audit, and persistence

If the top-level function does not read like this, the facade refactor is not complete.

## 13. PR Rules During Current And Future Work

Every PR touching `service.py` should follow these rules:

1. state whether the change is feature delivery, extraction, or both
2. if both, justify why combining them is safer than separating them
3. list any new helper/module introduced outside `service.py`
4. explain whether lane precedence changed
5. explain whether contract payload shape changed
6. identify whether any new smoke or probe was added and where it lives

If a PR adds more than a modest amount of code to `service.py`, it should also state:

1. why that logic could not yet be extracted
2. what future seam it belongs to

## 14. Required Testing Discipline

Do not refactor this file based on confidence or visual cleanliness alone.

Any meaningful extraction or orchestration change should preserve characterization coverage for:

1. pending clarification handling
2. prior-branch restore handling
3. compound-request continuation, completion, and cancellation
4. context isolation and fresh-query reset
5. evidence direct-answer versus evidence-boundary handling
6. local transform versus runtime fallback handling
7. out-of-scope guarded behavior
8. lane ordering and precedence

The greatest risk in this refactor is not syntax breakage.

The greatest risk is precedence drift.

## 15. Stop Conditions

The team should pause feature expansion and prioritize the refactor earlier if any of the following become true:

1. developers are afraid to touch `service.py`
2. most new bugs come from flow-order interactions
3. the same orchestration pattern is being copied repeatedly
4. merge conflicts in `service.py` become frequent
5. it becomes difficult to identify which stage owns a decision
6. one feature requires edits across many unrelated service-level clusters

If these signals become strong before the current implementation chapter ends, the refactor should be pulled forward.

## 16. Definition Of Success

This guidance is successful if the team achieves both of the following:

1. the current governed assistant implementation chapter completes without unnecessary disruption
2. the later `service.py` refactor becomes a structured extraction program rather than a rescue rewrite

The desired end state is not:

1. a perfectly small file immediately

The desired end state is:

1. feature completion now
2. controlled gravity during the current chapter
3. clean seam extraction afterward

## 17. Final Team Rule

Until the dedicated refactor chapter begins, every developer should work under this rule:

1. finish the current governed feature surface
2. add the minimum necessary orchestration glue to `service.py`
3. place new business logic outside the facade whenever practical
4. leave behind extraction seams, not new gravity wells

## 18. Applied Controlled Extraction Example

This guidance is already active in implementation, not only theoretical.

One concrete example already completed during the current delivery wave:

1. recent-focus affordance policy helpers were extracted from `service.py` into a dedicated shared helper module
2. the public `service.py` affordance seam was preserved as a thin orchestration wrapper
3. runtime behavior was kept stable
4. the full live `test_post_contract_state_integrity` suite was rerun green after the extraction

Why this example matters:

1. it proves the team can reduce facade gravity without pausing the active `IC4` / `IC5` implementation wave
2. it matches the intended pattern for the current chapter:
   keep `service.py` as orchestration shell, move detailed policy behavior outward
3. it should be treated as the model for further small safe seam extractions until the dedicated refactor chapter begins

## 19. Applied No-Fake-Extraction Example

This guidance also applies in the opposite direction.

One concrete example from the current `IC5-C` close-out review:

1. the remaining direct prior-branch restore handlers in `service.py` were reviewed after multiple restore-policy extractions had already landed
2. that review found the residual logic is now primarily ordered orchestration, not broad reusable business policy
3. because of that, the correct enterprise-grade move is:
   - do not force another helper extraction only to move append/save/dispatch glue elsewhere
   - record the boundary explicitly
   - return to broader mini-phase closure work
   - leave deeper orchestration slimming to the later dedicated refactor chapter

Why this example matters:

1. it prevents the team from mistaking line movement for architecture improvement
2. it reinforces the rule that extraction must create a real seam, not just a smaller-looking facade
3. it keeps the current implementation chapter focused on governed behavior closure while preserving a cleaner refactor target for later
