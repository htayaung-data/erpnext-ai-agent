# Finance & Accounting Phase F5S - Payment Schedule Semantics, Safe Detection, And AP Count Re-Readiness Proof

Date: 2026-07-10
Status: accepted with minimal fail-closed source patch; ready for re-review only
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Installed baseline inspected: ERPNext `16.4.1`, Frappe `16.5.0`

## Decision

A permission-preserving, company-scoped Payment Schedule presence detector is proven for the current installed stack.

The detector does not make Payables counts available. It deliberately returns controlled unavailable whenever any qualifying open Purchase Invoice has any Payment Schedule child row. It does not distinguish one row from multiple rows, inspect child due dates, validate schedule amounts, or interpret payment allocation.

This is the narrow safe correction for F5. A wrong AP aging count is worse than an unavailable count.

F5S is source-only. It does not approve live alignment, staging, commit, push, protected gates, or Payables feature expansion. The F5 package is ready for a separate closure-readiness re-review, but F5 staging remains blocked until that re-review is accepted.

## Installed ERPNext Evidence

Purchase Invoice metadata:

- `payment_schedule` is a Table field whose child DocType is `Payment Schedule`;
- `payment_terms_template` and `payment_schedule` are separate fields, so template absence does not imply child absence;
- `company`, `posting_date`, `due_date`, `outstanding_amount`, `total_advance`, `is_return`, `return_against`, and `on_hold` are parent fields available to permission-preserving aggregate filters;
- Purchase Invoice read permission exists for `Accounts Manager` and `Accounts User`, but the Finance service retains its stricter Accounts Manager-only count gate.

Payment Schedule metadata:

- `Payment Schedule` is `istable = 1` and has no standalone role permissions;
- child `due_date` and `payment_amount` are required fields;
- the child also contains invoice portion, paid, outstanding, base amount, discount, and due-date-basis fields that F5S does not read or return.

Installed `AccountsController` semantics:

- ERPNext creates a one-row 100 percent Payment Schedule when an invoice has no template and no inherited schedule;
- a template or linked order can create or inherit one or multiple rows, including cases where the invoice template field is blank;
- parent `due_date` becomes the maximum child due date;
- schedule totals are adjusted for advances and validated against invoice totals;
- overdue status considers child schedule amounts due before today.

Therefore, voucher-level aging by parent due date is not safe whenever child schedule semantics are present but unproved. A multiple-row schedule can contain an earlier overdue obligation while the parent due date points to the latest installment.

## Frappe Permission And Join Proof

The accepted detector queries `Purchase Invoice`, not `Payment Schedule` directly.

Frappe `DatabaseQuery` behavior for a child filter:

- adds the child table to the parent query;
- checks child read permission using `parent_doctype = Purchase Invoice`;
- joins child rows on `child.parenttype = Purchase Invoice` and `child.parent = Purchase Invoice.name`;
- retains Purchase Invoice role, sharing, permission-query, User Permission, and company conditions on the parent query.

F5S also supplies explicit child `parenttype` and `parentfield` filters. The selected company filter remains on Purchase Invoice because Payment Schedule has no company field.

Accepted query shape:

```python
frappe.get_list(
    "Purchase Invoice",
    filters=open_company_filters + [
        ["Payment Schedule", "parent", "is", "set"],
        ["Payment Schedule", "parenttype", "=", "Purchase Invoice"],
        ["Payment Schedule", "parentfield", "=", "payment_schedule"],
    ],
    fields=[{"COUNT": "name", "as": "count"}],
    limit_page_length=1,
)
```

The aggregate is parsed with the existing strict count parser. Only the boolean result `count > 0` affects policy. The aggregate count itself, parent identities, child identities, child fields, dates, portions, amounts, and debug/query details are never returned.

Rejected detection patterns:

- direct Payment Schedule row reads;
- direct child queries without parenttype and parentfield constraints;
- raw SQL, Query Builder pass-through, `frappe.get_all`, `frappe.db.count`, `frappe.db.exists`, or `ignore_permissions`;
- browser-supplied company, supplier, invoice, account, schedule, date, or currency filters;
- native Accounts Payable or Payment Terms report pass-through;
- grouped parent output or any query that returns parent/child names.

## Live Aggregate Proof

A read-only diagnostic ran as `finance.lead@meet.com` and returned only safe booleans:

- child permission through Purchase Invoice: allowed;
- aggregate shape: valid exact `count` alias;
- Payment Schedule presence: detected;
- template-based schedule presence: detected;
- template-less schedule presence: detected;
- identities returned: false.

No supplier, Purchase Invoice, Payment Schedule, account, Payment Entry, Payment Ledger, or GL identity or amount was printed or returned by the proof.

## Case Classification

| Case | F5S result | Reason |
| --- | --- | --- |
| `payment_terms_template` present | Unavailable | Child presence gate fails first; template gate remains as fallback if metadata is inconsistent. |
| Child schedule with no template | Unavailable | Template absence does not prove schedule absence. |
| One schedule row | Unavailable | It may be voucher-equivalent, but F5 does not inspect due-date or total integrity. |
| Multiple schedule rows | Unavailable | Parent due date can conceal earlier installment obligations. |
| Missing child due date | Unavailable | Any child presence stops before child fields are read. |
| Malformed child schedule | Unavailable | Any child presence stops before malformed fields can influence aging. |
| Schedule total mismatch | Unavailable | F5S does not interpret or reconcile schedule amounts. |
| Partial payment with schedule | Unavailable | Child allocation semantics remain outside F5. |
| Partial payment without schedule | Count candidate only if all existing parent gates pass | Count is voucher presence only; no payment amount or allocation truth is claimed. |
| Supplier advance / `total_advance > 0` | Unavailable | Advances are deferred and now have an explicit aggregate fail-closed gate. |
| Return or debit-note linkage | Unavailable | Existing `is_return` and `return_against` checks remain fail-closed. |
| On-hold invoice | Unavailable | Existing on-hold gate remains fail-closed. |
| Future-posted invoice | Unavailable | Source-only F5R posting-date gate remains in force. |
| Child belonging to another company | Does not affect selected company | Parent company filter and child relationship join exclude it. |
| Wrong child parenttype or parentfield | Does not join | Explicit relationship filters reject it. |
| No schedule child and all other gates pass | Count-only candidate | No schedule semantics are inferred; existing due-date parent count contract applies. |

## Minimal Source Patch

F5S adds only:

- `PAYABLES_SCHEDULE_CHILD_SOURCE = "Payment Schedule"`;
- a bounded parent aggregate presence query with explicit relationship filters;
- `payment_schedule_not_supported` controlled-unavailable response before aging buckets;
- an aggregate `total_advance > 0` fail-closed check;
- policy flags stating schedule support is false and schedule rows are not returned;
- business-facing unavailable copy that does not expose the internal reason code;
- neutral read-only page copy that no longer presents a green count-ready row while Payables is unavailable.

F5S does not add schedule-level aging, split-due allocation, AP amounts, rows, native ERP surfaces, or execution.

## Test Contract And Coverage

Focused tests now require:

- denied roles stop before permission and source adapters;
- browser filters stop before permission and source adapters;
- exact selected company on every aggregate query;
- exact child parent, parenttype, and parentfield constraints;
- one-row, multiple-row, missing-field, malformed, total-mismatch, and partial-payment schedule cases all return unavailable before buckets;
- wrong-company and wrong parent relationship rows do not trip selected-company detection;
- advances, missing due date, future posting, template, on-hold, return, permission denial, and malformed aggregate output fail closed;
- exact top-level and policy key sets prevent identity/debug-field drift;
- no counts or partial buckets return after schedule detection;
- user-facing copy says Payables counts are unavailable without exposing `payment_schedule_not_supported`;
- the static page posture no longer claims ready count status.

## Independent Review Integration

Accepted:

- template-only detection is incomplete;
- Payment Schedule presence must be detected through a permission-preserving parent query;
- any detected child schedule remains unavailable in F5S;
- advances need an explicit fail-closed parent gate;
- unavailable copy must describe schedule safety without implying payment authority.

Rejected:

- treating one Payment Schedule row as proof of split terms;
- treating one row as automatically safe enough for F5 runtime;
- direct child reads or amount/date inspection;
- weakening company or role gates to obtain visible counts.

Deferred:

- canonical one-row equivalence proof;
- child due-date/header due-date comparison;
- schedule total and allocation validation;
- Payment Entry and advance allocation semantics;
- schedule-level aging or AP amount posture.

## Re-Review Prerequisites

Before controlled staging can be approved:

- rerun focused and full source tests after F5S;
- inspect the staged diff through an exact allowlist;
- re-run the hard-boundary scan for forbidden APIs, identities, amounts, native surfaces, and execution;
- confirm source/live drift remains documented because F5R/F5S source fixes are not live-aligned;
- obtain Owner/Main Control closure-readiness acceptance.

## Boundary

No AP amount buckets, supplier rows, Purchase Invoice rows, Payment Schedule rows, Payment Entry rows, Payment Ledger rows, GL rows, account rows, native reports/routes/exports/download/print, payment/posting/reconciliation/write-off/tax/close behavior, notification, email, portal, external action, user/role/permission mutation, live alignment, restart, cache clear, metadata reload, migration, staging, commit, push, or protected gate is approved or performed by F5S.
