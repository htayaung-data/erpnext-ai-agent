# Sales Console ERP Capability Audit

Status: current-state ERP reality audit for `Sales Console`  
Scope: live DocTypes, fields, workflow, permissions, reports, gaps, and card feasibility  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md)

## 1. Purpose

This document audits what the live ERP site actually supports for `Sales Console`.

It exists to separate:

1. target enterprise design
2. current ERP reality
3. implementation decisions that are safe now
4. ERP structure changes that must happen before some cards can become fully truthful

This document should be used before adding more console formulas or navigation behavior.

## 2. Audit Method

The audit is based on live ERP metadata and configuration observed from the site, including:

1. DocType field lists
2. active workflows
3. workflow states and transitions
4. DocPerm role permissions
5. existing reports
6. existing custom fields
7. actual role names present on the site

This audit focuses on structural capability, not on whether enough transaction records have already been entered.

## 3. Executive Summary

### 3.1 What is structurally strong right now

The live ERP already supports these areas well enough for immediate or near-immediate console use:

1. `Quotation`
   - has `status`
   - has `valid_till`
   - has `workflow_state`
   - has an active approval workflow
2. `Sales Order`
   - has strong operational status fields
   - has delivery and billing progress fields such as `per_delivered` and `per_billed`
   - has delivery date
3. `ToDo`
   - has `allocated_to`
   - has `reference_type`
   - has `reference_name`
   - is suitable for phase-1 follow-up counting
4. `Opportunity`
   - has `status`
   - has `sales_stage`
   - has `expected_closing`
   - has `probability`
   - is a strong candidate for future console expansion
5. `Customer`
   - has `territory`
   - has `account_manager`
   - has credit-limit-related structures
   - can support scoped customer opening and later risk modeling

### 3.2 What is structurally weak right now

These are the most important current ERP gaps:

1. `Quotation` and `Sales Order` do not expose a direct `branch` field in metadata
2. some planned report targets do not exist under the expected names
3. role separation is improved, but branch-scoped and team-scoped governance is not yet fully modeled in core sales documents
4. current live records still need seeded exception cases for stronger demo evidence

### 3.3 Most important implication

The current `Sales Console` design is directionally correct, but some cards are only partially implementable until ERP structure catches up.

So the right implementation pattern is:

1. implement what is structurally truthful now
2. use controlled fallbacks where possible
3. add workflow or custom structure only for business-critical gaps
4. do not fake blocked/approval logic where the ERP does not model it yet

## 4. Live ERP Findings

### 4.1 Actual sales-related roles found on the site

Live role names currently present:

1. `Sales User`
2. `Sales Manager`
3. `Sales Master Manager`
4. `Executive Approver`

Implication:

1. the normalized design roles can be mapped onto real site roles
2. but the console should use site-role mapping carefully rather than assuming the design labels already exist exactly

### 4.2 Workflow findings

Live active workflows found:

1. `Quotation Approval - MMOB`
   - active on `Quotation`
   - workflow state field: `workflow_state`
2. `Sales Order Approval - MMOB`
   - active on `Sales Order`
   - workflow state field: `workflow_state`

Live `Quotation` workflow states:

1. `Draft`
2. `Pending Sales Approval`
3. `Pending Executive Approval`
4. `Approved`
5. `Rejected`

Live `Quotation` workflow transitions:

1. `Sales User`
   - `Draft` -> `Approved` for routine quotation
   - `Draft` -> `Pending Sales Approval` for exception quotation
   - `Rejected` -> `Approved` for routine resubmission
   - `Rejected` -> `Pending Sales Approval` for exception resubmission
2. `Sales Manager`
   - may approve manager-level exception quotations
   - may escalate larger quotation exceptions to `Pending Executive Approval`
   - may reject
3. `Executive Approver`
   - may approve or reject escalated quotations

Implication:

1. `Quotation` approval cards are structurally valid
2. `Sales Order` blocked-approval cards are now structurally valid
3. visible blocked-order counts still depend on live orders actually entering those workflow states

### 4.3 Custom-field findings

Relevant live custom fields found:

1. `Quotation.workflow_state`
2. `Sales Order.workflow_state`
3. `User.assistant_enabled`

Still not found as custom sales-control structures:

1. custom sales branch field on `Quotation`
2. custom sales branch field on `Sales Order`

### 4.4 Field capability findings

#### Quotation

Live support confirmed for:

1. `status`
2. `valid_till`
3. `workflow_state`
4. `opportunity`
5. `owner`
6. `territory`

Missing for direct console scoping:

1. `branch`

#### Sales Order

Live support confirmed for:

1. `status`
2. `delivery_date`
3. `per_delivered`
4. `per_billed`
5. `owner`
6. `territory`
7. `customer`

Missing for direct approval modeling:

1. none after workflow rollout

Missing for direct branch scoping:

1. `branch`

#### ToDo

Live support confirmed for:

1. `allocated_to`
2. `status`
3. `reference_type`
4. `reference_name`

Implication:

1. follow-up cards can be built on real structure now

#### Customer

Live support confirmed for:

1. `territory`
2. `account_manager`
3. `customer_group`
4. `credit_limits`

Implication:

1. customer scoping is supportable
2. customer credit-risk ideas may be possible later, but not yet through a simple direct card formula

#### Opportunity

Live support confirmed for:

1. `status`
2. `sales_stage`
3. `expected_closing`
4. `probability`
5. `territory`
6. `opportunity_owner`

Implication:

1. opportunity-based queue or KPI cards are structurally feasible and may be high-value additions later

### 4.5 Report findings

Live reports confirmed:

1. `Sales Analytics`
2. `Quotation Trends`
3. `Sales Order Trends`
4. `Sales Order Analysis`
5. `Item-wise Sales History`
6. `Territory-wise Sales`
7. `Sales Pipeline Analytics`
8. `Opportunity Summary by Sales Stage`
9. `First Response Time for Opportunity`
10. `Customer Credit Balance`
11. `Customer Acquisition and Loyalty`
12. `ToDo`

Planned report targets that do not currently exist under those names:

1. `Customer-wise Sales History`
2. `Open Orders`

Important nuance:

1. `Item-wise Sales Register` exists, but it is tied to `Sales Invoice` and `Accounts`
2. this makes it usable for historical review, but less ideal as a sales-console-first operational report

### 4.6 Permission findings

Live `DocPerm` shows:

1. `Sales User`
   - can read/create/write `Lead`, `Opportunity`, `Quotation`, `Sales Order`
   - currently has submit rights on `Quotation`
   - currently has submit rights on `Sales Order`
2. `Sales Manager`
   - can read/create/write `Lead`, `Opportunity`, `Quotation`, `Sales Order`
   - currently has submit rights on `Quotation`
   - currently has submit rights on `Sales Order`
3. `Executive Approver`
   - now has read/write/submit access on `Quotation` and `Sales Order`
   - does not have create/delete/cancel/amend authority on those sales transactions
4. `Sales User` now has read-only access on `Customer`
5. `Sales User` can read `Item`
4. `ToDo` is broadly open through role `All`

Critical implication:

1. the live permission model is now materially closer to the target role-separation design
2. `Quotation` and `Sales Order` approval roles are now aligned with the active workflows
3. deeper branch/team governance is still a later-phase refinement, not a phase-1 blocker

## 5. Card Capability Audit

### 5.1 Current card decision buckets

Use these buckets:

1. `Ready Now`
2. `Ready With Fallback`
3. `Needs ERP Structure`
4. `Needs Target Replacement`

### 5.2 Header KPI cards

| Card | Live ERP Support | Decision | Reason |
|---|---|---|---|
| `Awaiting Approval` | `Quotation.workflow_state` exists and active workflow exists | `Ready Now`, but current live counts may be zero until more workflowed quotations exist | Structurally correct card |
| `Open Orders` | `Sales Order.status` exists and active order statuses are available | `Ready Now` | Strong standard ERP support |

### 5.3 Queue cards

| Card | Live ERP Support | Decision | Reason |
|---|---|---|---|
| `Orders Blocked By Approval` | `Sales Order.workflow_state` exists and an active Sales Order workflow now exists | `Ready Now`, but live counts may remain zero until orders enter approval states | Structurally valid after workflow setup |
| `Sales Orders Pending Fulfillment` | `Sales Order.status`, `per_delivered`, `per_billed`, `delivery_date` exist | `Ready Now` | Strong operational support |
| `Quotations Waiting For Action` | `Quotation.status` plus workflow-state exclusion logic supported | `Ready Now` | Strong support |
| `Open Quotations Nearing Expiry` | `Quotation.valid_till` and `status` exist | `Ready Now` | Strong support |
| `Customer Follow-Up Tasks` | `ToDo.allocated_to`, `reference_type`, `reference_name`, `status` exist | `Ready Now` | Strong phase-1 support |

### 5.4 Reports and review links

| Link | Live ERP Support | Decision | Reason |
|---|---|---|---|
| `Sales Analytics` | exists | `Ready Now` | Direct match |
| `Customer-wise Sales History` | does not exist under that name | `Needs Target Replacement` | Must be replaced by a real report or filtered list |
| `Item-wise Sales Register` | similar report exists but is invoice-heavy | `Ready With Fallback` | Can be used, but not ideal as the final enterprise sales review surface |
| `Open Orders` | no exact report exists | `Ready With Fallback` | Use filtered `Sales Order` list as phase-1 destination |

## 6. Gap Analysis by Business Theme

### 6.1 Approval visibility gap

Target need:

1. show both quotation and sales-order approval bottlenecks

Live ERP reality:

1. `Quotation` approval is modeled
2. `Sales Order` approval is now modeled
3. current live records may not yet populate approval-state counts

Required next action:

1. seed or transition real exception orders into approval states for testing
2. keep runtime logic pointed at workflow-configured states so approval cards stay truthful even before many live records exist

### 6.2 Branch-scope gap

Target need:

1. branch-aware sales filtering

Live ERP reality:

1. `Employee` has branch
2. `Quotation` does not expose branch
3. `Sales Order` does not expose branch

Implication:

1. direct branch filtering on core sales documents is not currently reliable
2. phase-1 should use owner/team/territory logic where possible
3. if branch-level sales filtering is essential, a branch strategy must be defined:
   - custom field
   - customer/territory derivation
   - assignment-based logic

### 6.3 Role-separation gap

Target need:

1. staff create
2. managers approve
3. executives review escalations

Live ERP reality:

1. `Quotation` workflow partially supports this
2. `Sales Order` workflow now supports this
3. minimum live permissions are now tightened for:
   - `Sales User`
   - `Sales Manager`
   - `Executive Approver`

Implication:

1. phase-1 role separation is now good enough for demo
2. later governance work should focus on branch/team scope enforcement rather than basic approval-role separation

## 7. Meaningful Missing Card Candidates

These are not required immediately, but they are worth consideration because the live ERP already models them reasonably well.

### 7.1 Opportunities Closing Soon

Why it is meaningful:

1. `Opportunity` already has `expected_closing`
2. `Opportunity` already has `status`, `sales_stage`, and `probability`
3. the ERP already has opportunity-focused reports

Why it may deserve a future card:

1. it supports pipeline discipline before quotation stage
2. it is a strong manager and staff planning signal

Decision:

1. worth considering after current console cards are stabilized

### 7.2 Orders Due Soon

Why it is meaningful:

1. `Sales Order.delivery_date` exists
2. this is a stronger operational signal than generic open orders in some sales environments

Why it may deserve a future card:

1. supports customer expectation management
2. supports proactive follow-up on at-risk commitments

Decision:

1. strong future candidate

### 7.3 Executive Approval Quotations

Why it is meaningful:

1. `Quotation` workflow explicitly separates:
   - `Pending Sales Approval`
   - `Pending Executive Approval`

Why it may deserve a future card:

1. could improve manager/executive exception visibility
2. especially useful if escalations become frequent

Decision:

1. better treated first as a drill-down or filtered target under `Awaiting Approval`
2. separate card only if volume justifies it

### 7.4 Customer Credit Risk

Why it is meaningful:

1. business need is strong

Why it is not yet ready:

1. customer credit-limit-related fields exist
2. but a trustworthy sales-console card needs a clear formula combining:
   - receivable exposure
   - open order exposure
   - approval policy

Decision:

1. do not add yet
2. audit finance contract and exposure logic first

## 8. Recommended Implementation Decisions

### 8.1 Implement now

These cards are structurally safe to implement as real console cards:

1. `Open Orders`
2. `Sales Orders Pending Fulfillment`
3. `Quotations Waiting For Action`
4. `Open Quotations Nearing Expiry`
5. `Customer Follow-Up Tasks`
6. `Awaiting Approval` for quotations
7. `Orders Blocked By Approval` for sales orders

### 8.2 Keep with fallback for phase 1

These items may stay, but must be explicitly treated as fallback implementations:

1. `Orders Blocked By Approval`
   - live count may remain zero until exception orders actually enter approval states
2. `Open Orders` report target
   - fallback to filtered `Sales Order` list
3. `Item-wise Sales Register`
   - usable, but not ideal as the final operational sales review link

### 8.3 Replace or redesign

These should be changed before final enterprise-grade rollout:

1. `Customer-wise Sales History`
   - replace with:
     - a real existing report
     - a filtered sales-order/customer history list
     - or a custom report

### 8.4 ERP structure changes worth doing

These are justified if the business wants the target console fully realized:

1. tighten `Sales Order` role/approval permissions to match target governance
2. decide how branch should be represented on core sales documents if branch-specific sales control is required
3. define a real account-history target for `Customer-wise Sales History`

## 9. Final Judgment

The live ERP is already strong enough to support a meaningful `Sales Console`, but not every target card from the design can be treated as equally mature today.

The most important truths are:

1. `Quotation` approval is structurally ready
2. `Sales Order` approval is now structurally ready
3. operational sales-order and quotation queue cards are mostly strong
4. follow-up task modeling is good enough for phase 1
5. opportunity-based expansion is a meaningful next frontier
6. some planned review/report links need replacement with real site targets

So the correct implementation rule is:

1. use the current design as the target direction
2. implement only what the ERP can support truthfully now
3. elevate remaining business-critical gaps into ERP structure changes
4. do not fake blocked-order or approval logic when live records and permissions do not yet support the story fully
