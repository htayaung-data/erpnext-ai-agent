# Warehouse Console Phase W16G - Planned-State Burn-Down Audit

Date: 2026-07-01
Status: audit only
Scope: Warehouse Workspace owner-facing planned-state cleanup before true Workspace Closure

## Reasoning Budget

Recommended thinking: High.

Reason: W16G decides what still blocks true Warehouse Workspace Closure across owner-facing Warehouse screens. A mistake here could leave unfinished workflow states visible or accidentally imply ERP document activation.

## Current Position

W15J was a Warehouse foundation milestone, not Warehouse Workspace Closure.

W16B through W16F activated the major planned Workflow areas as custom-record workflows:

- W16B: Receiving Review custom workflow.
- W16C: Picking Review custom workflow.
- W16D: Returns work hub.
- W16E: Internal Transfer custom workflow.
- W16F: Cycle Count / Inventory Variance custom workflow.

Owner manual checks have accepted the visible behavior for the activated areas. The remaining work before true Warehouse Workspace Closure is not to activate ERP stock/accounting documents. The remaining work is to burn down owner-facing unfinished wording, stale smoke expectations, and legacy planned-shell code.

## Non-Negotiable Boundary

W16G does not approve:

- Purchase Receipt create, save, submit, cancel, amend, or draft runtime.
- Delivery Note create, save, submit, cancel, amend, or draft runtime.
- Pick List create, save, submit, cancel, amend, or draft runtime.
- Stock Reconciliation create, save, submit, cancel, amend, or draft runtime.
- Stock Entry create, save, submit, cancel, amend, or draft runtime.
- Stock Ledger, Stock Balance, Stock Reservation, reserve, unreserve, stock movement, or stock posting mutation.
- Native ERPNext route exposure.
- Valuation, accounting, commercial, or customer/supplier notification exposure.
- Email, portal, external action, Sales runtime mutation, or Procurement runtime mutation.
- Live alignment, restart, protected gate, commit, push, or closure approval.

Blocked ERP document policy text is acceptable only when it reads as stable policy. It must not read as unfinished workflow work or hidden future activation.

## Method

W16G used the Hybrid Review Ladder approach:

- Main Control performed the primary source scan and classification.
- Internal subagent preflight performed an independent read-only scan for planned, shell, inactive, future, preview-only, and later wording.
- Findings were merged into this audit.

No source/runtime patch is approved by this audit.

## Findings Matrix

| ID | Area | Current issue | Severity | Owner-facing? | Required action |
| --- | --- | --- | --- | --- | --- |
| W16G-H01 | Overview Action Center | Action Center still says "future Warehouse work", exposes `shell_only`, renders "Shell only", falls back to "Action shell only", and references "planned workflow lane". | High | Yes | Reword to active custom-workflow command center language. Remove shell/planned framing from owner-facing Action Center copy. |
| W16G-H02 | Receiving Review | Receiving document-policy panel says "Draft Policy Preview", "draft preparation comes later", "Draft comes later", "Draft remains unsubmitted", and "outside this shell". | High | Yes | Keep Purchase Receipt blocked, but reword as stable document policy: "Purchase Receipt blocked here", "No draft created here", "Procurement/Admin owns document handling outside this custom workflow". |
| W16G-H03 | Picking Review | Picking outbound policy says "Later phases must..." and smoke still calls the panel "delivery policy preview". | High | Yes | Keep Delivery Note, Pick List, Stock Reservation, Stock Entry, and stock ledger blocked. Reword future-phase framing to stable outbound document policy. |
| W16G-H04 | W9A Overview smoke | W9A smoke still expects old planned/shell Action Center behavior and calls old planned-workflow assertions while later asserting planned shells are gone. | High | Test-facing, closure-critical | Update W9A fixture/assertions to match active W16B-W16F state. Remove or retire old planned-shell expectations. |
| W16G-M01 | Legacy planned-shell renderer | Dead planned-shell renderer and CSS names remain in the shared Warehouse page. Current render path returns empty workflow list, so this is not visible, but it is static closure debt. | Medium | Not currently visible | Remove dead planned-shell renderer/CSS or explicitly prove unreachable in final closure scan. Prefer removal before closure. |
| W16G-M02 | Active controls with legacy class names | Receiving and Picking active custom controls still use `planned-control` class/data names in some places. This does not affect visible wording, but it weakens maintainability and static scans. | Medium | No | Rename in a contained cleanup if low risk, or document as non-owner-facing technical debt with final static evidence. |
| W16G-M03 | Manager-only disabled controls | Manager decision controls are visible but disabled when role/prerequisite gates are not satisfied. This is intentional role affordance, but final closure should decide whether disabled controls or explanatory posture cards are preferred for non-manager users. | Medium | Yes | Owner decision before closure. Current behavior is safe because backend role gates remain authoritative. |
| W16G-L01 | Old smoke helper names | Some smoke helper names still mention planned shells even when no visible planned shell remains. | Low | No | Rename/remove during W16G1 or W16G2 to reduce future confusion. |

## Acceptable Copy That Must Remain

The following copy is acceptable and should remain in some form:

- "No stock is posted."
- "No Purchase Receipt is created, saved, or submitted."
- "No Delivery Note, Pick List, Stock Reservation, Stock Entry, or stock ledger change is created."
- "No Sales Return, Credit Note, return Purchase Receipt, debit note, notification, native ERP route, or stock movement starts here."
- "Custom records only."
- "Manager only" when a control is actually role-gated.

This copy is not a planned-state problem. It is safety boundary copy.

## Required Next Step

Proceed to W16G1: planned-state wording and smoke cleanup.

W16G1 should patch only safe closure cleanup:

1. Reword Overview Action Center from shell/planned/future language to active custom-workflow command center language.
2. Reword Receiving Review document-policy panel from "draft comes later" language to stable blocked-policy language.
3. Reword Picking Review outbound document-policy panel from "later phases" language to stable blocked-policy language.
4. Update W9A smoke fixture/assertions so it expects active W16B-W16F state and no planned workflow shells.
5. Keep all ERP stock/accounting/native-route/notification boundaries blocked.

W16G1 should not activate any ERP document runtime.

## Closure Path After W16G1

After W16G1:

1. Run W16G2 final planned-state static and live visual scan.
2. Resolve any remaining owner-facing "planned", "shell only", "future", "later", "preview-only", or "inactive" wording that implies unfinished Warehouse work.
3. Ask Owner manual check only for visible wording/layout changes.
4. Then prepare the true Warehouse Workspace Closure package.

The closure package can only say Warehouse Workspace Closure after the owner-facing planned-state burn-down is clean.

## Validation Performed

- Main Control source scan of Warehouse overview, receiving, picking, service payload, and Warehouse smokes.
- Internal subagent read-only preflight scan for planned/shell/inactive/future/preview-only/later wording.
- Findings merged and classified.
- No runtime/backend/DocType/test/smoke/live patch was made by this audit.

## Boundary Confirmation

W16G is audit-only. It does not approve or perform live alignment, restart, protected gate, commit, push, ERPNext document runtime, stock/accounting mutation, native route exposure, notification behavior, Sales runtime mutation, Procurement runtime mutation, or Workspace Closure.
