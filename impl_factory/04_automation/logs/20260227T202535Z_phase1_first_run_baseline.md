# Phase 1 First-Run Baseline Score

- Executed: 2026-02-27T20:25:35Z
- Label: phase6_manifest_full
- Input artifacts: 5

## First-Run Policy
- Enforced: True
- Source: earliest_result_per_case_id
- Selected cases: 385
- Ignored duplicate results: 0

## KPI Summary
- Total cases scored: 385
- Pass count: 350
- Fail count: 35
- First-run pass rate: 0.9091
- Direct-answer rate (clear): 0.9474
- Clarification rate (clear): 0.0526
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Clarification loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- User correction rate: 0.0
- Write safety incidents: 0
- Latency p95 ms (clear): 12372

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
- context_topic_switch: 1.0
- correction_rebind: 1.0
- detail_projection: 1.0
- entity_disambiguation_followup: 0.9667
- error_envelope: 1.0
- kpi_aggregate: 1.0
- list_latest_records: 0.9667
- observability_contract: 1.0
- ranking_top_n: 0.9
- transform_last_result: 0.5738
- trend_time_series: 1.0
- write_safety: 0.9194

## Input Artifacts
- `impl_factory/04_automation/logs/20260227T165533Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T181158Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T190828Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T194428Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T202535Z_phase6_manifest_uat_raw_v3.json`
