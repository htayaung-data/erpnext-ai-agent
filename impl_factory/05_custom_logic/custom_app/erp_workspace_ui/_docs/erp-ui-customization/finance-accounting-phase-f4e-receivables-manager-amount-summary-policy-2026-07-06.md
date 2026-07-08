# Finance & Accounting Phase F4E Receivables Manager Amount Summary Policy

Date: 2026-07-06
Status: design policy only. No runtime code, no UI change, no DocType metadata, no tests, no live alignment, no restart, no protected gate, no commit, and no push are included.

## Decision

Recommended next phase: `F4E Receivables Manager Amount Summary Policy`.

F4E should define, but not implement, Accounts Manager-only aggregate receivables amount summaries by aging bucket. This is the next safest and most useful step after F4D count-only receivables posture.

F4E must not add customer rows, invoice rows, due-date rows, status rows, customer names, invoice identifiers, native reports, native routes, exports, print/download, posting, payment, reconciliation, write-off, customer communication, tax, close, or any accounting execution.

## Why This Sequence

F4D count-only posture is safe but only partially useful. It tells a Finance manager how many open receivables exist in each aging bucket, but not the financial exposure or cash-flow risk. Mature ERP finance workspaces commonly treat AR aging as a manager/accountant visibility surface with bucketed outstanding balances, while keeping posting and payment execution separate.

F4E should finish the receivables visibility ladder before broadening to payables. Payables count posture is a good future step, but starting AP now would add a second source family before the AR amount/currency/suppression policy is settled. Accounts User count coarsening is also important, but it is less useful than manager amount posture and requires separate low-count UX/role decisions.

External ERP practice comparison reviewed:

- Microsoft Business Central exposes accountant experiences and aged accounts receivable reporting as accountant-facing work surfaces: https://learn.microsoft.com/en-us/dynamics365/business-central/finance-accounting and https://learn.microsoft.com/en-us/dynamics365/business-central/reports/report-120
- Oracle Receivables aging reports are used to review outstanding receivable balances and can support summary or detail analysis: https://docs.oracle.com/en/cloud/saas/financials/25c/faofc/overview-of-the-receivables-aging-by-general-ledger-account.html
- Odoo accounting includes aged receivable and aged payable reports as finance reporting surfaces: https://www.odoo.com/documentation/19.0/applications/finance/accounting/reporting.html
- NetSuite describes AR aging as grouping unpaid receivables into aging buckets to assess receivables quality: https://www.netsuite.com/portal/resource/articles/accounting/accounts-receivable-aging.shtml

The project should not copy native ERP reports into the browser. The relevant practice is the separation of scoped financial visibility from execution, not report pass-through.

## Chosen Path

Chosen: `F4E Receivables Manager Amount Summary Policy`.

Rejected for immediate next phase:

- `F4E Accounts User Low-Count/Coarsening Policy`: defer. Accounts User should not receive raw counts or amounts until a normal-user operational model is designed. Coarsening thresholds need owner review and should not be rushed just to expose more data.
- `F5 Payables Posture Policy`: defer. Payables count posture is valid, but broadening to AP before completing AR amount/currency policy adds another source family and does not solve the current AR manager exposure gap.
- Customer or invoice visibility: reject. Customer-level and invoice-level visibility are stronger business/privacy exposure and remain separate future approvals.

## Allowed F4E Policy Surface

F4E may define policy for future runtime amount summaries with these limits:

- role: `Accounts Manager` only;
- company scope: selected company from the F4B resolver only;
- source: `Sales Invoice` only unless a future design rejects it for a safer source;
- source permission: no-row `Sales Invoice` read permission gate from F4D or stronger;
- aggregation: aging bucket totals only;
- amount basis: company currency `MMK` for the current single-company site;
- response: no customer keys, invoice keys, row arrays, document arrays, native route keys, report keys, export keys, print/download keys, or action keys;
- effect: no posting, payment, reconciliation, write-off, customer communication, tax, close, or mutation.

F4E remains design-only. Runtime implementation would require a later explicit approval.

## Amount And Currency Policy

The current site policy is company currency `MMK` only for `Mingalar Mobile Distribution Co., Ltd.`.

Future runtime must return unavailable, not partial amounts, if currency basis is ambiguous.

Required currency rules:

- Use the F4B resolver company currency as the presentation basis.
- Display only `MMK` company-currency amount summaries for the current site.
- Do not display mixed-currency totals.
- Do not silently convert between invoice currency, party currency, account currency, base currency, and company presentation currency.
- Do not include non-MMK receivables in an MMK total.
- If any open receivable in the scoped company is not proven to be compatible with the approved `MMK` basis, return amount summary unavailable while keeping F4D count-only posture available.
- If ERPNext `Sales Invoice.outstanding_amount` cannot be proven to represent the accepted company-currency basis for all included invoices, stop implementation and request a source-field policy decision.
- Amounts must be rounded/formatted by an approved backend policy. Do not let browser formatting decide accounting precision.
- No grand total should be displayed in the first amount phase unless all displayed buckets are unsuppressed and currency basis is clean. Bucket amounts are sufficient for F4E.

## Small-Population Suppression

Bucket amount totals can indirectly reveal a customer or invoice amount when a bucket has very few open receivables. F4E must require suppression before runtime.

Recommended first thresholds:

- `amount_min_bucket_invoice_count = 3`.
- `amount_min_bucket_distinct_customer_count = 3`, checked internally only.

Rules:

- Bucket count `0`: show count `0` and amount `0 MMK`.
- Bucket invoice count `1` or `2`: show the F4D count, suppress the amount value, and mark the bucket as `suppressed_low_invoice_population`.
- Bucket invoice count `3+` but internal distinct customer count below `3`: show the F4D count, suppress the amount value, and mark the bucket as `suppressed_low_customer_diversity`.
- Bucket invoice count `3+` and internal distinct customer count `3+`: amount total may be shown if all other gates pass.
- Distinct customer checks are allowed only as internal aggregate/suppression gates. The browser must not receive customer names, customer IDs, customer counts, customer shares, or top-customer indicators.
- Do not show a grand total if any bucket is suppressed, because the grand total can allow subtraction inference.
- Do not show percentages, averages, largest invoice, oldest invoice, customer count, customer share, or top-customer indicators in F4E.
- Do not reveal whether one customer accounts for all invoices in a bucket.

The thresholds may be changed later only by Owner/Main Control after Security/Data review.

## Source And Filter Semantics

Future runtime should extend the F4D source contract, not replace it.

Required filters:

- `company` equals the selected allowed company from the F4B resolver;
- `docstatus = 1`;
- `outstanding_amount > 0`;
- `is_return = 0`;
- `return_against` is not set;
- due-date bucket filter based on backend as-of date;
- company currency compatibility equals accepted `MMK` policy.

Potential future aggregate fields:

- `count(name) as count`;
- a reviewed aggregate sum field only after ERPNext field semantics are proven safe for `MMK` company-currency basis.

Forbidden source behavior:

- no `frappe.get_all`;
- no raw SQL;
- no `ignore_permissions`;
- no `frappe.get_doc`;
- no native Accounts Receivable report pass-through;
- no report API output in the browser;
- no customer, invoice, payment schedule, line item, or status rows fetched and trimmed later.

## Response Contract For Future Implementation

F4E runtime, if later approved, should return exact keys only. Proposed response keys:

- `phase`;
- `state`;
- `company_scope`;
- `as_of_date`;
- `bucket_labels`;
- `bucket_counts`;
- `bucket_amounts` for unsuppressed buckets only;
- `suppressed_buckets` with bucket keys and non-sensitive reasons;
- `currency_policy`;
- `policy`;
- `no_effect`;
- `rows_returned=false`;
- `amounts_are_aggregate=true`;
- `documents_returned=false`;
- `runtime_amount_summary_enabled`.

Blocked response keys:

- `rows`;
- `documents`;
- `metrics` if it carries arbitrary financial values;
- `customers`;
- `customer`;
- `customer_name`;
- `invoice`;
- `invoice_id`;
- `invoice_name`;
- `due_date` as a row field;
- `status` as a row field;
- `route`;
- `report`;
- `export`;
- `print`;
- `download`;
- `action`.

## Tests Required Before Runtime

Future implementation must include tests for:

- Accounts Manager with scoped F4B resolver, `Sales Invoice` read permission, clean MMK currency basis, and bucket counts above threshold returns aggregate bucket amounts only;
- Accounts Manager with source permission denied returns no amounts and does not query amount aggregates;
- Accounts Manager with resolver unavailable, restricted, or selection-required returns no amounts;
- user default company alone does not authorize amount summaries;
- Accounts User receives no raw counts or amount totals;
- System Manager-only, Executive-only, Auditor without approved audit scope, Sales/Purchase/Warehouse roles receive no amount summary;
- bucket count `0` returns amount `0 MMK` only for that bucket;
- bucket count `1` or `2` suppresses amount value;
- no grand total is returned when any bucket is suppressed;
- internal distinct-customer suppression is enforced without returning customer names, customer identifiers, customer counts, customer shares, or top-customer indicators;
- non-MMK or ambiguous currency basis returns amount summary unavailable;
- all required filters are present and use only the resolver-selected company;
- no rows, documents, customer names, invoice IDs, due dates, statuses, report keys, route keys, export keys, print/download keys, or action keys are returned;
- static scan blocks forbidden APIs, native routes, report APIs, exports, mutation APIs, email/notification/portal behavior, and execution labels.

## UI Contract For Future Runtime

F4E does not redesign Finance Control Desk.

If later implemented, the UI should add at most a calm amount-summary layer to the existing receivables posture card or a tightly scoped summary panel. It must follow the shared workspace UI grammar used by Sales, Procurement, and Warehouse: stable page shell, compact command posture, consistent spacing, no blank first-load states, predictable refresh/unavailable states, minimal premium copy, and no native route exposure.

Finance should not copy page-local Warehouse, Sales, or Procurement classes blindly. It should reuse shared grammar and keep accounting-specific wording short and precise.

Future Finance navigation/search requirements before adding any new targets:

- define a Finance-specific target allowlist before sidebar/search can return anything beyond declared productized Finance page routes;
- keep native Form, List, Report, Query Report, export, print/download, email/notification, payment, reconciliation, posting, and close targets blocked even if the shared sidebar runtime can handle those target kinds for other workspaces;
- add a stale-response/request-token guard before Finance receives company selectors, filters, or multiple refreshable panels, so older async responses cannot overwrite newer scoped responses;
- keep posture cards non-clickable until productized Finance detail routes exist in the registry and governance manifest;
- replace internal phase labels in visible owner-facing copy with business wording such as `Receivables counts only`, `Amounts unavailable`, and `No reports or exports`.

## Deferred Decisions

Deferred after F4E design:

- Accounts User count coarsening and normal-user operational queue design;
- F5 Payables count posture, which should start count-only, manager-scoped, `Purchase Invoice`-only, with supplier/invoice/amounts blocked unless separately approved;
- Finance registry/status metadata cleanup after source/runtime phase labels are reconciled;
- customer-level AR balances;
- invoice-level AR rows;
- payment schedule aging;
- mixed-currency totals or conversion policy;
- Auditor amount visibility;
- Owner/Executive amount visibility;
- exports, print/download, reports, native routes, custom review/request records, and execution workflows.

## Boundary

F4E design does not implement runtime code. It does not approve rows, customer names, invoice identifiers, amounts in the live payload, native reports, native routes, exports, print/download, posting, payment, reconciliation, write-off, tax, close, notifications, email, portal behavior, DocType metadata, user/role/permission mutation, live alignment, restart, migration, protected gate, commit, or push.
