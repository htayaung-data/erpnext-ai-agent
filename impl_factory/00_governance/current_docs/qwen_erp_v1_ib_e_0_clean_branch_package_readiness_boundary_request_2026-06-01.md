# V1-IB-E-0 Clean Branch / Package-Readiness Boundary Request

Decision target:
`v1_ib_e_0_clean_branch_package_readiness_boundary_request_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-0 is a report-only planning boundary request for the next phase: clean branch / package-readiness preparation and verification.

E-0 is not package implementation. It does not create a clean branch, move files, delete files, archive files, stage files, commit files, push files, package artifacts, run UAT, deploy, enable strict enforcement, claim release readiness, claim enterprise/product closure, or start V2 work.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_0_clean_branch_package_readiness_boundary_request_2026-06-01.md`

No source files were edited. No test files were edited. No old reports were edited. No package config changed. No source/test/report/config behavior changed except adding this E-0 report. No keyword, regex, synonym, punctuation, lexical, phrase, or no-alarm route authority was added.

## 2. Accepted Precondition

Accepted preconditions for E-0:

- V1-IB-A contract/validator foundation is accepted.
- V1-IB-B proposal classifier is accepted as evidence-only.
- V1-IB-C runtime integration evidence is formally closed.
- V1-IB-D is accepted as authority consistency, trace/diagnostic safety, legacy restrict-only, rejected/historical artifact classification, and package-readiness planning evidence.
- QA/Risk accepted V1-IB-D formal closure as evidence-only:

```text
accept_v1_ib_d_formal_closure_as_authority_consistency_trace_legacy_cleanup_planning_evidence
```

Important boundary:

- V1-IB-D closure does not approve package readiness.
- V1-IB-D closure does not approve release readiness.
- V1-IB-D closure does not approve browser/API UAT.
- V1-IB-D closure does not approve deployment.
- V1-IB-D closure does not approve strict enforcement.
- V1-IB-D closure does not approve enterprise/product closure.
- V1-IB-D closure does not approve V2 work.

D-4-E-1 accepted-evidence manifest is the current evidence-classification basis for all future package planning. The current dirty worktree must not be packaged.

## 3. E Phase Objective

V1-IB-E theme:

```text
Clean branch / package-readiness preparation and verification.
```

V1-IB-E should define and later execute, only after explicit QA approval, how to move from dirty V1-IB evidence to a clean, reviewable package-readiness branch.

E objectives:

- build a clean package/review branch plan
- preserve accepted V1-IB artifacts
- exclude or quarantine historical/rejected artifacts
- classify unknown file `=`
- define reapply strategy from the current dirty tree to clean `main`
- define package verification gates
- prepare for later QA package-readiness review

E-0 defines the boundary only. It does not implement any E cleanup, reapply, package, branch, staging, commit, push, UAT, or deployment action.

## 4. Clean Branch Strategy

Proposed future clean branch strategy:

1. Refresh from current `main`.
2. Create a clean review/package branch only after QA approval.
3. Reapply only `preserve_reapply` artifacts from the D-4-E-1 manifest.
4. Do not bring over rejected or historical artifacts as current evidence.
5. Investigate unknown file `=` before any package operation.
6. Run accepted tests and D tests on the clean branch.
7. Run package-readiness hygiene gates on the clean branch.
8. Request QA review before any staging, commit, package, or UAT action.

The current dirty worktree is evidence-bearing but not package-ready. It must be treated as the source for manifest-guided reapply decisions, not as a package branch.

## 5. Artifact Handling Rules

Artifact handling must follow D-4-E-1 classifications.

Must preserve/reapply on a future approved clean branch:

- accepted source/runtime files
- accepted V1-IB modules
- accepted tests
- accepted governance reports
- D-2-A current-message report-routing fix
- D-3-A blocked-turn raw-message redaction fix
- D-4-A legacy restrict-only tests

Must not package as current evidence:

- rejected structural classifier source/test
- old lexical `test_user_intent_boundary_*.py` tests unless rewritten/aligned and accepted
- old V1-R/Y lexical reports
- older superseded V1-R reports
- rejected 2026-05-28 V1-IB-B structural reports
- unknown file `=`
- unrelated governance reports without QA decision

Legacy `user_intent_boundary.py` may only be preserved as legacy restrict-only if runtime still imports it and D-4-A restrict-only evidence remains valid. It must not be described as route allow authority.

## 6. Proposed E Slice Sequence

Future E slices should be separately approved. E-0 does not implement them.

| Slice | Proposed scope |
| --- | --- |
| E-1 | Clean branch preparation plan, report-only. |
| E-2 | Accepted artifact reapply/staging plan, report-only. |
| E-3 | Rejected/historical artifact exclusion plan, report-only. |
| E-4 | Unknown file `=` classification/disposition plan, report-only or cleanup only if separately approved. |
| E-5 | Clean branch implementation request, boundary report. |
| E-6 | Clean branch reapply implementation, only after explicit approval. |
| E-7 | Clean branch verification report. |
| E-8 | Package-readiness QA checkpoint. |

Only after QA package-readiness approval should the project move to browser/API UAT planning. E-0 does not approve UAT.

## 7. Verification Gates For Future Clean Branch

Future clean branch must pass:

- accepted baseline
- D tests
- C-3 service adversarial tests
- contract validator tests
- proposal classifier tests
- final-emission veto tests
- trace/diagnostic leak tests
- legacy restrict-only tests
- Python compile
- Qwen enterprise guardrail
- fake-Frappe import
- direct assistant inventory
- raw assistant append scan only authorized sinks
- rejected structural classifier import scan
- old lexical tests excluded or explicitly aligned
- historical/rejected reports excluded or manifest-labeled
- clean git status except intended staged files, once staging is explicitly approved

No lexical, regex, keyword, synonym, punctuation, phrase, or no-alarm logic may be introduced as route authority during future package preparation.

## 8. Current Carry-Forward Risks

Carry-forward risks:

- Dirty worktree count remains high.
- Unknown root-level file `=` remains.
- Rejected structural classifier artifacts remain physically present.
- Old lexical tests remain physically present.
- Old V1-R/Y reports remain physically present.
- Older V1-R reports remain physically present.
- Package readiness is not approved.
- Browser/API UAT is not approved.
- Release readiness is not approved.
- Deployment is not approved.
- Strict enforcement is not approved.
- Enterprise/product closure is not approved.

The accepted D-4-E-1 manifest must guide all future cleanup and package-readiness work.

## 9. Decision Requested

QA/Counterpart decision requested:

```text
accept_v1_ib_e_0_clean_branch_package_readiness_boundary_request
```

If accepted, Development may proceed only to:

```text
V1-IB-E-1 clean branch preparation plan, report-only
```

E-0 does not approve E implementation, cleanup, staging, commit, push, packaging, UAT, deployment, release readiness, enterprise/product closure, strict enforcement, or V2.

## 10. Verification For E-0

Verification after report copy:

| Check | Result |
| --- | --- |
| Report present | PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS |
| Staged files count | PASS: `0` |
| Dirty worktree count | PASS: `153` after adding E-0 report |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

If any future E verification fails, the project should not fix source opportunistically. It should document the failure, recommend a narrow follow-up slice, and stop.

Do not claim package readiness, release readiness, UAT readiness, clean branch creation, V1-IB-E implementation, enterprise/product closure, or V2 work from E-0.
