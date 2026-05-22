# EC-7I-G-A Passive Environment Readiness Helper Hardening

Decision: ec_7i_g_a_readiness_helper_hardening_ready_for_counterpart_qa_review

Date: 2026-05-22
Generated: 2026-05-22T00:30:00+00:00
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

EC-7I-G-A fixes two readiness-gate blockers found by QA in `scripts/check_ec7h_environment_readiness.py`:

1. source checkout or arbitrary temp paths could be accepted as controlled bench paths;
2. redacted output candidates under excluded streams such as cache/probe/temp/ERP UI/seed paths could be accepted.

This slice is passive helper hardening only. It does not create an environment, activate an archive, seed a dataset, collect traces, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Fix 1: Controlled Bench Evidence

File:

`scripts/check_ec7h_environment_readiness.py`

Changes:

- rejects bench paths inside the repo;
- rejects source checkout markers such as `impl_factory` and `scripts/check_qwen_enterprise_guardrails.py`;
- rejects arbitrary temp directories without bench evidence;
- requires stronger bench evidence such as `sites`, `apps`, `Procfile`, or `sites/common_site_config.json`;
- reports `bench_evidence`, `bench_path_inside_repo`, and explicit bench blockers.

New tests prove:

- `/tmp/erpai_pr4_postmerge_verify`-style source checkout path is not ready;
- arbitrary temp directory is not ready;
- ready case requires bench markers.

## Fix 2: Redacted Output Exclusion Policy

File:

`scripts/check_ec7h_environment_readiness.py`

Changes:

- blocks ERP UI paths;
- blocks seed/data paths;
- blocks temp paths;
- blocks probe paths;
- blocks cache paths;
- blocks PrimeAxis paths;
- blocks generated scratch/S7 exclusion paths.

New tests prove `redacted_output_candidate_forbidden_stream` is triggered for:

- `erp_workspace_ui/redacted`
- `erp_ui/redacted`
- `02_seed_data/redacted`
- `seed/data/redacted`
- `tmp/redacted`
- `temp/redacted`
- `probe/redacted`
- `cache/redacted`
- `primeaxis/redacted`
- `generated/qwen_s7_browser_batch/redacted`

## Focused Tests

Focused EC-7I setup-support harness tests now cover dataset validator, archive checker, and readiness helper hardening.

Expected result after EC-7I-G-A: `15 passed`.

## Non-Goals Preserved

- `no_site_creation`
- `no_user_creation`
- `no_dataset_seeding`
- `no_archive_creation_or_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Verification Results

EC-7I-G-A verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I harness tests: `15 passed`
- Combined protocol/harness command: `32 passed`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_g_a_readiness_helper_hardening_ready_for_counterpart_qa_review`

If accepted, EC-7I readiness helpers should be considered hardened unless QA finds a P0/P1 case where the helper can still falsely approve unsafe live trace collection. Environment setup and live trace collection remain paused.
