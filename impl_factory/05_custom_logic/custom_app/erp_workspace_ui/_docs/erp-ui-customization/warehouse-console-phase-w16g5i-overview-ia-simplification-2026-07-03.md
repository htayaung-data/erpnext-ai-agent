# Warehouse Console Phase W16G5I - Overview IA Simplification

Date: 2026-07-03

## Scope

W16G5I simplifies the Warehouse Overview information architecture. It changes only the Overview rendering contract, W9A cockpit smoke assertions, and roadmap documentation.

## Decision

Overview now separates route intent into two surfaces:

- `Start Warehouse Work`: work-entry destinations only.
- `Review and Visibility`: manager review queues and read-only visibility destinations.

`Stock Exceptions`, `Movement Visibility`, and `Transfer Visibility` no longer duplicate into `Start Warehouse Work`. They remain reachable from `Review and Visibility`.

`Movement Visibility` and `Transfer Visibility` remain separate read-only pages because they answer different operational questions:

- `Movement Visibility`: posted movement evidence and item posture.
- `Transfer Visibility`: inter-warehouse transfer posture.

## Source Changes

- Removed the duplicate `work_entry` group from the rendered Action Center.
- Renamed the visible Action Center title to `Review and Visibility`.
- Limited `Start Warehouse Work` to:
  - Inbound Receiving
  - Outbound Picking
  - Returns
  - Internal Transfer
  - Cycle Count
- Removed stale legacy Overview risk/movement renderer functions that were no longer called.

## Smoke Coverage

W9A cockpit smoke now verifies:

- `Start Warehouse Work` renders exactly five work-entry cards.
- `Stock Exceptions`, `Movement Visibility`, and `Transfer Visibility` are absent from the Start lane.
- `Review and Visibility` renders manager-review and visibility groups only.
- Stock exceptions, movement visibility, and transfer visibility route coverage remains active through the Review and Visibility controls.
- No native route, stock document action, valuation/accounting exposure, notification/email/portal action, or Sales/Procurement runtime path is introduced.

## Boundaries

W16G5I does not approve or introduce:

- ERPNext document creation, save, submit, cancel, amend, delete, or posting.
- Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, or Stock Reservation mutation.
- Native ERP route exposure.
- Valuation, accounting, commercial, notification, email, portal, or external action behavior.
- Sales or Procurement runtime change.
- Live alignment, restart, protected gate, commit, push, or Warehouse Workspace Closure.
