# Sales Console Frozen Protection Package v2

Date: 2026-05-09
Status: Frozen and protected
Freeze marker tag: `sales-console-freeze-v2`
Branch: `feature/erpnext-ui-design`
Runtime source baseline: `7cf37078aacc42ef73fc698b2b543265fb7f0d4b fix: center sales directory metric row`
Previous historical freeze tag: `sales-console-freeze-v1`
Owner acceptance: manual Premium UI check confirmed on 2026-05-09

## 1. Freeze Decision

Sales Console is accepted as the premium-grade frozen reference workspace for ERP Workspace UI after Shared Core recovery and the final layout closure pass.

This v2 freeze package supersedes the 2026-05-03 historical freeze note for current live/source state. The v1 tag remains a historical marker. Future workspace work must protect the v2 Sales Console baseline.

The accepted v2 scope includes:

1. Shared Core + Workspace Adapter v2 compliance.
2. Premium Sales overview, directory, worklist, detail, report, and managed native form presentation.
3. Centered three-card directory KPI layout for Customer and Item directories.
4. Uniform report and directory filter width contract.
5. Governed native Sales document form boundaries.
6. No raw ERPNext leakage from productized Sales pages except declared governed native exceptions.
7. Owner-confirmed manual visual acceptance.

## 2. Frozen Routes And Page Families

Frozen route families:

| Page family | Routes |
| --- | --- |
| Overview | `/desk/sales-console-home`, `/desk/sales-console` |
| Worklists and directories | `/desk/sales-console-worklist/<queue-key>` |
| Customer detail/editor | `/desk/sales-console-worklist/customer-detail/<customer>`, `/desk/sales-console-worklist/customer-editor`, `/desk/sales-console-worklist/customer-editor/<customer>` |
| Item detail | `/desk/sales-console-worklist/item-detail/<item>` |
| Reports | `/desk/sales-console-report/<report-key>` |
| Managed native document forms | `/desk/quotation/<name>`, `/desk/sales-order/<name>`, `/desk/delivery-note/<name>`, `/desk/sales-invoice/<name>`, and corresponding new document routes |

Frozen sidebar destinations:

1. Overview
2. Quotations
3. Sales Orders
4. Customers
5. Items

Frozen report family:

1. Sales Analytics
2. Sales Order Analysis
3. Trend Analysis
4. Lost Quotations
5. Collections Status
6. Item-wise Sales History

Compatibility report keys:

1. `quotation_trends` maps into Trend Analysis with Quotation selected.
2. `payment_terms_status_sales_order` maps into Collections Status.

## 3. Accepted Business Scope

The frozen business scope is Sales Console as currently implemented:

- quotation and sales order operating review
- customer and item directory/detail review
- customer create/edit through the productized Sales editor
- Sales report review family
- Sales Inquiry on the overview
- governed managed native Sales document forms for transaction truth

No new Sales business scope is introduced by this freeze package.

## 4. Shared Component Mapping

| Surface | Accepted shared component contract |
| --- | --- |
| Overview | workspace console shell and Sales overview adapter |
| Sidebar | shared workspace sidebar with frozen Sales route aliases |
| Directory headers | shared list summary card, title/description row, centered/managed KPI grid |
| Directory filters | shared list filter deck, governed standard/search/date/action widths |
| Worklists | shared list shell, shared row link affordance, AJAX Apply/Reset/Refresh |
| Details | shared detail/list child shell, compact toolbar, detail KPI pattern |
| Reports | shared report shell, governed report filter spacing, contained wide table overflow |
| Native Sales forms | governed native exception wrapper/chrome with ERPNext workflow tools preserved |
| State handling | ready, empty, restricted, unavailable, and error states remain distinct |

Future workspaces must start from Shared Core + Adapter. They must not copy Sales page files or weaken the Sales baseline.

## 5. Governed Native Exceptions

Accepted governed native Sales document forms:

- Quotation
- Sales Order
- Delivery Note
- Sales Invoice

Allowed native workflow tools remain available where ERPNext permissions allow:

- Save
- Cancel
- Submit and related ERPNext lifecycle tools on governed native forms
- Get Items From
- child table controls
- ERPNext document conversion helpers

These native tools are accepted only inside declared governed native document forms. Productized Sales overview, worklists, directories, reports, Customer Detail, and Item Detail must not expose unclassified raw ERPNext leakage or forbidden mutations.

## 6. Validation Evidence

Validation was run against current source and current live state after final live alignment.

### Source Gate

| Command | Result |
| --- | --- |
| `python3 -m compileall erp_workspace_ui` | Pass |
| `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'` | Pass, 123 tests |
| `node --check erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js` | Pass |
| `node --check erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js` | Pass |
| `git diff --check` | Pass |

### Sales Browser Gate

All browser checks used the existing Docker Playwright runner and environment-provided credentials.

| Smoke | Result | Artifact |
| --- | --- | --- |
| Sales route lifecycle | Pass | `/work/artifacts/sales-route-lifecycle-smoke` |
| Sales action cards | Pass | `/work/artifacts/sales-action-cards-smoke/sales-action-cards-report.json` |
| Sales worklists | Pass | `/work/artifacts/sales-worklist-shell-smoke/sales-worklist-shell-report.json` |
| Sales detail boundary | Pass | `/work/artifacts/sales-detail-boundary-smoke/sales-detail-boundary-report.json` |
| Sales report family | Pass | `/work/artifacts/sales-report-family-smoke/sales-report-family-report.json` |
| Sales native leakage | Pass | `/work/artifacts/sales-native-leakage-smoke/sales-native-leakage-report.json` |
| Sales visual stability | Pass | `/work/artifacts/sales-visual-stability-smoke/sales-visual-stability-report.json` |
| Sales Order Analysis, Sales Manager and Sales User | Pass | `/work/erpw-sales-order-analysis-smoke/sales-order-analysis-report.json` |

### Shared Regression Evidence

Procurement Phase 3 smoke passed for Purchase Manager and Purchase User after the final Sales shared-layout fix. Procurement was not repaired in this Sales freeze package.

## 7. Accepted Owner Review

Owner manual check confirmed:

- Sales Console UI is accepted as Premium UI.
- Sales report filter widths are accepted.
- Item-wise Sales History standard/date and search/link filter sizing is accepted.
- Customer Directory and Item Directory three-card header KPI layout is accepted after centering fix.
- Current Sales Console is ready for freeze.

## 8. Known Risks And Deferred Work

No Sales Console freeze blocker remains.

Accepted boundaries:

1. Procurement remains a separate active workspace phase and is not frozen by this package.
2. Procurement implementation/repair belongs to the future Procurement phase unless a future shared-core change directly breaks a frozen Sales protection gate.
3. Sales native document forms intentionally preserve ERPNext transaction tools under governed native exception policy.
4. The historical `sales-console-freeze-v1` tag remains historical and must not be treated as the current protected baseline.

## 9. Future Protection Gate

Any future commit that touches shared CSS, list shell, report shell, app boot, sidebar runtime, route lifecycle, child/detail runtime, workspace registry, manifest, native exception policy, shared contracts, Sales adapter files, or Sales managed form assets must run the Sales frozen protection gate.

Minimum gate:

```bash
python3 -m compileall erp_workspace_ui
PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
node --check <touched-js-files>
git diff --check
cd ui_smoke
./run_playwright_docker.sh npm run test:sales-route-lifecycle
./run_playwright_docker.sh npm run test:sales-actions
./run_playwright_docker.sh npm run test:sales-worklists
./run_playwright_docker.sh npm run test:sales-detail-boundary
./run_playwright_docker.sh npm run test:sales-reports
./run_playwright_docker.sh npm run test:sales-native-leakage
./run_playwright_docker.sh npm run test:sales-visual-stability
./run_playwright_docker.sh npm run test:sales-order-analysis
```

If a future change touches shared core used by Procurement, run Procurement regression as separate evidence. Do not repair Procurement inside a Sales-only phase unless the owner explicitly approves that scope.

## 10. Freeze Control

The tag `sales-console-freeze-v2` marks the current protected Sales Console baseline.

After this tag:

1. No runtime Sales change may be made silently.
2. No shared-core change may proceed if it breaks the Sales frozen protection gate.
3. Any Sales change requires a controlled recovery/enhancement phase, before/after evidence, validation, and owner acceptance if user-visible.
4. Future workspace work must read this package before implementation.
