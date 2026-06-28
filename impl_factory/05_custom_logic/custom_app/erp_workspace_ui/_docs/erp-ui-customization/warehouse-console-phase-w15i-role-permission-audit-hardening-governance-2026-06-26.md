# Warehouse Console Phase W15I Role, Permission, Audit, And Hardening Governance

Decision: `docs_only_ready_for_control_review`

Date: 2026-06-26

Scope: documentation only. W15I does not implement runtime UI, backend methods, DocTypes, tests, smokes, live files, route behavior, native ERPNext links, stock documents, stock mutation, Sales runtime, Procurement runtime, notification behavior, or protected gates.

## 1. Purpose

W15I is the governance checkpoint after the W15C-W15H operations lanes reached their custom-record, manager-posture, request-only, or policy-only endpoints.

The purpose is to normalize role gates, permission boundaries, audit requirements, idempotency rules, and source-state hardening before any later Warehouse execution or release phase.

This phase does not approve any new operational mutation. It exists to prevent the next phase from starting with inconsistent contracts across receiving, dispatch, returns, supplier returns, internal transfer, and cycle count variance.

## 2. Covered Tracks

W15I applies to the currently planned Warehouse operations package:

- W15C inbound receiving and Purchase Receipt draft policy.
- W15D outbound picking / dispatch and Delivery Note policy.
- W15E customer return intake, manager posture, Sales/Admin handoff policy.
- W15F supplier return candidate, manager posture, Procurement/Admin handoff policy.
- W15G internal transfer candidate, manager posture, Inventory/Admin handoff, Stock Entry draft policy, and closure.
- W15H cycle count / inventory variance task, manager posture, Inventory/Admin handoff, Stock Reconciliation draft policy, and closure.

The accepted endpoint remains custom Warehouse records plus request/status handoff records only. ERPNext stock and accounting documents remain blocked unless a later owner/security-approved phase explicitly opens one document type with its own contract.

## 3. Standard Role Gate Policy

Every future W15-derived backend method must declare and test its role family.

Allowed role families:

- Warehouse evidence capture: `Warehouse User`, `Stock User`, `Warehouse Manager`, `Stock Manager`, `System Manager`, only where the phase explicitly allows physical evidence capture.
- Manager decision: `Warehouse Manager`, `Stock Manager`, `System Manager`.
- Downstream handoff request: `Warehouse Manager`, `Stock Manager`, `System Manager`.
- ERPNext document governance: blocked by default; if later approved, must be Inventory/Admin-owned or document-owner-owned, not silently Warehouse-owned.

Required denials:

- Warehouse User and Stock User must be denied from manager decision and downstream handoff methods.
- Sales and Procurement roles must not gain Warehouse mutation rights by implication.
- Customer, supplier, portal, guest, website, or unauthenticated contexts must have no Warehouse operation access.

## 4. Standard Permission Boundary

Custom DocType permissions must stay intentionally narrow:

- Evidence/task/candidate parent records may allow Warehouse User / Stock User create-write only when the workflow is physical evidence capture.
- Manager or handoff request parent records should keep Warehouse User / Stock User read-only.
- Manager, Stock Manager, and System Manager may create/write manager or handoff custom records where explicitly approved.
- Child tables must have no direct permissions.
- All fields should remain read-only metadata fields unless a later runtime form policy explicitly approves editable native forms.

Forbidden metadata remains:

- `Link`, `Dynamic Link`, `Attach`, `Attach Image`, `HTML`, `Button`, `Currency`.
- Native route, URL, file, portal, email, notification, or external action fields.
- ERPNext stock document link fields unless separately approved by security review.
- Valuation, rate, amount, tax, account, GL, margin, cost, profit, payment, billing, payable, debit, credit, or refund fields.

## 5. Standard Backend Contract

Every W15-derived write method must enforce:

- Server-side role gate before reading or writing workflow state.
- Actor derived from the session, not from the client payload.
- Visible warehouse validation for every source and target warehouse.
- Source record existence and source status allowlist.
- Request id required for every write.
- Payload hash idempotency for same-request retries.
- Changed-payload rejection for reused request ids.
- Cross-source request id reuse rejection.
- Derived child lines from the trusted custom source record for handoff methods.
- Explicit rejection of unknown non-empty top-level fields.
- Explicit rejection of unknown non-empty line fields.
- Positive/non-negative quantity rules by workflow.
- Duplicate line rejection where line identity matters.
- Evidence/note requirements for exception, variance, quarantine, reject, scrap, repair, shortage, or blocked states.
- Safe no-effect response flags for all blocked stock, document, notification, native-route, and valuation behavior.

## 6. Standard Audit Contract

Every write event should preserve enough context to prove what changed without exposing native ERPNext routes or commercial details.

Minimum event fields:

- `action_type`.
- `source_doctype`.
- `source_name`.
- `source_line_id` or line reference text when applicable.
- `target_workflow`.
- `old_state`.
- `new_state`.
- `actor`.
- `actor_role_family`.
- `timestamp`.
- `client_request_id`.
- `payload_hash`.
- `server_validation_result`.
- `note_or_evidence_summary`.

Event rows must stay custom-record-only. They must not create ERPNext comments, communications, timeline entries, notifications, files, or portal-visible records unless a later security review explicitly approves that behavior.

## 7. Standard Native Route And Reference Policy

References remain plain text/status unless a later native-route policy approves otherwise.

Blocked route patterns:

- `/app`
- `/desk/Form`
- `/desk/List`
- `/desk/Report`
- `/desk/query-report`

No Warehouse operation shell or backend response should expose native ERPNext document routes for Purchase Receipt, Delivery Note, Pick List, Sales Return, Credit Note, Purchase Invoice return, Stock Entry, Stock Reconciliation, Stock Ledger, Stock Balance, Stock Reservation, or related accounting documents.

## 8. Standard Blocked Behavior

W15I keeps these blocked across the W15 package:

- Purchase Receipt create/save/submit/cancel/amend/delete.
- Delivery Note create/save/submit/cancel/amend/delete.
- Pick List create/save/submit/cancel/amend/delete.
- Sales Return and Credit Note create/save/submit/cancel/amend/delete.
- Return Delivery Note behavior.
- Purchase Invoice return or debit note behavior.
- Stock Entry create/save/submit/cancel/amend/delete.
- Stock Reconciliation create/save/submit/cancel/amend/delete.
- Stock Ledger and Stock Balance mutation.
- Stock Reservation, reserve, or unreserve behavior.
- Stock movement, stock posting, stock increase, or stock decrease.
- Customer or supplier notification, email, portal, communication, or external action.
- Sales runtime or Procurement runtime changes.
- Valuation/accounting/commercial exposure.

## 9. Standard UI And Smoke Hardening

Every visible planned workflow shell must keep the current safe UI pattern until backend actions are explicitly approved:

- Planned shell cards may expand details.
- Planned controls must be inert `div` or equivalent non-action elements with `aria-disabled="true"`.
- No shell-local `<button>`, `<a>`, `[role=button]`, click handler, `frappe.call`, or `frappe.set_route` for unapproved actions.
- User-facing labels must use request/candidate/posture wording, not execution wording.
- Raw enum keys should not appear in owner-facing UI.
- Smoke tests should assert shell count, planned controls, zero active controls, guardrail text, and no native route exposure.

## 10. W15I1 Readiness Criteria

W15J should not start directly from this governance checkpoint. W15I must first run W15I1 contract setup, gap audit, and safe hardening patches.

Minimum W15I1 audit inputs:

- Current W15 custom record methods have tests for role denial, idempotency, changed payload rejection, cross-source request reuse rejection, forbidden fields, and no-effect payload flags.
- Current W15 metadata tests cover submittability, web indexing, permissions, child-table isolation, forbidden field types, forbidden field names, and native route absence.
- Current W15 UI smokes assert active-control absence for planned shells.
- Static scans cover stock document lifecycle verbs, native routes, valuation/accounting/commercial exposure, notification/email/portal behavior, Sales runtime, and Procurement runtime.
- Owner manual checks exist for visible Warehouse Overview shell behavior.

## 11. Recommended Next Step

Recommendation: `proceed_to_w15i1_review_contracts_and_gap_audit`

W15I1 should define strict Hardening, Security/Stability, and Operations review contracts, then use those contracts to audit W15E/F/G/H implementation gaps before any planned workflow activation.

Do not start W15J release closure, W16 active queue consolidation, Stock Reconciliation draft runtime, Stock Entry draft runtime, Purchase Receipt draft runtime, Delivery Note draft runtime, or any ERPNext document integration until W15I1 and its follow-up gap patches are accepted.

## 12. Boundary Confirmation

W15I is documentation only. It introduces no runtime/backend method, DocType metadata, test, smoke, live file, commit, push, live alignment, restart, protected gate, ERPNext stock document behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, Sales runtime, Procurement runtime, notification/email/portal behavior, or external action.
