# Finance & Accounting Phase F4G Receivables Payment Ledger Aggregate Contract

Date: 2026-07-06
Status: design contract only. No runtime code, no UI change, no DocType metadata, no tests, no live alignment, no restart, no protected gate, no commit, and no push are included.

## Decision

F4G defines the future implementation contract for Accounts Manager-only, company-scoped aggregate receivables aging amount summaries using ERPNext Payment Ledger semantics.

F4G does not approve runtime amount exposure. It does not add UI amount cards, customer rows, invoice rows, voucher names, party identifiers, account rows, raw Payment Ledger rows, native reports, native routes, exports, print/download, posting, payment, reconciliation, write-off, customer communication, tax, close, or any accounting execution.

The F4F2 source proof changes the F4E source assumption:

- `Sales Invoice.outstanding_amount` is rejected for amount summaries because installed ERPNext defines it in `party_account_currency`.
- `Payment Ledger Entry.amount` is the company-currency amount basis because installed ERPNext defines it as `Company:company:default_currency`.
- ERPNext Accounts Receivable report semantics are accepted as the source model because the installed report states that report amounts are company currency unless `in_party_currency` is selected, and that the report is based on Payment Ledger Entries.
- A future implementation must not simplify this into `sum(amount) by due_date`.

## Evidence Base

Installed source inspected in `erpai_project1-backend-1`, ERPNext 16.4.1 / Frappe 16.5.0:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/doctype/payment_ledger_entry/payment_ledger_entry.json`
  - `company` is a Link to Company.
  - `account_type` is Receivable or Payable.
  - `party_type`, `party`, `voucher_type`, `voucher_no`, `against_voucher_type`, and `against_voucher_no` are identity fields and must remain internal only.
  - `amount` is Currency with options `Company:company:default_currency`.
  - `amount_in_account_currency` is Currency with options `account_currency`.
  - `due_date`, `posting_date`, and `delinked` exist.
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/report/accounts_receivable/accounts_receivable.py`
  - Lines 38-39 state the report is company currency unless party currency is selected, and that it is based on Payment Ledger Entries.
  - Lines 296-323 update voucher balances from PLE rows, choosing `ple.amount` for company-currency report mode.
  - Lines 418-423 calculate `outstanding = invoiced - paid - credit_note` and account-currency outstanding separately.
  - Lines 870-904 age final voucher balances by due date with posting-date fallback in ERPNext report logic.
  - Lines 920-955 filter PLE rows by report date, `delinked = 0`, source filters, and match conditions.
  - Lines 1007-1033 apply company and receivable account filters through the report flow.
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/utils.py`
  - `QueryPaymentLedger.get_voucher_outstandings()` lines 2381-2418 is the reusable voucher-outstanding helper.
  - Lines 2274-2379 build voucher amount and voucher outstanding CTEs from Payment Ledger Entry and return voucher-level outstandings.
  - `get_outstanding_invoices()` is not accepted as the company-currency amount source because that helper is account-currency oriented for invoice outstanding output; F4H must use a reviewed adapter that preserves company-currency `amount` semantics.

## Source Options

### Rejected: Sales Invoice Fields

`Sales Invoice.outstanding_amount` remains allowed only as the existing F4D count-open filter. It must not be summed for amount posture.

Reasons:

- installed `sales_invoice.json` defines `outstanding_amount` as Currency with options `party_account_currency`;
- no installed `base_outstanding_amount` field was found;
- `base_grand_total`, `base_paid_amount`, and `base_write_off_amount` are not current outstanding balance fields;
- summing invoice fields would misstate company-currency AR exposure in multi-currency or party-account-currency cases.

### Rejected: Direct GL Entry Aggregates

Direct GL Entry aggregation is rejected for the first amount implementation.

Reasons:

- GL Entry `debit` and `credit` are company-currency fields, but direct ledger aggregation does not provide a safe AR aging balance without voucher allocation rules;
- GL Entry rows expose account, party, voucher, and ledger detail that this workspace must not return;
- ERPNext v16 Accounts Receivable report uses Payment Ledger Entry semantics for receivable aging, not a direct GL bucket sum;
- direct GL aggregation would be a separate accounting-source design, not an F4G implementation path.

### Accepted As Future Source Contract: Payment Ledger Entry Semantics

Payment Ledger Entry is accepted as the future source basis only through voucher-outstanding semantics.

Required amount basis:

- use company-currency `Payment Ledger Entry.amount` for displayed amount totals;
- use account-currency `amount_in_account_currency` only as an internal positivity/validation companion where ERPNext semantics require it;
- never return account currency amounts to the browser in the first runtime phase;
- fail closed if company currency from F4B resolver is not `MMK` for `Mingalar Mobile Distribution Co., Ltd.` or if the selected company scope is unavailable.

Native Accounts Receivable report output must not be passed through to the browser. The report is an evidence source and semantic reference only.

## Source And Filters

Future runtime may read only this DocType family:

- `Payment Ledger Entry`, through a reviewed permission-preserving adapter. Query Builder or CTE usage is not automatically permission-preserving; the adapter must prove equivalent user permission and match-condition enforcement before any source read.

Required internal source fields:

- `company`;
- `account_type`;
- `party_type`;
- `party`, internal only for distinct-customer suppression;
- `voucher_type`, internal only for voucher grouping and final invoice filtering;
- `voucher_no`, internal only for voucher grouping;
- `against_voucher_type`, internal only for voucher outstanding semantics;
- `against_voucher_no`, internal only for voucher outstanding semantics;
- `posting_date`;
- `due_date`;
- `amount`, company currency basis;
- `amount_in_account_currency`, internal validation and ERPNext outstanding compatibility;
- `account_currency`, internal validation only;
- `delinked`.

Required filters before aggregation:

- selected company equals the F4B resolver `selected_company.name`;
- resolver-selected currency equals `MMK` for the current site;
- `account_type = Receivable`;
- `party_type = Customer`;
- `delinked = 0`;
- `posting_date <= backend_as_of_date`;
- report/future-payment mode is off for first runtime;
- final voucher rows must represent Sales Invoice receivables after voucher-outstanding calculation;
- returned outstanding must be greater than zero by ERPNext voucher-outstanding semantics;
- browser-supplied company, currency, account, customer, voucher, due-date, and report filters are not trusted in the first runtime phase.

The future adapter must not prefilter only `voucher_type = Sales Invoice` at the raw PLE row level, because that can drop Payment Entry, Journal Entry, and credit/return ledger rows required to reduce invoice outstanding. Sales Invoice filtering happens on the final voucher-outstanding result, not before linked allocations are processed.

Fields explicitly forbidden to return:

- raw Payment Ledger row names;
- voucher names;
- against voucher names;
- customer names or IDs;
- party names or IDs;
- account names;
- cost centers or projects;
- due dates or posting dates as rows;
- account currency values;
- remarks;
- GL rows;
- report rows;
- native routes, reports, exports, print/download links, or action keys.

## Permission Model

Future amount runtime must pass all gates before reading source data:

- authenticated Finance request;
- F4B resolver returns `state=scoped`;
- F4B role category is exactly `manager` from `Accounts Manager`;
- selected company is from the server-side resolver, not user default or browser input;
- `System Manager` alone is not Finance data authority;
- `Executive Approver` alone is not Finance data authority;
- `Accounts User` receives no amount values;
- `Auditor` receives no amount values until a later audit scope policy approves it;
- source read permission for `Payment Ledger Entry` is verified without loading rows;
- no `ignore_permissions`;
- no `frappe.get_all`;
- no direct `frappe.db.sql` in the custom Finance adapter;
- no `frappe.get_doc` for invoices, customers, accounts, Payment Ledger rows, GL Entry rows, Payment Entry, or Journal Entry;
- no native Accounts Receivable report API pass-through;
- no native `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, query-report, export, print, or download targets.

ERPNext's own report source contains raw SQL and row-output paths. F4G accepts those as evidence only. A future Finance implementation must use a reviewed adapter and must prove it does not pass native report rows, raw SQL behavior, or permission-bypassing query paths through the custom workspace boundary. PLE read permission alone is not enough because native metadata grants read/report/export/print/email/share more broadly than this custom workspace allows.

## Aggregation Semantics

Future implementation must calculate voucher-level outstanding before aging and bucket aggregation.

Required semantic model:

1. Gather receivable Payment Ledger Entry rows for the selected company and as-of date.
2. Group invoice-side voucher amount by voucher identity, customer, account, posting date, due date, and currency metadata.
3. Group outstanding-side allocation by against-voucher identity, customer, and account.
4. Join voucher amount to outstanding amount by account, voucher type, voucher number, party type, and party, matching ERPNext `QueryPaymentLedger` semantics.
5. Calculate final company-currency outstanding from `Payment Ledger Entry.amount` semantics.
6. Use account-currency outstanding only as an internal positivity/compatibility companion; do not display it.
7. Include only final Sales Invoice voucher results with positive outstanding.
8. Apply aging bucket assignment to the final voucher balance, not to raw Payment Ledger rows.
9. Aggregate bucket count, unsuppressed amount total, and suppression state.
10. Return only aggregate bucket values after suppression.

What must not be simplified:

- no `sum(Payment Ledger Entry.amount) by due_date`;
- no `sum(Sales Invoice.outstanding_amount)`;
- no raw Payment Ledger row trimming after fetching identities for the browser;
- no native Accounts Receivable report pass-through;
- no direct GL Entry bucket sum;
- no browser-driven company/currency/source filter;
- no customer or invoice drilldown.

Payments and partial payments:

- Payment Entry and Journal Entry PLE rows linked against a Sales Invoice must reduce final voucher outstanding through voucher-outstanding semantics.
- Partial payments reduce only the outstanding amount for the final voucher, not the original invoice amount.
- Future runtime must test both full and partial payment examples.

Credit notes, returns, write-offs, and adjustments:

- Linked credits and write-offs that ERPNext records through Payment Ledger Entry must net into final voucher outstanding through the same voucher-outstanding calculation.
- Standalone negative or zero outstanding vouchers are excluded from amount buckets.
- The first runtime must not expose separate credit-note, return, write-off, or adjustment categories.
- If a return/credit scenario cannot be represented by the tested voucher-outstanding adapter, amount posture returns unavailable rather than a partial total.

Payment terms:

- Payment-term splitting is excluded in the first F4H runtime unless Owner/Main Control separately approves it.
- The installed AR report can split invoices by payment terms, but that creates row-level semantics and overpayment edge cases. F4G keeps the first amount runtime at voucher-level aging only.
- If the site requires payment-term aging for receivables, F4H must stop and request a separate payment-schedule policy.

Future payments:

- Future payment columns and future payment allocation are excluded.
- The as-of filter must use `posting_date <= backend_as_of_date`.
- Future-dated payments must not reduce current as-of outstanding until their posting date is within scope.

## Aging Semantics

F4G amount buckets align with F4D count labels:

- `current`: due date on or after the backend as-of date;
- `overdue_1_30`: 1-30 days overdue;
- `overdue_31_60`: 31-60 days overdue;
- `overdue_61_90`: 61-90 days overdue;
- `overdue_over_90`: more than 90 days overdue.

Aging basis:

- use backend-defined `as_of_date` only;
- use due date from final voucher semantics where present;
- if due date is missing, ERPNext report falls back to posting date, but F4H must explicitly test this before enabling fallback;
- if missing due-date fallback is not tested, return amount posture unavailable with reason `missing_due_date_policy_not_ready`;
- future due balances belong in `current`, not overdue;
- no due-date row values are returned.

F4D count posture currently uses Sales Invoice due-date count semantics. F4H must document and test any known differences between F4D count buckets and Payment Ledger voucher-count buckets before showing counts and amount totals together. If counts and amounts cannot be reconciled safely, F4H must keep F4D counts and F4H amounts as separately labeled postures or stop for policy review.

## Suppression Policy

Amount totals are more sensitive than counts and must pass small-population suppression.

Initial thresholds:

- `amount_min_bucket_voucher_count = 3`;
- `amount_min_bucket_distinct_customer_count = 3`.

Rules:

- bucket count `0`: may return count `0` and amount `0 MMK`;
- bucket count `1` or `2`: return bucket count only, suppress amount with browser reason `suppressed_low_population`;
- bucket count `3+` with fewer than 3 internal distinct customers: return bucket count only, suppress amount with browser reason `suppressed_low_population`;
- bucket count `3+` with at least 3 internal distinct customers: return bucket amount if all other gates pass;
- distinct customer count is internal only and must not be returned;
- customer concentration, largest customer, largest voucher, oldest voucher, percentages, averages, and customer share are blocked;
- no grand total is returned if any bucket is suppressed;
- no subtraction-friendly totals are returned when suppression is active.

Suppressed bucket response may include only:

- bucket key;
- `suppressed=true`;
- generic browser reason code `suppressed_low_population`;
- count if count policy already allows it for Accounts Manager.

Specific internal causes such as low voucher count or low customer diversity may be logged or tested server-side, but the browser must not receive distinct-customer counts, diversity hints, or customer-concentration reason details unless Owner/Main Control separately accepts that leakage tradeoff.

## Response Contract

Allowed future response keys:

- `phase`;
- `state`;
- `company_scope`;
- `as_of_date`;
- `currency`;
- `bucket_labels`;
- `bucket_counts`;
- `bucket_amounts` for unsuppressed buckets only;
- `suppressed_buckets` with bucket keys and the generic non-sensitive browser reason `suppressed_low_population`;
- `grand_total` only when every bucket is unsuppressed and currency/source gates are clean;
- `policy`;
- `no_effect`;
- `rows_returned=false`;
- `amounts_are_aggregate=true`;
- `documents_returned=false`;
- `runtime_payment_ledger_amount_summary_enabled`.

Explicitly blocked response keys:

- `rows` carrying source records;
- `documents` carrying source records;
- `metrics` carrying arbitrary financial rows;
- `customers`;
- `customer`;
- `customer_name`;
- `party`;
- `party_name`;
- `invoice`;
- `invoice_id`;
- `invoice_name`;
- `voucher`;
- `voucher_no`;
- `against_voucher_no`;
- `account`;
- `gl_entry`;
- `payment_ledger_entry`;
- `due_date` as a row field;
- `posting_date` as a row field;
- `route`;
- `report`;
- `export`;
- `print`;
- `download`;
- `action`;
- native report output rows.

No-effect flags must continue to show no document creation/update, no GL Entry creation, no Journal Entry creation, no Payment Entry creation, no reconciliation, no tax filing, no period close, no notification, no export, no native route opening, no report run, no email, no portal action, and no user/role mutation.

## Failure Modes

Future runtime must fail closed to an unavailable state with no amount values for:

- no Accounts Manager role;
- Accounts User role without manager role;
- System Manager only;
- Executive Approver only;
- Auditor without approved audit scope;
- non-finance roles;
- F4B resolver restricted, unavailable, or selection-required;
- selected company missing or outside allowed scope;
- selected company currency not `MMK` for current site policy;
- `Payment Ledger Entry` read permission denied or permission checker unavailable;
- source adapter unavailable;
- source version drift from ERPNext 16.4.1 semantics;
- required PLE fields missing;
- report/helper logic drift detected by source-signature tests;
- raw report pass-through required to compute values;
- payment-term aging required but not approved;
- missing due-date fallback not tested;
- mixed or ambiguous currency basis;
- low voucher population;
- low internal customer diversity;
- unexpected negative or zero outstanding behavior;
- any exception during source calculation.

Failure payloads must include no bucket amounts, no grand total, no source rows, no document identifiers, and no native route/report/export/print/download/action keys.

## Future Runtime Test Contract

F4H implementation, if approved, must add focused tests before any runtime amount exposure.

Required source and permission tests:

- Accounts Manager with scoped F4B resolver and `Payment Ledger Entry` read permission can reach the amount adapter;
- Accounts Manager without source read permission receives unavailable and no source query runs;
- every denial gate asserts the amount adapter is not called, including Accounts User, System Manager-only, Executive-only, Auditor without policy, non-finance roles, unresolved company, outside-scope company, source permission denied, and non-MMK company;
- Accounts User receives no amount values;
- System Manager-only receives no Finance data;
- Executive Approver-only receives no Finance data;
- Auditor receives no amount values unless a later audit scope policy explicitly approves it;
- Sales, Purchase, Warehouse, and Stock roles receive no amount values;
- requested company outside scope is denied and no source query runs;
- user default company alone does not authorize amount summaries;
- browser-supplied company/currency/account/customer/voucher filters are ignored or rejected.

Required aggregation tests:

- manager happy path with mocked Payment Ledger entries returns only aggregate bucket amounts;
- invoice amount is reduced by partial Payment Entry allocation;
- invoice amount is reduced by partial Journal Entry allocation;
- linked credit note or return ledger behavior nets into final voucher outstanding or returns unavailable if unsupported;
- write-off/adjustment ledger behavior nets into final voucher outstanding or returns unavailable if unsupported;
- zero outstanding vouchers are excluded;
- negative outstanding vouchers are excluded;
- final voucher filtering keeps Sales Invoice receivables only after allocation semantics, not by raw-row prefilter;
- future-dated payments do not reduce as-of outstanding;
- payment-term split requirement returns unavailable unless explicitly approved and tested;
- source adapter does not return raw PLE rows to response.

Required aging tests:

- due date on or after as-of maps to `current`;
- 1, 30, 31, 60, 61, 90, and 91 day boundaries map correctly;
- missing due date uses tested posting-date fallback or returns unavailable;
- future due balances remain current;
- F4D count labels and F4H amount labels are stable and not misleading.

Required suppression tests:

- bucket count 0 returns amount 0 MMK only for that bucket;
- bucket count 1 or 2 suppresses amount;
- bucket count 3+ with fewer than 3 distinct internal customers suppresses amount;
- distinct customer count is never returned;
- any suppressed bucket removes grand total;
- no percentages, averages, largest customer, largest invoice, or concentration hints are returned.

Required response tests:

- exact allowed top-level keys only;
- no customer, party, invoice, voucher, account, GL, or Payment Ledger identifiers;
- no rows, documents, report rows, native route keys, export keys, print/download keys, or action keys;
- no account-currency amount values returned;
- suppression responses use only generic browser reason `suppressed_low_population` unless Owner/Main Control approves more specific visible reasons;
- all no-effect flags remain false;
- unavailable states return no amounts.

Required source-drift tests:

- installed `Payment Ledger Entry.amount` still has options `Company:company:default_currency`;
- installed `Payment Ledger Entry.amount_in_account_currency` still has options `account_currency`;
- installed AR report still states company-currency report mode unless party currency is selected;
- installed `QueryPaymentLedger` or reviewed adapter still calculates voucher outstanding before aging;
- `get_outstanding_invoices()` remains blocked for company-currency summary output unless a later source proof reverses that decision;
- source permission and match-condition enforcement remain present for any Query Builder or CTE path;
- if any source signature changes, amount runtime returns unavailable until reviewed.

## Static And Boundary Scans

F4H must include static scans for:

- `frappe.get_all`;
- `frappe.db.sql`;
- `ignore_permissions`;
- `frappe.get_doc`;
- report API pass-through;
- native `/app`;
- native `/desk/Form`;
- native `/desk/List`;
- native `/desk/Report`;
- `query-report`;
- `export`;
- `print`;
- `download`;
- `sendmail`;
- `notification`;
- `portal`;
- `save`;
- `submit`;
- `cancel`;
- `delete`;
- `amend`;
- `set_value`;
- `enqueue`.

Allowed hits must be limited to blocked-policy copy, no-effect flag names, static-test assertions, source evidence references, or explicit response-denial tests. No future runtime path may use these to expose native Finance execution, reports, exports, routes, notifications, or accounting mutation.

## Recommended Next Phase

Recommended next phase: `F4H Receivables Payment Ledger Amount Summary Implementation`, but only after Owner/Main Control accepts this contract and explicitly approves implementation.

F4H should remain narrow:

- Accounts Manager only;
- one selected F4B company only;
- Payment Ledger voucher-outstanding semantics only;
- aggregate bucket amounts only after suppression;
- no row/identity/report/export/native route behavior;
- exact test suite and static scans from this contract;
- no UI redesign, at most a minimal existing receivables posture enhancement after backend tests pass.

If Owner/Main Control does not accept the Payment Ledger adapter risk, the safer next phase is F5 Payables count-only posture, not AR amount runtime.

## Boundary Confirmation

F4G is docs-only. It does not implement runtime amount exposure, UI amount cards, customer or invoice rows, voucher identifiers, account rows, GL rows, Payment Ledger rows, native reports, native routes, exports, print/download, posting, payment, reconciliation, write-off, notification, email, portal behavior, DocType metadata, user/role/permission mutation, live alignment, restart, migration, protected gate, commit, or push.
