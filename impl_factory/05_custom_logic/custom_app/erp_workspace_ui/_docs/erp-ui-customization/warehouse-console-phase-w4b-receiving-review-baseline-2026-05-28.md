# Warehouse Console Phase W4B Receiving Review Baseline

Date: 2026-05-28

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W4B runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime, live-data repair, and smoke baseline commits:

- W4B receiving review visibility: `8fee1a7aa2e4a9a8d4e9055a37abcc9a4771c75c`
- W4B live-data receiving line repair: `ca3508efd0123dda085e111822e08f667a469684`
- W4B live smoke direct-order correction: `0abed2f826b14909ec59182f126bdca5ebabf5bd`

W4B extends W4A inbound visibility with read-only receiving review:

- Inbound Receiving rows now drill into `/desk/warehouse-console-receiving/<purchase-order>`.
- The receiving page renders supplier, purchase order, target warehouse, received percent, due posture, item lines, and receipt-history tab shell.
- Item lines show ordered, received, remaining, UOM, target warehouse, required date, and safe status.
- Receipt history is read-only and bounded when permissions expose linked Purchase Receipt data.
- Warehouse Manager and Warehouse User can use the route.
- The route stays inside the Warehouse product surface and uses managed Warehouse service methods.
- Stock execution, Purchase Receipt creation, valuation, native ERP escape, Quick Find, and Warehouse search remain closed.

## 2. Accepted Artifacts

Focused W4B artifacts:

- Source W4B smoke: `/tmp/warehouse-phase-w4b-source-20260528T121502Z/warehouse-w4b-receiving-20260528T121510Z/warehouse-w4b-receiving-summary.json`
- Source W4B smoke after live-data repair: `/tmp/warehouse-phase-w4b-source-fix-20260528T130345Z/warehouse-w4b-receiving-20260528T130349Z/warehouse-w4b-receiving-summary.json`
- Source W4B smoke after smoke direct-order correction: `/tmp/warehouse-phase-w4b-smoke-fix-source-20260528T133211Z/warehouse-w4b-receiving-20260528T133215Z/warehouse-w4b-receiving-summary.json`
- Final live W4B smoke: `/tmp/warehouse-phase-w4b-live-final-20260528T133251Z/warehouse-w4b-receiving-20260528T133256Z/warehouse-w4b-receiving-summary.json`

Source protection artifacts:

- Source Sales freeze after W4B implementation: `/tmp/sales-freeze-protection-20260528T121619Z/sales-freeze-protection-summary.json`
- Source protected workspace gate after W4B implementation: `/tmp/warehouse-phase-w4b-protected-source-rerun-20260528T123649Z/protected-workspace-gate-summary.json`
- Source Sales freeze after live-data repair: `/tmp/sales-freeze-protection-20260528T130449Z/sales-freeze-protection-summary.json`
- Source protected workspace gate after live-data repair: `/tmp/warehouse-phase-w4b-fix-protected-source-20260528T130946Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Initial live alignment root: `/tmp/warehouse-w4b-live-alignment-20260528T125758Z`
- Final live alignment root: `/tmp/warehouse-w4b-live-alignment-fix-20260528T132850Z`
- Final live source/hash proof: `/tmp/warehouse-w4b-live-alignment-fix-20260528T132850Z/live-alignment.log`
- Final protected live gate: `/tmp/warehouse-phase-w4b-protected-live-20260528T133436Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w4b-protected-live-20260528T133436Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Transient and repaired gate notes:

- First protected source gate used the wrong Purchase User credential (`purchase.user@meet.com`) and failed before completing the Procurement user regression. Existing docs and focused rerun confirmed the correct user is `purchase.ygn.01@meet.com`; the full protected source gate then passed.
- First live W4B smoke exposed a real live-data gap: Warehouse roles could read the Purchase Order but direct child-table `Purchase Order Item` reads returned zero item lines. W4B now falls back through the readable parent Purchase Order document and still checks read permission.
- Second live W4B smoke exposed a smoke-only issue: direct-route validation used source fixture `PO-OVERDUE`, which does not exist as a live open PO. The smoke now reuses the actual Purchase Order selected from the live inbound queue.
- These repairs were committed and protected before final live acceptance.

## 3. Live Runtime Hashes

Final live alignment synced only approved W4B runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/workspace_registry.py` | `e564cf5915e242f24d5524443fd44bcd9ed4b133326f318e26c7ca313be120af` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `96c7b6e1d957e22f26c7ece675d07e5e312d45789f0eaa25ae7e7d396fdf279e` |
| `erp_workspace_ui/warehouse_console/service.py` | `66719f459524c58a2488da83e504c532ea3c6763536639a5a3c730b079fd7af6` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `58eb1f02866c005fca897cc73ab0427e0a16aa6e2cd5c67523456cf4db778129` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `4fa3104591da6b149e79cdcf52a8ccf44a548acf46bd31c57854a46c1136a035` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js` | `9dc67aeabf5340c2577833931a3e1bf50dda72e95254f8a1eda2aa6a07604c5b` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.json` | `dd08b8f3911f6315f38d919d31998af27a3bb8ab353f5e6d748515bc56236227` |

The smoke correction in commit `0abed2f826b14909ec59182f126bdca5ebabf5bd` changed smoke behavior only. It was not live-aligned because smoke files are not runtime files.

## 4. Protected Behavior

Accepted W4B behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Inbound Receiving remains available at `/desk/warehouse-console-worklist/inbound-receiving`.
- Inbound rows expose a productized `View details` control.
- `View details` routes to `/desk/warehouse-console-receiving/<purchase-order>`.
- Receiving Review renders one Warehouse shell for the `receiving-review` view.
- Receiving Review shows four summary cards: receiving state, received percent, open lines, and item count.
- Receiving Review shows read-only item lines when the user can read the Purchase Order parent, even if direct child-table access is unavailable.
- Receiving Review includes `Item Lines` and `Receipt History` tabs.
- Receiving Review actions are limited to `Back to inbound receiving` and `Refresh`.
- Refresh, browser reload, direct route, and viewport remount paths keep a single Warehouse shell.
- Warehouse Search / Quick Find remains inactive in W4B.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W4B smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W4B service posture:

- Uses controlled Warehouse service method `get_warehouse_receiving_review`.
- Requires Warehouse role access.
- Requires read access to the Purchase Order.
- Limits review to submitted open receiving posture.
- Reads item lines from `Purchase Order Item` when available.
- Falls back to the readable parent Purchase Order `items` child table when direct child-table reads are unavailable.
- Uses Purchase Receipt and Purchase Receipt Item only for bounded read-only history when readable.
- Keeps response sizes bounded.
- Provides business-safe restricted, empty, loading, unavailable, and error states.

Allowed W4B data concepts:

- Purchase Order id.
- Supplier name.
- Target warehouse.
- Required or expected date posture.
- Received percentage.
- Remaining quantity summary.
- Item code and item name.
- Ordered, received, and remaining quantity.
- UOM.
- Receipt id, posting date, status, item count, and quantity summary when history is readable.

Excluded W4B data concepts:

- Stock value.
- Valuation rate.
- Buying rates, amounts, taxes, payment terms, billing, or landed cost.
- Supplier pricing and commercial procurement controls.
- Raw framework errors in owner-facing copy.

## 6. Explicitly Excluded Actions

W4B remains read-only. It must not introduce:

- Purchase Receipt creation.
- Purchase Receipt submission.
- Stock Entry creation.
- Stock Entry submission.
- Delivery Note creation or submission.
- Stock Reconciliation creation or submission.
- Receive, post, submit, cancel, amend, close, approve, reject, reconcile, reserve, or unreserve actions.
- Serial or batch assignment.
- Quality Inspection creation, approval, rejection, or reading entry.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, or AI behavior.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

Disabled fake execution buttons are also excluded. If an execution action is not approved, it should not appear as an owner-facing disabled promise.

## 7. Protected Runtime Files

W4B runtime files that are part of this baseline:

- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/__init__.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.json`

W4B test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w4b_receiving_smoke.js`

## 8. Regression Protection Expectations

Future Warehouse work must preserve:

- Warehouse W3/W3A landing behavior.
- W4A Inbound Receiving route ownership.
- W4B Receiving Review route ownership.
- Single Warehouse shell/header/sidebar rendering.
- No native ERP route escape for normal Warehouse users.
- No stock mutation or lifecycle actions.
- No valuation exposure.
- No Warehouse Quick Find/Search until separately designed and protected.
- Sales freeze protection.
- Procurement protected workspace behavior.
- Full protected workspace gate success after shared runtime changes.

Any future change to Warehouse `service.py`, Warehouse JS, shared registry, boot routing, shared sidebar, or protected smoke behavior must rerun focused Warehouse smoke, Sales freeze, and full protected workspace gates before live alignment.

## 9. Recommended Next Phase

Recommended next phase: W5 docs-only outbound/picking visibility design, before implementation.

W5 should research and design read-only outbound warehouse visibility only. Recommended candidate route:

- `/desk/warehouse-console-worklist/outbound-picking`

Recommended W5 scope:

- Read-only outbound pick/dispatch posture from safe submitted source documents.
- Overview outbound posture cards.
- Grouped outbound queue by overdue, due today, ready to pick, blocked, and expected soon where data supports it.
- Productized drilldown only if owner approves after design.
- Back and Refresh actions only.

W5 must not include:

- Pick List creation or submission.
- Stock Entry creation or submission.
- Delivery Note creation or submission.
- Pick, pack, ship, dispatch, reserve, unreserve, scan, serial assignment, batch assignment, submit, cancel, amend, or reconcile actions.
- Native ERPNext form/report/list links.
- Valuation, pricing, billing, payment, or tax data.
- Warehouse Quick Find/Search unless separately approved.

Owner decisions before W5 implementation:

- Confirm outbound visibility should come before stock-on-hand/location visibility.
- Confirm the first W5 route name.
- Confirm whether outbound drilldown belongs in W5 or a later W5B phase.
- Confirm whether Warehouse Manager and Warehouse User both see identical outbound visibility.

## 10. Docs-Only Closure

This W4B closure is documentation only.

It does not:

- Change runtime code.
- Change tests.
- Change smoke scripts.
- Change live files.
- Run live alignment.
- Touch `ui_smoke/sales_final_acceptance_audit.js`.

Required docs-only validation:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
