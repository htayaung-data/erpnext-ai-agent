# Sales Console Deferred Tasks

Status: intentionally deferred follow-up backlog for `Sales Console`  
Scope: meaningful items that are not ignored, but delayed until the core demo implementation is stable  
Source authority: [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md), [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md)

## 1. Purpose

This document records important `Sales Console` work that is being deliberately deferred.

It exists so the team can say clearly:

1. this is not forgotten
2. this is not rejected
3. this is simply not phase-1 priority

The main rule is:

1. do not expand into these tasks until the core sales demo flow is stable and truthful

## 2. Defer Criteria

An item belongs in this document when:

1. it is meaningful for the final ERP product
2. it is not required to prove the phase-1 demo value
3. implementing it now would slow down the core sales console rollout

## 3. Deferred Items

### 3.1 Direct Branch Filtering on Sales Documents

Current status:

1. deferred

Why it is deferred:

1. `Quotation` and `Sales Order` do not currently expose a direct `branch` field in the live site metadata
2. current phase can still demonstrate meaningful sales behavior using:
   - owner scope
   - team scope
   - territory/customer context where available
3. branch-aware design remains important, but is not required to prove the first demo story

Why it still matters later:

1. multi-branch control is important for enterprise rollout
2. later branch-aware queue and KPI formulas will be stronger if branch is modeled directly
3. branch-driven management review becomes more trustworthy with explicit branch fields or approved derivation logic

Possible later implementation paths:

1. add direct custom `branch` field on `Quotation`
2. add direct custom `branch` field on `Sales Order`
3. derive branch from customer / employee / territory logic if business accepts the model
4. design a branch-governance rule before adding fields

Return trigger:

1. revisit after core demo flow is stable
2. prioritize earlier if multi-branch control becomes part of the formal demo script

### 3.2 Advanced Credit-Risk Sales Card

Current status:

1. deferred

Why it is deferred:

1. the concept is meaningful, but needs a trustworthy formula across:
   - customer receivable exposure
   - open order exposure
   - credit policy
   - approval policy
2. this is more finance-sensitive than the current sales demo needs

Return trigger:

1. revisit after approval workflow and permissions are stable

### 3.3 Dedicated Sales Follow-Up Worklist

Current status:

1. deferred

Why it is deferred:

1. `ToDo` already supports a good phase-1 fallback
2. a custom worklist is valuable, but not required for the first truthful demo

Return trigger:

1. revisit after the core queue cards and navigation targets are stabilized

### 3.4 Opportunity Expansion Cards

Current status:

1. deferred but promising

Why it is deferred:

1. `Opportunity` is structurally promising on the site
2. but the phase-1 console should first stabilize the quotation-to-order operating path

Potential future cards:

1. `Opportunities Closing Soon`
2. `Stalled Opportunities`
3. `High-Probability Opportunities`

Return trigger:

1. revisit after the current sales queue cards are fully trustworthy

## 4. Working Rule

Before reopening any deferred item, confirm:

1. core sales console formulas are stable
2. role-based behavior is stable
3. navigation targets are stable
4. the deferred item will improve business credibility, not just visual completeness
