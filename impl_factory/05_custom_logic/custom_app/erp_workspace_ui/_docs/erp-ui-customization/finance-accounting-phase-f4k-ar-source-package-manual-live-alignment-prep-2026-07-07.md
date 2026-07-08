# Finance & Accounting Phase F4K - AR Source Package Manual / Live-Alignment Prep

Date: 2026-07-07
Status: docs-only source-review and stopped live-alignment-prep gap report
Depends on: F1 governance, F2 shell, F3 overview, F4A/F4A2/F4A3 policy, F4B resolver, F4C source-read policy, F4D count posture, F4E/F4G amount policy/contract, F4H/F4H1 amount implementation/hardening, and F4I1/F4J remediation
Workspace family: Finance & Accounting
Visible page label: Finance Control Desk

## Decision

F4K records the Finance AR source package for Owner/Main Control review, but it does not accept the package as live-alignment-prep ready.

Decision: stopped gap report.

Reason: the F4K review found source-copy and documentation-traceability gaps that should be resolved before any live-alignment prep approval:

- visible copy can overstate "no financial rows loaded" even though the backend internally reads bounded Payment Ledger Entry rows before returning aggregate-only amounts;
- visible copy still does not make the Sales Invoice count source vs Payment Ledger amount source difference clear enough for manual review;
- F4G remains a design-only document while later F4H/F4H1/F4I1/F4J source work exists without standalone phase documents, so this F4K package must explicitly reconcile the phase history.

F4K does not approve live alignment. It does not approve restart, metadata reload, migration, protected gates, commit, push, posting, payment, reconciliation, write-off, tax, close, email, notification, portal behavior, native ERPNext routes, reports, exports, downloads, print, customer rows, invoice rows, voucher rows, account rows, GL rows, Payment Ledger rows, or accounting execution.

If Owner/Main Control accepts this F4K gap report, the recommended next step is a separately approved F4K1 remediation focused on business-facing copy and source traceability. Live alignment itself remains blocked until explicitly approved in a later instruction after the F4K1 gaps are closed.

Follow-up note: F4K1 was created to remediate these copy and traceability gaps without changing accounting behavior.

## Documentation Provenance

F4G is intentionally design-only and does not by itself approve runtime amount exposure. Later Owner/Main Control instructions approved source-only F4H, F4H1, F4I1, and F4J work in this thread, but separate phase documents for those implementation/review turns were not present in the docs tree when F4K was prepared.

F4K therefore acts as the first consolidated documentation record for the post-F4G source state. It does not rewrite F4G's design-only decision. It records that later source phases implemented and hardened manager-only aggregate MMK Payment Ledger amount posture, while live alignment and execution remain blocked.

Traceability still needs improvement before live-alignment prep:

- either add focused F4H/F4H1/F4I1/F4J source-history notes, or keep this F4K document as the accepted consolidated source-history record;
- update visible Finance copy so users do not infer that the backend performs no bounded source reads;
- update visible Finance copy so count posture and amount posture are understood as related but separately sourced aggregate signals, not a reconciled accounting report.

## Current Accepted Finance State Through F4J

The Finance & Accounting stream now has a controlled Finance Control Desk source package:

- F1 established the governance and scope contract.
- F2 registered the Finance & Accounting workspace shell, route, registry entry, sidebar identity, and governance manifest coverage.
- F3 added role-aware read-only overview behavior with restricted, loading, unavailable, and ready states.
- F4A/F4A2/F4A3 defined conservative receivables visibility policy, Accounts Manager as the first manager-level Finance visibility role, and strict company scope rules.
- F4B implemented the role/company resolver foundation without business data.
- F4C documented and tested the receivables source-read contract.
- F4D implemented Accounts Manager-only aggregate receivables aging counts from permission-preserving Sales Invoice count reads.
- F4E/F4G defined the manager-only amount policy and Payment Ledger Entry voucher-outstanding source contract.
- F4H implemented manager-only aggregate MMK Payment Ledger amount posture without rows or identities.
- F4H1 added pagination and source-size fail-closed protection.
- F4I1/F4J remediated date semantics, payload context exposure, split receivable account handling, stale copy, and amount-ready/count-unavailable copy.

The source package remains visibility-only. It is not an accounting execution package.

## Implemented Source Scope For Review

### Finance Shell

The Finance Control Desk route is implemented for manual review as a controlled workspace surface:

- route/page: `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`;
- service: `erp_workspace_ui/finance_accounting/service.py`;
- registry/governance: workspace registry, runtime registry/sidebar, and governance manifest entries created in F2;
- behavior: role-aware shell, safe loading state, restricted state, unavailable state, no blank first-load expectation, and no native execution links.

The shell may show posture cards only. It should not return, show, link, export, or make actionable any row-level financial data or document links. F4K found that visible copy should be tightened to use this wording rather than implying that the backend performs no bounded aggregate source reads.

### Role And Company Resolver

The resolver is implemented for manual review as the Finance authority gate:

- `Accounts Manager` is the only role that can reach manager amount posture.
- `Accounts User` can reach limited Finance posture but cannot see raw counts or amounts in the current AR source package.
- `Auditor` remains a candidate only and does not receive amount visibility.
- `System Manager` alone is not Finance data authority.
- `Executive Approver` alone is not Finance data authority.
- Warehouse, Sales, Purchase, and Stock roles alone remain restricted for Finance data.
- User default company is not an authorization source.
- Company scope must come from Company User Permission or the accepted strict single-company fallback for eligible Finance roles.
- The accepted current company/currency is `Mingalar Mobile Distribution Co., Ltd.` / `MMK`.

### Receivables Count Posture

The count posture is implemented for manual review with these limits:

- source: `Sales Invoice`;
- role: Accounts Manager only;
- scope: server-side F4B company resolver only;
- source permission: `Sales Invoice` read permission check before count reads;
- query pattern: permission-preserving aggregate count calls;
- buckets: Current / not due, 1-30 overdue, 31-60 overdue, 61-90 overdue, and greater than 90 overdue;
- date basis: backend as-of date and Sales Invoice due date;
- response: bucket counts only, no rows, no amounts, no customer names, no invoice names, no routes, no reports, no exports, no print/download, no execution.

Accounts User count visibility remains blocked until a separate low-count/coarsening policy is approved.

### Manager-Only MMK Amount Posture

The amount posture is implemented for manual review with these limits:

- source: `Payment Ledger Entry`;
- semantic model: voucher-level outstanding semantics, not naive row sum;
- amount basis: Payment Ledger `amount` verified as company-currency using metadata;
- visible currency: MMK only for `Mingalar Mobile Distribution Co., Ltd.`;
- role: Accounts Manager only;
- company: F4B resolver-scoped company only;
- source gates: browser filters rejected, resolver required, approved company/currency required, source permission required, metadata verification required, and Payment Ledger adapter called only after those gates;
- pagination/performance: bounded `frappe.get_list` pages with a maximum row cap and fail-closed `payment_ledger_source_too_large` reason;
- date basis: due date only;
- missing due date: fail closed with no amount values;
- multiple due dates/payment terms: unsupported and fail closed;
- split receivable accounts: unsupported and fail closed, including allocation-side account splits;
- suppression: bucket amount values are suppressed for low voucher count or low internal customer diversity; grand total is omitted if any bucket is suppressed;
- response: aggregate bucket counts and MMK bucket amounts only when ready; no source rows, party names, voucher names, invoice names, account names, Payment Ledger row identifiers, GL detail, routes, reports, exports, print/download, or execution controls.

F4K does not accept this amount posture for live-alignment prep until the visible copy and traceability gaps in this document are resolved.

## Blocked Scope

The following remain blocked after F4K:

- customer rows, customer lists, customer IDs, and customer drilldown;
- invoice rows, invoice IDs, due-date rows, status rows, and invoice drilldown;
- voucher, account, GL Entry, Payment Ledger Entry, and party detail;
- native ERPNext reports, Form/List/Report routes, query reports, report pass-through, and route keys;
- export, download, print, file generation, and copied report output;
- Payment Entry, Journal Entry, Sales Invoice, Purchase Invoice, GL Entry, and Payment Ledger mutation;
- submit, cancel, save, delete, insert, set value, enqueue, email, notification, portal, customer action, and supplier action;
- payment, posting, reconciliation, write-off, tax filing, period close, and accounting execution;
- Payables, Cash/Bank, GL, Tax, Close, and cross-workspace accounting impact lanes.

## Manual Review Checklist

### Accounts Manager View

Owner/Main Control should verify:

- Finance Control Desk opens without a blank screen.
- The page shows read-only posture, not an accounting execution console.
- Company scope is the approved company and currency when the resolver gates pass.
- Receivables count posture appears only as aggregate bucket counts.
- Manager-only MMK amount posture appears only as aggregate bucket amounts when all amount gates pass.
- Suppressed amount buckets are clearly marked as suppressed without revealing customer or invoice counts.
- Visible copy says no row-level financial data is returned, shown, linked, exported, or actionable; it should not claim that no bounded internal source rows are read for aggregation.
- No customer names, invoice names, voucher names, account names, Payment Ledger identifiers, GL identifiers, due-date rows, status rows, route links, report links, export/download/print controls, or action controls appear.
- Copy does not overclaim posting, payment, reconciliation, tax, close, or write-off readiness.

### Accounts User View

Owner/Main Control should verify:

- Accounts User can see only the allowed limited Finance posture.
- Accounts User does not see raw AR counts.
- Accounts User does not see AR amounts, currency totals, customer rows, invoice rows, or drilldowns.
- The page explains unavailable posture calmly without exposing internal source details or native routes.

### Non-Finance / Restricted View

Owner/Main Control should verify:

- Non-finance users receive a restricted state.
- `System Manager` alone does not receive Finance data authority.
- `Executive Approver` alone does not receive Finance data authority.
- Sales, Procurement, Warehouse, and Stock users do not receive receivables posture data through Finance.
- Restricted views do not show the full Finance shell as if ready.

### Company And Currency Posture

Owner/Main Control should verify:

- The displayed company is `Mingalar Mobile Distribution Co., Ltd.` only when the resolver authorizes it.
- MMK is the only displayed amount currency in this phase.
- Browser-selected company, currency, account, customer, voucher, report, or route filters do not influence the backend.
- Multi-company, no-company, or unauthorized-company states remain unavailable/restricted rather than aggregating across companies.

### Identity And Native Route Exposure

Owner/Main Control should verify no visible UI or network response contains:

- customer, invoice, voucher, account, GL, Payment Ledger, party, payment, or journal identifiers;
- native `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `query-report` targets;
- export, download, print, email, notification, portal, submit, cancel, save, delete, insert, set value, enqueue, payment, posting, reconciliation, write-off, tax, or close controls.

## Live-Alignment Prep Checklist

F4K records the checklist needed for a later approval, but F4K does not mark the package live-alignment-prep ready. Execute none of these steps unless Owner/Main Control separately approves a later live-alignment-prep phase after F4K1 remediation.

### Source Files That Would Need Alignment Later

If Owner/Main Control later approves live alignment, the likely source package to align is:

- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`;
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-phase-f*.md`;
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/finance_accounting/service.py`;
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`;
- Finance tests under `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/tests/test_finance_accounting*.py`;
- Finance registry/governance files changed during F2: backend workspace registry, governance manifest, runtime workspace registry, runtime sidebar, and related registry/governance tests.

Do not include unrelated dirty files, especially AI assistant diagnostics or Sales smoke files.

### Required Validation Before Any Later Alignment

Run from `impl_factory/05_custom_logic/custom_app/erp_workspace_ui` before any approved live-alignment attempt:

```bash
git diff --check HEAD
node --check erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js
python3 -m compileall -q erp_workspace_ui
PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_finance_accounting*.py'
PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
```

Also run a focused static scan for forbidden Finance APIs/routes/actions:

- `frappe.get_all`;
- raw SQL and `frappe.db.sql`;
- `ignore_permissions`;
- native `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, and `query-report` targets;
- report pass-through;
- export/download/print;
- save, submit, cancel, delete, insert, set value, enqueue, sendmail, notification, portal, payment, posting, reconciliation, write-off, tax, close, and mutation behavior.

Clean Python caches after compile/test runs and confirm final `git status --short --branch`.

### Post-Alignment Manual Checks

Only after a separately approved live alignment, Owner/Main Control should check:

- `/desk/finance-control-desk` as Accounts Manager;
- `/desk/finance-control-desk` as Accounts User;
- `/desk/finance-control-desk` as a non-finance restricted user;
- refresh/reload behavior for no blank screen;
- restricted/unavailable states;
- no native route, report, export, download, print, or action controls;
- no row or identity exposure in visible UI;
- no accounting execution behavior.

## Owner Acceptance Criteria

Owner/Main Control acceptance of F4K means only this:

- Owner understands count posture and amount posture use different approved sources: Sales Invoice aggregate count reads for counts and Payment Ledger Entry voucher-outstanding semantics for manager-only MMK amounts.
- Owner accepts that Payment Ledger Entry semantics are used only for aggregate manager posture and not for row drilldown.
- Owner accepts that payment terms, missing due dates, split receivable accounts, metadata drift, source-size overflow, and ambiguous company/currency states fail closed.
- Owner accepts that low-population buckets may suppress amounts and that grand total is omitted when suppression exists.
- Owner accepts that Accounts User amount visibility and raw count visibility remain blocked.
- Owner accepts that there is no customer, invoice, voucher, account, Payment Ledger, GL, route, report, export, download, print, or action drilldown in this phase.
- Owner accepts this is visibility only and does not approve posting, payment, reconciliation, write-off, tax, close, notification, portal, or accounting execution.
- Owner accepts that live alignment still needs a separate explicit approval.

## Residual Risks And Caveats

| Risk | Current handling | Owner review need |
| --- | --- | --- |
| Visible row-boundary copy | Runtime returns aggregate-only payloads, but the page copy can imply no bounded source rows are internally read. | F4K1 should update copy to say no row-level financial data is returned, shown, linked, exported, or actionable. |
| F4G-to-F4J traceability | F4G remains design-only while later source work exists without separate phase docs. | Owner must accept F4K as the consolidated source-history record or request separate F4H/F4H1/F4I1/F4J docs. |
| Count-vs-amount source difference | Counts use Sales Invoice aggregate count reads; amounts use Payment Ledger voucher-outstanding semantics. | Owner must confirm the UI copy is clear enough and not read as a reconciled accounting report. |
| Payment Ledger semantic drift | Metadata check verifies company-currency amount field and tests assert adapter behavior. | Owner/Main Control should treat installed ERPNext Payment Ledger semantics as a manual review item before live alignment. |
| Missing due dates in count posture | Sales Invoice count buckets use due-date filters; missing due-date invoice handling remains a caveat. | Owner should confirm whether missing due-date invoices exist and whether count posture needs a separate fail-closed policy. |
| Payment terms | Unsupported. Multiple due dates fail closed. Payment schedule rows are not read. | Owner should confirm fail-closed behavior is acceptable before broader receivables exposure. |
| Split receivable accounts | Unsupported and fail closed, including allocation-side splits. | Owner should confirm split-account receivables can wait for a later policy. |
| Low-population leakage | Bucket amounts suppress below voucher/customer-diversity thresholds and omit grand total when suppressed. | Owner should confirm thresholds are acceptable for current business privacy. |
| Production-scale source size | Pagination and maximum source-row cap fail closed with no partial aggregate. | Owner should confirm source-size failure copy is acceptable after live review. |
| Internal reason wording | Some unavailable reasons are code-like and may be too technical for owner-facing UI. | F4K1 should translate visible reason copy without weakening backend policy reasons. |
| Accounts User operational usefulness | Accounts User still gets no raw counts or amounts. | Reopen only after low-count/coarsening policy approval. |

## F4K Stopped Gap Report

F4K should not proceed to live-alignment prep approval until these gaps are closed or explicitly accepted by Owner/Main Control:

1. Runtime/page copy must distinguish aggregate source reads from row-level data exposure.
2. Runtime/page copy must make the Sales Invoice count source and Payment Ledger amount source difference clear enough for manual review.
3. Documentation traceability must reconcile F4G design-only status with later F4H/F4H1/F4I1/F4J source work.
4. Owner/Main Control must decide whether missing-due-date Sales Invoice count behavior needs a separate fail-closed policy before live alignment.

## Recommended Next Step

Recommended next phase: `F4K1 Finance AR Copy And Traceability Remediation`.

Do not perform live alignment, restart, metadata reload, protected gates, commit, push, Payables implementation, GL/Cash/Tax/Close work, row drilldown, native reports/routes, exports, or accounting execution from this document.
