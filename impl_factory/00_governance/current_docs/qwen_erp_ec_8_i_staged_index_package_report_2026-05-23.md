# EC-8-I Staged-Index Package Report

Decision target: `ec_8_i_staged_index_package_ready_for_counterpart_qa_review`

## Scope

This report records the owner-approved EC-8-I staged-index construction. No commit, push, broad `service.py` staging, additional facade expansion, runtime/authority/metadata change, or deployment occurred.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)

## Staged Package Before Proof-Report Addition

| Check | Result |
| --- | --- |
| Staged count | `10` |
| Manifest reconciliation | `MISSING=[]`, `EXTRA=[]` |
| `service.py` cached diff | approved three-wrapper hunk only, `15` insertions and `3` deletions |
| EC-8-H request report | untracked and unstaged before EC-8-I-A |

## Staged 10-File Manifest

| Path | Staging mode |
| --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | hunk-aware approved wrapper hunk only |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` | full-file |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_smoke_governance_facade.py` | full-file |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_e_tiny_first_facade_implementation_request_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md` | full-file governance |
| `impl_factory/00_governance/current_docs/qwen_erp_ec_8_g_packaging_readiness_baseline_2026-05-23.md` | full-file governance |

## Verification Results

| Check | Result |
| --- | --- |
| `git diff --cached --check` | PASS |
| Scoped diff check | PASS |
| Excluded staged scan | PASS: clean |
| Guardrail | PASS |
| Fake-Frappe service import | PASS |
| Facade import | PASS |
| Facade tests | PASS: 4 passed |
| Python compile | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Formal raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Public service inventory | PASS: baseline/current `215`, missing `[]`, extra `[]` |

## EC-8-I-A Report-Staging Expectation

Owner preference is to stage this EC-8-I proof report plus the EC-8-H staging request report before commit approval. After staging both reports, expected staged count is `12`, with no additional source/test/runtime files.

## EC-8-I Decision

`ec_8_i_staged_index_package_ready_for_counterpart_qa_review`

## What Is Next

Proceed to EC-8-I-A proof report staging only: stage EC-8-H and EC-8-I reports, rerun cached boundary checks, then wait for final owner commit approval.
