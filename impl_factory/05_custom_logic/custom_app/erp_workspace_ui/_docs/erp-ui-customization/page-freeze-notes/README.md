# Page Freeze Notes

This folder is the authoritative freeze record for the ERP UI customization pages that are complete enough to protect from casual reopening.

Purpose:

- define what is accepted
- record what is intentionally deferred
- prevent repeated redesign churn after a page family is already good enough

Evidence base:

- direct inspection of the current shared runtime and form modules in:
  - `public/js/runtime/child_page/child_page_helpers.js`
  - `public/js/runtime/child_page/child_page_shell.js`
  - `public/js/runtime/child_page/child_page_shell_content.js`
  - `public/js/quotation_form.js`
  - `public/js/sales_order_form.js`
- validated implemented behavior from the live ERP UI stream for the other finalized pages in the same program

Pages frozen here:

- `sales-console-freeze.md`
- `sales-order-freeze.md`
- `quotation-freeze.md`
- `delivery-note-freeze.md`
- `sales-invoice-freeze.md`
- `new-quotation-new-sales-order-freeze.md`

Use rule:

- reopen only for real regressions, data-trust issues, or clearly measured performance work
- do not reopen for low-signal aesthetic churn
