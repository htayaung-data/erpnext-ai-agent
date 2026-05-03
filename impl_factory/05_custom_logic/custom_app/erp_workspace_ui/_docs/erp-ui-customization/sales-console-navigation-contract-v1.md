# Sales Console Navigation Contract V1

Date: 2026-04-24
Status: Active implementation contract
Source of truth: `sales_console/service.py`, `sales_console/worklist.py`, `public/js/runtime/console/workspace_console_sidebar.js`

## Purpose

This note locks the Sales Console left-sidebar contract before more workspace pages are added.

The goal is to stop ad hoc menu growth and keep navigation aligned with enterprise sales-console behavior.

## Core Rule

The Sales Console sidebar should contain only stable destinations.

It should not repeat every operational queue or every home-page card.

Use this split:

1. Sidebar = stable destinations
2. Sales Console home = priorities, quick-create, and queue shortcuts
3. Directory pages = all visible records plus filters
4. Queue pages = filtered operational slices of the directory family
5. Form pages = contextual document actions, not broad menu expansion

## Sidebar V1

The left sidebar should show these destinations:

1. `Overview`
2. `Quotations`
3. `Sales Orders`
4. `Customers`
5. `Items`

Confirmed 2026-05-01: the first sidebar destination label is `Overview`, and it routes to `/desk/sales-console`. `Sales Console` remains the workspace/page identity and sidebar header context, not the left-sidebar item label.

Confirmed 2026-05-02: the standalone `Dashboard` page was removed before freeze because it overlapped with Sales Analytics and did not yet carry enough distinct enterprise dashboard value.

Confirmed 2026-05-03: the final route probe passed with this five-item sidebar for both Sales Manager and Sales User. No report or dashboard item is added to the sidebar in V1.

No top-level sidebar item is added for reports in V1.

Reason:

1. we already have report surfaces
2. we do not yet have a dedicated report home/index page
3. adding a single `Reports` item without a real destination would be misleading

## What Stays On Sales Console Home

The home page remains the place for:

1. `New Quotation`
2. `New Sales Order`
3. quick entry cards
4. approval and blocker cards
5. operational queue shortcuts
6. report shortcuts

These are not all repeated in the sidebar.

## Directory Versus Queue Rule

The Sales Console must support both:

1. directory pages
   - all visible Quotations
   - all visible Sales Orders
   - all visible Customers
   - all visible Items
2. queue pages
   - `Quotations Waiting Action`
   - `Quotations Awaiting Approval`
   - `Expiring Quotations`
   - `Open Orders`
   - `Orders Pending Fulfillment`
   - `Orders Due Soon`
   - `Orders Blocked by Approval`
   - other future operational slices

Queue pages are not replacements for directory pages.

## Form Page Rule

When a sales user opens a Sales Console-managed form route:

1. the native ERPNext form remains the system-of-record surface
2. the surrounding left navigation should stay the slim Sales Console sidebar
3. the page should not fall back to the full generic `Selling` workspace menu as the intended long-term UX
4. the sidebar header should continue to read `ERP Workspace UI / Sales Console`
5. the scoped Sales Console search should replace the native global ERP search

Managed form routes in V1:

1. `Quotation`
2. `Sales Order`
3. `Customer`
4. `Item`
5. `Delivery Note`
6. `Sales Invoice`

Active-state mapping:

1. `Quotation` highlights `Quotations`
2. `Sales Order`, `Delivery Note`, and `Sales Invoice` highlight `Sales Orders`
3. `Customer` highlights `Customers`
4. `Item` highlights `Items`

## Directory Page Filter Contract

`Quotations` and `Sales Orders` directory pages should use the same shared worklist shell already used by `Customers` and `Items`.

Required filter posture:

1. a `View` filter for operational slices
2. a `Status` filter
3. a `Keyword` filter
4. `Apply` and `Reset` actions above the table
5. `Apply`, `Reset`, and `Refresh` must refresh data in-place without a full Desk page reload
6. date-window filters should remain in the same row when desktop width allows

## Active-State Rule

Filtered queue pages should still highlight their parent directory destination in the sidebar.

Examples:

1. `Quotations Waiting Action` highlights `Quotations`
2. `Expiring Quotations` highlights `Quotations`
3. `Orders Due Soon` highlights `Sales Orders`
4. `Orders Blocked by Approval` highlights `Sales Orders`

This keeps the sidebar stable while still allowing focused operational pages.

## Implementation Scope For V1

This contract requires:

1. `Quotations` directory page
2. `Sales Orders` directory page
3. `Customers` directory page
4. `Items` directory page
5. `Customer Detail` and `Item Detail` productized routes
6. sidebar stable destinations only
7. sidebar active-key mapping from queue and detail routes to parent directory items

V1 report routes:

1. `/desk/sales-console-report/sales-analytics`
2. `/desk/sales-console-report/sales-order-analysis`
3. `/desk/sales-console-report/trend-analysis`
4. `/desk/sales-console-report/lost-quotations`
5. `/desk/sales-console-report/collections-status`
6. `/desk/sales-console-report/item-wise-sales-history`

Compatibility report routes:

1. `/desk/sales-console-report/quotation-trends`
2. `/desk/sales-console-report/payment-terms-status-sales-order`

## Deferred

These are intentionally deferred from V1:

1. dedicated Sales Console reports home page
2. additional sidebar expansion for every queue type
3. workspace-specific sidebar variants beyond the slim stable-destination model
4. standalone Sales Dashboard page until a full dashboard scope is justified
