# Sales Console Scenario Seeding Plan

Status: practical seeding plan for live scenario coverage  
Scope: add only the missing business data needed to validate `Sales Console` end to end  
Source authority: [Sales-Console-Scenario-Catalog.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Catalog.md), [Sales-Console-Scenario-Data-Requirements.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Data-Requirements.md), [Sales-Console-Current-Data-Gap-Assessment.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Current-Data-Gap-Assessment.md)

## 1. Purpose

This document defines the practical seeding approach for `Sales Console`.

The objective is not to fabricate a fake dataset.

The objective is to add only the missing scenario coverage so that:

1. the console behaves like a real operating workspace
2. each major card can be validated on live records
3. inquiry can be tested from multiple entry points
4. approval, fulfillment, payment, and return cases all exist in usable quantities

## 2. Seeding Philosophy

Use a gap-only seed strategy:

1. keep existing invoice and payment history
2. seed missing quotation and approval scenarios
3. seed missing normal delivery progression
4. seed missing partial-delivery cases
5. seed missing follow-up-task density
6. seed a few additional return examples, not a large return archive

## 3. Recommended Seed Package

Recommended new seeded volume:

1. 8 scenario-tagged customers
2. 8 quotations
3. 10 sales orders
4. 5 delivery notes
5. 11 sales invoices
6. 8 payment entries
7. 3 return documents
8. 6 sales-linked `ToDo` tasks

Practical note:

1. this is the seeded increment only
2. it is designed to sit on top of the existing live dataset

## 4. Customer Allocation Model

Use 8 seeded customers grouped as follows:

1. 2 approval customers
2. 2 fulfillment customers
3. 2 invoicing and payment customers
4. 1 return customer
5. 1 mixed-history customer

This avoids a flat one-customer-per-scenario model and makes inquiry more realistic.

## 5. Recommended Scenario Allocation

### Approval group

Seed:

1. 3 quotations pending manager approval
2. 2 quotations pending executive approval
3. 2 sales orders pending manager approval
4. 1 sales order pending executive approval

### Fulfillment group

Seed:

1. 4 approved sales orders pending fulfillment
2. 3 orders due soon
3. 2 partially delivered orders
4. 3 delivery notes linked to those orders

### Invoicing and payment group

Seed:

1. 3 paid invoices with payment entries
2. 2 partly paid invoices with payment entries
3. 4 overdue invoices
4. 3 payment entries for paid invoices
5. 2 payment entries for partly paid invoices

### Return group

Seed:

1. 2 return invoices
2. 1 delivery return
3. 1 additional payment or credit-related settlement record only if needed for realism

### Follow-up group

Seed:

1. 6 open sales-linked `ToDo` tasks

## 6. Tagging and Identification Rules

All seeded records should be traceable.

Use one or more of these:

1. realistic seeded customer names reserved for scenario coverage
2. remarks field with scenario code
3. custom note field if already available
4. consistent transaction date window reserved for scenario records

Do not seed records that are indistinguishable from organic demo data.

## 7. Import Order

Seed in this order:

1. customers
2. items if any are missing
3. quotations
4. sales orders
5. delivery notes
6. sales invoices
7. payment entries
8. return documents
9. `ToDo` tasks

This preserves document-link integrity.

## 8. Validation After Import

After seeding, validate in this order:

1. card formulas
2. `Customer Inquiry`
3. AI brief behavior
4. card click-through targets
5. child-page usefulness for:
   - `Quotation`
   - `Sales Order`
   - `Sales Invoice`
   - approval review pages

## 9. Acceptance Standard

The seed package is acceptable only if:

1. `Awaiting Approval` becomes live on real seeded records
2. `Orders Blocked By Approval` becomes live on real seeded records
3. `Customer Follow-Up Tasks` becomes meaningfully populated
4. `Orders Due Soon` and `Partially Delivered Orders` both show real cases
5. inquiry works for:
   - customer name
   - quotation ID
   - sales order ID
   - invoice ID
   - delivery note ID
6. return invoice and delivery return are both demonstrable

## 10. Recommended Next Execution Step

Do not import immediately from intuition.

Next do this:

1. confirm the seeded customer list and scenario codes
2. prepare the transaction package in exact ERP import order
3. load to a controlled demo environment
4. validate formulas and click-through behavior
5. only then decide whether child-page redesign is needed before the next workspace
