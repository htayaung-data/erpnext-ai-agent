# Warehouse Console Phase W5 Outbound Picking Visibility Design Plan

Date: 2026-05-28

Branch: `feature/erpnext-ui-design`

Status: docs-only W5 design plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, or live alignment.

Runtime baseline before W5 design:

- W3 read-only foundation: `368dc645e1ce6a6c80849c3cb211c06ade790d7a`
- W3A protected landing closure: `cca15a5fca07ad9bfc4e116101e08536880d8e62`
- W4A inbound receiving visibility protected baseline: `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca`
- W4B receiving review protected baseline: `0abed2f826b14909ec59182f126bdca5ebabf5bd`
- W4B receiving review docs closure: `f1c80fac584074f9e1d3015bf4ba45402c298f2b`

## 1. Executive Recommendation

W5 should add outbound picking visibility, not outbound execution.

Recommended W5 implementation scope after this design is approved:

- Add an outbound section to the existing Warehouse Overview.
- Add a read-only Outbound Picking Queue at `/desk/warehouse-console-worklist/outbound-picking`.
- Use submitted Sales Orders with pending delivery as the primary demand source.
- Use Pick List and Delivery Note only as bounded read-only status enrichments when readable.
- Keep Pick List creation/submission, Delivery Note creation/submission, packing, shipping, dispatch, reservation, serial/batch capture, and goods issue posting out of W5.
- Keep all commercial Sales behavior frozen. W5 must not change Sales Console runtime, sales workflows, customer communications, pricing, taxes, billing, or Sales native routes.
- Keep valuation, stock value, stock ledger, item price, and accounting data out of Warehouse W5.
- Keep Warehouse Quick Find/Search out of W5 unless separately approved and protected.

The product goal is a premium warehouse control room for pending outbound work. Warehouse users should know what is due, late, ready to pick, partially picked, or blocked by stock posture without being pushed into raw ERPNext picking or shipping transactions.

## 2. Research Basis

### 2.1 Current Local Baseline Reviewed

The current app source was reviewed before writing this plan:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- W4/W4A/W4B Warehouse docs in `_docs/erp-ui-customization/`

Current source-backed findings:

- W3/W3A owns the Warehouse landing and one managed Warehouse shell.
- W4A added inbound receiving visibility at `/desk/warehouse-console-worklist/inbound-receiving`.
- W4B added read-only receiving review at `/desk/warehouse-console-receiving/<purchase-order>`.
- `service.py` already has a placeholder `outbound_due` KPI concept, but no outbound queue or outbound product route is implemented.
- Existing Warehouse service methods deliberately gate access by Warehouse roles and return business-safe restricted/unavailable states.
- Existing Warehouse UI already protects against duplicate Warehouse shells, stale async renders, native ERP route escape, valuation exposure, Quick Find, and stock mutation.
- Existing tests protect W4B route registry, governance, read-only inbound payloads, and forbidden text/data exposure.

W5 must extend this pattern rather than creating a parallel shell, raw list page, or native ERPNext escape.

### 2.2 Official Documentation Reviewed

Official/vendor sources used:

- ERPNext Pick List: https://docs.frappe.io/erpnext/pick-list
- ERPNext Delivery Note: https://docs.frappe.io/erpnext/v13/user/manual/en/stock/delivery-note
- SAP EWM Outbound Delivery Order: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/9832125c23154a179bfa1784cdc9577a/60cbcb53ad377114e10000000a174cb4.html
- SAP EWM Picking: https://help.sap.com/docs/SAP_SUPPLY_CHAIN_MANAGEMENT/f41048b9ca054326bb9774db1d46e866/a4cecb53ad377114e10000000a174cb4.html
- Microsoft Dynamics 365 Warehouse management overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-management-overview
- Microsoft Dynamics 365 outbound load handling: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/outbound-load-handling
- Oracle Fusion SCM pick waves: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faims/pick-waves.html
- Oracle Fusion SCM pick wave release rules: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25a/faims/pick-wave-release-rules.html
- Odoo three-step delivery: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/delivery_three_steps.html
- Odoo batch picking: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/shipping_receiving/picking_methods/batch.html
- NetSuite Pick, Pack, and Ship overview: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N1229796.html
- NetSuite fulfilling orders using Pick, Pack, and Ship: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N1230473.html

Source-backed vendor patterns:

- ERPNext Pick List is an execution document that can lead to Delivery Note or Stock Entry creation after submission. W5 must not expose create/submit paths.
- ERPNext Delivery Note records customer shipment and updates inventory. W5 can use Delivery Note only as read-only status context; it must not create or submit one.
- SAP EWM separates outbound delivery orders, picking, warehouse tasks, packing, loading, and goods issue. This supports showing outbound posture without giving Warehouse users goods issue controls.
- Microsoft Dynamics 365 describes outbound warehouse processes around source documents, waves, work templates, location directives, picking, packing, and shipping. The UI should focus on queueing and workload posture first.
- Oracle pick waves batch shipment lines by demand and fulfillment criteria, then release selected lines for processing. W5 should use grouped operational lanes, not a flat sales order list.
- Odoo separates pick, pack, and ship steps in multi-step delivery flows and shows work to process on Inventory dashboard cards. This supports an overview-to-queue design.
- NetSuite separates Pick, Pack, and Ship statuses and lets users track orders through each fulfillment step. W5 should model visible states without enabling state transitions.

Design inference from research:

- A premium outbound Warehouse console starts with work visibility and exception posture, not transaction buttons.
- Sales Orders are the safest primary demand signal because they represent confirmed customer demand and can be filtered by pending delivery.
- Pick Lists and Delivery Notes are execution artifacts and should only enrich status after the queue is stable.
- Advanced batching, wave release, cluster picking, scanning, packing, dispatch, carrier labels, and shipment confirmation are later phases.

## 3. ERPNext Data Source Map

| Concept | ERPNext source | W5 use | Safe fields | Excluded fields/actions | Phase posture |
| --- | --- | --- | --- | --- | --- |
| Outbound demand | `Sales Order`, `Sales Order Item` | Primary W5 queue source | Sales Order id, customer display name, transaction date, delivery date, status, percent delivered, target warehouse if available, line count, item count, remaining quantity summary | rates, amounts, taxes, payment terms, margin, quotation links, invoice/payment state, Sales edits | Include W5A |
| Pick posture | `Pick List`, `Pick List Item` | Read-only enrichment only | pick list id, status, purpose, linked sales order, item count, picked quantity summary when readable | create, save, submit, update current stock, scan mode, reserve/unreserve, delivery/stock-entry creation | Optional enrichment only |
| Shipment/delivery posture | `Delivery Note`, `Delivery Note Item` | Read-only proof of shipped/delivered state | delivery note id, posting date, status, linked sales order, delivered quantity summary when readable | create, submit, cancel, amend, pack, ship, dispatch, tracking, print, email | Optional enrichment only |
| Stock availability context | `Bin`, `Warehouse`, `Item` | Support readiness label only | item, warehouse, stock UOM, actual quantity, reserved quantity, projected quantity, ordered quantity | stock value, valuation rate, stock ledger, stock account, inventory value | Limited indicator only |
| Transfer outbound | `Material Request`, `Stock Entry`, `Pick List` for transfer | Not primary W5 | none unless later approved | Stock Entry, transfer execution, inter-warehouse movement | Defer to W6 movement/transfer |
| Manufacturing picking | `Work Order`, `Pick List`, `Stock Entry` | Not primary W5 | none | material transfer for manufacture, production issue | Defer to manufacturing phase |
| Customer shipment communication | Delivery/Shipment/Email/Communication | Not W5 | none | email, print, send, portal, contact, customer notification | Exclude |

## 4. W5 Ownership Boundaries

Warehouse W5 owns:

- Read-only outbound picking posture for Warehouse Manager and Warehouse User / Stock User roles.
- Operational prioritization of pending customer-delivery demand after Sales has created/submitted the commercial Sales Order.
- Product-owned Warehouse route, shell, sidebar, controls, empty states, restricted states, and preview copy.
- Grouping by overdue, due today, ready to pick, partially picked, needs stock review, and expected soon when data supports those labels safely.
- Read-only summary of pick/delivery posture if Pick List or Delivery Note data is readable without side effects.

Warehouse W5 does not own:

- Sales Order creation, edit, submit, hold, close, cancellation, or amendment.
- Customer communications.
- Pricing, discount, tax, payment, billing, invoice, credit, or collection state.
- Delivery Note creation, submission, cancellation, amendment, printing, shipping, or email.
- Pick List creation, submission, update current stock, scan mode, reservation, unreservation, serial capture, or batch capture.
- Stock Entry creation or submission.
- Stock reservation, goods issue, stock ledger mutation, stock reconciliation, or valuation.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.
- Warehouse Quick Find/Search.

## 5. Proposed W5 Pages And Routes

| Route | Page title | Purpose | Target role | Source | Behavior | W5 recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/desk/warehouse-console` | Warehouse Console | Existing Overview with outbound work section | Warehouse Manager, Warehouse User / Stock User | Sales Order counts plus bounded status enrichment | Read-only summary and link to queue | Include W5A | Medium because Overview must preserve W3/W4A/W4B |
| `/desk/warehouse-console-worklist/outbound-picking` | Outbound Picking | Operational queue for pending picking demand | Warehouse Manager, Warehouse User / Stock User | Sales Order and Sales Order Item, optional Pick List/Delivery Note status | Read-only grouped queue, filters, product route links only | Include W5A | Medium due Sales freeze and stock-read boundaries |
| `/desk/warehouse-console-outbound/<sales-order>` | Outbound Review | Object review for one outbound demand record | Warehouse Manager, Warehouse User / Stock User | Sales Order, Sales Order Item, optional pick/delivery history | Read-only object page | Defer to W5B until W5A queue proves stable | Medium-high due Sales boundary and potential native escape temptation |
| `/desk/warehouse-console-worklist/outbound-waves` | Outbound Waves | Future batch/wave planning visibility | Warehouse Manager | Pick List / wave-like grouping if modeled | Read-only operational grouping | Defer | High because ERPNext does not have a direct Oracle-style wave abstraction by default |
| `/desk/warehouse-console-worklist/dispatch-ready` | Dispatch Ready | Future packed/shipping handoff visibility | Warehouse Manager | Delivery Note / shipment context | Read-only | Defer until pick queue and outbound detail are protected | High due shipping/communication scope |

Recommended W5 route set:

- Required W5A: `/desk/warehouse-console` Overview updates.
- Required W5A: `/desk/warehouse-console-worklist/outbound-picking`.
- Deferred W5B: `/desk/warehouse-console-outbound/<sales-order>`.
- Deferred later: waves, dispatch-ready, packing, shipping, carrier, labels, proof of delivery, customer pickup, transfer picking, manufacturing picking.

## 6. Proposed Overview Changes

The Warehouse Overview should become a balanced inbound/outbound command surface. W5 must not bury the working user under a data grid on the landing page.

Recommended first viewport order after W5A:

1. Existing Warehouse title/header and role-safe chips.
2. High-level W3/W4 KPIs.
3. Inbound cards and preview, already protected by W4A/W4B.
4. Outbound cards and preview.
5. Existing lower stock/movement posture sections.

Recommended outbound summary cards:

- `Picking Due Today`
- `Overdue Picking`
- `Ready to Pick`
- `Needs Stock Review`

Recommended preview behavior:

- Show up to 6 outbound records.
- Group label order: `Overdue`, `Due Today`, `Ready to Pick`, `Partially Picked`, `Needs Stock Review`, `Expected Soon`.
- Each preview row shows Sales Order id, customer, target warehouse, delivery date, item count, remaining quantity summary, and a read-only status pill.
- The only primary link is `Open outbound queue` in W5A.
- If no work exists, copy should read `No outbound picking needs attention.`

Do not show:

- Raw ERPNext Sales Order list layout.
- Customer contact, address, phone, email, portal, or communication data.
- Price, rate, discount, tax, margin, invoice, payment, credit, or valuation data.
- Buttons labeled `Pick`, `Create Pick List`, `Reserve`, `Unreserve`, `Pack`, `Ship`, `Dispatch`, `Create Delivery Note`, `Submit`, `Cancel`, `Amend`, `Post`, `Issue`, or `Reconcile`.
- Disabled fake execution actions.
- Native ERPNext form/report/list links.

## 7. Proposed Outbound Queue Behavior

The Outbound Picking Queue should answer: what demand is waiting on the warehouse, what is late, what is due now, what appears pickable, and what needs stock review before anyone attempts execution?

Default queue groups:

- `Overdue`: submitted Sales Orders with pending delivery and a delivery date before today.
- `Due Today`: submitted Sales Orders with pending delivery and a delivery date today.
- `Ready to Pick`: submitted Sales Orders with pending delivery where safe stock posture suggests enough available quantity for all or most lines.
- `Partially Picked`: Sales Orders with readable Pick List progress or partial delivery/pick posture.
- `Needs Stock Review`: pending demand where safe stock posture indicates short, unknown, mixed warehouse, or restricted item data.
- `Expected Soon`: submitted Sales Orders due within the default horizon, recommended 14 days.

Default query posture:

- Include `docstatus = 1` only.
- Include Sales Orders with `per_delivered < 100` when the field exists.
- Include statuses indicating delivery is still open, expected candidates are `To Deliver` and `To Deliver and Bill`, with a safe fallback if local status vocabulary differs.
- Exclude `Draft`, `Cancelled`, `Closed`, `Completed`, fully delivered orders, and quotation-only demand.
- Keep default row limit bounded, recommended 50.
- Sort by required/delivery date ascending, then status severity, then modified timestamp.

Filters:

- Due window: overdue, today, next 7 days, next 14 days.
- Customer display name.
- Sales Order id.
- Target warehouse.
- Picking state: overdue, due today, ready to pick, partially picked, needs stock review, expected soon.
- Item code/name only if the query remains bounded and protected.

Allowed actions:

- `Open Warehouse page`.
- `Apply filters`.
- `Reset filters`.
- `Refresh`.
- Optional W5A row affordance: `View outbound summary` only if it stays in the same queue row expansion and does not introduce a detail route.

Deferred actions:

- `Review outbound` route into `/desk/warehouse-console-outbound/<sales-order>` belongs to W5B after W5A queue is protected.
- Any create/submit/pack/ship/reserve action requires a separate owner-approved execution design and new protection gates.

## 8. Premium UI/UX Direction

W5 should not look like a basic CRUD table. The visual model should be an operations board with clear warehouse semantics.

Recommended visual language:

- Use a split command surface: left-side route sidebar already established, central board with inbound/outbound lanes, and compact summary cards.
- Use high-contrast status pills with business labels: `Late`, `Due today`, `Ready`, `Partial`, `Review stock`, `Expected`.
- Use lane headers with counts and short operational copy, not framework labels.
- Use dense row cards with enough information to work quickly, but keep row height disciplined.
- Use progressive disclosure: primary row facts visible, secondary line summary shown in a compact sub-row or hover-safe details area, no modal complexity in W5A.
- Keep typography calm and serious. Avoid playful gradients, oversized icons, or consumer-style cards.
- Use small line-level visual rhythm: date badge, warehouse chip, remaining quantity label, and status pill.
- On wide screens, show groups as stacked operational lanes. On narrower screens, collapse lanes into section cards with row stacks.
- Keep touch targets reasonable for warehouse tablet usage, but avoid mobile-only scanning patterns.

Recommended W5A queue row anatomy:

- Left: state rail color and status label.
- Main: Sales Order id and customer display name.
- Meta: delivery date, target warehouse, line count, remaining item count.
- Right: picked/delivered posture text, not an action button.
- Secondary line: top 2 item codes/names and remaining quantity summary.

Recommended empty/restricted states:

- Empty: `No outbound picking needs attention.`
- Restricted: `You do not have access to outbound picking.`
- Unavailable: `Outbound picking visibility is unavailable right now.`
- Partial data: `Some pick status details are hidden by permissions.`

Do not use developer-facing copy such as:

- `doctype`
- `method`
- `frappe.call`
- `undefined`
- raw stack traces
- raw permission exception text

## 9. Readiness Logic Recommendation

W5A can use a conservative readiness model. It should never over-promise that an order is executable.

Recommended readiness labels:

- `Ready to pick`: all visible stock-relevant lines appear available in their target warehouse using safe quantity fields.
- `Partial stock`: at least one visible line appears available and at least one appears short or unknown.
- `Needs stock review`: line warehouse, available quantity, or item stock posture cannot be determined safely.
- `Partially picked`: a readable Pick List or Delivery Note signal indicates partial progress.
- `Due soon`: not urgent but inside default horizon.

Readiness rules must be framed as guidance, not execution authorization. Copy should avoid saying `Available to ship` unless the implementation can prove all required constraints safely.

## 10. Role And Permission Model

Initial W5 access should match W4 Warehouse access:

- Warehouse Manager: can see overview outbound cards and outbound queue.
- Warehouse User / Stock User: can see overview outbound cards and outbound queue if role policy allows the current Warehouse console.
- System Manager: bypass remains administrative; W5 must not make Warehouse the default for broad admin roles.
- Sales roles: no route ownership change. Sales users continue using Sales Console; W5 must not redirect Sales users into Warehouse.
- Purchase roles: no route ownership change. Procurement users continue using Procurement Console.

If Sales Order read permission is unavailable for a Warehouse role, W5A must return a controlled restricted/unavailable state rather than falling back to native Sales screens.

## 11. Smoke And Protection Plan For W5A

Required focused source smoke after implementation:

- `test:warehouse-w5a-outbound:docker`
- Authorized users: Warehouse Manager and Warehouse User.
- Widths: 1136, 1240, 1440.
- Source override root: `ERPW_WAREHOUSE_W5A_ASSET_ROOT`.
- Artifact root: `ERPW_PLAYWRIGHT_ARTIFACT_ROOT`.

Focused W5A smoke assertions:

- Warehouse landing remains `/desk/warehouse-console`.
- Overview contains outbound cards and an outbound preview/empty state.
- `/desk/warehouse-console-worklist/outbound-picking` renders one Warehouse shell only.
- Queue route shows cards, filters, groups, rows or empty state.
- Refresh and repeated route navigation do not duplicate shells.
- Source override for Warehouse runtime is used during source smoke.
- Source override for outbound queue service is used during source smoke.
- No console errors, page errors, failed protected requests, or fallback injection.
- No native ERPNext route escape.
- No forbidden action labels.
- No valuation, stock value, rate, amount, discount, tax, payment, invoice, email, contact, portal, or AI copy.
- No Quick Find/Search behavior.
- Row text wrapping and overflow checks pass.

Required post-implementation gates before commit/live:

1. `python3 -m compileall erp_workspace_ui`
2. `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
3. `node --check` for touched runtime and smoke JS.
4. `python3 -m json.tool ui_smoke/package.json`
5. `bash -n ui_smoke/run_playwright_docker.sh`
6. `git diff --check HEAD`
7. Focused W5A source smoke.
8. Sales freeze protection gate.
9. Full protected workspace source gate.
10. Commit and push.
11. Runtime-only live alignment.
12. Focused W5A live smoke.
13. Final protected workspace live gate.

Stop at first failed protected gate and classify failure before continuing.

## 12. Implementation Sequence Recommendation

Recommended W5 sequence:

### W5A - Outbound Picking Queue Visibility

Implement only:

- Service method for outbound queue payload.
- Overview outbound cards and preview.
- `/desk/warehouse-console-worklist/outbound-picking` route support.
- Sidebar item for `Outbound Picking`.
- Registry/governance manifest entries.
- Unit/contract tests.
- Focused Playwright smoke.

Do not implement a detail page in W5A.

### W5B - Outbound Review Detail

Implement only after W5A is protected and owner approves drilldown:

- `/desk/warehouse-console-outbound/<sales-order>`.
- Read-only line posture.
- Read-only pick/delivery history where permissions allow.
- Back and Refresh only.

### W5C Or Later - Packing/Dispatch Visibility

Design separately:

- Pack queue.
- Dispatch-ready queue.
- Delivery Note status visibility.
- Carrier/shipment visibility.

This remains read-only unless owner approves execution phases.

### W6 Or Later - Movement/Transfer Visibility

Design separately:

- Internal transfer demand.
- Material Request movement watch.
- Stock Entry history.
- Transfer exception posture.

## 13. Explicit Non-Goals

W5 must not introduce:

- Pick List creation.
- Pick List submission.
- Pick List update current stock.
- Delivery Note creation.
- Delivery Note submission.
- Stock Entry creation.
- Stock Entry submission.
- Stock Reservation Entry creation, reserve, or unreserve.
- Packing, shipping, dispatch, delivery trip, proof of delivery, carrier labels, or tracking mutation.
- Serial number assignment.
- Batch assignment.
- Barcode scanning or scan-mode workflow.
- Print/email/send/customer notification/portal behavior.
- Contact/User/Communication/Email Queue behavior.
- Valuation, stock value, stock ledger value, price, rate, tax, discount, billing, invoice, margin, or payment fields.
- Native ERPNext form/report/list/workspace escape for normal Warehouse users.
- Warehouse Quick Find/Search.
- Sales Console runtime change.
- Procurement Console runtime change.
- AI behavior.

## 14. Owner Decisions Before W5A Implementation

Recommended owner decisions:

- Approve W5A as read-only outbound picking queue visibility only.
- Approve proposed route: `/desk/warehouse-console-worklist/outbound-picking`.
- Approve Sales Order as the primary outbound demand source.
- Approve Pick List and Delivery Note as optional read-only status enrichments only.
- Defer outbound detail route to W5B.
- Defer all execution actions and Quick Find/Search.

If approved, W5A can start without further manual UI check. Manual UI review should happen after focused W5A source smoke passes and before live alignment if the owner wants visual confirmation.

## 15. Recommended Next Task Prompt

Use this prompt for W5A implementation only after approving this docs-only design:

```text
Implement Warehouse Console Phase W5A outbound picking visibility from the approved W5 design.

Scope:
- Read-only outbound queue at /desk/warehouse-console-worklist/outbound-picking.
- Overview outbound summary cards and preview.
- Primary demand source: submitted Sales Orders with pending delivery.
- Optional bounded read-only Pick List / Delivery Note status enrichment only if safe.
- Warehouse Manager and Warehouse User access only through the Warehouse product surface.
- Add registry/governance entries, unit tests, focused smoke, and Docker env forwarding.

Forbidden:
- No Pick List/Delivery Note/Stock Entry creation or submission.
- No reserve/unreserve, scan, serial/batch assignment, pack, ship, dispatch, post, cancel, amend, reconcile, email, portal, Contact/User, valuation, pricing, billing, payment, native ERP escape, Quick Find/Search, Sales runtime change, or Procurement runtime change.

Validation:
- compileall, full unit tests, node checks, package JSON check, shell syntax check, git diff check, W5A focused source smoke, Sales freeze, full protected source gate, then commit/push and runtime-only live alignment followed by W5A live smoke and final protected live gate.
- Stop at first failed protected gate and classify.
```
