# Sales Console Enterprise Readiness Audit: SERA-3 Visual Stability And Shared Component Quality

Date: 2026-04-28
Final verification update: 2026-05-03
Status: Pass with owner visual acceptance still remaining
Audit phase: `SERA-3` Visual Stability And Shared Component Quality
Depends on:

1. `enterprise-shared-ui-component-standard-v1.md`
2. `enterprise-shared-ui-component-implementation-contract-v1.md`
3. `sales-console-enterprise-readiness-sera-0-baseline.md`
4. `sales-console-enterprise-readiness-sera-1-route-ownership.md`
5. `sales-console-enterprise-readiness-sera-2-security-permissions.md`
6. `sales-console-enterprise-readiness-standards-hardening-addendum.md`

## 1. Purpose

This note records the Sales Console visual stability and shared component quality audit.

The goal is to prove that the current Sales Console UI is stable enough to keep as the reference workspace pattern before the project starts implementing additional ERP workspaces.

This phase checks:

1. managed sidebar consistency
2. duplicate native ERP surface suppression
3. custom Sales Console search behavior
4. list and report shell consistency
5. filter command strip consistency
6. detail page header and tab stability
7. connection card hierarchy
8. form panel layout
9. empty, restricted, loading, and guard states
10. accessibility and reduced-motion behavior
11. final owner visual acceptance requirements

## 2. SERA-3 Decision

SERA-3 decision:

`Pass with shared visual stability hardening; final owner visual acceptance remains outside automated proof`

Final verification update:

1. Docker browser role smoke passed for Sales Manager and Sales User.
2. Full live route probe passed for Sales Manager and Sales User.
3. No managed Sales Console route returned a page error state.
4. Socket.IO realtime connected over websocket after the Caddy origin-forwarding fix.
5. Item Detail metric cards and detail breadcrumbs were verified live.

Reason:

1. The Sales Console now has a managed sidebar contract for all Sales Console-owned routes.
2. Native ERP search is suppressed on managed routes and `Ctrl+K` opens the Sales Console search.
3. Native sidebar duplicates are hidden on managed Sales Console routes.
4. Sidebar active state is resolved from the current route instead of remaining stuck on the home item.
5. List, report, customer detail, customer editor, and route guard pages share reusable shell patterns.
6. Filter command strips, navigation buttons, and primary actions use shared rendering rules instead of page-specific positioning.
7. Customer create/edit and detail routes use addressable URLs where required, avoiding context loss on refresh.
8. Search, sidebar utilities, and sidebar menu items were hardened with explicit accessible labels and result roles.
9. Reduced-motion rules were added for shared hover, row, action, report, sidebar, and skeleton motion.
10. The remaining condition is live browser verification across page refresh, back navigation, collapsed sidebar, `Ctrl+K`, datepicker, and narrow viewport states.

Important limitation:

This is a static code audit plus targeted shared hardening. It does not replace live authenticated browser review. Visual stability must be confirmed in the browser because Frappe route transitions and native form loading can still affect timing.

## 3. Visual Stability Principle

Sales Console visual stability must follow this order:

1. reserve the correct surface before data arrives
2. render one managed navigation system
3. show one active route at a time
4. keep primary actions close to their filter or document context
5. hide implementation copy from business users
6. avoid page-specific spacing hacks
7. support keyboard, collapsed sidebar, and reduced-motion users
8. treat native ERP widgets as controlled delegates, not the main workspace experience

The enterprise rule is:

`Stable first. Beautiful second. Decorative never at the cost of clarity.`

## 4. Component Audit Inventory

| Component surface | Source | SERA-3 decision |
| --- | --- | --- |
| Managed Sales Console sidebar | `workspace_console_sidebar.js` | Pass. Active route, native duplicate suppression, and collapsed behavior are implemented and live route smoke passed. |
| Sidebar utility actions | `workspace_console_sidebar.js` | Pass after hardening. Search and notification controls now have explicit accessible names. |
| Sales Console search dialog | `workspace_console_sidebar.js`, `service.py` | Pass after hardening. `Ctrl+K` opens custom search on managed routes, search input has an accessible label, and results expose listbox/option semantics. |
| Workspace home shell | `workspace_console_runtime.js` | Pass with owner-review note. Current hierarchy is accepted for freeze; first-load movement remains a Desk-level deferred visual item unless owner review marks it disruptive. |
| List shell | `list_page_shell.js`, `worklist.py` | Pass. Shared summaries, filters, metrics, tables, states, navigation actions, in-place Apply/Reset/Refresh, and detail routes were live-smoke verified. |
| Report shell | `report_page_shell.js`, `report.py` | Pass. Shared report surface is stable enough for Sales Console and role-visible report routes were live-smoke verified. |
| Filter command strip | `list_page_shell.js`, `erp_workspace_ui.css` | Pass. One-filter and multi-filter command layouts are now reusable and keep apply/reset/refresh close to the filter context. |
| Detail document shell | `child_page_sections.js`, `quotation_form.js`, `sales_order_form.js`, `delivery_note_form.js`, `sales_invoice_form.js` | Pass for Sales Console freeze. Page layout follows the shared header, attention, detail, summary, and connection model. Native delegates remain governed ERP behavior. |
| Attention band | `child_page_sections.js`, `erp_workspace_ui.css` | Pass. Business guidance appears only when there is meaningful attention, not as generic instruction text. |
| Detail body sections | `child_page_sections.js`, `erp_workspace_ui.css` | Pass. Implementation-facing text was removed or reduced and section copy is now business-facing where retained. |
| Connection cards | `child_page_sections.js`, `erp_workspace_ui.css` | Pass with native-delegate boundary. Shared hierarchy rules exist and non-productized destinations remain guarded or governed fallbacks. |
| Customer detail page | `list_page_shell.js`, `worklist.py` | Pass. Addressable customer detail routes and activity filters are implemented and live-smoke verified. |
| Item detail page | `list_page_shell.js`, `worklist.py` | Pass. Addressable item detail route, selling price metric, stock posture cards, and stock-by-warehouse table are implemented and live-smoke verified. |
| Customer create/edit form | `list_page_shell.js`, `worklist.py` | Pass. Uses shared form panel, centered width, save-in-place behavior, and controlled business copy. |
| Guard and restricted states | `list_page_shell.js`, `worklist.py` | Pass. Guard pages intentionally explain missing context or restricted access without exposing technical details. |
| Reduced-motion behavior | `erp_workspace_ui.css` | Pass after hardening. Shared transitions and skeleton shimmer are disabled for users requesting reduced motion. |

## 5. Hardening Applied In SERA-3

### 5.1 Sidebar And Search Accessibility

Changed source:

`erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`

Hardening:

1. Search input now has an explicit accessible label.
2. Search input now exposes combobox state for the result list.
3. Search result container now exposes `role="listbox"`.
4. Search result buttons now expose `role="option"`.
5. Active search result state is mirrored through `aria-activedescendant`.
6. Notification utility now has explicit label and title.
7. Search utility now has explicit label and title.
8. Sidebar menu buttons now have explicit label and title based on their business label.

Why this matters:

The Sales Console sidebar can collapse into an icon-only state. When visible text is hidden, the UI must still remain understandable to assistive technology and keyboard users.

Decision:

`Pass`

### 5.2 Reduced-Motion Visual Stability

Changed source:

`erp_workspace_ui/public/css/erp_workspace_ui.css`

Hardening:

1. Shared action hover transitions are disabled when `prefers-reduced-motion: reduce` is active.
2. Sidebar link and utility transitions are disabled in reduced-motion mode.
3. Sales Console search result transitions are disabled in reduced-motion mode.
4. List row open-arrow transforms are disabled in reduced-motion mode.
5. Report row/link motion is disabled in reduced-motion mode.
6. Connection card button transforms are disabled in reduced-motion mode.
7. Document skeleton shimmer animation is disabled in reduced-motion mode.

Why this matters:

Enterprise UI should not depend on motion to feel premium. The same interface must remain calm, predictable, and readable for users who prefer reduced motion.

Decision:

`Pass`

## 6. Visual Contract For Future Workspaces

Future workspaces must not copy page-by-page visual fixes. They must copy the shared pattern below.

### 6.1 Sidebar Contract

Required:

1. one managed workspace sidebar
2. one active menu item
3. no duplicate native workspace item
4. no native global search for role-focused workspace users
5. `Ctrl+K` opens the workspace-specific search
6. collapsed state remains icon-aligned and keyboard accessible
7. business brand appears in header, not project implementation names

Not allowed:

1. separate page-specific sidebar implementations
2. native and custom search appearing together
3. two selected menu items
4. developer or implementation labels in business navigation

### 6.2 List And Directory Contract

Required:

1. summary card first
2. filters before metrics
3. action buttons close to the filter context
4. primary action order: `Apply`, `Reset`, `Refresh`
5. low-emphasis navigation action separated from filtering actions
6. table rows route only to productized pages or approved native delegates
7. empty and restricted states explain the business reason

Not allowed:

1. action buttons floating far away from their filter
2. unaddressable detail routes where reload loses context
3. row links that silently leak to unrelated native ERP pages
4. helper copy that describes implementation instead of business meaning

### 6.3 Detail Page Contract

Required:

1. document identity first
2. status and commercial facts second
3. attention only when action is needed
4. action band only for high-value actions
5. details remain native where ERPNext is the authoritative editor
6. connections show only business-relevant linked records
7. create-new actions appear only when role, workflow, and productized route are safe

Not allowed:

1. action cards that duplicate right-pane native actions without additional business value
2. generic "what to do" copy on every record
3. optional links displayed only to prove the data model exists
4. native create pages exposed to Sales Console users without a productized route

### 6.4 Form Contract

Required:

1. centered form panel with a clear maximum width
2. stable title card aligned to the form panel
3. business copy that explains what the user can safely change
4. save-in-place behavior unless the user explicitly navigates away
5. server-side allowed-field enforcement

Not allowed:

1. full-width single-column forms that feel accidental
2. save actions that unexpectedly return to a list
3. developer guardrail text
4. empty list structure sections under forms

## 7. Remaining Browser Verification

The following browser checks are required before SERA-3 can become `Final Grade`.

### 7.1 Sidebar And Search

1. Open `/desk/sales-console`.
2. Navigate to Customers, Items, Quotations, Sales Orders, customer detail, customer editor, and customer creation.
3. Confirm only one sidebar menu item is selected on every route.
4. Collapse the sidebar and confirm all icons align vertically.
5. Confirm Notification and Search remain visually consistent in collapsed and expanded states.
6. Press `Ctrl+K` on managed routes and confirm only the Sales Console search opens.
7. Search for customer, item, quotation, and sales order terms and confirm route ownership is respected.

### 7.2 List And Directory Pages

1. Open each directory directly by URL and by sidebar navigation.
2. Refresh each page and confirm the route still resolves.
3. Use filters, Apply, Reset, and Refresh.
4. Confirm date fields open the calendar picker where date filters exist.
5. Confirm action buttons remain close to filter controls.
6. Confirm row navigation stays inside productized Sales Console routes where those routes exist.

### 7.3 Customer Pages

1. Open a customer detail page from the Customers page.
2. Refresh the customer detail URL and confirm the customer context remains.
3. Filter activity by document type and confirm table results update.
4. Open customer edit and save a safe field update.
5. Refresh and confirm saved truth remains.
6. Confirm Sales User cannot create or edit customers if role testing is available.

### 7.4 Document Pages

1. Open Quotation, Sales Order, Delivery Note, and Sales Invoice detail pages.
2. Confirm there is no excessive business copy above the native main body.
3. Confirm attention cards appear only when meaningful.
4. Confirm connection cards do not expose unsafe native create flows.
5. Confirm Print and Email stay as controlled native delegates.
6. Confirm no visible first-load shake is unacceptable during route transitions.

### 7.5 Reduced Motion

1. Enable reduced motion in the browser or OS.
2. Refresh Sales Console pages.
3. Confirm hover transforms, route shimmer, and search/sidebar motion do not animate.
4. Confirm the interface still looks complete and intentional without motion.

## 8. SERA-3 Risks And Follow-Up

### 8.1 Static Audit Cannot Fully Prove Route Timing

Risk:

Frappe route transitions and native form rendering can still create first-load movement that static code inspection cannot fully prove.

Follow-up:

Manual browser verification is required on the deployed server.

### 8.2 Token Discipline Is Partially Mature

Risk:

The CSS has a strong shared visual language, but not every surface is fully tokenized. Some colors, borders, and shadows remain hardcoded in runtime styles.

Decision:

This is not a blocker for SERA-3 because the current UI uses shared components and stable patterns. It should become a design-system consolidation task before broad multi-workspace scale-out.

Follow-up:

SERA-4 or the next shared component phase should consolidate repeated values into a smaller token set.

### 8.3 Report Shell Needs Business Relevance Review

Risk:

The report shell is visually consistent, but visual consistency alone does not prove that each report gives high business value.

Final update:

SERA-4 reviewed the report family, and the final route probe verified role-visible report routes. Future report changes should still pass the same relevance, default-filter, and next-action clarity checks.

### 8.4 Native ERP Delegates Remain Intentionally Present

Risk:

Print, Email, Assign, Attachments, Tags, Share, and native right-pane actions remain present. These are acceptable if they are treated as controlled native delegates, but they can still show native ERP permission/configuration errors.

Follow-up:

Document Email setup, print format setup, and native action permissions as deferred operational configuration.

## 9. Exit Criteria

| Gate | Result | Notes |
| --- | --- | --- |
| One managed sidebar | Pass | Live route probe passed for role-visible managed routes. |
| One active menu item | Pass | Route resolver is implemented and queue/detail routes map back to their parent directory. |
| Custom workspace search | Pass | Search owns `Ctrl+K` on managed routes. |
| Duplicate native search suppressed | Pass | Code suppresses it on managed routes; live smoke did not find duplicate route error states. |
| Filter/action command strip | Pass | Shared layout keeps Apply, Reset, and Refresh together. |
| Addressable customer detail/edit/create | Pass | URL can carry record context. |
| Business copy discipline | Pass for Sale Console freeze | Current Sales Console, inquiry, worklists, reports, and item/customer detail copy reflect the confirmed UI. |
| Reduced-motion support | Pass | Shared CSS hardening added. |
| Accessibility labels for collapsed navigation | Pass | Sidebar/search labels and roles added. |
| No page-specific visual hacks introduced | Pass | SERA-3 changes are shared runtime/CSS only. |

## 10. Go Or No-Go

SERA-3 recommendation:

`SERA-3 is complete for Sales Console freeze. Keep owner manual visual acceptance as the final non-automated checkpoint.`

Reason:

The shared visual foundation is good enough for Sales Console freeze. Browser verification has passed for the managed route set; the remaining proof is owner manual visual/business acceptance in the real browser.
