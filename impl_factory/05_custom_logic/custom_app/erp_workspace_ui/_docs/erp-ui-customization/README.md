# ERP UI Customization Notes

This folder records freeze decisions, deferred UI work, and implementation notes for the ERP UI customization stream.

Current implementation focus:

- Sales Console
- Enterprise shared UI component standard
- Enterprise shared UI implementation contract
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
- committed Customers/Items sync: `5ad8bca feat(erp-ui): sync customer and item sales console worklists`

Primary code paths:

- `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/sales_console/service.py`
- `erp_workspace_ui/sales_console/worklist.py`
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

Documents in this folder:

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
