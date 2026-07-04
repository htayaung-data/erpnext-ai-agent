# Warehouse Console Phase W16D3 - Customer Return Intake Activation

Date: 2026-07-01
Status: Source implementation complete; live alignment and owner manual check still required.
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder internal sidecar plus source validation

## 1. Purpose

W16D3 activates the first write action inside the Returns work hub: Customer Return intake evidence save.

The goal is to move Customer Return intake out of `Planned` state while keeping the action bounded to custom Warehouse records only.

W16D3 does not activate manager decisions, Sales/Admin handoff, Finance/Admin handoff, supplier return flow, ERPNext document creation, stock posting, notification, native route access, or Warehouse Workspace Closure.

## 2. Implemented Scope

Visible UI changes:

- The Returns work hub now labels Customer Return intake as `W16D3 active`.
- The Customer Return lane contains a compact evidence form.
- The form collects backend-required fields:
  - customer
  - visible warehouse
  - return authorization/reference
  - item code
  - UOM
  - returned quantity
  - accepted quantity
  - damaged quantity
  - quarantine quantity
  - condition grade
  - evidence reference
  - condition note
- One active button is exposed: `Save intake draft`.
- Supplier Return and Return Decisions lanes remain inactive foundation lanes.

Backend method exposed through the workspace registry:

- `save_warehouse_customer_return_intake_draft`

The frontend still has a fallback method string, but the registry now exposes `customer_return_intake_draft` so the method is auditable and not hidden in page code only.

## 3. Guardrails

W16D3 remains custom-record-only.

The save path writes only through the already-hardened backend method for `Warehouse Customer Return Intake` custom records.

Explicitly blocked:

- Sales Return creation/save/submit/cancel/amend
- Credit Note creation/save/submit/cancel/amend
- Delivery Note return behavior
- Stock Entry creation/save/submit/cancel/amend
- Stock Ledger / Stock Balance / Stock Reconciliation / Stock Reservation mutation
- stock movement or stock posting
- customer notification, email, portal, or external action
- Sales runtime mutation
- Finance/Admin runtime mutation
- native ERPNext route or document form exposure
- valuation/accounting/commercial payload exposure

## 4. Validation And Safety Decisions

UI validation mirrors the backend contract before calling the service:

- customer, warehouse, and return reference are required
- item code is required
- returned quantity must be greater than zero
- accepted, damaged, and quarantine quantities must be non-negative
- accepted + damaged + quarantine cannot exceed returned quantity
- condition grade or condition note is required
- damaged/quarantine quantity requires evidence reference in the UI

The UI does not expose editable `item_name` in W16D3 because the current customer-return backend payload hash does not include `item_name`. Exposing it would make changed-payload idempotency harder to audit. Item identity is therefore controlled by `item_code` in this phase.

The UI uses a stable request id while the same payload is retried, then clears that id after a successful save. If the user changes the payload after an error, a new request id is generated.

## 5. Smoke And Contract Coverage

Updated W9A smoke coverage:

- Returns work hub still renders once.
- Customer Return intake lane renders once.
- Customer Return intake fields render.
- Exactly one active Returns hub control exists: the Customer Return intake save button.
- Supplier Return lane remains inactive.
- Return Decisions lane remains inactive.
- In source-override smoke mode only, the save button calls the custom `save_warehouse_customer_return_intake_draft` method and receives a mocked custom-record response.
- The smoke does not click the save button against live data, so validation does not create live customer return records.

Registry contract coverage:

- `customer_return_intake_draft` is now part of the Warehouse workspace method registry contract.

## 6. Internal Sidecar Findings Applied

Hybrid Review Ladder sidecar review found these useful constraints, which were applied:

- W16D3 must require backend-required fields directly in the UI.
- W16D3 must remain save-only and must not activate manager or handoff calls.
- Editable `item_name` should not be exposed until backend payload hashing includes it or the field is otherwise governed.
- W9A smoke must change from zero active Returns hub controls to exactly the one allowed customer intake save control.
- The workspace registry should expose the customer-return draft method key.

No sidecar recommendation was used to expand scope into manager decisions, supplier returns, handoff requests, or ERPNext document behavior.

## 7. Validation Performed

Validation passed:

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m py_compile erp_workspace_ui/workspace_registry.py`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`, passing `404 tests OK`

Generated `__pycache__` and `.pyc` artifacts under `erp_workspace_ui` were removed after validation.

## 8. Manual Check Required

Owner manual check is required after live alignment because W16D3 changes visible Overview behavior and exposes a custom write action.

Manual check should verify:

- Returns work hub is visible in Warehouse Overview.
- Customer Return intake lane shows `W16D3 active` or equivalent active custom workflow context.
- Only Customer Return intake has an active save button.
- Supplier Return and Return Decisions remain inactive.
- Save button records a custom intake draft and shows a no-effect success message.
- The UI does not imply Sales Return, Credit Note, Delivery Note, stock increase, customer notification, refund, approval, or ERP document creation.
- The visual presentation remains premium and consistent with W16C header/button/pill polish.

## 9. Boundary Confirmation

No live alignment, owner acceptance, commit, push, restart, protected gate, supplier-return activation, manager-decision activation, handoff activation, Sales/Finance/Admin runtime mutation, ERPNext document runtime, stock/accounting mutation, native route exposure, notification/email/portal behavior, external action, or Warehouse Workspace Closure is approved by W16D3 source implementation alone.
