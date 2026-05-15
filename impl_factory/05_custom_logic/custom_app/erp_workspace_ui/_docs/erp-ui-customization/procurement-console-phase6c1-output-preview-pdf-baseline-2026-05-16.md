# Procurement Console Phase 6C1 Output Preview/PDF Protected Baseline

Date: 2026-05-16
Final accepted commit: `933e2d3d79d489f31e1186a3e4dabf7b4150858f`
Branch: `feature/erpnext-ui-design`

## Business Purpose

Phase 6C1 establishes the first protected supplier-facing document output foundation for Procurement without opening supplier communication or operational lifecycle actions.

The phase gives buyers controlled preview and PDF output for saved managed RFQs and saved managed Purchase Orders while preserving the business boundary that both documents are still drafts in this phase:

- RFQ output is a supplier-specific draft sourcing document, not a sent supplier communication.
- Purchase Order output is an internal draft preview, not a supplier commitment.

## Scope Implemented

Phase 6C1 implements productized output foundation and preview/PDF wrappers only.

Implemented surfaces:

- Saved managed RFQ form output card.
- Saved managed Purchase Order form output card.
- RFQ supplier-specific preview.
- RFQ supplier-specific PDF download through the managed backend wrapper.
- Purchase Order internal draft preview.
- Purchase Order internal draft PDF download through the managed backend wrapper.
- Draft/status watermarks and filename rules.
- Backend permission, doctype, document, and supplier validation.
- Smoke coverage for productized preview behavior, PDF filename fragments, and forbidden native/lifecycle leakage.

## Explicit Scope Not Implemented

Phase 6C1 intentionally does not implement:

- Actual email/send.
- Submit.
- Approve or reject.
- RFQ-to-Supplier Quotation conversion.
- Supplier Quotation-to-Purchase Order conversion.
- Purchase Request or Material Request-to-Purchase Order conversion.
- Receive or Purchase Receipt.
- Bill or Purchase Invoice.
- Payment.
- Item Price mutation.
- Default Supplier mutation.
- Supplier portal invite.
- AI quotation intake.
- Supplier or Item master-data create/edit.
- Broad Procurement redesign.
- Sales Console changes.

## Supported Routes And Pages

Supported productized pages:

- Saved managed RFQ form: `/desk/procurement-console-rfq-form/<rfq-name>`
- Saved managed Purchase Order form: `/desk/procurement-console-purchase-order-form/<purchase-order-name>`

Output actions appear only on saved managed documents. New unsaved RFQ and PO forms must not show output cards or output actions.

Native ERPNext print/email UI is not an accepted primary UX for Phase 6C1.

## Output Location Rule

RFQ output:

- The output card appears only after the managed RFQ is saved.
- The card is titled `Supplier Communication`.
- The card is positioned below the RFQ item lines and uses the managed buying form visual language.
- The card contains productized preview and PDF actions only.
- Supplier communication/send remains deferred and non-actionable.

Purchase Order output:

- The output card appears only after the managed Purchase Order is saved.
- The card is titled `Document Output`.
- The card is positioned below the PO item lines and uses the managed buying form visual language.
- The card contains productized preview and PDF actions only.
- Supplier send remains deferred and non-actionable.

The output card may require scrolling below item lines on smaller screens. This is accepted for Phase 6C1 as long as the saved form remains stable and the card is reachable.

## RFQ Output Behavior

Accepted RFQ behavior:

- `Preview RFQ` opens a productized preview modal.
- `Download RFQ PDF` uses the managed backend wrapper.
- Output is supplier-specific.
- A supplier must be selected for RFQ preview/PDF when the RFQ has multiple suppliers.
- The preview shows selected supplier context only.
- The preview/PDF must not mix supplier addressee or contact context.
- The preview/PDF shows `Draft / Not sent`.
- The PDF filename includes the RFQ number, supplier identifier, and `DRAFT-NOT-SENT`.
- Email/send remains disabled/deferred and must not be active.

Accepted RFQ filename shape:

`<RFQ>-<supplier>-DRAFT-NOT-SENT.pdf`

## Purchase Order Output Behavior

Accepted Purchase Order behavior:

- `Preview Purchase Order` opens a productized preview modal.
- `Download PO PDF` uses the managed backend wrapper.
- The preview/PDF is internal draft output only.
- The preview/PDF shows `Draft / Not for supplier`.
- The PDF filename includes the Purchase Order number and `DRAFT-NOT-FOR-SUPPLIER`.
- Supplier send remains disabled/deferred and must not be active.
- The preview table is buyer/supplier-readable and limited to Phase 6C1 fields.

Accepted Purchase Order preview columns:

- Item
- Qty
- UOM
- Required By
- Warehouse
- Rate
- Amount

The PO preview must not expose irrelevant ERPNext operational/internal columns, including:

- Finished Good Qty
- Stock UOM
- Subcontracted Quantity
- Discount Amount
- Distributed Discount Amount
- Rate Of Stock UOM

Accepted PO filename shape:

`<PUR-ORD>-DRAFT-NOT-FOR-SUPPLIER.pdf`

## Productized Wrapper Rule

Phase 6C1 output must go through managed backend wrappers. Direct native print/email UI leakage is not accepted as the primary productized experience.

Protected rules:

- Preview/PDF calls are mediated by `erp_workspace_ui.procurement_console.document_output`.
- Preview modals render controlled productized preview content.
- Embedded native ERPNext `Print` and `Get PDF` controls must not appear inside preview modals.
- PDF download must happen through the productized `Download RFQ PDF` or `Download PO PDF` action.
- Native ERPNext print/email dialogs must not be embedded inside the managed preview modal.

## Backend Safety Contract

The backend owns output eligibility and output shaping.

Required backend rules:

- Require authenticated Procurement access.
- Allow only `Request for Quotation` and `Purchase Order` doctypes.
- Re-read the saved document server-side before output.
- Enforce ERPNext read permissions.
- Validate RFQ selected supplier belongs to the RFQ.
- Require RFQ supplier context for supplier-specific output.
- Shape preview HTML server-side so client code does not decide output business truth.
- Preserve PDF filename policy server-side.
- Do not create Communication records in Phase 6C1 preview/PDF.
- Do not submit, send, convert, receive, bill, pay, or mutate master data.

## Forbidden Actions

The following must not be exposed as active Phase 6C1 actions:

- Email/send.
- Submit.
- Approve/Reject.
- RFQ-to-Supplier Quotation conversion.
- Supplier Quotation-to-Purchase Order conversion.
- Purchase Request or Material Request-to-Purchase Order conversion.
- Receive / Purchase Receipt.
- Bill / Purchase Invoice.
- Payment.
- Item Price mutation.
- Default Supplier mutation.
- Supplier portal invite.
- AI quotation intake.

## Validation Evidence

Accepted implementation commit:

- `933e2d3d79d489f31e1186a3e4dabf7b4150858f`

Focused Phase 6C1 smoke:

- `/tmp/procurement-phase6c1-preview-repair-live-20260516T003000Z/procurement-phase6c1`

Accepted preview screenshots:

- RFQ preview: `/tmp/procurement-phase6c1-preview-repair-live-20260516T003000Z/procurement-phase6c1/manager-rfq-preview-1136.png`
- PO preview: `/tmp/procurement-phase6c1-preview-repair-live-20260516T003000Z/procurement-phase6c1/manager-po-preview-1136.png`

Protected workspace gate:

- `/tmp/protected-workspaces-20260515T175141Z`

Sales freeze inside protected gate:

- `/tmp/protected-workspaces-20260515T175141Z/sales-freeze-protection`

Source/live runtime hash:

- `document_output.py`: `d7f8ee7cd3a087d1f83bb0df8f71990bda9ceb69c60b229d8b077691c11fe6f6`

Acceptance facts:

- Owner manual review accepted.
- Controller Contract V3 accepted.
- Native embedded `Print` / `Get PDF` controls are removed from preview modals.
- PO preview no longer exposes irrelevant ERPNext internal columns.
- Sales freeze and protected workspace gate passed.

## Future Protection Rules

Any future work touching supplier-facing output must run:

- Focused Phase 6C1 smoke.
- Full protected workspace gate.
- Sales freeze if any shared runtime changes are involved.
- Manual screenshot review of RFQ preview and PO preview.
- Manual PDF filename/content review when output templates change.

Any future email/send phase must be separately designed and approved before implementation.

Future changes must not reopen supplier send, submit, approval, conversion, receiving, billing, payment, Item Price, Default Supplier, supplier portal, or AI intake behavior through incidental UI or backend changes.

## Known Limitations

- Actual email/send is not implemented.
- No Communication audit trail is created by preview/PDF in Phase 6C1.
- Output cards may require scrolling below item lines on smaller screens.
- PDF visual quality must continue to be manually reviewed when template logic changes.
- Native Open ERP Form remains governed by earlier managed-form baseline rules and is not expanded by Phase 6C1.
