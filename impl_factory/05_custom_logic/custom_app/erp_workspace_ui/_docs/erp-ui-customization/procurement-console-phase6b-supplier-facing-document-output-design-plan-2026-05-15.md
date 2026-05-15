# Procurement Console Phase 6B Supplier-Facing Document Output Design Plan

Date: 2026-05-15

Baseline context:

- Phase 6A full workspace evaluation is complete at `c7be59fd01566bf7d6effa48abda68702ef171b0`.
- Protected managed buying forms are complete: Phase 5A Purchase Request, Phase 5B RFQ, Phase 5C Supplier Quotation, and Phase 5D Purchase Order.
- Sales Console remains frozen and protected.
- This is a design/research plan only. It does not implement print, PDF, email, send, submit, approval, conversions, receiving, billing, payment, AI intake, supplier portal, or template changes.

## Executive Recommendation

Phase 6B should lead to a cautious, supplier-facing output program, not a single broad "send document" feature.

Recommended architecture:

- Build productized Procurement output wrappers around ERPNext/Frappe print, PDF, email, and Communication primitives.
- Do not expose direct native ERPNext print/email UI as the primary user experience.
- Do not build a custom PDF/email engine from scratch unless ERPNext print formats prove insufficient in visual review.
- Keep all output actions permission-aware, audit-aware, and gated by document status.

Recommended policy:

- RFQ print preview and PDF download should be Phase 6C-ready for saved managed RFQs, clearly marked `Draft / Not sent` until a governed send state exists.
- RFQ email/send should be a separate phase after a managed ready-to-send/submission policy is approved, because installed ERPNext supplier email flow sends only submitted RFQs and may create or link supplier portal users.
- PO print preview and PDF download should be Phase 6C-ready for saved managed POs as internal preview only, with `Draft / Not for supplier` labeling.
- PO email/send must stay deferred until PO approval/submit governance exists. A PO is a supplier commitment, and sending a draft PO would create commercial and legal risk.

Immediate next recommendation:

1. Phase 6C1: Productized output foundation plus RFQ/PO print preview and PDF download wrappers, preview-only with draft warnings.
2. Phase 6C2: Governed RFQ email/send design and implementation after deciding whether managed RFQ send requires ERPNext submit or a new managed ready-to-send gate.
3. Phase 6C3: PO supplier-send design after PO approval/submit governance. Do not email draft POs to suppliers.

## Research Method

Research used:

- Installed ERPNext/Frappe source inside the live backend container.
- Installed site metadata for Print Format, Letter Head, and Email Account records.
- Official ERPNext/Frappe documentation.
- Official or product-owner documentation from SAP, Oracle, Microsoft Dynamics 365, and Odoo.

Installed source references:

- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.json`
- `erpnext/buying/doctype/request_for_quotation_supplier/request_for_quotation_supplier.json`
- `erpnext/buying/doctype/request_for_quotation_item/request_for_quotation_item.json`
- `erpnext/buying/doctype/purchase_order/purchase_order.py`
- `erpnext/buying/doctype/purchase_order/purchase_order.json`
- `erpnext/buying/doctype/purchase_order_item/purchase_order_item.json`
- `frappe/www/printview.py`
- `frappe/utils/print_format.py`
- `frappe/core/doctype/communication/communication.py`
- `frappe/desk/form/load.py`
- `frappe/email/doctype/notification/notification.py`

## ERPNext Native Findings

### Request For Quotation

Installed required RFQ header fields:

- `naming_series`
- `company`
- `transaction_date`
- `suppliers`
- `items`
- `message_for_supplier`
- `status`
- `subject`

Installed required RFQ Supplier child fields:

- `supplier`

Native RFQ supplier-facing behavior:

- RFQ validates supplier list, duplicate suppliers, zero quantity, and supplier email data.
- RFQ includes supplier communication fields such as `email_template`, `message_for_supplier`, `send_attached_files`, `send_document_print`, and `select_print_heading`.
- `on_submit()` sets RFQ status to `Submitted`, initializes supplier email status, and calls `send_to_supplier()`.
- `send_supplier_emails(rfq_name)` checks portal availability and sends only when `rfq.docstatus == 1`.
- `supplier_rfq_mail()` can attach current files and document print output with `frappe.attach_print`.
- RFQ email uses `frappe.core.doctype.communication.email.make(..., send_email=True, doctype=self.doctype, name=self.name)`, which links the communication to the RFQ.
- Native RFQ supplier email may create or link Contact records, create Website User records, and maintain Supplier portal user state.
- RFQ has a `get_pdf(...)` whitelisted method that calls Frappe `download_pdf` after updating supplier-specific print context.
- Native RFQ-to-Supplier Quotation mapping validates submitted RFQ state. This matches the existing Phase 5C decision to defer conversion.

Official ERPNext RFQ documentation aligns with the installed code:

- RFQ is sent to one or more suppliers asking for quotation.
- Supplier email and supplier portal behavior depend on contact/email data.
- ERPNext describes saving draft first, then submitting RFQ to trigger supplier emails.
- RFQ print/PDF can be supplier-specific; standard print preview uses first supplier data, while Download PDF asks for a supplier.
- Attachments can be included in supplier emails.

Phase 6B implication:

- Productized RFQ preview/PDF can reuse ERPNext/Frappe print/PDF primitives.
- Productized RFQ send cannot simply expose native send in the current managed draft workflow. Native send is tied to submitted RFQ and portal behavior.
- Any managed RFQ send must explicitly decide whether it submits RFQ, requires a new managed ready-to-send gate, or stays blocked.

### Purchase Order

Installed required PO header fields:

- `title`
- `naming_series`
- `supplier`
- `company`
- `transaction_date`
- `currency`
- `conversion_rate`
- `items`
- `status`

Native PO facts:

- PO validates supplier state and supplier scorecard restrictions.
- PO includes supplier address/contact/email fields, tax category, taxes and charges, terms, payment terms template, and print heading fields.
- PO lifecycle methods include `on_submit()`.
- Native mappings/actions to Purchase Receipt and Purchase Invoice validate submitted PO state.
- ERPNext documentation describes Purchase Order as a binding supplier contract and instructs users to save and submit.
- ERPNext documentation says submitted PO can create Purchase Receipt, Purchase Invoice, Payment Entry, and Journal Entry.
- PO print settings include letterhead, grouping same items, and print headings.
- PO terms and conditions are intended to appear in printed documents.

Installed site metadata:

- Installed PO Print Formats:
  - `Drop Shipping Format`
  - `Purchase Order Standard`
  - `Purchase Order with Item Image`
- No installed RFQ-specific `Print Format` row was returned from the site query; RFQ can still use standard/default print rendering.
- Letter Heads present:
  - `Company Letterhead`
  - `Company Letterhead - Grey`
- Outgoing Email Account query returned `Jobs` with outgoing disabled, so actual email sending readiness must be separately validated before enabling supplier send.

Phase 6B implication:

- PO preview/PDF can use ERPNext/Frappe print/PDF primitives and installed PO formats.
- PO email/send should not be allowed from draft managed POs. Sending a PO is supplier commitment behavior and should wait for approval/submit governance.
- PO output should include terms, taxes, signature/authorization state, and a clear status/watermark.

### Frappe Print, PDF, And Communication

Installed Frappe primitives:

- `frappe.utils.print_format.download_pdf` validates print permission and renders with `frappe.get_print(..., as_pdf=True)`.
- `frappe.www.printview` loads documents with permission checks and resolves print format and letterhead.
- `Communication` records and form timeline loading support linked communications by `reference_doctype` and `reference_name`.
- Frappe Notification supports templated email notifications, but Phase 6B should prefer explicit productized send actions over background notification rules for supplier-facing RFQ/PO send.

Official Frappe documentation confirms:

- Frappe supports print formats and PDF conversion for documents.
- Print formats use Jinja templates and can be customized.
- ERPNext Letter Head is used for company name, logo, address, header, and footer on print output.

Phase 6B implication:

- The right base is a productized wrapper over Frappe print/PDF/Communication APIs, with explicit Procurement policy gates.
- The implementation must not trust client state for status, recipients, send permissions, or document eligibility.

## Enterprise ERP Benchmark

### ERPNext

RFQ:

- RFQ can be emailed to suppliers and can include attachments and document print output.
- Native supplier email is tied to submitted RFQs and supplier portal/contact behavior.
- Supplier responses can become Supplier Quotations.

PO:

- PO is a binding supplier contract.
- PO supports print settings, letterhead, terms, taxes, and downstream receipt/invoice/payment flows after submit.

Takeaway:

- ERPNext already has useful primitives, but managed UI must gate send carefully because native behavior mixes email, portal access, contact creation, and submitted document state.

### SAP S/4HANA Cloud

PO:

- SAP uses output management and Output Parameter Determination for purchase order output.
- Output settings include output type, channel, receiver, email recipient, email settings, form template, printer settings, and output relevance.
- SAP supports channels such as email, print, EDI, and external output management.

RFQ:

- SAP sourcing/procurement treats RFQ and supplier quotation communication as governed sourcing output, not as a casual form action.

Takeaway:

- Supplier-facing output should be driven by configurable output policy, recipients, templates, and channels.

### Oracle Procurement

RFQ:

- Oracle Sourcing invitations can notify supplier contacts with email and PDF.
- Supplier contacts may receive invitations with or without supplier portal accounts.
- Offline supplier responses can be recorded by the buyer when suppliers do not respond in the portal.

PO:

- Oracle has a Communicate Purchasing Document process for printing PDF purchase orders or communicating them by fax/email using document communication preferences.
- Oracle supports purchase order PDF delivery as an email attachment through configured collaboration messages and delivery methods.

Takeaway:

- Enterprise PO/RFQ output is auditable, recipient-aware, template-driven, and commonly tied to explicit communication processes rather than raw document form buttons.

### Microsoft Dynamics 365 Supply Chain Management

RFQ:

- Microsoft describes RFQ as a process to create and send RFQs to one or more vendors, receive/register bids, compare replies, and award.
- Vendor collaboration can let vendors view RFQs and enter bids directly.
- RFQ amendments and returns create journals/reports that are printed, archived, and sent according to print settings.

PO:

- Vendor collaboration includes Purchase order confirmation where vendors monitor and respond to POs.

Takeaway:

- RFQ/PO output should be linked to workflow status, vendor collaboration/audit, and print/archive settings.

### Odoo

RFQ/PO:

- Odoo Purchase treats RFQ as a vendor-facing document. Buyers can send by email using a compose popup and can print RFQ PDF.
- Sent RFQs move to an RFQ Sent stage.
- Confirming the RFQ creates a Purchase Order and later receiving/billing follows.
- Odoo tracks communications through chatter.

Takeaway:

- A productized email composer with default recipients/template/PDF attachment and visible communication history is the expected modern ERP pattern.

## Current Project Fit

Current managed documents:

- Managed RFQ saves draft RFQ only.
- Managed PO saves draft PO only.
- Submit/approval is deferred.
- Conversions are deferred.
- Supplier portal is deferred.
- AI quotation intake is deferred.
- Native Open ERP Form is governed after save.

Design constraints:

- Output actions must appear only after a managed RFQ/PO is saved.
- Current draft managed RFQ/PO records should not imply that suppliers have been contacted.
- Current draft managed PO should not be sent to suppliers because PO is a purchase commitment.
- Productized output must not expose direct native create pages or uncontrolled native mutation actions.

Policy answers:

- RFQ draft print preview: allowed in Phase 6C as preview-only.
- RFQ draft PDF download: allowed in Phase 6C as preview-only with `Draft / Not sent` marking.
- RFQ draft email/send: not allowed until a governed ready-to-send/submission policy is approved.
- PO draft print preview: allowed in Phase 6C as internal preview-only.
- PO draft PDF download: allowed in Phase 6C as internal preview-only with `Draft / Not for supplier` marking.
- PO draft email/send: blocked until future PO approval/submit governance exists.
- Send means actual external email plus Communication audit record. It must never be simulated by UI state alone.

## Business Policy Matrix

| Document | Action | Phase 6C allowed | Future after governance | Forbidden for now | Policy |
| --- | --- | --- | --- | --- | --- |
| RFQ | Print preview | Yes | - | - | Saved managed RFQ only; mark draft/not sent. |
| RFQ | Download PDF | Yes | - | - | Saved managed RFQ only; use productized wrapper. |
| RFQ | Email/send | No | Yes | - | Requires governed RFQ submit/ready-to-send policy and recipient audit. |
| RFQ | Supplier portal invite | No | Yes | - | Defer because native flow may create users/portal access. |
| PO | Print preview | Yes | - | - | Saved managed PO only; internal preview. |
| PO | Download PDF | Yes | - | - | Saved managed PO only; watermark as draft/not for supplier until approved/submitted. |
| PO | Email/send | No | Yes | - | Requires PO approval/submit governance. |
| PO | Receive/bill/payment | No | Later lifecycle phase | Yes for Phase 6C | Operational lifecycle remains out of scope. |

## UX/Product Contract

### Shared Output Surface

Add supplier-facing output only to saved managed RFQ and saved managed PO surfaces. Do not show output actions on unsaved forms.

Use a compact `Supplier Communication` card or section on saved pages:

- Status: `Not sent`, `Preview only`, `Sent`, `Send blocked`, or `Communication unavailable`.
- Primary output policy reason when blocked.
- Recipients summary when available.
- Last communication timestamp and sender after send is later implemented.
- Recent communication/audit list.

Do not crowd the main form action bar. Keep the managed form primary action hierarchy intact.

### Managed RFQ Saved Page

Allowed Phase 6C1 actions:

- `Preview RFQ`
- `Download RFQ PDF`

Deferred/disabled Phase 6C1 action:

- `Email suppliers`

Disabled copy:

- `Email send requires a governed RFQ send step. This draft has not been sent to suppliers.`

Future RFQ email/send dialog:

- Supplier recipient list with supplier, contact, email, send checkbox, and missing-email state.
- Subject from RFQ subject or email template.
- Message from RFQ message/template.
- Include PDF checkbox.
- Include attachments checkbox.
- Print format and letterhead selection if authorized.
- Confirmation summary before send.
- Final send creates Communication records and updates visible communication status.

RFQ warnings:

- Draft previews must show `Draft RFQ - Not sent`.
- Email send must not imply supplier response has been requested until Communication send succeeds.

### Managed PO Saved Page

Allowed Phase 6C1 actions:

- `Preview Purchase Order`
- `Download PO PDF`

Deferred/disabled action:

- `Email supplier`

Disabled copy:

- `Supplier send requires approved/submitted purchase order governance. This draft is not a supplier commitment.`

PO output requirements:

- Draft preview/PDF must show `Draft Purchase Order - Not for supplier`.
- Supplier, delivery location, required/schedule dates, currency, items, qty, UOM, rate, amount, taxes, totals, and terms must be clear.
- Do not show or expose Submit, Receive, Bill, Payment, Create Purchase Receipt, or Create Purchase Invoice actions in the productized output surface.

Future PO email/send dialog:

- Recipient from supplier contact/email or explicit buyer-selected contact.
- Subject and message template.
- Include approved PO PDF.
- Terms and conditions visible before send.
- Optional attachments after policy approval.
- Confirmation step that acknowledges supplier commitment.
- Communication record after successful send.

### Action Styling

- Preview and Download PDF are secondary productized actions.
- Send action, when eventually enabled, is a guarded primary action inside the Supplier Communication section, not in the core draft-save action bar.
- Disabled send state must be visibly disabled with concise reason copy.
- No destructive/danger styling unless later phases introduce cancel/void actions.

### Placement Rules

Output actions may appear in:

- saved managed RFQ page
- saved managed PO page
- RFQ Review page, if same policy and backend guard are used
- Purchase Order Follow-up detail, if same policy and backend guard are used

Output actions should not appear in:

- unsaved managed forms
- directories as direct send buttons
- overview cards as direct send buttons
- native create routes

## Template And Branding Requirements

### Shared Requirements

Supplier-facing documents need:

- company name and logo/letterhead
- document title
- document number
- document status/watermark when draft
- supplier name
- supplier contact and email when available
- buyer contact
- transaction date
- currency
- item table
- UOM
- page number
- generated timestamp
- footer with company contact/legal text if configured
- clear print/PDF layout at A4 portrait
- predictable page breaks for long item tables

Use ERPNext Letter Head and Print Format where possible. The installed site has letterhead records and PO print formats, so Phase 6C should first test the current formats before designing custom print templates.

### RFQ Template Requirements

RFQ output should include:

- RFQ subject
- supplier-specific addressee data
- requested items
- quantities and UOM
- required by / response date
- target warehouse only if business-safe to expose
- message for supplier
- terms and conditions
- quotation submission instructions
- attachment list
- draft/not-sent watermark until governed send exists

RFQ should normally not include supplier pricing because it is a request for offers, not an offer from the buyer.

### PO Template Requirements

PO output should include:

- purchase order number
- supplier and supplier address/contact
- buyer/company information
- delivery location/warehouse
- transaction date
- required/schedule dates
- item rows with qty, UOM, rate, amount
- taxes/charges and grand total
- payment terms and terms and conditions
- authorized signature/approval status when governance exists
- draft/not-for-supplier watermark until approved/submitted

Phase 6C must not send a PO document that looks like an approved supplier commitment unless approval/submit governance is implemented.

## Backend/API Design

Proposed module:

`erp_workspace_ui/procurement_console/document_output.py`

Proposed whitelisted methods:

- `get_document_output_context(doctype, name)`
- `get_document_print_preview_context(doctype, name, print_format=None, letterhead=None)`
- `download_document_pdf(doctype, name, print_format=None, letterhead=None)`
- `send_document_email(payload)`

Allowed doctypes:

- `Request for Quotation`
- `Purchase Order`

Payload model for `send_document_email`:

```json
{
  "doctype": "Request for Quotation",
  "name": "RFQ-0001",
  "recipients": [
    {
      "supplier": "SUP-0001",
      "contact": "CONTACT-0001",
      "email": "supplier@example.com",
      "include": true
    }
  ],
  "subject": "Request for Quotation RFQ-0001",
  "message": "Please provide your quotation.",
  "attachments": [],
  "include_pdf": true,
  "print_format": "Standard",
  "letterhead": "Company Letterhead",
  "dry_run": false
}
```

Backend validation rules:

- Require authenticated user.
- Require Procurement role family.
- Require ERPNext document read permission for preview/PDF.
- Require explicit output/send permission for send.
- Deny Sales-only users and Guest.
- Re-read document from DB server-side.
- Do not trust client-provided status, supplier list, recipients, or print eligibility.
- Validate doctype allowlist.
- Validate document exists and is visible to user.
- Validate recipient emails.
- Reject send if no explicit recipient is selected.
- Reject PO send while PO is draft or unapproved.
- Reject RFQ send until governed RFQ ready-to-send/submission policy exists.
- For PDF, call Frappe print/PDF APIs with server-side permission checks.
- For send, create Communication records through Frappe email/Communication APIs.
- Do not submit documents.
- Do not create Supplier Quotations.
- Do not create Purchase Orders from RFQ/SQ.
- Do not receive, bill, pay, update Item Price, or set Default Supplier.

Output context response:

```json
{
  "doctype": "Purchase Order",
  "name": "PO-0001",
  "status": "Draft",
  "communication_status": "Preview only",
  "can_preview": true,
  "can_download_pdf": true,
  "can_send": false,
  "send_block_reason": "Supplier send requires approved/submitted purchase order governance.",
  "print_formats": ["Purchase Order Standard"],
  "letterheads": ["Company Letterhead", "Company Letterhead - Grey"],
  "recipients": [],
  "communications": []
}
```

## Permission And Audit Rules

Preview/download:

- Purchase Manager and Purchase User may preview/download only if ERPNext grants read/print access to the document.
- Sales-only and Guest are denied.
- Preview/download events do not need Communication records by default, but Phase 6C may add lightweight audit if owner wants print/download traceability.

Send:

- Send must require explicit permission beyond read.
- Send must be blocked for PO drafts.
- Send must be blocked for RFQ drafts until RFQ send governance is accepted.
- Send must create or link Communication records.
- Communication audit should show sent by, sent at, recipients, subject, delivery status, PDF/attachment inclusion, and error state.
- Resend/revision should be deferred until a revision policy exists.

Email readiness:

- Before enabling any send, validate outgoing email account configuration in the live site.
- Current installed site query showed outgoing disabled for the listed Email Account, so Phase 6C must include an environment readiness check and a graceful unavailable state.

## Native Reuse Versus Custom Wrapper Decision

Option A: Direct native ERPNext print/email routes/buttons

- Fastest.
- High native leakage risk.
- Exposes inconsistent UI and may surface Submit/portal/native actions.
- Not recommended as primary UX.

Option B: Productized wrapper using ERPNext/Frappe print/PDF/email/Communication APIs

- Reuses mature print/PDF/email primitives.
- Allows managed UI, permission gating, copy, warnings, audit panel, and protected smoke.
- Recommended.

Option C: Fully custom template/PDF/email engine

- Maximum control but unnecessary first step.
- Higher maintenance and PDF quality risk.
- Not recommended unless ERPNext print formats fail manual visual review.

Option D: Hybrid

- Productized wrapper around ERPNext/Frappe primitives.
- Use existing Print Format/Letter Head first.
- Add custom print formats later only where visual or legal requirements demand it.
- Recommended architecture.

## Test And Protection Plan

### Python Tests

RFQ:

- Purchase Manager preview allowed when read/print permission exists.
- Purchase User preview follows ERPNext permission.
- Sales-only/Guest denied.
- PDF route validates doctype allowlist.
- Missing RFQ denied cleanly.
- RFQ send blocked until governance flag/state exists.
- Missing supplier email returns validation state, not crash.
- Native supplier portal/user creation is not triggered by preview/PDF.

PO:

- Purchase Manager preview allowed when read/print permission exists.
- Purchase User preview follows ERPNext permission.
- Sales-only/Guest denied.
- PDF route validates doctype allowlist.
- PO draft send blocked.
- PO submitted/approved send remains unimplemented until owner-approved phase.
- No receive/bill/payment/create-invoice/create-receipt actions returned.

Communication:

- Send without explicit recipients rejected.
- Send creates Communication records only when send is enabled in a future phase.
- Communication list is permission-aware.
- Email account unavailable state is returned cleanly.

### Smoke Tests

RFQ saved managed page:

- Output card appears after save.
- `Preview RFQ` opens productized preview modal/page.
- `Download RFQ PDF` triggers controlled PDF route.
- `Email suppliers` is absent or disabled with approved block reason in Phase 6C1.
- Draft/not-sent watermark visible in preview.
- No native form leakage.
- No Submit/Send native action leakage.

PO saved managed page:

- Output card appears after save.
- `Preview Purchase Order` opens productized preview modal/page.
- `Download PO PDF` triggers controlled PDF route.
- `Email supplier` is absent or disabled with approved block reason.
- Draft/not-for-supplier watermark visible in preview.
- No Submit, Approve, Receive, Bill, Payment, Create Purchase Receipt, or Create Purchase Invoice actions.

Cross-workspace:

- Sales freeze protection passes.
- Protected workspace gate passes.
- Existing Phase 5A/5B/5C/5D smokes remain green.
- Screenshots at 1136px, 1240px, and 1440px verify output card placement and no layout regression.

### Manual Review Checklist

- PDF visual quality.
- Company branding and letterhead.
- RFQ wording does not imply commitment.
- PO wording does not imply approval when draft.
- Page breaks for long item tables.
- Item table alignment.
- Terms and conditions visibility.
- Supplier contact and recipient correctness.
- Email subject/body quality.
- Attachments and PDF inclusion.
- Audit/communication timeline visibility.

## Implementation Roadmap

### Phase 6C1: Output Foundation And Preview/PDF Wrappers

Scope:

- Add `document_output.py` backend wrapper.
- Add productized output context for saved managed RFQ and PO.
- Add productized preview modal/page.
- Add PDF download wrapper.
- Show disabled send states with clear business copy.
- Add draft watermarks/status labels.

Exclusions:

- No external email send.
- No submit/approval.
- No conversions.
- No portal.
- No receiving/billing/payment.

Validation:

- Python permission/output tests.
- Focused RFQ/PO output smoke.
- PDF manual visual review.
- Sales freeze.
- Protected workspace gate.

### Phase 6C2: Governed RFQ Email/Send

Dependency:

- Owner approval for RFQ send policy.
- Decide whether managed send submits RFQ, requires a managed ready-to-send state, or uses an ERPNext-compatible send wrapper after submit.
- Confirm outgoing email account readiness.

Scope:

- RFQ recipient panel.
- Email compose dialog.
- Include PDF and attachments.
- Communication record creation.
- Sent/failed audit state.

Exclusions:

- No Supplier Quotation conversion.
- No supplier portal unless explicitly approved.
- No automatic supplier/contact/user creation unless separately governed.

Validation:

- Email sandbox/manual verification.
- Communication audit verification.
- Negative tests for missing recipients/email account.
- Protected workspace gate.

### Phase 6C3: PO Print/PDF Preview Hardening

Scope:

- PO output template review.
- Terms/taxes/signature layout.
- PDF visual QA.
- Draft/not-for-supplier labeling.

Exclusions:

- No PO email/send.
- No submit/approval.
- No receive/bill/payment.

Validation:

- Manual PDF review with multi-line and tax cases.
- Protected workspace gate.

### Phase 6C4 Or Later: PO Email/Send

Dependency:

- PO approval/submit governance must be implemented and accepted first.

Scope:

- Email supplier only for approved/submitted PO.
- Recipient rules.
- Communication audit.
- Resend/revision policy if approved.

Exclusions:

- No receiving/billing/payment unless covered by separate lifecycle phase.

Validation:

- Strict permission and status gating.
- Email audit and PDF attachment verification.
- Protected workspace gate.

### Phase 6D: Procurement Workspace UI Polish/Redesign

Run after output design/preview foundation unless owner reprioritizes.

### Phase 6E Or Later: Conversion Workflows

Potential conversions:

- PR-to-RFQ
- RFQ-to-SQ
- SQ-to-PO
- PR/MR-to-PO

Must respect ERPNext submitted upstream document constraints and managed review/submit governance.

### Phase 6F Or Later: Operational Lifecycle

Potential lifecycle:

- submit/approval
- receiving
- billing
- payment
- warehouse/finance ownership boundaries

## Explicit Deferrals

Deferred from Phase 6B/6C1:

- RFQ email/send implementation.
- PO email/send implementation.
- RFQ submit.
- PO submit/approval.
- RFQ-to-Supplier Quotation conversion.
- Supplier Quotation-to-Purchase Order conversion.
- PR-to-RFQ conversion.
- PR/MR-to-PO conversion.
- Purchase Receipt creation.
- Purchase Invoice creation.
- Payment actions.
- Item Price mutation.
- Default Supplier mutation.
- Supplier/Item master-data mutation.
- AI supplier quotation intake.
- Supplier portal.
- Resend/revision policy.
- Broad Procurement redesign.

## Risks And Open Questions

- Outgoing email account readiness is not proven. Phase 6C must treat missing outgoing email as an unavailable state.
- ERPNext RFQ native send can create or link supplier contacts/users and depends on portal configuration. Productized send must not inherit that side effect without explicit owner approval.
- RFQ draft-send policy is unresolved. Installed ERPNext sends only submitted RFQs through `send_supplier_emails`.
- PO send requires approval/submit governance before implementation.
- PDF output quality depends on print formats, letterhead, PDF renderer behavior, and actual production data.
- Long item tables require manual PDF page-break review.
- Myanmar/local legal wording, tax layout, and authorized signature requirements need owner review before supplier-send.

## References

Installed source and site metadata:

- ERPNext RFQ source: `erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- ERPNext RFQ metadata: `erpnext/buying/doctype/request_for_quotation/request_for_quotation.json`
- ERPNext PO source: `erpnext/buying/doctype/purchase_order/purchase_order.py`
- ERPNext PO metadata: `erpnext/buying/doctype/purchase_order/purchase_order.json`
- Frappe print/PDF: `frappe/utils/print_format.py`, `frappe/www/printview.py`
- Frappe communication timeline: `frappe/core/doctype/communication/communication.py`, `frappe/desk/form/load.py`
- Installed PO print formats: `Drop Shipping Format`, `Purchase Order Standard`, `Purchase Order with Item Image`
- Installed letterheads: `Company Letterhead`, `Company Letterhead - Grey`

Official/product sources:

- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/request-for-quotation
- ERPNext Purchase Order: https://docs.frappe.io/erpnext/purchase-order
- Frappe Printing: https://docs.frappe.io/framework/v13/user/en/desk/printing
- ERPNext Letter Head: https://docs.frappe.io/erpnext/v13/user/manual/en/setting-up/print/letter-head
- SAP Purchase Order output parameter determination: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/1f58b66435ed4b15852fd934a644ba55.html
- SAP Manage Purchase Orders: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/38cbf557c328be12e10000000a4450e5.html
- Microsoft Dynamics 365 RFQ overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Microsoft Dynamics 365 vendor collaboration: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/vendor-collaboration-work-customers-dynamics-365-operations
- Oracle Communicate Purchasing Document: https://docs.oracle.com/en/cloud/saas/procurement/25d/faspp/communicate-purchasing-document.html
- Oracle Purchase Order PDF delivery: https://docs.oracle.com/en/cloud/saas/procurement/25c/oapro/configure-purchase-order-pdf-delivery-in-purchase-order.html
- Oracle supplier negotiation invitations: https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/how-you-invite-suppliers-to-negotiations.html
- Odoo Requests for Quotation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
