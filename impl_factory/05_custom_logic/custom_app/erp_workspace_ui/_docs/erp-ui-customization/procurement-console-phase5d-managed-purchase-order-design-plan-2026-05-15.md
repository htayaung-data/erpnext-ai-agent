# Procurement Console Phase 5D Managed Purchase Order Design Plan

Date: 2026-05-15

Baseline dependency: `16a46c5e611b17e29ef728eeb3cd6d5c9e563209`

Baseline documents:

- `_docs/erp-ui-customization/procurement-console-phase5a-5b-managed-buying-baseline-2026-05-15.md`
- `_docs/erp-ui-customization/procurement-console-phase5c-managed-supplier-quotation-baseline-2026-05-15.md`

## Executive Recommendation

Recommended Phase 5D scope: implement a managed Purchase Order form for direct draft Purchase Order entry only.

Phase 5D should finish the managed buying form family without introducing commitment, receiving, billing, payment, approval, or conversion workflows. The managed form should replace productized `New Purchase Order` create actions with a draft-only Procurement Console form that uses ERPNext Purchase Order document APIs and native validation.

Do not implement Supplier Quotation-to-Purchase Order conversion, Material Request-to-Purchase Order conversion, submit, approval, receiving, billing, payment, Item Price mutation, or Default Supplier mutation in Phase 5D. ERPNext's native conversion and downstream operational actions are submit-sensitive and materially higher risk than draft entry. They should become separate governed phases after the four managed buying forms are protected.

## Baseline Understanding

Phase 5A, 5B, and 5C are protected baseline behavior:

- Managed Purchase Request route: `/desk/procurement-console-purchase-request-form/new`
- Managed RFQ route: `/desk/procurement-console-rfq-form/new`
- Managed Supplier Quotation route: `/desk/procurement-console-supplier-quotation-form/new`
- Overview and directory create actions route to the same managed form for each accepted document type.
- Productized create actions must not leak to raw ERPNext native create pages after the managed replacement is accepted.
- Save actions are draft-only: `Save Request`, `Save RFQ`, and `Save Quotation`.
- `Open ERP Form` is allowed only after save and only as a secondary governed native exception.
- The accepted managed form shell uses compact headers, shared action styling, attached autocomplete overlays, clean UOM metadata, no duplicate chrome, no random gradients, and no stacked page shells.
- The accepted date contract uses `Default Required By`, `Line Required By`, inherited/manual line-date state, and helper copy: `New item lines use the default date unless changed.`
- Item line behavior uses shared headers at desktop widths, responsive row treatment at laptop widths, and no repeated per-row labels where the shared header is active.
- Any shared runtime, shared CSS, managed-form shell, action registry, or navigation change that can affect protected baselines must pass Sales freeze and the protected workspace gate.

Phase 5D implementation must preserve all accepted Phase 5A/5B/5C routes, wording, action hierarchy, autocomplete behavior, date behavior, UOM behavior, and shell lifecycle behavior.

## Native ERPNext Purchase Order Findings

Installed ERPNext source and current site metadata were inspected from the backend container. Key source files:

- `apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.py`
- `apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.js`
- `apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.json`
- `apps/erpnext/erpnext/buying/doctype/purchase_order_item/purchase_order_item.py`
- `apps/erpnext/erpnext/buying/doctype/purchase_order_item/purchase_order_item.json`
- `apps/erpnext/erpnext/buying/doctype/supplier_quotation/supplier_quotation.py`
- `apps/erpnext/erpnext/stock/doctype/material_request/material_request.py`

### Purchase Order DocType

`Purchase Order` is submittable and uses naming series `PUR-ORD-.YYYY.-` through `autoname: naming_series:`.

Important Purchase Order header fields verified from installed DocType JSON:

| Field | Type | Required | Phase 5D treatment |
| --- | --- | --- | --- |
| `naming_series` | Select | yes | Backend default/native value; not prominent in UI. |
| `supplier` | Link Supplier | yes | Main user field with autocomplete. |
| `supplier_name` | Data | no, read-only | Backend/display metadata only if useful. |
| `company` | Link Company | yes | Backend context. Do not show as a large field in single-company UI. |
| `transaction_date` | Date | yes, default Today | Visible as transaction date. |
| `schedule_date` | Date | no, label `Required By` | UI label should be `Default Required By`; used to seed item dates. |
| `currency` | Link Currency | yes | Visible as compact context or editable only if needed; default from company/supplier/native ERPNext. |
| `conversion_rate` | Float | yes | Backend-owned; do not make primary UI unless multi-currency demands it. |
| `buying_price_list` | Link Price List | no | Use default buying price list; optional advanced field only if implementation needs it. |
| `set_warehouse` | Link Warehouse | no | Optional header-level receiving location; may be used as a default for line warehouses. |
| `items` | Table Purchase Order Item | yes | Managed item lines. |
| `taxes_and_charges` | Link Purchase Taxes and Charges Template | no | Deferred from primary Phase 5D UI; ERPNext defaults may apply. |
| `taxes` | Table Purchase Taxes and Charges | no | Deferred from primary Phase 5D UI; optional read-only totals only if safe. |
| `status` | Select | yes, default Draft, read-only | Backend/native state; productized UI should say `New Purchase Order` or `Purchase Order Recorded`, not expose commit/submit language. |
| `grand_total` | Currency | read-only | Saved/summary display. |
| `base_grand_total` | Currency | read-only | Backend/native total. |

Current site metadata may include optional `workflow_state`; it is not required for draft save and must not drive Phase 5D UI permissions by itself.

### Purchase Order Item DocType

Important Purchase Order Item fields verified from installed DocType JSON:

| Field | Type | Required | Phase 5D treatment |
| --- | --- | --- | --- |
| `item_code` | Link Item | yes | Main line field with item autocomplete. |
| `item_name` | Data | yes | Derived/read-only from ERPNext item details. |
| `schedule_date` | Date | yes | UI label `Line Required By`; required per item. |
| `qty` | Float | yes | User field. |
| `stock_uom` | Link UOM | yes, read-only | Derived. |
| `uom` | Link UOM | yes | Derived/default; display as read-only UOM metadata for Phase 5D unless approved otherwise. |
| `conversion_factor` | Float | yes | Backend-derived. |
| `rate` | Currency | no in JSON but required for useful PO lines | User field; backend validates for Phase 5D. |
| `amount` | Currency | read-only | Derived from qty/rate for display and native totals. |
| `base_rate` | Currency | yes, read-only | Backend/native calculation. |
| `base_amount` | Currency | yes, read-only | Backend/native calculation. |
| `warehouse` | Link Warehouse | no | Optional line target warehouse with autocomplete. |
| `material_request` | Link Material Request | read-only | Conversion reference; not manually edited in Phase 5D. |
| `supplier_quotation` | Link Supplier Quotation | read-only | Conversion reference; not manually edited in Phase 5D. |
| `received_qty` | Float | read-only | Post-submit/receiving state; not editable. |
| `billed_amt` | Currency | read-only | Billing state; not editable. |

### Native Validation And Status Behavior

`PurchaseOrder.validate()` calls ERPNext buying controller validation, status setting, supplier validation, schedule date validation, item validation, UOM integer validation, previous-document validation, subcontracting validation, minimum order quantity validation, blanket-order validation, budget/inter-company checks, and default field resets.

`PurchaseOrder.on_submit()` updates previous document status, requested/ordered quantities, budgets, subcontracting reserves, blanket orders, inter-company links, and may auto-create subcontracting orders. Therefore submit is operationally meaningful and must remain out of Phase 5D.

Native status options include `Draft`, `On Hold`, `To Receive and Bill`, `To Bill`, `To Receive`, `Completed`, `Cancelled`, `Closed`, and `Delivered`. Phase 5D should save only draft Purchase Orders.

### Permissions

Current site permission checks on 2026-05-15:

| User | Purchase Order read/write/create/submit/cancel/amend |
| --- | --- |
| `purchase.manager@meet.com` | allowed |
| `purchase.ygn.01@meet.com` | allowed |
| `sale.manager@meet.com` | denied |
| `sale.user@meet.com` | denied |
| Guest | denied |

Implementation must still call ERPNext/Frappe permission checks for read, create, and write. Procurement role family alone is not sufficient.

### Company, Currency, And Buying Defaults

Current site data:

- Company: `Mingalar Mobile Distribution Co., Ltd.`
- Company default currency: `MMK`
- Buying Settings buying price list: `Standard Buying`
- Buying Settings `maintain_same_rate`: enabled

Phase 5D backend should resolve company and currency independently. Currency must come from `Company.default_currency`, supplier/default party details, or ERPNext system defaults, not from company name.

### Native Conversion Methods

ERPNext native mappings verified:

- Supplier Quotation to Purchase Order:
  - Method: `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order`
  - Validation: source `Supplier Quotation.docstatus = 1`
  - Maps Supplier Quotation Items to Purchase Order Items and preserves source references.
- Material Request to Purchase Order:
  - Method: `erpnext.stock.doctype.material_request.material_request.make_purchase_order`
  - Validation: source `Material Request.docstatus = 1` and `material_request_type in [Purchase, Subcontracting]`
  - Maps eligible Material Request Items to Purchase Order Items.
- Material Request to Purchase Order by supplier/default supplier:
  - Method: `erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier`
  - Uses default-supplier grouping logic and should not be recreated manually.

Implication: Phase 5D must not implement SQ-to-PO or MR-to-PO conversion by custom row copy. Native mapping requires submitted upstream documents and contains traceability/default-supplier behavior that should be productized separately.

### Native Actions To Exclude From Phase 5D

Native Purchase Order JS exposes or supports:

- `Get Items From > Material Request`
- `Get Items From > Supplier Quotation`
- `Tools > Update Rate as per Last Purchase`
- `Tools > Link to Material Request`
- Submit-driven actions: `Update Items`, `Hold`, `Resume`, `Close`, `Re-open`, `Delivered`
- Downstream creation: `Purchase Receipt`, `Purchase Invoice`, `Payment`, `Payment Request`, `Subcontracting Order`, `Material to Supplier`, inter-company order
- List view bulk actions: close/reopen, purchase invoice, purchase receipt, advance payment

These actions are native ERPNext operational tools and must not appear in the managed Phase 5D form.

## Enterprise ERP Purchase Order Pattern Findings

Official and source references reviewed:

- ERPNext Purchase Order documentation: `https://docs.frappe.io/erpnext/purchase-order`
- Installed ERPNext Purchase Order, Supplier Quotation, and Material Request source listed above.
- SAP S/4HANA purchase order processing and monitoring documentation entry point: `https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE`
- Oracle Fusion Cloud Procurement documentation entry point: `https://docs.oracle.com/en/cloud/saas/procurement/`
- Microsoft Dynamics 365 Supply Chain Management procurement documentation: `https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/`
- Odoo Purchase documentation: `https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase.html`

Practical enterprise alignment:

- Purchase Orders are supplier commitments once submitted/approved, but draft POs can be prepared internally before commitment.
- Mature ERP systems separate PO creation from approval/submission, receipt, invoice, and payment execution.
- Supplier, currency, item lines, quantities, prices, schedule dates, taxes/totals, and delivery or receiving locations are core PO data.
- Conversion from requests or quotations should preserve traceability through native mapping rules and source references.
- Receiving and billing are downstream execution flows, not part of draft PO creation.
- Approval and submit actions should be permissioned and workflow-aware, not added as a simple button in a draft form.

Design conclusion for this ERPNext Procurement Console:

- Direct managed draft PO entry is appropriate for Phase 5D because it completes the managed buying form family and removes native create leakage.
- SQ-to-PO and MR-to-PO conversion are important enterprise flows, but they require submitted upstream documents and should be deferred to a governed conversion phase.
- Submit/approval, receiving, billing, and payment must remain deferred operational phases.

## Phase 5D Scope Options

| Option | Description | Business value | Native alignment | Complexity | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| A | Direct managed Purchase Order draft entry only | High: completes managed buying form family and removes native PO create leakage | Strong: PO supports draft creation with required supplier/items/currency | Moderate | Lowest | Recommended |
| B | Direct managed PO plus Supplier Quotation-to-PO conversion | Higher traceability from quotes | Native mapper requires submitted SQ | High | High before governed SQ submit | Defer |
| C | Direct managed PO plus Material Request-to-PO conversion | Strong demand-to-order path | Native mapper requires submitted MR and default-supplier logic | High | High because Phase 5A PRs are draft/internal | Defer |
| D | Full PO lifecycle including submit/approval/receiving/billing | Very high operational coverage | Native ERPNext supports it | Very high | Unacceptable for this phase | Forbidden without owner approval |

Recommended Phase 5D scope: Option A.

Reasons:

- It finishes the fourth managed buying form without broadening operational risk.
- It mirrors Phase 5A/5B/5C save-first behavior.
- It uses ERPNext native draft validation while avoiding submit and downstream side effects.
- It gives users a productized PO create surface now, while preserving proper future conversion and approval design.
- It keeps Sales freeze and accepted Procurement managed forms easier to protect.

## Phase 5D Scope Boundary

### In Scope

- Managed Purchase Order direct create route.
- Managed saved draft Purchase Order route.
- Procurement Overview `New Purchase Order` action routes to managed form.
- Purchase Order Directory `New Purchase Order` action routes to the same managed form.
- Draft save only.
- Supplier autocomplete.
- Item autocomplete.
- Optional warehouse autocomplete for target warehouse/receiving location.
- Item line entry with item, quantity, line required date, warehouse, rate, UOM, and amount.
- Header `Default Required By` with inherited/manual line date behavior.
- Backend-derived UOM/conversion factor and native totals.
- Currency handled safely from ERPNext defaults and displayed compactly if useful.
- Secondary governed `Open ERP Form` after save only, if permission allows.
- Productized saved/review state after save.

### Deferred

- Supplier Quotation-to-Purchase Order conversion.
- Material Request/Purchase Request-to-Purchase Order conversion.
- `Get Items From` workflows.
- Submit/approval/reject workflows.
- Close, stop, hold, resume, amend, cancel, delivered actions.
- Purchase Receipt, receiving, stock transfer, or warehouse execution.
- Purchase Invoice, billing, payment, advance payment, or accounting execution.
- RFQ email/print/send.
- AI supplier quotation intake.
- Supplier or Item master-data create/edit.
- Item Price mutation.
- Default Supplier mutation.
- Blanket order/subcontracting/inter-company advanced flows.
- Taxes and charges editing as a full managed feature.

### Forbidden Without Explicit Owner Approval

- Any PO submit or approval action.
- Any downstream receiving, invoice, payment, or accounting action.
- Any conversion that bypasses ERPNext native mapping validation.
- Any mutation to Item Price, Default Supplier, Supplier master, or Item master.
- Any Sales runtime change.

## Managed Purchase Order Product Contract

### Business Purpose

Managed Purchase Order records a buyer-prepared draft order for a supplier before approval/submission or downstream execution. In Phase 5D it is still a draft preparation surface. It must not communicate commitment language beyond the ERPNext draft document.

Recommended user-facing subtitle:

- `Prepare supplier purchase details before approval.`

### Users And Roles

Primary users:

- Purchase Manager
- Purchase User

Access rule:

- User must be authenticated.
- User must pass Procurement workspace access rules.
- User must pass ERPNext Purchase Order read/create/write permissions for the requested operation.
- Sales-only and Guest users remain restricted.

### Entry Points

- Procurement Overview Start Buying Work: `New Purchase Order`
- Purchase Order Directory contextual action: `New Purchase Order`
- Direct URL: `/desk/procurement-console-purchase-order-form/new`
- Saved direct URL: `/desk/procurement-console-purchase-order-form/<purchase-order>`

No contextual conversion entry point should be active in Phase 5D.

### Routes

Recommended Frappe page route:

- Page name: `procurement_console_purchase_order_form`
- New route: `/desk/procurement-console-purchase-order-form/new`
- Saved route: `/desk/procurement-console-purchase-order-form/<purchase-order>`

### Header And Action Bar

Header contract:

- Kicker: `Purchase Order`
- New title: `New Purchase Order`
- Saved title: `<purchase-order-name>`
- Subtitle: `Prepare supplier purchase details before approval.`
- New badge: `New Purchase Order`
- Saved badge: `Purchase Order Recorded`
- Secondary badge: `Draft only`

Primary action:

- `Save Purchase Order`

Secondary actions:

- `Back to Purchase Orders`
- `Reset`
- `Open ERP Form` after save only, governed native exception
- Productized review action after save only if a Purchase Order review route exists or is added in Phase 5D

Forbidden visible actions:

- `Submit`
- `Approve`
- `Reject`
- `Create Purchase Receipt`
- `Create Purchase Invoice`
- `Payment`
- `Receive`
- `Bill`
- `Create Purchase Order`
- `Get Items From`
- `Update Item Price`
- `Set Default Supplier`

### Header Fields

Recommended request details section:

- Supplier: required, autocomplete.
- Transaction Date: required, default today.
- Default Required By: optional header default, but item line required dates must be present before save.
- Currency: compact display or controlled field, default from ERPNext company/supplier context.
- Target Warehouse: optional header default if useful. If shown, it should seed new line warehouses but not be required unless native validation requires it.
- Buying Price List: optional/advanced, preferably hidden or compact unless implementation needs it to derive item rates.

Company should remain backend context in single-company UI. It must not be shown as a large editable-looking field.

### Item Lines

Desktop/tablet shared header:

`Item | Qty | Line Required By | Warehouse | Rate | UOM | Amount | Action`

Line behavior:

- Item autocomplete is required.
- Quantity is required and must be positive.
- Line Required By is required before save.
- Warehouse is optional unless native validation or selected item behavior requires it.
- Rate is required for Phase 5D draft-save quality, even if ERPNext JSON does not mark it required.
- UOM displays `Derived` before item selection and actual UOM after selection; it is read-only metadata.
- Amount is derived from quantity and rate and displayed read-only.
- Add/remove line behavior must remain stable with 1, 2, and 3+ lines.
- Blank rows should be ignored only if truly empty; partially filled rows must produce explicit validation.

### Date Inheritance

Use the accepted Phase 5A/5B/5C inherited/manual rule:

- Header label: `Default Required By`.
- Line label: `Line Required By`.
- Helper copy: `New item lines use the default date unless changed.`
- New lines inherit the current header date.
- Lines that still inherit the header date update immediately when the header date changes.
- Manually edited line dates are preserved when the header date changes.
- Adding a new line after a header change uses the current header date and starts as inherited.

### Validation Behavior

Client validation may help with clear messages, but backend validation is authoritative.

Minimum validation before save:

- Supplier is present.
- Transaction Date is present.
- Currency is present or derivable.
- At least one valid item line exists.
- Each non-empty line has item, quantity, line required date, rate, UOM/conversion factor derivable by backend.
- Quantity and rate are numeric and non-negative; quantity must be positive unless ERPNext unit-price item settings are explicitly supported later.
- Submitted/cancelled/closed Purchase Orders cannot be edited through the draft managed save method.

### Saved State Behavior

After save:

- Route to `/desk/procurement-console-purchase-order-form/<purchase-order>`.
- Header shows saved PO name and `Purchase Order Recorded`.
- `Open ERP Form` appears only after save and only as a secondary governed native exception.
- Productized review route may appear if implemented and protected.
- The form remains draft-save only; no submit, approval, receiving, billing, or payment actions appear.

### Empty, Restricted, Unavailable, And Error States

Use the existing managed-form state model:

- `ready`: user can create or edit draft PO.
- `restricted`: user lacks workspace or DocType permission.
- `unavailable`: ERPNext dependency or default context cannot be resolved safely.
- `validation_error`: payload is missing required business fields.
- `error`: real technical failure.

Restricted users must not see a usable save action.

### Responsive UI Contract

Required viewport checks:

- 1136x768
- 1240x768
- 1440x900

Expectations:

- No horizontal overflow.
- No clipped fields, buttons, UOM pill, amount display, or remove action.
- No duplicate page shell/chrome.
- No stacked stale form after repeated navigation.
- Autocomplete overlays remain attached to active supplier/item/warehouse inputs.
- Shared item-line header is visible at desktop/tablet widths; responsive laptop wrapping remains intentional and readable.
- No random gradients or one-off colors.
- Shared primary/secondary action styling matches PR/RFQ/SQ managed forms.

## Native Leakage And Conversion Policy

Allowed in Phase 5D:

- `Open ERP Form` after save only, as a secondary governed native exception if the user has permission.
- Native ERPNext validation through document APIs.

Forbidden in Phase 5D:

- Raw ERPNext Purchase Order create page as a productized primary create target.
- Submit, cancel, amend, stop, close, hold, resume, delivered actions.
- Purchase Receipt, Purchase Invoice, Payment, Payment Request, Advance Payment, stock transfer, or receiving actions.
- Native `Get Items From` as an active productized action.
- Supplier Quotation-to-PO conversion.
- Material Request/Purchase Request-to-PO conversion.
- Item Price update.
- Default Supplier update.
- Supplier or Item master mutation.

Conversion recommendation:

- SQ-to-PO should be a future governed phase after Supplier Quotation submit/review is productized. It must use `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order` and preserve ERPNext source references.
- MR/PR-to-PO should be a future governed phase after Purchase Request submit/review is productized. It must use `erpnext.stock.doctype.material_request.material_request.make_purchase_order` or `make_purchase_order_based_on_supplier` where appropriate and respect default-supplier grouping.
- No conversion should custom-copy rows around ERPNext native mapping rules without explicit owner approval.

## Backend/API Design

Recommended backend module:

- `erp_workspace_ui/procurement_console/managed_purchase_order.py`

Recommended whitelisted methods:

- `get_managed_purchase_order_context(name=None, mode=None)`
- `save_managed_purchase_order_draft(payload)`
- Optional: `get_managed_purchase_order_item_defaults(item_code, supplier=None, transaction_date=None, currency=None, company=None, buying_price_list=None)` if existing item search/default helpers are insufficient.

### Context Response Contract

`get_managed_purchase_order_context` should return:

- state kind: `ready`, `restricted`, `unavailable`, or `error`.
- current mode: `new` or `saved`.
- document identity for saved PO.
- permission flags for read/create/write.
- default transaction date.
- default company backend context.
- default currency, resolved independently from company.
- default buying price list if available.
- default required by date if established.
- field values for saved draft.
- item rows for saved draft.
- action model with only allowed actions.
- productized route targets.
- secondary native route only after save.

### Save Payload Shape

Recommended payload:

```json
{
  "name": "PUR-ORD-2026-00001",
  "header": {
    "supplier": "Supplier Name",
    "transaction_date": "2026-05-15",
    "default_required_by": "2026-05-20",
    "currency": "MMK",
    "set_warehouse": "Stores - MMD",
    "buying_price_list": "Standard Buying"
  },
  "items": [
    {
      "item_code": "ITEM-001",
      "qty": 5,
      "line_required_by": "2026-05-20",
      "warehouse": "Stores - MMD",
      "rate": 1000
    }
  ]
}
```

Backend must ignore or reject forbidden fields such as `docstatus`, `status`, `workflow_state`, `submit`, `cancel`, `amend`, `per_received`, `per_billed`, `received_qty`, `billed_amt`, `material_request`, `supplier_quotation`, `item_price`, and default supplier mutations.

### Backend Rules

- Require authenticated user.
- Require Procurement workspace access.
- Require ERPNext Purchase Order read/create/write permission as appropriate.
- Use `frappe.get_doc`, `doc.insert`, and `doc.save`; no raw SQL/DB writes for business documents.
- Save only draft Purchase Orders.
- Reject editing submitted, cancelled, closed, or non-draft Purchase Orders through the managed draft method.
- Resolve company from safe defaults and site context.
- Resolve currency independently from company name.
- Derive UOM, stock UOM, conversion factor, item name, and native item defaults from ERPNext item behavior where possible.
- Let ERPNext calculate taxes/totals and run native validation.
- Return validation errors cleanly instead of silent save failures.
- Return saved name and productized route target after save.
- Do not return submit, approval, receive, bill, payment, Item Price, Default Supplier, SQ-to-PO, or MR-to-PO actions.

## Frontend/UI Design

Recommended frontend file:

- `erp_workspace_ui/public/js/procurement_console/procurement_console_purchase_order_form.js`

Recommended page folder:

- `erp_workspace_ui/erp_workspace_ui/page/procurement_console_purchase_order_form/`

UI architecture:

- Follow accepted PR/RFQ/SQ managed form lifecycle and shell patterns.
- Clear or replace page content on route load; do not append shells.
- Keep Procurement sidebar active.
- Avoid native Frappe create form leakage.
- Use the same managed-form header/action/token classes as accepted forms.
- Use the same floating autocomplete overlay positioning helper as accepted managed forms.
- Do not introduce new shared component or CSS unless truly necessary. If shared runtime/CSS is touched, Sales freeze and protected workspace gate are mandatory.

Visual standards:

- No random gradients.
- No decorative backgrounds outside shared token system.
- No large company field.
- No duplicate `Purchase Order`/`PO Form` chrome inside body.
- Compact command row attached to form composition.
- `Save Purchase Order` primary; Back/Reset/Open ERP Form secondary.
- Item-line shared header and responsive laptop behavior aligned with SQ form, with PO-specific columns.
- UOM pill reads `Derived` before item selection and actual UOM after selection.
- Amounts update predictably from qty/rate.
- Supplier, item, and warehouse autocomplete overlays attach to active inputs and are not clipped.

## Navigation And Route Contract

After Phase 5D implementation acceptance:

- Procurement Overview `New Purchase Order` routes to `/desk/procurement-console-purchase-order-form/new`.
- Purchase Order Directory `New Purchase Order` routes to the same managed form.
- Productized create actions must not route to `/desk/purchase-order/new-*` or raw native create pages.
- Saved route is `/desk/procurement-console-purchase-order-form/<purchase-order>`.
- Direct URL users without permission see restricted/unavailable state, not native fallback.
- Native `Open ERP Form` is available only after save and only as a secondary governed exception.
- RFQ, Supplier Quotation, and Purchase Request existing managed routes remain unchanged.
- No source-driven conversion action should be active in Phase 5D.

## Permission And Security Matrix

| Role/User type | View managed PO | Create draft PO | Edit draft PO | Open ERP after save | Submit/approve/receive/bill/pay |
| --- | --- | --- | --- | --- | --- |
| Purchase Manager | allowed if ERPNext permits | allowed if ERPNext permits | allowed if ERPNext permits | secondary, if ERPNext permits | forbidden in managed form |
| Purchase User | allowed if ERPNext permits | allowed if ERPNext permits | allowed if ERPNext permits | secondary, if ERPNext permits | forbidden in managed form |
| Sales-only user | denied unless also has required purchase permissions | denied | denied | denied | forbidden |
| Guest/unauthenticated | denied | denied | denied | denied | forbidden |

Security requirements:

- Do not grant access by role family alone.
- Do not bypass ERPNext DocType permission checks.
- Do not trust client totals, UOM, conversion factor, document status, or source references.
- Do not expose hidden native operations through action payloads.
- Log/save through ERPNext document APIs so audit trails and validation remain intact.

## Test And Protection Plan

### Python Contract Tests

Add tests for:

- Context for new Purchase Order is ready for Purchase Manager/Purchase User when ERPNext permission allows.
- Sales-only and Guest users are restricted where test patterns support it.
- Default company and default currency are resolved independently.
- Save creates a draft Purchase Order only.
- Missing supplier is rejected.
- Missing items are rejected.
- Missing item, qty, line required date, or rate in non-empty rows is rejected.
- Forbidden header/child fields are ignored or rejected.
- Submitted/cancelled/non-draft PO cannot be edited through managed draft save.
- Returned actions do not include submit, approve, receive, bill, pay, purchase receipt, purchase invoice, Item Price, Default Supplier, SQ-to-PO, or MR-to-PO.
- Governance manifest/registry tests prove managed PO route is productized and native PO create is no longer primary after Phase 5D.
- Existing PR/RFQ/SQ route/action contract remains unchanged.

### Focused Browser Smoke

Create a focused Phase 5D smoke for Purchase Manager and Purchase User covering:

- Overview `New Purchase Order` opens managed PO form.
- Purchase Order Directory `New Purchase Order` opens the same managed PO form.
- Direct managed new route loads without duplicate shell/chrome.
- Supplier autocomplete attaches to supplier input.
- Item autocomplete attaches to item input.
- Warehouse autocomplete attaches to warehouse input if warehouse field is exposed.
- UOM displays `Derived` before item selection and actual UOM after item selection/save.
- Qty/rate update amount.
- `Default Required By` and `Line Required By` inheritance/manual behavior works.
- Add 3+ item lines; shared header row and responsive layout remain stable.
- Remove line works.
- Save creates draft PO and routes to saved managed PO route.
- Saved PO screenshot captured.
- `Open ERP Form` appears only after save and is secondary.
- No raw ERPNext Purchase Order create route from productized actions.
- No duplicate shell after Overview -> New PO, Directory -> New PO, Back -> New PO, repeated navigation, and browser back/forward if supported.
- No forbidden action labels appear: `Submit`, `Approve`, `Create Purchase Receipt`, `Purchase Invoice`, `Receive`, `Bill`, `Payment`, `Update Item Price`, `Set Default Supplier`, `Get Items From`.
- Screenshots at 1136x768, 1240x768, and 1440x900.
- Autocomplete open-state screenshots at 1136px.
- No focus shrink, clipping, horizontal overflow, or page stacking.

### Required Gates

Before commit:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched JS/smoke files
- `bash -n ui_smoke/run_protected_workspace_gate.sh`
- `git diff --check HEAD`
- Sales freeze protection with correct Sales Manager and Sales User credentials.

After source commit/push and live alignment:

- Focused Phase 5D live smoke for Purchase Manager and Purchase User.
- Sales freeze if shared runtime/CSS/navigation changed.
- Full protected workspace gate with explicit Sales and Purchase credentials.

## Implementation Sequence Proposal

1. Reconfirm source state and Phase 5A/5B/5C protected baseline.
2. Verify native PO contract from installed source and site metadata again.
3. Implement backend `managed_purchase_order.py` with context and draft save only.
4. Add Python tests for permissions, payload validation, draft save, and forbidden actions.
5. Add Frappe page route `procurement_console_purchase_order_form`.
6. Implement frontend form using accepted managed-form shell and item-line patterns.
7. Integrate Overview and Purchase Order Directory create actions to the same managed route.
8. Add governance tests proving native PO create is no longer primary.
9. Add focused Phase 5D smoke.
10. Run source validation and Sales freeze.
11. Commit and push.
12. Align approved runtime files to live, reload new page if required, clear cache.
13. Run focused live Phase 5D smoke.
14. Run protected workspace gate.
15. Only after acceptance, write Phase 5D protected baseline documentation.

## Risks And Open Questions

Risks:

- Purchase Order is operationally sensitive because submit updates demand/order state and enables receiving/billing/payment paths.
- ERPNext item defaults, price list behavior, currency conversion, and taxes can be complex. Phase 5D should lean on ERPNext native APIs rather than client-side calculation for business truth.
- Native mapping from SQ/MR contains traceability and default-supplier behavior; bypassing it would create audit risk.
- Taxes/charges may be business-important but are not required for the first managed draft form. If owner requires tax editing, it should be a scoped follow-up.
- Multi-currency behavior may need additional UI if suppliers use non-company currency.
- Subcontracting, blanket orders, drop ship, inter-company, advance payment, and unit-price item workflows are native advanced flows and should remain governed native exceptions for now.

Open questions for owner before implementation if policy changes:

- Should Phase 5D show Currency as editable or compact read-only context for the current single-company/single-currency operating mode?
- Should Buying Price List be hidden/defaulted, compactly visible, or editable?
- Should target warehouse be shown at header level, line level, or both?
- Should taxes/charges be omitted entirely, shown as read-only totals after save, or exposed as an advanced native-only concern?
- Should there be a productized Purchase Order review route in Phase 5D, or should saved managed form be the review surface?

Recommended defaults if no new owner direction is provided:

- Currency compact/read-only by default, with backend native value.
- Buying Price List hidden/defaulted.
- Warehouse exposed at line level and optionally as a header default if existing design has room.
- Taxes/charges not editable in Phase 5D; show read-only totals only if native backend returns them safely.
- Saved managed PO form is the productized review surface for Phase 5D.
