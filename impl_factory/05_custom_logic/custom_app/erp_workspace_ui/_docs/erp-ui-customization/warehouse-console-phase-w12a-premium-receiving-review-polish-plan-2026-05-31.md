# Warehouse Console Phase W12A Premium Receiving Review Polish Plan

Date: 2026-05-31

Status: docs-only owner/Main Control decision.

This plan chooses the next Warehouse direction after W11B. It does not implement runtime code, routes, backend methods, tests, smokes, live alignment, Purchase Receipt creation, Purchase Receipt submission, stock posting, native ERP access, valuation/accounting exposure, Warehouse Quick Find/Search, Sales runtime behavior, or Procurement runtime behavior.

## Decision

Proceed next with read-only premium Receiving Review UI polish.

Execution remains deferred. Purchase Receipt draft creation is a mutation and is not approved for implementation. Purchase Receipt submission is a separate higher-risk milestone and remains blocked.

Reasoning:

- The current read-only Warehouse surface is functionally broad enough for visibility, but several screens still look basic compared with the accepted Sales and Procurement standard.
- W11B confirms Purchase Receipt receiving is the right first execution-design candidate, but Security/Stability and Operation Reviewer both require stronger owner confidence before any write surface exists.
- Premium Receiving Review polish reduces future execution risk because the owner, Warehouse Manager, and Warehouse User must understand the receiving mental model before draft creation or submit behavior is considered.

## Phase Goal

W12A should make `/desk/warehouse-console-receiving/<purchase-order>` feel like a serious premium operational review screen while remaining read-only.

The polished page should help a warehouse manager answer:

- What is expected to arrive?
- What is ready to receive later?
- What still needs review before any receiving action?
- Which lines are blocked by quality, serial/batch, rejected warehouse, warehouse mismatch, or missing posture?
- What has already been received?
- What is the safe next operational understanding, without implying execution?

## Allowed Runtime Direction For Later W12A Implementation

If Main Control assigns implementation after this plan, the implementation may touch only Warehouse read-only UI surfaces needed for receiving review polish.

Allowed:

- Read-only layout, hierarchy, typography, grouping, copy, responsive behavior, and visual polish.
- Custom Warehouse route `/desk/warehouse-console-receiving/<purchase-order>`.
- Existing read-only receiving payloads, if no write behavior and no valuation/commercial fields are introduced.
- Focused smoke screenshot/evidence hardening for Receiving Review.
- Idempotency and stale-shell rendering fixes if needed to keep the custom route stable.

Not allowed:

- Purchase Receipt creation.
- Purchase Receipt submission.
- Any disabled or hidden execution buttons.
- Native Purchase Receipt form/list/report links.
- Stock Ledger or Stock Balance exposure.
- Valuation, accounting, GL, tax, margin, profit, rate, amount, price, cost, landed cost, billing, payment, or commercial fields.
- Quick Find/Search.
- Sales runtime changes.
- Procurement runtime changes.

## Premium UI Requirements

W12A should raise the page to the shared premium UI standard:

- A strong command header with PO identity, supplier, receiving status, target warehouse, and read-only posture.
- A clear receiving readiness band that separates ready lines, blocked lines, already received posture, and unavailable data.
- Item-line cards or a structured dense table that is readable on laptop and mobile.
- Visual distinction between open quantity, already received quantity, and exception reasons.
- A receipt history panel that explains prior receipts without native ERP escape.
- Back and Refresh actions only.
- Clear guardrail copy that says stock is not posted and no Purchase Receipt is created from this screen.
- No generic system-looking Frappe page chrome duplication.
- No visual language suggesting submit, receive, post, create, complete, approve, or reconcile.

## Evidence Requirements

Any later W12A implementation must include:

- Python compileall.
- Full unit discovery.
- Node syntax checks for touched Warehouse runtime and smoke files.
- JSON and shell validation if smoke/package files change.
- `git diff --check HEAD`.
- Static scans for native escape, write calls, lifecycle labels, valuation/accounting/commercial terms, Quick Find/Search, Sales dirty boundary, and Procurement dirty boundary.
- Focused credentialed source smoke for Receiving Review polish.
- Protected workspace source gate before commit.
- Main Control commit/push only after source validation.
- Live alignment only if runtime changed.
- Focused live smoke and final protected live gate after live alignment.

## Agent Sequence

1. Warehouse Agent: source-only W12A read-only Premium Receiving Review polish implementation.
2. Hardening Agent: source-only review for route idempotency, stale responses, responsive layout, and smoke coverage.
3. Security/Stability Review Agent: confirm no execution, native escape, valuation, Quick Find/Search, or protected workspace regression.
4. Operation Reviewer Agent: confirm the polished UI is business-readable and does not imply execution.
5. Main Control: credentialed smoke, protected gates, commit/push, live alignment, and post-live gates.

## Warehouse Agent W12A Prompt

Use this prompt for the next Warehouse Agent task.

```text
You are Warehouse Agent for ERP Workspace UI.

Task: Implement W12A source-only read-only Premium Receiving Review polish.

Repository:
/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui

Branch:
feature/erpnext-ui-design

Primary route:
/desk/warehouse-console-receiving/<purchase-order>

Context:
- W10B froze Warehouse read-only visibility.
- W10C fixed duplicated Frappe page chrome.
- W11B documented future Purchase Receipt receiving design, but runtime execution remains blocked.
- W12A is a read-only premium UI polish phase only.

Hard boundaries:
- Do not create, submit, cancel, amend, post, receive, complete, approve, reject, reserve, reconcile, transfer, print, email, portal, workflow, AI, or background-job behavior.
- Do not create Purchase Receipt, Stock Entry, Delivery Note, Pick List, Stock Reservation, Stock Reconciliation, Serial and Batch Bundle, Quality Inspection, barcode, or scan mutation behavior.
- Do not add disabled execution buttons.
- Do not add native ERP Form/List/Report links.
- Do not add Stock Ledger or Stock Balance exposure.
- Do not expose valuation, accounting, GL, tax, margin, profit, rate, amount, price, cost, landed cost, billing, payment, or commercial fields.
- Do not add Warehouse Quick Find/Search.
- Do not touch Sales runtime.
- Do not touch Procurement runtime.
- Do not commit, push, live-align, or run protected gates.

Implementation scope:
- Improve only read-only Warehouse receiving review UI and any necessary focused smoke/test documentation for that UI.
- Preserve current custom route name.
- Keep Back and Refresh only.
- Use premium visual hierarchy consistent with Sales/Procurement quality, but keep Warehouse's own visual identity.
- Make laptop and mobile layouts readable.
- Prevent Frappe page-head/icon duplication.
- Keep the route idempotent and stable on repeated navigation.

Required UI outcome:
- Strong command header with PO, supplier, warehouse, status, and read-only posture.
- Receiving readiness summary that separates ready, blocked, already received, and unavailable posture.
- Item lines are easier to scan than the current basic layout.
- Receipt history is clear and custom-only.
- Guardrail copy explicitly says no stock is posted and no Purchase Receipt is created here.
- Empty/unavailable/restricted states are polished and in-shell.

Required validation:
- python3 -m compileall erp_workspace_ui
- PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
- node --check for touched Warehouse runtime JS and any smoke JS.
- python3 -m json.tool ui_smoke/package.json if changed.
- bash -n ui_smoke/run_playwright_docker.sh if changed.
- git diff --check HEAD
- Static scans for native escape, write calls, lifecycle/action labels, valuation/accounting/commercial terms, Quick Find/Search, Sales dirty boundary, and Procurement dirty boundary.

Focused smoke:
- Add or update a focused W12A Receiving Review smoke if useful.
- If credentials are unavailable, stop before browser smoke and provide the exact credentialed command for Main Control.

Output:
- Summary of changed files.
- What changed.
- Validation results.
- Focused smoke status.
- Final git status.
- Confirm no execution, no stock mutation, no valuation/accounting exposure, no native escape, no Quick Find/Search, no Sales runtime change, and no Procurement runtime change.

Stop condition:
Stop after source changes and local validation. Do not commit, push, live-align, or run protected gates.
```

## Final Recommendation

Start W12A with Warehouse Agent using the prompt above. Keep execution deferred until after premium receiving UI polish, owner visual review, and a later explicit implementation approval.
