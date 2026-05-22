# EC-7I-F-A Passive Harness Safety Fixes

Decision: ec_7i_f_a_passive_harness_safety_fixes_ready_for_counterpart_qa_review

Date: 2026-05-21
Generated: 2026-05-21T15:10:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Site/user/dataset/archive creation performed: `false`
Dataset seeding performed: `false`
Archive activation performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7I-F-A fixes two passive harness correctness gaps found by QA:

1. synthetic markers could allow raw business/entity/document text to pass dataset validation;
2. repo-local symlink archive paths resolving outside the repo could pass archive readiness checks.

This slice changes only the passive scripts, focused tests, and governance report. It does not create an environment, activate an archive, seed a dataset, collect traces, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Fix 1: Dataset Validator Raw Identifier Detection

File:

`scripts/validate_ec7h_synthetic_dataset.py`

Changes:

- synthetic marker no longer suppresses raw identifier detection;
- business/entity/legal-name values are rejected even if the string includes `EC7H Synthetic`;
- invoice/document-like identifiers such as `SINV-0001` are rejected even if marked synthetic;
- string metadata fields in each scenario are scanned for raw business identifiers.

Regression tests added:

- `EC7H Synthetic request for Yoma Bank invoice SINV-0001` is invalid;
- `EC7H Synthetic Myanmar Apex Co Ltd` is invalid;
- metadata string `Vendor value Myanmar Apex Co Ltd` is invalid;
- invalid scenarios emit explicit `*_raw_business_identifier` violations.

## Fix 2: Archive Checker Symlink Safety

File:

`scripts/check_ec7h_archive_readiness.py`

Changes:

- archive path is rejected if the lexical path is inside the repo, even when the resolved target is outside;
- symlink archive paths are rejected by default;
- report now includes `archive_is_symlink` and `lexically_outside_repo`;
- raw archive must not be reachable through the git worktree.

Regression test added:

- repo-local symlink pointing to an external archive directory fails with `archive_path_is_symlink` and `archive_path_lexically_inside_repo`.

## Focused Tests

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_ec7i_setup_support_harnesses
```

Expected result after EC-7I-F-A: `9 passed`.

## Non-Goals Preserved

- `no_site_creation`
- `no_user_creation`
- `no_dataset_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Verification Results

EC-7I-F-A verification should show:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I-F/F-A harness tests: `9 passed`
- Combined protocol/harness command: `26 passed`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_f_a_passive_harness_safety_fixes_ready_for_counterpart_qa_review`

If accepted, the passive setup-support harnesses are safer to use in a future setup verification slice. Environment setup and live trace collection remain paused.
