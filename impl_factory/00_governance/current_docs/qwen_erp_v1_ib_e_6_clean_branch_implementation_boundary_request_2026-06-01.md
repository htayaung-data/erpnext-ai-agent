# V1-IB-E-6 Clean Branch Implementation Boundary Request

Decision target:
`v1_ib_e_6_clean_branch_implementation_boundary_request_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-6 is a report-only implementation boundary request. It defines the exact future boundary for creating or switching to a clean branch and reapplying accepted V1-IB artifacts, but it does not perform the implementation.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_6_clean_branch_implementation_boundary_request_2026-06-01.md`

No branch was created. No branch was switched. No files were staged, committed, pushed, packaged, deployed, deleted, moved, renamed, archived, truncated, cleaned, or reapplied. No source files were edited. No tests were edited. No package config changed. No old reports or manifests were edited.

No browser/API UAT, strict enforcement, release readiness claim, enterprise/product closure claim, or V2 work occurred.

E-6 does not approve clean-branch implementation. It requests QA/Counterpart review of the future implementation boundary.

## 2. Accepted Prior Basis

Accepted basis:

- V1-IB-A accepted contract/validator foundation.
- V1-IB-B accepted proposal-classifier evidence-only closure.
- V1-IB-C accepted runtime integration closure.
- V1-IB-D accepted authority consistency, trace/diagnostic, legacy restrict-only, and cleanup planning evidence.
- V1-IB-E-0 through E-5 accepted package-readiness planning:
  - E-0 clean branch / package-readiness boundary request
  - E-1 clean branch preparation plan
  - E-2 accepted artifact reapply/staging plan
  - E-3 rejected/historical artifact exclusion plan
  - E-3-A older V1-R inventory completeness fix
  - E-4 unknown file `=` classification/disposition plan
  - E-5 package-exclusion verification plan
- D-4-E-1 accepted-evidence manifest remains the artifact-classification basis.
- Current dirty worktree remains not package-ready.

E-6 preserves the accepted authority rule:

```text
Only current, validated, hash-matching, trace-safe V1-IB contract authority may allow runtime business routing, context reuse, model reasoning, governed report routing, or final emission.
```

No classifier/proposer evidence, semantic-safe output, lexical/no-alarm logic, legacy intent boundary, report selector, visible context, final answer text, trace metadata, old V1-R artifact, or rejected structural classifier artifact may authorize runtime behavior.

## 3. Future Clean Branch Objective

Future QA-approved implementation slice objective:

Create or switch to a clean package/review branch and reapply only accepted V1-IB artifacts from the manifest-guided accepted set.

The future implementation must:

- start from current `main` or a QA-approved refreshed branch
- preserve accepted V1-IB source/runtime artifacts
- preserve accepted V1-IB tests
- preserve accepted current governance reports/manifests needed for release evidence
- exclude rejected, historical, unrelated, and unknown artifacts from current evidence
- run package-exclusion verification gates
- stop on conflicts, unknown artifacts, rejected imports, or authority-model regressions

E-6 does not perform branch creation, branch switching, reapply, staging, package, UAT, deployment, or cleanup.

## 4. Exact Future Branch Rules

Future clean branch rules:

- Branch name must use `codex/` prefix unless QA/Counterpart specifies otherwise.
- Candidate branch names:
  - `codex/v1-ib-package-readiness`
  - `codex/v1-ib-clean-reapply`
- Branch creation/switch may happen only after QA accepts E-6 and explicitly approves a future implementation slice.
- Before any branch action, record:
  - current `HEAD`
  - current branch name
  - current `git status --short`
  - dirty worktree count
  - staged file count
  - accepted artifact manifest version/reference
- No destructive cleanup in the dirty worktree.
- No `git reset --hard`.
- No `git checkout --`.
- No `git clean`.
- No broad deletion, rename, archive, or truncation.
- No staging unrelated dirty files.
- If patch/reapply is used, apply only accepted artifacts from D-4-E-1 and E planning manifests.
- Rejected, historical, unrelated, and unknown artifacts must not be copied into the clean branch as current evidence.
- If conflicts occur, stop and report; do not force.

Future implementation must treat the current dirty worktree as evidence-bearing but not package-ready.

## 5. Future Allowed Artifact Set

Future clean branch may reapply these accepted-current categories only after approval:

| Category | Allowed future artifacts |
| --- | --- |
| V1-IB contract/validator source | `intent_boundary_contract.py` and accepted contract validator tests/reports |
| Proposal-classifier source | `intent_boundary_proposal_classifier.py` and accepted evidence-only proposal classifier tests/reports |
| Runtime integration source changes | Accepted `service.py` changes and `intent_boundary_runtime_integration.py` runtime glue |
| Authorized emission final-veto changes | Accepted `authorized_emission.py` V1-IB final-emission veto and payload sanitization behavior |
| Legacy restrict-only dependency | `user_intent_boundary.py` only if runtime still requires it and only as restrict-only/fail-closed, never allow authority |
| Accepted V1-IB tests | A/B/C/D accepted validator, classifier, runtime, service adversarial, trace/diagnostic, authority consistency, and legacy restrict-only tests |
| Accepted governance evidence | V1-IB accepted architecture, A/B/C/D/E current reports and manifests |
| Package-exclusion verification evidence | E-5 package-exclusion verification plan and future verification report(s) |

Future reapply must preserve D-2-A current-message report-routing authority fix and D-3-A blocked-turn raw-message diagnostic redaction fix.

## 6. Future Excluded Artifact Set

Future clean branch must exclude as current evidence:

- rejected `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- rejected `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`
- rejected 2026-05-28 V1-IB-B structural reports:
  - `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
  - `qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
  - `qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- all old V1-R/Y reports from current evidence (`31`)
- all older non-Y V1-R reports from current evidence (`28`)
- old direct `test_user_intent_boundary_*.py` lexical tests unless rewritten and QA-accepted
- root file `=`
- unrelated EC-10-G report unless QA reclassifies it
- any unknown untracked artifact
- any lexical/regex/synonym/keyword/no-alarm artifact used as route-authority evidence

If QA later approves a historical archive, excluded artifacts may only appear outside runtime/package current evidence paths and must be labeled rejected, historical, unrelated, or unknown disposition evidence as appropriate.

## 7. Future Validation Gates After Clean-Branch Reapply

Future clean branch implementation must pass:

- package-exclusion verification gates from E-5
- accepted baseline tests
- V1-IB A/B/C/D tests
- C-3 service adversarial tests
- contract validator tests
- proposal classifier tests
- final-emission veto tests
- trace/diagnostic leak tests
- legacy restrict-only tests
- Python compile
- Qwen enterprise guardrail
- fake-Frappe import
- direct assistant inventory remains `0 / 1 / 27`
- raw append scan only authorized sinks
- rejected structural classifier import scan clean
- report hygiene
- staged-file review
- clean package tree scan
- accepted evidence manifest consistency scan
- no raw business payloads or secrets in reports/traces
- no lexical/keyword/regex/synonym/no-alarm route authority claims

Future implementation must produce verification evidence before any commit, push, package, or UAT request.

## 8. Failure Rules

Future clean branch implementation must stop if:

- rejected structural classifier appears in runtime/package
- rejected structural classifier test appears in accepted current tests
- stale lexical artifacts are required to pass accepted tests
- package tree contains root file `=`
- old V1-R reports appear as current evidence
- any unknown artifact appears in package tree
- tests require permissive fallback to legacy authority
- legacy `user_intent_boundary.py` expands V1-IB authority instead of restricting/failing closed
- V1-IB contract is not sole authority for routing, context reuse, model reasoning, governed requery, compiled query, report routing, final emission, or trace metadata
- package-exclusion verification gates are missing or unverifiable
- any raw business payload, selected answer text, ERP row, artifact, rendered payload, narrative, grounded evidence, secret, token, private key, or cookie appears in reports/traces where forbidden

If any failure occurs, do not fix opportunistically. Document the blocker and request a narrow follow-up slice.

## 9. Required E-6 Verification

Verification after report copy:

| Check | Result |
| --- | --- |
| Report present | PASS |
| Report hygiene | PASS: no placeholder results; decision target present |
| Control-character scan | PASS |
| Trailing-whitespace scan | PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS |
| Staged files count | PASS: `0` |
| Dirty worktree count | PASS: `160` after adding E-6 report |

Read-only stop-condition scan:

| Check | Result |
| --- | --- |
| Runtime dependency on rejected structural classifier | PASS: no `qwen_chat` runtime references found outside the rejected file itself |

## 10. Acceptance Standard

E-6 is acceptable only if it creates a precise, auditable boundary for a future clean-branch implementation without doing that implementation.

E-6 does not approve:

- branch creation
- branch switching
- accepted artifact reapply
- staging
- commit
- push
- package
- browser/API UAT
- deployment
- strict enforcement
- release readiness
- enterprise/product closure
- V2 work

If branch creation or cleanup appears necessary now, stop and request QA/Counterpart approval first.

The current dirty worktree remains not package-ready.
