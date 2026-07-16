# Finance & Accounting F6E3 Visual Accessibility and Final Acceptance Preparation

Date: 2026-07-14
Status: Source preparation completed; F6E4 blocked pending focused accessibility remediation

## Purpose

F6E3 prepares the accepted Finance Cycle 1 source package for a separately approved F6E4 controlled alignment and authenticated browser review. It makes one visual-accessibility correction, records the accepted F6E2 authorization evidence, and defines the manual acceptance sequence across all four managed workspaces.

F6E3 does not change Finance accounting semantics, source reads, role authority, company scope, payload contracts, routes, or execution boundaries. It does not approve F6E4, F6F, or final Cycle 1 closure.

## Shared UI accessibility correction

Finance Control Desk already follows the shared command-surface grammar: a constrained shell, dark hero, compact eyebrow, primary heading, business summary, boundary chips, posture panels, and a visible Refresh control. Sales uses `#f8fafc` for its title on the shared dark command surface, and the Warehouse dark command variant uses the same light-on-dark family.

The Finance hero already declared `#f8fafc` as its foreground, but the `h1` did not explicitly override Frappe's heading color. F6E3 applies `#f8fafc` directly to `.finance-control-title`. Layout, hierarchy, copy, badges, cards, focus treatment, responsive breakpoints, and accounting boundaries are unchanged.

The minimum contrast against every current Finance hero gradient stop is 7.77:1. The smoke requires an explicit title override against a representative Frappe heading rule and enforces a minimum 4.5:1 ratio. Its responsive contract covers desktop, 390px, and 320px widths across ready, restricted, and unavailable states.

## Accessibility findings before F6E4

Independent review accepted the heading correction but found two separate High accessibility issues outside this narrow patch:

- The shared managed-workspace sidebar removes the browser outline and replaces it with a near-white focus ring on light surfaces. The focus indicator does not meet the 3:1 non-text contrast expectation.
- Finance Refresh replaces its focused button when the overview rerenders. Focus is not restored, and the completed ready/unavailable result is not exposed through a persistent status announcement.

The existing unavailable card value `No counts` is also potentially ambiguous without its accompanying unavailable detail. It is not a verified zero and must not be treated as one during manual review.

These findings do not change accounting authority or invalidate the accepted F6E2 permission fix, but they block F6E4 live alignment until a separately approved, focused source remediation is completed and reviewed. F6E3 does not patch the shared sidebar or Finance interaction lifecycle.

## Accepted F6E2 evidence

Owner browser evidence accepted before F6E3:

- `finance.lead@meet.com` opens Finance Control Desk without an `Insufficient Permission for User Permission` modal.
- The Accounts Manager receives only the controlled, company-scoped aggregate posture allowed by the existing Finance gates.
- `accounts.ygn.01@meet.com` opens Finance Control Desk without a permission modal and receives no manager-only AR amounts or AP counts.
- Neither account receives row-level customer, supplier, invoice, voucher, account, Payment Ledger, or GL identity data.
- No native Finance report, route, export, download, print, or execution action is exposed.

This evidence accepts the F6E2 company-scope permission-message correction only. It is not final cross-workspace acceptance and does not close F6F.

## Source and live status

Before the F6E3 visual edit, the accepted F6E2 Finance service and Finance page matched live:

| Runtime path | Source/live SHA-256 before F6E3 | Status |
| --- | --- | --- |
| `erp_workspace_ui/finance_accounting/service.py` | `e5870574d11e4d5d1754814f5f5faf90df645ce47c16ebee73e2e7505023af9e` | F6E2 source/live aligned |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `8b06e2c3b1de1feb3366421e92d7299e27ef2b978a7040ae77310ef0d171ac70` | Matched before F6E3 |

After F6E3, the only expected Finance runtime difference is:

- `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js`

The F6E3 document, README entry, and responsive smoke are source/review evidence and are not required in the live runtime alignment. The F6E2 service is already aligned and must not be recopied merely for the heading correction.

## F6E4 authenticated manual browser package

Use a fresh authenticated session for each representative account. Record pass/fail and the observed route. Screenshots are optional; the checklist is authoritative.

### Finance - Accounts Manager

1. Sign in from the site root as `finance.lead@meet.com`.
2. Confirm the root landing reaches Finance Control Desk under the approved landing priority.
3. Open `/desk/finance-control-desk` directly and confirm the same workspace loads.
4. Confirm `Finance Control Desk` is clearly readable on the dark hero at desktop and approximately 390px width.
5. Confirm the page shows company-scoped, aggregate-only Finance posture when all existing gates pass.
6. Confirm AR count and manager-only MMK amount signals remain separately described.
7. Confirm Payables remains count-only and may show a controlled unavailable state when Payment Schedule semantics are unsupported.
8. Select Refresh once. Confirm it is unavailable while the request is active, becomes usable after settlement, and does not leave a blank or permanently loading page.
9. With an approved deterministic network-delay harness, start request A, leave Finance, return to create request B, then settle A after B. Repeat with A failing late. Confirm A cannot render, cache, or replace B and no stale loading or error state remains.
10. Confirm there is no permission modal, raw reason code, technical traceback, row-level identity, native report, export, download, print, or execution control.

### Finance - Accounts User

1. Sign in from the site root as `accounts.ygn.01@meet.com`.
2. Confirm the root landing reaches Finance Control Desk and the direct route also loads.
3. Confirm manager-only AR amounts and AP counts are not shown.
4. Confirm unavailable copy is business-facing and contains no internal policy or permission reason.
5. Refresh and confirm the limited Finance state remains stable without a modal, blank page, stale manager state, or loading failure.
6. Confirm there is no customer, supplier, invoice, voucher, account, Payment Ledger, GL, report, route, export, or action data.

### Sales

1. Sign in as a representative Sales user and, separately, a Sales manager.
2. Confirm root landing follows the approved Sales-first role priority.
3. Open Sales Console, its worklist, and its report pages using managed navigation.
4. Enter a search query, change it before the delayed response settles, and confirm only the latest query appears.
5. Use Clear, leave the route while a response is pending, and confirm no result, suggestion, AI content, timer content, sidebar, or header is reinserted after departure.
6. Return to Sales and confirm search and navigation remain usable without duplicate bootstrap content.
7. Repeat the delayed-response and Clear checks in the shared workspace sidebar search. Confirm an old result or governed target cannot reappear or dispatch after leaving and returning to Sales.

### Procurement

1. Sign in as a representative Purchase user and, separately, a Purchase manager.
2. Confirm root landing follows Procurement when no higher-priority Sales role is present.
3. Open Procurement Console, worklist, and report pages through managed navigation.
4. Use Quick Find, change the query before a delayed response settles, and confirm only the latest query is rendered.
5. Use Clear and leave the route while a response is pending. Confirm no stale result, preview, sidebar, or header appears after departure.
6. Return to Procurement and confirm Quick Find, worklist, and report navigation remain usable.
7. Repeat the delayed-response and Clear checks in the shared workspace sidebar search. Confirm an old result or governed target cannot reappear or dispatch after leaving and returning to Procurement.

### Warehouse

1. Sign in as a representative Warehouse user and, separately, a Warehouse manager.
2. Confirm root landing reaches Warehouse only when no Sales, Procurement, or Finance role has priority.
3. Confirm the custom Warehouse overview and its approved custom workspace navigation load.
4. Start a shared-sidebar search, change or clear its query, and leave Warehouse before the delayed result settles. Confirm no result, target, sidebar, or header is reinserted after departure or after returning.
5. Switch between Warehouse routes and another managed workspace. Confirm no stale Warehouse sidebar or header remains.
6. Confirm there is no unintended stock posting, transfer execution, valuation action, notification, native form/list/report escape, or other authority expansion.

### Cross-workspace isolation

1. Confirm `Sales + Procurement + Accounts + Warehouse` roles land in Sales.
2. Confirm `Procurement + Accounts + Warehouse` roles land in Procurement.
3. Confirm `Accounts + Warehouse` roles land in Finance.
4. Confirm a Warehouse-only role lands in Warehouse.
5. Switch rapidly among Sales, Procurement, Finance, Warehouse, and an unmanaged/native route.
6. Confirm each route shows only its current header, sidebar, search state, and body classes.
7. Start request A in one workspace, switch to a second workspace, return to the first workspace, then let A finish after the current request. Repeat with a late failure. Confirm A cannot store, render, dispatch, or leave a stale loading/error state.
8. Use a visibly distinct governed result in each workspace and confirm the prior workspace's target cannot dispatch after a switch.
9. Delete or clear a pending shared-sidebar query in Sales, Procurement, and Warehouse, then settle the older response. Confirm no result reappears. In Finance, confirm shared search is unavailable and no prior workspace dialog remains.
10. Return to each managed workspace and confirm current-route controls remain usable without duplicate content.
11. Open Finance directly with a non-Finance role and confirm no Finance data is returned, even if the page shell is reachable.
12. Confirm managed workspace targets do not escape to native forms, lists, reports, exports, print, new-document, or execution surfaces.

## F6E4 acceptance conditions

F6E4 manual acceptance requires all of the following:

- The Finance heading remains readable at desktop and 390px widths without layout regression.
- Accounts Manager and Accounts User behavior matches the role boundaries above.
- No browser-visible permission message or internal reason code appears.
- Refresh, route departure, delayed responses, and rapid workspace switching preserve current-route authority.
- Keyboard focus remains visibly indicated in the shared sidebar at a minimum 3:1 contrast and is not obscured.
- Refresh preserves or intentionally restores keyboard focus, and its busy/completed status is announced without exposing technical text.
- Any unavailable card reads as unavailable rather than a verified zero; `No counts` is never interpreted as an accounting balance or zero population.
- Sales, Procurement, and Warehouse representative flows remain functional.
- Landing priority remains `Sales > Procurement > Finance > Warehouse`.
- No row identity, native Finance surface, export, or accounting execution appears.

Any permission modal, stale cross-workspace render, native target escape, manager data shown to Accounts User, or accounting identity exposure blocks F6F.

## Boundaries preserved

F6E3 adds no:

- Finance source read or accounting-semantics change;
- role, permission, Page metadata, company-scope, or payload-contract change;
- AR/AP rows or customer, supplier, invoice, voucher, account, Payment Ledger, or GL identities;
- AP amounts or Payment Schedule aging/allocation;
- native report, route, export, download, print, email, notification, portal, or external action;
- posting, payment, reconciliation, write-off, tax, close, or other accounting execution;
- Sales, Procurement, or Warehouse behavior change.

No live alignment, restart, cache clear, metadata reload, migration, staging, commit, push, permission change, or protected gate is approved by this artifact.

## Next gate

The next permitted work is a separately approved, focused source remediation for shared-sidebar focus visibility and Finance Refresh focus/status preservation, followed by independent review. F6E4 controlled alignment and authenticated manual review may begin only after those findings are closed and Owner/Main Control approves the gate. F6F closure remains blocked until F6E4 passes.
