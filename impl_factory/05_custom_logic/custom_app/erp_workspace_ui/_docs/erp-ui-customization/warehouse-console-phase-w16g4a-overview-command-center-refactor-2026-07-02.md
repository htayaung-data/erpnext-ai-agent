# Warehouse Console Phase W16G4A Overview Command Center Refactor

Date: 2026-07-02

## Scope

W16G4A is the first implementation slice after the W16G4 UI/business-purpose audit reopened Warehouse closure readiness. It refactors the Warehouse Overview Action Center into a clearer command-center model.

This phase changes only Overview information architecture and presentation. It does not redesign the dedicated Returns, Internal Transfer, Cycle Count, Receiving, Picking, Stock Exceptions, Movement Visibility, or Transfer Visibility pages. Those remain later W16G4B-W16G4F slices.

## Owner Issue Addressed

Owner live review found that Overview cards such as Review transfer / Custom did not feel premium and did not clearly communicate business purpose. The old Action Center rendered custom workflow cards with `Custom` as a large metric-like value, making them look like fake KPIs instead of navigation and review-entry cards.

## Implementation Summary

- Renamed the Overview section from `Warehouse Action Center` to `Warehouse Command Center`.
- Replaced the two-section model with three business-purpose sections:
  - `Start Work`
  - `Manager Review`
  - `Visibility`
- Added explicit card role metadata:
  - `queue`
  - `custom_workflow`
  - `visibility`
- Updated custom workflow cards so `Custom` is no longer rendered as a large side metric.
- Added quiet role badges such as `Custom workflow`, `Manager posture`, and `Read-only`.
- Kept all existing productized Warehouse routes inside `/desk/warehouse-console-worklist/...`.
- Added a dedicated `Visibility` group so Movement Visibility and Transfer Visibility no longer appear as manager-decision cards.
- Reduced Action Center border/box dominance for a calmer premium ERP hierarchy.

## Route / Behavior Boundary

Allowed route targets remain productized Warehouse routes only:

- `warehouse-console-worklist/inbound-receiving`
- `warehouse-console-worklist/outbound-picking`
- `warehouse-console-worklist/stock-exceptions`
- `warehouse-console-worklist/movement-visibility`
- `warehouse-console-worklist/transfer-visibility`
- `warehouse-console-worklist/returns-work-hub`
- `warehouse-console-worklist/internal-transfer-workflow`
- `warehouse-console-worklist/cycle-count-workflow`

No new backend method, DocType, stock/accounting behavior, native ERP route, notification, or external action is introduced.

## Tests / Smokes Updated

- W3 service contract now asserts `card_role` / `role_label` metadata for Overview cards.
- W9A cockpit smoke now asserts:
  - role badges render for custom and visibility cards;
  - custom workflow cards do not render `Custom` as a large metric;
  - the `Visibility` group is present;
  - all expected productized Warehouse route targets remain present.

## Deferred To Later W16G4 Slices

- Shared premium UI system pass across all Warehouse pages.
- Internal Transfer dedicated page redesign.
- Cycle Count dedicated page redesign.
- Returns Hub final polish.
- Empty/fallback state overhaul.
- Owner final manual review package.

## Boundary Confirmation

W16G4A does not approve Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, return Purchase Receipt, Purchase Invoice return, debit note, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, stock movement, stock posting, valuation/accounting/commercial exposure, notification/email/portal behavior, native ERP document routes, Sales runtime mutation, Procurement runtime mutation, live alignment, restart, protected gate, commit, push, or Warehouse Workspace Closure.
