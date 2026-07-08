# Finance & Accounting Phase F4D Receivables Count Posture

Date: 2026-07-06
Status: source-only implementation, count-only receivables posture.

## Decision

F4D introduces the first runtime Finance receivables posture, limited to aggregate aging bucket counts for approved Accounts Manager scope. It does not expose customer names, invoice IDs, due-date rows, status rows, amounts, currency totals, reports, native routes, exports, print/download actions, or accounting execution.

Accounts User remains unavailable for receivables counts until low-count suppression or coarsening is designed and tested. Auditor visibility remains deferred.

## Runtime Gates

Receivables counts are returned only when all gates pass:

- authenticated Finance overview request;
- F4B role/company resolver returns `state=scoped`;
- role category is `manager` from Accounts Manager;
- selected company comes from the server-side resolver, not from the browser;
- `Sales Invoice` read permission is verified with a DocType permission check that fetches no rows;
- the count reader uses permission-preserving `frappe.get_list` aggregate count calls only;
- all count filters match the F4C source-read contract.

If any gate fails, the posture returns unavailable, empty bucket counts, no company scope, no rows, no amounts, no documents, and no execution effect.

## Count Source

Allowed source:

- `Sales Invoice` only.

Required filters on every bucket count:

- `company` equals the selected allowed company from the F4B resolver;
- `docstatus = 1`;
- `outstanding_amount > 0`;
- `is_return = 0`;
- `return_against` is not set;
- bucket-specific `due_date` filter based on backend as-of date.

Blocked sources and shortcuts:

- Accounts Receivable report pass-through;
- Accounts Payable, General Ledger, GL Entry, Payment Entry, Journal Entry, Purchase Invoice, Customer, Supplier, Bank Transaction;
- `frappe.get_all`, raw SQL, `ignore_permissions`, `frappe.get_doc`, `frappe.db.count`, `frappe.db.get_list`, `frappe.db.get_value`, report APIs, or native route strings.

## Aging Buckets

Backend as-of date controls the bucket windows:

- Current / not due: due date on or after the as-of date;
- 1-30 overdue;
- 31-60 overdue;
- 61-90 overdue;
- over 90 overdue.

Missing due-date handling and Payment Schedule aging remain deferred.

## Response Contract

The F4D count posture response is intentionally narrow:

- `phase`;
- `state`;
- `company_scope` only when counts are ready;
- `as_of_date`;
- `bucket_labels`;
- `bucket_counts`;
- `policy`;
- `no_effect`;
- `rows_returned=false`;
- `amounts_returned=false`;
- `documents_returned=false`;
- `runtime_count_enabled`.

The response does not include row arrays, amount arrays, document arrays, metrics, customer identifiers, invoice identifiers, route keys, report keys, export keys, print/download keys, or action keys.

## UI Scope

The Finance Control Desk overview can display the receivables posture card as `Counts only` when the backend returns ready count posture. The card is non-clickable and does not expose drilldowns or native ERPNext routes.


## Shared UI Future Contract

F4D does not redesign the Finance Control Desk. Future Finance UI phases must use the project shared workspace UI grammar established across Sales, Procurement, and Warehouse: stable page shell, compact command posture, consistent spacing, predictable refresh/loading/unavailable states, no blank first-load flashes, minimal premium copy, non-clickable unavailable states, and no native route exposure.

Finance should not copy Warehouse, Sales, or Procurement page-local classes blindly. It should reuse shared grammar and route stability principles while preserving accounting-specific boundaries around counts, rows, amounts, reports, exports, and execution.

## Boundary

F4D does not implement:

- Sales Invoice row browsing or detail drilldown;
- customer balances;
- amount totals or currency totals;
- payment, reconciliation, write-off, dunning, communication, or portal behavior;
- Journal Entry, Payment Entry, GL Entry, Purchase Invoice, or tax/close behavior;
- exports, print/download, notification/email, native routes, or execution controls;
- user, role, permission, DocType, metadata, migration, live alignment, restart, protected gate, commit, or push.

## Validation Requirements

Required validation for F4D source work:

- `git diff --check HEAD`;
- `node --check erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` when JS changes;
- `python3 -m compileall -q erp_workspace_ui`;
- focused Finance tests including `test_finance_accounting_receivables_count`;
- full unit discovery;
- cache cleanup/check;
- static boundary scan for forbidden APIs, routes, reports, exports, mutations, and native route strings.
