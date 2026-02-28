# Phase 1 First-Run Baseline Score

- Executed: 2026-02-23T18:07:45Z
- Label: phase6_manifest_resume
- Input artifacts: 5

## First-Run Policy
- Enforced: True
- Source: earliest_result_per_case_id
- Selected cases: 385
- Ignored duplicate results: 0

## KPI Summary
- Total cases scored: 385
- Pass count: 352
- Fail count: 33
- First-run pass rate: 0.9143
- Direct-answer rate (clear): 0.8947
- Clarification rate (clear): 0.1053
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Clarification loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- User correction rate: 0.0
- Write safety incidents: 0
- Latency p95 ms (clear): 13715

## Behavior Class Coverage
- Cases with behavior class labels: 385
- Distinct behavior classes observed: 14
- Target mandatory classes: 9
- Target class coverage: 1.0
- Missing target classes: -

## Manifest
- Path: /home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7_expanded/manifest.json
- Total expected cases: 385

## First-Run Pass Rate by Behavior Class
- clarification_blocker: 1.0
- comparison: 1.0
- context_topic_switch: 0.9667
- correction_rebind: 1.0
- detail_projection: 0.6571
- entity_disambiguation_followup: 0.9667
- error_envelope: 1.0
- kpi_aggregate: 1.0
- list_latest_records: 0.6
- observability_contract: 1.0
- ranking_top_n: 0.8
- transform_last_result: 1.0
- trend_time_series: 0.85
- write_safety: 1.0

## Input Artifacts
- `impl_factory/04_automation/logs/20260223T135049Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260223T151102Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260223T164821Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260223T172616Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260223T180745Z_phase6_manifest_uat_raw_v3.json`
