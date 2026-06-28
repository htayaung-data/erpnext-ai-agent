# Warehouse Console Phase W15I6 Role / Permission / Audit Hardening Closure

Decision: `implementation_ready_for_review`

Date: 2026-06-27

Scope: docs-only closure and readiness decision for W15I role, permission, audit, and hardening governance after W15I1-W15I5. W15I6 does not approve planned workflow activation, ERPNext stock/accounting document runtime, native ERPNext routes, notification behavior, Sales/Procurement runtime changes, live alignment, restart, protected gate, commit, push, or release closure.

## Purpose

W15I6 records whether the W15I governance track has completed its intended job:

- define strict review contracts;
- audit W15E/F/G/H implementation gaps;
- patch accepted High and Medium gaps;
- close safe audit metadata/test/UI wording cleanup;
- confirm remaining risks are deferred behind later owner/security approval.

W15I6 is not a claim that Warehouse operations are finished. It closes the W15I hardening pass over the current custom-record foundations and decides whether the project may proceed to the next planned governance phase.

## W15I Baseline

W15I is layered on top of the W15E/F/G/H Warehouse foundations:

- W15E: customer return intake, manager disposition posture, request-only Sales/Admin handoff, and customer-return policy boundaries.
- W15F: supplier return candidate, manager posture, request-only Procurement/Finance/Admin handoff, and supplier-return policy boundaries.
- W15G: internal transfer candidate, manager posture, request-only Inventory/Admin handoff, and Stock Entry draft policy boundaries.
- W15H: cycle count / inventory variance task, manager variance posture, request-only Inventory/Admin handoff, and Stock Reconciliation draft policy boundaries.

Those foundations remain custom Warehouse records and request/status behavior only. They do not create, save, submit, cancel, amend, or post ERPNext stock/accounting documents.

## Completed W15I Work

### W15I Governance Checkpoint

W15I established the rule set for role gates, custom DocType permissions, idempotency, audit fields, native-route containment, no-effect response flags, planned-shell UI behavior, and release-readiness criteria.

It explicitly kept these blocked:

- Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, Purchase Invoice return, Stock Entry, and Stock Reconciliation runtime;
- Stock Ledger, Stock Balance, Stock Reservation, stock movement, and stock posting;
- native ERPNext route exposure;
- valuation, accounting, and commercial exposure;
- customer/supplier notification, email, portal, or external action;
- Sales and Procurement runtime changes.

### W15I1 Review Contracts

W15I1 created strict review contracts for:

- Hardening review;
- Security/Stability review;
- Operations review;
- Hybrid Review Ladder usage;
- gap matrix shape and severity rules;
- external review handoff expectations.

The W15I1 contracts are now the review baseline for later Warehouse hardening and closure phases.

### W15I2 Gap Audit Matrix

W15I2 audited W15E/F/G/H against the W15I1 contracts and identified:

- High gaps in manager-decision idempotency, request-id scope, and forbidden line-field handling;
- Medium gaps in validation consistency, audit metadata, and request-line preservation;
- Low gaps in wording and explicit negative test coverage.

Reviewer correction from W15I2 was incorporated: forbidden top-level or line fields accepted/ignored is a High boundary issue unless source review proves otherwise.

### W15I3 High-Gap Hardening

W15I3 patched High gaps first.

Accepted W15I3 behavior includes:

- manager decision idempotency compares same-decision details, not only event type;
- handoff request ids reject reuse of source draft request ids and source manager-event request ids;
- supplier return manager request-id ownership checks the source parent draft request id;
- customer/supplier return draft line payloads reject non-empty unknown/forbidden line keys;
- customer return draft rejects over-limit line payloads instead of truncating line 81+.

W15I3 remained bounded to custom Warehouse validation/idempotency hardening.

### W15I4 Medium Validation Hardening

W15I4 patched the accepted Medium validation gaps.

Accepted W15I4 behavior includes:

- W15E/F manager and handoff endpoints reject non-empty unexpected top-level fields;
- supplier return handoff preserves `overage_qty` and `quality_hold_qty` through metadata, source-line derivation, payload hash, persistence, and response payload;
- inventory variance handoff revalidates derived source lines for negative counted quantity, invalid direction/status, missing evidence, and `No Variance` with non-zero variance quantity;
- duplicate request-id owner helpers fail closed instead of selecting the first row.

W15I4 remained bounded to custom Warehouse evidence/status/request behavior.

### W15I5 Audit Metadata Cleanup

W15I5 closed safe audit metadata/test/UI wording cleanup.

Accepted W15I5 behavior includes:

- all 24 W15E/F/G/H custom Warehouse workflow DocTypes have `allow_web_indexing: 0`;
- all 24 retain `index_web_pages_for_search: 0`;
- event child DocTypes require `event_type`, `event_by`, `event_at`, and `request_id`, all read-only;
- `Warehouse Cycle Count Task.request_id` is required;
- W15H4/W15H5 safe-payload tests explicitly assert forbidden-doctype absence in `GET_ALL_CALLS`;
- Warehouse Overview cycle-count copy says `System document access`, not raw `Native routes`;
- W9A smoke asserts the owner-facing wording and rejects raw `Native routes`.

W15I5 documented the accepted event model:

- required audit anchors: `event_type`, `event_by`, `event_at`, and `request_id`;
- optional display/detail fields: `event_label` and `details_json`;
- `details_json` remains the service-owned extension point for action-specific audit details.

## Validation Ledger

The latest cumulative source gate after W15I5 passed:

- `git diff --check HEAD`
- JSON validation on all 24 W15I5 DocTypes
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`: `402 tests OK`
- README/W15I5 trailing whitespace check
- metadata boundary scan
- cache cleanup/check

Prior W15I source gates were also accepted:

- W15I3: full tests passed with `399 tests OK`;
- W15I4: full tests passed with `401 tests OK`;
- W15I5: full tests passed with `402 tests OK`.

## Review Ledger

W15I used the Hybrid Review Ladder:

- internal subagent preflight for bounded audit/hardening checks;
- separate Hardening, Security/Stability, and Operations agents for phase acceptance.

External review status:

- W15I2 gap matrix: accepted after reviewer correction to matrix columns/classification expectations.
- W15I3 High-gap hardening: accepted by Hardening, Security/Stability, and Operations.
- W15I4 Medium validation hardening: accepted by Hardening, Security/Stability, and Operations.
- W15I5 audit metadata cleanup: accepted by Hardening, Security/Stability, and Operations.

No owner manual UI check was required for W15I5 because the only visible change was wording-only and smoke-covered. Earlier W15H2 owner manual review accepted the planned-shell organizer and cycle-count shell visibility.

## Current Readiness Decision

W15I6 recommends W15I as complete for its intended scope.

This means:

- the W15E/F/G/H custom-record foundations have passed the W15I audit/hardening pass;
- High and accepted Medium W15I gaps have been patched;
- remaining Low items are wording/future-UI posture only and do not block closure;
- W15J may start as a separate reviewed phase.

This does not mean:

- Warehouse implementation is finished;
- planned workflow shells are active queues;
- ERPNext stock/accounting documents may be created;
- native ERPNext routes may be exposed;
- live alignment, restart, protected gate, commit, push, or release closure is approved by this document.

## Recommended Next Phase

The next phase should be W15J as a separate release-readiness / closure package.

W15J should:

- summarize W15C-W15I Warehouse foundations and current state;
- decide whether the current Warehouse foundation can be committed/pushed as a safe milestone;
- list all planned-but-inactive workflow shells and runtime blockers;
- define whether W16 should focus on active queue consolidation, owner-facing UI polish, or a separate Inventory/Admin/Sales/Procurement integration phase;
- keep all ERPNext document runtime blocked unless a new owner/security-approved phase explicitly opens it.

W15J must not silently activate any planned workflow.

## Remaining Deferred Work

These remain deferred behind separate owner/security approval:

- active UI workflows for customer return, supplier return, internal transfer, and cycle count;
- Sales/Admin/Finance/Procurement/Inventory/Admin downstream queues;
- customer or supplier notification;
- Purchase Receipt, Delivery Note, Sales Return, Credit Note, Purchase Invoice return, Stock Entry, or Stock Reconciliation draft/runtime;
- Stock Ledger, Stock Balance, Stock Reservation, stock movement, or stock posting;
- native route exposure;
- valuation/accounting/commercial fields;
- attachments, portals, email, external actions, or native document links;
- live alignment, protected gate, restart, commit, push, or release closure.

## Closure Boundary

W15I6 is docs-only.

No runtime/backend method, DocType metadata, test, smoke, live file, Sales runtime, Procurement runtime, Stock Reconciliation behavior, Stock Entry behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, notification/email/portal behavior, commit, push, live alignment, restart, protected gate, or external action is approved by W15I6.
