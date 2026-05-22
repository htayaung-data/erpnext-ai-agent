# EC-7H-C-B Light Semantic Live-Trace Collection Approval Request

Decision: ec_7h_c_b_collection_approval_request_ready_for_counterpart_qa_owner_review

Date: 2026-05-21
Generated: 2026-05-21T01:20:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Live trace collection performed: `false`
Deployment performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-C-B requests approval for the first live-trace collection attempt, limited to the five light-semantic lanes approved in EC-7H-C-A. This artifact is an approval request only. It does not collect traces, modify runtime behavior, add instrumentation, enable strict enforcement, deploy, stage, commit, or push.

## Exact Environment

Collection may proceed only after Counterpart, QA, and owner approve this request and identify the exact controlled environment:

- environment type: staging or controlled test site only;
- production data: prohibited unless owner and QA explicitly approve a separate exception;
- test records: synthetic or QA-approved only;
- browser/UI collection: not required for EC-7H-C-B;
- runtime changes: prohibited;
- new instrumentation: prohibited;
- raw trace sharing: prohibited.

Placeholder pending owner approval:

| Field | Required owner/QA value before collection |
|---|---|
| Site / bench | `TBD_CONTROLLED_TEST_SITE` |
| Test user | `TBD_QA_TEST_USER` |
| Synthetic dataset reference | `TBD_SYNTHETIC_DATASET_OR_RECORDS` |
| Raw trace custodian | `TBD_QA_OR_OWNER_CUSTODIAN` |
| External secure archive location | `TBD_EXTERNAL_SECURE_ARCHIVE` |

If any value remains `TBD`, collection must not start.

## Lane Group

Approved collection group, pending this request approval:

| Lane | Expected role | Required outcome evidence |
|---|---|---|
| `frontdoor_semantic_classification` | `light_semantic` | Runtime metadata envelope, model role/name, fallback state, strict-readiness result. |
| `fresh_query_interpretation` | `light_semantic` | Runtime metadata envelope, fallback/degraded state when applicable. |
| `followup_interpretation` | `light_semantic` | Runtime metadata envelope, child/fallback metadata preservation. |
| `semantic_reasoning_activation` | `light_semantic` | Runtime metadata envelope, degraded/error status handling. |
| `semantic_repair_intent` | `light_semantic` | Runtime metadata envelope, not-applicable/degraded handling. |

No heavy reasoning, NBU shadow, governed-tool helper, deterministic/control, service-control, ERP UI, or production UAT traces are included.

## Exact Scenarios

Each lane should collect these scenarios only when safely triggerable with synthetic/QA-approved data:

| Scenario | Intent | Expected collection result |
|---|---|---|
| Accepted/success | Normal light-semantic accepted result with complete metadata. | Valid redacted summary may show `strict_ready` for provenance only. |
| Degraded or low-confidence | Low-confidence, rejected, invalid, or not-applicable semantic outcome. | Valid redacted summary must not be `strict_ready`; fallback/degraded reason visible. |
| Runtime error/fallback | Safely triggerable runtime failure or deterministic fallback. | Valid redacted summary must not be `strict_ready`; fallback reason visible. |
| Missing metadata | Safely triggerable missing model metadata. | Valid redacted summary must not be `strict_ready`; missing metadata visible. |

If a scenario cannot be triggered without instrumentation, deployment, production data, or behavior changes, record `not_collected` rather than forcing it.

## Procedure

No live trace collection is approved until this request is accepted. If accepted, the proposed procedure is:

1. Confirm controlled site, test user, synthetic dataset, raw trace custodian, and external secure archive.
2. Confirm the runtime is already deployed to the controlled site without EC-7H-specific code changes.
3. Run one lane/scenario at a time using synthetic or QA-approved prompts/records.
4. Capture only existing session/tool/audit/runtime metadata payloads.
5. Store raw trace artifacts only in the external secure archive under the raw trace custodian.
6. Build redacted candidate summaries from the captured payloads.
7. Run `redact_live_trace_record(...)` and `validate_live_trace_fixture(...)` from EC-7H-B-D.
8. Discard or keep out of repo any summary that fails validation.
9. Share only validation-passing redacted summaries or synthetic fixtures after owner/QA approval.

## Capture Sources

Allowed:

- existing session document payloads;
- existing tool/audit payloads;
- runtime metadata envelopes;
- model-role observability metadata;
- final-answer authority / authorized-emission payloads if already present;
- existing trace payloads emitted by the lane.

Forbidden:

- new logging or instrumentation;
- raw model prompts or raw model output in repo;
- database dumps;
- production session dumps;
- screenshots as trace evidence;
- browser telemetry;
- route/model/report-selection changes.

## Raw Trace Custody

Raw trace handling must be owner/QA controlled:

- raw traces stay outside repo;
- raw traces are stored only in `TBD_EXTERNAL_SECURE_ARCHIVE`;
- raw trace custodian must be named before collection;
- Development Agent must not version raw or unredacted traces;
- unredacted sensitive traces are `not_versioned`;
- any sharing of redacted summaries requires owner/QA approval.

## Redacted Output Locations

Proposed redacted output policy:

| Output | Location | Approval requirement |
|---|---|---|
| Raw live trace | External secure archive only | Owner/QA custodian required. |
| Unredacted sensitive trace | Not versioned | Must not be shared in repo. |
| Failed redacted candidate | QA archive notes only | Not repo-eligible. |
| Passing redacted summary | QA archive or repo governance/evidence path | Owner/QA approval required before repo inclusion. |
| Synthetic fixture | Repo-eligible | Must pass EC-7H-B-D validation. |

No concrete redacted summary path is approved by EC-7H-C-B. A future collection slice must name exact output paths before writing any redacted evidence into the repo.

## Pass / Warn / Block Criteria

| Decision | Criteria |
|---|---|
| `live_trace_pass` | Scenario collected from approved environment, redaction validation passes, expected metadata behavior observed, no raw sensitive data in shareable artifact. |
| `live_trace_warn` | Scenario safely collected but metadata is partial, fallback/degraded reason needs follow-up, or coverage is incomplete. |
| `live_trace_block_release` | Raw sensitive data appears in shareable artifact, redaction validation fails, strict-ready is incorrectly claimed, authority separation is violated, or collection used unapproved data/source. |
| `not_collected` | Scenario could not be safely collected under EC-7H-C-B constraints. |

All outcomes remain evidence-only and have `runtime_effect=none`.

## Required Pre-Collection Checks

Before any future approved collection attempt:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol
```

Also confirm:

- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Excluded status scan: clean
- staged files: `0`

## Non-Goals

- `no_live_trace_collection_yet`
- `no_new_instrumentation`
- `no_runtime_behavior_change`
- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_route_model_report_selection_change`
- `no_answer_text_change`
- `no_deployment`
- `no_staging_commit_push`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`

## Final Recommendation

`ec_7h_c_b_collection_approval_request_ready_for_counterpart_qa_owner_review`

If accepted, the next slice may be a separately approved EC-7H-C-C live-trace collection attempt for this exact light-semantic lane group, using only named controlled environment values and the EC-7H-B-D redaction protocol. EC-7H-C-B itself does not approve collection.
