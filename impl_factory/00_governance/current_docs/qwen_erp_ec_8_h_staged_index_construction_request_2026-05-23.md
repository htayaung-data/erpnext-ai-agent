# EC-8-H Exact Staged-Index Construction Request

Decision target: `ec_8_h_staged_index_construction_request_ready_for_counterpart_qa_owner_review`

## Scope

This is a request/report-only staging approval packet. It does not stage, commit, push, broaden `service.py`, expand the facade, change runtime/authority/metadata behavior, or claim unmocked smoke-wrapper execution coverage.

## Branch / Head

- Worktree: `/tmp/erpai_pr5_postmerge_verify`
- Git state: detached post-merge main verification checkout (`HEAD (no branch)`)
- HEAD: `bd99c70` (`bd99c70dac7bf5a83e987cfacd4ddfff8a5c8efd`)
- Current staged files: `0`

## Exact Future Staged Manifest

| # | Path | Staging mode | Classification |
| ---: | --- | --- | --- |
| 1 | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | hunk-aware only | `service.py` three-wrapper facade delegation hunk only |
| 2 | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py` | full-file | additive tiny smoke/governance facade module |
| 3 | `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_smoke_governance_facade.py` | full-file | focused facade compatibility test module |
| 4 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_a_service_py_containment_baseline` |
| 5 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_b_public_service_surface_caller_audit` |
| 6 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_c_compatibility_facade_extraction_feasibility_plan` |
| 7 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_d_smoke_governance_facade_design` |
| 8 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_e_tiny_first_facade_implementation_request_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_e_tiny_first_facade_implementation_request` |
| 9 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_f_tiny_facade_implementation` |
| 10 | `impl_factory/00_governance/current_docs/qwen_erp_ec_8_g_packaging_readiness_baseline_2026-05-23.md` | full-file | EC-8 governance report: `ec_8_g_packaging_readiness_baseline` |

Expected staged path count: `10` total paths.

## Required Future Staging Procedure

If owner/Counterpart/QA approve EC-8 staged-index construction, use an exact manifest and do not broad-stage directories.

1. Hunk-stage only the approved `service.py` wrapper delegation hunk for these three wrappers:
   `run_phase4_compiled_rollout_smoke`, `run_phase4_compiled_rollout_governance_selftests`, `run_phase4_compiled_rollout_monitoring_smoke`.
2. Full-file stage `service_smoke_governance_facade.py`.
3. Full-file stage `test_service_smoke_governance_facade.py`.
4. Full-file stage exactly the seven EC-8 governance reports listed above, including EC-8-G explicitly.
5. Verify staged set exactly matches the manifest: `MISSING=[]`, `EXTRA=[]`.
6. Do not stage this EC-8-H request report unless separately requested after QA review.

## Future Manifest Check Script Shape

A future staged-index check can use this manifest logic after staging approval:

```python
expected = {
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py",
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service_smoke_governance_facade.py",
    "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_smoke_governance_facade.py",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_a_service_py_containment_baseline_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_b_public_service_surface_caller_audit_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_c_compatibility_facade_extraction_feasibility_plan_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_d_smoke_governance_facade_design_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_e_tiny_first_facade_implementation_request_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_f_tiny_facade_implementation_2026-05-23.md",
    "impl_factory/00_governance/current_docs/qwen_erp_ec_8_g_packaging_readiness_baseline_2026-05-23.md",
}
actual = set(run("git diff --cached --name-only"))
print("STAGED_COUNT=", len(actual))
print("MISSING=", sorted(expected - actual))
print("EXTRA=", sorted(actual - expected))
```

Expected after approved staging:

- `STAGED_COUNT=10`
- `MISSING=[]`
- `EXTRA=[]`

## Required Future Cached Checks

| Check | Expected result |
| --- | --- |
| Staged count | `10` |
| Manifest reconciliation | `MISSING=[]`, `EXTRA=[]` |
| `git diff --cached --check` | PASS |
| Excluded staged scan | clean: no ERP UI, seed/data, temp/probe/cache, PrimeAxis, generated scratch, raw/redacted trace, site config, secret, archive-content paths |
| Guardrail | PASS |
| Fake-Frappe service import | PASS |
| Facade import | PASS |
| `test_service_smoke_governance_facade` | PASS |
| Python compile | PASS for touched source/test files |
| Direct assistant inventory | `0 / 1 / 27` |
| Formal raw assistant append scan | only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Public service inventory | unchanged: baseline/current `215`, missing `[]`, extra `[]` |

## Hard Boundaries For Future Staging

- No broad `service.py` staging. `service.py` must be hunk-aware only.
- No broad facade expansion beyond the three approved wrappers.
- No runtime, final-answer authority, runtime metadata, routing, answer-text, deployment, commit, or push work.
- No optional probes dependency repair in this package.
- No claim of unmocked smoke-wrapper execution coverage because `ai_assistant_ui.qwen_chat.probes.service_diagnostics` remains missing/pre-existing.

## Current Report-Only Verification

| Check | Result |
| --- | --- |
| Report created without staging | PASS |
| Current staged files | `0` |
| EC-8-G accepted package boundary preserved | PASS |

## EC-8-H Decision

`ec_8_h_staged_index_construction_request_ready_for_counterpart_qa_owner_review`

## What Is Next

If Counterpart/QA/owner approve EC-8-H, the next slice should be EC-8-I staged-index construction using exactly this manifest. No staging should happen before that explicit approval.
