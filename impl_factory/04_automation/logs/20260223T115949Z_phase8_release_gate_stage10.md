# Phase 8 Release Gate Decision

- Executed: 2026-02-23T11:59:49Z
- Label: -
- Stage: 10%
- GO: False
- Action: rollback_to_v2
- Rollback Triggered: True

## Summary
- Total: 8
- Passed: 8
- Failed: 0
- Direct-answer rate (clear): 1.0
- Clarification rate (clear): 0.0
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- Write safety incidents: 0
- Role parity reader/operator: True
- First-run sample size: 8
- First-run sample threshold: 300
- Target-class sample threshold: 20

## Behavior Class
- Declared: True
- Target coverage rate: 0.2222
- Missing target classes: ['comparison', 'correction_rebind', 'detail_projection', 'kpi_aggregate', 'list_latest_records', 'transform_last_result', 'trend_time_series']
- Target first-run pass ok: False

## Sample Size Policy
- First-run sample size ok: False
- Target-class sample size ok: False

## Gate Checks
- behavior_class_contract_declared: True
- behavior_class_first_run_pass_ge_90pct_each: False
- behavior_class_mandatory_coverage_ge_95pct: False
- behavior_class_target_sample_size_ge_threshold: False
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: True
- critical_clear_query_pass_100: False
- direct_answer_rate_clear_read_ge_90pct: True
- fac_preconditions_ok: True
- first_run_policy_declared: True
- first_run_sample_size_ge_threshold: False
- mandatory_pass_rate_100: False
- output_shape_pass_rate_eq_100pct: True
- role_parity_reader_vs_operator: True
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: False
- failed_gate_checks: ['behavior_class_first_run_pass_ge_90pct_each', 'behavior_class_mandatory_coverage_ge_95pct', 'behavior_class_target_sample_size_ge_threshold', 'critical_clear_query_pass_100', 'first_run_sample_size_ge_threshold', 'mandatory_pass_rate_100']

## Inputs
- `impl_factory/04_automation/logs/20260223T115809Z_phase6_manifest_uat_raw_v3.json`
