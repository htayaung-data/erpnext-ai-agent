# Phase 8 Release Gate Decision

- Executed: 2026-02-23T10:52:49Z
- Label: -
- Stage: 10%
- GO: True
- Action: promote_to_25pct
- Rollback Triggered: False

## Summary
- Total: 30
- Passed: 30
- Failed: 0
- Direct-answer rate (clear): 0.9474
- Clarification rate (clear): 0.0526
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- Write safety incidents: 0
- Role parity reader/operator: True

## Behavior Class
- Declared: True
- Target coverage rate: 1.0
- Missing target classes: []
- Target first-run pass ok: True

## Gate Checks
- behavior_class_contract_declared: True
- behavior_class_first_run_pass_ge_90pct_each: True
- behavior_class_mandatory_coverage_ge_95pct: True
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: True
- critical_clear_query_pass_100: True
- direct_answer_rate_clear_read_ge_90pct: True
- fac_preconditions_ok: True
- first_run_policy_declared: True
- mandatory_pass_rate_100: True
- output_shape_pass_rate_eq_100pct: True
- role_parity_reader_vs_operator: True
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: True
- failed_gate_checks: []

## Inputs
- `impl_factory/04_automation/logs/20260223T105244Z_phase6_canary_uat_raw_v3.json`
