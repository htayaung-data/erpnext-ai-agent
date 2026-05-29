# Warehouse Console Phase W6B Stock Exception Review Baseline

Date: 2026-05-29

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W6B runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime and smoke acceptance commits:

- W6B stock exception review runtime: `edd9c7e feat:naddnwarehousenstocknexceptionnreviewn`
- W6B live empty-queue smoke compatibility: `2730cf7 test: allow empty live warehouse stock exceptions`

Note: the runtime commit message is mangled by shell quoting, but the commit content is accepted and protected. Do not amend this commit unless the owner explicitly requests history cleanup.

W6B extends the protected W6A Stock Exceptions baseline with read-only exception detail review:

- `/desk/warehouse-console-stock-exception/<encoded-context>` is now a protected Warehouse product route.
- Stock Exception rows from W6A include a custom review drilldown target.
- The detail page renders demand posture, stock posture, inbound cover, recommended review, and related custom Warehouse route panels.
- Related drilldowns stay inside custom Warehouse routes only:
  - `/desk/warehouse-console-picking/<sales-order>`
  - `/desk/warehouse-console-receiving/<purchase-order>`
- The route is available to Warehouse Manager and Warehouse User.
- Browser reload, repeated direct route, and route-guard paths keep a single Warehouse shell.
- Live zero-exception state is accepted on the W6A queue: the live smoke validates the empty Stock Exceptions shell and does not falsely require a review drilldown when no live row exists.
- Source fixture smoke still requires and exercises the full W6B review route.
- No stock execution, valuation, native ERP escape, Quick Find, Warehouse search, or stock lifecycle action was introduced.

## 2. Accepted Artifacts

Focused W6B source artifacts:

- Source W6B smoke after implementation: `/tmp/warehouse-phase-w6b-source-20260529T080842Z/warehouse-w6b-stock-exception-review-20260529T080846Z/warehouse-w6b-stock-exception-review-summary.json`
- Source W6B smoke after smoke compatibility repair: `/tmp/warehouse-phase-w6b-source-smoke-fix-20260529T100717Z/warehouse-w6b-stock-exception-review-20260529T100721Z/warehouse-w6b-stock-exception-review-summary.json`

Source protection artifacts:

- Final source protected gate: `/tmp/warehouse-phase-w6b-protected-source-20260529T094256Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w6b-live-hashes-20260529T100250Z.txt`
- First live W6B smoke attempt with zero live rows: `/tmp/warehouse-phase-w6b-live-20260529T100334Z/warehouse-w6b-stock-exception-review-20260529T100338Z/warehouse-w6b-stock-exception-review-summary.json`
- Final live W6B smoke: `/tmp/warehouse-phase-w6b-live-20260529T100836Z/warehouse-w6b-stock-exception-review-20260529T100840Z/warehouse-w6b-stock-exception-review-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w6b-protected-live-20260529T100956Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w6b-protected-live-20260529T100956Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Transient and repaired gate notes:

- Early source protected gate attempts exposed credential mapping issues for the Procurement user slot. The accepted protected gate used `purchase.manager@meet.com` for both purchase protected slots because the previous `purchase.ygn.01@meet.com` role could not complete Phase5D purchase-order action coverage.
- A transient Sales 502/readiness issue appeared during protected source validation. Live Frappe cache was cleared and services were restarted; Sales freeze then passed.
- First live W6B smoke proved the live Stock Exceptions route mounted correctly but found zero live exception rows. The original smoke asserted the review renderer even when no row existed, which was a smoke-contract issue rather than a runtime defect.
- Commit `2730cf7` keeps source fixture behavior strict while allowing live zero-row Stock Exceptions queues to pass when the empty shell is rendered correctly.

## 3. Live Runtime Hashes

Final live alignment synced only approved W6B runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `76b7889d591f754b79ac01a1004ddf8d8b024ef774136f1e848e9e3968dc188f` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `5fb12830ca73006178107411d3857e45783fa0fa101ba70d9ca7dc71d59f3b20` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/__init__.py` | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.js` | `2012fec0abeb315cb864c3bc8364aeff645bc9b4b4ddec62d06db679889228e1` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.json` | `c7eada066100bbf85ea072cf5c9dcf06d6e8f2db3f41554880c3451505deddef` |
| `erp_workspace_ui/workspace_registry.py` | `eaacce84e39fb3beb8294f861c8342f51d84387d8e88ddcfc5ea5d7e810ae7a5` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `c10db7671510a91e828fa738bc51fb753cd747cbf72865093716207b710fd2cf` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d2e000d46809f8688048bd5346f4a544ecf1ead142a697345f39340db30b7a9f` |

Smoke and package files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W6B behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Warehouse Overview includes visible Stock Exceptions navigation inherited from W6A.
- Stock Exceptions remains available at `/desk/warehouse-console-worklist/stock-exceptions`.
- When Stock Exception rows exist, row detail action routes to `/desk/warehouse-console-stock-exception/<encoded-context>`.
- The encoded context identifies the review by Sales Order, item code, and warehouse without exposing a native ERP document route.
- Stock Exception Review renders one Warehouse shell for the `stock-exception-review` view.
- Stock Exception Review shows read-only cards and panels for demand, stock posture, inbound cover, and next review.
- Related links stay inside custom Warehouse route surfaces only.
- Refresh and back actions are read-only/navigation only.
- Browser reload and repeated direct route keep a single Warehouse shell.
- Live zero-row Stock Exceptions state renders empty group messaging without treating W6B as failed.
- Warehouse Search / Quick Find remains inactive in W6B.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W6B smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W6B service posture:

- Uses controlled Warehouse service method `get_warehouse_stock_exception_review`.
- Requires Warehouse role access.
- Requires read access to the Sales Order.
- Decodes a bounded stock exception context token.
- Reads the matching Sales Order line when available.
- Falls back through readable parent Sales Order `items` child tables when direct child-table access is unavailable.
- Uses Bin only for read-only warehouse stock posture when readable.
- Uses Purchase Order and Purchase Order Item only for inbound cover posture when readable.
- Converts missing, restricted, or unavailable data into safe business states.
- Keeps response sizes bounded.

Allowed W6B data concepts:

- Sales Order id.
- Customer name.
- Item code and item name.
- Source warehouse.
- Required date and urgency posture.
- Pending and delivered quantity.
- UOM.
- Available/projected quantity as operational posture only.
- Short quantity as operational posture only.
- Expected inbound quantity/date and Purchase Order id when inbound cover exists.
- Exception label, explanation, recommended review text, and related custom route context.

Excluded W6B data concepts:

- Stock value.
- Valuation rate.
- Buying rates, selling rates, amounts, taxes, margins, profit, cost, GL, accounting, billing, payment, or commercial pricing.
- Raw framework errors in owner-facing copy.
- Native ERP document links.
- Quick Find or generic Warehouse search.

## 6. Explicitly Excluded Actions

W6B remains read-only. It must not introduce:

- Pick List creation.
- Pick List submission.
- Delivery Note creation.
- Delivery Note submission.
- Purchase Receipt creation.
- Purchase Receipt submission.
- Stock Entry creation.
- Stock Entry submission.
- Stock Reconciliation creation or submission.
- Reservation, unreservation, transfer, or allocation creation.
- Pick, pack, ship, dispatch, receive, post, submit, cancel, amend, close, approve, reject, reconcile, reserve, or unreserve actions.
- Serial or batch assignment.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, or AI behavior.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

Disabled fake execution buttons are also excluded. If an execution action is not approved, it should not appear as an owner-facing disabled promise.

## 7. Protected Runtime Files

W6B runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/__init__.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_exception/warehouse_console_stock_exception.json`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

W6B test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w6b_stock_exception_review_smoke.js`

## 8. Regression Protection Expectations

Future Warehouse work must preserve:

- Warehouse W3/W3A landing behavior.
- W4A Inbound Receiving route ownership.
- W4B Receiving Review route ownership.
- W5A Outbound Picking route ownership.
- W5B Picking Review route ownership.
- W6A Stock Exceptions route ownership.
- W6B Stock Exception Review route ownership.
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

Recommended next phase: W7 read-only Item/Warehouse Stock Posture Review design before implementation.

Recommended candidate route:

- `/desk/warehouse-console-stock-posture/<encoded-item-warehouse-context>`

Recommended W7 scope:

- Read-only detail page for item and warehouse stock posture selected from Warehouse routes.
- Header with item, warehouse, current operational posture, and freshness.
- Sections for stock posture, inbound cover, outbound demand, and safe related Warehouse routes.
- Drilldowns only to custom Warehouse Receiving Review, Picking Review, and Stock Exception Review where source context exists.
- Back and Refresh actions only.

W7 must not include:

- Stock Ledger native escape.
- Stock Balance report native escape.
- Item form/list/report native escape.
- Pick List, Delivery Note, Purchase Receipt, Stock Entry, Stock Reconciliation, reservation, transfer, or allocation creation.
- Any submit/cancel/amend/post/receive/pick/pack/ship/reserve action.
- Valuation, pricing, billing, payment, accounting, margin, or cost data.
- Warehouse Quick Find/Search unless separately approved.

Owner decisions before W7 implementation:

- Confirm route shape and encoded context identity.
- Confirm whether W7 should be item-only, item-plus-warehouse, or warehouse-plus-item.
- Confirm whether W7 should be reachable from W6B, W5B, W4B, or only from future overview cards.
- Confirm whether W7 remains Warehouse Manager/User identical or has manager-only posture fields.

## 10. Docs-Only Closure

This W6B closure is documentation only.

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
