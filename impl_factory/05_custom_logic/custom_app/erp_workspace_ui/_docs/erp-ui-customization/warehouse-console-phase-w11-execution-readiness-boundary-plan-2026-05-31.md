# Warehouse Console Phase W11 Execution Readiness Boundary Plan

Date: 2026-05-31

Branch: `feature/erpnext-ui-design`

Status: docs-only planning and research boundary. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

Accepted baseline:

- Warehouse read-only freeze: `warehouse-console-read-only-visibility-v1`
- Latest runtime fix: `23dc8d42fe8bdef31eec2008efa20666abba9b8a`
- Latest docs closure: `25f487c228450220ca8a9d294566ae572697152a`

## 1. Decision

Do not start another Warehouse implementation phase yet.

W11 should be a research and boundary phase that decides whether the next Warehouse program stays read-only or opens a separately governed execution track.

Reason:

- Warehouse now has a protected read-only visibility foundation for receiving, picking, stock exceptions, stock posture, movement, and transfer visibility.
- The next natural requests are likely execution verbs: receive, pick, reserve, transfer, reconcile, post, submit, scan, pack, ship, or complete.
- Those verbs change the product risk category from visibility to operational mutation.
- Execution work must not be slipped into a UI polish or visibility prompt.

Main Control decision:

- Keep current Warehouse read-only baseline frozen.
- Use W11 to define execution boundaries, required controls, and agent responsibilities.
- Require owner approval before any execution implementation.

## 2. Research Baseline

ERPNext stock execution surfaces are real operational documents and should be treated as controlled write workflows, not UI links.

Official ERPNext/Frappe references reviewed:

- Purchase Receipt records received quantities and creates accounting and stock ledger entries on submission: [ERPNext Purchase Receipt](https://docs.frappe.io/erpnext/purchase-receipt)
- Delivery Note records sent goods and affects stock ledger on submission when items maintain stock: [ERPNext Delivery Note](https://docs.frappe.io/erpnext/delivery-note)
- Stock Entry covers material receipt, issue, transfer, manufacture, repack, subcontract, and stock reconciliation-related inventory movements: [ERPNext Stock Entry](https://docs.frappe.io/erpnext/stock-entry)
- Stock Reconciliation updates stock balances and valuation rates: [ERPNext Stock Reconciliation](https://docs.frappe.io/erpnext/stock-reconciliation)
- Pick List supports warehouse picking for Sales Orders, Work Orders, and Material Requests: [ERPNext Pick List](https://docs.frappe.io/erpnext/pick-list)
- Stock Reservation reserves stock against Sales Orders: [ERPNext Stock Reservation](https://docs.frappe.io/erpnext/stock-reservation)
- Serial and batch handling can create traceability obligations and validation complexity: [ERPNext Serial and Batch Bundle](https://docs.frappe.io/erpnext/serial-and-batch-bundle)

Implication:

- Receiving, picking, delivery, reservation, transfer, reconciliation, serial/batch assignment, and stock posting are not cosmetic UI concerns.
- Any execution layer needs role controls, validation, auditability, conflict handling, rollback/error states, and explicit business ownership.

## 3. Current Read-Only Baseline

Protected top-level route:

- `/desk/warehouse-console`

Protected worklists:

- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-worklist/outbound-picking`
- `/desk/warehouse-console-worklist/stock-exceptions`
- `/desk/warehouse-console-worklist/movement-visibility`
- `/desk/warehouse-console-worklist/transfer-visibility`

Protected reviews:

- `/desk/warehouse-console-receiving/<purchase-order>`
- `/desk/warehouse-console-picking/<sales-order>`
- `/desk/warehouse-console-stock-exception/<encoded-context>`
- `/desk/warehouse-console-stock-posture/<encoded-context>`
- `/desk/warehouse-console-movement/<encoded-context>`

Protected read-only posture:

- no stock mutation;
- no lifecycle controls;
- no native ERP form/list/report escape;
- no Stock Ledger or Stock Balance exposure;
- no valuation/accounting/commercial exposure;
- no Quick Find/Search;
- no Sales runtime change;
- no Procurement runtime change.

## 4. Execution Boundary

The following remain forbidden until an owner-approved execution track exists:

- create/submit/cancel/amend Purchase Receipt;
- create/submit/cancel/amend Delivery Note;
- create/submit/cancel/amend Stock Entry;
- create/submit/cancel/amend Pick List;
- create or release Stock Reservation;
- stock reconciliation or adjustment;
- serial/batch assignment or scan confirmation;
- transfer execution;
- receiving execution;
- picking completion;
- packing/shipping/dispatch execution;
- barcode scan that changes state;
- valuation/accounting/rate/amount exposure;
- native ERP Form/List/Report escape as the primary workflow.

Allowed without execution approval:

- docs-only research;
- role and permission audit;
- UI copy clarification;
- smoke hardening;
- duplicate chrome/shell cleanup;
- owner manual walkthrough evidence;
- read-only route polish that does not add new business capability.

## 5. Open Product Questions

W11 should answer these before implementation:

- Should the next Warehouse phase stay read-only?
- Which warehouse role is authorized to execute receiving, picking, transfer, and reconciliation?
- Are execution actions allowed in the custom Warehouse UI, or should execution remain in native ERPNext for now?
- What is the first execution workflow with the least risk and highest business value?
- What user confirmation, validation, and audit trail are mandatory?
- How should errors be handled when stock changed after the user opened a page?
- Should barcode/scan be part of v1 execution or deferred?
- Should serial/batch controlled items be excluded from initial execution?
- Should valuation/accounting remain fully hidden even if execution is introduced?
- How should Sales and Procurement workspaces remain protected from Warehouse execution changes?

## 6. Recommended W11 Agent Sequence

Main Control should not implement source in W11.

Recommended sequence:

1. Main Control writes and commits this W11 boundary plan.
2. Warehouse Agent performs source-only execution-readiness research.
3. Security and Stability Review Agent audits execution risks and required guardrails.
4. Operation Reviewer Agent validates warehouse-user workflow and business priority.
5. Hardening Agent reviews route/smoke/idempotency implications only after a candidate direction exists.
6. Main Control synthesizes a W11A decision document.
7. Owner chooses one of:
   - continue read-only visibility only;
   - start a premium UI polish phase;
   - start a separately governed execution design track.

## 7. Warehouse Agent Prompt

Use this prompt if assigning W11 to Warehouse Agent:

```text
You are the Warehouse Agent. Your task is W11 execution-readiness research only.

Repository:
/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui

Branch:
feature/erpnext-ui-design

Do not commit, push, live-align, or run protected gates.
Do not implement runtime, routes, APIs, tests, smokes, package scripts, or fixtures unless Main Control explicitly authorizes a later implementation phase.

Context:
Warehouse read-only visibility is frozen as `warehouse-console-read-only-visibility-v1`.
The accepted routes cover:
- Warehouse Cockpit
- Inbound Receiving
- Receiving Review
- Outbound Picking
- Picking Review
- Stock Exceptions
- Stock Exception Review
- Stock Posture Review
- Movement Visibility
- Movement Review
- Transfer Visibility

Task:
1. Inventory existing Warehouse read-only routes and service methods.
2. Identify which future execution workflows are adjacent:
   - receiving from Purchase Order
   - picking from Sales Order
   - Stock Entry transfer
   - Stock Reservation
   - Stock Reconciliation
   - serial/batch scan or assignment
3. For each workflow, classify:
   - business value
   - mutation risk
   - required ERPNext source documents
   - required role gates
   - required validation
   - whether v1 should include it or defer it
4. Recommend the safest next direction:
   - remain read-only;
   - premium UI polish;
   - docs-only execution design;
   - one narrow execution pilot.
5. Produce a written report only.

Hard restrictions:
- No receiving/posting/picking/transfer execution.
- No Stock Entry, Purchase Receipt, Delivery Note, Pick List, Stock Reservation, or Stock Reconciliation creation.
- No valuation/accounting/commercial exposure.
- No native ERP escape.
- No Quick Find/Search.
- No Sales or Procurement runtime changes.

Validation:
- If you changed no files, run only `git status --short --branch`.
- If you create docs only, run:
  - `git diff --check HEAD`
  - `python3 -m compileall erp_workspace_ui`
  - `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`

Return:
- Findings by workflow.
- Recommended next phase.
- Explicit list of things that must remain forbidden.
- Final git status.
```

## 8. Security And Stability Review Agent Prompt

Use this prompt after Warehouse Agent completes W11 research:

```text
You are the Security and Stability Review Agent. Your task is W11 execution-risk review only.

Do not commit, push, live-align, or run protected gates.
Do not implement execution.

Review the W11 Warehouse Agent report and the current Warehouse source.

Audit:
1. Role and permission gates required before any execution.
2. Server-side write risks for Purchase Receipt, Delivery Note, Stock Entry, Pick List, Stock Reservation, Stock Reconciliation, serial/batch assignment, and scan flows.
3. Concurrency risks when stock state changes between page load and action.
4. Validation requirements for warehouse, item, quantity, UOM, serial, batch, company, docstatus, and linked source document.
5. Audit trail requirements.
6. Rollback/error-state requirements.
7. Valuation/accounting exposure risks.
8. Native ERP escape risks.
9. Sales/Procurement protected workspace boundary risks.

Return:
- Blocker/High/Medium/Low findings.
- Required guardrails before execution can be designed.
- Whether any execution pilot is safe to design yet.
- Final git status.
```

## 9. Operation Reviewer Agent Prompt

Use this prompt after Security/Stability review:

```text
You are the Operation Reviewer Agent. Your task is W11 warehouse-operations review only.

Do not commit, push, live-align, or run protected gates.
Do not implement execution.

Review W11 Warehouse Agent and Security/Stability outputs as a warehouse supervisor.

Assess:
1. Which workflow creates the most operational value:
   - receiving
   - picking
   - transfer
   - stock reservation
   - stock reconciliation
   - scan/serial/batch
2. Which workflow has the clearest business ownership and least training risk.
3. Which workflow should remain native ERPNext for now.
4. Whether current read-only screens already answer enough operational questions.
5. Whether premium UI polish should come before execution.

Return:
- Operational acceptance decision.
- Recommended next business direction.
- Manual user-check checklist if needed.
- Final git status.
```

## 10. Hardening Agent Prompt

Use this prompt only after a W11 direction exists:

```text
You are the Hardening Agent. Your task is W11 route/smoke hardening analysis only.

Do not commit, push, live-align, or run protected gates.
Do not implement execution.

Given the W11 recommended direction, assess:
1. Route idempotency requirements.
2. Duplicate shell/chrome risks.
3. Stale async response risks.
4. Repeated route and refresh behavior.
5. Mobile/laptop/desktop layout pressure.
6. Focused smoke evidence required before Main Control accepts any future phase.

Return:
- Required hardening checklist.
- Suggested focused smoke scenarios.
- Forbidden regression assertions.
- Final git status.
```

## 11. Main Control Acceptance Criteria

Before any W11 implementation can begin, Main Control needs:

- Warehouse Agent report;
- Security/Stability risk review;
- Operation Reviewer decision;
- Hardening checklist if implementation is proposed;
- owner approval of the selected direction.

If the selected direction is execution, Main Control must require a new phase name and protection standard separate from read-only Warehouse visibility.

Suggested execution-track name if owner approves later:

- `warehouse-execution-design-v1`

Do not merge it into `warehouse-console-read-only-visibility-v1`.

## 12. Recommendation

Recommended next step after this docs-only W11 plan:

- Assign Warehouse Agent the W11 execution-readiness research prompt.

Recommended near-term product direction:

- Stay read-only until owner manual review is complete.
- If owner wants visible improvement next, choose premium UI polish before execution.
- If owner wants operational mutation next, start with docs-only execution design, not code.
