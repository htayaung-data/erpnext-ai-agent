# Phase 8 Release Gate Decision

- Executed: 2026-02-20T06:34:10Z
- Label: local_check_102236
- Stage: 10%
- GO: False
- Action: rollback_to_v2
- Rollback Triggered: True

## Summary
- Total: 26
- Passed: 25
- Failed: 1
- Direct-answer rate (clear): 1.0
- Clarification rate (clear): 0.0
- Unnecessary clarification rate (clear): 0.0
- Wrong-report rate (clear): 0.0
- Loop rate: 0.0
- Output-shape pass rate (clear): 1.0
- Write safety incidents: 0
- Role parity reader/operator: False

## Gate Checks
- clarification_loop_rate_lt_1pct: True
- clarification_rate_clear_read_le_10pct: True
- critical_clear_query_pass_100: True
- direct_answer_rate_clear_read_ge_90pct: True
- fac_preconditions_ok: False
- first_run_policy_declared: True
- latency_p95_within_sla: False
- mandatory_pass_rate_100: False
- output_shape_pass_rate_eq_100pct: True
- role_parity_reader_vs_operator: False
- unnecessary_clarification_rate_clear_read_le_5pct: True
- write_safety_incidents_eq_0: True
- wrong_report_rate_clear_read_le_3pct: True
- zero_meta_clarification_on_clear_asks: True
- overall_go: False
- failed_gate_checks: ['fac_preconditions_ok', 'latency_p95_within_sla', 'mandatory_pass_rate_100', 'role_parity_reader_vs_operator']

## Inputs
- `impl_factory/04_automation/logs/20260219T102236Z_phase6_canary_uat_raw_v3.json`
