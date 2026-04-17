# Sales Console Seed Import Manifest

Status: import-ready document manifest for seeded `Sales Console` scenario coverage  
Scope: minimum live field set, naming series, child-table expectations, and link rules for each seeded doctype  
Source authority: [Sales-Console-Seed-Execution-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Execution-Spec.md), [Sales-Console-Scenario-Data-Requirements.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Data-Requirements.md)

## 1. Purpose

This document exists so the seed package can be prepared exactly against the live ERP structure.

It does not attempt to list every field on each doctype.

It lists:

1. the live naming series to use
2. the minimum fields required for controlled seeding
3. the child tables and links that must be preserved
4. the practical execution notes needed to keep document chains valid

## 2. Shared Runtime Defaults

Use these values unless a scenario explicitly needs something else:

1. `company`: `Mingalar Mobile Distribution Co., Ltd.`
2. `currency`: `MMK`
3. `conversion_rate`: `1`
4. `selling_price_list`: `Standard Selling`
5. `price_list_currency`: `MMK`
6. `plc_conversion_rate`: `1`
7. primary warehouse: `Yangon Main Warehouse - MMOB`
8. alternate warehouse: `Mandalay Warehouse - MMOB`
9. return warehouse: `Returns and Damaged - MMOB`

## 3. Customer

### Live naming pattern

1. series: `CUST-.YYYY.-`

### Minimum fields

1. `customer_name`
2. `customer_type`
3. `territory`
4. `mobile_no` if available on the site import path

### Practical defaults

1. `customer_type = Company`
2. `territory = Yangon` or `Mandalay`

### Notes

1. customer names should use the realistic scenario portfolio from the execution spec
2. one phone number per customer is enough for inquiry realism

## 4. Quotation

### Live naming pattern

1. use the live quotation series configured on this site

### Minimum fields

1. `naming_series`
2. `quotation_to`
3. `customer`
4. `transaction_date`
5. `order_type`
6. `company`
7. `currency`
8. `conversion_rate`
9. `selling_price_list`
10. `price_list_currency`
11. `plc_conversion_rate`
12. `items`

### Recommended values

1. `quotation_to = Customer`
2. `order_type = Sales`
3. include `valid_till`
4. use `additional_discount_percentage` and `discount_amount` only where needed for approval scenarios

### Child table

`items` should include at minimum:

1. `item_code`
2. `qty`
3. `uom`
4. `rate`
5. `warehouse` only if the site requires it at row level

### Scenario notes

1. `SC-01` and `SC-02` must be created with value bands that drive the intended quotation workflow state
2. remarks should carry scenario code

## 5. Sales Order

### Live naming pattern

1. use the live sales-order series configured on this site

### Minimum fields

1. `naming_series`
2. `customer`
3. `order_type`
4. `transaction_date`
5. `delivery_date`
6. `company`
7. `currency`
8. `conversion_rate`
9. `selling_price_list`
10. `price_list_currency`
11. `plc_conversion_rate`
12. `items`

### Recommended values

1. `order_type = Sales`
2. use `delivery_date` deliberately for due-soon cases
3. use header discount fields only where the approval scenario needs them

### Child table

`items` should include at minimum:

1. `item_code`
2. `qty`
3. `uom`
4. `rate`
5. `delivery_date`
6. `warehouse`

### Scenario notes

1. `SC-03`, `SC-04`, and `SC-05` can share ordinary approved orders
2. `SC-11` orders must land in pending approval states
3. keep ordinary open orders in the package so not everything is an exception

## 6. Delivery Note

### Live naming pattern

1. normal: `MAT-DN-.YYYY.-`
2. return: `MAT-DN-RET-.YYYY.-`

### Minimum fields

1. `naming_series`
2. `customer`
3. `posting_date`
4. `posting_time`
5. `company`
6. `currency`
7. `conversion_rate`
8. `selling_price_list`
9. `price_list_currency`
10. `plc_conversion_rate`
11. `items`

### Row-level requirements

`items` should preserve these links where applicable:

1. `against_sales_order`
2. `so_detail`
3. `item_code`
4. `qty`
5. `uom`
6. `warehouse`

### Return delivery requirements

For `SC-10`:

1. `is_return = 1`
2. `return_against` must point to the original delivery
3. use the return series
4. quantities should reflect a believable partial or full return

## 7. Sales Invoice

### Live naming pattern

1. normal: `ACC-SINV-.YYYY.-`
2. return: `ACC-SINV-RET-.YYYY.-`

### Minimum fields

1. `naming_series`
2. `customer`
3. `company`
4. `posting_date`
5. `due_date`
6. `currency`
7. `conversion_rate`
8. `selling_price_list`
9. `price_list_currency`
10. `plc_conversion_rate`
11. `items`

### Optional but important fields

1. `update_stock`
2. `set_warehouse`
3. `is_return`
4. `return_against`
5. `remarks`

### Row-level requirements

`items` should preserve upstream links where possible:

1. `sales_order`
2. `so_detail`
3. `delivery_note`
4. `dn_detail`
5. `item_code`
6. `qty`
7. `uom`
8. `rate`
9. `warehouse`

### Scenario notes

1. `SC-06` overdue invoices should have a due date clearly in the past
2. `SC-07` paid invoices should be settled by linked payment entries
3. `SC-08` partly paid invoices should retain outstanding balance
4. `SC-09` return invoices must use `is_return = 1` and `return_against`

## 8. Payment Entry

### Live naming pattern

1. `ACC-PAY-.YYYY.-`

### Minimum fields

1. `naming_series`
2. `payment_type`
3. `posting_date`
4. `company`
5. `party_type`
6. `party`
7. `paid_from`
8. `paid_to`
9. `paid_amount`
10. `received_amount`
11. `source_exchange_rate`
12. `target_exchange_rate`
13. `references`

### Practical scenario defaults

For customer receipt examples:

1. `payment_type = Receive`
2. `party_type = Customer`
3. use a realistic mode such as `Bank Transfer`, `KBZ Pay`, or `Cash`

### Child table

`references` should include:

1. `reference_doctype = Sales Invoice`
2. `reference_name`
3. `allocated_amount`

### Notes

1. exact `paid_from` and `paid_to` accounts must be resolved from live company/account setup at execution time
2. do not hardcode account names in the import package until they are confirmed from the site

## 9. ToDo

### Naming

1. standard auto-name is acceptable

### Minimum fields

1. `description`
2. `status`
3. `priority`
4. `date`
5. `allocated_to`
6. `reference_type`
7. `reference_name`
8. `assigned_by`

### Practical guidance

1. keep tasks linked to `Quotation`, `Sales Order`, or `Customer`
2. avoid generic wording like `follow up later`
3. use concrete descriptions such as:
   - call customer on overdue invoice
   - confirm delivery schedule
   - revise quotation discount

## 10. Item

No new item import is recommended unless execution testing finds a stock or pricing gap.

Use the existing item pool from the execution spec.

If a new item becomes unavoidable, the minimum fields are:

1. `item_code`
2. `item_group`
3. `stock_uom`
4. `is_sales_item = 1`
5. `is_stock_item = 1`

## 11. Link Rules That Must Survive Import

Preserve these links whenever the scenario expects a full chain:

1. `Quotation -> Sales Order`
2. `Sales Order -> Delivery Note`
3. `Sales Order / Delivery Note -> Sales Invoice`
4. `Sales Invoice -> Payment Entry`
5. `Return document -> original document`

If these links are skipped, the console will still work, but `Customer Inquiry` will show intentionally partial chains.

## 12. Submission And Workflow Handling

Practical execution rule:

1. create draft records first where workflow state matters
2. submit only where the scenario needs a submitted operational or financial document
3. do not bulk-submit records before workflow and link integrity are verified

Expected handling by doctype:

1. `Quotation`: leave in approval states where scenario needs pending review
2. `Sales Order`: keep some approved and some pending approval
3. `Delivery Note`: submit normal deliveries and returns
4. `Sales Invoice`: submit all billing scenarios
5. `Payment Entry`: submit all settlement scenarios

## 13. Execution Constraint

The seed package should be prepared so that it can be loaded in small checkpoints, not only as one giant import.

Recommended checkpoint batches:

1. customer + quotation batch
2. sales-order + delivery batch
3. invoice + payment batch
4. return + task batch
