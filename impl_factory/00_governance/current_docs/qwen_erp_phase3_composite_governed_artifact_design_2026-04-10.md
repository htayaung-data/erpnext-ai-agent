# Qwen ERP Phase 3 Composite Governed Artifact Expansion Design

Status: `3.1` complete, `3.2` complete, `3.3` next  
Date: 2026-04-10  
Scope: detailed implementation plan for Phase 3, Composite Governed Artifact Expansion

## 1. Executive Decision

Phase `2.5` made single-metric governed KPI execution real.

That means the next enterprise step is not broader free-form business reasoning.

The next step is:

1. typed composite governed artifacts
2. family-based composite runtime behavior
3. governed compatibility rules for combining metrics
4. explicit primary-metric and join policy
5. blocked-safe behavior when the requested composite cannot be proven safely

Phase `3` exists so the assistant can answer richer business questions such as:

1. `show top customers by revenue last month with quantity and average order value`
2. `show top products by revenue with quantity and average selling price this quarter`
3. `show overdue customers with overdue amount, overdue ratio, and credit utilization`
4. `show customers with the highest credit utilization and outstanding amount`

These examples are evidence of the intended composite families.

They are not the implementation target by themselves.

The implementation target is:

1. reusable family contracts
2. reusable family metadata
3. reusable family-level compatibility rules
4. runtime support for safe variations inside each approved family

This phase must not be implemented as:

1. hand-built one-off ranking presenters
2. prompt-led metric stitching
3. raw text interpretation after structured KPI execution already exists
4. unsafe joins between unrelated grains or time scopes
5. convenience narrative that hides incompatibility or stale evidence

## 2. Why Phase 3 Is The Correct Next Step

The system now has:

1. governed KPI definitions
2. governed formula ownership
3. governed threshold and rule metadata
4. governed KPI runtime execution for single metrics
5. business-natural answers for scalar and ranking KPI requests

What it still lacks is a safe answer shape for multi-metric business asks.

Without Phase `3`, the assistant risks:

1. combining metrics with different grains
2. combining metrics with incompatible period bases
3. mixing executed KPI values with ad hoc listing totals
4. presenting stitched outputs that look confident but are not contract-safe
5. resolving composite intent through ad hoc prompt interpretation
6. implementing one merge path per family instead of one reusable composite assembly layer

So Phase `3` is the first place where composite business answers should become legal.

It should also be the place where the system proves that composite support is family-based, not prompt-based.

That means the real question for this phase is not:

1. can we answer three prepared examples

The real question is:

1. can we support a governed range of questions inside an approved composite family without adding one-off branches

## 3. Enterprise Guideline Constraints For Phase 3

This phase must obey:

1. [qwen_erp_enterprise_development_guidelines_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_enterprise_development_guidelines_2026-04-04.md)

The most important constraints are:

1. contract first
2. metadata owns business policy
3. fail closed
4. explicit authority order
5. no keyword routing
6. no hardcoded single-case fixes
7. no prompt-led business logic

That means:

1. composite shape must be declared before runtime widening
2. compatibility policy must live in governed metadata
3. joins must be auditable and replayable
4. unsupported composite asks must clarify or block explicitly
5. phase scope must stay bounded to governed read artifacts

## 4. Current Ecosystem Readiness

### 4.1 What already exists

The ecosystem now already provides:

1. `business_definition_registry.json`
2. `governed_formula_registry.json`
3. `business_threshold_registry.json`
4. `business_rule_registry.json`
5. `governed_kpi_execution_registry.json`
6. typed KPI value artifacts
7. single-metric customer ranking support
8. grounded entity-detail follow-up support

### 4.2 What is missing

The system still needs:

1. a composite artifact contract
2. family-level composite metadata
3. a typed family-resolution contract
4. a reusable composite assembly contract
5. metadata-owned compatibility rules
6. primary-metric policy
7. same-grain validation
8. join freshness policy
9. render policy for composite evidence blocks
10. composite follow-up continuity rules

### 4.3 What must remain out of scope

Phase `3` should not widen into:

1. decomposition planning
2. free-form recommendations
3. management advice
4. charts or dashboards
5. multilingual UX
6. writes or approval flows

## 5. Authority Model For Composite Artifacts

Composite answers must follow this authority order:

1. approved family-resolution contract
2. approved composite artifact contract
3. approved assembly contract
4. approved compatibility metadata
5. approved single-metric execution artifacts
6. governed entity or ranking evidence
7. rendered business answer

Never authoritative:

1. raw prompt language after structured interpretation exists
2. ad hoc metric stitching in rendering code
3. convenience joins by label similarity
4. hidden period widening
5. unsupported merge rescue logic

## 6. New Contracts And Metadata For Phase 3

### 6.1 `CompositeFamilyResolutionContract`

This should become the typed runtime seam between frontdoor understanding and composite execution.

Its job is to resolve:

1. which composite family the user is asking for
2. which variation axes are already explicit
3. which variation axes are still missing
4. whether the request is inside an approved family at all

Recommended fields:

1. `resolution_type`
2. `family_id`
3. `family_label`
4. `requested_primary_metric`
5. `requested_secondary_metrics`
6. `requested_basis`
7. `requested_period`
8. `requested_as_of_date`
9. `requested_limit`
10. `requested_sort_direction`
11. `variation_inputs`
12. `missing_clarifications`
13. `status`
14. `blocked_reason`

Required statuses:

1. `resolved_family`
2. `clarify_family_variation`
3. `blocked_no_governed_family`
4. `blocked_unsupported_family_variation`

### 6.2 `CompositeGovernedArtifactContract`

This should become the typed runtime artifact for multi-metric governed outputs.

Recommended fields:

1. `artifact_type`
2. `composite_id`
3. `label`
4. `composite_kind`
5. `primary_metric_id`
6. `secondary_metric_ids`
7. `entity_grain`
8. `time_scope_type`
9. `scope`
10. `period_start`
11. `period_end`
12. `as_of_date`
13. `row_count`
14. `rows`
15. `source_artifact_refs`
16. `compatibility_status`
17. `blocked_reason`
18. `render_policy`

The artifact must describe the composite result itself, not how the system guessed the family.

### 6.3 `CompositeAssemblyAdapterContract`

This should become the reusable seam that prevents Phase `3` from turning into one merge implementation per family.

Its job is to own:

1. which scalar artifacts must be executed
2. how rows are matched
3. how rows degrade when one component is missing
4. what provenance each row must retain

Recommended fields:

1. `assembly_id`
2. `family_id`
3. `component_metric_ids`
4. `component_execution_ids`
5. `join_key_schema`
6. `row_identity_policy`
7. `row_merge_policy`
8. `row_missing_component_policy`
9. `row_provenance_policy`
10. `status`
11. `blocked_reason`

Minimum row-level provenance should include:

1. join key used
2. contributing scalar artifacts
3. metrics missing by policy
4. whether the row is fully complete or partially degraded

### 6.4 `CompositeFamilyRegistry`

Phase `3` should first add:

1. `composite_family_registry.json`

Its job is to define reusable family behavior.

Recommended fields:

1. `family_id`
2. `label`
3. `entity_grain`
4. `time_scope_type`
5. `supported_variation_axes`
6. `allowed_primary_metrics`
7. `allowed_secondary_metrics`
8. `default_sort_direction`
9. `default_limit_policy`
10. `clarification_policy`
11. `activation_state`

Typical variation axes should include:

1. metric basis
2. period or as-of scope
3. top-N limit
4. primary sort metric
5. optional supporting metrics

### 6.5 `CompositeArtifactRegistry`

Phase `3` should add a new metadata home:

1. `composite_artifact_registry.json`

Its job is to own composite policy, not scalar KPI meaning.

Recommended fields:

1. `composite_id`
2. `label`
3. `composite_kind`
4. `entity_grain`
5. `time_scope_type`
6. `primary_metric_id`
7. `secondary_metric_ids`
8. `required_execution_ids`
9. `compatibility_rule_ids`
10. `render_style`
11. `activation_state`
12. `blocked_reason`

This registry should declare approved composite instances inside a family, not one-off prompt behaviors.

### 6.6 `CompositeCompatibilityRegistry`

Phase `3` should also add:

1. `composite_compatibility_registry.json`

Its job is to decide whether metrics can be combined safely.

Recommended fields:

1. `compatibility_rule_id`
2. `label`
3. `allowed_entity_grain`
4. `allowed_time_scope_type`
5. `required_period_alignment`
6. `required_as_of_alignment`
7. `required_scope_alignment`
8. `join_key_policy`
9. `freshness_policy`
10. `block_on_missing_metric`
11. `activation_state`

### 6.7 Required composite states

The runtime must distinguish:

1. `active_composite`
2. `clarify_scope`
3. `clarify_metric_basis`
4. `blocked_incompatible_grain`
5. `blocked_incompatible_time_scope`
6. `blocked_missing_component`
7. `unsupported_composite_shape`
8. `blocked_no_governed_family`
9. `blocked_unsupported_family_variation`

## 7. Composite Families To Cover

Phase `3` should cover only a small number of high-value composite families.

Each family must support a bounded but reusable range of user asks.

The goal is not:

1. one demo question per family

The goal is:

1. one governed runtime family per business surface
2. safe variation inside that family
3. explicit block or clarify behavior outside that family

### 7.1 Customer commercial ranking

Supported family shape:

1. customer
2. revenue
3. quantity
4. average order value or average invoice value

Supported variation axes:

1. sales-order basis or sales-invoice basis
2. top N limit
3. period
4. primary ranking metric within the approved family
5. presence or absence of one approved supporting metric

### 7.2 Product commercial ranking

Supported family shape:

1. product or item
2. revenue
3. quantity
4. average selling price

Supported variation axes:

1. top N limit
2. period
3. primary ranking metric
4. approved item-label wording policy
5. optional supporting metrics that stay within the same item grain

Enterprise framing:

1. this is not a new special-case runtime for `top products`
2. this is the item-grain activation of the same commercial-ranking archetype already proven on customer grain
3. the reusable runtime seam should stay:
   - family resolution
   - composite artifact resolution
   - shared assembly adapter
   - compatibility validation
   - family-generic rendering and continuation
4. item or product wording must remain metadata-owned, not prompt-owned

### 7.3 Customer credit and overdue composite

Supported family shape:

1. customer
2. overdue amount
3. overdue ratio
4. outstanding amount
5. credit utilization

Supported variation axes:

1. top N limit
2. as-of date
3. primary ranking metric
4. threshold-match filtering
5. optional supporting credit metrics inside the same customer/as-of family

Enterprise framing:

1. this is not a one-off `overdue customer report` handler
2. this is the first activation of a customer-risk composite archetype with:
   - customer grain
   - shared `as_of_date`
   - approved risk metrics
   - threshold-aware filtering
3. overdue-focused views should be expressed as governed family variations inside that archetype, not as separate prompt paths
4. future additions such as severity bands or payment-behavior metrics must enter only after they become approved scalar artifacts

This is intentionally a stronger Phase `3` target than the older roadmap placeholder `last payment date`, because `last payment date` is not yet a governed scalar KPI surface. It should not become a stealth blocker for the whole phase.

## 8. Family-Based Runtime Rule

Phase `3` must be built as a family-based composite runtime.

That means:

1. frontdoor resolves a request into a `CompositeFamilyResolutionContract`
2. runtime selects an approved `composite_id` inside that resolved family
3. `CompositeAssemblyAdapterContract` governs how scalar artifacts become composite rows
4. compatibility rules validate the requested mix
5. render logic stays generic to the family, not to one exact prompt

This phase must not rely on:

1. literal prompt templates
2. one branch per example question
3. case-by-case Python handlers with embedded metric knowledge
4. family-local merge code that bypasses a shared assembly adapter

If a user asks a new question that still fits the approved family, the system should answer it without new code.

If the question goes outside the family, the system should clarify or block explicitly.

## 9. Detailed Mini-Phase Plan

### 9.1 `3.1` Composite Artifact Contract

Goal:

1. define the typed composite seam before any composite runtime behavior is widened

Deliver:

1. `CompositeFamilyResolutionContract`
2. `CompositeGovernedArtifactContract`
3. `CompositeAssemblyAdapterContract`
4. `CompositeFamilyRegistry`
5. `CompositeArtifactRegistry`
6. `CompositeCompatibilityRegistry`
7. composite state resolver
8. contract validation tests

Implementation detail:

1. the runtime must not execute composites directly from prompt language
2. the frontdoor should resolve a composite request into a declared `family_id` plus structured variation inputs through `CompositeFamilyResolutionContract`
3. runtime should then resolve to a declared `composite_id`
4. `CompositeAssemblyAdapterContract` must own row assembly instead of family-specific merge helpers
5. the composite contract must reference already-approved scalar metric artifacts
6. compatibility checks must happen before merge or render

What must be true before `3.1` closes:

1. composite metadata can declare customer ranking, product ranking, and customer credit composite families
2. same-grain and same-period checks are explicit
3. family variation axes are explicit in metadata
4. family resolution is typed and auditable
5. row assembly is shared and typed, not family-local
6. unsupported composite asks fail closed through typed states

Completion note:

1. runtime contracts now exist in:
   - [composite_artifact_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_artifact_state.py)
   - [composite_artifact_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_artifact_registry.py)
2. governed metadata homes now exist in:
   - [composite_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_family_registry.json)
   - [composite_artifact_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_artifact_registry.json)
   - [composite_compatibility_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_compatibility_registry.json)
   - [composite_assembly_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_assembly_registry.json)
3. missing required variation axes such as `basis` now stop at typed clarification instead of resolving early
4. current scaffold no longer blocks at `blocked_missing_component` for approved customer commercial composites
5. deterministic coverage now lives in:
   - [test_composite_artifact_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_composite_artifact_registry.py)
   - [test_composite_artifact_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_composite_artifact_state.py)
6. callable probe verification is green through:
   - `run_composite_artifact_registry_probe`
   - `run_composite_artifact_contract_probe`

### 9.2 `3.2` Customer Ranking Composites

Goal:

1. support a reusable governed customer ranking family, not one fixed report shape

Deliver:

1. customer revenue + quantity + average order value composite
2. customer revenue + quantity + average invoice value composite
3. explicit primary-metric sorting rule
4. bounded top-N render policy
5. detail and follow-up continuity from composite rows
6. family-level variation support for period, top N, and basis

Implementation detail:

1. keep customer ranking composite limited to company-period scope first
2. revenue and quantity must share the same document basis as the chosen AOV basis
3. the runtime must block if the user asks for a mixed-basis composite without clarifying
4. rendered rows should stay business-natural and compact
5. new prompt phrasings inside the approved family should not require new code

Example governed asks:

1. `show top 5 customers by sales order revenue with quantity and average order value last month`
2. `show top 10 customers by sales invoice revenue with quantity and average invoice value this quarter`

What must stay blocked:

1. recommendation language such as `which customers should we prioritize`
2. cross-domain joins with credit metrics in the same composite unless declared separately

Current implementation note:

1. `3.2` is now active for the reusable `customer_commercial_ranking` family
2. approved period customer-grain component executions now exist for:
   - sales-order revenue
   - sales-order quantity
   - average order value by sales order
   - sales-invoice revenue
   - sales-invoice quantity
   - average invoice value by sales invoice
3. the front door now resolves `governed_composite_value` turns through typed family resolution and shared row assembly, not prompt-specific branches
4. missing `basis` and missing primary metric both clarify through governed family-variation continuations
5. row assembly remains metadata-owned through the approved composite and assembly registries
6. live probe and live smoke are green for:
   - direct customer commercial composite request
   - missing-basis clarification
   - `Sales Order` clarification continuation
7. Phase `3.3` should now extend the same family-based runtime pattern to product commercial composites rather than widening customer-family logic

### 9.3 `3.3` Entity-Period Commercial Ranking Generalization

Goal:

1. generalize the proven commercial-ranking composite pattern from customer grain to item grain without adding a new prompt-led runtime

Deliver:

1. reusable entity-period commercial-ranking activation for item grain
2. item and product commercial ranking as governed grain variations of the same family
3. governed item-grain compatibility rules
4. bounded top-N rendering
5. row detail continuity for item-level follow-up

Implementation detail:

1. keep this slice on one trusted item grain
2. price-per-unit must come from the same commercial basis as revenue and quantity
3. the runtime must clarify if the user asks for a product composite without period
4. the runtime must block if the item grain is not provable from the selected source
5. new prompt phrasings inside the approved family should not require new code
6. the runtime implementation should reuse the same family-level assembly and continuation contracts already used by customer commercial ranking
7. any new behavior that exists only for products should be metadata-owned and grain-owned, not prompt-owned

Example governed asks:

1. `show top 10 products by revenue with quantity and average selling price last month`
2. `show top items by quantity and average selling price this fiscal year`

What must stay blocked:

1. profitability joins
2. landed-cost or margin joins
3. warehouse stock joins

Current implementation note:

1. active bounded design note:
   - [qwen_erp_phase3_3_ranking_projection_and_evidence_contract_design_2026-04-11.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_phase3_3_ranking_projection_and_evidence_contract_design_2026-04-11.md)
2. the current `3.3` entry point is not a new family invention:
   - it is a shared ranking projection and continuation harmonization slice inside the existing composite runtime
3. the approved bounded order inside `3.3` is now:
   - `3.3A` ranking projection contract harmonization
   - `3.3B` entity-detail evidence request contract cleanup
   - `3.3C` metadata and semantic completion for the missing evidence distinctions
4. `3.3B` is intentionally inside active Phase `3`, not deferred into an undefined later cleanup chapter, because renderer lexical branching is still an authority problem inside the governed runtime

### 9.4 `3.4` Customer Risk-As-Of Composite Archetype

Goal:

1. activate a reusable customer-risk-as-of composite archetype using approved customer credit metrics

Deliver:

1. overdue amount + overdue ratio + outstanding amount + credit utilization as governed variations inside one customer-risk-as-of family
2. threshold-driven filtering for overdue-only surfaces
3. customer row continuity into detail follow-up
4. bounded ranking and filter render policy
5. metadata-owned variation policy for primary metric, supporting metrics, and threshold filters inside the same family

Implementation detail:

1. use the same `as_of_date` across all component metrics
2. do not include `last payment date` yet unless it first becomes an approved scalar metric with governed execution
3. ranking order must be explicit:
   - overdue amount first
   - credit utilization as supporting context
4. if credit limit data is missing for a customer row, the row should degrade safely rather than silently fabricate utilization
5. new prompt phrasings inside the approved family should not require new code
6. this slice should create no new report-specific handler; it should prove that a second archetype can be activated through the same composite runtime contracts

Example governed asks:

1. `show overdue customers with overdue amount, overdue ratio, and credit utilization as of today`
2. `show top overdue customers by overdue amount as of today`

What must stay blocked:

1. collection recommendations
2. follow-up claims about payment behavior not yet backed by governed scalar metrics

### 9.5 `3.5` Composite Phase Closure

Goal:

1. close Phase `3` with release-gated confidence and clear stop rules

Deliver:

1. composite live smoke pack
2. composite release-gate promotion
3. current baseline update
4. roadmap and design-note closure refresh
5. explicit stop rule for what Phase `3` does not try to solve

Required verification:

1. contract tests for composite registry and compatibility rules
2. focused runtime tests for customer, product, and overdue composites
3. browser/UAT pack with:
   - customer ranking composite
   - product ranking composite
   - overdue customer composite
   - one clarify case
   - one blocked case
4. at least one alternate wording per family to prove that the runtime is family-based rather than prompt-based
5. at least one proof that a new composite inside an existing family can be activated through metadata and shared assembly rules without adding a new family-specific runtime path
6. at least one proof that a blocked family variation fails through typed family-resolution status rather than silent fallback

## 10. Suggested Implementation Order Inside Phase 3

The correct order should be:

1. `3.1` composite contract and metadata
2. `3.2` customer ranking composites
3. `3.3` entity-period commercial ranking generalization
4. `3.4` customer-risk-as-of composite archetype
5. `3.5` closure and release-gate promotion

Do not invert this order.

In particular:

1. do not start with overdue composite before the generic composite seam exists
2. do not jump to decomposition planning before composite artifact runtime is proven

## 11. What Phase 3 Should Be Able To Answer

If Phase `3` is implemented correctly, the assistant should be able to answer:

1. the prepared examples in this note
2. alternate phrasings that still map to the approved family
3. safe metric variations that remain inside the declared family metadata

It should not be limited to a tiny list of blessed prompts.

It should also not pretend to answer every imaginable BI question.

The correct enterprise standard is:

1. broad reuse inside approved families
2. fail-closed behavior outside approved families
3. shared family resolution instead of prompt-led routing
4. shared composite assembly instead of one merge path per family
5. family archetypes that admit new governed variations without new runtime branches

That is not a single-case fix architecture.

That is a governed family-based enterprise runtime.

## 12. Business Definitions And Metrics Expected To Be Reused

Phase `3` should reuse governed metrics already established in Phase `2` and `2.5`.

Expected scalar dependencies:

1. sales-order revenue
2. sales-order quantity
3. average order value by sales order
4. sales-invoice revenue
5. sales-invoice quantity
6. average order value by sales invoice
7. customer overdue amount
8. customer overdue ratio
9. customer outstanding amount
10. customer credit utilization

If one of these is not yet available as a typed scalar artifact, it must be added as governed scalar support first.

Do not bypass Phase `2.5` execution just to make a composite look complete.

## 13. Phase 3 Open Questions That Must Stay Governed

These questions should not be solved casually during implementation:

1. whether customer ranking should default to sales-order basis or sales-invoice basis
2. whether product ranking should be called `product` or `item` in user-facing answers
3. whether overdue customer composites should sort by overdue amount or overdue ratio by default
4. whether threshold labels should appear by default in overdue composites

These belong in metadata or a short governance note, not in ad hoc runtime branching.

## 14. What Phase 3 Must Not Become

Phase `3` must not become:

1. a hidden decomposition planner
2. a general BI engine
3. recommendation logic
4. dashboard generation
5. an uncontrolled widening into every imaginable composite

The stop rule is:

1. customer ranking composite works
2. entity-period commercial ranking generalization works at item grain
3. customer-risk-as-of composite archetype works
4. compatibility checks fail closed
5. release gates are green

Then Phase `3` is done.

## 15. Current Recommendation

The approved next implementation order should be:

1. `3.1` Composite Artifact Contract
2. `3.2` Customer Ranking Composites
3. `3.3` Entity-Period Commercial Ranking Generalization
4. `3.4` Customer Risk-As-Of Composite Archetype
5. `3.5` Composite Phase Closure

That is the correct enterprise-grade next chapter after Phase `2.5`.
