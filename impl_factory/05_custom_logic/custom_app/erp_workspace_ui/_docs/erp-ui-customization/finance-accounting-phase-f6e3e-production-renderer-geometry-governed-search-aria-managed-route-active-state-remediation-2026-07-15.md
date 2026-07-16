# Finance & Accounting F6E3E: Production Renderer Geometry, Governed Search ARIA, And Managed Route Active-State Remediation

Date: 2026-07-15

Status: source-only implementation complete; independent F6E3D repeat counterpart review required before F6E4.

## Decision

The three confirmed F6E3D gaps are remediated in source. F6E3E does not approve live alignment, authenticated browser acceptance, F6F closure, staging, commit, push, or a protected gate.

## Production Renderer Geometry

The pinned Playwright smoke now invokes the registered `frappe.pages["finance-control-desk"].on_page_load` path instead of relying only on copied representative markup. It uses the real Finance renderer and shared-sidebar renderer at 1366px, 390px, and 320px for:

- manager-ready posture;
- non-Finance restricted posture;
- contract-valid controlled-unavailable company-scope posture;
- expanded and collapsed shared sidebar modes where the viewport contract permits them.

The assertions cover horizontal overflow, clipped focusable controls and copy, compact-versus-expanded copy, every rendered sidebar layout container, contained focus treatment for header, utilities, navigation, and collapse controls, sidebar/main and hero/sidebar separation, hero content and card overlap, visible enabled Refresh, persistent polite live status, and one aggregate request per registered render. The unmasked production geometry exposed a real 390px state-row overflow; the Finance layout now uses a zero-minimum narrow grid track and bounded/wrapping state content. Representative markup checks remain supplemental only.

## Governed Search ARIA

Direct focus on a governed result now updates the managed active index, leaves exactly one option with `aria-selected="true"`, and points the search input `aria-activedescendant` to that option. Clearing, query changes, route changes, workspace changes, and stale-generation invalidation use synchronous presentation reset, which removes selected state and `aria-activedescendant` before modal dismissal. Search progress and result status use a polite atomic status region. The managed dialog contains Tab focus and restores its opener after ordinary dismissal; governed dispatch and route departure suppress obsolete focus restoration.

Mouse, keyboard, governed dispatch, workspace/route/query/token isolation, native-target rejection, and contained 3px focus presentation remain unchanged.

## Managed Route Active State

The shared sidebar now resolves every Procurement and Warehouse detail, review, and managed-form route present in the browser registry and governance manifest to one existing fallback item:

| Workspace | Managed route | Current item |
| --- | --- | --- |
| Procurement | `procurement-console-po-follow-up` | Purchase Orders |
| Procurement | `procurement-console-supplier` | Suppliers |
| Procurement | `procurement-console-item` | Buying Items |
| Procurement | `procurement-console-purchase-request-review` | Purchase Requests |
| Procurement | `procurement-console-purchase-request-form` | Purchase Requests |
| Procurement | `procurement-console-rfq-form` | RFQs |
| Procurement | `procurement-console-rfq-review` | RFQs |
| Procurement | `procurement-console-supplier-quotation-form` | Supplier Quotations |
| Procurement | `procurement-console-supplier-quotation-review` | Supplier Quotations |
| Procurement | `procurement-console-purchase-order-form` | Purchase Orders |
| Warehouse | `warehouse-console-receiving` | Inbound Receiving |
| Warehouse | `warehouse-console-picking` | Outbound Picking |
| Warehouse | `warehouse-console-stock-exception` | Stock Exceptions |
| Warehouse | `warehouse-console-stock-posture` | Stock Exceptions |
| Warehouse | `warehouse-console-movement` | Movement Visibility |

The actual renderer test compares the complete governance-manifest route set with an independently enumerated browser-registry route set and asserts exactly one `aria-current="page"` item for every route emitted by the current registry-derived producers. The shared payload validator rejects duplicate item keys within or across sections and rejects unregistered item keys. Exact registered item-tuple binding and mandatory active-key inclusion remain deferred shared-contract hardening; the current producer fixtures are complete and are tested exhaustively rather than through one convenient fallback route.

## Validation Evidence

- JavaScript syntax checks passed for Finance, shared sidebar, registry, and both Finance smoke files.
- Finance Cycle 1 source lifecycle smoke passed.
- Pinned Docker Playwright production-runtime responsive smoke passed at 1366px, 390px, and 320px without root overflow masking.
- Focused Finance tests passed: 184.
- Focused Sales tests passed: 36.
- Focused Procurement, Warehouse, registry, and governance tests passed: 393.
- Full unit discovery passed: 613.

## Source And Live Truth

`finance_accounting/service.py` remains aligned and was not changed:

- source/live SHA-256: `e5870574d11e4d5d1754814f5f5faf90df645ce47c16ebee73e2e7505023af9e`

The only intended runtime source/live differences remain:

| Future runtime-only alignment path | Source SHA-256 | Current live SHA-256 |
| --- | --- | --- |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `d66cdae042761d1f2fcbc856c3521701a0757317dbeb3e4fa084203842bce2e5` | `8b06e2c3b1de1feb3366421e92d7299e27ef2b978a7040ae77310ef0d171ac70` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `c8bbd2b7690c6c126d626556ba09892ebc92698420d35b49fc946caefc9ac674` | `814ff0b95f949a365bfb44abea090e33df28d8c79304943439108881ed749f0e` |

Docs, tests, and smoke files are source-package evidence and are not part of a future runtime-only F6E4 alignment unless separately approved.

## Boundaries

F6E3E changes no Finance service, backend query, accounting semantic, AR/AP policy, role, permission, company scope, payload contract, Page metadata, or landing priority. It adds no rows, identities, amounts, native reports, routes, exports, notifications, execution, or external actions.

The four unrelated paths remain excluded:

- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `ui_smoke/sales_final_acceptance_audit.js`
- `a.out`

## Next Gate

Repeat the independent F6E3D counterpart review against this frozen source package. F6E4 and F6F remain blocked until that review accepts the package and Owner/Main Control separately approves controlled live alignment.
