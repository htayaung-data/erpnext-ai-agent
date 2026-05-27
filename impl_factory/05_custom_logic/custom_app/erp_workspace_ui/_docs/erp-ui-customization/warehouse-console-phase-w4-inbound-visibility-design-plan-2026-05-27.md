# Warehouse Console Phase W4 Inbound Visibility Design Plan

Date: 2026-05-27

Branch: `feature/erpnext-ui-design`

Status: docs-only W4 design plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, or live alignment.

Runtime baseline before W4 design:

- W3 read-only foundation: `368dc645e1ce6a6c80849c3cb211c06ade790d7a`
- W3A protected landing closure: `cca15a5fca07ad9bfc4e116101e08536880d8e62`
- W3/W3A baseline documentation: `2b69c22401c007aed535dee78dec870f25a95f54`

## 1. Executive Recommendation

W4 should add serious inbound visibility, not receiving execution.

Recommended W4 implementation scope after this design is approved:

- Add an inbound section to the existing Warehouse Overview.
- Add a read-only Inbound Receiving Queue at `/desk/warehouse-console-worklist/inbound-receiving`.
- Add a read-only Receiving Review object page at `/desk/warehouse-console-receiving/<purchase-order>` only if the queue needs a drilldown in the same phase.
- Use submitted Purchase Orders and Purchase Order Items as the expected-inbound source of truth.
- Use Purchase Receipts as receipt history/proof only.
- Keep Material Request transfer visibility out of W4 unless the owner explicitly accepts it as a small inbound transfer watch; otherwise it belongs in W6 stock movement and transfer visibility.
- Keep Quality Inspection as a read-only indicator only, not an approval/rejection workflow.
- Keep valuation, billing, supplier pricing, Item Price, Default Supplier, Item Supplier, native ERPNext forms/reports, and all stock lifecycle actions out of W4.

The goal is to turn W3's basic overview into a premium warehouse workspace: the first viewport should answer what is due, what is late, what is partially received, and what needs attention, then offer a product-owned review path. It must not look like a copied ERPNext List View.

## 2. Research Basis

### 2.1 Local ERPNext Source Reviewed

Installed ERPNext source in the live bench was reviewed first under:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/purchase_order/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/purchase_order_item/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/purchase_receipt_item/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/stock_entry/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/bin/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/warehouse/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/material_request/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/pick_list/`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/stock/doctype/quality_inspection/`

Source-backed ERPNext findings:

- `Purchase Order` is a submittable Buying document with `supplier`, `company`, `transaction_date`, header `schedule_date`, optional `set_warehouse`, `items`, `status`, `per_received`, and `per_billed`.
- `Purchase Order Item` carries inbound line facts including `item_code`, `item_name`, `schedule_date`, `expected_delivery_date`, `qty`, `stock_uom`, `uom`, `conversion_factor`, `warehouse`, `stock_qty`, `received_qty`, `actual_qty`, and `from_warehouse`.
- ERPNext's Purchase Order list indicator logic treats submitted POs with `per_received < 100` as receiving candidates when the status is `To Receive` or `To Receive and Bill`.
- ERPNext updates Purchase Order `per_received` from item-level `received_qty` against ordered `qty`. This makes submitted POs and PO Items the safest read-only expected-inbound source.
- `make_purchase_receipt` maps a Purchase Order to a Purchase Receipt by using remaining quantity (`qty - received_qty`). W4 must not call this mapping path because it creates a receiving action path.
- `Purchase Receipt` is a submittable Stock document. It records accepted/rejected received quantities, accepted warehouse, rejected warehouse, serial/batch information, quality inspection references, and purchase order links.
- Purchase Receipt submission updates stock and Purchase Order received quantities. This is execution and is outside W4.
- `Stock Entry` is submittable and covers Material Receipt, Material Transfer, Material Issue, Manufacture, Repack, and other stock movement purposes. It is not a W4 inbound PO visibility source except as a future transfer/movement integration.
- `Bin` is the warehouse/item quantity posture table with `actual_qty`, `reserved_qty`, `ordered_qty`, and `projected_qty`. It is useful for context but should not drive the inbound receiving queue.
- `Warehouse` provides warehouse identity and company context.
- `Material Request` supports purchase, material transfer, issue, manufacture, subcontracting, and customer-provided purposes. Transfer requests should be designed in the later movement/transfer phase unless owner approves a narrow inbound transfer watch.
- `Pick List` is outbound-oriented for delivery/material transfer/manufacture and should not be part of W4 inbound receiving.
- `Quality Inspection` can be linked to incoming stock documents and can block receipt submission when inspection is required. W4 can show a read-only quality indicator, but approval/rejection is not in scope.

### 2.2 Official Documentation Reviewed

Official/vendor sources used:

- ERPNext Purchase Order: https://docs.frappe.io/erpnext/purchase-order
- ERPNext Purchase Receipt: https://docs.frappe.io/erpnext/purchase-receipt
- ERPNext Material Request: https://docs.frappe.io/erpnext/material-request
- ERPNext Quality Inspection: https://docs.frappe.io/erpnext/quality-inspection
- ERPNext Stock Entry: https://docs.frappe.io/erpnext/stock-entry
- SAP EWM inbound delivery: https://help.sap.com/docs/SAP_SUPPLY_CHAIN_MANAGEMENT/dc8e3ce481cc493aad2145b99e6c53eb/57cbcb53ad377114e10000000a174cb4.html
- SAP EWM inbound process: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9832125c23154a179bfa1784cdc9577a%20/e15a4205bb284393add14c9d419fef45.html
- Microsoft Dynamics 365 Warehouse management overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-management-overview
- Microsoft Dynamics 365 inbound loads: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/create-or-modify-an-inbound-load
- Oracle Fusion Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/24b/famli/inventory-management-work-area.html
- Oracle Fusion tasks from Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/famml/overview-of-tasks-from-the-inventory-management-work-area.html
- Odoo incoming shipments and delivery orders: https://www.odoo.com/documentation/14.0/applications/inventory_and_mrp/inventory/management/shipments_deliveries.html
- NetSuite receiving orders: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_N2410585.html
- NetSuite WMS receiving orders: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1541435923.html
- NetSuite purchase order management: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N2399585.html

Source-backed vendor patterns:

- SAP EWM separates expected inbound/goods receipt preparation, inbound delivery, goods receipt, putaway planning, and warehouse tasks. This supports separating W4 visibility from future receipt/putaway execution.
- Microsoft Dynamics 365 treats warehouse management as inbound and outbound process workflows integrated with purchase, transfer, sales, transportation, manufacturing, and quality. Inbound loads can be created from purchase orders or shipment orders, but that is an execution/planning step, not a W4 action.
- Oracle Inventory Management exposes work areas and task groups for inventory, picks, shipments, and receipts. Receipt tasks include expected shipments, inbound shipments, receipt inspection, and put away. This supports a grouped queue model rather than one raw table.
- Odoo inventory distinguishes one-step, two-step, and three-step receipts. More advanced flows introduce input and quality locations before stock, which supports W4's quality-hold visibility without quality approval.
- NetSuite receiving docs identify vendor PO receipts, transfer receipts, and customer returns as separate inbound reasons. NetSuite also separates advanced receiving from billing, showing why W4 must not cross into Finance.

Design inference from research:

- Warehouse users need a time-prioritized inbound queue, not a general PO list.
- The best first inbound scope is expected receipts from submitted Purchase Orders because it is familiar to ERPNext, can be bounded by due date and `per_received`, and does not require posting stock.
- Purchase Receipt and Quality Inspection data can enrich review context after the queue is stable.
- Transfer receiving, returns, ASN/load planning, putaway, serial/batch capture, and barcode execution should remain future phases.

## 3. ERPNext Data Source Map

| Concept | ERPNext source | W4 use | Safe fields | Excluded fields/actions | Phase posture |
| --- | --- | --- | --- | --- | --- |
| Expected inbound from suppliers | `Purchase Order`, `Purchase Order Item` | Primary W4 queue source | PO name, supplier, status, transaction date, required date, line count, item count, target warehouse, `per_received`, remaining quantity summary, owner/buyer if available | rates, amounts, taxes, payment terms, create Purchase Receipt, close/update PO | Include W4 |
| Receipt history | `Purchase Receipt`, `Purchase Receipt Item` | Read-only proof of what has already arrived | receipt name, posting date, status, accepted qty, rejected qty, item count, linked PO, accepted warehouse | submit, cancel, amend, return, rejected warehouse mutation, serial/batch capture, valuation | Optional in W4 detail |
| Stock posture context | `Bin`, `Warehouse`, `Item` | Supporting context only | item, warehouse, stock UOM, actual qty, reserved qty, ordered qty, projected qty | stock value, valuation rate, inventory account, price list, Item Price | Limited context only |
| Internal inbound transfers | `Material Request` where type is Material Transfer, possibly `Stock Entry` later | Not primary W4; candidate for W6 movement/transfer | request id, from warehouse, target warehouse, item count, schedule date, status | Stock Entry creation/submission, transfer execution | Defer unless owner approves narrow watch |
| Quality hold / inspection | `Quality Inspection`, Item inspection flags, Purchase Receipt Item quality links | Indicator only | inspection required indicator, existing inspection status if safely linked, count of lines needing attention | approve, reject, create inspection, modify readings | Optional indicator; no action |
| Pick/dispatch | `Pick List`, `Delivery Note`, Sales documents | Not inbound | none for W4 | pick, pack, dispatch, ship | Exclude W4 |
| Stock ledger and reconciliation | `Stock Ledger Entry`, `Stock Reconciliation` | Not needed for inbound visibility | none for W4 | post, reconcile, valuation, ledger mutation | Exclude W4 |

## 4. W4 Ownership Boundaries

Warehouse W4 owns:

- Read-only inbound receiving posture for Warehouse roles.
- Supplier PO receiving queue visibility after Procurement has created and submitted the commercial Purchase Order.
- Operational grouping by due date, overdue state, partial receipt, target warehouse, and exception indicators.
- Read-only drilldown into PO receiving posture if owner approves the detail page in W4.
- Business-safe empty, restricted, loading, and unavailable states.

Warehouse W4 does not own:

- Supplier sourcing.
- RFQ or Supplier Quotation.
- Purchase Order creation, commercial approval, update, hold, close, or cancellation.
- Supplier pricing, Item Price, Default Supplier, or Item Supplier mutation.
- Purchase Receipt creation or submission.
- Stock Entry creation or submission.
- Quality Inspection creation, approval, rejection, or readings.
- Putaway execution.
- Serial or batch assignment.
- Billing, payment, accounting, taxes, landed costs, or valuation.
- Customer returns or inbound returns unless separately designed.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

## 5. Proposed W4 Pages And Routes

| Route | Page title | Purpose | Target role | Source | Behavior | W4 recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/desk/warehouse-console` | Warehouse Console | Existing Overview with inbound work section | Warehouse Manager, Warehouse User / Stock User | PO/PO Item counts plus W3 safe metrics | Read-only summary and link to queue | Include | Medium because Overview changes must preserve W3/W3A landing |
| `/desk/warehouse-console-worklist/inbound-receiving` | Inbound Receiving | Operational queue for expected supplier receipts | Warehouse Manager, Warehouse User / Stock User | Purchase Order and Purchase Order Item | Read-only grouped queue, filters, product route links | Include | Medium due data volume and role filtering |
| `/desk/warehouse-console-receiving/<purchase-order>` | Receiving Review | Object review for one PO receiving posture | Warehouse Manager, Warehouse User / Stock User | Purchase Order, Purchase Order Item, optional Purchase Receipt history | Read-only object page with tabs | Include only if queue needs drilldown in W4; otherwise W5 candidate | Medium-high because detail aggregation must stay bounded |
| `/desk/warehouse-console-worklist/inbound-transfers` | Inbound Transfers | Expected stock coming from another warehouse | Warehouse Manager only initially | Material Request / Stock Entry context | Read-only watch | Defer to W6 unless owner overrides | Medium-high due overlap with transfer execution |

Recommended W4 route set:

- Required: `/desk/warehouse-console` Overview updates.
- Required: `/desk/warehouse-console-worklist/inbound-receiving`.
- Conditional: `/desk/warehouse-console-receiving/<purchase-order>` if owner wants read-only drilldown now.
- Deferred: inbound transfers, returns, putaway, ASN/load planning, and Quick Find.

## 6. Proposed Overview Changes

The W4 Overview should remain compact. It should add inbound visibility without turning the first screen into a diagnostic stack.

Recommended first viewport order:

1. Existing Warehouse title/header and high-level KPIs.
2. Inbound summary cards.
3. A priority receiving queue preview.
4. Existing W3 stock/movement posture sections, trimmed if needed to avoid vertical overload.

Recommended inbound summary cards:

- `Receiving Due Today`
- `Overdue Receiving`
- `Partially Received`
- `Expected Soon`

Recommended priority preview:

- Show up to 6 receiving records.
- Group label order: `Overdue`, `Due Today`, `Partially Received`, `Expected Soon`.
- Each preview row shows supplier, PO id, target warehouse, due date, received percent, remaining line count, and `Review receiving` read-only link.
- Empty copy: `No receiving due today.` or `No inbound work needs attention.`

Do not show:

- Raw PO table with every column.
- Price, rate, tax, billing, stock value, or valuation data.
- Buttons labeled `Receive`, `Submit`, `Create`, `Post`, `Cancel`, `Amend`, or `Reconcile`.
- Native ERPNext form/report/list links.

## 7. Proposed Inbound Queue Behavior

The Inbound Receiving Queue should answer: what should the warehouse expect, what is late, what is partly received, and where should the stock arrive?

Default queue groups:

- `Overdue`: submitted POs with at least one unreceived line due before today.
- `Due Today`: submitted POs with at least one unreceived line due today.
- `Partially Received`: submitted POs with `per_received > 0` and `< 100`.
- `Expected Soon`: submitted POs with unreceived lines due within the default horizon, recommended 14 days.

Default query posture:

- Include `docstatus = 1` only.
- Include `per_received < 100`.
- Include statuses that indicate receipt is still open, expected candidates are `To Receive` and `To Receive and Bill`.
- Exclude `Draft`, `Cancelled`, `Closed`, `Completed`, and fully received orders.
- Exclude POs without warehouse-relevant stock items if the data can be determined cheaply.

Filters:

- Due window: overdue, today, next 7 days, next 14 days, custom range.
- Supplier.
- Target warehouse.
- Receiving state: overdue, due today, partially received, expected soon.
- Item search by item code/name, only after bounded query behavior is proven.
- Buyer/owner if available and useful to Warehouse Manager.

Allowed actions:

- `Open Warehouse page`.
- `Review receiving`.
- `Apply filters`.
- `Reset filters`.
- `Refresh`.

Row content:

- Priority badge.
- PO id.
- Supplier.
- Required/expected date.
- Target warehouse or `Multiple warehouses`.
- Line count and item count.
- Received percent.
- Remaining quantity summary in stock UOM where practical.
- Quality indicator only if safely derived.
- Buyer/owner if useful and not sensitive.

Empty, loading, restricted, and error states:

- Loading: `Checking inbound work...`
- Empty default: `No inbound receiving needs attention.`
- Empty filter: `No receiving matches these filters.`
- Restricted: `You do not have access to inbound receiving.`
- Partial data unavailable: `Some receiving details are unavailable for your role.`
- Error: `Receiving work could not be loaded. Refresh or contact an administrator.`

The queue should not display raw framework errors or permission traces.

## 8. Proposed Receiving Review Object Page

If included in W4, the Receiving Review page should be an object-profile page, not a native ERPNext form.

Route:

- `/desk/warehouse-console-receiving/<purchase-order>`

Header:

- PO id.
- Supplier.
- Receiving state badge: `Overdue`, `Due Today`, `Partially Received`, `Expected Soon`, or `On Track`.
- Required date.
- Received percent.
- Target warehouse summary.
- Read-only badge.

Tabs:

- `Summary`: supplier, due date, warehouse summary, received percent, line count, attention reasons.
- `Lines`: bounded PO item rows with item, remaining qty, stock UOM, due date, target warehouse, received qty.
- `Receipts`: latest submitted Purchase Receipts linked to the PO, bounded to recent 10.
- `Quality`: inspection-needed indicators and existing inspection status where safely linked.
- `Activity`: bounded business history if available without native comments/feed leakage.

Object page rules:

- Show bounded rows only.
- Use full-history drilldowns only after Warehouse reports exist.
- Do not expose native form openers.
- Do not show raw tax, rate, amount, billing, valuation, or ledger fields.
- Do not show disabled fake execution buttons.
- Use `Action not active yet` only if the owner explicitly wants inactive action messaging; default W4 should simply omit execution actions.

## 9. Role Matrix

| Role | Overview | Inbound queue | Receiving review | Reports | Future action candidates | Forbidden in W4 | Valuation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse Manager | Yes | Yes | Yes if route included | No W4 reports | Future controlled receiving review approvals only after separate design | create/submit/cancel PR, Stock Entry, quality approval, serial/batch, native routes | Hidden |
| Warehouse User / Stock User | Yes | Yes | Yes if route included, same read-only posture | No W4 reports | Future guided receiving task execution only after separate design | all lifecycle and stock mutations | Hidden |
| Purchase Manager | No by default unless they also have Warehouse role | No by default | No by default | No | Future read-only cross-workspace visibility decision | Warehouse access without Warehouse role | Hidden |
| Sales Manager | No by default unless they also have Warehouse role | No by default | No by default | No | Future outbound visibility integration only | Inbound access without Warehouse role | Hidden |
| Finance | No by default unless they also have Warehouse role | No by default | No by default | No | Future valuation/accounting read-only in Finance workspace, not W4 | valuation leakage into W4 | Hidden |
| System Manager/Admin | Admin/support exception | Admin/support exception | Admin/support exception | Admin/support exception | Support diagnostics only | Forced Warehouse landing or normal-user native escape | Admin policy, not W4 UI |

Role principles:

- W4 is Warehouse-role only.
- Purchase, Sales, and Finance users do not gain Warehouse access unless they also hold a Warehouse/Stock role.
- System Manager/Admin bypass policy from W3A stays protected.
- W4 does not introduce a new native route exception.

## 10. Safe Fields And Forbidden Fields/Actions

Safe W4 fields:

- Purchase Order id.
- Supplier name.
- Company if needed for filtering and user permission context.
- Transaction date.
- Required date / schedule date / expected delivery date.
- Target warehouse.
- Item count.
- Line count.
- Ordered quantity.
- Received quantity.
- Remaining quantity.
- Stock UOM.
- Received percent.
- Status.
- Buyer/owner if accepted by owner.
- Existing Purchase Receipt id and posting date in bounded history.
- Existing quality indicator/status if safely linked.

Forbidden W4 fields:

- Rate.
- Price list rate.
- Last purchase rate.
- Amount.
- Base amount.
- Taxes and charges.
- Grand total.
- Billing status beyond a non-financial hidden internal filter.
- Vendor bill references.
- Stock value.
- Valuation rate.
- Inventory account.
- Expense account.
- Cost center unless explicitly approved as warehouse-visible.
- Landed cost.
- Currency conversion details.
- Item Price.
- Default Supplier mutation fields.
- Item Supplier mutation fields.

Forbidden W4 actions:

- Create Purchase Receipt.
- Submit Purchase Receipt.
- Cancel Purchase Receipt.
- Amend Purchase Receipt.
- Create Stock Entry.
- Submit Stock Entry.
- Create Stock Reconciliation.
- Submit Stock Reconciliation.
- Post, reconcile, approve, reject, close, hold, unhold, reserve, unreserve.
- Assign Serial No.
- Assign Batch No.
- Create or approve Quality Inspection.
- Create Material Request.
- Convert Material Request.
- Update Item master.
- Update Warehouse master.
- Update Item Price.
- Update Default Supplier.
- Update Item Supplier.
- Open native ERPNext form, list, report, workspace, or query report.

## 11. UI Layout Sketches

Overview first viewport at 1440px:

```text
[Warehouse Console header]
[Active Warehouses] [Stocked Items] [Receiving Due Today] [Overdue Receiving] [Expected Soon]

Inbound Work                                         [Open receiving queue]
[Overdue count] [Due today count] [Partially received count]
- Supplier A | PO-00012 | WH/Main | Due May 27 | 40% received | Review receiving
- Supplier B | PO-00018 | WH/Raw | Overdue 2d | 0% received | Review receiving

Stock Health / Movement Watch stays compact below the fold edge.
```

Inbound queue at 1440px:

```text
[Inbound Receiving header]
[Due window] [Supplier] [Warehouse] [State] [Apply] [Reset] [Refresh]

[Overdue lane]             [Due Today lane]          [Expected Soon lane]
PO card                    PO card                   PO card
Supplier                   Supplier                  Supplier
Due date / warehouse       Due date / warehouse      Due date / warehouse
Received percent           Received percent          Received percent
Review receiving           Review receiving          Review receiving

[Partially Received] appears as a full-width compact band when count is high.
```

Receiving Review at 1240px:

```text
[PO id] [Supplier] [Receiving state] [Read-only]
Required date | Received percent | Target warehouse | Remaining lines

Tabs: Summary | Lines | Receipts | Quality | Activity

Summary tab:
- Attention reasons
- Warehouse targets
- Latest receipt proof
- Remaining item groups
```

Responsive behavior:

- 1440px: KPI cards in one row where possible; queue can use 3 columns for priority lanes.
- 1240px: KPI cards wrap to two rows; queue uses two columns or one priority column with side summary.
- 1136px: filters wrap into a compact toolbar; lanes collapse into stacked groups; cards retain fixed min/max widths and no horizontal overflow.
- All breakpoints must preserve one shell, one header, one sidebar, no overlapping text, and no horizontal scroll.

## 12. Copy Contract

Preferred visible copy:

- `Inbound Work`
- `Receiving Due Today`
- `Overdue Receiving`
- `Partially Received`
- `Expected Soon`
- `Review receiving`
- `Stock due into warehouse`
- `No receiving due today.`
- `No inbound receiving needs attention.`
- `Some receiving details are unavailable for your role.`

Do not use visible copy that implies execution:

- `Receive`
- `Receive All`
- `Create Purchase Receipt`
- `Submit`
- `Post`
- `Cancel`
- `Amend`
- `Reconcile`
- `Approve Quality`
- `Reject Quality`
- `Assign Serial`
- `Assign Batch`

Do not use visible developer/governance wording:

- `Productized`
- `native ERP`
- `governed`
- `deferred`
- `route only`
- `mutation`
- `backend`
- `frontend`
- `framework`
- `smoke`
- `test`
- `Frappe`

Business wording is allowed where it is also a normal ERP term, such as Purchase Order, Purchase Receipt, warehouse, supplier, item, quality, receiving, and stock.

## 13. Performance And Row-Limit Strategy

Implementation should be designed before code around these limits:

- Overview inbound preview: max 6 rows.
- Inbound queue first page: max 50 rows total, grouped by state.
- Receiving Review lines: max 100 PO lines, with a bounded overflow state if the PO is larger.
- Receipt history: max 10 recent Purchase Receipts.
- Quality rows: max 20 indicators unless a future Quality page exists.
- Default due horizon: overdue plus next 14 days.

Query strategy recommendation:

- Query Purchase Order headers first with `docstatus = 1`, `per_received < 100`, and allowed statuses.
- Use a date window based on header `schedule_date` and child row `schedule_date` or `expected_delivery_date`.
- Aggregate child PO Item details server-side through a controlled adapter wrapper.
- Fetch only allowlisted fields.
- Avoid Stock Ledger Entry for W4; it is too broad and not required for expected receiving.
- Avoid unbounded `Purchase Order Item` scans by applying parent/date/status constraints first.
- Do not fetch valuation, rates, taxes, or billing fields.
- Convert permission failures into business-safe unavailable states.
- Track first useful render and warm navigation timings in future W4 smoke.

Open performance questions before implementation:

- Which Purchase Order date field is most reliable on the MEET data set: header `schedule_date`, child `schedule_date`, child `expected_delivery_date`, or a fallback hierarchy?
- How many submitted open POs exist in production data?
- Are target warehouses consistently set at header or item level?
- Are stock UOM and conversion factors clean enough for remaining quantity summaries?

## 14. Future Smoke And Test Plan

Required W4 focused smoke coverage after implementation:

- Warehouse Manager can open `/desk/warehouse-console` and see inbound summary cards.
- Warehouse User / Stock User can open `/desk/warehouse-console` and see inbound summary cards.
- Warehouse Manager/User can open `/desk/warehouse-console-worklist/inbound-receiving`.
- Purchase/Sales/Finance users do not get W4 Warehouse access unless they also have Warehouse role.
- `/desk` landing still routes Warehouse operational users to Warehouse Console without duplicate shell/header/sidebar.
- Inbound queue filters render and Apply/Reset/Refresh work.
- Queue rows open only Warehouse product routes.
- Receiving Review, if included, has summary header and tabs.
- Bounded row counts are enforced.
- No native ERPNext form/list/report/workspace links appear in Warehouse-owned UI.
- No receiving execution or stock lifecycle buttons appear.
- No valuation fields or copy appear.
- No developer/governance copy appears in Warehouse-owned UI.
- No horizontal overflow at 1136, 1240, and 1440 widths.
- Duplicate shell/header/sidebar count remains 1 after direct route, refresh, `/desk` landing, and repeated navigation.
- Warm route navigation meets the accepted target.
- Sales freeze remains green.
- Procurement protected gate remains green.
- Full protected workspace gate remains green.

Future unit/contract tests:

- Registry and governance manifest include W4 route ownership when implementation begins.
- Service contract returns only allowlisted fields.
- Service contract never returns valuation/rate/tax fields.
- Role access blocks non-Warehouse roles.
- Empty, limited, and permission-safe states are deterministic.

Future static scans:

- Native escape scan: `/app`, `/desk/Form`, `frappe.set_route("Form"`, native list/report/query report route strings.
- Stock action scan: receive, submit, cancel, amend, post, reconcile, reserve, unreserve, Stock Entry, Purchase Receipt creation, Stock Reconciliation creation, serial/batch assignment controls.
- Valuation scan: stock value, valuation rate, `stock_value`, `valuation_rate`, amount/rate fields in Warehouse runtime payloads.
- Copy-risk scan: developer/governance terms in visible Warehouse UI strings.
- Dirty-boundary scan: no Sales or Procurement runtime files changed unless explicitly required shared files are protected by gates.

## 15. Live Alignment And Rollback Expectations

No live alignment happens in this W4 design phase.

Future W4 implementation live rules:

- Commit and push only after source compile, unit tests, node checks, static scans, focused W4 smoke, Sales freeze, Procurement protected coverage, and full protected gate pass.
- Sync only approved runtime files.
- Do not sync tests or smoke scripts to live.
- Clear Frappe cache and website cache.
- Restart backend/queues/scheduler/frontend only if required by touched runtime files.
- Produce SHA-256 source/live hash proof for every synced runtime file.
- Run focused live W4 smoke.
- Run Sales freeze and full protected workspace gate post-live.
- Stop at the first failed gate.

Rollback expectation:

- Keep W3/W3A as the known-good Warehouse baseline.
- If W4 live validation fails, restore touched runtime files from the last accepted commit or live hash set.
- Clear caches and rerun W3A landing plus protected workspace gates after rollback.

## 16. Explicit Non-Goals

W4 does not implement:

- Receiving execution.
- Purchase Receipt creation, submission, cancellation, amendment, return, or posting.
- Stock Entry creation, submission, cancellation, amendment, or posting.
- Stock Reconciliation.
- Putaway execution.
- Serial or batch assignment.
- Quality Inspection creation, approval, rejection, or readings.
- Warehouse Quick Find/Search.
- Warehouse reports.
- Outbound fulfillment visibility.
- Internal transfer execution.
- Stock ledger reports.
- Valuation visibility.
- Item Price, Default Supplier, or Item Supplier mutation.
- Billing, payment, accounting, or Finance workflows.
- Native ERPNext form/report/list/workspace escape.
- Sales or Procurement runtime changes.

## 17. Owner Decisions Needed Before Runtime Implementation

Owner decisions required before W4 code starts:

- Confirm W4 route set: Overview update plus Inbound Receiving Queue, with or without Receiving Review detail page.
- Confirm default due horizon: recommended overdue plus next 14 days.
- Confirm whether partially received POs should appear both in the priority state and in their due-date group, or only once with a `Partially Received` badge.
- Confirm whether Quality indicators belong in W4 or should wait for a dedicated quality watch phase.
- Confirm whether inbound transfer requests are excluded from W4 and moved to W6.
- Confirm whether buyer/owner is visible to Warehouse users.
- Confirm whether target warehouse is required for rows, and what fallback copy should show when PO lines have no warehouse.
- Confirm whether Warehouse User and Warehouse Manager see the same inbound fields in W4.
- Confirm no Purchase/Sales/Finance access unless the user also has Warehouse role.
- Confirm no execution actions until a separate controlled receiving design is approved.
- Confirm W4 smoke/gate acceptance criteria before implementation begins.

## 18. Recommended Next Step

Recommended next step: owner review of this W4 inbound visibility design plan.

After owner approval, implementation should begin with the smallest useful W4 slice:

- Registry/governance entries for the inbound queue route.
- A controlled read-only inbound service adapter using Purchase Order and Purchase Order Item allowlists.
- Overview inbound summary cards and a bounded priority preview.
- Inbound Receiving Queue with grouped states, filters, and read-only `Review receiving` navigation.
- No Receiving Review detail page unless owner confirms it is needed in W4.
- Focused W4 smoke plus Sales/Procurement protected gates before commit/live alignment.

## 19. Docs-Only Closure

This W4 plan is documentation only.

It does not:

- Change runtime code.
- Change tests.
- Change smoke scripts.
- Change live files.
- Run live alignment.
- Touch Sales runtime.
- Touch Procurement runtime.
- Touch `ui_smoke/sales_final_acceptance_audit.js`.

Required validation for this docs-only phase:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
