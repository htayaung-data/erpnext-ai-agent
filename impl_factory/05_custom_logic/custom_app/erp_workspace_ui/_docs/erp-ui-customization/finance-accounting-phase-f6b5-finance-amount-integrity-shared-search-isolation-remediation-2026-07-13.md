# Finance & Accounting F6B5 - Amount Integrity and Shared Search Isolation Remediation

Date: 2026-07-13
Status: historical source-only remediation; superseded by F6B6 after counterpart findings

## Decision context

F6B4 found two closure-blocking paths: a positive company-currency receivable could be omitted when the corresponding account-currency balance was non-positive, and delayed managed-workspace search results could reach the generic target dispatcher without a workspace-specific target contract. F6B5 corrects those paths without changing Finance roles, permissions, accounting authority, runtime data scope, or live state.

F6C remains blocked. This document does not approve staging, commit, push, live alignment, restart, cache clearing, metadata reload, migration, protected gates, or Finance Cycle 1 closure.

The completed F6B5 counterpart review returned `remediation_required`: bucket-count equality did not prove identical voucher populations, same-route query changes did not invalidate authority until request start, and date validation still accepted padded strings and datetime objects. F6B6 is the current remediation and traceability authority. The hashes below remain the historical F6B5 snapshot.

## Implemented source remediation

### AR company-currency integrity

- Payment Ledger voucher aggregation now compares company-currency and account-currency positive-balance state before any voucher is included or excluded.
- A positive/non-positive disagreement in either direction invalidates the entire manager amount posture.
- Invalid source returns no bucket counts, bucket amounts, suppressed buckets, grand total, company scope, source rows, voucher identities, or ready runtime flag.
- Vouchers whose company and account balances are both non-positive remain excluded; positive balances in both currencies remain eligible.
- Decimal parsing, fixed-scale MMK serialization, source pagination, row cap, company assertion, population suppression, due-date policy, and split-account fail-closed behavior remain unchanged.
- Before overview publication, ready Sales Invoice count buckets must exactly match ready Payment Ledger voucher-count buckets. A mismatch preserves count-only visibility but suppresses the entire amount posture with no partial values or difference details.

### Managed search governance and request isolation

- Search responses are wrapped in `workspace-search.v1` envelopes containing workspace identity, exact route identity, and request token.
- Raw result shape and every target are validated before normalized result storage; the target is validated again immediately before dispatch.
- Sales and Procurement search may dispatch only approved worklist queue targets with one bounded keyword filter.
- Warehouse search may dispatch only registered custom `warehouse-console*` page targets with bounded route parts or context tokens.
- Native new-document, form, list, report, export, print, arbitrary page, unknown queue, padded value, route escape, and execution-shaped targets are rejected.
- Every route change invalidates the current search token, stored results, envelope, active index, timer, and dialog. Delayed Sales search cannot render or dispatch after Finance, Procurement, Warehouse, or native navigation.
- Sales customer, item, quotation, and order results use only explicitly approved custom worklist targets with bounded keyword filters; native Sales form targets are not permitted.
- Warehouse uses an exact route-to-payload matrix for receiving, picking, stock-exception, stock-posture, and movement review targets. Generic Warehouse worklists, home routes, unknown routes, and mismatched route-part/context-token shapes are rejected.
- Stored target filters and route parts are copied and frozen; dispatch still revalidates the complete target.

### Sales delayed Guideline isolation

- The delayed Guideline insertion uses a route-bound generation and is cancelled through the supported outer Frappe wrapper `hide` event.
- Route departure removes the guide and invalidates the timer. A stale generation cannot cancel or mutate a newer generation after rapid return.
- The active Sales route retains the approved Guideline behavior.
- Cached Sales return starts a fresh Guideline generation. The same wrapper-hide invalidation also makes a late Sales bootstrap, delayed hydration, sidebar prime, DOM write, or global error alert non-authoritative after route departure.

### Business-facing copy and dates

- Finance validates every rendered workspace, state, overview, scope, lane title, lane detail, and lane value against snake_case, camelCase, and acronym-led technical patterns before normalization, caching, or rendering.
- Unsafe copy maps to a controlled generic unavailable panel whose workspace and text are hardcoded business copy. Raw backend reason metadata remains non-rendered.
- Financial date helpers accept date objects or exact `YYYY-MM-DD` calendar strings only. Prefixes, timestamps, trailing text, invalid calendar dates, and malformed source dates fail closed.
- Bytes, numeric values, and arbitrary string-convertible objects are rejected as financial dates.

## Source/live parity and future allowlist

All 11 mismatches are intentional. They combine prior F6B/F6B1/F6B3 source-only work with F6B5. No file was copied to live.

| Runtime file | F6B5 source SHA-256 | Current live SHA-256 | F6B5 relevance |
| --- | --- | --- | --- |
| `erp_workspace_ui/boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` | Prior bounded, non-persistent managed landing candidate. |
| `erp_workspace_ui/workspace_registry.py` | `34b5f0a04100ec3bcde89c8bb6907ae4458370d5f4eb6e3de28bd149c31cdfa7` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` | Prior versioned shared workspace definition. |
| `erp_workspace_ui/workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` | Prior Cycle 1 boundary truth. |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d5f26d96129beeca118846a19eb4a0939c2f8536a6d84089b09330a20a7d1b52` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` | Registered target and route allowlist authority. |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `f3fbb75c48f88a476eb6a39c019efac6ee0596960fb9175937e8434a4af2aaa8` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` | F6B5 versioned search envelope, exact target validation, and route invalidation. |
| `erp_workspace_ui/finance_accounting/service.py` | `bb7c41274aa515ab635eceeb5c6b9d2add39ec3c4625164b9b88f095fcd0d319` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` | F6B5 sign integrity, count/amount reconciliation, and strict financial dates. |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `44d095695d298694f93e9608504303f934a649c60308291b5b5f028d4ee13fd8` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` | F6B5 business-copy catalogue and contract rejection. |
| `erp_workspace_ui/sales_console/service.py` | `dc2b05dcb008723b95cc1054e0ecdf8da97b095c1af44368a40d7f25f156db27` | `638173cd6ce3bbb78fcbfa8351d523445e4a3917478790a5232e2b5b8f5856ad` | Versioned Sales producer with governed worklist search targets. |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `4fec5c4669629cc410161babd4cf3be666fbf1e50f64dfb67c2f22ce95c08b7c` | `71b5d4681d1d574e289ebc555d9bfbb9c964cc954db713e1367b54285d388b22` | F6B5 route-bound Guideline, cached recovery, and bootstrap authority. |
| `erp_workspace_ui/procurement_console/service.py` | `d730588927c309700dfa20c784fec284fceb6f2252b0711a5fb8a4b39ce74abb` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` | Versioned Procurement producer with bounded worklist keywords. |
| `erp_workspace_ui/warehouse_console/service.py` | `ed715c17683cc8a48d23b06781ad32d1d93d0abc4cd656c22adc80f4a092ae9f` | `c1b2adfe89113d12f80f12bffa8a70f37e2d86dd14b3eefe17ace90348a72312` | Prior versioned Warehouse producer contract. |

The exact future live-alignment allowlist is the 11 runtime paths in this table. `finance_control_desk.json` is unchanged and excluded. Alignment, restart, cache clear, and authenticated browser review require separate Owner/Main Control approval after counterpart acceptance.

## Explicit exclusions

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Validation and next gate

The validation contract covers exact sign-disagreement fail-closed responses, strict date rejection, technical-copy rejection, safe Finance rendering, managed-search target allowlists, delayed-response route isolation, stale-token rejection, Sales timer departure and rapid return, focused workspace regressions, full unit discovery, static boundary scans, cache cleanup, and the source/live hash comparison above.

Final source evidence: 149 focused Finance tests, 219 routing/registry/governance and Sales/Procurement tests, 184 Warehouse regression tests, and 576 full tests passed. The behavioral Finance/search/Sales lifecycle source smoke and representative Finance responsive smoke also passed. The responsive smoke is isolated source evidence, not authenticated live evidence.

F6B5 did not pass its repeat counterpart review. F6B6 supersedes this next-gate statement; F6C remains blocked until the F6B6 counterpart review confirms no Blocker or High finding.
