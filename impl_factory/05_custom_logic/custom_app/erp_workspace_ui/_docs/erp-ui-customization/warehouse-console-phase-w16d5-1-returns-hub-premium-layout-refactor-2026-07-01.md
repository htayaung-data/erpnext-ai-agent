# Warehouse Console Phase W16D5.1 - Returns Hub Premium Layout Refactor

Date: 2026-07-01
Status: source implementation pending live/manual acceptance

## Scope

W16D5.1 refactors the Warehouse Overview `Returns work hub` from three dense side-by-side workflow form cards into a compact selector plus single full-width workbench layout.

The layout intent is:
- keep the three business lanes visible at the top: Customer return intake, Supplier return candidate, and Return decisions;
- show only compact lane summaries in the selector cards;
- render one active workbench panel at a time;
- keep customer return intake selected by default;
- keep supplier return and manager decisions hidden until selected;
- preserve existing save and manager-decision selectors, methods, and custom-record behavior.

## Boundary

This phase is UI layout and smoke coverage only. It does not introduce handoff activation, customer or supplier notification, native ERPNext routing, Sales Return, Credit Note, Delivery Note, return Purchase Receipt, Purchase Invoice return, debit note, Stock Entry, Stock Ledger, Stock Balance, Stock Reconciliation, Stock Reservation, stock movement, valuation/accounting/commercial exposure, or Sales/Procurement runtime mutation.

## Validation Required

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- W9A smoke selector checks for default customer panel, supplier switch, and decisions switch
- live asset marker check after live alignment

## Owner Manual Check

Owner should manually inspect the Warehouse Overview Returns hub after live alignment and confirm:
- top selector cards look clean/minimal;
- only one workbench panel is visible at a time;
- customer intake, supplier candidate, and return decisions are easy to switch;
- form fields align cleanly in the workbench;
- save buttons remain visually consistent and clearly attached to the active panel;
- guardrail copy remains visible and does not imply ERP document creation.
