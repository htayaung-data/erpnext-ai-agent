# Finance & Accounting Phase F4M - AR Source Package Recheck And Manual Review Prep

Date: 2026-07-08
Status: source package accepted for Owner/Main Control manual review only
Depends on: F4K, F4K1, F4L, and F4L1 remediation
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk

## Decision

Decision: accepted for Owner/Main Control manual review.

F4M rechecks the Finance AR source package after F4L1. The F4L source-safety gaps are resolved in source and tests:

- malformed or incomplete Payment Ledger source rows now fail closed with `payment_ledger_source_invalid`;
- no malformed Payment Ledger row is skipped into a partial ready aggregate;
- source-invalid amount responses return no bucket counts, no bucket amounts, no grand total, no rows, no documents, and no ready runtime flag;
- Sales Invoice missing due dates now fail closed before receivables count buckets are calculated;
- amount aging remains due-date only and does not use posting-date fallback;
- the no-effect flag now uses `row_level_financial_data_returned`, not `financial_rows_loaded`;
- the Finance page includes a nested forbidden-payload guard for row, identity, route, report, export, download, print, and action-shaped data.

F4M does not approve live alignment. It does not approve restart, metadata reload, migration, protected gates, commit, push, Payables, GL, Cash, Tax, Close, native reports, native routes, exports, downloads, print, row drilldown, posting, payment, reconciliation, write-off, tax filing, period close, email, notification, portal behavior, user or role mutation, DocType mutation, or accounting execution.

## Source-Ready Scope

The following source package is ready for Owner manual review:

- Finance Control Desk shell and role-aware rendering;
- Finance role and company resolver foundation;
- Accounts Manager-only aggregate Sales Invoice receivables count buckets;
- Accounts Manager-only aggregate MMK Payment Ledger amount buckets;
- low-population suppression for amount buckets;
- bounded Payment Ledger pagination and row cap;
- fail-closed Payment Ledger malformed-row handling;
- fail-closed Sales Invoice missing-due-date count handling;
- row-level browser exposure guardrails in backend payloads and frontend rendering.

## Manual Review Pages And Views

Owner/Main Control should manually inspect the Finance Control Desk page after a separately approved alignment/review step:

- route/page label: Finance Control Desk;
- workspace family: Finance & Accounting;
- Accounts Manager view;
- Accounts User view;
- non-finance restricted view;
- unavailable or restricted states where company scope, role scope, or source gates do not pass.

This review is for source behavior and screen behavior only. It is not an approval to run accounting execution or native ERPNext routes.

## Accounts Manager Expected View

When all gates pass, an Accounts Manager may see:

- the approved company `Mingalar Mobile Distribution Co., Ltd.`;
- MMK as the only displayed amount currency;
- aggregate Sales Invoice receivables count buckets;
- manager-only aggregate Payment Ledger MMK amount buckets;
- suppressed amount buckets where low-population rules apply;
- copy stating that row-level data is not returned, shown, linked, exported, or actionable.

The manager view must not show:

- customer rows or customer identifiers;
- invoice rows or invoice identifiers;
- voucher rows, account rows, Payment Ledger rows, or GL rows;
- native report, Form, List, or query-report links;
- export, download, print, email, notification, portal, or action controls;
- posting, payment, reconciliation, write-off, tax, close, submit, cancel, save, delete, insert, set value, or enqueue controls.

## Accounts User And Restricted Views

Accounts User remains limited:

- no raw receivables counts until a later low-count or coarsening policy is approved;
- no amount buckets;
- no customer, invoice, voucher, account, Payment Ledger, or GL identities;
- no native reports, routes, exports, downloads, print, or execution controls.

Restricted users must not see Finance AR posture:

- System Manager alone is not Finance data authority;
- Executive Approver alone is not Finance data authority;
- Sales, Procurement, Warehouse, Stock, and other non-finance roles remain restricted for Finance data.

## Aggregate-Only Data Contract

Allowed browser-visible AR data in this package:

- bucket labels;
- aggregate bucket counts for Accounts Manager only when Sales Invoice count gates pass;
- aggregate MMK bucket amounts for Accounts Manager only when Payment Ledger amount gates pass;
- suppression state for low-population amount buckets;
- safe state, scope, and no-effect metadata.

Blocked browser-visible AR data:

- source rows;
- document names;
- customer names or IDs;
- invoice names or IDs;
- voucher names or IDs;
- account names or IDs;
- Payment Ledger row identifiers;
- GL identifiers;
- native route strings;
- report names or report output;
- export, download, print, or action payloads.

## Residual Risks And Caveats

Residual risks remain acceptable for manual review but not for execution approval:

- Payment Ledger semantics require Owner review against live business expectations before live alignment;
- payment terms remain unsupported and fail closed through the current multiple-due-date detection path;
- split receivable accounts remain unsupported and fail closed;
- low-population suppression thresholds remain policy decisions;
- count posture and amount posture are separate aggregate signals from different sources, not a reconciled accounting report;
- source files are still source-side only until Owner/Main Control separately approves any live alignment.

## Live-Alignment Prerequisites

Before any later live-alignment approval, Owner/Main Control must explicitly approve:

- exact source files to align;
- validation command results;
- manual browser checks for Accounts Manager, Accounts User, and restricted users;
- no identity exposure in network responses;
- no native route, report, export, download, print, or action controls;
- no accounting execution scope.

F4M does not grant that approval.

## Recommended Next Step

Recommended next step: Owner/Main Control manual review of the F4M source package.

If Owner accepts the source package and wants browser inspection, request a separate live-alignment-prep instruction. If Owner wants more source development before browser inspection, the safer next source phase is Payables count-posture policy, not rows, reports, exports, native routes, or execution.
