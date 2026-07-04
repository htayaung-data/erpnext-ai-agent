# Warehouse Console Phase W16D5 - Return Decisions Manager Posture Activation

Date: 2026-07-01
Status: Source implementation complete; live alignment and owner manual check required.
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder internal sidecar plus source validation

## 1. Purpose

W16D5 activates the `Return decisions` lane inside the Returns work hub.

The lane records manager posture on already-created custom Customer Return Intake and Supplier Return Candidate records. It does not create request handoff records yet, and it does not create ERPNext stock, sales, purchase, accounting, notification, or native-route behavior.

## 2. Implemented Scope

Visible UI changes:

- `Return decisions` is now labelled `W16D5 active`.
- Manager decision controls render for customer return posture and supplier return posture.
- Controls are disabled until the related custom source record is saved in the Returns work hub.
- Controls remain disabled for non-manager role context.
- Manager actions call the existing hardened backend methods:
  - `save_warehouse_customer_return_manager_decision`
  - `save_warehouse_supplier_return_manager_decision`
- The workspace registry exposes those methods as explicit Warehouse method keys.

Customer manager posture options exposed:

- `mark_restock_candidate`
- `request_reinspection`
- `escalate_to_sales`

Supplier manager posture options exposed:

- `mark_supplier_return_candidate`
- `mark_quarantine_review`
- `escalate_to_procurement`

The backend remains the source of truth for decision validity. If a manager selects a posture that does not match the saved evidence, the UI shows the backend rejection in the custom lane status.

## 3. Explicitly Not Activated

W16D5 does not activate:

- customer return handoff requests
- supplier return handoff requests
- Sales/Admin runtime mutation
- Procurement/Admin runtime mutation
- Finance/Admin runtime mutation
- Sales Return creation/save/submit/cancel/amend
- Credit Note creation/save/submit/cancel/amend
- Return Purchase Receipt creation/save/submit/cancel/amend
- Purchase Invoice return or debit note creation/save/submit/cancel/amend
- Stock Entry creation/save/submit/cancel/amend
- Stock Ledger, Stock Balance, Stock Reconciliation, or Stock Reservation mutation
- stock movement or stock posting
- customer or supplier notification, email, portal, or external action
- native ERPNext route exposure
- Warehouse Workspace Closure

## 4. Validation Plan

Required validation:

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m py_compile erp_workspace_ui/workspace_registry.py`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- W9A source-override smoke coverage for:
  - initial return decision controls disabled before source save
  - customer manager decision calls only the custom customer manager method
  - supplier manager decision calls only the custom supplier manager method
  - no native route or ERP document language appears

Generated `__pycache__` and `.pyc` artifacts must be removed after validation.

## 5. Manual Check Required

Owner manual check is required after live alignment.

Manual check should verify:

- Customer Return intake and Supplier Return candidate save actions still work.
- Return Decisions shows manager posture controls.
- Controls are disabled until a related custom source record is saved.
- Controls record manager posture only on custom records.
- Copy does not imply approval, handoff, ERP document creation, stock movement, accounting impact, customer notification, or supplier notification.
- The visual pattern remains premium and aligned with W16D3/W16D4.

## 6. Boundary Confirmation

W16D5 is manager-posture activation only. It writes only existing custom Customer Return Intake / Supplier Return Candidate status and event data through existing hardened backend methods. It does not approve handoff activation, ERPNext document runtime, stock/accounting mutation, native route exposure, notification behavior, external action, commit, push, restart, protected gate, or Warehouse Workspace Closure.
