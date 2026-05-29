# Warehouse Console Phase W8 Movement Visibility Design Plan

Date: 2026-05-29

Branch: `feature/erpnext-ui-design`

Status: docs-only W8 design plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

Runtime baseline before W8 design:

- W3 read-only foundation: `368dc645e1ce6a6c80849c3cb211c06ade790d7a`
- W3A protected landing closure: `cca15a5fca07ad9bfc4e116101e08536880d8e62`
- W4A inbound receiving visibility: `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca`
- W4B receiving review: `0abed2f826b14909ec59182f126bdca5ebabf5bd`
- W5A/W5B outbound picking visibility and review: `724ccd2e09857c1df4fa85a7b2ec604448538e07`
- W6A stock exceptions: `982edba`
- W6B stock exception review: `edd9c7e`
- W7A stock posture review: `8ce0961`
- W7A live-data smoke compatibility: `2d66486`
- W7A baseline documentation: `32ba134`

## 1. Executive Recommendation

W8 should add read-only movement visibility, not stock movement execution.

Recommended W8 implementation scope after this design is approved:

- Add a read-only Movement Visibility worklist at `/desk/warehouse-console-worklist/movement-visibility`.
- Start with submitted Stock Entry movement records as the primary source because ERPNext explicitly uses Stock Entry to record item movement between warehouses and stock states.
- Show operational movement facts only: movement id, purpose, posting date/time, source warehouse, target warehouse, item count, quantity summary, and related custom Warehouse posture route when context is available.
- Exclude Stock Ledger native report links and direct Stock Ledger Entry exposure from W8A, even though the stock ledger is the authoritative history, because ERPNext stock ledger reports commonly carry valuation-adjacent fields.
- Exclude stock value, valuation rate, incoming/outgoing rate, amount, accounting, GL, profit, margin, landed cost, item price, transfer cost, and commercial data.
- Exclude all Stock Entry, transfer, reconciliation, receipt, issue, reservation, serial/batch, and lifecycle actions.
- Defer a detailed movement-review route until the worklist is protected and owner-approved.
- Defer transfer exception posture to W8B or W8C unless the owner explicitly approves it as a separate read-only design.

The product goal is a premium warehouse operations ledger that answers what moved, where it moved, why it moved, and which safe Warehouse posture route can explain the current stock position. It must not become an ERPNext Stock Entry list, Stock Ledger report, or transfer execution console.

## 2. Research Basis

### 2.1 Current Protected Warehouse Baseline Reviewed

Current source and protected docs were reviewed before writing this plan:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- Warehouse phase docs W3 through W7A in `_docs/erp-ui-customization/`

Current source-backed findings:

- W3/W3A established the read-only Warehouse shell, protected landing, and native escape closure.
- W4A/W4B established read-only inbound receiving posture and receiving review.
- W5A/W5B established read-only outbound picking posture and picking review.
- W6A/W6B established read-only stock exception posture and exception review.
- W7A established read-only item/warehouse stock posture review linked from stock exception context.
- Existing Warehouse service methods use Warehouse role checks, bounded payloads, unavailable/restricted states, and no mutation calls.
- Existing Warehouse UI already protects single-shell rendering, direct route refresh, stale async render guards, custom route-only drilldowns, and no Quick Find/Search behavior.
- Existing protected smokes check native escape, valuation exposure, stock lifecycle/action labels, Sales freeze, Procurement protection, and multi-user Warehouse access.

W8 must extend this established pattern instead of creating a parallel shell or raw ERPNext transaction browser.

### 2.2 Official Documentation Reviewed

Official/vendor sources used:

- ERPNext Stock Entry: https://docs.frappe.io/erpnext/user/manual/en/stock-entry
- ERPNext Stock Ledger Report: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/stock-ledger
- ERPNext Stock Transactions: https://docs.frappe.io/erpnext/user/manual/en/stock-transactions
- SAP Extended Warehouse Management overview: https://help.sap.com/docs/SAP_SUPPLY_CHAIN_MANAGEMENT/f41048b9ca054326bb9774db1d46e866/4ecb88b8b2422afee10000000a42189e.html
- Microsoft Dynamics 365 warehouse-specific inventory transactions: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-transactions
- Microsoft Dynamics 365 inventory transaction details: https://learn.microsoft.com/en-us/dynamics365/supply-chain/inventory/inventory-transactions-details
- Oracle Fusion Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/famml/inventory-management-work-area.html
- Oracle Fusion Inventory Management tasks: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/famli/overview-of-tasks-from-the-inventory-management-work-area.html
- Odoo Moves History dashboard: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/warehouses_storage/reporting/moves_history.html
- NetSuite Inventory Transfer Orders: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_N2308766.html

Source-backed vendor patterns:

- ERPNext Stock Entry is the central stock transaction document for material receipt, issue, transfer, manufacturing transfer, manufacture, repack, and consumption. That makes it the best W8A source, but also means the UI must avoid execution controls.
- ERPNext Stock Ledger Report is a detailed stock movement record. Because ledger-style reports often carry quantity-after-transaction and valuation-adjacent concepts, W8A should not expose the native report or raw stock ledger rows.
- SAP EWM emphasizes warehouse stock and movement visibility while separating monitoring from physical movement execution through warehouse tasks/orders.
- Microsoft Dynamics 365 distinguishes inventory transaction inspection from warehouse work and physical inventory movement. This supports a read-only movement worklist that avoids posting journals or transfer work.
- Oracle Fusion Inventory Management separates work-area infolets, transaction visibility, and transfer creation tasks. This supports dashboard-to-drilldown visibility while keeping transfer creation out of W8.
- Odoo exposes a Moves History dashboard for product movements, including past/current locations and movement reasons. This supports a movement-history lens rather than a generic document list.
- NetSuite distinguishes transfer orders from basic inventory transfers because transfer orders track staged movement and in-transit state. This supports deferring transfer exception posture until after the basic movement worklist is protected.

Design inference from research:

- Warehouse users need a movement timeline and exception explanation path, not a raw Stock Entry or Stock Ledger browser.
- Movement visibility must be read-only, tightly bounded, and operationally worded.
- Stock Entry can be used safely if W8A reads only submitted records, redacts value/accounting fields, blocks native route links, and never exposes document actions.
- Stock Ledger should remain excluded from W8A unless a later design proves a sanitized, non-valuation adapter is necessary and protected.
- Transfer visibility is a separate decision because transfer orders and stock transfers imply staged execution and ownership/accounting complexity in many ERP/WMS systems.

## 3. W8 Scope Decision

Recommended W8 path:

- W8A: Movement Visibility worklist.
- W8B: Optional Movement Review detail route after W8A protection.
- W8C: Optional Transfer Visibility / Transfer Exceptions after a separate owner decision.

Rejected for immediate W8A:

- Native Stock Ledger report embedding.
- Native Stock Entry form/list route.
- Stock Balance report route.
- Stock Reconciliation route.
- Transfer creation, transfer receiving, transfer issue, or transfer approval.
- Location/bin movement execution.
- Serial/batch assignment or traceability execution.
- Any commercial, accounting, or valuation display.

Reasoning:

- W7A already gives item/warehouse posture. The next useful read-only step is to explain movement history behind that posture.
- A worklist is safer than a detail route because it can use a bounded, redacted summary payload first.
- Starting with Stock Entry parent records avoids direct stock ledger valuation fields and keeps W8A aligned to ERPNext's own stock movement document model.
- Transfer exception posture should wait because transfer flows can imply source commitment, in-transit ownership, receiving state, and possible costing exposure.

## 4. Data Source Map

| Concept | ERPNext source | W8 use | Safe fields | Excluded fields/actions | Phase posture |
| --- | --- | --- | --- | --- | --- |
| Movement source | `Stock Entry` | Primary W8A worklist source | name, purpose, posting date, posting time, docstatus, from warehouse, to warehouse, item count, movement group, freshness | create, save, submit, cancel, amend, print, email, native open, valuation, accounting | Include W8A |
| Movement lines | `Stock Entry Detail` | Safe line summary only | item code, item name, stock UOM, quantity, source warehouse, target warehouse, line count | basic rate, amount, valuation rate, serial/batch mutation, expense/account fields | Include as bounded summary |
| Stock posture context | `Bin`, `Warehouse`, `Item` | Link or summarize current posture only through existing custom route | item, warehouse, operational quantities already allowed by W7A | stock value, valuation rate, stock ledger, stock account | Use existing W7A route |
| Stock ledger history | `Stock Ledger Entry` / Stock Ledger Report | Not W8A source | none in W8A | valuation rate, stock value, qty-after-transaction report surface, native report | Exclude W8A |
| Stock reconciliation | `Stock Reconciliation` | Not W8A source | none | reconciliation creation/submission, valuation correction | Exclude |
| Transfer posture | `Stock Entry` Material Transfer, future transfer source docs if available | Movement type label only in W8A | purpose label and source/target warehouses | transfer creation, transfer receipt, in-transit confirmation, transfer order behavior | Defer W8C |
| Inbound/outbound related routes | Existing Warehouse routes | Custom drilldown only | receiving review, picking review, stock posture route targets | native Purchase Receipt, Delivery Note, Sales Order, Purchase Order, Stock Entry route | Custom route only |

## 5. Proposed W8A Route

| Route | Page title | Purpose | Target role | Source | Behavior | W8 recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/desk/warehouse-console-worklist/movement-visibility` | Movement Visibility | Read-only recent stock movement board | Warehouse Manager, Warehouse User / Stock User | Submitted Stock Entry and Stock Entry Detail summary | Grouped worklist with safe filters and custom route links | Include W8A | Medium-high due stock transaction proximity |
| `/desk/warehouse-console-movement/<encoded-context>` | Movement Review | Read-only detail for one movement or item/warehouse movement context | Warehouse Manager, Warehouse User / Stock User | Stock Entry summary plus safe line facts | Object-style review page | Defer W8B | Medium-high due temptation to native document links |
| `/desk/warehouse-console-worklist/transfer-visibility` | Transfer Visibility | Read-only transfer/in-transit posture | Warehouse Manager first, Warehouse User after proof | Stock Entry transfer purpose and future transfer source context | Separate transfer queue | Defer W8C | High due transfer execution and possible cost/ownership concepts |

Required W8A route set:

- Add only `/desk/warehouse-console-worklist/movement-visibility`.
- Add overview navigation card only if the implementation can keep the first viewport clean.
- Use existing W7A `Review stock posture` custom route for item/warehouse context.
- Do not add a native Stock Entry, Stock Ledger, or Stock Balance link.

## 6. Proposed Movement Worklist Behavior

The Movement Visibility worklist should answer:

- What stock-impacting movements were posted recently?
- Which warehouse did each movement come from and go to?
- Which movement types are most active?
- Which movements explain current item/warehouse posture?
- Which records need operational review without giving users transaction controls?

Default groups:

- `Internal Transfers`: submitted Stock Entries with material transfer purpose and both source/target warehouse posture.
- `Receipts`: submitted Stock Entries that increase warehouse stock from a receipt-like purpose.
- `Issues`: submitted Stock Entries that decrease warehouse stock from an issue-like purpose.
- `Adjustments and Repack`: submitted Stock Entries for adjustment, repack, manufacture, or other stock purposes that should be visible but not executable.
- `Needs Review`: records with missing warehouse context, mixed direction, or line summary too large for concise display.

Default query posture:

- Include `docstatus = 1` only.
- Default horizon: latest 14 days or latest 50 records, whichever bounds the query more tightly.
- Sort by posting date/time descending, then modified descending.
- Require Warehouse role access.
- Apply permission-safe query fallbacks and return unavailable/restricted states instead of raw exceptions.
- Do not query native reports from the browser.
- Do not expose raw framework exceptions in visible copy.

Recommended filters:

- Movement date window: today, last 7 days, last 14 days, custom bounded range.
- Movement type: transfer, receipt, issue, adjustment/repack/other.
- Warehouse: source, target, or either.
- Item code/name only after bounded query behavior is proven.
- Direction: inbound to selected warehouse, outbound from selected warehouse, internal transfer.

Allowed visible controls:

- `Open Warehouse page`.
- `Apply filters`.
- `Reset filters`.
- `Refresh`.
- `Review stock posture` when item/warehouse context is available.

Explicitly forbidden visible controls:

- `Create Stock Entry`.
- `Submit`.
- `Cancel`.
- `Amend`.
- `Post`.
- `Transfer`.
- `Receive`.
- `Issue`.
- `Reconcile`.
- `Reserve`.
- `Unreserve`.
- `Adjust stock`.
- `Open in ERPNext`.
- `Stock Ledger`.
- `Stock Balance`.
- `Quick Find`.
- Generic `Search`.

## 7. Premium UI/UX Direction

W8 should feel like a serious operations audit board, not a back-office transaction table.

Recommended visual direction:

- Use a command-board layout: compact header, operational summary cards, movement lanes, and a disciplined row-card timeline.
- Use movement semantics in the UI: `Moved from`, `Moved to`, `Direction`, `Purpose`, `Posted`, `Line summary`, and `Current posture`.
- Use muted status color, not alarm-heavy colors, because movement history is often informational.
- Use clear movement chips: `Transfer`, `Receipt`, `Issue`, `Adjustment`, `Repack`, `Other`.
- Represent source and target warehouses as directional chips with an arrow marker in text, for example `Main Store -> Yangon Floor`.
- Keep row cards dense but premium: movement id, date/time, purpose, warehouses, item count, quantity summary, posture link.
- Use an empty state that teaches: `No posted movements found for this window. Try a wider date range.`
- On mobile/tablet widths, stack movement direction above line summary so warehouse users can scan quickly.
- Do not use disabled execution buttons as a visual promise.
- Do not use native ERPNext table chrome.

Recommended overview addition:

- Add a small `Movement Visibility` panel only after W8A route is stable.
- Show three cards maximum: `Recent Transfers`, `Receipts Posted`, `Issues Posted`.
- Use one primary action: `Open movement visibility`.
- Keep W4/W5/W6/W7 cards above movement history if active work needs attention.

## 8. Service Contract Recommendation

Recommended backend method after W8A approval:

- `get_warehouse_movement_visibility_queue(filters=None)`

Recommended payload shape:

- `state`: `ready`, `restricted`, `unavailable`, or `empty`.
- `generated_at`: ISO timestamp.
- `summary`: movement counts by group and date window.
- `filters`: applied safe filters and available filter options.
- `groups`: ordered movement groups with bounded rows.
- `rows`: movement summaries with no valuation or native route data.
- `messages`: safe operational copy only.

Allowed row fields:

- `movement_id`
- `movement_type`
- `purpose`
- `posting_date`
- `posting_time`
- `source_warehouse`
- `target_warehouse`
- `direction_label`
- `item_count`
- `quantity_summary`
- `sample_items`
- `posture_route` only when it points to `/desk/warehouse-console-stock-posture/<encoded-context>`
- `receiving_route` only when it points to `/desk/warehouse-console-receiving/<purchase-order>` and is already protected
- `picking_route` only when it points to `/desk/warehouse-console-picking/<sales-order>` and is already protected

Forbidden row fields:

- `valuation_rate`
- `stock_value`
- `stock_value_difference`
- `incoming_rate`
- `outgoing_rate`
- `basic_rate`
- `rate`
- `amount`
- `base_amount`
- `transfer_price`
- `cost`
- `gl_entry`
- `account`
- `expense_account`
- `difference_account`
- `stock_queue`
- `serial_no` and `batch_no` unless a later traceability design is approved
- native `route`, `doctype`, or `form_url` values that open ERPNext documents

## 9. Regression And Protection Requirements

Any W8A implementation must add source tests for:

- Registry route ownership for `/desk/warehouse-console-worklist/movement-visibility`.
- Governance manifest entry for the movement visibility route.
- Warehouse role access only.
- Payload is read-only and bounded.
- Payload excludes valuation/accounting/commercial fields.
- Payload excludes native route targets.
- W8A does not dirty Sales or Procurement runtime boundaries.
- W8A preserves W3/W3A landing and single-shell behavior.
- W8A preserves W4A/W4B/W5A/W5B/W6A/W6B/W7A routes.

Focused smoke recommendation:

- Add `ui_smoke/warehouse_phase_w8a_movement_visibility_smoke.js`.
- Add package script `test:warehouse-w8a-movement-visibility`.
- Add Docker script `test:warehouse-w8a-movement-visibility:docker`.
- Forward `ERPW_WAREHOUSE_W8A_ASSET_ROOT` through the Docker runner.

Focused smoke must verify:

- Warehouse Manager can open the overview and movement visibility route.
- Warehouse User can open the overview and movement visibility route.
- Direct route refresh keeps one Warehouse shell.
- Empty live movement windows render a safe empty state.
- Rows, when present, show grouped movement cards with no native document link.
- `Review stock posture` routes, when present, target only custom Warehouse route.
- No visible lifecycle/action labels appear.
- No valuation/accounting/commercial terms appear.
- No Warehouse Quick Find/Search appears.
- No browser console hard errors.

Required gates before commit:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched runtime and W8A smoke files
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`
- Focused W8A source smoke with Warehouse credentials
- Sales freeze protection
- Full protected source gate

Required gates after live alignment:

- Live W8A focused smoke with no source asset root.
- Full protected live gate.
- Source/live SHA-256 proof for runtime files only.
- Confirm tests and smokes were not synced to live.

## 10. Warehouse Agent Handoff Boundary

Main control agent owns:

- This W8 docs-only design plan.
- Scope decision and guardrail enforcement.
- Credentialed source smoke execution.
- Sales freeze and full protected gates.
- Commit, push, live alignment, restart/cache-clear, and post-live gates.
- Final acceptance documentation.

Warehouse implementation agent owns only after this plan is approved:

- Source-only W8A implementation.
- Unit/contract tests.
- Focused W8A smoke.
- Noncredentialed static validation.
- Handoff notes with exact changed files and exact blocked credentialed command.

Warehouse implementation agent must not:

- Commit.
- Push.
- Live-align.
- Restart services.
- Modify Sales runtime.
- Modify Procurement runtime.
- Use native ERPNext routes for Warehouse users.
- Add stock mutation or lifecycle controls.
- Add valuation/accounting/commercial exposure.
- Add Warehouse Quick Find/Search.

## 11. Explicitly Excluded From W8A

W8A must not introduce:

- Stock Entry create/save/submit/cancel/amend.
- Stock Reconciliation create/save/submit/cancel/amend.
- Material Transfer creation.
- Purchase Receipt creation/submission.
- Delivery Note creation/submission.
- Pick List creation/submission.
- Reservation, unreservation, allocation, transfer order creation, transfer receipt, or transfer issue.
- Serial or batch assignment.
- Cycle count or physical inventory posting.
- Native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, or Purchase Order form/list/report escape.
- Valuation, stock value, incoming/outgoing rate, amount, transfer cost, GL, accounting, profit, margin, taxes, billing, payment, supplier price, customer price, or Item Price data.
- Contact, User, portal, email, print, barcode scan, AI, or workflow approval behavior.
- Quick Find or generic search.

## 12. Recommended Next Step

Recommended next step after this docs-only W8 plan:

1. Owner approves W8A movement visibility as the next implementation target.
2. Main control agent writes a sequential Warehouse-agent implementation prompt from this plan.
3. Warehouse agent implements W8A source-only and hands back for credentialed focused smoke.
4. Main control agent runs focused W8A source smoke, Sales freeze, full protected source gate, commit/push, live alignment, live smoke, full protected live gate, and docs baseline.

If owner prefers transfer visibility before movement history, W8A should be replaced by a separate docs-only transfer visibility plan before implementation because transfer scope is closer to stock execution.

## 13. Docs-Only Closure

This W8 plan is documentation only.

It does not:

- Change runtime code.
- Change tests.
- Change smokes.
- Change package scripts.
- Sync files to live.
- Restart services.
- Touch `ui_smoke/sales_final_acceptance_audit.js`.

Required docs-only validation:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
