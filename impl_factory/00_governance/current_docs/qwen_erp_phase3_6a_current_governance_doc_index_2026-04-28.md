# Qwen ERP Phase 3.6A Current Governance Documentation Index

Status: implemented as documentation-control baseline
Date: 2026-04-28
Scope: current source-of-truth map for AI assistant governance docs before Phase 3.6 quality gate execution and Phase 4 planning.

## 1. Purpose

This index exists because the project has accumulated many useful planning, research, design, refactor, and closure notes.

That history is valuable, but it is now hard to tell which docs are current direction, which docs are completed phase records, and which docs are historical research context.

Phase 3.6A creates a safer documentation baseline before Phase 4.

## 2. Current Executive Read Order

For current AI assistant work, read these first:

1. `qwen_erp_phase3_6_release_readiness_and_quality_exit_gate_2026-04-28.md`
2. `qwen_erp_phase3_6a_current_governance_doc_index_2026-04-28.md`
3. `qwen_erp_phase3_6a_archive_candidate_map_2026-04-28.md`
4. `qwen_erp_phase3_6b_business_question_quality_matrix_2026-04-28.md`
5. `qwen_erp_phase3_6c_automated_quality_gate_harness_2026-04-28.md`
6. `qwen_erp_phase3_6d0_full_capability_inventory_and_uat_coverage_map_2026-04-29.md`
7. `qwen_erp_governed_scope_activation_and_cross_family_alignment_roadmap_2026-04-13.md`
8. `qwen_erp_phase_g_live_uat_gate_2026-04-25.md`
9. `qwen_erp_phase3_5h_recommendation_boundary_closure_evaluation_2026-04-28.md`
10. `qwen_erp_phase3_4f_customer_risk_uat_guardrails_2026-04-27.md`
11. `qwen_erp_enterprise_development_guidelines_2026-04-04.md`
12. `qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md`

Use older phase design notes only when the current index or roadmap points to them.

## 3. Current Program State

The current documented state is:

1. Phase 3.4 Customer Risk-As-Of composite archetype is complete for the current delivery chapter.
2. Phase 3.5 reasoning authority, driver-analysis boundary, recommendation policy scaffold, execution gate, runtime guard, observability, and closure matrix are complete for the blocked-authority safety chapter.
3. Governed scope activation has completed the current D/E/F/G registry and contract readiness chapter for the approved active scopes.
4. G4 live/UAT gate has been prepared and partly executed, with major blockers corrected and documented.
5. Phase 3.6 is now the active bridge milestone before Phase 4, and 3.6C has an executable quality-gate registry for the required `A` rows.
6. Phase 3.6D-0 full capability inventory and UAT coverage mapping is required before manual browser UAT, so the manual pack covers the full implemented assistant surface.
7. Phase 4 Complex Business Question Decomposition must not start until Phase 3.6 quality exit gate passes.

## 4. Active Roadmap Docs

### 4.1 Current Bridge Milestone

`qwen_erp_phase3_6_release_readiness_and_quality_exit_gate_2026-04-28.md`

Role:

1. active bridge milestone
2. defines documentation cleanup, question matrix design, automated replay, manual UAT, wise fallback, and Phase 4 entry gate

Status:

1. active
2. start with `3.6A` and `3.6B`

### 4.1.1 Current Archive Candidate Map

`qwen_erp_phase3_6a_archive_candidate_map_2026-04-28.md`

Role:

1. non-destructive archive/read-status classification
2. identifies active docs, completed records, historical research stacks, and duplicate candidates
3. prevents old docs from being mistaken for current implementation authority

Status:

1. active documentation-control companion to this index
2. does not authorize deleting or moving files

### 4.1.2 Current Business-Question Quality Matrix

`qwen_erp_phase3_6b_business_question_quality_matrix_2026-04-28.md`

Role:

1. current Phase 3.6 quality matrix
2. groups assistant questions by master data, transaction listings, financial statements, composite/KPI evidence, follow-up/context, wise fallback, and presentation quality
3. defines gate level and execution mode for each question row

Status:

1. active QA design
2. input to Phase `3.6C` automated replay/smoke work
3. input to Phase `3.6D` manual browser UAT checklis

### 4.1.3 Current Automated Quality Gate Harness

`qwen_erp_phase3_6c_automated_quality_gate_harness_2026-04-28.md`

Role:

1. documents the executable quality-gate registry
2. maps every required Phase 3.6 `A` row to business-user aspect, automation layer, fallback/boundary requirement, and existing coverage refs
3. prevents the Phase 3.6B matrix from becoming stale documentation

Status:

1. active QA implementation
2. backed by `ai_assistant_ui/qwen_chat/evaluation/phase36_quality_gate.py`
3. validated by `ai_assistant_ui/tests/test_phase36_quality_gate.py`
4. input to Phase `3.6D` manual browser UAT execution

### 4.1.4 Current Full Capability Inventory And UAT Coverage Map

`qwen_erp_phase3_6d0_full_capability_inventory_and_uat_coverage_map_2026-04-29.md`

Role:

1. full-project coverage-control layer before browser UAT
2. maps Phase 3.6D manual browser testing to the implemented capability, report, scope, family, composite, KPI, and historical release-gate surfaces
3. prevents recent-conversation bias in the manual UAT pack

Status:

1. active QA design companion to Phase `3.6B` and `3.6C`
2. required input to Phase `3.6D` manual browser UAT checklis
3. confirms Phase 3.6B/3.6C remain valid as a minimum exit pack, not the whole-project UAT surface

### 4.2 Current Scope-Activation Baseline

`qwen_erp_governed_scope_activation_and_cross_family_alignment_roadmap_2026-04-13.md`

Role:

1. source of truth for governed scope activation, cross-family compatibility, D/E/F/G checkpoints, and active scope inventory
2. current approved active scope baseline includes customer, supplier, item, sales invoice, purchase invoice, delivery note, sales order, purchase order, purchase receipt, and payment entry

Status:

1. current baseline
2. scope activation chapter is closed for registry/contract readiness
3. use it as guardrail during Phase 3.6 and Phase 4

### 4.3 Current Live/UAT Gate

`qwen_erp_phase_g_live_uat_gate_2026-04-25.md`

Role:

1. release-style browser/UAT gate for activated scopes
2. covers master-data discovery/detail, transaction listings, financial statements, context control, lifecycle/event follow-up, unsupported/fail-closed behavior, and live data freshness

Status:

1. active release-gate reference
2. use as input to Phase 3.6 manual UAT matrix

### 4.4 Current Product Roadmap Reference

`qwen_erp_phase_implementation_roadmap_2026-04-04.md`

Role:

1. macro product roadmap from Phase 1 through Phase 8
2. still useful for phase ordering and Phase 4 definition

Status:

1. historical macro roadmap
2. current status inside this doc is older than the latest Phase 3.4/3.5/3.6 work
3. do not use it alone to decide current next work

## 5. Completed Phase Records To Keep Discoverable

These are completed or near-closure records that should remain easy to find during Phase 3.6.

### 5.1 Phase 3.4 Customer Risk

1. `qwen_erp_phase3_4_customer_risk_as_of_composite_design_2026-04-25.md`
2. `qwen_erp_phase3_4f_customer_risk_uat_guardrails_2026-04-27.md`

Current use:

1. regression and UAT reference for customer-risk evidence, selected-row follow-up, aging breakdown, context switching, and unsupported recommendation/prediction boundaries

### 5.2 Phase 3.5 Reasoning Boundary

1. `qwen_erp_phase3_5a_reasoning_authority_boundary_2026-04-28.md`
2. `qwen_erp_phase3_5b_driver_analysis_boundary_2026-04-28.md`
3. `qwen_erp_phase3_5c_recommendation_policy_artifact_scaffold_2026-04-28.md`
4. `qwen_erp_phase3_5d_recommendation_policy_activation_gate_2026-04-28.md`
5. `qwen_erp_phase3_5e_recommendation_execution_contract_2026-04-28.md`
6. `qwen_erp_phase3_5f_recommendation_runtime_guard_2026-04-28.md`
7. `qwen_erp_phase3_5g_recommendation_observability_surface_2026-04-28.md`
8. `qwen_erp_phase3_5h_recommendation_boundary_closure_evaluation_2026-04-28.md`

Current use:

1. authority boundary reference for evidence explanation, driver explanation, blocked causal analysis, blocked prediction, blocked recommendation, and execution-gate observability

### 5.3 Service Refactor And Conversation Control

1. `qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md`
2. `qwen_erp_service_py_refactor_sr0_baseline_2026-04-22.md`
3. `conversation_control/qwen_erp_conversation_control_miniphase_and_slice_status_update_2026-04-20.md`
4. `conversation_control/qwen_erp_conversation_control_post_design_implementation_roadmap_2026-04-18.md`

Current use:

1. reference for avoiding new `service.py` gravity
2. reference for conversation-control spine decisions
3. not the active roadmap unless Phase 3.6 exposes a concrete service or control regression

## 6. Stable Enterprise Baseline Docs

Keep these available as policy/baseline references:

1. `qwen_erp_enterprise_development_guidelines_2026-04-04.md`
2. `qwen_erp_enterprise_blueprint_2026-03-19.md`
3. `qwen_erp_enterprise_tech_debt_register_2026-04-04.md`
4. `qwen_erp_deferred_implementation_register_2026-04-09.md`
5. `qwen_erp_overdue_severity_policy_pack_2026-04-10.md`
6. `qwen_erp_post_contract_expansion_backlog_2026-03-25.md`

Current use:

1. architecture standards
2. deferred work memory
3. policy boundaries
4. known technical debt contex

## 7. Historical Or Archive Candidates

No files are physically moved in this slice.

These should be treated as archive candidates or historical context until a dedicated archive step moves them.

### 7.1 Phase 3 Entity Lookup Research Stack

Folder:

`phase3_entity_lookup_scope/`

Reason:

1. the research stack fed the governed scope activation roadmap
2. the active decisions now live in the top-level governed scope roadmap
3. the folder remains useful as research evidence, but it is not the current execution guide

Recommendation:

1. keep the folder intact for now
2. folder README is now marked as historical research during `3.6A-2`
3. optionally move it under an archive/research folder only after Phase 3.6 exit gate passes and the team approves physical movemen

### 7.2 Older Operational Phase Design Notes

Examples:

1. `qwen_erp_phase1_1_delivery_fulfillment_design_2026-04-04.md`
2. `qwen_erp_phase1_2_sales_order_status_design_2026-04-08.md`
3. `qwen_erp_phase1_3_purchase_order_tracking_design_2026-04-08.md`
4. `qwen_erp_phase1_4_customer_credit_status_design_2026-04-09.md`
5. `qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md`

Reason:

1. useful as completed phase history
2. not current execution direction

Recommendation:

1. keep accessible as completed records
2. do not use as current next-step authority unless Phase 3.6 exposes a regression tied to those surfaces

### 7.3 Phase 2 And Phase 2.5 Design Notes

Examples:

1. `qwen_erp_phase2_business_definition_formula_registry_design_2026-04-09.md`
2. `qwen_erp_phase2_5_governed_kpi_runtime_execution_design_2026-04-10.md`

Reason:

1. these define important lower-level registry/runtime history
2. they are baseline context, not current feature direction

Recommendation:

1. keep as baseline reference
2. avoid reopening unless Phase 3.6 or Phase 4 exposes a concrete KPI/formula authority issue

### 7.4 Duplicate Service Refactor Guidance Copy

Candidate:

`conversation_control/qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md`

Reason:

1. root-level `qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md` should be the preferred active reference
2. duplicate copies can drif

Recommendation:

1. root-level copy has `939` lines
2. conversation-control copy has `499` lines
3. checksums differ
4. root-level copy is the active reference for future implementation
5. do not delete or move either copy in `3.6A`
6. treat the shorter conversation-control copy as a duplicate candidate for a later archive step
7. compare for unique historical notes before any physical archive movemen

## 8. Current Phase 3.6A Decision

Phase 3.6A current decision is:

1. create this current documentation index
2. refresh the root README so this index is the first read
3. add a non-destructive archive-candidate map
4. mark the Phase 3 entity lookup research folder as historical contex
5. do not physically move docs ye
6. `3.6B` business-question matrix design is now available as the current QA design
7. proceed next to `3.6C` automated replay/smoke harness design

Recommended next step:

1. keep all docs physically in place during the quality gate
2. use this index and the archive-candidate map for navigation
3. start `3.6C` automated replay/smoke harness design from the `A` gate rows in the question matrix
4. only consider physical archive movement after Phase 3.6 exit-gate results are known

## 9. Phase 4 Guardrail

Phase 4 should not begin until:

1. Phase 3.6 docs are organized enough for future review
2. the business-question matrix exists
3. automated checks and manual browser UAT pass the exit gate
4. fallback behavior is proven across ambiguity, uncertainty, unsupported scope, unsupported authority, and context switching
