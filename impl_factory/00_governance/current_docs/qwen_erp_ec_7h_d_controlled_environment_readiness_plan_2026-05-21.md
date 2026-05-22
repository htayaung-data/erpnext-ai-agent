# EC-7H-D Controlled Environment Readiness Plan

Decision: ec_7h_d_controlled_environment_readiness_plan_ready_for_counterpart_review

Date: 2026-05-21
Generated: 2026-05-21T02:20:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Deployment performed: `false`
Environment creation performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-D defines the readiness plan for a controlled non-production environment before any EC-7H live trace collection. EC-7H-C-C correctly blocked collection because the server state did not provide a verified live bench/site, QA test user, named synthetic dataset, raw trace custodian, or activated secure archive. EC-7H-D is the planning step to make those prerequisites explicit.

This report is plan-only. It does not deploy, create a site, create users, seed data, collect traces, add instrumentation, change runtime behavior, enable strict enforcement, stage, commit, or push.

## Readiness Inputs Required

| Input | Required decision | Readiness rule |
|---|---|---|
| Controlled bench/site | Exact non-production bench and site name | Must be staging or controlled test only. Source checkouts such as `/tmp/erpai_pr4_postmerge_verify` are not valid live sites. |
| QA test user | Dedicated user, preferably `qa_ec7h_trace_user` | Must exist on the controlled site before collection. If unavailable, create only in a separately approved environment setup slice. |
| Synthetic dataset | `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` | Must be synthetic or QA-approved, named, and inspectable before collection. No production data. |
| Raw trace custodian | Named QA/Owner custodian | Development may collect only under approval; raw traces remain under QA/Owner custody. |
| Secure archive | External path outside repo | Proposed archive: `/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`. Activation requires separate approval and access verification. |
| Redacted output policy | Candidate path and approval owner | No redacted summary enters repo unless EC-7H-B-D validation passes and owner/QA approve inclusion. |

## Controlled Environment Options

EC-7H-D does not choose or create the environment. Owner/QA should select one of these options:

| Option | Description | Risk | Recommendation |
|---|---|---|---|
| Existing staging bench/site | Use an already deployed non-production ERP/Frappe site with the merged PR #4 code. | Lowest if site is available and isolated. | Preferred. |
| Fresh controlled test site | Create a new non-production site from approved baseline and deploy only accepted AI Assistant stabilization code. | Medium; requires setup/deployment approval. | Acceptable if existing staging is unavailable. |
| Source checkout only | Use `/tmp/erpai_pr4_postmerge_verify` or similar source tree. | Invalid for live traces; no runtime site/session context. | Not allowed. |
| Production site | Use real production data/session. | High; violates current owner boundary. | Not allowed without separate owner/QA production-data exception. |

## Required Environment Readiness Checklist

Before EC-7H collection can be requested again, the environment owner must provide:

- bench path;
- site name;
- site URL or bench command context if browserless/backend-only;
- deployed commit or package hash;
- confirmation PR #4 / commit `d3ce165` behavior is present;
- QA test user username;
- confirmation the QA user has only the permissions needed for synthetic test scenarios;
- synthetic dataset manifest for `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001`;
- raw trace custodian;
- secure archive path and access policy;
- redacted output candidate path;
- explicit confirmation that no production data is used.

If any checklist item is missing, collection remains blocked.

## Synthetic Dataset Requirements

`EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` must include only synthetic or QA-approved prompts/records for these lanes:

| Lane | Minimum synthetic cases |
|---|---|
| `frontdoor_semantic_classification` | accepted/success, invalid or degraded semantic parse, missing metadata if safely triggerable |
| `fresh_query_interpretation` | accepted/success, low-confidence or degraded interpretation, fallback if safely triggerable |
| `followup_interpretation` | accepted/success, rejected/not-applicable follow-up, deterministic fallback if safely triggerable |
| `semantic_reasoning_activation` | accepted/success, runtime-error/degraded activation if safely triggerable |
| `semantic_repair_intent` | accepted/success, not-applicable/degraded repair intent |

Dataset manifest should record:

- scenario id;
- lane id;
- synthetic prompt or synthetic record reference;
- expected metadata outcome;
- whether fallback/degraded status is expected;
- whether final-answer authority should remain not applicable;
- redaction expectation.

The dataset must not include customer/vendor/entity names copied from production data.

## QA Test User Requirements

Preferred test user: `qa_ec7h_trace_user`.

The QA user should:

- be created only on the controlled non-production site;
- have enough access to run the synthetic semantic scenarios;
- avoid broad administrative access unless required by the test harness;
- be disabled or removed after the approved collection window if owner/QA require;
- not be reused for production testing.

If the user does not exist, EC-7H-D recommends a separate owner-approved setup slice, not ad hoc creation during collection.

## Raw Trace Custody And Archive Activation

Raw traces must stay outside repo. Proposed archive path:

`/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/`

Activation checklist:

- archive path created by or under QA/Owner approval;
- permissions restricted to custodian-approved users;
- no raw traces copied into git worktrees;
- no raw traces attached to governance reports;
- manifest records scenario id, timestamp, collector, and checksum only;
- redacted summaries generated from archive-held raw traces must pass EC-7H-B-D validation before sharing.

If this path cannot be created or permissioned safely, collection remains `blocked_no_secure_archive`.

## Redacted Output Candidate Policy

No redacted output is written in EC-7H-D. A future collection slice must name exact redacted output paths before writing.

Recommended candidate, subject to QA approval:

`impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/`

Repo inclusion is allowed only for:

- synthetic fixtures; or
- redacted summaries that pass `validate_live_trace_fixture(...)`; and
- owner/QA-approved evidence files.

Failed redacted candidates remain outside repo in QA archive notes.

## Exact Future Collection Command Shape

EC-7H-D does not run these commands. The future collection slice should fill in the `TBD_*` values and run one scenario at a time:

```bash
cd TBD_CONTROLLED_BENCH_PATH

# Confirm site and code state.
bench --site TBD_SITE_NAME execute ai_assistant_ui.qwen_chat.service.ping_runtime_metadata_readiness

# Collect one approved synthetic scenario using existing runtime/session/tool/audit metadata only.
bench --site TBD_SITE_NAME execute ai_assistant_ui.qwen_chat.live_trace_collection.collect_light_semantic_trace \
  --kwargs '{
    "scenario_id": "TBD_SCENARIO_ID",
    "lane_id": "frontdoor_semantic_classification",
    "test_user": "qa_ec7h_trace_user",
    "dataset_id": "EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001",
    "raw_archive_path": "/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/",
    "runtime_effect": "none"
  }'
```

Important: the command shape above is a planning placeholder. It must not be executed until the actual collection function/command exists, is reviewed, and is separately approved. If the current runtime does not already expose such a safe command, EC-7H must add a plan or harness proposal before collection.

## Pass / Warn / Block Criteria

| Decision | Criteria |
|---|---|
| `environment_ready_for_collection_request` | Bench/site, test user, dataset, custodian, archive, and redacted output policy are all verified. |
| `environment_warn_partial_readiness` | Some fields are verified but collection coverage would be partial. No collection starts. |
| `blocked_no_controlled_site` | No verified staging/test site. |
| `blocked_no_test_user` | Dedicated QA test user missing or unverifiable. |
| `blocked_no_synthetic_dataset` | `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` missing or not QA-approved. |
| `blocked_no_raw_trace_custodian` | No named QA/Owner custodian. |
| `blocked_no_secure_archive` | External archive missing or permission policy unsafe. |
| `blocked_no_safe_collection_command` | No reviewed safe command/procedure for existing metadata capture. |

## Verification Expectations

EC-7H-D should remain passive and verify that backend safety posture is unchanged:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- EC-7H-B protocol tests: PASS
- Scoped diff check: PASS
- Excluded status scan: clean
- Staged files: `0`

## Verification Results

EC-7H-D passive verification reproduced:

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
- `no_environment_creation`
- `no_test_user_creation`
- `no_dataset_creation`
- `no_archive_activation`
- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_deployment`
- `no_runtime_behavior_change`
- `no_route_model_report_selection_change`
- `no_answer_text_change`
- `no_new_instrumentation`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7h_d_controlled_environment_readiness_plan_ready_for_counterpart_review`

Next should be an owner/QA environment decision, not live trace collection. If the environment inputs are provided, the following slice can be EC-7H-E environment readiness verification. If they are not provided, EC-7H remains blocked from collection.
