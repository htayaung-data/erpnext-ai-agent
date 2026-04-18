# Sales Console Mini-Phase 1 Scope Audit

Status: working audit for remaining Sales Console scope  
Date: 2026-04-17  
Source of truth: runtime route inventory from sales_console.js and sales_console/service.py

## 1. Purpose

This note maps the actual remaining Sales Console ecosystem from live code.

It answers:

1. which console actions and cards are already routed
2. what each route currently opens
3. which surfaces are already frozen
4. which surfaces are still native and unfinished
5. the recommended implementation order for the remaining Sales Console scope

## 2. Frozen vs Remaining

### 2.1 Already frozen

These are already productized and should be treated as stable child surfaces for the Sales Console domain:

1. Sales Console home
2. Sales Order detail page
3. Quotation detail page
4. Delivery Note detail page
5. Sales Invoice detail page
6. New Quotation draft page
7. New Sales Order draft page

### 2.2 Still native or unfinished

These are still routed to native ERP list pages or query reports:

1. operational work lists behind console cards
2. approval / blocker review lists
3. shared record review entry lists such as Customer and Item
4. report destinations opened as native query reports
5. New Opportunity, which still opens the native document flow and is not yet part of the frozen child-page family

## 3. Actual route inventory

### 3.1 Quick actions

| Console surface | Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- | --- |
| New Opportunity | new_opportunity | new Opportunity document | full transaction | native / unfinished | defer until sales core list-review-report cluster is complete |
| New Quotation | new_quotation | new Quotation document | full transaction | frozen | keep |
| New Sales Order | new_sales_order | new Sales Order document | full transaction | frozen | keep |
| Open Customer | open_customer | List/Customer with sales-safe filters | shared record review list | native / unfinished | later shared-review slice |
| Open Item | open_item | List/Item with sales-item filters | shared record review list | native / unfinished | later shared-review slice |

### 3.2 Header insight cards

| Console surface | Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Awaiting Approval | awaiting_approval | dynamic target to blocked Sales Orders or Quotation approvals | review list | native / unfinished | absorb into approval-review slice |
| Open Orders | open_orders | List/Sales Order with active-order filters | operational list | native / unfinished | absorb into sales-order operational list archetype |

### 3.3 My Sales Work

| Console surface | Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Sales Orders Pending Fulfillment | sales_orders_pending_fulfillment | List/Sales Order with active non-pending workflow filters | operational list | native / unfinished | first cluster |
| Quotations Waiting For Action | quotations_waiting_action | List/Quotation with actionable draft/open filters | operational list | native / unfinished | first cluster |
| Active Quotations Nearing Expiry | expiring_quotations | List/Quotation with expiring-soon filters | operational list / exception variant | native / unfinished | build as filter variant of quotation operational list |
| Customer Follow-Up Tasks | customer_follow_up_tasks | List/ToDo with sales reference filters | operational list | native / unfinished | first cluster |

### 3.4 Customer lifecycle visibility

| Console surface | Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Orders Due Soon | orders_due_soon | List/Sales Order with due-soon filters | operational list / timing variant | native / unfinished | build as filter variant of sales-order operational list |
| Partially Delivered Orders | partially_delivered_orders | List/Sales Order with partial-delivery filters | operational list / fulfillment variant | native / unfinished | build as filter variant of sales-order operational list |
| Invoices Outstanding | invoices_outstanding | List/Sales Invoice with outstanding settlement filters | operational list | native / unfinished | first cluster |
| Recent Sales Returns | sales_returns_in_progress | List/Sales Invoice returns, fallback List/Delivery Note returns | operational list / exception variant | native / unfinished | first cluster, but after invoice list |

### 3.5 Approvals / blockers

| Console surface | Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- | --- |
| Orders Blocked By Approval | orders_blocked_by_approval | List/Sales Order in pending workflow states, fallback active orders | review / exception list | native / unfinished | second cluster |
| Quotations Awaiting Approval | quotations_awaiting_approval | List/Quotation in pending workflow states, fallback actionable quotations | review / exception list | native / unfinished | second cluster |

### 3.6 Reports and review

These are opened as native query reports today.

| Runtime key | Current route target | Type | Current state | Recommendation |
| --- | --- | --- | --- | --- |
| sales_analytics | query-report/Sales Analytics | report | native / unfinished | third cluster |
| sales_order_analysis | query-report/Sales Order Analysis | report | native / unfinished | third cluster |
| sales_order_trends | query-report/Sales Order Trends | report | native / unfinished | third cluster |
| quotation_trends | query-report/Quotation Trends | report | native / unfinished | third cluster |
| lost_quotations | query-report/Lost Quotations | report | native / unfinished | third cluster |
| payment_terms_status_sales_order | query-report/Payment Terms Status for Sales Order | report | native / unfinished | third cluster |
| item_wise_sales_history | query-report/Item-wise Sales History | report | native / unfinished | third cluster |

Role visibility is variant-driven, but the report destinations are still native query-report surfaces.

### 3.7 Inquiry

Inquiry is already productized inside Sales Console and should not be treated as a remaining list/review/report page.

It already supports:

1. direct lookup by customer or commercial document
2. document-chain resolution
3. open-record navigation from resolved inquiry results
4. AI assist on the resolved chain

So Inquiry is not part of the remaining page backlog.

## 4. Actual remaining scope classification

### 4.1 Operational list family

These are the highest-priority unfinished surfaces because they are daily execution views directly behind console cards.

1. quotation operational list
2. sales-order operational list
3. follow-up task list
4. invoice outstanding list
5. sales return list

### 4.2 Review / exception family

These are second priority.

1. orders blocked by approval
2. quotations awaiting approval
3. approval aggregate review from header insight
4. expiring quotation and return-heavy exception variants where a normal operational list is not enough

### 4.3 Report family

These remain important, but should come after the operational and review lists are stable.

### 4.4 Shared review entry lists

These are valuable but lower priority than the sales-owned operational lists.

1. customer entry list
2. item entry list
3. later opportunity creation / review alignment if Sales Console keeps that quick action

## 5. Recommended implementation sequence

### 5.1 Mini-Phase 2: operational list archetype

Create one reusable list-page standard before page-by-page implementation.

Define:

1. page header summary
2. saved-filter or filter-chip model
3. search and scope controls
4. row density and information hierarchy
5. status and aging cues
6. row actions and linked-document opening
7. loading, empty, restricted, and error states

### 5.2 Mini-Phase 3: first operational list cluster

Implement these first because they support the highest-frequency work behind the console:

1. Quotations Waiting For Action
2. Sales Orders Pending Fulfillment
3. Customer Follow-Up Tasks
4. Invoices Outstanding
5. Recent Sales Returns

Design rule:

1. Expiring Quotations should be a variant of the quotation operational list
2. Orders Due Soon and Partially Delivered Orders should be variants of the sales-order operational list

### 5.3 Mini-Phase 4: review / exception cluster

Implement after the operational lists exist:

1. Orders Blocked By Approval
2. Quotations Awaiting Approval
3. Awaiting Approval review entry from the header

These should explain:

1. what is blocked
2. why it is blocked
3. what role owns the next action
4. which linked document should be opened next

### 5.4 Mini-Phase 5: reports cluster

Implement report surfaces last in the Sales Console backlog.

Rule:

1. keep them table-first and filter-trust-first
2. do not start with decorative chart work
3. make them consistent with the list archetype where possible

### 5.5 Mini-Phase 6: final cross-surface validation

Only after list, review, and report surfaces are productized:

1. validate every console card route
2. capture final screenshots
3. check loading and landing behavior
4. check spacing and premium visual consistency
5. update freeze and deferred notes

## 6. Immediate next move

The correct next step is:

Mini-Phase 2: operational list archetype

because Mini-Phase 1 confirms that the remaining Sales Console work is primarily native-list replacement, not more child-document detail work.
