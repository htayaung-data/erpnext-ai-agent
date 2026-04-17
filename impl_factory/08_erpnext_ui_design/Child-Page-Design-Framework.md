# Child-Page Design Framework

Status: source of truth for enterprise-grade child-page redesign after `Sales Console`  
Scope: reusable design framework for transaction pages and review pages opened from role-based consoles  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md)

## 1. Purpose

This document defines how child pages should be redesigned so the product remains coherent after the user leaves a console.

It exists to prevent this failure pattern:

1. user starts in a modern role-based console
2. user clicks into a raw default ERPNext page
3. user loses context, action clarity, and visual continuity

The goal is to make child pages:

1. coherent with the console
2. role-aware without becoming fragmented
3. easier to understand
4. easier to act on
5. reusable across multiple consoles

## 2. Scope

This framework applies to:

1. transaction forms
2. operational review pages
3. queue or worklist pages
4. drill-down pages opened from inquiry results

It is intended to support:

1. `Sales Console`
2. future `GM / Executive Console`
3. future `Purchase Console`
4. future `Finance Console`
5. future `Inventory Console`

## 3. Core Design Judgment

The product should not redesign every ERPNext page independently.

Instead it should define a reusable page framework and then apply that framework selectively to high-value pages.

This means:

1. keep the ERP transaction engine and document model stable
2. redesign the working experience around those documents
3. prefer shared UI rules over page-by-page improvisation

## 4. Page Philosophy

Child pages should not feel like generic forms.

They should feel like one of three things:

1. a decision page
2. an execution page
3. a customer-response page

Every page should have one primary purpose.

This is a hard guardrail.

Do not let a page become:

1. a dashboard
2. a queue
3. a form
4. a report
5. an AI surface

all at once.

## 5. Page Types

### 5.1 Enhanced Transaction Form

Use when the user needs to understand and work on one specific business document.

Examples:

1. `Quotation`
2. `Sales Order`
3. `Sales Invoice`

Design rule:

1. retain ERPNext form behavior
2. improve hierarchy, action clarity, and contextual guidance

### 5.2 Review / Worklist Page

Use when the user needs to process multiple records or work through a queue.

Examples:

1. approval queue
2. return review
3. follow-up worklist
4. overdue invoice review

Design rule:

1. queue logic belongs here, not inside the transaction form

### 5.3 Drill-Down Record View

Use when the user needs to inspect an exact record from inquiry or linked-document navigation.

Design rule:

1. exact record access should remain direct
2. users should not be forced back through generic lists if the record is already known

## 6. Shared Child-Page Skeleton

All enhanced transaction forms should use the same high-level structure:

1. `Top Summary Band`
2. `Primary Action Zone`
3. `Linked Document Strip`
4. `Primary Working Section`
5. `Supporting Context Section`
6. `Detailed Transaction Area`
7. `AI Assist` only as a compact secondary layer where useful

This shared skeleton is what makes the ERP feel like one coherent operating system.

## 7. Top Summary Band Standard

Every first-wave child page should start with a summary band containing:

1. document identity
2. customer or party
3. current status
4. workflow state if relevant
5. owner / responsible role
6. key amount or commitment value
7. key progress indicator
8. urgency, blocker, or exception signal

The user should be able to understand the document at a glance before reading the form body.

## 8. Primary Action Zone

The page must make the next business action obvious.

Rules:

1. place the most likely next actions near the top
2. keep the action set role-safe
3. group routine actions separately from exceptional actions
4. do not hide the main next action deep inside the form body

Examples of suitable actions:

1. submit
2. send for approval
3. revise
4. convert
5. open linked downstream documents
6. create follow-up task

## 9. Linked Document Strip

Every page should show the immediate related chain in a compact way.

Purpose:

1. preserve context
2. reduce menu hunting
3. help the user move across the business chain safely

Typical related records:

1. previous commercial document
2. downstream execution document
3. invoice or payment context
4. return document where relevant

## 10. Primary Working Section

This section depends on the page purpose.

Rules:

1. it must represent the main business job of the page
2. it must appear before secondary detail
3. it must be easy to scan

Examples:

1. pricing and approval context on `Quotation`
2. fulfillment and billing progress on `Sales Order`
3. settlement and due visibility on `Sales Invoice`

## 11. Supporting Context Section

This is where secondary but still useful context belongs.

Examples:

1. follow-up task
2. recent note or explanation
3. approval trigger reason
4. related exception or return state

This section should support the main page purpose, not compete with it.

## 12. Detailed Transaction Area

The lower part of the page may still contain traditional ERP form details, including:

1. items
2. taxes
3. terms
4. contacts
5. address
6. remarks

But the user should not need to read this area to answer:

1. what is this
2. what is happening
3. what should I do next

## 13. Role Strategy

Use the same page skeleton across roles.

Change by role:

1. visible actions
2. emphasis
3. level of detail
4. authority
5. review visibility

Do not change by role:

1. main page structure
2. top summary logic
3. major section order
4. basic mental model

This keeps the product trainable and maintainable.

## 14. AI Placement Rule

AI should be:

1. contextual
2. compact
3. secondary

AI may help with:

1. summary
2. blocker explanation
3. next action
4. customer-facing draft language

AI should not replace:

1. structured status
2. workflow truth
3. form controls
4. list navigation

## 15. Reuse Rule Across Consoles

Child pages should be built as reusable assets.

That means:

1. the same `Sales Invoice` page may be opened from more than one console
2. the same return review page may later be used by both sales and finance contexts
3. the same structure should stay valid even when the entry point changes

This is the enterprise-grade alternative to console-specific one-off pages.

## 16. First-Wave Priority

The first-wave child-page redesign priority is:

1. `Sales Order`
2. `Quotation`
3. `Sales Invoice`

This order is based on:

1. operational importance
2. customer-facing importance
3. reuse potential across future consoles

## 17. Quality Rules

No child page should be accepted unless it is:

1. visually aligned with the console
2. easier than the default ERPNext page
3. role-safe
4. truthful in workflow and status
5. clear about the next action

## 18. Outcome

This framework should allow the ERP to become:

1. simpler to use
2. more comprehensive in context
3. more consistent across modules
4. easier to extend without fragmentation
