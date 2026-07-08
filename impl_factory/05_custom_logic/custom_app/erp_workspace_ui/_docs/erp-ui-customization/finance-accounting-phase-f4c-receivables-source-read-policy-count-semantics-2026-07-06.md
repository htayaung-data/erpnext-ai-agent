# Finance & Accounting F4C Receivables Source-Read Policy and Count Semantics - 2026-07-06

Status: policy and test foundation only. F4C does not implement AR runtime count cards, amount totals, customer rows, invoice rows, ERPNext report calls, exports, native routes, posting, payment, reconciliation, write-off, customer communication, live alignment, restart, metadata reload, protected gate, commit, or push.

## Decision

F4C approves a future count-only source-read contract for Receivables posture. It does not enable runtime AR data.

F4D may use `Sales Invoice` as the future permission-aware count-only source only when the F4B resolver is scoped, role policy is accepted, company scope is selected or resolved, source permission is verified, and source/read tests pass. F4C does not verify `Sales Invoice` read permission and does not enable runtime counts. Accounts Receivable reports must not be passed through to the browser. `GL Entry`, `Payment Entry`, `Journal Entry`, `Customer`, and native reports remain blocked for F4D.

## F4B Dependency

F4C must not bypass F4B. Future count policy requires:

- resolver state is `scoped`;
- selected company comes from the F4B resolver;
- role category is `manager` or `normal_finance` for count-only posture;
- `System Manager`, `Executive Approver`, `Finance Lead Approver`, non-finance roles, and ungated `Auditor` remain blocked;
- no selected company means no policy contract acceptance;
- policy contract acceptance does not mean source permission has been verified;
- source permission verification remains false in F4C;
- runtime count enablement remains false in F4C.

## Future Source Contract

Allowed future source:

- `Sales Invoice`, count-only contract.

Blocked sources:

- Accounts Receivable report pass-through;
- Accounts Payable report pass-through;
- General Ledger report pass-through;
- `GL Entry`;
- `Payment Entry`;
- `Journal Entry`;
- `Customer`;
- `Purchase Invoice`;
- `Bank Transaction`.

Required future filters for `Sales Invoice` count-only semantics:

- `company` equals the selected allowed company from the F4B resolver;
- `docstatus` equals submitted only, `1`;
- `outstanding_amount` is greater than zero when using open receivable semantics;
- returns and credit notes are excluded in the first count cycle unless a later policy includes them;
- `return_against` records are excluded in the first count cycle unless a later policy includes them;
- cancelled, draft, amended, or reversed records are excluded;
- as-of date is backend-defined;
- payment schedule basis is deferred until an explicit policy is accepted.

## Field Allowlist

Internal-only future fields for count semantics:

- `company`, filter only;
- `docstatus`, filter only;
- `posting_date`, internal only if needed;
- `due_date`, internal only for bucket assignment;
- `outstanding_amount`, internal only for open-receivable filtering, never returned as an amount;
- `is_return`, internal filter only;
- `return_against`, internal filter only;
- `status`, internal filter only if needed.

Blocked browser fields:

- `name`;
- `customer`;
- `currency`;
- invoice identifiers;
- due dates as rows;
- posting dates as rows;
- outstanding amounts;
- payment schedule rows;
- route, report, export, print, or action keys.

## Aging Buckets

Future count-only buckets are:

- Current / not due;
- 1-30 overdue;
- 31-60 overdue;
- 61-90 overdue;
- greater than 90 overdue.

The as-of date must be set by the backend. Payment schedule aging remains deferred until explicitly approved because schedule-level due dates can change count semantics.

## Low-Count Policy

First-cycle behavior:

- Accounts Manager may see aggregate bucket counts after F4D gates, without customer or invoice identifiers, but F4C still does not verify source permission or enable runtime counts.
- Accounts User may receive count-only posture only after low-count suppression or coarsening is implemented and tested. Accounts User remains not-ready in F4C.
- Auditor visibility remains future read-only and requires explicit audit/company scope.
- No role receives customer-level or invoice-level data in F4C.

## Response Contract

Future count responses may include only these allowed response keys:

- `company_scope` for selected company label/currency already allowed by the resolver;
- `as_of_date` from the backend;
- `bucket_labels`;
- `bucket_counts`;
- `no_effect` flags;
- `policy` metadata.

`rows`, `amounts`, `documents`, and `metrics` are not allowed future count response keys. If retained defensively in F4C helper payloads, they must stay empty and are classified as blocked empty placeholders.

Future count responses must not include:

- rows;
- amounts;
- documents;
- metrics with money values;
- customer names;
- invoice names;
- invoice due dates as rows;
- status rows;
- native routes;
- report names or report payloads;
- export, print, download, or execution action keys.

## Implementation State

F4C adds a pure policy contract and tests only:

- no `Sales Invoice` query is executed;
- no `frappe.get_all` is used;
- no raw SQL or `frappe.db.sql` is used;
- no `ignore_permissions` is used;
- no Accounts Receivable report API is called;
- only F4B metadata reads remain allowed for `Company` and `User Permission`;
- policy contract acceptance is separated from source permission verification;
- source permission verification remains false;
- runtime count enablement remains false;
- Accounts User low-count suppression remains not-ready.

## Boundary Confirmation

F4C exposes no customer or invoice rows. It exposes no AR amount totals. It performs no accounting execution, user/role/permission mutation, posting, payment, reconciliation, write-off, native Finance route/report/export behavior, customer notification, email, portal behavior, live alignment, restart, metadata reload, protected gate, commit, or push.
