# Sales Order Approval Policy Spec

Status: implementation-stage approval policy source of truth for `Sales Order`  
Scope: approval triggers, workflow intent, role ownership, and phase-1 rule design  
Source authority: [Sales-Console-Implementation-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Implementation-Plan.md), [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md)

## 1. Purpose

This document defines the phase-1 approval policy for `Sales Order`.

It exists to make `Sales Order` approval:

1. meaningful for the demo
2. enterprise-grade in control logic
3. simple enough to explain to business owners
4. simple enough to implement cleanly in ERPNext workflow

This policy is intentionally **exception-based**.

That means:

1. routine orders should move fast
2. only exceptional commercial orders should require approval

## 2. Policy Design Principles

The approval policy must follow these rules:

1. do not require approval for all sales orders
2. use only fields that the live ERP already exposes reliably
3. prefer simple header-level conditions over complex child-row logic in phase 1
4. make manager approval and executive escalation both visible in the demo
5. keep the workflow explainable in one short business conversation

## 3. Live ERP Inputs Used

The live site already supports these relevant `Sales Order` fields:

1. `grand_total`
2. `discount_amount`
3. `additional_discount_percentage`
4. `status`

The live site also shows current submitted order values such as:

1. `27,436,000`
2. `25,260,000`
3. `18,060,000`
4. `16,610,000`
5. `15,068,000`

This means the policy can use real thresholds that already produce believable demo cases.

## 4. Phase-1 Approval Decision

### 4.1 Routine orders

Definition:

1. lower-value order
2. no header-level commercial discount exception

Business treatment:

1. no approval queue
2. fast operational flow

### 4.2 Manager-approval exception orders

Definition:

1. commercially significant order
2. or order using a header-level discount exception

Business treatment:

1. must enter `Pending Sales Approval`
2. reviewed by `Sales Manager`

### 4.3 Executive-approval exception orders

Definition:

1. very large order
2. or major commercial discount exception

Business treatment:

1. must be escalated to `Pending Executive Approval`
2. reviewed by `Executive Approver`

## 5. Exact Phase-1 Trigger Rules

### 5.1 Sales User direct routine path

Allow direct routine approval path only when all are true:

1. `grand_total < 10000000`
2. `additional_discount_percentage == 0`
3. `discount_amount == 0`

Meaning:

1. small routine order
2. no explicit header-level discount exception

### 5.2 Trigger manager approval

Send order to `Pending Sales Approval` when any are true:

1. `grand_total >= 10000000`
2. `additional_discount_percentage > 0`
3. `discount_amount > 0`

Meaning:

1. either the order is large enough to deserve review
2. or it contains a visible commercial exception at header level

### 5.3 Manager can approve directly

Allow `Sales Manager` to approve when all are true:

1. `grand_total < 25000000`
2. `additional_discount_percentage < 10`
3. `discount_amount < 1000000`

Meaning:

1. manager may approve medium-value exceptions
2. manager may approve modest discount exceptions

### 5.4 Manager must escalate

Require escalation to `Pending Executive Approval` when any are true:

1. `grand_total >= 25000000`
2. `additional_discount_percentage >= 10`
3. `discount_amount >= 1000000`

Meaning:

1. very large order
2. or very large commercial discount exception

### 5.5 Executive approval

`Executive Approver` may:

1. approve escalated cases
2. reject escalated cases

## 6. Recommended Workflow States

Phase-1 workflow states:

1. `Draft`
2. `Pending Sales Approval`
3. `Pending Executive Approval`
4. `Approved`
5. `Rejected`

## 7. Recommended Workflow Role Ownership

### 7.1 Sales User

Allowed:

1. prepare draft order
2. send exception order for approval
3. complete routine path for non-exception order if policy allows

### 7.2 Sales Manager

Allowed:

1. approve manager-level exception orders
2. reject manager-level exception orders
3. escalate larger exception orders

### 7.3 Executive Approver

Allowed:

1. approve escalated orders
2. reject escalated orders

## 8. Why These Thresholds

### 8.1 Consistency with existing quotation governance

The live `Quotation` workflow already uses:

1. `10000000` as the manager-to-executive boundary trigger

So the proposed `Sales Order` policy keeps the same lower approval entry point for business consistency.

### 8.2 Better demo coverage

With current live order values:

1. several orders already sit above `10000000`
2. at least two orders already sit above `25000000`

This means the demo can naturally show:

1. routine orders
2. manager-review orders
3. executive-escalation orders

without inventing unrealistic values.

### 8.3 Simpler workflow implementation

This phase-1 design uses only header-level fields:

1. `grand_total`
2. `additional_discount_percentage`
3. `discount_amount`

This is intentional because child-row discount logic is possible but less reliable for a first workflow rollout.

## 9. Explicit Phase-1 Limitation

This phase-1 policy does **not** yet evaluate:

1. item-row `discount_percentage`
2. customer receivable exposure
3. credit-limit breach
4. margin erosion
5. overdue receivable risk

Reason:

1. those are meaningful enterprise controls
2. but they add complexity that is not required for the first truthful demo

## 10. Phase-2 Improvement Path

Later phases may add:

1. computed maximum line discount field on `Sales Order`
2. receivable or credit-risk based approval trigger
3. branch-specific approval chain
4. customer-group-specific approval thresholds

## 11. Final Judgment

This is the recommended phase-1 approval policy for the demo:

1. routine orders move quickly
2. large-value orders require manager review
3. very large or high-discount orders escalate to executive review
4. the workflow remains simple, explainable, and structurally supportable by the live ERP
