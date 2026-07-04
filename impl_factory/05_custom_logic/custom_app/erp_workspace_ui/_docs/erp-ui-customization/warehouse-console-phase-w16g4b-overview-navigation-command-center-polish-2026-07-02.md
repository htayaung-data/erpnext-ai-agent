# Warehouse Console Phase W16G4B - Overview Navigation And Command Center Polish

Date: 2026-07-02

## Scope

W16G4B is a narrow source-side polish slice after W16G4A. It addresses Owner review findings on the Overview command center and first-click route reliability.

Included:
- Tighten custom Warehouse worklist route self-healing for first-click SPA navigation.
- Simplify visible Overview command-center card metadata.
- Render Start Warehouse Work as one responsive desktop grid instead of separate primary/secondary strips.
- Preserve custom workflow route boundaries.

Excluded:
- Dedicated Returns page redesign.
- Dedicated Internal Transfer page redesign.
- Dedicated Cycle Count page redesign.
- ERPNext document runtime.
- Stock, accounting, valuation, notification, Sales, Procurement, Finance, Inventory/Admin, or external-action behavior.
- Live alignment, restart, protected gate, release closure, or Warehouse Workspace Closure approval.

## Implementation Notes

The worklist page wrapper and shared Warehouse runtime now retry active worklist rendering on router changes, hash/popstate changes, animation frame, and delayed self-heal windows. This targets the observed blank first navigation where the URL and sidebar update but the worklist content does not appear until hard refresh.

The Overview command center still carries backend role metadata for audit and smoke assertions. The visible card UI no longer displays implementation labels such as Manager posture, Returns page, Count page, or Read-only as decorative badges. Queue cards keep operational counts; custom workflow cards act as direct navigation cards.

Start Warehouse Work now uses a single three-column desktop grid with responsive fallback, so all destinations read as one command surface.

## Boundary

No native ERPNext route is exposed. No Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, or Stock Reservation behavior is introduced. No stock movement, stock posting, valuation, accounting, commercial exposure, notification, email, portal, Sales runtime, or Procurement runtime behavior is introduced.

## Next

Proceed to focused source validation and Owner manual review after live alignment is explicitly approved. Dedicated page premium redesign remains a separate W16G4C+ track.
