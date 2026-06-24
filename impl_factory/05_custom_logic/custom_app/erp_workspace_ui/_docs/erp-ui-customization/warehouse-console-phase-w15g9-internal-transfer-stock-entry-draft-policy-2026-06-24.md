# Warehouse Console Phase W15G9 Internal Transfer Stock Entry Draft Policy

Date: 2026-06-24

Status: docs-only Stock Entry draft policy gate. This document does not implement runtime code, backend methods, DocTypes, tests, smokes, live alignment, commits, pushes, or Stock Entry behavior.

Related baseline:

- W15A Warehouse operations blueprint.
- W15G1 Internal Transfer Workflow Design.
- W15G2 Internal Transfer Candidate overview UI shell.
- W15G3 custom Warehouse Internal Transfer Candidate metadata.
- W15G4 custom Warehouse Internal Transfer Candidate draft backend.
- W15G5 custom Warehouse Internal Transfer Candidate manager decisions.
- W15G6 Internal Transfer Inventory/Admin Handoff Policy.
- W15G7 custom Warehouse Internal Transfer Handoff Request metadata.
- W15G8 request-only Internal Transfer Inventory/Admin handoff backend.

## 1. Title And Scope

W15G9 defines the policy boundary for any future internal-transfer Stock Entry draft phase.

This is a policy gate only. It does not approve Stock Entry draft creation. It does not approve Stock Entry submission. It does not approve stock movement, Stock Ledger mutation, Stock Balance mutation, Stock Reconciliation, Stock Reservation, reserve/unreserve actions, native ERPNext route exposure, valuation/accounting/commercial exposure, Sales runtime changes, Procurement runtime changes, notification behavior, email, portal access, or external actions.

The purpose is to document what must be true before Main Control may even consider a later runtime phase that prepares an unsubmitted Stock Entry draft from a reviewed internal transfer request.

W15G9 must not:

- Create Stock Entry.
- Save Stock Entry.
- Submit Stock Entry.
- Cancel Stock Entry.
- Amend Stock Entry.
- Delete Stock Entry.
- Create or mutate Stock Ledger.
- Create or mutate Stock Balance.
- Create or mutate Stock Reconciliation.
- Create or mutate Stock Reservation.
- Reserve stock.
- Unreserve stock.
- Move stock between warehouses.
- Post stock.
- Expose native Stock Entry routes.
- Expose `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report` native route patterns.
- Expose valuation, accounting, billing, payment, tax, landed cost, margin, profit, rate, amount, price, cost, debit, credit, payable, GL, or commercial fields.
- Update Sales Order, Purchase Order, Delivery Note, Purchase Receipt, Purchase Invoice, Pick List, or Material Request.
- Trigger customer notification.
- Trigger supplier notification.
- Send email.
- Open portal access.
- Change Sales runtime behavior.
- Change Procurement runtime behavior.

## 2. Current W15G State

The current internal-transfer workflow is bounded to custom Warehouse evidence, manager posture, and request-only Inventory/Admin handoff.

Current state:

- W15G4 saves custom `Warehouse Internal Transfer Candidate` draft evidence.
- W15G5 saves custom manager decisions on the candidate.
- W15G8 creates custom `Warehouse Internal Transfer Handoff Request` records.
- W15G8 writes only custom request parent, line, and event rows.
- W15G8 does not create Stock Entry drafts.
- W15G8 does not submit Stock Entry.
- W15G8 does not post stock.
- W15G8 does not expose native ERPNext routes.
- W15G8 keeps valuation hidden and stock-effect flags false.

The current approved endpoint is request-only handoff. Any Stock Entry draft is a future decision, not a current capability.

## 3. Business Flow In Plain English

Internal transfer governance has three separate stages.

Warehouse evidence stage:

- Warehouse records source warehouse, target warehouse, item, requested quantity, counted quantity, candidate quantity, condition, reason, and evidence.
- Warehouse Manager or Stock Manager reviews the physical evidence.
- The result is a transfer candidate or exception posture only.

Inventory/Admin review stage:

- Inventory/Admin reviews whether a stock document path is allowed.
- Inventory/Admin reviews source/target warehouse policy, serial/batch scope, quarantine restrictions, reservation policy, and native-submit containment.
- The result may be a decision to reject, close, request more evidence, or prepare a future unsubmitted draft under explicit policy.

ERPNext stock document stage:

- ERPNext Stock Entry draft creation, review, submit, cancel, amend, and posting are separate high-risk lifecycle actions.
- Stock posting affects stock ledger and stock balance.
- This stage must remain outside Warehouse until owner/security approval exists.

W15G9 governs only the policy between the second and third stages. It does not start the third stage.

## 4. Recommended Default

Default recommendation: keep Stock Entry draft creation blocked.

If the owner later approves a draft phase, the safest default is Inventory/Admin-owned preparation of an unsubmitted draft only. Warehouse should request review and provide evidence, but Warehouse should not directly create, open, submit, cancel, amend, or post Stock Entry.

Recommended default ownership:

- Warehouse User: no Stock Entry draft rights from Warehouse Console.
- Stock User: no Stock Entry draft rights from Warehouse Console.
- Warehouse Manager: may request policy review only.
- Stock Manager: may request policy review only unless owner explicitly grants draft preparation.
- Inventory/Admin or System Manager: owns future draft governance.
- ERPNext native Stock Entry submit remains outside Warehouse Console.

Rejected default:

- Direct Warehouse Stock Entry creation or submission from Warehouse Console.
- Native Stock Entry route links for Warehouse users.
- Warehouse-visible valuation/accounting fields.
- Auto-posting or background Stock Entry submission.

## 5. Future Draft Eligibility

A future Stock Entry draft phase must require all of the following before draft creation is considered:

- Existing custom `Warehouse Internal Transfer Handoff Request`.
- Handoff status must be explicitly approved by Inventory/Admin in a future phase, not merely `Requested`.
- Handoff type must be `transfer_execution_review` or another owner-approved stock-document policy type.
- Source candidate must be manager reviewed.
- Source warehouse and target warehouse must be visible and different.
- Source and target warehouse pair must be allowed by policy.
- Candidate lines must be derived from the custom handoff request or source candidate, not arbitrary client rows.
- Transfer candidate quantity must be greater than zero.
- Requested, counted, and candidate quantities must be internally consistent.
- Blocked, damaged, quarantine, and short quantities must be resolved or explicitly excluded.
- Serial/batch policy must be resolved for serial/batch items.
- Reservation policy must be resolved without creating reservations from Warehouse Console unless separately approved.
- Evidence reference and manager event must exist.
- Inventory/Admin approval reference must exist.
- Idempotency request id must exist.
- Source payload hash must be stable.
- Draft creation must return false stock-posting flags.

Draft eligibility must be deny-by-default. Missing evidence, unresolved policy, unexpected fields, invalid warehouse context, or native-route requirements must block draft creation.

## 6. Exclusion Rules

The following must exclude a line or request from any future Stock Entry draft:

- Unreviewed candidate.
- Request-only handoff without Inventory/Admin approval.
- Source warehouse equals target warehouse.
- Source or target warehouse not visible.
- Candidate quantity is zero or negative.
- Candidate quantity exceeds requested quantity.
- Candidate quantity exceeds counted quantity.
- Damaged quantity unresolved.
- Quarantine quantity unresolved.
- Blocked quantity unresolved.
- Short quantity unresolved without explicit policy.
- Serial number requirement unresolved.
- Batch requirement unresolved.
- Source warehouse restriction unresolved.
- Target warehouse restriction unresolved.
- Native route link required to proceed.
- Valuation, accounting, commercial, rate, amount, tax, GL, cost, margin, profit, debit, credit, payable, payment, billing, landed cost, or price fields required to proceed.
- Client supplies arbitrary Stock Entry rows instead of server-derived lines.
- Request id reused with changed payload.
- Request id reused across another handoff request.

Excluded quantities must not be silently drafted. They must remain in custom evidence/status records for Inventory/Admin review.

## 7. Draft Behavior If Later Approved

If a later phase approves Stock Entry draft creation, that phase must still be limited to an unsubmitted draft.

Allowed only after later approval:

- Prepare one unsubmitted Stock Entry draft for internal material transfer.
- Use server-derived rows from the approved custom handoff request.
- Preserve source and target warehouse context.
- Preserve item, UOM, and approved transfer quantity.
- Store safe custom reference text back to custom request records.
- Return safe status flags showing no stock posted.

Still blocked even in a draft phase unless separately approved:

- Stock Entry submit.
- Stock Entry cancel.
- Stock Entry amend.
- Stock Entry delete.
- Stock posting.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reconciliation.
- Stock Reservation.
- Reserve/unreserve.
- Native route exposure to Warehouse users.
- Valuation/accounting/commercial payload exposure.
- Background jobs that submit or post stock.

The future draft method must not call submit, cancel, amend, delete, enqueue-post, reserve, unreserve, reconcile, or stock-posting routines.

## 8. Native Submit Bypass Containment

Native-submit bypass containment is mandatory before any runtime draft phase.

Owner/security must decide:

- Who can open a generated Stock Entry draft in native ERPNext.
- Whether Warehouse users can see only a plain text draft reference.
- Whether Stock Manager can open a native draft or only Inventory/Admin can.
- Whether draft submit is technically blocked for Warehouse roles.
- Whether native submit requires a separate Inventory/Admin role.
- Whether draft references are never clickable in Warehouse UI.
- Whether generated drafts carry custom metadata or naming policy.
- Whether native form permissions prevent accidental submit/cancel/amend.
- Whether post-submit status can be reflected back to Warehouse as read-only text.

Default recommendation:

- Warehouse sees plain text/status only.
- Warehouse does not receive native Stock Entry links.
- Inventory/Admin owns native draft access.
- Submit remains outside Warehouse Console.

## 9. Role Ownership

Warehouse ownership:

- Physical transfer evidence.
- Count and condition posture.
- Manager recommendation.
- Request-only handoff.

Inventory/Admin ownership:

- Stock document policy.
- Warehouse pair policy.
- Serial/batch policy.
- Reservation policy.
- Native-submit containment.
- Future Stock Entry draft governance.
- Future Stock Entry submit governance.

System/Admin ownership:

- Permission model.
- Native form containment.
- Protected gates.
- Audit and rollback policy.

Sales and Procurement ownership:

- No normal ownership in internal transfer Stock Entry draft policy.
- Sales is involved only if internal transfer affects a customer promise or dispatch commitment.
- Procurement is involved only if the transfer relates to receiving dispute, supplier return, or supplier-owned correction.

## 10. Reference Visibility Policy

Until native route containment is approved, all references shown in Warehouse UI must be inert text/status only.

Allowed:

- `Stock Entry draft requested`.
- `Inventory/Admin review pending`.
- `Draft reference: STE-...` as plain text only after later approval.
- `No stock posted`.
- `No Stock Ledger update`.

Blocked:

- Clickable Stock Entry links.
- `/app/stock-entry/...`.
- `/desk/Form/Stock Entry/...`.
- `/desk/List/Stock Entry`.
- `/desk/Report/...`.
- `/desk/query-report/...`.
- Buttons that open native Stock Entry.
- Hidden anchors or role-button elements that navigate to native Stock Entry.

## 11. Payload And Custom Record Safety

Future runtime payloads and custom records must keep safe flags explicit.

Required false flags:

- `stock_effect: false` until submit/posting actually occurs outside Warehouse.
- `stock_moved: false`.
- `stock_entry_created: false` before draft phase approval.
- `stock_entry_submitted: false`.
- `stock_posted: false`.
- `stock_reservation_created: false`.
- `stock_ledger_updated: false`.
- `stock_balance_updated: false`.
- `stock_reconciliation_created: false`.

Required hidden object:

- `valuation: { visible: false, fields: [] }`.

Forbidden payload/custom-record fields:

- Valuation rate.
- Stock value.
- Rate.
- Amount.
- Base amount.
- Tax.
- Account.
- GL Entry.
- Payable.
- Payment.
- Billing.
- Landed cost.
- Margin.
- Profit.
- Cost.
- Debit.
- Credit.
- Price.
- Commercial terms.

## 12. Audit And Idempotency

Any future draft phase must include audit and idempotency.

Minimum audit:

- Source handoff request id.
- Source candidate id.
- Inventory/Admin approval reference.
- Request id.
- Actor.
- Timestamp.
- Policy version.
- Source payload hash.
- Line count.
- Total draft candidate quantity.
- Draft result status.
- Safe no-stock-posted flags.

Minimum idempotency:

- Same request id and same source payload returns the same result.
- Same request id with changed payload rejects.
- Same request id reused across another handoff request rejects.
- Source changes after draft request must require a new request id or explicit review.

## 13. Open Owner Decisions Before Runtime

Before any Stock Entry draft runtime phase, owner/security must resolve:

- Whether Stock Entry drafts are allowed at all from Warehouse-related workflow.
- Whether draft preparation is Inventory/Admin-only or can be requested by Stock Manager.
- Which handoff statuses can become draft-ready.
- Whether a separate Inventory/Admin approval state is required before draft creation.
- Whether Stock Manager can see draft reference text.
- Whether Warehouse Manager can see draft reference text.
- Whether any native Stock Entry route can ever be exposed.
- How native submit/cancel/amend bypass is contained.
- Whether serial/batch items are in scope.
- Whether quarantine or restricted stock can ever be drafted.
- Whether reservation is ever allowed.
- Whether draft creation must validate projected availability.
- Whether partial transfer drafting is allowed.
- Who closes rejected or cancelled draft requests.
- Which protected gates are mandatory before live alignment.

Default recommendation:

- Keep draft creation blocked until these decisions are resolved.
- Keep Stock Entry submit outside Warehouse Console.
- Keep native links blocked.
- Keep valuation/accounting/commercial fields hidden.
- Keep draft behavior Inventory/Admin-owned.

## 14. Future Implementation Test Requirements

Any future draft runtime phase must include tests proving:

- Warehouse User cannot create Stock Entry draft.
- Stock User cannot create Stock Entry draft unless explicitly approved.
- Warehouse Manager cannot submit Stock Entry.
- Stock Manager cannot submit Stock Entry unless explicitly approved outside Warehouse Console.
- Inventory/Admin approval is required.
- Source is a custom `Warehouse Internal Transfer Handoff Request`.
- Source state is draft-ready only after approved policy.
- Lines are server-derived from custom request/candidate records.
- Client-supplied Stock Entry rows are rejected.
- Source and target warehouses are visible and different.
- Invalid warehouse pair rejects.
- Unresolved damaged/quarantine/blocked/short quantities reject or are excluded by policy.
- Serial/batch unresolved lines reject.
- Request id is required.
- Idempotency returns existing result for the same payload.
- Changed payload with same request id rejects.
- Cross-request source reuse is controlled.
- No Stock Entry submit occurs.
- No Stock Ledger mutation occurs before submit.
- No Stock Balance mutation occurs before submit.
- No Stock Reconciliation occurs.
- No Stock Reservation occurs unless separately approved.
- No native route is returned to Warehouse users.
- Valuation/accounting/commercial fields remain hidden.
- Sales and Procurement runtime boundaries remain clean.
- No notification, email, portal, or external action occurs.

## 15. Acceptance Criteria For W15G9

W15G9 is acceptable when:

- It remains docs-only.
- It does not approve Stock Entry draft runtime.
- It does not approve Stock Entry submit.
- It defines future draft eligibility, exclusion rules, ownership, native-submit containment, reference visibility, audit, idempotency, and test requirements.
- It keeps Stock Entry lifecycle actions blocked.
- It keeps Stock Ledger, Stock Balance, Stock Reconciliation, and Stock Reservation mutation blocked.
- It keeps native routes blocked.
- It keeps valuation/accounting/commercial exposure blocked.
- It keeps Sales/Procurement runtime changes blocked.
- It updates README roadmap/status only.

## 16. Final Boundary Statement

W15G9 is only a policy artifact for possible future internal-transfer Stock Entry draft governance.

No Stock Entry draft is created. No Stock Entry is saved, submitted, cancelled, amended, or deleted. No stock moves. No stock posts. No Stock Ledger, Stock Balance, Stock Reconciliation, or Stock Reservation mutation is approved. No native ERPNext route exposure is approved. No valuation/accounting/commercial exposure is approved. No Sales or Procurement runtime change is approved. No notification, email, portal, or external action is approved.
