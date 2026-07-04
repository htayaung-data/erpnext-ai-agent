# Warehouse Console Phase W16G1 - Planned-State Wording And Smoke Cleanup

Date: 2026-07-01
Status: source cleanup
Scope: owner-facing planned-state burn-down after W16B-W16F custom workflow activation

## Reasoning Budget

Recommended thinking: High.

Reason: W16G1 removes owner-facing unfinished workflow language while preserving strict ERP document and stock/accounting boundaries.

## Purpose

W16G found that the major Warehouse custom workflows are active, but some owner-facing copy and smoke expectations still described the workspace as planned, shell-only, future, or preview-only.

W16G1 patches those closure blockers without activating any ERP document runtime.

## Changes

W16G1 changes:

- Overview Action Center language from shell/future/planned framing to active custom-workflow command-center framing.
- Action Center mode from `shell_only` to `custom_workflow`.
- Action Center guardrail from "Action shell only" to stable "Custom workflow only" policy.
- Receiving Review document panel from "Draft Policy Preview" and "Draft comes later" to stable Purchase Receipt blocked-policy wording.
- Picking Review outbound panel from "later phases" / "preview" wording to stable Delivery Note, Pick List, Stock Reservation, Stock Entry, and stock ledger blocked-policy wording.
- W9A smoke assertions so Overview expects active W16B-W16F state and no planned workflow shells.
- W5B smoke wording so Picking expects the outbound document policy panel, not a delivery-policy preview.

## Explicit Non-Changes

W16G1 does not add:

- Purchase Receipt create, save, submit, cancel, amend, or draft runtime.
- Delivery Note create, save, submit, cancel, amend, or draft runtime.
- Pick List create, save, submit, cancel, amend, or draft runtime.
- Stock Reconciliation create, save, submit, cancel, amend, or draft runtime.
- Stock Entry create, save, submit, cancel, amend, or draft runtime.
- Stock Ledger, Stock Balance, Stock Reservation, reserve, unreserve, stock movement, or stock posting mutation.
- Native ERPNext route exposure.
- Valuation, accounting, commercial, notification, email, portal, or external action behavior.
- Sales runtime mutation or Procurement runtime mutation.
- Live alignment, restart, protected gate, commit, push, or Workspace Closure approval.

## Remaining Closure Work

After W16G1, run W16G2:

1. Static scan for remaining owner-facing planned/shell/future/later/preview-only wording.
2. Runtime visual check on Overview, Receiving, Picking, Returns, Internal Transfer, and Cycle Count.
3. Decide whether visible disabled manager controls remain acceptable as manager-only affordance.
4. Remove or explicitly classify any remaining dead planned-shell code before final Workspace Closure.

## Boundary Confirmation

W16G1 is a wording, smoke, and documentation cleanup. It keeps all ERP stock/accounting/document actions blocked and does not claim true Warehouse Workspace Closure.
