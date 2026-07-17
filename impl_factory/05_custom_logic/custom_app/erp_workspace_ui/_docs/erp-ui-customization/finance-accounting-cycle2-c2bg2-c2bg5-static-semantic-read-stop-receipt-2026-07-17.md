# Finance & Accounting Cycle 2 C2BG2-C2BG5 Static Semantic Read and Stop Receipt

**Date:** 2026-07-17
**Authority:** Main Control v2
**Parent plan:** [Finance & Accounting Cycle 2 Targeted C2B Gap-Closure Plan](finance-accounting-cycle2-targeted-c2b-gap-closure-plan-2026-07-17.md)
**Fingerprint authority:** [Finance & Accounting Cycle 2 C2BG1 Targeted Gap Source Fingerprint Receipt](finance-accounting-cycle2-c2bg1-targeted-gap-source-fingerprint-receipt-2026-07-17.md)
**Prior gap record:** [Finance & Accounting Cycle 2 C2B2-C2B6 Installed-Source Semantic Proof and Stop Receipt](finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md)
**Owner gate:** `finance_cycle2_gl_tb_targeted_gap_semantic_read_authorized`
**Decision:** `c2bg2_c2bg5_static_semantic_read_stopped_for_synthetic_and_dependency_evidence`

## 1. Executive receipt

The Owner-approved semantic pass read exactly the frozen 34 installed files: 12 ERPNext lifecycle/test files, 18 Frappe permission/query/database files, and four active-app hook files. No imported or dotted target, test helper, voucher controller, external library or other dependency was followed.

The static read narrows the architecture materially:

- a custom aggregate-only `gl_reconstructed` mode remains the sole viable source direction;
- native General Ledger, native Trial Balance, Query Report passthrough and native tree-helper reuse remain rejected;
- `cache_verified` Account Closing Balance mode remains stopped;
- the prior cancellation freeze-call High remains unresolved and immutable-ledger behavior still lacks selected test proof;
- effective complete-chart authority, a primary consistent snapshot and workload caps require synthetic evidence;
- one active global CORS callback creates a High dependency before any Finance HTTP endpoint can be approved;
- no active hook directly grants Finance-to-AI access or directly overrides GL Entry/Trial Balance permissions.

This is a static stop receipt. It is not `targeted_c2b_gap_closure_pass`, does not open synthetic execution, and does not start C2B7 or runtime implementation.

## 2. Gate posture

| Area | Static decision | Meaning |
| --- | --- | --- |
| C2BG2 cancellation/lifecycle | `stopped_for_freeze_and_immutable_lifecycle_evidence_gap` | No equivalent company-freeze cancellation control was found; immutable/non-immutable behavior lacks selected test confirmation. |
| C2BG3 fiscal/PCV/ACB/book | `gl_reconstructed_source_mode_survives_static_read` | Strict company/date/base-currency raw GL remains viable; ACB/process/default-book authority does not close. |
| C2BG4 permission/leakage | `static_mechanisms_mapped_synthetic_authority_required` | Denial order is frozen, but effective permissions, masks, shares, hooks and complete-chart authority require synthetic proof. |
| C2BG5 snapshot/workload | `stopped_for_primary_snapshot_and_caps_synthetic_proof` | Source exposes read-only/replica and timeout mechanisms, but no capability-level snapshot or caps are proven. |
| C2BG6 one-pass closure | Not started | It follows frozen synthetic evidence and separate Owner approval. |

## 3. Exact scope and integrity

| Item | Verified value |
| --- | --- |
| Source repository | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Branch | `feature/erpnext-ui-design` |
| Local `HEAD` / upstream | `aef907a530d825278d070c47237aa3041faced29` |
| Ahead/behind | `0/0` |
| Git index | Empty before and after |
| Backend container | `d7835253b02c0176fb49d84672037c8566d6ac7d29f6b92b4e3baa7c9df20813` |
| Immutable image | `sha256:4c8b6fb188d81f5a355008730a1122658af88799ec759029c2dbd297dfc8e257` |
| Active-site dialect | `mariadb` |
| Semantic-read rows | 34 unique path/hash keys |
| Semantic-read allowlist SHA-256 | `5c16ba40833ac0163ed2b3b083f9db2f28e26b7e66d05730f3366b81894cca82` |
| ERPNext pre/post result | 12/12 exact |
| Frappe pre/post result | 18/18 exact |
| Active hook pre/post result | 4/4 exact |

Every file remained regular, readable, non-symlink and canonically contained beneath its approved app root. Pre-read and post-read hashes matched C2BG1. The accepted original 69-file receipt was referenced for already-governed semantics but those product files were not re-read in this gate.

## 4. C2BG2 cancellation and lifecycle

### 4.1 Freeze control remains unresolved

The newly read sources contain no equivalent control that closes the previously proven `make_reverse_gl_entries` freeze-call argument mismatch:

- `erpnext/controllers/accounts_controller.py:372-374`: `before_cancel()` calls only e-invoice validation;
- `erpnext/controllers/accounts_controller.py:1955-1983`: `on_cancel()` handles bank links, generated journals and payment unlinking, with no company accounting-freeze check;
- `erpnext/hooks.py:315-345`: Accounting Period protection is registered for validation, not as an explicit cancellation hook;
- `erpnext/accounts/doctype/accounting_period/test_accounting_period.py:33-91`: tests save/submit denial and exempt roles, not cancellation;
- `erpnext/accounts/doctype/gl_entry/test_gl_entry.py:13-142`: no cancellation-freeze case.

**Accepted finding:** High. The prior exact caller/signature mismatch remains unmitigated by the approved extension. No runtime defect beyond that proven call path is inferred, but no accounting-execution or frozen-period-control claim may rely on cancellation.

### 4.2 Immutable-ledger posture

- None of the 12 ERPNext extension files tests an immutable-ledger branch.
- `test_period_closing_voucher.py:15-18` forces the legacy PCV controller.
- Its cancellation assertion at `:128-136` is not parameterized for immutable mode.
- `test_process_period_closing_voucher.py:14-20` contains no substantive test.

The earlier mutable/immutable source trace remains the bounded semantic narrative. Behavior confirmation requires synthetic evidence or an exact later source amendment.

### 4.3 Owner decision branch

The parent plan permits two controlled outcomes:

1. accept the cancellation High as a reporting-only execution prerequisite outside a service that exposes no mutation, close/reopen, audit certification or freeze-control claim; or
2. require separate remediation or additional lifecycle proof before continuing.

Main Control does not infer this business-risk decision.

## 5. C2BG3 fiscal, PCV, ACB and Finance Book semantics

### 5.1 Process PCV state evidence

`process_period_closing_voucher_detail.py:17-23` and its JSON `:13-41` prove detail statuses `Queued`, `Running`, `Paused`, `Completed` and `Cancelled`, plus processing date, report type and serialized closing balance.

The selected detail controller contains no state logic, and its schema has no Failed status, error field, attempt counter or retry provenance. This does not prove that the overall process lacks failure handling; the process controller is already governed by the original 69-file receipt and requires behavioral evidence for pause/resume, failure rollback, retry and idempotency.

### 5.2 ACB integrity

Accepted bounded evidence from `test_period_closing_voucher.py`:

- lines `215-310` preserve cost-center cohorts across consecutive PCVs;
- lines `312-328` reject pre-closing repost valuation and accept current-dated reposting.

Still unproved:

- normalized blank/NULL dimension keys;
- composite uniqueness and duplicate prevention;
- retry replacement and partial-cache cleanup;
- complete key coverage;
- exact cache-to-GL parity;
- queued-process equivalence.

`test_account_closing_balance.py:8-9` contains no substantive test. `cache_verified` remains stopped.

### 5.3 Fiscal boundaries and carry-forward

Static source supports a strict raw-GL mode:

- `test_fiscal_year.py:13-26` rejects an excessive fiscal-year span;
- lines `28-47` allow global and overlapping company-specific fiscal years;
- `accounts_controller.py:747-762` validates document dates against fiscal year;
- `accounts_controller.py:1295-1307` resolves fiscal year by posting date and company and rejects ambiguity;
- `test_period_closing_voucher.py:330-345` uses exact fiscal-year start/end dates;
- cross-PCV cost-center evidence at `:215-310` supports annual carry-forward.

Short-year fixtures exist but lack a dedicated reporting carry-forward assertion. Synthetic boundary proof remains required.

### 5.4 Finance Book cohorts

- `test_finance_book.py:12-31` proves explicit Journal Entry Finance Book propagation to GL Entries.
- `test_period_closing_voucher.py:138-190` preserves separate explicit-book and no-book (`None`) PCV cohorts.
- `accounts_controller.py:2968-2977` requires an asset Finance Book when multiple possibilities remain unresolved.

Blank string versus SQL NULL, company default book, `include_default_book_entries`, selected/default/blank/NULL union and process-mode equality remain unproved. Initial synthetic work must keep one explicitly resolved company-default mode and fail closed on ambiguity.

### 5.5 Trial Balance test limit

`test_trial_balance.py:31-64` proves only one accounting-dimension-filtered balanced case. It does not prove opening, PCV/ACB selection, cancellation, immutable behavior, Finance Book cohorts, fiscal clamping, permissions or identity suppression. Native Trial Balance remains an internal formula reference only.

## 6. C2BG4 permission and leakage semantics

### 6.1 Effective authority mechanisms

Static evidence proves that effective authority is runtime-dependent:

- `frappe/tests/test_permissions.py:106-126`: User Permissions restrict document reads and `get_list`;
- lines `395-438`: strict-user-permission settings change visibility of empty or unmatched links;
- `user_permission/test_user_permission.py:146`: descendants are included unless `hide_descendants` is enabled;
- `test_permissions.py:763`: Custom DocPerm replaces standard permission rows;
- `custom_docperm.py:37` and its JSON: updates clear cache and may govern owner, permlevel, masks, report and share rights;
- `frappe/share.py:38,150`: shares add document authority and expand shared-name results;
- `role_permission_for_page_and_report.py:32-82`: Custom Role rows take precedence over standard Page/Report roles.

The mechanism is closed statically; effective state is not. Synthetic fixtures must deny Account/dimension restrictions, share-only access, masks, Custom DocPerm removal, strict-permission ambiguity and custom report-role drift.

### 6.2 Native report rejection strengthened

- `test_query_report.py:93-132` proves a Query Report may declare one `ref_doctype` while its SQL reads another table.
- `test_db_query.py:1242-1300` proves Report View filters fields unavailable at the user's permlevel.
- Lines `1339-1367` show an unauthorized selected field may be silently omitted.
- Lines `871-905` show a forbidden filter field raises `PermissionError`.

Report/ref-DocType permission is not source-query authority. Silent field removal cannot be treated as zero, absence or successful authorization.

### 6.3 Nested tree safety

- `frappe/utils/nestedset.py:386` uses permission-bypassing `frappe.get_all` for ancestors.
- `get_descendants_of()` at line `400` is permission-aware by default but permits `ignore_permissions`.
- `test_db_query.py:582` confirms permission-aware nested visibility.

A future complete Account chart must derive parent closure only from its already authorized Account set and validate structural integrity within that same set. Native ancestor expansion is rejected.

### 6.4 Frozen denial order

1. Authenticate and deny Guest.
2. Deny Administrator or mixed privileged posture unless later Owner policy says otherwise.
3. Require Finance role purpose independently of Page/Report roles and shares.
4. Require an explicit authorized company with no fallback.
5. Prove DocType and required-field authority, including Custom DocPerm and masks.
6. Deny Account or relevant dimension User Permissions and unresolved permission hooks.
7. Reject unsupported fiscal year, Finance Book, dimensions, currency or source mode.
8. Enforce caps before aggregation.
9. Begin one proven primary read-only snapshot.
10. Read chart, opening and movement under identical authority.
11. Validate chart completeness, exact debit/credit invariants and identity-safe schema.
12. Return generic unavailable state with no counts, figures or partial output.

No static evidence earns `C2B6_PERMISSION_PASS`; synthetic denial cases remain mandatory.

## 7. C2BG5 snapshot and workload semantics

### 7.1 Snapshot Blocker

- `frappe/app.py:206-223`: read-only mode may switch to a replica or begin a read-only transaction on the current connection.
- `test_db.py:1079` proves connection switching and restoration, not replica freshness.
- `frappe/app.py:416` commits unsafe requests and rolls back safe requests but does not establish an isolation level.
- `frappe/database/mariadb/database.py:105` enables connection auto-reconnect through the unread external `pymysql` dependency.
- The inspected MariaDB adapter does not select an isolation level.

**Accepted finding:** Blocker for C2BG5. Static source cannot prove primary pinning, isolation, replica exclusion, reconnect behavior or a complete before/after snapshot under concurrent GL, Account and PCV changes.

### 7.2 Workload High

- `mariadb/database.py:117` can set session `max_statement_time`.
- `test_db.py:39-59` proves an explicitly set timeout interrupts a longer statement.
- Lines `61-65` show timeout computation is request/configuration-dependent and may be zero outside a request.
- `estimate_count()` at MariaDB line `567` is estimated and not permission-aware.
- No inspected path defines Finance-specific account, period-day, output-row, response-byte, statement, request, retry or memory caps.

Synthetic benchmarking must derive every numeric constant, prove limit-pass and limit-plus-one denial, terminate without partial output, and reject oversized responses without truncation.

### 7.3 Identity and background state

- `frappe/app.py:344` delegates JSON error handling to an unread target; developer/runtime error settings remain unproved.
- request logging may record the user and full request path, so accounting identifiers must not be placed in query-string URLs;
- `frappe/utils/scheduler.py:94-137` connects per site and enqueues background jobs;
- `frappe/hooks.py:206,431-460` declares scheduler and request/job monitoring hooks.

Static source disproves any quiescent-read assumption. Synthetic isolation must disable or control background mutation and prove sanitized errors/logs.

## 8. Active hooks and protected-workspace impact

### 8.1 AI Assistant

`ai_assistant_ui/hooks.py` contains no active permission, request, report, scheduler, override or Finance-to-AI declaration. `frappe_assistant_core/hooks.py` exposes no Finance tool or accounting authority. Finance-to-AI remains prohibited.

### 8.2 Shared UI and routing

`erp_workspace_ui/hooks.py` registers global Desk assets, protected Sales form scripts, boot-home behavior and managed landing helpers. These surfaces are unchanged and must not be modified by GL/TB source proof. Landing precedence and all Sales, Procurement and Warehouse behavior remain protected.

### 8.3 HRMS

`hrms/hooks.py` participates in Payment Entry, Journal Entry, Company, period closing, accounting dimensions and bank reconciliation. No active declaration directly overrides GL Entry permissions or Trial Balance execution. All accounting execution and HRMS target implementations remain outside scope.

### 8.4 High endpoint dependency

`frappe_assistant_core/hooks.py:227-230` registers a global `before_request` target:

`frappe_assistant_core.api.oauth_cors.set_cors_for_oauth_endpoints`

The declaration says the target changes `frappe.conf.allow_cors` and `frappe.local.allow_cors` from settings. Because the target was not read, OAuth-only route containment is unproved. Before any Finance HTTP endpoint approval, its exact module must be fingerprinted and separately read to prove non-OAuth early exit and reject wildcard or credential-bearing Finance CORS exposure.

This High does not block architecture or an internal isolated synthetic oracle; it blocks request-exposed approval.

## 9. Source-mode decision

| Mode | Static disposition |
| --- | --- |
| `gl_reconstructed` | Sole surviving candidate for synthetic proof: one company, company base currency, strict fiscal/date bounds, explicit Finance Book posture, `is_cancelled=0`, zero active dimensions, aggregate-only and identity-free. No cancellation-freeze, close/reopen, audit or certification claim. |
| `cache_verified` | Stopped: Completed-state selection, normalized-key uniqueness, completeness, retry safety, exact GL parity, permission equality and snapshot equality are not proven. |
| `dual_compare` | Diagnostic-only and deferred; never a fallback. |
| Native Trial Balance / General Ledger | Rejected. |

There is no silent fallback between modes.

## 10. Dependency containment

### 10.1 Already governed by the original 69

The accounting specialist initially named several files outside the newer 34 but already covered by C2B1 and the prior semantic receipt, including `frappe/model/document.py`, general-ledger/GL Entry source, Accounting Period, PCV/Process PCV, ACB, Trial Balance, financial statements, Fiscal Year and `erpnext/accounts/utils.py`. They are not new amendment paths and were not re-read.

### 10.2 Exact unapproved paths

These test helpers were named by allowed imports but remain outside every accepted manifest:

- `erpnext/accounts/doctype/journal_entry/test_journal_entry.py`;
- `erpnext/accounts/doctype/sales_invoice/test_sales_invoice.py`;
- `erpnext/accounts/doctype/account/test_account.py`;
- `erpnext/accounts/doctype/cost_center/test_cost_center.py`.

They are optional only if a future harness avoids importing them. Reading or importing any requires a new fingerprint gate.

The exact CORS dotted target is material before endpoint approval. Its candidate module path must be existence-checked, fingerprinted and approved before content reading; no path claim is made by this receipt beyond the dotted target.

### 10.3 Unresolved path families

Journal Entry, Sales Invoice, Purchase Invoice and Payment Entry controllers are material only if the Owner requires deeper cancellation source proof. Exact paths/functions must be resolved under a separate path-inventory gate; conventional names must not be inferred automatically.

Frappe handler/API/response, background-job, Scheduled Job Type, Custom Role data/controller and `pymysql` dependencies remain behavioral/configuration evidence boundaries. They are not automatically added to source scope.

## 11. Findings and Main Control synthesis

| Severity | Finding | Disposition |
| --- | --- | --- |
| Blocker | One primary consistent accounting snapshot is not statically proven. | Accepted; C2BG5 requires synthetic primary/replica/isolation/concurrency evidence. |
| High | Cancellation freeze-call mismatch has no equivalent control in the 34-file extension. | Accepted; Owner must accept reporting-only deferral or require remediation/proof. |
| High | Effective complete-chart authority depends on runtime User Permission, Custom DocPerm, mask, share, strict-setting and custom-role state. | Accepted; synthetic denial matrix required. |
| High | Query Report authority does not constrain actual source tables, and Report View may silently omit fields. | Accepted; native report reuse remains rejected. |
| High | Native nested-tree helpers are not uniformly permission-preserving. | Accepted; derive hierarchy only from the approved complete set. |
| High | Finance-specific caps and no-partial timeout behavior are absent. | Accepted; numeric constants require benchmark evidence. |
| High | Global CORS request target is unread and applies before every request. | Accepted; fingerprint/read before endpoint approval. |
| Medium | Process-PCV detail tests/schema do not prove failure, retry, pause/resume or idempotency. | Accepted as a proof gap, not a proven runtime defect. |
| Medium | ACB normalized-key uniqueness, cleanup and exact parity remain unproved. | Accepted; cache mode remains stopped. |

Rejected conclusions:

- no claim that the overall Process PCV lacks failure handling;
- no claim that every active hook target is unsafe;
- no claim that deployment read-only mode is a consistent primary snapshot;
- no claim that source tests or static semantics are authenticated behavior or live acceptance;
- no recommendation to enter an open-ended review loop.

## 12. Owner decisions accepted and next controlled package

The Owner accepts:

1. the cancellation-freeze High as a strict reporting-only deferral; the capability remains read-only and makes no cancellation, close/reopen, frozen-period-control, audit-certification, mutation or accounting-execution claim;
2. `gl_reconstructed` as the sole synthetic-proof candidate; native General Ledger, native Trial Balance, Query Report passthrough, ACB/cache mode and silent fallback remain rejected;
3. deferral of all HTTP exposure; the global CORS target requires its own fingerprint/read gate before any Finance endpoint approval; and
4. planning only of the exact disposable Synthetic Evidence Execution Package and command/file allowlists.

These decisions do not change the findings, evidence, architecture, protection boundaries or deferred risks in this receipt. The synthetic execution gate `finance_cycle2_gl_tb_targeted_gap_synthetic_execution_authorized` remains unapproved.

## 13. Exact future documentation staging allowlist

The Owner separately authorizes one documentation-only staging, commit and push containing only:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2b2-c2b6-installed-source-semantic-proof-2026-07-17.md`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-targeted-c2b-gap-closure-plan-2026-07-17.md`
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2bg1-targeted-gap-source-fingerprint-receipt-2026-07-17.md`
5. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2bg2-c2bg5-static-semantic-read-stop-receipt-2026-07-17.md`

## 14. Protected exclusions and no-change statement

| Path | Required status | SHA-256 |
| --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged | `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked, unstaged | `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked, unstaged | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked, unstaged | `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

No source product file, test, runtime, registry, route, Shared UI, governance manifest, AI Assistant integration, live tree, database, metadata, role, permission, cache or service state was changed. Only the five documentation paths in section 13 are authorized for publication.
