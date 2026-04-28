# Sales Console Mini-Phase 1 Scope Audit

Status: implementation-aligned audit
Original date: 2026-04-17
Last updated: 2026-04-23
Source of truth: current `feature/erpnext-ui-design` code, especially `sales_console.js`, `sales_console/service.py`, and `sales_console/worklist.py`

## 1. Purpose

This note records the current Sales Console route surface after the worklist implementation and the Customers/Items sync.

It replaces the earlier assumption that most Sales Console cards still open native ERPNext lists.

## 2. Current Implementation Truth

### 2.1 Frozen child-document family

These remain accepted Sales Console child surfaces:

1. Sales Console home
2. Sales Order detail page
3. Quotation detail page
4. Delivery Note detail page
5. Sales Invoice detail page
6. New Quotation draft page
7. New Sales Order draft page

### 2.2 Productized worklist family

The shared worklist shell is now implemented through:

1. `page/sales_console_worklist/sales_console_worklist.js`
2. `public/js/runtime/list_page/list_page_shell.js`
3. `sales_console/worklist.py`

The route shape is:

1. `/desk/sales-console-worklist/<queue-key>`

The bare route `/desk/sales-console-worklist` is not a business page. It intentionally shows a guard state because the page requires a queue key.

### 2.3 Productized Customers and Items pages

Customers and Items no longer route to raw native lists from the Sales Console quick actions.

They now open:

1. `/desk/sales-console-worklist/customer-directory`
2. `/desk/sales-console-worklist/item-directory`

The Customers page includes:

1. sales-scope-aware customer filters
2. territory, customer group, and keyword controls
3. visible customer metrics
4. outstanding exposure signal
5. recent activity signal
6. row open actions to Customer records

The Items page includes:

1. sales-item filtering
2. item group, availability, and keyword controls
3. visible item metrics
4. in-stock and out-of-stock signals
5. stock posture by item
6. row open actions to Item records

## 3. Current Route Inventory

### 3.1 Quick actions

| Console surface | Runtime key | Current route target | Current state |
| --- | --- | --- | --- |
| New Quotation | `new_quotation` | new Quotation document | accepted draft flow |
| New Sales Order | `new_sales_order` | new Sales Order document | accepted draft flow |
| Customers | `open_customer` | `sales-console-worklist/customer-directory` | productized worklist |
| Items | `open_item` | `sales-console-worklist/item-directory` | productized worklist |

`new_opportunity` is no longer part of the current Sales Console quick-action contract.

### 3.2 Header insight cards

| Console surface | Runtime key | Current route target | Current state |
| --- | --- | --- | --- |
| Awaiting Approval | `awaiting_approval` | approval review target | productized review path |
| Open Orders | `open_orders` | `sales-console-worklist/open-orders` | productized worklist |

### 3.3 My Sales Work

| Console surface | Runtime key | Current route target | Current state |
| --- | --- | --- | --- |
| Sales Orders Pending Fulfillment | `sales_orders_pending_fulfillment` | `sales-console-worklist/sales-orders-pending-fulfillment` | productized worklist |
| Quotations Waiting For Action | `quotations_waiting_action` | `sales-console-worklist/quotations-waiting-action` | productized worklist |
| Active Quotations Nearing Expiry | `expiring_quotations` | `sales-console-worklist/expiring-quotations` | productized worklist |
| Customer Follow-Up Tasks | `customer_follow_up_tasks` | `sales-console-worklist/customer-follow-up-tasks` | productized worklist |

### 3.4 Customer lifecycle visibility

| Console surface | Runtime key | Current route target | Current state |
| --- | --- | --- | --- |
| Orders Due Soon | `orders_due_soon` | `sales-console-worklist/orders-due-soon` | productized worklist |
| Partially Delivered Orders | `partially_delivered_orders` | `sales-console-worklist/partially-delivered-orders` | productized worklist |
| Invoices Outstanding | `invoices_outstanding` | `sales-console-worklist/invoices-outstanding` | productized worklist |
| Recent Sales Returns | `sales_returns_in_progress` | `sales-console-worklist/sales-returns-in-progress` | productized worklist |

### 3.5 Approvals and blockers

| Console surface | Runtime key | Current route target | Current state |
| --- | --- | --- | --- |
| Orders Blocked By Approval | `orders_blocked_by_approval` | `sales-console-worklist/orders-blocked-by-approval` | productized review worklist |
| Quotations Awaiting Approval | `quotations_awaiting_approval` | `sales-console-worklist/quotations-awaiting-approval` | productized review worklist |

### 3.6 Reports and review

Reports are a separate Sales Console report-family stream.

Current report direction is:

1. use Collections Status instead of Payment Terms Status for Sales Order
2. treat report pages as a separate report runtime, not as worklists
3. keep report implementation and commit review separate from the Customers/Items worklist sync

## 4. Current Remaining Scope

The main native-list replacement problem is now closed for the Sales Console worklist family.

Remaining work should focus on:

1. live browser smoke coverage for every worklist key
2. final visual pass only where the shared list runtime reveals real usability issues
3. report-family validation and commit boundary
4. documentation alignment after each accepted code slice
5. eventual cleanup of misplaced ERP UI work from the AI Assistant branch after the ERP UI Design branch is fully validated

## 5. Immediate Next Move

The correct next move is not another native-list replacement pass.

The correct next move is:

1. keep Customers and Items in `feature/erpnext-ui-design`
2. run broader live Desk smoke tests for the worklist keys
3. decide and commit the separate report-family work
4. update freeze notes only after live validation confirms the page family behavior
