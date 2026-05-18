# Procurement Console Phase 7E Operations Capability Gap Audit

Date: 2026-05-18

Branch: `feature/erpnext-ui-design`

Scope: ERP Operations Reviewer audit only. No runtime, smoke, Sales Console, live alignment, send/email, conversion, submit/approval, receiving, billing, payment, Item Price, Default Supplier, supplier portal, or AI intake work is included.

## Executive Summary

The Procurement Console is operationally safe for the current protected phase after Phase 7D1. Normal Purchase User, Purchase Manager, and Purchase Master Manager paths no longer expose raw ERPNext form escape actions from the productized Procurement pages reviewed in Phase 7D1. Current behavior is coherent as a controlled draft-entry, read-only review, reporting, and output-preview workspace.

The workspace is not yet operationally complete for mature Purchase Manager work. Removing native form escapes closed the unsafe bypass, but it also exposed the next product gap: managers now need controlled, productized ways to maintain supplier buying readiness and item procurement context without reopening raw master-data forms. RFQ send readiness already tells buyers when supplier email/contact data is missing, but there is no safe Procurement Console action to correct that readiness.

The biggest business gap is Purchase Manager enablement after native escape closure, not send or conversion. The next implementation phase should be Phase 7E1, Productized Supplier Buying Profile and Contact Readiness. It should let managers maintain only approved buying-facing supplier readiness fields and recipient choices under audit, while forbidding supplier creation, disablement, tax/accounting/bank fields, portal users, Contact/User creation, and native form escape.

Submit, approval, conversion, external send, receiving, billing, payment, Item Price mutation, Default Supplier mutation, supplier portal, and AI intake should remain deferred until explicit workflow governance exists. Reports are useful, but they intentionally stop at review and drilldown; they do not yet support award, release, or conversion decisions.

## Source Gate Result

- Confirmed branch: `feature/erpnext-ui-design`.
- Confirmed HEAD: `4c7f06cbc4ca9f3a0d2b5207aa777095888f3833`.
- Confirmed Phase 7D1 correction commit `4c7f06cbc4ca9f3a0d2b5207aa777095888f3833` is HEAD and therefore included.
- Confirmed working tree was clean except the allowed untracked `ui_smoke/sales_final_acceptance_audit.js` before this docs-only audit began.

## Scope Reviewed

Docs read for current protected baselines:

- `_docs/erp-ui-customization/README.md`
- `_docs/erp-ui-customization/procurement-console-phase7d1-native-escape-closure-baseline-2026-05-18.md`
- `_docs/erp-ui-customization/procurement-console-phase7d-native-escape-closure-and-manager-capability-plan-2026-05-17.md`
- `_docs/erp-ui-customization/procurement-console-phase5a-5b-managed-buying-baseline-2026-05-15.md`
- `_docs/erp-ui-customization/procurement-console-phase5c-managed-supplier-quotation-baseline-2026-05-15.md`
- `_docs/erp-ui-customization/procurement-console-phase5d-managed-purchase-order-baseline-2026-05-15.md`
- `_docs/erp-ui-customization/procurement-console-phase6c1-output-preview-pdf-baseline-2026-05-16.md`
- `_docs/erp-ui-customization/procurement-console-phase6c2a-rfq-send-readiness-baseline-2026-05-16.md`
- `_docs/erp-ui-customization/procurement-console-phase6c2b-rfq-governed-send-design-plan-2026-05-16.md`
- `_docs/erp-ui-customization/procurement-console-phase6c2c-rfq-test-send-deferral-plan-2026-05-17.md`

Source areas inspected:

- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/procurement_console/service.py`
- `erp_workspace_ui/procurement_console/worklist.py`
- `erp_workspace_ui/procurement_console/requests.py`
- `erp_workspace_ui/procurement_console/sourcing.py`
- `erp_workspace_ui/procurement_console/purchase_orders.py`
- `erp_workspace_ui/procurement_console/purchase_order_follow_up.py`
- `erp_workspace_ui/procurement_console/purchase_order_detail.py`
- `erp_workspace_ui/procurement_console/supplier_detail.py`
- `erp_workspace_ui/procurement_console/items.py`
- `erp_workspace_ui/procurement_console/report.py`
- `erp_workspace_ui/procurement_console/document_reviews.py`
- `erp_workspace_ui/procurement_console/document_output.py`
- `erp_workspace_ui/procurement_console/managed_purchase_request.py`
- `erp_workspace_ui/procurement_console/managed_rfq.py`
- `erp_workspace_ui/procurement_console/managed_supplier_quotation.py`
- `erp_workspace_ui/procurement_console/managed_purchase_order.py`
- `erp_workspace_ui/public/js/procurement_console/*`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_shell_content.js`
- `erp_workspace_ui/tests/test_procurement_console_phase0_contracts.py`
- `erp_workspace_ui/tests/test_workspace_governance_manifest.py`

ERPNext installed source note:

- No importable `erpnext` Python package or `apps/erpnext` source tree was found on this host during the audit search. ERPNext source-level implications in this document therefore come from the current app comments that reference native ERPNext mappers and from official ERPNext documentation.

## Baseline Understanding

Sales Console remains frozen and protected. This audit did not inspect Sales behavior beyond README/governance context and did not change Sales files. Any future Procurement work must continue to pass the protected workspace gate when runtime or smoke scripts change.

Procurement Phase 7D1 is a protected native escape closure, not a final Procurement freeze. It removed normal-role links labeled `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, and `Advanced ERP Form` from productized Procurement paths. Admin access to raw ERPNext Desk remains outside the Procurement Console.

Managed Procurement forms currently support draft creation and draft update only:

- Purchase Request is a managed Material Request draft restricted to `material_request_type = Purchase`.
- RFQ is a managed Request for Quotation draft with supplier rows, item rows, supplier-specific preview/PDF, recipient readiness, and disabled send.
- Supplier Quotation is a managed direct draft entry for supplier offers.
- Purchase Order is a managed direct draft entry with preview/PDF marked as not supplier commitment.

Document review/detail/report pages are read-only operational surfaces. They support productized navigation and drilldown, not native document lifecycle actions.

## Current Protected Capability Map

| Surface | Current purpose | Primary role | Current action available | Operational classification | Immediate gap |
| --- | --- | --- | --- | --- | --- |
| Overview | Buyer workbench, counters, create cards, report shortcuts | Purchase User, Purchase Manager | Navigate to queues/reports, create draft PR/RFQ/SQ/PO when DocType permissions allow | Productized overview | Manager next-step decisions are mostly navigation, not governed actions |
| Supplier Directory | Supplier visibility for buying coordination | Purchase User, Purchase Manager | Filter, open Supplier Detail | Read-only worklist | No controlled supplier buying profile update |
| Supplier Detail | Supplier activity, contacts, RFQs, quotations, POs | Purchase Manager | Back, Refresh, productized PO drilldown | Read-only detail | Missing contact/email readiness management and buyer-owned supplier context |
| Buying Item Directory | Purchase-enabled item visibility | Purchase User, Purchase Manager | Filter, open Buying Item Detail | Read-only worklist | No controlled item procurement context update |
| Buying Item Detail | Item suppliers, buying prices, quotations, POs | Purchase Manager | Back, Refresh, productized PO drilldown | Read-only detail | Missing Item Supplier context governance; Item Price remains forbidden |
| Purchase Request Directory | Purchase Material Requests and requests to source | Purchase User, Purchase Manager | Review Request, New Purchase Request when permitted | Worklist plus draft create | No source/convert action |
| Purchase Request Review | Internal demand review before sourcing/order follow-up | Purchase Manager | Back, Refresh | Read-only review | No manager disposition, no PR-to-RFQ/PO conversion |
| Managed Purchase Request | Draft purchase demand entry | Purchase User, Purchase Manager | Save Draft, Reset, Review Request | Draft-entry form | No submit/approval; submitted PR opens read-only review |
| RFQ Directory | RFQ visibility and supplier response posture | Purchase User, Purchase Manager | Review RFQ, New RFQ when permitted | Worklist plus draft create | No release/send/ready-to-send state |
| RFQ Review | Read-only sourcing review, supplier rows, output/readiness | Purchase Manager | Back, Refresh, Preview RFQ, Download RFQ PDF, Recipient readiness, disabled Send RFQ | Review/output/readiness | No productized way to fix supplier recipient data |
| Managed RFQ | Draft RFQ entry | Purchase User, Purchase Manager | Save RFQ, Reset, Review RFQ, Preview/PDF/readiness, disabled Send RFQ | Draft-entry plus output/readiness | No submit, send, RFQ-to-SQ linkage, or supplier portal |
| Supplier Quotation Directory | Supplier offer visibility | Purchase User, Purchase Manager | Review Quote, New Supplier Quotation when permitted | Worklist plus draft create | No award/create PO action |
| Supplier Quotation Review | Offer review, validity, totals, quoted lines | Purchase Manager | Back, Refresh, Compare offers | Read-only review | Compare has no governed award next step |
| Managed Supplier Quotation | Direct supplier offer draft entry | Purchase User, Purchase Manager | Save Quotation, Reset, Review Quotation | Draft-entry form | No RFQ-linked intake, submit, Item Price, Default Supplier, PO creation |
| Purchase Order Directory | PO visibility and draft creation | Purchase User, Purchase Manager | Open follow-up, New Purchase Order when permitted | Worklist plus draft create | No manager release/approval/send workflow |
| PO Follow-up Detail | Supplier follow-up, receipt and billing visibility | Purchase User, Purchase Manager | Back, Refresh | Read-only lifecycle visibility | No receiving/billing execution, correctly outside Procurement |
| Managed Purchase Order | Direct draft PO entry and internal output | Purchase User, Purchase Manager | Save Purchase Order, Reset, Review Purchase Order, Preview/Download PO PDF, disabled supplier send | Draft-entry plus internal output | No submit/approval/release/send; draft output can look close to a supplier document unless warning remains prominent |
| Reports Index | Procurement report catalog | Purchase Manager | Open four ready reports | Read-only report index | No action bridge from report finding to manager workflow |
| Quote Comparison | Supplier offer comparison | Purchase Manager | Filter/report, productized drilldown | Read-only report | No award decision, no SQ-to-PO handoff |
| Purchase Order Analysis | PO value/receiving/billing posture | Purchase Manager | Filter/report, productized PO/Supplier/Item drilldown | Read-only report | Useful but cannot trigger release/follow-up tasks |
| Demand-to-Order Coverage | Demand coverage status | Purchase Manager | Filter/report, productized PR/PO/Item drilldown | Read-only report | No source/order conversion action |
| Item Purchase History | Buying history by item/supplier/order | Purchase Manager | Filter/report, productized drilldown | Read-only report | No controlled update to item supplier or buying terms |
| RFQ Supplier Communication | Recipient readiness only | Purchase Manager | View recipient/outgoing email readiness, disabled send | Read-only readiness | Missing supplier contact correction path |
| PO Document Output | Internal draft PO preview/PDF | Purchase Manager | Preview/Download PDF, disabled supplier send | Internal draft output | Needs future release/send governance before supplier use |

## Industry ERP Findings

Source notes from official documentation and primary vendor docs:

- ERPNext separates Material Request demand, Request for Quotation sourcing, Supplier Quotation supplier offers, and Purchase Order supplier commitment in the Buying flow. The official docs describe each document as a separate operational step: [Material Request](https://docs.frappe.io/erpnext/material-request), [Request for Quotation](https://docs.frappe.io/erpnext/request-for-quotation), [Supplier Quotation](https://docs.frappe.io/erpnext/supplier-quotation), and [Purchase Order](https://docs.frappe.io/erpnext/purchase-order).
- ERPNext Supplier and Item are shared master records, not buyer-only notes. Their docs show broad master-data scope: [Supplier](https://docs.frappe.io/erpnext/supplier) and [Item](https://docs.frappe.io/erpnext/item). This supports keeping raw master forms out of normal buyer paths.
- SAP procurement patterns separate requisition workflow, RFQ/quotation handling, and purchase order processing under role and workflow controls. Relevant official SAP sources include [purchase requisition workflow for procurement professionals](https://help.sap.com/docs/buying-invoicing/purchasing-guide-for-procurement-professionals/about-workflow-of-purchase-requisitions-8b3f5dbe7a7b4427a1039a46dfe475d3) and S/4HANA sourcing/procurement RFQ and PO management help pages.
- Oracle Procurement uses procurement-agent permissions and negotiation award flows, where awarding a negotiation and creating purchasing documents are controlled capabilities rather than generic form edits. See Oracle docs on [procurement agents](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faicf/define-procurement-agents.html) and [awarding negotiations](https://docs.oracle.com/en/cloud/saas/procurement/25b/oaprc/how-you-award-negotiations.html).
- Microsoft Dynamics 365 Procurement and sourcing describes purchase requisitions, RFQs, supplier bids, approved vendor lists, POs, receiving, invoices, and vendor collaboration as related but separately controlled processes. See [Procurement and sourcing overview](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview), [Purchase order overview](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-order-overview), [vendor collaboration](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/vendor-collaboration-work-external-vendors), and [approve vendors for products](https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/tasks/approve-vendors-specific-products).
- Odoo Purchase tracks RFQs, quotations, and purchase orders; confirmation turns an RFQ into an order. Vendor pricelists and product-vendor data can auto-populate RFQs/POs, which supports treating supplier/item buying context as governed master data. See [Odoo Purchase](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase.html), [Requests for quotation](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html), and [Vendor pricelists](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/products/pricelist.html).

Operational conclusions:

- Purchase Users typically enter demand/sourcing/order drafts, gather supplier responses, and follow up open operational queues within permissions.
- Purchase Managers typically review exceptions, approve or release governed steps, maintain buying-facing supplier and item context, select suppliers, and monitor KPIs.
- Supplier and item master data changes affect the whole ERP. Buyer workspace edits should be limited to controlled buying context, with audit trail and role gates.
- RFQ send/release, PO release/send, submit, approval, award, conversion, and cancellation should be workflow-gated and auditable.
- Warehouse execution owns receiving. Finance execution owns vendor invoices, billing, and payment. Procurement can view posture but should not execute those actions from this workspace without cross-functional scope.

## Purchase User Versus Purchase Manager Responsibility Matrix

| Capability | Purchase User current | Purchase User target | Purchase Manager current | Purchase Manager target | Boundary |
| --- | --- | --- | --- | --- | --- |
| View supplier/item/worklists | Yes | Yes | Yes | Yes | Productized Procurement only |
| Create draft Purchase Request | Permission-based | Yes for demand entry | Permission-based | Yes, plus review | Draft only until workflow approved |
| Create draft RFQ | Permission-based | Yes for sourcing prep | Permission-based | Yes, plus release readiness | No send until governed |
| Create draft Supplier Quotation | Permission-based | Yes for manual quote capture if allowed | Permission-based | Yes, plus comparison and award recommendation | No Item Price/Default Supplier mutation |
| Create draft Purchase Order | Permission-based | Possibly limited by policy | Permission-based | Yes for draft ordering | No supplier commitment until release/submit |
| Review submitted/current documents | Yes, read-only | Yes | Yes, read-only | Yes, with manager dispositions later | Productized pages only |
| Supplier buying profile edit | No | No or request-only | No | Yes, controlled fields only | No raw Supplier form |
| Supplier contact/email readiness | View only via RFQ readiness | Request correction | View only | Maintain approved recipient readiness under audit | No portal/User creation |
| Item buying context edit | No | No or request-only | No | Yes, controlled Item Supplier/buying context only | No Item Price/Default Supplier |
| PR/RFQ/SQ/PO submit/approve/release | No | No | No | Future governed manager workflow | Deferred |
| PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, PR-to-PO conversion | No | No | No | Future governed conversion workflow | Deferred until source state governance |
| RFQ/PO external send | No | No | Disabled | Future manager-only governed send | Requires email infrastructure and audit |
| Receiving | View posture only | View posture only | View posture only | View posture only | Warehouse owns execution |
| Billing/payment | View posture only | View posture only | View posture only | View posture only | Finance owns execution |
| Admin/master setup | No | No | No | No normal workflow | System Manager/Admin outside Procurement Console |

## Native Escape Closure Impact Assessment

Phase 7D1 fixed a blocker by removing raw form escape from normal Procurement Console paths. The remaining impact is a controlled capability gap, not a reason to reintroduce native links.

| Area | What native escape used to allow | 7D1 current state | Business risk if not productized | Recommendation |
| --- | --- | --- | --- | --- |
| Supplier Detail | Edit broad Supplier master, contacts, portal/user-related data | Read-only supplier profile | Managers cannot fix RFQ recipient readiness or buying notes inside workspace | Implement controlled Supplier Buying Profile and Contact Readiness |
| Buying Item Detail | Edit broad Item, Item Supplier, Item Price, Default Supplier, stock/accounting fields | Read-only item buying context | Managers cannot maintain approved supplier/lead-time context | Implement controlled item procurement context, excluding price/default supplier |
| PR Review | Submit/cancel/amend/convert via native Material Request | Read-only review | No manager disposition or sourcing action | Design review/readiness states before submit/conversion |
| RFQ Review/Form | Submit/send/create supplier portal/contact/users via native RFQ | Preview/readiness only; send disabled | No external RFQ communication, but safe | Keep send deferred until supplier/email policy is approved |
| SQ Review/Form | Submit/create PO/update price/default supplier via native SQ | Draft entry/review/compare only | No award or PO handoff | Design award/conversion workflow first |
| PO Form/Follow-up | Submit/cancel/receive/bill/print/email via native PO | Draft entry, internal preview/PDF, read-only follow-up | No release or supplier commitment inside workspace | Design PO release governance before send/submit |

## Gap Classification Table

| Gap | Route/page | Role affected | Classification | Severity | ERP expectation | Recommendation | Timing | Required gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Controlled supplier buying profile and recipient readiness | Supplier Detail, Managed RFQ, RFQ Review | Purchase Manager | Must implement soon | High | Managers need controlled supplier readiness without broad master access | Phase 7E1 with manager-only controlled fields and audit | Now-next | Unit tests, manager/user role smoke, native-escape static checks |
| Controlled item procurement context | Buying Item Detail, Item Purchase History | Purchase Manager | Must implement soon | High | Approved supplier/item sourcing data guides buying | Phase 7E2 for Item Supplier or buying-context fields only | Next | Unit tests, role smoke, Item Price/Default Supplier negative tests |
| Manager review/disposition readiness | PR/RFQ/SQ/PO review pages | Purchase Manager | Must implement soon | High | Managers need productized approve/reject/release-ready decisions before lifecycle actions | Phase 7E3 design/implementation of readiness states/comments without submit | After 7E1/7E2 | Workflow-state contract tests and audit-log expectations |
| Quote Comparison has no award handoff | Quote Comparison, SQ Review | Purchase Manager | Deferred until workflow governance exists | High | Quote comparison normally leads to supplier selection/award/PO | Design award and SQ-to-PO conversion before implementation | Phase 7E4 | Conversion design baseline, no native mapper until governed |
| PR-to-RFQ and PR-to-PO conversion missing | PR Review, Demand-to-Order Coverage | Purchase Manager | Deferred until workflow governance exists | High | Submitted demand can source/order through governed mappings | Define source state, approvals, rollback/cancel, and source-reference preservation | Phase 7E4 | Mapper tests, source state tests, no custom-copy shortcuts |
| RFQ governed send missing | RFQ Review, Managed RFQ | Purchase Manager | Deferred until infrastructure/governance exists | High if enabled too early, Medium as current gap | External supplier communication must be auditable and permission-gated | Keep disabled until email sender, recipient policy, confirmation, and audit are approved | Phase 7E5 | Email config smoke, no test-send shortcuts, Communication/Email Queue audit tests |
| PO release/send missing | Managed PO, PO Output | Purchase Manager | Deferred until workflow governance exists | High if enabled too early | PO becomes supplier commitment after approval/release | Design PO release before send; keep PDF warning | After conversion/release design | Approval/release tests, output warning tests |
| Receiving and billing are only visible | PO Follow-up, PO Analysis | Purchase User, Purchase Manager | Should remain outside Procurement execution | Deferred | Warehouse receives, Finance bills/pays | Keep read-only visibility; hand off to future Warehouse/Finance consoles | Later cross-workspace | Boundary tests forbidding receive/bill/pay actions |
| Supplier creation/disablement and portal/user creation | Supplier routes | Procurement Admin/System Manager | Should remain admin-only | Blocker if exposed | Master data and identities require admin governance | Do not expose in normal Procurement Console | Admin-only outside console | Native escape negative tests |
| Item creation/disablement/UOM/stock/accounting edits | Item routes | Procurement Admin/System Manager | Should remain admin-only | Blocker if exposed | Item master affects stock, accounting, manufacturing, selling | Do not expose in normal Procurement Console | Admin-only outside console | Item mutation negative tests |
| Item Price and Default Supplier mutation | Item/SQ/PO routes | Purchase Manager | Should remain deferred/admin-only unless separately governed | Blocker if exposed early | Price/default supplier changes affect procurement automation and valuation expectations | Keep forbidden until pricing governance exists | Later, separate design | Payload-forbidden tests and role gates |
| Supplier portal and AI quotation intake | RFQ/SQ routes | Supplier, Purchase Manager | Useful but can defer | Medium | External collaboration/intake needs identity, validation, audit | Defer until stable workflow and communication architecture | Phase 7E6 or later | Security, data validation, audit, attachment tests |
| Python workspace registry is behind JS registry/manifest for managed RFQ metadata | Workspace registry/governance | Implementation owners | Useful but can defer as metadata cleanup | Medium | Registries should agree on productized routes | Align registry metadata in a future governance cleanup, after owner approval | Later docs/runtime governance | Registry contract tests updated intentionally |
| Procurement status still says `phase_3` despite later protected phases | Registries/README | Owner/implementation agents | Useful but can defer as metadata cleanup | Low | Phase metadata should reflect protected baseline | Decide whether to rename status to protected phase marker | Later | Registry tests and docs alignment |

## Business Process Flow Findings

### Purchase Request

Current behavior supports internal purchase demand draft entry and read-only review of submitted/current Material Requests. It correctly restricts managed editing to draft Purchase Material Requests. The missing business capability is manager disposition and sourcing/order readiness. Do not implement PR-to-RFQ or PR-to-PO conversion until source document state, approval, rollback, and native mapper usage are governed.

### RFQ

Current behavior supports direct draft RFQ entry, supplier rows, requested items, supplier-specific preview/PDF, and read-only send readiness. This is safe because send is disabled and the UI states that external email is deferred. The missing business capability is a manager-owned release/readiness workflow and a controlled way to fix supplier recipient readiness.

### Supplier Quotation

Current behavior supports direct draft capture of supplier offers and read-only review/comparison. This is operationally useful for manual buying teams, but incomplete for RFQ-linked sourcing because RFQ-to-SQ conversion and supplier response intake are deferred. Quote Comparison should not gain an award button until SQ submit/award/SQ-to-PO conversion governance exists.

### Purchase Order

Current behavior supports direct draft Purchase Order entry and internal draft output. Existing submitted/current POs can be followed up through read-only receipt/billing visibility. This is safe if warnings remain prominent. The operational gap is PO release and supplier commitment governance; draft PO PDF must not be treated as a supplier-ready order.

### Reports

The four ready reports support manager review:

- Quote Comparison helps compare offers but lacks governed award/PO creation.
- Purchase Order Analysis helps monitor ordered value, receiving, and billing posture but correctly avoids execution.
- Demand-to-Order Coverage identifies demand gaps but cannot launch conversion.
- Item Purchase History helps buying context review but cannot update approved suppliers, prices, or defaults.

### Output And Send

RFQ and PO output are correctly productized and explicitly marked as draft/not sent or draft/not for supplier. RFQ recipient readiness is useful and should remain read-only until supplier-contact governance and email infrastructure are approved. No external send should be implemented as a test shortcut.

## Recommended Roadmap

### Phase 7E1: Productized Supplier Buying Profile And Contact Readiness

Business purpose: Give Purchase Managers a safe replacement for the removed Supplier native escape by supporting buying-facing supplier readiness and recipient correction.

User roles: Purchase User read-only; Purchase Manager edit controlled readiness; Procurement Admin/System Manager remains outside console for broad master setup.

Required governance: manager-only permission gate, before/after audit trail, field allowlist, no raw Supplier form, no user/portal side effects, validation for email formats and duplicate recipient ambiguity.

Data mutations allowed: only owner-approved buying-facing fields. Candidate examples include supplier buying notes/status, default RFQ recipient selection from existing contacts, supplier RFQ email readiness field if one already exists or a new controlled custom field is approved, and buyer follow-up metadata.

Data mutations forbidden: supplier creation, disablement, supplier group/tax/accounting/bank fields, Contact creation, User creation, portal activation, supplier portal invitation, email send, PO/RFQ lifecycle actions.

ERPNext DocTypes involved: Supplier, Contact read-only, Dynamic Link read-only, Request for Quotation Supplier read-only unless owner approves controlled recipient fields.

UI surfaces impacted: Supplier Detail, RFQ Review readiness, Managed RFQ readiness, Supplier Directory indicators.

Test/smoke requirements: Purchase User cannot edit; Purchase Manager can edit only allowlisted fields; forbidden payload keys rejected; no native escape labels or `Form` routes; RFQ readiness reflects updated data; audit/log entry verified.

Sales freeze/protected gate: run the protected workspace gate if runtime changes; ensure Sales smokes remain untouched and passing.

Risk if implemented too early: broad Supplier master edits, accidental supplier disablement, contact/user/portal side effects, and external communication readiness without audit.

### Phase 7E2: Productized Buying Item Procurement Context

Business purpose: Give Purchase Managers a safe replacement for removed Item native escape by maintaining buying-only item context used in sourcing decisions.

User roles: Purchase User read-only; Purchase Manager edit controlled buying context; Procurement Admin/System Manager owns broad Item master setup.

Required governance: manager-only gate, field allowlist, before/after audit, no stock/accounting/UOM mutation, no price/default supplier mutation.

Data mutations allowed: candidate controlled Item Supplier context such as approved supplier link, supplier part number, lead time, minimum order metadata, and buying notes if owner-approved.

Data mutations forbidden: Item creation/disablement, UOM, stock, valuation, accounting, item group, variants, Item Price, Default Supplier, reorder rules unless separately scoped with Inventory.

ERPNext DocTypes involved: Item read-only, Item Supplier controlled mutation candidate, Item Price read-only only.

UI surfaces impacted: Buying Item Detail, Buying Item Directory indicators, Item Purchase History.

Test/smoke requirements: role gate tests, Item Price and Default Supplier negative tests, no native escape checks, item detail smoke, report drilldown smoke.

Risk if implemented too early: corruption of shared product, inventory, valuation, and automatic buying behavior.

### Phase 7E3: Manager Review And Action Readiness For Sourcing And Ordering

Business purpose: Add manager-owned readiness/disposition without executing lifecycle mutations. This creates the operational language needed before submit, approval, conversion, or send.

User roles: Purchase User can request/prepare; Purchase Manager can mark readiness/disposition; Admin remains outside normal workflow.

Required governance: workflow vocabulary, audit, rejection/rework reasons, comments/attachments policy, no hidden submit/conversion.

Data mutations allowed: owner-approved custom review metadata or comment records only.

Data mutations forbidden: submit, approve, reject as ERP workflow action, cancel, amend, convert, send, receive, bill, pay.

ERPNext DocTypes involved: Material Request, Request for Quotation, Supplier Quotation, Purchase Order; optional comments/communication only if audited and not external email.

UI surfaces impacted: PR Review, RFQ Review, SQ Review, Managed PO, PO Follow-up, Overview counters.

Test/smoke requirements: state label tests, manager/user role tests, no lifecycle action tests, audit tests.

Risk if implemented too early: users may think a readiness marker is an ERP approval or supplier commitment.

### Phase 7E4: Conversion Workflow Design Before Implementation

Business purpose: Design governed source-to-target mappings that preserve ERPNext source references and states instead of custom-copying documents.

User roles: Purchase Manager primarily; Purchase User may prepare source documents.

Required governance: source state prerequisites, permission gates, duplicate prevention, rollback/cancel/amend policy, audit, native mapper behavior review.

Data mutations allowed: none in design phase. Later implementation may create RFQ/SQ/PO through governed native mappers only.

Data mutations forbidden: direct custom-copy conversion, conversion from drafts where ERPNext expects submitted sources, Item Price/Default Supplier side effects.

ERPNext DocTypes involved: Material Request, Request for Quotation, Supplier Quotation, Purchase Order and child tables.

UI surfaces impacted: PR Review, RFQ Review, SQ Review, Quote Comparison, Demand-to-Order Coverage, Managed PO.

Test/smoke requirements: conversion design baseline first; later mapper contract tests, duplicate guard tests, source-reference tests.

Risk if implemented too early: broken source traceability, duplicate orders, wrong supplier commitment, and bypassed approval rules.

### Phase 7E5: RFQ Governed Send Implementation After Email Infrastructure Approval

Business purpose: Enable auditable supplier RFQ communication only after sender identity, recipient governance, templates, confirmation, and audit are approved.

User roles: Purchase Manager send/release; Purchase User prepare; Admin configures email infrastructure outside the normal console.

Required governance: company-owned sender, recipient selection, confirmation, Communication/Email Queue audit, resend/amend policy, blocked portal/contact/user side effects unless separately approved.

Data mutations allowed: approved communication/audit records and send status fields only after owner approval.

Data mutations forbidden: test-send shortcuts, native RFQ send side effects, portal user creation, Contact/User creation, mass send without review.

ERPNext DocTypes involved: Request for Quotation, Communication, Email Queue, Email Account, Supplier/Contact read-only readiness inputs.

UI surfaces impacted: RFQ Review, Managed RFQ, Supplier Detail readiness.

Test/smoke requirements: email-disabled path, configured-email path, confirmation tests, audit tests, no secrets in repo/logs, no supplier portal side effects.

Risk if implemented too early: external supplier email, legal/audit exposure, leaked data, sender misconfiguration.

### Phase 7E6: AI Supplier Quotation Intake Design Later

Business purpose: Design assisted capture of supplier quotation data from attachments/emails after document lifecycle and communication foundations are stable.

User roles: Purchase User prepares; Purchase Manager reviews/accepts extracted data.

Required governance: human approval, source attachment retention, confidence flags, validation, no auto-price/default supplier mutation.

Data mutations allowed: draft Supplier Quotation creation/update only after human confirmation.

Data mutations forbidden: automatic submit, PO creation, Item Price update, Default Supplier update, supplier portal assumptions.

ERPNext DocTypes involved: Supplier Quotation, File/attachments, optional Communication if email intake is later approved.

UI surfaces impacted: Managed Supplier Quotation, SQ Review, RFQ Review.

Test/smoke requirements: validation tests, manual approval tests, no auto-submit/price/default supplier tests, attachment audit tests.

Risk if implemented too early: inaccurate supplier offer data becoming operational records without review.

## Recommended Next Implementation Phase

Recommended next implementation phase: Phase 7E1, Productized Supplier Buying Profile And Contact Readiness.

Reason: Phase 7D1 intentionally removed raw Supplier form escape. RFQ send readiness now surfaces missing or invalid supplier recipient data, but managers cannot correct that data inside the productized Procurement workspace. Supplier readiness is also less risky than document submit/conversion/send because it can be constrained to a small field allowlist, manager-only permissions, and audit logging. This phase builds the foundation needed before RFQ governed send without prematurely sending email or mutating supplier portal/users.

The second phase should be Phase 7E2, Productized Buying Item Procurement Context. It addresses the other major master-data capability removed by native escape closure, but it should remain explicitly separate because item data affects stock, valuation, pricing, UOM, and supplier automation.

## Deferred Scope And Explicit Non-goals

The following must remain deferred for this audit and should not be implemented without owner approval and a dedicated governance baseline:

- Native ERPNext form escape links for normal Procurement roles.
- RFQ send/email, test-send, Email Queue mutation, Communication mutation, SMTP/provider setup, secrets, or DNS changes.
- Submit, approval, reject, cancel, amend, stop, close, hold, resume, release, or workflow actions.
- PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, PR/MR-to-PO conversion implementation.
- Receiving, Purchase Receipt creation, warehouse execution, stock movement.
- Billing, Purchase Invoice creation, vendor payment, accounting execution.
- Item Price mutation, Default Supplier mutation, buying price automation.
- Supplier creation, supplier disablement, Contact creation, User creation, supplier portal activation.
- AI supplier quotation intake, OCR, email ingestion, automatic quote creation.
- Live alignment or protected gate execution for this docs-only audit.

## Security And Governance Considerations

- Native form escape closure should remain protected. Do not reintroduce raw `/desk/Form`, `/app`, or `frappe.set_route("Form", ...)` paths for normal Procurement roles.
- Productized master-data edits must use allowlists. Reject unknown payload keys and audit before/after values.
- Purchase User and Purchase Manager capabilities must diverge clearly. Purchase User may draft and view; manager-owned changes need explicit labels and permissions.
- State words must be precise. Draft, recorded, reviewed, ready, sent, approved, submitted, released, ordered, received, billed, and paid must not be used interchangeably.
- External communication needs confirmation and audit. A disabled send button is safer than a hidden or ambiguous send path.
- Warehouse and Finance boundaries are correct today and must remain clear when lifecycle features are added.
- Reports should not become hidden mutation launchers. Any report action that creates/updates ERP records must be declared in the manifest and gated.
- Broad master-data setup remains an ERP Admin/System Manager responsibility outside the normal Procurement Console.

## Test Strategy For Next Phase

For Phase 7E1 Supplier Buying Profile and Contact Readiness, require:

- Unit tests proving Purchase User receives read-only supplier detail and cannot submit edit payloads.
- Unit tests proving Purchase Manager can update only owner-approved supplier buying readiness fields.
- Negative tests for supplier creation, disablement, supplier group/tax/accounting/bank fields, Contact/User/portal fields, email send, RFQ submit, and native form route strings.
- RFQ readiness tests showing missing/invalid/ready recipient states update from controlled supplier readiness data.
- Manifest tests declaring all new actions as productized manager actions, not native exceptions.
- UI smoke for Supplier Detail edit flow, RFQ readiness reflection, and no native escape labels.
- `git diff --check HEAD`, `python3 -m compileall erp_workspace_ui`, and `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`.
- Protected workspace gate only if runtime or smoke scripts change. Sales freeze must remain protected.

For Phase 7E2, add Item Supplier/context tests and explicit negative tests for Item Price and Default Supplier mutation.

For Phase 7E3 and later lifecycle phases, require a design baseline before runtime work, with explicit workflow vocabulary, permissions, rollback/cancel policy, and audit record expectations.

## Owner Decisions Needed

1. Should Phase 7E1 be limited to Supplier Buying Profile and Contact Readiness, or should supplier contact creation be considered later as an admin-assisted workflow?
2. Which supplier fields are manager-owned buying context versus admin-owned master data?
3. Should RFQ recipient readiness use existing Contact records only, supplier-level email fields only, RFQ Supplier row email fields, or a new controlled custom field?
4. Should Purchase User be allowed to request supplier/item context changes, or should only Purchase Manager see edit controls?
5. Which item procurement fields are manager-owned: Item Supplier rows, supplier part number, lead time, minimum order metadata, buying notes, or other fields?
6. Should Item Price and Default Supplier remain admin-only indefinitely, or should a later pricing governance phase be planned?
7. What is the required audit artifact for manager changes: Version, Comment, custom log DocType, or another approved record?
8. What exact lifecycle words should be used before submit/send exists: `Draft`, `Recorded`, `Ready for manager review`, `Ready for send`, `Released`, or another policy vocabulary?
9. When conversions are designed, which source paths are required first: PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, or PR/MR-to-PO?
10. Who owns future PO supplier commitment: Purchase Manager, a separate approver, or a configured ERPNext workflow role?
11. Who owns email infrastructure and sender identity for eventual RFQ send?
12. Should Procurement reports eventually create manager tasks, or remain read-only until a separate task/governance system exists?
