# Warehouse Console Phase W16D4 - Supplier Return Candidate Activation

Date: 2026-07-01
Status: Source implementation complete; live alignment and owner manual check still required.
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder internal sidecar plus source validation

## 1. Purpose

W16D4 activates the Supplier Return candidate evidence save path inside the Returns work hub.

The goal is to move Supplier Return candidate work out of `Planned` state while keeping the action bounded to custom Warehouse records only.

W16D4 does not activate supplier manager decisions, Procurement/Admin handoff, Finance/Admin handoff, customer return manager decisions, ERPNext document creation, stock posting, supplier/customer notification, native route access, or Warehouse Workspace Closure.

## 2. Implemented Scope

Visible UI changes:

- The Returns work hub now labels Supplier Return candidate as `W16D4 active`.
- The Supplier Return lane contains a compact evidence form.
- The form collects backend-required fields:
  - supplier
  - visible warehouse
  - supplier return source reference
  - item code
  - optional item name
  - UOM
  - candidate quantity
  - quarantine quantity
  - damaged quantity
  - wrong item quantity
  - overage quantity
  - quality hold quantity
  - condition grade
  - evidence reference
  - condition note
- One active supplier button is exposed: `Save candidate draft`.
- Customer Return intake remains active from W16D3.
- Return Decisions lane remains inactive.

Backend method exposed through the workspace registry:

- `save_warehouse_supplier_return_candidate_draft`

The frontend still has a fallback method string, but the registry now exposes `supplier_return_candidate_draft` so the method is auditable and not hidden in page code only.

## 3. Guardrails

W16D4 remains custom-record-only.

The save path writes only through the already-hardened backend method for `Warehouse Supplier Return Candidate` custom records.

Explicitly blocked:

- supplier notification, email, portal, or external action
- return Purchase Receipt creation/save/submit/cancel/amend
- Purchase Invoice return or debit note creation/save/submit/cancel/amend
- Purchase Order update
- Stock Entry creation/save/submit/cancel/amend
- Stock Ledger / Stock Balance / Stock Reconciliation / Stock Reservation mutation
- stock movement or stock posting
- Procurement runtime mutation
- Finance/Admin runtime mutation
- native ERPNext route or document form exposure
- valuation/accounting/commercial payload exposure

## 4. Validation And Safety Decisions

UI validation mirrors the backend contract before calling the service:

- supplier, warehouse, and supplier return reference are required
- item code is required
- candidate quantity must be greater than zero
- quarantine, damaged, wrong item, overage, and quality hold quantities must be non-negative
- exception quantity sum cannot exceed candidate quantity
- condition grade or condition note is required
- any exception quantity requires evidence reference in the UI

The supplier backend payload hash includes `item_name`, so W16D4 may expose optional `item_name` without the customer-return idempotency issue seen in W16D3.

The UI uses a stable request id while the same supplier candidate payload is retried, then clears that id after a successful save. If the user changes the payload after an error, a new request id is generated.

## 5. Smoke And Contract Coverage

Updated W9A smoke coverage:

- Returns work hub still renders once.
- Customer Return intake remains active from W16D3.
- Supplier Return candidate lane renders once.
- Supplier Return candidate fields render.
- Exactly two active Returns hub controls exist: Customer Return intake save and Supplier Return candidate save.
- Return Decisions lane remains inactive.
- In source-override smoke mode only, the supplier save button calls the custom `save_warehouse_supplier_return_candidate_draft` method and receives a mocked custom-record response.
- The smoke does not click the supplier save button against live data, so validation does not create live supplier return candidate records.

Registry contract coverage:

- `supplier_return_candidate_draft` is now part of the Warehouse workspace method registry contract.

## 6. Internal Sidecar Findings Applied

Hybrid Review Ladder sidecar review found these useful constraints, which were applied:

- W16D4 must send only backend signature top-level fields because non-empty unknown top-level fields are rejected.
- W16D4 must remain save-only and must not activate supplier manager decisions or handoff calls.
- `item_name` is safe to expose for supplier candidate because the supplier payload hash includes it.
- W9A smoke must change from one active Returns hub control to exactly two allowed save controls.
- The workspace registry must expose the supplier-return draft method key.

No sidecar recommendation was used to expand scope into manager decisions, handoff requests, Procurement/Admin actions, Finance/Admin actions, supplier notification, or ERPNext document behavior.

## 7. Validation Performed

Validation passed:

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m py_compile erp_workspace_ui/workspace_registry.py`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`, passing `404 tests OK`

Generated `__pycache__` and `.pyc` artifacts under `erp_workspace_ui` must be removed after validation.

## 8. Manual Check Required

Owner manual check is required after live alignment because W16D4 changes visible Overview behavior and exposes a custom supplier-return write action.

Manual check should verify:

- Returns work hub is visible in Warehouse Overview.
- Customer Return intake remains active.
- Supplier Return candidate lane shows `W16D4 active` or equivalent active custom workflow context.
- There are exactly two active Returns hub save actions: Customer intake draft and Supplier candidate draft.
- Return Decisions remains inactive.
- Supplier save button records a custom candidate draft and shows a no-effect success message.
- The UI does not imply supplier notification, return Purchase Receipt, Purchase Invoice return, debit note, stock decrease, Procurement approval, Finance approval, or ERP document creation.
- The visual presentation remains premium and consistent with W16C/W16D3.

## 9. Boundary Confirmation

No live alignment, owner acceptance, commit, push, restart, protected gate, supplier manager-decision activation, supplier handoff activation, Procurement/Admin runtime mutation, Finance/Admin runtime mutation, ERPNext document runtime, stock/accounting mutation, native route exposure, notification/email/portal behavior, external action, or Warehouse Workspace Closure is approved by W16D4 source implementation alone.
