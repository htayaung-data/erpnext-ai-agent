# Warehouse Console Phase W10A Read-Only Hardening Baseline

Date: 2026-05-31

Branch: `feature/erpnext-ui-design`

Runtime hardening commit: `fa73deb5dddad0dc356876a320a6adba1a6b7acb`

Status: protected W10A hardening baseline. This phase did not add Warehouse product routes, backend methods, stock execution, lifecycle actions, native ERP escape, valuation/accounting/commercial exposure, Quick Find/Search, Sales runtime behavior, or Procurement runtime behavior.

## 1. Purpose

W10 paused net-new Warehouse feature implementation and requested a multi-agent protected-surface audit before the next Warehouse build phase. W10A closed the only required hardening patch from that audit.

The protected objective was narrow:

- keep parent document reads permission-aware;
- remove visible `Search ...` placeholder copy from Warehouse bounded filters;
- strengthen W4-W6 smoke assertions around `Search` / `Quick Find`;
- preserve all accepted W3-W8C read-only Warehouse behavior;
- prove source and live with focused Warehouse smokes plus Sales/Procurement protected gates.

## 2. Agent Sequence

Warehouse Agent reviewed the current Warehouse surface and did not patch source. The review confirmed that W3-W8C covers a coherent read-only operational visibility loop, but flagged `_safe_get_list` fallback behavior for Security/Stability review.

Security and Stability Review Agent patched the shared Warehouse helper and visible filter copy:

- `_safe_get_list` now returns `[]` on exception instead of falling back to `frappe.get_all`.
- Inbound/outbound filter placeholders now use `Filter order`, `Filter supplier`, `Filter customer`, and `Filter warehouse`.
- W4-W6 smokes now reject visible `Quick Find` / `Search` copy in the Warehouse shell.

Hardening Agent accepted the patch without further source changes.

Operation Reviewer Agent accepted the patch for freeze without further source changes.

Main Control ran credentialed source smokes, source protected gates, committed and pushed the hardening, live-aligned the runtime service file only, restarted live services, ran live Warehouse smokes, and completed the final protected live gate.

## 3. Runtime Changes

Changed runtime file:

- `erp_workspace_ui/warehouse_console/service.py`

Runtime behavior:

- Parent document reads stay permission-aware through `frappe.get_list`.
- On helper-level query exceptions, `_safe_get_list` returns an empty list after clearing transient Frappe messages.
- The helper no longer retries parent document reads through permission-bypassing `frappe.get_all`.
- Queue and detail surfaces continue to render controlled empty/unavailable states when no rows are visible.
- Inbound and outbound bounded filter controls say `Filter ...`, not `Search ...`.

No live smoke/test file was synced to production. Only `service.py` was live-aligned.

## 4. Smoke And Test Changes

Changed source smoke files:

- `ui_smoke/warehouse_phase_w4a_inbound_smoke.js`
- `ui_smoke/warehouse_phase_w4b_receiving_smoke.js`
- `ui_smoke/warehouse_phase_w5a_outbound_smoke.js`
- `ui_smoke/warehouse_phase_w5b_picking_review_smoke.js`
- `ui_smoke/warehouse_phase_w6a_stock_exceptions_smoke.js`
- `ui_smoke/warehouse_phase_w6b_stock_exception_review_smoke.js`

Smoke hardening:

- W4-W6 visible-copy assertions now include `Quick Find` and standalone `Search`.
- W4/W5 source fixtures use `Filter ...` placeholder copy.
- W5A detail button counting now accepts the live outbound picking drilldown selector: `[data-warehouse-row-open-picking-detail]`.

The W5A selector correction was source-smoke-only. It aligned the smoke to the accepted W5A outbound UI and did not change runtime behavior.

## 5. Source Validation

Source validation passed before commit:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- Result: `257 tests`, `OK`
- `node --check` for touched W4-W6 Warehouse smoke files
- `node --check ui_smoke/warehouse_phase_w8c_transfer_visibility_smoke.js`
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`

Source Warehouse smokes passed:

- W4A inbound: `/tmp/warehouse-w10a-hardening-source-smokes-20260530T173315Z/warehouse-w4a-inbound-20260530T173318Z/warehouse-w4a-inbound-summary.json`
- W4B receiving: `/tmp/warehouse-w10a-hardening-source-smokes-20260530T173315Z/warehouse-w4b-receiving-20260530T173338Z/warehouse-w4b-receiving-summary.json`
- W5A outbound: `/tmp/warehouse-w10a-hardening-source-smokes-rerun-20260530T173829Z/warehouse-w5a-outbound-20260530T173832Z/warehouse-w5a-outbound-summary.json`
- W5B picking review: `/tmp/warehouse-w10a-hardening-source-smokes-rerun-20260530T173829Z/warehouse-w5b-picking-20260530T173851Z/warehouse-w5b-picking-review-summary.json`
- W6A stock exceptions: `/tmp/warehouse-w10a-hardening-source-smokes-rerun-20260530T173829Z/warehouse-w6a-stock-exceptions-20260530T173911Z/warehouse-w6a-stock-exceptions-summary.json`
- W6B stock exception review: `/tmp/warehouse-w10a-hardening-source-smokes-rerun-20260530T173829Z/warehouse-w6b-stock-exception-review-20260530T173929Z/warehouse-w6b-stock-exception-review-summary.json`
- W7A stock posture: `/tmp/warehouse-w10a-hardening-later-source-smokes-20260530T174524Z/warehouse-w7a-stock-posture-20260530T174527Z/warehouse-w7a-stock-posture-summary.json`
- W8A movement visibility: `/tmp/warehouse-w10a-hardening-later-source-smokes-20260530T174524Z/warehouse-w8a-movement-visibility-20260530T174547Z/warehouse-w8a-movement-visibility-summary.json`
- W8B movement review: `/tmp/warehouse-w10a-hardening-later-source-smokes-20260530T174524Z/warehouse-w8b-movement-review-20260530T174604Z/warehouse-w8b-movement-review-summary.json`
- W8C transfer visibility: `/tmp/warehouse-w10a-hardening-later-source-smokes-20260530T174524Z/warehouse-w8c-transfer-visibility-20260530T174624Z/warehouse-w8c-transfer-visibility-summary.json`

The first W5A source smoke exposed a smoke selector mismatch and was not accepted as evidence. The selector was corrected, validation was rerun, and W5A passed in the rerun artifact listed above.

Source Sales freeze passed:

- `/tmp/sales-freeze-protection-20260530T174656Z/sales-freeze-protection-summary.json`

Source protected gate passed:

- `/tmp/warehouse-w10a-hardening-protected-source-rerun-20260530T175343Z/protected-workspace-gate-summary.json`

An earlier protected source attempt hit a transient Sales worklist timeout. The focused Sales worklist Docker smoke passed immediately afterward, and the full protected source rerun passed.

## 6. Live Alignment

Runtime file live-aligned:

- `erp_workspace_ui/warehouse_console/service.py`

Source/live hash proof:

- `/tmp/warehouse-w10a-hardening-live-hashes-20260530T181119Z.txt`

Hash:

- `4098c178ed495f176c52f9348eae684f39b1a3c4a1620bf0a62cf65046a8ff06`

Live actions:

- cleared Frappe cache for `erpai_prj1`;
- cleared website cache for `erpai_prj1`;
- restarted `backend`, `queue-short`, `queue-long`, `scheduler`, and `frontend`;
- verified `https://meet.erpbosai.com/api/method/ping` returned `pong`;
- verified backend container returned healthy.

## 7. Live Validation

Live Warehouse smokes passed without source asset overrides:

- W4A inbound: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w4a-inbound-20260530T181322Z/warehouse-w4a-inbound-summary.json`
- W4B receiving: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w4b-receiving-20260530T181344Z/warehouse-w4b-receiving-summary.json`
- W5A outbound: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w5a-outbound-20260530T181402Z/warehouse-w5a-outbound-summary.json`
- W5B picking review: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w5b-picking-20260530T181420Z/warehouse-w5b-picking-review-summary.json`
- W6A stock exceptions: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w6a-stock-exceptions-20260530T181436Z/warehouse-w6a-stock-exceptions-summary.json`
- W6B stock exception review: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w6b-stock-exception-review-20260530T181452Z/warehouse-w6b-stock-exception-review-summary.json`
- W7A stock posture: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w7a-stock-posture-20260530T181512Z/warehouse-w7a-stock-posture-summary.json`
- W8A movement visibility: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w8a-movement-visibility-20260530T181529Z/warehouse-w8a-movement-visibility-summary.json`
- W8B movement review: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w8b-movement-review-20260530T181546Z/warehouse-w8b-movement-review-summary.json`
- W8C transfer visibility: `/tmp/warehouse-w10a-hardening-live-smokes-20260530T181318Z/warehouse-w8c-transfer-visibility-20260530T181606Z/warehouse-w8c-transfer-visibility-summary.json`

Final protected live gate passed:

- `/tmp/warehouse-w10a-hardening-protected-live-20260530T181654Z/protected-workspace-gate-summary.json`

The SSH connection reset during the Procurement phase of the final protected live gate, but the process continued on the server and produced the final passing summary above. Main Control monitored the original run and did not start a duplicate gate.

## 8. Protected Boundaries Confirmed

W10A confirms:

- no Warehouse stock mutation;
- no receiving/posting/picking/transfer execution;
- no Pick List, Delivery Note, Purchase Receipt, Stock Entry, reservation, reconciliation, or transfer creation;
- no lifecycle controls such as submit, cancel, amend, reconcile, reserve, unreserve, post, receive, ship, or dispatch;
- no native ERP Form/List/Report escape in active Warehouse routes;
- no Stock Ledger or Stock Balance exposure;
- no valuation/accounting/commercial field exposure;
- no Quick Find/Search behavior in Warehouse;
- no Sales runtime change;
- no Procurement runtime change;
- no smoke/test files synced to live.

## 9. Residual Notes

`_safe_get_all` remains in use for bounded child/detail tables and `Bin` posture behind role/read gates and row caps. Security/Stability and Hardening accepted that residual posture for this freeze.

`_safe_count` still uses count-oriented database access for KPI counts. It exposes counts only, not row detail. If warehouse/company-specific document restrictions become stricter later, KPI count permission behavior should be revisited.

The next Warehouse phase should not add execution capability by default. Any receiving, picking, transfer, reservation, reconciliation, or posting work should be treated as a separately governed execution design track, not a continuation of the read-only visibility stream.

## 10. Next Recommendation

The read-only Warehouse visibility foundation is now suitable for a W10B freeze decision or owner visual walkthrough before any new Warehouse feature work.

Recommended next step:

- W10B docs-only freeze closure or final owner visual walkthrough checklist.

Do not assign another Warehouse implementation phase until the owner explicitly chooses one of:

- cockpit/mobile polish only;
- a narrow read-only visibility addition with clear business value;
- a separately governed execution design track.
