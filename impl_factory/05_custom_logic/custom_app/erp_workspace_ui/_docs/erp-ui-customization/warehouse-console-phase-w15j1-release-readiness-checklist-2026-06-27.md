# Warehouse Console Phase W15J1 Release Readiness Checklist

Decision: `implementation_ready_for_review`

Date: 2026-06-27

Scope: docs-only release-readiness checklist after W15I closure. W15J1 defines what must be true before a Warehouse milestone commit/push or any later release action can be considered. W15J1 does not approve commit, push, live alignment, restart, protected gate, workflow activation, ERPNext document runtime, stock/accounting mutation, native route exposure, notification behavior, Sales/Procurement runtime changes, or release closure.

## Purpose

W15J1 starts the Warehouse release-readiness track after W15I closed the role, permission, audit, and hardening pass.

The goal is to separate three decisions that must not be mixed:

- whether the current Warehouse worktree is a safe milestone candidate;
- whether the milestone may be committed and pushed;
- whether any live/runtime workflow may be activated.

W15J1 answers only the first question at checklist level. It prepares the evidence needed for later owner/security approval, but it does not itself authorize commit, push, live alignment, restart, protected gate, or runtime activation.

## Current Accepted Foundation

The current Warehouse foundation includes the accepted W15C-W15I tracks:

- W15C/W15D: controlled operations policy direction and Warehouse action-center foundations.
- W15E: customer return intake, manager disposition posture, and request-only Sales/Admin handoff foundations.
- W15F: supplier return candidate, manager posture, and request-only Procurement/Finance/Admin handoff foundations.
- W15G: internal transfer candidate, manager posture, and request-only Inventory/Admin handoff foundations.
- W15H: cycle count / inventory variance task, manager variance posture, and request-only Inventory/Admin handoff foundations.
- W15I: role, permission, audit, idempotency, metadata, validation, and wording hardening over W15E/F/G/H.

The accepted foundation is custom-record and request/status oriented. It is not ERPNext document execution.

## Safe Milestone Candidate Definition

A Warehouse milestone candidate is safe only if it remains within these boundaries:

- custom Warehouse records only for evidence, posture, request, and audit data;
- planned workflow shells remain planned/inactive unless separately approved;
- no ERPNext stock/accounting document lifecycle behavior;
- no native ERPNext route exposure;
- no valuation, accounting, commercial, rate, amount, tax, GL, payable, credit, debit, billing, payment, margin, cost, or profit exposure;
- no customer/supplier notification, email, portal, external action, or supplier/customer-facing communication;
- no Sales, Procurement, Finance, Inventory/Admin runtime workflow unless separately approved;
- no live alignment, restart, protected gate, commit, push, or release closure without a later explicit owner decision.

## Current Worktree Reality

The current Warehouse worktree is intentionally layered:

- W15I3 runtime hardening is present and accepted.
- W15I4 validation/schema hardening is present and accepted.
- W15I5 audit metadata/test/UI wording cleanup is present and accepted.
- W15I6 docs-only hardening closure is present and accepted.
- W15J1 adds this checklist only.

External reviewers should not reject W15J1 merely because W15I3-W15I6 accepted changes remain dirty in the same uncommitted worktree.

Before any later commit/push decision, the final staging scope must be reviewed file-by-file and unrelated dirty files must remain excluded.

## Planned But Inactive Workflows

The following Overview planned workflow shells remain inactive:

- Customer return intake.
- Supplier return candidate.
- Internal transfer candidate.
- Cycle count / inventory variance.

The following backend foundations exist as custom-record behavior but must not be treated as active execution queues:

- customer return draft evidence and manager disposition posture;
- customer return request-only Sales/Admin handoff;
- supplier return draft evidence and manager posture;
- supplier return request-only Procurement/Finance/Admin handoff;
- internal transfer candidate draft and manager posture;
- internal transfer request-only Inventory/Admin handoff;
- cycle count task draft and manager variance posture;
- inventory variance request-only Inventory/Admin handoff.

## Blocked ERPNext Document Actions

The following remain blocked until a later owner/security-approved phase explicitly opens them:

- Purchase Receipt draft/create/save/submit/cancel/amend;
- Delivery Note draft/create/save/submit/cancel/amend;
- Pick List create/save/submit/cancel/amend;
- Sales Return create/save/submit/cancel/amend;
- Credit Note create/save/submit/cancel/amend;
- Purchase Invoice return/debit note create/save/submit/cancel/amend;
- Stock Entry draft/create/save/submit/cancel/amend/delete;
- Stock Reconciliation draft/create/save/submit/cancel/amend/delete;
- Stock Ledger mutation;
- Stock Balance mutation;
- Stock Reservation, reserve, or unreserve;
- stock increase, decrease, movement, or posting.

## Blocked Exposure And Route Actions

The following remain blocked:

- native route exposure through `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report`;
- native `Link`, `Dynamic Link`, `Attach`, `Attach Image`, `HTML`, `Button`, route, URL, or file fields unless separately reviewed;
- valuation, accounting, commercial, rate, amount, tax, account, GL, landed cost, cost, margin, profit, payable, receivable, debit, credit, refund, billing, payment, or write-off exposure;
- customer/supplier notification, email, portal, external action, or communication trigger.

## Required Validation Before Any Commit/Push Decision

Before any later commit/push decision, Main Control must rerun and record:

- `git diff --check HEAD`;
- JSON validation on all changed DocType JSON files;
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`;
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`;
- `python3 -m compileall -q erp_workspace_ui`;
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`;
- targeted smoke/static checks for no native route exposure and zero active controls in planned shells;
- metadata scan for no forbidden field types;
- cache cleanup and cache absence check;
- final `git status --short --branch`.

The current latest full test gate after W15I5 was `402 tests OK`. W15J1 is docs-only and does not require rerunning the full test suite unless a reviewer requests it before commit/push readiness.

## Required Scope Review Before Any Commit/Push Decision

Before any later commit/push decision, Main Control must:

- list all modified and untracked files;
- separate accepted Warehouse files from unrelated dirty files;
- verify unrelated `ai_assistant_ui` files remain unstaged;
- verify unrelated `ui_smoke/sales_final_acceptance_audit.js` remains unstaged unless separately approved;
- verify all W15I docs intended for milestone inclusion are present;
- verify no generated `__pycache__`, `.pyc`, `node_modules`, screenshots, temp files, or diagnostics are staged;
- review staged diff after staging and before commit;
- record the intended commit message and milestone scope before committing.

## Owner / Agent Decision Gates

Before any later commit/push decision:

- Hardening must accept the exact staged milestone scope.
- Security/Stability must accept the exact staged milestone scope.
- Operations must accept the exact staged milestone scope.
- Owner must explicitly approve commit/push.

Before any live alignment/restart/protected gate:

- W15J or later must explicitly approve those actions;
- Owner must explicitly approve those actions;
- live target, migration implications, and rollback path must be documented.

## W15J1 Readiness Recommendation

W15J1 recommends the current Warehouse foundation can proceed to a later W15J2 staged-scope review, but not directly to commit/push.

W15J2 should be the exact staged-file and final validation phase.

W15J1 does not approve:

- commit;
- push;
- live alignment;
- restart;
- protected gate;
- release closure;
- planned workflow activation;
- ERPNext document runtime;
- native route exposure;
- stock/accounting mutation;
- notification/email/portal behavior;
- Sales/Procurement/Finance/Inventory/Admin runtime.

## W16 Direction Options

After W15J milestone closure is separately accepted, W16 should be selected explicitly. Plausible W16 directions are:

- active queue consolidation for planned Warehouse workflow shells, still custom-record only;
- owner-facing UI polish and manual review ergonomics;
- Sales/Admin/Finance/Procurement/Inventory/Admin downstream queue design;
- separate ERPNext document draft governance, if owner/security explicitly approves opening that risk area.

W16 must not be assumed by W15J1.

## Boundary Confirmation

W15J1 is docs-only.

No runtime/backend method, DocType metadata, test, smoke, live file, Sales runtime, Procurement runtime, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, commit, push, live alignment, restart, protected gate, release closure, or external action is approved by W15J1.
