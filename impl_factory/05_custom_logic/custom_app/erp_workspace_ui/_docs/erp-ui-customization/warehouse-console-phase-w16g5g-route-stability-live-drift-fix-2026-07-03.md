# W16G5G Route Stability + Live Drift Fix

Date: 2026-07-03

## Scope
W16G5G fixes Warehouse Console route stability defects found during closure-readiness review. This phase is limited to route wrappers, stale-response handling, first-paint safeguards, and smoke/static route assertions.

## Fixes
- Added lightweight first-paint loading shells to Warehouse Overview, worklist routes, Receiving Review, and Picking Review wrappers so first-click navigation does not present a blank white content area while the main Warehouse asset loads.
- Kept unsupported worklist slugs on a controlled unavailable route instead of falling through to Inbound Receiving.
- Aligned live runtime files with source for the affected route wrappers and central Warehouse renderer.
- Fixed Receiving and Picking detail stale-response guards that referenced `orde` instead of `order`.
- Added stale-response protection for Returns Work Hub, Internal Transfer workflow, and Cycle Count workflow async loaders so old responses cannot replace the current route after quick navigation.
- Added W9A smoke/static contract checks for first-paint route loading, unsupported worklist fallback, wrapper source contracts, and stale-response guard markers.

## Validation
- `git diff --check HEAD`: passed.
- `node --check` passed for:
  - `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js`
  - `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js`
  - `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`: passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`: passed, 411 tests OK.
- Focused static route-wrapper and stale-response checks: passed.
- Live runtime source/hash alignment for the five affected runtime files: passed.
- Backend cache cleared, backend container restarted, and live ping returned `pong`.

## Follow-Up Verification
Authenticated browser smoke was completed in W16G5H after owner supplied the Warehouse Manager credential for verification. First-load route checks passed for Overview, Returns, Stock Exceptions, Internal Transfer, Cycle Count, Receiving Review, Picking Review, and unsupported worklist fallback. Owner manual live verification may still be used as a business acceptance check, but the previous technical smoke gap is closed.

## Boundary
W16G5G does not introduce ERPNext document runtime, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, stock movement/posting, native ERP route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, Sales runtime, Procurement runtime, commit, push, protected gate, or Warehouse Workspace Closure.
