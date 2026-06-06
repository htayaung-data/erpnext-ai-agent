# V1-IB-A Contract Schema / Validator / Clause Model / Ontology

Date: 2026-05-28

Decision target: `v1_ib_a_contract_schema_validator_clause_model_ontology_ready_for_counterpart_qa_review`

## Scope

V1-IB-A implements a pure contract-first intent boundary layer. It does not wire into runtime routing, visible context, final emission, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work.

Binding authority documents:

- `qwen_erp_v1_ib_0_enterprise_intent_boundary_rebuild_architecture_plan_2026-05-27.md`
- `qwen_erp_v1_ib_0_a_formal_report_integrity_fix_2026-05-27.md`
- `qwen_erp_v1_ib_0_b_two_model_intent_boundary_authority_amendment_2026-05-27.md`
- `qwen_erp_v1_ib_0_c_proposal_completeness_constraint_addendum_2026-05-27.md`

## Implemented Deliverables

New pure module:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py`

New pure tests:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_contract_validator.py`

## Contract Schema

The typed `IntentBoundaryContract` preserves the required concepts:

- `contract_version`
- `raw_message_hash`
- `normalized_message_hash`
- `clause_count`
- `clauses`
- `erp_targets`
- `visible_context_references`
- `factual_lookup_intent`
- `safe_followup_intent`
- `decision_intent`
- `advice_intent`
- `business_action_intent`
- `policy_boundary_intent`
- `mixed_intent_detected`
- `business_action_domain`
- `policy_domain`
- `ambiguity_status`
- `report_routing_allowed`
- `context_reuse_allowed`
- `model_reasoning_allowed`
- `final_emission_allowed`
- `required_answer_mode`
- `boundary_reason`
- `validator_status`
- `trace_redaction_status`
- `intent_proposer_role`
- `intent_proposer_status`
- `intent_proposer_confidence`
- `intent_proposer_model_name`
- `intent_proposer_output_status`
- `deterministic_validator_status`
- `deterministic_validator_errors`
- `semantic_backstop_status`
- `semantic_backstop_effect`
- `authority_source`
- `authority_decision`
- `authority_blocking_reason`

Additional pure validation fields:

- `residual_text_status`
- `residual_text_segments`
- `connector_coverage_status`
- `pronoun_reference_status`
- `strict_deterministic_safe_subset_status`

## Clause / Target / Reference Models

Clause schema includes:

- clause id, index, span, redaction-safe text hash
- clause type
- ERP target ids
- visible-context reference ids
- factual, follow-up, decision, advice, business-action, and policy-boundary intent flags
- business and policy domain values
- ambiguity status

ERP target schema includes:

- target id
- target type
- redaction-safe value hash
- schema status
- trace redaction status

Visible-context reference schema includes:

- reference id
- reference type
- resolution status
- resolved target id, if any
- read-only intent status

## Ontology Domains

The typed ontology contains the required domain values:

- `pricing_valuation_action`
- `customer_supplier_retention_admission`
- `product_catalog_lifecycle`
- `inventory_stocking_disposal`
- `payment_delay_withholding_release`
- `report_hiding_or_manipulation`
- `accounting_writeoff_adjustment`
- `record_mutation_or_workflow_action`
- `prediction_score_or_future_cause`
- `legal_or_regulatory_advice`
- `unsupported_business_recommendation`

Each domain has a typed definition containing target types, route family, unsafe-for-report-routing status, and a short description.

## Proposal-Completeness Validation

The deterministic validator compares the lightweight proposal against the normalized raw message. It does not validate only the proposed safe clause.

Validation includes:

- required proposal fields
- clause count matching actual clauses
- clause order
- clause span validity against normalized raw message
- clause text/span consistency
- residual text computation
- residual non-filler blocking
- connector coverage through residual coverage
- target schema validation
- visible-context reference validation
- unresolved pronoun/reference blocking
- low-confidence and partial proposal blocking
- contradictory proposal blocking
- trace redaction safety

If a factual-only proposal omits an unsafe second clause, the uncovered raw-message residual blocks report routing.

## Strict Deterministic Safe Subset

The strict deterministic safe subset is defined narrowly through `strict_deterministic_safe_subset_definition()`.

It requires:

- no decision intent
- no advice intent
- no business action intent
- no policy-boundary intent
- no legal/regulatory advice intent
- no prediction/score/future-cause intent
- no manipulation/report-hiding intent
- no write/mutation/workflow intent
- no unsupported business recommendation intent
- no unresolved residual clause
- no mixed intent
- no visible-context ambiguity
- no unresolved pronoun/reference
- no unsafe domain evidence
- valid target schema
- complete clause coverage
- valid contract invariants
- safe trace redaction

Missing model proposal fails closed unless this strict proof object is complete and internally valid.

## Two-Model Authority

The lightweight model is represented only as proposal metadata:

- role
- status
- confidence
- model name
- output status

The deterministic validator is the authority source. Semantic/model output may restrict routing but cannot authorize ERP answers:

- deterministic unsafe plus semantic safe remains unsafe
- deterministic safe plus semantic unsafe/ambiguous becomes clarification/restricted
- missing/malformed proposal fails closed unless strict deterministic safe subset is proven
- enterprise model reasoning is allowed only when validated contract authority permits governed ERP answer mode
- final emission is disallowed for invalid contracts and allowed only for validated governed, boundary, or clarification contracts

## Test Coverage

Pure tests prove:

- complete safe factual proposal validates as report-eligible
- mixed factual plus unsafe proposal validates only as boundary
- factual-only proposal with residual unsafe text fails closed
- unaccounted connectors fail closed
- unaccounted pricing, payment, retention, mutation, legal, prediction, and manipulation evidence fails closed
- unresolved pronoun after ERP target fails closed
- partial proposal fails closed
- low-confidence proposal fails closed
- contradictory proposal fails closed
- malformed proposal fails closed
- missing proposal fails closed unless strict deterministic safe subset is fully proven
- semantic safe cannot override deterministic unsafe
- semantic unsafe/ambiguous can restrict routing
- enterprise model reasoning cannot be allowed without validated contract authority
- final emission cannot be allowed without validated contract authority
- redaction-safe trace payloads use hashes rather than raw clause text or raw target values

## Verification

Verification completed on `/tmp/erpai_pr5_postmerge_verify`.

- V1-IB-A pure tests: PASS, `12 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Runtime raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: clean
- Staged files: `0`

## Decision

`v1_ib_a_contract_schema_validator_clause_model_ontology_ready_for_counterpart_qa_review`
