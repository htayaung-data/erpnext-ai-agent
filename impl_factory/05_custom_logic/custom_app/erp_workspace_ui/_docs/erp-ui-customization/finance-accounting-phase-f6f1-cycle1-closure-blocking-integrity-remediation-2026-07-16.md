# Finance Accounting Phase F6F1 Cycle 1 Closure-Blocking Integrity Remediation

Date: 2026-07-16

## Decision

The source package is ready for fresh independent F6F1 counterpart review. It is not Finance Cycle 1 closure, live-alignment approval, staging approval, or release approval.

## Closure-Blocking Findings Remediated

### Stale Financial DOM

Finance now clears cached overview authority, prior rendered aggregate counts, MMK values, retained status text, and prior posture markup before every replacement request begins. Refresh, supersession, wrapper hide, cache invalidation, route return, timeout, transport failure, and stale late settlement cannot preserve or restore the old manager posture.

The persistent polite status region remains in its Finance-owned presentation shell. Only neutral loading or controlled unavailable markup remains while a fresh authoritative response is pending or cannot be validated.

### Payables As-Of Completeness

Installed ERPNext source proves that Purchase Invoice outstanding is recalculated from Payment Ledger activity without an as-of posting-date cutoff. Therefore a current Purchase Invoice.outstanding_amount cannot be treated as historical truth when future payable ledger activity exists.

The AP count posture now:

- proves read permission for both Purchase Invoice and Payment Ledger Entry before source reads;
- performs one strict aggregate Payment Ledger probe scoped to the selected company, Supplier party type, active ledger rows, and posting dates after the requested as-of date;
- returns controlled unavailable on any selected-company future activity, denied permission, malformed aggregate, ambiguous multiple aggregate rows, unsupported source form, or read failure;
- emits no partial buckets and no source rows, dates, amounts, suppliers, invoices, vouchers, accounts, parties, or Payment Ledger identities.

The probe is intentionally conservative. The installed outstanding recomputation filters party and account relationships but not `account_type`, so the gate deliberately omits an `account_type` filter that could under-detect future Supplier activity. It does not interpret payment allocations and does not implement payment-schedule aging or AP amounts.

## Direct Hardening

- Finance raw payload validation now requires exact Cycle 1 phase, scope_mode, company_scope_required, and financial_data_enabled values before financial rendering or caching.
- Every Finance permission-preserving list read now uses one message-safe adapter. A caught source denial removes only messages queued by that failing read, preserving prior messages while preventing a controlled unavailable response from carrying a Frappe permission modal.
- Payment Ledger page adapters accept only actual lists; falsey scalars, mappings, tuples, and malformed rows fail closed.
- Browser MMK amount validation accepts only non-negative fixed-scale decimal strings from the validated backend contract.
- F1 and F2 artifacts are directly indexed from the Finance README.

## Validation Evidence

- Diff integrity: passed.
- Finance JavaScript and smoke syntax: passed.
- Python compilation: passed.
- Focused Finance tests: 195 passed.
- Cross-workspace Sales, Procurement, Warehouse, routing, registry, and governance tests: 429 passed.
- Full unit discovery: 624 passed.
- Finance source lifecycle smoke: passed.
- Pinned Docker actual-renderer/responsive smoke at 1366px, 390px, and 320px: passed.
- Static forbidden-API and boundary scans are clean, generated Python caches were removed, and the Git index remains empty.

## Source and Live Runtime State

The task made no live or external-state change.

| Runtime path | Source SHA-256 | Live SHA-256 | Status |
| --- | --- | --- | --- |
| erp_workspace_ui/finance_accounting/service.py | f7a5aa8c82011b385cc0c5963575162ace51341477286c054fb9dbcc8290ecad | e5870574d11e4d5d1754814f5f5faf90df645ce47c16ebee73e2e7505023af9e | Expected F6F1 source-only difference |
| erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js | 52356627d4be4843c200c51a3b1bb11c070b5fdb4c51e2f26e5952ff94011e0c | d05b6bce8ca5f755e871e1814435580d55cbd2c8fe691de7e8f98fac96c4b72c | Expected F6F1 source-only difference |

All other previously aligned Finance Cycle 1 runtime paths remain outside the F6F1 runtime change scope.

## Exact F6F1 Source Candidate

1. _docs/erp-ui-customization/README.md
2. _docs/erp-ui-customization/finance-accounting-phase-f6f1-cycle1-closure-blocking-integrity-remediation-2026-07-16.md
3. erp_workspace_ui/finance_accounting/service.py
4. erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js
5. erp_workspace_ui/tests/test_finance_accounting_payables_count.py
6. erp_workspace_ui/tests/test_finance_accounting_receivables_amount.py
7. erp_workspace_ui/tests/test_finance_accounting_shell.py
8. ui_smoke/finance_cycle1_source_smoke.js
9. ui_smoke/finance_cycle1_responsive_smoke.js

## Complete Current Closure Source Dependency Manifest

The current closure source package contains 17 dirty Finance candidates. The nine paths above are the direct F6F1 delta. The following eight paths are accepted, uncommitted F6E2-F6E4C predecessor dependencies that remain necessary for the complete source package and its evidence:

1. _docs/erp-ui-customization/finance-accounting-phase-f6e3-visual-accessibility-final-acceptance-preparation-2026-07-14.md
2. _docs/erp-ui-customization/finance-accounting-phase-f6e3a-shared-accessibility-finance-refresh-remediation-2026-07-15.md
3. _docs/erp-ui-customization/finance-accounting-phase-f6e3c-focus-containment-refresh-intent-runtime-rendered-accessibility-remediation-2026-07-15.md
4. _docs/erp-ui-customization/finance-accounting-phase-f6e3e-production-renderer-geometry-governed-search-aria-managed-route-active-state-remediation-2026-07-15.md
5. _docs/erp-ui-customization/finance-accounting-phase-f6e4a-page-host-geometry-trailing-scroll-remediation-2026-07-15.md
6. _docs/erp-ui-customization/finance-accounting-phase-f6e4c-finance-live-status-containment-nested-scroll-remediation-2026-07-16.md
7. erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js
8. erp_workspace_ui/tests/test_finance_accounting_resolver.py

The 17 candidates are one closure source dependency set for future controlled staging classification. The four unrelated exclusions below are separate, and no dirty path is unclassified.

## Explicit Exclusions

- ../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py
- ../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py
- ui_smoke/sales_final_acceptance_audit.js
- a.out

## Boundaries

F6F1 adds no AP amounts, payment-schedule aging, row payloads, identities, native Finance reports or routes, exports, downloads, print, notifications, external actions, permissions, metadata changes, accounting mutation, or execution.

No live alignment, restart, site-cache clear, metadata reload, migration, staging, commit, push, or protected gate occurred.

## Next Gate

Run the independent F6F1 counterpart review. F6F closure remains blocked until that review accepts the source package and any later live alignment and authenticated browser retest are separately approved and completed.
