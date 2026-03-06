## Spec Pipeline Contract Hardening Status

Date: 2026-03-06  
Owner: AI Runtime Engineering  
Scope: bounded hardening to reduce parser-level business keyword gating in `spec_pipeline.py` for approved `contribution_share` / `threshold_exception_list` behavior

### Why This Slice Was Opened

Previous contract audit identified open debt in parser-level business gating:

1. [step18_contribution_share_contract_audit_trace_2026-03-05.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step18_contribution_share_contract_audit_trace_2026-03-05.md)

Goal of this slice:

1. move class-boundary dimension rules and threshold metric default rules into contract data
2. consume those rules via contract-registry accessors
3. remove direct threshold-keyword trigger dependency in parser path

### Files Changed In This Slice

1. [spec_contract_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/spec_contract_v1.json)
2. [contract_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contract_registry.py)
3. [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)
4. [test_v7_spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_spec_pipeline.py)

### What Was Explicitly Not Changed

1. no prompt-to-report maps
2. no case-ID logic
3. no runtime report-name keyword routing
4. no expansion of class scope beyond approved first slices

### Validation Evidence

Local/unit:

1. `python3 -m unittest impl_factory.04_automation.bench_scripts.test_v7_contract_registry` -> pass
2. `python3 -m unittest impl_factory.04_automation.bench_scripts.test_v7_spec_pipeline` -> pass
3. `python3 -m unittest impl_factory.04_automation.bench_scripts.test_v7_read_engine_clarification` -> pass

Replay:

1. full `contribution_share` suite pass:
   - [20260306T095108Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T095108Z_phase6_manifest_uat_raw_v3.json)
2. targeted impacted multiturn/transform probes pass:
   - [20260306T095303Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T095303Z_phase6_manifest_uat_raw_v3.json) (`STK-03`)
   - [20260306T095431Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T095431Z_phase6_manifest_uat_raw_v3.json) (`LST-01__v018`)
   - [20260306T095602Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T095602Z_phase6_manifest_uat_raw_v3.json) (`DET-01__v019`)
3. targeted threshold probes pass:
   - [20260306T101242Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T101242Z_phase6_manifest_uat_raw_v3.json) (`TEI-01`)
   - [20260306T101352Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260306T101352Z_phase6_manifest_uat_raw_v3.json) (`TEU-01`)
4. focused browser/manual smoke checks (fresh-chat where required):
   - `Show contribution share` -> clarification question shown
   - `Show contribution share of total revenue` -> clarification question shown
   - `Show revenue share by territory last month` -> safe unsupported response shown
   - `Show customers above threshold` (fresh chat) -> clarification question shown

### Remaining Gate Items Before Closure

1. attach broad Phase-3 rerun evidence on `main` per rerun checklist:
   - `core_read` full suite
   - `multiturn_context` full suite
2. sync this hardening merge to remote `main` after rerun evidence is attached

### Current Decision

Status: `provisionally-green-with-final-rerun-gate-open`  
Reason: targeted replay + manual evidence are green, branch is pushed, and local `main` includes merge commit `52d196f`; final closure needs explicit broad rerun evidence on `main`.
