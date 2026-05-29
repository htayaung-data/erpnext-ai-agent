# Warehouse Console Phase W8A Movement Visibility Baseline

Date: 2026-05-29

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W8A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commit

Runtime acceptance commit:

- W8A movement visibility runtime: `c408b85b9f9bdab9ac66e0be375930e50a8bece3 feat: add warehouse movement visibility`

W8A extends the protected W7A Stock Posture Review baseline with read-only movement visibility:

- `/desk/warehouse-console-worklist/movement-visibility` is now a protected Warehouse product route.
- The route renders a premium read-only operations board for submitted Stock Entry movement summaries.
- The service method is `get_warehouse_movement_visibility_queue`.
- Movement rows are grouped into operational lanes such as transfers, receipts, issues, adjustments/repack, and needs review.
- Movement rows can drill only into custom Warehouse Stock Posture Review when item/warehouse context is available.
- Browser reload, direct route load, overview navigation, filters, refresh, and repeated navigation keep a single Warehouse shell.
- Warehouse Manager and Warehouse User are both accepted.
- No stock movement execution, valuation, native ERP escape, Quick Find/Search, or Sales/Procurement runtime change was introduced.

## 2. Accepted Artifacts

Focused W8A source artifacts:

- Source W8A smoke: `/tmp/warehouse-phase-w8a-source-20260529T161227Z/warehouse-w8a-movement-visibility-20260529T161234Z/warehouse-w8a-movement-visibility-summary.json`

Source protection artifacts:

- Standalone Sales freeze before protected source gate: `/tmp/sales-freeze-protection-20260529T161737Z/sales-freeze-protection-summary.json`
- Corrected Purchase User identity check: `purchase.ygn.01@meet.com`
- Final source protected gate: `/tmp/warehouse-phase-w8a-protected-source-20260529T165517Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w8a-live-hashes-20260529T171316Z.txt`
- Live W8A smoke: `/tmp/warehouse-phase-w8a-live-20260529T171614Z/warehouse-w8a-movement-visibility-20260529T171620Z/warehouse-w8a-movement-visibility-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w8a-protected-live-20260529T171713Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w8a-protected-live-20260529T171713Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Gate notes:

- The first protected source gate was run with an invalid Purchase User identity, `purchase.user@meet.com`, which is not an enabled site user.
- The enabled purchase users are `purchase.ygn.01@meet.com` and `purchase.mdy.01@meet.com`; W8A source and live protected gates passed with `purchase.ygn.01@meet.com`.
- A second source protected gate run was interrupted by the local command timeout while Phase 5D was starting. It had no Phase 5D artifact directory and was rerun with a longer timeout.
- No code changes were made for either gate note.

## 3. Live Runtime Hashes

Final live alignment synced only approved W8A runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `2e6902c1b87263835fe3892888e3885a8c5f3847017f9e2b04c87a945e33452b` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `dd82910a91d014c7ee79096fd62dbf90754b0d206fc0552f9ecaa4bac27a8b9b` |
| `erp_workspace_ui/workspace_registry.py` | `9829b6cd940e1c5b471e9dfa98a56fd58ff5a50575c47329e7dd6778ff59ec03` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `37cc8d601ffa8d6e287f181757c074ea96118a2aabdf7ef04f5964bcc79089a6` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `0dda6aedffdf62a946b68e738eec20e1aa480e4998a4cb065fa449b3d57765c3` |

Smoke, test, and package files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W8A behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Movement Visibility is available at `/desk/warehouse-console-worklist/movement-visibility`.
- Warehouse Overview exposes a user-visible route into Movement Visibility without adding Quick Find/Search.
- Movement Visibility loads from direct URL and from overview navigation.
- Movement Visibility renders one Warehouse shell for the `movement-visibility` view.
- The route shows movement summary cards, filters, grouped movement lanes, row expansion, empty states, and freshness.
- Filters remain bounded and read-only.
- Refresh reloads the W8A payload without creating duplicate shells.
- Row drilldowns, when present, target only custom Warehouse Stock Posture Review routes.
- No native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, or Purchase Order route is exposed to normal Warehouse users.
- Warehouse Search / Quick Find remains inactive in W8A.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W8A smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W8A service posture:

- Uses controlled Warehouse service method `get_warehouse_movement_visibility_queue`.
- Requires Warehouse role access.
- Uses submitted Stock Entry records only as the primary movement source.
- Uses Stock Entry Detail only for bounded operational summaries.
- Defaults to a bounded recent movement window.
- Applies safe permission fallbacks and safe unavailable/restricted states.
- Keeps response sizes bounded.
- Does not use Stock Ledger native report or raw Stock Ledger Entry rows.

Allowed W8A data concepts:

- Movement id.
- Movement purpose/type.
- Posting date and posting time.
- Source warehouse.
- Target warehouse.
- Direction label.
- Item count.
- Quantity summary.
- Sample item codes/names.
- Related custom Warehouse Stock Posture route.
- Freshness timestamp.

Excluded W8A data concepts:

- Stock value.
- Valuation rate.
- Incoming rate.
- Outgoing rate.
- Basic rate.
- Amount.
- Transfer price.
- Stock queue.
- GL, accounting, cost, profit, margin, taxes, billing, payment, or commercial pricing.
- Native Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Item, Warehouse, Purchase Receipt, Delivery Note, Sales Order, or Purchase Order route targets.
- Raw framework errors in owner-facing copy.
- Quick Find or generic Warehouse search.

## 6. Explicitly Excluded Actions

W8A remains read-only. It must not introduce:

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

W8A runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

W8A test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w8a_movement_visibility_smoke.js`

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

Recommended next phase: W8B docs-only movement review detail decision before implementation, or W8C docs-only transfer visibility decision if the owner wants transfer posture next.

W8B candidate:

- `/desk/warehouse-console-movement/<encoded-context>`
- Read-only review for one movement summary or one item/warehouse movement context.
- Custom Warehouse route targets only.
- No Stock Entry native form/list/report link.

W8C candidate:

- `/desk/warehouse-console-worklist/transfer-visibility`
- Read-only transfer posture and transfer exceptions.
- No transfer creation, transfer issue, transfer receipt, reservation, or reconciliation.

W8B/W8C must start with docs-only design because movement detail and transfer posture are closer to stock execution and valuation/report surfaces.

## 10. Docs-Only Closure

This W8A closure is documentation only.

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
