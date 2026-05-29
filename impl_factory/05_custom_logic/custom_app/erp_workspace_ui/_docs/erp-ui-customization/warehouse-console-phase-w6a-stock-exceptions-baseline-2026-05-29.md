# Warehouse Console Phase W6A Stock Exceptions Baseline

Date: 2026-05-29

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W6A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime, live permission repair, and smoke empty-state baseline commits:

- W6A stock exception visibility: `8e41d92 feat: add warehouse stock exception visibility`
- W6A live child visibility repair: `ebf1dbc fix: support warehouse stock exception child visibility`
- W6A live empty-state/modal cleanup: `982edba fix: stabilize warehouse stock exception empty state`

W6A extends the protected W5 outbound posture baseline with read-only stock exception visibility:

- Warehouse Overview exposes `Stock Exceptions` as a visible navigation panel/action.
- `/desk/warehouse-console-worklist/stock-exceptions` is now a protected Warehouse product route.
- Stock Exceptions renders grouped read-only exception posture for Warehouse Manager/User.
- Groups are `Needs Stock Review`, `Inbound Cover Expected`, `Urgent / Aging Demand`, and `Warehouse Posture Missing`.
- Summary cards show total exceptions, shortage risk, inbound cover soon, and missing warehouse posture.
- Filters are read-only review controls for exception state, warehouse text, and order/item/customer text.
- Rows drill only to existing custom Warehouse routes when rows exist:
  - `/desk/warehouse-console-picking/<sales-order>`
  - `/desk/warehouse-console-receiving/<purchase-order>`
- Live zero-exception state is accepted and shows business-safe empty groups.
- No stock execution, valuation, native ERP escape, Quick Find, or Warehouse search was introduced.

## 2. Accepted Artifacts

Focused W6A artifacts:

- Final source W6A smoke: `/tmp/warehouse-phase-w6a-source-20260529T042845Z/warehouse-w6a-stock-exceptions-20260529T042849Z/warehouse-w6a-stock-exceptions-summary.json`
- Final live W6A smoke: `/tmp/warehouse-phase-w6a-live-20260529T045129Z/warehouse-w6a-stock-exceptions-20260529T045134Z/warehouse-w6a-stock-exceptions-summary.json`

Source protection artifacts:

- Initial source protected gate after W6A implementation: `/tmp/warehouse-phase-w6a-protected-source-20260529T031808Z/protected-workspace-gate-summary.json`
- Source protected gate after child visibility repair: `/tmp/warehouse-phase-w6a-protected-source-20260529T035743Z/protected-workspace-gate-summary.json`
- Final source protected gate after empty-state/modal cleanup: `/tmp/warehouse-phase-w6a-protected-source-20260529T042942Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Final live source/hash proof: `/tmp/warehouse-w6a-live-hashes-20260529T045037Z.txt`
- Final protected live gate: `/tmp/warehouse-phase-w6a-protected-live-20260529T050140Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w6a-protected-live-20260529T050140Z/sales-freeze-protection/sales-freeze-protection-summary.json`
- Targeted Sales worklists live rerun passed while classifying transient nested Sales gate failures.
- Targeted rerun command artifact root: `/tmp/warehouse-phase-w6a-sales-worklists-live-rerun-20260529T045521Z`
- Targeted rerun smoke report: `/tmp/erpw-ui-smoke/artifacts/sales-worklist-shell-smoke/sales-worklist-shell-report.json`

Transient and repaired gate notes:

- First live W6A smoke exposed a real permission posture issue: Warehouse roles could read parent Sales/Purchase documents but direct child table reads could be unavailable, causing restricted/empty behavior. The service now falls back through readable parent documents for child lines while preserving read permission checks.
- Second live W6A smoke exposed a valid live empty state: current live data had zero stock exceptions. The smoke now accepts rendered empty groups and still exercises drilldowns when source fixture rows exist.
- A blank Frappe message modal appeared after intentionally handled permission fallbacks. The service now clears transient Frappe message logs when exceptions are caught and converted to safe fallback data.
- Two final protected live attempts showed transient Sales worklist readiness failures unrelated to W6A runtime. A targeted Sales worklists rerun passed, and the final protected live gate passed with the Sales worklists timeout extended for the nested full gate.

## 3. Live Runtime Hashes

Final live alignment synced only approved W6A runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `9ea0315ba44782ab6b0bc80db742e54da25b285277c83c3b47d549c1d3fa9f4b` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `882af03951678040c368b91ba98a153a198fe0d2ec5aad6eebbd4e656b2986d3` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js` | `12b133a74ed38d7bd85a2ff7e5445d75ee1d6f96d4ba81457f4d20c06ff0767a` |
| `erp_workspace_ui/workspace_registry.py` | `d247f59d6a93c0e7c7a6eb1ec54c427bae839a3ab815e65557c705cffbd851c0` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `126f2410095605da9fefa4d792e13fa9b083b422c406e493c9d305c2acd55072` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `f8f369fcdc6f81c438338e0389978797394872d6c076bcdda337d98775de71fa` |

Smoke and package files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W6A behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Warehouse Overview includes a visible `Stock Exceptions` panel/action.
- `Open stock exceptions` routes to `/desk/warehouse-console-worklist/stock-exceptions`.
- Stock Exceptions renders one Warehouse shell for the `stock-exceptions` view.
- Stock Exceptions shows four summary cards and four exception groups.
- Stock Exceptions supports safe filters and refresh/reset/apply interactions.
- Live zero-row state renders empty group messaging without treating the route as failed.
- When exception rows exist, row actions stay inside custom Warehouse review routes only.
- Browser reload, repeated route open, direct route, and viewport checks keep a single shell.
- Warehouse Search / Quick Find remains inactive in W6A.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W6A smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W6A service posture:

- Uses controlled Warehouse service method `get_warehouse_stock_exceptions`.
- Requires Warehouse role access.
- Requires read access to parent Sales Order data for outbound demand posture.
- Uses Sales Order Item direct reads when available.
- Falls back through readable parent Sales Order `items` child tables when direct child-table access is unavailable.
- Uses Bin only for read-only warehouse stock posture when readable.
- Uses Purchase Order and Purchase Order Item for inbound cover posture when readable.
- Falls back through readable parent Purchase Order `items` child tables when direct child-table access is unavailable.
- Keeps response sizes bounded.
- Converts unavailable data into safe empty/restricted states rather than owner-facing framework errors.

Allowed W6A data concepts:

- Sales Order id.
- Customer name.
- Item code and item name.
- Required delivery date posture.
- Pending and delivered quantity.
- UOM.
- Warehouse name or missing-warehouse posture.
- Available/projected quantity as operational posture only.
- Short quantity as operational posture only.
- Expected inbound quantity/date and Purchase Order id when inbound cover exists.
- Exception label and explanation.

Excluded W6A data concepts:

- Stock value.
- Valuation rate.
- Buying rates, selling rates, amounts, taxes, margins, profit, cost, GL, accounting, billing, or payment data.
- Raw framework errors in owner-facing copy.
- Native ERP document links.

## 6. Explicitly Excluded Actions

W6A remains read-only. It must not introduce:

- Pick List creation.
- Pick List submission.
- Delivery Note creation.
- Delivery Note submission.
- Purchase Receipt creation.
- Purchase Receipt submission.
- Stock Entry creation.
- Stock Entry submission.
- Stock Reconciliation creation or submission.
- Pick, pack, ship, dispatch, receive, post, submit, cancel, amend, close, approve, reject, reconcile, reserve, or unreserve actions.
- Serial or batch assignment.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, or AI behavior.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

Disabled fake execution buttons are also excluded. If an execution action is not approved, it should not appear as an owner-facing disabled promise.

## 7. Protected Runtime Files

W6A runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

W6A test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w6a_stock_exceptions_smoke.js`

## 8. Regression Protection Expectations

Future Warehouse work must preserve:

- Warehouse W3/W3A landing behavior.
- W4A Inbound Receiving route ownership.
- W4B Receiving Review route ownership.
- W5A Outbound Picking route ownership.
- W5B Picking Review route ownership.
- W6A Stock Exceptions route ownership.
- Single Warehouse shell/header/sidebar rendering.
- No native ERP route escape for normal Warehouse users.
- No stock mutation or lifecycle actions.
- No valuation/accounting/commercial exposure.
- No Warehouse Quick Find/Search until separately designed and protected.
- Sales freeze protection.
- Procurement protected workspace behavior.
- Full protected workspace gate success after shared runtime changes.

Any future change to Warehouse `service.py`, Warehouse JS, shared registry, boot routing, shared sidebar, or protected smoke behavior must rerun focused Warehouse smoke, Sales freeze, and full protected workspace gates before live alignment.

## 9. Recommended Next Phase

Recommended next phase: W6B read-only Stock Exception Detail Review design before implementation.

Recommended candidate route:

- `/desk/warehouse-console-stock-exception/<sales-order>/<item-code>`

Recommended W6B scope:

- Read-only detail page for one exception row selected from W6A.
- Header with exception state, Sales Order, customer, item, warehouse, and due posture.
- Sections for demand source, stock posture, inbound cover, and safe related Warehouse routes.
- Drilldowns only to custom Warehouse Picking Review and Receiving Review where source documents exist.
- Back to Stock Exceptions and Refresh actions only.

W6B must not include:

- Pick List, Delivery Note, Purchase Receipt, Stock Entry, or Stock Reconciliation creation.
- Any submit/cancel/amend/post/receive/pick/pack/ship/reserve action.
- Native ERPNext form/report/list links.
- Valuation, pricing, billing, payment, accounting, margin, or cost data.
- Warehouse Quick Find/Search.

Owner decisions before W6B:

- Confirm the detail route shape.
- Confirm whether detail identity should be Sales Order + item code, Sales Order + row id, or a derived exception key.
- Confirm whether W6B should show inbound cover detail inline or route only to Receiving Review.
- Confirm whether W6B should remain Warehouse roles only.

## 10. Docs-Only Closure

This W6A closure is documentation only.

It does not:

- Change runtime code.
- Change tests.
- Change smokes.
- Change package scripts.
- Sync files to live.
- Restart services.
