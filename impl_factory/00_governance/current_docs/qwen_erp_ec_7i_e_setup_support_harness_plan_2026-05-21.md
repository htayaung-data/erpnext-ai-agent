# EC-7I-E Setup-Support Harness Plan

Decision: ec_7i_e_setup_support_harness_plan_ready_for_counterpart_qa_owner_review

Date: 2026-05-21
Generated: 2026-05-21T09:35:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Harness implementation performed: `false`
Site/user/dataset/archive creation performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7I-D correctly blocked setup execution because the readiness command, dataset validator, live trace command, controlled bench path, and raw archive path were not execution-ready. EC-7I-E designs the missing support harnesses so a future setup slice can be verified with small reviewed helpers instead of vague manual checks.

This is a plan/report slice only. It does not implement helpers, create a site, create a user, seed a dataset, activate an archive, collect traces, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Harness Design Summary

| Harness | Proposed artifact | Purpose | Runtime effect |
|---|---|---|---|
| Readiness check helper | `ai_assistant_ui.qwen_chat.ec7h_environment_readiness` | Verify controlled bench/site/app/user/dataset/archive before collection. | `none` |
| Synthetic dataset validator | `scripts/validate_ec7h_synthetic_dataset.py` | Validate `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` manifest shape and synthetic-only policy. | `none` |
| QA user setup support | Manual-first checklist, optional helper later | Verify or assist QA-user creation without secrets in repo. | `none` unless separately approved setup |
| Archive verification helper | `scripts/check_ec7h_archive_readiness.py` | Verify archive path, owner/group, permissions, retention marker. | `none` |
| Live trace collection | Manual procedure for now | Avoid premature collection script until environment and evidence path are proven. | `none` |

## Proposed Readiness Check Helper

Proposed module:

`impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/ec7h_environment_readiness.py`

Purpose:

- verify the command is running against an explicit controlled bench/site context;
- verify `ai_assistant_ui` is installed/importable;
- verify dedicated QA user exists;
- verify synthetic dataset manifest exists and passes validator;
- verify raw archive path exists, is external to repo, and has safe permissions;
- verify redacted output candidate path policy is known;
- emit a pass/fail JSON-like report;
- collect no traces;
- require no production data.

Proposed function shape:

```python
def build_ec7h_environment_readiness_report(
    *,
    site_name: str,
    qa_user: str,
    dataset_manifest_path: str,
    raw_archive_path: str,
    redacted_output_candidate_path: str,
    expected_dataset_id: str = "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001",
) -> dict:
    ...
```

Proposed bench command shape after implementation approval:

```bash
bench --site ec7h-test.local execute \
  ai_assistant_ui.qwen_chat.ec7h_environment_readiness.build_ec7h_environment_readiness_report \
  --kwargs '{
    "site_name": "ec7h-test.local",
    "qa_user": "qa_ec7h_trace_user@example.invalid",
    "dataset_manifest_path": "/home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json",
    "raw_archive_path": "/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/",
    "redacted_output_candidate_path": "impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/"
  }'
```

Required output fields:

- `runtime_effect: none`
- `site_name`
- `qa_user_exists`
- `app_import_ok`
- `dataset_manifest_exists`
- `dataset_manifest_valid`
- `raw_archive_exists`
- `raw_archive_outside_repo`
- `raw_archive_permissions_ok`
- `redacted_output_policy_defined`
- `ready_for_live_trace_collection_request`
- `blockers`

Forbidden behavior:

- no trace collection;
- no site/user/dataset/archive creation;
- no production-data queries;
- no route/model/report-selection changes;
- no strict enforcement.

## Proposed Synthetic Dataset Validator

Proposed script:

`scripts/validate_ec7h_synthetic_dataset.py`

Manifest name:

`EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001`

Purpose:

- parse the dataset manifest;
- validate schema;
- validate synthetic-only markers;
- validate lane/scenario coverage;
- reject raw customer/vendor/entity-like names;
- reject production-like document identifiers;
- output pass/fail report only;
- perform no database writes and no trace collection.

Required manifest fields:

- `dataset_id`
- `data_classification`
- `schema_version`
- `qa_owner`
- `scenarios`
- per scenario: `scenario_id`, `lane_id`, `scenario_type`, `synthetic_prompt`, `synthetic_record_reference`, `expected_metadata_status`, `expected_strict_readiness_status`, `expected_fallback_used`, `expected_fallback_reason`, `expected_authority_status`, `redaction_expectation`

Required lane coverage:

- `frontdoor_semantic_classification`
- `fresh_query_interpretation`
- `followup_interpretation`
- `semantic_reasoning_activation`
- `semantic_repair_intent`

Allowed scenario types:

- `accepted_success`
- `degraded_low_confidence`
- `runtime_error_fallback`
- `missing_metadata`
- `not_applicable`
- `rejected`

Synthetic-only rules:

- `data_classification` must equal `synthetic_only`;
- synthetic prompts should include `EC7H Synthetic` or another explicit synthetic marker;
- real-world customer/vendor/entity names are not allowed;
- production-like document identifiers such as `SINV-`, `SO-`, `PO-`, `ACC-`, and real invoice/account names are not allowed unless clearly prefixed as synthetic;
- no monetary balances from real records;
- no raw trace payloads.

Proposed command shape:

```bash
python3 scripts/validate_ec7h_synthetic_dataset.py \
  /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
```

Output:

- `dataset_id`
- `valid`
- `scenario_count`
- `lane_coverage`
- `violations`
- `runtime_effect: none`

## Proposed QA User Setup Support

Recommended approach: manual-first.

Manual-first path:

1. QA/Owner creates `qa_ec7h_trace_user@example.invalid` in the controlled non-production site UI or bench console.
2. QA/Owner assigns minimum roles needed for synthetic light-semantic scenarios.
3. QA/Owner stores credentials outside repo.
4. Readiness helper verifies the user exists, but does not create or modify the user.

Command-assisted path, only if separately approved:

- implement a tiny setup helper that creates the user only when explicitly invoked;
- helper must not accept or print passwords;
- role list must be passed explicitly from owner-approved config;
- helper must emit a report and perform no trace collection.

Proposed user identity:

- email/login: `qa_ec7h_trace_user@example.invalid`
- display name: `QA EC7H Trace`

Role policy:

- no Administrator role by default;
- minimum ERP/Frappe roles required for synthetic prompts;
- role list is an owner/QA decision before implementation;
- disable/remove after trace window if owner/QA require.

No password or secret may appear in repo, governance docs, command logs, dataset manifests, or redacted summaries.

## Proposed Archive Verification Helper

Proposed script:

`scripts/check_ec7h_archive_readiness.py`

Purpose:

- verify raw archive path exists;
- verify it is outside repo;
- verify owner/group match owner-approved policy;
- verify mode is `750` or stricter;
- verify no `.git` directory exists inside archive path;
- verify retention marker exists if owner requires one;
- write no raw traces.

Proposed command shape:

```bash
python3 scripts/check_ec7h_archive_readiness.py \
  --path /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521 \
  --expected-owner TBD_OWNER_APPROVED_USER \
  --expected-group TBD_QA_OWNER_GROUP \
  --max-mode 750
```

Required output fields:

- `archive_exists`
- `outside_repo`
- `owner_ok`
- `group_ok`
- `permissions_ok`
- `retention_marker_ok`
- `no_git_directory`
- `valid`
- `violations`

No raw trace writes are allowed unless a future collection slice explicitly approves collection.

## Live Trace Collection Decision

Recommendation: keep `live_trace_collection` manual for now.

Reason:

- a collection script would be premature while no controlled environment exists;
- the first priority is readiness verification and redaction discipline;
- manual collection can use existing runtime/session/tool/audit metadata under QA/Owner custody;
- a collection script may be proposed later only after the environment and redaction summary path are verified.

EC-7I-E does not design or approve a live trace collection script.

## Future Implementation Slices

Suggested narrow sequence:

1. EC-7I-F: implement dataset validator and archive readiness checker only.
2. EC-7I-G: implement passive environment readiness helper only.
3. EC-7I-H: owner-approved environment setup execution, if still needed.
4. EC-7I-I: environment readiness verification against the actual site/user/dataset/archive.
5. Return to EC-7H live trace collection request only after EC-7I readiness is verified.

Each slice should keep no live trace collection, no production data, no strict enforcement, and no deployment unless explicitly approved.

## Acceptance Criteria For This Plan

EC-7I-E is acceptable if Counterpart/QA/Owner agree that:

- helper boundaries are passive and report-only;
- dataset validator can be implemented without production data;
- QA user support is manual-first and secret-safe;
- archive verifier writes no raw traces;
- live trace collection remains manual/deferred;
- no setup execution is implied by this plan.

## Passive Verification Results

EC-7I-E preserved backend posture:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- Scoped report diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Non-Goals

- `no_site_creation`
- `no_user_creation`
- `no_dataset_creation_or_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7i_e_setup_support_harness_plan_ready_for_counterpart_qa_owner_review`

If accepted, the next slice should implement only the smallest passive harnesses needed for setup verification, likely the synthetic dataset validator and archive readiness checker first. Environment setup and live trace collection should remain paused.
