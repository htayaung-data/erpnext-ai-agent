# Warehouse Console Phase W16C - Picking Review Custom Workflow Closure

Date: 2026-07-01
Status: Owner/manual accepted for W16C. Closed for the W16C Picking Review activation scope only.

## Purpose

W16C activates the Picking Review planned workflow as a custom Warehouse workflow. It turns the previous shell-only picking preview into a controlled custom-record workflow for pick evidence, manager posture, and outbound handoff readiness.

This is not full Warehouse Workspace Closure. It closes only the W16C Picking Review activation slice. Remaining planned workflow areas continue in W16D and later phases.

## Implemented Scope

- Picking Review now presents a custom picking workflow instead of shell-only planned controls.
- Warehouse users can record pick evidence into custom Warehouse Picking Task records.
- Evidence includes picked quantity, packed quantity, shortage, damaged quantity, not-found quantity, exception reason, and evidence text.
- Manager decisions are role-gated for Warehouse Manager, Stock Manager, and System Manager contexts.
- Non-manager contexts see disabled manager controls and cannot trigger manager decisions client-side.
- Backend manager gates remain authoritative and deny unauthorized manager decisions.
- Header pills, action buttons, and status typography were polished to a quiet metadata treatment after owner review.
- The shared header/status polish is delivered through a stable Warehouse theme patch asset loaded by the receiving and picking page wrappers.

## Live Alignment Evidence

Runtime files were aligned to the live DigitalOcean workspace for W16C. The scoped runtime files are:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_theme_patch.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js`

A final security/stability preflight found that live runtime was aligned but live verification evidence was missing two files. That gap was resolved by aligning these verification files from design to live:

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `ui_smoke/warehouse_phase_w5b_picking_review_smoke.js`

The live Page doctypes were reloaded and cache was cleared after runtime alignment:

- `bench --site erpai_prj1 reload-doc erp_workspace_ui page warehouse_console_receiving`
- `bench --site erpai_prj1 reload-doc erp_workspace_ui page warehouse_console_picking`
- `bench --site erpai_prj1 clear-cache`
- `bench --site erpai_prj1 clear-website-cache`

## Validation

The W16C package passed the following checks before closure:

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_theme_patch.js`
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_receiving/warehouse_console_receiving.js`
- `node --check erp_workspace_ui/erp_workspace_ui/page/warehouse_console_picking/warehouse_console_picking.js`
- `node --check ui_smoke/warehouse_phase_w5b_picking_review_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`, passing `404 tests OK`
- live served asset syntax checks for `warehouse_console_page.js` and `warehouse_console_theme_patch.js`
- live verification-file alignment checks for W16C test and smoke files
- cache cleanup check for generated `__pycache__` / `.pyc` artifacts under changed service/test paths

## Subagent Review Summary

Operations/UX review found no blocker, high, medium, or low closure hold. It confirmed W16C business intent: UI actions call only custom picking task draft and manager-decision methods, service writes only Warehouse Picking Task records plus custom child rows/events, and the response payloads explicitly report no outbound ERP document or stock side effect.

Security/Stability review found no runtime blocker. It confirmed no forbidden create/save/submit/cancel/amend path for Delivery Note, Pick List, Stock Reservation, Stock Entry, Stock Ledger, Stock Balance, or Stock Reconciliation in W16C runtime paths. It also confirmed no native ERP document route, no notification/email/portal mutation, role-gated manager controls, and visual-only theme patch behavior. Its single Medium verification-evidence finding was resolved by aligning the missing live test and smoke files.

## Owner Manual Acceptance

Owner manually accepted the live W16C Picking Review behavior and UI after sign-out/sign-in verification. Accepted items include:

- Picking Review custom workflow visibility.
- Pick evidence entry and draft-save behavior.
- Manager decision controls remaining disabled for non-manager context.
- Header action placement.
- Header metadata pills using quiet non-gradient styling.
- Smaller status typography for overdue/picking state values.

No further owner manual check is required for W16C closure unless later runtime files are changed.

## Boundary Confirmation

W16C does not create, save, submit, cancel, amend, post, reserve, unreserve, email, notify, route to, or expose any ERPNext operational document.

The following remain blocked:

- Delivery Note creation, draft, save, submit, cancel, or amend.
- Pick List creation, draft, save, submit, cancel, or amend.
- Stock Reservation creation, reserve, unreserve, mutation, or posting.
- Stock Entry behavior.
- Stock Ledger, Stock Balance, and Stock Reconciliation mutation.
- Stock movement or stock posting.
- Sales Order update or customer-facing Sales runtime mutation.
- Native ERPNext document route exposure.
- Valuation, accounting, commercial, margin, price, or revenue exposure.
- Customer notification, email, portal, or external action.
- Protected gate, commit, push, restart, release closure, or full Warehouse Workspace Closure.

## Next Phase

Proceed to W16D only after W16C closure is accepted. W16D should continue planned-state burn-down toward real Warehouse Workspace Closure, likely starting with the next highest-priority planned workflow area after receiving and picking activation.
