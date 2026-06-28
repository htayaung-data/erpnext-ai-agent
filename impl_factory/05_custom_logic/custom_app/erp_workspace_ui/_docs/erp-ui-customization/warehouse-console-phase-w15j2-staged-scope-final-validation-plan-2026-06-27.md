# Warehouse Console Phase W15J2 Staged Scope / Final Validation Plan

Decision: `implementation_ready_for_review`

Date: 2026-06-27

Scope: docs-only staged-scope and final-validation plan after W15J1. W15J2 defines the exact Warehouse milestone files intended for a later staging review, the files that must remain excluded, and the final validation gates required before a future commit/push decision. W15J2 does not stage files, commit, push, run live alignment, restart, run protected gates, activate workflows, create ERPNext documents, mutate stock/accounting data, expose native routes, send notifications, or close release.

## Purpose

W15J1 defined the release-readiness checklist and required an exact staged-file review before any commit/push decision.

W15J2 provides that staged-scope plan. It does not perform staging. It defines what a later staging phase may include if owner and review agents approve.

W15J2 answers:

- which Warehouse files belong to the milestone candidate;
- which dirty files must remain excluded;
- which validations must pass before staging;
- which checks must pass after staging;
- which approvals are required before any commit/push.

## Current Worktree Basis

The current worktree contains:

- accepted W15I3/W15I4/W15I5 source, metadata, test, and UI wording changes;
- accepted W15I/W15I1/W15I2/W15I5/W15I6/W15J1 documentation;
- this W15J2 staged-scope plan;
- unrelated `ai_assistant_ui` dirty files;
- unrelated `ui_smoke/sales_final_acceptance_audit.js`.

The accepted Warehouse work is intentionally layered in one dirty worktree. That is not itself a rejection reason, but it makes file-by-file staging mandatory.

## Intended Warehouse Milestone Include List

The later staged milestone should include exactly these Warehouse files, if final validation and reviews pass.

### Documentation

- `_docs/erp-ui-customization/README.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15i-role-permission-audit-hardening-governance-2026-06-26.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15i1-review-contracts-and-gap-audit-setup-2026-06-27.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15i2-implementation-gap-audit-matrix-2026-06-27.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15i5-audit-metadata-cleanup-2026-06-27.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15i6-role-permission-audit-hardening-closure-2026-06-27.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15j1-release-readiness-checklist-2026-06-27.md`
- `_docs/erp-ui-customization/warehouse-console-phase-w15j2-staged-scope-final-validation-plan-2026-06-27.md`

### Warehouse Service / Tests / UI / Smoke

- `erp_workspace_ui/warehouse_console/service.py`
- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`

### Customer Return DocTypes

- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_intake/warehouse_customer_return_intake.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_intake_line/warehouse_customer_return_intake_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_intake_event/warehouse_customer_return_intake_event.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_handoff_request/warehouse_customer_return_handoff_request.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_handoff_request_line/warehouse_customer_return_handoff_request_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_customer_return_handoff_request_event/warehouse_customer_return_handoff_request_event.json`

### Supplier Return DocTypes

- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_candidate/warehouse_supplier_return_candidate.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_candidate_line/warehouse_supplier_return_candidate_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_candidate_event/warehouse_supplier_return_candidate_event.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_handoff_request/warehouse_supplier_return_handoff_request.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_handoff_request_line/warehouse_supplier_return_handoff_request_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_supplier_return_handoff_request_event/warehouse_supplier_return_handoff_request_event.json`

### Internal Transfer DocTypes

- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_candidate/warehouse_internal_transfer_candidate.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_candidate_line/warehouse_internal_transfer_candidate_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_candidate_event/warehouse_internal_transfer_candidate_event.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_handoff_request/warehouse_internal_transfer_handoff_request.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_handoff_request_line/warehouse_internal_transfer_handoff_request_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_internal_transfer_handoff_request_event/warehouse_internal_transfer_handoff_request_event.json`

### Cycle Count / Inventory Variance DocTypes

- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_cycle_count_task/warehouse_cycle_count_task.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_cycle_count_task_line/warehouse_cycle_count_task_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_cycle_count_task_event/warehouse_cycle_count_task_event.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_inventory_variance_handoff_request/warehouse_inventory_variance_handoff_request.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_inventory_variance_handoff_request_line/warehouse_inventory_variance_handoff_request_line.json`
- `erp_workspace_ui/erp_workspace_ui/doctype/warehouse_inventory_variance_handoff_request_event/warehouse_inventory_variance_handoff_request_event.json`

## Explicit Exclude List

The following dirty files must remain unstaged unless a separate owner-approved phase explicitly includes them:

- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `ui_smoke/sales_final_acceptance_audit.js`

The following generated or environment artifacts must also remain unstaged if present:

- `__pycache__/`
- `*.pyc`
- `node_modules/`
- screenshots
- browser traces
- temporary diagnostics
- local smoke output

## Pre-Staging Validation Gates

Before any later staging action, rerun:

- `git diff --check HEAD`
- JSON validation for all changed Warehouse DocType JSON files
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- README/W15 docs trailing whitespace scan
- metadata boundary scan for no forbidden field types
- static scan for no native route exposure except negative assertions and blocked-policy documentation
- static scan for no active Stock Reconciliation, Stock Entry, Stock Ledger, Stock Balance, Stock Reservation, stock movement/posting, valuation/accounting/commercial exposure, notification/email/portal behavior, Sales runtime, or Procurement runtime
- cache cleanup/check under changed Python paths
- `git status --short --branch`

The latest known full source gate before W15J2 was `402 tests OK` after W15I5. W15J2 is docs-only, but pre-staging validation should rerun the full gate because staging/commit is a higher-risk transition.

## Later Staging Procedure

If W15J2 is accepted and owner later approves staging, Main Control should stage only the include list.

After staging, Main Control must run:

- `git diff --cached --name-status`
- `git diff --cached --check`
- `git diff --cached --stat`
- a staged-file allowlist check against the include list;
- a staged-file denylist check against the exclude list;
- final `git status --short --branch`.

The staged diff must be reviewed before commit. No commit may happen in the same step as first staging unless owner explicitly approves after reviewing the staged result.

## Commit / Push Decision Gates

Before any commit:

- Hardening must accept exact staged scope.
- Security/Stability must accept exact staged scope.
- Operations must accept exact staged scope.
- Owner must explicitly approve commit.
- Commit message must be shown before commit.

Before any push:

- Owner must explicitly approve push after commit.
- Push target branch must be confirmed.
- No live alignment, restart, protected gate, or deployment may be bundled with push.

## Runtime / Live Boundary

W15J2 does not approve:

- planned workflow activation;
- active customer return, supplier return, internal transfer, or cycle count queues;
- Sales/Admin/Finance/Procurement/Inventory/Admin downstream runtime;
- Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, Purchase Invoice return, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, or Stock Reservation behavior;
- stock movement, stock posting, reserve, or unreserve;
- native route exposure;
- valuation/accounting/commercial exposure;
- notification, email, portal, or external action;
- live alignment, restart, protected gate, release closure, commit, or push.

## W15J2 Recommendation

W15J2 recommends proceeding next to a final validation and staging execution phase only if:

- this staged-scope plan is accepted by Hardening, Security/Stability, and Operations;
- owner approves moving from planning to staging execution;
- no new dirty files appear outside the include/exclude classification.

W15J2 itself must end without staging, commit, push, live alignment, restart, protected gate, release closure, runtime activation, or external action.

## Boundary Confirmation

W15J2 is docs-only.

No runtime/backend method, DocType metadata, test, smoke, live file, Sales runtime, Procurement runtime, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, staging, commit, push, live alignment, restart, protected gate, release closure, or external action is approved by W15J2.
