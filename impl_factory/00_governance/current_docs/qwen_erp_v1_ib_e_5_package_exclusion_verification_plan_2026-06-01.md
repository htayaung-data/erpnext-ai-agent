# V1-IB-E-5 Package-Exclusion Verification Plan

Decision target:
`v1_ib_e_5_package_exclusion_verification_plan_ready_for_counterpart_review`

Date: 2026-06-01

## 1. Scope And Boundary

V1-IB-E-5 is a report-only planning slice. It defines concrete future package-exclusion verification gates for proving rejected, historical, unrelated, and unknown artifacts are absent from any future clean package/review branch or are explicitly quarantined/archived under QA-approved labels.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_5_package_exclusion_verification_plan_2026-06-01.md`

No source files were edited. No test files were edited. No package config changed. No old reports were edited. No rejected, historical, unrelated, or unknown artifact was deleted, moved, renamed, archived, truncated, or modified.

No staging, commit, push, branch creation, branch switching, package, browser/API UAT, deployment, strict enforcement, release readiness, enterprise/product closure, or V2 work occurred. No excluded artifact was reclassified as accepted evidence. No lexical, regex, synonym, keyword, phrase, punctuation, or no-alarm artifact was described as route authority evidence.

## 2. Accepted Prior Basis

Accepted basis for E-5:

- E-3 rejected/historical artifact exclusion plan is accepted after the E-3-A addendum.
- E-3-A fixed the V1-R inventory:
  - all V1-R reports: `59`
  - V1-R/Y reports: `31`
  - older non-Y V1-R reports: `28`
- E-4 classified root file `=` as:

```text
generated_local_artifact / do_not_package / delete_or_archive_later_only_after_QA_approval
```

- D-4-E-1 accepted-evidence manifest remains the artifact-classification basis.
- The current dirty worktree remains not package-ready.

E-5 does not implement exclusion or packaging. It defines the audit gates future clean package work must pass.

## 3. Future Package-Exclusion Verification Gates

Future clean package/review branch must prove:

| Gate | Required proof |
| --- | --- |
| Rejected structural classifier source absent | `intent_boundary_structural_classifier.py` absent from package runtime source or present only in QA-approved rejected archive outside package runtime |
| Rejected structural classifier tests absent | `test_v1_ib_structural_classifier.py` absent from accepted current package tests |
| Rejected structural B reports excluded/labeled | Rejected 2026-05-28 V1-IB-B structural reports absent from current release evidence or explicitly archived as rejected/historical |
| V1-R/Y reports excluded/labeled | All `31` V1-R/Y reports absent from current release evidence |
| Older non-Y V1-R reports excluded/labeled | All `28` older non-Y V1-R reports absent from current release evidence |
| Old lexical/user-intent tests excluded | Old direct `test_user_intent_boundary_*.py` tests absent from accepted current package tests unless rewritten and QA-accepted |
| Root file `=` absent | Root-level `=` absent from package tree and clean branch reapply set |
| Unrelated EC-10-G report excluded | EC-10-G report absent from current V1-IB release evidence unless QA explicitly reclassifies it |
| No lexical authority claims | No lexical/regex/synonym/no-alarm artifact described as route authority evidence |
| Accepted evidence manifest consistency | D-4-E-1 or successor manifest agrees with package contents and current release evidence labels |

## 4. Exact Future Verification Commands / Checks

These are future checks for an approved clean package/review branch. They are not package cleanup implementation and do not run package operations in E-5.

### Static Runtime Import Scan

Purpose:
Prove rejected structural classifier is not imported by package runtime.

Future command shape:

```bash
grep -R -n --include='*.py' --exclude='intent_boundary_structural_classifier.py' \
  'intent_boundary_structural_classifier' \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat
```

Expected result:
No output.

### Source Tree / Package Tree Absence Scan

Purpose:
Prove rejected source/test and unknown artifacts are absent from the clean package tree.

Future checks:

```bash
test ! -e impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py
test ! -e impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py
test ! -e ./=
```

If a QA-approved archive is used, checks must prove these files are outside runtime/package evidence paths and explicitly labeled rejected/historical.

### Accepted Evidence Manifest Consistency Scan

Purpose:
Prove package contents match accepted artifact classifications.

Future checks:

- enumerate package source/test/governance files
- compare against D-4-E-1 or successor accepted-evidence manifest
- fail if any `rejected_superseded`, `historical_superseded`, `unknown_needs_review`, or `unrelated` artifact appears as current evidence
- fail if accepted-current artifacts are missing without QA-approved explanation

### Current Evidence Report Family Scan

Purpose:
Prove old reports are not current release evidence.

Future checks:

```bash
find impl_factory/00_governance/current_docs -maxdepth 1 -type f \
  \( -name 'qwen_erp_v1_r_y*.md' -o -name 'qwen_erp_v1_r_[a-z]*.md' \)
```

Expected result:
No old V1-R reports in current release evidence path, or all such reports are in a QA-approved archive with manifest labels showing historical/superseded status.

### Test Suite Inclusion / Exclusion Scan

Purpose:
Prove current package tests do not rely on old lexical route-authority tests.

Future checks:

```bash
find impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests -maxdepth 1 -type f \
  \( -name 'test_user_intent_boundary_*.py' -o -name 'test_v1_ib_structural_classifier.py' \)
```

Expected result:
No output unless a later QA-approved slice rewrites/aligned those tests and explicitly accepts them.

### Root-Level Unknown Artifact Scan

Purpose:
Prove generated/unknown root artifacts are absent.

Future checks:

```bash
test ! -e ./=
find . -maxdepth 1 -type f -name '=' -print
```

Expected result:
No package root file named `=`.

### Standard Safety Gates

Future clean branch must also run:

```bash
git diff --check
git diff --cached --check
python3 scripts/check_qwen_enterprise_guardrails.py
```

And project-specific scans:

- fake-Frappe service import
- direct assistant inventory remains `0 / 1 / 27`
- raw assistant append scan only authorized sinks
- staged-file review
- clean git status review
- no raw business payloads, secrets, selected answers, rows, artifacts, rendered payloads, or grounded evidence in package traces/reports

### Optional Accepted-Artifact Checksum Manifest

Optional future output:

- SHA-256 checksums for accepted-current source/test/governance artifacts only
- no checksums required for rejected/historical artifacts unless QA approves an archive manifest
- checksum report must not include raw business payloads or secrets

## 5. Fail Conditions

Future package-exclusion verification must fail closed if any of these occur:

- Any rejected structural classifier runtime import is present.
- Rejected structural classifier source is included in package runtime.
- Rejected structural classifier test is included in accepted current package tests.
- Any rejected 2026-05-28 V1-IB-B structural report is labeled current release evidence.
- Any old V1-R report is marked current V1-IB release evidence.
- Any old lexical/user-intent test is used as current enterprise proof without rewrite/alignment and QA acceptance.
- Root file `=` is present in package output.
- Any unknown root artifact is present in package output.
- Any stale lexical/keyword/regex/synonym/no-alarm report is used as authority evidence.
- Any package-exclusion scan is missing, unverifiable, or not archived as verification evidence.
- Any package evidence claims route authority from classifier/proposer output, semantic-safe output, lexical evidence, report selector, visible context, final answer text, trace metadata, old V1-R artifacts, or rejected structural classifier artifacts.

## 6. Future Output Artifacts

Future package-readiness work should produce:

- package exclusion verification report
- accepted evidence manifest
- rejected/historical archive manifest, if QA approves an archive later
- clean package tree scan result
- static runtime import scan result
- current evidence report-family scan result
- test suite inclusion/exclusion scan result
- root unknown-artifact scan result
- optional checksum manifest for accepted artifacts only

Future reports must not include raw business payloads, secrets, credentials, private keys, cookies, selected answer text, ERP rows, report payloads, rendered payloads, artifacts, narratives, or grounded evidence.

## 7. Planning-Only Boundary

E-5 is planning only:

- No package branch was created.
- No exclusion was implemented.
- No cleanup was performed.
- No deletion, move, rename, archive, or truncation was performed.
- No package readiness was claimed.
- No release readiness was claimed.
- No browser/API UAT was run.

The current dirty worktree remains not package-ready.

## 8. Verification For E-5

Read-only stop-condition scan:

| Check | Result |
| --- | --- |
| Runtime dependency on rejected structural classifier | PASS: no `qwen_chat` runtime references found outside the rejected file itself |
| Evidence that old lexical artifact is used as route authority | Not found in E-5 report-only scan; future clean branch must run package-level verification |

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
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS |
| Staged files count | PASS: `0` |
| Dirty worktree count | PASS: `159` after adding E-5 report |

If a future report or scan discovers an active runtime dependency on rejected structural classifier artifacts, or evidence that an old lexical artifact is still used as route authority, do not fix opportunistically. Document the blocker and recommend a narrow follow-up slice.

Do not claim clean branch creation, cleanup, exclusion implementation, package readiness, release readiness, UAT readiness, E implementation, enterprise/product closure, or V2 work from E-5.
