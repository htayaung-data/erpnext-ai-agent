# Sales Console Final Documentation Alignment

Date: 2026-05-03
Status: Active final documentation alignment note
Branch: `feature/erpnext-ui-design`
Confirmed commit: `6dbd85c fix: forward socket origin through caddy`

## Purpose

This note records the final documentation alignment pass before Sales Console freeze.

The confirmed implementation is the source of truth. Historical discovery and early design notes may remain useful for context, but they are not the final contract when they disagree with current code.

## Active Documentation Set

The active implementation documentation set is:

1. `README.md`
2. `_docs/erp-ui-customization/README.md`
3. `_docs/erp-ui-customization/page-freeze-notes/sales-console-freeze.md`
4. `_docs/erp-ui-customization/page-freeze-notes/sales-console-reports-freeze.md`
5. `_docs/erp-ui-customization/sales-console-navigation-contract-v1.md`
6. `_docs/erp-ui-customization/sales-console-business-copy-contract-v1.md`
7. `_docs/erp-ui-customization/enterprise-shared-ui-component-standard-v1.md`
8. `_docs/erp-ui-customization/enterprise-shared-ui-component-implementation-contract-v1.md`
9. `_docs/erp-ui-customization/sales-console-enterprise-readiness-sera-*.md`
10. `_docs/erp-ui-customization/sales-console-mini-phase-5-report-archetype.md`
11. `_docs/erp-ui-customization/sales-console-mini-phase-6-operating-foundation.md`
12. `ui_smoke/README.md`

The older `impl_factory/08_erpnext_ui_design` material is historical design input. Do not treat it as the freeze contract without checking the active docs and current code.

## Final Route Truth

Sales Console V1 owns these route families:

1. `/desk/sales-console`
2. `/desk/sales-console-worklist/<queue-key>`
3. `/desk/sales-console-worklist/customer-detail/<customer>`
4. `/desk/sales-console-worklist/customer-editor/<customer>`
5. `/desk/sales-console-worklist/customer-editor`
6. `/desk/sales-console-worklist/item-detail/<item>`
7. `/desk/sales-console-report/<report-key>`
8. managed ERP form routes for `Quotation`, `Sales Order`, `Delivery Note`, and `Sales Invoice`

Bare worklist and report routes intentionally show guarded states when required route keys are missing.

## Final Sidebar Truth

The confirmed V1 sidebar has exactly five stable destinations:

1. `Overview`
2. `Quotations`
3. `Sales Orders`
4. `Customers`
5. `Items`

No standalone `Dashboard` sidebar item exists. No `Reports` sidebar item exists in V1.

## Final Report Truth

Visible role-controlled report pages:

1. `Sales Analytics`
2. `Sales Order Analysis`
3. `Trend Analysis`
4. `Lost Quotations`
5. `Collections Status`
6. `Item-wise Sales History`

Compatibility routes:

1. `quotation_trends` maps into `Trend Analysis` with `Quotation` selected.
2. `payment_terms_status_sales_order` maps into `Collections Status`.

The standalone Sales Dashboard page was removed before freeze because it overlapped with Sales Analytics and did not yet provide enough distinct enterprise value.

## Final Worklist And Detail Truth

Confirmed productized directories:

1. `quotation_directory`
2. `sales_order_directory`
3. `customer_directory`
4. `item_directory`

Confirmed productized detail/profile routes:

1. `customer_detail`
2. `customer_editor`
3. `item_detail`

Item Detail is accepted. It shows active selling price, stock posture metrics, stock locations, and stock-by-warehouse rows.

## Final Interaction Truth

Filter and command behavior:

1. `Apply` refreshes data in-place.
2. `Refresh` refreshes data in-place.
3. `Reset` resets visible filter controls and refreshes data in-place.
4. Date-window filters should stay together on desktop when width allows.
5. Link/autocomplete filter behavior should be consistent across report pages.

Breadcrumb behavior:

1. Directory pages show `Sales Console / <Directory>`.
2. Customer detail pages show `Sales Console / Customer Details / <Customer>`.
3. Item detail pages show `Sales Console / Item Details / <Item>`.

## Final Security And Permission Truth

1. Whitelisted APIs require authentication.
2. Report direct URLs are checked against the role-visible report catalog.
3. Sales User direct URLs to manager-only reports return restricted states.
4. Sales User direct access to customer editor does not expose save actions.
5. Customer create/edit remains Sales Manager controlled.
6. Server-side permission checks remain the authority for mutation.

## Final Deployment Truth

Caddy must forward `Origin` for `/socket.io`:

```caddyfile
header_up Origin https://{host}
```

Without this line, Frappe realtime can reject the Socket.IO namespace with `Invalid origin`.

## Final Verification Truth

Verification completed on 2026-05-03:

1. JavaScript syntax check passed across app JavaScript files.
2. Python compile check passed for Sales Console modules.
3. Sales Console unit/contract tests passed.
4. Docker Playwright role smoke passed for Sales Manager and Sales User.
5. Sales Order Analysis smoke passed for Sales Manager and Sales User.
6. Full live route probe passed for 24 Sales Manager routes and 21 Sales User routes.
7. Restricted-route checks passed for Sales User.
8. Socket.IO connected to namespace `/erpai_prj1` over websocket with no `Invalid origin` warning.

## Freeze Interpretation

The implementation and active docs are aligned for final freeze.

Owner visual/business acceptance is recorded on 2026-05-03.

Final freeze marker: `sales-console-freeze-v1`

Do not start the next workspace from old design notes or Sales Console screenshots.

Start from:

1. `shared-component-and-implementation-golden-rule-standard-v1.md`
2. `enterprise-shared-ui-component-standard-v1.md`
3. `enterprise-shared-ui-component-implementation-contract-v1.md`
4. this alignment note
5. the current code

The Sales Console is the current reference implementation, not the name or scope of the shared component system.
