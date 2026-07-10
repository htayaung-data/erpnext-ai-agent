# Finance & Accounting Phase F5B - Payables Source-Proof And Count Contract

Date: 2026-07-09
Status: docs-only source-proof / count-contract
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Baseline: F5A Payables Visibility / Source Policy and current pushed Finance AR hardening commit `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0`

## Decision

F5B proves that installed ERPNext `Purchase Invoice` has the minimum metadata shape needed for a future AP aggregate count-only posture, but F5B does not approve runtime AP UI data. The count source decision is `conditionally_acceptable_for_future_count_only`, subject to the exact contract and tests below.

F5B does not approve AP amount buckets, supplier rows, Purchase Invoice rows, payment rows, native ERP reports/routes, exports, print/download, payment actions, live alignment, staging, commit, push, restart, metadata reload, migration, or protected gates.

## Installed Source Proof

Installed source and metadata were inspected read-only in backend container `erpai_project1-backend-1`. No Purchase Invoice, Supplier, Payment Ledger, GL Entry, Payment Entry, Bank, Account, or report business data was queried.

### Purchase Invoice Metadata

Installed file: `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/purchase_invoice/purchase_invoice.json`

Relevant installed metadata:

| Field / property | Installed evidence | F5B implication |
| --- | --- | --- |
| DocType submittable | `is_submittable = 1` | Future AP counts must use `docstatus = 1`; draft and cancelled documents are excluded. |
| `company` | Link to `Company` | Required count filter must be resolver-selected company only. |
| `posting_date` | Date, `reqd = 1`, default `Today` | Not an aging fallback. Future-dated posting needs explicit tests if runtime opens. |
| `due_date` | Date, no `reqd` flag in metadata | Missing due date must fail closed; no posting-date fallback. |
| `status` | Select: Draft, Return, Debit Note Issued, Submitted, Paid, Partly Paid, Unpaid, Overdue, Cancelled, Internal Transfer | Status may support an internal open filter, but cannot be displayed and cannot be the only safety gate. |
| `outstanding_amount` | Currency, read-only, `options = party_account_currency` | Forbidden for amount totals. May be used only as internal positive/open filter after tests prove no value is returned and parser fails closed. |
| `party_account_currency` | Hidden read-only Currency link | Confirms `outstanding_amount` is not company-currency safe. |
| `base_grand_total` / `base_rounded_total` | Currency in `Company:company:default_currency` | Forbidden for count posture and not an outstanding source. |
| `grand_total` / `rounded_total` | Currency in invoice `currency` | Forbidden for count posture. |
| `is_return` | Check, label `Is Return (Debit Note)` | Return/debit-note invoices must be excluded or fail closed. |
| `return_against` | Link to Purchase Invoice, read-only | Return/debit-note complexity is detectable and must be blocked or proven before runtime. |
| `payment_terms_template` | Link, depends on unpaid non-return invoices | Payment-term split support is not approved in first count runtime. |
| `payment_schedule` | Table `Payment Schedule`, depends on unpaid non-return invoices | Split payment schedule requires separate proof; detected schedule/terms should fail closed. |
| `on_hold`, `release_date`, `hold_comment` | Hold-related fields | On-hold treatment requires Owner policy; default contract fails closed if on-hold candidates exist. |
| `bill_no`, `bill_date` | Supplier invoice fields | Forbidden browser fields; never returned. |

### Purchase Invoice Source Logic

Installed file: `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py`

Relevant installed behavior:

- `set_missing_values()` can fill `due_date` from supplier/company/bill date/payment terms, which means due date may be generated but remains nullable in metadata.
- `make_gl_entries()` runs for submitted Purchase Invoices and updates supplier outstanding, confirming Purchase Invoice lifecycle remains accounting execution and is blocked.
- `set_status()` derives `Overdue`, `Partly Paid`, `Unpaid`, `Debit Note Issued`, `Return`, and `Paid` using `outstanding_amount`, due date, docstatus, and return checks.
- Because status depends on accounting state and due date, a future count source may use status only internally and must never expose it as row detail.

### Payment Schedule Metadata

Installed file: `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/payment_schedule/payment_schedule.json`

Relevant installed metadata:

- `due_date` is required on each schedule row;
- `payment_amount` is required and currency-valued;
- `payment_term` and `invoice_portion` can split a single invoice into multiple schedule obligations.

F5B policy: Payment Schedule / payment terms are deferred for first AP count runtime. If a candidate invoice uses split terms or schedule semantics, F5C must fail closed unless a separate schedule-aware count contract is approved.

### Payment Ledger Entry Reference

Installed file: `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/payment_ledger_entry/payment_ledger_entry.json`

Relevant installed metadata:

- `amount` is Currency with `options = Company:company:default_currency`;
- `amount_in_account_currency` is Currency with `options = account_currency`;
- `company`, `account_type`, `account`, `party_type`, `party`, `voucher_type`, `voucher_no`, `against_voucher_type`, `against_voucher_no`, and `due_date` exist.

F5B policy: Payment Ledger Entry remains future AP amount-proof reference only. It is not approved for count runtime or amount runtime in F5B.

### Accounts Payable Report Reference

Installed file: `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/report/accounts_payable/accounts_payable.py`

Installed behavior: the report imports `ReceivablePayableReport`, sets `account_type = Payable`, and returns the shared report runner.

F5B policy: native Accounts Payable report pass-through remains rejected. The report is a semantic reference only because shared AP/AR report behavior can expose supplier, voucher, bill, due-date, payment-term, future-payment, remarks, currency, and account context.

## Count Source Decision

`Purchase Invoice` is conditionally acceptable for a future aggregate count-only AP posture because the installed DocType exposes enough non-identity fields to count submitted, company-scoped, due-date-based payable posture without returning rows.

This is not runtime approval. F5C must still implement and test the source adapter before any Finance Control Desk AP count appears.

### Allowed Internal Fields For Future Count Contract

These fields may be used internally for count filtering/gating only:

- `company`
- `docstatus`
- `due_date`
- `is_return`
- `return_against`
- `status`
- `outstanding_amount`, only as a positive/open filter if F5C tests prove no value is returned and permission behavior is safe
- `payment_terms_template`, only to detect unsupported split-term complexity
- `payment_schedule`, only to detect unsupported split-term complexity if F5C can do so without row exposure
- `on_hold`, only to fail closed or apply an Owner-approved exclusion policy

### Forbidden Fields / Values

These must not be returned, shown, linked, exported, printed, or included in browser payloads:

- Purchase Invoice `name`, invoice ID, bill number, bill date, item rows, tax rows, status rows, due-date rows, posting-date rows, supplier-facing remarks, document route, owner, modified metadata;
- Supplier name, supplier ID, supplier group, supplier contact, supplier bank/account/tax/payment settings;
- amount fields including `outstanding_amount`, `grand_total`, `base_grand_total`, `rounded_total`, `base_rounded_total`, taxes, advances, write-off values, exchange-rate values;
- Payment Ledger, GL, account, voucher, Payment Entry, Journal Entry, Bank, and reconciliation identifiers;
- native route/report/export/download/print/action keys.

## AP Count Contract

### Role Gate

- `Accounts Manager` is the only first runtime AP count candidate.
- `Accounts User` receives no AP counts until low-count/coarsening policy is separately accepted.
- `Auditor`, `System Manager` alone, Executive-only, Sales/Purchase/Warehouse/Stock roles, and non-Finance users receive no AP data.
- Denied roles must stop before permission checks and before source adapter calls.

### Company Gate

- Company scope must come from the F4B Finance resolver.
- Browser-provided company is ignored/rejected.
- User default company display is not authorization.
- `single_company_site_fallback` is blocked for AP until Owner/Main Control explicitly re-accepts it for supplier liability posture.
- Every future count query must filter exactly on resolver-selected company.
- Any multi-company, missing-company, or mismatched-company condition must return controlled unavailable state.

### Permission Gate

Future F5C must prove a permission-preserving aggregate primitive:

- check `frappe.has_permission("Purchase Invoice", ptype="read")` or an equivalent permission-preserving method before count queries;
- use `frappe.get_list`, not raw SQL;
- no `frappe.get_all`;
- no `ignore_permissions`;
- no native report API pass-through;
- no browser-supplied filters;
- permission denial returns controlled unavailable state, not a Frappe modal exception.

### Aggregate Primitive

Future count queries must use Frappe-supported aggregate dict syntax, consistent with the accepted AR hardening pattern:

```python
frappe.get_list(
    "Purchase Invoice",
    fields=[{"COUNT": "name", "as": "count"}],
    filters=[...],
    limit_page_length=1,
)
```

A separate count query per bucket is preferred over grouping by due date because it avoids returning due-date rows. Any aggregate output must be parsed strictly: one row, expected alias only, non-negative integer count, no unexpected aliases, no row identity keys. Anything else fails closed.

### Docstatus / Status / Open Filter

Required filters for future count proof:

- `docstatus = 1` submitted only;
- `is_return = 0`;
- `return_against` empty / not set, or fail closed if the exact filter cannot be expressed safely;
- `due_date` present and within the bucket range;
- `company = resolver_selected_company`.

Open-filter policy:

- Preferred future proof: use `status in ("Unpaid", "Overdue", "Partly Paid")` as an internal open-state filter and test it against installed status behavior.
- `outstanding_amount > 0` remains a secondary internal count-filter candidate only if F5C proves it is permission-safe, returns no value, and behaves correctly for partial payments, debit notes/returns, overpayments, and party-account currency.
- No amount value may be returned or displayed under either approach.

### Aging Basis And Buckets

Aging basis: Purchase Invoice `due_date` only.

No posting-date fallback is allowed. This is stricter than ERPNext native AP/AR report behavior and matches Finance AR hardening.

Buckets for future F5C:

| Bucket | Count condition relative to cutoff date | Output |
| --- | --- | --- |
| `not_due` | `due_date >= cutoff_date` (due today or later) | Integer count only. |
| `overdue_1_30` | `cutoff_date - due_date` is 1 to 30 days | Integer count only. |
| `overdue_31_60` | `cutoff_date - due_date` is 31 to 60 days | Integer count only. |
| `overdue_61_90` | `cutoff_date - due_date` is 61 to 90 days | Integer count only. |
| `overdue_over_90` | `cutoff_date - due_date` is 91+ days | Integer count only. |
| `unavailable` | Any required gate fails | No partial counts. |

`due_soon` is not part of the first AP count contract.

Cutoff date must be server-derived. Browser-provided cutoff dates are rejected until a separate date policy is approved.

### Empty Result Behavior

If all gates pass and each aggregate bucket count returns a valid zero, the posture may return ready with zero counts. Empty result is not an error.

If any required gate, source check, complexity check, aggregate parse, or permission check fails, return unavailable with no partial counts.

## Complexity Policy

| Scenario | F5B policy | Reason |
| --- | --- | --- |
| Missing `due_date` | Fail closed. | Installed due date is nullable; no posting-date fallback. |
| Future posting date | Deferred / fail closed if detected by future policy. | AP posture should not infer future accounting documents without explicit cutoff policy. |
| Future due date | Allowed in `not_due` if all other gates pass. | Due-date aging requires not-due obligations. |
| Payment terms / Payment Schedule | Deferred; fail closed if detected. | Single invoice can split into multiple obligations; first count contract is voucher-level only. |
| Returns / debit notes (`is_return`, `return_against`) | Deferred; exclude or fail closed. Preferred first runtime: exclude `is_return = 1` and fail closed if return/debit-note interaction is detected. | Returns can alter outstanding posture. |
| Advances / Purchase Order advances | Deferred / excluded. | Not invoice AP posture. |
| Partial payments | Allowed only through proven open-state filter; no amount exposure. | Count can include partly paid invoices if status/open filter is proven. |
| On-hold invoices | Deferred; fail closed until Owner chooses include/exclude policy. | Payment pressure and payment readiness differ. |
| Overpayments / negative outstanding | Fail closed or exclude through open-state proof; no amount inference. | Negative/credit exposure can identify supplier credit posture. |
| Cancelled documents | Excluded by `docstatus = 1`. | Cancelled AP should not count. |
| Amended documents | Submitted amended replacement may count only if it passes filters; amended-from metadata is never returned. | Avoid row identity exposure. |
| Multi-currency | Counts can be currency-neutral; amounts remain blocked. | Count output has no currency. |
| Supplier credit exposure | Deferred / blocked. | Supplier credit is sensitive and not first count posture. |

## Response Contract For Future F5C

Allowed response keys only:

- `as_of_date`
- `bucket_counts`
- `bucket_labels`
- `company_scope`
- `no_effect`
- `policy`
- `source_state`

Required no-effect flags:

- no supplier rows returned;
- no Purchase Invoice rows returned;
- no payment rows returned;
- no amount values returned;
- no native report/route/export/download/print used;
- no Payment Entry / Payment Request / Payment Order / payment run performed;
- no Purchase Invoice lifecycle action performed;
- no Journal Entry, GL Entry, reconciliation, write-off, tax, close, email, notification, portal, supplier statement, or supplier communication performed.

## Required Tests Before Runtime

F5C must not start without tests for:

- Accounts Manager allowed candidate after gates;
- Accounts User gets no AP counts or amounts;
- Auditor/System Manager-only/Executive-only/non-Finance denied;
- denied roles do not call permission checks or source adapter;
- resolver-selected company required;
- `single_company_site_fallback` remains blocked unless Owner re-accepts it;
- browser company/supplier/account/voucher/currency/date/status filters rejected;
- permission denial returns controlled unavailable state;
- `frappe.get_list` aggregate dict syntax used;
- no raw SQL, no `frappe.get_all`, no `ignore_permissions`, no native report API;
- malformed aggregate output fails closed: empty response, multiple rows, missing alias, unexpected alias, `None`, non-numeric value, negative value, row identity keys, extra source fields;
- missing due date fails closed;
- payment terms / schedule detected and unavailable;
- return/debit-note cases excluded or unavailable;
- partial payment status/open-filter behavior;
- on-hold invoice policy;
- overpayment/negative outstanding policy;
- cancelled/amended document behavior;
- wrong company and multi-company behavior;
- no supplier/invoice/payment/voucher/account/PLE/GL identity in response or nested payloads;
- no row/action helper output such as `rows`, `columns`, `documents`, `records`, `invoices`, `action_targets`, `native_target`, `target`, `route`, `route_parts`, `doctype`, `name`, `debug`, raw filters, or SQL metadata;
- frontend AP-shaped payload guard rejects supplier, supplier name/ID, Purchase Invoice, bill number/date, payable account, party, supplier group, remarks, Payment Order, supplier bank/contact/tax, native report/route/export/download/print/action keys;
- static boundary scan for Payment Entry, Journal Entry, Purchase Invoice lifecycle, GL mutation, reconciliation, write-off, payment run, email, notification, portal, native route/report/export/download/print;
- static source scan proves no procurement shared row helpers, `frappe.db.count`, `frappe.get_all`, child-table `Purchase Invoice Item` reads, native form targets, or action target builders are used for AP count posture.

## Findings Integrated

Accepted:

- `Purchase Invoice` can be the future count-only candidate because installed metadata has company, docstatus lifecycle, due date, return markers, status, and open-state fields. This is an operational visibility count, not AP liability balance, cash requirement, or supplier exposure.
- Due date is nullable in installed metadata, so missing due date must fail closed.
- `outstanding_amount` is party-account currency and cannot support amount totals.
- Payment Schedule/payment terms split voucher obligations and are unsupported for first count runtime; first runtime must fail closed on detected terms instead of aging installments from schedule rows.
- Payment Ledger Entry remains future amount proof only.
- Native Accounts Payable report remains semantic reference only and cannot be used as a source/pass-through.

Rejected:

- AP runtime in F5B.
- Any amount bucket or amount total.
- Native AP report pass-through.
- Direct GL sums and raw Payment Ledger sums.
- Supplier rows, Purchase Invoice rows, Payment Entry rows, route/report/export/download/print/action surfaces.
- System Manager or Executive-only AP authority.

Deferred:

- Accounts User AP count visibility; F5B explicitly rejects allowing Accounts User in first AP count runtime.
- Auditor AP visibility.
- AP amount source proof.
- Payment terms support.
- Returns/debit-note normalization.
- Advances and supplier credit exposure.
- On-hold invoice policy.
- Due-soon bucket and custom cutoff policy.
- Cash/bank planning handoff.

## F5C Readiness

Not ready for runtime implementation.

F5B makes the count source conditionally acceptable as a future contract, but F5C needs Owner/Main Control approval plus a test-first implementation plan. The next recommended step is `F5C Payables Count Runtime Test Contract / Implementation Approval`, not direct UI expansion.

## Boundary Confirmation

F5B introduced no runtime Payables reads, no AP UI data cards, no amount buckets, no rows, no native AP reports/routes/exports/download/print, no payment/execution actions, no user/role/permission/DocType mutation, no live alignment, no restart, no reload, no migration, no staging, no commit, no push, and no protected gates.
