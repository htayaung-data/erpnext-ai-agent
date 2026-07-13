# Finance & Accounting F6B - Cycle 1 Grouped Source Remediation

Date: 2026-07-11

Status: source remediation complete; counterpart review required. This document does not approve live alignment, Finance Cycle 1 closure, protected gates, staging, commit, or push.
## Supersession note

F6B2 did not accept this package for closure. F6B3 on 2026-07-13 supersedes its current readiness and source/live hash claims while preserving this document as historical evidence. See `finance-accounting-phase-f6b3-closure-blocking-finance-shared-runtime-remediation-2026-07-13.md`.


## Remediation outcome

- AR count and amount posture now fail closed together before amount reads when an eligible Sales Invoice uses a payment-terms template or any Payment Schedule child row. The child probe is permission-preserving, selected-company scoped, positive-outstanding scoped, and constrained to `Sales Invoice.payment_schedule` parents.
- A separate permission-preserving Payment Ledger aggregate probe detects activity after the shared `as_of_date`. Any future activity or uncertain probe result disables AR count and amount posture. The bounded Payment Ledger row adapter retains `posting_date <= as_of_date` and never loads future identities.
- AR count and amount sources remain distinct and named: Sales Invoice supplies count buckets; Payment Ledger Entry supplies manager-only company-currency amount buckets.
- MMK amounts use ERPNext's authoritative global `get_currency_precision()` contract and approved rounding method. Decimal values remain authoritative in Python and cross the browser contract as fixed-scale strings; the browser does not recalculate them.
- Finance page requests use a page-instance token. Equivalent in-flight loads deduplicate, and F6B1 binds invalidation to Frappe 16.5.0's wrapper `hide` event so stale success or error responses cannot render or enter the cache. The visible Refresh control remains disabled during its active request.
- Shared sidebar context is keyed by workspace. Payload workspace identity is checked before caching, and late responses are ignored unless both workspace and route signature still match.
- The browser validates the complete raw Finance payload before normalization or caching. Unknown keys, incomplete no-effect contracts, identities, monetary aliases outside the approved AR amount section, native surfaces, and execution flags block rendering.
- Registry and governance labels now describe Cycle 1 truth: manager-only aggregate AR counts/MMK amounts and manager-only AP counts when semantic gates pass; no rows, native reports/routes/exports, or execution.
- `ui_smoke/finance_cycle1_source_smoke.js` behaviorally covers reversed responses, wrapper-hide invalidation, return after departure, cache clearing, cross-workspace sidebar isolation, and payload-validation ordering. `finance_cycle1_responsive_smoke.js` uses existing Playwright tooling for desktop and narrow-screen overflow checks.

## Accounting boundaries

Payment-schedule aging and installment allocation remain unsupported. Any detected schedule returns controlled unavailable. AP amounts, customer/supplier/invoice/voucher/account/Payment Ledger/GL rows or identities, native reports/routes/exports/download/print, and every accounting or external action remain blocked.

## Review integration

Accepted:

- Accounting review recommendation to fail closed on any schedule, use a separate future-activity aggregate probe, restore the approved Payment Ledger as-of row filter, and serialize decimal-safe fixed-scale values.
- Security review recommendation for an exact versioned browser schema, complete no-effect validation, unknown-key rejection, and validation before caching.
- Frontend review recommendation for page request tokens, in-flight deduplication, refresh supersession, workspace-keyed sidebar state, and active-route checks.
- Release review recommendation for truthful Cycle 1 labels, preserved landing priorities, exact source/live hashes, and a narrow future live allowlist.

Rejected:

- Reading future Payment Ledger rows into the bounded row adapter. Future activity is detected only through an aggregate count gate.
- Overwriting Sales Invoice permission provenance when suppressing count posture. Count posture now owns and reports its future-activity permission gate directly.
- Treating Finance Cycle 1 as closed before counterpart review and later approved live alignment/manual verification.

Deferred:

- Payment-schedule aging, AP amounts, row drilldowns, GL, Cash/Bank, Tax/Close, cross-workspace accounting, execution, live alignment, protected gates, staging, commit, and push.

## Future live-alignment allowlist

No live change occurred in F6B/F6B1. A future separately approved alignment must use only these runtime files and verify the recorded current source hash at the time of approval:

| Runtime file | Current F6B1 source SHA-256 | Current live SHA-256 | Reason for expected difference |
| --- | --- | --- | --- |
| `erp_workspace_ui/boot.py` | `0640d03a7621d749ef214912cb8481fe7d8943c3aed7ccd34e395ee4cd7c7584` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` | Source preserves Finance boot-only landing without persistent user-default writes; live is stale. |
| `erp_workspace_ui/workspace_registry.py` | `936d24b05dff90f9f3aa4cde8cdc9a7ca7c8905e535ca1232a6f29de08ffbbc9` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` | Cycle 1 status, mode, Overview label, and search truth. |
| `erp_workspace_ui/workspace_governance_manifest.py` | `4e93e4e25572851d185f9ce7f893767d325fc528634de9305cac02083be60d7c` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` | Cycle 1 route, smoke, refresh, and forbidden-action truth. |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d5f26d96129beeca118846a19eb4a0939c2f8536a6d84089b09330a20a7d1b52` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` | Browser registry parity with Python registry. |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `7865148206a312709bda24d822bd4a0443a2ea836affebacbc54144474ece9aa` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` | Workspace-keyed request/cache state and route-stale response guard. |
| `erp_workspace_ui/finance_accounting/service.py` | `68bbff90135c933a72bdfa88981057a1e1a2ace8bd1fe8f28dd2e0a90ddd2849` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` | AR schedule/as-of/future-activity/precision contract and exact overview schema. |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `482dca93f6947b36f9df45a2c74d5cfbe100fbb305bb24e67a4dab232b3d6a25` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` | Exact raw payload contract and stale-response protection. |

`finance_control_desk.json` already matches source and live at `fb0e0964cf9883e6224090f1e1efcd27c96798f585bc8afcbeb8dff5e4eaf765`; it is not a future copy candidate unless later metadata changes are separately approved.

## Explicit unrelated exclusions

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Release boundary

Tests, docs, and the source smoke belong in a future source staging package, not the live runtime copy. The four unrelated dirty paths remain excluded. F6B proceeds only to independent counterpart review; F6C remains blocked until that review accepts this source package.
