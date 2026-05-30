# Warehouse Console Phase W8C Transfer Visibility Baseline

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W8C runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Accepted commits:

- W8C docs-only transfer visibility plan: `df5f07e257cb0528f67378db9ad242cbd61690c9 docs: plan warehouse transfer visibility`
- W8C runtime implementation: `97cf78485ba5c1cf371dcce8348bab222755df37 feat: add warehouse transfer visibility`

W8C extends the protected W8A/W8B movement visibility baseline with a read-only transfer posture board:

- `/desk/warehouse-console-worklist/transfer-visibility` is now a protected Warehouse product route.
- `get_warehouse_transfer_visibility_queue` returns a bounded, read-only transfer posture payload.
- The source is submitted Stock Entry material-transfer records and bounded Stock Entry Detail summaries only.
- Transfer rows are grouped into Direct Transfers, Transit Related, Needs Review, and Recently Posted.
- The UI renders a premium custom Transfer Visibility board with summary cards, transfer-posture filters, source -> target warehouse direction, grouped rows, safe empty/restricted/unavailable states, Refresh, and custom drilldowns only.
- Optional drilldowns point only to existing custom Warehouse routes:
  - `/desk/warehouse-console-movement/<encoded-context>`
  - `/desk/warehouse-console-stock-posture/<encoded-context>`
- Warehouse Manager and Warehouse User are both accepted.
- No transfer execution, Stock Entry lifecycle controls, Stock Ledger/Stock Balance exposure, valuation/accounting/commercial exposure, native ERP escape, Warehouse Quick Find/Search, Sales runtime change, or Procurement runtime change was introduced.

## 2. Accepted Artifacts

Focused W8C source artifacts:

- Source W8C transfer visibility smoke: `/tmp/warehouse-phase-w8c-source-20260530T120445Z/warehouse-w8c-transfer-visibility-20260530T120452Z/warehouse-w8c-transfer-visibility-summary.json`

Source protection artifacts:

- Standalone Sales freeze before protected source gate: `/tmp/sales-freeze-protection-20260530T120534Z/sales-freeze-protection-summary.json`
- Focused Sales worklists rerun after transient protected-gate failure: `/tmp/warehouse-phase-w8c-sales-worklists-rerun-20260530T121227Z`
- Focused Procurement Phase 5C rerun after transient protected-gate failure: `/tmp/warehouse-phase-w8c-procurement-phase5c-rerun-20260530T122523Z/summary.json`
- Final source protected gate: `/tmp/warehouse-phase-w8c-protected-source-final-20260530T122616Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected source gate: `/tmp/warehouse-phase-w8c-protected-source-final-20260530T122616Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w8c-live-hashes-20260530T124228Z.txt`
- Final live W8C transfer visibility smoke: `/tmp/warehouse-phase-w8c-live-20260530T124531Z/warehouse-w8c-transfer-visibility-20260530T124535Z/warehouse-w8c-transfer-visibility-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w8c-protected-live-20260530T124609Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w8c-protected-live-20260530T124609Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Gate note:

- Two source protected-gate attempts stopped on unrelated Sales/Procurement smoke symptoms. The focused Sales worklists and Procurement Phase 5C reruns passed, and the final protected source gate passed with `overall_status=pass`, 18 protected commands, and no failed command. No W8C runtime patch was made for those transient gate symptoms.
- The live restart reset the SSH connection after containers started. Container health and `/api/method/ping` were verified before live smoke.

## 3. Live Runtime Hashes

Final live alignment synced only approved W8C runtime files. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/warehouse_console/service.py` | `5b2f4ef1c657d0eb9ed484434c5ae20d08623907b72bdd2feb4d511cccd94a13` |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `210d5c1903c774686d030b65840c3f973998c0a5c367c32db549bdd61aa1b764` |
| `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js` | `47c8ee94395eced450912a4e7e5b5489eb94c1d29ea326fa40af6bbb193ed0f5` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `b2955d71221e601a5c500358fc526b20dafe5c3905b2ce0a920af4faac5363db` |
| `erp_workspace_ui/workspace_registry.py` | `e405e95e9c33daa0ae7eef15e925d6ccec3666f3a7b99d132007c99f66501221` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `fb0cf62e37eb91cfa38684470c1023466359b8b142b243640d0a7dd908817629` |

Smoke, test, package, and Docker runner files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W8C behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- Transfer Visibility is available at `/desk/warehouse-console-worklist/transfer-visibility`.
- The W9A cockpit can route to Transfer Visibility under Movement To Understand without disturbing existing inbound, outbound, exception, posture, and movement starts.
- Transfer Visibility loads from direct custom route URL.
- Transfer Visibility survives browser reload and repeated route navigation without duplicate Warehouse shells.
- Repeated same-route navigation does not make unnecessary transfer service calls.
- Explicit Refresh remains a real forced reload.
- Transfer Visibility keeps restricted, unavailable, and error states inside the custom Warehouse shell.
- Transfer rows show transfer id, posting date/time, source warehouse, target warehouse, source -> target direction, item count, quantity summary, and safe posture labels.
- Transfer rows expose `Review movement` and `Review stock posture` only when safe custom Warehouse route contexts exist.
- Desktop, laptop, and mobile smoke screenshots are captured for initial transfer visibility and drilldown states.
- Warehouse Search / Quick Find remains inactive.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

## 5. Data Source And Query Posture

W8C service posture:

- Uses controlled Warehouse service method `get_warehouse_transfer_visibility_queue`.
- Requires authentication and Warehouse role access.
- Uses submitted records only: `docstatus = 1`.
- Uses transfer-like Stock Entry purpose, starting with Material Transfer.
- Keeps query horizon and result limits bounded.
- Uses Stock Entry Detail only for bounded operational line summaries.
- Applies permission fallbacks and safe unavailable/restricted states.
- Does not use Stock Ledger native report or raw Stock Ledger Entry rows.
- Does not expose native route URLs.

Allowed W8C data concepts:

- Transfer id.
- Posting date and posting time.
- Source warehouse.
- Target warehouse.
- Transfer posture.
- Direct/transit/needs-review grouping.
- Item count.
- Item code and item name in bounded summaries.
- Stock UOM and operational quantity.
- Related custom Movement Review route.
- Related custom Stock Posture route.
- Freshness timestamp.

Excluded W8C data concepts:

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

W8C remains read-only. It must not introduce:

- Transfer creation.
- Transfer issue.
- Transfer receipt.
- Transfer completion.
- Stock Entry creation.
- Stock Entry submission.
- Stock Entry cancellation or amendment.
- Stock Reconciliation creation or submission.
- Purchase Receipt creation or submission.
- Delivery Note creation or submission.
- Pick List creation or submission.
- Reservation or unreservation.
- Allocation.
- Serial or batch assignment.
- Cycle count or physical inventory posting.
- Pick, pack, ship, dispatch, receive, issue, post, submit, cancel, amend, close, complete, approve, reject, reconcile, reserve, or unreserve actions.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, print, barcode scan, AI, or workflow approval behavior.
- Native ERPNext form, report, list, or workspace escape for normal Warehouse users.

Disabled fake execution buttons are also excluded.

## 7. Protected Runtime Files

W8C runtime files that are part of this baseline:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`

W8C test and smoke files that protect source behavior but are not live-aligned:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
- `erp_workspace_ui/tests/test_workspace_registry_contracts.py`
- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w8c_transfer_visibility_smoke.js`

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
- W8C Transfer Visibility route ownership.
- W9A Cockpit information architecture and top-level route stability.
- Single Warehouse shell/header/sidebar rendering.
- No native ERP route escape for normal Warehouse users.
- No stock mutation or lifecycle actions.
- No transfer execution controls.
- No valuation/accounting/commercial exposure.
- No Warehouse Quick Find/Search until separately designed and protected.
- Sales freeze protection.
- Procurement protected workspace behavior.
- Full protected workspace gate success after shared runtime changes.

Any future change to Warehouse `service.py`, Warehouse JS, shared registry, boot routing, shared sidebar, or protected smoke behavior must rerun focused Warehouse smoke, Sales freeze, and full protected workspace gates before live alignment.

## 9. Recommended Next Phase

Recommended next phase: W10 docs-only Warehouse operations review and phase boundary decision.

W10 should decide whether to:

- Pause Warehouse buildout for a counterpart audit of the full W3-W8C protected surface.
- Polish W9A/W8C cockpit density and movement/transfer grouping based on live owner feedback.
- Design the next read-only surface only if it has clear business value and does not overlap with transfer execution.

Do not start transfer execution, receiving execution, picking execution, reservation, reconciliation, or valuation/accounting work without a separate owner-approved design and protected gate plan.
