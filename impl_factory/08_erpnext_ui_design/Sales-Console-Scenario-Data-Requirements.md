# Sales Console Scenario Data Requirements

Status: scenario-to-data mapping for seeded validation  
Scope: exact ERP data requirements for the approved `Sales Console` scenario set  
Source authority: [Sales-Console-Scenario-Catalog.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Catalog.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md), [Sales-Order-Approval-Policy-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Order-Approval-Policy-Spec.md), [Quotation-Approval-Policy-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Quotation-Approval-Policy-Spec.md)

## 1. Purpose

This document defines what data must exist in ERP for each scenario to be considered valid.

The purpose is to prevent vague “sample data” creation.

Each scenario must specify:

1. required DocTypes
2. required field values
3. required links between documents
4. required workflow states
5. expected console impact

## 2. Required Shared Master Data

Seed or confirm these shared records before transaction import:

1. 8 to 10 customers
2. 6 to 8 sellable items
3. 1 selling company
4. 1 or 2 warehouses used consistently
5. 3 role-mapped users:
   - `Sales User`
   - `Sales Manager`
   - `Executive Approver`
6. employees linked to those users where scope logic depends on employee mapping

## 3. Scenario Requirements

| Scenario | Required DocTypes | Critical Fields / States | Required Links | Expected Console Impact |
|---|---|---|---|---|
| `SC-01` quotation manager approval | `Quotation` | `workflow_state = Pending Sales Approval`; meaningful amount/discount | customer linked | `Awaiting Approval`, `Quotations Waiting For Action`, approval inquiry |
| `SC-02` quotation executive approval | `Quotation` | `workflow_state = Pending Executive Approval`; high amount or discount | customer linked | executive approval queue |
| `SC-03` order pending fulfillment | `Sales Order` | `docstatus = 1`, `workflow_state = Approved`, `status = To Deliver and Bill`, `per_delivered = 0`, `per_billed = 0` | customer linked | `Sales Orders Pending Fulfillment`, inquiry by order |
| `SC-04` order due soon | `Sales Order` | same as `SC-03` plus `delivery_date` within 3 days of test window | customer linked | `Orders Due Soon` |
| `SC-05` partially delivered order | `Sales Order`, `Delivery Note` | `Sales Order.per_delivered` between `0` and `100`; linked delivery not full chain complete | `Delivery Note Item.against_sales_order` | `Partially Delivered Orders` |
| `SC-06` overdue invoice | `Sales Invoice` | `status = Overdue`, `outstanding_amount > 0`, `is_return = 0` | customer linked; optional order link | `Invoices Outstanding`, inquiry by invoice |
| `SC-07` paid invoice | `Sales Invoice`, `Payment Entry`, `Payment Entry Reference` | invoice `status = Paid` or `outstanding_amount = 0`; payment `docstatus = 1` | payment references invoice | paid inquiry, AI brief for settled case |
| `SC-08` partly paid invoice | `Sales Invoice`, `Payment Entry`, `Payment Entry Reference` | invoice `status = Partly Paid`; partial allocation | payment references invoice | partial-settlement inquiry |
| `SC-09` return invoice | `Sales Invoice` | `is_return = 1`, `status = Return`, `return_against` set | linked original invoice if possible | `Sales Returns In Progress`, return inquiry |
| `SC-10` delivery return | `Delivery Note` | `is_return = 1`, `return_against` set | linked original delivery if possible | return inquiry by delivery note |
| `SC-11` order blocked by approval | `Sales Order` | `workflow_state = Pending Sales Approval` or `Pending Executive Approval`, `docstatus = 0 or 1` according to workflow behavior | customer linked | `Orders Blocked By Approval`, manager/executive review |
| `SC-12` mixed customer history | `Customer`, `Sales Order`, `Sales Invoice`, optional `Delivery Note`, optional `Payment Entry` | customer has both settled and unsettled records | related documents all point to same customer | inquiry by customer name |
| `SC-13` follow-up task | `ToDo` | `status != Closed`; assigned to sales users; reference to customer/opportunity/quotation/order where possible | user-linked task | `Customer Follow-Up Tasks` |

## 4. Link Integrity Rules

The following relationships must be preserved wherever possible:

1. `Quotation -> Sales Order` via previous-document fields
2. `Sales Order -> Delivery Note` via `against_sales_order`
3. `Sales Order / Delivery Note -> Sales Invoice`
4. `Sales Invoice -> Payment Entry` via `Payment Entry Reference`
5. return document -> original document via `return_against`

If seeded records are not linked, `Customer Inquiry` will show a partial chain. That is acceptable only where the scenario intentionally tests “direct invoice without upstream documents.”

## 5. Recommended Customer Mix

Use a small reusable customer set:

1. 2 customers focused on quotation/approval
2. 2 customers focused on order fulfillment
3. 2 customers focused on invoicing/payment
4. 1 customer focused on returns
5. 1 customer with mixed history across multiple invoices

This keeps the demo realistic without flooding the system.

## 6. Role Visibility Requirements

For seeded scenarios, verify that:

1. `Sales User` can see customer-facing lifecycle states
2. `Sales Manager` can see approval and review scenarios
3. `Executive Approver` can see escalated quotation and sales-order approval records
4. payment detail remains permission-aware while settlement status remains visible where intended

## 7. Validation Targets

Each seeded scenario must be validated against:

1. one visible console card or queue
2. one `Customer Inquiry` search path
3. one click-through target
4. one role-aware user view where relevant
