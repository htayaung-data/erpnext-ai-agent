# Sales Console Design

Status: redesigned business and UI source of truth for the first implementation target  
Scope: `Sales Console` only  
Source authority: [UI-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/UI-Design.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md)

## 1. Purpose

This document defines the redesigned `Sales Console`.

The redesign responds to a practical ERP reality:

1. the salesperson is often the main customer-facing focal person
2. sales users need status visibility beyond quotation and sales order
3. the console must support real customer inquiry, not only action shortcuts
4. the UI must stay sales-oriented without turning into a warehouse or finance cockpit

The goal is to make `Sales Console`:

1. operationally truthful
2. enterprise-grade in visibility and control
3. fast for daily sales work
4. strong for customer inquiry and follow-up
5. expandable without becoming cluttered

## 2. Sales Console Mission

The `Sales Console` should be the main daily workspace for sales roles.

It should help the sales team do six things well:

1. start the day with clear priorities
2. create and follow quotations and sales orders quickly
3. answer customer questions using one unified inquiry area
4. see delivery, invoice, payment, and return status without leaving the sales context
5. avoid missing approvals, blockers, and follow-up obligations
6. move from customer conversation to ERP action with minimal menu hunting

This console is not a generic dashboard and not a full CRM replacement.
It is a customer-facing commercial operating console.

## 3. Core Design Judgment

The redesigned `Sales Console` should no longer be only `quotation-first`.

It should be:

1. customer-facing
2. order-lifecycle-aware
3. inquiry-friendly
4. approval-aware
5. return-aware
6. role-sensitive

It should not become:

1. finance-heavy
2. warehouse-control-heavy
3. setup-heavy
4. report-first
5. AI-first

## 4. Target Users

Primary users:

1. `Sales Person`
2. `Key Account Sales`
3. `Sales Manager`

Secondary or occasional users:

1. `Executive Approver`
2. showroom or counter-sale user through a simplified mode later

## 5. Role Philosophy

The role logic for the UI should follow this principle:

1. `Sales Person`
   - broad visibility
   - limited approval authority
   - strong customer inquiry support
2. `Sales Manager`
   - broader team visibility
   - approval and exception control
   - stronger review surfaces
3. `Executive Approver`
   - escalation and exception review
   - not a routine daily transaction user

The console must distinguish between:

1. seeing status
2. owning operational action

Sales users often need to see downstream status even when they do not own delivery, invoicing, payment posting, or return settlement.

## 6. Business Outcomes

The redesigned console should improve:

1. quotation turnaround speed
2. order-entry efficiency
3. customer response speed
4. follow-up discipline
5. visibility of approvals and blockers
6. visibility of delivery, invoice, payment, and return status
7. confidence during customer calls and visits

## 7. Console Structure

The recommended top-to-bottom structure is:

1. `Header And Summary`
2. `Quick Actions`
3. `Customer Inquiry`
4. `My Sales Work`
5. `Customer Lifecycle Visibility`
6. `Approvals / Blockers`
7. `Reports And Review`
8. `AI Assist`

This is the new reference information architecture.

## 8. Detailed Section Design

### 8.1 Header And Summary

Contents:

1. workspace title: `Sales Console`
2. role label
3. branch or commercial scope
4. compact summary band

Recommended summary cards:

1. `Awaiting Approval`
2. `Open Orders`

Optional later additions:

1. `Orders Due Soon`
2. `Returns In Progress`

Purpose:

1. establish where the user is
2. show daily commercial scope
3. provide two trustworthy high-level signals without building a KPI-heavy dashboard

### 8.2 Quick Actions

This remains the immediate action zone.

Recommended cards:

1. `New Opportunity`
2. `New Quotation`
3. `New Sales Order`
4. `Open Customer`
5. `Open Item`

Rules:

1. must stay above the fold
2. should remain operational, not analytical
3. action cards should feel slightly more immediate than report cards

### 8.3 Customer Inquiry

This is a new core section and should become one of the most important surfaces in the console.

Purpose:

1. let sales users answer customer questions from one place
2. avoid jumping across multiple lists and forms
3. provide a unified commercial trace from any known clue

Search input should accept:

1. customer ID
2. customer name
3. quotation ID
4. sales order ID
5. sales invoice ID
6. delivery note ID
7. phone or keyword where available
8. optional date range filters

The result should return a unified chain such as:

1. customer
2. quotation
3. sales order
4. delivery
5. invoice
6. payment summary
7. return status

The inquiry result should show:

1. primary match
2. current overall status
3. related documents in sequence
4. blockers or pending actions
5. recent notes or follow-up indicators where available

This should be implemented as structured ERP data first.
AI may summarize it later, but should not be the primary answer mechanism.

### 8.4 My Sales Work

This is the salesperson's active operating queue.

Recommended cards:

1. `Quotations Waiting For Action`
2. `Open Quotations Nearing Expiry`
3. `Sales Orders Pending Fulfillment`
4. `Customer Follow-Up Tasks`

Optional next-phase additions:

1. `Opportunities Closing Soon`
2. `Quotations Returned For Revision`

Purpose:

1. show work that sales must move
2. keep the queue operational, not decorative

### 8.5 Customer Lifecycle Visibility

This is the most important conceptual addition in the redesign.

Purpose:

1. let sales users see downstream customer-impacting status
2. keep customer-facing answers inside the sales workspace
3. avoid forcing sales to ask warehouse or finance before answering basic status questions

Recommended phase-1 cards:

1. `Partially Delivered Orders`
2. `Invoices Outstanding`
3. `Sales Returns In Progress`

Possible alternates depending on real ERP capability:

1. `Orders Due Soon`
2. `Delivered Not Yet Invoiced`
3. `Payments Pending`

Rules:

1. this section is visibility-first, not authority-first
2. cards may open delivery, invoice, payment, or return records in review mode
3. sales users must not get inappropriate warehouse or finance controls through this section

### 8.6 Approvals / Blockers

This remains important, especially for `Sales Manager`.

Recommended cards:

1. `Orders Blocked By Approval`
2. `Quotations Awaiting Approval`
3. `Escalated Commercial Exceptions`

Role behavior:

1. `Sales Person`
   - sees only own blocked or pending items if meaningful
2. `Sales Manager`
   - sees full team approval queue
3. `Executive Approver`
   - sees escalation-focused approval view

### 8.7 Reports And Review

This zone remains a lower-priority review surface.

Recommended targets must be real and usable, not idealized labels.

Examples:

1. `Sales Analytics`
2. `Item-wise Sales Register`
3. a truthful customer-history target
4. a truthful open-order review target

Rules:

1. if a planned report does not truly exist, replace it
2. do not keep decorative or misleading report cards
3. this section should feel quieter than `Quick Actions`

### 8.8 AI Assist

AI should remain present but secondary.

Best-fit AI roles:

1. summarize inquiry results
2. produce customer brief
3. explain approval or blocker reason
4. recommend next action

AI should not be:

1. the main inquiry engine
2. the only source of truth for status
3. a replacement for document-linked lifecycle visibility

## 9. Role Variants In The Console

### 9.1 Sales Person

Highest emphasis:

1. `Quick Actions`
2. `Customer Inquiry`
3. `My Sales Work`
4. `Customer Lifecycle Visibility`

Lower emphasis:

1. `Approvals / Blockers`
2. `Reports And Review`

### 9.2 Sales Manager

Highest emphasis:

1. `Approvals / Blockers`
2. `My Sales Work`
3. `Customer Inquiry`
4. `Reports And Review`

Additional team-oriented visibility:

1. team queue
2. exception approvals
3. return issues requiring attention

### 9.3 Executive Approver

Highest emphasis:

1. `Approvals / Blockers`
2. summary visibility
3. escalated commercial cases

Lower emphasis:

1. routine action shortcuts
2. daily sales follow-up surfaces

## 10. Sales Return Treatment

`Sales Return` should be included in the console design.

Reason:

1. customer often contacts sales first about the return
2. sales needs visibility into whether the return is progressing
3. sales needs to know whether warehouse and finance steps have completed

Recommended role interpretation:

1. `Sales Person`
   - customer-facing initiator or follow-up owner
   - visibility into return progress
2. `Warehouse / Operations`
   - physical return validation
3. `Finance`
   - credit note / settlement
4. `Manager`
   - exception review if policy requires it

The console should therefore show return status, but not turn sales into stock or refund controllers.

## 11. What The Console Should Not Include

Avoid adding these as main first-wave cards:

1. full AR aging table
2. stock ledger detail
3. packing or dispatch processing actions
4. refund accounting actions
5. broad finance reconciliation views
6. generic dashboard widgets with weak sales meaning

The sales team needs visibility into outcomes, not ownership of every downstream process.

## 12. Technical Implementation Recommendation

The redesign should still follow the original first-wave technical approach:

1. ERPNext workspace shell
2. curated shortcuts
3. custom summary blocks
4. server-side formulas
5. role-aware visibility
6. truthful navigation targets

New technical priority:

1. implement a unified inquiry resolver that can trace related documents from one input

This is more valuable than adding more decorative KPI cards.

## 13. Success Criteria

The redesigned `Sales Console` is successful when:

1. sales users can answer customer status questions from one place
2. users can see where a quotation or order stands in the lifecycle
3. approvals and blockers remain obvious
4. sales can see return and downstream status without receiving inappropriate authority
5. managers can review team exceptions without using generic module navigation
6. the workspace stays clean and sales-oriented

## 14. Final Design Judgment

The correct reference direction for `Sales Console` is:

1. action-oriented
2. inquiry-capable
3. lifecycle-visible
4. approval-aware
5. return-aware

It should remain a sales workspace, but a stronger one:

1. not only for creating documents
2. not only for monitoring quotes
3. but for managing the customer-facing commercial journey from inquiry to post-sale status
