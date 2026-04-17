# Sales Console Current Data Gap Assessment

Status: live ERP data assessment before scenario seeding  
Scope: compare current site data against the required scenario set for `Sales Console` validation  
Assessment date: 2026-03-29  
Source authority: [Sales-Console-Scenario-Catalog.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Catalog.md), [Sales-Console-Scenario-Data-Requirements.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Data-Requirements.md)

## 1. Live Data Snapshot

Current live counts observed on the site:

1. `Customer`: 65
2. `Quotation`: 0
3. `Sales Order`: 12
4. `Delivery Note`: 14
5. `Sales Invoice`: 185
6. `Payment Entry`: 152
7. `ToDo`: 4

Observed status shape:

1. all 12 `Sales Order` records are `Approved` and `To Deliver and Bill`
2. `Delivery Note` records are all `Cancelled`
3. `Sales Invoice` records are heavily weighted toward `Overdue`
4. `Sales Invoice` returns exist, but only 2 were observed
5. `Quotation` is entirely absent on the current site
6. open `ToDo` records exist, but the sampled records are not strongly sales-linked yet

## 2. Practical Reading of Current Data

The current ERP already supports meaningful validation for:

1. open sales-order workload
2. invoice follow-up and outstanding exposure
3. paid invoice inquiry
4. partial-payment inquiry
5. return invoice inquiry
6. customer-name inquiry with mixed history

The current ERP does not yet support strong validation for:

1. quotation queues
2. quotation approval review
3. delivery-progress scenarios that are not cancelled
4. rich follow-up task scenarios
5. blocked `Sales Order` approval cases with live records

## 3. Scenario Coverage Assessment

| Scenario | Current Coverage | Practical Judgment |
|---|---|---|
| `SC-01` quotation manager approval | missing | no live quotations exist |
| `SC-02` quotation executive approval | missing | no live quotations exist |
| `SC-03` order pending fulfillment | covered | current site already has 12 approved open orders |
| `SC-04` order due soon | weak | delivery dates exist, but current dataset is narrow and static |
| `SC-05` partially delivered order | weak | delivery-note data is dominated by cancelled records |
| `SC-06` overdue invoice | covered | strong live coverage already exists |
| `SC-07` paid invoice with payment | covered | live examples exist and inquiry already works |
| `SC-08` partly paid invoice | covered | live examples exist |
| `SC-09` return invoice | partially covered | return invoices exist, but only a small number |
| `SC-10` delivery return | partially covered | one delivery return exists, not enough for broader validation |
| `SC-11` order blocked by approval | missing as live records | workflow exists, but live approval-state examples are not yet present |
| `SC-12` mixed customer history | covered | current site has customers with mixed invoice histories |
| `SC-13` follow-up task | weak | open `ToDo` exists, but scenario density is too low |

## 4. Main Gaps

The most important current gaps are:

1. no quotation data at all
2. no live quotation approval examples
3. no seeded sales-order approval examples in pending states
4. delivery activity is too cancellation-heavy to validate normal fulfillment well
5. sales follow-up tasks are too few and too weakly tied to sales flow
6. return coverage exists but is too thin for role-based scenario walkthroughs

## 5. What Should Not Be Re-Seeded

The following areas already have enough live data and should not be bulk-seeded again unless a very specific gap remains:

1. overdue invoices
2. paid invoices
3. partly paid invoices
4. payment entries in general
5. mixed-history customer invoice inquiry

## 6. What Must Be Seeded

The following areas should be seeded deliberately:

1. quotations
2. quotation approval records
3. sales-order approval-blocker records
4. normal non-cancelled delivery progression
5. partial-delivery chains
6. richer return examples
7. sales-linked follow-up tasks

## 7. Practical Conclusion

The current site is not empty.  
It already contains strong invoice and payment behavior.

However, it is not balanced enough to validate the whole `Sales Console` properly.

The correct next move is not full re-seeding.

The correct next move is:

1. keep the strong current invoice/payment dataset
2. seed the missing quotation, approval, delivery, and task scenarios
3. validate console formulas and click-through targets against the combined live plus seeded environment
