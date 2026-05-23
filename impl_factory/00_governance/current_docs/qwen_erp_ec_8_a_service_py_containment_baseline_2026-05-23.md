# EC-8-A Service.py Containment Baseline

Decision target: `ec_8_a_service_py_containment_baseline_ready_for_counterpart_qa_review`

## Scope

EC-8-A is investigation/report only. It maps `service.py` containment risk and proposes a controlled EC-8 sequence. It does not change runtime code, extract helpers, stage files, commit, push, deploy, collect live traces, enable strict enforcement, or refactor `service.py`.

## Worktree State

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Main HEAD: `bd99c70`
- Merge: PR #5, EC-7H/EC-7I passive readiness package
- Baseline source file: `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `service.py` line count: 7,809
- Top-level function count: 435
- Import block count: 73
- `run_*` exported smoke/probe function count: 213
- Private helper/wrapper function count: 220
- Public function count: 215
- Primary runtime function: `handle_qwen_user_message`, lines 3776-5841
- Smoke/probe/release-gate export region: lines 5844-7809
- Staged files during EC-8-A: 0

## Active Entry Points

| Entry point | File / line | Role | Containment note |
| --- | --- | --- | --- |
| `qwen_chat_send` | `api.py:63-79` | Frappe whitelisted API endpoint; validates session then calls `handle_qwen_user_message` | Active user-facing runtime entry. |
| `handle_qwen_user_message` | `service.py:3776-5841` | Main orchestration path for one assistant turn | High-risk containment center; no broad refactor. |
| `QWEN_SESSION_DOCTYPE` | `service.py:647` | Shared doctype constant imported by `api.py` | Stable public constant. |
| `run_*` service exports | `service.py:5844-7809` | Smoke/probe/regression/release-gate compatibility exports | Not user-facing chat path, but likely public test/governance API. |
| `phase8_hardening_support.py` callers | multiple references | Optional smoke/recovery support calls `handle_qwen_user_message` | Evaluation/support dependency; not primary API. |

`service.py` has no direct `@frappe.whitelist` decorators. The active whitelisted boundary is in `api.py`.

## Import / Dependency Surface

`service.py` currently imports or lazy-loads a wide dependency surface:

| Category | Import blocks | Notes |
| --- | ---: | --- |
| stdlib / Frappe | 7 | `datetime`, `importlib`, `json`, `re`, `time`, `uuid`, `frappe`. |
| typing / future | 2 | Type and future annotations. |
| `qwen_chat.context` | 3 | Session append/save, message history, grounded context. |
| `qwen_chat.lanes` | 9 | Clarification, artifact boundary, frontdoor, compiled query, entity drilldown, legacy runtime, reasoning, repair, runtime gate. |
| `qwen_chat.helpers` | 52 | Boundary, authority, metadata, NBU, visible context, reasoning, runtime, formatting, restore/control/requery support. |

Important containment observation: EC-7B0 import-integrity work already restored/lazy-deferred enough dependencies for `service.py` to import under Fake-Frappe. EC-8 should preserve that property and avoid reintroducing eager imports for smoke/probe-only modules.

## Responsibility Map

| Service region | Lines | Responsibility | Risk |
| --- | ---: | --- | --- |
| Lazy symbol helper and imports | 15-646 | Import active runtime dependencies and lazy-defer optional audit/evaluation/probe dependencies | Medium; import order and lazy/deferred split are part of EC-7B0 integrity. |
| Fresh-query / context-isolation predicates | 651-986 | Thin orchestration predicates for self-contained query detection, frontdoor yielding, artifact/current evidence precedence | Medium; many behavior-sensitive predicates. |
| Compiled and session wrappers | 989-1137 | Compatibility wrappers around compiled support and session/message-history helpers | Low-to-medium; mostly delegation but public tests may depend on names. |
| Grounded context / recent focus / recovery builders | 1140-1413 | Build contextual runtime messages, recovery query messages, evidence payloads | Medium; affects report/query behavior. |
| Clarification/control/restore/compound helpers | 1416-2977 | Conversation control ownership, restore semantics, active sequence and compound request handling | High; complex ordering and user-visible control paths. |
| Artifact/evidence/requery/observability helpers | 2980-3288 | Artifact evidence boundaries, recovery observability, knowledge boundary payloads | Medium-to-high; overlaps final-answer authority and evidence leakage controls. |
| Service policy/control authorized emission helpers | 3291-3411 | EC-4/EC-7 accepted policy/control metadata + authorized emission wrappers | High; do not alter outside narrow tests. |
| Boundary/local/entity helper wrappers | 3414-3773 | Delegate to artifact observability, local follow-up transform, entity follow-up | Medium; active final-answer paths. |
| `handle_qwen_user_message` | 3776-5841 | Main turn orchestration: contracts, NBU shadow, visible-context trace, control restore, frontdoor, NBU activation, compiled query, recovery, clarification, reasoning, artifact boundary, local transform, runtime gate, legacy runtime | Highest; no broad extraction. |
| Smoke/probe/release-gate exports | 5844-7809 | Public compatibility functions delegating to lazy smoke/probe/evaluation helpers and bounded release gates | Medium; non-chat runtime, but likely governance-call stable. |

## Main Runtime Order Snapshot

The main `handle_qwen_user_message` function performs, in broad order:

1. Load session/site/request context and conversation state snapshot.
2. Build interaction and conversation-control evidence contracts.
3. Apply prior-branch restore message override if applicable.
4. Build NBU always-on shadow trace.
5. Try visible-context trace inspection before ordinary runtime handling.
6. Handle compound completion/stop/continuation control.
7. Build provisional response-policy and frontdoor context.
8. Handle pending clarification and control/restore precedence.
9. Evaluate pre-frontdoor reasoning activation and semantic follow-up context isolation.
10. Try prior-branch direct route, NBU governed requery, compiled fresh query, recovery, NBU presentation, and frontdoor handling.
11. Handle pending clarification, visible-context follow-up, reasoning, entity drilldown, and local follow-up transforms.
12. Evaluate policy boundaries, artifact boundary, runtime gate, then legacy runtime fallback.

Containment implication: the function is effectively a lane scheduler. EC-8 should not split this function by moving arbitrary branches until branch-specific ownership and regression tests are proven.

## Final-Answer / Authority Surface

Current accepted authority points inside `service.py`:

- `_service_policy_boundary_metadata_envelope`, lines 3291-3305.
- `_service_control_metadata_envelope`, lines 3309-3324.
- `_emit_service_policy_boundary_answer`, lines 3327-3376.
- `_emit_service_control_answer`, lines 3379-3411.

These helpers emit through `emit_authorized_assistant_answer`, stage metadata/control/boundary payloads before assistant output, and should be treated as high-risk accepted infrastructure. No EC-8 extraction should modify their behavior unless a dedicated authority test gate is part of the slice.

## Duplicate / Legacy Notes For EC-9

- Active frontdoor import is `ai_assistant_ui.qwen_chat.lanes.frontdoor_lane` at `service.py:281-284`; no service import of the historical root duplicate frontdoor lane was found.
- `legacy_runtime_lane` remains an active runtime fallback import at `service.py:287` and final fallback call at the end of `handle_qwen_user_message`; it is not merely stale duplicate code.
- `run_*` smoke/probe functions in `service.py` are legacy-compatible exports, but many are likely still used by governance and release gates. Treat them as compatibility exports until an import/caller audit proves otherwise.

## Low-Risk Extraction Candidates

These are candidates only; EC-8-A does not approve implementation.

| Candidate | Lines | Why it is plausible | Required guard before implementation |
| --- | ---: | --- | --- |
| Smoke/probe export facade module | 5844-7809 | Mostly thin public wrappers over lazy helpers; not the active chat path | Import/caller audit proving external dotted paths; preserve service re-exports or provide compatibility facade. |
| Session/message-history wrapper cleanup | 1033-1112 | Thin wrappers delegate to context modules | Contract tests proving service-level wrapper names remain stable; no raw `_append_message` hard-gating. |
| Service predicate grouping | 651-986 | Helper predicates are independent from direct session mutation | Branch-specific tests for fresh query, frontdoor yield, artifact precedence, and runtime gate ordering. |

## High-Risk Areas Not To Touch Yet

- `handle_qwen_user_message` branch order, especially lines 3776-5841.
- Service policy/control authorized emission helpers, lines 3291-3411.
- Prior-branch restore, pending clarification, compound request, and active sequence logic.
- Runtime gate and legacy runtime fallback handoff.
- NBU governed requery/presentation activation and visible-context preemption order.
- Any import/lazy-deferred boundary introduced by EC-7B0.
- Any final-answer authority or runtime metadata behavior accepted in EC-4/EC-7.

## EC-8-B Recommendation

Recommended next slice: `EC-8-B service.py public surface / caller audit`.

Scope should remain report-only or test-only:

- Build a deterministic inventory of public service symbols used outside `service.py`.
- Classify public functions into active runtime, test/governance export, smoke/probe facade, compatibility wrapper, and unknown.
- Identify which `run_*` exports are actually imported or invoked by tests/governance.
- Decide whether a smoke/probe facade extraction is safe later.

Do not start helper extraction until EC-8-B proves public symbol ownership.

## Verification

EC-8-A verification reproduced:

- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Formal raw append scan:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- Staged files: `0`
- Excluded status scan: clean

## Final Decision

`ec_8_a_service_py_containment_baseline_ready_for_counterpart_qa_review`

## Next Step

Send EC-8-A to Counterpart/QA. If accepted, proceed to EC-8-B public service surface / caller audit before any extraction or refactor.
