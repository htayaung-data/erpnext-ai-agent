# Warehouse Console Phase W2 Route/Action Inventory And Protection Plan

Date: 2026-05-26

Branch: `feature/erpnext-ui-design`

Baseline: W1 roadmap commit `01bd135ff0211c7da193c72240fb61c6d33c9ef7`

Status: docs-only route/action contract. No Warehouse runtime implementation starts in this phase.

## 1. Source Gate

Source path:

`/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`

Gate result:

- Branch confirmed as `feature/erpnext-ui-design`.
- `HEAD` confirmed as `01bd135ff0211c7da193c72240fb61c6d33c9ef7`.
- Upstream confirmed as `01bd135ff0211c7da193c72240fb61c6d33c9ef7`.
- W1 commit `01bd135ff0211c7da193c72240fb61c6d33c9ef7` is included in `HEAD`.
- Working tree was clean except known allowed untracked `ui_smoke/sales_final_acceptance_audit.js`.

This W2 phase changes documentation only. It does not add Warehouse routes, registry entries, manifest entries, runtime code, tests, smoke scripts, or live files.

## 2. Context Reviewed

Required context reviewed:

- `_docs/erp-ui-customization/warehouse-console-onboarding-context-audit-2026-05-25.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w1-industry-research-and-roadmap-2026-05-26.md`
- `_docs/erp-ui-customization/procurement-console-final-freeze-closure-2026-05-25.md`
- `_docs/erp-ui-customization/sales-console-final-freeze-2026-05-03.md`
- `_docs/erp-ui-customization/frozen-workspace-protection-package-standard-v1.md`
- `_docs/erp-ui-customization/shared-core-workspace-adapter-contract-v2.md`
- `_docs/erp-ui-customization/native-exception-policy-v1.md`
- `_docs/erp-ui-customization/shared-component-and-implementation-golden-rule-standard-v1.md`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/workspace_registry.py`
- `ui_smoke/package.json`
- `ui_smoke/run_protected_workspace_gate.sh`
- `ui_smoke/run_playwright_docker.sh`

Contract implications:

- Warehouse Console must be Core + Adapter work, not copied Sales or Procurement pages.
- Sales Console is frozen and protected.
- Procurement Console is frozen and protected, and Procurement still stops before receiving, stock movement execution, billing, payment, Item Price, Default Supplier, and Item Supplier changes.
- Normal Warehouse users must stay inside Warehouse product routes.
- Native ERPNext forms and reports are not allowed unless a future exception is explicitly approved, manifest-declared, role-gated, and smoke-tested.
- W3 may add Warehouse runtime only after this W2 plan is accepted.

## 3. Proposed Warehouse Route Inventory

Route owner for all rows: `warehouse`.

Manifest classification terms should follow the existing governance manifest vocabulary:

- Overview: `productized_overview`
- Worklist: `productized_worklist`
- Detail/review: `productized_detail`
- Report/report index: `productized_report`
- Future home launcher: `productized_overview`

No Warehouse route should be classified as `managed_create_edit` or `governed_native_exception` in W3 through W10.

| Route key | URL pattern | Page title | Business purpose | Target roles | Data sources | Default posture | Dependencies | Native escape posture | First phase | Smoke coverage | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `warehouse-console` | `/desk/warehouse-console` | Warehouse Overview | Compact daily stock workbench with stock health, inbound, outbound, internal movement, and exception posture. | Warehouse Manager, Warehouse User; cross-role read-only only if approved. | Bin, Warehouse, Item, Purchase Order/Purchase Receipt counts, Delivery Note/Pick List counts, Material Request counts, Quality Inspection counts. | Read-only. | Procurement receiving handoff, Sales fulfillment handoff, Quality holds, Finance valuation policy. | Product route only; no native forms/reports. | W3 | Overview load, role access, no native escape, no stock actions, KPI layout, duplicate shell count, warm navigation performance. | Medium |
| `warehouse-console-worklist/inbound-receiving` | `/desk/warehouse-console-worklist/inbound-receiving` | Inbound Receiving | Expected supplier receipts, late receipts, partial receipts, and receiving blockers. | Warehouse Manager, Warehouse User, Purchase Manager read-only if approved. | Purchase Order, Purchase Order Item, Purchase Receipt, Purchase Receipt Item, Item, Warehouse, Quality Inspection. | Read-only. | Procurement owns PO commercial flow; Quality may own inspection; Finance owns billing/payment. | Product route only; row links open Warehouse Receiving Review. | W4 | Worklist filters, Apply/Reset/Refresh, row links, no receive/submit/cancel/native escape. | High |
| `warehouse-console-receiving/<id>` | `/desk/warehouse-console-receiving/<id>` | Receiving Review | Review one expected receipt, Purchase Order receipt posture, or Purchase Receipt without posting stock. | Warehouse Manager, Warehouse User, Purchase Manager read-only if approved. | Purchase Order, Purchase Order Item, Purchase Receipt, Purchase Receipt Item, Item, Warehouse, Serial No, Batch, Quality Inspection. | Read-only first; future controlled receiving design only. | Procurement upstream, Quality inspection, Finance valuation and billing. | Product route only; no native Purchase Receipt or PO form link for normal users. | W4 | Summary plus tabs, bounded rows, no lifecycle controls, no native links. | Very high |
| `warehouse-console-worklist/outbound-fulfillment` | `/desk/warehouse-console-worklist/outbound-fulfillment` | Outbound Fulfillment | Pick, pack, and dispatch visibility for customer demand. | Warehouse Manager, Warehouse User, Sales Manager read-only if approved. | Sales Order, Pick List, Delivery Note, Delivery Note Item, Packing Slip, Stock Reservation Entry, Bin. | Read-only. | Sales owns commercial order flow; Finance owns billing; Quality may own outgoing inspection. | Product route only; row links open Warehouse Fulfillment Review. | W7 | Worklist filters, row links, no ship/submit/cancel/native escape. | High |
| `warehouse-console-fulfillment/<id>` | `/desk/warehouse-console-fulfillment/<id>` | Delivery / Pick Review | Review fulfillment readiness, stock availability, reservations, picking, packing, and dispatch blockers. | Warehouse Manager, Warehouse User, Sales Manager read-only if approved. | Pick List, Delivery Note, Delivery Note Item, Sales Order, Packing Slip, Stock Reservation Entry, Bin, Serial No, Batch. | Read-only first; future controlled pick/pack/dispatch design only. | Sales upstream, Finance billing downstream, Quality if outgoing inspection applies. | Product route only; no native Delivery Note, Pick List, or Sales Order form link for normal users. | W7 | Summary plus tabs, bounded rows, no lifecycle controls, no native links. | Very high |
| `warehouse-console-worklist/internal-transfers` | `/desk/warehouse-console-worklist/internal-transfers` | Internal Transfers | Transfer, issue, and receipt requests that need warehouse visibility. | Warehouse Manager, Warehouse User. | Material Request, Material Request Item, Stock Entry, Stock Entry Detail, Warehouse, Bin. | Read-only. | Procurement/Manufacturing may request materials; Finance affected after posting. | Product route only; row links open Stock Movement Review. | W6 | Worklist filters, row links, no create/submit Stock Entry, no native escape. | High |
| `warehouse-console-movement/<id>` | `/desk/warehouse-console-movement/<id>` | Stock Movement Review | Review a transfer, issue, receipt, or stock movement context without posting. | Warehouse Manager, Warehouse User, Finance read-only if approved. | Stock Entry, Stock Entry Detail, Material Request, Pick List, Stock Ledger Entry, Warehouse, Bin. | Read-only first; future controlled transfer design only. | Finance valuation, Manufacturing/Subcontracting future, Procurement transfer requests. | Product route only; no native Stock Entry or Material Request form link for normal users. | W6 | Summary plus tabs, bounded movement rows, no stock posting controls. | Very high |
| `warehouse-console-item/<item-code>` | `/desk/warehouse-console-item/<item-code>` | Item Stock Detail | One item's availability, reservations, incoming/requested posture, low stock, and recent movement. | Warehouse Manager, Warehouse User; Purchase/Sales read-only if approved. | Item, Bin, Stock Ledger Entry, Item Reorder, Serial No, Batch, Stock Reservation Entry. | Read-only. | Sales and Procurement use item context; Finance may restrict valuation; Quality tracking. | Product route only; no native Item form link for normal users. | W5 | Detail route, tabs, bounded rows, valuation visibility check, no item master actions. | Medium |
| `warehouse-console-warehouse/<warehouse>` | `/desk/warehouse-console-warehouse/<warehouse>` | Warehouse Detail | One warehouse's stock posture, inbound/outbound pressure, movements, and exceptions. | Warehouse Manager, Warehouse User. | Warehouse, Bin, Stock Ledger Entry, Purchase Receipt, Delivery Note, Material Request, Quality Inspection. | Read-only. | Finance valuation, Procurement inbound, Sales outbound, Quality holds. | Product route only; no native Warehouse form link for normal users. | W5 | Detail route, tabs, bounded rows, no master-data actions. | Medium |
| `warehouse-console-worklist/low-stock` | `/desk/warehouse-console-worklist/low-stock` | Low Stock | Low stock, negative stock, reorder posture, and projected shortage watch. | Warehouse Manager, Warehouse User; Purchase Manager read-only if approved. | Bin, Item, Item Reorder, Material Request, Purchase Order. | Read-only. | Procurement replenishment handoff; Sales availability risk. | Product route only; item links open Item Stock Detail. | W3 or W5, owner decision. | Worklist filters, shortage rows, no create Material Request or reorder edits. | Medium |
| `warehouse-console-worklist/serial-batch-watch` | `/desk/warehouse-console-worklist/serial-batch-watch` | Serial / Batch Watch | Tracked inventory exceptions, expiry risk, required tracking, and stock location posture. | Warehouse Manager, Warehouse User, Quality read-only if approved. | Serial No, Batch, Serial and Batch Bundle, Item, Stock Ledger Entry, Purchase Receipt, Delivery Note. | Read-only first. | Quality, Procurement receiving, Sales dispatch. | Product route only; no native Serial No or Batch form link for normal users. | W7 or W8 | Worklist filters, tracking rows, no assign/change serial or batch controls. | High |
| `warehouse-console-worklist/quality-hold` | `/desk/warehouse-console-worklist/quality-hold` | Quality Hold | Warehouse work blocked by inspection or rejection. | Warehouse Manager, Warehouse User, Quality read-only if approved. | Quality Inspection, Purchase Receipt, Delivery Note, Stock Entry, Item, Warehouse. | Read-only first. | Quality owns acceptance/rejection; Procurement and Sales supply source documents. | Product route only; no native Quality Inspection form link for normal users. | W4 or W7, owner decision. | Worklist filters, hold rows, no approve/reject controls. | High |
| `warehouse-console-report/stock-balance` | `/desk/warehouse-console-report/stock-balance` | Stock Balance | Current stock by item, warehouse, date, and approved quantity/value fields. | Warehouse Manager, Warehouse User; Finance read-only. | ERPNext Stock Balance report, Bin, Stock Ledger Entry. | Read-only report. | Finance valuation policy. | Product report wrapper only; no native report route for normal users. | W8 | Report filters, Apply/Reset/Refresh, no native report link, no row native leakage. | Medium |
| `warehouse-console-report/stock-ledger` | `/desk/warehouse-console-report/stock-ledger` | Stock Ledger | Movement audit by item, warehouse, voucher, date, serial/batch. | Warehouse Manager, Warehouse User; Finance read-only. | ERPNext Stock Ledger report, Stock Ledger Entry. | Read-only report. | Finance valuation and audit. | Product report wrapper only; rows open Warehouse review routes where possible. | W8 | Report filters, bounded/contained wide table, product route drilldowns only. | Medium |
| `warehouse-console-reports` | `/desk/warehouse-console-reports` | Warehouse Reports | Catalog for approved Warehouse reports. | Warehouse Manager, Warehouse User; Finance read-only for approved reports. | Warehouse report definitions and safe report metadata. | Navigation only. | Finance-sensitive reports may be role-scoped. | Product route only. | W8 | Report card navigation, disabled planned reports, no native report escape. | Low |
| `warehouse-console-home` | `/desk/warehouse-console-home` | Warehouse Home | Optional launcher route if role-based Desk routing needs a handoff route like Sales/Procurement. | Warehouse Manager, Warehouse User. | Workspace registry route only. | Navigation only. | Desk boot/role routing. | Product route only; redirect or handoff to `/desk/warehouse-console`. | W3 only if needed. | Direct route load and redirect/handoff smoke. | Low |

Route inventory decisions still needed:

- Whether `warehouse-console-home` is required in W3 for role routing consistency or can wait.
- Whether Low Stock appears in W3 or waits until W5 after Item Stock Detail exists.
- Whether Quality Hold appears with W4 inbound or waits until W7/outbound or a Quality workspace decision.

## 4. Proposed Warehouse Action Inventory

Action posture definitions:

- Allowed read-only action: does not change data and stays in the current Warehouse shell.
- Allowed navigation action: opens a Warehouse product route or report route.
- Future controlled action: possible later, but blocked until a separate execution design, server checks, audit, and owner approval exist.
- Forbidden action: not owned by Warehouse or not allowed on Warehouse product pages.

| Action | Visible label if allowed | Posture | Owner role | Server-side permission if future | First phase allowed | Audit/confirmation if future | Forbidden reason if forbidden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Open Warehouse Overview | Open Warehouse page | Allowed navigation | Warehouse Manager/User | Existing route permission. | W3 | Not applicable. | Not applicable. |
| Refresh | Refresh | Allowed read-only action | All allowed Warehouse roles | Read permission to current payload sources. | W3 | Not applicable. | Not applicable. |
| Apply Filters | Apply | Allowed read-only action | All allowed Warehouse roles | Read permission and filter allowlist. | First worklist/report phase. | Not applicable. | Not applicable. |
| Reset Filters | Reset | Allowed read-only action | All allowed Warehouse roles | Read permission and filter allowlist. | First worklist/report phase. | Not applicable. | Not applicable. |
| Open item stock detail | Open item | Allowed navigation | Warehouse roles; cross-role read-only if approved. | Read Item and stock posture through adapter wrapper. | W5 | Not applicable. | Not applicable. |
| Open warehouse detail | Open warehouse | Allowed navigation | Warehouse roles. | Read Warehouse and stock posture through adapter wrapper. | W5 | Not applicable. | Not applicable. |
| Open receiving review | Review receiving | Allowed navigation | Warehouse roles; Purchase Manager read-only if approved. | Read Purchase Order/Purchase Receipt context through adapter wrapper. | W4 | Not applicable. | Not applicable. |
| Open movement review | Review movement | Allowed navigation | Warehouse roles; Finance read-only if approved. | Read Stock Entry/Material Request/SLE context through adapter wrapper. | W6 | Not applicable. | Not applicable. |
| Open fulfillment review | Review dispatch | Allowed navigation | Warehouse roles; Sales Manager read-only if approved. | Read Pick List/Delivery Note/Sales Order context through adapter wrapper. | W7 | Not applicable. | Not applicable. |
| Open report | Open report | Allowed navigation | Role scoped. | Read report access through adapter wrapper. | W8 | Not applicable. | Not applicable. |
| Export report if existing shell supports it | Export | Allowed read-only action if approved | Warehouse Manager, Finance; Warehouse User owner decision. | Read report plus export permission; field allowlist. | W8 owner decision. | Export should be logged if sensitive valuation fields are included. | Block if it leaks valuation or native report access. |
| Create Purchase Receipt | Not visible in early phases | Future controlled action | Warehouse Manager, future receiving role. | Create Purchase Receipt, linked PO permission, item/warehouse permission, company scope. | Not before future execution phase. | Required: manager confirmation, source PO, line allowlist, serial/batch/QI checks, audit log. | Forbidden in W3-W10 because it posts receiving workflow. |
| Submit Purchase Receipt | Not visible in early phases | Future controlled action | Warehouse Manager only unless later delegated. | Submit Purchase Receipt, document status, stock permission, serial/batch/QI readiness. | Not before future execution phase. | Required: explicit confirmation, before/after stock evidence, audit log, rollback policy. | Forbidden in W3-W10 because it changes stock ledger and finance handoff. |
| Cancel Purchase Receipt | Not visible | Forbidden until separate reversal design | Warehouse Manager with Finance approval if ever allowed. | Cancel permission, stock ledger reversal checks, billing state checks. | Not allowed. | Finance approval and reversal evidence if ever considered. | Cancels stock and can affect billing/valuation. |
| Create Stock Entry | Not visible in early phases | Future controlled action | Warehouse Manager. | Create Stock Entry, purpose allowlist, warehouse scope, item permission. | Not before future execution phase. | Required: source/target validation, stock availability, audit log. | Forbidden in W3-W10 because it creates stock movement. |
| Submit Stock Entry | Not visible in early phases | Future controlled action | Warehouse Manager only unless later delegated. | Submit Stock Entry, purpose allowlist, warehouse scope, stock checks. | Not before future execution phase. | Required: explicit confirmation, ledger evidence, audit log. | Forbidden in W3-W10 because it posts stock movement. |
| Create Delivery Note | Not visible | Future controlled action | Warehouse Manager with Sales/Finance design. | Create Delivery Note, Sales Order link, warehouse scope, item permission. | Not before future execution phase. | Required: Sales handoff check, stock availability, serial/batch, audit log. | Forbidden in W3-W10 because shipment affects stock and billing. |
| Submit Delivery Note | Not visible | Future controlled action | Warehouse Manager with Sales/Finance design. | Submit Delivery Note, stock checks, delivery/billing policy. | Not before future execution phase. | Required: dispatch confirmation, ledger evidence, audit log. | Forbidden in W3-W10 because it ships stock and affects billing. |
| Create Stock Reconciliation | Not visible | Future controlled action, likely Finance co-owned | Warehouse Manager and Finance. | Create Stock Reconciliation, Stock Manager permission, valuation policy. | Not before future execution design. | Required: approval, count evidence, variance reason, finance signoff. | Forbidden early because it changes quantities and valuation. |
| Submit Stock Reconciliation | Not visible | Future controlled action, likely Finance co-owned | Warehouse Manager and Finance. | Submit Stock Reconciliation, Stock Manager permission, finance approval. | Not before future execution design. | Required: explicit confirmation, evidence, audit log, rollback policy. | Forbidden early because it posts inventory correction. |
| Reserve Stock | Not visible | Future controlled action | Warehouse Manager with Sales allocation policy. | Create/submit Stock Reservation Entry, demand link, warehouse scope. | Not before future allocation design. | Required: demand reference, stock availability, audit log. | Forbidden early because it changes availability promises. |
| Unreserve Stock | Not visible | Future controlled action | Warehouse Manager with Sales allocation policy. | Cancel/close Stock Reservation Entry. | Not before future allocation design. | Required: demand impact confirmation and audit log. | Forbidden early because it can break fulfillment promises. |
| Assign Serial No | Not visible | Future controlled action | Warehouse Manager/User if approved for task flow. | Serial No read/write, item tracking requirement, document line scope. | Not before controlled receiving/picking design. | Required: scanned/selected serial evidence and audit log. | Forbidden early because wrong assignment breaks traceability. |
| Assign Batch No | Not visible | Future controlled action | Warehouse Manager/User if approved for task flow. | Batch read/write, item tracking requirement, expiry policy, document line scope. | Not before controlled receiving/picking design. | Required: batch/expiry evidence and audit log. | Forbidden early because wrong batch breaks traceability and expiry control. |
| Approve Quality Inspection | Not visible | Forbidden in Warehouse by default | Quality role, not Warehouse default. | Quality Inspection workflow permission. | Not allowed in Warehouse early phases. | Quality approval evidence if future Quality workspace integrates. | Quality owns acceptance decisions. |
| Reject Quality Inspection | Not visible | Forbidden in Warehouse by default | Quality role, not Warehouse default. | Quality Inspection workflow permission. | Not allowed in Warehouse early phases. | Quality rejection evidence if future Quality workspace integrates. | Quality owns rejection decisions. |
| Create Material Request | Not visible | Future controlled action, owner decision | Warehouse Manager maybe; Procurement/Manufacturing handoff required. | Create Material Request with type allowlist and company/warehouse scope. | Not before future replenishment/transfer design. | Required: reason, source/target, approval policy. | Forbidden early because it creates downstream procurement or movement demand. |
| Convert Material Request | Not visible | Forbidden in Warehouse early phases | Depends on conversion target. | Conversion permission and target document permission. | Not allowed. | Separate design required. | Can create PO, RFQ, Stock Entry, or other downstream documents outside Warehouse scope. |
| Update Item master | Not visible | Forbidden | Item Manager/Admin. | Item write permission and field allowlist if ever designed elsewhere. | Not allowed. | Not applicable. | Item master changes affect Sales, Procurement, Warehouse, Finance. |
| Update Warehouse master | Not visible | Forbidden in Warehouse Console early phases | System Manager/Admin or separate inventory admin. | Warehouse write permission, company scope. | Not allowed. | Not applicable. | Master-data mutation affects all stock movement. |
| Update Item Price | Not visible | Forbidden | Procurement/Finance pricing owner. | Item Price write permission. | Not allowed. | Not applicable. | Pricing is not Warehouse-owned and is explicitly forbidden from Procurement normal flow too. |
| Update Default Supplier | Not visible | Forbidden | Procurement owner. | Item default supplier write permission. | Not allowed. | Not applicable. | Supplier sourcing and defaults are Procurement-owned. |
| Update Item Supplier | Not visible | Forbidden | Procurement owner. | Item Supplier write permission. | Not allowed. | Not applicable. | Supplier association is Procurement-owned. |
| Open native ERP form | Not visible | Forbidden for normal users | Admin exception only if approved. | Native DocType permission plus manifest exception. | Not allowed. | Admin exception evidence if ever approved. | Warehouse product routes must be primary and only normal route target. |
| Open native report | Not visible | Forbidden for normal users | Admin exception only if approved. | Report permission plus manifest exception. | Not allowed. | Admin exception evidence if ever approved. | Warehouse report wrappers must be product routes. |
| Back to Warehouse | Back to Warehouse | Allowed navigation | All allowed Warehouse roles | Existing route permission. | W3 | Not applicable. | Not applicable. |
| Back to queue | Back to queue | Allowed navigation | All allowed Warehouse roles | Existing route permission. | First detail phase. | Not applicable. | Not applicable. |
| View read-only badge | Read-only | Allowed display state | All allowed Warehouse roles | Payload state. | W3 | Not applicable. | Not applicable. |
| Show inactive future action | Action not active yet | Allowed display only when necessary | Warehouse Manager/User | Payload state; no callable endpoint. | Avoid in W3 unless owner requests. | Not applicable. | Must not look like a usable stock action. |

Action manifest expectations for W3:

- Add only read-only/navigation Warehouse actions needed by W3.
- Add Warehouse forbidden mutation guard covering all existing forbidden labels plus Warehouse-specific labels listed in section 7.
- Do not add future controlled actions as callable actions. They can be documented in notes but must not be visible as enabled controls.

## 5. Role And Access Matrix

| Role | Allowed route families | Allowed report families | Allowed read-only actions | Future action candidates | Forbidden actions | Native route posture | Sensitive fields | Valuation visibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse Manager | All Warehouse route families as phases become active. | Stock Balance, Stock Ledger, Stock Projected Qty, Stock Aging, Batch/Serial, movement history; Finance-sensitive reports subject to owner decision. | Open pages, Refresh, Apply, Reset, review rows, open item/warehouse/receiving/movement/fulfillment details, view exception queues. | Controlled receiving, transfer execution, pick/pack/dispatch, serial/batch assignment, count/reconciliation review after separate design. | Pricing, supplier sourcing, Item Price, Default Supplier, Item Supplier, invoicing, payment, accounting entries, unapproved submit/cancel/amend/post/reconcile, native escape. | Product Warehouse routes only; admin/native exception only if separately approved. | Can see operational quantities. Stock value/rate owner decision. | Proposed default: stock value visible only if owner approves; valuation rate hidden until Finance approves. |
| Warehouse User / Stock User | W3 Overview; later active worklists/details for assigned/role-visible warehouse work; item/warehouse detail if approved. | Stock Balance quantity view, Stock Ledger operational movement view, Batch/Serial watch; valuation-sensitive reports limited. | Open pages, Refresh, Apply, Reset, review rows, open operational details. | Task-level receive/pick/move/scan only after strict execution design. | Reconciliation, master-data changes, pricing, supplier/customer commercial actions, billing/payment, submit/cancel/amend unless future flow explicitly delegates. | Product Warehouse routes only. | Hide valuation rate by default; stock value owner decision, likely hidden. | Proposed default: no valuation rate; no stock value unless owner approves. |
| Purchase Manager read-only integration | Inbound Receiving, Receiving Review, Low Stock if approved, Item Stock read-only if tied to buying. | Receiving performance later, Stock Projected Qty and Stock Balance if approved. | Open inbound rows, review receiving posture, apply filters, refresh. | None in Warehouse by default. | Receiving submit, Purchase Receipt creation, stock movement, Item Price from Warehouse, supplier/default changes from Warehouse. | Product Procurement/Warehouse routes only; no native Warehouse escape. | Supplier/commercial fields remain Procurement-owned. | Proposed default: no valuation rate; stock value hidden unless Finance/owner approves. |
| Sales Manager read-only integration | Outbound Fulfillment, Delivery/Pick Review, Item Stock availability if approved. | Availability/stock reports if approved; no valuation by default. | Open outbound rows, review dispatch posture, apply filters, refresh. | None in Warehouse by default. | Pick/ship execution, Delivery Note submit, stock reservation changes, billing, payment, accounting, native escape. | Product Sales/Warehouse routes only; no native Warehouse escape. | Customer/order commercial fields remain Sales-owned. | Proposed default: no stock value or valuation rate. |
| Finance read-only integration | Stock Ledger, Stock Balance, Stock Movement Review, Warehouse Detail if approved. | Stock Balance, Stock Ledger, Stock Aging, movement history, valuation-sensitive reports if approved. | Open reports, apply filters, review movement evidence. | Review/signoff for reconciliation or valuation-impacting workflows in future design. | Warehouse receiving/picking execution unless also assigned Warehouse role. | Product Warehouse/Finance routes; admin-native access governed separately. | Can see valuation fields if Finance role permits. | Proposed default: visible to Finance. |
| System Manager/Admin exception access | All product routes for support; native admin access outside normal Warehouse UX as existing ERPNext permits. | All reports as ERPNext role permits. | Support diagnostics and route verification. | Emergency native correction only under existing admin policy. | No normal-user shortcut behavior; no unreviewed shared runtime changes. | Native access only as admin/system exception, not as Warehouse normal UX. | Full system visibility by existing ERPNext permission. | Visible as existing ERPNext permission allows. |

Valuation decision:

- `stock_value`, `valuation_rate`, and value-based report columns may be Finance-sensitive.
- Recommended default for W3: do not show valuation rate to Warehouse Manager or Warehouse User.
- Recommended default for W3: show quantity posture only. If stock value is required for manager decisions, expose it to Warehouse Manager only after owner approval.
- Finance read-only users may see valuation data if their existing ERPNext role permits it.

## 6. Data Source Contract

Implementation rule:

- Future code should use controlled Warehouse adapter wrappers, even when the wrapper internally uses `frappe.get_all` or an existing report API.
- The adapter wrapper must enforce role, field allowlist, filter allowlist, row limits, product route targets, and no native route leakage.
- Direct client calls to arbitrary doctypes are not acceptable for Warehouse pages.

| Page or route family | Safe data sources | Read permission expectation | Sensitivity | Performance risk | Future access method | W3 or later |
| --- | --- | --- | --- | --- | --- | --- |
| Overview | Bin, Warehouse, Item, Purchase Order/Purchase Receipt counts, Delivery Note/Pick List counts, Material Request counts, Quality Inspection counts. | Stock User/Warehouse role for Bin/Warehouse/Item; document counts must respect user role and company. | Quantity posture moderate; valuation hidden by default; document identifiers role-sensitive. | Medium if counts scan large tables. | Controlled adapter wrapper with bounded aggregate queries and cached summary where needed. | W3 for Bin/Warehouse/Item and conservative counts; richer counts later. |
| Inbound Receiving | Purchase Order, Purchase Order Item, Purchase Receipt, Purchase Receipt Item, Item, Warehouse, Quality Inspection. | Read only for approved Warehouse/Purchase roles. | Supplier and PO data are Procurement-sensitive; receipt state affects Finance. | High on PO/PR joins without filters. | Controlled adapter wrapper with status/date/company/warehouse filters and row limits. | W4. |
| Receiving Review | Purchase Order, Purchase Receipt, item lines, warehouse, serial/batch, QI. | Read only; no submit/save permissions required. | Supplier, cost/valuation, tracking fields sensitive. | Medium per object; avoid loading unbounded history. | Controlled adapter wrapper by approved ID and type; bounded child rows and recent activity. | W4. |
| Outbound Fulfillment | Sales Order, Pick List, Delivery Note, Packing Slip, Stock Reservation Entry, Bin. | Read only for Warehouse/Sales roles according to owner decision. | Customer/order data and reservations are Sales-sensitive. | High if joining Sales and stock data broadly. | Controlled adapter wrapper with due-date/status filters and row limits. | W7. |
| Fulfillment Review | Pick List, Delivery Note, Sales Order, Packing Slip, Stock Reservation Entry, Bin, serial/batch. | Read only for approved roles. | Customer/order, shipment, tracking fields sensitive. | Medium per object; high if full history unbounded. | Controlled adapter wrapper with product route mapping. | W7. |
| Internal Transfers | Material Request, Material Request Item, Stock Entry, Stock Entry Detail, Warehouse, Bin. | Read only for Stock roles; Manufacturing/Subcontracting rows owner decision. | Transfer demand may reveal production plans. | Medium to high by status and date. | Controlled adapter wrapper with Material Request type allowlist. | W6. |
| Movement Review | Stock Entry, Stock Entry Detail, Material Request, Pick List, Stock Ledger Entry. | Read only for approved Stock/Finance roles. | Ledger/valuation-sensitive fields hidden by role. | Medium per object. | Controlled adapter wrapper; no native target URLs. | W6. |
| Item Stock Detail | Item, Bin, Stock Ledger Entry, Item Reorder, Serial No, Batch, Stock Reservation Entry. | Read Item and stock posture; reservations role-scoped. | Valuation, supplier defaults, Item Price, Item Supplier must be hidden unless specifically approved. | High for ledger/serial history. | Controlled adapter wrapper; bounded recent ledger; report drilldown for full history. | W5. |
| Warehouse Detail | Warehouse, Bin, Stock Ledger Entry, Purchase Receipt, Delivery Note, Material Request, Quality Inspection. | Read Warehouse and stock posture. | Valuation hidden by default; document references role-scoped. | High if showing all items/movements. | Controlled adapter wrapper with bounded top items and recent rows. | W5. |
| Low Stock | Bin, Item, Item Reorder, Material Request, Purchase Order. | Read stock posture; Procurement documents role-scoped. | Reorder posture and shortages are operationally sensitive. | Medium if computed across all items. | Controlled adapter wrapper, possibly materialized/cache later. | W3 owner decision or W5. |
| Serial / Batch Watch | Serial No, Batch, Serial and Batch Bundle, Item, Stock Ledger Entry, Purchase Receipt, Delivery Note. | Read tracking data for approved Stock/Quality roles. | High traceability and expiry sensitivity. | High if unbounded. | Controlled adapter wrapper with strict filters and row limits. | W7/W8. |
| Quality Hold | Quality Inspection, Purchase Receipt, Delivery Note, Stock Entry, Item, Warehouse. | Read Quality Inspection for approved Warehouse/Quality roles. | Quality decisions sensitive; Warehouse must not change them. | Medium. | Controlled adapter wrapper, status-filtered. | W4 or W7 owner decision. |
| Stock Balance report | Existing ERPNext Stock Balance report, Bin, Stock Ledger Entry. | Existing ERPNext report permission plus Warehouse wrapper permission. | Valuation columns sensitive. | High on wide date ranges. | Existing report API through controlled wrapper; field/column policy by role. | W8. |
| Stock Ledger report | Existing ERPNext Stock Ledger report, Stock Ledger Entry. | Existing ERPNext report permission plus Warehouse wrapper permission. | Voucher, valuation, serial/batch sensitive. | High on wide date ranges. | Existing report API through controlled wrapper; mandatory filters/limits. | W8. |
| Stock Projected Qty report | Existing ERPNext projected quantity logic/report, Bin. | Stock role read access. | Operational shortage and reservation posture. | Medium. | Existing report API or controlled aggregate wrapper. | W8 or W5 support. |
| Batch/Serial reports | Available Batch Report, Available Serial No, Batch Item Expiry Status, Serial and Batch Summary. | Stock/Quality role read access. | Traceability and expiry sensitive. | High if broad. | Existing report API through controlled wrapper with filters. | W8. |

Data-source proof required before W3:

- Confirm the live/site data has non-empty Warehouse, Item, and Bin posture or acceptable empty states.
- Confirm selected counts can be computed without full-table scans.
- Confirm Warehouse Manager/User roles can read required fields through server-side checks.
- Confirm valuation fields can be omitted cleanly from W3 payloads.

## 7. Native Escape And Route Protection Plan

Default policy:

- Normal Warehouse Manager/User routes must not expose native ERPNext forms or native reports.
- Any native exception must be admin-only or separately approved in a later phase.
- W3 through W10 should not include Warehouse governed native exceptions.

Route fragments forbidden in normal Warehouse page targets:

- `/app/`
- `/desk#Form/`
- `Form/`
- `List/`
- `Report/`
- `query-report/`
- `Tree/`
- `Module/`
- `Workspaces/`
- `stock-entry`
- `purchase-receipt`
- `delivery-note`
- `stock-reconciliation`
- `material-request`
- `pick-list`
- `quality-inspection`
- `serial-no`
- `batch`

Allowed target prefix:

- `/desk/warehouse-console`
- `/desk/warehouse-console-worklist/`
- `/desk/warehouse-console-report/`
- `/desk/warehouse-console-reports`
- Optional `/desk/warehouse-console-home`

Action labels that must not appear as enabled controls on Warehouse product pages:

- Submit
- Cancel
- Amend
- Close
- Unclose
- Approve
- Reject
- Receive
- Ship
- Dispatch
- Post
- Reconcile
- Reserve
- Unreserve
- Bill
- Pay
- Send
- Email
- Delete
- Create Purchase Receipt
- Create Stock Entry
- Create Delivery Note
- Create Stock Reconciliation
- Assign Serial No
- Assign Batch No
- Update Item
- Update Warehouse
- Update Item Price
- Set Default Supplier
- Update Item Supplier

Native form/report escape scan terms:

- `Open ERP`
- `Open ERP Form`
- `Open native`
- `native form`
- `native report`
- `frappe.set_route(\"Form\"`
- `frappe.set_route(\"List\"`
- `frappe.set_route(\"query-report\"`
- `#Form/`
- `/app/`
- `doctype=`
- `new_doc`
- `make_new_doc_and_get_name`
- `submit`
- `cancel`
- `amend`

Workspace governance manifest entries needed in W3:

- Warehouse overview route.
- Optional Warehouse home/launcher route if used.
- Warehouse Overview navigation actions.
- Warehouse sidebar navigation actions.
- Warehouse read-only Refresh action.
- Warehouse forbidden mutation guard.
- Any W3 Low Stock route/action if owner includes it.

Route ownership expectations:

- `workspace_registry.py` should declare Warehouse only when W3 implementation begins.
- The registry should map Warehouse routes, methods, sidebar metadata, managed doctypes for visibility, and role family.
- The governance manifest should classify every W3 route and visible W3 action before protected acceptance.

Sidebar and search target restrictions:

- Sidebar items must target Warehouse product routes only.
- Sidebar must not expose ERPNext Stock module pages.
- Shared search must be disabled for Warehouse until W9 or limited to Warehouse product targets only if owner accelerates search.
- Search results must preview before opening and must not auto-open on Enter.
- Search result targets must not include native form or report routes.

## 8. Warehouse Visible-Copy Contract

Do not show developer or governance vocabulary to normal users.

Avoid in visible Warehouse UI:

- Productized
- native ERP
- governed
- deferred
- route only
- mutation
- backend
- frontend
- framework
- smoke
- test
- Frappe
- method names
- route keys
- DocType unless the ERP term is also the business term users expect

Preferred business terms:

- Review receiving
- Review dispatch
- Stock movement
- Needs attention
- Open Warehouse page
- Read-only
- Action not active yet
- Stock available
- Reserved
- Incoming
- Requested
- Projected
- Quality hold
- Serial/batch required
- Low stock
- Internal transfer
- Recent movement

Overview section labels:

- `Needs attention`
- `Inbound work`
- `Outbound work`
- `Internal movement`
- `Stock health`
- `Quality and tracking`
- `Reports`

Worklist filter labels:

- `Warehouse`
- `Item`
- `Company`
- `Status`
- `Due from`
- `Due to`
- `Supplier`
- `Customer`
- `Movement type`
- `Quality status`
- `Tracking status`

Empty states:

- Overview: `No warehouse work needs attention right now.`
- Inbound: `No receiving is due for the selected filters.`
- Outbound: `No dispatch work is due for the selected filters.`
- Transfers: `No internal transfers match the selected filters.`
- Low stock: `No low stock items match the selected filters.`
- Serial/batch: `No serial or batch issues match the selected filters.`
- Quality hold: `No quality holds match the selected filters.`
- Reports: `No report rows match the selected filters.`

Read-only badges:

- `Read-only`
- `For review`
- `Review only`

Future inactive actions:

- Prefer hiding inactive actions.
- If an inactive action must be visible for owner review, use `Action not active yet`.
- Do not show `deferred`, `future governed`, `mutation`, or `not implemented`.

Error states:

- Permission: `You do not have access to this Warehouse page.`
- Missing record: `This Warehouse record could not be found.`
- Load failure: `Warehouse information could not be loaded. Refresh or try again.`
- Restricted action: `This action is not active for your role.`

Quantity labels:

- `Stock available` for available/actual posture where the data contract defines it.
- `Reserved` for demand-held quantity.
- `Incoming` for ordered supply not yet received.
- `Requested` for material requested but not fulfilled.
- `Projected` for ERPNext projected quantity.
- `Stock UOM` for unit display.

## 9. Smoke And Gate Plan

No smoke script is created in W2. This section defines the future W3+ strategy.

Future W3 smoke coverage:

- Warehouse Overview route loads for Warehouse Manager.
- Warehouse Overview route loads for Warehouse User.
- Optional Warehouse Home route redirects or hands off cleanly if implemented.
- Sidebar entry appears only for approved Warehouse roles.
- No native ERP escape labels or route targets are visible.
- No stock mutation buttons are visible.
- KPI cards render without horizontal overflow at 1136, 1240, and 1440 widths.
- Duplicate shell/header/sidebar count remains 1 after direct load, refresh, repeated navigation, and back/forward.
- Warm navigation performance meets target.
- Sales freeze passes after runtime/shared changes.
- Procurement protected gate passes after runtime/shared changes.

Future worklist/detail smoke coverage:

- List filters render.
- Apply, Reset, and Refresh work in place.
- Row links open Warehouse product routes only.
- Object pages have summary plus tabs.
- Recent rows are bounded.
- Full history routes through reports.
- Native form/report leakage is absent.
- Lifecycle and stock mutation controls are absent.
- Empty/restricted/error states are visually distinct.

Future report smoke coverage:

- Report routes load through Warehouse report shell.
- Filters render with stable command alignment.
- Wide tables stay inside the report region.
- Rows drill into Warehouse product routes where a detail route exists.
- Native report links are absent for normal users.
- Valuation columns follow role policy.

Future static scans:

- Native escape scan using route fragments and labels in section 7.
- Stock mutation forbidden scan for Receive, Ship, Dispatch, Post, Reconcile, Stock Entry, Purchase Receipt, Delivery Note, Stock Reconciliation, Reserve, Unreserve, Assign Serial No, Assign Batch No.
- Lifecycle forbidden scan for Submit, Cancel, Amend, Close, Unclose, Approve, Reject, Delete.
- Copy-risk scan for Productized, native ERP, governed, deferred, route only, mutation, backend, frontend, framework, smoke, test, Frappe, method names.
- Sales/Procurement dirty-file check before final W3 closure.
- Manifest coverage check for every Warehouse route/action visible in W3.

Future protected gate sequence after W3 runtime changes:

1. Source gate.
2. Python compileall.
3. Unit discovery.
4. JavaScript syntax check for touched runtime files.
5. Warehouse W3 smoke.
6. Sales freeze protection.
7. Procurement protected gate.
8. `git diff --check HEAD`.
9. Owner manual UI review.
10. Source/live hash proof only after live alignment is explicitly approved.

## 10. W3 Implementation Readiness Checklist

W3 must not start until each item is resolved:

- Owner-approved W3 route list.
- Owner-approved route names and URL patterns.
- Owner-approved role model.
- Owner-approved Warehouse Manager and Warehouse User labels.
- Owner-approved W3 KPI definitions.
- Owner-approved visible fields.
- Valuation visibility decision made for Warehouse Manager, Warehouse User, Sales Manager, Purchase Manager, and Finance.
- W3 data-source proof from live/site data for Warehouse, Item, Bin, and selected counts.
- W3 empty-state proof if stock data is sparse.
- W3 smoke plan approved.
- Protection gate plan approved.
- Native escape static scan terms approved.
- Forbidden stock/lifecycle action scan terms approved.
- Sales/Procurement regression gate requirement accepted.
- Rollback/live-alignment plan approved.
- Decision made on whether `warehouse-console-home` is needed.
- Decision made on whether Low Stock appears in W3 or waits until W5.
- Decision made on whether Quality Hold appears in W3 or waits.

Minimum W3 recommended scope:

- Registry entry for Warehouse.
- Governance manifest entries for W3 Warehouse routes/actions.
- Warehouse Overview route.
- Optional Warehouse Home launcher only if role routing needs it.
- Sidebar entry for approved Warehouse roles.
- Read-only KPI cards and bounded exception cards from safe data.
- No Warehouse worklists unless Low Stock is explicitly approved for W3.
- No Warehouse detail pages.
- No Warehouse reports.
- No Quick Find.
- No native escape.
- No stock execution.

## 11. Owner Decisions Needed

Owner decisions before W3:

- Confirm Warehouse Console visibility-first scope.
- Confirm W3 route list.
- Confirm whether `/desk/warehouse-console-home` is needed.
- Confirm Warehouse Manager and Warehouse User access labels.
- Decide whether Purchase Manager gets early read-only Inbound/Receiving visibility.
- Decide whether Sales Manager gets early read-only Outbound/Fulfillment visibility.
- Decide whether Finance gets early Stock Balance/Stock Ledger visibility.
- Decide valuation visibility for Warehouse Manager.
- Decide valuation visibility for Warehouse User.
- Decide whether Low Stock appears in W3 or waits until W5.
- Decide whether Quality Hold appears in W3, W4, W7, or later.
- Decide whether Warehouse Quick Find stays W9 or moves earlier.
- Confirm no execution actions until a later controlled execution design.
- Confirm no native ERPNext form/report exceptions for normal Warehouse users in W3 through W10.

Owner decisions before any future execution phase:

- Which role may create and submit Purchase Receipts.
- Which role may create and submit Stock Entries.
- Which role may create and submit Delivery Notes.
- Whether Stock Reconciliation is Warehouse-owned, Finance-owned, or co-owned.
- Serial/batch assignment policy.
- Quality inspection handoff policy.
- Approval, audit, and reversal policy for every stock-affecting action.

## 12. Explicit W2 Non-Goals

This W2 phase does not:

- Create Warehouse routes.
- Add registry entries.
- Add workspace manifest entries.
- Edit Python, JavaScript, or CSS runtime.
- Edit tests.
- Edit smoke scripts.
- Touch Sales runtime.
- Touch Procurement runtime.
- Live-align anything.
- Implement receiving.
- Implement delivery.
- Implement stock transfer.
- Implement stock reconciliation.
- Implement serial/batch assignment.
- Implement quality actions.
- Expose native ERPNext routes.

## 13. W2 Validation Plan

Required validation for this docs-only phase:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`

Not required for W2:

- Live alignment.
- Protected workspace gate.
- Playwright smoke.

Reason:

- W2 changes documentation only. Protected gates become mandatory when runtime, route, smoke, test, shared shell, Sales, Procurement, or Warehouse implementation files change.

## 14. Recommended Handover

Recommended next step:

- Ask the owner to approve the W3 readiness checklist decisions.

Recommended first implementation after owner approval:

- W3 should implement only the smallest safe Warehouse foundation: registry and manifest entries, Warehouse Overview, sidebar entry, read-only KPIs, native-escape guards, forbidden-action guards, focused Warehouse smoke, and Sales/Procurement gates.

Do not start Warehouse worklists, object pages, reports, Quick Find, or execution actions until the approved phase sequence reaches them.
