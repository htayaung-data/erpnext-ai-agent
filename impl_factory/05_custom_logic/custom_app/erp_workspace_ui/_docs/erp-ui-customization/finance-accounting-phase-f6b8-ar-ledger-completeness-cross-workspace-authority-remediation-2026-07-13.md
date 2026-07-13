# Finance & Accounting F6B8 - AR Ledger Completeness and Cross-Workspace Authority Remediation

Date: 2026-07-13
Status: source-only remediation; final independent counterpart re-review required

## Decision context

F6B7 found that Finance Cycle 1 could not advance while supported Payment Entry or Journal Entry activity could be omitted from Payment Ledger correlation, user defaults could influence amount rounding, a browser-global target bridge could bypass managed-workspace governance, and Sales or Procurement requests could outlive their query or route authority.

F6B8 addresses those findings only. The first four read-only reviews then identified additional fail-closed, dispatch, payload, and generation defects. Those findings were integrated into this source package and are recorded below. F6C remains blocked until a fresh independent review accepts the corrected package.

No source was copied to live. No staging, commit, push, restart, site-cache clear, metadata reload, migration, permission change, protected gate, or accounting execution occurred.

## Implemented remediation

### AR Payment Ledger completeness

- Selected-company Sales Invoice identities are collected internally through bounded, permission-preserving, deterministically ordered reads. They are never returned, logged, cached in browser state, or rendered.
- The primary Payment Ledger read remains selected-company, Receivable, Customer, non-delinked, and as-of scoped.
- A separate bounded, permission-preserving anomaly probe checks rows that reference or purport to be the selected Sales Invoice population. It prevents wrong-company, wrong-account, malformed, unsupported, orphaned, or misdirected activity from being silently filtered before validation.
- Every supported Payment Entry or Journal Entry activity must correlate with an exact self-originating Sales Invoice basis using the deployed Payment Ledger relationship fields. Missing basis, ambiguous relation, unknown voucher type, malformed identity, wrong company, duplicate activity identity, split-account ambiguity, future activity, due-date disagreement, or pagination overflow fails the entire manager amount posture closed.
- Activity uniqueness includes `voucher_detail_no`; distinct Journal Entry lines remain representable while replayed logical activity fails closed.
- Payment Ledger checkbox fields are parsed strictly. Missing or malformed values fail closed instead of being interpreted as false.
- Failure returns no partial bucket amount, grand total, source identity, source row, document, browser cache value, or ready runtime flag.
- Existing exact Sales Invoice and Payment Ledger voucher-set reconciliation remains mandatory after ledger-completeness validation.
- Count-only AR posture may remain independently available only when its own schedule, date, company, permission, and aggregate contracts pass. UI copy continues to distinguish Sales Invoice counts from Payment Ledger MMK amounts.

F6B8 does not add credit-note remapping, Payment Schedule aging, installment allocation, accounting rows, or posting authority.

### Authoritative rounding

- Finance no longer reads a user or global default for rounding.
- Currency precision remains sourced from ERPNext `get_currency_precision()`.
- Decimal quantization uses the deployed cached System Settings policy through `frappe.get_system_settings`.
- Missing, malformed, unsupported, or unavailable rounding authority or currency precision fails the manager amount posture closed.
- User defaults cannot alter Finance rounding. Fixed-scale decimal strings are the browser contract; binary float is never the authoritative amount representation.

### Target-dispatch governance

- The legacy browser-global `executeTarget` bridge is explicitly removed on runtime initialization.
- The only public shared-sidebar dispatcher is `executeSidebarTarget`. It first requires an active managed route, resolves the current workspace, and validates the exact workspace target immediately before private dispatch.
- The shared private dispatcher contains no native new-document, form, list, report, export, print, or execution branch.
- Managed search requires `workspace-search.v1`, exact workspace, route, request token, normalized query, explicit target kind, and validated target payload before storage, rendering, and dispatch.
- Child-page helpers no longer export generic `routeToDoc`, `routeToList`, or `routeToWorklist` browser functions. Script re-evaluation also deletes stale copies of all three helpers before publishing the approved helper set. The retained Sales helper is restricted to Sales-owned routes and the established exact Sales managed-form exceptions; it is not a cross-workspace or arbitrary target bridge.
- Sales and Procurement page-local dispatchers now accept custom app-owned worklist/report/page targets only. They do not interpret arbitrary native target kinds.
- Finance sidebar and posture-card contracts reconstruct approved copy from structured state. Workspace, overview, company-scope, period-scope, and other directly rendered Finance strings must match exact backend-owned copy contracts; business-looking identity or amount text is rejected before normalization, caching, or display.
- Native Frappe behavior outside managed workspaces remains Frappe-owned.

### Sales and Procurement request isolation

- Sales inquiry authority now combines a route epoch with independent suggestion, search, and AI generations. A suggestion-focus change cannot cancel or strand an active Search or AI request.
- Sales input, Clear, wrapper hide, and route departure invalidate the relevant authority immediately and settle all pending visual state. Late results cannot render after a newer query or route epoch.
- Procurement Quick Find binds options and selection to workspace, route, normalized query, and generation. Route departure clears the timer, results, selection preview, and status.
- Procurement revalidates authority immediately before storing or rendering a selection. A retained DOM option cannot restore stale state after route departure and return.
- Both workspaces retain their intended same-route behavior while rejecting stale result storage, rendering, insertion, or dispatch.

### Landing and registry parity

- Browser root fallback follows the approved server order exactly: Sales, Procurement, Finance, Warehouse.
- The Procurement browser fallback uses `procurement-console-home`, matching the server launcher.
- Python and browser registries include the active managed RFQ route and context/save/item-default methods.
- Browser Warehouse methods include the active customer-return and supplier-return draft and manager-decision methods present in the Python registry.
- Existing direct routes and role priorities for Sales, Procurement, Warehouse, and Finance remain unchanged.

## Independent review integration

The first F6B8 read-only reviews reported concrete defects. The main agent accepted and remediated:

- wrong-company or malformed Payment Ledger rows being filtered before validation;
- logical duplicate activity detection that relied only on source row name;
- stale browser-global and child-helper target surfaces;
- unmanaged-route invocation of the sidebar dispatcher;
- Finance text fields that could carry identity, route, or action values;
- Sales cross-channel generation cancellation;
- Procurement stale option storage after route return;
- stale manifest, hash, and validation evidence.

No reviewer was permitted to edit source or make the final decision. A fresh counterpart re-review is required after the validations in this document.

## Exact Finance/F6 source candidate manifest

The following 40 paths are the complete future source candidate. They are not staged by F6B8.

### Documentation

1. `README.md`
2. `_docs/erp-ui-customization/README.md`
3. `_docs/erp-ui-customization/finance-accounting-phase-f6b-cycle1-grouped-source-remediation-2026-07-11.md`
4. `_docs/erp-ui-customization/finance-accounting-phase-f6b1-closure-blocking-correctness-remediation-2026-07-11.md`
5. `_docs/erp-ui-customization/finance-accounting-phase-f6b3-closure-blocking-finance-shared-runtime-remediation-2026-07-13.md`
6. `_docs/erp-ui-customization/finance-accounting-phase-f6b5-finance-amount-integrity-shared-search-isolation-remediation-2026-07-13.md`
7. `_docs/erp-ui-customization/finance-accounting-phase-f6b6-ar-voucher-set-integrity-search-generation-remediation-2026-07-13.md`
8. `_docs/erp-ui-customization/finance-accounting-phase-f6b8-ar-ledger-completeness-cross-workspace-authority-remediation-2026-07-13.md`

### Runtime source

9. `erp_workspace_ui/boot.py`
10. `erp_workspace_ui/workspace_registry.py`
11. `erp_workspace_ui/workspace_governance_manifest.py`
12. `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
13. `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
14. `erp_workspace_ui/public/js/erp_workspace_ui_boot.js`
15. `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js`
16. `erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js`
17. `erp_workspace_ui/public/js/runtime/child_page/child_page_operating_actions.js`
18. `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`
19. `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
20. `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js`
21. `erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js`
22. `erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js`
23. `erp_workspace_ui/erp_workspace_ui/page/procurement_console_report/procurement_console_report.js`
24. `erp_workspace_ui/finance_accounting/service.py`
25. `erp_workspace_ui/sales_console/service.py`
26. `erp_workspace_ui/procurement_console/service.py`
27. `erp_workspace_ui/warehouse_console/service.py`

### Unit and contract tests

28. `erp_workspace_ui/tests/test_finance_accounting_payables_count.py`
29. `erp_workspace_ui/tests/test_finance_accounting_receivables_amount.py`
30. `erp_workspace_ui/tests/test_finance_accounting_receivables_count.py`
31. `erp_workspace_ui/tests/test_finance_accounting_resolver.py`
32. `erp_workspace_ui/tests/test_finance_accounting_shell.py`
33. `erp_workspace_ui/tests/test_procurement_console_phase0_contracts.py`
34. `erp_workspace_ui/tests/test_sales_console_service_contracts.py`
35. `erp_workspace_ui/tests/test_workspace_governance_manifest.py`
36. `erp_workspace_ui/tests/test_workspace_registry_contracts.py`

### Source smoke support

37. `ui_smoke/package.json`
38. `ui_smoke/run_playwright_docker.sh`
39. `ui_smoke/finance_cycle1_responsive_smoke.js`
40. `ui_smoke/finance_cycle1_source_smoke.js`

## Source/live runtime parity

All 19 scoped runtime paths intentionally differ from live. No mismatch is approved for alignment by this document.

| Runtime path | F6B8 source SHA-256 | Current live SHA-256 |
| --- | --- | --- |
| `erp_workspace_ui/boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` |
| `erp_workspace_ui/workspace_registry.py` | `efaafaa2c7a95bf0efe67d019328c1ff8cdc45e03faaab4233adcbb468375822` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `1196afd99234296e41671196bb357af546d1e04212dffbf0dc51bb8a78f144b6` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `814ff0b95f949a365bfb44abea090e33df28d8c79304943439108881ed749f0e` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` |
| `erp_workspace_ui/public/js/erp_workspace_ui_boot.js` | `443e7df4e6dc3953b306010990bf03d98845b98f41f38615bc97080e0de2e6dc` | `1620654e438e964641695a3f62dd277d6c6da65ae36cc8c463b09aefb9c6cb12` |
| `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js` | `95001b3ad95bdc53c0aaf78b05db3eb1089e7ef9814256ac9dbde36cca0e6f28` | `9d229c0aa31be067803041ab228620516493d659889f9cafc65ca720b73bed22` |
| `erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js` | `4e435ecf3c4367e4f15a2e2046b42ffe681eec068cbbfc28c4839e20a4de1c2b` | `1eae26a9a6d035361e4ea148044defb2dae4d91ad6e52ce110c90815377f1a39` |
| `erp_workspace_ui/public/js/runtime/child_page/child_page_operating_actions.js` | `1d591f4bca03f732e144b939fd0021ec0aad04b0e9a57aab9a48605e58054caa` | `20b32b803f8a6a46fad9e021c5fa992979cd843c420e2f4be06c0221e89bb627` |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `8b06e2c3b1de1feb3366421e92d7299e27ef2b978a7040ae77310ef0d171ac70` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `2ae91711eb99ac0e1cdc2767a76a1435324bd55d9ed6e77786e87ddb5a7f0cbf` | `71b5d4681d1d574e289ebc555d9bfbb9c964cc954db713e1367b54285d388b22` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js` | `11eed6ab3e96d6c62ef742a8e31506e361f93367edb0618836f07a008272cfee` | `07ded47d413f45721d5b8159d7e18c58123bd03d43bf84668825347928ee4002` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js` | `d983e06bce28900e4deeb330c4260d0d7066abdf0e26a068561a68284b3d14d6` | `be72eaadd7883a57dd815f53d30002a17394f5faf5c43d25ff11247642f4157a` |
| `erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js` | `2806077974dac131896f1a8cef1efd5e6bb188c60e36a40a8570950f18387407` | `e1823e4b7ebcdc77d3e0ac9dcdd03034d5fdf76b97389c4f330c0d7a6d9ec1eb` |
| `erp_workspace_ui/erp_workspace_ui/page/procurement_console_report/procurement_console_report.js` | `318e991c28313ffbafe726872876ab221194eb59feecaffbf27ac7340e23173d` | `8257f98d35922d12ca05be4cc04ef584ba7d09aafdce5128b1a1c218061e3464` |
| `erp_workspace_ui/finance_accounting/service.py` | `be494d19e387df121d666a2209967ccdebd69359e65fbb00ccde15b14e4108d2` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` |
| `erp_workspace_ui/sales_console/service.py` | `dc2b05dcb008723b95cc1054e0ecdf8da97b095c1af44368a40d7f25f156db27` | `638173cd6ce3bbb78fcbfa8351d523445e4a3917478790a5232e2b5b8f5856ad` |
| `erp_workspace_ui/procurement_console/service.py` | `d730588927c309700dfa20c784fec284fceb6f2252b0711a5fb8a4b39ce74abb` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` |
| `erp_workspace_ui/warehouse_console/service.py` | `ed715c17683cc8a48d23b06781ad32d1d93d0abc4cd656c22adc80f4a092ae9f` | `c1b2adfe89113d12f80f12bffa8a70f37e2d86dd14b3eefe17ace90348a72312` |

The exact future live-alignment allowlist is the 19 runtime paths in this table. A later gate must regenerate every hash from an approved source commit and stop on any difference.

Three live paths with carriage-return characters in their names and one empty source directory with a carriage-return suffix were observed outside this manifest. They are deployment/worktree artifacts, are not Finance/F6 candidate paths, and require a separately approved cleanup decision. F6B8 did not modify them.

## Explicit unrelated exclusions

These four dirty paths are excluded from every Finance/F6 candidate and future alignment list:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Validation state

- JavaScript syntax checks passed for every changed Finance, Sales, Procurement, shared runtime, registry, and Finance smoke file.
- Python compilation passed for `erp_workspace_ui`.
- 385 focused Finance, routing, registry, governance, Sales, and Procurement tests passed after the final F6B8 hardening; the full discovery below includes Warehouse regression coverage.
- 603 full unit-discovery tests passed.
- Finance lifecycle, managed search, Sales inquiry, Procurement Quick Find, target dispatch, landing priority, stale-helper re-evaluation, and exact-copy payload source smoke passed.
- Focused Python tests cover Payment Ledger anomaly detection, exact activity identity, malformed flags, and no-partial ledger-completeness failure.
- Representative Finance responsive Playwright smoke passed. It is source-layout evidence, not authenticated browser acceptance.
- Diff whitespace, documentation whitespace, and focused boundary scans passed. Allowed static hits are explicit boundary copy, governed legacy Sales target exceptions, test assertions, or module exports; no Finance native route, report, export, mutation, notification, raw SQL, `get_all`, `db.count`, or `ignore_permissions` path was introduced.
- Generated Python caches and temporary smoke dependencies were removed and verified absent after validation.
- Git classification contains exactly 40 Finance/F6 candidate paths plus the four excluded unrelated paths.
- A final independent read-only counterpart re-review remains required before the F6B8 decision.

## Boundaries

F6B8 adds no AP amounts, Payment Schedule aging or allocation, AR/AP rows, externally visible customer/supplier/invoice/voucher/account/Payment Ledger/GL identities, native Finance reports/routes/exports/download/print, payment or posting authority, mutation, notification, portal behavior, or external action.

## Next gate

F6B8 may proceed only to an independent counterpart review. F6C remains blocked until that review returns no Blocker or High finding. Authenticated browser verification and live behavior remain deferred to separately approved alignment and manual-review gates.
