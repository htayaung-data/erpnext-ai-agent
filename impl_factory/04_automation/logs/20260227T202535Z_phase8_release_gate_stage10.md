# Phase 8 Release Gate Decision

- Executed: 2026-02-27T20:25:35Z
- Label: phase6_manifest_full
- Stage: 10%
- GO: False
- Action: rollback_to_v2
- Rollback Triggered: True

## Summary
- Total: 385
- Passed: 350
- Failed: 35
- Direct-answer rate (clear): 0.9474
- Clarification rate (clear): 0.0526
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- Write safety incidents: 0
- Role parity reader/operator: True
- First-run sample size: 385
- First-run sample threshold: 300
- Target-class sample threshold: 20

## Behavior Class
- Declared: True
- Target coverage rate: 1.0
- Missing target classes: []
- Target first-run pass ok: False

## Sample Size Policy
- First-run sample size ok: True
- Target-class sample size ok: True

## Gate Checks
- behavior_class_contract_declared: True
- behavior_class_first_run_pass_ge_90pct_each: False
- behavior_class_mandatory_coverage_ge_95pct: True
- behavior_class_target_sample_size_ge_threshold: True
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: True
- critical_clear_query_pass_100: False
- direct_answer_rate_clear_read_ge_90pct: True
- fac_preconditions_ok: True
- first_run_policy_declared: True
- first_run_sample_size_ge_threshold: True
- mandatory_pass_rate_100: False
- output_shape_pass_rate_eq_100pct: True
- role_parity_reader_vs_operator: True
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: False
- failed_gate_checks: ['behavior_class_first_run_pass_ge_90pct_each', 'critical_clear_query_pass_100', 'mandatory_pass_rate_100']

## Inputs
- `impl_factory/04_automation/logs/20260227T165533Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T181158Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T190828Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T194428Z_phase6_manifest_uat_raw_v3.json`
- `impl_factory/04_automation/logs/20260227T202535Z_phase6_manifest_uat_raw_v3.json`
