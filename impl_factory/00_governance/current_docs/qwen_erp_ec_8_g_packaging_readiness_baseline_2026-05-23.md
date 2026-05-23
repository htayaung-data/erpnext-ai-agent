# EC-8-G Packaging Readiness Baseline

Decision target: `ec_8_g_packaging_readiness_baseline_ready_for_counterpart_qa_review`

## Scope

This is an investigation/report-only EC-8 packaging baseline. No staging, commit, push, additional extraction, broad `run_*` movement, runtime/authority/metadata change, deployment, or optional probes dependency repair is included.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)
- Staged files before/after this baseline: `0`

## Dirty Set Classification

| Git state | Path | Classification | Future packaging posture | Notes |
| --- | --- | --- | --- | --- |
| modified | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | service.py three-wrapper compatibility hunk | hunk-aware only | Bundle candidate; never whole-file stage. |
| untracked | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` | tiny facade source module | full-file candidate | Additive new module for three approved wrappers. |
| untracked | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_smoke_governance_facade.py` | focused facade compatibility tests | full-file candidate | New test module; mocked/sentinel compatibility only. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | EC-8-A governance report | full-file governance candidate | Containment baseline. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | EC-8-B governance report | full-file governance candidate | Public service surface/caller audit. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md` | EC-8-C governance report | full-file governance candidate | Facade feasibility plan. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md` | EC-8-D governance report | full-file governance candidate | Smoke/governance facade design. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_e_tiny_first_facade_implementation_request_2026-05-23.md` | EC-8-E governance report | full-file governance candidate | Tiny implementation approval request. |
| untracked | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md` | EC-8-F governance report | full-file governance candidate | Tiny implementation proof report. |

## Packaging Boundary Summary

| Category | Count | Files | Packaging decision |
| --- | ---: | --- | --- |
| Hunk-aware source | 1 | `service.py` | Include only the three-wrapper compatibility hunk if staging is later approved. No broad `service.py` staging. |
| Full-file source | 1 | `service_smoke_governance_facade.py` | Include as additive facade module candidate. No broader facade expansion. |
| Full-file tests | 1 | `test_service_smoke_governance_facade.py` | Include as focused compatibility test candidate. |
| Full-file governance reports | 7 | EC-8-A through EC-8-G reports | Include as EC-8 audit trail candidates. |
| Generated evidence / JSON | 0 | none | Excluded/not present. |
| Excluded streams | 0 | none | No ERP UI, seed/data, temp/probe/cache, PrimeAxis, raw/redacted traces, site configs, secrets, archive content, or generated scratch files in dirty set. |

## Explicit Constraints For Future Staging

- `service.py` must be hunk-aware only; never whole-file stage it.
- The only acceptable `service.py` hunk is the three-wrapper delegation hunk for the approved canary wrappers.
- `service_smoke_governance_facade.py` and `test_service_smoke_governance_facade.py` are full-file candidates because they are new focused files.
- EC-8 governance reports are full-file governance candidates.
- No broad `run_*` migration is part of this package.
- No additional facade functions are part of this package.
- No optional probes dependency repair is part of this package.

## Optional Probes Dependency Limitation

`ai_assistant_ui.qwen_chat.probes.service_diagnostics` is missing in this worktree. EC-8-G therefore does not claim unmocked execution coverage for the moved smoke wrappers. The accepted EC-8-F compatibility tests prove import compatibility, `service.py` re-export stability, public export inventory stability, and mocked/sentinel delegation equivalence only. Any future claim that the wrappers execute real smoke diagnostics requires a separate dependency decision or test environment where `service_diagnostics` is available.

## Future Staged-Index Procedure

If staging is later approved, use an exact manifest, not broad directory staging:

1. Hunk-stage only the approved `service.py` wrapper hunk.
2. Full-file stage `service_smoke_governance_facade.py`.
3. Full-file stage `test_service_smoke_governance_facade.py`.
4. Full-file stage the approved EC-8 governance reports requested by Counterpart/QA/owner.
5. Run cached checks against the staged index before any commit request.

## Required Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS (`python3 scripts/check_qwen_enterprise_guardrails.py`) |
| Fake-Frappe service import | PASS |
| Facade import | PASS |
| `test_service_smoke_governance_facade` | PASS: 4 tests passed |
| `service.py` compile | PASS |
| Direct assistant inventory | PASS: `active_runtime_direct_assistant_append_count=0`, `inventory_count=1`, `migrated_authorized_paths_length=27` |
| Formal raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Public service inventory | PASS: baseline public function count `215`, current public function count `215`, missing names `[]`, extra names `[]` |
| Diff check | PASS (`git diff --check -- impl_factory/05_custom_logic/custom_app/ai_assistant_ui`) |
| Excluded status scan | PASS: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, or archive-content entries |
| Staged files | PASS: `0` |

## EC-8-G Decision

`ec_8_g_packaging_readiness_baseline_ready_for_counterpart_qa_review`

## What Is Next

If EC-8-G is accepted, the next slice should be EC-8-H exact staged-index construction request for this EC-8 package. Do not stage until that request is accepted and owner approval is explicit.
