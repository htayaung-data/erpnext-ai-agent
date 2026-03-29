# Sales Console Card Definition Spec

Status: implementation-stage source of truth for visible sections, cards, inquiry functions, and formula direction in `Sales Console`  
Scope: business meaning, role-safe visibility, formula design, and click intent  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-UI-Layout-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-UI-Layout-Spec.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md)

## 1. Purpose

This document defines what every visible surface in `Sales Console` actually means.

It exists so the console is:

1. business-true
2. role-safe
3. formula-driven
4. customer-facing where needed
5. implementation-ready

## 2. Formula And Visibility Rules

All formulas and visible surfaces must follow these rules:

1. use real ERP data, not design placeholder counts
2. apply role scope before counting
3. apply ownership, assignment, branch, territory, and approval scope where supported
4. keep visibility separate from authority
5. prefer truthful filtered lists over invented analytics
6. if a card cannot be made operationally trustworthy, replace it or defer it

## 3. First-Wave Visible Structure

The first-wave visible structure is:

1. `Header And Summary`
2. `Quick Actions`
3. `Customer Inquiry`
4. `My Sales Work`
5. `Customer Lifecycle Visibility`
6. `Approvals / Blockers`
7. `Reports And Review`
8. `AI Assist`

## 4. Header And Summary

### 4.1 Awaiting Approval

Purpose:

1. show approval-relevant commercial documents waiting on manager or executive action

Primary users:

1. `Sales Manager`
2. `Executive Approver`

Meaning:

1. quotations or sales orders still in configured approval states within the current review scope

Formula direction:

1. `Quotation.workflow_state` in approval states
2. `Sales Order.workflow_state` in approval states
3. combine into one summary count only if the UI keeps the summary intentionally compact
4. if the UI needs document-type clarity, split it later into separate approval cards

Role behavior:

1. lower emphasis for `Sales Person`
2. primary for `Sales Manager`
3. primary for `Executive Approver`

### 4.2 Open Orders

Purpose:

1. give a simple count of active commercial commitments still in the execution pipeline

Primary users:

1. all sales roles

Meaning:

1. submitted sales orders not cancelled or closed and still requiring delivery and/or billing action

Formula direction:

1. `Sales Order.docstatus = 1`
2. exclude cancelled and closed
3. include active operational statuses
4. preserve role scope

## 5. Quick Actions

### 5.1 New Opportunity

Purpose:

1. create a qualified sales chance quickly

Primary users:

1. `Sales Person`
2. `Sales Manager`

### 5.2 New Quotation

Purpose:

1. create a formal commercial offer directly from the console

### 5.3 New Sales Order

Purpose:

1. create a confirmed operational order directly from the console

### 5.4 Open Customer

Purpose:

1. jump into customer context quickly

### 5.5 Open Item

Purpose:

1. jump into item lookup and selling context quickly

## 6. Customer Inquiry

This is a major console function, not only a single card.

### 6.1 Inquiry Entry

Purpose:

1. let sales users search with one clue and retrieve the related sales lifecycle

Accepted phase-1 entry types:

1. customer ID
2. customer name
3. quotation ID
4. sales order ID
5. sales invoice ID
6. delivery note ID

Accepted later if data quality supports it:

1. phone
2. partial keyword
3. broader date-driven lookup

### 6.2 Inquiry Result

Purpose:

1. show the related business chain in a single structured result

Expected result blocks:

1. `Primary Match`
2. `Customer Summary`
3. `Document Flow`
4. `Current Status`
5. `Exceptions / Blockers`
6. `Related Documents`

Default document flow sequence:

1. `Quotation`
2. `Sales Order`
3. `Delivery`
4. `Sales Invoice`
5. `Payment`
6. `Return`

Implementation rule:

1. if some steps do not exist for the transaction, show them as not used or not yet created
2. do not force every transaction into a full-chain assumption

### 6.3 Inquiry Trust Rule

The inquiry result is only valid if:

1. the matched document is real
2. the linked chain is document-traceable
3. the result states clearly when a step is absent versus unknown

## 7. My Sales Work

### 7.1 Quotations Waiting For Action

Purpose:

1. show quotations that still need sales-side movement

Meaning:

1. open quotations requiring follow-up, reply, revision, or conversion handling

Formula direction:

1. `Quotation.docstatus = 0 or 1` depending on workflow model
2. include sales-actionable statuses
3. exclude approval-blocked quotations counted elsewhere
4. exclude lost, ordered, cancelled, expired where not actionable

### 7.2 Open Quotations Nearing Expiry

Purpose:

1. prevent missed follow-up on quotations about to expire

Formula direction:

1. open quotation status
2. `valid_till` within the next 7 days in phase 1

### 7.3 Sales Orders Pending Fulfillment

Purpose:

1. show approved active sales orders still waiting for delivery or billing completion

Formula direction:

1. submitted `Sales Order`
2. not blocked by approval
3. not closed or cancelled
4. include partially delivered or partially billed orders

### 7.4 Customer Follow-Up Tasks

Purpose:

1. show live customer-facing follow-up obligations owned by sales

Primary source:

1. `ToDo`

Formula direction:

1. `ToDo.status = Open`
2. `allocated_to = current user` for staff
3. manager may see team scope later
4. `reference_type` in:
   - `Customer`
   - `Quotation`
   - `Sales Order`
   - `Opportunity`

### 7.5 Opportunities Closing Soon

Status:

1. approved for next-wave addition if data quality remains acceptable

Reason:

1. `Opportunity.expected_closing`, `status`, and `probability` already exist

## 8. Customer Lifecycle Visibility

This section is visibility-first, not authority-first.

### 8.1 Partially Delivered Orders

Purpose:

1. let sales answer customer delivery-progress questions quickly

Meaning:

1. submitted sales orders that are only partly delivered

Formula direction:

1. `Sales Order.docstatus = 1`
2. `per_delivered > 0`
3. `per_delivered < 100`

### 8.2 Invoices Outstanding

Purpose:

1. give sales users a customer-facing summary of orders or invoices still not settled

Meaning:

1. customer-facing billing/payment pending visibility, not finance control

Formula direction:

1. phase 1 may use `Sales Invoice.status` such as:
   - `Unpaid`
   - `Partly Paid`
   - `Overdue`
   - discounted unpaid variants
2. phase 1 should remain summary-safe and not expose finance posting controls

### 8.3 Sales Returns In Progress

Purpose:

1. let sales see active return situations that affect customer communication

Meaning:

1. return-related delivery or invoice documents still requiring follow-up

Formula direction:

1. `Sales Invoice.is_return = 1`
2. `Delivery Note.is_return = 1`
3. include only recent or active items relevant for customer-facing follow-up
4. exact phase-1 formula may remain conservative if cross-document settlement logic is complex

### 8.4 Delivered Not Yet Invoiced

Status:

1. optional replacement card

Reason:

1. may be more operationally useful than generic invoice-pending counts in some businesses

## 9. Approvals / Blockers

### 9.1 Orders Blocked By Approval

Purpose:

1. expose sales orders that cannot move forward due to configured approval workflow

Meaning:

1. `Sales Order.workflow_state` in blocked approval states

Formula direction:

1. use the live configured `Sales Order` workflow
2. include:
   - `Pending Sales Approval`
   - `Pending Executive Approval`

### 9.2 Quotations Awaiting Approval

Purpose:

1. expose quotations waiting on approval action rather than sales action

Formula direction:

1. use live configured quotation workflow states

### 9.3 Escalated Commercial Exceptions

Purpose:

1. show higher-risk or higher-value approval items escalated beyond routine manager handling

Formula direction:

1. use executive approval states from quotation and sales order workflow
2. if a combined card becomes confusing, split later by document type

## 10. Reports And Review

Only use real existing or high-quality review targets.

### 10.1 Sales Analytics

Purpose:

1. broad performance review

### 10.2 Item-wise Sales History

Purpose:

1. item-level commercial history

### 10.3 Quotation Trends

Purpose:

1. quotation pattern review and movement over time

### 10.4 Sales Order Analysis

Purpose:

1. deeper order review using a truthful existing report

### 10.5 Lost Quotations

Purpose:

1. commercial review of lost business and follow-up quality

### 10.6 Payment Terms Status for Sales Order

Purpose:

1. more relevant payment review surface than a fake customer-history report name

## 11. AI Assist

AI is a support layer, not a replacement for structured status visibility.

### 11.1 Customer Inquiry Summary

Purpose:

1. summarize inquiry result in plain language

### 11.2 Customer Brief

Purpose:

1. prepare the salesperson before a customer call or visit

### 11.3 Blocker Explanation

Purpose:

1. explain why a quotation or sales order is waiting or blocked

### 11.4 Next Best Action

Purpose:

1. suggest the next operational step after the user already has structured context

## 12. Cards And Functions Deferred From First Wave

### 12.1 Guided Today Worklist

Status:

1. strategically valuable but not first-wave required

Reason:

1. should follow after inquiry and lifecycle visibility are stable

### 12.2 Advanced Credit-Risk Flags

Status:

1. deferred

Reason:

1. exact sales-safe formula remains unsettled

### 12.3 Full Communication Timeline

Status:

1. deferred

Reason:

1. useful, but lower priority than inquiry and truthful status visibility

## 13. Final Card Rule

Every visible card or inquiry result block must answer:

1. why it exists
2. what it shows
3. whose scope it shows
4. whether it is visibility or authority
5. what happens when clicked
6. whether the data is operationally trustworthy

If it cannot answer those questions clearly, it should not remain in the console.
