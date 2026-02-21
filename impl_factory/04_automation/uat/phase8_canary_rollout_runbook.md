# Phase 8 Canary Rollout Runbook (v3.0)

Date: 2026-02-19  
Owner: Engineering Lead + QA Lead + DevOps  
Scope: staged `assistant_engine=v3_active` rollout with strict gates and rollback

## 1) Inputs
1. Raw first-run canary artifacts (JSON) from UAT runner.
2. Optional diagnostic rerun artifacts (non-gating).
3. Baseline correction rate (for trend gate when available).
4. Agreed latency SLA (`p95` in ms).

## 2) Shadow Diff (Pre-Canary)
1. Compare latest `v2` and `v3_shadow` raw outputs:
```bash
python3 impl_factory/04_automation/bench_scripts/phase8_shadow_diff.py \
  --v2-raw impl_factory/04_automation/logs/<v2_raw>.json \
  --v3-raw impl_factory/04_automation/logs/<v3_shadow_raw>.json
```
2. Review `regressed` cases.  
   Rule: if any critical scenario regresses, do not start canary.

## 3) Stage Gate Command
Run per stage (`10`, `25`, `50`, `100`):
```bash
python3 impl_factory/04_automation/bench_scripts/phase8_release_gate.py \
  --raw impl_factory/04_automation/logs/<stage_raw_1>.json \
  --raw impl_factory/04_automation/logs/<stage_raw_2_optional>.json \
  --stage 10 \
  --latency-p95-sla-ms 5000 \
  --baseline-correction-rate <baseline_rate_optional> \
  --label "phase8_stage10"
```

Outputs:
1. `*_phase8_release_gate_stage10.json`
2. `*_phase8_release_gate_stage10.md`

## 3A) Runtime Routing Configuration (Deterministic Canary)
Set rollout keys in site/runtime config before each stage:
1. `assistant_engine=v3_canary`
2. `ai_assistant_v3_canary_percent=10|25|50|100`
3. For full rollback: `assistant_engine=v2`

Notes:
1. Bucketing is deterministic by `session_name` (fallback `user`), so the same session stays on the same side of canary.
2. Route metadata is emitted in tool messages (`type=engine_route`, `phase=phase8`) for auditability.

## 4) Promotion Policy
1. Promotion allowed only when `overall_go=true`.
2. If pass at stage:
   - `10% -> 25%`
   - `25% -> 50%`
   - `50% -> 100%`
   - `100% -> hold_100pct_monitor`
3. If fail at any stage:
   - immediate rollback action: `assistant_engine=v2`
   - open defects for each failed gate check.

## 5) Rollback Rehearsal (Required Before 100%)
1. Set `assistant_engine=v2`.
2. Run smoke scenarios (`FIN-01`, `SAL-01`, `STK-01`, `WR-02`).
3. Capture evidence log path in UAT evidence.
4. Restore previous stage config only after rehearsal pass.

## 6) Non-Negotiable Gate Notes
1. First-run-only scoring is enforced by script (earliest case result wins).
2. Diagnostic reruns are ignored for gate scoring.
3. Role parity must pass (`ai.reader` and `ai.operator`).
4. Output-shape gate must be 100% on clear benchmark.
5. Write safety incidents must be zero.
