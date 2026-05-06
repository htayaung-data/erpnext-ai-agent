# Shared Core Route and Action Inventory

Date: 2026-05-06
Status: Main Phase 1 baseline inventory
Source repo: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
Branch: `feature/erpnext-ui-design`

## Purpose

This inventory classifies the current Sales Console and Procurement Console route and action surface before workspace-specific recovery work begins.

It is intentionally a governance artifact, not a UI repair plan. Entries marked as governed native exceptions are allowed only under the native exception policy and the route/action manifest. Entries marked as productized pages or productized actions must stay inside the shared core shell and workspace adapter contract.

## Classification Enums

Route/page classifications:

1. `productized_overview`
2. `productized_worklist`
3. `productized_report`
4. `productized_detail`
5. `managed_create_edit`
6. `governed_native_exception`
7. `not_allowed_leakage`

Action classifications:

1. `productized_navigation`
2. `productized_primary_action`
3. `productized_secondary_action`
4. `governed_native_action`
5. `forbidden_mutation`
6. `not_allowed_leakage`

## Sales Route Inventory

| Route or surface | Current owner | Classification | Shell or target | Notes |
| --- | --- | --- | --- | --- |
| `sales-console-home` | Sales adapter | `productized_overview` | launcher handoff | Frozen launcher route. |
| `sales-console` | Sales adapter | `productized_overview` | console runtime | Frozen Sales Console overview. |
| `sales-console-worklist` bare route | Sales adapter | `productized_worklist` | list page shell guarded state | Missing queue shows guarded state. |
| `sales-console-worklist/quotation_directory` | Sales adapter | `productized_worklist` | list page shell | Quotation directory. |
| `sales-console-worklist/quotations_waiting_action` | Sales adapter | `productized_worklist` | list page shell | Quotation action queue. |
| `sales-console-worklist/quotations_awaiting_approval` | Sales adapter | `productized_worklist` | list page shell | Quotation approval visibility queue. |
| `sales-console-worklist/expiring_quotations` | Sales adapter | `productized_worklist` | list page shell | Quotation expiry queue. |
| `sales-console-worklist/sales_order_directory` | Sales adapter | `productized_worklist` | list page shell | Sales Order directory. |
| `sales-console-worklist/open_orders` | Sales adapter | `productized_worklist` | list page shell | Open Sales Orders. |
| `sales-console-worklist/sales_orders_pending_fulfillment` | Sales adapter | `productized_worklist` | list page shell | Fulfillment queue. |
| `sales-console-worklist/partially_delivered_orders` | Sales adapter | `productized_worklist` | list page shell | Partially delivered order queue. |
| `sales-console-worklist/orders_due_soon` | Sales adapter | `productized_worklist` | list page shell | Due-soon queue. |
| `sales-console-worklist/orders_blocked_by_approval` | Sales adapter | `productized_worklist` | list page shell | Approval blocker queue. |
| `sales-console-worklist/customer_follow_up_tasks` | Sales adapter | `productized_worklist` | list page shell | Customer follow-up queue. |
| `sales-console-worklist/invoices_outstanding` | Sales adapter | `productized_worklist` | list page shell | Collections visibility queue. |
| `sales-console-worklist/sales_returns_in_progress` | Sales adapter | `productized_worklist` | list page shell | Return/exception visibility queue. |
| `sales-console-worklist/customer_directory` | Sales adapter | `productized_worklist` | list page shell | Customer directory. |
| `sales-console-worklist/customer_detail/<customer>` | Sales adapter | `productized_detail` | list/detail pattern | Productized customer detail. |
| `sales-console-worklist/customer_editor` | Sales adapter | `managed_create_edit` | form-panel pattern | Productized Customer create. |
| `sales-console-worklist/customer_editor/<customer>` | Sales adapter | `managed_create_edit` | form-panel pattern | Productized Customer edit. |
| `sales-console-worklist/item_directory` | Sales adapter | `productized_worklist` | list page shell | Item directory. |
| `sales-console-worklist/item_detail/<item>` | Sales adapter | `productized_detail` | list/detail pattern | Productized item detail. |
| `sales-console-report` bare route | Sales adapter | `productized_report` | report page shell guarded state | Missing report key shows guarded state. |
| `sales-console-report/sales_analytics` | Sales adapter | `productized_report` | report page shell | Sales Analytics. |
| `sales-console-report/sales_order_analysis` | Sales adapter | `productized_report` | report page shell | Sales Order Analysis. |
| `sales-console-report/trend_analysis` | Sales adapter | `productized_report` | report page shell | Active productized trend report. |
| `sales-console-report/quotation_trends` | Sales adapter | `productized_report` | report page shell | Compatibility alias into Trend Analysis. |
| `sales-console-report/lost_quotations` | Sales adapter | `productized_report` | report page shell | Lost Quotations. |
| `sales-console-report/collections_status` | Sales adapter | `productized_report` | report page shell | Collections Status. |
| `sales-console-report/payment_terms_status_sales_order` | Sales adapter | `productized_report` | report page shell | Compatibility alias into Collections Status. |
| `sales-console-report/item_wise_sales_history` | Sales adapter | `productized_report` | report page shell | Item-wise Sales History. |
| Native `Quotation` form route | Sales adapter + ERPNext | `managed_create_edit` | child page managed form | Wired through `doctype_js`. ERPNext remains transaction truth. |
| Native `Sales Order` form route | Sales adapter + ERPNext | `managed_create_edit` | child page managed form | Wired through `doctype_js`. ERPNext remains transaction truth. |
| Native `Delivery Note` form route | Sales adapter + ERPNext | `managed_create_edit` | child page managed form | Wired through `doctype_js`. ERPNext remains transaction truth. |
| Native `Sales Invoice` form route | Sales adapter + ERPNext | `managed_create_edit` | child page managed form | Wired through `doctype_js`. ERPNext remains transaction truth. |

## Sales Action Inventory

| Action or pattern | Source | Classification | Target | Notes |
| --- | --- | --- | --- | --- |
| `refresh` | Worklists/reports/details | `productized_secondary_action` | current productized shell | Must refresh in place where shell supports it. |
| `reset_filters` | Worklists/reports | `productized_secondary_action` | current productized shell | Must clear visible controls and data. |
| `apply_filters` | Worklists/reports | `productized_primary_action` | current productized shell | Must apply via AJAX/in-place reload. |
| `back_to_console` | Sales reports | `productized_navigation` | `sales-console` | Report toolbar navigation. |
| `open_record` row pattern | Sales directories/queues/reports | `productized_navigation` | productized route or managed document form | Productized target preferred; approved managed form target allowed for Sales documents. |
| `new_quotation` | Quotation directory | `governed_native_action` | native new `Quotation` managed form | ERPNext create workflow remains transaction truth. |
| `new_sales_order` | Sales Order directory | `governed_native_action` | native new `Sales Order` managed form | ERPNext create workflow remains transaction truth. |
| `create_customer` | Customer directory | `productized_primary_action` | `customer_editor` | Server-gated Customer create. |
| `edit_customer` | Customer detail | `productized_secondary_action` | `customer_editor/<customer>` | Server-gated Customer edit. |
| `back_to_customers` | Customer detail/editor | `productized_navigation` | `customer_directory` | Productized navigation. |
| `back_to_items` | Item detail | `productized_navigation` | `item_directory` | Productized navigation. |
| Report cell drilldown action pattern | Sales reports | `productized_navigation` | productized worklist/report/native report fallback as declared | Must not silently leak to raw ERP pages when a productized route exists. |
| Native form Save/Submit/Print/Email/Assign/Share controls | Managed Sales document forms | `governed_native_action` | ERPNext form lifecycle | Allowed only because the form route is classified as managed create/edit. |

## Procurement Route Inventory

| Route or surface | Current owner | Classification | Shell or target | Notes |
| --- | --- | --- | --- | --- |
| `procurement-console-home` | Procurement adapter | `productized_overview` | launcher handoff | Purchase-role home routing is owner-approved. |
| `procurement-console` | Procurement adapter | `productized_overview` | console runtime | Phase 3 buyer workbench. |
| `procurement-console-worklist` bare route | Procurement adapter | `productized_worklist` | list page shell guarded state | Missing queue shows guarded state. |
| `procurement-console-worklist/supplier_directory` | Procurement adapter | `productized_worklist` | list page shell | Supplier directory. |
| `procurement-console-worklist/buying_item_directory` | Procurement adapter | `productized_worklist` | list page shell | Buying Items directory. |
| `procurement-console-worklist/purchase_request_directory` | Procurement adapter | `productized_worklist` | list page shell | Purchase Material Request directory. |
| `procurement-console-worklist/requests_to_source` | Procurement adapter | `productized_worklist` | list page shell | Requests requiring sourcing. |
| `procurement-console-worklist/purchase_order_directory` | Procurement adapter | `productized_worklist` | list page shell | Purchase Order directory. |
| `procurement-console-worklist/purchase_orders_pending_approval` | Procurement adapter | `productized_worklist` | list page shell | Approval visibility only. |
| `procurement-console-worklist/purchase_orders_open` | Procurement adapter | `productized_worklist` | list page shell | Open purchase orders. |
| `procurement-console-worklist/purchase_orders_late_or_unreceived` | Procurement adapter | `productized_worklist` | list page shell | Backward-compatible overdue alias. |
| `procurement-console-worklist/purchase_orders_due_soon` | Procurement adapter | `productized_worklist` | list page shell | Due-soon PO follow-up. |
| `procurement-console-worklist/purchase_orders_overdue` | Procurement adapter | `productized_worklist` | list page shell | Overdue PO follow-up. |
| `procurement-console-worklist/purchase_orders_partially_received` | Procurement adapter | `productized_worklist` | list page shell | Partial receipt visibility. |
| `procurement-console-worklist/purchase_orders_not_billed_visibility` | Procurement adapter | `productized_worklist` | list page shell | Billing visibility only. |
| `procurement-console-worklist/purchase_orders_supplier_follow_up` | Procurement adapter | `productized_worklist` | list page shell | Supplier follow-up queue. |
| `procurement-console-worklist/rfq_directory` | Procurement adapter | `productized_worklist` | list page shell | RFQ directory. |
| `procurement-console-worklist/rfqs_awaiting_supplier_response` | Procurement adapter | `productized_worklist` | list page shell | RFQs waiting response. |
| `procurement-console-worklist/rfqs_partially_quoted` | Procurement adapter | `productized_worklist` | list page shell | RFQs with partial quotation status. |
| `procurement-console-worklist/supplier_quotation_directory` | Procurement adapter | `productized_worklist` | list page shell | Supplier Quotation directory. |
| `procurement-console-worklist/supplier_quotations_to_compare` | Procurement adapter | `productized_worklist` | list page shell | Supplier quotations ready for comparison. |
| `procurement-console-worklist/supplier_quotations_expiring` | Procurement adapter | `productized_worklist` | list page shell | Expiring supplier quotations. |
| `procurement-console-report` bare route | Procurement adapter | `productized_report` | report page shell guarded state | Missing report key shows guarded state. |
| `procurement-console-report/supplier_quotation_comparison` | Procurement adapter | `productized_report` | report page shell | Read-only wrapper around native Supplier Quotation Comparison report. |
| `procurement-console-po-follow-up/<purchase-order>` | Procurement adapter | `productized_detail` | compact child/detail shell | Read-only PO follow-up detail. |
| `procurement-console-supplier/<supplier>` | Procurement adapter | `productized_detail` | compact child/detail shell | Read-only supplier profile. |
| `procurement-console-item/<item>` | Procurement adapter | `productized_detail` | compact child/detail shell | Read-only buying item profile. |
| `procurement-console-purchase-request-review/<material-request>` | Procurement adapter | `productized_detail` | compact review shell | Read-only buyer review. |
| `procurement-console-rfq-review/<rfq>` | Procurement adapter | `productized_detail` | compact review shell | Read-only buyer review. |
| `procurement-console-supplier-quotation-review/<supplier-quotation>` | Procurement adapter | `productized_detail` | compact review shell | Read-only buyer review. |
| Native new `Material Request` form with Purchase defaults | Procurement adapter + ERPNext | `governed_native_exception` | ERPNext native form with Procurement chrome | Approved Phase 3 Start Buying Work exception. |
| Native new `Request for Quotation` form | Procurement adapter + ERPNext | `governed_native_exception` | ERPNext native form with Procurement chrome | Approved Phase 3 Start Buying Work exception. |
| Native new `Supplier Quotation` form | Procurement adapter + ERPNext | `governed_native_exception` | ERPNext native form with Procurement chrome | Approved Phase 3 Start Buying Work exception. |
| Native new `Purchase Order` form | Procurement adapter + ERPNext | `governed_native_exception` | ERPNext native form with Procurement chrome | Approved Phase 3 Start Buying Work exception. |
| Secondary native `Material Request`, `Request for Quotation`, `Supplier Quotation`, `Supplier`, and `Item` edit/open forms | Procurement adapter + ERPNext | `governed_native_exception` | ERPNext native form with Procurement chrome | Allowed only as governed secondary actions with permission checks. |

## Procurement Action Inventory

| Action or pattern | Source | Classification | Target | Notes |
| --- | --- | --- | --- | --- |
| `refresh` | Worklists/reports/details/reviews | `productized_secondary_action` | current productized shell | Must refresh in place where shell supports it. |
| `reset_filters` | Worklists/reports | `productized_secondary_action` | current productized shell | Must clear visible controls and data. |
| `apply_filters` | Worklists/reports | `productized_primary_action` | current productized shell | Must apply via AJAX/in-place reload. |
| Overview/sidebar card navigation | Overview/sidebar | `productized_navigation` | Procurement productized routes | Must not route to Sales worklists or raw Buying module pages. |
| `open_record` row pattern for directories and queues | Procurement worklists | `productized_navigation` | productized detail/review routes | Purchase Request, RFQ, and Supplier Quotation rows use review routes, not raw forms. |
| `back_to_worklist` | Procurement review pages | `productized_navigation` | source worklist | Productized navigation. |
| `back_to_queue` | PO follow-up detail | `productized_navigation` | source worklist | Productized navigation. |
| `back_to_suppliers` | Supplier detail | `productized_navigation` | supplier directory | Productized navigation. |
| `back_to_items` | Item detail | `productized_navigation` | buying item directory | Productized navigation. |
| `open_quote_comparison` | Supplier Quotation review | `productized_navigation` | `procurement-console-report/supplier_quotation_comparison` | Productized report route. |
| `new_purchase_request` | Start Buying Work | `governed_native_action` | native new `Material Request` form | Approved Phase 3 native create-form exception. |
| `new_rfq` | Start Buying Work | `governed_native_action` | native new `Request for Quotation` form | Approved Phase 3 native create-form exception. |
| `new_supplier_quotation` | Start Buying Work | `governed_native_action` | native new `Supplier Quotation` form | Approved Phase 3 native create-form exception. |
| `new_purchase_order` | Start Buying Work | `governed_native_action` | native new `Purchase Order` form | Approved Phase 3 native create-form exception. |
| `open_erp_form` | PR/RFQ/SQ review pages | `governed_native_action` | native existing document form | Secondary action only, never primary row action. |
| `open_supplier_form` | Supplier detail | `governed_native_action` | native existing Supplier form | Secondary manager/write-permission action only. Supplier create remains deferred. |
| `open_item_form` | Item detail | `governed_native_action` | native existing Item form | Secondary governance action only. Item create/edit remains deferred outside this route. |
| Native form workflow controls inside approved create/edit exceptions | ERPNext native forms | `governed_native_action` | ERPNext form lifecycle | `Get Items From`, `Tools`, `Save`, grid controls, and conversion helpers are legitimate inside the exception. |

## Current Not-Allowed Leakage Classification

No current Sales or Procurement route/action is intentionally classified as `not_allowed_leakage` in this inventory. Any future entry with that classification must include a repair owner and status in the machine-readable manifest before tests may pass.

## Forbidden Mutation Labels For Productized Pages

The following labels are forbidden on productized read-only/detail/worklist/report pages unless a future managed mutation page explicitly approves them in the manifest:

`Submit`, `Cancel`, `Amend`, `Close`, `Unclose`, `Approve`, `Reject`, `Receive`, `Bill`, `Pay`, `Set Default Supplier`, `Update Item Price`, `Delete`.

These controls may still appear inside approved native ERPNext create/edit exceptions when ERPNext permissions and workflow own the transaction lifecycle.
