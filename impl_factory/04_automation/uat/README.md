# AI Assistant UAT/Regression Pack (Step 11)

Date: 2026-02-18  
Scope: ERPNext Embedded AI Assistant (`ai_assistant_ui`) custom app

## Pack Contents
1. `impl_factory/04_automation/uat/step11_uat_matrix.md`  
   Business-facing UAT scenarios with expected outcomes and contract mapping.
2. `impl_factory/04_automation/uat/step11_uat_evidence_template.md`  
   Fillable template for execution evidence and sign-off.
3. `impl_factory/04_automation/bench_scripts/run_step11_regression.sh`  
   Deterministic regression runner (compile + contract regression tests + summary artifacts).

## How To Use
1. Run regression pack first:
   - `bash impl_factory/04_automation/bench_scripts/run_step11_regression.sh`
2. Execute UAT scenarios in `step11_uat_matrix.md`.
3. Record outcomes in `step11_uat_evidence_template.md`.
4. Attach generated logs from `impl_factory/04_automation/logs/`.

## Phase 8 Release Governance
After producing raw canary artifacts, use Phase 8 scripts for strict release control:
1. Set runtime canary routing:
   - `assistant_engine=v3_canary`
   - `ai_assistant_v3_canary_percent=10|25|50|100`
   - rollback key: `assistant_engine=v2`
1. Shadow diff (`v2` vs `v3`):
   - `python3 impl_factory/04_automation/bench_scripts/phase8_shadow_diff.py --v2-raw <v2_raw.json> --v3-raw <v3_raw.json>`
2. Stage gate (`10%|25%|50%|100%`, first-run-only scoring):
   - `python3 impl_factory/04_automation/bench_scripts/phase8_release_gate.py --raw <canary_raw_1.json> --raw <canary_raw_2.json> --stage 10 --latency-p95-sla-ms 5000`
3. Use generated outputs for go/no-go:
   - `*_phase8_release_gate_stage*.json`
   - `*_phase8_release_gate_stage*.md`
   - `*_phase8_shadow_diff.json`
   - `*_phase8_shadow_diff.md`

## Exit Gate
1. Regression runner reports success.
2. All mandatory UAT scenarios pass.
3. Any failed scenario has a linked defect and rerun evidence.
