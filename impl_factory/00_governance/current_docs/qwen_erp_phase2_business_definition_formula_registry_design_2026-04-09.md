# Qwen ERP Phase 2 Business Definition and Formula Registry Design

Status: 2.4 complete  
Date: 2026-04-09  
Scope: detailed implementation plan for Phase 2, Business Definition and Formula Registry

## 1. Executive Decision

Phase 2 should start with governed business-definition and formula registries, not with broader advisory behavior, composite dashboards, or another operational domain.

The first implementation must stay:

1. metadata-first
2. contract-first
3. fail-closed
4. company-governed
5. compatible with the current metadata/compiler/runtime ecosystem

This means the first target is:

1. a governed `BusinessDefinitionRegistry`
2. a governed `GovernedFormulaRegistry`
3. a threshold/risk-semantics registry that fits the same metadata pattern
4. typed runtime resolution for:
   - active definitions
   - blocked definitions
   - ambiguous definitions
   - tenant-data-blocked definitions
5. explicit blocked-safe behavior when a KPI is not ready for runtime use

This phase should not start with:

1. composite artifact joins
2. free-form management advice
3. predictive payment or credit behavior
4. HR, payroll, or headcount coverage
5. prompt-only KPI semantics
6. company-specific formulas hardcoded in Python

## 2. What Phase 1 Proved

Phase `1.1` through `1.5` changed the project in an important way.

What is now strong enough to build on:

1. Wave 1 operational coverage is closure-complete and release-gated
2. the assistant can already answer several high-value operational reads through governed metadata and typed artifacts
3. the most important late fixes were architecture-aligned shared-core fixes, not prompt patches
4. explicit deferral worked better than speculative widening

What Phase 1 still exposed:

1. derived business meaning is not yet governed deeply enough
2. KPI terms such as `tenure`, `average order value`, `collection ratio`, and `credit utilization` are not safe to treat as self-evident
3. future composite and reasoning work will drift if those meanings remain informal

So the next maturity step is not another operational family first.

It is semantic governance of business definitions and formulas.

## 3. Enterprise Guideline Constraints For Phase 2

Phase 2 must obey the active enterprise guide:

1. contract first
2. metadata owns business policy
3. runtime consumes typed definitions instead of rediscovering meaning from prompt text
4. fail closed when a KPI is undefined, disputed, or unsupported by tenant data
5. no keyword routing
6. no single-case formula hacks
7. no company-specific business definitions directly in code
8. no prompt-only threshold or formula ownership
9. release criteria must remain executable

This phase is enterprise-grade only if:

1. business-definition ownership is explicit
2. formula inputs and grain are explicit
3. threshold ownership is explicit
4. blocked states are explicit
5. future runtime usage is auditable

## 4. Current ERP And Repo Findings

The current ecosystem is ready for a registry-first phase, but not for ungoverned derived-metric expansion.

### 4.1 Current metadata architecture is already registry-oriented

The assistant already loads governed metadata from:

1. [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
2. `impl_factory/03_config/qwen_enterprise_metadata/*.json`

Current active registries already include:

1. capability registry
2. report registry
3. report-family registry
4. semantic resolution registry
5. validation registry
6. ontology and evaluation registries

This is the correct ecosystem for adding business-definition and formula registries.

### 4.2 The runtime can govern source reports, but not yet KPI meaning

Current runtime strength:

1. it can resolve governed capabilities and reports
2. it can validate family behavior
3. it can block unsupported or weakly grounded asks

Current gap:

1. the system still lacks a first-class registry for approved KPI meaning, formula basis, and threshold ownership

That means later questions such as:

1. `what is customer tenure?`
2. `what is our collection ratio?`
3. `who is high credit risk?`

should not be widened casually before the meanings are governed.

### 4.3 Some candidate KPIs are real, but not equally ready

Current candidate status:

1. `average order value` is a real KPI, but document basis must be explicit:
   - sales invoice basis
   - sales order basis
2. `tenure` is real, but basis is ambiguous:
   - customer creation date
   - first sales order date
   - first sales invoice date
3. `collection ratio` is real, but denominator and time basis are often disputed
4. `credit utilization` is real, and this tenant now has both active credit-limit data and governed formula plus threshold semantics

So Phase 2 must be able to represent:

1. active definitions
2. blocked-by-policy definitions
3. blocked-by-data definitions
4. ambiguous definitions that require approval before runtime use

### 4.4 Phase 2 should fit the current assistant, not bypass it

Phase 2 should adapt to the current ecosystem by adding:

1. new metadata files
2. metadata loader helpers
3. typed lookup contracts
4. deterministic blocked-safe runtime behavior

It should not introduce:

1. a new free-form reasoning lane
2. a hidden formula engine that bypasses report authority
3. prompt-only fallback semantics for disputed KPIs

## 5. Authority Model For Business Definitions And Formulas

The first authoritative model for derived business meaning must be intentionally strict.

Primary authority should be:

1. approved business-definition registry entries
2. approved formula registry entries
3. approved threshold entries
4. existing governed capability and report metadata
5. tenant data presence where the definition requires configured master data

Every approved definition must declare:

1. definition or formula identifier
2. business label
3. business meaning
4. owner
5. company scope
6. entity grain
7. time basis
8. source metric authority
9. activation state
10. blocked or clarify behavior when not executable

Deferred authority for later phases only:

1. composite joins whose compatibility is not yet proven
2. AI-invented KPI meaning
3. policy recommendations based only on narrative interpretation
4. HR, payroll, and people metrics without a dedicated domain design
5. credit-limit-based risk claims when limit rows are absent

This means:

1. Phase 2 should govern meaning before it governs broad answers
2. some KPIs may become `defined but blocked`
3. that is the correct enterprise result when approval or data is still missing

## 6. Scope For Phase 2

### 6.1 In scope

1. `BusinessDefinitionRegistry` metadata
2. `GovernedFormulaRegistry` metadata
3. threshold / risk-semantics metadata
4. metadata loader functions and accessor helpers
5. typed runtime contracts for definition lookup and formula resolution state
6. blocked-safe user-facing behavior for undefined or inactive KPIs
7. first governed KPI candidates:
   - tenure
   - average order value
   - collection ratio
   - credit utilization
8. deterministic tests and release-gate promotion where appropriate
9. doc updates and explicit stop rule

### 6.2 Explicitly deferred

1. HR or headcount coverage
2. inventory turnover if cost basis and inventory semantics are not yet governed
3. gross margin or profitability formulas if cost authority is not explicitly approved
4. credit approval policy, credit hold decisions, or collection strategy advice
5. predictive payment or behavioral scoring
6. composite KPI answering that depends on unproven joins
7. write actions or master-data mutation

## 7. Detailed Mini-Phase Plan

### 7.1 `2.1` Registry Contracts

Goal:

1. create the governed metadata and contract seam for business definitions, formulas, and thresholds

Implementation ownership:

1. metadata:
   - add `business_definition_registry.json`
   - add `governed_formula_registry.json`
   - add `business_threshold_registry.json`
2. runtime:
   - extend [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py) with loader and accessor helpers
   - add typed lookup/normalization helpers for definition state
3. docs:
   - record registry rules, ownership rules, and blocked-state policy immediately

Recommended registry fields for business definitions:

1. `definition_id`
2. `label`
3. `description`
4. `owner`
5. `company_scope`
6. `entity_grain`
7. `time_basis`
8. `semantic_category`
9. `activation_state`
10. `source_of_truth`
11. `clarify_policy`
12. `blocked_reason`

Recommended registry fields for formulas:

1. `formula_id`
2. `definition_id`
3. `label`
4. `formula_type`
5. `input_metrics`
6. `input_requirements`
7. `source_capabilities`
8. `source_reports`
9. `aggregation_rule`
10. `grain_requirements`
11. `time_scope_requirements`
12. `activation_state`
13. `blocked_reason`

Recommended registry fields for thresholds:

1. `threshold_id`
2. `label`
3. `definition_id` or `formula_id`
4. `owner`
5. `company_scope`
6. `threshold_basis`
7. `bands`
8. `effective_from`
9. `activation_state`
10. `blocked_reason`

Required activation states:

1. `active`
2. `blocked_missing_policy`
3. `blocked_missing_data`
4. `draft_unapproved`
5. `deprecated`

Acceptance for `2.1`:

1. the assistant has explicit metadata homes for business definitions, formulas, and thresholds
2. undefined KPI meaning is no longer forced into code or prompt text
3. the runtime can tell the difference between:
   - not defined
   - defined but inactive
   - defined and active
4. this seam is testable deterministically

Current `2.1` checkpoint:

1. governed metadata homes now exist:
   - `business_definition_registry.json`
   - `governed_formula_registry.json`
   - `business_threshold_registry.json`
2. loader and accessor scaffolding now exists in [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
3. deterministic registry validation now exists in [business_definition_formula_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_formula_registry.py)
4. deterministic contract coverage now exists in [test_business_definition_formula_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_business_definition_formula_registry.py)
5. `2.1A` intentionally keeps registry entries empty until `2.2A` defines the first KPI candidates through governed metadata instead of placeholder business logic
6. `2.1B` now adds typed state resolution in [business_definition_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/business_definition_state.py)
7. the runtime can now distinguish deterministically between:
   - active definitions
   - blocked definitions
   - undefined definitions
   - ambiguous definitions
8. governed formula state now blocks safely when:
   - the parent definition is not active
   - multiple formulas exist for one definition
9. deterministic state-contract coverage now exists in [test_business_definition_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_business_definition_state.py)
10. callable seam verification now exists through `run_business_definition_state_probe`

### 7.2 `2.2` Core KPI Definitions

Goal:

1. encode the first KPI candidates through registries instead of informal team memory

Recommended treatment by KPI:

1. `tenure`
   - do not activate a naked `tenure` metric without approved basis
   - define explicit candidate variants:
     - customer creation date basis
     - first sales order basis
     - first sales invoice basis
   - if the business wants a generic `tenure`, the registry must map it to one approved variant
2. `average order value`
   - do not activate a generic `AOV` without document basis
   - separate candidates should exist for:
     - sales order basis
     - sales invoice basis
3. `collection ratio`
   - define numerator and denominator explicitly
   - do not allow one vague `collection ratio` to stand in for multiple possible finance meanings
4. `credit utilization`
   - define the intended ratio shape
   - keep it blocked until both credit-limit data and approved ratio basis exist

Policy choice for `2.2`:

1. Phase 2 may define a KPI without making it runtime-active
2. defined-but-blocked is a valid enterprise result

Why:

1. the purpose of Phase 2 is governed meaning first
2. pretending that all KPIs are executable immediately would be dishonest

Acceptance for `2.2`:

1. every KPI candidate has an owner and explicit basis
2. ambiguous KPI names do not silently activate
3. tenant-data-dependent KPIs can be represented safely without fake execution
4. no Python code hardcodes a company KPI definition directly

Current `2.2A` checkpoint:

1. first governed KPI entries are now active in:
   - [business_definition_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_definition_registry.json)
   - [governed_formula_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_formula_registry.json)
2. active KPI definitions now include:
   - average order value by sales order
   - average order value by sales invoice
   - customer credit utilization as of date
   - customer tenure by customer created date
   - customer tenure by first sales order
   - customer tenure by first sales invoice
   - collection ratio by sales invoice period
3. blocked KPI definitions now include:
   - none in the current governed KPI registry
4. the current governed runtime now resolves:
   - `average order value` as ambiguous until document basis is clarified
   - `tenure` as ambiguous until basis is clarified
   - `collection ratio` as defined and active
   - `credit utilization` as defined and active
5. customer-created tenure basis is now active through a governed customer-master source:
   - it resolves through `Customer Master List`
   - it does not replace or silently default generic tenure
6. deterministic verification now covers both registry validation and real-state resolution:
   - [test_business_definition_formula_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_business_definition_formula_registry.py)
   - [test_business_definition_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_business_definition_state.py)
7. callable seam verification now exists for the real Phase 2 registry content through:
   - `run_governed_kpi_registry_probe`

### 7.3 `2.3` Threshold And Risk Semantics

Goal:

1. govern threshold meaning before reasoning or advisory behavior widens

Recommended first threshold candidates:

1. overdue severity bands
2. customer credit-risk exposure bands
3. escalation-ready versus watch-only customer states

Important rule:

1. threshold bands must not become broad user-facing risk claims unless the underlying basis is both approved and executable

For example:

1. overdue severity can be defined now because AR aging already exists, but user-facing labels should still stay blocked until policy approval
2. credit-utilization-based policy bands can be active because the approved basis and tenant credit-limit data are now present

Acceptance for `2.3`:

1. threshold semantics are owned in metadata
2. risk labels cannot appear without an approved basis
3. recommendation language remains blocked unless later policy phases approve it

Current `2.3` checkpoint:

1. governed threshold semantics are now active in:
   - [business_threshold_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_threshold_registry.json)
2. company-specific business rules are now active in:
   - [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json)
3. active threshold set now exists for:
   - customer credit utilization policy bands
4. blocked threshold sets now exist for:
   - overdue severity labels pending policy approval
   - collection-ratio health bands pending policy approval
5. supporting threshold-ready metric basis was added for:
   - customer overdue ratio as of date
6. deterministic validation now covers:
   - threshold registry structure
   - business-rule registry structure
   - active threshold evaluation
   - blocked threshold behavior
7. callable seam verification now exists through:
   - `run_business_rule_registry_probe`
   - `run_business_threshold_semantics_probe`

### 7.4 `2.4` Formula Phase Closure

Goal:

1. close Phase 2 with registry-backed runtime behavior and honest blocked-safe semantics

Required closure outcomes:

1. registry loaders and accessors are active
2. at least the first KPI candidates are represented in governed metadata
3. runtime can respond safely when users ask for:
   - a defined and active KPI
   - a defined but blocked KPI
   - an undefined KPI
4. deterministic contract tests are green
5. docs and active baseline references are updated

Closure does not require:

1. all KPI candidates to be fully executable
2. composite artifact rollout
3. management advice or policy recommendations

Current `2.4` checkpoint:

1. registry-backed runtime behavior is now active through:
   - [governed_kpi_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_support.py)
   - [frontdoor_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py)
2. the runtime now answers governed KPI-definition asks safely for:
   - active KPI definitions
   - blocked KPI definitions
   - ambiguous KPI names that require basis clarification
   - explicit definition asks for undefined KPIs
3. `2.3` threshold semantics are now visible in the user-facing governed definition path:
   - credit-utilization threshold bands render as active policy notes
   - overdue severity labels remain blocked-safe until policy approval
   - collection-ratio health labels remain blocked-safe until policy approval
4. deterministic coverage now includes:
   - [test_governed_kpi_frontdoor.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_frontdoor.py)
   - release-gate promotion in [test_post_contract_release_gates.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_post_contract_release_gates.py)
5. callable and live verification now exist through:
   - `run_governed_kpi_frontdoor_probe`
   - `run_phase2_4_governed_kpi_frontdoor_smoke`

## 8. Runtime Integration Strategy

Phase 2 should integrate with the current runtime in the smallest safe way.

Recommended first integration pattern:

1. registry lookup resolves KPI state before narrative freedom
2. active KPI definitions may later feed governed runtime execution when source authority is already proven
3. blocked or ambiguous definitions should produce deterministic clarify or block behavior

This means the first runtime usage may be:

1. semantic resolution support
2. governed clarification support
3. blocked-safe answer policy for undefined metrics

It does not need to become:

1. a full formula-computation engine in the first slice

## 9. Verification Strategy

Minimum deterministic coverage should include:

1. registry schema load and accessor behavior
2. active versus blocked definition-state handling
3. blocked-safe response behavior for undefined KPIs
4. owner, grain, and source-authority validation
5. no direct code-path formula constants for governed KPIs
6. parent-definition blocking for formula resolution
7. ambiguous formula-state handling when multiple variants remain approved in metadata

Live or site-backed verification should include bounded asks such as:

1. a KPI that is active and executable
2. a KPI that is defined but blocked by missing tenant data
3. a KPI whose name is ambiguous and should clarify or stop safely

## 10. Stop Rule

Stop Phase 2 when:

1. the registries exist and are active
2. first KPI candidates are represented honestly
3. blocked-safe semantics are deterministic
4. the runtime no longer needs prompt memory or code comments to know what a KPI means

Do not widen Phase 2 into:

1. composite joins
2. broad advisory behavior
3. HR expansion
4. another operational family

Those belong later.

## 11. Current Recommendation

The approved starting move should be:

1. `2.1A` registry metadata and loader scaffolding
   - complete
2. `2.1B` typed definition-state contracts
   - complete
3. `2.2A` first KPI definition entries with honest activation states
   - complete
4. `2.3` threshold and risk semantics
   - complete
5. `2.4` formula phase closure
   - complete

That is the safest enterprise-grade way to adapt Phase 2 to the current assistant ecosystem.
