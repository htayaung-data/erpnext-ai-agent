# Warehouse Console Phase W15A Operations Blueprint

Date: 2026-06-16

Decision: `blueprint_only_ready_for_owner_review`

Scope: documentation only. W15A does not implement runtime UI, backend methods, database models, routes, smokes, fixtures, package scripts, live alignment, protected gates, or stock actions.

## 1. Active Plan

W15 is the active Warehouse operations track after Phase 0.

W14 planning files are retained as historical input only. Future agents should not continue W14 phase naming unless Main Control explicitly reopens it.

Active sequence:

1. Phase 0: Quick Find/sidebar cleanup and Manager Readiness removal.
2. W15A: Full Warehouse operations blueprint, no code.
3. W15B: Action Center shell and work-entry foundation, no stock mutation.
4. W15C: Inbound receiving workflow.
5. W15D: Outbound picking and dispatch workflow.
6. W15E: Customer return workflow.
7. W15F: Supplier return workflow.
8. W15G: Internal transfer workflow.
9. W15H: Cycle count and variance workflow.
10. W15I: Manager approval, role, audit, and hardening.
11. W15J: Final protected gates, live validation, and release closure.

## 2. Core Principle

Warehouse Console should have three layers.

### Visibility Layer

The existing read-only layer:

- Overview.
- Inbound Receiving Queue.
- Outbound Picking Queue.
- Stock Exceptions.
- Stock Posture Review.
- Movement Visibility.
- Transfer Visibility.
- Review/detail pages.

Purpose:

- Show what exists.
- Explain current posture.
- Route users to custom Warehouse pages.
- Avoid native ERPNext escape.
- Avoid stock mutation.

### Task Layer

Warehouse users perform operational work:

- Arrival check.
- Count received quantity.
- Pick task.
- Pack/dispatch handoff.
- Return intake.
- Supplier return preparation.
- Transfer request.
- Cycle count.
- Discrepancy report.

Purpose:

- Capture operational evidence.
- Prepare work for manager review.
- Keep work auditable.
- Avoid silent ERPNext document mutation.

### Manager Control Layer

Warehouse managers make decisions:

- Approve clean arrivals.
- Resolve receiving discrepancies.
- Release picking or partial fulfillment.
- Authorize return handling.
- Approve transfer requests.
- Approve cycle count variance.
- Decide quarantine, restock, repair, scrap, or supplier follow-up.
- Monitor accountability.

Purpose:

- Put approval where operational risk exists.
- Keep ERPNext stock documents as the system of record.
- Ensure no stock posting happens without explicit review and protected gates.

## 3. System Of Record Rule

ERPNext stock documents remain the system of record.

Warehouse Console should guide, collect evidence, control decisions, and prepare drafts only when a future write phase explicitly approves that behavior.

Warehouse Console must not silently mutate:

- Purchase Receipt.
- Delivery Note.
- Pick List.
- Stock Entry.
- Stock Reconciliation.
- Stock Reservation.
- Serial and Batch Bundle.
- Purchase Order.
- Sales Order.
- Purchase Invoice or Sales Invoice.
- Valuation, GL, accounting, price, tax, margin, billing, or payment fields.

## 4. Current Warehouse Pages

The left sidebar has six visible entries:

- Overview.
- Inbound Receiving.
- Outbound Picking.
- Stock Exceptions.
- Movement Visibility.
- Transfer Visibility.

Additional custom Warehouse routes exist as child/detail pages:

- Receiving Review: `/desk/warehouse-console-receiving/<purchase-order>`.
- Picking Review: `/desk/warehouse-console-picking/<sales-order>`.
- Stock Exception Review: `/desk/warehouse-console-stock-exception/<encoded-context>`.
- Stock Posture Review: `/desk/warehouse-console-stock-posture/<encoded-context>`.
- Movement Review: `/desk/warehouse-console-movement/<encoded-context>`.

W15 should not add many new top-level sidebar pages. Prefer:

- Existing queue as daily entry.
- Existing review page as object context.
- Future Action Center as manager/user task entry.
- Workflow-specific panels inside the relevant custom page.

## 5. Phase 0 Baseline

Completed:

- Quick Find moved out of Overview.
- Search exists as the shared left-sidebar helper.
- Manager Readiness removed from Overview.
- Search routes only to custom Warehouse pages.
- No native ERPNext result target.
- No stock mutation.

Implication:

- Do not re-add a Quick Find block in the Overview content.
- Do not re-add the duplicated Overview Manager Readiness component.
- Manager decisions should appear in the Action Center and workflow pages.

## 6. Daily Business Flow In Plain English

### Inbound Supplier Delivery

1. Procurement creates and manages a Purchase Order.
2. Warehouse sees expected supplier stock in Inbound Receiving.
3. Warehouse waits for the physical delivery.
4. When goods arrive, Warehouse checks item, quantity, warehouse, and condition.
5. If clear, Warehouse submits the arrival evidence for manager review.
6. If there is a problem, Warehouse reports shortage, overage, damage, wrong item, missing warehouse, or quality concern.
7. Manager approves clean arrival, sends back for recount, marks quality/quarantine, or sends Procurement follow-up.
8. Purchase Receipt draft/submit remains a later governed phase.

### Outbound Customer Delivery

1. Sales creates and manages Sales Orders and customer commitments.
2. Warehouse sees open demand in Outbound Picking.
3. Warehouse checks stock availability and starts picking only after the workflow allows it.
4. User records picked quantity, shortage, damage, or readiness for pack/dispatch.
5. Manager releases, resolves shortage, or approves partial fulfillment.
6. Delivery Note draft/submit remains a later governed phase.
7. Sales owns customer communication and delivery promise changes.

### Customer Return

1. Customer return request or returned goods appear from Sales/customer process when available.
2. Warehouse receives returned item physically.
3. Warehouse inspects condition.
4. Manager decides restock, quarantine, repair, scrap, or Sales follow-up.
5. Return Delivery Note, stock movement, or adjustment remains a later governed phase.

### Supplier Return

1. Warehouse identifies damaged/wrong/extra supplier stock or Procurement initiates a supplier return need.
2. Warehouse prepares return evidence and item condition.
3. Manager reviews and approves supplier return readiness.
4. Procurement owns supplier communication.
5. Return Purchase Receipt or stock movement remains a later governed phase.

### Internal Transfer

1. A warehouse needs stock from another warehouse.
2. User requests transfer with item, source, target, quantity, and reason.
3. Manager approves or rejects.
4. Source warehouse picks and dispatches.
5. Target warehouse receives.
6. Stock Entry Material Transfer remains the ERPNext system record and is only prepared/posted in a later governed phase.

### Cycle Count And Variance

1. Manager or system assigns item/location count.
2. Warehouse user counts physical stock.
3. User submits counted quantity and evidence.
4. Manager reviews variance.
5. Manager approves recount, accepts variance, or escalates.
6. Stock Reconciliation remains a later governed phase.

### Stock Exception Resolution

1. Stock Exceptions shows shortage, missing posture, inbound cover, or demand risk.
2. User opens the exception and related posture pages.
3. Manager decides whether to resolve by Procurement follow-up, Sales follow-up, transfer request, cycle count, replenishment signal, or receiving/picking action.
4. No automatic document creation happens from an exception.

## 7. Workflow Matrix

| Workflow | Entry page | User task | Manager decision | ERPNext system document | First W15 mode | Forbidden until later |
| --- | --- | --- | --- | --- | --- | --- |
| Inbound receiving | Inbound Queue, Receiving Review | Arrival check, count, discrepancy note | Approve arrival readiness, recount, quarantine, Procurement follow-up | Purchase Receipt | Internal readiness record only | Create/submit Purchase Receipt |
| Outbound picking | Outbound Queue, Picking Review | Start pick, mark picked qty, report shortage/damage | Release pick, partial fulfillment, shortage resolution | Pick List, Delivery Note, Stock Reservation | Task shell and readiness record only | Reserve, create/submit Pick List or Delivery Note |
| Customer return | Future Action Center, return review | Return intake, condition check | Restock, quarantine, repair, scrap, Sales follow-up | Return Delivery Note, Stock Entry, Sales return docs | Intake/readiness record only | Post return stock movement |
| Supplier return | Action Center, receiving/stock exception context | Prepare supplier return evidence | Approve return, Procurement follow-up | Return Purchase Receipt, Stock Entry | Request/readiness record only | Supplier communication or stock posting |
| Internal transfer | Transfer Visibility, Action Center | Transfer request, source pick, target receive evidence | Approve/reject transfer, resolve shortage | Stock Entry Material Transfer | Request/readiness record only | Create/submit Stock Entry |
| Cycle count | Action Center, Stock Posture | Count item/location, submit variance | Approve variance, reject/recount | Stock Reconciliation | Count task and variance review only | Create/submit Stock Reconciliation |
| Stock exception | Stock Exceptions, Stock Exception Review | Inspect exception and related context | Choose resolution path | Depends on resolution | Manager resolution shell only | Automatic write from exception |

## 8. Role Matrix

| Capability | Warehouse User | Warehouse Manager | Procurement | Sales | System/Admin |
| --- | --- | --- | --- | --- | --- |
| View Warehouse queues | Yes | Yes | If role grants Warehouse access | If role grants Warehouse access | Yes |
| Sidebar Search | Role-scoped custom Warehouse results | Role-scoped custom Warehouse results | No Warehouse-only expansion unless role grants | No Warehouse-only expansion unless role grants | Yes |
| Arrival check | Yes | Yes | Review signal only | No | Configure |
| Receiving approval | No | Yes, after phase approval | Procurement follow-up owner | No | Configure |
| Purchase Receipt draft | No | Later, only if approved | Procurement aware, not owner of Warehouse action | No | Configure/gate |
| Pick task | Yes | Yes | No | Sales owns customer promise | Configure |
| Delivery release | No | Later, only if approved | No | Sales communication owner | Configure/gate |
| Customer return intake | Yes | Yes | No | Sales owns customer process | Configure |
| Supplier return request | Prepare evidence | Approve readiness | Supplier communication owner | No | Configure |
| Transfer request | Yes | Approve | No | No | Configure |
| Cycle count | Count assigned work | Approve/reject variance | No | No | Configure |
| Stock adjustment | No | Later, only if approved | No | No | Configure/gate |
| Valuation/accounting | No | No in Warehouse Console | No through Warehouse | No through Warehouse | Native ERP only |

## 9A. Common Warehouse Task State Model

Before W15B adds any Action Center shell, W15A must define a common task model that every later workflow can reuse.

Recommended task states:

- `draft`: task exists but is not ready for user work.
- `assigned`: task is assigned to a warehouse user or team.
- `in_progress`: user has started operational work.
- `submitted_for_review`: user completed evidence capture and sent it to manager.
- `sent_back`: manager returned the task for recount, repick, correction, or more evidence.
- `approved`: manager approved the readiness decision.
- `rejected`: manager rejected the task or request.
- `cancelled`: task is voided and no further action is expected.
- `converted_to_erpnext_draft`: a later approved write phase prepared an ERPNext draft document from the task.
- `closed`: workflow is completed without further action.

Minimum shared task fields:

- task_type.
- source_doctype.
- source_name.
- source_line_id or source_line_ids.
- item_code when line-specific.
- warehouse or source/target warehouse when applicable.
- assigned_to.
- assigned_role_family.
- priority.
- due_at.
- task_state.
- exception_codes.
- evidence_summary.
- manager_decision.
- created_by and created_at.
- updated_by and updated_at.
- submitted_by and submitted_at.
- reviewed_by and reviewed_at.
- client_request_id.
- idempotency_key.

Rules:

- W15B may show shell cards for these task states, but must not create tasks unless a later phase explicitly approves the storage model.
- Every future workflow should reuse the same state vocabulary so the Action Center does not become a set of unrelated one-off queues.
- ERPNext document creation is not a task state until a later write-governance phase approves the exact document and server contract.

## 9B. Policy-Based Approval Matrix

Do not require manager approval for every harmless future step forever. That would make the console slow and unrealistic.

Manager approval must be mandatory for:

- Receiving discrepancy: shortage, overage, damage, wrong item, missing warehouse, unclear supplier paperwork.
- Quality/quarantine decision.
- Serial, batch, expiry, or controlled-item case.
- Supplier return.
- Customer return condition decision.
- Partial fulfillment or shortage release.
- Transfer request above configured threshold.
- Cycle count variance above configured threshold.
- Stock adjustment request.
- Any conversion into ERPNext draft stock document.
- Any future submit/post action.

Manager approval may be optional or policy-driven for:

- Clean arrival check with no discrepancy.
- Clean pick task with full picked quantity.
- Low-risk transfer request below configured threshold.
- Cycle count with zero variance.

Policy dimensions to define before runtime:

- company.
- warehouse.
- item group.
- item controlled flag: serial, batch, expiry, quality inspection required.
- quantity threshold.
- variance threshold.
- return condition.
- role.
- document status.

W15B should show policy placeholders only. Policy execution belongs to later workflow phases.

## 9C. Inbound Putaway And Quality Staging

Inbound receiving should not be modeled as only arrived to final stock.

Industry-standard receiving often separates:

- Dock/input area.
- Quality inspection or quarantine area.
- Final stock/bin location.

W15C should therefore distinguish:

- arrival check: goods physically arrived;
- inspection/quarantine: goods need quality or damage decision;
- putaway readiness: goods can move to final warehouse/bin after acceptance;
- Purchase Receipt posting: ERPNext stock document behavior, deferred until write governance.

First implementation rule:

- W15C may capture arrival and readiness evidence.
- W15C must not post stock, move stock, or silently put away inventory.
- If target warehouse/bin is missing or ambiguous, task state should become `sent_back` or `needs_manager_review`, not a stock action.

## 9D. Serial, Batch, Expiry, And Controlled Items

Serial/batch/expiry-controlled items are high-risk and must not be treated like ordinary quantity-only stock.

Initial rule:

- Detect controlled-item cases.
- Show controlled status in review.
- Block execution-style actions until a dedicated controlled-item phase exists.
- Route to manager review or controlled unavailable state.

Deferred design lane:

- Serial number capture.
- Batch capture.
- Expiry date capture.
- Serial and Batch Bundle handling.
- Barcode/scan-assisted capture.
- Validation against ERPNext controlled inventory rules.

No W15B/W15C implementation should create Serial and Batch Bundle records.

## 9E. Barcode And Mobile Lane

Barcode/mobile should be planned, not implemented in W15B.

Future barcode/mobile scope:

- Scan PO/SO/task reference.
- Scan item barcode.
- Scan warehouse/bin/location.
- Scan serial/batch where controlled.
- Support mobile-friendly task flow.

Deferred until:

- task model is stable;
- role model is stable;
- controlled-item rules are defined;
- idempotency and audit trail are proven;
- owner approves mobile/scan workflow.

No scan should ever post stock directly.

## 9F. Warehouse KPI And Reporting Lane

Operational KPIs should be planned after workflows exist.

Candidate future KPIs:

- dock-to-stock time;
- arrival discrepancy rate;
- open receiving discrepancy aging;
- pick accuracy;
- pick shortage rate;
- return aging;
- quarantine aging;
- transfer aging;
- cycle count variance rate;
- manager approval aging;
- tasks by user/team.

Rules:

- W15B should not add these reports yet.
- KPI data should come from controlled Warehouse task/audit records and ERPNext source documents.
- No valuation/accounting KPIs should appear in Warehouse Console.

## 9G. W15B Gate After Amendments

Goal:

- Add a clear Warehouse Action Center shell without stock mutation.
- Replace the removed duplicated Manager Readiness idea with real action queues.

Recommended placement:

- Add an Action Center section on Overview, or a new custom route reachable from Overview.
- Do not add many new left-sidebar items until the workflow proves useful.

Initial manager cards:

- Arrivals needing approval.
- Receiving discrepancies.
- Picking release blockers.
- Return requests.
- Transfer approvals.
- Cycle count variances.
- Stock adjustment requests.
- Quarantine/damage decisions.

Initial user cards:

- My arrival checks.
- My pick tasks.
- My return intake tasks.
- My transfer tasks.
- My cycle counts.
- My discrepancy follow-ups.

Rules:

- Shell only.
- No create/submit/post actions.
- Cards open custom Warehouse pages only.
- Empty states must be clear and premium.
- No native ERPNext routes.

## 10. W15C Inbound Receiving Workflow

Start here because receiving quality drives stock accuracy.

User actions:

- Confirm goods arrived.
- Count received quantity.
- Mark shortage, overage, damaged, wrong item, or unclear paperwork.
- Add receiving note.
- Attach evidence later if approved.
- Submit for manager review.

Manager actions:

- Approve clean arrival readiness.
- Approve discrepancy readiness.
- Send back for recount.
- Mark quarantine/quality review.
- Route to Procurement follow-up.
- Prepare Purchase Receipt draft only in a later approved write phase.

Data capture:

- Internal readiness record or event log.
- Source Purchase Order and line references.
- Quantity evidence, not valuation.
- Condition/discrepancy codes.
- Actor and timestamp.

Forbidden:

- Purchase Receipt create/submit.
- Stock posting.
- PO mutation.
- Supplier messaging.
- Valuation or commercial fields.

## 11. W15D Outbound Picking And Dispatch Workflow

User actions:

- Start pick task.
- Mark picked quantity.
- Report shortage, damage, wrong bin, or unavailable stock.
- Mark ready for pack/dispatch handoff.

Manager actions:

- Release picking.
- Resolve shortage.
- Approve partial fulfillment.
- Route Sales follow-up.
- Prepare Delivery Note or Pick List draft only in a later approved write phase.

Forbidden:

- Reserve/unreserve stock.
- Create/submit Pick List.
- Create/submit Delivery Note.
- Ship/deliver/post.
- Customer messaging from Warehouse.

## 12. W15E Customer Return Workflow

User actions:

- Receive returned item physically.
- Identify linked Sales Order/Delivery Note when available.
- Inspect condition.
- Record restock/quarantine/repair/scrap suggestion.
- Submit for manager review.

Manager actions:

- Approve restock readiness.
- Approve quarantine.
- Approve repair/scrap path.
- Route Sales follow-up.

Forbidden:

- Create return Delivery Note.
- Post return stock movement.
- Credit note/invoice/accounting behavior.
- Customer messaging from Warehouse.

## 13. W15F Supplier Return Workflow

User actions:

- Identify received/damaged/wrong supplier item.
- Prepare supplier return evidence.
- Link to PO/Purchase Receipt where visible.
- Submit for manager review.

Manager actions:

- Approve supplier return readiness.
- Route Procurement follow-up.
- Approve quarantine/hold path.

Forbidden:

- Supplier email/send action.
- Return Purchase Receipt creation.
- Stock Entry posting.
- Purchase commercial changes.

## 14. W15G Internal Transfer Workflow

User actions:

- Request transfer.
- Select item, source warehouse, target warehouse, quantity, and reason.
- Source-side pick evidence.
- Target-side receive evidence.

Manager actions:

- Approve/reject transfer.
- Resolve source shortage.
- Authorize in-transit handling.

Forbidden:

- Stock Entry create/submit.
- Transfer posting.
- Stock Ledger/Stock Balance native route exposure.

## 15. W15H Cycle Count And Variance Workflow

User actions:

- Open assigned count.
- Count item/location.
- Submit counted quantity and note.
- Report damaged/unusable stock.

Manager actions:

- Approve variance.
- Reject and request recount.
- Escalate high-risk variance.
- Prepare stock adjustment request only in later approved phase.

Forbidden:

- Stock Reconciliation create/submit.
- Valuation rate or amount exposure.
- Automatic adjustment.

## 16. W15I Role, Permission, Audit, And Hardening

Every action needs:

- Allowed roles.
- Source document status requirements.
- Server-side validation.
- Idempotency key.
- Stale-state protection.
- Actor derived from session.
- Audit log.
- Error state.
- Rollback/void handling if applicable.
- Smoke selectors.
- Manager/user credentialed smoke.

Minimum audit fields:

- action_type.
- source_doctype.
- source_name.
- source_line_id.
- target_workflow.
- old_state.
- new_state.
- actor.
- actor_role_family.
- timestamp.
- client_request_id.
- server_validation_result.
- note/evidence summary.

## 17. W15J Protected Gates And Live Validation

Before any live alignment:

- Source unit tests.
- Static write/native-route/valuation/search scans.
- Credentialed source smoke.
- Security/Stability review.
- Operation review.
- Owner manual review where UI/action behavior changes.
- Protected source gate.
- Main Control commit.

After live alignment:

- Live asset build.
- Cache clear on the correct site.
- Service restart when needed.
- Live credentialed smoke.
- Live protected workspace gate.
- Rollback plan confirmed.

## 18. Non-Negotiable Boundaries

Do not add:

- Native ERPNext route escape.
- Global Quick Find back into page content.
- Duplicate Manager Readiness overview block.
- Stock document create/submit/cancel/amend.
- Purchase Receipt, Delivery Note, Pick List, Stock Entry, Stock Reconciliation, Stock Reservation mutation.
- Valuation/accounting/commercial exposure.
- Supplier/customer email send from Warehouse.
- Silent stock mutation.
- Sales runtime changes.
- Procurement runtime changes.

## 19. Recommended Next Agent Prompt

Use this for W15B only after owner accepts W15A:

```text
You are the Warehouse Agent. Implement W15B Action Center shell only.

Repository:
/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui

Scope:
- Add Warehouse Action Center shell/work-entry foundation.
- No backend write methods.
- No stock mutation.
- No Purchase Receipt, Delivery Note, Pick List, Stock Entry, Stock Reconciliation, Stock Reservation creation/submission.
- No Sales runtime change.
- No Procurement runtime change.
- No native ERPNext route targets.
- No valuation/accounting/commercial exposure.

Expected UI:
- Overview or custom Warehouse Action Center route with role-aware empty/action queues.
- Manager queues: arrivals needing approval, receiving discrepancies, picking blockers, returns, transfer approvals, cycle count variances, stock adjustment requests, quarantine/damage decisions.
- User queues: my arrival checks, my pick tasks, my returns, my transfer tasks, my cycle counts, my discrepancy follow-ups.
- Cards open only custom Warehouse pages or controlled unavailable states.
- Use the confirmed Warehouse premium UI theme and shared sidebar Search pattern.

Validation:
- compileall
- unit tests
- node --check touched JS
- git diff --check
- static scans for write APIs, native routes, stock document exposure, valuation/commercial exposure, Quick Find regression, Sales/Procurement boundary

Stop before commit, push, live alignment, restart, protected gates.
```

## 20. W15A Acceptance Checklist

W15A is complete when:

- The owner confirms the three-layer model.
- The owner confirms Phase 0 is complete.
- The owner confirms W15B should be an Action Center shell, not a stock action implementation.
- The owner confirms Inbound Receiving remains the first real workflow after the shell.
- Security/Stability accepts that the document does not approve writes.
- Operation Review accepts the flow order as realistic for warehouse work.
