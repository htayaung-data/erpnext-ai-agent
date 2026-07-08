# Finance & Accounting F4A Receivables Visibility Policy - 2026-07-04

Status: policy and permission design only. This document does not approve AR runtime data, report calls, accounting execution, exports, native ERP routes, customer notification, live alignment, restart, commit, or push.

## Decision

F4 stopped correctly. Receivables runtime visibility is not approved until company authorization, DocType read policy, field allowlists, currency display policy, and Owner/Executive role mapping are explicitly implemented, tested, and accepted.

F4A approves a policy artifact only. It keeps Cycle 1 Finance & Accounting in a controlled foundation posture and defines the requirements for a future F4B implementation.

## Why F4 Stopped

F3 introduced a safe read-only Finance overview shell without accounting rows, amounts, customer balances, supplier balances, report calls, exports, or native route exposure. F4 would cross into Accounts Receivable visibility and therefore needs decisions that F3 intentionally deferred:

- the user's default company is display context only and is not authorization;
- multi-company access must not leak totals across companies;
- Accounts Receivable data can reveal customers, invoice identifiers, due dates, aging, credit posture, write-off candidates, and commercial exposure;
- currency and amount display is sensitive even when summarized;
- ERPNext Accounts Receivable report output is useful but can expose row-level customer and invoice data if passed through directly;
- Owner/Executive visibility is a business decision, not an assumed native ERPNext role grant;
- native report/Form/List routes and export affordances must remain blocked.

## Company Scope Policy

Receivables data must be scoped by an explicit allowed-company authorization function before any AR counts, buckets, amounts, customers, invoices, or report-derived fields are returned.

Required rules:

- Determine allowed companies from permission-aware ERPNext company access, not from the user default company alone.
- Treat the user default company only as a preferred filter or display hint after it is proven to be within the allowed-company set.
- If exactly one company is allowed, use that company as the default F4B company context.
- If multiple companies are allowed, do not aggregate across companies by default. Require an explicit selected company or an Owner-approved aggregate policy before showing AR posture.
- A future multi-company selector may show only companies that the backend has already authorized for the same AR source and permission path. It may return display labels and opaque/backend-validated selection keys only; it must not return an all-company option, hidden broad company lists, accounting dimensions, or cross-company totals.
- If no company is allowed, return a restricted or unavailable state with no AR rows, counts, amounts, company lists, customers, invoices, routes, reports, or export controls.
- Never return hidden company identifiers, accounting dimensions, or cross-company totals to make UI filtering easier.
- All future F4B backend responses must include a no-effect marker and must declare the selected company scope in a non-sensitive way.

F4B is not ready until this company authorization policy is implemented and covered by tests for no-company, one-company, multi-company, requested-company-outside-scope, broad Company-read-but-no-AR-read, and default-company-not-allowed cases.

## Role Scope Policy

Native ERPNext roles and any custom Finance roles must be treated separately. A proposed custom role is not assumed to exist until added through an approved role/governance phase.

| Role | First-cycle AR visibility policy | Notes |
| --- | --- | --- |
| Accounts User | Future candidate for Tier 0, Tier 1, and Tier 2 after company, permission-preserving aggregate source, DocType read, and Owner checks pass. | Do not assume customer, amount, invoice, or report access. Tier 2 is future-only and count-only. |
| Accounts Manager | Future candidate for Tier 0, Tier 1, and Tier 2 after company and DocType read checks pass. | Amounts, customer balances, and invoice rows still need separate approval. |
| Auditor | Future candidate for read-only Tier 0, Tier 1, and possibly Tier 2 after company and DocType read checks pass. | Must remain no-effect and non-execution. |
| System Manager | Shell access only by default. | System administration role is not automatically AR data ownership. |
| Owner / Executive | Unmapped and blocked for AR data by default. | Requires explicit Owner/Main Control decision for aggregate-only or broader access. |
| Finance User / Finance Manager | Proposed custom roles only. | Must not be referenced as existing native roles unless created and approved later. |
| Non-finance roles | Restricted. | May see only restricted shell copy, no AR posture data. |

Role alone is never enough for AR data. Future F4B must require all of the following:

- workspace role eligibility;
- allowed-company authorization;
- permission-aware read access to the source DocType or approved report source;
- field allowlist enforcement;
- no native route/report/export/execution affordance.

## Visibility Tiers

| Tier | Description | F4A decision | Rationale |
| --- | --- | --- | --- |
| Tier 0 | No AR data, posture only. | Approved now. | Matches F3 foundation posture and can explain that AR visibility is pending. |
| Tier 1 | Aggregate counts only. | Future only. | Requires company authorization, DocType read policy, exact field allowlist, and count semantics. |
| Tier 2 | Aging buckets with counts. | Future only. | Requires aging definition, as-of date, company authorization, and no amount leakage. |
| Tier 3 | Monetary amounts by aging bucket. | Blocked. | Requires currency policy, amount sensitivity decision, and Owner approval. |
| Tier 4 | Customer-level balances. | Blocked. | Reveals customer exposure and collection posture. |
| Tier 5 | Invoice-level rows. | Blocked. | Reveals invoices, due dates, statuses, identifiers, and lifecycle context. |

Tier 0 must remain boundary/status copy only. It must not use placeholder zeroes, empty charts, disabled metric cards, fake aging graphics, or future-looking controls.

F4B may reopen only Tier 1 and Tier 2 if the backend contract is implemented and accepted. Tier 3, Tier 4, and Tier 5 remain outside the first Receivables posture implementation.

## Field Allowlist Policy

Future F4B responses must use explicit response keys. Returning whole ERPNext documents, report rows, dynamic report column payloads, or pass-through DocType fields is not allowed.

| Field | F4A decision | Notes |
| --- | --- | --- |
| company label | Future only | Allowed only after company authorization. Prefer display label, not hidden broad company lists. |
| selected company key | Future only | Allowed only when it is the authorized selected scope. |
| as-of date | Future only | Required for aging semantics; must be generated by backend policy. |
| aging bucket labels | Future only | Labels only, such as current/overdue ranges, after aging policy is accepted. |
| counts | Future only | Counts may be allowed in Tier 1/Tier 2 after source semantics are tested. |
| amount fields | Blocked | No totals, balances, paid amounts, outstanding amounts, credit notes, write-off amounts, or base currency amounts. |
| currency | Blocked | No currency code/symbol until amount and currency display policy is approved. |
| customer name | Blocked | Customer identity is commercial data. |
| customer group | Blocked | Can reveal segmentation and collection posture. |
| invoice identifiers | Blocked | No Sales Invoice names, references, external IDs, or links. |
| due date | Blocked | Row-level collection sensitivity. |
| status | Blocked for rows | Aggregate status definitions may be reconsidered later. |
| Sales Invoice line fields | Blocked | No item, quantity, rate, tax, discount, warehouse, or margin signals. |
| native route target | Blocked | No Form/List/report route strings. |
| export/download/print key | Blocked | No exportable datasets or print affordances. |

Tests for F4B must assert the exact allowed response keys and fail if unexpected keys are introduced. Counts also need explicit semantics before implementation: submitted/cancelled invoice handling, outstanding-greater-than-zero filtering, returns or credit note handling, payment allocation timing, payment schedule basis, timezone, as-of date rules, and low-count suppression or withholding thresholds.

## ERPNext Source Classification

This classification identifies possible future sources. It does not approve implementation.

| Source | Possible read-only use | F4A classification | Lifecycle and leakage risk |
| --- | --- | --- | --- |
| Sales Invoice | Future aggregate count source after permission and company checks. | Future only for Tier 1/Tier 2. | Create/save/submit/cancel/amend, customer exposure, due dates, status, outstanding amount, write-off/payment links. |
| Accounts Receivable report | Future reference for aging semantics. | Not approved as pass-through source. | Report output can expose customers, invoice rows, amounts, currencies, territories, salesperson, routes, and export-ready data. |
| Accounts Receivable Summary report | Future reference for semantics only. | Not approved as pass-through source. | Summary output can still reveal amounts, currencies, parties, and export-ready report data. |
| Customer | Future research only. | Blocked for first Receivables posture pass. | Customer identity, group, credit posture, territory, payment terms, contact context. |
| Payment Entry | None for F4B. | Blocked. | Payment lifecycle, allocation, submit/cancel, reconciliation and ledger impact. |
| Payment Request | None for F4B. | Blocked. | Payment link/request lifecycle, external customer communication, and payment collection exposure. |
| Dunning / Process Statement Of Accounts | None for F4B. | Blocked. | Collection notices, statements, email generation, customer communication, and external action risk. |
| Communication / Email Queue | None for F4B. | Blocked. | Email/notification delivery and customer/supplier external action risk. |
| GL Entry | None for F4B. | Blocked. | Ledger detail, account balances, posting exposure, reversal/amendment context. |
| Journal Entry | None for F4B. | Blocked. | Adjustment and write-off lifecycle, posting authority risk. |
| Payment Ledger / outstanding data | Future research only. | Not approved until source behavior is verified. | May expose allocations, parties, invoice references, payments, and balances. |
| Sales Invoice Item | None for F4B. | Blocked. | Line detail reveals product, tax, margin, warehouse, discounts, and customer terms. |

F4B should prefer a minimal permission-respecting backend query for approved aggregate count semantics after source contract approval. Native ERPNext Accounts Receivable report output must not be passed directly to the browser in Cycle 1.

## Blocked Actions And Routes

The following remain blocked in F4A and all F4B proposals unless separately approved in a future execution phase:

- Sales Invoice create, save, submit, cancel, amend, delete, duplicate, or payment allocation;
- Payment Entry create, save, submit, cancel, amend, delete, allocate, or unallocate;
- Journal Entry create, save, submit, cancel, amend, delete, reversal, adjustment, or write-off;
- GL Entry mutation or ledger adjustment;
- Payment Reconciliation mutation;
- write-off, credit note, debit note, dunning, Process Statement Of Accounts, customer statements, collection reminder, payment link, Payment Request, customer email, Communication, Email Queue, notification, portal, or external action;
- native ERPNext Form, List, Query Report, Script Report, General Ledger, Accounts Receivable, Sales Invoice, Payment Entry, Journal Entry, Customer, or print routes;
- export, download, print, clipboard copy of financial datasets, or API pass-through for browser export.

## Future F4B Backend Criteria

F4B may not start until the implementation plan includes backend tests for these criteria:

- an allowed-company function exists and is used before any AR source read;
- default company is treated as preferred filter only and rejected if not authorized;
- no allowed company returns restricted/unavailable state with no AR data keys;
- multi-company access is explicit and tested, with no default cross-company aggregate leakage;
- source DocType/report permission checks are explicit and tested for denied users;
- aggregate reads preserve user permissions and company filters; generic DocType read permission is not enough if the aggregate path can bypass row-level or company restrictions;
- response payload is an exact allowlist, not raw DocType or report output;
- source reads are also minimized by an internal source-field/query allowlist; F4B must not fetch full Sales Invoice, Customer, Payment Entry, or report rows server-side and trim them only at the browser boundary;
- Tier 1/Tier 2 data contains no amounts, currency, customer names, invoice identifiers, due dates, row status, routes, print, or export keys;
- Accounts User, Accounts Manager, Auditor, System Manager, Owner/Executive, and non-finance role behavior is tested;
- no use of `frappe.get_all` for AR business data;
- no `frappe.get_doc`, `frappe.db.get_value`, `frappe.db.get_list`, or `frappe.get_list` for AR business data unless the source-field allowlist, filters, limits, permission behavior, and leakage review are explicitly approved for F4B;
- no raw SQL unless a later security review approves a bounded, permission-preserving query;
- no `frappe.db.sql` or query-builder equivalent for AR posture unless separately reviewed;
- no `ignore_permissions`, including `ignore_permissions=True` and spacing variants;
- `frappe.get_list` is allowed only after role, company, DocType read, field allowlist, filters, and limit behavior are explicit;
- ERPNext report APIs are not used until report parameters, output columns, role checks, company filters, and export/native-route risks are reviewed;
- every successful response declares explicit F1-style no-effect metadata, including no document, GL, journal, payment, reconciliation, tax, close, notification, export, or external action effect;
- no native route/report/export/execution controls are returned.

## Future F4B Frontend Criteria

F4B frontend work must remain a narrow Receivables posture section, not a dashboard sprawl pass.

Required behavior:

- show one Receivables posture area within the Finance Control Desk;
- support loading, ready, restricted, unavailable, and empty states;
- make company scope visible only after backend authorization;
- avoid customer tables, invoice tables, financial rows, report links, native routes, and export/download/print controls;
- avoid collection, payment, reconciliation, write-off, reminder, email, notification, or portal actions;
- use small, calm boundary copy that explains that AR visibility is posture-only;
- preserve F2/F3 shell route stability and no blank first load behavior.

## Required F4B Tests And Scans

Before F4B can be accepted, focused tests and scans must prove:

- restricted users receive restricted/no-data AR state;
- allowed roles still receive no AR data without allowed-company authorization;
- no-company and multi-company cases do not leak data;
- DocType read denial returns restricted/unavailable, not partial rows;
- exact response keys match the field allowlist;
- no Tier 3, Tier 4, or Tier 5 data appears;
- no browser source includes native finance route strings;
- no browser source includes export/download/print behavior for AR;
- no browser source includes execution labels or handlers for post, pay, reconcile, close, submit, cancel, write off, remind, email, notify, portal, allocate, adjust, or journal entry behavior;
- no backend source includes AR `frappe.get_all`, `frappe.db.sql`, query-builder raw execution, raw SQL, `ignore_permissions`, `ignore_permissions=True`, insert/save/submit/cancel/delete/set_value/enqueue/email/notification calls, or ERPNext report API calls for AR posture;
- static scans cover route tokens for Form/List/Report/Query Report, Accounts Receivable and Accounts Receivable Summary report names, Sales Invoice/Payment Entry/Journal Entry/Payment Request/Dunning route strings, Process Statement Of Accounts, Communication, Email Queue, payment link/customer statement wording, and export/download/print strings in touched Finance sources.

## F4B Readiness Decision

F4B is not ready.

Reasons:

- allowed-company authorization is not implemented;
- DocType read policy for Sales Invoice or other AR sources is not implemented;
- currency and monetary visibility policy remains blocked;
- customer-level balances and invoice-level rows remain blocked;
- Owner/Executive role mapping is unresolved;
- Accounts Receivable report usage is not approved as a browser data source;
- exact Tier 1/Tier 2 response keys and tests are not yet implemented.

F4B can reopen as a narrow docs-plus-code implementation only after Owner/Main Control accepts these policies and explicitly approves Tier 1/Tier 2 aggregate count semantics.

## Boundary Confirmation

F4A implements no AR runtime data. It approves no accounting execution, posting, payment, reconciliation, write-off, Sales Invoice lifecycle behavior, Payment Entry lifecycle behavior, Journal Entry lifecycle behavior, GL mutation, native Finance route/report/export behavior, customer notification, email, portal behavior, live alignment, restart, metadata reload, protected gate, commit, or push.
