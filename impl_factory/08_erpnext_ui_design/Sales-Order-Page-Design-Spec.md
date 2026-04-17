# Sales Order Page Design Spec

Status: first-wave child-page design spec  
Scope: redesign direction for `Sales Order` as the primary post-console execution page  
Source authority: [Child-Page-Design-Framework.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Child-Page-Design-Framework.md), [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md)

## 1. Purpose

This document defines how `Sales Order` should be redesigned so it no longer feels like a generic ERP transaction form.

The page should become an execution-control surface for sales.

It should help the user answer:

1. what is happening with this order
2. what is blocked
3. what has been delivered
4. what has been billed
5. what action is needed next

## 2. Primary Page Identity

`Sales Order` is not mainly a pricing page and not mainly an accounting page.

Its primary purpose is:

1. execution control

This page should therefore emphasize:

1. commitment status
2. approval status
3. delivery progress
4. billing progress
5. customer-facing risk or follow-up relevance

## 3. Target Roles

Primary roles:

1. `Sales Person`
2. `Sales Manager`

Secondary role:

1. `Executive Approver`

## 4. Top Summary Band

The top summary band should show:

1. sales order ID
2. customer
3. order status
4. workflow state
5. owner / responsible sales user
6. delivery date
7. grand total
8. percent delivered
9. percent billed
10. urgency or blocker indicator

Purpose:

1. let the user understand the order without reading the full form

## 5. Primary Action Zone

The visible action set should depend on status and role.

Examples of primary actions:

1. submit
2. send for approval
3. approve
4. reject
5. open delivery documents
6. open linked sales invoices
7. create or open follow-up task

Rules:

1. routine next actions must be visible near the top
2. approval actions must be shown only to the appropriate role
3. downstream financial or logistics actions must not imply inappropriate authority

## 6. Linked Document Strip

The page should show a compact linked chain for:

1. source quotation if any
2. delivery note records
3. sales invoice records
4. return records if any

Purpose:

1. preserve the commercial chain
2. reduce menu hunting
3. support customer-facing response

## 7. Primary Working Section

This is the core section of the page.

It should focus on execution status.

Recommended content:

1. delivery progress summary
2. billing progress summary
3. pending fulfillment signal
4. due soon signal
5. blocked-by-approval signal where relevant

This section should make it clear whether the order is:

1. waiting approval
2. ready for fulfillment
3. partially delivered
4. delivered but not billed
5. operationally complete

## 8. Supporting Context Section

This section should contain:

1. latest customer-facing follow-up task
2. approval trigger explanation if approval is required
3. related return issue if any
4. customer communication note later if useful

This section should support action, not overwhelm the page.

## 9. Detailed Transaction Area

The detailed lower area may retain standard ERPNext sections such as:

1. items
2. taxes and charges
3. terms
4. shipping and address details
5. remarks

But this detailed area should be visually secondary to the execution summary above.

## 10. Role Behavior

### Sales Person

Should emphasize:

1. current execution status
2. delivery and billing visibility
3. follow-up relevance

Should not be overloaded with:

1. managerial review surfaces
2. finance-detail control

### Sales Manager

Should additionally see:

1. team ownership clarity
2. approval context
3. stronger blocker visibility
4. exception signals

### Executive Approver

Should see:

1. escalation context
2. approval reason
3. customer and order impact

The page should not become a routine work surface for this role.

## 11. Design Rules

### 11.1 Do Not Let The Page Become Too Dense

`Sales Order` should stay an execution page.

Do not turn it into:

1. a report page
2. a warehouse cockpit
3. a finance cockpit

### 11.2 Keep Customer Response Visible

Sales users often need to answer:

1. has it been delivered
2. has it been billed
3. is anything blocked
4. when is it due

The page should support those answers directly.

### 11.3 Preserve Role Safety

Users may see delivery and billing status without receiving:

1. warehouse authority
2. finance posting authority

## 12. Console Linkage

This page is a primary destination from:

1. `Open Orders`
2. `Sales Orders Pending Fulfillment`
3. `Orders Due Soon`
4. `Partially Delivered Orders`
5. `Orders Blocked By Approval`
6. `Customer Inquiry`

So its design must preserve context from those entry points.

## 13. Success Criteria

The redesign is successful if a user can open a `Sales Order` and understand within a few seconds:

1. whether it is approved
2. whether it is blocked
3. what has been delivered
4. what remains to bill
5. what they should do next

## 14. Implementation Note

Implementation should enhance the existing ERPNext page rather than replace the transaction engine.

Preferred approach:

1. improve page hierarchy
2. improve section order
3. add clearer status surfaces
4. add linked-document visibility
5. add role-safe action clarity
