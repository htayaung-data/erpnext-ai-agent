# Finance & Accounting Phase F5A - Payables Visibility / Source Policy

Date: 2026-07-09
Status: docs-only source policy
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Baseline: F5 Payables Posture Policy / Design and current pushed Finance AR hardening commit `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0`

## Decision

F5A defines Payables visibility and source policy only. It does not approve AP runtime reads, UI Payables data cards, count runtime, amount runtime, native ERP reports/routes, exports, print/download, payment actions, live alignment, staging, commit, push, restart, metadata reload, migration, or protected gates.

The safe next Payables path is not implementation. F5A recommends `F5B Payables Source-Proof And Count Contract` because the policy identifies plausible count-only candidates but still requires proof for due-date, returns/debit notes, payment terms, advances, partial payments, permission behavior, and company scoping before any runtime AP count is exposed.

## Research Performed

Project sources reviewed:

- F5 policy/design document: `_docs/erp-ui-customization/finance-accounting-phase-f5-payables-posture-policy-design-2026-07-09.md`.
- Finance Control Desk runtime copy in `erp_workspace_ui/finance_accounting/service.py` and page copy in `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` as design reference only.
- F4 AR hardening lessons summarized from the accepted source package and current baseline commit.

Installed ERPNext source/metadata inspected read-only inside `erpai_project1-backend-1`:

- `erpnext/accounts/report/accounts_payable/accounts_payable.py`: imports `ReceivablePayableReport`, sets `account_type: Payable`, and returns the shared report runner.
- `erpnext/accounts/report/accounts_receivable/accounts_receivable.py`: shared receivable/payable report implementation.
- `erpnext/accounts/doctype/purchase_invoice/purchase_invoice.json`: defines `due_date`, `is_return`, `return_against`, `payment_schedule`, `party_account_currency`, and `outstanding_amount` with `options: party_account_currency`.
- `erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py`: shows due-date assignment, return handling, Payment Ledger / GL interaction, status decisions from outstanding amount, and submit/cancel GL behavior.
- `erpnext/accounts/doctype/payment_ledger_entry/payment_ledger_entry.json`: defines `amount` as company default currency, plus `account_currency`, `amount_in_account_currency`, `party_type`, `party`, `voucher_type`, `against_voucher_type`, `against_voucher_no`, and `company`.

Official references kept for source-link sanity:

- ERPNext Purchase Invoice: https://docs.frappe.io/erpnext/purchase-invoice
- ERPNext Payment Entry: https://docs.frappe.io/erpnext/payment-entry
- ERPNext Payment Ledger: https://docs.frappe.io/erpnext/payment_ledger
- ERPNext Accounting Reports: https://docs.frappe.io/erpnext/accounting-reports
- ERPNext Payment Terms: https://docs.frappe.io/erpnext/payment-terms
- ERPNext Payment Reconciliation: https://docs.frappe.io/erpnext/process-payment-reconciliation-tool
- ERPNext Accounts Payable source wrapper: https://github.com/frappe/erpnext/blob/develop/erpnext/accounts/report/accounts_payable/accounts_payable.py
- ERPNext shared Accounts Receivable/Payable source: https://github.com/frappe/erpnext/blob/develop/erpnext/accounts/report/accounts_receivable/accounts_receivable.py
- Microsoft Business Central payables reports: https://learn.microsoft.com/en-us/dynamics365/business-central/payables-reports
- Microsoft Business Central Aged Accounts Payable report: https://learn.microsoft.com/en-us/dynamics365/business-central/reports/report-322
- Oracle Fusion Payables Invoice Aging Report: https://docs.oracle.com/en/cloud/saas/financials/25c/fappp/payables-invoice-aging-report.html

No Purchase Invoice, Supplier, Payment Ledger, GL Entry, Payment Entry, Bank, Account, or report business data was queried. Future source proof must pin behavior to the installed ERPNext source/version in the live backend container or an explicitly recorded source revision; public `develop` links are supporting references only and are not sufficient proof by themselves.

## Source Decisions

### Rejected For First Runtime

| Source or surface | F5A verdict | Reason |
| --- | --- | --- |
| Native ERPNext `Accounts Payable` report pass-through | Rejected | Installed source wraps the shared receivable/payable report with `account_type: Payable`; report output can include supplier, voucher, bill, due-date, payable-account, outstanding, currency, future-payment, payment-term, supplier-group, and remarks fields. That violates no-row/no-identity/no-native-report boundaries. |
| `Purchase Invoice.outstanding_amount` as amount total | Rejected | Installed Purchase Invoice metadata defines `outstanding_amount` with `options: party_account_currency`; it is not proven company-currency/MMK safe. It may be considered only as an open-invoice count filter after F5B proof. |
| Direct GL/AP account sums | Rejected | GL aggregation would bypass AP voucher semantics, payment allocation semantics, and row leakage boundaries. GL rows remain outside first Payables posture. |
| Raw Payment Ledger row sums | Rejected | AP amount posture must be voucher-outstanding semantics that net invoice, payment, journal, return/debit-note, and allocation rows. Raw row sums can misstate outstanding pressure. |
| Supplier rows or balances | Rejected | Supplier identity, tax, bank/default account, hold/payment settings, contacts, and portal context are sensitive and not first-cycle posture data. |
| Purchase Invoice rows | Rejected | Invoice identity, bill number, due-date rows, statuses, item/tax lines, and voucher links are row-level AP exposure. |
| Payment Entry rows/actions | Rejected | Payment Entry is payment execution/allocation posture, not visibility posture. |
| Native Form/List/query-report routes, export, download, print | Rejected | Native navigation and extraction bypass the custom Finance boundary. |

### Accepted Future Source Candidates

| Candidate | Allowed only for | Required proof before runtime |
| --- | --- | --- |
| `Purchase Invoice` aggregate count source | Future count-only AP posture, likely F5C after F5B proof. | Permission-preserving aggregate read; selected company filter; submitted-only filter; open unpaid/partially paid filter; due-date basis; no rows/identities; malformed aggregate fail-closed; no native route/report/export; handling for missing due date, payment terms, returns/debit notes, advances, on-hold invoices, and partial payments. |
| `Payment Ledger Entry` payable voucher-outstanding source | Future manager-only company-currency amount proof, not first runtime. | `amount` company-currency semantics, `amount_in_account_currency` internal only, payable account/party semantics, voucher-level netting across invoice/payment/journal/return rows, selected-company assertion, pagination/cap, malformed row fail-closed, low-population suppression, no raw rows. |
| Shared receivable/payable report source logic | Future reference only, not pass-through. | Any adapter must avoid report output, native routes, row fields, supplier/voucher identities, exports, and report API pass-through. |

## Proposed AP Count Bucket Semantics

AP count posture should be due-date based and count-only. It must not return supplier names, supplier IDs, Purchase Invoice IDs, bill numbers, due-date rows, statuses, amounts, currency totals, payment references, account references, or route/action keys.

Proposed buckets for future F5C only:

| Bucket | Semantics | Policy |
| --- | --- | --- |
| `not_due` | Open submitted AP vouchers due on the cutoff date or later. This includes invoices due today. | Count only. |
| `overdue_1_30` | Open submitted AP vouchers due 1 to 30 days before cutoff. | Count only. |
| `overdue_31_60` | Open submitted AP vouchers due 31 to 60 days before cutoff. | Count only. |
| `overdue_61_90` | Open submitted AP vouchers due 61 to 90 days before cutoff. | Count only. |
| `overdue_over_90` | Open submitted AP vouchers due more than 90 days before cutoff. | Count only. |
| `unavailable` | Any required gate fails. | No partial counts, no rows, no amounts. |

F5A intentionally drops `due_soon` from the first count contract. Due-soon timing is operationally useful, but it is a payment-planning signal and should be considered after basic due-date aging is proven.

### Count Source Rules For Future Proof

- Use submitted Purchase Invoice posture only if source proof accepts it.
- `docstatus` must be submitted-only; draft/cancelled documents are excluded.
- Do not trust document `status` labels as the primary source of truth without proof.
- Missing due date must fail closed for the entire count posture; no posting-date fallback.
- Payment terms / split payment schedule are unsupported until F5B proves a safe policy; detected split terms should fail closed.
- Purchase Invoice returns/debit notes are unsupported for first count runtime unless F5B proves a safe exclusion/netting policy.
- Supplier advances and Purchase Order advances are excluded from first count posture.
- Partial payments may be considered only through an open-invoice count filter; no amount values may be returned.
- On-hold invoices require explicit Owner policy before runtime; default posture is fail closed or exclude only if source proof is exact and tested.
- Company filter must come from the Finance resolver; browser-supplied company, supplier, account, voucher, currency, date, or status filters are rejected.

## Role / Company / Currency Policy

| Area | Policy |
| --- | --- |
| First AP role | `Accounts Manager` is the first candidate for future AP aggregate count posture. |
| Accounts User | No AP counts or amounts until low-count/coarsening policy is separately approved. |
| Auditor | Deferred. No AP data by default. |
| System Manager | Not Finance data authority by itself. System Manager only gets Finance data if paired with an approved Finance role. |
| Executive-only | No AP data by role alone. |
| Non-Finance roles | Restricted/no AP data. |
| Company scope | Must use Finance resolver selected company. User default company display does not authorize AP data. |
| Single-company fallback | Must be re-accepted for AP before runtime because supplier liability exposure is distinct from AR posture. |
| Currency | Counts return no currency. Amount posture is blocked until company-currency MMK proof. Mixed-currency totals must fail closed. |
| Permission path | No `ignore_permissions`, no raw SQL, no `frappe.get_all`, and no broad native report API pass-through. Permission denial must return controlled unavailable state. |

## Blocked Scope

F5A keeps these blocked:

- Purchase Invoice creation, save, submit, cancel, amend, return, debit note, write-off, or lifecycle behavior;
- Payment Entry creation, allocation, save, submit, cancel, supplier payment, payment run, Payment Request, or Payment Order behavior;
- Journal Entry behavior and GL Entry mutation;
- Payment Reconciliation, Bank Reconciliation, unreconcile, write-off, tax, close, or bank/cash behavior;
- Supplier notification, email, portal, statement sending, or customer/supplier communication;
- Supplier rows, supplier names, supplier IDs, supplier balances, supplier bank details, supplier contacts, supplier group, supplier tax data, or supplier payment settings;
- Purchase Invoice rows, invoice IDs, bill numbers, voucher IDs, due-date rows, item lines, statuses, tax rows, or document drilldown;
- Payment Ledger rows, GL rows, account rows, voucher rows, account-currency rows, or allocation rows returned to the browser;
- native Accounts Payable report pass-through, query-report route, Form/List route, `/app`, print, export, download, or dashboard embedding;
- browser-supplied source filters;
- live alignment, restart, metadata reload, migration, staging, commit, push, or protected gates.

## Required Future Tests Before Runtime

Before any F5C/F5E implementation, tests must prove:

- `Accounts Manager` is the first AP aggregate candidate;
- `Accounts User`, `Auditor`, `System Manager` alone, Executive-only, Sales/Purchase/Warehouse/Stock roles, and non-Finance users receive no AP counts or amounts;
- denied roles do not call source adapters;
- user default company does not authorize AP posture;
- selected company comes only from Finance resolver;
- AP use of `single_company_site_fallback` is blocked until Owner/Main Control explicitly re-accepts it for supplier liability posture;
- requested/browser-supplied company, supplier, account, voucher, currency, date, status, and source filters are rejected;
- wrong or missing company fails closed;
- permission denial returns controlled unavailable state, not a modal exception;
- aggregate count parser fails closed on missing key, unexpected alias, `None`, non-numeric, negative, multiple aggregate rows, and malformed output;
- missing due date fails closed before count buckets;
- payment terms / split schedules fail closed until explicitly supported;
- return Purchase Invoice, debit note, supplier credit, on-hold invoice, supplier advance, Purchase Order advance, overpayment, fully paid, partially paid, and cancelled invoice cases are covered;
- future amount proof does not use Purchase Invoice outstanding totals, direct GL sums, or raw Payment Ledger row sums;
- future Payment Ledger amount adapter asserts selected company on every source row and returns no partial aggregate on invalid rows;
- no supplier/invoice/payment/voucher/account/PLE/GL identity appears in response keys or nested payloads;
- frontend guard rejects injected supplier rows, invoice rows, payment rows, native report/route/export/download/print/action shapes;
- frontend raw and nested payload guard explicitly blocks AP identity keys before runtime, including `supplier`, `supplier_name`, `supplier_id`, `purchase_invoice`, `bill_no`, `bill_date`, `payable_account`, `party`, `party_name`, `supplier_group`, `remarks`, `payment_order`, supplier bank/contact/tax fields, report/export/download/print keys, and action keys;
- AP no-effect metadata explicitly states that supplier notification, supplier statement/payment communication, Payment Request, Payment Order, payment run, supplier bank/contact exposure, and Purchase Invoice lifecycle behavior were not performed;
- static scans stay clean for raw SQL, `frappe.get_all`, `ignore_permissions`, native routes, report pass-through, export/download/print, mutation calls, email/notification/portal behavior.

## Subagent Findings Integrated

Accepted:

- Native Accounts Payable report pass-through is unsafe because it can expose supplier/voucher/report row detail.
- Purchase Invoice is a plausible future count-only source candidate, but only after due-date/company/docstatus/open-filter semantics are proven.
- Purchase Invoice outstanding amount is rejected for amount totals because installed metadata binds it to `party_account_currency`.
- Payment Ledger Entry is the only plausible future AP amount proof candidate, and only with voucher-outstanding semantics.
- Supplier rows and supplier balances remain blocked for first AP posture.
- Payment preparation wording should not imply payment authority or cash availability.
- F5B must remain proof/contract work, not runtime.

Rejected:

- Native Accounts Payable report embedding.
- Supplier worklists, Purchase Invoice worklists, Payment Entry shortcuts, payment run controls, and exports.
- Reusing AR behavior for Accounts User AP visibility without a low-count/coarsening policy.
- Treating System Manager or Executive-only roles as AP authority.
- Adding `due_soon` to first AP count runtime before basic due-date aging is proven.

Deferred:

- Accounts User AP counts.
- Auditor AP posture.
- Supplier-level visibility.
- AP amount buckets.
- Payment terms support.
- Supplier advances / Purchase Order advances.
- Return/debit-note/on-hold/overpayment semantics.
- Cash/bank planning handoff.

## Recommended Next Subphase

Proceed to `F5B Payables Source-Proof And Count Contract`.

F5B should remain docs/proof/test-contract only unless Owner/Main Control separately approves runtime. It should decide whether Purchase Invoice can be used as a count-only aggregate source under strict due-date, company, docstatus, permission, malformed-output, payment-term, return/debit-note, advance, partial-payment, on-hold, and no-row/no-identity constraints.

## Runtime Readiness

Not ready.

F5A does not approve AP runtime reads, AP UI data cards, AP count implementation, AP amount implementation, live alignment, restart, metadata reload, staging, commit, push, or protected gates.

## Boundary Confirmation

No runtime Payables reads were implemented. No Purchase Invoice, Supplier, Payment Ledger, GL Entry, Payment Entry, Bank, Account, or report business data was queried. No UI Payables data cards were added. No native reports/routes/exports/download/print were added. No payment/execution actions were added. No live alignment, restart, reload, migrate, staging, commit, push, or protected gate was performed.
