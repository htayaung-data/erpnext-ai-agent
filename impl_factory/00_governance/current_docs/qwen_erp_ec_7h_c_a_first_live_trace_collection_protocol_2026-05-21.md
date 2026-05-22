# EC-7H-C-A First Live-Trace Collection Protocol

Decision: ec_7h_c_a_first_live_trace_collection_protocol_ready_for_counterpart_review

Date: 2026-05-21
Generated: 2026-05-21T00:55:00+00:00
Base: `main` post-PR #4 verification worktree
Head: `1504158`
Runtime effect: `none`
Strict enforcement enabled: `false`
Deployment performed: `false`
Live trace collection performed: `false`
Staging/commit/push performed: `false`

## Purpose

EC-7H-C-A defines the first safe live-trace collection protocol after EC-7H-B-D redaction hardening. This is a protocol/report slice only. It does not collect live traces, add instrumentation, change runtime behavior, enable strict enforcement, deploy, stage, commit, or push.

## First Lane Group

The first live-trace collection group should be limited to light semantic lanes:

| Lane | Expected role | Reason for first collection |
|---|---|---|
| `frontdoor_semantic_classification` | `light_semantic` | Entry semantic classifier with EC-7E-B provenance wiring and EC-7F-B probes. |
| `fresh_query_interpretation` | `light_semantic` | Active semantic interpretation path with accepted fallback strict-readiness guard. |
| `followup_interpretation` | `light_semantic` | Follow-up semantic path where fallback propagation was explicitly hardened. |
| `semantic_reasoning_activation` | `light_semantic` | Semantic activation signal with degraded-status guard coverage. |
| `semantic_repair_intent` | `light_semantic` | Repair intent classifier with accepted non-applicable/degraded metadata behavior. |

No heavy reasoning, governed-tool helper, deterministic/control, browser, ERP UI, or production UAT lanes are included in EC-7H-C-A.

## Environment

Live-trace collection, when separately approved, must use only:

- staging or controlled test site;
- synthetic or QA-approved test records;
- no production data unless owner and QA explicitly approve in writing;
- no unredacted trace sharing;
- no new runtime instrumentation unless separately approved;
- existing session/tool/audit/runtime metadata payloads only.

If a scenario cannot be safely triggered in staging without new instrumentation or production data, it must be marked `not_collected` rather than forced.

## Scenarios

Each lane should attempt these scenarios when safely triggerable:

| Scenario | Expected metadata behavior | Collection rule |
|---|---|---|
| Accepted/success | Complete AI metadata may be `strict_ready` for provenance. | Collect from existing runtime metadata payloads only. |
| Degraded or low-confidence | Valid metadata but not `strict_ready`; fallback state must be visible. | Use safe synthetic prompts/records. |
| Runtime error/fallback | Valid metadata but not `strict_ready`; fallback reason must be visible. | Only trigger if safe without deployment or code changes. |
| Missing metadata | Must not become `strict_ready`; missing fields must be visible. | Prefer mocked/staging-safe trigger; otherwise mark `not_collected`. |

## Capture Sources

Approved capture sources are limited to existing backend artifacts:

- session document message/tool payloads;
- `qwen_tool_trace` payloads;
- runtime metadata envelopes;
- model-role observability payloads;
- authorized-emission/final-answer authority payloads where present;
- existing audit/trace payloads already emitted by the lane.

Disallowed capture sources:

- raw browser screenshots or UI recordings;
- raw model prompts or unredacted model outputs;
- database exports;
- production session dumps;
- ad hoc runtime instrumentation;
- new route/model/report-selection logging.

## Redaction Flow

Future collection must follow this sequence:

1. Capture raw trace only into an external secure archive.
2. Build a candidate EC-7H fixture from existing trace payloads.
3. Apply `redact_live_trace_record(...)` from EC-7H-B-D.
4. Validate with `validate_live_trace_fixture(...)`.
5. If validation fails, keep the redacted candidate out of repo and record the failure reason in QA archive notes.
6. Share only synthetic fixtures or explicitly owner/QA-approved redacted summaries.

Raw traces must never be committed or shared in repo. Unredacted sensitive traces remain `not_versioned`.

## Storage Policy

| Artifact type | Storage policy |
|---|---|
| Raw live trace | External secure archive only. |
| Unredacted sensitive trace | Not versioned. |
| Redacted live trace summary | Repo or QA archive only with owner/QA approval. |
| Synthetic fixture | Repo-allowed after EC-7H-B-D validation. |
| Protocol/schema/report | Repo governance doc. |

## Pass / Warn / Block Criteria

| Decision | Meaning |
|---|---|
| `live_trace_pass` | Required fields present, EC-7H-B-D validation passes, no raw sensitive data, expected metadata behavior observed. |
| `live_trace_warn` | Trace is redacted/valid but scenario coverage is partial or fallback/missing metadata needs follow-up. Runtime remains unaffected. |
| `live_trace_block_release` | Redaction validation fails, raw sensitive data appears in a shareable artifact, strict-readiness is incorrectly claimed, or final-answer authority separation is violated. |
| `not_collected` | Scenario was not safely triggerable without new instrumentation, deployment, production data, or behavior changes. |

All EC-7H-C live-trace evidence has `runtime_effect=none`. These decisions are release-readiness evidence only and must not block runtime behavior.

## Verification Commands

Required passive checks for this protocol slice:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 - <<'PY'
import sys, types
fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.get_meta = lambda *args, **kwargs: types.SimpleNamespace(fields=[])
fake_frappe.get_traceback = lambda: ""
fake_frappe.log_error = lambda *args, **kwargs: None
fake_frappe.throw = lambda *args, **kwargs: (_ for _ in ()).throw(Exception(args[0] if args else "frappe.throw"))
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.session = types.SimpleNamespace(user="Administrator")
fake_frappe.db = types.SimpleNamespace(exists=lambda *a, **k: False, get_value=lambda *a, **k: None, get_all=lambda *a, **k: [], sql=lambda *a, **k: [], count=lambda *a, **k: 0)
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules["frappe"] = fake_frappe
import ai_assistant_ui.qwen_chat.service
print("FAKE_FRAPPE_SERVICE_IMPORT=PASS")
PY

PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest -q \
  ai_assistant_ui.tests.test_live_trace_evidence_protocol

git status --short
```

The direct assistant inventory must remain `0 / 1 / 27`. The formal raw append scan must show only `authorized_emission.py:271` and `authorized_emission.py:327`. Excluded status scan must remain clean.

## Verification Results

EC-7H-C-A passive verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan: `authorized_emission.py:271`, `authorized_emission.py:327`
- EC-7H-B protocol tests: `17 passed`
- Staged files: `0`
- Excluded status scan: clean
- Scoped report diff check: PASS

## Non-Goals

- `no_live_trace_collection`
- `no_strict_enforcement`
- `no_runtime_blocking`
- `no_deployment`
- `no_runtime_behavior_change`
- `no_route_model_report_selection_change`
- `no_answer_text_change`
- `no_new_instrumentation`
- `no_cleanup`
- `no_ux_filter_mi_family_expansion`
- `no_staging_commit_push`

## Final Recommendation

`ec_7h_c_a_first_live_trace_collection_protocol_ready_for_counterpart_review`

If accepted, Counterpart and QA may approve a separate EC-7H-C-B collection attempt for the first light-semantic lane group. EC-7H-C-A itself does not approve collection, deployment, strict enforcement, or repo inclusion of live trace artifacts.
