# EC-8-F Tiny Smoke/Governance Facade Implementation

Decision target: `ec_8_f_tiny_facade_implementation_ready_for_counterpart_qa_review`

## Scope

This slice implements only the owner-approved tiny smoke/governance facade canary. It does not stage, commit, push, deploy, change routing, change answer text, change final-answer authority, change runtime metadata, enable strict enforcement, or touch active runtime branches.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)

## Files Changed

| File | Change type | Scope control |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` | new source module | Full-file additive facade for three approved wrappers only. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | modified source | Hunk-only wrapper delegation for three approved public names; no `handle_qwen_user_message`, constants, authority, metadata, or runtime branch edits. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_smoke_governance_facade.py` | new test module | Focused compatibility tests for facade imports, service wrapper imports, identical sentinel payload delegation, and public export inventory. |

## Approved Wrapper Set

| Wrapper | Current service behavior after EC-8-F | Facade behavior |
| --- | --- | --- |
| `run_phase4_compiled_rollout_smoke` | Stable `service.py` public wrapper remains; delegates to facade with a local import. | Delegates lazily to `service_diagnostics.run_phase4_compiled_rollout_smoke`. |
| `run_phase4_compiled_rollout_governance_selftests` | Stable `service.py` public wrapper remains; delegates to facade with a local import. | Delegates lazily to `service_diagnostics.run_phase4_compiled_rollout_governance_selftests`. |
| `run_phase4_compiled_rollout_monitoring_smoke` | Stable `service.py` public wrapper remains; delegates to facade with a local import. | Delegates lazily to `service_diagnostics.run_phase4_compiled_rollout_monitoring_smoke`. |

## Preserved Boundaries

- `handle_qwen_user_message` was not edited and remains in `service.py`.
- `QWEN_SESSION_DOCTYPE` was not edited and remains stable in `service.py`.
- `api.py` import path remains unchanged.
- `phase8_hardening_support.py` callback/injection behavior was not edited.
- Session/message-history wrappers were not edited.
- Service policy/control authorized emission helpers were not edited.
- Local follow-up, entity follow-up, reasoning, NBU, runtime gate, artifact boundary, final-answer authority, and runtime metadata logic were not edited.
- No broad `run_*` migration occurred.

## Compatibility Evidence

| Evidence | Result |
| --- | --- |
| Existing service imports for selected wrappers | PASS: `from ai_assistant_ui.qwen_chat.service import ...` remains valid through unchanged public names. |
| Direct facade import | PASS: `service_smoke_governance_facade` imports and exposes all three wrappers. |
| Sentinel helper delegation | PASS: facade and service wrappers return identical mocked/sentinel payloads in focused tests. |
| Public service export inventory | PASS: baseline public function count `215`, current public function count `215`, missing names `[]`, extra names `[]`. |
| Fake-Frappe service import | PASS. |

## Test Results

| Command/group | Result |
| --- | --- |
| `python3 -m unittest ai_assistant_ui.tests.test_service_smoke_governance_facade` | PASS: 4 tests passed |
| Python compile for touched files | PASS |

## Required Verification

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| Facade import | PASS |
| New facade compatibility tests | PASS: 4 passed |
| `service.py` compile | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Public export inventory | PASS: unchanged, no names lost |
| Scoped AI diff check | PASS (`git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`) |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries |
| Staged files | PASS: `0` |

## Rollback Notes

Rollback is narrow: remove `service_smoke_governance_facade.py`, remove `test_service_smoke_governance_facade.py`, and restore the three `service.py` wrapper hunks to direct helper calls. No active runtime or authority code would need rollback.

## EC-8-F Decision

`ec_8_f_tiny_facade_implementation_ready_for_counterpart_qa_review`

## What Is Next

If Counterpart/QA accept EC-8-F, the next step should be EC-8-G packaging readiness for EC-8 reports plus the tiny facade implementation. Do not stage or commit until packaging approval is explicit.
