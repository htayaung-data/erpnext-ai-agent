# Finance & Accounting Capability Map and Integration Plan

**Main Control authority:** Main Control v2

**Decision:** `capability_map_ready_for_owner_decision`

**Status:** canonical architecture and roadmap-planning package; Owner decision pending

**Baseline:** `feature/erpnext-ui-design` at `d2aea503ab7375299d929be61731a9bd79421b54`

**Date:** 2026-07-17

**Implementation state:** Finance Cycle 2 is not started; no capability is selected or approved

## 1. Purpose, authority, and precedence

This document is the canonical Finance & Accounting capability map, integration plan, dependency model, sequencing record, deferred-scope register, and decision framework for the ERP AI project. It is a planning outcome only. It does not implement a capability, change a role or permission, authorize Finance-to-AI access, or approve staging, commit, push, live alignment, migration, metadata work, a protected gate, or accounting execution.

Project state is reconciled through the accepted Main Control v2 transition handoff, the Codex delivery operating model, and the latest accepted closure and protection artifacts. A later accepted closure or handoff supersedes an older phase label that still says `pending`, `blocked`, or `source-only`. Historical documents remain evidence of the path taken; they do not override the latest accepted state. Current repository behavior remains decisive if it contradicts a document.

The source repository is authoritative:

- repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
- branch/upstream: `feature/erpnext-ui-design` / `origin/feature/erpnext-ui-design`
- baseline revision: `d2aea503ab7375299d929be61731a9bd79421b54`
- baseline message: `docs(governance): add Main Control v2 handoff`
- live deployment tree: explicitly outside this planning outcome

The four accepted unrelated exclusions remain outside this candidate and must not be staged, cleaned, used as roadmap authority, or copied to live:

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## 2. Evidence method and source precedence

The review was bounded to current architecture truth. It did not re-audit every historical phase. Accepted closure evidence was reopened only where current committed repository evidence could materially contradict it.

Source precedence is:

1. current committed source behavior and exact metadata at the baseline;
2. latest accepted Main Control handoff, closure, and formal protection artifacts;
3. installed ERPNext/Frappe structures recorded by accepted source-proof artifacts;
4. primary official ERPNext/Frappe documentation where repository proof is insufficient;
5. older planning and phase artifacts as historical context only.

Financial semantics are not inferred from a field name, UI label, report name, or workspace payload. A capability remains unavailable until its installed source behavior, lifecycle, permission behavior, currency basis, date/period rules, and reconciliation boundary are proven.

Primary official references used to bound, not replace, installed-source proof include:

- [Payment Terms](https://docs.frappe.io/erpnext/payment-terms) and [Payment Terms Template](https://docs.frappe.io/erpnext/payment-terms-template)
- [Payment Ledger](https://docs.frappe.io/erpnext/payment_ledger)
- [Accounting Reports](https://docs.frappe.io/erpnext/accounting-reports)
- [Bank Transaction](https://docs.frappe.io/erpnext/bank-transaction) and [Bank Reconciliation](https://docs.frappe.io/erpnext/bank-reconciliation)
- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period) and [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher)
- [Multi Currency Accounting](https://docs.frappe.io/erpnext/multi-currency-accounting), [Finance Book](https://docs.frappe.io/erpnext/finance-book), [Inter Company Invoices](https://docs.frappe.io/erpnext/inter-company-invoices), [Inter Company Journal Entry](https://docs.frappe.io/erpnext/inter-company-journal-entry), and [Exchange Rate Revaluation](https://docs.frappe.io/erpnext/exchange-rate-revaluation)
- [Tax Rule](https://docs.frappe.io/erpnext/tax-rule) and [Tax Withholding Category](https://docs.frappe.io/erpnext/tax-withholding-category)
- [Accounting Dimensions](https://docs.frappe.io/erpnext/v14/user/manual/en/accounts/accounting-dimensions) and [Budget](https://docs.frappe.io/erpnext/budget)
- [Perpetual Inventory](https://docs.frappe.io/erpnext/perpetual-inventory), [Accounting of Inventory Stock](https://docs.frappe.io/erpnext/accounting-of-inventory-stock), [Stock Received But Not Billed](https://docs.frappe.io/erpnext/stock-received-but-not-billed), and [Asset Depreciation](https://docs.frappe.io/erpnext/asset-depreciation)
- Frappe [Database API permission distinction](https://docs.frappe.io/framework/user/en/api/database) and [Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions)

## 3. Reconciled current state

### 3.1 Finance Cycle 1

Finance Cycle 1 is closed only for its bounded, read-only aggregate posture:

- one custom Finance Control Desk route;
- Accounts Manager aggregate access after server-resolved role, company, and source-read gates;
- Accounts User shell/unavailable posture without manager aggregates;
- aggregate Sales Invoice AR aging counts;
- manager-only guarded MMK Payment Ledger AR amount buckets with exact voucher-set reconciliation and low-population suppression;
- aggregate Purchase Invoice AP count posture that fails closed on unsupported Payment Schedule, advance, hold, return, future-activity, permission, or malformed-source conditions;
- no customer, supplier, invoice, voucher, account, bank, tax, or employee identities in the public Finance payload;
- no native report, list, form, export, download, print, email, notification, mutation, payment, reconciliation, posting, closing, filing, or other execution path.

Cycle 1 does not prove installment aging, AP amounts, GL, trial balance, cash, bank, reconciliation, tax, closing, statements, consolidation, budgeting, accounting execution, or Finance-to-AI access. Prior authenticated browser and source/live evidence is historical acceptance for the exact F6F scope; it is not fresh acceptance for any future capability.

### 3.2 Known business and technical facts

| Fact | Current truth | Constraint |
| --- | --- | --- |
| Visible Finance company | `Mingalar Mobile Distribution Co., Ltd.` | Current Cycle 1 approved scope only; not a reusable multi-company policy. |
| Current Finance currency | MMK | Current AR amount contract only; presentation, document, account, and foreign-currency rules remain unproved. |
| Current page roles | Accounts Manager, Accounts User | Accounts Manager alone receives current aggregate data. Auditor and specialist roles are not approved. |
| Landing precedence | `Sales > Procurement > Finance > Warehouse` | Must not change incidentally. |
| Search/navigation | Finance search disabled; one Overview surface | No native-route escape or unregistered target. |
| Finance actions | Overview and Refresh only | Refresh is read-only; no workflow or accounting effect. |
| Shared runtime | lifecycle, teardown, shell, managed navigation, request isolation, responsive/accessibility contracts | Domain adapters own accounting semantics and authority; shared code must not acquire them. |
| Current versions | Point-in-time versions recorded by the accepted handoff | Re-prove installed structures and behavior at the start of any implementation outcome. |

### 3.3 Owner facts still unknown

No architecture may silently decide these facts:

- legal entities, branches, consolidation groups, elimination entities, and intercompany policy;
- operating, account, document, settlement, and presentation currencies and exchange-rate sources;
- chart-of-accounts ownership, fiscal calendars, open-period policy, close/reopen authority, and audit/certification model;
- tax jurisdictions, registrations, filing obligations, withholding, localization, and statutory retention;
- bank accounts, signatories, statement providers, reconciliation ownership, payment rails, and treasury segregation;
- materiality thresholds, aging definitions, credit/collections policy, payable timing, and installment volume;
- inventory valuation methods, negative-stock policy, landed costs, manufacturing, WIP, and stock-account ownership;
- assets, depreciation books, deferred accounting, opening balances, payroll, expense claims, financing, leases, investments, and equity requirements;
- budget owners, forecasting process, dimensions, cost centers, projects, and sparse-slice privacy policy;
- data retention, immutable audit evidence, backup/recovery, migration, integrations, volume, latency, and operational support requirements.

Unknown means Owner confirmation is required. No domain is classified `not applicable` at this gate because applicability has not been authoritatively ruled out.

## 4. Current-state ownership and protection matrix

| Surface | Source-of-truth owner | Accepted current state | Protection boundary | Change gate |
| --- | --- | --- | --- | --- |
| Sales | Sales workspace adapter and accepted Sales protection package | Productized custom Sales behavior; governed native exceptions only where explicitly declared | Preserve routes, landing, role authority, request isolation, managed navigation, and accepted browser behavior; Finance must not treat a Sales UI payload as accounting truth or mutate Sales incidentally | Formal Sales protected gate for triggered shared/runtime change; exact allowlist and separate live approval |
| Procurement | Procurement workspace adapter and accepted Procurement protection package | Productized custom PR/RFQ/SQ/PO posture; receive, bill, pay, and lifecycle mutation remain outside accepted workspace behavior | Preserve routes, roles, company isolation, no-native-escape posture, and accepted browser behavior; Finance does not inherit Procurement role authority | Formal Procurement protected gate for triggered shared/runtime change; exact allowlist and separate live approval |
| Warehouse | Warehouse adapter and W16H accepted custom-workflow closure | Accepted custom workflow scope; ERP stock valuation and accounting execution remain deferred | Preserve custom routes, records, role boundaries, request isolation, navigation, and accepted browser behavior; custom workflow status is not SLE/GL truth | Warehouse regression evidence for impacted runtime; formal protection status must not be overstated |
| Finance | Finance adapter, Finance page, resolver, and accepted F6F closure | Closed Cycle 1 aggregate-only read posture | Preserve role separation, one-company scope, aggregate-only schemas, fail-closed semantics, identity suppression, stale-state clearing, and no-execution boundary | Finance tests and browser evidence for future authorized scope; separate approval for every role, data, action, and live step |
| Shared UI | Shared Core platform contracts | Owns lifecycle, shell, sidebar/header/filter grammar, accessibility/responsiveness, target validation, request isolation, and teardown | Must remain domain-neutral; may not broaden roles, sources, native routes, reports, exports, actions, or accounting authority | Impact analysis, exact shared allowlist, formal Sales/Procurement and applicable Warehouse/Finance regressions, independent review, separate live approval |
| Boot routing | `erp_workspace_ui/boot.py` | Managed landing and role-to-workspace selection | Preserve `Sales > Procurement > Finance > Warehouse`; Finance roles must not displace higher-precedence accepted landing | Routing ownership lock plus all impacted workspace gates |
| Registries | workspace and browser registries | Exact workspace identities, routes, targets, and cached-workspace validation | No implicit target, page, report, role, or action expansion; stale phase labels are traceability debt, not runtime authority | Registry ownership lock, parity tests, no opportunistic cleanup |
| Governance | governance manifest and accepted standards | Finance exposes only Overview and Refresh; native routes and execution are blocked | Manifest authority must match page, service, registry, and visible copy | Exact manifest allowlist and governance review; permission/metadata approval remains separate |
| AI Assistant | separate `ai_assistant_ui` runtime | Not part of Finance Cycle 1 and not approved as a Finance data consumer or actor | AI cannot obtain broader data than the user, become an accounting source, choose accounting treatment, approve, post, pay, reconcile, close, or execute | Separate Owner-approved security/architecture task; committed data paths must be remediated and proven before any integration |
| Source/live alignment | Main Control release authority | Source is authoritative; historical F6F live evidence is bounded to Cycle 1 | Intentional drift must be documented; source tests and representative smoke are not authenticated live acceptance | Exact file allowlist, hashes, separate alignment approval, authenticated role-pair evidence, and no incidental live cleanup |

Sales and Procurement are formally protected. Warehouse and Finance have accepted bounded closures and must be preserved, but this document does not invent a formal-protection status not granted by their latest artifacts.

## 5. Mandatory architectural foundations

These are prerequisites, not a new implementation cycle.

### A. Canonical financial context

Every Finance response or action must carry or resolve one immutable context:

- authorized legal company and, when separately approved, an exact authorized consolidation set;
- exact `as_of`, `from_date`, `to_date`, fiscal year, accounting period, and timezone/calendar interpretation;
- company/base, account, document/transaction, settlement, and presentation currencies;
- exchange-rate type, source, date, precision, and rounding policy;
- Finance Book and exact dimension filters, including cost center and project;
- source/version identity and a consistency token or declared reconstruction boundary;
- role/purpose classification and data-sensitivity class.

Browser defaults, `User.defaults`, labels, route state, and cached prior context are never authorization.

### B. Accounting-source adapter framework

The current narrow report adapter is not sufficient for the complete map. Future source adapters must declare:

- authoritative DocType/report/query and installed-version proof;
- permission-preserving read method and field allowlist;
- document lifecycle states included and excluded;
- posting, cancellation, return, amendment, advance, allocation, write-off, and future-activity semantics;
- date, period, currency, dimension, and sign rules;
- duplicate, malformed, partial, oversized, concurrent-change, and unsupported-state behavior;
- consistency mode: same-snapshot read, bounded reconstruction, or explicit reconciliation;
- identity suppression/coarsening and aggregate privacy threshold;
- exact public schema, source freshness, and fail-closed reason codes.

### C. Posting-lineage and reconciliation framework

No total becomes authoritative merely because it can be queried. Required control pairs include:

- invoice and Payment Schedule to Payment Ledger allocation and subledger balance;
- AR/AP subledger to GL control accounts;
- Payment Ledger and vouchers to GL postings;
- Stock Ledger Entry and valuation layers to inventory, COGS, GRNI, and WIP GL;
- bank statement/Bank Transaction to bank GL and payment/journal vouchers;
- tax rows and withholding to tax GL and statutory returns;
- GL to trial balance, statements, retained earnings, and close vouchers;
- asset schedules to depreciation and asset GL;
- intercompany pairs, exchange differences, eliminations, and consolidation outputs.

Every mismatch has a named owner, fail-closed threshold, exception queue, aging/escalation policy, and closure evidence.

### D. Permission, privacy, and segregation-of-duties model

The future model must distinguish at least requester/preparer, reviewer, approver, poster, payment preparer, payment releaser, reconciler, close controller, reopen approver, tax preparer, tax filer, auditor, system administrator, and break-glass authority. It must define prohibited combinations, maker-checker requirements, company and dimension scope, sensitive account classes, and action-time reauthorization.

Role membership is necessary but insufficient. Every read and action also requires company, period, source DocType, field, row, dimension, and purpose authority. Finance authority is not inherited from Sales, Procurement, Warehouse, `System Manager`, Executive, or AI roles.

### E. Master-data ownership and control

Owner-approved authorities are required for Company, chart of accounts, Account Types, fiscal year/period, Currency, exchange rates, Finance Book, cost centers, projects, dimensions, tax templates/rules/registrations, banks/accounts, payment terms, parties, items, warehouses, assets, and intercompany mappings. Creation/change/disable/merge effects require audit, effective dating, dependency checks, and separate approval.

### F. Execution and operational control envelope

Any future Tier 3 action requires a separately approved command contract with action-time authorization, maker-checker, idempotency key, replay protection, immutable audit event, atomicity boundary, reconciliation result, retry/recovery semantics, observability, and a documented rollback or compensating path. Approval never implies posting; posting never implies payment; reconciliation never implies voucher creation; code acceptance never authorizes live execution.

## 6. Capability status taxonomy

Status meanings:

- **accepted-current:** closed only within the cited Cycle 1 boundary;
- **mapped-deferred:** included in canonical roadmap truth but not approved for implementation;
- **foundation-required:** architecture prerequisite before a dependent outcome;
- **unknown-applicability:** Owner business fact required before sequencing;
- **not-applicable:** none accepted at this gate.

| ID | Capability domain | Current status | Dependency posture |
| --- | --- | --- | --- |
| GOV-01 | Governance, release, source/live, audit evidence | foundation-required | Applies to every outcome |
| FND-01 | Financial masters and canonical financial context | foundation-required | First architecture dependency |
| FND-02 | Accounting-source adapters, consistency, lineage, reconciliation | foundation-required | After FND-01; before totals or actions |
| C1-01 | Cycle 1 aggregate AR/AP foundation | accepted-current | Protected baseline, not a general ledger foundation |
| AR-01 | AR aging and receivables expansion | mapped-deferred | Installment, PLE, authority, privacy proof |
| AR-02 | Payment Schedule and installment semantics | mapped-deferred | Parent/child/lifecycle proof before installment aging |
| AP-01 | AP aging and AP amount posture | mapped-deferred | AR-02 semantics, Supplier PLE, authority/privacy proof |
| SUB-01 | Payment Ledger and subledger integrity | mapped-deferred | FND-02; unlocks reliable AR/AP controls |
| GL-01 | General Ledger and trial balance posture | mapped-deferred | FND-01/FND-02; source/report semantic proof |
| TRE-01 | Cash, bank, liquidity, and reconciliation | mapped-deferred | Treasury authority; GL required for monetary liquidity |
| TAX-01 | Tax posture and statutory controls | mapped-deferred; unknown-applicability details | Jurisdiction/localization facts, tax-to-GL reconciliation |
| PER-01 | Fiscal period, close, reopen, and audit controls | mapped-deferred | GL/TB, period policy, SoD, immutable evidence |
| REP-01 | Financial statements and management reporting | mapped-deferred | GL/TB and close-state/version policy |
| ENT-01 | Multi-company, intercompany, consolidation, currency, Finance Book | mapped-deferred; unknown-applicability details | New authority model and elimination/revaluation controls |
| MGT-01 | Budgeting, forecasting, cost centers, projects, dimensions | mapped-deferred; unknown-applicability details | Dimension authority and actuals version |
| INV-01 | Stock valuation, COGS, GRNI, WIP, landed/manufacturing accounting | mapped-deferred; unknown-applicability details | Stock lifecycle and GL lineage proof |
| AST-01 | Fixed assets, depreciation, deferred accounting, opening balances | mapped-deferred; unknown-applicability details | Asset/books/period policy and GL lineage |
| CAP-01 | Debt, interest, investments, equity, dividends, leases | mapped-deferred; unknown-applicability details | Owner applicability and specialist accounting policy |
| PEO-01 | Expense claims, payroll, employee liabilities and privacy | mapped-deferred; unknown-applicability details | HR/payroll authority and restricted-data policy |
| XWS-01 | Cross-workspace accounting integration | foundation-required | Contracted before dependent productization |
| ACT-01 | Notifications, approvals, controlled actions, accounting execution | mapped-deferred | Read posture, SoD, command envelope, recovery first |
| AI-01 | AI advisory access and prohibited AI authority | mapped-deferred with stop gate | Separate security architecture and permission-preserving adapter |

## 7. Domain control records

Each record below is authoritative for outcome, source, semantics, authority/context, read/write boundary, dependencies, workspace/Shared UI impact, risks, assurance, and explicit deferral.

### GOV-01 — Governance, release, source/live, and audit evidence

- **Business outcome and source:** one truthful roadmap, exact candidate scope, independently reviewable evidence, and deliberate source/live state. Main Control handoff, operating model, governance manifest, registries, Git evidence, and accepted closures are authoritative.
- **Semantics and context:** distinguish design, source acceptance, staging, commit, push, live alignment, metadata, permission, protected gate, browser acceptance, and business closure. None implies another.
- **Authority and boundary:** Main Control owns phase authority and scope adjudication; Owner approves material business scope and every external-state gate. This domain does not itself approve a runtime effect.
- **Dependencies and impact:** applies to all workspaces and Shared UI. Exact file allowlists and ownership locks are mandatory; intentional drift must be documented.
- **Leakage/permission risks:** overclaiming test evidence, stale status labels, broad staging, live drift, or accidental inclusion of exclusions.
- **Assurance and closure:** exact revision/upstream/index/status; exclusion hashes; candidate manifest; static references/whitespace; evidence scorecard; one independent review; separate live proof when applicable.
- **Explicitly deferred:** staging, commit, push, live work, metadata, permissions, protected gates, and operational acceptance.

### FND-01 — Financial masters and canonical financial context

- **Business outcome and source:** every financial fact is labeled with an authorized entity, period, currency, book, dimension, source version, and consistency boundary. ERPNext Company, Account/Chart of Accounts, Fiscal Year, Accounting Period, Currency/Exchange Rate, Finance Book, Cost Center, Project, dimensions, and controlled master data are authoritative after installed proof.
- **Required semantics:** company/base versus account, document, settlement, and presentation currency; exchange source/date; precision/rounding; posting versus due/clearance dates; fiscal/closed period; dimension intersection; effective-dated master changes.
- **Role/company authority:** explicit company and dimension authorization; separate consolidation authority; master-data steward and approver roles. Defaults and browser values never grant access.
- **Read/execution boundary:** read-only context resolution may precede reports; master changes remain controlled execution with dependency and audit checks.
- **Dependencies and impact:** first dependency for every domain; Sales, Procurement, Warehouse, Finance, routing caches, and AI must consume the same authorized identifiers without sharing workspace role authority. Shared UI may display context but may not resolve authorization.
- **Risks:** cross-company union, stale cache, rate manipulation, closed-period mislabeling, dimension inference, and master-data drift.
- **Assurance and closure:** denial/ambiguity/cap tests, currency and calendar boundary fixtures, effective-date tests, cross-context cache isolation, master ownership sign-off, installed metadata proof, authenticated live evidence when productized.
- **Explicitly deferred:** multi-company selection, presentation currency, master maintenance, and permission changes.

### FND-02 — Accounting-source adapters, consistency, lineage, and reconciliation

- **Business outcome and source:** reproducible financial results with named source documents and reconciliation controls. Installed ERPNext document/report logic is authoritative only after adapter-specific proof.
- **Required semantics:** lifecycle states, cancellations/returns/amendments, allocations/advances/write-offs, future activity, signs, date basis, currencies, dimensions, snapshot/reconstruction policy, and exact reconciliation pairs.
- **Role/company authority:** permission-preserving reads, exact field/row/purpose scopes, sensitive-account controls, and no raw unrestricted query shortcut.
- **Read/execution boundary:** adapters may read and reconcile; correction/posting remains separate execution.
- **Dependencies and impact:** follows FND-01 and precedes all new totals. It may consume Sales Invoice, Purchase Invoice, Payment Schedule, Payment Ledger, GL Entry, Stock Ledger Entry, Bank Transaction, tax, asset, and close records without making source workspaces accounting owners.
- **Shared UI impact and risks:** no shared accounting adapter; Shared UI accepts a validated public schema only. Risks include double counting, mixed snapshots, orphaned ledger rows, identity leakage, and partial results.
- **Assurance and closure:** golden fixtures, malformed/duplicate/concurrent cases, permission denials, exact schemas, reconciliation thresholds, source-version proof, independent accounting review, and live tie-out for productized results.
- **Explicitly deferred:** all new adapters and reconciliation queues.

### C1-01 — Existing Cycle 1 aggregate foundation

- **Business outcome and source:** bounded manager awareness of AR aggregate posture and AP count availability. Current Finance service/page/tests/metadata, registry/governance, and F6F closure are authoritative.
- **Required semantics:** SI count buckets use submitted positive outstanding non-return invoices and due-date/as-of rules; AR MMK amounts use reconciled Payment Ledger voucher sets with privacy suppression; AP is PI count-only and fails closed on unsupported semantics.
- **Role/company/context:** Accounts Manager plus server-resolved selected company and source permissions; Accounts User shell only; current approved company/MMK scope.
- **Read/execution boundary:** strictly read-only aggregates with no identity, row, native surface, export, notification, or execution.
- **Dependencies and impact:** protected baseline for future Finance; landing and Shared UI lifecycle remain unchanged. It does not provide GL, cash, tax, close, or AI truth.
- **Risks:** later code broadening schemas or role/company scope, weakening fail-closed behavior, or treating Cycle 1 totals as ledger certification.
- **Assurance and closure:** preserve current unit/cross-workspace/smoke/browser evidence; rerun triggered gates for future runtime changes; exact role/company/identity regression.
- **Explicitly deferred:** every capability beyond this exact posture.

### AR-01 — AR aging and receivables expansion

- **Business outcome and source:** reliable collection posture, aging, credit exposure, disputed/overdue visibility, and eventually controlled collection workflow. SI, Payment Schedule where applicable, Payment Ledger, Payment Entry/Journal allocations, Credit Notes/returns/write-offs, and GL controls are candidate sources after proof.
- **Required semantics:** invoice versus installment aging; posting/due/as-of dates; advances/unallocated payments; partial allocations; credit notes, returns, write-offs, disputes, future activity, and subledger-to-GL tie-out.
- **Role/company/context:** company and collection-purpose roles; row access requires separate Owner approval. Currency labels must distinguish invoice and company amounts; periods/dimensions must be explicit.
- **Read/execution boundary:** aggregates first; customer/invoice rows, contacts, credit controls, communications, allocation, write-off, and collection actions are separate approvals.
- **Dependencies and impact:** FND-01/FND-02, AR-02, SUB-01; consumes Sales accounting documents without changing Sales routes or roles. Shared UI impact is none unless a generic contract is separately approved.
- **Risks:** customer/invoice identity inference, credit sensitivity, wrong aging basis, schedule double counting, multi-currency distortion, and Sales-role inheritance.
- **Assurance and closure:** schedule/no-schedule fixtures, allocation/credit/return/future cases, exact reconciliation, low-population privacy, role/company/field denial, no-native-route tests, accountant review, authenticated role-pair live tie-out.
- **Explicitly deferred:** rows/drilldowns, credit decisions, reminders, dunning, allocation, write-off, export, communication, and execution.

### AR-02 — Payment Schedule and installment semantics

- **Business outcome and source:** accurate installment-level due posture without misclassifying an invoice or exposing child rows. ERPNext Payment Terms, Payment Terms Template, parent invoice, and Payment Schedule child records are authoritative only through parent/lifecycle proof.
- **Required semantics:** template and template-less schedules; allocation percentages/amounts; invoice grand total and currency; term bases and due-date calculation; amendments/cancellations/returns; rounding residuals; partial payment allocation across installments; duplicate or regenerated schedules.
- **Role/company/context:** parent document permission and company authority must be proven for every child fact; child tables are never an independent broad data source. Date, currency, and precision inherit from a validated parent contract.
- **Read/execution boundary:** safe detection already supports Cycle 1 fail-closed behavior; installment interpretation and display remain read-only candidates. Changing terms or allocating payments is execution.
- **Dependencies and impact:** FND-01/FND-02; prerequisite for installment-aware AR/AP and AP amounts. Sales/Procurement document behavior remains owned by ERP lifecycle, not Finance UI.
- **Risks:** invoice identity and amount leakage, orphan/duplicate child rows, wrong parent inheritance, total mismatch, and false confidence from a single fixture.
- **Assurance and closure:** installed metadata and lifecycle proof, parent-child permission tests, template/no-template/mixed-currency/rounding/allocation fixtures, exact sum and duplicate controls, independent accounting/security review, live tie-out without row exposure.
- **Explicitly deferred:** schedule rows, edits, payment allocation, native forms, and any claim that current AP unavailable posture represents installment aging.

### AP-01 — AP aging and AP amount posture

- **Business outcome and source:** reliable liability timing and cash-needs posture. PI, Payment Schedule, Supplier Payment Ledger, Payment Entry/Journal allocations, debit notes/returns, advances, holds, and GL controls are candidate sources after proof.
- **Required semantics:** installment versus invoice due dates; payable sign; partial allocation; supplier advances; holds/disputes; debit notes/returns; overpayments; future activity; account/company/document currency; subledger-to-GL tie-out.
- **Role/company/context:** manager/Treasury purpose and company authority; supplier amounts need diversity suppression and exact currency labeling. Procurement access never grants AP access.
- **Read/execution boundary:** current AP count-only fail-closed posture remains; AP amount aggregates are future read-only. Supplier/invoice rows, bank/contact/tax identifiers, payment runs, and voucher creation are separate.
- **Dependencies and impact:** AR-02 and SUB-01 before reliable amount posture; FND foundations. Finance must not add receive/bill/pay actions to Procurement or bypass its boundary.
- **Risks:** supplier identity and liquidity-pressure inference, wrong currency/sign, unsupported schedules/advances/holds, duplicate liabilities, and premature payment authority.
- **Assurance and closure:** complete semantic fixtures, PLE/PI/GL reconciliation, suppression/coarsening, role/company/source denials, no supplier identity, accountant/security review, authenticated live tie-out.
- **Explicitly deferred:** AP amounts, rows, payment preparation, approvals, payment execution, exports, and communications.

### SUB-01 — Payment Ledger and subledger integrity

- **Business outcome and source:** controlled AR/AP outstanding balances and allocation lineage. Payment Ledger Entry plus authoritative vouchers and GL control accounts are sources after installed proof.
- **Required semantics:** party/account type, voucher/against-voucher lineage, posting date, due date, account and company currency, exchange differences, allocations, advances, write-offs, returns, cancellations, and future rows.
- **Role/company/context:** company, party-type, account, period, Finance Book, and dimension scope; raw party/voucher identities remain restricted.
- **Read/execution boundary:** read/reconcile first; allocations, corrections, write-offs, and reposting are execution.
- **Dependencies and impact:** FND-02; supports AR/AP and later GL controls. It must not become a native Payment Ledger passthrough.
- **Risks:** orphaned/misdirected rows, cross-company links, duplicate composites, identity leakage, mixed currencies, and inconsistent snapshots.
- **Assurance and closure:** composite-key reconciliation, bidirectional voucher-set equality, GL control tie-out, malformed/duplicate/future/concurrent tests, exact schema, accountant review, live sample tie-out under authorization.
- **Explicitly deferred:** public row access, allocation workbench, corrections, write-offs, reposting, and autonomous reconciliation.

### GL-01 — General Ledger and trial balance posture

- **Business outcome and source:** trustworthy ledger integrity and period opening/movement/closing balances, enabling later statements and close controls. GL Entry and installed General Ledger/Trial Balance report logic are authoritative after source and filter proof.
- **Required semantics:** debit/credit signs; opening, period movement, closing; cancelled/amended/return effects; Period Closing Voucher; Finance Book; account hierarchy; party, voucher, cost center, project and dimensions; base currency; provisional versus closed data.
- **Role/company/context:** Controller/Auditor-specific authority, exact company/period/book/dimensions, sensitive-account and payroll restrictions. Accounts User or generic `System Manager` is not a bypass.
- **Read/execution boundary:** aggregate account-level integrity posture first; GL rows, vouchers, export, journal creation, reposting, and close are separate.
- **Dependencies and impact:** FND foundations; unlocks monetary liquidity, statements, close, tax tie-outs, inventory controls, and management reporting. No native report passthrough.
- **Risks:** broad party/payroll/tax/intercompany inference, unbalanced or incomplete periods, hidden dimensions, huge result sets, mixed books/currencies, and false certification.
- **Assurance and closure:** installed report/source proof, opening+movement=closing invariants, debit/credit balance, hierarchy rollup, PCV/book/dimension fixtures, sensitive-account policy, denial/cap tests, independent accounting/security review, authenticated live tie-out.
- **Explicitly deferred:** GL/TB runtime, rows, drilldowns, exports, journals, corrections, certification, and close.

### TRE-01 — Cash, bank, liquidity, and reconciliation

- **Business outcome and source:** controlled visibility of bank-feed/reconciliation status, later GL-backed liquidity and governed reconciliation/payment operations. Bank Account, Bank Transaction, bank statements/imports, Payment Entry/Journal Entry, and bank GL accounts are candidate sources.
- **Required semantics:** bank statement versus book balance; value/transaction/posting/clearance dates; matched/unmatched/partially matched status; fees/interest/transfers; pending items; opening balance; currency; cut-off; duplicate import; reversal; reconciliation as-of.
- **Role/company/context:** Treasury and reconciler authority, masked account identifiers, company/account/currency/date scope, maker-checker for matching and voucher creation.
- **Read/execution boundary:** a non-monetary masked reconciliation-status proof may precede GL. Monetary liquidity requires GL/TB. Import, match, create voucher, update clearance, transfer, release payment, and credential access are execution.
- **Dependencies and impact:** FND foundations; GL-01 for monetary liquidity; ACT-01 for actions. Procurement may hand off payment-preparation facts but never execution authority. Shared UI must not expose bank identifiers.
- **Risks:** highly sensitive account/statement data, credential leakage, stale or double-counted balances, duplicate matches, unauthorized voucher creation, and conflating cash with available liquidity.
- **Assurance and closure:** masked schemas, Treasury role/company/account denials, duplicate/reversal/cut-off fixtures, bank-to-GL reconciliation, stale/concurrent match tests, SoD and idempotency for later actions, security/accounting review, authenticated Treasury live evidence.
- **Explicitly deferred:** monetary cash dashboard, statement rows/descriptions, bank import, matching, reconciliation effects, payments, transfers, credentials, and AI access.

### TAX-01 — Tax posture and statutory controls

- **Business outcome and source:** accurate tax liability/receivable posture and controlled statutory readiness. Installed transaction tax rows/templates, Tax Rule, withholding, tax accounts, localization reports/returns, and GL entries are authoritative after jurisdiction proof.
- **Required semantics:** jurisdiction, registration, place/date of supply, tax category/rule priority, inclusive/exclusive calculation, rounding, reverse charge, withholding, exemptions, credit notes, amendments, filing period, currency, recoverability, and tax-to-GL-to-return reconciliation.
- **Role/company/context:** Tax preparer/reviewer/filer roles; legal entity, registration, jurisdiction and period authority; tax IDs and filing artifacts restricted.
- **Read/execution boundary:** read-only posture/readiness first; return preparation, export, submission, amendment, payment, and certificate issuance are separate authorities.
- **Dependencies and impact:** Owner tax facts, FND/GL, Sales and Procurement document lifecycle contracts. Shared UI remains neutral.
- **Risks:** statutory error, identifier leakage, localization mismatch, incorrect period/rule, unreconciled GL, and treating advisory output as filing authority.
- **Assurance and closure:** jurisdiction-specific installed proof, authoritative test cases, transaction-to-GL-to-return tie-out, amendment/credit/withholding fixtures, permission/export controls, specialist review, regulator-appropriate live evidence.
- **Explicitly deferred:** all tax runtime, filings, exports, payments, registrations, and AI tax decisions.

### PER-01 — Fiscal periods, close, reopen, and audit controls

- **Business outcome and source:** controlled period integrity, transparent close readiness, immutable close/reopen evidence, and auditable adjustments. Fiscal Year, Accounting Period, Period Closing Voucher, GL, closing checklists, and audit logs are sources after proof.
- **Required semantics:** soft/hard close, document types restricted, effective posting date, late adjustments, retained earnings/P&L transfer, provisional/final/certified versions, reopen reason, subsequent events, comparative restatement, and cut-off.
- **Role/company/context:** preparer, Controller approver, poster, reopen approver, auditor, and break-glass roles separated; company/fiscal period/book/dimension scope explicit.
- **Read/execution boundary:** close-readiness posture can be read-only; close voucher, period restriction, reopen, adjustment, and certification are Tier 3 execution.
- **Dependencies and impact:** GL-01, reconciliation framework, tax/AR/AP/bank/inventory/asset controls, ACT-01. It affects all posting workspaces and therefore requires cross-workspace lifecycle analysis.
- **Risks:** unauthorized close/reopen, backdating, hidden late postings, incomplete subledgers, false certification, and mutable audit evidence.
- **Assurance and closure:** checklist invariants, all-subledger reconciliations, posting-denial matrices, maker-checker, immutable audit, recovery/reopen drills, independent accounting/security/release review, authenticated controlled-live evidence.
- **Explicitly deferred:** close readiness runtime, restrictions, PCV, reopen, adjustment posting, certification, and audit sign-off.

### REP-01 — Financial statements and management reporting

- **Business outcome and source:** labeled, reconcilable Balance Sheet, Profit and Loss, Cash Flow, KPI, variance, and management views. GL/TB, close version, account hierarchy, Finance Book, dimensions, budgets, and consolidation outputs are authoritative inputs.
- **Required semantics:** statement mapping, opening/comparatives, retained earnings, cash-flow method, period and version, draft/final/certified wording, base/presentation currency, rounding, eliminations, dimensions, and drill lineage.
- **Role/company/context:** Executive/Controller/Auditor purposes remain distinct; company/consolidation/period/book/dimension authority and sparse-slice privacy apply.
- **Read/execution boundary:** reports are read-only; certification, publication, export/distribution, adjustment, and narrative approval are separate.
- **Dependencies and impact:** GL-01 before statutory statements; PER-01 for closed/certified labels; ENT-01 for consolidation; MGT-01 for budget/variance. No native report passthrough or AI-authored accounting truth.
- **Risks:** revealing company health or payroll/small dimensions, wrong version/currency, inconsistent statements, export leakage, and misleading management labels.
- **Assurance and closure:** TB/statement tie-out, rollups, retained earnings and cash-flow reconciliation, period/version labels, permission/suppression/export tests, accounting review, authenticated live comparative evidence.
- **Explicitly deferred:** statements, KPIs, variances, drilldowns, exports, certification, publication, and AI narratives.

### ENT-01 — Multi-company, intercompany, consolidation, currency, and Finance Book

- **Business outcome and source:** authorized entity and group reporting with correct intercompany, elimination, exchange, and book treatment. ERPNext Company, intercompany documents/journals, GL, Exchange Rate Revaluation, Finance Book, account mappings, and approved consolidation logic are sources after proof.
- **Required semantics:** legal entity versus group; counterparty matching; due-to/due-from; transfer pricing/tax; elimination entity; ownership and minority interest if applicable; functional/transaction/presentation currency; rates; realized/unrealized FX; translation reserves; book adjustments.
- **Role/company/context:** explicit authority for every included entity plus separate group/consolidation authority; partial group access fails closed. Elimination and intercompany mappings are restricted masters.
- **Read/execution boundary:** read-only entity and consolidation posture first; intercompany creation, matching, elimination, revaluation, and consolidation journals are execution.
- **Dependencies and impact:** Owner entity/currency facts, FND foundations, GL/TB, tax, close, and ACT. Every source workspace retains its own lifecycle/role authority.
- **Risks:** unauthorized group union, cross-company leakage, unmatched pairs, wrong rates, double counting, unbalanced eliminations, and cache collisions.
- **Assurance and closure:** authorized-set denial tests, pair matching, elimination balance, rate/date/rounding fixtures, Finance Book isolation, partial-company failures, specialist review, group live tie-out.
- **Explicitly deferred:** multi-company UI, intercompany workflows, consolidation, eliminations, FX revaluation, group statements, and book postings.

### MGT-01 — Budgeting, forecasting, cost centers, projects, and dimensions

- **Business outcome and source:** controlled plan-versus-actual management, accountable cost ownership, and dimensional analysis. Budget, GL actuals, Cost Center, Project, Accounting Dimensions, approved forecast versions, and workflow/audit records are sources after proof.
- **Required semantics:** budget period/version/scenario; original/revised/committed/actual; encumbrance if applicable; hierarchy rollups; allocation; dimension intersection; forecast assumptions; currency; sparse slices; locked versions.
- **Role/company/context:** budget owner, reviewer, approver, Controller, and viewer scopes; company and dimension intersection, not union; sensitive/payroll account restrictions.
- **Read/execution boundary:** read-only variance after authoritative actuals; create/revise/approve/lock budgets and forecasts are controlled actions.
- **Dependencies and impact:** FND, GL-01, statements/version policy; Sales/Procurement may provide operational drivers but not accounting actuals. Shared UI may render filters only under exact dimension contracts.
- **Risks:** strategic data leakage, small-team payroll inference, unauthorized forecast changes, mixed versions, and dimension rollup errors.
- **Assurance and closure:** version immutability, hierarchy and dimension-permission tests, actuals tie-out, sparse suppression, workflow/SoD/idempotency tests, management/accounting review, authenticated owner/live evidence.
- **Explicitly deferred:** budgets, forecasts, commitments, variances, dimension drilldowns, approvals, and imports/exports.

### INV-01 — Inventory valuation, COGS, GRNI, WIP, landed and manufacturing accounting

- **Business outcome and source:** reconciled stock value, COGS, stock-received-not-billed, WIP, landed costs, and manufacturing variances. Stock Ledger Entry, valuation layers/bins where authoritative, Stock Entry/Delivery/Purchase Receipt lifecycle, GL Entry, Landed Cost Voucher, and manufacturing documents are candidate sources.
- **Required semantics:** perpetual inventory, valuation method, posting time, backdated/reposted transactions, negative stock, returns, transfers, damaged/consigned stock, GRNI, landed cost allocation, WIP, scrap, variance, warehouse/company/currency/dimensions.
- **Role/company/context:** Finance/Inventory/Manufacturing purposes separated; company, warehouse, item group, account, period and dimension authority. Warehouse custom-workflow roles do not grant accounting access.
- **Read/execution boundary:** reconciliation/read posture first; valuation repost, stock reconciliation, landed-cost allocation, manufacturing close, and GL correction are execution.
- **Dependencies and impact:** FND/GL, ERP stock lifecycle proof, Warehouse protection. The accepted Warehouse custom workflow is not valuation or GL truth.
- **Risks:** material misstatement from backdating/reposting, negative stock, mixed warehouses, incomplete GRNI/WIP, and accidental mutation of Warehouse behavior.
- **Assurance and closure:** SLE-to-GL and stock-value reconciliation, returns/transfers/backdate/negative/repost fixtures, cut-off tests, protected Warehouse regression, specialist review, authenticated live tie-out.
- **Explicitly deferred:** stock accounting dashboards, COGS/GRNI/WIP, valuation corrections/reposts, manufacturing accounting, and stock execution.

### AST-01 — Fixed assets, depreciation, deferred accounting, and opening balances

- **Business outcome and source:** controlled asset register, depreciation/books, deferrals/amortization, and opening-balance integrity. Asset/Asset Category, depreciation schedules, purchase/capitalization/disposal records, GL, Deferred Accounting records, opening entries, and Finance Book are sources after proof.
- **Required semantics:** capitalization date/cost, useful life/method/residual, book/tax depreciation, impairment, transfer, disposal/gain/loss, deferred periods, amendments, opening conversion date, currency, period and dimensions.
- **Role/company/context:** asset custodian, accountant, Controller and auditor scopes; company/book/location/dimension authority; asset identity may be sensitive.
- **Read/execution boundary:** register and schedule posture first; capitalization, depreciation posting, impairment, disposal, schedule change, deferral, and opening import are execution.
- **Dependencies and impact:** FND/GL/close/tax and Procurement lifecycle. Shared UI impact none unless separately justified.
- **Risks:** duplicate/missing assets, unauthorized schedule change, wrong period/book, unreconciled asset GL, and migration imbalance.
- **Assurance and closure:** register-to-GL, depreciation roll-forward, disposal/impairment/book fixtures, opening-balance equation and migration reconciliation, SoD/audit tests, specialist/live evidence.
- **Explicitly deferred:** all asset, deferral, opening-balance, migration, and execution capabilities.

### CAP-01 — Debt, interest, investments, equity, dividends, and leases

- **Business outcome and source:** complete financing and capital posture where applicable. Loan/lease/investment/equity agreements, schedules, GL, bank, interest accruals, approvals, and legal records are authoritative only after Owner applicability and installed-source proof.
- **Required semantics:** principal, interest/effective rate, fees, accrual, maturity, covenant, current/non-current split, fair value/impairment, lease liability/right-of-use, dividend declaration/payment, currency and period.
- **Role/company/context:** Treasury, Controller, Board/Owner, and auditor authorities separated; entity, instrument, account, currency, period and confidentiality scope.
- **Read/execution boundary:** read-only posture after proof; drawdown, repayment, investment trade, valuation, dividend, lease journal, and bank effect are execution.
- **Dependencies and impact:** FND/GL/bank/close/statements/tax/ACT; no incidental route or AI authority.
- **Risks:** highly confidential terms, valuation/model error, unauthorized cash movement, covenant misstatement, and wrong classification.
- **Assurance and closure:** contract-to-schedule-to-GL/bank reconciliation, rate/accrual/maturity fixtures, SoD and approval evidence, specialist review, authenticated restricted live proof.
- **Explicitly deferred:** entire domain pending Owner applicability and separate design.

### PEO-01 — Expense claims, payroll, employee liabilities, and privacy

- **Business outcome and source:** controlled employee-related costs, liabilities, reimbursements, payroll postings, and reconciliations. Expense Claim, Payroll Entry/Salary Slip where installed, employee advances, payment/GL records, and HR authority are sources after proof.
- **Required semantics:** earned/incurred/paid dates, approvals, advances/settlement, payroll period, deductions/taxes/benefits, accruals, reversals, cost allocation, currency and dimensions.
- **Role/company/context:** HR/payroll, manager, Accounts, Treasury, Controller and auditor scopes separated; strict employee and compensation privacy; company/dimension/purpose limits.
- **Read/execution boundary:** aggregate accounting posture only after privacy proof; employee rows, salary detail, approvals, payroll processing, reimbursement and payment are execution/restricted operations.
- **Dependencies and impact:** FND/GL/bank/tax/ACT and HR ownership. GL/TB views need payroll account blacklists or separate payroll authority.
- **Risks:** employee identity/compensation leakage, small-dimension inference, cross-role exposure, wrong tax/liability, and unauthorized payment.
- **Assurance and closure:** privacy impact assessment, aggregation thresholds, source/GL/payroll reconciliation, role/field denial, SoD, specialist review, restricted authenticated live evidence.
- **Explicitly deferred:** employee/payroll data, aggregates, workflows, exports, payments, and AI access.

### XWS-01 — Cross-workspace accounting integration

- **Business outcome and source:** each operational workspace owns its document lifecycle while Finance receives bounded accounting facts from ERPNext accounting sources and reconciles them to ledger truth.
- **Required semantics:** document state transitions, posting/cancellation/return/amendment, tax, allocations, stock valuation, period cut-off, company/currency/master identity, and eventual-consistency/reconciliation boundaries.
- **Role/company/context:** source-workspace role never grants Finance authority; Finance role never grants operational mutation. Context and source permissions are re-resolved server-side.
- **Read/execution boundary:** read integration is one-way/bounded until a separately approved command contract. No Finance implementation changes Sales, Procurement, Warehouse, Shared UI, routing, or source documents incidentally.
- **Dependencies and impact:** integration contracts in section 8; ownership locks and all triggered protected gates apply.
- **Risks:** role inheritance, circular ownership, UI payload used as accounting truth, duplicate events, partial lifecycle state, shared-runtime blast radius, and source/live drift.
- **Assurance and closure:** lifecycle/reconciliation fixtures, role/company denial, request isolation, cross-workspace tests, formal Sales/Procurement and applicable Warehouse/Finance evidence, exact allowlists, authenticated live acceptance.
- **Explicitly deferred:** event bus, write-back, shared accounting runtime, and operational workflow changes.

### ACT-01 — Notifications, approvals, controlled actions, and accounting execution

- **Business outcome and source:** governed work queues and eventually safe human-approved accounting actions. Authoritative ERPNext workflows/documents plus an approved command envelope and immutable audit evidence are required.
- **Required semantics:** notification versus task; prepare/review/approve/post/release/reconcile/close; action preconditions; idempotency; effective date; atomicity; retry; compensating action; reconciliation; expiry and revocation.
- **Role/company/context:** maker-checker and prohibited combinations, action-time reauthorization, exact company/period/source/amount/currency/dimension, break-glass and audit controls.
- **Read/execution boundary:** informational notifications may be separately designed; approvals do not execute. Every mutation, posting, payment, filing, close, email, notification send, export, or workflow transition needs its own authority.
- **Dependencies and impact:** dependent read posture, FND/FND-02, SoD, operational support/recovery, workspace ownership and separate live approvals.
- **Risks:** confused deputy, replay/double posting, stale approval, partial effects, unauthorized communication/payment, irreversible close, and absent recovery.
- **Assurance and closure:** threat model, command contract, action-time denial, maker-checker, idempotency/replay/concurrency, atomicity/recovery, immutable audit, reconciliation, security/accounting/release review, controlled authenticated live acceptance.
- **Explicitly deferred:** all notifications, approvals, communications, exports, mutations, postings, payments, reconciliations, filing, close/reopen, and autonomous effects.

### AI-01 — AI advisory access and prohibited AI authority

- **Business outcome and source:** optional explanations or summaries of an already-authorized Finance response, with traceability to authoritative ERP evidence. AI output is never accounting truth.
- **Required semantics:** same company, role, period, currency, dimension, source, field allowlist, suppression, freshness, and stale-state rules as the underlying approved Finance response; citations must identify authoritative evidence and uncertainty.
- **Role/company/context:** AI receives no independent Finance role, no cross-company union, and no broader row/field access. It is never requester, approver, poster, payer, reconciler, close controller, tax filer, or master-data owner.
- **Read/execution boundary:** no Finance-to-AI connection is currently approved. Future summarization is read-only and human-inspected. AI may not select company, account, tax treatment, posting date, payment, reconciliation, approval, close, or any action.
- **Dependencies and impact:** separate Owner-approved security architecture; permission-preserving Finance adapter; prompt/tool target validation; session isolation; retention/redaction/deletion policy; AI runtime remains separately owned.
- **Concrete stop-gate finding:** committed `HEAD` evidence is `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py:433-486,729-753`, which uses raw SQL/`frappe.get_all` for Finance-related aggregates and recent invoice/contact detail without an explicit Finance role/company/field contract in that path; `qwen_chat/compiler.py:143-147,445-448`, which derives a sole company using `frappe.get_all("Company")`; and `impl_factory/03_config/qwen_enterprise_metadata/report_registry.json:253,355,457,559,661,756,851`, whose committed registry advertises AP, AR, P&L, Balance Sheet, and Cash Flow families through the loader at `qwen_chat/metadata.py:45-46,94`. These paths are outside Cycle 1 and are not endorsed for Finance reuse.
- **Risks:** permission bypass, company-scope error, customer/supplier/invoice/contact/bank/tax/payroll identity leakage, prompt injection, cross-session data, unsupported accounting claims, and AI-initiated action.
- **Assurance and closure:** audit raw SQL/`get_all` and registry paths against committed source; replace or contain them behind permission-preserving exact contracts; role/company/row/field denial; identity-recursion and cross-session tests; prompt/tool denial; retention/redaction; authoritative citations; independent security/accounting review; authenticated live evidence.
- **Explicitly deferred:** all Finance-to-AI data access, reports, summaries, recommendations, tools, actions, and accounting authority. The High integration risk is accepted as a future implementation stop gate, not remediated by this document.

## 8. Integration contracts

These contracts identify ownership and failure boundaries. They are not implementation approvals.

### 8.1 Sales → AR → tax → GL → cash

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Sales owns accepted sales-workspace interaction and governed operational document behavior. ERPNext Sales Invoice and its lifecycle own the receivable-origin document; tax sources own transaction tax; Payment Ledger owns allocation/outstanding subledger facts after proof; GL Entry owns posting truth; bank statement/Bank Transaction and bank GL own cash reconciliation truth. |
| Read boundary | Finance reads only permission-preserving, company-scoped, lifecycle-proven fields through an accounting-source adapter. Sales UI payloads, browser registry data, and native route visibility are not accounting sources. |
| Write boundary | No Finance write is approved. Future credit control, allocation, write-off, payment, tax adjustment, journal, or communication requires a separate command contract and source-workspace impact review. |
| Lifecycle dependency | Quotation/Order/Delivery are operational context; submitted Sales Invoice establishes receivable/tax/posting facts subject to cancellation, return/credit note, amendment, schedule, allocation, write-off, future activity, and period state. Cash is recognized only through authorized voucher/bank/GL lifecycle, not invoice status alone. |
| Failure/reconciliation boundary | Invoice ↔ Payment Schedule ↔ Payment Ledger; Payment Ledger ↔ AR control GL; invoice tax ↔ tax GL ↔ statutory posture; settled vouchers ↔ bank GL ↔ statement. Any mismatch fails the affected result closed and enters a separately governed exception posture. |
| Protection gates | Finance exact-schema/role/company gates; formal Sales protected gate for any triggered Sales/shared change; Shared UI gate if triggered; security/accounting review; authenticated live evidence for each approved role pair. |

### 8.2 Procurement → AP → tax → GL → payment preparation

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Procurement owns accepted PR/RFQ/SQ/PO workspace behavior. ERPNext Purchase Invoice lifecycle owns the liability-origin document; Payment Schedule and Supplier Payment Ledger own installment/allocation facts after proof; tax sources and GL own accounting truth. Treasury/payment runtime, not Procurement or AI, owns any later payment preparation/release contract. |
| Read boundary | Finance may read permission-preserving, exact company/date/currency/status fields after schedule, advance, hold, return, allocation, and future-activity proof. Procurement UI state is never AP accounting truth. |
| Write boundary | No bill, receive, payment, supplier communication, allocation, journal, or bank effect is approved. Payment preparation must be a non-executing artifact distinct from approval, release, and bank transmission. |
| Lifecycle dependency | PR/RFQ/SQ/PO do not create AP. Purchase Receipt may affect GRNI/stock accounting. Submitted PI creates liability/tax/posting facts subject to schedules, holds, returns/debit notes, advances, amendments/cancellation, payment allocation, and period state. |
| Failure/reconciliation boundary | PI ↔ Payment Schedule ↔ Supplier PLE; PLE ↔ AP control GL; PI tax ↔ tax GL; Purchase Receipt ↔ GRNI/PI where applicable; approved payment instruction ↔ payment voucher ↔ bank/GL. Unsupported semantics fail closed. |
| Protection gates | Finance gates; formal Procurement protected gate for triggered Procurement/shared change; Treasury SoD and idempotency before any preparation/action; Shared UI/security/accounting/live gates as applicable. |

### 8.3 Warehouse → stock valuation → COGS/GRNI/WIP → GL

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Warehouse owns accepted custom workflow behavior. ERPNext stock documents and Stock Ledger Entry/valuation logic own inventory movement/value; GL Entry owns financial posting; manufacturing/landed-cost sources own their specialized allocations after proof. |
| Read boundary | Finance consumes installed, permission-preserving stock/accounting sources, not custom Warehouse queue/status payloads. Company, warehouse, item/account, posting date/time, valuation method, currency, Finance Book, and dimensions are explicit. |
| Write boundary | No stock reconciliation, valuation repost, backdated stock change, landed-cost allocation, manufacturing close, or GL correction is approved. |
| Lifecycle dependency | Receipt/delivery/transfer/return/manufacture/scrap affect SLE and, under perpetual inventory, corresponding GL states; backdating/reposting can change later valuation and COGS. GRNI and PI lifecycle reconcile separately. |
| Failure/reconciliation boundary | Stock document ↔ SLE/valuation layer ↔ inventory/COGS/GRNI/WIP GL; returns/transfers/backdated reposts must preserve lineage. A custom workflow completion does not prove ERP stock or accounting completion. |
| Protection gates | Warehouse regression/protection evidence for impacted surfaces; Finance/GL source proof; formal Sales/Procurement gates when shared or their documents are affected; exact live allowlist and specialist accounting evidence. |

### 8.4 Company, currency, fiscal year, chart of accounts, dimensions, and master data

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | ERPNext controlled masters under named business stewards; Main Control owns integration contract, not master values. |
| Read boundary | All domains consume canonical IDs through server-resolved authority. Labels/defaults/cached browser state cannot substitute for ID and permission proof. |
| Write boundary | Master creation/change/disable/merge, chart changes, rate changes, period restrictions, dimension configuration, and intercompany mappings are separate audited actions. |
| Lifecycle dependency | Effective dates, dependent documents, open periods, disabled/renamed records, hierarchy changes, and currency-rate timing must be modeled. |
| Failure/reconciliation boundary | Missing, ambiguous, disabled, unauthorized, malformed, over-cap, stale, or cross-company context fails closed before financial reads. Master changes require downstream impact and reconciliation. |
| Protection gates | Master steward/Owner approval, permission and metadata gates, migration/recovery plan, cross-workspace impact, exact source/live proof. |

### 8.5 Finance workspace, Shared UI, routing, registries, governance, and landing

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Finance adapter owns financial semantics, role/company resolver, schema, and page behavior. Shared Core owns lifecycle and neutral presentation contracts. Boot owns landing selection. Registries and governance own exact registered identities, targets, and permitted actions. |
| Read boundary | Shared UI receives only an already-authorized exact public schema and workspace key. Cached data is keyed and invalidated by workspace, route, generation, role/company authority, and request lifecycle. |
| Write boundary | Shared UI, boot, registry, and governance work may not add financial reads or actions. Finance changes may not edit shared/runtime surfaces without a separate impact decision. |
| Lifecycle dependency | Entry, refresh, supersession, timeout/error, route departure, wrapper hide, logout/user switch, authority loss, and return must clear or invalidate stale Finance data. |
| Failure/reconciliation boundary | Page metadata, boot roles/precedence, backend policy, browser registry, governance manifest, route allowlist, visible copy, and tests must agree; mismatch fails closed. |
| Protection gates | Exact file ownership locks, impact analysis, formal Sales/Procurement and applicable Warehouse/Finance regressions, responsive/accessibility evidence, independent review, separate live approval. |

### 8.6 AI Assistant access without accounting authority

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Finance remains source/authorization owner; AI Assistant owns only model/session presentation under its own security contract. AI output is non-authoritative. |
| Read boundary | No connection today. A future adapter may provide only the exact already-authorized Finance response, never raw broader sources, unrestricted SQL/`get_all`, native report passthrough, or inferred company access. |
| Write boundary | None. AI cannot create, submit, cancel, amend, post, pay, reconcile, file, close, reopen, approve, notify, email, export, or select controlling accounting parameters. |
| Lifecycle dependency | Re-resolve user, role, company, period, fields, suppression, and source freshness for each request/tool call; isolate sessions; invalidate on context/authority change. |
| Failure/reconciliation boundary | Unsupported question, missing authoritative evidence, permission ambiguity, stale context, prompt injection, identity risk, or source mismatch produces a bounded refusal/unavailable result, never a guessed financial answer. |
| Protection gates | Mandatory AI stop gate from section 7; separate Owner approval; committed-path audit/remediation; prompt/tool, role/company/field/row, session/retention, identity and no-action tests; security/accounting review; authenticated evidence. |

### 8.7 Source-to-live alignment and protected regression control

| Contract element | Canonical rule |
| --- | --- |
| Source-of-truth ownership | Source branch and approved revision are authoritative. Main Control records intentional live drift and decides candidate scope; Owner separately approves live alignment. |
| Read boundary | Read-only parity checks use exact paths/hashes and do not inspect operational accounting data unless a separately authorized acceptance plan requires it. |
| Write boundary | Live copy, metadata reload, migration, permission change, restart, cache clear, and protected gate are distinct approvals. One does not authorize another. |
| Lifecycle dependency | Source acceptance → optional staging decision → commit → push → exact live-alignment decision → required operational action → authenticated acceptance → closure. Each state is independently recorded. |
| Failure/reconciliation boundary | Unclassified diff, wrong revision, exclusion drift, unexpected live drift, failed gate, role mismatch, or incomplete evidence stops the affected transition. Source tests/smoke never substitute for authenticated live acceptance. |
| Protection gates | Exact allowlist/hashes, ownership locks, trigger matrix, formal Sales/Procurement and applicable Warehouse/Finance evidence, independent release review, rollback/recovery, and final go/no-go. |

## 9. Dependency model and implementation waves

The dependency model is:

```text
Owner business facts + governance/masters/permission policy
                         |
                         v
Canonical financial context + accounting-source adapter contract
                         |
                         v
Consistency, posting lineage, reconciliation, privacy, and evidence controls
          +--------------+-------------------+
          |              |                   |
          v              v                   v
 GL/TB source proof   Installment proof   Masked bank-status proof
          |              |                   |
          v              v                   +--> bank recon posture
 Statements/close    AR/AP expansion          |
          |              |                    +-- GL/TB --> monetary liquidity
          v              v
 Management/group    AP amount --> payment preparation
 reporting           (no execution)

All controlled actions wait for: proven read posture + SoD + command envelope +
idempotency/recovery + reconciliation + separate Owner and live approvals.
```

### Wave 0 — Owner facts and architecture acceptance

- Confirm the unknown business facts in section 3.3.
- Accept or revise the foundations, taxonomy, source ownership, role/SoD model, and integration contracts.
- Confirm the evaluation weights and choose whether the next outcome should optimize ledger leverage, receivable/payable availability, or Treasury status visibility.
- This wave does not start Finance Cycle 2.

### Wave A — Mandatory architecture foundations

- Canonical financial-context contract.
- Master-data ownership matrix.
- Permission/data-classification and segregation-of-duties matrix.
- Accounting-source adapter and consistency modes.
- Posting-lineage/reconciliation catalogue and exception ownership.
- Exact response/identity-suppression standards.
- Evidence, ownership-lock, source/live, and action-control templates.

These definitions may be approved as one architecture package because they share authority and no runtime effect. Installed-source proof remains candidate-specific.

### Wave B — Bounded source proofs, safely parallel at research level

After Wave A is accepted, separate read-only specialists may investigate in parallel:

- GL/Trial Balance source and integrity semantics;
- Payment Schedule/installment lifecycle and parent-permission semantics;
- masked, non-monetary bank-reconciliation status semantics;
- tax/localization applicability, inventory/COGS lineage, and other Owner-prioritized unknowns.

Each proof must use its own exact source list and stop without runtime implementation. Research may be parallel; synthesis and scope approval remain centralized.

### Wave C — First Owner-selected bounded read-only outcome

Only after a separate Owner decision may one approved outcome enter an implementation cycle. It must have a Level 2/3 scope contract, exact files, role/company/data schema, accounting fixtures, protection triggers, independent counterpart review, and separate external-state gates.

The current Finance service and page are large shared Finance ownership surfaces. Runtime changes there are sequential unless Main Control first creates proven non-overlapping adapters with explicit interfaces. Parallel writers must not edit the same Finance service/page, registry, manifest, boot, Shared UI, or smoke surface.

### Wave D — Dependent reporting and integration outcomes

- GL/TB before statements, certified close posture, management reporting, monetary liquidity, consolidation, and most accounting reconciliations.
- Installment proof before installment-aware AR/AP and AP amount posture.
- Proven subledgers before payment preparation or write-off posture.
- Stock/accounting lineage before COGS/GRNI/WIP claims.
- Jurisdiction proof plus GL reconciliation before statutory posture.
- Entity/currency authority before intercompany, consolidation, or presentation-currency results.

### Wave E — Controlled actions and execution

Notifications, approvals, payment preparation, posting, reconciliation, tax filing, closing/reopening, master changes, exports, and AI tools remain separate Tier 3 outcomes. They are sequential after the relevant read posture and require SoD, action-time authorization, idempotency, immutable audit, recovery, reconciliation, protected regression, and explicit live approval.

## 10. Parallel and sequential boundaries

### Safe to proceed in parallel after foundation acceptance

- read-only official/installed-source research in non-overlapping domains;
- business-fact collection by distinct Owner delegates;
- independent accounting, security, integration, and release reviews;
- fixture design and threat modeling that do not edit shared runtime;
- domain-specific architecture briefs with one Main Control synthesis.

### Must remain sequential

- foundation acceptance before any candidate implementation;
- Owner selection before declaring or starting Finance Cycle 2;
- installment semantics before installment-aware AR/AP or AP amounts;
- GL/TB integrity before statements, close certification, monetary liquidity, and consolidation;
- read posture before any action in the same domain;
- preparer/approver/poster/releaser/reconciler authority before controlled execution;
- implementation → source acceptance → staging → commit → push → live alignment → operational action → authenticated acceptance, each under its own approval;
- any edits to the same ownership-locked runtime surface.

### Ownership locks likely to overlap

| Lock | Surfaces | Rule |
| --- | --- | --- |
| Finance backend | `erp_workspace_ui/finance_accounting/service.py` and future Finance adapters | One writer; source contracts and public schemas frozen before edit |
| Finance browser/page | `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` and page metadata | One writer; role/schema/lifecycle evidence synchronized |
| Finance assurance | Finance unit tests, shell tests, source/lifecycle/responsive smokes | Coordinated with implementation owner; no smoke reuse as live acceptance |
| Registry/governance | `workspace_registry.py`, browser registry, `workspace_governance_manifest.py` | Main Control lock; exact parity and no opportunistic status cleanup |
| Routing/app boot | `boot.py`, hooks/app boot surfaces | Main Control/shared-runtime lock; landing precedence preserved |
| Shared runtime | sidebar, child-page helpers, common CSS/lifecycle/runtime contracts | Shared UI owner plus formal protection trigger review |
| Protected workspaces | Sales, Procurement, Warehouse services/pages/tests/smokes | Workspace owner; Finance does not edit incidentally |
| AI Assistant | committed Finance-related AI access/compiler/report-registry paths | Separate AI/security owner; excluded dirty files remain untouched |
| Canonical docs | this document and README index | Main Control writer; changes require roadmap-drift review |

## 11. Decision criteria and ranked recommendations

Scoring is a recommendation aid, not approval. Each criterion is scored 1–5. For risk/impact/cost criteria, 5 means safer, more contained, cheaper to evidence, or more reversible.

| Criterion | Weight |
| --- | ---: |
| Business value | 20% |
| Accounting/control risk reduction | 20% |
| Dependency unlock | 15% |
| Current data/source readiness | 10% |
| Permission/leakage safety | 10% |
| Integration containment | 10% |
| Evidence-cost efficiency | 5% |
| Reversibility | 10% |

| Rank | Candidate outcome for Owner consideration | Value | Control | Unlock | Data | Safety | Containment | Evidence | Reversible | Weighted result |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | GL / Trial Balance integrity and source-proof posture | 5 | 5 | 5 | 3 | 3 | 3 | 2 | 4 | **83/100** |
| 2 | Payment Schedule/installment semantic proof for AR/AP | 4 | 5 | 4 | 4 | 3 | 4 | 2 | 5 | **82/100** |
| 3 | Masked non-monetary bank reconciliation-status proof | 4 | 4 | 3 | 3 | 2 | 3 | 2 | 5 | **69/100** |

The one-point gap between the first two candidates is not a mandate. Owner strategy should decide it. AP Payment Schedule work is not automatically first.

### Recommendation 1 — GL / Trial Balance integrity and source-proof posture

- **Outcome:** prove the installed GL/TB sources, opening/movement/closing semantics, Finance Book/dimension behavior, sensitive-account restrictions, and reconciliation invariants; define a bounded read-only posture but do not implement it without later approval.
- **Why ranked first:** highest enterprise dependency leverage for statements, close, monetary liquidity, tax/inventory controls, consolidation, and management reporting.
- **Risk/cost:** broad permission surface, sensitive account inference, complex evidence, and likely Finance service/page overlap.
- **Owner must decide:** whether ledger/reporting leverage is the immediate business priority and which Controller/Auditor roles and account classes may be in scope.

### Recommendation 2 — Payment Schedule/installment semantic proof

- **Outcome:** prove parent/child permission, template and template-less lifecycle, amount/date/rounding/allocation semantics, and safe aggregate policy for both receivables and payables; source proof only unless later implementation is approved.
- **Why ranked closely:** directly resolves the main known semantic blocker that forces current AP count posture unavailable and constrains installment-aware AR/AP.
- **Risk/cost:** child-row identity/amount sensitivity and allocation complexity, but narrower and highly reversible if kept as proof.
- **Owner must decide:** whether restoring reliable installment-aware working-capital visibility is more valuable than GL foundation leverage.

### Recommendation 3 — Masked non-monetary bank reconciliation-status proof

- **Outcome:** prove safe counts/status/age of reconciliation items with masked account identity and no monetary liquidity claim, import, match, voucher creation, or clearance update.
- **Why considered:** useful Treasury control visibility can be separated from GL-backed cash amounts and execution.
- **Risk/cost:** bank data is highly sensitive; committed authority model is absent; monetary liquidity remains blocked on GL/TB.
- **Owner must decide:** Treasury roles, bank-account scope, masking, statement provider, and whether status visibility is an urgent control need.

AP amount posture, monetary liquidity, statements, close, tax, consolidation, inventory accounting, and controlled actions are not shortlisted as the first outcome because they have unmet semantic or dependency prerequisites.

## 12. Protection, permission, and failure gates

Every future domain must include, as applicable:

- guest, wrong-role, non-Finance-role, `System Manager`-only, Executive-only, and review-only denials before source reads;
- multi-role precedence and prohibited role-combination tests;
- allowed/denied company, missing selection, partial group authority, disabled/malformed/over-cap records, and cross-company cache isolation;
- source DocType, field, row, account class, Finance Book, period, currency, and dimension denials;
- browser inputs unable to broaden source, company, party, account, status, date, period, currency, or dimension scope;
- exact response-key/type allowlists and recursive identity/native-route/report/export/action-key rejection;
- low-population, sparse-dimension, and sensitive-account suppression;
- malformed, duplicate, orphaned, oversized, partial, future-dated, concurrent-change, and unsupported-state fail-closed cases;
- refresh, supersession, timeout/error, route departure, wrapper hide, logout/user switch, authority loss, and stale-response behavior;
- page metadata, boot, backend, browser registry, governance, copy, and cache-key parity;
- accounting reconciliation invariants and named exception ownership;
- formal Sales and Procurement gates plus applicable Warehouse, Finance, and Shared UI evidence for triggered changes;
- authenticated live evidence for each approved role pair and denied case when a live claim is made;
- exact source/live allowlists and hashes, with no incidental cleanup.

## 13. Findings and independent review disposition

Five bounded review lenses were used: accounting semantics, security/permissions/data leakage, cross-workspace/Shared UI integration, enterprise architecture/sequencing, and release/governance containment. One synthesis pass was performed. Findings below are accepted only where tied to concrete repository or official product evidence.

### High — future Finance-to-AI integration stop gate

Committed `HEAD` evidence shows Finance-related raw SQL/`frappe.get_all` aggregate, recent-invoice, and contact-detail access at `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_detail.py:433-486,729-753`; sole-company derivation through `frappe.get_all("Company")` at `qwen_chat/compiler.py:143-147,445-448`; and advertised AP, AR, P&L, Balance Sheet, and Cash Flow report families at `impl_factory/03_config/qwen_enterprise_metadata/report_registry.json:253,355,457,559,661,756,851`, loaded by `qwen_chat/metadata.py:45-46,94`. Those paths do not apply the Finance resolver's explicit role/company/field contract in the cited access path. This does not contradict or leak through the current Finance Cycle 1 workspace because there is no approved Finance-to-AI connection. It does prohibit any reuse or integration until a separate security outcome audits/remediates those committed paths and proves exact permission, company, identity, session, retention, and no-action controls.

**Disposition:** accepted as a mandatory future implementation stop gate; contained for this Tier 0 planning outcome; underlying AI risk remains deferred and is not described as remediated.

### Medium — future segregation-of-duties model is absent

Current Finance roles implement only the bounded manager/user Cycle 1 split. Controller, Treasury, Tax, consolidation, budget owner, preparer/reviewer/poster/releaser/reconciler/close/auditor/break-glass roles and prohibited combinations do not yet have a canonical runtime model.

**Disposition:** accepted as foundation D; implementation and permission changes deferred.

### Medium — accounting context and adapter architecture are too narrow for expansion

The current service is intentionally tailored to Cycle 1. It does not provide a reusable full financial-context, consistency, reconciliation, source-version, or posting-lineage framework.

**Disposition:** accepted as foundations A–C; no runtime refactor authorized.

### Medium — current company model is not a consolidation authority model

The current one-company/MMK fail-closed contract is safe for Cycle 1 but cannot authorize multi-company or consolidated results.

**Disposition:** accepted as a current limitation; ENT-01 deferred pending Owner facts and a new authorization contract.

### Medium — runtime ownership overlap limits safe parallel implementation

Finance service/page, registries, governance, boot, Shared UI, and smokes are common collision surfaces. Parallel research is safe; parallel runtime writers are not safe without extracted, proven non-overlapping adapters.

**Disposition:** accepted; ownership locks and sequential boundaries recorded.

### Low — stale traceability labels

Some registry/browser labels and earlier README language lag the later accepted closure/handoff. The accepted handoff explicitly classifies this as traceability debt.

**Disposition:** deferred; no opportunistic registry, runtime, or historical README cleanup is included.

### Rejected shortcuts

- role-only, `System Manager`, browser, default-company, or AI-derived authorization;
- direct child-table access without parent permission/lifecycle proof;
- native report/list/form passthrough as a Finance architecture;
- Sales/Procurement/Warehouse UI payloads as accounting truth;
- Purchase Invoice `outstanding_amount` alone as authoritative AP company-currency posture;
- Payment Schedule presence as proof of installment semantics;
- one smoke fixture or source test as authenticated live acceptance;
- approval as execution, or execution without idempotency/reconciliation/recovery;
- treating accepted Cycle 1 aggregates as GL, cash, tax, close, or certified statement truth.

### Deferred reviewer items

All runtime changes, new roles/permissions, installed-source proofs, live observations, business-applicability decisions, Finance-to-AI work, and protected gates remain deferred to separately authorized outcomes.

## 14. Tier 0 evidence scorecard

Scale: 0 absent, 1 partial/bounded with explicit caveat, 2 complete for this planning outcome. `N/A` is used only where no runtime/external-state claim is made.

| Evidence category | Score | Evidence/caveat |
| --- | ---: | --- |
| Scope and exact candidate manifest | 2 | Canonical document plus README only; four exclusions preserved |
| Source/version freshness | 2 | Exact baseline/upstream/ahead-behind/index verified for the planning snapshot |
| Accounting semantics coverage | 1 | Complete roadmap taxonomy and primary evidence; installed proof remains candidate-specific |
| Authorization and data leakage | 1 | Current Cycle 1 controls proven; future role/row/field/AI contracts intentionally unresolved |
| Segregation of duties | 1 | Mandatory model defined; Owner roles/combinations not yet approved |
| Reconciliation, idempotency, recovery, audit | 1 | Mandatory frameworks and gates defined; domain implementation absent |
| Protected/Shared UI impact | 2 | Ownership/protection matrix, triggers, landing and no-broadening rules recorded |
| Release/source-live containment | 2 | Sequential approvals, exact allowlist, drift and live-evidence rules recorded |
| Documentation/static validation | 2 | Exact final two-file snapshot, references, whitespace, newline, and diff checks required and recorded at handoff |
| Deployed metadata/config verification | N/A | No metadata/config or deployment claim is made |
| Source/live parity | N/A | No live access or alignment occurred; prior F6F evidence is historical context only |
| Authenticated browser behavior | N/A | No runtime behavior changed and no new live acceptance is claimed |

Applicable average: **1.56/2.00**. No applicable category is 0. The score supports an Owner planning decision, not implementation acceptance.

## 15. Owner decisions required before selecting the first implementation outcome

The Owner must explicitly decide:

1. Accept, revise, or reject this capability taxonomy, source ownership model, and protection matrix.
2. Confirm the known/unknown business facts in section 3, including legal entities, currencies, fiscal/tax policy, bank/Treasury model, dimensions, inventory, assets, payroll, financing, retention, recovery, and integrations.
3. Approve the canonical financial-context, source-adapter, reconciliation, privacy, SoD, master-data, and execution-control foundations as mandatory.
4. Define Finance role purposes and prohibited combinations, especially Controller/Auditor, Treasury preparer/releaser/reconciler, tax preparer/filer, close/reopen, and break-glass authority.
5. Decide whether near-term value is primarily ledger/reporting leverage, installment-aware working-capital visibility, or Treasury reconciliation-status visibility.
6. Accept or change the decision-criteria weights and choose **one** candidate outcome, or request a bounded source-proof brief before choosing.
7. Set the allowed company, period, currency, Finance Book, account-class, dimension, aggregation/identity, and live-evidence scope for the chosen outcome.
8. Decide whether any row-level, export, notification, approval, or action capability is categorically out of scope for the next roadmap horizon.
9. Confirm that Finance-to-AI remains prohibited until a separate security architecture remediates and proves the committed paths identified above.
10. Authorize a later Finance Cycle 2 scope contract separately. Acceptance of this document alone does not start it.

## 16. Planning closure and future documentation allowlist

Planning decision: `capability_map_ready_for_owner_decision`.

Closure state:

- **source:** documentation candidate ready for Owner decision after exact final static validation;
- **staging:** not staged and not authorized;
- **commit:** not performed and not authorized;
- **push:** not performed and not authorized;
- **live alignment:** not performed; no current parity claim;
- **browser acceptance:** not required for this docs-only candidate and not performed;
- **metadata/permission/protected gate:** not performed and not authorized;
- **implementation closure:** not applicable; Finance Cycle 2 is not started.

Exact future documentation staging allowlist, only if separately approved:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-capability-map-integration-plan-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

No runtime, test, smoke, registry, manifest, routing, hook, metadata, AI Assistant, permission, migration, or live file belongs in this candidate. A future staging decision must verify the cached manifest is exactly one added canonical document and one modified README, then inspect the cached diff. Staging, commit, push, live alignment, metadata, permission, protected-gate, and accounting-execution approvals remain distinct.
