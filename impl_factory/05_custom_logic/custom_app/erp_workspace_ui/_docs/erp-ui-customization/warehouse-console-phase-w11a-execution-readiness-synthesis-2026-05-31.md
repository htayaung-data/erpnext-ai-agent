# Warehouse Console Phase W11A Execution Readiness Synthesis

Date: 2026-05-31

Status: docs-only Main Control synthesis.

This record summarizes the W11 execution-readiness decision sequence after the Warehouse Console read-only visibility freeze. It does not add runtime code, routes, backend methods, tests, smokes, live alignment, stock mutation, valuation exposure, native ERP access, Quick Find/Search, Sales behavior, or Procurement behavior.

## Inputs

- Baseline decision: `warehouse-console-phase-w11-execution-readiness-boundary-plan-2026-05-31.md`, committed at `68db2ded87845c42ac4e74306308e8e7703b1cd9`.
- Warehouse Agent recommendation: `docs_only_execution_design`.
- Security/Stability Review Agent decision: `allow_docs_only_execution_design`.
- Operation Reviewer Agent decision: `docs_only_receiving_design`.
- Current protected Warehouse freeze: `warehouse-console-read-only-visibility-v1`, with W10A read-only hardening, W10B freeze closure, and W10C page chrome fix accepted.

## Main Control Decision

The next approved direction is `docs_only_receiving_design`.

This means:

- Do not implement receiving execution.
- Do not create a pilot runtime route.
- Do not create, submit, cancel, amend, or post Purchase Receipt records.
- Do not add any stock ledger, valuation, accounting, commercial, native ERP escape, Quick Find/Search, Sales runtime, or Procurement runtime behavior.
- Do prepare a design package for a possible future Purchase Receipt receiving workflow, because receiving from Purchase Order is the highest-value execution candidate and is adjacent to the accepted Inbound Receiving and Receiving Review screens.

Premium UI polish remains necessary before any execution implementation. It does not block a docs-only receiving design package, but it must happen before any future execution runtime is built.

Owner manual walkthrough remains recommended before locking any execution design. The owner should review the Warehouse Cockpit, Inbound Receiving, Receiving Review, Outbound Picking, Picking Review, Stock Exceptions, Stock Exception Review, Stock Posture, Movement Visibility, Movement Review, and Transfer Visibility surfaces before approving an execution workflow.

## Candidate Priority

1. Purchase Receipt receiving from Purchase Order: first design candidate only.
2. Premium UI polish: before any execution implementation.
3. Pick List or picking from Sales Order: later design candidate, after receiving.
4. Delivery Note or shipping handoff: defer because it is downstream-heavy and Sales/customer-facing.
5. Stock Entry material transfer execution: defer because Stock Entry is broad and high-risk.
6. Barcode or scan-assisted workflow: read-only lookup only until base execution is mature.
7. Stock Reservation: keep native ERPNext for now.
8. Serial or batch assignment: defer; treat as a constraint inside future receiving/picking design, not a standalone first workflow.
9. Stock Reconciliation or adjustment: keep native ERPNext; not suitable for normal Warehouse workspace execution.

## Required Receiving Design Package

Any W11B receiving design package must cover these sections before a runtime task can exist:

1. Scope and non-scope.
2. Role gates and actor model.
3. Source document eligibility from Purchase Order and Purchase Order Item.
4. Server write contract for any future Purchase Receipt creation/submission.
5. Idempotency key and duplicate-click protection.
6. Before/after audit trail and evidence model.
7. Error, rollback, unavailable, restricted, and conflict states.
8. Serial/batch, quality inspection, rejected warehouse, partial receipt, over-receipt, and unit-of-measure constraints.
9. UI mode separation between read-only review and any future execution mode.
10. Smoke, unit, static-scan, source, live, and protected-gate evidence standard.
11. Sales and Procurement protected boundary.

## Execution Safety Standard

Any future execution path must meet this minimum standard:

- Owner-approved scope before implementation.
- New explicit backend methods; no native form delegation.
- Manager-only initial role gate unless owner approves a narrower operational role.
- ERPNext DocPerm checks and custom Warehouse role checks.
- Server-side validation of source document status, item eligibility, quantity, warehouse, company, UOM, serial/batch rules, and duplicate state.
- Transaction boundary and rollback on failure.
- Idempotency key on every write attempt.
- Duplicate-click protection in the custom UI.
- Structured custom-shell errors.
- Before/after audit record.
- No valuation, accounting, GL, tax, margin, profit, rate, amount, or commercial payload exposure.
- No native Form/List/Report escape.
- Negative tests for unauthorized roles, duplicate calls, stale state, missing permissions, and invalid quantities.

## Forbidden Boundary

Until owner approval and multi-agent acceptance of a specific design package, the following remain forbidden:

- Receiving execution.
- Picking execution.
- Shipping execution.
- Transfer execution.
- Reservation or unreservation.
- Reconciliation or adjustment.
- Posting, submit, cancel, amend, approve, reject, complete, close, or reopen actions.
- Purchase Receipt, Delivery Note, Stock Entry, Pick List, Stock Reservation, Stock Reconciliation, serial/batch bundle, or barcode mutation.
- Stock Ledger or Stock Balance native report exposure.
- Valuation, accounting, GL, tax, margin, profit, rate, amount, price, or cost fields.
- Native ERP Form/List/Report escape.
- Warehouse Quick Find or Search.
- Email, print, portal, AI, workflow, background job, or notification behavior.
- Sales or Procurement runtime changes.

## Next Agent Sequence

1. Main Control writes the W11B prompt for Warehouse Agent.
2. Warehouse Agent creates a docs-only Receiving Execution Design package.
3. Security/Stability Review Agent reviews the W11B design before runtime exists.
4. Operation Reviewer Agent validates the W11B business workflow and owner-facing UX risks.
5. Hardening Agent waits until there is an approved runtime candidate shape; no hardening task is needed for docs-only design unless requested.
6. Main Control synthesizes those outputs and asks the owner to approve, reject, or defer implementation.
7. No implementation may start until owner approval is explicit.

## Warehouse Agent W11B Prompt

Use this prompt for the next Warehouse Agent task.

```text
You are Warehouse Agent for ERP Workspace UI. Main Control has accepted W11A as docs-only execution-readiness synthesis. Your task is W11B: write a docs-only Receiving Execution Design package for a possible future Purchase Receipt receiving workflow.

Repository:
/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui

Branch:
feature/erpnext-ui-design

Hard boundaries:
- Do not implement runtime code.
- Do not modify JS, Python services, registry, governance manifest, tests, smokes, hooks, fixtures, or live files.
- Do not commit, push, or live-align.
- Do not create Purchase Receipt, Stock Entry, Pick List, Delivery Note, Stock Reservation, Stock Reconciliation, serial/batch, barcode, or workflow behavior.
- Do not add stock posting, submit, cancel, amend, receive, pick, ship, transfer, reserve, reconcile, approve, reject, complete, close, reopen, email, print, portal, AI, or background job behavior.
- Do not expose valuation, accounting, GL, tax, margin, profit, rate, amount, price, cost, Stock Ledger, or Stock Balance data.
- Do not add native ERP Form/List/Report routes or Warehouse Quick Find/Search.
- Do not touch Sales runtime or Procurement runtime.

Allowed work:
- Read local ERPNext/custom app source.
- Review existing Warehouse docs and protected route behavior.
- If current external docs are needed, use official ERPNext/Frappe documentation only and cite links in the report.
- Create or update only a W11B docs file under _docs/erp-ui-customization and README documentation references, unless Main Control says otherwise.

Design package requirements:
1. Define the exact scope and non-scope for future Purchase Receipt receiving from Purchase Order.
2. Define user roles and gates. Start from manager-only execution unless a narrower role model is justified.
3. Define eligible source documents and line eligibility rules from Purchase Order and Purchase Order Item.
4. Define forbidden source states, partial receipt behavior, over-receipt behavior, warehouse mismatch behavior, UOM constraints, rejected warehouse handling, quality inspection handling, serial/batch handling, and unavailable data states.
5. Define the future backend write contract in design form only: method names, required inputs, validation order, transaction boundary, idempotency key, audit record, rollback behavior, and structured errors.
6. Define UI mode separation between current read-only Receiving Review and any future execution mode.
7. Define duplicate-click protection, stale-data protection, refresh behavior, confirmation copy, and success/failure states.
8. Define audit evidence: actor, timestamp, source PO, item rows, quantities, warehouses, before/after status, idempotency key, resulting document name if future implementation exists, and failure reason.
9. Define test/smoke/static-scan/protected-gate evidence required before implementation and before live alignment.
10. Define Sales and Procurement freeze boundary protection.
11. Rank unresolved risks and state whether W11B should remain design-only or can be sent to Security/Stability review for possible future implementation approval.

Output format:
- Start with an acceptance decision: design-only, implementable-later only after approvals, or blocked.
- Provide findings by severity.
- Provide the complete receiving design package.
- Provide explicit non-scope and forbidden boundary.
- Provide validation performed.
- Provide final git status.

Validation required:
- git status --short --branch
- git diff --check HEAD
- If docs are changed, run python3 -m compileall erp_workspace_ui and PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'

Stop condition:
Stop after docs and validation. Do not commit, push, run credentialed smokes, run protected gates, or live-align.
```

## Validation Standard For W11A

Because W11A is documentation-only, validation is limited to:

- Documentation diff review.
- `git diff --check HEAD`.
- Python compileall and unit discovery as a guard against accidental runtime edits.

## Final Recommendation

Proceed to Warehouse Agent W11B docs-only Receiving Execution Design using the prompt above. Do not start runtime implementation.
