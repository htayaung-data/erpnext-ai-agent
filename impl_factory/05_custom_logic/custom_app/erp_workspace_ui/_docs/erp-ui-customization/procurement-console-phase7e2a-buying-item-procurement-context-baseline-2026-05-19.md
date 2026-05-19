# Procurement Console Phase 7E2A Buying Item Procurement Context Baseline

Date: 2026-05-19

Protected baseline commit: `2ae32e891b491fa5af71cc4863e6b68e1754ee49`

Design commit: `3c07fae2b9da57e673d8cf2929ea9772c922dc8d`

Status: protected and owner-accepted after manual visual review.

## 1. Executive Summary

Phase 7E2A is the protected baseline for Productized Buying Item Procurement Context inside Procurement Console.

It adds app-owned buying context for items without reopening raw ERPNext Item forms. Purchase Managers can maintain a narrow procurement context profile from the productized Buying Item Detail page. Purchase Users can view the same context read-only.

The implementation uses companion app-owned records and an immutable buying log. It does not write to ERPNext Item master data, Item Supplier, Item Price, Item Defaults, Default Supplier, or supplier master data.

The final accepted visual repair commit also added consistent component padding to both Supplier Buying Profile and Buying Procurement Context so card titles, helper text, action buttons, and field boxes no longer touch component borders.

## 2. Implemented Capability

### Buying Item Directory

The Buying Item Directory includes a read-only readiness column/chip for each item.

Protected behavior:

- Shows item readiness context without allowing inline edit.
- Preserves Phase 7F search semantics.
- Does not add a readiness filter in this phase.
- Does not expose native Item form links or raw ERPNext routes.

Readiness status values:

- `Not reviewed`
- `Ready for buying`
- `Needs sourcing review`
- `Hold for sourcing`

### Buying Item Detail

The Buying Item Detail page includes a `Buying Procurement Context` card.

Purchase Manager behavior:

- Can open `Edit Context` from the detail page.
- Can save only the allowlisted app-owned context fields.
- Sees updated read-only context after save.
- Sees a business-readable `Last Updated` value with no raw microseconds.

Purchase User behavior:

- Sees the same card read-only.
- Does not see edit/save controls.
- Does not see native Item escape actions.

Editable fields protected in this baseline:

- `buying_readiness_status`
- `preferred_existing_supplier`
- `supplier_part_no_context`
- `procurement_lead_time_days`
- `minimum_order_qty_context`
- `buying_note`
- `readiness_note`

Validation bounds:

- `procurement_lead_time_days`: blank or integer from `0` to `365`.
- `minimum_order_qty_context`: blank or positive number up to `1,000,000`.
- `preferred_existing_supplier`: existing Supplier only; context-only.
- `supplier_part_no_context`: context-only text; does not write ERPNext Item Supplier.

### Final Accepted Padding Polish

The final accepted repair commit `2ae32e891b491fa5af71cc4863e6b68e1754ee49` added outer component padding to:

- Supplier Buying Profile.
- Buying Procurement Context.

Protected visual rule:

```css
padding: 15px 18px 18px;
box-sizing: border-box;
```

This padding is part of the protected baseline. Future edits must not regress the spacing so section headings, helper copy, action buttons, and inner field boxes touch the card border.

## 3. Protected Role Contract

### Purchase Manager

Purchase Manager can edit only the app-owned Buying Item Procurement Context fields listed above.

Purchase Manager cannot use Procurement Console to access the raw ERPNext Item form, mutate Item master data, mutate Item Supplier, mutate Item Price, mutate Item Defaults, mutate Default Supplier, or change stock/accounting/UOM/valuation records.

### Purchase User

Purchase User can view Buying Item Procurement Context only.

Purchase User cannot edit, save, or access native Item form escape actions from Procurement Console.

### Directory Edit Rule

There is no directory-level edit action in this baseline. Editing is available only from Buying Item Detail for Purchase Manager.

## 4. Data And Audit Contract

Phase 7E2A uses companion app-owned DocTypes:

- `Procurement Item Buying Profile`
- `Procurement Item Buying Log`

Profile contract:

- One profile per Item.
- Keyed by existing ERPNext Item.
- Stores only app-owned procurement context fields.
- Does not duplicate or replace ERPNext Item master ownership.

Log contract:

- Immutable append-only log for successful profile changes.
- Records before/after values, changed fields, changed user, and changed timestamp.
- Normal users must not edit/delete log records.

API and validation contract:

- Save API is allowlisted.
- Unknown or disallowed payload keys are rejected.
- Server-side role and permission checks are required.
- Errors must be controlled/productized and must not expose raw tracebacks or framework permission modals.

Forbidden writes from this feature:

- ERPNext `Item`
- ERPNext `Item Supplier`
- ERPNext `Item Price`
- ERPNext `Item Default`
- ERPNext `Supplier`
- ERPNext `Contact`
- ERPNext `User`
- ERPNext `Communication`
- ERPNext `Email Queue`
- ERPNext `Purchase Receipt`
- ERPNext `Purchase Invoice`
- ERPNext `Payment Entry`
- stock, accounting, warehouse, valuation, UOM, tax, serial, batch, variant, or reorder records

## 5. UX Contract

Buying Item Detail must present Buying Procurement Context as a productized Procurement Console card, not a raw ERPNext form fragment.

Protected UX rules:

- Card appears on Buying Item Detail.
- Directory shows read-only readiness chip/column.
- Purchase Manager gets `Edit Context` on detail only.
- Purchase User sees a read-only card with no edit/save controls.
- Validation is inline/productized.
- `Last Updated` is business-readable and must not show raw database microseconds.
- No raw Frappe permission dialogs.
- No native route names or native form labels.
- No `/desk/Form/Item`, `/app/item`, or `frappe.set_route("Form", "Item", ...)` normal-role path.
- Shared component visual style is required.
- Accepted card padding is protected: `padding: 15px 18px 18px; box-sizing: border-box;`.

## 6. Validation Evidence

Accepted validation results:

- `python3 -m compileall erp_workspace_ui` passed.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'` passed with 206 tests.
- `node --check` for touched JavaScript passed.
- `git diff --check HEAD` passed.
- Static native escape scan was clean.
- Static send-removal scan was clean.
- Focused Supplier readiness smoke passed.
- Focused Buying Item context smoke passed.
- Full protected workspace gate passed.
- Sales freeze inside protected gate passed.
- Owner manual visual review accepted the final padding repair.

Protected workspace gate:

- `/tmp/protected-workspaces-context-padding-rerun-20260519T112207Z`

Sales freeze inside protected gate:

- `/tmp/protected-workspaces-context-padding-rerun-20260519T112207Z/sales-freeze-protection`

## 7. Artifact Paths

Focused Supplier readiness smoke:

- `/tmp/procurement-context-padding-supplier-live-20260519T110624Z/procurement-phase7e1a`

Focused Buying Item context smoke:

- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/artifacts/procurement-phase7e2a`

Phase 7E2A focused summary:

- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/artifacts/procurement-phase7e2a/phase7e2a-summary.json`

Final protected workspace gate:

- `/tmp/protected-workspaces-context-padding-rerun-20260519T112207Z`

Sales freeze inside protected gate:

- `/tmp/protected-workspaces-context-padding-rerun-20260519T112207Z/sales-freeze-protection`

Source/live hashes for final accepted padding repair:

- `erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js`
  - `fd95d0d87f184cc6a36e9c8fa99b21e865901354c85ab77a3401aa09c257f64d`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_item_page.js`
  - `ba6441c2c89f4d9fb42b6c3f4a0f97fa281d4bca7136658d9d9ff52d983332df`

## 8. Manual Verification Checklist

### Purchase Manager

1. Open Procurement Console.
2. Open Buying Items Directory.
3. Confirm readiness chip/column is visible.
4. Open a Buying Item Detail page.
5. Confirm `Buying Procurement Context` card has clean padding and field boxes do not touch the component border.
6. Click `Edit Context`.
7. Confirm only these fields are editable:
   - Buying readiness
   - Preferred supplier
   - Supplier part reference
   - Lead time days
   - Minimum order quantity
   - Buying note
   - Readiness note
8. Save context.
9. Confirm `Last Updated` renders as business-readable date/time without microseconds.
10. Confirm no `Open ERP Item Form`, native form escape, `/desk/Form/Item`, or `/app/item` path is available.

### Purchase User

1. Open the same Buying Item Detail page.
2. Confirm `Buying Procurement Context` is read-only.
3. Confirm there is no `Edit Context` or save control.
4. Confirm there is no native Item escape.

### Supplier Detail

1. Open Supplier Detail.
2. Confirm `Supplier Buying Profile` padding remains clean.
3. Confirm inner field boxes do not touch left or right card borders.

### RFQ Review

1. Open RFQ Review.
2. Confirm Supplier Communication remains preview/PDF/readiness only.
3. Confirm `Send RFQ` remains disabled/non-actionable.
4. Confirm no native email/print leakage appears.

## 9. Forbidden And Deferred Scope

The following remain not implemented and forbidden in this baseline:

- Native ERPNext Item form escape.
- Item creation, deletion, disable, or broad Item mutation.
- Item Supplier mutation.
- Item Price creation, update, or delete.
- Item Default or Default Supplier mutation.
- Supplier creation or Supplier master editing.
- Contact creation/editing.
- User creation or supplier portal activation.
- RFQ send/email/SMTP.
- Communication or Email Queue creation.
- Submit, approval, reject, cancel, or conversion lifecycle actions.
- Purchase Receipt, Purchase Invoice, Payment, receiving, billing, or payment work.
- Stock, accounting, UOM, stock UOM, valuation, reorder, warehouse, tax, serial/batch, or variant changes.
- AI intake.
- Sales runtime changes.

## 10. Next Recommended Phase

Next recommended task is design only:

`Phase 7E3 - Manager Review/Action Readiness Design`

Purpose:

- Determine what manager review/action readiness should exist after Supplier Buying Profile and Buying Item Procurement Context are protected.
- Define future manager workflows without adding lifecycle mutation until separately governed.
- Keep submit, approval, conversion, RFQ send/email, PO commitment, receiving, billing, payment, Item Price, Default Supplier, and master-data mutation out of scope until owner-approved designs exist.

Do not implement Phase 7E3 from this baseline closure task.
