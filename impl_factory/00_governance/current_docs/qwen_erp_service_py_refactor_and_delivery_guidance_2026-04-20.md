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

1. move the remaining H3 conversation-control smoke runners out of `service.py` into the existing `qwen_chat/evaluation/conversation_control_smokes.py` module
2. keep only thin compatibility wrappers in `service.py` where callers still expect those entrypoints
3. extend the existing dependency-bundle pattern instead of creating another parallel smoke seam
4. add no new H3 conversation-control smoke or debug bodies directly into `service.py`
5. continue the current governed delivery wave only after that seam is in place

This is intentionally a small live extraction, not the full refactor chapter.
It reduces file gravity now without turning the active delivery wave into a broad orchestration rewrite.

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

## 19. Practical Mini-Phase Plan For The Dedicated Refactor Chapter

This section converts the general guidance above into a practical execution plan based on the current codebase state after `IC6` closure.

### 19.1 Current Code Audit Summary

The current project is in a better position than an untouched monolith.

The refactor should explicitly build on already-extracted seams rather than restart architecture work from zero.

Current facts:

1. `service.py` is still very large at roughly 13.9k lines and 382 top-level defs/classes
2. major extraction anchors already exist:
   - `recent_focus_support.py`
   - `restore_support.py`
   - `snapshot_defaults.py`
   - `conversation_control_support.py`
   - `compiled_support.py`
   - `boundary_support.py`
   - `continuation_support.py`
   - `requery_message_support.py`
   - `lanes/`
   - `evaluation/`
3. this means the refactor is not a new architecture design problem
4. it is now a seam-completion and orchestration-normalization problem

Practical implication:

1. do not create many new concept modules unless current extracted modules are clearly the wrong ownership home
2. prefer finishing ownership transfer into existing shared modules first
3. only introduce a new module when it creates a stable seam, not just because the file is large

Additional audit conclusion:

1. `service.py` already imports these extracted seams as live runtime dependencies, not as dead experiments
2. this proves the project has already been refactoring incrementally during implementation
3. therefore the dedicated refactor chapter must integrate with those existing modules first, not replace them with a second parallel architecture

Enterprise rule for this chapter:

1. treat the current extracted modules as the default ownership candidates
2. extend or finish those modules before inventing new ones
3. only create a new orchestration module when the existing extracted homes would become conceptually mixed or unstable

### 19.2 Refactor Chapter Goal

The goal of this chapter is:

1. make `service.py` read like a turn facade and orchestration pipeline
2. move remaining detailed subsystem logic into stable shared modules
3. preserve live behavior and lane precedence while reducing role mixing

This chapter is successful when:

1. `handle_qwen_user_message` becomes stage-shaped and easier to reason about
2. snapshot/control/runtime-message/evaluation logic no longer have large inline clusters in `service.py`
3. the refactor does not invent new business behavior

### 19.3 Mini-Phase Sequence

The dedicated refactor chapter should use the following mini phases.

#### SR0 Refactor Baseline Lock

Status: `next`

Purpose:

1. freeze the current refactor starting point before extractions begin
2. make later drift visible

Deliverables:

1. record current file metrics for `service.py`
2. record the active characterization suite that guards precedence and conversation control
3. identify the exact extraction candidates for each seam before code moves

Verification:

1. focused characterization suite green
2. current ownership inventory documented

#### SR1 Evaluation Seam Completion

Status: `next`

Purpose:

1. finish moving smoke, probe, debug, and family-evaluation bodies out of `service.py`
2. leave only thin compatibility wrappers in the facade when needed

Why first:

1. low runtime risk
2. large immediate line reduction
3. the project already has an `evaluation/` package, so this is a seam-completion task rather than a greenfield extraction

Deliverables:

1. move remaining Phase and H-series evaluation bodies into dedicated evaluation modules
2. keep wrapper-only entrypoints in `service.py` only where external callers still rely on them
3. do not leave new evaluation implementation bodies in `service.py`
4. prefer the existing `qwen_chat/evaluation/` package as the ownership home instead of creating a second evaluation structure

Verification:

1. evaluation entrypoints still callable
2. runtime behavior unchanged
3. focused characterization suite still green

#### SR2 Conversation Snapshot Seam Completion

Status: `next`

Purpose:

1. extract the remaining `_snapshot_*`, `_historical_*`, and `_build_conversation_state_snapshot` cluster out of `service.py`
2. reduce turn-start cognitive load in the facade

Why second:

1. snapshot logic is coherent
2. `snapshot_defaults.py` already exists
3. this seam is conceptually stable and largely data-shaping focused

Preferred target:

1. introduce an orchestration snapshot module such as `qwen_chat/orchestration/conversation_snapshot.py`
2. reuse `snapshot_defaults.py` instead of duplicating default-state shaping
3. if the existing snapshot-support surfaces can absorb the remaining logic cleanly, prefer that over creating unnecessary parallel helpers

Deliverables:

1. move snapshot assembly logic out of `service.py`
2. keep only a thin facade call from `handle_qwen_user_message`
3. preserve the current snapshot payload contract exactly unless a deliberate contract change is approved

Verification:

1. snapshot-related characterization tests stay green
2. recent-focus, pending-clarification, active-sequence, and resumable-prior behavior remain unchanged

#### SR3 Conversation Control Seam Completion

Status: `next`

Purpose:

1. extract the remaining control-decision cluster from `service.py`
2. consolidate ownership around shared control modules instead of facade-local arbitration

Why third:

1. this is the highest-value seam after snapshot extraction
2. the subsystem is already partly extracted into `conversation_control_support.py`, `recent_focus_support.py`, `restore_support.py`, and `compound_request_support.py`
3. what remains in `service.py` is now more clearly orchestration versus residual policy ownership

Deliverables:

1. move remaining recent-focus runtime decision helpers out of `service.py`
2. move remaining prior-branch restore contract-building helpers out of `service.py`
3. move remaining compound completion / continuation / cancellation decision helpers out of `service.py`
4. keep the facade responsible only for stage ordering and final branch selection
5. prefer existing ownership homes:
   - `conversation_control_support.py`
   - `recent_focus_support.py`
   - `restore_support.py`
   - `compound_request_support.py`

Verification:

1. pending clarification handling preserved
2. prior-branch restore precedence preserved
3. compound-request continuation / completion / cancellation preserved
4. no new transcript-local rescue logic introduced

#### SR4 Runtime Message Compilation Seam

Status: `next`

Purpose:

1. pull runtime-message rewriting and requery-message compilation out of the facade
2. make front-door and follow-up message shaping easier to audit

Why fourth:

1. this logic grows whenever continuation sophistication grows
2. parts already exist in `compiled_support.py` and `requery_message_support.py`
3. this seam should be stabilized before the final facade-stage split

Deliverables:

1. move recent-focus runtime message generation out of `service.py`
2. move remaining breakout/requery compilation helpers out of `service.py`
3. normalize ownership between `compiled_support.py`, `requery_message_support.py`, and any new orchestration runtime-message module
4. do not create a new runtime-message module if `compiled_support.py` and `requery_message_support.py` can absorb the remaining logic cleanly without becoming mixed-role monoliths themselves

Verification:

1. local-transform versus runtime fallback behavior preserved
2. out-of-scope guarded behavior preserved
3. lane ordering preserved

#### SR5 Turn Journal And Persistence Seam

Status: `next`

Purpose:

1. separate append ordering, audit finalization, and save behavior from turn decision logic
2. prepare the facade for a clean stage-based shape

Why fifth:

1. side-effect isolation is easier after snapshot/control/runtime-message ownership is cleaner
2. this seam is about orchestration safety, not business policy

Preferred target:

1. introduce a small orchestration journal module such as `qwen_chat/orchestration/turn_journal.py`
2. optionally introduce a minimal turn context object only if the call surface becomes materially clearer

Deliverables:

1. isolate append-message, append-tool-payload, audit-envelope, and save ordering helpers behind a narrower seam
2. reduce direct persistence noise inside `handle_qwen_user_message`

Verification:

1. artifact append order preserved
2. audit payload ordering preserved
3. no save-path regressions

#### SR6 Facade Stage Split

Status: `next`

Purpose:

1. make `handle_qwen_user_message` read like the intended pipeline
2. finish the dedicated refactor chapter with explicit stage boundaries

Target stages:

1. load session and turn context
2. build conversation snapshot
3. normalize control overrides
4. resolve restore and pending clarification state
5. evaluate front door
6. evaluate pre-runtime reasoning activation
7. build follow-up resolution and scope decision
8. try non-runtime handled lanes
9. choose runtime path
10. finalize artifacts, audit, and persistence

Deliverables:

1. replace story-sized flow blocks with named stage helpers
2. keep top-level orchestration readable
3. remove wrapper-only noise where safe

Verification:

1. full focused characterization suite green
2. no lane precedence drift
3. no contract payload regressions unless explicitly approved

#### SR7 Refactor Closure Review

Status: `next`

Purpose:

1. decide whether the dedicated refactor chapter is complete enough to close
2. hand back to the broader roadmap without leaving hidden facade re-growth

Deliverables:

1. before/after file-role summary
2. open debt list for anything intentionally deferred
3. explicit statement of what future work still belongs in shared modules versus in the facade

### 19.4 Recommended Immediate Execution Order

The practical order should be:

1. `SR0`
2. `SR1`
3. `SR2`
4. `SR3`
5. `SR4`
6. `SR5`
7. `SR6`
8. `SR7`

Execution note:

1. each mini phase should begin with an ownership check against already-extracted modules
2. “move out of `service.py`” does not automatically mean “create a brand-new file”
3. the default should be to complete existing seams first

### 19.5 What We Should Not Do In This Chapter

To keep this enterprise grade, do not:

1. combine the dedicated refactor chapter with new scope-family feature expansion
2. treat line count reduction as the primary success metric
3. move code into new modules without clear subsystem ownership
4. rewrite behavior while claiming to only refactor
5. reopen already-closed conversation-control delivery slices unless the extraction reveals a real shared policy gap

### 19.6 Recommended Next Practical Move

The next practical move should be:

1. start `SR0` baseline lock
2. then execute `SR1` evaluation seam completion as the first real extraction slice

Reason:

1. it is the safest place to begin
2. it matches the already-approved guidance sequence
3. it reduces `service.py` gravity immediately without touching the highest-risk precedence logic first

## 20. Consultant Addendum: Acceptance Criteria And Governance Tightening

This addendum records a second careful project re-evaluation after the `IC6` closure checkpoint.

Conclusion:

1. the current refactor chapter direction is correct
2. the project is not starting from zero
3. the primary improvement needed is stronger ownership governance during execution, not a redesign of the chapter

### 20.1 Honest Re-Evaluation

The current codebase already contains meaningful live extractions.

This means the dedicated `service.py` refactor chapter must be treated as:

1. seam completion
2. orchestration normalization
3. ownership clarification

It must not be treated as:

1. a fresh architecture rewrite
2. a chance to create a second parallel module map
3. a cleanup sprint optimized only for line count reduction

### 20.2 Refactor Chapter Acceptance Criteria

The chapter should be considered successful only if all of the following become true:

1. `service.py` reads primarily as a turn facade and stage-oriented orchestration shell
2. remaining subsystem logic in `service.py` is there because it is truly facade orchestration, not because ownership was unclear
3. no second parallel architecture has been created beside the already-extracted modules
4. existing characterization coverage remains green and precedence behavior remains stable
5. the team can resume main roadmap work without treating `service.py` as the default home for new business logic again

### 20.3 Mandatory Ownership Rule Before Any Extraction

Before moving any cluster out of `service.py`, the team must first answer:

1. does an existing module already provide the correct ownership home
2. if yes, why should the logic not move there now
3. if no, why is a new module genuinely required instead of just convenient

This must be explicit for every meaningful extraction.

Default ownership candidates should be considered first:

1. `conversation_control_support.py`
2. `recent_focus_support.py`
3. `restore_support.py`
4. `snapshot_defaults.py`
5. `compound_request_support.py`
6. `compiled_support.py`
7. `boundary_support.py`
8. `requery_message_support.py`
9. `evaluation/`
10. `lanes/`

### 20.4 Strengthened SR0 Requirement

`SR0` should not stop at file metrics and test inventory.

It should produce a lightweight ownership map covering:

1. cluster name
2. current location in `service.py`
3. intended ownership home
4. extraction type:
   - full move
   - move plus thin compatibility wrapper
   - stay in facade for now
5. rationale for that decision

This ownership map is the gate that prevents drift during the refactor chapter.

### 20.5 True Facade Logic Rule

The chapter should explicitly distinguish between:

1. logic that belongs in the facade
2. logic that only still happens to live in the facade

Likely true facade responsibilities:

1. session and request loading
2. top-level stage ordering
3. lane handoff orchestration
4. final result routing
5. persistence orchestration unless and until a dedicated journal seam is stable enough

Likely non-facade responsibilities:

1. snapshot assembly details
2. recent-focus policy details
3. prior-branch restore policy details
4. compound step transition policy
5. runtime message shaping details
6. evaluation bodies

### 20.6 Exit Criteria Per Mini Phase

Each `SR` mini phase should define and record:

1. what code moved
2. what code intentionally stayed
3. which module is now authoritative for that seam
4. what focused tests were used to verify the move
5. what known follow-on debt remains

Without this, the chapter risks becoming endless cleanup instead of governed refactoring.

### 20.7 Enterprise Warning

One of the biggest risks in this chapter is false progress through relocation.

Examples of false progress:

1. moving a large block from `service.py` into one new oversized helper without clear subsystem ownership
2. creating a second competing orchestration module set while the first extracted modules already exist
3. mixing behavior change with extraction and then calling the result “just refactor”

The chapter should optimize for stable ownership, not for visual neatness alone.

### 20.8 Updated Recommendation

The refactor chapter should proceed, but with stricter execution discipline:

1. perform `SR0` as a true ownership-lock checkpoint
2. begin with `SR1` evaluation seam completion
3. prefer completing existing extracted seams over creating new files
4. treat `SR2` and `SR3` as high-sensitivity characterization-led extractions
5. return to main roadmap work only after the refactor chapter reaches a deliberate closure checkpoint

### 20.9 Current Execution Baseline

The active `SR0` checkpoint for this chapter is recorded separately in:

1. `qwen_erp_service_py_refactor_sr0_baseline_2026-04-22.md`

That baseline should be treated as:

1. the dated ownership-lock starting point for the chapter
2. the reference for current file metrics
3. the reference for the primary guarded test suite
4. the reference for the next immediate move into `SR1`
