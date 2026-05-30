# Warehouse Console Phase W8C Transfer Visibility Design Plan

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: docs-only W8C design and sequencing plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

## 1. Baseline Before W8C

Accepted Warehouse baseline before this design:

- W8A Movement Visibility runtime: `c408b85b9f9bdab9ac66e0be375930e50a8bece3`
- W8B Movement Review runtime: `fb337a26d75af22d130fcb0bf43b779794bde055`
- W8B smoke hardening: `20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc`
- W8B baseline documentation: `5d225062b6c06d00fc64013e82eb35c18fc41576`
- W9 Information Architecture plan: `5e48154b5caae89988b3ecec932294bee806156d`
- W9A Cockpit runtime: `97b7f063a8ec9f248e6aaea63a8b5f4444f68336`
- W9A baseline documentation: `3aa818a3c8d442ee1b0b64951ec6cf4f2a6910f3`
- W9B Cockpit Usability Review: `6e4233fb92cdccfae148193b283e05ed51555105`

Accepted W9A/W9B conclusion:

- W9A cockpit is accepted as the protected Warehouse landing baseline.
- W9B found no blocker requiring immediate cockpit rework.
- W8C can proceed as a docs-only transfer visibility design, with implementation deferred until owner approval.

## 2. Executive Recommendation

W8C should add read-only transfer visibility only. It must not add transfer execution.

Recommended W8C implementation scope after this design is accepted:

- Add a read-only Transfer Visibility worklist at `/desk/warehouse-console-worklist/transfer-visibility`.
- Use submitted Stock Entry material-transfer records as the initial source because ERPNext records warehouse transfer movement through Stock Entry.
- Show transfer posture only: transfer id, posting date/time, source warehouse, target warehouse, transit posture when safely inferable, item count, quantity summary, and related custom movement/stock posture routes.
- Reuse the existing W8A/W8B movement visibility foundation and custom route model.
- Keep Transfer Visibility distinct from Movement Visibility:
  - Movement Visibility answers what stock movement was posted.
  - Transfer Visibility answers which warehouse-to-warehouse transfers need operational attention or explanation.
- Exclude transfer creation, transfer issue, transfer receipt, transit confirmation, Stock Entry lifecycle controls, Stock Reconciliation, reservation, valuation, accounting, native ERP links, and Quick Find/Search.

Recommended sequence:

1. W8C docs-only design acceptance.
2. W8C source-only Warehouse agent implementation.
3. Main-control credentialed W8C smoke, Sales freeze, protected source gate, commit/push, live alignment, live smoke, protected live gate, and baseline docs.

## 3. Research Basis

### 3.1 Current Protected Warehouse Baseline Reviewed

Current source and protected docs reviewed before this plan:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- Warehouse phase docs W3 through W9B in `_docs/erp-ui-customization/`

Current source-backed facts:

- Warehouse has one protected home route: `/desk/warehouse-console`.
- Warehouse has protected worklists for inbound receiving, outbound picking, stock exceptions, and movement visibility.
- W8A already exposes submitted Stock Entry movement records in a read-only Movement Visibility board.
- W8B already exposes a read-only movement review route at `/desk/warehouse-console-movement/<encoded-context>`.
- W9A reorganizes the home cockpit and makes Movement Visibility a known protected route family.
- No Warehouse Quick Find/Search exists.
- Normal Warehouse users must not receive native ERPNext Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Purchase Receipt, Delivery Note, Pick List, Item, Warehouse, Sales Order, or Purchase Order escape links.

### 3.2 Official / Vendor Sources Reviewed

Official/vendor sources used for transfer design:

- ERPNext Stock Entry documentation: https://docs.frappe.io/erpnext/user/manual/en/stock-entry
- ERPNext Stock Transactions documentation: https://docs.frappe.io/erpnext/user/manual/en/stock-transactions
- ERPNext Stock Ledger documentation: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/stock-ledger
- SAP EWM Warehouse Management Monitor: https://help.sap.com/docs/SAP_EXTENDED_WAREHOUSE_MANAGEMENT/3d97bec9bf1649099384bb8167df3cf2/51cdcb53ad377114e10000000a174cb4.html
- SAP stock transfer concepts: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/2d95c3180a974e0aad07556ee4d28e94/ed60b6531de6b64ce10000000a174cb4.html
- Microsoft Dynamics 365 warehouse-specific inventory transactions: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-transactions
- Oracle Fusion Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/famml/inventory-management-work-area.html
- Odoo Inter-warehouse transfers: https://www.odoo.com/documentation/saas-15.4/applications/inventory_and_mrp/inventory/routes/concepts/inter_warehouse.html

Design inferences:

- ERPNext uses Stock Entry for material transfer. That makes submitted Stock Entry material transfers the correct read-only source for W8C.
- ERPNext transfer-in-transit behavior can involve a transit warehouse. W8C may label transit posture only when it is safely inferable from submitted transfer records and warehouse type/name context; it must not simulate a transfer workflow.
- Stock Ledger remains excluded because ledger-style records can carry valuation-adjacent fields and native report escape risk.
- SAP, Microsoft, Oracle, and Odoo patterns separate monitoring/visibility from physical transfer execution. W8C should be a monitor, not an operations posting surface.
- Transfer visibility has higher execution temptation than generic movement visibility. It must be gated more tightly than W8A.

## 4. W8C Problem Statement

W8A Movement Visibility shows posted movement records. It does not yet give the warehouse user a focused view of internal transfer posture.

Warehouse teams need to answer:

- Which warehouse-to-warehouse transfers were posted recently?
- Which source and target warehouses are involved?
- Which transfers look direct, transit-related, or incomplete from a visibility standpoint?
- Which transfers need review because warehouse posture or line context is unclear?
- Where can the user inspect the related custom movement review or stock posture safely?

They must not be given controls to create, issue, receive, submit, cancel, amend, reconcile, reserve, or otherwise execute a transfer.

## 5. Proposed W8C Route

Recommended new route:

| Route | Page title | Purpose | Target role | Source | Behavior | Risk |
| --- | --- | --- | --- | --- | --- | --- |
| `/desk/warehouse-console-worklist/transfer-visibility` | Transfer Visibility | Read-only warehouse-to-warehouse transfer posture | Warehouse Manager, Warehouse User / Stock User | Submitted Stock Entry material transfer records and bounded Stock Entry Detail summaries | Grouped transfer board with safe filters and custom drilldowns | High due transfer execution proximity |

Do not add a detail route in W8C.

Reason:

- W8B Movement Review already provides safe movement detail for a Stock Entry context.
- W8C can link to the existing custom Movement Review route when a safe encoded context is available.
- A separate Transfer Review detail route should be deferred until W8C worklist behavior is protected and a real need is proven.

## 6. Data Source Map

| Concept | ERPNext source | W8C use | Safe fields | Excluded fields/actions | Phase posture |
| --- | --- | --- | --- | --- | --- |
| Transfer parent | `Stock Entry` | Primary source for submitted material transfers | name, purpose, posting date, posting time, docstatus, from warehouse, to warehouse, modified/freshness | create, save, submit, cancel, amend, print, email, native open, valuation, accounting | Include W8C |
| Transfer lines | `Stock Entry Detail` | Bounded summary only | item code, item name, stock UOM, transfer quantity, source warehouse, target warehouse, line count | basic rate, amount, valuation rate, serial/batch mutation, expense/account fields | Include as bounded summary |
| Transit posture | `Stock Entry` plus safe warehouse context | Label as direct, transit-related, or needs review only when inferable | source/target warehouse labels and transfer grouping | transit execution, receive transfer, issue transfer, ownership/cost claims | Include as label only |
| Movement review | Existing W8B custom route | Safe custom drilldown | `/desk/warehouse-console-movement/<encoded-context>` | native Stock Entry route | Include as optional custom link |
| Stock posture | Existing W7A custom route | Safe item/warehouse context | `/desk/warehouse-console-stock-posture/<encoded-context>` | native Item/Warehouse/Stock Ledger route | Include as optional custom link |
| Stock ledger history | `Stock Ledger Entry` / Stock Ledger Report | Not a source | none | valuation rate, stock value, qty-after-transaction report surface, native report | Exclude |
| Transfer orders / execution documents | Any future transfer workflow source | Not W8C source | none | issue, receive, approve, close, reserve, ship, dispatch | Defer |

## 7. Proposed Transfer Board Behavior

The Transfer Visibility worklist should answer:

- What internal warehouse transfers were posted recently?
- Which transfers are direct warehouse-to-warehouse movements?
- Which transfers appear transit-related?
- Which transfers need review due missing source/target warehouse, mixed line posture, or unavailable safe movement context?
- Which custom movement review or stock posture route can explain the record safely?

Default groups:

- `Direct Transfers`: submitted material transfers with clear source and target warehouses and no transit marker.
- `Transit Related`: submitted material transfers where a transit warehouse is safely detected from source/target warehouse context.
- `Needs Review`: transfer records with missing warehouse posture, mixed line context, oversized summary, or unavailable custom review context.
- `Recently Posted`: fallback group for posted transfers that are safe to show but do not fit the above groups.

Default query posture:

- Include submitted records only: `docstatus = 1`.
- Include transfer-like purposes only, starting with `Material Transfer`.
- Default horizon: latest 14 days or latest 50 records, whichever is tighter.
- Sort by posting date/time descending, then modified descending.
- Require Warehouse role access.
- Apply permission-safe query fallbacks and return unavailable/restricted states instead of raw exceptions.
- Keep line summaries bounded.
- Do not query native reports from the browser.
- Do not expose raw framework exceptions in visible copy.

Recommended filters:

- Transfer state: all, direct, transit related, needs review.
- Date window: today, last 7 days, last 14 days, bounded custom window.
- Source warehouse.
- Target warehouse.
- Item code/name only if bounded query behavior is proven.

Allowed visible controls:

- `Open Warehouse page`.
- `Apply filters`.
- `Reset filters`.
- `Refresh`.
- `Review movement` when a safe W8B context exists.
- `Review stock posture` when item/warehouse context exists.

Forbidden visible controls:

- `Create Transfer`.
- `Create Stock Entry`.
- `Issue Transfer`.
- `Receive Transfer`.
- `Complete Transfer`.
- `Submit`.
- `Cancel`.
- `Amend`.
- `Post`.
- `Transfer`.
- `Reconcile`.
- `Reserve`.
- `Unreserve`.
- `Open in ERPNext`.
- `Stock Entry`.
- `Stock Ledger`.
- `Stock Balance`.
- `Quick Find`.
- Generic `Search`.

## 8. Premium UI/UX Direction

Transfer Visibility should feel like a transfer control-room board, not a transaction list.

Recommended visual direction:

- Header: `Transfer Visibility`.
- Subtitle: `Read-only warehouse-to-warehouse transfer posture.`
- Status chips:
  - `Read-only`
  - `Submitted movement records`
  - freshness timestamp
- Summary cards:
  - `Direct transfers`
  - `Transit related`
  - `Needs review`
  - `Transfer quantity`
- Board groups:
  - Direct Transfers
  - Transit Related
  - Needs Review
  - Recently Posted
- Row card anatomy:
  - Transfer id
  - Posting date/time
  - Source warehouse -> target warehouse
  - Item count and transfer quantity summary
  - Transfer posture chip
  - Optional `Review movement`
  - Optional `Review stock posture`

Copy rules:

- Use "review", "visibility", "posture", "posted", and "submitted record".
- Avoid "execute", "process", "issue", "receive", "post", "complete", and "approve".
- Keep read-only guardrails visible in the header and empty states.
- Avoid disabled fake execution buttons.

Mobile direction:

- Source and target warehouse should stack vertically with a clear arrow label.
- Summary cards should be two columns on narrow screens only if no overflow occurs; otherwise one column.
- Row actions should stack after context text.
- Filters should be collapsible or stacked, not horizontally crowded.

## 9. Overview / Cockpit Integration

W8C should not disturb W9A cockpit hierarchy.

Recommended integration:

- Add a small Transfer Visibility entry under the W9A `Movement To Understand` pillar only after the route is protected.
- Do not place Transfer Visibility above Inbound, Outbound, or Stock Exceptions.
- Do not add Transfer Visibility to Start Here unless there are transfer records needing review.
- Do not add a new Quick Find/Search pattern.
- Sidebar grouping should place Transfer Visibility under a visibility/movement group if shared sidebar grouping is already safe; otherwise keep the existing sidebar stable and expose it from the cockpit card only.

## 10. Service Contract Recommendation

Recommended backend method:

- `get_warehouse_transfer_visibility_queue`

Recommended request shape:

```json
{
  "date_window": "last_14_days",
  "transfer_state": "all",
  "source_warehouse": null,
  "target_warehouse": null,
  "item": null,
  "limit": 50
}
```

Recommended response shape:

```json
{
  "state": "ready",
  "generated_at": "2026-05-30T00:00:00Z",
  "summary": {
    "direct_transfers": 0,
    "transit_related": 0,
    "needs_review": 0,
    "transfer_quantity": 0
  },
  "groups": [
    {
      "key": "direct_transfers",
      "label": "Direct Transfers",
      "rows": []
    }
  ],
  "rows": [
    {
      "transfer_id": "MAT-STE-YYYY-#####",
      "posting_date": "YYYY-MM-DD",
      "posting_time": "HH:MM:SS",
      "source_warehouse": "Source Warehouse",
      "target_warehouse": "Target Warehouse",
      "posture": "Direct transfer",
      "item_count": 1,
      "quantity_summary": "10 Nos",
      "movement_review_route": "/desk/warehouse-console-movement/<encoded-context>",
      "stock_posture_route": "/desk/warehouse-console-stock-posture/<encoded-context>"
    }
  ],
  "empty_state": {
    "title": "No transfer records match this view",
    "body": "Submitted transfer visibility will appear here when warehouse-to-warehouse movement records are available."
  }
}
```

Response rules:

- Keep unavailable/restricted states in the same custom Warehouse shell.
- Never return native route URLs.
- Never return valuation/accounting/commercial fields.
- Never return action permission flags for lifecycle operations.
- Keep payload bounded.

## 11. Smoke And Gate Requirements

Focused W8C smoke should verify:

- Warehouse Manager direct route load.
- Warehouse User direct route load.
- Overview/cockpit navigation to Transfer Visibility if cockpit integration is implemented.
- Summary cards render.
- Groups render with rows or safe empty state.
- Filters apply/reset without native navigation.
- `Review movement` opens only custom W8B movement route when available.
- `Review stock posture` opens only custom W7A route when available.
- Browser reload preserves one Warehouse shell.
- Repeated route navigation preserves one Warehouse shell.
- No Quick Find/Search.
- No native ERP route leakage.
- No lifecycle/action labels.
- No valuation/accounting/commercial text.
- No console/page errors, failed responses, or failed requests.
- Desktop, laptop, and mobile screenshots include initial worklist state before any drilldown.

Required main-control gates before live alignment:

- Focused W8C source smoke with credentials.
- Sales freeze protection.
- Full protected source gate.
- Commit/push.
- Runtime-only live alignment.
- Live W8C smoke with credentials.
- Full protected live gate.
- W8C baseline docs.

## 12. Implementation Boundaries

Allowed implementation files if W8C is approved:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js` only if required by the existing worklist route dispatcher
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- Warehouse contract tests
- Focused W8C smoke
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`

Avoid touching:

- Sales runtime files.
- Procurement runtime files.
- Shared boot routing unless absolutely required.
- Shared sidebar runtime unless the route cannot be reached through existing patterns.

## 13. Recommended Warehouse Agent Prompt

Use this only after owner accepts the W8C docs-only plan:

```text
You are the Warehouse implementation agent. Implement W8C source-only Transfer Visibility for the protected Warehouse Console.

Repository:
- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`
- Branch: `feature/erpnext-ui-design`

Scope:
- Add read-only route `/desk/warehouse-console-worklist/transfer-visibility`.
- Add backend method `get_warehouse_transfer_visibility_queue`.
- Source data from submitted Stock Entry material-transfer records and bounded Stock Entry Detail summaries only.
- Group transfer posture as Direct Transfers, Transit Related, Needs Review, and Recently Posted.
- Add summary cards, filters, safe empty states, and premium Warehouse board UI.
- Add optional custom drilldowns only to:
  - `/desk/warehouse-console-movement/<encoded-context>`
  - `/desk/warehouse-console-stock-posture/<encoded-context>`
- Add registry/governance coverage, unit contract tests, focused W8C smoke, and Docker env forwarding.
- If cockpit integration is added, place Transfer Visibility under Movement To Understand without disturbing W9A hierarchy.

Hard exclusions:
- No transfer creation, issue, receipt, completion, posting, submission, cancellation, amendment, approval, rejection, reservation, reconciliation, or stock execution.
- No native ERPNext form/list/report/workspace links.
- No Stock Ledger, Stock Balance, Stock Reconciliation, Purchase Receipt, Delivery Note, Pick List, Item, Warehouse, Sales Order, or Purchase Order native route escape.
- No valuation/accounting/commercial fields or copy: stock value, valuation rate, incoming/outgoing rate, basic rate, amount, base amount, transfer price, GL, cost, profit, margin, taxes, billing, payment, landed cost.
- No Warehouse Quick Find/Search.
- No Sales runtime changes.
- No Procurement runtime changes.

Validation required before handoff:
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched Warehouse runtime JS and smoke files
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`
- static scans for native escape, mutation/lifecycle controls, valuation/accounting/commercial exposure, Quick Find/Search, and Sales/Procurement dirty boundary

Stop before commit, push, live alignment, or protected gates. Report changed files, validation results, final git status, and exact credentialed focused smoke command for main control.
```

## 14. Main Control Decision

Recommended next action after this docs-only W8C plan is committed:

- Send the W8C implementation prompt to the Warehouse agent only if owner approves Transfer Visibility now.
- Otherwise hold W8C as design-ready and keep W9A as the live protected Warehouse cockpit baseline.
