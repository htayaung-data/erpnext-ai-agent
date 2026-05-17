# EC-4B Frontdoor Emission Mapping

- Branch: `feature/ai-assistant`
- Head: `154be1e`
- Dirty status count: `307`
- Runtime behavior changed: `True`
- Hard runtime blocking enabled: `False`
- Final recommendation: `enterprise_cleanup_ec_4u_frontdoor_duplicate_facade_closed`

## Frontdoor Emitters

| Path | Classification | Append lines | Service imported | Recommendation |
|---|---|---:|---:|---|
| frontdoor_lane_package_governed_report_or_projection | active_runtime_primary_migrated_to_authorized_helper |  | True | ec_4c_migration_complete_keep_root_for_ec_9_duplicate_cleanup |
| frontdoor_lane_root_duplicate | compatibility_facade_not_service_runtime |  | False | ec_4u_duplicate_closure_complete_keep_facade |

## Service Evidence

- Package lane imported by service: `True`
- Root lane imported by service: `False`
- Service evaluate call sites: `[4137, 4156, 4863, 5237]`
- Service handle call sites: `[4738, 4875, 5251]`

## Duplicate Drift

- Files identical: `False`
- Package line count: `984`
- Root line count: `14`
- Package has fresh-breakout helper: `True`
- Root has fresh-breakout helper: `False`
- Drift reason: Root frontdoor module is now an EC-4U compatibility facade over the active package lane.

## Proposed EC-4C Write Scope

Allowed files:
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_authorized_emission_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_frontdoor_emission_mapping_contracts.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/final_answer_emission_dry_run.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_emission_dry_run_contracts.py`

Forbidden files:
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/entity_drilldown_lane.py`

## Non-Goals

- `no_additional_runtime_migration_beyond_active_package_frontdoor_in_ec4c`
- `no_service_py_changes`
- `no_active_package_frontdoor_behavior_change`
- `no_model_role_strict_enforcement`
- `no_release_packaging_cleanup`
- `no_reasoning_nbu_entity_or_legacy_lane_migration`
