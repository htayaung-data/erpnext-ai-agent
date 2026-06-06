# Qwen ERP AI Assistant - V1-IB-0-C Proposal Completeness Constraint Addendum

Date: 2026-05-27

Decision target: v1_ib_0_c_proposal_completeness_constraint_addendum_ready_for_owner_qa_review

Owner: Architecture Agent

Implementation owner after approval: Development Agent

Verification owner: QA_Risk Auditor

Status: Architecture constraint addendum only. No source implementation is approved by this document.

## 1. Purpose

QA_Risk conditionally accepted V1-IB-0-B, the two-model intent-boundary authority amendment.

This addendum records the required V1-IB-A constraints from QA before Development starts implementation.

The added constraint is serious: a lightweight model can omit an unsafe clause. If the validator only validates the proposed clauses, the proposal may look internally consistent while still being incomplete and unsafe.

Therefore V1-IB-A must include proposal-completeness validation and a formal definition of strict deterministic safe subset.

## 2. Accepted Architecture Context

The accepted V1-IB direction remains:

- stop the V1-R-Y lexical patch stream as release architecture
- every user turn must produce one validated IntentBoundaryContract
- lightweight model proposes structured intent only
- deterministic contract validator authorizes route permissions
- enterprise model answers only after contract permission
- semantic/model output can restrict but never authorize
- fail closed on missing, malformed, low-confidence, contradictory, ambiguous, or incomplete output
- words are evidence; contracts are authority

This addendum does not replace V1-IB-0 or V1-IB-0-B. It tightens V1-IB-A implementation requirements.

## 3. Core New Risk: Omission By Proposal

Example user message:

Show item sales and tell me whether to reprice it.

A weak lightweight model could propose only:

- Clause 1: factual item sales lookup

If the validator checks only that proposed clause, the contract could falsely appear safe.

That is not acceptable. A model omission must not become hidden route authority.

The validator must compare the proposal against the normalized raw message and fail closed if any meaningful residual text, connector, pronoun, target, decision signal, action signal, or domain signal is unaccounted for.

## 4. Required Proposal-Completeness Validation

V1-IB-A must define and test proposal-completeness validation.

The validator must verify:

- every material span of the normalized raw message is accounted for by a clause, target, connector, or explicitly ignored safe filler
- clause_count matches the proposed clauses
- proposed clauses preserve the order and coverage of the raw message
- unresolved residual text prevents report eligibility
- unaccounted decision markers prevent report eligibility
- unaccounted advice markers prevent report eligibility
- unaccounted business action markers prevent report eligibility
- unaccounted policy, legal, prediction, manipulation, mutation, approval, pricing, payment, retention, report-hiding, or accounting-adjustment domain evidence prevents report eligibility
- conjunctions and connectors that introduce a second intent must be represented by a clause or fail closed
- pronouns after ERP targets must be resolved to a target or fail closed
- safe factual clause plus unresolved residual text cannot route as governed ERP answer
- partial proposal status cannot route as governed ERP answer
- low-confidence proposal status cannot route as governed ERP answer
- contradiction between raw-message evidence and proposed contract prevents report eligibility

## 5. Required Connector Coverage

V1-IB-A must treat these as examples of residual second-intent connectors that require clause coverage or fail closed:

- and tell me whether
- and tell me if
- and decide whether
- and decide if
- and say whether
- and say if
- and advise whether
- and recommend whether
- and what should we do
- and should we
- then tell me whether
- also tell me whether

This list is not the final design authority. It is a test set for the structural concept: connectors introducing a second decision, advice, action, or policy intent must not be ignored.

## 6. Required Residual-Text Rule

V1-IB-A must define a residual-text model.

At minimum, the validator must distinguish:

- accounted factual text
- accounted unsafe or ambiguous text
- safe filler text
- unaccounted residual text

If residual text contains or may contain a second intent, the contract must fail closed.

If residual text is non-empty and cannot be classified as safe filler, the contract must not be report-eligible.

Safe filler must be narrowly defined and tested. It must not include decision, advice, action, policy, legal, prediction, manipulation, mutation, or ambiguous business language.

## 7. Required Pronoun And Reference Rule

V1-IB-A must define pronoun and reference completeness.

If a user mentions an ERP target and later uses a pronoun or this/that reference in a second clause, the validator must require one of these outcomes:

- resolved to an explicit target with a safe read-only intent
- resolved to an explicit target with unsafe or mixed intent and therefore blocked
- unresolved and therefore clarification or boundary

A pronoun after an ERP target must not silently disappear from the proposal.

## 8. Strict Deterministic Safe Subset Definition

V1-IB-A must formally define strict deterministic safe subset.

It means only a request where all of these are true:

- no decision intent
- no advice intent
- no business action intent
- no policy-boundary intent
- no legal or regulatory advice intent
- no prediction, score, or future-cause intent
- no manipulation or report-hiding intent
- no write, mutation, workflow, approval, or accounting-adjustment intent
- no unsupported business recommendation intent
- no unresolved residual clause
- no mixed intent
- no visible-context ambiguity
- no unresolved pronoun or this/that reference
- no unsafe domain evidence
- all target schemas are valid
- all clause coverage checks pass
- all contract invariants pass
- trace_redaction_status is safe

Strict deterministic safe subset must not become the old lexical shortcut under a new name.

It is a narrow fallback path for obviously safe, fully covered, read-only factual ERP requests only.

## 9. Required V1-IB-A Pure Tests

V1-IB-A must include pure schema and validator tests proving:

- complete safe factual proposal can validate as report-eligible
- mixed factual plus unsafe proposal validates only as boundary or clarification
- proposed factual-only clause with residual unsafe text fails closed
- unaccounted connector such as and tell me whether fails closed
- unaccounted decision/action/advice marker fails closed
- unaccounted pricing/payment/retention/mutation/legal/prediction/manipulation domain evidence fails closed
- unresolved pronoun after ERP target fails closed
- partial proposal fails closed
- low-confidence proposal fails closed
- contradictory proposal fails closed
- malformed proposal fails closed
- missing proposal fails closed unless strict deterministic safe subset is fully proven
- semantic safe output cannot override deterministic unsafe
- semantic unsafe or ambiguous output can restrict routing
- enterprise model reasoning cannot be allowed without validated contract authority
- final emission cannot be allowed without validated contract authority

## 10. Development Boundary

If QA accepts this addendum, Development may start only V1-IB-A.

V1-IB-A scope is updated to include:

- contract schema
- typed enums
- clause schema
- ontology schema
- model-proposal fields
- deterministic validator fields
- proposal-completeness validation
- residual-text model
- connector coverage model
- pronoun/reference completeness model
- strict deterministic safe-subset definition
- redaction-safe trace field definitions
- pure validation tests

V1-IB-A must not include:

- runtime routing
- visible-context wiring
- final-emission changes
- model endpoint changes
- browser or API UAT
- staging
- commit
- push
- deployment
- strict enforcement
- V2 work

## 11. Technical Notes To QA_Risk Auditor

Please independently review whether this addendum closes the omission-by-proposal risk.

The key review question is: can a lightweight model omit the unsafe part of a user message and still produce a report-eligible contract?

QA should reject V1-IB-A later if:

- the validator only validates proposed clauses without checking raw-message completeness
- residual text can be ignored without proof it is safe filler
- connectors introducing second intents can be dropped
- pronouns after ERP targets can disappear
- low-confidence or partial proposals can route as factual
- strict deterministic safe subset is vague or permissive
- the implementation returns to synonym patching as the route authority

## 12. Final Position

V1-IB-0-C makes proposal completeness a mandatory enterprise safety invariant.

The lightweight model may propose, but omission cannot authorize.

The validator must prove the proposal covers the raw user message before any safe factual route is allowed.
