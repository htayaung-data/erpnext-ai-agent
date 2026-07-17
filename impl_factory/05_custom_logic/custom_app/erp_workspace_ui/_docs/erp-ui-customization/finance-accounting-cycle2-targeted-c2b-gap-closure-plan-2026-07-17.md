# Finance & Accounting Cycle 2 Targeted C2B Gap-Closure Plan

**Main Control authority:** Main Control v2

**Parent implementation plan:** [Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md)

**Gap evidence authority:** [Finance & Accounting Cycle 2 C2B2-C2B6 Installed-Source Semantic Proof and Stop Receipt](finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md)

**Installed-source authority:** [Finance & Accounting Cycle 2 C2B1 Exact Installed-Source Fingerprint Receipt](finance-accounting-cycle2-c2b1-exact-installed-source-fingerprint-receipt-2026-07-17.md)

**Owner planning gate received:** `finance_cycle2_gl_tb_targeted_c2b_gap_closure_plan_authorized`

**Decision:** `targeted_c2b_gap_closure_plan_ready_for_owner_execution_gate`

**State:** planning only; C2B2, C2B4 and C2B6 remain stopped; C2B7 and runtime remain unapproved

## 1. Purpose and bounded outcome

This document is the canonical execution plan for resolving only the evidence-backed gaps that stopped C2B2, C2B4 and C2B6. It does not reopen the complete Finance roadmap, redesign C2B3 or C2B5, select an adapter, implement a Finance service, patch ERPNext, or start C2B7.

The intended outcome of a later, separately authorized proof is one of two explicit decisions:

1. `targeted_c2b_gap_closure_pass` — the remaining C2B2/C2B4/C2B6 requirements close for the bounded read-only GL / Trial Balance posture, allowing Main Control to propose C2B7; or
2. `stopped_for_targeted_c2b_gap` — one or more accounting, permission, consistency, performance or provenance requirements remain unresolved.

No weaker partial result may be described as C2B closure.

## 2. Fixed authority and non-goals

The following remain fixed:

- Source repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`.
- Branch: `feature/erpnext-ui-design`.
- Planning baseline `HEAD` and upstream: `aef907a530d825278d070c47237aa3041faced29`, ahead/behind `0/0`.
- The C2B1 selected-source authority remains the exact 69-file manifest under canonical digest `063f716c4138d6bf1f69ecf9e71b4f1bd9c0e5cb4118a5841aa2b5cc6de9d40c`.
- ERPNext v16.4.1 official commit: `d74a649016d8bb12ee3c5a24361171cebe860bfc`.
- Frappe v16.5.0 official commit: `4dfcc56090eb3101d18ddb03750391511f163fcf`.
- Immutable installed image identity remains `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` unless a later gate proves otherwise.
- Finance Cycle 1 remains closed only for its accepted aggregate read-only posture.
- C2B3 remains a bounded algorithm-semantics close; native Trial Balance/General Ledger reuse remains rejected.
- C2B5 remains bounded to company base currency, company-default Finance Book plus blank/NULL entries, and no dimension slice.
- Sales, Procurement, Warehouse, Finance Cycle 1, Shared UI, routing, registries, governance manifests, AI Assistant and the live deployment tree remain protected.

This plan does not authorize:

- reading any new installed source file;
- obtaining site configuration, effective roles, User Permission rows, active dimensions or operational accounting data;
- building or starting a disposable test environment;
- running ERPNext/Frappe tests or reports;
- changing the installed image, ERPNext, Frappe, custom apps, runtime code, roles, permissions, metadata or settings;
- staging, commit, push, live alignment, restart, cache clear, migration, protected gates or accounting execution;
- C2B7, C2C, Finance-to-AI access or any public payload.

## 3. Exact stopped gaps and closure objectives

| Gap | Current evidence | Targeted closure objective |
| --- | --- | --- |
| C2B2 cancellation freeze control | `make_reverse_gl_entries` supplies `adv_adj` where `check_freezing_date` requires `company`; no selected test covers the call. | Prove an equivalent prior control, confirm the defect and isolate it outside read-only reporting, or stop for separately approved remediation. |
| C2B2 lifecycle coverage | Stored-row cancellation behavior is mapped, but end-to-end behavioral evidence is absent. | Prove immutable/non-immutable, partial-cancel, frozen-date, lineage and currency-swap outcomes using synthetic fixtures. |
| C2B4 PCV state | Native Trial Balance selects a submitted prior PCV without requiring processing status Completed. | Prove exact legacy/queued transitions and permit cache use only for one unique submitted Completed PCV. |
| C2B4 ACB integrity | Native consumption does not prove uniqueness, completeness, retry safety or cache-to-GL parity. | Establish a normalized key oracle, expected/actual key equality, exact monetary parity and fail-closed behavior. |
| C2B4 fiscal carry-forward | Prior-year P&L, opening entries, mid-year boundaries and later postings remain conditional. | Prove deterministic two-year carry-forward and strict date rejection for each accepted source mode. |
| C2B5 Finance Book parity | Opening applies the book filter conditionally while movement applies it unconditionally. | Prove opening and movement select exactly the same company-default-plus-blank/NULL cohort. |
| C2B6 permission equivalence | Native opening, movement, Account, PCV and dimension reads do not share one permission path. | Prove one complete authorized chart or return unavailable; no visible-subset balance. |
| C2B6 identity suppression | Native reports contain account, party and voucher identities. | Prove an aggregate-only internal result and recursively reject identity canaries from data, errors and logs. |
| C2B6 consistency | No report-level snapshot or reliable change token is proven. | Prove one primary-database consistent snapshot or stop; no hybrid before/after state. |
| C2B6 workload | No capability-specific caps or timeout behavior exists. | Derive exact caps from synthetic benchmark evidence and deny before truncation or partial output. |

## 4. Four distinct future evidence boundaries

The proof must keep these authorities separate.

### 4.1 Official path inventory

The candidate path names in section 5 were verified for existence only in the pinned official GitHub commit trees. Their contents were not read during this planning task. Official path existence does not prove installed presence, byte equality or semantics.

### 4.2 Installed fingerprint extension

After a separate Owner gate, each exact approved path must be checked as present, regular, non-symlink, readable and contained in the accepted app root. Its raw-byte SHA-256 must match the official pinned object and an immediate second installed collection. Any missing file, mismatch, unstable hash or unexpected file type stops the gate.

### 4.3 Source-semantic reading

Only after the fingerprint receipt is accepted may the exact approved files be read. No recursive dependency following is allowed. A newly material dependency is named and stops the affected task pending a narrow allowlist amendment.

### 4.4 Disposable synthetic behavior

Only after another separate Owner gate may the immutable image run against a disposable synthetic site. This is black-box installed-product behavior evidence, not permission to inspect every transitive source file. Unexpected behavior may be recorded, but diagnosing it through new source requires a new exact fingerprint/read gate.

## 5. Proposed exact source/test fingerprint extension

All paths below are relative to their accepted ERPNext or Frappe app roots. They are candidate paths, not yet approved for installed access.

### 5.1 ERPNext mandatory candidate paths

Official path existence was verified at ERPNext commit `d74a649016d8bb12ee3c5a24361171cebe860bfc`:

1. `erpnext/accounts/doctype/gl_entry/test_gl_entry.py`
2. `erpnext/accounts/doctype/process_period_closing_voucher_detail/process_period_closing_voucher_detail.py`
3. `erpnext/accounts/doctype/process_period_closing_voucher_detail/process_period_closing_voucher_detail.json`
4. `erpnext/controllers/accounts_controller.py`
5. `erpnext/hooks.py`
6. `erpnext/accounts/doctype/period_closing_voucher/test_period_closing_voucher.py`
7. `erpnext/accounts/doctype/process_period_closing_voucher/test_process_period_closing_voucher.py`
8. `erpnext/accounts/doctype/account_closing_balance/test_account_closing_balance.py`
9. `erpnext/accounts/report/trial_balance/test_trial_balance.py`
10. `erpnext/accounts/doctype/fiscal_year/test_fiscal_year.py`
11. `erpnext/accounts/doctype/accounting_period/test_accounting_period.py`
12. `erpnext/accounts/doctype/finance_book/test_finance_book.py`

These 12 paths are the maximum initial ERPNext extension. Existing fingerprinted controllers, reports, metadata and utilities remain governed by the original 69-file receipt.

### 5.2 Frappe mandatory candidate paths

Official path existence was verified at Frappe commit `4dfcc56090eb3101d18ddb03750391511f163fcf`:

1. `frappe/app.py`
2. `frappe/utils/scheduler.py`
3. `frappe/hooks.py`
4. `frappe/share.py`
5. `frappe/utils/nestedset.py`
6. `frappe/tests/test_permissions.py`
7. `frappe/tests/test_db.py`
8. `frappe/tests/test_db_query.py`
9. `frappe/tests/test_query_report.py`
10. `frappe/tests/test_reportview.py`
11. `frappe/core/doctype/user_permission/test_user_permission.py`
12. `frappe/core/doctype/custom_docperm/custom_docperm.py`
13. `frappe/core/doctype/custom_docperm/custom_docperm.json`
14. `frappe/core/doctype/custom_docperm/test_custom_docperm.py`
15. `frappe/core/doctype/role_permission_for_page_and_report/role_permission_for_page_and_report.py`
16. `frappe/core/doctype/role_permission_for_page_and_report/role_permission_for_page_and_report.json`
17. `frappe/core/doctype/role_permission_for_page_and_report/test_role_permission_for_page_and_report.py`

One and only one database-dialect path may be added after a sanitized `db_type` attestation:

- MariaDB branch: `frappe/database/mariadb/database.py`; or
- PostgreSQL branch: `frappe/database/postgres/database.py`.

The mutually exclusive dialect path and the 17 fixed paths make the initial Frappe extension 18 files.

### 5.3 Exact conditional stop-and-amend candidates

These paths exist in the official pinned trees but are not in the initial extension. They may be proposed only if the mandatory evidence proves they are material:

- request/response behavior: `frappe/handler.py`, `frappe/utils/response.py`;
- metadata customization: `frappe/custom/doctype/custom_field/custom_field.py`, `.json`, and `test_custom_field.py`;
- Property Setter behavior: `frappe/custom/doctype/property_setter/property_setter.py`, `.json`, and `test_property_setter.py`;
- role-profile behavior: `frappe/core/doctype/role_profile/role_profile.py`, `.json`, and `test_role_profile.py`;
- role child rows: `frappe/core/doctype/has_role/has_role.py` and `.json`;
- reporting currency: `erpnext/setup/utils.py`;
- party admission: `erpnext/accounts/party.py`.

No conditional path may be read automatically. Voucher-controller, budget-controller or other posting-admission expansion is outside this targeted plan unless a later Owner decision requires full execution-lifecycle assurance rather than read-only reporting.

### 5.4 Active-app hook attestation

Effective permission hooks cannot be inferred from Frappe and ERPNext alone. Before source-semantic reading, a separately approved sanitized attestation may return only:

- database dialect identifier;
- installed/active app identifiers;
- exact hook module paths derived from the immutable build;
- source hashes for those hook modules.

It must not return site paths, database names, credentials, environment values, configuration contents, roles, users or operational data. Main Control must then issue an exact hook-file allowlist amendment and obtain approval before reading any additional hook source. If exact active hooks cannot be enumerated safely, C2B6 remains stopped.

## 6. Disposable synthetic evidence environment

Future synthetic execution requires its own Owner approval and one environment owner.

### 6.1 Isolation requirements

- Build only from the accepted immutable image ID; record container and image identities before and after.
- Use a new disposable database, site, Redis/cache namespace and volumes with no live mounts or copied live configuration.
- Disable outbound network, email, notifications, integrations and external workers; any required background worker must be isolated to the synthetic namespace.
- Use only deterministic synthetic companies, users, accounts, dimensions, vouchers and amounts.
- Do not connect to `/home/deploy/erp-projects/erpai_project1`, its containers, databases, caches or files.
- Retain only sanitized fixture manifests, hashes, transition traces, query plans, timings and expected/actual comparisons.
- Teardown belongs to the same future environment approval; no cleanup action is authorized by this plan.

Frappe's official unit-testing guidance describes transaction rollback for `FrappeTestCase`, but PCV jobs, explicit commits, workers and failure injection still require full environment isolation rather than reliance on rollback alone.

### 6.2 Future Finance-owned proof harness lock

If a committed synthetic harness is necessary, the only initial candidate path is:

`impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_gl_trial_balance_source_proof.py`

Creating or editing that file is a later implementation/test-code gate. It is not authorized here. Any second test file requires an allowlist amendment.

## 7. Synthetic accounting and authority fixtures

### 7.1 Core complete-chart fixture

Use Company A and Company B with disjoint charts.

Company A:

- opening: Cash debit `100.00`; Equity credit `100.00`;
- movement 1: Receivable debit `60.00`; Revenue credit `60.00`;
- movement 2: Cash debit `40.00`; Receivable credit `40.00`;
- expected closing: Cash debit `140.00`, Receivable debit `20.00`, Revenue credit `60.00`, Equity credit `100.00`;
- expected closing debit and credit totals: `160.00` and `160.00`.

Company B contains balanced `999.00` canaries that must never affect Company A. Cancelled `777.00` and out-of-period `888.00` canaries must be excluded. Every Company A account, including zero-balance accounts and required parents, must appear exactly once in the internal completeness manifest.

### 7.2 Cancellation matrix

| Fixture | Required evidence |
| --- | --- |
| Non-immutable cancellation | Originals and swapped cancellation rows become report-ineligible exactly as proven. |
| Immutable cancellation | Originals and current-dated swapped reversals remain active and net correctly. |
| Frozen date, unauthorized user | Cancellation stops before any mutation. |
| Frozen date, authorized role | Behavior matches the exact Company freeze policy. |
| `adv_adj=True` | Bypass occurs only when explicitly intended and evidenced. |
| Partial cancellation | Only exact voucher-detail lineage is affected. |

Also assert debit/credit swapping in base, account and transaction currencies, voucher lineage preservation, new row identity and zero-row behavior.

### 7.3 PCV/ACB/fiscal matrix

- Two consecutive fiscal years, including a short fiscal year and the first day of the next year.
- Asset, liability, equity, income, expense and closing accounts.
- Opening entries, mid-year and year-end PCVs, multiple PCVs, cancelled PCVs and later postings.
- Legacy and queued processing with Queued, Running, Paused, Completed, Failed and Cancelled outcomes.
- Failure injection before, during and after GL/ACB work, followed by retry/resume.
- Default, alternate, blank and NULL Finance Book entries.
- Parent/child Cost Centers, Projects, and tree/non-tree dimensions for internal grouping proof only.

The normalized ACB key is:

```text
company + account + account_currency + cost_center + project + finance_book
+ is_period_closing_voucher_entry + every active accounting dimension
```

Pass requires exactly one ACB row for every expected normalized key and PCV, no extra key, exact Decimal equality with the GL oracle per key and globally, exact P&L/closing-account reconciliation, and no apparently valid partial cache after failure or retry.

### 7.4 Permission and leakage matrix

The positive user is synthetic `fin_mgr_a`: Accounts Manager, Company A authority, complete chart, and no Account/dimension restriction, share, custom permission condition or privileged bypass role.

Mandatory denial cases:

| Context | Required result |
| --- | --- |
| Guest/anonymous | Deny before accounting query. |
| Accounts User, Auditor, Sales, Procurement or Warehouse role | Deny despite any native-report role. |
| Administrator or mixed privileged role | Deny pending explicit Owner policy. |
| Missing, ambiguous or unauthorized company | Deny with no fallback. |
| Account User Permission or descendant restriction | Capability unavailable; never partial chart. |
| Cost Center, Project or custom-dimension restriction | Deny the initial no-dimension capability. |
| Custom DocPerm removes required authority | Deny. |
| Required field elevated, hidden or masked | Deny. |
| Share-only access | Deny. |
| Relevant permission hook/query condition | Deny until exact equivalence is proven. |
| Invalid dates, dimension filter, ambiguous book, alternate currency or multi-company request | Reject. |
| Malformed chart, imbalance, cache/GL disagreement, timeout, snapshot conflict or cap excess | Fail closed with no figures. |

Identity canaries populate account names/numbers, party, party name, voucher number, remarks, owner, modified-by, email, phone and address. None may occur in the public-candidate payload, error text or captured synthetic logger.

## 8. Source-mode decision branches

### 8.1 Cancellation freeze finding

1. **Equivalent prior control proven:** close the mismatch finding with exact call-path and behavior evidence.
2. **Defect confirmed, read-only deferral considered:** the Owner may accept it only as a High execution prerequisite outside the reporting boundary if the future service cannot call posting, cancellation, close/reopen or any mutation and makes no frozen-period-control, audit or certification claim.
3. **Remediation required:** any ERPNext call correction, upgrade or image rebuild is a separate runtime/release capability with separate ownership, tests and live gates. It cannot be patched incidentally in GL/TB work.
4. **Ambiguous:** C2B2 remains stopped.

An accepted scope exclusion may remove the defect from the read-only adapter's direct attack surface, but the risk remains carried forward and blocks every future accounting-execution or audit-control claim.

### 8.2 Opening/closing source mode

| Mode | Rule |
| --- | --- |
| `cache_verified` | ACB may be used only after unique Completed PCV, full key completeness, retry safety, exact GL parity and permission/snapshot equivalence all pass. |
| `gl_reconstructed` | Opening and movement derive directly from GL under frozen fiscal, PCV, opening, cancellation, Finance Book and dimension predicates. It must pass independently of ACB. |
| `dual_compare` | Diagnostic-only comparison of the two modes; never a runtime fallback policy. |

There is no silent fallback. A request configured for one mode returns unavailable when that mode fails.

## 9. Dependency-based mini-phase sequence

| Gate | Work | Exit |
| --- | --- | --- |
| C2BG0 plan acceptance | This document and README only. | Owner accepts or rejects the plan; no evidence access follows automatically. |
| C2BG1 identity and fingerprint | Obtain the separately approved sanitized dialect/app attestation, freeze exact paths, verify installed/official hashes twice. | Exact expanded fingerprint receipt or stop. |
| C2BG2 cancellation/lifecycle semantics | Read only approved fingerprinted source/tests; run later approved synthetic lifecycle fixtures. | Equivalent control, accepted reporting-only deferral, or stop/remediation decision. |
| C2BG3 PCV/ACB/fiscal/book semantics | Prove state machine, ACB key integrity, GL parity, carry-forward and Finance Book cohort equality. | At least one exact source mode survives or stop. |
| C2BG4 permission and leakage | Prove complete-chart authority, identical opening/movement scope, denial order and identity suppression. | `C2B6_PERMISSION_PASS` or stop. |
| C2BG5 snapshot and workload | Prove one primary-database snapshot, concurrency behavior, query plans and exact caps. | `C2B6_CONSISTENCY_CAP_PASS` or stop. |
| C2BG6 one-pass review and closure | Accounting, security, database/runtime and release reviewers inspect the frozen evidence once; Main Control synthesizes. | `targeted_c2b_gap_closure_pass` or `stopped_for_targeted_c2b_gap`. |

After C2BG1, static C2BG2 and C2BG3 source analysis may proceed in parallel because both are read-only and have separate evidence owners. Synthetic execution uses one environment owner and a frozen fixture generation. C2BG4 follows the C2BG3 source-mode decision; C2BG5 follows the permission/source-scope freeze; C2BG6 is sequential. Remediation code, if selected, is never parallel with proof and requires a new plan.

## 10. Snapshot and workload proof

Pass requires one explicit primary-database read-only consistent snapshot covering effective authority checks, Account chart, opening source, movement source, parent accumulation and balance validation.

Concurrency fixtures pause the reader between chart/opening/movement reads while a second synthetic transaction commits, separately:

- one balanced GL pair;
- one Account-tree change;
- one PCV/ACB change.

The result must represent the complete before-state or complete after-state, never a hybrid. Unknown isolation, read-replica switching, heuristic `count/max(modified)` tokens or mixed transactions are stop conditions. If no reliable mutation version exists, caching is disabled and snapshot-only consistency is required.

C2BG5 must derive and version these constants from synthetic benchmark evidence:

- `MAX_ACCOUNTS`
- `MAX_PERIOD_DAYS`
- `MAX_OUTPUT_ROWS`
- `MAX_RESPONSE_BYTES`
- `STATEMENT_TIMEOUT_MS`
- `REQUEST_TIMEOUT_MS`
- `MAX_RETRIES`
- `MAX_ACTIVE_DIMENSIONS = 0`

Each numeric boundary requires limit-pass, limit-plus-one-deny, timeout-without-partial-output and response-size-without-truncation evidence. Account caps apply before ledger aggregation. Query plans must not load voucher or identity rows into Python. Numeric values are not invented during planning.

## 11. Stop conditions

Stop the affected gate immediately if:

- an approved path is absent, mismatched, unstable or outside its app root;
- a material source dependency falls outside the exact allowlist;
- the database dialect or active hook set cannot be safely attested;
- the cancellation freeze mismatch has no equivalent control and no accepted read-only scope disposition;
- a non-Completed or ambiguous PCV can qualify for cache use;
- ACB retry/rerun can duplicate, omit or add normalized keys;
- cache and GL differ by any exact key or amount;
- fiscal carry-forward or Finance Book cohort equality is nondeterministic;
- opening and movement do not share one complete authorized chart;
- any account/dimension restriction would create a visible subset;
- any identity canary enters data, errors or evidence logs;
- a concurrent mutation produces a hybrid result;
- a query plan, timeout or cap can return partial/truncated output;
- synthetic isolation cannot be proven;
- any live or operational source is touched;
- any evidence-backed Blocker or in-scope High remains after the one-pass review.

## 12. Ownership locks and protection gates

| Surface | Owner/lock |
| --- | --- |
| Scope, path manifest, phase authority and final adjudication | Main Control v2. |
| Cancellation and accounting fixture equations | Accounting/source specialist. |
| PCV/ACB/fiscal/book oracle | Accounting/closing specialist. |
| Effective permission and identity canaries | Security specialist. |
| Isolation, concurrency, query plans and caps | Database/runtime specialist. |
| Disposable environment and synthetic fixture state | One environment owner; no parallel writers. |
| Future Finance proof harness | One implementation/test owner under a separate file allowlist. |
| ERPNext/Frappe remediation | Locked; requires separate Owner scope, image/release ownership and rollback plan. |
| Finance runtime service/page/tests | Locked until C2C/C2D approval. |
| Shared UI, routing, registries and governance manifests | No-touch; no trigger from source proof. |
| Sales, Procurement and Warehouse | Protected no-touch. |
| AI Assistant and Finance-to-AI | Protected no-access/no-authority. |
| Live deployment tree and live environment | Prohibited. |

Source tests and synthetic fixtures are not authenticated live acceptance. Any later Shared UI, route, registry, governance or live change retains its separate impact analysis, exact allowlist, regression and Owner approval gates.

## 13. One-pass review model

The future closure review is bounded to one evidence pass:

- accounting: cancellation, fiscal, PCV/ACB, book and Decimal invariants;
- security: complete-chart authority, denial order, identity leakage and error containment;
- database/runtime: snapshot, concurrency, query plans and caps;
- release/governance: image/source provenance, exact scope and no-live containment.

Blocker or High findings require exact source, synthetic behavior or authoritative product evidence. Main Control accepts, rejects or defers each once and stops if an in-scope Blocker/High remains. No repeated open-ended review loop is authorized.

## 14. Sequential Owner gates

This planning acceptance does not authorize the gates below.

1. **Next gate — fingerprint only:** `finance_cycle2_gl_tb_targeted_gap_source_fingerprint_authorized`
   - permits the sanitized dialect/app attestation and exact installed hash checks only;
   - does not permit semantic source reading or test execution.
2. **Semantic read gate:** `finance_cycle2_gl_tb_targeted_gap_semantic_read_authorized`
   - permits reading only the accepted fingerprinted paths;
   - does not permit a site, database or behavior execution.
3. **Synthetic execution gate:** `finance_cycle2_gl_tb_targeted_gap_synthetic_execution_authorized`
   - permits the exact disposable environment, fixture/harness allowlist and evidence commands accepted after semantic reading;
   - does not permit live access, remediation or C2B7.
4. **Gap-closure review gate:** `finance_cycle2_gl_tb_targeted_gap_closure_review_authorized`
   - permits one frozen-evidence review and Main Control synthesis only.
5. **C2B7 proposal gate:** available only after `targeted_c2b_gap_closure_pass`; it requires a new explicit Owner decision.

The Owner will also need to adjudicate the cancellation risk after C2BG2: accept a reporting-only scope exclusion, require separate remediation, or keep C2B2 stopped. Numeric workload caps and the surviving opening/closing source mode require explicit acceptance before any C2B7 proposal.

## 15. Authoritative primary references

- [ERPNext pinned official source tree](https://github.com/frappe/erpnext/tree/d74a649016d8bb12ee3c5a24361171cebe860bfc)
- [Frappe pinned official source tree](https://github.com/frappe/frappe/tree/4dfcc56090eb3101d18ddb03750391511f163fcf)
- [Frappe Testing](https://docs.frappe.io/framework/user/en/testing)
- [Frappe Unit Testing](https://docs.frappe.io/framework/user/en/guides/automated-testing/unit-testing)
- [Frappe Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions)
- [Frappe Database API](https://docs.frappe.io/framework/user/en/api/database)

Installed behavior and accepted synthetic evidence remain authoritative over general documentation for this pinned-version proof.

## 16. Documentation candidate and exclusions

The exact future documentation staging candidate becomes:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-targeted-c2b-gap-closure-plan-2026-07-17.md`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

The four unrelated exclusions remain outside the candidate and must remain untouched and unstaged:

| Path | Required status and SHA-256 |
| --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged; `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked; `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked; `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

No staging, commit, push, live alignment, protected gate or runtime action is implied.
