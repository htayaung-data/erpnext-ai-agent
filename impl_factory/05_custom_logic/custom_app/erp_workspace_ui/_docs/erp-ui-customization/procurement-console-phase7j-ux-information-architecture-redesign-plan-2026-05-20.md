# Procurement Console Phase 7J UX Information Architecture Redesign Plan

Date: 2026-05-20
Branch: `feature/erpnext-ui-design`
Baseline reviewed: Phase 7I protected freeze baseline at `7393f0c32a6c7e4f2b73628bd083a609b4558880`
Scope: docs/research/design only. No runtime implementation is included.

## Executive Summary

Phase 7I shows the Procurement Console is working and protected. The current baseline is not broken: the freeze audit covered 40 routes, two roles, three viewport widths, 240 screenshots, and found no freeze-blocking runtime defect. The next problem is information architecture and business comprehension.

The workspace now has enough capability that some pages feel dense. Overview Manager Readiness can become a long issue feed. Supplier Detail and Buying Item Detail stack profile, readiness, activity, contacts, price, RFQ, quotation, and order data in one vertical path. Managed forms and review pages combine data entry, readiness, output, and deferred-policy messaging close together. The next professional UX layer should make managers scan first, understand business importance, and drill down only when needed.

Recommendation: preserve the protected baseline and implement a staged IA redesign:

1. `Phase 7J1`: Overview Manager Readiness compression and business wording.
2. `Phase 7J2`: Supplier Detail and Buying Item Detail tabbed/activity redesign.
3. `Phase 7J3`: Managed form and review page hierarchy polish.
4. `Phase 7J4`: Directory/report explanation and label consistency.
5. `Phase 7J5`: Final visual regression and owner comprehension audit.

Do not implement send/email, submit/approval/conversion, receiving/billing/payment, Item Price, Default Supplier, Item Supplier, Contact/User/portal, AI intake, native ERPNext form escape, or Sales Console changes in this redesign phase.

## Evidence Reviewed

Project evidence:

- `_docs/erp-ui-customization/README.md`
- Phase 7I freeze baseline doc.
- Phase 7H operations handover and Phase 7H1 readiness inference baseline.
- Phase 7E1 Supplier Buying Profile design.
- Phase 7E2A Buying Item Procurement Context baseline.
- Phase 7E3 Manager Review / Action Readiness design.
- Phase 7I artifact root: `/tmp/procurement-phase7i-freeze-audit-20260520T130503Z`
- Phase 7I route inventory, screenshot index, function findings, performance findings, and audit findings.

Screenshots reviewed:

- Purchase Manager and Purchase User captures at `1136x768`, `1240x768`, and `1440x900` from the Phase 7I audit set.
- Representative direct review included Overview, Supplier Detail, Buying Item Detail, RFQ Review, managed saved RFQ, Purchase Order Follow-up, Reports Index, and Item Purchase History.

Source behavior referenced:

- `procurement_console/service.py`, `readiness.py`, `readiness_evidence.py`, `supplier_detail.py`, `items.py`, `document_reviews.py`, `document_output.py`, `report.py`, `worklist.py`
- `public/js/procurement_console/procurement_console_page.js`, `procurement_readiness_ui.js`, and managed PR/RFQ/SQ/PO form scripts.

## ERP Product Research Summary

| System | Relevant pattern | Procurement Console implication |
| --- | --- | --- |
| SAP Fiori | Object pages use a header, sections/tabs, and navigation to full lists for large related tables. Analytical/list pages separate filters, summaries, and result tables. | Supplier, Item, PO, and review pages should become object-page style surfaces: summary first, tabs/sections second, full history elsewhere. |
| Oracle Procurement | Work areas and infolets summarize critical data and issues needing action. Supplier profile, qualification, and administration are distinct from day-to-day purchasing. | Overview readiness should be infolet-like: counts, top issues, and drilldown, not a full exception report. |
| Microsoft Dynamics 365 | Procurement separates PO preparation from receipt/follow-up. Workspaces show lists by status and summarize actions needed. RFQ, bid comparison, award, and PO generation are governed. | Keep preparation, sourcing, order follow-up, warehouse status, and finance status separate. Do not collapse them into one page/action. |
| Odoo Purchase | RFQ dashboards show status summaries, filters, groups, and clear states such as To Send, Waiting, and Late. Forms use document sections/tabs and activity history. | Directories should remain Apply/filter worklists. Document pages should separate line entry, communication/output, and history/activity. |
| ERPNext | Buying flow separates Material Request, RFQ, Supplier Quotation, Purchase Order, Purchase Receipt, Purchase Invoice, Supplier, Item, Item Price, and Contacts. RFQ send can create email/portal side effects. | Keep productized views and governed output. Preview/PDF is safe; send/portal/lifecycle remain deferred. |

## IA Principles For Phase 7J

1. First screen answers one business question.
2. Summary comes before detail.
3. Exceptions are grouped by business ownership, not source module.
4. Readiness is guidance, not lifecycle approval.
5. Historical lists show recent rows by default and link to full productized lists/reports.
6. Manager-only review work is visible to Purchase Manager and reduced for Purchase User.
7. Long detail pages use tabs or collapsible sections, not long card stacks.
8. Copy explains business purpose, not implementation mechanics.
9. Read-only labels should describe ownership boundaries.
10. Deferred governance warnings stay local to the action area where the user would expect the action.

## Current Comprehension Risks

| Area | Current risk | Design direction |
| --- | --- | --- |
| Overview Manager Readiness | Can dominate the page and act like a report. | Compress into counts, top 3 issues, collapsed groups, and View all. |
| Supplier Detail | Profile, readiness, contacts, RFQs, SQs, and POs stack vertically. | Use object header plus tabs: Buying Profile, Activity, Contacts, Readiness. |
| Buying Item Detail | Context, readiness, suppliers, prices, quotations, and POs stack vertically. | Use object header plus tabs: Item Buying Context, Suppliers & Prices, Sourcing History, Order History, Readiness. |
| Managed forms | Readiness/output content can distract from draft entry. | Keep form first; readiness/output collapsed below saved forms. |
| Review pages | Readiness can appear before the document evidence the user opened. | Header and document lines first; readiness summary compact unless critical. |
| Reports Index | Cards are useful but read like an approved surface catalog. | Group by business question and add `What this report answers`. |
| Labels | `Visibility only` and repeated `Read-only` are technically correct but not business-friendly. | Use `Reference`, `Warehouse status`, `Finance status`, `Buyer follow-up`, and `Guidance only`. |

## Overview Manager Readiness Redesign

Business purpose: let a Purchase Manager answer in five seconds: What needs attention today, how severe is it, what type of problem is it, and where do I go next?

Recommended default layout:

1. Rename heading to `Readiness Review Queue`.
2. Subtitle: `Supplier, item, document, and communication exceptions needing manager attention.`
3. Severity count strip: Critical, Warning, Info.
4. Category cards with counts: Supplier readiness, Item buying readiness, RFQ communication, Document quality, Order follow-up.
5. Show top 3 critical/warning issues only.
6. Auto-expand groups with critical issues; collapse warning-only groups.
7. Add `View all readiness issues` to expand full grouped list or open a future productized readiness page.
8. Hide this section for Purchase User.

Acceptance rules:

- Overview first screen must not become a full issue report.
- Critical issues must remain visible without hunting.
- Deferred lifecycle info must not inflate warning/critical counts.
- No send/submit/convert actions are introduced.

## Supplier Detail Redesign

Business purpose: show whether the supplier is active, reviewed/known/held, contactable for RFQ preparation, and active in recent RFQ/SQ/PO work.

Recommended hierarchy:

1. Supplier object header: name, group, active/disabled, readiness state, open PO count, RFQ count, quotation count, contact readiness summary.
2. Compact actions: Back, Refresh, Edit Buying Profile for manager only.
3. Summary strip: buying readiness, RFQ communication readiness, open order exposure, latest activity.
4. Tabs:
   - `Buying Profile`: controlled manager-owned profile fields.
   - `Activity`: recent POs/RFQs/Supplier Quotations.
   - `Contacts`: linked contacts and recipient evidence.
   - `Readiness Guidance`: readiness issues and fix paths.
5. Activity lists show recent 5 rows by default with productized `View more` links where existing worklists/reports support filters.

Default behavior:

| Section | Default state |
| --- | --- |
| Header/facts | Expanded. |
| Buying Profile | Expanded for manager; summary/read-only for user. |
| Readiness Guidance | Compact; expand automatically only for critical/warning. |
| Activity | Tabbed; recent rows only. |
| Contacts | Tabbed or collapsed unless RFQ communication issue exists. |

## Buying Item Detail Redesign

Business purpose: show whether the item is purchase-enabled, reviewed/known/held, has supplier/price evidence, and has quotation/order history.

Recommended hierarchy:

1. Item object header: item name/code, group, UOM, active/disabled, readiness state, supplier count, recent price/history evidence.
2. Compact actions: Back, Refresh, Edit Context for manager only.
3. Summary strip: buying readiness, preferred supplier context, lead time/MOQ, last buying activity.
4. Tabs:
   - `Item Buying Context` replacing `Buying Procurement Context` if owner approves.
   - `Suppliers & Prices` for Item Supplier and Item Price read-only evidence.
   - `Sourcing History` for supplier quotations/RFQs.
   - `Order History` for POs and purchase history.
   - `Readiness Guidance` for manager/user readiness context.
5. Recent 5 rows by default per related list, with `View more` into productized worklists/reports.

Do not mutate Item, Item Supplier, Item Price, Default Supplier, stock, accounting, valuation, UOM, warehouse, tax, serial/batch, or variant data.

## Managed Form Redesign

Managed forms should keep drafting focused. The user should not have to parse readiness or output policy before completing the form.

| Page | Primary purpose | Recommended default |
| --- | --- | --- |
| New Purchase Request | Capture internal purchase demand. | Form only; readiness hidden or placeholder until saved. |
| Saved Purchase Request | Maintain draft demand. | Form first; readiness compact below form. |
| New RFQ | Prepare supplier sourcing request. | Form first; no output until saved. |
| Saved RFQ | Maintain RFQ draft and preview readiness/output. | Form first; recipient readiness/output collapsed below. |
| New Supplier Quotation | Record supplier offer. | Form first. |
| Saved Supplier Quotation | Maintain draft offer. | Form first; readiness compact below. |
| New Purchase Order | Prepare supplier order draft. | Form first. |
| Saved Purchase Order | Maintain draft PO and preview output. | Form first; PO preview/output collapsed below with draft warning. |

If a saved document has a critical blocker, show only the top blocker expanded. Keep the full readiness list collapsed until selected.

## Review Page Redesign

Review pages should first confirm what document is being reviewed, then show lines/participants, then readiness guidance.

Recommended pattern:

1. Header facts.
2. Core document lines or participants.
3. Compact readiness banner with counts and top issue.
4. Expandable full readiness guidance.
5. Context sections such as supplier communication, comparison, output, downstream status.

RFQ Review should separate four boxes: RFQ summary, supplier/item readiness, invited supplier response posture, and Supplier Communication. Supplier Communication should keep Preview/PDF visible and Send RFQ disabled with local wording: `RFQ email send is deferred until governed send is approved.`

PO Follow-up should replace generic `Visibility only` where possible:

- Receipt posture -> `Warehouse status`
- Billing posture -> `Finance status`
- Supplier coordination -> `Buyer follow-up`
- Linked records/history -> `Reference`

## Directory And Worklist Redesign

Keep Apply-based filters. Do not convert directory/worklist pages into typeahead navigation surfaces.

Recommended purpose lines:

| Page | Purpose line |
| --- | --- |
| Supplier Directory | `Find suppliers and open their buying profile, activity, and readiness context.` |
| Buying Item Directory | `Find purchase-enabled items and review buying context before sourcing.` |
| Purchase Request Directory | `Review purchase demand records visible to this buyer.` |
| Requests To Source | `Review submitted purchase demand that still needs sourcing or ordering action.` |
| RFQ Directory | `Find sourcing requests and supplier response posture.` |
| RFQs Awaiting Response | `Track RFQs where supplier responses are still pending.` |
| Supplier Quotation Directory | `Find supplier offers for review and comparison.` |
| Supplier Quotations To Compare | `Review offers that may support a future award decision.` |
| Purchase Order Directory | `Find purchase orders for buyer follow-up and supplier coordination.` |
| PO Follow-up queues | `Work orders by follow-up state without taking Warehouse or Finance actions.` |

## Reports Redesign

Reports should be grouped by business decision, not just listed as approved surfaces.

| Report | Business question answered |
| --- | --- |
| Quote Comparison | `Which supplier offer looks best by price, validity, item, and RFQ context?` |
| Purchase Order Analysis | `Which orders are open, late, partially received, or not fully billed?` |
| Demand-to-Order Coverage | `Which purchase demand is ordered, partially covered, or still open?` |
| Item Purchase History | `What has this item been bought for, from whom, and at what rate?` |

Reports Index grouping:

1. Sourcing decisions: Quote Comparison.
2. Order performance: Purchase Order Analysis.
3. Demand coverage: Demand-to-Order Coverage.
4. Item buying history: Item Purchase History.

Keep report filters visible and Apply-based. Long report tables belong on report pages and do not need tabbing.

## Page-By-Page IA Matrix

| Surface | Business purpose | First 5 seconds should answer | Recommended IA |
| --- | --- | --- | --- |
| Overview | Triage daily buying work and exceptions. | What needs attention today? | KPI header, create actions, compressed readiness, priority work. |
| Supplier Directory | Locate suppliers. | Can I find/open supplier? | Filter table with purpose line. |
| Supplier Detail | Understand supplier readiness/activity. | Is supplier usable and active? | Object header plus Buying Profile, Activity, Contacts, Readiness tabs. |
| Buying Item Directory | Locate purchase items. | Can I find item and readiness? | Filter table with purpose line. |
| Buying Item Detail | Understand item buying context/history. | Is item ready/known/held and who supplies it? | Object header plus context, suppliers/prices, sourcing, order, readiness tabs. |
| Purchase Request Directory | Browse demand. | Which requests exist? | Filter table. |
| Requests To Source | Work demand needing sourcing. | Which demand needs buyer action? | Queue purpose plus rows. |
| Purchase Request Review | Review demand before future sourcing/order step. | What is requested and when? | Header, requested items, compact readiness. |
| Managed PR New/Saved | Draft demand. | What must I enter/save? | Form first; readiness below saved forms. |
| RFQ Directory | Browse sourcing requests. | Which RFQs are active/pending? | Filter table. |
| RFQ Review | Review request, responses, communication readiness. | Who is invited and what is requested? | Header, suppliers/items, compact readiness, communication panel. |
| Managed RFQ New/Saved | Draft sourcing request. | Which suppliers/items/dates are included? | Form first; communication/output collapsed when saved. |
| Supplier Quotation Directory | Browse offers. | Which offers need review? | Filter table. |
| Supplier Quotation Review | Review offer for comparison. | Is offer valid and complete? | Header, quoted items, compact readiness, compare link. |
| Managed SQ New/Saved | Record supplier offer. | Supplier, validity, item rates. | Form first; readiness below. |
| Purchase Order Directory | Browse orders. | Which orders need follow-up? | Filter table. |
| PO follow-up queues | Work orders by state. | Which orders need buyer coordination? | Queue rows with ownership wording. |
| PO Follow-up Detail | Inspect order status/downstream posture. | What is open/received/billed? | Header, item lines, Warehouse status, Finance status, compact readiness. |
| Managed PO New/Saved | Prepare PO draft. | Supplier, rates, dates, warehouse. | Form first; output collapsed with draft warning. |
| Reports Index | Choose decision report. | Which report answers my question? | Grouped report cards by decision type. |
| Quote Comparison | Compare offers. | Which supplier offer is best? | Report filters, metrics, table. |
| PO Analysis | Analyze order posture. | Which orders are late/open/received/billed? | Report filters, metrics, table. |
| Demand-to-Order Coverage | Track demand coverage. | Which demand is uncovered? | Report filters, metrics, table. |
| Item Purchase History | Review buying history. | What did we buy and at what rate? | Report filters, metrics, table. |
| RFQ Preview/PDF | Validate supplier-facing draft output. | Is output ready to preview/download? | Collapsed output panel; no send. |
| PO Preview/PDF | Validate draft PO output. | Is draft output printable but not committed? | Collapsed output panel; not-for-supplier warning. |

## Collapse, Tab, Recent Row, And View-More Rules

| Content type | Default behavior |
| --- | --- |
| Object identity/key metrics | Always visible. |
| Overview readiness | Counts plus top 3 issues. |
| Critical detail readiness | Expanded top blocker. |
| Warning-only detail readiness | Collapsed summary. |
| Ready-only readiness | Single compact ready row/chip. |
| Supplier/item activity tables | Recent 5 rows. |
| Document line tables | Visible because they are core content. |
| Report filters/tables | Visible because reports are filter-first. |
| Output preview/PDF panels | Collapsed until selected. |
| Deferred/disabled actions | Local explanation near disabled action. |

## Label And Copy Recommendations

| Current wording | Recommended wording | Reason |
| --- | --- | --- |
| `Manager Readiness` | `Readiness Review Queue` | More business-readable. |
| `Buying Procurement Context` | `Item Buying Context` | Shorter and clearer. |
| `Visibility only` | `Reference`, `Warehouse status`, `Finance status`, or `Buyer follow-up` | Explains ownership. |
| `Read-only` | Keep as state chip, reduce as section wording | Avoids repetitive technical framing. |
| `Billing Visibility` | `Finance status` | Names owner. |
| `Receipt Visibility` | `Warehouse status` | Names owner. |
| `Send remains deferred` | `RFQ email send is deferred` | More explicit. |
| `Future governed order step` | `Order release/send is deferred` | More concrete. |
| `Ready` | `No readiness issues` or `Reviewed for buying` | Avoids implying approval/send. |

## Manager Versus User Presentation

| Area | Purchase Manager | Purchase User |
| --- | --- | --- |
| Overview readiness | Compressed queue visible. | Hidden. |
| Supplier Buying Profile | Manager edit allowed fields. | Read-only summary. |
| Item Buying Context | Manager edit allowed fields. | Read-only summary. |
| Detail readiness | Fix actions where manager-owned. | Guidance only, no manager edit actions. |
| Managed forms | Create/edit only if permissions allow. | Same permission rule, no manager-only profile edits. |
| Reports | Read-only decision support. | Read-only decision support if permitted. |
| Deferred actions | Same policy text, no active actions. | Same policy text, no active actions. |

Use the same layout for both roles; remove manager-only content/actions for Purchase User.

## Implementation Phases

### Phase 7J1: Overview Manager Readiness Compression

Purpose: reduce Overview cognitive load while preserving critical exception visibility.

Scope:

- Counts by severity and category.
- Top 3 visible issues.
- Collapsed groups by default.
- Auto-expand critical groups.
- `View all readiness issues` pattern.
- Business-friendly heading/subtitle.

Tests:

- Manager sees compressed readiness.
- User does not see manager readiness.
- Critical issues are visible without expanding.
- Deferred info does not inflate warning/critical counts.

### Phase 7J2: Supplier And Item Detail Tabbed Redesign

Purpose: make detail pages behave like business object pages.

Scope:

- Supplier tabs: Buying Profile, Activity, Contacts, Readiness.
- Item tabs: Item Buying Context, Suppliers & Prices, Sourcing History, Order History, Readiness.
- Recent 5 rows by default.
- Productized `View more` links where routes exist.

Tests:

- Manager edit controls remain scoped.
- Purchase User remains read-only.
- Native Supplier/Item form escape remains absent.
- No Item Price/Default Supplier/Item Supplier/Contact/User mutation appears.

### Phase 7J3: Managed Form And Review Page Hierarchy Polish

Purpose: keep form entry and document review focused.

Scope:

- Form first, readiness/output below.
- Readiness collapsed unless critical.
- RFQ Supplier Communication as distinct panel/tab.
- PO/RFQ output panels collapsed with draft/not-sent warnings.

Tests:

- Save/review actions remain visible.
- Autocomplete placement remains accepted.
- Send RFQ remains disabled.
- PO preview remains draft/not commitment.

### Phase 7J4: Directory, Queue, Report, And Label Consistency

Purpose: make every route's business purpose clear.

Scope:

- Purpose lines on directories/queues.
- Reports Index grouped by business question.
- Report pages show `What this report answers`.
- Replace generic `Visibility only` wording.

Tests:

- Apply filters still work.
- Row Open actions route only to productized pages.
- Report filters and rows still render.

### Phase 7J5: Final Visual Regression And Owner Comprehension Audit

Purpose: confirm the redesign improves comprehension and does not regress protected baselines.

Scope:

- Capture manager/user screenshots at 1136, 1240, 1440 widths.
- Run focused Procurement smokes and full protected workspace gate as needed.
- Owner answers: `What is this page for? What should I do next? What is deferred?`

## Non-Goals And Deferred Items

Phase 7J must not implement or start:

- Native ERPNext form escape for normal Procurement paths.
- RFQ/PO send/email, SMTP, Communication, Email Queue.
- Contact/User/portal creation or mutation.
- Submit, approve, reject, cancel, amend, award, release, or conversion.
- PR -> RFQ, PR -> PO, RFQ -> SQ, SQ -> PO conversion.
- Purchase Receipt, Purchase Invoice, Payment Entry, receiving, billing, payment.
- Item Price, Default Supplier, Item Supplier mutation.
- Broad Supplier/Item master mutation beyond protected companion profile fields.
- AI intake or autonomous procurement actions.
- Sales Console changes except validation when shared runtime changes require protected gates.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Collapsed readiness hides blockers. | Auto-expand critical blockers and show count strip. |
| Tabs hide activity. | Put activity counts in header and tab labels. |
| `View more` creates navigation confusion. | Use explicit productized route labels and filters. |
| Copy becomes too verbose. | Use one-line purpose text only. |
| Shared shell changes affect Sales. | Run Sales freeze/protected gate when shared runtime is touched. |
| Users expect deferred actions after polish. | Keep deferred wording local and explicit. |
| Recent rows hide history. | Always provide full-list/report drilldown where available. |

## Acceptance Criteria

1. Overview Manager Readiness no longer dominates the first screen.
2. Critical manager exceptions remain visible immediately.
3. Purchase User does not see manager-only readiness or edit actions.
4. Supplier Detail separates profile, readiness, contacts, and activity.
5. Buying Item Detail separates context, supplier/price data, sourcing history, order history, and readiness.
6. Long related lists show recent rows with productized view-more paths.
7. Managed forms keep primary draft entry above readiness/output.
8. Review pages separate document facts, lines, readiness, and communication/output.
9. Reports explain the decision question each report answers.
10. Generic `Visibility only` wording is reduced or replaced with ownership wording.
11. No forbidden lifecycle, send, master-data, portal, or AI behavior is introduced.
12. Sales frozen baseline remains protected.
13. Owner can explain each page's business purpose from screenshots without agent narration.

## Manual Review Checklist

Overview:

- Can the manager see critical/warning counts without scrolling?
- Are only the top issues visible by default?
- Is the full issue list reachable without turning Overview into a report?

Supplier Detail:

- Can the owner identify supplier status, readiness, contact posture, and activity within five seconds?
- Are RFQs, quotations, orders, and contacts easy to find without crowding the page?

Buying Item Detail:

- Can the owner identify item readiness, supplier/price evidence, and recent buying activity within five seconds?
- Is `Item Buying Context` clear without opening Item master data?

Managed Forms:

- Is data entry visually primary?
- Are readiness and output helpful but not distracting?
- Are disabled send/release policies clear?

Review Pages:

- Can the owner tell what document is being reviewed and what business decision is possible?
- Is readiness guidance separate from approval/action completion?

Reports:

- Can the owner explain when to use each report?
- Are filters still understandable and Apply-based?

## References Used

Project references:

- `_docs/erp-ui-customization/procurement-console-phase7i-full-freeze-audit-baseline-2026-05-20.md`
- `/tmp/procurement-phase7i-freeze-audit-20260520T130503Z`
- `_docs/erp-ui-customization/procurement-console-phase7h1-readiness-inference-exception-queue-baseline-2026-05-20.md`
- `_docs/erp-ui-customization/procurement-console-phase7e1-supplier-buying-profile-contact-readiness-design-plan-2026-05-18.md`
- `_docs/erp-ui-customization/procurement-console-phase7e2a-buying-item-procurement-context-baseline-2026-05-19.md`
- `_docs/erp-ui-customization/procurement-console-phase7e3-manager-review-action-readiness-design-plan-2026-05-19.md`

External references:

- SAP Fiori Object Page floorplan: https://www.sap.com/design-system/fiori-design-web/page-types/floorplans/object-page/
- SAP Fiori Analytical List Page floorplan: https://www.sap.com/design-system/fiori-design-web/page-types/floorplans/analytical-list-page/
- Oracle SCM/Procurement infolets: https://docs.oracle.com/en/cloud/saas/procurement/26b/oaprc/how-you-use-and-personalize-infolets-in-oracle-scm-and.html
- Oracle Procurement documentation index: https://docs.oracle.com/en/cloud/saas/procurement/26b/index.html
- Microsoft Dynamics 365 Purchase Order overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-order-overview
- Microsoft Dynamics 365 RFQ overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/request-quotations
- Odoo Purchase RFQ documentation: https://www.odoo.com/documentation/18.0/applications/inventory_and_mrp/purchase/manage_deals/rfq.html
- Odoo Purchase & Vendor analysis dashboard: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/purchase_dashboard.html
- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/request-for-quotation
- ERPNext Procurement Cycle Overview: https://docs.frappe.io/erpnext/procurement-cycle-overview

## Final Recommendation

Start with Phase 7J1. It directly addresses the most visible owner concern and has the lowest risk because it can compress information without changing procurement lifecycle behavior. Then proceed to Phase 7J2 for Supplier and Item object pages, because those are the pages most likely to become hard to understand as business history grows.