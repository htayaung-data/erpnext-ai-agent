# Procurement Console Phase 5C Supplier Quotation Design Plan

Date: 2026-05-15

Baseline dependency: `3490363dbeb3ad3176b82969d6727c5911a123d5`

Baseline document: `_docs/erp-ui-customization/procurement-console-phase5a-5b-managed-buying-baseline-2026-05-15.md`

## Executive Recommendation

Recommended Phase 5C scope: implement a managed Supplier Quotation form for direct buyer-entered supplier offers, saved as draft only.

Do not implement RFQ-to-Supplier Quotation conversion in the first Phase 5C implementation. ERPNext's native `Request for Quotation` to `Supplier Quotation` mapper requires a submitted RFQ (`docstatus = 1`), while the accepted Phase 5B managed RFQ records draft RFQs only. Bypassing that mapper with custom row-copy logic would weaken ERPNext traceability and validation.

Phase 5C should therefore replace the primary `New Supplier Quotation` productized create actions with a managed draft form, while keeping RFQ-sourced Supplier Quotation creation deferred until a governed RFQ submit/review step is approved.

## Baseline Understanding

Phase 5A and 5B are protected:

- Managed Purchase Request route: `/desk/procurement-console-purchase-request-form/new`
- Managed RFQ route: `/desk/procurement-console-rfq-form/new`
- Overview and directory create actions route to managed forms.
- Productized create actions must not leak to native ERPNext create pages for accepted managed forms.
- Save actions are draft-only: `Save Request` and `Save RFQ`.
- `Open ERP Form` is allowed only after a document is saved and only as a secondary governed native exception.
- Forms use the accepted managed form language: compact header, shared action hierarchy, no random gradients, no duplicate shell/chrome.
- Date behavior is protected: `Default Required By`, `Line Required By`, inherited/manual line-date state, and the helper copy `New item lines use the default date unless changed.`
- Item line behavior is protected: shared item-line header at desktop widths, responsive row layout at laptop widths, clean UOM metadata, attached autocomplete overlays.
- Sales freeze and protected workspace gates are mandatory after any shared runtime/CSS/navigation impact.

The Phase 5C implementation must preserve all of this behavior.

## Native ERPNext Findings

Installed ERPNext source inspected in the backend container:

- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.py`
- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.js`
- `erpnext/buying/doctype/request_for_quotation/request_for_quotation.json`
- `erpnext/buying/doctype/request_for_quotation_supplier/request_for_quotation_supplier.json`
- `erpnext/buying/doctype/request_for_quotation_item/request_for_quotation_item.json`
- `erpnext/buying/doctype/supplier_quotation/supplier_quotation.py`
- `erpnext/buying/doctype/supplier_quotation/supplier_quotation.js`
- `erpnext/buying/doctype/supplier_quotation/supplier_quotation.json`
- `erpnext/buying/doctype/supplier_quotation_item/supplier_quotation_item.json`
- `erpnext/buying/report/supplier_quotation_comparison/supplier_quotation_comparison.py`

### Request For Quotation

`Request for Quotation` is submittable and uses naming series `PUR-RFQ-.YYYY.-`.

Required header fields found in DocType JSON:

- `naming_series`
- `company`
- `transaction_date`
- `suppliers`
- `items`
- `message_for_supplier`
- `status`
- `subject`

Required child fields:

- `Request for Quotation Supplier.supplier`
- `Request for Quotation Item.item_code`
- `Request for Quotation Item.qty`
- `Request for Quotation Item.schedule_date`
- `Request for Quotation Item.uom`
- `Request for Quotation Item.stock_uom`
- `Request for Quotation Item.conversion_factor`

Native methods:

- `erpnext.stock.doctype.material_request.material_request.make_request_for_quotation`
  - maps submitted Purchase Material Requests to RFQ.
  - validates `docstatus = 1` and `material_request_type = Purchase`.
- `erpnext.buying.doctype.request_for_quotation.request_for_quotation.make_supplier_quotation_from_rfq`
  - maps submitted RFQ to Supplier Quotation.
  - validates RFQ `docstatus = 1`.
  - can receive `for_supplier` and sets supplier, currency, and buying price list from party details/defaults.
- `erpnext.buying.doctype.request_for_quotation.request_for_quotation.get_rfq_containing_supplier`
  - searches submitted RFQs containing a selected supplier for a selected company.
- RFQ native JS exposes `Create > Supplier Quotation`, Supplier Portal/email actions, and native Query Report routing to Supplier Quotation Comparison. These should not be exposed in the managed Phase 5C form.

### Supplier Quotation

`Supplier Quotation` is submittable and uses naming series `PUR-SQTN-.YYYY.-`.

Required header fields found in DocType JSON:

- `naming_series`
- `supplier`
- `transaction_date`
- `company`
- `currency`
- `conversion_rate`
- `items`
- `status`

Other important header fields:

- `valid_till`
- `supplier_name` read-only
- `grand_total` read-only

Required item fields found in `Supplier Quotation Item`:

- `item_code`
- `qty`
- `stock_uom`
- `uom`
- `conversion_factor`
- `base_rate`
- `base_amount`

Important item fields for Phase 5C:

- `rate`
- `amount`
- `expected_delivery_date`
- `warehouse`
- `request_for_quotation`
- `request_for_quotation_item`
- `material_request`
- `material_request_item`

Native methods:

- `erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order`
  - maps submitted Supplier Quotation to Purchase Order.
  - validates Supplier Quotation `docstatus = 1`.
  - must remain deferred.
- `erpnext.stock.doctype.material_request.material_request.make_supplier_quotation`
  - maps submitted Purchase Material Request to Supplier Quotation.
  - validates `docstatus = 1` and `material_request_type = Purchase`.
  - must remain deferred because Phase 5A Purchase Requests are draft/internal.
- Supplier Quotation native JS exposes `Get Items From > Request for Quotation`, `Get Items From > Material Request`, `Create > Purchase Order`, `Update Items`, and `Quotation`.
  - Phase 5C managed form must not expose these tools as primary actions.

Supplier Quotation can be created directly without an RFQ because the Supplier Quotation DocType requires supplier, company, currency, conversion rate, and items, but item RFQ references are optional. This is a native ERPNext capability, not an inference.

### Supplier Quotation Comparison

The accepted Procurement Quote Comparison wraps ERPNext's native `Supplier Quotation Comparison` query report.

Native report source filters Supplier Quotation Items with `docstatus < 2`, company, transaction date, optional item, supplier, supplier quotation, and RFQ filters. It displays supplier, item, quantity, UOM, price, unit price, quotation, valid till, lead time, and RFQ reference.

Implication for Phase 5C:

- Direct managed Supplier Quotations can participate in general comparison by supplier/item/date when saved.
- RFQ-filtered comparison depends on preserving `request_for_quotation` and `request_for_quotation_item`; this should only be populated through native RFQ mapping once RFQ submit/review is productized.

### Site Permissions And Data

Site permission check on 2026-05-15:

| User | Supplier Quotation read/create/write/submit/cancel | RFQ read/create/write/submit/cancel |
| --- | --- | --- |
| `purchase.manager@meet.com` | yes / yes / yes / yes / yes | yes / yes / yes / yes / yes |
| `purchase.ygn.01@meet.com` | yes / yes / yes / yes / no | yes / yes / yes / no / no |
| `sale.manager@meet.com` | no / no / no / no / no | no / no / no / no / no |
| `sale.user@meet.com` | no / no / no / no / no | no / no / no / no / no |
| Guest | no / no / no / no / no | no / no / no / no / no |

Current data snapshot:

- Supplier Quotations: 10
- Supplier Quotation Items: 16
- RFQs: 18
- Current Supplier Quotations are submitted and all sampled Supplier Quotation Items are RFQ-linked.

## Enterprise Pattern Alignment

Official product references reviewed:

- ERPNext Buying documentation and installed ERPNext source for RFQ, Supplier Quotation, and Supplier Quotation Comparison.
- SAP S/4HANA sourcing documentation for RFQ/quotation-to-award patterns.
- Microsoft Dynamics 365 Supply Chain Management RFQ documentation for RFQ replies and purchase-order award patterns.
- Odoo Purchase documentation for RFQ/vendor quotation/purchase order progression.
- Oracle Fusion Procurement/Sourcing documentation for supplier negotiation responses and award concepts.

Practical pattern summary:

- Internal demand/request is not supplier communication.
- RFQ is the sourcing request to suppliers.
- Supplier Quotation is the supplier offer/response.
- Quote comparison is a buyer review and award-support surface.
- Purchase Order is the purchase commitment.
- Enterprise systems usually support both supplier-entered responses and buyer-entered/internal capture of supplier offers.
- Enterprise systems preserve source traceability when converting RFQ responses into awards, rather than copying rows outside native mapping rules.

Recommendation for this ERPNext implementation:

- Productize buyer-entered Supplier Quotation draft capture first.
- Defer supplier portal/email/send behavior.
- Defer RFQ-to-Supplier Quotation mapping until submitted RFQs are governed.
- Defer Supplier Quotation-to-Purchase Order mapping until Phase 5D or later.
- Keep Quote Comparison read-only.

Reference links:

- ERPNext Request for Quotation: `https://docs.frappe.io/erpnext/user/manual/en/request-for-quotation`
- ERPNext Supplier Quotation: `https://docs.frappe.io/erpnext/user/manual/en/supplier-quotation`
- Microsoft Dynamics 365 request for quotation overview: `https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations`
- Microsoft Dynamics 365 compare bids and award contracts: `https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/tasks/compare-bids-award-contract`
- Odoo Purchase agreements and RFQ workflow: `https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/manage_deals/blanket_orders.html`
- SAP Help Portal sourcing/RFQ reference: `https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE`
- Oracle Fusion Procurement/Sourcing documentation entry point: `https://docs.oracle.com/en/cloud/saas/procurement/`

## Phase 5C Scope Options

| Option | Description | Business Value | Native Alignment | Complexity | Risk | Impact |
| --- | --- | --- | --- | --- | --- | --- |
| A | Managed Supplier Quotation form, direct entry only | Medium-high: captures supplier offers without native create leakage | Strong: Supplier Quotation supports direct creation | Moderate | Lowest | Preserves Phase 5A/5B; Quote Comparison can use saved SQ rows |
| B | Managed Supplier Quotation launched from managed RFQ context | High traceability if RFQ is submitted | Weak today: Phase 5B RFQs are draft-only, native mapper requires submitted RFQ | High | High | Risks bypassing ERPNext mapping if done now |
| C | RFQ response capture tied directly to Quote Comparison | High for buyer comparison | Partial: requires RFQ response state and possibly supplier portal/send semantics | High | High | Could mix data entry with read-only report boundary |
| D | Defer SQ form and implement managed RFQ review/send-first step | Strong traceability foundation | Strong if RFQ submit/send becomes governed | Moderate-high | Medium | Delays Supplier Quotation productization |

Recommended: Option A for Phase 5C.

Reasoning:

- It removes the next native create leakage point without disturbing the accepted managed RFQ baseline.
- It uses ERPNext's native Supplier Quotation document APIs and validation.
- It avoids fake RFQ mapping from draft RFQs.
- It can be implemented with the accepted Phase 5A/5B managed-form shell and protection tests.
- It keeps the future RFQ-to-SQ flow clean for a later phase that first productizes RFQ submit/review.

## Deferred Scope

The following remain outside Phase 5C implementation unless explicitly approved later:

- RFQ-to-Supplier Quotation conversion from submitted RFQs.
- Supplier portal response capture.
- RFQ submit/send email.
- Supplier Quotation submit.
- Supplier Quotation-to-Purchase Order conversion.
- Purchase Order managed form.
- Purchase Order approval/rejection.
- Receiving, billing, payment, accounting.
- Item Price mutation.
- Default Supplier mutation.
- Supplier or Item master create/edit.
- PR-to-RFQ conversion.

## Recommended Business Flow

1. Buyer opens Procurement Overview or Supplier Quotation Directory.
2. Buyer selects `New Supplier Quotation`.
3. Productized route opens `/desk/procurement-console-supplier-quotation-form/new`.
4. Buyer selects a supplier.
5. Buyer enters quote date and optional validity date.
6. Buyer adds item lines:
   - item
   - quantity
   - rate
   - expected delivery date
   - optional warehouse
   - derived/read-only UOM
   - calculated amount
7. Buyer saves with `Save Quotation`.
8. ERPNext records a draft Supplier Quotation using native document APIs.
9. Saved state shows `Quotation Recorded`, secondary `Review Quote`, and secondary governed `Open ERP Form`.
10. Buyer may use existing productized Supplier Quotation Review or Quote Comparison for visibility.

Direct Supplier Quotation creation from Supplier Quotation Directory should be allowed when ERPNext create/read/write permissions allow it.

Creation from RFQ Review or managed RFQ should not be active in initial Phase 5C. If shown later, it must be absent or disabled for draft RFQs with clear copy such as `Submit the RFQ before creating supplier quotations.`

Currency should be visible as read-only context or a compact selector only if multi-currency data requires it. For the current single-company baseline, company should remain hidden/backend context. Currency and conversion rate should be derived from ERPNext defaults/party details where possible and not dominate the first implementation UI.

Supplier Quotation must remain draft/save-first. Submit must be excluded.

## UI/UX Contract

Managed Supplier Quotation must follow the accepted Phase 5A/5B form standard.

Header:

- kicker: `Supplier Quotation`
- new title: `New Supplier Quotation`
- saved title: Supplier Quotation id
- subtitle: `Record supplier offer details for buyer comparison.`
- new badge: `New Quotation`
- saved badge: `Quotation Recorded`
- secondary badge: `Buyer entry`

Actions:

- primary: `Save Quotation`
- secondary: `Back to Supplier Quotations`
- secondary: `Reset`
- after save only, secondary: `Review Quote`
- after save only, secondary governed native exception: `Open ERP Form`
- no `Submit`, `Create Purchase Order`, `Update Item Price`, `Set Default Supplier`, `Receive`, `Bill`, or `Pay`

Field layout:

- Supplier selection is the first business field.
- Quote date and valid till appear together.
- Company is not displayed as a large editable field.
- Currency is compact/read-only unless implementation proves buyer selection is required.
- If currency is displayed, it must not crowd line entry or action hierarchy.

Line item layout:

- Use one shared header row at desktop/tablet: `Item | Qty | Rate | Amount | Expected By | Warehouse | UOM | Action`.
- At 1136px, use the accepted responsive two-line row/header behavior from Phase 5A/5B.
- UOM is derived read-only metadata.
- Amount is calculated/read-only from quantity and rate.
- Rate is buyer-entered numeric input.
- `Add line` remains visually connected to the item section.
- Remove action is secondary and not visually dominant.

Date behavior:

- Header validity date is not the same as line delivery date.
- Line date should be labeled `Expected By`.
- If a default expected date is included, use the same inherited/manual state pattern as Phase 5A/5B.
- If no default expected date is included, each line may require its own expected date.

Autocomplete overlay behavior:

- Supplier autocomplete attaches to supplier input.
- Item autocomplete attaches to item input.
- Warehouse autocomplete attaches to warehouse input.
- Overlays are fixed/floating, not clipped, not trapped inside cards, and do not shift layout.

Responsive and shell lifecycle:

- Verify at 1136x768, 1240x768, and 1440x900.
- No duplicate Frappe page shell.
- No stacked old shell after route navigation.
- No horizontal body overflow.
- No gradients or one-off colors.
- Use shared tokens/classes from the accepted managed form styling.

## Backend/API Contract

Proposed module:

- `erp_workspace_ui/procurement_console/managed_supplier_quotation.py`

Proposed whitelisted methods:

- `get_managed_supplier_quotation_context(name=None, mode=None)`
- `save_managed_supplier_quotation_draft(payload)`
- optional item/supplier defaults helper only if existing shared search/default helpers are insufficient.

Payload shape:

```json
{
  "name": "new or Supplier Quotation name",
  "header": {
    "supplier": "Supplier name",
    "transaction_date": "YYYY-MM-DD",
    "valid_till": "YYYY-MM-DD or empty",
    "currency": "optional compact/read-only context"
  },
  "items": [
    {
      "item_code": "Item",
      "qty": 1,
      "rate": 0,
      "expected_delivery_date": "YYYY-MM-DD or empty",
      "warehouse": "optional"
    }
  ]
}
```

Backend rules:

- Require authenticated user.
- Require Procurement role family.
- Require ERPNext `Supplier Quotation` read/create/write permissions for new drafts.
- Require read/write permission for existing draft edits.
- Use `frappe.get_doc`, `doc.insert`, and `doc.save`.
- Do not use raw SQL writes for business documents.
- Reject submitted/cancelled Supplier Quotations for managed draft editing.
- Allowlist header fields: `name`, `supplier`, `transaction_date`, `valid_till`, `currency` only if needed.
- Allowlist item fields: `item_code`, `qty`, `rate`, `expected_delivery_date`, `warehouse`.
- Derive company from ERPNext defaults, not from user-editable UI.
- Derive supplier name, currency/conversion rate, item UOM, stock UOM, and conversion factor using ERPNext document defaults and item/party data.
- Require at least one item.
- Require supplier.
- Require item, positive quantity, and non-negative rate.
- Let ERPNext calculate totals, amount, base rate, base amount, taxes/defaults where applicable.
- Return no submit/send/create-PO/item-price/default-supplier/receive/bill/pay actions.
- Return saved productized review route and secondary native form route only after save and only if permission allows.

State kinds:

- `ready`: context or saved draft loaded.
- `restricted`: user lacks Procurement or ERPNext permission.
- `unavailable`: required native fields/defaults are missing.
- `error`: real technical failure.

Audit/security expectations:

- Do not bypass ERPNext permissions.
- Do not set `ignore_permissions`.
- Do not accept forbidden fields from payload.
- Do not populate RFQ source fields unless a future native mapper call creates them.

## Navigation And Route Contract

Proposed managed route:

- `/desk/procurement-console-supplier-quotation-form/new`
- `/desk/procurement-console-supplier-quotation-form/<supplier-quotation>`

Expected route key:

- `procurement-console-supplier-quotation-form`

Overview:

- `New Supplier Quotation` should route to the managed Supplier Quotation form after Phase 5C acceptance.

Supplier Quotation Directory:

- Contextual `New Supplier Quotation` should route to the same managed form when ERPNext permissions allow it.

Supplier Quotation Review:

- Saved form may route to existing productized Supplier Quotation Review.

RFQ Review / managed RFQ:

- No active `Create Supplier Quotation` action for draft managed RFQs.
- Future action may be designed only for submitted RFQs and must use ERPNext's native `make_supplier_quotation_from_rfq` mapper.

Native route exceptions:

- Native Supplier Quotation create route remains a governed fallback only until the managed form is accepted.
- After acceptance, productized create actions must not navigate to native Supplier Quotation create pages.
- `Open ERP Form` after save remains a secondary governed native exception.

## Permission And Security Matrix

| Role/User family | View SQ | Create managed SQ draft | Edit managed SQ draft | Submit SQ | Open ERP Form after save | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Purchase Manager | Yes if ERPNext allows | Yes if ERPNext allows | Yes if ERPNext allows | Deferred/not exposed | Yes if ERPNext allows | Site currently allows submit/cancel, but Phase 5C UI must not expose it. |
| Purchase User | Yes if ERPNext allows | Yes if ERPNext allows | Yes if ERPNext allows | Deferred/not exposed | Yes if ERPNext allows | Site currently allows submit but not cancel; managed UI remains draft-only. |
| Sales Manager/User | No unless also granted purchase roles and DocType permissions | No | No | No | No | Must not receive Procurement access from Sales role family alone. |
| Guest | No | No | No | No | No | Restricted. |

## Native Exception And Leakage Policy

Forbidden productized UI leakage:

- Native Supplier Quotation create route from Overview or Supplier Quotation Directory after Phase 5C acceptance.
- Native Query Report route.
- Native Supplier Portal or email send actions.
- Native `Get Items From` actions until each source mapping is explicitly productized.
- Native `Create Purchase Order`.
- Native `Submit`, `Cancel`, `Amend`, `Stop`, `Update Items`, `Update Item Price`, `Set Default Supplier`.

Allowed governed exception:

- `Open ERP Form` after a Supplier Quotation draft exists, secondary style only, permission-aware.

## Test And Smoke Plan

Python/unit contract tests:

- Context `ready`, `restricted`, `unavailable`, and `error` states.
- Purchase roles allowed only when ERPNext permission allows.
- Sales/Guest restricted.
- Save draft creates `Supplier Quotation` with `docstatus = 0`.
- Supplier is required.
- At least one item is required.
- Item, quantity, rate validation.
- Forbidden header/item fields ignored or rejected.
- Submitted/cancelled Supplier Quotation cannot be edited through managed draft save.
- No submit/create-PO/item-price/default-supplier/receive/bill/pay actions returned.
- Saved payload includes productized review route.
- Native route target appears only as secondary after save.

Governance tests:

- Managed Supplier Quotation route is registered.
- Overview and Supplier Quotation Directory actions target the same managed route.
- Native Supplier Quotation create route is no longer primary after acceptance.
- Supplier Quotation-to-Purchase Order remains governed/deferred.
- Sales registry/routes unchanged.

Focused browser smoke:

- Purchase Manager opens Overview and clicks `New Supplier Quotation`.
- Purchase Manager opens Supplier Quotation Directory and clicks `New Supplier Quotation`.
- Purchase User follows the same flow if ERPNext permission allows.
- Both create actions route to the same managed form.
- Supplier autocomplete works and overlay is attached.
- Item autocomplete works and overlay is attached.
- Warehouse autocomplete works if shown.
- Save Quotation with one supplier/item/rate succeeds.
- Saved state shows `Quotation Recorded`.
- `Open ERP Form` appears only after save and is secondary.
- Productized `Review Quote` appears after save.
- No raw native create route.
- No duplicate shell/chrome after repeated route navigation.
- No horizontal overflow or clipping at 1136x768, 1240x768, and 1440x900.
- Visual screenshots captured for new, 3+ item lines, supplier autocomplete, item autocomplete, warehouse autocomplete, and saved state.

Forbidden action labels:

- `Submit`
- `Approve`
- `Create Purchase Order`
- `Update Item Price`
- `Set Default Supplier`
- `Receive`
- `Bill`
- `Pay`

Protection gates:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched JS/smoke files
- `git diff --check HEAD`
- `npm --prefix ui_smoke run test:sales-freeze-protection`
- `npm --prefix ui_smoke run test:protected-workspaces`

Live acceptance:

- Commit and push before live alignment.
- Sync only approved Phase 5C runtime files.
- Clear cache.
- Restart only if Python/page loading requires it.
- No live repo commit.
- Run focused Phase 5C live smoke for Purchase Manager and Purchase User.
- Run Sales freeze and protected workspace gate after live alignment if shared registry/runtime changed.

## Implementation Sequence Proposal

1. Phase 5C.0 native verification gate
   - Reconfirm Supplier Quotation required fields and site permissions.
   - Reconfirm no RFQ mapping from draft managed RFQ.
2. Phase 5C.1 backend contract
   - Add `managed_supplier_quotation.py`.
   - Add Python tests for state, permissions, draft save, forbidden actions.
3. Phase 5C.2 frontend managed form
   - Add managed route/page/controller using Phase 5A/5B visual contract.
   - Implement supplier/item/warehouse autocomplete overlays.
   - Implement rate/amount and UOM display behavior.
4. Phase 5C.3 navigation/governance
   - Move Overview and Supplier Quotation Directory create action to managed route.
   - Update governance manifest and route registry.
5. Phase 5C.4 smoke and protection
   - Add focused Phase 5C smoke.
   - Run source validation, Sales freeze, and protected workspace gates.
6. Phase 5C.5 commit, push, controlled live alignment
   - Live-align only after all source gates pass.
   - Run focused live smoke and post-live protected gate.

## Risks And Open Questions

- Current live Supplier Quotations are submitted and RFQ-linked. Direct managed drafts may appear in comparison by item/supplier/date but will not have RFQ references unless later created through native RFQ mapping.
- ERPNext Supplier Quotation `base_rate` and `base_amount` are required child fields. Backend implementation should rely on ERPNext item/default and totals methods, not frontend arithmetic alone.
- Currency/conversion handling must be verified carefully. If the site later uses multi-currency supplier quotes, Phase 5C may need a compact currency selector or locked context display.
- The existing governance manifest may still describe `new_rfq` as a native action in one line; Phase 5C implementation should review and align manifest wording for all managed buying forms without changing accepted runtime behavior.
- Supplier portal/email response capture remains a separate product decision.
- RFQ-to-Supplier Quotation conversion should wait until an RFQ submit/review step is productized and accepted.
