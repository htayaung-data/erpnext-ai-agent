# Sales Console Seed Batch Plan

Status: execution-batch plan for seeded `Sales Console` scenario coverage  
Scope: convert the approved seed package into practical batches that can be created, reviewed, and loaded safely  
Source authority: [Sales-Console-Seed-Execution-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Execution-Spec.md), [Sales-Console-Seed-Import-Manifest.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Import-Manifest.md)

## 1. Purpose

This document defines how the seed package should be executed in controlled batches.

The goal is to avoid:

1. one giant import with hard-to-debug link failures
2. scenario records that look valid in isolation but do not connect properly
3. noisy reseeding if one stage fails

## 2. Batch Strategy

Use 4 batches:

1. `Batch A`: customers and quotations
2. `Batch B`: sales orders and delivery notes
3. `Batch C`: sales invoices and payment entries
4. `Batch D`: return documents and follow-up tasks

Do not start the next batch until the previous batch has been validated at the console level.

## 3. Batch A: Customers And Quotations

### Goal

Establish the reusable customer portfolio and make quotation approval scenarios live.

### Seed scope

1. 8 customers
2. 8 quotations

### Primary scenarios covered

1. `SC-01`
2. `SC-02`
3. partial support for `SC-13`

### Expected console effects

1. `Awaiting Approval` becomes live
2. `Quotations Waiting For Action` becomes meaningfully populated
3. `Customer Inquiry` works from customer and quotation entry points
4. `Sales Manager` and `Executive Approver` approval views show real pending quotations

### Validation checkpoint

Confirm:

1. 3 quotations are visible in `Pending Sales Approval`
2. 2 quotations are visible in `Pending Executive Approval`
3. inquiry by quotation ID works
4. manager and executive approval queues both show records

## 4. Batch B: Sales Orders And Delivery Notes

### Goal

Make work queue, due-soon, partial-delivery, and sales-order approval scenarios live.

### Seed scope

1. 10 sales orders
2. 5 delivery notes

### Primary scenarios covered

1. `SC-03`
2. `SC-04`
3. `SC-05`
4. `SC-11`

### Expected console effects

1. `Sales Orders Pending Fulfillment` becomes stronger and more varied
2. `Orders Due Soon` becomes demonstrable
3. `Partially Delivered Orders` becomes demonstrable
4. `Orders Blocked By Approval` becomes live from real records

### Validation checkpoint

Confirm:

1. 2 manager-pending sales orders are visible
2. 1 executive-pending sales order is visible
3. 2 partial-delivery chains are visible
4. due-soon orders appear with correct delivery horizon
5. inquiry by sales-order ID and delivery-note ID works

## 5. Batch C: Sales Invoices And Payment Entries

### Goal

Create a balanced billing and settlement layer on top of the seeded customer and order base.

### Seed scope

1. 11 sales invoices
2. 8 payment entries

### Primary scenarios covered

1. `SC-06`
2. `SC-07`
3. `SC-08`
4. `SC-12`

### Expected console effects

1. `Invoices Outstanding` becomes stronger and more balanced
2. inquiry supports:
   - overdue invoice
   - partly paid invoice
   - paid invoice
3. AI brief can be validated across multiple payment states

### Validation checkpoint

Confirm:

1. at least 4 seeded overdue invoices are visible
2. at least 2 seeded partly paid invoices are visible
3. at least 3 seeded paid invoices are visible with linked payment entries
4. inquiry by customer name returns mixed histories cleanly
5. AI brief stays truthful across paid, partly paid, and overdue cases

## 6. Batch D: Returns And Follow-Up Tasks

### Goal

Finish the return and follow-up parts of the console and complete the operational validation set.

### Seed scope

1. 3 return documents
2. 6 `ToDo` tasks

### Primary scenarios covered

1. `SC-09`
2. `SC-10`
3. `SC-13`

### Expected console effects

1. `Sales Returns In Progress` becomes more believable
2. return inquiry works from invoice and delivery anchors
3. `Customer Follow-Up Tasks` becomes meaningfully populated

### Validation checkpoint

Confirm:

1. 2 return invoices appear in inquiry and lifecycle logic
2. 1 delivery return appears in inquiry
3. 6 sales-linked open `ToDo` tasks are visible
4. `Sales User` and `Sales Manager` both see appropriate task allocations

## 7. Batch Dependency Rules

Do not violate these dependencies:

1. customers before quotations
2. quotations before linked sales orders where a full chain is required
3. sales orders before delivery notes
4. sales orders or delivery notes before linked sales invoices
5. sales invoices before payment entries
6. original invoices or deliveries before return documents

## 8. Practical Execution Standard

Each batch should be treated as accepted only when:

1. creation succeeds in ERP
2. relevant links survive
3. target console cards react as expected
4. inquiry works on at least 2 records from that batch

## 9. Recommended Review Rhythm

Use this rhythm:

1. prepare batch blueprint
2. load batch
3. validate console and inquiry
4. correct any link or status issue
5. only then move to the next batch

This keeps the dataset believable and the debugging surface manageable.
