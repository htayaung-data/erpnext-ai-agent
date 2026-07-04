# Warehouse Console Phase W16E - Internal Transfer Custom Workflow Activation

Date: 2026-07-01
Scope: Activate Internal Transfer from an Overview planned shell into a dedicated custom Warehouse workflow page.

## Decision

Internal Transfer is no longer treated as an Overview planned workflow shell. It now has a dedicated custom route:

- `/desk/warehouse-console-worklist/internal-transfer-workflow`

The Overview remains a navigation and summary surface only. Active transfer evidence and manager posture live on the dedicated Internal Transfer page.

## Runtime Boundary

The W16E page writes only custom `Warehouse Internal Transfer Candidate` records and custom candidate events through existing W15G backend methods:

- `save_warehouse_internal_transfer_candidate_draft`
- `save_warehouse_internal_transfer_manager_decision`

The implementation does not create, save, submit, cancel, amend, or route to Stock Entry. It does not mutate Stock Ledger, Stock Balance, Stock Reconciliation, or Stock Reservation. It does not move, reserve, post, or value stock. It does not expose native ERPNext routes, notifications, email, portal behavior, Sales runtime changes, Procurement runtime changes, Finance/Admin runtime changes, or Inventory/Admin stock document runtime.

## UI Behavior

- Overview start cards and Action Center route to the dedicated Internal Transfer page.
- The remaining planned workflow section now keeps only Cycle Count / Inventory Variance.
- The Internal Transfer page records source warehouse, target warehouse, source context, transfer reason, one candidate line, exception quantities, condition, reason, and evidence reference.
- Manager controls are disabled until a custom candidate is saved.
- Manager controls are role-gated to Warehouse Manager, Stock Manager, or System Manager context and update only candidate status/event posture.

## Review Expectations

Reviewers should confirm:

- no Stock Entry or stock mutation path is introduced;
- no native route or ERP document action is exposed;
- Overview does not expose active transfer input fields;
- Internal Transfer route renders one custom workflow page;
- candidate save calls only the custom draft method;
- manager posture calls only the custom manager decision method;
- no valuation/accounting/commercial or notification behavior appears.

## Manual Owner Check

Manual UI check is required after live alignment because W16E changes visible navigation and activates a new dedicated custom workflow page.

Expected owner check:

1. Open Warehouse Console Overview.
2. Confirm Internal Transfer appears as a custom workflow navigation card, not as a planned shell detail.
3. Open Internal Transfer.
4. Confirm source/target/count/evidence fields render cleanly.
5. Save a transfer candidate.
6. Confirm success copy says custom record only and no stock document/movement.
7. Confirm manager controls unlock only after custom candidate save for manager-capable users.
