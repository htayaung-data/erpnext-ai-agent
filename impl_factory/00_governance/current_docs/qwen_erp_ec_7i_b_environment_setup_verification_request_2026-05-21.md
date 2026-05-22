# EC-7I-B Controlled Environment Setup/Verification Request

Decision: ec_7i_b_blocked_needs_owner_setup_approval

Date: 2026-05-21
Generated: 2026-05-21T08:05:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Site/user/dataset/archive creation performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7I-B verifies whether an existing controlled non-production Frappe/ERPNext bench/site is available for EC-7H live trace evidence, and if not, requests owner approval for a future setup slice. This is a request/verification packet only. It does not create a site, create a user, seed a dataset, activate an archive, deploy, instrument, collect traces, stage, commit, or push.

## Existing Environment Verification

No existing controlled non-production Frappe/ERPNext bench/site was verified.

Observed evidence:

- Source verification checkout: `/tmp/erpai_pr4_postmerge_verify`
- Source checkout HEAD: `1504158`
- Source checkout is not a live bench/site.
- Bench/site directory scan found only editor/workbench directories and no active Frappe `sites`/`apps` structure under `/home/deploy`.
- Config scan found only historical migration-pack backups:
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_backups/migration_pack/20260213_155948/common_site_config.json`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_backups/migration_pack/20260213_155948/site_config.json`
- `/home/deploy/erp-projects/migration_pack/20260213_155948/common_site_config.json`
- `/home/deploy/erp-projects/migration_pack/20260213_155948/site_config.json`
- No `qa_ec7h_trace_user` evidence was found.
- No `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` dataset artifact was found.

Because no controlled environment is verified, EC-7I-B closes as `ec_7i_b_blocked_needs_owner_setup_approval`.

## Required Controlled Environment

Owner/QA should approve either:

1. Designate an existing controlled non-production bench/site and provide exact evidence.
2. Approve a separate EC-7I-C setup slice to create a controlled test bench/site.

Required fields before collection can ever proceed:

| Field | Required value |
|---|---|
| Bench path | Exact non-production bench path, owner-approved. |
| Site name | Exact non-production site name. |
| Bench command context | Working `bench --site <site>` command context. |
| Code/package state | Must include PR #4 main state `1504158` or a later owner-approved package. |
| App state | `ai_assistant_ui` installed and importable. |
| Data boundary | Synthetic/QA-approved data only. |
| Live trace group | Five light-semantic lanes only. |

## Proposed Setup Commands For Future Approval

These commands are examples for a future owner-approved setup slice. They must not be run as part of EC-7I-B.

Create or designate bench/site:

```bash
# Option A: verify existing bench/site, preferred if available.
cd TBD_CONTROLLED_BENCH_PATH
bench --site TBD_SITE_NAME list-apps
bench --site TBD_SITE_NAME execute frappe.utils.now

# Option B: create a fresh controlled test site, only after explicit approval.
cd TBD_PARENT_PATH
bench init ec7h-controlled-bench
cd ec7h-controlled-bench
bench new-site ec7h-test.local
bench get-app ai_assistant_ui TBD_APPROVED_APP_SOURCE
bench --site ec7h-test.local install-app ai_assistant_ui
```

Production deployment is forbidden. Any actual setup command must be reviewed against the local server layout before execution.

## Dedicated QA Test User

Preferred username: `qa_ec7h_trace_user`

Future setup/verification command shapes:

```bash
cd TBD_CONTROLLED_BENCH_PATH
bench --site TBD_SITE_NAME execute frappe.db.exists --args '["User", "qa_ec7h_trace_user"]'

# Create only after explicit owner approval.
bench --site TBD_SITE_NAME execute frappe.get_doc --kwargs '{
  "doctype": "User",
  "email": "qa_ec7h_trace_user@example.invalid",
  "first_name": "QA EC7H Trace",
  "enabled": 1
}'
```

Required policy:

- non-production only;
- minimum necessary roles;
- synthetic data only;
- disable/remove after trace window if owner/QA require.

## Synthetic Dataset Manifest

Dataset id: `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001`

Recommended future manifest path:

`impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Minimum manifest requirements:

- five light-semantic lane coverage;
- accepted/success cases;
- degraded/low-confidence cases;
- runtime-error/fallback cases only if safely triggerable;
- missing-metadata cases only if safely triggerable;
- no production customer/vendor/entity/document names;
- expected metadata and redaction outcomes per scenario.

Future validation command shape:

```bash
python3 scripts/validate_ec7h_synthetic_dataset.py \
  impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
```

The validator script/manifest should be proposed in a separate approved setup slice if needed.

## Secure Raw Trace Archive

Proposed path:

`/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`

Current status:

- parent `/home/deploy/erp-projects/_cleanup_archives` exists;
- exact raw archive path does not exist;
- no archive was created in EC-7I-B.

Future owner-approved activation command shape:

```bash
mkdir -p /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
chmod 750 /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
```

Required missing owner input:

- named raw trace custodian;
- allowed user/group ownership;
- retention policy;
- checksum/manifest policy.

Raw traces must never be written to repo or attached to governance reports.

## Redacted Output Candidate Path

Recommended candidate path:

`impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/`

Future use requires:

- EC-7H-B-D redaction;
- `validate_live_trace_fixture(...)` PASS;
- owner/QA approval before repo inclusion;
- packaging review before staging/commit.

No redacted output path was created in EC-7I-B.

## Cleanup / Rollback Policy

Any future setup slice must define rollback before execution:

- disable/remove `qa_ec7h_trace_user` after trace window if required;
- remove synthetic site records if owner/QA require;
- archive raw traces under custodian policy;
- never delete governance evidence without packaging approval;
- no production data cleanup because production data must not be used;
- no ERP UI, seed/data, temp/probe/cache, UX, Filter, MI, or family expansion cleanup inside EC-7I.

## Verification Commands For Future Setup Review

Before any future collection attempt:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol

cd TBD_CONTROLLED_BENCH_PATH
bench --site TBD_SITE_NAME list-apps
bench --site TBD_SITE_NAME execute frappe.db.exists --args '["User", "qa_ec7h_trace_user"]'
bench --site TBD_SITE_NAME execute ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness
```

Expected backend posture:

- direct assistant inventory: `0 / 1 / 27`;
- formal raw append scan: only `authorized_emission.py:271`, `authorized_emission.py:327`;
- excluded status scan: clean;
- staged files: `0`.

## Passive Verification Results

EC-7I-B passive verification:

- Source checkout HEAD: `1504158`
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- Scoped report diff check: PASS
- Excluded status scan: clean
- Staged files: `0`
- Environment setup: not performed
- Live trace collection: not performed
- Existing controlled bench/site: not verified
- QA test user: not verified
- Synthetic dataset: not found
- Raw archive exact path: not activated

## Non-Goals

- `no_live_trace_collection`
- `no_production_data`
- `no_strict_enforcement`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_production_deployment`
- `no_site_user_dataset_archive_creation`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7i_b_blocked_needs_owner_setup_approval`

Owner/QA should either provide an existing controlled bench/site with exact evidence or approve a narrow EC-7I-C setup slice. Until then, EC-7H live trace collection remains paused.
