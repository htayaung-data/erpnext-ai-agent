# Finance & Accounting Phase F5T1 - Payables Payload Guard And Documentation Hardening

Date: 2026-07-10
Status: accepted source hardening; ready for F5T2 closure re-review
Workspace family: Finance & Accounting
Page label: Finance Control Desk

## Decision

F5T1 closes the remaining Payables browser-guard and cutoff-wording findings without changing the Payables backend adapter, accounting semantics, role policy, or live environment.

The Finance page now rejects nested Payment Schedule and bank identity or row-shaped values in the raw financial payload sections before normalization. Valid aggregate bucket payloads and the safe schedule-policy booleans remain allowed.

A rejected raw response is rendered through the controlled policy-violation state and is not retained in the page payload cache.

## F5T2 Security Recheck Addendum

F5T2 adds a path-specific Payables value guard. Normalized amount, currency, outstanding, rate, balance, value, and total key tokens are blocked under `payables_count_posture`, including camelCase aliases and compound keys such as `baseGrandTotal` and `totalOutstanding`.

The guard remains contextual: accepted F4 manager-only MMK amount buckets under `receivables_amount_summary` remain allowed. This does not approve any F5 AP amount source or runtime.

F5T2 remains source-only. Live alignment and final browser acceptance require separate approval.

## Guard Classification

Blocked collections include Payment Schedule rows, bank-account rows, bank-transaction rows, bank-reference rows, and bank-detail rows.

Blocked identities include Payment Schedule identifiers; bank, bank-account, and bank-transaction identifiers; bank references; IBAN; SWIFT/BIC values; routing numbers; branch codes; and bank-detail values.

The following policy metadata remains safe and allowed:

- `payment_schedule_supported`;
- `payment_schedule_presence_gate_required`;
- `payment_schedule_rows_returned`.

These fields describe disabled policy posture. They do not carry Payment Schedule rows or identities.

## Executable Test Contract

The focused Finance shell tests load the page guard through a Node-only module export. Browser/Frappe registration is unchanged.

Tests prove:

- nested Payment Schedule rows and identities are rejected before normalization;
- nested bank identities and transaction shapes are rejected before normalization;
- normalization alone would omit the hostile sections, so the raw guard remains required;
- safe schedule-policy metadata does not create a false block;
- valid count-ready and controlled-unavailable Payables payloads render the read-only Finance shell;
- Accounts User and non-Finance endpoint behavior remains restricted.

## Cutoff Wording

F5A and F5B now use the implemented and accepted rule:

- `Current / not overdue` means `due_date >= cutoff_date`;
- invoices due on the cutoff date or later are included;
- this is count posture only, not AP balance, cash requirement, or payment authority.

## Staging Scope

F5T1 adds this document to the existing F5 candidate. Exact-path staging remains mandatory, and the unrelated AI assistant files, Sales acceptance smoke, and `a.out` remain excluded.

F5T1 does not stage, commit, push, live-align, restart, clear cache, reload metadata, migrate, or run protected gates.

## Boundary

No AP amounts, supplier rows, Purchase Invoice rows, Payment Schedule rows, Payment Entry rows, Payment Ledger rows, GL rows, account or bank rows, native reports/routes/exports/download/print, payment-schedule allocation/aging, payment/accounting execution, notification, email, portal, or external action is returned, enabled, or approved.
