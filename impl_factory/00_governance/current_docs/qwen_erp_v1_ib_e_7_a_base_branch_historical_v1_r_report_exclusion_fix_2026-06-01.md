# V1-IB-E-7-A Base-Branch Historical V1-R Report Exclusion Fix

Decision target:
`v1_ib_e_7_a_base_branch_historical_v1_r_report_exclusion_fix_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-7-A is a narrow clean-branch package-exclusion fix for the E-7 blocker. It removes only the `14` inherited older non-Y V1-R reports from the clean branch current evidence path.

Allowed worktree used:

```text
/tmp/erpai_v1_ib_package_readiness_clean
```

Dirty source worktree not modified:

```text
/tmp/erpai_pr5_postmerge_verify
```

No new branch was created. No branch was switched. No files were staged, committed, pushed, packaged, deployed, or used for browser/API UAT. No strict enforcement, package readiness, release readiness, enterprise/product closure, or V2 approval is claimed.

## 2. Branch And Source Confirmation

Clean branch state:

| Field | Result |
| --- | --- |
| Branch | `codex/v1-ib-package-readiness` |
| Staged files before fix | `0` |
| Dirty status count before fix | `104` |
| Staged files after fix before report | `0` |
| Dirty status count after fix before report | `118` |

Dirty source worktree confirmation:

| Field | Result |
| --- | --- |
| Source branch | `feature/v1-browser-uat-readiness-package` |
| Source dirty count | `160` |
| Source staged files | `0` |
| The 14 historical V1-R files still present in source | PASS: `14 / 14` |

The fix was applied only in the clean branch worktree.

## 3. Files Removed From Clean Branch Current Evidence Path

The following `14` inherited older non-Y V1-R reports were removed from the clean branch current evidence path:

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

Removal result:

```text
REMOVED_COUNT=14
MISSING_COUNT=0
```

These reports are historical/superseded and are not accepted current V1-IB release evidence.

## 4. Before / After Package-Exclusion Counts

| Exclusion item | Before E-7-A | After E-7-A | Expected | Result |
| --- | ---: | ---: | ---: | --- |
| V1-R/Y reports | `0` | `0` | `0` | PASS |
| Older non-Y V1-R reports | `14` | `0` | `0` | PASS |
| Root file `=` | absent | absent | absent | PASS |
| Old `test_user_intent_boundary_*.py` tests | `0` | `0` | `0` | PASS |
| Rejected structural classifier source | absent | absent | absent | PASS |
| Rejected structural classifier test | absent | absent | absent | PASS |
| Rejected structural B reports | `0` | `0` | `0` | PASS |
| Unrelated EC-10-G report | absent | absent | absent | PASS |
| Runtime import references to rejected structural classifier | none | none | none | PASS |

The E-7 blocker is fixed in the clean branch current evidence path.

## 5. Verification Results

Required verification from `/tmp/erpai_v1_ib_package_readiness_clean`:

| Check | Result |
| --- | --- |
| Branch confirmation | PASS: `codex/v1-ib-package-readiness` |
| Staged files | PASS: `0` |
| Package-exclusion check: root `=` absent | PASS |
| Package-exclusion check: rejected structural classifier source absent | PASS |
| Package-exclusion check: rejected structural classifier test absent | PASS |
| Package-exclusion check: old lexical tests absent | PASS |
| Package-exclusion check: V1-R/Y count `0` | PASS |
| Package-exclusion check: older non-Y V1-R count `0` | PASS |
| Package-exclusion check: rejected structural B reports absent | PASS |
| Package-exclusion check: unrelated EC-10-G absent | PASS |
| Runtime import scan for `intent_boundary_structural_classifier` | PASS: no refs |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Report hygiene | PASS |
| Clean branch dirty status count after report | `119` |

Full accepted tests were not run in E-7-A. E-7-A is the package-exclusion fix needed before the next verification-focused slice.

## 6. Boundary Statement

No source, test, package config, or old report content was edited except removing the 14 inherited historical V1-R reports from the clean branch current evidence path and adding this E-7-A governance report.

No dirty source worktree changes occurred. No new branch was created. No branch was switched. No staging, commit, push, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred.

E-7-A fixes the inherited historical V1-R report package-exclusion blocker only. It does not claim package readiness.
