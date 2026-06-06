# Qwen ERP AI Assistant - V1-IB-0-B Two-Model Intent Boundary Authority Amendment

Date: 2026-05-27

Decision target: v1_ib_0_b_two_model_intent_boundary_authority_amendment_ready_for_owner_qa_review

Owner: Architecture Agent

Implementation owner after approval: Development Agent

Verification owner: QA_Risk Auditor

Status: Architecture amendment only. No source implementation is approved by this document.

## 1. Purpose

QA_Risk accepted V1-IB-0-A as the corrected formal architecture direction for the Enterprise Intent Boundary rebuild.

Before Development starts V1-IB-A, this amendment clarifies one critical architecture point: the project already has a two-model design, and V1-IB must encode that design explicitly.

The intended model split is:

- Lightweight model: intent, clause, ambiguity, target, and safety interpretation proposer.
- Enterprise model: governed ERP answer and business reasoning renderer only after the boundary contract allows it.

This amendment prevents Development from interpreting V1-IB as either a deterministic keyword classifier or an unconstrained model-judgment system.

## 2. Leadership Position

The V1-R-Y through V1-R-Y-Z5 lexical patch stream remains stopped as a release path.

The two-model design is accepted only with strict authority separation:

- The lightweight model may propose structured intent.
- The lightweight model may not authorize report routing by itself.
- The enterprise model may not answer unless the validated IntentBoundaryContract permits it.
- Deterministic validation is required, but it must validate contract invariants and ontology consistency, not become another scattered synonym patch layer.
- Missing, malformed, low-confidence, contradictory, ambiguous, or internally inconsistent model output must fail closed.

The enterprise rule is: words are evidence; contracts are authority.

## 3. Existing Project Evidence

The current project already contains model-role and provenance foundations that support this amendment:

- light_semantic role and metadata bundle support in qwen_chat/light_semantic_metadata.py
- heavy_reasoning role and reasoning provenance support in qwen_chat/reasoning_execution.py
- model roles and lane classes in qwen_chat/runtime_metadata_contract.py
- runtime endpoints for front-door interpretation, follow-up interpretation, fresh-query interpretation, reasoning activation interpretation, repair intent interpretation, and heavy reasoning render in qwen_chat/runtime_client.py
- EC-7F and EC-7G governance evidence stating that semantic metadata is provenance-only and heavy reasoning metadata cannot bypass final-answer authority
- EC-7H planning evidence for controlled light semantic trace collection

This amendment does not claim the existing runtime implementation is sufficient. It only records that V1-IB must align with the intended two-model authority architecture.

## 4. Corrected V1-IB Authority Model

Every user turn must produce one validated IntentBoundaryContract before any downstream route proceeds.

The contract construction pipeline should be:

1. Normalize and pre-process the raw user message.
2. Lightweight model proposes clause segmentation, ERP targets, visible-context references, factual lookup intent, follow-up intent, decision or action intent, ambiguity status, and candidate business or policy domains.
3. Deterministic contract validator checks schema, invariants, domain consistency, route permissions, trace-redaction readiness, and fail-closed conditions.
4. Only a valid contract may authorize report routing, visible-context reuse, model reasoning, or final emission.
5. Enterprise model receives only contract-permitted answer tasks.
6. Final emission reuses the same contract and vetoes any conflicting output.

No lane may independently reinterpret the raw user message after the contract is built.

## 5. Lightweight Model Role

The lightweight model is an interpreter and proposer.

Allowed lightweight model outputs:

- candidate clauses
- candidate ERP targets
- candidate visible-context references
- candidate factual lookup intent
- candidate safe read-only follow-up intent
- candidate decision, advice, action, policy, prediction, legal, manipulation, or mutation intent
- candidate mixed-intent status
- candidate business_action_domain or policy_domain
- confidence, ambiguity, and uncertainty signals
- short redaction-safe rationale for trace evidence

Forbidden lightweight model authority:

- cannot directly allow report routing
- cannot directly allow visible-context reuse
- cannot directly allow enterprise model reasoning
- cannot directly allow final answer emission
- cannot override deterministic unsafe classification
- cannot turn invalid or ambiguous input into a safe ERP answer
- cannot be treated as a final-answer authority source

If the lightweight model is unavailable, low-confidence, contradictory, malformed, or missing required fields, the contract validator must fail closed.

## 6. Deterministic Validator Role

The validator is the route authority layer.

It must validate:

- required contract fields exist
- clause_count matches clauses
- hashes are present and non-empty
- each clause has a type, target list, intent signals, and safety contribution
- ERP targets use allowed target schemas
- visible-context references are explicit and read-only if context reuse is requested
- mixed factual-plus-unsafe intent disables report routing and context reuse
- business or policy domains are consistent with clause evidence
- ambiguity without sufficient safe factual specificity requires clarification
- model_reasoning_allowed cannot be true when report_routing_allowed is false except for boundary or clarification text generation
- final_emission_allowed must match required_answer_mode
- trace_redaction_status must be safe before any trace payload is emitted

The validator must not be a growing phrase patch list. It may use typed ontology definitions, schema invariants, target-type rules, route consistency checks, and fail-closed validation.

## 7. Enterprise Model Role

The enterprise model is the answer and reasoning model.

It may be called only when the validated contract permits:

- report_routing_allowed is true for governed factual report answer paths, or
- required_answer_mode permits boundary or clarification generation, or
- model_reasoning_allowed is true for an approved governed reasoning path.

The enterprise model may not:

- reinterpret unsafe user intent into a factual answer
- override the IntentBoundaryContract
- use visible context unless context_reuse_allowed is true
- answer unsupported business decisions, legal advice, fraud/manipulation, mutation, prediction, or mixed unsafe prompts
- emit selected report rows or business evidence after a boundary veto

## 8. Semantic Backstop Clarification

V1-IB-0 allowed a semantic safety backstop. This amendment clarifies its relationship to the two-model design.

The lightweight model is the semantic proposer. Its output is useful but never authoritative.

Semantic output may only make routing more conservative. Examples:

- deterministic validator says unsafe, semantic says safe: unsafe wins
- deterministic validator says safe, semantic says unsafe: unsafe or clarification wins
- deterministic validator says safe, semantic says ambiguous: clarification wins unless deterministic evidence proves a safe factual-only request
- semantic output missing or invalid: fail closed or use a strictly deterministic safe subset only if all required contract invariants prove safe factual intent

A semantic model must never authorize final ERP answers.

## 9. Example: Mixed Factual Plus Unsafe Decision

User message: Show item sales for EC7H-ITEM-A and tell me whether we should discount it.

Expected lightweight proposal:

- Clause 1: factual ERP lookup for item sales, target EC7H-ITEM-A
- Clause 2: pricing or valuation decision, target EC7H-ITEM-A through pronoun reuse
- mixed_intent_detected: true
- candidate business_action_domain: pricing_valuation_action
- ambiguity_status: none or unsafe_mixed

Expected validator result:

- report_routing_allowed: false
- context_reuse_allowed: false
- model_reasoning_allowed: false except boundary or clarification generation if needed
- final_emission_allowed: true only for boundary or clarification
- required_answer_mode: policy_boundary or clarification
- boundary_reason: mixed_factual_plus_unsupported_pricing_decision

Expected runtime result:

- no item sales report is routed
- no visible-context reuse is activated
- no enterprise model business decision answer is allowed
- assistant emits boundary or clarification
- final veto blocks any later selected-answer payload that conflicts with the contract

Safe neighbor: Show item sales for EC7H-ITEM-A.

Expected result:

- one factual clause
- no decision or action clause
- report_routing_allowed: true
- required_answer_mode: governed_erp_answer

## 10. Relationship To Lexical Signals

This amendment does not require pretending that language systems use no words.

Allowed use of language terms:

- normalization
- clause segmentation evidence
- ERP target detection
- ontology concept evidence
- negation, modality, reference, and target evidence
- adversarial test fixtures
- trace explanation of contract classification

Forbidden use of language terms:

- scattered one-off blockers
- final routing authority
- flat synonym patch piles
- factual lookup authorization before unsafe intent clearance
- hidden route-specific reinterpretation after contract creation
- phrase-only QA closure claims

The mature standard is not zero lexical evidence. The mature standard is no lexical evidence as final authority.

## 11. Required V1-IB-A Additions

V1-IB-A must define schema and pure tests for the two-model authority model.

Required contract additions or explicit fields:

- intent_proposer_role
- intent_proposer_status
- intent_proposer_confidence
- intent_proposer_model_name
- intent_proposer_output_status
- deterministic_validator_status
- deterministic_validator_errors
- semantic_backstop_status
- semantic_backstop_effect
- authority_source
- authority_decision
- authority_blocking_reason

If field names differ, they must preserve these concepts.

Required V1-IB-A tests:

- valid light-model proposal cannot route until validator approves it
- malformed proposal fails closed
- missing proposal fails closed or strict deterministic safe subset only
- low-confidence proposal fails closed
- contradictory proposal fails closed
- mixed factual plus unsafe proposal validates only as boundary or clarification
- semantic safe cannot override deterministic unsafe
- semantic unsafe can override or restrict deterministic safe
- enterprise model reasoning cannot be allowed unless contract permits it
- final emission cannot be allowed without validated contract authority

## 12. Technical Notes To QA_Risk Auditor

This amendment is submitted for independent serious counterpart review before Development starts V1-IB-A.

The review question is not whether two models are a good slogan. The review question is whether the authority split is strict enough for enterprise safety.

Please verify:

- the lightweight model is not granted route authority
- the enterprise model is not allowed to override the boundary contract
- the validator remains the authority layer
- the validator is described as invariant and ontology validation, not keyword patching
- semantic output can only restrict routing, never authorize it
- fail-closed behavior is required for missing, malformed, low-confidence, contradictory, or ambiguous outputs
- V1-IB-A is blocked from runtime wiring and must remain schema, validator, clause model, ontology definitions, and pure tests only

QA should reject this amendment if it allows model judgment to become final authority, if it allows factual lookup to win before unsafe intent clearance, or if it can be interpreted as another synonym patch program.

## 13. Development Boundary After Acceptance

If QA accepts V1-IB-0-B, Development may proceed only to V1-IB-A.

V1-IB-A is limited to:

- contract schema
- typed enums
- clause schema
- ontology schema
- validator invariants
- two-model authority fields
- redaction-safe trace field definitions
- pure tests

V1-IB-A must not include:

- runtime routing
- visible-context wiring
- final-emission changes
- browser or API UAT
- model endpoint changes
- staging
- commit
- push
- deployment
- strict enforcement
- V2 work

## 14. Final Position

The two-model approach is enterprise-appropriate only when the lightweight model proposes and the contract validator disposes.

The enterprise product must never rely on the lightweight model, enterprise model, or lexical terms as unchecked authority.

The required architecture is model-assisted, contract-authorized, fail-closed, traceable, and adversarially tested.
