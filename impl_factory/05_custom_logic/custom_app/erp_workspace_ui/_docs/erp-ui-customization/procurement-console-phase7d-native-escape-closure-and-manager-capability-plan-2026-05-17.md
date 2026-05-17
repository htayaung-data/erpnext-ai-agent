# Procurement Console Phase 7D Native Escape Closure And Manager Capability Plan

Date: 2026-05-17

Source baseline: `feature/erpnext-ui-design` at or after `e8c3dae2e7ad55a39c66900de6cc30754998062c`.

Status: design and research only. No runtime code, smoke scripts, Sales files, or live deployment files are changed by this plan.

## 1. Executive Decision Summary

Procurement Console should stop treating raw ERPNext form navigation as a normal buyer or Purchase Manager workflow. The current `Open ERP Form`, `Open ERP Supplier Form`, and `Open ERP Item Form` actions were valid temporary governed exceptions while the managed buying family was incomplete. After Phase 5A through 5D and Phase 6C1/6C2A, the workspace is mature enough to replace those exits with productized Procurement capabilities.

The recommended policy is:

1. Purchase User should not see raw native ERPNext form exits from Procurement pages.
2. Purchase Manager should not see raw native ERPNext form exits as the normal way to perform work. The manager role should gain productized review, lifecycle, communication, conversion, supplier buying profile, and item buying-context capabilities instead.
3. Procurement Admin or System Manager may keep an explicit advanced native escape, but it should be admin-only, labeled as an advanced ERP action, visually separated from the premium workflow, and ideally audited before any implementation accepts it.
4. Existing native exits should be removed from normal user and manager surfaces in a controlled implementation phase, not edited ad hoc from one page.
5. If a business capability is still missing, the answer is not to leave raw ERPNext visible to managers forever. The answer is to define the productized replacement phase and keep a narrow admin escape until replacement is accepted.

Immediate next implementation recommendation: Phase 7D1 should hide or admin-gate all raw Procurement native form buttons for normal Purchase User and Purchase Manager roles, while preserving all protected managed forms, previews, PDF, readiness, reports, and review pages. Phase 7D1 must include a role matrix smoke and full protected workspace gate.

## 2. Current Native Escape Inventory

Inventory source basis: `erp_workspace_ui/procurement_console/*`, `erp_workspace_ui/public/js/procurement_console/*`, `erp_workspace_ui/workspace_governance_manifest.py`, protected baseline docs, and accepted smoke/manual behavior from the current Procurement baselines. No new runtime changes or live alignment were performed.

| Surface | Productized route | Visible native label | Target | Role visibility in current source | Current governance | Original reason | Current risk | Productized equivalent | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Supplier Detail | `/desk/procurement-console-supplier/<supplier>` | `Open ERP Supplier Form` | `Form/Supplier/<name>` | Purchase Manager or Purchase Master Manager with Supplier write permission | `procurement-open-supplier-form`, governed native action | Supplier edit was deferred while Supplier Detail was read-only | Exposes full Supplier master, contacts, portal users, comments, attachments, tools, and global supplier mutations | Read-only Supplier Detail exists; controlled supplier buying profile edit does not exist yet | Remove for Purchase User/Manager; keep admin-only only if owner approves; replace with Phase 7D2 Supplier Manager View/Edit |
| Buying Item Detail | `/desk/procurement-console-item/<item>` | `Open ERP Item Form` | `Form/Item/<name>` | Purchase Master Manager, Item Manager, Stock Manager, or System Manager with Item write permission; current tests exclude normal Purchase Manager | `procurement-open-item-form`, governed native action | Item edit was deferred while Item Detail was read-only | Exposes full Item master, stock/accounting attributes, UOM, variants, supplier items, Item Price/default supplier effects, and global item mutations | Read-only Buying Item Detail exists; controlled buying-context edit does not exist yet | Keep hidden from Purchase User/Manager; keep only master-data/admin roles; replace with Phase 7D3 Item Buying Context Edit |
| Purchase Request Review | `/desk/procurement-console-purchase-request-review/<mr>` | `Open ERP Form` | `Form/Material Request/<name>` | Any user with ERPNext write permission for Material Request | `procurement-open-erp-form`, governed native action | Advanced Material Request fields and submit flow were not productized | Native submit/cancel/amend/mapping to RFQ/PO/stock entry can appear outside controlled UI | Managed PR form and PR review exist | Admin-only near term; replace with Phase 7D4 lifecycle and Phase 7D5 conversion flows |
| RFQ Review | `/desk/procurement-console-rfq-review/<rfq>` | `Open ERP Form` | `Form/Request for Quotation/<name>` | Any user with ERPNext write permission for RFQ | `procurement-open-erp-form`, governed native action | Advanced RFQ fields, native print, and native send were not productized | Native submit can call supplier send behavior; native RFQ can create/update contacts and portal users; native print/email controls bypass Phase 6 policy | Managed RFQ form, RFQ review, supplier-specific preview/PDF, readiness panel exist | Admin-only near term; productized RFQ send remains deferred; no normal native escape |
| Supplier Quotation Review | `/desk/procurement-console-supplier-quotation-review/<sq>` | `Open ERP Form` | `Form/Supplier Quotation/<name>` | Any user with ERPNext write permission for Supplier Quotation | `procurement-open-erp-form`, governed native action | Advanced SQ fields and native conversion were not productized | Native submit, PO conversion, quotation/invoice mapping, and pricing fields can bypass governance | Managed Supplier Quotation form and review exist | Admin-only near term; replace with Phase 7D4 lifecycle and Phase 7D5 award/conversion |
| Saved Managed Purchase Request | `/desk/procurement-console-purchase-request-form/<mr>` | `Open ERP Form` | `Form/Material Request/<name>` | User with managed PR access plus ERPNext read/write | `procurement-managed-pr-open-native`, governed native action | Escape after save for fields not yet managed | Lets normal workflow leave protected form family after record creation | Managed PR and Review Request exist | Remove for normal Purchase User/Manager; use Review Request and future lifecycle/conversion actions |
| Saved Managed RFQ | `/desk/procurement-console-rfq-form/<rfq>` | `Open ERP Form` | `Form/Request for Quotation/<name>` | User with managed RFQ access plus ERPNext read/write | `procurement-managed-rfq-open-native`, governed native action | Escape after save for fields not yet managed | Bypasses supplier-specific output policy and disabled send governance | Managed RFQ saved form, RFQ review, preview/PDF/readiness exist | Remove for normal Purchase User/Manager; use productized review/output; admin-only escape if needed |
| Saved Managed Supplier Quotation | `/desk/procurement-console-supplier-quotation-form/<sq>` | `Open ERP Form` | `Form/Supplier Quotation/<name>` | User with managed SQ access plus ERPNext read/write | `procurement-managed-sq-open-native`, governed native action | Escape after save for fields not yet managed | Exposes submit/conversion/internal pricing actions outside managed guardrails | Managed SQ saved form and review exist | Remove for normal Purchase User/Manager; replace with lifecycle/award/conversion phases |
| Saved Managed Purchase Order | `/desk/procurement-console-purchase-order-form/<po>` | `Open ERP Form` | `Form/Purchase Order/<name>` | User with managed PO access plus ERPNext read/write | `procurement-managed-po-open-native`, governed native action | Escape after save for advanced PO fields | PO native form can expose submit, cancel, stop, receive, bill, print/email, and supplier commitment workflow | Managed PO draft form and PO follow-up exist | Remove for normal Purchase User/Manager; keep admin-only until lifecycle/output phases exist |
| Legacy native create routes in governance manifest | `Form/Material Request/new-purchase`, `Form/Request for Quotation/new`, `Form/Supplier Quotation/new`, `Form/Purchase Order/new` | native create route policy, not always visible as current primary UI | Native new documents | Manifest still records Phase 3 native create exceptions | `procurement-native-create-forms-phase3-v1` | Temporary before managed form family | Stale governance may legitimize direct native create if a future action accidentally points there | Managed PR/RFQ/SQ/PO create routes now exist | Retire or mark admin-only in Phase 7D1 governance update |

Other native leakage points to keep in future scans:

- Raw `frappe.set_route("Form", ...)` handlers in Procurement frontend route targets.
- Any row link that navigates to `Form/<doctype>/<name>` or `/app/<doctype>/<name>` instead of a productized route.
- Native report/query-report links. Current Phase 4 reports are productized and should remain that way.
- Native print/email/send/submit controls embedded in modals. Phase 6C1 already rejected this pattern for output previews.
- Framework tools menus, native comments/attachments, and workflow buttons visible through raw forms.

## 3. Industry ERP Research

### ERPNext / Frappe

ERPNext Buying documents provide native flows for Request for Quotation, Supplier Quotation, Purchase Order, Supplier, and Item. ERPNext RFQ supports sending requests to suppliers and supplier-specific quoting, Supplier Quotation can be mapped to Purchase Order, and Purchase Order drives later receiving and invoicing. The installed source confirms that native RFQ submit/send can touch supplier email/contact and portal-user paths, and native PO exposes downstream receipt/invoice paths.

Implication for this project: ERPNext native forms are powerful administrative objects, not just prettier versions of our managed pages. They are useful for administrators and fallback recovery, but they should not be the default premium Procurement Console experience.

References:

- ERPNext Request for Quotation: <https://docs.frappe.io/erpnext/user/manual/en/request-for-quotation>
- ERPNext Supplier Quotation: <https://docs.frappe.io/erpnext/supplier-quotation>
- ERPNext Purchase Order: <https://docs.frappe.io/erpnext/purchase-order>
- ERPNext Supplier: <https://docs.frappe.io/erpnext/supplier>
- ERPNext Item: <https://docs.frappe.io/erpnext/item>

### SAP S/4HANA

SAP procurement separates buyer work into role-specific apps for purchase requisitions, RFQs, supplier quotations, purchasing documents, output, and approvals. The product surface is organized by business action and app, not by exposing a single raw database form as the primary buyer path. Output management and supplier communication are controlled capabilities with configuration and document context.

Implication for this project: Purchase Managers should get productized procurement actions such as RFQ management, quotation comparison, purchasing document review, output, and approval. Advanced system maintenance should remain outside the normal buyer work area.

References:

- SAP S/4HANA Cloud sourcing and procurement documentation: <https://help.sap.com/docs/SAP_S4HANA_CLOUD>
- SAP S/4HANA Cloud output management documentation: <https://help.sap.com/docs/SAP_S4HANA_CLOUD/a630d57fc5004c6383e7a81efee7a8bb>

### Oracle Fusion Procurement

Oracle Procurement uses buyer and procurement work areas for requisitions, purchase orders, supplier negotiations, supplier invitations, and sourcing communication. Supplier invitations are explicit negotiation actions with selected suppliers, communication tracking, and controlled business state. Supplier profiles and setup are governed separately from day-to-day buying actions.

Implication for this project: RFQ send should remain a governed productized flow with selected suppliers, recipient validation, confirmation, and audit. Supplier master edits should not be a generic raw form escape for normal buyers.

References:

- Oracle Procurement supplier negotiation invitations: <https://docs.oracle.com/en/cloud/saas/procurement/24d/oaprc/invite-suppliers-to-a-negotiation.html>
- Oracle Procurement invite suppliers to negotiations: <https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/how-you-invite-suppliers-to-negotiations.html>

### Microsoft Dynamics 365 Supply Chain Management

Dynamics 365 Procurement and sourcing supports RFQ cases, vendor replies, purchase order workflows, confirmations, and vendor collaboration. Buyer actions are routed through procurement workspaces and workflows. Purchase order approval/confirmation and vendor collaboration are controlled areas rather than unrestricted native object editing.

Implication for this project: Productized worklists, reports, RFQ communication, and approval/conversion flows are the right direction. Raw native forms should not be the operational manager UX.

References:

- Microsoft Dynamics 365 request for quotations: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations>
- Microsoft Dynamics 365 Procurement and sourcing documentation: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/>

### Odoo Purchase

Odoo Purchase exposes RFQ and Purchase Order flows with email to vendors, vendor bills, receipts, and access rights. The buyer experience is built around business documents and actions such as RFQ send, purchase order confirmation, receipts, and bills. User access rights separate ordinary users from managers and system configuration.

Implication for this project: RFQ/PO communication and lifecycle actions should be productized and permissioned. Master data and system configuration should remain controlled, not surfaced as raw form exits.

References:

- Odoo Purchase RFQ flow: <https://www.odoo.com/documentation/saas-18.1/applications/inventory_and_mrp/purchase/manage_deals/rfq.html>
- Odoo Purchase application documentation: <https://www.odoo.com/documentation/saas-18.1/applications/inventory_and_mrp/purchase.html>

## 4. ERPNext-Specific Capability And Risk Mapping

| DocType | Native capabilities | Side effects and risks if raw form is exposed | Current productized coverage | Missing manager capability |
| --- | --- | --- | --- | --- |
| Material Request | create/edit, submit/cancel, item demand, schedule dates, mappings to RFQ/PO/SQ/Stock Entry | Submit/cancel changes procurement demand state; mapping can create downstream buying documents; default supplier can influence mapping | Managed PR draft form; PR review; reports | Productized submit/reject/hold; controlled PR-to-RFQ and PR/MR-to-PO conversion; audit/history |
| Request for Quotation | create/edit, suppliers/items, submit, send to suppliers, supplier-specific PDF/portal link, Supplier Quotation mapping | Installed source shows `on_submit()` calls supplier send path; RFQ send can validate supplier email, create/update Contact, create User, and update Supplier portal users; native form exposes print/email/tools | Managed RFQ form; RFQ review; supplier-specific preview/PDF; recipient readiness; send disabled | Governed RFQ send after email/domain policy; controlled RFQ lifecycle; PR-to-RFQ conversion |
| Supplier Quotation | create/edit, submit/cancel, update RFQ supplier status, map to Purchase Order, Purchase Invoice, Quotation | Submit and conversion can affect sourcing decisions and downstream purchasing; rates and taxes are sensitive | Managed SQ form; SQ review; quote comparison report | Quotation award/select preferred supplier; controlled SQ-to-PO conversion; lifecycle governance |
| Purchase Order | create/edit draft, submit/cancel/stop, supplier terms, taxes, schedule dates, receipt, invoice, portal invoice and related flows | PO submit is a supplier commitment; receive/bill/payment touch warehouse/finance ownership; native form exposes lifecycle and output controls | Managed PO draft form; PO follow-up/reports; internal preview/PDF from Phase 6C1 | PO approval/submit governance; PO output/send after approval; receive/bill ownership boundaries |
| Supplier | full master data, contacts, addresses, portal users, tax/category fields, payment and buying profile | Supplier edits affect every buying flow; portal user handling can grant external access; contacts and addresses are enterprise master data | Supplier Directory and Supplier Detail read views | Controlled supplier buying profile updates; supplier contact/email request workflow; admin-only full master edit |
| Item | full master data, UOM, stock/accounting, supplier items, item defaults, default supplier, Item Price logic | Item edits affect stock, accounting, sales, purchasing, pricing, and default supplier behavior across ERP | Buying Items directory and Item Detail read views | Controlled buying-context edits only: purchase UOM/lead time/preferred supplier request, not full Item master |

## 5. Purchase Role Model

### Purchase User

Purpose: operational buyer or requester working inside protected Procurement surfaces.

Allowed now:

- View Procurement overview, directories, detail pages, reports, and productized review pages.
- Create and edit managed PR/RFQ/SQ/PO drafts where current protected phases allow it.
- Use supplier-specific RFQ preview/PDF and readiness information.
- Use productized report drilldowns and productized detail routes.

Not allowed:

- Raw native ERP form escape.
- Submit/approve/reject/cancel/stop.
- RFQ email/send, PO send, or supplier portal actions until governed phases exist.
- PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, PR/MR-to-PO conversion until governed phases exist.
- Supplier master, Item master, Item Price, Default Supplier, Contact, User, or portal mutation.

### Purchase Manager

Purpose: accountable purchasing manager who needs real authority, but through controlled productized actions.

Allowed now:

- All Purchase User capabilities.
- View supplier/item/procurement performance surfaces.
- Use manager-level review and readiness views where currently implemented.

Future productized capabilities to add:

- Review/approve/submit/reject selected procurement documents after Phase 7D4 design.
- Governed RFQ send when email/domain and owner policy are ready.
- Quote comparison, supplier award, and preferred supplier selection workflow.
- Controlled conversion from approved PR/RFQ/SQ into downstream documents.
- Controlled supplier buying profile updates, such as buying contact/email, supplier tags, lead time, and preferred communication method if owner approves.
- Controlled item buying-context updates, such as purchase UOM, lead time, procurement notes, and supplier item cross-reference if owner approves.
- Audit/history review for comments, attachments, output, and document state.

Not allowed as normal workflow:

- Raw `Open ERP Form` buttons.
- Full Supplier or Item master edit via native forms.
- Native submit/send/receive/bill/payment actions outside controlled pages.
- Portal user, Contact, User, Item Price, or Default Supplier mutation without a separate phase.

### Procurement Admin / System Manager

Purpose: system maintenance and emergency recovery, not daily purchasing.

Possible native access policy:

- May access native ERP forms through Desk outside the Procurement Console, using normal ERPNext permissions.
- If the owner wants an in-console action, it should be a hidden/admin-only `Advanced ERP Form` action, not `Open ERP Form` in the normal toolbar.
- It should be visibly marked as leaving the productized Procurement flow.
- It should open in a separate tab or controlled route to avoid accidental state loss.
- It should be auditable if Frappe/event logging support is added in a later implementation.

## 6. Page-By-Page Recommendation Table

| Page/action | Decision | Replacement or follow-up | Owner decision needed |
| --- | --- | --- | --- |
| Supplier Detail `Open ERP Supplier Form` | Make admin-only or remove from normal Procurement UI | Phase 7D2 Supplier Manager View/Edit for buying profile only | Decide whether Procurement Admin escape is visible in-console or only through ERP Desk |
| Buying Item Detail `Open ERP Item Form` | Keep out of normal Purchase User/Manager UI; existing role gate is already stricter than Supplier | Phase 7D3 Item Buying Context Edit; no full Item master edit | Decide which item buying fields managers may request/update |
| PR Review `Open ERP Form` | Remove/admin-gate for normal roles | Productized lifecycle and conversion pages | Decide whether PR submit belongs to Purchase Manager or another approver |
| RFQ Review `Open ERP Form` | Remove/admin-gate for normal roles | Existing preview/PDF/readiness; future governed send and lifecycle | Decide RFQ submit/send policy before send implementation |
| SQ Review `Open ERP Form` | Remove/admin-gate for normal roles | Quote comparison, award, and SQ lifecycle/conversion | Decide manager authority for awarding supplier quotations |
| Saved Managed PR `Open ERP Form` | Remove/admin-gate for normal roles | Use Review Request; future lifecycle/conversion actions | Decide timing relative to Phase 7D1 |
| Saved Managed RFQ `Open ERP Form` | Remove/admin-gate for normal roles | Use Review RFQ and Supplier Communication | Confirm no native RFQ send exposure remains acceptable |
| Saved Managed SQ `Open ERP Form` | Remove/admin-gate for normal roles | Use Review Quote and future award/conversion | Decide SQ award flow ownership |
| Saved Managed PO `Open ERP Form` | Remove/admin-gate for normal roles | Use PO follow-up/review and future approval/output | Decide PO approval/submit ownership before PO send |
| Manifest native create exceptions | Retire or convert to admin-only governance | Managed create routes are protected for PR/RFQ/SQ/PO | Decide whether any legacy native create path remains needed for admin recovery |

## 7. Productized Replacement Roadmap

### Phase 7D1: Native Escape Closure For Normal Roles

Business purpose: prevent normal Procurement users and managers from leaving the protected console through raw ERPNext forms.

Scope:

- Hide/remove native form buttons for Purchase User and Purchase Manager on all inventoried Procurement surfaces.
- Keep optional admin-only `Advanced ERP Form` only if owner approves.
- Update governance manifest, tests, and smoke scans.

Exclusions:

- No lifecycle, send, conversion, supplier edit, or item edit implementation.
- No Sales changes.

Validation/protection:

- Role matrix smoke for Purchase User, Purchase Manager, and admin if enabled.
- Scan every Procurement route for `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, raw `Form/`, and `/app/` navigation for normal roles.
- Focused affected Procurement smoke plus full protected workspace gate and Sales freeze.

### Phase 7D2: Supplier Manager View/Edit Design

Business purpose: give Purchase Manager controlled buying-profile authority without full Supplier master exposure.

Candidate scope:

- Supplier buying profile panel: purchasing contact display, email readiness, payment/terms display if safe, preferred communication notes, supplier status/readiness, attachments/history.
- Controlled edit/request flow for buying contact/email, not portal users.

Exclusions:

- No full Supplier master edit.
- No Contact/User creation unless separately approved.
- No supplier portal invitation.

Validation/protection:

- Supplier role tests, no master-data leakage, no portal/user mutation, protected gate.

### Phase 7D3: Item Buying Context View/Edit Design

Business purpose: let buyers manage purchasing context while protecting global Item master data.

Candidate scope:

- Purchase UOM display, supplier item references, buying lead time, procurement notes, default warehouse display, supplier relationship readiness.
- Controlled request/update for buying-only fields if owner approves.

Exclusions:

- No stock/accounting/variant edit.
- No Item Price mutation.
- No Default Supplier mutation unless a later governed supplier-selection phase approves it.

Validation/protection:

- Item role tests, no Sales item behavior regression, protected gate and Sales freeze if shared item surfaces are touched.

### Phase 7D4: Document Lifecycle Governance Design

Business purpose: define how PR/RFQ/SQ/PO move from draft to reviewed/submitted/approved without native form exposure.

Candidate scope:

- Productized submit, approve, reject, hold, cancel/stop policy by DocType.
- Role and approval matrix.
- State labels and audit trail.

Exclusions:

- Receiving, billing, payment, and email send unless explicitly included later.

Validation/protection:

- Strong backend permission tests, lifecycle state tests, governance tests, protected gate.

### Phase 7D5: Conversion Workflows

Business purpose: replace native document mapping actions with productized conversions.

Candidate flows:

- PR -> RFQ.
- RFQ -> Supplier Quotation where appropriate.
- SQ -> PO.
- PR/MR -> PO.

Prerequisites:

- Lifecycle/submission policy, because ERPNext mappings often require submitted or status-qualified upstream documents.
- Role ownership and audit model.

Exclusions:

- No automatic conversion without explicit preview and confirmation.
- No Item Price or Default Supplier mutation.

### Phase 7D6: Supplier Communication Finalization

Business purpose: enable governed RFQ send and later PO send after email/domain infrastructure and owner policy are ready.

Scope direction:

- Continue from Phase 6C2A readiness and Phase 6C2B design.
- RFQ send before PO send, because PO send is a supplier commitment.

Exclusions:

- No active send until owner confirms email provider, domain/DNS, sender identity, audit, and confirmation policy.

### Phase 7D7: Attachments, Comments, And History

Business purpose: replace useful native form collaboration features with productized audit surfaces.

Scope direction:

- Attachments list/add where safe.
- Internal comments/activity timeline.
- Output and lifecycle history.

Exclusions:

- No native form reliance for routine collaboration.

## 8. Native Escape Policy Proposal

Recommended final policy:

| Role | Should see native ERP escape in Procurement Console? | Policy |
| --- | --- | --- |
| Purchase User | No | Productized Procurement routes only. No raw native form buttons. |
| Purchase Manager | No for normal workflow | Productized manager actions replace native forms. No raw `Open ERP Form` buttons as day-to-day tools. |
| Procurement Admin/System Manager | Possibly, if owner approves | Optional admin-only `Advanced ERP Form`, visually separated, warned, and ideally audited. |

Labeling if retained for admin:

- Use `Advanced ERP Form`, not `Open ERP Form`.
- Include explanatory text: `Leaves the protected Procurement Console and opens ERPNext administration.`
- Do not place it next to primary buyer actions.
- Prefer opening in a separate tab/window to avoid confusing productized navigation state.
- Add governance manifest classification as an admin-only native exception with explicit phase reference.

Owner-facing premium UI rule:

- Normal buyer and manager screens should not display raw ERPNext escape buttons once Phase 7D1 is accepted.
- If a required business action is missing, create a productized phase for it rather than exposing the native form.

## 9. Testing And Protection Plan

Future implementation must add or update tests/smokes before removing native exits.

Required Python tests:

- Governance manifest classifies all normal Procurement routes as productized, not native form routes.
- Purchase User contexts do not return native form actions.
- Purchase Manager contexts do not return native form actions.
- Admin/System Manager native escape appears only if explicitly enabled by owner policy.
- Supplier Detail, Item Detail, PR Review, RFQ Review, SQ Review, and saved managed PR/RFQ/SQ/PO contexts return productized actions only for normal roles.
- RFQ send remains disabled and no SMTP/send endpoint returns.
- No submit/approve/conversion/lifecycle actions are introduced by Phase 7D1.

Required smoke coverage:

- Visit every Procurement route for Purchase User and Purchase Manager.
- Assert no visible labels: `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, `Advanced ERP Form` for normal roles.
- Click every visible primary/secondary action and verify it stays in productized `/desk/procurement-console-*` routes unless admin-only role is under test.
- Assert no raw `Form/` route or `/app/` route navigation for normal roles.
- Verify reports still route through productized report pages.
- Verify RFQ Preview/PDF/readiness remains intact and Send RFQ remains disabled.
- Verify managed PR/RFQ/SQ/PO forms still save drafts and productized review links still work.
- Full protected workspace gate and Sales freeze must pass.

Manual review checklist:

1. Supplier Detail no longer presents a normal-manager native escape, or shows an owner-approved admin-only escape only for the admin role.
2. Buying Item Detail follows the same policy.
3. Saved managed buying forms remain usable without native escape.
4. Review pages remain useful and do not feel like dead ends.
5. Purchase Manager still has a credible roadmap for business authority.

## 10. Deferred Scope

This Phase 7D plan does not implement or approve:

- Runtime removal of native buttons.
- Supplier edit or master-data mutation.
- Item edit, Item Price mutation, or Default Supplier mutation.
- Submit, approve, reject, cancel, stop, receive, bill, or payment.
- RFQ email/send or SMTP runtime.
- Supplier portal invitation, Contact creation, User creation, or Communication/Email Queue creation.
- PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, or PR/MR-to-PO conversion.
- PO send or supplier commitment output.
- Broad Procurement redesign unrelated to native escape closure.
- Any Sales Console runtime change.

## 11. Open Owner Decisions

Before Phase 7D1 implementation, the owner should decide:

1. Should Procurement Admin/System Manager have an in-console `Advanced ERP Form` escape, or should admin native access happen only through standard ERPNext Desk outside Procurement Console?
2. If an admin escape remains, should it open in a separate browser tab and should it require a confirmation modal?
3. Should admin native escape usage be audited immediately, or can audit wait for a later platform audit phase?
4. Which Supplier buying-profile fields should Purchase Manager be allowed to update in a productized future phase?
5. Which Item buying-context fields should Purchase Manager be allowed to update without touching global Item master data?
6. Who owns PR/RFQ/SQ/PO submit/approve/reject in the future role matrix?
7. Should Purchase User retain draft creation for SQ and PO, or should those be Purchase Manager-only after lifecycle governance is designed?
8. What is the priority order after Phase 7D1: Supplier Manager edit, Item Buying Context edit, document lifecycle, conversions, or RFQ send finalization?

## Final Recommendation

Proceed next with Phase 7D1 Native Escape Closure for normal roles. It should be a narrow implementation: no new business mutations, no send, no lifecycle, no conversions, and no master-data edits. Its purpose is to close the raw native ERP exit pattern while preserving all protected Procurement capabilities and setting the stage for manager-grade productized replacements.
