# Warehouse Console Phase W4A Inbound Receiving Visibility Baseline

Date: 2026-05-28

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W4A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime and smoke baseline commits:

- W4A inbound receiving visibility: `a0c80f3000c9ebace9b38be386ed30302050f4d3`
- W4A live smoke mode correction: `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca`

W4A extends the W3/W3A Warehouse baseline with read-only inbound receiving visibility:

- Warehouse Overview now includes inbound posture cards and preview rows.
- Warehouse sidebar includes `Inbound Receiving`.
- `/desk/warehouse-console-worklist/inbound-receiving` is now a protected product route.
- Inbound Receiving renders grouped read-only supplier receiving work.
- Submitted open Purchase Orders are used as expected inbound source data.
- Queue grouping covers overdue, due today, partially received, and expected soon receiving work.
- Warehouse Manager and Warehouse User can view the queue.
- Stock execution, Purchase Receipt creation, valuation, and native ERP escape remain closed.

## 2. Accepted Artifacts

Focused W4A artifacts:

- Source W4A smoke: `/tmp/warehouse-phase-w4a-source-20260528T074742Z/warehouse-w4a-inbound-20260528T074746Z/warehouse-w4a-inbound-summary.json`
- Live W4A smoke: `/tmp/warehouse-phase-w4a-live-rerun-20260528T101515Z/warehouse-w4a-inbound-20260528T101521Z/warehouse-w4a-inbound-summary.json`

Source protection artifacts:

- Source Sales freeze rerun: `/tmp/sales-freeze-protection-20260528T084620Z/sales-freeze-protection-summary.json`
- Source protected workspace gate: `/tmp/warehouse-phase-w4a-protected-source-20260528T093941Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live alignment root: `/tmp/warehouse-w4a-live-alignment-20260528T100732Z`
- Live source/hash proof: `/tmp/warehouse-w4a-live-alignment-20260528T100732Z/source-live-hashes-after.txt`
- Final protected live gate: `/tmp/warehouse-phase-w4a-protected-live-rerun-20260528T101944Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w4a-protected-live-rerun-20260528T101944Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Transient gate notes:

- First source Sales freeze failed once on a Sales detail `502`; focused Sales detail rerun passed, then full Sales freeze passed.
- First final protected live gate failed once on a Sales worklist/date-width check with a `502` console error; focused Sales worklists rerun passed, then full protected live gate passed.
- These transient failures were not W4A runtime regressions and were resolved by focused reruns before acceptance.

## 3. Live Runtime Hashes

Live alignment synced only approved W4A runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/workspace_registry.py` | `489a924efe48660c3299280806c4af8f3a172079f115375a269542c292693de0` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `86fce53d566888422175af5b0cae27b49a93972c2424de252377621fe71f344a` |
| `erp_workspace_ui/warehouse_console/service.py` | `79cba66d765c3b21e44db67d3291ceeafd96028cdf4b8261b96d78b01948b811` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `b7ad56f3902205857b6052f1028136674420107624cac7f3b92629a8362322a8` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `cfeb9acddc416bd96cb901d94953bcac9855ece1e98a0b0fd2205ff137741b9c` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js` | `bb1a465418256449c72b98111b7d82bdf72ae79e49a9c7c4004aabd9258ce571` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.json` | `b1e7b80fd679cd4ad76d8b35edb35850574765aed31745c333e9c97a9e6959b6` |

The W4A smoke correction in commit `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca` changed smoke behavior only. It was not live-aligned because smoke files are not runtime files.

## 4. Protected Behavior

Accepted W4A behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Warehouse Overview renders W3/W3A overview content plus inbound work posture.
- The Overview `Open inbound receiving` control routes to `/desk/warehouse-console-worklist/inbound-receiving`.
- Inbound Receiving renders one Warehouse shell for the `inbound-receiving` view.
- Inbound Receiving shows four summary cards: receiving due today, overdue receiving, partially received, and expected soon.
- Inbound Receiving shows safe filters for purchase order, supplier, warehouse, and receiving state.
- Inbound Receiving groups rows by receiving posture.
- Inbound rows show business-safe supplier, PO, warehouse, age/due state, remaining summary, received percent, and inline line details.
- Row line expansion remains inline and read-only.
- Warehouse Search / Quick Find remains inactive in W4A.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

Live W4A smoke confirmed both authorized users:

- `warehouse-manager`
- `warehouse-user`

## 5. Data Source And Query Posture

W4A service posture:

- Uses controlled Warehouse service methods.
- Uses read-only Purchase Order and Purchase Order Item data for expected inbound work.
- Limits inbound visibility to submitted, open receiving posture.
- Uses receipt progress as posture only, not as a receiving action path.
- Keeps response sizes bounded.
- Provides business-safe restricted, empty, loading, and unavailable states.

Allowed W4A data concepts:

- Purchase Order id.
- Supplier name.
- Target warehouse.
- Required or expected date posture.
- Received percentage.
- Remaining quantity summary.
- Item line summary for inline review.
- Group and filter labels.

Excluded W4A data concepts:

- Stock value.
- Valuation rate.
- Buying rates, amounts, taxes, payment terms, billing, or landed cost.
- Supplier pricing and commercial procurement controls.
- Raw framework errors in owner-facing copy.

## 6. Explicitly Excluded Actions

W4A remains read-only. It must not introduce:

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

W4A runtime files that are part of this baseline:

- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/__init__.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.json`

W4A test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w4a_inbound_smoke.js`

## 8. Regression Protection Expectations

Future Warehouse work must preserve:

- Warehouse W3/W3A landing behavior.
- W4A Inbound Receiving route ownership.
- Single Warehouse shell/header/sidebar rendering.
- No native ERP route escape for normal Warehouse users.
- No stock mutation or lifecycle actions.
- No valuation exposure.
- No Warehouse Quick Find/Search until separately designed and protected.
- Sales freeze protection.
- Procurement protected workspace behavior.
- Full protected workspace gate success after shared runtime changes.

Any future change to Warehouse `service.py`, Warehouse JS, shared registry, boot routing, or shared sidebar must rerun focused Warehouse smoke, Sales freeze, and full protected workspace gates before live alignment.

## 9. Recommended Next Phase

Recommended next phase: W4B read-only Receiving Review detail design and implementation, only after owner approval.

Recommended W4B route:

- `/desk/warehouse-console-receiving/<purchase-order>`

Recommended W4B scope:

- Read-only purchase order receiving posture page.
- Header with supplier, PO, target warehouse, due posture, and received percent.
- Item line table with ordered, received, remaining, target warehouse, and safe status.
- Optional read-only receipt history if safely linked and bounded.
- Optional quality indicator only, with no approval/rejection.
- Back to Inbound Receiving and Refresh actions only.

W4B must not include:

- `Receive` action.
- `Create Purchase Receipt` action.
- Native Purchase Order or Purchase Receipt form links.
- Stock posting or serial/batch capture.
- Valuation, billing, or supplier pricing data.

Owner decisions before W4B:

- Confirm the route `/desk/warehouse-console-receiving/<purchase-order>`.
- Confirm whether Purchase Manager gets read-only access to Warehouse receiving review, or Warehouse roles only.
- Confirm whether receipt history appears in W4B or later.
- Confirm whether quality indicators appear in W4B or later.

## 10. Docs-Only Closure

This W4A closure is documentation only.

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
