# EC-10-E Docs Packaging / Archive Proposal

Decision target: `ec_10_e_docs_packaging_archive_proposal_ready_for_counterpart_qa_review`

## Scope

EC-10-E is a proposal-only slice for packaging EC-9 and EC-10 governance reports. It defines a future include/exclude boundary and a future archive posture, but does not execute any packaging, staging, commit, push, move, archive, deployment, V1 release, live trace collection, strict enforcement, or V2 implementation.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Branch | `main` |
| HEAD | `46ed5ef` |
| EC-9 status | Closed with no cleanup implementation |
| EC-10-A status | Accepted docs readiness baseline |
| EC-10-B status | QA-accepted Doc V1 outline/consolidation plan |
| EC-10-C status | QA-accepted V1 release readiness checklist/evidence matrix |
| EC-10-D status | QA-accepted V2 roadmap stub |
| EC-10-E action | New proposal report only |
| File moves/archive creation | None |
| Staging/commit/push | None |

## Packaging Recommendation

Package EC-9 and EC-10 governance reports as one compact docs/governance package after Counterpart/QA/Owner approval.

Rationale:

- EC-9 and EC-10 are currently untracked report-only outputs.
- They form a coherent docs-readiness closure packet.
- They do not require source/test/generated evidence staging.
- They should be packaged before drafting or moving any future AI Assistant Doc V1 artifact.

## Proposed Future Include Boundary

Future package type: full-file governance reports only.

Expected future include count: `8`

| # | Path | Reason |
| --- | --- | --- |
| 1 | `impl_factory/00_governance/current_docs/qwen_erp_ec_9_a_duplicate_legacy_cleanup_baseline_2026-05-23.md` | Accepted EC-9 duplicate/legacy baseline |
| 2 | `impl_factory/00_governance/current_docs/qwen_erp_ec_9_b_compatibility_retirement_deletion_feasibility_plan_2026-05-23.md` | Accepted EC-9 retirement/deletion feasibility plan |
| 3 | `impl_factory/00_governance/current_docs/qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md` | EC-9 closure; no cleanup implementation required |
| 4 | `impl_factory/00_governance/current_docs/qwen_erp_ec_10_a_v1_v2_docs_readiness_baseline_2026-05-24.md` | Accepted EC-10 docs readiness baseline |
| 5 | `impl_factory/00_governance/current_docs/qwen_erp_ec_10_b_ai_assistant_doc_v1_outline_consolidation_plan_2026-05-24.md` | QA-accepted Doc V1 outline/consolidation plan |
| 6 | `impl_factory/00_governance/current_docs/qwen_erp_ec_10_c_v1_release_readiness_checklist_evidence_matrix_2026-05-24.md` | QA-accepted V1 release readiness checklist/evidence matrix |
| 7 | `impl_factory/00_governance/current_docs/qwen_erp_ec_10_d_v2_mi_filter_complex_question_roadmap_stub_2026-05-24.md` | QA-accepted V2 roadmap stub |
| 8 | `impl_factory/00_governance/current_docs/qwen_erp_ec_10_e_docs_packaging_archive_proposal_2026-05-24.md` | Packaging/archive proposal itself, if accepted |

## Proposed Future Exclude Boundary

The future EC-9/EC-10 docs package should exclude:

| Exclusion | Reason |
| --- | --- |
| Source code files | EC-10 is docs/readiness planning only |
| Test files | No EC-10 test implementation is part of this package |
| Generated evidence files under `current_docs/generated/` | Not part of compact docs package unless separately approved |
| Bundle C JSON or other generated JSON/JSONL/CSV/log artifacts | Not required for EC-9/EC-10 docs package |
| Raw traces or redacted live trace JSON | No live trace collection has occurred; trace artifacts must not enter repo |
| Dataset manifests | No dataset is created or seeded in EC-10 |
| Site configs, secrets, archive content, or environment setup files | No environment setup is approved |
| ERP UI paths | Out of scope |
| Seed/data or dummy data paths | Out of scope |
| Temp/probe/cache paths | Out of scope |
| PrimeAxis owner-decision docs | Out of scope |
| Older EC-4 through EC-8 reports already tracked on `main` | Already present; no restaging needed in this package |
| Future AI Assistant Doc V1 draft | Not created yet; belongs to a later approved EC-10 slice |
| Future archive/move plan outputs | Not created yet; require separate approval |

## Archive Posture

No archive action should occur in EC-10-E.

Recommended posture:

| Document family | Proposed treatment |
| --- | --- |
| Existing EC-4 through EC-8 reports | Stay in `current_docs` for now |
| EC-9 reports | Package as current governance evidence |
| EC-10-A through EC-10-E reports | Package as current governance evidence |
| Future AI Assistant Doc V1 | Create later as a consolidated source-of-truth document after EC-10 outline/checklist acceptance |
| Older/superseded EC reports | Consider archive/index later only after Doc V1 exists and owner approves an archive proposal |

Potential future archive direction, not approved here:

- Keep the detailed EC audit trail accessible.
- Create a consolidated AI Assistant Doc V1 document or folder only after a separate plan.
- Do not move historical EC reports until reviewers agree which reports are current operational governance versus retained audit trail.

## Future Staged-Index Proposal

If Counterpart/QA/Owner later approves packaging execution, use an exact file list, not broad directory staging.

Future staging command shape:

```bash
git add -- \
  impl_factory/00_governance/current_docs/qwen_erp_ec_9_a_duplicate_legacy_cleanup_baseline_2026-05-23.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_9_b_compatibility_retirement_deletion_feasibility_plan_2026-05-23.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_9_c_duplicate_legacy_cleanup_closure_2026-05-24.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_10_a_v1_v2_docs_readiness_baseline_2026-05-24.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_10_b_ai_assistant_doc_v1_outline_consolidation_plan_2026-05-24.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_10_c_v1_release_readiness_checklist_evidence_matrix_2026-05-24.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_10_d_v2_mi_filter_complex_question_roadmap_stub_2026-05-24.md \
  impl_factory/00_governance/current_docs/qwen_erp_ec_10_e_docs_packaging_archive_proposal_2026-05-24.md
```

Future expected staged result:

| Check | Expected |
| --- | --- |
| Staged count | `8` |
| Missing | `[]` |
| Extra | `[]` |
| Hunk-aware files | None |
| Source/test files | None |
| Generated files | None |

## Future Verification Commands

If staging is later approved, run:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --check -- impl_factory/00_governance/current_docs
git diff --cached --name-only | grep -E 'erp_workspace_ui|02_seed_data|dummy_data|tmp/|\.codex_tmp|primeaxis|generated|raw_trace|redacted_trace|site_config|secret|archive|\.json|\.jsonl|\.csv|\.log' || true
python3 scripts/check_qwen_enterprise_guardrails.py
python3 /tmp/ec8b_verify.py
```

Future acceptance should require:

- staged files exactly match the 8-report manifest,
- excluded staged scan returns no output,
- direct assistant inventory remains `0 / 1 / 27`,
- raw append scan remains limited to the two authorized `authorized_emission.py` sinks,
- staged count is exactly `8`,
- no doc moves or archive directory creation occurred.

## Risks

| Risk | Mitigation |
| --- | --- |
| Accidentally staging broad current_docs history | Use exact 8-file manifest only |
| Accidentally treating proposal as archive approval | Explicitly separate packaging from archive execution |
| Accidentally including generated evidence or trace artifacts | Exclude generated/raw/redacted/data/site/archive paths |
| Moving older EC reports too early | Keep EC-4 through EC-8 in current location until Doc V1 exists and archive is separately approved |
| Using EC docs as release approval | Keep V1 release gates pending per EC-10-C |

## Explicit Non-Approvals

EC-10-E does not approve:

- file moves,
- archive directory creation,
- source edits,
- generated evidence inclusion,
- packaging execution,
- staging,
- commit,
- push,
- deployment,
- V1 release execution,
- live trace collection,
- strict enforcement,
- V2 implementation.

## EC-10-E Decision

`ec_10_e_docs_packaging_archive_proposal_ready_for_counterpart_qa_review`
