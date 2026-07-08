# Finance & Accounting Phase F1 - Governance / Scope Contract

Date: 2026-07-04
Status: docs-only governance artifact for Owner/Main Control review
Decision basis: `accepted_for_F1_docs_only_with_conditions`
Workspace family: Finance & Accounting
Proposed page/product label: Finance Control Desk, pending Owner approval

## 1. Purpose

Finance & Accounting is the next workspace planning stream after Warehouse Console Phase W16H custom workflow closure.

Warehouse W16H closed only the current custom Warehouse workflow scope. It did not approve ERPNext stock execution, valuation exposure, accounting execution, Purchase Receipt, Delivery Note, Pick List, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, stock posting, commercial exposure, notification behavior, native ERP execution routes, protected release action, or full Warehouse business closure.

Finance & Accounting must start with governance before any workspace implementation begins. The first Finance cycle must establish visibility, posture, review boundaries, data sensitivity, role authority, and future accounting execution controls. It must not begin by exposing raw ERPNext accounting screens or by creating posting, payment, reconciliation, close, or tax controls.

F1 is documentation only. F1 creates no route, registry entry, backend method, frontend page, DocType, custom field, workspace sidebar item, report wrapper, smoke test, live alignment, metadata reload, migration, commit, push, restart, or protected gate.

No accounting execution is approved in F1.

Evidence anchors for this contract:

- Warehouse W16H explicitly keeps ERPNext stock/accounting execution deferred after custom workflow closure.
- The Multi-Workspace Foundation Contract says Finance must not be built until purchase, invoice, and accounting ownership boundaries are written down.
- ERPNext accounting sources and documentation show that Journal Entry, Payment Entry, Sales Invoice, Purchase Invoice, GL Entry, reconciliation, tax, and period close behavior affect accounting truth.
- Mature ERP patterns separate financial visibility, review queues, and controller posture from posting authority, payment authority, reconciliation authority, tax filing, and period close.

## 2. Workspace Model Decision

Recommendation: use one combined Finance & Accounting workspace for now. Do not split Finance and Accounting yet.

Reasoning:

- Accounts receivable, accounts payable, general ledger posture, payments, cash and bank posture, tax, close, and cross-workspace accounting impact are connected.
- Splitting too early would duplicate dashboards, filters, route families, role decisions, and ownership surfaces.
- Early split would create unclear authority between AP, AR, treasury, controller, and owner views before the data visibility contract is proven.
- The combined workspace can still have internal lanes and role-specific views.
- A future split may be possible after the combined workspace matures and real usage proves separate ownership is needed.

Naming contract:

- `Finance & Accounting` is the workspace family name for this governance phase.
- `Finance Control Desk` is only the proposed product/page label.
- `Finance Control Desk` is not final unless Owner/Main Control approves it.
- The historical matrix name `Finance Console` remains a source reference, not final visible naming law.

Open naming decision: Owner/Main Control must approve the final visible workspace name before F2 shell work.

### Cross-workspace ownership boundary

| Area | Sales | Procurement | Warehouse | Finance & Accounting | Boundary in F1 |
| --- | --- | --- | --- | --- | --- |
| Customer orders and quotations | Owns productized sales workflow | No ownership | No ownership | Reads only future accounting impact | Finance must not mutate Sales documents. |
| Customer receivables | May show bounded customer-facing exposure | No ownership | No ownership | Owns full AR posture and aging visibility | Cycle 1 Finance may show AR aging only if role/company rules pass. |
| Supplier sourcing and buying | No ownership | Owns procurement workflow before accounting | No ownership | Owns AP posture after supplier invoice/accounting evidence | Finance must not mutate Procurement documents. |
| Supplier payables | No ownership | May show downstream billing posture only | No ownership | Owns full AP posture and aging visibility | Cycle 1 Finance may show AP aging only if role/company rules pass. |
| Stock movement and warehouse evidence | No ownership | Receives procurement status only | Owns custom Warehouse workflow posture | Reviews future accounting impact only | Finance must not mutate stock documents or warehouse custom records. |
| Invoice lifecycle | Sales/Procurement may show document context where already approved | Shows managed buying context only | No lifecycle ownership | Future Finance authority requires separate approval | Cycle 1 blocks Sales Invoice and Purchase Invoice lifecycle actions. |
| Payment Entry | No ownership | No ownership | No ownership | Future Finance/Treasury authority only after approval | Blocked. |
| Journal Entry | No ownership | No ownership | No ownership | Future Controller authority only after approval | Blocked. |
| GL and financial statements | No ownership | No ownership | No ownership | Future Controller/Auditor posture | Detailed GL blocked in Cycle 1. |
| Tax and period close | No ownership | No ownership | No ownership | Future Controller/Tax authority | Blocked in Cycle 1. |
| Native ERP execution routes | Existing governed exceptions only | Existing governed exceptions only | None for execution | None approved | No Finance native execution route in F1/Cycle 1. |

## 3. First-Cycle MVP Scope

Cycle 1 is the safe Finance & Accounting visibility MVP. It contains only these phases:

| Phase | Scope | Decision posture |
| --- | --- | --- |
| F1 | Governance/scope contract | Docs only. This document. |
| F2 | Workspace shell, registry, governance manifest, no native execution routes | Future implementation only after F1 acceptance. |
| F3 | Safe accounting overview with aggregate posture only | Future read-only implementation only. |
| F4 | Receivables posture and aging visibility | Future read-only implementation only. |
| F5 | Payables posture and aging visibility | Future read-only implementation only. |
| F6 | Security/stability hardening and Owner manual verification | Future validation phase only. |

Explicitly deferred from Cycle 1:

- Cash and Bank.
- GL detail and Trial Balance.
- Close and Tax.
- Custom review/request records.
- Cross-workspace accounting impact review.
- Export/download.
- Posting, payment, reconciliation, close, tax, write-off, and lifecycle execution.

Cycle 1 must not become a dashboard suite. It should provide one controlled workspace shell, one aggregate accounting overview, one receivables visibility lane, one payables visibility lane, and hardening/Owner verification.

### First-cycle metric dictionary

F1 does not approve exact implementation formulas, but it defines the required metric dictionary before F3-F5 can start.

| Metric family | Intended source | Allowed Cycle 1 posture | Required decisions before implementation |
| --- | --- | --- | --- |
| Company selector | ERPNext Company plus user/company permissions | Show only allowed companies. No all-company default. | Company default policy and multi-company handling. |
| AR aging totals | Sales Invoice or ERPNext Accounts Receivable report semantics | Aggregate buckets and counts only unless Owner approves customer detail. | Aging basis, cutoff date, currency display, credit/debit note treatment. |
| Customer outstanding | Sales Invoice outstanding posture | Owner decision: allowed or aggregate-only. | Customer-level balance visibility approval. |
| AP aging totals | Purchase Invoice or ERPNext Accounts Payable report semantics | Aggregate buckets and counts only unless Owner approves supplier detail. | Aging basis, cutoff date, currency display, advances/credit note treatment. |
| Supplier outstanding | Purchase Invoice outstanding posture | Owner decision: allowed or aggregate-only. | Supplier-level balance visibility approval. |
| Currency values | Document currency, company currency, presentation currency | Must be explicit in every value label. No silent conversion. | Owner must decide display policy before F3-F5. |

Cycle 1 overview is not cash truth, GL truth, tax truth, close readiness, audit certification, or payment authority.

## 4. Role Model

F1 distinguishes native ERPNext-style roles from proposed/custom/business roles. The existence of proposed roles must not be assumed in ERPNext until verified or created in a later approved phase.

| Role | Role type | First-cycle visibility | Blocked actions | Owner confirmation needed | Mapping note |
| --- | --- | --- | --- | --- | --- |
| Accounts User | Native-style ERP/accounting role | Candidate for AR/AP worklist visibility within permitted company scope. | Posting, payment, reconciliation, JE, invoice lifecycle, export, native routes. | Yes, for exact fields. | Treat as ERPNext role family, but still check permissions and company. |
| Accounts Manager | Native-style ERP/accounting role | Candidate for aggregate overview plus AR/AP detail within permitted company scope. | Posting/payment/reconciliation/close/tax execution in Cycle 1. | Yes. | Strongest candidate for Cycle 1 manager visibility. |
| Auditor | Native-style review role | Candidate for read-only overview and AR/AP visibility if company permission allows. | All mutation, export by default, native drilldown by default. | Yes. | Audit visibility does not imply posting authority. |
| System Manager | Native-style administration role | Candidate for setup/admin awareness only; not automatic Finance business owner. | Business execution and cross-company finance visibility unless explicitly approved. | Yes. | Avoid treating System Manager as universal finance bypass. |
| Finance User | Proposed/custom business role | Candidate for future narrow AR/AP visibility. | All execution, native routes, export. | Yes. | Not assumed to exist. |
| Finance Manager | Proposed/custom business role | Candidate for future manager posture, aggregate overview, AR/AP review. | Posting/payment/reconciliation/close/tax execution until separately approved. | Yes. | Not assumed to exist. |
| Controller | Proposed/custom business role | Candidate for future GL, close, tax, and audit posture. | All Cycle 1 execution; GL detail deferred. | Yes. | Not assumed to exist. |
| Owner / Executive | Business identity or future custom role | Candidate for aggregate posture only unless approved otherwise. | Operational execution, native routes, export by default. | Yes. | Must be defined as real role, custom role, or manual review identity. |

Role rules:

- Role checks are necessary but not sufficient.
- Every future backend method must also check company scope, DocType read permission, field allowlist, and route/action allowlist.
- Cross-workspace roles such as Sales, Purchase, and Warehouse roles do not automatically receive Finance data.
- Finance role names must not be introduced as assumed runtime roles before Owner approval.

## 5. Data Sensitivity And Visibility Matrix

Global data rules:

- Multi-company data is high risk. Default company filters must be restricted to the user's permitted company scope.
- No all-company or consolidated view is allowed in Cycle 1 unless Owner/Main Control explicitly approves it.
- Company filter defaults must be decided before F3-F5 implementation.
- Currency handling is a required decision before F3-F5. Values must distinguish document currency, company currency, and presentation currency. Silent conversion is not allowed.
- Customer-level and supplier-level balance visibility are explicit Owner decisions.
- Export/download is blocked by default unless later approved with audit and permission rules.

| Data type | Sensitivity | First-cycle visibility | Candidate roles allowed | Owner decision required | Reason | Tests required later |
| --- | --- | --- | --- | --- | --- | --- |
| Company-level financial summary | High | Aggregate only | Accounts Manager, Auditor, Owner/Executive if approved | Yes | Shows financial posture and may expose company health. | Role, company, aggregate-only, no export. |
| AR aging totals | Medium | Allowed | Accounts User, Accounts Manager, Auditor, Finance Manager if approved | No for aggregate, yes for role mapping | Core receivables posture. | Aging bucket accuracy, company filter, no mutation labels. |
| Customer-level outstanding balances | High | Owner decision: allowed or aggregate only | Accounts User, Accounts Manager, Auditor, Finance Manager if approved | Yes | Exposes customer credit and collection sensitivity. | Customer field allowlist, role/company permission. |
| Sales Invoice header data | High | Allowed only for AR aging fields if approved | Accounts User, Accounts Manager, Auditor | Yes | Invoice identity and due/outstanding posture are sensitive. | Header field allowlist, no line/tax fields. |
| Sales Invoice line/detail | Restricted | Blocked | None in Cycle 1 | Yes | Exposes pricing, item, tax, margin, and commercial detail. | Absence scan for line fields. |
| AP aging totals | Medium | Allowed | Accounts User, Accounts Manager, Auditor, Finance Manager if approved | No for aggregate, yes for role mapping | Core payables posture. | Aging bucket accuracy, company filter, no mutation labels. |
| Supplier-level outstanding balances | High | Owner decision: allowed or aggregate only | Accounts User, Accounts Manager, Auditor, Finance Manager if approved | Yes | Exposes supplier obligations and payment sensitivity. | Supplier field allowlist, role/company permission. |
| Purchase Invoice header data | High | Allowed only for AP aging fields if approved | Accounts User, Accounts Manager, Auditor | Yes | Supplier invoice identity and due/outstanding posture are sensitive. | Header field allowlist, no line/tax fields. |
| Purchase Invoice line/detail | Restricted | Blocked | None in Cycle 1 | Yes | Exposes supplier pricing, item, tax, and buying terms. | Absence scan for line fields. |
| Cash/bank balances | Restricted | Blocked | None in Cycle 1 | Yes | Treasury-sensitive and often executive-only. | No bank balance payloads. |
| Bank account identifiers | Restricted | Blocked/masked | None in Cycle 1 | Yes | Bank account identifiers are high-risk. | Masking/absence tests. |
| Bank transaction descriptions | High | Blocked | None in Cycle 1 | Yes | Counterparty and cash movement leakage. | No bank transaction fields. |
| GL account balances | High | Blocked in Cycle 1 | None in Cycle 1 | Yes | Ledger posture needs report permission and dimension controls. | No GL payloads. |
| GL Entry line detail | Restricted | Blocked | None in Cycle 1 | Yes | Full ledger trail, parties, accounts, and accounting dimensions. | No GL Entry reads or routes. |
| Cost center / accounting dimension detail | Medium/High | Blocked in Cycle 1 | None in Cycle 1 | Yes | Internal performance and allocation detail. | No dimension fields unless allowlisted later. |
| Tax IDs / tax registration data | Restricted | Blocked/masked | None in Cycle 1 | Yes | Compliance and identity exposure. | Tax field absence/masking. |
| Tax reports | Restricted | Blocked | None in Cycle 1 | Yes | Filing-sensitive and jurisdiction-sensitive. | No tax report routes or payloads. |
| Payroll-related accounting data | Restricted | Blocked | None in Cycle 1 | Yes | Employee privacy and compensation inference risk. | Payroll account/party absence. |
| Write-off / adjustment candidates | Restricted | Blocked | None in Cycle 1 | Yes | Implies accounting judgment and execution. | No write-off fields or actions. |
| Period close blockers | High | Blocked | None in Cycle 1 | Yes | Close authority and certification risk. | No Accounting Period/PCV payloads. |
| Cross-workspace accounting impact | High | Blocked | None in Cycle 1 | Yes | Ownership with Sales, Procurement, Warehouse, and Admin is unresolved. | No cross-workspace impact routes. |

## 6. Read-Only Backend / Data Access Contract

This contract applies to future F2-F5 backend work. It is not implemented in F1.

### Allowed

Future Cycle 1 Finance backend methods may use only:

- Authenticated whitelisted read methods.
- Explicit role checks.
- Explicit company scoping before any metric, count, row, or currency lookup.
- DocType read permission checks.
- `frappe.get_list` as the default DocType read method because it respects user permissions.
- Allowlisted report-style reads only when report name, filters, columns, roles, and output fields are controlled.
- Field allowlists for every payload.
- No-effect flags in every response.
- Controlled response states: `ready`, `empty`, `restricted`, `unavailable`, and `error`.

Required no-effect flags for every Finance response:

- `erp_document_created: false`
- `erp_document_updated: false`
- `gl_entry_created: false`
- `journal_entry_created: false`
- `payment_entry_created: false`
- `reconciliation_performed: false`
- `tax_filing_performed: false`
- `period_close_performed: false`
- `notification_sent: false`
- `export_generated: false`

### Forbidden

The following are forbidden for Finance Cycle 1 backend work:

- `insert`
- `save`
- `submit`
- `cancel`
- `delete`
- `frappe.db.set_value`
- background jobs
- emails, notifications, portal messages, customer sends, supplier sends, bank sends, or external sends
- `ignore_permissions=True`
- `frappe.get_all` for Finance business data by default
- raw SQL by default
- native ERP route strings in responses or UI targets
- export/download by default
- Payment Entry lifecycle
- Journal Entry lifecycle
- Sales Invoice lifecycle
- Purchase Invoice lifecycle
- GL Entry mutation
- bank reconciliation mutation
- payment reconciliation mutation
- tax filing/submission
- Period Closing Voucher creation/submission/cancellation
- write-off execution
- close execution

### Conditional

- `frappe.get_all` is allowed only for non-sensitive static metadata and only after a written exception. It is never allowed for first-cycle Finance business data unless Owner/Main Control separately approves it.
- Raw SQL is forbidden by default. It may be considered only in later approved cycles with parameterized SQL, company filters, permission review, security review, field allowlists, and tests.
- ERPNext report APIs may be used only when allowlisted by report name, filters, columns, roles, and no action targets.
- Exports may be considered only after a separate export policy, export permission, audit event, masking decision, and Owner approval.
- Consolidated or all-company views are blocked until a multi-company consolidation policy exists.

### Cross-company leakage prevention

Future Finance methods must:

1. Resolve allowed companies for the current user before reading data.
2. Reject or restrict any requested company outside that allowed set.
3. Default to a single allowed company unless Owner approves a different default.
4. Return zero rows, zero counts, zero action targets, and `restricted` or `unavailable` state for unauthorized company access.
5. Never compute totals before company permission has been checked.
6. Never use broad report filters that silently include all companies.

### Empty, restricted, unavailable, and error states

- `empty`: user is allowed, filters are valid, but no rows match.
- `restricted`: user or company does not have enough permission.
- `unavailable`: route/report/lane is not active or not approved.
- `error`: unexpected failure with generic user-facing wording only.

Restricted, unavailable, and error responses must not include partial metrics, native action targets, raw exception text, report names that imply a route, or sensitive field values.

### Native route exposure prevention

Future Finance payloads and UI must not include:

- `/app/`
- `Form`
- `List`
- `Report`
- `query-report`
- `open_native_report`
- generic `Open ERP Form`
- generic `View in ERPNext`

Any future native exception must be separately declared in the governance manifest and approved before use. No Finance native exception is approved in F1.

### Hidden write side-effect prevention

Future Finance read methods must not call helper methods that create, update, submit, cancel, reconcile, send, allocate, enqueue, attach files, or write audit events unless that exact custom write surface has been approved. Cycle 1 should not create custom records.

### Field allowlist testing

Every future Finance payload must have tests that assert allowed keys exactly. Tests must fail if blocked fields appear, including line items, tax rows, bank identifiers, GL Entry fields, native route targets, export keys, mutation labels, attachment keys, or external-send fields.

## 7. First-Cycle Lane Definitions

### Accounting Overview

Business purpose:

- Give approved Finance/Accounting users a safe aggregate view of financial posture.
- Help managers see whether receivables or payables need attention without implying cash, GL, tax, or close truth.

Users:

- Accounts Manager.
- Auditor if approved.
- Owner/Executive if approved.
- Accounts User only if Owner approves limited summary visibility.

Allowed first-cycle data:

- Selected permitted company.
- AR total by aging bucket.
- AP total by aging bucket.
- Count of overdue AR/AP documents by bucket.
- Currency labels according to approved currency policy.
- Restricted/unavailable indicators for deferred lanes.

Blocked data/actions:

- GL account balances.
- GL Entry detail.
- Cash and bank balances.
- Tax posture.
- Close readiness.
- Invoice line/detail.
- Payment, posting, reconciliation, write-off, export, or native route action.

Route/page expectation:

- Future productized Finance workspace overview route only after F2 approval.
- No default Desk takeover in F1.

Backend expectation:

- One allowlisted overview method after F3 approval.
- Company and role checks before computation.
- Aggregate-only payload.

UI expectation:

- Minimal command center, not dense dashboard sprawl.
- Calm posture cards and worklist entry points only.
- No fake disabled future cards that look active.

Validation expectation:

- Aggregate-only tests.
- Role and company tests.
- No native route/action tests.
- No-effect flag tests.

Owner manual check:

- Owner confirms the overview does not imply financial statement certification, cash truth, close readiness, or posting authority.

### Receivables

Business purpose:

- Help Finance identify customer money risk and overdue receivables.
- Keep collections/payment actions out of Cycle 1.

Users:

- Accounts User.
- Accounts Manager.
- Auditor if approved.
- Finance Manager if custom role is later approved.

Allowed first-cycle data:

- Sales Invoice header-level AR aging fields only if Owner approves customer-level visibility.
- Candidate fields: invoice identifier, company, customer, posting date, due date, currency, outstanding amount, status, aging bucket.
- Aggregate AR bucket totals if customer-level visibility is not approved.

Blocked data/actions:

- Sales Invoice line items.
- Tax rows.
- Margin/profit detail.
- Email/send/dunning/statement actions.
- Payment Entry creation.
- Write-off.
- Payment reconciliation.
- Sales Invoice submit/cancel/amend.
- Native Sales Invoice route.
- Export/download.

Route/page expectation:

- Future productized receivables lane or worklist only.
- No native Accounts Receivable report route unless separately approved as a governed exception.

Backend expectation:

- Invoice-led AR read with controlled fields, company scope, role checks, and permission checks.
- Aging basis, cutoff date, currency policy, credit/debit note handling, and payment allocation assumptions documented before implementation.

UI expectation:

- Focused AR posture list with clear aging buckets and restricted states.
- No collection workbench controls in Cycle 1.

Validation expectation:

- Field allowlist tests.
- Aging bucket tests.
- Company/role permission tests.
- Native route and mutation label scans.

Owner manual check:

- Owner decides whether customer-level balances are visible in Cycle 1.

### Payables

Business purpose:

- Help Finance identify supplier money risk and overdue payables.
- Keep payment and settlement actions out of Cycle 1.

Users:

- Accounts User.
- Accounts Manager.
- Auditor if approved.
- Finance Manager if custom role is later approved.

Allowed first-cycle data:

- Purchase Invoice header-level AP aging fields only if Owner approves supplier-level visibility.
- Candidate fields: invoice identifier, company, supplier, posting date, due date, currency, outstanding amount, status, aging bucket.
- Aggregate AP bucket totals if supplier-level visibility is not approved.

Blocked data/actions:

- Purchase Invoice line items.
- Tax rows.
- Supplier bank details.
- Payment Entry creation.
- Payment Order.
- Payment Reconciliation.
- Write-off.
- Purchase Invoice submit/cancel/amend.
- Native Purchase Invoice route.
- Export/download.

Route/page expectation:

- Future productized payables lane or worklist only.
- No native Accounts Payable report route unless separately approved as a governed exception.

Backend expectation:

- Invoice-led AP read with controlled fields, company scope, role checks, and permission checks.
- Aging basis, cutoff date, currency policy, advances, credit/debit notes, and payment allocation assumptions documented before implementation.

UI expectation:

- Focused AP posture list with clear aging buckets and restricted states.
- No payment workbench controls in Cycle 1.

Validation expectation:

- Field allowlist tests.
- Aging bucket tests.
- Company/role permission tests.
- Native route and mutation label scans.

Owner manual check:

- Owner decides whether supplier-level balances are visible in Cycle 1.

### Security/Stability/Owner Verification

Business purpose:

- Prove the Finance MVP is controlled, read-only, route-stable, and role-safe before closure.

Users:

- Owner/Main Control.
- Security/permission reviewer.
- ERP/accounting operations reviewer.
- UI/UX reviewer as needed.
- Accounts roles for manual smoke checks after implementation.

Allowed first-cycle data:

- Only data already allowed by the Overview, Receivables, and Payables lanes.

Blocked data/actions:

- All deferred lanes.
- All execution workflows.
- Any route, method, field, or action not allowlisted.

Route/page expectation:

- Direct route load, refresh, first-click navigation, restricted state, and unavailable state must be stable.

Backend expectation:

- Every method returns no-effect flags.
- Restricted users receive no data and no action targets.

UI expectation:

- Minimal, premium, operationally useful, no decorative dashboard sprawl.
- No active-looking controls that do nothing.

Validation expectation:

- Full Cycle 1 validation suite before closure.

Owner manual check:

- Required before F6 and before any Cycle 1 closure claim.

## 8. Deferred Lane Register

| Deferred lane | Why deferred | Risk | Prerequisite | Reopen condition |
| --- | --- | --- | --- | --- |
| Cash & Bank | Bank data and reconciliation behavior are highly sensitive. | Bank identifiers, transaction descriptions, treasury exposure, reconciliation mutation. | Treasury role policy, masking policy, no-reconcile contract. | Cycle 2 design accepted. |
| GL / Trial Balance | GL reads require ERPNext permission, company, finance-book, dimension, cancelled-entry, and report semantics. | Ledger leakage, incorrect totals, native report escape. | Allowlisted report contract and GL detail policy. | Cycle 2 design accepted. |
| Tax / Compliance | Tax data and reports affect compliance posture and may expose tax registration details. | Filing authority, tax ID exposure, jurisdiction risk. | Tax role/visibility policy and no-filing contract. | Cycle 3 design accepted. |
| Period Close | Period close and PCV affect accounting truth. | Close certification, irreversible accounting posture, period blocking. | Controller authority policy and close-readiness vocabulary. | Cycle 3 design accepted. |
| Custom review/request records | Custom records are a write surface even if they do not post. | Audit/idempotency gaps, implied execution, duplicate requests. | Approved custom record contract and tests. | Cycle 4 design accepted. |
| Cross-workspace accounting impact | Sales, Procurement, Warehouse, Inventory/Admin, and Finance ownership must be coordinated. | Conflicting authority and premature accounting conclusions. | Cross-workspace handoff contract. | Cycle 5 design accepted. |
| Reports / Statements | Financial statements can imply certification and may expose broad data. | Misstated truth, native report route, export risk. | Statement posture policy and report allowlist. | Later report cycle accepted. |
| Admin / Setup visibility | Setup data can mutate accounting behavior. | COA, dimensions, fiscal year, tax, bank setup exposure. | Admin/setup visibility matrix. | Later admin visibility cycle accepted. |
| Execution workflows | Posting/payment/reconciliation/close/tax actions mutate accounting truth. | Ledger, commercial, legal, bank, and compliance effects. | Separate Owner/Security approved execution phase. | Future execution phase accepted. |

## 9. Custom Review / Request Record Contract

Custom review/request records are deferred from Cycle 1, but this contract defines the minimum conditions before activation.

Likely record types:

- Finance Receivables Review Request.
- Finance Payables Review Request.
- Finance Payment Match Review Request.
- Finance Journal Adjustment Review Request.
- Finance Write-off Review Request.
- Finance Bank Match Review Request.
- Finance Tax Setup Review Request.
- Finance Period Close Review Request.
- Finance Master Data Change Review Request.

Allowed fields:

- Server-generated request ID.
- Request type.
- Company.
- Source DocType from an allowlist.
- Source document identifier.
- Party type and party identifier where allowed.
- Amount summary.
- Currency.
- Posting date or due date where allowed.
- Reason code.
- Priority.
- Status.
- Requester.
- Assigned reviewer role.
- Policy version.
- Payload hash.

Forbidden fields:

- GL Entry line payloads.
- Bank account identifiers.
- Full bank transaction descriptions.
- Tax registration identifiers.
- Sales Invoice line details.
- Purchase Invoice line details.
- Native route strings.
- Raw report payloads.
- Raw SQL/query text.
- External recipient fields.
- Commands or flags for submit, cancel, post, pay, reconcile, write off, close, file tax, send email, or notify party.

Role ownership:

- Accounts User may create only future approved review requests.
- Accounts Manager or proposed Controller may triage only after role approval.
- Auditor may read only if approved.
- System Manager does not automatically receive finance business ownership.
- Owner/Executive visibility must be explicitly approved.

Request ID rules:

- Request IDs must be server-generated.
- Request IDs must be immutable.
- Request IDs must include enough scope to prevent cross-company or cross-source collision.
- A request ID cannot be reused for a different payload.

Idempotency requirements:

- Duplicate same payload returns the existing request with `duplicate_ignored: true`.
- Same request ID with a different payload is rejected.
- Payload hash must be stored and compared.
- Repeated browser submission must not create duplicate requests.

Duplicate/reuse rejection:

- Reused request ID with different company, source, party, amount, reason, or request type must fail.
- Closed request reuse must not create a new implied execution path.

Append-only event log:

Every request must have append-only events for:

- create;
- status change;
- reviewer assignment;
- comment;
- duplicate ignored;
- rejection.

Event metadata must include actor, role, timestamp, company, previous status, new status, policy version, request ID, and request payload hash.

No-effect response flags:

Every custom request response must include false flags for document creation/update, GL creation, Journal Entry creation, Payment Entry creation, reconciliation, tax filing, period close, notification, and export.

Source reference policy:

- Source references must use productized labels, not native ERP routes.
- Source DocTypes must be allowlisted.
- Source document read permission and company permission must be verified before request creation.

Native route/reference visibility policy:

- No `/app/`, `Form`, `List`, `Report`, `query-report`, or `open_native_report` values in custom request payloads.
- No source route should be displayed unless it is a productized Finance route approved in the manifest.

Audit metadata:

- Company.
- Request type.
- Source DocType and source name.
- Actor.
- Actor roles relevant to the action.
- Policy version.
- Payload hash.
- No-effect flags.
- Created/modified timestamps.

Tests required before activation:

- Idempotency tests.
- Duplicate/reuse rejection tests.
- Role and company permission tests.
- Forbidden field tests.
- Native route absence tests.
- No ledger/payment/journal/reconciliation/tax/close writes.
- No email, notification, background job, attachment generation, or export.
- Append-only event tests.

Custom review/request records must not imply posting, payment, reconciliation, tax filing, write-off, close execution, notification, or external action.

## 10. Boundary Contract

F1 does not approve:

- GL Entry mutation.
- Journal Entry lifecycle.
- Payment Entry lifecycle.
- Sales Invoice lifecycle.
- Purchase Invoice lifecycle.
- Bank reconciliation mutation.
- Payment reconciliation mutation.
- Period Closing Voucher creation, submission, cancellation, or amendment.
- Tax filing or tax submission.
- Write-off execution.
- Close execution.
- Notification, email, customer, supplier, bank, portal, or external action.
- Native ERP route execution.
- Export/download.
- File attachment generation.
- Commit, push, live alignment, restart, migration, metadata reload, protected gate, or release action.

F1 also does not approve:

- Runtime JavaScript changes.
- Python service changes.
- DocType changes.
- Registry activation.
- Governance manifest activation.
- Test/smoke file changes.
- Live file changes.
- Metadata changes.

## 11. Validation And Review Gates

Required before F2 can start:

- F1 docs review.
- Security/permission review.
- ERP accounting operations review.
- UI/UX review if needed.
- Owner/Main Control acceptance.

Future technical gates for F2-F6, when implementation is approved:

- `git diff --check`.
- Python compile.
- Unit tests.
- JavaScript syntax checks.
- Static scan for forbidden methods.
- Native route scan.
- Field allowlist tests.
- Role/company permission tests.
- Empty/restricted/unavailable/error state tests.
- No-effect flag tests.
- Smoke tests.
- Owner manual review.

Minimum future static scans must cover:

- `insert`
- `save`
- `submit`
- `cancel`
- `delete`
- `frappe.db.set_value`
- `ignore_permissions=True`
- `frappe.get_all`
- `frappe.db.sql`
- `/app/`
- `Form`
- `List`
- `Report`
- `query-report`
- `open_native_report`
- `Submit`
- `Cancel`
- `Post`
- `Pay`
- `Reconcile`
- `Write off`
- `Close Period`
- `Export`
- `Download`

F1 validation for this docs-only task is limited to:

- `git diff --check HEAD`.
- Trailing whitespace check on this document and README.
- Focused boundary scan showing risky terms appear only as blocked, deferred, forbidden, or validation policy language.
- `git status --short --branch`.

Runtime tests are not required for F1 because F1 changes only documentation.

## 12. Open Owner/Main Control Decisions

Owner/Main Control must decide:

1. Final visible workspace name.
2. Whether customer-level balances are visible in Cycle 1 or aggregate-only.
3. Whether supplier-level balances are visible in Cycle 1 or aggregate-only.
4. Whether Owner/Executive is a real ERPNext role, a custom role, or a manual business-review identity.
5. Company filter default.
6. Whether multi-company consolidation remains blocked or receives a separately approved read-only policy.
7. Currency display policy: document currency, company currency, presentation currency, or multiple labeled values.
8. Export/download policy. Default is blocked.
9. Whether F2 shell may be visible to all accounting roles or manager-only at first.
10. Whether `Finance Control Desk` is the approved product/page label.
11. Whether Accounts User can see customer/supplier-level names or only aggregate buckets.
12. Whether Auditor receives Cycle 1 data by default or only by company-specific permission.
13. Whether System Manager can view Finance business data or only setup/admin context.

## 13. Recommended Next Step

Recommended next step:

1. Owner/Main Control reviews this F1 docs-only governance/scope contract.
2. Security/permission reviewer confirms the data visibility and read-only backend contract.
3. ERP/accounting operations reviewer confirms the business usefulness and deferrals.
4. UI/UX reviewer confirms the first-cycle workspace remains minimal and not dashboard sprawl.
5. If accepted, proceed to F2 shell/registry/governance manifest planning only.

No Finance & Accounting implementation should begin until F1 is accepted.
