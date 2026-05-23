# EC-8-C Compatibility Facade / Extraction Feasibility Plan

Decision target: `ec_8_c_compatibility_facade_extraction_feasibility_plan_ready_for_counterpart_qa_review`

## Scope

This is a report/test-only feasibility plan. No `service.py` implementation, helper extraction, import movement, routing change, answer-text change, final-answer authority change, strict enforcement, deployment, staging, commit, or push is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)
- Source of truth for public surface: EC-8-B public service/caller audit

## EC-8-B Inputs Used

| Input | Value |
| --- | ---: |
| `service.py` lines | 7809 |
| Top-level functions | 435 |
| Public functions | 215 |
| Public constants | 2 |
| `run_*` exports | 213 |
| Direct service import statements | 1 |
| Smoke/probe compatibility exports | 159 |
| Governance/test exports | 55 |

Direct import remains limited to `api.py:5: from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, handle_qwen_user_message`. `phase8_hardening_support.py` has callback/injection references and must remain behaviorally compatible, but it is not a direct service import.

## Feasibility Classification

| Candidate surface | Current lines / count | Feasibility | Compatibility strategy | Re-export strategy | Caller/test evidence required | Future staging posture | Runtime path touched |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `run_*` smoke/probe/release-gate exports | 213 exports, service region `5844-7809` | safe later if facade-only and re-exported | Create a smoke/governance facade module that owns wrapper bodies or delegates back during transition; preserve exact function names and signatures. | Keep `service.py` import/re-export wrappers until all external scripts/docs/tests move. | Full `run_*` caller scan, release-gate tests, smoke/probe compatibility tests, `phase8_hardening_support.py` callback proof. | New facade full-file plus hunk-aware `service.py`; existing tests hunk-aware if touched. | mostly smoke/governance only; some wrappers call active runtime through `handle_qwen_user_message` |
| Governance/test helper exports | 55 exports including bounded release gates | safe later, but only after caller proof | Split governance/release-gate helpers into a dedicated compatibility facade; do not remove service re-exports in first implementation. | `service.py` continues to expose same names. | Contract tests for release-gate names, grep/AST caller inventory, QA approval for any moved evidence helpers. | New facade full-file plus hunk-aware `service.py`. | governance/test path, not normal user runtime |
| `summarize_compiled_first_turn_audits` | `5852-5861` | safe later with re-export | Move to governance facade only if tests prove identical return shape. | Re-export from `service.py` under the same name. | Focused audit-summary tests and release-gate wrapper tests. | New facade full-file plus hunk-aware `service.py`. | governance/test helper only |
| `QWEN_SESSION_DOCTYPE` | constant line `647` | not now for movement; stable API constant | Keep in `service.py` or re-export from any future public service facade. | Existing `api.py` import path must remain valid. | API import test and session CRUD tests. | Hunk-aware only if changed. | API/session dependency, not answer runtime |
| `handle_qwen_user_message` | `3776-5841` | not now | No extraction in EC-8; containment map only. | Keep exact service import path for `api.py`. | Full runtime, authority, metadata, live trace readiness, and Frappe API proof would be needed before any movement. | Hunk-aware only; no full-file staging. | active runtime path |
| `phase8_hardening_support.py` callback/injection behavior | 17 text references | risky unless preserved exactly | Any facade must continue accepting/injecting `handle_qwen_user_message` callback without changing invocation semantics. | No direct service import replacement needed now. | Phase8 hardening/recovery smoke evidence and callback contract tests. | Hunk-aware only if touched. | smoke/probe support that exercises runtime |
| Session/message-history wrapper cluster | private helpers lines `1041-1108`, plus trace/snapshot helpers | risky / not now | Future extraction would need a message/session adapter that preserves append/save ordering, payload shape, final-answer authority boundaries, and trace ordering. | Keep private helpers in `service.py` for now; no public re-export. | Final-answer authority tests, raw append scan, metadata/probe tests, session history regression tests, no-leak tests. | Hunk-aware `service.py`; new helper full-file only after approved. | active runtime path |
| `VISIBLE_ROLES` | constant line `648` | safe to leave; no extraction pressure | Treat as internal helper constant unless future caller evidence appears. | No public re-export requirement found. | Caller scan if touched. | Hunk-aware only if changed. | internal helper |

## Session / Message-History Wrapper Candidate Detail

These helpers are extraction candidates only in the architectural sense. EC-8-C recommends no implementation yet because they sit on the active runtime path and control message ordering, tool payload visibility, and save timing.

| Helper | Lines | Internal caller count | Feasibility | Reason |
| --- | ---: | ---: | --- | --- |
| `_append_message` | 1041-1042 | 5 | risky / not now | Append/save/tool-payload helper used by active runtime or service authority helpers; extraction could affect emission order or authority evidence. |
| `_append_tool_payload` | 1045-1046 | 5 | risky / not now | Append/save/tool-payload helper used by active runtime or service authority helpers; extraction could affect emission order or authority evidence. |
| `_append_tool_payload_values` | 1049-1054 | 6 | risky / not now | Append/save/tool-payload helper used by active runtime or service authority helpers; extraction could affect emission order or authority evidence. |
| `_service_tool_payload_values` | 1057-1072 | 1 | risky / not now | Append/save/tool-payload helper used by active runtime or service authority helpers; extraction could affect emission order or authority evidence. |
| `_save_session` | 1079-1080 | 9 | risky / not now | Append/save/tool-payload helper used by active runtime or service authority helpers; extraction could affect emission order or authority evidence. |
| `_assistant_text_payload` | 1083-1084 | 0 | safe to review later | No direct internal callers found in this scan; verify dead-code status before removal or movement. |
| `_visible_message_text` | 1087-1088 | 0 | safe to review later | No direct internal callers found in this scan; verify dead-code status before removal or movement. |
| `_parse_payload` | 1091-1092 | 0 | safe to review later | No direct internal callers found in this scan; verify dead-code status before removal or movement. |
| `_recent_messages` | 1099-1100 | 5 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |
| `_latest_assistant_payload` | 1103-1104 | 10 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |
| `_session_tool_payloads` | 1107-1108 | 4 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |
| `_latest_qwen_trace_payload` | 3029-3030 | 1 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |
| `_build_conversation_state_snapshot` | 3104-3109 | 1 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |
| `_recent_messages_for_grounded_source` | 3123-3134 | 1 | risky / not now | Session/history/trace helper participates in active runtime or smoke/runtime assertions; requires focused regression proof before movement. |

## Required Compatibility Rules For Any Future Implementation

- `handle_qwen_user_message` stays in `service.py` and keeps the existing `api.py` import path.
- `QWEN_SESSION_DOCTYPE` remains stable for `api.py` session CRUD and send paths.
- `service.py` must continue re-exporting moved smoke/governance names during any first extraction slice.
- `phase8_hardening_support.py` callback/injection behavior must continue to work without changing callback semantics.
- No future extraction may modify final-answer authority, authorized emission, runtime metadata, routing, answer text, model behavior, or report selection as a side effect.
- `service.py` should never be whole-file staged for these changes; future implementation must be hunk-aware.

## Recommended Future Sequence

1. EC-8-D: smoke/governance facade design with exact file names, re-export pattern, and test list; report-only.
2. EC-8-E: optional first low-risk facade implementation for a tiny subset of `run_*` wrappers only, if Counterpart/QA approve; hunk-aware `service.py` only.
3. EC-8-F: post-implementation compatibility audit proving no public names disappeared and `api.py`/phase8 callback behavior still works.
4. Defer session/message-history helper extraction until after smoke/governance facade work proves the compatibility pattern.

## Non-Goals

- No helper extraction in EC-8-C.
- No import movement in EC-8-C.
- No `service.py` runtime containment implementation in EC-8-C.
- No strict enforcement, live trace collection, deployment, staging, commit, or push.

## Verification Summary

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| `service.py` compile | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Scoped AI diff check | PASS (`git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`) |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries |
| Staged files | PASS: `0` |

No runtime/source behavior changes were made for EC-8-C. The only new file from this slice is this governance report.

## EC-8-C Decision

`ec_8_c_compatibility_facade_extraction_feasibility_plan_ready_for_counterpart_qa_review`

## What Is Next

If Counterpart/QA accept EC-8-C, the next slice should be EC-8-D smoke/governance facade design only. Do not implement extraction until that design is accepted.
