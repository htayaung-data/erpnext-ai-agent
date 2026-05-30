# Warehouse Console Phase W8B Movement Review Baseline

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W8B runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Accepted commits:

- Runtime implementation: `fb337a26d75af22d130fcb0bf43b779794bde055 feat: add warehouse movement review`
- Smoke hardening after live validation: `20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc test: harden warehouse movement review smoke`

W8B extends the protected W8A Movement Visibility baseline with read-only movement detail:

- `/desk/warehouse-console-movement/<encoded-context>` is now a protected Warehouse product route.
- W8A movement rows expose `Review movement` only when a safe custom movement review context is available.
- `get_warehouse_movement_review` returns a bounded, read-only submitted Stock Entry movement explanation.
- The UI renders a premium custom Movement Review shell with summary cards, direction/related panels, grouped movement lines, Back, Refresh, and custom Stock Posture links.
- Direct route load, browser reload, row drilldown, repeated route navigation, Back, Refresh, and related Stock Posture navigation are covered by the W8B smoke.
- Warehouse Manager and Warehouse User are both accepted.
- No Stock Entry native form/list/report escape, Stock Ledger exposure, transfer execution, reconciliation, stock lifecycle action, valuation/accounting/commercial exposure, Warehouse Quick Find/Search, Sales runtime change, or Procurement runtime change was introduced.

## 2. Accepted Artifacts

Focused W8B source artifacts:

- Initial accepted source W8B smoke before smoke hardening: `/tmp/warehouse-phase-w8b-source-20260530T015127Z/warehouse-w8b-movement-review-20260530T015131Z/warehouse-w8b-movement-review-summary.json`
- Final source W8B smoke after smoke hardening: `/tmp/warehouse-phase-w8b-source-smokefix3-20260530T023421Z/warehouse-w8b-movement-review-20260530T023424Z/warehouse-w8b-movement-review-summary.json`

Source protection artifacts:

- Standalone Sales freeze before protected source gate: `/tmp/sales-freeze-protection-20260530T015213Z/sales-freeze-protection-summary.json`
- Source protected gate: `/tmp/warehouse-phase-w8b-protected-source-20260530T015624Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w8b-live-hashes-20260530T021321Z.txt`
- Final live W8B smoke: `/tmp/warehouse-phase-w8b-live-smokefix3-20260530T023440Z/warehouse-w8b-movement-review-20260530T023444Z/warehouse-w8b-movement-review-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w8b-protected-live-20260530T023604Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w8b-protected-live-20260530T023604Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Gate note:

- The first live W8B smoke used a hard-coded fixture token for direct/reload checks. Live correctly rendered that fake token as unavailable, so the smoke was hardened to reuse the real movement-review token discovered from the live movement row and to record real network service calls. This was a smoke-only correction in `20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc`; no runtime file changed after live alignment.

## 3. Live Runtime Hashes

Final live alignment synced only approved W8B runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `5a5a395a8cb64b1fcd63071740db53b2d987903925132168c347f906ca566c0e` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `8aaf5f50984b6f7afedfce8b624e6782faebc1ba858153bea1a5c7b7155ceaa7` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/__init__.py` | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.js` | `47e3dd2933cd884216a24847fee3a3e7a3777ab2a72656c977b9a5d2d0c6abad` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.json` | `644ec7b2ae8b58a82cb99d78ae5aed045f9e3c66de35a85e6fb7ed38f7a302a5` |
| `erp_workspace_ui/workspace_registry.py` | `51c638ff4860678d76aae586a87c96ea2db5bc4683a753136a7cf3c275fd1774` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `fe4408875be277ab88919f44309bfd4e18dc98d8f81472d6c96c02aa1fae0de1` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `9d68daf24c45e9ae1abc9dbf3a3fa9e147d303cd703b2ed741a216c56f68a845` |

Smoke, test, and package files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W8B behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Movement Visibility remains available at `/desk/warehouse-console-worklist/movement-visibility`.
- Movement Review is available at `/desk/warehouse-console-movement/<encoded-context>`.
- Movement Review loads from W8A row drilldown and from direct custom route URL.
- Movement Review survives browser reload and repeated route navigation without duplicate Warehouse shells.
- Movement Review uses only custom Warehouse routes for Back and related Stock Posture navigation.
- Refresh reloads the W8B payload without creating duplicate shells.
- Restricted, unavailable, and malformed contexts stay inside the custom Warehouse shell with safe owner-facing copy.
- The route exposes movement purpose/type, posting date/time, source/target warehouses, direction, item count, quantity summary, grouped item lines, and safe custom Stock Posture routes.
- The route does not expose native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, or Purchase Order routes to normal Warehouse users.
- Warehouse Search / Quick Find remains inactive in W8B.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W8B smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W8B service posture:

- Uses controlled Warehouse service method `get_warehouse_movement_review`.
- Requires Warehouse role access.
- Accepts a bounded encoded context.
- Uses submitted Stock Entry as the movement parent source.
- Uses Stock Entry Detail only for bounded operational line summaries.
- Applies permission fallbacks and safe unavailable/restricted states.
- Keeps response sizes bounded.
- Does not use Stock Ledger native report or raw Stock Ledger Entry rows.

Allowed W8B data concepts:

- Movement id.
- Movement purpose/type.
- Posting date and posting time.
- Source warehouse.
- Target warehouse.
- Direction label.
- Posted/submitted docstatus label.
- Item count.
- Quantity summary.
- Item code and item name.
- Stock UOM and operational quantity.
- Related custom Warehouse Stock Posture route.
- Freshness timestamp.

Excluded W8B data concepts:

- Stock value.
- Valuation rate.
- Incoming rate.
- Outgoing rate.
- Basic rate.
- Amount.
- Base amount.
- Transfer price.
- Stock queue.
- GL, accounting, cost, profit, margin, taxes, billing, payment, landed cost, or commercial pricing.
- Native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, or Purchase Order route targets.
- Raw framework errors in owner-facing copy.
- Quick Find or generic Warehouse search.

## 6. Explicitly Excluded Actions

W8B remains read-only. It must not introduce:

- Stock Entry creation.
- Stock Entry submission.
- Stock Entry cancellation or amendment.
- Stock Reconciliation creation or submission.
- Transfer creation or transfer execution.
- Purchase Receipt creation or submission.
- Delivery Note creation or submission.
- Pick List creation or submission.
- Reservation or unreservation.
- Allocation.
- Serial or batch assignment.
- Cycle count or physical inventory posting.
- Pick, pack, ship, dispatch, receive, issue, post, submit, cancel, amend, close, approve, reject, reconcile, reserve, or unreserve actions.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, print, barcode scan, AI, or workflow approval behavior.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

Disabled fake execution buttons are also excluded.

## 7. Protected Runtime Files

W8B runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/__init__.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_movement/warehouse_console_movement.json`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

W8B test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w8b_movement_review_smoke.js`

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
- W8A Movement Visibility route ownership.
- W8B Movement Review route ownership.
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

Recommended next phase: W8C docs-only transfer visibility decision or W9 docs-only inventory operations cockpit review.

W8C candidate:

- `/desk/warehouse-console-worklist/transfer-visibility`
- Read-only transfer posture and transfer exceptions.
- Custom Warehouse routes only.
- No transfer creation, transfer issue, transfer receipt, reservation, reconciliation, or Stock Entry lifecycle controls.

W9 candidate:

- A design-only review of the Warehouse landing information architecture now that inbound, outbound, stock exception, stock posture, movement visibility, and movement review all exist.
- Could rationalize navigation, section density, and premium visual hierarchy before adding more operational surfaces.

W8C or W9 must start with docs-only design because transfer posture and consolidated inventory operations are close to stock execution and valuation/report surfaces.

## 10. Docs-Only Closure

This W8B closure is documentation only.
