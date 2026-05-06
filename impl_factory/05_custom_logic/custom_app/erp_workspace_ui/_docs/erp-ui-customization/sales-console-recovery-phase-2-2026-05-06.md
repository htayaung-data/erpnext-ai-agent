# Sales Console Recovery Phase 2

Date: 2026-05-06
Status: Source implementation completed; final commit gate still pending in the Phase 2 sequence
Workspace: Sales Console

## Scope

Main Phase 2 recovered Sales Console against the Shared Core + Workspace Adapter v2 contract without renaming frozen Sales routes or changing confirmed Sales business scope.

This phase did not start Procurement repair, Procurement Phase 4, or a new workspace.

## Shared Core Behavior Hardened

- Route lifecycle uses the shared managed-host cleanup path for Sales overview, worklists, and reports.
- Sidebar/back/forward/direct route smoke now checks that Sales pages do not stack shells or duplicate headers.
- Shared worklist shell behavior covers in-place Apply, Reset, Refresh, date-pair layout, link autocomplete, row-link affordance, and focus stability.
- Shared report shell behavior covers the Sales report family with in-place Apply, Reset, Refresh and distinct ready, empty, restricted, unavailable, and error states.
- Productized Sales pages no longer expose native list/report fallback actions such as `open_native_list` or `open_native_report`.

## Sales Adapter Behavior Hardened

- Sales overview quick actions are limited to manifest-declared actions: New Quotation, New Sales Order, Customers, and Items.
- Live-only `new_opportunity` drift was classified as unapproved and removed from the validation target by syncing the clean Sales overview source for task validation.
- Customer and Item directories declare link autocomplete filters through the Sales adapter payload.
- Customer Detail recent activity row open is declared as a managed Sales document form boundary in the manifest.
- Sales copy was updated to avoid implementation-facing wording such as "permission scope" and "productized review surface".

## Native Exception Posture

Approved Sales managed document forms remain under `sales-managed-document-forms-v1`:

- Quotation
- Sales Order
- Delivery Note
- Sales Invoice

ERPNext remains transaction truth inside those managed form surfaces. Productized overview, worklist, report, customer detail, item detail, and customer editor pages must not expose raw ERPNext list/report/form fallbacks unless a future owner-approved manifest entry declares a governed exception.

## Evidence

Source validation used:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched Sales and smoke JavaScript files
- `git diff --check`

Browser evidence used existing Docker Playwright runner only:

- `sales-route-lifecycle-smoke`
- `sales-action-cards-smoke`
- `sales-worklist-shell-smoke`
- `sales-detail-boundary-smoke`
- `sales-report-family-smoke`
- `sales-native-leakage-smoke`
- `sales-visual-stability-smoke`

Key artifact folders:

- `ui_smoke/artifacts/sales-recovery-baseline-20260506T060311Z`
- `ui_smoke/artifacts/sales-route-lifecycle-smoke`
- `ui_smoke/artifacts/sales-action-cards-smoke`
- `ui_smoke/artifacts/sales-worklist-shell-smoke`
- `ui_smoke/artifacts/sales-detail-boundary-smoke`
- `ui_smoke/artifacts/sales-report-family-smoke`
- `ui_smoke/artifacts/sales-native-leakage-smoke`
- `ui_smoke/artifacts/sales-visual-stability-smoke`

## Accepted Procurement Waiver

Sales Recovery validation passed for the Sales-only Phase 2 gate.

Procurement Phase 2 smoke mismatch was observed during regression, but the owner accepted a waiver because it is unrelated to this Sales-only diff. The observed mismatch is: Supplier Quotation Comparison API returns `["refresh"]`; the existing smoke expects `["refresh", "back_to_console"]`.

This mismatch must be handled in Main Phase 3 Procurement Alignment. No Procurement repair was done in Main Phase 2.

## Remaining Risks

- Controlled task validation alignment touched only approved ERP Workspace UI files in the dirty live deployment repo. It was not a final deployment alignment and was not committed in the live repo.
- Mobile/responsive smoke was not run in Task 8 because the phase changed copy and desktop density only, with no breakpoint or responsive CSS changes.
- Final Phase 2 validation, commit, push, and live alignment gates remain separate exit gates.
