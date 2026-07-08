# Finance & Accounting Phase F4N - Owner Manual Review Checklist / Live Alignment Decision Gate

Date: 2026-07-08
Status: decision-gate package for explicit Owner/Main Control live-alignment approval
Depends on: F4K, F4K1, F4L, F4L1, and F4M
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk
Custom page route: `finance-control-desk`
Desk page path for manual review: `/desk/finance-control-desk`

## Decision

Decision: ready for Owner/Main Control manual review and explicit live-alignment decision.

F4N creates the exact manual review checklist for the Finance Control Desk AR posture. It does not perform live alignment and does not approve live alignment by itself.

Owner/Main Control may review this source package and checklist now. Browser inspection against the live app requires a separate explicit live-alignment-prep instruction that names the exact files and scope.

Owner/Main Control must make a separate explicit decision before any source-to-live alignment, backend service reload/restart, metadata reload, migration, protected gate, commit, push, or browser live-review action is performed.

F4N does not approve Payables, GL, Cash, Tax, Close, native reports, native routes, exports, downloads, print, row drilldown, posting, payment, reconciliation, write-off, tax filing, period close, email, notification, portal behavior, user or role mutation, DocType mutation, or accounting execution.

## Review Source

This checklist is grounded in:

- F4K AR source package manual/live-alignment prep gap report;
- F4K1 copy and traceability remediation;
- F4L recheck stopped gap report;
- F4L1 fail-closed remediation;
- F4M source package recheck and manual review prep;
- Finance service source;
- Finance Control Desk page source;
- Finance shell, resolver, receivables policy, receivables count, and receivables amount tests;
- workspace registry and governance manifest entries for the Finance page route.

Current registry and governance labels remain conservative source-side labels for the Finance read-only overview route. They must not be interpreted as live alignment approval, and any later registry wording alignment is a separate source change.

F4L1 was a remediation patch turn, not a standalone phase document in the docs tree. F4M and F4N are the consolidated documentation records for the F4L1 source/test remediation and the resulting manual review decision gate.

## Login And Role Contexts

Owner/Main Control should verify three role contexts.

### Accounts Manager

Expected authority:

- may open the Finance Control Desk shell;
- may see company-scoped AR posture when resolver, source, permission, and currency gates pass;
- may see aggregate Sales Invoice count buckets;
- may see manager-only aggregate Payment Ledger MMK amount buckets;
- may see amount buckets suppressed when low-population rules apply.

Required example role posture:

- `Accounts Manager` is the manager-level Finance visibility role.
- If a user also has `System Manager` or `Executive Approver`, the Accounts Manager role is what grants Finance AR posture, not the non-finance role alone.

### Accounts User

Expected authority:

- may open limited Finance posture only where the shell allows it;
- must not see raw receivables counts in this AR package;
- must not see manager-only MMK amount buckets;
- must not see customer, invoice, voucher, account, Payment Ledger, or GL identities.

### Non-Finance / Restricted User

Expected authority:

- must see restricted or unavailable Finance posture;
- must not see the full AR posture;
- must not see count buckets, amount buckets, row-level data, native reports, exports, or execution controls.

Important role boundary:

- `System Manager` alone is not Finance data authority.
- `Executive Approver` alone is not Finance data authority.
- Sales, Procurement, Warehouse, Stock, and other non-finance roles alone are not Finance AR data authority.

## Role Review Checklist

Use this table for pass/fail manual review after a separately approved browser inspection step.

| Role context | Route | Expected page status | Allowed visible posture | Forbidden visible posture | Pass/Fail |
| --- | --- | --- | --- | --- | --- |
| Accounts Manager | `/desk/finance-control-desk` | Read-only overview when company/source gates pass | Finance Control Desk header, Finance & Accounting family, company-scoped AR posture, Sales Invoice aggregate count buckets, manager-only Payment Ledger MMK amount buckets, suppressed amount labels if applicable | customer/invoice/voucher/account/PLE/GL rows or IDs, native reports/routes, exports/downloads/print, posting/payment/reconciliation/write-off/tax/close controls | |
| Accounts User | `/desk/finance-control-desk` | Limited read-only posture or controlled unavailable posture | Finance shell and unavailable/deferred posture only | manager-only MMK amount buckets, raw count buckets, row-level accounting data, reports, routes, exports, execution controls | |
| System Manager only | `/desk/finance-control-desk` | Shell/admin or restricted posture only | No Finance AR data authority unless also mapped to an approved Finance role | manager AR counts, manager MMK amounts, row-level accounting data, reports, routes, exports, execution controls | |
| Executive Approver only | `/desk/finance-control-desk` | Restricted posture | No Finance AR data authority unless also mapped to an approved Finance role | manager AR counts, manager MMK amounts, row-level accounting data, reports, routes, exports, execution controls | |
| Non-Finance role | `/desk/finance-control-desk` | Restricted posture | Restricted message only | full Finance posture, count buckets, amount buckets, row-level accounting data, reports, routes, exports, execution controls | |

## Accounts Manager Manual Checks

On the Finance Control Desk custom page route `finance-control-desk` at `/desk/finance-control-desk`, verify:

- the page header reads Finance Control Desk;
- the workspace family reads Finance & Accounting;
- the sidebar entry opens the same Finance Control Desk page route;
- the page is a read-only overview posture, not an accounting execution console;
- the company posture is scoped to `Mingalar Mobile Distribution Co., Ltd.` when company gates pass;
- MMK is the only visible amount currency in this AR package;
- Receivables posture uses aggregate bucket cards, not rows.

If all AR gates pass, Accounts Manager may see:

- Sales Invoice aggregate count buckets;
- manager-only Payment Ledger MMK aggregate amount buckets;
- suppressed amount bucket labels where low-population suppression applies;
- copy stating that bounded aggregate source reads may occur server-side;
- copy stating that row-level accounting data is not returned, shown, linked, exported, or actionable.

Accounts Manager must not see:

- customer list rows, customer names, or customer IDs;
- invoice list rows, invoice names, invoice IDs, invoice statuses, or due-date row lists;
- voucher rows or voucher IDs;
- account rows or account IDs;
- Payment Ledger rows or Payment Ledger row identifiers;
- GL rows or GL Entry identifiers;
- native ERPNext Form, List, Report, or query-report links;
- export, download, or print controls;
- posting, payment, reconciliation, write-off, tax, close, email, notification, portal, submit, cancel, save, delete, insert, set value, or enqueue controls.

## Accounts User Manual Checks

On the same Finance Control Desk route, verify:

- the page does not expose manager-only amount buckets;
- raw receivables count buckets remain unavailable until a later low-count or coarsening policy is approved;
- row-level accounting data remains blocked;
- Payables, cash, ledger, tax, and close lanes remain unavailable or deferred;
- no native reports, routes, exports, downloads, print surfaces, or execution buttons appear.

## Restricted User Manual Checks

For a user without Finance data authority, verify:

- the page renders a restricted state, not the full ready Finance posture;
- restricted copy is concise and business-facing;
- no AR count buckets are visible;
- no MMK amount buckets are visible;
- no row-level accounting data is returned or shown;
- no native route, report, export, download, print, or action surface appears.

## Exact UI And Page Checks

Owner/Main Control should check:

- route/page: `finance-control-desk`;
- Desk path: `/desk/finance-control-desk`;
- page title: Finance Control Desk;
- workspace family: Finance & Accounting;
- visible status: read-only overview or restricted/unavailable state;
- boundary chips include no row-level data, aggregate source reads only, no report calls, and no native execution routes;
- ready copy distinguishes server-side bounded aggregate source reads from forbidden browser-returned row-level data;
- receivables copy distinguishes Sales Invoice aggregate count buckets from Payment Ledger MMK amount buckets;
- no stale `F2 shell` or `no financial rows loaded` wording appears;
- refresh reloads only the overview context;
- policy-violation state blocks rendering if a response contains row, identity, route, report, export, download, print, or action-shaped data.

Expected visible copy includes these plain-language cues:

- `No row-level data shown`;
- `Aggregate source reads only`;
- `No report calls`;
- `No native execution routes`;
- `Read-only overview`;
- `Finance overview shows scoped aggregate posture only`;
- `row-level accounting data is not returned, shown, linked, exported, or actionable`;
- `Sales Invoice aggregate count buckets`;
- `Payment Ledger MMK amount buckets`;
- `Finance overview shows no row-level financial data`.

For restricted users, expected visible copy includes:

- `Finance Control Desk is restricted`;
- `The Finance overview is not shown for this role`;
- no row-level financial data, metrics, reports, exports, or execution routes are returned or shown.

If Owner/Main Control sees internal policy keys such as `low_count_policy_not_ready` in otherwise safe unavailable copy, record it as a UX copy follow-up. It is not by itself accounting execution or row exposure, but it should not be treated as final polished owner-facing wording.

If source gates fail, Owner/Main Control may see unavailable/fail-closed states. Acceptable examples:

- company scope unavailable or restricted;
- Sales Invoice count buckets unavailable because missing due date policy is not ready;
- Payment Ledger amount buckets unavailable because source metadata, permission, approved currency, row cap, malformed source rows, missing due dates, payment terms, or split receivable accounts failed;
- suppressed amount buckets where low-population thresholds block display.

Unavailable states are acceptable only when they remain no-row, no-native-route, no-export, and no-execution.

## Fail-Closed Scenario Checklist

| Scenario | Expected visible behavior | Required boundary |
| --- | --- | --- |
| Company scope unavailable or restricted | Controlled unavailable or restricted state | No AR counts, no MMK amounts, no rows, no native routes, no execution |
| Multiple company selection required | Controlled unavailable state requesting approved selection | No cross-company aggregation |
| Sales Invoice read permission denied | Receivables count posture unavailable | No bucket counts and no invoice/customer detail |
| Sales Invoice missing due date detected | Receivables count posture unavailable | No partial count buckets |
| Payment Ledger permission or metadata gate fails | Amount posture unavailable | No amount buckets, no grand total, no Payment Ledger detail |
| Payment Ledger source exceeds row cap | Amount posture unavailable | No partial aggregate |
| Malformed Payment Ledger source row detected | Amount posture unavailable | No partial bucket counts, no partial bucket amounts, no grand total, no source identifiers |
| Missing Payment Ledger due date | Amount posture unavailable | No posting-date fallback |
| Payment terms or multiple due dates detected | Amount posture unavailable | No payment schedule rows or invoice rows |
| Split receivable account detected | Amount posture unavailable | No account names or account rows |
| Low-population suppression applies | Bucket shown as suppressed or grand total omitted | No customer or invoice inference |
| Frontend receives row/identity-shaped payload | Policy-violation blocked state | No row, identity, native route, report, export, print, download, or action rendering |

## Exact Boundary Checks

Owner/Main Control should explicitly confirm absence of:

- Payment Entry creation, submission, cancellation, save, or mutation;
- Journal Entry creation, submission, cancellation, save, or mutation;
- Sales Invoice lifecycle action, route drilldown, submit, cancel, save, or mutation;
- Purchase Invoice lifecycle action or mutation;
- GL Entry mutation;
- Payment Reconciliation mutation;
- Bank Reconciliation mutation;
- write-off or adjustment execution;
- tax filing or tax report submission;
- close, period close, or Period Closing Voucher behavior;
- customer notification, supplier notification, email, portal, or external customer action;
- native Form/List/Report/query-report route exposure;
- export, download, print, or report-output generation.

## Residual Caveats For Owner

Owner/Main Control should acknowledge:

- Payment Ledger amount semantics are accepted for manual review only and still require business review against live expectations;
- count posture and amount posture are separate aggregate signals, not a reconciled accounting report;
- count source is Sales Invoice aggregate counts;
- amount source is Payment Ledger aggregate MMK voucher-outstanding posture;
- missing Sales Invoice due dates fail closed for counts;
- malformed or incomplete Payment Ledger source rows fail closed for amounts;
- Payment Ledger rows over the configured cap fail closed with no partial aggregate;
- payment terms remain unsupported and can cause unavailable posture;
- split receivable accounts remain unsupported and fail closed;
- low-population suppression can hide amount bucket values and grand total;
- live data may legitimately show unavailable posture if any role, company, permission, metadata, currency, source-size, due-date, payment-term, split-account, or suppression gate fails.

## Live-Alignment Decision Requirements

F4N is ready for Owner/Main Control to answer a separate decision question:

Should Finance AR source package live alignment be approved for manual browser review?

If yes, the approval must explicitly name what is approved:

- source-to-live file alignment for Finance AR posture only;
- no accounting execution;
- no native reports/routes/exports;
- no row drilldown;
- no Payables, GL, Cash, Tax, or Close expansion;
- no commit or push unless separately approved.

Still separate after any live-alignment approval:

- backend service reload or restart approval;
- metadata reload approval;
- migration approval;
- protected gate approval;
- commit approval;
- push approval;
- generation of additional validation evidence, unless explicitly requested;
- any execution/posting/payment/reconciliation/tax/close feature approval.

Running protected gates or producing new validation evidence is not authorized by this document.

## Recommended Owner Decision

Recommended decision to request:

Approve Finance AR source package live alignment for Owner manual browser review only, with no execution expansion and no commit/push.

If Owner/Main Control does not want browser review yet, keep the package source-ready and continue only with a separately approved docs/source phase.
