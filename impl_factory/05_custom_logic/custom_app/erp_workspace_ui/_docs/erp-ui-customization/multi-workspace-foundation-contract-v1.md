# Multi-Workspace Foundation Contract v1

Date: 2026-05-03
Status: mandatory foundation for all future ERP workspace UI work
Reference freeze: Sales Console `sales-console-freeze-v1`

## 1. Purpose

This contract prevents the next workspaces from becoming copied Sales Console code with different labels.

Sales Console remains the frozen reference implementation. Future workspaces must reuse the shared runtime and operating rules, but each workspace must have its own registered identity, route ownership, backend methods, sidebar context, permission scope, and freeze evidence.

The foundation rule is:

`Register the workspace first, then build pages from shared shells.`

## 2. Matrix Source

The foundation is based on the workspace matrix workbook:

`impl_factory/08_erpnext_ui_design/references/raw_reference/legacy_custom_workspaces/Mingalar_ERP_Workspace_Configuration_Matrix.xlsx`

Relevant workbook sheets:

1. `Overview`
2. `Workspace Matrix`
3. `Navigation Rules`
4. `Form Priorities`
5. `Implementation Sequence`

The matrix is the base authority for project scope, role families, navigation direction, and delivery sequence. It is not blindly final naming law. If implementation review finds a better enterprise name, the matrix name and recommended name must both be recorded.

## 3. Workspace Roadmap

Current roadmap contract:

1. Sales Console: frozen reference workspace
2. Procurement Console: first-wave planned workspace
3. Warehouse Console: first-wave planned workspace
4. Finance Console: first-wave matrix name, recommended name under review as `Finance Control Desk`
5. Executive Console: second-wave matrix name, recommended name under review as `Management Daily Brief`
6. Customer Service Console: second-wave planned workspace
7. HR and Admin Console: second-wave planned workspace
8. ERP Admin Console: second-wave planned workspace

Do not rename `Warehouse Console` unless the owner explicitly approves a matrix-level naming change.

## 4. Active Registry Paths

Backend registry:

`erp_workspace_ui/workspace_registry.py`

Frontend registry:

`erp_workspace_ui/public/js/runtime/console/workspace_registry.js`

The registry currently exposes Sales Console as the only active workspace because it is the only frozen workspace.

The registry also records the future workspace roadmap so future agents and developers use the same foundation names.

## 5. Frozen Sales Console Mapping

Sales Console route names are frozen and must not be renamed during foundation work:

1. launcher route: `sales-console-home`
2. launcher path: `/desk/sales-console-home`
3. home route: `sales-console`
4. home path: `/desk/sales-console`
5. worklist route: `sales-console-worklist`
6. report route: `sales-console-report`

Sales Console backend methods are also frozen:

1. bootstrap: `erp_workspace_ui.sales_console.service.get_sales_console_bootstrap`
2. sidebar context: `erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context`
3. workspace search: `erp_workspace_ui.sales_console.service.search_sales_console_workspace`
4. worklist context: `erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context`
5. report context: `erp_workspace_ui.sales_console.report.get_sales_console_report_context`

Future workspace work may map to new route and method names. It must not rewrite the frozen Sales Console route names to make them look generic.

## 6. Registry Contract

Every active workspace definition must declare:

1. `workspace_id`
2. status
3. title
4. mode label
5. role family
6. route keys and route paths
7. backend method names
8. managed doctypes
9. directory queue mapping
10. sidebar identity
11. safe fallback navigation items

Every future workspace must be added to the registry before it is exposed in navigation, app boot, sidebar runtime, search, worklist shell, or report shell.

## 7. Runtime Contract

Shared runtime code must read workspace route and method identity from the registry when the value is workspace-owned.

Allowed hardcoded values:

1. frozen Sales Console fallback values for backward compatibility
2. shared CSS prefixes such as `erpw-`
3. data attributes that intentionally remain Sales Console-specific during the frozen reference phase
4. native ERPNext route names such as `Form`, `List`, or `query-report`
5. DocType names that are business truth

Not allowed:

1. copying Sales Console route names into future workspace code
2. using Sales Console method names for a different workspace without an explicit compatibility adapter
3. building page-local shells when a shared shell already exists
4. exposing a workspace route before permission and role scope are defined server-side

## 8. New Workspace Startup Sequence

Use this sequence for every future workspace:

1. confirm matrix scope and role family
2. decide matrix name versus recommended enterprise name
3. define route ownership and route keys
4. define backend method contract
5. define sidebar destinations and active-key mapping
6. map each page to a shared archetype
7. add registry definition and contract tests
8. implement backend payloads with permission-safe scope
9. implement frontend only through shared shells
10. run syntax, unit, role, browser, and route ownership verification
11. update docs and freeze notes before acceptance

## 9. Parallel Workspace Rule

Multiple workspaces can be built at the same time only when their ownership boundaries are separate.

Safe parallel split:

1. Procurement Console: supplier, purchase, request/order/receipt flow
2. Warehouse Console: stock, transfer, receiving, delivery readiness, warehouse operation

Do not build Finance in parallel with Procurement until purchase/invoice/accounting boundary ownership is written down. Finance touches accounting truth and can easily conflict with purchasing or receivables logic.

## 10. Freeze Rule

Each workspace must have its own freeze note.

A workspace is not frozen until:

1. registry definition is correct
2. shared shell usage is confirmed
3. role and permission checks pass
4. route ownership is stable
5. browser checks pass for refresh, back, filters, and restricted access
6. docs match the final code
7. deferred work is explicitly listed

The Sales Console freeze tag remains a historical marker. Future workspace freezes must receive their own freeze notes and, when appropriate, their own tags.
