# Sales Console Implementation Plan

Status: redesigned enterprise-grade implementation plan for the next execution phase  
Scope: truthful sales-console completion, customer inquiry, lifecycle visibility, approval alignment, report cleanup, and AI staging  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-UI-Layout-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-UI-Layout-Spec.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md), [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md)

## 1. Purpose

This document defines the correct next implementation order for the redesigned `Sales Console`.

The goal is not only to finish existing cards.
The goal is to complete the console as a:

1. daily sales workspace
2. customer inquiry surface
3. lifecycle visibility surface
4. truthful approval and blocker surface

## 2. Working Principles

Implementation must follow these rules:

1. prefer business truth over design symmetry
2. prefer one powerful inquiry surface over many weak widgets
3. separate visibility from authority
4. use standard ERP structures where strong enough
5. build custom features only where they create obvious efficiency gains
6. stage AI after structured truth exists

## 3. Already Completed Foundations

The following foundations are already live or decided:

1. quotation exception approval policy
2. sales-order exception approval policy
3. live quotation workflow
4. live sales-order workflow
5. approval-state-aware console detection
6. first role-permission tightening pass

These remain part of the new console design.

## 4. New Priority Order

### Step 1. Finalize visible cards against the redesigned model

Goal:

1. align current visible cards with the redesigned section model

Work:

1. keep truthful existing cards
2. replace weak or outdated labels
3. decide exact phase-1 visible cards for:
   - `Customer Lifecycle Visibility`
   - `Reports And Review`

Deliverable:

1. final first-wave card set

### Step 2. Implement `Customer Inquiry`

Goal:

1. create one search-driven inquiry surface that resolves a customer or document clue into the full commercial chain

Phase-1 search inputs:

1. customer ID
2. customer name
3. quotation ID
4. sales order ID
5. sales invoice ID
6. delivery note ID

Phase-1 result:

1. primary match
2. customer summary
3. linked document flow
4. current status
5. blocker summary
6. related documents

Deliverable:

1. working server-side inquiry resolver
2. working UI inquiry surface in `Sales Console`

Why second:

1. this is the highest-value new feature
2. it directly improves customer response efficiency

### Step 3. Implement `Customer Lifecycle Visibility`

Goal:

1. give sales users downstream visibility they genuinely need

Recommended first-wave cards:

1. `Partially Delivered Orders`
2. `Invoices Outstanding`
3. `Sales Returns In Progress`

Implementation rule:

1. only activate cards that are formula-truthful on the live ERP

Deliverable:

1. one dedicated lifecycle row in the console

### Step 4. Rebalance role visibility and emphasis

Goal:

1. make the same console shell feel right for:
   - `Sales Person`
   - `Sales Manager`
   - `Executive Approver`

Work:

1. role-based first-look emphasis
2. compact vs stronger section behavior
3. ensure downstream visibility remains visible for sales without giving extra authority

Deliverable:

1. runtime role-based section emphasis and visibility behavior

### Step 5. Replace weak or outdated report targets

Goal:

1. ensure `Reports And Review` uses only strong, real targets

Recommended first-wave report set:

1. `Sales Analytics`
2. `Item-wise Sales History`
3. `Quotation Trends`
4. `Sales Order Analysis`
5. `Lost Quotations`
6. `Payment Terms Status for Sales Order`

Deliverable:

1. cleaned report section with truthful report cards

### Step 6. Align navigation to the new console intent

Goal:

1. make the console reduce menu hunting

Work:

1. direct record navigation from inquiry result
2. direct filtered lists from work, lifecycle, and blocker cards
3. role-safe destination handling

Deliverable:

1. updated click behavior across the redesigned console

### Step 7. Add AI as contextual assistant

Goal:

1. add AI in the places where structured truth already exists

Phase-1 AI use:

1. `Customer Inquiry Summary`
2. `Customer Brief`
3. `Blocker Explanation`
4. `Next Best Action`

Do not do yet:

1. AI-first inquiry
2. fully conversational status engine
3. invisible AI decisions

Deliverable:

1. compact AI layer attached to inquiry and context surfaces

### Step 8. Demo validation

Goal:

1. validate the new console as a customer-facing sales workspace, not only a styled page

Scenarios:

1. customer asks about quotation status
2. customer asks about order delivery progress
3. customer asks about invoice/payment status
4. customer asks about return status
5. sales manager reviews approval queue
6. executive approver reviews escalated exception

Deliverable:

1. scenario-based validation evidence

## 5. Recommended Phase Breakdown

### Phase 1. Complete Truthful Sales Console

Includes:

1. final card set
2. customer inquiry
3. lifecycle visibility
4. role-based emphasis
5. truthful reports

### Phase 2. Add Contextual AI

Includes:

1. inquiry summary
2. customer brief
3. blocker explanation
4. next-best-action

### Phase 3. Add Guided Work Intelligence

Includes:

1. `Today Worklist`
2. smarter prioritization
3. deeper activity and follow-up surfacing

## 6. Immediate Execution Recommendation

Implement next in this exact order:

1. finalize first-wave visible cards
2. implement `Customer Inquiry`
3. implement `Customer Lifecycle Visibility`
4. update role-based first-look behavior
5. replace report targets
6. add contextual AI after the structured surfaces are stable

## 7. Stop/Go Rule

Do not expand into more analytics or more AI until these are true:

1. inquiry works reliably
2. delivery / invoice / payment / return visibility is truthful
3. approval and blocker cards are truthful
4. report cards open real useful targets
5. role-based emphasis is stable

Only after that should the team expand further.

## 8. Final Implementation Judgment

The strongest implementation path is:

1. fewer but more truthful cards
2. one strong inquiry area
3. one grouped lifecycle visibility area
4. one approval and blocker area
5. AI added as contextual augmentation

That is the enterprise-grade way to make the `Sales Console` genuinely useful.
