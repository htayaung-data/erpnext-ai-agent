# Qwen ERP Governed Scope Coverage Research Plan

Status: active research plan
Date: 2026-04-12
Scope: phase-by-phase enterprise research plan to map actual governed AI Assistant coverage before further scope expansion or seam generalization

## 1. Purpose

This note defines the practical research plan we will use before further governed-scope expansion.

It exists to prevent three bad behaviors:

1. guessing coverage from one or two browser prompts
2. treating `data exists in ERP` as `governed contract exists`
3. fixing one entity or one prompt path without understanding the larger system seam

The plan is meant to answer, with evidence:

1. what is already implemented
2. what is already active end to end
3. what is only partially wired
4. what is available in one contract family but missing in another
5. what should be prioritized nex

This plan is research first, design second, implementation third.

## 2. Working Principles

The research itself must follow the same enterprise rules as implementation.

1. no guessing
2. no estimate-as-fac
3. repo evidence firs
4. runtime truth second
5. browser/UAT only after code-level mapping
6. distinguish declared from active
7. distinguish active from safe
8. distinguish safe from generalized

Important rule:

If a capability appears to exist, we must still classify whether it is:

1. metadata-declared only
2. contract-wired
3. runtime-executable
4. renderer-supported
5. follow-up-safe

## 3. Research Output Structure

The research chapter should produce a set of Markdown notes, not one giant dump.

Required outputs:

1. one phase note per research phase
2. one cumulative governed coverage matrix
3. one gap and priority note
4. one implementation design note only after research closure

Suggested final artifact set:

1. `qwen_erp_governed_scope_coverage_phase0_baseline_YYYY-MM-DD.md`
2. `qwen_erp_governed_scope_coverage_phase1_frontdoor_inventory_YYYY-MM-DD.md`
3. `qwen_erp_governed_scope_coverage_phase2_contract_runtime_matrix_YYYY-MM-DD.md`
4. `qwen_erp_governed_scope_coverage_phase3_behavior_truthing_YYYY-MM-DD.md`
5. `qwen_erp_governed_scope_coverage_phase4_gap_priority_YYYY-MM-DD.md`
6. `qwen_erp_governed_scope_coverage_matrix_YYYY-MM-DD.md`
7. `qwen_erp_governed_scope_expansion_design_YYYY-MM-DD.md`

The date suffix can be finalized when each phase is written.

## 4. Research Questions

These are the core questions the research must answer.

### 4.1 Front Door

1. Which user request shapes are already recognized by the front door?
2. Which intent classes are already active?
3. Which slots are already normalized by metadata?
4. Which valid ERP asks still fall through to weak or generic handling?

### 4.2 Contract Surface

1. Which contract families already support customer?
2. Which already support supplier?
3. Which already support item or product?
4. Which support document entities such as invoice, order, or delivery note?
5. Which families already support deictic follow-up?
6. Which families already support profile or detail drilldown?

### 4.3 Metadata Surface

1. What is already declared in registries?
2. What is active versus blocked versus partial?
3. Where are the seams uneven across entities?
4. Where is the metadata richer than runtime?
5. Where is runtime richer than metadata?

### 4.4 Runtime Truth

1. Which declared capabilities are actually executable?
2. Which executable paths render correctly?
3. Which rendered paths preserve context correctly?
4. Which paths fail closed correctly?

### 4.5 Expansion Readiness

1. Which missing behaviors are truly missing?
2. Which missing behaviors are really just missing handoff or activation?
3. Which next expansion can reuse the most existing infrastructure?
4. Which expansion would create architecture drift if done too early?

## 5. Research Scope Model

The analysis should not be organized only by files.

It should be organized by governed scope.

Recommended scope groups:

1. entity navigation
   - customer
   - supplier
   - item or produc
   - warehouse
   - sales person
   - territory
2. document navigation
   - sales invoice
   - purchase invoice
   - sales order
   - purchase order
   - delivery note
   - payment entry
3. analytical scopes
   - ranking
   - trend
   - KPI
   - composite
   - aging
   - inventory
4. evidence and detail scopes
   - profile
   - lifecycle
   - credi
   - overdue
   - first activity
5. continuation scopes
   - deictic follow-up
   - projection change
   - time correction
   - subject switch
   - fresh breakou

## 6. Phase-By-Phase Research Plan

## 6.1 Phase 0: Baseline And Rules Alignmen

Goal:

1. establish the authoritative docs
2. establish the research taxonomy
3. define the evidence standards before deeper inspection

Key questions:

1. what do the governing docs say the current phase owns?
2. what are the current do-not-cross boundaries?
3. what counts as active support versus partial support?

Primary sources:

1. enterprise development guidelines
2. phase implementation roadmap
3. active Phase `3` design notes
4. latest enterprise evaluation note

Required output:

1. one baseline note summarizing:
   - active docs
   - active phase ownership
   - research taxonomy
   - evidence standards

Exit criteria:

1. the team agrees on what counts as:
   - declared
   - active
   - verified
   - generalized

## 6.2 Phase 1: Front-Door And Metadata Inventory

Goal:

1. inventory what the assistant claims to support at the front door
2. map those claims to metadata

What to inspect:

1. frontdoor intent registry
2. semantic resolution registry
3. capability registry
4. report registry
5. report family registry
6. entity reference policy registry
7. composite family and artifact registries

Questions to answer:

1. what intent classes exist?
2. what entity or domain slots exist?
3. what family-resolution rules exist?
4. what capabilities are mapped to which intent classes?
5. where do customer, supplier, and item appear?
6. where do they appear only in analytics but not navigation?

Required output:

1. front-door inventory note
2. initial coverage matrix draf

Exit criteria:

1. every major ERP scope is classified as:
   - present in metadata
   - absent in metadata
   - present only in another family

## 6.3 Phase 2: Contract And Runtime Seam Mapping

Goal:

1. map the actual runtime consumers of those registries
2. identify where behavior is shared versus one-off

What to inspect:

1. fresh query interpreter
2. semantic resolution runtime
3. family adapters
4. family rendering
5. entity detail
6. follow-up interpreter
7. continuation suppor
8. artifact boundary lane
9. entity drilldown lane
10. recovery and clarification seams

Questions to answer:

1. which metadata entries are actually consumed?
2. where does runtime still branch by entity type directly?
3. where does the system already use shared typed seams?
4. where are there uneven handoffs across entity types?
5. where does customer get a path that supplier or item does not?

Required output:

1. contract/runtime seam map
2. list of customer-only, supplier-only, and item-only branches
3. list of shared seams already suitable for generalization

Exit criteria:

1. every major scope can be linked to:
   - metadata entry
   - contract seam
   - runtime consumer
   - renderer or detail consumer

## 6.4 Phase 3: Behavior Truthing

Goal:

1. verify which seams are real in execution, not only in code structure
2. classify behavior-level maturity

Method:

1. targeted unit and contract tests
2. targeted probes
3. narrow browser/UAT prompts only after code-level mapping

Questions to answer:

1. which paths are green in tests?
2. which paths are green only in one contract family?
3. which paths fail at handoff boundaries?
4. which paths fail because of missing metadata activation?
5. which paths fail because of stale artifact reuse?

Required output:

1. behavior truth note
2. scope-by-scope verification table

Exit criteria:

1. each scope is classified as one of:
   - active and verified
   - active but inconsisten
   - partial
   - declared only
   - missing

## 6.5 Phase 4: Gap Classification And Priority

Goal:

1. convert the research into an implementation priority order

Gap categories:

1. declared but not consumed
2. consumed but not rendered correctly
3. rendered but not continuation-safe
4. active in one family but missing in another
5. truly missing governed source

Priority factors:

1. business value
2. reuse potential
3. architecture safety
4. amount of existing infrastructure already presen
5. risk of regression

Required output:

1. gap and priority note

Exit criteria:

1. top-priority next seam is chosen with evidence
2. lower-priority gaps are explicitly deferred, not forgotten

## 6.6 Phase 5: Implementation Design Preparation

Goal:

1. write the implementation design only after research closure

The design note should answer:

1. what exact seam will be generalized
2. what existing contracts will be reused
3. what metadata changes are required
4. what runtime files will change
5. what tests will prove the change
6. what should remain deferred

Important:

Implementation design must be based on the coverage matrix, not on whichever prompt failed most recently.

Required output:

1. implementation design note

Exit criteria:

1. the design identifies:
   - keep
   - reuse
   - extend
   - defer
   - remove

## 7. Governed Coverage Matrix Design

The matrix should be one of the main deliverables.

Each row should represent one governed scope.

Suggested columns:

1. scope id
2. business scope label
3. entity or domain
4. front-door intent coverage
5. metadata coverage
6. fresh-query suppor
7. detail or profile suppor
8. ranking or KPI suppor
9. continuation safety
10. renderer quality
11. verification status
12. current classification
13. main gap
14. recommended next action

Recommended classifications:

1. `active_verified`
2. `active_inconsistent`
3. `partial`
4. `declared_only`
5. `missing`

## 8. Practical Execution Order

To keep the work manageable, the research should not attempt to answer everything in one pass.

Recommended practical order:

1. customer
2. supplier
3. item or produc
4. document entities
5. analytical families
6. continuation and handoff cross-check

Reason:

1. customer is the most mature and gives the baseline
2. supplier often exists in aging and detail seams
3. item or product often exists in ranking and performance seams
4. comparing these three will reveal where the contract surface is uneven

## 9. Stop Rules

The research should stop and escalate before design if any of these are true:

1. the same scope is implemented through two conflicting authority models
2. a proposed next step would require bypassing existing contracts
3. a proposed next step would force prompt-led business logic
4. the system is relying on one entity-specific branch that should really be shared
5. metadata and runtime disagree so heavily that design would be premature

## 10. Immediate Recommendation

The first research execution tranche should be:

1. Phase 0 baseline
2. Phase 1 metadata inventory
3. Phase 2 contract/runtime seam mapping

for these scopes only:

1. customer
2. supplier
3. item or produc

Why this is the right first tranche:

1. it is small enough to complete carefully
2. it directly addresses the current uncertainty
3. it will tell us whether the current customer path is reusable or too narrow
4. it will show whether supplier and item are missing, partial, or simply disconnected from the current seam

## 11. Final Research Principle

The point of this plan is not to prove that the system is weak.

The point is to identify exactly where the system is already strong, where it is uneven, and how to expand it without architecture drift.

The correct outcome is not:

1. more patches

The correct outcome is:

1. researched truth
2. reusable design
3. bounded implementation
