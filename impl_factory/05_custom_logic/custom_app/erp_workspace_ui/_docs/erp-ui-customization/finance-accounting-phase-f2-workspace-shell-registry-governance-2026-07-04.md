# Finance & Accounting Phase F2 - Workspace Shell / Registry Governance

Date: 2026-07-04
Status: source-only implementation baseline for shell and governance foundation
Depends on: `finance-accounting-phase-f1-governance-scope-contract-2026-07-04.md`
Workspace family: Finance & Accounting
Visible shell label: Finance Control Desk

## Purpose

F2 introduces the Finance & Accounting workspace shell without financial data. It registers the workspace identity, route, sidebar target, static context methods, and governance manifest coverage so future Finance work starts from a controlled product surface instead of raw ERPNext Desk routes.

F2 does not approve accounting execution. It does not load AR/AP rows, accounting overview metrics, invoice data, GL data, bank data, tax data, close data, report output, exports, or custom review/request records.

## Implemented Scope

F2 includes:

- active backend workspace registry entry for `finance`;
- browser workspace registry entry for `finance`;
- Desk Page shell route `finance-control-desk`;
- static Finance & Accounting service context for shell/sidebar/search-disabled responses;
- governance manifest route/action entries for the shell only;
- Finance forbidden-mutation guard;
- registry and manifest unit coverage;
- README index entry.

F2 intentionally does not add:

- app-home/default-route assignment for accounting users;
- Finance worklist routes;
- Finance report routes;
- native ERP routes;
- ERPNext report API calls;
- Sales Invoice, Purchase Invoice, GL Entry, Payment Entry, Journal Entry, Account, Company, or Bank Transaction reads;
- write methods or custom review/request records.

## Shell Behavior

The Finance Control Desk shell communicates:

- Finance & Accounting is being introduced as a controlled accounting visibility foundation.
- Cycle 1 will begin with safe overview, receivables posture, payables posture, and hardening.
- No financial rows are loaded in F2.
- Posting, payment, reconciliation, tax filing, period close, write-off, exports, and native execution routes remain blocked.

The shell uses static markup only. It has no active financial cards, no sample amounts, no fake metrics, no disabled future buttons that look actionable, and no native ERPNext execution links.

## Registered Route

| Route key | Path | Classification | Shell | Notes |
| --- | --- | --- | --- | --- |
| `finance-control-desk` | `/desk/finance-control-desk` | `productized_overview` | `finance_control_desk_shell` | Static F2 shell. No financial rows or execution. |

## Backend Contract

The F2 service methods may return only static workspace context:

- `get_finance_control_desk_shell_context`
- `get_finance_control_desk_sidebar_context`
- `search_finance_control_desk_workspace`

The methods return no-effect flags and never read finance business data. Search returns unavailable/restricted empty results because Finance search is not active in F2.

Forbidden in F2 backend scope:

- `frappe.get_all` for finance business data;
- raw SQL;
- `ignore_permissions=True`;
- ERPNext report APIs;
- insert, save, submit, cancel, delete, set value, enqueue, email, notification, export, or file generation;
- native route strings as execution targets.

## Governance Manifest

F2 adds only shell-safe manifest entries:

- one productized overview route;
- one refresh/current-shell action;
- one sidebar navigation action;
- one Finance forbidden-mutation guard.

There are no Finance governed native exceptions and no Finance native actions in F2.

## Validation Expectations

Required before F2 acceptance:

- `git diff --check HEAD`;
- JavaScript syntax check for touched JS files;
- `python3 -m compileall -q erp_workspace_ui`;
- registry/governance unit tests;
- full unit suite if feasible;
- static scan for forbidden Finance execution terms in touched source;
- native route scan in touched source;
- cache cleanup/check;
- `git status --short --branch`.

Runtime/live alignment and protected gates are not part of F2.

## Deferred To Later Phases

- F3: safe accounting overview with aggregate posture only.
- F4: receivables posture and aging visibility.
- F5: payables posture and aging visibility.
- F6: security/stability hardening and Owner manual verification.
- Later cycles: cash/bank, GL/trial balance, tax, close, custom records, cross-workspace impact, exports, and any execution behavior.

## Boundary

F2 does not approve:

- GL Entry mutation;
- Journal Entry lifecycle;
- Payment Entry lifecycle;
- Sales Invoice lifecycle;
- Purchase Invoice lifecycle;
- bank reconciliation mutation;
- payment reconciliation mutation;
- tax filing/submission;
- Period Closing Voucher behavior;
- write-off execution;
- close execution;
- notification/email/customer/supplier external action;
- native ERP route execution;
- export/download;
- live alignment, commit, push, restart, migration, metadata reload, or protected gate.

## Recommended Next Step

Owner/Main Control reviews the F2 shell and validation results. If accepted, the next phase should be F3 planning for safe aggregate accounting overview only.
