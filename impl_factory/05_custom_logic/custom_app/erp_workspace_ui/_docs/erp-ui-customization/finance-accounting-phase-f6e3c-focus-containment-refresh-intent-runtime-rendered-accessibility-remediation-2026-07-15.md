# Finance & Accounting F6E3C Focus Containment, Refresh Intent, and Runtime-Rendered Accessibility Remediation

Date: 2026-07-15

## Decision context

F6E3B rejected F6E4 because the governed search-result outline could be clipped by its real overflow container, repeated identical Finance outcomes were not guaranteed to create a fresh polite status update, and Refresh could reclaim focus after the user deliberately moved elsewhere. F6E3C corrects those source-only accessibility defects and prepares the package for F6E3D independent review. It does not approve F6E4 live alignment or F6F closure.

## Implemented remediation

### Shared focus containment

- Managed sidebar navigation, header, utility, collapse, and search-input controls retain the shared three-pixel `#2563eb` focus outline.
- Governed search results now use a three-pixel inset `#2563eb` focus treatment. The indicator stays inside each rounded result box and cannot be clipped by the actual scroll container.
- Active/current navigation retains its border, shadow, radius, and `aria-current="page"` semantics.
- The production sidebar renderer is exercised directly for Sales, Procurement, Warehouse, and Finance at desktop, 390px, and 320px widths. Production search markup is exercised only where each workspace registry enables governed search.

### Finance announcements and Refresh intent

- The persistent polite status node is cleared and repopulated in a later microtask for every authoritative completion. Consecutive identical outcomes therefore produce distinct DOM mutation sequences while preserving the same live-region node.
- A generation check prevents a queued status update from repopulating after supersession or route departure.
- Completion copy is concise and business-facing. Initial load and user Refresh wording are distinguished; timestamps, values, identities, internal policy reasons, and technical exceptions are never announced.
- Refresh restoration is represented by a request-bound focus intent. The intent remains eligible when rendering replaces the focused Refresh control, but a `focusin` on another control cancels it. Settlement, supersession, and route departure release the listener.
- No extra Finance overview request is introduced. Existing deduplication, forced-refresh supersession, timeout, stale-response, error, and re-entry behavior remains authoritative.

## Runtime-rendered source evidence

The pinned Playwright Docker smoke executes the actual shared sidebar renderer for all four managed workspaces and the production search markup generators for search-enabled workspaces. It verifies compact sidebar container state at 390px and 320px, non-home active-route resolution, governed custom-route clicks, a vertically overflowing result list, first/last result focus containment, and desktop layout at 1366px.

The same smoke executes the actual Finance page render and request lifecycle with contract-valid backend fixtures. It covers:

- initial ready rendering and initial-load announcement;
- consecutive identical Refresh outcomes observed through live-region mutations;
- focus restoration when Refresh remains the user's intent;
- no focus theft after movement to a persistent sidebar control;
- controlled unavailable and controlled request-failure rendering;
- timeout without technical exception disclosure;
- stale success after newer unavailable and stale error after newer ready;
- same-turn route-departure suppression before transport dispatch;
- route departure invalidation and fresh return;
- ready zero-count copy versus unavailable copy.

Representative layout fixtures remain only for broad state/viewport geometry. They are not presented as authenticated browser evidence. Authenticated assistive-technology behavior and cross-workspace browser acceptance remain Owner checks for a later F6E4 gate.

## Scope and release truth

F6E3C changes no Finance service, query, role, permission, company-scope, Page metadata, accounting semantics, payload contract, amount authority, route priority, or execution boundary. The accepted F6E2 Finance service remains source/live aligned.

The source package contains these eleven classified candidates:

1. `_docs/erp-ui-customization/README.md` - F6E3C traceability entry.
2. `_docs/erp-ui-customization/finance-accounting-phase-f6e3-visual-accessibility-final-acceptance-preparation-2026-07-14.md` - existing F6E3 preparation record.
3. `_docs/erp-ui-customization/finance-accounting-phase-f6e3a-shared-accessibility-finance-refresh-remediation-2026-07-15.md` - existing F6E3A remediation record.
4. `_docs/erp-ui-customization/finance-accounting-phase-f6e3c-focus-containment-refresh-intent-runtime-rendered-accessibility-remediation-2026-07-15.md` - this record.
5. `erp_workspace_ui/finance_accounting/service.py` - accepted F6E2 hotfix, unchanged by F6E3C and already live aligned.
6. `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` - persistent announcements and request-bound Refresh focus intent.
7. `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` - contained result focus plus production renderer test hooks.
8. `erp_workspace_ui/tests/test_finance_accounting_resolver.py` - accepted F6E2 resolver coverage, unchanged by F6E3C.
9. `erp_workspace_ui/tests/test_finance_accounting_shell.py` - focused accessibility contract coverage.
10. `ui_smoke/finance_cycle1_source_smoke.js` - lifecycle, focus-intent, and announcement mutation evidence.
11. `ui_smoke/finance_cycle1_responsive_smoke.js` - actual-renderer and responsive browser evidence.

Only items 6 and 7 are candidates for a future runtime-only F6E4 alignment. Documentation, tests, and smokes are source evidence and must not be copied as runtime files unless separately approved.

| Future F6E4 runtime path | F6E3C source SHA-256 | Current live SHA-256 | Status |
| --- | --- | --- | --- |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `ef1b7102df5539bdb7bf69f744e7f55e45e39e01c8f2518095614afee7509373` | `8b06e2c3b1de1feb3366421e92d7299e27ef2b978a7040ae77310ef0d171ac70` | Intentional source-only accessibility difference |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `aa216cb9ccbae55980e826b70ecf91cf53db4c94e387ecf31a715ad9a9a17dbc` | `814ff0b95f949a365bfb44abea090e33df28d8c79304943439108881ed749f0e` | Intentional source-only shared focus difference |

The following unrelated dirty paths remain explicitly excluded:

- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`;
- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`;
- `ui_smoke/sales_final_acceptance_audit.js`;
- `a.out`.

## Boundaries and next gate

F6E3C adds no rows, identities, amounts, native reports/routes, exports, downloads, print, notification, email, portal, external action, posting, payment, reconciliation, write-off, tax, close, or execution. No live alignment, restart, cache clear, metadata reload, migration, permission change, staging, commit, push, or protected gate occurs.

The next permitted step is F6E3D independent counterpart review. F6E4 remains blocked until that review accepts this corrected source package, and F6F remains blocked until separately approved live alignment and authenticated browser acceptance pass.
