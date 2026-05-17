# EC-5D-A Mapping Evidence Drift Correction

## Executive Decision

Recommendation:

`enterprise_cleanup_ec_5d_a_ready_for_counterpart_review_ec_5e_may_start_if_accepted`

EC-5D-A is a narrow governance/evidence correction. It performs no staging, commit, cleanup, delete, move, archive, `.gitignore` change, runtime behavior change, UX work, Filter work, MI work, or family expansion.

## Baseline

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Pre-EC-5D-A dirty count: `312`
- Dirty count after mapping/test/report evidence refresh, before this note: `312`
- Current dirty count after adding this EC-5D-A note: `313`
- Runtime/source behavior changed: `False`
- Mapping/test/report evidence changed: `True`

## Issue Corrected

Counterpart found stale service import line-number assertions in three mapping contract tests:

- `test_compiled_support_emission_mapping_contracts`: expected `133`, current detected line `138`
- `test_legacy_runtime_emission_mapping_contracts`: expected `265`, current detected line `271`
- `test_reasoning_lane_emission_mapping_contracts`: expected `266`, current detected line `272`

These were governance/evidence drift failures, not runtime answer-emission failures.

## Fix Applied

The three mapping tests now derive expected service import/call evidence from current `service.py` text and compare it to generated mapping scan output. They no longer hard-code historical absolute line numbers.

Updated tests:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_compiled_support_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_reasoning_lane_emission_mapping_contracts.py`

Refreshed generated mapping evidence:

- `impl_factory/00_governance/current_docs/generated/ec_4d_compiled_support_emission_mapping/qwen_ec4d_compiled_support_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4d_compiled_support_emission_mapping/qwen_ec4d_compiled_support_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4h_legacy_runtime_emission_mapping/qwen_ec4h_legacy_runtime_emission_mapping_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4h_legacy_runtime_emission_mapping/qwen_ec4h_legacy_runtime_emission_mapping_report.md`
- `impl_factory/00_governance/current_docs/generated/ec_4g_reasoning_lane_authorized_emission_migration/qwen_ec4g_reasoning_lane_authorized_emission_migration_report.json`
- `impl_factory/00_governance/current_docs/generated/ec_4g_reasoning_lane_authorized_emission_migration/qwen_ec4g_reasoning_lane_authorized_emission_migration_report.md`

Refreshed evidence now records:

- compiled support service import line: `138`
- compiled support helper alias line: `140`
- legacy runtime service import line: `271`
- legacy runtime call line: `5773`
- reasoning lane service import line: `272`
- reasoning lane call line: `5029`

## Verification

- `python3 scripts/check_qwen_enterprise_guardrails.py`: `PASS`
- EC-4 mapping/closure/leakage group requested by Counterpart: `74 passed`
- `test_semantic_financial_resolution`: `276 passed`
- Source scan: `current_dirty_status_count=313`
- Source scan: `active_runtime_direct_assistant_append_count=0`
- Source scan: `inventory_count=1`
- Source scan: `migrated_authorized_paths` length `27`

## Non-Goals Preserved

- `no staging`
- `no commit`
- `no cleanup`
- `no runtime behavior change`
- `no source implementation beyond mapping/test/report evidence correction`
- `no UX / Filter / MI / family expansion`

## Final Recommendation

`enterprise_cleanup_ec_5d_a_ready_for_counterpart_review_ec_5e_may_start_if_accepted`

After Counterpart accepts EC-5D-A, EC-5E can proceed as the final EC-5 packaging decision gate.
