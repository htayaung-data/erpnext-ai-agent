# Phase 8 Release Gate Decision

- Executed: 2026-02-19T12:37:00Z
- Label: phase8_stage10_single
- Stage: 10%
- GO: False
- Action: rollback_to_v2
- Rollback Triggered: True

## Summary
- Total: 1
- Passed: 0
- Failed: 1
- Direct-answer rate (clear): 0.0
- Clarification rate (clear): 0.0
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 0.0
- Write safety incidents: 0
- Role parity reader/operator: False

## Gate Checks
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: True
- critical_clear_query_pass_100: False
- direct_answer_rate_clear_read_ge_90pct: False
- fac_preconditions_ok: False
- first_run_policy_declared: True
- mandatory_pass_rate_100: False
- output_shape_pass_rate_eq_100pct: False
- role_parity_reader_vs_operator: False
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: False
- failed_gate_checks: ['critical_clear_query_pass_100', 'direct_answer_rate_clear_read_ge_90pct', 'fac_preconditions_ok', 'mandatory_pass_rate_100', 'output_shape_pass_rate_eq_100pct', 'role_parity_reader_vs_operator']

## Inputs
- `impl_factory/04_automation/logs/20260219T100916Z_phase6_canary_uat_raw_v3.json`
