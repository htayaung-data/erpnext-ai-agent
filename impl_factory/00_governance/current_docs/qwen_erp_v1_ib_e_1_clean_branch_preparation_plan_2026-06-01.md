# V1-IB-E-1 Clean Branch Preparation Plan

Decision target:
`v1_ib_e_1_clean_branch_preparation_plan_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-1 is a report-only clean branch preparation planning slice. It defines how a future approved package-readiness branch should be prepared from current `main` or a QA-approved refreshed branch, how accepted artifacts should be mapped for reapply, how rejected/historical/unknown artifacts should be excluded or investigated, and what approvals are required before any branch creation or file changes.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_1_clean_branch_preparation_plan_2026-06-01.md`

No branch was created. No branch was switched. No `git checkout`, `git switch`, `git reset`, `git clean`, or destructive git command was run.

No source files were edited. No test files were edited. No old reports were edited. No package config changed. No files were moved, deleted, renamed, or archived. No source/test/report/config behavior changed except adding this E-1 report.

No cleanup, staging, commit, push, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred. No keyword, regex, synonym, punctuation, phrase, lexical, or no-alarm route authority was added.

## 2. Accepted Precondition

Accepted preconditions for E-1:

- V1-IB-A contract/validator foundation evidence is accepted.
- V1-IB-B proposal classifier evidence-only foundation is accepted.
- V1-IB-C runtime integration evidence is formally closed.
- V1-IB-D formal closure is accepted as evidence-only:

```text
accept_v1_ib_d_formal_closure_as_authority_consistency_trace_legacy_cleanup_planning_evidence
```

- E-0 clean branch / package-readiness boundary request is accepted.
- D-4-E-1 accepted-evidence manifest is accepted and is the current artifact-classification basis.
- Current dirty tree remains not package-ready.
- Clean branch work requires explicit QA/Counterpart approval later.

E-1 does not approve clean branch creation, clean branch switching, reapply implementation, cleanup, staging, commit, push, package, UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2.

## 3. Proposed Clean Branch Source

Proposed future clean branch source:

- current `main`, or
- a QA-approved refreshed branch if QA/Counterpart requires a different source.

Required future rules:

- The source branch must be refreshed before implementation.
- The current dirty worktree must not be used as the package branch.
- Future package work must not stage directly from the dirty evidence worktree.
- Current branch name, current `HEAD`, and refresh state must be captured during a later approved preflight slice before branch implementation.

E-1 does not fetch, pull, switch branches, create branches, stage files, or modify branch state. If the current branch/main status is unknown or stale, that is a required preflight check for later E-5/E-6, not something to fix in E-1.

## 4. Branch Naming Proposal

Suggested future branch names:

- `codex/v1-ib-package-readiness`
- `codex/v1-ib-clean-reapply`

The final branch name requires QA/Counterpart approval. E-1 does not create either branch.

## 5. Accepted Artifact Reapply Strategy

Future reapply must use D-4-E-1 manifest classifications.

| Manifest classification | Future handling rule |
| --- | --- |
| `accepted_current` | Preserve/reapply on the clean branch with acceptance references and verification. |
| `legacy_restrict_only` | Preserve only if still required by runtime and documented as restrict-only/fail-closed, not route allow authority. |
| `historical_superseded` | Archive or package-exclude; do not include as current evidence. |
| `rejected_superseded` | Package-exclude or quarantine; do not include as current evidence. |
| `unrelated` | Include only with separate QA decision. |
| `unknown_needs_review` | Investigate and do not package until classified. |

Later reapply should happen as follows:

- Source files reapply as reviewed diffs from accepted evidence only.
- Tests reapply with acceptance references and verification mapping.
- Governance reports reapply only accepted-current reports.
- Rejected/historical docs are not included as current evidence.
- Unknown file `=` remains excluded until classified.
- Reapply should preserve D-2-A current-message report-routing authority fix, D-3-A blocked-turn raw-message redaction fix, D-4-A legacy restrict-only evidence, and accepted V1-IB A/B/C/D evidence.

## 6. Preflight Checks Required Before Branch Implementation

Future E-5/E-6 preflight checks must include:

- current `main` fetch/refresh status
- current branch name and current `HEAD`
- dirty status summary
- accepted artifact list from D-4-E-1 manifest
- rejected/historical/unknown artifact list from D-4-E-1 manifest
- no unreviewed binary/artifact files
- no package config changes pending
- no staged files
- explicit QA approval for branch operation
- explicit QA approval for branch name
- explicit QA approval for any cleanup, exclusion, or quarantine action

Do not run fetch, pull, branch creation, branch switching, or cleanup unless a later approved slice explicitly allows it.

## 7. Future E Slice Sequence

Future E slices should proceed only after separate approval:

| Slice | Proposed scope |
| --- | --- |
| E-2 | Accepted artifact reapply/staging plan, report-only. |
| E-3 | Rejected/historical artifact exclusion plan, report-only. |
| E-4 | Unknown file `=` classification/disposition plan, report-only unless cleanup is separately approved. |
| E-5 | Clean branch implementation boundary request. |
| E-6 | Clean branch creation/reapply implementation, only after explicit approval. |
| E-7 | Clean branch verification report. |
| E-8 | Package-readiness QA checkpoint. |

E-1 does not implement any future E slice.

## 8. Rollback / Safety Plan For Future Branch Work

Future branch work safety rules:

- No destructive git commands.
- No `git reset --hard`.
- No `git clean`.
- No deletion without an explicit file list and QA approval.
- No archive/move/rename operation without an explicit file list and QA approval.
- Before any future branch operation, capture current status and current `HEAD`.
- Keep the dirty evidence tree untouched until clean branch implementation is approved.
- If reapply conflicts occur, stop and report; do not force.
- If manifest ambiguity is found, stop and request a narrow QA decision.
- If unknown file `=` is still unclassified, do not package it.

The future clean branch should be reversible by abandoning the new branch, not by destructive operations against the dirty evidence worktree.

## 9. Verification Gates For Future Clean Branch

Future clean branch must pass:

- accepted baseline
- D tests
- C-3 service adversarial tests
- contract validator tests
- proposal classifier tests
- final-emission veto tests
- trace leak tests
- legacy restrict-only tests
- Python compile
- Qwen enterprise guardrail
- fake-Frappe import
- direct assistant inventory
- raw assistant append scan only authorized sinks
- rejected structural classifier import scan clean
- old lexical tests excluded or explicitly aligned
- historical/rejected reports excluded or manifest-labeled
- unknown file `=` absent or QA-classified
- clean git status except explicitly approved intended staged files

No legacy, lexical, regex, keyword, synonym, punctuation, phrase, semantic-safe, model-output, report-selector, visible-context, trace-metadata, final-answer, or no-alarm path may be introduced or reintroduced as route authority during package preparation.

## 10. Current Carry-Forward Risks

Current carry-forward risks:

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

The dirty worktree remains evidence-bearing but not package-ready.

## 11. Decision Requested

QA/Counterpart decision requested:

```text
accept_v1_ib_e_1_clean_branch_preparation_plan
```

If accepted, the next step should be:

```text
V1-IB-E-2 accepted artifact reapply/staging plan, report-only
```

E-1 does not approve clean branch creation, package readiness, release readiness, browser/API UAT readiness, V1-IB-E implementation, enterprise/product closure, or V2.

## 12. Verification For E-1

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
| Dirty worktree count | PASS: `154` after adding E-1 report |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

If any future verification fails, do not fix source opportunistically. Document the failure, recommend a narrow follow-up slice, and stop.

Do not claim clean branch creation, package readiness, release readiness, UAT readiness, E implementation, enterprise/product closure, or V2 work from E-1.
