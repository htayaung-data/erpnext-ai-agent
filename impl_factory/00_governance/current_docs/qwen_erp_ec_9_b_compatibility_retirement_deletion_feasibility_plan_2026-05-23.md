# EC-9-B Compatibility Retirement / Deletion Feasibility Plan

Decision target: `ec_9_b_compatibility_retirement_deletion_feasibility_plan_ready_for_counterpart_qa_review`

## Scope

This is a report/test-only feasibility plan. No file deletion, import movement, runtime change, final-answer authority change, runtime metadata change, deployment, staging, commit, or push is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Branch: `main`
- HEAD: `46ed5ef` (`46ed5ef9aef28da443e16811280ddabbc8714152`)
- Carry-forward dirty file before EC-9-B: EC-9-A report only.

## Feasibility Conclusion

No compatibility or legacy source file is deletion-ready in EC-9-B. The only plausible retirement candidate is the root `qwen_chat/frontdoor_lane.py` compatibility facade, but it must remain for now because governance/mapping tests still intentionally reference it and external bench/operator imports have not been proven absent.

## Candidate Retirement Matrix

| Candidate | Current classification | Deletion feasibility | Required compatibility strategy before any deletion | Required evidence before implementation |
| --- | --- | --- | --- | --- |
| `qwen_chat/frontdoor_lane.py` | compatibility facade | not now | Keep root import path until all consumers migrate or a replacement deprecation facade strategy is accepted. | AST/text caller scan outside package, bench/operator command scan, mapping/test update plan, frontdoor authorized-emission and mapping tests green, owner/QA approval. |
| `qwen_chat/lanes/frontdoor_lane.py` | active runtime | no | Must remain native active runtime lane. | Not a retirement candidate; `service.py` imports it directly. |
| `qwen_chat/lanes/legacy_runtime_lane.py` | active runtime fallback | no | Must remain native active fallback lane. | Not a retirement candidate; `service.py` imports it directly and EC-7 deterministic/control coverage depends on it. |
| `qwen_chat/frontdoor_emission_mapping.py` | governance/test evidence generator | not now | Keep until generated evidence lifecycle policy says source generator is obsolete. | Governance evidence owner decision, mapping tests replacement/deprecation plan. |
| `qwen_chat/legacy_runtime_emission_mapping.py` | governance/test evidence generator | not now | Keep until generated evidence lifecycle policy says source generator is obsolete. | Governance evidence owner decision, mapping tests replacement/deprecation plan. |
| `qwen_chat/service_smoke_governance_facade.py` | compatibility facade | no | Newly merged EC-8 canary; retain. | Not a cleanup candidate. |
| Ignored `__pycache__/` directories | generated cache | feasible later | Cleanup as ignored generated artifacts only, not source cleanup. | Owner-approved generated-cache cleanup slice; verify no tracked files affected. |

## Root Frontdoor Retirement Preconditions

Before any future slice may propose deleting or replacing root `qwen_chat/frontdoor_lane.py`, it must prove:

- No active runtime imports root `ai_assistant_ui.qwen_chat.frontdoor_lane`; current `service.py` imports package `qwen_chat.lanes.frontdoor_lane`.
- No tests, mapping generators, scripts, governance instructions, bench commands, or operator docs require the root import path, or those references are updated in a separately approved compatibility plan.
- `frontdoor_emission_mapping.py` and related mapping tests are updated or explicitly accept root-facade absence without weakening evidence.
- External import compatibility risk is accepted by owner/QA, or a deprecation window is defined.
- Frontdoor authorized-emission, mapping, dry-run inventory, and raw append scans remain green.

## Evidence From EC-9-B Scan

- Direct runtime service imports use `ai_assistant_ui.qwen_chat.lanes.frontdoor_lane` and `ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane`.
- Root frontdoor references found in source are mapping/test/governance compatibility references, not active `service.py` runtime imports.
- `legacy_runtime_lane.py` is referenced by runtime service import and tests/probes; it remains active fallback infrastructure.
- `frontdoor_emission_mapping.py` and `legacy_runtime_emission_mapping.py` expose report builders/writers used by contract tests and governance evidence; they are not stale duplicate runtime files.
- Ignored `__pycache__` directories exist and can be considered only under a separate generated-cache cleanup approval.

## Future Slice Recommendation

Recommended next EC-9 slice, if needed: EC-9-C external/root frontdoor caller audit. It should scan scripts, docs, bench command references, governance reports, and any deployment/operator paths for `ai_assistant_ui.qwen_chat.frontdoor_lane` before any deletion request. EC-9-C should still be report-only.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries in tracked status |
| Staged files | PASS: `0` |

## EC-9-B Decision

`ec_9_b_compatibility_retirement_deletion_feasibility_plan_ready_for_counterpart_qa_review`

## What Is Next

If EC-9-B is accepted, proceed only to EC-9-C external/root frontdoor caller audit if Counterpart/QA/owner want deletion evidence. Otherwise EC-9 can close with no cleanup implementation.
