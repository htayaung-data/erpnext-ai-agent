# ERP UI Customization Notes

This folder records freeze decisions, deferred UI work, and implementation notes for the ERP UI customization stream.

Current implementation focus:

- Main Phase 1 Shared Core Platform governance
- Sales Console
- Procurement Console
- Warehouse Console W1/W2 docs-only roadmap, W3/W3A protected read-only foundation and landing baseline, W4/W4A/W4B inbound visibility, W5A/W5B outbound picking visibility, W6A/W6B stock exception visibility and review, W7A stock posture review, and W8 movement visibility design
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
- Procurement Console Phase 7D1 native escape closure is protected on 2026-05-18 after cleanup removed dead native chrome helpers and post-live protected gates passed.
- Procurement Console Phase 7E operations capability gap audit is documented on 2026-05-18 as a docs-only Purchase Manager roadmap after native escape closure.
- Procurement Console Phase 7G Quick Find operations review is documented on 2026-05-19 as a docs-only design review; implementation is deferred.
- Procurement Console Phase 7E2 Buying Item Procurement Context is documented on 2026-05-19 as a docs-only design for app-owned item buying readiness/context; implementation is deferred.
- Procurement Console Phase 7E2A Buying Item Procurement Context is protected on 2026-05-19; native Item escape remains closed and Item Price, Default Supplier, and Item Supplier mutation remain forbidden. Next recommended step is Phase 7E3 design only.
- Procurement Console Phase 7E3 Manager Review / Action Readiness is documented on 2026-05-19 as a docs-only design; recommended implementation is readiness/exception guidance without lifecycle mutation. Native escape, send/email, conversion, submit/approval, Item Price, Default Supplier, receiving, billing, and payment remain deferred.
- Procurement Console Phase 7H1 Readiness Inference and Exception Queue Realism is protected on 2026-05-20; fake historical `No profile` / `Not reviewed` backlog is removed, Manager Readiness is exception-oriented, and no lifecycle/send/master-data mutations were introduced. Next recommended step is Phase 7I full Procurement freeze audit.
- Procurement Console Phase 7I Full Freeze Audit is closed on 2026-05-20 as a protected freeze baseline for the current accepted Procurement scope; artifact root `/tmp/procurement-phase7i-freeze-audit-20260520T130503Z`, final Sales freeze `/tmp/sales-freeze-protection-20260520T141113Z`, and final protected workspace gate `/tmp/protected-workspaces-20260520T141521Z` passed. Future planned Procurement phases may continue only without regressing this protected baseline.
- Procurement Console Phase 7J UX Information Architecture redesign is documented on 2026-05-20 as a docs-only plan for compressing Manager Readiness, tabbing supplier/item detail activity, polishing managed form/review hierarchy, and improving report/directory comprehension without changing the protected Phase 7I runtime baseline.
- Procurement Console Phase 7J1D Readiness Review Queue evidence correction and premium polish is protected on 2026-05-23 at `88b144263f594f98e6828d52628b5d1983dd7e62`; the previous 21 item buying warnings were corrected to 11 valid warnings after sales/purchase history was counted as operational evidence, clear categories became compact pills, readiness performance remained healthy, Purchase User readiness calls remained zero, and the post-live protected workspace gate passed at `/tmp/procurement-readiness-sales-history-protected-live-20260523T122410Z`.
- Procurement Console Phase 7J2 Supplier and Buying Item Detail tabbed information architecture is documented on 2026-05-23 as a docs-only design plan for turning stacked Supplier/Item detail sections into object-style tabs, recent-row lists, productized drilldowns, and business-friendly ownership labels while preserving Phase 7J1D protected behavior.
- Procurement Console Phase 7J2B Supplier and Buying Item Detail tab simplification review is documented on 2026-05-24 as a docs-only recommendation to default both pages to Profile, remove redundant Activity/References/standalone Readiness tabs, reduce duplicate badges, and keep Phase 7J2A protected behavior without runtime changes.
- Procurement Console Phase 7J2C Supplier and Buying Item Detail tab simplification is protected on 2026-05-24 at `268e443451742fd10cf6ea705e17880101685005`; Supplier Detail now defaults to Profile with only Profile/Orders/RFQs/Quotations, Buying Item Detail now defaults to Profile with only Profile/Suppliers & Prices/Orders/Quotation History, duplicate below-header badge clutter is removed, Purchase User remains read-only/productized, and final post-live protected gate passed at `/tmp/procurement-phase7j2c-protected-live-rerun-20260524T045633Z`.
- Procurement Console Phase 7K Overview Quick Find is protected on 2026-05-24 at `27764669a9242e732135eec1a8ae59521b85813d`; Overview now keeps Header/KPI, `Start Buying Work`, `Quick Find`, then `Readiness Review`, Quick Find copy reads `Preview before opening`, grouped suggestions preview before explicit Open, productized Procurement routes remain the only targets, and final post-live protected gate passed at `/tmp/procurement-phase7k-consistency-protected-live-20260524T104308Z`.
- Procurement Console final freeze closure is documented on 2026-05-25 at `c1059b1`; Sales and Procurement are protected workspaces for the next Warehouse Console work.
- Warehouse Console Phase W1 industry research and roadmap is documented on 2026-05-26 as a docs-only design phase. No Warehouse runtime, route, API, stock action, Sales change, Procurement change, or live alignment is included.
- Warehouse Console Phase W2 route/action inventory and protection plan is documented on 2026-05-26 as a docs-only implementation gate. It defines proposed Warehouse routes, actions, roles, data sources, native escape restrictions, copy rules, future smoke coverage, and W3 readiness decisions without adding runtime routes or stock actions.
- Warehouse Console Phase W3 read-only foundation and W3A protected landing closure are protected on 2026-05-27. Warehouse operational users land on `/desk/warehouse-console`; W3 remains read-only with no Quick Find, valuation, native escape, or stock mutation.
- Warehouse Console Phase W4 inbound visibility design is documented on 2026-05-27 as a docs-only plan for premium supplier receiving visibility, grouped inbound queues, and read-only receiving review without receiving execution or stock posting.
- Warehouse Console Phase W4A inbound receiving visibility is protected on 2026-05-28 at `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca`; Warehouse Overview now exposes inbound posture and `/desk/warehouse-console-worklist/inbound-receiving` renders a read-only grouped receiving queue for Warehouse Manager/User without stock posting, valuation, native escape, Quick Find, or Sales/Procurement runtime change.
- Warehouse Console Phase W4B Receiving Review is protected on 2026-05-28 at `0abed2f826b14909ec59182f126bdca5ebabf5bd`; `/desk/warehouse-console-receiving/<purchase-order>` renders read-only receiving posture, item lines, and bounded receipt history for Warehouse Manager/User without Purchase Receipt creation, stock posting, valuation, native escape, Quick Find, or Sales/Procurement runtime change.
- Warehouse Console Phase W5 outbound picking visibility is documented on 2026-05-28 as a docs-only plan for premium read-only outbound work posture at proposed route `/desk/warehouse-console-worklist/outbound-picking`; Pick List creation/submission, Delivery Note creation/submission, packing, shipping, dispatch, stock reservation, valuation, native escape, Quick Find, and Sales/Procurement runtime changes remain excluded.
- Warehouse Console Phase W5B Picking Review is protected on 2026-05-29 at `724ccd2e09857c1df4fa85a7b2ec604448538e07`; `/desk/warehouse-console-worklist/outbound-picking` and `/desk/warehouse-console-picking/<sales-order>` provide read-only outbound posture and picking review without Pick List, Delivery Note, reservation, stock posting, valuation, native escape, Quick Find, or Sales/Procurement runtime change.
- Warehouse Console Phase W6A Stock Exceptions is protected on 2026-05-29 at `982edba`; `/desk/warehouse-console-worklist/stock-exceptions` renders read-only grouped stock exception posture for Warehouse Manager/User, accepts live empty-state data safely, and preserves no stock mutation, valuation/accounting/commercial exposure, native escape, Quick Find/Search, or Sales/Procurement runtime change.
- Warehouse Console Phase W6B Stock Exception Review is protected on 2026-05-29 at `edd9c7e`; `/desk/warehouse-console-stock-exception/<encoded-context>` renders read-only exception review and custom related Warehouse routes without Stock Entry, Pick List, Delivery Note, Purchase Receipt, reservation, reconciliation, valuation, native escape, Quick Find/Search, or Sales/Procurement runtime change.
- Warehouse Console Phase W7A Stock Posture Review is protected on 2026-05-29 at `8ce0961`; `/desk/warehouse-console-stock-posture/<encoded-context>` renders read-only item/warehouse stock posture, inbound cover, open demand, and custom related route context without stock mutation, valuation/accounting/commercial exposure, native escape, Quick Find/Search, or Sales/Procurement runtime change.
- Warehouse Console Phase W8 Movement Visibility is documented on 2026-05-29 as a docs-only design plan for a proposed read-only movement visibility worklist at `/desk/warehouse-console-worklist/movement-visibility`; Stock Entry creation/submission, Stock Ledger native report escape, Stock Balance native report escape, transfer execution, reconciliation, valuation/accounting/commercial exposure, Quick Find/Search, and Sales/Procurement runtime changes remain excluded.
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
- Procurement Console route names are active protected Procurement entries including `procurement-console-home`, `procurement-console`, `procurement-console-worklist`, `procurement-console-report`, `procurement-console-po-follow-up`, `procurement-console-supplier`, `procurement-console-item`, `procurement-console-purchase-request-review`, `procurement-console-purchase-request-form`, `procurement-console-rfq-review`, `procurement-console-rfq-form`, `procurement-console-supplier-quotation-review`, `procurement-console-supplier-quotation-form`, and `procurement-console-purchase-order-form`.
- `/desk/procurement-console-worklist/<queue-key>` uses the shared worklist shell.
- `/desk/procurement-console-report/<report-key>` uses the shared report shell for Quote Comparison, Purchase Order Analysis, Demand-to-Order Coverage, and Item Purchase History.
- Phase 7D1 supersedes normal-role Procurement native create/open form exceptions. Managed PR/RFQ/SQ/PO draft forms are the productized create/edit surfaces; normal Procurement users and managers must not receive raw ERPNext form escape links.
- Warehouse Console W3/W3A protected route is `/desk/warehouse-console`; Warehouse operational users landing on `/desk` or `/app` are routed to the Warehouse Console unless an admin or broad cross-workspace bypass applies.
- Warehouse Console W4A protected route is `/desk/warehouse-console-worklist/inbound-receiving`; W4B protected read-only receiving review route is `/desk/warehouse-console-receiving/<purchase-order>`.
- Warehouse Console W5A protected route is `/desk/warehouse-console-worklist/outbound-picking`; W5B protected read-only picking review route is `/desk/warehouse-console-picking/<sales-order>`.
- Warehouse Console W6A protected route is `/desk/warehouse-console-worklist/stock-exceptions`.
- Warehouse Console W6B protected read-only stock exception review route is `/desk/warehouse-console-stock-exception/<encoded-context>`.
- Warehouse Console W7A protected read-only stock posture review route is `/desk/warehouse-console-stock-posture/<encoded-context>`.

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

- `warehouse-console-phase-w5-outbound-picking-visibility-design-plan-2026-05-28.md`
- `warehouse-console-phase-w6a-stock-exceptions-baseline-2026-05-29.md`
- `warehouse-console-phase-w6b-stock-exception-review-baseline-2026-05-29.md`
- `warehouse-console-phase-w7a-stock-posture-review-baseline-2026-05-29.md`
- `warehouse-console-phase-w8-movement-visibility-design-plan-2026-05-29.md`
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
- `procurement-console-phase7d-native-escape-closure-and-manager-capability-plan-2026-05-17.md`
- `procurement-console-phase7d1-native-escape-closure-baseline-2026-05-18.md`
- `procurement-console-phase7e-operations-capability-gap-audit-2026-05-18.md`
- `procurement-console-phase7e1-supplier-buying-profile-contact-readiness-design-plan-2026-05-18.md`
- `procurement-console-phase7e2-buying-item-procurement-context-design-plan-2026-05-19.md`
- `procurement-console-phase7e2a-buying-item-procurement-context-baseline-2026-05-19.md`
- `procurement-console-phase7e3-manager-review-action-readiness-design-plan-2026-05-19.md`
- `procurement-console-phase7g-quick-find-operations-review-2026-05-19.md`
- `procurement-console-phase7h-operations-realism-audit-main-agent-handover-2026-05-20.md`
- `procurement-console-phase7h1-readiness-inference-exception-queue-baseline-2026-05-20.md`
- `procurement-console-phase7i-full-freeze-audit-baseline-2026-05-20.md`
- `procurement-console-phase7j-ux-information-architecture-redesign-plan-2026-05-20.md`
- `procurement-console-phase7j1d-readiness-review-polish-baseline-2026-05-23.md`
- `procurement-console-phase7j2-supplier-item-detail-tabs-design-plan-2026-05-23.md`
- `procurement-console-phase7j2b-supplier-item-tab-simplification-review-2026-05-24.md`
- `procurement-console-phase7j2c-supplier-item-tab-simplification-baseline-2026-05-24.md`
- `procurement-console-phase7k-overview-quick-find-baseline-2026-05-24.md`
- `procurement-console-phase7l4-owner-facing-copy-search-polish-baseline-2026-05-25.md`
- `procurement-console-final-freeze-closure-2026-05-25.md`
- `warehouse-console-onboarding-context-audit-2026-05-25.md`
- `warehouse-console-phase-w1-industry-research-and-roadmap-2026-05-26.md`
- `warehouse-console-phase-w2-route-action-inventory-and-protection-plan-2026-05-26.md`
- `warehouse-console-phase-w3-read-only-foundation-and-landing-baseline-2026-05-27.md`
- `warehouse-console-phase-w4-inbound-visibility-design-plan-2026-05-27.md`
- `warehouse-console-phase-w4a-inbound-receiving-visibility-baseline-2026-05-28.md`
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
