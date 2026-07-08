# Finance & Accounting Phase F4L - AR Source Package Manual / Live-Alignment Prep Recheck

Date: 2026-07-07
Status: docs-only stopped gap report
Depends on: F4K stopped gap report and F4K1 copy / traceability remediation
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk

## Decision

Decision: `stopped_gap_report`.

F4L rechecked the Finance AR source package after F4K1. F4K1 materially improved owner-facing copy and provenance:

- bounded aggregate source reads are separated from row-level browser exposure;
- Sales Invoice aggregate count buckets are distinguished from manager-only Payment Ledger MMK amount buckets;
- F4G design-only provenance is reconciled with later F4H/F4H1/F4I1/F4J source work;
- runtime copy no longer uses `No financial rows loaded` framing.

F4L does not accept the package as ready for live-alignment prep because the review found source-safety and contract gaps that need a separate remediation phase.

F4L does not approve live alignment, restart, metadata reload, migration, protected gates, commit, push, row drilldown, native reports, routes, exports, downloads, print, posting, payment, reconciliation, write-off, tax, close, email, notification, portal behavior, user/role/permission mutation, DocType mutation, or accounting execution.

## Accepted Findings

### High - Payment Ledger Malformed Row Fail-Closed Gap

The Payment Ledger amount adapter currently skips some malformed rows instead of failing closed:

- rows missing required identity fields can be skipped;
- rows missing `against_voucher_type` or `against_voucher_no` can be ignored;
- this can produce a ready partial aggregate instead of returning unavailable with no amount values.

F4G requires required Payment Ledger source-field failures to return unavailable with no amounts. F4L therefore blocks live-alignment-prep readiness until malformed or incomplete Payment Ledger source rows fail closed.

Expected future remediation:

- treat missing required Payment Ledger identity fields as unavailable;
- treat Receivable Customer rows without supported against-voucher linkage as unavailable unless a later policy explicitly proves they are safe to ignore;
- return no bucket amounts, no grand total, no rows, and no identifiers on this failure;
- add tests for missing required fields and missing against-voucher linkage.

### Medium - Sales Invoice Missing-Due-Date Count Policy

Sales Invoice count buckets use due-date filters. Positive outstanding Sales Invoices without due dates can be omitted from all count buckets rather than making count posture unavailable.

F4K and F4K1 already flagged this as an Owner review item. F4L keeps it as a readiness gap that must be explicitly resolved before live-alignment prep:

- either fail closed when missing due-date open Sales Invoice rows are possible or detected;
- or Owner/Main Control explicitly accepts the omission risk for count posture with a documented business rationale.

### Medium - No-Effect Flag Naming Drift

The response still includes `financial_rows_loaded: false` as a no-effect flag. The flag is technically false for browser-returned rows, but the name conflicts with F4K1 wording because bounded Payment Ledger source rows may be read server-side for aggregate amounts.

Expected future remediation:

- rename or replace this flag with wording aligned to row-level exposure, for example `row_level_financial_data_returned: false`;
- update tests and frontend no-effect expectations;
- keep no-effect semantics for posting, payment, reconciliation, tax, close, notification, export, native route, and portal behavior.

### Low - Nested Row/Identity Guard

The frontend policy-violation guard checks top-level `payload.rows`. Current backend payloads return empty rows and tests cover that. Before live-alignment prep, the page should also defensively reject nested row or identity regressions under posture cards, lanes, receivables payloads, amount summaries, or future payload sections.

## Confirmed Safe Boundaries

F4L did not find direct row identity leakage or execution exposure in the reviewed source:

- no customer rows;
- no invoice rows;
- no voucher rows;
- no account rows;
- no Payment Ledger rows;
- no GL rows;
- no native route/report/export/download/print/action keys;
- no posting/payment/reconciliation/write-off/tax/close behavior;
- no email, notification, portal, user, role, permission, or DocType mutation.

The current amount posture remains gated by:

- Accounts Manager role category;
- scoped company from the Finance role/company resolver;
- approved company `Mingalar Mobile Distribution Co., Ltd.`;
- approved currency `MMK`;
- Payment Ledger source read permission;
- Payment Ledger metadata proof for company-currency amount semantics;
- bounded pagination and source-size cap;
- low-population suppression;
- fail-closed behavior for source-size overflow, missing amount due date, multiple due dates, split receivable accounts, and metadata drift.

The current count posture remains gated by:

- Accounts Manager role category;
- scoped company from the Finance role/company resolver;
- Sales Invoice source read permission;
- permission-preserving aggregate count reads;
- no rows, amounts, customer identifiers, invoice identifiers, routes, reports, exports, print/download, or actions.

## Owner Manual Review Readiness

F4L is not ready for live-alignment prep approval.

F4L may be used as an Owner/Main Control source-review gap report. Owner should not be asked to approve live alignment until the High and Medium gaps above are remediated or explicitly accepted where acceptance is appropriate.

## Recommended Next Step

Recommended next phase: `F4M Finance AR Source Safety Remediation`.

F4M should be scoped narrowly to:

- Payment Ledger malformed-row fail-closed behavior and tests;
- Sales Invoice missing-due-date count policy decision or fail-closed implementation;
- no-effect flag rename or contract correction;
- nested row/identity defensive frontend guard if approved;
- docs/tests updates only as needed to prove the remediation.

Do not proceed to live alignment, restart, metadata reload, protected gates, commit, push, Payables implementation, GL/Cash/Tax/Close work, row drilldown, native reports/routes, exports, or accounting execution from F4L.
