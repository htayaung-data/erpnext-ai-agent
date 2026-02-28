# Phase 1 First-Run Baseline Score

- Executed: 2026-02-23T04:54:00Z
- Label: p1_baseline_r4
- Input artifacts: 1

## First-Run Policy
- Enforced: True
- Source: earliest_result_per_case_id
- Selected cases: 28
- Ignored duplicate results: 0

## KPI Summary
- Total cases scored: 28
- Pass count: 28
- Fail count: 0
- First-run pass rate: 1.0
- Direct-answer rate (clear): 0.9375
- Clarification rate (clear): 0.0625
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Clarification loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- User correction rate: 0.0
- Write safety incidents: 0
- Latency p95 ms (clear): 11809

## Behavior Class Coverage
- Cases with behavior class labels: 28
- Distinct behavior classes observed: 12
- Target mandatory classes: 9
- Target class coverage: 0.7778
- Missing target classes: comparison, trend_time_series

## Manifest
- Path: /home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/replay_v7/manifest.json
- Total expected cases: 28

## First-Run Pass Rate by Behavior Class
- clarification_blocker: 1.0
- context_topic_switch: 1.0
- correction_rebind: 1.0
- detail_projection: 1.0
- entity_disambiguation_followup: 1.0
- error_envelope: 1.0
- kpi_aggregate: 1.0
- list_latest_records: 1.0
- observability_contract: 1.0
- ranking_top_n: 1.0
- transform_last_result: 1.0
- write_safety: 1.0

## Input Artifacts
- `impl_factory/04_automation/logs/20260223T044513Z_phase6_canary_uat_raw_v3.json`
