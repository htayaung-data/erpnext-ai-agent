# Finance & Accounting F6B1 - Closure-Blocking Correctness Remediation

Date: 2026-07-11

Status: source remediation complete; independent F6B2 counterpart review required. This document does not approve staging, commit, push, live alignment, restart, metadata reload, protected gates, or Finance Cycle 1 closure.
## Supersession note

F6B2 did not accept this package for closure. F6B3 on 2026-07-13 supersedes its current readiness and source/live hash claims while preserving this document as historical evidence. See `finance-accounting-phase-f6b3-closure-blocking-finance-shared-runtime-remediation-2026-07-13.md`.


## Correctness outcome

- AR aging now uses two schedule gates before count buckets: the permission-preserving parent aggregate catches valid schedules, and a bounded integrity read checks only permission-visible, selected-company candidate invoice relationships.
- Candidate invoice identities and Payment Schedule relationship fields are internal gate inputs only. They are bounded, never returned, and any malformed candidate-linked, cross-scope, over-cap, or uncertain result returns controlled unavailable. Globally orphaned child rows cannot be attributed to the selected company safely and are excluded from this request path; their audit is deferred to a separately privileged integrity phase.
- AR amount readiness now requires AR count readiness in the raw browser contract. Contradictory amount-ready/count-unavailable payloads are rejected before cache or rendering, and the obsolete amount-only server card branch is removed.
- Payment Ledger values reject malformed and non-finite decimals. Bounded pagination uses unique internal `name asc` ordering. Currency precision remains ERPNext's permission-safe global currency precision contract; authoritative values remain Decimal and fixed-scale strings.
- Finance route departure is bound to Frappe 16.5.0's real wrapper `hide` event. Hidden-page success and error responses become stale and cannot repopulate the page cache.
- Shared sidebar state is cleared on unmanaged routes. Top-level and nested sidebar workspace identities must both match before caching or rendering.
- Browser policy values are deeply constrained to safe scalar metadata; acronym-led and nested identity, monetary, native, and execution aliases are rejected.
- Python and browser roadmap status now agree on Warehouse `w8c_transfer_visibility`. Existing Sales, Procurement, Warehouse, and Finance priorities are unchanged.
- Behavioral lifecycle smoke covers wrapper hide, late success/error suppression, return to Finance, workspace cache clearing, route switching, nested workspace mismatch, deduplication, and reversed responses.
- Existing Playwright tooling renders representative manager and restricted Finance layouts at desktop and 390px widths and checks horizontal overflow, viewport bounds, and panel overlap.

## Refresh contract

The visible Refresh button remains deliberately disabled while its current request is in flight. Equivalent loads deduplicate. A later enabled refresh starts a new request; internal forced-load tests still prove token supersession. The UI does not claim that a disabled button can supersede its active request.

## Explicit exclusions

These unrelated dirty paths are outside every Finance staging or live-alignment scope:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## Future live-alignment allowlist

No live change occurred. Any later alignment requires separate Owner/Main Control approval and exact hash verification.

| Runtime file | F6B1 source SHA-256 | Current live SHA-256 |
| --- | --- | --- |
| `erp_workspace_ui/boot.py` | `0640d03a7621d749ef214912cb8481fe7d8943c3aed7ccd34e395ee4cd7c7584` | `a84c0b5c8de8a8532325ce593facef40b5d0eafc21c4f00082fbcff1cbbbe578` |
| `erp_workspace_ui/workspace_registry.py` | `936d24b05dff90f9f3aa4cde8cdc9a7ca7c8905e535ca1232a6f29de08ffbbc9` | `3129d1cb0c1d53f89eb848aa3befc3502b0257435830cf994da3755ca445c283` |
| `erp_workspace_ui/workspace_governance_manifest.py` | `4e93e4e25572851d185f9ce7f893767d325fc528634de9305cac02083be60d7c` | `edf722b0304b445af4f1f2b1b6b1c9a72fca4d32a557249f7ccfa1be7d4eef0a` |
| `erp_workspace_ui/public/js/runtime/console/workspace_registry.js` | `d5f26d96129beeca118846a19eb4a0939c2f8536a6d84089b09330a20a7d1b52` | `83dc9f818f30dead996c22ac5bc32d4a6fe50b259c78541b70d82da99f5c5873` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `7865148206a312709bda24d822bd4a0443a2ea836affebacbc54144474ece9aa` | `eb88e76df25178b0ce06c1784c2bb2ff0e0d1e26f53a2c1dadf39019e0598e27` |
| `erp_workspace_ui/finance_accounting/service.py` | `68bbff90135c933a72bdfa88981057a1e1a2ace8bd1fe8f28dd2e0a90ddd2849` | `7a79246430835263cacd920866b1cecfd22e64c8739e20605e7e3733930af948` |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `482dca93f6947b36f9df45a2c74d5cfbe100fbb305bb24e67a4dab232b3d6a25` | `b09a1f30f19a30a515c7e65f54e25745331e0f522a7b9d0319c9f3dc531b0f53` |

`finance_control_desk.json` matches source and live at `fb0e0964cf9883e6224090f1e1efcd27c96798f585bc8afcbeb8dff5e4eaf765` and is not an alignment candidate.

## Boundaries

Payment-schedule aging and allocation, AP amounts, AR/AP rows or browser identities, native reports/routes/exports/download/print, and all accounting or external execution remain blocked. F6C remains blocked until F6B2 independently accepts this source package.
