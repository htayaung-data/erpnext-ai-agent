# Qwen ERP Contracts Mini-phase 1 Inventory (2026-03-25)

Status: active contract-inventory checkpoint  
Scope: inventory current runtime pieces related to `ArtifactContinuationContract`, `GovernedScopeDecisionContract`, and `ClarificationReasonContract` before deeper contract cutover  
Decision: keep reusable contract-adjacent building blocks, retire split authority gradually, and do not add new phrase-driven fixes during contract migration

## 1. Executive Decision

Mini-phase 1 exists to answer one question before more runtime cutover:

Which current pieces should be integrated into the three-contract architecture, and which current pieces should be treated as transitional logic to retire?

The answer is:

1. keep the current contract and metadata building blocks that already express structured business state
2. keep current runtime behavior only as transitional fallback where contract authority is not complete
3. do not start deleting broad old paths until the matching contract becomes authoritative in that area
4. do not add more keyword-style logic in Python or JSON while this migration is underway

## 2. Enterprise Rule For This Mini-phase

This mini-phase must preserve the Phase 5 guardrails:

1. no phrase-heavy Python interpretation as the primary architecture
2. no token-bag registries masquerading as enterprise metadata
3. contracts must become decision authorities
4. service must become orchestration, not business interpretation

## 3. Current Inventory Summary

The current codebase already contains several nearby pieces, but authority is still split.

### 3.1 Current building blocks that already exist

1. `ArtifactContinuationContract` exists in `qwen_chat/contracts.py`
2. `FollowUpResolution` exists in `qwen_chat/contracts.py`
3. `ClarificationSignalContract` exists in `qwen_chat/contracts.py`
4. `clarification_reason_type` already exists in compiler output in `qwen_chat/compiler.py`
5. `translate_clarification_signal(...)` exists in `qwen_chat/clarification_translation.py`
6. metadata registries already exist for ontology, capabilities, families, and canonical aliases

### 3.2 Current split-authority problem

The current runtime still spreads authority across:

1. `contracts.py`
2. `service.py`
3. `followup_interpreter.py`
4. `compiler.py`
5. `clarification_translation.py`

This means the branch currently has:

1. partial contract surfaces
2. partial contract consumption
3. old fallback logic still making real decisions in parallel

That split authority is the main reason follow-up behavior can still drift.

## 4. Contract-by-Contract Inventory

### 4.1 Contract 1: `ArtifactContinuationContract`

Current state:

1. implemented in `qwen_chat/contracts.py`
2. built from grounded turn + normalized family artifact + `FollowUpResolution`
3. already threaded into `qwen_chat/service.py`
4. already used by capability requery message compilation

Current strengths:

1. captures source artifact family, capability, report, dimension, metric, limit, sort, and time scope
2. captures preserved continuation scope
3. captures ranked-membership preservation intent
4. captures whether the current turn should preserve grounded context

Current gaps:

1. it is not yet the sole authority for continuation decisions
2. service still has parallel continuation logic and context-isolation overrides
3. local follow-up and requery branches can still compete with contract preservation

Mini-phase 1 decision:

1. keep the current contract class
2. keep the current builder
3. treat service-level continuation re-guessing as transitional logic to retire in later slices

### 4.2 Contract 2: `GovernedScopeDecisionContract`

Current state:

1. no explicit class exists yet
2. closest current pieces are:
   - `FollowUpResolution`
   - `assess_context_isolation(...)`
   - several service-level branches deciding `new_query`, `capability_requery`, `local_grounded_transform`, and out-of-scope behavior

Current strengths:

1. the runtime already exposes the four major practical outcomes:
   - local continuation
   - governed requery
   - fresh query
   - out-of-scope fallback
2. these outcomes are already wired into service orchestration paths

Current gaps:

1. there is no first-class structured scope-decision contract yet
2. decision authority is still spread across interpreter, service, and compiler
3. clarification is not yet a first-class governed scope outcome for follow-up turns

Mini-phase 1 decision:

1. keep `FollowUpResolution` as a transitional ancestor, not the final replacement
2. keep `assess_context_isolation(...)` only as transitional scope input
3. design Contract 2 so it becomes the explicit authority for:
   - local continuation
   - governed requery
   - clarify
   - fresh query
   - governed out-of-scope

### 4.3 Contract 3: `ClarificationReasonContract`

Current state:

1. no explicit class exists yet
2. closest current pieces are:
   - `ClarificationSignalContract`
   - compiler `clarification_reason_type`
   - `translate_clarification_signal(...)`

Current strengths:

1. compiler already emits structured reason-type hints
2. translation layer already converts structured reasons into business-language clarification prompts
3. user-facing clarification no longer needs to rely entirely on raw failure text

Current gaps:

1. clarification reasons are not yet unified across fresh-query and follow-up paths
2. family/service validation can still generate clarification behavior indirectly
3. there is no dedicated contract describing clarification cause, missing slot, blocking severity, or recommended choices

Mini-phase 1 decision:

1. keep `ClarificationSignalContract` as the user-facing presentation contract
2. introduce `ClarificationReasonContract` later as the upstream reason authority
3. make translation consume the reason contract instead of mixed compiler/service payloads

## 5. Integration Map

### 5.1 Keep and integrate

These pieces are already aligned enough to keep:

1. `ArtifactContinuationContract`
2. `ClarificationSignalContract`
3. compiler `clarification_reason_type`
4. metadata registries:
   - `business_ontology.json`
   - `semantic_alias_registry.json`
   - `capability_registry.json`
   - `report_family_registry.json`
5. `translate_clarification_signal(...)` as a downstream wording layer

### 5.2 Transitional pieces to retain for now

These should stay temporarily, but only until the matching contract becomes authoritative:

1. `FollowUpResolution`
2. `assess_context_isolation(...)`
3. service-level requery upgrade branches
4. service-level fresh-query breakout overrides
5. follow-up interpreter compatibility fallbacks

### 5.3 Transitional pieces to retire later

These should not survive as final decision authorities:

1. ad hoc continuation re-guessing in `service.py`
2. split scope decisions between service and follow-up interpreter
3. clarification creation from mixed validation branches
4. phrase-driven fallback behavior where a contract or canonical registry should decide

## 6. Ownership Boundaries Going Forward

### 6.1 `ArtifactContinuationContract` must own

1. what must be preserved from the prior grounded artifact
2. preserved metric, dimension, limit, sort, and date context
3. ranked membership and order preservation intent
4. whether the next step is a true continuation at all

### 6.2 `GovernedScopeDecisionContract` must own

1. whether the turn should:
   - continue locally
   - continue by governed requery
   - clarify
   - break out as fresh query
   - fall out as governed out-of-scope
2. why that decision was chosen
3. what contract inputs were considered

### 6.3 `ClarificationReasonContract` must own

1. why clarification is required
2. what slot or business choice is missing
3. whether clarification is blocking
4. which suggested business-safe options may be shown to the user

## 7. Runtime Areas To Touch In Later Slices

### 7.1 Primary migration files

1. `qwen_chat/contracts.py`
2. `qwen_chat/service.py`
3. `qwen_chat/followup_interpreter.py`
4. `qwen_chat/compiler.py`
5. `qwen_chat/clarification_translation.py`

### 7.2 Supporting files

1. `qwen_chat/fresh_query_interpreter.py`
2. `qwen_chat/family_followup.py`
3. `qwen_chat/metadata.py`
4. enterprise metadata registries in `impl_factory/03_config/qwen_enterprise_metadata/`

## 8. Acceptance For Mini-phase 1

Mini-phase 1 is complete when:

1. the branch has a written integration/retirement map
2. current contract-adjacent pieces are clearly classified as:
   - keep
   - transitional
   - retire later
3. the next contract slice can proceed without adding more split-authority logic

## 9. Immediate Next Step

Proceed to Mini-phase 2:

1. finish `ArtifactContinuationContract` as the full authoritative data model
2. remove continuation ambiguity about what must be preserved
3. then begin the authoritative cutover in service orchestration

## 10. Explicit Non-Goals For This Mini-phase

This mini-phase does not:

1. introduce new keyword logic
2. add a front-door conversational gate yet
3. solve quantity-enrichment behavior yet
4. delete broad old runtime logic before the replacement contract is authoritative
