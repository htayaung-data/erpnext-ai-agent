# Procurement Console Phase 6C2 Governed RFQ Email/Send Design Plan

Date: 2026-05-16
Baseline: Phase 6C1 output preview/PDF protected at `f6c43c46b2e4a5910825a360c8e55d10a277db09`
Design scope: research and planning only. No runtime implementation is included in this document.

## 1. Context

The protected Procurement baseline now includes:

- Phase 5A Managed Purchase Request.
- Phase 5B Managed RFQ.
- Phase 5C Managed Supplier Quotation.
- Phase 5D Managed Purchase Order.
- Phase 6C1 productized RFQ/PO preview and PDF wrappers.

Phase 6C1 deliberately kept RFQ and PO email/send disabled. RFQ send is the next lower-risk supplier-facing communication step because an RFQ asks suppliers for offers and is not a purchase commitment. PO send remains deferred because a PO is a supplier commitment and should wait for approval/submit governance.

## 2. Installed ERPNext Native RFQ Send Findings

Findings are from installed ERPNext/Frappe source in `/home/frappe/frappe-bench/apps` and current site metadata.

### 2.1 RFQ DocType lifecycle

Installed RFQ behavior:

- `Request for Quotation` is submittable.
- RFQ validation updates missing supplier email IDs from linked Contact records.
- While `docstatus < 1`, RFQ status is set to `Draft`.
- `on_submit` sets status to `Submitted`, resets supplier `email_sent` to `0`, sets supplier `quote_status` to `Pending`, and calls `send_to_supplier()`.
- The native RFQ form exposes `Send Emails to Suppliers` only when `docstatus === 1`.
- The native RFQ PDF action is supplier-specific and prompts for one supplier.

Installed code references:

- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
  - `validate()` sets draft status for docstatus below submitted.
  - `validate_email_id()` throws if a supplier selected for send has no email.
  - `on_submit()` immediately calls `send_to_supplier()`.
  - `send_to_supplier()` loops supplier rows where `email_id` exists and `send_email` is enabled.
  - `get_pdf(name, supplier, ...)` updates supplier part numbers for the selected supplier before PDF generation.
- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.js`
  - Native `Send Emails to Suppliers` button is visible on submitted RFQs.
  - Native `Download PDF` prompts for a supplier, print format, language, and letterhead.

Design implication: native ERPNext RFQ send is submit-driven. A managed send implementation that uses native submit must treat submit as an external communication trigger, not as a harmless state change.

### 2.2 Native supplier side effects

Native `send_to_supplier()` has side effects beyond sending an email:

- It validates supplier email ID.
- It calls `update_supplier_contact()`.
- If no User exists for the supplier email, native code creates a Website User.
- It links or creates Contact records for the supplier.
- It appends Portal User entries to Supplier documents when missing.
- It sends a portal link in the email body.
- It marks RFQ supplier rows as `email_sent = 1` after sending.
- It saves supplier child rows after setting contact/email state.

Design implication: Phase 6C2 must not call native RFQ send blindly. Portal user/contact mutation must be explicit policy, tested, and owner-approved.

### 2.3 Native email fields and attachments

Current RFQ metadata includes:

- `subject`: required, not allow-on-submit.
- `message_for_supplier`: required and allow-on-submit.
- `email_template`: link to Email Template.
- `send_attached_files`: attaches files already attached to the RFQ to each supplier email.
- `send_document_print`: attaches a document print to each supplier email.

Current `Request for Quotation Supplier` metadata includes:

- `supplier`: required.
- `contact`: allow-on-submit.
- `send_email`: allow-on-submit.
- `email_sent`: allow-on-submit.
- `quote_status`: allow-on-submit, values `Pending` and `Received`.
- `email_id`: not required.

Design implication: native ERPNext supports email template/message, attached files, document print, per-supplier send flags, and per-supplier send/quote tracking. The managed UI should surface these concepts deliberately rather than leaking the native form.

### 2.4 Current site readiness

Current site metadata:

- Email Account rows: one account, `Jobs`, with `enable_outgoing = 0`, `default_outgoing = 0`, `awaiting_password = 0`.
- RFQ Portal Menu Item: route `/rfq`, enabled for `Request for Quotation`.

Design implication: current live site is not email-ready. A Phase 6C2 implementation must show `Email unavailable` and block actual send until an outgoing Email Account is configured and validated.

### 2.5 Frappe email behavior

Installed Frappe behavior:

- `frappe.core.doctype.communication.email.make()` creates a `Communication` record and validates email permission on the referenced document.
- When `send_email=True`, Frappe checks for an outgoing Email Account and throws if none is available.
- Attachments are stored against the Communication as File records.
- Email Queue tracks recipient status values such as `Not Sent`, `Sending`, `Sent`, `Partially Sent`, and `Error`.
- Email Queue can be blocked by muted email settings, suspended queue defaults, or missing/invalid SMTP configuration.

Design implication: send status and audit should use Communication/Email Queue semantics, but the managed wrapper must preflight environment readiness so users do not experience silent send failure.

## 3. Official ERPNext/Frappe Documentation Findings

ERPNext RFQ documentation says supplier contact/email can be used for RFQ email and supplier portal access, and that submitting a saved RFQ triggers email to suppliers with `Send Email` enabled. It also describes supplier PDF/print behavior and Supplier Quotation replies in ERPNext. Source: https://docs.frappe.io/erpnext/request-for-quotation

ERPNext Email Account documentation says outgoing Email Accounts are required for system-sent transactional email and describes default outgoing account behavior and reply linking. Source: https://docs.frappe.io/erpnext/email-account

ERPNext Sending Email documentation says document email can attach a PDF, goes through Email Queue, and requires outgoing Email Accounts. Source: https://docs.frappe.io/erpnext/sending-email

These official docs align with the installed source: RFQ send is tied to supplier email/contact setup, supplier portal access, PDF/attachment behavior, Communication, and Email Queue readiness.

## 4. Enterprise Benchmark Findings

### SAP S/4HANA

SAP S/4HANA Manage RFQs supports creating RFQs and sending them through sourcing systems, the SAP Business Network, email, or print/mail. SAP also treats RFQ output and attachments as part of a governed sourcing process, and SAP documentation notes approval/release concepts for RFQs in some scenarios. Sources:

- https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/b6e67357efb1a86be10000000a4450e5.html
- https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/8a57feade137489098f59374c06f1e0e/c306b753128eb44ce10000000a174cb4.html

Pattern: RFQ send is an explicit external output step with supplier selection, output management, attachments, and possible approval/release before issue.

### Oracle Procurement / Sourcing

Oracle Sourcing documentation treats supplier invitation as an explicit negotiation step. Supplier contacts are selected in an invitation list; notifications are sent to identified supplier contacts. Source: https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/how-can-i-invite-suppliers-to-my-negotiation.html

Pattern: supplier invitation/send is contact-specific and auditable, not a loose email blast.

### Microsoft Dynamics 365 Supply Chain

Dynamics RFQ documentation describes creating and sending RFQs to one or more vendors, generating RFQ journals for each vendor, printing/archiving/sending reports according to print settings, and resend/amendment behavior. Source: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations

Pattern: sent RFQs create vendor-specific journals/reports, statuses, amendment/resend rules, and configured templates.

### Odoo

Odoo Purchase RFQ documentation shows a `Send by Email` compose flow with a Request for Quotation template and vendor email, moving the RFQ to `RFQ Sent`. It also tracks communications in the chatter. Source: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html

Pattern: email send is productized, template-driven, state-changing, and communication-tracked.

### Benchmark Summary

Across systems, RFQ send is not just a button. It usually includes:

- Explicit supplier/contact selection.
- Email template or output template.
- PDF/report attachment.
- Audit trail or communication log.
- Sent status.
- Resend/amendment rules.
- Environment/output configuration.
- Optional portal/network integration.

## 5. Current Project Fit Analysis

Current managed RFQ behavior:

- Managed RFQ saves an ERPNext draft RFQ only.
- Saved RFQ has productized preview/PDF output in Phase 6C1.
- RFQ preview/PDF is supplier-specific.
- Email/send is disabled/deferred.
- Submit, approval, conversion, supplier portal, and Supplier Quotation intake remain deferred.

Design options:

### Option A: Use ERPNext native submit + send_to_supplier

Pros:

- Strong ERPNext lifecycle alignment.
- Native `quote_status` and `email_sent` fields are used.
- Future RFQ-to-Supplier Quotation and supplier portal features align better with ERPNext.

Cons:

- `on_submit` automatically sends to supplier rows with `send_email` enabled.
- Native code can create Website Users, Contacts, and Supplier Portal User links.
- Submitted RFQ editing becomes constrained.
- Current live email account is not outgoing-enabled.
- Native send depends on portal settings and may throw if portal menu is unavailable.

Conclusion: good long-term alignment, unsafe as a first direct implementation without a governed ready/send path.

### Option B: Managed Ready-to-Send state, then productized email wrapper without ERPNext submit

Pros:

- Maximum productized control.
- Can avoid portal user creation.
- Can use Communication/Email Queue directly.
- Can provide clean readiness/error states.

Cons:

- Diverges from ERPNext native RFQ lifecycle.
- May confuse native RFQ status because ERPNext still sees draft.
- Future conversion and portal response features may require submitted RFQ later.

Conclusion: useful for readiness and dry-run phases; risky for actual external send unless the owner accepts a custom send lifecycle.

### Option C: Draft RFQ direct email/send

Pros:

- Fastest to implement.
- Keeps managed form editing simple.

Cons:

- Weak audit/status semantics.
- Conflicts with ERPNext documentation that submit triggers send.
- May create supplier confusion because an unsubmitted draft was externally sent.

Conclusion: not recommended.

### Option D: Keep send deferred and only support preview/PDF

Pros:

- Safest.
- Preserves Phase 6C1 baseline.

Cons:

- Does not complete supplier communication workflow.

Conclusion: acceptable only if the owner defers supplier communication; not the preferred strategic path.

## 6. Recommended Send Policy

Recommended Phase 6C2 direction: split the work and do not implement actual send in the first step.

Recommended policy for actual RFQ send, once approved:

- RFQ send must not be allowed from an unsaved RFQ.
- RFQ send should require a managed `Ready to send` gate before any external email leaves the system.
- `Purchase User` may prepare the send package but should not send externally by default.
- `Purchase Manager` should be the default role allowed to externally send RFQs.
- Owner may later approve Purchase User send if ERPNext permissions and business policy require it.
- Send can target one supplier or multiple suppliers, but each supplier must have explicit selection and validated email.
- A missing email for one supplier must not block preview/PDF for other suppliers, but must block that supplier from send.
- Partial send should be represented as `Partially sent` with per-supplier results.
- PDF should be attached per selected supplier using the supplier-specific Phase 6C1 PDF logic.
- Additional attachments should remain deferred until owner approves attachment policy; first actual send should include the RFQ PDF only.
- Subject/message can be editable in a controlled compose step, seeded from RFQ subject/message/template.
- Print format/letterhead selection should remain controlled by backend allowlists and should default to the Phase 6C1 productized output.
- Supplier portal invitations/user creation must remain blocked unless explicitly approved.
- Resend and revision/amendment should be deferred; initial implementation may show sent history but not resend.
- Communication record is mandatory for each supplier send attempt.
- Send must be blocked if outgoing email is unavailable or muted/suspended.

## 7. Submit / Status Recommendation

The central decision is whether send submits ERPNext RFQ.

Recommendation: Phase 6C2 should not jump directly to native submit/send. Implement a staged, owner-reviewed path:

1. Phase 6C2A: RFQ send readiness context and recipient panel only. No actual send.
2. Phase 6C2B: managed `Ready to send` review gate and dry-run validation. No external email.
3. Phase 6C2C: owner decision on actual send architecture after reviewing readiness/dry-run evidence.

Recommended target architecture for actual send: submit-compatible, but guarded.

- Do not allow direct draft send as the default production design.
- Treat external RFQ send as a lifecycle event, not just an email action.
- Prefer an explicit managed review/ready state before native submit or a custom send wrapper.
- If native ERPNext submit is used, the backend must control supplier `send_email` flags and document all portal/contact/user side effects before submit.
- If portal/contact/user side effects are not accepted, actual send should use a productized Communication wrapper and remain clearly marked as a custom managed send lifecycle until an ERPNext submit phase is designed.

Current owner decision needed before actual send implementation:

- Are native portal user/contact creation side effects acceptable?
- Should send submit the ERPNext RFQ immediately, or should Phase 6C2 stop at managed Ready-to-Send plus dry-run?

Until those are approved, do not implement external send.

## 8. UX / Product Contract

### 8.1 Saved RFQ Supplier Communication card

Add a governed send area to the existing saved RFQ Supplier Communication card without disturbing Phase 6C1 preview/PDF behavior.

Status labels:

- `Draft / Not sent`: saved RFQ, no ready/send state.
- `Email unavailable`: outgoing email account unavailable, muted, suspended, or invalid.
- `Ready to send`: all required checks pass and a Purchase Manager has marked it ready.
- `Sent`: all selected suppliers were sent successfully.
- `Partially sent`: some selected suppliers succeeded and some failed.
- `Send failed`: no selected supplier was sent successfully.

Actions:

- `Preview RFQ`: existing Phase 6C1 productized preview.
- `Download RFQ PDF`: existing Phase 6C1 controlled PDF.
- `Prepare Send`: opens productized send preparation panel.
- `Send RFQ`: hidden or disabled until actual send phase and policy are approved.
- `View Communication Log`: visible after send history exists or as an empty audit panel.

### 8.2 Recipient panel

Recipient rows should include:

- Supplier.
- Contact.
- Email.
- Selected checkbox.
- Email validity state.
- Missing-email state.
- Last sent status.
- Last sent timestamp.

Rules:

- Users must explicitly select recipients.
- Missing email rows are disabled with clear copy.
- One supplier row must not leak another supplier's PDF or addressee context.
- The panel must be readable at 1136px and 1440px.

### 8.3 Compose panel

Compose fields:

- Subject.
- Message.
- Include PDF, default enabled.
- Include additional attachments, deferred and disabled initially.
- Selected suppliers summary.
- Preview selected supplier PDF action.

Copy:

- Use buyer-facing wording.
- Avoid implementation terms like `docstatus`.
- Make external-send warning clear: `This will send the RFQ externally to selected supplier contacts.`

### 8.4 Confirmation step

Before actual send, show:

- RFQ number.
- Selected suppliers.
- Recipient email addresses.
- Subject.
- Attachments/PDF list.
- Outgoing email account status.
- Warning that this is external supplier communication.

### 8.5 Post-send state

After send:

- Show per-supplier result.
- Show sent timestamp.
- Show sent by.
- Show Communication record link or managed log entry.
- Show failure reason if any supplier failed.

Constraints:

- No native email dialog leakage.
- No native print dialog leakage.
- No supplier portal user creation unless explicitly approved.
- No conversion actions.
- No PO actions.
- No broad redesign.
- Existing Phase 6C1 preview/PDF layout remains protected.

## 9. Backend / API Design

Recommended module:

- `erp_workspace_ui/procurement_console/rfq_communication.py`

This may call shared helpers from `document_output.py` for supplier-specific PDF generation.

Proposed methods:

- `get_rfq_send_context(rfq_name)`
- `prepare_rfq_send(payload)`
- `send_rfq_to_suppliers(payload)`
- `get_rfq_communication_log(rfq_name)`

Payload fields:

- `rfq_name`
- `selected_suppliers`
- `subject`
- `message`
- `include_pdf`
- `include_attachments`
- `print_format`
- `letterhead`
- `dry_run`

Backend rules:

- Require authenticated user.
- Require Procurement role family.
- Enforce Purchase Manager/Purchase User policy from the approved business decision.
- Re-read RFQ from DB.
- RFQ must be saved.
- Validate RFQ status and ready/send gate server-side.
- Validate selected supplier rows belong to the RFQ.
- Validate recipient email syntax server-side.
- Validate outgoing email account exists and is enabled before send.
- Do not trust client-provided supplier list, status, sender, or PDF content.
- Generate PDF per supplier server-side.
- Create Communication record for each supplier send attempt.
- Record success/failure per supplier.
- Provide idempotency protection for double-clicks, such as a send token or server-side in-progress guard.
- Do not create portal users or supplier contacts unless owner-approved.
- Do not create Supplier Quotation, Purchase Order, Item Price, Default Supplier, Purchase Receipt, Purchase Invoice, or Payment.

## 10. Permission And Audit Matrix

| Actor | View send context | Prepare send | Mark ready | Actual send | View communication log | Resend |
| --- | --- | --- | --- | --- | --- | --- |
| Purchase Manager | Yes | Yes | Yes | Future approved phase only | Yes | Deferred |
| Purchase User | Yes | Yes | No by default | No by default | Yes | Deferred |
| Sales roles | No | No | No | No | No | No |
| Guest | No | No | No | No | No | No |
| Administrator | According to system policy | According to system policy | According to system policy | According to system policy | According to system policy | Deferred |

Audit fields:

- RFQ name.
- Supplier.
- Contact.
- Recipient email.
- Subject.
- Message snapshot or Communication reference.
- PDF filename.
- Attachment names.
- Sent by.
- Sent at.
- Outgoing Email Account.
- Communication name.
- Email Queue name if available.
- Status: success, failed, skipped, queued.
- Failure reason.

## 11. Email Environment Readiness Plan

Readiness checks:

- At least one enabled outgoing Email Account exists.
- Default outgoing Email Account exists or sender resolution is deterministic.
- Email queue is not suspended.
- Emails are not muted.
- Supplier selected rows have syntactically valid email addresses.
- RFQ has at least one supplier.
- Supplier-specific PDF generation succeeds in dry-run.

Current live readiness:

- Not email-ready. The only Email Account found is `Jobs`, and it is not outgoing-enabled.

UX fallback:

- Show `Email unavailable` status.
- Keep `Preview RFQ` and `Download RFQ PDF` enabled.
- Disable `Send RFQ` with clear copy: `Outgoing email is not configured. Configure an outgoing Email Account before sending RFQs.`
- Do not fail silently.

## 12. Test And Protection Plan

### Python tests

Required tests:

- Send context allowed for Purchase Manager.
- Send context allowed/read-only or prepare-only for Purchase User, depending policy.
- Sales roles denied.
- Guest denied.
- Missing outgoing email account returns `Email unavailable` and blocks send.
- Missing supplier email disables that supplier row.
- Selected supplier must belong to the RFQ.
- Supplier-specific PDF generated per selected supplier.
- No mixed supplier context in PDFs.
- Dry-run validates subject, message, selected recipients, PDF generation, and outgoing email readiness.
- Actual send cannot run when policy is not approved or environment is unavailable.
- Communication is mandatory in actual send phase.
- Partial failure is represented per supplier.
- No portal user creation when portal side effects are blocked.
- No conversion/lifecycle actions returned.

### Smoke tests

Required smoke:

- Saved RFQ card shows send readiness state.
- Recipient panel renders supplier/contact/email rows.
- Missing email state is visible and non-actionable.
- Preview RFQ still works.
- Download RFQ PDF still works.
- Send is disabled when email unavailable.
- No native email dialog appears.
- No native form leakage.
- No PO send is enabled.
- Protected workspace gate passes.
- Sales freeze passes.

Email-ready scenario, only when environment is configured:

- Prepare send succeeds.
- Confirmation step shows selected suppliers and attachments.
- Actual send creates Communication/audit records.
- Per-supplier success/failure is visible.
- Email body and PDF attachment are manually reviewed.

Manual checks:

- Email subject/body quality.
- PDF attachment quality.
- Supplier recipient correctness.
- Communication audit correctness.
- No accidental supplier portal account/contact creation unless approved.

## 13. Recommended Implementation Roadmap

### Phase 6C2A: RFQ Send Readiness Context

Scope:

- Backend readiness context.
- Supplier recipient panel.
- Email unavailable state.
- Missing email state.
- Preserve Phase 6C1 preview/PDF.
- No actual send.

Exclusions:

- No submit.
- No email send.
- No portal/user/contact mutation.

Validation:

- Python tests for readiness and permissions.
- Focused RFQ UI smoke.
- Protected workspace gate.
- Sales freeze.

### Phase 6C2B: Managed Ready-to-Send Review Gate

Scope:

- Purchase Manager marks RFQ ready to send after validation.
- Purchase User can prepare but not mark ready by default.
- Dry-run validates recipients, subject/message, PDF generation, and email environment.
- No external email.

Exclusions:

- No native submit.
- No actual send.
- No portal/user/contact mutation.

Validation:

- Ready-state tests.
- Dry-run tests.
- Smoke for status transitions.
- Protected workspace gate.

### Phase 6C2C: Send Architecture Decision

Scope:

- Owner decides between submit-compatible native lifecycle and custom Communication wrapper.
- Confirm whether portal user/contact side effects are approved.
- Confirm whether Purchase User may send.
- Confirm email environment readiness.

Exit requirement:

- No implementation until owner approves submit/portal policy.

### Phase 6C2D: Actual RFQ Send

Scope, after approval only:

- Productized confirmation step.
- Server-side send.
- Supplier-specific PDF attachment.
- Communication/Email Queue audit.
- Per-supplier result display.

Exclusions:

- No PO send.
- No RFQ-to-SQ conversion.
- No Supplier Quotation intake automation.
- No resend/revision unless separately approved.

### Phase 6C2E: Communication Log And Failure Handling

Scope:

- Managed communication log.
- Failure reasons.
- Retry readiness, not resend by default.
- Manual review of sent PDFs/emails.

## 14. Explicit Deferrals

Deferred beyond this design:

- Actual RFQ send implementation until owner approves readiness/submit/portal policy.
- RFQ resend/revision/amendment.
- Supplier portal enablement beyond existing ERPNext settings.
- Supplier Quotation intake from email or portal.
- RFQ-to-Supplier Quotation conversion.
- PO email/send.
- PO approval/submit.
- Receiving, billing, payment.
- AI supplier quotation intake.
- Broad Procurement workspace redesign.

## 15. Immediate Recommendation

Do not implement actual RFQ send next.

Recommended next implementation is Phase 6C2A: RFQ send readiness context and recipient panel with disabled send when email is unavailable. This gives the owner actionable visibility into supplier recipients, email configuration, and policy blockers without triggering native submit, emails, portal user creation, or contact mutation.

After 6C2A and 6C2B are reviewed, decide whether actual send should use ERPNext submit-compatible native behavior or a custom Communication wrapper.

## 16. References

Installed source references:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.js`
- `/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/communication/email.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_queue/email_queue.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_account/email_account.py`

Official/reputable references:

- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/request-for-quotation
- ERPNext Email Account: https://docs.frappe.io/erpnext/email-account
- ERPNext Sending Email: https://docs.frappe.io/erpnext/sending-email
- SAP S/4HANA Manage RFQs: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/b6e67357efb1a86be10000000a4450e5.html
- SAP S/4HANA RFQ release role reference: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/8a57feade137489098f59374c06f1e0e/c306b753128eb44ce10000000a174cb4.html
- Microsoft Dynamics 365 RFQ overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Oracle Procurement supplier invitations: https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/how-can-i-invite-suppliers-to-my-negotiation.html
- Odoo RFQ send documentation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
