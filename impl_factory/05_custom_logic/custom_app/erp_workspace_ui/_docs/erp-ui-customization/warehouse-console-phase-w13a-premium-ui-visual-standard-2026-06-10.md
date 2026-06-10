# Warehouse Console Phase W13A Premium UI Visual Standard

Date: 2026-06-10

Branch: `feature/erpnext-ui-design`

Decision: `proceed_to_w13b_shared_visual_foundation`

Status: docs-only visual audit and implementation standard. W13A does not change Warehouse runtime, service methods, routes, tests, smokes, registry, governance, hooks, fixtures, live files, Sales runtime, or Procurement runtime.

## 1. Executive Decision

W13A recommends proceeding to `proceed_to_w13b_shared_visual_foundation`.

W13 is the final Warehouse visual harmonization phase after W12A-W12K completed read-only structural polish across the current Warehouse surfaces. W13 must focus on visual quality, component consistency, responsiveness, and evidence standards only. It does not approve receiving execution, picking execution, transfer execution, backend expansion, native ERPNext navigation, valuation exposure, Quick Find/Search, or broader data access.

Warehouse is now structurally functional and protected, but it is still visually less mature than the accepted Sales and Procurement consoles. The next phase should consolidate Warehouse-specific visual primitives first, then apply them page by page. This reduces the risk of each page continuing to drift through local one-off card, row, chip, header, fallback, and guardrail styles.

## 2. Current Warehouse Surface Inventory

Source reviewed for W13A:

- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
- `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- W12 focused smoke files under `ui_smoke/warehouse_phase_w12*.js`
- `_docs/erp-ui-customization/README.md`
- recent Warehouse W8-W12 design and baseline notes listed in the README

### `/desk/warehouse-console`

- Current role in workflow: Warehouse landing and cockpit for all read-only Warehouse starts.
- Current visual strengths: W12K adds command header, chips, Start Here, Work To Do, Risk, Movement, Transfer Visibility, and explicit read-only guardrail.
- Current visual weaknesses: the cockpit still mixes several local card families; Start Here and route sections can feel dense; transfer and movement cards are close in language; page needs a stronger common primitive system before final polish.
- W13 priority: high.
- Needed change: visual token/component refinement, not structure change.

### `/desk/warehouse-console-worklist/inbound-receiving`

- Current role in workflow: read-only supplier-side receiving queue from open submitted purchase orders.
- Current visual strengths: grouped receiving posture, filters, cards, and row drilldown into custom receiving review.
- Current visual weaknesses: PO cards and row cards are serviceable but not yet as layered as Sales action cards or Procurement readiness/Quick Find panels; filter/action strip and group hierarchy need tighter rhythm.
- W13 priority: high.
- Needed change: visual token/component refinement; no route or data structure change.

### `/desk/warehouse-console-receiving/<purchase-order>`

- Current role in workflow: read-only object review for one purchase order receiving posture.
- Current visual strengths: W12A introduced a stronger command header, readiness summary, item-line scan layout, custom receipt history, and guardrail copy.
- Current visual weaknesses: item lines and receipt history still need clearer separation, consistent row facts, and stronger object-page hierarchy comparable to Procurement detail tabs.
- W13 priority: high.
- Needed change: visual token/component refinement; no receiving action.

### `/desk/warehouse-console-worklist/outbound-picking`

- Current role in workflow: read-only customer-side picking queue from open submitted sales orders.
- Current visual strengths: grouped outbound posture, filters, cards, and route-safe drilldown into custom picking review.
- Current visual weaknesses: Sales Order row cards should better match Picking Review detail hierarchy; shortage/readiness signals need a calmer visual hierarchy.
- W13 priority: high.
- Needed change: visual token/component refinement; no picking execution.

### `/desk/warehouse-console-picking/<sales-order>`

- Current role in workflow: read-only object review for one sales order picking posture.
- Current visual strengths: custom Warehouse shell, read-only sales order identity, stock readiness and item line posture.
- Current visual weaknesses: readiness facts and item rows need improved scan rhythm; related stock posture links need the same card treatment as other detail pages.
- W13 priority: high.
- Needed change: visual token/component refinement; no Pick List or Delivery Note action.

### `/desk/warehouse-console-worklist/stock-exceptions`

- Current role in workflow: read-only exception board for shortage risk, inbound cover, urgent demand, and missing posture.
- Current visual strengths: groups and safe custom route drilldowns are in place; W12E added stronger structure.
- Current visual weaknesses: exception cards can feel visually heavy; expanded row evidence and grouping need clearer density rules; risk colors should be restrained and consistent.
- W13 priority: high.
- Needed change: visual token/component refinement; no route/data expansion.

### `/desk/warehouse-console-stock-exception/<encoded-context>`

- Current role in workflow: read-only exception review for one demand/item/warehouse context.
- Current visual strengths: demand, stock posture, inbound cover, recommended review, related route panels, and controlled fallback states exist.
- Current visual weaknesses: recommended review and related cards need stronger visual hierarchy; low-detail fallback states should look intentionally premium instead of sparse.
- W13 priority: high.
- Needed change: visual token/component refinement; no data leak or action.

### `/desk/warehouse-console-stock-posture/<encoded-context>`

- Current role in workflow: read-only item/warehouse posture review reached from Warehouse context.
- Current visual strengths: posture facts, inbound cover, outbound demand, freshness, and related custom routes are present.
- Current visual weaknesses: posture facts and related review sections need clearer grouping and less repetition; source context should be easier to understand.
- W13 priority: medium.
- Needed change: visual token/component refinement; no generic stock lookup.

### `/desk/warehouse-console-worklist/movement-visibility`

- Current role in workflow: read-only board for posted movement visibility.
- Current visual strengths: grouped movement records, safe filters, posted movement copy, and route-safe Movement Review links.
- Current visual weaknesses: movement facts repeat between summary cards, row cards, and group notes; needs clearer distinction between movement summary and row detail.
- W13 priority: medium.
- Needed change: visual token/component refinement; no Stock Ledger or Stock Entry exposure.

### `/desk/warehouse-console-movement/<encoded-context>`

- Current role in workflow: read-only object review for one posted movement.
- Current visual strengths: movement identity, source/target posture, line facts, custom stock posture drilldowns, and guardrail exist.
- Current visual weaknesses: source-to-target direction should be visually stronger; line card hierarchy should distinguish movement-level facts from item-line facts.
- W13 priority: medium.
- Needed change: visual token/component refinement; no transfer or stock execution.

### `/desk/warehouse-console-worklist/transfer-visibility`

- Current role in workflow: read-only transfer posture board from submitted material-transfer Stock Entries.
- Current visual strengths: W12J adds command header, chips, summary cards, row fact panels, custom Movement Review and Stock Posture drilldowns, and guardrail.
- Current visual weaknesses: summary cards and row facts can duplicate each other; transfer posture needs clearer distinction from general Movement Visibility.
- W13 priority: medium.
- Needed change: visual token/component refinement; no transfer execution.

## 3. Cross-Console Comparison

### Command Header Quality

Sales has the strongest command header: dark premium surface, strong title scale, subtle depth, role context, and KPI grouping. Procurement inherits much of the Sales shell language and uses shared runtime primitives with clear object/workbench purpose. Warehouse now has command headers across surfaces, but most are locally styled, lighter, and less visually decisive. W13 should not copy the Sales dark hero literally, but Warehouse needs comparable confidence, consistent header anatomy, and stronger surface depth.

### Card Depth And Hierarchy

Sales cards use elevation, icon blocks, hover states, and consistent action strips. Procurement uses shared action/insight/queue primitives and readiness panels that feel intentionally composed. Warehouse has many cards, but the card families differ across cockpit, inbound/outbound, stock exceptions, posture, movement, and transfer pages. W13 should standardize card depth, border weights, internal spacing, and state treatments.

### Typography Rhythm

Sales has clearer type scale separation between page title, section title, card title, metric value, and meta text. Procurement follows this rhythm through shared classes. Warehouse uses readable text but often keeps titles, notes, row facts, and card labels close in size and weight. W13 should define exact type tiers and prevent overuse of uppercase micro-labels.

### Color System

Sales uses a dark slate/teal premium header with controlled accent usage. Procurement uses the same shared base with procurement-specific behavior. Warehouse currently uses off-white, slate, green/teal, and amber risk accents, which is appropriate, but it needs tighter token discipline. W13 should keep Warehouse distinct, avoid purple/default AI visual bias, and define green/teal as operational, amber as attention, red only for critical blockers, and slate as neutral structure.

### Chips And Status Treatment

Sales and Procurement chips are consistent in size, casing, and role/status meaning. Warehouse chips exist, but chip sizing and use varies by surface. W13 should define command chips, row status chips, risk chips, and disabled/unavailable chips separately.

### Row Density

Sales worklists and Procurement object pages are dense but scannable. Warehouse rows sometimes repeat facts already visible in summary cards and can feel heavier than needed. W13 should use row facts sparingly: identity, posture, date/age, quantity, route action. Long details should be under expansion or detail pages.

### Action Placement

Sales and Procurement actions have predictable placement and style. Warehouse actions are custom-route-only, but placement varies by row, panel, and page. W13 should define a single action strip pattern: Back/Refresh at command level, custom review links at card/row/footer level, no disabled execution buttons.

### Empty And Unavailable States

Sales and Procurement empty states are visibly framed and explanatory. Warehouse has safe empty/unavailable states, but low-detail fallbacks can look sparse. W13 should make fallback panels visibly intentional, with a header, short explanation, and safe next step.

### Responsive Behavior

Warehouse W12 smokes cover desktop/laptop/mobile patterns and horizontal overflow negatives. Sales and Procurement still feel more mature on narrower screens because their shared primitives wrap consistently. W13 should standardize Warehouse mobile wrapping, full-width buttons where needed, collapsed sidebar evidence, and one-column object page behavior.

### Sidebar And Chrome Consistency

W10C removed duplicated Frappe page-head chrome across Warehouse routes. W12K hardens cockpit duplicate-sidebar/page-head evidence. Sales and Procurement are already more mature in shared chrome usage. W13 should preserve the current route ownership and not edit shared sidebar runtime unless a visual issue is proven and protected by Sales/Procurement gates.

### Screenshot And Smoke Evidence

Warehouse now has focused W12 smokes for each polished surface. Sales and Procurement freeze packages also include protected gate evidence. W13 should require visual evidence across all changed surfaces, not just selector-only assertions.

## 4. Warehouse Premium UI Design Principles

- Keep the console a read-only cockpit/workbench. Every visual cue should support review, planning, and exception comprehension, not execution.
- Prefer operational clarity over decoration. Do not add decorative blobs, marketing-style hero treatment, or generic dashboard ornamentation.
- Reduce repeated facts. A fact should appear in the command header, summary cards, row facts, or detail panel only when it helps the task at that level.
- Strengthen hierarchy between page title, command facts, summary cards, groups, rows, details, and guardrails.
- Use consistent guardrails. Guardrails should be visible, calm, and owner-facing, not developer-facing.
- Style custom-route-only actions consistently. Review links must stay inside Warehouse routes and must not look like lifecycle commands.
- Do not add disabled execution buttons. A missing execution action should not be represented by a greyed button.
- Make mobile wrapping a first-class rule. At 390px, cards, filters, facts, row actions, and guardrails must wrap without horizontal overflow.
- Keep bounded density. Use summary cards and grouped rows, not unbounded raw ERPNext lists.
- Avoid purple/default-AI visual bias. Warehouse should use off-white, slate, green/teal, and amber accents with disciplined contrast.
- Match Sales/Procurement quality while retaining Warehouse identity. The goal is comparable polish, not visual sameness.

## 5. Shared Visual Foundation Specification

### Command Header

- Purpose: establish page identity, role/scope, freshness, and allowed safe controls.
- Visual treatment: elevated panel, strong title, short subtitle, command chips, optional fact strip, Back/Refresh aligned consistently.
- Density rules: one title, one subtitle, three to five chips/facts; avoid repeating row-level counts.
- Responsive behavior: controls wrap below title at narrow widths; no two-column command layout below 900px.
- Accessibility/focus: visible focus ring on Back, Refresh, and custom route buttons.
- Smoke selector expectation: one command/header selector per page, one shell, no visible Frappe page-head duplication.

### Command Chips

- Purpose: show read-only status, workspace scope, freshness, and page posture.
- Visual treatment: compact rounded chips with consistent height, uppercase label only when brief.
- Density rules: no more than five; no chip should contain long sentences.
- Responsive behavior: wrap naturally; never overflow row.
- Accessibility/focus: chips are informational unless interactive; interactive chips must be buttons with focus state.
- Smoke selector expectation: page-specific chip selectors where W12/W13 smokes already use them.

### Fact Strip

- Purpose: summarize the most important operational facts for the page.
- Visual treatment: grid of quiet fact cards, stronger label/value separation, no heavy borders between every fact.
- Density rules: four to six facts for command summaries; item/detail pages may use two tiers only if justified.
- Responsive behavior: 4 columns at wide desktop, 2 columns at laptop, 1 column at mobile.
- Accessibility/focus: fact labels and values must remain readable without relying on color only.
- Smoke selector expectation: stable fact selectors for command facts and row facts.

### Summary Card Grid

- Purpose: communicate queue/posture totals and top states.
- Visual treatment: consistent card height, title, value, short note, optional state accent.
- Density rules: four cards preferred; six maximum only for cockpit pulse.
- Responsive behavior: 4/2/1 grid based on width.
- Accessibility/focus: no clickable card unless it is visibly a route action and keyboard reachable.
- Smoke selector expectation: summary card count and no horizontal overflow.

### Row Card Shell

- Purpose: make each queue row scannable without becoming a native ERPNext table.
- Visual treatment: identity column, status/date/warehouse/quantity facts, short explanation, action strip.
- Density rules: one primary ID, one secondary party/item, three to five facts, optional expansion for detail.
- Responsive behavior: one-column row cards at mobile; actions wrap below facts.
- Accessibility/focus: row action buttons must have visible focus and descriptive labels.
- Smoke selector expectation: row shell selectors and route target selectors.

### Row Fact Blocks

- Purpose: expose operational facts such as warehouse, due date, quantity, posture, or urgency.
- Visual treatment: compact label/value blocks with clear label hierarchy.
- Density rules: avoid repeating the exact summary card label/value in every row unless it is row-specific.
- Responsive behavior: facts wrap to one column on mobile.
- Accessibility/focus: text must not truncate critical document IDs.
- Smoke selector expectation: row fact selectors for pages that support expansion/detail.

### Action Strip

- Purpose: hold safe controls and custom review links.
- Visual treatment: quiet buttons, consistent size, aligned right on desktop and full-width/stacked on mobile where needed.
- Density rules: Back and Refresh in command header; custom drilldowns in row/detail related panels.
- Responsive behavior: wrap without overflow; no icon-only actions without accessible label.
- Accessibility/focus: visible focus ring; Enter/Space activates buttons.
- Smoke selector expectation: custom route targets only; no native route href/action.

### Tabs

- Purpose: reduce long vertical stacks on detail pages.
- Visual treatment: simple segmented/tab row, active state obvious, content panel framed.
- Density rules: only use tabs when there are distinct categories; do not create one-item tabs.
- Responsive behavior: tabs wrap or scroll inside their own container without page overflow.
- Accessibility/focus: tab buttons must be keyboard reachable and active state must be exposed.
- Smoke selector expectation: active tab, panel count, and no duplicate shell.

### Guardrail Panel

- Purpose: remind users the page is read-only and does not perform stock/accounting changes.
- Visual treatment: calm framed footer/panel, not a warning banner unless risk is immediate.
- Density rules: one to two sentences; no developer/governance wording.
- Responsive behavior: full-width under content; never hidden on mobile.
- Accessibility/focus: plain text, sufficient contrast.
- Smoke selector expectation: one guardrail selector per surface after W13C.

### Fallback/Unavailable Panel

- Purpose: show restricted, unavailable, empty, or low-detail states without broken UI.
- Visual treatment: intentional empty panel with title, short explanation, and safe next step if any.
- Density rules: no raw framework errors; no stack traces; no hidden data leaks.
- Responsive behavior: centered or full-width readable block on mobile.
- Accessibility/focus: message readable and not color-only.
- Smoke selector expectation: unavailable/empty selectors accepted where live data can be empty.

### Related-Review Cards

- Purpose: route to another custom Warehouse review page when safe context exists.
- Visual treatment: card with title, why it matters, and one custom route action.
- Density rules: only show when the route is safe and context is visible; otherwise show an unavailable card.
- Responsive behavior: 2 columns desktop, 1 column mobile.
- Accessibility/focus: action label must describe the route, not imply execution.
- Smoke selector expectation: route must start with a Warehouse custom route key.

### Mobile Collapsed Layout

- Purpose: keep Warehouse usable at 390px without page overflow or hidden critical actions.
- Visual treatment: one-column content, wrapped chips, full-width action strips where needed.
- Density rules: collapse facts before hiding them; do not shrink text below readable size.
- Responsive behavior: no horizontal overflow at 390px; sidebar collapsed evidence required.
- Accessibility/focus: focus ring remains visible after wrapping.
- Smoke selector expectation: mobile screenshot and horizontal overflow check.

### Loading State

- Purpose: indicate data is loading without flashing native Desk content or duplicate shells.
- Visual treatment: same command shell skeleton as the final page, with minimal loading copy.
- Density rules: no long diagnostic lists.
- Responsive behavior: same layout constraints as final shell.
- Accessibility/focus: do not trap focus; no disappearing controls that shift layout aggressively.
- Smoke selector expectation: loading state must not satisfy ready-state assertions.

## 6. Page-By-Page W13C Checklist

### Cockpit

- Reduce crowding in Start Here by making five route cards visually balanced.
- Make Start Here, Work To Do, Risks To Resolve, Movement To Understand, and Transfer Visibility visually distinct without adding route complexity.
- Keep Transfer Visibility as a top-level start but clarify it is posted transfer posture, not transfer execution.
- Normalize command chips, pulse cards, route cards, and guardrail treatment.

### Inbound Queue

- Align PO cards with Receiving Review hierarchy.
- Make overdue/due/partial/expected groups visually distinct without heavy color.
- Keep filters compact and locally scoped.
- Ensure row action reads as a safe review path only.

### Receiving Review

- Refine item line density and make ordered/received/remaining quantities easier to compare.
- Separate receipt history from item lines with a different panel rhythm.
- Keep guardrail visible and specific: no stock posting and no Purchase Receipt creation.

### Outbound Queue

- Align Sales Order row cards with Picking Review detail facts.
- Make customer, due date, pending quantity, and readiness state easy to scan.
- Keep row route action inside `/desk/warehouse-console-picking/<sales-order>`.

### Picking Review

- Polish stock readiness tab/panel and item line scan.
- Reduce repeated availability facts when the same posture appears in header and rows.
- Make related Stock Posture links visually consistent with other detail pages.

### Stock Exceptions Queue

- Reduce visual heaviness in exception cards and expanded rows.
- Improve evidence of detail expansion and custom drilldown availability.
- Keep risk accents restrained and not alarming for informational rows.

### Stock Exception Review

- Improve recommended review cards and fallback state.
- Ensure low-detail/unavailable state still looks intentional and premium.
- Keep custom route cards clearly separate from facts.

### Stock Posture Review

- Clarify posture facts, inbound cover, outbound demand, and related review sections.
- Avoid making Stock Posture look like a generic stock search page.
- Ensure freshness/context is visible but not overemphasized.

### Movement Visibility

- Reduce repeated movement facts across summary, group, and row levels.
- Clarify grouping: receipts, issues, internal movement, adjustments/repack, needs review.
- Keep the row drilldown clearly labeled as review, not Stock Entry.

### Movement Review

- Improve source/target direction with a clear directional panel.
- Separate movement-level facts from item-line facts.
- Keep Stock Posture links route-safe and visually secondary.

### Transfer Visibility

- Reduce summary duplication between transfer cards and row facts.
- Clarify transfer posture compared with general Movement Visibility.
- Keep custom Movement Review and Stock Posture drilldowns only.

## 7. Forbidden Boundary

W13 must not add or change:

- backend methods
- document writes
- `create`, `save`, `submit`, `cancel`, `amend`, `delete`, `set_value`, `new_doc`, or `enqueue`
- Purchase Receipt, Pick List, Delivery Note, Stock Entry, or Stock Reservation creation
- receiving, picking, shipping, transfer, reconciliation, reservation, approval, rejection, barcode, or scan execution
- native ERPNext Form/List/Report routes
- Stock Ledger, Stock Balance, or Stock Reconciliation exposure
- valuation, accounting, GL, tax, margin, profit, rate, amount, price, cost, landed cost, billing, payment, or commercial fields
- Quick Find/Search
- print, email, portal, AI, workflow, or background job behavior
- Sales runtime changes
- Procurement runtime changes

## 8. Smoke And Evidence Requirements

W13B/W13C must produce evidence before commit:

- source focused smoke for every changed surface
- screenshots at 1440px, 1240px, 1136px, and 390px where relevant
- mobile sidebar collapsed evidence for cockpit and representative worklists/detail pages
- no duplicate page head, sidebar, top-left icon, shell, header, or route chrome
- no horizontal overflow at every required viewport
- repeated route navigation does not duplicate shell, header, sidebar, or refetch unnecessarily
- Refresh intentionally reloads where applicable
- custom route drilldowns only
- negative scans for native routes, lifecycle verbs, write calls, valuation/accounting/commercial terms, Quick Find/Search, and protected workspace dirty boundaries
- protected source gate before commit, run by Main Control
- live smoke and protected live gate after live alignment, run by Main Control only

Smoke evidence should include selector assertions and screenshots. Screenshot evidence matters because W13 is a visual harmonization phase, and selector-only proof is not enough to judge final quality.

## 9. Acceptance Criteria

W13 succeeds when:

- Warehouse visual quality is comparable to Sales and Procurement while retaining Warehouse identity.
- All Warehouse surfaces use consistent premium primitives for command headers, chips, fact strips, summary cards, row shells, action strips, guardrails, fallback states, and related review cards.
- Pages remain read-only and custom-route-only.
- No Warehouse execution capability, native route escape, valuation/accounting/commercial exposure, or Quick Find/Search is added.
- Sales and Procurement protected baselines remain unchanged.
- Owner can manually review screenshots without having to infer whether a page is polished or safe.
- Mobile and laptop layouts are readable with no horizontal overflow.

## 10. Recommended W13 Sequence

1. **W13B shared Warehouse visual foundation**
   - Create/refine shared Warehouse visual primitives inside existing Warehouse runtime only.
   - Scope should be styling and markup normalization for accepted selectors, not backend or route expansion.
   - Produce source smoke and screenshot evidence for representative surfaces.

2. **W13C1 Cockpit and top-level worklists**
   - Apply W13 primitives to Cockpit, Inbound Receiving, Outbound Picking, Stock Exceptions, Movement Visibility, and Transfer Visibility.
   - Prioritize route cards, summary cards, filter/action strips, row card shells, and guardrails.

3. **W13C2 Receiving and Picking review pages**
   - Apply object-page hierarchy to Receiving Review and Picking Review.
   - Prioritize command facts, item lines, related custom routes, and history/stock readiness panels.

4. **W13C3 Stock exception and posture pages**
   - Apply W13 primitives to Stock Exceptions Queue, Stock Exception Review, and Stock Posture Review.
   - Prioritize fallback states, related-review cards, and posture fact clarity.

5. **W13C4 Movement and Transfer pages**
   - Apply W13 primitives to Movement Visibility, Movement Review, and Transfer Visibility.
   - Prioritize source/target direction, row fact reduction, and posted movement/transfer language.

6. **W13D final cross-surface smoke and evidence hardening**
   - Run full W13 screenshot/evidence pass across all Warehouse surfaces.
   - Confirm no duplicate chrome, no horizontal overflow, no native route escape, and no forbidden scope.

7. **Security/Stability review**
   - Confirm no data-scope, route, API, permission, or write behavior changed.

8. **Operation review**
   - Confirm owner-facing copy and page hierarchy support daily warehouse review work.

9. **Main Control gates, commit, and live alignment**
   - Main Control runs protected source gates, commits, pushes, live-aligns, and runs live protected gates.

