# V1-R-E Synthetic Dataset And Environment Input Plan

Decision target: `v1_r_e_input_plan_ready_for_counterpart_qa_review`

## Scope

V1-R-E is a report-only planning slice. It defines the minimum safe environment, user, secret, dataset, artifact, screenshot, trace, custodian, and stop-condition inputs needed before browser UAT can be unblocked.

This report does not create a site, create a user, create or seed a dataset, run browser automation, capture screenshots, collect traces, edit source/test files, stage, commit, push, deploy, enable strict enforcement, or implement V2 work.

## Baseline

| Field | Value |
| --- | --- |
| Worktree | `/tmp/erpai_pr5_postmerge_verify` |
| Baseline HEAD | `a9f34e4` |
| Input blocker source | V1-R-D Browser UAT Execution Input Preflight |
| Question bank source | V1-R-A scenarios `V1RA-001` through `V1RA-066` |
| Proposed first execution scope | Smoke-10 only, after explicit approval |
| Execution authority | Not granted |

## Minimum Safe Inputs

| Input | Minimum acceptable definition | Evidence required before execution |
| --- | --- | --- |
| Non-production site | Controlled ERPNext/Frappe site that is explicitly not production | Site URL or stable site label, owner/QA attestation, and evidence it is non-production |
| QA user | Dedicated non-production QA user | Username, role list, and confirmation the user is not a production/operator account |
| Secret handling | External secret source or secure interactive handoff | Method description that stores no secret in repo, docs, logs, screenshots, or command history |
| Synthetic dataset | Approved synthetic records covering smoke-10 | Manifest path/name, record inventory, and owner/QA approval |
| Artifact output path | Safe path for redacted summaries/screenshots if approved | Path review showing it avoids excluded streams and does not store raw traces/secrets |
| Screenshot policy | Explicit allow/deny/redaction policy | Owner/QA decision before screenshots are captured |
| Visible-context/trace policy | Explicit allow/deny/redaction policy | Owner/QA decision before context/trace capture |
| Reviewer/custodian | Named QA/Owner reviewer and artifact custodian | Name/role and custody policy |
| Stop conditions | Approved stop rules | Owner/QA acceptance of stop conditions before execution |

## Non-Production Site Requirement

The browser UAT site must satisfy all requirements below before any execution request can proceed.

| Requirement | Acceptable evidence |
| --- | --- |
| Not production | Owner/QA attestation plus site label or URL that clearly identifies development, staging, test, or QA environment |
| ERPNext/Frappe site reachable | Future preflight may verify login page and route availability without submitting UAT prompts |
| AI Assistant route available | Owner/QA provides expected navigation path or URL |
| Synthetic data only | Site is loaded only with synthetic/QA-approved records for the UAT scenarios |
| No production credentials | QA user is non-production and dedicated to UAT |

If the site cannot be identified or attested as non-production, the browser UAT path remains blocked.

## QA User Requirement

Minimum QA user expectation:

| Field | Required value |
| --- | --- |
| Username | Owner/QA-approved dedicated user, preferably a name like `qa_v1_browser_uat_user` |
| Roles | Read-only or least-privilege roles sufficient to open AI Assistant and view approved synthetic ERP records |
| Data access | Synthetic/QA-approved records only |
| Write permission | Not required for V1 smoke UAT; avoid write roles unless owner/QA explicitly approve |
| Auditability | User should be identifiable as a test user in logs |

The QA user must not be created in V1-R-E. This plan only defines the requirement.

## Secret Handling Method

Approved future options:

| Method | Requirement |
| --- | --- |
| Secure interactive prompt | Secret entered at execution time; never stored |
| External secret manager | Runtime reads secret from approved external location; no repo storage |
| Temporary QA credential handoff | Owner/QA provides credential through secure channel; not captured in artifacts |

Forbidden:

- storing passwords in markdown,
- committing `.env` files,
- passing secrets in shell commands that may enter history,
- saving cookies/session tokens in repo,
- capturing secrets in screenshots or logs.

## Synthetic Dataset Manifest Design

Recommended manifest name:

`V1_BROWSER_UAT_SYNTHETIC_SET_001`

Recommended manifest format:

| Field | Purpose |
| --- | --- |
| `manifest_name` | Must equal approved manifest name |
| `approval_reference` | Owner/QA approval reference |
| `site_label` | Approved non-production site label |
| `company` | Synthetic company/context if required |
| `date_context` | Current month/fiscal year/prior month assumptions |
| `customers` | Synthetic customer records for AR/sales scenarios |
| `suppliers` | Synthetic supplier records for AP scenarios |
| `items` | Synthetic item/product records for sales/product scenarios |
| `sales_invoices` | Synthetic invoice IDs and detail fields |
| `purchase_invoices` | Synthetic AP invoice IDs if needed |
| `reports_available` | Expected governed reports available in the site |
| `scenario_mappings` | Scenario-to-record mapping for smoke-10 and later full-66 runs |

Manifest safety rules:

- No real customer/vendor/entity names.
- No production invoice IDs.
- No real monetary amounts if they can identify production data.
- Placeholder values like `SINV-0001` are not valid unless explicitly listed as synthetic.
- Missing mapping blocks the scenario as `uat_blocked_dataset`.

## Smoke-10 Dataset Requirements

Smoke-10 is the recommended first future execution scope after approval.

| Scenario ID | Purpose | Required synthetic records |
| --- | --- | --- |
| `V1RA-001` | AR/customer outstanding | At least two synthetic customers with outstanding balances and aging/due context |
| `V1RA-009` | AP/supplier payable | At least two synthetic suppliers with payable balances and due/overdue context |
| `V1RA-017` | P&L/profit summary | Synthetic P&L/report data for the selected company/date period |
| `V1RA-025` | Sales/customer performance | Synthetic sales summary by customer for selected period |
| `V1RA-033` | Invoice lookup/detail | One approved synthetic sales invoice ID and expected invoice detail |
| `V1RA-041` | Follow-up detail/explanation | Prior answer context from `V1RA-001` or another approved seeded list |
| `V1RA-049` | Vague business overview | Enough synthetic AR/AP/sales/P&L context to support a bounded overview or clarification |
| `V1RA-055` | Messy/mobile AR shorthand | Same AR dataset as `V1RA-001`, with expected shorthand interpretation |
| `V1RA-061` | Recommendation boundary | No extra record required; should validate refusal/bounded behavior using available factual evidence |
| `V1RA-064` | Write/action boundary | No write-capable setup required; should validate refusal/bounded behavior |

## Broader Full-66 Dataset Categories

Before full `V1RA-001` through `V1RA-066` execution, the manifest should cover:

| Category | Required synthetic coverage |
| --- | --- |
| AR/customer outstanding | Outstanding balances, overdue/aging, invoice detail, top customer examples |
| AP/supplier payable | Supplier balances, due/overdue invoices, supplier detail |
| P&L/profit summary | Monthly and fiscal-year P&L data with income/expense breakdown |
| Sales/product performance | Customer sales, item/product sales, quantity/value distinctions |
| Invoice lookup/detail | Sales invoice and purchase invoice records safe for lookup |
| Follow-up scenarios | Seeded prior-answer flows or deterministic setup sequence |
| Vague overview | Multi-area data or expected clarification behavior |
| Boundary scenarios | Policy/refusal expectations; no special records unless factual alternatives are offered |

## Artifact Output Policy

Artifact output path must:

- be outside source/test directories,
- avoid ERP UI paths,
- avoid seed/data paths,
- avoid temp/probe/cache paths unless a separately approved external QA scratch policy exists,
- avoid PrimeAxis paths,
- avoid generated scratch paths,
- avoid raw trace/redacted trace JSON paths unless separately approved,
- avoid site config, secret, and archive-content paths,
- store only approved redacted summaries or safe screenshots.

Recommended future artifact structure, if approved outside repo:

```text
<approved_external_qa_artifact_root>/
  v1_browser_uat/
    run_<date>_<id>/
      summary_redacted.md
      scenario_results_redacted.csv
      screenshots_redacted/
```

No artifact path is approved in V1-R-E.

## Screenshot Policy

Owner/QA must choose one before execution:

| Policy | Meaning |
| --- | --- |
| `screenshots_disabled` | Do not capture screenshots; text summary only |
| `screenshots_redacted_only` | Capture screenshots only after confirming synthetic data and redact before sharing |
| `screenshots_external_custody` | Store screenshots outside repo under QA/Owner custody |

Default until approved: `screenshots_disabled`.

## Visible-Context / Trace Policy

Owner/QA must choose one before execution:

| Policy | Meaning |
| --- | --- |
| `visible_context_disabled` | Do not capture visible context/trace evidence |
| `visible_context_text_redacted` | Capture only safe/redacted visible context text |
| `trace_external_custody_only` | Raw trace/context payloads remain external; repo gets summary only |

Default until approved: `visible_context_disabled`.

Live trace collection remains separate from browser UAT and is not approved by V1-R-E.

## Reviewer / Custodian

Minimum requirement:

| Role | Responsibility |
| --- | --- |
| Owner reviewer | Approves site, scenario scope, and risk acceptance |
| QA_Risk reviewer | Reviews safety boundaries and artifact policy |
| Artifact custodian | Controls any screenshots/logs/traces outside repo |
| Development Agent | Executes only after approval and reports results; does not own raw sensitive artifacts |

No reviewer/custodian is named yet, so execution remains blocked.

## Stop Conditions

Proposed stop conditions for owner/QA approval:

| Stop condition | Required action |
| --- | --- |
| Site is production or unclear | Stop; classify `uat_blocked_environment` |
| QA user is missing or wrong | Stop; classify `uat_blocked_environment` |
| Secret handling would expose credentials | Stop; classify `uat_blocked_environment` |
| Dataset manifest missing | Stop; classify mapped scenarios `uat_blocked_dataset` |
| Real customer/vendor/entity/document appears | Stop; quarantine artifact externally for owner/QA review |
| Screenshot would expose sensitive data | Do not capture or store screenshot |
| Trace/visible context exposes raw payload | Stop trace/context capture |
| Assistant gives unsafe advice/prediction/action | Mark scenario `uat_fail`; continue only if stop policy permits |
| Browser/app error prevents reliable results | Stop; classify remaining scenarios `uat_blocked_environment` |

## Current Readiness Decision

The input plan is ready for Counterpart/QA review, but execution remains blocked until owner/QA provide and approve the required inputs.

## Verification Results

| Check | Result |
| --- | --- |
| Guardrail | PASS |
| Durable helper presence | PASS: `/tmp/ec8b_verify.py` exists |
| Fake-Frappe `service.py` import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` only |
| Browser execution | Not run |
| Screenshots/traces | Not captured |
| Dataset creation/seeding | Not performed |
| Source/test edits | None |
| Staging | Not performed |

## V1-R-E Decision

`v1_r_e_input_plan_ready_for_counterpart_qa_review`
