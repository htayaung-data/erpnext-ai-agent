# EC-8-E Tiny First-Facade Implementation Approval Request

Decision target: `ec_8_e_tiny_first_facade_implementation_request_ready_for_counterpart_qa_review`

## Scope

This is an approval request / implementation plan only. It does not create a facade module, edit `service.py`, extract helpers, move imports, change routing, change answer text, touch final-answer authority, enable strict enforcement, deploy, stage, commit, or push.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)

## Proposed Tiny First Slice

| Item | Proposal |
| --- | --- |
| New future module path | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` |
| First slice size | 3 public wrappers only |
| Service hunk scope | Wrapper bodies only, plus any minimal local-import/delegation hunk required for those three wrappers |
| Implementation posture | Additive facade plus `service.py` compatibility wrappers; no public import path removal |
| Runtime posture | No active runtime branch movement; no `handle_qwen_user_message` movement |
| Authority posture | No final-answer authority, authorized emission, or runtime metadata behavior changes |

## Exact Proposed Function Subset

| Function | Current lines | Current delegate | Classification | Why low-risk |
| --- | ---: | --- | --- | --- |
| `run_phase4_compiled_rollout_smoke` | 5844-5845 | `_run_phase4_compiled_rollout_smoke_helper()` | smoke/probe compatibility export | One-line no-argument wrapper; smoke/governance path; delegates to `service_diagnostics`; does not own routing, answer text, final-answer authority, or metadata behavior. |
| `run_phase4_compiled_rollout_governance_selftests` | 5848-5849 | `_run_phase4_compiled_rollout_governance_selftests_helper()` | governance/test export | One-line no-argument wrapper; smoke/governance path; delegates to `service_diagnostics`; does not own routing, answer text, final-answer authority, or metadata behavior. |
| `run_phase4_compiled_rollout_monitoring_smoke` | 5864-5865 | `_run_phase4_compiled_rollout_monitoring_smoke_helper()` | smoke/probe compatibility export | One-line no-argument wrapper; smoke/governance path; delegates to `service_diagnostics`; does not own routing, answer text, final-answer authority, or metadata behavior. |

## Explicit Non-Inclusions

- `handle_qwen_user_message` stays native in `service.py`.
- `QWEN_SESSION_DOCTYPE` stays stable in `service.py`.
- Session/message-history wrappers stay in `service.py`.
- Service policy/control authorized emission helpers stay in `service.py`.
- Local follow-up, entity follow-up, reasoning, NBU, runtime gate, artifact boundary, final-answer authority, and runtime metadata logic are not included.
- No broad `run_*` mass migration is included.

## Future Facade Implementation Pattern

If this request is approved later, the implementation should use this compatibility pattern:

```python
# service_smoke_governance_facade.py
import importlib
from typing import Any, Dict

def _lazy_symbol(module_name: str, symbol_name: str):
    def _call(*args, **kwargs):
        module = importlib.import_module(module_name)
        return getattr(module, symbol_name)(*args, **kwargs)
    return _call

_run_phase4_compiled_rollout_smoke_helper = _lazy_symbol(
    "ai_assistant_ui.qwen_chat.probes.service_diagnostics",
    "run_phase4_compiled_rollout_smoke",
)

def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
    return _run_phase4_compiled_rollout_smoke_helper()
```

`service.py` should keep the existing public names as compatibility wrappers. A local import inside each wrapper is preferred for the tiny first slice because it avoids broad top-level import churn:

```python
def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
    from ai_assistant_ui.qwen_chat.service_smoke_governance_facade import (
        run_phase4_compiled_rollout_smoke as _facade_run_phase4_compiled_rollout_smoke,
    )
    return _facade_run_phase4_compiled_rollout_smoke()
```

This pattern preserves `from ai_assistant_ui.qwen_chat.service import run_phase4_compiled_rollout_smoke` and allows direct future facade imports without requiring any caller migration in the first implementation.

## Compatibility Tests To Add In Future Implementation Slice

| Test | Required assertion |
| --- | --- |
| `test_service_smoke_governance_facade_imports_selected_wrappers` | New facade imports successfully and exposes the three selected functions. |
| `test_service_reexports_selected_facade_wrappers` | Existing imports from `ai_assistant_ui.qwen_chat.service` still expose the same three names. |
| `test_selected_facade_wrappers_delegate_without_payload_change` | With `service_diagnostics` helpers mocked/sentinel-returning, facade and service wrappers return identical payloads. |
| `test_public_service_export_inventory_does_not_drop_names` | Public `service.py` export inventory remains at least the EC-8-B baseline; no selected names disappear. |
| `test_phase8_callback_injection_still_accepts_handle` | `phase8_hardening_support.py` callback/injection behavior remains valid and still accepts `handle_qwen_user_message`. |
| `test_fake_frappe_service_import_after_facade` | Fake-Frappe `service.py` import remains green after facade addition. |

## Public Export Inventory Check

Future implementation should generate a deterministic public export inventory before and after the hunk and assert:

- `handle_qwen_user_message` exists and has not moved.
- `QWEN_SESSION_DOCTYPE` exists and remains importable from `service.py`.
- The three selected wrappers exist in both `service.py` and `service_smoke_governance_facade.py`.
- No pre-existing public `service.py` function/constant is removed.
- `api.py` import path remains unchanged and valid.

## Future Staged-Index Procedure

If a later implementation slice is explicitly approved, stage only:

1. Full-file new module: `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py`.
2. Hunk-aware `service.py` edits for the three selected wrappers only; never whole-file stage `service.py`.
3. Full-file new focused test module if added, or hunk-aware existing tests if reused.
4. Governance implementation report/proof only if separately requested.

Future staged-index verification should include:

- `git diff --cached --name-only` exactly matches the approved implementation boundary.
- `git diff --cached --check` PASS and scoped AI diff check PASS.
- Guardrail PASS.
- Fake-Frappe service import PASS.
- New facade compatibility tests PASS.
- Direct assistant inventory remains `0 / 1 / 27`.
- Raw assistant append scan remains limited to `authorized_emission.py:271` and `authorized_emission.py:327`.
- Excluded staged scan clean.
- Python compile PASS for touched files.

## Rollback Plan

- Because the first implementation would be additive and only three wrappers, rollback can remove the new facade module and restore the three `service.py` wrapper hunks.
- If any export/import compatibility test fails before commit, stop and unstage/revert only the approved facade file and wrapper hunks; do not touch active runtime logic.
- If a post-merge issue appears, rollback commit should restore the original direct helper delegation for the three wrappers while leaving `handle_qwen_user_message`, `QWEN_SESSION_DOCTYPE`, final-answer authority, and runtime metadata untouched.

## Risk Assessment

| Risk | Assessment | Control |
| --- | --- | --- |
| Import-cycle risk | Low if facade imports no `service.py` symbols and `service.py` uses local wrapper imports. | Test fake-Frappe service import and direct facade import. |
| Behavior drift | Low for selected one-line wrappers, but still test with mocked sentinel helpers. | Return-shape/delegation tests. |
| Public export break | Medium if wrappers are accidentally removed. | Public export inventory test and `service.py` re-export requirement. |
| Runtime/authority drift | Low for selected wrappers, but must be guarded. | Guardrail, direct inventory, raw append scan, no active runtime edits. |

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

No runtime/source behavior changes were made for EC-8-E. The only new file from this slice is this governance report.

## EC-8-E Decision

`ec_8_e_tiny_first_facade_implementation_request_ready_for_counterpart_qa_review`

## What Is Next

If EC-8-E is accepted, the next slice can request owner approval for EC-8-F tiny facade implementation using only the three selected wrappers. No implementation should happen until that approval is explicit.
