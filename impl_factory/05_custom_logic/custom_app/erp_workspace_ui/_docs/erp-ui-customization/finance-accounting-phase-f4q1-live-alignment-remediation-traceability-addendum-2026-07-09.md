# Finance & Accounting Phase F4Q1 - Live Alignment Remediation Traceability Addendum

Date: 2026-07-09
Status: docs-only traceability addendum before any controlled staging decision
Depends on: F4O, F4O1, F4O2, F4O3, F4O4, F4O5, F4O6, F4P, and F4Q
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk
Custom page route: `finance-control-desk`
Desk page path: `/desk/finance-control-desk`

## Decision

Decision: traceability addendum created.

F4Q1 records the live alignment and remediation sequence that made the Finance Control Desk available for Owner manual browser review. It exists to make the future source package and staging decision auditable.

F4Q1 is documentation only. It does not stage files, commit, push, live-align, restart, reload metadata, migrate, run protected gates, change runtime code, expand Finance behavior, or approve accounting execution.

## Traceability Ledger

### F4O - Finance AR Live Alignment For Manual Browser Review Only

Purpose: align the accepted Finance AR source package to the live app so Owner could manually inspect `/desk/finance-control-desk`.

Recorded scope:

- copied accepted Finance source/runtime files needed for manual browser review;
- kept the scope limited to Finance workspace files and accepted shared registry/sidebar/governance files;
- did not add Payables, GL, Cash, Tax, Close, row drilldown, native reports, native routes, exports, print, or execution behavior;
- did not run protected gates, commit, push, migrate, or metadata reload.

Outcome: direct route testing reached the Finance Control Desk path, but Page metadata access blocked approved Finance users until F4O1.

### F4O1 - Finance Control Desk Page Metadata / Role Access Reload

Purpose: resolve the live Frappe Page permission blocker for approved Finance roles.

Problem observed:

- `finance.lead@meet.com` and `accounts.ygn.01@meet.com` hit Page access errors before Finance page logic could run.

Recorded remediation:

- limited the fix to Finance Control Desk Page metadata/role access;
- allowed `Accounts Manager` and `Accounts User` to open the custom Page;
- did not grant broad global Page access;
- did not change accounting DocType permissions;
- did not change Sales Invoice, Payment Ledger Entry, GL Entry, Payment Entry, Journal Entry, Account, Customer, Company, Bank, Tax, or reconciliation permissions.

Outcome: Page access advanced far enough for Finance backend context calls, which exposed the Company field-permission issue handled in F4O2/F4O3.

### F4O2 - Finance Company Field Permission Fix

Purpose: remove the live `Company.disabled` field-permission modal for approved Finance users without broad Company permission grants.

Problem observed:

- browser showed `Permission Error: You do not have permission to access field: Company.disabled` for both Finance users.

Recorded remediation:

- removed the Finance runtime resolver dependency on `Company.disabled`;
- preserved company scoping and fail-closed behavior;
- did not grant broad Company permissions;
- did not add `ignore_permissions`, raw SQL, accounting permission mutation, native routes, reports, exports, or execution behavior.

Outcome: source logic no longer depended on `Company.disabled`, but live browser still showed the stale modal until the backend worker was restarted in F4O3.

### F4O3 - Company.disabled Runtime Drift Diagnosis And Stale Worker Resolution

Purpose: determine why the browser still showed `Company.disabled` after the F4O2 source patch.

Problem observed:

- source and live file inspection indicated the patched service no longer depended on `Company.disabled`, but the browser still surfaced the old error.

Recorded remediation:

- diagnosed stale live Python worker/module state as the likely cause;
- performed the minimal backend restart and cache clear needed for the patched Finance service to run;
- did not change accounting permissions;
- did not grant Company field access;
- did not add `ignore_permissions`, raw SQL, native routes, reports, exports, or execution behavior.

Outcome: Finance page advanced past the Company field issue and then exposed a User Permission read blocker handled in F4O4.

### F4O4 - Finance User Permission Resolver Fail-Closed Fix

Purpose: prevent Finance users from seeing a modal exception when the resolver attempted to read User Permission records.

Problem observed:

- browser showed `Insufficient Permission for User Permission` after the Company field issue was resolved.

Recorded remediation:

- avoided direct User Permission reads for the current single-company MMK fallback path;
- used the accepted single-company site fallback for eligible Finance users;
- preserved multi-company controlled unavailable behavior where explicit scope is required;
- did not grant broad User Permission access;
- did not use `ignore_permissions`, raw SQL, or broad accounting permissions;
- did not expose native routes, reports, exports, or execution behavior.

Outcome: both `finance.lead@meet.com` and `accounts.ygn.01@meet.com` could load Finance context without the User Permission modal. The manager path then exposed the aggregate query syntax issue fixed in F4O5.

### F4O5 - Finance Manager Aggregate Query Syntax Fix

Purpose: fix the manager-only aggregate count query that used unsupported Frappe `get_list` field-string syntax.

Problem observed:

- `finance.lead@meet.com` saw `SQL functions are not allowed as strings in SELECT: count(name) as count. Use dict syntax like {'COUNT': '*'} instead.`
- `accounts.ygn.01@meet.com` did not see the modal because Accounts User remains blocked from manager-only aggregate posture.

Recorded remediation:

- replaced the invalid `count(name) as count` string with Frappe-supported aggregate dict syntax;
- kept the read permission-preserving through `frappe.get_list`;
- did not use raw SQL, `frappe.get_all`, or `ignore_permissions`;
- did not expose rows, identities, native routes, reports, exports, print, or execution behavior.

Outcome: manager aggregate counts loaded without the SQL syntax modal, while Accounts User remained safe and did not receive manager-only amount buckets.

### F4O6 - Finance Login Landing / Default Workspace Routing

Purpose: route approved Finance users to the Finance Control Desk from root login while preserving existing Sales, Procurement, Warehouse, and non-Finance behavior.

Problem observed:

- manual direct route worked, but `https://meet.erpbosai.com/` root login did not automatically land Finance users on the Finance Control Desk.

Recorded remediation:

- added Finance roles to the existing role-based Desk home policy;
- routed `Accounts Manager` and `Accounts User` to `finance-control-desk`;
- preserved workspace priority as Sales, then Procurement, then Finance, then Warehouse fallback;
- did not change Finance AR data logic;
- did not broaden accounting permissions;
- did not expose native routes, reports, exports, or execution behavior.

Outcome: `finance.lead@meet.com` and `accounts.ygn.01@meet.com` resolve to `finance-control-desk` through root-login boot home behavior.

### F4P - Finance AR Manual Browser Review Acceptance

Purpose: record Owner/Main Control manual browser acceptance after F4O-F4O6 remediation.

Owner observed and accepted:

- `/desk/finance-control-desk` direct route loads;
- `https://meet.erpbosai.com/` root login routes Finance users correctly;
- `finance.lead@meet.com` lands on the Finance Control Desk;
- `accounts.ygn.01@meet.com` lands on the Finance Control Desk;
- Page permission error no longer appears;
- `Company.disabled` permission modal no longer appears;
- User Permission modal no longer appears;
- SQL aggregate syntax modal no longer appears;
- Finance page remains read-only and aggregate-only;
- no execution expansion is approved.

Outcome: manual browser review is accepted for the current F4 AR posture scope only.

## Remaining Boundaries

F4Q1 keeps these boundaries unchanged:

- no accounting execution;
- no Payables, GL, Cash, Tax, or Close expansion;
- no customer rows, invoice rows, voucher rows, account rows, Payment Ledger rows, or GL rows;
- no customer, invoice, voucher, account, Payment Ledger, or GL drilldown;
- no native ERPNext Form, List, Report, query-report, export, download, or print surfaces;
- no Payment Entry, Journal Entry, Sales Invoice lifecycle, Purchase Invoice lifecycle, GL mutation, reconciliation, write-off, tax filing, period close, customer notification, email, portal, or external action;
- no accounting permission broadening;
- no staging, commit, push, protected gate, migration, metadata reload, restart, or live alignment.

## Staging Implication

F4Q classified the accepted Finance package for later controlled staging and identified a traceability caveat: F4O-F4O6 were recorded in turn outputs and summarized in F4P, but not as standalone docs.

F4Q1 resolves that documentation gap by adding this traceability record. It does not by itself approve staging or commit readiness.

A later staging phase must still use the exact F4Q include/exclude list, exclude unrelated dirty files and generated artifacts, and receive explicit Owner/Main Control approval before staging.

## Recommended Next Step

Recommended next step: `F4Q2 controlled staging approval` only if Owner/Main Control is ready to stage the exact accepted Finance package.

Do not stage, commit, push, live-align, restart, reload metadata, run protected gates, or start F5 Payables until explicitly approved.
