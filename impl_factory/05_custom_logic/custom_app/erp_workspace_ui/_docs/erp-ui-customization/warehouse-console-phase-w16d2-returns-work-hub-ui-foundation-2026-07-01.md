# Warehouse Console Phase W16D2 - Returns Work Hub UI Foundation

Date: 2026-07-01
Status: Source implementation complete; owner manual check required before live alignment.
Owner: ERP UI Main Agent
Review mode: Hybrid Review Ladder internal sidecars plus source validation

## 1. Purpose

W16D2 starts burning down the return-related planned state in Warehouse Overview. It adds a visible Warehouse-owned `Returns work hub` foundation without enabling return evidence save, manager decision, or handoff write actions.

This phase is intentionally Overview-only. Customer return runtime activation remains W16D3. Supplier return runtime activation remains W16D4.

## 2. Implemented Scope

- Warehouse Action Center `Return intake` now points to the Returns work hub instead of staying as a plain planned card.
- Warehouse Action Center `Return decisions` now points to the Returns work hub instead of staying as a plain planned card.
- A new `Returns work hub` section renders in Warehouse Overview.
- The hub contains three lanes:
  - Customer returns
  - Supplier returns
  - Return decisions
- The hub is labelled `Custom foundation`, not `Planned`, `Approved`, or `Executable`.
- The hub has no active write controls, links, or native-route targets.
- Customer and supplier return cards were removed from the remaining `Planned workflow shells` section.
- Remaining planned workflow shells now show only Internal Transfer and Cycle Count / Inventory Variance.

## 3. User-Facing Wording

Accepted wording direction:

- `Returns work hub`
- `Customer returns`
- `Supplier returns`
- `Return decisions`
- `Custom foundation`
- `Request-only custom return records`
- `No Sales Return`
- `No Credit Note`
- `No supplier notified`
- `No stock decreased`
- `No ERP document`

Forbidden implication remains blocked:

- No `Approve return` wording.
- No `Create Sales Return` wording.
- No `Create Credit Note` wording.
- No `Return Purchase Receipt` action wording.
- No `Debit note` action wording.
- No native route or document creation wording.

## 4. Source Changes

Scoped source changes:

- `erp_workspace_ui/warehouse_console/service.py`
  - Action Center return cards now include `target_section="returns-work-hub"` and `state="hub"`.
  - No backend write method was added.
  - No ERPNext document route or mutation target was added.

- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
  - Action Center cards can now target a safe in-page section.
  - The Returns work hub renderer was added.
  - Return Action Center buttons scroll to the Returns work hub instead of routing.
  - Planned workflow shells were reduced to Internal Transfer and Cycle Count / Inventory Variance.

- `erp_workspace_ui/tests/test_warehouse_console_w3_contracts.py`
  - Action Center contract now distinguishes routed cards, returns hub target cards, and still-planned cards.
  - Return hub cards are asserted as in-page targets, not worklist routes.

- `ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
  - Smoke now asserts Returns work hub visibility.
  - Smoke asserts three hub lanes and zero active hub controls.
  - Smoke asserts Action Center return cards target `returns-work-hub`.
  - Smoke asserts no Sales return queue key, Sales route, `new_doc`, native route, or native form pattern leaks into the Returns hub.
  - Planned workflow shell smoke now expects only two remaining cards.

## 5. Subagent Review Handling

Internal sidecars warned against reusing Sales return keys and Procurement native document creation patterns. Their repository-path discovery was not reliable for the remote DigitalOcean design root, so their `no Warehouse foundation exists` findings were treated as false-path findings rather than blockers.

Useful sidecar constraints were applied:

- Do not reuse `sales_returns_in_progress`.
- Do not route to `sales-console-worklist`.
- Do not reuse Procurement `new_doc` patterns.
- Do not expose native ERPNext document forms.
- Keep W16D2 as no-write Overview foundation only.

## 6. Validation

Validation passed:

- `git diff --check HEAD`
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js`
- `python3 -m compileall -q erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`, passing `404 tests OK`

Static scan notes:

- Hits for Sales Return, Credit Note, Purchase Receipt, Purchase Invoice, Stock Entry, and Stock Reconciliation are guardrail copy or negative smoke assertions only.
- No active native route, Sales route, Procurement `new_doc`, stock/accounting mutation, notification, email, portal, or external action pattern was introduced by W16D2.

## 7. Manual Check Required

Owner manual UI check is required before live alignment because W16D2 changes visible Warehouse Overview layout.

Manual check should verify:

- `Returns work hub` appears in Warehouse Overview.
- Action Center return cards point visually and behaviorally to the Returns hub.
- The hub feels like a useful custom foundation, not a fake executable workflow.
- Customer and supplier return work no longer appears as unresolved planned workflow shell cards.
- Remaining planned shells show only Internal Transfer and Cycle Count / Inventory Variance.
- No return action button implies document creation, stock movement, customer notification, supplier notification, refund, debit, credit, or approval.

## 8. Boundary Confirmation

W16D2 does not create, save, submit, cancel, amend, post, notify, email, route to, or expose any ERPNext return, stock, sales, purchase, accounting, or notification document.

Still blocked:

- Customer return evidence save.
- Supplier return evidence save.
- Customer return manager decisions.
- Supplier return manager decisions.
- Return handoff requests.
- Sales Return.
- Credit Note.
- Return Delivery Note.
- Return Purchase Receipt.
- Purchase Invoice return / debit note.
- Stock Entry.
- Stock Ledger, Stock Balance, Stock Reconciliation, and Stock Reservation mutation.
- Stock movement or posting.
- Native ERPNext route exposure.
- Sales/Procurement/Finance/Admin runtime mutation.
- Customer notification, supplier notification, email, portal, or external action.
- Live alignment, restart, protected gate, commit, push, release closure, or full Warehouse Workspace Closure.

## 9. Next Phase

Proceed to W16D3 only after W16D2 owner/manual check is accepted. W16D3 should activate Customer Return intake evidence save using existing custom backend methods and preserve the same custom-record-only boundaries.
