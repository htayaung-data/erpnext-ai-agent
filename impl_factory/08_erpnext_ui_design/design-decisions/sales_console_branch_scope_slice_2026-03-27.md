# Sales Console Branch Scope Slice

Status: accepted  
Date: 2026-03-27  
Decision owner: UI workstream

## 1. Decision

Apply branch-aware scope to Sales Console metrics where the underlying doctype supports a `branch` field, and expose the scope mode clearly in the UI.

## 2. What This Slice Adds

1. server-side scope contract for the current user
2. branch-filtered metrics where supported by the doctype
3. explicit fallback to permission scope when branch filtering is not available
4. visible scope label in the Sales Console header

## 3. Why This Is The Right Enterprise Step

The design requires branch-aware visibility, but the system cannot assume every doctype is branch-filterable in the same way.

This slice keeps the behavior safe by:

1. applying branch filters only when the field exists
2. explaining when branch context exists but cannot be enforced in that metric
3. avoiding hidden scope assumptions

## 4. What Still Remains For Later

1. richer branch sales snapshot metrics
2. cross-branch comparison for management roles
3. branch-aware child-page defaults and prefill behavior

## 5. Next Slice

The next slice should strengthen:

1. queue semantics tied to business states
2. the first detailed child page in the Sales family
