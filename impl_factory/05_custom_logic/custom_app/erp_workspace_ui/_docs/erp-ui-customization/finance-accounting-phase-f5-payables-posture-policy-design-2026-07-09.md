# Finance & Accounting Phase F5 - Payables Posture Policy / Design

Date: 2026-07-09
Status: docs-only policy/design
Workspace family: Finance & Accounting
Page label: Finance Control Desk
Current Finance AR hardening baseline: `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0` (`fix(finance): harden AR aggregate guards`)

## Decision

F5 starts Payables as policy/design only. It does not approve Payables runtime reads, Purchase Invoice queries, Supplier queries, Payment Ledger queries, GL reads, Payment Entry behavior, Payment Entry lifecycle, native reports/routes, exports, live alignment, staging, commit, push, restart, metadata reload, migration, or protected gates.

The recommended first runtime step, after separate Owner/Main Control approval, is an aggregate-only Accounts Payable count posture with strict role/company/source gates. Manager-visible AP amount buckets are deferred until a separate source proof demonstrates company-currency-safe, permission-preserving semantics.

## Baseline Reconciliation

F4R closed the initial AR posture package at commit `5231d078389568e2d6db552d1598f3bdc9aee082`, and F4R1 pushed the closure document at `50eec8ab26ea5d4eb587f63871d274d6bc139eec`. A later accepted hardening patch was pushed as `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0`. F5 treats `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0` as the current Finance AR source baseline.

That hardening matters for Payables because future AP work must not copy unsafe early AR patterns. F5 inherits these lessons:

- aggregate parser output must fail closed on malformed, missing, ambiguous, or negative data;
- source rows used for aggregate amounts must assert the resolver-selected company;
- browser payload guards must inspect raw and nested forbidden row/native/action shapes;
- default Finance landing must not grant Finance data authority by itself;
- no native report, route, export, print/download, or accounting action may be introduced by posture work.

Known unrelated dirty files remain outside F5 scope and must stay excluded from any future staging decision:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Evidence References

ERPNext/Frappe references used for this policy:

- Purchase Invoice: https://docs.frappe.io/erpnext/purchase-invoice
- Payment Entry: https://docs.frappe.io/erpnext/payment-entry
- Payment Ledger: https://docs.frappe.io/erpnext/payment_ledger
- Accounting Reports index, including Accounts Receivable and Payable: https://docs.frappe.io/erpnext/accounting-reports
- Payment Terms: https://docs.frappe.io/erpnext/payment-terms
- Process Payment Reconciliation Tool: https://docs.frappe.io/erpnext/process-payment-reconciliation-tool
- Accounts Payable report source wrapper: https://github.com/frappe/erpnext/blob/develop/erpnext/accounts/report/accounts_payable/accounts_payable.py
- Shared Accounts Receivable/Payable report source: https://github.com/frappe/erpnext/blob/develop/erpnext/accounts/report/accounts_receivable/accounts_receivable.py

External ERP benchmark references used for practical patterns:

- Microsoft Business Central payables analytics: https://learn.microsoft.com/en-us/dynamics365/business-central/payables-reports
- Microsoft Business Central Aged Accounts Payable report: https://learn.microsoft.com/en-us/dynamics365/business-central/reports/report-322
- Oracle Fusion Payables Invoice Aging Report: https://docs.oracle.com/en/cloud/saas/financials/25c/fappp/payables-invoice-aging-report.html

No live ERPNext business data was queried for F5. Local installed ERPNext source was not modified. This policy relies on official ERPNext documentation, public ERPNext source references, existing Finance F1-F4 project artifacts, and read-only source inspection of the current Finance Control Desk.

## Business Purpose

The Payables posture lane should help Finance understand supplier payment pressure without turning the Finance Control Desk into an ERPNext execution surface. The lane should answer controlled, aggregate questions:

- how much AP work pressure exists by due/overdue timing, once amount source proof is approved;
- whether supplier bills are current, due soon, overdue, or unavailable because source semantics are unsafe;
- whether payment preparation needs review, without implying payment authority;
- which AP source conditions are blocked by missing due dates, unsupported payment terms, currency ambiguity, permission denial, malformed source rows, or low-population suppression;
- what information should later hand off to cash/bank planning without exposing bank balances or starting a payment run.

The lane must not become a supplier worklist, invoice worklist, native Accounts Payable report, payment run tool, or cash forecast in the first Payables cycle.

## Role Policy

| Role | F5 policy posture | Notes |
| --- | --- | --- |
| `Accounts Manager` | First candidate for AP aggregate count visibility after F5 source gates. First candidate for manager-only amount visibility only after separate amount source proof and Owner approval. | Same manager role accepted for AR amount posture, but AP must receive its own source contract. |
| `Accounts User` | Can land on Finance Control Desk. AP counts and AP amounts remain blocked until a separate low-count/coarsening policy is approved. | Do not assume Accounts User AP counts from AR behavior. |
| `Auditor` | Deferred. No AP runtime data by default. | May be considered later as read-only audit posture, not in first AP runtime. |
| `System Manager` | Shell/admin awareness only unless explicitly paired with an approved Finance role. | System Manager alone is not Finance data authority. |
| Future Controller / Executive | Deferred custom role decision. | Executive approval does not imply supplier liability visibility. |
| Non-Finance roles | Restricted/no Payables data. | Sales, Purchase, Warehouse, Stock, or Executive-only roles do not inherit AP visibility. |

Company scoping must continue to use the Finance resolver pattern. The current single-company fallback for `Mingalar Mobile Distribution Co., Ltd.` / `MMK` can be considered only if Owner/Main Control re-accepts it for Payables, because supplier liability data is a separate exposure class from receivables posture.

## First Acceptable Payables Posture

The first acceptable AP runtime posture, if later approved, should be narrower than a dashboard:

- lane name: `Payables posture`;
- source state: unavailable until F5A/F5B source policy and role/company gates are accepted;
- first data shape: aggregate AP count buckets only;
- first role: `Accounts Manager` only unless Owner approves Accounts User coarsening;
- company scope: resolver-selected company only;
- currency posture: no amount values until AP amount source proof; when amounts are later approved, company currency must be `MMK` for the current site and mixed-currency totals must fail closed;
- row exposure: none;
- native ERP exposure: none;
- action exposure: none.

Potential count bucket design for later F5C, subject to source proof:

| Bucket | Purpose | Initial policy |
| --- | --- | --- |
| `not_due` | Bills not yet due. | Count only, no supplier/invoice identities. |
| `due_soon` | Bills approaching due date, proposed 0-7 days. | Requires cutoff-date policy before runtime. |
| `overdue_1_30` | Recently overdue supplier pressure. | Count only. |
| `overdue_31_60` | Material overdue supplier pressure. | Count only. |
| `overdue_61_90` | Long overdue pressure. | Count only. |
| `overdue_over_90` | Severe overdue pressure. | Count only. |
| `unavailable` | Source gates failed. | No partial counts or amounts. |

F5 does not approve these buckets for runtime. They are the design target for the next source policy phase.

## Blocked Scope

F5 keeps these surfaces blocked:

- Purchase Invoice creation, save, submit, cancel, amend, return, debit note, write-off, or lifecycle action;
- Payment Entry creation, save, submit, cancel, allocation, supplier payment, payment run, Payment Request, or Payment Order behavior;
- Journal Entry lifecycle and GL Entry mutation;
- Payment Reconciliation, Bank Reconciliation, advance reconciliation, or unreconcile behavior;
- Supplier notification, email, portal, statement sending, or payment communication;
- Supplier rows, supplier names, supplier IDs, supplier balances, supplier bank details, supplier contacts, or supplier tax details;
- Purchase Invoice rows, invoice IDs, voucher IDs, due-date rows, item lines, statuses, or drilldowns;
- Payment Ledger, GL, account, voucher, or account-currency rows;
- native Accounts Payable report pass-through, query-report route, Form/List route, `/app`, print, export, download, or dashboard embedding;
- raw SQL, `frappe.get_all`, `ignore_permissions`, broad report APIs, or user-supplied browser filters;
- cash/bank balances, payment affordability, or treasury authority claims;
- live alignment, restart, metadata reload, migration, protected gates, staging, commit, or push from this phase.

## Source Policy Questions

F5A must answer these before any Payables runtime read is approved:

Important source-risk findings from ERPNext semantics review:

- native `Accounts Payable` report output is not a safe browser/source pass-through because it can include supplier, voucher, bill, due-date, payable account, outstanding, currency, future-payment, payment-term, supplier-group, and remarks fields;
- `Purchase Invoice.outstanding_amount` is not approved for amount totals because it can be party/account currency rather than company currency; it may be considered only as an open-invoice count filter after separate policy approval;
- later AP amount semantics, if pursued, must be voucher-outstanding semantics that account for payments, journal allocations, returns/debit notes, and related allocation rows; raw Purchase Invoice totals, raw GL sums, and raw Payment Ledger row sums are rejected;
- payment terms, supplier advances, on-hold invoices, returns/debit notes, and overpayment cases need explicit policy before runtime because they can distort both count and amount posture.

| Area | Question | Initial F5 stance |
| --- | --- | --- |
| Purchase Invoice count source | Can a permission-preserving aggregate count read use Purchase Invoice without returning supplier/invoice identities? | Possible for count-only, but must be proven. |
| Purchase Invoice outstanding fields | Are outstanding values supplier/account currency, invoice currency, or company currency in this deployment? | Not approved for amount totals. Do not sum until proven. |
| Payment Ledger Entry AP source | Can payable voucher-outstanding semantics be reproduced safely like AR, with selected-company assertion and no partial aggregates? | Candidate for F5D proof only, not runtime. |
| Accounts Payable report | ERPNext uses report logic for AP posture, and public source wraps shared receivable/payable report logic. Can any logic be adapted without native report pass-through or row output? | Native report pass-through rejected. Adapter proof required. |
| Due date basis | Should AP count aging use Purchase Invoice due date only, and fail closed if missing? | Preferred to match F4 hardening: due-date-only, no posting-date fallback. |
| Payment terms | How are split payment schedules represented for Purchase Invoice, and can they be detected without row leakage? | Unsupported until explicit proof. Multiple due dates or payment-term ambiguity should fail closed. |
| Advances and allocations | How do supplier advances and partial payments affect open AP posture? | Must be handled by source proof; do not infer from invoice outstanding fields. |
| Debit notes / returns / credits | How are return Purchase Invoices, debit notes, and supplier credits represented? | Must be excluded or normalized by policy before runtime. |
| Currency | Is the data in company currency `MMK`, party/account currency, or mixed currency? | Amount posture blocked until company-currency proof. |
| Company scope | Can AP source rows assert resolver-selected company? | Required. Missing or mismatched company must fail closed. |
| Low population | Could aggregate AP counts or amounts identify one supplier/invoice? | Suppression/coarsening required before Accounts User visibility and before manager amounts in small populations. |
| Permission path | Can source checks run without `ignore_permissions`, raw SQL, broad `get_all`, or Finance users reading restricted metadata fields directly? | Required before runtime. Permission denial must return controlled unavailable state. |

## UI / Operations Policy

Future UI should stay lean and use the shared workspace grammar already used by Sales, Procurement, Warehouse, and Finance AR:

- one compact Payables posture lane in Finance Control Desk, not a separate AP dashboard;
- no fake action controls;
- no native ERP terminology that implies execution;
- unavailable and restricted states must be controlled and non-blank;
- copy should say `payment preparation` or `supplier payment pressure`, not `ready to pay`;
- cash planning should be framed as a future handoff, not as bank/cash truth;
- no supplier names, invoice names, account names, or document links in the first runtime cycle;
- no export/download/print affordances.

Suggested business-facing lane promise:

> Company-scoped AP aging signals from approved Payables source semantics. No supplier detail, native reports, exports, or payment actions.

## Proposed F5 Subphases

| Phase | Objective | Runtime approval? | Acceptance gate |
| --- | --- | --- | --- |
| F5A Payables visibility/source policy | Define exact AP sources, due-date basis, role exposure, source fields, blocked surfaces, and proof requirements. | No. Docs/proof only. | Owner accepts source policy questions and blocked scope. |
| F5B Payables role/company/currency gate contract | Reuse Finance resolver posture for AP, decide single-company fallback for AP, define MMK/company-currency gate and denied-role behavior. | No runtime AP reads unless separately approved. | Tests planned for manager/user/non-Finance, company scope, no browser filters. |
| F5C AP count-only posture | Implement aggregate AP count buckets only if F5A/F5B are accepted and a safe count source is proven. | Separate approval required. | Strict aggregate parsing, due-date fail-closed, no rows/identities, no partial output on invalid source. |
| F5D Manager-only AP amount source proof | Prove or reject AP amount source, likely Payment Ledger payable voucher-outstanding semantics. | No UI/runtime amount exposure. | Company-currency proof, source permission proof, selected-company row assertion, currency/suppression policy. |
| F5E Manager-only AP amount runtime | Add manager-only aggregate MMK AP amount buckets only if F5D proves a safe source and Owner approves implementation. | Separate approval required. | Pagination/cap, malformed row fail-closed, no supplier/invoice/voucher/account/PLE/GL identity, no exports. |
| F5F Manual review / live decision | Prepare Owner manual browser checklist and live-alignment decision package. | No live alignment unless separately approved. | Manager/user/restricted browser checks and no native/action leak. |
| F5G Hardening / closure | Counterpart review, source package classification, controlled staging/commit decision if approved. | Separate approval required. | Dirty-file exclusion, full boundary scan, no protected gate unless separately approved. |

## Tests Required Before Any Runtime Payables Phase

Future runtime tests must cover at least:

- `Accounts Manager` is the first AP aggregate candidate;
- `Accounts User` sees no AP counts or amounts until coarsening policy is approved;
- `Auditor`, `System Manager` alone, Executive-only, Sales/Purchase/Warehouse/Stock roles, and non-Finance users receive no AP data;
- default company display does not authorize AP data;
- selected company must come from the resolver and must match every source row used for aggregation;
- permission denial returns controlled unavailable state and does not call the source adapter;
- no raw SQL, `frappe.get_all`, `ignore_permissions`, native report pass-through, or user-supplied browser filters;
- aggregate parser fails closed on missing, malformed, unexpected, negative, ambiguous, or multi-row aggregate output;
- missing due date fails closed before count buckets;
- payment terms, multiple due dates, advances, debit/credit notes, and returns are either proven safe or fail closed;
- over-cap source reads return no partial aggregate;
- low-population suppression/coarsening blocks identity inference;
- no response keys or nested payloads expose supplier rows, invoice rows, payment rows, voucher/account/PLE/GL rows, route/report/export/download/print/action keys;
- frontend guard rejects injected supplier/invoice/payment/native/action-shaped payloads while allowing safe aggregate bucket fields.

## Owner Manual Checks Before Runtime

Owner/Main Control must explicitly accept these decisions before F5C or later runtime work starts:

- whether `Accounts Manager` is the only first AP count role;
- whether `Accounts User` AP counts stay blocked until low-count/coarsening policy;
- whether the single-company fallback is acceptable for AP on the current `Mingalar Mobile Distribution Co., Ltd.` / `MMK` site;
- whether AP count buckets should include `due_soon` or remain AR-style aging only;
- whether Purchase Invoice due date is the only approved count aging basis;
- whether supplier-level visibility remains blocked for the entire first AP runtime cycle;
- whether AP amount source proof should prioritize Payment Ledger payable semantics or pause until GL/AP reconciliation ownership is clearer.

## Findings Integrated From F5 Reviews

Accepted:

- AP must have its own source contract and cannot inherit AR Payment Ledger assumptions blindly.
- First Payables runtime, if approved later, should start aggregate-only and count-only.
- Manager-only amount visibility must wait for company-currency source proof.
- Native Accounts Payable report output is unsafe for Finance Control Desk posture because it exposes row/context fields beyond F4 boundaries.
- `Purchase Invoice.outstanding_amount` is not a company-currency-safe amount source; at most it is a future count-filter candidate after policy approval.
- AP amount proof, if reopened, must model payable voucher-outstanding semantics rather than raw invoice, GL, or Payment Ledger row sums.
- Finance registry/navigation should remain page-only and avoid native report/Form/List/query-report targets.
- Cash planning language should remain a handoff, not a bank/cash forecast or payment authority.
- Current `e198fa4` hardening commit must be treated as the baseline before F5 runtime design proceeds.

Rejected:

- Native Accounts Payable report embedding or pass-through.
- Purchase Invoice outstanding amount totals, direct GL bucket sums, and raw Payment Ledger row sums for AP amount posture.
- Supplier balances, supplier rows, Purchase Invoice rows, payment rows, voucher/account/GL/Payment Ledger row drilldown.
- Payment Entry, Journal Entry, Purchase Invoice lifecycle shortcuts, payment run, reconciliation, write-off, export, print, download, email, portal, or supplier notification controls.
- Treating `System Manager` or Executive-only roles as Finance data authority.

Deferred:

- Auditor AP visibility.
- Accounts User AP count visibility.
- Supplier-level balances.
- Invoice-level detail.
- AP amount buckets.
- Payment Ledger payable aggregation proof.
- Payment-term split support.
- Supplier advances / Purchase Order advances.
- Debit-note, return, on-hold, and overpayment semantics.
- Cash/bank planning integration.

## Runtime Readiness

Not ready.

F5 is ready only as a policy/design artifact. No Payables runtime implementation should start until Owner/Main Control accepts F5A/F5B source and gate decisions. If F5A is approved next, it should be a source-policy/proof phase, not a UI data-card or execution phase.

## Boundary Confirmation

F5 introduced no runtime code, no Payables reads, no Purchase Invoice reads, no Payment Ledger reads, no Supplier reads, no Payment Entry reads, no GL reads, no Bank/Cash reads, no UI data cards, no native routes, no exports, no print/download, no posting/payment/reconciliation/write-off/tax/close behavior, no user/role/permission/DocType mutation, no live alignment, no restart, no metadata reload, no migration, no staging, no commit, no push, and no protected gates.

## Recommended Next Step

Proceed to `F5A Payables visibility/source policy` only after Owner/Main Control accepts this F5 policy. F5A should remain research/proof/design first. It should not implement runtime Payables data until the AP source, due-date basis, role/company/currency gates, and suppression rules are explicitly accepted.
