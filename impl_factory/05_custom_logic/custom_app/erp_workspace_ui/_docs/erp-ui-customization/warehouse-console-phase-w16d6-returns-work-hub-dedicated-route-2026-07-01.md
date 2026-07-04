# Warehouse Console Phase W16D6 - Returns Work Hub Dedicated Route

Date: 2026-07-01
Status: live aligned and owner manual accepted

## Scope

W16D6 moves active Returns work out of the Warehouse Overview and into the custom Warehouse worklist route:

- `/desk/warehouse-console-worklist/returns-work-hub`

Overview becomes summary/navigation only. The dedicated Returns page owns:

- Customer return intake custom draft save.
- Supplier return candidate custom draft save.
- Return manager posture controls.

## Design Decision

Overview answers: what needs attention?

Returns page answers: what can the Warehouse user or manager work now?

This keeps active operational controls out of Overview and matches standard ERP information architecture without adding any native ERPNext document route.

## Boundary

This phase does not add Sales Return, Credit Note, Delivery Note, return Purchase Receipt, Purchase Invoice return, debit note, supplier/customer notification, native ERP route exposure, Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Stock Reservation, stock movement/posting, valuation/accounting/commercial exposure, or Sales/Procurement runtime mutation.

The route remains a custom Warehouse Console route only.

## Validation Required

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- W9A smoke must prove Overview has summary/navigation only and the dedicated Returns page has the active workbench.

## Manual Check

Owner should confirm:

- Overview no longer looks like an action workbench for Returns.
- Overview has a clear Open Returns entry point.
- The dedicated Returns page loads the premium selector/workbench.
- Customer, supplier, and decision panels switch cleanly.
- No wording implies ERP document creation, stock movement, notification, or native route behavior.


## Acceptance Result

Owner manual check accepted on 2026-07-01.

Confirmed owner-facing behavior:

- Warehouse Overview is summary/navigation only for Returns.
- Active customer return intake, supplier return candidate, and return decision controls are no longer embedded in Overview.
- `Open Returns` navigates to `/desk/warehouse-console-worklist/returns-work-hub`.
- Dedicated Returns page loads the premium selector/workbench.
- Customer, Supplier, and Return decisions panels switch cleanly.
- Overview navigation uses neutral navigation styling, not save-control styling.

## Implementation Notes

- Added the custom worklist route key `returns_work_hub`.
- Added `returns-work-hub` route support to the Warehouse worklist page.
- Updated Warehouse Action Center return cards to route to the dedicated Returns page.
- Added a Returns entry to Start Warehouse Work and Warehouse fallback navigation.
- Replaced the active Overview workbench with a summary/navigation section.
- Added fail-fast route error rendering when the Returns page cannot load overview context.

## Validation Completed

Design workspace:

- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`: passed.
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`: passed.
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`: passed.
- `git diff --check HEAD`: passed.
- `python3 -m compileall -q erp_workspace_ui`: passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`: passed, 404 tests OK.
- Static W16D6 scan: route markers present; no native ERP route pattern; no notification/email/portal pattern.
- Cache artifact cleanup: clean.

Live alignment:

- Scoped live backup created: `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/.live_align_backups/w16d6_20260701112131`.
- Scoped live files aligned from the design workspace.
- Live JS syntax checks passed for Warehouse page, worklist page, and W9A smoke.
- Live targeted W16D6 registry/action-center tests passed: 4 tests OK.
- ERPNext site cache and website cache were cleared.
- Served asset marker check confirmed `returns-work-hub`, `data-warehouse-returns-overview-summary`, `warehouse-returns-overview-open-button`, `renderReturnsWorkHubPage`, and `data-warehouse-returns-page-error`.

Live full unit discovery was not used as W16D6 acceptance evidence because the live tree contains unrelated existing Procurement and older Warehouse metadata/test baseline gaps outside this scoped route move.

## Closure Boundary

W16D6 closes only the Returns IA move from Overview into a dedicated custom Warehouse route.

It does not approve commit, push, restart, protected gate, full Warehouse Workspace Closure, ERPNext document creation, Sales Return, Credit Note, Delivery Note, return Purchase Receipt, Purchase Invoice return, debit note, supplier/customer notification, native ERP route exposure, Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Stock Reservation, stock movement/posting, valuation/accounting/commercial exposure, or Sales/Procurement runtime mutation.
