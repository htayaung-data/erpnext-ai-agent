# Procurement Console Phase 5 Managed Buying Forms Design Plan

Date: 2026-05-13
Status: Design only, pending owner approval
Workspace: Procurement Console
Baseline: Procurement Phase 4A protected baseline at `ed72e4baf6cc79d8a5f8f2de3b5f9c9bf2e99763`

## Executive Summary

Phase 5 should replace the current Procurement native create-form exceptions with managed buying forms only after owner approval and phased validation. The goal is not to rewrite ERPNext procurement. The goal is to productize the buyer entry experience while preserving ERPNext as the transaction, validation, permission, workflow, and mapping source of truth.

Recommended direction:

- Build productized managed routes for Purchase Request, RFQ, Supplier Quotation, and Purchase Order creation and draft edit.
- Start with managed Purchase Request because it has the smallest external dependency surface.
- Implement source-document conversion as native ERPNext mapping wrappers, not custom copy logic.
- Keep current governed native forms as secondary advanced ERP access until each managed form is proven stable.
- Do not expose PO approve/reject, warehouse receipt, finance billing/payment, Item Price mutation, default supplier mutation, Supplier master edit, or Item master edit.
- Require Sales freeze protection and the protected workspace gate for any shared runtime, CSS, navigation, or managed-form shell change.

Phase 5 is not Phase 6 reporting, not Supplier/Item master governance, and not a Warehouse or Finance execution phase.

## Task 0: Baseline And Safety Check

Source state verified before design work:

| Check | Result |
| --- | --- |
| Branch | `feature/erpnext-ui-design` |
| HEAD | `ed72e4baf6cc79d8a5f8f2de3b5f9c9bf2e99763` |
| Git status | Only known untracked `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` |
| Runtime edits | None |
| Live alignment | Not performed |

Exit gate result: passed. Workspace is safe for design-only documentation.

## Task 1: Native ERPNext Buying Truth

Native truth was verified against the installed ERPNext/Frappe source and current site metadata in the backend container for site `erpai_prj1`.

Current company context:

- Company: `Mingalar Mobile Distribution Co., Ltd.`
- Buying Settings default buying price list: `Standard Buying`
- Active workflow: `Purchase Order Approval - MMOB` on Purchase Order using `workflow_state`

### DocType Truth Summary

| DocType | Native module | Submittable | Key required fields | Important status/workflow facts |
| --- | --- | --- | --- | --- |
| Material Request | Stock | Yes | `naming_series`, `material_request_type`, `company`, `transaction_date`, `items` | Purpose must be `Purchase` for Procurement managed PR. Native statuses include Draft, Submitted, Pending, Partially Ordered, Ordered, Stopped, Cancelled. |
| Material Request Item | Stock | Child | `item_code`, `schedule_date`, `qty`, `stock_uom`, `uom`, `conversion_factor` | Warehouse is optional but important for stock items. |
| Request for Quotation | Buying | Yes | `naming_series`, `company`, `transaction_date`, `status`, `suppliers`, `items`, `subject`, `message_for_supplier` | Supplier table and item table are both required. |
| RFQ Supplier | Buying | Child | `supplier` | Supplier contact/email may be used by native email/portal tools. |
| RFQ Item | Buying | Child | `item_code`, `schedule_date`, `qty`, `stock_uom`, `uom`, `conversion_factor` | Can preserve Material Request references. |
| Supplier Quotation | Buying | Yes | `naming_series`, `supplier`, `company`, `status`, `transaction_date`, `currency`, `conversion_rate`, `items` | Statuses include Draft, Submitted, Stopped, Cancelled, Expired. |
| Supplier Quotation Item | Buying | Child | `item_code`, `qty`, `stock_uom`, `uom`, `conversion_factor`, `base_rate`, `base_amount` | Rates are document-entry truth, not Item Price mutation. |
| Purchase Order | Buying | Yes | `title`, `naming_series`, `supplier`, `transaction_date`, `company`, `currency`, `conversion_rate`, `items`, `status` | Active workflow controls approval. Procurement Phase 5 must not expose approve/reject. |
| Purchase Order Item | Buying | Child | `item_code`, `item_name`, `schedule_date`, `qty`, `stock_uom`, `uom`, `conversion_factor`, `base_rate`, `base_amount` | Preserves `material_request`, `material_request_item`, and `supplier_quotation` references when mapped. |
| Supplier | Buying | No | `supplier_name`, `supplier_type` | Purchase User has read only. Supplier create/edit remains deferred. |
| Item | Stock | No | `item_code`, `item_group`, `stock_uom` | Purchase User has read only. Item create/edit remains deferred. |
| Warehouse | Stock | No | `warehouse_name`, `company` | Purchase users have read only. Receiving remains Warehouse-owned. |
| UOM | Setup | No | `uom_name` | Purchase users do not have direct UOM read in current permission check. Managed forms should default UOM from item and treat advanced UOM selection carefully. |
| Buying Settings | Buying | No | none | Purchase Manager can read/write. Purchase User read only. |

### Current Permission Facts

| Role/User family | MR | RFQ | SQ | PO | Supplier | Item | Warehouse | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Purchase Manager | read/write/create/submit/cancel | full | full | full plus workflow role effects | read/write, no create | read only | read only | Supplier create still requires Purchase Master Manager. |
| Purchase User | read/write/create/submit/cancel on MR | read/write/create, no submit/cancel | read/write/create/submit, no cancel | read/write/create/submit/cancel, workflow starts at Draft | read only | read only | read only | Managed UI must not infer workflow authority from role alone. |
| Sales Manager/User | no buying document access | no buying document access | no buying document access | no buying document access | no Supplier read | Item/Warehouse read may exist | restricted | Procurement routes should remain restricted. |
| Guest | no access | no access | no access | no access | no access | no access | no access | Restricted. |

### Active Purchase Order Workflow

Workflow: `Purchase Order Approval - MMOB`

States:

- Draft, editable by Purchase User
- Pending Purchase Approval, editable by Purchase Manager
- Pending Finance Review, editable by Finance Lead Approver
- Pending Executive Approval, editable by Executive Approver
- Approved, docstatus 1
- Rejected, editable by Purchase User

Transitions:

- Purchase User: `Submit for Approval` from Draft to Pending Purchase Approval
- Purchase Manager: `Approve`, `Escalate`, `Reject` from Pending Purchase Approval depending on total thresholds
- Finance Lead Approver: `Approve`, `Escalate`, `Reject` from Pending Finance Review
- Executive Approver: `Approve`, `Reject` from Pending Executive Approval

Phase 5 implication: managed PO forms may save drafts, but PO workflow actions must remain native or deferred until a dedicated workflow approval phase is approved. Phase 5 must not expose approve/reject.

### Native Mapping And Tool Methods To Preserve

The following installed ERPNext methods are the safe source-document truth. Phase 5 must call or wrap these methods instead of reimplementing document copying by hand.

| Flow | Native method | Notes |
| --- | --- | --- |
| Material Request to Purchase Order | `erpnext.stock.doctype.material_request.material_request.make_purchase_order` | Validates submitted Purchase/Subcontracting MR. Supports optional default supplier and child filtering. Preserves MR row references. |
| Material Request to RFQ | `erpnext.stock.doctype.material_request.material_request.make_request_for_quotation` | Validates submitted Purchase MR. Maps MR Items to RFQ Items. |
| Material Request to Supplier Quotation | `erpnext.stock.doctype.material_request.material_request.make_supplier_quotation` | Validates submitted Purchase MR. Maps MR Items to SQ Items. |
| Material Request to Purchase Order by supplier | `erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier` | Used by PO native Get Items From Open Material Requests. Depends on default supplier filtering. |
| RFQ to Supplier Quotation | `erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq` | Validates submitted RFQ. Requires supplier context for buyer-created SQ. |
| RFQ Get Items From Material Request | `erpnext.stock.doctype.material_request.material_request.make_request_for_quotation` through native `map_current_doc` | Productized UI should present source picker and call the same mapping. |
| RFQ Get Items From Possible Supplier | `erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_item_from_material_requests_based_on_supplier` | Useful but riskier because it queries possible supplier/default supplier logic. Productize after PR-to-RFQ is stable. |
| Supplier Quotation from RFQ | `erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq` | Productized supplier picker must restrict to RFQ supplier list. |
| Supplier Quotation from Material Request | `erpnext.stock.doctype.material_request.material_request.make_supplier_quotation` | Native Get Items From path. |
| Supplier Quotation to Purchase Order | `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order` | Validates submitted SQ, maps taxes and items, preserves SQ/MR references. |
| Purchase Order to Purchase Receipt | `erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt` | Warehouse execution. Forbidden in Phase 5 productized Procurement pages. |
| Purchase Order to Purchase Invoice | `erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice` | Finance execution. Forbidden in Phase 5 productized Procurement pages. |
| Supplier Quotation to Purchase Invoice | `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_invoice` | Finance execution. Forbidden. |
| Supplier Quotation to Sales Quotation | `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_quotation` | Sales-side flow. Out of Procurement Phase 5. |

Task 1 exit gate result: passed. Required native buying flows are verified. No required native behavior is unknown enough to block design. Known implementation risk: Purchase User direct UOM read permission is false, so managed forms should default UOM from Item and use native fallback for advanced UOM changes unless implementation proves a safe server-side selector.

## Task 2: Enterprise ERP Pattern Findings

Official sources reviewed:

- SAP Help Portal, Manage Purchase Requisitions - Professional: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/0df90d3c7cb848eeb4a6832e96606c32.html
- SAP Help Portal, Process Purchase Requisitions: https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/af9ef57f504840d2b81be8667206d485/59fd1db3028c49ddb837a9796cc788f3.html
- SAP Help Portal, Manage Purchase Orders: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/38cbf557c328be12e10000000a4450e5.html
- Microsoft Learn, Procurement and sourcing overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview
- Microsoft Learn, Purchase requisition overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-requisitions-overview
- Microsoft Learn, RFQ overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Microsoft Learn, Purchase order overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-order-overview
- Oracle Procurement, Create a Requisition: https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/create-a-requisition.html
- Oracle Procurement, Create Procurement Documents from Requisitions: https://docs.oracle.com/en/cloud/saas/procurement/25c/oaprc/Chunk1082072322.html
- Oracle Procurement, Considerations for Purchase Order Creation: https://docs.oracle.com/en/cloud/saas/procurement/25a/oaprc/considerations-for-purchase-order-creation.html
- Odoo Purchase RFQ documentation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
- ERPNext Material Request: https://docs.frappe.io/erpnext/user/manual/en/material-request
- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/user/manual/en/request-for-quotation
- ERPNext Supplier Quotation: https://docs.frappe.io/erpnext/supplier-quotation
- ERPNext Purchase Order: https://docs.frappe.io/erpnext/v13/user/manual/en/buying/purchase-order

Practical patterns relevant to our ERPNext Procurement Console:

| Pattern | What mature ERPs do | Fit for Procurement Phase 5 |
| --- | --- | --- |
| Guided document creation | Requisition and PO entry expose the minimum fields needed while ERP rules fill defaults. | Strong fit. Managed forms should default company, date, UOM, currency, and price list where ERPNext can derive them. |
| Source-document processing | Requisitions can become RFQs, negotiations, or POs through controlled document-builder or mapping flows. | Strong fit. Use ERPNext `get_mapped_doc` methods through productized source pickers and preview pages. |
| Line-item table as the center of the form | Serious systems make line entry, source references, quantities, UOM, dates, and supplier context explicit. | Strong fit. Managed forms need robust child-table behavior before they are accepted. |
| Draft/save/submit separation | Draft creation is separate from approval or fulfillment. | Strong fit. Phase 5 should start with Save Draft and defer workflow/approval actions. |
| Workflow visibility without unauthorized action | Workflows show status and next steps, but actions are role and status controlled. | Strong fit. PO workflow status can be visible; approve/reject stays out of productized Procurement Phase 5. |
| Native advanced tools remain available | Advanced ERP functions exist behind expert mode or native forms. | Strong fit. Keep governed native form as secondary advanced access during Phase 5. |
| Supplier portal/email as separate capability | RFQ sending and supplier responses are often distinct flows with communication controls. | Defer. Current Phase 5 should not implement supplier portal or email sending until form basics are stable. |
| Warehouse and Finance separation | Receipt and invoicing are downstream workspaces, not buyer creation forms. | Strong fit. Keep receive, bill, and pay forbidden on productized Procurement pages. |

Task 2 exit gate result: passed. Suitable patterns are guided draft entry, source-document mapping, line-focused forms, and controlled native fallback. Unsuitable patterns for this phase are broad supplier portals, full approval workbench, warehouse receipt execution, and finance invoice/payment execution.

## Task 3: Phase 5 Scope Boundary

| In Phase 5 | Deferred | Forbidden |
| --- | --- | --- |
| Managed New Purchase Request draft/create/edit | Supplier master create/edit | Warehouse receiving / Purchase Receipt creation from productized Procurement page |
| Managed New RFQ draft/create/edit | Item master create/edit | Purchase Invoice, payment, or accounting execution |
| Managed New Supplier Quotation draft/create/edit | Item Price update | PO approve/reject workflow actions |
| Managed New Purchase Order draft/create/edit | Default Supplier update | Submit/cancel/amend/close on productized pages unless owner separately approves a controlled workflow phase |
| Productized source pickers for MR/RFQ/SQ/PO conversion where ERPNext mapping methods exist | Supplier portal and RFQ email sending | Raw DB writes for buying documents |
| Save Draft through permission-aware ERPNext APIs | Full replacement of every native ERPNext advanced field | Frontend-only document mutations |
| Productized review after save | Advanced tax/accounting/payment schedule editing | Native ERPNext report/list leakage |
| Secondary governed native advanced access | Manufacturing, Stock Transfer, Sales Order, Opportunity source imports | Broad dashboard or analytics changes |

Owner approval required before including any currently deferred item. No current exclusion should be included in Phase 5 without approval.

Task 3 exit gate result: passed. No forbidden or deferred item is recommended for immediate implementation.

## Task 4: Form-By-Form Product Contracts

### Shared Managed Form Principles

All managed buying forms must:

- use backend-provided field definitions, defaults, allowed actions, state, and route targets;
- call ERPNext document APIs and DocType validation, never raw DB writes;
- save drafts only until submit/workflow behavior is separately approved;
- preserve source references when created from source documents;
- show read-only workflow/status posture where useful;
- keep native advanced form access as a secondary governed action while the managed form does not cover every advanced field;
- expose the same managed create target from both the Overview launcher and the relevant directory/worklist contextual action once that managed form is accepted.

### Purchase Request Managed Form

| Area | Contract |
| --- | --- |
| Business goal | Capture purchase demand as a Purchase Material Request with clean line entry. |
| Primary roles | Purchase User, Purchase Manager. |
| Route key | `procurement-console-purchase-request-form` |
| URL pattern | `/desk/procurement-console-purchase-request-form/new`, `/desk/procurement-console-purchase-request-form/<material-request>` |
| Modes | create draft, edit draft, read submitted summary with link to Purchase Request Review. |
| Required header fields | `material_request_type` fixed to `Purchase`, `company` defaulted, `transaction_date`, optional shared `schedule_date` if used as line default. |
| Required line fields | `item_code`, `qty`, `schedule_date`, derived `stock_uom`, `uom`, `conversion_factor`; `warehouse` optional but recommended for stock items. |
| Defaults | Company from single-company context, transaction date Today, naming series native, buying price list from Buying Settings where relevant. |
| Autocomplete | Item, Warehouse. UOM should be item-derived first because Purchase User direct UOM permission is not guaranteed. |
| Validation | At least one line, positive quantities, required date, purchasable/readable item, valid warehouse when provided, no non-Purchase material request type. |
| Allowed actions | Save Draft, Add Line, Remove unsaved line, Refresh defaults, Open ERP Form as secondary governed action after save. |
| Deferred actions | Submit, Stop, Cancel, Amend, BOM/Sales Order item import, manufacturing/transfer request types. |
| Forbidden actions | Stock transfer, issue, manufacture, receive, bill, pay, Item Price update, default supplier update. |
| After save | Stay in managed form with saved id and show `Review Request`; or route to `/desk/procurement-console-purchase-request-review/<name>` depending owner preference. |
| Return context | Back to Purchase Requests directory or Start Buying Work context. |

Implementation readiness: ready for Phase 5A if Save Draft only and UOM selection is default-derived.

### RFQ Managed Form

| Area | Contract |
| --- | --- |
| Business goal | Create a Request for Quotation for selected suppliers and requested items. |
| Primary roles | Purchase User can create/edit draft; Purchase Manager can create/edit/submit natively according to permissions. |
| Route key | `procurement-console-rfq-form` |
| URL pattern | `/desk/procurement-console-rfq-form/new`, `/desk/procurement-console-rfq-form/<rfq>` |
| Modes | create draft, edit draft, source from Material Request, read submitted review. |
| Required header fields | `company`, `transaction_date`, `subject`, `message_for_supplier`. |
| Required child tables | suppliers table with at least one `supplier`; items table with item, qty, schedule date, UOM. |
| Defaults | Subject `Request for Quotation`, message from native default, company single context, date Today. |
| Autocomplete | Supplier, Item, Warehouse. Supplier table should use existing readable suppliers only. |
| Validation | At least one supplier, at least one item, positive quantities, schedule date, supplier readable, item readable. |
| Allowed actions | Save Draft, Add Supplier, Add Item, Get Items From Purchase Request through productized source picker after Phase 5B, Open ERP Form secondary after save. |
| Deferred actions | Submit, Send Emails to Suppliers, Download PDF per supplier, supplier portal creation, Opportunity import, Possible Supplier import until after MR source picker is stable. |
| Forbidden actions | Supplier portal provisioning, supplier master create/edit, native email blast from productized page without approval. |
| After save | Productized RFQ Review or managed form saved state. |
| Return context | Back to RFQ Directory or source Purchase Request Review. |

Implementation readiness: ready for Phase 5B after Purchase Request form is stable.

### Supplier Quotation Managed Form

| Area | Contract |
| --- | --- |
| Business goal | Enter or review supplier quote details against an RFQ or purchase request without mutating master pricing. |
| Primary roles | Purchase User and Purchase Manager according to DocType permissions. |
| Route key | `procurement-console-supplier-quotation-form` |
| URL pattern | `/desk/procurement-console-supplier-quotation-form/new`, `/desk/procurement-console-supplier-quotation-form/<supplier-quotation>` |
| Modes | create draft, edit draft, create from RFQ, create from Material Request, read submitted review. |
| Required header fields | `supplier`, `company`, `transaction_date`, `currency`, `conversion_rate`. |
| Optional header fields | `valid_till`, `buying_price_list`, terms. |
| Required line fields | `item_code`, `qty`, `uom`, `conversion_factor`, `rate`; base rate/amount calculated by ERPNext. |
| Defaults | Company single context, date Today, currency from supplier/company, buying price list from supplier or Buying Settings if native method supplies it. |
| Autocomplete | Supplier, Item, Warehouse. RFQ source supplier picker must be constrained to RFQ supplier list. |
| Validation | At least one item, positive qty, valid supplier, valid rate where required, no Item Price update. |
| Allowed actions | Save Draft, Add Item, Get Items From RFQ through native mapping wrapper, Get Items From Purchase Request after source-picker support, Open ERP Form secondary after save. |
| Deferred actions | Submit, Update Items on submitted SQ, link Material Requests tool, supplier portal submission. |
| Forbidden actions | Item Price update, default supplier update, PO creation until Phase 5D, Purchase Invoice creation. |
| After save | Productized Supplier Quotation Review or managed form saved state. |
| Return context | Back to Supplier Quotation Directory, RFQ Review, or Quote Comparison. |

Implementation readiness: ready for Phase 5C after RFQ source workflow is stable.

### Purchase Order Managed Form

| Area | Contract |
| --- | --- |
| Business goal | Create a purchase order draft from manual entry or safe source conversion while preserving PO workflow truth. |
| Primary roles | Purchase User can create/edit Draft by native permissions; Purchase Manager can create/edit and has workflow authority in certain states, but approve/reject remains out of Phase 5 productized UI. |
| Route key | `procurement-console-purchase-order-form` |
| URL pattern | `/desk/procurement-console-purchase-order-form/new`, `/desk/procurement-console-purchase-order-form/<purchase-order>` |
| Modes | create draft, edit draft, create from Material Request, create from Supplier Quotation, read/route submitted PO to PO Follow-up Detail. |
| Required header fields | `supplier`, `company`, `transaction_date`, `currency`, `conversion_rate`. |
| Required line fields | `item_code`, `item_name`, `schedule_date`, `qty`, `uom`, `conversion_factor`, `rate`; base fields calculated by ERPNext. |
| Defaults | Company single context, date Today, title from supplier name, currency/conversion from supplier/company, price list from Buying Settings if available. |
| Autocomplete | Supplier, Item, Warehouse, Material Request source, Supplier Quotation source. |
| Validation | Supplier required, at least one item, positive qty, schedule date, rate when required, no submit/approval leakage. |
| Allowed actions | Save Draft, Add Item, Get Items From Purchase Request, Get Items From Supplier Quotation, Open ERP Form secondary after save. |
| Deferred actions | Submit for Approval, Approve, Reject, Escalate, Cancel, Amend, Close, Unclose, Update Rate as per Last Purchase as a direct mutation. |
| Forbidden actions | Receive, Bill, Pay, Purchase Receipt, Purchase Invoice, stock execution, finance execution. |
| After save | Stay in managed form or route to PO Follow-up Detail if submitted; for drafts, managed form remains canonical. |
| Return context | Back to Purchase Orders directory, Demand-to-Order Coverage, Supplier Quotation Review, or source review. |

Implementation readiness: not first. Implement in Phase 5D after PR/RFQ/SQ managed forms and conversion previews are proven.

Task 4 exit gate result: passed. Each form has a complete implementation contract. Submit/workflow actions are intentionally not marked implementation-ready until owner approval.

## Task 5: Source-Document Conversion Design

### Conversion Matrix

| Source | Target | Native method | UX treatment | Required permissions | Risk | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| Material Request | RFQ | `material_request.make_request_for_quotation` | Productized source picker with row preview, then managed RFQ draft | MR read, RFQ create/write | Low/medium | Productize in Phase 5B. |
| Material Request | Purchase Order | `material_request.make_purchase_order` | Productized source picker with child selection and optional default supplier prompt, then managed PO draft | MR read, PO create/write, Supplier read | Medium/high because supplier grouping matters | Productize in Phase 5D only after PO form exists. |
| Material Request | Purchase Order by default supplier | `material_request.make_purchase_order_based_on_supplier` | Possible governed native bridge first; productize only if default supplier behavior is validated | MR read, PO create/write, Supplier read | Medium/high due default supplier logic | Defer or bridge. |
| Material Request | Supplier Quotation | `material_request.make_supplier_quotation` | Productized source picker after SQ form exists | MR read, SQ create/write | Medium | Productize in Phase 5C optional. |
| RFQ | Supplier Quotation | `request_for_quotation.make_supplier_quotation_from_rfq` | Productized RFQ Review action: select supplier from RFQ suppliers, preview lines, create SQ draft | RFQ read, SQ create/write, Supplier read | Low/medium | Productize in Phase 5C. |
| Supplier Quotation | Purchase Order | `supplier_quotation.make_purchase_order` | Productized Supplier Quotation Review action: preview selected lines, create PO draft | SQ read, PO create/write | Medium | Productize in Phase 5D. |
| RFQ | Supplier portal quote | `request_for_quotation.create_supplier_quotation` | Native/supplier portal only | Portal/user setup | High | Defer. |
| Purchase Order | Purchase Receipt | `purchase_order.make_purchase_receipt` | Not in Procurement managed forms | Warehouse permissions | High and out of ownership | Forbidden. |
| Purchase Order | Purchase Invoice | `purchase_order.make_purchase_invoice` | Not in Procurement managed forms | Finance permissions | High and out of ownership | Forbidden. |
| Supplier Quotation | Purchase Invoice | `supplier_quotation.make_purchase_invoice` | Not in Procurement managed forms | Finance permissions | High and out of ownership | Forbidden. |

Conversion rules:

- All conversions must call native ERPNext mapping methods or use saved mapped document output from those methods.
- Productized UI may filter/select source rows before mapping only through arguments supported by native mapping methods.
- Productized UI must not manually copy child rows into a different DocType as its primary conversion mechanism.
- Conversion previews should show source id, item, requested qty, remaining/open qty when available, UOM, warehouse, required date, supplier, and references.
- After conversion, save as Draft only unless user confirms Save Draft and owner later approves submit behavior.

Task 5 exit gate result: passed. No conversion is approved if it bypasses ERPNext mapping or validation.

## Task 6: Backend/API Design

Recommended new backend module:

- `erp_workspace_ui/procurement_console/managed_forms.py`

Recommended existing-module integration:

- `procurement_console/common.py` for role, state, and route helpers.
- `workspace_governance_manifest.py` for route/action classification.
- `workspace_registry.py` for route family declarations.
- Existing review/report modules for productized return targets.

### API Contracts

#### `get_managed_buying_form_context(form_key, name=None, source=None, mode=None)`

Purpose: return page payload, field contract, defaults, allowed actions, route targets, and state for a managed buying form.

Request:

```json
{
  "form_key": "purchase_request|rfq|supplier_quotation|purchase_order",
  "name": "optional existing document name",
  "source": {"doctype": "Material Request", "name": "MAT-MR-2026-00007"},
  "mode": "create|edit|review"
}
```

Response:

```json
{
  "state": {"kind": "ready|restricted|unavailable|error", "message": "..."},
  "page": {"title": "New Purchase Request", "kicker": "Buying request"},
  "doctype": "Material Request",
  "document": {"name": null, "docstatus": 0, "workflow_state": null},
  "fields": [],
  "line_table": {"columns": [], "rows": []},
  "actions": [],
  "action_targets": {},
  "return_target": {}
}
```

Permission rule: require Procurement role and the relevant DocType read/create/write permission for the requested mode.

#### `save_managed_buying_draft(form_key, payload)`

Purpose: insert or save a draft buying document using ERPNext document APIs.

Request:

```json
{
  "form_key": "purchase_request|rfq|supplier_quotation|purchase_order",
  "name": "optional draft document name",
  "header": {},
  "items": [],
  "suppliers": [],
  "source_context": {}
}
```

Response:

```json
{
  "state": {"kind": "ready", "message": "Draft saved"},
  "name": "PUR-RFQ-2026-00007",
  "docstatus": 0,
  "route": "/desk/procurement-console-rfq-form/PUR-RFQ-2026-00007",
  "review_route": "/desk/procurement-console-rfq-review/PUR-RFQ-2026-00007"
}
```

Rules:

- Call `frappe.get_doc`, `doc.insert`, and `doc.save` with standard ERPNext validation.
- Call `doc.check_permission("create")` or `doc.check_permission("write")` before mutation.
- Maintain a strict header and child-row field allowlist per DocType.
- Never write submitted documents through this endpoint.
- Roll back on exception and return `error` without losing the submitted client payload.

#### `get_source_document_candidates(target_form_key, source_doctype, filters)`

Purpose: return permission-safe source documents for `Get Items From` panels.

Rules:

- Use `frappe.get_list` or native query helpers with permissions.
- Only return records valid for the target mapping: submitted Purchase MRs, submitted RFQs, submitted SQs as applicable.
- Exclude stopped/cancelled/expired where native mapping would reject them.

#### `map_source_to_managed_draft(target_form_key, source, options)`

Purpose: call native ERPNext mapping and reshape mapped output into managed form draft payload.

Rules:

- Call verified native methods only.
- Do not save automatically unless user confirms Save Draft.
- Preserve source child references.
- If mapping fails, return `unavailable` or `error` based on cause.

#### `search_managed_buying_link(doctype, txt, filters)`

Purpose: provide autocomplete for managed forms with permission-aware filters.

Rules:

- Allow only approved link doctypes: Item, Supplier, Warehouse, Material Request, RFQ, SQ, PO as needed.
- Enforce DocType read permission.
- Apply business filters server-side, for example purchasable items and submitted source documents.

### Error And State Mapping

| State | Meaning |
| --- | --- |
| `ready` | Form context or save response is valid. |
| `empty` | Valid request but no source candidates or no line rows. |
| `restricted` | User lacks Procurement role or ERPNext DocType permission. |
| `unavailable` | Required native method, field, or mapping prerequisite is missing. |
| `error` | Technical exception or validation failure that should be surfaced safely. |

Task 6 exit gate result: passed. Every mutation method is permission checked, DocType validated, and rollback safe by design.

## Task 7: Frontend Runtime And Shared Component Design

### Component Map

| UI need | Existing shared component/shell | Phase 5 usage |
| --- | --- | --- |
| Managed create/edit shell | Sales managed child-page form pattern, generalized only if needed | Use as reference; do not edit Sales-specific code. Extract shared component only with Sales freeze gate. |
| Header | Shared compact detail/child header | Title, status chips, draft/submitted/workflow posture. |
| Toolbar | Shared compact toolbar/action buttons | Save Draft, Refresh, Back, Review, Open ERP Form secondary. |
| Form sections | Shared panel/card discipline | Header details, supplier/request context, items, totals. |
| Link autocomplete | Shared link autocomplete runtime | Item, Supplier, Warehouse, source docs. |
| Child table | Shared row table/list behavior | Editable line rows with stable widths and no mid-token wrapping. |
| Guard states | Shared ready/empty/restricted/unavailable/error states | Permission and mapping failures. |
| Source picker | New shared managed-source-picker may be needed | If created, it must be root shared component and Sales freeze gate mandatory. |
| Draft dirty-state guard | New shared managed-form utility may be needed | Warn on route away with unsaved changes. Sales impact must be assessed. |

Design rules:

- Do not create Procurement-only visual button variants.
- Do not reuse report/list shells for editable document forms.
- Prefer a generic `managed_document_form_shell` rather than a page-local ad hoc layout.
- If implementation extracts shared code from Sales managed forms, Sales freeze protection and protected workspace gate are mandatory.

Task 7 exit gate result: passed. New shared runtime/CSS is possible but not required for the first design; any shared extraction is explicitly protected.

## Task 8: Navigation And Native Leakage Policy

### Contextual Create Action Contract

Phase 5 creation must not be limited to the Procurement Overview launcher. Enterprise buying workspaces need both global and contextual entry points, with one route contract per document type.

1. Global launcher rule: Start Buying Work on the Procurement Overview remains the global entry point for common buying creation actions.
2. Contextual directory action rule: each relevant directory/worklist must expose its own create action when the user has the corresponding ERPNext create/write permission:
   - Purchase Requests page: `New Purchase Request`
   - RFQs page: `New RFQ`
   - Supplier Quotations page: `New Supplier Quotation`
   - Purchase Orders page: `New Purchase Order`
3. Same-route rule: contextual create actions must route to the same managed Phase 5 form routes as the Overview action cards. Do not create duplicate native routes, parallel managed flows, or page-specific one-off create paths.
4. Permission rule: create actions must be hidden or rendered disabled when the current user lacks the corresponding ERPNext DocType create/write permission. Procurement role family alone is not sufficient.
5. Conversion action rule: source-driven queues may later expose contextual conversion actions only after the matching conversion mini-phase is implemented and validated:
   - Purchase Request to RFQ: Phase 5B
   - RFQ to Supplier Quotation: Phase 5C
   - Supplier Quotation to Purchase Order: Phase 5D
   - Purchase Request to Purchase Order: Phase 5D or later because supplier grouping and default supplier logic are riskier
6. Deferred native fallback rule: until a managed form replaces a native create route, current native create forms remain governed fallback exceptions. After each managed form is accepted, update Overview and directory/worklist actions together so global and contextual creation do not diverge.

### Route/Action Leakage Matrix

| Current or future entry | Current classification | Phase 5 target classification | Decision |
| --- | --- | --- | --- |
| Start Buying Work: New Purchase Request | governed native exception | productized managed route | Replace in 5A after managed PR passes. Keep native as secondary Advanced ERP Form. |
| Start Buying Work: New RFQ | governed native exception | productized managed route | Replace in 5B. |
| Start Buying Work: New Supplier Quotation | governed native exception | productized managed route | Replace in 5C. |
| Start Buying Work: New Purchase Order | governed native exception | productized managed route | Replace in 5D. |
| Purchase Request Review row/action | productized review | productized managed edit for draft, review for submitted | Keep productized primary. |
| RFQ Review row/action | productized review | productized managed edit for draft, review for submitted | Keep productized primary. |
| Supplier Quotation Review row/action | productized review | productized managed edit for draft, review for submitted | Keep productized primary. |
| Secondary `Open ERP Form` on PR/RFQ/SQ review | governed native secondary | governed native secondary | Keep until managed forms cover advanced fields; must remain secondary. |
| Supplier Detail `Open ERP Supplier Form` | governed native secondary | governed native secondary | Keep as-is; Supplier create/edit deferred. |
| Item Detail `Open ERP Item Form` if present | governed native secondary | governed native secondary | Keep as-is; Item create/edit deferred. |
| Reports drilldowns | productized navigation | productized navigation | No change. |
| Worklist row actions | productized review/detail | productized review/detail or managed draft edit where appropriate | No native primary row action. |
| PR to RFQ conversion | currently native inside ERP form | productized source conversion route | Implement in 5B using native mapping. |
| RFQ to SQ conversion | currently native inside ERP form | productized source conversion route | Implement in 5C using native mapping. |
| SQ to PO conversion | currently native inside ERP form | productized source conversion route | Implement in 5D using native mapping. |
| PO to Receipt/Invoice | native ERP downstream | forbidden productized Procurement leakage | Do not expose. |

No raw ERPNext default route remains unclassified.

Task 8 exit gate result: passed.

## Task 9: Security, Permission, And Workflow Design

| Role family | View productized Procurement | Save PR draft | Save RFQ draft | Save SQ draft | Save PO draft | Submit/workflow | Native fallback |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Purchase User | Yes, if ERPNext DocType read permits | Yes if MR create/write permits | Yes if RFQ create/write permits | Yes if SQ create/write permits | Yes if PO create/write permits | Deferred in productized UI. Native ERP may show allowed actions. | Allowed only for governed forms and secondary actions. |
| Purchase Manager | Yes | Yes | Yes | Yes | Yes | Deferred in productized UI. Native workflow approval not exposed in Phase 5. | Allowed where current policy permits. |
| Purchase Master Manager | Only if also has Procurement/DocType permission | Not by role alone | Not by role alone | Not by role alone | Not by role alone | Not by role alone | Supplier master permissions remain outside Phase 5. |
| Finance Lead Approver | Restricted unless also has Procurement/DocType permission | No by default | No by default | No by default | No by default | PO approval native/future approval workspace only, not Phase 5 | Native only if ERPNext grants. |
| Executive Approver | Restricted unless also has Procurement/DocType permission | No by default | No by default | No by default | No by default | PO approval native/future approval workspace only, not Phase 5 | Native only if ERPNext grants. |
| Sales-only users | Restricted | No | No | No | No | No | No Procurement native fallback. |
| Guest | Restricted | No | No | No | No | No | No. |

Security rules:

- Role family is not enough. Every managed operation must also call ERPNext DocType and record permission checks.
- Child-row references must be validated against readable source documents and current user permissions.
- Productized forms must not save submitted documents.
- Productized forms must not expose hidden workflow transitions.
- Any native fallback must carry Procurement chrome and remain governed by `native-exception-policy-v1`.

Potential permission conflict: Purchase users do not have direct UOM read in current checks. Design response: do not require arbitrary UOM browsing in first managed forms. Default UOM from Item and native ERPNext item triggers; expose UOM override only after implementation proves a permission-safe selector or owner accepts native fallback for advanced UOM.

Task 9 exit gate result: passed. No desired UX currently conflicts with ERPNext permissions because risky controls are deferred or moved to governed native fallback.

## Task 10: Test And Smoke Plan

### Mandatory Source Checks

```bash
python3 -m compileall erp_workspace_ui
PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
node --check <touched-js-files>
git diff --check HEAD
```

### Mandatory Browser/Protection Gates

```bash
./run_playwright_docker.sh npm run test:procurement-phase3
npm --prefix ui_smoke run test:sales-freeze-protection
npm --prefix ui_smoke run test:protected-workspaces
```

Use role-specific Procurement smoke for:

- Purchase Manager: `purchase.manager@meet.com`
- Purchase User: `purchase.ygn.01@meet.com`

Sales freeze protection is mandatory if implementation touches shared runtime, shared CSS, registry, list shell, report shell, child/detail shell, boot, navigation, managed form shell, or native exception policy.

### Contract Tests To Add During Implementation

| Area | Required coverage |
| --- | --- |
| Route ownership | New managed form routes belong to Procurement and do not steal Sales routes. |
| Governance manifest | Managed routes classified as productized managed forms; native fallback remains secondary. |
| State kinds | ready, empty, restricted, unavailable, error for each form and source picker. |
| Permissions | Purchase Manager/User allowed only when ERPNext permission allows; Sales-only and Guest restricted. |
| Field allowlists | Header and child fields saved only from approved allowlists. |
| Save draft | Insert/save draft calls ERPNext validations and preserves source references. |
| Submitted safety | Productized save rejects submitted documents. |
| Source mapping | MR-to-RFQ, RFQ-to-SQ, SQ-to-PO, MR-to-PO wrappers call native mapping methods. |
| Forbidden actions | No receive, bill, pay, approve, reject, cancel, amend, close, Item Price update, default supplier update on productized pages. |
| Native fallback | Secondary only, permission gated, declared in manifest. |
| Link autocomplete | Item, Supplier, Warehouse, source document queries are permission aware. |
| Dirty state | Unsaved draft navigation guard works without shell stacking. |
| Sales protection | Sales freeze gate passes when shared form shell changes. |

### Contextual Create Test Requirements

Phase 5 implementation tests and smoke must prove:

- Overview and each relevant directory page expose the same managed create target for the same document type.
- Permission-denied users do not see unauthorized create actions, or see them disabled with a restricted state that does not navigate.
- Create buttons do not navigate to raw ERPNext native forms after the managed replacement for that document type is accepted.
- Overview and directory/worklist targets are updated in the same mini-phase, so global and contextual creation cannot diverge.
- Protected workspace gate and Sales freeze protection remain mandatory if shared action/list/runtime behavior is touched.

### Browser Smoke Checklist

For each mini-phase:

- open managed route directly;
- open from Start Buying Work;
- create draft with one valid line;
- validate missing required fields;
- test autocomplete suggestions;
- save draft;
- refresh saved route;
- back/forward navigation;
- open productized review after save;
- open secondary native form only if allowed;
- verify no duplicate header, no page stacking, no stale shell;
- verify no forbidden mutation labels;
- run restricted user smoke where credentials exist;
- capture screenshots at `1240x768` and `1440x900` for premium layout.

Task 10 exit gate result: passed. Validation checklist and commands are defined.

## Task 11: Risk Assessment And Implementation Roadmap

### Phase 5A: Managed Purchase Request Form

| Item | Plan |
| --- | --- |
| Business value | Replaces the simplest native create exception with a premium buyer demand entry flow. |
| Likely files | new managed form backend module, new page route JS/JSON/Python, governance manifest, registry, smoke/tests, docs. |
| Risks | Item/UOM/warehouse defaults, required schedule dates, accidental non-Purchase MR types. |
| Required tests | MR draft save, field allowlist, required lines, permissions, no non-Purchase type, no stock/manufacturing actions. |
| Live alignment | Sync only new Procurement managed form files and manifest/registry after commit. |
| Rollback | Restore Start Buying Work target to governed native Material Request route. |
| Exit gate | Purchase Manager/User can create and review PR draft; Sales freeze passes if shared files touched. |

### Phase 5B: Managed RFQ Form And PR-to-RFQ Conversion

| Item | Plan |
| --- | --- |
| Business value | Buyers can turn submitted purchase demand into RFQs without raw native form dependency. |
| Likely files | RFQ managed form backend/frontend, source picker, mapping wrapper, tests/smoke. |
| Risks | Supplier table behavior, RFQ message defaults, email/supplier portal scope creep. |
| Required tests | RFQ draft save, supplier/item child tables, MR source mapping, restricted access. |
| Live alignment | Sync RFQ route and backend only after source gates. |
| Rollback | Keep native RFQ Start Buying Work and review secondary native action. |
| Exit gate | PR-to-RFQ draft creation preserves MR references and no email/portal action leaks. |

### Phase 5C: Managed Supplier Quotation Form And RFQ-to-SQ Context

| Item | Plan |
| --- | --- |
| Business value | Buyers can enter supplier quote drafts from RFQs and compare later in existing Quote Comparison. |
| Likely files | SQ managed form backend/frontend, RFQ supplier picker, mapping wrapper, tests/smoke. |
| Risks | Currency/conversion rate, rate/base amount calculations, supplier constraints, supplier portal confusion. |
| Required tests | SQ draft save, RFQ-to-SQ mapping, rate validation, no Item Price/default supplier mutation. |
| Live alignment | Sync after source gates. |
| Rollback | Keep native SQ Start Buying Work and review secondary native action. |
| Exit gate | SQ draft from RFQ works for allowed users and remains read-only to master data. |

### Phase 5D: Managed Purchase Order Form And Safe Source Conversions

| Item | Plan |
| --- | --- |
| Business value | Buyers can prepare PO drafts from PR or SQ without raw native form as primary path. |
| Likely files | PO managed form backend/frontend, MR/SQ source picker, mapping wrapper, PO draft tests/smoke. |
| Risks | Active PO workflow, supplier/currency/tax defaults, child selection, partial quantities, schedule dates, rate suggestions. |
| Required tests | PO draft save, MR-to-PO mapping, SQ-to-PO mapping, workflow status visibility, no approve/reject/receive/bill/pay. |
| Live alignment | Sync carefully. Restart only if stale Python imports require it. |
| Rollback | Keep native PO Start Buying Work and PO Follow-up read-only detail. |
| Exit gate | PO draft creation works and workflow actions remain native/deferred. |

### Phase 5E: Native Exception Cleanup And Freeze Candidate

| Item | Plan |
| --- | --- |
| Business value | Moves Start Buying Work primary actions to managed forms and leaves native access as secondary advanced path. |
| Likely files | service action targets, governance manifest, native exception docs, smoke/tests. |
| Risks | Removing native too early, advanced tools still needed, owner acceptance. |
| Required tests | Start Buying Work routes, native fallback secondary, no primary native leakage, protected workspace gate. |
| Live alignment | Only after full owner review. |
| Rollback | Restore Start Buying Work native targets. |
| Exit gate | Owner manually accepts managed forms and native exception policy update. |

Task 11 exit gate result: passed. Roadmap starts with the least risky form and does not start with PO conversion.

## Open Questions Requiring Owner Approval

1. Should Phase 5A expose `Submit` for Purchase Request, or should productized forms remain Save Draft only with native fallback for submit during Phase 5?
2. Should Purchase User be allowed to change UOM in managed forms, or should UOM be derived from Item and advanced UOM edits remain native until a permission-safe selector is implemented?
3. Should RFQ email sending and supplier portal access remain fully deferred, or should a later Phase 5 subtask design a governed send flow?
4. Should PO `Submit for Approval` be productized in Phase 5D, or deferred to a separate Procurement Workflow Actions phase?
5. Should PR-to-PO be implemented as a fully productized source picker in Phase 5D, or first as a governed native bridge because of supplier grouping/default supplier complexity?
6. Should managed forms route to productized review pages after save by default, or remain on the saved managed draft form?

## Final Design Decisions

- Phase 5 should proceed only after owner approval of this plan.
- No runtime implementation should start from this document alone.
- ERPNext native document methods remain the source of truth for mapping and validation.
- Current native create forms remain governed exceptions until each managed replacement passes source validation, smoke, protected workspace gate, and manual owner review.
- No Sales Console runtime/UI change is approved by this design.
- No Phase 5 managed form should bypass ERPNext permissions, workflows, or DocType validation.
