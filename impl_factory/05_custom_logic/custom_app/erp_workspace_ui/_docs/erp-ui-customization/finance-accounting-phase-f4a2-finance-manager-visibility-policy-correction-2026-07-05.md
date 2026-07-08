# Finance & Accounting F4A2 Finance Manager Visibility Policy Correction - 2026-07-05

Status: policy and governance correction only. This document does not implement AR, AP, cash, GL, bank, tax, close, report, export, native route, posting, payment, reconciliation, write-off, customer communication, live alignment, restart, metadata reload, protected gate, commit, or push behavior.

## Decision

F4A was correct to stop F4 before receivables data was implemented, but its blanket "amounts blocked" posture is too restrictive for Finance and Accounts Manager roles. Mature ERP finance workspaces normally separate financial visibility from posting authority. A manager must be able to see company-scoped amounts, aging posture, and cash-flow indicators to manage finance operations, while execution remains separately controlled.

F4A2 corrects the policy as follows:

- Amounts remain blocked for normal users by default.
- Company-scoped amount totals are approved in principle for approved Accounts Manager and future Finance Manager roles after company scope, currency policy, DocType/read policy, field allowlist, and tests are accepted.
- Company-scoped amount totals may be approved for Auditor read-only scope if audit/company access is explicitly accepted.
- Owner/Executive amount visibility requires explicit role mapping and scope policy; it is not assumed.
- System Manager is not automatically Finance authority and must not receive finance data only because of system administration access.
- Posting, payment, reconciliation, write-off, period close, tax filing, customer communication, exports, native ERP routes, and ERPNext document lifecycle actions remain blocked.

F4A remains the conservative stop/governance baseline. F4A2 supersedes only the blanket treatment of manager-level amount visibility.

## ERP Practice Rationale

The Finance Control Desk should follow the common ERP separation between visibility, review, and execution:

- ERP suites such as Oracle Fusion use finance job roles together with scoped data access.
- Microsoft Dynamics 365 Business Central provides accounting role centers with key figures, posted-document visibility, and company access controls.
- NetSuite combines role permissions with subsidiary, department, class, and location restrictions.
- SAP finance access is governed through business roles and authorization scope.
- Odoo separates application access groups and record-level rules.
- ERPNext combines Role Permissions with User Permissions, so a role may grant DocType capability while linked-record restrictions such as Company scope must still be enforced.

The project policy should therefore allow manager visibility where scope is proven, but should not treat visibility as authorization to mutate accounting records.

## Visibility, Review, And Execution

| Capability class | Meaning | F4A2 policy |
| --- | --- | --- |
| Visibility | Seeing AR/AP/cash/aging totals, posture, and company-scoped finance health. | Approved in principle for manager roles after F4B gates. |
| Review | Marking posture, adding review notes, or requesting follow-up in future custom no-effect records. | Future only, separate custom record phase. |
| Execution | Posting, paying, reconciling, writing off, closing periods, filing tax, sending reminders, using native ERP actions, or mutating commercial/accounting documents. | Blocked in the custom workspace. |

Review records, if introduced later, must remain no-effect. They must not imply Sales Invoice, Payment Entry, Journal Entry, GL Entry, bank reconciliation, tax, close, write-off, dunning, email, notification, portal, or external action execution.

## Role Visibility Matrix

| Role | Shell access | Tier 0 posture | Count-only access | Amount-total access | Customer-level visibility | Invoice-row visibility | Execution authority | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Accounts User | Yes, if workspace role policy allows. | Yes. | Future yes after F4B prerequisites. | Future optional only if Owner approves a company-scoped limited user policy. | Blocked in first cycle. | Blocked in first cycle. | No. | Default posture should be operational counts, not amounts, unless a later policy grants limited amount totals. |
| Accounts Manager | Yes. | Yes. | Yes after F4B prerequisites. | Yes in principle after company scope, currency policy, DocType/read policy, field allowlist, and tests. | Future separate approval. | Future separate approval. | No in the custom workspace. | Primary role for manager-level AR/AP/cash amount posture. |
| Finance Manager (custom future role) | Yes after role exists and governance maps it. | Yes. | Yes after F4B prerequisites. | Yes in principle, same or stronger than Accounts Manager after role creation and scope approval. | Future separate approval. | Future separate approval. | No in the custom workspace. | Proposed custom role only; do not assume it exists in ERPNext. |
| Auditor | Yes if audit role/scope is approved. | Yes. | Future yes for read-only audit scope. | Future yes for read-only company/audit scope if approved. | Future separate approval. | Future separate approval. | No. | Audit visibility must remain read-only and no-effect. |
| System Manager | Shell/admin yes if registry permits. | Shell posture only by default. | No finance counts by default. | No finance amounts by default. | No by default. | No by default. | No in the custom workspace. | System administration is not finance data ownership unless the user also has an approved finance role and company scope. |
| Owner / Executive | Future explicit role mapping required. | Future summary posture. | Future summary counts if mapped. | Future executive totals if mapped and scoped. | Future separate approval. | Future separate approval. | No in the custom workspace. | Executive visibility is a business decision, not inferred from title or System Manager status. |
| Non-finance roles | Restricted. | Restricted copy only. | No. | No. | No. | No. | No. | No AR/AP/cash posture data. |

Role alone is insufficient for finance amounts. Future implementations must combine role eligibility, allowed-company scope, DocType/read policy, field allowlist, and currency policy.

## Revised Visibility Tiers

| Tier | Description | Revised F4A2 decision | Scope |
| --- | --- | --- | --- |
| Tier 0 | Posture and boundary copy only; no AR/AP/cash data. | Approved now. | All allowed shell roles; restricted users see restricted shell only. |
| Tier 1 | Aggregate counts only. | Future near-term. | Company-scoped and permission-aware. |
| Tier 2 | Aging buckets with counts. | Future near-term. | Company-scoped and permission-aware; no amounts. |
| Tier 3 | Aging buckets with amount totals. | Approved in principle for Accounts Manager, future Finance Manager, and possibly Auditor after F4B gates. | Company-scoped; currency policy required; no customer or invoice rows. |
| Tier 4 | Customer-level balances. | Future separate approval. | Stronger privacy, audit, and manual review required. |
| Tier 5 | Invoice-level rows. | Future separate approval. | Stronger privacy, audit, route, and row-level policy required. |
| Tier 6 | Execution actions. | Blocked. | Must be a separate future execution phase after Owner/Security approval. |

Tier 3 approval in principle does not approve runtime code. It approves the policy direction that manager amount totals are legitimate once all safeguards are implemented and accepted.

## Company Scope Policy

Amount visibility requires an allowed-company resolver before any amount field, currency, count, aging bucket, AR/AP total, cash indicator, or posture value is returned.

Required rules:

- Resolve allowed companies through permission-aware ERPNext access, including User Permissions and any accepted project role mapping.
- Treat user default company as a preferred filter only; it is not authorization.
- Validate selected company server-side and reject requested-company-outside-scope cases.
- If one company is allowed, it may become the default selected company after authorization.
- If multiple companies are allowed, require explicit selected company before showing company-specific amounts.
- Do not show all-company totals unless Owner/Main Control explicitly approves a consolidation policy.
- If no company is allowed, return a restricted or unavailable state with no amounts, counts, rows, company list, routes, exports, or report data.
- A future selector may return only authorized company display labels plus opaque/backend-validated selection keys. It must not leak hidden company identifiers, accounting dimensions, or cross-company totals.

Required tests before F4B amount visibility:

- one-company allowed;
- multi-company allowed with explicit selected company;
- no-company allowed;
- default-company-not-allowed;
- requested-company-outside-scope;
- broad Company read but denied AR/AP/cash source permission;
- role-eligible but company-denied user;
- non-finance restricted user.

## Currency And Amount Policy

Manager amount totals require an accepted currency display policy before runtime implementation.

Rules:

- If the selected company has one presentation currency and the amount source is unambiguous, company-scoped amount totals may be shown after F4B approval.
- If multiple currencies are present, do not display mixed totals without an explicit conversion, revaluation, and presentation policy.
- Do not mix base currency, party currency, account currency, and company presentation currency in the same UI label.
- Do not show customer-level amount totals in the first manager amount phase.
- Do not show invoice-level amount rows in the first manager amount phase.
- Amount labels must identify the approved currency basis without exposing native report internals.
- Negative amounts, credit notes, debit notes, returns, advances, allocations, write-off candidates, and rounding differences require explicit count/amount semantics before display.
- Low-count or small-population suppression may be required where totals could identify a single customer or invoice.

## Customer And Invoice Visibility

Customer and invoice visibility remain separate future decisions.

- Customer names and customer-level balances remain blocked for the first manager amount phase unless Owner/Main Control separately approves Tier 4.
- Invoice identifiers, due dates, statuses, line items, payment schedules, and invoice-level outstanding amounts remain blocked unless Owner/Main Control separately approves Tier 5.
- Future Tier 4/Tier 5 phases require stronger audit metadata, manual review, exact field allowlists, row limits, no native route strings, no export/download/print, and no execution affordances.

## ERPNext Implementation Implications

Future F4B code must not pass native ERPNext report output or document rows to the browser.

Required implementation constraints:

- Do not expose `/app`, Form, List, Report, Query Report, or query-report routes.
- Do not expose native Accounts Receivable, Accounts Payable, General Ledger, Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry, Customer, Supplier, Bank Transaction, Payment Request, Dunning, Communication, Email Queue, or Process Statement Of Accounts route strings.
- Do not use `ignore_permissions`, including `ignore_permissions=True` variants.
- Avoid `frappe.get_all` for finance business data.
- Do not use raw SQL or `frappe.db.sql` unless a later security review approves a bounded permission-preserving exception.
- Use permission-aware reads only after DocType read policy, allowed-company policy, source-field allowlist, row/aggregate semantics, and leakage review are accepted.
- Enforce role plus company plus source permission plus field allowlist before reading or returning finance data.
- Return exact response keys only; do not return raw DocType documents, report rows, report columns, route strings, or export metadata.
- Include explicit no-effect flags for document, GL, journal, payment, reconciliation, tax, close, notification, export, email, portal, and external action effects.
- No export, download, print, clipboard-copy dataset, native route, report drilldown, or execution control may appear in F4B.

## F4B Recommendation

F4B should remain narrow.

Preferred path:

- Implement Accounts Manager company-scoped Receivables aging posture with Tier 1/Tier 2 counts first.
- Add Tier 3 amount-total cards only if company scope and currency policy are accepted before implementation.
- Keep amount totals aggregated by aging bucket or summary posture only.
- Do not show customer rows.
- Do not show invoice rows.
- Do not show native ERPNext routes or reports.
- Do not show execution controls.
- If currency policy is not accepted, deliver manager count-only aging posture first and keep amounts unavailable.

F4B should not expand into AP, cash, GL, bank, close, tax, or cross-workspace impact unless those lanes receive their own policy gates.

## Explicit Boundaries

The following remain blocked:

- Sales Invoice create, save, submit, cancel, amend, delete, payment allocation, or native route behavior;
- Purchase Invoice create, save, submit, cancel, amend, delete, or native route behavior;
- Payment Entry create, save, submit, cancel, amend, delete, allocate, unallocate, or native route behavior;
- Journal Entry create, save, submit, cancel, amend, delete, reversal, adjustment, or native route behavior;
- GL Entry mutation or ledger adjustment;
- Payment Reconciliation mutation;
- Bank Transaction or bank reconciliation mutation;
- write-off, adjustment, credit note, debit note, dunning, customer statements, payment requests, payment links, customer reminders, email, notification, portal, Communication, Email Queue, or external action;
- Period Closing Voucher, tax filing, close submission, or compliance submission behavior;
- native ERPNext route/report/export/download/print behavior;
- live alignment, restart, metadata reload, migration, protected gate, commit, or push.

## F4B Readiness

F4B is not ready.

Required gates before F4B may implement amount visibility:

- Owner/Main Control accepts F4A2.
- Allowed-company resolver is designed and tested.
- DocType/read policy is designed and tested for the selected source.
- Currency and amount display policy is accepted.
- Role mapping is accepted for Accounts Manager, future Finance Manager, Auditor, Owner/Executive, System Manager, and non-finance roles.
- Field allowlist and source-field/query allowlist are accepted.
- Count and aging semantics are accepted.
- Low-count/customer-identification suppression policy is accepted or explicitly waived.
- Static scans for native routes, reports, export/download/print, mutation APIs, `ignore_permissions`, `frappe.get_all`, raw SQL, email/notification/portal, and execution labels are defined.
- Owner manual verification checklist is prepared.

## Boundary Confirmation

F4A2 implements no AR, AP, cash, GL, bank, close, tax, or cross-workspace runtime data. It approves no accounting execution, posting, payment, reconciliation, write-off, Sales Invoice lifecycle behavior, Purchase Invoice lifecycle behavior, Payment Entry lifecycle behavior, Journal Entry lifecycle behavior, GL mutation, bank reconciliation mutation, native Finance route/report/export behavior, customer notification, email, portal behavior, live alignment, restart, metadata reload, protected gate, commit, or push.
