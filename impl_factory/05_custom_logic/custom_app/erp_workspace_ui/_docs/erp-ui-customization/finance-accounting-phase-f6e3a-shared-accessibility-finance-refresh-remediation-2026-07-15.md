# Finance & Accounting F6E3A Shared Accessibility and Finance Refresh Remediation

Date: 2026-07-15
Status: Source remediation prepared; F6E4 not approved

## Purpose

F6E3A closes the focused accessibility findings recorded by F6E3 without changing Finance authority or accounting behavior. It retains the accepted Finance hero-title contrast and the F6E3 cross-workspace manual checklist, adds shared keyboard-focus visibility, makes Finance Refresh completion accessible, and removes the ambiguous visible `No counts` label from unavailable Receivables and Payables cards.

This is source-only preparation. It does not approve live alignment, authenticated F6E4 acceptance, F6F closure, or final Finance Cycle 1 closure.

## Defects and corrections

### Shared managed-workspace focus

The shared sidebar previously replaced the browser outline with a near-white ring on a light surface. F6E3A applies one three-pixel `#2563eb` focus-visible outline to managed-workspace navigation, utility buttons, the workspace header, collapse control, search input surface, and governed search results. The ring remains distinct for active items and applies in expanded and collapsed layouts across Sales, Procurement, Finance, and Warehouse. The active navigation item also exposes `aria-current="page"`.

The source contrast check measures the focus indicator at greater than 3:1 against white. No route, target, search, workspace priority, or content behavior changes.

### Finance Refresh completion

Finance Refresh now records whether the Refresh control held focus when the approved refresh began. Only the authoritative request settlement may restore focus to the replacement Refresh button and update the persistent polite status region. The live region remains outside the replaced render host and busy subtree, so a refresh does not recreate it. Ready, restricted, controlled-unavailable, rejected-payload, and controlled transport-failure outcomes use concise business-facing announcements.

The existing request coordinator remains authoritative. Equivalent non-forced loads still deduplicate, a forced refresh still supersedes an older load, stale success and stale failure cannot render or cache, timeout remains bounded, and route departure still invalidates pending authority. The accessibility layer performs no additional backend read.

### Unavailable count labels

The backend wire contract remains unchanged. When a validated Receivables or Payables card is not ready, the browser displays `Unavailable` instead of the ambiguous `No counts`. A ready posture with verified zero bucket counts remains ready and displays its aggregate bucket detail, including numeric zero values.

Frontend validation now rejects a Receivables or Payables card whose ready/unavailable state or value contradicts its nested posture. Internal reasons remain excluded from visible copy and announcements.

## F6E2 and F6E3 evidence retained

- `finance.lead@meet.com` and `accounts.ygn.01@meet.com` loaded Finance Control Desk after F6E2 without a `User Permission` modal.
- Accounts Manager remained limited to approved company-scoped aggregate posture.
- Accounts User received no manager-only AR amounts or AP counts.
- No row-level identities, native Finance reports/routes, exports, or execution actions appeared.
- The Finance title retains the explicit `#f8fafc` light-on-dark color and the F6E3 minimum contrast contract.
- The F6E3 desktop, 390px, and 320px responsive checks now cover ready, restricted, and unavailable Finance states at every width. Its expanded Finance, Sales, Procurement, Warehouse, and cross-workspace authenticated checklist remains part of the future F6E4 package.

## F6E4 checklist additions

In addition to every F6E3 manual check, F6E4 must confirm:

1. Keyboard focus is clearly visible on managed sidebar navigation and utility buttons in Sales, Procurement, Finance, and Warehouse, including active and collapsed states.
2. With keyboard focus on Finance Refresh, success, controlled unavailable, and controlled failure each return focus to the replacement Refresh control.
3. A screen reader or accessibility inspector observes one polite, non-technical completion announcement for the authoritative request only.
4. A late stale success or failure does not announce, restore focus, render, cache, or replace the current Finance state.
5. Unavailable Receivables and Payables cards display `Unavailable`; ready zero-count posture appears only as ready aggregate detail and is not described as unavailable.
6. No raw reason code, permission message, accounting identity, native report/route/export, or execution control appears.

## Source and live status

F6E3A intentionally creates two runtime source/live differences pending a separately approved F6E4 alignment review:

| Future runtime alignment path | Source SHA-256 | Current live SHA-256 | Reason |
| --- | --- | --- | --- |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `a42ca4e8a6a8b6a4055b42a583a31f708330dbc0093be630c0e542d0ebb49bdc` | `8b06e2c3b1de1feb3366421e92d7299e27ef2b978a7040ae77310ef0d171ac70` | F6E3 title contrast plus F6E3A Refresh and unavailable-label accessibility |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `009e17df1ca55b66e2a5e8db0d990b359210c791243dfb91de406953978543b0` | `814ff0b95f949a365bfb44abea090e33df28d8c79304943439108881ed749f0e` | Shared managed-workspace focus visibility and current-item semantics |

The F6E3A document, README entry, focused test changes, and smoke changes are source/review evidence, not live runtime files. The accepted F6E2 Finance service remains aligned and is not part of the future F6E3A runtime allowlist.

### Exact source candidate manifest

The source package contains exactly these ten classified candidates:

1. `_docs/erp-ui-customization/README.md` - F6E3A index and existing F6E3 traceability.
2. `_docs/erp-ui-customization/finance-accounting-phase-f6e3-visual-accessibility-final-acceptance-preparation-2026-07-14.md` - existing F6E3 acceptance preparation.
3. `_docs/erp-ui-customization/finance-accounting-phase-f6e3a-shared-accessibility-finance-refresh-remediation-2026-07-15.md` - this remediation record.
4. `erp_workspace_ui/finance_accounting/service.py` - accepted F6E2 resolver hotfix; unchanged by F6E3A and already source/live aligned.
5. `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` - F6E3 title contrast and F6E3A Refresh/card accessibility.
6. `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` - shared managed-workspace focus visibility.
7. `erp_workspace_ui/tests/test_finance_accounting_resolver.py` - accepted F6E2 resolver coverage.
8. `erp_workspace_ui/tests/test_finance_accounting_shell.py` - F6E2 plus F6E3A shell/accessibility contract coverage.
9. `ui_smoke/finance_cycle1_responsive_smoke.js` - title, focus, responsive-state, and browser Refresh evidence.
10. `ui_smoke/finance_cycle1_source_smoke.js` - request authority, stale-response, business-copy, and live-region source evidence.

Only items 5 and 6 are candidates for a future controlled F6E4 live alignment. Items 1-3 and 7-10 are documentation, test, or smoke evidence; item 4 is already aligned and must not be recopied for F6E3A.

The following unrelated dirty paths are explicitly excluded:

- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`;
- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`;
- `ui_smoke/sales_final_acceptance_audit.js`;
- `a.out`.

## Deferred and blocked scope

F6E3A does not add or approve:

- Finance service, query, role, permission, company-scope, Page metadata, accounting-semantic, or payload-contract changes;
- AR/AP rows or customer, supplier, invoice, voucher, account, Payment Ledger, GL, bank, or Payment Schedule identities;
- AP amounts or Payment Schedule aging/allocation;
- native reports, routes, exports, downloads, print, email, notifications, portal, or external actions;
- posting, payment, reconciliation, write-off, tax, close, or other accounting execution;
- Sales, Procurement, Warehouse, search, route, or landing behavior changes.

## Next gate

The next permitted step is independent source review of F6E3A, followed by explicit Owner/Main Control approval for F6E4 controlled live alignment and authenticated cross-workspace browser acceptance. F6F remains blocked until F6E4 passes.
