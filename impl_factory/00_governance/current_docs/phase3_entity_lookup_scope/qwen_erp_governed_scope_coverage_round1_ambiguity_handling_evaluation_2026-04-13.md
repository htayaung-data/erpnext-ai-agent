# Qwen ERP Governed Scope Coverage Round 1 Ambiguity Handling Evaluation

Status: active research note  
Date: 2026-04-13  
Scope: ambiguity and underspecified-question handling across the current ERP AI runtime, with emphasis on Phase `3.3` continuity and later multi-family expansion

## 1. Purpose

This note records a focused evaluation of how the current system handles:

1. ambiguous questions
2. underspecified questions
3. missing basis or missing scope questions
4. follow-up questions whose meaning depends on prior context

The goal is not to design a single-case fix.

The goal is to answer five practical questions:

1. do we already have ambiguity-handling architecture
2. where does it already work
3. where is it uneven or incomplete
4. whether this should be implemented immediately or after broader research
5. how this finding fits into the three-round governed scope research program

## 2. Executive Conclusion

The system already has real ambiguity-handling architecture.

This is an important finding.

The current weakness is not "there is no ambiguity framework."
The current weakness is "ambiguity handling is not yet activated evenly across all seams and families."

That means the correct enterprise decision is:

1. record this now as a shared architecture finding
2. continue the broader research program
3. use later rounds to measure how wide this pattern is across more ERP families
4. design one shared implementation plan after research is complete

The correct next step is not:

1. add special handling for one phrase such as `delivered`
2. add another special handling for one phrase such as `received`
3. widen narrow question-specific branches one by one

That would repeat the exact debt the enterprise rules are trying to avoid.

## 3. Evidence Basis

This note is based on direct inspection of:

1. enterprise governance documents
2. current clarification contracts and translation helpers
3. clarification continuation lane behavior
4. follow-up boundary behavior
5. entity-detail clarification behavior

Primary evidence sources:

1. [qwen_erp_enterprise_development_guidelines_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_enterprise_development_guidelines_2026-04-04.md)
2. [qwen_erp_phase_implementation_roadmap_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase_implementation_roadmap_2026-04-04.md)
3. [qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md)
4. [clarification_translation.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py)
5. [clarification_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py)
6. [lanes/clarification_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py)
7. [ambiguity_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/ambiguity_support.py)
8. [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
9. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)

## 4. What Already Exists

### 4.1 Governance-Level Clarification Policy Already Exists

The current governance docs already require:

1. fail closed when evidence is weak
2. clarify instead of guessing
3. keep follow-up meaning tied to structured evidence
4. avoid converting ambiguity into fabricated confidence

This means ambiguity handling is already part of the approved enterprise direction.

### 4.2 Compiler-Level Clarification Already Exists

The runtime already supports typed clarification reasons such as:

1. `capability_ambiguity`
2. `report_ambiguity`
3. `time_scope_missing`
4. `filter_missing`
5. `capability_missing`
6. `request_underspecified`

These are translated into user-facing clarification prompts in [clarification_translation.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_translation.py).

This is a real shared seam, not a prompt trick.

### 4.3 Pending Clarification Continuation Already Exists

The system already stores pending clarification state and can:

1. repeat the clarification
2. interpret the user's selected option
3. continue the correct lane
4. stop after bounded retry limits

This lives in:

1. [clarification_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py)
2. [lanes/clarification_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/clarification_lane.py)

This is important because it means the continuation engine does not need to be reinvented.

### 4.4 Follow-Up Boundary Ambiguity Control Already Exists

The system already has follow-up boundary logic that decides whether a follow-up should:

1. stay on the current grounded context
2. force a fresh query
3. fail closed to reasoning

That is already part of the shared runtime boundary design in [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py).

This means ambiguity control is not only a front-door feature.
It already exists in continuation behavior too.

### 4.5 Artifact-Boundary Clarification Already Exists, But Narrowly

The entity-detail evidence layer already has typed clarification for some cases, including:

1. missing customer tenure basis
2. missing customer operational document basis

Those are defined in [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py).

This proves the architecture already supports clarification below the compiler layer as well.

## 5. What Is Incomplete

### 5.1 Clarification Types Are Uneven Across Seams

The current clarification system is strongest at:

1. compiler/front-door ambiguity
2. some family-level clarification
3. some follow-up boundary decisions

It is weaker at:

1. entity-detail ambiguity
2. event-date ambiguity
3. cross-family deictic ambiguity
4. missing operational target ambiguity
5. artifact-boundary questions that are valid in business language but not yet represented by shared typed ambiguity classes

### 5.2 Some Clarification Reasons Are Too Narrow

The current entity-detail clarification reasons are useful, but they are narrow and customer-weighted.

Examples:

1. `customer_tenure_basis_missing`
2. `customer_operational_document_missing`

These solve a real need, but they do not yet form a reusable ambiguity taxonomy that can cover many unseen questions across many families.

### 5.3 The Main Gap Is Activation And Generalization

The system already knows how to clarify.

What it does not yet do consistently is:

1. detect the same class of ambiguity across different families
2. express that ambiguity using a shared typed reason
3. route that typed reason through the same clarification engine
4. present a business-natural prompt that reflects the real ambiguity type

This is why some questions get a good clarification while others still:

1. fall through to a generic stop
2. receive a clarification that is too broad
3. receive a clarification that feels technically valid but business-unnatural

## 6. Architectural Interpretation

This research finding should be interpreted as:

1. a shared architecture gap
2. not a single-family bug
3. not proof that the current clarification framework is wrong
4. proof that the framework needs wider and more consistent activation

The system does not need a brand-new ambiguity engine.

The system needs a stronger shared ambiguity taxonomy and broader typed activation.

## 7. Recommended Shared Design Direction

The recommended direction is to extend the existing clarification system, not replace it.

That future design should likely introduce a more reusable ambiguity taxonomy across families, including classes such as:

1. missing time scope
2. missing entity scope
3. missing metric basis
4. missing document basis
5. missing event target
6. ambiguous reference
7. ambiguous business area
8. unsupported-in-current-family

These labels are design placeholders in this note, not yet approved implementation names.

The key design rule is:

1. metadata and typed contracts should identify the ambiguity class
2. translation helpers should render the business-natural clarification question
3. the existing pending clarification engine should continue to own the continuation flow

This keeps the architecture aligned with enterprise policy:

1. contract first
2. runtime second
3. fail closed on weak evidence
4. no raw-phrase rescue logic

## 8. What We Should Not Do

This note explicitly recommends against:

1. implementing one branch for `delivered`
2. implementing one branch for `received`
3. solving unseen ambiguity by extending a phrase list
4. widening customer-only clarification logic as the default expansion path
5. introducing a second clarification engine beside the one already present

Those paths may produce short-term improvement, but they do not satisfy the project's enterprise constraints.

## 9. Relation To The Three-Round Research Program

This ambiguity-handling evaluation is not a separate workstream.

It is one direct finding from the current governed scope research program.

That means:

1. Round 1 has already exposed a shared ambiguity activation issue
2. Round 2 should test how far this pattern extends across more ERP families and scopes
3. Round 3 should help define which ambiguity classes become shared implementation work, which stay deferred, and which are already solved elsewhere

So this note should be treated as:

1. a recorded research finding now
2. an input into later implementation planning
3. not yet a full implementation decision across the whole runtime

## 10. Practical Decision For Now

The correct practical decision at this stage is:

1. record this finding now
2. continue Round 2 and Round 3 research
3. build the implementation plan only after broader coverage is known

Reason:

If implementation starts now at full-system scope, the ambiguity model may be shaped too heavily by the few cases already seen in Round 1.

That would risk another partial design instead of a true shared seam.

## 11. Implementation Planning Trigger

This ambiguity finding should become active implementation planning work after:

1. Round 2 confirms how this appears across more families
2. Round 3 confirms the safe shared abstraction boundary
3. the final implementation plan can group ambiguity work into:
   1. metadata changes
   2. typed contract changes
   3. translation changes
   4. family activation changes
   5. regression coverage

## 12. Current Status Statement

Current status:

1. the project already has a strong ambiguity foundation
2. the weakness is uneven activation, not total absence
3. this should be treated as a shared architecture design item
4. it should be implemented after broader research, not rushed as a phrase-level patch
