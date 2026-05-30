# Warehouse Console Phase W8B Movement Review Design Plan

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: docs-only W8B design plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

Runtime baseline before W8B design:

- W8A movement visibility runtime: `c408b85b9f9bdab9ac66e0be375930e50a8bece3`
- W8A protected baseline documentation: `bd5cc253859a418830b81456708e9b63dc4274ed`
- W8A source smoke: `/tmp/warehouse-phase-w8a-source-20260529T161227Z/warehouse-w8a-movement-visibility-20260529T161234Z/warehouse-w8a-movement-visibility-summary.json`
- W8A protected live gate: `/tmp/warehouse-phase-w8a-protected-live-20260529T171713Z/protected-workspace-gate-summary.json`

## 1. Executive Recommendation

W8B should add a read-only Movement Review detail route for one movement context, not Stock Entry execution.

Recommended W8B implementation scope after this design is approved:

- Add a read-only custom route: `/desk/warehouse-console-movement/<encoded-context>`.
- Link to W8B only from W8A Movement Visibility rows that can produce a safe encoded context.
- Use the existing W8A movement summary as the entry point, then fetch bounded detail for one submitted Stock Entry.
- Keep the displayed detail operational: movement purpose, posted date/time, source/target warehouses, grouped line summary, direction, sample items, and custom related Warehouse posture routes.
- Keep all native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, and Purchase Order routes out of W8B.
- Keep Stock Ledger Entry and native Stock Ledger report out of W8B.
- Keep transfer execution, receiving, issuing, reconciliation, reservation, serial/batch assignment, and lifecycle actions out of W8B.
- Keep valuation, accounting, costing, rates, amounts, GL, profit, margin, tax, billing, payment, Item Price, and commercial fields out of W8B.

The product goal is an operations-grade movement explanation page: a warehouse user should understand why a stock movement appears on the board and what safe custom Warehouse posture pages explain the resulting item/warehouse state. The page must not become a disguised Stock Entry form or Stock Ledger drilldown.

## 2. Research Basis

### 2.1 Current Protected Warehouse Baseline Reviewed

Current source and protected docs were reviewed before writing this plan:

- W8 movement visibility design plan.
- W8A movement visibility protected baseline.
- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `ui_smoke/warehouse_phase_w8a_movement_visibility_smoke.js`

Current source-backed findings:

- W8A already owns `/desk/warehouse-console-worklist/movement-visibility`.
- W8A already exposes a safe movement board from submitted Stock Entry summaries.
- W8A row drilldowns currently stay inside custom Warehouse Stock Posture Review where available.
- W8A excludes Stock Ledger, native Stock Entry routes, valuation, Quick Find/Search, and stock mutation.
- Existing Warehouse detail patterns exist for W4B Receiving Review, W5B Picking Review, W6B Stock Exception Review, and W7A Stock Posture Review.
- Those detail patterns use custom Frappe Page routes, idempotent render guards, safe back routes, bounded service payloads, and focused smoke coverage.

W8B should follow the existing protected detail-page pattern instead of introducing a new raw document viewer.

### 2.2 Official Documentation Reviewed

Official/vendor sources used:

- ERPNext Stock Entry: https://docs.frappe.io/erpnext/user/manual/en/stock-entry
- ERPNext Stock Ledger Report: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/stock-ledger
- ERPNext Stock Transactions: https://docs.frappe.io/erpnext/user/manual/en/stock-transactions
- Microsoft Dynamics 365 inventory transaction details: https://learn.microsoft.com/en-us/dynamics365/supply-chain/inventory/inventory-transactions-details
- Microsoft Dynamics 365 warehouse-specific inventory transactions: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-transactions
- Odoo Moves History dashboard: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/inventory/warehouses_storage/reporting/moves_history.html
- Oracle Fusion Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/famml/inventory-management-work-area.html

Source-backed design inferences:

- ERPNext Stock Entry is the operational movement parent, so W8B can review one submitted Stock Entry safely if it remains read-only and redacted.
- ERPNext Stock Ledger is better treated as an excluded native/report surface for W8B because ledger-oriented history can carry valuation-adjacent fields.
- Microsoft Dynamics separates transaction inspection from warehouse execution, supporting a read-only review page that explains movement state without posting work.
- Odoo's Moves History model supports reviewing movement reason and locations, but that should remain an operational history lens, not a mutation surface.
- Oracle Inventory work areas separate inventory visibility tasks from transaction-creation tasks, supporting W8B as review-only.

## 3. W8B Ownership Boundaries

Warehouse W8B owns:

- Read-only review of one movement context selected from W8A.
- A custom movement explanation page for Warehouse Manager and Warehouse User.
- Operational line grouping by direction, source warehouse, target warehouse, movement purpose, and item summary.
- Custom related route links to existing Warehouse pages only.
- Safe empty, restricted, unavailable, loading, refresh, back, and direct-route states.

Warehouse W8B does not own:

- Stock Entry creation, edit, save, submit, cancel, amend, close, print, or email.
- Stock Ledger, Stock Balance, or Stock Reconciliation native reports/forms.
- Transfer creation, transfer issue, transfer receipt, transfer order, transfer approval, or in-transit confirmation.
- Purchase Receipt, Delivery Note, Pick List, reservation, reconciliation, cycle count, or serial/batch execution.
- Valuation, costing, accounting, GL, stock value, rates, amounts, taxes, profit, margin, billing, payment, landed cost, or Item Price data.
- Sales runtime behavior.
- Procurement runtime behavior.
- Warehouse Quick Find/Search.
- Native ERPNext route escape for normal Warehouse users.

## 4. Proposed Route And Page

| Route | Page title | Purpose | Target role | Source | Behavior | Recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/desk/warehouse-console-movement/<encoded-context>` | Movement Review | Explain one submitted stock movement in a Warehouse-owned detail shell | Warehouse Manager, Warehouse User / Stock User | Submitted Stock Entry plus bounded Stock Entry Detail summary | Read-only object page with custom related routes only | Include W8B | Medium-high because Stock Entry is close to execution |

Required route posture:

- Context must be encoded; do not expose raw native document route syntax.
- Context should include the minimum needed identifiers, expected first version: movement id and optional return route.
- Context decoding must be bounded and reject malformed, oversized, missing, or unsafe contexts into a safe unavailable state.
- Direct route load must render through the Warehouse shell.
- Repeated route load and refresh must keep one Warehouse shell.
- Back route must return to W8A Movement Visibility when no safer custom return route exists.

## 5. Proposed Service Contract

Recommended backend method:

- `get_warehouse_movement_review(context=None)`

Recommended payload:

- `state`: `ready`, `empty`, `restricted`, or `unavailable`.
- `generated_at`: ISO timestamp.
- `movement`: redacted parent movement summary.
- `sections`: operational detail sections.
- `line_groups`: bounded grouped line summaries.
- `related_routes`: custom Warehouse routes only.
- `messages`: safe business copy.

Allowed parent movement fields:

- `movement_id`
- `purpose`
- `movement_type`
- `posting_date`
- `posting_time`
- `source_warehouse`
- `target_warehouse`
- `direction_label`
- `docstatus_label`, fixed to posted/submitted semantics only
- `item_count`
- `quantity_summary`
- `freshness`

Allowed line fields:

- `item_code`
- `item_name`
- `stock_uom`
- `quantity`
- `source_warehouse`
- `target_warehouse`
- `direction_label`
- `line_note`, only if generated by safe Warehouse logic
- `stock_posture_route`, only `/desk/warehouse-console-stock-posture/<encoded-context>`

Forbidden payload fields:

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
- `serial_no`
- `batch_no`
- native `doctype`, `route`, `form_url`, `list_url`, `report_url`
- raw exception, traceback, SQL, or framework diagnostic text

## 6. Proposed UI/UX Direction

W8B should look like a premium operational incident/review page, not a transaction form.

Recommended layout:

- Compact header with `Movement Review`, movement id, purpose chip, posted date/time, and source/target route context.
- Direction panel showing source warehouse, target warehouse, and movement direction in a clear visual flow.
- Summary cards for line count, total movement quantity, affected warehouses, and related posture links.
- Grouped line section with row cards instead of a raw table.
- Related context panel with custom Warehouse links only.
- Safe footer copy indicating the page is read-only operational visibility.

Recommended visual tone:

- Serious, quiet, operational.
- Directional chips and timeline cues should aid scanning.
- Avoid disabled action buttons.
- Avoid native ERPNext document chrome.
- Avoid heavy warning colors unless the record is genuinely unavailable/restricted.

Allowed controls:

- `Back to movement visibility`.
- `Refresh`.
- `Review stock posture` for safe item/warehouse contexts.

Forbidden controls:

- `Open Stock Entry`.
- `Open Ledger`.
- `Stock Ledger`.
- `Stock Balance`.
- `Create`.
- `Edit`.
- `Save`.
- `Submit`.
- `Cancel`.
- `Amend`.
- `Post`.
- `Receive`.
- `Issue`.
- `Transfer`.
- `Reconcile`.
- `Reserve`.
- `Unreserve`.
- `Print`.
- `Email`.
- `Quick Find`.
- Generic `Search`.

## 7. Regression And Protection Requirements

Any W8B implementation must add source tests for:

- Route ownership for `/desk/warehouse-console-movement/<encoded-context>`.
- Governance manifest entry.
- Backend method existence and role access.
- Safe context decoding and malformed context fallback.
- Payload excludes valuation/accounting/commercial fields.
- Payload excludes native route targets.
- Payload excludes stock lifecycle/action controls.
- W8A rows route to W8B only when safe context exists.
- W3/W4/W5/W6/W7/W8A route ownership remains intact.
- Sales and Procurement runtime dirty boundary remains clean.

Focused smoke recommendation:

- Add `ui_smoke/warehouse_phase_w8b_movement_review_smoke.js`.
- Add package script `test:warehouse-w8b-movement-review`.
- Add Docker script `test:warehouse-w8b-movement-review:docker`.
- Forward `ERPW_WAREHOUSE_W8B_ASSET_ROOT` through Docker runner.

Focused smoke must verify:

- Warehouse Manager can navigate from W8A to W8B when movement rows exist.
- Warehouse User can navigate from W8A to W8B when movement rows exist.
- If live movement rows are empty, direct fixture/source override still validates the route.
- Direct route load renders the detail page.
- Refresh keeps one Warehouse shell.
- Back returns to Movement Visibility or safe custom route.
- No native ERPNext route escape.
- No visible lifecycle/action labels.
- No valuation/accounting/commercial text.
- No Quick Find/Search.
- No browser console hard errors.

Required gates before commit:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched runtime and W8B smoke files
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`
- Focused W8B source smoke with Warehouse credentials
- Sales freeze protection
- Full protected source gate with corrected Purchase User `purchase.ygn.01@meet.com`

Required gates after live alignment:

- Live W8B focused smoke with no source asset root.
- Full protected live gate with corrected Purchase User `purchase.ygn.01@meet.com`.
- Source/live SHA-256 proof for runtime files only.
- Confirm tests and smokes were not synced to live.

## 8. Warehouse Agent Handoff Boundary

Main control agent owns:

- This W8B docs-only design plan.
- Scope decision and guardrail enforcement.
- Credentialed source smoke execution.
- Sales freeze and full protected gates.
- Commit, push, live alignment, cache clear, restart, and post-live gates.
- Final acceptance documentation.

Warehouse implementation agent owns only after this plan is approved:

- Source-only W8B implementation.
- Unit/contract tests.
- Focused W8B smoke.
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

## 9. Recommended Implementation Sequence

Recommended W8B source-only sequence:

1. Add backend service method `get_warehouse_movement_review`.
2. Add route/page wrapper if required by existing Warehouse detail-route pattern.
3. Add renderer/export in `warehouse_console_page.js`.
4. Add W8A row link into W8B only when safe context exists.
5. Add registry and governance entries.
6. Add contract tests.
7. Add focused smoke and Docker env forwarding.
8. Run noncredentialed validation.
9. Stop for main-control credentialed smoke and gates.

## 10. Explicitly Deferred

Defer until a separate docs-only plan:

- W8C Transfer Visibility.
- Transfer exception posture.
- In-transit transfer state.
- Transfer order behavior.
- Stock Ledger-safe adapter.
- Serial/batch traceability review.
- Cycle count / physical inventory review.
- Stock reconciliation review.

These areas are closer to stock execution, valuation, or regulated inventory history and should not be mixed into W8B.

## 11. Docs-Only Closure

This W8B plan is documentation only.

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
