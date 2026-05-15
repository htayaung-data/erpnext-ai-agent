# Procurement Console Phase 5D Managed Purchase Order Baseline

Date: 2026-05-15

Accepted implementation commit: `42f218883d4230a0ae505af560424fd74a01ddc6`

## Purpose

This document closes Procurement Phase 5D as the stable protected baseline for managed Purchase Order direct draft entry.

Phase 5D completes the managed buying form family after the accepted Purchase Request, RFQ, and Supplier Quotation forms. It gives buyers a productized way to record Purchase Order draft details before operational processing. A Purchase Order is the buying document that can become a supplier commitment after ERPNext submission and downstream workflow, but this phase intentionally records draft Purchase Orders only.

Managed buying form family now protected:

- Phase 5A: managed Purchase Request for internal purchase demand capture.
- Phase 5B: managed RFQ for sourcing request draft capture.
- Phase 5C: managed Supplier Quotation for direct supplier-offer draft capture.
- Phase 5D: managed Purchase Order for direct supplier-order draft capture.

## Direct Draft-Entry-Only Decision

Phase 5D implements direct managed Purchase Order draft entry only.

This boundary is deliberate. Supplier Quotation-to-Purchase Order and Material Request/Purchase Request-to-Purchase Order conversions require governed upstream document state and native ERPNext mapping rules. Purchase Order lifecycle actions such as submit, approval, receiving, billing, and payment are operationally sensitive. They remain out of scope until separately designed, implemented, and protected.

## Accepted Scope

Phase 5D includes only the managed Purchase Order draft form and its productized create entry points:

- Managed Purchase Order form route for new draft entry.
- Managed Purchase Order form route for saved draft review/edit.
- Procurement Overview `New Purchase Order` action routes to the managed form.
- Purchase Order Directory `New Purchase Order` action routes to the same managed form.
- `Save Purchase Order` creates or updates an ERPNext draft Purchase Order using backend-owned validation and ERPNext document APIs.
- Supplier autocomplete is available and attached to the active supplier input.
- Item autocomplete is available and attached to the active item input.
- Warehouse autocomplete is available and attached to the active warehouse input where the field is shown.
- Empty item-line UOM displays `Derived` cleanly.
- Selected and saved item UOM values display cleanly.
- Quantity and rate drive the displayed amount.
- Item lines support add/remove behavior and remain stable with three or more lines.
- Header `Default Required By` drives inherited line required dates.
- Manually edited line dates remain manual and are not overwritten by later header date changes.
- Saved state shows the Purchase Order id and saved managed form actions.
- `Open ERP Form` appears only after save as a secondary governed native exception.

## Supported Routes And Entry Points

Accepted productized routes:

- Managed new route: `/desk/procurement-console-purchase-order-form/new`
- Managed saved route: `/desk/procurement-console-purchase-order-form/<name>`

Accepted productized create entry points:

- Procurement Overview action: `New Purchase Order`
- Purchase Order Directory action: `New Purchase Order`

The Overview action and Purchase Order Directory contextual action must continue to route to the same managed Purchase Order form route. They must not diverge into separate create flows.

Native ERPNext Purchase Order create pages are not productized primary create targets after this baseline.

## Role And Permission Support

Accepted roles:

- Purchase Manager
- Purchase User

Both roles may use the managed Purchase Order form only when ERPNext DocType permissions allow the corresponding read/create/write behavior.

Denied or restricted roles:

- Sales roles remain restricted unless the user also has the required purchase roles and ERPNext Purchase Order permissions.
- Guest and unauthenticated users remain restricted.

Security expectations:

- Procurement role family alone is not sufficient if ERPNext DocType permissions deny access.
- No broad permission bypass is allowed.
- The backend must continue to use ERPNext/Frappe document APIs and permission-aware checks.

## Save Behavior

Accepted save behavior:

- `Save Purchase Order` is the only primary mutation action.
- Save creates or updates a draft Purchase Order only.
- Save returns the saved Purchase Order name and routes to `/desk/procurement-console-purchase-order-form/<name>`.
- Submitted, cancelled, stopped, or otherwise non-draft Purchase Orders must not be edited through this draft-only managed form.
- Blank or invalid item lines must not silently create broken documents.
- Validation messages must remain clear if supplier, item, quantity, rate, or required date values are missing or invalid.

Forbidden save behavior:

- No submit.
- No approval or rejection.
- No cancel or stop.
- No receiving or Purchase Receipt creation.
- No billing or Purchase Invoice creation.
- No payment action.
- No Item Price update.
- No Default Supplier update.
- No Supplier or Item master-data mutation.

## UI/UX Contract

The managed Purchase Order form uses the shared managed buying form shell established by Phase 5A, Phase 5B, and Phase 5C.

Accepted UI contract:

- Compact enterprise header.
- Kicker: `Purchase Order`.
- New state title: `New Purchase Order`.
- Saved state title: saved Purchase Order id.
- Buyer-facing subtitle: `Record supplier order details before operational processing.`
- New state badge communicates new Purchase Order draft entry.
- Saved state badge communicates recorded Purchase Order state.
- Secondary badge communicates buying order context.
- Primary action: `Save Purchase Order`.
- Secondary actions: `Back to Purchase Orders`, `Reset`, and `Open ERP Form` after save.
- Shared managed-form action styling is used.
- No random gradients, one-off decorative backgrounds, or visual treatment outside the accepted managed form family.
- No duplicate Frappe page header, stale chrome, or stacked managed shells.
- No horizontal overflow at 1136px, 1240px, or 1440px.
- Layout remains clean with three or more item lines at laptop and desktop widths.

Item-line UI contract:

- Desktop/tablet row rhythm clearly separates item-line labels and fields.
- 1440px layout keeps column labels readable with no collisions, including `Line Required By` and `Warehouse`.
- 1136px layout remains clean with no clipping or overflow.
- Amount, UOM, Warehouse, Required By, Rate, Qty, and Remove remain readable and aligned.
- Per-row repeated labels are avoided at desktop/tablet widths where the shared header pattern is active.
- Mobile/narrow layouts may use inline labels if needed for readability.
- Remove action remains visible, secondary, and inside the viewport.
- Add/remove line behavior is stable.

Autocomplete contract:

- Supplier autocomplete floats above the form layer and attaches to the active supplier input.
- Item autocomplete floats above the form layer and attaches to the active item input.
- Warehouse autocomplete floats above the form layer and attaches to the active warehouse input.
- Autocomplete overlays are not clipped by cards or row containers.
- Autocomplete overlays do not shift the page layout.
- Item autocomplete should prefer opening below the active input when there is usable viewport space and must not cover the Save/Back/Reset toolbar or page header under normal laptop/desktop layouts.
- Overlay width remains aligned to the active input and does not create horizontal overflow.

Date behavior contract:

- Header `Default Required By` applies to new item lines.
- Line `Required By` can be manually overridden.
- Changing the header default date updates only inherited line dates.
- Manually edited line dates remain manual and are preserved.
- New lines inherit the current header default date.

UOM and amount contract:

- Empty/new UOM placeholder displays exactly `Derived`.
- Actual UOM values display cleanly after item selection and after save.
- UOM is read-only metadata, not an editable input.
- Amount is derived from quantity and rate for display and is validated through backend/ERPNext save behavior.

## Backend Contract

The managed Purchase Order backend owns business truth. Client-side display logic must not replace ERPNext/Frappe validation.

Accepted backend contract:

- Draft Purchase Order only.
- Permission-aware context load for new and saved Purchase Orders.
- Permission-aware save using ERPNext/Frappe document APIs.
- Supplier is required.
- At least one valid item line is required.
- Item code is required for each saved line.
- Quantity must be valid and greater than zero.
- Rate must be valid according to ERPNext Purchase Order expectations.
- Required/schedule date must be supplied where ERPNext requires it.
- UOM, stock UOM, and conversion factor are derived from ERPNext item behavior where possible.
- Amount is calculated consistently from quantity and rate.
- Company and currency are backend context and must not become prominent editable fields without owner approval.
- Error/state handling must remain explicit and must not mask permission, validation, unavailable, or technical failures.

## Native Exception And Leakage Boundary

`Open ERP Form` remains a governed native exception after a Purchase Order exists. It is not a primary create route and must not appear before save.

Productized create actions must not route to raw ERPNext Purchase Order create pages.

Forbidden labels/actions on the managed Purchase Order surface include:

- `Submit`
- `Approve`
- `Reject`
- `Cancel`
- `Stop`
- `Receive`
- `Create Purchase Receipt`
- `Bill`
- `Create Purchase Invoice`
- `Payment`
- `Pay`
- `Item Price`
- `Default Supplier`
- Supplier master-data mutation
- Item master-data mutation

## Explicitly Deferred Items

The following are not included in this baseline and remain deferred:

- Supplier Quotation-to-Purchase Order conversion.
- Material Request/Purchase Request-to-Purchase Order conversion.
- PR-to-RFQ conversion.
- RFQ-to-Supplier Quotation conversion.
- Purchase Order submit/approval/rejection workflow.
- Purchase Order cancel/stop lifecycle actions.
- Receiving and Purchase Receipt creation.
- Billing and Purchase Invoice creation.
- Payment workflow.
- RFQ email/print/send workflow.
- AI supplier quotation upload, OCR, extraction, or intake.
- Item Price mutation.
- Default Supplier mutation.
- Supplier or Item master-data create/edit.
- Broad Procurement workspace redesign or Phase 6 polish.

## Validation Evidence

Accepted final implementation and polish commit:

- `42f218883d4230a0ae505af560424fd74a01ddc6`

Focused Phase 5D final smoke:

- `/tmp/procurement-phase5d-autocomplete-placement-final-20260515T121000Z/procurement-phase5d`

Protected workspace gate:

- `/tmp/protected-workspaces-20260515T120612Z`
- Overall status: `pass`

Sales freeze evidence:

- Sales freeze passed inside the protected workspace gate.
- Artifact: `/tmp/protected-workspaces-20260515T120612Z/sales-freeze-protection`

Source/live runtime hash evidence:

- Purchase Order managed form JS source/live hash: `4835e4f747717890689f1d8754a03cf067658f372b984a0dd03328196903c6ed`

Manual/controller visual review:

- Owner manual check accepted the final managed Purchase Order form.
- Controller Verification Contract V3 accepted the final focused Phase 5D smoke and protected workspace gate.

Known untracked file note:

- `ui_smoke/sales_final_acceptance_audit.js` remains an allowed untracked file and is not part of this baseline closure.

## Future Protection Rules

Future changes touching managed Purchase Order behavior, shared managed form patterns, Procurement route registry entries, or primary Purchase Order create actions must run the focused affected smoke plus the full protected workspace gate.

Any shared runtime or shared CSS change must pass Sales freeze protection.

Future Phase 5D-adjacent work must preserve this baseline unless the owner explicitly approves a new scope and the protection tests are updated accordingly. This applies especially to Purchase Order conversion, submit/approval, receiving, billing, payment, Item Price, Default Supplier, and master-data mutation work.

After this closure, the managed buying form family is complete: Purchase Request, RFQ, Supplier Quotation, and Purchase Order. The next project step should be a full Procurement workspace evaluation or redesign planning pass, not immediate new feature implementation.
