# Warehouse Console Phase W16F - Cycle Count Custom Workflow Activation

Date: 2026-07-01
Scope: Activate Cycle Count / Inventory Variance from an Overview planned shell into a dedicated custom Warehouse workflow page.

## Decision

Cycle Count / Inventory Variance is no longer treated as an Overview planned workflow shell. It now has a dedicated custom route:

- `/desk/warehouse-console-worklist/cycle-count-workflow`

The Overview remains a navigation and summary surface only. Count evidence and manager variance posture live on the dedicated Cycle Count page.

## Runtime Boundary

The W16F page writes only custom `Warehouse Cycle Count Task` records and custom task events through existing W15H backend methods:

- `save_warehouse_cycle_count_task_draft`
- `save_warehouse_cycle_count_manager_decision`

The implementation does not create, save, submit, cancel, amend, or route to Stock Reconciliation or Stock Entry. It does not mutate Stock Ledger, Stock Balance, Stock Reservation, stock quantities, valuation, or accounting records. It does not expose native ERPNext routes, notifications, email, portal behavior, Sales runtime changes, Procurement runtime changes, Finance/Admin runtime changes, or Inventory/Admin stock document runtime.

## UI Behavior

- Overview start cards and Action Center route to the dedicated Cycle Count page.
- The remaining planned workflow shell section is removed because Cycle Count is activated.
- The Cycle Count page records warehouse, count source, count scope, blind/guided visibility, count reason, one count line, variance posture, reason, and evidence reference.
- Manager controls are disabled until a custom task is saved.
- Manager controls are role-gated to Warehouse Manager, Stock Manager, or System Manager context and update only task status/event posture.

## Review Expectations

Reviewers should confirm:

- no Stock Reconciliation, Stock Entry, or stock mutation path is introduced;
- no native route or ERP document action is exposed;
- Overview does not expose active count input fields or remaining planned workflow shells;
- Cycle Count route renders one custom workflow page;
- task save calls only the custom task draft method;
- manager posture calls only the custom manager decision method;
- no valuation/accounting/commercial or notification behavior appears.

## Manual Owner Check

Manual UI check is required after live alignment because W16F changes visible navigation and activates a new dedicated custom workflow page.

Expected owner check:

1. Open Warehouse Console Overview.
2. Confirm Cycle Count appears as a custom workflow navigation card, not as a planned shell detail.
3. Confirm the Remaining planned workflow shells section is gone.
4. Open Cycle Count.
5. Confirm count evidence fields render cleanly.
6. Save a cycle count task.
7. Confirm success copy says custom record only and no Stock Reconciliation, Stock Entry, stock movement, ledger, or balance record.
8. Confirm manager controls unlock only after custom task save for manager-capable users.
