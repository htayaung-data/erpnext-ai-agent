# Sales Console Validation Checkpoint

Status: post-seeding validation checkpoint for `Sales Console`  
Scope: confirm count correctness, destination correctness, and role correctness against the live Batch A-D scenario dataset

## 1. Validation Date

1. `2026-03-30`

## 2. Roles Validated

1. `Sales Manager`
2. `Sales User`
3. `Executive Approver`

Validated accounts:

1. `sale.manager@meet.com`
2. `sales.exec.ygn.01@meet.com`
3. `general.manager@meet.com`

## 3. Count Correctness

The following cards were validated by comparing the live card metric with the direct filtered list count produced by the same navigation target:

1. `Open Orders`
2. `Quotations Waiting For Action`
3. `Open Quotations Nearing Expiry`
4. `Sales Orders Pending Fulfillment`
5. `Customer Follow-Up Tasks`
6. `Orders Due Soon`
7. `Partially Delivered Orders`
8. `Invoices Outstanding`
9. `Sales Returns In Progress`
10. `Orders Blocked By Approval`
11. `Quotations Awaiting Approval`

Result:

1. all validated list-backed cards matched their target list counts for the tested roles

## 4. Destination Correctness

Validated:

1. work cards open filtered operational lists
2. lifecycle cards open filtered review lists
3. blocker cards open workflow-pending approval queues
4. customer inquiry related documents open exact linked records
5. report cards point to real installed reports on this site

Confirmed real reports:

1. `Sales Analytics`
2. `Sales Order Analysis`
3. `Quotation Trends`
4. `Lost Quotations`
5. `Payment Terms Status for Sales Order`
6. `Item-wise Sales History`
7. `Sales Order Trends`

## 5. Role Correctness

### Sales Manager

Confirmed:

1. approval and blocker section comes first
2. manager sees team-scope queues and tasks
3. manager report set is broader and review-oriented

### Sales User

Confirmed:

1. inquiry, work, and lifecycle sections are emphasized first
2. approvals remain visible but secondary
3. user scope is constrained to owned/actionable commercial work where supported

### Executive Approver

Confirmed:

1. approval review is primary
2. transaction-creation actions are hidden in the UI
3. reports remain available for executive review context

## 6. Special Interpretation Note

`Awaiting Approval` is intentionally different from most other cards:

1. the KPI shows a combined count of approval-pending quotations and sales orders
2. the click target opens the dominant approval queue for the current role
3. target count therefore may be lower than the KPI total by design

This is currently accepted behavior, not a counting defect.

## 7. Findings

### No blocking defects found

The validated card formulas and list-backed click targets are behaving correctly for the tested roles.

### Minor design note

1. `Awaiting Approval` may deserve a split or a richer drill-down later if users want direct separation between quotation approvals and sales-order approvals from the top KPI

## 8. Outcome

The `Sales Console` is validated enough to move to the next stage:

1. downstream page review
2. child-page design improvement
3. next workspace planning
