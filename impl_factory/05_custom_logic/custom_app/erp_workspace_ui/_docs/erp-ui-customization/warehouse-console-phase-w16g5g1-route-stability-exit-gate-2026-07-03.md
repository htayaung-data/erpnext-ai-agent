# W16G5H Route Stability Exit Gate

Date: 2026-07-03

## Scope
W16G5H closes the W16G5G route-stability regression fix with source assertions, authenticated live browser verification, and documentation correction. This phase does not add business workflow behavior.

## What Was Verified
- Overview first-load route renders the final Warehouse Console shell without a persistent loading placeholder.
- Returns Work Hub first-load route renders without `renderReturnsWorkHubPagePayload is not defined`.
- Stock Exceptions first-load route does not retain a stale Returns or Warehouse loading shell.
- Internal Transfer first-load route renders the custom workflow page without helper errors.
- Cycle Count first-load route renders the custom workflow page without helper errors.
- Receiving Review and Picking Review first-load routes still render their detail shells.
- Unsupported worklist slugs render the controlled unavailable-worklist fallback.

## Source Assertions Added
W9A source/static coverage now checks:
- Warehouse wrappers contain first-paint route loading shells.
- Warehouse wrappers prefer the active Frappe page wrapper before any global body fallback.
- Warehouse wrappers refuse to write loading placeholders into `document.body` / `#body`.
- Central Warehouse renderer removes stale `[data-warehouse-route-loading]` shells after the real page renders.
- Returns, Internal Transfer, and Cycle Count render through `replaceWarehouseRouteHost(viewState, $root)` instead of replacing the whole page body.
- Returns, Internal Transfer, and Cycle Count payload renderers exist exactly once.
- Returns, Internal Transfer, and Cycle Count route renderers exist exactly once.
- Existing stale-response markers remain present for the three custom workflow routes.

## Sidecar Finding Resolved
A sidecar quality gate found that Returns, Internal Transfer, and Cycle Count were still using whole-page body replacement for loading/error/ready renders. W16G5H replaced those nine calls with the shared route-host helper and added static assertions to prevent regression.

## Authenticated Live Browser Smoke
Authenticated browser smoke was completed after W16G5G live alignment using the Warehouse Manager account supplied by the owner for this verification. The smoke checked Overview, Returns, Stock Exceptions, Internal Transfer, Cycle Count, Receiving Review, Picking Review, and unsupported worklist fallback.

Result: passed. Each checked route had one expected final shell, zero visible route-loading placeholders, no error runtime shell, no login redirect, and no persistent `Loading Warehouse workspace...` placeholder text.

After the sidecar route-host fix, a focused live browser smoke was rerun for Returns, Internal Transfer, and Cycle Count. All three rendered one final ready shell, zero route-loading placeholders, and no error shell.

## Validation
- `node --check` passed for:
  - `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js`
  - `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- Live/source hash match was confirmed for the five W16G5G runtime files before W16G5H documentation.
- Backend cache was cleared, backend was restarted, and live ping returned `pong` during W16G5G live verification.
- Generated Python cache artifacts were removed from source after validation.

## Boundary
W16G5H does not introduce ERPNext document runtime, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, stock movement/posting, native ERP route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, Sales runtime, Procurement runtime, commit, push, protected gate, or Warehouse Workspace Closure.

## Next Step
Proceed to the next Warehouse closure gate only after owner confirms the first-click route behavior remains stable in manual browsing. W16H remains Warehouse Custom Workflow Closure only; ERPNext document execution and stock/accounting posting remain deferred to W17+.
