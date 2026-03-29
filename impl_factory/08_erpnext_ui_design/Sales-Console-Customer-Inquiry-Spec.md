# Sales Console Customer Inquiry Spec

Status: functional and UX specification for the `Customer Inquiry` area inside `Sales Console`  
Scope: search inputs, match logic, result layout, lifecycle tracing, and AI support boundary  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-UI-Layout-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-UI-Layout-Spec.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md)

## 1. Purpose

`Customer Inquiry` is the most important new functional area in the redesigned `Sales Console`.

Its purpose is:

1. let sales users answer customer questions from one place
2. reduce switching across multiple ERP lists and modules
3. show a linked commercial chain from one clue
4. support customer-facing communication without expanding sales authority inappropriately

## 2. Design Principle

The inquiry area should work like this:

1. user enters one clue
2. system identifies the likely document or customer
3. system traces the related commercial flow
4. system returns a structured result
5. AI may summarize that result later

This is a structured inquiry engine first, not a chat-first feature.

## 3. Accepted Inputs

### 3.1 Phase-1 Accepted Inputs

1. customer ID
2. customer name
3. quotation ID
4. sales order ID
5. sales invoice ID
6. delivery note ID

### 3.2 Later Inputs If Data Quality Supports Them

1. phone
2. WhatsApp number
3. partial keyword
4. broader date-based search

## 4. Match Strategy

### 4.1 Exact Match Priority

If the input matches:

1. `Quotation.name`
2. `Sales Order.name`
3. `Sales Invoice.name`
4. `Delivery Note.name`
5. `Customer.name`

then the inquiry should treat that as the primary match.

### 4.2 Name-Based Customer Match

If the input is a customer name:

1. return the best customer match
2. show recent commercial history and related flow

### 4.3 Multiple Match Handling

If multiple records are plausible:

1. show a small result chooser
2. let the user pick the correct commercial chain

The system must not pretend certainty when there are multiple plausible matches.

## 5. Result Layout

The default result layout should contain these blocks:

1. `Primary Match`
2. `Customer Summary`
3. `Document Flow`
4. `Current Status`
5. `Exceptions / Blockers`
6. `Related Documents`

## 6. Result Content

### 6.1 Primary Match

Should show:

1. matched record type
2. matched record ID
3. customer name
4. primary status

### 6.2 Customer Summary

Should show:

1. customer
2. territory if relevant
3. latest commercial document references
4. contact-friendly context if available

### 6.3 Document Flow

Default sequence:

1. `Quotation`
2. `Sales Order`
3. `Delivery`
4. `Sales Invoice`
5. `Payment`
6. `Return`

This should read like one business chain, not like unrelated tables.

### 6.4 Current Status

Should answer:

1. is the order confirmed
2. is delivery pending / partial / complete
3. is invoice pending / issued / partly paid / paid / overdue
4. is return active or not
5. is approval or exception blocking progress

### 6.5 Exceptions / Blockers

Should show:

1. approval waiting
2. delivery issue if evident
3. invoice/payment concern at summary level
4. return issue if present

### 6.6 Related Documents

Should show clickable links to:

1. matched source document
2. upstream documents
3. downstream documents

## 7. Result Trust Rules

The result must distinguish between:

1. `not used`
2. `not yet created`
3. `not applicable`
4. `unknown because no trustworthy link exists`

This prevents the inquiry from giving a false sense of completeness.

## 8. Role Rules

### 8.1 Sales Person

Can use the inquiry to:

1. answer customer questions
2. view downstream status
3. open related records in review mode

### 8.2 Sales Manager

Can use the inquiry to:

1. review customer chain
2. understand team blockers
3. review approval context

### 8.3 Executive Approver

Can use the inquiry to:

1. review escalated commercial context
2. understand the cross-document story before approving

## 9. ERP Data Sources

Phase-1 inquiry should use:

1. `Customer`
2. `Quotation`
3. `Sales Order`
4. `Delivery Note`
5. `Sales Invoice`
6. `Payment Entry`
7. return-related invoice or delivery documents

## 10. Phase-1 Scope

Phase-1 inquiry should:

1. accept exact document IDs and customer names
2. resolve linked documents
3. show structured result blocks
4. allow direct record navigation

Phase-1 inquiry should not yet try to:

1. interpret vague free-text customer stories
2. rely on AI for matching
3. solve poor data linkage invisibly

## 11. AI Boundary

AI should support inquiry by:

1. summarizing the result
2. explaining blockers
3. suggesting next action
4. preparing a short customer-facing explanation

AI should not:

1. replace the structured result
2. be the only matching engine
3. invent missing links

## 12. Success Criteria

`Customer Inquiry` is successful when a sales user can:

1. enter one clue
2. get the related commercial chain
3. understand the current customer-impacting status quickly
4. answer the customer without checking multiple ERP lists manually

## 13. Final Design Judgment

If the redesigned `Sales Console` only adds one major new feature, it should be `Customer Inquiry`.

It is the strongest productivity improvement and the clearest differentiator for a customer-facing sales workspace.
