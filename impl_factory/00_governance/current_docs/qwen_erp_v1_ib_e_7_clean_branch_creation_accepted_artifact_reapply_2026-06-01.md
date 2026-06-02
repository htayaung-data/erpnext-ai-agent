# V1-IB-E-7 Clean Branch Creation / Accepted Artifact Reapply

Decision target:
`v1_ib_e_7_clean_branch_creation_accepted_artifact_reapply_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-7 is the bounded clean-branch creation and accepted-artifact reapply implementation slice approved after E-6.

Branch created:

```text
codex/v1-ib-package-readiness
```

Clean worktree path:

```text
/tmp/erpai_v1_ib_package_readiness_clean
```

Dirty evidence source worktree:

```text
/tmp/erpai_pr5_postmerge_verify
```

No `git reset --hard`, `git checkout --`, or `git clean` was used. No rejected, historical, unrelated, or unknown artifact was deleted, moved, renamed, archived, truncated, or cleaned from the dirty source worktree.

No files were staged, committed, pushed, packaged, deployed, or used for browser/API UAT. No strict enforcement, package readiness, release readiness, enterprise/product closure, or V2 approval is claimed.

## 2. Pre-Branch State Recorded

Pre-branch source worktree:

| Field | Value |
| --- | --- |
| Source worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Current branch before branch action | `feature/v1-browser-uat-readiness-package` |
| Current HEAD before branch action | `08f0ec202d9ae6af33305b74c8b15e37f617680d` |
| Staged files before branch action | `0` |
| Dirty worktree count before branch action | `160` |
| Target branch existence before action | missing |

The pre-branch `git status --short` was recorded before branch creation. It contained `160` entries:

- `4` modified tracked accepted-current files
- `156` untracked files
- known dirty source evidence included accepted V1-IB files/reports, rejected structural artifacts, historical V1-R reports, old lexical tests, unrelated EC-10-G, and root file `=`

Accepted manifest/report basis:

- D-4-E-1 accepted-evidence manifest
- E-0 through E-6 package-readiness planning reports
- QA/Risk E-6 acceptance:

```text
accept_v1_ib_e_6_clean_branch_implementation_boundary_request_for_future_clean_branch_slice
```

## 3. Branch Action Taken

Branch action:

```bash
git worktree add -b codex/v1-ib-package-readiness /tmp/erpai_v1_ib_package_readiness_clean 08f0ec202d9ae6af33305b74c8b15e37f617680d
```

Result:

```text
Preparing worktree (new branch 'codex/v1-ib-package-readiness')
HEAD is now at 08f0ec2 Add V1 browser UAT readiness package
```

Post-action clean branch:

| Field | Value |
| --- | --- |
| Branch | `codex/v1-ib-package-readiness` |
| HEAD | `08f0ec202d9ae6af33305b74c8b15e37f617680d` |
| Staged files after reapply | `0` |
| Worktree status count after accepted reapply, before E-7 report | `103` |

## 4. Accepted Artifacts Reapplied

Accepted artifact reapply was performed using an explicit allowlist from the dirty evidence source worktree to the clean branch worktree.

Reapply result:

| Metric | Result |
| --- | ---: |
| Accepted artifacts copied | `103` |
| Missing accepted artifacts | `0` |
| Accepted source/test files copied | `25` |
| Accepted governance reports copied | `78` |

Accepted source/runtime categories reapplied:

- `service.py`
- `authorized_emission.py`
- `intent_boundary_contract.py`
- `intent_boundary_runtime_integration.py`
- `intent_boundary_proposal_classifier.py`
- `user_intent_boundary.py` as legacy restrict-only/fail-closed dependency only

Accepted test categories reapplied:

- contract validator tests
- proposal classifier tests
- runtime integration tests
- final-emission veto tests
- runtime adversarial pre-routing/final-emission tests
- C-3 service adversarial tests
- D authority consistency tests
- D trace/diagnostic tests
- D legacy restrict-only tests
- authorized-emission alignment tests

Accepted governance reports reapplied:

- V1-IB architecture reports
- accepted V1-IB-A reports
- accepted V1-IB-B proposal-classifier reports, excluding rejected structural reports
- accepted V1-IB-C reports
- accepted V1-IB-D reports
- accepted V1-IB-E reports through E-6

E-7 report was then added to the clean branch worktree as the implementation evidence report.

## 5. Excluded Artifact Scan Results

Package-exclusion scan results after accepted reapply:

| Exclusion item | Result |
| --- | --- |
| Root file `=` | PASS: absent from clean branch |
| Rejected `intent_boundary_structural_classifier.py` | PASS: absent from clean branch |
| Rejected `test_v1_ib_structural_classifier.py` | PASS: absent from clean branch |
| Rejected 2026-05-28 structural B reports | PASS: absent from clean branch |
| Unrelated EC-10-G report | PASS: absent from clean branch |
| Old direct `test_user_intent_boundary_*.py` lexical tests | PASS: absent from clean branch |
| Runtime references to rejected structural classifier | PASS: none found outside the rejected file itself |
| V1-R/Y reports | PASS: `0` present |
| Older non-Y V1-R reports | FAIL: `14` present |

## 6. Stop-Condition Blocker

E-7 stop condition triggered.

The clean branch inherited `14` older non-Y V1-R reports from base HEAD. These reports are present in the current governance evidence path of the clean branch:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_a_human_like_browser_uat_question_bank_automation_plan_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_b_browser_uat_automation_harness_plan_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_c_controlled_browser_uat_execution_request_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_d_browser_uat_execution_input_preflight_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_e_synthetic_dataset_environment_input_plan_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_f_synthetic_dataset_manifest_template_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_g_synthetic_dataset_manifest_creation_approval_request_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_h_synthetic_manifest_validator_plan_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_a_synthetic_manifest_validator_hardening_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_b_synthetic_manifest_validator_hardening_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_i_synthetic_manifest_validator_implementation_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_j_synthetic_manifest_creation_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_k_browser_uat_environment_readiness_recheck_2026-05-24.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_r_p_packaging_readiness_baseline_2026-05-24.md`

Why this is a blocker:

- E-6 required all older non-Y V1-R reports to be excluded from current evidence.
- E-7 explicitly required stopping if old V1-R reports appear as current evidence.
- These files were not copied from the dirty source allowlist; they were inherited from the base HEAD used to create the clean branch.

No deletion or cleanup was performed in E-7. Fixing this requires a separate QA-approved follow-up slice.

Recommended next slice:

```text
V1-IB-E-7-A base-branch historical V1-R report exclusion fix
```

The follow-up should explicitly approve either:

- removing the inherited old V1-R reports from the clean branch current evidence path, or
- moving them to a QA-approved package-excluded/historical archive location with manifest labels.

## 7. Verification Status

Because the stop condition triggered, full post-reapply validation was not completed. In particular, accepted baseline tests, C-3 service tests, full V1-IB A/B/C/D tests, and full compile were not run after the blocker was found.

Read-only verification completed:

| Check | Result |
| --- | --- |
| Branch created | PASS: `codex/v1-ib-package-readiness` |
| Clean worktree path | PASS: `/tmp/erpai_v1_ib_package_readiness_clean` |
| Accepted artifact reapply count | PASS: `103` |
| Missing accepted artifacts | PASS: `0` |
| E-7 report present | PASS |
| E-7 report hygiene | PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Staged files | PASS: `0` |
| Clean branch dirty status count after E-7 report | `104` |
| Root file `=` absent | PASS |
| Rejected structural classifier source absent | PASS |
| Rejected structural classifier test absent | PASS |
| Rejected structural B reports absent | PASS |
| Old direct lexical tests absent | PASS |
| Unrelated EC-10-G report absent | PASS |
| Runtime rejected structural classifier import scan | PASS |
| V1-R/Y reports absent | PASS: `0` |
| Older non-Y V1-R reports absent | FAIL: `14` present |

## 8. Boundary Statement

No commit, push, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred.

No rejected/historical/unknown artifact was deleted, moved, archived, truncated, or cleaned from the dirty source worktree.

E-7 produced blocker evidence. It does not claim package readiness.
