# Procurement Console Phase 6C2B RFQ Governed Send Design Plan

Date: 2026-05-16
Baseline: Phase 6C2A RFQ Send Readiness protected at `9450691b131489c5ef41aa886da8d78ed972e859`
Design scope: research and planning only. No runtime implementation is included in this document.

## Executive Recommendation

Do not expose ERPNext native RFQ send directly. Native ERPNext RFQ send is submit-triggered and can create supplier portal users, Contacts, Supplier portal links, Communication, Email Queue, and supplier-row state changes. That is too much side effect for a buyer-facing button without a governed send policy.

Recommended future implementation path:

1. Keep Phase 6C2A protected behavior unchanged until email setup is approved.
2. Prepare a company-owned outgoing email identity such as `procurement@company.com` or `buying@company.com`.
3. Implement a productized managed RFQ send wrapper only after owner approval.
4. Use a managed `Ready to send` gate before external email leaves the system.
5. Default external send permission to Purchase Manager only.
6. Send supplier-specific RFQ PDF to explicitly selected supplier contacts only.
7. Create auditable send records using Frappe Communication and Email Queue semantics, plus a productized send-history view.
8. Keep supplier portal user/contact creation blocked unless a separate owner-approved portal phase allows it.

Recommended policy for Phase 6C2B implementation after this design: implement governed RFQ send for saved managed RFQs with a managed `Ready to send` gate, explicit confirmation modal, supplier-specific PDF attachment, per-supplier audit trail, and no native email dialog. Do not implement PO send, conversions, submit/approval lifecycle, supplier portal, or resend/revision in the first send implementation.

## Baseline Context

Phase 6C2A is closed and protected. Current Supplier Communication supports:

- Supplier-specific RFQ preview.
- Supplier-specific RFQ PDF download.
- Recipient readiness panel.
- Controlled `Email unavailable` / readiness state.
- Disabled `Send RFQ`.
- RFQ Review page integration.
- No actual send/email side effects.

This design starts from that protected state. Future work must not weaken supplier-specific output, disabled send safety, RFQ Review integration, or New RFQ autocomplete placement.

## Installed ERPNext/Frappe Research Findings

Installed source was inspected in the live ERPNext/Frappe container under `/home/frappe/frappe-bench/apps`.

### ERPNext Request For Quotation

Installed code paths:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.js`
- RFQ metadata: `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.json`

Key native behavior:

- RFQ is submittable.
- `RequestforQuotation.on_submit()` sets `status` to `Submitted`, resets supplier row `email_sent` to `0`, sets `quote_status` to `Pending`, and calls `send_to_supplier()`.
- `send_to_supplier()` loops supplier rows where `email_id` exists and `send_email` is enabled.
- `validate_email_id()` throws if a selected supplier row has no email.
- `send_to_supplier()` calls `update_supplier_contact()` before sending.
- `update_supplier_contact()` creates a User if one does not already exist for the supplier email.
- `link_supplier_contact()` creates or updates Contact records, using `ignore_permissions=True`, and links a Supplier portal user to the Supplier.
- `get_link()` requires a Portal Menu Item route for `Request for Quotation` and generates supplier portal links.
- `supplier_rfq_mail()` renders supplier-specific subject/message, can include attached files, can attach document print output, and delegates send to Frappe email logic.
- Native RFQ `get_pdf(name, supplier, ...)` is supplier-specific and updates supplier part numbers before calling Frappe PDF download.

Native RFQ client behavior:

- Native `Send Emails to Suppliers` appears only when `frm.doc.docstatus === 1`.
- Native `Download PDF` prompts for a supplier, print format, language, and letterhead.
- Native `Supplier Quotation > Create` is also exposed on submitted RFQs.

Design implication: ERPNext native send is not only email delivery. It is coupled to submit, portal link generation, Contact/User/Supplier portal mutation, supplier row state updates, and native follow-on actions. A managed RFQ send implementation must wrap or replace that behavior deliberately.

### Frappe Communication And Email Queue

Installed code paths:

- `/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/communication/email.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/communication/mixins.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_queue/email_queue.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_account/email_account.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/__init__.py`

Key native behavior:

- `frappe.core.doctype.communication.email.make()` creates a Communication and checks `ptype="email"` permission on the referenced document.
- When `send_email=True`, it requires an outgoing Email Account and throws an outgoing email error when none exists.
- Communication email sending builds attachments, reply-to, sender, subject, content, and calls `frappe.sendmail()`.
- `frappe.sendmail()` builds Email Queue records.
- Email Queue status includes unsent, partially sent, sent, and error states.
- Email Queue sending is blocked when emails are muted, the queue is suspended, or no valid outgoing account exists.
- `EmailAccount.find_outgoing()` searches by sender, reference doctype, default outgoing account, or site config. It throws if configured to raise and no outgoing account exists.

Design implication: Communication and Email Queue are the right audit and delivery primitives, but the managed UX must preflight email availability and convert missing account/provider errors into productized states. Buyers must not see raw Frappe permission, outgoing-account, or server-error dialogs.

### Current Site Email Readiness

Current site query on `erpai_prj1` found one Email Account row:

- `Jobs`, `jobs@example.com`, `enable_outgoing = 0`, `default_outgoing = 0`, `enable_incoming = 0`, `append_to = Job Applicant`, `auth_method = Basic`.

The current site is not RFQ-send-ready. Future implementation must continue to show controlled `Email unavailable` until an approved outgoing account exists and is validated.

## Official ERPNext/Frappe Documentation Findings

ERPNext Request for Quotation documentation confirms the installed behavior: supplier Contact and Email Id are used for email and supplier portal access; the RFQ can use an Email Template; attachments can be sent; submitting an RFQ triggers email to suppliers with Send Email enabled; RFQ PDF output is supplier-specific; and native supplier email can create a Website User for supplier portal access.

ERPNext Email Account documentation confirms that outgoing Email Accounts use SMTP, require `Enable Outgoing`, and can be marked default outgoing. It also describes account email-as-sender, signatures, and outgoing email options.

Relevant official sources:

- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/request-for-quotation
- ERPNext Email Account: https://docs.frappe.io/erpnext/email-account

## Enterprise ERP Pattern Research

### SAP S/4HANA

SAP Manage RFQs supports adding bidders/suppliers, sending RFQs through SAP Ariba Sourcing, SAP Business Network, email, or printed mail, and checking output information. SAP Output Management treats business document output as configured print/email/external/EDI channels with templates and transmission monitoring.

Sources:

- SAP Manage RFQs: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/b6e67357efb1a86be10000000a4450e5.html
- SAP Output Management: https://help.sap.com/docs/SAP_S4HANA_CLOUD/a630d57fc5004c6383e7a81efee7a8bb/d7bd4b5d70d94f09bcf99b221a7a1688.html
- SAP Output Channels: https://help.sap.com/docs/SAP_S4HANA_CLOUD/a630d57fc5004c6383e7a81efee7a8bb/f4093514c55c4c739a64697f5d85354b.html

Pattern: RFQ send is output-managed, channel-specific, supplier/bidder-aware, and status-monitored.

### Oracle Procurement / Sourcing

Oracle Sourcing supplier invitations are contact-specific. Oracle documentation describes notifying invited supplier contacts, emailing a negotiation invitation and PDF, allowing contacts with or without portal accounts, and configuring From/Reply-To as either category manager email or generic organization email.

Source:

- Oracle How You Invite Suppliers to Negotiations: https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/how-you-invite-suppliers-to-negotiations.html

Pattern: supplier invitation is a governed negotiation action with explicit contacts, notification/PDF, access controls, and sender identity policy.

### Microsoft Dynamics 365 Supply Chain

Dynamics RFQ send generates an RFQ journal for each vendor. Print settings can archive reports or send reports to vendor email addresses. Dynamics supports resend/amendment flows and tracks sent/received/accepted/rejected status.

Source:

- Microsoft Dynamics 365 RFQs overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations

Pattern: each vendor gets a specific journal/report, send is configurable, and amendments/resends are controlled.

### Odoo

Odoo RFQ send opens a productized compose email popup with a purchase RFQ template and vendor email. Once sent, the RFQ moves to `RFQ Sent`; communications are visible in the chatter.

Source:

- Odoo Requests for quotation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html

Pattern: email send is template-driven, state-changing, and communication-tracked inside the document UI.

### Enterprise Pattern Summary

Major ERP systems treat RFQ send as a controlled external communication step. Common controls are:

- Draft preview before send.
- Explicit suppliers/recipients.
- Supplier-specific PDF/report package.
- Email template and editable message.
- Send confirmation.
- Auditable sent status.
- Resend/amendment rules.
- Permission/approval gate.
- No accidental supplier contact.

## Email Setup Recommendation

Use a company/domain mailbox for production ERP procurement sending. Preferred identities:

- `procurement@company.com`
- `buying@company.com`
- `sourcing@company.com`

Personal Gmail is not preferred for production ERP send because it ties supplier communications to an individual, weakens business continuity, complicates audit/reply ownership, and can expose personal identity in supplier-facing documents. A personal mailbox may be acceptable only for a temporary sandbox test after owner approval, never as the production sender.

Provider options:

- Google Workspace.
- Microsoft 365.
- Zoho Mail.
- Domain-hosting SMTP.
- A transactional provider later, if ERPNext/Frappe compatibility and business policy approve it.

Required technical data for future setup:

- SMTP host.
- SMTP port.
- TLS or SSL mode.
- Username/login ID.
- Password, app password, or OAuth credentials depending provider.
- From name.
- From email.
- Reply-to email.
- Whether account email must always be used as sender.
- Whether replies should be appended to Communication or another DocType.

DNS and deliverability requirements:

- SPF for authorized senders.
- DKIM signing for the sending domain.
- DMARC policy and reporting.
- MX records if the domain mailbox is also receiving mail.
- Bounce/reply monitoring plan.

Google Workspace notes:

- Google recommends email authentication for senders, including SPF or DKIM and DMARC for higher-volume sending.
- For apps/devices, Google recommends SMTP relay service rather than arbitrary personal mailbox SMTP where possible.
- OAuth or app-specific credential handling must be reviewed before implementation.

Microsoft 365 notes:

- SMTP AUTH may need to be enabled for the specific mailbox if ERPNext uses SMTP AUTH.
- Microsoft recommends careful authentication controls and DMARC/DKIM/SPF alignment for custom domains.

Zoho Mail notes:

- Zoho Mail supports custom-domain email hosting and provides MX, SPF, and DKIM setup steps.
- The owner must confirm regional SMTP settings and authentication requirements before ERPNext configuration.

Sources:

- Google Workspace SPF: https://support.google.com/a/answer/33786
- Google Workspace SMTP relay: https://support.google.com/a/answer/176600
- Microsoft 365 SMTP AUTH: https://learn.microsoft.com/en-us/Exchange/clients-and-mobile-in-exchange-online/authenticated-client-smtp-submission
- Microsoft 365 DMARC: https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dmarc-configure
- Zoho Mail hosting setup: https://www.zoho.com/mail/help/adminconsole/email-hosting-setup.html

Email subscription, payment, provider selection, DNS setup, SMTP/OAuth setup, and live ERPNext Email Account configuration remain deferred until implementation is explicitly approved.

## Governed RFQ Send Workflow

Future productized workflow:

1. Buyer opens a saved managed RFQ or RFQ Review page.
2. Supplier Communication shows supplier-specific preview/PDF and recipient readiness.
3. System verifies outgoing email is configured and safe to use.
4. System verifies supplier row belongs to the RFQ.
5. System verifies selected supplier has a valid contact/email.
6. System verifies the RFQ is saved and eligible under the selected status policy.
7. Send button remains disabled until readiness is green.
8. Buyer clicks `Send RFQ`.
9. System opens a confirmation modal showing:
   - Supplier.
   - Contact.
   - Recipient email.
   - RFQ number.
   - Supplier-specific PDF filename.
   - Email subject.
   - Message body preview.
   - Selected sender/from identity.
   - Reply-to identity.
   - Warning that the action will contact the supplier externally.
10. Buyer confirms send.
11. Backend re-reads RFQ and selected supplier row.
12. Backend regenerates supplier-specific PDF.
13. Backend creates approved audit/send records and queues/sends the email.
14. UI shows success, failure, or queued state.
15. Send history becomes visible on Supplier Communication.

Default send granularity: one selected supplier at a time.

Multi-supplier send can be designed later as an explicit package action, but it must still generate supplier-specific PDFs and per-supplier audit records. It must never generate one ambiguous PDF for multiple suppliers.

## Draft / Submission Policy Options

### Option A: Send saved draft RFQ with clear `Draft / Sent` status

Pros:

- Fastest productized send.
- Keeps managed RFQ editing simple.
- Avoids ERPNext native submit side effects.

Cons:

- Diverges from ERPNext documentation and native lifecycle.
- Weakens supplier trust because a draft document was externally sent.
- Creates custom status semantics that future agents must maintain.
- May complicate future RFQ-to-Supplier Quotation conversion if ERPNext expects submitted RFQs.

Decision: not recommended for production send.

### Option B: Require ERPNext submitted RFQ before send

Pros:

- Aligns with ERPNext native lifecycle.
- Supports native `email_sent` and `quote_status` semantics.
- Better future compatibility with supplier portal and RFQ-to-Supplier Quotation flow.

Cons:

- Native `on_submit()` immediately calls `send_to_supplier()`.
- Native send can create Website Users, Contacts, and Supplier portal links.
- Submitted RFQ editing is constrained.
- Requires careful suppression or governance of native side effects if productized send should control timing.

Decision: best long-term lifecycle alignment, but unsafe as a direct first implementation without a submit/send governance design.

### Option C: Add productized internal `Ready to send` gate before submit/send

Pros:

- Gives owner/buyer a controlled review point.
- Keeps external send disabled until readiness, policy, and confirmation pass.
- Allows preparation by Purchase User and approval/send by Purchase Manager.
- Lets implementation decide whether final send uses native submit, productized Communication/Email Queue, or a hybrid.

Cons:

- Requires a small managed state model or derived state.
- Adds implementation complexity.
- Still requires a future decision on whether/when ERPNext submit is invoked.

Decision: recommended staged path for this project.

Recommended policy: implement a managed `Ready to send` gate first. Actual send should be a separate step after readiness is green and Purchase Manager confirms. The first actual send implementation should use productized Communication/Email Queue wrappers and should not call native `send_to_supplier()` unless owner explicitly approves portal/contact/user side effects. A later submit-compatible phase can align with ERPNext lifecycle once submit side effects and future RFQ-to-SQ conversion are governed.

## Side-Effect Policy

Allowed only after owner approval for active send:

- Communication record.
- Email Queue entry.
- RFQ sent marker or managed send status.
- Send log table/custom DocType if needed.
- PDF attachment record or transient attachment reference.
- Per-supplier send result state.

Forbidden until separately approved:

- Contact creation.
- User creation.
- Supplier portal invitation.
- Supplier Portal User link mutation.
- Default Supplier mutation.
- Item Price mutation.
- Purchase Order creation.
- Submit/approval lifecycle action.
- RFQ-to-Supplier Quotation conversion.
- PR-to-RFQ conversion.
- SQ-to-PO conversion.
- PO send.

Policy detail: active RFQ send may create Communication/Email Queue because those are the auditable delivery primitives. It must not create Contacts or Users by default. Missing Contact/email must be a readiness error, not an automatic master-data mutation.

## UI/UX Contract

Supplier Communication card after email setup:

- Keep the card on saved managed RFQ form and RFQ Review route.
- Keep supplier selector when multiple suppliers exist.
- Keep `Preview RFQ`.
- Keep `Download RFQ PDF`.
- Add active `Send RFQ` only when readiness and permission policy pass.
- Reduce long readiness copy once send is active; keep concise policy copy and status chips.
- Do not crowd the main managed RFQ action bar.

Status chips:

- `Draft / Not sent`.
- `Ready to send`.
- `Sent`.
- `Partially sent` if multi-supplier send is later approved.
- `Failed`.
- `Email unavailable`.

Confirmation modal requirements:

- Productized modal only, not native email composer.
- Shows supplier, contact, email, RFQ number, PDF filename, subject, message body preview, sender/from, reply-to, and attachments.
- Requires explicit confirm action.
- Warns: `This will email the selected supplier.`
- Primary action: `Send RFQ`.
- Secondary action: `Cancel`.
- No hidden auto-send on modal open.

Error states:

- Missing supplier email.
- Invalid email.
- Supplier not part of RFQ.
- RFQ unsaved.
- RFQ not ready.
- Outgoing email unavailable.
- Email provider failure.
- Permission denied.
- Duplicate send in progress.
- PDF generation failure.

Visual rules:

- No native email composer leakage.
- No native print controls.
- No raw Frappe permission/server dialogs.
- No random gradients or one-off colors.
- Use the accepted managed form/shared card/button language.
- Fit 1136px laptop and 1440px desktop layouts.
- Avoid repeated labels in dense desktop rows.
- Ensure modal content scrolls internally without page overflow.

## Backend/API Contract

Likely module: `erp_workspace_ui/procurement_console/rfq_communication.py` or a send-specific section in `document_output.py`. A new module is preferred once actual send is implemented to keep preview/PDF wrappers separate from external communication side effects.

### `get_rfq_send_context(rfq_name)`

Input:

- `rfq_name`.

Output:

- RFQ identity, status, docstatus.
- Supplier rows from RFQ.
- Contact/email readiness.
- Outgoing email readiness.
- Current send status/history summary.
- `can_prepare`.
- `can_send`.
- Block reasons.
- Allowed actions.

Permission and validation:

- Authenticated user required.
- Procurement role required.
- ERPNext read permission for RFQ required.
- Sales roles and Guest denied.
- No mutation.

### `prepare_rfq_send(payload)`

Input:

- `rfq_name`.
- selected supplier.
- selected contact/email.
- print format/letterhead if allowed.
- include PDF flag.

Output:

- Confirmation context.
- Server-rendered subject.
- Server-rendered message preview.
- Supplier-specific PDF filename.
- Warnings/blockers.
- Idempotency token or send draft token.

Permission and validation:

- User may prepare only if policy allows.
- RFQ must be saved.
- Selected supplier must belong to RFQ.
- Recipient email validated server-side.
- Outgoing email must be available for active send preparation.
- No Communication or Email Queue created in prepare.

### `send_rfq_to_supplier(payload)`

Input:

- `rfq_name`.
- selected supplier.
- selected recipient email/contact.
- subject.
- message.
- include PDF.
- print format/letterhead.
- idempotency token.

Output:

- status: queued/sent/failed.
- supplier send result.
- Communication reference if created.
- Email Queue reference if created.
- sent_by / sent_at.
- productized error if failed.

Permission and validation:

- Purchase Manager send permission by default.
- ERPNext RFQ email permission required or explicit managed permission equivalent.
- Re-read RFQ and supplier row from DB.
- Do not trust client supplier list, status, email availability, or can_send.
- Validate idempotency token to prevent double-click duplicate send.
- Generate supplier-specific PDF server-side at send time.
- No native `send_to_supplier()` call unless a later owner-approved phase permits native side effects.

Expected side effects after approval:

- Communication record.
- Email Queue entry.
- Managed send log / sent marker.
- Optional File/PDF record if policy says to retain the sent PDF.

Forbidden side effects:

- Contact/User/Supplier Portal User creation.
- RFQ submit unless separately approved.
- Supplier Quotation or Purchase Order creation.

### `get_rfq_send_history(rfq_name)`

Input:

- `rfq_name`.

Output:

- Send attempts by supplier.
- sent_by, sent_at, recipient, subject, result, Communication/Email Queue refs.
- Failure reasons.
- Resend eligibility if later approved.

Permission and validation:

- Procurement read access.
- No mutation.

### `retry_rfq_send(payload)`

Deferred endpoint. Do not implement until resend/failure policy is approved.

## Permission Model

Recommended safest production model:

- Purchase Manager: may prepare and send RFQ after readiness is green.
- Purchase User: may view Supplier Communication, preview, download PDF, and prepare send context; actual send disabled unless owner explicitly approves Purchase User send.
- Sales roles: denied.
- Guest: denied.
- Administrator: allowed by system role but still subject to productized validation and no native leakage.

Rationale: RFQ is lower risk than PO but still contacts real suppliers externally. Purchase Manager-only send provides a defensible control while the organization is still establishing email identity, audit, and send policy.

## Audit Model

Every actual send attempt must be auditable.

Required audit fields:

- RFQ name.
- Supplier.
- Supplier contact.
- Recipient email.
- Sender/from account.
- Reply-to account.
- Subject snapshot.
- Message body snapshot.
- PDF filename/version.
- Attachments list.
- sent_by.
- sent_at.
- Result: queued/sent/failed.
- Failure reason.
- Communication reference if used.
- Email Queue reference if used.
- Provider/account used.
- Idempotency token or send attempt ID.
- Resend linkage if later approved.

No silent failures: a queued or failed email must be visible in Supplier Communication send history.

## Test And Smoke Plan

Python/unit tests:

- RFQ send context allowed for Purchase Manager.
- RFQ send context allowed for Purchase User but `can_send` false if policy is Manager-only.
- Sales/Guest denied.
- Missing outgoing Email Account blocks active send.
- Missing recipient blocks active send.
- Invalid email blocks active send.
- Selected supplier must belong to RFQ.
- Prepare send returns subject/message/PDF filename without side effects.
- Send requires saved RFQ.
- Send requires readiness green.
- Send requires Purchase Manager permission by default.
- PDF is generated per selected supplier.
- Communication/Email Queue created only by actual send endpoint, not by preview/prepare.
- No Contact/User/Supplier portal mutation.
- No RFQ submit/conversion/lifecycle action.
- Duplicate send token prevents double-click duplicate send.

Smoke tests:

- Existing Preview RFQ still works.
- Existing Download RFQ PDF still works.
- Supplier selector remains supplier-specific.
- Send remains disabled when email unavailable.
- Confirmation modal appears only when ready and authorized.
- Confirmation modal shows supplier/contact/email/RFQ/PDF/subject/message/warning.
- Confirm send in controlled email-ready environment creates visible send result.
- Failed provider response shows productized failure state.
- No native email composer.
- No native print/get-PDF controls.
- No raw Frappe permission/server modal.
- No Contact/User/portal creation.
- No PO send.
- Sales freeze passes.
- Full protected workspace gate passes.

Manual tests:

- Email body quality.
- PDF attachment quality.
- Sender/from and reply-to correctness.
- Recipient correctness.
- Supplier-specific PDF context.
- Audit/history correctness.
- No accidental supplier portal user creation.
- Actual mailbox receipt in a controlled test supplier mailbox before production supplier use.

## Implementation Roadmap

Recommended split after this design:

### Phase 6C2B-1: Email Setup Readiness Specification

Scope:

- Owner selects provider and official sender identity.
- DNS/SPF/DKIM/DMARC plan documented.
- ERPNext Email Account setup plan written.

Exclusions:

- No runtime send.
- No provider setup by agent unless separately approved.

Validation:

- Owner confirms sender identity and provider.

### Phase 6C2B-2: Managed Ready-To-Send Gate

Scope:

- Productized ready status, review checklist, and manager-only send eligibility.
- No external email.

Exclusions:

- No Communication/Email Queue.
- No submit.

Validation:

- Focused RFQ smoke and protected gate.

### Phase 6C2B-3: Composer And Dry-Run Confirmation

Scope:

- Productized confirmation modal and server-rendered send package preview.
- No external email.

Exclusions:

- No actual send.

Validation:

- Modal UX/manual review; no side effects.

### Phase 6C2B-4: Controlled Actual Send In Email-Ready Environment

Scope:

- Send to selected supplier only.
- Supplier-specific PDF attachment.
- Communication/Email Queue audit.
- Productized success/failure state.

Exclusions:

- No portal user/contact creation.
- No multi-supplier bulk send unless separately approved.
- No resend/revision.

Validation:

- Controlled test supplier mailbox receipt.
- Full protected gate.
- Owner manual email/PDF review.

### Later: Resend, Revision, Native Submit Alignment

Scope:

- Resend/failure handling.
- RFQ amendment policy.
- ERPNext submit-compatible lifecycle if approved.
- Future RFQ-to-Supplier Quotation flow.

Exclusions:

- PO send remains separate.

## Explicit Deferrals

Deferred from this design and any first implementation step:

- Actual email provider subscription/payment/setup.
- ERPNext Email Account configuration.
- Actual RFQ send implementation.
- PO send.
- ERPNext RFQ submit.
- Approval workflow.
- RFQ-to-Supplier Quotation conversion.
- PR-to-RFQ conversion.
- Supplier portal.
- Contact/User creation.
- AI quotation intake.
- Receive/bill/payment lifecycle.
- Broad Procurement redesign.

## Source Links And References

Installed source references:

- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- `/home/frappe/frappe-bench/apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.js`
- `/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/communication/email.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/core/doctype/communication/mixins.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_queue/email_queue.py`
- `/home/frappe/frappe-bench/apps/frappe/frappe/email/doctype/email_account/email_account.py`

Official/vendor documentation:

- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/request-for-quotation
- ERPNext Email Account: https://docs.frappe.io/erpnext/email-account
- SAP Manage RFQs: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/b6e67357efb1a86be10000000a4450e5.html
- SAP Output Management: https://help.sap.com/docs/SAP_S4HANA_CLOUD/a630d57fc5004c6383e7a81efee7a8bb/d7bd4b5d70d94f09bcf99b221a7a1688.html
- SAP Output Channels: https://help.sap.com/docs/SAP_S4HANA_CLOUD/a630d57fc5004c6383e7a81efee7a8bb/f4093514c55c4c739a64697f5d85354b.html
- Oracle supplier negotiation invitations: https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/how-you-invite-suppliers-to-negotiations.html
- Microsoft Dynamics 365 RFQs: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Odoo RFQ send: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
- Google Workspace SPF: https://support.google.com/a/answer/33786
- Google Workspace SMTP relay: https://support.google.com/a/answer/176600
- Microsoft 365 SMTP AUTH: https://learn.microsoft.com/en-us/Exchange/clients-and-mobile-in-exchange-online/authenticated-client-smtp-submission
- Microsoft 365 DMARC: https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dmarc-configure
- Zoho Mail hosting setup: https://www.zoho.com/mail/help/adminconsole/email-hosting-setup.html
