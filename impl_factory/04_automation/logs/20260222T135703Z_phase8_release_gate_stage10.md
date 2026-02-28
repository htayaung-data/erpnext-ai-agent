# Phase 8 Release Gate Decision

- Executed: 2026-02-22T13:57:03Z
- Label: -
- Stage: 10%
- GO: False
- Action: rollback_to_v2
- Rollback Triggered: True

## Summary
- Total: 27
- Passed: 23
- Failed: 4
- Direct-answer rate (clear): 0.75
- Clarification rate (clear): 0.25
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- Write safety incidents: 0
- Role parity reader/operator: True

## Gate Checks
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: False
- critical_clear_query_pass_100: True
- direct_answer_rate_clear_read_ge_90pct: False
- fac_preconditions_ok: True
- first_run_policy_declared: True
- mandatory_pass_rate_100: False
- output_shape_pass_rate_eq_100pct: True
- role_parity_reader_vs_operator: True
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: False
- failed_gate_checks: ['clarification_rate_clear_read_le_10pct', 'direct_answer_rate_clear_read_ge_90pct', 'mandatory_pass_rate_100']

## Inputs
- `impl_factory/04_automation/logs/20260222T135557Z_phase6_canary_uat_raw_v3.json`
