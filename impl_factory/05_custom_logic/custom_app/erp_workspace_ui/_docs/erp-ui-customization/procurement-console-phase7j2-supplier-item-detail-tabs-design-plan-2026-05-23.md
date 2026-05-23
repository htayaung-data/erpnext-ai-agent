# Procurement Console Phase 7J2 Supplier And Buying Item Detail Tabs Design Plan

Date: 2026-05-23
Branch: `feature/erpnext-ui-design`
Baseline reviewed: Phase 7J1D docs baseline commit `45d56c34b763a94cf5fb3053f1807957c95e8d39`
Scope: docs-only business and UX information architecture design. No runtime implementation is included.

## Executive Summary

Supplier Detail and Buying Item Detail are functionally protected and business-useful, but they are now too vertically dense for a premium day-to-day procurement workspace. Both pages behave more like long read-only reports than object profile pages: the user sees an object header, then profile/readiness, then several related tables stacked one after another.

Phase 7J2 should redesign these two pages as object profile pages with strong summary headers, role-aware primary context, tabbed major sections, compact readiness banners, recent rows by default, and productized drilldowns for full history. This should preserve the Phase 7J1D readiness model and all protected governance boundaries.

Recommended implementation sequence for the Hardening Agent:

1. Add page-local tabbed layouts to Supplier Detail and Buying Item Detail, avoiding shared Sales runtime changes unless explicitly needed.
2. Keep the existing backend payloads as the first implementation source of truth; the current APIs already provide enough bounded related rows for a recent-first tab design.
3. Replace generic `Visibility only` labels with business ownership labels such as `Buyer follow-up`, `Reference`, `RFQ readiness`, `Price reference`, `Warehouse status`, and `Finance status`.
4. Add focused role and viewport smokes before any broader protected gate.
5. Preserve all forbidden actions: native ERP form escape, send/email, submit/approve/convert, receive/bill/pay, Item Price mutation, Default Supplier mutation, Item Supplier mutation, Contact/User/portal creation, and Sales changes.

## Evidence Reviewed

Project docs reviewed:

- `_docs/erp-ui-customization/README.md`
- `_docs/erp-ui-customization/procurement-console-phase7j-ux-information-architecture-redesign-plan-2026-05-20.md`
- `_docs/erp-ui-customization/procurement-console-phase7j1d-readiness-review-polish-baseline-2026-05-23.md`
- `_docs/erp-ui-customization/procurement-console-phase7e1-supplier-buying-profile-contact-readiness-design-plan-2026-05-18.md`
- `_docs/erp-ui-customization/procurement-console-phase7e2-buying-item-procurement-context-design-plan-2026-05-19.md`
- `_docs/erp-ui-customization/procurement-console-phase7e2a-buying-item-procurement-context-baseline-2026-05-19.md`

Source inspected:

- `erp_workspace_ui/procurement_console/suppliers.py`
- `erp_workspace_ui/procurement_console/supplier_detail.py`
- `erp_workspace_ui/procurement_console/items.py`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_supplier_page.js`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_item_page.js`
- `erp_workspace_ui/public/js/runtime/child_page/child_page_shell_content.js`
- Existing smoke references for Supplier Detail, Buying Item Detail, forbidden actions, and productized routing.

Artifacts/screenshots reviewed:

- `ui_smoke/artifacts/procurement-phase7e3a/manager-supplier-detail-1440.png`
- `ui_smoke/artifacts/procurement-phase7e3a/user-supplier-detail-1440.png`
- `ui_smoke/artifacts/procurement-phase7e3a/manager-item-detail-1440.png`
- `ui_smoke/artifacts/procurement-phase7e3a/user-item-detail-1440.png`
- Older Supplier/Item detail artifacts were checked only for route and layout continuity.

Industry/product references used are listed at the end of this document.

## Current Pain Points

| Area | Current behavior | Business/UX risk | Phase 7J2 direction |
| --- | --- | --- | --- |
| Supplier Detail vertical stack | Header, Supplier Buying Profile, Readiness Review, open POs, recent POs, RFQs, Supplier Quotations, Contacts render sequentially. | Purchase Manager must scroll through multiple concepts before deciding what matters. Purchase User sees manager-owned readiness near the top even when they only need activity context. | Keep a compact summary header, then use tabs for Profile, Activity, Contacts, and Readiness Guidance. |
| Buying Item Detail vertical stack | Header, Buying Procurement Context, Readiness Review, approved suppliers, Item Price rows, Supplier Quotations, Purchase Orders render sequentially. | Item pages can feel like a catalog report rather than a buying profile. Item Price and Item Supplier evidence can be misunderstood as editable master data. | Use tabs for Item Buying Context, Suppliers & Prices, Sourcing History, Order History, and Readiness Guidance. |
| Readiness prominence | Critical/warning cards are expanded inline below the profile/context card. | Useful guidance can dominate a profile page, especially for users who cannot fix it. | Show compact readiness banner outside tabs when there is a critical/warning. Put full guidance in a dedicated tab. |
| `Visibility only` label | Each list section uses the same technical label. | Users may not understand whether the section is buyer-owned, warehouse-owned, finance-owned, or reference-only. | Replace with section-specific business ownership labels. |
| Related lists | Backend returns bounded recent lists, usually up to 12 rows, but all rows appear inside the long page. | The detail page becomes a history report as data grows. | Show 5 recent or highest-priority rows by default; allow local `Show 12 recent` or productized `View all` drilldown. |
| Manager/User distinction | Manager gets edit buttons; Purchase User sees read-only cards. Overall layout remains almost the same. | Purchase User can be asked to interpret manager governance context before routine activity context. | Keep the same protected data, but make defaults and action prominence role-aware. |
| Ambiguous item label | `Buying Procurement Context` is technically understandable but awkward. | Owner and end users may not know whether this is item master data, supplier setup, or buyer notes. | Rename to `Item Buying Context` unless owner rejects the change. |

## Business Interpretation Of Supplier Detail

Supplier Detail should answer this business question:

`Can we safely coordinate buying work with this supplier, and what recent sourcing/order activity matters now?`

It is not a Supplier master-data form. It should not feel like a raw ERPNext Supplier record. It is a productized procurement profile combining read-only supplier identity, manager-owned buying readiness, RFQ communication readiness, and recent procurement activity.

A Purchase Manager should see first:

1. Supplier name, ID, supplier group, active/disabled state.
2. Buying readiness: reviewed/known/hold/new review needed.
3. RFQ communication readiness: contact/email ready, missing, override, or blocked.
4. Open PO exposure: count and whether there are overdue/unreceived orders.
5. Latest sourcing/order activity: whether RFQs, quotations, or POs exist.
6. A manager-only `Edit Buying Profile` action when permitted.

A Purchase User should see first:

1. Supplier name, ID, supplier group, active/disabled state.
2. Whether the supplier is usable or on hold for sourcing.
3. Open PO and sourcing activity context.
4. Contact/recipient evidence only as reference.
5. No edit action and no suggestion that the user can correct readiness.

Operational rule: Supplier Detail may guide buying readiness, but it must not grant broad Supplier master-data ownership.

## Business Interpretation Of Buying Item Detail

Buying Item Detail should answer this business question:

`Is this item ready for sourcing or ordering, and what supplier, price, quotation, and order evidence exists?`

It is not an Item master-data form. It should not mutate Item, Item Supplier, Item Price, Default Supplier, stock, accounting, UOM, valuation, warehouse, tax, serial/batch, or variant records. It is a productized procurement item profile that helps buyers understand sourcing readiness and buying context.

A Purchase Manager should see first:

1. Item name/code, item group, UOM, active/disabled state.
2. Buying readiness: reviewed, known by activity, needs review, or hold.
3. Preferred supplier context, lead time, MOQ, and supplier part reference when available.
4. Supplier/price evidence count.
5. Latest sourcing/order activity.
6. A manager-only `Edit Item Buying Context` action when permitted.

A Purchase User should see first:

1. Item name/code, group, UOM, active/disabled state.
2. Buying readiness in simple terms.
3. Current buyer-approved context as read-only guidance.
4. Supplier, price, quotation, and PO evidence through tabs.
5. No edit action and no cue that Item Price, Default Supplier, or Item Supplier can be changed here.

Operational rule: Item Detail may maintain app-owned buying context, but it must not become a hidden Item master maintenance page.

## ERP Pattern Summary

| Source | Pattern relevant to Phase 7J2 | Design implication |
| --- | --- | --- |
| ERPNext Buying | Procurement flow separates Supplier, Item, RFQ, Supplier Quotation, Purchase Order, Purchase Receipt, Purchase Invoice, Item Price, and Contact concepts. | Supplier and Item pages can reference these objects but must preserve ownership boundaries and not mix lifecycle or finance/warehouse actions into the profile page. |
| SAP Fiori object pages | Object pages use a strong header plus sections or tabs for related facets and tables. Large related content should be structured, not stacked endlessly. | Supplier and Item detail should become object profile pages: header first, tabbed facets second, drilldown for large lists. |
| Oracle Procurement | Supplier model separates profile, addresses, sites, contacts, bank accounts, tax, user accounts, and spend authorization. Work areas highlight things needing attention. | Buying readiness can be manager-owned, but supplier identity, tax, bank, portal, and site/contact maintenance remain governed/admin-owned. |
| Microsoft Dynamics 365 Procurement | Vendor accounts, contacts, RFQs, purchase orders, receipt, and invoice processes are distinct. Vendor collaboration and RFQ responses are governed. | Do not merge RFQ send, vendor portal, PO release, receipt, or invoice functions into these object pages. |
| Odoo Purchase | RFQ/PO forms and purchase dashboards use status filters, recent activity, and explicit document states. Email send and order confirmation are distinct actions. | Detail pages should expose status and activity in tabs, while send/confirm lifecycle remains deferred and governed. |

## Summary Header Contract

The summary header should remain outside tabs and should fit the first viewport at 1136, 1240, and 1440 widths without forcing the user past the header just to understand the object.

### Supplier Header

Required fields:

| Element | Purpose | Notes |
| --- | --- | --- |
| Kicker | Page type | Recommended: `Supplier profile` instead of `Supplier buying profile` if the buying profile becomes a tab. |
| Title | Supplier name | Use supplier display name, fallback to ID. |
| Subtitle | Business purpose | `Buying profile, communication readiness, and recent procurement activity.` |
| Chip: Active/Disabled | Master status | Disabled should use danger tone. |
| Chip: Buying readiness | Procurement readiness | Use protected labels from readiness model. |
| Chip: RFQ communication | Contact/email posture | `RFQ contact ready`, `RFQ contact missing`, `RFQ email override`, or similar. Do not imply send is enabled. |
| Fact: Supplier ID | Identity | Meta can show Supplier Group. |
| Fact: Open POs | Buyer exposure | Meta: `Buyer follow-up`. |
| Fact: RFQs | Sourcing evidence | Meta: `Visible RFQ links`. |
| Fact: Quotations | Offer evidence | Meta: `Visible supplier offers`. |
| Fact: Latest activity | Recency | Add if data is available without extra expensive query; otherwise defer. |

Header actions:

- `Back to suppliers`
- `Refresh`
- Purchase Manager only: `Edit Buying Profile`, either as a header action or inside the Profile tab. If placed in header, it should scroll/focus the Profile tab rather than opening a modal over unknown context.

### Buying Item Header

Required fields:

| Element | Purpose | Notes |
| --- | --- | --- |
| Kicker | Page type | Recommended: `Buying item profile`. |
| Title | Item name | Use item name, fallback to item code. |
| Subtitle | Business purpose | `Buying context, supplier evidence, prices, sourcing, and order history.` |
| Chip: Active/Disabled | Item status | Disabled should use danger tone. |
| Chip: Buying readiness | Procurement item readiness | Use protected readiness labels. |
| Chip: Evidence | Historical/catalog evidence | Examples: `Existing buying activity`, `Catalog evidence found`, `New item - review needed`. |
| Fact: Item Code | Identity | Meta can show Item Group. |
| Fact: UOM | Stock UOM | Label as `UOM`, meta `Stock unit`. |
| Fact: Suppliers | Supplier evidence | Meta: `Approved supplier rows`, read-only. |
| Fact: Prices | Price evidence | Meta: `Buying price references`, read-only. |
| Fact: Latest activity | Recency | Add if data is already available or cheap. |

Header actions:

- `Back to items`
- `Refresh`
- Purchase Manager only: `Edit Item Buying Context`, either as a header action or inside the Item Buying Context tab.

## Proposed Supplier Detail Tab Model

Recommended tabs:

1. `Buying Profile`
2. `Activity`
3. `Contacts & RFQ Readiness`
4. `Readiness Guidance`

### Supplier Tab Defaults

| Role/state | Default tab | Reason |
| --- | --- | --- |
| Purchase Manager with critical hold/warning | `Buying Profile` with compact critical banner above tabs | Manager can act on the profile immediately. |
| Purchase Manager with no critical issues | `Activity` or `Buying Profile`, owner decision required | Activity is more day-to-day; Profile is more governance-oriented. Recommended default: `Activity` once profile is healthy. |
| Purchase User | `Activity` | User usually needs business context, not edit governance. |
| Opened from Manager Readiness Queue | `Buying Profile` or `Readiness Guidance` depending on link target | Review links should deep-link to the most relevant tab, not simply open the top of the page. |
| Opened from RFQ communication readiness | `Contacts & RFQ Readiness` | The user is investigating recipient/contact posture. |

### Supplier Tab Content Contract

| Tab | Business purpose | Default content | Recent/View all behavior | Role differences |
| --- | --- | --- | --- | --- |
| `Buying Profile` | Maintain or inspect supplier buying readiness without editing Supplier master. | Supplier Buying Profile card: readiness status, preferred RFQ contact, recipient email/override, buying note, readiness note, last updated, permission. | No long list. Keep fields compact. If edit form opens, keep it inside this tab. | Manager can edit allowlisted app-owned fields. User sees read-only profile and permission explanation. |
| `Activity` | Understand current and recent supplier procurement work. | Open/overdue POs first, then recent POs, RFQs, Supplier Quotations. Use small section summaries inside the tab. | Show 5 rows per list. `Show 12 recent` can reveal already-loaded rows. `View all POs/RFQs/Quotes` must route to productized worklists/reports only when filtered drilldown is supported. | Same data for both roles subject to permissions. No lifecycle actions. |
| `Contacts & RFQ Readiness` | Understand whether this supplier can be addressed for RFQ preparation. | Linked Contacts table, preferred RFQ contact, recipient email source, RFQ send deferred note, outgoing email readiness if already available in RFQ context. | Show up to 5 linked contacts; allow `Show more contacts` only from bounded existing payload. | Manager can edit preferred contact/override only through Buying Profile if permitted. User reference-only. No Contact/User creation. |
| `Readiness Guidance` | Explain readiness exceptions and fix paths. | Full readiness card content, grouped by severity/category. | Not a history list. Expand only issue groups; clear groups compact. | Manager sees fix-oriented links to productized profile. User sees guidance and who owns the fix. |

### Supplier Compact Banner Above Tabs

Use a compact banner only when readiness has critical or warning items.

Required behavior:

- Banner text example: `Supplier on hold for sourcing. Review Buying Profile before new sourcing.`
- Banner action for manager: `Review profile`, which activates `Buying Profile` or `Readiness Guidance`.
- Banner action for user: `View guidance`, which activates `Readiness Guidance`.
- Do not duplicate the full readiness card above the tabs.
- Clear readiness should appear only as a chip or small positive line, not as a large card.

## Proposed Buying Item Detail Tab Model

Recommended tabs:

1. `Item Buying Context`
2. `Suppliers & Prices`
3. `Sourcing History`
4. `Order History`
5. `Readiness Guidance`

Rename recommendation:

- Replace `Buying Procurement Context` with `Item Buying Context`.
- Reason: it is shorter, clearer, and avoids the awkward double noun phrase. It also signals that this is app-owned buying context, not raw Item master data.

### Buying Item Tab Defaults

| Role/state | Default tab | Reason |
| --- | --- | --- |
| Purchase Manager with sourcing warning/hold | `Item Buying Context` with compact warning banner above tabs | Manager can correct allowed context immediately. |
| Purchase Manager with healthy context | `Suppliers & Prices` or `Item Buying Context`, owner decision required | Buyers often need supplier/price evidence first; managers may prefer context first. Recommended default: `Item Buying Context` until owner validates comprehension. |
| Purchase User | `Suppliers & Prices` | User normally checks sourcing evidence, supplier references, and prices rather than edit governance. |
| Opened from Manager Readiness Queue | `Item Buying Context` or `Readiness Guidance` depending on link target | Review links should land at the task-relevant tab. |
| Opened from item purchase history/report | `Order History` | The user is investigating buying history. |

### Buying Item Tab Content Contract

| Tab | Business purpose | Default content | Recent/View all behavior | Role differences |
| --- | --- | --- | --- | --- |
| `Item Buying Context` | Maintain or inspect app-owned buying context for the item. | Buying readiness, preferred existing supplier context, supplier part reference, lead time, MOQ, buying note, readiness note, last updated, permission. | No long list. Edit form stays inside this tab. | Manager can edit allowlisted profile fields. User read-only. |
| `Suppliers & Prices` | Show catalog/buying evidence without exposing master-data mutation. | Approved suppliers from Item Supplier, buying Item Price references, evidence explanations. | Show 5 supplier rows and 5 price rows by default. `Show 12 recent` may reveal existing bounded rows. `View all` only if a productized filtered report/list exists. | Same read-only evidence. No Item Supplier, Item Price, or Default Supplier mutation. |
| `Sourcing History` | Show supplier offer and sourcing evidence for this item. | Recent Supplier Quotations and, when available in future payload, RFQs linked through RFQ Item rows. | Show 5 recent quotations/RFQs. Productized drilldown to Supplier Quotation Directory/Quote Comparison with item filter when supported. | Same read-only context. No award/convert action. |
| `Order History` | Show ordering evidence and downstream posture. | Recent/open Purchase Orders linked to item, received %, billed %, required by. | Show 5 order rows. `View purchase history` can route to productized Item Purchase History report with item filter when supported. | Same read-only context. PO links may open productized PO Follow-up Detail. No receive/bill/pay. |
| `Readiness Guidance` | Explain item readiness exceptions and fix paths. | Full readiness card content, grouped by severity/category. | Not a history list. Clear categories compact. | Manager sees fix links to Item Buying Context. User sees guidance and ownership. |

### Buying Item Compact Banner Above Tabs

Use a compact banner only when there is a warning or critical item issue.

Required behavior:

- Banner text example: `Item needs sourcing review. Update Item Buying Context before new sourcing.`
- Banner action for manager: `Review context`.
- Banner action for user: `View guidance`.
- The full Readiness Review card should move into the `Readiness Guidance` tab.

## Recent Rows And View All Rules

These rules apply to both pages.

| Rule | Contract |
| --- | --- |
| Default row count | Show 5 rows per related list by default. |
| Already-loaded rows | If backend already returns up to 12 rows, `Show 12 recent` may reveal them locally without another API call. |
| Full history | Use productized worklists/reports only. Do not route to raw ERPNext list, raw Form, or query-report routes. |
| View all label | Use specific labels: `View purchase order analysis`, `View quote comparison`, `View item purchase history`, `View supplier quotations`, not generic `View all` when the target has a clear business purpose. |
| Sorting | Open/overdue operational exceptions first; otherwise recent by transaction date/modified. |
| Empty state | Explain what absence means in business language, for example `No visible supplier quotations for this supplier`. |
| Loading | Do not block the header while related tabs load if future lazy-loading is introduced. Header and active tab should appear first. |
| Permissions | Do not show `View all` targets that the user cannot open. |
| No native route | Every drilldown must remain inside productized Procurement routes. |

Recommended first implementation compromise:

- Keep the current single detail endpoint.
- Render first 5 rows by default from the existing table payload.
- Add `Show 12 recent` only when rows beyond 5 are already in the payload.
- Defer true server-side pagination or filtered full-history endpoints until a later performance/report phase.

## Role Visibility Matrix

| Surface | Purchase Manager | Purchase User |
| --- | --- | --- |
| Supplier header | Full summary, readiness chips, open activity facts. | Same summary, no manager-only action. |
| Supplier Buying Profile tab | Editable app-owned profile if permission allows. | Read-only profile with ownership explanation. |
| Supplier Activity tab | Read-only related activity and productized drilldowns. | Same, permission-aware. |
| Contacts & RFQ Readiness tab | Existing contacts and recipient readiness; profile edit path if allowed. | Existing contacts and recipient readiness only. |
| Supplier Readiness Guidance tab | Full guidance with manager fix links. | Guidance only; explain Purchase Manager ownership. |
| Item header | Full summary, readiness chips, supplier/price facts. | Same summary, no manager-only action. |
| Item Buying Context tab | Editable app-owned context if permission allows. | Read-only context with ownership explanation. |
| Suppliers & Prices tab | Read-only Item Supplier and Item Price evidence. | Same read-only evidence. |
| Sourcing History tab | Read-only RFQ/SQ context and productized drilldowns. | Same, permission-aware. |
| Order History tab | Read-only PO/purchase history; PO Follow-up route where allowed. | Same, permission-aware. |
| Item Readiness Guidance tab | Full guidance with manager fix links. | Guidance only; explain Purchase Manager ownership. |

Purchase User should not see empty edit controls, disabled save buttons, or manager-only copy that implies they are expected to fix readiness.

## Allowed Actions Matrix

| Action | Supplier Detail | Buying Item Detail | Role | Conditions |
| --- | --- | --- | --- | --- |
| Back | Allowed | Allowed | Manager/User | Productized route only. |
| Refresh | Allowed | Allowed | Manager/User | Reload current productized context. |
| Switch tabs | Allowed | Allowed | Manager/User | Keyboard accessible and stateful within current route. |
| Expand/collapse readiness issue groups | Allowed | Allowed | Manager/User | No mutation. |
| Edit Supplier Buying Profile | Allowed | Not applicable | Purchase Manager only | App-owned readiness profile fields only. |
| Save Supplier Buying Profile | Allowed | Not applicable | Purchase Manager only | Existing protected allowlist, validation, audit log. |
| Edit Item Buying Context | Not applicable | Allowed | Purchase Manager only | App-owned item buying profile fields only. |
| Save Item Buying Context | Not applicable | Allowed | Purchase Manager only | Existing protected allowlist, validation, audit log. |
| Show 12 recent rows | Allowed | Allowed | Manager/User | Reveals already-loaded bounded rows only. |
| Productized drilldown | Allowed | Allowed | Manager/User | Route must be productized Procurement worklist/report/detail and permission-aware. |
| Open PO Follow-up Detail | Allowed | Allowed | Manager/User if readable | Existing productized PO Follow-up route only. |

## Deferred And Forbidden Actions Matrix

| Action/data mutation | Status | Reason |
| --- | --- | --- |
| Native ERPNext Supplier or Item form escape | Forbidden | Phase 7D1 closed normal-role native escape. |
| Supplier master edit | Forbidden | Supplier identity, group, status, tax, bank, payment, and portal data are not buyer-page actions. |
| Contact create/edit/delete/relink | Deferred/forbidden for 7J2 | Contact governance and external communication risk. |
| User or supplier portal creation | Forbidden | External identity/security scope. |
| RFQ/PO send/email/SMTP | Deferred | Governed send infrastructure remains out of scope. |
| RFQ Supplier `send_email` or `email_sent` mutation | Forbidden | Would imply or trigger external communication state. |
| Submit/approve/reject/cancel/amend | Deferred | Lifecycle governance not implemented in this redesign. |
| PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, PR-to-PO conversion | Deferred | Needs separate workflow design, role gates, rollback/cancel design. |
| Purchase Receipt, Purchase Invoice, Payment Entry mutation | Forbidden | Warehouse/Finance ownership. |
| Item master edit | Forbidden | Item ownership extends beyond procurement workspace. |
| Item Supplier mutation | Forbidden | Approved supplier master data needs governance. |
| Item Price mutation | Forbidden | Pricing governance and financial consequences. |
| Default Supplier mutation | Forbidden | Defaulting and buying automation consequences. |
| Stock/accounting/UOM/valuation/tax/serial/batch/variant mutation | Forbidden | Warehouse, Finance, inventory, and item master ownership. |
| AI quotation intake | Deferred | Separate design and data-quality governance required. |
| Sales Console change | Forbidden in 7J2 | Sales freeze remains protected. |

## Label And Copy Recommendations

Replace generic labels with business ownership labels.

| Current label/copy | Recommended replacement | Where |
| --- | --- | --- |
| `Visibility only` | `Buyer follow-up` | Open/overdue POs and supplier order posture. |
| `Visibility only` | `Reference` | Linked history or read-only evidence sections. |
| `Visibility only` | `Price reference` | Item Price evidence. |
| `Visibility only` | `Supplier reference` | Item Supplier evidence. |
| `Visibility only` | `RFQ readiness` | Supplier contact/recipient posture. |
| `Read-only` chip in header | `Procurement view` or remove if redundant | Supplier/Item headers. |
| `Buying Procurement Context` | `Item Buying Context` | Buying Item Detail tab/card. |
| `Supplier price review` | `Buying price references` | Item Detail price section. |
| `Approved suppliers` | `Supplier references` or `Approved supplier references` | Item Supplier evidence. |
| `Recent purchase orders` | `Recent order activity` | Supplier Activity tab. |
| `Open or overdue purchase orders` | `Open order follow-up` | Supplier Activity tab. |
| `Readiness Review` | `Readiness Guidance` | Full readiness tab. |
| `Review supplier profile` | `Review Buying Profile` | Supplier readiness link. |
| `Review item context` | `Review Item Buying Context` | Item readiness link. |

Copy style rules:

- Use ownership language: `Managed by Purchase Manager`, `Reference only`, `Warehouse status`, `Finance status`.
- Avoid implementation language: `companion DocType`, `payload`, `native route`, `query report` should not appear in UI copy.
- Avoid implying approval: readiness is guidance, not document approval.
- Keep deferred action copy local to the action area; do not turn the whole page into a warning about deferred send/submit/conversion.

## Data And Loading Expectations

Current backend fit:

- `supplier_detail.py` already returns bounded supplier activity: recent purchase orders, open purchase orders, RFQs, Supplier Quotations, Contacts, Supplier Buying Profile, and readiness context.
- `items.py` already returns bounded item context: Item Suppliers, Item Prices, Supplier Quotations, Purchase Orders, Item Buying Profile, and readiness context.
- Both pages already cache same-route payloads client-side for a short TTL.
- Current related lists are suitable for recent-first tab rendering without expanding backend scope.

Performance expectations for implementation:

| Requirement | Target |
| --- | --- |
| Header render | Should appear as soon as the existing payload is available. Do not introduce separate header-blocking calls. |
| Default active tab | Render without loading full history. |
| Related rows | Keep bounded. Do not query unbounded Supplier/Item history from detail pages. |
| Tab switch | Should be instant if using existing payload. |
| Future lazy-load | Acceptable only if each tab has a bounded endpoint, controlled loading state, permission checks, and deterministic smoke behavior. |
| Mobile/tablet | Tabs may become a segmented dropdown or horizontally scrollable tab row, but labels must not overflow. |
| Accessibility | Tabs need proper active state, keyboard focus, and readable button labels. |
| No N+1 | Avoid per-row calls for supplier names, contacts, prices, or PO details. Use existing payload aggregation or bounded batch calls. |

Do not add server-side pagination in the first 7J2 implementation unless the owner explicitly approves it. The business goal is comprehension, not a new reporting engine.

## Smoke And Test Recommendations

Docs-only validation remains compile/unit/diff-check only. For later implementation, require focused UI smokes before protected gates.

Recommended focused smoke coverage:

| Test area | Required assertions |
| --- | --- |
| Supplier Detail Manager | Header visible; tabs visible; default tab follows contract; `Edit Buying Profile` visible; no native form route; no forbidden action labels. |
| Supplier Detail User | Header visible; tabs visible; no edit/save controls; profile read-only explanation visible; activity tab usable. |
| Buying Item Detail Manager | Header visible; tabs visible; `Edit Item Buying Context` visible; `Item Buying Context` label used if owner approves; no Item Price/Item Supplier mutation labels. |
| Buying Item Detail User | Header visible; tabs visible; no edit/save controls; supplier/price evidence read-only. |
| Readiness warning state | Compact banner appears; full readiness content lives in `Readiness Guidance`; manager link activates correct tab. |
| Clear readiness state | No large clear readiness card competes with profile/activity; readiness appears as chip or compact status. |
| Recent rows | Default list row count is capped at 5; `Show 12 recent` appears only when extra loaded rows exist. |
| Productized drilldown | PO Follow-up and report/worklist links stay inside Procurement routes. |
| Forbidden scan | No `Open ERP Form`, native `/desk/Form/`, `send email`, `Submit`, `Approve`, `Convert`, `Receive`, `Bill`, `Pay`, `Update Item Price`, `Set Default Supplier`, or `Create Contact/User/Portal`. |
| Responsive | Manager and user screenshots at 1136, 1240, and 1440 widths show no overlap and tabs remain usable. |
| Sales protection | If shared runtime/CSS is touched, run the Sales freeze/protected workspace gate. If only Supplier/Item page JS/CSS is touched, still run targeted Sales smoke if shared classes are altered. |

Backend/unit test recommendations if implementation changes payload contracts:

- Assert Supplier Detail payload still has only productized actions.
- Assert Item Detail payload still has only productized actions.
- Assert Purchase User contexts do not return edit permission or save controls.
- Assert manager editable payload keys remain allowlisted.
- Assert forbidden DocTypes are not mutated by save endpoints.

## Manual Review Checklist

As Purchase Manager, Supplier Detail:

1. Open a supplier with hold/warning readiness.
2. Confirm first 5 seconds answer: supplier identity, readiness/hold, RFQ contact posture, open order exposure, and available manager action.
3. Confirm the page does not show all related lists stacked vertically before tabs.
4. Confirm `Edit Buying Profile` is available only to manager and edits only app-owned profile fields.
5. Confirm `Activity` shows recent rows first and productized drilldowns only.
6. Confirm `Contacts & RFQ Readiness` does not create Contact/User/portal and does not send email.
7. Confirm full readiness details are in `Readiness Guidance`, not duplicated as a large top stack.

As Purchase User, Supplier Detail:

1. Confirm no edit/save controls are visible.
2. Confirm the default experience emphasizes activity/reference context rather than manager fix work.
3. Confirm read-only ownership copy is clear and business-friendly.

As Purchase Manager, Buying Item Detail:

1. Open an item with a sourcing warning.
2. Confirm first 5 seconds answer: item identity, readiness, preferred supplier context, lead time/MOQ, supplier/price evidence, and latest buying activity.
3. Confirm `Item Buying Context` is understandable and does not imply Item master edit.
4. Confirm `Suppliers & Prices` is clearly read-only evidence.
5. Confirm `Order History` and `Sourcing History` are separated.
6. Confirm no Item Price, Default Supplier, or Item Supplier mutation is exposed.

As Purchase User, Buying Item Detail:

1. Confirm no edit/save controls are visible.
2. Confirm supplier/price/order evidence is easy to find.
3. Confirm readiness guidance explains ownership without asking the user to fix manager-owned fields.

Cross-role checks:

1. Confirm tabs are keyboard accessible.
2. Confirm row counts do not overwhelm the first tab.
3. Confirm no native ERP route appears in UI or action targets.
4. Confirm all visible route changes stay inside Procurement Console productized pages.
5. Confirm Sales Console is untouched.

## Implementation Sequencing Recommendation For Hardening Agent

### Phase 7J2A: Tab Shell And Labels

Purpose: introduce tabbed information architecture on Supplier Detail and Buying Item Detail without changing backend semantics.

Recommended steps:

1. Add page-local tab rendering in `procurement_console_supplier_page.js` and `procurement_console_item_page.js`.
2. Avoid changing shared child-page runtime unless the implementation cannot remain clean locally.
3. Move existing profile/context, readiness, and related list markup into the tab structure.
4. Add compact readiness banner above tabs for warning/critical states.
5. Replace `Visibility only` labels with section-specific business labels.
6. Keep existing save APIs, payloads, validation, and permissions unchanged.

Risk if done poorly: shared runtime regression, Sales freeze risk, hidden lifecycle/native route leak, or unreadable mobile tab overflow.

### Phase 7J2B: Recent Rows And Productized Drilldown

Purpose: reduce table density while preserving access to history.

Recommended steps:

1. Show 5 rows by default for each related list.
2. Add `Show 12 recent` for already-loaded rows only.
3. Add productized drilldown links only where the target already exists and can be permission-aware.
4. Defer new filtered endpoints if not needed for first owner review.

Risk if done too early: accidental raw query-report/list escape or slow detail pages due unbounded history.

### Phase 7J2C: Role-Aware Defaults And Deep Links

Purpose: make the page open to the most useful tab for the user's role and route source.

Recommended steps:

1. Manager readiness links open the relevant profile/context or readiness tab.
2. Purchase User defaults to activity/reference tabs where appropriate.
3. Report/worklist drilldowns can open Order History or Activity tabs when useful.
4. Preserve same-route cache behavior and route cleanup.

Risk if done too early: hard-to-test route state and inconsistent browser back behavior.

### Phase 7J2D: Protected Gate And Owner Comprehension Review

Purpose: prove the redesign improves comprehension without changing business authority.

Required evidence:

- Manager/User screenshots for Supplier and Item detail at 1136, 1240, 1440 widths.
- Focused smoke summary for tabs, row caps, forbidden actions, and role differences.
- `git diff --check HEAD`, Python compileall, unit discovery.
- Node syntax checks for touched JS.
- Static forbidden action/native route scans.
- Sales freeze/protected gate if shared runtime or shared CSS changed.
- Owner manual review checklist completed.

## Owner Decisions Needed

| Decision | Recommended answer | Why it matters |
| --- | --- | --- |
| Should `Buying Procurement Context` be renamed? | Yes, rename to `Item Buying Context`. | Clearer, shorter, and less technical. |
| Supplier default tab for healthy manager view | Recommended: `Activity`; alternative: `Buying Profile`. | `Activity` supports daily work; `Buying Profile` supports governance. Owner preference matters. |
| Item default tab for healthy manager view | Recommended initial: `Item Buying Context`; revisit after owner review. | Keeps manager-owned item context visible while the concept is still new. |
| Purchase User default tabs | Supplier: `Activity`; Item: `Suppliers & Prices`. | Users need reference/activity first, not edit governance. |
| Should `Show 12 recent` be local or server-loaded? | Local only for 7J2. | Avoids new performance and pagination scope. |
| Should full history drilldowns be added immediately? | Only for existing productized routes/reports with safe filters. | Prevents raw ERP route leakage. |
| Should Contacts have a separate tab? | Yes for Supplier; no for Item. | Supplier communication readiness is important and contact data can grow. |
| Should Item Price evidence remain visible? | Yes, as read-only `Buying price references`. | Important buying evidence, but must not imply price mutation. |
| Should readiness be hidden when clear? | Do not hide completely; compress to chip/status. | Users need confidence, but not noise. |
| Should manager edit buttons live in header or tab? | Prefer tab-local edit; optional header shortcut focuses the tab. | Reduces accidental edit framing and keeps actions near owned fields. |

## Acceptance Criteria

Phase 7J2 implementation can be accepted only if all of these are true:

1. Supplier Detail and Buying Item Detail no longer present all major long lists in one vertical stack by default.
2. Each page has a strong object header that explains identity, readiness, and operational posture within the first viewport.
3. Tabs have clear business labels and purposes.
4. Purchase Manager can still edit only the protected app-owned Supplier Buying Profile and Item Buying Context fields.
5. Purchase User sees read-only context with no edit/save affordances.
6. Related lists show recent rows first and do not become unbounded history reports.
7. All drilldowns stay inside productized Procurement routes.
8. `Visibility only` is replaced or reduced to business-specific ownership labels.
9. Readiness is visible but not overwhelming; full guidance is tabbed/expandable.
10. No runtime behavior from the forbidden/deferred list is introduced.
11. No Sales Console file is changed unless explicitly approved and protected by Sales freeze validation.
12. Manual owner review confirms the pages are easier to understand than the current stacked layout.

## Non-Goals And Deferred Scope

Phase 7J2 must not implement or start:

- Runtime send/email/SMTP.
- RFQ or PO external communication.
- Native ERPNext form links or raw list/report escapes.
- Supplier master edit.
- Item master edit.
- Contact/User/portal creation or mutation.
- Submit, approve, reject, cancel, amend, or conversion actions.
- Receiving, billing, payment, Purchase Receipt, Purchase Invoice, or Payment Entry mutation.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- AI intake.
- Supplier scorecards, onboarding, qualification workflow, or portal readiness workflow.
- Server-side full-history pagination unless separately scoped.
- Sales Console redesign.

## References Used

Official/product references:

- ERPNext Procurement Cycle Overview: <https://docs.frappe.io/erpnext/procurement-cycle-overview>
- ERPNext Supplier: <https://docs.frappe.io/erpnext/supplier>
- ERPNext Item: <https://docs.frappe.io/erpnext/item>
- ERPNext Request for Quotation: <https://docs.frappe.io/erpnext/request-for-quotation>
- ERPNext Supplier Quotation: <https://docs.frappe.io/erpnext/supplier-quotation>
- ERPNext Purchase Order: <https://docs.frappe.io/erpnext/purchase-order>
- SAP Fiori Object Page floorplan: <https://www.sap.com/design-system/fiori-design-web/page-types/floorplans/object-page/>
- SAP Fiori Analytical List Page floorplan: <https://www.sap.com/design-system/fiori-design-web/page-types/floorplans/analytical-list-page/>
- Oracle Supplier Model: <https://docs.oracle.com/en/cloud/saas/procurement/26a/oaprc/oracle-supplier-model.html>
- Oracle Procurement documentation index: <https://docs.oracle.com/en/cloud/saas/procurement/26b/index.html>
- Microsoft Dynamics 365 vendor account setup: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/set-up-vendor-accounts>
- Microsoft Dynamics 365 request for quotations: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations>
- Microsoft Dynamics 365 purchase order overview: <https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-order-overview>
- Odoo Purchase RFQ documentation: <https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html>
- Odoo Purchase dashboard and vendor analysis: <https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/purchase_dashboard.html>

## Final Recommendation

Proceed with Phase 7J2 as a focused information architecture implementation, not as a new procurement capability phase. The correct next step is to reorganize existing protected Supplier and Item detail capability into business-readable tabs with recent-first related lists and role-aware defaults. This directly addresses owner comprehension concerns while preserving the safer post-native-escape procurement model.

The first implementation should be conservative: page-local tabs, existing payloads, compact readiness banner, recent row caps, and label cleanup. Full-history filtered endpoints, route deep-linking, or shared runtime abstraction can follow only after the tabbed IA is manually accepted.
