# Procurement Console Phase 7J2B Supplier And Buying Item Tab Simplification Review

Date: 2026-05-24
Branch: `feature/erpnext-ui-design`
Baseline reviewed: Phase 7J2A protected alignment commit `eb30c721e2642310cd814222f11b295250d529ed`
Scope: docs-only business and UX review. No runtime implementation is included.

## Executive Summary

Phase 7J2A is accepted and should not be treated as broken. It successfully moved Supplier Detail and Buying Item Detail away from long vertical stacks and into productized object-style tabs. The remaining issue is second-order information architecture: the new tab model still repeats counts, readiness, and related activity in several places.

Recommendation: simplify both pages around a `Profile` default tab and remove tabs that do not represent a distinct business object or decision. Supplier Detail should become `Profile`, `Orders`, `RFQs`, and `Quotations`. Buying Item Detail should become `Profile`, `Suppliers & Prices`, `Orders` or `Demand & Orders`, and `Quotation History`. The standalone `Activity`, `Readiness Guidance`, and `References` tabs should be removed or merged into `Profile`.

This is a design recommendation only. It must not introduce native ERPNext escape, send/email, lifecycle actions, master-data mutation, Item Price mutation, Default Supplier mutation, Item Supplier mutation, Contact/User/portal creation, Quick Find, Sales runtime changes, or live alignment.

## Evidence Reviewed

Project evidence:

- `_docs/erp-ui-customization/README.md`
- `_docs/erp-ui-customization/procurement-console-phase7j2-supplier-item-detail-tabs-design-plan-2026-05-23.md`
- `_docs/erp-ui-customization/procurement-console-phase7j1d-readiness-review-polish-baseline-2026-05-23.md`
- Current source after Phase 7J2A protected alignment commit `eb30c721e2642310cd814222f11b295250d529ed`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_item_page.js`
- Phase 7J2A live smoke summary: `/tmp/procurement-phase7j2a-live-smoke-20260523T183714Z/procurement-phase7j2a-20260523T183717Z/phase7j2a-summary.json`
- Phase 7J2A screenshots for manager/user Supplier Detail and Buying Item Detail at 1136, 1240, and 1440 widths.

Industry/product references:

- ERPNext buying docs separate Supplier, Item, RFQ, Supplier Quotation, Purchase Order, Purchase Receipt, Purchase Invoice, Item Price, and Contact concepts.
- SAP Fiori object page guidance supports a strong object header plus sections/tabs for major facets, with tabs representing sections of the object rather than duplicate summaries.
- Oracle Procurement models Supplier as a global entity with addresses, sites, contacts, tax, bank, and controls, reinforcing that buying profile edits must stay narrow and governed.
- Microsoft Dynamics 365 procurement separates vendor records, approved vendor/product information, RFQs, purchase orders, receipt, invoicing, and vendor collaboration.
- Odoo Purchase separates vendor/product setup, RFQ/email behavior, purchase order confirmation, and reporting dashboards.

## Current Duplication Analysis

### Supplier Detail In Phase 7J2A

Current tabs:

1. `Activity`
2. `Readiness Guidance`
3. `Orders`
4. `RFQs`
5. `Quotations`
6. `References`

Observed duplication:

| Current element | Duplicates or confuses | Recommendation |
| --- | --- | --- |
| Header facts: `Open POs`, `RFQs`, `Quotations` | Below-header badges `12 open orders`, `12 RFQs`. | Remove below-header count badges. Keep counts in header only. |
| Below-header `Reviewed for buying` badge | Header readiness/status chips already communicate readiness. | Remove when clear; show one compact issue banner only when warning/critical. |
| `Activity` tab | Repeats Orders and Quotations content that also appears in dedicated tabs. | Remove `Activity` until a true chronological timeline exists. |
| `References` tab | Contains the Supplier Buying Profile and contacts, which are primary profile data, not secondary references. | Rename/merge into `Profile`. |
| `Readiness Guidance` tab | Separates readiness from the profile fields that managers must edit to resolve it. | Merge readiness guidance into `Profile`. |
| Open POs and recent POs | Same orders can appear in both open and recent sections. | In `Orders`, either de-duplicate or label sections clearly and exclude open rows from recent when possible. |

Operational interpretation: `Activity` is not currently a real activity timeline. It is an aggregate tab that duplicates distinct objects. Mature ERP pages usually expose distinct facets such as profile, orders, RFQs, and quotations rather than an aggregate tab plus the same object-specific tabs.

### Buying Item Detail In Phase 7J2A

Current tabs:

1. `Suppliers & Prices`
2. `Readiness Guidance`
3. `Demand & Orders`
4. `Quotation History`
5. `References`

Observed duplication:

| Current element | Duplicates or confuses | Recommendation |
| --- | --- | --- |
| Header facts: suppliers and recent prices | Below-header badges `0 suppliers`, `0 price references`. | Remove below-header count badges. Keep counts in header only. |
| Default tab `Suppliers & Prices` | Opens to empty supplier/price tables for items without evidence, while the item buying context is hidden in `References`. | Default to `Profile`. |
| `References` tab | Contains Item Buying Context, which is the primary business profile. | Merge into `Profile`. |
| `Readiness Guidance` tab | Separates readiness from Item Buying Context fields that managers update. | Merge into `Profile`. |
| `Demand & Orders` label | Current source shows purchase orders; no visible demand/Purchase Request rows are included in the tab. | Use `Orders` now, or use `Demand & Orders` only if demand coverage is also shown. |

Operational interpretation: Item Detail should first explain the procurement posture of the item. Supplier/price evidence is important, but when there are zero supplier and price rows, making it the default tab feels like a data absence page rather than a buying profile.

## Answers To Owner Questions

| Question | Recommendation |
| --- | --- |
| Is removing Supplier `Activity` business-correct? | Yes. Current `Activity` is redundant because it repeats Orders and Quotations. Keep it only for a future true chronological timeline across POs, RFQs, quotations, communications, and profile changes. |
| Should Supplier Detail default to `Profile` instead of `Activity`? | Yes. `Profile` should be the default for both roles unless the route explicitly deep-links from an order/RFQ/quotation context. |
| Should Supplier `Readiness Guidance` and `References` merge into `Profile`? | Yes. Readiness, contacts, RFQ recipient evidence, and Supplier Buying Profile all belong to supplier profile comprehension. |
| Should Purchase Manager update controlled Supplier Buying Profile fields inside `Profile` when supplier is not ready? | Yes. The user should not switch tabs to understand or fix readiness. Manager-owned update controls belong next to the readiness issue. |
| Should below-header badges be removed or reduced? | Remove redundant count badges. Keep at most one meaningful readiness/status banner when warning/critical. Clear readiness should remain a header chip, not a second badge row. |
| For Buying Item Detail, should default tab be `Profile`, `Buying Context`, or `Suppliers & Prices`? | Use `Profile` as the tab label, with section title `Item Buying Context`. This is clearer than opening to empty supplier/price tables and keeps supplier/item pages consistent. |
| Should item `Readiness Guidance` and `References` merge into `Profile` / `Buying Context`? | Yes. Item Buying Context and readiness are one business conversation. |
| What labels best fit business users? | Use `Profile`, `Orders`, `RFQs`, `Quotations`, `Suppliers & Prices`, `Quotation History`, and `Readiness` as section text inside Profile. Avoid `References` for primary profile content. |
| Which tab structure best matches ERP industry patterns? | Distinct object facets: profile, orders, RFQs, quotations, suppliers/prices. Avoid aggregate tabs that duplicate object-specific tabs. |
| Which Phase 7J2A pieces should remain unchanged? | Keep the tab shell styling, productized routing, role-gated edit controls, row caps, `Show 12 recent`, business ownership labels, and no-forbidden-action governance. |

## Recommended Supplier Detail Final Tab Model

Final tabs:

1. `Profile`
2. `Orders`
3. `RFQs`
4. `Quotations`

Remove:

- `Activity`
- `References`
- Standalone `Readiness Guidance`

### Supplier Header

Keep the header focused on identity and key facts.

| Header element | Keep/change | Reason |
| --- | --- | --- |
| Supplier name and ID | Keep | Primary object identity. |
| Supplier group | Keep as meta under Supplier ID | Useful classification without adding a new badge. |
| Active/Disabled | Keep as header chip | Master status affects sourcing judgement. |
| Buying readiness | Keep as one header chip | Quick posture signal. |
| Open POs | Keep as fact | Manager/User need immediate order exposure. |
| RFQs | Keep as fact | Sourcing activity signal. |
| Quotations | Keep as fact | Offer history signal. |
| `Read-only` chip | Consider replacing with `Procurement view` or removing | It is less important than active/readiness state and can feel technical. |
| Below-header count badges | Remove | Duplicate header facts. |

If a supplier is not ready, show a single compact warning banner below the header and above tabs:

`Supplier needs readiness review. Update Supplier Buying Profile before new sourcing.`

Manager action: `Review profile`

User action: `View profile`

### Supplier `Profile` Tab

Purpose: answer whether this supplier can be used for buying coordination and what manager-owned profile data controls readiness.

Content:

1. Supplier Buying Profile card.
2. Readiness summary and issue list, compact by default.
3. Buying contacts and RFQ recipient evidence.
4. Permission/ownership explanation.
5. Manager edit form for allowed Supplier Buying Profile fields.

Manager behavior:

- If readiness is warning/critical, the top of `Profile` should show the issue and the controlled fields that can fix it.
- `Edit Profile` remains manager-only.
- Save continues to mutate only the app-owned Supplier Buying Profile / readiness profile and its log.
- No Supplier master, Contact, User, portal, RFQ send, or RFQ Supplier row mutation.

Purchase User behavior:

- Shows the same profile context read-only.
- Does not show edit/save controls.
- Uses copy such as `Managed by Purchase Manager` instead of disabled edit affordances.

### Supplier `Orders` Tab

Purpose: support order follow-up without warehouse or finance mutation.

Content:

1. Open or overdue purchase orders first.
2. Recent purchase orders second, but avoid repeating rows already shown as open when possible.
3. Received and billed percentages remain visibility/reference only.

Labels:

- Section status: `Buyer follow-up`
- Receipt columns/copy: `Warehouse status`
- Billing columns/copy: `Finance status`

Actions:

- Productized PO Follow-up Detail link is allowed.
- No receive, bill, payment, close, submit, approve, or cancel.

### Supplier `RFQs` Tab

Purpose: show sourcing requests involving this supplier.

Content:

- RFQ name, status, supplier response/quote status, date, required by.
- If recipient readiness matters, link back to `Profile` rather than duplicating full readiness content.

Labels:

- Section status: `RFQ history` or `RFQ readiness` if response/contact posture is included.

Actions:

- Productized RFQ review route only if already supported.
- No send/email/SMTP, no submit, no supplier portal.

### Supplier `Quotations` Tab

Purpose: show supplier offer history.

Content:

- Supplier Quotation, status, date, validity, total.
- Productized drilldown only when available and permission-aware.

Labels:

- Section status: `Quotation history`

Actions:

- No award, conversion, submit, approval, or PO creation from this tab in 7J2B.

## Recommended Buying Item Detail Final Tab Model

Final tabs:

1. `Profile`
2. `Suppliers & Prices`
3. `Orders` now, or `Demand & Orders` only if demand rows are actually present.
4. `Quotation History`

Remove:

- Standalone `Readiness Guidance`
- `References`

### Buying Item Header

Keep the header focused on item identity and evidence counts.

| Header element | Keep/change | Reason |
| --- | --- | --- |
| Item name and code | Keep | Primary object identity. |
| Item group | Keep as meta under Item Code | Helps categorize buying context. |
| UOM | Keep | Essential buying/order interpretation. |
| Active/Disabled | Keep as header chip | Disabled items should not look order-ready. |
| Buying readiness | Keep as one header chip | Quick posture signal. |
| Supplier count | Keep as fact | Signals catalog/vendor evidence. |
| Recent price count | Keep as fact | Signals buying price reference evidence. |
| Below-header count badges | Remove | Duplicate header facts. |

If an item is not ready, show a single compact warning banner below the header and above tabs:

`Item needs sourcing review. Update Item Buying Context before new sourcing.`

Manager action: `Review profile`

User action: `View profile`

### Buying Item `Profile` Tab

Purpose: explain item buying readiness and manager-owned buying context.

Tab label recommendation:

- Use `Profile` for consistency across Supplier and Item pages.
- Use `Item Buying Context` as the card/section title inside the tab.

Content:

1. Item Buying Context card.
2. Buying readiness summary and issue list, compact by default.
3. Preferred existing supplier context.
4. Supplier part reference.
5. Lead time and minimum order quantity.
6. Buying note and readiness note.
7. Permission/ownership explanation.

Manager behavior:

- `Edit Context` remains manager-only and lives inside `Profile`.
- Save mutates only the app-owned Procurement Item Buying Profile and log.
- No Item, Item Supplier, Item Price, Default Supplier, stock, warehouse, accounting, UOM, tax, serial/batch, or variant mutation.

Purchase User behavior:

- Shows the profile context read-only.
- Does not show edit/save controls.
- Uses copy such as `Managed by Purchase Manager`.

### Buying Item `Suppliers & Prices` Tab

Purpose: show buying catalog evidence without exposing master-data mutation.

Content:

1. Approved supplier references from Item Supplier.
2. Buying price references from Item Price.
3. Clear empty states when no rows exist.

Labels:

- `Supplier reference`
- `Price reference`

Actions:

- No Item Supplier mutation.
- No Item Price mutation.
- No Default Supplier mutation.
- No raw Item or Item Price form route.

### Buying Item `Orders` Or `Demand & Orders` Tab

Purpose: show order usage and downstream posture.

Recommended label:

- Use `Orders` if the tab only contains Purchase Orders.
- Use `Demand & Orders` only if the implementation also includes purchase request/material request demand or a productized Demand-to-Order Coverage drilldown.

Content:

- Purchase Order, supplier, required by, status, received %, billed %.
- Optional productized Item Purchase History or Demand-to-Order Coverage route when safe and permission-aware.

Actions:

- Productized PO Follow-up Detail is allowed.
- No receive, bill, payment, submit, approve, cancel, or conversion.

### Buying Item `Quotation History` Tab

Purpose: show supplier offer evidence for the item.

Content:

- Supplier Quotation, supplier, status, validity, total.
- Future RFQ history may be added if RFQ Item evidence is included in the payload.

Actions:

- No award, conversion, supplier communication send, or price update.

## What To Remove

| Current piece | Remove now? | Reason |
| --- | --- | --- |
| Supplier `Activity` tab | Yes | Duplicates Orders and Quotations; not a true chronological timeline. |
| Supplier `References` tab | Yes | Contains primary profile/contact content, not secondary reference. |
| Supplier standalone `Readiness Guidance` tab | Yes | Readiness belongs with Supplier Buying Profile in `Profile`. |
| Supplier below-header count badges | Yes | Duplicate header facts. |
| Item standalone `Readiness Guidance` tab | Yes | Readiness belongs with Item Buying Context in `Profile`. |
| Item `References` tab | Yes | Contains Item Buying Context, which should be primary. |
| Item below-header count badges | Yes | Duplicate header facts. |
| Clear-readiness large panels | Yes, when clear | Use compact status only; do not spend page weight on absence of issue. |

## What To Keep From Phase 7J2A

| Current piece | Keep | Reason |
| --- | --- | --- |
| Page-local tab shell | Yes | It solved the long-stack problem without requiring shared Sales runtime changes. |
| Productized Supplier and Item routes | Yes | Preserves native escape closure. |
| Header object summary | Yes | Strong first-viewport identity and facts are valuable. |
| Business ownership labels | Yes | `Buyer follow-up`, `Reference`, `RFQ readiness`, `Price reference`, and `Supplier reference` are better than `Visibility only`. |
| `Show 12 recent` local reveal | Yes | Good bounded-history compromise. |
| Role-gated edit controls | Yes | Manager can update app-owned profiles; user cannot. |
| App-owned profile save APIs | Yes | Correct governance model. |
| No lifecycle/send/master-data actions | Yes | Must remain protected. |

## What To Merge Into `Profile`

### Supplier

Merge these into Supplier `Profile`:

- Supplier Buying Profile.
- Readiness status and full readiness guidance.
- Preferred RFQ contact.
- Recipient email evidence or override.
- Buying contacts table.
- Permission/ownership copy.

Do not merge:

- Purchase Orders.
- RFQs.
- Supplier Quotations.

These are large operational histories and should stay as separate tabs.

### Buying Item

Merge these into Item `Profile`:

- Item Buying Context.
- Readiness status and full readiness guidance.
- Preferred existing supplier context.
- Supplier part reference context.
- Lead time and MOQ.
- Buying/readiness notes.
- Permission/ownership copy.

Do not merge:

- Item Supplier rows.
- Item Price rows.
- Purchase Orders.
- Supplier Quotations.

These are evidence/history tables and should stay separate.

## Default Tab Recommendation By Role

| Page | Purchase Manager default | Purchase User default | Exceptions |
| --- | --- | --- | --- |
| Supplier Detail | `Profile` | `Profile` | If opened from a PO link, use `Orders`; from RFQ link, use `RFQs`; from quotation link, use `Quotations`; from future timeline, use that context. |
| Buying Item Detail | `Profile` | `Profile` | If opened from Item Purchase History or PO route, use `Orders`; from quote comparison, use `Quotation History`; from supplier/price evidence route, use `Suppliers & Prices`. |

Why not default Purchase User to activity/evidence tabs?

- The owner concern is comprehension. The first screen should explain what the object is and whether it is ready/usable.
- A read-only user still needs to know that readiness and context are manager-owned.
- Empty supplier/price tables as the first tab can make a valid item look incomplete before the user understands the item profile.

## Purchase Manager Edit And Update Rules

Supplier `Profile` manager edits may include only the protected Supplier Buying Profile fields already governed by Phase 7E1A/J2A behavior:

- Buying readiness status.
- Preferred existing linked RFQ contact.
- RFQ recipient email override if already approved in the existing profile design.
- Buying note.
- Readiness note.

Item `Profile` manager edits may include only the protected Item Buying Context fields already governed by Phase 7E2A/J2A behavior:

- Buying readiness status.
- Preferred existing supplier context.
- Supplier part reference context.
- Procurement lead time days.
- Minimum order quantity context.
- Buying note.
- Readiness note.

Manager update rules:

- Edit controls live inside `Profile`.
- Warning/critical banners should activate `Profile`, not a separate readiness tab.
- Save remains inline/productized and audited.
- Unknown/disallowed payload keys remain rejected.
- Save success should refresh only the productized page context.
- Manager edits do not imply Supplier approval, Item approval, RFQ send readiness, or document lifecycle approval.

## Purchase User Read-Only Rules

Purchase User behavior:

- Can open Supplier and Item details.
- Defaults to `Profile`.
- Sees Profile content read-only.
- Sees clear ownership copy such as `Managed by Purchase Manager`.
- Can switch tabs and use productized read-only drilldowns where permission allows.
- Cannot see edit/save controls.
- Cannot mutate Supplier Buying Profile or Item Buying Context.
- Cannot access native ERPNext Supplier/Item/Item Price/Contact forms through these pages.

Avoid:

- Disabled edit buttons that look like broken capability.
- Manager-only fix text such as `Update context` for users.
- Copy that implies Purchase User is expected to solve readiness.

## Label Recommendations

| Concept | Recommended label | Avoid |
| --- | --- | --- |
| Supplier primary tab | `Profile` | `References`, `Supplier buying profile` as tab label |
| Supplier profile card | `Supplier Buying Profile` | `Reference`, `Master data` |
| Supplier order tab | `Orders` | `Activity` |
| Supplier RFQ tab | `RFQs` | `RFQ readiness` as tab label |
| Supplier quotation tab | `Quotations` | `Supplier reference` as tab label |
| Item primary tab | `Profile` | `References` |
| Item profile card | `Item Buying Context` | `Buying Procurement Context` |
| Item supplier/price tab | `Suppliers & Prices` | `References` |
| Item order tab | `Orders` until demand rows exist; `Demand & Orders` when demand rows exist | `Demand & Orders` if no demand is visible |
| Item quotation tab | `Quotation History` | `Supplier reference` as tab label |
| Clear readiness | Header chip only, such as `Reviewed for buying` | Large clear-state panel |
| Warning readiness | Compact banner plus Profile issue | Duplicate tab and badge |
| Read-only ownership | `Managed by Purchase Manager`, `Reference only`, `Buyer follow-up`, `Warehouse status`, `Finance status` | `Visibility only` everywhere |

## Non-Goals

Phase 7J2B must not implement or start:

- Runtime code changes.
- Test or smoke script changes.
- Sales runtime changes.
- Native ERPNext form/list/report escape.
- RFQ/PO send, email, SMTP, Communication, or Email Queue behavior.
- Submit, approve, reject, cancel, amend, or conversion actions.
- Receiving, billing, payment, Purchase Receipt, Purchase Invoice, or Payment Entry mutation.
- Supplier master mutation.
- Item master mutation.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact/User/portal creation or mutation.
- AI quotation intake.
- Quick Find.
- Live alignment.

## Implementation Prompt Outline For Hardening Agent

Use this outline if the owner approves implementation:

1. Start from commit `eb30c721e2642310cd814222f11b295250d529ed` or later on `feature/erpnext-ui-design`.
2. Preserve the current protected J2A tab shell and productized routes.
3. Supplier Detail:
   - Change tabs to `Profile`, `Orders`, `RFQs`, `Quotations`.
   - Move Supplier Buying Profile, readiness card, and contacts into `Profile`.
   - Remove `Activity`, `References`, and standalone `Readiness Guidance`.
   - Default to `Profile`.
   - Remove below-header count badges; keep only a compact warning/critical banner when needed.
   - De-duplicate open/recent order rows where practical.
4. Buying Item Detail:
   - Change tabs to `Profile`, `Suppliers & Prices`, `Orders` or `Demand & Orders`, `Quotation History`.
   - Move Item Buying Context and readiness into `Profile`.
   - Remove `References` and standalone `Readiness Guidance`.
   - Default to `Profile`.
   - Remove below-header count badges; keep only a compact warning/critical banner when needed.
   - Use `Orders` unless demand rows or demand coverage are visibly included.
5. Keep manager edit controls only inside `Profile`; keep Purchase User read-only.
6. Do not add new backend mutation, new DocTypes, native routes, send/email, lifecycle actions, or master-data writes.
7. Add focused smokes for:
   - Supplier/Item tabs and default `Profile`.
   - Absence of removed tabs.
   - Role-gated edit controls.
   - No forbidden labels/actions/routes.
   - Responsive 1136, 1240, 1440 screenshots.
8. Run required source validation and protected gates appropriate to touched files.

## Manual Review Checklist

Supplier Detail:

1. Header shows supplier identity, active/disabled state, readiness, open PO count, RFQ count, and quotation count once.
2. Below-header duplicate badges are gone, except one warning/critical banner when needed.
3. Default tab is `Profile`.
4. `Profile` contains Supplier Buying Profile, readiness guidance, contacts/RFQ recipient evidence, and permission ownership.
5. Purchase Manager can edit only controlled Supplier Buying Profile fields from `Profile`.
6. Purchase User sees the same Profile read-only and no edit/save controls.
7. `Activity`, `References`, and standalone `Readiness Guidance` tabs are absent.
8. `Orders`, `RFQs`, and `Quotations` tabs each show only their own object history.
9. No native ERPNext form/list routes appear.
10. No send/email, submit/approve/convert, receive/bill/pay, Contact/User/portal, Item Price, Default Supplier, or Item Supplier action appears.

Buying Item Detail:

1. Header shows item identity, active/disabled state, readiness, UOM, supplier count, and price count once.
2. Below-header duplicate badges are gone, except one warning/critical banner when needed.
3. Default tab is `Profile`.
4. `Profile` contains Item Buying Context, readiness guidance, and permission ownership.
5. Purchase Manager can edit only controlled Item Buying Context fields from `Profile`.
6. Purchase User sees the same Profile read-only and no edit/save controls.
7. `References` and standalone `Readiness Guidance` tabs are absent.
8. `Suppliers & Prices` clearly remains read-only evidence.
9. `Orders` is not labelled `Demand & Orders` unless actual demand context appears.
10. `Quotation History` contains quotation evidence only.

Cross-page:

1. Tab rows fit at 1136, 1240, and 1440 widths.
2. Keyboard tab activation still works.
3. `Show 12 recent` remains bounded and local.
4. Productized PO Follow-up links still work.
5. Sales Console remains untouched.

## Final Recommendation

Accept the Main Agent direction with one refinement: default both Supplier Detail and Buying Item Detail to `Profile`, and use `Profile` as the common tab label. Inside the item profile, keep the business section title `Item Buying Context`.

For Supplier Detail, remove `Activity`, `References`, and standalone `Readiness Guidance`. For Buying Item Detail, remove `References` and standalone `Readiness Guidance`. Reduce below-header badges to zero in clear states and one compact issue banner in warning/critical states. This produces a cleaner ERP object-page model without reducing any protected capability from Phase 7J2A.
