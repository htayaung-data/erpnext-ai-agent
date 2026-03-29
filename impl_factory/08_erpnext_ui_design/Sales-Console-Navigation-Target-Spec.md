# Sales Console Navigation Target Spec

Status: navigation source of truth for the redesigned `Sales Console`  
Scope: click targets, inquiry behavior, filtered destinations, and downstream review navigation  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md)

## 1. Purpose

This document defines where each action, card, or inquiry result in `Sales Console` should take the user.

The navigation must feel:

1. direct
2. role-safe
3. business-correct
4. not dependent on menu hunting

## 2. Navigation Rules

All navigation must follow these rules:

1. clicks should preserve user scope where possible
2. staff should land in operational views
3. managers should land in review-oriented views
4. executive users should land in escalation-oriented views
5. downstream document visibility must not expose inappropriate authority

## 3. Quick Actions

### 3.1 New Opportunity

Target:

1. new `Opportunity` form

### 3.2 New Quotation

Target:

1. new `Quotation` form

### 3.3 New Sales Order

Target:

1. new `Sales Order` form

### 3.4 Open Customer

Target:

1. `Customer` list or search-first customer surface

Behavior:

1. respect role scope where possible

### 3.5 Open Item

Target:

1. `Item` list

Behavior:

1. read-oriented for sales roles

## 4. Header Summary Targets

### 4.1 Awaiting Approval

Target:

1. combined approval review list if implemented later
2. otherwise filtered `Quotation` or `Sales Order` list depending on the dominant count source

Preferred phase-1 behavior:

1. open the most relevant filtered approval queue for the current role

### 4.2 Open Orders

Target:

1. filtered `Sales Order` list

Filter intent:

1. active submitted orders not cancelled or closed

## 5. Customer Inquiry Navigation

This is the most important new navigation behavior.

### 5.1 Inquiry Search

Behavior:

1. user enters one clue
2. system identifies the primary match
3. system resolves related documents
4. result shows linked chain

### 5.2 Inquiry Result Click Targets

If the result contains:

1. `Customer`
   - open customer record
2. `Quotation`
   - open quotation record
3. `Sales Order`
   - open sales order record
4. `Delivery`
   - open delivery note
5. `Invoice`
   - open sales invoice
6. `Payment`
   - open payment entry or payment reference surface
7. `Return`
   - open return invoice or return delivery record

### 5.3 Inquiry Result Review Rule

The inquiry result should not force users through generic list pages if the primary record is already known.

So:

1. exact match should open exact record
2. related documents should be clickable in the result itself
3. if multiple matches exist, the user should first choose the correct commercial chain

## 6. My Sales Work Targets

### 6.1 Quotations Waiting For Action

Target:

1. filtered `Quotation` list

### 6.2 Open Quotations Nearing Expiry

Target:

1. filtered `Quotation` list

### 6.3 Sales Orders Pending Fulfillment

Target:

1. filtered `Sales Order` list

### 6.4 Customer Follow-Up Tasks

Target:

1. filtered `ToDo` list

Future preferred destination:

1. dedicated sales follow-up worklist

## 7. Customer Lifecycle Visibility Targets

### 7.1 Partially Delivered Orders

Target:

1. filtered `Sales Order` list

Reason:

1. sales users think in terms of orders first
2. sales order is a better customer-facing commercial anchor than delivery list alone

Secondary drill-down:

1. related `Delivery Note` records should be visible from the order

### 7.2 Invoices Outstanding

Target:

1. filtered `Sales Invoice` list in review mode

Reason:

1. sales needs billing and payment visibility, not finance control

### 7.3 Sales Returns In Progress

Target:

1. filtered return review list

Phase-1 fallback:

1. filtered `Sales Invoice` return list or `Delivery Note` return list, depending on the dominant return model

## 8. Approvals / Blockers Targets

### 8.1 Orders Blocked By Approval

Target:

1. filtered `Sales Order` approval review list

### 8.2 Quotations Awaiting Approval

Target:

1. filtered `Quotation` approval review list

### 8.3 Escalated Commercial Exceptions

Target:

1. filtered approval queue for executive review states

## 9. Reports And Review Targets

Only use real existing review targets.

### 9.1 Sales Analytics

Target:

1. `Sales Analytics` report

### 9.2 Item-wise Sales History

Target:

1. `Item-wise Sales History` report

### 9.3 Quotation Trends

Target:

1. `Quotation Trends` report

### 9.4 Sales Order Analysis

Target:

1. `Sales Order Analysis` report

### 9.5 Lost Quotations

Target:

1. `Lost Quotations` report

### 9.6 Payment Terms Status for Sales Order

Target:

1. `Payment Terms Status for Sales Order` report

## 10. AI Assist Targets

AI surfaces should be context-bound.

### 10.1 Customer Inquiry Summary

Target:

1. no navigation by default
2. may provide optional links back to source documents

### 10.2 Blocker Explanation

Target:

1. link to the blocked source record

### 10.3 Next Best Action

Target:

1. link to the recommended next operational destination

## 11. Destination Quality Rules

Every target should pass these tests:

1. is it the right record type
2. is it filtered correctly
3. does it preserve role scope
4. does it feel like the logical next step
5. does it reduce menu hunting

## 12. Standard Page vs Enhanced Page Strategy

Phase-1 rule:

1. use standard ERPNext list, form, and report pages where they are good enough

High-value enhancement candidates:

1. `Customer Inquiry` custom resolver and result panel
2. `Today Worklist` later
3. `Blocked Approval Review` later if standard lists prove too weak

## 13. Final Navigation Rule

The redesigned console should never require the user to think:

1. which module holds this answer
2. which document should I open first
3. which downstream table should I check next

The console must do that thinking for them.
