# Phase 1 First-Run Baseline Score

- Executed: 2026-02-23T10:52:49Z
- Label: post_hardening
- Input artifacts: 1

## First-Run Policy
- Enforced: True
- Source: earliest_result_per_case_id
- Selected cases: 30
- Ignored duplicate results: 0

## KPI Summary
- Total cases scored: 30
- Pass count: 30
- Fail count: 0
- First-run pass rate: 0.0779
- Direct-answer rate (clear): 0.9474
- Clarification rate (clear): 0.0526
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Clarification loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- User correction rate: 0.0
- Write safety incidents: 0
- Latency p95 ms (clear): 12359

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
- clarification_blocker: 0.1111
- comparison: 0.05
- context_topic_switch: 0.0333
- correction_rebind: 0.05
- detail_projection: 0.1714
- entity_disambiguation_followup: 0.1333
- error_envelope: 0.1111
- kpi_aggregate: 0.05
- list_latest_records: 0.0333
- observability_contract: 0.1053
- ranking_top_n: 0.15
- transform_last_result: 0.0492
- trend_time_series: 0.05
- write_safety: 0.0645

## Input Artifacts
- `impl_factory/04_automation/logs/20260223T105244Z_phase6_canary_uat_raw_v3.json`
