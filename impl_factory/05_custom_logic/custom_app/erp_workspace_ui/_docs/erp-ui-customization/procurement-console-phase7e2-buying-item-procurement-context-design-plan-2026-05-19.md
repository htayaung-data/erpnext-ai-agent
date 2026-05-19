# Procurement Console Phase 7E2 Buying Item Procurement Context Design Plan

Date: 2026-05-19

Branch: `feature/erpnext-ui-design`

Scope: docs-only design and research. No runtime Python, JavaScript, CSS, smoke script, DocType, migration, Sales Console, live alignment, native escape, RFQ send/email, submit/approval, conversion, receiving, billing, payment, Item Price, Default Supplier, Supplier/Contact/User/portal, or AI intake implementation is included.

## Executive Recommendation

Phase 7E2 should add a productized Buying Item Procurement Context capability as the controlled replacement for any remaining need to open the raw ERPNext Item form from Procurement Console.

The recommended architecture is a companion custom app record, tentatively named `Procurement Item Buying Profile`, keyed by Item, plus an immutable `Procurement Item Buying Log`. The profile stores buyer-maintained context only. It must not write to ERPNext `Item`, `Item Supplier`, `Item Price`, `Item Default`, `Supplier`, `Warehouse`, `UOM`, stock, accounting, tax, valuation, or lifecycle records.

Purchase Users remain read-only. Purchase Managers may edit only allowlisted buying context fields: `buying_readiness_status`, `preferred_existing_supplier`, `supplier_part_no_context`, `procurement_lead_time_days`, `minimum_order_qty_context`, `buying_note`, and `readiness_note`. These fields are procurement context, not ERP master data and not sourcing automation. `preferred_existing_supplier` is a context pointer only; it must not mutate ERPNext Default Supplier, Item Default, Item Supplier, Item Price, or PO supplier selection.

Phase 7E2A, if approved for implementation, should deliver the companion profile, log, Buying Item Detail card, optional directory readiness chip, backend allowlisted save API, and tests/smokes. It should not introduce price maintenance, default supplier mutation, Item Supplier editing, RFQ send, conversions, or lifecycle actions.

## Current System Findings

### Baseline Constraints

- Phase 7D1 removed normal-role native ERP form escapes from Procurement Console. Purchase Users and Purchase Managers must not see `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, or `Advanced ERP Form` in normal Procurement workflows.
- Phase 7E1A introduced Supplier Buying Readiness with companion app records and audit logging. That pattern is the closest precedent for item buying context.
- Phase 6C2A protects RFQ Supplier Communication as preview/PDF/readiness only. `Send RFQ` remains visible but disabled.
- Phase 6C2C corrected history by removing attempted test-send runtime. Current protected state must have no SMTP send endpoint or email-provider dependency.
- Phase 7G Quick Find is deferred. This phase continues the Purchase Manager capability roadmap rather than adding cross-workspace search.
- Sales Console is frozen/protected. Any future runtime implementation must pass Sales freeze and the full protected workspace gate.

### Current Buying Item Directory

`erp_workspace_ui/procurement_console/items.py` exposes a productized Buying Item Directory. It filters purchase-enabled Items, searches item code/name/group/brand, and routes rows to `procurement-console-item`. It does not create, edit, delete, disable, or mutate Items.

### Current Buying Item Detail

`get_item_detail_context` returns a read-only procurement detail page with:

- Item identity, item group, stock UOM, purchase-enabled status, and disabled status.
- Approved suppliers from ERPNext `Item Supplier` child rows.
- Supplier price review from read-only `Item Price` records.
- Recent Supplier Quotations.
- Open Purchase Orders.
- Productized Back and Refresh actions.

The current detail page has no native Item form escape and no edit action. The frontend page `procurement_console_item_page.js` renders a productized child-page shell and productized cards only.

### Missing Manager Capability

After native escape closure, Purchase Managers can inspect item purchasing context but cannot capture buyer-owned sourcing readiness, notes, preferred existing supplier context, supplier part number context, lead time assumptions, or MOQ context without using raw ERPNext master forms. That is the gap Phase 7E2 should fill.

The gap should not be solved by granting raw Item form access. The ERPNext Item master contains stock, accounting, valuation, warehouse, UOM, tax, variant, serial/batch, price, website, and default fields that are broader than procurement readiness.

## ERPNext And Frappe Data Model Findings

Installed ERPNext/Frappe metadata was inspected in the backend container for `Item`, `Item Supplier`, `Item Price`, `Item Default`, `Supplier`, and `UOM`.

### Item

Installed `Item` metadata has `track_changes = 1` and belongs to the Stock module. Relevant fields include:

- Identity and grouping: `item_code`, `item_name`, `item_group`, `brand`.
- Status and type: `disabled`, `is_stock_item`, `is_purchase_item`, `is_sales_item`, `end_of_life`.
- Units: `stock_uom`, `purchase_uom`.
- Valuation/accounting-adjacent data: `valuation_rate`, `valuation_method`, `item_defaults`.
- Stock and planning data: `reorder_levels`, `safety_stock`, `lead_time_days`, `min_order_qty`.
- Traceability/configuration: `has_serial_no`, `has_batch_no`, `has_variants`, `variant_of`.
- Buying/supplier child data: `supplier_items` table with `Item Supplier`.
- Tax and quality data: `taxes`, inspection-required flags.

ERPNext Item documentation also notes that Supplier Codes track item codes defined by suppliers and that selecting an item in purchase transactions can fetch the supplier part number. It also notes that entering a standard selling rate during Item creation can create an Item Price. Source: <https://docs.frappe.io/erpnext/item>.

Design implication: the native Item form is too broad for normal Procurement Console editing. Phase 7E2 must avoid Item mutation entirely.

### Item Supplier

Installed `Item Supplier` is a child table with `track_changes = 1`. It contains `supplier` and `supplier_part_no` in the installed metadata. It is embedded in Item and therefore normally edited through the broader Item master.

Design implication: Item Supplier data is buyer-relevant, but direct editing in Phase 7E2A would still mutate ERPNext Item child-table master data. It should remain read-only in the first implementation. A later phase may design a narrowly governed Item Supplier update if owner approves the extra risk.

### Item Price And Price Lists

Installed `Item Price` has `track_changes = 1` and includes item, UOM, price list, supplier/customer-specific applicability, currency, rate, validity, lead time, note, and reference fields. ERPNext documentation states that Item Price records track selling and buying rates, can be supplier-specific, can have validity dates, and affect transaction price fetching. Source: <https://docs.frappe.io/erpnext/item-price>. ERPNext Price Lists documentation states that buying and selling prices are stored separately in Item Prices. Source: <https://docs.frappe.io/erpnext/price-lists>.

Design implication: Item Price mutation is commercial pricing governance, not readiness context. It must remain forbidden in Phase 7E2.

### Item Default

Installed `Item Default` is a child table with company-specific defaults such as `default_warehouse`, `default_price_list`, `default_supplier`, cost centers, expense accounts, income accounts, inventory accounts, and other accounting defaults.

Design implication: Default Supplier and item defaults can affect future purchase, stock, and accounting behavior. They must remain admin-owned and out of scope.

### Permissions Observed

The installed site showed Purchase Manager has read permission for Item but not write/create. Purchase User does not have direct Item read through native permission checks, though the productized Procurement backend can provide controlled read context. Sales Manager had Item Price write/create in the installed role setup, which reinforces that ERPNext native permissions are broad and not aligned with Procurement Console product contracts.

Design implication: Phase 7E2 must use server-owned procurement APIs with explicit role checks and payload allowlists, not native form permission assumptions.

## Industry ERP Findings

### ERPNext

ERPNext treats Item as a core master record across stock, buying, selling, accounting, manufacturing, webshop, and quality workflows. Supplier codes, supplier part numbers, Item Prices, Price Lists, Item Defaults, and stock/UOM settings are connected to transaction behavior. This supports a strict separation between read-only ERPNext master context and productized procurement notes/readiness.

Sources: <https://docs.frappe.io/erpnext/item>, <https://docs.frappe.io/erpnext/item-price>, <https://docs.frappe.io/erpnext/price-lists>.

### SAP S/4HANA

SAP separates material master data from purchasing info records and source lists. SAP purchasing info records contain supplier-material purchasing information such as prices, conditions, planned delivery time, vendor evaluation data, and regular-vendor indicators. SAP Manage Purchasing Info Records allows searching and maintaining info records by material, supplier, plant, purchasing organization, and conditions. SAP source lists manage possible sources of supply for purchase requisitions and purchase orders and can mark sources as fixed or blocked.

Sources: <https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/49e387576b49ab76e10000000a441470.html>, <https://help.sap.com/docs/SAP_ERP/967e1c2a6a8c4183b7e07d28e7574445/4b7fb65334e6b54ce10000000a174cb4.html>, <https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/49fb9b57aba49f2de10000000a44147b.html>.

Project implication: mature ERP systems isolate supplier-item purchasing context from the entire material master. Our companion profile follows that separation without prematurely implementing full source-list or info-record mutation.

### Oracle Fusion Procurement

Oracle uses Approved Supplier Lists to authorize or restrict suppliers for items/categories and maintain supplier-item ordering attributes by procurement business unit or ship-to organization. Oracle ASL entries can include ordering requirements such as minimum order amount, references to source agreements, review dates, statuses, supplier item attributes, purchasing UOM, and minimum order quantity.

Sources: <https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/approved-supplier-list.html>, <https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42846.htm>.

Project implication: readiness/status, review cadence, supplier/item context, MOQ, and purchasing UOM are procurement concepts, but they are governed by role and business unit. Phase 7E2 should capture readiness context first and defer authoritative ASL/default sourcing behavior.

### Microsoft Dynamics 365 Supply Chain Management

Dynamics 365 supports approved vendors for specific products. The Microsoft task flow starts from released products, records primary vendor context, adds approved vendor lines with effective periods, sets policy for non-approved vendors on purchase order lines, and provides overview pages by item and by vendor.

Source: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/tasks/approve-vendors-specific-products>.

Project implication: product/vendor eligibility is a governed procurement concept. Phase 7E2 can model readiness and preferred-supplier context without immediately enforcing PO sourcing policy.

### Odoo Purchase

Odoo vendor pricelists can be maintained on products or imported. Vendor price data can auto-populate RFQs and POs. Odoo fields include vendor, vendor price, minimum quantity, unit price, delivery lead time, and vendor sequencing. Odoo purchase lead-time documentation states that vendor lead time helps calculate PO deadlines and receipt dates.

Sources: <https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/products/pricelist.html>, <https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/lead_times.html>.

Project implication: vendor item numbers, MOQ, lead time, and supplier preference are normal buyer concerns. They should be productized carefully because price and lead-time fields can drive operational dates and costs in mature systems.

## Architecture Options

| Option | Description | Business fit | Safety | ERPNext compatibility | Auditability | Complexity | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A. Companion Procurement Item Buying Profile plus immutable log | Store buyer-maintained item readiness/context in app-owned records keyed by Item. ERPNext Item, Item Supplier, Item Price, and Item Default remain read-only. | Strong fit for current gap. Gives managers a safe place for sourcing readiness without master mutation. | High. Payload allowlist prevents broad writes. | Strong. Does not fight ERPNext master model. | High with custom log plus Version on profile. | Moderate; requires two DocTypes and API/UI. | Recommended for Phase 7E2A. |
| B. Controlled editing of ERPNext Item Supplier only | Let Purchase Manager update Item Supplier child rows through a productized UI. | Useful later for supplier part numbers and supplier associations. | Medium/low for first slice because it mutates Item child-table master data. | Native-compatible but requires careful Item save/version behavior and permissions. | Medium; Item Version may record changes but business reason would need custom logging. | Higher; child-table update and conflict handling. | Defer to separate phase after owner approves master-data mutation. |
| C. Hybrid profile with read-only ERPNext Item and Item Supplier context | Show ERPNext Item and Item Supplier read-only, store only notes/status in companion profile. | Strong as a first step but too narrow if no preferred supplier/lead-time context is editable. | Very high. | Strong. | High. | Low/moderate. | Use as the implementation shape inside Option A: read-only native context plus companion editable fields. |

Final recommendation: implement Option A using the safer Option C interaction model. The companion profile is the only write target. ERPNext Item, Item Supplier, Item Price, and Item Default remain read-only sources.

## Product Contract

### Purchase Manager Can View

- Item identity: item code, item name, item group, brand, stock UOM, purchase UOM when available, purchase-enabled status, disabled/end-of-life status.
- Read-only approved supplier context from `Item Supplier`.
- Read-only recent Item Price buying context, clearly labeled as read-only price history/review.
- Recent Supplier Quotations and open Purchase Orders already shown by the current item detail page.
- Procurement Item Buying Profile fields and latest audit summary.

### Purchase Manager Can Edit

Only the companion profile fields below:

| Field | Type | Purpose | Validation | ERPNext mutation? |
| --- | --- | --- | --- | --- |
| `buying_readiness_status` | Select | Buyer-facing item readiness. | Allowed values: `Ready`, `Needs supplier`, `Needs price review`, `Needs specification review`, `Hold for sourcing`. | No. |
| `preferred_existing_supplier` | Link to existing Supplier | Contextual preferred supplier for buyer review. | Supplier must exist and not be disabled. It is not Default Supplier. | No. |
| `supplier_part_no_context` | Data | Context-only supplier part number or buying reference. | Max length, printable text only. Does not write Item Supplier. | No. |
| `procurement_lead_time_days` | Int | Context-only expected buying lead time. | Optional; integer 0-730 unless owner chooses stricter limit. | No. |
| `minimum_order_qty_context` | Float | Context-only MOQ note for buyer planning. | Optional; positive number. Does not write Item Price or UOM rules. | No. |
| `buying_note` | Small Text | Internal buyer note. | Max length and plain text. | No. |
| `readiness_note` | Small Text | Required explanation for non-ready/hold statuses. | Required when status is not `Ready`. | No. |

### Purchase User Can View

Purchase User sees the same Buying Item Detail context and the profile card in read-only mode. They cannot open edit mode, save profile fields, or see native ERP links.

### Purchase User Cannot Edit

- Procurement Item Buying Profile.
- Item Supplier.
- Item Price.
- Item Default.
- Item master fields.
- Supplier, Contact, User, portal, or downstream lifecycle records.

### Admin-Owned Or Separately Governed

- Item creation, deletion, disabled flag, item group, brand, stock UOM, purchase UOM, valuation, taxes, default warehouses, accounts, cost centers, reorder levels, stock settings, serial/batch, variants, website fields, and inspection controls.
- Item Price creation/update/delete.
- Default Supplier and Item Default mutation.
- ERPNext Item Supplier mutation.
- Supplier master, Contact/User/portal, RFQ send/email, submit/approve/convert/receive/bill/pay.

### Directory Behavior

Phase 7E2A should include a compact readiness chip on Buying Item Directory if it can be implemented with a bounded batch lookup. Recommended chip values: `Ready`, `Needs supplier`, `Needs price review`, `Needs specification review`, `Hold for sourcing`, and `Not reviewed` for no profile.

If the implementation cannot batch-read profiles without layout/performance risk, the chip may be deferred, but the design preference is to include it because it makes the manager capability discoverable.

### RFQ/SQ/PO Impact

Phase 7E2A should not change document generation, supplier selection, RFQ send readiness, pricing, or default supplier behavior. It may be read by future RFQ/SQ/PO helper UI as context, but the first implementation should only display item context on Buying Item Directory/Detail.

`Hold for sourcing` should be designed as an item-context warning for future document workflows. In Phase 7E2A, it should not block saved documents unless the owner separately approves item-readiness enforcement.

## Forbidden Field And Action Matrix

| Forbidden area | Examples | Why forbidden in Phase 7E2 |
| --- | --- | --- |
| Native Item form access | `Open ERP Item Form`, `/desk/Form/Item`, `/app/item` | Phase 7D1 closed native escapes for normal roles. |
| Item lifecycle/master data | create/delete/disable Item, item group, brand, stock UOM, purchase UOM, maintain stock, sales/purchase flags, end-of-life | Affects stock, sales, purchasing, reports, and master-data governance. |
| Valuation/accounting/tax | valuation rate/method, expense/income/inventory accounts, cost centers, tax rows | Finance/stock accounting ownership. |
| Item Price | buying/selling price, price list, supplier-specific price, validity, currency, UOM price | Price mutation affects transaction pricing and margin. Needs separate approval. |
| Default Supplier / Item Default | `default_supplier`, default warehouse, default price list, account defaults | Can drive future sourcing/accounting behavior. |
| Item Supplier mutation | add/remove supplier rows, supplier part no in ERP child table | Useful but still mutates Item master child data. Defer to a separate governed phase. |
| Supplier/Contact/User/Portal | supplier creation/editing, contact creation/editing, portal user creation | Covered by supplier readiness and RFQ send governance; no side effects here. |
| RFQ send/email/SMTP | Communication, Email Queue, provider setup, outgoing email | Deferred supplier-facing communication risk. |
| Submit/approval/conversion/lifecycle | submit, approve, RFQ-to-SQ, SQ-to-PO, PR-to-PO, receive, bill, pay | Separate workflow governance phases. |
| Reorder/warehouse/stock settings | reorder levels, warehouses, safety stock, serial/batch, variants | Warehouse/stock planning ownership. |
| AI intake | automatic extraction/mutation from documents | Future controlled feature only. |

## Role And Permission Matrix

| Capability | Purchase User | Purchase Manager | Procurement Admin/System Manager |
| --- | --- | --- | --- |
| View Buying Item Directory | Yes, through productized route | Yes | Yes |
| View Buying Item Detail | Yes, productized read-only | Yes | Yes |
| View read-only Item Supplier/Price/PO/SQ context | Yes where productized permissions allow | Yes | Yes |
| Edit Procurement Item Buying Profile | No | Yes | Optional through same API if assigned Procurement Admin role |
| View profile audit summary | Yes | Yes | Yes |
| Native Item form access inside Procurement Console | No | No | No in Phase 7E2; use ERPNext Desk outside console if needed |
| Edit ERPNext Item/Item Supplier/Item Price/Item Default | No | No | Outside Procurement Console only, according to ERPNext admin policy |
| RFQ send/email or document lifecycle | No | No in this phase | No in this phase |

## UI/UX Plan

### Buying Item Detail Card

Add a compact `Buying Procurement Context` card near the top of Buying Item Detail, after the item identity summary and before long historical sections.

Card content:

- Readiness chip.
- Preferred supplier context.
- Supplier part number context.
- Procurement lead time.
- Minimum order quantity context.
- Buying note.
- Readiness note.
- Last updated by and date formatted as business-readable text, for example `19 May 2026, 14:30`.

Purchase Manager sees an `Edit Context` action. Purchase User sees read-only content only.

### Edit Interaction

Use a productized compact modal or inline edit panel, not a raw ERPNext form. Fields should be grouped as:

- Readiness: status and readiness note.
- Supplier context: preferred existing supplier and supplier part number context.
- Planning context: lead time and MOQ context.
- Internal note: buying note.

Buttons:

- Primary: `Save Context`.
- Secondary: `Cancel`.

Validation errors should appear inline inside the productized panel. No Frappe permission dialogs, raw exceptions, native forms, or framework modals should leak to normal users.

### Directory Chip

If included, Buying Item Directory should show one concise readiness chip per item. It must not crowd the existing directory at 1136px. Preferred placement: near Status or in a compact `Readiness` column. Empty profile state should show `Not reviewed`, not an error.

### Responsive Expectations

- At 1136px, 1240px, and 1440px, cards must not overflow horizontally.
- Long notes and supplier names should wrap or truncate with accessible title text, depending on existing component conventions.
- No gradients, marketing-style cards, duplicate chrome, nested cards, or verbose instructional paragraphs.

## Backend/API/DocType Plan

### DocType: Procurement Item Buying Profile

Purpose: one mutable, app-owned profile per Item.

Recommended fields:

| Field | Type | Notes |
| --- | --- | --- |
| `item` | Link Item, unique, required | Key. Must be purchase-enabled or at least visible in Buying Item context. |
| `buying_readiness_status` | Select | `Ready`, `Needs supplier`, `Needs price review`, `Needs specification review`, `Hold for sourcing`. |
| `preferred_existing_supplier` | Link Supplier | Existing supplier only; context-only; not Default Supplier. |
| `supplier_part_no_context` | Data | Context-only; does not mutate Item Supplier. |
| `procurement_lead_time_days` | Int | Optional planning context. |
| `minimum_order_qty_context` | Float | Optional planning context, not Item Price/UOM rule. |
| `buying_note` | Small Text | Internal procurement note. |
| `readiness_note` | Small Text | Required for non-ready statuses. |
| `last_context_update_by` | Data/Link User or rely on owner/modified_by | For display if available. |

Set `track_changes = 1` so Frappe Version can record profile changes as secondary evidence.

### DocType: Procurement Item Buying Log

Purpose: immutable audit record for every profile save.

Recommended fields:

| Field | Type | Notes |
| --- | --- | --- |
| `item` | Link Item | Target item. |
| `changed_by` | Link User | User who saved. |
| `changed_at` | Datetime | Server timestamp. |
| `changed_fields` | JSON/Text | Field names changed. |
| `before_values` | JSON/Text | Sanitized before snapshot. |
| `after_values` | JSON/Text | Sanitized after snapshot. |
| `reason_note` | Small Text | Copy of readiness note or save note where applicable. |
| `source_route` | Data | Optional productized route/source marker. |

The log should be insert-only by backend API. Normal users should not edit or delete log rows.

### API Methods

Recommended whitelisted methods:

- `get_item_buying_profile(item)`
  - Input: item name/code.
  - Output: profile fields, read-only item summary, audit summary, can_edit boolean, allowed statuses.
  - Checks: authenticated Procurement user, item visible through productized Buying Item route.
  - Side effects: none.

- `save_item_buying_profile(item, payload)`
  - Input: item and allowlisted payload.
  - Output: updated profile context and audit summary.
  - Checks: Purchase Manager or explicit Procurement Admin role; server-side Item visibility; payload allowlist; unknown-key rejection.
  - Side effects: write only `Procurement Item Buying Profile` and insert `Procurement Item Buying Log`.

- `get_item_detail_context(item)` integration
  - Add read-only profile context and can_edit flag to existing Buying Item Detail payload.
  - Side effects: none.

- Directory integration
  - Batch-read profiles for visible item names and attach readiness chip data.
  - Side effects: none.

### Validation Rules

- Unknown payload keys are rejected.
- `buying_readiness_status` must be one of the allowed values.
- `readiness_note` is required for `Needs supplier`, `Needs price review`, `Needs specification review`, and `Hold for sourcing`.
- `preferred_existing_supplier` must exist, must be visible through controlled lookup, and must not be disabled.
- `supplier_part_no_context` must be bounded text.
- `procurement_lead_time_days` must be an integer in owner-approved range.
- `minimum_order_qty_context` must be positive if present.
- No client-provided business truth is accepted without server re-read.

### Failure Modes

Return productized errors:

- `Item not available in Buying Items.`
- `You can view this context but cannot edit it.`
- `Readiness note is required for this status.`
- `Preferred supplier is not available for buying context.`
- `This field is not editable in Procurement Console.`

Do not leak raw Frappe permission dialogs, tracebacks, or native route names.

## Audit And Governance Plan

Recommended audit approach: custom immutable `Procurement Item Buying Log` as primary evidence, with Frappe Version on the profile as secondary platform evidence.

Audit must capture:

- Item.
- Changed by.
- Changed at.
- Changed field names.
- Sanitized before values.
- Sanitized after values.
- Readiness note/reason.
- Source productized route where practical.

Forbidden attempts should be rejected and may be logged only if a future security audit policy requires it. Phase 7E2A does not need negative audit logging unless simple and low risk.

Governance manifest should classify:

- Buying Item Procurement Context view as productized allowed.
- Buying Item Procurement Context save as productized manager-only.
- Native Item form access, Item Price mutation, Default Supplier mutation, Item Supplier mutation, and lifecycle actions as forbidden/deferred.

## Test And Gate Plan

### Python Contract Tests

- Purchase Manager can read and save profile allowlisted fields.
- Purchase User can read but cannot save.
- Sales roles and Guest are denied.
- Unknown payload keys are rejected.
- Forbidden keys such as `item_group`, `stock_uom`, `default_supplier`, `price_list_rate`, `disabled`, `valuation_rate`, `default_warehouse`, and `supplier_items` are rejected.
- Preferred supplier must exist and must not be disabled.
- Invalid lead time/MOQ values are rejected.
- Readiness note is required for non-ready statuses.
- Save creates immutable log with before/after values.
- Item, Item Supplier, Item Price, Item Default, Supplier, Contact, User, Communication, Email Queue, and lifecycle records are not created or mutated.
- Buying Item Detail context includes profile and can_edit flag.
- Buying Item Directory readiness chip maps profile values if implemented.
- Native escape labels remain absent.
- RFQ send/email/SMTP symbols remain absent.

### Smoke Tests For Implementation Phase

Focused Phase 7E2 smoke should cover Purchase Manager and Purchase User:

- Buying Item Directory loads and readiness chip appears if implemented.
- Buying Item Detail shows Buying Procurement Context.
- Purchase Manager opens edit panel, saves allowlisted fields, sees updated chip/summary and last-updated text.
- Purchase User sees read-only panel and no edit/save controls.
- Forbidden fields are not present.
- No native labels: `Open ERP Form`, `Open ERP Item Form`, `Advanced ERP Form`.
- No raw navigation to `/desk/Form/`, `/app/`, or route array beginning with `Form`.
- No native email/send/print/lifecycle controls.
- Layout is clean at 1136px, 1240px, and 1440px.
- No framework permission modal or Internal Server Error modal.

### Gates

Implementation phase must run:

- `python3 -m compileall erp_workspace_ui`.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`.
- `node --check` for touched JS/smoke files.
- `git diff --check HEAD`.
- Static native escape scan.
- Static send-removal scan.
- Focused Phase 7E2 smoke.
- Sales freeze protection.
- Full protected workspace gate.
- Controlled live alignment with source/live hash verification.
- Focused live Phase 7E2 smoke and post-live protected gate.
- Owner manual review before baseline closure.

## Deferred Scope

- Native Item form access inside Procurement Console.
- Item creation, deletion, disable, item group, brand, stock UOM, purchase UOM, valuation, accounting, tax, stock, reorder, variant, serial/batch, website, and quality fields.
- ERPNext Item Supplier mutation.
- Item Price and Price List mutation.
- Default Supplier and Item Default mutation.
- Supplier creation/editing, Contact/User creation, supplier portal activation.
- RFQ send/email/SMTP, Communication, Email Queue.
- Submit/approval/conversion, receiving, billing, payment.
- Automatic PO/RFQ supplier selection from preferred supplier context.
- AI intake or automatic profile population from supplier documents.

## Owner Decisions Needed Before Implementation

1. Confirm the allowed status list: recommended `Ready`, `Needs supplier`, `Needs price review`, `Needs specification review`, `Hold for sourcing`.
2. Confirm whether `preferred_existing_supplier` is allowed as context-only in Phase 7E2A.
3. Confirm whether `supplier_part_no_context` should be context-only now or deferred until controlled Item Supplier editing is designed.
4. Confirm numeric bounds for `procurement_lead_time_days` and `minimum_order_qty_context`.
5. Confirm whether Buying Item Directory should show a readiness chip in the first implementation.
6. Confirm whether `Hold for sourcing` is display-only in Phase 7E2A or should block future document creation in a later phase.
7. Confirm whether a separate later phase should design controlled ERPNext Item Supplier updates.

## Recommended Implementation Sequence

### Phase 7E2A: Companion Profile And Detail UI

Scope:

- Add `Procurement Item Buying Profile` and `Procurement Item Buying Log` DocTypes.
- Add backend read/save APIs with strict role gates and payload allowlist.
- Add Buying Procurement Context card to Buying Item Detail.
- Add optional Buying Item Directory readiness chip through bounded batch lookup.
- Add tests, smoke, Sales freeze, protected gate, controlled live alignment, and manual review.

Exclusions:

- ERPNext Item/Item Supplier/Item Price/Item Default mutation.
- RFQ/SQ/PO lifecycle changes.
- Native ERP escape.

### Phase 7E2B: Item Context Consumption In Procurement Documents

Design only first. Decide whether managed PR/RFQ/SQ/PO item selectors should show item readiness warnings, lead-time hints, or preferred supplier context. Do not auto-select suppliers or block documents without owner-approved policy.

### Phase 7E2C: Controlled Item Supplier Update Design

Design whether Purchase Manager may update ERPNext Item Supplier rows through a productized audited action. This phase must separately address conflict handling, ERPNext Item Version behavior, Supplier permissions, and master-data ownership.

### Phase 7E2D: Pricing Governance Design

Separate design for Item Price, price lists, validity, supplier-specific pricing, approval, and audit. This is intentionally not part of 7E2A.

## References

- ERPNext Item documentation: <https://docs.frappe.io/erpnext/item>
- ERPNext Item Price documentation: <https://docs.frappe.io/erpnext/item-price>
- ERPNext Price Lists documentation: <https://docs.frappe.io/erpnext/price-lists>
- SAP Manage Purchasing Info Records: <https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/49e387576b49ab76e10000000a441470.html>
- SAP Purchasing Info Record definition: <https://help.sap.com/docs/SAP_ERP/967e1c2a6a8c4183b7e07d28e7574445/4b7fb65334e6b54ce10000000a174cb4.html>
- SAP Manage Source Lists: <https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/49fb9b57aba49f2de10000000a44147b.html>
- Oracle Approved Supplier List: <https://docs.oracle.com/en/cloud/saas/procurement/25d/oaprc/approved-supplier-list.html>
- Oracle Redwood Manage Approved Supplier Lists readiness note: <https://docs.oracle.com/en/cloud/saas/readiness/scm/26b/proc26b/26B-procurement-wn-f42846.htm>
- Microsoft Dynamics 365 approved vendors for specific products: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/tasks/approve-vendors-specific-products>
- Odoo vendor pricelist documentation: <https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/products/pricelist.html>
- Odoo purchase lead times documentation: <https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/lead_times.html>
