# Procurement Console Phase 7G Quick Find Operations Review

Date: 2026-05-19

Branch: `feature/erpnext-ui-design`

Scope: operations and UX workflow design review only. No runtime Python, JavaScript, CSS, smoke script, Sales Console, live alignment, native ERP form escape, RFQ send/email, Contact/User/portal creation, submit/approval/conversion, receiving, billing, payment, Item Price, Default Supplier, or AI intake implementation is included.

## Executive Summary

Recommendation: accept the Main Controller proposal with operational refinements.

Procurement should keep directory and worklist pages as Apply-based filters. Those pages are where buyers refine queues, compare rows, and use visible filter labels introduced in Phase 7F. They should not become typeahead-driven navigation surfaces.

Procurement should add one smart Overview Quick Find box, but it must behave differently from Sales Overview Inquiry. Sales Inquiry resolves a customer commercial chain and can immediately render a rich result after a suggestion is selected. Procurement Quick Find should be a locator and triage helper: typing returns grouped suggestions, selecting a suggestion shows a compact preview card, and the user must click an explicit Open action to navigate to the productized Procurement route. Selection must not auto-navigate.

The feature should include core records now: Supplier, Buying Item, Purchase Request/Material Request, RFQ, Supplier Quotation, Purchase Order, and report shortcuts. Supplier readiness profile, RFQ recipient readiness issues, and PO follow-up queues should be deferred until their preview data and route semantics are explicitly designed. Native ERPNext forms, mutation actions, send/email, Contact/User/portal effects, submit/approval/conversion, receiving/billing/payment, Item Price, Default Supplier, and AI intake are out of scope.

## Source Gate Result

- Confirmed branch: `feature/erpnext-ui-design`.
- Confirmed HEAD: `ac2a48086e16af5531c81131af3a43c6602b643b`.
- Confirmed Phase 7F follow-up commit `ac2a48086e16af5531c81131af3a43c6602b643b` is HEAD and therefore included.
- Confirmed working tree was clean except the allowed untracked `ui_smoke/sales_final_acceptance_audit.js` before this docs-only review began.

## Scope Reviewed

Source reviewed:

- `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
- `erp_workspace_ui/sales_console/service.py`
- `erp_workspace_ui/procurement_console/service.py`
- `erp_workspace_ui/procurement_console/common.py`
- `erp_workspace_ui/procurement_console/suppliers.py`
- `erp_workspace_ui/procurement_console/items.py`
- `erp_workspace_ui/procurement_console/requests.py`
- `erp_workspace_ui/procurement_console/sourcing.py`
- `erp_workspace_ui/procurement_console/purchase_orders.py`
- `erp_workspace_ui/procurement_console/purchase_order_follow_up.py`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/tests/test_procurement_console_phase0_contracts.py`
- `ui_smoke/procurement_phase7f_search_smoke.js`

Docs reviewed:

- `_docs/erp-ui-customization/README.md`
- `_docs/erp-ui-customization/procurement-console-phase7e-operations-capability-gap-audit-2026-05-18.md`
- `_docs/erp-ui-customization/procurement-console-phase7e1-supplier-buying-profile-contact-readiness-design-plan-2026-05-18.md`

Recent commit context reviewed:

- `b7be1e8 fix: align procurement worklist search semantics`
- `ac2a480 fix: harden procurement search smoke fixture`

## Sales Inquiry Comparison

Sales Overview Inquiry currently has three backend capabilities:

- `suggest_customer_inquiry(query)` returns visible suggestions after at least two characters.
- `resolve_customer_inquiry(query, doctype, name)` resolves a selected customer or document to a customer commercial chain.
- `generate_customer_inquiry_assist(...)` can generate a structured AI/fallback brief after a single chain is resolved.

The Sales UI groups suggestions, lets the user choose with mouse or keyboard, writes the selected value into the inquiry input, and immediately runs the resolver. The result panel can show primary match, customer summary, document flow, current status, exceptions/blockers, related records, and an explicit Open Record button.

This is acceptable in Sales because the inquiry object is a customer commercial chain. The buyer's equivalent is not one chain. Procurement records represent different operational decisions: supplier readiness, buying item context, internal demand, sourcing request, supplier offer, purchase order, follow-up, and reports. A suggestion click can move the user into very different business states. Procurement should therefore avoid Sales-style immediate resolution and avoid auto-opening.

## Procurement Directory Filter Distinction

Phase 7F aligned Procurement worklist search semantics:

- Supplier Directory searches supplier or group.
- Buying Item Directory searches item, name, or group.
- Purchase Request queues search request, item, or warehouse through child item data.
- RFQ queues search RFQ, supplier, or item through supplier and item child rows.
- Supplier Quotation queues search quotation, supplier, or item through child item data.
- Purchase Order and follow-up queues search order, supplier, or item through child item data.

These filters are Apply-based and visible on the directory/worklist pages. That should remain unchanged because:

- Buyers use directories to refine operational queues, not just locate one record.
- Apply-based filters are deterministic and testable.
- Filter labels explain what the search is matching.
- Results stay in the current page context, which helps comparison and follow-up.
- Worklists can include queue-specific constraints such as submitted RFQs, expiring quotations, overdue POs, or requests to source.

Overview Quick Find should not replace these filters. It should help users jump from the Overview to the right productized page after a compact preview confirms they selected the right record.

## Operations Workflow Review

### Purchase User

A Purchase User uses Overview Quick Find when they already know an identifier, supplier name, item, or supplier-facing document reference and want to locate it quickly. They still use directory pages when they need to work a queue, compare many rows, apply multiple filters, or review operational lists.

Purchase User Quick Find must be read-only. It may show draft records the user can read and open in productized managed forms if route and permissions allow. It must not expose manager readiness edit controls, send actions, submit, conversion, receiving, billing, payment, Item Price, Default Supplier, or raw master data.

### Purchase Manager

A Purchase Manager uses Overview Quick Find for triage: find a supplier, item, PR, RFQ, SQ, PO, or report from the dashboard before choosing whether to open a detail/review/report page. A manager needs enough preview context to avoid opening the wrong record, especially when IDs are similar or the same supplier appears across RFQs, quotations, and POs.

The manager still needs directories for sustained operational work. Quick Find should not turn the Overview into a hidden worklist with mutation actions.

### Auto-navigation Risk

Suggestion auto-navigation would create avoidable business risk:

- Similar document IDs can route to the wrong lifecycle stage.
- A supplier result and a supplier quotation result can share the same supplier term but require different actions.
- A PO preview could be mistaken for commitment context if opened too quickly.
- Users may lose Overview context and current work.
- Keyboard selection could accidentally navigate.
- Future result types such as readiness issues or follow-up queues would have non-record semantics.

The safer pattern is selection -> preview -> explicit Open.

## Result Type Matrix

| Result type | Recommendation | Why | Target productized route | Role visibility | Preview fields | Primary action label |
| --- | --- | --- | --- | --- | --- | --- |
| Supplier | Include now | Core buying context and common lookup target | `/desk/procurement-console-supplier/<supplier>` | Users with Supplier read and Procurement access | Supplier name/id, active/disabled, group, readiness summary if available, open PO/RFQ/SQ counts | Open supplier |
| Buying Item | Include now | Buyers often locate by item before sourcing/order review | `/desk/procurement-console-item/<item>` | Users with Item read and Procurement access; purchase-enabled items only | Item name/code, group, UOM, active/disabled, approved supplier count, recent buying activity | Open item |
| Purchase Request / Material Request | Include now | Internal demand is a starting point for sourcing/order coverage | `/desk/procurement-console-purchase-request-review/<material-request>` for submitted/current review; managed form for editable draft only if allowed later | Users with Material Request read; purchase requests only | Status, required by, company, item count, ordered/coverage posture | Review request |
| RFQ / Request for Quotation | Include now | Sourcing follow-up and recipient readiness are central buyer work | `/desk/procurement-console-rfq-review/<rfq>` for submitted/current review; managed form for editable draft only if allowed later | Users with RFQ read | Status, required by, supplier count, pending/received counts, send disabled/readiness summary | Review RFQ |
| Supplier Quotation | Include now | Offer review and comparison are manager workflows | `/desk/procurement-console-supplier-quotation-review/<supplier-quotation>` | Users with Supplier Quotation read | Supplier, status, total, valid till, linked RFQ if visible | Review quotation |
| Purchase Order | Include now | PO follow-up is a major Overview activity | `/desk/procurement-console-po-follow-up/<purchase-order>` for submitted/current follow-up; managed form for editable draft only if allowed later | Users with Purchase Order read | Supplier, status/workflow state, required by, total, received %, billed % | Open follow-up |
| Reports | Include now | Managers may know they need a report rather than a record | Productized report routes only | Procurement roles with report/page access and underlying read permissions | Report name, purpose, boundary, no mutation note | Open report |
| Supplier readiness profile | Defer | Phase 7E1 introduced readiness capability, but Quick Find should first stabilize core records; readiness can appear as supplier preview context | Supplier Detail now; direct readiness panel anchor later if implemented | Purchase Manager for edit context, Purchase User read-only | Readiness status, preferred existing contact, last updated | Open supplier |
| RFQ recipient readiness issues | Defer | This is an exception queue, not a simple record result; needs deterministic issue model | RFQ Review or future readiness queue | Purchase Manager primarily | RFQ, supplier, issue type, block reason | Review readiness |
| PO follow-up queues | Defer as result type, include reports/queue shortcuts later | Queues are operational groupings; they should stay visible as Overview cards/worklists unless a queue shortcut design is approved | `/desk/procurement-console-worklist/<queue-key>` | Procurement roles with PO read | Queue name, count if cheap, boundary | Open queue |

Excluded result types for Phase 7G:

- Contact records, User records, portal users, Email Account, Communication, Email Queue.
- Item Price and Default Supplier records.
- Purchase Receipt, Purchase Invoice, Payment Entry as executable targets.
- Native ERPNext report/list/form links.
- AI intake actions or supplier portal artifacts.

## Preview Field Matrix

Preview cards should be compact and operational. They should answer: "Is this the right thing, and what page will I open?" They should not become mini-detail pages.

| Result type | Recommended preview fields | Remove or avoid |
| --- | --- | --- |
| Supplier | Supplier name/id, status, supplier group, buying readiness chip if available, open POs, active RFQs, recent quotations, preferred existing recipient if available | Bank/tax/payment terms, portal users, full contact table, edit controls |
| Buying Item | Item name/code, item group, UOM, active/disabled, approved supplier count, recent quotation/PO count | Item Price rates in Quick Find, stock/accounting fields, variant/UOM controls |
| Purchase Request | Request id, status, required by, company, item count, ordered %, source posture | Full item table, warehouse execution controls, conversion action |
| RFQ | RFQ id, status, required by, supplier count, pending/received supplier response counts, readiness summary, Send RFQ disabled note | Message body, native email controls, portal/contact/user state |
| Supplier Quotation | Quotation id, supplier, status, total, valid till, linked RFQ/reference if visible, comparison hint | Item Price update, Default Supplier, create PO, full quoted lines |
| Purchase Order | PO id, supplier, workflow/status, required by, total, received %, billed %, draft/not supplier commitment warning when docstatus 0 | Receive, bill, pay, email supplier, native print/send |
| Report | Report title, purpose, current boundary, main filters if any, no mutation note | Report results inside preview, hidden export/mutation actions |
| Deferred readiness issue | Issue type, supplier/RFQ, block reason, suggested safe page | Send button, Contact/User creation, automatic correction |
| Deferred PO queue | Queue name, count, date posture, boundary | Inline order list, receive/bill/pay |

## UX Interaction Contract

Recommended interaction: dropdown plus preview, no auto-open.

- Minimum query length: 2 characters for suggestions.
- Debounce: yes, short delay consistent with Sales Inquiry behavior.
- Maximum suggestions: 12 total initially, with per-group caps so one DocType cannot dominate.
- Result grouping order: Suppliers, Buying Items, Purchase Requests, RFQs, Supplier Quotations, Purchase Orders, Reports. If a future exception mode is added, show readiness/issues after core records unless explicitly filtered.
- Selecting a suggestion: updates the input with the selected label/reference and renders the preview card. It must not navigate.
- Primary action: the preview card contains exactly one main Open action for the selected result, using a productized route.
- Secondary actions: keep to Clear/Back to suggestions. Do not add lifecycle actions.
- Keyboard behavior: Up/Down moves active suggestion; Enter selects suggestion when dropdown is open; Enter on a selected preview activates Open only when focus is on the Open button, not from the input by default; Escape closes suggestions or clears preview.
- Empty state: "No visible Procurement records match this search. Use directory filters for broader queue review."
- Idle state: "Type at least 2 characters to find suppliers, items, requests, RFQs, quotations, purchase orders, or reports."
- Loading state: "Searching visible Procurement records..."
- Preview clear behavior: clear preview on input edit, Clear action, route change, or workspace refresh.
- Route change behavior: do not persist a selected preview across route changes.
- Mobile behavior: suggestions and preview must remain vertically stacked; Open action stays explicit and visible.
- Accessibility: suggestions should expose listbox/option semantics, active descendant or equivalent, and deterministic labels.

## Security And Governance Requirements

- Productized routes only. Targets must be Procurement Console page/report/worklist routes.
- No native ERPNext Form/List/Report escape routes, including `/desk/Form`, `/app`, `frappe.set_route("Form", ...)`, raw report routes, or Desk form URLs.
- No mutation from Quick Find. No save, submit, approve, reject, cancel, amend, convert, send, receive, bill, pay, update price, set default supplier, create Contact/User/portal, or create Communication/Email Queue.
- Permission-aware results only. A user must not see suggestions or previews for records they cannot open through the target productized page.
- No Contact/User/portal side effects. Contact data may appear only as read-only context where already visible and permitted.
- No send/email side effects. RFQ and PO previews must keep send disabled and must not call email endpoints.
- No records the user cannot open. Suggestion generation and preview generation must share route-access/read checks.
- No broad unbounded searches. Enforce minimum length, maximum result count, per-Doctype caps, and bounded child-table lookups.
- Sanitize and bound search terms. Trim input, reject or neutralize control characters, avoid direct SQL string assembly, and use structured filters/helpers.
- Deterministic enough for smoke tests. Group order, labels, result keys, and primary actions should be stable.
- No hidden report mutation actions. Report results may open productized report pages only.
- No Sales changes. Sales Inquiry is reference context, not shared-runtime scope for Phase 7G unless separately approved.

## Technical Feasibility Notes

Existing `search_procurement_console_workspace` is a useful starting point but should not be stretched into the full Quick Find API without design changes.

Current endpoint behavior:

- Requires authentication and Procurement role access.
- Requires at least two characters.
- Searches top-level Supplier, Item, Material Request, RFQ, Supplier Quotation, and Purchase Order fields.
- Returns a flat list of results with worklist targets and keyword filters.
- Does not search Phase 7F child-table fields.
- Does not return previews.
- Does not route directly to detail/review pages.

Phase 7F worklist filters added better child-table matching through helpers such as `matching_parent_names_for_keyword` and `apply_keyword_name_filter`. Quick Find should reuse these helper concepts where feasible, but should stay bounded and should avoid duplicating every queue-specific filter path.

Cleaner implementation recommendation:

1. Keep `search_procurement_console_workspace` backward compatible if it is used by global workspace search.
2. Add a new read-only endpoint such as `get_procurement_quick_find_suggestions(query, limit=12)` for grouped Overview suggestions.
3. Add a second read-only endpoint such as `get_procurement_quick_find_preview(result_type, name_or_key)` or include lightweight preview data in suggestions only when cheap.
4. For core record previews, reuse existing productized context builders where safe, but avoid N+1 calls. Prefer summary queries/counts with strict limits.
5. For report suggestions, use the existing report catalog metadata and route keys.
6. Keep preview targets explicit and productized.
7. Do not add shared runtime behavior that changes Sales Inquiry.

Suggested backend shape for suggestion rows:

- `result_type`
- `group`
- `doctype` or `report_key`
- `name`
- `label`
- `meta`
- `target`
- `preview_token` or deterministic key
- `is_draft` if relevant
- `boundary_note`

Suggested preview shape:

- `state`
- `result_type`
- `title`
- `subtitle`
- `facts`
- `chips`
- `warnings`
- `target`
- `primary_action`

## Implementation Sequence Recommendation

1. Design and contract first: add manifest expectations and backend payload contract for suggestions/preview.
2. Implement suggestion endpoint with core records and report shortcuts only.
3. Implement preview endpoint/cards for core records with permission checks.
4. Add Overview UI: input, grouped suggestions, selected preview, explicit Open.
5. Add unit tests for result grouping, permissions, target routes, no native routes, no mutation keys, and bounded result limits.
6. Add smoke test for Purchase User and Purchase Manager: type, suggestions appear, select, preview appears, Open navigates to productized route, no auto-navigation.
7. Defer readiness issue and queue shortcut result types until after the core pattern is stable.

## Smoke And Test Requirements

Required tests before accepting a future implementation:

- Unit: suggestions require at least two characters.
- Unit: suggestions are permission-aware and hide unreadable DocTypes.
- Unit: result targets are productized Procurement routes only.
- Unit: no suggestion/preview includes native Form/List/Report target kinds.
- Unit: no mutation action keys appear in suggestions or previews.
- Unit: core record result types return deterministic group order.
- Unit: preview endpoint enforces read permission before loading details.
- Unit: reports are productized report shortcuts only.
- Unit: Quick Find does not include Contact/User/portal, Item Price, Default Supplier, Purchase Receipt, Purchase Invoice, Payment Entry, Communication, or Email Queue results.
- Smoke: Purchase User can type, see grouped suggestions, select one, see preview, click Open, and land on a productized route.
- Smoke: Purchase Manager gets the same safe pattern with manager-visible context but no mutation.
- Smoke: selecting a suggestion does not auto-navigate.
- Smoke: route change clears preview.
- Static: no `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, `Advanced ERP Form`, `/desk/Form`, `/app/`, or `frappe.set_route("Form"` in active Quick Find code.
- Protected workspace gate only if runtime or smoke scripts change. Not required for this docs-only review.

## Deferred Scope

Defer these until separately designed and approved:

- Quick Find mutation actions.
- RFQ send/email or test-send.
- Contact creation/editing, User creation, portal provisioning, supplier portal links.
- Submit, approval, release, reject, cancel, amend, or conversion workflows.
- Receiving, billing, payment, Purchase Receipt, Purchase Invoice, Payment Entry execution.
- Item Price and Default Supplier result types or mutation.
- AI supplier quotation intake or AI-assisted Procurement Quick Find summaries.
- Native ERPNext form/list/report escape links.
- Supplier readiness issue result type.
- RFQ recipient readiness issue result type.
- PO follow-up queue result type, unless explicitly designed as a queue shortcut.

## Owner Decisions Needed

1. Should Phase 7G include report shortcuts in the first implementation, or keep first release record-only?
2. Should draft managed PR/RFQ/SQ/PO records open their managed form routes when editable, or should all document suggestions open review/follow-up pages first?
3. Should disabled suppliers and disabled buying items appear in Quick Find if the user can read them, with clear disabled chips, or be hidden by default?
4. Should supplier readiness status appear in Supplier suggestions/previews now that Phase 7E1 exists, or wait until Quick Find core records are stable?
5. Should Overview Quick Find show queue shortcuts, or should queue navigation stay exclusively in Overview cards and sidebar/worklists?
6. What is the maximum acceptable suggestion count for mobile and desktop?
7. Should Enter from the input ever activate Open after a preview is selected, or should Open require focus/click for stronger navigation safety?
8. Should Quick Find search child table fields immediately, matching Phase 7F worklists, or start with top-level fields and add child matching after performance testing?
9. Should Quick Find previews show totals/currency for SQ/PO when the user can read those documents, or keep financial values out of Overview search?
10. Should Quick Find be Purchase Manager prioritized in grouping/order, or identical for Purchase User and Purchase Manager except permissions/context?
