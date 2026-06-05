# V1-IB-E-28 Final Pre-Merge Verification / Merge-Execution Boundary

Decision target: v1_ib_e_28_final_pre_merge_verification_boundary_ready_for_qa_owner_review

## 1. Scope And Boundary

E-28 is a report-only final pre-merge verification and merge-execution boundary request for PR #9.

This report does not approve or execute merge. It does not change PR state, PR title/body, reviewers, labels, comments, approvals, base, or head. It does not stage, commit, push, package build, run browser/API UAT, deploy, enable strict enforcement, claim package readiness, claim release readiness, claim enterprise/product closure, or approve V2 work.

Allowed worktree used:

- `/tmp/erpai_v1_ib_package_readiness_clean`

PR under review:

- URL: https://github.com/htayaung-data/erpnext-ai-agent/pull/9
- Base/head: `main <- codex/v1-ib-package-readiness`
- Expected head SHA: `ec2b59d151c9b4ee4cde2ab710754a86c86839d9`

## 2. Current PR / Branch State

| Check | Result |
| --- | --- |
| Local branch | `codex/v1-ib-package-readiness` |
| Local HEAD | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| Remote HEAD | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| PR head SHA | `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` |
| Upstream | `origin/codex/v1-ib-package-readiness` |
| Ahead/behind | `0 / 0` |
| Worktree before report | staged `0`, unstaged `0`, untracked `0` |
| PR state | open, ready for review / not Draft, unmerged |
| PR mergeable field | `true` from connector metadata |

## 3. GitHub Review / Check Status

GitHub connector metadata verified PR #9 is open, not Draft, unmerged, base `main`, head `codex/v1-ib-package-readiness`, and head SHA `ec2b59d151c9b4ee4cde2ab710754a86c86839d9`.

Review/comment status is not clean for merge execution:

- Submitted reviews: one `COMMENTED` automated Codex review.
- Inline review threads: one unresolved, non-outdated thread remains.
- Unresolved thread location: `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py:4159`.
- Thread summary: asks for validator evidence before strict V1-IB pre-routing authority gates all reports.
- The review was anchored to an earlier reviewed commit `b48aedb46c`, but the thread remains unresolved and non-outdated in PR metadata.

GitHub check / branch-protection status is not sufficient for automatic merge execution:

- Combined commit status for `ec2b59d151c9b4ee4cde2ab710754a86c86839d9`: `statuses=[]`.
- GitHub check-runs API for the head SHA: HTTP 200, `total_count=0`.
- GitHub workflow-runs connector for the head SHA: `workflow_runs=[]`.
- Branch protection API for `main`: HTTP 401 `Requires authentication`, so required check/review enforcement could not be verified from this environment.

E-29 merge execution must not proceed unless QA/Owner either resolves the review/check evidence gaps or explicitly waives them for the merge-execution slice.

## 4. Package-Exclusion Gates

| Gate | Result |
| --- | --- |
| Root file `=` absent | PASS |
| Rejected `intent_boundary_structural_classifier.py` absent | PASS |
| Rejected `test_v1_ib_structural_classifier.py` absent | PASS |
| Rejected structural B reports absent | PASS |
| Old `test_user_intent_boundary_*.py` absent | PASS |
| V1-R/Y report count | `0` PASS |
| Older non-Y V1-R report count | `0` PASS |
| EC-10-G report absent | PASS |
| Runtime rejected structural classifier refs | `[]` PASS |

## 5. Local Verification Results

| Verification group | Command/result |
| --- | --- |
| Accepted baseline | `python3 -m unittest ...` ran 157 tests: PASS |
| C-3 service adversarial | `python3 -m unittest ...` ran 19 tests: PASS |
| Focused contract/classifier/runtime/authorized-emission | `python3 -m unittest ...` ran 147 tests: PASS |
| D authority/trace/legacy | `python3 -m unittest ...` ran 18 tests: PASS |
| Python compile | `python3 -m compileall -q ...`: PASS |
| Qwen enterprise guardrail | `scripts/check_qwen_enterprise_guardrails.py`: PASS |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | `0 / 1 / 27` PASS |
| Raw assistant append scan | only `authorized_emission.py:271` and `authorized_emission.py:327` PASS |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |

## 6. PR Body / Overclaim Review

PR body review found no approval claim for package build, browser/API UAT, deployment, strict enforcement, package readiness, release readiness, enterprise/product closure, V2 work, or merge.

The PR body still contains conservative stale wording such as `This draft PR` and older verification metadata through E-16 / earlier head SHA. E-28 did not edit the PR body. The stale wording is conservative and not a readiness overclaim, but QA/Owner may choose to refresh metadata in a separate approved PR-body update slice before merge.

## 7. Lexical / Keyword Authority Scan

A contextual scan across current source, tests, and governance reports found:

- Raw lexical/keyword/regex/synonym/punctuation/no-alarm authority mentions: `59`.
- Current positive authority candidates after context review: `0`.

The raw candidates are historical, negative, stop-condition, supersession, or prohibition statements. No current source/test/current evidence path was found claiming that lexical, keyword, regex, synonym, punctuation, no-alarm, or token logic may grant route authority.

The accepted authority model remains:

- IntentBoundaryContract is sole runtime authority.
- Classifier/proposer output is evidence only.
- Semantic-safe/model output cannot authorize.
- Lexical/token/no-alarm evidence cannot authorize.
- Visible context cannot authorize model reasoning.
- Report selector cannot authorize itself.
- Enterprise model output cannot authorize final answer.
- Final-answer authority cannot bypass V1-IB.
- Missing, invalid, stale, unsafe, mixed, ambiguous, unresolved, non-redaction-safe, or unproven V1-IB contracts fail closed.

## 8. Merge-Execution Boundary Assessment

Local verification and package-exclusion gates are green, but E-28 is not clean for unconditional merge execution because GitHub-side merge evidence is incomplete:

- One unresolved, non-outdated PR review thread remains.
- No GitHub status contexts, check runs, or workflow runs were available for the current head SHA.
- Branch protection / required check policy could not be verified from this environment without authentication.

Therefore this report requests QA/Owner decision before any E-29 merge execution slice.

If QA/Owner accepts the unresolved review/check status as waived or separately resolved, the next bounded slice may be:

- `V1-IB-E-29 explicit merge execution request`

If QA/Owner does not waive or resolve the GitHub-side issues, the next bounded slice should be one of:

- Review-thread resolution / response planning.
- Check/branch-protection verification with appropriate GitHub permissions.
- PR body metadata refresh, if QA wants current head metadata reflected before merge.

## 9. E-29 Stop Conditions

E-29 must stop if any of the following are true:

- PR head SHA changes from `ec2b59d151c9b4ee4cde2ab710754a86c86839d9` without explicit approval.
- Local/remote head mismatch appears.
- PR becomes Draft, closed, or merged before E-29.
- Worktree is dirty before merge execution.
- Package-exclusion gates fail.
- Rejected artifacts reappear.
- Lexical/keyword/regex/synonym/punctuation/no-alarm route authority regression appears.
- Any accepted local test group fails.
- Required GitHub checks fail or cannot be verified without Owner waiver.
- Required review/comment status fails or remains unresolved without Owner waiver.
- Merge would require package build, browser/API UAT, deployment, strict enforcement, readiness claim, enterprise/product closure, or V2 work.

## 10. Final Boundary Statement

E-28 created this report only. No merge, PR state change, staging, commit, push, package build, browser/API UAT, deployment, strict enforcement, readiness claim, enterprise/product closure, or V2 work occurred.
