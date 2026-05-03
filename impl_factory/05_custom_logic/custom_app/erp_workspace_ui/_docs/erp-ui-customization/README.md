# ERP UI Customization Notes

This folder records freeze decisions, deferred UI work, and implementation notes for the ERP UI customization stream.

Current implementation focus:

- Sales Console
- Shared Component and Implementation Golden Rule Standard
- workspace-wide shared UI component standard
- workspace-wide shared UI implementation contract
- Sales Console enterprise readiness audit
- Sales Console operating foundation mini-phase
- Sales Console operational worklists
- Sales Console Customers page
- Sales Console Items page
- Sales Console report family
- Sales Order
- Quotation
- Delivery Note
- Sales Invoice
- New Quotation draft
- New Sales Order draft

Implementation source of truth currently lives in the ERP UI Design branch:

- branch: `feature/erpnext-ui-design`
- worktree: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
- current confirmed UI baseline commit: `6dbd85c fix: forward socket origin through caddy`
- current confirmed documentation alignment commit: `50cd6fa docs: align sales console freeze documentation`
- previous UI polish commit: `d71592c style: polish item detail cards and breadcrumb`

Primary code paths:

- `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`
- `erp_workspace_ui/sales_console/service.py`
- `erp_workspace_ui/sales_console/worklist.py`
- `erp_workspace_ui/sales_console/report.py`
- `erp_workspace_ui/public/js/runtime/child_page/*`
- `erp_workspace_ui/public/js/quotation_form.js`
- `erp_workspace_ui/public/js/sales_order_form.js`

Current routing truth:

- `/desk/sales-console` is the Sales Console home.
- `/desk/sales-console-worklist/<queue-key>` is the shared worklist shell.
- `/desk/sales-console-worklist/customer-directory` is the productized Customers page.
- `/desk/sales-console-worklist/item-directory` is the productized Items page.
- `/desk/sales-console-worklist/customer-detail/<customer>` is the productized Customer Detail page.
- `/desk/sales-console-worklist/item-detail/<item>` is the productized Item Detail page.
- bare `/desk/sales-console-worklist` intentionally shows a guard state because no queue key was supplied.
- `/desk/sales-console-report/<report-key>` is the shared report shell.

Current visible report keys:

- `sales_analytics`
- `sales_order_analysis`
- `trend_analysis`
- `lost_quotations`
- `collections_status`
- `item_wise_sales_history`

Compatibility report keys:

- `quotation_trends` maps into `Trend Analysis` with `Quotation` selected.
- `payment_terms_status_sales_order` maps into `Collections Status`.

Current freeze facts:

- the standalone Sales Dashboard page was removed before freeze
- Item Detail is accepted and includes the active selling price and stock-by-warehouse posture
- Customer Detail and Item Detail breadcrumbs include their parent detail family before the record name
- Docker Playwright role smoke and Sales Order Analysis smoke passed for Sales Manager and Sales User
- full live route probing passed for 24 Sales Manager routes and 21 Sales User routes
- Socket.IO realtime is fixed by forwarding `Origin` through the Caddy `/socket.io` proxy

Documents in this folder:

- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `enterprise-shared-ui-component-standard-v1.md`
- `enterprise-shared-ui-component-implementation-contract-v1.md`
- `sales-console-enterprise-readiness-audit-mini-phase-plan.md`
- `sales-console-enterprise-readiness-standards-hardening-addendum.md`
- `sales-console-enterprise-readiness-sera-0-baseline.md`
- `sales-console-enterprise-readiness-sera-1-route-ownership.md`
- `sales-console-enterprise-readiness-sera-2-security-permissions.md`
- `sales-console-enterprise-readiness-sera-3-visual-stability.md`
- `sales-console-enterprise-readiness-sera-4-page-archetypes.md`
- `sales-console-enterprise-readiness-sera-5-cross-page-fix-pass.md`
- `sales-console-final-documentation-alignment-2026-05-03.md`
- `page-freeze-notes/README.md`
- `page-freeze-notes/sales-console-freeze.md`
- `page-freeze-notes/sales-order-freeze.md`
- `page-freeze-notes/quotation-freeze.md`
- `page-freeze-notes/delivery-note-freeze.md`
- `page-freeze-notes/sales-invoice-freeze.md`
- `page-freeze-notes/new-quotation-new-sales-order-freeze.md`
- `page-freeze-notes/sales-console-reports-freeze.md`
- `deferred-ui-improvements.md`
- `sales-console-mini-phase-6-operating-foundation.md`
- `sales-console-business-copy-contract-v1.md`
- `sales-console-navigation-contract-v1.md`

Future workspace implementation must start from `shared-component-and-implementation-golden-rule-standard-v1.md`.

The Sales Console is the current reference implementation, not the naming scope of the shared component standard.
