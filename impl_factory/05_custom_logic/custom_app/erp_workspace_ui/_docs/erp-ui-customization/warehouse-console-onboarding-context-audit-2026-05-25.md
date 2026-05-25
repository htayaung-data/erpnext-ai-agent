# Warehouse Console Onboarding Context Audit - 2026-05-25

Status: onboarding handover draft
Branch: `feature/erpnext-ui-design`
Scope: investigation and documentation only
Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`
Live tree: `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`

## 1. Source Gate Result

Task 0 passed.

- Current branch: `feature/erpnext-ui-design`.
- Source HEAD: `c1059b1f6ba2651d8342a4822a2b9df20e9fd1c1`.
- Upstream HEAD: `c1059b1f6ba2651d8342a4822a2b9df20e9fd1c1`.
- Source is synced with `origin/feature/erpnext-ui-design`.
- Working tree was clean except known allowed untracked `ui_smoke/sales_final_acceptance_audit.js`.

Recorded status:

```text
## feature/erpnext-ui-design...origin/feature/erpnext-ui-design
?? ui_smoke/sales_final_acceptance_audit.js
```

Recent source history:

```text
c1059b1 docs: close procurement final freeze
5e9fe67 docs: close procurement phase 7l4 copy polish baseline
db0c569 fix: polish procurement search copy and shared search input
d90621a fix: align procurement search labels
2395fbb fix: align procurement quick find badges
4cc11d1 fix: stabilize procurement worklist route cache
ac0f21c fix: harden procurement route stability
fa3a1f9 fix: polish procurement purchase order copy
0439044 docs: close procurement quick find baseline
2776466 fix: align procurement quick find placement
```

No unexpected dirty files were present at onboarding start.

## 2. Documents And Source Reviewed

Foundation contracts reviewed:

- `_docs/erp-ui-customization/frozen-workspace-protection-package-standard-v1.md`
- `_docs/erp-ui-customization/shared-core-workspace-adapter-contract-v2.md`
- `_docs/erp-ui-customization/native-exception-policy-v1.md`
- `_docs/erp-ui-customization/shared-component-and-implementation-golden-rule-standard-v1.md`
- `_docs/erp-ui-customization/enterprise-shared-ui-component-standard-v1.md`
- `_docs/erp-ui-customization/enterprise-shared-ui-component-implementation-contract-v1.md`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/workspace_registry.py`
- shared console, sidebar, list shell, and report shell runtime files.

Sales reference reviewed: final freeze, frozen protection package, freeze v2 gate, navigation contract, business copy contract, SERA-0, SERA-5, Sales backend adapter, Sales page controllers, and Sales-related public JS.

Procurement reference reviewed: final freeze closure, Phase 7L4, 7K, 7J2C, 7I, 7H1, 7D1, 6C1, 6C2A, 5A/5B, 5C, and 5D baselines, plus Procurement backend adapter, page controllers, and public JS.

Smoke/gate files reviewed: `ui_smoke/package.json`, `ui_smoke/run_protected_workspace_gate.sh`, `ui_smoke/run_playwright_docker.sh`, `ui_smoke/procurement_phase3_smoke.js`, `ui_smoke/procurement_phase7l_performance_smoke.js`, `ui_smoke/procurement_phase7k_quick_find_smoke.js`, and `ui_smoke/workspace_search_modal_smoke.js`.

Note: `ui_smoke/sales_freeze_protection_smoke.js` was requested for inspection, but is not present in this source tree. The actual Sales freeze entry point is `ui_smoke/run_sales_freeze_protection_gate.sh`, invoked by the `test:sales-freeze-protection` package script.

Installed ERPNext source was reviewed inside running container `erpai_project1-backend-1`, image `ghcr.io/htayaung-data/erpnext-factory:erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0`, source root `/home/frappe/frappe-bench/apps/erpnext/erpnext`.

## 3. Current Protected Workspace Status

Sales Console is frozen and protected as the v2 baseline. Any shared core, sidebar, list shell, report shell, boot, native exception, registry, governance manifest, or Sales adapter change that can affect Sales must pass the Sales freeze protection gate.

Procurement Console is accepted for protected final freeze closure as of 2026-05-25. It has owner-facing copy, Quick Find, protected productized routes, managed draft buying forms, preview/PDF output, readiness views, and protected native-escape boundaries. The registry still records Procurement status as `phase_3`, while closure docs state that Procurement should be treated as a protected frozen workspace baseline.

Warehouse Console exists only as roadmap metadata today. `workspace_registry.py` lists `warehouse`, recommended name `Warehouse Console`, wave `first`, priority `3`, status `planned`. There is no active Warehouse adapter, route family, page controller, governance manifest entry, smoke, or freeze package yet.

## 4. Core Contract Implications For Warehouse

Warehouse must begin from Core + Adapter, not by copying Sales or Procurement pages.

Core owns shell lifecycle, first paint, no-stacking cleanup, native sidebar suppression, active navigation, scoped search entry point, headers, filter layouts, date-pair behavior, worklist/list shell, report shell, row-link affordance, guarded states, and in-place Apply/Reset/Refresh behavior.

Warehouse should own only adapter payloads: workspace-specific roles, route keys, business copy, queue definitions, report keys, filters, rows, targets, permission flags, allowed actions, and guarded states.

Normal users must stay inside productized workspace routes. Raw ERPNext routes are allowed only as governed native exceptions declared in `workspace_governance_manifest.py`, permission-gated, visually governed, smoke-tested, and documented.

Every Warehouse route and visible action needs manifest classification before freeze. Stock mutation must be server-side permission checked and should not appear in first scope unless separately designed.

## 5. Sales Freeze Implications

Sales Console is the frozen premium reference and protection gate, not a page template.

Warehouse must not change Sales route names, sidebar labels, managed form behavior, Customer/Item detail behavior, Sales reports, Sales search, or Sales native exception policy. Protected Sales route families are `/desk/sales-console-home`, `/desk/sales-console`, `/desk/sales-console-worklist/...`, `/desk/sales-console-report/...`, and governed Sales document forms for Quotation, Sales Order, Delivery Note, and Sales Invoice.

Sales allows ERPNext lifecycle tools only inside declared governed native Sales document forms. Productized Sales overview, worklists, reports, Customer Detail, and Item Detail must not gain Warehouse-driven native leakage or forbidden mutations.

## 6. Procurement Freeze Implications

Procurement is the immediate upstream handoff for Warehouse.

Accepted Procurement scope includes purchase demand, sourcing, supplier/item buying context, RFQ and Supplier Quotation review, managed draft Purchase Orders, PO follow-up, preview/PDF output, Quick Find, and readiness surfaces.

Procurement explicitly does not authorize receiving, Purchase Receipt creation, stock movement, warehouse execution, billing, Purchase Invoice, payment, accounting execution, RFQ/PO active send/email, Item Price mutation, Default Supplier mutation, Item Supplier mutation, supplier/item master mutation outside allowed Procurement profile doctypes, or native ERPNext escape for normal Purchase Manager or Purchase User paths.

Warehouse should start after Procurement because Procurement reaches buyer follow-up and PO status posture, then stops before physical receiving and stock movement. Warehouse should consume Procurement PO and material demand visibility as upstream context without changing Procurement routes or action semantics.

## 7. ERPNext Warehouse Domain Findings

Installed ERPNext v16 stock source shows the warehouse domain is broad and mutation-heavy. Warehouse Console should begin with read-only visibility and exception queues before execution.

Key findings:

- `Warehouse` is a Stock master with company, parent warehouse, warehouse type, disabled flag, group flag, in-transit warehouse, and rejected warehouse flags.
- `Item` carries stock UOM, maintain-stock flag, reorder levels, alternate UOMs, batch/serial settings, quality inspection requirements, total projected qty, over-delivery/receipt allowance, and negative-stock setting. Item master mutation is not a Warehouse first-scope action.
- `Bin` is the strongest first data source for item-by-warehouse posture: actual qty, reserved qty, ordered qty, requested qty, planned qty, projected qty, stock value, reserved stock, and stock UOM.
- `Stock Ledger Entry` is stock movement truth with item, warehouse, qty change, qty after transaction, stock value, voucher type/no, batch, serial, company, and serial/batch bundle fields.
- `Stock Entry` is submittable stock mutation for material issue, receipt, transfer, manufacture, repack, subcontracting delivery/return, customer receipt, and related movements. It is high-risk and should be deferred.
- `Purchase Receipt` is submittable receiving with supplier delivery note, accepted/rejected warehouses, supplier warehouse, Purchase Order links, accepted/rejected qty, stock UOM conversion, serial/batch, quality inspection, and statuses including Draft, To Bill, Partly Billed, Completed, Return, Cancelled, and Closed.
- `Delivery Note` is submittable outbound stock movement with source/target warehouse, Sales Order links, packed qty, serial/batch, quality inspection, and billing-relevant statuses. Warehouse may need pick/dispatch visibility, but commercial Sales and invoice/payment remain outside Warehouse.
- `Material Request` supports Purchase, Material Transfer, Material Issue, Manufacture, Subcontracting, and Customer Provided purposes. Warehouse should likely own transfer/issue/receipt visibility later, not Procurement purchase sourcing.
- `Pick List` supports Material Transfer for Manufacture, Material Transfer, and Delivery, with warehouse, picked qty, reserved qty, delivered qty, serial/batch, and Draft/Open/Partly Delivered/Completed/Cancelled status.
- `Stock Reservation Entry` records item, warehouse, reserved qty, delivered qty, available qty, voucher/from-voucher context, and reservation status. It should be visibility-first.
- `Stock Reconciliation` is a submittable Stock Manager correction document and should be treated as high-risk.
- `Serial No`, `Batch`, and `Serial and Batch Bundle` support tracked-item visibility and exceptions before any assignment workflow is considered.
- `Quality Inspection` is relevant to incoming/outgoing stock touchpoints, but ownership needs owner decision.
- UOM display must preserve stock UOM truth while showing purchase/sales UOM as context. Warehouse should not mutate UOM conversion in first scope.
- Work Order/manufacturing is visible as a future integration only, not first scope.

ERPNext stock reports available for productized wrappers include Stock Balance, Stock Ledger, Available Batch Report, Available Serial No, Batch Item Expiry Status, Serial and Batch Summary, Reserved Stock, and traceability/invariant reports. Stock Balance and Stock Ledger are strongest first report candidates. Reserved Stock needs role review because installed report metadata is narrower than general stock visibility.

## 8. Warehouse Ownership Boundaries

Likely Warehouse-owned:

- warehouse and stock visibility by company, warehouse, and item
- receiving due and pending receipt visibility from submitted/open Purchase Orders and Purchase Receipts
- Purchase Receipt review posture after Procurement PO handoff
- stock movement visibility through Stock Ledger Entry and Stock Entry posture
- transfer request visibility from Material Request transfer/issue/receipt purposes
- low stock, negative stock, reorder posture, and projected quantity watch
- Bin posture and item stock by warehouse
- warehouse detail pages with recent movements, stock posture, open receiving, and open transfer/delivery context
- item stock detail pages with warehouse split, reorder posture, reservations, recent ledger movement, and serial/batch flags
- outbound pick/pack/dispatch visibility from Sales Order, Pick List, and Delivery Note where available
- batch/serial tracking visibility and exception queues
- productized Warehouse report wrappers for Stock Balance, Stock Ledger, and later batch/serial/reserved-stock reports

Likely not Warehouse-owned:

- supplier sourcing, RFQ, supplier quotation comparison, and purchase pricing
- Item Price mutation, Default Supplier mutation, Item Supplier mutation
- vendor billing, Purchase Invoice, payment, and accounting posting
- customer quotation/order commercial approval
- Sales invoice and payment collection
- accounting entries, valuation repair, and finance close actions
- HR/admin and AI intake
- normal-user native ERPNext escape

High-risk future mutations requiring separate design:

- create/submit Purchase Receipt
- create/submit Stock Entry
- create/submit Delivery Note
- create/submit Stock Reconciliation
- transfer execution
- pick/pack/ship execution
- serial/batch assignment
- quality inspection acceptance/rejection
- cancellation, amendment, close/reopen, or reposting-related stock behavior

## 9. Proposed Role Model

Warehouse Manager:

- Visibility: all Warehouse overview metrics, exception queues, open receiving, movement posture, low stock, transfer posture, pick/dispatch posture, and productized stock reports.
- Read-only pages: all Warehouse worklists, item stock detail, warehouse detail, receiving review, movement review, transfer review, delivery/pick/dispatch queue, low stock watch, batch/serial watch, Stock Ledger report, and Stock Balance report.
- Future mutation candidates: controlled Purchase Receipt, Stock Entry transfer, Pick List handling, Delivery Note execution handoff, serial/batch assignment, and reconciliation only after approved design.
- Forbidden: procurement pricing/sourcing, billing, payment, accounting entries, item supplier/default supplier mutation, Item Price mutation, raw native escape, delete, cancel/amend/submit outside designed flows.
- Native restrictions: productized by default; exceptions require manifest, permission gate, and smoke evidence.

Warehouse User / Stock User:

- Visibility: assigned or role-visible queues, receiving due, transfer/pick tasks, stock posture, and relevant exceptions.
- Read-only pages: overview, queues, item/warehouse stock detail, movement history, limited reports, and batch/serial lookup where permitted.
- Future mutation candidates: task-level scan/confirm/receive/move/pick actions only after strict design and server-side checks.
- Forbidden: Stock Reconciliation, master-data mutation, pricing, supplier mutation, billing/payment/accounting, lifecycle cancellation/amendment, and broad native route escape.

Purchase Manager read-only integration:

- Visibility: PO receiving posture, late/unreceived PO handoff, receipt status drilldowns tied to Procurement-owned POs.
- Future mutation candidates: none by default; Procurement remains buyer system for sourcing and PO draft behavior.
- Forbidden: Warehouse stock execution unless assigned Warehouse role.

Sales Manager read-only integration:

- Visibility: outbound availability, pick/dispatch posture, delivery exception visibility tied to Sales Orders where approved.
- Future mutation candidates: none by default.
- Forbidden: warehouse execution, stock reconciliation, inventory adjustment, finance/accounting, native escape.

Finance read-only integration:

- Visibility: receipt/delivery completion posture that affects billing readiness, if approved.
- Future mutation candidates: none in Warehouse; Finance owns billing/payment/accounting.
- Forbidden: stock movement execution, receiving submit, Delivery Note submit, reconciliation, warehouse master changes.

## 10. Proposed First-Pass Page Inventory

| Page | Purpose | Business user | Primary data source | Likely route | Posture | Dependencies | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse Overview | Compact daily stock workbench | Warehouse Manager/User | Bin, PO/PR posture, Material Request, Pick List, Delivery Note, SLE | `/desk/warehouse-console` | Read-only first | Procurement PO handoff, Sales fulfillment | Medium |
| Receiving Queue | PO lines and receipts needing attention | Warehouse Manager/User | Purchase Order, Purchase Receipt | `/desk/warehouse-console-worklist/receiving-queue` | Read-only first | Procurement, Finance | High |
| Receiving Review | One PO or receipt receiving posture | Warehouse, Purchase read-only | Purchase Order, Purchase Receipt, Item, Warehouse, QI | `/desk/warehouse-console-receiving-review/<name>` | Read-only first | Future PR mutation | High |
| Stock Movement Queue | Recent and pending stock movements | Warehouse Manager | Stock Entry, Stock Ledger Entry, Material Request | `/desk/warehouse-console-worklist/stock-movement-queue` | Read-only first | Stock Entry lifecycle | High |
| Stock Transfer Review | Transfer requests and transfer status | Warehouse Manager/User | Material Request, Stock Entry | `/desk/warehouse-console-transfer-review/<name>` | Read-only first | Transfer execution deferred | High |
| Delivery / Pick / Dispatch Queue | Outbound warehouse-side fulfillment | Warehouse, Sales read-only | Sales Order, Pick List, Delivery Note, SRE | `/desk/warehouse-console-worklist/delivery-dispatch-queue` | Read-only first | Sales handoff | High |
| Item Stock Detail | Item by warehouse stock posture | Warehouse, approved read-only roles | Item, Bin, SLE, Reorder, SRE, Serial/Batch | `/desk/warehouse-console-item/<item>` | Read-only | Sales/Procurement item pages protected | Medium |
| Warehouse Detail | One warehouse profile | Warehouse Manager/User | Warehouse, Bin, SLE, open queues | `/desk/warehouse-console-warehouse/<warehouse>` | Read-only | Warehouse master mutation deferred | Medium |
| Low Stock / Reorder Watch | Low projected qty and reorder posture | Warehouse, Purchase read-only | Bin, Item Reorder, Item, Material Request | `/desk/warehouse-console-worklist/low-stock-watch` | Read-only | Procurement sourcing handoff | Medium |
| Batch / Serial Watch | Tracked-item exceptions | Warehouse Manager/User | Serial No, Batch, bundles, stock reports | `/desk/warehouse-console-worklist/batch-serial-watch` | Read-only first | Quality/expiry policy | Medium/High |
| Stock Ledger Report | Movement audit report | Warehouse Manager/Stock User | ERPNext Stock Ledger | `/desk/warehouse-console-report/stock-ledger` | Read-only report | Report shell | Medium |
| Stock Balance Report | Balance by warehouse/item/date | Warehouse Manager/Stock User | ERPNext Stock Balance | `/desk/warehouse-console-report/stock-balance` | Read-only report | Report shell | Medium |
| Warehouse Reports Index | Catalog of reports | Warehouse Manager | Adapter definitions | `/desk/warehouse-console-report` | Navigation | Report shell | Low |
| Warehouse Quick Find | Search visible warehouse records after IA is stable | Warehouse Manager/User | Warehouse search backend | Later overview utility | Read-only navigation | Follow Procurement Quick Find | Medium |

## 11. Proposed Initial Roadmap Phases

Phase W0 - Warehouse design roadmap and contract intake:

- Confirm users, role matrix, boundaries, first page list, route families, page archetypes, report wrappers, and native exception posture.
- Produce design roadmap only; no runtime implementation.

Phase W1 - Registry, governance, and read-only overview skeleton:

- Add active Warehouse workspace definition only after W0 approval.
- Add route/action manifest entries for planned read-only pages.
- Build Warehouse Overview from shared console runtime with no stock mutation.
- Add minimal role guard and route guard contract tests.

Phase W2 - Read-only core queues:

- Receiving Queue, Stock Movement Queue, Low Stock Watch, Warehouse Detail, and Item Stock Detail.
- Use list shell and compact detail/object profile patterns.
- Add focused Warehouse smokes without weakening Sales or Procurement gates.

Phase W3 - Productized reports:

- Stock Balance, Stock Ledger, reports index, then batch/serial/reserved-stock reports.
- Use report shell, bounded result rows, and productized drilldowns.

Phase W4 - Outbound and transfer visibility:

- Delivery/Pick/Dispatch Queue and Stock Transfer Review.
- Read-only first, with Sales and Procurement handoff contracts explicit.

Phase W5 - Execution design only:

- Separate design packages for Purchase Receipt, Stock Entry transfer, Delivery Note/Pick List, serial/batch assignment, and reconciliation.
- No mutation should ship without owner approval, server-side permission checks, document lifecycle checks, smoke coverage, and protected workspace gates.

## 12. Premium UI/UX Expectations

Warehouse should be compact, operational, and exception-oriented.

- Avoid long vertical stacks on Overview.
- Use object-profile pages with tabs for item and warehouse details.
- Keep first viewport focused on highest-risk work queues and exceptions.
- Use shared console runtime, sidebar, scoped Search, list shell, report shell, compact detail/review shell, guarded states, and shared command strips.
- Use business-facing copy only; do not expose route keys, governance language, or implementation wording.
- Use bounded recent rows and drilldowns instead of unbounded lists.
- Prefer clear labels such as `Receiving due`, `Transfer requests`, `Low stock`, `Reserved stock`, `Batch exceptions`, and `Recent movement`.
- Avoid labels such as `Visibility only` in the UI. Describe the business state instead.
- Keep route changes stable and fast. Avoid duplicate render/reload behavior.
- Delay Quick Find until core IA is stable, then follow Procurement's preview-before-open behavior.

## 13. Explicit Non-Goals And Forbidden Actions

This onboarding task does not implement Warehouse Console.

Warehouse first scope should not implement:

- Purchase Receipt creation or submit
- Stock Entry creation or submit
- Delivery Note creation or submit
- Stock Reconciliation creation or submit
- serial/batch assignment
- pick/pack/ship execution
- quality acceptance/rejection
- purchase pricing, Item Price, Default Supplier, or Item Supplier mutation
- RFQ, Supplier Quotation, PO send/email, or supplier portal behavior
- billing, Purchase Invoice, Sales Invoice, Payment Entry, or accounting posting
- customer commercial approval or Sales order commercial mutation
- native ERPNext escape for normal users
- changes to Sales or Procurement runtime behavior
- live alignment

Forbidden action labels from the governance manifest that are especially relevant to Warehouse mutation design include Submit, Cancel, Amend, Close, Unclose, Approve, Reject, Receive, Bill, Pay, Set Default Supplier, Update Item Price, and Delete.

## 14. Risks And Open Owner Decisions

Open decisions before implementation:

- Confirm whether Procurement registry status should be updated from `phase_3` to a frozen/protected status in a separate governance task, or left as historical code naming while docs carry freeze authority.
- Confirm exact Warehouse role names and whether `Stock Manager`, `Stock User`, `Warehouse Manager`, and `Warehouse User` map to existing ERPNext roles or project-specific roles.
- Decide whether Purchase Manager and Sales Manager get Warehouse read-only integration, and on which pages.
- Decide if Quality Inspection is Warehouse-owned, Quality-owned, or shared.
- Decide whether Pick List belongs in first Warehouse visibility scope or a later outbound phase.
- Decide whether Reserved Stock report visibility is acceptable for Warehouse roles.
- Decide the first native exception policy for stock forms, if any. Recommendation: none in initial implementation.
- Decide whether Warehouse should expose Work Order/manufacturing context in first release. Recommendation: defer.
- Decide how low-stock findings hand off to Procurement without reopening Item Price, Default Supplier, or Item Supplier mutation.
- Decide whether Warehouse needs mobile/scanner UX later.

Key risks:

- Stock documents are submittable, valuation-sensitive, and often linked to accounting or billing readiness.
- Purchase Receipt sits between Procurement, Warehouse, and Finance.
- Delivery Note sits between Sales, Warehouse, and Finance.
- Stock Reconciliation can rewrite operational truth and must be heavily restricted.
- Serial/batch flows are error-prone and need purpose-built UX before mutation.
- Native ERPNext stock forms expose powerful lifecycle tools that are not safe as normal Warehouse defaults.
- Shared runtime changes for Warehouse can regress protected Sales or Procurement shells.

## 15. Smoke And Gate Implications

Current protected gate behavior:

- `ui_smoke/run_protected_workspace_gate.sh` requires Sales and Purchase role credentials.
- It runs Python compile, Python unit discovery, JS syntax checks, `git diff --check HEAD`, Sales freeze protection, Procurement split smokes, Procurement managed-form smokes, responsive filters, and Sales directory performance.
- Docker Playwright runs through `ui_smoke/run_playwright_docker.sh` with `mcr.microsoft.com/playwright:v1.59.1-noble` unless overridden.
- Artifacts are written under `ui_smoke/artifacts`, `/tmp`, or configured artifact roots.

Warehouse implementation must add focused Warehouse smokes rather than weakening existing Sales/Procurement gates. Expected future smoke categories:

- Warehouse route lifecycle and no-stacking.
- Warehouse role access and restricted direct routes.
- Warehouse Overview first paint and guarded states.
- Warehouse list shell Apply/Reset/Refresh and filter layout.
- Warehouse item/warehouse detail refresh-safe deep links.
- Warehouse report shell behavior for Stock Balance and Stock Ledger.
- Warehouse native leakage scan.
- Warehouse forbidden mutation scan.
- Cross-workspace protected gate including Sales freeze and Procurement protected stages when shared runtime is touched.

## 16. Recommended Next Phase

Recommended next step: Warehouse Console design roadmap, not implementation.

The next phase should produce an owner-reviewable Warehouse Console roadmap that locks business scope, role policy, route families, first-pass page IA, read-only data contracts, native exception posture, smoke plan, and explicit deferrals. Only after that roadmap is accepted should implementation begin.
