# Procurement Console Phase 7E3 Manager Review / Action Readiness Design Plan

Date: 2026-05-19

Design scope: docs only. No runtime implementation is included in this document.

Baseline: Phase 7E2A Buying Item Procurement Context protected at `d148248d9c6d481fbaf62f568254bbfe83e67477`.

## Executive Recommendation

Implement the next runtime slice as Phase 7E3A: a combined manager readiness layer consisting of:

1. An Overview-level `Manager Readiness` queue for Purchase Managers.
2. Page-level readiness cards on key Procurement review/detail pages.
3. Disabled/deferred next-action guidance that explains why lifecycle actions are unavailable and where to fix readiness issues through productized Supplier Buying Profile or Buying Item Procurement Context.

Phase 7E3A must not submit, approve, reject, convert, send email, create downstream documents, mutate Item Price, mutate Default Supplier, mutate Item Supplier, create Contacts/Users, or reopen native ERPNext forms. It should be a review and exception-guidance layer only.

Recommended option: Option 3, combined overview queue plus page-level readiness cards, with no lifecycle mutation.

Reason:

- Purchase Managers need a consolidated view of sourcing/order blockers, not only isolated page warnings.
- Buyers also need local context on the document they are reviewing.
- Supplier and item readiness are now productized and can be linked safely.
- Lifecycle actions remain too risky until their own governance phases define state, audit, role, and side effects.

## Current System Findings

### Source And Baseline Constraints

The current protected Procurement baseline includes:

- Phase 5A/5B managed Purchase Request and RFQ draft forms.
- Phase 5C managed Supplier Quotation draft form.
- Phase 5D managed Purchase Order draft form.
- Phase 6C1 RFQ/PO productized preview/PDF wrappers.
- Phase 6C2A RFQ send readiness with `Send RFQ` disabled.
- Phase 6C2B governed RFQ send design only.
- Phase 6C2C corrective send deferral/removal.
- Phase 7D1 native ERPNext form escape closure for normal Procurement roles.
- Phase 7E1A Supplier Buying Profile / Supplier Readiness.
- Phase 7E2A Buying Item Procurement Context.
- Phase 7G Quick Find review, with implementation deferred.

Explicit protected boundaries:

- Normal Purchase User and Purchase Manager paths must not expose raw native ERPNext form links.
- RFQ send/email remains disabled/deferred.
- PO send remains disabled/deferred.
- Submit, approval, rejection, cancel, conversion, receive, bill, payment, Item Price mutation, Default Supplier mutation, Item Supplier mutation, Contact/User creation, portal activation, and AI intake remain out of scope.
- Sales Console remains frozen/protected.

### Installed Source Availability

No importable ERPNext source tree was found in the checked host locations during this design pass:

- `/home/deploy/frappe-bench/apps/erpnext`
- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/apps/erpnext`
- `/home/deploy/erp-projects/erpai_project1/apps/erpnext`

ERPNext-specific conclusions therefore combine official ERPNext documentation with current custom app source and already protected project baselines.

### Current Procurement Surfaces

| Surface | Current manager capability | Current gap for Phase 7E3 |
| --- | --- | --- |
| Overview | Workbench cards, KPIs, navigation, draft create entries | No consolidated manager exception/readiness queue |
| Supplier Detail | Supplier Buying Profile, manager-only readiness edit | Not aggregated into manager action readiness beyond RFQ recipient checks |
| Buying Item Detail | Buying Procurement Context, manager-only context edit | Not aggregated into document readiness beyond item detail itself |
| Purchase Request Review | Read-only demand review | No readiness checklist for sourcing/order preparation |
| RFQ Review | Read-only RFQ review, supplier-specific preview/PDF, recipient readiness, disabled Send RFQ | No page-level summary that combines supplier readiness, item readiness, RFQ completeness, and deferred send policy |
| Supplier Quotation Review | Read-only offer review, Compare offers link | No award/readiness explanation, no missing-rate or missing-date blocker summary |
| Purchase Order Follow-up Detail | Read-only PO follow-up | No manager release/send readiness summary; receiving/billing remain outside scope |
| Managed PR/RFQ/SQ/PO saved forms | Draft save/reset/review, plus output where protected | No save-time readiness panel beyond RFQ output/readiness |
| Reports Index and reports | Read-only analytics and drilldowns | No action bridge from exception report finding to manager readiness queue |

### Current Safe Productized Fix Paths

The following productized fix paths already exist and should be referenced by Phase 7E3A readiness guidance:

- Supplier Buying Profile on Supplier Detail for supplier readiness, RFQ recipient override, preferred contact, buying note, and readiness note.
- Buying Procurement Context on Buying Item Detail for item readiness, preferred existing supplier context, lead time context, MOQ context, supplier part reference, buying note, and readiness note.
- Managed draft forms for correcting draft PR/RFQ/SQ/PO data where the document is editable.
- Productized Preview/PDF wrappers for RFQ and PO output validation.

Readiness guidance must use these productized paths and must not tell buyers to open raw ERPNext forms.

## Industry Research Summary

### ERPNext

ERPNext buying documentation separates Material Request, Request for Quotation, Supplier Quotation, Purchase Order, Purchase Receipt, and Purchase Invoice as distinct documents. It also treats Supplier and Item as broad master records. Current project baselines already reflect the ERPNext implication: document lifecycle actions and downstream conversions should not be simulated by custom copying; they require governed source state and native validation.

Relevant official sources:

- ERPNext Buying module overview: https://docs.frappe.io/erpnext/user/manual/en/buying
- ERPNext Material Request: https://docs.frappe.io/erpnext/user/manual/en/material-request
- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/user/manual/en/request-for-quotation
- ERPNext Supplier Quotation: https://docs.frappe.io/erpnext/user/manual/en/supplier-quotation
- ERPNext Purchase Order: https://docs.frappe.io/erpnext/user/manual/en/purchase-order
- ERPNext Supplier: https://docs.frappe.io/erpnext/user/manual/en/supplier
- ERPNext Item: https://docs.frappe.io/erpnext/user/manual/en/item

Design implication:

- Phase 7E3 should present readiness and exception state only. It should not bypass ERPNext lifecycle, submit, conversion, pricing, or master-data controls.

### SAP S/4HANA

SAP procurement patterns separate purchase requisition processing, sourcing/RFQ, supplier quotation handling, purchase order processing, and workflow approvals. Procurement professionals usually work from role-based apps and queues that expose exceptions and next steps, while approval/release flows remain workflow-controlled.

Relevant official sources:

- SAP Help Portal for SAP S/4HANA Cloud Sourcing and Procurement: https://help.sap.com/docs/SAP_S4HANA_CLOUD
- SAP workflow for purchase requisitions for procurement professionals: https://help.sap.com/docs/buying-invoicing/purchasing-guide-for-procurement-professionals/about-workflow-of-purchase-requisitions-8b3f5dbe7a7b4427a1039a46dfe475d3

Design implication:

- A manager readiness queue is enterprise-aligned, but release/approval and PO commitment actions should remain workflow phases.

### Oracle Fusion Cloud Procurement

Oracle Procurement separates requisitioning, sourcing negotiations, supplier responses/award decisions, purchasing document generation, and approvals. Supplier-facing communication and purchasing commitments are governed by roles, approvals, document controls, and audit.

Relevant official sources:

- Oracle Fusion Cloud Procurement documentation library: https://docs.oracle.com/en/cloud/saas/procurement/
- Oracle Procurement purchasing and document approval documentation: https://docs.oracle.com/en/cloud/saas/procurement/oaprc/

Design implication:

- Readiness should classify whether a document is prepared for a future governed step, but the action to award, approve, or create a downstream purchasing document must not be hidden inside readiness UI.

### Microsoft Dynamics 365 Supply Chain Management

Dynamics 365 Procurement and sourcing uses RFQ cases, vendor bid handling, purchase requisitions, purchase orders, workflow approvals, and vendor collaboration as governed areas. Operational queues and statuses guide users without collapsing approval, sourcing, and PO execution into one ungoverned button.

Relevant official sources:

- Procurement and sourcing overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview
- Request for quotation overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Purchase order workflows: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-order-workflows

Design implication:

- The correct next step is readiness and exception visibility, not immediate conversion or approval implementation.

### Odoo

Odoo Purchase separates RFQs, purchase orders, vendor pricelists, approvals, and purchase agreements/calls for tenders. Buyer-facing flows can compare vendors and prepare documents, while confirmation and approval remain governed by purchasing settings and access rights.

Relevant official sources:

- Odoo Purchase documentation: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase.html
- Odoo RFQ and purchase order documentation: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals.html

Design implication:

- Readiness warnings and comparison context should guide the buyer to clean supplier/item/document data before later confirmation or approval phases.

### Industry Pattern Conclusion

Across ERP systems, mature procurement workspaces provide:

- Role-specific queues.
- Exception badges.
- Readiness/status summaries.
- Drilldowns to productized detail pages.
- Workflow-gated external send, award, conversion, approval, and release.
- Audit trail for changes and decisions.

They do not normally expose broad master-data forms or lifecycle commands as the normal buyer workspace path. Phase 7E3 should therefore add visibility and guidance, not mutation.

## Architecture Option Comparison

| Option | Description | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| 1. Overview-level manager readiness dashboard only | Add a manager queue/card on Overview with counts and drilldowns | Strong manager scanning; low page clutter | Users still lack local page-level explanation while reviewing a specific document | Not enough alone |
| 2. Page-level readiness panels only | Add readiness cards to review/detail pages | Excellent local context; easier to phase by page | No consolidated manager workload view | Not enough alone |
| 3. Combined overview queue plus page-level readiness cards | Overview summarizes exceptions; pages explain local blockers and productized fix paths | Best enterprise fit; supports manager scanning and detail review; avoids lifecycle mutation | More design/test surface; needs careful performance aggregation | Recommended |
| 4. Implement lifecycle actions now | Add send/submit/convert/award/approve actions | Completes business workflows faster | Violates current deferrals; high side-effect risk; needs separate governance | Reject |
| 5. Do nothing until conversions are designed | Keep current surfaces unchanged | Safest short term | Managers still lack next-step visibility after Supplier and Item context work | Reject |

Final recommendation: implement Option 3 in Phase 7E3A.

## Recommended Product Contract For Phase 7E3A

### Purchase Manager Experience

Purchase Manager sees:

- Overview `Manager Readiness` section with grouped exception queues.
- Page-level readiness cards on document review/detail pages.
- Severity chips and counts.
- Productized links to fix Supplier Buying Profile or Buying Procurement Context.
- Productized links back to managed draft forms only when the document is still editable and the existing managed form supports it.
- Disabled/deferred action guidance for send, submit, conversion, approval, award, receiving, billing, payment, and price/default-supplier mutation.

Purchase Manager does not get:

- Active submit/approve/reject/cancel.
- Active RFQ send/email.
- Active PO send/email.
- Active PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, or PR/MR-to-PO conversion.
- Active Item Price, Default Supplier, Item Supplier, Contact/User, or portal mutation.
- Native ERPNext form escape.

### Purchase User Experience

Purchase User sees:

- Read-only warnings where applicable.
- Read-only page-level readiness context.
- Productized navigation to Supplier Detail or Item Detail when already permitted.
- No manager-only edit/fix action unless an existing protected action is already allowed for Purchase User.

Purchase User does not get:

- Manager readiness dashboard controls that imply ownership of manager decisions.
- Edit buttons for Supplier Buying Profile or Buying Procurement Context.
- Lifecycle, conversion, send, price, default supplier, contact/user, or portal actions.

### Data Feeds

Phase 7E3A readiness should read from:

- Saved PR/RFQ/SQ/PO document fields and child rows.
- Supplier Buying Profile / Supplier Readiness records.
- Buying Item Procurement Context records.
- RFQ Supplier Communication readiness context.
- Productized output context for RFQ/PO preview availability.
- Existing report/worklist data where needed, but not by scraping rendered report pages.

### Overview Readiness Queues

Recommended Overview queues:

1. `Sourcing preparation blockers`
   - Purchase Requests with missing item/warehouse/required date readiness.
   - Purchase Requests where item buying context is `Not reviewed` or `Hold for sourcing`.
   - Requests that cannot be converted because conversion policy remains deferred.

2. `RFQ release blockers`
   - RFQs missing suppliers.
   - RFQs missing item lines.
   - RFQs with supplier readiness on hold, missing email, missing contact review, or outgoing email unavailable.
   - RFQs with item buying context on hold.
   - RFQs blocked because governed RFQ send is deferred.

3. `Supplier quotation review blockers`
   - Supplier Quotations missing item rates.
   - Supplier Quotations missing required validity or required-by dates where relevant.
   - Supplier Quotations that look ready for comparison but award/SQ-to-PO is deferred.

4. `PO draft readiness blockers`
   - Draft POs missing supplier, items, rates, required dates, warehouse/delivery context, or currency.
   - POs blocked because approval/submit/release/send governance is not implemented.
   - POs with item context on hold.

5. `Master/context readiness`
   - Suppliers on hold for sourcing.
   - Suppliers needing email/contact review.
   - Items not reviewed or on hold for sourcing.

### Page-Level Readiness Cards

Recommended placement:

- Purchase Request Review: `Sourcing Readiness` card.
- RFQ Review: `RFQ Release Readiness` card near Supplier Communication.
- Supplier Quotation Review: `Offer Review Readiness` card near totals/items.
- Purchase Order Follow-up or managed PO saved page: `PO Release Readiness` or `Draft Commitment Readiness` card.
- Supplier Detail: retain Supplier Buying Profile; optionally show a compact `Used in readiness` summary later.
- Buying Item Detail: retain Buying Procurement Context; optionally show `Used in readiness` summary later.

### Allowed Actions In Phase 7E3A

Allowed action types:

- Navigate to productized detail/review pages.
- Navigate to productized Supplier Detail.
- Navigate to productized Buying Item Detail.
- Navigate to managed draft form only when a currently protected managed form exists and document state is editable.
- Refresh readiness.
- Filter/read readiness queues.

No mutation is allowed except any already protected Supplier/Item profile edits on their own detail pages.

## Readiness Categories And Severity Model

### Severity Levels

| Severity | Meaning | UI tone | Action model |
| --- | --- | --- | --- |
| Critical | Unsafe to proceed; future action must remain blocked | Red/blocked | Explain blocker and productized fix path |
| Warning | Data incomplete or policy deferred; future action not ready | Amber | Show next review step or fix path |
| Info | Informational deferred policy, no user fix available yet | Neutral/blue | Explain deferred phase |
| Ready | Data passes current readiness checks, but lifecycle may still be deferred | Green | State ready for future governed phase, not active action |

### Candidate Readiness Checks

| Category | Check | Severity | Productized fix path | Still deferred |
| --- | --- | --- | --- | --- |
| Supplier readiness missing | Supplier Buying Profile status absent/not reviewed | Warning | Supplier Detail -> Supplier Buying Profile | RFQ send |
| Supplier on hold | Supplier status `Hold for sourcing` | Critical | Supplier Detail -> Supplier Buying Profile | RFQ send, PO commitment |
| Supplier email missing | RFQ recipient email missing | Critical for send readiness | Supplier Detail -> Supplier Buying Profile | Actual send |
| Supplier contact review needed | Preferred RFQ contact not reviewed | Warning | Supplier Detail -> Supplier Buying Profile | Actual send |
| Outgoing email unavailable | Email setup unavailable | Info/Critical for send | No in-app fix until email phase | Actual send |
| Item not reviewed | Item buying status `Not reviewed` | Warning | Buying Item Detail -> Buying Procurement Context | Item Supplier/Price mutation |
| Item on hold | Item buying status `Hold for sourcing` | Critical | Buying Item Detail -> Buying Procurement Context | RFQ/PO conversion |
| RFQ has no supplier | Supplier rows empty | Critical | Managed RFQ form if draft/editable | RFQ send |
| RFQ has no items | Item rows empty | Critical | Managed RFQ form if draft/editable | RFQ send |
| SQ missing rate | Quoted item has no rate | Critical | Managed SQ form if draft/editable | Award/SQ-to-PO |
| SQ missing validity | Valid till missing/expired | Warning | Managed SQ form if draft/editable | Award/SQ-to-PO |
| PO missing supplier | Draft PO supplier absent | Critical | Managed PO form if draft/editable | Submit/release/send |
| PO missing item/rate/date | Draft PO incomplete | Critical/Warning | Managed PO form if draft/editable | Submit/release/send |
| Document unsaved | New draft not saved | Info/Warning | Save draft first | Output/readiness/lifecycle |
| Draft/internal only | Draft output is not supplier-facing | Info | Preview/PDF only | PO send/commitment |
| Native lifecycle required | Native submit/mapper needed for later step | Info | No user fix in Phase 7E3A | Submit/conversion |
| Conversion policy missing | PR/RFQ/SQ/PO handoff not governed | Info | No user fix in Phase 7E3A | Conversion |

## Role Matrix

| Capability | Purchase User | Purchase Manager | Procurement Admin/System Manager |
| --- | --- | --- | --- |
| View page readiness cards | Yes, read-only | Yes | Yes if using Procurement Console |
| View Overview manager readiness queue | Optional read-only if owner wants transparency; default no | Yes | Yes if using Procurement Console |
| Navigate to Supplier Detail | If already permitted | If already permitted | If already permitted |
| Edit Supplier Buying Profile | No | Yes, existing Phase 7E1A allowlist only | Outside normal console policy unless assigned manager role |
| Navigate to Buying Item Detail | If already permitted | If already permitted | If already permitted |
| Edit Buying Procurement Context | No | Yes, existing Phase 7E2A allowlist only | Outside normal console policy unless assigned manager role |
| Submit/approve/reject/cancel | No | No | Not inside Procurement Console in Phase 7E3A |
| Convert PR/RFQ/SQ/PO | No | No | Not inside Procurement Console in Phase 7E3A |
| Send RFQ/PO email | No | No | Not inside Procurement Console in Phase 7E3A |
| Native ERP form escape | No | No | No in-console escape in Phase 7E3A |

Owner decision required: whether Purchase User should see the Overview-level manager readiness queue read-only. Default recommendation is manager-only on Overview, with page-level warnings visible to both roles.

## UX Plan

### Overview `Manager Readiness` Section

Placement:

- Below priority work and buying pipeline, above report shortcuts if possible.
- Visible to Purchase Manager by default.
- Optional read-only visibility to Purchase User only if owner approves.

Layout:

- Compact card band, not a marketing hero.
- Group rows by queue: Sourcing, RFQ, Supplier Quotation, Purchase Order, Master/Context.
- Each group shows count, highest severity, and the first few exception types.
- Each row opens the relevant productized page/worklist/report with filters or a readiness queue route.

Copy rules:

- Use action-oriented but non-mutating labels.
- Examples:
  - `Review sourcing blockers`
  - `RFQs needing release readiness`
  - `Supplier quotations needing review`
  - `PO drafts needing release readiness`
  - `Supplier/item context blockers`
- Avoid phrases like `Approve now`, `Send now`, `Convert`, `Submit`, or `Create PO`.

### Page-Level Readiness Cards

Placement:

- Near the top of review pages, after summary header and before detail tables.
- On RFQ Review, the readiness card should sit near Supplier Communication and not duplicate the existing recipient rows.
- On saved managed forms, show a compact readiness card only after save if it uses saved document data.

Card structure:

- Title: e.g. `Readiness for sourcing`, `RFQ release readiness`, `Offer review readiness`, `PO release readiness`.
- Severity chip: `Ready`, `Needs review`, `Blocked`, or `Deferred`.
- Short issue list, capped to avoid crowding.
- Productized fix links where available.
- Deferred action explanation where no fix exists yet.

Disabled action explanation card:

- Shows why an action is not available.
- Does not render as a disabled primary CTA when no implementation exists.
- Example: `RFQ send remains disabled until governed email setup, confirmation, and audit are approved.`

### Link And Navigation Rules

Allowed links:

- Productized Supplier Detail.
- Productized Buying Item Detail.
- Productized managed draft forms where the saved draft is editable.
- Productized RFQ Review, SQ Review, PR Review, PO Follow-up.
- Productized reports.

Forbidden links:

- `/desk/Form/...`
- `/app/...`
- Native ERPNext form labels.
- Native print/email dialogs.

### Empty States

If no readiness blockers exist:

- Overview card: `No manager readiness blockers in current view.`
- Page card: `No readiness issues found for the checks available in this phase.`
- If a lifecycle remains deferred despite data readiness, show `Ready for future governed step` rather than implying an active action exists.

### Responsive Expectations

At 1136px, 1240px, and 1440px:

- Cards must not clip horizontally.
- Issue rows should wrap cleanly.
- Severity chips must stay readable.
- No nested cards inside cards.
- Use shared card spacing, 8px-or-less inner card radius where applicable unless existing Procurement shared style requires otherwise.
- Avoid long explanatory paragraphs in the main UI; keep detailed policy in docs/tooltips if needed.

## Backend / API / Data Plan

### Recommended Module Shape

Add a focused readiness service in a future implementation, for example:

- `erp_workspace_ui/procurement_console/manager_readiness.py`

Recommended APIs:

- `get_manager_readiness_overview(filters=None)`
- `get_purchase_request_readiness(name)`
- `get_rfq_readiness(name)`
- `get_supplier_quotation_readiness(name)`
- `get_purchase_order_readiness(name)`
- `get_supplier_context_readiness(supplier)`
- `get_item_context_readiness(item_code)`

These APIs should read existing data and return productized readiness objects only.

### Readiness Object Contract

Recommended shape:

```json
{
  "state": {"kind": "ok"},
  "summary": {
    "overall_status": "blocked|needs_review|deferred|ready",
    "label": "Needs review",
    "highest_severity": "critical|warning|info|ready",
    "issue_count": 3
  },
  "issues": [
    {
      "key": "supplier_email_missing",
      "severity": "critical",
      "label": "Supplier email missing",
      "detail": "Supplier recipient is required before a future governed RFQ send.",
      "entity_type": "Supplier",
      "entity_name": "SUP-0001",
      "fix_route": {"kind": "page", "route": "procurement-console-supplier", "route_parts": ["SUP-0001"]},
      "deferred_action": "RFQ send remains disabled"
    }
  ],
  "actions": []
}
```

### Performance Rules

- Batch-read Supplier Buying Profile and Buying Item Procurement Context records.
- Avoid per-row API calls from the browser.
- Aggregate at the backend with bounded limits.
- Use permission-aware parent document visibility.
- Return counts and top examples rather than unbounded issue lists.
- Cache/coalesce within request scope where the same supplier/item appears repeatedly.

### Mutation Rules

Phase 7E3A readiness APIs must not create, update, submit, cancel, send, or convert any document.

Forbidden in implementation:

- `frappe.sendmail` or RFQ send wrappers.
- Communication or Email Queue creation.
- Contact/User/portal creation.
- ERPNext mapper calls for PR/RFQ/SQ/PO conversion.
- `submit`, `approve`, `reject`, `cancel`, `receive`, `bill`, `pay` calls.
- Writes to Item, Item Supplier, Item Price, Item Default, Default Supplier, Supplier master, stock/accounting records.

## Governance And Safety Plan

Future Phase 7E3A implementation must update governance manifest with productized read-only readiness actions only:

- `procurement-manager-readiness-overview-view`
- `procurement-pr-readiness-view`
- `procurement-rfq-readiness-view`
- `procurement-sq-readiness-view`
- `procurement-po-readiness-view`
- Productized fix navigation entries to Supplier Detail / Buying Item Detail / managed draft forms where applicable.

It must not add governed native exceptions or native action entries.

Required static scans:

- No `Open ERP Form` labels.
- No `/desk/Form/` or `/app/` links in Procurement runtime.
- No `send_rfq_test_email`.
- No SMTP env symbols.
- No `frappe.sendmail` or `smtplib` in Procurement runtime.
- No `Communication` or `Email Queue` creation in active code.
- No Item Price / Default Supplier / Item Supplier mutation symbols in active save paths.
- No submit/approval/conversion mapper calls in readiness code.

Audit requirements:

- Phase 7E3A itself should not create audit records because it is read-only.
- It may surface latest audit metadata from Supplier Readiness and Item Buying Profile logs.
- Any future manager disposition phase must define a separate immutable audit model before implementation.

Gate requirements:

- Source validation.
- Focused Phase 7E3A smoke.
- Sales freeze protection.
- Full protected workspace gate.
- Source/live hash verification if runtime files change.
- Owner manual review before baseline closure.

## Test And Smoke Plan For Future Implementation

### Python Contract Tests

- Purchase Manager can read manager readiness overview.
- Purchase User access follows owner decision; default should deny Overview manager queue or return read-only limited context.
- Purchase User can read page-level readiness warnings where already allowed to view the page.
- Sales/Guest denied.
- PR readiness detects missing items, missing required dates, missing warehouses, and item context hold/not-reviewed states.
- RFQ readiness detects missing suppliers, missing item lines, supplier hold/missing email/contact review, item hold, and deferred send policy.
- SQ readiness detects missing rates, missing item lines, expired/missing validity where fields exist, and deferred award/SQ-to-PO policy.
- PO readiness detects missing supplier, items, rates, schedule/required dates, currency, item hold, and deferred release/send policy.
- Overview aggregation dedupes repeated supplier/item blockers.
- Readiness APIs do not mutate documents or create logs.
- No Communication, Email Queue, Contact, User, Item Price, Default Supplier, Item Supplier, submit, conversion, receipt, invoice, payment, or native route side effects.

### Governance Tests

- Manifest entries classify readiness as productized read-only actions.
- No normal Procurement `governed_native_action` entries are added.
- Native escape labels remain absent.
- Send/email/lifecycle forbidden symbols remain absent.

### Focused Smoke

For Purchase Manager:

- Overview shows Manager Readiness section.
- Manager readiness rows are visible and navigate only to productized routes.
- PR Review shows readiness card.
- RFQ Review shows readiness card plus existing Supplier Communication; Send RFQ remains disabled.
- Supplier Quotation Review shows readiness card and Compare offers remains navigation only.
- Purchase Order Follow-up or saved PO form shows release/draft readiness warning; no submit/send.
- Supplier Detail and Buying Item Detail fix links work and preserve protected edit/read-only role behavior.
- No native ERP labels or raw routes.
- No Frappe permission modals.
- No horizontal overflow at 1136, 1240, 1440.

For Purchase User:

- Page-level warnings are read-only.
- No manager-only edit/fix controls beyond already allowed protected pages.
- No lifecycle/send/conversion actions.
- No native ERP labels or raw routes.

### Manual Owner Review Checklist

- Manager Overview: confirm readiness queue wording is useful and not too verbose.
- PR Review: confirm sourcing readiness explains blockers without offering conversion.
- RFQ Review: confirm supplier/item readiness and disabled send policy are clear.
- SQ Review: confirm quote readiness explains missing rates/validity and deferred award.
- PO view/form: confirm PO release/send remains clearly deferred.
- Supplier and Item fix links: confirm they navigate to productized detail pages only.
- Confirm no native form, send, submit, conversion, receive, bill, payment, Item Price, Default Supplier, Contact/User, portal, or AI action appears.

## Deferred And Forbidden Scope

Explicitly not in Phase 7E3A:

- Native ERPNext form escape.
- RFQ send/email/SMTP.
- PO send/email.
- Communication or Email Queue creation.
- Contact/User creation or supplier portal activation.
- Submit, approval, reject, cancel, amend, close, hold, release, or workflow mutation.
- PR-to-RFQ conversion.
- RFQ-to-SQ conversion.
- SQ-to-PO conversion.
- PR/MR-to-PO conversion.
- Supplier Quotation award.
- Purchase Receipt / receiving.
- Purchase Invoice / billing.
- Payment.
- Item Price mutation.
- Item Supplier mutation.
- Item Default / Default Supplier mutation.
- Supplier master mutation beyond existing Phase 7E1A app-owned profile.
- Item master mutation beyond existing Phase 7E2A app-owned profile.
- Stock/accounting/UOM/valuation/reorder/variant changes.
- AI intake.
- Sales runtime changes.

## Owner Decisions Needed Before Implementation

1. Should Purchase User see the Overview-level Manager Readiness queue read-only, or only page-level warnings?
2. Which readiness queues should appear first: all five recommended groups, or RFQ/PO first?
3. Should saved managed forms show readiness cards immediately after save, or should readiness be limited to review pages in Phase 7E3A?
4. Should readiness issue links open in the same tab or new controlled tab? Default recommendation: same tab productized route.
5. Should manager readiness include report-derived exceptions in Phase 7E3A, or defer report aggregation until performance is proven?
6. What issue count limit should be shown on Overview? Default recommendation: count plus top three examples per group.
7. Should a future manager disposition/comment log be designed in Phase 7E3B after read-only readiness is accepted?

## Recommended Phase 7E3A Implementation Sequence

1. Backend read-only readiness service with unit tests.
2. Overview Manager Readiness card/queue for Purchase Manager only.
3. Page-level readiness cards for PR Review, RFQ Review, SQ Review, and PO view/form.
4. Productized fix navigation to Supplier Detail, Buying Item Detail, and managed draft forms where safe.
5. Governance manifest entries and static forbidden-symbol scans.
6. Focused Phase 7E3A smoke for Purchase Manager and Purchase User.
7. Sales freeze and full protected workspace gate.
8. Controlled live alignment and source/live hash verification.
9. Owner manual review.
10. Docs-only Phase 7E3A protected baseline closure after acceptance.

Do not implement Phase 7E3A from this design task.
