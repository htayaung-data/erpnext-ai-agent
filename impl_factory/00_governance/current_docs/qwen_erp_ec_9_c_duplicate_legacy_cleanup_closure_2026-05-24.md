# EC-9-C Duplicate / Legacy Cleanup Closure

Decision target: `ec_9_c_duplicate_legacy_cleanup_closed_no_implementation_required`

## Scope

This is a report-only closure artifact. No file deletion, import movement, runtime change, final-answer authority change, metadata change, deployment, staging, commit, or push is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Branch: `main`
- HEAD: `46ed5ef` (`46ed5ef9aef28da443e16811280ddabbc8714152`)

## Accepted EC-9 Inputs

- EC-9-A duplicate/legacy cleanup baseline accepted.
- EC-9-B compatibility retirement/deletion feasibility plan accepted.
- Owner decision: close EC-9 with no cleanup implementation for V1.

## Closure Findings

| Item | Final EC-9 classification | Closure decision |
| --- | --- | --- |
| `qwen_chat/frontdoor_lane.py` | Compatibility facade | Remains. Not deletion-ready; keep root import compatibility. |
| `qwen_chat/lanes/frontdoor_lane.py` | Active runtime | Remains. Active package frontdoor implementation. |
| `qwen_chat/lanes/legacy_runtime_lane.py` | Active runtime fallback | Remains. Active legacy fallback implementation. |
| Emission mapping modules | Governance/test evidence | Remain. They support release/governance evidence and contract tests. |
| Ignored `__pycache__/` directories | Generated local cache | Not part of EC-9 source cleanup; only future generated-cache cleanup if owner approves. |

## No V1 Cleanup Implementation Required

EC-9 found no source file that is deletion-ready for V1. The root frontdoor file is intentionally a compatibility facade, not an unsafe duplicate. Active runtime lanes and governance mapping modules remain needed. Therefore no deletion, import movement, or source cleanup implementation is required before V1 readiness work.

## Future Retirement Preconditions

Any future retirement of root `qwen_chat/frontdoor_lane.py` requires a separate owner-approved slice that performs an external/operator caller audit first. That future audit must cover package imports, scripts, bench commands, governance docs, generated evidence references, deployment/operator instructions, and test/mapping references. No retirement should proceed without owner and QA approval.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| Python compile for inspected runtime files | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Diff checks | PASS |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries in tracked status |
| Staged files | PASS: `0` |

## EC-9-C Decision

`ec_9_c_duplicate_legacy_cleanup_closed_no_implementation_required`

## What Is Next

After Counterpart/QA accept EC-9-C, proceed to EC-10 V1/V2 docs readiness planning. Do not start V1 release execution, deployment, or feature expansion from EC-9 closure alone.
