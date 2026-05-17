# Qwen Enterprise Metadata

This directory is the shared metadata source of truth for the Qwen ERP assistant path.

It is intentionally separated from runtime code so that:

1. ERP-side follow-up logic can read the same metadata as runtime policy
2. report/capability approval is governed as data, not scattered code
3. future multilingual, artifact, and write-safety layers can extend the same structure

Deployment note:

1. ERP Python services should mount this directory read-only and expose it through `QWEN_ENTERPRISE_METADATA_DIR`
2. the external Qwen runtime should mount the same directory read-only
3. ERP-side and runtime-side code should read this directory as configuration, not copy it into code-local JSON files

Current files:

1. `capability_registry.json`
2. `report_registry.json`
3. `report_family_registry.json`
4. `business_ontology.json`
5. `frontdoor_intent_registry.json`
6. `validation_rules.json`
7. `semantic_alias_registry.json`
8. `semantic_resolution_registry.json`
9. `business_definition_registry.json`
10. `governed_formula_registry.json`
11. `business_threshold_registry.json`
12. `business_rule_registry.json`
13. `governed_kpi_execution_registry.json`
14. `composite_family_registry.json`
15. `composite_artifact_registry.json`
16. `composite_compatibility_registry.json`
17. `composite_assembly_registry.json`
18. `governed_scope_registry.json`
19. `scope_owner_registry.json`
20. `family_scope_compatibility_registry.json`
21. `scope_projection_registry.json`
22. `scope_clarification_registry.json`

Phase 2 note:

1. the business-definition, formula, threshold, and business-rule registries are now active runtime inputs, not documentation-only files
2. the governed KPI-definition frontdoor path reads these registries directly to answer active, blocked, ambiguous, and explicit-definition undefined KPI asks without hardcoded formula semantics

Phase 3 note:

1. the composite family, artifact, compatibility, and assembly registries are now active runtime inputs for governed composite execution
2. approved family resolution and row assembly must stay metadata-owned; do not widen composite support with family-specific merge logic in Python

Phase A note:

1. the governed scope, ownership, compatibility, projection, and clarification registries are now the policy backbone for scope activation
2. do not activate a new scope in runtime without first declaring its owner, source authority, family compatibility, projection policy, and clarification coverage in metadata

## Registry Maintenance Map

Use this section when a business definition, number, label, or policy needs to change later.

The rule is simple:

1. change governed business meaning in metadata first
2. change runtime code only if the generic seam itself must widen
3. do not bury business definitions or threshold numbers inside Python logic

### Which File To Edit

Edit [business_definition_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_definition_registry.json) when you are changing:

1. KPI name or canonical definition
2. entity grain
3. time basis
4. activation state of the business definition itself
5. source authority references at the definition level

Edit [governed_formula_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_formula_registry.json) when you are changing:

1. formula basis
2. numerator or denominator semantics
3. aggregation rule
4. formula activation state
5. parent-definition-to-formula linkage

Edit [business_threshold_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_threshold_registry.json) when you are changing:

1. numeric bands
2. risk labels
3. threshold activation state
4. threshold direction
5. blocked reasons for threshold presentation

Edit [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json) when you are changing:

1. clarification rules
2. user-facing policy wording gates
3. whether a threshold label may appear in runtime answers
4. approved business-policy basis
5. company-specific rule behavior

Edit [governed_kpi_execution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_kpi_execution_registry.json) when you are changing:

1. approved KPI execution shape
2. whether a KPI supports period scalar, as-of scalar, or ranking execution
3. source-mode ownership for KPI execution
4. supported execution filters and dimensions
5. unit type and runtime value-metric mapping
6. execution activation state

Edit [composite_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_family_registry.json) when you are changing:

1. approved composite family boundaries
2. supported family variation axes
3. allowed primary and supporting metrics inside a family
4. default limit and sort policy
5. clarification policy for family resolution

Edit [composite_artifact_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_artifact_registry.json) when you are changing:

1. approved composite instances inside a family
2. basis-specific composite activation
3. required component execution IDs
4. render style for a declared composite
5. composite activation state or blocked reason

Edit [composite_compatibility_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_compatibility_registry.json) when you are changing:

1. same-grain compatibility rules
2. same-period or same-as-of alignment rules
3. join-key policy
4. freshness policy
5. missing-component blocking rules

Edit [composite_assembly_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_assembly_registry.json) when you are changing:

1. shared row-assembly policy
2. component metric membership
3. component execution references
4. join key schema
5. row provenance and degradation rules

Edit [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json) when you are changing:

1. what business read capability exists
2. whether a new governed authority path is allowed
3. source-capability ownership

Edit [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json) when you are changing:

1. approved report authority
2. report column or filter metadata
3. which report supports a governed KPI or operational path

### When A Design Note Is Required First

Write or update a governance note before editing the registries when the change is:

1. a new KPI meaning
2. a disputed formula basis
3. a new risk label or threshold band
4. a new source-authority path
5. a policy-sensitive user-facing wording change
6. a cross-domain KPI such as margin, turnover, productivity, or HR metrics
7. a new composite family or family-wide compatibility rule

Direct metadata-only edits are acceptable when the change is small and already approved, for example:

1. correcting a blocked reason
2. adding an already-approved alternate label
3. adjusting an already-approved effective date
4. updating a threshold number after explicit finance approval

### Safe Change Workflow

When adding or changing a governed business definition:

1. update the relevant registry file or files
2. update tests for registry validation and runtime behavior
3. update any governance note if the change affects business policy
4. run the relevant probe or smoke before treating the change as complete

### Current Central Homes For Definitions And Numbers

For future adjustment, these are the main central files:

1. business definitions:
   - [business_definition_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_definition_registry.json)
2. formula ownership:
   - [governed_formula_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_formula_registry.json)
3. KPI execution policy:
   - [governed_kpi_execution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_kpi_execution_registry.json)
4. threshold numbers and labels:
   - [business_threshold_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_threshold_registry.json)
5. policy gates and wording rules:
   - [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json)
6. composite family boundaries:
   - [composite_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_family_registry.json)
7. composite instances and required components:
   - [composite_artifact_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_artifact_registry.json)
8. composite compatibility policy:
   - [composite_compatibility_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_compatibility_registry.json)
9. composite row assembly policy:
   - [composite_assembly_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/composite_assembly_registry.json)

That is the intended enterprise-grade adjustment path.
