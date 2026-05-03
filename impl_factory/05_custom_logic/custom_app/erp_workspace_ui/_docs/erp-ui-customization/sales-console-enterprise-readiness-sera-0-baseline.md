# Sales Console Enterprise Readiness Audit: SERA-0 Baseline

Date: 2026-04-28
Final alignment update: 2026-05-03
Status: Pass with audit notes
Audit phase: `SERA-0` Audit Setup And Baseline
Depends on: `sales-console-enterprise-readiness-audit-mini-phase-plan.md`

## 1. Purpose

This note records the baseline before the Sales Console enterprise readiness audit moves into route ownership, security, visual stability, and page-family review.

This phase does not change product behavior.

It confirms:

1. correct branch and worktree
2. current commit truth
3. live deployment assumption
4. managed route inventory
5. shared runtime inventory
6. page family inventory
7. known local files that should not be accidentally committed

## 2. Baseline Decision

SERA-0 decision:

`Pass with audit notes`

Reason:

1. the audit is being performed in the correct ERP UI worktree
2. the branch is the expected ERP UI branch
3. the local branch is aligned with origin
4. selected live bench app files match the current worktree implementation files
5. Sales Console managed routes and shared runtimes are identifiable from code
6. untracked non-product files are known and isolated

Notes:

Final alignment update:

1. Current confirmed branch remains `feature/erpnext-ui-design`.
2. Current confirmed commit is `6dbd85c fix: forward socket origin through caddy`.
3. The standalone Dashboard page is not part of the final Sales Console route inventory.
4. `Trend Analysis` is the canonical visible trend report.
5. `quotation_trends` remains a compatibility alias into Trend Analysis with Quotation selected.
6. Full route probing and role smoke were completed after the original baseline note.

1. new documentation files from the standardization work are intentionally uncommitted at this moment
2. live deployment verification is based on selected file comparison through the running gunicorn process root
3. SERA-1 must still validate actual browser navigation behavior page by page

## 3. Branch And Worktree Truth

Audited worktree:

`/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Branch:

`feature/erpnext-ui-design`

Upstream:

`origin/feature/erpnext-ui-design`

Remote:

`https://github.com/htayaung-data/erpnext-ai-agent.git`

Current HEAD:

`ad4587ce098046d2479f8dec4910669720eae88f`

Current latest commit:

`ad4587c feat(erp-ui): advance sales console operating foundation`

Recent commit context:

1. `ad4587c feat(erp-ui): advance sales console operating foundation`
2. `5ad8bca feat(erp-ui): sync customer and item sales console worklists`
3. `ab3ee3e Implement sales console operational worklists`

Status at audit start:

1. branch is aligned with origin
2. docs changed locally
3. raw reference folder remains untracked
4. old backup file remains untracked

## 4. Local Change Posture

Current intentional documentation changes:

1. `enterprise-shared-ui-component-standard-v1.md`
2. `sales-console-enterprise-readiness-audit-mini-phase-plan.md`
3. `sales-console-enterprise-readiness-sera-0-baseline.md`
4. `README.md` index updates

Current known files that should not be committed unless explicitly reviewed:

1. `Raw Base Reference files/`
2. `erp_workspace_ui/sales_console/report.py.20260420_054947.bak`

Ignored local smoke-test artifacts observed:

1. `ui_smoke/node_modules/`
2. `ui_smoke/test-results/`

SERA-0 recommendation:

Keep the raw reference folder and backup file out of commits.

Commit the new standardization docs only after the current audit slice is reviewed or when the user asks to save this documentation checkpoint.

## 5. Live Deployment Assumption

Running gunicorn process observed:

1. master process: `3134796`
2. workers observed: `3134872`, `3134873`
3. process command includes `/home/frappe/frappe-bench/env/bin/gunicorn`
4. app path visible through process root:
   `/proc/3134796/root/home/frappe/frappe-bench/apps/erp_workspace_ui`

Direct `/home/frappe/frappe-bench/apps/erp_workspace_ui` was not visible from this shell context.

Selected live-code comparison through process root:

1. `workspace_console_sidebar.js`: match
2. `worklist.py`: match
3. `report.py`: match
4. `list_page_shell.js`: match

SERA-0 deployment decision:

The live app appears synced for the core Sales Console files checked.

Limit:

This does not prove every asset, cache, or browser-loaded bundle is current. SERA-1 and SERA-3 should still use browser verification for navigation and visual stability.

## 6. Frappe Page Inventory

Current app page records in code:

1. `/desk/sales-console`
   - Frappe page: `sales-console`
   - primary Sales Console home surface
2. `/desk/sales-console-home`
   - Frappe page: `sales-console-home`
   - launcher/handoff page
   - redirects to `sales-console`
3. `/desk/sales-console-worklist`
   - Frappe page: `sales-console-worklist`
   - shared directory, queue, customer detail, and customer editor shell
4. `/desk/sales-console-report`
   - Frappe page: `sales-console-report`
   - shared productized report shell

Bare route guard behavior:

1. bare `/desk/sales-console-worklist` intentionally shows a guarded unavailable state
2. bare `/desk/sales-console-report` intentionally shows a guarded unavailable state

SERA-1 must confirm these guard states are understandable and premium enough in browser.

## 7. App Hook Inventory

App home:

`/desk/sales-console-home`

Reason:

The launcher page hands off to the real Sales Console route without colliding with the page route itself.

Global included runtimes:

1. `erp_workspace_ui_boot.js`
2. `workspace_console_runtime.js`
3. `workspace_console_sidebar.js`
4. child-page shared runtime files
5. `list_page_shell.js`
6. `report_page_shell.js`

Managed form scripts:

1. `Sales Order` -> `sales_order_form.js`
2. `Quotation` -> `quotation_form.js`
3. `Delivery Note` -> `delivery_note_form.js`
4. `Sales Invoice` -> `sales_invoice_form.js`

App screen entry:

1. title: `Sales Console`
2. route: `/desk/sales-console-home`
3. permission guard: `erp_workspace_ui.boot.can_use_sales_console_app`

## 8. Managed Route Inventory

### 8.1 Workspace Home Routes

Managed routes:

1. `/desk/sales-console`
2. `/desk/sales-console-home`

Expected behavior:

1. `sales-console-home` shows a compact opening state
2. then it routes to `sales-console`
3. sidebar active key resolves to `sales_console_home`

Audit note:

SERA-3 should validate that the handoff does not feel like flicker or unstable first paint.

### 8.2 Worklist And Directory Routes

Backend queue keys:

1. `quotation_directory`
2. `sales_order_directory`
3. `open_orders`
4. `sales_orders_pending_fulfillment`
5. `partially_delivered_orders`
6. `orders_due_soon`
7. `quotations_waiting_action`
8. `customer_directory`
9. `customer_detail`
10. `item_directory`
11. `expiring_quotations`
12. `orders_blocked_by_approval`
13. `quotations_awaiting_approval`
14. `customer_follow_up_tasks`
15. `invoices_outstanding`
16. `sales_returns_in_progress`
17. `customer_editor`

Frontend route form:

The frontend converts underscores to hyphens in URL route segments.

Examples:

1. `/desk/sales-console-worklist/quotation-directory`
2. `/desk/sales-console-worklist/sales-order-directory`
3. `/desk/sales-console-worklist/customer-directory`
4. `/desk/sales-console-worklist/item-directory`
5. `/desk/sales-console-worklist/customer-detail/<encoded-customer>`
6. `/desk/sales-console-worklist/customer-editor/<encoded-customer>`
7. `/desk/sales-console-worklist/customer-editor`

Customer route behavior:

1. `customer_detail` supports customer identity in the third route segment
2. `customer_editor` supports customer identity in the third route segment for edit mode
3. `customer_editor` without a customer defaults to new-customer mode
4. route options may still pass filters, but customer detail/edit deep links are no longer only transient route state

SERA-1 must validate direct refresh for:

1. `customer-detail/<customer>`
2. `customer-editor/<customer>`
3. `customer-editor`

### 8.3 Report Routes

Backend report keys:

1. `sales_analytics`
2. `sales_order_analysis`
3. `trend_analysis`
4. `quotation_trends`
5. `collections_status`
6. `payment_terms_status_sales_order`
7. `item_wise_sales_history`
8. `lost_quotations`

Frontend route form:

The frontend accepts report keys through:

`/desk/sales-console-report/<report-key>`

The report route normalizes hyphens to underscores.

Examples:

1. `/desk/sales-console-report/sales-order-analysis`
2. `/desk/sales-console-report/trend-analysis`
3. `/desk/sales-console-report/collections-status`
4. `/desk/sales-console-report/item-wise-sales-history`
5. `/desk/sales-console-report/lost-quotations`

Compatibility examples:

1. `/desk/sales-console-report/quotation-trends`
2. `/desk/sales-console-report/payment-terms-status-sales-order`

Audit note:

Current sidebar active-state resolver returns no active sidebar item for report pages because the navigation contract does not yet include a top-level Reports destination.

SERA-1 should confirm this remains intentional and acceptable.

### 8.4 Managed Form Routes

Managed doctypes:

1. `Quotation`
2. `Sales Order`
3. `Customer`
4. `Item`
5. `Delivery Note`
6. `Sales Invoice`

Active sidebar mapping:

1. `Quotation` -> `quotation_directory`
2. `Sales Order` -> `sales_order_directory`
3. `Customer` -> `customer_directory`
4. `Item` -> `item_directory`
5. `Delivery Note` -> `sales_order_directory`
6. `Sales Invoice` -> `sales_order_directory`

Route styles recognized:

1. Frappe form route: `Form/<doctype>/<name>`
2. desk slug route: `/desk/quotation/<name>`
3. desk slug route: `/desk/sales-order/<name>`
4. desk slug route: `/desk/customer/<name>`
5. desk slug route: `/desk/item/<name>`
6. desk slug route: `/desk/delivery-note/<name>`
7. desk slug route: `/desk/sales-invoice/<name>`

SERA-1 must verify that managed forms retain the Sales Console sidebar and scoped search after refresh and route transition.

## 9. Shared Runtime Inventory

### 9.1 Console Runtime

Files:

1. `workspace_console_runtime.js`
2. `workspace_console_sidebar.js`

Responsibilities:

1. Sales Console home rendering support
2. action target routing
3. sidebar replacement
4. active-state mapping
5. scoped workspace search
6. managed-route detection

### 9.2 List Runtime

File:

`list_page_shell.js`

Responsibilities:

1. directory and queue shell
2. filter command strip
3. metrics
4. result tables
5. row actions
6. form-panel layout for customer create/edit
7. top-level actions such as Apply, Reset, Refresh, Back

### 9.3 Report Runtime

File:

`report_page_shell.js`

Responsibilities:

1. report shell
2. report filters
3. metrics
4. result table
5. report actions
6. route-unavailable states

### 9.4 Child Page Runtime

Files:

1. `child_page_helpers.js`
2. `child_page_sections.js`
3. `child_page_details.js`
4. `child_page_terms.js`
5. `child_page_summaries.js`
6. `child_page_observability.js`
7. `child_page_shell.js`
8. `child_page_shell_content.js`
9. `child_page_runtime.js`
10. `child_page_connections.js`
11. `child_page_support.js`
12. `child_page_operating_actions.js`
13. `child_page_sidebar.js`

Responsibilities:

1. saved document shell
2. draft readiness
3. action band
4. document actions
5. business-copy suppression rules
6. details and summary sections
7. connection cards
8. support/footer behavior
9. native action orchestration for save, print, email, assign, comment, and share

### 9.5 Backend Services

Files:

1. `sales_console/service.py`
2. `sales_console/worklist.py`
3. `sales_console/report.py`

Responsibilities:

1. bootstrap payload
2. user context and scope
3. sidebar context
4. workspace search
5. worklist payloads
6. report payloads
7. customer detail
8. customer create/edit save
9. permission-aware restricted states

## 10. Page Family Inventory

### Family A: Workspace Entry

Surfaces:

1. Sales Console home
2. launcher handoff page
3. shared sidebar
4. scoped workspace search

Primary SERA focus:

1. first paint stability
2. sidebar replacement stability
3. no native global search duplication
4. role-aware home actions
5. one source of truth for workspace entry

### Family B: Directories And Queues

Surfaces:

1. Quotations directory
2. Sales Orders directory
3. Customers directory
4. Items directory
5. operational queues for approvals, follow-up, fulfillment, invoices, returns, and expiring quotations

Primary SERA focus:

1. filter clarity
2. row navigation
3. all-record versus queue-slice clarity
4. restricted and empty states
5. table readability

### Family C: Customer Profile Surfaces

Surfaces:

1. Customer Detail
2. Create Customer
3. Edit Customer

Primary SERA focus:

1. deep-link refresh
2. safe-field boundary
3. save persistence
4. Sales User versus Sales Manager behavior
5. navigation back to Customers or Customer Detail

### Family D: Draft Documents

Surfaces:

1. New Quotation
2. New Sales Order

Primary SERA focus:

1. draft readiness quality
2. action-band posture
3. native save/submit boundary
4. print/email disabled state
5. first-load stability
6. future stock-availability integration readiness

### Family E: Saved Execution Documents

Surfaces:

1. saved Quotation
2. saved Sales Order
3. managed Delivery Note
4. managed Sales Invoice

Primary SERA focus:

1. summary header
2. action band
3. attention cards
4. connection cards
5. native fallback boundaries
6. print/email entry points

### Family F: Reports

Surfaces:

1. Sales Analytics
2. Sales Order Analysis
3. Trend Analysis
4. Collections Status
5. Payment Terms Status for Sales Order as collections alias
6. Item Wise Sales History
7. Lost Quotations

Primary SERA focus:

1. report purpose
2. compact filters
3. metric clarity
4. row navigation safety
5. native report fallback behavior

## 11. Existing Validation Inventory

Current committed validation assets:

1. `test_sales_console_service_contracts.py`
2. `test_sales_console_operating_contracts.py`
3. `ui_smoke/`
4. `scripts/verify_runtime_asset_serving.sh`

Current SERA-0 validation performed:

1. branch and upstream confirmed
2. selected live file comparison passed
3. route key inventory extracted from backend registries
4. report key inventory extracted from backend registry
5. managed form mapping extracted from sidebar runtime
6. documentation hygiene checks should be run after this file is linked

SERA-0 does not claim browser smoke has passed.

Browser smoke belongs to later SERA phases.

## 12. Baseline Risks For Next Phases

These are not SERA-0 blockers, but they must be audited next.

### 12.1 Route Ownership Risk

Some actions intentionally still allow native fallback targets.

SERA-1 must classify every fallback as:

1. acceptable
2. needs productized route
3. should be hidden
4. should be deferred

### 12.2 Report Sidebar Active State

Report pages currently do not map to a sidebar item because there is no Reports sidebar destination in V1.

SERA-1 must confirm whether this is still acceptable after the report family became stronger.

### 12.3 Launcher Handoff Stability

`sales-console-home` hands off to `sales-console`.

SERA-3 must verify whether this feels stable enough in browser and does not create a visible double-load experience.

### 12.4 Native Form Surface Leakage

Managed form routes include native ERP form content beneath the custom shell.

SERA-1 and SERA-3 must verify:

1. sidebar stays productized
2. native global search does not duplicate custom search
3. native menu overflow does not expose unsafe business actions
4. top toolbar actions remain acceptable and governed

### 12.5 Customer Editor Route Options

Customer edit has a route segment for customer identity.

Customer create uses `customer_editor` without a customer and defaults to new mode.

SERA-1 must validate direct refresh of both create and edit routes.

### 12.6 Documentation Checkpoint

The enterprise standard, mini-phase plan, and SERA-0 baseline are local documentation changes.

These should be committed after review if accepted.

## 13. SERA-0 Exit Criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Correct branch confirmed | Pass | `feature/erpnext-ui-design` |
| Correct worktree confirmed | Pass | `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design` |
| Upstream alignment confirmed | Pass | local branch aligned with `origin/feature/erpnext-ui-design` |
| Current commit recorded | Pass | `ad4587c` |
| Live deployment assumption recorded | Pass | selected files match through process-root app path |
| Managed route inventory recorded | Pass | worklist/report registries and sidebar runtime reviewed |
| Shared runtime inventory recorded | Pass | runtime files listed from current code |
| Page family inventory recorded | Pass | Families A through F defined |
| Untracked files posture recorded | Pass | docs pending, raw refs and backup excluded |

SERA-0 is complete.

## 14. Next Step

Proceed to `SERA-1 Route Ownership And Navigation Safety`.

Recommended first SERA-1 artifact:

Create a route matrix covering:

1. source page
2. element label
3. expected target
4. actual target
5. route type
6. business decision
7. fix status

Priority route groups for SERA-1:

1. sidebar navigation
2. Sales Console home cards
3. directory row opens
4. Customer Detail activity row opens
5. saved Quotation and Sales Order action bands
6. Connections tab actions
7. report row opens
8. native fallback actions
