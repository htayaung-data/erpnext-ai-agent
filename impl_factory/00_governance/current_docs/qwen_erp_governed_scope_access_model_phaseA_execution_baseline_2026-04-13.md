# Qwen ERP Governed Scope Access Model Phase A Execution Baseline

Status: active execution baseline
Date: 2026-04-13
Scope: concrete execution baseline for Phase A of the governed scope activation and cross-family alignment chapter

## 1. Purpose

This document turns Phase A of the new governed scope roadmap into an execution-ready baseline.

It exists to answer the practical implementation questions that must be settled before coding begins:

1. what exact outputs Phase A must produce
2. which metadata registries should be created or extended
3. which existing registries and contracts are the official integration targets
4. what the first bounded implementation slice should cover
5. how acceptance will be measured

This is not a broad implementation chapter by itself.

It is the baseline that makes later activation work safe, consistent, and auditable.

## 2. Phase A Goal

Phase A exists to define one shared governed scope access model for the ERP AI assistant.

That model must answer, for every approved or candidate scope:

1. what the scope is
2. what class of scope it belongs to
3. who owns i
4. which families may consume i
5. which fields or projections are allowed by family
6. which ambiguity classes apply
7. what the current support state is

If Phase A is done correctly, later phases will no longer need to guess whether a scope should be available in:

1. front-door interpretation
2. listing
3. detail
4. ranking
5. composite behavior
6. finance/evidence behavior
7. follow-up and deictic continuity

## 3. Enterprise Baseline Rules

Phase A must follow these rules strictly.

### 3.1 Scope Is A Policy Objec

Scope must not remain scattered across:

1. report naming
2. capability naming
3. direct runtime branches
4. family-specific conventions

Scope must become an explicit policy object in metadata.

### 3.2 No Partial Activation Claims

No scope may be called active unless the access model can point to:

1. a primary owner
2. an approved source authority
3. compatible family lis
4. projection policy
5. clarification policy
6. support-state classification

### 3.3 Policy Must Explain Asymmetry

If one scope is allowed in:

1. detail but not listing
2. listing but not ranking
3. specialized runtime but not shared family flow

that asymmetry must be recorded explicitly as policy or support state, not left as accidental behavior.

### 3.4 Phase A Is Contract And Metadata Firs

Phase A is allowed to introduce:

1. metadata registries
2. metadata integrity validation
3. contract-safe helper structures
4. minimal read-only loader code if needed

Phase A is not allowed to:

1. widen runtime behavior broadly before the metadata model exists
2. activate many new scopes directly in production paths
3. add phrase-led rescue as a shortcut for missing policy

## 4. Deliverables

Phase A must produce six concrete outputs.

### 4.1 Scope Inventory Registry

Deliver one canonical registry of governed scope objects.

Minimum fields per scope:

1. `scope_id`
2. `scope_label`
3. `scope_class`
4. `status`
5. `primary_owner_family`
6. `approved_source_authority`
7. `canonical_grains`
8. `canonical_alias_groups`
9. `support_state`
10. `notes`

### 4.2 Scope Ownership Registry

Deliver one explicit ownership model.

Minimum fields:

1. `scope_id`
2. `primary_owner_family`
3. `secondary_compatible_families`
4. `prohibited_families`
5. `ownership_reason`
6. `policy_notes`

### 4.3 Family Compatibility Registry

Deliver one compatibility matrix between governed scope and family contracts.

Minimum fields:

1. `scope_id`
2. `family_id`
3. `compatibility_level`
4. `allowed_modes`
5. `blocked_reason`
6. `followup_compatibility`

### 4.4 Projection Policy Registry

Deliver one policy registry that controls what fields or section groups a family may expose for a scope.

Minimum fields:

1. `scope_id`
2. `family_id`
3. `projection_group_id`
4. `allowed_dimensions`
5. `allowed_metrics`
6. `allowed_detail_sections`
7. `default_projection_shape`
8. `projection_notes`

### 4.5 Clarification Coverage Registry

Deliver one policy mapping between scope/family combinations and ambiguity classes.

Minimum fields:

1. `scope_id`
2. `family_id`
3. `supported_ambiguity_classes`
4. `required_basis_slots`
5. `required_event_slots`
6. `clarification_template_group`
7. `clarification_notes`

### 4.6 Integrity Validation Rules

Deliver validation rules that reject impossible or incomplete activation states.

Minimum checks:

1. no active scope without owner
2. no active scope without approved source
3. no active scope without at least one compatible family
4. no active scope without projection policy
5. no active scope without clarification coverage
6. no compatibility entry for unknown scope
7. no projection policy for unknown family

## 5. Exact Metadata Targets

Phase A should use the existing enterprise metadata folder and add only the minimum new registries required.

### 5.1 New Registries To Introduce

Recommended new files:

1. [governed_scope_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_scope_registry.json)
2. [scope_owner_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/scope_owner_registry.json)
3. [family_scope_compatibility_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/family_scope_compatibility_registry.json)
4. [scope_projection_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/scope_projection_registry.json)
5. [scope_clarification_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/scope_clarification_registry.json)

These files should become the canonical policy backbone for scope activation.

### 5.2 Existing Registries That Must Be Aligned

Phase A must align with these existing files rather than replacing them:

1. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
2. [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)
3. [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
4. [semantic_resolution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_resolution_registry.json)
5. [entity_reference_policy_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/entity_reference_policy_registry.json)
6. [clarification_templates_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json)
7. [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json)
8. [validation_rules.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/validation_rules.json)

### 5.3 Existing Contracts And Runtime Seams To Respec

Phase A should be designed to feed these existing contracts and shared seams:

1. `FreshQueryInterpretationContract`
2. `EntityReferenceResolutionContract`
3. `EntityDetailEvidenceRequestContract`
4. `FollowUpBoundaryContract`
5. normalized family artifact and rendering contracts

The Phase A baseline must not invent a parallel contract universe.

## 6. Scope Seed Set For Phase A

Phase A should begin with a deliberate seed set taken from research, not from the whole ERP universe at once.

### 6.1 Mandatory Seed Scopes

The first Phase A baseline must explicitly model these scopes:

1. `customer_master`
2. `supplier_master`
3. `item_master`
4. `sales_invoice`
5. `purchase_invoice`
6. `delivery_note`
7. `sales_order`
8. `purchase_order`
9. `payment_entry`

### 6.2 Important Support-State Seeds

These support states must be represented honestly in the baseline:

1. `customer_master`
   - active reference scope
2. `supplier_master`
   - contract-ready vocabulary, policy-inactive
3. `item_master`
   - contract-ready vocabulary, ownership-sensitive
4. `sales_invoice`
   - active and broadly routed
5. `purchase_invoice`
   - runtime-real, generic listing support-state restricted / clarified
6. `delivery_note`
   - active operational document scope
7. `sales_order`
   - active operational document scope
8. `purchase_order`
   - active operational document scope
9. `payment_entry`
   - partial / specialized-owned pending ownership decision

### 6.3 Deferred-But-Visible Seeds

The baseline may also record, but not activate, deferred scopes such as:

1. `purchase_receipt`
2. `journal_entry`
3. later HR or manufacturing scope if discovered

This is useful because deferred scope should still be represented consistently in planning.

## 7. Family Set For Phase A Compatibility Modeling

Phase A compatibility work must at minimum cover these families:

1. direct navigation
2. entity detail
3. transaction listing
4. ranked entities
5. composite artifac
6. financial summary / aging
7. inventory / product-performance
8. clarification / follow-up continuity

This list matches the research conclusion that the problem is cross-family unevenness, not one-family absence.

## 8. Mini-Phase Structure

Phase A should be executed in five mini-phases.

## A.1 Inventory Baseline

Goal:

1. create the first normalized governed scope inventory

Deliver:

1. initial `governed_scope_registry.json`
2. support-state classification for the seed scope se
3. naming normalization notes for inconsistent scope names

Acceptance:

1. all seed scopes exist in the registry
2. each has one support-state classification
3. no duplicate scope representations remain in the Phase A doc se

## A.2 Ownership Baseline

Goal:

1. assign one primary owner and explicit compatible families to every seed scope

Deliver:

1. initial `scope_owner_registry.json`
2. ownership decisions for:
   - supplier_master
   - item_master
   - purchase_invoice
   - payment_entry

Acceptance:

1. no seed scope remains without a primary owner
2. unresolved ownership is tracked explicitly as `pending_policy_decision`, not hidden

## A.3 Compatibility Baseline

Goal:

1. state which families may consume each seed scope

Deliver:

1. initial `family_scope_compatibility_registry.json`
2. explicit compatibility entries for all seed scope x family combinations that matter immediately

Acceptance:

1. compatibility is explicit for all seed scopes
2. blocked combinations carry a reason
3. no family compatibility is assumed silently

## A.4 Projection And Clarification Baseline

Goal:

1. define allowed field groups and ambiguity classes per seed scope

Deliver:

1. initial `scope_projection_registry.json`
2. initial `scope_clarification_registry.json`
3. mapping into existing clarification template groups where possible

Acceptance:

1. every active or partial seed scope has at least one projection group
2. every active or partial seed scope has ambiguity coverage defined

## A.5 Integrity And Publication Baseline

Goal:

1. enforce consistency and publish the access model as active governance

Deliver:

1. validation rules added to `validation_rules.json`
2. metadata loader/integrity hooks if required
3. updated governance read order

Acceptance:

1. incomplete active scope entries are rejected by validation
2. the Phase A baseline is part of the active governance stack

## 9. First Bounded Implementation Slice

The first bounded implementation slice after this baseline should be:

## Slice A0: Seed Scope Policy Backbone

Purpose:

1. build the metadata backbone for the seed scope set without activating broad new runtime behavior ye

Scope:

1. create the five new registries
2. populate them for the Phase A seed scopes
3. align the seed scope names with existing capability/report/entity-reference metadata
4. add integrity validation rules
5. expose loader/read helpers if needed for later runtime use

Why this should be first:

1. it solves the cross-layer truth problem before any new activation work starts
2. it prevents future supplier/item/payment-entry work from repeating partial activation mistakes
3. it gives later runtime changes one source of truth to consume

Important boundary:

Slice A0 should not yet:

1. activate supplier behavior in production
2. activate item/product behavior in production
3. activate payment-entry behavior in production
4. widen ambiguity handling in runtime

It should define the policy backbone that those later slices will consume.

## 10. Recommended Second Slice

After Slice A0, the next slice should be:

## Slice A1: Scope-Aware Front-Door And Compatibility Validation

Purpose:

1. make the front door and compatibility validation aware of the new scope metadata backbone

Scope:

1. read canonical scope IDs from the new registries
2. validate that active scope has complete policy backing
3. reject partial activation states early
4. expose compatibility decisions to later family/runtime work

Important boundary:

This slice is still infrastructure-first.
It should not widen broad user-visible behavior beyond consistency and validation.

## 11. Acceptance Criteria For Phase A As A Whole

Phase A is complete only if:

1. the seed scope set is modeled exactly once in canonical metadata
2. ownership is explicit for every seed scope
3. family compatibility is explicit for every seed scope
4. projection policy is explicit for every active or partial seed scope
5. clarification policy is explicit for every active or partial seed scope
6. validation rules can detect incomplete active scope definitions
7. later phases can consume the Phase A outputs without adding another parallel planning layer

## 12. What Phase A Explicitly Does Not Do

Phase A does not:

1. activate all approved scopes in runtime
2. remove all mixed branching from runtime
3. solve all ambiguity breadth in user-facing behavior
4. retrofit every family immediately

Those belong to later phases.

Phase A succeeds when it makes those later phases safe, consistent, and policy-driven.

## 13. Final Direction

The first post-roadmap implementation work should not jump directly into supplier, item, or payment-entry user behavior.

It should first establish the governed scope access backbone so that later activation work can be:

1. full-stack
2. cross-family
3. auditable
4. compatible with existing contracts
5. safe from partial-activation drif
