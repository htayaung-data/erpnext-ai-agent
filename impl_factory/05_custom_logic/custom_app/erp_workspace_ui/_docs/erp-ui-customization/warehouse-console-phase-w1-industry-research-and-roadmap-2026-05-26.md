# Warehouse Console Phase W1 Industry Research And Roadmap

Date: 2026-05-26

Branch: `feature/erpnext-ui-design`

Document status: docs-only roadmap. No Warehouse Console runtime implementation starts in this phase.

## 1. Source Gate Result

Source path:

`/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`

Gate findings:

- Current branch confirmed as `feature/erpnext-ui-design`.
- `HEAD` confirmed as `c1059b1f6ba2651d8342a4822a2b9df20e9fd1c1`.
- Source and upstream were aligned at `c1059b1f6ba2651d8342a4822a2b9df20e9fd1c1`.
- Latest history includes `c1059b1 docs: close procurement final freeze`.
- `_docs/erp-ui-customization/procurement-console-final-freeze-closure-2026-05-25.md` exists.
- Working tree before this W1 work contained the known untracked `ui_smoke/sales_final_acceptance_audit.js`.
- Working tree also contained the prior Warehouse onboarding handover `_docs/erp-ui-customization/warehouse-console-onboarding-context-audit-2026-05-25.md`, which this phase explicitly depends on.

Source gate posture:

- No runtime, smoke, test, Sales, Procurement, or live files were edited for this W1 roadmap.
- The prior onboarding handover remains a pre-existing docs artifact and should be committed or explicitly accepted before a later freeze branch if the Main Agent wants a fully clean source gate.

## 2. Context Reviewed

Required project documents reviewed:

- `_docs/erp-ui-customization/warehouse-console-onboarding-context-audit-2026-05-25.md`
- `_docs/erp-ui-customization/frozen-workspace-protection-package-standard-v1.md`
- `_docs/erp-ui-customization/shared-core-workspace-adapter-contract-v2.md`
- `_docs/erp-ui-customization/native-exception-policy-v1.md`
- `_docs/erp-ui-customization/shared-component-and-implementation-golden-rule-standard-v1.md`
- `_docs/erp-ui-customization/enterprise-shared-ui-component-standard-v1.md`
- `_docs/erp-ui-customization/enterprise-shared-ui-component-implementation-contract-v1.md`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/workspace_registry.py`
- `_docs/erp-ui-customization/sales-console-final-freeze-2026-05-03.md`
- `_docs/erp-ui-customization/sales-console-frozen-protection-package-2026-05-09.md`
- `_docs/erp-ui-customization/procurement-console-final-freeze-closure-2026-05-25.md`
- `_docs/erp-ui-customization/procurement-console-phase7l4-owner-facing-copy-search-polish-baseline-2026-05-25.md`

Installed ERPNext/Frappe source reviewed from the running project image:

- Image: `ghcr.io/htayaung-data/erpnext-factory:erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0`
- Source root: `/home/frappe/frappe-bench/apps/erpnext/erpnext`
- Stock doctypes, controllers, reports, and JSON metadata were inspected before using external documentation.

Official product documentation referenced:

- ERPNext Stock Entry: https://docs.frappe.io/erpnext/user/manual/en/stock-entry
- ERPNext Stock Transactions: https://docs.frappe.io/erpnext/user/manual/en/stock-transactions
- ERPNext Purchase Receipt: https://docs.frappe.io/erpnext/purchase-receipt
- ERPNext Delivery Note: https://docs.frappe.io/erpnext/user/manual/en/delivery-note
- ERPNext Material Request: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/material-request
- ERPNext Pick List: https://docs.frappe.io/erpnext/pick-list
- ERPNext Stock Reservation: https://docs.frappe.io/erpnext/user/manual/en/stock-reservation
- ERPNext Quality Inspection: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/quality-inspection
- ERPNext Batch: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/batch
- ERPNext Serial Number: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/serial-no
- SAP Overview Inventory Processing: https://help.sap.com/docs/SAP_S4HANA_CLOUD/32da8359c8ee4e8b8e8c5e15cacba5aa/5d5159607ade4c50b19eb26c86a6bb3f.html
- SAP EWM Warehouse Request for Inbound/Outbound Delivery: https://help.sap.com/docs/SAP_EXTENDED_WAREHOUSE_MANAGEMENT/3d97bec9bf1649099384bb8167df3cf2/39cecb53ad377114e10000000a174cb4.html
- Microsoft Dynamics 365 Warehouse Management Overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-management-overview
- Microsoft Dynamics 365 Inbound Load Handling: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/inbound-load-handling
- Microsoft Dynamics 365 Outbound Load Handling: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/outbound-load-handling
- Oracle Fusion Cloud Inventory Management Work Area: https://docs.oracle.com/pls/topic/lookup?ctx=fa26b&id=s20076382
- Oracle Fusion Cloud Inventory Tasks: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/famli/overview-of-tasks-from-the-inventory-management-work-area.html
- Odoo Inventory: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory.html
- Odoo Lot Numbers: https://www.odoo.com/documentation/master/applications/inventory_and_mrp/inventory/product_management/product_tracking/lots.html
- Odoo Serial Numbers: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/product_management/product_tracking/serial_numbers.html
- NetSuite WMS Overview: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/chapter_156382517509.html
- NetSuite Bin Management: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N2270284.html
- NetSuite Lot, Serial, and Bin Numbering: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_1504285820.html

## 3. Protected Workspace Implications

Warehouse Console must be built as a new workspace through the shared core plus a Warehouse adapter. It must not copy Sales or Procurement page files as a starting point.

Required architecture posture:

- The shared core owns workspace lifecycle, duplicate render protection, route registration shape, sidebar behavior, shared search behavior, list shells, report shells, guard states, and common loading/error patterns.
- The Warehouse adapter owns Warehouse business labels, page definitions, permitted actions, route keys, data payload shape, and role-specific business behavior.
- Sales Console is frozen and protected. Its route names, reports, worklists, search behavior, sidebar behavior, and business copy are not test material for Warehouse changes unless a Sales freeze gate explicitly permits it.
- Procurement Console is frozen and protected by the 2026-05-25 final freeze closure. Procurement ends before receiving, billing, payment, stock movement execution, Item Price updates, Default Supplier updates, and Item Supplier updates.
- Normal users must not be given native ERPNext route escape. Warehouse routes must be product-owned Warehouse routes.
- Shared runtime changes are high-risk because they can break Sales or Procurement. Warehouse should start by using existing shared surfaces before requesting shared runtime changes.

Notable registry observation:

- `workspace_registry.py` already contains planned Warehouse roadmap metadata.
- Procurement final docs say Procurement is frozen/protected, while the registry still labels Procurement as `phase_3`. This W1 roadmap treats the freeze documents and gates as the protection authority. Any registry metadata cleanup should be owner-approved and handled separately from Warehouse W1.

## 4. ERPNext Warehouse And Stock Domain Findings

The installed ERPNext/Frappe source confirms that Warehouse Console should begin as a visibility and exception workspace. Most operational documents that change stock are submittable and ledger-affecting.

| Doctype or concept | Business purpose | Owner department | Workflow stage | Read-only visibility needs | Execution risk | Dependencies | Phase fit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse | Storage location hierarchy by company, parent warehouse, rejected warehouse, and in-transit warehouse posture. | Warehouse | Foundation master data | Warehouse profile, hierarchy, stock posture, rejected or in-transit flags. | Medium if edited, because stock location setup affects all movements. | Sales, Procurement, Manufacturing, Finance inventory valuation. | First phase visibility, future admin-only editing outside Warehouse Console. |
| Item | Defines stock item, stock UOM, serial/batch flags, quality inspection flags, reorder rows, item defaults, supplier links, and projected quantity. | Item/Inventory ownership, with Procurement and Sales dependencies | Foundation master data | Stock posture, UOM, tracking flags, quality requirements, reorder context, active warehouses. | High if edited because it affects selling, buying, valuation, and stock behavior. | Sales, Procurement, Warehouse, Finance, Manufacturing, Quality. | First phase visibility; no item master updates. |
| Item Reorder | Per item and warehouse reorder thresholds and material request type. | Warehouse with Procurement planning input | Replenishment planning | Reorder level, reorder quantity, warehouse group, replenishment type. | Medium to high if edited because it can trigger wrong buying or transfers. | Procurement, Warehouse, Manufacturing. | Low Stock/Reorder Watch visibility; updates later only after owner approval. |
| Item Warehouse Details | Not available in the inspected installed source. | Not applicable | Not applicable | Do not design first phase around it. | Not applicable | Not applicable | Out of first scope unless a later installed app provides it. |
| Bin | Per item and warehouse stock summary: actual, reserved, ordered, requested, planned, projected, reserved for production/subcontracting, stock value, stock UOM. | Warehouse | Daily stock posture | Primary source for availability, low stock, reservations, ordered/requested quantities, projected quantity. | Low for read-only; high if changed directly. | Sales reservations, Purchase orders, Material Requests, Manufacturing, Subcontracting, Finance valuation. | First phase read-only source. |
| Projected Qty | ERPNext stock planning posture calculated from actual, incoming, requested/planned, and reserved quantities. | Warehouse and planning | Availability planning | Show alongside actual and reserved stock to avoid false confidence. | High if recalculated or overridden outside ERPNext logic. | Procurement, Sales, Manufacturing. | First phase visibility. |
| Actual Qty | Physical or ledger-backed on-hand quantity by item and warehouse. | Warehouse | Stock availability | Core KPI, item detail, warehouse detail, Stock Balance. | High if changed except through stock documents. | Finance valuation, Sales fulfillment, Procurement receipt. | First phase visibility. |
| Reserved Qty | Quantity held for demand, including sales-side reservations. | Warehouse/Sales handoff | Allocation and fulfillment | Show why stock is not free to use. | High if unreserved improperly. | Sales, Pick List, Stock Reservation Entry. | First phase visibility. |
| Ordered Qty | Incoming purchase quantity represented in Bin. | Procurement upstream, Warehouse downstream | Supply expected | Show what is expected but not yet received. | Medium if interpreted as available stock. | Procurement POs, receiving. | First phase visibility. |
| Requested Qty / Indented Qty | Requested material quantity represented through Material Requests. | Warehouse, Procurement, Manufacturing | Demand or transfer request | Show transfer/issue/receipt requests waiting for action. | Medium if converted incorrectly. | Material Request, Procurement, Manufacturing. | First phase visibility. |
| Stock Ledger Entry | Immutable transaction history for item, warehouse, quantity movement, valuation rate, voucher, batch/serial, and balance after transaction. | Finance and Warehouse | Audit trail | Stock Ledger report, recent movement on object pages, issue tracing. | Very high if altered; never edited from Warehouse Console. | Every stock movement, Finance valuation. | Report first; read-only only. |
| Stock Entry | Submittable document for material issue, receipt, transfer, manufacture, repack, subcontracting, customer receipt, and related stock movements. | Warehouse, Manufacturing, Subcontracting depending purpose | Execution | View transfer/movement posture and linked items. | Very high: submit/cancel/posting changes stock ledger and value. | Finance, Manufacturing, Procurement, Sales. | Future visibility first; execution deferred. |
| Stock Reconciliation | Submittable stock correction and opening stock process. | Warehouse Manager with Finance control | Inventory accuracy correction | Watch pending/draft reconciliations and completed adjustments. | Very high: changes quantities and valuation. | Finance, Audit, Warehouse. | Future report/watch only; execution deferred. |
| Purchase Receipt | Submittable receipt of supplier items, usually against Purchase Order; updates stock and may include accepted/rejected warehouses, serial/batch, quality inspection. | Warehouse receiving, Procurement upstream | Inbound receipt | Receiving queue from ordered but not received POs, PR review, accepted/rejected quantities, supplier delivery note, QI state. | Very high: submission posts stock and affects procurement/finance handoff. | Procurement, Quality, Finance. | First inbound visibility; creation/submission later only after design. |
| Delivery Note | Submittable customer shipment document; updates stock and supports Pick List and Packing Slip relationships. | Warehouse dispatch, Sales upstream | Outbound shipment | Outbound fulfillment queue, packed/delivered posture, item availability, linked Sales Order. | Very high: submission ships stock and affects billing. | Sales, Finance, Warehouse. | Future outbound visibility; execution deferred. |
| Material Request | Submittable document for Purchase, Material Transfer, Material Issue, Manufacture, Subcontracting, Customer Provided. | Requesting department, Warehouse, Procurement, Manufacturing | Demand, transfer, issue, replenishment | Transfer/issue/receipt request queues and fulfillment status. | High: submit/stop/cancel and conversion actions can alter downstream work. | Procurement, Warehouse, Manufacturing, Sales. | First visibility for transfer queue if scope approved. |
| Pick List | Submittable picking document for Delivery, Material Transfer, and Material Transfer for Manufacture. | Warehouse | Picking and fulfillment | Pick queue, picked quantities, item locations, serial/batch requirements. | High: submitting and generating Delivery Note or Stock Entry affects fulfillment. | Sales, Material Request, Manufacturing, Stock Entry, Delivery Note. | Future visibility; no create/submit in early phases. |
| Packing Slip | Submittable package/case document linked to Delivery Note with package contents and weights. | Warehouse dispatch | Packing | Show packing state after Delivery Note exists. | Medium to high: supports shipment paperwork and quantities. | Sales, Delivery Note, logistics. | Future outbound phase. |
| Serial No | Unit-level traceability and availability status. | Warehouse/Quality | Receipt, movement, dispatch, warranty tracing | Serial availability, location, inbound/outbound history, exceptions. | High if assigned or changed incorrectly. | Item, Purchase Receipt, Stock Entry, Delivery Note, Quality. | Serial/Batch Watch visibility. |
| Batch No | Lot-level traceability with expiry and movement across warehouses. | Warehouse/Quality | Receipt, movement, dispatch, recall tracing | Batch availability, expiry, warehouse posture, movement history. | High if assignment or expiry handling is wrong. | Item, Purchase Receipt, Delivery Note, Stock Entry, Quality. | Serial/Batch Watch visibility. |
| Serial and Batch Bundle | ERPNext v15+ bundle for serial/batch movement detail. | Warehouse | Transaction detail | Trace specific serial/batch allocation on stock documents. | High if changed. | Stock Ledger Entry, stock documents. | Future detail tab/report support. |
| Quality Inspection | Submittable inspection record for incoming, outgoing, or in-process goods. | Quality | Inspection hold or release | Quality hold queue, items requiring inspection, accepted/rejected status. | High if Warehouse overrides quality decision. | Quality, Procurement, Sales, Warehouse. | First visibility if data exists; execution owned by Quality. |
| Stock Reservation Entry | Submittable reservation against demand; status includes Draft, Reserved, Delivered, Cancelled, Closed. | Sales/Warehouse allocation | Reservation and fulfillment | Reserved stock visibility and allocation pressure. | High: reserve/unreserve affects fulfillment promises. | Sales Order, Pick List, Warehouse. | Visibility only; execution deferred. |
| UOM / Stock UOM | Standard unit used for stock movement and conversion. | Item/Inventory setup | Master data and transaction display | Show quantities in stock UOM; expose conversion context where needed. | Medium if edited; confusion can cause picking/receiving errors. | Item, Purchasing, Sales, Warehouse. | First phase display standard. |
| Putaway Rule | Rule for suggested warehouse location/capacity/priority during receipt or stock entry. | Warehouse | Putaway planning | Show whether putaway logic exists for incoming items. | Medium if edited; wrong rule misroutes stock. | Purchase Receipt, Stock Entry, Warehouse. | Future visibility; execution deferred. |
| Work Order and subcontracting | Manufacturing and subcontracting movement integration. | Manufacturing/Subcontracting | Future integration | Show only where stock movement queues need future handoff context. | High. | Manufacturing, Procurement, Warehouse. | Future integration only. |

Important first-phase data rule:

- `Bin` plus productized stock reports are the safest first sources for Warehouse Overview and item/warehouse stock posture.
- `Stock Ledger Entry` is appropriate for read-only movement history.
- Submittable documents such as `Purchase Receipt`, `Delivery Note`, `Stock Entry`, `Stock Reconciliation`, `Material Request`, `Pick List`, `Packing Slip`, and `Stock Reservation Entry` require protection against submit, cancel, amend, close, post, reserve, unreserve, receive, ship, and reconcile actions until a later governance design is approved.

## 5. Industry ERP/WMS Patterns

The external ERP/WMS review supports a Warehouse Console organized around operating lanes, exception queues, and role-gated execution.

### SAP

SAP Fiori Inventory Processing uses an overview page with cards that surface relevant work, overdue materials, goods movement analysis, outbound deliveries, and throughput. SAP EWM uses inbound and outbound delivery requests as warehouse worklists and generates warehouse tasks for putaway and picking.

Warehouse Console implication:

- Use compact overview cards and exception-ranked lists.
- Treat inbound receiving and outbound picking/dispatch as separate lanes.
- Avoid exposing posting actions until the Warehouse task model is explicitly designed.

### Microsoft Dynamics 365

Dynamics 365 Warehouse Management separates inbound, outbound, internal movement, reservations, quality, transfer, manufacturing, and transportation integration. It emphasizes source documents, warehouse work, location directives, putaway, picking, packing, shipping, serial/batch support, and mobile execution.

Warehouse Console implication:

- First IA should separate inbound work, outbound work, internal movement, stock health, and exceptions.
- Read-only Warehouse should expose work pressure before it exposes work execution.
- Mobile/scanner execution is a separate future design, not part of early desktop console visibility.

### Oracle Fusion Cloud Inventory

Oracle Inventory Management presents an Inventory Management work area with task groups for Inventory, Counts, Shipments, Picks, and Receipts. It also shows high-level operation details through infolets and gates page access by licensed products, privileges, and roles.

Warehouse Console implication:

- Use a work-area model: Overview first, then task-specific queues.
- Separate inventory accuracy/counting from fulfillment and receiving.
- Role access must determine which pages and reports appear.

### Odoo

Odoo Inventory organizes warehouse work around Receipts, Delivery Orders, Internal Transfers, Reordering Rules, Lots/Serial Numbers, and quality-related routes. Lot and serial assignment is explicitly tied to receipts and deliveries, with validation errors when required tracking is missing.

Warehouse Console implication:

- Serial and batch issues should appear as exceptions, not hidden fields.
- Receiving and delivery reviews need item-level tracking status before any later submit action is considered.
- Reordering and internal transfer visibility are first-class warehouse concerns.

### NetSuite

NetSuite WMS focuses on receiving, storing, picking, shipping, bins, lot/serial detail, available versus on-hand quantities, bin putaway, picking tickets, and cycle counts.

Warehouse Console implication:

- Availability must distinguish on-hand from available and reserved.
- Warehouse Detail should eventually support bin/location posture if the ERPNext installation later gains finer bin-location modeling.
- Cycle counts and stock reconciliation should remain manager-controlled and audit-heavy.

### Cross-System Conclusions

Standard operating lanes:

- Inbound receiving and putaway.
- Outbound picking, packing, dispatch, and shipment confirmation.
- Internal movement and transfer.
- Inventory accuracy, counting, and reconciliation.
- Stock health, low stock, reorder, and availability.
- Quality, serial, batch, and reservation exceptions.

Standard queues:

- Expected receipts.
- Receipts needing inspection or putaway.
- Sales/dispatch demand needing pick.
- Picked but not shipped.
- Internal transfer requests.
- Low stock and projected shortage.
- Negative stock or stock mismatch.
- Serial/batch missing, expired, blocked, or mismatched.
- Quality hold.
- Reserved stock pressure.
- Pending inventory transactions or reconciliation review.

Standard KPIs:

- On-hand stock value and count of stocked items.
- Items below reorder level.
- Receiving due today and overdue.
- Outbound orders due today and overdue.
- Pick backlog and dispatch backlog.
- Internal transfer backlog.
- Quality holds.
- Serial/batch exceptions.
- Negative stock or projected shortage count.
- Movement volume by day or week.

Read-only first:

- Stock posture, item/warehouse availability, receiving due, outbound due, movement history, quality hold, serial/batch exceptions, and reports.

Execution later:

- Receiving, putaway, picking confirmation, packing, dispatch, stock transfer, stock reconciliation, reservation changes, serial/batch assignment, quality disposition, and ledger-impacting stock actions.

## 6. Warehouse Ownership Boundaries

Warehouse owns:

- Stock visibility.
- Warehouse-level item availability.
- Inbound receiving visibility.
- Outbound pick, pack, and dispatch visibility.
- Internal movement visibility.
- Transfer queue visibility.
- Stock ledger visibility.
- Low stock and reorder visibility.
- Serial and batch exception visibility.
- Quality hold visibility where it affects warehouse work.
- Warehouse operational exception queues.
- Warehouse reports.

Warehouse does not own:

- Supplier sourcing.
- RFQ and Supplier Quotation.
- Purchase Order creation or commercial ownership.
- Supplier pricing.
- Item Price.
- Default Supplier.
- Item Supplier updates.
- Customer quotation or order commercial approval.
- Invoicing.
- Payment.
- Accounting entries.
- HR or admin.
- AI intake.
- Native ERPNext route escape for normal users.

Cross-workspace handoff boundaries:

- Procurement owns supplier/commercial buying work through Purchase Order follow-up and stops before receiving execution.
- Warehouse owns visibility into expected receiving and later may own controlled receiving execution after a separate design.
- Sales owns customer commercial flow and order promise; Warehouse owns visibility into pick/dispatch execution once fulfillment data exists.
- Finance owns billing, payment, accounting, valuation controls, and posting review.
- Quality owns inspection decisions; Warehouse may show quality hold and action readiness without replacing Quality.
- Manufacturing and subcontracting are future integrations only.

## 7. Initial Role Model

| Role | Overview visibility | Page access | Report access | Future action candidates | Forbidden actions | Native route posture | Approval before execution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse Manager | Full warehouse operational overview, exceptions, inbound, outbound, transfers, stock health, quality holds. | All Warehouse pages. | All Warehouse reports, subject to Finance-sensitive valuation policy. | Approve controlled receiving, transfer execution, reconciliation review, count review, exception assignment. | Supplier pricing, PO commercial approval, invoicing, payment, accounting, Sales commercial approval, Item Price, Default Supplier, Item Supplier. | Product-owned Warehouse routes only; native route access only through admin exception policy. | Required for all stock-affecting actions until a later execution design is approved. |
| Warehouse User / Stock User | Daily work queues, assigned receiving, picking, internal movement, item/warehouse stock lookup. | Overview, receiving queue, outbound queue, transfer queue, item stock detail, warehouse detail, read-only reviews. | Stock Balance, Stock Ledger with operational filters, movement history, serial/batch watch. | Record receipt quantities, confirm pick, scan serial/batch, request transfer, update pack details only after explicit execution design. | Submit/cancel/amend, reconciliation posting, pricing, supplier/customer commercial work, finance work, master data updates. | Product-owned Warehouse routes only. | Manager approval or configured role gate required for every stock posting action. |
| Purchase Manager read-only integration | Expected receiving status for POs and supplier delivery posture. | Inbound Receiving Queue, Receiving Review, Item Stock Detail read-only where tied to buying. | Receiving performance, Stock Balance read-only if owner approves. | None in Warehouse; Procurement remains commercial owner. | Receive/submit Purchase Receipt, stock transfer, Item Price, Default Supplier, Item Supplier. | Procurement and Warehouse product routes only; no native escape. | Not authorized for Warehouse stock posting by default. |
| Sales Manager read-only integration | Fulfillment status, dispatch risk, available stock posture for customer promises. | Outbound Fulfillment Queue, Delivery/Pick Review, Item Stock Detail read-only. | Stock Balance or availability reports if owner approves. | None in Warehouse; Sales remains commercial owner. | Delivery Note submission, pick confirmation, stock transfer, pricing/accounting changes. | Sales and Warehouse product routes only; no native escape. | Not authorized for Warehouse stock posting by default. |
| Finance read-only visibility | Stock movement and valuation-sensitive history where needed. | Stock Ledger, Stock Balance, movement history, reconciliation watch. | Full ledger/balance/valuation reports subject to Finance role. | Review controls for reconciliation and valuation-impacting changes in a later design. | Warehouse receiving/picking execution unless separately assigned. | Product-owned routes; finance-native routes governed by Finance workspace later. | Finance approval required before stock reconciliation or valuation-impacting workflows. |
| System Manager/Admin exception access | Diagnostic visibility for support and governance. | Admin exception access only. | All, as permitted by existing system role. | Emergency correction through native ERPNext only under admin policy. | Normal-user workflow shortcuts and unreviewed shared runtime changes. | Native access allowed only under admin/system exception policy. | Manual approval and audit record required for stock-affecting exception work. |

Role principle:

- Early Warehouse phases should hide inactive actions rather than show attractive buttons that cannot be used.
- If a future page must show an inactive action, the label should be business-facing, for example `Action not active yet`, and should not reveal implementation vocabulary.

## 8. Information Architecture

Initial Warehouse Console route namespace should use Warehouse-owned names only. Suggested route keys are conceptual until W2 route/action inventory approves them.

| Page | User purpose | Target user | Data sources | Likely route | Read-only first behavior | Future action behavior | Owner department | Dependency | UI pattern | Risk | First implementation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Warehouse Overview | See today's warehouse posture and work needing attention. | Warehouse Manager, Warehouse User | Bin, Warehouse, Item, Purchase Order/Purchase Receipt status, Delivery Note/Pick List status, Material Request, Quality Inspection, Stock Reservation Entry. | `/desk/warehouse-console` | KPI header, compact exception lanes, drilldowns to queues/reports. | Later launch receiving/pick/transfer actions through protected flows. | Warehouse | Procurement, Sales, Quality, Finance. | Console overview with bounded sections. | Medium | Yes, after W2, with safe data only. |
| Inbound Receiving Queue | See expected and overdue inbound work. | Warehouse Manager, Warehouse User, Purchase Manager read-only | Purchase Order, Purchase Receipt, Purchase Receipt Item, Item, Warehouse, Quality Inspection. | `/desk/warehouse-console-worklist/inbound-receiving` | List due receipts, PO links as Warehouse reviews, status, supplier, expected qty, warehouse, inspection need. | Create/review Purchase Receipt only after governance design. | Warehouse receiving | Procurement upstream, Quality downstream, Finance later. | Shared worklist shell. | High | W4. |
| Purchase Receipt / Receiving Review | Review a receiving object without posting stock. | Warehouse Manager, Warehouse User, Purchase Manager read-only | Purchase Receipt, Purchase Receipt Item, Purchase Order, Item, Warehouse, Serial/Batch, Quality Inspection. | `/desk/warehouse-console-receiving/<id>` | Summary, lines, accepted/rejected, inspection, serial/batch readiness, recent ledger after submit. | Controlled receive, putaway, serial/batch assignment later. | Warehouse receiving | Procurement, Quality, Finance. | Object profile with tabs. | Very high | W4 visibility only. |
| Outbound Fulfillment Queue | See pick, pack, and dispatch work tied to customer demand. | Warehouse Manager, Warehouse User, Sales Manager read-only | Sales Order, Pick List, Delivery Note, Packing Slip, Stock Reservation Entry, Bin. | `/desk/warehouse-console-worklist/outbound-fulfillment` | Show due dispatch, available/reserved posture, pick state, packing state. | Pick confirmation, pack, dispatch later. | Warehouse dispatch | Sales upstream, Finance billing downstream. | Shared worklist shell. | High | W7. |
| Delivery / Pick / Dispatch Review | Review fulfillment readiness and exceptions. | Warehouse Manager, Warehouse User, Sales Manager read-only | Pick List, Delivery Note, Packing Slip, Sales Order, Serial/Batch, Bin. | `/desk/warehouse-console-fulfillment/<id>` | Header, items, reservations, pick status, serial/batch needs, package state. | Confirm pick, create Delivery Note, packing slip, shipment confirmation later. | Warehouse dispatch | Sales, Finance, Quality. | Object profile with tabs. | Very high | W7 visibility only. |
| Internal Transfer Queue | See requested or pending warehouse-to-warehouse movements. | Warehouse Manager, Warehouse User | Material Request, Stock Entry, Pick List, Warehouse, Bin. | `/desk/warehouse-console-worklist/internal-transfers` | Show transfer requests, source/target, available stock, status. | Create/submit Stock Entry transfer later. | Warehouse | Manufacturing/Procurement if request source. | Shared worklist shell. | High | W6. |
| Stock Movement Review | Review a movement or transfer without posting. | Warehouse Manager, Warehouse User | Stock Entry, Material Request, Pick List, Stock Ledger Entry. | `/desk/warehouse-console-movement/<id>` | Summary, source/target, line quantities, linked request, recent ledger. | Controlled transfer execution later. | Warehouse | Finance, Manufacturing. | Object profile with tabs. | Very high | W6 visibility only. |
| Item Stock Detail | Understand one item's availability across warehouses. | Warehouse Manager, Warehouse User, Sales/Purchase read-only | Item, Bin, Item Reorder, Stock Ledger Entry, Serial/Batch, Stock Reservation Entry. | `/desk/warehouse-console-item/<item-code>` | Summary, availability by warehouse, reservations, incoming/requested, reorder, recent movements. | Request transfer or replenishment later. | Warehouse | Procurement, Sales, Manufacturing. | Object profile with tabs. | Medium | W5. |
| Warehouse Detail | Understand one warehouse's stock, exceptions, and movement. | Warehouse Manager, Warehouse User | Warehouse, Bin, Stock Ledger Entry, Purchase Receipt, Delivery Note, Material Request, Quality Inspection. | `/desk/warehouse-console-warehouse/<warehouse>` | Summary, stock health, top items, inbound/outbound, recent movements. | Capacity/putaway controls later if data supports them. | Warehouse | Finance valuation, Quality, Sales, Procurement. | Object profile with tabs. | Medium | W5. |
| Low Stock / Reorder Watch | See shortages and reorder pressure. | Warehouse Manager, Purchase Manager read-only | Bin, Item Reorder, Material Request, Purchase Order, Item. | `/desk/warehouse-console-worklist/low-stock` | Items below reorder or projected shortage, incoming and requested posture. | Create replenishment request later only after Procurement handoff design. | Warehouse planning | Procurement. | Shared worklist shell. | Medium | W3 or W5 if data is clean. |
| Stock Ledger | Trace item/warehouse movement history. | Warehouse Manager, Warehouse User, Finance | ERPNext Stock Ledger report / Stock Ledger Entry. | `/desk/warehouse-console-report/stock-ledger` | Report filters, read-only rows, voucher shown as Warehouse review where available. | No execution. | Warehouse/Finance | Finance valuation. | Shared report shell. | Medium | W8. |
| Stock Balance | See current stock by item and warehouse. | Warehouse Manager, Warehouse User, Finance | ERPNext Stock Balance report / Bin / Stock Ledger Entry. | `/desk/warehouse-console-report/stock-balance` | Report filters by company, warehouse, item group, item. | No execution. | Warehouse/Finance | Finance valuation. | Shared report shell. | Medium | W8, maybe W3 summary source. |
| Serial / Batch Watch | See tracking exceptions and expiring/blocked tracked stock. | Warehouse Manager, Warehouse User, Quality | Serial No, Batch, Serial and Batch Bundle, Stock Ledger Entry, Item. | `/desk/warehouse-console-worklist/serial-batch-watch` | Missing, expiring, unavailable, location mismatch, required tracking warnings. | Assign serial/batch later only in controlled receiving/picking flows. | Warehouse/Quality | Quality, Sales, Procurement. | Shared worklist plus object tabs. | High | W7 or W8 visibility. |
| Quality Hold / Inspection Watch | See warehouse work blocked by inspection. | Warehouse Manager, Warehouse User, Quality | Quality Inspection, Purchase Receipt, Delivery Note, Stock Entry, Item. | `/desk/warehouse-console-worklist/quality-hold` | Items needing inspection or rejected/held. | Quality decision stays in Quality workspace or approved role-gated flow. | Quality with Warehouse visibility | Procurement, Sales, Warehouse. | Shared worklist shell. | High | W4 or W7, if useful data exists. |
| Warehouse Reports Index | Give users a stable report entry point. | Warehouse Manager, Warehouse User, Finance | Report registry and Warehouse report definitions. | `/desk/warehouse-console-reports` | Cards for stock and movement reports. | No execution. | Warehouse | Finance where valuation-sensitive. | Compact report index. | Low | W8. |
| Warehouse Quick Find | Search items, warehouses, receiving, dispatch, transfers, reports after IA is stable. | Warehouse Manager, Warehouse User | Warehouse adapter search providers. | Shared console search | Preview before opening; only Warehouse product routes. | No execution from search results. | Warehouse | Shared search core. | Search modal with grouped previews. | Medium | W9 only after core IA. |

## 9. Warehouse Overview Design

The Overview should be compact, exception-oriented, and useful on first render.

Recommended first viewport:

- Header: selected company/warehouse scope, last refreshed time, and route-safe primary drilldowns.
- KPI strip: items in stock, low stock items, receiving due, outbound due, transfer backlog, quality/serial/batch issues.
- Today's operational exceptions: overdue receiving, dispatch risk, negative/projected-short items, quality hold, serial/batch issues.
- Work lanes: Inbound, Outbound, Internal Movement, Stock Health.
- Right-side or lower compact cards: Stock Balance, Stock Ledger, Low Stock Watch, Serial/Batch Watch.

Recommended section behavior:

- Each lane should show a bounded set of recent or urgent rows, usually 5 to 8.
- Each row should have a clear business label, status, quantity, warehouse, due date, and an `Open` or `Review` route-owned action.
- Empty states should be useful: `No receiving due today`, `No stock issues needing attention`, `No quality holds`.
- Avoid showing every possible queue on the first screen.
- Avoid raw diagnostic dumps, long tables, and governance language.

Example Overview sections:

| Section | Purpose | First data source | Notes |
| --- | --- | --- | --- |
| KPI header | Fast operational readout. | Bin and simple document counts. | Use small, stable cards; do not make this a marketing hero. |
| Needs attention | Today's true exceptions. | Due dates, projected shortage, QI, tracking exceptions. | Rank by urgency and business risk. |
| Inbound work | Expected receipts and receiving blockers. | Purchase Orders/Purchase Receipts. | Procurement handoff visible, not editable. |
| Outbound work | Pick/dispatch pressure. | Pick List, Delivery Note, Sales Order links. | Sales handoff visible, not editable. |
| Internal movement | Transfer and issue requests. | Material Request, Stock Entry. | Keep transfer execution inactive. |
| Stock health | Low stock, negative/projected shortage, reserved pressure. | Bin, Item Reorder, Stock Reservation Entry. | Make actual/reserved/projected clear. |
| Tracking and quality | Serial/batch and inspection blockers. | Serial No, Batch, Quality Inspection. | Do not let Warehouse override Quality. |
| Reports | Stable report entry points. | Report definitions. | Compact cards only. |

Visible copy standards:

- Use: `Review receiving`, `Stock movement`, `Needs attention`, `Open Warehouse page`, `Read-only`, `Action not active yet`.
- Avoid in visible UI: `Productized`, `native ERP`, `governed`, `deferred`, `route only`, `mutation`, `framework`, `backend`, `frontend`, `smoke`, `test`.
- ERP terms such as `Stock Ledger`, `Stock Balance`, `Purchase Receipt`, `Delivery Note`, `Pick List`, `Serial No`, and `Batch No` are acceptable where they are also business terms used by ERPNext users.

## 10. Object Page Patterns

Object pages should follow the Procurement lesson: summary first, tabs for distinct categories, bounded recent rows, and full history through reports.

### Item Stock Detail

Purpose:

- Show whether an item can be used, where it is held, what is reserved, what is incoming, and whether it needs replenishment.

Suggested header:

- Item code/name, stock UOM, maintain-stock flag, tracking flags, quality flags, total actual, total reserved, total projected, low-stock indicator.

Suggested tabs:

- Profile: stock UOM, item group, tracking and inspection flags.
- Availability: warehouse rows with actual, reserved, ordered, requested, planned, projected.
- Reorder: reorder levels and replenishment posture.
- Reservations: stock reservations and demand links.
- Serial & Batch: tracked quantity, expiry or missing assignment signals.
- Movements: recent stock ledger rows, bounded to recent entries.
- History: report drilldowns.

### Warehouse Detail

Purpose:

- Show operational state of one warehouse.

Suggested header:

- Warehouse name, company, parent warehouse, type, rejected/in-transit indicators, stocked item count, low-stock count, exception count.

Suggested tabs:

- Profile: hierarchy and warehouse settings.
- Stock: top items, low stock, negative/projected shortage.
- Inbound: expected receipts and receiving issues.
- Outbound: pick/dispatch posture.
- Movements: recent ledger movement.
- Quality & Tracking: holds, serial/batch issues.
- Reports: Stock Balance and Stock Ledger scoped to warehouse.

### Receiving Review

Purpose:

- Let users review expected or actual receiving without creating or submitting a Purchase Receipt in early phases.

Suggested header:

- Supplier, source PO or Purchase Receipt, expected date, receiving warehouse, status, item count, inspection/tracking flags.

Suggested tabs:

- Summary: supplier, dates, warehouse, status, linked Procurement context.
- Items: ordered, received, accepted, rejected, warehouse, UOM.
- Quality: inspection requirements and status.
- Serial & Batch: tracking requirements and assignment posture.
- Activity: recent receiving events and linked document state.

### Delivery / Pick Review

Purpose:

- Let users understand fulfillment readiness and risk without shipping stock.

Suggested header:

- Customer/order reference, delivery date, warehouse, pick state, dispatch state, available/reserved gap.

Suggested tabs:

- Summary: source demand, due date, warehouse, fulfillment status.
- Items: requested, picked, packed, delivered, stock availability.
- Reservations: Stock Reservation Entry and reserved quantity posture.
- Serial & Batch: required tracked inventory and gaps.
- Packing: Packing Slip state when available.
- Activity: recent pick/delivery events.

### Stock Movement Review

Purpose:

- Let users review transfer/issue/receipt movement context without posting a Stock Entry.

Suggested header:

- Movement type, source warehouse, target warehouse, requested by, due date, status, line count.

Suggested tabs:

- Summary: source/target, purpose, status.
- Items: quantity, UOM, available stock, requested quantity.
- Request: linked Material Request or Pick List.
- Movements: related Stock Ledger rows after posting.
- Exceptions: short stock, tracking, quality, or warehouse mismatch.

## 11. Warehouse Reports

Warehouse reports should prefer existing ERPNext report logic in read-only mode where possible. New custom reports should only be added when existing reports cannot answer the business question cleanly.

| Report | Purpose | Source data | Filters | Role access | First-phase inclusion | Existing ERPNext logic |
| --- | --- | --- | --- | --- | --- | --- |
| Stock Balance | Current stock by item, warehouse, value, and quantity. | Stock Balance report, Bin, Stock Ledger Entry. | Company, warehouse, item, item group, date. | Warehouse Manager, Warehouse User, Finance. | Yes, W8; W3 can use summary data. | Yes. |
| Stock Ledger | Audit movement history by item and warehouse. | Stock Ledger report, Stock Ledger Entry. | Company, item, warehouse, date range, voucher, batch/serial. | Warehouse Manager, Warehouse User, Finance. | Yes, W8. | Yes. |
| Stock Aging | Identify old stock and aging risk. | ERPNext Stock Ageing report. | Company, warehouse, item group, item, date. | Warehouse Manager, Finance. | W8 or later. | Yes. |
| Stock Projected Qty | Compare actual, ordered, requested, reserved, planned, and projected quantities. | ERPNext Stock Projected Qty report, Bin. | Company, warehouse, item group, item. | Warehouse Manager, Warehouse User, Purchase Manager read-only. | W8 or earlier as stock health source. | Yes. |
| Batch/Serial report | Trace tracked items and exceptions. | Available Batch Report, Available Serial No, Serial and Batch Summary, Batch Item Expiry Status. | Item, warehouse, batch, serial, expiry, status. | Warehouse Manager, Warehouse User, Quality. | W8 or W7 watch. | Yes. |
| Reorder report | Show low-stock and reorder recommendations. | Item Reorder, Bin, recommended reorder report. | Company, warehouse, item group, item. | Warehouse Manager, Purchase Manager read-only. | W5/W8. | Yes, if report fits installed data. |
| Warehouse movement history | Product-facing movement history for one warehouse or item. | Stock Ledger Entry, Stock Entry, Purchase Receipt, Delivery Note. | Warehouse, item, date, movement type. | Warehouse Manager, Warehouse User, Finance. | W8 or custom later. | Partial through Stock Ledger. |
| Inbound performance | Track receiving due, overdue, and completed timing. | Purchase Order, Purchase Receipt. | Supplier, warehouse, date range, status. | Warehouse Manager, Purchase Manager read-only. | Later, after W4 data validation. | Likely custom. |
| Outbound performance | Track pick/dispatch backlog and completed delivery timing. | Sales Order, Pick List, Delivery Note, Packing Slip. | Customer, warehouse, date range, status. | Warehouse Manager, Sales Manager read-only. | Later, after W7 data validation. | Likely custom. |

Report navigation rule:

- Report rows must not open native ERPNext forms for normal users. They should open Warehouse review pages where those pages exist, or present route-safe read-only detail.

## 12. Phased Roadmap

### W1: Industry Research And Roadmap Design

Objective:

- Produce this docs-only roadmap from project contracts, installed ERPNext source, and major ERP/WMS patterns.

Included:

- Ownership boundaries, role model, information architecture, overview design, object page patterns, report plan, phased implementation plan.

Explicit exclusions:

- No runtime code.
- No Warehouse routes.
- No APIs.
- No tests or smokes.
- No Sales or Procurement changes.
- No live alignment.

Required gates:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`

Owner decisions:

- Accept Warehouse as visibility-first.
- Accept no stock execution in early phases.
- Confirm whether prior onboarding doc should be committed with W1 docs.

Risk: Low.

### W2: Warehouse Route/Action Inventory And Protection Plan

Objective:

- Convert this roadmap into a route/action contract and protection plan before code starts.

Included pages:

- Conceptual route inventory for Overview, worklists, object reviews, reports, and future search.
- Allowed actions and forbidden actions.
- Role and native route restrictions.
- Data source read-only contract.
- Smoke/gate design.

Explicit exclusions:

- No runtime implementation.
- No Warehouse registry entry unless owner explicitly makes W2 implementation-enabled.
- No stock posting actions.

Required tests/smokes:

- Docs-only validation.
- Draft Warehouse protection smoke design, not runnable code unless W3 starts.

Required gates:

- Source gate.
- Docs diff check.

Owner decisions:

- Approve route names.
- Approve role matrix.
- Approve first data sources.
- Decide whether valuation-sensitive fields are visible to Warehouse User.

Risk: Low.

### W3: Warehouse Foundation Shell And Overview Read-Only

Objective:

- Create the smallest useful Warehouse runtime surface without execution.

Included pages:

- Warehouse Overview.
- Sidebar entry.
- Safe route ownership.
- Read-only KPI header and bounded exception cards from safe stock/warehouse data.

Explicit exclusions:

- No receiving creation/submission.
- No Delivery Note creation/submission.
- No Stock Entry creation/submission.
- No Stock Reconciliation.
- No serial/batch assignment.
- No native escape.
- No broad shared runtime changes unless required and freeze-gated.

Required tests/smokes:

- Warehouse Overview role smoke.
- Native escape smoke for Warehouse normal users.
- Sales freeze protection smoke.
- Procurement protected gate.
- Performance check for first useful render and duplicate route calls.

Required gates:

- Source gate.
- Unit tests.
- Protected workspace gate after runtime changes.
- Manual owner UI review before live alignment.

Owner decisions:

- KPI definitions.
- Warehouse/user roles allowed.
- Whether low stock appears in W3 or waits for W5.

Risk: Medium.

### W4: Inbound Receiving Visibility

Objective:

- Show expected receiving and receiving blockers without creating or submitting Purchase Receipts.

Included pages:

- Inbound Receiving Queue.
- Receiving Review.
- Quality hold visibility for inbound items if data is reliable.

Explicit exclusions:

- No receive action.
- No Purchase Receipt submit/cancel/amend.
- No putaway confirmation.
- No serial/batch creation.
- No supplier pricing or Procurement ownership changes.

Required tests/smokes:

- Queue loads for Warehouse Manager/User.
- Purchase Manager read-only access if approved.
- No native PO/PR escape for normal users.
- Sales and Procurement protected gates.

Required gates:

- Unit tests.
- Warehouse smoke.
- Protected workspace gate.

Owner decisions:

- Which PO statuses count as expected receiving.
- Whether direct Purchase Receipt without PO appears in queue.
- How rejected warehouse and QI states are labeled.

Risk: High.

### W5: Item Stock And Warehouse Detail Object Pages

Objective:

- Provide object-profile detail pages for item and warehouse stock posture.

Included pages:

- Item Stock Detail.
- Warehouse Detail.
- Low Stock / Reorder Watch if owner approves data definitions.

Explicit exclusions:

- No item master updates.
- No reorder level updates.
- No transfer request creation.
- No native Item/Warehouse form escape.

Required tests/smokes:

- Object page route smoke.
- Bounded row rendering checks.
- No unbounded list smoke.
- Sales/Procurement protected gates.

Required gates:

- Unit tests.
- Protected workspace gate.
- Performance check for heavy item/warehouse data.

Owner decisions:

- Whether stock value is shown to Warehouse User.
- How to label projected, ordered, requested, and reserved quantities for business users.

Risk: Medium.

### W6: Stock Movement And Transfer Visibility

Objective:

- Show internal movement and transfer queues without posting Stock Entries.

Included pages:

- Internal Transfer Queue.
- Stock Movement Review.

Explicit exclusions:

- No Stock Entry creation/submission.
- No Material Request submit/stop/cancel.
- No transfer execution.
- No manufacturing or subcontracting execution.

Required tests/smokes:

- Queue and review route smoke.
- Forbidden action checks.
- No native escape.
- Sales/Procurement protected gates.

Required gates:

- Unit tests.
- Protected workspace gate.

Owner decisions:

- Which Material Request types belong in Warehouse.
- Whether manufacturing transfer requests are shown in first version.

Risk: High.

### W7: Outbound Fulfillment Visibility

Objective:

- Show pick, pack, and dispatch posture from Sales-side fulfillment data without shipping stock.

Included pages:

- Outbound Fulfillment Queue.
- Delivery / Pick / Dispatch Review.
- Serial / Batch Watch if tied to outbound exceptions.

Explicit exclusions:

- No Pick List submit.
- No Delivery Note creation/submission.
- No Packing Slip creation/submission.
- No shipment confirmation.
- No Sales commercial changes.
- No billing.

Required tests/smokes:

- Sales Manager read-only route if approved.
- Warehouse User route smoke.
- No Delivery Note native escape.
- Sales freeze and Procurement protected gates.

Required gates:

- Unit tests.
- Protected workspace gate.
- Performance check for pick/delivery query shape.

Owner decisions:

- Which fulfillment documents are authoritative when Sales Order, Pick List, and Delivery Note disagree.
- Whether packing is shown in W7 or later.

Risk: High.

### W8: Warehouse Reports

Objective:

- Expose Warehouse report index and read-only stock reports using existing ERPNext report logic where practical.

Included pages:

- Warehouse Reports Index.
- Stock Balance.
- Stock Ledger.
- Stock Aging.
- Stock Projected Qty.
- Batch/Serial reports.
- Reorder report.
- Movement history if needed.

Explicit exclusions:

- No row-level native form escape.
- No report-driven stock actions.
- No custom finance posting views unless Finance approves.

Required tests/smokes:

- Report route smoke.
- Filter persistence smoke.
- Role access smoke.
- Sales/Procurement protected gates.

Required gates:

- Unit tests.
- Protected workspace gate.
- Performance checks on report load.

Owner decisions:

- Which valuation fields are visible to each role.
- Which existing reports are acceptable as first Warehouse reports.

Risk: Medium.

### W9: Warehouse Quick Find/Search Integration

Objective:

- Add Warehouse search after the core IA is stable.

Included:

- Grouped previews for items, warehouses, receiving, dispatch, transfers, and reports.
- Preview before opening.
- Route-safe Warehouse targets only.

Explicit exclusions:

- No search result action execution.
- No native ERPNext result targets.
- No broad search core rewrite unless freeze-gated.

Required tests/smokes:

- Search modal smoke.
- Preview route smoke.
- No native escape smoke.
- Sales/Procurement protected gates.

Required gates:

- Unit tests.
- Protected workspace gate.
- Duplicate route call check.

Owner decisions:

- Search result ranking.
- Which document identifiers are safe for each role.

Risk: Medium.

### W10: Performance And Freeze Audit

Objective:

- Stabilize Warehouse Console enough to freeze its read-only scope.

Included:

- Full route audit.
- Role audit.
- Native escape audit.
- Performance audit.
- Cross-workspace regression audit.
- Freeze handover.

Explicit exclusions:

- No new functional scope.
- No execution actions.

Required tests/smokes:

- Warehouse protected gate.
- Sales freeze protection smoke.
- Procurement protected gate.
- Relevant unit tests.
- Route probe for Warehouse roles.
- Performance and duplicate request audit.

Required gates:

- Source gate.
- Full validation.
- Manual owner UI review.
- Freeze docs.

Owner decisions:

- Confirm Warehouse read-only baseline accepted.
- Decide next execution design sequence.

Risk: Medium.

### Future: Controlled Execution Design

Objective:

- Design stock-affecting execution only after Warehouse read-only scope is protected.

Potential future actions:

- Create/submit Purchase Receipt.
- Create/submit Stock Entry for transfer.
- Create/submit Delivery Note.
- Stock Reconciliation review and posting.
- Serial/batch assignment.
- Pick/pack/ship execution.
- Putaway confirmation.

Non-negotiable prerequisites:

- Separate governance design.
- Role and approval matrix.
- Audit trail.
- Reversal/cancel/amend policy.
- Finance approval for valuation-affecting workflows.
- Quality approval for inspection decisions.
- Dedicated tests and protected gates.
- Owner manual review.

Risk: Very high.

## 13. First Implementation Recommendation

Recommended next step after W1:

- Do W2 first as docs-only route/action inventory and protection planning.

Recommended first runtime implementation after W2 approval:

- W3: a very small Warehouse foundation and read-only Overview.

W3 should include:

- Warehouse workspace registry entry and route ownership.
- Sidebar shell entry using shared console/sidebar runtime.
- Warehouse Overview with safe read-only KPIs and bounded exception cards from `Bin`, `Warehouse`, `Item`, and carefully selected document counts.
- No native ERPNext route escape.
- No stock posting.
- No receiving, delivery, transfer, reconciliation, serial/batch assignment, submit, cancel, amend, close, reserve, unreserve, send, bill, or pay actions.
- Focused Warehouse smoke.
- Sales and Procurement protected gates after runtime changes.

Reason:

- This proves the new workspace can exist safely inside the protected multi-workspace architecture before attaching high-risk warehouse documents.
- It gives users useful stock posture without changing ledger-affecting workflows.
- It avoids breaking Procurement's completed boundary: Procurement can continue to stop before receiving while Warehouse begins by showing receiving posture only.

## 14. Security And Stability Requirements

Warehouse implementation must enforce these controls from the first runtime phase:

- No native ERPNext escape for normal users.
- No write APIs in early phases.
- No submit, cancel, amend, close, post, receive, ship, reconcile, reserve, unreserve, approve, reject, bill, pay, send, or pricing actions.
- Role-safe data access for every page and report.
- No Sales or Procurement route, copy, search, sidebar, or report regression.
- No broad shared runtime changes without running Sales and Procurement protection gates.
- No live alignment until owner review and source/live hash proof are prepared.
- Performance gate for first useful render.
- Duplicate route/API call checks before freeze.
- Bounded lists on overview and object pages.
- Full-history access through reports, not unbounded page sections.
- Route-owned Warehouse review pages instead of native form links.

## 15. Owner Decisions Needed

Before W2 closes:

- Confirm Warehouse is visibility-first through W10.
- Approve conceptual route names.
- Approve role matrix and cross-workspace read-only access for Purchase Manager, Sales Manager, and Finance.
- Decide whether Warehouse User can see stock valuation fields.
- Decide how to label projected, reserved, ordered, and requested quantities in owner-facing language.
- Confirm whether inbound receiving queue is based only on Purchase Orders or also direct Purchase Receipts.
- Confirm whether Quality Inspection appears as a Warehouse watch surface in W4 or waits until later.
- Confirm whether outbound fulfillment visibility begins with Pick List, Delivery Note, Sales Order links, or all three.
- Confirm whether manufacturing/subcontracting movements are hidden until a future manufacturing integration.
- Confirm whether the prior onboarding handover doc should be committed with the W1 roadmap.

Before any execution phase:

- Approve stock posting workflow ownership.
- Approve reversal/cancel/amend policy.
- Approve manager approval requirements.
- Approve Finance controls for valuation-impacting changes.
- Approve Quality controls for inspection decisions.
- Approve audit and evidence requirements.

## 16. Non-Goals And Forbidden Actions

W1 non-goals:

- No runtime implementation.
- No Warehouse routes.
- No APIs.
- No buttons.
- No doctypes.
- No UI components.
- No tests or smoke scripts.
- No live alignment.

Early Warehouse forbidden actions:

- Submit.
- Cancel.
- Amend.
- Close or reopen stock documents.
- Receive.
- Ship.
- Create Delivery Note.
- Create Purchase Receipt.
- Create Stock Entry.
- Create Stock Reconciliation.
- Post stock ledger movement.
- Change Item Price.
- Change Default Supplier.
- Change Item Supplier.
- Change supplier pricing.
- Create or approve RFQ/Supplier Quotation/Purchase Order commercial terms.
- Create or approve customer commercial documents.
- Invoice.
- Pay.
- Send supplier/customer communications.
- Override Quality decision.
- Reserve or unreserve stock.
- Assign serial/batch numbers outside an approved execution flow.
- Expose native ERPNext routes for normal users.

## 17. Validation Plan For This Docs-Only Phase

Required validation:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`

Not required for W1:

- Live alignment.
- Protected workspace gate.
- Playwright gate.

Reason:

- W1 changes documentation only. Protected workspace gates become mandatory when runtime, smoke, test, route, shared component, Sales, Procurement, or Warehouse implementation files change.

## 18. Recommended Handover

The Main Agent should treat this W1 document as the Warehouse Console design roadmap, not as permission to implement.

Recommended immediate next phase:

- W2: Warehouse route/action inventory and protection plan, docs-only.

Recommended first implementation after W2:

- W3: smallest safe Warehouse foundation shell plus read-only Overview.

Implementation must not begin until W2 resolves route names, action posture, role access, data sources, forbidden actions, and smoke/gate requirements.
