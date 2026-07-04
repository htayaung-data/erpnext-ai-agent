# Warehouse Console Phase W16G5A Security / Stability Hardening

Date: 2026-07-02

## Scope

W16G5A hardens the Warehouse Console after W16G4 UI/business-purpose cleanup. It focuses on permission scoping, stale-route stability, and owner-facing wording honesty before any Warehouse Workspace Closure decision.

This phase does not approve live alignment, restart, protected gates, commit, push, ERPNext document runtime, stock/accounting mutation, native ERP routes, notification/email/portal behavior, Sales runtime mutation, Procurement runtime mutation, or Warehouse Workspace Closure.

## Changes

- Quick Find stock-exception suggestions now require readable parent `Sales Order` access before any `Sales Order Item` result can expose item, warehouse, open quantity, or context token.
- Stock-exception child-row lookup is constrained to visible parent Sales Orders and rechecks parent membership before returning results.
- Test fixtures now honor list-style child-table filters so Quick Find tests exercise parent-constrained child scans realistically.
- Unsupported Warehouse worklist slugs now render a safe fallback shell with the requested slug escaped and a Back to overview action.
- The worklist wrapper preserves unknown slugs as `unsupported-worklist` instead of treating them as inbound receiving.
- Overview and Returns/Action Center wording no longer claims manager queues for pages that are custom workflow posture pages.
- W9A smoke coverage now includes unsupported worklist route fallback checks and no-service-call assertions for unsupported slugs.

## Validation

- `git diff --check HEAD`: passed.
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`: passed.
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_worklist/warehouse_console_worklist.js`: passed.
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`: passed.
- `python3 -m compileall -q erp_workspace_ui`: passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`: passed, 408 tests OK.
- Cache artifacts from changed Python paths were removed.
- Internal subagent quality gate found one Low wording issue; it was patched and revalidated.

## Boundary Confirmation

W16G5A introduces no Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, return Purchase Receipt, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, stock movement, stock posting, valuation/accounting/commercial exposure, native ERP route exposure, notification/email/portal behavior, Sales runtime mutation, Procurement runtime mutation, external action, live alignment, restart, protected gate, commit, push, or Warehouse Workspace Closure.

## Remaining Gate

The next step remains owner/manual final verification and any remaining closure-readiness review before W16H can be considered. W16H must be a separate closure decision and must not silently activate ERP document runtime or stock/accounting behavior.
