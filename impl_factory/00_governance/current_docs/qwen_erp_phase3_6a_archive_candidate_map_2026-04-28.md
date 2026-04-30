# Qwen ERP Phase 3.6A Archive Candidate Map

Status: implemented as non-destructive archive map
Date: 2026-04-28
Scope: archive/read-status classification for current governance docs before Phase 3.6 quality-gate execution.

## 1. Purpose

This map prevents documentation confusion without losing history.

It does not move, delete, or rewrite old planning documents. It classifies them so future review can start from current source-of-truth docs while still preserving the reasoning that led here.

## 2. Archive Policy

Use these rules:

1. `active`: current implementation or release-gate authority.
2. `current baseline`: stable policy or architecture reference used by active work.
3. `completed record`: completed phase history that may be needed for regression or UAT context.
4. `historical research`: research evidence that fed a later roadmap but is no longer the execution guide.
5. `archive candidate`: safe to move later after team review, but not moved in this slice.
6. `duplicate candidate`: potentially superseded copy that must be compared before archiving.

No physical archive movement is approved by this file.

## 3. Active Docs

These should remain in the top-level current read path.

| Doc | Status | Reason |
| --- | --- | --- |
| `qwen_erp_phase3_6_release_readiness_and_quality_exit_gate_2026-04-28.md` | active | Current bridge milestone before Phase 4. |
| `qwen_erp_phase3_6a_current_governance_doc_index_2026-04-28.md` | active | Current source-of-truth doc index. |
| `qwen_erp_governed_scope_activation_and_cross_family_alignment_roadmap_2026-04-13.md` | current baseline | Latest scope activation, E/F/G closure, and active scope inventory. |
| `qwen_erp_phase_g_live_uat_gate_2026-04-25.md` | active release-gate reference | Live/browser UAT baseline for activated scopes. |
| `qwen_erp_enterprise_development_guidelines_2026-04-04.md` | current baseline | Enterprise development rules. |
| `qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md` | current baseline | Active service facade/refactor guidance. |

## 4. Completed Records To Keep Discoverable

These should remain easy to find during Phase 3.6.

| Doc Or Group | Status | Reason |
| --- | --- | --- |
| `qwen_erp_phase3_4_customer_risk_as_of_composite_design_2026-04-25.md` | completed record | Customer Risk design and activation record. |
| `qwen_erp_phase3_4f_customer_risk_uat_guardrails_2026-04-27.md` | completed record | Customer Risk UAT and selected-row evidence guardrails. |
| `qwen_erp_phase3_5a_*` through `qwen_erp_phase3_5h_*` | completed record | Reasoning authority, driver, recommendation boundary, execution gate, and closure matrix. |
| `qwen_erp_service_py_refactor_sr0_baseline_2026-04-22.md` | completed record | Service refactor baseline and metrics. |
| `conversation_control/qwen_erp_conversation_control_miniphase_and_slice_status_update_2026-04-20.md` | completed record | Conversation-control implementation truth snapshot. |
| `conversation_control/qwen_erp_conversation_control_post_design_implementation_roadmap_2026-04-18.md` | completed record | Conversation-control design/implementation roadmap. |

## 5. Historical Research Stack

### 5.1 Phase 3 Entity Lookup Scope Folder

Folder:

`phase3_entity_lookup_scope/`

Status:

`historical research`

Reason:

1. this folder contains the Phase 3.3 entity lookup and governed scope research stack
2. the output of that research is now represented in the top-level governed scope activation roadmap
3. it should not be treated as the current execution guide

Recommended future action:

1. keep intact for now
2. mark folder README as historical research
3. optionally move to `archive_docs/research/phase3_entity_lookup_scope/` only after Phase 3.6 exit gate passes

## 6. Older Completed Phase Docs

Status:

`completed record`

Examples:

1. `qwen_erp_phase1_1_delivery_fulfillment_design_2026-04-04.md`
2. `qwen_erp_phase1_2_sales_order_status_design_2026-04-08.md`
3. `qwen_erp_phase1_3_purchase_order_tracking_design_2026-04-08.md`
4. `qwen_erp_phase1_4_customer_credit_status_design_2026-04-09.md`
5. `qwen_erp_phase1_5_operational_phase_closure_2026-04-09.md`
6. `qwen_erp_phase2_business_definition_formula_registry_design_2026-04-09.md`
7. `qwen_erp_phase2_5_governed_kpi_runtime_execution_design_2026-04-10.md`
8. `qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md`

Reason:

1. valuable implementation history
2. not the current next-step authority
3. useful when Phase 3.6 detects a regression in those surfaces

Recommended future action:

1. leave in place until Phase 3.6 exit gate is complete
2. later group into completed-phase archive folders by phase if desired

## 7. Duplicate Candidate

Candidate:

`conversation_control/qwen_erp_service_py_refactor_and_delivery_guidance_2026-04-20.md`

Status:

`duplicate candidate`

Observed comparison:

1. root-level service guidance exists and is longer
2. conversation-control copy exists and is shorter
3. checksums are differen
4. root-level copy should be treated as the active reference

Recommended future action:

1. do not delete either file now
2. during a later archive step, compare the shorter copy against the root active copy
3. if it contains no unique current guidance, move the shorter copy to archive

## 8. Docs That Should Not Be Archived Ye

Do not archive these during Phase 3.6A:

1. current root `README.md`
2. Phase 3.6 docs
3. governed scope activation roadmap
4. Phase G live UAT gate
5. Phase 3.4F and Phase 3.5H closure/guardrail docs
6. enterprise development guidelines
7. active root service-refactor guidance
8. deferred implementation and tech debt registers

## 9. Recommended Next Documentation Step

After this map:

1. keep all files physically in place
2. use this map and the root README for navigation
3. move to Phase `3.6B` business-question matrix design
4. postpone physical archive movement until after Phase 3.6 exit-gate results are known
