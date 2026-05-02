# Sales Console Enterprise Readiness Audit: SERA-1 Route Ownership

Date: 2026-04-28
Status: Pass with shared route hardening and required browser verification
Audit phase: `SERA-1` Route Ownership And Navigation Safety
Depends on: `sales-console-enterprise-readiness-sera-0-baseline.md`

## 1. Purpose

This note records the Sales Console route ownership audit.

The goal is to prove that Sales Console has one user journey and does not accidentally leak sales users into confusing raw ERP pages when a productized Sales Console route exists.

This phase primarily audits the implementation. It does not change product behavior.

## 2. SERA-1 Decision

SERA-1 decision:

`Pass with shared route hardening and required browser verification`

Reason:

1. primary Sales Console navigation is centralized through shared route helpers
2. productized worklists, directories, reports, customer detail, and customer editor use owned Sales Console routes
3. document pages use managed ERP form routes with Sales Console sidebar and document-shell enhancements
4. native fallback exists, but it is mostly controlled through shared route policy instead of random page-local links
5. customer detail and customer editor deep links now carry the customer name in the route and should survive refresh
6. shared route hardening was applied for customer detail/editor active state and the payment-terms report alias
7. remaining browser behavior must still be verified before SERA-1 is frozen

Important limitation:

Authenticated browser smoke was not executed in this phase because `ERP_UI_SMOKE_SID` is not set in the shell environment. This audit is a static code audit plus implementation contract review.

## 3. Route Ownership Principle

Sales Console should own the sales user's journey.

Route ownership does not mean every destination must be a brand-new custom page.

It means every navigation must be classified before it is allowed:

1. `productized route`
   - a Sales Console owned page, worklist, report, detail, editor, or directory
2. `managed native form`
   - a native ERPNext document form that is intentionally enhanced by Sales Console runtime
3. `governed native fallback`
   - a native ERP list or report used only when no productized page exists or when restricted-state recovery requires it
4. `deferred route`
   - a business-visible destination that is intentionally not opened because its productized page is not ready
5. `blocked route`
   - an action the sales workspace should not expose

This classification is the route ownership contract for future workspaces.

## 4. Shared Route Owner Inventory

### 4.1 Shared JavaScript Route Owner

Primary shared route owner:

`erp_workspace_ui/public/js/runtime/child_page/child_page_helpers.js`

Important functions and contracts:

1. `routeToSalesConsoleTarget(target)`
   - accepts abstract targets from pages
   - routes to Sales Console worklists where productized routes exist
   - routes to managed ERP forms where form enhancement exists
   - shows deferred notices for destinations that should not open raw ERP yet
   - returns `false` only when the caller may use native fallback
2. `routeToWorklist(queueKey, filters)`
   - owns `/desk/sales-console-worklist/<queue-key>`
   - encodes customer deep links for `customer_detail` and `customer_editor`
3. `routeToDoc(doctype, name)`
   - first asks `routeToSalesConsoleTarget`
   - falls back to native Form route only when the shared owner allows no Sales Console target
4. `routeToList(doctype, filters)`
   - first asks `routeToSalesConsoleTarget`
   - falls back to native List route only when the shared owner allows no Sales Console target

### 4.2 Shared Sidebar Route Owner

Primary sidebar runtime:

`erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`

Managed route families:

1. `/desk/sales-console`
2. `/desk/sales-console-home`
3. `/desk/sales-console-worklist/<queue-key>`
4. `/desk/sales-console-report/<report-key>`
5. managed native forms:
   - `Quotation`
   - `Sales Order`
   - `Customer`
   - `Item`
   - `Delivery Note`
   - `Sales Invoice`

Sidebar menu contract:

1. `Overview` points to Sales Console home
2. `Quotations` points to `quotation_directory`
3. `Sales Orders` points to `sales_order_directory`
4. `Customers` points to `customer_directory`
5. `Items` points to `item_directory`

Current active-state mapping:

1. Quotation form and quotation worklists map to `quotation_directory`
2. Sales Order, Delivery Note, Sales Invoice forms and sales-order worklists map to `sales_order_directory`
3. Customer form maps to `customer_directory`
4. Item form maps to `item_directory`
5. customer detail and customer editor map to `customer_directory`
6. report pages intentionally have no sidebar active item in V1

SERA-1 hardening:

`customer_detail` and `customer_editor` now resolve to `customer_directory` in the shared sidebar active-state map.

## 5. Productized Route Registry

### 5.1 Frappe Page Routes

Owned Frappe page routes:

| Route | Owner | Decision |
| --- | --- | --- |
| `/desk/sales-console` | Sales Console home | Productized |
| `/desk/sales-console-home` | Sales Console launcher | Productized handoff |
| `/desk/sales-console-worklist/<queue-key>` | Shared worklist shell | Productized |
| `/desk/sales-console-report/<report-key>` | Shared report shell | Productized |

Guarded routes:

| Route | Behavior | Decision |
| --- | --- | --- |
| `/desk/sales-console-worklist` | unavailable state when no queue key exists | Accept |
| `/desk/sales-console-report` | unavailable state when no report key exists | Accept |

### 5.2 Worklist Queue Routes

Productized queue keys from `sales_console/worklist.py`:

| Queue key | User meaning | Route type |
| --- | --- | --- |
| `quotation_directory` | all visible quotations | Productized directory |
| `sales_order_directory` | all visible sales orders | Productized directory |
| `customer_directory` | all visible customers | Productized directory |
| `customer_detail` | customer drill-down | Productized detail |
| `customer_editor` | customer create/edit | Productized form shell |
| `item_directory` | all visible items | Productized directory |
| `open_orders` | order operations slice | Productized worklist |
| `sales_orders_pending_fulfillment` | pending fulfillment slice | Productized worklist |
| `partially_delivered_orders` | partial delivery slice | Productized worklist |
| `orders_due_soon` | due-soon order slice | Productized worklist |
| `quotations_waiting_action` | quotation follow-up slice | Productized worklist |
| `expiring_quotations` | expiring quotation slice | Productized worklist |
| `orders_blocked_by_approval` | approval blocker slice | Productized worklist |
| `quotations_awaiting_approval` | quotation approval slice | Productized worklist |
| `customer_follow_up_tasks` | follow-up task slice | Productized worklist |
| `invoices_outstanding` | receivable exposure slice | Productized worklist |
| `sales_returns_in_progress` | returns slice | Productized worklist |

Deep-link decision:

1. `customer_detail` should use `/desk/sales-console-worklist/customer-detail/<encoded-customer>`
2. `customer_editor` edit mode should use `/desk/sales-console-worklist/customer-editor/<encoded-customer>`
3. new customer mode may use `/desk/sales-console-worklist/customer-editor`

This is the correct route ownership pattern because refresh does not depend only on `frappe.route_options`.

### 5.3 Productized Report Routes

Productized report keys from `sales_console/report.py`:

| Report key | User meaning | Route type |
| --- | --- | --- |
| `sales_analytics` | sales overview analytics | Productized report |
| `sales_order_analysis` | order execution analysis | Productized report |
| `quotation_trends` | quotation movement | Productized report |
| `collections_status` | receivable collection status | Productized report |
| `payment_terms_status_sales_order` | collections alias | Productized backend alias |
| `item_wise_sales_history` | item-level sales history | Productized report |
| `lost_quotations` | lost quotation analysis | Productized report |

Audit finding:

`payment_terms_status_sales_order` is supported by the report backend and report page title mapping, but `_report_target` in `sales_console/service.py` does not include it in the `productized_report_keys` set. If this report key is exposed from the home catalog or future navigation, it should route to `report_page` rather than native report.

SERA-1 hardening:

`payment_terms_status_sales_order` is now included in the productized report key set used by `_report_target`.

Required follow-up:

Verify in browser only if this alias becomes a visible report-card route.

## 6. Navigation Matrix

### 6.1 Home And Sidebar

| Source | Element | Expected target | Actual route type | Decision |
| --- | --- | --- | --- | --- |
| Sidebar | Overview | `/desk/sales-console` | Productized | Accept |
| Sidebar | Quotations | `quotation_directory` | Productized | Accept |
| Sidebar | Sales Orders | `sales_order_directory` | Productized | Accept |
| Sidebar | Customers | `customer_directory` | Productized | Accept |
| Sidebar | Items | `item_directory` | Productized | Accept |
| Sidebar | Search | scoped Sales Console search dialog | Productized utility | Accept |
| Sidebar | Notification | native notifications surfaced in custom shell | Managed native utility | Accept for V1 |
| Home | New Quotation | native new Quotation form | Managed native form | Accept |
| Home | New Sales Order | native new Sales Order form | Managed native form | Accept |
| Home | Customers | `customer_directory` | Productized | Accept |
| Home | Items | `item_directory` | Productized | Accept |

Decision:

New Quotation and New Sales Order intentionally open native new-document forms because ERPNext remains the transaction owner for creation, save, workflow, print, and email. The Sales Console runtime owns the surrounding navigation, readiness guidance, and sidebar.

### 6.2 Directory And Worklist Rows

| Source | Row/action | Expected target | Actual route type | Decision |
| --- | --- | --- | --- | --- |
| Quotation directory | Open row | Quotation form | Managed native form | Accept |
| Sales Order directory | Open row | Sales Order form | Managed native form | Accept |
| Customer directory | Open row | `customer_detail` | Productized detail | Accept |
| Customer detail | Activity row | matching document | Productized if directory/form exists, managed native if enhanced form exists | Accept |
| Item directory | Open row | Item route context | Productized directory or managed native form depending helper outcome | Browser verify |
| Operational queues | Open row | matching Quotation or Sales Order form | Managed native form | Accept |
| Restricted worklist state | Open Native List | ERP list fallback | Governed native fallback | Accept only as recovery |

Required follow-up:

Confirm Item row behavior in browser. If opening an Item form feels like raw ERP leakage, decide whether Item Detail should be productized before next workspace.

### 6.3 Customer Detail And Customer Editor

| Source | Element | Expected target | Actual route type | Decision |
| --- | --- | --- | --- | --- |
| Customer detail | Back to Customers | `customer_directory` | Productized | Accept |
| Customer detail | Edit Customer | `customer_editor/<customer>` | Productized form shell | Accept |
| Customer editor edit mode | Back to Customer | `customer_detail/<customer>` | Productized detail | Accept |
| Customer editor new mode | Back to Customers | `customer_directory` | Productized | Accept |
| Customer editor | Save Customer | whitelisted backend API then stay on page | Server mutation with route stability | Accept, SERA-2 must audit permissions |

Deep-link finding:

The implementation supports customer names in the address route for detail and editor pages. This is the correct enterprise pattern because reload should not lose the customer context.

Browser verification required:

1. refresh `customer-detail/<customer>` and confirm detail stays loaded
2. refresh `customer-editor/<customer>` and confirm edit form stays loaded
3. confirm Customers remains the active sidebar item on both pages

### 6.4 Saved Document Actions

Managed form scripts:

1. `quotation_form.js`
2. `sales_order_form.js`
3. `delivery_note_form.js`
4. `sales_invoice_form.js`

Route policy:

1. document action bands must use `routeToDoc` and `routeToList`
2. those functions must ask `routeToSalesConsoleTarget` first
3. linked document action cards are filtered by `applySalesConsoleDocumentActionPolicy`
4. only business-relevant next actions should remain in the top action band

Current decision:

This is acceptable for V1.

Important distinction:

Opening a saved Quotation, Sales Order, Delivery Note, or Sales Invoice is not considered route leakage if the Sales Console sidebar and document shell are active. These are managed native forms, not raw native lists.

### 6.5 Connections Tab Links

Current route policy:

1. linked document lists call the shared `routeToList`
2. `Quotation`, `Sales Order`, `Customer`, `Item`, and `ToDo` map to productized worklists/directories
3. `Delivery Note` and `Sales Invoice` list routes are form-only/deferred for list behavior and should show a controlled notice instead of opening raw list pages
4. single linked Delivery Note and Sales Invoice documents may open managed enhanced forms
5. `Opportunity`, `Payment Entry`, `Warehouse`, `Supplier`, `Driver`, and similar non-productized doctypes are deferred

Enterprise decision:

Keep this rule.

Sales Console should not expose generic raw ERP creation or list pages from Connections just because ERPNext has them. If a related document type becomes business-critical, create a productized route or a managed form policy first.

### 6.6 Reports

| Source | Element | Expected target | Actual route type | Decision |
| --- | --- | --- | --- | --- |
| Home/report card | productized report key | `/desk/sales-console-report/<report-key>` | Productized | Accept |
| Report cell link | Quotation/Sales Order/Customer/Item/ToDo | shared route owner | Accept |
| Report cell link | Delivery Note/Sales Invoice | managed form if single document | Accept |
| Report cell link | non-productized doctype | deferred or native fallback depending helper | Verify |
| Sidebar active state | report page | none | Accepted V1 decision |

Report sidebar decision:

Sales Console does not currently have a Reports sidebar destination. Therefore report pages intentionally do not highlight a sidebar item. This is acceptable for V1, but should be revisited if reports become a primary navigation family.

## 7. Native Fallback Classification

Native fallback is allowed only when it is intentional.

Allowed V1 fallback cases:

1. ERP new-document form for Quotation and Sales Order creation
2. managed ERP document forms for Quotation, Sales Order, Delivery Note, and Sales Invoice
3. restricted-state recovery when the productized list cannot read rows
4. non-productized report fallback if explicitly emitted by `_report_target`
5. native print and email composer, because ERPNext remains the print/email authority

Not allowed:

1. a productized directory card opening raw ERP List
2. a customer drill-down losing context on refresh
3. a row action opening raw Customer form when `customer_detail` exists
4. a generic Connections create button for a doctype without a productized or managed route
5. sidebar active state showing two selected destinations
6. Ctrl+K opening both native ERP search and scoped Sales Console search

## 8. Findings

### Finding 1: Customer Detail/Editor Sidebar Active State Hardened

Severity:

Medium before hardening, low after hardening

Evidence:

`resolveActiveKey` maps many quotation and sales-order worklist variants back to their directory keys. SERA-1 now maps `customer_detail` and `customer_editor` to `customer_directory` as the shared Customers menu owner.

Risk:

Customers should remain selected on customer detail/editor pages. Browser verification is still required because visual active state depends on the loaded sidebar payload and browser route timing.

Implementation:

Updated shared sidebar runtime, not page-specific code.

### Finding 2: Productized Report Alias Hardened

Severity:

Low before hardening, very low after hardening

Evidence:

`payment_terms_status_sales_order` is supported by the report backend and report page mapping. SERA-1 now includes it in the service `_report_target` productized report key set.

Risk:

If a visible report card uses this alias in the future, it should route to the productized report shell.

Static exposure note:

The service report catalog search did not show this alias as a currently emitted home/report-card key, but the frontend still carries display-name support for it. Treat it as a compatibility alias unless future navigation exposes it.

Implementation:

Updated `_report_target` so the alias is productized if emitted.

### Finding 3: Item Row Ownership Needs Browser Verification

Severity:

Low to medium

Evidence:

`Item` is a productized directory key and also a managed form doctype in the sidebar map. The route owner can route list activity to the item directory, but item row open behavior should be confirmed in browser for user expectation.

Risk:

Users may feel they have left Sales Console if an Item opens as a raw form without enough Sales Console context.

Recommended decision:

If sales users mostly need stock and sales posture, keep Item Directory as the main productized page and defer Item Detail until there is a clear business case.

### Finding 4: Reports Have No Sidebar Active Item By Design

Severity:

Low

Evidence:

`resolveActiveKey` returns blank for `sales-console-report`.

Risk:

Report pages may feel slightly less anchored than directories.

Recommended decision:

Accept for V1 unless reports become a major navigation family. Do not add a Reports menu item just to solve active state unless reports become a daily user destination.

### Finding 5: Browser Verification Not Yet Executed

Severity:

Medium process risk

Evidence:

`ERP_UI_SMOKE_SID` is not set.

Risk:

Static code audit can miss browser timing, route option, hard refresh, and active-sidebar behavior.

Recommended action:

Run an authenticated browser route test or ask the user to manually verify the critical URLs listed below.

## 9. Required Browser Verification Script

Use an authenticated Sales Manager session.

Verify these routes:

1. `/desk/sales-console`
2. `/desk/sales-console-worklist/quotation-directory`
3. `/desk/sales-console-worklist/sales-order-directory`
4. `/desk/sales-console-worklist/customer-directory`
5. `/desk/sales-console-worklist/item-directory`
6. `/desk/sales-console-worklist/customer-detail/<encoded-customer>`
7. `/desk/sales-console-worklist/customer-editor/<encoded-customer>`
8. `/desk/sales-console-report/sales-order-analysis`
9. `/desk/quotation/<quotation-name>`
10. `/desk/sales-order/<sales-order-name>`

For each route, confirm:

1. hard refresh stays on the correct business page
2. sidebar shows only one active item where an active item exists
3. Sales Console sidebar is present on all managed pages
4. Ctrl+K opens only Sales Console scoped search
5. row links do not open raw ERP lists when productized routes exist
6. Back buttons return to productized Sales Console pages
7. browser Back/Forward does not produce duplicate menus or blank states

## 10. Exit Criteria Status

| Exit criterion | Status | Notes |
| --- | --- | --- |
| Static route inventory completed | Pass | Worklist, report, sidebar, child helper, and document action code reviewed |
| Primary navigation productized | Pass | Sidebar/home/directory navigation uses Sales Console routes |
| Customer deep links refresh-safe by design | Pass pending browser | Customer name is encoded in route for detail/editor |
| Native fallback classified | Pass | Fallback is mostly governed through shared helper policy |
| No known high-value productized action leaks to raw ERP list | Pass pending browser | Connections list behavior should be manually verified |
| Sidebar active state correct across all managed routes | Pass pending browser | Customer detail/editor mapping hardened; reports intentionally have no active item in V1 |
| Browser route verification completed | Pending | Requires authenticated browser session |

## 11. SERA-1 Recommendation

Do not start the next workspace from Sales Console until SERA-1 browser verification is completed.

Recommended immediate next step:

1. verify the required browser route script
2. confirm customer detail/editor active state in browser
3. confirm Connections links do not open raw ERP lists where productized routes exist
4. then proceed to `SERA-2` Security, Permission, And Data Mutation Safety

This keeps route ownership enterprise-grade without turning SERA-1 into a broad redesign sprint.
