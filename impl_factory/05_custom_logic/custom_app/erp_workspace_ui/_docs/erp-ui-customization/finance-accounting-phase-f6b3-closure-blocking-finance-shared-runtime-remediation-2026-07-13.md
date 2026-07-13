# Finance & Accounting F6B3 - Closure-Blocking Finance and Shared Runtime Remediation

Date: 2026-07-13

Status: source remediation complete; F6B4 independent counterpart review required. This document does not approve live alignment, restart, cache clear, metadata reload, migration, permission changes, staging, commit, push, protected gates, or Finance Cycle 1 closure.

## Implemented remediation

### Finance initialization and lifecycle

- Normal page initialization uses the actual Frappe page wrapper and resolves `.layout-main-section` only as its render target.
- The supported wrapper `hide.financeControlDesk` event invalidates the target request coordinator and cached payload.
- Request tokens make late ready and late error responses non-authoritative after route departure or a newer forced load. Returning to Finance issues a fresh request.
- Equivalent initial loads deduplicate. A bounded 30-second request timeout, Frappe callback and transport-failure settlement, and a single-settlement guard ensure a request cannot leave the page permanently loading or let a late callback replace current state.
- Controlled errors render a business-facing unavailable state; internal transport or policy reasons are never shown to normal users.

`ui_smoke/finance_cycle1_source_smoke.js` is a source-behavioral Node smoke. It proves exported lifecycle/coordinator behavior using representative browser globals, but it is not authenticated live Frappe browser evidence.

### Resolver permission and bounds

- Finance company scope no longer uses `frappe.db.count` or any permission-bypassing site cardinality call.
- Permission-visible Company and User Permission reads use `frappe.get_list`, deterministic ordering, explicit start offsets, and cap-plus-one sentinels.
- Company scope allows the current fallback only when the permission-preserving Company read proves exactly one visible company with the exact required Company record shape. Aliases, extra fields, ambiguity, malformed data, over-cap results, or denied reads fail controlled unavailable.
- `Company.disabled` is neither selected nor normalized.
- Managed System User inventory is deterministic and bounded; malformed, duplicate, denied, and over-cap results return no batch candidates. Existing Sales, Procurement, Warehouse, and Finance landing priorities are unchanged.

### Shared sidebar contract

- Sales bootstrap/sidebar, Procurement, Warehouse, and Finance now emit `workspace-sidebar.v1` at both top-level and nested sidebar context.
- Top-level and nested workspace identities must be exact non-padded strings and agree with the active registered workspace before cache or render.
- Every top-level and section sidebar item target must exactly match that workspace's registered page/worklist fallback target. Generic new-document, form, list, report, native-route, export, or execution targets are rejected.
- Shared sidebar state is workspace-keyed. Managed refresh clears only the active workspace key; route signatures and synchronous unmanaged-route cleanup prevent late responses from overwriting another workspace.
- A late Sales bootstrap primes and synchronizes only when its workspace identity matches the current route. It cannot clear Finance or another workspace after navigation.
- Native header `href` and drop-icon `aria-hidden`/`tabindex` values are captured and restored, including originally absent attributes.

### Payload, numeric, and accounting truth

- Raw Finance payloads are recursively rejected before normalization, caching, or rendering when they contain unknown schema fields, invalid scalar types, incomplete no-effect flags, identity aliases, plural native surfaces, acronym-led aliases such as `GL2Rows`/`APBalance`, monetary aliases outside the approved AR amount contract, or execution fields.
- Company scope, period, scope, AR, AP, policy, and no-effect sections use exact typed contracts. All populated AR/AP postures must share one validated `as_of_date`.
- Payment Ledger source amounts use strict finite Decimal parsing. The unused lenient zero-coercion helper was removed. Fixed-scale decimal strings remain the only browser authority.
- The page displays business-facing `As of` and `Refreshed` context. Internal unavailable reason codes remain hidden.
- User-facing and governance copy describes Cycle 1 truth: Accounts Manager-only aggregate AR count/MMK amount posture and AP count posture when all gates pass; no financial rows, native reports/routes/exports, or execution.

## Cross-workspace regression status
- Cycle 1 policy flags are validated against required truth values, not only names and scalar types. Contradictory payment-schedule, Accounts User, navigation, output, or execution claims are rejected.
- As-of dates and fetched timestamps require valid calendar/time values; impossible dates and trailing timestamp text are rejected.

- Sales: existing route priority and registered page/worklist navigation are unchanged; bootstrap and sidebar payloads now supply the shared version and nested identity, and delayed bootstrap completion cannot invalidate another workspace.
- Procurement: existing route priority and registered page/worklist navigation are unchanged; the producer now supplies the shared sidebar version.
- Warehouse: roadmap status remains `w8c_transfer_visibility` in Python and browser registries; the producer now supplies the shared sidebar version.
- Finance: direct route, boot-only Accounts Manager/Accounts User landing, manager/user role boundaries, aggregate-only posture, and no-execution boundaries remain unchanged.

## Validation evidence

- Python compilation passed.
- Focused Finance tests passed: 143 tests.
- Focused routing/registry/governance tests passed: 207 tests.
- Full unit discovery passed: 570 tests.
- Finance source lifecycle smoke passed.
- Representative Finance responsive smoke passed at 1366px and 390px in the existing isolated Playwright Docker runner.
- The responsive smoke renders actual Finance page CSS but representative manager/restricted markup. It is not an authenticated live route or permission test.
- F6B3 has not changed live state. Authenticated live verification remains a separately approved future step after F6B4 acceptance.

## Exact future live-alignment allowlist and hashes

Every mismatch below is expected because F6B/F6B1/F6B3 remain source-only. No other runtime mismatch is part of the F6B3 live candidate.

| Runtime file | F6B3 source SHA-256 | Current live SHA-256 | Reason |
| --- | --- | --- | --- |
| `erp_workspace_ui/boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` | Bounded deterministic managed-user inventory; boot-only Finance landing remains non-persistent. |
| `erp_workspace_ui/workspace_registry.py` | `34b5f0a04100ec3bcde89c8bb6907ae4458370d5f4eb6e3de28bd149c31cdfa7` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` | Shared sidebar schema constant and Cycle 1/Warehouse registry truth. |
| `erp_workspace_ui/workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` | Cycle 1 overview/navigation and blocked-surface truth. |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d5f26d96129beeca118846a19eb4a0939c2f8536a6d84089b09330a20a7d1b52` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` | Browser registry parity and registered sidebar target allowlists. |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `2da00c49ced2525f627ccd5ec9a9db286d9f973621a7735ddf0f6f15e35e269b` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` | Version/identity validation, exact top-level/section targets, workspace-keyed races, valid fallbacks, native cleanup. |
| `erp_workspace_ui/finance_accounting/service.py` | `38d6c1fae74d25d0683fdf4f22c7f74375efb4a20886bf1007abd2f4de11b9f7` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` | Bounded company resolver, AR semantics/Decimal contract, exact overview/sidebar payloads, business-facing scope copy. |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `1cab912c073cdb27d137388813ce8456939f0b154d664de3573ef791e849a314` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` | Normal initialization, bounded request settlement, outer-wrapper lifecycle, exact policy/date/payload validation, as-of/freshness UI. |
| `erp_workspace_ui/sales_console/service.py` | `ebf6950f8d3ffbaafd98026e8aca9180a015a0c908ea204c4a80df99b768e8c7` | `638173cd6ce3bbb78fcbfa8351d523445e4a3917478790a5232e2b5b8f5856ad` | Shared versioned Sales bootstrap and sidebar producer contract. |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `aa25c291b6ced3d7a7ff44175de20bb340d5ad50e0e9b81a41d9074539860f2b` | `71b5d4681d1d574e289ebc555d9bfbb9c964cc954db713e1367b54285d388b22` | Validates Sales bootstrap priming before synchronization so delayed Sales completion cannot invalidate another workspace. |
| `erp_workspace_ui/procurement_console/service.py` | `a2f92e1d76075b8e6783a7d9ec129f1a4b295d605d11b46038753c5631646af1` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` | Shared versioned Procurement sidebar producer contract. |
| `erp_workspace_ui/warehouse_console/service.py` | `ed715c17683cc8a48d23b06781ad32d1d93d0abc4cd656c22adc80f4a092ae9f` | `c1b2adfe89113d12f80f12bffa8a70f37e2d86dd14b3eefe17ace90348a72312` | Shared versioned Warehouse sidebar producer contract. |

`finance_control_desk.json` remains unchanged and is not a live-alignment candidate.

## Explicit unrelated exclusions

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Cache classification

Python bytecode under touched `erp_workspace_ui` package paths is generated validation output and must be removed before handoff. Repository `node_modules`, Playwright browser caches, and unrelated environment caches are dependency/runtime state and are not modified or classified as Finance source.

## Boundaries and next gate

Payment-schedule aging/allocation, AP amounts, AR/AP rows or identities, native Finance reports/routes/exports/download/print/actions, accounting execution, role/permission/DocType changes, and external actions remain blocked.

F6B3 may proceed only to F6B4 independent counterpart review. F6C remains blocked until F6B4 accepts the source package and any later live alignment/manual verification receives separate Owner/Main Control approval.
