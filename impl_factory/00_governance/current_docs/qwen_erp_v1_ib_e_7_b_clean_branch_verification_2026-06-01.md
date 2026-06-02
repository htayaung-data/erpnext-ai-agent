# V1-IB-E-7-B Clean Branch Verification

Decision target:
`v1_ib_e_7_b_clean_branch_verification_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-7-B is a clean-branch verification-only slice after accepted artifact reapply and the E-7-A historical V1-R report exclusion fix.

Allowed worktree used:

```text
/tmp/erpai_v1_ib_package_readiness_clean
```

Branch:

```text
codex/v1-ib-package-readiness
```

No source files were edited. No test files were edited. No package config changed. No additional cleanup, deletion, move, archive, or package-exclusion action was performed. The dirty source worktree `/tmp/erpai_pr5_postmerge_verify` was not modified.

No staging, commit, push, package, browser/API UAT, deployment, strict enforcement, package-readiness claim, release-readiness claim, enterprise/product closure, or V2 work occurred.

## 2. Branch And Status

| Field | Result |
| --- | --- |
| Clean worktree | `/tmp/erpai_v1_ib_package_readiness_clean` |
| Branch | `codex/v1-ib-package-readiness` |
| HEAD | `08f0ec202d9ae6af33305b74c8b15e37f617680d` |
| Staged files before report | `0` |
| Dirty status count before report | `119` |
| Staged files after report | `0` |
| Dirty status count after report | `120` |

## 3. Package-Exclusion Gates

Package-exclusion gates passed before test execution:

| Gate | Result |
| --- | --- |
| Root file `=` absent | PASS |
| Rejected `intent_boundary_structural_classifier.py` absent | PASS |
| Rejected `test_v1_ib_structural_classifier.py` absent | PASS |
| Rejected 2026-05-28 structural B reports absent | PASS |
| Old `test_user_intent_boundary_*.py` tests absent | PASS |
| V1-R/Y report count | PASS: `0` |
| Older non-Y V1-R report count | PASS: `0` |
| Unrelated EC-10-G report absent | PASS |
| Unknown untracked artifacts absent outside accepted E artifacts/reports | PASS |
| Runtime import scan for `intent_boundary_structural_classifier` | PASS: no refs |

## 4. Test And Verification Commands

### Accepted Baseline

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_prerouting \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_final_emission \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration \
  ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_service_control_authorized_emission_contracts
```

Result:

```text
Ran 157 tests in 0.637s
OK
```

### C-3 Service Adversarial Tests

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_model_reasoning \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_selector \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_trace_redaction \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_long_context_full_stack
```

Result:

```text
Ran 19 tests in 1.380s
OK
```

### Focused Contract / Classifier / Runtime / Authorized-Emission Tests

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration \
  ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_service_control_authorized_emission_contracts
```

Result:

```text
Ran 147 tests in 0.730s
OK
```

### D Authority / Trace / Legacy Tests

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_contract_audit \
  ai_assistant_ui.tests.test_v1_ib_d_legacy_restrict_only
```

Result:

```text
Ran 18 tests in 0.297s
FAILED (failures=1)
```

Failing test:

```text
ai_assistant_ui.tests.test_v1_ib_d_legacy_restrict_only.V1IBDLegacyRestrictOnlyTests.test_rejected_structural_classifier_is_not_runtime_authority_import
```

Failure summary:

```text
self.assertTrue(test_path.exists())
AssertionError: False is not true
```

## 5. Blocker

E-7-B found a clean-branch test-alignment blocker.

The package-exclusion gate correctly requires the rejected structural classifier test file to be absent:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py
```

The D legacy restrict-only test still asserts that rejected test file exists as part of its historical artifact check. In the clean package branch, that assertion is no longer valid because rejected structural classifier artifacts are intentionally excluded from current package evidence.

This is not a runtime authority leak. It is a test expectation mismatch between:

- accepted E package-exclusion behavior: rejected structural classifier test absent from clean package tests
- old D legacy restrict-only assertion: rejected structural classifier test path exists

## 6. Stop Condition

The E-7-B stop condition fired because an accepted D test failed.

No source or test fix was made in E-7-B. Verification stopped after documenting blocker evidence. The following required verification items were not run after the blocker:

- Python compile for accepted V1-IB source/tests
- Qwen enterprise guardrail
- fake-Frappe import
- direct assistant inventory
- raw append scan
- final `git diff --check`
- final `git diff --cached --check`
- final report hygiene scan before this report was copied

Report hygiene and diff checks were run after adding this report and are recorded below.

## 7. Post-Report Hygiene

| Check | Result |
| --- | --- |
| Report present | PASS |
| Report hygiene | PASS |
| Control-character scan | PASS |
| Trailing-whitespace scan | PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Staged files | PASS: `0` |
| Dirty status count after report | `120` |

## 8. Recommended Follow-Up

Recommended next slice:

```text
V1-IB-E-7-C clean-branch D legacy restrict-only test alignment
```

The follow-up should update the D legacy restrict-only clean-branch expectation so it proves rejected structural classifier artifacts cannot authorize runtime behavior without requiring the rejected test file to exist in the clean package test suite.

The follow-up must remain bounded:

- no runtime source changes unless separately approved
- no reintroduction of rejected structural classifier artifacts
- no reintroduction of old lexical tests
- no staging, commit, push, package, UAT, deployment, strict enforcement, readiness claim, enterprise closure, or V2

## 9. Boundary Statement

E-7-B does not claim package readiness. It found blocker evidence after package-exclusion gates passed.

No commit, push, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred.
