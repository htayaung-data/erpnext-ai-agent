# Comparison Class Strict Implementation Contract

Date: 2026-03-07  
Owner: AI Runtime Engineering  
Scope: mandatory execution contract for the next behavioral-class expansion (`comparison`) in Phase 3  
Status: active for next-class implementation

## Purpose
This note defines strict implementation discipline for the `comparison` class so work stays inside enterprise contract boundaries and avoids previous wrong-direction failure patterns.

This contract is binding for design, coding, verification, and closure of the `comparison` first slice.

## Governing References

1. [step13_behavioral_class_development_contract.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_behavioral_class_development_contract.md)
2. [step14_phase3_regression_discipline_contract.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_phase3_regression_discipline_contract.md)
3. [step15_behavioral_class_expansion_approval_review_template.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step15_behavioral_class_expansion_approval_review_template.md)
4. [step21_spec_pipeline_contract_hardening_status_2026-03-06.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step21_spec_pipeline_contract_hardening_status_2026-03-06.md)

## First-Slice Scope Boundary (Approved)

### In Scope

1. Same-period comparison only (single period such as `last month`).
2. Entity-vs-entity comparison inside the same period.
3. Deterministic comparison routing through ontology + metadata + class contract.

### Out Of Scope (Must Return Clarification/Unsupported)

1. Cross-period comparison (for example `this month vs last month`, `month-over-month`).
2. Forecasting or trend decomposition.
3. New follow-up style expansions not listed in approved variation matrix.

## Non-Negotiable Boundaries

1. No prompt-to-report runtime maps.
2. No case-ID logic in runtime.
3. No keyword-driven business routing in runtime modules.
4. No hidden fallback that cannot be explained by contract/ontology/metadata/state.
5. No informal scope widening during implementation.

## Strict Change-Control Rules

1. Before edits, run `git status` and record:
   - already dirty files
   - proposed in-scope files
   - excluded files
2. Edit only approved in-scope files.
3. If any out-of-scope file is required, stop and request approval first.
4. Use `apply_patch` for every manual code edit.
5. Keep patch batches small and single-purpose.
6. If failure analysis is unclear after 10 to 15 minutes, stop and summarize before continuing.

## Mandatory Stop Checkpoints

1. After contract + scope review.
2. After file-set proposal.
3. Before first code edit.
4. Before replay execution.
5. Before closure statement.

No checkpoint may be skipped.

## Allowed Implementation Surfaces (Typical)

1. Contract data for class semantics.
2. Ontology data for governed normalization.
3. Capability metadata declarations.
4. Generic resolver/planner/policy logic only when data contracts cannot express required behavior.
5. Replay/manual assets and tests.

## Disallowed Implementation Patterns

1. `if message contains "...compare..." then force report ...`
2. `if case_id == ...`
3. Hardcoded phrase maps in:
   - `read_engine.py`
   - `semantic_resolver.py`
   - `spec_pipeline.py`
   - `response_shaper.py`
   - `quality_gate.py`
   - `memory.py`
4. Forcing output shape to satisfy one prompt while violating class semantics.

## Required Asset Set Before Runtime Edits

1. `comparison` class definition and explicit non-goals.
2. Approved variation matrix.
3. Replay case pack updates for the first slice.
4. Manual golden pack for first slice.
5. Impacted-suite rerun plan.
6. Risk tier + owner assignment.

Runtime implementation cannot start until these are ready.

## Verification Contract

### Targeted Verification (Required First)

1. `comparison` targeted unit/module tests.
2. `comparison` targeted replay probes.
3. Manual golden prompts for:
   - base comparison ask
   - phrasing variants
   - restrictive projection follow-up
   - correction follow-up
   - unsupported cross-period ask

### Impacted Regression Verification

Rerun by touched surfaces:

1. Resolver/spec selection touched -> rerun `core_read`.
2. State/follow-up touched -> rerun `multiturn_context` and `transform_followup`.
3. Shaping touched -> rerun `core_read` plus affected class suite.

### Closure Verification

1. Replay evidence attached with log paths.
2. Manual browser evidence attached.
3. Deferred gaps listed explicitly as non-blockers only if approved.

## Enterprise Definition Of Done For Comparison Slice

`comparison` first slice is complete only when all are true:

1. Scope boundary respected (no cross-period support silently added).
2. Contract boundaries respected (no ad-hoc routing logic).
3. Targeted replay and impacted reruns are green.
4. Manual golden checks are green.
5. Closure note records:
   - exact files changed
   - excluded files
   - why each file changed
   - deferred items and ownership

## Deviation Rule

If any rule in this contract is at risk:

1. Stop implementation immediately.
2. Record the risk in writing.
3. Request explicit approval before continuing.

