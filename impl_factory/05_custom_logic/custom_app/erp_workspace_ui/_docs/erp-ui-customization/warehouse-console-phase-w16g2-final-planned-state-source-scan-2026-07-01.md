# Warehouse Console Phase W16G2 - Final Planned-State Source Scan

Date: 2026-07-01
Status: scan and classification only
Scope: post-W16G1 source scan before true Warehouse Workspace Closure

## Reasoning Budget

Recommended thinking: High.

Reason: W16G2 decides whether any remaining planned/shell/future wording blocks true Warehouse Workspace Closure.

## What Was Checked

W16G2 scanned the Warehouse source paths that produce or validate owner-facing Warehouse behavior:

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `ui_smoke/warehouse_phase_w4b_receiving_smoke.js`
- `ui_smoke/warehouse_phase_w5b_picking_review_smoke.js`

The scan looked for:

- planned
- shell only / shell-only
- future
- later
- preview-only / preview only
- inactive / not active
- stale W16G1 target strings
- forbidden activation terms around ERPNext stock/accounting documents

An internal subagent was attempted for a read-only cross-check, but it could not access the remote Linux workspace and reported a local path mismatch. Its output was not used as authoritative evidence.

## Result Summary

W16G1 successfully removed the direct High blockers from the target areas:

- Overview Action Center no longer presents as shell-only in source contract.
- Action Center payload now uses `custom_workflow`.
- Action Center guardrail now uses stable custom-workflow language.
- Receiving Review no longer says "Draft comes later" in active runtime copy.
- Picking Review no longer says "Later phases must" in active runtime copy.
- W9A/W5B smoke expectations now validate the active custom-workflow state.

No new ERPNext document runtime or stock/accounting mutation path was introduced.

## Remaining Findings

| ID | Severity | Area | Finding | Closure action |
| --- | --- | --- | --- | --- |
| W16G2-M01 | Medium | Shared Warehouse page source | Dead planned-shell CSS, data attributes, and renderer code remain in `warehouse_console_page.js`. The current rendered workflow list is empty, so this is not currently owner-visible, but it is static closure debt. | W16G3 should remove the dead planned-shell renderer/CSS where safe, or prove all remaining selectors are only non-rendered legacy code. |
| W16G2-M02 | Medium | W9A smoke | Legacy W15 shell helper functions and planned-control counters remain in the smoke file. Active assertions now expect zero planned shells, but old helpers still create scan noise. | W16G3 should retire unused planned-shell helper functions and stale planned workflow disclosure helpers. |
| W16G2-M03 | Medium | Active custom workflow policy copy | Some active pages still use owner-facing "future Stock Entry policy" or "future Stock Reconciliation policy" phrasing to describe ERP document ownership outside the workflow. This is safe boundary copy, but the word "future" can still read unfinished. | W16G3 should reword to "separate owner-approved document policy outside this workflow" without implying activation. |
| W16G2-M04 | Medium | Internal CSS/data names | Some active receiving/picking controls still use `planned-control` CSS/data names. This is not visible to users, but it weakens static closure scans. | W16G3 should rename only if the change is low-risk, or document as internal non-owner-facing naming debt. |
| W16G2-L01 | Low | Python and negative tests | `from __future__` and negative smoke assertions still match broad scan terms. | No action required; these are false positives. |

## Acceptable Boundary Hits

The scan found many expected safety-boundary references to ERP documents and stock/accounting concepts. These are acceptable when they are negative or read-only:

- No Purchase Receipt created/saved/submitted.
- No Delivery Note, Pick List, Stock Reservation, Stock Entry, or stock ledger change.
- No Stock Reconciliation, Stock Entry, Stock Ledger, Stock Balance, or Stock Reservation mutation.
- Valuation visibility remains hidden.
- Movement/transfer visibility reads submitted Stock Entry posture only where previously approved, without creating or submitting stock documents.
- Negative smoke assertions preventing native-route or stock-document exposure.

These are not planned-state blockers.

## Live Visual Scan Status

No live alignment was performed in W16G2.

Reason: W16G1 source changes are not automatically live-aligned, and live alignment/restart/protected gates require explicit owner approval. W16G2 therefore remains a source/static scan phase.

## Required Next Step

Proceed to W16G3: closure cleanup patch.

W16G3 should:

1. Remove or quarantine dead planned-shell source code from the shared Warehouse page.
2. Retire unused W9A planned-shell helper functions and stale disclosure exercise code.
3. Reword remaining active "future policy" owner-facing copy to stable "separate owner-approved policy outside this workflow" copy.
4. Preserve all ERP document, stock/accounting, native-route, valuation, notification, Sales runtime, and Procurement runtime boundaries.
5. Run full source validation.

Only after W16G3 and a clean W16G4 live/manual scan should the Warehouse Workspace Closure package be prepared.

## Boundary Confirmation

W16G2 is scan and documentation only. It does not approve or perform live alignment, restart, protected gate, commit, push, ERPNext document runtime, stock/accounting mutation, native route exposure, notification behavior, Sales runtime mutation, Procurement runtime mutation, or Workspace Closure.
