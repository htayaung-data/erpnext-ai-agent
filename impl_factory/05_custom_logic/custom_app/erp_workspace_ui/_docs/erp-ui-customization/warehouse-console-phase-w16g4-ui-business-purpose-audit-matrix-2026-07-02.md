# Warehouse Console Phase W16G4 UI / Business Purpose Audit Matrix

Date: 2026-07-02

## Scope

This document reopens W16G4 after owner live review found that the Warehouse workspace is not yet ready for true Workspace Closure. The issue is not limited to CSS polish. Several pages and cards still need clearer business purpose, stronger navigation affordance, better empty-state explanation, and a more consistent premium ERP visual system.

This is a docs-only audit and correction plan. It does not approve runtime implementation, live alignment, commit, push, restart, protected gates, ERPNext document execution, stock/accounting mutation, native ERP routes, notification/email/portal behavior, Sales/Procurement runtime mutation, or Warehouse Workspace Closure.

## Owner Findings That Reopened W16G4

- Grey borders are too dominant across new workflow pages, especially Internal Transfer and related custom workflow pages.
- Overview Manager Decision cards such as Review Transfer / Custom do not feel premium and do not clearly explain their business purpose.
- Some Overview cards and page components show text but do not provide useful information, clear navigation, or clear state.
- The new Returns, Internal Transfer, and Cycle Count pages do not yet consistently match the premium UI quality of Inbound Receiving, Outbound Picking, and Stock Exceptions.
- Empty or fallback states such as Not visible / empty posture panels can look broken instead of explaining role, source, scope, or next step.
- The owner expects page-by-page review before continuing toward Warehouse Workspace Closure.

## Product Principle

The Warehouse Overview should not be a collection of decorative boxes. It should work as an exception-led command center:

- Operational work starts from clear entry lanes.
- Manager work appears as review lanes with business consequence and route.
- Visibility pages explain what can be inspected and why.
- Every card is either a navigation card, a filter card, a KPI/status card, or it should be removed.
- Disabled or request-only controls must explain why they are disabled and what must happen first.
- ERP document actions remain outside Warehouse custom workflow pages unless a future owner/security-approved phase explicitly changes that.

## Page / Component Audit Matrix

| Area | Current issue | Decision | Required correction | Boundary |
| --- | --- | --- | --- | --- |
| Overview Start Warehouse Work | Good idea, but custom cards can still read like generic decorative tiles. | Redesign, keep navigable | Keep as primary navigation, but reduce visual noise and make card purpose explicit: queue, custom workflow, or visibility. | Custom routes only. |
| Overview Work Entry | Arrival and picking entries are useful queue gateways. | Keep | Keep as active navigable cards. Use operational labels and useful counts. | No Purchase Receipt, Delivery Note, Pick List, or stock mutation. |
| Overview Returns entry | Useful as navigation to the dedicated Returns Work Hub. | Keep, redesign | Use one concise navigation card. Do not duplicate return intake/supplier/manager details on Overview. | Custom Returns page only. |
| Overview Internal Transfer entry | Useful as navigation to custom transfer evidence page. | Keep, redesign | Make it read as "Record transfer intent" / "Review transfer posture", not as stock transfer execution. | No Stock Entry or stock movement. |
| Overview Cycle Count entry | Useful as navigation to custom count evidence page. | Keep, redesign | Make it read as count evidence / variance posture, not adjustment execution. | No Stock Reconciliation or stock adjustment. |
| Overview Manager Decisions | Currently mixes numeric review queues and custom workflow shortcuts in identical cards. | Redesign | Split into clear lanes: active queue reviews, custom workflow manager posture, and visibility reviews. Avoid "Custom" as a large metric value. | Review/navigation only. |
| Overview Return decisions | Duplicates the Returns destination without enough separate purpose. | Keep only if differentiated | Explain that this opens Returns Work Hub directly to manager posture, or remove if it cannot deep-link. | Manager posture only. |
| Overview Transfer decisions | Reads like a generic "Review transfer" card. | Redesign | Explain source-count posture and Inventory/Admin request boundary. Prefer direct route to Internal Transfer manager panel if implemented. | No Stock Entry. |
| Overview Inventory variance | Reads like a generic custom card. | Redesign | Explain variance posture and blocked adjustment document policy. Prefer direct route to Cycle Count manager panel if implemented. | No Stock Reconciliation. |
| Overview read-only visibility cards | Movement/Transfer visibility can overlap with Internal Transfer. | Clarify | Movement Visibility should mean posted movement inspection. Internal Transfer should mean custom transfer intent. Transfer Visibility should mean posted/inter-warehouse visibility. | No native document route. |
| Overview low-signal cards | Generic status cards with no route/filter create dashboard fatigue. | Remove or redesign | Any card without route, filter, or useful status explanation should be removed. | N/A |
| Sidebar | Custom workflow pages now route, but icon/readability must remain consistent. | Keep | Keep concise labels. Icons should indicate purpose, not fallback plus. | Custom routes only. |
| Inbound Receiving | Current quality benchmark. | Keep | Use as premium grammar template: command header, posture summary, evidence work panel, manager panel, policy panel. | Custom receiving task only. |
| Receiving Review manager decision panel | Owner found prior centered disabled cards weak. | Keep after alignment | Disabled cards must be left-aligned and explain exact blocker: manager-only, save draft first, or not decision-ready. | Manager gate remains server-side. |
| Outbound Picking | Current quality benchmark after W16C. | Keep | Use same header/action/button pattern for new pages. Empty states must explain unavailable source data. | Custom picking task only. |
| Picking fallback / Not visible states | Can look broken when customer/warehouse/date are not visible. | Redesign | Replace with role/source/scope explanation and a safe next step: Refresh, Back to outbound, or contact admin. | No native route. |
| Stock Exceptions | Strong concept, likely acceptable as premium baseline. | Keep with review | Ensure cards filter or navigate; empty state must mention current role/filter scope. | Read-only/custom review only. |
| Returns Work Hub | Good dedicated-page decision, but must avoid action clutter. | Keep, refine | Keep full-width lane model. Ensure customer/supplier/manager lanes are clear, aligned, and visually calm. | Custom return records only. |
| Customer Return lane | Functional but can become form-heavy. | Keep, refine | Use compact form grouping, clear save location, and status summary. Avoid badge clutter below buttons. | No Sales Return/Credit Note. |
| Supplier Return lane | Functional but can become form-heavy. | Keep, refine | Match Customer Return alignment and action placement exactly. Preserve overage/quality posture. | No supplier notification/Purchase Receipt return. |
| Return Decisions lane | Useful if it operates on saved custom records. | Keep | Explain why controls are disabled until a record exists; do not show as fake action. | Manager posture only. |
| Internal Transfer page | Live page is too border-heavy and form-dense. | Redesign | Apply the Inbound/Outbound premium grammar: command summary, quiet guardrail, candidate evidence work area, manager posture side panel, cleaner field grouping. | No Stock Entry, stock movement, ledger, balance. |
| Internal Transfer candidate status | Current "not recorded" state is useful but visually too dominant. | Redesign | Turn into a calm status strip with "What happens next" copy. | Custom candidate only. |
| Internal Transfer manager posture | Controls are valid but visually cramped and passive. | Redesign | Make manager lane explain unlock condition, role boundary, and decision result. | Server manager gate remains. |
| Cycle Count page | Needs more inventory-control purpose. | Redesign | Show count scope, blind/guided visibility, count evidence, variance posture, and manager review. Reduce generic form-wall feeling. | No Stock Reconciliation/Stock Entry. |
| Cycle Count empty state | "No count" can imply no control process. | Redesign | Explain "No custom count task recorded from this page yet" and what to save first. | Custom count task only. |
| Movement Visibility | Valuable read-only page. | Keep, refine | Position as posted movement evidence and operational trace, not ledger/accounting analysis. | No valuation/accounting/native route. |
| Transfer Visibility | Overlaps with Internal Transfer. | Clarify | Keep as posted/inter-warehouse visibility. Internal Transfer remains custom intent/evidence workflow. | No execution action. |
| Guardrail panels | Current dashed/bordered panels can dominate. | Redesign | Use quieter policy strips. Guardrails should support trust, not visually overpower the work. | Boundaries remain explicit. |
| Buttons | Header/back/refresh buttons must match shared premium style. | Standardize | Apply same spacing, border, hover, and typography across all Warehouse pages. | Navigation/refresh only. |
| Pills/chips | Some pills still read decorative. | Standardize | Use smaller quiet chips for identity/status. Reserve accent chips for custom-record-only or severity. | No native route. |
| Empty states | Several are too generic: Not visible, no activity, unavailable. | Redesign | Every empty state must include scope, reason, and safe next step. | No unsafe route. |

## Required Design Corrections Before Closure

1. Reframe Overview as command center, not dashboard box grid.
2. Reduce border dominance across custom workflow pages.
3. Standardize buttons, chips, panels, and guardrails across all Warehouse pages.
4. Clarify the business purpose of every Overview card.
5. Remove or redesign low-information cards that do not route, filter, or explain a useful state.
6. Upgrade Returns, Internal Transfer, and Cycle Count to the Inbound/Outbound quality bar.
7. Improve fallback states so unavailable data looks governed, not broken.
8. Keep all ERP document boundaries explicit but visually quiet.

## Proposed Implementation Sequence

### W16G4A - Overview Command Center Refactor

- Redesign Overview card hierarchy.
- Split cards into Work Entry, Manager Review, and Visibility.
- Remove oversized "Custom" metric treatment.
- Ensure every card routes, filters, or reads clearly as status-only.
- Add smoke assertions for routes and absence of stale/placeholder wording.

### W16G4B - Shared Premium UI System Pass

- Normalize Warehouse buttons, chips, guardrail strips, card borders, and empty states.
- Reduce dominant grey borders.
- Keep status color only for operational meaning.
- Apply to Overview, Returns, Internal Transfer, Cycle Count, Receiving, and Picking without changing backend behavior.

### W16G4C - Internal Transfer Page Redesign

- Keep existing custom save/manager behavior.
- Redesign layout around transfer intent, source count evidence, manager posture, and policy boundary.
- Improve candidate-not-recorded and manager-disabled explanations.
- Validate no Stock Entry, stock movement, ledger, balance, native route, or valuation exposure.

### W16G4D - Cycle Count Page Redesign

- Keep existing custom save/manager behavior.
- Redesign around count scope, blind/guided visibility, count evidence, variance posture, and manager review.
- Improve no-task and manager-disabled explanations.
- Validate no Stock Reconciliation, Stock Entry, stock adjustment, native route, or valuation exposure.

### W16G4E - Returns Hub Final Polish

- Keep dedicated Returns Work Hub approach.
- Tighten customer/supplier lane field grouping and save-button alignment.
- Keep manager posture lane clear and non-deceptive.
- Validate no Sales Return, Credit Note, return Purchase Receipt, notification, stock mutation, or native route.

### W16G4F - Empty State And Route Quality Gate

- Review all pages for Not visible / blank / unavailable states.
- Each fallback must explain role/scope/source and provide a safe next action.
- Smoke-check all top-level Warehouse routes and key detail routes.

### W16G4G - Final Owner Manual Review Package

- Produce a concise manual checklist for owner review page by page.
- Only after owner acceptance should W16H Warehouse Workspace Closure be considered.

## Closure Blockers

- Overview cards still feel decorative or ambiguous.
- Internal Transfer and Cycle Count pages do not yet match Inbound/Outbound premium quality.
- Any card that looks clickable but does not navigate/filter.
- Any empty state that looks broken or unexplained.
- Any live mismatch between source and browser-loaded assets.
- Any new native ERP route exposure or ERP document action.

## Non-Blocking Polish

- Microcopy improvements where business meaning is already clear.
- Minor spacing adjustments that do not affect hierarchy.
- Additional icon refinements after the card/page purpose is fixed.

## Validation Required For Each Patch Batch

- `git diff --check HEAD`
- JS syntax checks for changed Warehouse JS and affected smoke files.
- `python3 -m compileall -q erp_workspace_ui`
- Full unit discovery for Warehouse contract tests.
- Targeted static scans for native routes, ERP document actions, stock/accounting mutation, valuation/commercial exposure, notification/email/portal behavior, and Sales/Procurement runtime mutation.
- Cache artifact cleanup/check.
- Owner manual review for visible UI batches.

## Boundary Confirmation

This audit does not implement or approve Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, return Purchase Receipt, Purchase Invoice return, debit note, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, reserve/unreserve, stock movement, stock posting, valuation/accounting/commercial exposure, notification/email/portal behavior, native ERP document routes, Sales runtime mutation, Procurement runtime mutation, live alignment, restart, protected gate, commit, push, or Warehouse Workspace Closure.
