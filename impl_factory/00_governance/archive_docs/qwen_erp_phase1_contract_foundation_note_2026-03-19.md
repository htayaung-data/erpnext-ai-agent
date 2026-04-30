# Qwen ERP Phase 1 Contract Foundation Note (2026-03-19)

Status: completed with known gaps  
Scope: enterprise Phase 1 from the Qwen ERP blueprint  
Phase goal: establish the first contract-governed foundation for the Qwen chat path so follow-up and execution behavior no longer lives only as implicit model behavior.

## Objective

Phase 1 was defined as the contract foundation layer:

1. `InteractionContract`
2. `GroundedTurnContext`
3. `FollowUpResolution`
4. `ExecutionPath`

The purpose of this phase was not to make the product feature-complete.  
The purpose was to introduce a stable internal state model that later phases can build on safely.

## What Was Implemented

### 1. Interaction contract

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`

Each Qwen chat turn now records a hidden `qwen_interaction_contract` containing:

- request id
- session id
- user id
- site name
- raw message
- detected language
- UI channel
- received timestamp

### 2. Follow-up resolution contract

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Each turn now records a hidden `qwen_followup_resolution` with a typed mode, currently including:

- `new_query`
- `grounded_follow_up`
- `presentation_transform`

This phase intentionally kept the resolver simple and safe.  
The main change is that follow-up handling now has an explicit contract instead of only informal runtime behavior.

### 3. Execution path contract

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Each turn now records a hidden `qwen_execution_path` describing whether the system chose:

- `local_transform`
- `erp_requery`

This is the first step toward enterprise auditability for follow-ups.

### 4. Grounded turn context

Implemented in:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/qwen_agent_engine.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/schemas.py`

For successful grounded ERP answers, the system now records a hidden `qwen_grounded_turn_context` with:

- grounding status
- source kind
- source report/tool name
- company
- date range
- report filters
- dimensions
- metrics
- returned schema
- table rows
- row count
- base language

This required a runtime trace improvement so tool traces now preserve machine-usable structured arguments through `detail_obj`, not only shortened preview strings.

## What Was Fixed During Phase 1

Two important implementation corrections were made during the phase:

1. grounded context was initially being built from the runtime trace message rather than the assistant payload
2. runtime tool traces were initially too lossy for reliable contract reconstruction because arguments were stored only as truncated text

Both issues were corrected before this note was written.

## Verification Performed

Technical verification completed:

1. Python compile checks passed for:
   - ERP-side `contracts.py`
   - ERP-side `service.py`
   - ERP-side `api.py`
   - runtime-side app modules
2. Runtime rebuilt successfully
3. Backend and websocket restarted successfully
4. Runtime health check succeeded
5. Fresh session verification confirmed hidden contract persistence for:
   - `qwen_interaction_contract`
   - `qwen_followup_resolution`
   - `qwen_execution_path`
   - `qwen_grounded_turn_context`
6. Verified behavior across:
   - fresh grounded read query
   - presentation transform follow-up
   - self-contained requery in the same session

Verified examples:

1. `show sales last month`
2. `Show in million`
3. `show sales last month only for Yangon`

## What Phase 1 Does Not Yet Do

This phase intentionally does not yet provide:

1. a rich typed follow-up taxonomy beyond the first safe modes
2. full policy-driven capability registry enforcement
3. stronger result validation rules
4. write proposal / confirmation handling
5. artifact contracts for chart/report/dashboard generation
6. Burmese language layer
7. dedicated least-privilege service-user security

Those belong to later phases.

## Manual Browser Sign-Off

Manual browser sign-off is recommended, but it is not the primary closure criterion for this phase.

Reason:

1. Phase 1 is mainly a backend/control-plane foundation phase
2. the key success condition is correct hidden contract persistence and runtime decision recording
3. visible UI behavior was not the main scope of this phase

So the correct operational stance is:

1. engineering completion is justified
2. browser confirmation is still useful as a sanity check
3. release-level quality should still be judged after later user-visible phases

## Exit Decision

Phase 1 is considered:

`completed with known gaps`

Why not plain `completed`:

1. the contract foundation is in place and verified
2. but later phases are still required before enterprise release claims are justified
3. manual browser confirmation for this phase has not been treated as a formal sign-off artifact

## Next Phase

Phase 2: Read Query Hardening

Planned focus:

1. capability/report registry tightening
2. tool gateway policy refinement
3. stronger grounded validation
4. richer audit envelope

