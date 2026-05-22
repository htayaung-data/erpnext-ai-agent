# EC-7I-F-B Dataset Validator Edge-Case Fix

Decision: ec_7i_f_b_dataset_validator_edge_case_fix_ready_for_counterpart_qa_review

Date: 2026-05-21
Generated: 2026-05-21T15:45:00+00:00
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

EC-7I-F-B fixes one remaining dataset validator edge case: production-style ERP document IDs could pass when hidden behind synthetic prefixes such as `EC7H_SYNTH_SINV-0001`.

This slice changes only the passive dataset validator, focused tests, and governance report. It does not use or seed a dataset, create an environment, activate an archive, collect traces, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Fix

File:

`scripts/validate_ec7h_synthetic_dataset.py`

Change:

- document ID detection now catches IDs after underscores or other separators;
- synthetic prefixes no longer hide ERP document IDs;
- examples such as `EC7H_SYNTH_SINV-0001` and `EC7H_SYNTH_SO-0001` are rejected.

## Tests

File:

`impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py`

Added regression coverage:

- `EC7H_SYNTH_SINV-0001` is invalid;
- `EC7H_SYNTH_SO-0001` is invalid;
- prior laundering tests for `Yoma Bank`, `SINV-0001`, and `Myanmar Apex Co Ltd` remain green.

Expected focused harness result after EC-7I-F-B: `10 passed`.

## Non-Goals Preserved

- `no_environment_setup`
- `no_dataset_use_or_seeding`
- `no_archive_activation`
- `no_live_trace_collection`
- `no_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`

## Verification Results

EC-7I-F-B verification should show:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I-F/F-A/F-B harness tests: `10 passed`
- Combined protocol/harness command: `27 passed`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_f_b_dataset_validator_edge_case_fix_ready_for_counterpart_qa_review`

If accepted, EC-7I passive setup-support harnesses are ready for the next narrow planning step. Environment setup and live trace collection remain paused.
