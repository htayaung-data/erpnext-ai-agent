# Procurement Console Phase 5C Managed Supplier Quotation Baseline

Date: 2026-05-15

Accepted source commit: `df2f0f90e5b93e2a4eaea39a7f8f032ac44dca8a`

## Purpose

This document closes Procurement Phase 5C as the stable protected baseline for managed Supplier Quotation direct draft entry.

Phase 5C records supplier offers manually for buyer review and later quote comparison or award decisions. A Supplier Quotation is a supplier offer captured in the Procurement Console. It is not a purchase commitment, does not send a request to a supplier, and does not create a Purchase Order.

This baseline extends the accepted Phase 5A/5B managed buying baseline:

- Phase 5A: managed Purchase Request for internal purchase demand capture.
- Phase 5B: managed RFQ for sourcing request draft capture.
- Phase 5C: managed Supplier Quotation for direct supplier-offer draft capture.

## Accepted Scope

Phase 5C includes only managed Supplier Quotation direct draft entry:

- Managed Supplier Quotation form.
- Procurement Overview `New Supplier Quotation` action routes to the managed form.
- Supplier Quotation Directory `New Supplier Quotation` action routes to the same managed form.
- `Save Quotation` creates or updates a draft Supplier Quotation using ERPNext document APIs.
- Supplier autocomplete is available and attached to the active supplier input.
- Item autocomplete is available and attached to the active item input.
- Quantity and rate update the displayed amount.
- Empty item-line UOM displays `Derived` cleanly.
- Selected and saved item UOM values, for example `Nos`, display cleanly.
- Item lines support add/remove behavior.
- Saved state shows the Supplier Quotation id, `Quotation Recorded`, and secondary actions.
- `Open ERP Form` appears only after save as a governed native exception.
- Productized `Review Quotation` remains available after save.

## Managed Routes And Entry Points

Accepted productized routes and actions:

- Procurement Overview action: `New Supplier Quotation`
- Supplier Quotation Directory action: `New Supplier Quotation`
- Managed new route: `/desk/procurement-console-supplier-quotation-form/new`
- Managed saved route: `/desk/procurement-console-supplier-quotation-form/<supplier-quotation>`
- Productized review route after save: `/desk/procurement-console-supplier-quotation-review/<supplier-quotation>`

The Overview action and Supplier Quotation Directory contextual action must continue to route to the same managed Supplier Quotation form route. They must not diverge into separate create flows.

Native ERPNext Supplier Quotation create pages are not productized primary create targets after this baseline.

## Business Flow

Direct Supplier Quotation creation is allowed in this phase. The buyer may record a supplier offer without first selecting an RFQ.

Accepted direct flow:

1. User opens Procurement Overview or Supplier Quotation Directory.
2. User selects `New Supplier Quotation`.
3. Managed Supplier Quotation form opens.
4. User selects supplier, transaction date, validity date, item, quantity, and rate.
5. Amount displays from quantity and rate.
6. User selects `Save Quotation`.
7. ERPNext creates a draft Supplier Quotation.
8. The managed form routes to the saved Supplier Quotation route.
9. `Open ERP Form` becomes available only as a secondary governed native exception after save.

Supplier Quotation remains an offer record for comparison and buyer review. It does not award business, send email, submit the document, or create a Purchase Order.

RFQ-linked Supplier Quotation remains deferred until a governed RFQ submit/review step exists. Phase 5C must not bypass ERPNext native mapping rules by copying draft RFQ rows into Supplier Quotations.

## Role And Permission Support

Accepted roles:

- Purchase Manager
- Purchase User

Both roles may use the managed Supplier Quotation form only when ERPNext DocType permissions allow the corresponding read/create/write behavior.

Security expectations:

- Procurement role family alone is not sufficient if ERPNext DocType permissions deny access.
- Non-purchase roles remain restricted by existing access rules unless they also hold required Procurement and ERPNext permissions.
- Guest and unauthenticated users remain restricted.
- No broad permission bypass is allowed.
- The backend must continue to use ERPNext/Frappe document APIs and permission-aware checks.

## Save Behavior

Accepted save behavior:

- `Save Quotation` is the only primary mutation action.
- Save creates or updates a draft Supplier Quotation.
- Save returns the saved Supplier Quotation name and routes to `/desk/procurement-console-supplier-quotation-form/<supplier-quotation>`.
- Blank or invalid item lines must not silently create broken documents.
- Validation messages must remain clear if required supplier, item, quantity, or rate values are missing.
- Submitted, cancelled, or non-draft Supplier Quotations must not be edited through this draft-only managed form.

Forbidden save behavior:

- No submit.
- No approval.
- No Purchase Order creation.
- No Item Price update.
- No Default Supplier update.
- No Supplier or Item master-data mutation.

## UI/UX Contract

The managed Supplier Quotation form uses the shared managed-form shell established by Phase 5A/5B.

Accepted UI contract:

- Compact enterprise header.
- Kicker: `Supplier Quotation`.
- New state title: `New Supplier Quotation`.
- Saved state title: saved Supplier Quotation id.
- Buyer-facing subtitle: `Record supplier offer details for buyer comparison.`
- New state badge: `New Quotation`.
- Saved state badge: `Quotation Recorded`.
- Secondary badge: `Buying offer`.
- Primary action: `Save Quotation`.
- Secondary actions: `Back to Supplier Quotations`, `Reset`, `Open ERP Form` after save, and `Review Quotation` after save.
- No random gradients or one-off decorative styling.
- No duplicate Frappe page header, stale chrome, or stacked managed shells.
- No horizontal overflow at 1136px, 1240px, or 1440px.

Item-line UI contract:

- Desktop/tablet header row: `Item | Qty | Rate | UOM | Amount | Action`.
- 1440px layout keeps the line in a clean single shared row.
- 1136px layout remains compact; Amount stays visually connected to quantity/rate in the same row rhythm.
- Per-row repeated labels are not visible at desktop/tablet widths.
- Mobile/narrow layouts may use inline labels if needed for readability.
- Remove action remains visible, secondary, and inside the viewport.
- Add/remove line behavior is stable.

Autocomplete contract:

- Supplier autocomplete floats above the form layer and attaches to the active supplier input.
- Item autocomplete floats above the form layer and attaches to the active item input.
- Autocomplete overlays are not clipped by cards or table containers.
- Autocomplete overlays do not shift the layout.

UOM and amount contract:

- Empty/new UOM placeholder displays exactly `Derived`.
- Actual UOM values display cleanly after item selection and after save.
- UOM is read-only metadata, not an editable input.
- Amount is derived from quantity and rate for display and saved through ERPNext validation.

## Native Exception And Leakage Boundary

`Open ERP Form` remains a governed native exception after a Supplier Quotation exists. It is not a primary create route and must not appear before save.

Productized create actions must not route to raw ERPNext Supplier Quotation create pages.

The following remain forbidden from the managed form surface:

- `Submit`
- `Approve`
- `Create Purchase Order`
- `Update Item Price`
- `Set Default Supplier`
- `Receive`
- `Bill`
- `Pay`

## Explicitly Deferred Items

The following are not included in this baseline and remain deferred:

- RFQ-to-Supplier Quotation conversion.
- PR-to-RFQ conversion.
- Managed Purchase Order form.
- RFQ send/email/print workflow.
- Supplier portal workflow.
- AI supplier quotation upload, OCR, extraction, or intake.
- Submit/approval/create-PO workflow.
- Item Price mutation.
- Default Supplier mutation.
- Supplier or Item master-data create/edit.
- Warehouse receiving.
- Purchase Invoice, billing, payment, or accounting execution.

## Validation Evidence

Accepted final implementation and acceptance repair commit:

- `df2f0f90e5b93e2a4eaea39a7f8f032ac44dca8a`

Focused Phase 5C live smoke:

- `/tmp/procurement-phase5c-live-final-20260515T060301Z/procurement-phase5c`
- Summary: `/tmp/procurement-phase5c-live-final-20260515T060301Z/procurement-phase5c/summary.json`
- Saved SQ screenshot: `/tmp/procurement-phase5c-live-final-20260515T060301Z/procurement-phase5c/manager-managed-sq-saved.png`

Protected workspace gate:

- `/tmp/protected-workspaces-phase5c-final-rerun-20260515T060924Z`
- Summary: `/tmp/protected-workspaces-phase5c-final-rerun-20260515T060924Z/protected-workspace-gate-summary.json`
- Overall status: `pass`

Sales freeze evidence:

- Sales freeze passed inside the protected workspace gate.
- Artifact: `/tmp/protected-workspaces-phase5c-final-rerun-20260515T060924Z/sales-freeze-protection`

Source/live runtime hash evidence:

- Supplier Quotation managed form JS source hash: `435f00a3450025d2243600449af3fb2a3ae796282ad3a88b305f3c492790eb60`
- Supplier Quotation managed form JS live hash: `435f00a3450025d2243600449af3fb2a3ae796282ad3a88b305f3c492790eb60`

Manual/controller visual review:

- Owner manual check accepted New Purchase Request, New RFQ, and New Supplier Quotation.
- Controller Verification Contract V3 accepted the final focused Phase 5C smoke and protected workspace gate.

Known untracked file note:

- `ui_smoke/sales_final_acceptance_audit.js` is a known allowed untracked file and is intentionally not part of this baseline commit.

## Future Protection Rules

Future Procurement work must treat Phase 5A, Phase 5B, and Phase 5C managed buying forms as protected baseline behavior.

Rules for future phases:

- Phase 5D must not alter Phase 5A/5B/5C behavior without explicit owner approval.
- Managed Purchase Order work must preserve the accepted Supplier Quotation form route, shell lifecycle, autocomplete behavior, UOM display, and saved-state action hierarchy.
- Any shared runtime, shared CSS, managed-form shell, action registry, or navigation change that can affect this baseline must pass Sales freeze and the protected workspace gate.
- If the Supplier Quotation managed form is touched, screenshots at 1136px, 1240px, and 1440px must be reviewed.
- Productized create actions must continue to avoid raw ERPNext native create-page leakage.
- New conversion work must use ERPNext native mapping/business validation and must not custom-copy rows around ERPNext workflow requirements without explicit owner approval.

## Future Phase Guidance

Recommended future sequence:

- Phase 5D: Managed Purchase Order form after Phase 5A/5B/5C are protected.
- Later governed phase: RFQ send/print/email workflow.
- Later governed phase: AI supplier quotation intake with human review.
- Later governed phase: RFQ-to-Supplier Quotation conversion once RFQ submit/review is governed.
- Later governed phase: Supplier Quotation-to-Purchase Order award/create workflow.

The broader Procurement workspace should not be redesigned or reprioritized until the managed buying form family is complete and protected.
