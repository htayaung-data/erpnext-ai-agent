# Warehouse Console Phase W9A Cockpit Information Architecture Baseline

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W9A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Accepted commits:

- W9 docs-only information architecture plan: `5e48154b5caae89988b3ecec932294bee806156d docs: plan warehouse cockpit information architecture`
- W9A runtime implementation: `97b7f063a8ec9f248e6aaea63a8b5f4444f68336 feat: polish warehouse cockpit information architecture`

W9A implements the W9 recommendation to polish `/desk/warehouse-console` before adding another Warehouse route:

- The Warehouse home is now a cockpit, not a stack of phase panels.
- The cockpit has a command header, read-only/status chips, Warehouse Pulse metrics, Start Here cards, Work To Do, Risks To Resolve, Movement To Understand, and a read-only guardrail footer.
- Existing protected Warehouse starts remain accepted:
  - `/desk/warehouse-console-worklist/inbound-receiving`
  - `/desk/warehouse-console-worklist/outbound-picking`
  - `/desk/warehouse-console-worklist/stock-exceptions`
  - `/desk/warehouse-console-worklist/movement-visibility`
- W9A did not add a backend method, new route family, transfer visibility route, sidebar shared-runtime change, stock action, valuation field, native ERP escape, or Warehouse Quick Find/Search.
- Warehouse Manager and Warehouse User are both accepted.

## 2. Accepted Artifacts

Focused W9A source artifacts:

- Source W9A cockpit smoke: `/tmp/warehouse-phase-w9a-source-20260530T054904Z/warehouse-w9a-cockpit-20260530T054911Z/warehouse-w9a-cockpit-summary.json`

Source protection artifacts:

- Standalone Sales freeze before protected source gate: `/tmp/sales-freeze-protection-20260530T055023Z/sales-freeze-protection-summary.json`
- Source protected gate: `/tmp/warehouse-phase-w9a-protected-source-20260530T055502Z/protected-workspace-gate-summary.json`

Live alignment and final protection artifacts:

- Live source/hash proof: `/tmp/warehouse-w9a-live-hashes-20260530T061504Z.txt`
- Final live W9A cockpit smoke: `/tmp/warehouse-phase-w9a-live-20260530T061631Z/warehouse-w9a-cockpit-20260530T061637Z/warehouse-w9a-cockpit-summary.json`
- Final protected live gate: `/tmp/warehouse-phase-w9a-protected-live-20260530T063811Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected live gate: `/tmp/warehouse-phase-w9a-protected-live-20260530T063811Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Gate results:

- Source W9A cockpit smoke passed for Warehouse Manager and Warehouse User.
- Source protected workspace gate passed.
- Live W9A cockpit smoke passed for Warehouse Manager and Warehouse User across desktop, laptop, and mobile viewport coverage.
- Final protected live gate passed with `overall_status=pass`, 18 protected commands, and no failed command.

## 3. Live Runtime Hashes

Final live alignment synced only the approved W9A runtime file. Source and live hashes matched after alignment:

| Runtime file | SHA-256 |
| --- | --- |
| `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` | `a243a3c5d13637319cd3923726cf164bd8afdc5078b73cb8a49fe42461a4ef5d` |

Smoke, test, package, and Docker runner files were not live-aligned because they are source protection files, not runtime files.

## 4. Protected Behavior

Accepted W9A behavior:

- Warehouse operational users still land on `/desk/warehouse-console`.
- `/desk/warehouse-console` now presents a premium Warehouse Cockpit with clear start points instead of phase-stacked panels.
- The cockpit separates current Warehouse work into three owner-facing areas:
  - Work To Do: inbound receiving and outbound picking.
  - Risks To Resolve: stock exceptions and stock posture context entry points.
  - Movement To Understand: submitted movement visibility and movement review entry points.
- Warehouse Pulse metrics are derived from existing read-only overview data.
- Start Here cards route only to existing protected custom Warehouse routes.
- Existing top-level Warehouse route names and worklist routes remain stable.
- Existing receiving, picking, stock exception, stock posture, movement visibility, and movement review route families remain protected.
- Cockpit rendering is covered by a focused W9A smoke with source override coverage.
- Warehouse Search / Quick Find remains inactive.
- Sales Console freeze protection remains green.
- Procurement Console protected gate remains green.

## 5. Data And UI Scope

W9A is an information-architecture and presentation phase.

Allowed W9A concepts:

- Read-only Warehouse cockpit copy.
- Existing overview metrics and counts.
- Existing protected Warehouse route starts.
- Existing Warehouse freshness/status labels.
- Existing inbound, outbound, exception, stock posture, and movement labels.
- Read-only operational guidance for where to start.

Excluded W9A concepts:

- New backend Warehouse service methods.
- New Warehouse route families.
- Transfer visibility route.
- Native ERPNext form, list, report, or workspace route targets.
- Stock Ledger, Stock Balance, Stock Reconciliation, Stock Entry native report/form/list exposure.
- Purchase Receipt, Delivery Note, Pick List, Item, Warehouse, Sales Order, or Purchase Order native route escape for normal Warehouse users.
- Stock value, valuation rate, incoming rate, outgoing rate, basic rate, amount, base amount, transfer price, GL, accounting, cost, profit, margin, taxes, billing, payment, landed cost, or commercial pricing.
- Warehouse Quick Find or generic search.
- Developer-facing visible copy.

## 6. Explicitly Excluded Actions

W9A remains read-only. It must not introduce:

- Stock Entry creation, submission, cancellation, or amendment.
- Transfer creation or transfer execution.
- Stock Reconciliation creation or submission.
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
- Disabled fake execution buttons.

## 7. Protected Runtime Files

W9A runtime file that is part of this baseline:

- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`

W9A test and smoke files that protect source behavior but are not live-aligned:

- `ui_smoke/package.json`
- `ui_smoke/run_playwright_docker.sh`
- `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`

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
- W9A Cockpit information architecture and top-level route stability.
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

Recommended next control-agent phase: W9B docs-only cockpit usability review, unless the owner explicitly prioritizes W8C Transfer Visibility.

W9B candidate:

- Review the live W9A cockpit screenshots and owner walkthrough feedback.
- Tighten section density, copy, visual hierarchy, mobile stacking, and empty-state language.
- Stay docs-only unless owner approves a small visual polish implementation.
- No new Warehouse workflow route.

W8C candidate:

- Docs-only transfer visibility decision before implementation.
- Proposed route would be `/desk/warehouse-console-worklist/transfer-visibility`.
- Must remain read-only and custom-route-only.
- Must not introduce transfer creation, transfer issue, transfer receipt, reservation, reconciliation, Stock Entry lifecycle controls, valuation/accounting/commercial exposure, native escape, Quick Find/Search, or Sales/Procurement runtime changes.
