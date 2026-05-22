# EC-7H-C-C Light Semantic Live-Trace Collection Preflight

Decision: ec_7h_c_c_blocked_missing_controlled_collection_inputs

Date: 2026-05-21
Generated: 2026-05-21T01:45:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-C-C is the controlled collection preflight for the first light-semantic live-trace group. Owner/Counterpart approved preparation only, not collection. This report identifies the required collection inputs and closes blocked because the controlled site, QA test user, and named synthetic dataset could not be verified from the server context.

## Owner Conditions

Approved collection scope remains limited to these five light-semantic lanes:

- `frontdoor_semantic_classification`
- `fresh_query_interpretation`
- `followup_interpretation`
- `semantic_reasoning_activation`
- `semantic_repair_intent`

Allowed data remains synthetic or QA-approved only. Runtime evidence must use existing session/tool/audit/runtime metadata only. EC-7H-B-D redaction must run before anything is shareable.

## Preflight Findings

| Required owner field | Required value | Preflight result | Decision |
|---|---|---|---|
| Controlled site / bench | Non-production controlled test/staging environment | Not identified. `/tmp/erpai_pr4_postmerge_verify` is a source checkout, not a live site. Server scan did not find an active Frappe `sites` directory under `/home/deploy`; only migration-pack config backups were found. | `blocked_no_controlled_site` |
| QA test user | Dedicated user, preferably `qa_ec7h_trace_user` | Not verified because no controlled site/bench was identified for a safe user lookup. | `blocked_no_test_user` |
| Synthetic dataset | `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` | Not found by file/path scan under `/home/deploy/erp-projects`. | `blocked_no_synthetic_dataset` |
| Raw trace custodian | QA/Owner custody only | Not named in server-verifiable form. | `blocked_no_raw_trace_custodian` |
| External secure archive | `/home/deploy/erp-projects/_cleanup_archives/ec7h_live_trace_raw_20260521/` | Parent archive directory exists. Specific raw archive path was not created because collection is blocked before archive activation. | `blocked_pending_secure_archive_activation` |

Because required owner fields remain unknown, EC-7H-C-C must not proceed to collection.

## Exact Procedure If Unblocked Later

This procedure is not approved for execution until the blocked fields above are resolved:

1. Confirm the exact non-production site/bench and test user.
2. Confirm synthetic dataset `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` exists and contains only synthetic or QA-approved records/prompts.
3. Confirm QA/Owner raw trace custodian and external secure archive path.
4. Run one lane/scenario at a time using existing runtime/session/tool/audit metadata only.
5. Capture raw traces only into the external secure archive.
6. Build redacted candidate summaries.
7. Apply `redact_live_trace_record(...)` and validate with `validate_live_trace_fixture(...)`.
8. Exclude any failing redacted candidate from repo.
9. Share only validation-passing redacted summaries or synthetic fixtures after owner/QA approval.

## Scenario Matrix

| Lane | Accepted/success | Degraded/low-confidence | Runtime error/fallback | Missing metadata |
|---|---|---|---|---|
| `frontdoor_semantic_classification` | Planned only | Planned only | Planned only if safely triggerable | Planned only if safely triggerable |
| `fresh_query_interpretation` | Planned only | Planned only | Planned only if safely triggerable | Planned only if safely triggerable |
| `followup_interpretation` | Planned only | Planned only | Planned only if safely triggerable | Planned only if safely triggerable |
| `semantic_reasoning_activation` | Planned only | Planned only | Planned only if safely triggerable | Planned only if safely triggerable |
| `semantic_repair_intent` | Planned only | Planned only | Planned only if safely triggerable | Planned only if safely triggerable |

Any scenario that requires instrumentation, deployment, production data, route/model/report-selection changes, or behavior changes remains `not_collected`.

## Proposed Redacted Output Candidate Path

No redacted output was written. If unblocked later, a candidate path should be named before collection, for example:

`impl_factory/00_governance/current_docs/generated/ec_7h_live_trace_redacted_summaries/`

Repo inclusion of any redacted summary remains separately owner/QA approved only.

## Pass / Warn / Block Criteria

| Decision | Criteria |
|---|---|
| `live_trace_pass` | Controlled site/user/dataset verified, redaction validation passes, expected metadata behavior observed, no raw sensitive data in shareable artifact. |
| `live_trace_warn` | Valid redacted evidence but partial scenario coverage or follow-up metadata concern. |
| `live_trace_block_release` | Redaction validation fails, raw sensitive data appears in shareable artifact, strict-ready is incorrectly claimed, authority separation is violated, or collection uses unapproved data/source. |
| `not_collected` | Scenario cannot be safely collected under EC-7H-C constraints. |
| `blocked_no_controlled_site` | No verified non-production site/bench. |
| `blocked_no_test_user` | No verified dedicated QA test user. |
| `blocked_no_synthetic_dataset` | Named synthetic dataset unavailable. |
| `blocked_no_secure_archive` | External archive path cannot be safely created/verified. |

## Verification Results

Passive verification for this preflight:

- Source checkout HEAD: `1504158`
- Live trace collection: not performed
- Runtime effect: `none`
- Staging/commit/push: not performed
- Controlled bench/site scan: no active site identified
- Synthetic dataset scan: `EC7H_LIGHT_SEMANTIC_SYNTHETIC_SET_001` not found
- Archive parent `/home/deploy/erp-projects/_cleanup_archives`: exists

Required runtime safety checks should still be run with the final packet before any future collection attempt:

- Guardrail: PASS expected
- Fake-Frappe service import: PASS expected
- Direct assistant inventory: `0 / 1 / 27` expected
- Formal raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327` expected
- EC-7H-B protocol tests: PASS expected
- Excluded status scan: clean expected

## Non-Goals

- `no_live_trace_collection`
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

`ec_7h_c_c_blocked_missing_controlled_collection_inputs`

Resolve the controlled site/bench, dedicated QA test user, named synthetic dataset, raw trace custodian, and external archive activation before any EC-7H live trace collection attempt. Do not collect live traces from `/tmp/erpai_pr4_postmerge_verify` because it is only a source verification checkout.
