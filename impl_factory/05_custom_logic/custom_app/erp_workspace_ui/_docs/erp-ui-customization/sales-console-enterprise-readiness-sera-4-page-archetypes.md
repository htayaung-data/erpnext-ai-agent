# Sales Console Enterprise Readiness Audit: SERA-4 Page Archetype Audit By Family

Date: 2026-04-28
Status: Conditional Pass with business-copy hardening and browser review required
Audit phase: `SERA-4` Page Archetype Audit By Family
Depends on:

1. `enterprise-shared-ui-component-standard-v1.md`
2. `enterprise-shared-ui-component-implementation-contract-v1.md`
3. `sales-console-enterprise-readiness-sera-1-route-ownership.md`
4. `sales-console-enterprise-readiness-sera-2-security-permissions.md`
5. `sales-console-enterprise-readiness-sera-3-visual-stability.md`

## 1. Purpose

This note audits Sales Console as a set of reusable page archetypes.

The goal is to decide whether the Sales Console page families have enough business purpose, route safety, and UI maturity to be used as the reference pattern for future ERP workspaces.

SERA-4 is not a visual taste pass.

It asks:

1. Does each page family have a clear business job?
2. Does the page use the right shared archetype?
3. Does the page expose only useful actions?
4. Does the page avoid implementation-facing copy?
5. Does navigation stay inside the Sales Console contract where productized routes exist?
6. Are remaining native ERP delegates intentional?
7. What must be fixed before the next workspace copies the pattern?

## 2. SERA-4 Decision

SERA-4 decision:

`Conditional Pass with business-copy hardening and browser review required`

Reason:

1. The page families are clearly mapped to reusable archetypes.
2. The Sales Console home, sidebar, search, directories, customer profile pages, draft documents, saved documents, and reports each have a defensible business role.
3. The most important custom operational flows now use shared shells and route contracts.
4. Customer create/edit is correctly treated as manager-controlled profile maintenance, not full Customer administration.
5. Draft Quotation and Sales Order pages keep readiness signals but defer stock availability until the next planned feature phase.
6. Saved document pages correctly treat Print, Email, Assign, Attachments, Tags, Share, and document lifecycle actions as controlled ERP delegates.
7. Implementation-facing copy found during this audit was hardened at the shared source level.
8. Report relevance and live route behavior still require browser review before Sales Console can become `Final Grade`.

## 3. Page Family Matrix

| Family | Pages | Archetype | Status | Primary decision |
| --- | --- | --- | --- | --- |
| A. Workspace Entry | Home, sidebar, scoped search | Workspace home, navigation, search | Conditional pass | Ready as reference after browser verification of route return, collapse, and `Ctrl+K`. |
| B. Directories And Queues | Quotations, Sales Orders, Customers, Items, approval queues, blocker queues, follow-up queues | Directory and queue shell | Conditional pass | Good shared structure. Directory pages are strong; operational queues need browser route review. |
| C. Customer Profile Surfaces | Customer Detail, Customer Create, Customer Edit | Drill-down detail and create/edit profile | Pass with role verification required | Correct business scope for Sales Manager create/edit and Sales User read-only behavior. |
| D. Draft Documents | New Quotation, New Sales Order | Draft create | Conditional pass | Readiness shell is acceptable; stock availability is intentionally deferred. Browser stability must be checked. |
| E. Saved Execution Documents | Quotation, Sales Order, Delivery Note, Sales Invoice | Managed document execution | Conditional pass | Strong pattern after action-band cleanup. Native delegates are acceptable if browser route behavior is verified. |
| F. Reports | Sales Analytics, Sales Order Analysis, Quotation Trends, Lost Quotations, Collections Status, Item Sales History | Report shell | Conditional pass | Shell is usable, but each report still needs business relevance and default-filter review. |

## 4. Family A: Workspace Entry

### Scope

1. Sales Console home
2. managed sidebar
3. scoped search

### Decision

`Conditional Pass`

### Business Value

This family gives sales users a single operating entry point:

1. create new Quotation
2. create new Sales Order
3. browse Customers
4. browse Items
5. review operational blockers
6. search only Sales Console-relevant records

### Risks

Top business risk:

Search results must remain role-relevant and must not lead users to unrelated raw ERP pages.

Top UI risk:

Sidebar collapse and route transitions must remain visually stable after browser back, forward, and refresh.

Top route risk:

The home page and child routes must never show both native ERP navigation and managed Sales Console navigation.

### Fixes Applied

1. Search input has an accessible label and combobox state.
2. Search result list has listbox/option semantics.
3. Sidebar utilities and menu items have accessible labels for collapsed state.
4. Reduced-motion rules cover sidebar and search result motion.

### Deferred

1. Live browser verification of `Ctrl+K` on every managed route.
2. Live browser verification that one menu item is selected after back/forward navigation.

## 5. Family B: Directories And Queues

### Scope

1. Quotations directory
2. Sales Orders directory
3. Customers directory
4. Items directory
5. approval queues
6. blocker queues
7. follow-up queues

### Decision

`Conditional Pass`

### Business Value

Directories answer broad browsing questions:

1. what quotations exist
2. what sales orders exist
3. which customers are in scope
4. which items are available for sales work

Queues answer operational questions:

1. what needs approval
2. what is blocked
3. what needs follow-up
4. what is overdue or exposed

Keeping both patterns is correct. A directory is not a queue, and a queue is not a complete directory.

### Risks

Top business risk:

Users may confuse all-record directories with operational slices if titles, filters, and metrics are unclear.

Top UI risk:

Large filter bars can become busy if every directory adds fields independently.

Top route risk:

Rows must use productized routes when available and controlled managed forms when a full custom detail page is not available.

### Fixes Applied

1. Removed an accidental duplicate `rows` assignment from the Quotation directory payload.
2. Reworded queue unavailable copy away from implementation language.
3. Reworded empty and restricted states to say `current access scope` instead of `ERP permission scope`.
4. Reworded directory scope copy to use business-facing Sales Console language.

### Deferred

1. Browser check that date filters open the calendar picker.
2. Browser check that queue row navigation follows route ownership.
3. Decide later whether operational queues need additional filters after real user feedback.

## 6. Family C: Customer Profile Surfaces

### Scope

1. Customer Detail
2. Customer Create
3. Customer Edit

### Decision

`Pass with role verification required`

### Business Value

Customer Detail is valuable because it lets sales users see:

1. receivable exposure
2. credit posture
3. open orders
4. open invoices
5. recent Quotation, Sales Order, and Sales Invoice activity

Customer Create/Edit is valuable for Sales Managers because it lets them maintain safe sales profile fields:

1. customer name
2. customer group
3. territory
4. phone
5. email

It correctly excludes finance and administration controls:

1. credit limit
2. payment terms
3. tax settings
4. account controls
5. delete or disable

### Risks

Top business risk:

Sales Manager can maintain basic contact data, but Finance/Admin still owns credit and account controls. Users must not misunderstand this boundary.

Top UI risk:

Create and Edit copy must stay distinct and business-facing.

Top route risk:

Customer Detail and Customer Edit must survive refresh with customer context in the URL.

### Fixes Applied

1. Customer Detail uses addressable record routes.
2. Customer Edit saves in place and returns saved truth.
3. Customer Create/Edit form copy is now business-facing.
4. Customer Detail `Customer ID` meta now says `ERP customer record`, not implementation-owned context.

### Deferred

1. Sales User versus Sales Manager role test in browser/API session.
2. Browser refresh test for Customer Detail and Customer Editor URLs.

## 7. Family D: Draft Documents

### Scope

1. New Quotation
2. New Sales Order

### Decision

`Conditional Pass`

### Business Value

Draft readiness is useful because it tells users what must be completed before downstream work is meaningful:

1. customer
2. date or validity
3. price list
4. item lines
5. pricing readiness

This is the right place for future stock availability, but stock should stay a line-level decision signal, not a large dashboard block.

### Risks

Top business risk:

Too many draft widgets can distract users from actually entering customer and item details.

Top UI risk:

Frappe native form loading can create first-load movement if placeholder and final shell timing disagree.

Top route risk:

Draft pages are managed ERP forms, so route ownership must keep the Sales Console sidebar and avoid native menu confusion.

### Fixes Applied

1. Shared operating action copy now avoids implementation terms.
2. Print and Email remain unavailable until the draft is saved.
3. Submit/save copy is business-facing.

### Deferred

1. Stock availability support for New Quotation and New Sales Order.
2. Browser verification of placeholder-to-body stability.
3. Final decision on how much draft action guidance should remain visible before save.

## 8. Family E: Saved Execution Documents

### Scope

1. saved Quotation
2. saved Sales Order
3. Delivery Note
4. Sales Invoice

### Decision

`Conditional Pass`

### Business Value

Saved document pages help sales users and managers read the document operating state quickly:

1. customer
2. status
3. total value
4. expiry or delivery due date
5. fulfillment or settlement posture
6. attention cards only when action is needed
7. related commercial chain records

The UI is strongest when it summarizes business state and lets ERPNext remain the transaction truth.

### Risks

Top business risk:

Actions such as Print, Email, Assign, Share, Attachments, and Tags depend on ERPNext permissions and configuration. Email may fail until email accounts are configured.

Top UI risk:

Action bands become busy if low-value linked-document actions are promoted into the top document area.

Top route risk:

Connection actions must not expose unsafe raw create forms or unsupported native list flows.

### Fixes Applied

1. Shared document action copy no longer says `native`.
2. Standard Print and Email language is now business-facing.
3. Deferred related doctypes show a Sales Console notice instead of silently routing to unsupported raw pages.
4. Visible implementation copy on Quotation, Delivery Note, Sales Invoice, and Sales Order was reworded.

### Deferred

1. Manual browser check for connection links on Quotation, Sales Order, Delivery Note, and Sales Invoice.
2. Email account setup and print format design remain operational configuration work.
3. Future decision: whether Payment Entry, Warehouse, Opportunity, Supplier, Driver, and Delivery Trip need productized Sales Console pages.

## 9. Family F: Reports

### Scope

1. Sales Analytics
2. Sales Order Analysis
3. Quotation Trends
4. Lost Quotations
5. Collections Status
6. Item Sales History

### Decision

`Conditional Pass`

### Business Value

Reports are valuable only when they answer sales operating questions:

1. what revenue moved
2. which orders are open
3. which quotations are moving or lost
4. which invoices need collection action
5. which items are selling

The report shell is usable and visually consistent. The next risk is not layout; it is whether every report default view has enough business value for sales users.

### Risks

Top business risk:

Reports copied from ERPNext can be technically correct but not role-focused enough.

Top UI risk:

Report filters and metrics can become too broad if every report is treated as equally important.

Top route risk:

Report row links must route through managed forms or documented standard report/list delegates.

### Fixes Applied

1. Report unavailable copy no longer says `productized route`.
2. Report empty states now use `current access scope`.
3. `Open Native Report` was reworded to `Open Standard Report`.

### Deferred

1. Business-owner review of report priorities.
2. Browser verification of report filters and row navigation.
3. Decide whether Sales Console needs a sidebar Reports entry or report cards only.

## 10. Shared Standard Update

SERA-4 discovered one standard-level rule that future workspaces must inherit.

The implementation contract now explicitly bans implementation-facing terms in normal workspace UI:

1. native
2. productized
3. route
4. raw ERP
5. implementation
6. permission scope
7. console-owned

Preferred business-facing replacements were added:

1. standard report
2. standard list
3. current access scope
4. current Sales Console scope
5. related records
6. document view
7. activity area

Changed document:

`enterprise-shared-ui-component-implementation-contract-v1.md`

## 11. SERA-4 Fix Inventory

Code hardening applied:

1. `child_page_operating_actions.js`: reworded shared Print, Email, Assign, Comment, Share, and Submit action copy.
2. `child_page_helpers.js`: reworded deferred-route notice.
3. `worklist.py`: reworded queue, directory, restricted, and empty-state copy.
4. `report.py`: reworded report unavailable and empty-state copy.
5. `quotation_form.js`: reworded quotation detail guidance copy.
6. `sales_order_form.js`: reworded empty connection copy.
7. `delivery_note_form.js`: reworded delivery guidance copy.
8. `sales_invoice_form.js`: reworded invoice guidance copy.

No new mutation behavior was added.

No new route was added.

No permission boundary was weakened.

## 12. Remaining Browser Verification

SERA-4 cannot become `Final Grade` without browser review.

Required browser checks:

1. Home to every sidebar destination and back.
2. Quotation and Sales Order directories with filters and row opening.
3. Customer Detail direct refresh and activity row opening.
4. Customer Create/Edit save and cancel.
5. New Quotation and New Sales Order first-load stability.
6. Saved Quotation and Sales Order attention/action/connection behavior.
7. Delivery Note and Sales Invoice managed document behavior.
8. Report filters, rows, empty states, and standard report fallback.
9. Deferred connection notices for unsupported related doctypes.
10. Print opens without trapping users in an unintended route.
11. Email icon remains available but configuration errors are understood as setup work.

## 13. Go Or No-Go

SERA-4 recommendation:

`Go to SERA-5 Cross-Page Fix Pass, with no known high-risk archetype blocker.`

Reason:

Sales Console has a coherent enterprise page family model. The next step should not start a new workspace yet. The next step should run SERA-5 to verify and fix only cross-page blockers discovered by browser review.
