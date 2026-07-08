# Finance & Accounting Phase F4P - AR Manual Browser Review Acceptance

Date: 2026-07-09
Status: Owner/Main Control manual browser review accepted for the current F4 AR posture scope
Depends on: F4N, F4O, F4O1, F4O2, F4O3, F4O4, F4O5, and F4O6
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk
Custom page route: `finance-control-desk`
Desk page path: `/desk/finance-control-desk`

## Decision

Decision: accepted for the current F4 Finance AR manual browser review scope.

Owner/Main Control accepted the live browser behavior for the Finance Control Desk AR posture after direct route access, root-login landing, permission-modality remediation, and manager aggregate query remediation were verified in browser.

F4P records acceptance only. It does not approve any new source/runtime implementation, live alignment, restart, metadata reload, migration, protected gate, commit, push, Payables, GL, Cash, Tax, Close, row drilldown, native reports, native routes, exports, downloads, print, posting, payment, reconciliation, write-off, tax filing, period close, customer notification, email, portal behavior, or accounting execution.

## Manual Browser Results Accepted

Owner/Main Control reported these checks as accepted:

- direct route `/desk/finance-control-desk` loads;
- root login from `https://meet.erpbosai.com/` routes Finance users to the Finance Control Desk;
- `finance.lead@meet.com` lands on the Finance Control Desk;
- `accounts.ygn.01@meet.com` lands on the Finance Control Desk;
- the page no longer shows the Finance Control Desk Page permission error;
- the page no longer shows the `Company.disabled` permission modal;
- the page no longer shows the `User Permission` modal;
- the page no longer shows the SQL aggregate syntax modal for `count(name) as count`;
- the page remains read-only and aggregate-posture only;
- no accounting execution expansion is approved.

## Accounts Tested

| Account | Expected role posture | Accepted browser behavior |
| --- | --- | --- |
| `finance.lead@meet.com` | Accounts Manager / manager-level Finance visibility candidate | Lands on Finance Control Desk from root login and may see manager-only aggregate AR posture when all resolver, source, currency, permission, cap, and suppression gates pass |
| `accounts.ygn.01@meet.com` | Accounts User / normal Finance user candidate | Lands on Finance Control Desk from root login but must not see manager-only amount buckets |

System Manager alone, Executive Approver alone, and non-Finance roles remain outside Finance data authority unless they also hold an accepted Finance role. This acceptance does not make System Manager a Finance data role.

## Accepted F4 Scope

The accepted F4 browser scope is limited to:

- Finance Control Desk page access;
- root-login landing for Accounts Manager and Accounts User;
- role-aware Finance shell rendering;
- company-scoped resolver behavior for the current single-company MMK site;
- aggregate Sales Invoice receivables count posture for Accounts Manager when gates pass;
- manager-only aggregate Payment Ledger MMK receivables amount posture when all amount gates pass;
- controlled unavailable or suppressed states when gates fail;
- frontend defensive blocking for row, identity, route, report, export, print, download, or action-shaped response payloads.

No customer, invoice, voucher, account, Payment Ledger Entry, or GL Entry rows are accepted in this phase.

## Manager And User Visibility Expectations

Accounts Manager expected view:

- Finance Control Desk shell;
- Finance & Accounting workspace family;
- company-scoped AR posture when gates pass;
- Sales Invoice aggregate count buckets;
- manager-only Payment Ledger MMK aggregate amount buckets when all gates pass;
- suppressed or unavailable amount posture when low-population, permission, metadata, source-quality, row-cap, missing due date, payment-term, or split-account gates fail;
- no row-level customer, invoice, voucher, account, Payment Ledger, or GL detail.

Accounts User expected view:

- Finance Control Desk shell;
- limited or unavailable Finance posture;
- no manager-only Payment Ledger MMK amount buckets;
- no raw AR count buckets unless a later low-count/coarsening policy is approved;
- no row-level accounting data;
- no native reports, exports, downloads, print, or execution controls.

Restricted user expected view:

- restricted or unavailable state;
- no full Finance AR posture;
- no count buckets;
- no MMK amount buckets;
- no row-level accounting data;
- no native route, report, export, download, print, or action surface.

## Still Blocked

The following remain blocked after F4P:

- customer rows, customer lists, customer IDs, or customer drilldown;
- invoice rows, invoice lists, invoice IDs, invoice statuses, due-date rows, or invoice drilldown;
- voucher rows or voucher IDs;
- account rows or account IDs;
- Payment Ledger Entry rows or identifiers;
- GL rows, GL Entry identifiers, or GL mutation;
- native ERPNext Form, List, Report, or query-report routes;
- export, download, or print surfaces;
- Payment Entry creation, submission, cancellation, save, or mutation;
- Journal Entry creation, submission, cancellation, save, or mutation;
- Sales Invoice lifecycle action, submit, cancel, save, mutation, or native route exposure;
- Purchase Invoice lifecycle action or mutation;
- Payment Reconciliation or Bank Reconciliation mutation;
- write-off behavior;
- tax filing or period close behavior;
- notification, email, portal, or customer/supplier external action;
- Payables, GL, Cash, Tax, and Close workspace expansion;
- live alignment, backend restart, metadata reload, migration, protected gate, commit, or push without separate explicit approval.

## Residual Caveats

- Finance AR remains aggregate-only.
- Count source and amount source are intentionally separate: Sales Invoice aggregate count buckets and Payment Ledger MMK aggregate amount buckets.
- Count and amount posture can differ because the source semantics differ; the UI copy must continue to avoid treating them as the same measurement.
- Missing due dates, malformed Payment Ledger source rows, payment terms, split receivable accounts, unsupported source metadata, source row caps, and low-population suppression can return controlled unavailable or suppressed states.
- No row-level detail is available in this phase, including for Accounts Manager.
- No accounting execution is available in this phase.
- The live full unit suite has unrelated Warehouse drift in the dirty live deployment tree; F4P acceptance is based on focused Finance/routing validation and Owner browser review.
- Source and live trees remain dirty until a later staged handoff or closure phase explicitly defines staging, commit, push, and cleanup scope.

## Validation Record

F4P is docs-only. The supporting live/manual path before this acceptance included:

- direct route check for `/desk/finance-control-desk`;
- root-login landing check from `https://meet.erpbosai.com/`;
- Finance user checks for `finance.lead@meet.com` and `accounts.ygn.01@meet.com`;
- focused Finance source and live tests during F4O-F4O6 remediation;
- source full unit discovery during F4O5 and F4O6;
- live focused Finance/routing tests during F4O5 and F4O6;
- backend restart/cache clear only in the approved live remediation phases before F4P.

This F4P document does not add a new runtime validation gate and does not require compile or unit tests because it does not change runtime source.

## Acceptance Criteria Recorded

F4P is accepted when all of the following are true:

- Finance direct route loads for manual review;
- Finance root-login landing works for Accounts Manager and Accounts User;
- no Page permission, Company field permission, User Permission, or aggregate SQL syntax modal appears;
- Accounts Manager visibility remains aggregate-only;
- Accounts User does not receive manager-only amount visibility;
- row-level accounting data remains blocked;
- native reports, routes, exports, downloads, print, and execution controls remain blocked;
- Owner/Main Control understands that this acceptance is visibility-only and does not approve accounting execution.

Owner/Main Control reported these criteria as met for the current F4 browser scope.

## Recommended Next Step

Recommended next step: Owner/Main Control should choose one of two separate next phases.

- `F4Q Finance AR source package / staging readiness`: prepare an exact staging and commit-readiness package for the accepted Finance F4 source, docs, tests, and live-alignment trail. This should still avoid protected gates, commit, and push until explicitly approved.
- `F5 Payables posture policy/design`: start docs-only Payables visibility policy and design, without runtime implementation, rows, amounts, reports, routes, exports, payment behavior, or accounting execution until separately approved.

Do not start F5 until Owner/Main Control chooses it explicitly.

## Boundary Confirmation

F4P confirms:

- no accounting execution;
- no Payables, GL, Cash, Tax, or Close expansion;
- no row, customer, invoice, voucher, account, Payment Ledger, or GL drilldown;
- no native Finance route, report, export, download, or print behavior;
- no Payment Entry, Journal Entry, Sales Invoice lifecycle, GL mutation, reconciliation, write-off, tax, close, email, portal, or customer action;
- no live alignment, restart, metadata reload, migration, protected gate, commit, or push.
