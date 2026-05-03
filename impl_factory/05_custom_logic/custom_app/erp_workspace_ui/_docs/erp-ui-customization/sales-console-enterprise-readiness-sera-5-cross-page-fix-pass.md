# Sales Console Enterprise Readiness Audit: SERA-5 Cross-Page Fix Pass

Date: 2026-04-28
Final verification update: 2026-05-03
Final freeze update: 2026-05-03
Status: Frozen after automated checks and owner visual acceptance
Audit phase: `SERA-5` Cross-Page Fix Pass
Depends on:

1. `enterprise-shared-ui-component-standard-v1.md`
2. `enterprise-shared-ui-component-implementation-contract-v1.md`
3. `sales-console-enterprise-readiness-sera-1-route-ownership.md`
4. `sales-console-enterprise-readiness-sera-2-security-permissions.md`
5. `sales-console-enterprise-readiness-sera-3-visual-stability.md`
6. `sales-console-enterprise-readiness-sera-4-page-archetypes.md`

## 1. Purpose

This note records the cross-page fix pass after the route, security, visual, and archetype audits.

SERA-5 is not a redesign phase.

Its job is to fix only the shared issues that would damage the next workspace if copied forward.

## 2. SERA-5 Decision

SERA-5 decision:

`Final automated freeze checks passed and owner visual acceptance recorded`

Reason:

1. No new high-risk security or mutation blocker was found during the static pass.
2. Route ownership remains centralized through shared Sales Console helpers.
3. Customer detail and editor routes remain addressable and refresh-safe by design.
4. Directory, queue, report, and customer profile shells use shared components rather than page-local hacks.
5. The remaining implementation-facing user copy found in shared fallback states was corrected.
6. User-facing scope and route wording was softened into business-safe language.
7. Live Sales Manager/Sales User browser and permission smoke passed for the core Sales Console route, directory, report, and customer-management gate.
8. Full live route probing passed on 2026-05-03 for 24 Sales Manager routes and 21 Sales User routes.
9. Socket.IO realtime connection passed after forwarding `Origin` through the Caddy `/socket.io` proxy.

## 3. Fix Priority Register

| Priority | Status | Decision |
| --- | --- | --- |
| Security and permission defects | Core role gate passed | Additional save-persistence proof is deferred unless a future mutation change introduces risk or a disposable customer record is approved. |
| Route ownership defects | Browser route probe passed | Freeze accepted; future non-productized destinations require separate route review. |
| Data persistence defects | No new code blocker found | Customer create/edit save remains fixed; future mutation changes require controlled save regression. |
| Shared component instability | Browser route probe passed | Freeze accepted after owner visual acceptance. |
| Major visual alignment defects | No blocking issue found | Freeze accepted; future visual changes must follow the Golden Rule standard. |
| Confusing business copy | Fixed in this phase | Shared fallback, scope, route, and payment schedule copy hardened. |
| Page-local polish | Deferred | Do not block SERA-6 unless browser review finds a copied-pattern defect. |

## 4. Fixes Applied In SERA-5

### 4.1 Shared List And Report Fallback Copy

Files:

1. `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
2. `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`

Change:

1. Replaced implementation-facing fallback text such as `No list structure defined`.
2. Replaced `Columns were not configured for this list/report surface`.
3. New copy tells the user the Sales Console view or report is not ready and suggests refresh or return to console.

Why this matters:

This fallback is shared. If a future workspace forgets columns, the user should see a controlled product message, not internal setup language.

### 4.2 Report And Worklist Guard Copy

Files:

1. `erp_workspace_ui/sales_console/report.py`
2. `erp_workspace_ui/sales_console/worklist.py`

Change:

1. Replaced `route unavailable` and `unsupported route` wording in user-facing states.
2. Replaced unsupported queue fact copy with a business-safe instruction.
3. Replaced `operational slices` with `focused views` on directory pages.

Why this matters:

Sales users should not be asked to understand routes, keys, surfaces, or implementation mechanics.

### 4.3 Scope And Visibility Copy

File:

1. `erp_workspace_ui/sales_console/service.py`

Change:

1. Replaced `permission scope fallback` wording with `current access`.
2. Replaced `commercial chain scope applied` with linked-document language.
3. Replaced manager/executive `scope` wording with review visibility language.
4. Replaced AI fallback confidence wording from linked ERP permission scope to linked documents visible to current access.

Why this matters:

Scope is an implementation concept. The user needs to understand what records are visible, not why the backend used a particular filter mode.

### 4.4 Payment Schedule Copy

Files:

1. `erp_workspace_ui/public/js/quotation_form.js`
2. `erp_workspace_ui/public/js/sales_order_form.js`
3. `erp_workspace_ui/public/js/sales_invoice_form.js`

Change:

1. Replaced `Payment structure is not configured yet`.
2. Replaced `Payment schedule is not configured yet`.
3. New standard wording: `Payment schedule is not set up yet`.

Why this matters:

The copy now sounds like business workflow language rather than system setup language.

## 5. Route Ownership Static Result

Static result:

`Pass after browser smoke`

Final browser update:

Full live route probing passed on 2026-05-03 for both Sales Manager and Sales User. Keep this section as a regression checklist, not as an open blocker.

Reviewed route owner:

1. `routeToSalesConsoleTarget`
2. `routeToWorklist`
3. `routeToDoc`
4. `routeToList`
5. managed sidebar active-state resolver

Current route behavior by policy:

1. Customer form links route to Sales Console Customer Detail.
2. Customer editor routes carry customer context in the URL.
3. Quotation and Sales Order links route to managed enhanced forms.
4. Delivery Note and Sales Invoice links route to managed enhanced forms.
5. Quotation and Sales Order list links route to Sales Console directories.
6. Customer and Item list links route to Sales Console directories.
7. ToDo links route to Sales Console follow-up worklist.
8. Payment Entry, Opportunity, Warehouse, Delivery Trip, Driver, and Supplier are deferred or guarded rather than silently opened as raw pages.

Residual risk:

Browser behavior can still differ because Frappe route timing, route options, native form hydration, and connection-tab event binding are runtime concerns.

## 6. Security And Mutation Static Result

Static result:

`Pass for Sales Manager/Sales User role gate`

No SERA-5 security code change was required.

Current security result remains:

1. Customer create/edit is Sales Manager gated.
2. Customer create/edit requires native Customer create/write permission.
3. Customer create/edit writes only the approved sales profile field allowlist.
4. Customer save uses ERP document save truth.
5. Sales User should remain read-only for customer profile maintenance.
6. Print, Email, Attachments, Tags, Share, Assign, Submit, Cancel, and lifecycle actions remain ERP-delegated.

Residual risk:

Live Sales User and Sales Manager role testing passed on 2026-05-01. Administrator-like users remain outside this smoke pass.

## 7. Browser Smoke Evidence

SERA-5 browser review was completed through automated smoke, full route probing, and owner freeze acceptance.

Regression browser checks:

1. `/desk/sales-console` loads with one managed sidebar and one active menu item.
2. Browser back and forward do not create duplicate menus or stale active states.
3. Collapsed sidebar aligns icons and labels correctly.
4. `Ctrl+K` opens only the Sales Console scoped search on managed routes.
5. Search results navigate to Sales Console-owned routes or governed managed forms.
6. Quotation and Sales Order directories show date fields with calendar pickers.
7. Customer Detail direct URL refresh keeps customer context.
8. Customer Edit direct URL refresh keeps customer context.
9. Customer Create/Edit save persists and stays in the intended flow.
10. Sales User cannot create or edit customers.
11. Sales Manager can create and edit allowed customer fields.
12. Saved Quotation connection links route through the shared owner.
13. Saved Sales Order connection links route through the shared owner.
14. Delivery Note and Sales Invoice managed forms keep Sales Console sidebar behavior.
15. Deferred related records show a notice and do not silently open confusing raw pages.
16. Print opens the expected document print flow.
17. Email remains visible but fails safely until email account setup is completed.
18. Reduced-motion preference removes nonessential animation.
19. Narrow viewport does not break filter/action alignment.
20. Report pages load and their filter/actions remain stable.

## 8. Deferred Notes

The following are not SERA-5 blockers:

1. Stock availability for New Quotation and New Sales Order.
2. Final email account configuration.
3. Final PDF/print format design.
4. Productized detail pages for Payment Entry, Opportunity, Warehouse, Driver, Supplier, and Delivery Trip.
5. Deeper report business relevance tuning after real manager feedback.
6. Future AI features beyond deferred notes.

These should not be mixed into the Sales Console readiness gate unless browser smoke reveals a high-risk shared defect.

## 9. Validation

Static validation performed in this phase:

1. Python compile for Sales Console backend files.
2. Node syntax checks for touched shared shell files.
3. Focused search for remaining implementation-facing user copy in active product files.

Full final validation should run again after this document is indexed.

## 10. SERA-5A Browser Refinement Pass

Date: 2026-04-29
Status: Implemented and later browser-smoke verified

This addendum records the first browser-feedback refinement pass after SERA-5.

Decision:

`Shared component fixes first, page-specific fixes only when the page requires a new archetype.`

Fixes applied:

1. Shared worklist filter panels now use a compact grid action contract, so directory filters do not become tall one-column cards when three to five fields are present.
2. Shared worklist return actions now use the same subtle pill treatment across `Back to Customers`, `Back to Items`, and similar navigation actions.
3. Shared Refresh actions are treated as utility actions instead of decorative standalone panels.
4. Sales Console sidebar icon borders were softened to reduce visual noise, especially in collapsed mode.
5. Quotation Directory and Sales Order Directory now expose create actions only when native create permission exists.
6. Item Directory now opens a Sales Console-owned Item Detail route instead of routing to the raw ERP Item form.
7. Item Detail now has a productized Sales Console worklist view with stock-by-warehouse posture.
8. Direct Item Detail routes are addressable with `/desk/sales-console-worklist/item-detail/<item>`.
9. Draft Quotation and Draft Sales Order skeleton behavior now blocks late placeholder regressions after the draft body has already been revealed for the current route/session.

Residual browser checks:

1. Verify Quotation Directory and Sales Order Directory filter cards on desktop and collapsed-sidebar widths.
2. Verify `New Quotation` and `New Sales Order` create actions appear only for users with create permission.
3. Verify Item Directory row open routes to Item Detail and browser refresh preserves item context.
4. Verify Item Detail stock values are meaningful for branch/team expectations.
5. Verify the draft placeholder no longer returns after the main body is visible during a normal new quotation/order load.

## 11. Confirmed UI Contract Alignment

Date: 2026-05-01
Status: Tests/docs aligned and core role smoke passed

Confirmed page behavior is the source of truth for this alignment pass:

1. The first Sales Console sidebar destination label is `Overview`.
2. `Overview` routes to `/desk/sales-console`; `Sales Console` remains the workspace/page identity.
3. Report top actions render in this order: `Refresh`, `Back to Sales Console`, then report-specific actions such as native report fallback.
4. Tests and navigation notes should assert the confirmed UI contract instead of the older planned labels or action order.

Browser and role-permission checks passed on 2026-05-01 for Sales Manager and Sales User. The smoke did not create or update business records; owner visual freeze acceptance is recorded on 2026-05-03.

## 12. SERA-5B Filter Action Rail Alignment

Date: 2026-05-02
Status: Implemented and live-smoke verified

Decision:

Filter action bars belong to the same command row as their filters when they render beside filter boxes. In that layout, `Apply`, `Reset`, `Refresh`, and related utility actions must align to the input control center, not the label line or the bottom of the full filter field group.

Implemented shared rule:

1. Worklist command filters use a shared input-height and label-offset action rail.
2. Report command filters use the same action-rail alignment model.
3. Mobile and narrow layouts keep natural stacking, with no artificial label offset once actions wrap below filters.
4. The fix is shared in the list/report runtimes rather than page-local CSS.

Live measurement on 2026-05-02:

1. Item Directory action rail center delta: within 1 px of the filter input center.
2. Customer Directory action rail center delta: within 1 px of the filter input center.
3. Sales Analytics report action rail center delta: within 1 px of the filter input center.
4. Sales Manager and Sales User role smoke remained passing after the visual alignment change.

## 13. Go/No-Go

Current gate:

`Sales Console freeze accepted. Future workspace work may begin only from the Golden Rule standard and the frozen Sales Console reference.`

Future reuse may begin after:

1. validation checks remain passing
2. owner manual visual freeze acceptance is recorded
3. any owner-found high or medium shared defects are fixed or consciously deferred
4. the final freeze marker is pushed

Next workspace implementation should not start from old notes or screenshots.
