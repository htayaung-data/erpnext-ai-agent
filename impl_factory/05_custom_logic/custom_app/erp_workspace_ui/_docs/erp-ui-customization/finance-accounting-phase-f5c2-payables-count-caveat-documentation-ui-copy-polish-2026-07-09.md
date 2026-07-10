# Finance & Accounting Phase F5C2 - Payables Count Caveat Documentation And UI Copy Polish

Date: 2026-07-09
Status: source-only copy and documentation polish
Workspace family: Finance & Accounting
Page label: Finance Control Desk

## Decision

F5C2 records F5C1 manual-review caveats and polishes user-facing Payables copy before any live alignment decision.

No Payables source-read behavior changed in F5C2. The F5C runtime remains Accounts Manager-only, aggregate count-only, and read-only. F5C2 does not approve live alignment, staging, commit, push, protected gates, AP amount buckets, supplier rows, Purchase Invoice rows, Payment Entry rows, native reports, exports, routes, print/download, or payment execution.

## Caveats Recorded

- Payment Schedule child rows are not inspected in F5C.
- F5C fails closed when `payment_terms_template` is present on a candidate Purchase Invoice.
- Schedules without a payment terms template remain a residual semantic caveat until a future child-schedule source policy and proof are approved.
- `not_due` means current / not overdue and includes Purchase Invoices due today or due in the future.
- The count posture is not an AP balance, cash requirement, payment approval, payment run, supplier aging truth, or native Accounts Payable report replacement.

## Copy Polish

F5C2 changes Payables copy only:

- Accounts User and non-manager unavailable states use owner-facing wording instead of raw policy reasons such as `accounts_manager_required`.
- Manager-ready copy states that Current / not overdue includes invoices due today or later.
- The static overview row now uses count-only wording instead of pairing an Unavailable label with count-only Payables text.

## Boundaries Preserved

- No Payables amount values.
- No supplier names, supplier IDs, supplier contact, supplier bank, or supplier tax detail.
- No Purchase Invoice names, bill numbers, bill dates, due-date rows, posting-date rows, item rows, or tax rows.
- No Payment Entry, Payment Request, Payment Order, GL, Payment Ledger, Bank, account, voucher, or reconciliation row detail.
- No native report, route, export, download, print, or action target.
- No Purchase Invoice lifecycle, Payment Entry lifecycle, Journal Entry, GL mutation, reconciliation, write-off, tax, close, email, notification, portal, supplier statement, or supplier communication behavior.

## Live Alignment Readiness

After F5C2, the source package remains ready for an Owner/Main Control live-alignment decision only. Live alignment is not approved by this document.

Owner should explicitly accept the Payment Schedule caveat and current/not-overdue bucket meaning before live alignment.
