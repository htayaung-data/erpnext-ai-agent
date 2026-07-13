# Finance & Accounting F6B6 - AR Voucher-Set Integrity and Search Generation Remediation

Date: 2026-07-13
Status: source-only remediation; final independent counterpart review required

Historical note: the 11-file source/live table below is point-in-time F6B6 evidence. F6B8 supersedes the current readiness and parity count with a 19-file source-only runtime allowlist. This document does not approve F6C or external-state action.

## Decision context

The F6B5 counterpart review rejected bucket cardinality as proof that Sales Invoice count posture and Payment Ledger amount posture describe the same receivable population. It also found that a same-route search response could remain authoritative during the debounce interval after the user changed the query, and that financial date helpers accepted padded strings and datetime values.

F6B6 addresses those findings only. F6C remains blocked. No source file was copied to live and no staging, commit, push, restart, cache clear, metadata reload, migration, permission change, protected gate, or accounting execution occurred.

## Deployed Payment Ledger relationship proof

The installed ERPNext 16.4.1 receivables implementation was inspected read-only:

- `erpnext/accounts/report/accounts_receivable/accounts_receivable.py:184-251` keys voucher balances by account, voucher type, voucher number, and party, then applies activity through account, against-voucher type, against-voucher number, and party.
- `accounts_receivable.py:300-323` classifies Payment Entry and Journal Entry activity against the correlated voucher.
- `accounts_receivable.py:909-942` selects Payment Ledger name, account, voucher and against-voucher fields, party, posting/due dates, currencies, and amounts.
- `erpnext/accounts/doctype/payment_ledger_entry/test_payment_ledger_entry.py:209-440` verifies Sales Invoice correlation through `against_voucher_type` and `against_voucher_no`; lines 290-350 prove credit notes post ledger entries against themselves.

F6B6 therefore does not use invoice number alone. Its internal correlation identity is receivable account, `Sales Invoice`, invoice name, `Customer`, and customer. Unknown or uncorrelatable ledger activity fails the whole amount posture closed.

## Implemented source remediation

### Exact voucher-set reconciliation

- A bounded, permission-preserving Sales Invoice identity reader uses the existing selected-company, submitted, positive-outstanding, non-return, no-return-link, and as-of filters.
- Reads are ordered by unique invoice name, paged at 500 rows, capped at 5,000 rows, and reject permission errors, malformed rows, duplicates, cap overflow, wrong company, future posting, missing/invalid due date, return state, or invalid parent fields.
- Payment Ledger reads now include the unique ledger row name so duplicate source rows fail closed.
- Every company, account, party, invoice, voucher, and ledger identity component must be an exact, unpadded, non-empty string; scalar coercion and trimmed aliases fail closed.
- Payment Ledger rows must correlate through `against_voucher_type = Sales Invoice`; only Sales Invoice, Payment Entry, and Journal Entry voucher activity is understood. Standalone advances and unknown voucher types are unavailable.
- A bounded selected-company Sales Invoice return aggregate gate runs before identity reconciliation. Any submitted return or credit note on or before the as-of date makes the amount posture unavailable because this adapter deliberately does not reproduce ERPNext's separate return-to-original remapping.
- Each company-currency and account-currency voucher outstanding is rounded with the verified deployed currency precision before sign eligibility, identity inclusion, and bucket aggregation, matching ERPNext's voucher-level rounding order.
- Positive outstanding Payment Ledger vouchers carry an internal composite identity only until exact per-aging-bucket set comparison completes.
- Every Sales Invoice bucket set must equal the corresponding Payment Ledger bucket set. Missing, extra, ambiguous, duplicated, cross-company, or differently bucketed identities suppress the entire amount posture.
- Internal identities are never returned, logged, cached, rendered, linked, exported, or included in unavailable copy.
- Existing count-only posture can remain available when amount reconciliation fails, but the amount response contains no bucket counts, amounts, suppressed buckets, total, selected company, reconciliation-ready marker, or ready flag.
- Payment Schedule gates, future activity gates, selected-company assertions, Decimal parsing, deployed currency precision, low-population suppression, and bounded source reads remain in force.

### Search input generations

- Managed search now normalizes the query once and binds workspace, exact route, request token, and normalized query into `workspace-search.v1`.
- Every input event begins a new generation before debounce. This immediately clears result and dispatch authority for the prior query.
- A late response must match all four identities before storage, rendering, or dispatch.
- Rapid A to B to C input, route departure during debounce, stale same-route responses, and stale dispatch all fail authority checks.
- A whitespace-equivalent query is normalized to the same backend query, but the input event still receives a new token so prior work cannot become authoritative.
- Existing workspace target allowlists and native target rejection remain unchanged.

### Strict financial dates

- A supplied as-of value is accepted only when it is a true `date` object or a non-empty exact `YYYY-MM-DD` string.
- Datetime objects, including timezone-aware values, padded strings, prefixes, timestamps, malformed dates, and unsupported types fail closed.
- Only an absent optional as-of value uses the existing server-date policy.
- AR count, AR amount, and AP count paths share this rule; an invalid supplied value cannot silently become today.

## Transaction consistency assumption

Cycle 1 continues to rely on the deployed MariaDB `REPEATABLE-READ` isolation and Frappe's single request transaction for the count, return-activity aggregate, identity, and amount reads. Deterministic ordering, caps, selected-company assertions, and exact set reconciliation fail closed on observable inconsistency. F6B6 does not introduce an explicit accounting snapshot or lock. That remains an accepted deployment-specific assumption for source review and must be rechecked if database isolation or request transaction behavior changes.

## Source/live parity and future allowlist

Exactly 11 scoped runtime files differ from live. Eight differences are inherited F6 source-only work; Finance service, Finance page contract validation, and shared sidebar hashes changed again in F6B6. No unexpected scoped mismatch was found.

| Runtime file | F6B6 source SHA-256 | Current live SHA-256 |
| --- | --- | --- |
| `erp_workspace_ui/boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` |
| `erp_workspace_ui/workspace_registry.py` | `34b5f0a04100ec3bcde89c8bb6907ae4458370d5f4eb6e3de28bd149c31cdfa7` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d5f26d96129beeca118846a19eb4a0939c2f8536a6d84089b09330a20a7d1b52` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `e6dea620ea13bb3fffdca37ecaa808dc3baced21799947b57907b3a1f2a990e5` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` |
| `erp_workspace_ui/finance_accounting/service.py` | `2a30de48f4e2909217c44c1e966ba7cc9508888986af85ce25e330ea1f8ba752` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `69bc474ab0c84b2611a541f8e4055104f389ea3fa80da52a8f4f05e388cb6687` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` |
| `erp_workspace_ui/sales_console/service.py` | `dc2b05dcb008723b95cc1054e0ecdf8da97b095c1af44368a40d7f25f156db27` | `638173cd6ce3bbb78fcbfa8351d523445e4a3917478790a5232e2b5b8f5856ad` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `4fec5c4669629cc410161babd4cf3be666fbf1e50f64dfb67c2f22ce95c08b7c` | `71b5d4681d1d574e289ebc555d9bfbb9c964cc954db713e1367b54285d388b22` |
| `erp_workspace_ui/procurement_console/service.py` | `d730588927c309700dfa20c784fec284fceb6f2252b0711a5fb8a4b39ce74abb` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` |
| `erp_workspace_ui/warehouse_console/service.py` | `ed715c17683cc8a48d23b06781ad32d1d93d0abc4cd656c22adc80f4a092ae9f` | `c1b2adfe89113d12f80f12bffa8a70f37e2d86dd14b3eefe17ace90348a72312` |

The exact future live-alignment allowlist is the 11 runtime paths above. Alignment is not approved by F6B6. Authenticated browser verification of search generations, role views, and Finance unavailable/ready states remains deferred until a separate live-alignment gate.

## Explicit unrelated exclusions

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

These paths are not Finance changes and remain outside all staging and future live-alignment candidates.

## Validation evidence

- 165 focused Finance tests passed.
- 219 routing, registry, governance, Sales, and Procurement contract tests passed.
- 184 Warehouse regression tests passed.
- 592 full unit-discovery tests passed.
- Finance/search/Sales lifecycle source smoke passed.
- Representative Finance responsive smoke passed in the repository's pinned Playwright container.
- Python compilation, JavaScript syntax checks, diff whitespace checks, documentation whitespace checks, generated-cache cleanup, and focused static boundary scans passed.
- Responsive source smoke is representative evidence only. Authenticated live browser acceptance remains deferred.

## Remaining boundaries

F6B6 adds no AP amounts, payment-schedule aging or allocation, customer/supplier/invoice/voucher/account/Payment Ledger/GL rows, browser-visible identities, native reports/routes/exports/download/print, payment or posting authority, mutations, notifications, portal behavior, or external actions.

## Next gate

F6B6 may proceed only to a final independent counterpart review after validation. F6C remains blocked until that review confirms no Blocker or High finding. Source evidence and representative smoke do not substitute for later authenticated browser verification.
