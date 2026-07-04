# Warehouse Console Phase W16D1 - Returns Work Hub Activation Contract

Date: 2026-07-01
Status: Docs-only activation contract for W16D. No runtime implementation in this phase.
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder for internal preflight; separate review agents required for major runtime activation.

## 1. Purpose

W16B activated inbound receiving custom workflow behavior. W16C activated outbound picking custom workflow behavior. W16D starts the returns workstream so the Warehouse Overview does not continue showing return work as `Planned` or `Shell only`.

W16D1 defines the activation contract before code is changed. It decides what the owner should see, what the UI may call, which roles own each action, and what must remain blocked.

W16D1 does not implement runtime behavior and does not close the Warehouse workspace.

## 2. Current State

The Warehouse Overview currently has return-related planned content:

- Action Center `Return intake` planned card.
- Action Center `Return decisions` planned card.
- `Customer return intake` planned workflow shell.
- `Supplier return candidate` planned workflow shell.

The backend foundation already exists and has been hardened through W15E, W15F, W15I, and W16 validation patterns.

Customer return custom-record methods:

- `save_warehouse_customer_return_intake_draft`
- `save_warehouse_customer_return_manager_decision`
- `request_warehouse_customer_return_handoff`

Supplier return custom-record methods:

- `save_warehouse_supplier_return_candidate_draft`
- `save_warehouse_supplier_return_manager_decision`
- `request_warehouse_supplier_return_handoff`

These methods are custom Warehouse workflow methods only. They do not create ERPNext stock, sales, purchasing, accounting, notification, or native-route behavior.

## 3. Target Owner Experience

W16D should replace the planned return shells with an active `Returns work hub`.

Recommended structure:

- One Overview entry point named `Returns work hub`.
- Two lanes inside the hub:
  - `Customer returns`
  - `Supplier returns`
- A compact manager queue inside the hub for `Return decisions`.
- Request-only handoff panels for Sales/Finance/Admin and Procurement/Finance/Admin.

Why one hub instead of separate top-level pages:

- Customer and supplier returns share a warehouse evidence pattern: source reference, warehouse, item, quantity, condition, evidence, manager posture, and request-only handoff.
- A single hub keeps Overview compact and avoids adding too many top-level cards.
- Separate lanes inside the hub still preserve business ownership: Sales/Finance for customer returns, Procurement/Finance for supplier returns.

## 4. W16D Implementation Sequence

### W16D2 - Returns Hub UI Foundation

Goal: add an owner-facing Returns hub entry point without activating all writes at once.

Scope:

- Replace the Overview planned `Return intake` and `Return decisions` cards with an active Returns hub entry point.
- Keep Customer Return and Supplier Return lanes visible inside the hub.
- Show current custom workflow status summaries if records exist.
- Keep all write controls disabled until W16D3/W16D4 unless a narrow save action is explicitly implemented.
- Add smoke coverage proving the old planned-shell labels are removed or downgraded appropriately.

Allowed behavior:

- Navigation inside Warehouse Console custom UI only.
- Read custom return workflow summaries.
- Show policy guardrails.

Blocked behavior:

- No ERPNext document routes.
- No Sales/Procurement/Finance/Admin runtime mutation.
- No stock movement, accounting, notification, or external action.

### W16D3 - Customer Return Intake Activation

Goal: make Customer Return intake usable as a custom Warehouse workflow.

Allowed UI actions:

- Record customer return source/reference text.
- Record target warehouse.
- Record item lines with returned quantity, accepted quantity, damaged quantity, quarantine quantity, condition grade, evidence reference, and notes supported by the existing backend contract.
- Save draft using `save_warehouse_customer_return_intake_draft`.
- Show saved custom intake status and no-effect flags.
- Show manager-only actions disabled for non-manager roles.

Manager-only actions:

- Request reinspection.
- Mark restock candidate.
- Mark quarantine review.
- Mark repair review.
- Mark scrap candidate.
- Reject return intake.
- Escalate to Sales.

Allowed manager method:

- `save_warehouse_customer_return_manager_decision`

Allowed handoff method after valid reviewed source state:

- `request_warehouse_customer_return_handoff`

Business labels to use:

- `Customer return intake`
- `Return evidence`
- `Manager disposition posture`
- `Sales/Admin handoff request`
- `Finance/Admin handoff request`
- `Request only`
- `No stock increased`
- `No ERP document created`

Forbidden labels:

- `Approve return`
- `Create Sales Return`
- `Create Credit Note`
- `Receive returned stock`
- `Post return`
- `Refund customer`
- `Notify customer`

### W16D4 - Supplier Return Candidate Activation

Goal: make Supplier Return candidate flow usable as a custom Warehouse workflow.

Allowed UI actions:

- Record supplier/source reference text.
- Record warehouse.
- Record item lines with candidate quantity, quarantine quantity, damaged quantity, overage quantity, quality hold quantity, condition grade, evidence reference, and notes supported by the existing backend contract.
- Save draft using `save_warehouse_supplier_return_candidate_draft`.
- Show saved custom candidate status and no-effect flags.
- Show manager-only actions disabled for non-manager roles.

Manager-only actions:

- Request reinspection.
- Mark quarantine review.
- Mark supplier-return candidate.
- Escalate to Procurement.
- Escalate to Finance/Admin.
- Reject supplier-return candidate.

Allowed manager method:

- `save_warehouse_supplier_return_manager_decision`

Allowed handoff method after valid reviewed source state:

- `request_warehouse_supplier_return_handoff`

Business labels to use:

- `Supplier return candidate`
- `Supplier-return evidence`
- `Manager return posture`
- `Procurement/Admin handoff request`
- `Finance/Admin handoff request`
- `Request only`
- `No supplier notified`
- `No stock decreased`
- `No ERP document created`

Forbidden labels:

- `Approve supplier return`
- `Return Purchase Receipt`
- `Create debit note`
- `Create Purchase Invoice return`
- `Send to supplier`
- `Notify supplier`
- `Decrease stock`
- `Post supplier return`

### W16D5 - Returns Decision Queue And Manual Review

Goal: make manager return work visible and usable without creating ERP documents.

Scope:

- Show customer return intakes needing manager posture.
- Show supplier return candidates needing manager posture.
- Show request-only handoff records after manager review.
- Keep final handoff actions as custom request/status records only.
- Run owner/manual UI acceptance for Returns hub layout, labels, action states, saved-record behavior, and role gating.

### W16D6 - Returns Work Hub Closure

Goal: close W16D only after return planned states are burned down.

Closure bar:

- Overview no longer shows return intake/decision work as unresolved `Planned` or `Shell only`.
- Customer returns can save custom intake evidence and manager posture.
- Supplier returns can save custom candidate evidence and manager posture.
- Handoff requests remain request-only custom records.
- Non-manager users cannot access active manager actions.
- Tests and smoke coverage prove custom method calls only.
- Owner manually accepts live return workflow behavior.

## 5. Role Ownership

Warehouse User / Stock User:

- May record physical return evidence into custom records only.
- May not make manager disposition decisions.
- May not request Sales, Procurement, Finance/Admin, or external document action directly.

Warehouse Manager / Stock Manager / System Manager:

- May record manager posture on custom return records.
- May request handoff records after source-state rules are satisfied.
- May not create ERPNext stock, sales, purchasing, accounting, or notification documents from Warehouse Console.

Sales / Finance/Admin:

- Own customer-facing authorization, replacement, refund, credit, write-off, and document governance.
- W16D must not mutate their runtime records.

Procurement / Finance/Admin:

- Own supplier communication, claim, debit, payable, return purchase document, and document governance.
- W16D must not mutate their runtime records.

## 6. Required UI Contract

All active controls must be explicit about custom-record-only behavior.

Required visible guardrails:

- Customer return: `No stock is increased and no Sales Return or Credit Note is created from this workflow.`
- Supplier return: `No supplier is notified, no stock is decreased, and no return Purchase Receipt or debit note is created from this workflow.`
- Handoff panels: `Request only` and `No ERP document created`.

Required status language:

- Use `candidate`, `intake`, `posture`, `request`, `review`, and `handoff request`.
- Avoid `approve`, `post`, `submit`, `create document`, `notify`, `refund`, `debit`, or `stock update` unless the sentence explicitly says the behavior is blocked.

Required interaction behavior:

- Active Warehouse user save buttons must say `Save evidence` or `Save draft` with a small custom-record note.
- Manager actions must show `Manager only` disabled state for non-manager roles.
- Handoff actions must show `Request only` context.
- Any success toast must say a custom Warehouse record was saved, not an ERP document.

Forbidden implementation shortcuts:

- Do not reuse Sales Console return queue keys such as `sales_returns_in_progress` for Warehouse returns.
- Do not reuse Procurement native `new_doc` / document-creation patterns for Warehouse returns.
- Do not create return workflows by linking to native ERPNext Sales Return, Credit Note, Delivery Note, Purchase Receipt, Purchase Invoice, Stock Entry, or Stock Reconciliation forms.
- Do not expose read-only native document links until a later phase explicitly approves native-reference visibility.

## 7. Backend Boundary Contract

Allowed write targets:

- `Warehouse Customer Return Intake`
- `Warehouse Customer Return Intake Line`
- `Warehouse Customer Return Intake Event`
- `Warehouse Customer Return Handoff Request`
- `Warehouse Customer Return Handoff Request Line`
- `Warehouse Customer Return Handoff Request Event`
- `Warehouse Supplier Return Candidate`
- `Warehouse Supplier Return Candidate Line`
- `Warehouse Supplier Return Candidate Event`
- `Warehouse Supplier Return Handoff Request`
- `Warehouse Supplier Return Handoff Request Line`
- `Warehouse Supplier Return Handoff Request Event`

Forbidden write targets and side effects:

- Sales Return
- Credit Note
- Return Delivery Note
- Purchase Receipt return
- Purchase Invoice return
- Debit Note
- Stock Entry
- Stock Ledger
- Stock Balance
- Stock Reconciliation
- Stock Reservation
- Sales Order update
- Purchase Order update
- Customer notification
- Supplier notification
- Email
- Portal action
- External action
- Native ERPNext route exposure
- Valuation, accounting, commercial, payment, receivable, payable, GL, tax, landed cost, price, margin, or billing fields

## 8. Required Test And Smoke Coverage

For each runtime activation phase, tests must cover:

- Warehouse/Stock user evidence save allowed.
- Non-warehouse user evidence save denied.
- Manager roles can record manager posture.
- Warehouse/Stock user manager actions denied.
- Unknown decision rejected.
- Invalid source/final status rejected.
- Required notes/references enforced by decision/handoff type.
- Idempotent same request accepted.
- Changed payload with same request rejected.
- Request-id reuse across source records rejected.
- Forbidden top-level and line fields rejected.
- Payload no-effect flags remain false for stock/accounting/native/notification behavior.

Smoke coverage must prove:

- Returns hub is visible.
- Old planned shell labels are removed or no longer the primary owner action.
- Active controls call only allowed custom methods.
- Manager controls are disabled for non-manager context.
- No native route strings are exposed.
- Guardrail text is visible.

## 9. Live Alignment Policy

Runtime activation phases require live alignment only after source validation and owner approval.

Before live alignment:

- Run source validation in design workspace.
- Run Hybrid Review Ladder internal preflight.
- Resolve blocker/high/medium findings.
- Ask owner before live alignment if visible UI behavior changes.

After live alignment:

- Verify served assets when JS changes.
- Reload affected Page doctypes if page wrapper files change.
- Clear Frappe cache and website cache.
- Ask owner for manual live UI check.

## 10. W16D1 Decision

Proceed to W16D2 only after this contract is accepted.

Recommended W16D2 scope: create the Returns hub foundation and convert Overview return entry points from planned shells into an active custom workflow hub shell, while keeping writes limited or disabled until the customer/supplier runtime phases are implemented.

## 11. Boundary Confirmation

W16D1 is docs-only. It does not implement, stage, commit, push, live-align, restart, activate runtime, create ERPNext documents, mutate stock/accounting records, expose native routes, send notifications, or approve full Warehouse Workspace Closure.
