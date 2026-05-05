# Procurement Console Phased Implementation Plan v1

Date: 2026-05-03

Source branch: `feature/erpnext-ui-design`

Source repo: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Custom app: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`

Status: implementation plan with accepted Phase 0-3 build decisions. Later phases still require owner approval.

## 0. Current Phase 3 Completion Decisions

Updated: 2026-05-04

The current Procurement Console is a buyer workbench, not a raw DocType launcher. It now includes demand, sourcing, ordering follow-up, supplier context, and item/catalog visibility while keeping Warehouse and Finance execution outside Procurement.

Current accepted surfaces:

- Procurement Overview with buyer priority signals, buying pipeline, sourcing desk, order follow-up, directories, and governed create actions.
- Supplier Directory and productized read-only Supplier Detail.
- Purchase Request and Purchase Order worklists.
- RFQ and Supplier Quotation worklists.
- Governed read-only Supplier Quotation Comparison.
- Productized read-only Purchase Order Follow-up Detail.
- Buying Items directory and productized read-only Buying Item Detail with supplier, price, quotation, and order context.

Current explicit deferrals:

- Do not add a separate Reports catalog page until at least three or four procurement reports are useful and implemented. Quote Comparison remains the only active Procurement report surface for now.
- Do not add Procurement Query, Inquiry, or AI summary yet. That feature is deferred until supplier, item, RFQ, quotation, and purchase order details are stable enough to summarize reliably.
- Do not expose Purchase Receipt, Purchase Invoice, payment, approval, submit, cancel, close, Item Price update, default supplier, or supplier acknowledgment mutation actions from Procurement.
- Do not implement custom create overlays yet. Governed create actions open ERPNext native new-document forms and rely on native permission and workflow behavior.
- Do not make Procurement responsible for warehouse stock operations, receipt execution, invoice settlement, payment, or accounting.

Current native-form exception boundary:

- Native Purchase Request, RFQ, Supplier Quotation, and Purchase Order create/edit forms are accepted Phase 3 exceptions.
- These forms retain Procurement sidebar/chrome where the workspace launches them, but the form body remains ERPNext native and continues to rely on ERPNext permission and workflow control.
- They are not custom premium managed Procurement forms yet.
- Start Buying Work therefore keeps native ERPNext create destinations in Phase 3. This matches the current Sales Console quick-action destination pattern for complex ERPNext documents while making the exception explicit.
- Managed Procurement Forms is the future phase name for replacing these governed native create/edit exceptions with custom managed form wrappers, if owner-approved.
- Supplier create/edit remains deferred to a later Supplier Master phase.
- Item create/edit remains deferred to a later Item Governance phase because Item master changes affect buying, selling, stock, accounting, and reporting.
- Warehouse receiving, Finance billing/payment, Item Price mutation, Default Supplier mutation, submit/cancel/amend/close, and approval/rejection actions remain outside the Phase 3 Procurement surface.

Current ERPNext leakage and governed native access policy:

- Productized Procurement pages are custom workspace pages, worklists, reports, and read-only review/detail pages controlled by ERP Workspace UI. Their primary row actions must stay inside productized Procurement routes.
- Productized worklists must not expose generic `Open ERP Form` as the primary row action. Purchase Request rows use `Review Request`, RFQ rows use `Review RFQ`, and Supplier Quotation rows use `Review Quote`.
- Purchase Request Review, RFQ Review, and Supplier Quotation Review are productized read-only buyer review pages. They provide document context, status, dates, supplier/request references, and item lines without exposing workflow mutation shortcuts.
- If native ERP form access is needed for an authorized user, it is a secondary governed action inside the productized review/detail toolbar, not a default row action on every worklist row.
- Governed native create/edit forms opened from Start Buying Work may show ERPNext workflow controls such as `Get Items From`, `Tools`, `Save`, `Add row`, `Add multiple`, grid controls, download/upload tools, and document conversion helpers. These are allowed only inside the intentionally native form body and remain governed by ERPNext permissions and workflow.
- Bad leakage means a productized Procurement page sends users to ERPNext native list/form pages as the default review action without a custom buyer review surface. Allowed native controls inside governed create/edit forms are not leakage.

Current shared UI contract decisions:

- Procurement Overview direct route must not render as sidebar-only blank content. The route lifecycle must render a stable buyer workbench shell by first paint and must replace, not stack, on back/forward or repeated navigation.
- Shared direct-route pruning must never remove a newer ready shell from an older detached loading shell. Delayed cleanup must verify the keep-node is still connected before pruning.
- Worklist and report date windows must keep related Date From and Date To fields on the same row at desktop widths when space allows, with responsive stacking only on narrower widths.
- Productized detail pages use the compact shared child/detail header and compact toolbar controls. Back, Refresh, and governed native form actions must not use large Overview action-card styling.
- Productized detail and child tables use the universal shared row-link/table action affordance for document navigation. Procurement-specific colored PO link pills are not part of the accepted shared contract.
- Supplier Detail and Buying Item Detail purchase order rows route to productized Procurement PO Follow-up Detail, not native Purchase Order forms.
- Productized Procurement pages must not expose receive, bill, pay, approve, reject, submit, cancel, amend, close, Item Price update, or Default Supplier mutation actions.

## 1. Planning Context

Procurement Console is the next first-wave ERP workspace after the frozen Sales Console.

The matrix name is `Procurement Console`; this plan does not rename it.

Sales Console remains frozen under `sales-console-freeze-v1`. It must not be renamed, refactored, or disturbed unless a shared component contract fix is explicitly approved.

The source-of-truth order for this workspace is:

1. Current code in the clean UI branch.
2. ERPNext native buying, stock, accounting, permission, and workflow behavior.
3. The workspace matrix.
4. Golden Rule and shared component contracts.
5. Sales Console as reference implementation.
6. Screenshots or older opinions.

## 2. Approved Owner Decisions

These decisions are locked for implementation planning until the owner revises them:

1. Procurement Console must not become the default app or Desk home for Purchase roles in Phase 0. Default routing can be enabled only after Phase 1 is usable and separately owner-approved.
2. Finance and Executive approvers must not receive broad Procurement Console access in v1. Their visibility remains restricted unless a specific Purchase Order workflow approval use case is approved.
3. Supplier Directory is read-only in Phase 1. Supplier create/edit is deferred.
4. Item Price updates are excluded from v1. Read-only price review can be considered only in a later phase.
5. Supplier acknowledgment is only an internal follow-up signal unless current ERPNext exposes a reliable native acknowledgment feature for the inspected site/version.

Phase scope gates:

- Phase 0 is foundation only: registry, routes, placeholders, unavailable/restricted states, and tests.
- Phase 1 is the first usable buyer workbench: Overview, Suppliers, Purchase Requests, and Purchase Orders.
- Phase 2 owns RFQ and Supplier Quotation comparison.
- Phase 3 upgrades Purchase Order control and follow-up beyond Phase 1 basic PO visibility.
- Phase 4 and Phase 5 are later phases and must not block the core buyer workbench.

## 3. Business Purpose

Procurement Console is the buyer workbench for deciding what to buy, who to buy from, what needs approval, and which supplier or order needs follow-up.

It must not become a raw list of purchase DocTypes. It should answer practical buyer questions:

- What purchase requests need sourcing action?
- Which RFQs need supplier response?
- Which supplier quotations need comparison?
- Which purchase orders need approval or supplier follow-up?
- Which purchase orders are late or not yet received?
- Which suppliers are risky on price, delivery, or response?
- What has been ordered, received, and billed, without taking ownership from Warehouse or Finance?

## 4. Global Ownership Boundary

Procurement Console owns:

- Supplier and buying decision workflow.
- Purchase request sourcing visibility.
- RFQ and supplier quotation review.
- Purchase order creation, approval posture, and supplier follow-up.
- Supplier performance and buying price review.
- Controlled downstream visibility for receipt and billing status.

Warehouse Console owns:

- Physical stock execution.
- Purchase receipt operation.
- Warehouse receiving, putaway, picking, packing, transfer, stock movement, and stock reconciliation.
- Warehouse-led shortage and movement execution.

Finance Console owns:

- Purchase invoice accounting control.
- Payable settlement.
- Payment Entry.
- Journal Entry.
- Financial exposure, ledger, tax, and payable aging decisions.

Procurement may show receipt and billing posture only as downstream visibility. It must not present Purchase Receipt or Purchase Invoice work as buyer-owned execution.

## 5. Proposed Route Family

These routes are reserved for Procurement Console implementation:

- Launcher: `procurement-console-home`
- Home: `procurement-console`
- Worklist: `procurement-console-worklist`
- Report: `procurement-console-report`

Route paths:

- `/desk/procurement-console-home`
- `/desk/procurement-console`
- `/desk/procurement-console-worklist`
- `/desk/procurement-console-report`

Do not reuse Sales route keys or Sales backend method names.

## 6. Proposed Backend Package

Use a domain split instead of one large file:

- `erp_workspace_ui.procurement_console.service`
- `erp_workspace_ui.procurement_console.worklist`
- `erp_workspace_ui.procurement_console.report`
- `erp_workspace_ui.procurement_console.suppliers`
- `erp_workspace_ui.procurement_console.requests`
- `erp_workspace_ui.procurement_console.sourcing`
- `erp_workspace_ui.procurement_console.purchase_orders`
- `erp_workspace_ui.procurement_console.downstream_visibility`

Whitelisted entrypoints:

- `erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap`
- `erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context`
- `erp_workspace_ui.procurement_console.service.search_procurement_console_workspace`
- `erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context`
- `erp_workspace_ui.procurement_console.report.get_procurement_console_report_context`

Internal modules should be called by these entrypoints and should not create independent public surfaces unless approved.

## 7. Shared Component Position

Procurement Console should reuse existing shared shells first:

- Workspace console runtime.
- Workspace sidebar.
- List page shell.
- Report page shell.
- Child page/detail shell.
- Shared filter command strip.
- Shared table/result state handling.
- Shared action target contract.

Do not create a new shared component unless the existing shell cannot support a real procurement requirement.

The only likely new shared need is a comparison matrix pattern for supplier quotations. That should be deferred until Phase 2 proves the report/list shells cannot serve the requirement.

## 8. State Contract

Procurement must use state kinds consistently:

- `ready`: valid payload with usable data.
- `empty`: valid request and permission, but no matching records.
- `restricted`: user is authenticated but lacks permission or role access.
- `unavailable`: ERP feature, report, setup, or workspace route is not available/configured.
- `error`: real technical failure only.

Restricted or unavailable states must not be encoded as generic errors.

## 9. Phase 0: Foundation and Registry

### Business Goal

Make Procurement Console a registered workspace with correct identity, routes, roles, placeholder payloads, and backend contracts before any business page implementation.

This phase proves the multi-workspace foundation can host Procurement without disturbing the frozen Sales Console.

Phase 0 must not make Procurement Console the default app or Desk home for Purchase roles.

### Included Pages

- Procurement launcher page placeholder.
- Procurement home page placeholder.
- Procurement worklist route placeholder.
- Procurement report route placeholder.

Pages should return governed `unavailable` or controlled placeholder payloads until later phases add business data.

No sidebar item, home card, queue, or report should be advertised as ready in Phase 0.

### Included Queues

No active business queues are included.

The following queue keys may be reserved in registry or route-contract tests, but they must not be rendered in navigation or presented as ready:

- `supplier_directory`
- `purchase_request_directory`
- `requests_to_source`
- `rfq_directory`
- `rfqs_awaiting_supplier_response`
- `supplier_quotation_directory`
- `supplier_quotations_to_compare`
- `purchase_order_directory`
- `purchase_orders_pending_approval`
- `purchase_orders_late_or_unreceived`
- `pending_receipt_visibility`
- `billing_status_visibility`
- `supplier_price_review`

### Included Reports

No active business reports are included.

The following report keys may be reserved in contract tests, but they must not be advertised as ready:

- `supplier_quotation_comparison`
- `procurement_tracker`
- `purchase_order_analysis`
- `purchase_trends`
- `supplier_performance`
- `price_variance_review`
- `receipt_visibility`
- `billing_visibility`

### Included DocTypes

Registry only:

- `Supplier`
- `Supplier Group`
- `Item`
- `Item Price`
- `Item Supplier`
- `Material Request`
- `Request for Quotation`
- `Supplier Quotation`
- `Purchase Order`
- `Purchase Receipt`
- `Purchase Invoice`
- `Buying Settings`
- `Supplier Scorecard`

### Ownership Boundary With Warehouse and Finance

Registry must mark `Purchase Receipt` and `Purchase Invoice` as downstream visibility surfaces, not Procurement-owned execution DocTypes.

Registry and boot behavior must not grant broad Procurement access to Finance or Executive approver roles.

### Route Keys

- `procurement-console-home`
- `procurement-console`
- `procurement-console-worklist`
- `procurement-console-report`

### Backend Modules and Methods

Create the Procurement package and entrypoint stubs:

- `service.get_procurement_console_bootstrap`
- `service.get_procurement_console_sidebar_context`
- `service.search_procurement_console_workspace`
- `worklist.get_procurement_console_worklist_context`
- `report.get_procurement_console_report_context`

Expected placeholder state:

- Known route, unsupported queue/report: `unavailable`.
- Authenticated but wrong role family: `restricted`.
- Guest: permission error.

### Shared Components Used

- Workspace registry.
- Workspace console runtime.
- Workspace sidebar.
- List page shell.
- Report page shell.

### Permission and Restricted-State Rules

Allowed role family:

- `Purchase User`
- `Purchase Manager`
- `Purchase Master Manager`

Approval-related roles remain restricted by default:

- `Finance Lead Approver`
- `Executive Approver`

These approver roles must not automatically gain Procurement Console buyer access unless a specific PO workflow approval use case is approved.

### Tests and Browser Smoke Required

Tests:

- Python compile for new package.
- Registry contract test for Procurement routes and methods.
- Registry copy-safety test.
- Sales frozen route/method regression test.
- Default app/home regression test confirming Purchase roles are not routed to Procurement in Phase 0.
- JS syntax check for touched runtime/page files.
- Restricted direct URL test for users without procurement roles.
- Placeholder state-kind tests for known unavailable queue/report.

Browser smoke:

- Procurement launcher opens for Purchase Manager.
- Procurement home opens and refreshes.
- Worklist route with unknown queue shows unavailable, not error.
- Report route with unknown report shows unavailable, not error.
- Sales Console still opens on frozen routes.

### Acceptance Criteria

- Procurement exists in backend and frontend workspace registry.
- Sales registry values are unchanged.
- Procurement routes are unique and not Sales-derived.
- Purchase roles are not made default-routed to Procurement in Phase 0.
- Unauthorized users see `restricted`.
- Unknown Procurement queue/report routes show `unavailable`.
- No business page claims final readiness.

## 10. Phase 1: Buyer Workbench Core

### Business Goal

Give buyers a practical daily overview of open procurement demand and supplier/order workload.

This phase should answer: what needs buyer attention today?

Phase 1 is the first usable buyer workbench. Only after this phase is owner-approved may default app/home routing for Purchase roles be considered.

### Included Pages

- Procurement Overview.
- Supplier Directory, read-only.
- Purchase Request Directory.
- Purchase Order Directory, basic version.

### Included Queues

- `requests_to_source`
- `purchase_requests_pending_order`
- `purchase_orders_pending_approval`
- `purchase_orders_open`
- `purchase_orders_late_or_unreceived`

Supplier follow-up beyond basic PO visibility is deferred to Phase 3.

### Included Reports

No full report pages yet.

The home may show lightweight summary metrics derived from native DocTypes:

- Open purchase requests.
- Purchase requests not fully ordered.
- Purchase orders pending approval.
- Submitted purchase orders not completed.
- Late required-by dates.

### Included DocTypes

- `Supplier`
- `Supplier Group`
- `Material Request`
- `Purchase Order`
- `Buying Settings`

Supplier create/edit is excluded from Phase 1.

### Ownership Boundary With Warehouse and Finance

Warehouse:

- Procurement may show `per_received`, required date, and receipt posture from Purchase Order.
- Procurement must not create or submit Purchase Receipt in this phase.

Finance:

- Procurement may show `per_billed` as a buyer awareness field only.
- Procurement must not create Purchase Invoice, Payment Entry, or Journal Entry.

### Route Keys

Worklist queue keys:

- `supplier_directory`
- `purchase_request_directory`
- `requests_to_source`
- `purchase_order_directory`
- `purchase_orders_pending_approval`
- `purchase_orders_open`
- `purchase_orders_late_or_unreceived`

### Backend Modules and Methods

Entrypoints:

- `service.get_procurement_console_bootstrap`
- `service.get_procurement_console_sidebar_context`
- `worklist.get_procurement_console_worklist_context`

Internal modules:

- `requests.build_purchase_request_directory`
- `requests.build_requests_to_source`
- `purchase_orders.build_purchase_order_directory`
- `purchase_orders.build_purchase_orders_pending_approval`
- `purchase_orders.build_late_or_unreceived_purchase_orders`
- `suppliers.build_supplier_directory`

### Shared Components Used

- Workspace console runtime.
- Sidebar.
- List page shell.
- Shared KPI/metric cards.
- Shared action target contract.
- Shared filter controls: company, date range, supplier, status, workflow state.

### Permission and Restricted-State Rules

- `Material Request`: require read permission and filter to `material_request_type = Purchase`.
- `Purchase Order`: require read permission.
- `Supplier`: require read permission.
- Supplier Directory is read-only. No create/edit action should appear.
- Pending approval queue should use ERPNext workflow state when available.
- If `workflow_state` does not exist or workflow is inactive, the queue should degrade to `unavailable` or use DocStatus/status only if explicitly documented.

### Tests and Browser Smoke Required

Tests:

- Queue registry tests for all Phase 1 queues.
- State-kind tests for no permission vs no records.
- Purchase Request filters enforce `Purchase` only.
- Purchase Order pending approval respects configured workflow states.
- Supplier Directory exposes no create/edit action.
- Action order tests: Refresh, Reset, Apply, then contextual create/open actions.
- Python unit tests with mocked Frappe calls.
- Python compile.
- JS syntax check for touched files.

Browser smoke:

- Overview loads for Purchase Manager.
- Overview loads for Purchase User with correct allowed actions.
- Supplier Directory Apply/Reset/Refresh.
- Purchase Request Directory Apply/Reset/Refresh.
- Purchase Order Directory Apply/Reset/Refresh.
- Direct URL restricted route for Sales-only user.

### Acceptance Criteria

- Buyer can land on Procurement Console and see daily procurement workload.
- Supplier, request, and PO directories are usable.
- Purchase request queues do not include transfer/manufacture/issue requests.
- Purchase order approval queue reflects workflow state.
- Supplier Directory is read-only.
- Default routing remains disabled unless a separate owner approval is given after Phase 1 review.
- Empty, restricted, unavailable, and error states are visually and semantically distinct.

## 11. Phase 2: RFQ and Supplier Quotation Comparison

### Business Goal

Support sourcing decisions: send RFQs, track supplier response, review supplier quotations, and compare quoted prices and terms.

This phase should answer: which supplier should we choose?

### Included Pages

- RFQ Directory.
- RFQ Detail.
- Supplier Quotation Directory.
- Supplier Quotation Review.
- Supplier Quotation Comparison report page.

### Included Queues

- `rfq_directory`
- `rfqs_draft`
- `rfqs_awaiting_supplier_response`
- `rfqs_partially_quoted`
- `supplier_quotation_directory`
- `supplier_quotations_to_compare`
- `supplier_quotations_expiring`
- `requests_without_supplier_quotation`

### Included Reports

- `supplier_quotation_comparison`, based on ERPNext native `Supplier Quotation Comparison`.

Optional derived report if native report is insufficient:

- `rfq_response_status`, based on RFQ supplier rows and supplier quotation links.

### Included DocTypes

- `Request for Quotation`
- `Request for Quotation Supplier`
- `Request for Quotation Item`
- `Supplier Quotation`
- `Supplier Quotation Item`
- `Material Request`
- `Supplier`
- `Item`
- `Item Price`, read-only context only where ERPNext uses it for buying rates.

### Ownership Boundary With Warehouse and Finance

Warehouse:

- Target warehouse fields may be displayed as requested delivery context.
- No warehouse receiving operation belongs in this phase.

Finance:

- Taxes, charges, payment terms, and currency can be displayed as buying decision inputs.
- No payable booking, invoice approval, or payment action belongs in this phase.

### Route Keys

Worklist queue keys:

- `rfq_directory`
- `rfq_detail`
- `rfqs_awaiting_supplier_response`
- `supplier_quotation_directory`
- `supplier_quotation_review`
- `supplier_quotations_to_compare`
- `requests_without_supplier_quotation`

Report keys:

- `supplier_quotation_comparison`
- `rfq_response_status`

### Backend Modules and Methods

Entrypoints:

- `worklist.get_procurement_console_worklist_context`
- `report.get_procurement_console_report_context`

Internal modules:

- `sourcing.build_rfq_directory`
- `sourcing.build_rfq_detail`
- `sourcing.build_rfq_response_queues`
- `sourcing.build_supplier_quotation_directory`
- `sourcing.build_supplier_quotation_review`
- `report.build_supplier_quotation_comparison`

Use `frappe.desk.query_report.run` for native report integration where reliable.

### Shared Components Used

- List page shell.
- Report page shell.
- Child page/detail shell.
- Shared filter command strip.
- Shared action targets.

Possible new shared component:

- Supplier comparison matrix, only if list/report shell cannot show item/supplier comparison clearly.

### Permission and Restricted-State Rules

- RFQ read required for RFQ queues.
- Supplier Quotation read required for quotation queues and comparison.
- Create actions are shown only if user has create permission on the target DocType.
- Submit/approval actions are not custom-implemented unless workflow and permissions are explicitly modeled.
- Supplier portal behavior must remain native ERPNext behavior.
- Supplier acknowledgment, if needed, is represented only as an internal follow-up signal unless a reliable native feature is confirmed.

### Tests and Browser Smoke Required

Tests:

- RFQ queue status classification.
- Supplier quotation comparison state handling.
- Requests without supplier quotation query contract.
- Permission tests for RFQ-only restricted state.
- Native report unavailable fallback.
- Action visibility tests for create/open actions.

Browser smoke:

- RFQ Directory filters and refresh.
- Supplier Quotation Directory filters and refresh.
- Supplier Quotation Comparison with valid date/company filters.
- Direct report route restricted for role without report access.
- Empty comparison state with filters that return no quotations.

### Acceptance Criteria

- Buyer can identify RFQs with missing supplier responses.
- Buyer can review supplier quotations from a governed Procurement route.
- Comparison page uses ERPNext business truth and handles no-data cases cleanly.
- No supplier selection logic is invented on the frontend.

## 12. Phase 3: Purchase Order Control and Follow-Up

### Business Goal

Turn approved sourcing decisions into controlled purchase orders and give purchase managers deeper visibility into approvals, late orders, and supplier follow-up beyond the basic Phase 1 PO view.

This phase should answer: which POs need approval, confirmation, or escalation?

### Included Pages

- Purchase Order Directory, full version.
- Purchase Order Follow-Up Queue.
- Purchase Order Detail.
- PO Approval Queue.
- Late or At-Risk PO Queue.

### Included Queues

- `purchase_order_directory`
- `purchase_orders_pending_approval`
- `purchase_orders_rejected`
- `purchase_orders_to_receive`
- `purchase_orders_late_or_unreceived`
- `purchase_orders_partially_received`
- `purchase_orders_pending_supplier_follow_up`

Gated queues, not advertised unless owner approves a specific PO workflow approval use case:

- `purchase_orders_pending_finance_review`
- `purchase_orders_pending_executive_approval`

### Included Reports

- `purchase_order_analysis`, based on ERPNext native `Purchase Order Analysis`.
- `procurement_tracker`, based on ERPNext native `Procurement Tracker`.

### Included DocTypes

- `Purchase Order`
- `Purchase Order Item`
- `Supplier`
- `Supplier Quotation`
- `Material Request`
- `Purchase Receipt`, visibility only
- `Purchase Invoice`, visibility only

### Ownership Boundary With Warehouse and Finance

Warehouse:

- Procurement can show quantity ordered, received quantity, pending quantity, required date, and lateness.
- Procurement must route receipt execution to Warehouse/native Stock surfaces, not present it as buyer-owned.

Finance:

- Procurement can show billed percentage and invoice existence as awareness.
- Finance review workflow state can be shown when the Purchase Order workflow requires it.
- Procurement must not grant broad Finance or Executive approver access.
- Procurement must not expose Finance or Executive approval actions unless the owner approves that specific PO workflow use case and the backend confirms the current user can perform the action.

### Route Keys

Worklist queue keys:

- `purchase_order_directory`
- `purchase_order_detail`
- `purchase_orders_pending_approval`
- `purchase_orders_late_or_unreceived`
- `purchase_orders_partially_received`
- `purchase_orders_pending_supplier_follow_up`

Gated route keys:

- `purchase_orders_pending_finance_review`
- `purchase_orders_pending_executive_approval`

Report keys:

- `purchase_order_analysis`
- `procurement_tracker`

### Backend Modules and Methods

Entrypoints:

- `worklist.get_procurement_console_worklist_context`
- `report.get_procurement_console_report_context`

Internal modules:

- `purchase_orders.build_purchase_order_directory`
- `purchase_orders.build_purchase_order_detail`
- `purchase_orders.build_purchase_order_approval_queues`
- `purchase_orders.build_late_or_unreceived_purchase_orders`
- `purchase_orders.build_supplier_follow_up`
- `report.build_purchase_order_analysis`
- `report.build_procurement_tracker`

### Shared Components Used

- List page shell.
- Report page shell.
- Child detail shell.
- Shared action band.
- Shared workflow/status badges.
- Shared state rendering.

### Permission and Restricted-State Rules

- PO read permission is required for all PO queues.
- Workflow-specific queues must respect configured workflow state names.
- Direct approval/reject actions should only be exposed if the backend confirms the current user can perform that workflow action.
- If workflow is missing or inactive, approval queues should be `unavailable`, not error.
- Supplier acknowledgment is an internal follow-up signal only, unless current ERPNext native behavior proves otherwise.
- Finance and Executive approver routes stay restricted unless explicitly approved.

### Tests and Browser Smoke Required

Tests:

- Purchase Order workflow state classification.
- Pending Finance and Executive review queues restricted by role catalog.
- Late PO date calculation.
- Partial receipt calculation from ERPNext fields.
- No frontend-owned workflow decision tests.
- Supplier acknowledgment follow-up is not treated as native ERPNext truth unless proven.
- Report fallback tests for native report errors.

Browser smoke:

- Purchase Manager opens PO approval queue.
- Purchase User sees restricted or reduced approval actions where appropriate.
- Late PO queue Apply/Reset/Refresh.
- PO detail refresh/back.
- Purchase Order Analysis report route.
- Procurement Tracker report route.

### Acceptance Criteria

- Purchase managers can see and act on approval workload through governed routes.
- Buyers can see open and late orders without owning receipt or finance execution.
- Workflow state is backend-owned and permission-safe.
- Native report fallback is available when the custom report payload fails.

## 13. Phase 4: Supplier Intelligence and Price Review

### Business Goal

Give procurement a supplier performance and buying-cost view that supports negotiation, sourcing quality, and risk review.

This phase should answer: which suppliers or prices need attention?

Phase 4 is a later phase. It must not block the Phase 1 buyer workbench or Phase 3 PO control readiness.

### Included Pages

- Supplier Detail.
- Supplier Performance Report.
- Supplier Price Review, read-only.
- Item Supplier / Buying Price view, read-only.

### Included Queues

- `supplier_directory`
- `supplier_detail`
- `supplier_follow_up`
- `supplier_scorecard_attention`
- `supplier_price_review`
- `items_with_buying_price_changes`
- `items_without_active_supplier_price`

### Included Reports

- `supplier_performance`
- `price_variance_review`
- `item_wise_purchase_history`, based on ERPNext native `Item-wise Purchase History`.
- Optional `purchase_trends`, based on `Purchase Order Trends` or `Purchase Analytics`.

### Included DocTypes

- `Supplier`
- `Supplier Group`
- `Supplier Scorecard`
- `Supplier Scorecard Period`
- `Supplier Scorecard Criteria`
- `Item`
- `Item Supplier`
- `Item Price`
- `Purchase Order`
- `Purchase Receipt`, visibility-derived performance only
- `Supplier Quotation`

### Ownership Boundary With Warehouse and Finance

Warehouse:

- Delivery timeliness and accepted/rejected quantity may be shown as supplier performance inputs.
- Procurement must not manage quality inspection or warehouse receipt correction.

Finance:

- Purchase value, billed amount, and price variance may be used for buying analysis.
- Procurement must not expose payable aging, settlement, or payment action as buyer-owned work.

### Route Keys

Worklist queue keys:

- `supplier_directory`
- `supplier_detail`
- `supplier_scorecard_attention`
- `supplier_price_review`
- `items_without_active_supplier_price`

Report keys:

- `supplier_performance`
- `price_variance_review`
- `item_wise_purchase_history`
- `purchase_trends`

### Backend Modules and Methods

Entrypoints:

- `worklist.get_procurement_console_worklist_context`
- `report.get_procurement_console_report_context`

Internal modules:

- `suppliers.build_supplier_detail`
- `suppliers.build_supplier_performance_context`
- `suppliers.build_supplier_scorecard_attention`
- `suppliers.build_supplier_price_review`
- `report.build_supplier_performance`
- `report.build_price_variance_review`
- `report.build_item_wise_purchase_history`
- `report.build_purchase_trends`

### Shared Components Used

- Child page/detail shell.
- List page shell.
- Report page shell.
- Summary/KPI cards.
- Connection cards.
- Shared table shell.

### Permission and Restricted-State Rules

- Supplier read required for supplier pages.
- Supplier Scorecard read may be restricted; if so, supplier performance should show `restricted` for scorecard-specific cards or use approved derived performance metrics.
- Item Price read requires `Purchase Master Manager` in native ERPNext; users without that permission should see restricted price controls, not a generic failure.
- Item Price updates are excluded from v1.
- Any price review is read-only and must not expose save/update actions.

### Tests and Browser Smoke Required

Tests:

- Supplier detail visibility by role.
- Scorecard unavailable/restricted fallback.
- Item Price restricted state.
- Price variance calculation with currency/UOM guardrails.
- Supplier performance report no-data state.
- Search result target contracts for Supplier and Item.

Browser smoke:

- Supplier Directory to Supplier Detail.
- Supplier Performance report.
- Price Review report.
- Restricted read-only Item Price view for user without master role.
- Refresh/back on Supplier Detail.

### Acceptance Criteria

- Procurement can inspect suppliers from a business decision view.
- Supplier performance does not depend solely on optional Scorecard availability.
- Buying price review is permission-safe.
- No Item Price update workflow is introduced in v1.

## 14. Phase 5: Downstream Visibility for Receipt and Billing

### Business Goal

Give buyers controlled visibility into what happened after ordering, without taking over Warehouse receiving or Finance payable work.

This phase should answer: did the order arrive and has it been billed?

Phase 5 is a later phase. It must not block the Phase 1 buyer workbench or Phase 3 PO control readiness.

### Included Pages

- Pending Receipt Visibility.
- Billing Status Visibility.
- PO Downstream Timeline inside Purchase Order Detail.

### Included Queues

- `pending_receipt_visibility`
- `partial_receipt_visibility`
- `overdue_receipt_visibility`
- `billing_status_visibility`
- `unbilled_purchase_order_visibility`
- `partially_billed_purchase_order_visibility`

### Included Reports

- `receipt_visibility`, based on Purchase Order and Purchase Receipt facts.
- `billing_visibility`, based on Purchase Order and Purchase Invoice facts.
- Optional governed links to native Stock/Accounts reports:
  - `Purchase Receipt Trends`
  - `Purchase Register`
  - `Item-wise Purchase Register`

### Included DocTypes

- `Purchase Order`
- `Purchase Order Item`
- `Purchase Receipt`
- `Purchase Receipt Item`
- `Purchase Invoice`
- `Purchase Invoice Item`
- `Supplier`
- `Item`

### Ownership Boundary With Warehouse and Finance

Warehouse:

- Owns creating, submitting, correcting, returning, and closing receipt operations.
- Procurement only shows received quantity, pending quantity, receipt dates, and linked receipt documents.

Finance:

- Owns Purchase Invoice, payable validation, settlement, payment, ledger, and accounting corrections.
- Procurement only shows billed amount/percentage, invoice status, and linked invoice documents if user has permission.

### Route Keys

Worklist queue keys:

- `pending_receipt_visibility`
- `partial_receipt_visibility`
- `overdue_receipt_visibility`
- `billing_status_visibility`
- `unbilled_purchase_order_visibility`
- `partially_billed_purchase_order_visibility`

Report keys:

- `receipt_visibility`
- `billing_visibility`

### Backend Modules and Methods

Entrypoints:

- `worklist.get_procurement_console_worklist_context`
- `report.get_procurement_console_report_context`

Internal modules:

- `downstream_visibility.build_pending_receipt_visibility`
- `downstream_visibility.build_billing_status_visibility`
- `downstream_visibility.build_purchase_order_downstream_timeline`
- `report.build_receipt_visibility_report`
- `report.build_billing_visibility_report`

### Shared Components Used

- List page shell.
- Report page shell.
- Child detail shell.
- Connection cards.
- Status timeline sections if already available in shared child shell.

### Permission and Restricted-State Rules

- If user lacks Purchase Receipt read permission, receipt card or queue should be `restricted`.
- If user lacks Purchase Invoice read permission, billing card or queue should be `restricted`.
- If downstream DocTypes do not exist or reports are unavailable, show `unavailable`.
- No create/submit/cancel actions for Purchase Receipt or Purchase Invoice from Procurement.

### Tests and Browser Smoke Required

Tests:

- Receipt visibility respects Purchase Receipt read permission.
- Billing visibility respects Purchase Invoice read permission.
- Downstream route actions are view-only.
- No Purchase Receipt or Purchase Invoice create actions appear.
- Empty state when no downstream records exist.
- Restricted state when role lacks downstream read.

Browser smoke:

- Pending Receipt Visibility loads.
- Billing Status Visibility loads.
- Purchase Order Detail shows downstream timeline.
- User without Accounts permission sees billing restriction.
- Refresh/back/Apply/Reset on visibility pages.

### Acceptance Criteria

- Buyers can see receipt and billing posture.
- Procurement UI never implies it owns warehouse or finance execution.
- Downstream visibility is permission-safe and view-only.
- Warehouse and Finance boundaries are documented in user-facing behavior and internal docs.

## 15. Phase 6: Freeze Hardening, Docs, Smoke Tests, and Acceptance

### Business Goal

Make Procurement Console freeze-ready as a stable first-wave workspace.

This phase turns working features into a governed, documented, tested workspace suitable for freeze review.

The owner may choose a core freeze after Phases 0-3. Phase 4 supplier intelligence and Phase 5 downstream visibility are later phases and must not block core buyer workbench readiness.

### Included Pages

All accepted Procurement Console pages from the owner-approved freeze scope.

Core freeze candidate after Phases 0-3:

- Launcher.
- Overview.
- Supplier Directory.
- Purchase Request Directory.
- RFQ Directory.
- RFQ Detail.
- Supplier Quotation Directory.
- Supplier Quotation Review.
- Purchase Order Directory.
- Purchase Order Detail.
- Accepted report pages from Phase 2 or 3.

Later freeze additions if Phases 4-5 are accepted:

- Supplier Detail.
- Pending Receipt Visibility.
- Billing Status Visibility.

### Included Queues

All accepted queues from the owner-approved freeze scope.

Queues not implemented by this phase must be removed from active navigation or clearly marked unavailable by route contract.

### Included Reports

Accepted report keys from the owner-approved freeze scope:

- `supplier_quotation_comparison`
- `procurement_tracker`
- `purchase_order_analysis`

Later report keys if Phases 4-5 are accepted:

- `purchase_trends`
- `supplier_performance`
- `price_variance_review`
- `item_wise_purchase_history`
- `receipt_visibility`
- `billing_visibility`

Reports not implemented by this phase must not be advertised as ready.

### Included DocTypes

All accepted Procurement-owned and downstream visibility DocTypes for the owner-approved freeze scope:

- Core buyer-decision: Supplier, Supplier Group, Material Request, RFQ, Supplier Quotation, Purchase Order, Item, Buying Settings.
- Later read-only price/performance review: Item Price, Item Supplier, Supplier Scorecard.
- Downstream visibility only: Purchase Receipt, Purchase Invoice.

### Ownership Boundary With Warehouse and Finance

Freeze documentation must explicitly state:

- Procurement owns buying decisions and supplier follow-up.
- Warehouse owns physical stock execution.
- Finance owns accounting, payables, and payment.
- Procurement receipt/billing pages are visibility-only.
- Finance and Executive approvers do not have broad Procurement Console access unless a specific PO workflow use case is approved.
- Default app/home routing for Purchase roles is enabled only after Phase 1 owner approval.

### Route Keys

Freeze route keys:

- `procurement-console-home`
- `procurement-console`
- `procurement-console-worklist`
- `procurement-console-report`

Freeze worklist/report keys must be documented with final active status.

### Backend Modules and Methods

Freeze must document:

- All whitelisted methods.
- All internal modules.
- Queue builders.
- Report builders.
- Permission rules.
- State-kind rules.
- Native ERP report dependencies.

### Shared Components Used

Freeze must document:

- Existing shared shells reused.
- Any shared shell extension made for Procurement.
- Any new shared component added, with justification and cross-workspace contract.
- Confirmation that Sales Console behavior remains unchanged unless separately approved.

### Permission and Restricted-State Rules

Freeze must prove:

- Guest cannot access Procurement methods.
- Non-procurement users cannot access direct Procurement URLs.
- Purchase User and Purchase Manager have expected differences.
- Purchase Master Manager-only price/master actions are restricted for ordinary buyers.
- Finance/Executive approvers remain restricted unless a specific workflow approval use case is approved.
- Receipt and billing visibility respect Stock/Accounts permissions.
- Item Price update actions do not exist in v1.

### Tests and Browser Smoke Required

Required validation:

- `python3 -m compileall erp_workspace_ui`
- `node --check` for every touched JS file.
- `python3 -m unittest` for related contract/unit tests.
- Registry contract tests.
- Queue state-kind tests.
- Report state-kind tests.
- Action order tests.
- Role visibility tests.
- Restricted direct URL tests.
- Native report fallback tests.
- Docker Playwright smoke where available.
- Browser verification for normal route, refresh, back, Apply, Reset, Refresh, and restricted direct URL.

Recommended role smoke matrix:

- Purchase Manager.
- Purchase User.
- Purchase Master Manager, if test credential exists.
- Sales-only user for restricted route regression.
- Accounts role user for billing visibility boundary, if credential exists.
- Stock role user for receipt visibility boundary, if credential exists.

### Acceptance Criteria

- All active Procurement routes load.
- All advertised sidebar destinations work.
- All advertised queues and reports return correct state kinds.
- No unsupported queue or report is presented as ready.
- Sales Console remains frozen and functional.
- Documentation matches final code.
- Branch has no unrelated live repo changes.
- Work is committed and pushed only after owner approval and validation.

## 16. Suggested Implementation Order After Approval

1. Implement Phase 0 and validate foundation-only registry/routes/placeholders. Do not enable default routing.
2. Implement Phase 1 as the first usable buyer workbench. Ask for owner approval before enabling Purchase-role default routing.
3. Implement Phase 2 for RFQ and Supplier Quotation comparison.
4. Implement Phase 3 for PO approval and follow-up beyond Phase 1 basic PO visibility.
5. Run a core hardening pass for Phases 0-3 if the owner wants an early core freeze.
6. Implement Phase 4 supplier intelligence and read-only price review only when approved as a later phase.
7. Implement Phase 5 receipt/billing visibility only when approved as a later phase.
8. Run Phase 6 hardening, update docs, and request freeze review for the accepted scope.

Each phase should be independently reviewable and should not depend on hidden future work to be useful.

## 17. Resolved Owner Decisions

The owner resolved the previous open decisions as follows:

1. Procurement Console does not become the default app/home for Purchase roles in Phase 0. Default routing is considered only after Phase 1 is usable and owner-approved.
2. Finance/Executive approvers do not receive broad Procurement Console access yet. Visibility remains restricted unless a specific PO workflow approval use case is approved.
3. Supplier Directory is read-only in Phase 1. Supplier create/edit is deferred.
4. Item Price updates are excluded from v1. Read-only price review can be considered in a later phase.
5. Supplier acknowledgment is modeled only as an internal follow-up signal unless current ERPNext has a reliable native feature for it.

Implementation must not begin until the owner approves this phased plan or provides revisions.
