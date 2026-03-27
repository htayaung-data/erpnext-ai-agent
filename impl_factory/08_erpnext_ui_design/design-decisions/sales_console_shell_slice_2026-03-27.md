# Sales Console Shell Slice

Status: accepted  
Date: 2026-03-27  
Decision owner: UI workstream

## 1. Decision

Implement the first `Sales Console` slice as a standard Frappe custom page shell inside `erp_workspace_ui`.

## 2. Why This Slice Comes First

This slice creates the production route and visual structure without prematurely coupling the console to:

1. live queue contracts
2. finance visibility rules
3. assistant runtime embedding
4. branch-aware data aggregation

That keeps the first implementation slice stable and reviewable.

## 3. What This Slice Includes

1. `sales-console` route and page asset
2. enterprise shell layout aligned to the design notes
3. quick action navigation to standard ERPNext doctypes where available
4. structural sections for queue, insight, reports, and AI assist

## 4. What This Slice Deliberately Excludes

1. live KPI queries
2. custom queue APIs
3. AI runtime integration
4. role-variant rendering logic
5. workspace metadata optimization

## 5. Next Slice

The next implementation slice should wire:

1. live sales work queue data
2. approval and blocker visibility contracts
3. branch-aware summary cards
4. controlled role-aware rendering
