# Warehouse Console Phase W16G5H - Workflow Action Bug + Permission Hardening

Date: 2026-07-03

## Scope

W16G5H is a narrow hardening phase after the W16G5G route-stability work. It addresses action correctness and custom workflow recall permission safety only.

Included:

- Fix the Returns Work Hub supplier manager-decision browser action typo.
- Require explicit Warehouse read permission before custom workflow record recall.
- Require explicit read permission on each custom workflow parent DocType before recall queries.
- Add tests and smoke assertions to prevent regression.

Excluded:

- No UI redesign.
- No new workflow activation.
- No ERPNext document lifecycle action.
- No stock/accounting mutation.
- No native ERP route exposure.
- No Sales, Procurement, Finance, Inventory/Admin runtime action.
- No live alignment, commit, push, restart, protected gate, or Warehouse Workspace Closure approval.

## Changes

- `saveReturnManagerDecision(...)` now uses the existing `isSupplier` variable when selecting supplier-return manager-decision payload arguments.
- Custom workflow recall endpoints now call `_can_recall_custom_workflow_records(context)` before reading saved custom workflow records.
- `_custom_workflow_fetch_rows(...)` now returns no rows unless the current user has read permission for the requested custom workflow DocType.
- Contract tests now mark custom workflow parent DocTypes readable by default and explicitly remove those permissions in negative tests.
- W9A smoke now asserts the misspelled `isSupplie` variable is not present in the Warehouse runtime source.

## Validation Required

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- Focused negative tests for custom workflow recall permission gates
- Cache cleanup/check under changed Python paths

## Boundary

W16G5H remains custom Warehouse workflow hardening only. It does not create, save, submit, cancel, amend, delete, post, reserve, reconcile, notify, email, expose portal behavior, or open native ERPNext routes.
