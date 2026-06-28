# Warehouse Console Phase W15I5 Audit Metadata Cleanup

Decision: `implementation_ready_for_review`

Date: 2026-06-27

Scope: narrow W15I audit/metadata/test cleanup after W15I3 High-gap hardening and W15I4 Medium validation hardening. W15I5 does not approve planned workflow activation, ERPNext stock/accounting document runtime, native ERPNext routes, notification behavior, Sales/Procurement runtime changes, live alignment, restart, protected gate, commit, or release closure.

## Review Baseline

W15I5 is applied on top of the already reviewed-but-uncommitted W15I3 and W15I4 worktree.

W15I3 owns the High-gap runtime hardening for manager-decision idempotency, request-id scope, source draft/event reuse rejection, unknown line-field rejection, and customer-return over-limit line rejection.

W15I4 owns the Medium validation hardening for explicit extra top-level payload rejection, supplier handoff preservation of `overage_qty` and `quality_hold_qty`, inventory variance source-line revalidation, and duplicate request-id owner fail-closed behavior.

W15I5 does not re-approve or expand those W15I3/W15I4 runtime/schema changes. W15I5 reviewers should evaluate only the new audit metadata, tests, documentation, and owner-facing wording cleanup introduced after W15I4 acceptance.

## Purpose

W15I5 resolves the remaining safe audit and metadata cleanup items from W15I2 without expanding Warehouse runtime behavior.

The target gaps are:

- Event child DocType requiredness for core audit fields.
- Cycle Count Task `request_id` metadata alignment with the service contract.
- Explicit web-indexing disablement through `allow_web_indexing: 0`.
- Cycle Count safe-payload negative test explicitness for list-fetch calls.
- Owner-facing W15H planned-shell wording.
- W15I audit-event normalization decision.

## Audit Event Schema Decision

W15I5 standardizes the current event model as:

- First-class required core fields: `event_type`, `event_by`, `event_at`, and `request_id`.
- First-class optional display/detail fields: `event_label` and `details_json`.
- `details_json` remains the accepted structured extension point for action-specific audit data in W15E/F/G/H.

The accepted `details_json` model is intentionally service-owned and custom-record-only. It may contain normalized action details such as decision key, note, references, previous state, next state, handoff type, line count, payload flags, and no-effect confirmation flags.

W15I5 does not add broad first-class audit columns such as source doctype/name/line, target workflow, old/new state, actor role family, payload hash, validation result, or evidence summary across all event DocTypes. That larger schema migration remains deferred until there is a specific owner/security-approved need, because the current records are service-created child rows and not direct native-entry workflows.

## Metadata Cleanup

W15I5 should mark these event child fields required across W15E/F/G/H event DocTypes:

- `event_type`
- `event_by`
- `event_at`
- `request_id`

W15I5 should mark `Warehouse Cycle Count Task.request_id` required, matching the backend service requirement.

W15I5 should add `allow_web_indexing: 0` to W15E/F/G/H custom DocTypes, preserving the existing `index_web_pages_for_search: 0` boundary.

## Test And UI Cleanup

W15I5 should add `GET_ALL_CALLS` negative assertions to W15H4/W15H5 safe payload tests where they previously asserted only `GET_DOC_CALLS`.

W15I5 should replace the owner-facing W15H Overview copy `Native routes` with `System document access` while keeping native-route exposure blocked by smoke assertions.

## Explicit Non-Goals

W15I5 must not:

- create, save, submit, cancel, amend, or delete Stock Reconciliation or Stock Entry records;
- mutate Stock Ledger, Stock Balance, Stock Reservation, or stock quantities;
- expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report`;
- expose valuation, accounting, commercial, rate, amount, tax, GL, payable, credit, debit, payment, billing, margin, cost, or profit fields;
- notify customers or suppliers;
- add email, portal, external action, Sales runtime, or Procurement runtime behavior;
- activate planned workflow shells.

## Review Requirement

W15I5 requires Hardening, Security/Stability, and Operations review before acceptance.

No owner manual UI check is required if the only visible change is the copy replacement from `Native routes` to `System document access`, because this is owner-facing wording cleanup and not workflow activation.
