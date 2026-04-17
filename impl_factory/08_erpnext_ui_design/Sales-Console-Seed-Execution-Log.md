# Sales Console Seed Execution Log

Status: live execution log for seeded `Sales Console` scenario coverage  
Scope: track what has actually been loaded into ERP, by batch, so planning and runtime do not drift apart

## Batch A

Execution date:

1. `2026-03-30`

Result:

1. completed successfully

### Customers created

1. `Maha Bandula Mobile Wholesale`
2. `Theingyi Telecom Distribution`
3. `Hledan Mobile Trade Center`
4. `Zegyo Mobile Supply House`
5. `Lanmadaw Digital Wholesale`
6. `Pazundaung Mobile Distribution`
7. `Thaketa Mobile Exchange`
8. `Chan Aye Mobile Trading Hub`

### Quotations created

1. `SAL-QTN-2026-00001`
2. `SAL-QTN-2026-00002`
3. `SAL-QTN-2026-00003`
4. `SAL-QTN-2026-00004`
5. `SAL-QTN-2026-00005`
6. `SAL-QTN-2026-00006`
7. `SAL-QTN-2026-00007`
8. `SAL-QTN-2026-00008`

### Quotation workflow distribution

1. `Pending Sales Approval`
   - `SAL-QTN-2026-00001`
   - `SAL-QTN-2026-00002`
   - `SAL-QTN-2026-00003`
2. `Pending Executive Approval`
   - `SAL-QTN-2026-00004`
   - `SAL-QTN-2026-00005`
3. `Draft`
   - `SAL-QTN-2026-00006`
   - `SAL-QTN-2026-00007`
   - `SAL-QTN-2026-00008`

### Practical validation outcome

Batch A now gives live support for:

1. quotation approval visibility
2. manager approval queue
3. executive approval queue
4. customer inquiry by seeded customer and quotation
5. draft/actionable quotation coverage

### Notes

1. live quotation naming series confirmed as `SAL-QTN-.YYYY.-`
2. quotation row payload requires `conversion_factor`
3. quotation lookup is more reliable on `customer_name` than `party_name` for this site shape

## Next Batch

Next target:

1. `Batch B`
2. sales orders and delivery notes

## Batch B

Execution date:

1. `2026-03-30`

Result:

1. completed successfully

### Sales Orders created

1. `SAL-ORD-2026-00015`
2. `SAL-ORD-2026-00016`
3. `SAL-ORD-2026-00017`
4. `SAL-ORD-2026-00018`
5. `SAL-ORD-2026-00019`
6. `SAL-ORD-2026-00020`
7. `SAL-ORD-2026-00021`
8. `SAL-ORD-2026-00022`
9. `SAL-ORD-2026-00023`
10. `SAL-ORD-2026-00024`

### Sales Order state distribution

1. `Pending Sales Approval`
   - `SAL-ORD-2026-00015`
   - `SAL-ORD-2026-00016`
2. `Pending Executive Approval`
   - `SAL-ORD-2026-00017`
3. `Approved`
   - `SAL-ORD-2026-00018`
   - `SAL-ORD-2026-00019`
   - `SAL-ORD-2026-00020`
   - `SAL-ORD-2026-00021`
   - `SAL-ORD-2026-00022`
   - `SAL-ORD-2026-00023`
   - `SAL-ORD-2026-00024`

### Delivery Notes created and submitted

1. `MAT-DN-2026-00009`
2. `MAT-DN-2026-00010`
3. `MAT-DN-2026-00011`
4. `MAT-DN-2026-00012`
5. `MAT-DN-2026-00013`

### Practical lifecycle outcome

Batch B now gives live support for:

1. `Orders Blocked By Approval`
2. `Orders Due Soon`
3. `Partially Delivered Orders`
4. customer inquiry by sales-order ID
5. customer inquiry by delivery-note ID

### Verified order delivery shape

1. `SAL-ORD-2026-00021`
   - `per_delivered = 60`
2. `SAL-ORD-2026-00022`
   - `per_delivered = 50`
3. `SAL-ORD-2026-00018`
   - fully delivered, still `To Bill`
4. `SAL-ORD-2026-00024`
   - fully delivered, still `To Bill`
5. `SAL-ORD-2026-00019`
   - due soon and not yet delivered
6. `SAL-ORD-2026-00020`
   - due soon and not yet delivered
7. `SAL-ORD-2026-00023`
   - due soon and not yet delivered

### Notes

1. live sales-order naming series confirmed as `SAL-ORD-.YYYY.-`
2. delivery note row payload validated cleanly with:
   - `against_sales_order`
   - `so_detail`
   - `conversion_factor`
3. current site stock levels in Yangon and Mandalay were sufficient for the seeded Batch B quantities
4. post-seed scope alignment completed on `2026-03-30`
   - seeded `Quotation` and `Sales Order` records were reassigned from `Administrator` to real sales users so the role-aware Sales Console cards would reflect live team ownership correctly
   - seeded ownership was distributed across:
     - `sales.exec.ygn.01@meet.com`
     - `sales.exec.ygn.02@meet.com`
     - `sales.exec.mdy.01@meet.com`
     - `key.account.mdy.01@meet.com`
   - manager and sales-executive console counts now validate against live seeded Batch A and Batch B data

## Next Batch

Next target:

1. `Batch C`
2. sales invoices and payment entries

## Batch C

Execution date:

1. `2026-03-30`

Result:

1. completed successfully

### Sales Invoices created

1. `ACC-SINV-2026-00185`
2. `ACC-SINV-2026-00186`
3. `ACC-SINV-2026-00187`
4. `ACC-SINV-2026-00188`
5. `ACC-SINV-2026-00189`
6. `ACC-SINV-2026-00190`
7. `ACC-SINV-2026-00191`
8. `ACC-SINV-2026-00192`
9. `ACC-SINV-2026-00193`
10. `ACC-SINV-2026-00194`
11. `ACC-SINV-2026-00195`

### Payment Entries created

1. `ACC-PAY-2026-00153`
2. `ACC-PAY-2026-00154`
3. `ACC-PAY-2026-00155`
4. `ACC-PAY-2026-00156`
5. `ACC-PAY-2026-00157`
6. `ACC-PAY-2026-00158`
7. `ACC-PAY-2026-00159`
8. `ACC-PAY-2026-00160`

### Invoice settlement distribution

1. `Overdue`
   - `ACC-SINV-2026-00185`
   - `ACC-SINV-2026-00186`
   - `ACC-SINV-2026-00187`
   - `ACC-SINV-2026-00188`
   - `ACC-SINV-2026-00189`
2. `Paid`
   - `ACC-SINV-2026-00190`
   - `ACC-SINV-2026-00191`
   - `ACC-SINV-2026-00192`
   - `ACC-SINV-2026-00195`
3. `Partly Paid`
   - `ACC-SINV-2026-00193`
   - `ACC-SINV-2026-00194`

### Practical billing outcome

Batch C now gives live support for:

1. `Invoices Outstanding` with meaningful overdue and partly paid scenarios
2. customer inquiry by invoice ID across overdue, paid, partly paid, and mixed-history cases
3. payment-settlement visibility without exposing finance records outside current read scope
4. AI-generated customer briefs for billing follow-up and settlement questions

### Notes

1. this site required overdue demo invoices to be created with current posting date first, then adjusted to past `due_date` and `Overdue` status after submit
2. payment entries were created against submitted invoices using the site’s live receivable and bank/cash accounts
3. seeded invoice ownership was aligned to real sales users so role-aware console counts and inquiry results stay consistent with team scope

## Next Batch

Next target:

1. `Batch D`
2. returns and follow-up tasks

## Batch D

Execution date:

1. `2026-03-30`

Result:

1. completed successfully

### Support chain created for `Thaketa Mobile Exchange`

#### Sales Orders

1. `SAL-ORD-2026-00025`
2. `SAL-ORD-2026-00026`

#### Delivery Notes

1. `MAT-DN-2026-00014`
2. `MAT-DN-2026-00015`

#### Sales Invoices

1. `ACC-SINV-2026-00196`
2. `ACC-SINV-2026-00197`

#### Payment Entries

1. `ACC-PAY-2026-00161`
2. `ACC-PAY-2026-00162`

### Return documents created

1. `ACC-SINV-2026-00198`
2. `ACC-SINV-2026-00199`
3. `MAT-DN-2026-00016`

### Follow-up tasks created

1. `uh4rnrbinp`
2. `uh56bqcis1`
3. `uh5d8qrpqq`
4. `uh51c02rkg`
5. `uh68t6jurf`
6. `uh6vcdgtkh`

### Practical validation outcome

Batch D now gives live support for:

1. `Sales Returns In Progress`
2. return inquiry by return-invoice ID
3. return inquiry by delivery-return ID
4. return inquiry by customer anchor
5. `Customer Follow-Up Tasks` through sales-linked `ToDo`
6. manager and sales-user task visibility against the seeded follow-up set

### Live console validation snapshot

1. `sale.manager@meet.com`
   - `customer_follow_up_tasks = 6`
   - `sales_returns_in_progress = 2`
2. `sales.exec.ygn.01@meet.com`
   - `customer_follow_up_tasks = 3`
   - `sales_returns_in_progress = 2`
3. `sales.exec.ygn.02@meet.com`
   - `customer_follow_up_tasks = 1`
   - `sales_returns_in_progress = 2`

### Notes

1. Batch D used fresh seeded support chains for `Thaketa Mobile Exchange` instead of reusing older live returns, so the demo remains traceable and role-consistent
2. `Customer Follow-Up Tasks` logic was widened to include `Sales Invoice` and `Delivery Note` references, which was necessary to support realistic overdue and return callback tasks
3. return inquiries now validate cleanly on:
   - `ACC-SINV-2026-00198`
   - `ACC-SINV-2026-00199`
   - `MAT-DN-2026-00016`
   - `Thaketa Mobile Exchange`
