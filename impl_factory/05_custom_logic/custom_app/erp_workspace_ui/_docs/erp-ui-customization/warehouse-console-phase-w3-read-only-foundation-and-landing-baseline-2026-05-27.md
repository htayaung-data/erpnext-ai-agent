# Warehouse Console Phase W3 Read-Only Foundation And Landing Baseline

Date: 2026-05-27

Branch: `feature/erpnext-ui-design`

Status: protected Warehouse W3/W3A runtime baseline closure. This document is docs-only and does not change runtime, tests, smokes, or live files.

## 1. Baseline Commits

Runtime baseline commits:

- W3 read-only Warehouse Console foundation: `368dc645e1ce6a6c80849c3cb211c06ade790d7a`
- W3A Warehouse landing closure: `cca15a5fca07ad9bfc4e116101e08536880d8e62`

W3 established the smallest accepted Warehouse runtime foundation:

- Warehouse registry/sidebar visibility.
- Warehouse route ownership for `/desk/warehouse-console`.
- Read-only Warehouse Overview.
- Warehouse Manager and Warehouse User / Stock User role access.
- Quantity/posture-only overview data with no valuation fields.
- No Warehouse worklists, detail pages, reports, or Quick Find.
- No stock execution or lifecycle actions.

W3A closed the owner-reported native Desk landing gap:

- Warehouse Manager/User now land on Warehouse Console.
- Opening plain `/desk` or `/app` redirects operational Warehouse roles to `/desk/warehouse-console`.
- System Manager/Admin and broad cross-workspace roles keep broader Desk access and are not forced into Warehouse Console.
- Direct `/desk/warehouse-console` still works.
- Duplicate shell/header/sidebar rendering is protected after login landing, explicit `/desk`, refresh, direct route, and repeated `/desk`.

## 2. Accepted Artifacts

W3 accepted artifacts:

- W3 source smoke: `/tmp/warehouse-phase-w3-source-20260526T092825Z/warehouse-w3-20260526T100658Z/warehouse-w3-summary.json`
- W3 source protected gate: `/tmp/warehouse-phase-w3-protected-source-20260526T114903Z/protected-workspace-gate-summary.json`
- W3 live smoke: `/tmp/warehouse-phase-w3-live-20260526T162059Z/warehouse-w3-20260526T162105Z/warehouse-w3-summary.json`
- W3 post-live protected gate: `/tmp/warehouse-phase-w3-protected-live-20260526T162615Z/protected-workspace-gate-summary.json`

W3A accepted artifacts:

- W3A source landing smoke: `/tmp/warehouse-phase-w3a-source-20260527T140345Z/warehouse-w3a-landing-20260527T140351Z/warehouse-w3a-landing-summary.json`
- W3A source protected gate: `/tmp/warehouse-phase-w3a-protected-source-20260527T140713Z/protected-workspace-gate-summary.json`
- W3A live landing smoke: `/tmp/warehouse-phase-w3a-live-20260527T144409Z/warehouse-w3a-landing-20260527T144413Z/warehouse-w3a-landing-summary.json`
- W3A post-live protected gate: `/tmp/warehouse-phase-w3a-protected-live-20260527T145626Z/protected-workspace-gate-summary.json`

## 3. Protected Behavior

Warehouse W3/W3A accepted behavior:

- Warehouse Overview is available at `/desk/warehouse-console`.
- Warehouse Manager and Warehouse User / Stock User can open the Warehouse Overview.
- Warehouse operational users landing at `/desk` or `/app` are routed to `/desk/warehouse-console`.
- System Manager/Admin bypass policy remains protected; admin-style users are not globally redirected away from Desk.
- Cross-workspace roles that need broader Sales, Procurement, Accounts/Finance, HR, Manufacturing, Projects, Report, or Workspace access are not forced into Warehouse landing unless separately designed later.
- Warehouse Overview renders a single shell, single header, and single sidebar instance after login landing, refresh, direct route, and repeated Desk entry.
- Overview KPIs and compact read-only sections render without horizontal overflow at the accepted smoke widths.
- Warehouse Search / Quick Find is not active in W3/W3A.
- Sales Console protected behavior remains unchanged.
- Procurement Console protected behavior remains unchanged.

## 4. W3 Read-Only Scope

W3/W3A is read-only only.

Allowed W3/W3A behavior:

- Open Warehouse Overview.
- Refresh read-only Warehouse Overview data.
- View compact warehouse posture cards and exception-oriented sections.
- Navigate only within the productized Warehouse Overview route.

Explicitly excluded from W3/W3A:

- Warehouse worklists.
- Warehouse detail or object-profile pages.
- Warehouse reports.
- Warehouse Search / Quick Find.
- Receiving execution.
- Delivery, pick, pack, or dispatch execution.
- Internal transfer execution.
- Stock Entry creation or submission.
- Purchase Receipt creation or submission.
- Delivery Note creation or submission.
- Stock Reconciliation creation or submission.
- Reserve or unreserve stock.
- Serial or batch assignment.
- Quality approval or rejection.
- Submit, cancel, amend, close, approve, reject, post, or reconcile actions.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Contact, User, portal, email, or AI behavior.

## 5. Data And Security Boundaries

W3/W3A payload and visible UI protections:

- No `stock_value`.
- No `valuation_rate`.
- No stock value copy.
- No valuation rate copy.
- No native ERP form, report, or list escape from Warehouse Console.
- No raw ERPNext Desk workspace grid as the final landing state for Warehouse operational users.
- No enabled or disabled fake stock execution buttons.
- No product route targets outside the Warehouse Overview in W3/W3A.

Warehouse Overview data posture:

- W3 uses controlled read-only service behavior.
- Payloads expose overview state, role/access flags, overview copy, KPI cards, bounded read-only sections, and allowed navigation/read-only actions only.
- If a data source is unavailable, unavailable state must be business-safe and must not expose raw framework errors.
- Quantity and work posture are acceptable; valuation stays hidden.

## 6. Landing Policy

Warehouse operational landing rule:

- If the current path is exactly `/desk` or `/app`, and the user has an operational Warehouse/Stock role, and the user does not have System Manager or broader cross-workspace/admin-style roles, route to `warehouse-console`.

Operational Warehouse/Stock roles:

- `Warehouse Manager`
- `Warehouse User`
- `Stock Manager`
- `Stock User`

Bypass roles include:

- `System Manager`
- Sales roles
- Purchase roles
- Accounts/Finance roles
- HR roles
- Manufacturing roles
- Projects roles
- Report/Workspace management roles

The landing rule must not become a global Desk redirect. Future changes to this policy require protected smoke coverage for Warehouse, Sales, Procurement, and admin/native Desk behavior.

## 7. Protected Runtime Files

W3/W3A runtime files that are part of this baseline:

- `erp_workspace_ui/boot.py`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/workspace_governance_manifest.py`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.js`
- `erp_workspace_ui/erp_workspace_ui/page/warehouse_console/warehouse_console.json`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`

W3A changed only the landing/runtime idempotency layer from the W3 baseline:

- `erp_workspace_ui/boot.py`
- `erp_workspace_ui/public/js/erp_workspace_ui_boot.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`

This baseline document does not modify any of those files.

## 8. Regression Protection Expectations

Future Warehouse phases must preserve:

- W3/W3A Warehouse landing behavior.
- Single Warehouse shell/header/sidebar rendering.
- No native ERP route escape for normal Warehouse users.
- No stock mutation or lifecycle action until a separate controlled execution design is approved.
- No valuation exposure unless Finance/owner approval is documented and tested.
- Sales Console freeze protection.
- Procurement Console freeze protection.
- Protected workspace gate coverage.

Future Warehouse route additions must include focused smokes before live alignment. Any shared boot, registry, sidebar, or runtime change must run Sales freeze, Procurement protected coverage, and the full protected workspace gate.

## 9. Recommended Next Phase

Recommended next phase: Warehouse W4 design/implementation readiness for inbound receiving visibility, not receiving execution.

W4 should remain read-only unless a separate controlled execution design is approved. The expected next scope is:

- Inbound receiving queue visibility.
- Receiving Review object page, read-only.
- Purchase Order and Purchase Receipt posture without creation/submission.
- Quality hold visibility only if owner-approved for the inbound scope.
- No native form/report/list escape.
- No stock ledger posting.

Owner decisions before W4:

- Confirm W4 should start with inbound receiving visibility.
- Confirm whether Quality Hold belongs in W4 or later.
- Confirm visible inbound fields and role access.
- Confirm whether Purchase Manager gets read-only Warehouse inbound pages.
- Confirm W4 smoke/gate requirements before implementation starts.

## 10. Docs-Only Closure

This W3/W3A closure is documentation only.

It does not:

- Change runtime code.
- Change tests.
- Change smoke scripts.
- Change live files.
- Run live alignment.
- Touch `ui_smoke/sales_final_acceptance_audit.js`.

Required docs-only validation:

- `git diff --check HEAD`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
