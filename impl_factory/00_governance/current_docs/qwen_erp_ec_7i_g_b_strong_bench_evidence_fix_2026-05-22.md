# EC-7I-G-B Strong Bench Evidence Fix

Decision: ec_7i_g_b_strong_bench_evidence_fix_ready_for_counterpart_qa_review

Date: 2026-05-22
Generated: 2026-05-22T01:15:00+00:00
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

EC-7I-G-B fixes one remaining false-approval path in `scripts/check_ec7h_environment_readiness.py`: a temp directory with a single empty bench marker, such as `sites/`, could qualify as strong bench evidence.

This slice is passive readiness-helper hardening only. It does not create a site, create a user, seed a dataset, activate an archive, collect traces, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Fix

File:

`scripts/check_ec7h_environment_readiness.py`

Required strong bench evidence now requires:

- `sites/` directory;
- `apps/` directory;
- and at least one site/control marker:
- `Procfile`;
- `sites/common_site_config.json`;
- `sites/{site_name}/site_config.json`;
- or `sites/{site_name}` directory.

The readiness report now exposes granular bench evidence fields:

- `sites_exists`
- `apps_exists`
- `procfile_exists`
- `common_site_config_exists`
- `site_dir_exists`
- `site_config_exists`
- `has_site_specific_evidence`
- `has_strong_bench_evidence`

If evidence is incomplete, readiness returns blocked with `bench_path_lacks_controlled_bench_evidence`.

## Tests

New adversarial tests prove these are not ready:

- temp directory with only `sites/`;
- temp directory with only `apps/`;
- temp directory with only `Procfile`;
- temp directory with empty `sites/` and `apps/` but no site/control marker.

The positive synthetic test now uses combined bench markers, including `sites/`, `apps/`, `Procfile`, and `sites/ec7h-test.local/site_config.json`.

Expected focused harness result after EC-7I-G-B: `16 passed`.

## Non-Goals Preserved

- `no_environment_setup`
- `no_site_user_dataset_archive_creation`
- `no_dataset_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_packaging_staging_commit_push`
- `no_cleanup`

## Verification Results

EC-7I-G-B verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I harness tests: `16 passed`
- Combined protocol/harness command: `33 passed`
- Empty-marker adversarial probes: PASS
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_g_b_strong_bench_evidence_fix_ready_for_counterpart_qa_review`

If accepted, the readiness helper should be considered hardened unless QA finds a P0/P1 false-approval case. Environment setup and live trace collection remain paused.
