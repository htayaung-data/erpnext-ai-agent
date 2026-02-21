# R1 Phase Report (2026-02-21, completed)

Status: Completed  
Roadmap phase: `R1 - Capability Registry Hardening`

## What was implemented
1. Capability registry overlay and metadata-first enrichment:
   - `ai_core/v3/capability_registry.py`
   - `ai_core/v3/capability_index.py`
2. Resolver hard-compatibility blocking (sold/received, receivable/payable, dimension mismatch, count-KPI mismatch, document compatibility).
3. Clarification policy hardening:
   - blocker reasons include entity no-match/ambiguity
   - unsupported-capability responses carry deterministic pending state
4. Deterministic entity filter resolution:
   - `ai_core/v3/entity_resolution.py`
   - robust no-match vs multiple-match behavior with options
5. Document detail stability:
   - document-id spec normalization clears conflicting date constraints
   - direct document lookup path for invoice detail asks in read engine
   - response shaper document fallback for invoice-family detail reconstruction
6. Write safety/read routing parity retained with v2 delegation for write-confirm flows.

## Deterministic test status
Command:
`PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -v ai_assistant_ui.tests.test_v3_entity_resolution ai_assistant_ui.tests.test_v3_phase5_policy_shaper ai_assistant_ui.tests.test_v3_spec_pipeline ai_assistant_ui.tests.test_v3_read_engine ai_assistant_ui.tests.test_v3_semantic_resolver ai_assistant_ui.tests.test_v3_resolver_pipeline`

Result:
1. `87` tests executed
2. `87` passed
3. `0` failed

## Integration canary status (R1 exit run)
Raw:
`impl_factory/04_automation/logs/20260221T043044Z_phase6_canary_uat_raw_v3.json`

Gate:
`impl_factory/04_automation/logs/20260221T043108Z_phase8_release_gate_stage10.json`

Current summary:
1. total: `26`
2. passed: `26`
3. failed: `0`
4. direct-answer rate (clear): `93.33%`
5. unnecessary clarification rate (clear): `0.00%`
6. wrong-report rate (clear): `0.00%`
7. clarification-loop rate: `0.00%`
8. reader pass rate: `100.00%`
9. operator pass rate: `100.00%`
10. p95 latency (clear): `6,278 ms`

Gate decision:
1. `GO`
2. action: `promote_to_25pct`

## R1 delta vs frozen R0 baseline
Snapshot:
`impl_factory/04_automation/r1/r1_delta_snapshot_2026-02-21.json`

Delta highlights:
1. pass count: `+1` (`25 -> 26`)
2. wrong-report rate: `0.00%` (`0.00% -> 0.00%`)
3. p95 latency: `-4,303 ms` (`10,581 -> 6,278`)
4. reader pass rate: `+0.00%` (`100.00% -> 100.00%`)
5. operator pass rate: `+14.29%` (`85.71% -> 100.00%`)

## R1 exit status
Met.
1. Deterministic R1 scope implemented with generalized logic (no single-case hardcoding).
2. Canary phase-10 release gate is `GO`.
