# V1-IB-E-28-A Pre-Merge Blocker Resolution Boundary

Decision target: v1_ib_e_28_a_pre_merge_blocker_resolution_boundary_ready_for_qa_owner_review

## 1. Scope And Boundary

E-28-A is report-only. It is a boundary request for resolving the blockers documented by E-28 before any merge-execution slice is reconsidered.

E-28-A does not resolve blockers. It does not edit code, tests, runtime behavior, package config, existing governance reports, PR metadata, PR comments, PR review threads, or GitHub approvals. It does not stage, commit, push, merge, enable auto-merge, close PR #9, package build, run browser/API UAT, deploy, enable strict enforcement, claim package readiness, claim release readiness, claim enterprise/product closure, or approve V2 work.

Allowed worktree:

- `/tmp/erpai_v1_ib_package_readiness_clean`

PR under review:

- URL: https://github.com/htayaung-data/erpnext-ai-agent/pull/9
- Base/head: `main <- codex/v1-ib-package-readiness`
- Expected head SHA: `ec2b59d151c9b4ee4cde2ab710754a86c86839d9`

## 2. Accepted Current State

QA conditionally accepted E-28 as:

- `conditional_accept_v1_ib_e_28_final_pre_merge_verification_boundary_with_blockers`

Current verified state before E-28-A report creation:

| Check | Result |
| --- | --- |
| Branch | `codex/v1-ib-package-readiness` |
| Local HEAD | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| Remote HEAD | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| PR #9 head SHA | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| Ahead/behind | `0 / 0` |
| Worktree before E-28-A | staged `0`, unstaged `0`, untracked exactly E-28 report |
| PR state | open, ready for review / not Draft, unmerged |
| Existing untracked report | `qwen_erp_v1_ib_e_28_final_pre_merge_verification_boundary_2026-06-05.md` |

## 3. Blocker Summary

E-28 identified the following pre-merge blockers. E-28-A does not resolve them.

### 3.1 Unresolved Review Thread

- File: `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- Line: `4159`
- GitHub discussion: `discussion_r3356338969`
- Connector thread id: `PRRT_kwDORVn-is6HFhAO`
- Status: unresolved and non-outdated
- Comment title: `Provide validator evidence before gating all reports`

Allowed local inspection around `service.py:4159` showed the live service path builds the V1-IB runtime boundary immediately after the legacy boundary:

- `legacy_user_intent_boundary = build_user_intent_boundary_contract(raw_msg)`
- `v1_ib_runtime_boundary = build_v1_ib_runtime_boundary(raw_msg)`
- `user_intent_boundary = merge_v1_ib_with_legacy_boundary(...)`

The review concern is that strict runtime validation may fail closed without verifier/proof evidence and may block ordinary factual governed report routing before report execution.

### 3.2 Branch Protection / Required Checks Not Proven

E-28 found that required-check state is not proven:

- Branch protection API for `main` returned HTTP `401`.
- Combined commit statuses for `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` were empty.
- Check-runs total was `0`.
- Workflow-runs list was empty.

Empty check/status lists are not proof of passing required checks. Required-check state must be verified by GitHub-authorized access or explicitly waived by Owner before merge execution.

### 3.3 Governance Reports Not Yet Committed

E-28 report is currently untracked and not part of PR #9 remote branch. E-28-A is also intended to remain untracked in this slice unless a later approved governance follow-up commit stages and commits it.

## 4. Proposed Resolution Path

The safest bounded path is:

1. Decide whether to commit the E-28 and E-28-A governance reports before code/comment resolution.
2. If the review-thread concern is valid, create a separate Dev implementation slice for the `service.py:4159` issue.
3. If a code fix is approved later, run focused tests and accepted verification groups after the fix.
4. Use GitHub-authorized verification for branch protection and required checks, or obtain explicit Owner waiver with reason.
5. Ask QA to verify blocker closure or waiver sufficiency.
6. Only after blocker closure or explicit waiver may `V1-IB-E-29 explicit merge execution request` be reconsidered.

No E-29 merge execution should proceed from E-28-A alone.

## 5. Review-Thread Handling Options

QA/Owner should choose one of these bounded options:

| Option | Description | Boundary |
| --- | --- | --- |
| Dev code/test/report fix | Approve a separate implementation slice if the review comment is valid. | No opportunistic fix inside E-28-A. |
| QA/Owner explicit waiver | Waive the thread if accepted evidence already satisfies the concern. | Waiver must be explicit and reasoned. |
| GitHub thread resolution | Resolve the thread only after QA/Owner agrees the concern is fixed or waived. | No thread resolution or reply occurred in E-28-A. |

## 6. Constraints For Any Future Code Fix

Any future implementation slice for the review-thread issue must preserve these constraints:

- No lexical, keyword, regex, synonym, punctuation, phrase, or no-alarm route-authority shortcuts.
- No broad report-gating bypass.
- Preserve V1-IB validator authority as the runtime authority model.
- Preserve fail-closed behavior for missing, invalid, stale, unsafe, mixed, ambiguous, unresolved, non-redaction-safe, or unproven contracts.
- Preserve package-exclusion gates.
- Update focused tests if behavior changes.
- Preserve final-emission, visible-context, report-routing, model-reasoning, trace/diagnostic, and legacy restrict-only evidence.
- Do not package build, run browser/API UAT, deploy, enable strict enforcement, claim readiness, claim enterprise/product closure, or approve V2 from the fix slice.

## 7. Constraints For Required-Check Verification

Required-check verification before merge execution must be one of:

- Verified by GitHub-authorized access that can inspect branch protection, required status checks, check-runs, and review requirements; or
- Explicitly waived by Owner with a reason recorded in governance.

Empty status/check lists cannot be treated as passing required checks.

## 8. Verification Results For E-28-A

| Verification | Result |
| --- | --- |
| Branch/head/local/remote state | PASS |
| PR #9 state | open, ready for review / not Draft, unmerged |
| Worktree pre-report state | staged `0`, unstaged `0`, untracked exactly E-28 report |
| Package-exclusion gates | PASS |
| Runtime rejected structural classifier refs | `[]` PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | `0 / 1 / 27` PASS |
| Raw append scan | only `authorized_emission.py:271` and `authorized_emission.py:327` PASS |

Package-exclusion gate details:

- Root file `=` absent.
- Rejected structural classifier source absent.
- Rejected structural classifier test absent.
- Rejected structural B reports absent.
- Old `test_user_intent_boundary_*.py` absent.
- V1-R/Y reports absent.
- Older non-Y V1-R reports absent.
- EC-10-G report absent.
- Runtime rejected structural classifier refs empty.

## 9. Explicit Non-Actions

E-28-A performed none of the following:

- No code edit.
- No source/test/runtime/package-config edit.
- No existing governance report edit.
- No GitHub thread resolution.
- No GitHub comment reply.
- No PR state/title/body/reviewer/label/comment/approval/base/head change.
- No merge.
- No auto-merge enablement.
- No package build.
- No browser/API UAT.
- No deployment.
- No strict enforcement.
- No package readiness claim.
- No release readiness claim.
- No enterprise/product closure claim.
- No V2 work.
- No staging, commit, or push.

## 10. Decision Request

QA/Owner should decide:

- Whether to commit E-28 and E-28-A governance reports before blocker-resolution work.
- Whether the unresolved review thread requires a Dev implementation slice or can be explicitly waived.
- Whether branch protection / required checks can be verified with authorized GitHub access or must be explicitly waived.

Recommended next step:

- Governance follow-up commit for E-28 and E-28-A, or a QA/Owner decision selecting the review-thread resolution path.

E-29 merge execution should remain blocked until the unresolved review thread and required-check evidence are resolved or explicitly waived by QA/Owner.
