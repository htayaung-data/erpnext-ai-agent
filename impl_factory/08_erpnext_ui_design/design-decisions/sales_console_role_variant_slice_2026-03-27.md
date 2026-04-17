# Sales Console Role Variant Slice

Status: accepted  
Date: 2026-03-27  
Decision owner: UI workstream

## 1. Decision

Implement role-aware rendering inside the single `Sales Console` page instead of creating separate pages for each sales role too early.

## 2. What This Slice Adds

1. explicit role variants returned by the server contract
2. front-end rendering that changes action order, queue order, section notes, and showroom simplification
3. a single console shell that behaves differently for:
   - sales manager
   - sales executive
   - key account sales
   - showroom sales

## 3. Why This Is The Right Enterprise Step

This keeps the experience role-aware without fragmenting the product into multiple near-duplicate pages.

It also preserves:

1. one route
2. one implementation surface
3. one design family
4. clearer future maintenance

## 4. What Still Remains For Later

1. permission enforcement beyond visual rendering
2. stronger showroom-specific business restrictions
3. branch-sensitive queue prioritization
4. AI behavior that adapts by role

## 5. Next Slice

The next slice should strengthen:

1. branch-aware summary logic
2. queue semantics tied more closely to real business states
3. the first detailed child page, most likely quotation flow
