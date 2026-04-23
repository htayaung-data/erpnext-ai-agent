# Qwen ERP Master-Data Front-Door Typed Activation Slice Design

Status: proposed next implementation slice  
Date: 2026-04-14  
Scope: exact design for the next enterprise slice after Phase A baseline establishment, focused on replacing interim master-data lexical recovery with typed front-door activation

## 1. Purpose

This note defines the exact next implementation slice that should follow the completed Phase A backbone and the recent customer/supplier activation work.

It exists because the current system has improved materially, but one important architectural bridge remains:

1. master-data recovery still relies on alias inference inside `fresh_query_interpreter.py`
2. that bridge is safer than the earlier customer-only branching
3. but it is still not the final enterprise seam for broad scope expansion

The next slice must move master-data request interpretation one layer earlier:

1. from lexical recovery inside fresh-query interpretation
2. to typed front-door assessment and ambiguity handling

This slice is the correct next move because it:

1. directly addresses the review finding
2. strengthens the architecture before item/product expansion
3. preserves the existing contract ecosystem instead of creating a parallel path

## 2. Roadmap Placement

This slice should be treated as:

1. the first post-Phase-A cleanup and alignment slice
2. primarily `Phase B.1 + B.3 + C.1`
3. with limited `Phase F` impact for typed ambiguity coverage

In practical roadmap language:

1. Phase A baseline is substantially established
2. this slice is the next foundation slice before further scope package expansion
3. it should run before `E1.3 item/product ownership decision` and `E1.4 item/product activation`

## 3. Current State Summary

### 3.1 What is already good

The system already has:

1. canonical governed scope metadata registries from Phase A
2. active customer and supplier master-data directory routing
3. shared `master_data_directory` family behavior
4. existing entity-reference policy metadata
5. clarification framework and pending-clarification continuation
6. a working front-door clarification seam for compound requests

### 3.2 What is still architecturally interim

The current master-data route still depends on:

1. `_augment_master_data_lookup_interpretation_from_message(...)`
2. `infer_entity_grains_from_message(message)`
3. `infer_master_data_lookup_slots(message, entity_grain=...)`

inside:

1. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)

Specifically, the current flow can still:

1. infer `entity_grain` from the raw user message after initial interpretation
2. infer `lookup_mode` and `lookup_search_text` after that
3. resolve entity references from that inferred state

This is acceptable as a temporary bridge because it:

1. fails closed
2. respects active entity-reference policy
3. does not invent facts

But it is still not the final seam because:

1. the front door is not yet the authoritative typed source for master-data request shape
2. ambiguity is not yet handled at the earliest possible shared layer
3. future item/product expansion would inherit the same interim pattern if we stop here

## 4. Exact Goal Of This Slice

The goal is:

1. make master-data request shape available as typed front-door output
2. let fresh-query interpretation consume that typed output first
3. keep lexical alias recovery only as bounded fallback
4. move master-data ambiguity to a shared typed front-door clarification seam

In simple terms:

1. the system should know earlier whether the user means customer, supplier, or another master-data grain
2. the system should know earlier whether the user wants:
   - directory list
   - similar-name match
   - detail/profile target
3. if it does not know safely, it should clarify there, not rely on downstream inference

## 5. What We Keep

This slice must reuse current enterprise assets and avoid replacing them.

Keep:

1. Phase A scope backbone registries:
   - `governed_scope_registry.json`
   - `scope_owner_registry.json`
   - `family_scope_compatibility_registry.json`
   - `scope_projection_registry.json`
   - `scope_clarification_registry.json`
2. `master_data_directory` as the shared family path
3. existing capability/report mappings for customer and supplier
4. existing entity-reference policy registry
5. existing clarification framework and continuation behavior
6. current `FreshQueryInterpretationContract`
7. current `FrontDoorIntentGateContract`
8. current `resolve_master_data_lookup_interpretation(...)` path

Important:

This slice should not create:

1. a new master-data runtime lane
2. a second navigation pipeline
3. a prompt-led fallback router

## 6. What Changes

### 6.1 New typed assessment at the front door

Add a typed front-door assessment object for master-data requests.

Recommended contract:

`MasterDataFrontDoorAssessmentContract`

Minimum fields:

1. `request_id`
2. `status`
   - `resolved`
   - `clarification_required`
   - `unsupported_scope`
   - `not_applicable`
3. `entity_grain`
4. `request_mode`
   - `directory_list`
   - `candidate_resolution`
   - `profile_target`
5. `lookup_projection`
6. `lookup_search_text`
7. `supported_entity_grains`
8. `ambiguity_reason_type`
9. `internal_details`

This is not a parallel family contract.
It is a typed pre-interpretation assessment that feeds the existing family path.

### 6.2 Front-door ambiguity handling for master-data grain

Add shared front-door clarification behavior for cases like:

1. `give me some names`
2. `do we have a name similar to Nay Lin Mobile`
3. `tell me more about that record`
   only when no valid grounded deictic reference exists

The front door should clarify:

1. which master-data group the user means
2. only from active or clarification-visible grains

Examples of user-facing clarification shape:

1. `Do you want customers or suppliers?`
2. `I can help with customer or supplier names. Which one would you like?`

This should be typed clarification, not a raw phrase repair.

### 6.3 Fresh-query interpreter must consume typed front-door assessment first

When a valid master-data front-door assessment exists:

1. `fresh_query_interpreter` should use it as the primary source for:
   - `entity_grain`
   - `lookup_mode`
   - `lookup_projection`
   - `lookup_search_text`
2. semantic resolution should continue from that typed state
3. `_augment_master_data_lookup_interpretation_from_message(...)` should only run as fallback if no typed front-door master-data assessment is present

### 6.4 Alias inference becomes bounded fallback only

The current inference helper may remain temporarily, but only under these rules:

1. no front-door master-data assessment exists
2. it still respects active entity-reference policy
3. it still fails closed
4. it is clearly marked as interim fallback in code comments and design docs

This slice should not fully remove alias inference yet.
It should demote it from primary architecture to temporary fallback.

## 7. Detailed Design Shape

### 7.1 Front-door layer

Extend the front-door layer to support a new typed master-data assessment step before normal route-onward behavior.

Recommended seam:

1. add a small helper module for master-data front-door assessment
2. invoke it inside the front-door evaluation path
3. if the assessment says `clarification_required`, front door handles it
4. if the assessment says `resolved`, front door attaches the typed assessment payload and routes onward
5. if the assessment says `not_applicable`, normal flow continues unchanged

### 7.2 Front-door intent registry

Only add new front-door intent entries if necessary for conversational ownership.

Recommended minimal rule:

1. use a front-door clarification intent only when ambiguity must be surfaced to the user
2. do not create a new front-door intent for every resolved master-data request
3. resolved master-data requests should still route onward through the main governed family path

### 7.3 Contracts layer

Extend [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py) with:

1. `MasterDataFrontDoorAssessmentContract`
2. builder helper
3. payload serializer

This should sit alongside:

1. `FrontDoorIntentGateContract`
2. clarification contracts
3. `FreshQueryInterpretationContract`

### 7.4 Clarification translation

Add typed clarification translation support for master-data grain ambiguity.

Do not:

1. hardcode many grain labels inline in multiple places
2. add separate one-off wording paths per family

Use existing entity-grain display metadata where possible.

### 7.5 Fresh-query interpretation

Refactor `fresh_query_interpreter.py` so that:

1. typed master-data front-door payload is checked first
2. semantic interpretation is augmented from typed payload
3. current message-based inference is fallback only

Important:

The review finding specifically points to [fresh_query_interpreter.py:1121](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py:1121).

That block should remain only as bridge logic after this slice, not as the primary master-data activation seam.

## 8. Scope Boundaries For This Slice

### 8.1 In scope

1. customer master-data front-door typed resolution
2. supplier master-data front-door typed resolution
3. grain ambiguity clarification between currently active master-data grains
4. integration of typed assessment into fresh-query interpretation
5. fallback demotion of lexical inference

### 8.2 Not in scope

1. item/product activation
2. item/product ownership decision
3. broad multi-step execution
4. removal of all lexical helpers across the whole codebase
5. broad rewording of all clarification text
6. broad response naturalness cleanup

## 9. Acceptance Criteria

This slice is complete only if:

1. customer and supplier master-data requests can be typed at the front door before fresh-query lexical augmentation
2. ambiguous master-data requests clarify at the front door through typed continuation
3. `fresh_query_interpreter` no longer depends primarily on message alias inference for active master-data grains
4. the current alias-recovery seam is still available only as bounded fallback
5. no new parallel master-data path is introduced
6. current customer and supplier behavior does not regress

## 10. Verification Plan

### 10.1 Contract and unit verification

Add narrow tests for:

1. front-door master-data assessment returns `resolved` for:
   - `give me some customer list`
   - `give me some supplier list`
2. front-door master-data assessment returns `clarification_required` for:
   - `give me some names`
   - `do u have name similar to Nay Lin Mobile`
   if grain is not explicit
3. fresh-query interpretation consumes typed front-door assessment before fallback inference
4. fallback inference still works only when typed assessment is absent

### 10.2 Behavior verification

Recommended manual checks:

1. `give me some customer list`
2. `give me some supplier list`
3. `do u have supplier name similar to "Myanmar Tech Import"`
4. `do u have customer name similar to "Nay Lin Mobile"`
5. ambiguous request:
   - `give me some names`
6. ambiguous near-match request:
   - `do u have a name similar to "Nay Lin Mobile"`

Expected:

1. explicit grain requests resolve directly
2. ambiguous grain requests clarify early
3. no unsupported scope silently collapses into another active grain

## 11. Risks To Avoid

Do not do these:

1. add more phrase-specific branches into `fresh_query_interpreter.py`
2. move raw aliases from code into a different phrase list and call it done
3. create a second master-data router outside the shared family path
4. auto-activate item/product grain in the same slice
5. let front door over-own the request and bypass the normal family pipeline

## 12. Recommended Execution Order

Implement in this order:

1. design and add `MasterDataFrontDoorAssessmentContract`
2. add front-door assessment helper
3. wire front-door clarification for ambiguous master-data grain
4. pass typed assessment into the existing fresh-query path
5. demote `_augment_master_data_lookup_interpretation_from_message(...)` to fallback semantics
6. add focused tests
7. verify customer and supplier regression behavior

## 13. What Comes Next After This Slice

After this slice, the next correct roadmap step should be:

1. `E1.3 item/product ownership decision`
2. `E1.4 item/product activation`

Why:

1. the front-door master-data seam will then be strong enough to absorb a new grain cleanly
2. item/product expansion will not need to repeat the current interim alias pattern

## 14. Final Direction

The right next implementation move is not another isolated scope activation.

It is:

1. strengthen the shared front-door master-data contract seam
2. reduce interim lexical ownership
3. keep the current customer/supplier success path
4. prepare the system for the next safe grain expansion

That is the clean enterprise answer to the current review finding.
