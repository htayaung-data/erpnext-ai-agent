# Warehouse Console Phase W7A Stock Posture Review Baseline

Date: 2026-05-29

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W7A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime and smoke acceptance commits:

- W7A stock posture review runtime: `8ce0961 feat: add warehouse stock posture review`
- W7A live-data smoke compatibility: `2d66486 test: allow live warehouse stock posture fallback`

W7A extends the protected W6B Stock Exception Review baseline with read-only item/warehouse stock posture review:

- `/desk/warehouse-console-stock-posture/<encoded-context>` is now a protected Warehouse product route.
- W6B Stock Exception Review can link to W7A through `Review stock posture` when source context exists.
- The W7A route renders item and warehouse operational posture, inbound cover, open outbound demand, related custom review paths, and freshness.
- Related drilldowns stay inside custom Warehouse routes only:
  - `/desk/warehouse-console-picking/<sales-order>`
  - `/desk/warehouse-console-receiving/<purchase-order>`
  - `/desk/warehouse-console-stock-exception/<encoded-context>`
- Live Stock Exceptions can be empty. The live W7A smoke therefore validates the deployed W7A route through a direct item/warehouse posture context while source fixture smoke still requires the W6B-to-W7A drilldown path.
- The route is available to Warehouse Manager and Warehouse User.
- Browser reload, repeated direct route, refresh, and back paths keep a single Warehouse shell.
- No stock execution, valuation, native ERP escape, Quick Find, Warehouse search, or stock lifecycle action was introduced.

## 2. Accepted Artifacts

Focused W7A source artifacts:

- Source W7A smoke after implementation: `/tmp/warehouse-phase-w7a-source-20260529T124503Z/warehouse-w7a-stock-posture-20260529T124510Z/warehouse-w7a-stock-posture-summary.json`
- Source W7A smoke after live-data compatibility repair: `/tmp/warehouse-phase-w7a-source-smoke-fix-20260529T131825Z/warehouse-w7a-stock-posture-20260529T131829Z/warehouse-w7a-stock-posture-summary.json`

Source protection artifacts:

- Source Sales freeze before protected source gate: `/tmp/sales-freeze-protection-20260529T124630Z/sales-freeze-protection-summary.json`
- Final source protected gate: `/tmp/warehouse-phase-w7a-protected-source-20260529T125119Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w7a-live-hashes-20260529T130956Z.txt`
- First live W7A smoke attempt with empty Stock Exceptions: `/tmp/warehouse-phase-w7a-live-20260529T131517Z/warehouse-w7a-stock-posture-20260529T131522Z/warehouse-w7a-stock-posture-summary.json`
- Final live W7A smoke: `/tmp/warehouse-phase-w7a-live-20260529T131857Z/warehouse-w7a-stock-posture-20260529T131902Z/warehouse-w7a-stock-posture-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w7a-protected-live-20260529T132014Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w7a-protected-live-20260529T132014Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Transient and repaired gate notes:

- Initial W7A source smoke exposed a smoke wait race. The smoke was returning on the loading skeleton before the W6B review payload rendered `Review stock posture`. The wait now requires rendered review content.
- A second source smoke attempt exposed the same skeleton issue on the W7A page. The W7A wait now requires rendered stock posture cards or route rows.
- First live W7A smoke exposed a valid live-data difference: live Stock Exceptions had no rows, so the W6B-to-W7A drilldown could not be used. The smoke now keeps source fixture coverage strict and uses a direct live item/warehouse context when the live exception queue is empty.
- A later live smoke attempt exposed a back-route expectation mismatch. Live W7A can back to picking or receiving when those related routes exist. The smoke now follows the actual available related target priority.
- These changes were smoke-only and were committed in `2d66486`. No smoke file was live-aligned.

## 3. Live Runtime Hashes

Final live alignment synced only approved W7A runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `0b869e6e89886f1dbf15013b3744d843aaabfe392c1402ef1f7ab882ca0e7e3b` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `950ee40344ab460383d80fde13b9013eb56f27dda5b4a665771f4b30822a3a19` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/__init__.py` | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js` | `f835619c6f1ea0a79ac66f02e3e6e9577da133b7b1b700acc38526a1802d4e94` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.json` | `6a5dbfa68b87983ebf7cdaec3e54fd7ab718c1b14d8188faf565e9b19f6c2ac6` |
| `erp_workspace_ui/workspace_registry.py` | `a15626935a4d2ace0b9ca9e8801dd9ccfcb3930aa525a18127b8c945c6ff97d2` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `6980d063b34547cfa60888e19df903ebf3ea892518b8ecde92ff59da8ac8045e` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `81ea01c5873bbea6f902157b757d7775cfb3435815fa0866ca39b0603416489f` |

Smoke and package files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W7A behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Stock Exceptions remains available at `/desk/warehouse-console-worklist/stock-exceptions`.
- Stock Exception Review can route to W7A through a custom `Review stock posture` control when the source exception row has item and warehouse context.
- Direct W7A route loads through `/desk/warehouse-console-stock-posture/<encoded-context>`.
- The encoded context identifies item code, warehouse, and optional related custom route context without exposing native ERP document routes.
- Stock Posture Review renders one Warehouse shell for the `stock-posture-review` view.
- Stock Posture Review shows read-only cards and panels for stock posture, inbound cover, open demand, and related custom routes.
- Refresh reloads the W7A payload without creating duplicate shells.
- Back follows safe custom Warehouse route context when present, or the Stock Exceptions worklist fallback.
- Live empty Stock Exceptions state does not block W7A live validation because a direct item/warehouse context is accepted.
- Warehouse Search / Quick Find remains inactive in W7A.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W7A smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W7A service posture:

- Uses controlled Warehouse service method `get_warehouse_stock_posture_review`.
- Requires Warehouse role access.
- Decodes a bounded stock posture context token.
- Requires item code and warehouse in the decoded context.
- Uses Bin only for read-only operational stock posture when readable.
- Uses submitted/open Purchase Orders and Purchase Order Items only for inbound cover posture when readable.
- Uses submitted/open Sales Orders and Sales Order Items only for outbound demand posture when readable.
- Uses readable parent document fallbacks where direct child-table access is unavailable.
- Converts missing, restricted, or unavailable data into safe business states.
- Keeps response sizes bounded.

Allowed W7A data concepts:

- Item code and item name.
- Warehouse.
- Actual quantity as operational posture.
- Available quantity as operational posture.
- Reserved quantity as operational posture.
- Projected quantity as operational posture.
- Open inbound quantity/date/order posture.
- Open outbound demand quantity/date/order posture.
- Related custom Warehouse route context.
- Freshness timestamp.

Excluded W7A data concepts:

- Stock value.
- Valuation rate.
- Buying rates, selling rates, amounts, taxes, margins, profit, cost, GL, accounting, billing, payment, or commercial pricing.
- Stock Ledger, Stock Balance, Item Form, Item List, or native ERP report links.
- Raw framework errors in owner-facing copy.
- Quick Find or generic Warehouse search.

## 6. Explicitly Excluded Actions

W7A remains read-only. It must not introduce:

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

W7A runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/__init__.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_stock_posture/warehouse_console_stock_posture.json`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

W7A test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w7a_stock_posture_smoke.js`

## 8. Regression Protection Expectations

Future Warehouse work must preserve:

- Warehouse W3/W3A landing behavior.
- W4A Inbound Receiving route ownership.
- W4B Receiving Review route ownership.
- W5A Outbound Picking route ownership.
- W5B Picking Review route ownership.
- W6A Stock Exceptions route ownership.
- W6B Stock Exception Review route ownership.
- W7A Stock Posture Review route ownership.
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

Recommended next phase: W8 docs-only warehouse operations roadmap decision before implementation.

Recommended candidate directions:

- W8A read-only warehouse movement history from Stock Entry and Stock Ledger-safe parent records, excluding valuation.
- W8B read-only warehouse location/bin posture by item group or warehouse, excluding native reports.
- W8C read-only transfer visibility and transfer exception posture, without Stock Entry creation.

W8 should start with a docs-only design plan before implementation because movement history and transfer visibility are closer to stock execution and native ERPNext valuation surfaces.

W8 must not include:

- Stock Ledger native report escape.
- Stock Balance native report escape.
- Stock Entry creation or submission.
- Transfer creation.
- Reconciliation creation.
- Any valuation, accounting, or commercial exposure.
- Warehouse Quick Find/Search unless separately approved and protected.

Owner decisions before W8 implementation:

- Confirm whether movement history, location/bin posture, or transfer visibility should come first.
- Confirm whether W8 is still Warehouse Manager/User identical.
- Confirm whether any historical movement fields are acceptable without valuation.
- Confirm whether W8 should remain detail-route only or add overview cards.

## 10. Docs-Only Closure

This W7A closure is documentation only.

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
