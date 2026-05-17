# ERP UI Customization Notes

This folder records freeze decisions, deferred UI work, and implementation notes for the ERP UI customization stream.

Current implementation focus:

- Main Phase 1 Shared Core Platform governance
- Sales Console
- Procurement Console
- Multi-Workspace Foundation
- Shared Component and Implementation Golden Rule Standard
- Frozen Workspace Protection Package Standard
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
- current confirmed Golden Rule commit: `3b071b0 docs: define workspace UI golden rule standard`
- current clean source baseline before Main Phase 1: `a05e4f8 fix: standardize procurement worklist filter widths`
- live deployment repo remains a dirty deployment/integration working tree and is not the Main Phase 1 source of truth
- previous UI polish commit: `d71592c style: polish item detail cards and breadcrumb`

Freeze and governance status:

- Sales Console is frozen on 2026-05-03.
- Freeze marker tag: `sales-console-freeze-v1`.
- Sales Console v2 freeze/protection package is accepted on 2026-05-09 after owner manual Premium UI confirmation.
- Current freeze marker tag: `sales-console-freeze-v2`.
- Procurement Console Phase 3 Stable Baseline is accepted on 2026-05-10 after owner manual review confirmed the current Phase 3 surface clean.
- Main Phase 2 Sales Recovery on 2026-05-06 hardens Sales against the Shared Core + Workspace Adapter v2 contract while preserving frozen route names and business scope.
- Procurement Console is active Phase 3 in the source registry.
- Purchase-role routing to `procurement-console-home` is owner-approved; Procurement is not the default app.
- Main Phase 1 added shared-core governance only; Main Phase 2 repairs Sales shared-core compliance only. Procurement repair, Procurement Phase 4, and new workspace work remain out of scope until owner-approved.
- Every frozen workspace must receive a Frozen Workspace Protection Package before future workspace work can safely proceed.

Primary code paths:

- `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js`
- `erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_runtime.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`
- `erp_workspace_ui/sales_console/service.py`
- `erp_workspace_ui/sales_console/worklist.py`
- `erp_workspace_ui/sales_console/report.py`
- `erp_workspace_ui/procurement_console/*`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/public/js/procurement_console/*`
- `erp_workspace_ui/public/js/runtime/child_page/*`
- `erp_workspace_ui/public/js/quotation_form.js`
- `erp_workspace_ui/public/js/sales_order_form.js`

Current routing truth:

- The route/action manifest is the Main Phase 1 machine-readable governance authority.
- Sales Console route names remain frozen and are now mapped through the workspace registry for future multi-workspace safety.
- `/desk/sales-console` is the Sales Console home.
- `/desk/sales-console-worklist/<queue-key>` is the shared worklist shell.
- `/desk/sales-console-worklist/customer-directory` is the productized Customers page.
- `/desk/sales-console-worklist/item-directory` is the productized Items page.
- `/desk/sales-console-worklist/customer-detail/<customer>` is the productized Customer Detail page.
- `/desk/sales-console-worklist/item-detail/<item>` is the productized Item Detail page.
- bare `/desk/sales-console-worklist` intentionally shows a guard state because no queue key was supplied.
- `/desk/sales-console-report/<report-key>` is the shared report shell.
- Procurement Console route names are active Phase 3 registry entries: `procurement-console-home`, `procurement-console`, `procurement-console-worklist`, `procurement-console-report`, `procurement-console-po-follow-up`, `procurement-console-supplier`, `procurement-console-item`, `procurement-console-purchase-request-review`, `procurement-console-rfq-review`, and `procurement-console-supplier-quotation-review`.
- `/desk/procurement-console-worklist/<queue-key>` uses the shared worklist shell.
- `/desk/procurement-console-report/supplier-quotation-comparison` uses the shared report shell.
- Procurement native create forms remain governed Phase 3 exceptions until a future owner-approved Managed Procurement Forms phase.

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
- the multi-workspace foundation keeps Sales Console frozen while recording the matrix-based roadmap for Procurement Console, Warehouse Console, Finance Console, Executive Console, Customer Service Console, HR and Admin Console, and ERP Admin Console
- Item Detail is accepted and includes the active selling price and stock-by-warehouse posture
- Customer Detail and Item Detail breadcrumbs include their parent detail family before the record name
- Docker Playwright role smoke and Sales Order Analysis smoke passed for Sales Manager and Sales User
- full live route probing passed for 24 Sales Manager routes and 21 Sales User routes
- Socket.IO realtime is fixed by forwarding `Origin` through the Caddy `/socket.io` proxy

Documents in this folder:

- `frozen-workspace-protection-package-standard-v1.md`
- `sales-console-frozen-protection-package-2026-05-09.md`
- `procurement-console-phase3-stable-baseline-2026-05-10.md`
- `procurement-console-phase5a-5b-managed-buying-baseline-2026-05-15.md`
- `procurement-console-phase5c-managed-supplier-quotation-baseline-2026-05-15.md`
- `procurement-console-phase5d-managed-purchase-order-baseline-2026-05-15.md`
- `procurement-console-phase6a-full-workspace-evaluation-plan-2026-05-15.md`
- `procurement-console-phase6b-supplier-facing-document-output-design-plan-2026-05-15.md`
- `procurement-console-phase6c1-output-preview-pdf-baseline-2026-05-16.md`
- `procurement-console-phase6c2a-rfq-send-readiness-baseline-2026-05-16.md`
- `procurement-console-phase6c2-rfq-email-send-design-plan-2026-05-16.md`
- `procurement-console-phase6c2b-rfq-governed-send-design-plan-2026-05-16.md`
- `procurement-console-phase6c2c-rfq-test-send-deferral-plan-2026-05-17.md`
- `procurement-console-phase5d-managed-purchase-order-design-plan-2026-05-15.md`
- `procurement-console-phase5c-supplier-quotation-design-plan-2026-05-15.md`
- `shared-core-route-action-inventory-2026-05-06.md`
- `sales-console-recovery-phase-2-2026-05-06.md`
- `shared-core-workspace-adapter-contract-v2.md`
- `native-exception-policy-v1.md`
- `multi-workspace-foundation-contract-v1.md`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `sales-console-final-freeze-2026-05-03.md`
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

Future workspace implementation must start from `frozen-workspace-protection-package-standard-v1.md`, `shared-core-workspace-adapter-contract-v2.md`, `native-exception-policy-v1.md`, `workspace_governance_manifest.py`, and `shared-component-and-implementation-golden-rule-standard-v1.md`.

Future workspaces must start from Core + Adapter, not by copying Sales Console or Procurement Console page files. The Sales Console is the current business reference implementation, not the naming scope of the shared component standard.
