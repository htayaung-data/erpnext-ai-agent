# Sales Console Scenario Catalog

Status: planned scenario coverage for seeded sales-console validation  
Scope: practical, business-realistic scenario set for `Sales Console`, `Customer Inquiry`, lifecycle cards, approvals, reports, and click-through validation  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md), [Sales-Console-Customer-Inquiry-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Customer-Inquiry-Spec.md)

## 1. Purpose

This document defines the business scenarios that the seeded ERP dataset must support before `Sales Console` is treated as fully validated.

The goal is not to create dummy records.

The goal is to create a practical sales dataset that:

1. feels like a real operating environment
2. covers all important console cards
3. supports inquiry from multiple document entry points
4. supports role-based review for `Sales User`, `Sales Manager`, and `Executive Approver`
5. produces believable AI-assisted inquiry results

## 2. Scenario Design Principles

The scenario set must follow these rules:

1. do not create only one record per scenario unless the business case is inherently singular
2. use enough volume that list views, counts, and reports look believable
3. avoid excessive volume that makes the demo environment noisy or hard to control
4. reuse a small but realistic customer set across multiple chains
5. include both clean and exception cases
6. include both operational flow and customer-response flow

## 3. Recommended Scenario Volume

Use one seeded package with approximately:

1. 8 to 10 scenario-tagged customers
2. 8 quotations
3. 10 sales orders
4. 5 delivery notes
5. 11 sales invoices
6. 8 payment entries
7. 3 return documents
8. 6 follow-up `ToDo` tasks

This is large enough to validate the console properly and small enough to keep the demo environment understandable.

## 4. Core Scenario Set

### SC-01. Quotation waiting for manager approval

Purpose:

1. validate quotation approval queue
2. validate `Awaiting Approval`
3. validate manager approval path

Suggested volume:

1. 3 quotations

### SC-02. Quotation escalated to executive approval

Purpose:

1. validate executive escalation logic
2. validate `Executive Approver` view
3. validate approval-related inquiry wording

Suggested volume:

1. 2 quotations

### SC-03. Approved sales orders pending fulfillment

Purpose:

1. validate `Sales Orders Pending Fulfillment`
2. validate sales-order click-through
3. validate inquiry from `Sales Order` ID

Suggested volume:

1. 4 sales orders

### SC-04. Orders due soon

Purpose:

1. validate `Orders Due Soon`
2. validate date-sensitive lifecycle visibility
3. validate customer-response use for delivery commitment

Suggested volume:

1. 3 sales orders

Note:

1. this can overlap partially with `SC-03`

### SC-05. Partially delivered orders

Purpose:

1. validate `Partially Delivered Orders`
2. validate downstream customer-visibility behavior
3. validate inquiry from delivery-linked chains

Suggested volume:

1. 2 sales orders
2. 3 delivery notes

### SC-06. Overdue invoices requiring follow-up

Purpose:

1. validate `Invoices Outstanding`
2. validate inquiry from invoice ID
3. validate AI wording for customer payment follow-up

Suggested volume:

1. 4 invoices

### SC-07. Paid invoices with linked payment entries

Purpose:

1. validate settled-payment inquiry behavior
2. validate AI wording for paid cases
3. validate payment-chain visibility under current permission scope

Suggested volume:

1. 3 invoices
2. 3 payment entries

### SC-08. Partly paid invoices

Purpose:

1. validate partial-settlement inquiry
2. validate nuanced payment status
3. validate finance-follow-up wording

Suggested volume:

1. 2 invoices
2. 2 payment entries

### SC-09. Sales return and return follow-up

Purpose:

1. validate `Sales Returns In Progress`
2. validate return invoice inquiry
3. validate return exception messaging

Suggested volume:

1. 2 return invoices

### SC-10. Delivery return

Purpose:

1. validate return behavior when the anchor is a `Delivery Note`
2. validate return-stage rendering without invoice dependency

Suggested volume:

1. 1 delivery return

### SC-11. Order blocked by approval

Purpose:

1. validate `Orders Blocked By Approval`
2. validate `Sales Order` workflow-state logic
3. validate manager and executive sales-order approval review

Suggested volume:

1. 2 sales orders pending manager approval
2. 1 sales order pending executive approval

### SC-12. Customer with mixed sales history

Purpose:

1. validate inquiry by customer name
2. validate mixed chain output with multiple invoices and mixed payment states
3. validate related-document list quality

Suggested volume:

1. 2 customers with 3 to 5 linked commercial records each

### SC-13. Customer follow-up tasks

Purpose:

1. validate `Customer Follow-Up Tasks`
2. validate sales-facing operational workload
3. validate role filtering on `ToDo`

Suggested volume:

1. 6 open `ToDo` tasks

## 5. Scenario Coverage by Console Area

`Header And Summary`

1. `SC-01`
2. `SC-02`
3. `SC-03`
4. `SC-11`

`My Sales Work`

1. `SC-01`
2. `SC-03`
3. `SC-04`
4. `SC-13`

`Customer Lifecycle Visibility`

1. `SC-04`
2. `SC-05`
3. `SC-06`
4. `SC-08`
5. `SC-09`
6. `SC-10`

`Approvals / Blockers`

1. `SC-01`
2. `SC-02`
3. `SC-11`

`Customer Inquiry`

1. `SC-03`
2. `SC-05`
3. `SC-06`
4. `SC-07`
5. `SC-08`
6. `SC-09`
7. `SC-10`
8. `SC-12`

## 6. Minimum Acceptance

The seeded scenario package is acceptable only when:

1. each major console section has at least 2 meaningful live cases
2. each major approval level has live records to review
3. at least one clean and one exceptional inquiry case exists for invoice/payment
4. at least one return invoice and one delivery return exist
5. inquiry by customer name, invoice ID, sales order ID, and delivery note ID all work on live seeded data
