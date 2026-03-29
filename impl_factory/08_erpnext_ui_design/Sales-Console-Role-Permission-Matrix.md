# Sales Console Role Permission Matrix

Status: design and implementation authority for role behavior inside `Sales Console`  
Scope: sales roles, authority boundaries, visibility boundaries, workspace emphasis, and downstream status access  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md), [ERP Governance and Operating Architecture.pdf](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/Raw%20Base%20Reference%20files/ERP%20Governance%20and%20Operating%20Architecture.pdf), [Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/Raw%20Base%20Reference%20files/Mingalar_ERP_RoleSlot_Permission_Workflow_Pack.xlsx)

## 1. Purpose

This document defines what each role should be able to:

1. do
2. see
3. approve
4. review
5. not control

inside the `Sales Console`.

This document is especially important because sales is treated as the customer-facing focal role.

## 2. Normalized Role Set

The normalized role set for `Sales Console` is:

1. `Sales Person`
2. `Key Account Sales`
3. `Sales Manager`
4. `Executive Approver`

## 3. Core Role Principle

The console must distinguish clearly between:

1. visibility
2. authority

`Sales Person` should often see more than they control.

That means the console should allow broad customer-facing status visibility without accidentally giving warehouse, finance, or executive authority to sales.

## 4. Role Intent

### 4.1 Sales Person

Purpose:

1. handle daily selling work
2. act as focal communication point for customers
3. create and follow quotations and routine sales orders
4. answer customer questions using truthful lifecycle visibility

### 4.2 Key Account Sales

Purpose:

1. perform the same broad commercial role as `Sales Person`
2. handle assigned strategic or wholesale accounts
3. operate with wider account visibility where business rules allow

### 4.3 Sales Manager

Purpose:

1. supervise the team
2. approve routine exception cases
3. review blockers and escalations
4. manage sales discipline and queue quality

### 4.4 Executive Approver

Purpose:

1. handle escalated commercial cases
2. review high-threshold exception approvals
3. review without being a routine daily sales operator

## 5. Transaction Authority By Role

### 5.1 Sales Person

Allowed:

1. create and edit `Opportunity`
2. create and edit `Quotation`
3. submit routine `Quotation`
4. create and edit `Sales Order`
5. submit routine `Sales Order`
6. read `Customer`
7. read `Item`

Not allowed:

1. approve exception `Quotation`
2. approve exception `Sales Order`
3. perform finance posting
4. perform warehouse posting as a policy default
5. edit customer master as a policy default

### 5.2 Key Account Sales

Allowed:

1. same transaction pattern as `Sales Person`
2. broader account-scope selling visibility where configured

Not allowed:

1. quotation approval
2. sales-order approval
3. customer master editing by default

### 5.3 Sales Manager

Allowed:

1. team-wide quotation review
2. routine exception quotation approval
3. team-wide sales-order review
4. routine exception sales-order approval
5. escalation to executive approval
6. queue and blocker review

Not allowed by default:

1. finance-only release authority
2. broad accounting posting
3. warehouse transaction ownership

### 5.4 Executive Approver

Allowed:

1. approve escalated quotation exceptions
2. approve escalated sales-order exceptions
3. review cross-document exception context

Not allowed by default:

1. routine new transaction creation from this console
2. routine daily selling operations

## 6. Downstream Visibility By Role

This section is the most important design correction.

### 6.1 Sales Person Visibility

`Sales Person` should be able to see:

1. quotation status
2. sales-order status
3. delivery progress
4. invoice status
5. payment summary status
6. return status

Reason:

1. the customer contacts sales first
2. sales needs to answer status questions quickly

But `Sales Person` should not automatically gain:

1. delivery-note operational ownership
2. invoice posting ownership
3. payment-entry posting ownership
4. refund or credit-note authority

### 6.2 Sales Manager Visibility

`Sales Manager` should see:

1. all `Sales Person` visibility
2. team-level queue visibility
3. approval and escalation context
4. return issues requiring management review

### 6.3 Executive Approver Visibility

`Executive Approver` should see:

1. escalated quotations and sales orders
2. relevant delivery, invoice, payment, or return context when needed for decision-making

## 7. Customer Inquiry Visibility Rule

All three roles may use `Customer Inquiry`, but the result must respect role scope.

### 7.1 Sales Person

Should be able to search and view:

1. own customers
2. assigned or reachable commercial documents
3. related downstream status needed for customer communication

### 7.2 Sales Manager

Should be able to search and view:

1. team-related commercial documents
2. broader queue and approval context

### 7.3 Executive Approver

Should be able to search and view:

1. escalated commercial chains
2. high-level context for approval decisions

## 8. Workspace Emphasis By Role

### 8.1 Sales Person

Primary sections:

1. `Quick Actions`
2. `Customer Inquiry`
3. `My Sales Work`
4. `Customer Lifecycle Visibility`

Secondary sections:

1. `Approvals / Blockers`
2. `Reports And Review`

### 8.2 Sales Manager

Primary sections:

1. `Approvals / Blockers`
2. `Customer Inquiry`
3. `My Sales Work`
4. `Customer Lifecycle Visibility`

Secondary sections:

1. `Reports And Review`
2. `Quick Actions`

### 8.3 Executive Approver

Primary sections:

1. `Approvals / Blockers`
2. `Header And Summary`
3. `Customer Inquiry`

Secondary sections:

1. `Reports And Review`

Low emphasis:

1. routine quick actions
2. daily operational queue

## 9. Sales Return Responsibility Model

The console should follow this responsibility interpretation:

1. `Sales Person`
   - receives customer return complaint or inquiry
   - follows up and communicates status
2. `Warehouse / Operations`
   - validates and processes physical return
3. `Finance`
   - handles credit note, refund, and accounting settlement
4. `Sales Manager`
   - intervenes on exception or dispute cases

So the UI must allow sales to see return progress without turning sales into return-posting owners.

## 10. Approval Routing

### 10.1 Quotation

1. `Sales Person` creates
2. routine quotation may be submitted directly
3. exception quotation goes to `Sales Manager`
4. larger exception quotation escalates to `Executive Approver`

### 10.2 Sales Order

1. `Sales Person` creates
2. routine sales order may be submitted directly
3. exception sales order goes to `Sales Manager`
4. larger exception sales order escalates to `Executive Approver`

## 11. Current ERP Alignment Note

The live ERP already supports much of this role model, but the design intent remains:

1. customer-facing visibility for sales
2. approval authority for manager and executive
3. downstream status visibility without inappropriate downstream control

Implementation may continue to tighten around this authority.

## 12. Final Role Rule

For `Sales Console`, the role model should be remembered simply as:

1. `Sales Person`
   - act
   - inquire
   - follow up
   - see downstream status
2. `Sales Manager`
   - supervise
   - approve
   - resolve
3. `Executive Approver`
   - review escalations

This is the correct enterprise-grade role logic for the redesigned console.
