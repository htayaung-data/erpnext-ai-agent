# V1-IB-E-7-C Clean-Branch D Legacy Restrict-Only Test Alignment

Decision target: `v1_ib_e_7_c_clean_branch_d_legacy_restrict_only_test_alignment_ready_for_counterpart_review`

## Scope And Boundary

E-7-C is a clean-branch test-alignment slice only. Work was performed only in `/tmp/erpai_v1_ib_package_readiness_clean` on branch `codex/v1-ib-package-readiness`.

No runtime source, package config, existing cleanup files, package output, browser/API UAT, staging, commit, push, deployment, strict enforcement, readiness claim, enterprise closure, or V2 work occurred. The dirty source worktree `/tmp/erpai_pr5_postmerge_verify` was not modified.

## Alignment Performed

Changed file:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_legacy_restrict_only.py`

Added report:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_7_c_clean_branch_d_legacy_restrict_only_test_alignment_2026-06-02.md`

The legacy D restrict-only test `test_rejected_structural_classifier_is_not_runtime_authority_import` previously expected the rejected structural classifier test file to exist. That expectation was valid for dirty historical inventory work, but is wrong on the E clean branch where rejected structural artifacts must be absent from the package-readiness tree.

The test now asserts the clean-branch authority model:

- Rejected structural classifier source is absent.
- Rejected structural classifier test is absent.
- Runtime files do not import or reference `intent_boundary_structural_classifier`.
- Accepted `intent_boundary_proposal_classifier.py` remains present as the current evidence-only proposal classifier.
- Old `test_user_intent_boundary_*.py` lexical tests are absent.
- Legacy `user_intent_boundary.py` style allow metadata cannot override a blocking V1-IB contract.
- The rejected structural classifier and old lexical tests are not required for accepted clean-branch tests.

No compatibility mode or keyword/regex/synonym/punctuation/no-alarm authority was added.

## Clean Branch Package-Exclusion Evidence

| Gate | Result |
| --- | --- |
| Root file `=` absent | PASS |
| `intent_boundary_structural_classifier.py` absent | PASS |
| `test_v1_ib_structural_classifier.py` absent | PASS |
| Rejected 2026-05-28 structural B reports absent | PASS |
| Old `test_user_intent_boundary_*.py` tests absent | PASS |
| V1-R/Y report count | PASS: 0 |
| Older non-Y V1-R report count | PASS: 0 |
| Unrelated EC-10-G report absent | PASS |
| Runtime references to rejected structural classifier | PASS: no refs |
| Source/test positive lexical authority claims | PASS: 0 |

The conservative all-report authority scan found historical governance lines that restate prohibitions or neutral inventory language. The source/test positive authority-claim scan returned zero hits.

## Test Verification

| Command group | Result |
| --- | --- |
| Focused aligned legacy restrict-only module | PASS: 8 tests |
| D authority/trace/legacy group | PASS: 18 tests |
| Accepted baseline group | PASS: 157 tests |
| C-3 service adversarial group | PASS: 19 tests |
| Focused contract/classifier/runtime/authorized-emission group | PASS: 147 tests |
| Python compile for accepted V1-IB source/test files | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS |

## Inventory And Append Scans

| Scan | Result |
| --- | --- |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Staged files | PASS: 0 |
| Dirty status before report | 120 |
| Dirty status after report | 121 |

## Residual Boundary

E-7-C does not claim package readiness or release readiness. The clean branch remains dirty by design because it contains accepted re-applied V1-IB artifacts and planned exclusions that have not been staged or committed.

No browser/API UAT, packaging, staging, commit, push, deployment, strict enforcement, enterprise/product closure, or V2 work occurred.

## Decision Request

Please review for:

`v1_ib_e_7_c_clean_branch_d_legacy_restrict_only_test_alignment_ready_for_counterpart_review`
