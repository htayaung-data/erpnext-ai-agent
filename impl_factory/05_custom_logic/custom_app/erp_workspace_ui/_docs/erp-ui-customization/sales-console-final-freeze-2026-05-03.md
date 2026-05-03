# Sales Console Final Freeze

Date: 2026-05-03
Status: Frozen
Freeze marker tag: `sales-console-freeze-v1`
Branch: `feature/erpnext-ui-design`
Frozen implementation baseline before final freeze marker: `3b071b0 docs: define workspace UI golden rule standard`
Owner decision: accepted for Sales Console freeze

## 1. Freeze Decision

Sales Console is frozen as the first enterprise-grade workspace reference for this UI project.

The freeze means:

1. current Sales Console UI behavior is accepted as the working baseline
2. current shared shells and route ownership are accepted as the reference pattern
3. current report family is accepted
4. current Customers and Items directory/detail behavior is accepted
5. current managed Quotation, Sales Order, Delivery Note, and Sales Invoice overlays are accepted for this workspace
6. current docs and tests are aligned with the confirmed UI
7. future workspace work must start from the Golden Rule standard, not from old screenshots or draft notes

## 2. Frozen Scope

Frozen Sales Console surfaces:

1. `/desk/sales-console`
2. `/desk/sales-console-worklist/<queue-key>`
3. `/desk/sales-console-worklist/customer-detail/<customer>`
4. `/desk/sales-console-worklist/customer-editor/<customer>`
5. `/desk/sales-console-worklist/customer-editor`
6. `/desk/sales-console-worklist/item-detail/<item>`
7. `/desk/sales-console-report/<report-key>`
8. managed ERP forms for Quotation, Sales Order, Delivery Note, and Sales Invoice

Frozen sidebar destinations:

1. Overview
2. Quotations
3. Sales Orders
4. Customers
5. Items

Frozen report family:

1. Sales Analytics
2. Sales Order Analysis
3. Trend Analysis
4. Lost Quotations
5. Collections Status
6. Item-wise Sales History

## 3. Accepted Compatibility Rules

Compatibility routes remain accepted only as controlled aliases:

1. `quotation_trends` maps into `Trend Analysis` with Quotation selected
2. `payment_terms_status_sales_order` maps into `Collections Status`

The standalone Sales Dashboard remains removed.

## 4. Post-Freeze Multi-Workspace Foundation

After freeze, Sales Console was mapped into the shared workspace registry so future workspaces can reuse the shared shells without copying Sales Console-specific route assumptions.

This foundation does not rename or weaken the frozen Sales Console contract.

Frozen route names remain:

1. `sales-console-home`
2. `sales-console`
3. `sales-console-worklist`
4. `sales-console-report`

Future workspaces must receive their own registry definitions and must not rewrite these frozen Sales Console routes to appear generic.

## 5. Freeze Evidence

Accepted evidence before freeze:

1. JavaScript syntax checks passed.
2. Python compile checks passed.
3. Sales Console unit and contract tests passed.
4. Docker Playwright role smoke passed for Sales Manager and Sales User.
5. Sales Order Analysis smoke passed for Sales Manager and Sales User.
6. Full live route probe passed for 24 Sales Manager routes and 21 Sales User routes.
7. Restricted-route checks passed for Sales User.
8. Socket.IO connected cleanly after the Caddy origin-forwarding fix.
9. Active docs were aligned with final code and pushed.
10. Shared Component and Implementation Golden Rule Standard was created and pushed.

## 6. Accepted Boundaries

These are accepted boundaries, not freeze blockers:

1. Overview first-load movement is a Desk-level/Frappe shell concern and is deferred unless it becomes visibly disruptive after future platform changes.
2. No standalone Sales Dashboard is frozen; the page was removed because it overlapped with Sales Analytics and did not provide enough distinct enterprise value.
3. AI expansion is not part of this freeze; current AI Assist behavior remains read-only and non-authoritative.
4. The current freeze does not prove every possible future role family.
5. Additional customer save-persistence proof is not required for this freeze because no new mutation expansion is being introduced now; future mutation changes must run a controlled save regression with an approved or disposable record.

## 7. Change Control After Freeze

After this freeze, any Sales Console change must include:

1. reason for change
2. affected page or shared component
3. route and permission impact
4. tests or browser checks run
5. docs updated if behavior changes
6. explicit decision whether the freeze tag remains historical only or a new freeze tag is needed

Do not silently change the frozen Sales Console baseline while starting another workspace.

## 8. Next Workspace Rule

Future workspace work must begin from:

1. `shared-component-and-implementation-golden-rule-standard-v1.md`
2. `enterprise-shared-ui-component-standard-v1.md`
3. `enterprise-shared-ui-component-implementation-contract-v1.md`
4. the current shared runtime code
5. this final freeze note

Sales Console is now the reference implementation. It is not a template to copy blindly.
