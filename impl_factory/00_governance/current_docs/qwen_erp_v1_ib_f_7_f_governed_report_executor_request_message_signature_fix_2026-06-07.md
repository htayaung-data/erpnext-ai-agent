# V1-IB-F-7-F Governed Report Executor Request Message Signature Fix

Decision target: v1_ib_f_7_f_governed_report_executor_request_message_signature_fix_ready_for_qa_review

## Scope And Boundary

F-7-F is a narrow source/test/report fix for the F-7-E live development UI crash:

```text
TypeError: execute_governed_report() got an unexpected keyword argument 'request_message'
```

This slice does not merge PR #10, does not deploy to production, does not package build, does not enable strict enforcement, does not claim package readiness, release readiness, enterprise/product closure, or V2, and does not perform destructive ERP actions.

## Root Cause

The compiled fresh-query runtime path passed `request_message=message` into `execute_governed_report(...)` from `fresh_query_interpreter.py`. Other runtime paths also already pass request-message metadata into the governed report executor.

The governed report executor signature did not accept the keyword, so the deployed development UI send path crashed before it could persist a safe synthetic send response.

## Files Changed

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_browser_send_persistence_snapshot_defaults.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_f_7_f_governed_report_executor_request_message_signature_fix_2026-06-07.md`

## Fix Summary

`execute_governed_report(...)` now accepts optional `request_message: str | None = None` for compatibility with compiled-query and browser-send call paths.

The new argument is compatibility metadata only:

- It is not used as report-routing authority.
- It is not used to authorize context reuse, model reasoning, governed ERP answer mode, or final emission.
- It is not exposed through governed report tool trace detail metadata.
- It does not change report execution filters, report name, user, mode, target limit, retry behavior, validation metadata, or fail-closed posture.

A focused regression test proves the executor accepts `request_message` and does not leak the raw prompt or a `request_message` field into the executor tool trace.

## Authority Model Preservation

The fix preserves the accepted V1-IB authority model:

- IntentBoundaryContract remains the sole route authority.
- Validator-owned evidence remains required for safe report routing.
- Missing, stale, malformed, unsafe, mixed, ambiguous, non-redaction-safe, or unproven authority remains fail-closed.
- Proposer/classifier output remains evidence-only.
- Semantic-safe output cannot authorize routing.
- Lexical, keyword, regex, synonym, punctuation, and no-alarm logic cannot authorize routing.
- Final-answer authority alone cannot bypass V1-IB.

## Verification Results

| Check | Result |
| --- | --- |
| Focused F-7-A/F-7-F browser send persistence tests | PASS, 4 tests |
| F-7-A/F-7-F plus E-28-F runtime evidence provider tests | PASS, 13 tests |
| C-3 service adversarial group | PASS, 30 tests |
| D authority/trace/legacy group | PASS, 18 tests |
| Accepted baseline group | PASS, 157 tests |
| Python compile for touched V1-IB source/test files | PASS |
| Package-exclusion gates | PASS |
| Runtime rejected structural classifier refs | PASS, `[]` |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | PASS, `0 / 1 / 27` |
| Raw append scan | PASS, only `authorized_emission.py:271` and `authorized_emission.py:327` |
| `git diff --check` | PASS |
| `git diff --cached --check` before staging | PASS |

## Live Development Validation

A validation-only copy of the fixed executor file was applied to the approved development/synthetic-data backend container for bounded safe-send validation.

Environment:

- URL: `https://meet.erpbosai.com/desk/qwen-chat`
- Development container: `erpai_project1-backend-1`
- Deployed target file: `/home/frappe/frappe-bench/apps/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py`

File copy evidence:

| Item | Value |
| --- | --- |
| Source fixed executor SHA-256 | `20b21e1a488cef3409174cb759792ef6ddca02475187610c9ab245924ee8234e` |
| Container executor SHA-256 before copy | `310a199f7879bceeacea08e99489a9ac9511f0f4c1c75752dde7d151004ab215` |
| Container executor SHA-256 after copy | `20b21e1a488cef3409174cb759792ef6ddca02475187610c9ab245924ee8234e` |
| Reload method | backend container restart only |
| Backend status after restart | healthy |

Bounded safe-send validation:

- Synthetic prompt: `Show EC7H-ITEM-A item sales`
- Session: `lc5mkk29u6`
- Send result: `ok=true`
- Persisted messages: 2
- Roles: `user`, `assistant`
- User prompt persisted: PASS
- Assistant message persisted: PASS
- Error-like message detected: NO
- Previous crash signature observed: NOT reproduced

No unsafe/mixed browser UAT matrix was run in F-7-F. This slice validated only the blocker-specific safe-send path after the signature fix.

## Remaining Blockers

No blocker remains for the specific `request_message` signature crash.

Carry-forward:

- PR #10 still requires push and QA/Owner review before any merge decision.
- Full browser/UI UAT completion remains separately governed.
- Package build, production deployment, strict enforcement, release readiness, enterprise/product closure, and V2 remain out of scope.

## Explicit Non-Actions

F-7-F did not merge PR #10, did not deploy to production, did not package build, did not enable strict enforcement, did not claim package readiness, release readiness, enterprise/product closure, or V2, did not perform destructive ERP actions, did not expose sensitive data, and did not introduce lexical/keyword/regex/synonym/punctuation/no-alarm route authority.
