# Quotation Page Design Spec

Status: first-wave child-page design spec  
Scope: redesign direction for `Quotation` as the primary commercial decision page after `Sales Console`  
Source authority: [Child-Page-Design-Framework.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Child-Page-Design-Framework.md), [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md)

## 1. Purpose

This document defines how `Quotation` should be redesigned so it becomes a stronger commercial working surface than the default ERPNext presentation.

The page should help the user answer:

1. is this quotation still active
2. is it waiting approval
3. is it near expiry
4. can it move to the next stage
5. what is the next commercial action

## 2. Primary Page Identity

`Quotation` is not mainly an execution page and not mainly a reporting page.

Its primary purpose is:

1. commercial decision page

This page should therefore emphasize:

1. approval state
2. pricing and discount meaning
3. quotation validity and expiry urgency
4. customer follow-up readiness
5. conversion readiness

## 3. Target Roles

Primary roles:

1. `Sales Person`
2. `Sales Manager`

Secondary role:

1. `Executive Approver`

## 4. Top Summary Band

The top summary band should show:

1. quotation ID
2. customer
3. quotation status
4. workflow state
5. owner / responsible sales user
6. valid till date
7. grand total
8. discount indicator
9. urgency or blocker indicator

Purpose:

1. let the user immediately understand the commercial state of the quotation

## 5. Primary Action Zone

The top actions should reflect the quotation lifecycle.

Examples of primary actions:

1. save draft
2. submit or send for approval
3. approve
4. reject
5. revise
6. convert to sales order
7. create or open follow-up task

Rules:

1. the most likely next commercial action must be visible near the top
2. approval actions must be visible only to the correct roles
3. conversion should not appear as the main action when approval or revision is still pending

## 6. Linked Document Strip

The page should show a compact related chain for:

1. customer
2. linked opportunity if any
3. resulting sales order if converted
4. related follow-up task if present

Purpose:

1. preserve commercial context
2. help the user move through the sales chain without menu hunting

## 7. Primary Working Section

This is the core commercial section.

It should focus on the quotation’s ability to move forward.

Recommended content:

1. approval trigger and approval state
2. discount summary
3. validity and expiry visibility
4. conversion readiness
5. customer response or revision need

This section should make it clear whether the quotation is:

1. still draft
2. waiting approval
3. ready to send or negotiate
4. nearing expiry
5. ready for conversion

## 8. Supporting Context Section

This section should contain:

1. latest follow-up task
2. approval trigger explanation
3. last commercial note or remark later if useful
4. linked customer inquiry context later if needed

This section should support commercial movement rather than duplicate the whole form.

## 9. Detailed Transaction Area

The detailed lower area may retain standard ERPNext sections such as:

1. items
2. taxes and charges
3. terms and conditions
4. contact and address details
5. remarks

But the user should not need to scan the entire form body just to understand whether the quotation is commercially actionable.

## 10. Role Behavior

### Sales Person

Should emphasize:

1. draft and actionable state
2. expiry urgency
3. next customer-facing move

Should not be overloaded with:

1. executive review detail
2. unnecessary management analytics

### Sales Manager

Should additionally see:

1. approval context
2. team ownership clarity
3. stronger discount and exception visibility
4. review of stalled or risky quotations

### Executive Approver

Should see:

1. escalation reason
2. approval impact
3. customer and commercial value context

The page should not become a routine work surface for this role.

## 11. Design Rules

### 11.1 Keep The Page Commercial

`Quotation` should remain a commercial page.

Do not turn it into:

1. a CRM timeline
2. an analytics page
3. an execution-control page

### 11.2 Make Approval Meaning Visible

If the quotation requires approval, the user should understand quickly:

1. why approval is needed
2. who should act next
3. whether the quotation can move forward yet

### 11.3 Make Expiry Risk Visible

The page should make it easy to answer:

1. is this quotation close to expiry
2. does a follow-up need to happen today

## 12. Console Linkage

This page is a primary destination from:

1. `New Quotation`
2. `Quotations Waiting For Action`
3. `Open Quotations Nearing Expiry`
4. `Quotations Awaiting Approval`
5. `Customer Inquiry`

So its design must preserve context from those entry points.

## 13. Success Criteria

The redesign is successful if a user can open a `Quotation` and understand within a few seconds:

1. whether it is draft, active, or blocked
2. whether it is near expiry
3. whether approval is required
4. whether it is ready for conversion
5. what the next commercial action should be

## 14. Implementation Note

Implementation should enhance the existing ERPNext page rather than replace the transaction engine.

Preferred approach:

1. improve page hierarchy
2. improve section order
3. add clearer approval and expiry surfaces
4. add linked-document visibility
5. make the next commercial action obvious
