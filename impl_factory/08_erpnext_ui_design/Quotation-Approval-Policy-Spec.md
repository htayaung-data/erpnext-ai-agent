# Quotation Approval Policy Spec

Status: implementation-stage approval policy for `Quotation`  
Scope: exception-based quotation submission and approval routing for the `Sales Console` demo  
Source authority: [Sales-Console-Implementation-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Implementation-Plan.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md)

## 1. Purpose

This document defines the quotation approval rules for the phase-1 enterprise demo.

It is designed to keep routine quotation flow fast while still demonstrating:

1. approval governance
2. role separation
3. escalation handling for larger or discounted quotations

## 2. Core Principle

`Quotation` should follow the same exception-based approval philosophy as `Sales Order`.

That means:

1. routine quotation
   - `Sales User` may submit directly
2. exception quotation
   - `Sales Manager` reviews first
3. larger or more exceptional quotation
   - `Executive Approver` reviews escalation

The goal is to avoid forcing manager review on every ordinary quotation.

## 3. Fields Used

The policy uses only standard header-level quotation fields already present on the site:

1. `grand_total`
2. `additional_discount_percentage`
3. `discount_amount`

Phase 1 does not use item-row discount logic.

## 4. Policy Thresholds

### 4.1 Routine quotation

Direct `Sales User` submission is allowed when all are true:

1. `grand_total < 10,000,000`
2. `additional_discount_percentage == 0`
3. `discount_amount == 0`

### 4.2 Manager approval required

Quotation must go to `Pending Sales Approval` when any are true:

1. `grand_total >= 10,000,000`
2. `additional_discount_percentage > 0`
3. `discount_amount > 0`

### 4.3 Manager may approve

`Sales Manager` may approve when all are true:

1. `grand_total < 25,000,000`
2. `additional_discount_percentage < 10`
3. `discount_amount < 1,000,000`

### 4.4 Executive escalation required

Quotation must escalate to `Pending Executive Approval` when any are true:

1. `grand_total >= 25,000,000`
2. `additional_discount_percentage >= 10`
3. `discount_amount >= 1,000,000`

## 5. Workflow States

The live phase-1 workflow uses:

1. `Draft`
2. `Pending Sales Approval`
3. `Pending Executive Approval`
4. `Approved`
5. `Rejected`

## 6. Role Behavior

### 6.1 Sales User

May:

1. create and edit quotation
2. submit routine quotation directly
3. submit exception quotation into manager review
4. revise and resubmit rejected quotation

May not:

1. approve manager-review quotation
2. approve executive-review quotation

### 6.2 Sales Manager

May:

1. approve routine exception quotation inside threshold
2. escalate larger exception quotation
3. reject quotation

### 6.3 Executive Approver

May:

1. approve escalated quotation
2. reject escalated quotation

## 7. Final Judgment

This quotation policy is the correct demo-grade design because it shows:

1. fast routine selling flow
2. controlled exception governance
3. manager review
4. executive escalation

without making every quotation artificially slow.
