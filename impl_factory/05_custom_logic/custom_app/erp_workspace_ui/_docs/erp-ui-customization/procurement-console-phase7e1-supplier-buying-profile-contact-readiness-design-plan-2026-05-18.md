# Procurement Console Phase 7E1 Supplier Buying Profile And Contact Readiness Design Plan

Date: 2026-05-18

Branch: `feature/erpnext-ui-design`

Scope: docs-only design and research. No runtime Python, JavaScript, CSS, smoke script, Sales Console, live alignment, supplier/contact/user creation, RFQ send, submit/approval, conversion, receiving, billing, payment, Item Price, Default Supplier, supplier portal, SMTP, or AI intake implementation is included.

## Executive Summary

Phase 7D1 correctly removed raw ERPNext Supplier form escapes from normal Procurement Console workflows. That closure made the workspace safer, but it also exposed the next product gap: Purchase Managers need a controlled way to maintain buying-facing supplier readiness and RFQ recipient context without entering the broad Supplier master form.

Phase 7E1 should introduce a productized Supplier Buying Profile and Contact Readiness capability on Supplier Detail. Purchase Users remain read-only. Purchase Managers may update only an allowlisted Procurement-owned readiness profile. Supplier master fields, Contact records, User records, portal activation, accounting/tax/bank/payment fields, Item Price, Default Supplier, RFQ send, and lifecycle actions remain forbidden.

The recommended architecture is a companion custom app record, tentatively named `Procurement Supplier Readiness Profile`, keyed by Supplier, with a separate immutable `Procurement Supplier Readiness Log`. This avoids broad Supplier master mutation while giving managers a controlled place for buying notes, RFQ contact preference, recipient override if owner-approved, readiness status, and audit evidence. RFQ readiness should consume this profile as read-only data in a future implementation, while `Send RFQ` remains disabled until the governed send phase is separately approved.

## Governing Constraints From Current Baselines

- Phase 7D1 removed normal-role labels `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, and `Advanced ERP Form` from Procurement Console. This design must not restore them.
- Phase 6C2A protects RFQ Supplier Communication as preview/PDF/readiness only. `Send RFQ` remains visible but disabled/non-actionable.
- Phase 6C2B recommends governed RFQ send later, with explicit confirmation, audit, recipient validation, and no native ERPNext send exposure.
- Phase 6C2C corrected history by removing attempted test-send runtime. Current protected state must have no SMTP send runtime, no send endpoint, and no email-provider dependency.
- Phase 7E audit identifies Supplier Buying Profile and Contact Readiness as the next Purchase Manager capability gap after native escape closure.
- Sales Console is frozen/protected. Any future runtime implementation must pass Sales freeze if shared runtime changes are touched.

## Current Source Findings

Source inspected for this design:

- `erp_workspace_ui/procurement_console/suppliers.py`
- `erp_workspace_ui/procurement_console/supplier_detail.py`
- `erp_workspace_ui/procurement_console/document_output.py`
- `erp_workspace_ui/procurement_console/document_reviews.py`
- `erp_workspace_ui/procurement_console/managed_rfq.py`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_review_page.js`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_rfq_form.js`
- `erp_workspace_ui/workspace_governance_manifest.py`
- Procurement contract tests around Supplier Detail, RFQ readiness, and native escape closure

### Supplier Directory

`suppliers.py` exposes a read-only Supplier worklist. It reads `name`, `supplier_name`, `supplier_group`, `disabled`, and `modified`; filters by supplier, keyword, supplier group, and disabled status; and routes rows to productized Supplier Detail. It does not provide create/edit actions.

### Supplier Detail

`supplier_detail.py` is a read-only buying profile page. It shows supplier identity, group, active/disabled status, open PO/RFQ/quotation counts, recent and open purchase orders, RFQs, supplier quotations, and linked buying contacts. Actions are Back to suppliers and Refresh.

Linked contacts are read through `Dynamic Link` rows where `link_doctype = Supplier`, `link_name = supplier`, and `parenttype = Contact`, then displayed with `Contact` fields `name`, `first_name`, `last_name`, `email_id`, `phone`, `mobile_no`, and `modified`. No Contact or Supplier mutation is currently available.

### RFQ Readiness

`document_output.py` returns RFQ output and send-readiness context. It re-reads RFQ supplier rows from the Request for Quotation document and derives recipient readiness from this order:

1. RFQ Supplier row `email_id`.
2. Selected RFQ Supplier row `contact`, if present, through Contact.
3. First linked Supplier Contact through Dynamic Link.
4. Direct Supplier email-like fields (`email_id`, `contact_email`, `email`) when available.

Outgoing email account status is checked through a safe read path that returns a controlled unavailable state if Email Account cannot be inspected safely. The readiness response always returns `can_send: false`, a send block reason, supplier rows, recipient status, and future policy requirements.

### RFQ Form And Review UI

Managed RFQ and RFQ Review both show Supplier Communication after save or on a saved review page. The card includes Supplier context selection, Preview RFQ, Download RFQ PDF, recipient readiness, outgoing email state, and a disabled Send RFQ button. The UI does not expose native email composer or native print controls.

### Missing Manager Capability

After Phase 7D1, Purchase Managers can see that a supplier is missing email/contact readiness but cannot correct the buying-facing readiness inside Procurement Console. Reopening the raw Supplier form would also expose disabled status, supplier group, payment terms, tax fields, bank/accounting fields, portal users, contacts, and other master data. Phase 7E1 should fill only the buying-readiness gap, not restore full master-data edit power.

## ERPNext Data Model Findings

Installed ERPNext/Frappe source metadata was inspected in the backend container for Supplier, Request for Quotation, Request for Quotation Supplier, Contact, and Dynamic Link.

### Supplier

Installed Supplier metadata shows `track_changes = 1`, so ERPNext can track Supplier changes through Version records when Supplier itself is edited. Supplier includes broad master fields that are not buyer-only:

- Identity/group/status: `supplier_name`, `supplier_group`, `supplier_type`, `disabled`, `is_internal_supplier`, `country`.
- Buying defaults: `default_currency`, `default_price_list`, `payment_terms`.
- Accounting/tax/bank fields: `default_bank_account`, `tax_id`, `tax_category`, `tax_withholding_category`, `tax_withholding_group`.
- Contact/portal related fields: `supplier_primary_contact`, `email_id`, contact/address sections and portal users in ERPNext source behavior.
- Notes/detail fields: `supplier_details` and related profile text.

ERPNext Supplier docs confirm that Supplier defaults can auto-populate future transactions, that supplier disable/hold behavior can block purchase invoices, purchase orders, and payments, and that Contacts and Addresses are separate records linked to the Supplier. Source: <https://docs.frappe.io/erpnext/supplier>.

Design implication: Supplier master data must remain admin-owned. Procurement Console should not directly mutate Supplier, disable Supplier, Supplier Group, tax/accounting/bank/payment defaults, or portal/user data.

### Contact And Dynamic Link

Installed Contact metadata includes personal/contact fields such as `first_name`, `last_name`, `email_id`, child table `email_ids`, `phone_nos`, `mobile_no`, `is_primary_contact`, `user`, and Dynamic Link child rows. Dynamic Link links a Contact to a Supplier through `link_doctype`, `link_name`, and `link_title`.

Design implication: Phase 7E1 may display existing linked Contacts and may allow selecting one existing linked Contact as the preferred RFQ recipient. It must not create, edit, relink, or delete Contact records and must not create or assign User records.

### Request For Quotation Supplier

Installed Request for Quotation Supplier metadata includes:

- `supplier` required Link to Supplier.
- `contact` Link to Contact.
- `email_id` Data.
- `send_email` Check.
- `email_sent` read-only Check.
- `quote_status` read-only Select Pending/Received.

Design implication: RFQ readiness has a native place to show selected supplier, contact, and email. Phase 7E1 should feed readiness context; it should not silently mutate saved RFQ Supplier rows unless a later implementation explicitly designs that write and audit behavior.

### Request For Quotation Native Send Risk

Installed ERPNext source and official docs show that submitting an RFQ can trigger supplier email behavior when RFQ Supplier rows have `send_email`. Native send creates or updates supplier contacts, creates Website Users when needed, updates Supplier portal users, sends email, sets `email_sent`, and lets suppliers submit quotations through the portal. ERPNext docs also state that setting Contact and Email Id can be used for email sending and supplier portal access, and that submitting RFQ triggers email to suppliers with Send Email enabled. Source: <https://docs.frappe.io/erpnext/request-for-quotation>.

Design implication: Phase 7E1 must remain readiness-only. It may improve data shown to RFQ readiness but must not touch `send_email`, `email_sent`, native `send_to_supplier`, native submit, portal user creation, Contact creation, or Supplier Quotation creation.

### Audit Facilities

Frappe Versioning/Audit Trail records before/after changes for doctypes with tracking enabled. Supplier has tracking enabled in installed metadata. Frappe's audit trail discussion describes Version records capturing changed properties and child table changes. Source: <https://frappe.io/blog/erpnext-features/versioning-and-audit-trail>.

Design implication: Frappe Version can be used as secondary evidence if a custom companion DocType is tracked, but Phase 7E1 should not rely only on Supplier Version records because the design should avoid broad Supplier mutation and should capture business reason/context for readiness changes.

## Industry ERP Findings

### ERPNext

ERPNext treats Supplier as shared buying master data and Contacts as separate linked records. Supplier settings affect future transactions, payment terms, taxes, bank/accounting behavior, and blocking. RFQ supplier contact/email data participates in email sending and supplier portal access. This supports a strict split between buyer-facing readiness and master-data ownership.

### SAP

SAP S/4HANA and SAP Ariba documentation separates supplier lifecycle/master-data management from purchasing execution. SAP supplier management covers common supplier information, onboarding, lifecycle, qualification, performance, and risk. SAP S/4HANA supplier master maintenance includes roles, address, company code, bank accounts, purchasing data, and contacts, typically under business partner/master-data specialist control. SAP Manage Purchase Orders also shows approval statuses and supplier output as controlled states, not generic form bypasses. Sources: <https://help.sap.com/docs/strategic-sourcing/managing-suppliers-and-supplier-lifecycles/managing-suppliers-and-supplier-lifecycles>, <https://help.sap.com/docs/SAP_S4HANA_CLOUD/f86dc2eb1f8b48c880a7607213104b27/fdb98c570c9b6b10e10000000a441470.html>, <https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/af9ef57f504840d2b81be8667206d485/ecc316567879bf45e10000000a4450e5.html>.

### Oracle Procurement

Oracle Supplier Model separates supplier profile attributes into addresses, sites, contacts, bank accounts, tax registrations, and other supplier data. Oracle also separates prospective suppliers from spend-authorized suppliers, and supplier user accounts are provisioned by supplier administrators. Supplier contact invitations for negotiations require a specified contact. Sources: <https://docs.oracle.com/en/cloud/saas/procurement/26a/oaprc/oracle-supplier-model.html>, <https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/how-can-i-invite-suppliers-to-my-negotiation.html>, <https://docs.oracle.com/en/cloud/saas/procurement/24c/oaprc/supplier-user-account-administration.html>.

### Microsoft Dynamics 365

Dynamics 365 vendor setup distinguishes vendor contact information from specific contact person records. Contacts can be used on POs and RFQs, and referenced contacts should be deactivated rather than deleted. Vendor collaboration exposes RFQ and PO interactions to external vendors under configured collaboration settings, templates, attachments, amendments, and publication rules. Sources: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/set-up-vendor-accounts>, <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/vendor-collaboration-work-external-vendors>.

### Odoo

Odoo Purchase sends RFQs by email to the vendor email configured in Contacts, moves RFQs to sent state, downloads RFQ PDFs, and tracks email/internal notes/activities in the chatter. Confirming an RFQ turns it into an active PO, and downstream receiving/billing behavior is triggered by inventory/accounting configuration. Source: <https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html>.

### Industry Conclusion

Mature ERP systems let procurement managers coordinate supplier readiness, select contacts for sourcing, and monitor supplier communication state. They do not treat broad supplier master forms, bank/tax/payment setup, portal user provisioning, or document lifecycle release as casual buyer-page actions. Phase 7E1 should therefore create a narrow, audited buying-readiness layer rather than giving Purchase Managers raw Supplier form access.

## Proposed Phase 7E1 Scope

Implement later, after owner approval, a productized Supplier Buying Profile and Contact Readiness capability with these boundaries:

- Supplier Detail gains a `Supplier Buying Profile` or `Buying readiness` panel.
- Purchase User sees the panel read-only.
- Purchase Manager can edit only allowlisted buying-readiness fields.
- Data is stored in a companion custom app record keyed by Supplier, not directly in broad ERPNext Supplier fields.
- Existing linked Contacts may be selected as preferred RFQ contact, but no Contact is created or edited.
- RFQ readiness consumes the controlled readiness profile in read-only mode.
- RFQ send remains disabled.
- Every manager update creates audit evidence.
- Native Supplier form escape remains absent.

## Field Allowlist Proposal

### Candidate Editable Now

These are the recommended Phase 7E1 editable fields for Purchase Manager only:

| Field | Type | Stored on | Rule | Reason |
| --- | --- | --- | --- | --- |
| `buying_readiness_status` | Select: `Ready`, `Needs email`, `Needs contact review`, `Hold for sourcing` | Companion readiness profile | Does not disable Supplier globally; affects Procurement readiness display only | Lets managers classify buying readiness without touching Supplier disabled/hold state |
| `preferred_rfq_contact` | Link to existing Contact | Companion readiness profile | Contact must be linked to this Supplier through Dynamic Link; no Contact creation/edit | Selects the person buyers intend to use for future RFQs |
| `rfq_recipient_email_override` | Email | Companion readiness profile | Optional; validated email format; clearly labelled as readiness override; no Contact/User creation | Provides a controlled bridge when ERPNext Contact data is not yet maintained, if owner approves this field |
| `buying_note` | Small Text | Companion readiness profile | Internal only; length limited; sanitized; no HTML | Captures buyer context that does not belong in broad Supplier master |
| `readiness_note` | Small Text | Companion readiness profile | Required when status is `Needs email`, `Needs contact review`, or `Hold for sourcing` | Forces explanation for blocked/exception readiness states |

Owner decision required: approve or reject `rfq_recipient_email_override`. It is operationally useful, but it can diverge from official Contact records. If rejected, Phase 7E1 should support only preferred linked Contact selection and internal notes/status.

### Candidate Read-Only Display

These should be shown but not editable in Procurement Console:

| Field/context | Source | Reason |
| --- | --- | --- |
| Supplier ID, supplier name, supplier group | Supplier | Identity and classification affect master data and reporting |
| Active/disabled status | Supplier | Must remain visible because disabled suppliers should not be treated as ready |
| Existing linked Contacts | Dynamic Link + Contact | Buyers need to see available contacts |
| Contact email/phone/mobile | Contact | Readiness evidence, but Contact itself remains master/admin-owned |
| Supplier primary contact and Supplier `email_id` if available | Supplier | Useful context but broad Supplier mutation remains forbidden |
| Recent RFQs, Supplier Quotations, Purchase Orders | Existing Supplier Detail tables | Operational buying history |
| Outgoing email availability | Existing document output readiness | Explains why send remains blocked |
| Last readiness update by/at | Companion readiness profile/log | Audit summary |

### Candidate Deferred

These are useful but should not be included in the first implementation unless owner approves a larger phase:

- Supplier communication preference that changes future send behavior.
- Buyer follow-up owner or task assignment.
- Supplier attachments/documents inside the readiness panel.
- Supplier scorecard or qualification workflow.
- Supplier onboarding/request-to-create workflow.
- Controlled Contact edit/create request workflow.
- Supplier portal readiness.

### Explicitly Forbidden

These must not be editable or triggered by Phase 7E1:

| Forbidden field/action | Reason |
| --- | --- |
| Supplier creation | Master-data onboarding requires admin/governance |
| Supplier disabled flag, hold/block state, frozen status | Can block purchasing, invoices, or payments globally |
| Supplier group, supplier type, country, tax/category/withholding fields | Reporting, taxation, and accounting consequences |
| Bank account, payable account, payment terms, billing currency, price list | Finance/accounting and transaction-default consequences |
| Supplier primary contact mutation | Changes global transaction defaults and should be admin-governed |
| Contact creation/edit/delete/relink | Contact master data and identity consequences |
| User creation, Website User creation, portal user assignment | External identity/security consequences |
| RFQ Supplier `send_email` or `email_sent` mutation | Can trigger or misrepresent external send state |
| RFQ send/email, SMTP, Email Queue, Communication creation | Deferred supplier communication phase |
| RFQ submit, PR/RFQ/SQ/PO submit/approve/reject/cancel | Lifecycle governance not implemented |
| PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, PR/MR-to-PO conversion | Native mappings require separate design and submitted upstream states |
| Item Price and Default Supplier | Buying automation and pricing governance consequences |
| Receiving, Purchase Receipt, billing, Purchase Invoice, payment | Warehouse/Finance ownership |
| AI supplier quotation intake | Separate data validation and audit problem |

## Role Matrix

| Capability | Purchase User | Purchase Manager | Procurement Admin/System Manager |
| --- | --- | --- | --- |
| View Supplier Directory | Allowed | Allowed | Allowed outside normal console as configured |
| View Supplier Detail | Allowed | Allowed | Allowed |
| View Supplier Buying Profile panel | Allowed read-only | Allowed | Allowed |
| Edit allowlisted readiness fields | Denied | Allowed if Supplier read permission and manager role pass | Not exposed as special in-console admin escape in Phase 7E1 |
| Select existing preferred RFQ contact | Denied | Allowed only from linked Contact options | Admin can manage Contact outside console |
| Add RFQ recipient email override | Denied | Allowed only if owner approves field | Admin can manage Supplier/Contact outside console |
| Create/edit Supplier | Denied | Denied | Outside Procurement Console only |
| Create/edit Contact or User | Denied | Denied | Outside Procurement Console only |
| Activate portal supplier user | Denied | Denied | Outside Procurement Console only |
| Send RFQ | Disabled | Disabled | Deferred, no Phase 7E1 implementation |
| Submit/approve/convert/lifecycle actions | Denied | Denied | Deferred or outside console depending future policy |

## UI/UX Design

### Supplier Detail Placement

Add a compact `Supplier Buying Profile` panel near the top of Supplier Detail, after the summary facts and before recent purchase activity. This panel should replace the business value that raw `Open ERP Supplier Form` previously provided for buyers, without using ERPNext/native language.

Recommended panel sections:

- Status row: Buying readiness chip, recipient readiness chip, last updated by/at.
- Preferred RFQ recipient: linked Contact name, email, phone if available, and source label.
- Internal buying note: short read-only text for Purchase User; editable textarea for Purchase Manager.
- Readiness note: visible when readiness is not ready.
- Audit link or collapsed history: last five readiness changes.

### Purchase User Experience

Purchase User sees:

- Read-only readiness chips.
- Existing linked contacts and selected preferred contact.
- Missing-email or needs-review copy if applicable.
- No Edit button.
- No native Supplier form link.

### Purchase Manager Experience

Purchase Manager sees a secondary `Edit readiness` button inside the panel. Editing should open an inline edit state or compact modal with Save and Cancel. The edit UI must be dense, business-like, and consistent with Procurement managed form styling.

Validation should be inline and productized:

- If selected Contact is not linked to the Supplier: `Select a contact linked to this supplier.`
- If email override is invalid: `Enter a valid supplier recipient email.`
- If readiness is blocked without note: `Add a readiness note before saving this blocked state.`
- If payload contains unknown/forbidden keys: show a controlled save error and log server-side.

### Supplier Directory Indicator

Supplier Directory should later add a compact readiness column or chip:

- `Ready`
- `Needs email`
- `Needs review`
- `Hold for sourcing`
- `No profile`

This should be filterable only after implementation proves performance is acceptable. It should not crowd the existing directory at 1136px.

### RFQ Readiness Integration

Managed RFQ and RFQ Review Supplier Communication should later display the readiness source in each supplier row:

- `RFQ row email`
- `Preferred supplier contact`
- `Supplier readiness override`
- `Linked contact`
- `Supplier master email`
- `Missing`

If the Supplier Buying Profile says `Hold for sourcing`, the RFQ readiness row should show a blocked readiness state and the readiness note. Send remains disabled in Phase 7E1 regardless of readiness.

### Copy Rules

- Use buyer-facing terms: `Buying readiness`, `Preferred RFQ contact`, `Recipient readiness`, `Internal buying note`.
- Do not use raw/native terms such as `ERPNext form`, `DocType`, `Dynamic Link`, `Portal User`, or `Email Queue` in normal UI copy.
- Keep explanatory text concise. The panel should feel like an operational control, not a documentation page.

## Backend/API Design

Recommended future module:

- `erp_workspace_ui/procurement_console/supplier_readiness.py`

Recommended future methods:

| Method | Purpose | Mutation |
| --- | --- | --- |
| `get_supplier_buying_profile_context(supplier)` | Returns Supplier identity, read-only contacts, readiness profile, role capabilities, audit summary | No |
| `save_supplier_buying_profile(payload)` | Updates allowlisted readiness profile fields for Purchase Manager | Yes, companion profile only |
| `get_supplier_readiness_audit(supplier)` | Returns immutable readiness log entries | No |
| `get_supplier_contact_options(supplier)` | Returns linked Contact choices for the edit UI | No |

Suggested payload for `save_supplier_buying_profile`:

```json
{
  "supplier": "SUP-0001",
  "buying_readiness_status": "Needs email",
  "preferred_rfq_contact": "CONT-0001",
  "rfq_recipient_email_override": "buyer-safe@example.com",
  "buying_note": "Use WhatsApp follow-up after RFQ preview.",
  "readiness_note": "Supplier contact email must be confirmed before RFQ send."
}
```

Backend rules:

- Require authenticated user.
- Require Procurement access.
- Require Supplier read permission.
- Require Purchase Manager role for save.
- Re-read Supplier from DB; do not trust client supplier name/title.
- Validate selected Contact through Dynamic Link to the same Supplier.
- Validate email syntax server-side.
- Reject unknown keys.
- Reject forbidden keys explicitly and return controlled productized error.
- Write only to the companion readiness profile and log doctypes.
- Do not mutate Supplier, Contact, User, RFQ, RFQ Supplier row, Email Account, Communication, Email Queue, Item, Item Price, or Default Supplier.
- Return updated context after save.

## Audit Design

### Options Considered

| Option | Strength | Weakness | Recommendation |
| --- | --- | --- | --- |
| Frappe Version on Supplier | Built in; Supplier has `track_changes = 1` | Requires mutating Supplier, which Phase 7E1 should avoid; weak business reason capture | Do not use as primary |
| Frappe Version on companion profile | Built in before/after diff | May be harder to query in productized UI; not enough alone for readiness reason | Use as secondary if profile DocType tracks changes |
| Comment records | User-friendly timeline | Less structured for before/after field audit; can mix with narrative notes | Optional display layer only |
| Custom `Procurement Supplier Readiness Log` DocType | Structured, queryable, productized, can include before/after/reason | Requires a new DocType in implementation | Recommended primary audit |
| JSON log field inside profile | Simple | Harder to query, validate, and protect | Not recommended |

### Recommended Audit Mechanism

Create a companion profile DocType plus immutable log DocType in the future implementation:

- `Procurement Supplier Readiness Profile`: one record per Supplier, owned by the custom app.
- `Procurement Supplier Readiness Log`: append-only log of field changes.

Each log entry should record:

- Supplier.
- Profile record.
- Changed by.
- Changed at.
- Role context.
- Field names changed.
- Before values.
- After values.
- Readiness note/reason.
- Source route, if available.
- Negative/blocked attempt flag for forbidden payload keys, if owner approves security logging.

The implementation should also enable tracking on the profile DocType if practical, but the productized log should be the authoritative audit evidence shown to Purchase Managers.

## Security And Stability Requirements

- All mutation must be server-owned.
- Frontend role state is display only; backend must enforce role and field allowlist.
- Unknown payload keys must be rejected.
- Forbidden field names must never be silently ignored if they indicate attempted master-data mutation.
- Save must not depend on native Supplier write permission unless the companion profile is implemented as a custom DocType with its own controlled permission path.
- Purchase User must never receive edit capability in context.
- Sales roles and Guest must be denied.
- No raw native route target may be returned.
- No hidden RFQ send, native RFQ submit, native portal user, Contact/User creation, Communication, or Email Queue side effect may occur.
- No secrets or email provider settings are involved in Phase 7E1.
- Report pages must remain read-only and must not mutate Supplier readiness.
- Any shared runtime or shared shell change during implementation requires Sales freeze.
- Runtime implementation must run focused Procurement smoke plus full protected workspace gate.

## Test And Smoke Plan For Future Implementation

### Python Unit Tests

- Purchase Manager can read Supplier Buying Profile context.
- Purchase User can read the context but receives `can_edit = false`.
- Purchase Manager can update only allowlisted fields.
- Purchase User cannot update readiness fields.
- Sales roles and Guest are denied.
- Unknown payload keys are rejected.
- Forbidden keys such as `disabled`, `supplier_group`, `payment_terms`, `default_bank_account`, `contact_email`, `send_email`, `item_price`, and `default_supplier` are rejected.
- Selected preferred Contact must be linked to the Supplier through Dynamic Link.
- Invalid email override is rejected.
- Readiness blocked state requires a note.
- Save creates a readiness log with before/after values.
- Save does not create or mutate Supplier, Contact, User, RFQ, RFQ Supplier, Communication, Email Queue, Item Price, or Default Supplier.
- RFQ readiness reflects the saved profile as read-only context.
- Native escape labels remain absent from Supplier Detail and related Procurement routes.
- RFQ send remains disabled/deferred.

### Smoke Tests

- Supplier Directory shows readiness indicator without horizontal overflow at 1136px and 1440px.
- Supplier Detail shows Buying Profile panel for Purchase User and Purchase Manager.
- Purchase User sees no edit button.
- Purchase Manager edit flow validates and saves allowlisted fields.
- Audit summary updates after save.
- RFQ Review and saved Managed RFQ show updated recipient readiness.
- Preview RFQ still works.
- Download RFQ PDF still works.
- Send RFQ remains disabled.
- No native email composer appears.
- No native print controls appear.
- No raw Frappe permission/server modals appear.
- No `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, or `Advanced ERP Form` appears.
- No route navigates to `/desk/Form/`, `/app/`, or route array beginning with `Form` for normal Procurement roles.
- Full protected workspace gate passes.
- Sales freeze passes if shared runtime is touched.

## Implementation Roadmap If Owner Approves

### Phase 7E1A: Data Contract And Backend Context

Scope:

- Add companion readiness profile/log doctypes or app-owned equivalent.
- Add read-only context endpoint.
- Add manager-only save endpoint with allowlist validation.
- Add unit tests for role gates, forbidden payloads, and audit log creation.

Exclusions:

- No frontend edit UI yet.
- No RFQ readiness integration yet.
- No send/email.

Validation:

- Python unit discovery.
- Static no-native/no-send symbol scans.

### Phase 7E1B: Supplier Detail UI

Scope:

- Add Supplier Buying Profile panel to Supplier Detail.
- Purchase User read-only state.
- Purchase Manager edit/save/cancel state.
- Audit summary display.

Exclusions:

- No Supplier Directory readiness column yet unless layout is proven.
- No RFQ send or Contact creation.

Validation:

- Focused Supplier Detail smoke for Purchase User and Purchase Manager.
- Visual screenshots at 1136px and 1440px.

### Phase 7E1C: RFQ Readiness Integration

Scope:

- Read Supplier Buying Profile in RFQ readiness calculation.
- Display readiness source on Managed RFQ and RFQ Review.
- Keep Send RFQ disabled.

Exclusions:

- No mutation of RFQ Supplier row unless separately approved.
- No email/send.

Validation:

- Phase 6C2A smoke plus new supplier readiness assertions.
- Protected workspace gate.

### Phase 7E1D: Directory Indicator And Performance Hardening

Scope:

- Add compact Supplier Directory readiness indicator if query cost is acceptable.
- Add indexing/caching strategy if needed.

Exclusions:

- No broad dashboard redesign.

Validation:

- Directory performance and responsive visual smoke.

## Deferred Scope

- Actual RFQ email/send.
- Email account/provider setup.
- Communication or Email Queue creation.
- Contact creation/editing/relinking.
- User creation or supplier portal activation.
- Supplier creation or broad Supplier master edit.
- Supplier disabled/hold/group/tax/accounting/bank/payment defaults.
- Item Price or Default Supplier mutation.
- RFQ submit, approval, conversion, or Supplier Quotation creation.
- Purchase Order submit/release/send.
- Receiving, Purchase Receipt, billing, Purchase Invoice, payment.
- Supplier scorecards, qualification workflows, onboarding, and AI intake.

## Owner Decisions Needed Before Implementation

1. Approve the companion profile/log DocType architecture instead of direct Supplier custom fields.
2. Decide whether `rfq_recipient_email_override` is allowed in Phase 7E1 or deferred until Contact governance exists.
3. Confirm Purchase Manager is the only role allowed to edit readiness fields.
4. Decide whether `Hold for sourcing` should block future RFQ readiness display or simply warn.
5. Decide whether forbidden payload attempts should be logged as security events.
6. Confirm whether Supplier Directory should include readiness indicators in the first implementation or only after Supplier Detail is proven.
7. Confirm the naming: `Supplier Buying Profile`, `Supplier Readiness`, or another owner-preferred business term.

## Final Recommendation

Proceed next with Phase 7E1A only after owner approval: backend context, companion readiness profile/log design, allowlist validation, and audit tests. Do not begin with broad UI changes or Supplier master edits. The highest-value first slice is manager-owned readiness status, preferred existing contact selection, internal buying note, and immutable audit, while RFQ send remains disabled.
