# Warehouse Console Phase W10C Page Chrome Fix

Date: 2026-05-31

Branch: `feature/erpnext-ui-design`

Runtime fix commit: `23dc8d42fe8bdef31eec2008efa20666abba9b8a`

Status: protected runtime chrome fix after owner manual feedback. This phase did not add Warehouse product routes, backend methods, stock execution, lifecycle actions, native ERP escape, valuation/accounting/commercial exposure, Quick Find/Search, Sales runtime behavior, or Procurement runtime behavior.

## 1. Owner Feedback

Owner observed that the top-left default page icon/chrome repeated while navigating through Warehouse pages. Owner also noted that the Warehouse UI works functionally but still feels basic compared with the shared premium UI standard.

Decision:

- The repeated icon/page-head behavior was a bug, not deferred scope.
- The broader premium visual polish question remains a separate follow-up task, not part of this narrow fix.

## 2. Fix

Runtime file changed:

- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`

Smoke file changed:

- `ui_smoke/warehouse_phase_w8c_transfer_visibility_smoke.js`

Implementation:

- Added Warehouse-owned route detection for all accepted Warehouse routes.
- Replaced the overview-only page-head cleanup with generic Warehouse route page-head cleanup.
- Centralized route host replacement so all worklist and detail renders remove default Frappe `.page-head` chrome after custom Warehouse render.
- Added W8C smoke assertion that visible `.page-head` count must remain zero.

This keeps the custom Warehouse shell as the only visible app-owned page chrome.

## 3. Validation

Source validation passed:

- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w8c_transfer_visibility_smoke.js`
- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- Result: `257 tests`, `OK`
- `git diff --check HEAD`

Focused source smoke passed:

- `/tmp/warehouse-w10c-page-head-source-20260530T185033Z/warehouse-w8c-transfer-visibility-20260530T185037Z/warehouse-w8c-transfer-visibility-summary.json`

Source protected gate passed:

- `/tmp/warehouse-w10c-page-head-protected-source-20260530T185116Z/protected-workspace-gate-summary.json`

## 4. Live Alignment

Live-aligned runtime file:

- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`

Source/live hash proof:

- `/tmp/warehouse-w10c-page-head-live-hashes-20260530T190543Z.txt`

Hash:

- `c8ad80238394a48449b8f0466dc7c579c83ac11a296c9cc9b6b2449189acda54`

Live actions:

- cleared Frappe cache for `erpai_prj1`;
- cleared website cache for `erpai_prj1`;
- restarted `backend`, `queue-short`, `queue-long`, `scheduler`, and `frontend`;
- verified backend healthy and `https://meet.erpbosai.com/api/method/ping` returned `pong`.

Focused live smoke passed:

- `/tmp/warehouse-w10c-page-head-live-20260530T190622Z/warehouse-w8c-transfer-visibility-20260530T190626Z/warehouse-w8c-transfer-visibility-summary.json`

Final protected live gate passed:

- `/tmp/warehouse-w10c-page-head-protected-live-20260530T190659Z/protected-workspace-gate-summary.json`

## 5. Premium UI Standard Note

The current Warehouse surface is a protected read-only operations visibility foundation. It is not a final visual-polish endpoint.

What is accepted now:

- protected navigation and routing;
- read-only data posture;
- custom Warehouse shell ownership;
- no duplicate native/Frappe page chrome;
- no stock execution, valuation exposure, native escape, or Quick Find/Search.

What remains suitable for a separate owner-approved polish phase:

- stronger visual hierarchy across worklists;
- more premium card density and spacing;
- cockpit/worklist color and typography refinement;
- mobile/tablet row density review;
- screenshot-led owner walkthrough.

Recommended next task if the owner wants visual quality raised:

- W10D or W11A docs-first Warehouse premium polish plan, followed by a narrow implementation task only after owner approval.
