# Warehouse Console Phase W10B Read-Only Freeze Closure

Date: 2026-05-31

Branch: `feature/erpnext-ui-design`

Status: docs-only freeze closure. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

Accepted runtime baseline:

- W8C Transfer Visibility runtime: `97cf78485ba5c1cf371dcce8348bab222755df37`
- W10A read-only hardening runtime: `fa73deb5dddad0dc356876a320a6adba1a6b7acb`
- W10A hardening docs: `e7eaa539c998fe5c6d372fb91d18d8ce1928cd62`

## 1. Decision

Warehouse Console read-only visibility is accepted as a protected freeze baseline for the current W3-W10A scope.

Main Control can proceed without waiting for owner manual UI review because the W10A change was a narrow hardening patch and the credentialed source/live smoke evidence is complete. Owner manual review remains recommended as supplemental visual acceptance evidence before any new Warehouse implementation phase.

Freeze name:

- `warehouse-console-read-only-visibility-v1`

This freeze protects the accepted Warehouse visibility foundation. It does not authorize receiving, picking, transfer execution, reservation, reconciliation, stock posting, valuation exposure, native ERP access, or Quick Find/Search.

## 2. Protected Scope

Protected top-level route:

- `/desk/warehouse-console`

Protected worklist routes:

- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-worklist/outbound-picking`
- `/desk/warehouse-console-worklist/stock-exceptions`
- `/desk/warehouse-console-worklist/movement-visibility`
- `/desk/warehouse-console-worklist/transfer-visibility`

Protected detail/review routes:

- `/desk/warehouse-console-receiving/<purchase-order>`
- `/desk/warehouse-console-picking/<sales-order>`
- `/desk/warehouse-console-stock-exception/<encoded-context>`
- `/desk/warehouse-console-stock-posture/<encoded-context>`
- `/desk/warehouse-console-movement/<encoded-context>`

Protected user posture:

- Warehouse operational users land on the Warehouse Console.
- Warehouse Manager and Warehouse User/Stock User are covered by focused Warehouse smokes.
- The surface remains operationally read-only.

## 3. Freeze Evidence

W10A source validation passed:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- Result: `257 tests`, `OK`
- `node --check` for touched W4-W6 Warehouse smoke files
- `node --check ui_smoke/warehouse_phase_w8c_transfer_visibility_smoke.js`
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`

W10A source Warehouse smoke evidence:

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

W10A source protected evidence:

- Sales freeze: `/tmp/sales-freeze-protection-20260530T174656Z/sales-freeze-protection-summary.json`
- Protected workspace gate: `/tmp/warehouse-w10a-hardening-protected-source-rerun-20260530T175343Z/protected-workspace-gate-summary.json`

W10A live evidence:

- Source/live hash proof: `/tmp/warehouse-w10a-hardening-live-hashes-20260530T181119Z.txt`
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
- Final protected live gate: `/tmp/warehouse-w10a-hardening-protected-live-20260530T181654Z/protected-workspace-gate-summary.json`

## 4. Manual Review Posture

Owner manual UI review is recommended but not a blocker for this freeze closure.

Reason:

- W10B is docs-only.
- W10A changed only permission fallback behavior and visible filter placeholder wording.
- Live focused Warehouse smokes covered W4A through W8C.
- Final protected live gate passed after the live restart.

Recommended later manual walkthrough:

- Warehouse Cockpit;
- Inbound Receiving;
- Receiving Review;
- Outbound Picking;
- Picking Review;
- Stock Exceptions;
- Stock Exception Review;
- Stock Posture Review;
- Movement Visibility;
- Movement Review;
- Transfer Visibility.

Manual review should focus on layout, information hierarchy, label clarity, and whether `Filter ...` wording is acceptable. Any owner feedback should be handled as a new W10C/W9C polish task, not as a reopening of the W10A hardening patch.

## 5. Guardrails

The freeze preserves these guardrails:

- no stock mutation;
- no lifecycle action controls;
- no receiving, shipping, picking, transfer, reconciliation, reservation, posting, submit, cancel, or amend execution;
- no Pick List, Delivery Note, Purchase Receipt, Stock Entry, Stock Reconciliation, reservation, or transfer creation;
- no native ERP Form/List/Report escape in active Warehouse routes;
- no Stock Ledger or Stock Balance exposure;
- no valuation/accounting/commercial exposure;
- no Quick Find/Search behavior in Warehouse;
- no Sales runtime changes;
- no Procurement runtime changes.

## 6. Agent Responsibilities After Freeze

Main Control owns:

- freeze decisions;
- credentialed smokes and protected gates;
- commits, pushes, and live alignment;
- final source/live evidence recording.

Warehouse Agent owns:

- source-only Warehouse feature design/implementation when explicitly assigned;
- route and operational question coherence;
- no commits, pushes, or live alignment.

Hardening Agent owns:

- source-only route idempotency, stale-response protection, layout pressure, and smoke evidence hardening.

Security and Stability Review Agent owns:

- source-only read-only posture, role/read gates, native escape, valuation/commercial exposure, server write calls, and protected workspace boundary review.

Operation Reviewer Agent owns:

- source-only warehouse-user mental model, labels, empty states, and business usefulness review.

## 7. Next Decision

Do not start another Warehouse implementation by default.

Acceptable next options:

- owner manual visual walkthrough and W10C polish notes;
- docs-only W11 planning for the next read-only visibility tranche;
- separately governed execution design research, if the owner explicitly wants receiving/picking/transfer execution later.

Recommended immediate next task:

- Wait for owner manual review when convenient, or assign W10C cockpit/mobile polish only if the owner finds visual issues.
