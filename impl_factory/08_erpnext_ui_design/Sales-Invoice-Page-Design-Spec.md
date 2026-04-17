# Sales Invoice Page Design Spec

Status: first-wave child-page design spec  
Scope: redesign direction for `Sales Invoice` as the primary settlement-visibility page after `Sales Console`  
Source authority: [Child-Page-Design-Framework.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Child-Page-Design-Framework.md), [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md)

## 1. Purpose

This document defines how `Sales Invoice` should be redesigned so it supports sales-facing settlement visibility better than the default ERPNext presentation.

The page should help the user answer:

1. is this invoice paid, partly paid, overdue, or returned
2. what balance is still outstanding
3. what linked order or delivery context exists
4. whether return or refund activity is involved
5. what the user should tell the customer next

## 2. Primary Page Identity

`Sales Invoice` is not only an accounting record from the viewpoint of `Sales Console`.

Its primary purpose in this redesign is:

1. settlement visibility page

This page should therefore emphasize:

1. payment and settlement status
2. due visibility
3. outstanding amount
4. customer-facing payment meaning
5. return or credit-note context

## 3. Target Roles

Primary roles:

1. `Sales Person`
2. `Sales Manager`

Secondary role:

1. `Executive Approver`

Related but non-primary users later:

1. finance users through future finance-oriented surfaces

## 4. Top Summary Band

The top summary band should show:

1. sales invoice ID
2. customer
3. invoice status
4. due date
5. grand total
6. outstanding amount
7. paid or partly paid signal
8. return indicator if relevant
9. owner or responsible sales user where useful

Purpose:

1. let the user immediately understand the settlement position of the invoice

## 5. Primary Action Zone

The visible action set should focus on visibility and customer response rather than finance authority.

Examples of primary actions:

1. open linked sales order
2. open linked delivery note
3. open payment records where allowed
4. open return or credit-note records
5. create or open follow-up task
6. print or share invoice if appropriate

Rules:

1. actions should help the user understand and respond
2. finance posting authority must not be implied by sales visibility
3. return-linked actions should become prominent when the invoice is a return

## 6. Linked Document Strip

The page should show a compact chain for:

1. linked sales order
2. linked delivery note
3. payment reference surface if visible
4. return invoice or delivery return where relevant

Purpose:

1. preserve the commercial and settlement chain
2. reduce menu hunting
3. help the user answer customer questions quickly

## 7. Primary Working Section

This is the core settlement section.

It should focus on payment meaning and customer-facing interpretation.

Recommended content:

1. settlement status
2. outstanding amount
3. due or overdue visibility
4. payment summary
5. return or refund state if relevant

This section should make it clear whether the invoice is:

1. fully paid
2. partly paid
3. overdue
4. under return or credit review
5. operationally settled

## 8. Supporting Context Section

This section should contain:

1. related follow-up task
2. overdue follow-up note
3. return settlement note if relevant
4. AI summary later if helpful

This section should help the user communicate and follow up, not duplicate finance detail.

## 9. Detailed Transaction Area

The detailed lower area may retain standard ERPNext sections such as:

1. items
2. taxes and charges
3. payment terms
4. remarks
5. addresses

But the user should not need to study the form body to answer:

1. has the customer paid
2. is a balance still pending
3. is this overdue
4. is a return involved

## 10. Role Behavior

### Sales Person

Should emphasize:

1. payment status meaning
2. overdue or partly paid visibility
3. what to tell the customer
4. linked return context if relevant

Should not be overloaded with:

1. deep accounting controls
2. low-level ledger detail

### Sales Manager

Should additionally see:

1. settlement risk signals
2. overdue and return follow-up patterns
3. stronger task and escalation visibility

### Executive Approver

Should see:

1. settlement or return context only when relevant to escalations or commercial exceptions

This page should not become a routine operational page for this role.

## 11. Design Rules

### 11.1 Keep The Page Settlement-Focused

`Sales Invoice` should not become:

1. a finance ledger page
2. a warehouse page
3. a generic reporting page

### 11.2 Preserve Customer-Facing Meaning

The page should make it easy for sales to answer:

1. whether the invoice is paid
2. whether money is still pending
3. whether a follow-up is needed
4. whether return activity is affecting settlement

### 11.3 Preserve Role Safety

Sales visibility into invoice and payment status must not be confused with:

1. authority to post payments
2. authority to reconcile finance
3. authority to complete refund processing

## 12. Console Linkage

This page is a primary destination from:

1. `Invoices Outstanding`
2. `Sales Returns In Progress`
3. `Customer Inquiry`
4. return-related inquiry chains

So its design must preserve context from those entry points.

## 13. Success Criteria

The redesign is successful if a user can open a `Sales Invoice` and understand within a few seconds:

1. whether it is paid, partly paid, overdue, or returned
2. what balance remains
3. what linked execution chain exists
4. whether return or refund review is involved
5. what the next customer-facing response should be

## 14. Implementation Note

Implementation should enhance the existing ERPNext page rather than replace the transaction engine.

Preferred approach:

1. improve page hierarchy
2. improve settlement visibility
3. add clearer overdue and return surfaces
4. add linked-document visibility
5. make customer-response interpretation more obvious
