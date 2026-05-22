# EC-7I-G Passive Environment Readiness Helper

Decision: ec_7i_g_passive_environment_readiness_helper_ready_for_counterpart_qa_review

Date: 2026-05-21
Generated: 2026-05-21T16:20:00+00:00
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

EC-7I-G adds a passive environment readiness helper that composes the accepted EC-7I-F harnesses:

- `scripts/validate_ec7h_synthetic_dataset.py`
- `scripts/check_ec7h_archive_readiness.py`

The helper reports whether EC-7H live trace prerequisites exist. It does not create missing prerequisites, collect traces, connect to Frappe, seed records, activate archives, deploy, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Files Added / Updated

| File | Purpose |
|---|---|
| `scripts/check_ec7h_environment_readiness.py` | New passive readiness helper. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ec7i_setup_support_harnesses.py` | Adds focused readiness-helper tests. |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_7i_g_passive_environment_readiness_helper_2026-05-21.md` | EC-7I-G governance report. |

## Helper Behavior

Script:

`scripts/check_ec7h_environment_readiness.py`

Checks:

- controlled bench/site path exists;
- site name is provided;
- QA user identifier is provided, with warning if it does not include `qa_ec7h_trace_user`;
- synthetic dataset manifest path exists;
- synthetic dataset manifest passes `validate_ec7h_synthetic_dataset.py`;
- archive path passes `check_ec7h_archive_readiness.py`;
- raw trace custodian is named;
- redacted output candidate path is not in forbidden streams;
- staged file count is zero;
- excluded status entries are absent.

Output:

- JSON report;
- `runtime_effect: none`;
- `ready: true/false`;
- `decision: environment_ready_for_collection_request` or `environment_not_ready`;
- `blockers`;
- `warnings`;
- nested dataset and archive reports.

The helper exits `0` only if ready. It exits nonzero when blockers are present.

## Command Shape

```bash
python3 scripts/check_ec7h_environment_readiness.py \
  --bench-path /home/deploy/erp-projects/ec7h_controlled_bench \
  --site-name ec7h-test.local \
  --qa-user qa_ec7h_trace_user@example.invalid \
  --dataset-manifest-path /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json \
  --archive-path /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521 \
  --raw-trace-custodian TBD_QA_OWNER_CUSTODIAN \
  --redacted-output-candidate-path impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries \
  --repo-root /tmp/erpai_pr4_postmerge_verify \
  --archive-retention-marker RETENTION.md
```

This command is safe to run as a read-only check once the paths exist. It does not create paths or write traces.

## Focused Tests

Tests added:

- readiness passes when all passive inputs exist;
- readiness reports blockers when bench, site name, dataset, archive, custodian, or redacted output policy are missing/invalid;
- helper does not attempt to fix missing inputs.

Expected focused harness test result after EC-7I-G: `12 passed`.

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

EC-7I-G verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- EC-7I-F/G harness tests: `12 passed`
- Combined protocol/harness command: `29 passed`
- Python compile: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Final Recommendation

`ec_7i_g_passive_environment_readiness_helper_ready_for_counterpart_qa_review`

If accepted, the project has passive setup-support checks for dataset, archive, and environment readiness. The next step should still not be live trace collection unless a controlled environment actually exists and passes this helper.
