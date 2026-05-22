# EC-7I-C Controlled Environment Setup Plan

Decision: ec_7i_c_controlled_environment_setup_plan_ready_for_counterpart_qa_owner_review

Date: 2026-05-21
Generated: 2026-05-21T08:35:00+00:00
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

EC-7I-B was accepted as blocked because no usable controlled bench/site, QA user, dataset, or active archive exists. EC-7I-C designs the exact controlled environment setup before creating anything. This is a setup plan/request only.

No setup commands were executed in EC-7I-C.

## Recommended Setup Architecture

Safest path: create a fresh non-production Frappe/ERPNext controlled test bench/site dedicated to EC-7H trace evidence.

Recommended names:

| Item | Proposed value |
|---|---|
| Bench path | `/home/deploy/erp-projects/ec7h_controlled_bench` |
| Site name | `ec7h-test.local` |
| QA user | `qa_ec7h_trace_user` |
| Dataset id | `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` |
| Raw archive path | `/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/` |
| Redacted output candidate path | `impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/` |

Rationale:

- avoids accidental production data exposure;
- avoids relying on source checkout `/tmp/erpai_pr4_postmerge_verify` as a live site;
- gives QA/Owner explicit custody and cleanup boundaries;
- supports future live trace collection from real runtime/session/tool/audit metadata without production deployment.

## Proposed Setup Commands

These commands are proposed for a future owner-approved execution slice. Do not run them in EC-7I-C.

### 1. Create Controlled Bench / Site

```bash
cd /home/deploy/erp-projects

# Create a dedicated non-production bench only after owner/QA approval.
bench init ec7h_controlled_bench
cd /home/deploy/erp-projects/ec7h_controlled_bench

# Create a dedicated non-production site.
bench new-site ec7h-test.local

# Install required ERP/Frappe apps according to the server's approved baseline.
# Exact app sources must be confirmed before execution.
bench get-app erpnext TBD_APPROVED_ERPNEXT_SOURCE
bench get-app ai_assistant_ui TBD_APPROVED_AI_ASSISTANT_SOURCE
bench --site ec7h-test.local install-app erpnext
bench --site ec7h-test.local install-app ai_assistant_ui
```

If the server already has an approved bench creation process, use that process instead of these generic commands. Do not use production app sources or unreviewed branch history.

### 2. Verify Accepted AI Assistant Code State

```bash
cd /home/deploy/erp-projects/ec7h_controlled_bench
bench --site ec7h-test.local list-apps
bench --site ec7h-test.local execute ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness
```

If `ping_runtime_metadata_readiness` does not exist, EC-7I-D should either choose an existing safe import/readiness command or request a tiny harness plan. Do not add instrumentation inside EC-7I-C.

## Dedicated QA User

Preferred user: `qa_ec7h_trace_user`

Proposed creation commands for future approval:

```bash
cd /home/deploy/erp-projects/ec7h_controlled_bench

bench --site ec7h-test.local execute frappe.get_doc --kwargs '{
  "doctype": "User",
  "email": "qa_ec7h_trace_user@example.invalid",
  "first_name": "QA EC7H Trace",
  "enabled": 1,
  "send_welcome_email": 0
}'
```

Role policy:

- minimum permissions required for synthetic light-semantic trace scenarios;
- no production access;
- no broad Administrator role unless owner/QA explicitly approve;
- disable or remove after the trace evidence window if required.

Future verification:

```bash
bench --site ec7h-test.local execute frappe.db.exists --args '["User", "qa_ec7h_trace_user@example.invalid"]'
```

## Synthetic Dataset Manifest

Dataset id: `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001`

Proposed manifest path:

`/home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Optional repo candidate path, only if owner/QA approve versioning synthetic fixtures:

`impl_factory/00_governance/current_docs/generated/ec_7i_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json`

Proposed manifest schema:

```json
{
  "dataset_id": "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001",
  "data_classification": "synthetic_only",
  "qa_owner": "TBD_QA_OWNER",
  "scenarios": [
    {
      "scenario_id": "ec7h_frontdoor_success_001",
      "lane_id": "frontdoor_semantic_classification",
      "scenario_type": "accepted_success",
      "synthetic_prompt": "Open the synthetic sales dashboard for EC7H Synthetic Customer A.",
      "synthetic_record_reference": "EC7H_SYNTH_CUSTOMER_A",
      "expected_metadata_status": "covered",
      "expected_strict_readiness_status": "strict_ready",
      "expected_fallback_used": false,
      "expected_fallback_reason": "",
      "expected_authority_status": "not_applicable",
      "redaction_expectation": "no_raw_sensitive_values"
    }
  ]
}
```

Minimum scenario coverage:

- `frontdoor_semantic_classification`: accepted/success, invalid/degraded, missing metadata if safely triggerable.
- `fresh_query_interpretation`: accepted/success, low-confidence/degraded, fallback if safely triggerable.
- `followup_interpretation`: accepted/success, rejected/not-applicable, deterministic fallback if safely triggerable.
- `semantic_reasoning_activation`: accepted/success, runtime-error/degraded if safely triggerable.
- `semantic_repair_intent`: accepted/success, not-applicable/degraded.

Dataset rules:

- no production customer/vendor/entity/document names;
- use visibly synthetic names such as `EC7H Synthetic Customer A`;
- no real balances, invoices, account identifiers, SO/PO numbers, or vendor records;
- prompts must be safe to include in governance evidence.

## Secure Raw Trace Archive

Proposed path:

`/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`

Proposed future activation commands:

```bash
mkdir -p /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
chmod 750 /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
```

Custodian policy:

- raw trace custodian must be named by QA/Owner before activation;
- raw traces stay outside repo;
- no raw trace attached to governance reports;
- archive manifest may contain only non-sensitive scenario id, timestamp, collector, checksum, and redaction status;
- redacted summaries must pass EC-7H-B-D validation before sharing.

Open owner decisions:

- custodian name;
- allowed Unix owner/group;
- retention period;
- backup/encryption policy if required.

## Redacted Output Candidate Path

Recommended future path:

`impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/`

Rules:

- do not create in EC-7I-C;
- write only validation-passing redacted summaries;
- apply EC-7H-B-D `redact_live_trace_record(...)`;
- validate with EC-7H-B-D `validate_live_trace_fixture(...)`;
- repo inclusion requires explicit owner/QA approval;
- package-review generated outputs before staging/commit.

## Permissions

Recommended permission model:

| Resource | Permission policy |
|---|---|
| Controlled bench/site | Accessible to deployment owner and QA-approved operators only. |
| QA user | Non-production only, minimum roles. |
| Synthetic dataset | Readable by QA/development, contains no sensitive data. |
| Raw trace archive | `750` or stricter, owned by QA/Owner-approved user/group. |
| Redacted summaries | Repo candidate only after validation and owner/QA approval. |

## Cleanup / Rollback Procedure

Future setup slice must include rollback commands before execution:

```bash
# Disable QA user if required after trace window.
bench --site ec7h-test.local execute frappe.db.set_value --args '["User", "qa_ec7h_trace_user@example.invalid", "enabled", 0]'

# Remove synthetic dataset files if owner/QA require.
rm -f /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json

# Archive cleanup only under custodian policy.
# Do not delete raw trace archive without QA/Owner approval.
```

Boundaries:

- no production data cleanup;
- no unrelated ERP UI or seed/data cleanup;
- no deletion of governance docs without packaging approval;
- no broad repository cleanup inside EC-7I.

## Post-Setup Verification Commands

Future EC-7I-D or setup-verification slice should run:

```bash
cd /home/deploy/erp-projects/ec7h_controlled_bench
bench --site ec7h-test.local list-apps
bench --site ec7h-test.local execute frappe.db.exists --args '["User", "qa_ec7h_trace_user@example.invalid"]'
bench --site ec7h-test.local execute ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness

test -f /home/deploy/erp-projects/ec7h_controlled_bench/ec7h_synthetic_datasets/EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001.json
test -d /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521
test -w /home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521

python3 scripts/check_qwen_enterprise_guardrails.py
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol
```

Expected backend safety posture:

- direct assistant inventory: `0 / 1 / 27`;
- formal raw append scan: only `authorized_emission.py:271`, `authorized_emission.py:327`;
- excluded status scan: clean;
- no staged files unless a later packaging slice explicitly approves staging.

## Risks

| Risk | Mitigation |
|---|---|
| Bench setup accidentally uses production data | Require fresh site or owner-verified non-production site and synthetic dataset only. |
| App source ambiguity | Require exact approved app source before setup. |
| QA user over-permissioned | Owner/QA define minimum roles before creation. |
| Raw traces leak into repo | Archive outside repo; redacted summaries only after EC-7H-B-D validation and owner approval. |
| Setup command differs from server conventions | Review against actual server baseline before EC-7I-D execution. |
| Readiness command missing | Treat as blocker or plan a tiny harness separately; do not instrument in EC-7I-C. |

## Passive Verification Results

EC-7I-C passive verification preserved backend posture:

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
- `no_production_deployment`
- `no_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7i_c_controlled_environment_setup_plan_ready_for_counterpart_qa_owner_review`

If accepted, the next slice should be an owner-approved EC-7I-D setup execution request or a revised plan if QA requires architecture changes. No setup should run until owner/QA explicitly approve execution.
