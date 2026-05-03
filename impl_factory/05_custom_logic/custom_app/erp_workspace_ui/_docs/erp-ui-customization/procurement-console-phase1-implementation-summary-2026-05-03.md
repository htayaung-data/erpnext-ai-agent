# Procurement Console Phase 1 Implementation Summary

Date: 2026-05-03

Branch: `feature/erpnext-ui-design`

Status: implemented in the clean UI design branch. Default routing for Purchase roles remains disabled.

## Scope

Phase 1 delivers the first usable buyer workbench:

- Procurement Overview
- Supplier Directory, read-only
- Purchase Request Directory
- Requests To Source queue
- Purchase Order Directory
- Purchase Orders Pending Approval queue, visibility only
- Open Purchase Orders queue
- Late Or Unreceived Purchase Orders queue

Reports remain unavailable in Phase 1.

RFQ, Supplier Quotation, Supplier Quotation comparison, Item Price mutation, Supplier create/edit, and Purchase Order approve/reject actions remain excluded.

## Backend Contract

Entrypoints:

- `erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap`
- `erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context`
- `erp_workspace_ui.procurement_console.service.search_procurement_console_workspace`
- `erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context`
- `erp_workspace_ui.procurement_console.report.get_procurement_console_report_context`

Phase 1 internal modules:

- `erp_workspace_ui.procurement_console.common`
- `erp_workspace_ui.procurement_console.suppliers`
- `erp_workspace_ui.procurement_console.requests`
- `erp_workspace_ui.procurement_console.purchase_orders`

## Queue Keys

- `supplier_directory`
- `purchase_request_directory`
- `requests_to_source`
- `purchase_order_directory`
- `purchase_orders_pending_approval`
- `purchase_orders_open`
- `purchase_orders_late_or_unreceived`

Unknown or later-phase queues return `unavailable`, not `error`.

## Permission Rules

Allowed workspace roles:

- `Purchase User`
- `Purchase Manager`
- `Purchase Master Manager`

Finance and Executive approver roles remain restricted unless they also hold one of the Purchase roles.

Guest access raises a permission error.

Each queue also checks native read permission for its DocType. Missing DocType read permission returns `restricted`.

## Business Rules

Material Request views always enforce:

- `material_request_type = Purchase`

Requests To Source additionally requires submitted requests that are not fully ordered.

Supplier Directory is read-only and exposes no create/edit actions.

Purchase Order queues expose visibility and open-record navigation only. They do not expose approve or reject workflow actions.

Late or unreceived Purchase Order visibility may show receipt and billing posture for buyer follow-up, but it does not take over Warehouse receiving or Finance billing ownership.

## Shared UI

Phase 1 reuses:

- Workspace registry
- Workspace console runtime
- Workspace sidebar
- Shared list shell
- Shared action target contract

The Overview uses the shared console runtime for modest workload KPIs, priority queues, and directory shortcuts.

All Phase 1 worklists use the shared list shell.

## Validation

Required validation for this phase:

- `python3 -m compileall erp_workspace_ui`
- `node --check` for touched runtime/page/smoke JavaScript files
- full `python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- Procurement browser smoke through `ui_smoke/run_playwright_docker.sh npm run test:procurement-phase1` when credentials and a deployed Procurement backend are available

The live site must serve the clean-branch Procurement backend module before browser smoke can pass.
