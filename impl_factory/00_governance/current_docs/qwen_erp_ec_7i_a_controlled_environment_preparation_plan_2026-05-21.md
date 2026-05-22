# EC-7I-A Controlled Test Environment Preparation Plan

Decision: ec_7i_a_controlled_environment_preparation_plan_ready_for_counterpart_qa_review

Date: 2026-05-21
Generated: 2026-05-21T07:25:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Environment setup performed: `false`
Production deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-E correctly blocked live-trace collection because no controlled non-production bench/site, dedicated QA user, named synthetic dataset, raw trace custodian, or activated secure archive was verified. EC-7I-A moves one level earlier: it defines how to prepare the controlled environment deliberately before returning to EC-7H collection.

This is a plan/report slice only. It does not create a site, create users, seed data, activate an archive, collect traces, deploy to production, instrument runtime behavior, enable strict enforcement, stage, commit, or push.

## Safest Environment Path

Preferred path: designate an existing isolated non-production Frappe/ERPNext bench/site if one already exists and can be proven to run the accepted main branch package.

Fallback path: create a fresh controlled test bench/site under a separately approved EC-7I-B setup slice.

Disallowed paths:

- source checkout only, such as `/tmp/erpai_pr4_postmerge_verify`;
- production bench/site;
- staging site with production data unless owner/QA grant a separate exception;
- ad hoc runtime instrumentation or route/model/report-selection changes.

## Environment Candidate Requirements

| Requirement | Required evidence before use |
|---|---|
| Non-production bench path | Absolute bench path, owner, and access boundary. |
| Site name | Exact Frappe site name and confirmation it is not production. |
| Code/package state | Commit/package includes PR #4 merge `1504158` and accepted EC-7H-B-D protocol files when applicable. |
| App availability | `ai_assistant_ui` app installed and importable. |
| Data boundary | Synthetic/QA-approved data only. |
| Network/access | Limited to QA/Owner-approved users. |
| Trace archive access | Raw traces stay outside repo with restricted permissions. |

If an existing environment is found, EC-7I-B should verify evidence only. If none exists, EC-7I-B should request explicit setup approval before creating anything.

## QA Test User Plan

Preferred username: `qa_ec7h_trace_user`.

Required properties:

- exists only on the controlled non-production site;
- has the minimum roles required for the light-semantic trace scenarios;
- does not have broad administrator permissions unless explicitly required and approved;
- is tied to synthetic/QA-approved data only;
- can be disabled or removed after the approved trace window;
- must not be used for production testing.

Future EC-7I-B setup/verification should either:

- verify `qa_ec7h_trace_user` exists; or
- request owner-approved creation with exact roles and cleanup policy.

## Synthetic Dataset Manifest

Dataset id: `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001`

The dataset must be a named manifest, not an informal prompt list. Recommended manifest path for a future approved setup:

`impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Repo inclusion of this manifest should be owner/QA-approved because it is synthetic and should contain no production data.

Required manifest fields:

- `dataset_id`
- `scenario_id`
- `lane_id`
- `scenario_type`
- `synthetic_prompt`
- `synthetic_record_reference`
- `expected_metadata_status`
- `expected_strict_readiness_status`
- `expected_fallback_used`
- `expected_fallback_reason`
- `expected_authority_status`
- `redaction_expectation`
- `qa_owner`

Minimum lane coverage:

| Lane | Required synthetic scenarios |
|---|---|
| `frontdoor_semantic_classification` | accepted/success, invalid/degraded, missing metadata if safely triggerable |
| `fresh_query_interpretation` | accepted/success, low-confidence/degraded, fallback if safely triggerable |
| `followup_interpretation` | accepted/success, rejected/not-applicable, deterministic fallback if safely triggerable |
| `semantic_reasoning_activation` | accepted/success, runtime-error/degraded if safely triggerable |
| `semantic_repair_intent` | accepted/success, not-applicable/degraded |

Dataset rules:

- no production customer/vendor/entity/document names;
- synthetic entity names should be clearly fake, for example `EC7H Synthetic Customer A`;
- no real monetary balances;
- no real account, invoice, SO, PO, or vendor identifiers;
- all scenario prompts should be safe to include in a redacted or synthetic repo artifact.

## Raw Trace Custodian Policy

Raw trace custodian: QA/Owner only.

Policy:

- Development may assist collection only after explicit approval;
- raw traces are never committed;
- raw traces are never attached to governance reports;
- raw traces are stored only in the external secure archive;
- raw trace access is limited to named custodian-approved users;
- any redacted summary must pass EC-7H-B-D validation before sharing;
- repo inclusion of redacted summaries requires explicit owner/QA approval.

Future EC-7I-B must name the custodian before any archive activation.

## External Secure Archive Plan

Proposed path:

`/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`

Future setup requirements:

- create only after owner approval;
- owner/group permissions restricted to QA/Owner-approved users;
- no git repository inside the archive;
- include a non-sensitive manifest with scenario id, timestamp, collector, checksum, and redaction status;
- do not store redacted repo artifacts in the raw archive path;
- do not copy raw traces into `/tmp/erpai_pr4_postmerge_verify` or any git worktree.

Suggested future permission command shape, not approved for execution in EC-7I-A:

```bash
mkdir -p /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
chmod 750 /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
```

Actual owner/group selection must be provided before execution.

## Redacted Output Candidate Path

Recommended candidate path for future owner/QA-approved redacted summaries:

`impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/`

Rules:

- do not create this path in EC-7I-A;
- only write validation-passing redacted summaries;
- validate with EC-7H-B-D `validate_live_trace_fixture(...)`;
- include only synthetic fixtures or owner/QA-approved redacted summaries;
- generated output should be package-reviewed before any commit.

## Future EC-7I-B Setup / Verification Commands

These are command shapes for future approval, not commands run in EC-7I-A.

Verify an existing bench/site:

```bash
cd TBD_BENCH_PATH
bench --site TBD_SITE_NAME list-apps
bench --site TBD_SITE_NAME execute frappe.db.exists --args '["User", "qa_ec7h_trace_user"]'
bench --site TBD_SITE_NAME execute ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness
```

Verify dataset manifest:

```bash
python3 scripts/validate_ec7h_synthetic_dataset.py \
  impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
```

Verify archive readiness:

```bash
test -d /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
test -w /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
find /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521 -maxdepth 1 -type d -name .git -print
```

Backend safety checks:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol
```

## Risks

| Risk | Mitigation |
|---|---|
| Existing staging site contains production-like data | Require synthetic dataset manifest and owner/QA data-boundary signoff. |
| QA user has excessive permissions | Define minimal roles before creation/verification. |
| Raw traces accidentally enter repo | Keep raw archive outside repo and require EC-7H-B-D validation before any shareable artifact. |
| Setup work becomes deployment work | EC-7I-B must be explicitly approved before environment setup; production deployment remains forbidden. |
| Collection command does not exist safely | Treat as `blocked_no_safe_collection_command` and plan a harness separately. |
| Generated redacted summaries become packaging drift | Package-review generated outputs before staging/commit. |

## Rollback / Cleanup Boundaries

Future cleanup must be separately approved. Planned cleanup boundaries:

- disable or remove `qa_ec7h_trace_user` after trace window if owner/QA require;
- archive or delete raw traces only under custodian policy;
- remove synthetic test records from the controlled site if created there;
- do not delete repo governance evidence without packaging approval;
- do not touch production data;
- do not clean unrelated ERP UI, seed/data, temp/probe/cache streams inside EC-7I.

## Passive Verification Results

EC-7I-A preserved the same backend posture:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- Scoped report diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Non-Goals

- `no_live_trace_collection`
- `no_production_data`
- `no_production_deployment`
- `no_environment_creation`
- `no_test_user_creation`
- `no_dataset_creation`
- `no_archive_creation`
- `no_runtime_behavior_change`
- `no_instrumentation`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7i_a_controlled_environment_preparation_plan_ready_for_counterpart_qa_review`

If accepted, the next slice should be EC-7I-B controlled environment setup/verification request. EC-7I-B should either verify an existing environment with concrete owner-provided values or request explicit approval to create the site/user/dataset/archive. EC-7H live trace collection should remain paused until EC-7I confirms environment readiness.
