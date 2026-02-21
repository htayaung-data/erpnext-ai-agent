# R0 Baseline Reset Artifacts (2026-02-21)

This folder contains the Phase `R0` deliverables defined in `ai_assistant_roadmap_2026.md`.

## Deliverables
1. `r0_defect_stage_ledger_2026-02-21.csv`
   - Defect backlog tagged by mandatory stage taxonomy:
     - `intent_normalization`
     - `capability_resolution`
     - `execution_loop`
     - `quality_gate`
     - `transform_last`
     - `context_binding`
     - `response_shaping`
     - `clarification_policy`
2. `core_read_replay.json`
   - Canonical single-turn business asks.
3. `multiturn_context_replay.json`
   - Canonical 3-4 turn follow-up/correction chains.
4. `transform_followup_replay.json`
   - Canonical transform-on-last-result chains.
5. `r0_baseline_kpi_snapshot_2026-02-21.json`
   - Baseline KPI snapshot frozen from latest release-gate/shadow artifacts plus manual replay seeds.

## Source Evidence Used
1. `impl_factory/04_automation/logs/20260219T102236Z_phase6_canary_uat_raw_v3.json`
2. `impl_factory/04_automation/logs/20260220T063410Z_phase8_release_gate_stage10.json`
3. `impl_factory/04_automation/logs/20260219T123637Z_phase8_shadow_diff.json`
4. Manual test transcripts captured in project discussion on 2026-02-20 to 2026-02-21.

## R0 Exit Check
1. Known failures are stage-tagged in the ledger.
2. Replay suites are versioned and stable.
3. Baseline KPI snapshot is frozen and can be compared in R1+.
