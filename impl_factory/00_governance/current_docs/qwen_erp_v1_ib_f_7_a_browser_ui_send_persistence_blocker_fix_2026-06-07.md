# V1-IB-F-7-A Browser UI Send/Persistence Blocker Fix

Decision target: v1_ib_f_7_a_browser_ui_send_persistence_blocker_fix_ready_for_qa_review

## Scope And Boundary

F-7-A reproduced and fixed the P0 browser/UI send persistence blocker from F-7. This slice was limited to the send/persistence path. It did not resume unsafe/mixed browser UAT beyond the safe-lane validation required to prove the blocker was closed.

No production deployment, package build, migration, strict-enforcement change, readiness/release claim, enterprise/product closure, V2 work, destructive ERP action, authentication bypass, or sensitive-data capture occurred.

## Reproduction Evidence

Initial browser/UI behavior on the dev/synthetic environment:

- URL: `https://meet.erpbosai.com/desk/qwen-chat`
- Authenticated role: `Administrator`; password was not requested, typed by Codex, printed, logged, stored, screenshotted, or reported.
- Fresh chat opened with an empty message pane.
- Safe synthetic prompt entered: `Show EC7H-ITEM-A item sales`
- Before fix: composer cleared after send, but message pane remained empty with `0` persisted user/assistant message nodes.

Redaction-safe backend evidence showed `qwen_chat_send` was reached, but crashed before persistence/response completion.

## Root Cause

Two narrow backend send-path blockers were found in sequence:

1. `service.py` lazy-loaded `ai_assistant_ui.qwen_chat.snapshot_defaults`, but `snapshot_defaults.py` was missing from merged main and from the deployed dev runtime. This caused `ModuleNotFoundError` during conversation snapshot construction.
2. After restoring the missing helper, the send path advanced to compiled query routing and failed with `TypeError: execute_compiled_fresh_query_message() got an unexpected keyword argument 'front_door_contract'`. The compiled-query lane passed front-door evidence metadata, but the helper signature did not accept that optional payload.

Neither failure was an intent-boundary policy failure. Both were backend exceptions that prevented UI send persistence.

## Files Changed

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/snapshot_defaults.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_browser_send_persistence_snapshot_defaults.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_f_7_a_browser_ui_send_persistence_blocker_fix_2026-06-07.md`

## Fix Summary

- Restored the missing `snapshot_defaults.py` helper source from the F-6 rollback artifact.
- Added optional `front_door_contract` handling to `compile_from_fresh_query_message` and `execute_compiled_fresh_query_message`.
- Preserved `front_door_contract` only as metadata/evidence in the compiled query pipeline.
- Did not use front-door, semantic, proposer, lexical, keyword, regex, punctuation, synonym, no-alarm, or visible-context evidence as route authority.
- Preserved V1-IB runtime authority, validator-owned evidence provider behavior, fail-closed behavior, and redaction behavior.

## Focused Tests Added

`test_v1_ib_browser_send_persistence_snapshot_defaults.py` proves:

- `snapshot_defaults` exports the lazy helpers used by the service send snapshot path.
- `service.py` lazy snapshot-default helpers resolve and return safe empty/default state.
- compiled-query helper accepts `front_door_contract` metadata without treating it as routing authority.

## Dev Environment Update

The dev/synthetic environment was updated only to validate the UI fix:

- Copied `snapshot_defaults.py` into the dev backend app path.
- Copied `fresh_query_interpreter.py` into the dev backend app path.
- Ran Python compile on both deployed files.
- Reloaded the existing gunicorn master with `HUP`; worker PIDs changed from the prior set to `1423512` and `1423513`.
- No migration, package build, production deployment, or strict-enforcement change occurred.

Rollback reference remains the F-6 rollback artifact:

- `/tmp/v1_ib_f6_ai_assistant_ui_rollback_20260607T034836Z.tar.gz`
- SHA-256: `322c876d9a47c51d11a5df160ad0abf86118b65edd04405d0b2e6ce0dad8e350`

## Browser Safe-Prompt Validation

After the dev update and reload:

- Fresh chat opened.
- Safe synthetic prompt entered: `Show EC7H-ITEM-A item sales`
- Composer cleared after send.
- Message pane persisted `2` message nodes.
- User prompt was visible in the message pane.
- Assistant returned a non-table clarification/control response asking which period to use.
- No selected rows, raw sensitive payloads, rendered report payloads, report artifacts, or secrets were captured in evidence.
- Latest Error Log remained at the pre-fix `front_door_contract` TypeError timestamp; the browser retry did not add a new send crash.

## API/Service Smoke

Redaction-safe API/service smoke on the dev/synthetic environment:

| Case | Expected | Result |
| --- | --- | --- |
| Safe synthetic item sales prompt | safe route or clarification/control under V1-IB authority | PASS; persisted user and assistant messages; boundary/clarification class |
| Supplier aging plus delay payment decision | fail closed | PASS; persisted user and assistant messages; boundary/clarification class, no table-bearing report |
| Sales plus prediction | fail closed | PASS; persisted user and assistant messages; boundary/clarification class, no table-bearing report |

## Verification Results

| Check | Result |
| --- | --- |
| Focused F-7-A regression tests | PASS, `3` passed |
| Focused F-7-A + E-28-F runtime evidence tests | PASS, `12` passed |
| Python compile for touched source/test files | PASS |
| C-3 service/runtime group | PASS, `30` passed |
| D authority/trace/legacy group | PASS, `18` passed |
| Accepted baseline group | PASS, `157` passed |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS |
| Package-exclusion gates | PASS |
| Runtime rejected structural classifier refs | PASS; no runtime refs |
| Direct assistant inventory | PASS, `0 / 1 / 27` |
| Raw append scan | PASS; only `authorized_emission.py:271` and `authorized_emission.py:327` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |

## Remaining Boundaries

Unsafe/mixed browser UAT remains paused for this slice. F-7-A closes the safe send/persistence blocker and validates API/service unsafe fail-closed smoke only. A separate QA-accepted browser UAT continuation slice is still required before broader UI UAT closure.

The work does not approve package readiness, release readiness, deployment readiness, enterprise/product closure, strict enforcement, or V2.
