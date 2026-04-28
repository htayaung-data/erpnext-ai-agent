# Page Freeze Notes

This folder is the authoritative freeze record for the ERP UI customization pages that are complete enough to protect from casual reopening.

Purpose:

- define what is accepted
- record what is intentionally deferred
- prevent repeated redesign churn after a page family is already good enough

Evidence base:

- direct inspection of the current shared runtime and form modules in:
  - `public/js/runtime/console/workspace_console_runtime.js`
  - `public/js/runtime/console/workspace_console_sidebar.js`
  - `public/js/runtime/list_page/list_page_shell.js`
  - `public/js/runtime/report_page/report_page_shell.js`
  - `public/js/runtime/child_page/child_page_helpers.js`
  - `public/js/runtime/child_page/child_page_shell.js`
  - `public/js/runtime/child_page/child_page_shell_content.js`
  - `public/js/runtime/child_page/child_page_operating_actions.js`
  - `page/sales_console/sales_console.js`
  - `page/sales_console_worklist/sales_console_worklist.js`
  - `page/sales_console_report/sales_console_report.js`
  - `sales_console/service.py`
  - `sales_console/worklist.py`
  - `sales_console/report.py`
  - `public/js/quotation_form.js`
  - `public/js/sales_order_form.js`
- validated implemented behavior from the live ERP UI stream for the other finalized pages in the same program
- live manual check on 2026-04-23 confirmed `customer-directory` and `item-directory` worklist routes render successfully
- automated validation on 2026-04-23 passed for the Mini-Phase 6 operating foundation contract:
  - `erp_workspace_ui.tests.test_sales_console_service_contracts`
  - `erp_workspace_ui.tests.test_sales_console_operating_contracts`

Pages frozen here:

- `sales-console-freeze.md`
- `sales-order-freeze.md`
- `quotation-freeze.md`
- `delivery-note-freeze.md`
- `sales-invoice-freeze.md`
- `new-quotation-new-sales-order-freeze.md`
- `sales-console-reports-freeze.md`

Use rule:

- reopen only for real regressions, data-trust issues, or clearly measured performance work
- do not reopen for low-signal aesthetic churn
