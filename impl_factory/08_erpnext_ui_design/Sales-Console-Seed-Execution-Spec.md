# Sales Console Seed Execution Spec

Status: import-ready execution spec for seeded `Sales Console` scenario coverage  
Scope: define the exact practical seed package, live site defaults, customer mix, and execution order before data loading  
Source authority: [Sales-Console-Scenario-Catalog.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Catalog.md), [Sales-Console-Scenario-Data-Requirements.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Data-Requirements.md), [Sales-Console-Current-Data-Gap-Assessment.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Current-Data-Gap-Assessment.md), [Sales-Console-Scenario-Seeding-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Seeding-Plan.md)

## 1. Purpose

This document turns the scenario-seeding strategy into a concrete package that can be loaded into the live demo ERP with minimal guesswork.

The aim is to create:

1. believable commercial activity
2. enough volume for cards, inquiry, and reports to feel real
3. a clean scenario-tagged layer that does not flood the site with random demo records

## 2. Live Site Defaults To Reuse

Use the existing site defaults instead of inventing new master data unless a real gap is found.

Confirmed live defaults:

1. `Company`: `Mingalar Mobile Distribution Co., Ltd.`
2. `Currency`: `MMK`
3. `Selling Price List`: `Standard Selling`
4. primary operational warehouse: `Yangon Main Warehouse - MMOB`
5. secondary operational warehouse: `Mandalay Warehouse - MMOB`
6. return warehouse: `Returns and Damaged - MMOB`

Recommended payment modes for seeded examples:

1. `Bank Transfer`
2. `KBZ Pay`
3. `Cash`

## 3. Reusable Seed Item Pool

Use existing live sellable items instead of seeding new items unless stock or pricing gaps make that impossible.

Recommended item pool:

1. `SPH-XMI-RN13-8/256`
2. `SPH-SAM-A15-6/128`
3. `SPH-OPP-A58-6/128`
4. `SPH-APP-IP14-128`
5. `ACC-CHR-XMI-33W`
6. `ACC-PWB-BAS-20K`
7. `MEM-MSD-SND-128`
8. `ACC-SP-GLS-RN13`

Practical selection rule:

1. keep 4 smartphone-heavy lines for higher-value approval cases
2. keep 4 accessory or memory lines for lower-value fast-flow cases
3. mix them across scenarios so inquiry results do not look repetitive

## 4. Scenario Customer Portfolio

Seed 8 scenario-tagged customers, not one per single transaction.

Recommended customer set:

1. `Maha Bandula Mobile Wholesale`
2. `Theingyi Telecom Distribution`
3. `Hledan Mobile Trade Center`
4. `Zegyo Mobile Supply House`
5. `Lanmadaw Digital Wholesale`
6. `Pazundaung Mobile Distribution`
7. `Thaketa Mobile Exchange`
8. `Chan Aye Mobile Trading Hub`

Recommended territory split:

1. 6 customers in `Yangon`
2. 2 customers in `Mandalay`

Recommended customer behavior:

1. approval customers reused across quotation and sales-order approval cases
2. fulfillment customers reused across due-soon and partial-delivery cases
3. billing customers reused across paid, partly paid, and overdue invoice cases
4. one return customer reused across return invoice and delivery-return cases
5. one mixed-history customer reused across multiple invoices and payment outcomes

## 5. Practical Seed Package

Use this seeded increment:

1. 8 customers
2. 8 quotations
3. 10 sales orders
4. 5 delivery notes
5. 11 sales invoices
6. 8 payment entries
7. 3 return documents
8. 6 `ToDo` tasks

This package is large enough to look like a real sales period and still small enough to audit manually.

## 6. Scenario Allocation By Customer

### `Maha Bandula Mobile Wholesale`

Use for:

1. 2 quotations pending manager approval
2. 1 sales order pending manager approval

### `Theingyi Telecom Distribution`

Use for:

1. 2 quotations pending executive approval
2. 1 quotation pending manager approval
3. 1 sales order pending executive approval
4. 1 sales order pending manager approval

### `Hledan Mobile Trade Center`

Use for:

1. 2 approved orders pending fulfillment
2. 1 order due soon
3. 1 partially delivered chain

### `Zegyo Mobile Supply House`

Use for:

1. 2 approved orders pending fulfillment
2. 2 orders due soon
3. 1 partially delivered chain

### `Lanmadaw Digital Wholesale`

Use for:

1. 2 overdue invoices
2. 1 partly paid invoice
3. 1 paid invoice

### `Pazundaung Mobile Distribution`

Use for:

1. 2 overdue invoices
2. 1 partly paid invoice
3. 2 paid invoices

### `Thaketa Mobile Exchange`

Use for:

1. 2 return invoices
2. 1 delivery return

### `Chan Aye Mobile Trading Hub`

Use for:

1. 1 approved sales order pending fulfillment
2. 1 paid invoice
3. 1 overdue invoice
4. 1 follow-up `ToDo`

## 7. Transaction Date Window

Use a controlled recent date window so the dataset looks current and the due-soon logic behaves properly.

Recommended seeded window:

1. `2026-03-10` to `2026-04-05`

Practical distribution:

1. quotations and order approvals in the earlier part of the window
2. due-soon orders inside the next 3-day horizon from the chosen validation date
3. overdue invoices dated at least 15 to 30 days before the validation date
4. paid and partly paid invoices spread across the same period

## 8. Approval Trigger Design For Seeded Transactions

Use the already-approved workflow policy instead of arbitrary values.

### Quotation approval examples

Create:

1. 3 manager-level quotations
2. 2 executive-level quotations

Use value and discount combinations that sit clearly in the intended threshold band.

### Sales Order approval examples

Create:

1. 2 manager-level pending orders
2. 1 executive-level pending order

Do not make all orders high-value. Keep enough ordinary approved orders so the console still feels commercially balanced.

## 9. Delivery And Billing Shape

To validate lifecycle cards properly:

1. create 5 non-cancelled delivery notes
2. make 2 sales orders partially delivered
3. keep at least 3 approved orders with no delivery yet
4. keep at least 3 invoices still overdue
5. keep at least 2 partly paid invoices
6. keep at least 3 fully paid invoices linked to real payment entries

## 10. Follow-Up Task Shape

Seed 6 `ToDo` tasks with sales-facing language, not generic admin wording.

Recommended task mix:

1. 2 quotation follow-up tasks
2. 2 overdue invoice follow-up tasks
3. 1 delivery commitment follow-up task
4. 1 return-status callback task

Recommended allocation:

1. 4 tasks to `Sales User`
2. 2 tasks to `Sales Manager`

## 11. Tagging Rules

All seeded records must remain traceable.

Use:

1. realistic customer names reserved for the seeded scenario portfolio
2. document `remarks` containing scenario code such as `SC-06` or `SC-11`
3. a consistent validation date window

Do not use artificial prefixes or fake-looking placeholder names on live-facing customer records.

## 12. Recommended Load Order

Load in this order:

1. confirm shared master records
2. create or confirm 8 customers
3. confirm seed item pool and stock availability
4. create quotations
5. create sales orders
6. create delivery notes
7. create sales invoices
8. create payment entries
9. create return documents
10. create `ToDo` tasks

## 13. Execution Checkpoints

After each stage, validate before continuing:

### Checkpoint A

1. customers created
2. inquiry finds them by customer name

### Checkpoint B

1. quotation approval cards become live
2. manager and executive approval queues show records

### Checkpoint C

1. order workload cards become meaningfully populated
2. due-soon and blocked-by-approval logic both respond

### Checkpoint D

1. lifecycle cards show:
   - partially delivered
   - invoices outstanding
   - returns in progress

### Checkpoint E

1. inquiry works from:
   - customer
   - quotation
   - sales order
   - invoice
   - delivery
2. AI brief works on:
   - paid invoice
   - overdue invoice
   - partial payment
   - return

## 14. Practical Acceptance Standard

The seed execution is successful only if:

1. `Sales User`, `Sales Manager`, and `Executive Approver` all see meaningful live records in their own console view
2. every major card in `Sales Console` is validated by more than one seeded record where the business case permits
3. inquiry is no longer limited by missing quotations or missing approval-state examples
4. the dataset looks like a small but believable operating period rather than a one-record test script
