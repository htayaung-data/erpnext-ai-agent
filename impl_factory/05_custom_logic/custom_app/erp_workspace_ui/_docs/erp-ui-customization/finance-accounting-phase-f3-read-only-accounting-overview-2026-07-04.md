# Finance & Accounting F3 Read-Only Accounting Overview - 2026-07-04

## Scope

F3 introduces the first Finance Control Desk overview posture. It remains read-only and intentionally minimal.

Implemented:
- role-aware overview context via `get_finance_control_desk_overview_context`;
- accounting/audit-role overview gate separate from shell visibility;
- user-default-company scope check without scanning Company records;
- small posture cards for workspace readiness, company scope, fiscal period posture, receivables posture, payables posture, and ledger posture;
- no-effect flags;
- frontend loading, ready, restricted, and unavailable states;
- tests for role, company, frontend call, and forbidden source boundaries.

## Data Boundary

F3 does not load accounting rows, document rows, customer or supplier balances, account balances, ledger entries, bank data, tax data, close records, monetary values, reports, exports, or native Finance routes.

The only scoped value displayed in a ready overview is the current user default company label. If no default company is available, the overview returns a controlled unavailable state.

## Role Boundary

Shell visibility remains available to `Accounts User`, `Accounts Manager`, `Auditor`, and `System Manager`. F3 overview posture is narrower: `Accounts User`, `Accounts Manager`, and `Auditor`. `System Manager` alone does not grant F3 overview access.

## Deferred

Deferred to later owner-approved phases:
- AR/AP counts and aging posture;
- customer/supplier-level balances;
- currency and amount display;
- fiscal period and close posture reads;
- GL, trial balance, bank/cash, tax, and cross-workspace accounting impact;
- custom review/request records;
- any posting, payment, reconciliation, tax, close, write-off, export, notification, or native route behavior.

## Validation

Required validation for this phase includes JS syntax, Python compile, Finance tests, registry/governance tests, full unit discovery, forbidden-pattern scans, and cache cleanup. No live alignment, restart, migration, metadata reload, protected gate, commit, or push is part of F3 source implementation.
