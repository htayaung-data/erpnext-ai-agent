# Sales Console Live Data Slice

Status: accepted  
Date: 2026-03-27  
Decision owner: UI workstream

## 1. Decision

Add a guarded bootstrap API for `Sales Console` and wire the page shell to live data only where the current site contract is reliable enough.

## 2. What This Slice Adds

1. permission-aware bootstrap method for the page
2. live counts for quotations, open sales orders, workflow-based approval queues, and user follow-up tasks where supported
3. explicit unavailable states for metrics that still require a business-approved contract

## 3. Why This Is Enterprise-Safe

This slice does not invent hidden finance logic or assistant behavior.

Instead it:

1. reads only what the current user can access
2. keeps unsupported metrics visibly pending
3. avoids leaking restricted counts
4. preserves the existing UI shell while moving toward production data

## 4. Metrics Still Deliberately Deferred

1. finance-owned credit exposure logic
2. branch performance rollups requiring approved branch contract
3. showroom-specific role variants
4. AI embedding

## 5. Next Slice

The next slice should focus on:

1. stronger sales queue semantics
2. branch-aware summary contracts
3. role-variant rendering inside the console
