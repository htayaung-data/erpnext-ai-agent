# EC-9-A Remaining Duplicate / Legacy Cleanup Baseline

Decision target: `ec_9_a_duplicate_legacy_cleanup_baseline_ready_for_counterpart_qa_review`

## Scope

This is an investigation/report-only baseline. No file deletion, cleanup implementation, import movement, refactor, runtime change, authority change, metadata change, deployment, staging, commit, or push is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Branch: `main`
- HEAD: `46ed5ef` (`46ed5ef9aef28da443e16811280ddabbc8714152`)
- PR #6 post-merge state verified before EC-9-A.

## Baseline Findings

- Root duplicate frontdoor remains resolved as a compatibility facade: `qwen_chat/frontdoor_lane.py` is a thin re-export of `qwen_chat/lanes/frontdoor_lane.py`.
- `qwen_chat/lanes/frontdoor_lane.py` is the active runtime frontdoor implementation and is imported by `service.py`.
- `qwen_chat/lanes/legacy_runtime_lane.py` is an active runtime fallback lane and is imported by `service.py`; it must remain.
- No tracked duplicate filename collision was found under `qwen_chat` in the focused scan.
- Ignored `__pycache__` directories exist from verification runs; they are generated cache cleanup candidates only, not tracked legacy source duplicates.

## Candidate Classification

| Path / pattern | Classification | Rationale |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py` | compatibility facade | Root frontdoor compatibility facade that re-exports `evaluate_frontdoor_lane` and `handle_frontdoor_turn` from `qwen_chat/lanes/frontdoor_lane.py`; must remain until external/root import callers are proven migrated. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py` | active runtime | Active package frontdoor implementation imported by `service.py` and direct frontdoor tests; not a cleanup candidate. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py` | active runtime fallback | Active legacy runtime fallback lane imported by `service.py`; keeps authorized emission and runtime metadata behavior; not a cleanup candidate. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_emission_mapping.py` | test/governance-only | Mapping/evidence generator for frontdoor emission authority; referenced by contract tests and governance evidence; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py` | test/governance-only | Mapping/evidence generator for legacy runtime emission authority; referenced by contract tests and governance evidence; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` | compatibility facade | EC-8 tiny smoke/governance facade canary; active compatibility surface for three service wrappers; not cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiled_support_emission_mapping.py` | test/governance-only | Mapping/evidence generator references frontdoor and legacy lanes for emission coverage; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_lane_emission_mapping.py` | test/governance-only | Mapping/evidence generator references legacy/frontdoor as migrated paths; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py` | test/governance-only | Mapping/evidence generator references root frontdoor compatibility facade in closure inventory; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py` | test/governance-only | Mapping/evidence generator references frontdoor/legacy in migrated-path proof; not runtime cleanup. |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/**/__pycache__/` | stale generated cache | Ignored Python bytecode/cache directories produced by verification; cleanup candidate only after owner-approved generated-cache cleanup slice, not EC-9-A. |

## Files That Must Remain

| File | Must remain because |
| --- | --- |
| `qwen_chat/frontdoor_lane.py` | Compatibility facade for older root imports; final-answer mapping reports and tests still reference the root facade as a compatibility surface. |
| `qwen_chat/lanes/frontdoor_lane.py` | Active runtime lane used by `service.py`; owns frontdoor authorized emission paths. |
| `qwen_chat/lanes/legacy_runtime_lane.py` | Active runtime fallback lane used by `service.py`; owns legacy governed/report, policy-boundary, and error-fallback authorized emission paths. |
| `qwen_chat/service_smoke_governance_facade.py` | Newly merged EC-8 compatibility canary; not stale. |
| Emission mapping modules | Governance/test evidence generators for migrated authority paths; not runtime duplicates. |

## Cleanup Candidates For Later EC-9 Slices

- Ignored `__pycache__/` directories may be cleaned in a future generated-cache cleanup slice if owner approves. They are ignored artifacts, not release source.
- Root `qwen_chat/frontdoor_lane.py` could be reviewed in a future compatibility retirement decision only after external caller evidence proves no root import consumers remain. EC-9-A does not recommend deletion now.
- Mapping/evidence modules may be reviewed only as part of governance evidence lifecycle cleanup, not as duplicate runtime cleanup.

## Unknowns / Further Evidence Needed

- External operator scripts or bench commands outside the Python package may still import `ai_assistant_ui.qwen_chat.frontdoor_lane`; keep the root facade until those callers are scanned.
- Generated/cache cleanup policy should be decided separately before deleting ignored `__pycache__` directories from the working tree.
- Any future compatibility retirement must rerun frontdoor and legacy mapping/authorized-emission tests before proposing deletion.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries in tracked status |
| Staged files | PASS: `0` |

## EC-9-A Decision

`ec_9_a_duplicate_legacy_cleanup_baseline_ready_for_counterpart_qa_review`

## What Is Next

If EC-9-A is accepted, the next slice should be EC-9-B compatibility retirement/deletion feasibility plan only. Do not delete files or move imports until that plan is accepted and owner explicitly approves implementation.
