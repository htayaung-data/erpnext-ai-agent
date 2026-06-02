# V1-IB-D-4-E Package-Readiness Cleanup Plan

Decision target:
`v1_ib_d_4_e_package_readiness_cleanup_plan_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-E is a report-only package-readiness cleanup planning slice. It defines how to move from the current dirty V1-IB worktree toward a clean, reviewable, package-safe branch later.

No source, test, old report, runtime, config, packaging, import, deletion, move, rename, archive, package-exclusion, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, enterprise closure, or V2 work occurred.

No cleanup implementation occurred. This slice only adds this D-4-E governance report.

## 2. Accepted Current V1-IB Evidence To Preserve

Future package/release work must preserve the accepted V1-IB evidence chain:

- V1-IB-A/Q contract/validator foundation.
- V1-IB-B proposal classifier evidence-only path.
- V1-IB-C runtime integration formal closure.
- V1-IB-D authority surface inventory, authority consistency tests, trace/diagnostic redaction audit, legacy restrict-only tests, and cleanup planning reports through D-4-E.
- Current runtime source changes in `service.py` and `authorized_emission.py`.
- Current V1-IB modules:
  - `intent_boundary_contract.py`
  - `intent_boundary_runtime_integration.py`
  - `intent_boundary_proposal_classifier.py`
- Accepted V1-IB tests, including runtime integration, proposal classifier, contract validator, final-emission veto, service adversarial C-3 tests, D-2 authority consistency tests, D-3 trace/diagnostic tests, and D-4-A legacy restrict-only tests.
- D-2-A current-message report-routing authority fix.
- D-3-A blocked-turn raw-message trace redaction fix.

## 3. Dirty Worktree Inventory

Pre-D-4-E dirty count: `149`.

Categorized scan before adding this report:

| Category | Count | Representative paths | Future action | Risk if packaged as-is |
| --- | ---: | --- | --- | --- |
| Accepted source/runtime files | 2 | `qwen_chat/service.py`; `qwen_chat/authorized_emission.py` | Preserve/reapply on clean package branch; verify final diff against accepted C/D evidence | Runtime authority fixes could be lost or mixed with unrelated changes if not reapplied deliberately |
| Accepted V1-IB modules | 3 | `intent_boundary_contract.py`; `intent_boundary_runtime_integration.py`; `intent_boundary_proposal_classifier.py` | Preserve/reapply as accepted A/B/C foundation modules | Missing module reapply would break V1-IB authority path |
| Accepted V1-IB test files | 19 | `test_v1_ib_runtime_integration.py`; `test_v1_ib_runtime_final_emission_contract_veto.py`; `test_v1_ib_service_adversarial_long_context_full_stack.py`; `test_v1_ib_d_legacy_restrict_only.py` | Preserve/reapply accepted tests; run focused and baseline groups | Package could ship without proof of stale-contract, trace, final-emission, service, or legacy restrict-only behavior |
| Accepted governance reports | 67 | V1-IB 0/A/B/C/D accepted reports excluding rejected structural reports | Preserve accepted evidence in manifest-approved package path | Reviewers may lack decision chain if reports are omitted or mixed with stale evidence |
| Rejected structural classifier artifacts | 2 | `intent_boundary_structural_classifier.py`; `test_v1_ib_structural_classifier.py` | Do not package as current authority; archive/package-exclude later after approval | Could be confused with accepted V1-IB-B proposal classifier |
| Rejected structural classifier reports | 3 | 2026-05-28 V1-IB-B deterministic/structural reports | Package-exclude or archive as rejected/superseded | Could be mistaken for accepted B/B-A/B-B evidence |
| Old lexical/user-intent artifacts | 6 | `user_intent_boundary.py`; five `test_user_intent_boundary_*.py` files | Legacy runtime module may remain restrict-only if needed; old tests must be classified/rewrite/quarantine before release evidence | Old lexical allow tests can imply keyword authority if packaged unclassified |
| Old V1-R/Y lexical reports | 31 | `qwen_erp_v1_r_y_a...`; `qwen_erp_v1_r_y_z5...` | Archive/package-exclude as historical superseded lexical patch-loop evidence | Could be mistaken for current enterprise closure evidence |
| Older V1-R governance reports | 14 | V1-R L/M/N/O/Q/U/V/W/X reports | Classify in accepted-evidence manifest; package-exclude unless explicitly accepted | Pre-V1-IB reports may confuse release path |
| Unrelated/pre-existing governance reports | 1 | `qwen_erp_ec_10_g_revised_docs_packaging_boundary_approval_request_2026-05-24.md` | Classify in manifest before package | Unrelated packaging decision could contaminate V1-IB evidence package |
| Unknown/unclassified files | 1 | `=` | Investigate/classify in manifest slice; do not delete silently | Unknown dirty file blocks package-readiness confidence |

The current dirty worktree is not package-ready.

## 4. Package-Readiness Strategy

Recommended package path:

1. Refresh against current `main`.
2. Create a clean package/review branch.
3. Reapply only accepted V1-IB artifacts from the manifest.
4. Exclude or quarantine historical/rejected artifacts.
5. Run full accepted verification on the clean branch.
6. Request QA packaging approval before any staging/commit/package/UAT.

Do not package from the current dirty worktree. The present tree mixes accepted runtime/test/report evidence with rejected structural artifacts, old lexical artifacts, old V1-R/Y reports, older V1-R governance reports, and at least one unknown file.

The clean branch/reapply strategy is safer than trying to stage from this dirty worktree because it forces each artifact to be tied to an accepted decision record.

## 5. Cleanup / Packaging Future Slice Sequence

No cleanup occurs in D-4-E. Future bounded slices should be:

1. `V1-IB-D-4-E-1 accepted-evidence manifest creation`
   - Report-only.
   - Classify every dirty artifact as accepted/current, historical, rejected, unrelated, unknown, package-excluded, or needs QA decision.

2. `V1-IB-D-4-E-2 clean branch / refreshed-main preparation request`
   - Boundary request only.
   - Define branch source, reapply method, file lists, and rollback plan.

3. `V1-IB-D-4-E-3 accepted source/test/report staging plan`
   - Report-only.
   - Define exact accepted files to stage later, with tests and reports mapped to acceptance decisions.

4. `V1-IB-D-4-E-4 historical/rejected artifact archive/package-exclusion implementation`
   - Implementation only after QA/Counterpart approval.
   - Archive/package-exclude rejected structural classifier artifacts, old lexical tests, and old V1-R/Y reports.

5. `V1-IB-D-4-E-5 full verification on clean branch`
   - Verification-only after approved reapply/cleanup.

6. `V1-IB-D-4-E-6 packaging readiness QA checkpoint`
   - Report-only QA gate.
   - No release claim without QA approval.

Only after QA approval:

- browser/API UAT planning.
- packaging execution planning.
- staging/commit/push/package/deployment discussions.

## 6. Do-Not-Package List

Do not include these as current authority or current release evidence:

- `intent_boundary_structural_classifier.py`
- `test_v1_ib_structural_classifier.py`
- old `test_user_intent_boundary_*.py` files unless rewritten/aligned under V1-IB and accepted
- old V1-R/Y lexical reports
- rejected 2026-05-28 V1-IB-B structural reports
- stale reports marked historical, superseded, or rejected
- unknown file `=`
- any artifact, test, or report not explicitly accepted in the V1-IB chain

Legacy `user_intent_boundary.py` must not be packaged as an allow-authority source. If retained temporarily, it must be documented as restrict-only/fail-closed and covered by D-4-A-style assertions.

## 7. Must-Preserve List

Must preserve/reapply on a clean package/review branch:

- `service.py`
- `authorized_emission.py`
- `intent_boundary_contract.py`
- `intent_boundary_runtime_integration.py`
- `intent_boundary_proposal_classifier.py`
- accepted V1-IB tests:
  - `test_v1_ib_intent_boundary_contract_validator.py`
  - `test_v1_ib_intent_boundary_proposal_classifier.py`
  - `test_v1_ib_runtime_integration.py`
  - `test_v1_ib_runtime_final_emission_contract_veto.py`
  - `test_v1_ib_runtime_adversarial_prerouting.py`
  - `test_v1_ib_runtime_adversarial_final_emission.py`
  - C-3 service adversarial tests
  - D-2 authority consistency tests
  - D-3 trace/diagnostic audit tests
  - D-4-A legacy restrict-only tests
  - aligned authorized-emission tests
- accepted governance reports:
  - V1-IB-0/A plan and amendments
  - V1-IB-A through A-Q
  - V1-IB-B through B-B accepted proposal-classifier evidence
  - V1-IB-C through C-5 runtime integration closure
  - V1-IB-D through D-4-E accepted checkpoints/plans
- D-2-A current-message report-routing fix evidence
- D-3-A blocked-turn trace raw-message redaction fix evidence
- D-4-A tests proving legacy restrict-only behavior

## 8. Verification Gates Before Any Packaging

Future packaging cannot proceed until all of these pass on a clean branch:

- clean `git status` except intended staged files
- accepted baseline passes
- D tests pass
- full relevant V1-IB test group passes
- Python compile
- Qwen enterprise guardrail PASS
- fake-Frappe service import PASS
- direct assistant inventory remains expected
- raw append scan shows only authorized sinks
- trace leak tests pass
- legacy restrict-only tests pass
- stale contract tests pass
- rejected structural classifier import scan clean
- old lexical tests are not included as current release evidence
- stale V1-R/Y reports are archived/package-excluded or manifest-labeled as historical
- unknown file `=` is classified or removed only with approval
- report manifest approved by QA/Counterpart

## 9. Risk Assessment

The current dirty worktree is not package-ready.

Packaging from the dirty tree would be high risk because accepted V1-IB artifacts are intermingled with rejected structural classifier artifacts, old lexical/user-intent tests, stale V1-R/Y reports, older V1-R governance reports, and at least one unknown file.

The architecture direction is sound: V1-IB authority has moved to contract authority, current-message gates, fail-closed runtime integration, final-emission veto, trace redaction, adversarial service tests, and legacy restrict-only proof.

Package discipline is now the main enterprise risk. Cleanup must not become stealth deletion, stealth staging, or stealth release. QA/Counterpart approval is required before any implementation cleanup.

## 10. Recommended Next Step

Recommend:

`V1-IB-D-4-E-1 accepted-evidence manifest creation`, report-only.

Reason:
the dirty count is high, and the audit found an unknown/unclassified dirty file (`=`) plus multiple historical/rejected report/test families. A manifest is needed before D-5 closure readiness or any package branch work.

Do not proceed to D-5 formal D closure readiness until the manifest/classification step is accepted or QA explicitly decides D-4-E is sufficient.

## 11. Verification

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_e_package_readiness_cleanup_plan_2026-05-31.md` exists |
| Dirty worktree count | Pre-report recorded: `149`; final count recorded: `150` |
| Categorized dirty file summary | PASS: categories and counts recorded above |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

Do not claim D-4 closure, V1-IB-D closure, packaging readiness, release readiness, enterprise closure, or V2 work from D-4-E.
